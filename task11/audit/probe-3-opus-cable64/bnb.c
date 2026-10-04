/* Exact branch-and-bound for the non-crossing capacitated cable-tree problem.
 *
 * LP relaxation: capacity-indexed (load-indexed) arc formulation.
 *   x[a][q] in {0,1}: directed arc a=(i->j) carries load exactly q (1..Qa)
 *   (R1) for every turbine i:   sum_{a out of i, q} x = 1
 *   (R2) for every turbine i:   sum_{a out of i, q} q x - sum_{a into i, q} q x = 1
 *   (R3) sum_{root arcs, q} x <= K
 *   (R4) for every clique C of pairwise-crossing undirected edges: sum_{e in C, both dirs, q} x <= 1
 *   (R5) for undirected turbine edges in no clique: both directions <= 1
 *   cost(x[a][q]) = len(a) * price(q)   (price of cheapest admissible type)
 *   Lazy cuts (R6), separated at every node:  x[a][q]-aggregate ... see separate_cuts().
 * Solved with a bounded dual simplex (dense explicit basis inverse, periodic refactorisation).
 * Every node bound is recomputed in a numerically safe way from the dual vector
 * (weak duality with box bounds), so pruning does not rely on simplex accuracy.
 * Branching: on a directed arc (fix to 1 => all other arcs out of i, the reverse arc and all
 * crossing arcs fixed to 0; fix to 0 => all its load-variables fixed to 0).
 * A node whose arc aggregate is integral is a complete tree; its exact cost is evaluated.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define INF 1e30
static int n, K, Q, UBin;
static int price[64];
static int nE; static int *Ei, *Ej, *Elen;
static int nCl; static int **Cl; static int *Clsz;
/* arcs */
static int nA; static int *Ai, *Aj, *Ae, *Alen, *Aq; static int *Acol0; /* first column of arc */
/* columns */
static int ncol; static int *colA, *colQ;
/* sparse column storage (structural) */
static int *cbeg, *cnt_; static int *crow; static double *cval;
static int nnzcap, nnz;
/* rows */
static int m, mcap; static double *b; static int *rtype; /* 0: '=', 1: '<=' */
/* all vars: 0..ncol-1 structural, ncol+r slack of row r */
static double *lb, *ub, *cost, *x, *d;
static int *head, *pos, *atub;
static double *Binv; /* mcap x mcap row-major */
static int nvar_cap;
static double tol_p = 1e-7, tol_d = 1e-9;
static long long total_iters = 0;
static double cutoff = INF;
static clock_t t0;

static int out_cnt[70]; static int *out_arcs[70]; static int in_cnt[70]; static int *in_arcs[70];

/* lazy cut rows: each is a list of (col, coef) entries (stored in columns too) */
#define VARIDX_SLACK(r) (ncol + (r))

static void die(const char *s) { fprintf(stderr, "%s\n", s); exit(1); }

/* Column structure: since we add rows, each structural column stores entries in a
 * per-column dynamic array. */
static int **colrows; static double **colvals; static int *colnz, *colcap;
static void col_add(int j, int r, double v) {
    if (colnz[j] == colcap[j]) {
        colcap[j] = colcap[j] ? 2 * colcap[j] : 4;
        colrows[j] = realloc(colrows[j], colcap[j] * sizeof(int));
        colvals[j] = realloc(colvals[j], colcap[j] * sizeof(double));
    }
    colrows[j][colnz[j]] = r; colvals[j][colnz[j]] = v; colnz[j]++;
}

/* dot of row vector (length m) with column j of [A I] */
static inline double dotcol(const double *rho, int j) {
    if (j >= ncol) return rho[j - ncol];
    double s = 0; int k;
    for (k = 0; k < colnz[j]; k++) s += rho[colrows[j][k]] * colvals[j][k];
    return s;
}

static double *Bmat, *work, *work2, *rho_buf, *alpha_r, *alpha_q, *ybuf;

