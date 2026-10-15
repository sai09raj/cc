"""Extended-period simulation: per 15-min step a steady hydraulic solve (global gradient algorithm: Hazen-Williams pipes, parallel pumps with check valve,
PRV), then an explicit tank update and level controls evaluated at the start of each step."""
import math, numpy as np
import net as N
G = 9.81
ZONE = ("J10", "J11", "J12")
EXP = 1.852
def sec_k(t, L):
    _, D, C = N.PIPE[t]; return 10.67 * L / (C ** 1.852 * (D / 1000.0) ** 4.87)      # h = k Q^1.852, Q in m3/s
def pipe_k(st, pid):
    secs = st["pipes"].get(pid, dict((p[0], p[3]) for p in N.PIPES)[pid]); return sum(sec_k(t, L) for t, L in secs)
def hyd(st, mult, level, npump):
    """Steady solve for one step: heads (m), pipe flows (L/s), pump flow (L/s), pump lift (m), PRV mode."""
    main = [p for p in N.PIPES if p[1] not in ZONE]
    juncs = [n for n in N.NODE if n not in ZONE]; idx = {n: i for i, n in enumerate(juncs)}; nj = len(juncs)
    HT = N.TANK["base"] + level; a, b = N.PUMP
    dem = np.array([N.NODE[x][1] * mult / 1000.0 for x in juncs])
    zone_q = sum(N.NODE[x][1] * mult for x in ZONE) / 1000.0
    dem[idx[N.PRV["up"]]] += zone_q                                  # PRV passes exactly the low-zone demand
    links = [(pid, u, v, pipe_k(st, pid)) for pid, u, v, _ in main]
    pump_on = npump > 0
    for _ in range(3):                                               # check-valve status loop
        nl = len(links) + (1 if pump_on else 0)
        Q = np.full(nl, 0.02); H = np.full(nj, HT)
        for it in range(200):
            A = np.zeros((nl + nj, nl + nj)); r = np.zeros(nl + nj)
            def hd(x): return HT if x == "T" else H[idx[x]]
            for i, (pid, u, v, k) in enumerate(links):
                q = Q[i]; aq = max(abs(q), 1e-7)
                r[i] = k * aq ** (EXP - 1) * q - (hd(u) - hd(v)); A[i, i] = EXP * k * aq ** (EXP - 1)
                if u != "T": A[i, nl + idx[u]] = -1.0; r[nl + idx[u]] -= q
                if v != "T": A[i, nl + idx[v]] = 1.0; r[nl + idx[v]] += q
                if u != "T": A[nl + idx[u], i] = -1.0
                if v != "T": A[nl + idx[v], i] = 1.0
            if pump_on:
                i = nl - 1; q = Q[i]; qp = 1000 * q / npump
                r[i] = -(a - b * qp * abs(qp)) - (N.H_RES - H[idx["J1"]]); A[i, i] = 2 * b * abs(qp) * 1000 / npump + 1e-6
                A[i, nl + idx["J1"]] = 1.0; r[nl + idx["J1"]] += q; A[nl + idx["J1"], i] = 1.0
            r[nl:] -= dem
            dx = np.linalg.solve(A, -r); Q += dx[:nl]; H += dx[nl:]
            if np.max(np.abs(dx)) < 1e-12: break
        else: raise RuntimeError("no convergence")
        if pump_on and Q[-1] < 0: pump_on = False; continue      # check valve shuts
        break
    Hd = {x: H[idx[x]] for x in juncs}; Hd["T"] = HT
    flows = {pid: 1000 * Q[i] for i, (pid, u, v, k) in enumerate(links)}
    qpump = 1000 * Q[-1] if pump_on else 0.0; lift = Hd["J1"] - N.H_RES
    up = Hd[N.PRV["up"]]; mode = "active" if up >= N.PRV["setting"] else "open"
    h10 = N.PRV["setting"] if mode == "active" else up
    q11 = (N.NODE["J11"][1] + N.NODE["J12"][1]) * mult / 1000; q12 = N.NODE["J12"][1] * mult / 1000
    k1, k2 = pipe_k(st, "L1"), pipe_k(st, "L2")
    Hd["J10"] = h10; Hd["J11"] = h10 - k1 * q11 ** EXP; Hd["J12"] = Hd["J11"] - k2 * q12 ** EXP
    flows["L1"], flows["L2"] = 1000 * q11, 1000 * q12
    return dict(H=Hd, flows=flows, qpump=qpump, lift=lift, prv=mode)
def simulate(st):
    A = math.pi * N.TANK["diameter"] ** 2 / 4; level = st.get("init", N.TANK["init"]); pumps = dict(st.get("pumps0", N.INIT_PUMPS))
    ctrl = st.get("ctrl", N.CTRL); dt = N.DT_MIN * 60; steps = 24 * 60 // N.DT_MIN
    rows, events, energy, cost = [], [], 0.0, 0.0; pmin = (1e9, None, None)
    for k in range(steps):
        t = k * N.DT_MIN; hour = t // 60
        for p, (on, off) in ctrl.items():
            new = True if level <= on else (False if level >= off else pumps[p])
            if new != pumps[p]: events.append((t, p, "start" if new else "stop")); pumps[p] = new
        mult = st["pattern"][hour]
        r = hyd(st, mult, level, sum(pumps.values()))
        qt = r["flows"]["TK"]
        P = G * (r["qpump"] / 1000) * r["lift"] / N.ETA if r["qpump"] else 0.0     # kW (rho = 1000 kg/m3)
        energy += P * dt / 3600; cost += P * dt / 3600 * N.TARIFF[hour]
        for x, (z, d) in N.NODE.items():
            if d > 0:
                pr = r["H"][x] - z
                if pr < pmin[0]: pmin = (pr, x, t)
        rows.append(dict(t=t, level=level, pumps=dict(pumps), mult=mult, qt=qt, qpump=r["qpump"], lift=r["lift"], prv=r["prv"], H=r["H"], flows=r["flows"], P=P))
        level += qt / 1000 * dt / A
    return dict(rows=rows, events=events, energy=energy, cost=cost, pmin=pmin, final=level, minlevel=min([x["level"] for x in rows] + [level]))
