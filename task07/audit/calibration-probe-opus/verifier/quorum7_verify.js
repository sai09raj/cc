#!/usr/bin/env node
// QUORUM-7 independent verifier (JavaScript; shares only ../constants.json with the Python engine).
//
// 1. Re-derives all 15 runs with its own, separately written simulator.
// 2. Checks election safety, log matching, leader completeness (+ committed-entry
//    immutability and the real-vote term rule) on every tick of its own traces.
// 3. Checks the engine's certificates (per-tick snapshots + event log) both by rule
//    (no reference to the re-derivation) and by exact comparison with the re-derivation.
// 4. Applies the two required adversarial mutations to the baseline certificate and
//    confirms both are rejected while the original is accepted.
//
// Usage: node verifier/quorum7_verify.js [--engine-out out] [--report out/verifier_report.json]
'use strict';
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const crypto = require('crypto');

const argv = process.argv.slice(2);
function opt(name, dflt) { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : dflt; }
const ROOT = path.join(__dirname, '..');
const C = JSON.parse(fs.readFileSync(path.join(ROOT, 'constants.json'), 'utf8'));
const ENGINE_OUT = opt('--engine-out', path.join(ROOT, 'out'));
const REPORT = opt('--report', path.join(ENGINE_OUT, 'verifier_report.json'));

const ORDER = {};
C.class_priority.forEach((c, i) => { ORDER[c] = i; });
const NN = C.num_nodes;
const QUORUM = C.majority;

// ---------------------------------------------------------------------------
// Independent re-derivation
// ---------------------------------------------------------------------------
function commandTicks(T) {
  const s = C.client_schedule_ASSUMED; const m = new Map(); let id = 1;
  if (s.every > 0) for (let t = s.first_tick; t <= Math.min(s.last_tick, T - 1); t += s.every) m.set(t, id++);
  return m;
}

