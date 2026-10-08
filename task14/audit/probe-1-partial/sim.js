'use strict';
// GRID-14 step-by-step cell simulator (Node.js, standard library only).
// Implements Sections 2-7 of grid14_v1.pdf exactly as read from its text and Figures 1-4.
//
// Usage:
//   node sim.js baseline                      -> AM/PM/EVENT/total TTS of the baseline
//   node sim.js variants                      -> baseline + the three requested variants
//   node sim.js eval C plan lead|lag o0 ... o8  (offsets as multiples k=0..3 of C/4)
//   node sim.js trace <file>                  -> baseline AM run with full step trace
//   node sim.js inputs                        -> prints all values read from the figures

// ---------------------------------------------------------------- values read from the figures
// Figure 1 (metres). Cells = metres / 7.5.
const M = 7.5;
// horizontal street blocks, row r, between column c and c+1 (I(3r+c) -- I(3r+c+1))
const H_BLOCK_M = [[240, 195], [165, 270], [210, 180]];
// vertical street blocks, column c, between row r and r+1 (I(3r+c) -- I(3r+3+c))
const V_BLOCK_M = [[225, 180, 202.5], [150, 255, 157.5]]; // [r][c]
// inbound boundary links ('in' labels), terminal T0..T11
const IN_M = [285, 330, 270, 307.5, 262.5, 322.5, 292.5, 277.5, 337.5, 315, 300, 270];
const OUT_CELLS = 10;
// Figure 2: demand (veh/h) per terminal T0..T11
const DEMAND = {
  AM:    [208, 266, 182, 234, 195, 254, 221, 176, 273, 247, 202, 228],
  PM:    [221, 176, 273, 247, 202, 228, 208, 266, 182, 234, 195, 254],
  EVENT: [208, 266, 182, 234, 312, 254, 221, 176, 273, 395, 202, 228],
};
const SCEN = ['AM', 'PM', 'EVENT'];
// Figure 3: turning shares (L, T, R) %, by approach; phase content and sequences
const SHARES_NS = [20, 65, 15];
const SHARES_EW = [10, 75, 15];
const ORDERS = { lead: [0, 1, 2, 3], lag: [1, 0, 3, 2] }; // phases A=0,B=1,C=2,D=3
// Figure 4: green seconds (A/B/C/D) by cycle and plan 1..6
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

// ---------------------------------------------------------------- network
// sides: N=0, E=1, S=2, W=3 ; approach side a = side the vehicle arrives from
// movement: L=0, T=1, R=2 ; exit side: L=(a+1)%4, T=(a+2)%4, R=(a+3)%4
const EXIT = (a, m) => (a + [1, 2, 3][m]) % 4;
const cells = (m) => {
  const n = m / M;
  if (Math.abs(n - Math.round(n)) > 1e-9) throw new Error('length not a multiple of 7.5 m: ' + m);
  return Math.round(n);
};

function buildNetwork() {
  const links = []; // {len, endJ (-1 = outbound to terminal), approach, kind, name}
  const inLink = [...Array(9)].map(() => [-1, -1, -1, -1]); // [j][a]
  const outLink = [...Array(9)].map(() => [-1, -1, -1, -1]); // [j][side]
  const termIn = Array(12).fill(-1);
  const add = (o) => { links.push(o); return links.length - 1; };
  // boundary terminals
  const termOf = (j, side) => {
    const r = Math.floor(j / 3), c = j % 3;
    if (side === 0 && r === 0) return c;
    if (side === 1 && c === 2) return 3 + r;
    if (side === 2 && r === 2) return 6 + c;
    if (side === 3 && c === 0) return 9 + r;
    return -1;
  };
  const SN = 'NESW';
  for (let j = 0; j < 9; j++) {
    for (let s = 0; s < 4; s++) {
      const k = termOf(j, s);
      if (k >= 0) {
        const li = add({ len: cells(IN_M[k]), endJ: j, approach: s, kind: 'in', name: `T${k}->I${j}` });
        inLink[j][s] = li; termIn[k] = li;
        const lo = add({ len: OUT_CELLS, endJ: -1, approach: -1, kind: 'out', name: `I${j}->T${k}` });
        outLink[j][s] = lo;
      }
    }
  }
  // street blocks, both directions
  for (let r = 0; r < 3; r++) for (let c = 0; c < 2; c++) {
    const a = 3 * r + c, b = a + 1, n = cells(H_BLOCK_M[r][c]);
    let l = add({ len: n, endJ: b, approach: 3, kind: 'block', name: `I${a}->I${b}` }); // eastbound arrives at b from W
    outLink[a][1] = l; inLink[b][3] = l;
    l = add({ len: n, endJ: a, approach: 1, kind: 'block', name: `I${b}->I${a}` }); // westbound arrives at a from E
    outLink[b][3] = l; inLink[a][1] = l;
  }
  for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) {
    const a = 3 * r + c, b = a + 3, n = cells(V_BLOCK_M[r][c]);
    let l = add({ len: n, endJ: b, approach: 0, kind: 'block', name: `I${a}->I${b}` }); // southbound arrives at b from N
    outLink[a][2] = l; inLink[b][0] = l;
    l = add({ len: n, endJ: a, approach: 2, kind: 'block', name: `I${b}->I${a}` }); // northbound arrives at a from S
    outLink[b][0] = l; inLink[a][2] = l;
  }
  for (let j = 0; j < 9; j++) for (let s = 0; s < 4; s++) {
    if (inLink[j][s] < 0 || outLink[j][s] < 0) throw new Error('network incomplete');
  }
  return { links, inLink, outLink, termIn, SN };
}
const NET = buildNetwork();

