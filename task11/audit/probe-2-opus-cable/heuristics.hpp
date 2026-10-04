// heuristics.hpp -- Esau-Williams greedy (baseline) and simulated annealing (upper bounds).
#pragma once
#include "instance.hpp"

// Classic Esau-Williams greedy on cable lengths, respecting capacity Q, the feeder
// limit (keeps merging while feeders > K even at a loss) and the no-crossing rule.
static vector<int> esauWilliams(const Inst& I) {
    int n = I.n, R = n;
    vector<int> comp(n); vector<int> sz(n, 1); vector<int> gate(n);  // gate node of component
    for (int i = 0; i < n; i++) { comp[i] = i; gate[i] = i; }
    vector<char> used(I.edges.size(), 0);
    for (int i = 0; i < n; i++) used[I.eid[i][R]] = 1;
    vector<pair<int, int>> treeEdges;
    int ncomp = n;
    while (true) {
        double best = -1e18; int bi = -1, bj = -1;
        for (auto& e : I.edges) {
            if (e.v == R) continue;
            for (int dir = 0; dir < 2; dir++) {
                int i = dir ? e.v : e.u, j = dir ? e.u : e.v;
                int ci = comp[i], cj = comp[j];
                if (ci == cj || sz[ci] + sz[cj] > I.Q) continue;
                int eidx = I.eid[i][j]; bool ok = true;
                for (int f : I.cross[eidx]) if (used[f] && f != I.eid[gate[ci]][R]) { ok = false; break; }
                if (!ok) continue;
                double sav = (double)I.len(gate[ci], R) - (double)e.len;
                if (sav > best) { best = sav; bi = i; bj = j; }
            }
        }
        if (bi < 0) break;
        if (best <= 0 && ncomp <= I.sc.K) break;
        int ci = comp[bi], cj = comp[bj];
        used[I.eid[gate[ci]][R]] = 0; used[I.eid[bi][bj]] = 1; treeEdges.push_back({bi, bj});
        for (int k = 0; k < n; k++) if (comp[k] == ci) comp[k] = cj;
        sz[cj] += sz[ci]; ncomp--;
    }
    // orient
    vector<vector<int>> g(n);
    for (auto& e : treeEdges) { g[e.first].push_back(e.second); g[e.second].push_back(e.first); }
    vector<int> par(n, -2);
    for (int c = 0; c < n; c++) if (comp[c] == c || true) {
        int gt = -1; for (int k = 0; k < n; k++) if (comp[k] == comp[c] && used[I.eid[k][R]]) gt = k;
        if (gt < 0 || par[gt] != -2) continue;
        par[gt] = R; vector<int> st = {gt};
        while (!st.empty()) { int v = st.back(); st.pop_back(); for (int w : g[v]) if (par[w] == -2) { par[w] = v; st.push_back(w); } }
    }
    return par;
}

