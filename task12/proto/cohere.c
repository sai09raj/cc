/* COHERE-12 reference engine, C port of cohere.py (must match it exactly).
 * Generalized: any directory node pair, any line->bank home table, any
 * workload size. Build: gcc -O2 -o cohere cohere.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RESP 0
#define FWD 1
#define REQ 2
#define NCORE 8
#define MAXLINE 32
#define SETS 2
#define WAYS 2
#define MAXOPS 4096
#define MAXQ 4096

enum { T_GETS, T_GETM, T_PUTS, T_PUTM, T_FWDGETS, T_FWDGETM, T_INV, T_PUTACK, T_DATA, T_INVACK, T_NACK };
enum { S_NONE, S_ISD, S_IMAD, S_IMA, S_S, S_SMAD, S_SMA, S_M, S_MIA, S_SIA, S_IIA };
enum { D_I, D_S, D_M, D_SD };
enum { OP_LD, OP_ST, OP_WAIT };

typedef struct { int serial, typ, vnet, src, dst, line, req, ack, val, dnode; } Msg;
/* entity ids: 0..7 caches C0..C7, 8..9 directories D0..D1 */

static int LAT[8][8];
static int NLINE = 8, NOPS = 40;
static int prog_op[NCORE][MAXOPS], prog_arg[NCORE][MAXOPS];

typedef struct { int t0; Msg m; } Wait;
typedef struct { Wait *a; int n, cap; } WList;
typedef struct { Msg *a; int n, cap; } MList;
typedef struct { int line, st, lru, val; } Way;

static void wpush(WList *l, Wait w) { if (l->n == l->cap) { l->cap = l->cap ? l->cap * 2 : 16; l->a = realloc(l->a, l->cap * sizeof(Wait)); } l->a[l->n++] = w; }
static void mpush(MList *l, Msg m) { if (l->n == l->cap) { l->cap = l->cap ? l->cap * 2 : 16; l->a = realloc(l->a, l->cap * sizeof(Msg)); } l->a[l->n++] = m; }
static void mremove(MList *l, int i) { memmove(l->a + i, l->a + i + 1, (l->n - i - 1) * sizeof(Msg)); l->n--; }

typedef struct {
    int dnode[2], qcap, backoff, home[MAXLINE];
    int t, serial;
    WList link[8][8];
    MList inflight[8];               /* bucket by arrival time mod 8; entries hold arrive time in .ack? no: separate */
    int infl_t[8][MAXQ];
    MList inq[10][3];
    MList rejected[2];
    int dstate[MAXLINE], sharers[MAXLINE], owner[MAXLINE], mem[MAXLINE];
    Way ways[NCORE][SETS][WAYS];
    int acks[NCORE][MAXLINE], nackc[NCORE][MAXLINE];
    int pend_kind[NCORE][MAXLINE], pend_t[NCORE][MAXLINE];   /* pend_t<0: none */
    int pc[NCORE], busy_until[NCORE], wline[NCORE], wkind[NCORE], wt0[NCORE], done_t[NCORE], seq[NCORE];
    int nmsgs, nnacks, *lat, nlat, latcap, npend, ninflight, nlinkwait;
} Sim;

static int next_hop(int cur, int dst) {
    int r = cur / 4, c = cur % 4, dr = dst / 4, dc = dst % 4;
    if (dc > c) return cur + 1;
    if (dc < c) return cur - 1;
    if (dr > r) return cur + 4;
    return cur - 4;
}
static int node_of(Sim *s, int e) { return e < 8 ? e : s->dnode[e - 8]; }

static void send(Sim *s, int typ, int vnet, int src, int dst, int line, int req, int ack, int val) {
    Msg m; m.serial = ++s->serial; m.typ = typ; m.vnet = vnet; m.src = src; m.dst = dst; m.line = line; m.req = req; m.ack = ack; m.val = val;
    s->nmsgs++; if (typ == T_NACK) s->nnacks++;
    int sn = node_of(s, src), dn = node_of(s, dst); m.dnode = dn;
    if (sn == dn) {
        int b = (s->t + 1) & 7; MList *l = &s->inflight[b];
        s->infl_t[b][l->n] = (s->t + 1) * 16 + dn; mpush(l, m); s->ninflight++;
    } else {
        Wait w; w.t0 = s->t; w.m = m; wpush(&s->link[sn][next_hop(sn, dn)], w); s->nlinkwait++;
    }
}

