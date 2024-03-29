from pylogic.fol import (
    HornClauseFOL,
    Predicate,
    Term,
    TermType,
    fol_bc_ask,
    Substitution,
)

wa = Term("wa", TermType.VARIABLE)
sa = Term("sa", TermType.VARIABLE)
nt = Term("nt", TermType.VARIABLE)
q = Term("q", TermType.VARIABLE)
nsw = Term("nsw", TermType.VARIABLE)
v = Term("v", TermType.VARIABLE)
t = Term("t", TermType.VARIABLE)

map = HornClauseFOL(
    [
        Predicate("Diff", [wa, nt]),
        Predicate("Diff", [wa, sa]),
        Predicate("Diff", [nt, q]),
        Predicate("Diff", [nt, sa]),
        Predicate("Diff", [q, nsw]),
        Predicate("Diff", [q, sa]),
        Predicate("Diff", [nsw, v]),
        Predicate("Diff", [nsw, sa]),
        Predicate("Diff", [v, sa]),
    ],
    Predicate("Colorable", []),
)

red = Term("Red", TermType.CONSTANT)
blue = Term("Blue", TermType.CONSTANT)
green = Term("Green", TermType.CONSTANT)

p1 = HornClauseFOL(
    [],
    Predicate("Diff", [red, blue]),
)
p2 = HornClauseFOL(
    [],
    Predicate("Diff", [red, green]),
)
p3 = HornClauseFOL(
    [],
    Predicate("Diff", [green, red]),
)
p4 = HornClauseFOL(
    [],
    Predicate("Diff", [green, blue]),
)
p5 = HornClauseFOL(
    [],
    Predicate("Diff", [blue, red]),
)
p6 = HornClauseFOL([], Predicate("Diff", [blue, green]))

kb = [map, p1, p2, p3, p4, p5, p6]

goal = Predicate("Colorable", [])
answers = fol_bc_ask(kb, [goal], Substitution({}))

for answer in answers:
    for k, v in answer.substitution_values.items():
        print(k, v)
    print("=" * 7)
