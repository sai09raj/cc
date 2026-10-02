#!/usr/bin/env python3
"""TYPECHAIN-9 independent bidirectional type checker (S05).

Structurally different from typecheck_engine.py's Algorithm-W-style
unification-driven inference: this module is handed a SUBMITTED scheme
for every top-level binding and verifies each binding's body actually
has that type, in checking mode, rather than inferring types from
scratch bottom-up. It never imports typecheck_engine's own
substitution, environment, or any computed intermediate value -- it
shares only immutable input constants (the grammar/parser logic and the
program text itself, which any from-scratch implementation would need).

Every scheme, top-level (submitted certificate) or local (a nested
let), is represented uniformly as (quantified: list[MVar], type: a
type tree built from these same MVar objects). instantiate() copies the
type, substituting a FRESH MVar for each quantified variable and
leaving every other MVar (free in the type, shared with the enclosing
environment) untouched by identity -- this identity-sharing is exactly
what makes the over-generalization check below work: if a binding's
claimed scheme wrongly quantifies a variable that should have stayed
shared with the environment, two "independent" instantiations will
silently end up needing to unify that variable's fresh copies together.

Soundness check for S02 (this is what makes mutation B detectable):
when checking a top-level binding against its claimed scheme,
instantiate it, and track every (quantified-var -> fresh-var) binding
used system-wide for that binding's own instantiations during the
proof. If checking the body successfully requires unifying two DISTINCT
fresh copies of what the claim asserted were independent quantified
variables, the claim over-generalizes -- reject, even though a naive
check against one arbitrary instantiation would "succeed".
"""


class CheckError(Exception):
    pass


# ---------------------------------------------------------------------
# Local type representation (kept deliberately separate from
# typecheck_engine's TVar/TCon/... classes -- no shared code).
# ---------------------------------------------------------------------
class MVar:
    _n = [0]
    def __init__(self):
        self.id = MVar._n[0]
        MVar._n[0] += 1
    def __repr__(self):
        return f"?{self.id}"


class Con:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name


class Arrow:
    def __init__(self, a, b):
        self.a, self.b = a, b
    def __repr__(self):
        return f"({self.a}->{self.b})"


class Pair:
    def __init__(self, a, b):
        self.a, self.b = a, b
    def __repr__(self):
        return f"({self.a}*{self.b})"


class Lst:
    def __init__(self, a):
        self.a = a
    def __repr__(self):
        return f"List({self.a})"


IINT = Con("Int")
IBOOL = Con("Bool")


def walk(t, sub):
    while isinstance(t, MVar) and t in sub:
        t = sub[t]
    return t


def occurs(v, t, sub):
    t = walk(t, sub)
    if t is v:
        return True
    if isinstance(t, Arrow):
        return occurs(v, t.a, sub) or occurs(v, t.b, sub)
    if isinstance(t, Pair):
        return occurs(v, t.a, sub) or occurs(v, t.b, sub)
    if isinstance(t, Lst):
        return occurs(v, t.a, sub)
    return False


def unify(t1, t2, sub):
    t1, t2 = walk(t1, sub), walk(t2, sub)
    if isinstance(t1, MVar) and isinstance(t2, MVar) and t1 is t2:
        return
    if isinstance(t1, MVar):
        if occurs(t1, t2, sub):
            raise CheckError(f"occurs check: {t1} occurs in {t2}")
        sub[t1] = t2
        return
    if isinstance(t2, MVar):
        unify(t2, t1, sub)
        return
    if isinstance(t1, Con) and isinstance(t2, Con):
        if t1.name != t2.name:
            raise CheckError(f"cannot unify {t1} with {t2}")
        return
    if isinstance(t1, Arrow) and isinstance(t2, Arrow):
        unify(t1.a, t2.a, sub)
        unify(t1.b, t2.b, sub)
        return
    if isinstance(t1, Pair) and isinstance(t2, Pair):
        unify(t1.a, t2.a, sub)
        unify(t1.b, t2.b, sub)
        return
    if isinstance(t1, Lst) and isinstance(t2, Lst):
        unify(t1.a, t2.a, sub)
        return
    raise CheckError(f"cannot unify {t1} with {t2}")


