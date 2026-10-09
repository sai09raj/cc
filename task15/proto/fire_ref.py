#!/usr/bin/env python3
"""FIRE-15 literal reference, written from design/spec.md.  usage: fire_ref.py s1,...,s7 [scenarios]"""
import json, sys
P = json.load(open(__file__.rsplit('/', 1)[0] + '/params.json' if '/' in __file__ else 'params.json'))
W, H, B = P["W"], P["H"], P["BLOCK"]
COVER = [[P["BLOCKS"][y // B][x // B] for x in range(W)] for y in range(H)]
SPEEDS = ["calm", "moderate", "strong"]
DIRS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
M31 = 2 ** 31
def lcg(x): return (1103515245 * x + 12345) % M31

def run(scen, plan):
    seed = P["SEED"][scen]; xl, xs = seed, 7 * seed + 1
    state = {}            # (x, y) -> 'burning' | 'burnt'
    rem, fire_of = {}, {}
    fires = []            # dicts: cell, ign, crew
    crews = []
    for k, (spd, cap) in enumerate(P["CREWS"]):
        st = tuple(P["STATIONS"][plan[k] - 1])
        crews.append(dict(speed=spd, cap=cap, home=st, pos=st, mode="available", fire=None, when=0))
    t = 0
    while True:
        if t < P["T_LIGHT"]:
            xl = lcg(xl)
            if (xl // 256) % 1000 < P["RATE"][scen]:
                xl = lcg(xl); X = (xl // 256) % W; xl = lcg(xl); Y = (xl // 256) % H
                if COVER[Y][X] not in "WR" and (X, Y) not in state:
                    state[(X, Y)] = "burning"; rem[(X, Y)] = P["BURN"][COVER[Y][X]]
                    fires.append(dict(cell=(X, Y), ign=t, crew=None)); fire_of[(X, Y)] = len(fires) - 1
        wdir, wspd = P["WIND"][scen][t // P["PERIOD"]]
        marked = []
        burning = sorted((c for c, s in state.items() if s == "burning"), key=lambda c: (c[1], c[0]))
        for (x, y) in burning:
            for d, (dx, dy) in enumerate(DIRS):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H) or COVER[ny][nx] in "WR" or (nx, ny) in state:
                    continue
                xs = lcg(xs); r = (xs // 65536) % 1000
                ang = min(abs(d - wdir), 8 - abs(d - wdir))
                p = P["BASE"][COVER[ny][nx]] * P["WF"][SPEEDS[wspd]][ang] // 100
                if d % 2 == 1: p = p * P["DIAG"] // 100
                if r < p:
                    state[(nx, ny)] = "marked"; fire_of[(nx, ny)] = fire_of[(x, y)]; marked.append((nx, ny))
        for c in crews:
            if c["mode"] == "travelling" and c["when"] <= t:
                c["mode"] = "working"; c["pos"] = fires[c["fire"]]["cell"]
            elif c["mode"] == "returning" and c["when"] <= t:
                c["mode"] = "available"; c["pos"] = c["home"]
            if c["mode"] == "working":
                for _ in range(c["cap"]):
                    cand = [q for q, s in state.items() if s == "burning" and fire_of[q] == c["fire"]]
                    if not cand: break
                    px, py = c["pos"]
                    q = min(cand, key=lambda q: (abs(q[0] - px) + abs(q[1] - py), q[1], q[0]))
                    state[q] = "burnt"; del rem[q]; c["pos"] = q
        for q in [q for q, s in state.items() if s == "burning"]:
            rem[q] -= 1
            if rem[q] == 0: state[q] = "burnt"; del rem[q]
        for q in marked:
            state[q] = "burning"; rem[q] = P["BURN"][COVER[q[1]][q[0]]]
        live = {}
        for q, s in state.items():
            if s == "burning": live[fire_of[q]] = live.get(fire_of[q], 0) + 1
        for c in crews:
            if c["mode"] == "working" and live.get(c["fire"], 0) == 0:
                d = abs(c["pos"][0] - c["home"][0]) + abs(c["pos"][1] - c["home"][1])
                c["mode"] = "returning"; c["when"] = t + 1 + -(-d // c["speed"])
        for i, f in enumerate(fires):
            if t >= f["ign"] + P["DET"] and f["crew"] is None and live.get(i, 0) > 0:
                best = None
                for k, c in enumerate(crews):
                    if c["mode"] != "available": continue
                    d = abs(c["home"][0] - f["cell"][0]) + abs(c["home"][1] - f["cell"][1])
                    tt = -(-d // c["speed"])
                    if best is None or tt < best[0]: best = (tt, k)
                if best is None: break
                tt, k = best; f["crew"] = k
                crews[k].update(mode="travelling", fire=i, when=t + 1 + tt)
        t += 1
        if t == P["T_END"] or (t >= P["T_LIGHT"] and not any(s == "burning" for s in state.values())):
            break
    burnt = len(state); houses = sum(1 for (x, y) in state if COVER[y][x] == "H")
    return burnt + P["HOUSE_W"] * houses, burnt, houses, len(fires), t

if __name__ == "__main__":
    plan = [int(v) for v in sys.argv[1].split(",")]
    scs = sys.argv[2] if len(sys.argv) > 2 else "ABCD"
    tot = 0
    for s in scs:
        r = run(s, plan); tot += r[0]
        print("%s: loss %d burned %d houses %d fires %d end %d | " % ((s,) + r), end="")
    print("total %d" % tot)
