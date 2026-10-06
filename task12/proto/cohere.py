#!/usr/bin/env python3
"""COHERE-12 prototype: directory MSI with transient states on a 2x4 mesh.

Author-side prototype. Every rule here must later appear in the packet.
Cycle stages: (1) links, (2) arrivals, (3) controllers D0, D1, C0..C7.
Vnets: RESP=0, FWD=1, REQ=2 (lower = higher link priority).
"""
import sys

RESP, FWD, REQ = 0, 1, 2
ROWS, COLS = 2, 4
NCORE = 8
NLINE = 8
SETS, WAYS = 2, 2

# undirected link latencies (cycles), keyed by sorted node pair
LINK_LAT = {(0, 1): 1, (1, 2): 2, (2, 3): 1, (4, 5): 2, (5, 6): 1, (6, 7): 3,
            (0, 4): 1, (1, 5): 3, (2, 6): 1, (3, 7): 2}


def node_rc(n):
    return divmod(n, COLS)


def next_hop(cur, dst):
    r, c = node_rc(cur)
    dr, dc = node_rc(dst)
    if dc > c:
        return cur + 1
    if dc < c:
        return cur - 1
    if dr > r:
        return cur + COLS
    return cur - COLS


def lcg(x):
    return (1103515245 * x + 12345) % (1 << 31)


def workload(nops=40, nline=None):
    nl = NLINE if nline is None else nline
    progs = []
    for core in range(NCORE):
        x = 101 + 7 * core
        prog = []
        for _ in range(nops):
            x = lcg(x); r = x >> 8
            kind = r % 10
            x = lcg(x); s = x >> 8
            line = (s % 3) if (s >> 4) % 10 < 6 else (s % nl)
            if kind < 5:
                prog.append(("LD", line))
            elif kind < 8:
                prog.append(("ST", line))
            else:
                prog.append(("WAIT", 1 + (s >> 3) % 7))
        progs.append(prog)
    return progs


class Msg:
    __slots__ = ("serial", "typ", "vnet", "src", "dst", "line", "req", "ack", "val", "dnode")

    def __init__(self, serial, typ, vnet, src, dst, line, req=None, ack=0, val=None):
        self.serial, self.typ, self.vnet, self.src, self.dst = serial, typ, vnet, src, dst
        self.line, self.req, self.ack, self.val = line, req, ack, val


