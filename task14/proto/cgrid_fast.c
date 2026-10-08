/* GRID-14 fast engine (C). Same semantics as grid_ref.py.
   usage: cgrid one C plan o0,o1,...,o8        -> tts generated exited end
          cgrid bench N                         -> timing over N pseudo-random configurations */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "params.h"

#define NL 60
#define MAXV 20000
#define MAXC 64
typedef struct { int n, kind, to, to_side; } Link;   /* kind 0 internal, 1 entry, 2 exit */
static Link LK[NL];
static int OUTL[9][4], ENTRYL[12];
static int cells[NL][MAXC];
static int vgen[MAXV], vexit[MAXV], vmv[MAXV], vstamp[MAXV];
static unsigned vst[MAXV];
static int queue_[12][MAXV], qh[12], qt[12];
static unsigned char gmask[9][128];

static unsigned lcg(unsigned x) { return (unsigned)((1103515245ULL * x + 12345ULL) & 0x7fffffffULL); }

static void build(void) {
    int nl = 0;
    for (int r = 0; r < 3; r++) for (int c = 0; c < 2; c++) {
        int L = L_EW[r][c], a = 3 * r + c, b = a + 1;
        LK[nl] = (Link){L, 0, b, 3}; OUTL[a][1] = nl++;
        LK[nl] = (Link){L, 0, a, 1}; OUTL[b][3] = nl++;
    }
    for (int r = 0; r < 2; r++) for (int c = 0; c < 3; c++) {
        int L = L_NS[r][c], a = 3 * r + c, b = a + 3;
        LK[nl] = (Link){L, 0, b, 0}; OUTL[a][2] = nl++;
        LK[nl] = (Link){L, 0, a, 2}; OUTL[b][0] = nl++;
    }
    for (int k = 0; k < 12; k++) {
        int j, s;
        if (k < 3) { j = k; s = 0; } else if (k < 6) { j = 3 * (k - 3) + 2; s = 1; }
        else if (k < 9) { j = 6 + (k - 6); s = 2; } else { j = 3 * (k - 9); s = 3; }
        LK[nl] = (Link){L_ENTRY[k], 1, j, s}; ENTRYL[k] = nl++;
        LK[nl] = (Link){L_EXIT, 2, -1, -1}; OUTL[j][s] = nl++;
    }
}

/* movement codes: 0 L, 1 T, 2 R */
static int turn(int v, int side) {
    const int *p = (side == 0 || side == 2) ? TURN_NS : TURN_EW;
    vst[v] = lcg(vst[v]);
    int r = (vst[v] >> 16) % 100;
    return r < p[0] ? 0 : (r < p[0] + p[1] ? 1 : 2);
}

typedef struct { long long tts; int gen, exited, end; } Res;


