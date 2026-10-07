'use strict';
// COHERE-12 cycle-accurate simulator (Node.js, standard library only).
// Usage:
//   node sim.js baseline [traceFile]       run baseline, print metrics (optionally write trace)
//   node sim.js run d0 d1 map Q B [trace]  run one configuration
// Also exported as a module: simulate(d0, d1, map, Q, B, traceFn) -> metrics object.

// ---------------- Figures (values read from the packet) ----------------
// Figure 1: node n is at row floor(n/4), column n%4; core Ci sits on node Ni.
// Figure 2: link latencies (cycles, both directions).
const LINK_LAT = {
  '0-1': 1, '1-2': 2, '2-3': 1,
  '4-5': 2, '5-6': 1, '6-7': 3,
  '0-4': 1, '1-5': 3, '2-6': 1, '3-7': 2,
};
// Figure 5: baseline line map (bit L = 1 when line L's home is D1).
const BASELINE_MAP = 19245; // L0 L2 L3 L5 L8 L9 L11 L14 -> D1

// ---------------- constants ----------------
const NNODES = 8, NCORES = 8, NLINES = 16;
const GETS = 0, GETM = 1, PUTS = 2, PUTM = 3, FWDGETS = 4, FWDGETM = 5, INV = 6, PUTACK = 7, DATA = 8, INVACK = 9, NACK = 10;
const TNAME = ['GetS', 'GetM', 'PutS', 'PutM', 'FwdGetS', 'FwdGetM', 'Inv', 'PutAck', 'Data', 'InvAck', 'Nack'];
const NET_RESP = 0, NET_FWD = 1, NET_REQ = 2; // also link priority order
const NETNAME = ['RESP', 'FWD', 'REQ'];
const NET_OF = [NET_REQ, NET_REQ, NET_REQ, NET_REQ, NET_FWD, NET_FWD, NET_FWD, NET_FWD, NET_RESP, NET_RESP, NET_RESP];
// cache states
const I = 0, IS_D = 1, IM_AD = 2, IM_A = 3, S = 4, SM_AD = 5, SM_A = 6, M = 7, MI_A = 8, SI_A = 9, II_A = 10;
const SNAME = ['I', 'IS_D', 'IM_AD', 'IM_A', 'S', 'SM_AD', 'SM_A', 'M', 'MI_A', 'SI_A', 'II_A'];
// directory states
const DI = 0, DS = 1, DM = 2, DSD = 3;
const DSNAME = ['I', 'S', 'M', 'S_D'];

// ---------------- topology ----------------
// directed links: id -> (from, to, lat)
const LFROM = [], LTO = [], LLAT = [];
const linkId = {}; // "a>b" -> id
for (const k of Object.keys(LINK_LAT)) {
  const [a, b] = k.split('-').map(Number);
  for (const [x, y] of [[a, b], [b, a]]) {
    linkId[x + '>' + y] = LFROM.length;
    LFROM.push(x); LTO.push(y); LLAT.push(LINK_LAT[k]);
  }
}
const NLINKS = LFROM.length;
// XY routing: next link from cur toward dst (-1 if cur==dst)
const NEXT = new Int32Array(NNODES * NNODES).fill(-1);
for (let c = 0; c < NNODES; c++) for (let d = 0; d < NNODES; d++) {
  if (c === d) continue;
  const cr = c >> 2, cc = c & 3, dr = d >> 2, dc = d & 3;
  let n;
  if (cc !== dc) n = cr * 4 + cc + (dc > cc ? 1 : -1);
  else n = (dr > cr ? cr + 1 : cr - 1) * 4 + cc;
  const id = linkId[c + '>' + n];
  if (id === undefined) throw new Error('no link ' + c + '>' + n);
  NEXT[c * NNODES + d] = id;
}

