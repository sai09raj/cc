// cable_opt.cpp -- exact optimizer for the inter-array cable layout task (C++17, std library only).
// Build:  g++ -O2 -std=c++17 -o cable_opt cable_opt.cpp
// Usage:  ./cable_opt <S1|S2|S3|S4> <field.json> <outdir> [sa_restarts=40]
//
// Pipeline
//  1. Esau-Williams greedy (baseline) and simulated annealing (initial upper bound UB0).
//  2. Enumerate every connected turbine set S with |S| <= Q (Q = largest cable capacity);
//     dynamic programming gives w(S) = cheapest feeder tree spanning S (crossings ignored).
//  3. Set-partitioning LP  min sum w(S) lam_S, each turbine covered once, sum lam <= K,
//     solved by column generation (Kelley cutting planes on the dual, own dual simplex).
//     Its duals (pi, mu) give the rigorous bound  cost >= sum pi + K mu + K min(0, min_S rc(S)).
//  4. For a target T: every feeder tree that can appear in a layout of cost <= T-1 has
//     reduced cost <= gap(T); enumerate exactly those trees (internally non-crossing).
//  5. Branch-and-cut over these tree columns (crossing cliques separated lazily, arc branching,
//     strong branching, reduced-cost fixing, rigorous Lagrangian pruning).  If it finds a layout
//     it also proves it optimal (the column set covers every layout cheaper than T);
//     if not, the optimum is >= T and T is raised.  The last target is UB0 itself.
#include "heuristics.hpp"
#include "arcmodel.hpp"
#include "poolbnb.hpp"

static void writeLayout(const Inst& I, const vector<int>& par, const string& path, const string& extra) {
    vector<int> load; ll cost = evalLayout(I, par, &load);
    FILE* f = fopen(path.c_str(), "w");
    int feeders = 0; for (int i = 0; i < I.n; i++) if (par[i] == I.n) feeders++;
    fprintf(f, "{\n  \"scenario\": \"%s\",\n  \"substation\": \"%s\",\n  \"total_cost\": %lld,\n  \"feeders\": %d,\n%s  \"layout\": {\n", I.sc.name.c_str(), I.sc.primary ? "substation_primary" : "substation_alternative", cost, feeders, extra.c_str());
    for (int i = 0; i < I.n; i++) {
        int t = I.typeOfLoad[load[i]];
        fprintf(f, "    \"%s\": {\"to\": \"%s\", \"type\": \"C%d\", \"load\": %d, \"length_m\": %lld, \"cost\": %lld}%s\n", I.names[i].c_str(), par[i] == I.n ? "OSS" : I.names[par[i]].c_str(), t + 1, load[i], I.len(i, par[i]), I.len(i, par[i]) * PRICE[t], i + 1 < I.n ? "," : "");
    }
    fprintf(f, "  }\n}\n"); fclose(f);
}


