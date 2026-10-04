#!/usr/bin/env python3
"""ATRIUM-9 independent verifier.

Shares ONLY the immutable constants module with the primary simulator.  It
  (1) re-derives the 80-call table from the packet formulas,
  (2) re-simulates any configuration with a separately-written engine
      (timer-based phases, incrementally maintained per-direction commitment
      multisets, plain dicts -- no code shared with atrium9_sim.py),
  (3) audits the primary's delivered baseline artefacts for physical
      feasibility (header, tick continuity, per-tick power <= budget, energy
      law, boarding never before arrival, boarding at origin / alighting at the
      re-derived destination, capacity, wait/energy totals) and checks that the
      delivered trace is byte-identical to the independent re-simulation,
  (4) optionally re-checks every row of the 144-row sweep table.

Usage:
  atrium9_verify.py OUTDIR                      audit + full-sweep cross-check
  atrium9_verify.py OUTDIR --trace F --calls F  audit alternative artefacts
Exit status 0 = ACCEPT, 1 = REJECT.
"""
import csv
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atrium9_constants as K

U, D = "UP", "DOWN"


def call_table():
    tab = []
    for g in range(80):
        s, k = divmod(g, 20)
        grp = k // 3
        o = (2 * s + 3 * grp) % 8
        if o in (0, 7):
            dr = U if o == 0 else D
        else:
            dr = U if (s + grp) % 2 == 0 else D
        span = 1 + ((3 * s + 5 * k) % 7)
        if dr == U:
            de = min(7, o + span)
            de = de if de != o else min(7, o + 1)
        else:
            de = max(0, o - span)
            de = de if de != o else max(0, o - 1)
        tab.append({"g": g, "o": o, "dir": dr, "arr": 8 * k + 200 * s, "dest": de})
    return tab