static int refactor(void) {
    /* build B and invert with Gauss-Jordan partial pivoting */
    int i, j, k;
    for (i = 0; i < m * m; i++) Bmat[i] = 0;
    for (k = 0; k < m; k++) {
        int v = head[k];
        if (v >= ncol) Bmat[(v - ncol) * m + k] = 1.0;
        else for (j = 0; j < colnz[v]; j++) Bmat[colrows[v][j] * m + k] = colvals[v][j];
    }
    /* Binv = I */
    for (i = 0; i < m; i++) for (j = 0; j < m; j++) Binv[i * m + j] = (i == j);
    for (k = 0; k < m; k++) {
        int p = k; double best = fabs(Bmat[k * m + k]);
        for (i = k + 1; i < m; i++) if (fabs(Bmat[i * m + k]) > best) { best = fabs(Bmat[i * m + k]); p = i; }
        if (best < 1e-11) return -1;
        if (p != k) {
            for (j = 0; j < m; j++) { double t = Bmat[k*m+j]; Bmat[k*m+j] = Bmat[p*m+j]; Bmat[p*m+j] = t;
                                      t = Binv[k*m+j]; Binv[k*m+j] = Binv[p*m+j]; Binv[p*m+j] = t; }
        }
        double piv = Bmat[k * m + k];
        for (j = 0; j < m; j++) { Bmat[k*m+j] /= piv; Binv[k*m+j] /= piv; }
        for (i = 0; i < m; i++) if (i != k) {
            double f = Bmat[i * m + k];
            if (f != 0) {
                double *bi = Bmat + i*m, *bk = Bmat + k*m, *vi = Binv + i*m, *vk = Binv + k*m;
                for (j = 0; j < m; j++) { bi[j] -= f * bk[j]; vi[j] -= f * vk[j]; }
            }
        }
    }
    return 0;
}

static void compute_primal(void) {
    int i, j, k;
    for (i = 0; i < m; i++) work[i] = b[i];
    for (j = 0; j < ncol + m; j++) if (pos[j] < 0) {
        if (x[j] != 0) {
            if (j >= ncol) work[j - ncol] -= x[j];
            else for (k = 0; k < colnz[j]; k++) work[colrows[j][k]] -= colvals[j][k] * x[j];
        }
    }
    for (i = 0; i < m; i++) {
        double s = 0; double *bi = Binv + i * m;
        for (k = 0; k < m; k++) s += bi[k] * work[k];
        x[head[i]] = s;
    }
}

static void compute_duals(void) {
    int i, k, j;
    for (k = 0; k < m; k++) ybuf[k] = 0;
    for (i = 0; i < m; i++) {
        double c = cost[head[i]];
        if (c != 0) { double *bi = Binv + i * m; for (k = 0; k < m; k++) ybuf[k] += c * bi[k]; }
    }
    for (j = 0; j < ncol + m; j++) d[j] = (pos[j] >= 0) ? 0 : cost[j] - dotcol(ybuf, j);
}

/* put nonbasic vars on the bound that keeps them dual feasible */
static void fix_status(void) {
    int j;
    for (j = 0; j < ncol + m; j++) if (pos[j] < 0) {
        if (ub[j] >= INF) { atub[j] = 0; x[j] = lb[j]; }
        else if (lb[j] == ub[j]) { atub[j] = 0; x[j] = lb[j]; }
        else if (d[j] < 0) { atub[j] = 1; x[j] = ub[j]; }
        else { atub[j] = 0; x[j] = lb[j]; }
    }
}

static double objective(void) { double s = 0; int j; for (j = 0; j < ncol; j++) s += cost[j] * x[j]; return s; }

/* safe lower bound from the current dual vector y (ybuf): weak duality with box constraints */
static double safe_bound(void) {
    int r, j; double s = 0;
    static double *yy = NULL; static int yycap = 0;
    if (yycap < mcap) { yy = realloc(yy, mcap * sizeof(double)); yycap = mcap; }
    for (r = 0; r < m; r++) { yy[r] = ybuf[r]; if (rtype[r] == 1 && yy[r] > 0) yy[r] = 0; s += b[r] * yy[r]; }
    for (j = 0; j < ncol; j++) {
        double dj = cost[j] - dotcol(yy, j);
        s += (dj < 0) ? dj * ub[j] : dj * lb[j];
    }
    return s;
}

