"""Export a scenario as a text model for the C branch-and-bound solver.
Format:
  n K Q UB
  price[1..Q]                      (price per metre for a cable of load q)
  nE ; nE lines: i j len           (undirected edges; j==n means substation)
  nC ; nC lines: size e1 e2 ...    (cliques of mutually crossing edges)
"""
import sys, json
from common import Instance

def cliques(I):
    E = I.E; cr = I.cross
    seen = set(); out = []
    for a in range(len(E)):
        for b in sorted(cr[a]):
            if b < a: continue
            C = {a, b}
            cand = sorted(cr[a] & cr[b])
            for c in cand:
                if all(c in cr[d] for d in C):
                    C.add(c)
            key = frozenset(C)
            if key not in seen:
                seen.add(key); out.append(sorted(C))
    # drop cliques dominated by another (subset)
    out.sort(key=len, reverse=True)
    keep = []
    for C in out:
        s = set(C)
        if not any(s <= set(D) for D in keep):
            keep.append(C)
    return keep

def export(scen, ub, path):
    I = Instance(scen)
    Cs = cliques(I)
    with open(path, 'w') as f:
        f.write(f"{I.n} {I.K} {I.Q} {ub}\n")
        f.write(' '.join(str(I.price(q)) for q in range(1, I.Q+1)) + "\n")
        f.write(f"{len(I.E)}\n")
        for (i, j) in I.E:
            f.write(f"{i} {j} {I.L[i][j]}\n")
        f.write(f"{len(Cs)}\n")
        for C in Cs:
            f.write(f"{len(C)} " + ' '.join(map(str, C)) + "\n")
    return I, Cs

if __name__ == '__main__':
    scen = sys.argv[1]; ub = int(sys.argv[2]); path = sys.argv[3]
    I, Cs = export(scen, ub, path)
    print(scen, 'edges', len(I.E), 'cliques', len(Cs), 'max clique', max(map(len, Cs)))
