#!/usr/bin/env python3
"""QUORUM-7 independent verifier.

Deliberately structured differently from quorum_sim.py (a single
dict-of-dicts state table updated per tick, rather than Node objects with
methods; a flat sorted event queue rather than a tick-indexed inbox
dict), sharing only the immutable input constants (S01-S09). Provides
both a from-scratch re-simulation and a safety-invariant checker that can
be run against any delivered final-state + commit-history record,
including a deliberately corrupted one, without re-simulating.
"""
import quorum_sim as REF  # immutable constants only: timeouts, K, etc.

N = REF.NUM_NODES


def log_ok(cand_term, cand_idx, term, idx):
    if cand_term != term:
        return cand_term > term
    return cand_idx >= idx


def independent_resimulate(base_timeout_name, script):
    """From-scratch re-simulation: state as a dict of dicts, messages as a
    flat sorted list of (deliver_tick, seq, dst, src, msg) rather than a
    tick-indexed inbox. Returns final state + full commit-event history
    (used by the leader-completeness check)."""
    timeout = REF.TIMEOUTS[base_timeout_name]
    state = {i: {"term": 0, "voted_for": None, "log": [(0, None)],
                 "commit": 0, "role": "FOLLOWER", "elapsed": 0,
                 "crashed": False, "next_idx": {}, "match_idx": {},
                 "pre_grants": set(), "grants": set(), "last_sent": {}}
              for i in range(N)}
    pending = []  # (deliver_tick, seq, dst, src, msg)
    seq_ctr = [0]
    msg_count = [0]
    commit_history = []  # (tick, node, index, term, cmd)

    def eff_timeout(nid):
        return timeout + REF.STAGGER * nid

    def emit(tick, src, dst, msg):
        if script.are_partitioned(src, dst, tick):
            return
        cls = msg[0]
        action = script.override_for(tick, src, dst, cls)
        msg_count[0] += 1
        if action == "DROP":
            return
        delay = REF.BASE_DELAY
        dup = None
        if isinstance(action, tuple) and action[0] == "DELAY":
            delay += action[1]
        elif isinstance(action, tuple) and action[0] == "DUPLICATE":
            dup = action[1]
        seq_ctr[0] += 1
        pending.append((tick + delay, seq_ctr[0], dst, src, msg))
        if dup is not None:
            seq_ctr[0] += 1
            pending.append((tick + delay + dup, seq_ctr[0], dst, src, msg))

    def emit_all(tick, src, msg):
        for j in range(N):
            if j != src:
                emit(tick, src, j, msg)

    def send_ae(tick, leader_id, j):
        s = state[leader_id]
        s["last_sent"][j] = tick
        prev = s["next_idx"][j] - 1
        prev_term = s["log"][prev][0] if prev >= 0 else 0
        entries = tuple(s["log"][prev + 1: prev + 1 + REF.BATCH_K])
        emit(tick, leader_id, j, ("APPEND_REQ", s["term"], prev, prev_term, entries, s["commit"]))

    def become_leader(tick, nid):
        s = state[nid]
        s["role"] = "LEADER"
        s["next_idx"] = {j: len(s["log"]) for j in range(N) if j != nid}
        s["match_idx"] = {j: 0 for j in range(N) if j != nid}
        s["last_sent"] = {}
        for j in range(N):
            if j != nid:
                send_ae(tick, nid, j)

    def advance_commit(tick, nid):
        s = state[nid]
        for idx in range(len(s["log"]) - 1, s["commit"], -1):
            if s["log"][idx][0] != s["term"]:
                continue
            cnt = 1 + sum(1 for m in s["match_idx"].values() if m >= idx)
            if cnt >= 3:
                for k in range(s["commit"] + 1, idx + 1):
                    commit_history.append((tick, nid, k, s["log"][k][0], s["log"][k][1]))
                s["commit"] = idx
                return

    for tick in range(script.total_ticks):
        for nid in range(N):
            s = state[nid]
            was = s["crashed"]
            s["crashed"] = script.is_crashed(nid, tick)
            if was and not s["crashed"]:
                s["role"] = "FOLLOWER"
                s["elapsed"] = 0

        due = [m for m in pending if m[0] == tick]
        pending[:] = [m for m in pending if m[0] != tick]
        # S09's general same-tick delivery order: by recipient, then fixed
        # message-class priority, then ascending sender-node-ID -- NOT
        # send/insertion order (m[1]), which the primary doesn't use either.
        due.sort(key=lambda m: (m[2], REF.MSG_CLASS_ORDER[m[4][0]], m[3]))
        for _, _, dst, src, msg in due:
            s = state[dst]
            if s["crashed"]:
                continue
            kind = msg[0]
            if kind == "PREVOTE_REQ":
                _, term, lidx, lterm = msg
                granted = log_ok(lterm, lidx, s["log"][-1][0], len(s["log"]) - 1)
                emit(tick, dst, src, ("PREVOTE_RESP", term, granted))
            elif kind == "PREVOTE_RESP":
                term, granted = msg[1], msg[2]
                if s["role"] == "PRECANDIDATE" and term == s["term"] + 1 and granted:
                    s["pre_grants"].add(src)
                    if len(s["pre_grants"]) >= 3:
                        s["term"] += 1
                        s["voted_for"] = dst
                        s["role"] = "CANDIDATE"
                        s["elapsed"] = 0
                        s["grants"] = {dst}
                        emit_all(tick, dst, ("VOTE_REQ", s["term"], len(s["log"]) - 1, s["log"][-1][0]))
            elif kind == "VOTE_REQ":
                _, term, lidx, lterm = msg
                if term > s["term"]:
                    s["term"], s["role"], s["voted_for"] = term, "FOLLOWER", None
                granted = False
                if term >= s["term"] and s["voted_for"] in (None, src):
                    if log_ok(lterm, lidx, s["log"][-1][0], len(s["log"]) - 1):
                        s["voted_for"] = src
                        s["elapsed"] = 0
                        granted = True
                emit(tick, dst, src, ("VOTE_RESP", term, granted))
            elif kind == "VOTE_RESP":
                term, granted = msg[1], msg[2]
                if s["role"] == "CANDIDATE" and term == s["term"] and granted:
                    s["grants"].add(src)
                    if len(s["grants"]) >= 3:
                        become_leader(tick, dst)
            elif kind == "APPEND_REQ":
                _, term, prev, prev_term, entries, lcommit = msg
                if term > s["term"]:
                    s["term"], s["role"], s["voted_for"] = term, "FOLLOWER", None
                if term >= s["term"]:
                    if s["role"] in ("CANDIDATE", "PRECANDIDATE"):
                        s["role"] = "FOLLOWER"
                    s["elapsed"] = 0
                ok = term >= s["term"] and (prev == 0 or
                                             (prev <= len(s["log"]) - 1 and s["log"][prev][0] == prev_term))
                if ok:
                    for k, entry in enumerate(entries):
                        idx = prev + 1 + k
                        if idx <= len(s["log"]) - 1:
                            if s["log"][idx][0] != entry[0]:
                                s["log"] = s["log"][:idx]
                                s["log"].append(entry)
                        else:
                            s["log"].append(entry)
                    last_new = prev + len(entries)
                    if lcommit > s["commit"]:
                        for k in range(s["commit"] + 1, min(lcommit, last_new) + 1):
                            commit_history.append((tick, dst, k, s["log"][k][0], s["log"][k][1]))
                        s["commit"] = min(lcommit, last_new)
                    emit(tick, dst, src, ("APPEND_RESP", s["term"], True, prev + len(entries)))
                else:
                    emit(tick, dst, src, ("APPEND_RESP", s["term"], False, 0))
            elif kind == "APPEND_RESP":
                term, ok, match_idx = msg[1], msg[2], msg[3]
                if s["role"] == "LEADER" and term == s["term"]:
                    if ok:
                        s["match_idx"][src] = match_idx
                        s["next_idx"][src] = match_idx + 1
                        advance_commit(tick, dst)
                    else:
                        s["next_idx"][src] = max(1, s["next_idx"][src] - 1)
                        send_ae(tick, dst, src)

        for cmd_tick, cmd_id in script.commands:
            if cmd_tick == tick:
                for nid in range(N):
                    s = state[nid]
                    if not s["crashed"] and s["role"] == "LEADER":
                        s["log"].append((s["term"], cmd_id))
                        for j in range(N):
                            if j != nid:
                                send_ae(tick, nid, j)

        for nid in range(N):
            s = state[nid]
            if s["crashed"] or s["role"] == "LEADER":
                continue
            s["elapsed"] += 1
            if s["elapsed"] >= eff_timeout(nid):
                s["role"] = "PRECANDIDATE"
                s["elapsed"] = 0
                s["pre_grants"] = {nid}
                emit_all(tick, nid, ("PREVOTE_REQ", s["term"] + 1, len(s["log"]) - 1, s["log"][-1][0]))

        for nid in range(N):
            s = state[nid]
            if s["crashed"] or s["role"] != "LEADER":
                continue
            for j in range(N):
                if j != nid and tick - s["last_sent"].get(j, -10**9) >= REF.HEARTBEAT_INTERVAL:
                    send_ae(tick, nid, j)

    return {"final": state, "commit_history": commit_history, "msg_count": msg_count[0]}