def simulate(n_active, zoning, timeout, budget):
    """Independent engine.  Returns (trace list of (t,p,e), call records)."""
    T = K.TRAVEL_TICKS
    calls = call_table()
    for c in calls:
        c.update(car=None, since=None, banned=[], board=None, alight=None)
    home = K.HOMES[zoning]
    cars = []
    for i in range(n_active):
        cars.append({"id": i, "home": home[i], "floor": home[i], "mode": "STILL",
                     "end": 0, "start": 0, "mv": 0, "scan": None, "riders": [],
                     "c": {U: {}, D: {}}})

    def bump(car, dr, f, n):
        m = car["c"][dr]
        m[f] = m.get(f, 0) + n
        if m[f] == 0:
            del m[f]

    def stops(car, dr):
        return set(car["c"][dr])

    def free(car):
        return not car["c"][U] and not car["c"][D]

    def where(car, t):              # position in ticks (4 per floor)
        if car["mode"] == "MOVE":
            return car["floor"] * T + car["mv"] * (t - car["start"])
        return car["floor"] * T

    def dist(car, f, t):
        if car["mode"] == "MOVE":
            nxt = car["floor"] + car["mv"]
            return (car["end"] - t) + T * abs(nxt - f)
        return T * abs(car["floor"] - f)

    def ok(car, c, t):
        if car["id"] in c["banned"]:
            return False
        if free(car):
            return True
        if car["scan"] != c["dir"]:
            return False
        w = where(car, t)
        return c["o"] * T > w if c["dir"] == U else c["o"] * T < w

    def pick(c, t, skip):
        cand = sorted((dist(car, c["o"], t), car["id"]) for car in cars
                      if car["id"] != skip and ok(car, c, t))
        return cand[0] if cand else None

    trace = []
    t = 0
    remaining = 80
    while remaining:
        if t > 100000:
            raise RuntimeError("verifier engine did not terminate")
        # finished phases
        for car in cars:
            if car["mode"] != "STILL" and car["mode"] != "DWELL" and t >= car["end"]:
                if car["mode"] == "MOVE":
                    car["floor"] += car["mv"]
                    car["mode"], car["mv"] = "STILL", 0
                elif car["mode"] == "OPEN":
                    car["mode"], car["start"] = "DWELL", t
                elif car["mode"] == "SHUT":
                    car["mode"] = "STILL"
        # timeouts
        for c in calls:
            if c["car"] is None or c["board"] is not None:
                continue
            if t - c["since"] <= timeout:
                continue
            inc = cars[c["car"]]
            alt = pick(c, t, inc["id"])
            if alt and alt[0] < dist(inc, c["o"], t):
                bump(inc, c["dir"], c["o"], -1)
                c["banned"].append(inc["id"])
                c["car"], c["since"] = alt[1], t
                bump(cars[alt[1]], c["dir"], c["o"], +1)
        # fresh assignments
        for c in calls:
            if c["arr"] <= t and c["car"] is None:
                b = pick(c, t, None)
                if b:
                    c["car"], c["since"] = b[1], t
                    bump(cars[b[1]], c["dir"], c["o"], +1)
        # power: keep admitted draws
        pw = sum(K.P_TRAVEL if car["mode"] == "MOVE" else
                 (K.P_OPEN if car["mode"] == "OPEN" else
                  K.P_CLOSE if car["mode"] == "SHUT" else 0) for car in cars)
        for car in cars:
            if car["mode"] == "DWELL":
                if car["start"] == t:
                    f = car["floor"]
                    keep = []
                    for g in car["riders"]:
                        if calls[g]["dest"] == f:
                            calls[g]["alight"] = t
                            remaining -= 1
                            bump(car, calls[g]["dir"], f, -1)
                        else:
                            keep.append(g)
                    car["riders"] = keep
                    for c in calls:
                        if (c["car"] == car["id"] and c["board"] is None and
                                c["o"] == f and c["dir"] == car["scan"] and
                                c["arr"] <= t and len(car["riders"]) < K.CAPACITY):
                            c["board"] = t
                            car["riders"].append(c["g"])
                            bump(car, c["dir"], f, -1)
                            bump(car, c["dir"], c["dest"], +1)
                if t - car["start"] >= K.DWELL_TICKS and pw + K.P_CLOSE <= budget:
                    pw += K.P_CLOSE
                    car["mode"], car["end"] = "SHUT", t + K.CLOSE_TICKS
                continue
            if car["mode"] != "STILL":
                continue
            want = plan(car, stops(car, U), stops(car, D))
            if want is None:
                continue
            kind, dr = want
            cost = K.P_OPEN if kind == "open" else K.P_TRAVEL
            if pw + cost > budget:
                continue
            pw += cost
            if kind == "open":
                car["mode"], car["end"] = "OPEN", t + K.OPEN_TICKS
            else:
                car["mode"], car["start"], car["end"] = "MOVE", t, t + T
                car["mv"] = 1 if dr == U else -1
        en = 0
        for car in cars:
            if car["mode"] == "MOVE":
                n = len(car["riders"])
                en += 3 + n if car["mv"] > 0 else 3 - n
        trace.append((t, pw, en))
        t += 1
    return trace, calls


def plan(car, up, dn):
    f = car["floor"]
    if not up and not dn:
        car["scan"] = None
        if f == car["home"]:
            return None
        return ("hop", U if car["home"] > f else D)
    sc = car["scan"]
    if sc == U:
        if f in up:
            return ("open", U)
        if any(x > f for x in up | dn):
            return ("hop", U)
    elif sc == D:
        if f in dn:
            return ("open", D)
        if any(x < f for x in up | dn):
            return ("hop", D)
    # nearest commitment; ties -> lower floor, then UP before DOWN
    best = min([(abs(x - f), x, 0) for x in up] + [(abs(x - f), x, 1) for x in dn])
    _, x, side = best
    if x == f:
        car["scan"] = U if side == 0 else D
        return ("open", car["scan"])
    car["scan"] = U if x > f else D
    return ("hop", car["scan"])


def header(n, zoning, timeout, budget):
    return ("CONFIG:{'active_cars': %d, 'zoning': '%s', 'wait_timeout': %d, "
            "'capacity': %d, 'power_budget': %d}" % (n, zoning, timeout,
                                                       K.CAPACITY, budget))


def serial(n, zoning, timeout, budget, trace):
    return "\n".join([header(n, zoning, timeout, budget)] +
                     ["%d,%d,%d" % row for row in trace])