function derive(setting, scenario, anchor, crashed) {
  const T = C.run_ticks;
  const base = C.base_timeout[setting];
  const cmds = commandTicks(T);
  let win = null, side = null, rules = [];
  if (scenario !== 'CLEAN') {
    const w = C.fault_windows_rel_anchor[scenario];
    win = [anchor + w.start, anchor + w.end];
    if (w.sides) { side = new Array(NN); w.sides.forEach((grp, k) => grp.forEach(n => { side[n] = k; })); }
    if (scenario === 'MESSAGE_LOSS') rules = C.message_loss_overrides_ASSUMED;
  }
  const inWin = t => win !== null && t >= win[0] && t < win[1];
  const down = (n, t) => scenario === 'CRASH_RECOVER' && n === crashed && inWin(t);

  // node state as parallel arrays
  const S = [];
  for (let n = 0; n < NN; n++) S.push({
    term: 0, vote: -1, log: [], commit: 0,
    role: 'F', since: 0, round: -1, pv: new Set(), rv: new Set(),
    nxt: [], mat: [], hb: [], to: base + C.timeout_stagger_per_node_id * n,
  });
  const queue = new Map(); // tick -> array of messages
  let seq = 0, sent = 0;
  const leaders = []; const votes = []; const snaps = []; const logsPerTick = [];
  let prevotes = 0;

  function post(t, from, to, kind, data) {
    sent++;
    let when = [t + C.base_delivery_delay];
    if (rules.length && inWin(t)) {
      for (const r of rules) {
        if (r.class !== kind) continue;
        if (r.to !== undefined && r.to !== to) continue;
        if (r.from !== undefined && r.from !== from) continue;
        if (r.action === 'DROP') when = [];
        else if (r.action === 'DUPLICATE') when = when.concat(when.map(x => x + r.extra_copy_delay));
        else if (r.action === 'DELAY') when = when.map(x => x + r.extra_delay);
      }
    }
    for (const d of when) {
      if (side && side[from] !== side[to] && (inWin(t) || inWin(d))) continue;
      if (!queue.has(d)) queue.set(d, []);
      queue.get(d).push({ kind, from, to, d, seq: seq++, data });
    }
  }
  const lastTerm = s => (s.log.length ? s.log[s.log.length - 1][0] : 0);
  const okLog = (s, llt, lli) => llt > lastTerm(s) || (llt === lastTerm(s) && lli >= s.log.length);
  const tAt = (s, i) => (i === 0 ? 0 : (i <= s.log.length ? s.log[i - 1][0] : null));

  function ae(t, n, j) {
    const s = S[n]; const p = s.nxt[j] - 1;
    post(t, n, j, 'APPEND_REQ', { term: s.term, p, pt: tAt(s, p), ents: s.log.slice(p, p + C.batch_k).map(e => e.slice()), lc: s.commit });
    s.hb[j] = t;
  }
  function higher(t, n, term) { // adopt strictly higher term
    const s = S[n];
    if (s.role === 'L') { s.since = t; s.nxt = []; s.mat = []; s.hb = []; }
    s.term = term; s.vote = -1; s.role = 'F'; s.round = -1; s.pv = new Set(); s.rv = new Set();
  }
  function preVote(t, n) {
    const s = S[n]; prevotes++;
    s.role = 'P'; s.since = t; s.round = t; s.pv = new Set([n]); s.rv = new Set();
    for (let j = 0; j < NN; j++) if (j !== n) post(t, n, j, 'PREVOTE_REQ', { term: s.term + 1, lli: s.log.length, llt: lastTerm(s), round: t });
  }
  function realVote(t, n) {
    const s = S[n];
    s.term += 1; s.vote = n; s.role = 'C'; s.since = t; s.round = -1; s.pv = new Set(); s.rv = new Set([n]);
    for (let j = 0; j < NN; j++) if (j !== n) post(t, n, j, 'VOTE_REQ', { term: s.term, lli: s.log.length, llt: lastTerm(s) });
  }
  function lead(t, n) {
    const s = S[n];
    s.role = 'L'; s.rv = new Set(); s.nxt = []; s.mat = []; s.hb = [];
    for (let j = 0; j < NN; j++) if (j !== n) { s.nxt[j] = s.log.length + 1; s.mat[j] = 0; }
    leaders.push([t, n, s.term]);
    for (let j = 0; j < NN; j++) if (j !== n) ae(t, n, j);
  }
  function recv(t, n, m) {
    const s = S[n]; const x = m.data;
    switch (m.kind) {
      case 'PREVOTE_REQ':
        post(t, n, m.from, 'PREVOTE_RESP', { round: x.round, ok: okLog(s, x.llt, x.lli) });
        break;
      case 'PREVOTE_RESP':
        if (s.role === 'P' && x.round === s.round && x.ok) { s.pv.add(m.from); if (s.pv.size >= QUORUM) realVote(t, n); }
        break;
      case 'VOTE_REQ': {
        const t0 = s.term, v0 = s.vote;
        if (x.term > s.term) higher(t, n, x.term);
        const yes = x.term >= s.term && (s.vote === -1 || s.vote === m.from) && okLog(s, x.llt, x.lli);
        if (yes) { s.vote = m.from; s.since = t; votes.push([t, n, m.from, x.term, t0, v0]); }
        post(t, n, m.from, 'VOTE_RESP', { term: s.term, ok: yes });
        break;
      }
      case 'VOTE_RESP':
        if (x.term > s.term) higher(t, n, x.term);
        else if (s.role === 'C' && x.term === s.term && x.ok) { s.rv.add(m.from); if (s.rv.size >= QUORUM) lead(t, n); }
        break;
      case 'APPEND_REQ': {
        if (x.term < s.term) { post(t, n, m.from, 'APPEND_RESP', { term: s.term, ok: false, mi: 0 }); break; }
        if (x.term > s.term) higher(t, n, x.term);
        if (s.role === 'L') { s.nxt = []; s.mat = []; s.hb = []; }
        s.role = 'F'; s.round = -1; s.pv = new Set(); s.rv = new Set(); s.since = t;
        if (x.p > 0 && tAt(s, x.p) !== x.pt) { post(t, n, m.from, 'APPEND_RESP', { term: s.term, ok: false, mi: 0 }); break; }
        for (let k = 0; k < x.ents.length; k++) {
          const i = x.p + 1 + k; const have = tAt(s, i);
          if (have !== null && have !== x.ents[k][0]) s.log.length = i - 1;
          if (s.log.length < i) s.log.push(x.ents[k].slice());
        }
        const lastNew = x.p + x.ents.length;
        if (x.lc > s.commit) s.commit = Math.max(s.commit, Math.min(x.lc, lastNew));
        post(t, n, m.from, 'APPEND_RESP', { term: s.term, ok: true, mi: lastNew });
        break;
      }
      case 'APPEND_RESP': {
        if (x.term > s.term) { higher(t, n, x.term); break; }
        if (s.role !== 'L' || x.term !== s.term) break;
        if (x.ok) {
          s.mat[m.from] = x.mi; s.nxt[m.from] = x.mi + 1;
          for (let N = s.log.length; N > s.commit; N--) {
            if (s.log[N - 1][0] !== s.term) continue;
            let c = 1; for (let j = 0; j < NN; j++) if (j !== n && s.mat[j] >= N) c++;
            if (c >= QUORUM) { s.commit = N; break; }
          }
        } else s.nxt[m.from] = Math.max(1, s.nxt[m.from] - 1);
        break;
      }
    }
  }

  for (let t = 0; t < T; t++) {
    const batch = queue.get(t) || []; queue.delete(t);
    for (let n = 0; n < NN; n++) {
      const s = S[n];
      if (down(n, t)) continue;
      if (scenario === 'CRASH_RECOVER' && n === crashed && win && t === win[1]) {
        s.role = 'F'; s.since = t; s.round = -1; s.pv = new Set(); s.rv = new Set(); s.nxt = []; s.mat = []; s.hb = [];
      }
      const mine = batch.filter(m => m.to === n).sort((a, b) => (ORDER[a.kind] - ORDER[b.kind]) || (a.from - b.from) || (a.seq - b.seq));
      for (const m of mine) recv(t, n, m);
      if (cmds.has(t) && s.role === 'L') {
        s.log.push([s.term, cmds.get(t)]);
        for (let j = 0; j < NN; j++) if (j !== n) ae(t, n, j);
      }
      if (s.role === 'L') {
        for (let j = 0; j < NN; j++) if (j !== n && (s.hb[j] === undefined || t - s.hb[j] >= C.heartbeat_interval)) ae(t, n, j);
      } else if (t - s.since >= s.to) preVote(t, n);
    }
    snaps.push(S.map((s, n) => [down(n, t) ? 'X' : s.role, s.term, s.vote, s.commit, s.log.length]));
    logsPerTick.push(S.map(s => s.log.map(e => e.slice())));
  }
  return { setting, scenario, win, crashed, snaps, logsPerTick, leaders, votes, sent, prevotes };
}

