#!/usr/bin/env python3
"""QUORUM-7 primary protocol engine.

Offline, deterministic, tick-by-tick simulator of the 5-node Raft-family
protocol in quorum7.pdf (pre-vote, bounded-batch AppendEntries K=4,
current-term-only commit).  Reads ONLY ../constants.json for inputs.

Usage:
  python3 engine/quorum7_engine.py --out out            # full 15-row sweep
  python3 engine/quorum7_engine.py --out out_sens --schedule-every 20 ...  (sensitivity)
"""
import argparse
import csv
import gzip
import hashlib
import json
import os
import sys

FOLLOWER, PRECANDIDATE, CANDIDATE, LEADER = "F", "P", "C", "L"
CRASHED_MARK = "X"  # display-only marker for a node inside its crash window

HERE = os.path.dirname(os.path.abspath(__file__))


def load_constants(path=None):
    path = path or os.path.join(HERE, "..", "constants.json")
    with open(path) as f:
        return json.load(f)


class Message:
    __slots__ = ("cls", "src", "dst", "sent", "deliver", "seq", "body")

    def __init__(self, cls, src, dst, sent, deliver, seq, body):
        self.cls, self.src, self.dst = cls, src, dst
        self.sent, self.deliver, self.seq, self.body = sent, deliver, seq, body


class Node:
    def __init__(self, nid, timeout):
        self.id = nid
        self.timeout = timeout
        # persisted
        self.current_term = 0
        self.voted_for = None
        self.log = []  # list of (term, cmd_id); index i (1-based) -> log[i-1]
        self.commit_index = 0
        # volatile
        self.role = FOLLOWER
        self.reset_tick = 0  # election_elapsed == t - reset_tick
        self.prevote_round = None
        self.prevote_grants = set()
        self.votes = set()
        self.next_index = {}
        self.match_index = {}
        self.last_sent = {}

    def last_log_index(self):
        return len(self.log)

    def last_log_term(self):
        return self.log[-1][0] if self.log else 0

    def term_at(self, idx):
        if idx == 0:
            return 0
        if idx > len(self.log):
            return None
        return self.log[idx - 1][0]

    def wipe_volatile(self, t):
        self.role = FOLLOWER
        self.reset_tick = t
        self.prevote_round = None
        self.prevote_grants = set()
        self.votes = set()
        self.next_index, self.match_index, self.last_sent = {}, {}, {}