struct SA {
    const Inst& I; mt19937_64 rng;
    int n, R; vector<int> par, load; vector<char> used; ll cost = 0; int feeders = 0;
    SA(const Inst& I_, uint64_t seed) : I(I_), rng(seed) { n = I.n; R = n; }
    ll penalty() const { return 3000000LL * max(0, feeders - I.sc.K); }
    bool recompute() {  // loads + cost; false if capacity violated
        load.assign(n, 0); feeders = 0; cost = 0;
        for (int i = 0; i < n; i++) { int v = i; while (v != R) { if (++load[v] > I.Q) return false; v = par[v]; } if (par[i] == R) feeders++; }
        for (int i = 0; i < n; i++) cost += I.len(i, par[i]) * I.priceOfLoad[load[i]];
        return true;
    }
    bool inSubtree(int p, int u) { while (p != R) { if (p == u) return true; p = par[p]; } return false; }
    pair<ll, vector<int>> run(const vector<int>& init, long iters, double T0, double T1) {
        par = init; used.assign(I.edges.size(), 0);
        for (int i = 0; i < n; i++) used[I.eid[i][par[i]]] = 1;
        recompute();
        ll bestCost = LLONG_MAX; vector<int> bestPar;
        if (feeders <= I.sc.K) { bestCost = cost; bestPar = par; }
        uniform_real_distribution<double> U(0, 1);
        vector<int> path; path.reserve(64); vector<int> oldpar;
        for (long it = 0; it < iters; it++) {
            double T = T0 * pow(T1 / T0, (double)it / iters);
            int v = rng() % n; const auto& A = I.adj[v]; int p = A[rng() % A.size()];
            path.clear(); int a = v; while (a != R) { path.push_back(a); a = par[a]; }
            int k = (U(rng) < 0.6) ? 0 : (int)(rng() % path.size());
            int u = path[k];
            if (k == 0 && p == par[v]) continue;
            if (p != R && inSubtree(p, u)) continue;
            int rem = I.eid[u][par[u]], add = I.eid[v][p];
            if (rem == add) continue;
            bool ok = true; for (int f : I.cross[add]) if (used[f] && f != rem) { ok = false; break; }
            if (!ok) continue;
            ll oldCost = cost + penalty(); oldpar = par;
            par[v] = p; for (int t = 1; t <= k; t++) par[path[t]] = path[t - 1];
            used[rem] = 0; used[add] = 1;
            bool feas = recompute();
            ll newCost = cost + penalty();
            bool acc = feas && (newCost <= oldCost || U(rng) < exp((double)(oldCost - newCost) / T));
            if (!acc) { par = oldpar; used[add] = 0; used[rem] = 1; recompute(); continue; }
            if (feeders <= I.sc.K && cost < bestCost) { bestCost = cost; bestPar = par; }
        }
        return {bestCost, bestPar};
    }
};

// Sweep + Prim greedy: sort turbines by polar angle around the substation (or, strip=true, by
// y then x), cut the circular
// order (starting at turbine `start`) into g consecutive groups of balanced size (<= Q), and wire
// each group by repeatedly adding the shortest admissible cable (Prim, one feeder per group,
// <= 1300 m between turbines, no crossing with anything already laid).  Returns empty on failure.
static vector<int> sweepPrim(const Inst& I, int start, int g, bool strip = false) {
    int n = I.n, R = n;
    vector<int> ord(n); iota(ord.begin(), ord.end(), 0);
    auto ang = [&](int i) { return atan2((double)(I.P[i].y - I.P[R].y), (double)(I.P[i].x - I.P[R].x)); };
    if (strip) sort(ord.begin(), ord.end(), [&](int a, int b) { return I.P[a].y != I.P[b].y ? I.P[a].y < I.P[b].y : I.P[a].x < I.P[b].x; });
    else sort(ord.begin(), ord.end(), [&](int a, int b) { return ang(a) < ang(b); });
    rotate(ord.begin(), ord.begin() + start, ord.end());
    vector<int> par(n, -1); vector<char> used(I.edges.size(), 0);
    int pos = 0;
    for (int k = 0; k < g; k++) {
        int sz = n / g + (k < n % g ? 1 : 0);
        if (sz > I.Q) return {};
        vector<int> grp(ord.begin() + pos, ord.begin() + pos + sz); pos += sz;
        vector<char> in(n, 0); bool feeder = false;
        for (int step = 0; step < sz; step++) {
            ll bl = LLONG_MAX; int bu = -1, bv = -1;
            for (int u : grp) if (!in[u]) {
                vector<int> cands; if (!feeder) cands.push_back(R);
                for (int v : grp) if (in[v] && I.eid[u][v] >= 0) cands.push_back(v);
                for (int v : cands) {
                    int e = I.eid[u][v]; ll L = I.edges[e].len; if (L >= bl) continue;
                    bool ok = true; for (int f : I.cross[e]) if (used[f]) { ok = false; break; }
                    if (ok) { bl = L; bu = u; bv = v; }
                }
            }
            if (bu < 0) return {};
            in[bu] = 1; par[bu] = bv; used[I.eid[bu][bv]] = 1; if (bv == R) feeder = true;
        }
    }
    return par;
}

