/* FIRE-15 fast engine (bit-row scan, per-fire cell lists).  usage: ffast one s1,..,sK | ffast bench N */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include "params.h"

#define NC (GW*GH)
#define WPR (GW/64)
#define MAXF 1024
static inline unsigned lcg(unsigned x) { return (unsigned)((1103515245ULL * x + 12345ULL) & 0x7fffffffULL); }
static const int DX[8] = {0,1,1,1,0,-1,-1,-1}, DY[8] = {-1,-1,0,1,1,1,0,-1};
static int PT[5][3][8][5];   /* p[fuel][speed][dir][diff] */
static int NB[NC][8];

typedef struct { int loss, burned, houses, fires, end; } Res;

static void init(void) {
    for (int f = 1; f < 5; f++) for (int s = 0; s < 3; s++) for (int d = 0; d < 8; d++) for (int df = 0; df < 5; df++) {
        int p = BASE[f] * WF[s][df] / 100; if (d & 1) p = p * DIAG / 100; PT[f][s][d][df] = p; }
    for (int c = 0; c < NC; c++) for (int d = 0; d < 8; d++) {
        int nx = c % GW + DX[d], ny = c / GW + DY[d];
        NB[c][d] = (nx < 0 || ny < 0 || nx >= GW || ny >= GH || !FUEL[ny * GW + nx]) ? -1 : ny * GW + nx; }
}

static int ndisp[NCREW];
static Res run(int sc, const int *stn) {
    static unsigned char rem[NC], state[NC]; static int fid[NC];   /* state 0 unburned 1 burning/marked 2 done */
    static uint64_t brow[GH][WPR];
    int forig[MAXF], fign[MAXF], fasg[MAXF], fcnt[MAXF], nf = 0;
    int cpos[NCREW], cst[NCREW], cf[NCREW], carr[NCREW], home[NCREW];
    memset(state, 0, sizeof state); memset(rem, 0, sizeof rem); memset(brow, 0, sizeof brow);
    for (int k = 0; k < NCREW; k++) { home[k] = ST[stn[k]][1] * GW + ST[stn[k]][0]; cpos[k] = home[k]; cst[k] = 0; }
    unsigned xl = SEED[sc], xs = SEED[sc] * 7u + 1u;
    int nburn = 0, t = 0, nn; static int newl[NC];
    for (;;) {
        if (t < T_LIGHT) {
            xl = lcg(xl);
            if ((int)((xl >> 8) % 1000) < RATE[sc]) {
                xl = lcg(xl); int X = (xl >> 8) % GW; xl = lcg(xl); int Y = (xl >> 8) % GH; int c = Y * GW + X;
                if (FUEL[c] && !state[c] && nf < MAXF) {
                    state[c] = 1; rem[c] = BURN[FUEL[c]]; fid[c] = nf; brow[Y][X >> 6] |= 1ULL << (X & 63);
                    forig[nf] = c; fign[nf] = t; fasg[nf] = 0; fcnt[nf] = 1; nf++; nburn++;
                }
            }
        }
        int wd = WIND[sc][t / PERIOD][0], ws = WIND[sc][t / PERIOD][1];
        nn = 0;
        if (nburn) for (int y = 0; y < GH; y++) for (int w = 0; w < WPR; w++) {
            uint64_t m = brow[y][w];
            while (m) {
                int b = __builtin_ctzll(m); m &= m - 1; int c = y * GW + w * 64 + b;
                for (int d = 0; d < 8; d++) {
                    int n = NB[c][d]; if (n < 0 || state[n]) continue;
                    int df = d > wd ? d - wd : wd - d; if (df > 4) df = 8 - df;
                    xs = lcg(xs);
                    if ((int)((xs >> 16) % 1000) < PT[FUEL[n]][ws][d][df]) { state[n] = 1; fid[n] = fid[c]; newl[nn++] = n; }
                }
            }
        }
        for (int k = 0; k < NCREW; k++) {
            if (cst[k] == 1 && t >= carr[k]) { cst[k] = 2; cpos[k] = forig[cf[k]]; }
            else if (cst[k] == 3 && t >= carr[k]) { cst[k] = 0; cpos[k] = home[k]; }
            if (cst[k] == 2) {
                int f = cf[k];
                for (int a = 0; a < CREW[k][1] && fcnt[f] > 0; a++) {
                    int best = -1, bd = 1 << 30, px = cpos[k] % GW, py = cpos[k] / GW;
                    for (int y = 0; y < GH; y++) {
                        int dy = abs(y - py); if (dy > bd) { if (y > py) break; else continue; }
                        for (int w = 0; w < WPR; w++) { uint64_t m = brow[y][w];
                            while (m) { int b = __builtin_ctzll(m); m &= m - 1; int c = y * GW + w * 64 + b;
                                if (fid[c] != f) continue; int dd = dy + abs(w * 64 + b - px); if (dd < bd) { bd = dd; best = c; } } }
                    }
                    int bx = best % GW, by = best / GW;
                    brow[by][bx >> 6] &= ~(1ULL << (bx & 63)); state[best] = 2; rem[best] = 0; fcnt[f]--; nburn--; cpos[k] = best;
                }
            }
        }
        for (int y = 0; y < GH; y++) for (int w = 0; w < WPR; w++) { uint64_t m = brow[y][w];
            while (m) { int b = __builtin_ctzll(m); m &= m - 1; int c = y * GW + w * 64 + b;
                if (--rem[c] == 0) { state[c] = 2; brow[y][w] &= ~(1ULL << b); fcnt[fid[c]]--; nburn--; } } }
        for (int i = 0; i < nn; i++) { int n = newl[i]; rem[n] = BURN[FUEL[n]]; brow[n / GW][(n % GW) >> 6] |= 1ULL << (n % GW & 63); fcnt[fid[n]]++; nburn++; }
        for (int k = 0; k < NCREW; k++) if ((cst[k] == 2 || cst[k] == 1) && fcnt[cf[k]] == 0 && cst[k] == 2) {
            int d = abs(cpos[k] % GW - home[k] % GW) + abs(cpos[k] / GW - home[k] / GW);
            cst[k] = 3; carr[k] = t + 1 + (d + CREW[k][0] - 1) / CREW[k][0]; }
        for (int f = 0; f < nf; f++) if (!fasg[f] && t >= fign[f] + DET && fcnt[f] > 0) {
            int bk = -1, bt = 1 << 30, ox = forig[f] % GW, oy = forig[f] / GW;
            for (int k = 0; k < NCREW; k++) if (cst[k] == 0) {
                int dist = abs(home[k] % GW - ox) + abs(home[k] / GW - oy), tt = (dist + CREW[k][0] - 1) / CREW[k][0];
                if (tt < bt) { bt = tt; bk = k; } }
            if (bk < 0) break;
            fasg[f] = 1; ndisp[bk]++; cst[bk] = 1; cf[bk] = f; carr[bk] = t + 1 + bt;
        }
        t++;
        if (t >= T_END || (t >= T_LIGHT && nburn == 0)) break;
    }
    Res r = {0, 0, 0, nf, t};
    for (int c = 0; c < NC; c++) if (state[c]) { r.burned++; if (FUEL[c] == 4) r.houses++; }
    r.loss = r.burned + HOUSE_W * r.houses;
    return r;
}

