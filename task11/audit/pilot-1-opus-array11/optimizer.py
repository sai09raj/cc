#!/usr/bin/env python3
"""ARRAY-11 inter-array cable layout optimizer (Python 3 standard library only).

Contains: problem data, exact integer geometry, a capacitated-Prim greedy,
a simulated-annealing local search over rooted spanning trees, and a
Lagrangian lower bound (relaxed flow conservation + Edmonds arborescences).
"""
import math, random, sys, json, time, os

# ---------------------------------------------------------------- data
TURBINES = [
    (4720, -80), (3040, -20), (1680, 20), (80, 40), (780, 340), (5640, 340),
    (2400, 480), (3840, 520), (0, 660), (4700, 700), (1700, 820), (3260, 940),
    (3920, 1040), (700, 1060), (2360, 1080), (5520, 1140), (1440, 1540),
    (-140, 1600), (3220, 1680), (4680, 1700), (2500, 1860), (3920, 1900),
    (840, 1980), (5440, 2140), (1520, 2280), (80, 2380), (3300, 2400),
    (4920, 2440), (3840, 2640), (640, 2680), (5540, 2720), (2520, 2880),
    (-120, 3060), (1700, 3080), (3100, 3180), (4860, 3320), (700, 3520),
    (2560, 3700), (3980, 3700), (5700, 3720), (4740, 3960), (-120, 4000),
    (1600, 4080), (3220, 4120), (3880, 4360), (760, 4380), (5440, 4380),
    (2440, 4480), (1580, 4720), (4920, 4760), (3100, 4780), (-60, 4940),
    (780, 5080), (4080, 5100), (2540, 5240), (5740, 5280), (1540, 5520),
    (3360, 5540), (60, 5600), (4660, 5760), (860, 5840), (4100, 5880),
    (5660, 5960), (2320, 6160),
]
N = len(TURBINES)  # 64
PLATFORMS = {"P": (3200, 3000), "A": (-700, 2700)}   # read from Figure 1
# (name, capacity, price per metre) read from Figure 2
CATALOGUE = [("C1", 4, 100), ("C2", 8, 160), ("C3", 14, 245)]
SCENARIOS = {
    "S1": dict(platform="P", types=["C1", "C2", "C3"], B=6),
    "S2": dict(platform="P", types=["C1", "C2", "C3"], B=5),
    "S3": dict(platform="P", types=["C2", "C3"], B=6),
    "S4": dict(platform="A", types=["C1", "C2", "C3"], B=6),
    "S5": dict(platform="A", types=["C1", "C2", "C3"], B=5),
}
MAX_TT = 1300


def tname(i):
    return "T%02d" % (i + 1) if i < N else "PLATFORM"


def rlen(p, q):
    """Euclidean length rounded to nearest metre, halves up (exact integer)."""
    d2 = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
    return (math.isqrt(4 * d2) + 1) // 2


def orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (v > 0) - (v < 0)


def on_seg(a, b, c):
    """c collinear with a-b assumed; is c within the bounding box of a-b"""
    return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])


def seg_intersect(a, b, c, d):
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 != o2 and o3 != o4 and o1 * o2 <= 0 and o3 * o4 <= 0:
        if o1 != 0 or o2 != 0:
            return True
    if o1 == 0 and on_seg(a, b, c): return True
    if o2 == 0 and on_seg(a, b, d): return True
    if o3 == 0 and on_seg(c, d, a): return True
    if o4 == 0 and on_seg(c, d, b): return True
    return False


def cables_cross(a, b, c, d):
    """Packet rule: segments share a point other than a common endpoint."""
    shared = {a, b} & {c, d}
    if not shared:
        return seg_intersect(a, b, c, d)
    if len(shared) == 2:
        return True
    s = shared.pop()
    p = b if a == s else a
    q = d if c == s else c
    # only possible extra common points: collinear overlap in same direction
    if orient(s, p, q) != 0:
        return False
    return (p[0] - s[0]) * (q[0] - s[0]) + (p[1] - s[1]) * (q[1] - s[1]) > 0


