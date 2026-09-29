#!/usr/bin/env python3
"""Builds quorum7.pdf, the QUORUM-7 engineering packet.

Security/fairness requirement (explicit, non-negotiable, same discipline
as CISTERN-7's make_packet.py): all four diagrams (node state-machine,
AppendEntries batch/replication-tracking diagram, election-timeout
stagger chart, per-scenario fault-window timeline) are rendered to RASTER
(PNG) images with matplotlib's Agg backend and embedded into the PDF as
opaque image XObjects -- never as vector `savefig(..., format='pdf')`
paths, which would embed exact plotted coordinates in the content stream
for a model to parse programmatically instead of reading visually.

None of the four diagrams, and none of SPEC_TEXT below, contains any
DERIVED value (a sweep sum, a selection, a witness number, the
trace-integrity hash, or any tick number that only exists because the
reference engine was actually run). Every number shown is a STATED input
constant from design/semantic-contract.md (BASE_TIMEOUT settings,
HEARTBEAT_INTERVAL, K=4, the per-node stagger formula, fault-window
OFFSET formulas relative to a run-time-derived anchor) -- exactly the
same category CISTERN-7's Figures 1-4 encoded (elevations, pump-curve
shape, hydrograph anchors, tariff bands): inputs to compute from, never
the computation's own output.

After assembly, all document metadata (Info dictionary AND XMP) is
stripped so no authoring timestamps, tool paths, or producer strings ride
along with the shipped artifact.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import fitz  # PyMuPDF

DPI = 300
PAGE_W, PAGE_H = 612, 792  # US letter, points

TIMEOUTS = {"SHORT": 150, "MEDIUM": 250, "LONG": 400}
NUM_NODES = 5
HEARTBEAT_INTERVAL = 10
BATCH_K = 4

SCENARIOS = [
    ("CLEAN", "no scripted faults", None),
    ("PARTITION", "{N0,N1,N2} vs {N3,N4}, 400 ticks", "anchor+200 .. anchor+600"),
    ("CRASH_RECOVER", "CLEAN's own first leader crashed, 300 ticks", "anchor+200 .. anchor+500"),
    ("MESSAGE_LOSS", "targeted DROP/DUPLICATE/DELAY overrides, 400 ticks", "anchor+200 .. anchor+600"),
    ("COMPETING_CANDIDATES", "{N2,N3} isolated from {N0,N1,N4}, 500 ticks", "anchor+200 .. anchor+700"),
]


def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------
# Diagram 1: node role state-machine (S03-S05). Boxes + labeled edges.
# ---------------------------------------------------------------------
def diagram_state_machine():
    fig, ax = plt.subplots(figsize=(8.6, 7.4))
    positions = {
        "FOLLOWER": (1.6, 6.2),
        "PRECANDIDATE": (7.6, 6.2),
        "CANDIDATE": (7.6, 1.6),
        "LEADER": (1.6, 1.6),
    }
    colors = {"FOLLOWER": "#3f6f8f", "PRECANDIDATE": "#a06b3f",
              "CANDIDATE": "#8b3a3a", "LEADER": "#5b9270"}
    for name, (x, y) in positions.items():
        ax.add_patch(plt.Rectangle((x - 1.05, y - 0.42), 2.1, 0.84,
                                     facecolor="white", edgecolor=colors[name], lw=2.2, zorder=3))
        ax.text(x, y, name, ha="center", va="center", fontsize=11, fontweight="bold",
                color=colors[name], zorder=4)

    # Numbered edges only on the diagram; full descriptions live in the
    # legend below so no two labels can ever overlap on the canvas.
    edges = [
        ("FOLLOWER", "PRECANDIDATE", 0.15, 0.0, "1"),
        ("PRECANDIDATE", "PRECANDIDATE", -0.9, 0.95, "2"),
        ("PRECANDIDATE", "CANDIDATE", 0.15, 0.0, "3"),
        ("CANDIDATE", "CANDIDATE", 0.9, -0.95, "4"),
        ("CANDIDATE", "LEADER", 0.15, 0.0, "5"),
        ("LEADER", "FOLLOWER", -0.32, 0.0, "6"),
        ("CANDIDATE", "FOLLOWER", 0.55, 0.0, "7"),
        ("PRECANDIDATE", "FOLLOWER", 0.28, 0.0, "8"),
    ]

    def arrow(a, b, rad, dy, num):
        xa, ya = positions[a]
        xb, yb = positions[b]
        if a == b:
            # Self-loop: two distinct points straddling the box, offset
            # vertically by dy (above/below), so arc3 has something to
            # bow around instead of a zero-length (invisible) path.
            pa = (xa - 0.55, ya + dy)
            pb = (xb + 0.55, yb + dy)
        else:
            pa = (xa, ya + dy)
            pb = (xb, yb + dy)
        p = FancyArrowPatch(pa, pb,
                             connectionstyle=f"arc3,rad={rad}",
                             arrowstyle="-|>", mutation_scale=14,
                             color="0.3", lw=1.3, zorder=1,
                             shrinkA=26, shrinkB=26)
        ax.add_patch(p)
        # Matplotlib's own arc3 control-point formula (independent of the
        # patch's internal (unreliable-to-introspect) rendered path), so
        # the badge always lands ON the visible curve's true midpoint.
        dx_, dy_ = pb[0] - pa[0], pb[1] - pa[1]
        cx = (pa[0] + pb[0]) / 2 - rad * dy_
        cy = (pa[1] + pb[1]) / 2 + rad * dx_
        mx = 0.25 * pa[0] + 0.5 * cx + 0.25 * pb[0]
        my = 0.25 * pa[1] + 0.5 * cy + 0.25 * pb[1]
        ax.add_patch(plt.Circle((mx, my), 0.17, facecolor="white",
                                  edgecolor="0.3", lw=1.0, zorder=2))
        ax.text(mx, my, num, ha="center", va="center", fontsize=8.5,
                fontweight="bold", color="0.15", zorder=3)

    for a, b, rad, dy, num in edges:
        arrow(a, b, rad, dy, num)

    ax.set_xlim(-0.4, 9.6)
    ax.set_ylim(0.3, 7.6)
    ax.axis("off")
    ax.set_title("QUORUM-7 per-node role state machine (S03-S05)\n"
                  "current_term only increments on winning a pre-vote majority, never directly on timeout",
                 fontsize=10)

    legend_lines = [
        "1  own effective timeout elapses (election_elapsed reaches BASE_TIMEOUT + 20*node_id)",
        "2  timeout again without a pre-vote majority: fresh pre-vote round, current_term unchanged",
        "3  wins pre-vote majority (>=3/5): increment current_term, vote for self, request real votes",
        "4  split real vote, timeout again: return to a fresh pre-vote round, current_term unchanged",
        "5  wins real-vote majority (>=3/5): init next_index/match_index per follower, start replication",
        "6  (from LEADER) sees an AppendEntries or vote request at a term >= its own current_term",
        "7  (from CANDIDATE) sees an AppendEntries at term >= own (another node already won this term)",
        "8  (from PRECANDIDATE) sees an AppendEntries at term >= own while still pre-voting",
    ]
    fig.subplots_adjust(bottom=0.30, top=0.90, left=0.03, right=0.97)
    fig.text(0.04, 0.235, "\n".join(legend_lines), fontsize=8.3,
              va="top", ha="left", family="monospace")

    return render_png(fig)


# ---------------------------------------------------------------------
# Diagram 2: bounded-batch AppendEntries / per-follower tracking (S06).
# Schematic sequence for ONE leader replicating to ONE lagging follower
# across several rounds -- illustrates the mechanism, not real trace data.
# ---------------------------------------------------------------------
def diagram_batch_replication():
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    leader_y, follower_y = 3.6, 1.0
    ax.text(-0.3, leader_y, "LEADER", ha="right", va="center", fontsize=10, fontweight="bold")
    ax.text(-0.3, follower_y, "FOLLOWER j\n(far behind)", ha="right", va="center", fontsize=9)
    ax.axhline(leader_y, color="0.6", lw=1.0, xmin=0.02, xmax=0.98)
    ax.axhline(follower_y, color="0.6", lw=1.0, xmin=0.02, xmax=0.98)

    rounds = [
        (1.0, "next_index[j]=1", "entries [1..4] (K=4)", "reject: gap/term mismatch\nnext_index[j] -= 1 (backoff)"),
        (3.6, "next_index[j]=1", "entries [1..4] (K=4)", "accept: matchIndex=4\nnext_index[j]=5"),
        (6.2, "next_index[j]=5", "entries [5..8] (K=4)", "accept: matchIndex=8\nnext_index[j]=9"),
    ]
    for x, pre_label, batch_label, resp_label in rounds:
        ax.annotate("", xy=(x + 1.1, follower_y + 0.12), xytext=(x, leader_y - 0.12),
                     arrowprops=dict(arrowstyle="-|>", color="#3f6f8f", lw=1.6))
        ax.text(x + 0.15, (leader_y + follower_y) / 2 + 0.55, batch_label,
                fontsize=7.6, color="#3f6f8f")
        ax.text(x, leader_y + 0.28, pre_label, fontsize=7.2, color="0.3")
        ax.annotate("", xy=(x - 0.15, leader_y - 0.12), xytext=(x + 1.1 - 0.15, follower_y + 0.12),
                     arrowprops=dict(arrowstyle="-|>", color="#8b3a3a", lw=1.6))
        ax.text(x + 0.15, (leader_y + follower_y) / 2 - 0.55, resp_label,
                fontsize=7.2, color="#8b3a3a")

    ax.set_xlim(-2.6, 8.6)
    ax.set_ylim(0.0, 4.4)
    ax.axis("off")
    ax.set_title("Bounded-batch AppendEntries with per-follower next_index/match_index (S06)\n"
                  "K=4 entries per round; a lagging follower needs multiple rounds to catch up",
                 fontsize=9.8)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Diagram 3: election-timeout stagger, three swept BASE_TIMEOUT settings
# across the 5 nodes (S03: effective timeout = BASE_TIMEOUT + 20*node_id).
# ---------------------------------------------------------------------
def diagram_timeout_stagger():
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    colors = {"SHORT": "#8b3a3a", "MEDIUM": "#a06b3f", "LONG": "#3f6f8f"}
    bar_h = 0.22
    group_gap = 1.7
    for gi, (name, base) in enumerate(TIMEOUTS.items()):
        for nid in range(NUM_NODES):
            eff = base + 20 * nid
            y = gi * group_gap + nid * bar_h - 2 * bar_h
            ax.barh(y, eff, height=bar_h * 0.8, color=colors[name],
                     edgecolor="0.2", lw=0.4, left=0)
            ax.text(eff + 8, y, f"N{nid}: {eff}", va="center", fontsize=6.8, color="0.2")

    for gi, name in enumerate(TIMEOUTS.keys()):
        ax.text(-15, gi * group_gap, name, ha="right", va="center", fontsize=10, fontweight="bold",
                color=colors[name])

    ax.set_xlim(0, 560)
    ax.set_ylim(-0.7, 2 * group_gap + 0.7)
    ax.set_yticks([])
    ax.set_xlabel("effective election timeout (ticks) = BASE_TIMEOUT + 20 * node_id", fontsize=9)
    ax.set_title("Per-node election-timeout stagger across the 3 swept BASE_TIMEOUT settings (S03)",
                 fontsize=10)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Diagram 4: per-scenario fault-window timeline (S11), shown structurally
# against an abstract "anchor" tick (the CLEAN scenario's own first
# stable-leadership tick) -- NOT a literal computed tick number.
# ---------------------------------------------------------------------
def diagram_fault_timeline():
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    y_positions = list(range(len(SCENARIOS)))[::-1]
    ax.axvline(0, color="0.4", lw=1.2, linestyle="--", ymax=0.86)
    ax.text(18, len(SCENARIOS) + 0.55, "anchor\n(CLEAN's own first stable-leader tick,\nread from your own execution)",
            ha="left", va="top", fontsize=7.6, color="0.35")

    for (name, desc, window), y in zip(SCENARIOS, y_positions):
        ax.text(-330, y, name, ha="left", va="center", fontsize=9, fontweight="bold")
        ax.text(-330, y - 0.32, desc, ha="left", va="center", fontsize=7.2, color="0.35")
        ax.plot([-30, 780], [y, y], color="0.85", lw=6, solid_capstyle="butt", zorder=0)
        if window:
            lo, hi = 200, {"PARTITION": 600, "CRASH_RECOVER": 500,
                            "MESSAGE_LOSS": 600, "COMPETING_CANDIDATES": 700}[name]
            ax.plot([lo, hi], [y, y], color="#8b3a3a", lw=6, solid_capstyle="butt", zorder=1)
            ax.text((lo + hi) / 2, y + 0.28, window, ha="center", fontsize=6.6, color="#8b3a3a")

    ax.set_xlim(-340, 800)
    ax.set_ylim(-0.8, len(SCENARIOS) + 0.9)
    ax.axis("off")
    ax.set_title("Per-scenario fault window, offsets relative to the run's own anchor tick (S11)\n"
                  "each scenario is one continuous 2400-tick run; only the fault window shown here is scripted",
                 fontsize=9.6)
    fig.tight_layout()
    return render_png(fig)


SPEC_TEXT = """QUORUM-7 -- Engineering Packet
Computer Engineering -- Distributed Systems & Fault-Tolerant Protocols
5-node Raft-family consensus protocol -- pre-vote, bounded-batch replication, current-term-only commit

