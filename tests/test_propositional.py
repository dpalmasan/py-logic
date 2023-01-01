from functools import reduce
from typing import List
from pylogic.propositional import (
    BadHornClause,
    BicondClause,
    Clause,
    CnfParser,
    DpllKB,
    HornClause,
    ResolutionKB,
    Variable,
    dpll_satisfiable,
    find_clause_symbols,
    find_pure_symbol,
    find_unit_clause,
    pl_fc_entails,
    to_cnf,
    CnfClause,
)
import pytest

p = Variable("P", True)
q = Variable("Q", True)
r = Variable("R", True)
a = Variable("A", True)
b = Variable("B", True)
c = Variable("C", True)
d = Variable("D", True)


def test_to_cnf():
    assert to_cnf((a & b & c & p) | q) == (a | q) & (b | q) & (c | q) & (p | q)
    assert to_cnf(~((~p > ~q) & ~r)) == (~p | r) & (q | r)
    assert to_cnf((a | b) | (~a & ~b & c & p)) == (a | b | ~a) & (a | b | ~b) & (
        a | b | c
    ) & (a | b | p)
    assert to_cnf((a & b & c & p) | q) == (a | q) & (b | q) & (c | q) & (p | q)
    assert to_cnf((a | b | c | p) & q) == (a | b | c | p) & q
    assert str(to_cnf(BicondClause(a | b, c & d))) == str(
        (a | b | ~a)
        & (a | b | ~b)
        & (a | b | ~c | ~d)
        & (c | ~a)
        & (c | ~b)
        & (d | ~a)
        & (d | ~b)
        & (c | ~c | ~d)
        & (d | ~c | ~d)
    )


def test_cnf_class():
    p = Variable("P", True)
    q = Variable("Q", True)
    r = Variable("R", True)
    a = Variable("A", True)
    c1 = CnfClause({p, q, a})
    c2 = CnfClause({r, ~q})
    assert q in c1
    assert c1.resolve(c2, q) == CnfClause({p, r, a})

    # We don't desire to mutate any of the clauses
    assert q in c1 and ~q in c2


def test_pl_kb():
    kb = ResolutionKB()
    assert len(kb.clauses) == 0

    kb.add(p | q | a)
    assert kb.clauses == {CnfClause({p, q, a})}
    kb.add([p | q, r])
    assert kb.clauses == {CnfClause({p, q, a}), CnfClause({p, q}), CnfClause({r})}


def test_cnf_parser():
    B11 = Variable("B11", True)
    P12 = Variable("P12", True)
    P21 = Variable("P21", True)

    # Example from AIMA book
    cnf = to_cnf(BicondClause(B11, (P12 | P21)))
    parser = CnfParser()
    assert (
        len(
            parser.parse(cnf).intersection(
                {
                    CnfClause({B11, ~P21}),
                    CnfClause({B11, ~P12}),
                    CnfClause({P21, ~B11, P12}),
                }
            )
        )
        == 3
    )

    # Extra checking to confirm hashing works well
    assert parser.parse(cnf).issubset(
        {
            CnfClause({B11, ~P21}),
            CnfClause({B11, ~P12}),
            CnfClause({P21, ~B11, P12}),
        }
    )


def test_pl_resolution():
    # Example from AIMA
    B11 = Variable("B11", True)
    P12 = Variable("P12", True)
    P21 = Variable("P21", True)
    cnf = to_cnf(BicondClause(B11, (P12 | P21)) & ~B11)
    parser = CnfParser()
    clauses = parser.parse(cnf)
    kb = ResolutionKB(clauses)
    assert kb.query(Variable("P12", False))


def test_previous_bug_1():
    parser = CnfParser()
    result = to_cnf(
        BicondClause(
            Variable("B21", True), (Variable("P22", True) | Variable("P31", True))
        )
    )
    r4 = parser.parse(result)

    result = to_cnf(~Variable("B11", True))
    r2 = parser.parse(result)

    alpha = ~Variable("P12", True)

    kb = ResolutionKB()
    kb.add(list(r4))
    kb.add(list(r2))
    assert kb.query(alpha) is False


def test_debug():
    parser = CnfParser()
    result = to_cnf(
        BicondClause(
            Variable("B13", True),
            (Variable("P12", True) | Variable("P03", True) | Variable("P32", True)),
        )
    )
    r4 = parser.parse(result)

    result = to_cnf(
        Variable("P12", True) & Variable("P03", True) & Variable("B13", True)
    )
    r2 = parser.parse(result)

    alpha = ~Variable("P32", True)

    kb = ResolutionKB()
    kb.add(list(r4))
    kb.add(list(r2))
    assert kb.query(alpha) is False


def test_find_clause_symbols():
    B11 = Variable("B11", True)
    P12 = Variable("P12", True)
    P21 = Variable("P21", True)
    cnf = to_cnf(BicondClause(B11, (P12 | P21)) & ~B11)
    parser = CnfParser()
    clauses = parser.parse(cnf)
    assert find_clause_symbols(clauses) == {"B11", "P12", "P21"}