// ---------------- workload (Section 7) ----------------
// op encoding: kind 0=LD,1=ST,2=WAIT ; arg = line or n
const OPK = [], OPA = [];
const NOPS = 400;
for (let c = 0; c < NCORES; c++) {
  let x = 101 + 7 * c;
  const k = new Int8Array(NOPS), a = new Int32Array(NOPS);
  for (let i = 0; i < NOPS; i++) {
    x = Number((1103515245n * BigInt(x) + 12345n) % 2147483648n);
    const r = Math.floor(x / 256), kind = r % 10;
    x = Number((1103515245n * BigInt(x) + 12345n) % 2147483648n);
    const s = Math.floor(x / 256);
    const line = (Math.floor(s / 16) % 10) < 6 ? s % 3 : s % 16;
    if (kind <= 4) { k[i] = 0; a[i] = line; }
    else if (kind <= 7) { k[i] = 1; a[i] = line; }
    else { k[i] = 2; a[i] = 1 + (Math.floor(s / 8) % 7); }
  }
  OPK.push(k); OPA.push(a);
}
const OPKF = new Int8Array(NCORES * NOPS), OPAF = new Int32Array(NCORES * NOPS);
for (let c = 0; c < NCORES; c++) { OPKF.set(OPK[c], c * NOPS); OPAF.set(OPA[c], c * NOPS); }

// ---------------- message store (reused across runs) ----------------
let CAP = 1 << 18;
let mType = new Int8Array(CAP), mSrc = new Int8Array(CAP), mDst = new Int8Array(CAP), mLine = new Int8Array(CAP),
  mReq = new Int8Array(CAP), mAck = new Int8Array(CAP), mX = new Int8Array(CAP), mNode = new Int8Array(CAP),
  mData = new Int32Array(CAP), mEntry = new Int32Array(CAP);
function grow() {
  const n = CAP * 2;
  const g = (A, T) => { const b = new T(n); b.set(A); return b; };
  mType = g(mType, Int8Array); mSrc = g(mSrc, Int8Array); mDst = g(mDst, Int8Array); mLine = g(mLine, Int8Array);
  mReq = g(mReq, Int8Array); mAck = g(mAck, Int8Array); mX = g(mX, Int8Array); mNode = g(mNode, Int8Array);
  mData = g(mData, Int32Array); mEntry = g(mEntry, Int32Array); CAP = n;
}

// reusable ring buffers
const LC = 1024, IC = 1024, RING = 8, BC = 4096;
const LQ = new Int32Array(NLINKS * 3 * LC), lqHead = new Int32Array(NLINKS * 3), lqTail = new Int32Array(NLINKS * 3), lqCnt = new Int32Array(NLINKS);
const IQ = new Int32Array(10 * 3 * IC), iqHead = new Int32Array(30), iqTail = new Int32Array(30);
const BK = new Int32Array(RING * BC), bkN = new Int32Array(RING);
function lqPush(l, net, m) {
  const qi = l * 3 + net;
  if (lqTail[qi] - lqHead[qi] >= LC) throw new Error('link queue overflow');
  LQ[qi * LC + (lqTail[qi]++ & (LC - 1))] = m; lqCnt[l]++;
}
function iqPush(qi, m) {
  if (iqTail[qi] - iqHead[qi] >= IC) throw new Error('input queue overflow');
  IQ[qi * IC + (iqTail[qi]++ & (IC - 1))] = m;
}
const MAXCYC = +(process.env.MAXCYC || 5000000);

