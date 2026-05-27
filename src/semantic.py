from src.ast_nodes import (
    AlertNode,
    AssignmentNode,
    BinaryOperationNode,
    DeclarationNode,
    IdentifierNode,
    IfNode,
    LiteralNode,
    ProgramNode,
    ReportNode,
    WhileNode,
)
from src.errors import ErrorCollector, SemanticError
from src.symbol_table import SymbolTable


class SemanticAnalyzer:
    def __init__(self, errors: ErrorCollector | None = None):
        self.errors = errors or ErrorCollector()
        self.symbol_table = SymbolTable()

    def analyze(self, program: ProgramNode | None) -> SymbolTable:
        if program is None:
            return self.symbol_table
        for statement in program.statements:
            self._analyze_statement(statement)
        return self.symbol_table

    def _analyze_statement(self, statement) -> None:
        try:
            if isinstance(statement, DeclarationNode):
                self._declaration(statement)
            elif isinstance(statement, AssignmentNode):
                self._assignment(statement)
            elif isinstance(statement, (ReportNode, AlertNode)):
                self._expression_type(statement.expression)
            elif isinstance(statement, IfNode):
                self._if_statement(statement)
            elif isinstance(statement, WhileNode):
                self._while_statement(statement)
        except SemanticError as e:
            self.errors.add(e)

    def _if_statement(self, node: IfNode) -> None:
        cond_type = self._expression_type(node.condition)
        if cond_type is not None and cond_type != "booleano":
            self.errors.add_error(
                "semántico",
                "la condición del 'si' debe ser de tipo booleano",
                node.line,
                node.column,
            )
        for stmt in node.body:
            self._analyze_statement(stmt)

    def _while_statement(self, node: WhileNode) -> None:
        cond_type = self._expression_type(node.condition)
        if cond_type is not None and cond_type != "booleano":
            self.errors.add_error(
                "semántico",
                "la condición del 'mientras' debe ser de tipo booleano",
                node.line,
                node.column,
            )
        for stmt in node.body:
            self._analyze_statement(stmt)

    def _declaration(self, node: DeclarationNode) -> None:
        if self.symbol_table.exists(node.name):
            self.errors.add_error(
                "semántico",
                f"variable '{node.name}' ya declarada",
                node.line,
                node.column,
            )
        else:
            self.symbol_table.define(node.name, node.var_type)

    def _assignment(self, node: AssignmentNode) -> None:
        if not self.symbol_table.exists(node.name):
            self.errors.add_error(
                "semántico",
                f"variable '{node.name}' no declarada",
                node.line,
                node.column,
            )
            return
        target_type = self.symbol_table.get_type(node.name)
        value_type = self._expression_type(node.expression)
        if value_type is not None and target_type != value_type:
            self.errors.add_error(
                "semántico",
                f"no se puede asignar {value_type} a {target_type}",
                node.line,
                node.column,
            )

    def _expression_type(self, expression) -> str | None:
        if expression is None:
            return None
        if isinstance(expression, LiteralNode):
            return expression.value_type
        if isinstance(expression, IdentifierNode):
            if not self.symbol_table.exists(expression.name):
                self.errors.add_error(
                    "semántico",
                    f"variable '{expression.name}' no declarada",
                    expression.line,
                    expression.column,
                )
                return None
            return self.symbol_table.get_type(expression.name)
        if isinstance(expression, BinaryOperationNode):
            left_type = self._expression_type(expression.left)
            right_type = self._expression_type(expression.right)

            if left_type is None or right_type is None:
                return None

            if expression.operator == "+" and (
                left_type == "cadena" or right_type == "cadena"
            ):
                expression.result_type = "cadena"
                return "cadena"

            numeric_types = {"entero", "decimal"}

            if expression.operator in (">", "<", ">=", "<="):
                if left_type not in numeric_types or right_type not in numeric_types:
                    self.errors.add_error(
                        "semántico",
                        f"tipos incompatibles para '{expression.operator}': {left_type} y {right_type}",
                        expression.line,
                        expression.column,
                    )
                    return None
                expression.result_type = "booleano"
                return "booleano"

            if expression.operator in ("==", "!="):
                if left_type == right_type or (
                    left_type in numeric_types and right_type in numeric_types
                ):
                    expression.result_type = "booleano"
                    return "booleano"
                self.errors.add_error(
                    "semántico",
                    f"tipos incompatibles para '{expression.operator}': {left_type} y {right_type}",
                    expression.line,
                    expression.column,
                )
                return None

            if left_type not in numeric_types or right_type not in numeric_types:
                self.errors.add_error(
                    "semántico",
                    f"tipos incompatibles para '{expression.operator}': {left_type} y {right_type}",
                    expression.line,
                    expression.column,
                )
                return None

            if expression.operator == "/":
                expression.result_type = "decimal"
                return "decimal"
            if "decimal" in (left_type, right_type):
                expression.result_type = "decimal"
                return "decimal"
            expression.result_type = "entero"
            return "entero"

        return None