static int lv[NL][MAXV > 4096 ? 4096 : MAXV];   /* ring of vehicle ids per link, front = downstream */
static int lpos[MAXV];                           /* cell position of each vehicle */
static int lfront[NL], lcount[NL];
#define RING 4096
static Res run(int ci, int plan, const int *off, int lag, int sc) {
    int C = CYCLES[ci];
    const int *g = GREEN[ci][plan];
    unsigned char ph[128];
    int x = 0;
    for (int t = 0; t < C; t++) ph[t] = 0;
    static const int ORD[2][4] = {{0, 1, 2, 3}, {1, 0, 3, 2}};
    for (int q = 0; q < 4; q++) {
        int p = ORD[lag][q];
        for (int t = x; t < x + g[p]; t++) ph[t] = (unsigned char)(1 << p);
        x += g[p] + ALL_RED;
    }
    for (int l = 0; l < NL; l++) { lfront[l] = 0; lcount[l] = 0; }
    unsigned ts[12];
    for (int k = 0; k < 12; k++) { ts[k] = 1000 + 17 * k; qh[k] = qt[k] = 0; }
    int nv = 0, exited = 0, t = 0, head0[NL], inside = 0;
    for (;;) {
        if (t < T_GEN)
            for (int k = 0; k < 12; k++) {
                ts[k] = lcg(ts[k]);
                if ((int)((ts[k] >> 8) % 3600) < DEMAND[sc][k]) {
                    vgen[nv] = t; vexit[nv] = -1; vstamp[nv] = -1;
                    vst[nv] = (unsigned)(((unsigned long long)nv * 2654435761ULL + 12345ULL) & 0x7fffffffULL);
                    queue_[k][qt[k]++] = nv; nv++;
                }
            }
        for (int l = 0; l < NL; l++)
            head0[l] = lcount[l] && lpos[lv[l][(lfront[l] + lcount[l] - 1) & (RING - 1)]] == 0;
        int tau[9];
        for (int j = 0; j < 9; j++) { int q = (t - off[j]) % C; if (q < 0) q += C; tau[j] = q; }
        for (int l = 0; l < NL; l++) {
            int cnt = lcount[l]; if (!cnt) continue;
            int n = LK[l].n, f = lfront[l];
            int prev_start = 1 << 30;     /* start position of the vehicle ahead */
            int removed = 0;
            for (int k = 0; k < cnt; k++) {
                int v = lv[l][(f + k) & (RING - 1)];
                int p = lpos[v];
                if (vstamp[v] == t) { prev_start = p; continue; }
                if (k == 0 && p == n - 1) {
                    if (LK[l].kind == 2) { vexit[v] = t; exited++; vstamp[v] = t; removed = 1; inside--; }
                    else {
                        int j = LK[l].to, s = LK[l].to_side, mv = vmv[v];
                        int d = mv == 1 ? (s + 2) & 3 : (mv == 2 ? (s + 3) & 3 : (s + 1) & 3);
                        int dl = OUTL[j][d];
                        unsigned char m = ph[tau[j]];
                        int ns = (s == 0 || s == 2);
                        int green = ns ? ((mv == 0) ? (m & 2) : (m & 1)) : ((mv == 0) ? (m & 8) : (m & 4));
                        if (green && !head0[dl]) {
                            removed = 1; vstamp[v] = t; lpos[v] = 0;
                            lv[dl][(lfront[dl] + lcount[dl]) & (RING - 1)] = v; lcount[dl]++;
                            if (LK[dl].kind == 0) vmv[v] = turn(v, LK[dl].to_side);
                        }
                    }
                    prev_start = p;
                } else {
                    if (p + 1 < prev_start) { lpos[v] = p + 1; vstamp[v] = t; }
                    prev_start = p;
                }
            }
            if (removed) { lfront[l] = (f + 1) & (RING - 1); lcount[l]--; }
        }
        for (int k = 0; k < 12; k++) {
            int el = ENTRYL[k];
            if (qh[k] < qt[k] && !head0[el]) {
                int v = queue_[k][qh[k]++];
                lpos[v] = 0; vstamp[v] = t; vmv[v] = turn(v, LK[el].to_side);
                lv[el][(lfront[el] + lcount[el]) & (RING - 1)] = v; lcount[el]++; inside++;
            }
        }
        t++;
        if ((t >= T_GEN && exited == nv) || t >= CAP) break;
    }
    Res r; r.tts = 0;
    for (int v = 0; v < nv; v++) r.tts += vexit[v] >= 0 ? (vexit[v] - vgen[v] + 1) : (CAP - vgen[v]);
    r.gen = nv; r.exited = exited; r.end = t;
    return r;
}