class Sim:
    def __init__(self, placement, qcap, backoff, progs, mut=frozenset(), trace=False, home=None):
        self.home_tab = home
        self.placement = placement          # node of D0, D1
        self.qcap, self.backoff, self.mut = qcap, backoff, mut
        self.progs = progs
        self.t = 0
        self.serial = 0
        self.links = {}                      # (a,b) directed -> waiting list
        for (a, b), lat in LINK_LAT.items():
            self.links[(a, b)] = []
            self.links[(b, a)] = []
        self.inflight = []                   # (arrive_t, serial, node, msg)
        self.inq = {}                        # entity -> [resp, fwd, req]
        for e in [f"D{i}" for i in range(2)] + [f"C{i}" for i in range(NCORE)]:
            self.inq[e] = [[], [], []]
        self.rejected = {"D0": [], "D1": []}
        # directory
        self.dstate = ["I"] * NLINE
        self.sharers = [set() for _ in range(NLINE)]
        self.owner = [None] * NLINE
        self.mem = [0] * NLINE
        # caches: per core, per set, list of ways: dict(line,state,lru,val)
        self.ways = [[[None] * WAYS for _ in range(SETS)] for _ in range(NCORE)]
        self.acks = {}                       # (core,line) -> counter
        self.pending = {}                    # (core,line) -> (kind, attempt, retry_t) for nacked
        self.pc = [0] * NCORE
        self.busy_until = [0] * NCORE
        self.waiting = [None] * NCORE        # (line, kind, issue_t)
        self.done_t = [None] * NCORE
        self.loads = []                      # (core,line,val,t)
        self.stores = []
        self.lat = []
        self.stats = {}
        self.trace = [] if trace else None
        self.race = {}
        self.seq = [0] * NCORE

    # ---------- helpers
    def node_of(self, ent):
        if ent[0] == "C":
            return int(ent[1:])
        return self.placement[int(ent[1:])]

    def home(self, line):
        if self.home_tab is not None:
            return f"D{self.home_tab[line]}"
        return f"D{line % 2}"

    def send(self, typ, vnet, src, dst, line, req=None, ack=0, val=None):
        self.serial += 1
        m = Msg(self.serial, typ, vnet, src, dst, line, req, ack, val)
        self.stats[typ] = self.stats.get(typ, 0) + 1
        sn, dn = self.node_of(src), self.node_of(dst)
        m.dnode = dn
        if sn == dn:
            self.inflight.append((self.t + 1, m.serial, dn, m))
        else:
            nh = next_hop(sn, dn)
            self.links[(sn, nh)].append((self.t, m))
        if self.trace is not None:
            self.trace.append((self.t, "S", typ, src, dst, line))

    def find(self, c, line):
        for w in self.ways[c][(line // 2) % SETS]:
            if w is not None and w["line"] == line:
                return w
        return None

    def note(self, k):
        self.race[k] = self.race.get(k, 0) + 1

    # ---------- stage 1: links
    def stage_links(self):
        for key in sorted(self.links):
            q = self.links[key]
            elig = [(m.vnet if "novnetprio" not in self.mut else 0, t0 if "serial_only" not in self.mut else 0, m.serial, i)
                    for i, (t0, m) in enumerate(q) if t0 < self.t]
            if not elig:
                continue
            _, _, _, i = min(elig)
            t0, m = q.pop(i)
            a, b = key
            lat = LINK_LAT[(min(a, b), max(a, b))]
            self.inflight.append((self.t + lat, m.serial, b, m))
            self.stats["hops"] = self.stats.get("hops", 0) + 1

    # ---------- stage 2: arrivals
    def stage_arrivals(self):
        now = [x for x in self.inflight if x[0] == self.t]
        self.inflight = [x for x in self.inflight if x[0] != self.t]
        for _, _, node, m in sorted(now, key=lambda x: x[1]):
            if node == m.dnode:
                if m.dst[0] == "D" and m.vnet == REQ and len(self.inq[m.dst][REQ]) >= self.qcap:
                    self.rejected[m.dst].append(m)
                    continue
                self.inq[m.dst][m.vnet].append(m)
            else:
                nh = next_hop(node, m.dnode)
                self.links[(node, nh)].append((self.t, m))

    # ---------- directory
    def dir_step(self, d):
        q = self.inq[d]
        if "dir_req_first" in self.mut and q[REQ]:
            m0 = q[REQ][0]
            if self.dir_req(d, m0):
                q[REQ].pop(0)
        if q[RESP]:
            m = q[RESP].pop(0)
            assert m.typ == "Data" and self.dstate[m.line] == "S_D"
            self.mem[m.line] = m.val
            self.dstate[m.line] = "S"
        order = [self.dir_req] if "nacks_first" not in self.mut else []
        if q[REQ] and "dir_req_first" not in self.mut:
            m = q[REQ][0]
            if self.dir_req(d, m):
                q[REQ].pop(0)
        for m in self.rejected[d]:
            self.send("Nack", RESP, d, m.src, m.line, req=m.typ)
        self.rejected[d] = []

    def dir_req(self, d, m):
        L, r = m.line, int(m.src[1:])
        st = self.dstate[L]
        sh = self.sharers[L]
        if m.typ == "GetS":
            if st == "I":
                self.send("Data", RESP, d, m.src, L, ack=0, val=self.mem[L]); sh.add(r); self.dstate[L] = "S"
            elif st == "S":
                self.send("Data", RESP, d, m.src, L, ack=0, val=self.mem[L]); sh.add(r)
            elif st == "M":
                o = self.owner[L]
                self.send("FwdGetS", FWD, d, f"C{o}", L, req=r)
                sh.add(r); sh.add(o); self.owner[L] = None; self.dstate[L] = "S_D"
            else:
                self.note("dir_stall"); return False
        elif m.typ == "GetM":
            if st == "I":
                self.send("Data", RESP, d, m.src, L, ack=0, val=self.mem[L]); self.owner[L] = r; self.dstate[L] = "M"
            elif st == "S":
                others = sorted(sh - {r})
                if "ackcount_all" in self.mut:
                    n = len(sh)
                else:
                    n = len(others)
                self.send("Data", RESP, d, m.src, L, ack=n, val=self.mem[L])
                for s in others:
                    self.send("Inv", FWD, d, f"C{s}", L, req=r)
                sh.clear(); self.owner[L] = r; self.dstate[L] = "M"
                if others:
                    self.note("inv_fanout")
            elif st == "M":
                o = self.owner[L]
                self.send("FwdGetM", FWD, d, f"C{o}", L, req=r); self.owner[L] = r
            else:
                self.note("dir_stall"); return False
        elif m.typ == "PutS":
            if st in ("S", "S_D") and r in sh:
                sh.discard(r)
                if st == "S" and not sh:
                    self.dstate[L] = "I"
            self.send("PutAck", FWD, d, m.src, L)
        elif m.typ == "PutM":
            if st == "M" and self.owner[L] == r:
                self.mem[L] = m.val; self.owner[L] = None; self.dstate[L] = "I"
            else:
                if st in ("S", "S_D"):
                    sh.discard(r)
                    if st == "S" and not sh:
                        self.dstate[L] = "I"
                self.note("putm_nonowner")
            self.send("PutAck", FWD, d, m.src, L)
        return True

    # ---------- cache
    def complete(self, c, w, t):
        line, kind, t0 = self.waiting[c]
        if kind == "LD":
            self.loads.append((c, line, w["val"], t))
        else:
            self.seq[c] += 1
            w["val"] = c * 1000 + self.seq[c]
            self.stores.append((c, line, w["val"], t))
        self.lat.append((kind, t - t0))
        w["lru"] = t
        self.waiting[c] = None
        self.pc[c] += 1
        self.busy_until[c] = t + (0 if "same_cycle" in self.mut else 1)

    def cache_step(self, c):
        C = f"C{c}"
        q = self.inq[C]
        if q[RESP] and "fwd_first" not in self.mut:
            m = q[RESP].pop(0)
            self.cache_resp(c, m)
        blocked = set()
        for i, m in enumerate(q[FWD]):
            if m.line in blocked and "hol_fwd" not in self.mut:
                continue
            if self.cache_fwd(c, m):
                q[FWD].pop(i)
                if i:
                    self.note("fwd_bypass")
                break
            self.note("fwd_stall_" + m.typ)
            if "hol_fwd" in self.mut:
                break
            blocked.add(m.line)
        if q[RESP] and "fwd_first" in self.mut:
            m = q[RESP].pop(0)
            self.cache_resp(c, m)
        # retry one nacked request
        due = sorted((v[2], k[1]) for k, v in self.pending.items() if k[0] == c and v[2] <= self.t)
        if due:
            _, line = due[0]
            kind, att, _ = self.pending.pop((c, line))
            w = self.find(c, line)
            val = w["val"] if (w and kind == "PutM") else None
            self.send(kind, REQ, C, self.home(line), line, val=val)
            self.note("retry")
        self.core_step(c)

    def cache_resp(self, c, m):
        w = self.find(c, m.line)
        k = (c, m.line)
        if m.typ == "Nack":
            kind = m.req
            att = self.pending.get(k, (kind, 0, 0))[1] + 1
            att = self.nack_count.get(k, 0) + 1
            self.nack_count[k] = att
            if "linear_backoff" in self.mut:
                delay = self.backoff * att
            else:
                delay = min(self.backoff * (1 << (att - 1)), 64)
            self.pending[k] = (kind, att, self.t + delay)
            self.note("nack")
            return
        if m.typ == "InvAck":
            self.acks[k] = self.acks.get(k, 0) - 1
            if w["st"] in ("IM_A", "SM_A") and self.acks[k] == 0:
                w["st"] = "M"; self.nack_count.pop(k, None); self.complete(c, w, self.t)
            else:
                self.note("ack_before_data" if w["st"] in ("IM_AD", "SM_AD") else "ack")
            return
        assert m.typ == "Data", m.typ
        st = w["st"]
        w["val"] = m.val
        self.nack_count.pop(k, None)
        if st == "IS_D":
            w["st"] = "S"; self.complete(c, w, self.t)
        elif st in ("IM_AD", "SM_AD"):
            if m.src[0] == "C":
                w["st"] = "M"; self.complete(c, w, self.t)
            else:
                self.acks[k] = self.acks.get(k, 0) + m.ack
                if self.acks[k] == 0:
                    w["st"] = "M"; self.complete(c, w, self.t)
                else:
                    w["st"] = "IM_A" if st == "IM_AD" else "SM_A"
        else:
            raise AssertionError((c, m.line, st, "Data"))

    def cache_fwd(self, c, m):
        C = f"C{c}"
        w = self.find(c, m.line)
        st = w["st"] if w else "I"
        if m.typ == "PutAck":
            assert st in ("MI_A", "SI_A", "II_A"), (c, st)
            self.free(c, w); self.nack_count.pop((c, m.line), None)
            return True
        if m.typ == "Inv":
            if st == "IS_D":
                return False
            if st in ("S", "SM_AD", "SI_A"):
                self.send("InvAck", RESP, C, f"C{m.req}", m.line)
                if st == "S":
                    self.free(c, w)
                elif st == "SM_AD":
                    w["st"] = "IM_AD"; self.note("inv_in_SM_AD")
                else:
                    w["st"] = "II_A"; self.note("inv_in_SI_A")
                return True
            raise AssertionError((c, m.line, st, "Inv"))
        # FwdGetS / FwdGetM
        if st in ("IM_AD", "IM_A", "SM_AD", "SM_A"):
            if "no_fwd_stall" in self.mut:
                return True
            return False
        if st not in ("M", "MI_A"):
            raise AssertionError((c, m.line, st, m.typ))
        if m.typ == "FwdGetS":
            self.send("Data", RESP, C, f"C{m.req}", m.line, val=w["val"])
            self.send("Data", RESP, C, self.home(m.line), m.line, val=w["val"])
            if st == "M":
                w["st"] = "S"
            else:
                w["st"] = "SI_A"; self.note("fwdgets_in_MI_A")
        else:
            self.send("Data", RESP, C, f"C{m.req}", m.line, val=w["val"])
            if st == "M":
                self.free(c, w)
            else:
                w["st"] = "II_A"; self.note("fwdgetm_in_MI_A")
        return True

    def free(self, c, w):
        s = self.ways[c][(w["line"] // 2) % SETS]
        s[s.index(w)] = None

    def core_step(self, c):
        if self.done_t[c] is not None or self.waiting[c] is not None or self.busy_until[c] > self.t:
            return
        prog = self.progs[c]
        if self.pc[c] >= len(prog):
            self.done_t[c] = self.t
            return
        op, arg = prog[self.pc[c]]
        if op == "WAIT":
            self.busy_until[c] = self.t + arg
            self.pc[c] += 1
            return
        line = arg
        w = self.find(c, line)
        C = f"C{c}"
        if w is not None:
            st = w["st"]
            if op == "LD" and st in ("S", "M", "SM_AD", "SM_A"):
                self.loads.append((c, line, w["val"], self.t)); w["lru"] = self.t
                self.pc[c] += 1; self.busy_until[c] = self.t + 1; return
            if op == "ST" and st == "M":
                self.seq[c] += 1; w["val"] = c * 1000 + self.seq[c]
                self.stores.append((c, line, w["val"], self.t)); w["lru"] = self.t
                self.pc[c] += 1; self.busy_until[c] = self.t + 1; return
            if op == "ST" and st == "S":
                w["st"] = "SM_AD"; self.waiting[c] = (line, "ST", self.t)
                self.send("GetM", REQ, C, self.home(line), line); return
            self.note("core_stall_transient"); return
        sset = self.ways[c][(line // 2) % SETS]
        if None not in sset:
            stable = [(x["lru"], i) for i, x in enumerate(sset) if x["st"] in ("S", "M")]
            if stable:
                _, i = min(stable)
                v = sset[i]
                if v["st"] == "S":
                    v["st"] = "SI_A"; self.send("PutS", REQ, C, self.home(v["line"]), v["line"])
                else:
                    v["st"] = "MI_A"; self.send("PutM", REQ, C, self.home(v["line"]), v["line"], val=v["val"])
                self.note("evict")
            else:
                self.note("evict_blocked")
            return
        i = sset.index(None)
        st = "IS_D" if op == "LD" else "IM_AD"
        sset[i] = {"line": line, "st": st, "lru": self.t, "val": None}
        self.waiting[c] = (line, op, self.t)
        self.send("GetS" if op == "LD" else "GetM", REQ, C, self.home(line), line)

    # ---------- run
    def quiescent(self):
        if any(d is None for d in self.done_t):
            return False
        if self.inflight or self.pending or any(self.links.values()):
            return False
        if any(any(qq) for qq in self.inq.values()):
            return False
        return True

    def run(self, limit=200000):
        self.nack_count = {}
        while not self.quiescent():
            self.t += 1
            if self.t > limit:
                raise RuntimeError("deadlock or livelock at %d" % self.t)
            self.stage_links()
            self.stage_arrivals()
            self.dir_step("D0"); self.dir_step("D1")
            for c in range(NCORE):
                self.cache_step(c)
            self.check()
        return self.summary()

    def check(self):
        for L in range(NLINE):
            m = s = 0
            for c in range(NCORE):
                w = self.find(c, L)
                if w and w["st"] == "M":
                    m += 1
                if w and w["st"] in ("S",):
                    s += 1
            assert m <= 1, ("SWMR", self.t, L)

    def summary(self):
        miss = sorted(x for k, x in self.lat if k == "LD")
        p95 = miss[min(len(miss) - 1, int(0.95 * len(miss)))] if miss else 0
        return dict(makespan=max(self.done_t), p95_load_miss=p95,
                    msgs=sum(v for k, v in self.stats.items() if k != "hops"),
                    hops=self.stats.get("hops", 0), nacks=self.stats.get("Nack", 0),
                    race=dict(self.race))


def check_values(sim):
    """Every load returns the value of the latest store to that line completed
    at or before it (stores are serialized by SWMR)."""
    last = {}
    ev = sorted([(t, 1, c, L, v) for c, L, v, t in sim.stores] + [(t, 0, c, L, v) for c, L, v, t in sim.loads])
    bad = 0
    for t, isst, c, L, v in ev:
        if isst:
            last[L] = v
        else:
            if v != last.get(L, 0) and v is not None:
                bad += 1
    return bad


PLACEMENTS = {"P1": (0, 7), "P2": (1, 6), "P3": (3, 4), "P4": (2, 5)}

if __name__ == "__main__":
    progs = workload()
    for pn, pl in PLACEMENTS.items():
        for q in (1, 2, 3, 4):
            for b in (1, 2, 4, 8):
                s = Sim(pl, q, b, progs)
                r = s.run()
                print(pn, q, b, r["makespan"], r["p95_load_miss"], r["msgs"], r["nacks"], "valbad", check_values(s),
                      {k: v for k, v in r["race"].items() if k in ("fwd_stall_FwdGetS", "fwd_stall_FwdGetM", "inv_in_SM_AD", "inv_in_SI_A", "fwdgets_in_MI_A", "fwdgetm_in_MI_A", "ack_before_data", "fwd_stall_Inv", "putm_nonowner", "dir_stall")})
