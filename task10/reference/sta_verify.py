"""STATIC10 independent verifier — S05/S06.

Deliberately NOT the primary's algorithm: the primary (sta_engine.py)
computes arrival times via forward topological fixed-point propagation
per launch flip-flop. This verifier instead enumerates every distinct
simple DFS path between a launch/capture pair explicitly and takes the
max/min delay over those paths directly -- a different traversal
strategy over the same stated circuit, never importing the primary's
arrival tables.
"""
import circuit as CKT


def _gate_graph():
    """node -> list of (child_node, delay) edges, built directly from CKT.GATES.

    Each gate's delay is charged once, on the edge INTO that gate from each
    of its inputs. The edge from a gate's output to whatever it drives is
    zero-weight only when that target is a terminal flip-flop input
    ('X.D') -- when it drives another gate, that connection is already
    captured by the downstream gate's own input-edge rule, so adding a
    second zero-weight edge here would create a spurious parallel path.
    """
    adj = {}
    for gname, (inputs, delay, drives) in CKT.GATES.items():
        for src in inputs:
            adj.setdefault(src, []).append((gname, delay))
        if drives.endswith(".D"):
            adj.setdefault(gname, []).append((drives, 0))
    return adj


def enumerate_simple_path_delays(launch, capture):
    """DFS enumeration of every simple path from launch.Q to capture.D.
    Returns list of total delays (one per distinct path), or [] if unreachable."""
    adj = _gate_graph()
    start = f"{launch}.Q"
    target = f"{capture}.D"
    results = []

    def dfs(node, visited, acc):
        if node == target and acc > 0 or (node == target and node != start):
            results.append(acc)
            return
        for nxt, edge_delay in adj.get(node, []):
            if nxt in visited:
                continue
            dfs(nxt, visited | {nxt}, acc + edge_delay)

    dfs(start, {start}, 0)
    return results


def independent_arc_delays(launch, capture):
    delays = enumerate_simple_path_delays(launch, capture)
    if not delays:
        return None
    return max(delays), min(delays)


def independent_regime(launch, capture):
    c = CKT.CONSTRAINTS.get((launch, capture))
    if c is None:
        return {"regime": "DEFAULT"}
    return c


def check_submission(claimed):
    """claimed: dict (launch, capture) -> dict with keys:
       'regime' ('DEFAULT'/'MULTICYCLE'/'FALSE'/'CDC'), plus 'N' for MULTICYCLE,
       'setup'/'hold' for DEFAULT/MULTICYCLE, 'depth'/'status' for CDC.
       claimed_critical: (launch, capture, setup) ; claimed_worst_hold: (launch, capture, hold)
    Returns (accept: bool, reason: str)."""
    for (launch, capture), row in claimed.items():
        true_reg = independent_regime(launch, capture)
        true_regime_name = true_reg["regime"]

        if row["regime"] != true_regime_name:
            return False, f"{launch}>{capture}: claimed regime {row['regime']} != true regime {true_regime_name}"

        if true_regime_name == "FALSE":
            if "setup" in row or "hold" in row:
                return False, f"{launch}>{capture}: FALSE path must not report numeric setup/hold"
            continue

        if true_regime_name == "CDC":
            threshold = CKT.CDC_SYNC_THRESHOLD
            expected_status = "SYNCHRONIZED" if row["depth"] >= threshold else "CDC_VIOLATION"
            if row["depth"] != true_reg["synchronizer_depth"]:
                return False, f"{launch}>{capture}: claimed depth {row['depth']} != true depth {true_reg['synchronizer_depth']}"
            if row["status"] != expected_status:
                return False, f"{launch}>{capture}: claimed status {row['status']} != expected {expected_status}"
            continue

        # DEFAULT or MULTICYCLE: independently recompute via DFS path enumeration
        delays = independent_arc_delays(launch, capture)
        if delays is None:
            return False, f"{launch}>{capture}: not actually connected"
        max_comb, min_comb = delays

        clk_l, tcq, _, _ = CKT.FLIP_FLOPS[launch]
        clk_c, _, tsu, th = CKT.FLIP_FLOPS[capture]
        T = CKT.CLOCKS[clk_l]["period"]
        unc = CKT.CLOCKS[clk_l]["uncertainty"]

        if true_regime_name == "MULTICYCLE":
            if row.get("N") != true_reg["N"]:
                return False, f"{launch}>{capture}: claimed N {row.get('N')} != true N {true_reg['N']}"
            N = true_reg["N"]
        else:
            N = 1

        expected_setup = N * T - tsu - unc - tcq - max_comb
        expected_hold = tcq + min_comb - th  # never shifted, per S02

        if row["setup"] != expected_setup:
            return False, f"{launch}>{capture}: claimed setup {row['setup']} != independently recomputed {expected_setup}"
        if row["hold"] != expected_hold:
            return False, f"{launch}>{capture}: claimed hold {row['hold']} != independently recomputed {expected_hold}"

    return True, "all arcs consistent"


