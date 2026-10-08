"use strict";
// GRID-14 fast engine (JS port of cgrid_fast.c), used to size the configuration space.
const P = require("./params.json");
const NL = 60, RING = 4096;
function lcg(x) { return Number((1103515245n * BigInt(x) + 12345n) & 0x7fffffffn); }
function lcgf(x) { // exact 31-bit LCG without BigInt: split multiply
  const a = 1103515245; const lo = (x & 0xffff) * a; const hi = ((x >>> 16) * a) % 0x80000000;
  return (((hi * 65536) % 0x80000000) + lo + 12345) % 0x80000000;
}
const LK = []; const OUTL = Array.from({length: 9}, () => [0,0,0,0]); const ENTRYL = [];
for (let r = 0; r < 3; r++) for (let c = 0; c < 2; c++) { const L = P.L_EW[r][c], a = 3*r+c, b = a+1;
  LK.push({n: L, kind: 0, to: b, side: 3}); OUTL[a][1] = LK.length-1; LK.push({n: L, kind: 0, to: a, side: 1}); OUTL[b][3] = LK.length-1; }
for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) { const L = P.L_NS[r][c], a = 3*r+c, b = a+3;
  LK.push({n: L, kind: 0, to: b, side: 0}); OUTL[a][2] = LK.length-1; LK.push({n: L, kind: 0, to: a, side: 2}); OUTL[b][0] = LK.length-1; }
for (let k = 0; k < 12; k++) { let j, s; if (k < 3) { j = k; s = 0; } else if (k < 6) { j = 3*(k-3)+2; s = 1; } else if (k < 9) { j = 6+(k-6); s = 2; } else { j = 3*(k-9); s = 3; }
  LK.push({n: P.L_ENTRY[k], kind: 1, to: j, side: s}); ENTRYL.push(LK.length-1); LK.push({n: P.L_EXIT, kind: 2, to: -1, side: -1}); OUTL[j][s] = LK.length-1; }
