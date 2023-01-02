from pylogic.fol import Predicate, Term, TermType


def test_predicate():
    x = Term("x", TermType.VARIABLE)
    c = Term("John", TermType.CONSTANT)
    p = Predicate("Admires", (x, c))
    assert p.__repr__() == "Admires(x, John)"
    p = Predicate("King", (x,))
    assert (~p).__repr__() == "¬King(x)"
