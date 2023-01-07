from pylogic.fol import (
    HornClauseFOL,
    Predicate,
    Term,
    TermType,
    fol_bc_ask,
    Substitution,
)


x = Term("x", TermType.VARIABLE)
y = Term("y", TermType.VARIABLE)
z = Term("z", TermType.VARIABLE)

nono = Term("Nono", TermType.CONSTANT)
west = Term("West", TermType.CONSTANT)
m1 = Term("M1", TermType.CONSTANT)
america = Term("America", TermType.CONSTANT)

p1 = Predicate("American", [x])
p2 = Predicate("Weapon", [y])
p3 = Predicate("Sells", [x, y, z])
p4 = Predicate("Hostile", [z])
p5 = Predicate("Criminal", [x])
p6 = Predicate("Owns", [nono, m1])
p7 = Predicate("Missile", [m1])
p8 = Predicate("Missile", [x])
p9 = Predicate("Owns", [nono, x])
p10 = Predicate("Sells", [west, x, nono])
p11 = Predicate("Weapon", [x])
p12 = Predicate("Enemy", [x, america])
p13 = Predicate("American", [west])
p14 = Predicate("Enemy", [nono, america])

hc1 = HornClauseFOL([p1, p2, p3, p4], p5)
hc2 = HornClauseFOL([], p6)
hc3 = HornClauseFOL([], p7)
hc4 = HornClauseFOL([p8, p9], p10)
hc5 = HornClauseFOL([p8], p11)
hc6 = HornClauseFOL([p12], Predicate("Hostile", [x]))
hc7 = HornClauseFOL([], p13)
hc8 = HornClauseFOL([], p14)

kb = [
    hc1,
    hc2,
    hc3,
    hc4,
    hc5,
    hc6,
    hc7,
    hc8,
]

goal = Predicate("Criminal", [west])
for rule in kb:
    print(rule)

answers = fol_bc_ask(kb, [goal], Substitution({}))
for answer in answers:
    for k, v in answer.substitution_values.items():
        print(k, v)
