from pylogic.fol import Predicate, Substitution, Term, TermType


def test_predicate():
    x = Term("x", TermType.VARIABLE)
    c = Term("John", TermType.CONSTANT)
    p = Predicate("Admires", (x, c))
    assert p.__repr__() == (
        "Admires(Term(x, type=TermType.VARIABLE), "
        "Term(John, type=TermType.CONSTANT))"
    )
    p = Predicate("King", (x,))
    assert (~p).__repr__() == "¬King(Term(x, type=TermType.VARIABLE))"
    cp = Term("John", TermType.CONSTANT)
    assert c == cp
    p1 = Predicate("Admires", (x, c))
    p2 = Predicate("Admires", (Term("x", TermType.VARIABLE), cp))
    assert p1 == p2


def test_substitution():
    x = Term("x", TermType.VARIABLE)
    term = Term("Diego", TermType.CONSTANT)
    p = Predicate("King", (x,))
    sub = Substitution({x: term})

    result = sub.substitute(p)
    expected = Predicate("King", (term,))
    print(result)
    print(expected)
    assert result == expected
