'use strict';
// COHERE-12 engine, JavaScript port (independent check of cohere.c and speed probe for Node).
const RESP = 0, FWD = 1, REQ = 2, NCORE = 8, SETS = 2, WAYS = 2;
const T = { GETS: 0, GETM: 1, PUTS: 2, PUTM: 3, FWDGETS: 4, FWDGETM: 5, INV: 6, PUTACK: 7, DATA: 8, INVACK: 9, NACK: 10 };
const S = { NONE: 0, ISD: 1, IMAD: 2, IMA: 3, S: 4, SMAD: 5, SMA: 6, M: 7, MIA: 8, SIA: 9, IIA: 10 };
const D = { I: 0, S: 1, M: 2, SD: 3 };
const LAT = Array.from({ length: 8 }, () => new Array(8).fill(0));
for (const [a, b, l] of [[0,1,1],[1,2,2],[2,3,1],[4,5,2],[5,6,1],[6,7,3],[0,4,1],[1,5,3],[2,6,1],[3,7,2]]) { LAT[a][b] = l; LAT[b][a] = l; }
function nextHop(cur, dst) { const r = cur >> 2, c = cur & 3, dr = dst >> 2, dc = dst & 3; if (dc > c) return cur + 1; if (dc < c) return cur - 1; if (dr > r) return cur + 4; return cur - 4; }

function workload(nline, nops) {
  const progs = [];
  for (let c = 0; c < NCORE; c++) {
    let x = 101 + 7 * c; const p = [];
    for (let i = 0; i < nops; i++) {
      x = Number((1103515245n * BigInt(x) + 12345n) % 2147483648n); const r = Math.floor(x / 256); const kind = r % 10;
      x = Number((1103515245n * BigInt(x) + 12345n) % 2147483648n); const s = Math.floor(x / 256);
      const line = (Math.floor(s / 16) % 10) < 6 ? s % 3 : s % nline;
      if (kind < 5) p.push([0, line]); else if (kind < 8) p.push([1, line]); else p.push([2, 1 + Math.floor(s / 8) % 7]);
    }
    progs.push(p);
  }
  return progs;
}

