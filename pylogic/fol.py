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

    def __str__(self) -> str:
        return f"{self.identifier}"

    def __eq__(self, other) -> bool:
        return self.identifier == other.identifier and self.type == other.type

    def __hash__(self) -> int:
        return hash(repr(self))


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
        arg_string = ", ".join(map(repr, self._args))
        neg = "¬" if self.is_negated else ""
        return f"{neg}{self.identifier}({arg_string})"

    def __str__(self) -> str:
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

    def is_empty(self) -> bool:
        return len(self._substitution_values) == 0

    @no_type_check
    def substitute(self, pred: Predicate) -> Predicate:

        args: Tuple[Term] = tuple(
            self._substitution_values.get(self._arg_exception_handler(arg), arg)
            for arg in pred.args
        )
        return Predicate(pred.identifier, args)

    @property
    def substitution_values(self) -> Dict[Term, Term]:
        return {
            Term(k.identifier, k.type): Term(v.identifier, v.type)
            for k, v in self._substitution_values.items()
        }

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
        antecedents = sorted(antecedents, key=lambda x: x.identifier)
        for antecedent in antecedents:
            if antecedent.is_negated:
                raise HornClauseFOL.BadHornClauseFOL(
                    "Antecedents should not be negated"
                )

        # TODO: Raise exception if not atomic (has variables)
        if len(antecedents) == 1 and consequent is None:
            self._antecedents = antecedents
            self._consequent = True
            return

        # TODO: Here it would be better to raise exception, as we are only interested
        # in True atoms
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
        if antecedents:
            return f"{' ^ '.join([repr(v) for v in antecedents])} => {repr(self.consequent)}"
        return f"{repr(self.consequent)}"

    def __str__(self):
        antecedents = sorted(self.antecedents, key=lambda x: str(x))
        if antecedents:
            return f"{' ^ '.join([str(v) for v in antecedents])} => {self.consequent}"
        return f"{self.consequent}"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other) -> bool:
        if not isinstance(other, HornClauseFOL):
            return False

        return self.consequent == other.consequent


def unify(
    x: Union[Term, List[Term]],
    y: Union[Term, List[Term]],
    theta: Optional[Substitution],
) -> Optional[Substitution]:
    """Applies unification of terms.

    It is responsibility of the caller making sure that both
    arguments are applied to the same predicate. We could change the API
    in the future to pass the predicates instead of using the args.
    """
    if theta is None:
        return None

    if isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            return None
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
    """Unifies a variable.

    For example:

    ```
    Knows(John, x) | Knows(y, Carlos)
    ```

    Making the substitutions:

    ```
    {
        x: Carlos,
        y: John
    }
    ```

    We could unify both predicates.
    """
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


def standardize_predicate(pred: Optional[Union[Predicate, bool]], counter, seen):
    args = []
    if isinstance(pred, Predicate):
        for arg in pred.args:
            if arg.type == TermType.VARIABLE:
                if arg.identifier in seen:
                    val = seen[arg.identifier]
                    new_arg = Term(f"{arg.identifier}{val}", arg.type)
                else:
                    new_arg = Term(f"{arg.identifier}{counter}", arg.type)
                    seen[arg.identifier] = counter
                    counter += 1
            else:
                new_arg = Term(arg.identifier, arg.type)
            args.append(new_arg)
    else:
        return pred, counter, seen

    return Predicate(pred.identifier, args), counter, seen


# TODO: Add test and fix implementation as it seems it is not doing what is expected
def standardize_variables(rule: HornClauseFOL, counter):
    """Standardizes all the variables in a Predicate belonging to an Horn Clause.

    For example, if we have the Horn clause:

    ```
    Knows(x, y) ^ Emperor(y) => King(x)
    ```

    Then the standardized version of the clause would be:

    ```
    Knows(x0, y1) ^ Emperor(y1) => King(x0)
    ```

    This is to avoid cases in which the variable name will be a problem in
    unification:

    ```
    Knows(John, x) | Knows(x, Elizabeth)
    ```

    In this case, no unification is possible, since the variable name is the same for
    both predicates, even though they come from different clauses.
    """
    new_antecedents = []
    seen: Dict[str, int] = {}
    for antecedent in rule.antecedents:
        new_pred, counter, seen = standardize_predicate(antecedent, counter, seen)
        new_antecedents.append(new_pred)

    new_consequent, counter, _ = standardize_predicate(rule.consequent, counter, seen)
    return HornClauseFOL(new_antecedents, new_consequent), counter


@no_type_check
def fol_fc_ask(kb: List[HornClauseFOL], alpha) -> Optional[Substitution]:
    known_facts = []
    known_facts_identifier = []
    actual_kb = []
    for hc in kb:
        if is_fact(hc):
            known_facts.append(hc.consequent)
            known_facts_identifier.append(hc.consequent.identifier)
        else:
            actual_kb.append(hc)

    no_new_knowledge = False
    while True:
        new = []
        counter = 0
        for rule in actual_kb:
            rule, counter = standardize_variables(rule, counter)
            theta = Substitution({})
            for antecedent in rule.antecedents:
                for fact, identifier in zip(known_facts, known_facts_identifier):
                    if antecedent.identifier == identifier:
                        theta = unify(fact.args, antecedent.args, theta)

            if theta is not None and not theta.is_empty():
                satisfied = True
                for antecedent in rule.antecedents:
                    p_ = theta.substitute(antecedent)
                    for arg in p_.args:
                        if arg.type == TermType.VARIABLE:
                            satisfied = False
                            break
                    if not satisfied:
                        break

                if satisfied:
                    q_ = theta.substitute(rule.consequent)
                    # TODO: Check renaming of a sentence:
                    if q_ not in known_facts:
                        new.append(q_)
                    if q_.identifier == alpha.identifier:
                        phi = unify(q_.args, alpha.args, theta)
                        if phi is not None:
                            return phi

            for n in new:
                if n not in known_facts:
                    known_facts.append(n)
                    known_facts_identifier.append(n.identifier)
        if no_new_knowledge:
            break
    return None


def compose(theta1, theta2) -> Substitution:
    new_values = theta1.substitution_values
    new_values.update(theta2.substitution_values)
    return Substitution(new_values)


def is_fact(hc: HornClauseFOL) -> bool:
    return len(hc.antecedents) == 0


def fol_bc_ask(kb, goals, theta: Substitution) -> List[Substitution]:
    if len(goals) == 0:
        return [theta]
    q_ = theta.substitute(goals[0])
    counter = 0
    answers: List[Substitution] = []
    for r in kb:
        r, counter = standardize_variables(r, counter)
        q = r.consequent
        if q_.identifier == q.identifier:
            theta_ = unify(q.args, q_.args, Substitution({}))
            if theta_ is not None:
                rest_goals = r.antecedents + goals[1:]

                answers = fol_bc_ask(kb, rest_goals, compose(theta_, theta)) + answers
    return answers
