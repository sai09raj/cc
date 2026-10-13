"""Network state at the 08:00 handover (from the control room log)."""
import net as N
def final(**over):
    st = dict(open={r[0] for r in N.ROUTES},                     # D1 propped open 03:20, still open (X1 in service); ST-7 damaged 05:10 -> brattice 06:20 (X2 in service)
              fan="standby",                                     # main fan tripped 04:10; standby running; main held pending vibration test
              reg={**N.REG_AREA, "REG-E": 3.6, "REG-T": 1.0},   # REG-E opened 02:00 for gas dilution, reset deferred; REG-T reduced 00:30
              extra_R={"X2": N.R_BRATTICE}, routes={})
    st.update(over); return st
def normal(**over):
    st = dict(open={r[0] for r in N.ROUTES} - {"X1", "X2"}, fan="main 0", reg=dict(N.REG_AREA), extra_R={}, routes={})
    st.update(over); return st
