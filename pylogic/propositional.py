from enum import Enum
from abc import ABC, abstractmethod
from typing import DefaultDict, Dict, List, Optional, Set, Tuple, Union, no_type_check
from functools import reduce, singledispatchmethod
from collections import defaultdict


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

    def __init__(
        self, identifier: str, is_negated: bool, truthyness: Optional[bool] = None
    ):
        self._identifier = identifier
        self._is_negated = is_negated
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
    def is_negated(self) -> bool:
        return self._is_negated

    @property
    def truthyness(self) -> Optional[bool]:
        return self._truthyness

    @truthyness.setter
    def truthyness(self, val):
        self._truthyness = val

    def __repr__(self) -> str:
        return "{}{}".format("¬" if (self._is_negated) else "", self._identifier)

    def __invert__(self) -> "Clause":
        return Variable(self._identifier, not self._is_negated, not self._truthyness)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Variable):
            return False
        return (
            self.identifier == other.identifier and self.is_negated == other.is_negated
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


def _is_simple_clause(phi: Clause) -> bool:
    return (
        type(phi.lhs) == Variable
        and type(phi.rhs) == Variable
        and phi.OP != Operator.VARIABLE
    )


def _is_variable(phi: Clause):
    return phi.OP == Operator.VARIABLE


def _distribute_clauses(p, q):  # noqa: C901
    # Base Cases
    if _is_variable(p) and _is_simple_clause(q):
        if q.OP == Operator.AND:
            return (p.lhs | q.lhs) & (p.lhs | q.rhs)
        return p.lhs | q.lhs | q.rhs

    if _is_variable(q) and _is_simple_clause(p):
        if p.OP == Operator.AND:
            return (p.lhs | q.lhs) & (p.rhs | q.lhs)
        return p.lhs | p.rhs | q.lhs

    if _is_variable(p) and _is_variable(q):
        return p | q

    if _is_simple_clause(p) and _is_simple_clause(q):
        if p.OP == Operator.AND and q.OP == Operator.AND:
            return (p.lhs | q.lhs) & (p.lhs | q.rhs) & (p.rhs | q.lhs) & (p.rhs | q.rhs)

        if p.OP == Operator.AND:
            return (p.lhs | q.lhs | q.rhs) & (p.rhs | q.lhs | q.rhs)

        if q.OP == Operator.AND:
            return (p.lhs | p.rhs | q.lhs) & (p.lhs | p.rhs | q.rhs)
        return p.lhs | p.rhs | q.lhs | q.rhs

    # Recursion
    if _is_variable(p):
        if q.OP == Operator.AND:
            return _distribute_clauses(p.lhs, q.lhs) & _distribute_clauses(p.lhs, q.rhs)
        return p | _distribute_clauses(q.lhs, q.rhs)

    if _is_variable(q):
        if p.OP == Operator.AND:
            return _distribute_clauses(p.lhs, q.lhs) & _distribute_clauses(p.rhs, q.lhs)
        return _distribute_clauses(p.lhs, p.rhs) | q

    if _is_simple_clause(p):
        if q.OP == Operator.AND:
            return _distribute_clauses(p, q.lhs) & _distribute_clauses(p, q.rhs)
        return _distribute_clauses(p, q.lhs) | _distribute_clauses(p, q.rhs)

    if _is_simple_clause(q):
        if p.OP == Operator.AND:
            return _distribute_clauses(p.lhs, q) & _distribute_clauses(p.rhs, q)
        return _distribute_clauses(p.lhs, q) | _distribute_clauses(p.rhs, q)

    if p.OP == Operator.AND and q.OP == Operator.AND:
        return (
            _distribute_clauses(p.lhs, q.lhs)
            & _distribute_clauses(p.lhs, q.rhs)
            & _distribute_clauses(p.rhs, q.lhs)
            & _distribute_clauses(p.rhs, q.rhs)
        )

    if p.OP == Operator.AND:
        return _distribute_clauses(p, q.lhs) & _distribute_clauses(p, q.rhs)

    if q.OP == Operator.AND:
        return _distribute_clauses(p.lhs, q) & _distribute_clauses(p.rhs, q)
    return _distribute_clauses(p.lhs, p.rhs) | _distribute_clauses(q.lhs, q.rhs)


def to_cnf(phi: Clause) -> Clause:
    if phi.OP == Operator.AND:
        p = to_cnf(phi.lhs)
        q = to_cnf(phi.rhs)
        return p & q

    if phi.OP == Operator.OR:
        p = to_cnf(phi.lhs)
        q = to_cnf(phi.rhs)
        return _distribute_clauses(p, q)

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

    @property
    def literals(self) -> Set[Variable]:
        return self._literals

    def resolve(self, other: "CnfClause", literal: Variable) -> "CnfClause":
        c1 = CnfClause(self._literals.copy())
        c2 = CnfClause(other._literals.copy())
        if literal not in c1 and ~literal not in c1:
            raise CnfResolveError(f"Literal {literal} not found in clause {self}")

        if literal not in c2 and ~literal not in c2:
            raise CnfResolveError(f"Literal {literal} not found in clause {other}")

        c1p = c1 if literal in self else c2
        c2p = c1 if ~literal in self else c2

        c1p._literals.remove(literal)
        c2p._literals.remove(~literal)  # type: ignore
        return CnfClause(c1p._literals | c2p._literals)

    def is_empty_clause(self) -> bool:
        return len(self._literals) == 0

    def __contains__(self, key: Clause) -> bool:
        return key in self._literals

    def __repr__(self) -> str:
        return "({})".format(
            " v ".join(map(str, sorted(self._literals, key=lambda x: str(x))))
        )

    def __eq__(self, other) -> bool:
        return self.__repr__() == other.__repr__()

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.__repr__())

    def __len__(self) -> int:
        return len(self._literals)

    def issubset(self, other) -> bool:
        subset = True
        for literal in self.literals:
            if literal not in other.literals:
                subset = False
        return subset

    def is_true(self, model) -> Optional[bool]:
        for literal in self.literals:
            if literal.identifier in model:
                if literal.is_negated:
                    literal.truthyness = not model[literal.identifier]
                else:
                    literal.truthyness = model[literal.identifier]
            else:
                literal.truthyness = None

        is_true = reduce(
            lambda x, y: x is True or y is True,
            (literal.truthyness for literal in self.literals),
        )
        if is_true:
            return True

        for literal in self.literals:
            if literal.truthyness is None:
                return None
        return False


