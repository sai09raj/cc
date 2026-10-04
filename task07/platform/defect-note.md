# QUORUM-7 — specification defect note (for withdraw-or-revise decision)

## Summary

The submitted QUORUM-7 packet (`quorum7.pdf`) omits three facts that the
reference implementation uses and that the rubric's highest-weight block
depends on. A solver cannot recover them from the prompt or the packet, so
part of the 31% and 32% pilot scores comes from missing specification
rather than task difficulty.

## The three gaps

1. **Client command schedule.** The packet says commands "are broadcast to
   all 5 nodes at fixed ticks" but never lists the ticks. The reference uses
   five commands at t = 300, 600, 900, 1500 and 2000.
2. **MESSAGE_LOSS overrides.** The packet says "targeted
   DROP/DUPLICATE/DELAY overrides" but gives none. The reference applies,
   during the scenario's window: DROP on N0→N3 AppendEntries requests;
   DUPLICATE ×3 on N1→N2 vote requests; DELAY by 15 ticks on N0→N4
   AppendEntries requests.
3. **Definition of "message count".** The packet never defines it. The
   reference counts every message a node sends, except a message whose
   sender and receiver are on opposite sides of an active partition (not
   counted); a message discarded by a DROP override is counted.

## Rubric impact

Criteria 19–28 (100 of 197 positive points) are message-count and
commit-index sums over the sweep. Commit sums depend on gap 1; message sums
depend on gap 3 (and, for the MESSAGE_LOSS rows, gap 2). Criteria 14, 16–18
and 33 (the baseline hash) also depend on these gaps. Both real pilots
converged on the same alternate baseline hash `d75121e3abb34538`, which is
the expected signature of a specification gap.

## Exact fix (if revising)

Add to the packet's scenario section, verbatim or equivalent:

- "Client commands c1–c5 are broadcast at ticks 300, 600, 900, 1500 and 2000
  in every scenario."
- "MESSAGE_LOSS applies, only during its window: DROP every AppendEntries
  request from N0 to N3; DUPLICATE every vote request from N1 to N2 so it is
  delivered 3 times; DELAY every AppendEntries request from N0 to N4 by 15
  ticks."
- "Message count is the number of messages sent by any node, excluding
  messages between nodes on opposite sides of an active partition (never
  sent) and including messages that a DROP override later discards."

Then issue a new artifact filename, regenerate the goldens (unchanged if
these match the reference), and re-pilot. Old scores cannot be reused. With
the gaps closed, expect the scores to rise substantially: a blind
`opus`-alias pilot, guessing the missing facts, still matched the
reference's message counts exactly on all three CLEAN rows (the rows no
partition or override touches), and matched the SHORT and MEDIUM crash
recovery latencies (172 and 272 ticks).
