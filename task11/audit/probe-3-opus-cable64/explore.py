import json, math
from math import isqrt
F=json.load(open('../field.json'))
T=F['turbines']; names=sorted(T); P=[tuple(T[n]) for n in names]
def rlen(a,b):
    d2=(a[0]-b[0])**2+(a[1]-b[1])**2
    n=isqrt(d2)
    # round half up: n or n+1
    if 4*d2 >= (2*n+1)**2: n+=1
    return n
import itertools
cnt=0; near=[]
for i,j in itertools.combinations(range(64),2):
    d=math.dist(P[i],P[j])
    if 1290<d<1310: near.append((names[i],names[j],d))
    if rlen(P[i],P[j])<=1300: cnt+=1
print('undirected turbine edges <=1300:',cnt); print(near)
# degree distribution
deg=[sum(1 for j in range(64) if j!=i and rlen(P[i],P[j])<=1300) for i in range(64)]
print(sorted(deg))
# collinear triples
for i,j,k in itertools.permutations(range(64),3):
    if i<j:
        a,b,c=P[i],P[j],P[k]
        cr=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        if cr==0 and min(a[0],b[0])<=c[0]<=max(a[0],b[0]) and min(a[1],b[1])<=c[1]<=max(a[1],b[1]) and rlen(a,b)<=1300:
            print('collinear on short edge',names[i],names[j],names[k])
for key in ['substation_primary','substation_alternative']:
    s=tuple(F[key]); ds=sorted((rlen(s,p),n) for p,n in zip(P,names)); print(key, ds[:8], ds[-3:])