static Way *findw(Sim *s, int c, int line) {
    Way *set = s->ways[c][(line / 2) % SETS];
    for (int i = 0; i < WAYS; i++) if (set[i].st != S_NONE && set[i].line == line) return &set[i];
    return NULL;
}
static void freeway(Way *w) { w->st = S_NONE; }

static void stage_links(Sim *s) {
    for (int a = 0; a < 8; a++) for (int b = 0; b < 8; b++) {
        WList *q = &s->link[a][b];
        if (!q->n) continue;
        int bi = -1;
        for (int i = 0; i < q->n; i++) {
            if (q->a[i].t0 >= s->t) continue;
            if (bi < 0) { bi = i; continue; }
            Wait *x = &q->a[i], *y = &q->a[bi];
            if (x->m.vnet < y->m.vnet || (x->m.vnet == y->m.vnet && (x->t0 < y->t0 || (x->t0 == y->t0 && x->m.serial < y->m.serial)))) bi = i;
        }
        if (bi < 0) continue;
        Msg m = q->a[bi].m;
        memmove(q->a + bi, q->a + bi + 1, (q->n - bi - 1) * sizeof(Wait)); q->n--; s->nlinkwait--;
        int at = s->t + LAT[a][b], bk = at & 7;
        m.ack = m.ack; /* unchanged */
        MList *l = &s->inflight[bk]; s->infl_t[bk][l->n] = at;
        /* stash current node in req? no: we need the node the message arrives at: b. store via dnode compare later */
        Msg mm = m; mpush(l, mm); s->ninflight++;
        /* record arrival node by encoding: keep a parallel array */
        extern int arr_node_tmp; (void)arr_node_tmp;
        s->infl_t[bk][l->n - 1] = at * 16 + b;
    }
}
int arr_node_tmp;

static int cmp_serial(const void *a, const void *b) { return ((const Msg *)a)->serial - ((const Msg *)b)->serial; }

static void stage_arrivals(Sim *s) {
    int bk = s->t & 7; MList *l = &s->inflight[bk];
    if (!l->n) return;
    /* collect those arriving now; all entries in the bucket arrive now (lat<=7) */
    static Msg buf[MAXQ]; static int node[MAXQ]; int n = 0;
    MList keep = {0};
    for (int i = 0; i < l->n; i++) {
        int code = s->infl_t[bk][i];
        int at, nd;
        at = code / 16; nd = code % 16;
        (void)at;
        buf[n] = l->a[i]; node[n] = nd; n++;
    }
    l->n = 0; s->ninflight -= n;
    (void)keep;
    /* sort by serial (insertion sort, n small) */
    for (int i = 1; i < n; i++) { Msg m = buf[i]; int nd = node[i]; int j = i - 1; while (j >= 0 && buf[j].serial > m.serial) { buf[j + 1] = buf[j]; node[j + 1] = node[j]; j--; } buf[j + 1] = m; node[j + 1] = nd; }
    for (int i = 0; i < n; i++) {
        Msg m = buf[i]; int nd = node[i] < 0 ? m.dnode : node[i];
        if (nd == m.dnode) {
            if (m.dst >= 8 && m.vnet == REQ && s->inq[m.dst][REQ].n >= s->qcap) { mpush(&s->rejected[m.dst - 8], m); continue; }
            mpush(&s->inq[m.dst][m.vnet], m);
        } else {
            Wait w; w.t0 = s->t; w.m = m; wpush(&s->link[nd][next_hop(nd, m.dnode)], w); s->nlinkwait++;
        }
    }
}

static int popcount(int x) { return __builtin_popcount(x); }

