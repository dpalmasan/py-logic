from enum import Enum
from abc import ABC, abstractmethod
from typing import List

class Operator(Enum):
    AND = "^"
    OR = "v"
    COND = "->"
    BICOND = "<->"
    VARIABLE = "VAR"


class NonCnfClauseException(Exception):
    pass

class UselessCnfClauseException(Exception):
    pass

class Clause(ABC):
    OP = None
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
        if type(self.lhs) == Variable:
            return f"({self.lhs.__repr__()} {self.OP.value} {self.rhs.__repr__()})"

        return self.lhs.__repr__() + f"{self.OP.value}" + self.rhs.__repr__()
    
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

    def __eq__(self, other: "Variable") -> bool:
        return self.identifier == other.identifier and self.truthyness == other.truthyness

    def __hash__(self) -> str:
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


def to_cnf(phi: Clause) -> Clause:
    if type(phi) == Variable:
        return phi

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
            return (p.lhs | q.lhs) & (p.lhs | q.rhs) & (p.rhs | q.lhs) & (p.rhs | q.rhs)

        if is_p_variable and not is_q_variable:
            if q.OP == Operator.AND:
                return to_cnf(p.lhs | q.lhs) & to_cnf(p.lhs | q.rhs)
            return p.lhs | to_cnf(q.lhs | q.rhs)

        if not is_p_variable and is_q_variable:
            if p.OP == Operator.AND:
                return  to_cnf(p.lhs | q.lhs) & to_cnf(p.rhs | q.lhs)
            return to_cnf(p.lhs | p.rhs) | q.lhs
        return p | q

    if phi.OP == Operator.COND:
        return to_cnf(~phi.lhs | phi.rhs)

    if phi.OP == Operator.BICOND:
        return to_cnf((phi.lhs & p.rhs) | (~phi.lhs & ~phi.rhs))


class CnfClause:
    def __init__(self, variables: List[Variable]):
        self._literals = set(variables)
        for variable in variables:
            if variable in self._literals and ~variable in self._literals:
                raise UselessCnfClauseException("This clause is always true!")