# --------------------------------------------------------------------------
def audit(trace_path, calls_path, cert_path=None):
    """Feasibility audit of delivered baseline artefacts.  Returns list of
    violation strings (empty = accept)."""
    B = K.BASELINE
    n, zn, wt, pb = B["active_cars"], B["zoning"], B["wait_timeout"], B["power_budget"]
    bad = []
    raw = open(trace_path, "rb").read().decode("utf-8")
    lines = raw.split("\n")
    if lines[0] != header(n, zn, wt, pb):
        bad.append("header mismatch: %r" % lines[0])
    rows = []
    for i, ln in enumerate(lines[1:]):
        parts = ln.split(",")
        if len(parts) != 3:
            bad.append("malformed line %d: %r" % (i + 1, ln))
            continue
        tt, p, e = (int(x) for x in parts)
        rows.append((tt, p, e))
        if tt != i:
            bad.append("tick discontinuity at line %d (t=%d)" % (i + 1, tt))
        if p > pb:
            bad.append("tick %d power %d exceeds budget %d" % (tt, p, pb))
        if p < 0:
            bad.append("tick %d negative power" % tt)
        if e < (3 - K.CAPACITY) * n:  # loaded descent floor
            bad.append("tick %d impossible energy %d" % (tt, e))
        if e > (3 + K.CAPACITY) * n:
            bad.append("tick %d energy %d above physical max" % (tt, e))
    tab = call_table()
    recs = json.load(open(calls_path))
    if len(recs) != 80:
        bad.append("expected 80 call records, got %d" % len(recs))
    waits = []
    for r in recs:
        c = tab[r["gidx"]]
        for key, mine in (("origin", "o"), ("dir", "dir"), ("arrival", "arr"),
                          ("dest", "dest")):
            if r[key] != c[mine]:
                bad.append("call %d %s=%r but packet formula gives %r"
                           % (r["gidx"], key, r[key], c[mine]))
        if r["board_t"] is None or r["alight_t"] is None:
            bad.append("call %d never served" % r["gidx"])
            continue
        if r["board_t"] < c["arr"]:
            bad.append("call %d boards at t=%d before its arrival t=%d"
                       % (r["gidx"], r["board_t"], c["arr"]))
        if r["alight_t"] <= r["board_t"]:
            bad.append("call %d alights (t=%d) not after boarding (t=%d)"
                       % (r["gidx"], r["alight_t"], r["board_t"]))
        hist = r.get("assignment_history", [])
        if hist and hist[-1][1] != r["board_car"]:
            bad.append("call %d boarded %s but was assigned to %s"
                       % (r["gidx"], r["board_car"], hist[-1][1]))
        if r["board_car"] in r.get("banned", []):
            bad.append("call %d served by car %s it was reassigned away from"
                       % (r["gidx"], r["board_car"]))
        waits.append(r["board_t"] - c["arr"])
    # capacity: riders aboard per car never exceed CAPACITY
    for car in set(r["board_car"] for r in recs if r["board_car"]):
        evs = sorted([(r["board_t"], 1) for r in recs if r["board_car"] == car] +
                     [(r["alight_t"], -1) for r in recs if r["board_car"] == car],
                     key=lambda x: (x[0], x[1]))
        load = 0
        for _, dlt in evs:
            load += dlt
            if load > K.CAPACITY:
                bad.append("car %s exceeds capacity" % car)
                break
    # independent re-simulation must reproduce trace and call timings
    ref_trace, ref_calls = simulate(n, zn, wt, pb)
    ref = serial(n, zn, wt, pb, ref_trace)
    if ref != raw:
        diff = next((i for i, (a, b) in enumerate(zip(ref.split("\n"), lines))
                     if a != b), min(len(lines), len(ref.split("\n"))))
        bad.append("trace differs from independent re-simulation at line %d" % diff)
    for r in recs:
        rc = ref_calls[r["gidx"]]
        if (r["board_t"], r["alight_t"]) != (rc["board"], rc["alight"]):
            bad.append("call %d board/alight (%s,%s) != independent (%s,%s)"
                       % (r["gidx"], r["board_t"], r["alight_t"], rc["board"],
                          rc["alight"]))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    if cert_path:
        cert = json.load(open(cert_path))
        if cert["certificate"] != digest[:16]:
            bad.append("certificate %s != recomputed %s" % (cert["certificate"],
                                                           digest[:16]))
        if waits and abs(cert["result"]["avg_wait"] - sum(waits) / len(waits)) > 1e-12:
            bad.append("reported avg_wait inconsistent with boarding times")
        if cert["result"]["net_energy"] != sum(e for _, _, e in rows):
            bad.append("reported net_energy != sum of per-tick energy")
    return bad, digest, hashlib.sha256(ref.encode("utf-8")).hexdigest()


