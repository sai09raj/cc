#!/usr/bin/env python3
"""QUORUM-7 canonical reference protocol engine.

Deterministic, tick-by-tick simulation of a custom Raft-family consensus
protocol (pre-vote extension, bounded-batch AppendEntries with
per-follower next_index/match_index) for a 5-node cluster, driven by a
fully scripted (non-random) network-event model. Implements
design/semantic-contract.md S01-S12 exactly. Offline, stdlib-only.
"""
import copy

NUM_NODES = 5
NODE_NAMES = {0: "N0", 1: "N1", 2: "N2", 3: "N3", 4: "N4"}

BASE_DELAY = 2
HEARTBEAT_INTERVAL = 10
BATCH_K = 4
STAGGER = 20

TIMEOUTS = {"SHORT": 150, "MEDIUM": 250, "LONG": 400}

FOLLOWER, PRECANDIDATE, CANDIDATE, LEADER = "FOLLOWER", "PRECANDIDATE", "CANDIDATE", "LEADER"


def effective_timeout(base_timeout, node_id):
    return base_timeout + STAGGER * node_id


class Node:
    __slots__ = ("nid", "current_term", "voted_for", "log", "commit_index",
                 "role", "election_elapsed", "next_index", "match_index",
                 "crashed", "pre_vote_grants", "vote_grants", "last_sent")

    def __init__(self, nid):
        self.nid = nid
        self.current_term = 0
        self.voted_for = None
        self.log = [(0, None)]  # index 0 sentinel
        self.commit_index = 0
        self.role = FOLLOWER
        self.election_elapsed = 0
        self.next_index = {}
        self.match_index = {}
        self.crashed = False
        self.pre_vote_grants = set()
        self.vote_grants = set()
        self.last_sent = {}

    def last_log_index(self):
        return len(self.log) - 1

    def last_log_term(self):
        return self.log[-1][0]


def log_is_at_least_as_up_to_date(cand_last_term, cand_last_index, node):
    if cand_last_term != node.last_log_term():
        return cand_last_term > node.last_log_term()
    return cand_last_index >= node.last_log_index()


class Script:
    """One scenario's fault script. All windows are [start, end) in ticks."""

    def __init__(self, total_ticks, commands):
        self.total_ticks = total_ticks
        self.commands = list(commands)  # [(tick, cmd_id)]
        self.crash_windows = []         # [(node_id, start, end)]
        self.partition_windows = []     # [(start, end, side_a:set, side_b:set)]
        self.msg_overrides = []         # [(start, end, src or None, dst or None, cls or None, action)]

    def add_crash(self, node_id, start, end):
        self.crash_windows.append((node_id, start, end))

    def add_partition(self, start, end, side_a, side_b):
        self.partition_windows.append((start, end, set(side_a), set(side_b)))

    def add_override(self, start, end, action, src=None, dst=None, cls=None):
        self.msg_overrides.append((start, end, src, dst, cls, action))

    def is_crashed(self, node_id, tick):
        return any(nid == node_id and s <= tick < e for nid, s, e in self.crash_windows)

    def are_partitioned(self, a, b, tick):
        for s, e, sa, sb in self.partition_windows:
            if s <= tick < e:
                if (a in sa and b in sb) or (a in sb and b in sa):
                    return True
        return False

    def override_for(self, tick, src, dst, cls):
        for s, e, osrc, odst, ocls, action in self.msg_overrides:
            if s <= tick < e:
                if osrc is not None and osrc != src:
                    continue
                if odst is not None and odst != dst:
                    continue
                if ocls is not None and ocls != cls:
                    continue
                return action
        return None


