"""STATIC10 primary engine — S01-S04, with mutant hooks for the S08
score-topology audit (see MUTANT dict)."""
import hashlib

import circuit as CKT

NEG_INF = float("-inf")
POS_INF = float("inf")

MUTANT = {
    "no_multicycle_relax": False,   # mutant 1: treat every MULTICYCLE arc as N=1
    "shift_multicycle_hold": False,  # mutant 2: shift hold by (N-1)*T for multicycle arcs
    "no_false_exclusion": False,    # mutant 3: report FALSE arcs' real numeric values
    "cdc_threshold_2": False,       # mutant 4: use synchronizer threshold 2, not 3
    "tie_break_last": False,        # mutant 5: last in sort order wins ties, not first
}


def _driver_of(node):
    """Return the single source feeding FF.D node `node` (an 'FF.D' string), or None."""
    for gname, (inputs, delay, drives) in CKT.GATES.items():
        if drives == node:
            return gname
    for ffname in CKT.FLIP_FLOPS:
        if node == f"{ffname}.D":
            continue
    return None


def _propagate(launch_ff, mode):
    """mode: 'max' or 'min'. Returns {node_name: arrival} reached from launch_ff.Q,
    for every gate output and every FF.D input, topologically."""
    combine = max if mode == "max" else min
    arrival = {f"{launch_ff}.Q": 0}

    # topological order: gates only depend on earlier gates/FF outputs, and
    # GATES dict is defined in dependency order already (verified by construction).
    order = list(CKT.GATES.keys())
    changed = True
    # fixed-point loop (handles dict insertion order safely regardless)
    for _ in range(len(order) + 1):
        changed = False
        for gname in order:
            inputs, delay, drives = CKT.GATES[gname]
            reached_inputs = [arrival[i] for i in inputs if i in arrival]
            if not reached_inputs:
                continue
            new_val = combine(reached_inputs) + delay
            if gname not in arrival or arrival[gname] != new_val:
                arrival[gname] = new_val
                changed = True
            dst = drives
            dst_val = arrival[gname]
            if dst not in arrival or arrival[dst] != dst_val:
                arrival[dst] = dst_val
                changed = True
        if not changed:
            break
    return arrival


def enumerate_arcs():
    """Returns sorted list of (launch, capture) pairs with real connectivity."""
    arcs = set()
    for launch in CKT.FLIP_FLOPS:
        max_arr = _propagate(launch, "max")
        for capture in CKT.FLIP_FLOPS:
            node = f"{capture}.D"
            if node in max_arr and capture != launch:
                arcs.add((launch, capture))
            elif node in max_arr and capture == launch:
                arcs.add((launch, capture))  # self-loop arcs are physically valid
    return sorted(arcs)


def arc_comb_delays(launch, capture):
    max_arr = _propagate(launch, "max")
    min_arr = _propagate(launch, "min")
    node = f"{capture}.D"
    return max_arr[node], min_arr[node]


def classify(launch, capture):
    c = CKT.CONSTRAINTS.get((launch, capture))
    if c is None:
        return {"regime": "DEFAULT"}
    return c


def compute_certificate():
    arcs = enumerate_arcs()
    lines = ["STATIC10-CERT-V1"]
    rows = []  # (launch, capture, regime_str, dict of fields, setup_slack_or_None, hold_slack_or_None)

    for launch, capture in arcs:
        reg = classify(launch, capture)
        regime = reg["regime"]
        clk_l, tcq, _, _ = CKT.FLIP_FLOPS[launch]
        clk_c, _, tsu, th = CKT.FLIP_FLOPS[capture]
        max_comb, min_comb = arc_comb_delays(launch, capture)

        if regime == "FALSE":
            if MUTANT["no_false_exclusion"]:
                T = CKT.CLOCKS[clk_l]["period"]
                unc = CKT.CLOCKS[clk_l]["uncertainty"]
                setup = T - tsu - unc - tcq - max_comb
                hold = tcq + min_comb - th
                line = f"{launch}>{capture}:DEFAULT:setup={setup};hold={hold}"
                rows.append((launch, capture, "DEFAULT", setup, hold))
            else:
                line = f"{launch}>{capture}:FALSE:EXCLUDED"
                rows.append((launch, capture, "FALSE", None, None))
            lines.append(line)
            continue

        if regime == "CDC":
            depth = reg["synchronizer_depth"]
            threshold = 2 if MUTANT["cdc_threshold_2"] else CKT.CDC_SYNC_THRESHOLD
            status = "SYNCHRONIZED" if depth >= threshold else "CDC_VIOLATION"
            line = f"{launch}>{capture}:CDC:depth={depth};status={status}"
            rows.append((launch, capture, "CDC", None, None))
            lines.append(line)
            continue

        assert clk_l == clk_c, "no DEFAULT/MULTICYCLE arc crosses domains in this circuit"
        T = CKT.CLOCKS[clk_l]["period"]
        unc = CKT.CLOCKS[clk_l]["uncertainty"]

        if regime == "MULTICYCLE":
            N = 1 if MUTANT["no_multicycle_relax"] else reg["N"]
            setup = N * T - tsu - unc - tcq - max_comb
            if MUTANT["shift_multicycle_hold"]:
                hold = tcq + min_comb - th - (reg["N"] - 1) * T
            else:
                hold = tcq + min_comb - th
            regime_str = f"MULTICYCLE{reg['N']}" if not MUTANT["no_multicycle_relax"] else "MULTICYCLE1"
            line = f"{launch}>{capture}:{regime_str}:setup={setup};hold={hold}"
            rows.append((launch, capture, "DEFAULT_OR_MC", setup, hold))
            lines.append(line)
            continue

        # DEFAULT
        setup = T - tsu - unc - tcq - max_comb
        hold = tcq + min_comb - th
        line = f"{launch}>{capture}:DEFAULT:setup={setup};hold={hold}"
        rows.append((launch, capture, "DEFAULT_OR_MC", setup, hold))
        lines.append(line)

    candidates = [(l, c, s, h) for (l, c, regtag, s, h) in rows if regtag == "DEFAULT_OR_MC"]

    def sort_key(row):
        return (row[0], row[1])

    if MUTANT["tie_break_last"]:
        crit = min(candidates, key=lambda r: (r[2], tuple(-ord(ch) for ch in sort_key(r)[0] + sort_key(r)[1])))
        # pick last-in-order among ties: reverse sort order for tie-break
        min_setup = min(r[2] for r in candidates)
        tied = sorted([r for r in candidates if r[2] == min_setup], key=sort_key)
        crit = tied[-1]
        min_hold = min(r[3] for r in candidates)
        tied_h = sorted([r for r in candidates if r[3] == min_hold], key=sort_key)
        worst_hold = tied_h[-1]
    else:
        min_setup = min(r[2] for r in candidates)
        tied = sorted([r for r in candidates if r[2] == min_setup], key=sort_key)
        crit = tied[0]
        min_hold = min(r[3] for r in candidates)
        tied_h = sorted([r for r in candidates if r[3] == min_hold], key=sort_key)
        worst_hold = tied_h[0]

    lines.append(f"CRITICAL_PATH={crit[0]}>{crit[1]}:{crit[2]}")
    lines.append(f"WORST_HOLD={worst_hold[0]}>{worst_hold[1]}:{worst_hold[3]}")

    return "\n".join(lines) + "\n", rows, crit, worst_hold


def certificate_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


if __name__ == "__main__":
    text, rows, crit, worst_hold = compute_certificate()
    print(text)
    print("HASH:", certificate_hash(text))