/* dual simplex. returns 0 optimal, 1 infeasible, 2 cutoff reached, 3 numerical trouble */
static int need_refactor = 1;
static int dual_simplex(void) {
    int it = 0, since = 0;
    if (need_refactor) { if (refactor()) return 3; need_refactor = 0; }
    compute_duals(); fix_status(); compute_primal();
    for (;;) {
        int r = -1, i, j; double maxinf = tol_p;
        for (i = 0; i < m; i++) {
            int v = head[i]; double inf = 0;
            if (x[v] < lb[v] - tol_p) inf = lb[v] - x[v];
            else if (x[v] > ub[v] + tol_p) inf = x[v] - ub[v];
            if (inf > maxinf) { maxinf = inf; r = i; }
        }
        if (r < 0) return 0;
        if ((it & 31) == 0 && cutoff < INF) {
            double z = safe_bound();
            if (z > cutoff) return 2;
        }
        int leave = head[r];
        int toLower = x[leave] < lb[leave];
        double *rho = Binv + r * m;
        /* Harris two-pass ratio test */
        double thmax = INF;
        for (j = 0; j < ncol + m; j++) {
            if (pos[j] >= 0) { alpha_r[j] = 0; continue; }
            if (lb[j] == ub[j]) { alpha_r[j] = 0; continue; }
            double a = dotcol(rho, j); alpha_r[j] = a;
            if (fabs(a) < 1e-9) continue;
            double ratio = INF;
            if (toLower) {
                if (!atub[j] && a < 0) ratio = (d[j] + tol_d) / (-a);
                else if (atub[j] && a > 0) ratio = (-d[j] + tol_d) / a;
            } else {
                if (!atub[j] && a > 0) ratio = (d[j] + tol_d) / a;
                else if (atub[j] && a < 0) ratio = (d[j] - tol_d) / a;
            }
            if (ratio < thmax) thmax = ratio;
        }
        if (thmax >= INF) return 1;
        int q = -1; double besta = 0;
        for (j = 0; j < ncol + m; j++) {
            double a = alpha_r[j];
            if (a == 0 || fabs(a) < 1e-9) continue;
            double ratio = INF;
            if (toLower) {
                if (!atub[j] && a < 0) ratio = d[j] / (-a);
                else if (atub[j] && a > 0) ratio = -d[j] / a;
            } else {
                if (!atub[j] && a > 0) ratio = d[j] / a;
                else if (atub[j] && a < 0) ratio = d[j] / a;
            }
            if (ratio <= thmax && fabs(a) > besta) { besta = fabs(a); q = j; }
        }
        if (q < 0) return 1;
        /* column alpha_q = Binv A_q */
        for (i = 0; i < m; i++) {
            double *bi = Binv + i * m;
            alpha_q[i] = dotcol(bi, q);
        }
        double arq = alpha_q[r];
        if (fabs(arq) < 1e-11) return 3;
        /* primal update */
        double bound = toLower ? lb[leave] : ub[leave];
        double delta = (x[leave] - bound) / arq;
        for (i = 0; i < m; i++) x[head[i]] -= delta * alpha_q[i];
        x[q] += delta;
        x[leave] = bound;
        /* dual update */
        double theta = d[q] / arq;
        for (j = 0; j < ncol + m; j++) if (pos[j] < 0 && alpha_r[j] != 0) d[j] -= theta * alpha_r[j];
        d[q] = 0;
        d[leave] = -theta;
        /* basis update */
        pos[q] = r; head[r] = q; pos[leave] = -1; atub[leave] = toLower ? 0 : 1;
        if (lb[leave] == ub[leave]) atub[leave] = 0;
        double *br = Binv + r * m;
        for (j = 0; j < m; j++) br[j] /= arq;
        for (i = 0; i < m; i++) if (i != r) {
            double f = alpha_q[i];
            if (f != 0) { double *bi = Binv + i * m; for (j = 0; j < m; j++) bi[j] -= f * br[j]; }
        }
        it++; since++; total_iters++;
        if (since >= 400) {
            since = 0;
            if (refactor()) return 3;
            compute_duals(); fix_status(); compute_primal();
        }
        if (it > 200000) return 3;
    }
}

/* add a <= row: sum coef*x <= rhs ; new slack is basic */
static void add_row(int cnt, const int *cols, const double *vals, double rhs, int type) {
    int i, j;
    if (m + 1 > mcap) die("row capacity");
    int r = m;
    for (i = 0; i < cnt; i++) col_add(cols[i], r, vals[i]);
    b[r] = rhs; rtype[r] = type;
    int sv = ncol + r;
    lb[sv] = 0; ub[sv] = (type == 1) ? INF : 0; cost[sv] = 0;
    /* extend Binv: rows/cols stride change -> rebuild with new stride */
    m++; need_refactor = 1;
    /* Binv stride m: just mark for refactor (done at start of dual_simplex) */
    head[r] = sv; pos[sv] = r; atub[sv] = 0;
    (void)j;
}

/* ---------------- problem specific ---------------- */
static int best_cost; static int *best_parent;
static int *aggfix; /* per arc: -1 free, 0 fixed 0 */

static double arc_val(int a) { double s = 0; int q; for (q = 0; q < Aq[a]; q++) s += x[Acol0[a] + q]; return s; }

static int eval_tree(int *par) {
    int load[70], i, c = 0;
    for (i = 0; i < n; i++) load[i] = 0;
    for (i = 0; i < n; i++) {
        int v = i, steps = 0;
        while (v != n) { if (v < 0 || ++steps > n) return -1; load[v]++; v = par[v]; }
    }
    for (i = 0; i < n; i++) {
        if (load[i] > Q) return -1;
        int L = -1;
        for (int k = 0; k < out_cnt[i]; k++) { int a = out_arcs[i][k]; if (Aj[a] == par[i]) L = Alen[a]; }
        if (L < 0) return -1;
        c += L * price[load[i] - 1];
    }
    return c;
}

