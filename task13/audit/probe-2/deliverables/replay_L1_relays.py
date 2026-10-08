#!/usr/bin/env python3
"""
Replay of the 230 kV line L1 relays (L1-21 relay A at Substation A, L1-21 relay B at
Substation B) for the 2026-09-14 14:22:07 event, sample by sample, exactly as specified in
the L1-21 instruction manual excerpt:

  * full-cycle Fourier phasors in a fixed reference frame (32 samples/cycle, from k = 31)
  * phase-to-phase loops AB, BC, CA, loop current supervision 50PP, Z = V / I
  * mho zones Z1, Z2 (forward) and Z3R (reverse), maximum torque angle Z1ANG
  * POTT logic per Figure 2, evaluated per sample in the order
        zone elements -> RX -> echo logic -> KEY -> TRIP
    channel delay 12 samples each direction, TRIP latch, breaker opens 96 samples after TRIP.
  * Echo (ECHO = Y): AND(not Z1, not Z2, not Z3R, not EBLK-dropout(Z3R), RX)
        -> EDPU pickup (asserts on the EDPU-th consecutive sample)
        -> EDUR one-shot (EDUR samples from a rising input, non-retriggerable)

Relay A is replayed from its own oscillography.  Relay B's oscillography was not retrieved;
its inputs are reconstructed:
  * voltages: Substation B 230 kV bus VT (VT-B, 2000:1) as recorded by the Substation B
    L2-21 relay, which takes its voltages from the same bus VT (one-line S-230-001);
  * currents: L1 has no fault and negligible charging (one-line note, operations log
    "no fault found on L1"), so the primary current entering L1 at B equals minus the
    primary current entering L1 at A, sample by sample (records are GPS synchronised and
    share start time and rate).  Relay A's CT (1200:5, X1-X5 landed, CTR 240) matches its
    setting, so I_A,primary = 240 * i_A,sec.  Relay B's secondary current is
    I_B,primary / N_B where N_B is the ratio of the CT tap actually landed on relay B
    (commissioning record 2023-04-14: 52-L1 core 1 landed X1-X5 = 2000:5, N_B = 400).

The two L2 relays (Sub B, Sub C) are replayed with the same engine as validation of the
engine against two further independent records with recorded digital channels.

Usage:  python3 replay_L1_relays.py <case_dir> <out_dir>
"""
import sys, os, json, csv, math
import numpy as np

N = 32                 # samples per cycle
FS = 1920.0            # samples per second
CH_DELAY = 12          # channel delay, samples, each direction
BKR_DELAY = 96         # breaker opening time after TRIP, samples
T0_SEC = 7.345000      # record start, seconds within minute 14:22 (all records)