class Simulation:
    def __init__(self, K, setting, scenario, anchor=None, crash_node=None,
                 schedule=None, leader_steps_down_on_equal_vote_req=False):
        self.K = K
        self.setting = setting
        self.scenario = scenario
        self.N = K["num_nodes"]
        self.T = K["run_ticks"]
        base = K["base_timeout"][setting]
        self.nodes = [Node(i, base + K["timeout_stagger_per_node_id"] * i) for i in range(self.N)]
        self.hb = K["heartbeat_interval"]
        self.batch = K["batch_k"]
        self.delay = K["base_delivery_delay"]
        self.maj = K["majority"]
        self.prio = {c: i for i, c in enumerate(K["class_priority"])}
        self.anchor = anchor
        self.crash_node = crash_node
        self.fig1_equal_term_rule = leader_steps_down_on_equal_vote_req
        sch = schedule or K["client_schedule_ASSUMED"]
        self.commands = {}
        cid = 1
        t = sch["first_tick"]
        while t <= min(sch["last_tick"], self.T - 1) and sch["every"] > 0:
            self.commands[t] = cid
            cid += 1
            t += sch["every"]
        # fault window (absolute ticks, half-open)
        self.window = None
        self.sides = None
        self.ml_rules = []
        if scenario != "CLEAN":
            w = K["fault_windows_rel_anchor"][scenario]
            self.window = (anchor + w["start"], anchor + w["end"])
            if "sides" in w:
                self.sides = {}
                for si, side in enumerate(w["sides"]):
                    for n in side:
                        self.sides[n] = si
            if scenario == "MESSAGE_LOSS":
                self.ml_rules = K["message_loss_overrides_ASSUMED"]
        # network
        self.inflight = {}
        self.seq = 0
        # accounting
        self.sent_total = 0
        self.sent_by_class = {c: 0 for c in K["class_priority"]}
        self.delivered = 0
        self.dropped = 0
        self.duplicated = 0
        # trace / certificate
        self.snapshots = []  # per tick: list of (role, term, voted_for, commit, loglen)
        self.events = []     # certificate events
        self.leader_events = []  # (tick, node, term)
        self.appended = 0

    # ---------------- network ----------------
    def in_window(self, t):
        return self.window is not None and self.window[0] <= t < self.window[1]

    def is_crashed(self, n, t):
        return (self.scenario == "CRASH_RECOVER" and n == self.crash_node and self.in_window(t))

    def partition_cuts(self, sent, deliver):
        rule = getattr(self, "partition_rule", "send_or_deliver")
        if rule == "send":
            return self.in_window(sent)
        if rule == "deliver":
            return self.in_window(deliver)
        return self.in_window(sent) or self.in_window(deliver)

    def partitioned(self, a, b):
        return self.sides is not None and self.sides[a] != self.sides[b]

    def send(self, t, src, dst, cls, body):
        self.sent_total += 1
        self.sent_by_class[cls] += 1
        deliveries = [t + self.delay]
        if self.scenario == "MESSAGE_LOSS" and self.in_window(t):
            for r in self.ml_rules:
                if r["class"] != cls:
                    continue
                if "to" in r and r["to"] != dst:
                    continue
                if "from" in r and r["from"] != src:
                    continue
                if r["action"] == "DROP":
                    deliveries = []
                elif r["action"] == "DUPLICATE":
                    deliveries = deliveries + [d + r["extra_copy_delay"] for d in deliveries]
                    self.duplicated += 1
                elif r["action"] == "DELAY":
                    deliveries = [d + r["extra_delay"] for d in deliveries]
        if not deliveries:
            self.dropped += 1
            return
        for d in deliveries:
            if self.partitioned(src, dst) and self.partition_cuts(t, d):
                self.dropped += 1
                continue
            self.seq += 1
            self.inflight.setdefault(d, []).append(Message(cls, src, dst, t, d, self.seq, body))

    # ---------------- logging helpers ----------------
    def log_set(self, t, node, idx, entry):
        # idx 1-based; idx <= len+1
        if idx == len(node.log) + 1:
            node.log.append(entry)
        else:
            node.log[idx - 1] = entry
        self.events.append(["LOGSET", t, node.id, idx, entry[0], entry[1]])

    def log_trunc(self, t, node, newlen):
        if newlen < len(node.log):
            del node.log[newlen:]
            self.events.append(["LOGTRUNC", t, node.id, newlen])

    def set_term(self, node, term):
        if term > node.current_term:
            node.current_term = term
            node.voted_for = None

    def step_down(self, t, node, term):
        """Adopt a strictly higher term and become FOLLOWER."""
        was_leader = node.role == LEADER
        self.set_term(node, term)
        node.role = FOLLOWER
        node.prevote_round = None
        node.prevote_grants = set()
        node.votes = set()
        if was_leader:
            # a LEADER does not track election_elapsed; it starts from 0 on stepping down
            node.reset_tick = t
            node.next_index, node.match_index, node.last_sent = {}, {}, {}

    # ---------------- protocol actions ----------------
    def up_to_date(self, node, cand_llt, cand_lli):
        return (cand_llt > node.last_log_term() or
                (cand_llt == node.last_log_term() and cand_lli >= node.last_log_index()))

    def start_prevote(self, t, node):
        node.role = PRECANDIDATE
        node.reset_tick = t
        node.prevote_round = t
        node.prevote_grants = {node.id}
        node.votes = set()
        self.events.append(["PREVOTE_ROUND", t, node.id, node.current_term])
        for j in range(self.N):
            if j != node.id:
                self.send(t, node.id, j, "PREVOTE_REQ", {
                    "term": node.current_term + 1, "lli": node.last_log_index(),
                    "llt": node.last_log_term(), "round": t})

    def start_election(self, t, node):
        node.current_term += 1
        node.voted_for = node.id
        node.role = CANDIDATE
        node.reset_tick = t
        node.prevote_round = None
        node.prevote_grants = set()
        node.votes = {node.id}
        self.events.append(["ELECTION", t, node.id, node.current_term])
        for j in range(self.N):
            if j != node.id:
                self.send(t, node.id, j, "VOTE_REQ", {
                    "term": node.current_term, "lli": node.last_log_index(),
                    "llt": node.last_log_term()})

    def become_leader(self, t, node):
        node.role = LEADER
        node.votes = set()
        node.next_index = {j: len(node.log) + 1 for j in range(self.N) if j != node.id}
        node.match_index = {j: 0 for j in range(self.N) if j != node.id}
        node.last_sent = {}
        self.leader_events.append((t, node.id, node.current_term))
        self.events.append(["LEADER", t, node.id, node.current_term])
        for j in range(self.N):
            if j != node.id:
                self.send_append(t, node, j)

    def send_append(self, t, node, j):
        ni = node.next_index[j]
        prev = ni - 1
        entries = node.log[prev:prev + self.batch]
        self.send(t, node.id, j, "APPEND_REQ", {
            "term": node.current_term, "prev": prev, "prev_term": node.term_at(prev),
            "entries": [list(e) for e in entries], "commit": node.commit_index})
        node.last_sent[j] = t

    def advance_commit(self, t, node):
        for n in range(len(node.log), node.commit_index, -1):
            if node.log[n - 1][0] != node.current_term:
                continue
            cnt = 1 + sum(1 for j, m in node.match_index.items() if m >= n)
            if cnt >= self.maj:
                node.commit_index = n
                break

    # ---------------- message handlers ----------------
    def handle(self, t, node, m):
        b = m.body
        if m.cls == "PREVOTE_REQ":
            grant = self.up_to_date(node, b["llt"], b["lli"])
            self.send(t, node.id, m.src, "PREVOTE_RESP", {"round": b["round"], "granted": grant,
                                                          "term": node.current_term})
        elif m.cls == "PREVOTE_RESP":
            if node.role == PRECANDIDATE and b["round"] == node.prevote_round and b["granted"]:
                node.prevote_grants.add(m.src)
                if len(node.prevote_grants) >= self.maj:
                    self.start_election(t, node)
        elif m.cls == "VOTE_REQ":
            before_term, before_vote = node.current_term, node.voted_for
            if b["term"] > node.current_term:
                self.step_down(t, node, b["term"])
            elif (self.fig1_equal_term_rule and node.role == LEADER
                  and b["term"] == node.current_term):
                self.step_down(t, node, b["term"])
            grant = (b["term"] >= node.current_term
                     and node.voted_for in (None, m.src)
                     and self.up_to_date(node, b["llt"], b["lli"]))
            if grant:
                node.voted_for = m.src
                node.reset_tick = t
                self.events.append(["VOTE", t, node.id, m.src, b["term"], before_term,
                                    -1 if before_vote is None else before_vote])
            self.send(t, node.id, m.src, "VOTE_RESP", {"term": node.current_term, "granted": grant})
        elif m.cls == "VOTE_RESP":
            if b["term"] > node.current_term:
                self.step_down(t, node, b["term"])
            elif node.role == CANDIDATE and b["term"] == node.current_term and b["granted"]:
                node.votes.add(m.src)
                if len(node.votes) >= self.maj:
                    self.become_leader(t, node)
        elif m.cls == "APPEND_REQ":
            if b["term"] < node.current_term:
                self.send(t, node.id, m.src, "APPEND_RESP",
                          {"term": node.current_term, "success": False, "match": 0})
                return
            if b["term"] > node.current_term:
                self.step_down(t, node, b["term"])
            if node.role != FOLLOWER:
                # Fig.1 arrows 6/7/8: any role seeing AppendEntries at term >= own -> FOLLOWER
                was_leader = node.role == LEADER
                node.role = FOLLOWER
                node.prevote_round = None
                node.prevote_grants = set()
                node.votes = set()
                if was_leader:
                    node.next_index, node.match_index, node.last_sent = {}, {}, {}
            node.reset_tick = t
            prev = b["prev"]
            if prev > 0 and node.term_at(prev) != b["prev_term"]:
                self.send(t, node.id, m.src, "APPEND_RESP",
                          {"term": node.current_term, "success": False, "match": 0})
                return
            idx = prev
            for e in b["entries"]:
                idx += 1
                existing = node.term_at(idx)
                if existing is not None and existing != e[0]:
                    self.log_trunc(t, node, idx - 1)
                    existing = None
                if existing is None:
                    self.log_set(t, node, idx, (e[0], e[1]))
            last_new = prev + len(b["entries"])
            if b["commit"] > node.commit_index:
                node.commit_index = max(node.commit_index, min(b["commit"], last_new))
            self.send(t, node.id, m.src, "APPEND_RESP",
                      {"term": node.current_term, "success": True, "match": last_new})
        elif m.cls == "APPEND_RESP":
            if b["term"] > node.current_term:
                self.step_down(t, node, b["term"])
                return
            if node.role != LEADER or b["term"] != node.current_term:
                return
            j = m.src
            if b["success"]:
                node.match_index[j] = b["match"]
                node.next_index[j] = b["match"] + 1
                self.advance_commit(t, node)
            else:
                node.next_index[j] = max(1, node.next_index[j] - 1)

    # ---------------- main loop ----------------
    def run(self):
        for t in range(self.T):
            arriving = self.inflight.pop(t, [])
            per_node = {i: [] for i in range(self.N)}
            for m in arriving:
                per_node[m.dst].append(m)
            for node in self.nodes:
                i = node.id
                if self.is_crashed(i, t):
                    self.dropped += len(per_node[i])
                    continue
                if (self.scenario == "CRASH_RECOVER" and i == self.crash_node
                        and self.window and t == self.window[1]):
                    node.wipe_volatile(t)
                    self.events.append(["RECOVER", t, i])
                msgs = sorted(per_node[i], key=lambda m: (self.prio[m.cls], m.src, m.seq))
                for m in msgs:
                    self.delivered += 1
                    self.handle(t, node, m)
                # client command broadcast at fixed tick
                if t in self.commands and node.role == LEADER:
                    self.log_set(t, node, len(node.log) + 1, (node.current_term, self.commands[t]))
                    self.appended += 1
                    for j in range(self.N):
                        if j != i:
                            self.send_append(t, node, j)
                # timers
                if node.role == LEADER:
                    for j in range(self.N):
                        if j != i and t - node.last_sent.get(j, -10**9) >= self.hb:
                            self.send_append(t, node, j)
                elif t - node.reset_tick >= node.timeout:
                    if getattr(self, "ablate_prevote", False):
                        # COUNTERFACTUAL ONLY (never used for the sweep): classic Raft,
                        # term increments directly on timeout
                        self.start_election(t, node)
                    else:
                        self.start_prevote(t, node)
            snap = []
            for node in self.nodes:
                role = CRASHED_MARK if self.is_crashed(node.id, t) else node.role
                snap.append((role, node.current_term,
                             -1 if node.voted_for is None else node.voted_for,
                             node.commit_index, len(node.log)))
            self.snapshots.append(snap)
            if t == self.T - 1:
                self.final_logs = [list(map(list, n.log)) for n in self.nodes]
        return self

    # ---------------- outputs ----------------
    def trace_lines(self):
        lines = [f"QUORUM7|{self.setting}|{self.scenario}"]
        for t, snap in enumerate(self.snapshots):
            lines.append(str(t) + "|" + "|".join(f"{r},{term}" for (r, term, _, _, _) in snap))
        return lines

    def trace_hash(self):
        data = "\n".join(self.trace_lines()).encode("utf-8")
        return hashlib.sha256(data).hexdigest()