// ---------------------------------------------------------------------------
// Safety checks, written against plain per-tick (snapshot, logs) data so they
// can be applied to either the verifier's own derivation or an engine certificate.
// ---------------------------------------------------------------------------
function safety(snaps, logsPerTick, voteEvents, leaderEvents) {
  const bad = [];
  // election safety: per tick and across the whole run (one leader node per term)
  const termOwner = new Map();
  for (let t = 0; t < snaps.length; t++) {
    const seen = new Map();
    snaps[t].forEach((r, n) => {
      if (r[0] !== 'L') return;
      if (seen.has(r[1])) bad.push(`election_safety: t${t} N${seen.get(r[1])} and N${n} both LEADER term ${r[1]}`);
      seen.set(r[1], n);
      if (termOwner.has(r[1]) && termOwner.get(r[1]) !== n) bad.push(`election_safety: term ${r[1]} led by N${termOwner.get(r[1])} and N${n}`);
      termOwner.set(r[1], n);
    });
  }
  // real-vote rule: never grant to a request term below own term; at most one vote per term
  const votedIn = new Map();
  for (const [t, voter, cand, reqTerm, termBefore, voteBefore] of voteEvents) {
    if (reqTerm < termBefore) bad.push(`vote_rule: t${t} N${voter} (term ${termBefore}) granted vote to N${cand} at lower term ${reqTerm}`);
    if (reqTerm === termBefore && voteBefore !== -1 && voteBefore !== cand) bad.push(`vote_rule: t${t} N${voter} double vote in term ${reqTerm}`);
    const k = voter + ':' + reqTerm;
    if (votedIn.has(k) && votedIn.get(k) !== cand) bad.push(`vote_rule: N${voter} voted for two candidates in term ${reqTerm}`);
    votedIn.set(k, cand);
  }
  // log matching, leader completeness, committed-entry immutability
  const committed = []; // index-1 -> [term, cmd]
  const same = (a, b) => a && b && a[0] === b[0] && a[1] === b[1];
  for (let t = 0; t < logsPerTick.length; t++) {
    const L = logsPerTick[t];
    for (let a = 0; a < NN; a++) for (let b = a + 1; b < NN; b++) {
      const la = L[a], lb = L[b]; const m = Math.min(la.length, lb.length);
      let hi = -1; for (let i = m - 1; i >= 0; i--) if (la[i][0] === lb[i][0]) { hi = i; break; }
      for (let i = 0; i <= hi; i++) if (!same(la[i], lb[i])) { bad.push(`log_matching: t${t} N${a}/N${b} agree on term at ${hi + 1} but differ at ${i + 1}`); break; }
    }
    // committed entries must stay in place in every log that held them, and every leader holds them
    if (t > 0) {
      const P = logsPerTick[t - 1];
      for (let n = 0; n < NN; n++) for (let i = 0; i < committed.length; i++) {
        if (same(P[n][i], committed[i]) && !same(L[n][i], committed[i])) bad.push(`committed_overwrite: t${t} N${n} index ${i + 1} ${JSON.stringify(committed[i])} -> ${JSON.stringify(L[n][i] || null)}`);
      }
    }
    for (let n = 0; n < NN; n++) if (snaps[t][n][0] === 'L') {
      for (let i = 0; i < committed.length; i++) if (!same(L[n][i], committed[i])) { bad.push(`leader_completeness: t${t} leader N${n} lacks committed index ${i + 1}`); break; }
    }
    for (let n = 0; n < NN; n++) {
      const c = snaps[t][n][3];
      if (c > L[n].length) bad.push(`commit_beyond_log: t${t} N${n}`);
      for (let i = 0; i < Math.min(c, L[n].length); i++) {
        if (i >= committed.length) committed.push(L[n][i].slice());
        else if (!same(committed[i], L[n][i])) bad.push(`leader_completeness: t${t} N${n} committed ${JSON.stringify(L[n][i])} at ${i + 1} but ${JSON.stringify(committed[i])} already committed there`);
      }
    }
  }
  return { election_safety: !bad.some(b => b.startsWith('election_safety')),
           log_matching: !bad.some(b => b.startsWith('log_matching')),
           leader_completeness: !bad.some(b => /^(leader_completeness|committed_overwrite|commit_beyond_log)/.test(b)),
           vote_rule: !bad.some(b => b.startsWith('vote_rule')),
           violations: bad.slice(0, 20), violation_count: bad.length };
}