// ---------------------------------------------------------------- generators
const lcg = (x) => (Math.imul(1103515245, x) + 12345) & 0x7fffffff; // mod 2^31
const vehSeed = (v) => (Math.imul(2654435761 | 0, v) + 12345) & 0x7fffffff;

// Creation times, terminals and routes do not depend on the signal configuration
// (terminal generators advance every step t<3600 regardless; a vehicle's generator advances
// once per link-ending-at-intersection it enters, and its sequence of such links is fixed by
// its own choices). They are therefore precomputed once per scenario.
function makeScenario(name) {
  const dem = DEMAND[name];
  const x = []; for (let k = 0; k < 12; k++) x.push(1000 + 17 * k);
  const gen = [], term = [];
  for (let t = 0; t < 3600; t++) {
    for (let k = 0; k < 12; k++) {
      x[k] = lcg(x[k]);
      if (((x[k] >>> 8) % 3600) < dem[k]) { gen.push(t); term.push(k); }
    }
  }
  const nV = gen.length;
  // routes: flat arrays of link ids and movements (movement at the end of that link, -1 for outbound)
  const routeStart = new Int32Array(nV + 1);
  const rl = [], rm = [];
  const L = NET.links;
  for (let v = 0; v < nV; v++) {
    routeStart[v] = rl.length;
    let y = vehSeed(v);
    let l = NET.termIn[term[v]];
    for (;;) {
      const lk = L[l];
      if (lk.endJ < 0) { rl.push(l); rm.push(-1); break; }
      y = lcg(y);
      const r = (y >>> 16) % 100;
      const sh = (lk.approach === 0 || lk.approach === 2) ? SHARES_NS : SHARES_EW;
      const m = r < sh[0] ? 0 : (r < sh[0] + sh[1] ? 1 : 2);
      rl.push(l); rm.push(m);
      l = NET.outLink[lk.endJ][EXIT(lk.approach, m)];
      if (rl.length - routeStart[v] > 100000) throw new Error('route too long');
    }
  }
  routeStart[nV] = rl.length;
  return { name, nV, gen: Int32Array.from(gen), term: Int32Array.from(term), routeStart,
    routeLink: Int32Array.from(rl), routeMov: Int8Array.from(rm) };
}

// ---------------------------------------------------------------- signals
// phase served sets: A: N/S approaches T,R ; B: N/S L ; C: E/W T,R ; D: E/W L
function serves(phase, a, m) {
  const ns = (a === 0 || a === 2);
  if (phase === 0) return ns && m !== 0;
  if (phase === 1) return ns && m === 0;
  if (phase === 2) return !ns && m !== 0;
  if (phase === 3) return !ns && m === 0;
  return false;
}
// table[tau] = phase index 0..3 green at local time tau, or -1 (all-red)
function phaseTable(C, plan, order) {
  const g = GREENS[C][plan - 1];
  const tab = new Int8Array(C).fill(-1);
  let tau = 0;
  for (const p of ORDERS[order]) {
    for (let i = 0; i < g[p]; i++) tab[tau++] = p;
    tau += ALL_RED;
  }
  if (tau !== C) throw new Error(`greens + all-red != C for C=${C} plan=${plan}`);
  return tab;
}