# ---------------- engine-side summary / self-check ----------------

def engine_safety_check(sim):
    """Engine's own (non-independent) quick invariant check."""
    es = lm = lc = True
    # election safety: at most one leader per term over whole run
    seen = {}
    for (t, n, term) in sim.leader_events:
        if term in seen and seen[term] != n:
            es = False
        seen[term] = n
    for snap in sim.snapshots:
        terms = [term for (r, term, _, _, _) in snap if r == LEADER]
        if len(terms) != len(set(terms)):
            es = False
    # log matching / completeness on final logs (cheap form)
    logs = sim.final_logs
    for a in range(sim.N):
        for b in range(a + 1, sim.N):
            la, lb = logs[a], logs[b]
            for i in range(min(len(la), len(lb)) - 1, -1, -1):
                if la[i][0] == lb[i][0]:
                    if la[:i + 1] != lb[:i + 1]:
                        lm = False
                    break
    return es, lm, lc


PARTITION_RULE = "send_or_deliver"
ABLATE_PREVOTE = False


def run_one(K, setting, scenario, anchor, crash_node, schedule=None, fig1=False):
    sim = Simulation(K, setting, scenario, anchor=anchor, crash_node=crash_node,
                     schedule=schedule, leader_steps_down_on_equal_vote_req=fig1)
    sim.partition_rule = PARTITION_RULE
    sim.ablate_prevote = ABLATE_PREVOTE
    return sim.run()