// entity ids: 0..7 caches (on node i), 8 = D0, 9 = D1
function simulate(d0node, d1node, lineMap, Q, B, trace) {
  const entNode = new Int8Array(10);
  for (let i = 0; i < 8; i++) entNode[i] = i;
  entNode[8] = d0node; entNode[9] = d1node;
  const home = new Int8Array(NLINES);
  for (let L = 0; L < NLINES; L++) home[L] = ((lineMap >> L) & 1) ? 9 : 8;

  // link queues: ring buffer per (link, net), FIFO of message ids (sorted by entry cycle, then serial)
  lqHead.fill(0); lqTail.fill(0); lqCnt.fill(0);
  let inRouters = 0; // messages waiting in router queues
  // arrival buckets (ring of cycles)
  bkN.fill(0);
  let inFlight = 0;
  // entity input queues: ring buffer per (entity, net)
  iqHead.fill(0); iqTail.fill(0);
  let inQueues = 0;
  const refused = [[], []]; // per directory, message ids refused this cycle

  // directory state per line
  const dState = new Int8Array(NLINES), dSharers = new Int32Array(NLINES), dOwner = new Int8Array(NLINES).fill(-1), dMem = new Int32Array(NLINES);
  // cache state per core*16+line
  const cState = new Int8Array(NCORES * NLINES), cData = new Int32Array(NCORES * NLINES), cAck = new Int32Array(NCORES * NLINES),
    cWay = new Int8Array(NCORES * NLINES).fill(-1), cK = new Int32Array(NCORES * NLINES);
  // retry: per core*16+line retry cycle (0 = none) and type
  const rCyc = new Int32Array(NCORES * NLINES), rType = new Int8Array(NCORES * NLINES);
  const rCount = new Int32Array(NCORES); let rTotal = 0;
  // ways: core*4 + set*2 + way -> line or -1 ; lru stamp
  const wLine = new Int8Array(NCORES * 4).fill(-1), wLru = new Int32Array(NCORES * 4);
  // cores
  const pc = new Int32Array(NCORES), nextOp = new Int32Array(NCORES).fill(1), waiting = new Int8Array(NCORES),
    finished = new Int32Array(NCORES), stores = new Int32Array(NCORES), issueCyc = new Int32Array(NCORES), firstTry = new Int32Array(NCORES);
  const opTry = new Int32Array(NCORES).fill(-1);
  let nFinished = 0;
  const lat = [], latFirst = [];
  let serial = 0, nacks = 0, cycle = 0;
  const msgCount = new Int32Array(11);

  function send(type, src, dst, line, req, ack, data, x) {
    if (serial + 1 >= CAP) grow();
    const m = ++serial;
    mType[m] = type; mSrc[m] = src; mDst[m] = dst; mLine[m] = line; mReq[m] = req; mAck[m] = ack; mData[m] = data; mX[m] = x;
    msgCount[type]++;
    const sn = entNode[src], dn = entNode[dst];
    mNode[m] = sn;
    if (sn === dn) { const b = (cycle + 1) & (RING - 1); BK[b * BC + bkN[b]++] = m; inFlight++; }
    else { mEntry[m] = cycle; lqPush(NEXT[sn * NNODES + dn], NET_OF[type], m); inRouters++; }
    if (trace) trace(`MSG ${cycle} ${m} ${TNAME[type]} src=${src} dst=${dst} line=${line} req=${req} ack=${ack} data=${data}` + (type === NACK ? ` refused=${TNAME[x]}` : ''));
    return m;
  }
  function setState(c, L, ns) {
    const i = c * NLINES + L;
    if (trace) trace(`STATE ${cycle} C${c} L${L} ${SNAME[cState[i]]} ${SNAME[ns]}`);
    cState[i] = ns;
  }
  function freeWay(c, L) {
    const i = c * NLINES + L;
    wLine[c * 4 + cWay[i]] = -1; cWay[i] = -1;
    setState(c, L, I);
  }
  function completeStore(c, L) {
    const i = c * NLINES + L;
    stores[c]++;
    cData[i] = 1000 * c + stores[c];
    wLru[c * 4 + cWay[i]] = cycle;
    waiting[c] = 0; nextOp[c] = cycle + 1; pc[c]++;
    if (trace) trace(`STORE ${cycle} C${c} L${L} ${cData[i]} miss`);
  }
  function completeLoad(c, L) {
    const i = c * NLINES + L;
    wLru[c * 4 + cWay[i]] = cycle;
    waiting[c] = 0; nextOp[c] = cycle + 1; pc[c]++;
    lat.push(cycle - issueCyc[c]); latFirst.push(cycle - firstTry[c]);
    if (trace) trace(`LOAD ${cycle} C${c} L${L} ${cData[i]} miss`);
  }

  for (cycle = 1; cycle < MAXCYC; cycle++) {
    // (1) links
    if (inRouters) {
      for (let l = 0; l < NLINKS; l++) {
        if (!lqCnt[l]) continue;
        let m = 0;
        for (let n = 0; n < 3; n++) {
          const qi = l * 3 + n;
          // each FIFO is sorted by (entry cycle, serial); everything waiting entered before this cycle
          if (lqHead[qi] !== lqTail[qi]) { m = LQ[qi * LC + (lqHead[qi]++ & (LC - 1))]; break; }
        }
        if (m) {
          lqCnt[l]--; inRouters--;
          mNode[m] = LTO[l];
          const b = (cycle + LLAT[l]) & (RING - 1); BK[b * BC + bkN[b]++] = m; inFlight++;
          if (trace) trace(`LINK ${cycle} ${m} ${LFROM[l]}>${LTO[l]} arrive=${cycle + LLAT[l]}`);
        }
      }
    }
    // (2) arrivals
    const bslot = cycle & (RING - 1), nb = bkN[bslot];
    if (nb) {
      const b0 = bslot * BC;
      // arrivals in increasing serial order (insertion sort; buckets are small)
      for (let j = 1; j < nb; j++) { const v = BK[b0 + j]; let k = j - 1; while (k >= 0 && BK[b0 + k] > v) { BK[b0 + k + 1] = BK[b0 + k]; k--; } BK[b0 + k + 1] = v; }
      for (let j = 0; j < nb; j++) {
        const m = BK[b0 + j]; inFlight--;
        const dst = mDst[m], node = mNode[m];
        if (node === entNode[dst]) {
          const net = NET_OF[mType[m]];
          const qi = dst * 3 + net;
          if (net === NET_REQ && dst >= 8 && iqTail[qi] - iqHead[qi] >= Q) {
            refused[dst - 8].push(m);
            if (trace) trace(`REFUSE ${cycle} ${m} D${dst - 8}`);
          } else {
            iqPush(qi, m); inQueues++;
            if (trace) trace(`ARRIVE ${cycle} ${m} ent=${dst}`);
          }
        } else {
          mEntry[m] = cycle;
          lqPush(NEXT[node * NNODES + entNode[dst]], NET_OF[mType[m]], m); inRouters++;
        }
      }
      bkN[bslot] = 0;
    }
    // (3) controllers: D0, D1
    for (let d = 8; d <= 9; d++) {
      const qr = d * 3 + NET_RESP, qq = d * 3 + NET_REQ;
      // (a) RESP
      if (iqHead[qr] !== iqTail[qr]) {
        const m = IQ[qr * IC + (iqHead[qr]++ & (IC - 1))]; inQueues--;
        const L = mLine[m];
        if (mType[m] !== DATA || dState[L] !== DSD) throw new Error(`dir unexpected ${TNAME[mType[m]]} in ${DSNAME[dState[L]]} cyc ${cycle}`);
        dMem[L] = mData[m]; dState[L] = DS;
        if (trace) trace(`DIR ${cycle} D${d - 8} L${L} Data S_D->S mem=${dMem[L]}`);
      }
      // (b) REQ
      if (iqHead[qq] !== iqTail[qq]) {
        const m = IQ[qq * IC + (iqHead[qq] & (IC - 1))];
        const L = mLine[m], t = mType[m], r = mSrc[m], st = dState[L];
        let stall = false;
        if (t === GETS) {
          if (st === DI) { send(DATA, d, r, L, r, 0, dMem[L], 0); dSharers[L] |= 1 << r; dState[L] = DS; }
          else if (st === DS) { send(DATA, d, r, L, r, 0, dMem[L], 0); dSharers[L] |= 1 << r; }
          else if (st === DM) { const o = dOwner[L]; send(FWDGETS, d, o, L, r, 0, 0, 0); dSharers[L] |= (1 << r) | (1 << o); dOwner[L] = -1; dState[L] = DSD; }
          else stall = true;
        } else if (t === GETM) {
          if (st === DI) { send(DATA, d, r, L, r, 0, dMem[L], 0); dOwner[L] = r; dState[L] = DM; }
          else if (st === DS) {
            const others = dSharers[L] & ~(1 << r);
            let n = 0; for (let c = 0; c < 8; c++) if (others & (1 << c)) n++;
            send(DATA, d, r, L, r, n, dMem[L], 0);
            for (let c = 0; c < 8; c++) if (others & (1 << c)) send(INV, d, c, L, r, 0, 0, 0);
            dSharers[L] = 0; dOwner[L] = r; dState[L] = DM;
          }
          else if (st === DM) { send(FWDGETM, d, dOwner[L], L, r, 0, 0, 0); dOwner[L] = r; }
          else stall = true;
        } else if (t === PUTS) {
          if (st === DS) { dSharers[L] &= ~(1 << r); send(PUTACK, d, r, L, r, 0, 0, 0); if (!dSharers[L]) dState[L] = DI; }
          else if (st === DSD) { dSharers[L] &= ~(1 << r); send(PUTACK, d, r, L, r, 0, 0, 0); }
          else send(PUTACK, d, r, L, r, 0, 0, 0);
        } else if (t === PUTM) {
          if (st === DS) { dSharers[L] &= ~(1 << r); send(PUTACK, d, r, L, r, 0, 0, 0); if (!dSharers[L]) dState[L] = DI; }
          else if (st === DSD) { dSharers[L] &= ~(1 << r); send(PUTACK, d, r, L, r, 0, 0, 0); }
          else if (st === DM && dOwner[L] === r) { dMem[L] = mData[m]; dOwner[L] = -1; dState[L] = DI; send(PUTACK, d, r, L, r, 0, 0, 0); }
          else send(PUTACK, d, r, L, r, 0, 0, 0);
        } else throw new Error('dir bad req');
        if (!stall) { iqHead[qq]++; inQueues--; }
        if (trace) trace(`DIR ${cycle} D${d - 8} L${L} ${TNAME[t]} from C${r} ${DSNAME[st]}->${DSNAME[dState[L]]}${stall ? ' stall' : ''} sharers=${dSharers[L]} owner=${dOwner[L]}`);
      }
      // (c) Nacks
      const rf = refused[d - 8];
      if (rf.length) {
        for (let j = 0; j < rf.length; j++) { const m = rf[j]; send(NACK, d, mSrc[m], mLine[m], mSrc[m], 0, 0, mType[m]); nacks++; }
        rf.length = 0;
      }
    }
    // caches / cores
    for (let c = 0; c < NCORES; c++) {
      const base = c * NLINES;
      const qr = c * 3 + NET_RESP, qf = c * 3 + NET_FWD;
      if (iqHead[qr] === iqTail[qr] && iqHead[qf] === iqTail[qf] && !rCount[c] && (finished[c] || waiting[c] || nextOp[c] > cycle)) continue;
      // (a) RESP
      if (iqHead[qr] !== iqTail[qr]) {
        const m = IQ[qr * IC + (iqHead[qr]++ & (IC - 1))]; inQueues--;
        const t = mType[m], L = mLine[m], i = base + L, st = cState[i];
        if (t === NACK) {
          cK[i]++;
          const delay = Math.min(B * (1 << (cK[i] - 1)), 64);
          if (rCyc[i]) throw new Error('double retry');
          rCyc[i] = cycle + delay; rType[i] = mX[m]; rCount[c]++; rTotal++;
          if (trace) trace(`NACKRCV ${cycle} C${c} L${L} ${TNAME[mX[m]]} k=${cK[i]} retry=${cycle + delay}`);
        } else if (t === DATA) {
          const fromHome = mSrc[m] >= 8;
          cK[i] = 0;
          if (st === IS_D) { cData[i] = mData[m]; setState(c, L, S); completeLoad(c, L); }
          else if (st === IM_AD || st === SM_AD) {
            cData[i] = mData[m];
            if (fromHome) {
              cAck[i] += mAck[m];
              if (cAck[i] === 0) { setState(c, L, M); completeStore(c, L); }
              else setState(c, L, st === IM_AD ? IM_A : SM_A);
            } else { setState(c, L, M); completeStore(c, L); }
          } else throw new Error(`C${c} Data in ${SNAME[st]} L${L} cyc ${cycle}`);
        } else if (t === INVACK) {
          if (st === IM_AD || st === SM_AD) cAck[i]--;
          else if (st === IM_A || st === SM_A) { cAck[i]--; if (cAck[i] === 0) { setState(c, L, M); completeStore(c, L); } }
          else throw new Error(`C${c} InvAck in ${SNAME[st]}`);
        } else throw new Error('cache bad resp');
      }
      // (b) FWD scan
      if (iqHead[qf] !== iqTail[qf]) {
        let blocked = 0;
        const fh = iqHead[qf], ft = iqTail[qf], fb = qf * IC;
        for (let j = fh; j < ft; j++) {
          const m = IQ[fb + (j & (IC - 1))], L = mLine[m];
          if (blocked & (1 << L)) continue;
          const t = mType[m], i = base + L, st = cState[i];
          let stall = false;
          if (t === FWDGETS) {
            if (st === M || st === MI_A) {
              send(DATA, c, mReq[m], L, mReq[m], 0, cData[i], 0);
              send(DATA, c, home[L] , L, mReq[m], 0, cData[i], 0);
              setState(c, L, st === M ? S : SI_A);
            } else if (st === IM_AD || st === IM_A || st === SM_AD || st === SM_A) stall = true;
            else throw new Error(`C${c} FwdGetS in ${SNAME[st]}`);
          } else if (t === FWDGETM) {
            if (st === M) { send(DATA, c, mReq[m], L, mReq[m], 0, cData[i], 0); freeWay(c, L); }
            else if (st === MI_A) { send(DATA, c, mReq[m], L, mReq[m], 0, cData[i], 0); setState(c, L, II_A); }
            else if (st === IM_AD || st === IM_A || st === SM_AD || st === SM_A) stall = true;
            else throw new Error(`C${c} FwdGetM in ${SNAME[st]}`);
          } else if (t === INV) {
            if (st === S) { send(INVACK, c, mReq[m], L, mReq[m], 0, 0, 0); freeWay(c, L); }
            else if (st === SM_AD) { send(INVACK, c, mReq[m], L, mReq[m], 0, 0, 0); setState(c, L, IM_AD); }
            else if (st === SI_A) { send(INVACK, c, mReq[m], L, mReq[m], 0, 0, 0); setState(c, L, II_A); }
            else if (st === IS_D) stall = true;
            else throw new Error(`C${c} Inv in ${SNAME[st]} L${L} cyc ${cycle}`);
          } else if (t === PUTACK) {
            if (st === MI_A || st === SI_A || st === II_A) { cK[i] = 0; freeWay(c, L); }
            else throw new Error(`C${c} PutAck in ${SNAME[st]}`);
          } else throw new Error('cache bad fwd');
          if (stall) { blocked |= 1 << L; continue; }
          // remove element j: shift earlier elements one slot towards the tail
          for (let k = j; k > fh; k--) IQ[fb + (k & (IC - 1))] = IQ[fb + ((k - 1) & (IC - 1))];
          iqHead[qf]++; inQueues--;
          break;
        }
      }
      // (c) resend
      if (rCount[c]) {
        let best = -1, bc = 0;
        for (let L = 0; L < NLINES; L++) { const rc = rCyc[base + L]; if (rc && rc <= cycle && (best < 0 || rc < bc)) { best = L; bc = rc; } }
        if (best >= 0) {
          const i = base + best;
          rCyc[i] = 0; rCount[c]--; rTotal--;
          send(rType[i], c, home[best], best, c, 0, rType[i] === PUTM ? cData[i] : 0, 0);
        }
      }
      // (d) core
      if (finished[c] || waiting[c] || nextOp[c] > cycle) continue;
      if (pc[c] >= NOPS) { finished[c] = cycle; nFinished++; if (trace) trace(`FINISH ${cycle} C${c}`); continue; }
      const k = OPKF[c * NOPS + pc[c]], a = OPAF[c * NOPS + pc[c]];
      if (k === 2) { nextOp[c] = cycle + a; pc[c]++; continue; }
      const L = a, i = base + L, st = cState[i];
      if (cWay[i] >= 0) {
        if (k === 0) {
          if (st === S || st === SM_AD || st === SM_A || st === M) {
            wLru[c * 4 + cWay[i]] = cycle; nextOp[c] = cycle + 1; pc[c]++;
            if (trace) trace(`LOAD ${cycle} C${c} L${L} ${cData[i]} hit`);
          } else nextOp[c] = cycle + 1; // stall
        } else {
          if (st === M) {
            stores[c]++; cData[i] = 1000 * c + stores[c];
            wLru[c * 4 + cWay[i]] = cycle; nextOp[c] = cycle + 1; pc[c]++;
            if (trace) trace(`STORE ${cycle} C${c} L${L} ${cData[i]} hit`);
          } else if (st === S) {
            if (opTry[c] !== pc[c]) { opTry[c] = pc[c]; firstTry[c] = cycle; }
            cAck[i] = 0; cK[i] = 0; setState(c, L, SM_AD); waiting[c] = 1; issueCyc[c] = cycle;
            send(GETM, c, home[L], L, c, 0, 0, 0);
          } else nextOp[c] = cycle + 1; // stall
        }
      } else {
        // miss: record first attempt of this op
        if (opTry[c] !== pc[c]) { opTry[c] = pc[c]; firstTry[c] = cycle; }
        const set = (L >> 1) & 1, wb = c * 4 + set * 2;
        let w = -1;
        if (wLine[wb] < 0) w = 0; else if (wLine[wb + 1] < 0) w = 1;
        if (w >= 0) {
          wLine[wb + w] = L; wLru[wb + w] = cycle; cWay[i] = set * 2 + w; cAck[i] = 0; cK[i] = 0;
          setState(c, L, k === 0 ? IS_D : IM_AD);
          waiting[c] = 1; issueCyc[c] = cycle;
          send(k === 0 ? GETS : GETM, c, home[L], L, c, 0, 0, 0);
        } else {
          let v = -1;
          for (let ww = 0; ww < 2; ww++) {
            const vl = wLine[wb + ww], vs = cState[base + vl];
            if (vs === S || vs === M) { if (v < 0 || wLru[wb + ww] < wLru[wb + v]) v = ww; }
          }
          if (v >= 0) {
            const vl = wLine[wb + v], vi = base + vl;
            cK[vi] = 0;
            if (cState[vi] === S) { setState(c, vl, SI_A); send(PUTS, c, home[vl], vl, c, 0, 0, 0); }
            else { setState(c, vl, MI_A); send(PUTM, c, home[vl], vl, c, 0, cData[vi], 0); }
          }
          nextOp[c] = cycle + 1;
        }
      }
    }
    if (nFinished === NCORES && !inRouters && !inFlight && !inQueues && !rTotal && !refused[0].length && !refused[1].length) break;
  }
  if (cycle >= MAXCYC) { console.error(JSON.stringify({pc:Array.from(pc),waiting:Array.from(waiting),fin:Array.from(finished),nextOp:Array.from(nextOp),inRouters,inFlight,inQueues,rTotal,serial,nacks})); for(let c=0;c<8;c++){let s='';for(let L=0;L<16;L++)s+=SNAME[cState[c*16+L]]+' ';console.error('C'+c,s);} console.error('wLine',Array.from(wLine).join(','),'cWay',Array.from(cWay).join(','),'ops',[0,1,2].map(c=>OPK[c][pc[c]]+':'+OPA[c][pc[c]]));console.error('dir',Array.from(dState).map(x=>DSNAME[x]).join(' '), ); throw new Error('did not terminate'); }
  let makespan = 0; for (let c = 0; c < NCORES; c++) if (finished[c] > makespan) makespan = finished[c];
  const sl = lat.slice().sort((a, b) => a - b);
  const p95 = sl.length ? sl[Math.min(sl.length - 1, Math.floor(0.95 * sl.length))] : 0;
  const sf = latFirst.slice().sort((a, b) => a - b);
  const p95first = sf.length ? sf[Math.min(sf.length - 1, Math.floor(0.95 * sf.length))] : 0;
  return { makespan, p95, p95first, loadMisses: lat.length, messages: serial, nacks, endCycle: cycle, msgCount: Array.from(msgCount) };
}

