import cohere as C, sys
progs=C.workload()
cfgs=[(pn,q,b) for pn in C.PLACEMENTS for q in (1,2,3,4) for b in (1,2,4,8)]
def sweep(mut):
    out={}
    for pn,q,b in cfgs:
        s=C.Sim(C.PLACEMENTS[pn],q,b,progs,mut=frozenset(mut))
        try: r=s.run(limit=20000); out[(pn,q,b)]=(r["makespan"],r["p95_load_miss"],r["msgs"],r["nacks"],C.check_values(s))
        except Exception as e: out[(pn,q,b)]=("ERR",type(e).__name__)
    return out
base=sweep([])
for mut in ["novnetprio","linear_backoff","fwd_first","serial_only","dir_req_first","same_cycle","nacks_first","hol_fwd","ackcount_all","no_fwd_stall"]:
    r=sweep([mut])
    ch=sum(1 for k in cfgs if r[k][:1]!=base[k][:1]); err=sum(1 for k in cfgs if r[k][0]=="ERR"); vb=sum(1 for k in cfgs if r[k][0]!="ERR" and r[k][4])
    print(f"{mut:15s} makespan changed {ch}/64  errors {err}  value-violations {vb}")
