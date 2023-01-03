from pylogic.fol import (
    HornClauseFOL,
    Predicate,
    Substitution,
    Term,
    TermType,
    standardize_variables,
    unify,
    unify_var,
)
import pytest


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
    assert result == expected

    y = Term("x", TermType.VARIABLE)
    a = Term("John", TermType.CONSTANT)
    assert y in sub
    assert a not in sub
    assert sub[x] == Term("Diego", TermType.CONSTANT)

    y = Term("y", TermType.VARIABLE)
    assert Term("y", TermType.VARIABLE) in sub.add_substitutions({y: a})
    assert sub.add_substitutions({y: a})[Term("y", TermType.VARIABLE)] == Term(
        "John", TermType.CONSTANT
    )


def test_horn_clause_fol():
    x = Term("x", TermType.VARIABLE)
    p1 = Predicate("King", (x,))
    p2 = Predicate("Greedy", (x,))
    b = Predicate("Evil", (x,))

    with pytest.raises(HornClauseFOL.BadHornClauseFOL):
        HornClauseFOL([p1, ~p2], b)

    hc = HornClauseFOL([p1, p2], b)
    assert repr(hc) == (
        "Greedy(Term(x, type=TermType.VARIABLE)) ^ "
        "King(Term(x, type=TermType.VARIABLE)) => "
        "Evil(Term(x, type=TermType.VARIABLE))"
    )
    assert hc == HornClauseFOL([p2, p1], b)
    hc = HornClauseFOL([p1, p2], ~b)
    assert hc.consequent is False
    assert hc == HornClauseFOL([p1, b, p2], None)


def test_unify_var():
    x = Term("x", TermType.VARIABLE)
    y = Term("y", TermType.VARIABLE)
    s = Substitution({})
    expected = Substitution(
        {Term("x", TermType.VARIABLE): Term("y", TermType.VARIABLE)}
    )
    result = unify_var(x, y, s)
    assert expected == result


def test_unify():
    x = Term("x", TermType.VARIABLE)
    y = Term("x", TermType.VARIABLE)
    a = Term("A", TermType.CONSTANT)
    s1 = Substitution({Term("z", TermType.VARIABLE): Term("A", TermType.CONSTANT)})
    s2 = Substitution({Term("z", TermType.VARIABLE): a})
    assert unify(x, y, s1) == s2
    assert unify(x, y, None) is None
    assert unify(x, a, Substitution({})) == Substitution({x: a})
    assert unify(a, y, Substitution({})) == Substitution({y: a})
    assert unify(x, [a], Substitution({})) is None

    x = Term("x", TermType.VARIABLE)
    y = Term("y", TermType.VARIABLE)
    z = Term("z", TermType.VARIABLE)
    a = Term("A", TermType.CONSTANT)
    b = Term("B", TermType.CONSTANT)

    expected = Substitution(
        {
            x: a,
            y: b,
            z: a,
        }
    )
    result = unify([x, b, z], [a, y, x], Substitution({}))
    assert expected == result


def test_standardize_variables():
    x = Term("x", TermType.VARIABLE)
    y = Term("x", TermType.VARIABLE)
    a = Term("A", TermType.CONSTANT)
    z = Term("x", TermType.VARIABLE)
    p1 = Predicate("King", [x])
    p2 = Predicate("TalksTo", [x, y, a])
    p3 = Predicate("Good", [z])
    hc = standardize_variables(HornClauseFOL([p1, p2], p3))
    assert hc == HornClauseFOL(
        [
            Predicate("King", [Term("x", TermType.VARIABLE)]),
            Predicate(
                "TalksTo",
                [Term("x0", TermType.VARIABLE), Term("x1", TermType.VARIABLE), a],
            ),
        ],
        Predicate("Good", [Term("x", TermType.VARIABLE)]),
    )
