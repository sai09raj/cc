#!/usr/bin/env python3
"""QUORUM-7's 5 named scenario scripts (design/semantic-contract.md S11).
Fault-window tick numbers are derived from the CLEAN scenario's own
executed trace, never hand-guessed.
"""
import quorum_sim as SIM

TOTAL_TICKS = 2400
COMMANDS = [(300, "c1"), (600, "c2"), (900, "c3"), (1500, "c4"), (2000, "c5")]


def clean_script():
    return SIM.Script(total_ticks=TOTAL_TICKS, commands=list(COMMANDS))


def first_stable_leader_tick(base_timeout_name="MEDIUM"):
    """Run CLEAN once to find the tick the first leader is elected."""
    r = SIM.run_scenario(base_timeout_name, clean_script())
    for row in r["trace"]:
        for nid, info in row["nodes"].items():
            if info["role"] == "LEADER":
                return row["t"], nid
    raise RuntimeError("no leader elected in CLEAN scenario")


def partition_script(anchor_tick):
    start = anchor_tick + 200
    end = start + 400
    sc = SIM.Script(total_ticks=TOTAL_TICKS, commands=list(COMMANDS))
    sc.add_partition(start, end, {0, 1, 2}, {3, 4})
    return sc, start, end


def crash_recover_script(anchor_tick, leader_id):
    start = anchor_tick + 200
    end = start + 300
    sc = SIM.Script(total_ticks=TOTAL_TICKS, commands=list(COMMANDS))
    sc.add_crash(leader_id, start, end)
    return sc, start, end


def message_loss_script(anchor_tick):
    start = anchor_tick + 200
    end = start + 400
    sc = SIM.Script(total_ticks=TOTAL_TICKS, commands=list(COMMANDS))
    sc.add_override(start, end, "DROP", src=0, dst=3, cls="APPEND_REQ")
    sc.add_override(start, end, ("DUPLICATE", 3), src=1, dst=2, cls="VOTE_REQ")
    sc.add_override(start, end, ("DELAY", 15), src=0, dst=4, cls="APPEND_REQ")
    return sc, start, end


def competing_candidates_script(anchor_tick):
    start = anchor_tick + 200
    end = start + 500
    sc = SIM.Script(total_ticks=TOTAL_TICKS, commands=list(COMMANDS))
    sc.add_partition(start, end, {2, 3}, {0, 1, 4})
    return sc, start, end


def all_scenarios():
    anchor, leader = first_stable_leader_tick("MEDIUM")
    part_sc, part_start, part_end = partition_script(anchor)
    crash_sc, crash_start, crash_end = crash_recover_script(anchor, leader)
    loss_sc, loss_start, loss_end = message_loss_script(anchor)
    comp_sc, comp_start, comp_end = competing_candidates_script(anchor)
    return {
        "CLEAN": (clean_script(), {}),
        "PARTITION": (part_sc, {"anchor": anchor, "start": part_start, "end": part_end}),
        "CRASH_RECOVER": (crash_sc, {"anchor": anchor, "leader": leader,
                                       "start": crash_start, "end": crash_end}),
        "MESSAGE_LOSS": (loss_sc, {"anchor": anchor, "start": loss_start, "end": loss_end}),
        "COMPETING_CANDIDATES": (comp_sc, {"anchor": anchor, "start": comp_start, "end": comp_end}),
    }


if __name__ == "__main__":
    scenarios = all_scenarios()
    for name, (sc, meta) in scenarios.items():
        print(name, meta)