module.exports = { simulate, BASELINE_MAP, LINK_LAT, OPK, OPA };

if (require.main === module) {
  const fs = require('fs');
  const argv = process.argv.slice(2);
  let cfg, traceFile;
  if (argv[0] === 'baseline') { cfg = [0, 7, BASELINE_MAP, 2, 2]; traceFile = argv[1]; }
  else if (argv[0] === 'run') { cfg = argv.slice(1, 6).map(Number); traceFile = argv[6]; }
  else { console.error('usage: node sim.js baseline [trace] | run d0 d1 map Q B [trace]'); process.exit(1); }
  let out = null, buf = [];
  const tr = traceFile ? (s) => { buf.push(s); if (buf.length > 10000) { fs.appendFileSync(traceFile, buf.join('\n') + '\n'); buf = []; } } : null;
  if (traceFile) fs.writeFileSync(traceFile, `CONFIG d0=${cfg[0]} d1=${cfg[1]} map=${cfg[2]} Q=${cfg[3]} B=${cfg[4]}\n`);
  const t0 = process.hrtime.bigint();
  const r = simulate(cfg[0], cfg[1], cfg[2], cfg[3], cfg[4], tr);
  const t1 = process.hrtime.bigint();
  if (traceFile) { fs.appendFileSync(traceFile, buf.join('\n') + '\nEND ' + JSON.stringify(r) + '\n'); }
  r.ms = Number(t1 - t0) / 1e6;
  console.log(JSON.stringify(r));
}
