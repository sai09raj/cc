// setpart.hpp -- enumeration of feeder sets, min-cost feeder-tree DP, set-partitioning bound,
// reduced-cost filtering and enumeration of candidate feeder trees.
#pragma once
#include "instance.hpp"
#include "lp.hpp"
typedef unsigned long long u64;

struct MaskHash {  // open addressing  mask -> index
    vector<u64> keys; vector<int> vals; u64 cap;
    void init(size_t n) { cap = 1; while (cap < 2 * n + 16) cap <<= 1; keys.assign(cap, 0); vals.assign(cap, -1); }
    static u64 h(u64 x) { x ^= x >> 33; x *= 0xff51afd7ed558ccdULL; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ULL; x ^= x >> 33; return x; }
    void put(u64 k, int v) { u64 i = h(k) & (cap - 1); while (vals[i] >= 0 && keys[i] != k) i = (i + 1) & (cap - 1); keys[i] = k; vals[i] = v; }
    int get(u64 k) const { u64 i = h(k) & (cap - 1); while (vals[i] >= 0) { if (keys[i] == k) return vals[i]; i = (i + 1) & (cap - 1); } return -1; }
};

struct FeederSets {
    const Inst& I; int n, Q;
    vector<u64> nb;
    vector<u64> masks; MaskHash idx;
    vector<array<ll, 8>> g;   // g[s][k]: min cost of tree on S rooted at k-th element (uplink excluded)
    vector<ll> w;             // min cost of a feeder tree on S (incl. root cable)
    static constexpr ll BIG = (ll)4e18;
    FeederSets(const Inst& I_) : I(I_) { n = I.n; Q = I.Q; }
    static int posIn(u64 S, int v) { return __builtin_popcountll(S & ((1ULL << v) - 1)); }

    void enumerate() {
        nb.assign(n, 0);
        for (int i = 0; i < n; i++) for (int j : I.adj[i]) if (j < n) nb[i] |= 1ULL << j;
        // ESU (Wernicke) enumeration of connected induced subgraphs, each exactly once
        function<void(u64, u64, int, int)> rec = [&](u64 S, u64 ext, int v, int sz) {
            masks.push_back(S); if (sz == Q) return;
            u64 NS = 0; for (u64 t = S; t; t &= t - 1) NS |= nb[__builtin_ctzll(t)];
            while (ext) {
                int x = __builtin_ctzll(ext); ext &= ext - 1;
                u64 excl = nb[x] & ~S & ~NS & ~((2ULL << v) - 1);
                rec(S | (1ULL << x), (ext | excl) & ~(1ULL << x), v, sz + 1);
            }
        };
        for (int v = 0; v < n; v++) rec(1ULL << v, nb[v] & ~((2ULL << v) - 1), v, 1);
        sort(masks.begin(), masks.end(), [](u64 a, u64 b) { int pa = __builtin_popcountll(a), pb = __builtin_popcountll(b); return pa != pb ? pa < pb : a < b; });
        idx.init(masks.size());
        for (size_t i = 0; i < masks.size(); i++) idx.put(masks[i], i);
    }
    void dp() {
        size_t M = masks.size(); g.assign(M, {}); w.assign(M, BIG);
        for (size_t s = 0; s < M; s++) {
            u64 S = masks[s]; int sz = __builtin_popcountll(S);
            for (auto& x : g[s]) x = BIG;
            int k = 0;
            for (u64 t = S; t; t &= t - 1, k++) {
                int v = __builtin_ctzll(t);
                if (sz == 1) { g[s][k] = 0; continue; }
                u64 rest = S & ~(1ULL << v); u64 mbit = rest & (~rest + 1); u64 rest2 = rest & ~mbit;
                ll best = BIG;
                for (u64 sub = rest2;; sub = (sub - 1) & rest2) {
                    u64 T = sub | mbit, U = S & ~T;
                    int it = idx.get(T), iu = idx.get(U);
                    if (it >= 0 && iu >= 0) {
                        ll gu = g[iu][posIn(U, v)];
                        if (gu < BIG) {
                            int tsz = __builtin_popcountll(T); ll pr = I.priceOfLoad[tsz];
                            for (u64 tt = T & nb[v]; tt; tt &= tt - 1) {
                                int u = __builtin_ctzll(tt); ll gt = g[it][posIn(T, u)];
                                if (gt >= BIG) continue;
                                ll c = gt + I.len(u, v) * pr + gu;
                                if (c < best) best = c;
                            }
                        }
                    }
                    if (sub == 0) break;
                }
                g[s][k] = best;
            }
            k = 0;
            for (u64 t = S; t; t &= t - 1, k++) { int v = __builtin_ctzll(t); if (g[s][k] < BIG) w[s] = min(w[s], g[s][k] + I.len(v, n) * I.priceOfLoad[sz]); }
        }
    }

