from pylogic.propositional import (
    CnfParser,
    PropLogicKB,
    Variable,
    pl_resolution,
    to_cnf,
    CnfClause,
)

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
    kb = PropLogicKB()
    assert len(kb.clauses) == 0

    kb.add(CnfClause({p, q, a}))
    assert kb.clauses == {CnfClause({p, q, a})}
    kb.add([CnfClause({p, q}), CnfClause({r})])
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
    kb = PropLogicKB(clauses)
    assert pl_resolution(kb, Variable("P12", False))
