from src.ast_nodes import AlertNode, AssignmentNode, BinaryOperationNode, IdentifierNode, IfNode, LiteralNode, ProgramNode, ReportNode, WhileNode


class IntermediateGenerator:
    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def _new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"

    def generate(self, program: ProgramNode) -> list[tuple[str, str, str, str]]:
        code: list[tuple[str, str, str, str]] = []
        for statement in program.statements:
            self._generate_statement(statement, code)
        return code

    def _generate_statement(self, statement, code: list[tuple[str, str, str, str]]) -> None:
        if isinstance(statement, AssignmentNode):
            result = self._generate_expression(statement.expression, code)
            code.append(("=", result, "-", statement.name))
        elif isinstance(statement, ReportNode):
            result = self._generate_expression(statement.expression, code)
            code.append(("REPORTE", result, "-", "-"))
        elif isinstance(statement, AlertNode):
            result = self._generate_expression(statement.expression, code)
            code.append(("ALERTA", result, "-", "-"))
        elif isinstance(statement, IfNode):
            self._generate_if(statement, code)
        elif isinstance(statement, WhileNode):
            self._generate_while(statement, code)

    def _generate_if(self, node: IfNode, code: list[tuple[str, str, str, str]]) -> None:
        result = self._generate_expression(node.condition, code)
        end_label = self._new_label()
        code.append(("JF", result, "-", end_label))
        for stmt in node.body:
            self._generate_statement(stmt, code)
        code.append(("LABEL", "-", "-", end_label))

    def _generate_while(self, node: WhileNode, code: list[tuple[str, str, str, str]]) -> None:
        start_label = self._new_label()
        end_label = self._new_label()
        code.append(("LABEL", "-", "-", start_label))
        result = self._generate_expression(node.condition, code)
        code.append(("JF", result, "-", end_label))
        for stmt in node.body:
            self._generate_statement(stmt, code)
        code.append(("JMP", "-", "-", start_label))
        code.append(("LABEL", "-", "-", end_label))

    def _generate_expression(self, expression, code: list[tuple[str, str, str, str]]) -> str:
        if isinstance(expression, LiteralNode):
            if expression.value_type == "cadena":
                return f'"{expression.value}"'
            if expression.value_type == "booleano":
                return "verdadero" if expression.value else "falso"
            return str(expression.value)
        if isinstance(expression, IdentifierNode):
            return expression.name
        if isinstance(expression, BinaryOperationNode):
            left = self._generate_expression(expression.left, code)
            right = self._generate_expression(expression.right, code)
            op = "CONCAT" if expression.operator == "+" and expression.result_type == "cadena" else expression.operator
            temp = self._new_temp()
            code.append((op, left, right, temp))
            return temp
        raise ValueError("expresión intermedia no soportada")


def format_intermediate(code: list[tuple[str, str, str, str]]) -> str:
    return "\n".join(f"({op}, {arg1}, {arg2}, {result})" for op, arg1, arg2, result in code)
