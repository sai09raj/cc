/* FIRE-15 prototype engine.  usage: cfire one s1,..,s6 | cfire bench N | cfire stats N */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "params.h"

#define NC (GW*GH)
#define MAXF 512
static unsigned lcg(unsigned x) { return (unsigned)((1103515245ULL * x + 12345ULL) & 0x7fffffffULL); }
static const int DX[8] = {0,1,1,1,0,-1,-1,-1}, DY[8] = {-1,-1,0,1,1,1,0,-1};

typedef struct { int loss, burned, houses, fires, end; } Res;

static Res run(int sc, const int *stn) {
    static int rem[NC], fid[NC], mark[NC]; static unsigned char burned[NC];
    int forig[MAXF], fign[MAXF], fasg[MAXF], fcnt[MAXF], nf = 0;
    int cpos[NCREW], cst[NCREW], cf[NCREW], carr[NCREW];
    memset(rem, 0, sizeof rem); memset(burned, 0, sizeof burned); memset(mark, 0, sizeof mark);
    for (int c = 0; c < NCREW; c++) { cpos[c] = ST[stn[c]][1] * GW + ST[stn[c]][0]; cst[c] = 0; }
    unsigned xl = SEED[sc], xs = SEED[sc] * 7u + 1u;
    int nburn = 0, t = 0, newl[NC], nn;
    for (;;) {
        if (t < T_LIGHT) {
            xl = lcg(xl);
            if ((int)((xl >> 8) % 1000) < RATE[sc]) {
                xl = lcg(xl); int X = (xl >> 8) % GW; xl = lcg(xl); int Y = (xl >> 8) % GH; int c = Y * GW + X;
                if (FUEL[c] && !rem[c] && !burned[c] && nf < MAXF) {
                    rem[c] = BURN[FUEL[c]]; fid[c] = nf; forig[nf] = c; fign[nf] = t; fasg[nf] = 0; fcnt[nf] = 1; nf++; nburn++;
                }
            }
        }
        int wd = WIND[sc][t / 60][0], ws = WIND[sc][t / 60][1];
        nn = 0;
        for (int c = 0; c < NC; c++) if (rem[c]) {
            int x = c % GW, y = c / GW;
            for (int d = 0; d < 8; d++) {
                int nx = x + DX[d], ny = y + DY[d];
                if (nx < 0 || ny < 0 || nx >= GW || ny >= GH) continue;
                int n = ny * GW + nx;
                if (!FUEL[n] || rem[n] || burned[n] || mark[n]) continue;
                int diff = abs(d - wd); if (diff > 4) diff = 8 - diff;
                int p = BASE[FUEL[n]] * WF[ws][diff] / 100; if (d & 1) p = p * DIAG / 100;
                xs = lcg(xs);
                if ((int)((xs >> 16) % 1000) < p) { mark[n] = 1; fid[n] = fid[c]; newl[nn++] = n; }
            }
        }
        for (int k = 0; k < NCREW; k++) {
            if (cst[k] == 1 && t >= carr[k]) { cst[k] = 2; cpos[k] = forig[cf[k]]; }
            if (cst[k] == 2) {
                for (int a = 0; a < CREW[k][1]; a++) {
                    int best = -1, bd = 1 << 30, px = cpos[k] % GW, py = cpos[k] / GW;
                    for (int c = 0; c < NC; c++) if (rem[c] && fid[c] == cf[k]) {
                        int dd = abs(c % GW - px) + abs(c / GW - py);
                        if (dd < bd) { bd = dd; best = c; }
                    }
                    if (best < 0) break;
                    rem[best] = 0; burned[best] = 1; fcnt[cf[k]]--; nburn--; cpos[k] = best;
                }
            }
        }
        for (int c = 0; c < NC; c++) if (rem[c]) { if (--rem[c] == 0) { burned[c] = 1; fcnt[fid[c]]--; nburn--; } }
        for (int i = 0; i < nn; i++) { int n = newl[i]; mark[n] = 0; rem[n] = BURN[FUEL[n]]; fcnt[fid[n]]++; nburn++; }
        for (int k = 0; k < NCREW; k++) if (cst[k] == 2 && fcnt[cf[k]] == 0) cst[k] = 0;
        for (int f = 0; f < nf; f++) if (!fasg[f] && t >= fign[f] + DET && fcnt[f] > 0) {
            int bk = -1, bt = 1 << 30, ox = forig[f] % GW, oy = forig[f] / GW;
            for (int k = 0; k < NCREW; k++) if (cst[k] == 0) {
                int dist = abs(cpos[k] % GW - ox) + abs(cpos[k] / GW - oy);
                int tt = (dist + CREW[k][0] - 1) / CREW[k][0];
                if (tt < bt) { bt = tt; bk = k; }
            }
            if (bk < 0) break;
            fasg[f] = 1; cst[bk] = 1; cf[bk] = f; carr[bk] = t + 1 + bt;
        }
        t++;
        if (t >= T_END || (t >= T_LIGHT && nburn == 0)) break;
    }
    Res r = {0, 0, 0, nf, t};
    for (int c = 0; c < NC; c++) if (burned[c] || rem[c]) { r.burned++; if (FUEL[c] == 4) r.houses++; }
    r.loss = r.burned + HOUSE_W * r.houses;
    return r;
}

int main(int argc, char **argv) {
    if (argc >= 3 && !strcmp(argv[1], "one")) {
        int s[NCREW]; char *p = argv[2];
        for (int k = 0; k < NCREW; k++) { s[k] = (int)strtol(p, &p, 10) - 1; if (*p == ',') p++; }
        int tot = 0;
        for (int sc = 0; sc < 3; sc++) { Res r = run(sc, s); tot += r.loss; printf("%c: loss %d burned %d houses %d fires %d end %d | ", 'A' + sc, r.loss, r.burned, r.houses, r.fires, r.end); }
        printf("total %d\n", tot); return 0;
    }
    if (argc >= 3 && (!strcmp(argv[1], "bench") || !strcmp(argv[1], "stats"))) {
        int n = atoi(argv[2]); unsigned s = 99; clock_t c0 = clock(); long long acc = 0; int mn = 1 << 30, mx = 0;
        for (int i = 0; i < n; i++) {
            int st[NCREW]; for (int k = 0; k < NCREW; k++) { s = lcg(s); st[k] = (s >> 8) % NST; }
            int tot = 0; for (int sc = 0; sc < 3; sc++) tot += run(sc, st).loss;
            acc += tot; if (tot < mn) mn = tot; if (tot > mx) mx = tot;
            if (!strcmp(argv[1], "stats") && i < 20) printf("%d\n", tot);
        }
        printf("%.3f ms/config  mean %.1f min %d max %d\n", 1000.0 * (clock() - c0) / CLOCKS_PER_SEC / n, (double)acc / n, mn, mx);
    }
    return 0;
}
