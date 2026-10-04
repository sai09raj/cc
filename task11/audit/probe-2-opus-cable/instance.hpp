// instance.hpp -- data loading, exact geometry, scenario definition.
// C++17, standard library only.
#pragma once
#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

struct Pt { ll x, y; };
static inline bool eqPt(const Pt& a, const Pt& b) { return a.x == b.x && a.y == b.y; }
static inline ll orient(const Pt& a, const Pt& b, const Pt& c) {
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
}
static inline int sgnll(ll v) { return (v > 0) - (v < 0); }
static inline bool inBox(const Pt& a, const Pt& b, const Pt& c) {
    return min(a.x, b.x) <= c.x && c.x <= max(a.x, b.x) && min(a.y, b.y) <= c.y && c.y <= max(a.y, b.y);
}
// closed segments intersect (any common point)
static bool closedIntersect(Pt p1, Pt p2, Pt p3, Pt p4) {
    int d1 = sgnll(orient(p3, p4, p1)), d2 = sgnll(orient(p3, p4, p2));
    int d3 = sgnll(orient(p1, p2, p3)), d4 = sgnll(orient(p1, p2, p4));
    if (d1 * d2 < 0 && d3 * d4 < 0) return true;
    if (d1 == 0 && inBox(p3, p4, p1)) return true;
    if (d2 == 0 && inBox(p3, p4, p2)) return true;
    if (d3 == 0 && inBox(p1, p2, p3)) return true;
    if (d4 == 0 && inBox(p1, p2, p4)) return true;
    return false;
}
// Rule 5: cables cross if they share any point other than a common endpoint;
// collinear overlap counts even if they share an endpoint.
static bool cablesCross(Pt a1, Pt a2, Pt b1, Pt b2) {
    Pt c, a, b; bool sh = true;
    if (eqPt(a1, b1)) { c = a1; a = a2; b = b2; }
    else if (eqPt(a1, b2)) { c = a1; a = a2; b = b1; }
    else if (eqPt(a2, b1)) { c = a2; a = a1; b = b2; }
    else if (eqPt(a2, b2)) { c = a2; a = a1; b = b1; }
    else sh = false;
    if (sh) {
        if (eqPt(a, b)) return true;  // identical segment
        if (orient(c, a, b) != 0) return false;
        return (a.x - c.x) * (b.x - c.x) + (a.y - c.y) * (b.y - c.y) > 0;
    }
    return closedIntersect(a1, a2, b1, b2);
}
// Rule 3: Euclidean length rounded to nearest integer, halves up (exact integer arithmetic)
static ll roundedLen(const Pt& a, const Pt& b) {
    ll dx = a.x - b.x, dy = a.y - b.y, D = dx * dx + dy * dy;
    ll r = (ll)sqrtl((long double)D);
    while (r * r > D) --r;
    while ((r + 1) * (r + 1) <= D) ++r;
    if (4 * D >= (2 * r + 1) * (2 * r + 1)) ++r;
    return r;
}

struct Scenario { string name; bool primary; int K; int ntypes; };
static const int CAP[3] = {3, 5, 8};
static const int PRICE[3] = {100, 145, 210};

static Scenario getScenario0(const string& s);
static Scenario getScenario(const string& s) {
    Scenario sc = getScenario0(s);
    if (const char* k = getenv("CABLE_K")) sc.K = atoi(k);  // testing hook only
    return sc;
}
static Scenario getScenario0(const string& s) {
    if (s == "S1") return {"S1", true, 7, 3};
    if (s == "S2") return {"S2", true, 6, 3};
    if (s == "S3") return {"S3", true, 11, 2};
    if (s == "S4") return {"S4", false, 7, 3};
    fprintf(stderr, "unknown scenario %s\n", s.c_str()); exit(1);
}

struct Inst {
    Scenario sc;
    int n = 0;              // turbines 0..n-1, root = n
    vector<string> names;
    vector<Pt> P;           // n+1 points
    int Q = 0;              // max capacity
    vector<int> priceOfLoad; // [0..Q]
    vector<int> typeOfLoad;  // [0..Q] -> type index 0..2
    struct Edge { int u, v; ll len; };  // v may be root
    vector<Edge> edges;
    vector<vector<int>> eid;   // (n+1)x(n+1)
    vector<vector<int>> adj;   // per turbine: neighbours incl. root
    vector<vector<int>> cross; // per edge: crossing edges
    ll len(int i, int j) const { return edges[eid[i][j]].len; }
};