/* lazy cuts R6: for arc a=(i->j), j turbine, and load q:
 *   sum_{q'>=q} x[a][q'] <= sum_{b out of j} sum_{q''>=q+1} x[b][q'']
 * (if i's subtree has >= q turbines then j's subtree has >= q+1). */
static int separate_cuts(int maxcuts) {
    int a, q, added = 0;
    static int cols[4096]; static double vals[4096];
    for (a = 0; a < nA && added < maxcuts; a++) {
        int j = Aj[a]; if (j == n) continue;
        double lhs = 0;
        for (q = Aq[a]; q >= 1; q--) { /* q from high to low; lhs accumulates x[a][>=q] */
            lhs += x[Acol0[a] + q - 1];
            if (lhs < 1e-6) continue;
            double rhs = 0;
            for (int k = 0; k < out_cnt[j]; k++) { int bb = out_arcs[j][k]; for (int qq = q + 1; qq <= Aq[bb]; qq++) rhs += x[Acol0[bb] + qq - 1]; }
            if (lhs > rhs + 1e-3) {
                int c = 0;
                for (int qq = q; qq <= Aq[a]; qq++) { cols[c] = Acol0[a] + qq - 1; vals[c++] = 1; }
                for (int k = 0; k < out_cnt[j]; k++) { int bb = out_arcs[j][k]; for (int qq = q + 1; qq <= Aq[bb]; qq++) { cols[c] = Acol0[bb] + qq - 1; vals[c++] = -1; } }
                if (m + 1 >= mcap) return added;
                add_row(c, cols, vals, 0, 1); added++;
                break;
            }
        }
    }
    if (!getenv("NOPAIR")) {
    /* pairwise: arcs a,b into j, thresholds s,r: x[a][>=s] + x[b][>=r] <= 1 + x[out j][>= s+r+1] */
    static double cum[2048][16]; /* cum[a][q] = x[a][>=q] */
    for (a = 0; a < nA; a++) { double c = 0; for (q = Aq[a]; q >= 1; q--) { c += x[Acol0[a]+q-1]; cum[a][q] = c; } for (q = Aq[a]+1; q <= 15; q++) cum[a][q] = 0; }
    for (int j = 0; j < n && added < maxcuts; j++) {
        double outc[17]; for (q = 0; q <= 16; q++) outc[q] = 0;
        for (int k = 0; k < out_cnt[j]; k++) { int bb = out_arcs[j][k]; for (q = 1; q <= Aq[bb]; q++) outc[q] += cum[bb][q]; }
        double bestv = 1e-3; int bs = -1, br = -1, ba = -1, bb2 = -1;
        for (int k1 = 0; k1 < in_cnt[j]; k1++) for (int k2 = k1 + 1; k2 < in_cnt[j]; k2++) {
            int a1 = in_arcs[j][k1], a2 = in_arcs[j][k2];
            for (int s1 = 1; s1 <= Aq[a1]; s1++) { if (cum[a1][s1] < 1e-6) break;
              for (int r1 = 1; r1 <= Aq[a2]; r1++) { if (cum[a2][r1] < 1e-6) break;
                int t = s1 + r1 + 1; double rhs = 1 + (t <= Q ? outc[t] : 0);
                double viol = cum[a1][s1] + cum[a2][r1] - rhs;
                if (viol > bestv) { bestv = viol; bs = s1; br = r1; ba = a1; bb2 = a2; } } }
        }
        if (ba >= 0) {
            int c = 0; int t = bs + br + 1;
            for (q = bs; q <= Aq[ba]; q++) { cols[c] = Acol0[ba] + q - 1; vals[c++] = 1; }
            for (q = br; q <= Aq[bb2]; q++) { cols[c] = Acol0[bb2] + q - 1; vals[c++] = 1; }
            for (int k = 0; k < out_cnt[j]; k++) { int o = out_arcs[j][k]; for (q = t; q <= Aq[o]; q++) { cols[c] = Acol0[o] + q - 1; vals[c++] = -1; } }
            if (m + 1 >= mcap) return added;
            add_row(c, cols, vals, 1, 1); added++;
        }
    }
    }
    return added;
}