# ---------------------------------------------------------------- instance
class Instance:
    def __init__(self, scen):
        cfg = SCENARIOS[scen]
        self.name = scen
        self.B = cfg["B"]
        self.pname = cfg["platform"]
        self.root = N
        self.pts = list(TURBINES) + [PLATFORMS[cfg["platform"]]]
        types = [c for c in CATALOGUE if c[0] in cfg["types"]]
        types.sort(key=lambda c: c[1])
        self.types = []          # (name, lo, cap, price)
        lo = 1
        for nm, cap, pr in types:
            self.types.append((nm, lo, cap, pr))
            lo = cap + 1
        self.maxcap = self.types[-1][2]
        self.price = [0] * (self.maxcap + 1)
        self.tname_by_load = [None] * (self.maxcap + 1)
        for nm, lo, cap, pr in self.types:
            for l in range(lo, cap + 1):
                self.price[l] = pr
                self.tname_by_load[l] = nm
        R = self.root
        P = self.pts
        # candidate undirected edges (u < v), v == R for feeders
        self.edges = []
        for u in range(N):
            for v in range(u + 1, N + 1):
                L = rlen(P[u], P[v])
                if v < N and L > MAX_TT:
                    continue
                # an edge passing through any other occupied point can never be
                # used (every turbine / the platform has at least one cable)
                bad = False
                for w in range(N + 1):
                    if w in (u, v):
                        continue
                    if orient(P[u], P[v], P[w]) == 0 and on_seg(P[u], P[v], P[w]):
                        bad = True
                        break
                if not bad:
                    self.edges.append((u, v, L))
        self.eid = {}
        for k, (u, v, L) in enumerate(self.edges):
            self.eid[(u, v)] = k
            self.eid[(v, u)] = k
        self.L = {}
        for (u, v, L) in self.edges:
            self.L[(u, v)] = L
            self.L[(v, u)] = L
        self.adj = [[] for _ in range(N + 1)]
        for (u, v, L) in self.edges:
            self.adj[u].append(v)
            self.adj[v].append(u)
        # crossing bitmasks
        E = len(self.edges)
        self.cross = [0] * E
        for a in range(E):
            ua, va, _ = self.edges[a]
            for b in range(a + 1, E):
                ub, vb, _ = self.edges[b]
                if cables_cross(P[ua], P[va], P[ub], P[vb]):
                    self.cross[a] |= 1 << b
                    self.cross[b] |= 1 << a

    def arc_cost(self, i, j, load):
        return self.L[(i, j)] * self.price[load]

    # full evaluation of a parent array (used for verification inside optimizer)
    def evaluate(self, par):
        R = self.root
        ch = [[] for _ in range(N + 1)]
        for i in range(N):
            ch[par[i]].append(i)
        load = [0] * (N + 1)
        order = []
        st = [R]
        seen = 0
        while st:
            x = st.pop()
            order.append(x)
            st.extend(ch[x])
        if len(order) != N + 1:
            raise ValueError("not a tree")
        for x in reversed(order):
            if x != R:
                load[x] = 1 + sum(load[c] for c in ch[x])
        cost = 0
        mask = 0
        for i in range(N):
            if (i, par[i]) not in self.eid:
                raise ValueError("non-candidate edge")
            if load[i] > self.maxcap:
                raise ValueError("over capacity")
            e = self.eid[(i, par[i])]
            if self.cross[e] & mask:
                raise ValueError("crossing")
            mask |= 1 << e
            cost += self.arc_cost(i, par[i], load[i])
        if len(ch[R]) > self.B:
            raise ValueError("too many feeders")
        return cost, load, len(ch[R])


