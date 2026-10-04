// lp.hpp -- bounded-variable revised dual simplex with a dense explicit basis inverse,
// bound-flipping ratio test, dynamic row addition, and a rigorous (Lagrangian) bound.
// Rows:  a_r . x + s_r = b_r,  s_r in [0,0] (equality) or [0,+inf) (<= row).
#pragma once
#include <bits/stdc++.h>
using namespace std;

struct DualSimplex {
    static constexpr double INF = 1e30;
    int N = 0, m = 0;
    vector<vector<pair<int, double>>> col;  // structural columns
    vector<double> c, lb, ub;
    vector<double> b; vector<char> rowEq;
    vector<int> head, bpos; vector<char> atUp;
    vector<double> Binv, xB, d;
    long totalIters = 0; int sinceRefactor = 0;
    double ptol = 1e-7, dtol = 1e-9, pivtol = 1e-9;

    void init(int N_, const vector<double>& cost) {
        N = N_; c = cost; lb.assign(N, 0); ub.assign(N, 1); col.assign(N, {});
        bpos.assign(N, -1); atUp.assign(N, 0); d = c; m = 0;
    }
    double lo(int j) const { return j < N ? lb[j] : 0.0; }
    double hi(int j) const { return j < N ? ub[j] : (rowEq[j - N] ? 0.0 : INF); }
    double valNB(int j) const { return atUp[j] ? hi(j) : lo(j); }
    double value(int j) const { return bpos[j] >= 0 ? xB[bpos[j]] : valNB(j); }

    // add a row over structurals; new slack enters the basis
    void addRow(const vector<pair<int, double>>& coefs, double rhs, bool eq) {
        int r = m;
        unordered_map<int, double> cm; cm.reserve(coefs.size() * 2);
        double ax = 0;
        for (auto& [j, v] : coefs) { col[j].push_back({r, v}); cm[j] += v; ax += v * value(j); }
        b.push_back(rhs); rowEq.push_back(eq);
        vector<double> nb((size_t)(m + 1) * (m + 1), 0.0);
        for (int i = 0; i < m; i++) memcpy(&nb[(size_t)i * (m + 1)], &Binv[(size_t)i * m], sizeof(double) * m);
        vector<double> aB(m, 0.0);
        for (int i = 0; i < m; i++) if (head[i] < N) { auto it = cm.find(head[i]); if (it != cm.end()) aB[i] = it->second; }
        for (int i = 0; i < m; i++) if (aB[i] != 0) {
            const double* row = &Binv[(size_t)i * m]; double f = aB[i];
            for (int k = 0; k < m; k++) nb[(size_t)m * (m + 1) + k] -= f * row[k];
        }
        nb[(size_t)m * (m + 1) + m] = 1.0;
        Binv.swap(nb);
        head.push_back(N + r); bpos.push_back(r); atUp.push_back(0); d.push_back(0.0);
        xB.push_back(rhs - ax);
        m++;
    }

    void colTimesBinv(int j, vector<double>& out) {  // out = Binv * A_j
        out.assign(m, 0.0);
        if (j >= N) { int k = j - N; for (int i = 0; i < m; i++) out[i] = Binv[(size_t)i * m + k]; return; }
        for (auto& [k, v] : col[j]) for (int i = 0; i < m; i++) out[i] += Binv[(size_t)i * m + k] * v;
    }

