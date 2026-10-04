import gcp, itertools
for old, step, m in [(128*1024,96,13),(160*1024,96,13),(192*1024,96,13)]:
    gcp.P["OLD_SIZE"]=old; gcp.VAR["BLOB"]=(m,step)
    r=gcp.sweep(dims="PT")
    oom=sum(v[0] for v in r.values())
    # effect of PT dim within each (e,s,t)
    g={}
    for (e,s,t,pt),v in r.items(): g.setdefault((e,s,t),{})[pt]=v
    spread=[]
    for k,d in g.items():
        f=[v[5] for v in d.values() if not v[0]]
        if len(f)>1: spread.append((max(f)-min(f))/min(f))
    nonmono_t=0
    g2={}
    for (e,s,t,pt),v in r.items(): g2.setdefault((e,s,pt),{})[t]=v
    for k,d in g2.items():
        seq=[d[t][5] for t in sorted(d) if not d[t][0]]
        diffs=[b-a for a,b in zip(seq,seq[1:])]
        if any(x>0 for x in diffs) and any(x<0 for x in diffs): nonmono_t+=1
    print(old//1024,"oom",oom,"PT ptot spread median %.3f max %.3f"%(sorted(spread)[len(spread)//2],max(spread)),"tenure-nonmono groups",nonmono_t,"/",len(g2))