def summarize(sim, anchor, crash_node):
    les = sim.leader_events
    row = {
        "setting": sim.setting,
        "scenario": sim.scenario,
        "base_timeout": sim.K["base_timeout"][sim.setting],
        "anchor_tick": anchor,
        "fault_window": "-" if sim.window is None else f"[{sim.window[0]},{sim.window[1]})",
        "first_leader": f"N{les[0][1]}@t{les[0][0]}/term{les[0][2]}" if les else "none",
        "leader_elections": len(les),
        "leaders_seq": ";".join(f"N{n}@t{t}/T{term}" for (t, n, term) in les),
        "final_max_term": max(n.current_term for n in sim.nodes),
        "final_roles": "".join(s[0] for s in sim.snapshots[-1]),
        "prevote_rounds": sum(1 for e in sim.events if e[0] == "PREVOTE_ROUND"),
        "real_elections": sum(1 for e in sim.events if e[0] == "ELECTION"),
        "msgs_sent_total": sim.sent_total,
    }
    for c, v in sim.sent_by_class.items():
        row["sent_" + c] = v
    row["msgs_delivered"] = sim.delivered
    row["msgs_dropped"] = sim.dropped
    row["cmds_appended"] = sim.appended
    row["commit_index_min_final"] = min(s[3] for s in sim.snapshots[-1])
    row["commit_index_max_final"] = max(s[3] for s in sim.snapshots[-1])
    latency = ""
    if sim.scenario == "CRASH_RECOVER":
        crash_start = sim.window[0]
        crashed_term = sim.snapshots[crash_start - 1][crash_node][1]
        for (t, n, term) in les:
            if t >= crash_start and n != crash_node and term > crashed_term:
                latency = t - crash_start
                row["new_leader_after_crash"] = f"N{n}@t{t}/term{term}"
                break
    row["crash_to_new_leader_ticks"] = latency
    if sim.scenario in ("PARTITION", "COMPETING_CANDIDATES"):
        minority = [n for n, s in sim.sides.items() if s == (0 if sim.scenario == "COMPETING_CANDIDATES" else 1)]
        w0 = sim.window[0]
        row["minority"] = ",".join(f"N{n}" for n in sorted(minority))
        row["minority_term_at_window_start"] = ",".join(str(sim.snapshots[w0 - 1][n][1]) for n in sorted(minority))
        row["minority_max_term_in_run"] = ",".join(str(max(s[n][1] for s in sim.snapshots)) for n in sorted(minority))
        row["leader_changes_after_window_start"] = sum(1 for (t, _, _) in les if t >= w0)
    es, lm, lc = engine_safety_check(sim)
    row["engine_selfcheck_election_safety"] = es
    row["engine_selfcheck_log_matching_final"] = lm
    row["trace_sha256_16"] = sim.trace_hash()[:16]
    return row


