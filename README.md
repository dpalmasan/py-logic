# Pylogic: A logic programming library for python

<p align="center">
<a href="https://github.com/dpalmasan/py-logic/actions"><img alt="Actions Status" src="https://github.com/dpalmasan/py-logic/workflows/build/badge.svg"></a>
<a href="https://codecov.io/gh/dpalmasan/py-logic" > <img src="https://codecov.io/gh/dpalmasan/py-logic/branch/main/graph/badge.svg?token=1ROCTA6VNM"/></a>
<a href="https://github.com/dpalmasan/py-logic/blob/master/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/dpalmasan/py-logic"></a>
<a href="https://www.contributor-covenant.org/" > <img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg"/></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

## Overview

`Pylogic` is a library to integrate logic programming to your python programs. Currently it supports propositional logic, and a subset of first order logic (Horn Clauses). The API is supposed to be expressive as `python` is as a language.

## Install

```
pip install python-logic
```

### Examples

```python
a = Literal("P", True)
b = Literal("Q", True)

print(a | b)
print(~a | b)
print(~(a | b ))
```

Output:

```
P v Q
¬P v Q
¬P ^ ¬Q
```

#### Making inferences using the resolution rule (Propositional Logic)

Suppose we have the following knowledge base (KB):

$$(B_{11} \Leftrightarrow (P_{12} \vee P_{21})) \wedge \neg B_{11}$$

And we want to prove $\alpha = \neg P_{12}$.

We could use several algorithms, based on desired KB type as shown in the code below.

```python
from pylogic.propositional import (
    BicondClause,
    DpllKB,
    ResolutionKB,
    Variable,
)

B11 = Variable("B11", True)
P12 = Variable("P12", True)
P21 = Variable("P21", True)
clauses = BicondClause(B11, (P12 | P21)) & ~B11
kb = ResolutionKB(clauses)
alpha = Variable("P12", False)
print(f"Ask entailment of {alpha} using resolution:", kb.query(alpha))
kb = DpllKB(clauses)
print(f"Ask entailment of {alpha} using DPLL algorithm:", kb.query(alpha))

kb = ResolutionKB(clauses)
alpha = B11 & ~B11
print(f"Ask entailment of {alpha} using resolution:", kb.query(alpha))
kb = DpllKB(clauses)
print(f"Ask entailment of {alpha} using DPLL algorithm:", kb.query(alpha))
```

Output:

```
Ask entailment of P12 using resolution: True
Ask entailment of P12 using DPLL algorithm: True
Ask entailment of ¬B11 ^ B11 using resolution: False
Ask entailment of ¬B11 ^ B11 using DPLL algorithm: False
```

#### Using First Order Logic (Forward and Backward chaining)

Examples are located under `/examples` folder. Lets go with the example in the AIMA (Artificial Intelligence a Modern Approach) example, we have the following predicates:

1. It is a crime for an american to sell weapons to hostile nations


```math
\begin{array} {   rr} \quad American(x) \land Weapon(y) \land \\ Sells(x, y, z) \land Hostile(z) \Rightarrow Criminal(x) \end{array}

$$ $$
```

2. Nono has some missiles:

$$Owns(Nono, M1)$$

$$Missile(M1)$$

3. All missiles were sold to it by Colonel West

$$Missile(x) \land Owns(Nono, x) \Rightarrow Sells(West, x, Nono)$$

4. Missiles are weapons

$$Missile(x) \Rightarrow Weapon(x)$$

5. An enemy of America counts as Hostile:

$$Enemy(x, America) \Rightarrow Hostile(x)$$

6. West who is american

$$American(West)$$

7. The country of Nono an enemy of America

$$Enemy(Nono, America)$$

8. Prove west is a Criminal

$$Criminal(West)$$

Let us use forward chaining, the code would look as follows:

```python
from pylogic.fol import (
    HornClauseFOL,
    Predicate,
    Term,
    TermType,
    fol_bc_ask,
    Substitution,
    fol_fc_ask,
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

print("Forward Chaining:")

sub = fol_fc_ask(kb, Predicate("Criminal", [west]))
for k, v in sub.substitution_values.items():
    print(k, v)

print("Backward Chaining:")
answers = fol_bc_ask(kb, [goal], Substitution({}))
for answer in answers:
    for k, v in answer.substitution_values.items():
        print(k, v)
```

Output (Notice that variables will be standardized, to avoid unification issues)

```
American(x) ^ Hostile(z) ^ Sells(x, y, z) ^ Weapon(y) => Criminal(x)
Owns(Nono, M1)
Missile(M1)
Missile(x) ^ Owns(Nono, x) => Sells(West, x, Nono)
Missile(x) => Weapon(x)
Enemy(x, America) => Hostile(x)
American(West)
Enemy(Nono, America)
Forward Chaining:
x0 West
z1 Nono
y2 M1
Backward Chaining:
x4 M1
y2 M1
x3 y2
z1 Nono
x5 z1
x0 West
```

Let's take a more challenging problem, the coloreable map:

```math
\begin{array} {   rr} \quad Diff(wa, nt) \land Diff(wa, sa) \land \\ Diff(nt, q) \land Diff(nt, sa) \land \\ Diff(q, nsw) \land Diff(q, sa) \land \\ Diff(nsw, v) \land Diff(nsw, a) \land \\ Diff(v, sa) \Rightarrow Coloreable() \\ Diff(Red, Blue) \quad Diff(Red, Green) \\ Diff(Blue, Red) \quad Diff(Blue, Green) \\ Diff(Green, Red) \quad Diff(Green, Blue) \end{array}
```

Currently, forward chaining will get stuck due to being a hard-matching problem, and that the current FC implementation is naive:

```python
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
```

Output (All possible variable assignments):

```
v5 Blue
nsw4 Green
q3 Blue
sa2 Red
wa0 Blue
nt1 Green
=======
v5 Blue
nsw4 Red
q3 Blue
sa2 Green
wa0 Blue
nt1 Red
=======
v5 Green
nsw4 Blue
q3 Green
sa2 Red
wa0 Green
nt1 Blue
=======
v5 Green
nsw4 Red
q3 Green
sa2 Blue
wa0 Green
nt1 Red
=======
v5 Red
nsw4 Green
q3 Red
sa2 Blue
wa0 Red
nt1 Green
=======
v5 Red
nsw4 Blue
q3 Red
sa2 Green
wa0 Red
nt1 Blue
=======
```


## Goals

This library could be used to create logic agents, or even inference engines to be easily integrated with `python`. There is multiple work to be done, but a current goal is to be able to apply an intersection between `Machine Learning` and `Logic Programming` that is built solely on python, and with the flexibility of using different algorithms depending the context.

## Code of Conduct

Everyone participating in the _Pylogic_ project, and in particular in the issue tracker,
pull requests, and social media activity, is expected to treat other people with respect
and more generally to follow the guidelines articulated in the
[Covenant Code of Conduct](code_of_conduct.md).
