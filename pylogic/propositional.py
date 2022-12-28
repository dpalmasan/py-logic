from enum import Enum
from abc import ABC, abstractmethod
from typing import DefaultDict, List, Optional, Set, Tuple
from functools import singledispatchmethod
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


# noqa: C901
def pl_resolution(kb: PropLogicKB, alpha: Clause, maxit=1000, threshold=10000) -> bool:
    parser = CnfParser()
    alpha_cnf = parser.parse(to_cnf(~alpha))

    kb = PropLogicKB(kb.clauses.copy())
    interesting_clauses = PropLogicKB()
    for clause in alpha_cnf:
        interesting_clauses.add(clause)

    new_knowledge = PropLogicKB()

    it = 1
    while it <= maxit:
        literal_clause_map: DefaultDict[Variable, List[CnfClause]] = defaultdict(list)
        for clause in interesting_clauses.clauses:
            for literal in clause.literals:
                literal_clause_map[literal].append(clause)  # type: ignore

        for clause in kb.clauses:
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

        if not added_knowledge or len(interesting_clauses.clauses) >= threshold:
            return False

        it += 1

    # Negation as failure (exhausted!)
    return False