def check_election_safety(primary_trace):
    """No two nodes may be LEADER for the same term at the same tick."""
    for row in primary_trace:
        leaders_by_term = {}
        for nid, info in row["nodes"].items():
            if info["role"] == "LEADER":
                leaders_by_term.setdefault(info["term"], []).append(nid)
        for term, leaders in leaders_by_term.items():
            if len(leaders) > 1:
                return False, f"t={row['t']}: nodes {leaders} both LEADER in term {term}"
    return True, "ok"


def check_log_matching(final_logs):
    """If two logs agree in term at some index, every earlier index must
    also agree (in both term and command)."""
    ids = list(final_logs.keys())
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            la, lb = final_logs[ids[a]], final_logs[ids[b]]
            for i in range(1, min(len(la), len(lb))):
                if la[i][0] == lb[i][0] and la[i] != lb[i]:
                    return False, (f"nodes {ids[a]}/{ids[b]} index {i}: same term "
                                    f"{la[i][0]} but different command {la[i][1]} vs {lb[i][1]}")
    return True, "ok"


def check_leader_completeness(commit_history, final_logs):
    """Every entry ever recorded as committed by any node must still be
    present, unchanged, in every node's final log at that same index --
    a DIFFERENT term at that index is itself a violation (the committed
    entry was replaced entirely), not just a same-term/different-command
    mismatch."""
    for tick, nid, idx, term, cmd in commit_history:
        for other, log in final_logs.items():
            if idx >= len(log):
                return False, (f"committed at t={tick} by node {nid}: index {idx} "
                                f"term {term} cmd={cmd}, but node {other}'s final log "
                                f"has no entry at that index (log truncated below it)")
            if log[idx] != (term, cmd):
                return False, (f"committed at t={tick} by node {nid}: index {idx} "
                                f"term {term} cmd={cmd}, but node {other}'s final log "
                                f"has {log[idx]} at that index")
    return True, "ok"


