from enum import Enum
from abc import ABC, abstractmethod

class Operator(Enum):
    AND = "^"
    OR = "v"
    COND = "->"
    BICOND = "<->"
    NONE = None

class BinClause(ABC):
    OP = Operator.NONE
    
    def __or__(self, other) -> "BinClause":
        return OrClause(self, other)

    def __and__(self, other) -> "BinClause":
        return AndClause(self, other)

    def __gt__(self, other) -> "BinClause":
        return CondClause(self, other)

    def __rshift__(self, other) -> "BinClause":
        return BicondClause(self, other)

    def __repr__(self) -> str:
        return f"({self._c1.__repr__()} {self.OP.value} {self._c2.__repr__()})"
    
    @abstractmethod
    def __invert__(self) -> "BinClause":
        pass


class Literal(BinClause):
    def __init__(self, identifier: str, truthyness: bool):
        self._identifier = identifier
        self._truthyness = truthyness

    @property
    def identifier(self):
        return self._identifier

    @property
    def truthyness(self) -> bool:
        return self._truthyness


    def __repr__(self) -> str:
        return "{}{}".format("" if (self._truthyness) else "¬", self._identifier)

    def __invert__(self) -> "BinClause":
        return Literal(self._identifier, not self._truthyness)


class OrClause(BinClause):
    OP = Operator.OR
    def __init__(self, c1: BinClause, c2: BinClause):
        self._c1 = c1
        self._c2 = c2

    def __invert__(self) -> "BinClause":
        return ~self._c1 & ~self._c2


class AndClause(BinClause):
    OP = Operator.AND
    def __init__(self, c1: BinClause, c2: BinClause):
        self._c1 = c1
        self._c2 = c2

    def __invert__(self) -> "BinClause":
        return ~self._c1 | ~self._c2


class CondClause(BinClause):
    OP = Operator.COND
    def __init__(self, c1: BinClause, c2: BinClause):
        self._c1 = c1
        self._c2 = c2

    def __invert__(self) -> "BinClause":
        return self._c1 & ~self._c2


class BicondClause(BinClause):
    OP = Operator.BICOND
    def __init__(self, c1: BinClause, c2: BinClause):
        self._c1 = c1
        self._c2 = c2

    def __invert__(self) -> "BinClause":
        return (self._c1 & ~self._c2) | (self._c2 & ~self._c1)
