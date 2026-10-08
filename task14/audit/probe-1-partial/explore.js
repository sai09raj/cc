'use strict';
// Configuration-space exploration driver for sim.js (Node.js standard library only).
//
//   node explore.js sample <worker> <nWorkers> <outCsv> [maxRounds]
//       Stratified uniform random sample: job j -> stratum j mod 72 (C, plan, order), round j div 72;
//       offsets drawn uniformly from 4^9 with a per-job deterministic hash. Worker w runs j = w, w+W, ...
//       Rows are appended as they finish, so the run can be stopped at any time.
//   node explore.js search <outCsv> <C> <plan> <order> <nStarts> [seed]
//       Multi-start coordinate descent over the nine offsets inside one (C, plan, order) stratum.
//
// CSV columns: C,plan,order,k0..k8 (offset = k*C/4),AM,PM,EVENT,total,gridlock
const fs = require('fs');
const S = require('./sim.js');
const CYC = S.CYCLES;

function strat(s) { // 0..71 -> C, plan, order
  return { C: CYC[Math.floor(s / 12)], plan: 1 + Math.floor((s % 12) / 2), order: (s % 2) ? 'lag' : 'lead' };
}
function hash32(a) { // splitmix-like integer hash
  a = (a + 0x9e3779b9) | 0; a = Math.imul(a ^ (a >>> 16), 0x85ebca6b); a = Math.imul(a ^ (a >>> 13), 0xc2b2ae35); return (a ^ (a >>> 16)) >>> 0;
}
function offsetsFor(job) { // 18 random bits -> nine base-4 digits
  const h = hash32(hash32(job) ^ 0x5bd1e995) & 0x3ffff;
  const ks = []; for (let i = 0; i < 9; i++) ks.push((h >>> (2 * i)) & 3);
  return ks;
}
function row(st, ks, r) {
  return `${st.C},${st.plan},${st.order},${ks.join(',')},${r.AM},${r.PM},${r.EVENT},${r.total},${r.gridlock ? 1 : 0}\n`;
}
const cfgOf = (st, ks) => ({ C: st.C, plan: st.plan, order: st.order, offsets: ks.map((k) => k * st.C / 4) });