# ---------------------------------------------------------------- greedy
def greedy(inst, rule="marginal"):
    """Capacitated Prim greedy: grow the tree from the platform, each step
    adding the feasible (non-crossing, capacity, feeder, length) connection of
    an unconnected turbine with the smallest marginal cost increase."""
    R = inst.root
    par = [None] * N
    intree = [False] * (N + 1)
    intree[R] = True
    load = [0] * (N + 1)
    mask = 0
    feeders = 0
    for _ in range(N):
        best = None
        for u in range(N):
            if intree[u]:
                continue
            for v in inst.adj[u]:
                if not intree[v]:
                    continue
                if v == R and feeders >= inst.B:
                    continue
                e = inst.eid[(u, v)]
                if inst.cross[e] & mask:
                    continue
                # branch chain of v
                ok = True
                inc = inst.arc_cost(u, v, 1)
                x = v
                while x != R:
                    if load[x] + 1 > inst.maxcap:
                        ok = False
                        break
                    inc += inst.L[(x, par[x])] * (inst.price[load[x] + 1] - inst.price[load[x]])
                    x = par[x]
                if not ok:
                    continue
                key = inc if rule == "marginal" else inst.L[(u, v)]
                if best is None or key < best[0]:
                    best = (key, u, v, e)
        if best is None:
            greedy.partial = (par, load)
            return None
        _, u, v, e = best
        par[u] = v
        intree[u] = True
        mask |= 1 << e
        if v == R:
            feeders += 1
        load[u] = 1
        x = v
        while x != R:
            load[x] += 1
            x = par[x]
    return par


def tree_cost(inst, par):
    """cost of a parent array (no feasibility checks); None if over capacity"""
    R = inst.root
    ch = [[] for _ in range(N + 1)]
    for i in range(N):
        ch[par[i]].append(i)
    order = []
    st = [R]
    while st:
        x = st.pop()
        order.append(x)
        st.extend(ch[x])
    load = [0] * (N + 1)
    cost = 0
    for x in reversed(order):
        if x != R:
            l = 1
            for c in ch[x]:
                l += load[c]
            if l > inst.maxcap:
                return None
            load[x] = l
            cost += inst.L[(x, par[x])] * inst.price[l]
    return cost


def reroot(par, nodes_path):
    """nodes_path = [u, ..., g] path from u up to g (g's parent is dropped);
    reverse parent pointers so that u becomes the top of the subtree"""
    for a in range(len(nodes_path) - 1, 0, -1):
        par[nodes_path[a]] = nodes_path[a - 1]


def esau_williams(inst):
    """Classic Esau-Williams savings heuristic, crossing/capacity/feeder aware.
    Start from the star; repeatedly join a whole feeder branch X (re-rooted at
    turbine u) to a turbine v of another branch through edge u-v, choosing the
    join with the largest exact cost saving; stop when no join saves money and
    the feeder count is within B."""
    R = inst.root
    par = [R] * N
    while True:
        gate = [None] * N
        for i in range(N):
            x = i
            while par[x] != R:
                x = par[x]
            gate[i] = x
        size = {}
        for i in range(N):
            size[gate[i]] = size.get(gate[i], 0) + 1
        mask = 0
        for i in range(N):
            mask |= 1 << inst.eid[(i, par[i])]
        cur = tree_cost(inst, par)
        feeders = len(size)
        best = None
        for (u, v, L) in inst.edges:
            if v == R:
                continue
            for (a, b) in ((u, v), (v, u)):
                ga, gb = gate[a], gate[b]
                if ga == gb or size[ga] + size[gb] > inst.maxcap:
                    continue
                e = inst.eid[(a, b)]
                if inst.cross[e] & (mask & ~(1 << inst.eid[(ga, R)])):
                    continue
                p2 = par[:]
                path = [a]
                while path[-1] != ga:
                    path.append(par[path[-1]])
                reroot(p2, path)
                p2[a] = b
                c = tree_cost(inst, p2)
                if c is None:
                    continue
                if best is None or c < best[0]:
                    best = (c, p2)
        if best is None:
            return par if feeders <= inst.B else None
        if best[0] >= cur and feeders <= inst.B:
            return par
        par = best[1]


