from pylogic.propositional import PropLogicKB, Variable, to_cnf, CnfClause

p = Variable("P", True)
q = Variable("Q", True)
r = Variable("R", True)
a = Variable("A", True)
b = Variable("B", True)
c = Variable("C", True)


def test_to_cnf():
    assert to_cnf((a & b & c & p) | q) == (a | q) & (b | q) & (c | q) & (p | q)
    assert to_cnf(~((~p > ~q) & ~r)) == (~p | r) & (q | r)


def test_cnf_class():
    p = Variable("P", True)
    q = Variable("Q", True)
    r = Variable("R", True)
    a = Variable("A", True)
    c1 = CnfClause([p, q, a])
    c2 = CnfClause([r, ~q])
    assert q in c1
    assert c1.resolve(c2, q) == CnfClause([p, r, a])


def test_pl_kb():
    kb = PropLogicKB()
    assert len(kb.clauses) == 0

    kb.add(CnfClause([p, q, a]))
    assert kb.clauses == {CnfClause([p, q, a])}
    kb.add([CnfClause([p, q]), CnfClause([r])])
    assert kb.clauses == {[CnfClause([p, q, a]), CnfClause([p, q]), CnfClause([r])]}