const mode = process.argv[2];
if (mode === 'sample') {
  const w = +process.argv[3], W = +process.argv[4], out = process.argv[5];
  const maxRounds = +(process.argv[6] || 1e9);
  const fd = fs.openSync(out, 'a');
  for (let j = w; j < 72 * maxRounds; j += W) {
    const st = strat(j % 72);
    const ks = offsetsFor(j);
    const r = S.evalConfig(cfgOf(st, ks));
    fs.writeSync(fd, row(st, ks, r));
  }
  fs.closeSync(fd);
} else if (mode === 'search') {
  const out = process.argv[3];
  const st = { C: +process.argv[4], plan: +process.argv[5], order: process.argv[6] };
  const nStarts = +process.argv[7];
  let seed = +(process.argv[8] || 1);
  const fd = fs.openSync(out, 'a');
  const cache = new Map();
  const ev = (ks) => {
    const key = ks.join('');
    let r = cache.get(key);
    if (!r) { r = S.evalConfig(cfgOf(st, ks)); cache.set(key, r); fs.writeSync(fd, row(st, ks, r)); }
    return r;
  };
  // lexicographic tie-break on offsets (C, plan, order fixed inside a stratum)
  const better = (a, ka, b, kb) => a.total < b.total || (a.total === b.total && ka.join('') < kb.join(''));
  const rnd = () => { seed = hash32(seed); return seed; };
  const starts = [[0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 1, 2, 0, 1, 2, 0, 1, 2], [0, 0, 0, 1, 1, 1, 2, 2, 2], [0, 1, 2, 1, 2, 3, 2, 3, 0]];
  while (starts.length < nStarts) { const ks = []; for (let i = 0; i < 9; i++) ks.push(rnd() & 3); starts.push(ks); }
  let gbest = null, gks = null;
  for (const s0 of starts.slice(0, nStarts)) {
    let ks = s0.slice(), cur = ev(ks);
    let improved = true;
    while (improved) {
      improved = false;
      for (let i = 0; i < 9; i++) {
        for (let v = 0; v < 4; v++) {
          if (v === ks[i]) continue;
          const k2 = ks.slice(); k2[i] = v;
          const r = ev(k2);
          if (better(r, k2, cur, ks)) { ks = k2; cur = r; improved = true; }
        }
      }
    }
    // pairwise polish: try changing two offsets at once (adjacent intersections)
    let again = true;
    while (again) {
      again = false;
      for (let i = 0; i < 9 && !again; i++) for (let j = i + 1; j < 9 && !again; j++) {
        for (let a = 0; a < 4 && !again; a++) for (let b = 0; b < 4 && !again; b++) {
          if (a === ks[i] && b === ks[j]) continue;
          const k2 = ks.slice(); k2[i] = a; k2[j] = b;
          const r = ev(k2);
          if (better(r, k2, cur, ks)) { ks = k2; cur = r; again = true; }
        }
      }
    }
    if (!gbest || better(cur, ks, gbest, gks)) { gbest = cur; gks = ks; }
    console.log(`${st.C}/${st.plan}/${st.order} start ${s0.join('')} -> ${ks.join('')} total=${cur.total} (evaluated ${cache.size})`);
  }
  console.log(`BEST ${st.C}/${st.plan}/${st.order} ${gks.join('')} total=${gbest.total} evaluated=${cache.size}`);
  fs.closeSync(fd);
} else if (mode === 'list') {
  // node explore.js list <outCsv> C/plan/order/k0k1...k8 ...   (evaluate the named configurations)
  const fd = fs.openSync(process.argv[3], 'a');
  for (const spec of process.argv.slice(4)) {
    const [C, plan, order, kk] = spec.split('/');
    const st = { C: +C, plan: +plan, order };
    const ks = kk.split('').map(Number);
    const r = S.evalConfig(cfgOf(st, ks));
    fs.writeSync(fd, row(st, ks, r));
    console.log(spec, r.AM, r.PM, r.EVENT, r.total, r.gridlock);
  }
  fs.closeSync(fd);
} else if (mode === 'ils') {
  // node explore.js ils <outCsv> <C> <plan> <order> <seconds> <seed> [start k0..k8 as a 9-digit string]
  // Iterated local search: first-improvement single-offset descent in random order, then a random
  // kick of 2-4 offsets, accept the new local optimum if it is not worse. Every simulated
  // configuration is appended to outCsv.
  const out = process.argv[3];
  const st = { C: +process.argv[4], plan: +process.argv[5], order: process.argv[6] };
  const secs = +process.argv[7];
  let seed = +process.argv[8];
  const startStr = process.argv[9];
  const fd = fs.openSync(out, 'a');
  const cache = new Map();
  const ev = (ks) => {
    const key = ks.join('');
    let r = cache.get(key);
    if (!r) { r = S.evalConfig(cfgOf(st, ks)); cache.set(key, r); fs.writeSync(fd, row(st, ks, r)); }
    return r;
  };
  const better = (a, ka, b, kb) => a.total < b.total || (a.total === b.total && ka.join('') < kb.join(''));
  const rnd = () => { seed = hash32(seed); return seed; };
  const descend = (ks, cur) => {
    let improved = true;
    while (improved) {
      improved = false;
      const moves = [];
      for (let i = 0; i < 9; i++) for (let v = 0; v < 4; v++) if (v !== ks[i]) moves.push([i, v]);
      for (let a = moves.length - 1; a > 0; a--) { const b = rnd() % (a + 1); [moves[a], moves[b]] = [moves[b], moves[a]]; }
      for (const [i, v] of moves) {
        if (ks[i] === v) continue;
        const k2 = ks.slice(); k2[i] = v;
        const r = ev(k2);
        if (better(r, k2, cur, ks)) { ks = k2; cur = r; improved = true; }
      }
    }
    return [ks, cur];
  };
  let ks = startStr ? startStr.split('').map(Number) : [...Array(9)].map(() => rnd() & 3);
  let cur;
  [ks, cur] = descend(ks, ev(ks));
  let best = cur, bks = ks;
  const t0 = Date.now();
  let iter = 0;
  while ((Date.now() - t0) / 1000 < secs) {
    iter++;
    const k2 = ks.slice();
    const nk = 2 + (rnd() % 3);
    for (let q = 0; q < nk; q++) k2[rnd() % 9] = rnd() & 3;
    const [k3, r3] = descend(k2, ev(k2));
    if (!better(cur, ks, r3, k3)) { ks = k3; cur = r3; }
    if (better(cur, ks, best, bks)) { best = cur; bks = ks; console.log(`${((Date.now() - t0) / 1000).toFixed(0)}s iter ${iter} new best ${bks.join('')} total=${best.total} (evaluated ${cache.size})`); }
  }
  console.log(`BEST ${st.C}/${st.plan}/${st.order} ${bks.join('')} total=${best.total} AM=${best.AM} PM=${best.PM} EVENT=${best.EVENT} evaluated=${cache.size} iters=${iter}`);
  fs.closeSync(fd);
} else {
  console.error('usage: see header'); process.exit(1);
}
