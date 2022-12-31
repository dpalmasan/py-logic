from functools import reduce
from itertools import product
from typing import List
from pylogic.propositional import (
    BadHornClause,
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
    assert str(to_cnf((a | b) >> (c & d))) == str(
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
    cnf = to_cnf(B11 >> (P12 | P21))
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
    cnf = to_cnf((B11 >> (P12 | P21)) & ~B11)
    parser = CnfParser()
    clauses = parser.parse(cnf)
    kb = ResolutionKB(clauses)
    assert kb.query(Variable("P12", False))


def test_previous_bug_1():
    parser = CnfParser()
    result = to_cnf(
        Variable("B21", True) >> (Variable("P22", True) | Variable("P31", True))
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
        Variable("B13", True)
        >> (Variable("P12", True) | Variable("P03", True) | Variable("P32", True))
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
    cnf = to_cnf((B11 >> (P12 | P21)) & ~B11)
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
    clause = ((b11 >> p12 | p21) & ~b11) & ~p12
    assert dpll_satisfiable(clause) is True

    assert dpll_satisfiable(b11 & ~b11) is False


def test_dpll_kb():
    # Example from AIMA
    B11 = Variable("B11", True)
    P12 = Variable("P12", True)
    P21 = Variable("P21", True)
    kb = DpllKB([(B11 >> (P12 | P21)), ~B11])
    assert kb.query(Variable("P12", False))


def test_debug_dpll():
    kb = DpllKB()
    kb.add(
        Variable("B13", True)
        >> (Variable("P12", True) | Variable("P03", True) | Variable("P32", True))
    )

    kb.add(Variable("P12", True) & Variable("P03", True) & Variable("B13", True))
    alpha = ~Variable("P32", True)
    assert kb.query(alpha) is False


def test_wumpus_examples():
    """
    This is to prove that there is an assignment in which

    For b11 <-> (p21 v p12) & ¬b11 to be True we need
    b11 = False
    p21 = False
    p12 = False

    For b21 & b21 <-> (p11 v p31 v p22) & ¬p11 & ¬p31 & ¬p11 to be True

    p11 = False
    b21 = True
    p31 = False

    The only way for p31 being True is that p22 is False
    """
    grid = [1, 2, 3, 4]
    r1 = reduce(
        lambda x, y: x & y,
        [Variable(f"W{x}{y}", False) for x, y in product(grid, grid)],
    )
    b21 = Variable("B21", False)
    pits1 = Variable("P11", False) | Variable("P31", False) | Variable("P22", False)
    pits2 = Variable("P21", False) | Variable("P12", False)
    p11 = Variable("P11", False)
    w11 = Variable("W11", False)
    b11 = Variable("B11", False)
    r2 = b21 >> pits1
    r3 = b11 >> pits2
    p31 = Variable("P31", False)
    w31 = Variable("W31", False)
    sentence = r1 & r2 & r3 & b21 & ~b11 & ~p11 & ~w11
    kb = ResolutionKB()
    kb.add(sentence)
    assert kb.query(~p31 & ~w31) is False

    kb = DpllKB()
    kb.add(sentence)
    assert kb.query(~p31 & ~w31) is False


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


def test_debug_case_2():
    """
    ¬P13 ^ ¬W13
    S02,
    ¬W02
    ¬W03
    ¬S03
    S02 <-> W12 v W01 v W03
    S03 <-> W13 v W02
    S01 <-> W11 v W00 v W02
    S12 <-> W02 v W22 v W11 v W13
    S13 <-> W03 v W23 v W12

    ¬B02
    ¬B03
    ¬P03
    ¬P02
    B02 <-> P12 v P01 v P03
    B03 <-> P13 v P02
    B01 <-> P11 v P00 v P02
    B12 <-> P02 v P22 v P11 v P13
    B13 <-> P03 v P23 v P12


    """
    b01 = Variable("B01", False)
    b02 = Variable("B02", False)
    b03 = Variable("B03", False)
    b12 = Variable("B12", False)
    b13 = Variable("B12", False)
    p12 = Variable("P12", False)
    p00 = Variable("P00", False)
    p01 = Variable("P01", False)
    p03 = Variable("P03", False)
    p13 = Variable("P13", False)
    p11 = Variable("P11", False)
    p22 = Variable("P22", False)
    p02 = Variable("P02", False)
    p23 = Variable("P23", False)

    rw1 = _one_wumpus_rule()
    rw2 = _at_most_one_wumpus()

    # S02 <-> W12 v W01 v W03
    # B02 <-> P12 v P01 v P03, S03 <-> W13 v W02,
    # B13 <-> P03 v P23 v P12, S13 <-> W03 v W23 v W12]
    r1 = b02 >> p12 | p01 | p03
    # B03 <-> P13 v P02
    r2 = b03 >> p13 | p02

    # B01 <-> P11 v P00 v P02
    r3 = b01 >> p11 | p00 | p02

    # B12 <-> P02 v P22 v P11
    r4 = b12 >> p02 | p22 | p11 | p13
    # B13 <-> P03 v P23 v P12
    r5 = b13 >> p03 | p23 | p12

    # Breeze rules
    s1 = ~b02 & ~b03 & ~p02 & ~p03 & r1 & r2 & r3 & r4 & r5

    kb = ResolutionKB()
    kb.add(s1)

    w02 = Variable("W02", False)
    w03 = Variable("W03", False)
    s03 = Variable("S03", False)
    s02 = Variable("S02", False)

    # Add stench and wumpus knowledge
    kb.add(s02 & ~s03 & ~w02 & ~w03)

    s01 = Variable("S01", False)
    s12 = Variable("S12", False)
    s13 = Variable("S12", False)
    w12 = Variable("W12", False)
    w00 = Variable("W00", False)
    w01 = Variable("W01", False)
    w13 = Variable("W13", False)
    w11 = Variable("W11", False)
    w22 = Variable("W22", False)
    w23 = Variable("W23", False)

    r1 = s02 >> w12 | w01 | w03
    r2 = s03 >> w13 | w02
    r3 = s01 >> w11 | w00 | w02
    r4 = s12 >> w02 | w22 | w11 | w13
    r5 = s13 >> w03 | w23 | w12
    # ¬W03, ¬P03, ¬S03, ¬B03, S02, ¬B02
    # Stench rules
    kb.add(r1)
    kb.add(r2)
    kb.add(r3)
    kb.add(r4)
    kb.add(r5)

    kb.add(rw1)
    kb.add(rw2)

    assert kb.query(~p13) is True


def test_horn_clause():
    a1 = Variable("a1", is_negated=True)
    a2 = Variable("a2", is_negated=True)
    a3 = Variable("a3", is_negated=True)
    b = Variable("b", is_negated=False)

    with pytest.raises(BadHornClause):
        HornClause([a1, a2, ~a3], b)

    hc = HornClause([a3, a1, a2], b)
    assert repr(hc) == "a1 ^ a2 ^ a3 => b"
    assert hc == HornClause([a1, a2, a3], b)