1. CLUSTER AND TICK MODEL
5 nodes, N0-N4. Ticks are discrete integer time units. Each of the 5
named scenarios (item 8) is one continuous run of exactly its own stated
2400-tick length, run to completion -- never a shortened or sampled run.
The full sweep is 3 election-timeout settings x 5 scenarios = 15 rows.

2. PER-NODE STATE
current_term (int, persisted across crash), voted_for (persisted, reset
to None whenever current_term increases), log (list of (term, cmd_id)
entries, 1-indexed, persisted), commit_index (persisted). role
(FOLLOWER/PRECANDIDATE/CANDIDATE/LEADER, volatile, resets to FOLLOWER on
crash recovery), election_elapsed (volatile). While LEADER only:
next_index[j], match_index[j] per other node j (volatile, reinitialized
on becoming leader).

3. ELECTION TIMEOUT AND ITS RESET RULE (Figure 3)
Each node's own effective election timeout is BASE_TIMEOUT + 20*node_id
ticks. BASE_TIMEOUT is the swept setting: SHORT=150, MEDIUM=250,
LONG=400. This per-node stagger is fixed and deterministic, never
randomized. election_elapsed resets to 0 only when: the node grants a
vote; the node receives a valid AppendEntries at term >= its own; or the
node itself just began a fresh pre-vote round. It is not reset by merely
receiving or sending a pre-vote message, and a LEADER does not track it.