# ----------------------------------------------------------------------------------------
# File readers
# ----------------------------------------------------------------------------------------
def read_comtrade(cfg_path):
    """Minimal COMTRADE 1999 ASCII reader.  Returns dict of analog (secondary units:
    volts, amperes) and digital channels as numpy arrays indexed by relay sample k."""
    with open(cfg_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    tot, na, nd = lines[1].split(',')
    na = int(na.rstrip('A')); nd = int(nd.rstrip('D'))
    analog = []
    for i in range(na):
        p = lines[2 + i].split(',')
        analog.append(dict(name=p[1], unit=p[4], a=float(p[5]), b=float(p[6]),
                           prim=float(p[10]), sec=float(p[11]), ps=p[12]))
    digital = [lines[2 + na + i].split(',')[1] for i in range(nd)]
    rate_line = lines[2 + na + nd + 2].split(',')
    assert float(rate_line[0]) == FS
    dat_path = cfg_path[:-4] + '.dat'
    raw = np.loadtxt(dat_path, delimiter=',', dtype=float)
    n = raw[:, 0].astype(int)
    assert np.all(n == np.arange(1, len(n) + 1)), 'sample numbers not contiguous'
    out = {'k': n - 1, 'analog': {}, 'digital': {}}
    for i, ch in enumerate(analog):
        v = raw[:, 2 + i] * ch['a'] + ch['b']
        if ch['ps'].upper() == 'P':      # convert to secondary if stored primary
            v = v * ch['sec'] / ch['prim']
        out['analog'][ch['name']] = v
    for i, name in enumerate(digital):
        out['digital'][name] = raw[:, 2 + na + i].astype(int)
    return out


def read_settings(path):
    s = {}
    with open(path) as f:
        for line in f:
            if '=' not in line:
                continue
            key, val = line.split(';')[0].split('=', 1)
            key = key.strip(); val = val.strip()
            try:
                s[key] = float(val)
            except ValueError:
                s[key] = val
    return s


def read_ser(path):
    """Parse the SER section of an event report -> list of (k, element, state)."""
    ser = []
    with open(path) as f:
        for line in f:
            p = line.split()
            if len(p) >= 3 and p[0].startswith('14:22:'):
                t = float(p[0].split(':')[2])
                k = int(round((t - T0_SEC) * FS))
                ser.append((k, p[1], p[2]))
    return ser

# ----------------------------------------------------------------------------------------
# Relay measurement: phasors, loops, zones
# ----------------------------------------------------------------------------------------
def phasors(x):
    """Full-cycle Fourier RMS phasor in fixed reference frame (manual section 1).
    Returns complex array, NaN for k < 31."""
    n = len(x)
    rot = np.exp(-1j * 2 * np.pi * np.arange(n) / N)
    y = x * rot
    c = np.concatenate([[0], np.cumsum(y)])
    X = np.full(n, np.nan + 1j * np.nan)
    k = np.arange(N - 1, n)
    X[k] = math.sqrt(2) / N * (c[k + 1] - c[k + 1 - N])
    return X


LOOPS = (('AB', 'A', 'B'), ('BC', 'B', 'C'), ('CA', 'C', 'A'))


def measure(v, i, st):
    """v, i: dicts phase -> secondary sample arrays as seen by the relay.
    Returns loop impedances and zone element arrays (bool) per manual section 2."""
    V = {p: phasors(v[p]) for p in 'ABC'}
    I = {p: phasors(i[p]) for p in 'ABC'}
    n = len(v['A'])
    T = math.radians(st['Z1ANG'])
    res = {'Z': {}, 'Ilp': {}, 'op': {}}
    zones = {'Z1': np.zeros(n, bool), 'Z2': np.zeros(n, bool), 'Z3R': np.zeros(n, bool)}
    for name, x, y in LOOPS:
        Vl = V[x] - V[y]; Il = I[x] - I[y]
        valid = np.isfinite(Il) & (np.abs(np.nan_to_num(Il)) >= st['50PP'])
        Z = np.full(n, np.nan + 1j * np.nan)
        Z[valid] = Vl[valid] / Il[valid]
        res['Z'][name] = Z; res['Ilp'][name] = Il
        for zn, key, sign in (('Z1', 'Z1P', 1), ('Z2', 'Z2P', 1), ('Z3R', 'Z3P', -1)):
            R = st.get(key, 'OFF')
            if R == 'OFF' or not isinstance(R, float):
                continue
            c = sign * (R / 2) * np.exp(1j * T)
            op = np.zeros(n, bool)
            op[valid] = np.abs(Z[valid] - c) <= R / 2
            res['op'][(zn, name)] = op
            zones[zn] |= op
    res['zones'] = zones
    return res

# ----------------------------------------------------------------------------------------
# Scheme logic (Figure 2) for a pair of relays joined by one channel
# ----------------------------------------------------------------------------------------
class Scheme:
    def __init__(self, st, zones):
        self.st = st; self.z = zones
        self.echo_en = str(st['ECHO']).upper() == 'Y'
        self.EDPU = int(st['EDPU']); self.EDUR = int(st['EDUR']); self.EBLK = int(st['EBLK'])
        n = len(zones['Z1'])
        self.out = {s: np.zeros(n, int) for s in
                    ('Z1', 'Z2', 'Z3R', 'RX', 'EBLKT', 'ECHO', 'KEY', 'TRIP', '52A')}
        self.cons = 0             # EDPU consecutive count
        self.edpu_prev = False
        self.pulse_left = 0       # EDUR one-shot remaining samples
        self.since_z3r = 10**9    # samples since Z3R last asserted
        self.trip = False
        self.trip_k = None

    def step(self, k, rx):
        z1 = bool(self.z['Z1'][k]); z2 = bool(self.z['Z2'][k]); z3 = bool(self.z['Z3R'][k])
        o = self.out
        o['Z1'][k] = z1; o['Z2'][k] = z2; o['Z3R'][k] = z3
        o['RX'][k] = rx
        # echo logic
        echo = False
        if self.echo_en:
            self.since_z3r = 0 if z3 else self.since_z3r + 1
            eblk = z3 or (self.since_z3r <= self.EBLK)
            o['EBLKT'][k] = eblk
            a = (not z1) and (not z2) and (not z3) and (not eblk) and rx
            self.cons = self.cons + 1 if a else 0
            edpu = self.cons >= self.EDPU
            if edpu and not self.edpu_prev and self.pulse_left == 0:
                self.pulse_left = self.EDUR
            self.edpu_prev = edpu
            if self.pulse_left > 0:
                echo = True; self.pulse_left -= 1
        o['ECHO'][k] = echo
        key = z2 or echo
        o['KEY'][k] = key
        if z1 or (z2 and rx):
            if not self.trip:
                self.trip_k = k
            self.trip = True
        o['TRIP'][k] = self.trip
        o['52A'][k] = 0 if (self.trip_k is not None and k >= self.trip_k + BKR_DELAY) else 1
        return key


def run_pair(stA, zA, stB, zB, n):
    a = Scheme(stA, zA); b = Scheme(stB, zB)
    keyA = np.zeros(n, bool); keyB = np.zeros(n, bool)
    for k in range(n):
        rxA = bool(keyB[k - CH_DELAY]) if k >= CH_DELAY else False
        rxB = bool(keyA[k - CH_DELAY]) if k >= CH_DELAY else False
        keyA[k] = a.step(k, rxA)
        keyB[k] = b.step(k, rxB)
    return a.out, b.out

# ----------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------
def first(arr):
    idx = np.flatnonzero(arr)
    return int(idx[0]) if len(idx) else None


def transitions(arr):
    d = np.diff(np.concatenate([[0], np.asarray(arr, int)]))
    return [(int(k), 'asserted' if d[k] > 0 else 'deasserted') for k in np.flatnonzero(d)]


def ktime(k):
    # relay SER time stamps are truncated to 0.1 ms
    t = math.floor(round((T0_SEC + k / FS) * 1e4, 6)) / 1e4
    return '14:22:%07.4f' % t


def ser_from_replay(out, names):
    ev = []
    for nm in names:
        for k, s in transitions(out[nm]):
            ev.append((k, nm, s))
    return sorted(ev)


def compare_ser(replay_out, ser, names_map=None):
    """Compare event-report SER (k, element, state) to replay transitions."""
    rows = []
    for k, el, state in ser:
        nm = (names_map or {}).get(el, el)
        if nm not in replay_out:
            rows.append(dict(element=el, state=state, ser_k=k, replay_k=None, match=None))
            continue
        tr = [t for t in transitions(replay_out[nm]) if t[1] == state]
        if el == '52A':
            tr = [(kk, 'closed' if s == 'asserted' else 'open') for kk, s in
                  transitions(replay_out[nm])]
            tr = [t for t in tr if t[1] == state]
            if state == 'closed' and not tr and replay_out[nm][0] == 1:
                tr = [(0, 'closed')]
        rk = min((t[0] for t in tr), key=lambda x: abs(x - k)) if tr else None
        rows.append(dict(element=el, state=state, ser_k=k, ser_time=ktime(k), replay_k=rk,
                         match=(rk == k)))
    return rows


def fault_inception(rec, names=('IA', 'IB', 'IC', 'VA', 'VB', 'VC'), thr=0.10):
    """First sample at which any channel departs from its value one cycle earlier by more
    than thr x its pre-fault peak (cycle-difference detector)."""
    ks = []
    for nm in names:
        x = rec['analog'][nm]
        pk = np.max(np.abs(x[:300]))
        d = np.abs(x[N:] - x[:-N])
        base = np.max(d[:250])
        idx = np.flatnonzero(d > base + thr * pk)
        ks.append(int(idx[0]) + N if len(idx) else 10**9)
    return min(ks), dict(zip(names, ks))


def main(case, outdir):
    os.makedirs(outdir, exist_ok=True)
    P = lambda f: os.path.join(case, f)
    recA = read_comtrade(P('SUBA_L1-21_20260914_142207.cfg'))
    recBL2 = read_comtrade(P('SUBB_L2-21_20260914_142207.cfg'))
    recCL2 = read_comtrade(P('SUBC_L2-21_20260914_142207.cfg'))
    stA = read_settings(P('SUBA_L1-21_settings.txt'))
    stB = read_settings(P('SUBB_L1-21_settings.txt'))
    stBL2 = read_settings(P('SUBB_L2-21_settings.txt'))
    stCL2 = read_settings(P('SUBC_L2-21_settings.txt'))
    serA = read_ser(P('SUBA_L1-21_event_report.txt'))
    serB = read_ser(P('SUBB_L1-21_event_report.txt'))
    serBL2 = read_ser(P('SUBB_L2-21_event_report.txt'))
    serCL2 = read_ser(P('SUBC_L2-21_event_report.txt'))
    n = len(recA['k'])
    assert len(recBL2['k']) == n == len(recCL2['k'])

    # CT ratio actually landed on relay B (commissioning record Sub B 2023-04-14,
    # 52-L1 core 1 leads landed X1-X5; DWG B-E-2214 tap chart X1-X5 = 2000:5)
    CT_TAPS_B = {'X1-X2': 250, 'X2-X3': 400, 'X3-X4': 800, 'X4-X5': 550, 'X1-X3': 650,
                 'X2-X4': 1200, 'X3-X5': 1350, 'X1-X4': 1450, 'X2-X5': 1750, 'X1-X5': 2000}
    NB_LANDED = CT_TAPS_B['X1-X5'] / 5.0       # 400
    NB_DESIGN = CT_TAPS_B['X2-X4'] / 5.0       # 240 = setting CTR

    def va(rec):
        return {p: rec['analog']['V' + p] for p in 'ABC'}

    def ia(rec):
        return {p: rec['analog']['I' + p] for p in 'ABC'}

    vA, iA = va(recA), ia(recA)
    vB = va(recBL2)                                         # VT-B, same bus VT
    iA_prim = {p: iA[p] * stA['CTR'] for p in 'ABC'}        # primary A, into L1 at A

    def relayB_currents(ratio, polarity=1.0):
        return {p: polarity * (-iA_prim[p]) / ratio for p in 'ABC'}

    # ---------------- validation of the engine with the L2 records (B and C) -------------
    mBL2 = measure(va(recBL2), ia(recBL2), stBL2)
    mCL2 = measure(va(recCL2), ia(recCL2), stCL2)
    oBL2, oCL2 = run_pair(stBL2, mBL2['zones'], stCL2, mCL2['zones'], n)
    l2_check = {}
    for nm, rec, o in (('SUBB_L2-21', recBL2, oBL2), ('SUBC_L2-21', recCL2, oCL2)):
        mism = {ch: int(np.sum(o[ch] != rec['digital'][ch])) for ch in rec['digital']}
        l2_check[nm] = mism
    l2_ser = {'SUBB_L2-21': compare_ser(oBL2, serBL2), 'SUBC_L2-21': compare_ser(oCL2, serCL2)}

    # ---------------- as-found replay of L1 relays A and B ------------------------------
    mA = measure(vA, iA, stA)
    iB = relayB_currents(NB_LANDED)
    mB = measure(vB, iB, stB)
    oA, oB = run_pair(stA, mA['zones'], stB, mB['zones'], n)
    a_mism = {ch: int(np.sum(oA[ch] != recA['digital'][ch])) for ch in recA['digital']}
    a_ser = compare_ser(oA, serA)
    b_ser = compare_ser(oB, serB)

    # ---------------- hypotheses for relay B's inputs (which reproduces relay B's SER?) ---
    hyp = {}
    for label, ratio, pol in (('CT 1200:5 as designed (CTR 240), normal polarity', NB_DESIGN, 1),
                              ('CT 2000:5 X1-X5 as landed (400), normal polarity', NB_LANDED, 1),
                              ('CT 1200:5, reversed polarity', NB_DESIGN, -1),
                              ('CT 2000:5, reversed polarity', NB_LANDED, -1)):
        m = measure(vB, relayB_currents(ratio, pol), stB)
        a_, b_ = run_pair(stA, mA['zones'], stB, m['zones'], n)
        rows = compare_ser(b_, serB)
        hyp[label] = dict(ratio=ratio, polarity=pol,
                          relayB_first={s: first(b_[s]) for s in ('Z1', 'Z2', 'Z3R', 'ECHO', 'KEY', 'TRIP')},
                          relayA_trip=first(a_['TRIP']),
                          reproduces_relayB_SER=all(r['match'] for r in rows),
                          reproduces_relayA_record=all(int(np.sum(a_[ch] != recA['digital'][ch])) == 0
                                                       for ch in recA['digital']))
    # range of effective ratios for which B's Z3R fails (scan)
    scan = []
    for ratio in np.arange(200, 601, 5):
        m = measure(vB, relayB_currents(ratio), stB)
        a_, b_ = run_pair(stA, mA['zones'], stB, m['zones'], n)
        scan.append((float(ratio), first(b_['Z3R']), first(b_['ECHO']), first(a_['TRIP'])))
    ratios_fail = [r for r, z3, e, t in scan if t is not None]
    ratios_ok = [r for r, z3, e, t in scan if t is None]

    # ---------------- counterfactual: relay B CT on X2-X4 (1200:5) = setting CTR 240 ------
    iBc = relayB_currents(NB_DESIGN)
    mBc = measure(vB, iBc, stB)
    oAc, oBc = run_pair(stA, mA['zones'], stB, mBc['zones'], n)
    # alternative corrective action: keep X1-X5, set CTR = 400 and rescale secondary settings
    k_new = 400.0 / stB['PTR']
    stB_alt = dict(stB)
    stB_alt.update(CTR=400.0,
                   Z1P=round(30.89 * k_new, 2), Z2P=round(48.26 * k_new, 2),
                   Z3P=round(14.48 * k_new, 2), **{'50PP': round(0.50 * 240 / 400, 2)})
    mBalt = measure(vB, iB, stB_alt)
    oAalt, oBalt = run_pair(stA, mA['zones'], stB_alt, mBalt['zones'], n)

    # ---------------- fault characterisation --------------------------------------------
    k_inc, k_inc_ch = fault_inception(recBL2)
    k_inc_A, _ = fault_inception(recA)
    k_inc_C, _ = fault_inception(recCL2)
    # steady fault window: two cycles after inception until before the first L2 breaker opens
    k_bkrB_L2 = first(recBL2['digital']['52A'] == 0)
    win = np.arange(k_inc + 2 * N, k_bkrB_L2 - 1)
    zl_km = 0.05 + 0.48j
    loopsBL2 = {nm: np.nanmedian(np.abs(mBL2['Ilp'][nm][win])) for nm, _, _ in LOOPS}
    loopsA = {nm: np.nanmedian(np.abs(mA['Ilp'][nm][win])) for nm, _, _ in LOOPS}
    pre = np.arange(100, 280)
    preA = {nm: float(np.nanmedian(np.abs(mA['Ilp'][nm][pre]))) for nm, _, _ in LOOPS}
    # (a) single-ended reactance from Sub B L2-21 (CT and settings consistent: X2-X4 = 1200:5)
    ZB = mBL2['Z']['BC'][win] * stBL2['PTR'] / stBL2['CTR']
    d_react_B = float(np.median(ZB.imag) / 0.48)
    ZC = mCL2['Z']['BC'][win] * stCL2['PTR'] / stCL2['CTR']
    d_react_C = float(np.median(ZC.imag) / 0.48)
    # (b) two-ended (B and C, synchronised), immune to fault resistance and infeed
    VBl = (phasors(recBL2['analog']['VB']) - phasors(recBL2['analog']['VC']))[win] * stBL2['PTR']
    IBl = (phasors(recBL2['analog']['IB']) - phasors(recBL2['analog']['IC']))[win] * stBL2['CTR']
    VCl = (phasors(recCL2['analog']['VB']) - phasors(recCL2['analog']['VC']))[win] * stCL2['PTR']
    ICl = (phasors(recCL2['analog']['IB']) - phasors(recCL2['analog']['IC']))[win] * stCL2['CTR']
    L2 = 50.0
    d2 = (VBl - VCl + zl_km * L2 * ICl) / (zl_km * (IBl + ICl))
    d_two_end = float(np.median(d2.real))
    Rf = (VBl - zl_km * d2.real * IBl) / (IBl + ICl)
    # (c) L1 integrity check: VA - VB = ZL1 * I_A for each loop if L1 is healthy
    L1 = 80.0
    VAl = (phasors(vA['B']) - phasors(vA['C']))[win] * stA['PTR']
    VBb = (phasors(vB['B']) - phasors(vB['C']))[win] * stA['PTR']
    IAl = (phasors(iA['B']) - phasors(iA['C']))[win] * stA['CTR']
    zl1_est = (VAl - VBb) / IAl / L1
    # current balance at bus B (KCL) -> contribution of T1 / other sources at B
    IB_from_L1 = -IAl                                        # current at B entering L1
    I_other = -(IB_from_L1 + IBl)                             # current from other bus-B bays
    # apparent impedances at B (as-found and with correct CT) in the fault window
    def zstats(m, nm='BC'):
        z = m['Z'][nm][win]
        return dict(R=float(np.median(z.real)), X=float(np.median(z.imag)),
                    mag=float(np.median(np.abs(z))),
                    ang=float(np.degrees(np.median(np.angle(z)))))
    Zb_found = zstats(mB); Zb_correct = zstats(mBc); Za = zstats(mA)
    # A fault locator at trip sample (manual sec. 4)
    ktripA = first(oA['TRIP'])
    ZA_trip = mA['Z']['BC'][ktripA] * stA['PTR'] / stA['CTR']
    d_A_locator = float(ZA_trip.imag / 0.48)
    # Z3R reach margin: required reach (centre distance) for the observed apparent impedance
    T = math.radians(stB['Z3ANG'] if 'Z3ANG' in stB else stB['Z1ANG'])
    def mho_reach_needed(z):   # smallest reach R such that |z + R/2 e^jT| <= R/2  (reverse)
        # |z|^2 + R Re(z e^-jT) <= 0  ->  R >= -|z|^2 / Re(z e^-jT)
        p = (z * np.exp(-1j * T)).real
        return float(-abs(z) ** 2 / p) if p < 0 else float('inf')
    zf = complex(Zb_found['R'], Zb_found['X']); zc = complex(Zb_correct['R'], Zb_correct['X'])
    reach_needed_found = mho_reach_needed(zf)
    reach_needed_correct = mho_reach_needed(zc)
    # previous Z3P (1.80, before R5) with the CT as landed
    st_old = dict(stB); st_old['Z3P'] = 1.80
    m_old = measure(vB, iB, st_old)
    a_old, b_old = run_pair(stA, mA['zones'], st_old, m_old['zones'], n)
    # first assertion of each loop element (as found and corrected)
    def loop_first(m):
        return {'%s_%s' % kz: first(v) for kz, v in m['op'].items()}

    # ---------------- outputs ----------------------------------------------------------
    chans = ('Z1', 'Z2', 'Z3R', 'RX', 'ECHO', 'KEY', 'TRIP', '52A')
    def write_csv(path, oa, ob):
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['sample_k', 'dat_sample_n', 'time'] + ['A_' + c for c in chans] +
                       ['B_' + c for c in chans] + ['A_recorded_' + c for c in recA['digital']])
            for k in range(n):
                w.writerow([k, k + 1, ktime(k)] + [int(oa[c][k]) for c in chans] +
                           [int(ob[c][k]) for c in chans] +
                           [int(recA['digital'][c][k]) for c in recA['digital']])
    write_csv(os.path.join(outdir, 'replay_digital_channels.csv'), oA, oB)
    write_csv(os.path.join(outdir, 'replay_digital_channels_without_root_cause.csv'), oAc, oBc)

    elems = ('Z1', 'Z2', 'Z3R', 'RX', 'ECHO', 'KEY', 'TRIP')
    def firsts(o):
        return {e: first(o[e]) for e in elems}
    def lasts(o):
        r = {}
        for e in elems:
            idx = np.flatnonzero(o[e]); r[e] = int(idx[-1]) + 1 if len(idx) else None
        return r
    def kt(d):
        return {e: (None if v is None else {'k': v, 'dat_n': v + 1, 'time': ktime(v)})
                for e, v in d.items()}
    bk_open_A = first(oA['52A'] == 0)

    result = {
        'event': 'L1 breaker trip at Substation A, 2026-09-14 14:22:07',
        'sample_convention': 'relay sample k = dat sample n - 1; k = 0 at 14:22:07.345000; 1920 samples/s',
        'item1_fault': {
            'type': 'phase B to phase C (BC phase-to-phase, no ground)',
            'faulted_line': 'L2 (Substation B - Substation C)',
            'distance_from_substation_B_km_two_ended': round(d_two_end, 2),
            'distance_from_substation_B_km_reactance_SubB_L2_relay': round(d_react_B, 2),
            'distance_from_substation_C_km_reactance_SubC_L2_relay': round(d_react_C, 2),
            'distance_from_substation_B_km_patrol': 6.5,
            'fault_resistance_ohm_primary_two_ended': round(float(np.median(Rf.real)), 2),
            'fault_inception_sample_k': k_inc, 'fault_inception_dat_n': k_inc + 1,
            'fault_inception_time': ktime(k_inc),
            'inception_sample_by_record': {'SUBA_L1-21': k_inc_A, 'SUBB_L2-21': k_inc,
                                           'SUBC_L2-21': k_inc_C},
        },
        'item2_first_assertion_as_found': {
            'relay_A': kt(firsts(oA)), 'relay_B': kt(firsts(oB)),
            'relay_A_deassertion_k': lasts(oA), 'relay_B_deassertion_k': lasts(oB),
            'relay_A_breaker_open_k': bk_open_A,
            'relay_A_replay_vs_record_mismatched_samples': a_mism,
            'relay_A_SER_comparison': a_ser, 'relay_B_SER_comparison': b_ser,
            'relay_A_fault_locator_km': round(d_A_locator, 1),
        },
        'item3_root_cause': (
            'Relay B (Substation B L1-21) is fed from CT 52-L1 core 1 landed on the full winding '
            'X1-X5 = 2000:5 (ratio 400; commissioning record Sub B 2023-04-14, DWG B-E-2214), '
            'while the relay is set CTR = 240 (1200:5, tap X2-X4) as the settings calculation '
            'requires. Relay B measures 240/400 = 0.60 of the true current, so every apparent '
            'impedance is 1.667x too large and the reverse zone Z3R (1.74 ohm sec) did not reach '
            'the reverse BC fault on L2. With no Z1, Z2 or Z3R and RX from relay A (Z2 keying for '
            'the L2 fault in its overreach), the echo AND held for EDPU = 32 samples and relay B '
            'echoed the permissive back; relay A then tripped by POTT (Z2 AND RX). The tap error '
            'became exposed when ECHO was enabled at B in settings revision R5 (2026-05-26).'),
        'relayB_apparent_impedance_BC_fault_window_sec_ohm': {
            'as_found_CT_400': Zb_found, 'with_correct_CT_240': Zb_correct,
            'Z3P_setting': stB['Z3P'],
            'Z3P_reach_needed_to_operate_as_found': round(reach_needed_found, 3),
            'Z3P_reach_needed_to_operate_correct_CT': round(reach_needed_correct, 3),
            'old_Z3P_1.80_with_CT_as_landed': {'Z3R_first': first(b_old['Z3R']),
                                               'ECHO_first': first(b_old['ECHO']),
                                               'relay_A_trip_first': first(a_old['TRIP'])}},
        'loop_element_first_assertion': {'relay_A': loop_first(mA), 'relay_B_as_found': loop_first(mB),
                                         'relay_B_CT_corrected': loop_first(mBc)},
        'relayA_apparent_impedance_BC_fault_window_sec_ohm': Za,
        'item4_without_root_cause': {
            'relay_A': kt(firsts(oAc)), 'relay_B': kt(firsts(oBc)),
            'relay_A_trips': first(oAc['TRIP']) is not None,
            'relay_B_trips': first(oBc['TRIP']) is not None,
            'relay_B_echo': first(oBc['ECHO']) is not None,
            'relay_A_keys_from_Z2_k': first(oAc['KEY']),
            'summary': 'Relay B Z3R asserts and blocks echo; relay B never keys; relay A keys on Z2 '
                       'but receives no permissive and does not trip. L1 stays in service; L2 '
                       'fault cleared by L2 relays only.',
        },
        'item5_corrective_action': {
            'primary': 'Re-land relay B CT circuit (52-L1 core 1 at Sub B) on tap X2-X4 = 1200:5 to '
                       'match CTR = 240 and the settings calculation; no relay setting change. '
                       'Verify by ratio test from primary injection and in-service load check '
                       '(relay B current magnitude equal to relay A at 1:1, phase 180 deg).',
            'new_setting_values_primary_option': 'none (settings R5 remain valid: CTR 240, Z1P 3.71, '
                                                 'Z2P 5.79, Z3P 1.74, 50PP 0.50)',
            'alternative_if_X1_X5_tap_retained': {
                'CTR': 400, 'Z1P': stB_alt['Z1P'], 'Z2P': stB_alt['Z2P'], 'Z3P': stB_alt['Z3P'],
                '50PP': stB_alt['50PP'], 'others': 'unchanged (Z1ANG 84, ECHO Y, EDPU 32, EDUR 64, EBLK 64)',
                'replay_relay_A_trips': first(oAalt['TRIP']) is not None,
                'replay_relay_B_first': {e: v for e, v in firsts(oBalt).items()}},
            'other': ['Audit CT tap/ratio of all bays against relay CTR settings (Sub B uses 2000:5 MR CTs).',
                      'Add in-service load-current comparison (both line ends) to commissioning and '
                      'to post-setting-change procedure; secondary injection at the test switch '
                      'cannot detect a CT tap error.',
                      'Correct one-line S-230-001 (G2 retired; T1 bay at B not shown).',
                      'Increase relay B event storage / retrieve records before restoration switching.'],
        },
        'evidence': {
            'engine_validation_L2_relays_mismatched_samples': l2_check,
            'engine_validation_L2_SER': l2_ser,
            'relayB_input_hypotheses': hyp,
            'effective_ratio_scan_relayA_trips_for_ratio_range':
                [min(ratios_fail), max(ratios_fail)] if ratios_fail else None,
            'effective_ratio_scan_no_trip_for_ratio_range':
                [min(ratios_ok), max(ratios_ok)] if ratios_ok else None,
            'L1_series_impedance_from_A_and_B_voltages_ohm_per_km':
                {'R': round(float(np.median(zl1_est.real)), 4), 'X': round(float(np.median(zl1_est.imag)), 4),
                 'expected': '0.05 + j0.48'},
            'loop_current_fault_window_A_sec': {k: round(float(v), 2) for k, v in loopsA.items()},
            'loop_current_prefault_A_sec': {k: round(v, 3) for k, v in preA.items()},
            'loop_current_fault_window_SubB_L2_sec': {k: round(float(v), 2) for k, v in loopsBL2.items()},
            'BC_loop_current_primary_A_fault_window': {
                'L1_at_A': round(float(np.median(np.abs(IAl))), 0),
                'L2_at_B': round(float(np.median(np.abs(IBl))), 0),
                'L2_at_C': round(float(np.median(np.abs(ICl))), 0),
                'other_bays_at_B_(T1)': round(float(np.median(np.abs(I_other))), 0)},
            'relayB_BC_loop_current_sec_as_found': round(float(np.nanmedian(np.abs(mB['Ilp']['BC'][win]))), 2),
            'fault_window_samples': [int(win[0]), int(win[-1])],
        },
    }
    with open(os.path.join(outdir, 'L1_trip_results.json'), 'w') as f:
        json.dump(result, f, indent=2, default=lambda o: o.item() if hasattr(o, 'item') else str(o))

    # ---------- figures --------------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(13, 6))
        th = np.linspace(0, 2 * np.pi, 400)
        Tz = math.radians(stB['Z1ANG'])
        for R, ls, lab in ((stB['Z1P'], '-', 'Z1'), (stB['Z2P'], '--', 'Z2')):
            c = R / 2 * np.exp(1j * Tz); ax[0].plot((c + R / 2 * np.exp(1j * th)).real,
                                                     (c + R / 2 * np.exp(1j * th)).imag, 'k' + ls, lw=1, label=lab)
        R = stB['Z3P']; c = -R / 2 * np.exp(1j * Tz)
        ax[0].plot((c + R / 2 * np.exp(1j * th)).real, (c + R / 2 * np.exp(1j * th)).imag, 'k-.', lw=1, label='Z3R (1.74)')
        kk = np.arange(k_inc, k_bkrB_L2)
        ax[0].plot(mB['Z']['BC'][kk].real, mB['Z']['BC'][kk].imag, '.', color='tab:red', ms=3,
                   label='relay B BC loop, CT as landed (2000:5)')
        ax[0].plot(mBc['Z']['BC'][kk].real, mBc['Z']['BC'][kk].imag, '.', color='tab:blue', ms=3,
                   label='relay B BC loop, CT 1200:5 (= CTR 240)')
        ax[0].plot(mA['Z']['BC'][kk].real, mA['Z']['BC'][kk].imag, '.', color='tab:green', ms=3,
                   label='relay A BC loop')
        ax[0].set_xlim(-4, 4); ax[0].set_ylim(-4, 6.5); ax[0].set_aspect('equal'); ax[0].grid(alpha=.3)
        ax[0].set_xlabel('R (sec ohm)'); ax[0].set_ylabel('X (sec ohm)')
        ax[0].set_title('BC loop impedance, samples %d-%d' % (kk[0], kk[-1]))
        ax[0].legend(fontsize=7, loc='upper left')
        ks = np.arange(300, 520)
        sig = [('A_Z2', oA['Z2']), ('A_KEY', oA['KEY']), ('A_RX', oA['RX']), ('A_TRIP', oA['TRIP']),
               ('A_52A', oA['52A']), ('B_Z3R', oB['Z3R']), ('B_RX', oB['RX']), ('B_ECHO', oB['ECHO']),
               ('B_KEY', oB['KEY']), ('B_Z3R*', oBc['Z3R']), ('B_ECHO*', oBc['ECHO']), ('A_TRIP*', oAc['TRIP'])]
        for j, (nm, s) in enumerate(sig):
            ax[1].step(ks, j * 1.5 + 0.9 * s[ks], where='post', lw=1.2,
                       color='tab:blue' if '*' in nm else 'k')
            ax[1].text(ks[0] - 2, j * 1.5 + 0.2, nm, ha='right', fontsize=8)
        ax[1].axvline(k_inc, color='tab:red', lw=.8, ls=':'); ax[1].set_yticks([])
        ax[1].set_xlabel('relay sample k'); ax[1].set_title('Replay (black: as found; blue *: CT corrected)')
        fig.tight_layout(); fig.savefig(os.path.join(outdir, 'replay_figure.png'), dpi=130)
    except Exception as e:  # figure is optional
        print('figure skipped:', e)

    # ---------- console summary --------------------------------------------------------
    print('Engine validation (L2 relays) mismatched samples:', l2_check)
    print('Relay A replay vs recorded digital channels, mismatched samples:', a_mism)
    print('Relay A SER compare:'); [print('  ', r) for r in a_ser]
    print('Relay B SER compare:'); [print('  ', r) for r in b_ser]
    print('First assertions A:', firsts(oA)); print('First assertions B:', firsts(oB))
    print('Counterfactual A:', firsts(oAc)); print('Counterfactual B:', firsts(oBc))
    print('Alt settings A:', firsts(oAalt), 'B:', firsts(oBalt))
    print('Fault inception k:', k_inc, k_inc_ch, 'A rec', k_inc_A, 'C rec', k_inc_C)
    print('d two-ended %.3f km, reactance B %.3f, C %.3f, Rf %.3f' % (d_two_end, d_react_B, d_react_C,
                                                                       float(np.median(Rf.real))))
    print('A locator at trip k=%d: %.2f km' % (ktripA, d_A_locator))
    print('Zb found', Zb_found, 'needed reach', reach_needed_found)
    print('Zb correct', Zb_correct, 'needed reach', reach_needed_correct)
    print('Za', Za)
    print('Hypotheses:'); [print('  ', k, v) for k, v in hyp.items()]
    print('ratio scan: trip for', (min(ratios_fail), max(ratios_fail)) if ratios_fail else None,
          'no trip for', (min(ratios_ok), max(ratios_ok)) if ratios_ok else None)
    print('L1 z per km', np.median(zl1_est.real), np.median(zl1_est.imag))
    print(json.dumps(result['evidence']['BC_loop_current_primary_A_fault_window']))
    return result


if __name__ == '__main__':
    case = sys.argv[1] if len(sys.argv) > 1 else 'case'
    out = sys.argv[2] if len(sys.argv) > 2 else 'deliverables'
    main(case, out)
