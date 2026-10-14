"""Network state at the 07:30 peak check (from the control log)."""
import net as N
def final(**over):
    st = dict(open={r[0] for r in N.ROUTES}, tss={"TSS-A", "TSS-C", "TSS-D"}, tap={"TSS-D": 1}, trams=dict(N.TRAMS), routes={})
    st.update(over); return st
