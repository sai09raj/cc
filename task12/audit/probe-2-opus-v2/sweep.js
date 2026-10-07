'use strict';
// Stratified sampling sweep of the configuration space.
// The space is split into 448 cells = 28 placements x 4 Q x 4 B; each cell holds 65,536 line maps.
// Round i simulates, in every cell, the i-th map of a fixed keyed pseudo-random permutation
// of 0..65535 for that cell (a 4-round Feistel network), so each cell's sample is a
// sample without replacement, and all cells get the same number of samples.
// Worker w of W handles rounds i = w, w+W, w+2W, ...  Runs until a stop time.
// Usage: node sweep.js <worker> <nworkers> <outfile.csv> <stopEpochSeconds>
// Output CSV: d0,d1,map,Q,B,round,makespan,messages,nacks
const fs = require('fs');
const { simulate } = require('./sim.js');

const PAIRS = [];
for (let a = 0; a < 8; a++) for (let b = a + 1; b < 8; b++) PAIRS.push([a, b]);
const QS = [1, 2, 3, 4], BS = [1, 2, 4, 8];

function mix32(x) { x = Math.imul(x ^ (x >>> 16), 0x7feb352d); x = Math.imul(x ^ (x >>> 15), 0x846ca68b); return (x ^ (x >>> 16)) >>> 0; }
// keyed permutation of 16-bit values (Feistel, 8-bit halves)
function perm16(i, key) {
  let L = (i >>> 8) & 255, R = i & 255;
  for (let r = 0; r < 4; r++) { const F = mix32((R + 1) * 0x9e3779b1 ^ mix32(key * 4 + r)) & 255; const nL = R; R = L ^ F; L = nL; }
  return (L << 8) | R;
}
function cellMap(cell, i) { return perm16(i, 0x51ed270b ^ cell); }

module.exports = { PAIRS, QS, BS, cellMap, perm16 };

if (require.main === module) {
  const w = +process.argv[2], W = +process.argv[3], out = process.argv[4], stop = +process.argv[5];
  // resume: find last completed round for this worker
  let startRound = w;
  if (fs.existsSync(out)) {
    const lines = fs.readFileSync(out, 'utf8').trim().split('\n').filter(Boolean);
    const counts = {};
    for (const l of lines) { const r = +l.split(',')[5]; counts[r] = (counts[r] || 0) + 1; }
    // keep only complete rounds
    const complete = Object.keys(counts).map(Number).filter(r => counts[r] === 448);
    const keep = new Set(complete);
    fs.writeFileSync(out, lines.filter(l => keep.has(+l.split(',')[5])).map(l => l + '\n').join(''));
    if (complete.length) startRound = Math.max(...complete) + W;
  }
  const t0 = Date.now(); let n = 0;
  for (let i = startRound; Date.now() / 1000 < stop && i < 65536; i += W) {
    const buf = [];
    for (let p = 0; p < 28; p++) for (let qi = 0; qi < 4; qi++) for (let bi = 0; bi < 4; bi++) {
      const cell = p * 16 + qi * 4 + bi;
      const map = cellMap(cell, i);
      const r = simulate(PAIRS[p][0], PAIRS[p][1], map, QS[qi], BS[bi], null);
      buf.push(`${PAIRS[p][0]},${PAIRS[p][1]},${map},${QS[qi]},${BS[bi]},${i},${r.makespan},${r.messages},${r.nacks}\n`);
      n++;
    }
    fs.appendFileSync(out, buf.join(''));
  }
  console.log(`worker ${w}: ${n} runs in ${(Date.now() - t0) / 1000}s, ${((Date.now() - t0) / n).toFixed(3)} ms/run`);
}
