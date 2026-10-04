#!/usr/bin/env node
// TENURE-11 independent verifier.
//
// Separately coded re-implementation of the collector rules (tenure11_v1.pdf
// sections 2-13, Figures 1-6). It does NOT import, call, or read the Python
// simulator. Different data model on purpose: every evacuation creates a NEW
// object record (a real copy) and leaves a forwarding pointer in the old one;
// references are rewritten through the forwarding pointer; regions are tracked
// as address-keyed tables; the remembered set is a sorted address array.
//
// Usage:
//   node verify.js LOGFILE [--hash HASHFILE] [--sweep SWEEP.CSV] [--rows 3,25,27,...|all]
// Exit status 0 = ACCEPT, 1 = REJECT.

'use strict';
const fs = require('fs');
const crypto = require('crypto');

// ---- figure constants (independently re-stated) ----
const HDR = 16, AL = 8, OLDCAP = 131072;
const BASE = { TEMP: 24, SESSION: 96, BLOB: 96, ENTRY: 56, NODE: 40, REG: 112 };
const NSLOT = { TEMP: 0, SESSION: 1, BLOB: 0, ENTRY: 1, NODE: 1, REG: 4 };
const PHASE_EDGES = [0, 4000, 16000, 22000, 26000];
const MIX = [
  'TEMP TEMP SESSION NODE TEMP ENTRY TEMP NODE TEMP SESSION',
  'TEMP SESSION TEMP ENTRY NODE TEMP ENTRY TEMP NODE TEMP',
  'SESSION TEMP SESSION ENTRY SESSION NODE SESSION TEMP ENTRY NODE',
  'TEMP TEMP ENTRY TEMP NODE TEMP TEMP TEMP ENTRY TEMP',
].map(s => s.split(' '));

function sizeOf(kind, i) {
  let p = BASE[kind];
  if (kind === 'BLOB') p += 96 * (i % 13);
  if (kind === 'ENTRY') p += 24 * (i % 3);
  if (kind === 'NODE') p += 8 * (i % 5);
  const raw = HDR + p;
  return Math.ceil(raw / AL) * AL;
}
function kindAt(i) {
  for (let ph = 0; ph < 4; ph++) if (i >= PHASE_EDGES[ph] && i < PHASE_EDGES[ph + 1]) return MIX[ph][i % 10];
  throw new Error('bad op ' + i);
}

class OutOfMemory extends Error { constructor(op) { super('OOM'); this.op = op; } }

// region codes
const EDEN = 1, SA = 2, SB = 3, OLD = 4, DEAD = 5;

