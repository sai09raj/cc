#!/usr/bin/env python3
"""
L1-21 line relay replay - 230 kV line L1 event of 2026-09-14.

Reads both COMTRADE 1999 ASCII records (Substation A and Substation B L1-21 relays)
and the two settings exports, and replays both relays sample by sample exactly as
the L1-21 manual excerpt specifies:

  * full-cycle (32 sample) Fourier RMS phasors in a fixed reference frame, k >= 31
  * phase-to-phase loops AB, BC, CA, V = VX-VY, I = IX-IY, evaluated only if |I| >= 50PP
  * mho circles through the origin: forward Z1/Z2, reverse Z3R
  * logic order per sample: zone elements, RX, echo, KEY, TRIP
  * channel: remote KEY at k -> local RX at k+12 (each direction)
  * echo (only when ECHO=Y): AND(!Z1, !Z2, !Z3R, !EBLK(Z3R), RX) -> EDPU pickup
    (asserts on the EDPU-th consecutive asserted sample) -> EDUR one-shot (EDUR
    samples from a rising input, non-retriggerable while running)
  * EBLK dropout timer: output asserted while Z3R is asserted and for EBLK samples
    after Z3R deasserts
  * KEY = Z2 + ECHO ; TRIP = Z1 + Z2*RX, latched
  * breaker 52A opens 96 samples after its relay asserts TRIP

The program
  1. replays both relays from the recorded analogs and compares every replayed digital
     channel with the recorded one, sample by sample;
  2. computes the investigation quantities (fault inception, first assertions,
     BC loop impedances and currents at sample 400, through-current comparison,
     fault locator);
  3. runs counterfactual replays (Substation B currents restored to the design CT
     ratio 1200:5; and the alternative fix CTR=400 with re-scaled reaches);
  4. writes replayed_digitals.csv and results.json next to this script (or to --out).

Usage:  python3 l1_replay.py <directory containing the extracted zip> [--out DIR]
"""
import argparse
import cmath
import csv
import json
import math
import os
import re
import sys

import numpy as np

N = 32                  # samples per cycle
FS = 1920.0             # samples per second
CHANNEL_DELAY = 12      # samples, each direction
BREAKER_DELAY = 96      # samples from TRIP to 52A open
LOOPS = (("AB", "VA", "VB", "IA", "IB"),
         ("BC", "VB", "VC", "IB", "IC"),
         ("CA", "VC", "VA", "IC", "IA"))
X1_PER_KM = 0.48        # ohm/km, L1 positive-sequence reactance (manual sec. 4)


# --------------------------------------------------------------------------- I/O
def read_comtrade(cfg_path):
    dat_path = cfg_path[:-4] + ".dat"
    with open(cfg_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    station, device, rev = lines[0].split(",")
    tt, na, nd = lines[1].split(",")
    na = int(na.rstrip("A")); nd = int(nd.rstrip("D"))
    analog = []
    for i in range(na):
        p = lines[2 + i].split(",")
        analog.append(dict(name=p[1], unit=p[4], a=float(p[5]), b=float(p[6]),
                           skew=float(p[7]), primary=float(p[10]), secondary=float(p[11]),
                           ps=p[12]))
    digital = [lines[2 + na + i].split(",")[1] for i in range(nd)]
    idx = 2 + na + nd
    freq = float(lines[idx]); nrates = int(lines[idx + 1])
    rate, endsamp = lines[idx + 2].split(",")
    t_first = lines[idx + 2 + nrates]
    t_trig = lines[idx + 3 + nrates]
    raw = np.loadtxt(dat_path, delimiter=",", dtype=np.int64)
    n = raw[:, 0]
    assert np.all(n == np.arange(1, len(n) + 1)), "sample numbers not contiguous"
    ana = {}
    for i, ch in enumerate(analog):
        ana[ch["name"]] = raw[:, 2 + i] * ch["a"] + ch["b"]
    dig = {name: raw[:, 2 + na + i].astype(int) for i, name in enumerate(digital)}
    return dict(station=station, device=device, analog_cfg=analog, digital_names=digital,
                ana=ana, dig=dig, n=n, t_us=raw[:, 1], freq=freq, rate=float(rate),
                endsamp=int(endsamp), t_first=t_first, t_trig=t_trig)


def read_settings(path):
    s = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"^\s*([A-Z0-9]+)\s*=\s*([^;]+)", line)
            if m:
                s[m.group(1)] = m.group(2).strip()
    out = dict(raw=s)
    for k in ("CTR", "PTR", "Z1ANG", "Z1P", "Z2P", "Z3P", "50PP"):
        v = s.get(k, "OFF")
        out[k] = None if v.upper() == "OFF" else float(v)
    for k in ("EDPU", "EDUR", "EBLK"):
        out[k] = int(s[k])
    out["ECHO"] = s.get("ECHO", "N").upper() == "Y"
    out["SCHEME"] = s.get("SCHEME")
    return out


