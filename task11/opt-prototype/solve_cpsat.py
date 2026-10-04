"""Author-side exact solver (CP-SAT) for the array-cable prototype. Not for solvers."""
import itertools
import json
import sys
import time
from ortools.sat.python import cp_model
from instance import length, cross


def solve(inst, max_feeders, time_limit=600, workers=8, log=False):
    S = tuple(inst["substation"])
    T = [tuple(p) for p in inst["turbines"]]
    P = [S] + T                       # node 0 = substation
    n = len(T)
    types = inst["types"]
    edges = [(i, j) for i in range(n + 1) for j in range(i + 1, n + 1)]
    L = {(i, j): length(P[i], P[j]) for i, j in edges}
    m = cp_model.CpModel()
    x = {}   # directed arc i->j (toward substation): i turbine, j any other node
    y = {}
    f = {}
    for i in range(1, n + 1):
        for j in range(0, n + 1):
            if i == j or (j != 0 and length(P[i], P[j]) > inst.get("dmax", 10**9)):
                continue
            x[i, j] = m.NewBoolVar(f"x{i}_{j}")
            f[i, j] = m.NewIntVar(0, n, f"f{i}_{j}")
            for t, (_, cap, _) in enumerate(types):
                y[i, j, t] = m.NewBoolVar(f"y{i}_{j}_{t}")
            m.Add(sum(y[i, j, t] for t in range(len(types))) == x[i, j])
            m.Add(f[i, j] <= sum(cap * y[i, j, t] for t, (_, cap, _) in enumerate(types)))
            m.Add(f[i, j] >= x[i, j])
    for i in range(1, n + 1):
        m.AddExactlyOne(x[i, j] for j in range(0, n + 1) if (i, j) in x)
        out_f = sum(f[i, j] for j in range(0, n + 1) if (i, j) in f)
        in_f = sum(f[k, i] for k in range(1, n + 1) if (k, i) in f)
        m.Add(out_f - in_f == 1)
    m.Add(sum(x[i, 0] for i in range(1, n + 1) if (i, 0) in x) <= max_feeders)

    def used(e):
        i, j = e
        lits = []
        if i != 0 and (i, j) in x:
            lits.append(x[i, j])
        if j != 0 and (j, i) in x:
            lits.append(x[j, i])
        return lits

    ncross = 0
    for e1, e2 in itertools.combinations(edges, 2):
        u1, u2 = used(e1), used(e2)
        if u1 and u2 and cross(P[e1[0]], P[e1[1]], P[e2[0]], P[e2[1]]):
            m.Add(sum(u1 + u2) <= 1)
            ncross += 1
    cost = []
    for (i, j), v in y.items() if False else []:
        pass
    obj = []
    for (i, j, t), v in y.items():
        a, b = min(i, j), max(i, j)
        obj.append(L[a, b] * types[t][2] * v)
    m.Minimize(sum(obj))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_search_workers = workers
    s.parameters.log_search_progress = log
    t0 = time.time()
    st = s.Solve(m)
    sol = []
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for (i, j, t), v in y.items():
            if s.Value(v):
                sol.append((i, j, types[t][0], s.Value(f[i, j])))
    return dict(status=s.StatusName(st), obj=s.ObjectiveValue() if sol else None,
                bound=s.BestObjectiveBound(), time=round(time.time() - t0, 1),
                crossing_pairs=ncross, arcs=sorted(sol))


if __name__ == "__main__":
    inst = json.load(open(sys.argv[1]))
    mf = int(sys.argv[2]) if len(sys.argv) > 2 else 99
    tl = float(sys.argv[3]) if len(sys.argv) > 3 else 600
    r = solve(inst, mf, tl)
    print(json.dumps({k: v for k, v in r.items() if k != "arcs"}))
    print(r["arcs"])