def test_find_pure_symbol():
    clauses = {
        CnfClause(
            {
                Variable("A", True, True),
                Variable("B", False, True),
                Variable("C", False, False),
            }
        ),
        CnfClause({Variable("A", False, True), Variable("C", True, False)}),
        CnfClause({Variable("B", True, False)}),
    }
    symbols = find_clause_symbols(clauses)
    p, value = find_pure_symbol(symbols, clauses, {"A": False, "B": False, "C": True})
    assert (p, value) == (None, None)

    clauses = {
        CnfClause(
            {
                Variable("A", False, True),
                Variable("B", False, True),
                Variable("C", False, False),
            }
        ),
        CnfClause({Variable("A", False, True), Variable("C", True, False)}),
        CnfClause({Variable("B", True, False)}),
    }
    symbols = find_clause_symbols(clauses)
    p, value = find_pure_symbol(symbols, clauses, {"A": False, "B": False, "C": True})
    assert (p, value) == ("A", False)

    clauses = {
        CnfClause(
            {
                Variable("A", False, True),
                Variable("B", False, True),
                Variable("C", True, False),
            }
        ),
        CnfClause({Variable("A", True, True), Variable("C", True, False)}),
        CnfClause({Variable("B", True, False)}),
    }
    symbols = find_clause_symbols(clauses)
    p, value = find_pure_symbol(symbols, clauses, {"A": False, "B": False, "C": True})
    assert (p, value) == ("C", True)


def test_find_unit_clause():
    clauses = {
        CnfClause({Variable("B", True, True), Variable("C", True, False)}),
    }

    model = {"B": False}

    p, val = find_unit_clause(clauses, model, set())
    assert p is None and val is None


def test_dpll():
    b11 = Variable("b11", False, None)
    p12 = Variable("p12", False, None)
    p21 = Variable("p21", False, None)

    # Simple case
    assert dpll_satisfiable(b11) is True

    # More complex case
    clause = (BicondClause(b11, p12 | p21) & ~b11) & ~p12
    assert dpll_satisfiable(clause) is True

    assert dpll_satisfiable(b11 & ~b11) is False


def test_dpll_kb():
    # Example from AIMA
    B11 = Variable("B11", True)
    P12 = Variable("P12", True)
    P21 = Variable("P21", True)
    kb = DpllKB([BicondClause(B11, (P12 | P21)), ~B11])
    assert kb.query(Variable("P12", False))


def test_debug_dpll():
    kb = DpllKB()
    kb.add(
        BicondClause(
            Variable("B13", True),
            (Variable("P12", True) | Variable("P03", True) | Variable("P32", True)),
        )
    )

    kb.add(Variable("P12", True) & Variable("P03", True) & Variable("B13", True))
    alpha = ~Variable("P32", True)
    assert kb.query(alpha) is False


def _one_wumpus_rule() -> Clause:
    """There should exist one wumpus."""
    map_width = 3
    map_height = 3
    literals: List[Variable] = []
    for i in range(map_width):
        for j in range(map_height):
            literals.append(Variable(f"W{i}{j}", is_negated=False, truthyness=None))

    return reduce(lambda x, y: x | y, literals)  # type: ignore


def _at_most_one_wumpus() -> Clause:
    """There must be just one Wumpus."""
    map_width = 4
    map_height = 4
    clauses = []
    for j in range(map_height):
        for i in range(map_width):
            if i > 0:
                clauses.append(
                    Variable(f"W{i}{j}", is_negated=True, truthyness=None)
                    | Variable(f"W{i - 1}{j}", is_negated=True, truthyness=None)
                )
            if i < map_width - 1:
                clauses.append(
                    Variable(f"W{i}{j}", is_negated=True, truthyness=None)
                    | Variable(f"W{i + 1}{j}", is_negated=True, truthyness=None)
                )
            if j > 0:
                clauses.append(
                    Variable(f"W{i}{j}", is_negated=True, truthyness=None)
                    | Variable(f"W{i}{j - 1}", is_negated=True, truthyness=None)
                )

            if j < map_height - 1:
                if j > 0:
                    clauses.append(
                        Variable(f"W{i}{j}", is_negated=True, truthyness=None)
                        | Variable(f"W{i}{j + 1}", is_negated=True, truthyness=None)
                    )

    # type: ignore
    return reduce(lambda x, y: x & y, clauses)


def test_horn_clause():
    a1 = Variable("a1", is_negated=False)
    a2 = Variable("a2", is_negated=False)
    a3 = Variable("a3", is_negated=False)
    b = Variable("b", is_negated=False)

    with pytest.raises(BadHornClause):
        HornClause([a1, a2, ~a3], b)

    hc = HornClause([a3, a1, a2], b)
    assert repr(hc) == "a1 ^ a2 ^ a3 => b"
    assert hc == HornClause([a1, a2, a3], b)
    hc = HornClause([a1, a2, a3], ~b)
    assert hc.consequent is False
    hc = HornClause([a1, a2, a3], None)
    assert hc.consequent is False


def test_pl_fc_entails():
    A = Variable("A", is_negated=False, truthyness=True)
    B = Variable("B", is_negated=False, truthyness=True)
    L = Variable("L", is_negated=False)
    P = Variable("P", is_negated=False)
    M = Variable("M", is_negated=False)
    Q = Variable("Q", is_negated=False)
    kb = {
        HornClause([A]),
        HornClause([B]),
        HornClause([A, B], L),
        HornClause([A, P], L),
        HornClause([B, L], M),
        HornClause([L, M], P),
        HornClause([P], Q),
    }

    assert pl_fc_entails(kb, Q) is True
    X = Variable("X", is_negated=False)
    assert pl_fc_entails(kb, X) is False