static int dir_req(Sim *s, int d, Msg *m) {
    int L = m->line, r = m->src, st = s->dstate[L], de = 8 + d;
    if (m->typ == T_GETS) {
        if (st == D_I) { send(s, T_DATA, RESP, de, r, L, 0, 0, s->mem[L]); s->sharers[L] |= 1 << r; s->dstate[L] = D_S; }
        else if (st == D_S) { send(s, T_DATA, RESP, de, r, L, 0, 0, s->mem[L]); s->sharers[L] |= 1 << r; }
        else if (st == D_M) { int o = s->owner[L]; send(s, T_FWDGETS, FWD, de, o, L, r, 0, 0); s->sharers[L] |= (1 << r) | (1 << o); s->owner[L] = -1; s->dstate[L] = D_SD; }
        else return 0;
    } else if (m->typ == T_GETM) {
        if (st == D_I) { send(s, T_DATA, RESP, de, r, L, 0, 0, s->mem[L]); s->owner[L] = r; s->dstate[L] = D_M; }
        else if (st == D_S) {
            int others = s->sharers[L] & ~(1 << r);
            send(s, T_DATA, RESP, de, r, L, 0, popcount(others), s->mem[L]);
            for (int c = 0; c < NCORE; c++) if (others >> c & 1) send(s, T_INV, FWD, de, c, L, r, 0, 0);
            s->sharers[L] = 0; s->owner[L] = r; s->dstate[L] = D_M;
        } else if (st == D_M) { int o = s->owner[L]; send(s, T_FWDGETM, FWD, de, o, L, r, 0, 0); s->owner[L] = r; }
        else return 0;
    } else if (m->typ == T_PUTS) {
        if ((st == D_S || st == D_SD) && (s->sharers[L] >> r & 1)) {
            s->sharers[L] &= ~(1 << r);
            if (st == D_S && !s->sharers[L]) s->dstate[L] = D_I;
        }
        send(s, T_PUTACK, FWD, de, r, L, 0, 0, 0);
    } else { /* PutM */
        if (st == D_M && s->owner[L] == r) { s->mem[L] = m->val; s->owner[L] = -1; s->dstate[L] = D_I; }
        else if (st == D_S || st == D_SD) {
            s->sharers[L] &= ~(1 << r);
            if (st == D_S && !s->sharers[L]) s->dstate[L] = D_I;
        }
        send(s, T_PUTACK, FWD, de, r, L, 0, 0, 0);
    }
    return 1;
}

static void dir_step(Sim *s, int d) {
    MList *q = s->inq[8 + d];
    if (q[RESP].n) { Msg m = q[RESP].a[0]; mremove(&q[RESP], 0); s->mem[m.line] = m.val; s->dstate[m.line] = D_S; }
    if (q[REQ].n) { if (dir_req(s, d, &q[REQ].a[0])) mremove(&q[REQ], 0); }
    for (int i = 0; i < s->rejected[d].n; i++) { Msg *m = &s->rejected[d].a[i]; send(s, T_NACK, RESP, 8 + d, m->src, m->line, m->typ, 0, 0); }
    s->rejected[d].n = 0;
}

static void complete(Sim *s, int c, Way *w, int t) {
    if (s->wkind[c] == OP_LD) {
        if (s->nlat == s->latcap) { s->latcap = s->latcap ? s->latcap * 2 : 256; s->lat = realloc(s->lat, s->latcap * sizeof(int)); }
        s->lat[s->nlat++] = t - s->wt0[c];
    } else { s->seq[c]++; w->val = c * 1000 + s->seq[c]; }
    w->lru = t; s->wkind[c] = -1; s->pc[c]++; s->busy_until[c] = t + 1;
}

static void cache_resp(Sim *s, int c, Msg *m) {
    int L = m->line; Way *w = findw(s, c, L);
    if (m->typ == T_NACK) {
        int att = ++s->nackc[c][L];
        int delay = s->backoff << (att - 1); if (att - 1 >= 7 || delay > 64) delay = 64;
        if (s->pend_t[c][L] < 0) s->npend++;
        s->pend_kind[c][L] = m->req; s->pend_t[c][L] = s->t + delay;
        return;
    }
    if (m->typ == T_INVACK) {
        s->acks[c][L]--;
        if ((w->st == S_IMA || w->st == S_SMA) && s->acks[c][L] == 0) { w->st = S_M; s->nackc[c][L] = 0; complete(s, c, w, s->t); }
        return;
    }
    /* Data */
    int st = w->st; w->val = m->val; s->nackc[c][L] = 0;
    if (st == S_ISD) { w->st = S_S; complete(s, c, w, s->t); }
    else if (st == S_IMAD || st == S_SMAD) {
        if (m->src < 8) { w->st = S_M; complete(s, c, w, s->t); }
        else {
            s->acks[c][L] += m->ack;
            if (s->acks[c][L] == 0) { w->st = S_M; complete(s, c, w, s->t); }
            else w->st = (st == S_IMAD) ? S_IMA : S_SMA;
        }
    } else { fprintf(stderr, "bad Data c%d L%d st%d\n", c, L, st); exit(2); }
}

