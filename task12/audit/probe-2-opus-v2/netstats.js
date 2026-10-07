'use strict';
// Zero-load XY-route latency from every core to every candidate directory node and back
// (link latencies from Figure 2; +1 cycle per hop for the router's leave-next-cycle rule).
const { LINK_LAT } = require('./sim.js');
const lat = {}; for (const k of Object.keys(LINK_LAT)) { const [a, b] = k.split('-').map(Number); lat[a + '>' + b] = lat[b + '>' + a] = LINK_LAT[k]; }
function route(s, d) { let c = s, t = 0, hops = 0; while (c !== d) { const cr = c >> 2, cc = c & 3, dr = d >> 2, dc = d & 3; const n = cc !== dc ? cr * 4 + cc + (dc > cc ? 1 : -1) : (dr > cr ? cr + 1 : cr - 1) * 4 + cc; t += lat[c + '>' + n] + 1; hops++; c = n; } return c === s ? 1 : t; }
const rows = [];
for (let n = 0; n < 8; n++) { let s = 0; const per = []; for (let c = 0; c < 8; c++) { const rt = route(c, n) + route(n, c); per.push(rt); s += rt; } rows.push({ node: 'N' + n, meanRoundTrip: s / 8, perCore: per.join(' ') }); }
console.table(rows);