class PropLogicKB(ABC):
    _clauses: Optional[Union[Set[Clause], List[Clause]]] = None

    @property
    def clauses(self) -> Optional[Union[Set[Clause], List[Clause]]]:
        return self._clauses

    @singledispatchmethod
    def add(self, arg) -> None:
        raise NotImplementedError(f"Cannot add objects of type {type(arg)}")

    @add.register
    def _(self, clause: Clause) -> None:
        if isinstance(self, ResolutionKB):
            clauses = CnfParser().parse(to_cnf(clause))
            for c in clauses:
                self.add(c)
            return

        if isinstance(self.clauses, set):
            self.clauses.add(clause)
        else:
            self.clauses.append(clause)  # type: ignore

    @no_type_check
    @add.register
    def _(self, clause: CnfClause) -> None:  # type: ignore
        assert isinstance(self, PropLogicKB)
        self.clauses.add(clause)

    @no_type_check
    @add.register
    def _(self, clauses: list) -> None:  # type: ignore
        for clause in clauses:
            self.add(clause)

    @no_type_check
    @add.register
    def _(self, clauses: set) -> None:  # type: ignore
        for clause in clauses:
            self.add(clause)

    @abstractmethod
    def query(self, alpha: Clause) -> bool:
        pass


class ResolutionKB(PropLogicKB):
    @no_type_check
    def __init__(
        self, clauses: Optional[Union[Set[Clause], List[Clause], Clause]] = None
    ):
        clauses = set() if clauses is None else clauses
        cnf_clauses = set()
        parser = CnfParser()
        if not isinstance(clauses, Clause):
            for clause in clauses:
                if not isinstance(clause, CnfClause):
                    cnf_clause = parser.parse(to_cnf(clause))
                    cnf_clauses |= cnf_clause
                else:
                    cnf_clauses |= {clause}
        else:
            cnf_clauses = parser.parse(to_cnf(clauses))

        self._clauses = cnf_clauses if cnf_clauses else set()

    def query(self, alpha: Clause) -> bool:
        return pl_resolution(self, alpha)