static int cache_fwd(Sim *s, int c, Msg *m) {
    int L = m->line; Way *w = findw(s, c, L); int st = w ? w->st : S_NONE;
    if (m->typ == T_PUTACK) {
        if (!(st == S_MIA || st == S_SIA || st == S_IIA)) { fprintf(stderr, "bad PutAck\n"); exit(2); }
        freeway(w); s->nackc[c][L] = 0; return 1;
    }
    if (m->typ == T_INV) {
        if (st == S_ISD) return 0;
        if (st == S_S || st == S_SMAD || st == S_SIA) {
            send(s, T_INVACK, RESP, c, m->req, L, 0, 0, 0);
            if (st == S_S) freeway(w); else if (st == S_SMAD) w->st = S_IMAD; else w->st = S_IIA;
            return 1;
        }
        fprintf(stderr, "bad Inv st%d\n", st); exit(2);
    }
    if (st == S_IMAD || st == S_IMA || st == S_SMAD || st == S_SMA) return 0;
    if (!(st == S_M || st == S_MIA)) { fprintf(stderr, "bad Fwd st%d\n", st); exit(2); }
    int home = 8 + s->home[L];
    if (m->typ == T_FWDGETS) {
        send(s, T_DATA, RESP, c, m->req, L, 0, 0, w->val);
        send(s, T_DATA, RESP, c, home, L, 0, 0, w->val);
        w->st = (st == S_M) ? S_S : S_SIA;
    } else {
        send(s, T_DATA, RESP, c, m->req, L, 0, 0, w->val);
        if (st == S_M) freeway(w); else w->st = S_IIA;
    }
    return 1;
}

static void core_step(Sim *s, int c) {
    if (s->done_t[c] >= 0 || s->wkind[c] >= 0 || s->busy_until[c] > s->t) return;
    if (s->pc[c] >= NOPS) { s->done_t[c] = s->t; return; }
    int op = prog_op[c][s->pc[c]], arg = prog_arg[c][s->pc[c]];
    if (op == OP_WAIT) { s->busy_until[c] = s->t + arg; s->pc[c]++; return; }
    int L = arg; Way *w = findw(s, c, L);
    if (w) {
        int st = w->st;
        if (op == OP_LD && (st == S_S || st == S_M || st == S_SMAD || st == S_SMA)) { w->lru = s->t; s->pc[c]++; s->busy_until[c] = s->t + 1; return; }
        if (op == OP_ST && st == S_M) { s->seq[c]++; w->val = c * 1000 + s->seq[c]; w->lru = s->t; s->pc[c]++; s->busy_until[c] = s->t + 1; return; }
        if (op == OP_ST && st == S_S) { w->st = S_SMAD; s->wline[c] = L; s->wkind[c] = OP_ST; s->wt0[c] = s->t; send(s, T_GETM, REQ, c, 8 + s->home[L], L, 0, 0, 0); return; }
        return;
    }
    Way *set = s->ways[c][(L / 2) % SETS];
    int freei = -1;
    for (int i = 0; i < WAYS; i++) if (set[i].st == S_NONE) { freei = i; break; }
    if (freei < 0) {
        int vi = -1;
        for (int i = 0; i < WAYS; i++) if (set[i].st == S_S || set[i].st == S_M) { if (vi < 0 || set[i].lru < set[vi].lru) vi = i; }
        if (vi >= 0) {
            Way *v = &set[vi];
            if (v->st == S_S) { v->st = S_SIA; send(s, T_PUTS, REQ, c, 8 + s->home[v->line], v->line, 0, 0, 0); }
            else { v->st = S_MIA; send(s, T_PUTM, REQ, c, 8 + s->home[v->line], v->line, 0, 0, v->val); }
        }
        return;
    }
    Way *nw = &set[freei]; nw->line = L; nw->st = (op == OP_LD) ? S_ISD : S_IMAD; nw->lru = s->t; nw->val = 0;
    s->wline[c] = L; s->wkind[c] = op; s->wt0[c] = s->t;
    send(s, op == OP_LD ? T_GETS : T_GETM, REQ, c, 8 + s->home[L], L, 0, 0, 0);
}