# --------------------------------------------------------------------- phasors
def phasors(x):
    """Full-cycle Fourier RMS phasor, fixed reference frame (manual sec. 1).
    Returns complex array, NaN for k < 31."""
    x = np.asarray(x, float)
    K = len(x)
    rot = np.exp(-1j * 2 * np.pi * np.arange(K) / N)
    prod = x * rot
    cs = np.concatenate(([0], np.cumsum(prod)))
    X = np.full(K, np.nan + 1j * np.nan)
    k = np.arange(N - 1, K)
    X[k] = (math.sqrt(2) / N) * (cs[k + 1] - cs[k + 1 - N])
    return X


def mho_forward(Z, R, T):
    c = (R / 2) * cmath.exp(1j * T)
    return abs(Z - c) <= R / 2


def mho_reverse(Z, R, T):
    c = (R / 2) * cmath.exp(1j * T)
    return abs(Z + c) <= R / 2


# --------------------------------------------------------------------- relay
class Relay:
    """One L1-21 relay: element and scheme state, evaluated once per sample."""

    def __init__(self, name, settings, ana, current_scale=1.0):
        self.name = name
        self.s = settings
        self.P = {ch: phasors(ana[ch] * (current_scale if ch.startswith("I") else 1.0))
                  for ch in ("VA", "VB", "VC", "IA", "IB", "IC")}
        self.K = len(ana["VA"])
        T = math.radians(settings["Z1ANG"])
        self.T = T
        # precompute loop impedances / zone outputs per sample
        self.Z = {}
        self.Iloop = {}
        zones = {"Z1": np.zeros(self.K, int), "Z2": np.zeros(self.K, int),
                 "Z3R": np.zeros(self.K, int)}
        self.loop_op = {}
        for lname, vx, vy, ix, iy in LOOPS:
            V = self.P[vx] - self.P[vy]
            I = self.P[ix] - self.P[iy]
            self.Iloop[lname] = I
            Zl = np.full(self.K, np.nan + 1j * np.nan)
            ops = {z: np.zeros(self.K, int) for z in zones}
            for k in range(N - 1, self.K):
                if abs(I[k]) >= settings["50PP"]:
                    z = V[k] / I[k]
                    Zl[k] = z
                    if settings["Z1P"] is not None and mho_forward(z, settings["Z1P"], T):
                        ops["Z1"][k] = 1
                    if settings["Z2P"] is not None and mho_forward(z, settings["Z2P"], T):
                        ops["Z2"][k] = 1
                    if settings["Z3P"] is not None and mho_reverse(z, settings["Z3P"], T):
                        ops["Z3R"][k] = 1
            self.Z[lname] = Zl
            self.loop_op[lname] = ops
            for z in zones:
                zones[z] |= ops[z]
        self.zones = zones
        # scheme state
        self.pu_count = 0
        self.pu_prev = 0
        self.edur_left = 0
        self.eblk_left = 0
        self.trip_latch = 0
        self.trip_k = None
        self.out = {c: np.zeros(self.K, int) for c in
                    ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP", "52A")}

    def step(self, k, rx):
        s = self.s
        z1 = int(self.zones["Z1"][k]); z2 = int(self.zones["Z2"][k]); z3 = int(self.zones["Z3R"][k])
        # echo logic
        echo = 0
        if s["ECHO"]:
            # EBLK dropout timer on Z3R
            if z3:
                self.eblk_left = s["EBLK"]
                eblk = 1
            elif self.eblk_left > 0:
                self.eblk_left -= 1
                eblk = 1
            else:
                eblk = 0
            andout = int((not z1) and (not z2) and (not z3) and (not eblk) and rx)
            # EDPU pickup: asserts on the EDPU-th consecutive asserted sample
            self.pu_count = self.pu_count + 1 if andout else 0
            pu = int(self.pu_count >= s["EDPU"])
            # EDUR one-shot from rising pickup output, not retriggerable while running
            if pu and not self.pu_prev and self.edur_left == 0:
                self.edur_left = s["EDUR"]
            self.pu_prev = pu
            if self.edur_left > 0:
                echo = 1
                self.edur_left -= 1
        key = int(z2 or echo)
        trip = int(z1 or (z2 and rx))
        if trip and not self.trip_latch:
            self.trip_latch = 1
            self.trip_k = k
        o = self.out
        o["Z1"][k] = z1; o["Z2"][k] = z2; o["Z3R"][k] = z3; o["RX"][k] = rx
        o["ECHO"][k] = echo; o["KEY"][k] = key; o["TRIP"][k] = self.trip_latch
        return key


def replay(relA, relB, k52_init_A=1, k52_init_B=1):
    K = min(relA.K, relB.K)
    keyA = np.zeros(K, int); keyB = np.zeros(K, int)
    for k in range(K):
        rxA = int(keyB[k - CHANNEL_DELAY]) if k >= CHANNEL_DELAY else 0
        rxB = int(keyA[k - CHANNEL_DELAY]) if k >= CHANNEL_DELAY else 0
        keyA[k] = relA.step(k, rxA)
        keyB[k] = relB.step(k, rxB)
    for rel, init in ((relA, k52_init_A), (relB, k52_init_B)):
        b = np.full(K, init, int)
        if rel.trip_k is not None:
            b[rel.trip_k + BREAKER_DELAY:] = 0
        rel.out["52A"] = b


def first(arr):
    idx = np.flatnonzero(arr)
    return int(idx[0]) if len(idx) else None


def edges(arr):
    d = np.diff(np.concatenate(([0], arr)))
    return [int(i) for i in np.flatnonzero(d == 1)], [int(i) for i in np.flatnonzero(d == -1)]


def cplx(z, nd=4):
    return {"R": round(z.real, nd), "X": round(z.imag, nd), "mag": round(abs(z), nd),
            "ang_deg": round(math.degrees(cmath.phase(z)), 2)}


def pol(z, nd=4):
    return {"mag": round(abs(z), nd), "ang_deg": round(math.degrees(cmath.phase(z)), 2)}


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="directory with the extracted event files")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    src = a.src
    recA = read_comtrade(os.path.join(src, "SUBA_L1_RLY_20260914_142207.cfg"))
    recB = read_comtrade(os.path.join(src, "SUBB_L1_RLY_20260914_142207.cfg"))
    setA = read_settings(os.path.join(src, "SUBA_L1_RLY_settings.txt"))
    setB = read_settings(os.path.join(src, "SUBB_L1_RLY_settings.txt"))
    K = len(recA["n"])
    assert K == len(recB["n"]) == recA["endsamp"] == recB["endsamp"]
    assert recA["rate"] == FS and recA["freq"] == 60
    res = {"files": {"A": "SUBA_L1_RLY_20260914_142207", "B": "SUBB_L1_RLY_20260914_142207"},
           "sample_convention": "relay sample k = .dat sample number n - 1 (manual sec. 1); "
                                "all sample numbers below are relay samples k unless labelled n",
           "samples_per_record": K}

    # ---------------------------------------------------------- 1. as-found replay
    relA = Relay("A", setA, recA["ana"])
    relB = Relay("B", setB, recB["ana"])
    replay(relA, relB, k52_init_A=int(recA["dig"]["52A"][0]), k52_init_B=int(recB["dig"]["52A"][0]))

    match = {}
    for rec, rel, tag in ((recA, relA, "A"), (recB, relB, "B")):
        m = {}
        for name in rec["digital_names"]:
            mism = np.flatnonzero(rel.out[name] != rec["dig"][name])
            m[name] = {"samples_compared": K, "mismatches": int(len(mism)),
                       "first_mismatch_k": int(mism[0]) if len(mism) else None}
        match[tag] = m
    all_ok = all(v["mismatches"] == 0 for t in match.values() for v in t.values())
    res["replay_vs_record"] = {"all_digital_channels_match": all_ok, "detail": match}

    # CSV of replayed digitals (and recorded, for side-by-side)
    csv_path = os.path.join(a.out, "replayed_digitals.csv")
    colsA = recA["digital_names"]; colsB = recB["digital_names"]
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        hdr = ["k", "n", "t_rel_us"]
        hdr += ["A_" + c for c in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP", "52A")]
        hdr += ["B_" + c for c in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP", "52A")]
        hdr += ["A_rec_" + c for c in colsA] + ["B_rec_" + c for c in colsB]
        w.writerow(hdr)
        for k in range(K):
            row = [k, k + 1, int(recA["t_us"][k])]
            row += [int(relA.out[c][k]) for c in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP", "52A")]
            row += [int(relB.out[c][k]) for c in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP", "52A")]
            row += [int(recA["dig"][c][k]) for c in colsA] + [int(recB["dig"][c][k]) for c in colsB]
            w.writerow(row)

    # ------------------------------------------------------ fault inception / type
    # disturbance detector on raw samples: |x[k] - x[k-32]| (one-cycle difference)
    def inception(rec):
        res_ = {}
        for ch in ("IA", "IB", "IC", "VA", "VB", "VC"):
            x = rec["ana"][ch]
            d = np.abs(x[N:] - x[:-N])
            pre = d[:200]                     # well before the trigger
            noise = pre.max()
            peak = np.abs(x[:200]).max()
            thr = max(4 * noise, 0.02 * peak)
            idx = np.flatnonzero(d > thr)
            res_[ch] = {"first_k": int(idx[0] + N) if len(idx) else None,
                        "prefault_cycle_diff_max": round(float(noise), 4),
                        "threshold": round(float(thr), 4)}
        return res_
    incA = inception(recA); incB = inception(recB)
    kincA = min(v["first_k"] for v in incA.values() if v["first_k"] is not None)
    kincB = min(v["first_k"] for v in incB.values() if v["first_k"] is not None)
    # trigger time from cfg
    def tsec(s):
        hh, mm, ss = s.split(",")[1].split(":")
        return int(hh) * 3600 + int(mm) * 60 + float(ss)
    k_trig = round((tsec(recA["t_trig"]) - tsec(recA["t_first"])) * FS)

    # sequence components during fault (k = 400) and pre-fault (k = 300)
    a_ = cmath.exp(2j * math.pi / 3)
    def seq(rel, k, q="I"):
        A_, B_, C_ = rel.P[q + "A"][k], rel.P[q + "B"][k], rel.P[q + "C"][k]
        return ((A_ + B_ + C_) / 3, (A_ + a_ * B_ + a_ * a_ * C_) / 3, (A_ + a_ * a_ * B_ + a_ * C_) / 3)
    fault_type = {}
    for tag, rel in (("A", relA), ("B", relB)):
        d = {}
        for k in (300, 400):
            i0, i1, i2 = seq(rel, k, "I"); v0, v1, v2 = seq(rel, k, "V")
            d[f"k{k}"] = {
                "IA": pol(rel.P["IA"][k]), "IB": pol(rel.P["IB"][k]), "IC": pol(rel.P["IC"][k]),
                "VA": pol(rel.P["VA"][k]), "VB": pol(rel.P["VB"][k]), "VC": pol(rel.P["VC"][k]),
                "I0": pol(i0), "I1": pol(i1), "I2": pol(i2), "V0": pol(v0), "V2": pol(v2),
                "IB_plus_IC": pol(rel.P["IB"][k] + rel.P["IC"][k]),
            }
        # superimposed (fault - prefault) currents, two cycles apart, at k=400 vs k=300 load
        dI = {ph: rel.P["I" + ph][400] - rel.P["I" + ph][300] for ph in "ABC"}
        d["delta_I_k400_minus_k300"] = {ph: pol(v) for ph, v in dI.items()}
        fault_type[tag] = d
    res["item1_fault"] = {
        "fault_type": "phase B to phase C (BC phase-to-phase, no ground) on line L2, 6.5 km from Substation B; external to L1",
        "fault_inception_k_SubA": int(kincA),
        "fault_inception_k_SubB": int(kincB),
        "fault_inception_n_dat": int(min(kincA, kincB) + 1),
        "record_trigger_k": int(k_trig),
        "inception_detector": "first sample where |x[k]-x[k-32]| exceeds max(4 x pre-fault maximum, 2 % of pre-fault peak)",
        "per_channel_detection": {"A": incA, "B": incB},
        "phasor_evidence": fault_type,
    }

    # ------------------------------------------------- 2. first element assertions
    def first_assertions(rel, rec):
        fa = {}
        for c in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP"):
            fa[c] = first(rel.out[c])
        b52 = rel.out["52A"]
        fa["52A_open"] = first(1 - b52) if b52[0] == 1 else None
        loops = {}
        for lname, *_ in LOOPS:
            loops[lname] = {z: first(rel.loop_op[lname][z]) for z in ("Z1", "Z2", "Z3R")}
        return fa, loops
    faA, loopsA = first_assertions(relA, recA)
    faB, loopsB = first_assertions(relB, recB)
    t0 = tsec(recA["t_first"])
    def ktime(k):
        if k is None:
            return None
        t = t0 + k / FS
        hh = int(t // 3600); mm = int((t % 3600) // 60); ss = t - hh * 3600 - mm * 60
        return f"{hh:02d}:{mm:02d}:{ss:07.4f}"
    def edges_all(rel, names):
        d = {}
        for c in names:
            r, f_ = edges(rel.out[c])
            d[c] = {"asserted_k": r, "deasserted_k": f_,
                    "asserted_time": [ktime(x) for x in r], "deasserted_time": [ktime(x) for x in f_]}
        return d
    res["item2_first_assertions"] = {
        "A": {"first_asserted_k": faA, "not_asserted": [c for c, v in faA.items() if v is None],
              "per_loop_first_k": loopsA,
              "edges": edges_all(relA, ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP"))},
        "B": {"first_asserted_k": faB, "not_asserted": [c for c, v in faB.items() if v is None],
              "per_loop_first_k": loopsB,
              "edges": edges_all(relB, ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP"))},
        "note": "Relay A has ECHO=N and Z3P=OFF, so its ECHO and Z3R elements are disabled; "
                "relay B Z1, Z2, Z3R and TRIP never asserted.",
    }

    # ------------------------------------------------- 3./4. values at sample 400
    k = 400
    item3 = {}
    for tag, rel, s in (("A", relA, setA), ("B", relB, setB)):
        Zs = rel.Z["BC"][k]
        Iloop = rel.Iloop["BC"][k]
        item3[tag] = {
            "Z_BC_secondary_ohm": cplx(Zs),
            "Z_BC_primary_ohm_relay_settings_CTR_PTR": cplx(Zs * s["PTR"] / s["CTR"]),
            "I_BC_loop_secondary_A": pol(Iloop),
            "relay_CTR": s["CTR"], "relay_PTR": s["PTR"],
        }
    # true primary for B: actual CT ratio 2000:5 (core 1 found on X1-X5)
    CTR_B_actual = 400.0
    ZsB = relB.Z["BC"][k]
    item3["B"]["Z_BC_primary_ohm_true_CT_2000_5"] = cplx(ZsB * setB["PTR"] / CTR_B_actual)
    item3["B"]["Z_BC_secondary_ohm_if_CT_on_design_1200_5_tap"] = cplx(ZsB * 240.0 / CTR_B_actual)
    item3["A"]["Z_BC_primary_ohm_true"] = item3["A"]["Z_BC_primary_ohm_relay_settings_CTR_PTR"]
    res["item3_BC_impedance_k400"] = item3

    IB_B = relB.P["IB"][k]; IB_A = relA.P["IB"][k]
    res["item4_IB_L1_at_SubB_k400"] = {
        "IB_secondary_A": pol(IB_B),
        "IB_primary_A_true_CT_2000_5": round(abs(IB_B) * CTR_B_actual, 1),
        "IB_primary_A_as_relay_B_reports_CTR_240": round(abs(IB_B) * setB["CTR"], 1),
        "cross_check_IB_primary_at_SubA_A": round(abs(IB_A) * setA["CTR"], 1),
        "cross_check_angle_A_minus_B_deg": round(math.degrees(cmath.phase(IB_A / IB_B)), 2),
    }

    # through-current (KCL) check over the fault interval: line charging negligible,
    # so primary current entering L1 at A = primary current leaving L1 at B.
    ratio = {}
    for ph in "ABC":
        r = []
        for kk in range(340, 450):
            ia = relA.P["I" + ph][kk]; ib = relB.P["I" + ph][kk]
            r.append(-ia / ib)
        r = np.array(r)
        ratio[ph] = {"mean_mag_IA_over_IB_secondary": round(float(np.mean(np.abs(r))), 4),
                     "std_mag": round(float(np.std(np.abs(r))), 4),
                     "mean_angle_deg_of_-IA/IB": round(float(np.degrees(np.angle(np.mean(r)))), 2)}
    pre = {}
    for ph in "ABC":
        r = np.array([-relA.P["I" + ph][kk] / relB.P["I" + ph][kk] for kk in range(40, 300)])
        pre[ph] = {"mean_mag": round(float(np.mean(np.abs(r))), 4),
                   "mean_angle_deg": round(float(np.degrees(np.angle(np.mean(r)))), 2)}
    res["ct_ratio_evidence"] = {
        "description": "secondary current ratio |I_A|/|I_B| for the same primary through-current of L1; "
                       "equal CT ratios give 1.000, B on 2000:5 vs A on 1200:5 gives 2000/1200 = 1.667",
        "fault_interval_k340_449": ratio, "prefault_load_k40_299": pre,
        "implied_CT_ratio_B_primary_A_per_5A": round(240 * 5 * float(np.mean([v["mean_mag_IA_over_IB_secondary"] for v in ratio.values() if v["mean_mag_IA_over_IB_secondary"] > 0])) , 1),
    }
    # restrict implied ratio to B and C phases (A phase carries only load)
    impl = 240 * 5 * np.mean([ratio["B"]["mean_mag_IA_over_IB_secondary"], ratio["C"]["mean_mag_IA_over_IB_secondary"]])
    res["ct_ratio_evidence"]["implied_CT_ratio_B_primary_A_per_5A"] = round(float(impl), 1)

    # independent absolute check of the CT ratios: the BC loop voltage drop along L1
    # divided by the BC loop primary current must equal the L1 impedance 4.00 + j38.40 ohm.
    zl = {}
    for kk in (380, 400, 420):
        dV = (relA.P["VB"][kk] - relA.P["VC"][kk] - relB.P["VB"][kk] + relB.P["VC"][kk]) * setA["PTR"]
        IA_loop = (relA.P["IB"][kk] - relA.P["IC"][kk])
        IB_loop = (relB.P["IB"][kk] - relB.P["IC"][kk])
        zl[f"k{kk}"] = {
            "ZL1_from_A_current_CTR240": cplx(dV / (IA_loop * 240.0), 3),
            "ZL1_from_B_current_CTR400": cplx(dV / (-IB_loop * 400.0), 3),
            "ZL1_from_B_current_CTR240": cplx(dV / (-IB_loop * 240.0), 3)}
    res["ct_ratio_evidence"]["line_impedance_check"] = {
        "expected_ZL1_primary": cplx(complex(4.0, 38.4), 3), "computed": zl}
    # fault interruption by the L2 breakers: largest waveform discontinuity (second
    # difference) of the B-phase current at B between k = 420 and the A breaker opening
    xb = recB["ana"]["IB"]
    d2 = np.abs(xb[2:] - 2 * xb[1:-1] + xb[:-2])
    lo, hi = 420, 495
    k_clear = int(np.argmax(d2[lo - 2:hi - 2]) + lo)
    res["item1_fault"]["fault_interrupted_first_postfault_k"] = k_clear
    res["item1_fault"]["fault_duration_samples"] = int(k_clear - min(kincA, kincB))
    res["item1_fault"]["fault_duration_ms"] = round((k_clear - min(kincA, kincB)) / FS * 1000, 1)

    # fault locator at A (trip sample)
    kt = relA.trip_k
    ZA_t = relA.Z["BC"][kt]
    Xp = (ZA_t * setA["PTR"] / setA["CTR"]).imag
    res["fault_locator_A"] = {"trip_k": kt, "Z_BC_sec_at_trip": cplx(ZA_t),
                              "X_primary": round(Xp, 3), "distance_km": round(Xp / X1_PER_KM, 1),
                              "event_report_km": 92.0,
                              "actual_fault_location": "L2 tower 18, 80 km (L1) + 6.5 km = 86.5 km electrical path from A; the larger "
                                                       "apparent distance is the infeed of the Substation B source"}

    # B loop impedance trajectory vs Z3R circle
    T = math.radians(setB["Z1ANG"])
    def z3r_margin(z, R):  # positive = outside the circle
        return abs(z + (R / 2) * cmath.exp(1j * T)) - R / 2
    trajB = []
    for kk in range(330, 470, 5):
        z = relB.Z["BC"][kk]
        if np.isnan(z.real):
            trajB.append({"k": kk, "Z": None}); continue
        trajB.append({"k": kk, "Z_sec_as_found": cplx(z, 3),
                      "Z_sec_design_ratio": cplx(z * 0.6, 3),
                      "outside_Z3R_by_ohm_as_found": round(z3r_margin(z, setB["Z3P"]), 3),
                      "outside_Z3R_by_ohm_design_ratio": round(z3r_margin(z * 0.6, setB["Z3P"]), 3)})
    res["B_BC_loop_trajectory"] = trajB

    # minimum over the fault of B's BC apparent impedance distance to Z3R boundary
    ks = [kk for kk in range(340, 460) if not np.isnan(relB.Z["BC"][kk].real)]
    mins = min(ks, key=lambda kk: z3r_margin(relB.Z["BC"][kk], setB["Z3P"]))
    res["B_Z3R_closest_approach"] = {"k": mins, "Z_sec": cplx(relB.Z["BC"][mins]),
                                     "outside_by_ohm": round(z3r_margin(relB.Z["BC"][mins], setB["Z3P"]), 4),
                                     "required_Z3P_to_reach_ohm_sec_as_found": round(
                                         abs(relB.Z["BC"][mins]) ** 2 / (-(relB.Z["BC"][mins] * cmath.exp(-1j * T)).real), 3)}

    # --------------------------------------------- 5. counterfactual replays
    def run_cf(label, setB_cf, scaleB):
        rA = Relay("A", setA, recA["ana"])
        rB = Relay("B", setB_cf, recB["ana"], current_scale=scaleB)
        replay(rA, rB)
        fa_A, _ = first_assertions(rA, recA)
        fa_B, lB = first_assertions(rB, recB)
        return {"label": label,
                "A_first_asserted_k": fa_A, "B_first_asserted_k": fa_B,
                "A_trips": rA.trip_k is not None, "B_trips": rB.trip_k is not None,
                "B_edges": edges_all(rB, ("Z3R", "RX", "ECHO", "KEY")),
                "A_edges": edges_all(rA, ("Z2", "KEY", "RX", "TRIP")),
                "B_Z_BC_sec_k400": cplx(rB.Z["BC"][400]),
                "B_ECHO_ever": bool(rB.out["ECHO"].any())}, rA, rB
    # NOTE: the recorded analogs after k ~ 502 include the effect of breaker A opening;
    # in the counterfactual A would not trip, so post-502 analogs are not representative,
    # but every decision (echo or not) is made before k = 502.
    cf1, cfA1, cfB1 = run_cf("B CT secondary restored to design tap X2-X4 (1200:5); B currents x 2000/1200; settings unchanged",
                             setB, 2000.0 / 1200.0)
    setB_alt = dict(setB)
    setB_alt.update({"CTR": 400.0, "Z1P": 6.18, "Z2P": 9.65, "Z3P": 2.90, "50PP": 0.30})
    cf2, _, _ = run_cf("B CT left on X1-X5 (2000:5); relay B re-set CTR=400, Z1P=6.18, Z2P=9.65, Z3P=2.90, 50PP=0.30",
                       setB_alt, 1.0)
    # what if only the echo were absent (sensitivity: ECHO=N at B)
    setB_noecho = dict(setB); setB_noecho["ECHO"] = False
    cf3, _, _ = run_cf("as-found wiring but echo disabled at B (illustration only, not a recommended fix)", setB_noecho, 1.0)
    # timing margin of Z3R vs echo pickup in the corrected case
    rxB_first = first(cfB1.out["RX"]); z3_first = first(cfB1.out["Z3R"])
    cf1["coordination"] = {"B_RX_first_k": rxB_first, "B_Z3R_first_k": z3_first,
                           "echo_pickup_would_complete_k": (rxB_first + setB["EDPU"] - 1) if rxB_first is not None else None,
                           "Z3R_margin_samples_before_pickup": (rxB_first + setB["EDPU"] - 1 - z3_first)
                           if (rxB_first is not None and z3_first is not None) else None}
    res["item5_counterfactual"] = {"as_found": {"A_trips": relA.trip_k is not None, "A_trip_k": relA.trip_k,
                                                "B_trips": relB.trip_k is not None},
                                   "design_tap_restored": cf1, "ctr400_resettings": cf2,
                                   "echo_disabled_sensitivity": cf3}

    # --------------------------------------------- 6. settings recalculation for alt fix
    calc = {}
    ZL1 = complex(4.0, 38.4)
    for ctr in (240.0, 400.0):
        f_ = ctr / setB["PTR"]
        calc[str(int(ctr))] = {"Z1P": round(0.8 * abs(ZL1) * f_, 2), "Z2P": round(1.25 * abs(ZL1) * f_, 2),
                               "Z3P": round(1.5 * (1.25 * abs(ZL1) - abs(ZL1)) * f_, 2),
                               "50PP_same_primary_pickup": round(0.5 * 240.0 / ctr, 2)}
    res["item6_setting_recalc_by_CTR"] = calc

    # ------------------------------------------------ curated deliverable JSON
    i3 = res["item3_BC_impedance_k400"]; i4 = res["item4_IB_L1_at_SubB_k400"]
    summary = {
        "event": "230 kV line L1 trip at Substation A, 2026-09-14 14:22:07",
        "sample_convention": res["sample_convention"],
        "replay_reproduces_all_recorded_digital_channels": all_ok,
        "replay_mismatch_counts": {t: {c: v["mismatches"] for c, v in m.items()} for t, m in match.items()},
        "item1": {
            "fault_type": "BC phase-to-phase fault (no ground: I0 ~ 0, V0 ~ 0, IA unchanged) on line L2, tower 18, "
                          "6.5 km from Substation B - external to L1",
            "fault_inception_relay_sample_k": int(min(kincA, kincB)),
            "fault_inception_dat_sample_n": int(min(kincA, kincB) + 1),
            "fault_inception_time": ktime(min(kincA, kincB)),
            "fault_cleared_by_L2_first_postfault_sample_k": res["item1_fault"]["fault_interrupted_first_postfault_k"],
            "fault_duration_ms": res["item1_fault"]["fault_duration_ms"],
        },
        "item2": {
            "SubA": {e: faA[e] for e in ("Z1", "Z2", "RX", "KEY", "TRIP")} | {
                "Z3R": "disabled (Z3P=OFF)", "ECHO": "disabled (ECHO=N)", "52A_opened_k": faA["52A_open"],
                "Z2_loop": "BC"},
            "SubB": {e: faB[e] for e in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP")} | {
                "52A_opened_k": faB["52A_open"]},
            "note": "null = never asserted in the record",
        },
        "item3": {
            "SubA": {"Z_BC_secondary_ohm": i3["A"]["Z_BC_secondary_ohm"],
                     "Z_BC_primary_ohm": i3["A"]["Z_BC_primary_ohm_relay_settings_CTR_PTR"],
                     "conversion": "x PTR/CTR = 2000/240 (CT 1200:5 correct at A)"},
            "SubB": {"Z_BC_secondary_ohm": i3["B"]["Z_BC_secondary_ohm"],
                     "Z_BC_primary_ohm_true": i3["B"]["Z_BC_primary_ohm_true_CT_2000_5"],
                     "true_conversion": "x 2000/400 (CT actually on 2000:5 tap)",
                     "Z_BC_primary_ohm_as_relay_B_computes_with_CTR_240": i3["B"]["Z_BC_primary_ohm_relay_settings_CTR_PTR"],
                     "Z_BC_secondary_ohm_on_design_1200_5_tap": i3["B"]["Z_BC_secondary_ohm_if_CT_on_design_1200_5_tap"]},
        },
        "item4": {
            "IB_L1_SubB_secondary_A": i4["IB_secondary_A"],
            "IB_L1_SubB_primary_A_true": i4["IB_primary_A_true_CT_2000_5"],
            "IB_L1_SubB_primary_A_as_relay_B_would_report_CTR_240": i4["IB_primary_A_as_relay_B_reports_CTR_240"],
            "cross_check_IB_L1_SubA_primary_A": i4["cross_check_IB_primary_at_SubA_A"],
            "cross_check_phase_difference_deg": i4["cross_check_angle_A_minus_B_deg"],
        },
        "item5": {
            "root_cause": "Substation B line-protection CT core 1 (52-L1, replaced like-for-like 2000:5 MR in 2026-05) was "
                          "landed on the full-winding tap X1-X5 (2000:5) instead of the design tap X2-X4 (1200:5, drawing "
                          "B-E-2214 rev C), while relay B kept CTR = 240. Relay B under-measured current by 1200/2000 = 0.6, "
                          f"so its impedances were 1.667 x too large; its zone 3 reverse ({setB['Z3P']} ohm sec) did not see the external "
                          f"BC fault on L2 (closest approach {res['B_Z3R_closest_approach']['outside_by_ohm']:.2f} ohm outside the circle at "
                          f"k = {res['B_Z3R_closest_approach']['k']}), so the echo was not blocked, "
                          f"B echoed A's zone 2 permissive back and A tripped by POTT (Z2 * RX) at k = {relA.trip_k}.",
            "commissioning_gap": "The 2026-05-27 record shows core 1 on X1-X5 with ratio check PASS because the check compares "
                                 "with the nameplate ratio of the landed tap, not with the design ratio / relay CTR.",
            "ct_ratio_evidence": {
                "secondary_current_ratio_IA_SubA_over_IB_SubB_fault": res["ct_ratio_evidence"]["fault_interval_k340_449"]["B"]["mean_mag_IA_over_IB_secondary"],
                "secondary_current_ratio_prefault_load_phaseA": res["ct_ratio_evidence"]["prefault_load_k40_299"]["A"]["mean_mag"],
                "implied_SubB_CT_ratio": f'{res["ct_ratio_evidence"]["implied_CT_ratio_B_primary_A_per_5A"]}:5',
                "ZL1_check_k400_with_B_at_400": res["ct_ratio_evidence"]["line_impedance_check"]["computed"]["k400"]["ZL1_from_B_current_CTR400"],
                "ZL1_check_k400_with_B_at_240": res["ct_ratio_evidence"]["line_impedance_check"]["computed"]["k400"]["ZL1_from_B_current_CTR240"],
                "ZL1_expected": res["ct_ratio_evidence"]["line_impedance_check"]["expected_ZL1_primary"],
            },
            "without_root_cause_replay": {
                "SubB": (f"Z3R asserts at k = {cf1['B_edges']['Z3R']['asserted_k'][0]} "
                         f"({cf1['B_edges']['RX']['asserted_k'][0] - cf1['B_edges']['Z3R']['asserted_k'][0]} samples before RX at "
                         f"k = {cf1['B_edges']['RX']['asserted_k'][0]}, {cf1['coordination']['Z3R_margin_samples_before_pickup']} samples "
                         f"before the echo pickup would have completed at k = {cf1['coordination']['echo_pickup_would_complete_k']}) and "
                         f"deasserts at k = {cf1['B_edges']['Z3R']['deasserted_k'][0]}; EBLK holds to k = "
                         f"{cf1['B_edges']['Z3R']['deasserted_k'][0] + setB['EBLK'] - 1}, beyond RX dropout at "
                         f"k = {cf1['B_edges']['RX']['deasserted_k'][0]}: no ECHO, no KEY, no trip (correct - fault is behind B)."),
                "SubA": (f"Z2/KEY asserted k = {cf1['A_edges']['Z2']['asserted_k'][0]} to {cf1['A_edges']['Z2']['deasserted_k'][0] - 1} "
                         "(correct overreach), RX never asserts, no TRIP; L1 stays in service."),
                "A_trips": cf1["A_trips"], "B_trips": cf1["B_trips"], "B_echo": cf1["B_ECHO_ever"],
                "B_first_asserted_k": cf1["B_first_asserted_k"], "A_first_asserted_k": cf1["A_first_asserted_k"],
            },
        },
        "item6": {
            "corrective_action_recommended": "Re-land Substation B 52-L1 core 1 (L1-21 relay B IA/IB/IC) on tap X2-X4 (1200:5) "
                                             "per drawing B-E-2214 rev C; relay B settings unchanged (CTR = 240, Z1P = 3.71, "
                                             "Z2P = 5.79, Z3P = 1.74 ohm sec, 50PP = 0.50 A).",
            "settings_if_recommended_fix": {"CTR": 240, "PTR": 2000, "Z1P": 3.71, "Z2P": 5.79, "Z3P": 1.74, "50PP": 0.50},
            "alternative_if_core_must_stay_on_X1_X5_2000_5": {"CTR": 400, "PTR": 2000, "Z1P": 6.18, "Z2P": 9.65, "Z3P": 2.90,
                                                             "50PP": 0.30, "Z1ANG": 84.0,
                                                             "replay_result": {"A_trips": cf2["A_trips"], "B_echo": cf2["B_ECHO_ever"],
                                                                               "B_Z3R_first_k": cf2["B_first_asserted_k"]["Z3R"]}},
            "followups": [
                "Verify by primary injection / in-service load comparison that relay B secondary currents equal relay A's (ratio 1.000, 180 deg) before returning the POTT/echo scheme to normal",
                "Amend form P-14: ratio check against the design ratio and the relay CTR setting, not only the nameplate of the landed tap",
                "Audit all secondary circuits re-landed after the 2026-05 CT replacement at Substation B (cores 2 and 3 agree with B-E-2214)",
                "Add an end-to-end current comparison (both line ends) to the post-maintenance return-to-service checklist",
            ],
        },
        "other_values": {
            "SubA_fault_locator_km": res["fault_locator_A"]["distance_km"],
            "SubA_trip_sample_Z_BC_secondary": res["fault_locator_A"]["Z_BC_sec_at_trip"],
            "SubB_Z3R_closest_approach": res["B_Z3R_closest_approach"],
            "coordination_margin_samples_design_ratio": cf1["coordination"],
        },
    }
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(a.out, "replay_full_results.json"), "w") as f:
        json.dump(res, f, indent=2)

    # console summary
    print("Replay vs record, all digital channels match:", all_ok)
    for t, m in match.items():
        print(" ", t, {c: v["mismatches"] for c, v in m.items()})
    print("Fault inception k: A", kincA, " B", kincB, " trigger k", k_trig)
    print("First assertions A:", faA)
    print("First assertions B:", faB)
    print("Z_BC k400 A:", item3["A"])
    print("Z_BC k400 B:", item3["B"])
    print("IB at B k400:", res["item4_IB_L1_at_SubB_k400"])
    print("CT ratio evidence:", res["ct_ratio_evidence"])
    print("line check:", res["ct_ratio_evidence"]["line_impedance_check"]); print("clear:", res["item1_fault"]["fault_interrupted_first_postfault_k"], res["item1_fault"]["fault_duration_ms"])
    print("Fault locator A:", res["fault_locator_A"])
    print("B Z3R closest:", res["B_Z3R_closest_approach"])
    for cf in (cf1, cf2, cf3):
        print("CF:", cf["label"]); print("   A trips", cf["A_trips"], "B trips", cf["B_trips"], "B echo", cf["B_ECHO_ever"])
        print("   A first", cf["A_first_asserted_k"]); print("   B first", cf["B_first_asserted_k"])
        print("   Z_BC B k400", cf["B_Z_BC_sec_k400"])
    print("coordination", cf1["coordination"])
    print("phasors:", json.dumps(fault_type, indent=1))
    print("settings recalc:", calc)
    return res


if __name__ == "__main__":
    main()