def write_certificate(sim, path):
    cert = {
        "setting": sim.setting, "scenario": sim.scenario,
        "window": sim.window, "crash_node": sim.crash_node,
        "snapshots": sim.snapshots,  # per tick: [role, term, voted_for(-1=None), commit, loglen] x5
        "events": sim.events,
        "msgs_sent_total": sim.sent_total,
    }
    with gzip.open(path, "wt") as f:
        json.dump(cert, f, separators=(",", ":"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "out"))
    ap.add_argument("--constants", default=None)
    ap.add_argument("--schedule-every", type=int, default=None, help="sensitivity: override command cadence")
    ap.add_argument("--schedule-first", type=int, default=None)
    ap.add_argument("--fig1-equal-term-stepdown", action="store_true",
                    help="sensitivity: LEADER steps down on VOTE_REQ at term == own (Fig.1 arrow 6 literal)")
    ap.add_argument("--no-certs", action="store_true")
    ap.add_argument("--ablate-prevote", action="store_true",
                    help="COUNTERFACTUAL: increment term directly on timeout (no pre-vote); memo evidence only")
    ap.add_argument("--partition-rule", default="send_or_deliver", choices=["send_or_deliver", "send", "deliver"],
                    help="sensitivity: which tick decides whether a cross-partition message is cut")
    args = ap.parse_args()
    K = load_constants(args.constants)
    global PARTITION_RULE, ABLATE_PREVOTE
    PARTITION_RULE = args.partition_rule
    ABLATE_PREVOTE = args.ablate_prevote
    schedule = dict(K["client_schedule_ASSUMED"])
    if args.schedule_every is not None:
        schedule["every"] = args.schedule_every
    if args.schedule_first is not None:
        schedule["first_tick"] = args.schedule_first
    out = args.out
    os.makedirs(out, exist_ok=True)
    certdir = os.path.join(out, "certificates")
    os.makedirs(certdir, exist_ok=True)

    rows = []
    for setting in K["setting_order"]:
        clean = run_one(K, setting, "CLEAN", None, None, schedule, args.fig1_equal_term_stepdown)
        if not clean.leader_events:
            sys.exit(f"{setting}: CLEAN elected no leader; anchor undefined")
        anchor_t, anchor_node, _ = clean.leader_events[0]
        # 'stable': confirm the first leader is never displaced in CLEAN
        stable = len(clean.leader_events) == 1
        for scenario in K["scenario_order"]:
            if scenario == "CLEAN":
                sim = clean
            else:
                sim = run_one(K, setting, scenario, anchor_t, anchor_node, schedule,
                              args.fig1_equal_term_stepdown)
            row = summarize(sim, anchor_t, anchor_node)
            row["clean_first_leader_stable"] = stable
            rows.append(row)
            if not args.no_certs:
                write_certificate(sim, os.path.join(certdir, f"{setting}_{scenario}.json.gz"))
            if (setting == K["certificate"]["baseline_setting"]
                    and scenario == K["certificate"]["baseline_scenario"]):
                lines = sim.trace_lines()
                assert lines[0] == K["certificate"]["header"]
                with open(os.path.join(out, "baseline_trace_MEDIUM_PARTITION.txt"), "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))  # exactly the hashed byte string (no trailing newline)
                full = sim.trace_hash()
                with open(os.path.join(out, "baseline_certificate.json"), "w") as f:
                    json.dump({"config": "election_timeout=MEDIUM, scenario=PARTITION",
                               "algorithm": "SHA-256 over UTF-8 of header + per-tick lines joined by \\n (no trailing newline)",
                               "lines": len(lines), "sha256": full,
                               "certificate_first16": full[:16]}, f, indent=2)

    # sweep table
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(out, "sweep_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    with open(os.path.join(out, "sweep_table.json"), "w") as f:
        json.dump(rows, f, indent=1)

    # selections
    per_setting = {}
    for s in K["setting_order"]:
        rs = [r for r in rows if r["setting"] == s]
        feasible = all(r["engine_selfcheck_election_safety"] and r["engine_selfcheck_log_matching_final"] for r in rs)
        cr = [r for r in rs if r["scenario"] == "CRASH_RECOVER"][0]["crash_to_new_leader_ticks"]
        per_setting[s] = {"feasible_engine_selfcheck": feasible,
                          "crash_to_new_leader_ticks": cr,
                          "total_msgs_5_scenarios": sum(r["msgs_sent_total"] for r in rs)}
    feas = [s for s in K["setting_order"] if per_setting[s]["feasible_engine_selfcheck"]]
    rec = min(feas, key=lambda s: (per_setting[s]["crash_to_new_leader_ticks"], K["setting_order"].index(s)))
    ovh = min(feas, key=lambda s: (per_setting[s]["total_msgs_5_scenarios"], K["setting_order"].index(s)))
    decision = {"per_setting": per_setting, "feasible_settings": feas,
                "recovery_optimal": rec, "overhead_optimal": ovh,
                "selections_agree": rec == ovh,
                "note": "feasibility here is the engine self-check; the independent verifier's verdict is in verifier_report.json"}
    with open(os.path.join(out, "decision_engine.json"), "w") as f:
        json.dump(decision, f, indent=2)
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
