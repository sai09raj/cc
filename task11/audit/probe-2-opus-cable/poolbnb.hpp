// poolbnb.hpp -- branch-and-price-and-cut over an enumerated pool of feeder trees.
//
// Master LP (working subset W of the pool, plus one artificial column per turbine of cost BIGM):
//    min sum c_T lam_T   s.t.  sum_{T contains i} lam_T = 1          (each turbine)
//                             sum lam_T <= K                        (feeder bays)
//                             sum_{T meets clique C} lam_T <= 1     (pairwise-crossing edge sets)
// Pricing scans the whole pool. Every pruning decision uses the Lagrangian bound
//    L(y) = sum_r y_r b_r + sum_{T in pool, allowed at node} min(0, rc_T(y))
// which is a valid lower bound for any multipliers y (inequality-row multipliers clamped <= 0),
// computed in long double and compared to UB-1 with a 1e-3 margin.
#pragma once
#include "setpart.hpp"

#ifndef NOWSEC_DEFINED
#define NOWSEC_DEFINED
static double nowSec() { static auto t0 = chrono::steady_clock::now(); return chrono::duration<double>(chrono::steady_clock::now() - t0).count(); }
#endif

struct PoolBnB {
    const Inst& I; const vector<PTree>& pool; int n, R; size_t P;
    DualSimplex lp;
    vector<int> lpToPool, poolToLp;
    vector<vector<int>> cliqueEdges; vector<int> cliqueRow; vector<vector<int>> edgeCliques; set<vector<int>> cliqueSet;
    vector<int> forcedPar; vector<vector<int>> forbid; vector<int> poolFix;
    struct Log { char type; int a, b; };
    vector<Log> log;
    ll UB; vector<int> bestPar; bool haveSol = false;
    long nodes = 0, maxDepth = 0, pricedCols = 0; double rootLB = -1, lastLog = 0;
    int sbCands = 6; long sbIters = 150;
    static constexpr double BIGM = 1e8;
    vector<double> rcBuf;

    PoolBnB(const Inst& I_, const vector<PTree>& pool_, ll ub) : I(I_), pool(pool_), UB(ub) {
        n = I.n; R = n; P = pool.size();
        poolToLp.assign(P, -1); poolFix.assign(P, 0); forcedPar.assign(n, -1); forbid.assign(n, vector<int>(n + 1, 0));
        edgeCliques.assign(I.edges.size(), {});
        vector<double> cost(n, BIGM); lp.init(n, cost);
        for (int i = 0; i < n; i++) { lp.addRow({{i, 1.0}}, 1, true); lpToPool.push_back(-1); }
        lp.addRow({}, I.sc.K, false);
        lp.refactor();
    }
    double cutoff() const { return (double)UB - 1 + 1e-3; }
    bool allowed(size_t t) const {
        if (poolFix[t]) return false;
        const PTree& T = pool[t];
        for (int k = 0; k < T.na; k++) { int c = T.ch[k], p = T.pa[k]; if (forbid[c][p]) return false; if (forcedPar[c] >= 0 && forcedPar[c] != p) return false; }
        return true;
    }
    vector<pair<int, double>> buildCol(size_t t) {
        const PTree& T = pool[t]; vector<pair<int, double>> r;
        for (u64 m = T.S; m; m &= m - 1) r.push_back({__builtin_ctzll(m), 1.0});
        r.push_back({n, 1.0});
        for (int k = 0; k < T.na; k++) { int e = I.eid[T.ch[k]][T.pa[k]]; for (int ci : edgeCliques[e]) r.push_back({cliqueRow[ci], 1.0}); }
        return r;
    }
    void addPoolCols(const vector<size_t>& ts) {
        vector<vector<pair<int, double>>> cols; vector<double> costs;
        for (size_t t : ts) { cols.push_back(buildCol(t)); costs.push_back((double)pool[t].cost); poolToLp[t] = lp.N + cols.size() - 1; lpToPool.push_back(t); }
        lp.addCols(cols, costs);
    }
    void lpFix(int j) { if (lp.ub[j] != 0) { lp.ub[j] = 0; log.push_back({'L', j, 0}); } }
    void syncLP() { for (int j = n; j < lp.N; j++) if (lp.ub[j] != 0 && !allowed(lpToPool[j])) lpFix(j); }
    void undoTo(size_t sz) {
        while (log.size() > sz) {
            Log L = log.back(); log.pop_back();
            if (L.type == 'L') lp.ub[L.a] = 1;
            else if (L.type == 'P') poolFix[L.a]--;
            else if (L.type == 'F') forcedPar[L.a] = L.b;
            else if (L.type == 'B') forbid[L.a][L.b]--;
        }
    }
    // decision: type 'F' force parent, 'B' forbid arc, 'C' forbid pool columns
    struct Dec { char type; int i, p; vector<size_t> cols; };
    void apply(const Dec& d) {
        if (d.type == 'F') { log.push_back({'F', d.i, forcedPar[d.i]}); forcedPar[d.i] = d.p; }
        else if (d.type == 'B') { forbid[d.i][d.p]++; log.push_back({'B', d.i, d.p}); }
        else for (size_t t : d.cols) { poolFix[t]++; log.push_back({'P', (int)t, 0}); }
        syncLP();
    }
    vector<double> xv() { vector<double> x(lp.N); for (int j = 0; j < lp.N; j++) x[j] = lp.value(j); return x; }