function run(progs, nline, d0, d1, qcap, backoff, home) {
  const dnode = [d0, d1];
  let t = 0, serial = 0, nmsgs = 0, nnacks = 0;
  const links = new Map(); // key a*8+b -> array of {t0,m}
  for (let a = 0; a < 8; a++) for (let b = 0; b < 8; b++) if (LAT[a][b]) links.set(a * 8 + b, []);
  let inflight = []; // {at, node, m}
  const inq = Array.from({ length: 10 }, () => [[], [], []]);
  const rejected = [[], []];
  const dstate = new Array(nline).fill(D.I), sharers = new Array(nline).fill(0), owner = new Array(nline).fill(-1), mem = new Array(nline).fill(0);
  const ways = Array.from({ length: NCORE }, () => Array.from({ length: SETS }, () => Array.from({ length: WAYS }, () => ({ line: 0, st: 0, lru: 0, val: 0 }))));
  const acks = Array.from({ length: NCORE }, () => new Array(nline).fill(0));
  const nackc = Array.from({ length: NCORE }, () => new Array(nline).fill(0));
  const pend = Array.from({ length: NCORE }, () => new Array(nline).fill(null));
  const pc = new Array(NCORE).fill(0), busy = new Array(NCORE).fill(0), wk = new Array(NCORE).fill(-1), wt0 = new Array(NCORE).fill(0), done = new Array(NCORE).fill(-1), seq = new Array(NCORE).fill(0);
  const lat = []; let npend = 0;
  const nodeOf = e => e < 8 ? e : dnode[e - 8];
  function send(typ, vnet, src, dst, line, req, ack, val) {
    const m = { serial: ++serial, typ, vnet, src, dst, line, req, ack, val, dnode: nodeOf(dst) };
    nmsgs++; if (typ === T.NACK) nnacks++;
    const sn = nodeOf(src);
    if (sn === m.dnode) inflight.push({ at: t + 1, node: m.dnode, m });
    else links.get(sn * 8 + nextHop(sn, m.dnode)).push({ t0: t, m });
  }
  const findw = (c, L) => { for (const w of ways[c][(L >> 1) % SETS]) if (w.st && w.line === L) return w; return null; };
  function complete(c, w) {
    if (wk[c] === 0) lat.push(t - wt0[c]); else { seq[c]++; w.val = c * 1000 + seq[c]; }
    w.lru = t; wk[c] = -1; pc[c]++; busy[c] = t + 1;
  }
  function dirReq(d, m) {
    const L = m.line, r = m.src, st = dstate[L], de = 8 + d;
    if (m.typ === T.GETS) {
      if (st === D.I) { send(T.DATA, RESP, de, r, L, 0, 0, mem[L]); sharers[L] |= 1 << r; dstate[L] = D.S; }
      else if (st === D.S) { send(T.DATA, RESP, de, r, L, 0, 0, mem[L]); sharers[L] |= 1 << r; }
      else if (st === D.M) { const o = owner[L]; send(T.FWDGETS, FWD, de, o, L, r, 0, 0); sharers[L] |= (1 << r) | (1 << o); owner[L] = -1; dstate[L] = D.SD; }
      else return false;
    } else if (m.typ === T.GETM) {
      if (st === D.I) { send(T.DATA, RESP, de, r, L, 0, 0, mem[L]); owner[L] = r; dstate[L] = D.M; }
      else if (st === D.S) {
        const others = sharers[L] & ~(1 << r); let n = 0; for (let c = 0; c < 8; c++) if (others >> c & 1) n++;
        send(T.DATA, RESP, de, r, L, 0, n, mem[L]);
        for (let c = 0; c < 8; c++) if (others >> c & 1) send(T.INV, FWD, de, c, L, r, 0, 0);
        sharers[L] = 0; owner[L] = r; dstate[L] = D.M;
      } else if (st === D.M) { const o = owner[L]; send(T.FWDGETM, FWD, de, o, L, r, 0, 0); owner[L] = r; }
      else return false;
    } else if (m.typ === T.PUTS) {
      if ((st === D.S || st === D.SD) && (sharers[L] >> r & 1)) { sharers[L] &= ~(1 << r); if (st === D.S && !sharers[L]) dstate[L] = D.I; }
      send(T.PUTACK, FWD, de, r, L, 0, 0, 0);
    } else {
      if (st === D.M && owner[L] === r) { mem[L] = m.val; owner[L] = -1; dstate[L] = D.I; }
      else if (st === D.S || st === D.SD) { sharers[L] &= ~(1 << r); if (st === D.S && !sharers[L]) dstate[L] = D.I; }
      send(T.PUTACK, FWD, de, r, L, 0, 0, 0);
    }
    return true;
  }
  function cacheResp(c, m) {
    const L = m.line, w = findw(c, L);
    if (m.typ === T.NACK) { const att = ++nackc[c][L]; const delay = Math.min(backoff * Math.pow(2, att - 1), 64); if (!pend[c][L]) npend++; pend[c][L] = [m.req, t + delay]; return; }
    if (m.typ === T.INVACK) { acks[c][L]--; if ((w.st === S.IMA || w.st === S.SMA) && acks[c][L] === 0) { w.st = S.M; nackc[c][L] = 0; complete(c, w); } return; }
    const st = w.st; w.val = m.val; nackc[c][L] = 0;
    if (st === S.ISD) { w.st = S.S; complete(c, w); }
    else if (st === S.IMAD || st === S.SMAD) {
      if (m.src < 8) { w.st = S.M; complete(c, w); }
      else { acks[c][L] += m.ack; if (acks[c][L] === 0) { w.st = S.M; complete(c, w); } else w.st = st === S.IMAD ? S.IMA : S.SMA; }
    } else throw new Error('bad data');
  }
  function cacheFwd(c, m) {
    const L = m.line, w = findw(c, L), st = w ? w.st : 0;
    if (m.typ === T.PUTACK) { w.st = 0; nackc[c][L] = 0; return true; }
    if (m.typ === T.INV) {
      if (st === S.ISD) return false;
      send(T.INVACK, RESP, c, m.req, L, 0, 0, 0);
      if (st === S.S) w.st = 0; else if (st === S.SMAD) w.st = S.IMAD; else if (st === S.SIA) w.st = S.IIA; else throw new Error('bad inv');
      return true;
    }
    if (st === S.IMAD || st === S.IMA || st === S.SMAD || st === S.SMA) return false;
    if (st !== S.M && st !== S.MIA) throw new Error('bad fwd');
    if (m.typ === T.FWDGETS) { send(T.DATA, RESP, c, m.req, L, 0, 0, w.val); send(T.DATA, RESP, c, 8 + home[L], L, 0, 0, w.val); w.st = st === S.M ? S.S : S.SIA; }
    else { send(T.DATA, RESP, c, m.req, L, 0, 0, w.val); if (st === S.M) w.st = 0; else w.st = S.IIA; }
    return true;
  }
  function coreStep(c) {
    if (done[c] >= 0 || wk[c] >= 0 || busy[c] > t) return;
    if (pc[c] >= progs[c].length) { done[c] = t; return; }
    const [op, arg] = progs[c][pc[c]];
    if (op === 2) { busy[c] = t + arg; pc[c]++; return; }
    const L = arg, w = findw(c, L);
    if (w) {
      const st = w.st;
      if (op === 0 && (st === S.S || st === S.M || st === S.SMAD || st === S.SMA)) { w.lru = t; pc[c]++; busy[c] = t + 1; return; }
      if (op === 1 && st === S.M) { seq[c]++; w.val = c * 1000 + seq[c]; w.lru = t; pc[c]++; busy[c] = t + 1; return; }
      if (op === 1 && st === S.S) { w.st = S.SMAD; wk[c] = 1; wt0[c] = t; send(T.GETM, REQ, c, 8 + home[L], L, 0, 0, 0); return; }
      return;
    }
    const set = ways[c][(L >> 1) % SETS];
    let fi = -1; for (let i = 0; i < WAYS; i++) if (!set[i].st) { fi = i; break; }
    if (fi < 0) {
      let vi = -1; for (let i = 0; i < WAYS; i++) if (set[i].st === S.S || set[i].st === S.M) { if (vi < 0 || set[i].lru < set[vi].lru) vi = i; }
      if (vi >= 0) { const v = set[vi]; if (v.st === S.S) { v.st = S.SIA; send(T.PUTS, REQ, c, 8 + home[v.line], v.line, 0, 0, 0); } else { v.st = S.MIA; send(T.PUTM, REQ, c, 8 + home[v.line], v.line, 0, 0, v.val); } }
      return;
    }
    const nw = set[fi]; nw.line = L; nw.st = op === 0 ? S.ISD : S.IMAD; nw.lru = t; nw.val = 0; wk[c] = op; wt0[c] = t;
    send(op === 0 ? T.GETS : T.GETM, REQ, c, 8 + home[L], L, 0, 0, 0);
  }
  const quiet = () => {
    for (let c = 0; c < NCORE; c++) if (done[c] < 0) return false;
    if (inflight.length || npend) return false;
    for (const q of links.values()) if (q.length) return false;
    for (const e of inq) for (const q of e) if (q.length) return false;
    return true;
  };
  while (!quiet()) {
    t++;
    if (t > 2000000) throw new Error('deadlock');
    for (const [k, q] of links) {
      let bi = -1;
      for (let i = 0; i < q.length; i++) { const x = q[i]; if (x.t0 >= t) continue; if (bi < 0) { bi = i; continue; } const y = q[bi];
        if (x.m.vnet < y.m.vnet || (x.m.vnet === y.m.vnet && (x.t0 < y.t0 || (x.t0 === y.t0 && x.m.serial < y.m.serial)))) bi = i; }
      if (bi < 0) continue;
      const { m } = q.splice(bi, 1)[0]; const a = k >> 3, b = k & 7;
      inflight.push({ at: t + LAT[a][b], node: b, m });
    }
    const now = inflight.filter(x => x.at === t).sort((x, y) => x.m.serial - y.m.serial);
    inflight = inflight.filter(x => x.at !== t);
    for (const { node, m } of now) {
      if (node === m.dnode) {
        if (m.dst >= 8 && m.vnet === REQ && inq[m.dst][REQ].length >= qcap) { rejected[m.dst - 8].push(m); continue; }
        inq[m.dst][m.vnet].push(m);
      } else links.get(node * 8 + nextHop(node, m.dnode)).push({ t0: t, m });
    }
    for (let d = 0; d < 2; d++) {
      const q = inq[8 + d];
      if (q[RESP].length) { const m = q[RESP].shift(); mem[m.line] = m.val; dstate[m.line] = D.S; }
      if (q[REQ].length && dirReq(d, q[REQ][0])) q[REQ].shift();
      for (const m of rejected[d]) send(T.NACK, RESP, 8 + d, m.src, m.line, m.typ, 0, 0);
      rejected[d] = [];
    }
    for (let c = 0; c < NCORE; c++) {
      const q = inq[c];
      if (q[RESP].length) cacheResp(c, q[RESP].shift());
      let blocked = 0;
      for (let i = 0; i < q[FWD].length; i++) { const m = q[FWD][i]; if (blocked >> m.line & 1) continue; if (cacheFwd(c, m)) { q[FWD].splice(i, 1); break; } blocked |= 1 << m.line; }
      if (npend) {
        let bl = -1; for (let L = 0; L < nline; L++) { const p = pend[c][L]; if (p && p[1] <= t && (bl < 0 || p[1] < pend[c][bl][1])) bl = L; }
        if (bl >= 0) { const [kind] = pend[c][bl]; pend[c][bl] = null; npend--; const w = findw(c, bl); send(kind, REQ, c, 8 + home[bl], bl, 0, 0, (w && kind === T.PUTM) ? w.val : 0); }
      }
      coreStep(c);
    }
  }
  lat.sort((a, b) => a - b);
  const idx = Math.min(lat.length - 1, Math.floor(0.95 * lat.length));
  return [Math.max(...done), lat.length ? lat[idx] : 0, nmsgs, nnacks];
}

if (require.main === module) {
  const [mode, ...a] = process.argv.slice(2);
  if (mode === 'one') {
    const [nline, nops, d0, d1, q, b, hb] = a.map(Number); const progs = workload(nline, nops);
    const home = Array.from({ length: nline }, (_, L) => (hb >> L) & 1);
    console.log(run(progs, nline, d0, d1, q, b, home).join(' '));
  } else if (mode === 'bench') {
    const [nline, nops, n] = a.map(Number); const progs = workload(nline, nops); const t0 = Date.now(); let acc = 0;
    for (let i = 0; i < n; i++) { const home = Array.from({ length: nline }, (_, L) => (i >> L) & 1); acc += run(progs, nline, 1, 6, 1 + i % 4, 1 << (i % 4), home)[0]; }
    console.log(acc, ((Date.now() - t0) / n).toFixed(3), 'ms per run');
  }
}
module.exports = { run, workload };