function run(EDENSZ, SURVSZ, T, PT) {
  // object table
  const kind = [], size = [], slots = [], region = [], addr = [], age = [], occ = [], fwd = [];
  const newObj = (k, sz, ns) => {
    const id = kind.length;
    kind.push(k); size.push(sz); slots.push(new Array(ns).fill(-1));
    region.push(0); addr.push(0); age.push(0); occ.push(0); fwd.push(-1);
    return id;
  };
  const root = new Map();          // slot number -> id
  let edenTop = 0;
  let fromSpace = SA, toSpace = SB;
  let fromTop = 0;
  let freeList = [{ a: 0, n: OLDCAP }];
  const oldAt = new Map();         // address -> id
  let remset = [];                 // sorted array of old addresses
  let op = -1;
  const events = [];
  const M = { minor: 0, major: 0, copied: 0, promoted: 0, pretenured: 0, total: 0, maxp: 0, peak: 0 };

  const isYoung = id => region[id] === EDEN || region[id] === fromSpace;
  const occupancy = () => { let s = 0; for (const id of oldAt.values()) s += occ[id]; return s; };
  const freeTotal = () => freeList.reduce((s, b) => s + b.n, 0);
  const rsAdd = a => {
    let lo = 0, hi = remset.length;
    while (lo < hi) { const m = (lo + hi) >> 1; if (remset[m] < a) lo = m + 1; else hi = m; }
    if (remset[lo] !== a) remset.splice(lo, 0, a);
  };
  const pause = p => { M.total += p; if (p > M.maxp) M.maxp = p; };

  function placeOld(id) {
    const s = size[id];
    let pick = -1;
    for (let j = 0; j < freeList.length; j++) {
      if (freeList[j].n >= s && (pick < 0 || freeList[j].a < freeList[pick].a)) pick = j;
    }
    if (pick < 0) return false;
    const b = freeList[pick];
    let used;
    if (b.n - s >= 32) { used = s; freeList[pick] = { a: b.a + s, n: b.n - s }; }
    else { used = b.n; freeList.splice(pick, 1); }
    region[id] = OLD; addr[id] = b.a; occ[id] = used;
    oldAt.set(b.a, id);
    return true;
  }

  function majorGC() {
    const seen = new Set();
    const work = [];
    for (const k of [...root.keys()].sort((x, y) => x - y)) { const id = root.get(k); if (!seen.has(id)) { seen.add(id); work.push(id); } }
    while (work.length) {
      const id = work.shift();
      for (const r of slots[id]) if (r >= 0 && !seen.has(r)) { seen.add(r); work.push(r); }
    }
    let marked = 0, freed = 0;
    for (const [a, id] of [...oldAt.entries()]) {
      if (seen.has(id)) marked += occ[id];
      else {
        freed++;
        oldAt.delete(a);
        freeList.push({ a, n: occ[id] });
        region[id] = DEAD;
        const ix = remset.indexOf(a); if (ix >= 0) remset.splice(ix, 1);
      }
    }
    freeList.sort((x, y) => x.a - y.a);
    const merged = [];
    for (const b of freeList) {
      const last = merged[merged.length - 1];
      if (last && last.a + last.n === b.a) last.n += b.n; else merged.push({ a: b.a, n: b.n });
    }
    freeList = merged;
    const p = 150 + Math.floor(marked / 32) + Math.floor(freed / 2);
    M.major++; pause(p);
    events.push(['M', op, 0, 0, 0, marked, freed, occupancy(), p]);
  }

  function minorGC() {
    if (freeTotal() < edenTop + fromTop) majorGC();
    const R = remset.length;
    let toTop = 0, cp = 0, pr = 0;
    const fifo = [];
    // evacuate one reference; returns the new id to store
    const evac = ref => {
      if (ref < 0) return ref;
      if (fwd[ref] >= 0) return fwd[ref];
      if (!isYoung(ref)) return ref;
      const nage = age[ref] + 1;
      const copy = newObj(kind[ref], size[ref], 0);
      slots[copy] = slots[ref].slice();
      if (nage < T && toTop + size[ref] <= SURVSZ) {
        region[copy] = toSpace; addr[copy] = toTop; age[copy] = nage;
        toTop += size[ref]; cp += size[ref];
      } else {
        if (!placeOld(copy)) throw new OutOfMemory(op);
        pr += size[ref];
      }
      fwd[ref] = copy;
      region[ref] = DEAD;
      fifo.push(copy);
      return copy;
    };
    for (const k of [...root.keys()].sort((x, y) => x - y)) root.set(k, evac(root.get(k)));
    for (const a of remset.slice()) {
      const id = oldAt.get(a);
      for (let j = 0; j < slots[id].length; j++) slots[id][j] = evac(slots[id][j]);
    }
    for (let q = 0; q < fifo.length; q++) {
      const id = fifo[q];
      for (let j = 0; j < slots[id].length; j++) slots[id][j] = evac(slots[id][j]);
    }
    // empty eden + from-space (anything still there is abandoned)
    for (let id = 0; id < region.length; id++) if (region[id] === EDEN || region[id] === fromSpace) region[id] = DEAD;
    edenTop = 0;
    const t = fromSpace; fromSpace = toSpace; toSpace = t; fromTop = toTop;
    // rebuild remset: every old object with a reference into survivor (from) space
    remset = [];
    for (const [a, id] of oldAt) if (slots[id].some(r => r >= 0 && region[r] === fromSpace)) remset.push(a);
    remset.sort((x, y) => x - y);
    const p = 40 + Math.floor(cp / 64) + Math.floor(pr / 32) + 2 * R;
    M.minor++; M.copied += cp; M.promoted += pr; pause(p);
    const o = occupancy(); if (o > M.peak) M.peak = o;
    events.push(['m', op, cp, pr, R, 0, 0, o, p]);
  }

  function allocate(k, i) {
    const sz = sizeOf(k, i);
    const id = newObj(k, sz, NSLOT[k]);
    if (PT !== null && sz >= PT) {
      if (!placeOld(id)) { majorGC(); if (!placeOld(id)) throw new OutOfMemory(op); }
      M.pretenured += sz;
      const o = occupancy(); if (o > M.peak) M.peak = o;
      return id;
    }
    if (edenTop + sz > EDENSZ) minorGC();
    region[id] = EDEN; addr[id] = edenTop; age[id] = 0; edenTop += sz;
    return id;
  }
  function write(holder, j, ref) {
    slots[holder][j] = ref;
    if (ref >= 0 && region[holder] === OLD && isYoung(ref)) rsAdd(addr[holder]);
  }
  const setRoot = (k, id) => { if (id < 0) root.delete(k); else root.set(k, id); };
  const getRoot = k => root.has(k) ? root.get(k) : -1;

  let oomAt = null;
  try {
    op = -1;
    for (let j = 0; j < 16; j++) { const id = allocate('REG', -1); setRoot(100 + j, id); }
    let nSess = 0, nEnt = 0;
    for (let i = 0; i < PHASE_EDGES[4]; i++) {
      op = i;
      const k = kindAt(i);
      const id = allocate(k, i);
      switch (k) {
        case 'TEMP': setRoot(0, id); break;
        case 'SESSION': {
          const rs = 1 + (nSess % 64); nSess++;
          setRoot(rs, id);
          const blob = allocate('BLOB', i);
          write(getRoot(rs), 0, blob);
          break;
        }
        case 'ENTRY': {
          if (nSess > 0) write(id, 0, getRoot(1 + ((nSess - 1) % 64)));
          write(getRoot(100 + (nEnt % 16)), Math.floor(nEnt / 16) % 4, id);
          nEnt++;
          break;
        }
        case 'NODE': write(id, 0, getRoot(120)); setRoot(120, id); break;
      }
      if (i % 1500 === 1499) setRoot(120, -1);
    }
  } catch (e) {
    if (e instanceof OutOfMemory) oomAt = e.op; else throw e;
  }
  return { events, M, oomAt };
}

