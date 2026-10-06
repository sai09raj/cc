#!/usr/bin/env python3
"""COHERE-12 cycle-accurate simulator (standard library only).

Implements the directory MSI protocol, 2x4 mesh network with XY routing,
cores, workload, Nack/backoff and metrics exactly as cohere12_v1.pdf states.

Usage:
  python3 sim.py baseline [--trace FILE]        # P1, Q=2, B=2 (summary + trace)
  python3 sim.py run P Q B [--trace FILE]       # any single configuration
  python3 sim.py sweep FILE.csv                 # all 64 configurations
"""
import sys
import json

# ---------------------------------------------------------------- topology
# Figure 1: node Ni at row i//4, column i%4; core Ci lives on node Ni.
NODE_RC = {n: (n // 4, n % 4) for n in range(8)}
RC_NODE = {v: k for k, v in NODE_RC.items()}
# Figure 1: placement -> (node hosting D0, node hosting D1)
PLACEMENTS = {"P1": (0, 7), "P2": (1, 6), "P3": (3, 4), "P4": (2, 5)}
# Figure 2: link latencies in cycles (same in both directions)
LINK_LAT_UNDIRECTED = {
    (0, 1): 1, (1, 2): 2, (2, 3): 1,
    (4, 5): 2, (5, 6): 1, (6, 7): 3,
    (0, 4): 1, (1, 5): 3, (2, 6): 1, (3, 7): 2,
}
LINK_LAT = {}
for (a, b), lat in LINK_LAT_UNDIRECTED.items():
    LINK_LAT[(a, b)] = lat
    LINK_LAT[(b, a)] = lat

VNET_OF = {"Data": "RESP", "InvAck": "RESP", "Nack": "RESP",
           "FwdGetS": "FWD", "FwdGetM": "FWD", "Inv": "FWD", "PutAck": "FWD",
           "GetS": "REQ", "GetM": "REQ", "PutS": "REQ", "PutM": "REQ"}
VNET_PRIO = {"RESP": 0, "FWD": 1, "REQ": 2}
MSG_TYPES = ["GetS", "GetM", "PutS", "PutM", "FwdGetS", "FwdGetM", "Inv",
             "PutAck", "Data", "InvAck", "Nack"]


def next_hop(cur, dst):
    """XY routing: move along the row (change column) first, then the column."""
    r, c = NODE_RC[cur]
    dr, dc = NODE_RC[dst]
    if c != dc:
        c += 1 if dc > c else -1
    else:
        r += 1 if dr > r else -1
    return RC_NODE[(r, c)]


# ---------------------------------------------------------------- workload
def gen_ops(core):
    x = 101 + 7 * core
    M = 2 ** 31
    ops = []
    for _ in range(40):
        x = (1103515245 * x + 12345) % M
        r = x // 256
        kind = r % 10
        x = (1103515245 * x + 12345) % M
        s = x // 256
        line = s % 3 if ((s // 16) % 10) < 6 else s % 8
        if kind <= 4:
            ops.append(("LD", line))
        elif kind <= 7:
            ops.append(("ST", line))
        else:
            ops.append(("WAIT", 1 + ((s // 8) % 7)))
    return ops


class ProtocolError(Exception):
    pass


class Msg:
    __slots__ = ("serial", "type", "vnet", "src", "dst", "line", "value", "ack",
                 "req", "rtype", "cur", "entered", "nxt", "arrival", "created")

    def __init__(self, serial, mtype, src, dst, line, created, value=None,
                 ack=0, req=None, rtype=None):
        self.serial = serial
        self.type = mtype
        self.vnet = VNET_OF[mtype]
        self.src = src            # entity: ("C", i) or ("D", k)
        self.dst = dst
        self.line = line
        self.value = value
        self.ack = ack
        self.req = req            # original requester core (Fwd*, Inv, Data)
        self.rtype = rtype        # refused request type (Nack)
        self.created = created
        self.cur = None
        self.entered = None
        self.nxt = None
        self.arrival = None


class Sim:
    def __init__(self, placement, Q, B, trace=None):
        self.placement = placement
        self.dnode = PLACEMENTS[placement]
        self.Q = Q
        self.B = B
        self.trace = trace  # list of strings or None
        self.now = 0
        self.serial = 0
        self.msg_count = {t: 0 for t in MSG_TYPES}
        self.waiting = {n: [] for n in range(8)}   # router wait lists
        self.inflight = []                         # messages with an arrival cycle
        # directory banks
        self.dirs = []
        for k in range(2):
            self.dirs.append({
                "REQ": [], "RESP": [], "refused": [],
                "state": {L: "I" for L in range(8) if L % 2 == k},
                "sharers": {L: set() for L in range(8) if L % 2 == k},
                "owner": {L: None for L in range(8) if L % 2 == k},
                "mem": {L: 0 for L in range(8) if L % 2 == k},
            })
        # caches / cores
        self.caches = []
        for i in range(8):
            self.caches.append({
                "RESP": [], "FWD": [],
                "sets": [[None, None], [None, None]],
                "out": {},        # line -> {"type", "k", "retry"} outstanding request
                "ops": gen_ops(i), "pc": 0, "ready": 1, "waitmiss": False,
                "issue": None, "finished": None, "stores": 0,
            })
        self.load_lat = []
        self.loads_done = 0
        self.stores_done = 0

    # ------------------------------------------------------------ helpers
    def node_of(self, ent):
        return ent[1] if ent[0] == "C" else self.dnode[ent[1]]

    def T(self, s):
        if self.trace is not None:
            self.trace.append("%d %s" % (self.now, s))

    def ename(self, ent):
        return ("C%d" if ent[0] == "C" else "D%d") % ent[1]

    def send(self, mtype, src, dst, line, value=None, ack=0, req=None, rtype=None):
        self.serial += 1
        m = Msg(self.serial, mtype, src, dst, line, self.now, value, ack, req, rtype)
        self.msg_count[mtype] += 1
        sn, dn = self.node_of(src), self.node_of(dst)
        if sn == dn:
            m.cur = dn
            m.arrival = self.now + 1
            self.inflight.append(m)
        else:
            m.cur = sn
            m.entered = self.now
            m.nxt = next_hop(sn, dn)
            self.waiting[sn].append(m)
        self.T("MSG %d %s %s->%s L%d v=%s ack=%d req=%s%s" % (
            m.serial, mtype, self.ename(src), self.ename(dst), line, value, ack,
            req, (" rtype=" + rtype) if rtype else ""))
        return m

    def home(self, L):
        return ("D", L % 2)

    # ------------------------------------------------------------ network
    def links_stage(self):
        now = self.now
        for n in range(8):
            wl = self.waiting[n]
            if not wl:
                continue
            best = {}
            for m in wl:
                if m.entered >= now:
                    continue
                key = (VNET_PRIO[m.vnet], m.entered, m.serial)
                b = best.get(m.nxt)
                if b is None or key < b[0]:
                    best[m.nxt] = (key, m)
            for nxt, (key, m) in best.items():
                wl.remove(m)
                m.arrival = now + LINK_LAT[(n, nxt)]
                m.cur = nxt
                self.inflight.append(m)

    def arrivals_stage(self):
        now = self.now
        arr = [m for m in self.inflight if m.arrival == now]
        if not arr:
            return
        self.inflight = [m for m in self.inflight if m.arrival != now]
        arr.sort(key=lambda m: m.serial)
        for m in arr:
            if m.cur == self.node_of(m.dst):
                if m.dst[0] == "D":
                    d = self.dirs[m.dst[1]]
                    if m.vnet == "REQ" and len(d["REQ"]) >= self.Q:
                        d["refused"].append(m)
                        self.T("REFUSE %d %s C%d L%d at D%d" % (
                            m.serial, m.type, m.src[1], m.line, m.dst[1]))
                        continue
                    d[m.vnet].append(m)
                else:
                    self.caches[m.dst[1]][m.vnet].append(m)
            else:
                m.entered = now
                m.nxt = next_hop(m.cur, self.node_of(m.dst))
                self.waiting[m.cur].append(m)

    # ------------------------------------------------------------ directory
    def dir_step(self, k):
        d = self.dirs[k]
        me = ("D", k)
        # (a) RESP: Data from a cache
        if d["RESP"]:
            m = d["RESP"].pop(0)
            L = m.line
            if m.type != "Data" or d["state"][L] != "S_D":
                raise ProtocolError("D%d RESP %s in %s" % (k, m.type, d["state"][L]))
            d["mem"][L] = m.value
            d["state"][L] = "S"
            self.T("DIR D%d L%d S_D->S mem=%s" % (k, L, m.value))
        # (b) REQ
        if d["REQ"]:
            m = d["REQ"][0]
            L = m.line
            st = d["state"][L]
            req = m.src[1]
            reqent = ("C", req)
            t = m.type
            stall = False
            new = st
            if st == "I":
                if t == "GetS":
                    self.send("Data", me, reqent, L, value=d["mem"][L], ack=0, req=req)
                    d["sharers"][L].add(req)
                    new = "S"
                elif t == "GetM":
                    self.send("Data", me, reqent, L, value=d["mem"][L], ack=0, req=req)
                    d["owner"][L] = req
                    new = "M"
                else:
                    self.send("PutAck", me, reqent, L, req=req)
            elif st == "S":
                if t == "GetS":
                    self.send("Data", me, reqent, L, value=d["mem"][L], ack=0, req=req)
                    d["sharers"][L].add(req)
                elif t == "GetM":
                    others = sorted(d["sharers"][L] - {req})
                    self.send("Data", me, reqent, L, value=d["mem"][L], ack=len(others), req=req)
                    for c in others:
                        self.send("Inv", me, ("C", c), L, req=req)
                    d["sharers"][L] = set()
                    d["owner"][L] = req
                    new = "M"
                else:  # PutS / PutM
                    d["sharers"][L].discard(req)
                    self.send("PutAck", me, reqent, L, req=req)
                    if not d["sharers"][L]:
                        new = "I"
            elif st == "M":
                own = d["owner"][L]
                if t == "GetS":
                    if own == req:
                        raise ProtocolError("GetS from owner")
                    self.send("FwdGetS", me, ("C", own), L, req=req)
                    d["sharers"][L].add(req)
                    d["sharers"][L].add(own)
                    d["owner"][L] = None
                    new = "S_D"
                elif t == "GetM":
                    if own == req:
                        raise ProtocolError("GetM from owner")
                    self.send("FwdGetM", me, ("C", own), L, req=req)
                    d["owner"][L] = req
                elif t == "PutS":
                    self.send("PutAck", me, reqent, L, req=req)
                else:  # PutM
                    if req == own:
                        d["mem"][L] = m.value
                        d["owner"][L] = None
                        new = "I"
                    self.send("PutAck", me, reqent, L, req=req)
            elif st == "S_D":
                if t in ("GetS", "GetM"):
                    stall = True
                else:
                    d["sharers"][L].discard(req)
                    self.send("PutAck", me, reqent, L, req=req)
            if not stall:
                d["REQ"].pop(0)
                d["state"][L] = new
                self.T("DIRREQ D%d %s C%d L%d %s->%s" % (k, t, req, L, st, new))
        # (c) Nacks for this cycle's refusals, in refusal order
        for m in d["refused"]:
            self.send("Nack", me, m.src, m.line, req=m.src[1], rtype=m.type)
        d["refused"] = []

    # ------------------------------------------------------------ caches
    def find(self, c, L):
        s = (L // 2) % 2
        for w in range(2):
            e = c["sets"][s][w]
            if e is not None and e["line"] == L:
                return e
        return None

    def set_state(self, i, e, new):
        old = e["state"]
        e["state"] = new
        self.T("ST C%d L%d %s->%s" % (i, e["line"], old, new))

    def free_way(self, i, e):
        c = self.caches[i]
        s = (e["line"] // 2) % 2
        for w in range(2):
            if c["sets"][s][w] is e:
                c["sets"][s][w] = None
        self.T("ST C%d L%d %s->I" % (i, e["line"], e["state"]))

    def complete_load(self, i, e):
        c = self.caches[i]
        e["lru"] = self.now
        lat = self.now - c["issue"]
        self.load_lat.append(lat)
        self.loads_done += 1
        self.T("LD C%d L%d val=%s miss lat=%d" % (i, e["line"], e["data"], lat))
        c["waitmiss"] = False
        c["pc"] += 1
        c["ready"] = self.now + 1

    def do_store_write(self, i, e):
        c = self.caches[i]
        c["stores"] += 1
        e["data"] = 1000 * i + c["stores"]
        e["lru"] = self.now
        self.stores_done += 1
        self.T("STORE C%d L%d val=%d" % (i, e["line"], e["data"]))

    def complete_store(self, i, e):
        c = self.caches[i]
        self.set_state(i, e, "M")
        self.do_store_write(i, e)
        c["waitmiss"] = False
        c["pc"] += 1
        c["ready"] = self.now + 1

    def cache_resp(self, i, m):
        c = self.caches[i]
        L = m.line
        e = self.find(c, L)
        st = e["state"] if e else "I"
        t = m.type
        if t == "Nack":
            o = c["out"].get(L)
            if o is None or o["type"] != m.rtype or o["retry"] is not None:
                raise ProtocolError("unexpected Nack C%d L%d" % (i, L))
            o["k"] += 1
            o["retry"] = self.now + min(self.B * 2 ** (o["k"] - 1), 64)
            self.T("NACK C%d %s L%d k=%d retry=%d" % (i, m.rtype, L, o["k"], o["retry"]))
            return
        if t == "Data":
            fromhome = m.src[0] == "D"
            if st == "IS_D":
                e["data"] = m.value
                c["out"].pop(L, None)
                self.set_state(i, e, "S")
                self.complete_load(i, e)
            elif st in ("IM_AD", "SM_AD"):
                e["data"] = m.value
                c["out"].pop(L, None)
                if fromhome:
                    e["acks"] += m.ack
                    if e["acks"] == 0:
                        self.complete_store(i, e)
                    else:
                        self.set_state(i, e, "IM_A" if st == "IM_AD" else "SM_A")
                else:
                    self.complete_store(i, e)
            else:
                raise ProtocolError("C%d Data in %s L%d" % (i, st, L))
        elif t == "InvAck":
            if st in ("IM_AD", "SM_AD"):
                e["acks"] -= 1
            elif st in ("IM_A", "SM_A"):
                e["acks"] -= 1
                if e["acks"] == 0:
                    self.complete_store(i, e)
            else:
                raise ProtocolError("C%d InvAck in %s" % (i, st))
        else:
            raise ProtocolError("C%d RESP %s" % (i, t))

    def cache_fwd(self, i, m, e):
        """Return True if handled, False if stall."""
        c = self.caches[i]
        me = ("C", i)
        st = e["state"] if e else "I"
        t = m.type
        L = m.line
        if t == "FwdGetS":
            if st in ("M", "MI_A"):
                self.send("Data", me, ("C", m.req), L, value=e["data"], req=m.req)
                self.send("Data", me, self.home(L), L, value=e["data"], req=m.req)
                self.set_state(i, e, "S" if st == "M" else "SI_A")
                return True
            if st in ("IM_AD", "IM_A", "SM_AD", "SM_A"):
                return False
        elif t == "FwdGetM":
            if st in ("M", "MI_A"):
                self.send("Data", me, ("C", m.req), L, value=e["data"], req=m.req)
                if st == "M":
                    self.free_way(i, e)
                else:
                    self.set_state(i, e, "II_A")
                return True
            if st in ("IM_AD", "IM_A", "SM_AD", "SM_A"):
                return False
        elif t == "Inv":
            if st in ("S", "SM_AD", "SI_A"):
                self.send("InvAck", me, ("C", m.req), L, req=m.req)
                if st == "S":
                    self.free_way(i, e)
                elif st == "SM_AD":
                    self.set_state(i, e, "IM_AD")
                else:
                    self.set_state(i, e, "II_A")
                return True
            if st == "IS_D":
                return False
        elif t == "PutAck":
            if st in ("MI_A", "SI_A", "II_A"):
                c["out"].pop(L, None)
                self.free_way(i, e)
                return True
        raise ProtocolError("C%d %s in %s L%d" % (i, t, st, L))

    def cache_step(self, i):
        c = self.caches[i]
        me = ("C", i)
        # (a) RESP
        if c["RESP"]:
            self.cache_resp(i, c["RESP"].pop(0))
        # (b) FWD scan
        blocked = set()
        q = c["FWD"]
        for idx, m in enumerate(q):
            if m.line in blocked:
                continue
            e = self.find(c, m.line)
            if self.cache_fwd(i, m, e):
                q.pop(idx)
                break
            blocked.add(m.line)
        # (c) resend refused request
        cand = [(o["retry"], L) for L, o in c["out"].items()
                if o["retry"] is not None and o["retry"] <= self.now]
        if cand:
            _, L = min(cand)
            o = c["out"][L]
            o["retry"] = None
            val = None
            if o["type"] == "PutM":
                val = self.find(c, L)["data"]
            self.send(o["type"], me, self.home(L), L, value=val, req=i)
        # (d) core
        if c["finished"] is not None or c["waitmiss"] or self.now < c["ready"]:
            return
        if c["pc"] >= len(c["ops"]):
            c["finished"] = self.now
            self.T("FINISH C%d" % i)
            return
        op, arg = c["ops"][c["pc"]]
        if op == "WAIT":
            c["ready"] = self.now + arg
            c["pc"] += 1
            return
        L = arg
        e = self.find(c, L)
        if e is not None:
            st = e["state"]
            if op == "LD":
                if st in ("S", "M", "SM_AD", "SM_A"):
                    e["lru"] = self.now
                    self.loads_done += 1
                    self.T("LD C%d L%d val=%s hit" % (i, L, e["data"]))
                    c["pc"] += 1
                    c["ready"] = self.now + 1
                else:
                    c["ready"] = self.now + 1
            else:
                if st == "M":
                    self.do_store_write(i, e)
                    c["pc"] += 1
                    c["ready"] = self.now + 1
                elif st == "S":
                    e["acks"] = 0
                    self.set_state(i, e, "SM_AD")
                    c["out"][L] = {"type": "GetM", "k": 0, "retry": None}
                    self.send("GetM", me, self.home(L), L, req=i)
                    c["waitmiss"] = True
                    c["issue"] = self.now
                else:
                    c["ready"] = self.now + 1
            return
        s = (L // 2) % 2
        ways = c["sets"][s]
        for w in range(2):
            if ways[w] is None:
                st = "IS_D" if op == "LD" else "IM_AD"
                ne = {"line": L, "state": "I", "data": None, "lru": self.now, "acks": 0}
                ways[w] = ne
                self.set_state(i, ne, st)
                rt = "GetS" if op == "LD" else "GetM"
                c["out"][L] = {"type": rt, "k": 0, "retry": None}
                self.send(rt, me, self.home(L), L, req=i)
                c["waitmiss"] = True
                c["issue"] = self.now
                return
        vic = [(ways[w]["lru"], w) for w in range(2) if ways[w]["state"] in ("S", "M")]
        if vic:
            _, w = min(vic)
            v = ways[w]
            if v["state"] == "S":
                self.set_state(i, v, "SI_A")
                c["out"][v["line"]] = {"type": "PutS", "k": 0, "retry": None}
                self.send("PutS", me, self.home(v["line"]), v["line"], req=i)
            else:
                self.set_state(i, v, "MI_A")
                c["out"][v["line"]] = {"type": "PutM", "k": 0, "retry": None}
                self.send("PutM", me, self.home(v["line"]), v["line"], value=v["data"], req=i)
        c["ready"] = self.now + 1

    # ------------------------------------------------------------ run
    def quiescent(self):
        if any(c["finished"] is None for c in self.caches):
            return False
        if self.inflight or any(self.waiting[n] for n in range(8)):
            return False
        for d in self.dirs:
            if d["REQ"] or d["RESP"] or d["refused"]:
                return False
        for c in self.caches:
            if c["RESP"] or c["FWD"]:
                return False
            if any(o["retry"] is not None for o in c["out"].values()):
                return False
        return True

    def run(self, max_cycles=1000000):
        while True:
            self.now += 1
            if self.now > max_cycles:
                raise ProtocolError("no termination")
            self.links_stage()
            self.arrivals_stage()
            self.dir_step(0)
            self.dir_step(1)
            for i in range(8):
                self.cache_step(i)
            if self.quiescent():
                break
        self.end_cycle = self.now
        return self.results()

    def results(self):
        fin = [c["finished"] for c in self.caches]
        lat = sorted(self.load_lat)
        n = len(lat)
        p95 = lat[min(n - 1, (95 * n) // 100)] if n else 0
        return {
            "placement": self.placement, "Q": self.Q, "B": self.B,
            "makespan": max(fin), "finish": fin, "end_cycle": self.end_cycle,
            "p95": p95, "n_load_misses": n,
            "messages": self.serial, "nacks": self.msg_count["Nack"],
            "by_type": dict(self.msg_count),
            "loads": self.loads_done, "stores": self.stores_done,
        }


def run_config(p, Q, B, trace=None):
    return Sim(p, Q, B, trace).run()


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd in ("baseline", "run"):
        if cmd == "baseline":
            p, Q, B, rest = "P1", 2, 2, argv[2:]
        else:
            p, Q, B, rest = argv[2], int(argv[3]), int(argv[4]), argv[5:]
        tr = None
        tfile = None
        if len(rest) >= 2 and rest[0] == "--trace":
            tfile = rest[1]
            tr = []
        res = run_config(p, Q, B, tr)
        if tfile:
            with open(tfile, "w") as f:
                f.write("# COHERE-12 trace %s Q=%d B=%d\n" % (p, Q, B))
                f.write("# format: <cycle> <event> ...\n")
                for s in tr:
                    f.write(s + "\n")
                f.write("%d END\n" % res["end_cycle"])
        print(json.dumps(res, indent=1))
        return 0
    if cmd == "sweep":
        out = argv[2]
        rows = []
        for p in ("P1", "P2", "P3", "P4"):
            for Q in (1, 2, 3, 4):
                for B in (1, 2, 4, 8):
                    r = run_config(p, Q, B)
                    rows.append(r)
        with open(out, "w") as f:
            f.write("placement,Q,B,makespan,p95_load_miss_latency,messages,nacks\n")
            for r in rows:
                f.write("%s,%d,%d,%d,%d,%d,%d\n" % (r["placement"], r["Q"], r["B"],
                        r["makespan"], r["p95"], r["messages"], r["nacks"]))
        fastest = min(rows, key=lambda r: (r["makespan"], r["p95"], r["messages"],
                                           r["placement"], r["Q"], r["B"]))
        lean_c = [r for r in rows if r["makespan"] <= 640]
        leanest = min(lean_c, key=lambda r: (r["messages"], r["makespan"],
                                             r["placement"], r["Q"], r["B"])) if lean_c else None
        keys = ("placement", "Q", "B", "makespan", "p95", "messages", "nacks")
        print("Fastest:", {k: fastest[k] for k in keys})
        print("Leanest:", {k: leanest[k] for k in keys} if leanest else None,
              "(%d configs with makespan <= 640)" % len(lean_c))
        print("Sum makespan:", sum(r["makespan"] for r in rows))
        print("Sum messages:", sum(r["messages"] for r in rows))
        print("Sum nacks:", sum(r["nacks"] for r in rows))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
