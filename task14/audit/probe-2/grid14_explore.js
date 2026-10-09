#!/usr/bin/env node
// Batch driver for grid14_sim.js: stratified random sampling, exhaustive offset enumeration of one
// (cycle, plan, order) stratum, and coordinate-descent search. Writes CSV lines:
//   index,C,plan,order,offsets(9, ';'-separated),AM,PM,EVENT,total,gridlock
'use strict';
const fs = require('fs');
const S = require('./grid14_sim.js');

const args = process.argv.slice(2);
const get = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const mode = args[0];
const worker = +get('worker', 0), nworkers = +get('nworkers', 1);
const outFile = get('out', `out_${mode}_${worker}.csv`);
let buf = [];
function flush() { if (buf.length) { fs.appendFileSync(outFile, buf.join('\n') + '\n'); buf = []; } }
function record(idx, r) {
  const c = S.decode(idx);
  buf.push([idx, c.C, c.plan, c.order, c.offsets.join(';'), r.AM, r.PM, r.EVENT, r.total, r.gridlock ? 1 : 0].join(','));
  if (buf.length >= 200) flush();
}
// deterministic 32-bit RNG (mulberry32)
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

if (mode === 'sample') {
  // Stratified uniform sample: for each of the 72 (C, plan, order) strata, `per` offset vectors drawn
  // uniformly with replacement from the 4^9 offset combinations. Strata have equal size, so the pooled
  // sample is a uniform sample of the whole space.
  const per = +get('per', 1000), seed = +get('seed', 1);
  const jobs = [];
  for (let s = 0; s < 72; s++) { const r = rng(seed * 1000 + s); for (let i = 0; i < per; i++) jobs.push(s * S.NOFF + Math.floor(r() * S.NOFF)); }
  // interleave strata so partial output is balanced
  const order = [];
  for (let i = 0; i < per; i++) for (let s = 0; s < 72; s++) order.push(jobs[s * per + i]);
  for (let q = worker; q < order.length; q += nworkers) record(order[q], S.evaluate(S.decode(order[q])));
  flush();
} else if (mode === 'exhaust') {
  // all 4^9 offset vectors of one stratum
  const C = +get('C'), plan = +get('plan'), ord = get('order');
  const base = S.encode(C, plan, ord, [0, 0, 0, 0, 0, 0, 0, 0, 0]);
  for (let o = worker; o < S.NOFF; o += nworkers) record(base + o, S.evaluate(S.decode(base + o)));
  flush();
} else if (mode === 'descent') {
  // coordinate descent on offsets from given start indices (comma separated), within their stratum
  const starts = get('starts').split(',').map(Number);
  const cache = new Map();
  const ev = (idx) => { if (!cache.has(idx)) { const r = S.evaluate(S.decode(idx)); cache.set(idx, r); record(idx, r); } return cache.get(idx); };
  const better = (a, ia, b, ib) => a.total < b.total || (a.total === b.total && ia < ib);
  for (let si = worker; si < starts.length; si += nworkers) {
    let cur = starts[si], curR = ev(cur);
    let improved = true;
    while (improved) {
      improved = false;
      for (let j = 0; j < 9; j++) {
        const c = S.decode(cur);
        for (let q = 0; q < 4; q++) {
          if (q === c.offIdx[j]) continue;
          const oi = c.offIdx.slice(); oi[j] = q;
          const idx = S.encode(c.C, c.plan, c.order, oi), r = ev(idx);
          if (better(r, idx, curR, cur)) { cur = idx; curR = r; improved = true; }
        }
      }
    }
    console.log(JSON.stringify({ start: starts[si], best: cur, total: curR.total, cfg: S.decode(cur) }));
  }
  flush();
} else {
  console.log('usage: node grid14_explore.js sample|exhaust|descent [--per N --seed S] [--C --plan --order] [--starts i,j] --worker w --nworkers W --out file');
}
