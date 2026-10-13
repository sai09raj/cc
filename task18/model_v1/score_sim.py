"""Strict rubric score under single misreads (everything else right). Numeric rows graded at +/-0.1 % (abs floor)."""
import fem, state, sens

GRADED = {  # quantity: weight
    "ux_L2": 3, "ux_R": 4,
    "V1": 2, "V2": 2, "V3": 2, "V4": 2, "H3": 3, "H4": 3, "BR1": 4,
    "BL1:1-2_MR": 4, "BL1:2-3_ML": 4, "BL1:2-3_MR": 4, "BL1:3-4_ML": 4,
    "BL2:1-2_MR": 4, "BL2:2-3_ML": 4, "BL2:2-3_MR": 4, "BL2:3-4_ML": 4, "BL2:3-4_Msag": 3,
    "BL3:1-2_MR": 4, "BL3:2-3_ML": 4, "BL3:2-3_MR": 4, "BL3:3-4_ML": 4,
    "BR:1-2_MR": 4, "BR:2-3_ML": 4, "BR:2-3_MR": 4, "BR:3-4_ML": 4,
    "BL1:2-3_Msag": 3, "BL2:2-3_Msag": 3, "BR:3-4_Msag": 3,
}
NONNUM = 34          # line-up, memo, reading and file rows (assumed all passed)
POS = sum(GRADED.values()) + NONNUM

def ok(k, a, b):
    tol = max(0.001 * abs(b), 0.02 if k.startswith("ux") else 0.05)
    return abs(a - b) <= tol

def score(c, base):
    q = sens.quantities(fem.solve(c))
    lost = sum(w for k, w in GRADED.items() if not ok(k, q.get(k, 0.0), base[k]))
    return 100 * (POS - lost) / POS

if __name__ == "__main__":
    base = sens.quantities(fem.solve(state.final()))
    print("positive", POS, "numeric", sum(GRADED.values()), f"({100*sum(GRADED.values())/POS:.0f} %)")
    for name, c in sens.mods().items():
        print(f"{name:30s} {score(c, base):5.1f}")