static void cache_step(Sim *s, int c) {
    MList *q = s->inq[c];
    if (q[RESP].n) { Msg m = q[RESP].a[0]; mremove(&q[RESP], 0); cache_resp(s, c, &m); }
    int blocked = 0; /* bitmask over lines (<=32) */
    for (int i = 0; i < q[FWD].n; i++) {
        Msg *m = &q[FWD].a[i];
        if (blocked >> m->line & 1) continue;
        Msg mm = *m;
        if (cache_fwd(s, c, &mm)) { mremove(&q[FWD], i); break; }
        blocked |= 1 << m->line;
    }
    if (s->npend) {
        int bl = -1;
        for (int L = 0; L < NLINE; L++) if (s->pend_t[c][L] >= 0 && s->pend_t[c][L] <= s->t) { if (bl < 0 || s->pend_t[c][L] < s->pend_t[c][bl]) bl = L; }
        if (bl >= 0) {
            int kind = s->pend_kind[c][bl]; s->pend_t[c][bl] = -1; s->npend--;
            Way *w = findw(s, c, bl); int val = (w && kind == T_PUTM) ? w->val : 0;
            send(s, kind, REQ, c, 8 + s->home[bl], bl, 0, 0, val);
        }
    }
    core_step(s, c);
}

static int quiescent(Sim *s) {
    for (int c = 0; c < NCORE; c++) if (s->done_t[c] < 0) return 0;
    if (s->ninflight || s->npend || s->nlinkwait) return 0;
    for (int e = 0; e < 10; e++) for (int v = 0; v < 3; v++) if (s->inq[e][v].n) return 0;
    return 1;
}

static int cmpint(const void *a, const void *b) { return *(const int *)a - *(const int *)b; }

typedef struct { int makespan, p95, msgs, nacks; } Result;

static Sim SIM;
static Result run(int d0, int d1, int qcap, int backoff, const int *home) {
    Sim *s = &SIM;
    /* reset, keeping allocated buffers */
    for (int a = 0; a < 8; a++) for (int b = 0; b < 8; b++) s->link[a][b].n = 0;
    for (int i = 0; i < 8; i++) s->inflight[i].n = 0;
    for (int e = 0; e < 10; e++) for (int v = 0; v < 3; v++) s->inq[e][v].n = 0;
    s->rejected[0].n = s->rejected[1].n = 0;
    s->dnode[0] = d0; s->dnode[1] = d1; s->qcap = qcap; s->backoff = backoff;
    for (int L = 0; L < NLINE; L++) { s->home[L] = home[L]; s->dstate[L] = D_I; s->sharers[L] = 0; s->owner[L] = -1; s->mem[L] = 0; }
    memset(s->ways, 0, sizeof s->ways);
    for (int c = 0; c < NCORE; c++) for (int L = 0; L < NLINE; L++) { s->acks[c][L] = 0; s->nackc[c][L] = 0; s->pend_t[c][L] = -1; }
    for (int c = 0; c < NCORE; c++) { s->pc[c] = 0; s->busy_until[c] = 0; s->wkind[c] = -1; s->done_t[c] = -1; s->seq[c] = 0; }
    s->t = 0; s->serial = 0; s->nmsgs = s->nnacks = 0; s->nlat = 0; s->npend = 0; s->ninflight = 0; s->nlinkwait = 0;
    while (!quiescent(s)) {
        s->t++;
        if (s->t > 2000000) { fprintf(stderr, "deadlock\n"); exit(3); }
        stage_links(s); stage_arrivals(s);
        dir_step(s, 0); dir_step(s, 1);
        for (int c = 0; c < NCORE; c++) cache_step(s, c);
    }
    Result r; r.makespan = 0;
    for (int c = 0; c < NCORE; c++) if (s->done_t[c] > r.makespan) r.makespan = s->done_t[c];
    qsort(s->lat, s->nlat, sizeof(int), cmpint);
    int idx = (int)(0.95 * s->nlat); if (idx > s->nlat - 1) idx = s->nlat - 1;
    r.p95 = s->nlat ? s->lat[idx] : 0; r.msgs = s->nmsgs; r.nacks = s->nnacks;
    return r;
}

static unsigned lcg(unsigned long long x) { return (unsigned)((1103515245ULL * x + 12345ULL) % (1ULL << 31)); }
static void gen_workload(void) {
    for (int c = 0; c < NCORE; c++) {
        unsigned long long x = 101 + 7 * c;
        for (int i = 0; i < NOPS; i++) {
            x = lcg(x); unsigned r = (unsigned)(x >> 8); int kind = r % 10;
            x = lcg(x); unsigned sv = (unsigned)(x >> 8);
            int line = (((sv >> 4) % 10) < 6) ? (int)(sv % 3) : (int)(sv % NLINE);
            if (kind < 5) { prog_op[c][i] = OP_LD; prog_arg[c][i] = line; }
            else if (kind < 8) { prog_op[c][i] = OP_ST; prog_arg[c][i] = line; }
            else { prog_op[c][i] = OP_WAIT; prog_arg[c][i] = 1 + (sv >> 3) % 7; }
        }
    }
}

