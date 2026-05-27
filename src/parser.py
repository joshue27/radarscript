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
from src.errors import ErrorCollector, SyntaxRadarError
from src.tokens import Token, TokenType

# Palabras clave que inician una instrucción → puntos de sincronización
_SYNC_KEYWORDS = {"reporte", "alerta", "si", "mientras", "fin", "programa"}


class Parser:
    def __init__(self, tokens: list[Token], errors: ErrorCollector | None = None):
        self.tokens = tokens
        self.errors = errors or ErrorCollector()
        self.current = 0
        self._in_error = False  # evita cascada de errores

    def parse(self) -> ProgramNode | None:
        if not self._check_lexeme("programa"):
            self._error(
                "se esperaba 'programa' al inicio",
                self._peek().line,
                self._peek().column,
            )
            self._synchronize()
            return None

        self._advance()

        if not self._check(TokenType.IDENTIFICADOR):
            self._error(
                "se esperaba el nombre del programa",
                self._peek().line,
                self._peek().column,
            )
            name_token = Token(TokenType.IDENTIFICADOR, "__desconocido", 0, 0)
        else:
            name_token = self._advance()

        if not self._check(TokenType.PUNTO_Y_COMA):
            self._error(
                "se esperaba ';' después del nombre del programa",
                self._peek().line,
                self._peek().column,
            )
        else:
            self._advance()

        statements = []
        while not self._check(TokenType.EOF):
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)
            else:
                # Error en statement, sincronizar y seguir
                self._synchronize()
                if self._check(TokenType.EOF):
                    break

        return ProgramNode(name_token.lexeme, statements)

    def _statement(self):
        """Intenta reconocer una instrucción. Retorna None si hay error."""
        try:
            self._in_error = False
            if self._check(TokenType.TIPO):
                return self._declaration()
            if self._check(TokenType.IDENTIFICADOR):
                return self._assignment()
            if self._check_lexeme("reporte"):
                return self._report()
            if self._check_lexeme("alerta"):
                return self._alert()
            if self._check_lexeme("si"):
                return self._if_statement()
            if self._check_lexeme("mientras"):
                return self._while_statement()
            token = self._peek()
            if token.type != TokenType.EOF:
                raise SyntaxRadarError(
                    f"instrucción no válida cerca de '{token.lexeme}'",
                    token.line,
                    token.column,
                )
            return None
        except SyntaxRadarError as e:
            self.errors.add(e)
            self._in_error = True
            return None

    def _declaration(self) -> DeclarationNode | None:
        type_token = self._advance()
        name = self._consume(TokenType.IDENTIFICADOR, "se esperaba identificador")
        self._consume(TokenType.PUNTO_Y_COMA, "se esperaba ';'")
        if name is None:
            return None
        return DeclarationNode(type_token.lexeme, name.lexeme, name.line, name.column)

    def _assignment(self) -> AssignmentNode | None:
        name = self._advance()
        self._consume(TokenType.ASIGNACION, "se esperaba '='")
        expression = self._expression()
        self._consume(TokenType.PUNTO_Y_COMA, "se esperaba ';'")
        if expression is None:
            return None
        return AssignmentNode(name.lexeme, expression, name.line, name.column)

    def _report(self) -> ReportNode | None:
        report = self._advance()
        self._consume(TokenType.PARENTESIS_IZQ, "se esperaba '('")
        expression = self._expression()
        self._consume(TokenType.PARENTESIS_DER, "se esperaba ')'")
        self._consume(TokenType.PUNTO_Y_COMA, "se esperaba ';'")
        if expression is None:
            return None
        return ReportNode(expression, report.line, report.column)

    def _alert(self) -> AlertNode | None:
        alert = self._advance()
        self._consume(TokenType.PARENTESIS_IZQ, "se esperaba '('")
        expression = self._expression()
        self._consume(TokenType.PARENTESIS_DER, "se esperaba ')'")
        self._consume(TokenType.PUNTO_Y_COMA, "se esperaba ';'")
        if expression is None:
            return None
        return AlertNode(expression, alert.line, alert.column)

    def _if_statement(self) -> IfNode | None:
        si_token = self._advance()
        condition = self._expression()
        self._consume_lexeme("entonces", "se esperaba 'entonces'")
        body = []
        while not self._check_lexeme("fin") and not self._check(TokenType.EOF):
            stmt = self._statement()
            if stmt is not None:
                body.append(stmt)
        self._consume_lexeme("fin", "se esperaba 'fin'")
        if condition is None:
            return None
        return IfNode(condition, body, si_token.line, si_token.column)

    def _while_statement(self) -> WhileNode | None:
        mientras_token = self._advance()
        condition = self._expression()
        self._consume_lexeme("hacer", "se esperaba 'hacer'")
        body = []
        while not self._check_lexeme("fin") and not self._check(TokenType.EOF):
            stmt = self._statement()
            if stmt is not None:
                body.append(stmt)
        self._consume_lexeme("fin", "se esperaba 'fin'")
        if condition is None:
            return None
        return WhileNode(condition, body, mientras_token.line, mientras_token.column)

    def _expression(self):
        node = self._additive()
        while node is not None and self._check(TokenType.OPERADOR_RELACIONAL):
            op = self._advance()
            right = self._additive()
            if right is None:
                return None
            node = BinaryOperationNode(node, op.lexeme, right, op.line, op.column)
        return node

    def _additive(self):
        node = self._term()
        while (
            node is not None
            and self._check(TokenType.OPERADOR_ARITMETICO)
            and self._peek().lexeme in ("+", "-")
        ):
            op = self._advance()
            right = self._term()
            if right is None:
                return None
            node = BinaryOperationNode(node, op.lexeme, right, op.line, op.column)
        return node

    def _term(self):
        node = self._factor()
        while (
            node is not None
            and self._check(TokenType.OPERADOR_ARITMETICO)
            and self._peek().lexeme in ("*", "/")
        ):
            op = self._advance()
            right = self._factor()
            if right is None:
                return None
            node = BinaryOperationNode(node, op.lexeme, right, op.line, op.column)
        return node

    def _factor(self):
        if self._check(TokenType.PARENTESIS_IZQ):
            self._advance()
            node = self._expression()
            self._consume(TokenType.PARENTESIS_DER, "se esperaba ')'")
            return node

        if self._is_at_end():
            self._error(
                "se esperaba una expresión pero se encontró fin de archivo",
                self._peek().line,
                self._peek().column,
            )
            return None

        token = self._advance()
        if token.type == TokenType.NUMERO_ENTERO:
            return LiteralNode(int(token.lexeme), "entero", token.line, token.column)
        if token.type == TokenType.NUMERO_DECIMAL:
            return LiteralNode(float(token.lexeme), "decimal", token.line, token.column)
        if token.type == TokenType.CADENA:
            return LiteralNode(token.lexeme[1:-1], "cadena", token.line, token.column)
        if token.type == TokenType.BOOLEANO:
            return LiteralNode(
                token.lexeme == "verdadero", "booleano", token.line, token.column
            )
        if token.type == TokenType.IDENTIFICADOR:
            return IdentifierNode(token.lexeme, token.line, token.column)

        self._error("se esperaba una expresión", token.line, token.column)
        return None

    def _consume(self, token_type: TokenType, message: str) -> Token | None:
        """Consume si coincide, si no registra error y retorna None."""
        if self._check(token_type):
            return self._advance()
        token = self._peek()
        self._error(message, token.line, token.column)
        return None

    def _consume_lexeme(self, lexeme: str, message: str) -> Token | None:
        """Consume si coincide el lexema, si no registra error y retorna None."""
        if self._check_lexeme(lexeme):
            return self._advance()
        token = self._peek()
        self._error(message, token.line, token.column)
        return None

    def _error(self, message: str, line: int, column: int) -> None:
        """Registra un error sin lanzar excepción."""
        self.errors.add(SyntaxRadarError(message, line, column))

    def _synchronize(self) -> None:
        """Salta tokens hasta un punto seguro (; o inicio de instrucción)."""
        while not self._is_at_end():
            if self._check(TokenType.PUNTO_Y_COMA):
                self._advance()  # consumir el ;
                return
            if self._check(TokenType.TIPO):
                return
            if self._check_lexeme_in(_SYNC_KEYWORDS):
                return
            self._advance()

    def _check_lexeme_in(self, keywords: set) -> bool:
        return self._peek().lexeme in keywords

    def _check(self, token_type: TokenType) -> bool:
        return self._peek().type == token_type

    def _check_lexeme(self, lexeme: str) -> bool:
        return self._peek().lexeme == lexeme

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self.tokens[self.current - 1]

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF
