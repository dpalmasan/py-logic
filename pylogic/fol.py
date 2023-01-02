from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Tuple, no_type_check, Union

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
        return f"Term({self.identifier}, type={self.type})"

    def __eq__(self, other) -> bool:
        return self.identifier == other.identifier and self.type == other.type

    def __hash__(self) -> int:
        return hash(str(self))


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

    @property
    def args(self) -> Tuple[Term]:
        return self._args

    def __repr__(self) -> str:
        arg_string = ", ".join(map(str, self._args))
        neg = "¬" if self.is_negated else ""
        return f"{neg}{self.identifier}({arg_string})"

    def __invert__(self) -> "Predicate":
        return Predicate(self.identifier, self._args, not self.is_negated)

    def __hash__(self) -> int:
        return hash(self.__repr__())

    def __eq__(self, other) -> bool:
        return (
            self.identifier == other.identifier
            and self.args == other.args
            and self.is_negated == other.is_negated
        )


class OrSentence(Sentence):
    OP = Operator.OR

    def __init__(self, s1: Sentence, s2: Sentence):
        self._s1 = s1
        self._s2 = s2

    # def __invert__(self) -> Sentence:
    #     return ~self._s2 & ~self._s1


class Substitution:
    class ConstantAsVariableException(Exception):
        pass

    def __init__(self, substitution_values: Dict[Term, Term]) -> None:
        self._substitution_values = substitution_values

    def _arg_exception_handler(self, term: Term) -> Term:
        if term in self._substitution_values and term.type is TermType.CONSTANT:
            raise self.ConstantAsVariableException(
                f"Trying to substitute a constant: {term}, type: {term.type}"
            )

        return term

    @no_type_check
    def substitute(self, pred: Predicate) -> Predicate:

        args: Tuple[Term] = tuple(
            self._substitution_values.get(self._arg_exception_handler(arg), arg)
            for arg in pred.args
        )
        return Predicate(pred.identifier, args)


class HornClauseFOL:
    class BadHornClauseFOL(Exception):
        pass

    def __init__(
        self,
        antecedents: List[Predicate],
        consequent: Optional[Union[Predicate, bool]] = None,
    ):
        for antecedent in antecedents:
            if antecedent.is_negated:
                raise HornClauseFOL.BadHornClauseFOL(
                    "Antecedents should not be negated"
                )

        if len(antecedents) == 1 and consequent is None:
            self._antecedents = antecedents
            self._consequent = True
            return

        if isinstance(consequent, Predicate) and consequent.is_negated:
            self._consequent = False
            antecedents.append(~consequent)
        elif consequent is None:
            self._consequent = False
        else:
            self._consequent = consequent  # type: ignore
        self._antecedents = antecedents

    @property
    def antecedents(self) -> List[Predicate]:
        return self._antecedents

    @property
    def consequent(self) -> Union[Predicate, bool]:
        return self._consequent

    def __repr__(self):
        antecedents = sorted(self.antecedents, key=lambda x: str(x))
        return f"{' ^ '.join([str(v) for v in antecedents])} => {self.consequent}"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other) -> bool:
        if not isinstance(other, HornClauseFOL):
            return False
        antecedents = sorted(self.antecedents, key=lambda x: str(x))
        other_ant = sorted(other.antecedents, key=lambda x: str(x))
        if antecedents != other_ant:
            return False

        return self.consequent == other.consequent