int main(int argc, char **argv) {
    int pairs[10][3] = {{0,1,1},{1,2,2},{2,3,1},{4,5,2},{5,6,1},{6,7,3},{0,4,1},{1,5,3},{2,6,1},{3,7,2}};
    for (int i = 0; i < 10; i++) { LAT[pairs[i][0]][pairs[i][1]] = LAT[pairs[i][1]][pairs[i][0]] = pairs[i][2]; }
    if (argc < 2) { fprintf(stderr, "usage\n"); return 1; }
    if (!strcmp(argv[1], "ref64")) {
        gen_workload();
        int pl[4][2] = {{0,7},{1,6},{3,4},{2,5}}; int bs[4] = {1,2,4,8}; int home[MAXLINE];
        for (int L = 0; L < NLINE; L++) home[L] = L % 2;
        for (int p = 0; p < 4; p++) for (int q = 1; q <= 4; q++) for (int b = 0; b < 4; b++) {
            Result r = run(pl[p][0], pl[p][1], q, bs[b], home);
            printf("P%d %d %d %d %d %d %d\n", p + 1, q, bs[b], r.makespan, r.p95, r.msgs, r.nacks);
        }
        return 0;
    }
    if (!strcmp(argv[1], "one")) {
        /* one NLINE NOPS d0 d1 Q B homebits */
        NLINE = atoi(argv[2]); NOPS = atoi(argv[3]); gen_workload();
        int home[MAXLINE]; unsigned hb = (unsigned)strtoul(argv[8], 0, 10);
        for (int L = 0; L < NLINE; L++) home[L] = hb >> L & 1;
        Result r = run(atoi(argv[4]), atoi(argv[5]), atoi(argv[6]), atoi(argv[7]), home);
        printf("%d %d %d %d\n", r.makespan, r.p95, r.msgs, r.nacks);
        return 0;
    }
    if (!strcmp(argv[1], "slice")) {
        /* slice NLINE NOPS d0 d1 Q B outfile : makespan for every home table */
        NLINE = atoi(argv[2]); NOPS = atoi(argv[3]); gen_workload();
        int d0 = atoi(argv[4]), d1 = atoi(argv[5]), q = atoi(argv[6]), b = atoi(argv[7]);
        FILE *f = fopen(argv[8], "wb"); int home[MAXLINE];
        for (unsigned h = 0; h < (1u << NLINE); h++) {
            for (int L = 0; L < NLINE; L++) home[L] = h >> L & 1;
            Result r = run(d0, d1, q, b, home); int v[2] = {r.makespan, r.msgs}; fwrite(v, sizeof v, 1, f);
        }
        fclose(f); return 0;
    }
    if (!strcmp(argv[1], "enum")) {
        /* enum NLINE NOPS d0 d1 Q B outfile : uint16 makespan, uint16 msgs for every home table */
        NLINE = atoi(argv[2]); NOPS = atoi(argv[3]); gen_workload();
        int d0 = atoi(argv[4]), d1 = atoi(argv[5]), q = atoi(argv[6]), b = atoi(argv[7]);
        char tmp[512]; snprintf(tmp, sizeof tmp, "%s.part", argv[8]);
        FILE *f = fopen(tmp, "wb"); int home[MAXLINE];
        for (unsigned h = 0; h < (1u << NLINE); h++) {
            for (int L = 0; L < NLINE; L++) home[L] = h >> L & 1;
            Result r = run(d0, d1, q, b, home);
            if (r.makespan > 65535 || r.msgs > 65535) { fprintf(stderr, "overflow\n"); return 4; }
            unsigned short v[2] = {(unsigned short)r.makespan, (unsigned short)r.msgs}; fwrite(v, sizeof v, 1, f);
        }
        fclose(f); rename(tmp, argv[8]); return 0;
    }
    if (!strcmp(argv[1], "bench")) {
        NLINE = atoi(argv[2]); NOPS = atoi(argv[3]); int n = atoi(argv[4]); gen_workload();
        int home[MAXLINE]; long long acc = 0;
        for (int i = 0; i < n; i++) {
            for (int L = 0; L < NLINE; L++) home[L] = (i >> L) & 1;
            Result r = run(1, 6, 1 + i % 4, 1 << (i % 4), home); acc += r.makespan;
        }
        printf("%lld\n", acc);
        return 0;
    }
    return 1;
}
