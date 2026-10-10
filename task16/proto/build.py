"""Build 3D geometry from network.py and compute the answer key."""
import json, network as NW
def build():
    nodes = {NW.START[0]: NW.START[1]}; segs = []; fittings = []
    for lid, dn, frm, items in NW.LINES:
        p = nodes[frm]; prev_dir = None; d = dn
        for it in items:
            if isinstance(it, str):
                nodes[it] = p; continue
            dr, L = it[0], it[1]; v = NW.VEC[dr]
            q = (p[0] + v[0] * L, p[1] + v[1] * L, p[2] + v[2] * L)
            segs.append(dict(line=lid, dn=d, a=p, b=q, dir=dr, len=L))
            if prev_dir and prev_dir != dr: fittings.append(("ELL", lid, p))
            if len(it) > 2:
                fittings.append((it[2], lid, q))
                if it[2] == "RED": d = {150: 100, 100: 80, 80: 50}[d]
            prev_dir = dr; p = q
    return nodes, segs, fittings
if __name__ == "__main__":
    nodes, segs, fit = build()
    for k in sorted(nodes): print(k, nodes[k])
    tot = {}
    for s in segs: tot[s["dn"]] = tot.get(s["dn"], 0) + s["len"]
    print("length by DN", tot); from collections import Counter; print(Counter(f[0] for f in fit))
