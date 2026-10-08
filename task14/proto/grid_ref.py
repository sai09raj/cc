"""GRID-14 reference simulator (Python, written straight from the semantic contract; slow, for verification).

Geometry: intersections (r, c), r = 0..2 north to south, c = 0..2 west to east, index j = 3r + c.
Sides: N=0, E=1, S=2, W=3. An approach is named by the side vehicles arrive FROM.
Movement from side s: through -> leaves by side s+2, right -> side s+3, left -> side s+1 (mod 4).
Terminals (12): T0-T2 north of column 0..2, T3-T5 east of row 0..2, T6-T8 south of column 0..2, T9-T11 west of row 0..2.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "params.json")))
M31 = 2 ** 31


def lcg(x):
    return (1103515245 * x + 12345) % M31


def build_links():
    """Returns links list: dict(kind, length, to_int, to_side, frm_int, frm_side, term)."""
    links = []
    out_link = {}   # (j, side) -> link index leaving j by that side
    in_link = {}    # (j, side) -> link index arriving at j from that side
    for r in range(3):
        for c in range(2):   # east-west blocks
            L = P["L_EW"][r][c]; a, b = 3 * r + c, 3 * r + c + 1
            links.append(dict(kind="int", n=L, frm=a, to=b, to_side=3)); out_link[(a, 1)] = len(links) - 1; in_link[(b, 3)] = len(links) - 1
            links.append(dict(kind="int", n=L, frm=b, to=a, to_side=1)); out_link[(b, 3)] = len(links) - 1; in_link[(a, 1)] = len(links) - 1
    for r in range(2):
        for c in range(3):   # north-south blocks
            L = P["L_NS"][r][c]; a, b = 3 * r + c, 3 * (r + 1) + c
            links.append(dict(kind="int", n=L, frm=a, to=b, to_side=0)); out_link[(a, 2)] = len(links) - 1; in_link[(b, 0)] = len(links) - 1
            links.append(dict(kind="int", n=L, frm=b, to=a, to_side=2)); out_link[(b, 0)] = len(links) - 1; in_link[(a, 2)] = len(links) - 1
    terms = []
    for k in range(12):
        if k < 3:
            j, s = k, 0
        elif k < 6:
            j, s = 3 * (k - 3) + 2, 1
        elif k < 9:
            j, s = 6 + (k - 6), 2
        else:
            j, s = 3 * (k - 9), 3
        links.append(dict(kind="entry", n=P["L_ENTRY"][k], to=j, to_side=s, term=k)); in_link[(j, s)] = len(links) - 1
        links.append(dict(kind="exit", n=P["L_EXIT"], frm=j, term=k)); out_link[(j, s)] = len(links) - 1
        terms.append(len(links) - 2)
    return links, out_link, in_link, terms


LINKS, OUT, IN, ENTRY = build_links()


def greens(C, plan):
    return P["GREEN"][str(C)][plan]   # [gA, gB, gC, gD]


def is_green(C, plan, off, side, mv, t, lag=False):
    g = greens(C, plan); R = P["ALL_RED"]
    tau = (t - off) % C
    order = [1, 0, 3, 2] if lag else [0, 1, 2, 3]
    bounds = [None] * 4
    x = 0
    for ph in order:
        bounds[ph] = (x, x + g[ph]); x += g[ph] + R
    ph = next((p for p, (a, b) in enumerate(bounds) if a <= tau < b), None)
    if ph is None:
        return False
    ns = side in (0, 2)
    if ph == 0:
        return ns and mv in ("T", "R")
    if ph == 1:
        return ns and mv == "L"
    if ph == 2:
        return (not ns) and mv in ("T", "R")
    return (not ns) and mv == "L"


def turn(state, side):
    pct = P["TURN_NS"] if side in (0, 2) else P["TURN_EW"]   # [L, T, R] percent
    state = lcg(state); r = (state >> 16) % 100
    mv = "L" if r < pct[0] else ("T" if r < pct[0] + pct[1] else "R")
    return state, mv


def run(C, plan, offs, lag=False, scen="AM"):
    D = P["DEMANDS"][scen]
    cells = [[None] * l["n"] for l in LINKS]
    tstate = [1000 + 17 * k for k in range(12)]
    queues = [[] for _ in range(12)]
    veh = []    # per vehicle: [gen, exit, lcg state, movement]
    exited = 0
    t = 0
    T_GEN, CAP = P["T_GEN"], P["CAP"]
    while True:
        if t < T_GEN:
            for k in range(12):
                tstate[k] = lcg(tstate[k])
                if (tstate[k] >> 8) % 3600 < D[k]:
                    vid = len(veh)
                    veh.append([t, None, (vid * 2654435761 + 12345) % M31, None])
                    queues[k].append(vid)
        snap = [list(c) for c in cells]
        moves = []
        for li, l in enumerate(LINKS):
            n = l["n"]; cl = snap[li]
            for i in range(n - 1, -1, -1):
                v = cl[i]
                if v is None:
                    continue
                if i == n - 1:
                    if l["kind"] == "exit":
                        moves.append(("exit", li, i, v))
                    else:
                        j, s = l["to"], l["to_side"]; mv = veh[v][3]
                        d = {"T": (s + 2) % 4, "R": (s + 3) % 4, "L": (s + 1) % 4}[mv]
                        dl = OUT[(j, d)]
                        if is_green(C, plan, offs[j], s, mv, t, lag) and snap[dl][0] is None:
                            moves.append(("cross", li, i, v, dl))
                elif cl[i + 1] is None:
                    moves.append(("adv", li, i, v))
        for k in range(12):
            if queues[k] and snap[ENTRY[k]][0] is None:
                moves.append(("enter", k, queues[k][0]))
        for m in moves:
            if m[0] == "exit":
                cells[m[1]][m[2]] = None; veh[m[3]][1] = t; exited += 1
            elif m[0] == "adv":
                cells[m[1]][m[2]] = None; cells[m[1]][m[2] + 1] = m[3]
            elif m[0] == "cross":
                _, li, i, v, dl = m
                cells[li][i] = None; cells[dl][0] = v
                if LINKS[dl]["kind"] == "int":
                    veh[v][2], veh[v][3] = turn(veh[v][2], LINKS[dl]["to_side"])
            else:
                _, k, v = m
                queues[k].pop(0); cells[ENTRY[k]][0] = v
                veh[v][2], veh[v][3] = turn(veh[v][2], LINKS[ENTRY[k]]["to_side"])
        t += 1
        empty = exited == len(veh)
        if (t >= T_GEN and empty) or t >= CAP:
            break
    tts = sum((v[1] - v[0] + 1) if v[1] is not None else (CAP - v[0]) for v in veh)
    return dict(tts=tts, generated=len(veh), exited=exited, end=t)


if __name__ == "__main__":
    import time
    C, plan = int(sys.argv[1]), int(sys.argv[2]); offs = [int(x) for x in sys.argv[3].split(",")]
    lag = len(sys.argv) > 4 and sys.argv[4] == "lag"
    t0 = time.time(); out = {s: run(C, plan, offs, lag, s) for s in ("AM", "PM", "EVENT")}
    out["total_tts"] = sum(out[s]["tts"] for s in ("AM", "PM", "EVENT")); out["sec"] = round(time.time() - t0, 2); print(json.dumps(out))
