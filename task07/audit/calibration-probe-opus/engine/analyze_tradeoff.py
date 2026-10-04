#!/usr/bin/env python3
"""Extracts the facts the memo cites, by re-executing the engine (no hand-derived numbers).

Writes out/tradeoff_analysis.json and out/baseline_role_transitions.txt.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quorum7_engine as E  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(E.HERE, "..", "out")
K = E.load_constants()


def transitions(sim):
    out = []
    prev = None
    for t, snap in enumerate(sim.snapshots):
        cur = [(r, term) for (r, term, _, _, _) in snap]
        if prev is None:
            prev = cur
            continue
        for n in range(sim.N):
            if cur[n] != prev[n]:
                out.append((t, n, f"{prev[n][0]},{prev[n][1]}", f"{cur[n][0]},{cur[n][1]}"))
        prev = cur
    return out




res = {"settings": {}}
for setting in K["setting_order"]:
    clean = E.run_one(K, setting, "CLEAN", None, None)
    anchor, anode, _ = clean.leader_events[0]
    info = {"anchor": anchor, "anchor_leader": f"N{anode}",
            "clean_first_prevote_tick": [e[1] for e in clean.events if e[0] == "PREVOTE_ROUND"][0],
            "scenarios": {}}
    for sc in K["scenario_order"]:
        sim = clean if sc == "CLEAN" else E.run_one(K, setting, sc, anchor, anode)
        rounds = [(e[1], f"N{e[2]}") for e in sim.events if e[0] == "PREVOTE_ROUND"]
        elections = [(e[1], f"N{e[2]}", e[3]) for e in sim.events if e[0] == "ELECTION"]
        pre_leader = sim.leader_events[0][0]
        d = {
            "msgs_sent_total": sim.sent_total,
            "sent_by_class": sim.sent_by_class,
            "election_traffic(PREVOTE+VOTE msgs)": sum(v for c, v in sim.sent_by_class.items() if "VOTE" in c),
            "replication_traffic(APPEND msgs)": sim.sent_by_class["APPEND_REQ"] + sim.sent_by_class["APPEND_RESP"],
            "ticks_with_a_leader": sum(1 for s in sim.snapshots if any(r[0] == "L" for r in s)),
            "prevote_rounds(tick,node)": rounds,
            "real_elections(tick,node,term)": elections,
            "leaders(tick,node,term)": sim.leader_events,
        }
        if sc == "CRASH_RECOVER":
            ws = sim.window[0]
            nl = [x for x in sim.leader_events if x[0] >= ws and x[1] != anode][0]
            pv = [r for r in rounds if r[0] >= ws][0]
            d["crash_window"] = sim.window
            d["first_prevote_after_crash(tick,node)"] = pv
            d["new_leader(tick,node,term)"] = nl
            d["latency_crash_to_new_leader"] = nl[0] - ws
            d["latency_decomposition"] = {
                "crash_start_to_prevote": pv[0] - ws,
                "prevote_to_leader": nl[0] - pv[0],
            }
        info["scenarios"][sc] = d
    res["settings"][setting] = info

# cross-setting deltas, explained by election-chatter vs leaderless-time
for s in K["setting_order"]:
    st = res["settings"][s]["scenarios"]
    res["settings"][s]["sum_election_traffic"] = sum(v["election_traffic(PREVOTE+VOTE msgs)"] for v in st.values())
    res["settings"][s]["sum_replication_traffic"] = sum(v["replication_traffic(APPEND msgs)"] for v in st.values())
    res["settings"][s]["sum_total"] = sum(v["msgs_sent_total"] for v in st.values())
    res["settings"][s]["sum_ticks_with_leader"] = sum(v["ticks_with_a_leader"] for v in st.values())

with open(os.path.join(OUT, "tradeoff_analysis.json"), "w") as f:
    json.dump(res, f, indent=1)

# baseline role/term transitions
base = E.run_one(K, "MEDIUM", "CLEAN", None, None)
a, an, _ = base.leader_events[0]
sim = E.run_one(K, "MEDIUM", "PARTITION", a, an)
with open(os.path.join(OUT, "baseline_role_transitions.txt"), "w") as f:
    f.write(f"# MEDIUM/PARTITION role,term transitions (anchor={a}, partition window [{sim.window[0]},{sim.window[1]}))\n")
    for (t, n, p, c) in transitions(sim):
        f.write(f"t={t} N{n} {p} -> {c}\n")
    f.write("# prevote rounds: " + json.dumps([(e[1], e[2]) for e in sim.events if e[0] == "PREVOTE_ROUND"]) + "\n")
    f.write("# messages: " + json.dumps(sim.sent_by_class) + f" total={sim.sent_total} dropped={sim.dropped}\n")
for s in K["setting_order"]:
    r = res["settings"][s]
    print(s, "anchor", r["anchor"], "total", r["sum_total"], "election", r["sum_election_traffic"],
          "replication", r["sum_replication_traffic"], "leader-ticks", r["sum_ticks_with_leader"],
          "CR", r["scenarios"]["CRASH_RECOVER"]["latency_decomposition"],
          r["scenarios"]["CRASH_RECOVER"]["new_leader(tick,node,term)"])
print(open(os.path.join(OUT, "baseline_role_transitions.txt")).read())