function traceHash(setting, scenario, snaps) {
  const lines = [`QUORUM7|${setting}|${scenario}`];
  snaps.forEach((row, t) => lines.push(t + '|' + row.map(r => r[0] + ',' + r[1]).join('|')));
  return { text: lines.join('\n'), sha: crypto.createHash('sha256').update(lines.join('\n'), 'utf8').digest('hex') };
}

// ---------------------------------------------------------------------------
// Engine certificate checking
// ---------------------------------------------------------------------------
function loadCert(file) { return JSON.parse(zlib.gunzipSync(fs.readFileSync(file)).toString('utf8')); }

function replayLogs(cert) {
  const logs = Array.from({ length: NN }, () => []);
  const out = []; let k = 0;
  const ev = cert.events.filter(e => e[0] === 'LOGSET' || e[0] === 'LOGTRUNC');
  for (let t = 0; t < cert.snapshots.length; t++) {
    while (k < ev.length && ev[k][1] === t) {
      const e = ev[k++];
      if (e[0] === 'LOGSET') logs[e[2]][e[3] - 1] = [e[4], e[5]];
      else logs[e[2]].length = e[3];
    }
    out.push(logs.map(l => l.map(x => x.slice())));
  }
  return out;
}

function checkCert(cert, derived) {
  const logs = replayLogs(cert);
  const reasons = [];
  // internal consistency: replayed log length == snapshot loglen
  for (let t = 0; t < logs.length; t++) for (let n = 0; n < NN; n++) {
    if (logs[t][n].length !== cert.snapshots[t][n][4]) { reasons.push(`cert_inconsistent: t${t} N${n} loglen`); t = logs.length; break; }
  }
  const votes = cert.events.filter(e => e[0] === 'VOTE').map(e => e.slice(1));
  const leaders = cert.events.filter(e => e[0] === 'LEADER').map(e => e.slice(1));
  const s = safety(cert.snapshots, logs, votes, leaders);
  reasons.push(...s.violations);
  // exact agreement with independent re-derivation
  let firstDiff = null;
  for (let t = 0; t < derived.snaps.length && firstDiff === null; t++) {
    if (JSON.stringify(cert.snapshots[t]) !== JSON.stringify(derived.snaps[t]) ||
        JSON.stringify(logs[t]) !== JSON.stringify(derived.logsPerTick[t])) firstDiff = t;
  }
  if (JSON.stringify(votes) !== JSON.stringify(derived.votes)) reasons.push('vote_events_differ_from_rederivation');
  if (firstDiff !== null) reasons.push(`trace_differs_from_rederivation_at_t${firstDiff}`);
  if (cert.msgs_sent_total !== derived.sent) reasons.push(`msg_total_differs ${cert.msgs_sent_total} vs ${derived.sent}`);
  return { accepted: reasons.length === 0, rule_checks: { election_safety: s.election_safety, log_matching: s.log_matching, leader_completeness: s.leader_completeness, vote_rule: s.vote_rule }, reasons: reasons.slice(0, 12) };
}

