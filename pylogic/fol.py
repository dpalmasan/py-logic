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
        args: List[Term],
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
    def args(self) -> List[Term]:
        return list(self._args)

    def __repr__(self) -> str:
        arg_string = ", ".join(map(str, self._args))
        neg = "¬" if self.is_negated else ""
        return f"{neg}{self.identifier}({arg_string})"

    def __invert__(self) -> "Predicate":
        return Predicate(self.identifier, list(self.args), not self.is_negated)

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

    def __contains__(self, key: Term) -> bool:
        return key in self._substitution_values

    def __getitem__(self, key: Term) -> Term:
        return self._substitution_values[key]

    def add_substitutions(
        self, substitution_values: Dict[Term, Term]
    ) -> "Substitution":
        new_subs = {
            Term(k.identifier, k.type): Term(v.identifier, v.type)
            for k, v in self._substitution_values.items()
        }

        new_subs.update(substitution_values)
        return Substitution(new_subs)

    def __len__(self):
        return len(self._substitution_values)

    def __repr__(self):
        return str(self._substitution_values)

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        return all(
            x in self and x in other and self[x] == other[x]
            for x in self._substitution_values
        )


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


def unify(
    x: Union[Term, List[Term]],
    y: Union[Term, List[Term]],
    theta: Optional[Substitution],
) -> Optional[Substitution]:
    if theta is None:
        return None

    if isinstance(x, list) and isinstance(y, list):
        if x == y:
            return theta
        return unify(x[1:], y[1:], unify(x[0], y[0], theta))

    if isinstance(x, list) or isinstance(y, list):
        return None
    if x == y:
        return theta
    if x.type == TermType.VARIABLE:
        return unify_var(x, y, theta)
    if y.type == TermType.VARIABLE:
        return unify_var(y, x, theta)

    # TODO: Case with compound expression, example using function symbols

    return None


def unify_var(
    var: Term, x: Term, theta: Optional[Substitution]
) -> Optional[Substitution]:
    if theta is not None:
        if var in theta:
            return unify(theta[var], x, theta)
        if x in theta:
            return unify(var, theta[x], theta)
    else:
        theta = Substitution({})

    # TODO: This is only if functional symbols appear in the expression
    # Case with occur check, example x/f(x), meaning f(f(x))...

    return theta.add_substitutions({var: x})


def standardize_variables(rule: HornClauseFOL):
    new_antecedents = []
    i = 0
    for antecedent in rule.antecedents:
        args = []
        for arg in antecedent.args:
            if arg.type == TermType.VARIABLE:
                new_arg = Term(f"x{i}", arg.type)
                i += 1
            else:
                new_arg = Term(arg.identifier, arg.type)

            args.append(new_arg)
        new_antecedents.append(
            Predicate(antecedent.identifier, args, antecedent.is_negated)
        )

    new_consequent = rule.consequent
    if isinstance(rule.consequent, Predicate):
        args = []
        for arg in rule.consequent.args:
            if arg.type == TermType.VARIABLE:
                new_arg = Term(f"x{i}", arg.type)
                i += 1
            else:
                new_arg = Term(arg.identifier, arg.type)
            args.append(new_arg)
        new_consequent = Predicate(rule.consequent.identifier, args)

    return HornClauseFOL(new_antecedents, new_consequent)


def fol_fc_ask(kb: List[HornClauseFOL], alpha) -> Optional[Substitution]:
    while True:
        # new = set()
        for _ in kb:
            pass  # std_rule = standardize_variables(rule)
        break
    return None