    bool refactor() {
        vector<double> B((size_t)m * m, 0.0);
        for (int i = 0; i < m; i++) {
            int j = head[i];
            if (j >= N) B[(size_t)(j - N) * m + i] = 1.0;
            else for (auto& [k, v] : col[j]) B[(size_t)k * m + i] = v;
        }
        // Gauss-Jordan on [B | I]
        vector<double> Inv((size_t)m * m, 0.0);
        for (int i = 0; i < m; i++) Inv[(size_t)i * m + i] = 1.0;
        for (int cc = 0; cc < m; cc++) {
            int pr = -1; double best = 0;
            for (int r = cc; r < m; r++) { double v = fabs(B[(size_t)r * m + cc]); if (v > best) { best = v; pr = r; } }
            if (best < 1e-11) { fprintf(stderr, "singular basis\n"); return false; }
            if (pr != cc) {
                for (int k = 0; k < m; k++) { swap(B[(size_t)pr * m + k], B[(size_t)cc * m + k]); swap(Inv[(size_t)pr * m + k], Inv[(size_t)cc * m + k]); }
            }
            double pv = B[(size_t)cc * m + cc];
            for (int k = 0; k < m; k++) { B[(size_t)cc * m + k] /= pv; Inv[(size_t)cc * m + k] /= pv; }
            for (int r = 0; r < m; r++) if (r != cc) {
                double f = B[(size_t)r * m + cc]; if (f == 0) continue;
                double* Br = &B[(size_t)r * m]; const double* Bc = &B[(size_t)cc * m];
                double* Ir = &Inv[(size_t)r * m]; const double* Ic = &Inv[(size_t)cc * m];
                for (int k = 0; k < m; k++) { Br[k] -= f * Bc[k]; Ir[k] -= f * Ic[k]; }
            }
        }
        Binv.swap(Inv);
        computePrimal(); computeDual(); sinceRefactor = 0;
        return true;
    }
    void computePrimal() {
        vector<double> rhs = b;
        for (int j = 0; j < N; j++) if (bpos[j] < 0) { double v = valNB(j); if (v != 0) for (auto& [k, a] : col[j]) rhs[k] -= a * v; }
        for (int r = 0; r < m; r++) { int j = N + r; if (bpos[j] < 0) { double v = valNB(j); if (v != 0) rhs[r] -= v; } }
        xB.assign(m, 0.0);
        for (int i = 0; i < m; i++) { double s = 0; const double* row = &Binv[(size_t)i * m]; for (int k = 0; k < m; k++) s += row[k] * rhs[k]; xB[i] = s; }
    }
    vector<double> duals() {
        vector<double> y(m, 0.0);
        for (int i = 0; i < m; i++) { int j = head[i]; double cb = j < N ? c[j] : 0.0; if (cb == 0) continue; const double* row = &Binv[(size_t)i * m]; for (int k = 0; k < m; k++) y[k] += cb * row[k]; }
        return y;
    }
    void computeDual() {
        vector<double> y = duals();
        d.assign(N + m, 0.0);
        for (int j = 0; j < N; j++) { double s = c[j]; for (auto& [k, a] : col[j]) s -= a * y[k]; d[j] = bpos[j] >= 0 ? 0.0 : s; }
        for (int r = 0; r < m; r++) d[N + r] = bpos[N + r] >= 0 ? 0.0 : -y[r];
    }
    // make nonbasic boxed variables sit at the dual-feasible bound, then recompute primal
    void restoreDualFeas() {
        for (int j = 0; j < N; j++) if (bpos[j] < 0) {
            if (lb[j] == ub[j]) atUp[j] = 0;
            else if (d[j] < -dtol) atUp[j] = 1; else if (d[j] > dtol) atUp[j] = 0;
        }
        computePrimal();
    }
    double objective() const { double z = 0; for (int j = 0; j < N; j++) z += c[j] * value(j); return z; }

    // rigorous Lagrangian lower bound for the LP with current bounds, from multipliers y
    double safeBound(vector<double> y) {
        for (int r = 0; r < m; r++) if (!rowEq[r] && y[r] > 0) y[r] = 0;
        long double z = 0;
        for (int r = 0; r < m; r++) z += (long double)y[r] * b[r];
        for (int j = 0; j < N; j++) {
            long double s = c[j]; for (auto& [k, a] : col[j]) s -= (long double)a * y[k];
            z += s >= 0 ? s * lb[j] : s * ub[j];
        }
        return (double)z;
    }
    double safeBound() { return safeBound(duals()); }

    enum Status { OPTIMAL, INFEASIBLE, CUTOFF, ITERLIMIT };
    vector<double> alpha, acol, dbv;
    vector<pair<double, int>> cand;
    double lastRayBound = -INF;

    Status solve(long maxIter, double cutoff) {
        alpha.assign(N + m, 0.0);
        for (long it = 0; it < maxIter; it++) {
            if (sinceRefactor >= 120) { if (!refactor()) return ITERLIMIT; }
            // choose leaving row (largest primal infeasibility)
            int r = -1; double worst = ptol;
            for (int i = 0; i < m; i++) {
                int j = head[i]; double v = xB[i], inf = 0;
                if (v < lo(j)) inf = lo(j) - v; else if (v > hi(j)) inf = v - hi(j);
                if (inf > worst) { worst = inf; r = i; }
            }
            if (r < 0) return OPTIMAL;
            int lv = head[r];
            bool below = xB[r] < lo(lv);
            double target = below ? lo(lv) : hi(lv);
            double slope = fabs(xB[r] - target);
            const double* rho = &Binv[(size_t)r * m];
            cand.clear();
            for (int j = 0; j < N + m; j++) {
                if (bpos[j] >= 0) { alpha[j] = 0; continue; }
                double a;
                if (j < N) { a = 0; for (auto& [k, v] : col[j]) a += rho[k] * v; }
                else a = rho[j - N];
                alpha[j] = a;
                if (lo(j) == hi(j)) continue;
                if (fabs(a) < pivtol) continue;
                bool ok = below ? ((!atUp[j] && a < 0) || (atUp[j] && a > 0)) : ((!atUp[j] && a > 0) || (atUp[j] && a < 0));
                if (!ok) continue;
                double dj = atUp[j] ? max(0.0, -d[j]) : max(0.0, d[j]);
                cand.push_back({dj / fabs(a), j});
            }
            if (cand.empty()) {
                // dual ray: Farkas-type certificate; evaluate bound along ray
                vector<double> y = duals(); vector<double> ray(rho, rho + m);
                double sgn = below ? -1.0 : 1.0;  // try both signs, keep the best
                double best = -INF;
                for (double s : {sgn, -sgn}) for (double lam : {1e4, 1e6, 1e8, 1e10, 1e12, 1e14, 1e16, 1e18}) {
                    vector<double> yy(m); for (int k = 0; k < m; k++) yy[k] = y[k] + s * lam * ray[k];
                    best = max(best, safeBound(yy));
                }
                lastRayBound = best;
                return INFEASIBLE;
            }
            sort(cand.begin(), cand.end());
            int K = cand.size(), stop = K - 1;
            for (int k = 0; k < K; k++) {
                int j = cand[k].second; double rng = hi(j) - lo(j);
                if (k < K - 1 && rng < 1e20 && slope - fabs(alpha[j]) * rng > 0) { slope -= fabs(alpha[j]) * rng; continue; }
                stop = k; break;
            }
            // stability: among non-flipped candidates with ratio close to stop's, take max |alpha|
            int q = cand[stop].second; double tmax = cand[stop].first + 1e-9;
            for (int k = stop + 1; k < K && cand[k].first <= tmax; k++) if (fabs(alpha[cand[k].second]) > fabs(alpha[q])) q = cand[k].second;
            // flips: candidates before stop (those are exactly the ones with lower ratio we passed)
            dbv.assign(m, 0.0); bool anyFlip = false;
            for (int k = 0; k < stop; k++) {
                int j = cand[k].second; if (j == q) continue;
                double old = valNB(j); atUp[j] ^= 1; double nw = valNB(j); double del = nw - old;
                anyFlip = true;
                if (j < N) for (auto& [kk, v] : col[j]) dbv[kk] += v * del; else dbv[j - N] += del;
            }
            if (anyFlip) {
                for (int k = 0; k < m; k++) if (dbv[k] != 0) { double f = dbv[k]; for (int i = 0; i < m; i++) xB[i] -= Binv[(size_t)i * m + k] * f; }
            }
            colTimesBinv(q, acol);
            double piv = acol[r];
            if (fabs(piv) < 1e-11) { refactor(); continue; }
            double theta = (xB[r] - target) / piv;
            double xq = valNB(q) + theta;
            for (int i = 0; i < m; i++) xB[i] -= theta * acol[i];
            double t = d[q] / alpha[q];
            for (int j = 0; j < N + m; j++) if (bpos[j] < 0) d[j] -= t * alpha[j];
            d[lv] = -t; d[q] = 0;
            bpos[lv] = -1; atUp[lv] = (target == hi(lv) && lo(lv) != hi(lv)) ? 1 : 0;
            if (lo(lv) == hi(lv)) atUp[lv] = 0;
            head[r] = q; bpos[q] = r; xB[r] = xq;
            // update Binv
            double* Rr = &Binv[(size_t)r * m];
            double ip = 1.0 / piv; for (int k = 0; k < m; k++) Rr[k] *= ip;
            for (int i = 0; i < m; i++) if (i != r) { double f = acol[i]; if (f == 0) continue; double* Ri = &Binv[(size_t)i * m]; for (int k = 0; k < m; k++) Ri[k] -= f * Rr[k]; }
            totalIters++; sinceRefactor++;
            if (cutoff < INF && (it % 5 == 4)) {
                if (objective() > cutoff) { double sb = safeBound(); if (sb > cutoff) return CUTOFF; }
            }
        }
        return ITERLIMIT;
    }