# ---------------------------------------------------------------- simulated annealing
def anneal(inst, par0, iters, T0, T1, seed, M=400000):
    """Simulated annealing over feasible-crossing, feasible-capacity trees.
    Move: cut a branch at turbine i (its subtree S), re-root S at any k in S
    and attach k to a neighbour j outside S. Feeder excess over B is
    penalised by M per extra feeder; best penalty-free tree is returned."""
    rng = random.Random(seed)
    R = inst.root
    price = inst.price
    maxcap = inst.maxcap
    Ld = inst.L
    eid = inst.eid
    cross = inst.cross
    adj = inst.adj
    B = inst.B
    par = list(par0) + [None]
    ch = [set() for _ in range(N + 1)]
    for i in range(N):
        ch[par[i]].add(i)
    cost = tree_cost(inst, par[:N])
    load = [0] * (N + 1)

    def calc_load(x):
        l = 1
        for c in ch[x]:
            l += calc_load(c)
        load[x] = l
        return l
    for c in ch[R]:
        calc_load(c)
    mask = 0
    for i in range(N):
        mask |= 1 << eid[(i, par[i])]
    feeders = len(ch[R])
    pen = lambda f: M * (f - B) if f > B else 0
    best = None
    if feeders <= B:
        best = (cost, par[:N])
    inS = [0] * (N + 1)
    stamp = 0
    ratio = (T1 / T0) ** (1.0 / max(1, iters))
    T = T0
    rand = rng.random
    randrange = rng.randrange
    for it in range(iters):
        T *= ratio
        i = randrange(N)
        stamp += 1
        S = [i]
        inS[i] = stamp
        idx = 0
        while idx < len(S):
            for c in ch[S[idx]]:
                inS[c] = stamp
                S.append(c)
            idx += 1
        s = load[i]
        k = i if (len(S) == 1 or rand() < 0.5) else S[randrange(len(S))]
        nb = adj[k]
        j = nb[randrange(len(nb))]
        if j != R and inS[j] == stamp:
            continue
        pi = par[i]
        if k == i and j == pi:
            continue
        e_old = eid[(i, pi)]
        e_new = eid[(k, j)]
        if cross[e_new] & (mask & ~(1 << e_old)):
            continue
        nf = feeders - (pi == R) + (j == R)
        d = pen(nf) - pen(feeders)
        # reversed path k -> ... -> i
        path = [k]
        while path[-1] != i:
            path.append(par[path[-1]])
        for a in range(len(path) - 1):
            u = path[a]
            lu = load[u]
            d += Ld[(u, path[a + 1])] * (price[s - lu] - price[lu])
        d += (Ld[(k, j)] - Ld[(i, pi)]) * price[s]
        dl = {}
        x = pi
        while x != R:
            dl[x] = -s
            x = par[x]
        x = j
        ok = True
        while x != R:
            dl[x] = dl.get(x, 0) + s
            x = par[x]
        for x, dv in dl.items():
            if dv:
                nl = load[x] + dv
                if nl > maxcap:
                    ok = False
                    break
                d += Ld[(x, par[x])] * (price[nl] - price[load[x]])
        if not ok:
            continue
        if d > 0 and rand() >= math.exp(-d / T):
            continue
        # apply
        ch[pi].discard(i)
        newl = [s - load[path[a]] for a in range(len(path) - 1)]
        for a in range(len(path) - 1):
            ch[path[a + 1]].discard(path[a])
        for a in range(len(path) - 1):
            par[path[a + 1]] = path[a]
            ch[path[a]].add(path[a + 1])
            load[path[a + 1]] = newl[a]
        load[k] = s
        par[k] = j
        ch[j].add(k)
        for x, dv in dl.items():
            load[x] += dv
        mask = (mask & ~(1 << e_old)) | (1 << e_new)
        cost += d - (pen(nf) - pen(feeders))
        feeders = nf
        if feeders <= B and (best is None or cost < best[0]):
            best = (cost, par[:N])
    return best


def run_sa(args):
    scen, seed, iters, T0, T1, start = args
    inst = Instance(scen)
    if start is None:
        start = [inst.root] * N
    t = time.time()
    res = anneal(inst, start, iters, T0, T1, seed)
    if res is None:
        return (scen, seed, None, None, time.time() - t)
    c, par = res
    c2, _, f = inst.evaluate(par)
    assert c2 == c, (c, c2)
    return (scen, seed, c, par, time.time() - t)