def free_mvars(t, sub):
    t = walk(t, sub)
    if isinstance(t, MVar):
        return {t}
    if isinstance(t, Arrow):
        return free_mvars(t.a, sub) | free_mvars(t.b, sub)
    if isinstance(t, Pair):
        return free_mvars(t.a, sub) | free_mvars(t.b, sub)
    if isinstance(t, Lst):
        return free_mvars(t.a, sub)
    return set()


def copy_type(t, mapping):
    if isinstance(t, MVar):
        return mapping.get(t, t)
    if isinstance(t, Arrow):
        return Arrow(copy_type(t.a, mapping), copy_type(t.b, mapping))
    if isinstance(t, Pair):
        return Pair(copy_type(t.a, mapping), copy_type(t.b, mapping))
    if isinstance(t, Lst):
        return Lst(copy_type(t.a, mapping))
    return t


def instantiate(scheme, trace=None):
    """scheme = (quantified: list[MVar], type). Returns a fresh copy of
    type with each quantified var replaced by a brand-new MVar; other
    MVars pass through unchanged (shared by identity with whatever else
    references them). If `trace` (a list) is given, appends
    (original_quantified_var, fresh_var) pairs for the over-
    generalization check."""
    quant, t = scheme
    if not quant:
        return t
    mapping = {}
    for q in quant:
        fresh = MVar()
        mapping[q] = fresh
        if trace is not None:
            trace.append((q, fresh))
    return copy_type(t, mapping)


# ---------------------------------------------------------------------
# S06-template -> local-scheme conversion for the SUBMITTED certificate.
# The caller (score_counterfactual.py / the glue around real submissions)
# builds `claimed: dict[name, (quantified_mvars, type)]` once, using
# fresh MVar objects as the "canonical" quantified placeholders for each
# top-level scheme; `instantiate()` then makes a fresh copy per use.
# ---------------------------------------------------------------------

def _eligible(e1, cenv):
    """Mirrors S02 exactly -- the checker enforces the same stated rule
    independently; it does not import is_generalization_eligible."""
    if e1[0] == "fun":
        return True
    if e1[0] == "var" and e1[1] in cenv:
        quant, _ = cenv[e1[1]]
        return len(quant) > 0
    return False