class Engine:
    def __init__(self, base_timeout_name, script, mutant_no_prevote=False,
                 mutant_commit_any_term=False, mutant_vote_no_log_check=False,
                 mutant_wrong_quorum=False, mutant_reset_on_any_message=False,
                 mutant_ignore_replication_tracking=False):
        self.base_timeout = TIMEOUTS[base_timeout_name]
        self.script = script
        self.nodes = {i: Node(i) for i in range(NUM_NODES)}
        self.inbox = {}  # delivery_tick -> list of (dst, src, msg)
        self.msg_count = 0
        self.trace = []  # per-tick snapshot
        self.commit_history = []  # (tick, node, index, term, cmd)
        self.mutant_no_prevote = mutant_no_prevote
        self.mutant_commit_any_term = mutant_commit_any_term
        self.mutant_vote_no_log_check = mutant_vote_no_log_check
        self.mutant_reset_on_any_message = mutant_reset_on_any_message
        self.mutant_ignore_replication_tracking = mutant_ignore_replication_tracking
        self.quorum = 2 if mutant_wrong_quorum else 3

    def eff_timeout(self, nid):
        return effective_timeout(self.base_timeout, nid)

    def send(self, tick, src, dst, msg):
        cls = msg[0]
        if self.script.are_partitioned(src, dst, tick):
            return
        action = self.script.override_for(tick, src, dst, cls)
        self.msg_count += 1
        if action == "DROP":
            return
        delay = BASE_DELAY
        dup_offset = None
        if isinstance(action, tuple) and action[0] == "DELAY":
            delay += action[1]
        elif isinstance(action, tuple) and action[0] == "DUPLICATE":
            dup_offset = action[1]
        deliver_at = tick + delay
        self.inbox.setdefault(deliver_at, []).append((dst, src, msg))
        if dup_offset is not None:
            self.inbox.setdefault(deliver_at + dup_offset, []).append((dst, src, msg))

    def broadcast(self, tick, src, msg):
        for j in range(NUM_NODES):
            if j != src:
                self.send(tick, src, j, msg)

    def become_precandidate(self, tick, node):
        node.role = PRECANDIDATE
        node.election_elapsed = 0
        node.pre_vote_grants = {node.nid}
        self.broadcast(tick, node.nid, ("PREVOTE_REQ", node.current_term + 1,
                                         node.last_log_index(), node.last_log_term()))

    def become_candidate(self, tick, node):
        node.current_term += 1
        node.voted_for = node.nid
        node.role = CANDIDATE
        node.election_elapsed = 0
        node.vote_grants = {node.nid}
        self.broadcast(tick, node.nid, ("VOTE_REQ", node.current_term,
                                         node.last_log_index(), node.last_log_term()))

    def become_leader(self, tick, node):
        node.role = LEADER
        node.next_index = {j: node.last_log_index() + 1 for j in range(NUM_NODES) if j != node.nid}
        node.match_index = {j: 0 for j in range(NUM_NODES) if j != node.nid}
        node.last_sent = {}
        for j in range(NUM_NODES):
            if j != node.nid:
                self.send_append_entries(tick, node, j)

    def step_down(self, node, new_term):
        node.current_term = new_term
        node.role = FOLLOWER
        node.voted_for = None

    def send_append_entries(self, tick, leader, j):
        leader.last_sent[j] = tick
        prev_index = 0 if self.mutant_ignore_replication_tracking else leader.next_index[j] - 1
        prev_term = leader.log[prev_index][0] if prev_index >= 0 else 0
        entries = leader.log[prev_index + 1: prev_index + 1 + BATCH_K]
        self.send(tick, leader.nid, j, ("APPEND_REQ", leader.current_term, prev_index,
                                         prev_term, tuple(entries), leader.commit_index))

    def advance_commit_index(self, tick, leader):
        for n in range(leader.last_log_index(), leader.commit_index, -1):
            if not self.mutant_commit_any_term and leader.log[n][0] != leader.current_term:
                continue
            count = 1 + sum(1 for j, m in leader.match_index.items() if m >= n)
            if count >= self.quorum:
                for k in range(leader.commit_index + 1, n + 1):
                    self.commit_history.append((tick, leader.nid, k, leader.log[k][0], leader.log[k][1]))
                leader.commit_index = n
                return

    def deliver(self, tick, dst, src, msg):
        node = self.nodes[dst]
        if node.crashed:
            return
        kind = msg[0]
        if self.mutant_reset_on_any_message and node.role != LEADER:
            node.election_elapsed = 0

        if kind == "PREVOTE_REQ":
            _, term, last_idx, last_term = msg
            granted = log_is_at_least_as_up_to_date(last_term, last_idx, node)
            self.send(tick, dst, src, ("PREVOTE_RESP", term, granted))
        elif kind == "PREVOTE_RESP":
            term, granted = msg[1], msg[2]
            if node.role == PRECANDIDATE and term == node.current_term + 1 and granted:
                node.pre_vote_grants.add(src)
                if len(node.pre_vote_grants) >= self.quorum:
                    self.become_candidate(tick, node)
        elif kind == "VOTE_REQ":
            _, term, last_idx, last_term = msg
            if term > node.current_term:
                self.step_down(node, term)
            granted = False
            if term >= node.current_term and node.voted_for in (None, src):
                if self.mutant_vote_no_log_check or log_is_at_least_as_up_to_date(last_term, last_idx, node):
                    node.voted_for = src
                    node.election_elapsed = 0
                    granted = True
            self.send(tick, dst, src, ("VOTE_RESP", term, granted))
        elif kind == "VOTE_RESP":
            term, granted = msg[1], msg[2]
            if node.role == CANDIDATE and term == node.current_term and granted:
                node.vote_grants.add(src)
                if len(node.vote_grants) >= self.quorum:
                    self.become_leader(tick, node)
        elif kind == "APPEND_REQ":
            _, term, prev_index, prev_term, entries, leader_commit = msg
            if term > node.current_term:
                self.step_down(node, term)
            if term >= node.current_term:
                if node.role in (CANDIDATE, PRECANDIDATE):
                    node.role = FOLLOWER
                node.election_elapsed = 0
            ok = term >= node.current_term and (
                prev_index == 0 or
                (prev_index <= node.last_log_index() and node.log[prev_index][0] == prev_term))
            if ok:
                for k, entry in enumerate(entries):
                    idx = prev_index + 1 + k
                    if idx <= node.last_log_index():
                        if node.log[idx][0] != entry[0]:
                            node.log = node.log[:idx]
                            node.log.append(entry)
                    else:
                        node.log.append(entry)
                last_new_index = prev_index + len(entries)
                if leader_commit > node.commit_index:
                    new_commit = min(leader_commit, last_new_index)
                    for k in range(node.commit_index + 1, new_commit + 1):
                        self.commit_history.append((tick, node.nid, k, node.log[k][0], node.log[k][1]))
                    node.commit_index = new_commit
                self.send(tick, dst, src, ("APPEND_RESP", node.current_term, True,
                                            prev_index + len(entries)))
            else:
                self.send(tick, dst, src, ("APPEND_RESP", node.current_term, False, 0))
        elif kind == "APPEND_RESP":
            term, success, match_idx = msg[1], msg[2], msg[3]
            if node.role == LEADER and term == node.current_term:
                if success:
                    node.match_index[src] = match_idx
                    node.next_index[src] = match_idx + 1
                    self.advance_commit_index(tick, node)
                else:
                    node.next_index[src] = max(1, node.next_index[src] - 1)
                    self.send_append_entries(tick, node, src)

    def run(self):
        for tick in range(self.script.total_ticks):
            for nid, node in self.nodes.items():
                was_crashed = node.crashed
                node.crashed = self.script.is_crashed(nid, tick)
                if node.crashed and not was_crashed:
                    pass  # crashing: state freezes in place, nothing to do
                elif was_crashed and not node.crashed:
                    node.role = FOLLOWER
                    node.election_elapsed = 0

            for dst, src, msg in self.inbox.pop(tick, []):
                self.deliver(tick, dst, src, msg)

            for cmd_tick, cmd_id in self.script.commands:
                if cmd_tick == tick:
                    for node in self.nodes.values():
                        if not node.crashed and node.role == LEADER:
                            node.log.append((node.current_term, cmd_id))
                            for j in range(NUM_NODES):
                                if j != node.nid:
                                    self.send_append_entries(tick, node, j)

            for node in self.nodes.values():
                if node.crashed:
                    continue
                if node.role == LEADER:
                    continue
                node.election_elapsed += 1
                if node.election_elapsed >= self.eff_timeout(node.nid):
                    if self.mutant_no_prevote:
                        self.become_candidate(tick, node)
                    else:
                        self.become_precandidate(tick, node)

            for node in self.nodes.values():
                if node.crashed or node.role != LEADER:
                    continue
                for j in range(NUM_NODES):
                    if j == node.nid:
                        continue
                    if tick - node.last_sent.get(j, -10**9) >= HEARTBEAT_INTERVAL:
                        self.send_append_entries(tick, node, j)

            self.trace.append(self.snapshot(tick))

        return self.result()

    def snapshot(self, tick):
        return {
            "t": tick,
            "nodes": {
                nid: {
                    "term": n.current_term, "role": n.role,
                    "log_len": n.last_log_index(), "commit": n.commit_index,
                    "crashed": n.crashed,
                }
                for nid, n in self.nodes.items()
            },
        }

    def result(self):
        return {
            "trace": self.trace,
            "msg_count": self.msg_count,
            "commit_history": self.commit_history,
            "final": {nid: {"term": n.current_term, "role": n.role,
                             "log": list(n.log), "commit_index": n.commit_index,
                             "voted_for": n.voted_for}
                      for nid, n in self.nodes.items()},
        }


def run_scenario(base_timeout_name, script, **mutant_kwargs):
    return Engine(base_timeout_name, script, **mutant_kwargs).run()


def canonical_trace_serialization(base_timeout_name, scenario_name, result):
    """Deterministic serialization of one scenario run's full trace for
    hashing. One line per tick: t|role0,term0|role1,term1|...|role4,term4."""
    parts = [f"QUORUM7|{base_timeout_name}|{scenario_name}"]
    for row in result["trace"]:
        cells = "|".join(f"{row['nodes'][i]['role'][0]}{row['nodes'][i]['term']}"
                          for i in range(NUM_NODES))
        parts.append(f"{row['t']}|{cells}")
    return "\n".join(parts)


if __name__ == "__main__":
    sc = Script(total_ticks=2400, commands=[(300, "c1"), (600, "c2"), (900, "c3")])
    r = run_scenario("MEDIUM", sc)
    for nid, f in r["final"].items():
        print(nid, f["role"], "term=", f["term"], "log_len=", len(f["log"]) - 1,
              "commit=", f["commit_index"])
    print("total messages:", r["msg_count"])