# ---------------------------------------------------------------- lower bound
def edmonds(nodes, root, arcs):
    """Minimum-weight spanning arborescence (Chu-Liu/Edmonds).
    arcs: list of (u, v, w) meaning u is the parent of v. Returns list of
    chosen arc indices (one entering every node except root)."""
    best = {}
    for idx, (u, v, w) in enumerate(arcs):
        if v == root or u == v:
            continue
        if v not in best or w < arcs[best[v]][2]:
            best[v] = idx
    for v in nodes:
        if v != root and v not in best:
            raise ValueError("no arborescence")
    # find a cycle
    color = {}
    cycle = None
    for v0 in nodes:
        if v0 == root or v0 in color:
            continue
        path = []
        v = v0
        while v != root and v not in color:
            color[v] = v0
            path.append(v)
            v = arcs[best[v]][0]
        if v != root and color.get(v) == v0:
            cyc = [v]
            x = arcs[best[v]][0]
            while x != v:
                cyc.append(x)
                x = arcs[best[x]][0]
            cycle = cyc
            break
    if cycle is None:
        return [best[v] for v in nodes if v != root]
    C = set(cycle)
    c = ("c", id(cycle))
    new_nodes = [v for v in nodes if v not in C] + [c]
    new_arcs = []
    back = []
    for idx, (u, v, w) in enumerate(arcs):
        uin, vin = u in C, v in C
        if uin and vin:
            continue
        if vin:
            new_arcs.append((u, c, w - arcs[best[v]][2]))
        elif uin:
            new_arcs.append((c, v, w))
        else:
            new_arcs.append((u, v, w))
        back.append(idx)
    sub = edmonds(new_nodes, root, new_arcs)
    chosen = [back[s] for s in sub]
    entry_v = None
    for s in sub:
        if new_arcs[s][1] == c:
            entry_v = arcs[back[s]][1]
    for x in cycle:
        if x != entry_v:
            chosen.append(best[x])
    return chosen


