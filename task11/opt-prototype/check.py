"""Stdlib-only checker: validates a layout (parent map) and recomputes its cost."""
import itertools, json
from instance import length, cross

def check(inst, max_feeders, parent):
    P = [tuple(inst["substation"])] + [tuple(p) for p in inst["turbines"]]
    n = len(P) - 1
    assert set(parent) == set(range(1, n + 1)), "every turbine needs exactly one outgoing cable"
    load = {i: 0 for i in range(1, n + 1)}
    for i in range(1, n + 1):
        j, steps = i, 0
        while j != 0:
            load[j] += 1; j = parent[j]; steps += 1
            assert steps <= n, "cycle"
    cap = max(c for _, c, _ in inst["types"])
    cost = 0
    for i in range(1, n + 1):
        j = parent[i]
        assert j != i
        if j != 0: assert length(P[i], P[j]) <= inst["dmax"], f"span {i}->{j}"
        ok = [c for _, cp, c in inst["types"] if cp >= load[i]]
        assert ok, f"overload on {i}->{j}: {load[i]}"
        cost += length(P[i], P[j]) * min(ok)
    assert sum(1 for i in parent if parent[i] == 0) <= max_feeders, "bays"
    segs = [(i, parent[i]) for i in range(1, n + 1)]
    for (a, b), (c, d) in itertools.combinations(segs, 2):
        assert not cross(P[a], P[b], P[c], P[d]), f"crossing {a}-{b} x {c}-{d}"
    return cost

if __name__ == "__main__":
    data = json.load(open("scen48.json"))
    for name, d in data.items():
        parent = {i: j for i, j, q in d["result"]["arcs"]}
        c = check(d["inst"], d["scenario"]["mf"], parent)
        print(name, "checker cost", c, "solver obj", d["result"]["obj"], "match", c == d["result"]["obj"])
