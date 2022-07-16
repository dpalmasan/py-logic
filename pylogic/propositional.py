from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, Set
from functools import singledispatchmethod


class Operator(Enum):
    AND = "^"
    OR = "v"
    COND = "->"
    BICOND = "<->"
    VARIABLE = "VAR"
    NONE = "NONE"


class NonCnfClauseException(Exception):
    pass


class UselessCnfClauseException(Exception):
    pass


class CnfResolveError(Exception):
    pass


class Clause(ABC):
    OP = Operator.NONE

    @property
    def lhs(self):
        return self._c1

    @property
    def rhs(self):
        return self._c2

    def __or__(self, other) -> "Clause":
        return OrClause(self, other)

    def __and__(self, other) -> "Clause":
        return AndClause(self, other)

    def __gt__(self, other) -> "Clause":
        return CondClause(self, other)

    def __rshift__(self, other) -> "Clause":
        return BicondClause(self, other)

    def __repr__(self) -> str:
        return f"{self.lhs.__repr__()} {self.OP.value} {self.rhs.__repr__()}"

    @abstractmethod
    def __invert__(self) -> "Clause":
        pass

    def __eq__(self, other):
        if self.OP != other.OP:
            return False

        if type(self) == Variable:
            return self == other
        return self.lhs == other.lhs and self.rhs == other.rhs


class Variable(Clause):
    OP = Operator.VARIABLE

    def __init__(self, identifier: str, truthyness: bool):
        self._identifier = identifier
        self._truthyness = truthyness

    @property
    def lhs(self):
        return self

    @property
    def rhs(self):
        return self

    @property
    def identifier(self):
        return self._identifier

    @property
    def truthyness(self) -> bool:
        return self._truthyness

    def __repr__(self) -> str:
        return "{}{}".format("" if (self._truthyness) else "¬", self._identifier)

    def __invert__(self) -> "Clause":
        return Variable(self._identifier, not self._truthyness)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Variable):
            return False
        return (
            self.identifier == other.identifier and self.truthyness == other.truthyness
        )

    def __hash__(self) -> int:
        return hash(self.__str__())


class OrClause(Clause):
    OP = Operator.OR

    def __init__(self, c1: Clause, c2: Clause):
        self._c1 = c1
        self._c2 = c2

    def __invert__(self) -> "Clause":
        return ~self._c1 & ~self._c2


class AndClause(Clause):
    OP = Operator.AND

    def __init__(self, c1: Clause, c2: Clause):
        self._c1 = c1
        self._c2 = c2

    def __invert__(self) -> "Clause":
        return ~self._c1 | ~self._c2


class CondClause(Clause):
    OP = Operator.COND

    def __init__(self, c1: Clause, c2: Clause):
        self._c1 = c1
        self._c2 = c2

    def __invert__(self) -> "Clause":
        return self._c1 & ~self._c2


class BicondClause(Clause):
    OP = Operator.BICOND

    def __init__(self, c1: Clause, c2: Clause):
        self._c1 = c1
        self._c2 = c2

    def __invert__(self) -> "Clause":
        return (self._c1 & ~self._c2) | (self._c2 & ~self._c1)


def is_simple_clause(phi: Clause) -> bool:
    return type(phi.lhs) == Variable and type(phi.rhs) == Variable


def to_cnf(phi: Clause) -> Clause:
    if phi.OP == Operator.AND:
        p = to_cnf(phi.lhs)
        q = to_cnf(phi.rhs)
        return p & q

    if phi.OP == Operator.OR:
        p = to_cnf(phi.lhs)
        q = to_cnf(phi.rhs)
        is_p_variable = type(p) == Variable
        is_q_variable = type(q) == Variable
        if not is_p_variable and not is_q_variable:
            if p.OP == Operator.OR and q.OP == Operator.OR:
                return to_cnf(p.lhs | p.rhs) | to_cnf(q.lhs | q.rhs)

            if p.OP == Operator.OR:
                return to_cnf(p.lhs | p.rhs | q.lhs) & to_cnf(p.lhs | p.rhs | q.rhs)

            if q.OP == Operator.OR:
                return to_cnf(p.lhs | q.lhs | q.rhs) & to_cnf(p.rhs | q.lhs | q.rhs)

            return (
                to_cnf(p.lhs | q.lhs)
                & to_cnf(p.lhs | q.rhs)
                & to_cnf(p.rhs | q.lhs)
                & to_cnf(p.rhs | q.rhs)
            )

        if is_p_variable and not is_q_variable:
            if q.OP == Operator.AND:
                return to_cnf(p.lhs | q.lhs) & to_cnf(p.rhs | q.lhs)
            return p.lhs | to_cnf(q.lhs | q.rhs)

        if not is_p_variable and is_q_variable:
            if p.OP == Operator.AND:
                return to_cnf(p.lhs | q.lhs) & to_cnf(p.rhs | q.lhs)
            return to_cnf(p.lhs | p.rhs) | q.lhs

        return p | q

    if phi.OP == Operator.COND:
        return to_cnf(~phi.lhs | phi.rhs)

    if phi.OP == Operator.BICOND:
        return to_cnf((phi.lhs & phi.rhs) | (~phi.lhs & ~phi.rhs))

    return phi


class CnfClause:
    def __init__(self, variables: Set[Variable]):
        self._literals = variables
        for variable in variables:
            if variable in self._literals and ~variable in self._literals:
                raise UselessCnfClauseException("This clause is always true!")

    def resolve(self, other: "CnfClause", literal: Variable) -> Optional["CnfClause"]:
        c1 = CnfClause(self._literals)
        c2 = CnfClause(other._literals)
        if literal not in c1 and ~literal not in c1:
            raise CnfResolveError(f"Literal {literal} not found in clause {self}")

        if literal not in c2 and ~literal not in c2:
            raise CnfResolveError(f"Literal {literal} not found in clause {other}")

        c1p = c1 if literal in self else c2
        c2p = c1 if ~literal in self else c2

        c1p._literals.remove(literal)
        c2p._literals.remove(~literal)  # type: ignore
        return CnfClause(c1p._literals | c2p._literals)

    def __contains__(self, key: Clause) -> bool:
        return key in self._literals

    def __repr__(self) -> str:
        return "({})".format(" v ".join(map(str, self._literals)))

    def __eq__(self, other) -> bool:
        return self._literals == other._literals

    def __ne__(self, other) -> bool:
        return self._literals != other._literals

    def __hash__(self) -> int:
        return hash(self.__repr__())


class PropLogicKB:
    def __init__(self, clauses: Optional[Set[CnfClause]] = None):
        self._clauses = clauses if clauses else set()

    @property
    def clauses(self) -> Set[CnfClause]:
        return self._clauses

    @singledispatchmethod
    def add(self, arg) -> None:
        raise NotImplementedError(f"Cannot add objects of type {type(arg)}")

    @add.register
    def _(self, clause: CnfClause) -> None:
        self._clauses.add(clause)

    @add.register
    def _(self, clauses: list) -> None:
        for clause in clauses:
            if type(clause) != CnfClause:
                raise TypeError("clauses must be a list of CnfClause")
            self.add(clause)