// ---------------------------------------------------------------- simulation
const NL = NET.links.length;
const LEN = Int32Array.from(NET.links.map((l) => l.len));
const ENDJ = Int32Array.from(NET.links.map((l) => l.endJ));
const APP = Int32Array.from(NET.links.map((l) => l.approach));
const BUFOFF = new Int32Array(NL + 1);
for (let i = 0; i < NL; i++) BUFOFF[i + 1] = BUFOFF[i] + LEN[i];
const TOTAL_CELLS = BUFOFF[NL];
// green lookup: SERVE[phase+1][a*3+m]
const SERVE = [];
for (let p = -1; p < 4; p++) { const row = new Uint8Array(12); for (let a = 0; a < 4; a++) for (let m = 0; m < 3; m++) row[a * 3 + m] = serves(p, a, m) ? 1 : 0; SERVE.push(row); }

// cfg: {C, plan, order:'lead'|'lag', offsets:[9 seconds]}
// trace: optional object {write(str)}
function simulate(cfg, sc, trace) {
  const C = cfg.C;
  const tab = phaseTable(C, cfg.plan, cfg.order);
  const offs = cfg.offsets;
  const nV = sc.nV;
  const pos = new Int32Array(nV);
  const ridx = new Int32Array(nV); // index into route arrays of current link
  for (let v = 0; v < nV; v++) ridx[v] = sc.routeStart[v];
  const buf = new Int32Array(TOTAL_CELLS); // per link circular buffer of vehicle ids (front first)
  const head = new Int32Array(NL), cnt = new Int32Array(NL);
  const occ0 = new Uint8Array(NL);
  const pendL = new Int32Array(NL), pendV = new Int32Array(NL);
  const phase = new Int8Array(9);
  const termIn = NET.termIn;
  // terminal queues: vehicles of each terminal in creation order
  const tq = [...Array(12)].map(() => []);
  for (let v = 0; v < nV; v++) tq[sc.term[v]].push(v);
  const tqArr = tq.map((a) => Int32Array.from(a));
  const tqHead = new Int32Array(12);
  let created = 0, entered = 0, departed = 0, inNet = 0;
  let tts = 0;
  let endStep = -1;
  const gen = sc.gen, routeLink = sc.routeLink, routeMov = sc.routeMov;
  const tr = trace || null;
  if (tr) {
    tr.write(`# GRID-14 trace v1 scenario=${sc.name} C=${C} plan=${cfg.plan} order=${cfg.order} offsets=${offs.join(',')}\n`);
    tr.write('# LINK id name len endJ approach(N0E1S2W3,-1=outbound)\n');
    for (let l = 0; l < NL; l++) tr.write(`LINK ${l} ${NET.links[l].name} ${LEN[l]} ${ENDJ[l]} ${APP[l]}\n`);
    tr.write('# per step: G t v term (created) | X t v fromLink toLink J approach mov(L0,T1,R2) (stop-line crossing) | O t v link (left network) | E t v term link (entered inbound link) | P t v:link:cell ... (end-of-step positions) | N t created waiting innet departed\n');
  }
  for (let t = 0; t < 7200; t++) {
    // (1) creation (precomputed, identical to generator procedure)
    while (created < nV && gen[created] === t) { if (tr) tr.write(`G ${t} ${created} ${sc.term[created]}\n`); created++; }
    // (2) movements decided on start-of-step occupancy
    for (let j = 0; j < 9; j++) { let tau = (t - offs[j]) % C; if (tau < 0) tau += C; phase[j] = tab[tau]; }
    for (let l = 0; l < NL; l++) occ0[l] = (cnt[l] > 0 && pos[buf[BUFOFF[l] + ((head[l] + cnt[l] - 1) % LEN[l])]] === 0) ? 1 : 0;
    let np = 0;
    for (let l = 0; l < NL; l++) {
      let c = cnt[l];
      if (c === 0) continue;
      const n = LEN[l], off = BUFOFF[l];
      let h = head[l];
      // front vehicle
      let v = buf[off + h];
      let p = pos[v];
      let prevStart; // start-of-step position of the vehicle ahead
      let removed = 0;
      if (p < n - 1) { pos[v] = p + 1; prevStart = p; }
      else {
        prevStart = p;
        if (ENDJ[l] < 0) { // leaves the network
          departed++; inNet--; tts += t - gen[v] + 1; removed = 1;
          if (tr) tr.write(`O ${t} ${v} ${l}\n`);
        } else {
          const ri = ridx[v];
          const m = routeMov[ri];
          const ph = phase[ENDJ[l]];
          if (SERVE[ph + 1][APP[l] * 3 + m]) {
            const to = routeLink[ri + 1];
            if (!occ0[to]) {
              removed = 1; ridx[v] = ri + 1;
              pendL[np] = to; pendV[np] = v; np++;
              if (tr) tr.write(`X ${t} ${v} ${l} ${to} ${ENDJ[l]} ${APP[l]} ${m}\n`);
            }
          }
        }
      }
      // followers
      for (let i = 1; i < c; i++) {
        const w = buf[off + ((h + i) % n)];
        const q = pos[w];
        if (prevStart > q + 1) pos[w] = q + 1;
        prevStart = q;
      }
      if (removed) { head[l] = (h + 1) % n; cnt[l] = c - 1; }
    }
    // terminal queues -> cell 0 of inbound link
    for (let k = 0; k < 12; k++) {
      const qh = tqHead[k];
      const qa = tqArr[k];
      if (qh < qa.length && qa[qh] < created) {
        const l = termIn[k];
        if (!occ0[l]) {
          const v = qa[qh]; tqHead[k] = qh + 1; entered++; inNet++;
          pendL[np] = l; pendV[np] = v; np++;
          if (tr) tr.write(`E ${t} ${v} ${k} ${l}\n`);
        }
      }
    }
    for (let i = 0; i < np; i++) {
      const l = pendL[i], v = pendV[i];
      const n = LEN[l];
      buf[BUFOFF[l] + ((head[l] + cnt[l]) % n)] = v; cnt[l]++;
      pos[v] = 0;
    }
    if (tr) {
      let s = `P ${t}`;
      for (let l = 0; l < NL; l++) { const n = LEN[l]; for (let i = 0; i < cnt[l]; i++) { const v = buf[BUFOFF[l] + ((head[l] + i) % n)]; s += ` ${v}:${l}:${pos[v]}`; } }
      tr.write(s + '\n');
      tr.write(`N ${t} ${created} ${created - entered} ${inNet} ${departed}\n`);
    }
    if (t + 1 >= 3600 && created === nV && entered === nV && inNet === 0) { endStep = t; break; }
  }
  let gridlock = false;
  if (endStep < 0) {
    endStep = 7199;
    // everyone not departed spends 7200 - g
    const left = nV - departed;
    if (left > 0) gridlock = true;
    // sum over not-departed vehicles: need their g; departed tracked via tts already
    // recompute: total over all = sum_departed(e-g+1) + sum_rest(7200-g)
    const gone = new Uint8Array(nV);
    // mark departed by walking positions: vehicles still waiting or in network
    for (let k = 0; k < 12; k++) for (let i = tqHead[k]; i < tqArr[k].length; i++) gone[tqArr[k][i]] = 1;
    for (let l = 0; l < NL; l++) for (let i = 0; i < cnt[l]; i++) gone[buf[BUFOFF[l] + ((head[l] + i) % LEN[l])]] = 1;
    for (let v = 0; v < nV; v++) if (gone[v]) tts += 7200 - gen[v];
  }
  if (tr) tr.write(`# END endStep=${endStep} TTS=${tts} vehicles=${nV} gridlock=${gridlock}\n`);
  return { tts, gridlock, endStep, nV };
}

