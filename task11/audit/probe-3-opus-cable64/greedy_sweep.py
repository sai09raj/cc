"""Simple 'sweep + Prim' greedy: split turbines into K angular sectors around the substation,
connect each sector's closest turbine to the substation and grow a nearest-neighbour (Prim)
tree inside the sector, skipping edges that would cross existing cables. Best over all
sector rotations."""
import math
from common import Instance

def sweep_prim(I, sizes=None):
    n, R = I.n, I.root
    sx, sy = I.P[R]
    order = sorted(range(n), key=lambda i: math.atan2(I.P[i][1]-sy, I.P[i][0]-sx))
    K = I.K
    if sizes is None: sizes = [n//K + (1 if g < n % K else 0) for g in range(K)]
    K = len(sizes)
    best = None
    for rot in range(n):
        seq = order[rot:] + order[:rot]
        groups = []; pos = 0
        for s in sizes:
            groups.append(seq[pos:pos+s]); pos += s
        parent = [None]*n; used = set(); ok = True
        for G in groups:
            gate = min(G, key=lambda i: I.L[i][R])
            e = I.eid[(gate, R)]
            if I.cross[e] & used: ok = False; break
            parent[gate] = R; used.add(e)
            intree = {gate}; rest = set(G) - intree
            while rest:
                cand = None
                for v in rest:
                    for u in I.nbr[v]:
                        if u in intree:
                            e = I.eid[(u, v)]
                            if I.cross[e] & used: continue
                            if cand is None or I.L[u][v] < cand[0]:
                                cand = (I.L[u][v], v, u, e)
                if cand is None: ok = False; break
                _, v, u, e = cand
                parent[v] = u; used.add(e); intree.add(v); rest.discard(v)
            if not ok: break
        if not ok: continue
        c, _ = I.evaluate(parent)
        if c is not None and (best is None or c < best[0]):
            best = (c, parent)
    return best

def sweep_any(I, tries=150, seed=0):
    import random
    rnd = random.Random(seed)
    best = sweep_prim(I)
    for _ in range(tries):
        while True:
            cuts = sorted(rnd.sample(range(1, I.n), I.K - 1))
            sizes = [b - a for a, b in zip([0] + cuts, cuts + [I.n])]
            if max(sizes) <= I.Q: break
        b = sweep_prim(I, sizes)
        if b and (best is None or b[0] < best[0]): best = b
    return best

if __name__ == '__main__' and 'any' in __import__('sys').argv:
    for s in ['S1', 'S2', 'S3', 'S4']:
        I = Instance(s); b = sweep_any(I)
        print(s, 'sweep(any sizes)', b[0] if b else None, flush=True)
elif __name__ == '__main__':
    for s in ['S1', 'S2', 'S3', 'S4']:
        I = Instance(s); b = sweep_prim(I)
        print(s, b[0] if b else None)

def cap_prim(I, root_weight=1.0):
    """Capacitated Prim: repeatedly attach the unconnected turbine with the shortest
    feasible (non-crossing, capacity- and feeder-respecting) cable to the growing forest."""
    n, R = I.n, I.root
    parent = [None]*n; gate = [None]*n; size = {}; used = set(); feeders = 0
    intree = {R}
    for _ in range(n):
        cand = None
        for v in range(n):
            if parent[v] is not None: continue
            for u in I.nbr[v]:
                if u not in intree: continue
                if u == R:
                    if feeders >= I.K: continue
                    w = I.L[v][R]*root_weight
                else:
                    if size[gate[u]] >= I.Q: continue
                    w = I.L[v][u]
                e = I.eid[(u, v)]
                if I.cross[e] & used: continue
                if cand is None or w < cand[0]:
                    cand = (w, v, u, e)
        if cand is None: return None
        _, v, u, e = cand
        parent[v] = u; used.add(e); intree.add(v)
        if u == R: gate[v] = v; size[v] = 1; feeders += 1
        else: gate[v] = gate[u]; size[gate[v]] += 1
    c, _ = I.evaluate(parent)
    return (c, parent) if c is not None else None

if __name__ == '__main__':
    for s in ['S1', 'S2', 'S3', 'S4']:
        I = Instance(s)
        print(s, 'capPrim', [ (w, (lambda b: b[0] if b else None)(cap_prim(I, w))) for w in (1.0, 0.5, 0.3)])