def check_sweep(path):
    bad = []
    rows = list(csv.DictReader(open(path)))
    seen = set()
    for r in rows:
        key = (int(r["active_cars"]), r["zoning"], int(r["wait_timeout"]),
               int(r["power_budget"]))
        seen.add(key)
        tr, cl = simulate(*key)
        aw = sum(c["board"] - c["arr"] for c in cl) / 80.0
        ne = sum(e for _, _, e in tr)
        h = hashlib.sha256(serial(*key, tr).encode("utf-8")).hexdigest()[:16]
        if repr(aw) != r["avg_wait"] or ne != int(r["net_energy"]) or h != r["trace_sha16"]:
            bad.append("sweep row %s: primary (%s,%s,%s) vs independent (%r,%d,%s)"
                       % (key, r["avg_wait"], r["net_energy"], r["trace_sha16"],
                          aw, ne, h))
        if max(p for _, p, _ in tr) > key[3]:
            bad.append("sweep row %s: independent engine exceeded budget" % (key,))
    full = {(a, z, w, p) for a in K.SWEEP["active_cars"] for z in K.SWEEP["zoning"]
            for w in K.SWEEP["wait_timeout"] for p in K.SWEEP["power_budget"]}
    if seen != full or len(rows) != 144:
        bad.append("sweep table does not cover exactly the 144 legal configs")
    return bad, rows


def check_decision(dec_path, rows):
    bad = []
    dec = json.load(open(dec_path))
    rr = [dict(cfg=dict(active_cars=int(r["active_cars"]), zoning=r["zoning"],
                        wait_timeout=int(r["wait_timeout"]), capacity=K.CAPACITY,
                        power_budget=int(r["power_budget"])),
               w=float(r["avg_wait"]), e=int(r["net_energy"])) for r in rows]
    w = min(x["w"] for x in rr)
    we = min(x["e"] for x in rr if x["w"] == w)
    e = min(x["e"] for x in rr)
    ew = min(x["w"] for x in rr if x["e"] == e)
    feas = [x for x in rr if x["e"] <= K.ENERGY_CEILING]
    bw = min(x["w"] for x in feas)
    be = min(x["e"] for x in feas if x["w"] == bw)
    for name, (kw, ke) in (("wait_optimal", (w, we)), ("energy_optimal", (ew, e)),
                           ("budget_constrained", (bw, be))):
        d = dec[name]
        if (d["avg_wait"], d["net_energy"]) != (kw, ke):
            bad.append("%s key (%s,%s) != recomputed (%s,%s)"
                       % (name, d["avg_wait"], d["net_energy"], kw, ke))
        match = [x for x in rr if x["cfg"] == d["config"]]
        if not match or (match[0]["w"], match[0]["e"]) != (kw, ke):
            bad.append("%s config does not attain its key" % name)
    return bad


def main():
    args = sys.argv[1:]
    out = args[0]
    tp = os.path.join(out, "baseline_trace.txt")
    cp = os.path.join(out, "baseline_calls.json")
    cert = os.path.join(out, "baseline_certificate.json")
    full = True
    if "--trace" in args:
        tp = args[args.index("--trace") + 1]
        full = False
    if "--calls" in args:
        cp = args[args.index("--calls") + 1]
        full = False
    if "--no-cert" in args or not full:
        cert = None
    bad, dig, refdig = audit(tp, cp, cert)
    report = {"trace_file": tp, "calls_file": cp,
              "delivered_sha256": dig, "delivered_certificate": dig[:16],
              "independent_sha256": refdig, "independent_certificate": refdig[:16]}
    if full:
        sb, rows = check_sweep(os.path.join(out, "sweep_144.csv"))
        bad += sb
        bad += check_decision(os.path.join(out, "decision.json"), rows)
        report["sweep_rows_checked"] = len(rows)
    report["violations"] = bad
    report["verdict"] = "ACCEPT" if not bad else "REJECT"
    print(json.dumps(report, indent=2))
    sys.exit(0 if not bad else 1)


if __name__ == "__main__":
    main()
