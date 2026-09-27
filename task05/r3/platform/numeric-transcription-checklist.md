## Numeric transcription checklist

- [ ] Prompt: 343 whitespace-delimited words (permitted 2-500).
- [ ] Analyze: 1064 characters (permitted 5-3000).
- [ ] Execute & Generate: 1143 characters (permitted 5-3000).
- [ ] Synthesize: 1136 characters (permitted 5-3000).
- [ ] Exactly 39 criteria (38 positive + 1 negative); weights in order:
      1,1,1,1,2,2,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,2,3,1,1,1,1,1,1,1,1,-8.
- [ ] Positive weights sum 61; criterion 39 alone has weight -8.
- [ ] Attachment filename: `kw-r3.pdf` (unique to this revision; do not
      upload any R1/R2 file).
- [ ] Four campaigns 0..3, five lots 0..4 per campaign, twenty lots per design, six
      designs D0..D5 — one continuous trace per design, not 24 independent cases.
- [ ] Budget population `capital<=9` includes D0, D1, D2, D3 (D2 at equality).
- [ ] Correct unrestricted key: `(142, 1356, 22, D5)`.
- [ ] Correct capital<=9 key: `(165, 1315, 7, D1)`.

| Design | Makespan | Bill |
|---|---:|---:|
| D0 | 187 | 1331 |
| D1 | 165 | 1294 |
| D2 | 187 | 1447 |
| D3 | 185 | 1401 |
| D4 | 155 | 1413 |
| D5 | 142 | 1290 |

- [ ] Node-4 fault: fires at minute 7 for D0/D2/D3/D4/D5, minute 9 for D1 (offline
      window = arrival minute + 5 more, 6 minutes total).
- [ ] Witness W3 (D4): Q's campaign-1 job on global-index-6 lot runs 10 minutes
      (Qbase 8 + setup 2).
- [ ] Witness W4 (D1): mixed-campaign batch at t=50, members {global index 3, 7}.
- [ ] After entry, compare an export or screenshots of every field and weight
      against this guide. This checkbox remains unverified until that evidence
      exists.