function render(events) {
  return 'TENURE11-GCLOG-V1\n' + events.map((e, n) => [n + 1, ...e].join(';')).join('\n') + '\n';
}

// ---------------------------------------------------------------- main
function main() {
  const argv = process.argv.slice(2);
  const opt = { rows: '3,25,27,54,91,92,0,26' };
  const pos = [];
  for (let j = 0; j < argv.length; j++) {
    if (argv[j] === '--hash') opt.hash = argv[++j];
    else if (argv[j] === '--sweep') opt.sweep = argv[++j];
    else if (argv[j] === '--rows') opt.rows = argv[++j];
    else pos.push(argv[j]);
  }
  const problems = [];
  const notes = [];
  const logPath = pos[0];
  const text = fs.readFileSync(logPath, 'latin1');

  // 1. structural/format checks
  const lines = text.split('\n');
  if (!text.endsWith('\n') || text.endsWith('\n\n')) problems.push('log must end with exactly one trailing newline');
  if (lines[0] !== 'TENURE11-GCLOG-V1') problems.push('missing/incorrect header line');
  const body = lines.slice(1, -1);
  const re = /^(0|[1-9]\d*);([mM]);(-1|0|[1-9]\d*)(;(0|[1-9]\d*)){7}$/;
  body.forEach((ln, k) => {
    if (!re.test(ln)) { problems.push(`line ${k + 2}: bad format: ${ln}`); return; }
    const f = ln.split(';');
    if (+f[0] !== k + 1) problems.push(`line ${k + 2}: n=${f[0]} expected ${k + 1}`);
    const [cp, pr, rs, mk, fr, , pa] = f.slice(3).map(Number);
    if (f[1] === 'm') {
      if (mk !== 0 || fr !== 0) problems.push(`line ${k + 2}: minor with nonzero marked/freed`);
      if (pa !== 40 + Math.floor(cp / 64) + Math.floor(pr / 32) + 2 * rs) problems.push(`line ${k + 2}: minor pause formula mismatch`);
    } else {
      if (cp || pr || rs) problems.push(`line ${k + 2}: major with nonzero copied/promoted/remset`);
      if (pa !== 150 + Math.floor(mk / 32) + Math.floor(fr / 2)) problems.push(`line ${k + 2}: major pause formula mismatch`);
    }
  });
  const fileHash = crypto.createHash('sha256').update(Buffer.from(text, 'latin1')).digest('hex').slice(0, 16);
  if (opt.hash) {
    const claimed = fs.readFileSync(opt.hash, 'utf8').trim();
    if (claimed !== fileHash) problems.push(`claimed hash ${claimed} != sha256 prefix of log ${fileHash}`);
  }

  // 2. independent recomputation of the baseline log
  const base = run(24576, 8192, 2, null);
  const ref = render(base.events);
  const refHash = crypto.createHash('sha256').update(ref).digest('hex').slice(0, 16);
  notes.push(`recomputed baseline: ${base.events.length} events, hash ${refHash}${base.oomAt !== null ? ', OOM at ' + base.oomAt : ''}`);
  notes.push(`submitted log: ${body.length} events, hash ${fileHash}`);
  if (text !== ref) {
    const rl = ref.split('\n');
    let k = 0; while (k < Math.max(rl.length, lines.length) && rl[k] === lines[k]) k++;
    problems.push(`log differs from recomputation at line ${k + 1}: submitted "${lines[k]}" expected "${rl[k]}"`);
  }

  // 3. sweep rows
  if (opt.sweep) {
    const csv = fs.readFileSync(opt.sweep, 'utf8').trim().split('\n');
    const hdr = csv[0].split(',');
    const rows = csv.slice(1).map(l => { const v = l.split(','); const o = {}; hdr.forEach((h, j) => o[h] = v[j]); return o; });
    if (rows.length !== 96) problems.push(`sweep has ${rows.length} rows, expected 96`);
    const want = opt.rows === 'all' ? rows.map(r => +r.idx) : opt.rows.split(',').map(Number);
    let ok = 0;
    for (const ix of want) {
      const r = rows.find(x => +x.idx === ix);
      if (!r) { problems.push(`sweep row ${ix} missing`); continue; }
      const PT = r.pt === 'off' ? null : +r.pt;
      const res = run(+r.eden, +r.surv, +r.T, PT);
      const exp = res.oomAt !== null
        ? { oom: 'yes', oom_op: String(res.oomAt) }
        : { oom: 'no', minor: res.M.minor, major: res.M.major, copied: res.M.copied, promoted: res.M.promoted,
            pretenured: res.M.pretenured, total_pause: res.M.total, max_pause: res.M.maxp, peak_old: res.M.peak };
      const bad = Object.keys(exp).filter(k => String(exp[k]) !== String(r[k]));
      if (bad.length) problems.push(`sweep row ${ix} (${r.eden}/${r.surv}/T${r.T}/PT${r.pt}) mismatch in ${bad.map(b => `${b}: got ${r[b]} want ${exp[b]}`).join(', ')}`);
      else ok++;
    }
    notes.push(`sweep rows recomputed and matched: ${ok}/${want.length} (${opt.rows === 'all' ? 'all' : want.join(',')})`);
  }

  for (const n of notes) console.log('note: ' + n);
  for (const p of problems.slice(0, 20)) console.log('FAIL: ' + p);
  if (problems.length > 20) console.log(`... ${problems.length - 20} more problems`);
  console.log(problems.length === 0 ? 'VERDICT: ACCEPT' : `VERDICT: REJECT (${problems.length} problem(s))`);
  process.exit(problems.length === 0 ? 0 : 1);
}
main();
