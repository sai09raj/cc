"""FIRE-15 model constants (single source of truth). Writes params.json and params.h."""
import json
# 16 x 16 block map, each block 4 x 4 cells; row 0 = north. Codes: W water, R rock, G grass, B brush, T timber, H houses
BLOCKS = [
    "TTTTBBGGGGBBTTTT",
    "TTTBBGGGGGGBBTTT",
    "TTBBGGWWWGGGBBTT",
    "TBBGGWWWWWGGGBBT",
    "BBGGGWWWWGGGHHBB",
    "BGGGGGWWGGGHHHHB",
    "GGGBBGGGGGBBHHGG",
    "GGBBBBRRRRBBBGGG",
    "GBBTTBBBRRRBBBGG",
    "BBTTTTBBBBRRBBBG",
    "BTTTTTTBBGGRRGGG",
    "BTTTHHTTBBGGGGBB",
    "TTTTHHTTTBBGGBBT",
    "TTTTTTTTTTBBBBTT",
    "TTTTTTTTTTTBBTTT",
    "TTTTTTTTTTTTTTTT",
]
P = dict(
    W=128, H=128, BLOCK=8, BLOCKS=BLOCKS,
    BURN={"G": 2, "B": 4, "T": 7, "H": 5},
    BASE={"G": 100, "B": 75, "T": 50, "H": 65},
    WF={"calm": [100, 100, 100, 100, 100], "moderate": [170, 135, 90, 55, 35], "strong": [250, 170, 75, 35, 20]},
    DIAG=70,
    HOUSE_W=9,
    T_LIGHT=480, T_END=960, DET=10, PERIOD=120,
    RATE={"A": 100, "B": 115, "C": 130, "D": 145},
    SEED={"A": 4401, "B": 5503, "C": 6607, "D": 7717},
    # wind per 60-step period: (direction toward, speed class); directions 0=N,1=NE,...,7=NW
    WIND={"A": [[2, 1], [2, 1], [3, 2], [3, 2], [2, 2], [1, 1], [1, 1], [2, 0]],
          "B": [[4, 1], [4, 2], [3, 2], [2, 2], [2, 1], [1, 1], [0, 0], [0, 1]],
          "C": [[6, 2], [6, 2], [5, 2], [4, 1], [4, 1], [3, 1], [2, 0], [2, 0]],
          "D": [[0, 1], [1, 1], [2, 2], [2, 2], [3, 1], [4, 1], [5, 0], [6, 1]]},
    STATIONS=[[12, 20], [44, 12], [84, 12], [116, 28], [24, 60], [68, 52], [108, 60], [12, 100], [52, 92], [88, 84], [116, 108], [60, 120], [36, 36], [100, 92]],
    CREWS=[[3, 1], [4, 1], [2, 2], [3, 2], [2, 3], [4, 2], [3, 3]],  # (speed cells/step, capacity cells/step)
)
json.dump(P, open("params.json", "w"), indent=1)
code = {"W": 0, "R": 0, "G": 1, "B": 2, "T": 3, "H": 4}
B=P["BLOCK"]; fuel = [code[P["BLOCKS"][y // B][x // B]] for y in range(P["H"]) for x in range(P["W"])]
sp = ["calm", "moderate", "strong"]
h = ["/* generated */", "#define GW %d" % P["W"], "#define GH %d" % P["H"],
     "static const unsigned char FUEL[%d]" % (P["W"]*P["H"]) + " = {%s};" % ",".join(map(str, fuel)),
     "static const int BURN[5] = {0,%d,%d,%d,%d};" % tuple(P["BURN"][k] for k in "GBTH"),
     "static const int BASE[5] = {0,%d,%d,%d,%d};" % tuple(P["BASE"][k] for k in "GBTH"),
     "static const int WF[3][5] = {%s};" % ",".join("{%s}" % ",".join(map(str, P["WF"][s])) for s in sp),
     "#define DIAG %d\n#define HOUSE_W %d\n#define T_LIGHT %d\n#define T_END %d\n#define DET %d\n#define PERIOD %d" % (P["DIAG"], P["HOUSE_W"], P["T_LIGHT"], P["T_END"], P["DET"], P["PERIOD"]),
     "#define NSC 4\nstatic const int RATE[NSC] = {%d,%d,%d,%d};" % tuple(P["RATE"][s] for s in "ABCD"),
     "static const unsigned SEED[NSC] = {%d,%d,%d,%d};" % tuple(P["SEED"][s] for s in "ABCD"),
     "static const int WIND[NSC][8][2] = {%s};" % ",".join("{%s}" % ",".join("{%d,%d}" % tuple(w) for w in P["WIND"][s]) for s in "ABCD"),
     "#define NST %d\nstatic const int ST[NST][2] = {%s};" % (len(P["STATIONS"]), ",".join("{%d,%d}" % tuple(s) for s in P["STATIONS"])),
     "#define NCREW %d\nstatic const int CREW[NCREW][2] = {%s};" % (len(P["CREWS"]), ",".join("{%d,%d}" % tuple(c) for c in P["CREWS"]))]
open("params.h", "w").write("\n".join(h) + "\n")
