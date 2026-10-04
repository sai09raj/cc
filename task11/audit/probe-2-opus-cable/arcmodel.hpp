// arcmodel.hpp -- capacity-indexed arc formulation x[i->j,q] (arc carries exactly q turbines).
// Used only to report its (weaker) root LP bound for comparison with the set-partitioning bound.
#pragma once
#include "instance.hpp"
#include "lp.hpp"
struct Model {
    const Inst& I; int n, R, Q;
    struct Arc { int from, to, edge; ll len; };
    vector<Arc> arcs; vector<vector<int>> outA, inA, edgeArcs;
    vector<int> varArc, varQ; vector<vector<int>> arcVars;  // arcVars[a][q] -> var or -1
    DualSimplex lp;
    set<vector<int>> cliqueCuts; set<pair<int, int>> loadCuts;
    Model(const Inst& I_) : I(I_) {
        n = I.n; R = n; Q = I.Q;
        outA.assign(n, {}); inA.assign(n, {}); edgeArcs.assign(I.edges.size(), {});
        for (int i = 0; i < n; i++) for (int j : I.adj[i]) {
            int a = arcs.size(); arcs.push_back({i, j, I.eid[i][j], I.len(i, j)});
            outA[i].push_back(a); if (j < n) inA[j].push_back(a); edgeArcs[I.eid[i][j]].push_back(a);
        }
        vector<double> cost;
        arcVars.assign(arcs.size(), vector<int>(Q + 1, -1));
        for (int a = 0; a < (int)arcs.size(); a++) {
            int qmax = arcs[a].to == R ? Q : Q - 1;
            for (int q = 1; q <= qmax; q++) { arcVars[a][q] = varArc.size(); varArc.push_back(a); varQ.push_back(q); cost.push_back((double)arcs[a].len * I.priceOfLoad[q]); }
        }
        lp.init(varArc.size(), cost);
        lp.head.clear(); lp.Binv.clear(); lp.xB.clear();
        for (int i = 0; i < n; i++) { vector<pair<int, double>> r; for (int a : outA[i]) for (int q = 1; q <= Q; q++) if (arcVars[a][q] >= 0) r.push_back({arcVars[a][q], 1.0}); lp.addRow(r, 1, true); }
        for (int i = 0; i < n; i++) {
            vector<pair<int, double>> r;
            for (int a : outA[i]) for (int q = 1; q <= Q; q++) if (arcVars[a][q] >= 0) r.push_back({arcVars[a][q], (double)q});
            for (int a : inA[i]) for (int q = 1; q <= Q; q++) if (arcVars[a][q] >= 0) r.push_back({arcVars[a][q], -(double)q});
            lp.addRow(r, 1, true);
        }
        { vector<pair<int, double>> r; for (int i = 0; i < n; i++) for (int a : outA[i]) if (arcs[a].to == R) for (int q = 1; q <= Q; q++) if (arcVars[a][q] >= 0) r.push_back({arcVars[a][q], 1.0}); lp.addRow(r, I.sc.K, false); }
        lp.refactor();
    }
    vector<double> xv() { vector<double> x(lp.N); for (int j = 0; j < lp.N; j++) x[j] = lp.value(j); return x; }
    vector<double> arcY(const vector<double>& x) { vector<double> y(arcs.size(), 0); for (int j = 0; j < lp.N; j++) y[varArc[j]] += x[j]; return y; }

    int separate(const vector<double>& x, int maxCuts = 60) {
        int added = 0;
        vector<double> y = arcY(x);
        vector<double> ye(I.edges.size(), 0);
        for (int a = 0; a < (int)arcs.size(); a++) ye[arcs[a].edge] += y[a];
        // crossing cliques
        vector<tuple<double, int, int>> viol;
        for (int e = 0; e < (int)I.edges.size(); e++) if (ye[e] > 1e-7) for (int f : I.cross[e]) if (f > e && ye[e] + ye[f] > 1 + 1e-6) viol.push_back({ye[e] + ye[f], e, f});
        sort(viol.rbegin(), viol.rend());
        for (auto& [v, e, f] : viol) {
            if (added >= maxCuts) break;
            vector<int> mem = {e, f};
            vector<int> cands;
            for (int g : I.cross[e]) if (g != f && find(I.cross[f].begin(), I.cross[f].end(), g) != I.cross[f].end()) cands.push_back(g);
            sort(cands.begin(), cands.end(), [&](int a, int b) { return ye[a] > ye[b]; });
            for (int g : cands) { bool ok = true; for (int h : mem) if (find(I.cross[h].begin(), I.cross[h].end(), g) == I.cross[h].end()) { ok = false; break; } if (ok) mem.push_back(g); }
            sort(mem.begin(), mem.end());
            double s = 0; for (int h : mem) s += ye[h];
            if (s <= 1 + 1e-6 || cliqueCuts.count(mem)) continue;
            cliqueCuts.insert(mem);
            vector<pair<int, double>> r;
            for (int h : mem) for (int a : edgeArcs[h]) for (int q = 1; q <= Q; q++) if (arcVars[a][q] >= 0) r.push_back({arcVars[a][q], 1.0});
            lp.addRow(r, 1, false); added++;
        }
        // child-load cuts: #children with load >= q <= floor((outload-1)/q)
        for (int i = 0; i < n && added < maxCuts; i++) for (int q = 2; q <= Q - 1; q++) {
            if (loadCuts.count({i, q})) continue;
            double lhs = 0;
            for (int a : inA[i]) for (int qq = q; qq <= Q; qq++) if (arcVars[a][qq] >= 0) lhs += x[arcVars[a][qq]];
            for (int a : outA[i]) for (int qq = 1; qq <= Q; qq++) if (arcVars[a][qq] >= 0) lhs -= (double)((qq - 1) / q) * x[arcVars[a][qq]];
            if (lhs > 1e-6) {
                loadCuts.insert({i, q});
                vector<pair<int, double>> r;
                for (int a : inA[i]) for (int qq = q; qq <= Q; qq++) if (arcVars[a][qq] >= 0) r.push_back({arcVars[a][qq], 1.0});
                for (int a : outA[i]) for (int qq = 1; qq <= Q; qq++) if (arcVars[a][qq] >= 0 && (qq - 1) / q > 0) r.push_back({arcVars[a][qq], -(double)((qq - 1) / q)});
                lp.addRow(r, 0, false); added++;
            }
        }
        return added;
    }
};


static double arcRootLP(const Inst& I, double& safe) {
    Model M(I);
    while (true) {
        auto st = M.lp.solve(10000000, DualSimplex::INF);
        if (st != DualSimplex::OPTIMAL) { safe = -1; return -1; }
        if (!M.separate(M.xv())) break;
    }
    safe = M.lp.safeBound();
    return M.lp.objective();
}
