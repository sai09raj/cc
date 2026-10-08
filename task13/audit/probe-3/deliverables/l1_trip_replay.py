#!/usr/bin/env python3
"""
L1 trip investigation, 2026-09-14 14:22:07  -  sample-by-sample replay of the L1-21 relays.

Usage:
    python3 l1_trip_replay.py <case_dir> <out_dir>

<case_dir>  directory holding the extracted case file L1_trip_case_r3_2026-09-14.zip
<out_dir>   directory for the outputs (CSV, JSON, figures, console log)

What the program does
---------------------
1.  Reads the three COMTRADE 1999 ASCII records (SUBA L1-21, SUBB L2-21, SUBC L2-21) and the
    relay setting exports.
2.  Implements the L1-21 / L2-21 protection exactly as the instruction-manual excerpt specifies:
      - full-cycle Fourier phasor, fixed reference, for k >= 31 (manual sec. 1)
      - phase-to-phase loops AB, BC, CA, loop-current supervision 50PP, Z = V/I (sec. 2)
      - mho circles through the origin: forward Z1/Z2, reverse Z3R (sec. 2, Fig. 1)
      - per-sample logic order: zones, RX, echo, KEY, TRIP (sec. 5, Fig. 2)
      - channel: remote KEY at k  ->  local RX at k+12
      - echo: AND(/Z1, /Z2, /Z3R, /EBLK(Z3R), RX) -> EDPU pickup -> EDUR one-shot
      - KEY = Z2 + ECHO (ECHO only when ECHO=Y), TRIP = latch(Z1 + Z2*RX)
      - breaker (52A) opens 96 samples after TRIP
      - fault locator d = X_primary / x1 at the trip sample
    The two line ends are simulated in lock step so that the channel couples them.
3.  Validates the implementation on the two L2 relays (both records available) and on relay A,
    comparing every replayed digital channel with the recorded digital channels, and every SER
    entry of every event report with the replayed transition sample.
4.  Reconstructs relay B (L1-21 at Substation B) inputs:
      voltages  = Substation B 230 kV bus VT  = the VA/VB/VC of the SUBB L2-21 record
                  (one-line S-230-001: both Sub B line relays use the same bus VT)
      currents  = - m * (relay A currents)    (L1 charging negligible, same CTR 240 at both
                  ends, P1 toward the bus at both ends, so the L1 secondary current at B is
                  the negative of A's; m is the fraction of the CT secondary current that
                  flows through the relay input)
    As built (cable schedule bay L1 rev C) the BF-50 is connected in PARALLEL with the relay
    current inputs, so the CT secondary current divides in inverse proportion to the burdens
    (relay 0.04 ohm, BF-50 0.06 ohm, both resistive): m = 0.06/(0.04+0.06) = 0.60.
    By design (AC schematic B-E-3301) the devices are in SERIES: m = 1.00.
5.  Runs the actual case (m = 0.60), the counterfactual (m = 1.00) and the alternative
    hypotheses, writes the CSV/JSON outputs and the figures.
"""
import sys, os, re, json, math
import numpy as np

N_CYC = 32
F_SYS = 60.0
FS = N_CYC * F_SYS
CH_DELAY = 12          # samples, channel delay each direction (manual sec. 5)
BKR_DELAY = 96         # samples, breaker opening after TRIP (manual sec. 5)
X1_PER_KM = 0.48       # ohm/km, L1 and L2 positive-sequence reactance
Z1_PER_KM = complex(0.05, 0.48)
L1_KM, L2_KM = 80.0, 50.0
R_RELAY, R_BF50 = 0.04, 0.06   # ohm per phase, device technical data

# ----------------------------------------------------------------------------------------------
# input readers
# ----------------------------------------------------------------------------------------------
def read_comtrade(case, stem):
    cfg = open(os.path.join(case, stem + '.cfg')).read().splitlines()
    nA = int(re.findall(r'(\d+)A', cfg[1])[0]); nD = int(re.findall(r'(\d+)D', cfg[1])[0])
    ana = []
    for l in cfg[2:2 + nA]:
        p = l.split(',')
        ana.append(dict(name=p[1], a=float(p[5]), b=float(p[6]), unit=p[4], ps=p[12].strip()))
    dig = [cfg[2 + nA + i].split(',')[1] for i in range(nD)]
    i0 = 2 + nA + nD
    freq = float(cfg[i0]); rate, nsamp = cfg[i0 + 2].split(',')
    t_start = cfg[i0 + 3].split(',')[1]; t_trig = cfg[i0 + 4].split(',')[1]
    raw = np.loadtxt(os.path.join(case, stem + '.dat'), delimiter=',')
    rec = dict(stem=stem, freq=freq, rate=float(rate), nsamp=int(nsamp), t_start=t_start,
               t_trig=t_trig, n=raw[:, 0].astype(int), analog={}, digital={})
    for j, a in enumerate(ana):
        rec['analog'][a['name']] = raw[:, 2 + j] * a['a'] + a['b']
    for j, d in enumerate(dig):
        rec['digital'][d] = raw[:, 2 + nA + j].astype(int)
    assert rec['rate'] == FS and rec['nsamp'] == len(raw)
    return rec

def read_settings(path):
    s = {}
    for l in open(path):
        m = re.match(r'^(\w+)\s*=\s*([^;]+)', l)
        if m:
            k, v = m.group(1), m.group(2).strip()
            try:
                s[k] = float(v)
            except ValueError:
                s[k] = v
    return s

def read_ser(path):
    ev = []
    for l in open(path):
        m = re.match(r'^\d\d:\d\d:(\d\d\.\d{4})\s+(\S+)\s+(\S+)', l.strip())
        if m:
            ev.append((float(m.group(1)), m.group(2), m.group(3), l.strip()))
    return ev

def sec_to_sample(sec, t0=7.345):
    return int(round((sec - t0) * FS))

def sample_time_str(k, t0=7.345):
    # the relays' SER prints time truncated to 0.1 ms
    t = math.floor((t0 + k / FS) * 1e4 + 1e-6) / 1e4
    return '14:22:%07.4f' % t

# ----------------------------------------------------------------------------------------------
# relay algorithms (manual excerpt)
# ----------------------------------------------------------------------------------------------
_PH_CACHE = {}

def phasors(x):
    """X(k) = sqrt(2)/32 * sum_{i=0..31} x[k-i] exp(-j 2 pi (k-i)/32), computed per sample.
    Results are cached by waveform content (the same waveform is replayed in several scenarios)."""
    key = x.tobytes()
    if key not in _PH_CACHE:
        _PH_CACHE[key] = _phasors(x)
    return _PH_CACHE[key].copy()

def _phasors(x):
    n = len(x)
    X = np.full(n, np.nan + 1j * np.nan)
    for k in range(N_CYC - 1, n):
        acc = 0j
        for i in range(N_CYC):
            acc += x[k - i] * complex(math.cos(2 * math.pi * (k - i) / N_CYC),
                                      -math.sin(2 * math.pi * (k - i) / N_CYC))
        X[k] = math.sqrt(2) / N_CYC * acc
    return X

LOOPS = (('AB', 'A', 'B'), ('BC', 'B', 'C'), ('CA', 'C', 'A'))

def in_mho(Z, reach, ang_deg, reverse=False):
    c = (reach / 2) * complex(math.cos(math.radians(ang_deg)), math.sin(math.radians(ang_deg)))
    if reverse:
        c = -c
    return abs(Z - c) <= reach / 2

class Relay:
    """One L1-21 / L2-21 relay, evaluated once per sample in the manual's order."""
    def __init__(self, name, st, v, i):
        self.name, self.st = name, st
        self.n = len(v['A'])
        self.V = {p: phasors(v[p]) for p in 'ABC'}
        self.I = {p: phasors(i[p]) for p in 'ABC'}
        self.z3_on = not (isinstance(st['Z3P'], str) and st['Z3P'].upper() == 'OFF')
        self.echo_on = str(st['ECHO']).upper() == 'Y'
        n = self.n
        self.ch = {c: np.zeros(n, int) for c in
                   ('Z1', 'Z2', 'Z3R', 'RX', 'EBLK', 'EPU', 'ECHO', 'KEY', 'TRIP', '52A')}
        self.Zloop = {l[0]: np.full(n, np.nan + 1j * np.nan) for l in LOOPS}
        self.Iloop = {l[0]: np.full(n, np.nan) for l in LOOPS}
        self.loop_op = {(l[0], z): np.zeros(n, int) for l in LOOPS for z in ('Z1', 'Z2', 'Z3R')}
        self.epu_count = 0
        self.echo_left = 0
        self.last_z3 = -10 ** 9
        self.trip_latched = False
        self.trip_sample = None
        self.fault_location = None

    def zones(self, k):
        st = self.st
        z1 = z2 = z3 = 0
        if k >= N_CYC - 1:
            for lname, x, y in LOOPS:
                Vl = self.V[x][k] - self.V[y][k]
                Il = self.I[x][k] - self.I[y][k]
                self.Iloop[lname][k] = abs(Il)
                if abs(Il) >= st['50PP']:
                    Z = Vl / Il
                    self.Zloop[lname][k] = Z
                    o1 = in_mho(Z, st['Z1P'], st['Z1ANG'])
                    o2 = in_mho(Z, st['Z2P'], st['Z1ANG'])
                    o3 = self.z3_on and in_mho(Z, st['Z3P'], st['Z1ANG'], reverse=True)
                    self.loop_op[(lname, 'Z1')][k] = o1
                    self.loop_op[(lname, 'Z2')][k] = o2
                    self.loop_op[(lname, 'Z3R')][k] = o3
                    z1 |= o1; z2 |= o2; z3 |= o3
        c = self.ch
        c['Z1'][k], c['Z2'][k], c['Z3R'][k] = z1, z2, z3

    def logic(self, k, rx):
        st, c = self.st, self.ch
        c['RX'][k] = rx
        # echo logic (Fig. 2): EBLK dropout timer on Z3R
        if c['Z3R'][k]:
            self.last_z3 = k
        eblk = int(k - self.last_z3 <= int(st['EBLK']))
        c['EBLK'][k] = eblk
        and_in = rx and not c['Z1'][k] and not c['Z2'][k] and not c['Z3R'][k] and not eblk
        self.epu_count = self.epu_count + 1 if and_in else 0
        epu = int(self.epu_count >= int(st['EDPU']))
        c['EPU'][k] = epu
        rising = epu and (k == 0 or not c['EPU'][k - 1])
        if self.echo_on and rising and self.echo_left == 0:
            self.echo_left = int(st['EDUR'])
        echo = 0
        if self.echo_left > 0:
            echo = 1
            self.echo_left -= 1
        c['ECHO'][k] = echo
        # transmit
        c['KEY'][k] = int(c['Z2'][k] or echo)
        # trip
        if (c['Z1'][k] or (c['Z2'][k] and rx)) and not self.trip_latched:
            self.trip_latched = True
            self.trip_sample = k
            self.fault_location = self.locate(k)
        c['TRIP'][k] = int(self.trip_latched)
        # breaker
        c['52A'][k] = int(not (self.trip_sample is not None and k >= self.trip_sample + BKR_DELAY))

    def locate(self, k):
        best = None
        for lname, _, _ in LOOPS:
            Z = self.Zloop[lname][k]
            if np.isnan(Z.real):
                continue
            ops = self.loop_op[(lname, 'Z1')][k] or self.loop_op[(lname, 'Z2')][k]
            if ops and (best is None or self.Iloop[lname][k] > best[2]):
                best = (lname, Z, self.Iloop[lname][k])
        if best is None:
            return None
        lname, Z, _ = best
        Xp = Z.imag * self.st['PTR'] / self.st['CTR']
        return dict(loop=lname, sample=k, Z_sec=[Z.real, Z.imag], X_primary=Xp, km=Xp / X1_PER_KM)

def simulate_pair(rL, rR, ext_rx_L=None, ext_rx_R=None):
    """Lock-step simulation; RX at k = remote KEY at k-12. ext_rx_* overrides (validation)."""
    n = rL.n
    for k in range(n):
        rL.zones(k); rR.zones(k)
        rxL = ext_rx_L[k] if ext_rx_L is not None else (rR.ch['KEY'][k - CH_DELAY] if k >= CH_DELAY else 0)
        rxR = ext_rx_R[k] if ext_rx_R is not None else (rL.ch['KEY'][k - CH_DELAY] if k >= CH_DELAY else 0)
        rL.logic(k, int(rxL)); rR.logic(k, int(rxR))
    return rL, rR

def first(arr):
    idx = np.flatnonzero(arr)
    return int(idx[0]) if len(idx) else None

def transitions(arr):
    out = []
    for k in range(1, len(arr)):
        if arr[k] != arr[k - 1]:
            out.append((k, int(arr[k])))
    return out

# ----------------------------------------------------------------------------------------------
# relay-B input reconstruction
# ----------------------------------------------------------------------------------------------
def relay_b_inputs(recA, recB2, m, extend_after=None):
    v = {p: recB2['analog']['V' + p].copy() for p in 'ABC'}
    i = {p: -m * recA['analog']['I' + p].copy() for p in 'ABC'}
    if extend_after is not None:
        v = {p: sine_extend(v[p], extend_after) for p in 'ABC'}
        i = {p: sine_extend(i[p], extend_after) for p in 'ABC'}
    return v, i

def sine_extend(x, k_last):
    """Replace samples after k_last by the steady sinusoid of the phasor at k_last
    (used only for the counterfactual, where breaker A would not have opened)."""
    X = phasors(x)[k_last]
    y = x.copy()
    for k in range(k_last + 1, len(x)):
        y[k] = math.sqrt(2) * (X * complex(math.cos(2 * math.pi * k / N_CYC),
                                           math.sin(2 * math.pi * k / N_CYC))).real
    return y

def rec_vi(rec, extend_after=None):
    v = {p: rec['analog']['V' + p].copy() for p in 'ABC'}
    i = {p: rec['analog']['I' + p].copy() for p in 'ABC'}
    if extend_after is not None:
        v = {p: sine_extend(v[p], extend_after) for p in 'ABC'}
        i = {p: sine_extend(i[p], extend_after) for p in 'ABC'}
    return v, i

def summary(r):
    c = r.ch
    keys = ['Z1', 'Z2', 'Z3R', 'RX', 'ECHO', 'KEY', 'TRIP']
    out = {}
    for kk in keys:
        f = first(c[kk])
        last = int(np.flatnonzero(c[kk])[-1]) if f is not None else None
        out[kk] = dict(first_assert_sample=f, last_asserted_sample=last,
                       first_assert_time=sample_time_str(f) if f is not None else None)
    f52 = first(c['52A'] == 0)
    out['52A_open'] = dict(first_open_sample=f52, time=sample_time_str(f52) if f52 is not None else None)
    return out