class DpllKB(PropLogicKB):
    def __init__(
        self, clauses: Optional[Union[Set[Clause], List[Clause], Clause]] = None
    ):
        self._clauses = []

        if clauses is None:
            return

        if isinstance(clauses, Clause):
            self.add(clauses)
            return
        self._clauses.extend(clauses)

    @no_type_check
    def query(self, alpha: Clause) -> bool:
        return dpll_satisfiable(reduce(lambda x, y: x & y, self.clauses) & alpha)


class CnfParser:
    def __init__(self):
        self.and_clauses = []
        self.or_clauses = []

    def _get_subtrees(self, node: Clause):
        if type(node) != Variable:
            if node.OP == Operator.AND:
                if node.lhs.OP != Operator.AND:
                    self.and_clauses.append(node.lhs)
                else:
                    self._get_subtrees(node.lhs)

                if node.rhs.OP != Operator.AND:
                    self.and_clauses.append(node.rhs)
                else:
                    self._get_subtrees(node.rhs)

    def _get_cnf_clause(self, subtree: Clause) -> Set[Variable]:
        if type(subtree) != Variable:
            return self._get_cnf_clause(subtree.lhs) | self._get_cnf_clause(subtree.rhs)

        return {subtree.lhs}

    def parse(self, clause: Clause) -> Set[CnfClause]:
        """Transform a formula into a set of CnfClauses.

        Assumes that tha ``clause`` comes in CNF form, otherwise
        the behavior is undefined. It is recommended running ``to_cnf`` to
        the sentence you'd like to transform.

        :param clause: Clause in CNF form
        :type clause: Clause
        :return: All disjoint clauses
        :rtype: Set[CnfClause]
        """
        self.and_clauses = []
        self.or_clauses = []
        cnf_clauses = set()
        self._get_subtrees(clause)

        if self.and_clauses:
            for subtree in self.and_clauses:
                try:
                    cnf_clauses.add(CnfClause(self._get_cnf_clause(subtree)))
                except UselessCnfClauseException:
                    pass
        else:
            try:
                cnf_clauses.add(CnfClause(self._get_cnf_clause(clause)))
            except UselessCnfClauseException:
                pass
        return cnf_clauses


class BadHornClause(Exception):
    pass


class HornClause:
    def __init__(self, antecedents: List[Variable], consequent: Variable):
        current_sign = None
        for antecedent in antecedents:
            if current_sign is None:
                current_sign = antecedent.is_negated
            else:
                if antecedent.is_negated != current_sign:
                    raise BadHornClause("Antecedents should have the same sign")

        self._consequent = consequent
        self._antecedents = antecedents

    @property
    def antecedents(self) -> List[Variable]:
        return self._antecedents

    @property
    def consequent(self) -> Variable:
        return self._consequent

    def __repr__(self):
        antecedents = sorted(self.antecedents, key=lambda x: str(x))
        return f"{' ^ '.join([str(~v) for v in antecedents])} => {self.consequent}"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other) -> bool:
        if not isinstance(other, HornClause):
            return False
        antecedents = sorted(self.antecedents, key=lambda x: str(x))
        other_ant = sorted(other.antecedents, key=lambda x: str(x))
        if antecedents != other_ant:
            return False

        return self.consequent == other.consequent


# noqa: C901
def pl_resolution(kb: ResolutionKB, alpha: Clause, maxit=1000) -> bool:
    parser = CnfParser()
    alpha_cnf = parser.parse(to_cnf(~alpha))

    assert kb.clauses is not None
    kb = ResolutionKB(kb.clauses.copy())
    interesting_clauses = ResolutionKB()
    for clause in alpha_cnf:
        interesting_clauses.add(clause)

    new_knowledge = ResolutionKB()

    it = 1
    while it <= maxit:
        literal_clause_map: DefaultDict[Variable, List[CnfClause]] = defaultdict(list)
        for clause in interesting_clauses.clauses:
            for literal in clause.literals:
                literal_clause_map[literal].append(clause)  # type: ignore

        assert isinstance(kb.clauses, list) or isinstance(kb.clauses, set)
        for clause in kb.clauses:  # type: ignore
            for literal in clause.literals:
                literal_clause_map[literal].append(clause)  # type: ignore

        clause_pairs: List[Tuple[CnfClause, CnfClause, Variable]] = []
        for ci in interesting_clauses.clauses:
            for literal in ci.literals:
                if ~literal in literal_clause_map:
                    for cj in literal_clause_map[~literal]:  # type: ignore
                        clause_pairs.append((ci, cj, literal))

        for ci, cj, literal in clause_pairs:
            try:
                res = ci.resolve(cj, literal)
            except UselessCnfClauseException:
                pass
            if res.is_empty_clause():
                return True
            else:
                new_knowledge.add(res)

        added_knowledge = False
        for clause in new_knowledge.clauses:
            any_subset = False
            for old_clause in interesting_clauses.clauses:
                if old_clause.issubset(clause):
                    any_subset = True

            for old_clause in kb.clauses:
                if old_clause.issubset(clause):
                    any_subset = True

            if not any_subset:
                interesting_clauses.add(clause)
                added_knowledge = True

        if not added_knowledge:
            return False

        it += 1

    # Negation as failure (exhausted!)
    return False