    int separate(const vector<double>& x) {
        vector<double> ye(I.edges.size(), 0);
        for (int j = n; j < lp.N; j++) if (x[j] > 1e-9) { const PTree& T = pool[lpToPool[j]]; for (int k = 0; k < T.na; k++) ye[I.eid[T.ch[k]][T.pa[k]]] += x[j]; }
        vector<tuple<double, int, int>> viol;
        for (int e = 0; e < (int)I.edges.size(); e++) if (ye[e] > 1e-7) for (int f : I.cross[e]) if (f > e && ye[e] + ye[f] > 1 + 1e-6) viol.push_back({ye[e] + ye[f], e, f});
        sort(viol.rbegin(), viol.rend());
        int added = 0;
        for (auto& [v, e, f] : viol) {
            if (added >= 40) break;
            vector<int> mem = {e, f}, cands;
            for (int g : I.cross[e]) if (g != f && find(I.cross[f].begin(), I.cross[f].end(), g) != I.cross[f].end()) cands.push_back(g);
            sort(cands.begin(), cands.end(), [&](int a, int b) { return ye[a] > ye[b]; });
            for (int g : cands) { bool ok = true; for (int h : mem) if (find(I.cross[h].begin(), I.cross[h].end(), g) == I.cross[h].end()) { ok = false; break; } if (ok) mem.push_back(g); }
            sort(mem.begin(), mem.end());
            if (cliqueSet.count(mem)) continue;
            double s = 0; for (int h : mem) s += ye[h];
            if (s <= 1 + 1e-6) continue;
            cliqueSet.insert(mem);
            vector<char> inC(I.edges.size(), 0); for (int h : mem) inC[h] = 1;
            vector<pair<int, double>> r;
            for (int j = n; j < lp.N; j++) { const PTree& T = pool[lpToPool[j]]; for (int k = 0; k < T.na; k++) if (inC[I.eid[T.ch[k]][T.pa[k]]]) { r.push_back({j, 1.0}); break; } }
            int ci = cliqueEdges.size(); cliqueEdges.push_back(mem); cliqueRow.push_back(lp.m);
            for (int h : mem) edgeCliques[h].push_back(ci);
            lp.addRow(r, 1, false); added++;
        }
        return added;
    }
    // Lagrangian bound over the allowed pool; optionally collect negative-rc columns not in LP.
    double lagrangian(vector<size_t>* add, vector<double>* rcOut) {
        vector<double> y = lp.duals();
        for (int r = 0; r < lp.m; r++) if (!lp.rowEq[r] && y[r] > 0) y[r] = 0;
        vector<double> edgeDual(I.edges.size(), 0);
        for (size_t ci = 0; ci < cliqueEdges.size(); ci++) for (int e : cliqueEdges[ci]) edgeDual[e] += y[cliqueRow[ci]];
        long double L = 0;
        for (int r = 0; r < lp.m; r++) L += (long double)y[r] * lp.b[r];
        vector<pair<double, size_t>> neg;
        if (rcOut) rcOut->assign(P, 0);
        for (size_t t = 0; t < P; t++) {
            if (!allowed(t)) continue;
            const PTree& T = pool[t];
            long double rc = (long double)T.cost - y[n];
            for (u64 m = T.S; m; m &= m - 1) rc -= y[__builtin_ctzll(m)];
            for (int k = 0; k < T.na; k++) rc -= edgeDual[I.eid[T.ch[k]][T.pa[k]]];
            if (rc < 0) L += rc;
            if (rcOut) (*rcOut)[t] = (double)rc;
            if (add && rc < -1e-6 && poolToLp[t] < 0) neg.push_back({(double)rc, t});
        }
        if (add) {
            sort(neg.begin(), neg.end());
            add->clear(); for (size_t k = 0; k < neg.size() && k < 400; k++) add->push_back(neg[k].second);
        }
        return (double)L;
    }
    // solve node LP with cuts and pricing; returns Lagrangian bound (or > cutoff if pruned)
    double solveNode() {
        while (true) {
            lp.restoreDualFeas();
            auto st = lp.solve(100000000, DualSimplex::INF);
            if (st != DualSimplex::OPTIMAL) { fprintf(stderr, "master LP status %d\n", (int)st); exit(4); }
            if (separate(xv())) continue;
            vector<size_t> add;
            double L = lagrangian(&add, nullptr);
            if (L > cutoff()) return L;
            if (!add.empty()) { pricedCols += add.size(); addPoolCols(add); continue; }
            return L;
        }
    }
    void tryIntegral(const vector<double>& x) {
        for (int j = 0; j < n; j++) if (x[j] > 1e-6) return;  // artificial in use
        vector<int> par(n, -1);
        for (int j = n; j < lp.N; j++) if (x[j] > 0.5) { const PTree& T = pool[lpToPool[j]]; for (int k = 0; k < T.na; k++) par[T.ch[k]] = T.pa[k]; }
        for (int i = 0; i < n; i++) if (par[i] < 0) return;
        string why; ll c = evalLayout(I, par, nullptr, &why);
        if (c < 0) { fprintf(stderr, "FATAL: integral master solution violates rule (%s)\n", why.c_str()); exit(6); }
        if (c < UB) { UB = c; bestPar = par; haveSol = true; printf("    [%.1fs] incumbent %lld (node %ld)\n", nowSec(), c, nodes); fflush(stdout); }
    }
    // strong-branching probe; returns estimate, or 1e30 if child is rigorously pruned
    double probe(const Dec& d) {
        auto S = lp.save(); size_t ls = log.size();
        apply(d);
        lp.restoreDualFeas();
        auto st = lp.solve(sbIters, DualSimplex::INF);
        double val = lp.objective();
        if (st == DualSimplex::OPTIMAL || val > cutoff()) {
            double L = lagrangian(nullptr, nullptr);
            if (L > cutoff()) val = 1e30;
        }
        undoTo(ls); lp.restore(S);
        return val;
    }
    void node(int depth) {
        nodes++; maxDepth = max<long>(maxDepth, depth);
        if (nowSec() - lastLog > 20) { lastLog = nowSec(); printf("    [%.0fs] nodes %ld depth %d UB %lld lpcols %d rows %d\n", nowSec(), nodes, depth, UB, lp.N, lp.m); fflush(stdout); }
        size_t base = log.size();
        while (true) {
            double L = solveNode();
            if (depth == 0 && rootLB < 0) { rootLB = L; printf("    root bound %.3f (LP cols %d, rows %d)\n", L, lp.N, lp.m); fflush(stdout); }
            if (L > cutoff()) { undoTo(base); return; }
            vector<double> x = xv();
            bool integral = true; for (double v : x) if (v > 1e-6 && v < 1 - 1e-6) { integral = false; break; }
            if (integral) { tryIntegral(x); undoTo(base); return; }
            // reduced-cost fixing over the pool
            {
                vector<double> rc; double L2 = lagrangian(nullptr, &rc);
                for (size_t t = 0; t < P; t++) if (rc[t] > 0 && L2 + rc[t] > cutoff() && allowed(t)) { poolFix[t]++; log.push_back({'P', (int)t, 0}); }
                syncLP();
            }
            // candidates: fractional arcs
            map<pair<int, int>, double> ya;
            for (int j = n; j < lp.N; j++) if (x[j] > 1e-9) { const PTree& T = pool[lpToPool[j]]; for (int k = 0; k < T.na; k++) ya[{T.ch[k], T.pa[k]}] += x[j]; }
            vector<pair<double, pair<Dec, Dec>>> C;
            for (auto& [a, v] : ya) if (v > 1e-6 && v < 1 - 1e-6) C.push_back({min(v, 1 - v), {Dec{'F', a.first, a.second, {}}, Dec{'B', a.first, a.second, {}}}});
            if (C.empty()) {
                for (int j = n; j < lp.N; j++) if (x[j] > 1e-6 && x[j] < 1 - 1e-6) {
                    size_t t = lpToPool[j]; Dec up{'C', 0, 0, {}}, down{'C', 0, 0, {t}};
                    for (size_t u = 0; u < P; u++) if (u != t && (pool[u].S & pool[t].S)) up.cols.push_back(u);
                    C.push_back({min(x[j], 1 - x[j]), {up, down}});
                }
            }
            if (C.empty()) { fprintf(stderr, "no branching candidate\n"); exit(5); }
            sort(C.begin(), C.end(), [](auto& p, auto& q) { return p.first > q.first; });
            int nc = min<int>(C.size(), depth < 6 ? 2 * sbCands : sbCands);
            double z0 = lp.objective();
            int best = 0; double bestScore = -1, bL = 0, bR = 0; bool implied = false;
            for (int k = 0; k < nc; k++) {
                double l = probe(C[k].second.first), r = probe(C[k].second.second);
                if (l >= 1e29 && r >= 1e29) { undoTo(base); return; }
                if (l >= 1e29) { apply(C[k].second.second); implied = true; break; }
                if (r >= 1e29) { apply(C[k].second.first); implied = true; break; }
                double sc = max(l - z0, 1e-3) * max(r - z0, 1e-3);
                if (sc > bestScore) { bestScore = sc; best = k; bL = l; bR = r; }
            }
            if (implied) continue;
            Dec d1 = C[best].second.first, d2 = C[best].second.second;
            if (bR < bL) swap(d1, d2);
            for (int side = 0; side < 2; side++) {
                auto S = lp.save(); size_t ls = log.size();
                apply(side == 0 ? d1 : d2);
                node(depth + 1);
                undoTo(ls); lp.restore(S);
            }
            undoTo(base); return;
        }
    }
};