const Ln = Int32Array.from(LK.map(l => l.n)), Lk = Int32Array.from(LK.map(l => l.kind)), Lto = Int32Array.from(LK.map(l => l.to)), Lside = Int32Array.from(LK.map(l => l.side));
const OUT = Int32Array.from(OUTL.flat());
const MAXV = 20000;
const vgen = new Int32Array(MAXV), vexit = new Int32Array(MAXV), vmv = new Int32Array(MAXV), vstamp = new Int32Array(MAXV), vst = new Int32Array(MAXV), lpos = new Int32Array(MAXV);
const lv = new Int32Array(NL * RING), lfront = new Int32Array(NL), lcount = new Int32Array(NL), head0 = new Uint8Array(NL);
const queue = new Int32Array(12 * MAXV), qh = new Int32Array(12), qt = new Int32Array(12);
const CYC = Object.keys(P.GREEN).map(Number).sort((a, b) => a - b);
const SC = ["AM", "PM", "EVENT"];
function turn(v, side) { const p = (side === 0 || side === 2) ? P.TURN_NS : P.TURN_EW; vst[v] = lcgf(vst[v]); const r = (vst[v] >>> 16) % 100; return r < p[0] ? 0 : (r < p[0] + p[1] ? 1 : 2); }
function run(C, plan, off, lag, sc) {
  const g = P.GREEN[String(C)][plan], ph = new Uint8Array(C), ord = lag ? [1,0,3,2] : [0,1,2,3]; let x = 0;
  for (const p of ord) { for (let t = x; t < x + g[p]; t++) ph[t] = 1 << p; x += g[p] + P.ALL_RED; }
  lfront.fill(0); lcount.fill(0); const D = P.DEMANDS[SC[sc]];
  const ts = new Array(12); for (let k = 0; k < 12; k++) { ts[k] = 1000 + 17*k; qh[k] = 0; qt[k] = 0; }
  let nv = 0, exited = 0, t = 0; const tau = new Int32Array(9);
  for (;;) {
    if (t < P.T_GEN) for (let k = 0; k < 12; k++) { ts[k] = lcgf(ts[k]); if (((ts[k] >>> 8) % 3600) < D[k]) {
      vgen[nv] = t; vexit[nv] = -1; vstamp[nv] = -1; vst[nv] = Number((BigInt(nv) * 2654435761n + 12345n) & 0x7fffffffn); queue[k*MAXV + qt[k]++] = nv; nv++; } }
    for (let l = 0; l < NL; l++) head0[l] = (lcount[l] && lpos[lv[l*RING + ((lfront[l] + lcount[l] - 1) & (RING-1))]] === 0) ? 1 : 0;
    for (let j = 0; j < 9; j++) { let q = (t - off[j]) % C; if (q < 0) q += C; tau[j] = q; }
    for (let l = 0; l < NL; l++) { const cnt = lcount[l]; if (!cnt) continue; const n = Ln[l], f = lfront[l]; let prev = 1 << 30, removed = 0;
      for (let k = 0; k < cnt; k++) { const v = lv[l*RING + ((f + k) & (RING-1))], p = lpos[v];
        if (vstamp[v] === t) { prev = p; continue; }
        if (k === 0 && p === n - 1) {
          if (Lk[l] === 2) { vexit[v] = t; exited++; vstamp[v] = t; removed = 1; }
          else { const j = Lto[l], s = Lside[l], mv = vmv[v]; const d = mv === 1 ? (s+2)&3 : (mv === 2 ? (s+3)&3 : (s+1)&3); const dl = OUT[j*4+d];
            const m = ph[tau[j]], ns = (s === 0 || s === 2); const green = ns ? (mv === 0 ? (m & 2) : (m & 1)) : (mv === 0 ? (m & 8) : (m & 4));
            if (green && !head0[dl]) { removed = 1; vstamp[v] = t; lpos[v] = 0; lv[dl*RING + ((lfront[dl] + lcount[dl]) & (RING-1))] = v; lcount[dl]++; if (Lk[dl] === 0) vmv[v] = turn(v, Lside[dl]); } }
          prev = p;
        } else { if (p + 1 < prev) { lpos[v] = p + 1; vstamp[v] = t; } prev = p; } }
      if (removed) { lfront[l] = (f + 1) & (RING-1); lcount[l]--; } }
    for (let k = 0; k < 12; k++) { const el = ENTRYL[k]; if (qh[k] < qt[k] && !head0[el]) { const v = queue[k*MAXV + qh[k]++]; lpos[v] = 0; vstamp[v] = t; vmv[v] = turn(v, Lside[el]);
      lv[el*RING + ((lfront[el] + lcount[el]) & (RING-1))] = v; lcount[el]++; } }
    t++; if ((t >= P.T_GEN && exited === nv) || t >= P.CAP) break; }
  let tts = 0; for (let v = 0; v < nv; v++) tts += vexit[v] >= 0 ? (vexit[v] - vgen[v] + 1) : (P.CAP - vgen[v]);
  return [tts, nv, exited, t];
}
module.exports = { run, CYC };
if (require.main === module) {
  const a = process.argv.slice(2);
  if (a[0] === "one") { const C = +a[1], plan = +a[2], off = a[3].split(",").map(Number), lag = a[4] === "lag" ? 1 : 0; let tot = 0, s = "";
    for (let sc = 0; sc < 3; sc++) { const r = run(C, plan, off, lag, sc); tot += r[0]; s += r.join(" ") + " | "; } console.log(s + "total " + tot); }
  else { const n = +a[1]; let st = 7, acc = 0; const L = x => lcgf(x);
    for (let i = 0; i < 20; i++) run(84, 0, [0,0,0,0,0,0,0,0,0], 0, 0);
    const t0 = process.hrtime.bigint();
    for (let i = 0; i < n; i++) { st = L(st); const ci = st % CYC.length; st = L(st); const plan = st % 6; const off = [];
      for (let j = 0; j < 9; j++) { st = L(st); off.push(((st >>> 8) % 4) * CYC[ci] / 4); } st = L(st); const lag = st & 1;
      for (let sc = 0; sc < 3; sc++) acc += run(CYC[ci], plan, off, lag, sc)[0]; }
    console.log((Number(process.hrtime.bigint() - t0) / 1e6 / n).toFixed(2), "ms per config, acc", acc); }
}