    // ---- add structural columns (boxed [0,1]); slack indices shift by the number added
    void addCols(const vector<vector<pair<int, double>>>& cols, const vector<double>& costs) {
        int add = cols.size(); if (!add) return;
        int N0 = N;
        vector<double> y = duals();
        for (auto& h : head) if (h >= N0) h += add;
        bpos.insert(bpos.begin() + N0, add, -1);
        atUp.insert(atUp.begin() + N0, add, 0);
        d.insert(d.begin() + N0, add, 0.0);
        for (int k = 0; k < add; k++) {
            col.push_back(cols[k]); c.push_back(costs[k]); lb.push_back(0); ub.push_back(1);
            double dj = costs[k]; for (auto& [r, v] : cols[k]) dj -= v * y[r];
            d[N0 + k] = dj; atUp[N0 + k] = dj < 0 ? 1 : 0;
        }
        N += add;
        computePrimal();
    }
    struct State { vector<int> head; vector<char> atUp; vector<double> Binv; int m, N; };
    State save() const { return {head, atUp, Binv, m, N}; }
    void restore(const State& s) {
        int m0 = s.m, N0 = s.N, addN = N - N0;
        head = s.head; for (auto& h : head) if (h >= N0) h += addN;
        atUp.assign(N + m, 0);
        for (int j = 0; j < N0; j++) atUp[j] = s.atUp[j];
        for (int r = 0; r < m0; r++) atUp[N + r] = s.atUp[N0 + r];
        if (m0 == m) Binv = s.Binv;
        else {
            Binv.assign((size_t)m * m, 0.0);
            for (int i = 0; i < m0; i++) memcpy(&Binv[(size_t)i * m], &s.Binv[(size_t)i * m0], sizeof(double) * m0);
            for (int r = m0; r < m; r++) {
                head.push_back(N + r);
                for (int i = 0; i < m0; i++) { int j = head[i]; if (j >= N) continue;
                    double a = 0; for (auto& [k, v] : col[j]) if (k == r) a += v;
                    if (a != 0) for (int k = 0; k < m0; k++) Binv[(size_t)r * m + k] -= a * s.Binv[(size_t)i * m0 + k];
                }
                Binv[(size_t)r * m + r] = 1.0;
            }
        }
        bpos.assign(N + m, -1); for (int i = 0; i < m; i++) bpos[head[i]] = i;
        computeDual();
        // new columns: dual-feasible bound
        for (int j = N0; j < N; j++) atUp[j] = d[j] < 0 ? 1 : 0;
        computePrimal();
    }
};