4. PRE-VOTE PHASE (Figure 1)
On reaching its own effective timeout, a FOLLOWER (or a CANDIDATE after a
failed election) becomes PRECANDIDATE without touching current_term or
voted_for, resets election_elapsed to 0, and sends a pre-vote request
(term=current_term+1, last_log_index, last_log_term) to every other node.
A recipient grants a pre-vote iff the requester's log is at least as
up-to-date as its own by the same log-completeness rule as a real vote
(item 5) -- regardless of the recipient's own current_term or voted_for;
granting a pre-vote never mutates voted_for. On collecting grants from a
majority (>=3 of 5, itself included), the PRECANDIDATE proceeds to a real
election (item 5). If its own effective timeout elapses again first
without a majority, it stays PRECANDIDATE and resends a fresh pre-vote
round, still without incrementing current_term.

5. REAL ELECTION (Figure 1)
On winning a pre-vote majority: increment current_term by 1, vote for
self, become CANDIDATE, reset election_elapsed, and request real votes.
A recipient grants a vote iff: the request's term is >= its own (adopting
that term and stepping down first if strictly greater); its voted_for is
None or already the requester this term; AND the requester's log is at
least as up-to-date (higher last_log_term, or equal and last_log_index
>=). Concurrent same-tick requests from different candidates are
evaluated in ascending requester-node-ID order. A CANDIDATE reaching a
real-vote majority (>=3/5) becomes LEADER immediately, initializing
next_index[j]=len(own log)+1 and match_index[j]=0 for every other node j,
and immediately starts replication (item 6). A split real vote (timeout
without a majority) returns to a fresh pre-vote round, not a term
increment.

