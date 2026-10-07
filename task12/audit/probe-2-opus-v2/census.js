'use strict';
// Exhaustive census of whole cells: every line map 0..65535 for the given placement and (Q,B) list.
// Usage: node census.js <d0> <d1> <QBlist e.g. 4:1,4:2> <worker> <nworkers> <out.csv>
// Worker w simulates maps m with m % nworkers == w. Output CSV: d0,d1,map,Q,B,makespan,messages,nacks
const fs = require('fs');
const { simulate } = require('./sim.js');
const [d0, d1] = [+process.argv[2], +process.argv[3]];
const qbs = process.argv[4].split(',').map(s => s.split(':').map(Number));
const w = +process.argv[5], W = +process.argv[6], out = process.argv[7];
const t0 = Date.now(); let n = 0;
for (const [Q, B] of qbs) {
  const buf = [];
  for (let m = w; m < 65536; m += W) {
    const r = simulate(d0, d1, m, Q, B, null);
    buf.push(`${d0},${d1},${m},${Q},${B},${r.makespan},${r.messages},${r.nacks}\n`); n++;
    if (buf.length >= 2000) { fs.appendFileSync(out, buf.join('')); buf.length = 0; }
  }
  fs.appendFileSync(out, buf.join(''));
}
console.log(`census ${d0}-${d1} worker ${w}: ${n} runs, ${((Date.now() - t0) / n).toFixed(3)} ms/run`);
