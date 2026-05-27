from dataclasses import dataclass
from typing import Any


@dataclass
class ProgramNode:
    name: str
    statements: list[Any]


@dataclass
class DeclarationNode:
    var_type: str
    name: str
    line: int
    column: int


@dataclass
class AssignmentNode:
    name: str
    expression: Any
    line: int
    column: int


@dataclass
class ReportNode:
    expression: Any
    line: int
    column: int


@dataclass
class LiteralNode:
    value: Any
    value_type: str
    line: int
    column: int


@dataclass
class IdentifierNode:
    name: str
    line: int
    column: int


@dataclass
class BinaryOperationNode:
    left: Any
    operator: str
    right: Any
    line: int
    column: int
    result_type: str | None = None


@dataclass
class IfNode:
    condition: Any
    body: list[Any]
    line: int
    column: int


@dataclass
class AlertNode:
    expression: Any
    line: int
    column: int


@dataclass
class WhileNode:
    condition: Any
    body: list[Any]
    line: int
    column: int