def synth(e, cenv, sub):
    """cenv: name -> (quantified: list[MVar], type)."""
    tag = e[0]
    if tag == "int":
        return IINT
    if tag == "bool":
        return IBOOL
    if tag == "var":
        name = e[1]
        if name not in cenv:
            raise CheckError(f"unbound variable {name}")
        return instantiate(cenv[name])
    if tag == "fun":
        _, param, body = e
        tparam = MVar()
        cenv2 = dict(cenv)
        cenv2[param] = ([], tparam)
        tbody = synth(body, cenv2, sub)
        return Arrow(walk(tparam, sub), tbody)
    if tag == "app":
        _, fn, arg = e
        tfn = synth(fn, cenv, sub)
        targ = synth(arg, cenv, sub)
        tret = MVar()
        unify(tfn, Arrow(targ, tret), sub)
        return walk(tret, sub)
    if tag == "let":
        _, name, e1, e2 = e
        eligible = _eligible(e1, cenv)
        t1 = synth(e1, cenv, sub)
        if eligible:
            env_free = set()
            for q, t in cenv.values():
                env_free |= free_mvars(t, sub) - set(q)
            quant = sorted(free_mvars(t1, sub) - env_free, key=lambda v: v.id)
            scheme = (quant, walk(t1, sub))
        else:
            scheme = ([], walk(t1, sub))
        cenv2 = dict(cenv)
        cenv2[name] = scheme
        return synth(e2, cenv2, sub)
    if tag == "if":
        _, c, t_, f_ = e
        tc = synth(c, cenv, sub)
        unify(tc, IBOOL, sub)
        tt = synth(t_, cenv, sub)
        tf = synth(f_, cenv, sub)
        unify(tt, tf, sub)
        return walk(tt, sub)
    if tag == "prim2":
        _, op, e1, e2 = e
        t1 = synth(e1, cenv, sub)
        unify(t1, IINT, sub)
        t2 = synth(e2, cenv, sub)
        unify(t2, IINT, sub)
        return IBOOL if op in ("<", "==") else IINT
    if tag == "pair":
        _, e1, e2 = e
        t1 = synth(e1, cenv, sub)
        t2 = synth(e2, cenv, sub)
        return Pair(walk(t1, sub), t2)
    if tag == "fst":
        t1 = synth(e[1], cenv, sub)
        a, b = MVar(), MVar()
        unify(t1, Pair(a, b), sub)
        return walk(a, sub)
    if tag == "snd":
        t1 = synth(e[1], cenv, sub)
        a, b = MVar(), MVar()
        unify(t1, Pair(a, b), sub)
        return walk(b, sub)
    if tag == "nil":
        return Lst(MVar())
    if tag == "cons":
        _, e1, e2 = e
        t1 = synth(e1, cenv, sub)
        t2 = synth(e2, cenv, sub)
        unify(t2, Lst(walk(t1, sub)), sub)
        return walk(t2, sub)
    if tag == "isnil":
        t1 = synth(e[1], cenv, sub)
        unify(t1, Lst(MVar()), sub)
        return IBOOL
    if tag == "head":
        t1 = synth(e[1], cenv, sub)
        a = MVar()
        unify(t1, Lst(a), sub)
        return walk(a, sub)
    if tag == "tail":
        t1 = synth(e[1], cenv, sub)
        a = MVar()
        unify(t1, Lst(a), sub)
        return Lst(walk(a, sub))
    raise CheckError(f"unknown expression node {e!r}")


def check_program(bindings, claimed):
    """bindings: list of (name, expr) from the shared parser.
    claimed: dict name -> (quantified: list[MVar], type) -- the
    SUBMITTED certificate, already converted to this module's local
    type representation (see score_counterfactual.py's converter).
    Returns (ok: bool, report: list[str])."""
    cenv = {}
    report = []
    ok = True
    for name, e1 in bindings:
        sub = {}
        scheme = claimed.get(name)
        if scheme is None:
            report.append(f"{name}: NO CLAIMED TYPE SUBMITTED -- reject")
            ok = False
            continue
        quant, template = scheme
        trace_list = []
        over_gen_trace = {"_current": trace_list}
        try:
            fresh_claimed = instantiate((quant, template), trace=None)
            eligible = _eligible(e1, cenv)
            inferred = synth(e1, cenv, sub)
            unify(inferred, fresh_claimed, sub)
            # Over-generalization check: instantiate the claim a SECOND
            # time (independently) and verify its quantified vars don't
            # collapse into each other or into the body's own free vars
            # beyond what the first pass already required.
            trace2 = []
            fresh2 = instantiate((quant, template), trace=trace2)
            sub2 = dict(sub)
            unify(inferred, fresh2, sub2)
            reps = set()
            for _, v in trace2:
                r = walk(v, sub2)
                reps.add(id(r) if isinstance(r, MVar) else repr(r))
            if len(reps) < len(trace2):
                report.append(f"{name}: REJECT -- claimed scheme over-generalizes "
                               f"(quantified variables claimed independent are "
                               f"actually forced to coincide)")
                ok = False
                continue
            report.append(f"{name}: accept")
        except CheckError as ex:
            report.append(f"{name}: REJECT -- {ex}")
            ok = False
            continue
        cenv[name] = (quant, template)
    return ok, report