// ---------------------------------------------------------------------------
function main() {
  const report = { runs: [], per_setting: {}, cert_checks: [], mutations: {} };
  const derivedBy = {};
  for (const setting of C.setting_order) {
    const clean = derive(setting, 'CLEAN', null, null);
    const [anchor, anchorNode] = clean.leaders[0];
    let total = 0, latency = null, feasible = true;
    for (const scenario of C.scenario_order) {
      const d = scenario === 'CLEAN' ? clean : derive(setting, scenario, anchor, anchorNode);
      derivedBy[setting + '_' + scenario] = d;
      const s = safety(d.snaps, d.logsPerTick, d.votes, d.leaders);
      const h = traceHash(setting, scenario, d.snaps);
      total += d.sent;
      if (scenario === 'CRASH_RECOVER') {
        const crashTerm = d.snaps[d.win[0] - 1][anchorNode][1];
        const nl = d.leaders.find(([t, n, term]) => t >= d.win[0] && n !== anchorNode && term > crashTerm);
        latency = nl ? nl[0] - d.win[0] : null;
      }
      const ok = s.election_safety && s.log_matching && s.leader_completeness && s.vote_rule;
      feasible = feasible && ok;
      report.runs.push({ setting, scenario, anchor, msgs_sent_total: d.sent, leaders: d.leaders, prevote_rounds: d.prevotes,
        max_term: Math.max(...d.snaps[d.snaps.length - 1].map(r => r[1])),
        election_safety: s.election_safety, log_matching: s.log_matching, leader_completeness: s.leader_completeness,
        vote_rule: s.vote_rule, trace_sha256_16: h.sha.slice(0, 16) });
      if (setting === C.certificate.baseline_setting && scenario === C.certificate.baseline_scenario) {
        report.baseline = { sha256: h.sha, certificate_first16: h.sha.slice(0, 16) };
        const engineTrace = path.join(ENGINE_OUT, 'baseline_trace_MEDIUM_PARTITION.txt');
        if (fs.existsSync(engineTrace)) report.baseline.engine_trace_file_byte_identical = fs.readFileSync(engineTrace, 'utf8') === h.text;
      }
      // engine certificate for this run
      const cf = path.join(ENGINE_OUT, 'certificates', `${setting}_${scenario}.json.gz`);
      if (fs.existsSync(cf)) report.cert_checks.push({ setting, scenario, ...checkCert(loadCert(cf), d) });
      else report.cert_checks.push({ setting, scenario, accepted: false, reasons: ['missing engine certificate'] });
    }
    report.per_setting[setting] = { feasible, crash_to_new_leader_ticks: latency, total_msgs_5_scenarios: total };
  }
  const feas = C.setting_order.filter(s => report.per_setting[s].feasible);
  const argmin = key => feas.reduce((b, s) => (b === null || report.per_setting[s][key] < report.per_setting[b][key] ? s : b), null);
  report.recovery_optimal = argmin('crash_to_new_leader_ticks');
  report.overhead_optimal = argmin('total_msgs_5_scenarios');
  report.selections_agree = report.recovery_optimal === report.overhead_optimal;

  // ---- adversarial mutations on the baseline certificate ----
  const bkey = C.certificate.baseline_setting + '_' + C.certificate.baseline_scenario;
  const bfile = path.join(ENGINE_OUT, 'certificates', bkey + '.json.gz');
  const der = derivedBy[bkey];
  const orig = loadCert(bfile);
  report.mutations.original = checkCert(orig, der);

  // M1: a vote granted to a candidate whose term is below the recipient's own current_term.
  {
    const m = JSON.parse(JSON.stringify(orig));
    const w0 = m.window[0];
    const t = w0 + 100;                     // inside the partition
    const voter = 1, cand = 3;              // N1 (majority side) grants to minority N3
    const voterTerm = m.snapshots[t - 1][voter][1];
    const reqTerm = voterTerm - 1;          // candidate term strictly below the voter's term
    m.events.push(['VOTE', t, voter, cand, reqTerm, voterTerm, m.snapshots[t - 1][voter][2]]);
    m.events.sort((a, b) => a[1] - b[1]);
    for (let u = t; u < m.snapshots.length && m.snapshots[u][voter][1] === voterTerm; u++) m.snapshots[u][voter][2] = cand;
    report.mutations.M1_vote_to_lower_term_candidate = { injected: { tick: t, voter: `N${voter}`, voter_term: voterTerm, candidate: `N${cand}`, request_term: reqTerm }, ...checkCert(m, der) };
  }
  // M2: the leader overwrites an already-committed log entry with a different one.
  {
    const m = JSON.parse(JSON.stringify(orig));
    const t = m.window[1] + 200;
    const ldr = m.snapshots[t].findIndex(r => r[0] === 'L');
    const ci = m.snapshots[t][ldr][3];
    const idx = Math.max(1, ci - 2);        // an index the leader has already committed
    const logs = replayLogs(m)[t - 1];
    const old = logs[ldr][idx - 1];
    const forged = [old[0], 9999];
    m.events.push(['LOGSET', t, ldr, idx, forged[0], forged[1]]);
    m.events.sort((a, b) => a[1] - b[1]);
    report.mutations.M2_leader_overwrites_committed_entry = { injected: { tick: t, leader: `N${ldr}`, index: idx, leader_commit_index: ci, old_entry: old, new_entry: forged }, ...checkCert(m, der) };
  }
  report.mutations.verdict = report.mutations.original.accepted &&
    !report.mutations.M1_vote_to_lower_term_candidate.accepted &&
    !report.mutations.M2_leader_overwrites_committed_entry.accepted;

  // ---- cross-check against the engine's sweep table / decision ----
  const st = path.join(ENGINE_OUT, 'sweep_table.json');
  if (fs.existsSync(st)) {
    const rows = JSON.parse(fs.readFileSync(st, 'utf8'));
    const mism = [];
    for (const r of report.runs) {
      const e = rows.find(x => x.setting === r.setting && x.scenario === r.scenario);
      if (!e) { mism.push(`${r.setting}/${r.scenario} missing`); continue; }
      if (e.msgs_sent_total !== r.msgs_sent_total) mism.push(`${r.setting}/${r.scenario} msgs ${e.msgs_sent_total} vs ${r.msgs_sent_total}`);
      if (e.trace_sha256_16 !== r.trace_sha256_16) mism.push(`${r.setting}/${r.scenario} hash ${e.trace_sha256_16} vs ${r.trace_sha256_16}`);
      if (e.anchor_tick !== r.anchor) mism.push(`${r.setting}/${r.scenario} anchor`);
    }
    report.sweep_table_crosscheck = { mismatches: mism, ok: mism.length === 0 };
  }
  report.all_engine_certificates_accepted = report.cert_checks.every(c => c.accepted);
  report.all_runs_safe = report.runs.every(r => r.election_safety && r.log_matching && r.leader_completeness && r.vote_rule);
  fs.writeFileSync(REPORT, JSON.stringify(report, null, 1));
  const brief = {
    all_runs_safe: report.all_runs_safe, all_engine_certificates_accepted: report.all_engine_certificates_accepted,
    sweep_table_crosscheck: report.sweep_table_crosscheck, per_setting: report.per_setting,
    recovery_optimal: report.recovery_optimal, overhead_optimal: report.overhead_optimal, selections_agree: report.selections_agree,
    baseline: report.baseline,
    original_accepted: report.mutations.original.accepted,
    M1: { accepted: report.mutations.M1_vote_to_lower_term_candidate.accepted, injected: report.mutations.M1_vote_to_lower_term_candidate.injected, reasons: report.mutations.M1_vote_to_lower_term_candidate.reasons },
    M2: { accepted: report.mutations.M2_leader_overwrites_committed_entry.accepted, injected: report.mutations.M2_leader_overwrites_committed_entry.injected, reasons: report.mutations.M2_leader_overwrites_committed_entry.reasons },
    mutation_verdict_pass: report.mutations.verdict,
  };
  console.log(JSON.stringify(brief, null, 1));
  const pass = report.all_runs_safe && report.all_engine_certificates_accepted && report.mutations.verdict && (!report.sweep_table_crosscheck || report.sweep_table_crosscheck.ok);
  process.exit(pass ? 0 : 1);
}
main();