// minimal scanner for the known field.json structure
static void loadField(const string& path, map<string, Pt>& out) {
    ifstream f(path); if (!f) { fprintf(stderr, "cannot open %s\n", path.c_str()); exit(1); }
    stringstream ss; ss << f.rdbuf(); string s = ss.str();
    string lastKey; size_t i = 0;
    while (i < s.size()) {
        char ch = s[i];
        if (ch == '"') { size_t j = s.find('"', i + 1); lastKey = s.substr(i + 1, j - i - 1); i = j + 1; }
        else if (ch == '[') {
            size_t j = s.find(']', i); string body = s.substr(i + 1, j - i - 1);
            for (char& c : body) if (c == ',') c = ' ';
            stringstream bs(body); ll x, y; bs >> x >> y; out[lastKey] = {x, y}; i = j + 1;
        } else ++i;
    }
}

static Inst buildInst(const string& fieldPath, const Scenario& sc) {
    map<string, Pt> m; loadField(fieldPath, m);
    Inst I; I.sc = sc;
    for (auto& kv : m) if (kv.first.size() == 3 && kv.first[0] == 'T') { I.names.push_back(kv.first); I.P.push_back(kv.second); }
    I.n = I.names.size();
    I.P.push_back(m[sc.primary ? "substation_primary" : "substation_alternative"]);
    I.names.push_back("OSS");
    I.Q = CAP[sc.ntypes - 1];
    I.priceOfLoad.assign(I.Q + 1, 0); I.typeOfLoad.assign(I.Q + 1, -1);
    for (int q = 1; q <= I.Q; q++)
        for (int t = 0; t < sc.ntypes; t++) if (CAP[t] >= q) { I.priceOfLoad[q] = PRICE[t]; I.typeOfLoad[q] = t; break; }
    int n = I.n;
    I.eid.assign(n + 1, vector<int>(n + 1, -1)); I.adj.assign(n, {});
    for (int i = 0; i < n; i++) for (int j = i + 1; j <= n; j++) {
        ll L = roundedLen(I.P[i], I.P[j]);
        if (j < n && L > 1300) continue;  // rule 4
        I.eid[i][j] = I.eid[j][i] = I.edges.size(); I.edges.push_back({i, j, L});
        I.adj[i].push_back(j); if (j < n) I.adj[j].push_back(i);
    }
    int E = I.edges.size(); I.cross.assign(E, {});
    for (int a = 0; a < E; a++) for (int b = a + 1; b < E; b++) {
        auto& ea = I.edges[a]; auto& eb = I.edges[b];
        if (cablesCross(I.P[ea.u], I.P[ea.v], I.P[eb.u], I.P[eb.v])) { I.cross[a].push_back(b); I.cross[b].push_back(a); }
    }
    return I;
}

// evaluate a parent array: returns cost or -1 if infeasible (fills loads)
static ll evalLayout(const Inst& I, const vector<int>& par, vector<int>* loadsOut = nullptr, string* why = nullptr) {
    int n = I.n; vector<int> load(n, 0); int feeders = 0;
    for (int i = 0; i < n; i++) {
        int v = i, steps = 0;
        while (v != n) { if (par[v] < 0 || par[v] > n || I.eid[v][par[v]] < 0) { if (why) *why = "bad arc"; return -1; }
            load[v]++; v = par[v]; if (++steps > n) { if (why) *why = "cycle"; return -1; } }
        if (par[i] == n) feeders++;
    }
    if (feeders > I.sc.K) { if (why) *why = "feeders"; return -1; }
    ll cost = 0;
    for (int i = 0; i < n; i++) { if (load[i] > I.Q) { if (why) *why = "capacity"; return -1; } cost += I.len(i, par[i]) * I.priceOfLoad[load[i]]; }
    vector<char> used(I.edges.size(), 0);
    for (int i = 0; i < n; i++) used[I.eid[i][par[i]]] = 1;
    for (int i = 0; i < n; i++) for (int f : I.cross[I.eid[i][par[i]]]) if (used[f]) { if (why) *why = "crossing"; return -1; }
    if (loadsOut) *loadsOut = load;
    return cost;
}