# ----------------------------------------------------------------------------------------------
def main(case, outdir):
    os.makedirs(outdir, exist_ok=True)
    log_lines = []
    def log(*a):
        s = ' '.join(str(x) for x in a)
        print(s); log_lines.append(s)

    recA = read_comtrade(case, 'SUBA_L1-21_20260914_142207')
    recB2 = read_comtrade(case, 'SUBB_L2-21_20260914_142207')
    recC2 = read_comtrade(case, 'SUBC_L2-21_20260914_142207')
    stA = read_settings(os.path.join(case, 'SUBA_L1-21_settings.txt'))
    stB = read_settings(os.path.join(case, 'SUBB_L1-21_settings.txt'))
    stB2 = read_settings(os.path.join(case, 'SUBB_L2-21_settings.txt'))
    stC2 = read_settings(os.path.join(case, 'SUBC_L2-21_settings.txt'))
    serA = read_ser(os.path.join(case, 'SUBA_L1-21_event_report.txt'))
    serB = read_ser(os.path.join(case, 'SUBB_L1-21_event_report.txt'))
    serB2 = read_ser(os.path.join(case, 'SUBB_L2-21_event_report.txt'))
    serC2 = read_ser(os.path.join(case, 'SUBC_L2-21_event_report.txt'))
    for r in (recA, recB2, recC2):
        assert r['t_start'] == '14:22:07.345000', r['t_start']
    n = recA['nsamp']
    R = {}   # results for JSON

    # ------------------------------------------------------------------ fault inception / type
    log('=== FAULT INCEPTION AND TYPE')
    incep = {}
    for nm, rec in (('SUBA_L1', recA), ('SUBB_L2', recB2), ('SUBC_L2', recC2)):
        first_k = {}
        for ch in ('VA', 'VB', 'VC', 'IA', 'IB', 'IC'):
            x = rec['analog'][ch]
            thr = 5.0 if ch[0] == 'V' else 0.2     # V sec / A sec, one-cycle superimposed change
            d = np.abs(x[N_CYC:] - x[:-N_CYC])
            idx = np.flatnonzero(d > thr)
            first_k[ch] = int(idx[0] + N_CYC) if len(idx) else None
        incep[nm] = first_k
        log(nm, 'first sample with one-cycle superimposed change > 5 V / 0.2 A:', first_k)
    k_f = min(v for d in incep.values() for c, v in d.items() if v is not None)
    log('fault inception: relay sample k =', k_f, '(record line n =', k_f + 1, '), time', sample_time_str(k_f),
        '; trigger time in cfg', recA['t_trig'])
    PA = {c: phasors(recA['analog'][c]) for c in recA['analog']}
    PB2 = {c: phasors(recB2['analog'][c]) for c in recB2['analog']}
    PC2 = {c: phasors(recC2['analog'][c]) for c in recC2['analog']}
    win = range(370, 430)    # steady fault window (full post-fault cycle, before any breaker opens)
    def avg(f):
        return complex(np.mean([f(k) for k in win]))
    ftype = {}
    for nm, P in (('SUBA_L1', PA), ('SUBB_L2', PB2), ('SUBC_L2', PC2)):
        pre = 300
        d = dict(
            IA_pre=abs(P['IA'][pre]), IB_pre=abs(P['IB'][pre]), IC_pre=abs(P['IC'][pre]),
            IA_flt=abs(avg(lambda k: P['IA'][k])), IB_flt=abs(avg(lambda k: P['IB'][k])),
            IC_flt=abs(avg(lambda k: P['IC'][k])),
            I0_flt=abs(avg(lambda k: (P['IA'][k] + P['IB'][k] + P['IC'][k]) / 3)),
            VA_flt=abs(avg(lambda k: P['VA'][k])), VB_flt=abs(avg(lambda k: P['VB'][k])),
            VC_flt=abs(avg(lambda k: P['VC'][k])), VA_pre=abs(P['VA'][pre]))
        ftype[nm] = {k: round(v, 3) for k, v in d.items()}
        log(nm, 'pre-fault (k=300) and fault (k=370..429) RMS secondary:', ftype[nm])

    # ------------------------------------------------------------------ fault location on L2
    log('=== FAULT LOCATION')
    zkm_sec = Z1_PER_KM * stB2['CTR'] / stB2['PTR']
    ds, rfs = [], []
    for k in win:
        VB = PB2['VB'][k] - PB2['VC'][k]; IB_ = PB2['IB'][k] - PB2['IC'][k]
        VC = PC2['VB'][k] - PC2['VC'][k]; IC_ = PC2['IB'][k] - PC2['IC'][k]
        d = (VB - VC + L2_KM * zkm_sec * IC_) / (zkm_sec * (IB_ + IC_))
        dr = d.real
        VF = VB - dr * zkm_sec * IB_
        rf_loop = (VF / (IB_ + IC_))        # loop (B-C) fault resistance / 2 ... see report
        ds.append(d); rfs.append(rf_loop)
    d2 = complex(np.mean(ds)); rf = complex(np.mean(rfs))
    Rf_primary = 2 * rf.real * stB2['PTR'] / stB2['CTR']
    log('two-ended (B,C) BC-loop location on L2: d = %.3f km from Substation B (imag part %.3f km), '
        'spread over window %.3f..%.3f km' % (d2.real, d2.imag, min(x.real for x in ds), max(x.real for x in ds)))
    log('phase-to-phase fault resistance R_f = %.2f ohm primary (%.3f ohm sec); reactive part of V_F/I_F %.3f ohm sec'
        % (Rf_primary, 2 * rf.real, 2 * rf.imag))
    # single-ended reactance at B L2 relay (infeed / resistance affected)
    zB2 = avg(lambda k: (PB2['VB'][k] - PB2['VC'][k]) / (PB2['IB'][k] - PB2['IC'][k]))
    zC2 = avg(lambda k: (PC2['VB'][k] - PC2['VC'][k]) / (PC2['IB'][k] - PC2['IC'][k]))
    zA = avg(lambda k: (PA['VB'][k] - PA['VC'][k]) / (PA['IB'][k] - PA['IC'][k]))
    fl = dict(two_ended_km_from_B=d2.real, two_ended_imag_km=d2.imag,
              Rf_phase_to_phase_ohm_primary=Rf_primary,
              B_L2_apparent_Z_sec=[zB2.real, zB2.imag],
              B_L2_reactance_km=zB2.imag * stB2['PTR'] / stB2['CTR'] / X1_PER_KM,
              C_L2_apparent_Z_sec=[zC2.real, zC2.imag],
              C_L2_reactance_km_from_C=zC2.imag * stC2['PTR'] / stC2['CTR'] / X1_PER_KM,
              A_L1_apparent_Z_sec=[zA.real, zA.imag],
              A_L1_reactance_km_from_A=zA.imag * stA['PTR'] / stA['CTR'] / X1_PER_KM)
    log('apparent BC-loop impedances (k=370..429 mean, sec): A(L1) %s, B(L2) %s, C(L2) %s' %
        (np.round(zA, 3), np.round(zB2, 3), np.round(zC2, 3)))
    log('reactance distances: A->%.1f km, B(L2)->%.2f km, C(L2)->%.2f km' %
        (fl['A_L1_reactance_km_from_A'], fl['B_L2_reactance_km'], fl['C_L2_reactance_km_from_C']))

    # L1 healthy check: V_A - V_B = ZL1 * I_A for all three loops (no current leaves L1)
    zl1_sec = L1_KM * Z1_PER_KM * stA['CTR'] / stA['PTR']
    res = []
    for k in win:
        for _, x, y in LOOPS:
            dv = (PA['V' + x][k] - PA['V' + y][k]) - (PB2['V' + x][k] - PB2['V' + y][k])
            drop = zl1_sec * (PA['I' + x][k] - PA['I' + y][k])
            res.append(abs(dv - drop) / abs(dv))
    l1chk = dict(ZL1_sec=[zl1_sec.real, zl1_sec.imag], max_relative_residual=max(res))
    log('L1 check V_A - V_B = ZL1*I_A over fault window: max relative residual %.4f' % max(res))
    # implied L1 impedance from A and B data (BC loop)
    zl1_meas = avg(lambda k: ((PA['VB'][k] - PA['VC'][k]) - (PB2['VB'][k] - PB2['VC'][k])) /
                   (PA['IB'][k] - PA['IC'][k]))
    l1chk['ZL1_measured_sec_BC'] = [zl1_meas.real, zl1_meas.imag]
    l1chk['ZL1_measured_primary_BC'] = [zl1_meas.real * stA['PTR'] / stA['CTR'], zl1_meas.imag * stA['PTR'] / stA['CTR']]
    infeed = avg(lambda k: (PB2['IB'][k] - PB2['IC'][k]) / (PA['IB'][k] - PA['IC'][k]))
    l1chk['infeed_ratio_IL2B_over_IL1_BC'] = [abs(infeed), math.degrees(math.atan2(infeed.imag, infeed.real))]
    log('infeed at B: I_L2(B)/I_L1(A) BC loop = %.3f at %.1f deg (T1 infeed fraction of L2 current %.3f)' %
        (abs(infeed), math.degrees(math.atan2(infeed.imag, infeed.real)), abs(1 - 1 / infeed)))
    log('ZL1 measured from A and B records (BC loop): %s ohm sec = %s ohm primary (data: 4.00+j38.40)' %
        (np.round(zl1_meas, 4), np.round(zl1_meas * stA['PTR'] / stA['CTR'], 2)))

    # ------------------------------------------------------------------ validation on L2 relays
    log('=== VALIDATION 1: L2 relays (B and C), replayed in lock step from their own records')
    vB2, iB2 = rec_vi(recB2); vC2, iC2 = rec_vi(recC2)
    rB2, rC2 = simulate_pair(Relay('SUBB-L2-21', stB2, vB2, iB2), Relay('SUBC-L2-21', stC2, vC2, iC2))
    val = {}
    for r, rec in ((rB2, recB2), (rC2, recC2)):
        mism = {c: int(np.sum(r.ch[c] != rec['digital'][c])) for c in ('Z1', 'Z2', 'KEY', 'RX', 'TRIP', '52A')}
        val[r.name] = dict(mismatching_samples_vs_recorded_digitals=mism)
        log(r.name, 'mismatching samples replay vs recorded digital channels:', mism)

    # ------------------------------------------------------------------ actual case (as built)
    m_asbuilt = R_BF50 / (R_RELAY + R_BF50)
    log('=== ACTUAL CASE: relay B inputs reconstructed with relay share m = %.3f (as-built parallel BF-50)' % m_asbuilt)
    vA, iA = rec_vi(recA)
    vB, iB = relay_b_inputs(recA, recB2, m_asbuilt)
    rA, rB = simulate_pair(Relay('SUBA-L1-21', stA, vA, iA), Relay('SUBB-L1-21', stB, vB, iB))
    mismA = {c: int(np.sum(rA.ch[c] != recA['digital'][c])) for c in ('Z1', 'Z2', 'KEY', 'RX', 'TRIP', '52A')}
    log('relay A replay vs recorded digital channels, mismatching samples:', mismA)
    val['SUBA-L1-21'] = dict(mismatching_samples_vs_recorded_digitals=mismA)

    # SER comparison
    def ser_compare(r, ser, label):
        rows = []
        for sec, el, state, line in ser:
            k_ser = sec_to_sample(sec)
            name = el
            if el not in r.ch:
                continue
            want = 1 if state in ('asserted', 'closed') else 0
            arr = r.ch[name]
            tr = [k for k, v in transitions(arr) if v == want]
            if name == '52A' and want == 1:
                tr = [0] if arr[0] == 1 else tr
                k_rep = tr[0] if tr else None
                rows.append(dict(element=el, state=state, ser_time=line.split()[0], ser_sample=k_ser,
                                 replay_sample=k_rep, replay_time=None, match='record start (closed)' if k_rep == 0 else 'NO'))
                continue
            k_rep = min(tr, key=lambda k: abs(k - k_ser)) if tr else None
            t_rep = sample_time_str(k_rep) if k_rep is not None else None
            ok = t_rep is not None and t_rep == line.split()[0]
            rows.append(dict(element=el, state=state, ser_time=line.split()[0], ser_sample=k_ser,
                             replay_sample=k_rep, replay_time=t_rep, match=bool(ok)))
        log('SER comparison', label)
        for row in rows:
            log('   %-6s %-11s SER %s (k=%s)  replay k=%s %s  match=%s' % (row['element'], row['state'], row['ser_time'],
                row['ser_sample'], row['replay_sample'], row['replay_time'], row['match']))
        return rows
    serc = {}
    serc['SUBA-L1-21'] = ser_compare(rA, serA, 'relay A (L1, Sub A)')
    serc['SUBB-L1-21'] = ser_compare(rB, serB, 'relay B (L1, Sub B)')
    serc['SUBB-L2-21'] = ser_compare(rB2, serB2, 'L2-21 Sub B')
    serc['SUBC-L2-21'] = ser_compare(rC2, serC2, 'L2-21 Sub C')
    # elements not in SER of relay B must never assert
    log('relay B elements absent from its SER: Z1 first=%s, Z2 first=%s, Z3R first=%s, TRIP first=%s' %
        (first(rB.ch['Z1']), first(rB.ch['Z2']), first(rB.ch['Z3R']), first(rB.ch['TRIP'])))
    log('relay A fault locator (replay): %s ; event report: 92.0 km BC' % rA.fault_location)

    sumA, sumB = summary(rA), summary(rB)
    log('relay A first assertions:', {k: v.get('first_assert_sample', v.get('first_open_sample')) for k, v in sumA.items()})
    log('relay B first assertions:', {k: v.get('first_assert_sample', v.get('first_open_sample')) for k, v in sumB.items()})

    # B apparent impedance during the fault, actual and correct wiring
    def zb_stats(r, label):
        zs = r.Zloop['BC'][win.start:win.stop]
        zm = complex(np.nanmean(zs))
        st = r.st
        c3 = -(st['Z3P'] / 2) * complex(math.cos(math.radians(st['Z1ANG'])), math.sin(math.radians(st['Z1ANG'])))
        dist = abs(zm - c3)
        # smallest Z3P (reverse mho at Z1ANG) that would contain zm:  |z + R/2 u| <= R/2  <=> R >= |z|^2 / (-Re(z conj(u)))
        u = complex(math.cos(math.radians(st['Z1ANG'])), math.sin(math.radians(st['Z1ANG'])))
        proj = -(zm * u.conjugate()).real
        rmin = abs(zm) ** 2 / proj if proj > 0 else float('inf')
        log('%s: BC-loop Z (k=370..429 mean) = %.3f%+.3fj ohm sec, |Z|=%.3f at %.1f deg; distance to Z3R centre %.3f vs radius %.3f;'
            ' minimum reverse reach that would contain it %.3f ohm sec' %
            (label, zm.real, zm.imag, abs(zm), math.degrees(math.atan2(zm.imag, zm.real)), dist, st['Z3P'] / 2, rmin))
        return dict(Z_sec=[zm.real, zm.imag], mag=abs(zm), ang_deg=math.degrees(math.atan2(zm.imag, zm.real)),
                    dist_to_Z3R_centre=dist, Z3R_radius=st['Z3P'] / 2, min_Z3P_to_include=rmin,
                    loop_current_A_sec=float(np.nanmean(r.Iloop['BC'][win.start:win.stop])))
    zb_actual = zb_stats(rB, 'relay B as built (m=0.60)')

    # ------------------------------------------------------------------ counterfactual
    k_ext = None
    if rA.trip_sample is not None:
        k_ext = rA.trip_sample + BKR_DELAY - 1      # last sample before breaker A opened in reality
    log('=== COUNTERFACTUAL: correct series CT circuit (m = 1.00); after sample %s the analog data are continued'
        ' with the steady pre-opening sinusoid because breaker A would not have opened' % k_ext)
    vAc, iAc = rec_vi(recA, extend_after=k_ext)
    vBc, iBc = relay_b_inputs(recA, recB2, 1.0, extend_after=k_ext)
    rAc, rBc = simulate_pair(Relay('SUBA-L1-21', stA, vAc, iAc), Relay('SUBB-L1-21', stB, vBc, iBc))
    sumAc, sumBc = summary(rAc), summary(rBc)
    log('relay A (counterfactual) first assertions:', {k: v.get('first_assert_sample', v.get('first_open_sample')) for k, v in sumAc.items()})
    log('relay B (counterfactual) first assertions:', {k: v.get('first_assert_sample', v.get('first_open_sample')) for k, v in sumBc.items()})
    zb_correct = zb_stats(rBc, 'relay B correct wiring (m=1.00)')
    # Z3R / EBLK status at relay B when RX arrives
    k_rx = first(rBc.ch['RX'])
    log('counterfactual relay B: RX first at %s, Z3R at that sample=%d, EBLK=%d; Z3R asserted %d samples before RX'
        % (k_rx, rBc.ch['Z3R'][k_rx], rBc.ch['EBLK'][k_rx], k_rx - first(rBc.ch['Z3R'])))
    # same counterfactual without the data extension (record only) for transparency
    vBc2, iBc2 = relay_b_inputs(recA, recB2, 1.0)
    rAc2, rBc2 = simulate_pair(Relay('SUBA-L1-21', stA, vA, iA), Relay('SUBB-L1-21', stB, vBc2, iBc2))
    log('counterfactual on unextended record: A TRIP=%s, B ECHO=%s, B KEY=%s' %
        (first(rAc2.ch['TRIP']), first(rBc2.ch['ECHO']), first(rBc2.ch['KEY'])))

    # ------------------------------------------------------------------ hypotheses / sensitivity
    log('=== ALTERNATIVE HYPOTHESES AND SENSITIVITY')
    def run_case(m, stB_mod=None, stA_mod=None, extend=None):
        sb = dict(stB); sb.update(stB_mod or {})
        sa = dict(stA); sa.update(stA_mod or {})
        if extend is None:
            va, ia = rec_vi(recA)
        else:
            va, ia = rec_vi(recA, extend_after=extend)
        vb, ib = relay_b_inputs(recA, recB2, m, extend_after=extend)
        a, b = simulate_pair(Relay('A', sa, va, ia), Relay('B', sb, vb, ib))
        return a, b
    def brief(a, b):
        return dict(A_Z2=first(a.ch['Z2']), A_RX=first(a.ch['RX']), A_TRIP=first(a.ch['TRIP']),
                    B_Z1=first(b.ch['Z1']), B_Z2=first(b.ch['Z2']), B_Z3R=first(b.ch['Z3R']),
                    B_RX=first(b.ch['RX']), B_ECHO=first(b.ch['ECHO']), B_KEY=first(b.ch['KEY']), B_TRIP=first(b.ch['TRIP']))
    target = dict(A_TRIP=406, B_ECHO=394, B_KEY=394, B_Z2=None, B_Z3R=None, B_TRIP=None, B_RX=363)
    def matches_ser(br):
        return all(br[k] == v for k, v in target.items())
    hyp = {}
    cases = [
        ('H0_as_built_parallel_BF50_m0.60', dict(m=m_asbuilt)),
        ('H1_correct_series_m1.00', dict(m=1.0, extend=k_ext)),
        ('H2_wrong_CT_tap_X1X5_2000to5_series_m0.60', dict(m=1200 / 2000)),
        ('H3_reversed_CT_polarity_at_B_series', dict(m=-1.0)),
        ('H4_reversed_polarity_and_parallel_BF50', dict(m=-m_asbuilt)),
        ('H9_open_or_shorted_CT_circuit_at_B_m0', dict(m=0.0)),
        ('H10_Z3R_disabled_at_B_correct_wiring', dict(m=1.0, stB_mod={'Z3P': 'OFF'}, extend=k_ext)),
        ('H5_previous_setting_Z3P_1.80_with_parallel_BF50', dict(m=m_asbuilt, stB_mod={'Z3P': 1.80})),
        ('H6_previous_setting_Z3P_1.80_correct_wiring', dict(m=1.0, stB_mod={'Z3P': 1.80}, extend=k_ext)),
        ('H7_interim_ECHO_N_at_B_with_parallel_BF50', dict(m=m_asbuilt, stB_mod={'ECHO': 'N'}, extend=k_ext)),
        ('H8_echo_disabled_correct_wiring', dict(m=1.0, stB_mod={'ECHO': 'N'}, extend=k_ext)),
    ]
    for name, kw in cases:
        a, b = run_case(kw['m'], kw.get('stB_mod'), kw.get('stA_mod'), kw.get('extend'))
        br = brief(a, b)
        hyp[name] = dict(relay_B_current_share_m=kw['m'], settings_override=kw.get('stB_mod'), result=br,
                         reproduces_recorded_event=matches_ser(br))
        log('%-52s %s  reproduces SER/record: %s' % (name, br, matches_ser(br)))
    # sweep of the relay-B current share
    sweep = []
    ms = np.round(np.arange(0.00, 1.0001, 0.01), 2)
    for m in ms:
        a, b = run_case(float(m), extend=k_ext if m > 0.999 else None)
        br = brief(a, b)
        sweep.append(dict(m=float(m), **br, reproduces=matches_ser(br)))
    ok = [s['m'] for s in sweep if s['reproduces']]
    log('relay-B current share m reproducing the recorded event (sweep 0.00..1.00 step 0.01): %.2f .. %.2f' % (min(ok), max(ok)))
    log('smallest m for which B Z3R blocks the echo:', min(s['m'] for s in sweep if s['B_ECHO'] is None))

    # effective reaches of relay B with the parallel BF-50 (reach scales with m)
    eff = dict(Z1P_effective_sec=stB['Z1P'] * m_asbuilt, Z2P_effective_sec=stB['Z2P'] * m_asbuilt,
               Z3P_effective_sec=stB['Z3P'] * m_asbuilt,
               Z1_percent_of_L1=100 * stB['Z1P'] * m_asbuilt / abs(zl1_sec),
               Z2_percent_of_L1=100 * stB['Z2P'] * m_asbuilt / abs(zl1_sec))
    log('relay B effective reaches with m=%.2f: %s' % (m_asbuilt, {k: round(v, 3) for k, v in eff.items()}))

    # Z3R coordination coverage on the line angle (settings calculation check)
    zl1p = abs(L1_KM * Z1_PER_KM)
    z2a_prim = stA['Z2P'] * stA['PTR'] / stA['CTR']
    cover = dict(A_Z2_reach_primary=z2a_prim, overreach_beyond_B_primary=z2a_prim - zl1p,
                 B_Z3R_reach_primary=stB['Z3P'] * stB['PTR'] / stB['CTR'],
                 margin_ratio_correct_wiring=(stB['Z3P'] * stB['PTR'] / stB['CTR']) / (z2a_prim - zl1p),
                 margin_ratio_as_built=(stB['Z3P'] * stB['PTR'] / stB['CTR']) * m_asbuilt / (z2a_prim - zl1p))
    log('on-angle coordination (primary ohm): %s' % {k: round(v, 3) for k, v in cover.items()})

    # CT duty at Sub B (saturation check)
    ipk = max(abs(PA['IB'][k]) for k in win)
    loopR = 0.38   # highest loop R, CT 52-L1 core 1 at Sub B (commissioning record 2023-04-14)
    burden_par = loopR + R_RELAY * R_BF50 / (R_RELAY + R_BF50)
    burden_ser = loopR + R_RELAY + R_BF50
    xr = math.tan(math.radians(84.05))
    vs = ipk * burden_ser * (1 + xr)
    ct = dict(max_phase_current_A_sec=ipk, burden_series_ohm=burden_ser, burden_parallel_ohm=burden_par,
              X_over_R=xr, required_voltage_full_offset_V=vs, C800_on_1200_tap_V=800 * 1200 / 2000)
    log('CT 52-L1 core 1 at B duty: %s' % {k: round(v, 3) for k, v in ct.items()})

    # ------------------------------------------------------------------ CSV outputs
    def write_csv(path, rA_, rB_):
        cols_A = ['Z1', 'Z2', 'RX', 'KEY', 'TRIP', '52A']
        cols_B = ['Z1', 'Z2', 'Z3R', 'EBLK', 'RX', 'ECHO', 'KEY', 'TRIP', '52A']
        with open(path, 'w') as f:
            f.write('n,k,time,' + ','.join('A_' + c for c in cols_A) + ',' + ','.join('B_' + c for c in cols_B)
                    + ',A_BC_Z_re,A_BC_Z_im,B_BC_Z_re,B_BC_Z_im\n')
            for k in range(n):
                za, zb = rA_.Zloop['BC'][k], rB_.Zloop['BC'][k]
                f.write('%d,%d,%s,' % (k + 1, k, sample_time_str(k)) +
                        ','.join(str(rA_.ch[c][k]) for c in cols_A) + ',' +
                        ','.join(str(rB_.ch[c][k]) for c in cols_B) + ',' +
                        ','.join('' if np.isnan(v) else '%.4f' % v for v in (za.real, za.imag, zb.real, zb.imag)) + '\n')
    write_csv(os.path.join(outdir, 'replay_digital_channels_actual.csv'), rA, rB)
    write_csv(os.path.join(outdir, 'replay_digital_channels_counterfactual.csv'), rAc, rBc)

    # ------------------------------------------------------------------ figures
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(13, 6))
        u = np.exp(1j * np.radians(stB['Z1ANG']))
        th = np.linspace(0, 2 * np.pi, 400)
        for reach, sty, lab, sgn in ((stB['Z1P'], '-', 'Z1 (3.71)', 1), (stB['Z2P'], '--', 'Z2 (5.79)', 1),
                                     (stB['Z3P'], '-.', 'Z3R (1.74)', -1), (1.80, ':', 'Z3R old R4 (1.80)', -1)):
            c = sgn * reach / 2 * u
            ax[0].plot((c + reach / 2 * np.exp(1j * th)).real, (c + reach / 2 * np.exp(1j * th)).imag, 'k' + sty, lw=1, label=lab)
        for r_, col, lab in ((rB, 'C3', 'relay B as built (m=0.60)'), (rBc, 'C2', 'relay B correct wiring (m=1.00)')):
            z = r_.Zloop['BC'][330:446]
            ax[0].plot(z.real, z.imag, '.', color=col, ms=3, label=lab + ', BC loop k=330..445')
        za = rA.Zloop['BC'][330:446]
        ax[0].plot(za.real, za.imag, '.', color='C0', ms=3, label='relay A, BC loop k=330..445')
        ax[0].set_xlim(-3, 4); ax[0].set_ylim(-2.5, 6.5); ax[0].set_aspect('equal'); ax[0].grid(alpha=.3)
        ax[0].axhline(0, color='k', lw=.5); ax[0].axvline(0, color='k', lw=.5)
        ax[0].set_xlabel('R (ohm sec)'); ax[0].set_ylabel('X (ohm sec)'); ax[0].legend(fontsize=7, loc='upper left')
        ax[0].set_title('BC-loop apparent impedance vs. relay B characteristics')
        axz = ax[1]
        rows = [('A Z2', rA.ch['Z2']), ('A KEY', rA.ch['KEY']), ('A RX', rA.ch['RX']), ('A TRIP', rA.ch['TRIP']),
                ('A 52A', rA.ch['52A']), ('B Z3R', rB.ch['Z3R']), ('B RX', rB.ch['RX']), ('B ECHO', rB.ch['ECHO']),
                ('B KEY', rB.ch['KEY']), ('B Z3R (m=1)', rBc.ch['Z3R']), ('B ECHO (m=1)', rBc.ch['ECHO']),
                ('A TRIP (m=1)', rAc.ch['TRIP'])]
        for i_, (lab, arr) in enumerate(rows):
            y0 = len(rows) - i_
            axz.step(np.arange(n), y0 + 0.7 * arr, where='post', lw=1.2)
            axz.text(255, y0 + 0.2, lab, fontsize=8, ha='right')
        axz.axvline(k_f, color='grey', ls=':'); axz.text(k_f + 2, 0.4, 'fault k=%d' % k_f, fontsize=7)
        axz.set_xlim(260, 540); axz.set_yticks([]); axz.set_xlabel('relay sample k')
        axz.set_title('Replayed digital channels (actual, and m=1 counterfactual)')
        fig.tight_layout(); fig.savefig(os.path.join(outdir, 'fig_replay_overview.png'), dpi=130)
        plt.close(fig)
    except Exception as e:  # figures are optional
        log('figure generation failed:', e)

    # ------------------------------------------------------------------ JSON
    def chsum(r):
        return {c: (dict(first_assert_sample=first(r.ch[c]),
                         first_assert_time=sample_time_str(first(r.ch[c])) if first(r.ch[c]) is not None else None)
                    if c != '52A' else dict(first_open_sample=first(r.ch['52A'] == 0)))
                for c in ('Z1', 'Z2', 'Z3R', 'RX', 'ECHO', 'KEY', 'TRIP', '52A')}
    R = dict(
        event='230 kV line L1 breaker trip at Substation A, 2026-09-14 14:22:07',
        conventions=dict(relay_sample_k='k = n - 1, n = first column of the .dat (1-based); time = 14:22:07.345000 + k/1920 s',
                         channel_delay_samples=CH_DELAY, breaker_delay_samples=BKR_DELAY),
        item1_fault=dict(fault_type='phase-to-phase B-C (no ground, I0 ~ 0), through fault resistance',
                         faulted_line='L2 (Substation B - Substation C)',
                         distance_from_substation_B_km=round(d2.real, 2),
                         distance_from_substation_B_km_patrol=6.5,
                         fault_inception_sample_k=k_f, fault_inception_record_line_n=k_f + 1,
                         fault_inception_time=sample_time_str(k_f),
                         fault_resistance_ohm_primary=round(Rf_primary, 2),
                         superimposed_change_first_samples=incep,
                         fault_currents_and_voltages=ftype, location_details=fl, L1_consistency_check=l1chk),
        item2_first_assertions=dict(
            relay_A=chsum(rA), relay_B=chsum(rB),
            relay_A_elements_not_applicable='Z3R (Z3P=OFF) and ECHO (ECHO=N) are disabled at relay A',
            relay_A_fault_locator=rA.fault_location,
            relay_B_input_reconstruction=dict(voltages='SUBB L2-21 record VA/VB/VC (common Sub B bus VT)',
                                              currents='-m x SUBA L1-21 record IA/IB/IC', m=m_asbuilt,
                                              m_basis='as-built parallel BF-50: 0.06/(0.04+0.06)')),
        replay_validation=dict(digital_channel_mismatch=val, SER_comparison=serc),
        item3_root_cause=dict(
            summary=('At Substation B the numerical BF-50 breaker-failure relay installed on 2025-02-12 (cable schedule '
                     'bay L1 rev C) was wired in PARALLEL with the L1-21 relay B current inputs instead of in SERIES as '
                     'drawn on AC schematic B-E-3301. The CT secondary current divides between the 0.04 ohm relay and '
                     'the 0.06 ohm BF-50, so relay B measured only %.0f %% of the L1 current. Its apparent impedance for '
                     'the reverse L2 fault was magnified by 1/%.2f and fell outside the reverse zone 3 (Z3P 1.74), so '
                     'Z3R/EBLK did not block the weak-infeed echo; relay B echoed relay A\'s Z2 permissive and relay A '
                     'tripped by POTT for an external fault on L2.' % (100 * m_asbuilt, m_asbuilt)),
            relay_B_BC_loop_impedance_as_built=zb_actual,
            relay_B_BC_loop_impedance_correct_wiring=zb_correct,
            relay_B_effective_reaches_as_built=eff,
            on_angle_coordination=cover,
            relay_B_current_share_consistent_with_records=dict(min=min(ok), max=max(ok)),
            CT_duty=ct,
            hypotheses=hyp),
        item4_without_root_cause=dict(
            relay_A=chsum(rAc), relay_B=chsum(rBc),
            relay_A_trips=first(rAc.ch['TRIP']) is not None, relay_B_echoes=first(rBc.ch['ECHO']) is not None,
            relay_B_Z3R_lead_over_RX_samples=k_rx - first(rBc.ch['Z3R']),
            note='m = 1.00 (series CT circuit); after k=%d analog data continued as steady sinusoid (breaker A would stay closed)' % k_ext),
        item5_corrective_action=dict(
            wiring=('Re-terminate CT 52-L1 core 1 at Substation B in series per B-E-3301: L1-21:Z02/Z04/Z06 -> '
                    'BF50-L1:A1/B1/C1 and BF50-L1:A2/B2/C2 -> TB-L1:10; remove the parallel connections '
                    'TS-L1:2/4/6 -> BF50-L1:A1/B1/C1 and L1-21:Z02/Z04/Z06 -> TB-L1:10; issue cable schedule rev D.'),
            settings=dict(relay_B_interim_until_rewired=dict(ECHO='N'),
                          relay_B_after_rewiring_and_recommissioning=dict(ECHO='Y', Z3P=stB['Z3P'], Z1P=stB['Z1P'],
                                                                          Z2P=stB['Z2P'], EDPU=int(stB['EDPU']),
                                                                          EDUR=int(stB['EDUR']), EBLK=int(stB['EBLK'])),
                          relay_A='no change'),
            interim_ECHO_N_replay=hyp['H7_interim_ECHO_N_at_B_with_parallel_BF50']['result'],
            verification='primary (or CT-terminal secondary) injection through the complete series chain, then '
                         'on-load check: relay B phase currents equal in magnitude to relay A within 1-2 % and 180 deg '
                         'opposite; BF-50 currents equal to relay B currents.'),
    )
    with open(os.path.join(outdir, 'l1_trip_results.json'), 'w') as f:
        json.dump(R, f, indent=2, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    with open(os.path.join(outdir, 'replay_console_log.txt'), 'w') as f:
        f.write('\n'.join(log_lines) + '\n')
    return R

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2])