/* bound change log for backtracking */
typedef struct { int var; double lb, ub; } Chg;
static Chg *trail; static int ntrail, trailcap;
static void setub0(int v) {
    if (ub[v] == 0) return;
    if (ntrail == trailcap) { trailcap = trailcap ? 2 * trailcap : 4096; trail = realloc(trail, trailcap * sizeof(Chg)); }
    trail[ntrail].var = v; trail[ntrail].lb = lb[v]; trail[ntrail].ub = ub[v]; ntrail++;
    ub[v] = 0; if (pos[v] < 0) x[v] = 0;
}
static void undo_to(int mark) {
    while (ntrail > mark) { ntrail--; ub[trail[ntrail].var] = trail[ntrail].ub; lb[trail[ntrail].var] = trail[ntrail].lb; }
}
static void fix_arc0(int a) { for (int q = 0; q < Aq[a]; q++) setub0(Acol0[a] + q); }
static int *edge_cross_cnt; static int **edge_cross;
static int *Erev; /* arcs by edge: up to 2 */
static int earcs[2048][2];
static void fix_arc1(int a) {
    int i = Ai[a];
    for (int k = 0; k < out_cnt[i]; k++) if (out_arcs[i][k] != a) fix_arc0(out_arcs[i][k]);
    int e = Ae[a];
    for (int t = 0; t < 2; t++) if (earcs[e][t] >= 0 && earcs[e][t] != a) fix_arc0(earcs[e][t]);
    for (int k = 0; k < edge_cross_cnt[e]; k++) { int f = edge_cross[e][k]; for (int t = 0; t < 2; t++) if (earcs[f][t] >= 0) fix_arc0(earcs[f][t]); }
}

static long long nodes = 0, leaves = 0; static int maxdepth = 0;
static double rootLB = 0;
static int cut_rounds_root = 30;
static int timelimit = 3600; static int timed_out = 0;
static FILE *LOG;

static int *save_head; static int save_m;

static int cut_depth = 0;
static double node_solve(int depth, int *status) {
    int st, rounds = 0;
    for (;;) {
        st = dual_simplex();
        if (st != 0) break;
        rounds++;
        if ((depth == 0 && rounds <= cut_rounds_root) || (depth > 0 && depth <= cut_depth && rounds <= 3)) {
            int added = separate_cuts(depth == 0 ? 400 : 100);
            if (added == 0) break;
            continue;
        }
        break;
    }
    *status = st;
    if (st == 1) return INF;
    if (st == 2) return cutoff + 1;
    double sb = safe_bound();
    return sb;
}

static void bnb(int depth) {
    nodes++;
    if (depth > maxdepth) maxdepth = depth;
    if ((double)(clock() - t0) / CLOCKS_PER_SEC > timelimit) { timed_out = 1; return; }
    int st; double lbv = node_solve(depth, &st);
    if (depth == 0 && getenv("DUMP")) {
        for (int a = 0; a < nA; a++) { double v = arc_val(a); if (v > 1e-6) { printf("ARC %d %d %d %.4f :", Ai[a], Aj[a], Alen[a], v); for (int q = 1; q <= Aq[a]; q++) if (x[Acol0[a]+q-1] > 1e-6) printf(" %d:%.3f", q, x[Acol0[a]+q-1]); printf("\n"); } }
        exit(0);
    }
    if (depth == 0) { rootLB = lbv; fprintf(LOG, "root LP bound (safe) %.3f  status %d  rows %d  iters %lld\n", lbv, st, m, total_iters); fflush(LOG); }
    if (st == 3) { fprintf(LOG, "numerical trouble at node %lld depth %d -- treating as unsolved\n", nodes, depth); timed_out = 1; return; }
    if (st == 1) return;
    if (lbv > cutoff) return;
    /* integral? choose branching arc */
    int bestA = -1; double bestscore = -1;
    int par[70];
    for (int i = 0; i < n; i++) par[i] = -1;
    int integral = 1;
    for (int a = 0; a < nA; a++) {
        double v = arc_val(a);
        if (v > 1e-6 && v < 1 - 1e-6) {
            integral = 0;
            double sc = (v < 1 - v ? v : 1 - v) * (1.0 + 0.0 * Alen[a]);
            if (sc > bestscore) { bestscore = sc; bestA = a; }
        } else if (v >= 1 - 1e-6) par[Ai[a]] = Aj[a];
    }
    if (integral) {
        leaves++;
        int c = eval_tree(par);
        if (c >= 0 && c < best_cost) {
            best_cost = c; memcpy(best_parent, par, n * sizeof(int)); cutoff = best_cost - 1 + 1e-3;
            fprintf(LOG, "  new incumbent %d at node %lld depth %d (%.1fs)\n", c, nodes, depth, (double)(clock() - t0) / CLOCKS_PER_SEC); fflush(LOG);
        }
        if (c < 0) { fprintf(LOG, "WARNING: integral LP point not a valid tree\n"); }
        return;
    }
    double v = arc_val(bestA);
    int mark = ntrail;
    int first = v >= 0.5 ? 1 : 0;
    for (int t = 0; t < 2; t++) {
        int br = t == 0 ? first : 1 - first;
        if (br == 1) fix_arc1(bestA); else fix_arc0(bestA);
        bnb(depth + 1);
        undo_to(mark);
        if (timed_out) return;
    }
}


