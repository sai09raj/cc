# TENURE-11 semantic contract (v1)

Every rule the reference engine implements is listed here, with the
artifact location that will carry it. Nothing may exist only in code.
The artifact must distribute these rules across the panels where they
naturally belong; it must not reproduce this file as one ordered list
(mistake #70).

Units: bytes and integer pause units. All arithmetic is integer; every
division is floor division.

## S01 — Fixed constants

| Name | Value | Artifact source |
|---|---|---|
| `ALIGN` | 8 | prose |
| `HEADER` | 16 | **measured**: object-layout drawing, header segment against a byte ruler |
| `OLD_SIZE` | 131072 (128 KiB) | **measured**: heap map, old-generation span against the address axis |
| `MIN_SPLIT` | 32 | prose |
| `N_OPS` | 26000 | timeline axis end + prose |
| `RING` | 64 | prose |
| `REG_COUNT` | 16 | prose |
| `LIST_DROP` | 1500 | prose |

## S02 — Object kinds and sizes

Object size = round up (`HEADER` + payload) to a multiple of `ALIGN`.
Payload depends on the kind and, for three kinds, on the operation index
`i` (0-based) of the operation that allocates the object.

| Kind | Payload | Reference slots | Artifact source |
|---|---|---|---|
| TEMP | 24 | 0 | bar chart (payload), markers (slots) |
| SESSION | 96 | 1 | bar chart, markers |
| BLOB | 96 + 96 × (i mod 13) | 0 | bar chart shows base; step and modulus in chart annotation |
| ENTRY | 56 + 24 × (i mod 3) | 1 | bar chart base; annotation |
| NODE | 40 + 8 × (i mod 5) | 1 | bar chart base; annotation |
| REG | 112 | 4 | bar chart, markers |

Registry objects use `i = j` for registry index `j` (irrelevant to size,
since REG is fixed).

## S03 — Roots

Root slots are numbered. Slot 0 = scratch; slots 1..64 = session ring;
slots 100..115 = registry; slot 120 = list head. All start null. Whenever
roots are scanned, they are scanned in ascending slot number, skipping
null slots.

## S04 — Mutator workload

Before operation 0: allocate `REG_COUNT` REG objects in order j = 0..15;
REG j goes into root slot 100 + j.

Operation `i` for i = 0 .. N_OPS − 1:

1. Phase: warm for i < 4000, steady for i < 16000, burst for i < 22000,
   drain otherwise. (**measured**: phase boundaries on the timeline axis;
   only 0, 8000, 16000, 24000 carry labels.)
2. Kind = the phase's 10-entry mix at position `i mod 10`:

   | Phase | Mix (positions 0..9) |
   |---|---|
   | warm | TEMP TEMP SESSION NODE TEMP ENTRY TEMP NODE TEMP SESSION |
   | steady | TEMP SESSION TEMP ENTRY NODE TEMP ENTRY TEMP NODE TEMP |
   | burst | SESSION TEMP SESSION ENTRY SESSION NODE SESSION TEMP ENTRY NODE |
   | drain | TEMP TEMP ENTRY TEMP NODE TEMP TEMP TEMP ENTRY TEMP |

3. Allocate one object of that kind (S06). Then:
   - TEMP: root 0 ← new object.
   - SESSION: let `k` = number of sessions created before this one;
     root `1 + (k mod 64)` ← new session. Then allocate a BLOB (same `i`).
     After that allocation, read the session **from its root slot** (a GC
     during the BLOB allocation may have moved it) and store the BLOB into
     its slot 0.
   - ENTRY: if at least one session exists, the entry's slot 0 ← the
     object currently in the ring slot of the most recently created
     session (read after the entry's allocation); otherwise null. Let `c`
     = number of entries created before this one. Registry object in root
     slot `100 + (c mod 16)`, slot `(c div 16) mod 4` ← the entry.
   - NODE: node slot 0 ← object currently in root 120 (read after the
     node's allocation); root 120 ← node.
4. After the operation's actions: if `i mod 1500 = 1499`, root 120 ← null.

If any allocation causes OOM (S10), the run stops immediately.

## S05 — Heap regions

Eden (size `EDEN`, a sweep dimension), two survivor spaces (each
`SURV`), old generation (`OLD_SIZE`). Eden and survivors are bump
allocated from offset 0. One survivor is "from" (holds the previous
GC's survivors), the other "to" (empty). Each young object has an age,
0 at allocation.

## S06 — Allocation

Object size `s` (S02).

1. **Pretenure:** if the configuration's pretenure threshold `PT` is not
   off and `s ≥ PT`: place in the old generation (S08). If placement
   fails, run a major GC (S09) and place again; if it still fails, OOM.
   No minor GC is involved. After a successful pretenured placement,
   sample old occupancy (S11).
2. Otherwise, if `eden_used + s > EDEN`, run a minor GC (S07) first.
3. Bump-allocate in eden, age 0.

## S07 — Minor GC

1. **Promotion guard:** if total free bytes in the old generation <
   `eden_used + from_used`, run a major GC (S09) before anything else.
2. Count the minor GC. Record `R` = current remembered-set size.
3. **Evacuation order (Cheney):** evacuate every non-null root, in
   ascending slot order (S03). Then, for each remembered-set object in
   ascending old-generation address, evacuate each young reference in
   its slots in slot order. Then process a FIFO queue of every object
   evacuated so far (copied or promoted, in evacuation order): for each,
   evacuate each young reference in its slots in slot order. Every slot
   holding an evacuated object is updated to its new location.
4. **Evacuate(o)** for a young object not yet evacuated in this GC:
   `a = age + 1`.
   - If `a ≥ T` (tenuring threshold): promote.
   - Else if `to_used + size ≤ SURV`: copy into to-space at `to_used`,
     age `a`; add `size` to bytes copied.
   - Else (survivor overflow): promote.
   Promote = place in the old generation (S08); add `size` to bytes
   promoted. If placement fails: OOM, run stops. An object already
   evacuated in this GC is not evacuated again; its new location is used.
5. Afterwards: eden and the old from-space are empty; to-space becomes
   from-space.
6. **Remembered-set rebuild:** the set becomes every live old-generation
   object holding at least one reference to a survivor-space object.
7. Pause = 40 + `copied` div 64 + `promoted` div 32 + 2 × `R`.
8. Sample old occupancy (S11).

## S08 — Old-generation placement

Free list of blocks `(address, length)`, initially `(0, OLD_SIZE)`.
Address-ordered first fit: choose the lowest-address block with
`length ≥ s`. If `length − s ≥ MIN_SPLIT`, the object occupies
`[address, address + s)` and the remainder stays free; otherwise the
object occupies the whole block. Each old object records its occupied
length. No coalescing happens here.

## S09 — Major GC

1. Count the major GC.
2. Mark every object reachable from the non-null roots, following all
   references in every region.
3. Sweep the old generation: every unmarked old object is freed (its
   occupied block returns to the free list) and removed from the
   remembered set.
4. Coalesce: sort the free list by address and merge blocks that are
   exactly adjacent.
5. Pause = 150 + (sum of occupied lengths of marked old objects) div 32 +
   (number of freed old objects) div 2.

Young objects are not moved by a major GC.

## S10 — Write barrier and OOM

- Whenever the mutator stores a non-null reference into a slot of an
  old-generation object and the referenced object is in eden or a
  survivor space, the old object is added to the remembered set (a set:
  adding twice has no effect). No other store changes the set.
- OOM: a failed promotion (S07.4) or a failed pretenured placement after
  its major GC (S06.1). The run stops; the configuration is infeasible.

## S11 — Metrics (per configuration)

`oom` (and the operation index at which it occurred), `minor`, `major`,
`copied` (sum of S07 bytes copied), `promoted`, `pretenured` (sum of
sizes of pretenured objects), `pause_total`, `pause_max` (over all minor
and major pauses), `old_peak` (maximum old occupancy sampled after every
minor GC and after every pretenured placement; occupancy = sum of
occupied lengths of old objects).

## S12 — Sweep

`EDEN` ∈ {16384, 24576, 32768, 49152} × `SURV` ∈ {8192, 24576} ×
`T` ∈ {1, 2, 3, 5} × `PT` ∈ {off, 768, 1024}: 96 configurations, each a
complete fresh run of S04.

## S13 — Selections (`BUDGET` = 220000, `CEILING` = 2400)

Over non-OOM configurations only:

1. **Cost-optimal:** minimum `pause_total`; ties by minimum `pause_max`,
   then by (EDEN, SURV, T, PT) ascending with off < 768 < 1024.
2. **Latency-optimal under budget:** minimum `pause_max` among
   configurations with `pause_total ≤ BUDGET`; ties by `pause_total`,
   then configuration order.
3. **Footprint-optimal under ceiling:** minimum `EDEN + 2 × SURV` among
   configurations with `pause_max ≤ CEILING`; ties by `pause_total`,
   then configuration order.

## S14 — Baseline trace and certificate

Baseline configuration (the service's current setting): EDEN 24576,
SURV 8192, T 2, PT off. Its GC event log has one line per GC, in order:
`n;type;op;copied;promoted;remset;marked;freed;occupancy;pause` where
`n` is the 1-based event number, `type` is `m` (minor) or `M` (major),
`op` is the index of the operation during which the GC occurred
(registry initialisation counts as op −1), `remset` is `R` from S07.2,
`marked` and `freed` are the S09 marked bytes and freed object count,
`occupancy` is old occupancy immediately after the event, and fields not
applicable to the type are 0. A major GC triggered by the promotion guard
is logged before the minor GC it precedes. The certificate is the header
line `TENURE11-GCLOG-V1` followed by those lines, newline-joined with a
trailing newline; its hash is the first 16 hex characters of SHA-256 of
that text. The artifact must show this format with a fake-number
example (mistake #66).
