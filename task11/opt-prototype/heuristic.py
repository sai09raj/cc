"""Stdlib heuristics for the array-cable prototype: Esau-Williams + local improvement.
Used to measure how close a plausible non-exact solver gets."""
import json
import sys
from instance import length, cross


def tree_cost(inst, parent):
    """parent[i] = next node toward substation for turbine i (1..n). Cost with cheapest cable per arc."""
    P = [tuple(inst["substation"])] + [tuple(p) for p in inst["turbines"]]
    n = len(P) - 1
    types = inst["types"]
    load = [0] * (n + 1)
    for i in range(1, n + 1):
        j = i
        seen = 0
        while j != 0:
            load[j] += 1
            j = parent[j]
            seen += 1
            if seen > n:
                return None
    total = 0
    for i in range(1, n + 1):
        ok = [c for _, cap, c in types if cap >= load[i]]
        if not ok:
            return None
        total += length(P[i], P[parent[i]]) * min(ok)
    return total


def feasible_cross(inst, parent):
    P = [tuple(inst["substation"])] + [tuple(p) for p in inst["turbines"]]
    segs = [(i, parent[i]) for i in range(1, len(P))]
    for a in range(len(segs)):
        for b in range(a + 1, len(segs)):
            if cross(P[segs[a][0]], P[segs[a][1]], P[segs[b][0]], P[segs[b][1]]):
                return False
    return True


def feeders(parent):
    return sum(1 for i in range(1, len(parent)) if parent[i] == 0)


def esau_williams(inst, max_feeders):
    P = [tuple(inst["substation"])] + [tuple(p) for p in inst["turbines"]]
    n = len(P) - 1
    cap = max(c for _, c, _ in inst["types"])
    parent = [0] * (n + 1)
    comp = list(range(n + 1))
    size = {i: 1 for i in range(1, n + 1)}
    gate = {i: length(P[i], P[0]) for i in range(1, n + 1)}
    while True:
        best = None
        for i in range(1, n + 1):
            ci = comp[i]
            for j in range(1, n + 1):
                cj = comp[j]
                if ci == cj or size[ci] + size[cj] > cap or (i, j) in esau_williams.blocked:
                    continue
                if length(P[i], P[j]) > inst.get("dmax", 10**9):
                    continue
                save = gate[ci] - length(P[i], P[j])
                if save <= 0:
                    continue
                # tentative: component ci's root edge (to 0) replaced by i->j; reroot ci at i
                if best is None or save > best[0]:
                    best = (save, i, j)
        if best is None:
            break
        _, i, j = best
        ci, cj = comp[i], comp[j]
        # reroot component ci at i
        trial = parent[:]
        path = [i]
        while trial[path[-1]] != 0:
            path.append(trial[path[-1]])
        for a, b in zip(path[1:], path[:-1]):
            trial[a] = b
        trial[i] = j
        if not feasible_cross(inst, trial) or tree_cost(inst, trial) is None:
            # forbid by inflating: simple fallback, mark pair unusable
            gate_backup = gate[ci]
            gate[ci] = -1  # temporarily block this component
            # try others; restore after loop iteration
            best2 = None
            gate[ci] = gate_backup
            # skip this pair permanently via a blocked set
            esau_williams.blocked.add((i, j))
            continue
        parent = trial
        for k in range(1, n + 1):
            if comp[k] == ci:
                comp[k] = cj
        size[cj] += size.pop(ci)
        gate.pop(ci)
    return parent


esau_williams.blocked = set()


def local_search(inst, parent, max_feeders, rounds=50):
    n = len(parent) - 1
    best = parent[:]
    bc = tree_cost(inst, best)
    improved = True
    it = 0
    while improved and it < rounds:
        improved = False
        it += 1
        for i in range(1, n + 1):
            for j in range(0, n + 1):
                if j == i or j == best[i]:
                    continue
                trial = best[:]
                trial[i] = j
                c = tree_cost(inst, trial)
                if c is None or c >= bc or feeders(trial) > max_feeders:
                    continue
                Q = [tuple(inst["substation"])] + [tuple(p) for p in inst["turbines"]]
                if j != 0 and length(Q[i], Q[j]) > inst.get("dmax", 10**9):
                    continue
                if not feasible_cross(inst, trial):
                    continue
                best, bc = trial, c
                improved = True
    return best, bc


if __name__ == "__main__":
    inst = json.load(open(sys.argv[1]))
    mf = int(sys.argv[2])
    p = esau_williams(inst, mf)
    c0 = tree_cost(inst, p)
    print("EW cost", c0, "feeders", feeders(p), "cross-free", feasible_cross(inst, p))
    p2, c1 = local_search(inst, p, mf)
    print("EW+LS cost", c1, "feeders", feeders(p2), "cross-free", feasible_cross(inst, p2))