// Capacitated Prim greedy: grow from the substation; at every step add the shortest admissible
// cable joining an unconnected turbine to the tree (feeder subtree stays <= Q turbines, at most K
// feeders, <= 1300 m between turbines, no crossing).  Returns empty on failure (dead end).
static vector<int> capPrim(const Inst& I) {
    int n = I.n, R = n;
    vector<int> par(n, -1), top(n, -1), feederSize(n, 0); vector<char> used(I.edges.size(), 0);
    int feeders = 0;
    for (int step = 0; step < n; step++) {
        ll bl = LLONG_MAX; int bu = -1, bv = -1;
        for (int u = 0; u < n; u++) if (par[u] < 0) for (int v : I.adj[u]) {
            if (v == R) { if (feeders >= I.sc.K) continue; }
            else { if (par[v] < 0 || feederSize[top[v]] >= I.Q) continue; }
            int e = I.eid[u][v]; ll L = I.edges[e].len; if (L >= bl) continue;
            bool ok = true; for (int f : I.cross[e]) if (used[f]) { ok = false; break; }
            if (ok) { bl = L; bu = u; bv = v; }
        }
        if (bu < 0) return {};
        par[bu] = bv; used[I.eid[bu][bv]] = 1;
        if (bv == R) { feeders++; top[bu] = bu; } else top[bu] = top[bv];
        feederSize[top[bu]]++;
    }
    return par;
}

// Cost-aware Esau-Williams: start with every turbine on its own feeder; repeatedly perform the
// merge "re-root feeder tree A at turbine i and hang it below turbine j of another feeder tree"
// with the largest exact saving in total cable cost (true cable types and loads), subject to
// capacity, the 1300 m limit and no crossings.  Stops when no merge saves money and the feeder
// count is within the bay limit; while too many feeders remain it takes the least costly merge.
// Returns empty on a dead end.
static vector<int> costEW(const Inst& I) {
    int n = I.n, R = n;
    vector<int> par(n, R);
    auto cost = [&](const vector<int>& p) {
        vector<int> load(n, 0);
        for (int i = 0; i < n; i++) for (int v = i; v != R; v = p[v]) load[v]++;
        ll c = 0; for (int i = 0; i < n; i++) { if (load[i] > I.Q) return (ll)-1; c += I.len(i, p[i]) * I.priceOfLoad[load[i]]; }
        return c;
    };
    auto topOf = [&](const vector<int>& p, int v) { while (p[v] != R) v = p[v]; return v; };
    ll cur = cost(par);
    while (true) {
        int feeders = 0; for (int i = 0; i < n; i++) if (par[i] == R) feeders++;
        vector<char> used(I.edges.size(), 0); for (int i = 0; i < n; i++) used[I.eid[i][par[i]]] = 1;
        ll best = LLONG_MAX; vector<int> bestPar;
        for (int i = 0; i < n; i++) for (int j : I.adj[i]) {
            if (j == R) continue;
            int ti = topOf(par, i), tj = topOf(par, j); if (ti == tj) continue;
            int e = I.eid[i][j], rem = I.eid[ti][R]; bool ok = true;
            for (int f : I.cross[e]) if (used[f] && f != rem) { ok = false; break; }
            if (!ok) continue;
            vector<int> p = par;  // re-root A at i: reverse path i..ti
            int prev = j, v = i; while (true) { int nx = p[v]; p[v] = prev; if (v == ti) break; prev = v; v = nx; }
            ll c = cost(p); if (c < 0) continue;
            if (c - cur < best) { best = c - cur; bestPar = p; }
        }
        if (bestPar.empty()) return feeders <= I.sc.K ? par : vector<int>();
        if (best >= 0 && feeders <= I.sc.K) return par;
        par = bestPar; cur += best;
    }
}