def lagrangian_bound(inst, UB, iters=3000, verbose=False, exact=True, cuts=True):
    """Lagrangian relaxation of flow conservation.

    Variables of the relaxed problem: a spanning in-arborescence to the
    platform over candidate edges, and for every chosen arc (i->j) a cable
    type t and an integer load l in [lo_t, cap_t] (and l <= maxcap-1 when j
    is a turbine). Flow conservation l_i = 1 + sum_{children c} l_c is
    dualised with free multipliers rho_i; the feeder limit with pi >= 0.
    Arc weight: L*p_t + l*(rho_i - rho_j) [+ pi if j is the platform];
    minimised exactly per arc (endpoint l), then Edmonds gives the best
    arborescence. Any rho, pi >= 0 yields a valid bound."""
    R = inst.root
    darcs = []  # (i, j, L)
    for (u, v, L) in inst.edges:
        darcs.append((u, v, L))
        if v != R:
            darcs.append((v, u, L))
    opts = []   # per arc: list of (base cost, load)
    for (i, j, L) in darcs:
        o = []
        for (nm, lo, cap, pr) in inst.types:
            hi = cap if j == R else min(cap, inst.maxcap - 1)
            if lo > hi:
                continue
            o.append((L * pr, lo))
            if hi != lo:
                o.append((L * pr, hi))
        opts.append(o)
    nodes = list(range(N + 1))

    eidx = [inst.eid[(i, j)] for (i, j, L) in darcs]
    gam = {}          # (e, f) crossing pair -> multiplier >= 0  (x_e + x_f <= 1)

    def solve(rho, pi, gam):
        epen = {}
        for (e, f), gv in gam.items():
            epen[e] = epen.get(e, 0) + gv
            epen[f] = epen.get(f, 0) + gv
        arcs = []
        chl = []
        for a, (i, j, L) in enumerate(darcs):
            dr = rho[i] - (rho[j] if j != R else 0)
            bw = None
            bl = None
            for (base, l) in opts[a]:
                w = base + l * dr
                if bw is None or w < bw:
                    bw, bl = w, l
            if j == R:
                bw += pi
            bw += epen.get(eidx[a], 0)
            arcs.append((j, i, bw))
            chl.append(bl)
        ch = edmonds(nodes, R, arcs)
        val = sum(arcs[a][2] for a in ch) - sum(rho) - pi * inst.B - sum(gam.values())
        return val, [(darcs[a][0], darcs[a][1], chl[a]) for a in ch]

    rho = [0.0] * N
    pi = 0.0
    best_val = -1e18
    best_mult = (rho[:], pi, dict(gam))
    theta = 1.0
    stall = 0
    for it in range(iters):
        val, sol = solve(rho, pi, gam)
        if val > best_val + 1e-9:
            best_val = val
            best_mult = (rho[:], pi, dict(gam))
            stall = 0
        else:
            stall += 1
            if stall >= 40:
                theta *= 0.6
                stall = 0
                rho, pi, gam = best_mult[0][:], best_mult[1], dict(best_mult[2])
        used = set(inst.eid[(i, j)] for (i, j, l) in sol)
        if cuts:
            ul = sorted(used)
            for a in range(len(ul)):
                ca = inst.cross[ul[a]]
                for b in range(a + 1, len(ul)):
                    if ca >> ul[b] & 1 and (ul[a], ul[b]) not in gam:
                        gam[(ul[a], ul[b])] = 0.0
        g = [-1.0] * N
        deg = 0
        for (i, j, l) in sol:
            g[i] += l
            if j == R:
                deg += 1
            else:
                g[j] -= l
        gp = deg - inst.B
        if pi <= 0 and gp < 0:
            gp = 0
        gg = {}
        for key, gv in gam.items():
            s = (key[0] in used) + (key[1] in used) - 1
            if gv <= 0 and s < 0:
                s = 0
            gg[key] = s
        nrm = sum(x * x for x in g) + gp * gp + sum(x * x for x in gg.values())
        if nrm == 0:
            break
        step = theta * (UB - val) / nrm
        for i in range(N):
            rho[i] += step * g[i]
        pi = max(0.0, pi + step * gp)
        for key, s in gg.items():
            if s:
                gam[key] = max(0.0, gam[key] + step * s)
        if verbose and it % 200 == 0:
            print(it, round(val), round(best_val), theta, file=sys.stderr)
        if theta < 1e-5:
            break
    rho, pi, gam = best_mult
    if exact:
        from fractions import Fraction
        fr = [Fraction(x) for x in rho]
        val, _ = solve(fr, Fraction(pi), {k: Fraction(v) for k, v in gam.items()})
        lb = math.ceil(val)
    else:
        lb = math.ceil(best_val - 1e-6)
    return lb, best_val, (rho, pi, gam)


# ---------------------------------------------------------------- output
def layout_json(inst, par, cost, extra=None):
    _, load, feeders = inst.evaluate(par)
    cables = []
    for i in range(N):
        j = par[i]
        L = inst.L[(i, j)]
        cables.append({"from": tname(i), "to": tname(j), "type": inst.tname_by_load[load[i]],
                       "load": load[i], "length_m": L, "cost": L * inst.price[load[i]]})
    d = {"scenario": inst.name, "platform": inst.pname,
         "platform_xy": list(inst.pts[inst.root]), "feeder_bays_B": inst.B,
         "cable_types": [{"type": t[0], "capacity": t[2], "price_per_m": t[3]} for t in inst.types],
         "total_cost": cost, "feeders_used": feeders, "cables": cables}
    if extra:
        d.update(extra)
    return d


def read_layout(inst, path):
    d = json.load(open(path))
    idx = {tname(i): i for i in range(N)}
    par = [None] * N
    for c in d["cables"]:
        par[idx[c["from"]]] = inst.root if c["to"] == "PLATFORM" else idx[c["to"]]
    return inst.evaluate(par)[0], par