int main(int argc, char** argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s S1|S2|S3|S4 field.json outdir [sa_restarts]\n", argv[0]); return 1; }
    Scenario sc = getScenario(argv[1]); string outdir = argv[3];
    int restarts = argc > 4 ? atoi(argv[4]) : 40;
    nowSec();
    Inst I = buildInst(argv[2], sc);
    printf("%s: compiler g++ %s, C++ %ld\n", sc.name.c_str(), __VERSION__, (long)__cplusplus);
    printf("%s: n=%d Q=%d K=%d candidate cables=%zu (turbine-turbine %zu), crossing pairs=%zu\n", sc.name.c_str(), I.n, I.Q, sc.K,
           I.edges.size(), I.edges.size() - I.n, [&] { size_t c = 0; for (auto& v : I.cross) c += v.size(); return c / 2; }());
    // 1. greedy + SA
    ll greedyCost = -1;
    {
        auto g = esauWilliams(I); string why; ll gc = evalLayout(I, g, nullptr, &why);
        if (gc >= 0) { greedyCost = gc; printf("greedy (Esau-Williams) cost %lld\n", gc); writeLayout(I, g, outdir + "/" + sc.name + "_ew_greedy.json", "  \"method\": \"Esau-Williams greedy\",\n"); }
        else printf("greedy (Esau-Williams) infeasible: %s\n", why.c_str());
    }
    ll primCost = -1, costEWCost = -1;
    {
        auto p = capPrim(I); if (!p.empty()) primCost = evalLayout(I, p);
        if (primCost >= 0) { printf("greedy (capacitated Prim) cost %lld\n", primCost); writeLayout(I, p, outdir + "/" + sc.name + "_prim_greedy.json", "  \"method\": \"capacitated Prim greedy\",\n"); }
        else printf("greedy (capacitated Prim) dead end, no feasible layout\n");
        auto q = costEW(I); if (!q.empty()) costEWCost = evalLayout(I, q);
        if (costEWCost >= 0) { printf("greedy (cost-aware Esau-Williams) cost %lld\n", costEWCost); writeLayout(I, q, outdir + "/" + sc.name + "_costew_greedy.json", "  \"method\": \"cost-aware Esau-Williams greedy\",\n"); }
        else printf("greedy (cost-aware Esau-Williams) dead end, no feasible layout\n");
    }
    ll sweepCost = -1; int sweepG = 0, sweepStart = 0, sweepStrip = 0;
    {
        vector<int> bestG;
        for (int strip = 0; strip < 2; strip++)
            for (int g = (I.n + I.Q - 1) / I.Q; g <= sc.K; g++) for (int st = 0; st < I.n; st++) {
                auto p = sweepPrim(I, st, g, strip); if (p.empty()) continue;
                ll c = evalLayout(I, p); if (c < 0) continue;
                if (sweepCost < 0 || c < sweepCost) { sweepCost = c; bestG = p; sweepG = g; sweepStart = st; sweepStrip = strip; }
            }
        if (sweepCost >= 0) {
            printf("greedy (sweep+Prim) best %lld (%s order, %d groups, start %d)\n", sweepCost, sweepStrip ? "strip" : "angular", sweepG, sweepStart);
            writeLayout(I, bestG, outdir + "/" + sc.name + "_greedy.json", sweepStrip ? "  \"method\": \"sweep (strip order) + Prim greedy, best start/group count\",\n" : "  \"method\": \"sweep (angular order) + Prim greedy, best start/group count\",\n");
        } else printf("greedy (sweep+Prim) found no feasible layout\n");
    }
    double t0 = nowSec();
    ll UB0 = LLONG_MAX; vector<int> best; vector<int> star(I.n, I.n);
    for (int r = 0; r < restarts; r++) {
        SA sa(I, 1000 + r); auto res = sa.run(star, 2000000, 2e5, 3e2);
        if (res.first < UB0) { UB0 = res.first; best = res.second; }
        SA sb(I, 5000 + r); auto res2 = sb.run(best, 500000, 2e4, 1e2);
        if (res2.first < UB0) { UB0 = res2.first; best = res2.second; }
    }
    double tSA = nowSec() - t0;
    printf("SA upper bound %lld (%.1fs)\n", UB0, tSA); fflush(stdout);
    // arc-formulation root bound (for comparison only)
    double t1 = nowSec(), arcSafe; double arcLP = arcRootLP(I, arcSafe);
    printf("arc formulation root LP %.3f (%.1fs)\n", arcSafe, nowSec() - t1); fflush(stdout);
    // 2-3. sets, DP, SP bound
    double t2 = nowSec();
    FeederSets F(I); F.enumerate(); F.dp(); F.solveSP(sc.K);
    long double base = 0; for (double p : F.pi) base += p; base += (long double)sc.K * F.mu;
    double minrcTerm = (sc.K - 1) * min(0.0, F.minRC);
    ll LBsp = (ll)ceil(F.lbSP - 1e-3);
    double tSP = nowSec() - t2;
    printf("feeder sets %zu; set-partitioning LP bound %.3f -> %lld (%.1fs, %d CG rounds)\n", F.masks.size(), F.lbSP, LBsp, tSP, F.cgRounds); fflush(stdout);
    // 4-5. targets: first the SA value itself; if its pool is too large, a ladder of smaller targets
    const long POOL_LIMIT = 4000000;
    auto buildPool = [&](ll T, vector<PTree>& cols, long& setsKept, double& gap) -> bool {
        gap = (double)(T - 1 - base) - minrcTerm + 1e-3;
        TreeEnum TE(I, F); TE.limit = POOL_LIMIT; cols.clear(); setsKept = 0;
        for (size_t s = 0; s < F.masks.size(); s++) {
            double r = F.rc(s); if (r > gap) continue;
            setsKept++;
            TE.enumFeeder(F.masks[s], (ll)floor((double)F.w[s] + (gap - r)), cols);
            if (TE.overflow) return false;
        }
        return true;
    };
    vector<ll> targets;
    {
        vector<PTree> tmp; long sk; double gp;
        bool fits = UB0 < LLONG_MAX && buildPool(UB0, tmp, sk, gp);
        if (!fits) {
            ll cap = UB0 < LLONG_MAX ? UB0 : 2 * LBsp + 10000000;
            for (ll delta = max<ll>(2000, LBsp / 1000), T = LBsp + delta; T < cap; delta = delta * 3 / 2, T = LBsp + delta) targets.push_back(T);
        }
        if (UB0 < LLONG_MAX) targets.push_back(UB0);
    }
    double t3 = nowSec();
    ll opt = -1; vector<int> optPar; string runs; ll provenLB = LBsp; long totalNodes = 0;
    for (ll T : targets) {
        vector<PTree> cols; long setsKept; double gap;
        if (!buildPool(T, cols, setsKept, gap)) { printf("  target %lld: pool limit exceeded, abort\n", T); break; }
        printf("  target %lld (gap %.0f): %ld sets, %zu trees\n", T, gap, setsKept, cols.size()); fflush(stdout);
        PoolBnB B(I, cols, T);
        if (T == UB0) { B.bestPar = best; B.haveSol = true; }
        double tb = nowSec();
        B.node(0);
        totalNodes += B.nodes;
        char buf[600];
        snprintf(buf, sizeof buf, "%s    {\"target\": %lld, \"gap\": %.3f, \"sets\": %ld, \"trees\": %zu, \"root_bound\": %.3f, \"nodes\": %ld, \"max_depth\": %ld, \"priced_columns\": %ld, \"seconds\": %.1f, \"result\": \"%s\"}",
                 runs.empty() ? "" : ",\n", T, gap, setsKept, cols.size(), B.rootLB, B.nodes, B.maxDepth, B.pricedCols, nowSec() - tb,
                 B.haveSol ? (T == UB0 && B.UB == UB0 ? "incumbent proven optimal" : "solution found and proven optimal") : "no layout cheaper than target");
        runs += buf;
        printf("  target %lld done: nodes %ld, %s, %.1fs\n", T, B.nodes, B.haveSol ? "solution" : "none below target", nowSec() - tb); fflush(stdout);
        if (B.haveSol) { opt = B.UB; optPar = B.bestPar; provenLB = B.UB; break; }
        provenLB = T;
    }
    double tBB = nowSec() - t3;
    if (opt < 0) { printf("RESULT %s not solved; best %lld, proven LB %lld\n", sc.name.c_str(), UB0, provenLB); if (best.empty()) return 1; opt = UB0; optPar = best; }
    int feeders = 0; for (int i = 0; i < I.n; i++) if (optPar[i] == I.n) feeders++;
    printf("RESULT %s optimum %lld feeders %d proven_lb %lld | greedy: EW %lld costEW %lld capPrim %lld sweep %lld | SA %lld | arcLP %.1f spLP %.1f | time: SA %.1f bound %.1f exact %.1f total %.1f\n",
           sc.name.c_str(), opt, feeders, provenLB, greedyCost, costEWCost, primCost, sweepCost, UB0 == LLONG_MAX ? -1 : UB0, arcSafe, F.lbSP, tSA, tSP, tBB, nowSec());
    char extra[512];
    snprintf(extra, sizeof extra, "  \"proven_optimal\": %s,\n  \"lower_bound\": %lld,\n", provenLB == opt ? "true" : "false", provenLB);
    writeLayout(I, optPar, outdir + "/" + sc.name + "_optimal.json", extra);
    // evidence
    auto js = [](ll v) { return v < 0 || v == LLONG_MAX ? string("null") : to_string(v); };
    FILE* f = fopen((outdir + "/" + sc.name + "_evidence.json").c_str(), "w");
    fprintf(f, "{\n  \"scenario\": \"%s\",\n  \"optimal_cost\": %lld,\n  \"proven_lower_bound\": %lld,\n  \"proven_optimal\": %s,\n  \"optimal_feeders\": %d,\n", sc.name.c_str(), opt, provenLB, provenLB == opt ? "true" : "false", feeders);
    fprintf(f, "  \"greedy\": {\"esau_williams\": %s, \"cost_aware_esau_williams\": %s, \"capacitated_prim\": %s, \"sweep_prim_best\": %s},\n", js(greedyCost).c_str(), js(costEWCost).c_str(), js(primCost).c_str(), js(sweepCost).c_str());
    fprintf(f, "  \"sa_upper_bound\": %s,\n", js(UB0).c_str());
    fprintf(f, "  \"arc_formulation_root_lp\": %.3f,\n  \"feeder_sets\": %zu,\n  \"set_partitioning_lp_bound\": %.6f,\n  \"cg_rounds\": %d,\n  \"min_reduced_cost\": %.9g,\n", arcSafe, F.masks.size(), F.lbSP, F.cgRounds, F.minRC);
    fprintf(f, "  \"dual_certificate\": {\"K\": %d, \"mu\": %.9f, \"pi\": {", sc.K, F.mu);
    for (int i = 0; i < I.n; i++) fprintf(f, "%s\"%s\": %.9f", i ? ", " : "", I.names[i].c_str(), F.pi[i]);
    fprintf(f, "}},\n  \"exact_runs\": [\n%s\n  ],\n  \"time_sa_s\": %.1f,\n  \"time_bound_s\": %.1f,\n  \"time_exact_s\": %.1f,\n  \"time_total_s\": %.1f,\n  \"bnb_nodes_total\": %ld,\n  \"compiler\": \"g++ %s, __cplusplus=%ld\"\n}\n",
            runs.c_str(), tSA, tSP, tBB, nowSec(), totalNodes, __VERSION__, (long)__cplusplus);
    fclose(f);
    (void)arcLP;
    return 0;
}
