#!/usr/bin/env python3
"""Independent layout checker (does not import any optimizer code).

usage: python3 checker.py layout.json [field.json]
layout.json: {"scenario": "S1", "cost": <int>, "cables": {"T01": {"to": "T07" | "SUB", "type": "C2"}, ...}}
Validates every rule of the specification and recomputes the cost exactly.
"""
import json, sys, os
from fractions import Fraction

CABLES = {'C1': (4, 100), 'C2': (8, 160), 'C3': (14, 245)}
SCEN = {'S1': ('substation_primary', ('C1', 'C2', 'C3'), 6),
        'S2': ('substation_primary', ('C1', 'C2', 'C3'), 5),
        'S3': ('substation_primary', ('C2', 'C3'), 6),
        'S4': ('substation_alternative', ('C1', 'C2', 'C3'), 6)}

def length(p, q):
    """Euclidean distance rounded to nearest integer, halves up (exact integer arithmetic)."""
    s = (p[0]-q[0])**2 + (p[1]-q[1])**2
    # integer sqrt by Newton
    if s == 0: return 0
    r = s
    y = (r + 1) // 2
    while y < r:
        r = y; y = (r + s // r) // 2
    # r = floor(sqrt(s)); round half up: compare s with (r+1/2)^2  <=> 4s vs (2r+1)^2
    return r + 1 if 4*s >= (2*r+1)**2 else r

def common_points(a, b, c, d):
    """Return the set of intersection of closed segments ab and cd as:
    None (empty), ('pt', point as Fractions) or ('seg', p, q) for collinear overlap of positive length."""
    def cross(o, p, q): return (p[0]-o[0])*(q[1]-o[1]) - (p[1]-o[1])*(q[0]-o[0])
    rx, ry = b[0]-a[0], b[1]-a[1]
    sx, sy = d[0]-c[0], d[1]-c[1]
    den = rx*sy - ry*sx
    qpx, qpy = c[0]-a[0], c[1]-a[1]
    if den != 0:
        t = Fraction(qpx*sy - qpy*sx, den)
        u = Fraction(qpx*ry - qpy*rx, den)
        if 0 <= t <= 1 and 0 <= u <= 1:
            return ('pt', (a[0] + t*rx, a[1] + t*ry))
        return None
    if cross(a, b, c) != 0:
        return None          # parallel, not collinear
    # collinear: project onto ab parameter
    rr = rx*rx + ry*ry
    t0 = Fraction(qpx*rx + qpy*ry, rr)
    t1 = Fraction((d[0]-a[0])*rx + (d[1]-a[1])*ry, rr)
    lo, hi = max(Fraction(0), min(t0, t1)), min(Fraction(1), max(t0, t1))
    if lo > hi: return None
    pl = (a[0] + lo*rx, a[1] + lo*ry); ph = (a[0] + hi*rx, a[1] + hi*ry)
    if lo == hi: return ('pt', pl)
    return ('seg', pl, ph)

def cables_cross(a, b, c, d):
    inter = common_points(a, b, c, d)
    if inter is None: return False
    if inter[0] == 'seg': return True        # collinear overlap always counts
    p = inter[1]
    shared = {tuple(a), tuple(b)} & {tuple(c), tuple(d)}
    return not (p in {(Fraction(s[0]), Fraction(s[1])) for s in shared})

def check(layout, field):
    errs = []
    scen = layout['scenario']
    sub_key, allowed, K = SCEN[scen]
    sub = tuple(field[sub_key]); tur = {k: tuple(v) for k, v in field['turbines'].items()}
    cab = layout['cables']
    if set(cab) != set(tur): errs.append('turbine set mismatch')
    pos = dict(tur); pos['SUB'] = sub
    for t, c in cab.items():
        if c['to'] not in pos or c['to'] == t: errs.append(f'{t}: bad endpoint {c["to"]}')
    if errs: return errs, None
    # reachability / acyclicity
    for t in cab:
        seen = set(); v = t
        while v != 'SUB':
            if v in seen: errs.append(f'{t}: cycle'); break
            seen.add(v); v = cab[v]['to']
    if errs: return errs, None
    load = {t: 0 for t in cab}
    for t in cab:
        v = t
        while v != 'SUB':
            load[v] += 1; v = cab[v]['to']
    total = 0
    avail = sorted((CABLES[n][0], CABLES[n][1], n) for n in allowed)
    for t, c in cab.items():
        L = length(pos[t], pos[c['to']])
        if c['to'] != 'SUB' and L > 1300: errs.append(f'{t}->{c["to"]}: length {L} > 1300')
        fit = [x for x in avail if x[0] >= load[t]]
        if not fit: errs.append(f'{t}: load {load[t]} exceeds all capacities'); continue
        cheapest = min(fit, key=lambda x: x[1])
        if c.get('type') != cheapest[2]: errs.append(f'{t}: type {c.get("type")} but cheapest admissible is {cheapest[2]} (load {load[t]})')
        total += L * cheapest[1]
    feeders = sum(1 for c in cab.values() if c['to'] == 'SUB')
    if feeders > K: errs.append(f'{feeders} feeders > {K}')
    segs = [(t, pos[t], pos[c['to']]) for t, c in cab.items()]
    for i in range(len(segs)):
        for j in range(i+1, len(segs)):
            if cables_cross(segs[i][1], segs[i][2], segs[j][1], segs[j][2]):
                errs.append(f'cables from {segs[i][0]} and {segs[j][0]} cross')
    if 'cost' in layout and layout['cost'] != total:
        errs.append(f'stated cost {layout["cost"]} != recomputed {total}')
    return errs, {'cost': total, 'feeders': feeders, 'max_load': max(load.values())}

if __name__ == '__main__':
    lay = json.load(open(sys.argv[1]))
    fpath = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'field.json')
    errs, info = check(lay, json.load(open(fpath)))
    if errs:
        print('INVALID'); [print('  ' + e) for e in errs]; sys.exit(1)
    print(f"VALID {lay['scenario']} cost={info['cost']} feeders={info['feeders']} max_load={info['max_load']}")