def find_pure_symbol(
    symbols: Set[str], clauses: Set[CnfClause], model: Dict[str, bool]
) -> Tuple[Optional[str], Optional[bool]]:
    variables = set()
    for symbol in symbols:
        for clause in clauses:
            for literal in clause.literals:
                if literal.identifier == symbol:
                    variables.add(literal)

    for clause in clauses:
        for literal in clause.literals:
            if literal in variables and ~literal not in variables:
                return literal.identifier, model[literal.identifier]

    return None, None


def find_unit_clause(
    clauses: Set[CnfClause], model, previously_seen: Set[str]
) -> Tuple[Optional[str], Optional[bool]]:
    """Model should already assign all values

    :param clauses: _description_
    :type clauses: Set[CnfClause]
    :param model: _description_
    :type model: _type_
    :return: _description_
    :rtype: Tuple[str, bool]
    """
    for clause in clauses:
        for literal in clause.literals:
            # Search for a unit clause, we look for the positive symbol
            false_literals = set()
            if literal.identifier in model:
                value = model[literal.identifier]
                if literal.is_negated:
                    value = not value
                if value is False:
                    false_literals.add(literal)
            # If we find positive symbols, a unit clause should contain just 1
            if len(clause.literals) - len(false_literals) == 1:
                unit_clause_symbol = next(
                    iter(clause.literals - false_literals)
                ).identifier
                if unit_clause_symbol in previously_seen:
                    continue
                return unit_clause_symbol, model[unit_clause_symbol]
    return None, None


def dpll(
    clauses: Set[CnfClause], symbols: Set[str], model, previously_seen: Set[str]
) -> bool:
    all_clauses_true = reduce(
        lambda x, y: (x is True and y is True),
        (clause.is_true(model) for clause in clauses),
    )
    if all_clauses_true:
        return True
    # If some clause is True in model
    for clause in clauses:
        if clause.is_true(model) is not None and not clause.is_true(model):
            return False

    p, value = find_pure_symbol(symbols, clauses, model)
    # if p is not None:
    if p is not None and value is not None:
        d1 = model.copy()
        d1[p] = value
        return dpll(clauses, symbols - {p}, d1, previously_seen)
    p, value = find_unit_clause(clauses, model, previously_seen)
    if p is not None and value is not None:
        d1 = model.copy()
        d1[p] = value
        previously_seen.add(p)
        return dpll(clauses, symbols - {p}, d1, previously_seen)

    symbols_ = symbols.copy()
    p = symbols_.pop()
    rest = symbols_
    d1 = model.copy()
    d1[p] = True
    d2 = model.copy()
    d2[p] = False
    return dpll(clauses, rest, d1, previously_seen) or dpll(
        clauses, rest, d2, previously_seen
    )


def find_clause_symbols(cnf_clauses: Set[CnfClause]) -> Set[str]:
    symbols = set()
    for clause in cnf_clauses:
        for literal in clause.literals:
            if literal not in symbols and ~literal not in symbols:
                symbols.add(literal.identifier)
    return symbols


def dpll_satisfiable(s: Clause) -> bool:
    if not isinstance(s, Clause):
        raise Exception("Input must be a propositional logic sentence.")

    parser = CnfParser()
    clauses = to_cnf(s)
    cnf_clauses = parser.parse(clauses)
    symbols = find_clause_symbols(cnf_clauses)
    return dpll(cnf_clauses, symbols, defaultdict(lambda: None), set())
