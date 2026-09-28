## Numeric transcription checklist

- [ ] Prompt: 343 whitespace-delimited words (permitted 2-500).
- [ ] Analyze: 1352 characters (permitted 5-3000).
- [ ] Execute & Generate: 1143 characters (permitted 5-3000).
- [ ] Synthesize: 1221 characters (permitted 5-3000).
- [ ] Exactly 50 criteria (49 positive + 1 negative); weights in order:
      2,1,1, 2,2,1,1,1,1,1,1,1,1,2,1,1, 10,10,10,10,10,10,10,10,10,10,7,10, 3,3,3,3,3,
      1,1,1,1, 10,10,10,10,10,10, 1,1,1,1,1,1, -8.
      (Criterion 27 is +7, not +10 — 3 of its original weight moved to the standalone
      witness criterion 33, once W3 was split out to stop double-counting/inconsistent
      bundling. Criteria 1-3 are 3 rows, not 4 — the old commands/tool-versions
      criterion merged into criterion 1. Criteria 10/11 and 14/15/16 are each split
      from one previously-bundled criterion, per a rubric-guidelines atomicity fix;
      see `revision-delta.md` for the full accounting.)
- [ ] Positive weights sum 222; criterion 50 alone has weight -8.
- [ ] Attachment filename: `kw-r3c.pdf` (unique to this revision; do not upload any
      R1/R2/R3b file, and do not upload the earlier `kw-r3b.pdf` that blind-pilot-2
      saw — this hardened version changes Section H's maintenance mechanism to
      recurring and has different bytes; verify against the hash in
      `frozen-packet-manifest.json`).
- [ ] Four campaigns 0..3, five lots 0..4 per campaign, twenty lots per design, six
      designs D0..D5 — one continuous trace per design, not 24 independent cases.
- [ ] Budget population `capital<=9` includes D0, D1, D2, D3 (D2 at equality).
- [ ] Correct unrestricted key: `(151, 1324, 22, D5)`.
- [ ] Correct capital<=9 key: `(159, 1260, 7, D1)`.

| Design | Makespan | Bill |
|---|---:|---:|
| D0 | 187 | 1331 |
| D1 | 159 | 1239 |
| D2 | 188 | 1435 |
| D3 | 185 | 1378 |
| D4 | 152 | 1344 |
| D5 | 151 | 1258 |

- [ ] Node-4 fault (S07): freezes 6 minutes including arrival, fires once per design.
- [ ] Machine-Q maintenance freeze (S13, hardened R3c): triggers at cumulative
      processing (since the last freeze ended) >= 10; freezes 13 minutes starting
      the minute AFTER the trigger (not inclusive, unlike S07); **recurring** —
      cumulative tracking resets to 0 on every trigger, no per-design cap. D0
      triggers it exactly once (its 2-job Q workload sums to exactly 12, crossing
      on its last job) but that trigger has zero effect — no remaining Q work is
      left to delay. D1/D2/D3/D4/D5 each trigger it 2-3 times with real effect.
- [ ] Witness W3 (D4): Q's campaign-1 job on global-index-6 lot runs 10 minutes
      (Qbase 8 + setup 2). Unaffected by the R3c threshold change.
- [ ] Witness W4 (D1): mixed-campaign batch at t=50, members {global index 3, 7}.
      Unaffected by the R3c threshold change.
- [ ] Witness W5 (D1): two maintenance triggers — t=44 (freeze [45,57]) and t=118
      (freeze [119,131]) — the second changes which lot fills Q's last slot
      (global index 18 instead of 16, see `production-witnesses.md`).
- [ ] All six per-design trace-integrity values are each exactly 16 lowercase hex
      characters — the first 16 characters of the full SHA-256, truncated for safe
      manual transcription (verify programmatically, not by eye) and copied from
      `production-witnesses.md` / `frozen-packet-manifest.json`, never retyped by
      hand:
      D0=`955957f0e6a9788d`, D1=`9eafc0820bda70a9`, D2=`7d104044363f36b2`,
      D3=`b1086cb4f38396f4`, D4=`c9e705daef1ddcf7`, D5=`6a1d99ca7302e560`.
      (Only D0's value is unchanged from R3b — see above.)
- [ ] After entry, compare an export or screenshots of every field and weight
      against this guide. This checkbox remains unverified until that evidence
      exists.
