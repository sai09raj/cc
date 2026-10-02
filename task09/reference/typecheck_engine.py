#!/usr/bin/env python3
"""TYPECHAIN-9 reference type inference engine.

Implements S01-S03, S06: a small S-expression-syntax functional
language, Hindley-Milner-style inference via Algorithm W, with S02's
bespoke (stricter-than-ML) generalization rule and S03's occurs-check,
and S06's fully mechanical certificate serialization. Offline,
stdlib-only, deterministic.
"""
import hashlib
import re

# ---------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------
class TVar:
    _counter = [0]
    def __init__(self, name=None):
        if name is None:
            name = f"_v{TVar._counter[0]}"
            TVar._counter[0] += 1
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, TVar) and self.name == other.name
    def __hash__(self):
        return hash(("TVar", self.name))

class TCon:
    """Int, Bool."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, TCon) and self.name == other.name
    def __hash__(self):
        return hash(("TCon", self.name))

class TArrow:
    def __init__(self, a, b):
        self.a, self.b = a, b
    def __repr__(self):
        return f"({self.a}->{self.b})"

class TPair:
    def __init__(self, a, b):
        self.a, self.b = a, b
    def __repr__(self):
        return f"({self.a}*{self.b})"

class TList:
    def __init__(self, a):
        self.a = a
    def __repr__(self):
        return f"List({self.a})"

INT = TCon("Int")
BOOL = TCon("Bool")


def ftv(t):
    """Free type variables of a type, as a set."""
    if isinstance(t, TVar):
        return {t}
    if isinstance(t, TCon):
        return set()
    if isinstance(t, TArrow):
        return ftv(t.a) | ftv(t.b)
    if isinstance(t, TPair):
        return ftv(t.a) | ftv(t.b)
    if isinstance(t, TList):
        return ftv(t.a)
    raise TypeError(f"unknown type node {t!r}")


def ftv_env(env):
    s = set()
    for scheme in env.values():
        s |= ftv_scheme(scheme)
    return s


def ftv_scheme(scheme):
    quant, t = scheme
    return ftv(t) - set(quant)


# ---------------------------------------------------------------------
# Substitutions
# ---------------------------------------------------------------------
def apply(sub, t):
    if isinstance(t, TVar):
        return apply(sub, sub[t]) if t in sub else t
    if isinstance(t, TCon):
        return t
    if isinstance(t, TArrow):
        return TArrow(apply(sub, t.a), apply(sub, t.b))
    if isinstance(t, TPair):
        return TPair(apply(sub, t.a), apply(sub, t.b))
    if isinstance(t, TList):
        return TList(apply(sub, t.a))
    raise TypeError(f"unknown type node {t!r}")


def apply_env(sub, env):
    return {k: (quant, apply(sub, t)) for k, (quant, t) in env.items()}


def compose(sub2, sub1):
    """sub2 after sub1: apply sub1 first, then sub2."""
    out = {k: apply(sub2, v) for k, v in sub1.items()}
    for k, v in sub2.items():
        if k not in out:
            out[k] = v
    return out


class UnifyError(Exception):
    pass


def unify(t1, t2):
    """Returns a substitution. Raises UnifyError (including on occurs-
    check failure, S03) if t1 and t2 cannot be unified."""
    if isinstance(t1, TVar):
        return bind_var(t1, t2)
    if isinstance(t2, TVar):
        return bind_var(t2, t1)
    if isinstance(t1, TCon) and isinstance(t2, TCon):
        if t1.name == t2.name:
            return {}
        raise UnifyError(f"cannot unify {t1} with {t2}")
    if isinstance(t1, TArrow) and isinstance(t2, TArrow):
        s1 = unify(t1.a, t2.a)
        s2 = unify(apply(s1, t1.b), apply(s1, t2.b))
        return compose(s2, s1)
    if isinstance(t1, TPair) and isinstance(t2, TPair):
        s1 = unify(t1.a, t2.a)
        s2 = unify(apply(s1, t1.b), apply(s1, t2.b))
        return compose(s2, s1)
    if isinstance(t1, TList) and isinstance(t2, TList):
        return unify(t1.a, t2.a)
    raise UnifyError(f"cannot unify {t1} with {t2}")


def bind_var(v, t):
    if isinstance(t, TVar) and t.name == v.name:
        return {}
    if not MUTANT["no_occurs_check"] and v in ftv(t):  # S03 occurs-check
        raise UnifyError(f"occurs check: {v} occurs in {t}")
    return {v: t}


# ---------------------------------------------------------------------
# Expressions (S-expression AST, already parsed -- see parse())
# ---------------------------------------------------------------------
# Represented as Python tuples:
#   ('int', n) | ('bool', b) | ('var', name)
#   ('fun', param, body) | ('app', fn, arg)
#   ('let', name, e1, e2)
#   ('if', c, t, f)
#   ('prim2', op, e1, e2)   -- op in + - * < ==
#   ('pair', e1, e2) | ('fst', e) | ('snd', e)
#   ('nil',) | ('cons', e1, e2) | ('isnil', e) | ('head', e) | ('tail', e)

def instantiate(scheme):
    quant, t = scheme
    sub = {q: TVar() for q in quant}
    return apply(sub, t)


# Mutant hooks for the score-topology audit (reference/score_counterfactual.py)
# and the two required adversarial-mutation tests. Unset = correct S02/S03.
MUTANT = {
    "no_occurs_check": False,         # S10 mutation A
    "no_env_exclusion": False,        # S10 mutation B / closure_pair_* divergence
    "no_alias_eligibility": False,    # drops S02's second eligibility clause
    "ml_value_restriction": False,    # generalizes literals/pairs/lists too (S02 vs standard ML)
    "unsubstituted_exclusion_env": False,  # excludes ftv(pre-substitution env), not post
}


def is_generalization_eligible(e1, env):
    """S02: generalize only if e1 is syntactically a lambda, or a bare
    variable reference to a name already bound to a POLYMORPHIC scheme
    (non-empty quantifier list) in env."""
    if e1[0] == "fun":
        return True
    if e1[0] == "var" and not MUTANT["no_alias_eligibility"]:
        name = e1[1]
        if name in env:
            quant, _ = env[name]
            return len(quant) > 0
    if MUTANT["ml_value_restriction"] and e1[0] in ("int", "bool", "nil", "pair", "cons"):
        return True
    return False


def infer(e, env, sub):
    """Returns (sub', type). sub is the substitution accumulated so
    far; env is name -> (quant_list, type) scheme."""
    tag = e[0]

    if tag == "int":
        return sub, INT
    if tag == "bool":
        return sub, BOOL
    if tag == "var":
        name = e[1]
        if name not in env:
            raise UnifyError(f"unbound variable {name}")
        return sub, instantiate(env[name])
    if tag == "fun":
        _, param, body = e
        tv = TVar()
        env2 = dict(env)
        env2[param] = ([], tv)
        sub1, tbody = infer(body, env2, sub)
        return sub1, TArrow(apply(sub1, tv), tbody)
    if tag == "app":
        _, fn, arg = e
        sub1, tfn = infer(fn, env, sub)
        sub2, targ = infer(arg, apply_env(sub1, env), sub1)
        tv = TVar()
        s3 = unify(apply(sub2, tfn), TArrow(targ, tv))
        sub3 = compose(s3, sub2)
        return sub3, apply(sub3, tv)
    if tag == "let":
        _, name, e1, e2 = e
        eligible = is_generalization_eligible(e1, env)
        sub1, t1 = infer(e1, env, sub)
        env1 = apply_env(sub1, env)
        if eligible:
            exclusion_env = env if MUTANT["unsubstituted_exclusion_env"] else env1
            quant = sorted(
                ftv(t1) if MUTANT["no_env_exclusion"] else ftv(t1) - ftv_env(exclusion_env),
                key=lambda v: v.name,
            )
            scheme = (quant, t1)
        else:
            scheme = ([], t1)
        env2 = dict(env1)
        env2[name] = scheme
        sub2, t2 = infer(e2, env2, sub1)
        return sub2, t2
    if tag == "if":
        _, c, t_, f_ = e
        sub1, tc = infer(c, env, sub)
        s2 = unify(apply(sub1, tc), BOOL)
        sub2 = compose(s2, sub1)
        sub3, tt = infer(t_, apply_env(sub2, env), sub2)
        sub4, tf = infer(f_, apply_env(sub3, env), sub3)
        s5 = unify(apply(sub4, tt), tf)
        sub5 = compose(s5, sub4)
        return sub5, apply(sub5, tf)
    if tag == "prim2":
        _, op, e1, e2 = e
        sub1, t1 = infer(e1, env, sub)
        s2 = unify(apply(sub1, t1), INT)
        sub2 = compose(s2, sub1)
        sub3, t2 = infer(e2, apply_env(sub2, env), sub2)
        s4 = unify(apply(sub3, t2), INT)
        sub4 = compose(s4, sub3)
        result = BOOL if op in ("<", "==") else INT
        return sub4, result
    if tag == "pair":
        _, e1, e2 = e
        sub1, t1 = infer(e1, env, sub)
        sub2, t2 = infer(e2, apply_env(sub1, env), sub1)
        return sub2, TPair(apply(sub2, t1), t2)
    if tag == "fst":
        _, e1 = e
        sub1, t1 = infer(e1, env, sub)
        a, b = TVar(), TVar()
        s2 = unify(apply(sub1, t1), TPair(a, b))
        sub2 = compose(s2, sub1)
        return sub2, apply(sub2, a)
    if tag == "snd":
        _, e1 = e
        sub1, t1 = infer(e1, env, sub)
        a, b = TVar(), TVar()
        s2 = unify(apply(sub1, t1), TPair(a, b))
        sub2 = compose(s2, sub1)
        return sub2, apply(sub2, b)
    if tag == "nil":
        return sub, TList(TVar())
    if tag == "cons":
        _, e1, e2 = e
        sub1, t1 = infer(e1, env, sub)
        sub2, t2 = infer(e2, apply_env(sub1, env), sub1)
        s3 = unify(apply(sub2, t2), TList(apply(sub2, t1)))
        sub3 = compose(s3, sub2)
        return sub3, apply(sub3, t2)
    if tag == "isnil":
        _, e1 = e
        sub1, t1 = infer(e1, env, sub)
        a = TVar()
        s2 = unify(apply(sub1, t1), TList(a))
        sub2 = compose(s2, sub1)
        return sub2, BOOL
    if tag == "head":
        _, e1 = e
        sub1, t1 = infer(e1, env, sub)
        a = TVar()
        s2 = unify(apply(sub1, t1), TList(a))
        sub2 = compose(s2, sub1)
        return sub2, apply(sub2, a)
    if tag == "tail":
        _, e1 = e
        sub1, t1 = infer(e1, env, sub)
        a = TVar()
        s2 = unify(apply(sub1, t1), TList(a))
        sub2 = compose(s2, sub1)
        return sub2, apply(sub2, TList(a))
    raise TypeError(f"unknown expression node {e!r}")


# ---------------------------------------------------------------------
# Top-level program: a list of (name, expr) bindings
# ---------------------------------------------------------------------
def infer_program(bindings):
    """Returns a list of (name, quant_list, type, generalized_bool)."""
    env = {}
    sub = {}
    results = []
    for name, e1 in bindings:
        eligible = is_generalization_eligible(e1, env)
        sub1, t1 = infer(e1, env, sub)
        env1 = apply_env(sub1, env)
        if eligible:
            exclusion_env = env if MUTANT["unsubstituted_exclusion_env"] else env1
            quant = sorted(
                ftv(t1) if MUTANT["no_env_exclusion"] else ftv(t1) - ftv_env(exclusion_env),
                key=lambda v: v.name,
            )
            scheme = (quant, t1)
        else:
            scheme = ([], t1)
        env1[name] = scheme
        env, sub = env1, sub1
        results.append((name, scheme[0], scheme[1], eligible))
    return results


# ---------------------------------------------------------------------
# S-expression parser (text -> AST)
# ---------------------------------------------------------------------
def tokenize(text):
    return re.findall(r"\(|\)|[^\s()]+", text)


def parse_tokens(tokens):
    tok = tokens.pop(0)
    if tok == "(":
        items = []
        while tokens[0] != ")":
            items.append(parse_tokens(tokens))
        tokens.pop(0)  # ')'
        return parse_form(items)
    else:
        return atom(tok)


def atom(tok):
    if tok == "true":
        return ("bool", True)
    if tok == "false":
        return ("bool", False)
    if tok == "nil":
        return ("nil",)
    if re.fullmatch(r"-?\d+", tok):
        return ("int", int(tok))
    return ("var", tok)


def parse_form(items):
    head = items[0]
    if head == ("var", "fun"):
        return ("fun", items[1][1], items[2])
    if head == ("var", "let"):
        return ("let", items[1][1], items[2], items[3])
    if head == ("var", "if"):
        return ("if", items[1], items[2], items[3])
    if head in (("var", "+"), ("var", "-"), ("var", "*"), ("var", "<"), ("var", "==")):
        return ("prim2", head[1], items[1], items[2])
    if head == ("var", "pair"):
        return ("pair", items[1], items[2])
    if head == ("var", "fst"):
        return ("fst", items[1])
    if head == ("var", "snd"):
        return ("snd", items[1])
    if head == ("var", "cons"):
        return ("cons", items[1], items[2])
    if head == ("var", "isnil"):
        return ("isnil", items[1])
    if head == ("var", "head"):
        return ("head", items[1])
    if head == ("var", "tail"):
        return ("tail", items[1])
    # application: ((f a) ...) or (f a) -- left-assoc application of items
    node = items[0]
    for arg in items[1:]:
        node = ("app", node, arg)
    return node


def parse_expr(text):
    tokens = tokenize(text)
    node = parse_tokens(tokens)
    assert not tokens, f"trailing tokens: {tokens}"
    return node


def parse_program(text):
    """Parses `(program (def name1 e1) (def name2 e2) ...)`."""
    tokens = tokenize(text)
    assert tokens.pop(0) == "("
    assert tokens.pop(0) == "program"
    bindings = []
    while tokens[0] != ")":
        assert tokens.pop(0) == "("
        assert tokens.pop(0) == "def"
        name = tokens.pop(0)
        e = parse_tokens(tokens)
        assert tokens.pop(0) == ")"
        bindings.append((name, e))
    tokens.pop(0)  # final ')'
    return bindings


# ---------------------------------------------------------------------
# S06: certification
# ---------------------------------------------------------------------
def render_type(t, varnames):
    if isinstance(t, TVar):
        return varnames[t.name]
    if isinstance(t, TCon):
        return t.name
    if isinstance(t, TArrow):
        return f"({render_type(t.a, varnames)}->{render_type(t.b, varnames)})"
    if isinstance(t, TPair):
        return f"({render_type(t.a, varnames)}*{render_type(t.b, varnames)})"
    if isinstance(t, TList):
        return f"List({render_type(t.a, varnames)})"
    raise TypeError(f"unknown type node {t!r}")


def first_occurrence_order(t, order):
    if isinstance(t, TVar):
        if t.name not in order:
            order.append(t.name)
    elif isinstance(t, TArrow):
        first_occurrence_order(t.a, order)
        first_occurrence_order(t.b, order)
    elif isinstance(t, TPair):
        first_occurrence_order(t.a, order)
        first_occurrence_order(t.b, order)
    elif isinstance(t, TList):
        first_occurrence_order(t.a, order)


def render_scheme(quant, t):
    order = []
    first_occurrence_order(t, order)
    varnames = {name: f"t{i}" for i, name in enumerate(order)}
    body = render_type(t, varnames)
    if quant:
        # S06: forall list in first-occurrence order (the same `order`
        # used to assign t0/t1/t2.., not the quant list's own order).
        quant_set = {v.name for v in quant}
        quant_names = [varnames[name] for name in order if name in quant_set]
        # S06 clarification: if generalization-eligible but zero free
        # type variables remain, print the bare type (nothing to quantify).
        if quant_names:
            return "forall " + " ".join(quant_names) + " . " + body
    return body


def canonical_serialization(results):
    lines = ["TYPECHAIN9-CERT-V1"]
    for name, quant, t, generalized in results:
        lines.append(f"{name}={render_scheme(quant if generalized else [], t)}")
    return "\n".join(lines)


def certificate_hash(results):
    ser = canonical_serialization(results)
    return hashlib.sha256(ser.encode()).hexdigest()[:16]


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "program.ty"
    text = open(path).read()
    bindings = parse_program(text)
    results = infer_program(bindings)
    for name, quant, t, generalized in results:
        print(f"{name}: {render_scheme(quant if generalized else [], t)}  "
              f"(generalized={generalized})")
    print()
    ser = canonical_serialization(results)
    print(ser)
    print()
    print("hash16:", certificate_hash(results))