def main():
    import argparse
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", default="S1,S2,S3,S4,S5")
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--iters", type=int, default=10000000)
    ap.add_argument("--T0", type=float, default=60000)
    ap.add_argument("--T1", type=float, default=100)
    ap.add_argument("--lb-iters", type=int, default=4000)
    ap.add_argument("--outdir", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--seed-base", type=int, default=1000)
    ap.add_argument("--keep-best", action="store_true",
                    help="also start stage 2 from an existing layout file and only overwrite if improved")
    a = ap.parse_args()
    scens = a.scenarios.split(",")
    results = {}
    rawp = os.path.join(a.outdir, "results_raw.json")
    if a.keep_best and os.path.exists(rawp):
        results = json.load(open(rawp))
    pool = Pool(a.procs)
    for sc in scens:
        inst = Instance(sc)
        t0 = time.time()
        jobs = [(sc, a.seed_base + s, a.iters, a.T0, a.T1, None) for s in range(a.seeds)]
        runs = pool.map(run_sa, jobs)
        ok = [r for r in runs if r[2] is not None]
        ok.sort(key=lambda r: r[2])
        best_c, best_par = ok[0][2], ok[0][3]
        lp = os.path.join(a.outdir, "layout_%s.json" % sc)
        prev = None
        if a.keep_best and os.path.exists(lp):
            prev = read_layout(inst, lp)
            if prev[0] < best_c:
                best_c, best_par = prev
        if a.keep_best:
            # a layout found for another scenario may also be feasible here
            for other in SCENARIOS:
                op = os.path.join(a.outdir, "layout_%s.json" % other)
                if other == sc or not os.path.exists(op):
                    continue
                try:
                    cand = read_layout(inst, op)
                except ValueError:
                    continue
                if cand[0] < best_c:
                    print("  %s: layout of %s is feasible and cheaper (%d)" % (sc, other, cand[0]), flush=True)
                    best_c, best_par = cand
        # second stage: re-anneal from the best tree at lower temperature
        jobs2 = [(sc, a.seed_base + 5000 + s, a.iters // 2, a.T0 / 6, a.T1, best_par) for s in range(a.seeds // 2)]
        runs2 = pool.map(run_sa, jobs2)
        for r in runs2:
            if r[2] is not None and r[2] < best_c:
                best_c, best_par = r[2], r[3]
        t_heur = time.time() - t0
        t1 = time.time()
        lb, lbval, _ = lagrangian_bound(inst, best_c, iters=a.lb_iters)
        t_lb = time.time() - t1
        ew = esau_williams(inst)
        ew_cost = inst.evaluate(ew)[0] if ew is not None else None
        c, load, feeders = inst.evaluate(best_par)
        assert c == best_c
        if sc in results and a.keep_best:
            old = results[sc]
            res_prev_runs = old.get("sa_costs", []) + old.get("sa_costs_more", [])
        else:
            res_prev_runs = []
        res = dict(cost=c, feeders=feeders, lb=lb, gap=c - lb, gap_pct=100.0 * (c - lb) / c,
                   sa_costs=[r[2] for r in runs], sa2_costs=[r[3] is not None and r[2] for r in runs2],
                   ew_cost=ew_cost, t_heur=t_heur, t_lb=t_lb, lb_dual_value=lbval)
        if a.keep_best and sc in results:
            old = results[sc]
            res["sa_costs"] = old.get("sa_costs", [])
            res["sa_costs_more"] = old.get("sa_costs_more", []) + [r[2] for r in runs]
            res["t_heur"] = old.get("t_heur", 0) + t_heur
        results[sc] = res
        with open(os.path.join(a.outdir, "layout_%s.json" % sc), "w") as f:
            json.dump(layout_json(inst, best_par, c), f, indent=1)
        if ew is not None:
            with open(os.path.join(a.outdir, "greedy_EW_%s.json" % sc), "w") as f:
                json.dump(layout_json(inst, ew, ew_cost, {"note": "Esau-Williams greedy"}), f, indent=1)
        print(sc, json.dumps(res), flush=True)
    with open(os.path.join(a.outdir, "results_raw.json"), "w") as f:
        json.dump(results, f, indent=1)


if __name__ == "__main__":
    main()