/* ---------- best-first search (global lower bound reporting) ---------- */
typedef struct { double lb; int nd; int *dec; } BNode; /* dec[k] = arc*2 + dir */
static BNode *heap; static int hn, hcap;
static void hpush(BNode v) {
    if (hn == hcap) { hcap = hcap ? 2 * hcap : 1024; heap = realloc(heap, hcap * sizeof(BNode)); }
    int i = hn++; heap[i] = v;
    while (i > 0) { int p = (i - 1) / 2; if (heap[p].lb <= heap[i].lb) break; BNode t = heap[p]; heap[p] = heap[i]; heap[i] = t; i = p; }
}
static BNode hpop(void) {
    BNode top = heap[0]; heap[0] = heap[--hn]; int i = 0;
    for (;;) { int l = 2 * i + 1, r = l + 1, s = i;
        if (l < hn && heap[l].lb < heap[s].lb) s = l; if (r < hn && heap[r].lb < heap[s].lb) s = r;
        if (s == i) break; BNode t = heap[s]; heap[s] = heap[i]; heap[i] = t; i = s; }
    return top;
}
static double globalLB = 0;
static void best_first(void) {
    BNode r0 = { -INF, 0, NULL }; hpush(r0);
    double lastrep = 0;
    while (hn > 0) {
        double el = (double)(clock() - t0) / CLOCKS_PER_SEC;
        if (heap[0].lb > cutoff) { hn = 0; break; }
        if (el > timelimit) { timed_out = 1; break; }
        BNode nd = hpop();
        undo_to(0);
        for (int k = 0; k < nd.nd; k++) { int a = nd.dec[k] >> 1; if (nd.dec[k] & 1) fix_arc1(a); else fix_arc0(a); }
        nodes++;
        int st; double lbv = node_solve(nd.nd, &st);
        if (nd.nd == 0) { rootLB = lbv; fprintf(LOG, "root LP bound (safe) %.3f status %d rows %d\n", lbv, st, m); fflush(LOG); }
        if (st == 3) { fprintf(LOG, "numerical trouble; node kept with parent bound\n"); timed_out = 1; hpush(nd); break; }
        if (lbv < nd.lb) lbv = nd.lb;
        if (st == 1 || lbv > cutoff) { free(nd.dec); continue; }
        int bestA = -1; double bestscore = -1; int par[70]; int integral = 1;
        for (int i = 0; i < n; i++) par[i] = -1;
        for (int a = 0; a < nA; a++) {
            double v = arc_val(a);
            if (v > 1e-6 && v < 1 - 1e-6) { integral = 0; double sc = v < 1 - v ? v : 1 - v; if (sc > bestscore) { bestscore = sc; bestA = a; } }
            else if (v >= 1 - 1e-6) par[Ai[a]] = Aj[a];
        }
        if (integral) {
            leaves++;
            int c = eval_tree(par);
            if (c >= 0 && c < best_cost) { best_cost = c; memcpy(best_parent, par, n * sizeof(int)); cutoff = best_cost - 1 + 1e-3;
                fprintf(LOG, "  new incumbent %d (%.1fs)\n", c, el); fflush(LOG); }
            free(nd.dec); continue;
        }
        for (int dir = 0; dir < 2; dir++) {
            BNode ch; ch.lb = lbv; ch.nd = nd.nd + 1; ch.dec = malloc(ch.nd * sizeof(int));
            if (nd.nd) memcpy(ch.dec, nd.dec, nd.nd * sizeof(int));
            ch.dec[nd.nd] = bestA * 2 + dir; hpush(ch);
        }
        free(nd.dec);
        if (el - lastrep > 30) { lastrep = el; fprintf(LOG, "  t=%.0fs nodes=%lld open=%d globalLB=%.1f inc=%d\n", el, nodes, hn, heap[0].lb, best_cost); fflush(LOG); }
    }
    globalLB = hn > 0 ? heap[0].lb : (best_cost <= UBin ? best_cost : cutoff);
    if (hn > 0 && globalLB > best_cost) globalLB = best_cost;
}

