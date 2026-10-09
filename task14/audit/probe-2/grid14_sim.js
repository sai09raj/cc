#!/usr/bin/env node
// GRID-14 step-by-step traffic simulator (Node.js, standard library only).
// Implements the model of grid14_v1.pdf (Sections 1-7, Figures 1-4).
'use strict';
const fs = require('fs');

// ---------------------------------------------------------------- data read from the figures
// Figure 1: street blocks (metres), stop line to stop line.
const H_BLOCKS = [[240, 195], [165, 270], [210, 180]];          // row r: I(r,0)-I(r,1), I(r,1)-I(r,2)
const V_BLOCKS = [[225, 150], [180, 255], [202.5, 157.5]];      // col c: I(0,c)-I(1,c), I(1,c)-I(2,c)
// Figure 1: inbound boundary approaches 'in' (metres), terminals T0..T11.
const IN_LEN_M = [285, 330, 270, 307.5, 262.5, 322.5, 292.5, 277.5, 337.5, 315, 300, 270];
const OUT_CELLS = 10;  // Section 2
const CELL_M = 7.5;
// Figure 2: demand veh/h by terminal T0..T11.
const DEMAND = {
  AM:    [208, 266, 182, 234, 195, 254, 221, 176, 273, 247, 202, 228],
  PM:    [221, 176, 273, 247, 202, 228, 208, 266, 182, 234, 195, 254],
  EVENT: [208, 266, 182, 234, 312, 254, 221, 176, 273, 395, 202, 228],
};
const SCENARIOS = ['AM', 'PM', 'EVENT'];
// Figure 3: turning shares (L, T, R) %, by approach side.
const SHARES_NS = [20, 65, 15];
const SHARES_EW = [10, 75, 15];
// Figure 4: green times A/B/C/D by cycle and plan.
const CYCLES = [60, 72, 84, 96, 108, 120];
const GREENS = {
  60:  [[18, 8, 18, 8], [22, 6, 18, 6], [16, 7, 22, 7], [20, 9, 16, 7], [16, 7, 20, 9], [21, 5, 21, 5]],
  72:  [[22, 10, 22, 10], [27, 8, 22, 7], [20, 9, 27, 8], [25, 11, 20, 8], [20, 8, 25, 11], [26, 6, 26, 6]],
  84:  [[26, 12, 26, 12], [32, 9, 26, 9], [23, 11, 32, 10], [29, 14, 23, 10], [23, 11, 29, 13], [31, 7, 31, 7]],
  96:  [[30, 14, 30, 14], [37, 11, 30, 10], [27, 12, 37, 12], [34, 15, 27, 12], [27, 12, 34, 15], [36, 8, 36, 8]],
  108: [[34, 16, 34, 16], [42, 12, 34, 12], [30, 14, 42, 14], [38, 18, 30, 14], [30, 14, 38, 18], [40, 10, 40, 10]],
  120: [[39, 17, 39, 17], [48, 13, 38, 13], [34, 15, 48, 15], [43, 20, 34, 15], [34, 15, 43, 20], [45, 11, 45, 11]],
};
const ALL_RED = 2;
// Phase order (Figure 3): phases indexed A=0,B=1,C=2,D=3.
const ORDERS = { lead: [0, 1, 2, 3], lag: [1, 0, 3, 2] };

// ---------------------------------------------------------------- network construction
// Sides: N=0, E=1, S=2, W=3. A link "arrives from side s" at its downstream intersection.
const SIDE = ['N', 'E', 'S', 'W'];
function cellsOf(m) { const n = m / CELL_M; if (Math.abs(n - Math.round(n)) > 1e-9) throw new Error('non-integer cells ' + m); return Math.round(n); }

