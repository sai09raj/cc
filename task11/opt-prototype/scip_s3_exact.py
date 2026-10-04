import json, solve_scip
from ortools.linear_solver import pywraplp
orig = pywraplp.Solver.Solve
def exact_solve(self, *a):
    p = pywraplp.MPSolverParameters()
    p.SetDoubleParam(pywraplp.MPSolverParameters.RELATIVE_MIP_GAP, 0.0)
    return orig(self, p)
pywraplp.Solver.Solve = exact_solve
d = json.load(open("scen48.json"))
for name in ["S3", "S1", "S2", "S4"]:
    e = d[name]
    r = solve_scip.solve(e["inst"], e["scenario"]["mf"])
    print(name, r, "exact" if r["bound"] == r["obj"] else "NOT exact", "agree", r["obj"] == e["result"]["obj"], flush=True)