6. LOG REPLICATION -- BOUNDED-BATCH APPENDENTRIES (Figure 2)
LEADER only. For each other node j, the leader sends an AppendEntries
round to j every HEARTBEAT_INTERVAL=10 ticks, or immediately after a new
command is appended to its own log, whichever is sooner. The message
carries prevLogIndex=next_index[j]-1, prevLogTerm, up to K=4 entries
starting at next_index[j] (a lagging follower needs multiple rounds to
catch up), and leaderCommit=the leader's own commit_index. A follower
rejects iff prevLogIndex>0 and it lacks a matching entry there; on
rejection the leader decrements next_index[j] by 1 (linear backoff, no
conflict-term optimization) and retries next round. On acceptance the
follower truncates any conflicting existing entries the batch covers,
appends the batch, and advances its own commit_index toward leaderCommit
if applicable; it reports its new matchIndex, and the leader sets
match_index[j] to that value and next_index[j]=matchIndex+1.

7. COMMIT-INDEX ADVANCEMENT (LEADER)
The leader advances its own commit_index to the highest index N such
that a majority of nodes (>=3/5, itself included) have match_index[j]>=N
AND the log entry at index N has term == the leader's own CURRENT
current_term. An entry from an earlier term is never committed directly
merely because a majority already has it -- only indirectly, once a
same-term entry after it is committed by this rule.

