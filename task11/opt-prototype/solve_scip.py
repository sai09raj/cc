"""Second certification: capacity-indexed model solved with SCIP (LP-based MIP) instead of CP-SAT."""
import itertools
import json
import time
from ortools.linear_solver import pywraplp
from instance import length, cross


def solve(inst, max_feeders, time_limit=1800):
    P = [tuple(inst["substation"])] + [tuple(p) for p in inst["turbines"]]
    n = len(P) - 1
    types = inst["types"]
    Q = max(c for _, c, _ in types)
    dmax = inst.get("dmax", 10 ** 9)
    s = pywraplp.Solver.CreateSolver("SCIP")
    s.SetTimeLimit(int(time_limit * 1000))
    x, arcs = {}, []
    for i in range(1, n + 1):
        for j in range(0, n + 1):
            if i == j or (j != 0 and length(P[i], P[j]) > dmax):
                continue
            arcs.append((i, j))
            for q in range(1, Q + 1):
                x[i, j, q] = s.BoolVar(f"x{i}_{j}_{q}")
    for i in range(1, n + 1):
        outs = [(j, q) for (a, j, q) in x if a == i]
        ins = [(k, q) for (k, b, q) in x if b == i]
        s.Add(sum(x[i, j, q] for j, q in outs) == 1)
        s.Add(sum(q * x[i, j, q] for j, q in outs) - sum(q * x[k, i, q] for k, q in ins) == 1)
    s.Add(sum(x[i, 0, q] for i in range(1, n + 1) for q in range(1, Q + 1) if (i, 0, q) in x) <= max_feeders)
    arcset = set(arcs)

    def lits(a, b):
        r = []
        for u, v in ((a, b), (b, a)):
            if (u, v) in arcset:
                r += [x[u, v, q] for q in range(1, Q + 1)]
        return r

    for e1, e2 in itertools.combinations(sorted({(min(i, j), max(i, j)) for i, j in arcs}), 2):
        if cross(P[e1[0]], P[e1[1]], P[e2[0]], P[e2[1]]):
            s.Add(sum(lits(*e1) + lits(*e2)) <= 1)

    def cost(i, j, q):
        return length(P[i], P[j]) * min(c for _, cap, c in types if cap >= q)

    s.Minimize(sum(cost(i, j, q) * v for (i, j, q), v in x.items() if any(cap >= q for _, cap, _ in types)))
    for (i, j, q), v in x.items():
        if not any(cap >= q for _, cap, _ in types):
            s.Add(v == 0)
    t0 = time.time()
    st = s.Solve()
    names = {pywraplp.Solver.OPTIMAL: "OPTIMAL", pywraplp.Solver.FEASIBLE: "FEASIBLE",
             pywraplp.Solver.INFEASIBLE: "INFEASIBLE", pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED"}
    return dict(status=names.get(st, str(st)), obj=round(s.Objective().Value()),
                bound=round(s.Objective().BestBound()), time=round(time.time() - t0, 1))


if __name__ == "__main__":
    d = json.load(open("scen48.json"))
    for name, e in d.items():
        r = solve(e["inst"], e["scenario"]["mf"])
        print(name, r, "CP-SAT", e["result"]["obj"], "agree", r["obj"] == e["result"]["obj"], flush=True)
