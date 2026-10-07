import glob, os, json, sys
from array import array
D=sys.argv[1]; BASE=6725
tot=0; n=0; better=0; le6000=0; perQ={q:0 for q in (1,2,3,4)}; perB={b:0 for b in (1,2,4,8)}; sumQ={q:0 for q in (1,2,3,4)}
hist={}
for f in sorted(glob.glob(D+"/c_*.bin")):
    d0,d1,q,b=map(int,os.path.basename(f)[2:-4].split("_"))
    a=array("H"); a.frombytes(open(f,"rb").read()); ms=a[0::2]
    s=sum(ms); tot+=s; sumQ[q]+=s; n+=len(ms)
    bt=sum(1 for v in ms if v<BASE); better+=bt; perQ[q]+=bt; perB[b]+=bt
    le6000+=sum(1 for v in ms if v<=6000)
out=dict(configs=n,sum_makespan=tot,mean_makespan=tot/n,faster_than_baseline=better,at_most_6000=le6000,faster_by_Q=perQ,faster_by_B=perB,sum_makespan_by_Q=sumQ)
json.dump(out,open(D+"/aggregates2.json","w"),indent=1); print(json.dumps(out,indent=1))