int main(int argc, char **argv) {
    if (argc < 3) die("usage: bnb model.txt out.txt [timelimit]");
    FILE *f = fopen(argv[1], "r"); if (!f) die("open");
    if (argc > 3) timelimit = atoi(argv[3]);
    LOG = stdout;
    if (fscanf(f, "%d %d %d %d", &n, &K, &Q, &UBin) != 4) die("hdr");
    for (int q = 0; q < Q; q++) if (fscanf(f, "%d", &price[q]) != 1) die("price");
    if (fscanf(f, "%d", &nE) != 1) die("nE");
    Ei = malloc(nE * sizeof(int)); Ej = malloc(nE * sizeof(int)); Elen = malloc(nE * sizeof(int));
    for (int e = 0; e < nE; e++) if (fscanf(f, "%d %d %d", &Ei[e], &Ej[e], &Elen[e]) != 3) die("edge");
    if (fscanf(f, "%d", &nCl) != 1) die("nC");
    Cl = malloc(nCl * sizeof(int *)); Clsz = malloc(nCl * sizeof(int));
    edge_cross_cnt = calloc(nE, sizeof(int)); edge_cross = calloc(nE, sizeof(int *));
    int *incl = calloc(nE, sizeof(int));
    for (int c = 0; c < nCl; c++) {
        if (fscanf(f, "%d", &Clsz[c]) != 1) die("cl");
        Cl[c] = malloc(Clsz[c] * sizeof(int));
        for (int k = 0; k < Clsz[c]; k++) { if (fscanf(f, "%d", &Cl[c][k]) != 1) die("cl2"); incl[Cl[c][k]] = 1; }
    }
    /* crossing adjacency from cliques (every crossing pair lies in some clique) */
    for (int e = 0; e < nE; e++) edge_cross[e] = malloc(nE * sizeof(int));
    {
        char *adj = calloc((size_t)nE * nE, 1);
        for (int c = 0; c < nCl; c++) for (int a = 0; a < Clsz[c]; a++) for (int bq = 0; bq < Clsz[c]; bq++) if (a != bq) adj[Cl[c][a] * nE + Cl[c][bq]] = 1;
        for (int e = 0; e < nE; e++) for (int g = 0; g < nE; g++) if (adj[e * nE + g]) edge_cross[e][edge_cross_cnt[e]++] = g;
        free(adj);
    }
    /* arcs */
    nA = 0; Ai = malloc(2 * nE * sizeof(int)); Aj = malloc(2 * nE * sizeof(int)); Ae = malloc(2 * nE * sizeof(int));
    Alen = malloc(2 * nE * sizeof(int)); Aq = malloc(2 * nE * sizeof(int)); Acol0 = malloc(2 * nE * sizeof(int));
    for (int e = 0; e < nE; e++) {
        earcs[e][0] = earcs[e][1] = -1;
        if (Ej[e] == n) { Ai[nA] = Ei[e]; Aj[nA] = n; Ae[nA] = e; Alen[nA] = Elen[e]; Aq[nA] = Q; earcs[e][0] = nA; nA++; }
        else {
            Ai[nA] = Ei[e]; Aj[nA] = Ej[e]; Ae[nA] = e; Alen[nA] = Elen[e]; Aq[nA] = Q - 1; earcs[e][0] = nA; nA++;
            Ai[nA] = Ej[e]; Aj[nA] = Ei[e]; Ae[nA] = e; Alen[nA] = Elen[e]; Aq[nA] = Q - 1; earcs[e][1] = nA; nA++;
        }
    }
    for (int i = 0; i <= n; i++) { out_arcs[i] = malloc(nA * sizeof(int)); in_arcs[i] = malloc(nA * sizeof(int)); }
    for (int a = 0; a < nA; a++) { int i = Ai[a], j = Aj[a]; out_arcs[i][out_cnt[i]++] = a; in_arcs[j][in_cnt[j]++] = a; }
    ncol = 0; for (int a = 0; a < nA; a++) { Acol0[a] = ncol; ncol += Aq[a]; }
    mcap = 2 * n + 1 + nCl + nE + 3000;
    nvar_cap = ncol + mcap;
    colrows = calloc(ncol, sizeof(int *)); colvals = calloc(ncol, sizeof(double *)); colnz = calloc(ncol, sizeof(int)); colcap = calloc(ncol, sizeof(int));
    b = calloc(mcap, sizeof(double)); rtype = calloc(mcap, sizeof(int));
    lb = calloc(nvar_cap, sizeof(double)); ub = calloc(nvar_cap, sizeof(double)); cost = calloc(nvar_cap, sizeof(double));
    x = calloc(nvar_cap, sizeof(double)); d = calloc(nvar_cap, sizeof(double));
    head = calloc(mcap, sizeof(int)); pos = malloc(nvar_cap * sizeof(int)); atub = calloc(nvar_cap, sizeof(int));
    for (int j = 0; j < nvar_cap; j++) pos[j] = -1;
    for (int a = 0; a < nA; a++) for (int q = 1; q <= Aq[a]; q++) {
        int j = Acol0[a] + q - 1; lb[j] = 0; ub[j] = 1; cost[j] = (double)Alen[a] * price[q - 1];
    }
    m = 0;
    /* R1, R2 */
    for (int i = 0; i < n; i++) {
        int r1 = m, r2 = m + 1;
        for (int k = 0; k < out_cnt[i]; k++) { int a = out_arcs[i][k]; for (int q = 1; q <= Aq[a]; q++) { col_add(Acol0[a] + q - 1, r1, 1); } }
        for (int k = 0; k < out_cnt[i]; k++) { int a = out_arcs[i][k]; for (int q = 1; q <= Aq[a]; q++) col_add(Acol0[a] + q - 1, r2, q); }
        for (int k = 0; k < in_cnt[i]; k++) { int a = in_arcs[i][k]; for (int q = 1; q <= Aq[a]; q++) col_add(Acol0[a] + q - 1, r2, -q); }
        b[r1] = 1; rtype[r1] = 0; b[r2] = 1; rtype[r2] = 0; m += 2;
    }
    /* R3 */
    for (int k = 0; k < in_cnt[n]; k++) { int a = in_arcs[n][k]; for (int q = 1; q <= Aq[a]; q++) col_add(Acol0[a] + q - 1, m, 1); }
    b[m] = K; rtype[m] = 1; m++;
    /* R4 cliques */
    for (int c = 0; c < nCl; c++) {
        for (int k = 0; k < Clsz[c]; k++) { int e = Cl[c][k]; for (int t = 0; t < 2; t++) if (earcs[e][t] >= 0) { int a = earcs[e][t]; for (int q = 1; q <= Aq[a]; q++) col_add(Acol0[a] + q - 1, m, 1); } }
        b[m] = 1; rtype[m] = 1; m++;
    }
    /* R5 */
    for (int e = 0; e < nE; e++) if (!incl[e] && earcs[e][1] >= 0) {
        for (int t = 0; t < 2; t++) { int a = earcs[e][t]; for (int q = 1; q <= Aq[a]; q++) col_add(Acol0[a] + q - 1, m, 1); }
        b[m] = 1; rtype[m] = 1; m++;
    }
    for (int r = 0; r < m; r++) { int sv = ncol + r; lb[sv] = 0; ub[sv] = rtype[r] == 1 ? INF : 0; head[r] = sv; pos[sv] = r; }
    Binv = malloc((size_t)mcap * mcap * sizeof(double)); Bmat = malloc((size_t)mcap * mcap * sizeof(double));
    work = malloc(mcap * sizeof(double)); work2 = malloc(mcap * sizeof(double)); ybuf = malloc(mcap * sizeof(double));
    alpha_r = malloc(nvar_cap * sizeof(double)); alpha_q = malloc(mcap * sizeof(double));
    best_parent = malloc(n * sizeof(int)); best_cost = UBin + 1; /* allow re-finding UB */
    cutoff = UBin - 1 + 1e-3 + 1.0; /* search for solutions with cost <= UB */
    fprintf(LOG, "n=%d K=%d Q=%d arcs=%d cols=%d rows=%d cliques=%d UBin=%d\n", n, K, Q, nA, ncol, m, nCl, UBin);
    t0 = clock();
    int bestfirst = getenv("BEST") != NULL;
    if (bestfirst) best_first(); else bnb(0);
    double secs = (double)(clock() - t0) / CLOCKS_PER_SEC;
    fprintf(LOG, "done: nodes=%lld leaves=%lld maxdepth=%d iters=%lld time=%.1fs timed_out=%d rows_final=%d\n", nodes, leaves, maxdepth, total_iters, secs, timed_out, m);
    FILE *o = fopen(argv[2], "w");
    fprintf(o, "status %s\nbest %d\nrootLB %.3f\nglobalLB %.3f\nnodes %lld\ntime %.1f\n", timed_out ? "INCOMPLETE" : "COMPLETE", best_cost <= UBin ? best_cost : -1, rootLB, bestfirst ? globalLB : rootLB, nodes, secs);
    if (best_cost <= UBin) for (int i = 0; i < n; i++) fprintf(o, "%d %d\n", i, best_parent[i]);
    fclose(o);
    if (bestfirst) fprintf(LOG, "global lower bound at stop: %.3f\n", globalLB);
    fprintf(LOG, "result: %s best=%d\n", timed_out ? "INCOMPLETE" : "COMPLETE (optimal or UB proven)", best_cost <= UBin ? best_cost : -1);
    return 0;
}
