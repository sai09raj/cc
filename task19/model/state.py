"""Control-room log replay: network state at 09:00."""
import copy, net as N
REPAIR = {"A3": [("DN125", 450), ("DN125", 290)]}           # 06:40 damaged DN100 260 m section replaced by 290 m of DN125
def final(**over):
    st = dict(open={r[0] for r in N.ROUTES},                  # X3 opened 23:30 and left open; L2 isolation for meter change deferred (08:15), valves open
              T_ec=92.0,                                     # 06:00 winter curve setpoint
              loads={k: v for k, v in N.LOAD.items() if k != "H7"},   # H7 isolated 02:10, still out
              routes=dict(REPAIR))
    st.update(over); return st
