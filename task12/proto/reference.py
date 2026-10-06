import cohere as C, json, csv, sys
progs=C.workload()
rows=[]
for pn in sorted(C.PLACEMENTS):
    for q in (1,2,3,4):
        for b in (1,2,4,8):
            s=C.Sim(C.PLACEMENTS[pn],q,b,progs); r=s.run()
            assert C.check_values(s)==0
            rows.append(dict(placement=pn,Q=q,B=b,makespan=r["makespan"],p95=r["p95_load_miss"],msgs=r["msgs"],nacks=r["nacks"]))
key=lambda x:(x["makespan"],x["p95"],x["msgs"],x["placement"],x["Q"],x["B"])
best=min(rows,key=key)
feas=[x for x in rows if x["p95"]<=32 and x["nacks"]<=20]
cons=min(feas,key=key)
print("best",best); print("constrained n=",len(feas),cons)
print("sum makespan",sum(x["makespan"] for x in rows),"sum msgs",sum(x["msgs"] for x in rows),"sum nacks",sum(x["nacks"] for x in rows))
s=C.Sim(C.PLACEMENTS["P1"],2,2,progs); r=s.run(); print("baseline P1/2/2",r["makespan"],s.done_t,dict(sorted((k,v) for k,v in s.stats.items())))
json.dump(rows,open("sweep_ref.json","w"),indent=0)