function buildNetwork() {
  const links = []; // {id, name, n, kind:0 inbound,1 block,2 outbound, to:j or -1, from:j or -1, side, term}
  const exitLink = []; // exitLink[j][d] -> link index leaving intersection j on side d
  const inLink = [];   // inLink[k] -> inbound link of terminal k
  for (let j = 0; j < 9; j++) exitLink.push([-1, -1, -1, -1]);
  const rc = (j) => [Math.floor(j / 3), j % 3];
  const idx = (r, c) => r * 3 + c;
  const add = (o) => { o.id = links.length; links.push(o); return o.id; };
  // terminal on side d of intersection j
  function terminalOf(j, d) {
    const [r, c] = rc(j);
    if (d === 0 && r === 0) return c;
    if (d === 1 && c === 2) return 3 + r;
    if (d === 2 && r === 2) return 6 + c;
    if (d === 3 && c === 0) return 9 + r;
    return -1;
  }
  // inbound boundary links
  for (let k = 0; k < 12; k++) {
    let j, d;
    if (k < 3) { j = idx(0, k); d = 0; }
    else if (k < 6) { j = idx(k - 3, 2); d = 1; }
    else if (k < 9) { j = idx(2, k - 6); d = 2; }
    else { j = idx(k - 9, 0); d = 3; }
    inLink[k] = add({ name: `in:T${k}->I${j}`, n: cellsOf(IN_LEN_M[k]), kind: 0, to: j, from: -1, side: d, term: k });
  }
  // street blocks
  for (let r = 0; r < 3; r++) for (let c = 0; c < 2; c++) {
    const a = idx(r, c), b = idx(r, c + 1), n = cellsOf(H_BLOCKS[r][c]);
    exitLink[a][1] = add({ name: `I${a}->I${b}`, n, kind: 1, to: b, from: a, side: 3, term: -1 }); // eastbound arrives at b from W
    exitLink[b][3] = add({ name: `I${b}->I${a}`, n, kind: 1, to: a, from: b, side: 1, term: -1 }); // westbound arrives at a from E
  }
  for (let c = 0; c < 3; c++) for (let r = 0; r < 2; r++) {
    const a = idx(r, c), b = idx(r + 1, c), n = cellsOf(V_BLOCKS[c][r]);
    exitLink[a][2] = add({ name: `I${a}->I${b}`, n, kind: 1, to: b, from: a, side: 0, term: -1 }); // southbound arrives at b from N
    exitLink[b][0] = add({ name: `I${b}->I${a}`, n, kind: 1, to: a, from: b, side: 2, term: -1 }); // northbound arrives at a from S
  }
  // outbound boundary links
  for (let j = 0; j < 9; j++) for (let d = 0; d < 4; d++) {
    if (exitLink[j][d] >= 0) continue;
    const k = terminalOf(j, d);
    exitLink[j][d] = add({ name: `out:I${j}->T${k}`, n: OUT_CELLS, kind: 2, to: -1, from: j, side: -1, term: k });
  }
  let base = 0;
  for (const L of links) { L.base = base; base += L.n; }
  return { links, exitLink, inLink, totalCells: base };
}
const NET = buildNetwork();

// movement m: 0=left,1=through,2=right; arriving from side s
function exitSide(s, m) { return m === 0 ? (s + 1) % 4 : m === 1 ? (s + 2) % 4 : (s + 3) % 4; }
function phaseOf(s, m) { const ns = (s === 0 || s === 2); return ns ? (m === 0 ? 1 : 0) : (m === 0 ? 3 : 2); }

// ---------------------------------------------------------------- 31-bit LCG
function lcg(x) { return ((Math.imul(1103515245, x) + 12345) & 0x7fffffff) >>> 0; }

// ---------------------------------------------------------------- scenario pre-computation (config independent)
// Creation times and routes do not depend on the signal configuration.
function prepareScenario(name) {
  const dem = DEMAND[name];
  const gen = []; for (let k = 0; k < 12; k++) gen.push(1000 + 17 * k);
  const vTerm = [], vBorn = [];
  const createdAt = []; // per step list start index
  const createStart = new Int32Array(3601);
  for (let t = 0; t < 3600; t++) {
    createStart[t] = vTerm.length;
    for (let k = 0; k < 12; k++) {
      gen[k] = lcg(gen[k]);
      if (((gen[k] >>> 8) % 3600) < dem[k]) { vTerm.push(k); vBorn.push(t); }
    }
  }
  createStart[3600] = vTerm.length;
  const V = vTerm.length;
  // routes: sequence of links; for each link that ends at an intersection, the phase needed and movement
  const routeStart = new Int32Array(V + 1);
  const rLink = [], rPhase = [], rMove = [];
  for (let v = 0; v < V; v++) {
    routeStart[v] = rLink.length;
    let y = (Math.imul(2654435761 | 0, v) + 12345) & 0x7fffffff; // (2654435761 v + 12345) mod 2^31
    y = y >>> 0;
    let link = NET.inLink[vTerm[v]];
    for (;;) {
      const L = NET.links[link];
      if (L.kind === 2) { rLink.push(link); rPhase.push(-1); rMove.push(-1); break; }
      y = lcg(y);
      const r = (y >>> 16) % 100;
      const sh = (L.side === 0 || L.side === 2) ? SHARES_NS : SHARES_EW;
      const m = r < sh[0] ? 0 : (r < sh[0] + sh[1] ? 1 : 2);
      rLink.push(link); rPhase.push(phaseOf(L.side, m)); rMove.push(m);
      link = NET.exitLink[L.to][exitSide(L.side, m)];
    }
  }
  routeStart[V] = rLink.length;
  const termQ = []; for (let k = 0; k < 12; k++) termQ.push([]);
  for (let v = 0; v < V; v++) termQ[vTerm[v]].push(v);
  const qStart = new Int32Array(13); const qList = new Int32Array(V); let p = 0;
  for (let k = 0; k < 12; k++) { qStart[k] = p; for (const v of termQ[k]) qList[p++] = v; }
  qStart[12] = p;
  return { name, V, vTerm: Int32Array.from(vTerm), vBorn: Int32Array.from(vBorn), createStart,
    routeStart, rLink: Int32Array.from(rLink), rPhase: Int8Array.from(rPhase), rMove: Int8Array.from(rMove), qStart, qList };
}

