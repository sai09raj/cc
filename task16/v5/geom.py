"""Derive node coordinates, per-line segments, lengths, elbows and fittings from plant.py."""
import plant as P
def build():
    nodes = {P.START[0]: P.START[1], "TK1": P.TK1_OUTLET}; lines = {}
    for lid, dn, frm, items in P.LINES:
        p = nodes[frm]; pieces = []; cur = dict(frm=frm, moves=[], fit=[]); prev = None
        for it in items:
            if isinstance(it, str):
                if it in nodes and it != frm:
                    assert all(abs(a - b) < 1e-6 for a, b in zip(nodes[it], p)), (lid, it, nodes[it], p)
                nodes[it] = p; cur["to"] = it; pieces.append(cur); cur = dict(frm=it, moves=[], fit=[]); continue
            v = P.VEC[it[0]]; q = tuple(p[i] + v[i] * it[1] for i in range(3))
            cur["moves"].append(it); p = q
            if len(it) > 2: cur["fit"].append(it[2])
        for pc in pieces:
            mv = pc["moves"]; pc["L"] = sum(m[1] for m in mv) / 1000.0
            pc["elbows"] = sum(1 for a, b in zip(mv, mv[1:]) if a[0] != b[0])
            pc["dn"] = dn; pc["line"] = lid
        lines[lid] = pieces
    return nodes, lines
if __name__ == "__main__":
    n, l = build()
    for k, v in n.items(): print(k, v)
    for lid, pcs in l.items():
        for pc in pcs: print(lid, pc["frm"], "->", pc["to"], "L", pc["L"], "ell", pc["elbows"], pc["fit"])
