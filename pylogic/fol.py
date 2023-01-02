from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple

from pylogic.common_defs import Operator


class TermType(Enum):
    CONSTANT = 0
    VARIABLE = 1


class Term:
    def __init__(self, identifier: str, type: TermType) -> None:
        self._identifier = identifier
        self._type = type

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def type(self) -> TermType:
        return self._type

    def __repr__(self) -> str:
        return f"{self.identifier}"


class Sentence(ABC):
    OP = Operator.NONE

    @property
    def lhs(self):
        return self._c1

    @property
    def rhs(self):
        return self._c2

    # def __or__(self, other) -> "Clause":
    #     return OrClause(self, other)

    # def __and__(self, other) -> "Clause":
    #     return AndClause(self, other)

    # def __gt__(self, other) -> "Clause":
    #     return CondClause(self, other)

    def __repr__(self) -> str:
        return f"({self.lhs.__repr__()}) {self.OP.value} ({self.rhs.__repr__()})"

    @abstractmethod
    def __invert__(self) -> "Sentence":
        pass

    def __eq__(self, other):
        if self.OP != other.OP:
            return False

        if type(self) == Predicate:
            return self == other
        return self.lhs == other.lhs and self.rhs == other.rhs


class Predicate(Sentence):
    def __init__(
        self,
        identifier,
        args: Tuple[Term],
        is_negated: bool = False,
    ):
        self._identifier = identifier
        self._args = args
        self._is_negated = is_negated

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def is_negated(self) -> bool:
        return self._is_negated

    def __repr__(self) -> str:
        arg_string = ", ".join(map(str, self._args))
        neg = "¬" if self.is_negated else ""
        return f"{neg}{self.identifier}({arg_string})"

    def __invert__(self) -> "Predicate":
        return Predicate(self.identifier, self._args, not self.is_negated)


class OrSentence(Sentence):
    OP = Operator.OR

    def __init__(self, s1: Sentence, s2: Sentence):
        self._s1 = s1
        self._s2 = s2

    # def __invert__(self) -> Sentence:
    #     return ~self._s2 & ~self._s1