int main(int argc, char **argv) {
    build();
    if (argc >= 5 && !strcmp(argv[1], "one")) {
        int C = atoi(argv[2]), plan = atoi(argv[3]), off[9], ci = -1;
        for (int i = 0; i < NCYC; i++) if (CYCLES[i] == C) ci = i;
        char *p = argv[4];
        for (int j = 0; j < 9; j++) { off[j] = (int)strtol(p, &p, 10); if (*p == ',') p++; }
        int lag = argc > 5 && !strcmp(argv[5], "lag");
        long long tot = 0;
        for (int sc = 0; sc < 3; sc++) {
            Res r = run(ci, plan, off, lag, sc); tot += r.tts;
            printf("%lld %d %d %d | ", r.tts, r.gen, r.exited, r.end);
        }
        printf("total %lld\n", tot);
        return 0;
    }

    if (argc >= 9 && !strcmp(argv[1], "chunk")) {
        /* chunk C plan lag oi_lo oi_hi baseline_total outfile */
        int C = atoi(argv[2]), plan = atoi(argv[3]), ci = -1, LAG = atoi(argv[4]), LO = atoi(argv[5]), HI = atoi(argv[6]);
        long long base = atoll(argv[7]);
        for (int i = 0; i < NCYC; i++) if (CYCLES[i] == C) ci = i;
        long long sum = 0, sumsc[3] = {0, 0, 0}, mn = -1, mx = 0; long long below = 0, grid = 0, n = 0;
        static int hist[70000]; memset(hist, 0, sizeof hist);
        long long topv[20]; int topk[20]; int nt = 0;
        for (int lag = LAG; lag == LAG; lag++) for (int oi = LO; oi < HI; oi++) {
            int off[9];
            for (int j = 0; j < 9; j++) off[j] = ((oi >> (2 * (8 - j))) & 3) * C / 4;
            long long tot = 0; int gl = 0;
            for (int sc = 0; sc < 3; sc++) { Res r = run(ci, plan, off, lag, sc); tot += r.tts; sumsc[sc] += r.tts; if (r.end >= CAP && r.exited < r.gen) gl = 1; }
            n++; sum += tot; if (tot < base) below++; if (gl) grid++;
            if (mn < 0 || tot < mn) mn = tot; if (tot > mx) mx = tot;
            long long b = tot / 1000; if (b >= 70000) b = 69999; hist[b]++;
            int key = lag * 262144 + oi;
            int pos = nt < 20 ? nt : 20;
            while (pos > 0 && topv[pos - 1] > tot) pos--;   /* strict: earlier key wins ties (iteration order is the tie-break order) */
            if (pos < 20) {
                int last = nt < 20 ? nt : 19;
                for (int k = last; k > pos; k--) { topv[k] = topv[k - 1]; topk[k] = topk[k - 1]; }
                topv[pos] = tot; topk[pos] = key; if (nt < 20) nt++;
            }
        }
        char tmp[600]; snprintf(tmp, sizeof tmp, "%s.part", argv[8]);
        FILE *f = fopen(tmp, "w");
        fprintf(f, "{\"lag\":%d,\"lo\":%d,\"hi\":%d,\"C\":%d,\"plan\":%d,\"n\":%lld,\"sum\":%lld,\"sum_AM\":%lld,\"sum_PM\":%lld,\"sum_EVENT\":%lld,\"below\":%lld,\"gridlock\":%lld,\"min\":%lld,\"max\":%lld,\"top\":[",
                LAG, LO, HI, C, plan, n, sum, sumsc[0], sumsc[1], sumsc[2], below, grid, mn, mx);
        for (int k = 0; k < nt; k++) fprintf(f, "%s[%lld,%d]", k ? "," : "", topv[k], topk[k]);
        fprintf(f, "],\"hist1000\":{");
        int first = 1;
        for (int b = 0; b < 70000; b++) if (hist[b]) { fprintf(f, "%s\"%d\":%d", first ? "" : ",", b, hist[b]); first = 0; }
        fprintf(f, "}}\n"); fclose(f); rename(tmp, argv[8]);
        return 0;
    }
    if (argc >= 3 && !strcmp(argv[1], "bench")) {
        int n = atoi(argv[2]); unsigned s = 7; long long acc = 0;
        clock_t c0 = clock();
        for (int i = 0; i < n; i++) {
            int off[9]; s = lcg(s); int ci = s % NCYC; s = lcg(s); int plan = s % 6;
            for (int j = 0; j < 9; j++) { s = lcg(s); off[j] = (s >> 8) % 4 * CYCLES[ci] / 4; }
            s = lcg(s); int lag = s & 1;
            for (int sc = 0; sc < 3; sc++) acc += run(ci, plan, off, lag, sc).tts;
        }
        printf("%.3f ms per config  (acc %lld)\n", 1000.0 * (clock() - c0) / CLOCKS_PER_SEC / n, acc);
        return 0;
    }
    fprintf(stderr, "usage\n"); return 1;
}