// ---------------------------------------------------------------- signal table
function phaseTable(C, plan, order) {
  const g = GREENS[C][plan - 1];
  const tab = new Int8Array(C).fill(-1);
  let t = 0;
  for (const ph of ORDERS[order]) {
    for (let i = 0; i < g[ph]; i++) tab[t + i] = ph;
    t += g[ph] + ALL_RED;
  }
  if (t !== C) throw new Error('timing does not sum to cycle');
  return tab;
}

// ---------------------------------------------------------------- simulation of one scenario run
const NL = NET.links.length;
const LN = new Int32Array(NL), LKIND = new Int8Array(NL), LTO = new Int32Array(NL), LBASE = new Int32Array(NL);
for (const L of NET.links) { LN[L.id] = L.n; LKIND[L.id] = L.kind; LTO[L.id] = L.to; LBASE[L.id] = L.base; }
const INLINK = Int32Array.from(NET.inLink);
// per link ring buffer of vehicle ids (capacity n)
const ringBuf = new Int32Array(NET.totalCells);
const ringHead = new Int32Array(NL), ringCnt = new Int32Array(NL);
const c0 = new Uint8Array(NL);
const pendLink = new Int32Array(64), pendVeh = new Int32Array(64);
function c0now(l) { const cnt = ringCnt[l]; return (cnt > 0 && posRef[ringBuf[LBASE[l] + (ringHead[l] + cnt - 1) % LN[l]]] === 0) ? 1 : 0; }
let posRef = null;

/**
 * Simulate one scenario. cfg = {C, plan, order, offsets[9]}.
 * Returns {tts, gridlock, endStep, vehicles}. If tracer is given it is called per step.
 */