8. NETWORK MODEL AND THE 5 NAMED SCENARIOS (Figure 4)
Every message sent at tick T is delivered at T+2 ticks unless the active
scenario's script overrides it: DELAY, DROP, or DUPLICATE for named
message classes/pairs/windows. A partition window (a tick range plus a
2-way node split) drops every message between opposite sides for its
whole duration. A crash window means the node sends and processes
nothing at all for its whole duration; on recovery it resumes as
FOLLOWER with election_elapsed at 0, using its persisted state exactly
as it was at the crash tick. Client commands are broadcast to all 5
nodes at fixed ticks; only whichever node is LEADER at that exact tick
appends the command, every other node ignores it. The 5 named scenarios,
each its own full 2400-tick run: CLEAN (no faults); PARTITION
({N0,N1,N2} vs {N3,N4}); CRASH_RECOVER (CLEAN's own first elected leader
crashed); MESSAGE_LOSS (targeted DROP/DUPLICATE/DELAY overrides);
COMPETING_CANDIDATES ({N2,N3} isolated from the 3-node majority long
enough that both independently exceed their own timeout repeatedly,
demonstrating the pre-vote phase's purpose: 2 of 5 can never reach a
3-node pre-vote majority, so neither may ever increment current_term or
disrupt the majority once the partition heals).

9. THE SWEEP AND SELECTIONS
election_timeout_setting in {SHORT, MEDIUM, LONG} x the 5 named
scenarios = 15 sweep rows, each a full run to completion. A setting is
feasible only if it violates none of the three safety invariants (item
10) in any of its 5 runs. Among feasible settings, report two
selections: recovery-optimal (minimizes ticks from CRASH_RECOVER's own
crash-window start to a new node establishing LEADER for a higher term)
and overhead-optimal (minimizes total message count across all 5
scenarios combined). These need not agree; disclose explicitly whether
they do.

10. INDEPENDENT VERIFICATION
A separately-coded verifier, sharing only immutable input constants with
your primary implementation, must independently re-derive each
scenario's full 5-node trace (or check a feasibility certificate) and
confirm for every one of the 15 runs: election safety (no two nodes are
LEADER for the same current_term simultaneously); log matching (if two
logs both hold an entry at the same index with the same term, every
earlier index in both is identical); leader completeness (once any node
commits an entry, every future leader has that exact entry at that
index). Two required adversarial mutations: a vote granted to a
candidate whose term is below the recipient's own current_term; and a
leader overwriting an already-committed log entry with a different one.
The verifier must reject both while still accepting the true original.