    // ---- set-partitioning LP bound by Kelley cutting planes on its dual (= column generation)
    vector<double> pi; double mu = 0; double lbSP = 0; double minRC = 0; int cgRounds = 0, cgRows = 0;
    double rc(size_t s) const { double t = (double)w[s] - mu; for (u64 m = masks[s]; m; m &= m - 1) t -= pi[__builtin_ctzll(m)]; return t; }
    void solveSP(int K) {
        DualSimplex lp; vector<double> cost(n + 1, -1.0); cost[n] = -(double)K;
        lp.init(n + 1, cost);
        const double B = 5e7;
        for (int i = 0; i < n; i++) { lp.lb[i] = -B; lp.ub[i] = B; }
        lp.lb[n] = -B; lp.ub[n] = 0;
        lp.restoreDualFeas();
        pi.assign(n, 0);
        vector<char> inLP(masks.size(), 0);
        while (true) {
            auto st = lp.solve(10000000, DualSimplex::INF);
            if (st != DualSimplex::OPTIMAL) { fprintf(stderr, "SP LP status %d\n", (int)st); exit(3); }
            for (int i = 0; i < n; i++) pi[i] = lp.value(i);
            mu = lp.value(n);
            vector<pair<double, int>> viol;
            for (size_t s = 0; s < masks.size(); s++) { double r = rc(s); if (r < -1e-6 && !inLP[s]) viol.push_back({r, (int)s}); }
            cgRounds++;
            if (viol.empty()) break;
            sort(viol.begin(), viol.end());
            // add the most violated rows, at most one per smallest element for diversity
            int added = 0; vector<int> per(n, 0);
            for (auto& [r, s] : viol) {
                int lowv = __builtin_ctzll(masks[s]);
                if (per[lowv] >= 3) continue;
                per[lowv]++;
                vector<pair<int, double>> row; for (u64 m = masks[s]; m; m &= m - 1) row.push_back({__builtin_ctzll(m), 1.0});
                row.push_back({n, 1.0});
                lp.addRow(row, (double)w[s], false); inLP[s] = 1; added++;
                if (added >= 300) break;
            }
            cgRows += added;
            lp.restoreDualFeas();
        }
        // rigorous bound: any (pi, mu<=0) gives  cost >= sum pi + K mu + K min(0, min rc)
        mu = min(mu, 0.0);
        double mr = 0; for (size_t s = 0; s < masks.size(); s++) mr = min(mr, rc(s));
        minRC = mr;
        long double z = 0; for (int i = 0; i < n; i++) z += pi[i]; z += (long double)K * mu + (long double)K * min(0.0, mr);
        lbSP = (double)z;
    }
};

// A candidate feeder tree (column)
struct TreeCol { u64 S; vector<pair<int, int>> arcs; ll cost; };  // arcs (child -> parent), parent n = root
struct PTree { u64 S; ll cost; uint8_t na; uint8_t ch[8], pa[8]; };  // compact feeder tree

struct TreeEnum {
    const Inst& I; const FeederSets& F; int n;
    vector<TreeCol>* out; long limit; bool overflow = false;
    TreeEnum(const Inst& I_, const FeederSets& F_) : I(I_), F(F_) { n = I.n; }
    // enumerate all trees on set S rooted at v (v's uplink excluded) with cost <= budget.
    // callback receives (arcs, cost)
    void enumRooted(u64 S, int v, ll budget, vector<pair<int, int>>& cur, ll curCost, const function<void(ll)>& cb) {
        // cur holds arcs collected so far; we enumerate the structure of S under v
        if (S == (1ULL << v)) { cb(curCost); return; }
        u64 rest = S & ~(1ULL << v); u64 mbit = rest & (~rest + 1); u64 rest2 = rest & ~mbit;
        for (u64 sub = rest2;; sub = (sub - 1) & rest2) {
            u64 T = sub | mbit, U = S & ~T;
            int it = F.idx.get(T), iu = F.idx.get(U);
            if (it >= 0 && iu >= 0) {
                ll gu = F.g[iu][FeederSets::posIn(U, v)];
                int tsz = __builtin_popcountll(T); ll pr = I.priceOfLoad[tsz];
                for (u64 tt = T & F.nb[v]; tt; tt &= tt - 1) {
                    int u = __builtin_ctzll(tt); ll gt = F.g[it][FeederSets::posIn(T, u)];
                    ll base = I.len(u, v) * pr;
                    if (gt >= FeederSets::BIG || gu >= FeederSets::BIG) continue;
                    if (curCost + gt + base + gu > budget) continue;
                    cur.push_back({u, v});
                    // enumerate subtree on T rooted at u, then the remainder U rooted at v
                    enumRooted(T, u, budget - gu, cur, curCost + base, [&](ll c1) {
                        enumRooted(U, v, budget, cur, c1, cb);
                    });
                    cur.pop_back();
                    if (overflow) return;
                }
            }
            if (sub == 0) break;
        }
    }
    static void add(vector<TreeCol>& r, u64 S, const vector<pair<int, int>>& cur, ll c) { r.push_back({S, cur, c}); }
    static void add(vector<PTree>& r, u64 S, const vector<pair<int, int>>& cur, ll c) {
        PTree t; t.S = S; t.cost = c; t.na = cur.size();
        for (size_t k = 0; k < cur.size(); k++) { t.ch[k] = cur[k].first; t.pa[k] = cur[k].second; }
        r.push_back(t);
    }
    // all internally non-crossing feeder trees on S with cost <= budget
    template <class OUT> void enumFeeder(u64 S, ll budget, OUT& res) {
        int sz = __builtin_popcountll(S); int s = F.idx.get(S);
        int k = 0;
        for (u64 t = S; t; t &= t - 1, k++) {
            int v = __builtin_ctzll(t);
            ll rootc = I.len(v, n) * I.priceOfLoad[sz];
            if (F.g[s][k] >= FeederSets::BIG || F.g[s][k] + rootc > budget) continue;
            vector<pair<int, int>> cur = {{v, n}};
            enumRooted(S, v, budget, cur, rootc, [&](ll c) {
                // crossing check within the tree
                for (size_t a = 0; a < cur.size(); a++) for (size_t b = a + 1; b < cur.size(); b++) {
                    int ea = I.eid[cur[a].first][cur[a].second], eb = I.eid[cur[b].first][cur[b].second];
                    for (int f : I.cross[ea]) if (f == eb) return;
                }
                add(res, S, cur, c);
                if ((long)res.size() > limit) overflow = true;
            });
        }
    }
};