function simulate(sc, cfg, tracer) {
  const C = cfg.C, tab = phaseTable(C, cfg.plan, cfg.order), off = cfg.offsets;
  const V = sc.V, vBorn = sc.vBorn, routeStart = sc.routeStart, rLink = sc.rLink, rPhase = sc.rPhase;
  const pos = new Int32Array(V), ridx = new Int32Array(V);
  posRef = pos;
  const qPtr = new Int32Array(12); for (let k = 0; k < 12; k++) qPtr[k] = sc.qStart[k];
  const qStart = sc.qStart, qList = sc.qList, createStart = sc.createStart;
  ringHead.fill(0); ringCnt.fill(0);
  const green = new Int8Array(9);
  const offm = new Int32Array(9); for (let j = 0; j < 9; j++) offm[j] = ((off[j] % C) + C) % C;
  let created = 0, inNet = 0, departed = 0;
  let tts = 0, endStep = 7199, gridlock = false, frozenAt = -1;
  let lastMove = 0;
  const gone = new Uint8Array(V);
  const qEnd = new Int32Array(12); // number of created vehicles per terminal -> end pointer into qList
  for (let k = 0; k < 12; k++) qEnd[k] = qStart[k];
  const ev = tracer ? { cross: [], depart: [], enter: [], created: [] } : null;
  for (let t = 0; t < 7200; t++) {
    // (1) creation
    if (t < 3600) {
      const a = createStart[t], b = createStart[t + 1];
      for (let v = a; v < b; v++) { qEnd[sc.vTerm[v]]++; if (ev) ev.created.push(v); }
      created = b;
    }
    // signal state
    for (let j = 0; j < 9; j++) { let tau = (t - offm[j]) % C; if (tau < 0) tau += C; green[j] = tab[tau]; }
    // start-of-step occupancy of cell 0 of each link
    for (let l = 0; l < NL; l++) {
      const cnt = ringCnt[l];
      c0[l] = (cnt > 0 && pos[ringBuf[LBASE[l] + (ringHead[l] + cnt - 1) % LN[l]]] === 0) ? 1 : 0;
    }
    let np = 0;
    // (2) movements
    for (let l = 0; l < NL; l++) {
      let cnt = ringCnt[l];
      if (cnt === 0) continue;
      const n = LN[l], base = LBASE[l];
      let h = ringHead[l];
      let prevStart = n; // start position of the vehicle ahead (n = none)
      let i = 0;
      // front vehicle
      const vf = ringBuf[base + h];
      const pf = pos[vf];
      if (pf === n - 1) {
        prevStart = pf;
        if (LKIND[l] === 2) {
          // leaves the network
          tts += t - vBorn[vf] + 1; departed++; inNet--; gone[vf] = 1; lastMove = t;
          if (ev) ev.depart.push(vf);
          h = h + 1 === n ? 0 : h + 1; cnt--; i = 0;
        } else {
          const ri = ridx[vf];
          if (green[LTO[l]] === rPhase[ri] && c0[rLink[ri + 1]] === 0) {
            pendLink[np] = rLink[ri + 1]; pendVeh[np] = vf; np++; lastMove = t;
            if (ev) ev.cross.push([vf, l, rLink[ri + 1]]);
            h = h + 1 === n ? 0 : h + 1; cnt--;
          } else { i = 1; }
        }
      }
      // remaining vehicles (front may already be handled)
      let k = i;
      let hh = h + k; if (hh >= n) hh -= n;
      for (; k < cnt; k++) {
        const v = ringBuf[base + hh];
        const p = pos[v];
        if (p + 1 !== prevStart) { pos[v] = p + 1; lastMove = t; }
        prevStart = p;
        hh++; if (hh === n) hh = 0;
      }
      ringHead[l] = h; ringCnt[l] = cnt;
    }
    // terminal queue heads enter inbound links
    for (let k = 0; k < 12; k++) {
      if (qPtr[k] < qEnd[k] && c0[INLINK[k]] === 0) {
        const v = qList[qPtr[k]++];
        pendLink[np] = INLINK[k]; pendVeh[np] = v; np++;
        ridx[v] = routeStart[v] - 1; // will be incremented below
        inNet++; lastMove = t;
        if (ev) ev.enter.push(v);
      }
    }
    // apply pending entries into cell 0
    for (let q = 0; q < np; q++) {
      const l = pendLink[q], v = pendVeh[q];
      const n = LN[l];
      let slot = ringHead[l] + ringCnt[l]; if (slot >= n) slot -= n;
      ringBuf[LBASE[l] + slot] = v; ringCnt[l]++;
      pos[v] = 0; ridx[v]++;
    }
    if (tracer) { tracer(t, { pos, ridx, rLink, qPtr, qEnd, qStart, qList, created, inNet, departed, ev, green }); ev.cross = []; ev.depart = []; ev.enter = []; ev.created = []; }
    if (t >= 3599) {
      let waiting = 0; for (let k = 0; k < 12; k++) waiting += qEnd[k] - qPtr[k];
      if (waiting === 0 && inNet === 0) { endStep = t; break; }
    }
    // Exact shortcut for a frozen (deadlocked) network: if nothing has moved for C consecutive steps
    // (a full signal cycle, so every movement has had its green) and no new vehicle could ever enter
    // (t >= 3600, or every inbound link's cell 0 is occupied), the state can never change again, so
    // every vehicle not yet departed stays until step 7199. The TTS is then identical to running on.
    if (!tracer && inNet > 0 && t - lastMove >= C) {
      let blocked = t >= 3600;
      if (!blocked) { blocked = true; for (let k = 0; k < 12; k++) if (c0now(INLINK[k]) === 0) { blocked = false; break; } }
      if (blocked) { frozenAt = t; break; }
    }
  }
  if (endStep === 7199) {
    // every vehicle created (now or, for a frozen network, later) that has not left spends 7200 - g
    for (let v = 0; v < V; v++) if (!gone[v]) { tts += 7200 - vBorn[v]; gridlock = true; }
  }
  return { tts, gridlock, endStep, vehicles: V, frozenAt };
}

let SC = null;
function scenarios() { if (!SC) SC = SCENARIOS.map(prepareScenario); return SC; }

