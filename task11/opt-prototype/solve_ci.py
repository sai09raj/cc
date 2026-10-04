"""Author-side exact solver: capacity-indexed CMST formulation in CP-SAT.
x[i,j,q] = 1 iff turbine i's outgoing cable goes to j and carries exactly q turbines."""
import itertools
import json
import sys
import time
from ortools.sat.python import cp_model
from instance import length, cross


def arc_cost(L, q, types):
    ok = [c for _, cap, c in types if cap >= q]
    return L * min(ok) if ok else None


def solve(inst, max_feeders, time_limit=600, workers=4, log=False):
    P = [tuple(inst["substation"])] + [tuple(p) for p in inst["turbines"]]
    n = len(P) - 1
    types = inst["types"]
    Q = max(c for _, c, _ in types)
    dmax = inst.get("dmax", 10 ** 9)
    m = cp_model.CpModel()
    x = {}
    arcs = []
    for i in range(1, n + 1):
        for j in range(0, n + 1):
            if i == j:
                continue
            Lij = length(P[i], P[j])
            if j != 0 and Lij > dmax:
                continue
            arcs.append((i, j))
            for q in range(1, Q + 1):
                x[i, j, q] = m.NewBoolVar(f"x{i}_{j}_{q}")
    out = {i: [(j, q) for (a, j, q) in x if a == i] for i in range(1, n + 1)}
    inn = {i: [(k, q) for (k, b, q) in x if b == i] for i in range(1, n + 1)}
    for i in range(1, n + 1):
        m.AddExactlyOne(x[i, j, q] for j, q in out[i])
        m.Add(sum(q * x[i, j, q] for j, q in out[i]) - sum(q * x[k, i, q] for k, q in inn[i]) == 1)
    m.Add(sum(x[i, 0, q] for i in range(1, n + 1) for q in range(1, Q + 1) if (i, 0, q) in x) <= max_feeders)
    arcset = set(arcs)

    def lits(a, b):
        r = []
        for (u, v) in ((a, b), (b, a)):
            if (u, v) in arcset:
                r += [x[u, v, q] for q in range(1, Q + 1)]
        return r

    edges = sorted({(min(i, j), max(i, j)) for i, j in arcs})
    ncross = 0
    for e1, e2 in itertools.combinations(edges, 2):
        if cross(P[e1[0]], P[e1[1]], P[e2[0]], P[e2[1]]):
            m.Add(sum(lits(*e1) + lits(*e2)) <= 1)
            ncross += 1
    m.Minimize(sum(arc_cost(length(P[i], P[j]), q, types) * v for (i, j, q), v in x.items()))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_search_workers = workers
    s.parameters.log_search_progress = log
    t0 = time.time()
    st = s.Solve(m)
    sol = sorted((i, j, q) for (i, j, q), v in x.items() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) and s.Value(v))
    return dict(status=s.StatusName(st), obj=s.ObjectiveValue() if sol else None, bound=s.BestObjectiveBound(),
                time=round(time.time() - t0, 1), crossing_pairs=ncross, arcs=sol)


if __name__ == "__main__":
    inst = json.load(open(sys.argv[1]))
    r = solve(inst, int(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 600)
    print(json.dumps({k: v for k, v in r.items() if k != "arcs"}))
