# Pylogic: A logic programming library for python

<p align="center">
<a href="https://github.com/dpalmasan/py-logic/actions"><img alt="Actions Status" src="https://github.com/dpalmasan/py-logic/workflows/build/badge.svg"></a>
<a href="https://codecov.io/gh/dpalmasan/py-logic" > <img src="https://codecov.io/gh/dpalmasan/py-logic/branch/main/graph/badge.svg?token=1ROCTA6VNM"/></a>
<a href="https://github.com/dpalmasan/py-logic/blob/master/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/dpalmasan/py-logic"></a>
<a href="https://www.contributor-covenant.org/" > <img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg"/></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

## Overview

`Pylogic` is a library to integrate logic programming to your python programs. Currently it only supports propositonal logic, but First Order Logic (FOL) is planned as a project. Not all the algorithms are implemented, and the API is supposed to be expressive as `python` is as a language.

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

## Goals

This library could be used to create logic agents, or even inference engines to be easily integrated with `python`. There is multiple work to be done, but a current goal is to be able to apply an intersection between `Machine Learning` and `Logic Programming` that is built solely on python, and with the flexibility of using different algorithms depending the context.

## Code of Conduct

Everyone participating in the _Pylogic_ project, and in particular in the issue tracker,
pull requests, and social media activity, is expected to treat other people with respect
and more generally to follow the guidelines articulated in the
[Covenant Code of Conduct](code_of_conduct.md).