function evaluate(cfg) {
  const sc = scenarios();
  const r = sc.map((s) => simulate(s, cfg));
  return { AM: r[0].tts, PM: r[1].tts, EVENT: r[2].tts, total: r[0].tts + r[1].tts + r[2].tts,
    gridlock: r.some((x) => x.gridlock), end: r.map((x) => x.endStep) };
}

// ---------------------------------------------------------------- configuration indexing
// index = ((((ci*6 + plan-1)*2 + order)*4^9) + sum offIdx[j]*4^(8-j)) ; ordering equals the tie-break order
const NOFF = 262144;
function decode(idx) {
  let o = idx % NOFF; let rest = Math.floor(idx / NOFF);
  const ord = rest % 2; rest = Math.floor(rest / 2);
  const plan = rest % 6 + 1; const ci = Math.floor(rest / 6);
  const C = CYCLES[ci];
  const offIdx = new Array(9);
  for (let j = 8; j >= 0; j--) { offIdx[j] = o % 4; o = Math.floor(o / 4); }
  return { C, plan, order: ord ? 'lag' : 'lead', offsets: offIdx.map((q) => q * C / 4), offIdx };
}
function encode(C, plan, order, offIdx) {
  let o = 0; for (let j = 0; j < 9; j++) o = o * 4 + offIdx[j];
  return ((CYCLES.indexOf(C) * 6 + (plan - 1)) * 2 + (order === 'lag' ? 1 : 0)) * NOFF + o;
}

// ---------------------------------------------------------------- trace writer (baseline AM)
function writeTrace(cfg, scenName, file) {
  const sc = scenarios()[SCENARIOS.indexOf(scenName)];
  const out = [];
  out.push(`# GRID-14 trace scenario=${scenName}`);
  out.push(`CONFIG C=${cfg.C} plan=${cfg.plan} order=${cfg.order} offsets=${cfg.offsets.join(',')}`);
  for (const L of NET.links) out.push(`LINK ${L.id} ${L.n} ${['in', 'block', 'out'][L.kind]} from=${L.from} to=${L.to} arrside=${L.side >= 0 ? SIDE[L.side] : '-'} term=${L.term}`);
  const res = simulate(sc, cfg, (t, s) => {
    out.push(`STEP ${t}`);
    for (const v of s.ev.created) out.push(`NEW ${v} T${sc.vTerm[v]}`);
    for (const v of s.ev.depart) out.push(`EXIT ${v}`);
    // positions of every vehicle in the network at the end of the step
    const parts = [];
    for (let l = 0; l < NL; l++) {
      const n = LN[l];
      for (let q = 0; q < ringCnt[l]; q++) { const v = ringBuf[LBASE[l] + (ringHead[l] + q) % n]; parts.push(`${v}:${l}:${s.pos[v]}`); }
    }
    out.push('POS ' + parts.join(' '));
    const w = [];
    for (let k = 0; k < 12; k++) for (let q = s.qPtr[k]; q < s.qEnd[k]; q++) w.push(`${s.qList[q]}`);
    out.push('WAIT ' + w.join(' '));
  });
  out.push(`END endStep=${res.endStep} TTS=${res.tts} gridlock=${res.gridlock}`);
  fs.writeFileSync(file, out.join('\n') + '\n');
  return res;
}

module.exports = { NET, DEMAND, CYCLES, GREENS, ORDERS, prepareScenario, simulate, evaluate, scenarios, decode, encode, NOFF, phaseTable, writeTrace, cellsOf, IN_LEN_M, H_BLOCKS, V_BLOCKS };

// ---------------------------------------------------------------- CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  const get = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
  const cmd = args[0];
  const cfg = { C: +get('C', 84), plan: +get('plan', 1), order: get('order', 'lead'), offsets: get('offsets', '0,0,0,0,0,0,0,0,0').split(',').map(Number) };
  if (cmd === 'run') {
    const t0 = Date.now(); const r = evaluate(cfg);
    console.log(JSON.stringify({ cfg, ...r, ms: Date.now() - t0 }));
  } else if (cmd === 'trace') {
    const r = writeTrace(cfg, get('scenario', 'AM'), get('out', 'trace.txt'));
    console.log(JSON.stringify({ cfg, scenario: get('scenario', 'AM'), ...r }));
  } else if (cmd === 'network') {
    for (const L of NET.links) console.log(L.id, L.name, L.n);
    for (const s of scenarios()) console.log(s.name, 'vehicles', s.V);
  } else {
    console.log('usage: node grid14_sim.js run|trace|network [--C 84 --plan 1 --order lead --offsets 0,0,0,0,0,0,0,0,0] [--scenario AM --out file]');
  }
}