int main(int argc, char **argv) {
    init();
    if (argc >= 3 && !strcmp(argv[1], "one")) {
        int s[NCREW]; char *p = argv[2];
        for (int k = 0; k < NCREW; k++) { s[k] = (int)strtol(p, &p, 10) - 1; if (*p == ',') p++; }
        int tot = 0;
        for (int sc = 0; sc < NSC; sc++) { Res r = run(sc, s); tot += r.loss; printf("%c: loss %d burned %d houses %d fires %d end %d | ", 'A' + sc, r.loss, r.burned, r.houses, r.fires, r.end); }
        printf("total %d\n", tot); return 0;
    }
    if (argc >= 6 && !strcmp(argv[1], "chunk")) {
        /* chunk s1 s2 bA,bB,bC,bD outfile : all plans with crew 1 at station s1 and crew 2 at s2 (1-based) */
        int s1 = atoi(argv[2]) - 1, s2 = atoi(argv[3]) - 1; long long bs[NSC], base = 0; char *p = argv[4];
        for (int k = 0; k < NSC; k++) { bs[k] = strtoll(p, &p, 10); if (*p == ',') p++; base += bs[k]; }
        long long n = 0, sum = 0, sumsc[NSC] = {0}, sumh = 0, below = 0, below_all = 0, mn = -1, mx = 0;
        static long long below_by[NCREW][NST], sum_by[NCREW][NST]; static int hist[4000];
        long long topv[20]; long long topk[20]; int nt = 0;
        int rest = 1; for (int k = 2; k < NCREW; k++) rest *= NST;
        int lim = getenv("LIMIT") ? atoi(getenv("LIMIT")) : rest;
        for (int r = 0; r < lim; r++) {
            int st[NCREW]; st[0] = s1; st[1] = s2; int q = r;
            for (int k = NCREW - 1; k >= 2; k--) { st[k] = q % NST; q /= NST; }
            long long tot = 0; int all = 1;
            for (int sc = 0; sc < NSC; sc++) { Res x = run(sc, st); tot += x.loss; sumsc[sc] += x.loss; sumh += x.houses; if (x.loss >= bs[sc]) all = 0; }
            n++; sum += tot; if (tot < base) below++; if (all) below_all++;
            for (int k = 0; k < NCREW; k++) { sum_by[k][st[k]] += tot; if (tot < base) below_by[k][st[k]]++; }
            if (mn < 0 || tot < mn) mn = tot; if (tot > mx) mx = tot;
            long long b = tot / 100; if (b >= 4000) b = 3999; hist[b]++;
            long long key = ((long long)s1 * NST + s2) * rest + r;
            int pos = nt < 20 ? nt : 20;
            while (pos > 0 && topv[pos - 1] > tot) pos--;
            if (pos < 20) { int last = nt < 20 ? nt : 19; for (int k = last; k > pos; k--) { topv[k] = topv[k - 1]; topk[k] = topk[k - 1]; }
                topv[pos] = tot; topk[pos] = key; if (nt < 20) nt++; }
        }
        char tmp[600]; snprintf(tmp, sizeof tmp, "%s.part", argv[5]);
        FILE *f = fopen(tmp, "w");
        fprintf(f, "{\"s1\":%d,\"s2\":%d,\"n\":%lld,\"sum\":%lld,\"sum_sc\":[%lld,%lld,%lld,%lld],\"sum_houses\":%lld,\"below\":%lld,\"below_all\":%lld,\"min\":%lld,\"max\":%lld,",
                s1 + 1, s2 + 1, n, sum, sumsc[0], sumsc[1], sumsc[2], sumsc[3], sumh, below, below_all, mn, mx);
        fprintf(f, "\"below_by\":["); for (int k = 0; k < NCREW; k++) { fprintf(f, "%s[", k ? "," : ""); for (int s = 0; s < NST; s++) fprintf(f, "%s%lld", s ? "," : "", below_by[k][s]); fprintf(f, "]"); }
        fprintf(f, "],\"sum_by\":["); for (int k = 0; k < NCREW; k++) { fprintf(f, "%s[", k ? "," : ""); for (int s = 0; s < NST; s++) fprintf(f, "%s%lld", s ? "," : "", sum_by[k][s]); fprintf(f, "]"); }
        fprintf(f, "],\"top\":["); for (int k = 0; k < nt; k++) fprintf(f, "%s[%lld,%lld]", k ? "," : "", topv[k], topk[k]);
        fprintf(f, "],\"hist100\":{"); int first = 1;
        for (int b = 0; b < 4000; b++) if (hist[b]) { fprintf(f, "%s\"%d\":%d", first ? "" : ",", b, hist[b]); first = 0; }
        fprintf(f, "}}\n"); fclose(f); rename(tmp, argv[5]);
        return 0;
    }
    if (argc >= 3 && !strcmp(argv[1], "sample")) {   /* print totals of N random configs */
        int n = atoi(argv[2]); unsigned s = 12345;
        for (int i = 0; i < n; i++) { int st[NCREW]; for (int k = 0; k < NCREW; k++) { s = lcg(s); st[k] = (s >> 8) % NST; }
            int tot = 0; for (int sc = 0; sc < NSC; sc++) tot += run(sc, st).loss; printf("%d\n", tot); }
        return 0;
    }
    if (argc >= 3 && !strcmp(argv[1], "bench")) {
        int n = atoi(argv[2]); unsigned s = 99; clock_t c0 = clock(); long long acc = 0; int mn = 1 << 30, mx = 0;
        static int hist[64]; int never = 0, mind = 1 << 30;
        for (int i = 0; i < n; i++) {
            int st[NCREW]; for (int k = 0; k < NCREW; k++) { s = lcg(s); st[k] = (s >> 8) % NST; }
            memset(ndisp, 0, sizeof ndisp);
            int tot = 0; for (int sc = 0; sc < NSC; sc++) tot += run(sc, st).loss;
            for (int k = 0; k < NCREW; k++) { if (!ndisp[k]) never++; if (ndisp[k] < mind) mind = ndisp[k]; }
            acc += tot; if (tot < mn) mn = tot; if (tot > mx) mx = tot;
        }
        printf("%.3f ms/config  mean %.1f min %d max %d  crew-never-dispatched %d  min dispatches %d\n", 1000.0 * (clock() - c0) / CLOCKS_PER_SEC / n, (double)acc / n, mn, mx, never, mind);
    }
    return 0;
}
