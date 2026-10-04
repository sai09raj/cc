"""Greedy (Esau-Williams) and simulated-annealing local search for upper bounds."""
import sys, random, math, json
from common import Instance

def edges_of(I, parent):
    return {I.eid[(i, parent[i])] for i in range(I.n)}

def crosses_any(I, e, used, skip=()):
    c = I.cross[e]
    for f in used:
        if f in c and f not in skip:
            return True
    return False

def esau_williams(I):
    n, R = I.n, I.root
    parent = [R]*n
    comp = list(range(n))           # component id = gate turbine
    members = {i: [i] for i in range(n)}
    used = set(edges_of(I, parent))
    # Note: all-to-root star may itself contain crossings (collinear root edges); fixed as merges proceed.
    def cost(par):
        c, _ = I.evaluate(par); return c
    cur = cost(parent)
    while True:
        best = None
        feeders = len(members)
        for g, mem in members.items():
            size = len(mem)
            for i in mem:
                for j in I.nbr[i]:
                    if j == R or comp[j] == g: continue
                    if size + len(members[comp[j]]) > I.Q: continue
                    # reroot component g at i, hang under j
                    e = I.eid[(i, j)]
                    if crosses_any(I, e, used, skip={I.eid[(g, R)]}): continue
                    newp = reroot(parent, g, i, j, R)
                    c = cost(newp)
                    if c is None: continue
                    sav = cur - c
                    if best is None or sav > best[0]:
                        best = (sav, newp, g, j)
        if best is None: break
        if best[0] <= 0 and feeders <= I.K: break
        sav, newp, g, j = best
        parent = newp; cur -= sav
        tg = comp[j]
        for v in members[g]: comp[v] = tg
        members[tg] += members.pop(g)
        used = edges_of(I, parent)
    ok = len(members) <= I.K and not any(I.cross[e] & used for e in used)
    return parent, cur, ok

def reroot(parent, top, k, p, R):
    """subtree rooted at `top` (k inside it): reverse path k..top, set parent[k]=p."""
    newp = list(parent)
    v = k; prev = p
    while True:
        nxt = parent[v]
        newp[v] = prev
        if v == top: break
        prev = v; v = nxt
    return newp

def subtree_flags(I, parent, top):
    n = I.n
    ch = [[] for _ in range(n+1)]
    for i in range(n): ch[parent[i]].append(i)
    st = [top]; mark = set()
    while st:
        v = st.pop(); mark.add(v); st.extend(ch[v])
    return mark

PEN = 400000
def pcost(I, parent):
    c, _ = I.evaluate(parent)
    if c is None: return None
    f = sum(1 for p in parent if p == I.root)
    return c + PEN*max(0, f - I.K)

def anneal(I, parent, iters=200000, T0=3000.0, T1=5.0, seed=0):
    rnd = random.Random(seed)
    n, R = I.n, I.root
    cur = pcost(I, parent)
    feas = lambda p: sum(1 for v in p if v == R) <= I.K
    best, bestp = (cur, list(parent)) if feas(parent) else (None, None)
    used = edges_of(I, parent)
    for it in range(iters):
        T = T0 * (T1/T0) ** (it/iters)
        k = rnd.randrange(n)
        p = rnd.choice(I.nbr[k])
        if p == parent[k]: continue
        # choose ancestor top on path k->root
        path = [k]
        while parent[path[-1]] != R: path.append(parent[path[-1]])
        top = path[rnd.randrange(len(path))] if rnd.random() < 0.5 else k
        sub = subtree_flags(I, parent, top)
        if p in sub: continue
        e = I.eid[(k, p)]
        old = I.eid[(top, parent[top])]
        if crosses_any(I, e, used, skip={old}): continue
        newp = reroot(parent, top, k, p, R)
        c = pcost(I, newp)
        if c is None: continue
        d = c - cur
        if d <= 0 or rnd.random() < math.exp(-d/T):
            parent = newp; cur = c
            used.discard(old); used.add(e)
            if (best is None or cur < best) and feas(parent):
                best, bestp = cur, list(parent)
    return best, bestp

if __name__ == '__main__':
    scen = sys.argv[1]
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 200000
    I = Instance(scen)
    gp, gc, ok = esau_williams(I)
    print(scen, 'greedy EW cost', gc, 'feasible', ok, flush=True)
    best, bp = (gc, gp) if ok else (None, None)
    seed0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    for r in range(seed0, seed0+runs):
        c, p = anneal(I, gp, iters=iters, seed=r)
        print(' SA run', r, c, flush=True)
        if c is not None and (best is None or c < best): best, bp = c, p
    try:
        old = json.load(open(f'ub_{scen}.json'))
        if old['cost'] <= best: best, bp = old['cost'], old['parent']
    except Exception: pass
    print(scen, 'best', best)
    json.dump({'scenario': scen, 'greedy_cost': gc, 'greedy_parent': gp, 'cost': best, 'parent': bp},
              open(f'ub_{scen}.json', 'w'))