def check_aggregate(claimed, claimed_critical, claimed_worst_hold):
    """claimed_critical/claimed_worst_hold: (launch, capture, value)."""
    candidates = [(l, c, row["setup"], row["hold"])
                  for (l, c), row in claimed.items()
                  if row["regime"] in ("DEFAULT", "MULTICYCLE")]
    if not candidates:
        return False, "no DEFAULT/MULTICYCLE arcs to select from"

    def sort_key(row):
        return (row[0], row[1])

    min_setup = min(r[2] for r in candidates)
    tied = sorted([r for r in candidates if r[2] == min_setup], key=sort_key)
    true_crit = tied[0]
    if (claimed_critical[0], claimed_critical[1], claimed_critical[2]) != (true_crit[0], true_crit[1], true_crit[2]):
        return False, f"claimed CRITICAL_PATH {claimed_critical} != true {true_crit[0]}>{true_crit[1]}:{true_crit[2]}"

    min_hold = min(r[3] for r in candidates)
    tied_h = sorted([r for r in candidates if r[3] == min_hold], key=sort_key)
    true_wh = tied_h[0]
    if (claimed_worst_hold[0], claimed_worst_hold[1], claimed_worst_hold[2]) != (true_wh[0], true_wh[1], true_wh[3]):
        return False, f"claimed WORST_HOLD {claimed_worst_hold} != true {true_wh[0]}>{true_wh[1]}:{true_wh[3]}"

    return True, "aggregate selections consistent"


# ---------------------------------------------------------------------------
# S06 required adversarial mutations (crafted standalone, not derived from
# corrupting the main circuit's own run).
# ---------------------------------------------------------------------------

def true_claimed_table():
    """Build the TRUE claimed table from the primary engine's own canonical
    output, used as the 'accept the true program' half of each adversarial
    test."""
    import sta_engine as E
    for k in E.MUTANT:
        E.MUTANT[k] = False
    text, rows, crit, worst_hold = E.compute_certificate()
    claimed = {}
    for (launch, capture, regtag, s, h) in rows:
        reg = E.classify(launch, capture)
        if reg["regime"] == "FALSE":
            claimed[(launch, capture)] = {"regime": "FALSE"}
        elif reg["regime"] == "CDC":
            threshold = CKT.CDC_SYNC_THRESHOLD
            depth = reg["synchronizer_depth"]
            status = "SYNCHRONIZED" if depth >= threshold else "CDC_VIOLATION"
            claimed[(launch, capture)] = {"regime": "CDC", "depth": depth, "status": status}
        elif reg["regime"] == "MULTICYCLE":
            claimed[(launch, capture)] = {"regime": "MULTICYCLE", "N": reg["N"], "setup": s, "hold": h}
        else:
            claimed[(launch, capture)] = {"regime": "DEFAULT", "setup": s, "hold": h}
    claimed_critical = (crit[0], crit[1], crit[2])
    claimed_worst_hold = (worst_hold[0], worst_hold[1], worst_hold[3])
    return claimed, claimed_critical, claimed_worst_hold


def adversarial_mutation_A():
    """A claimed table where the FALSE arc (C1>F0) instead reports numeric
    setup/hold values as if DEFAULT. Verifier must reject."""
    claimed, crit, wh = true_claimed_table()
    claimed[("C1", "F0")] = {"regime": "DEFAULT", "setup": 3060, "hold": 1660}
    ok, reason = check_submission(claimed)
    return (not ok), reason  # mutation correctly rejected iff ok is False


def adversarial_mutation_B():
    """A claimed table that is otherwise fully correct, but names the wrong
    arc as CRITICAL_PATH (A1>B1 instead of the true A0>B1, despite an
    identical setup slack -- i.e. breaks the tie-break rule, not the slack
    math). Verifier must reject."""
    claimed, crit, wh = true_claimed_table()
    bad_critical = ("A1", "B1", 4040)
    ok, reason = check_aggregate(claimed, bad_critical, wh)
    return (not ok), reason


def accepts_true_program():
    claimed, crit, wh = true_claimed_table()
    ok1, r1 = check_submission(claimed)
    ok2, r2 = check_aggregate(claimed, crit, wh)
    return ok1 and ok2, f"{r1} / {r2}"


if __name__ == "__main__":
    ok, reason = accepts_true_program()
    print("accepts true program:", ok, "-", reason)
    rejA, reasonA = adversarial_mutation_A()
    print("rejects mutation A (false-path numeric leak):", rejA, "-", reasonA)
    rejB, reasonB = adversarial_mutation_B()
    print("rejects mutation B (wrong critical-path tie-break):", rejB, "-", reasonB)
