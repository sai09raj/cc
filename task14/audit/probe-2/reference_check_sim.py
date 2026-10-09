# Independent, slow, cell-array reference implementation (Python) used only to cross-check grid14_sim.js.
import sys
C_M = 7.5
H = {(0,0):240,(0,1):195,(1,0):165,(1,1):270,(2,0):210,(2,1):180}   # (row, col) -> block east of I(row,col)
Vb = {(0,0):225,(1,0):150,(0,1):180,(1,1):255,(0,2):202.5,(1,2):157.5}  # (row,col) -> block south of I(row,col)
IN = [285,330,270,307.5,262.5,322.5,292.5,277.5,337.5,315,300,270]
DEM = {'AM':[208,266,182,234,195,254,221,176,273,247,202,228],
       'PM':[221,176,273,247,202,228,208,266,182,234,195,254],
       'EVENT':[208,266,182,234,312,254,221,176,273,395,202,228]}
_G = {60:[(18,8,18,8),(22,6,18,6),(16,7,22,7),(20,9,16,7),(16,7,20,9),(21,5,21,5)],
72:[(22,10,22,10),(27,8,22,7),(20,9,27,8),(25,11,20,8),(20,8,25,11),(26,6,26,6)],
84:[(26,12,26,12),(32,9,26,9),(23,11,32,10),(29,14,23,10),(23,11,29,13),(31,7,31,7)],
96:[(30,14,30,14),(37,11,30,10),(27,12,37,12),(34,15,27,12),(27,12,34,15),(36,8,36,8)],
108:[(34,16,34,16),(42,12,34,12),(30,14,42,14),(38,18,30,14),(30,14,38,18),(40,10,40,10)],
120:[(39,17,39,17),(48,13,38,13),(34,15,48,15),(43,20,34,15),(34,15,43,20),(45,11,45,11)]}
GREENS = {(c,p+1):g for c,l in _G.items() for p,g in enumerate(l)}
DIRS = {'N':(-1,0),'S':(1,0),'E':(0,1),'W':(0,-1)}
# heading vectors; a vehicle travelling with heading h
LEFT = {'S':'E','N':'W','E':'N','W':'S'}
RIGHT = {'S':'W','N':'E','E':'S','W':'N'}

def build():
    links = {}  # key -> dict(n, to=(r,c) or None, heading)
    def ln(m): return int(round(m / C_M))
    for (r,c),m in H.items():
        links[('blk',(r,c),'E')] = dict(n=ln(m), to=(r,c+1), heading='E')
        links[('blk',(r,c+1),'W')] = dict(n=ln(m), to=(r,c), heading='W')
    for (r,c),m in Vb.items():
        links[('blk',(r,c),'S')] = dict(n=ln(m), to=(r+1,c), heading='S')
        links[('blk',(r+1,c),'N')] = dict(n=ln(m), to=(r,c), heading='N')
    term_in = {}
    for k in range(12):
        if k < 3: node, h = (0,k), 'S'
        elif k < 6: node, h = (k-3,2), 'W'
        elif k < 9: node, h = (2,k-6), 'N'
        else: node, h = (k-9,0), 'E'
        key = ('in', k)
        links[key] = dict(n=ln(IN[k]), to=node, heading=h)
        term_in[k] = key
    return links, term_in

def exit_link(links, node, heading):
    key = ('blk', node, heading)
    if key in links: return key
    key = ('out', node, heading)
    if key not in links: links[key] = dict(n=10, to=None, heading=heading)
    return key

def lcg(x): return (1103515245 * x + 12345) % (2**31)

def run(scen, C, plan, order, offs):
    links, term_in = build()
    for r in range(3):
        for c in range(3):
            for h in 'NSEW': exit_link(links, (r,c), h)
    g = GREENS[(C,plan)]
    seq = 'ABCD' if order == 'lead' else 'BADC'
    gl = dict(zip('ABCD', g))
    def phase_at(tau):
        t0 = 0
        for p in seq:
            if t0 <= tau < t0 + gl[p]: return p
            t0 += gl[p] + 2
        return None
    occ = {k: [None]*v['n'] for k,v in links.items()}
    gen = [1000 + 17*k for k in range(12)]
    queues = [[] for _ in range(12)]
    veh = []  # dict(born, y, move, link)
    tts = 0; end = 7199
    for t in range(7200):
        if t < 3600:
            for k in range(12):
                gen[k] = lcg(gen[k])
                if (gen[k] // 256) % 3600 < DEM[scen][k]:
                    v = len(veh)
                    veh.append(dict(born=t, y=(2654435761*v + 12345) % 2**31, move=None))
                    queues[k].append(v)
        # make sure all out links exist
        snap = {k: list(c) for k,c in occ.items()}
        moves = []
        for key, cells in snap.items():
            L = links[key]; n = L['n']
            for i, v in enumerate(cells):
                if v is None: continue
                if i < n-1:
                    if snap[key][i+1] is None: moves.append((v, key, i, key, i+1))
                elif L['to'] is None:
                    moves.append((v, key, i, None, None))
                else:
                    r, c = L['to']; j = r*3 + c
                    tau = (t - offs[j]) % C
                    ph = phase_at(tau)
                    m = veh[v]['move']; h = L['heading']
                    ns = h in 'NS'
                    need = ('B' if m == 'L' else 'A') if ns else ('D' if m == 'L' else 'C')
                    newh = h if m == 'T' else (LEFT[h] if m == 'L' else RIGHT[h])
                    nk = exit_link(links, (r,c), newh)
                    if nk not in occ: occ[nk] = [None]*10; snap[nk] = [None]*10
                    if ph == need and snap[nk][0] is None: moves.append((v, key, i, nk, 0))
        for k in range(12):
            if queues[k] and snap[term_in[k]][0] is None:
                moves.append((queues[k].pop(0), None, None, term_in[k], 0))
        for v, fk, fi, tk, ti in moves:
            if fk is not None: occ[fk][fi] = None
            if tk is None:
                tts += t - veh[v]['born'] + 1; veh[v]['gone'] = True
            else:
                occ[tk][ti] = v
                if ti == 0 and links[tk]['to'] is not None:
                    veh[v]['y'] = lcg(veh[v]['y']); r = (veh[v]['y'] // 65536) % 100
                    L, T = (20, 65) if links[tk]['heading'] in 'NS' else (10, 75)
                    veh[v]['move'] = 'L' if r < L else ('T' if r < L + T else 'R')
        if t >= 3599:
            if not any(queues) and all(all(c is None for c in cells) for cells in occ.values()):
                end = t; break
    if end == 7199:
        for v in veh:
            if not v.get('gone'): tts += 7200 - v['born']
    return tts, end, len(veh)

if __name__ == '__main__':
    scen = sys.argv[1]; C = int(sys.argv[2]); plan = int(sys.argv[3]); order = sys.argv[4]
    offs = [int(x) for x in sys.argv[5].split(',')]
    print(scen, run(scen, C, plan, order, offs))
