"""The 09:00 state the log leaves in force (reference), plus a helper to build variants."""
import net as N
REPAIR = {"F1-3": [("185", 640), ("185", 410)]}   # the damaged 380 m 95 section (joint J7 to S3) replaced by 410 m of 185 in a new trench (07:20)
def routes(repair=True):
    return [(r[0], r[1], r[2], REPAIR[r[0]] if (repair and r[0] in REPAIR) else r[3]) for r in N.ROUTES]
def final(**over):
    closed = {r[0] for r in N.ROUTES}
    s = dict(closed=closed, tx={"T1", "T2"}, bs=False, taps={"T1": 9, "T2": "auto"}, cap=True, pv_kw=2500.0, routes=routes())
    s.update(over); return s