let SCENARIOS = null;
function scenarios() { if (!SCENARIOS) SCENARIOS = SCEN.map(makeScenario); return SCENARIOS; }

function evalConfig(cfg) {
  const sc = scenarios();
  const r = sc.map((s) => simulate(cfg, s));
  return { AM: r[0].tts, PM: r[1].tts, EVENT: r[2].tts, total: r[0].tts + r[1].tts + r[2].tts,
    gridlock: r.some((x) => x.gridlock), end: r.map((x) => x.endStep) };
}

const BASELINE = { C: 84, plan: 1, order: 'lead', offsets: [0, 0, 0, 0, 0, 0, 0, 0, 0] };

module.exports = { NET, DEMAND, CYCLES, GREENS, ORDERS, H_BLOCK_M, V_BLOCK_M, IN_M, cells, makeScenario,
  simulate, evalConfig, scenarios, phaseTable, BASELINE, SHARES_NS, SHARES_EW };

if (require.main === module) {
  const cmd = process.argv[2] || 'baseline';
  const show = (label, cfg) => {
    const t0 = Date.now();
    const r = evalConfig(cfg);
    console.log(`${label}: AM=${r.AM} PM=${r.PM} EVENT=${r.EVENT} total=${r.total} gridlock=${r.gridlock} endSteps=${r.end.join('/')} (${Date.now() - t0} ms)`);
    return r;
  };
  if (cmd === 'inputs') {
    console.log('Figure 1 street blocks (each is two links, one per direction, same length):');
    for (let r = 0; r < 3; r++) for (let c = 0; c < 2; c++) console.log(`   I${3 * r + c}-I${3 * r + c + 1}  ${H_BLOCK_M[r][c]} m = ${cells(H_BLOCK_M[r][c])} cells`);
    for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) console.log(`   I${3 * r + c}-I${3 * r + c + 3}  ${V_BLOCK_M[r][c]} m = ${cells(V_BLOCK_M[r][c])} cells`);
    console.log('Figure 1 inbound boundary links (terminal -> stop line):');
    for (let k = 0; k < 12; k++) { const l = NET.links[NET.termIn[k]]; console.log(`   ${l.name.padEnd(8)} ${IN_M[k]} m = ${l.len} cells`); }
    console.log(`Outbound boundary links: ${OUT_CELLS} cells each (text). Total cells in network: ${TOTAL_CELLS} on ${NL} links.`);
    console.log('Figure 2 demand (veh/h), T0..T11:');
    for (const s of SCEN) console.log(`   ${s.padEnd(5)} ${DEMAND[s].join(' ')}  (sum ${DEMAND[s].reduce((a, b) => a + b)})`);
    console.log(`Figure 3 turning shares L/T/R %: arrivals from north or south ${SHARES_NS.join('/')}, from west or east ${SHARES_EW.join('/')}`);
    console.log('Figure 3 phases: A = N+S approaches through+right, B = N+S left, C = E+W through+right, D = E+W left; lead = A B C D, lag = B A D C; each green followed by 2 s all-red');
    console.log('Figure 4 greens A/B/C/D (s):');
    for (const C of CYCLES) console.log(`   C=${String(C).padEnd(3)} ` + GREENS[C].map((g, i) => `plan ${i + 1}: ${g.join('/')}`).join('  '));
    for (const s of scenarios()) {
      const lens = []; for (let v = 0; v < s.nV; v++) lens.push(s.routeStart[v + 1] - s.routeStart[v]);
      console.log(`scenario ${s.name}: vehicles=${s.nV}, mean links/route=${(lens.reduce((a, b) => a + b) / s.nV).toFixed(3)}, max=${Math.max(...lens)}`);
    }
  } else if (cmd === 'baseline') {
    show('baseline', BASELINE);
  } else if (cmd === 'variants') {
    show('baseline (C84 plan1 lead offsets 0)', BASELINE);
    show('variant offsets 0/21/42 by column', { ...BASELINE, offsets: [0, 21, 42, 0, 21, 42, 0, 21, 42] });
    show('variant lag', { ...BASELINE, order: 'lag' });
    show('variant C=60', { ...BASELINE, C: 60 });
  } else if (cmd === 'eval') {
    const C = +process.argv[3], plan = +process.argv[4], order = process.argv[5];
    const ks = process.argv.slice(6, 15).map(Number);
    show(`C=${C} plan=${plan} ${order} k=${ks.join('')}`, { C, plan, order, offsets: ks.map((k) => k * C / 4) });
  } else if (cmd === 'trace') {
    const fs = require('fs');
    const file = process.argv[3] || 'trace_baseline_AM.txt';
    const fd = fs.openSync(file, 'w');
    let chunk = [];
    let size = 0;
    const w = { write(s) { chunk.push(s); size += s.length; if (size > 1 << 20) { fs.writeSync(fd, chunk.join('')); chunk = []; size = 0; } } };
    const r = simulate(BASELINE, scenarios()[0], w);
    fs.writeSync(fd, chunk.join('')); fs.closeSync(fd);
    console.log(`trace written to ${file}: AM TTS=${r.tts} endStep=${r.endStep} vehicles=${r.nV}`);
  } else {
    console.error('unknown command'); process.exit(1);
  }
}
