## Numeric transcription checklist

- [ ] Prompt: 343 whitespace-delimited words (permitted 2-500).
- [ ] Analyze: 1352 characters (permitted 5-3000).
- [ ] Execute & Generate: 1143 characters (permitted 5-3000).
- [ ] Synthesize: 1221 characters (permitted 5-3000).
- [ ] Exactly 48 criteria (47 positive + 1 negative); weights in order:
      1,1,1,1,2,2,1,1,1,1,1,1,1,2,2,10,10,10,10,10,10,10,10,10,10,10,10,3,3,3,3,1,1,1,1,
      10,10,10,10,10,10,1,1,1,1,1,1,-8.
- [ ] Positive weights sum 221; criterion 48 alone has weight -8.
- [ ] Attachment filename: `kw-r3b.pdf` (unique to this revision; do not upload any
      R1/R2 file, and do not upload the earlier `kw-r3.pdf` that blind-pilot-1 saw —
      this hardened version adds Section G and Section H and has different bytes;
      verify against the hash in `frozen-packet-manifest.json`).
- [ ] Four campaigns 0..3, five lots 0..4 per campaign, twenty lots per design, six
      designs D0..D5 — one continuous trace per design, not 24 independent cases.
- [ ] Budget population `capital<=9` includes D0, D1, D2, D3 (D2 at equality).
- [ ] Correct unrestricted key: `(151, 1432, 16, D4)`.
- [ ] Correct capital<=9 key: `(161, 1263, 7, D1)`.

| Design | Makespan | Bill |
|---|---:|---:|
| D0 | 187 | 1331 |
| D1 | 161 | 1242 |
| D2 | 187 | 1373 |
| D3 | 185 | 1408 |
| D4 | 151 | 1384 |
| D5 | 153 | 1298 |

- [ ] Node-4 fault (S07): freezes 6 minutes including arrival, fires once per design.
- [ ] Machine-Q maintenance freeze (S13): triggers at cumulative processing >= 12;
      freezes 13 minutes starting the minute AFTER the trigger (not inclusive,
      unlike S07); fires once per design. D0 never triggers it (structural, not a
      bug — Q's total workload in D0 stays under 12).
- [ ] Witness W3 (D4): Q's campaign-1 job on global-index-6 lot runs 10 minutes
      (Qbase 8 + setup 2).
- [ ] Witness W4 (D1): mixed-campaign batch at t=50, members {global index 3, 7}.
- [ ] Witness W5 (D1): maintenance trigger at t=44, freeze [45,57]; Q's next job
      (global index 8) delayed to t=62 (vs t=55 if the mechanism were absent).
- [ ] All six per-design trace-integrity SHA-256 hashes are each exactly 64
      lowercase hex characters (verify programmatically, not by eye) and were
      copied from `production-witnesses.md` / `frozen-packet-manifest.json`, never
      retyped by hand.
- [ ] After entry, compare an export or screenshots of every field and weight
      against this guide. This checkbox remains unverified until that evidence
      exists.