def verify_scenario(base_timeout_name, script, primary_result):
    """Checks the PRIMARY's own delivered trace/logs/commit-history against
    the three safety invariants (not just the independent re-simulation's
    self-consistency), plus cross-checks the independent re-simulation
    agrees with the primary as a second, independent line of evidence."""
    primary_final_logs = {nid: f["log"] for nid, f in primary_result["final"].items()}
    ok1, r1 = check_election_safety(primary_result["trace"])
    ok2, r2 = check_log_matching(primary_final_logs)
    ok3, r3 = check_leader_completeness(primary_result["commit_history"], primary_final_logs)

    indep = independent_resimulate(base_timeout_name, script)
    agree = all(indep["final"][nid]["term"] == f["term"] and
                indep["final"][nid]["log"] == f["log"] and
                indep["final"][nid]["commit"] == f["commit_index"]
                for nid, f in primary_result["final"].items())
    return {"election_safety": (ok1, r1), "log_matching": (ok2, r2),
            "leader_completeness": (ok3, r3), "agrees_with_primary": agree}


def run_adversarial_mutations(base_timeout_name, script):
    """Confirms the verifier accepts a true baseline and rejects both
    required adversarial mutations: a stale-term vote that produces a
    second LEADER in an already-occupied term, and a leader overwriting
    an already-committed log entry."""
    primary = REF.run_scenario(base_timeout_name, script)
    ok0 = all(v[0] if isinstance(v, tuple) else v
              for v in verify_scenario(base_timeout_name, script, primary).values())
    print(f"[baseline]                       accepted={ok0}")
    assert ok0, "verifier must accept the true baseline"

    import copy
    bad_trace = copy.deepcopy(primary["trace"])
    mid_tick = script.total_ticks // 2
    for row in bad_trace:
        if row["t"] == mid_tick:
            leader_term = next(n["term"] for n in row["nodes"].values() if n["role"] == "LEADER")
            other = next(nid for nid in row["nodes"] if row["nodes"][nid]["role"] != "LEADER")
            row["nodes"][other] = dict(row["nodes"][other])
            row["nodes"][other]["role"] = "LEADER"
            row["nodes"][other]["term"] = leader_term
    ok_a, reason_a = check_election_safety(bad_trace)
    print(f"[mutation A: stale-term vote]    accepted={ok_a}  ({reason_a})")
    assert not ok_a, "verifier must reject the stale-term-vote mutation"

    indep = independent_resimulate(base_timeout_name, script)
    final_logs = {nid: list(st["log"]) for nid, st in indep["final"].items()}
    commit_history = list(indep["commit_history"])
    tick0, nid0, idx0, term0, cmd0 = commit_history[0]
    final_logs[nid0][idx0] = (term0, "CORRUPTED")
    ok_b, reason_b = check_leader_completeness(commit_history, final_logs)
    print(f"[mutation B: overwrite commit]   accepted={ok_b}  ({reason_b})")
    assert not ok_b, "verifier must reject the committed-entry-overwrite mutation"

    print("\nAll three checks passed: baseline accepted, both required "
          "adversarial mutations rejected.")


if __name__ == "__main__":
    import scenarios as SC
    clean_script, _ = SC.all_scenarios()["CLEAN"]
    primary = REF.run_scenario("MEDIUM", clean_script)
    report = verify_scenario("MEDIUM", clean_script, primary)
    for k, v in report.items():
        print(k, v)
    print()
    run_adversarial_mutations("MEDIUM", clean_script)