11. CERTIFICATION
For the baseline configuration (election_timeout=MEDIUM,
scenario=PARTITION) only: serialize the complete per-tick trace as one
line per tick "t|role0,term0|role1,term1|role2,term2|role3,term3|
role4,term4" (role as its first letter), preceded by one header line
"QUORUM7|MEDIUM|PARTITION", lines joined by \\n, UTF-8 encoded, hashed
with SHA-256; report the first 16 hex characters as the trace-integrity
certificate.

Deliver: protocol-engine source, an independently-coded verifier, the
full 15-row sweep table, a decision file with both selections and their
agreement/divergence disclosure, the baseline trace plus its SHA-256
certificate and your adversarial-mutation results, and an engineering
memo explaining the recovery/overhead trade-off and the pre-vote phase's
role in the COMPETING_CANDIDATES scenario. Base every reported number on
your own executed implementation -- never hand-derive a trace, a sum, or
the hash.
"""


def build_text_pages(doc):
    blocks = SPEC_TEXT.split("\n\n")
    margin = 44
    rect = fitz.Rect(margin, margin, PAGE_W - margin, PAGE_H - margin)
    fontsize = 8.0

    def fits(text, fs):
        tmp = fitz.open()
        p = tmp.new_page(width=PAGE_W, height=PAGE_H)
        rc = p.insert_textbox(rect, text, fontsize=fs, fontname="helv",
                               align=fitz.TEXT_ALIGN_LEFT)
        tmp.close()
        return rc >= 0

    pages_text = []
    current = ""
    for block in blocks:
        candidate = (current + "\n\n" + block) if current else block
        if fits(candidate, fontsize):
            current = candidate
        else:
            if current:
                pages_text.append(current)
            current = block
            if not fits(current, fontsize):
                raise RuntimeError(f"single block too large to fit page:\n{block[:80]}...")
    if current:
        pages_text.append(current)

    for text in pages_text:
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_textbox(rect, text, fontsize=fontsize, fontname="helv",
                             align=fitz.TEXT_ALIGN_LEFT)


def build_image_page(doc, png_bytes, caption):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    img = fitz.open("png", png_bytes)
    iw, ih = img[0].rect.width, img[0].rect.height
    margin = 40
    max_w = PAGE_W - 2 * margin
    max_h = PAGE_H - 2 * margin - 30
    scale = min(max_w / iw, max_h / ih)
    w, h = iw * scale, ih * scale
    x0 = (PAGE_W - w) / 2
    y0 = 40
    page.insert_image(fitz.Rect(x0, y0, x0 + w, y0 + h), stream=png_bytes)
    page.insert_textbox(fitz.Rect(margin, y0 + h + 6, PAGE_W - margin, y0 + h + 40),
                         caption, fontsize=9, fontname="helv",
                         align=fitz.TEXT_ALIGN_CENTER)


def main():
    doc = fitz.open()

    build_image_page(doc, diagram_state_machine(),
                      "Figure 1 -- Per-node role state machine. Pre-vote gates every real election.")
    build_image_page(doc, diagram_batch_replication(),
                      "Figure 2 -- Bounded-batch AppendEntries, K=4, per-follower next_index/match_index (schematic).")
    build_image_page(doc, diagram_timeout_stagger(),
                      "Figure 3 -- Per-node election-timeout stagger across the 3 swept BASE_TIMEOUT settings.")
    build_image_page(doc, diagram_fault_timeline(),
                      "Figure 4 -- Per-scenario fault window, offsets relative to your own run's anchor tick.")
    build_text_pages(doc)

    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    doc.xref_set_key(doc.pdf_catalog(), "Info", "null")

    out_path = "/home/user/cc/task07/artifact/quorum7.pdf"
    doc.save(out_path, garbage=4, deflate=True, clean=True)
    doc.close()

    raw = open(out_path, "rb").read()
    start = raw.find(b"% Written by")
    if start != -1:
        end = raw.find(b"\n", start)
        segment = raw[start:end]
        blanked = b"%" + b" " * (len(segment) - 1)
        raw = raw[:start] + blanked + raw[end:]
        open(out_path, "wb").write(raw)

    print("wrote", out_path)


if __name__ == "__main__":
    main()
