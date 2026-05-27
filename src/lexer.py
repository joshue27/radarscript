from src.errors import ErrorCollector, LexicalError
from src.tokens import BOOLEANS, RESERVED_WORDS, TYPES, Token, TokenType


class Lexer:
    def __init__(self, source: str, errors: ErrorCollector | None = None):
        self.source = source
        self.errors = errors or ErrorCollector()
        self.tokens: list[Token] = []
        self.current = 0
        self.line = 1
        self.column = 1

    def scan_tokens(self) -> list[Token]:
        while not self._is_at_end():
            char = self._advance()

            if char in " \r\t":
                continue
            if char == "\n":
                self.line += 1
                self.column = 1
                continue
            if char == "/" and self._match("/"):
                self._skip_comment()
                continue

            token_line = self.line
            token_column = self.column - 1

            try:
                if char.isalpha():
                    self._identifier(char, token_line, token_column)
                elif char.isdigit():
                    self._number(char, token_line, token_column)
                elif char == '"':
                    self._string(token_line, token_column)
                elif char in "+-*/":
                    self._add(
                        TokenType.OPERADOR_ARITMETICO, char, token_line, token_column
                    )
                elif char in "><=!":
                    self._operator_or_assignment(char, token_line, token_column)
                elif char == ";":
                    self._add(TokenType.PUNTO_Y_COMA, char, token_line, token_column)
                elif char == "(":
                    self._add(TokenType.PARENTESIS_IZQ, char, token_line, token_column)
                elif char == ")":
                    self._add(TokenType.PARENTESIS_DER, char, token_line, token_column)
                elif char == ",":
                    self._add(TokenType.COMA, char, token_line, token_column)
                else:
                    raise LexicalError(
                        f"símbolo inválido '{char}'", token_line, token_column
                    )
            except LexicalError as e:
                self.errors.add(e)
                # Saltar el carácter problemático y seguir

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def _identifier(self, first: str, line: int, column: int) -> None:
        lexeme = first
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            lexeme += self._advance()

        if lexeme in TYPES:
            token_type = TokenType.TIPO
        elif lexeme in BOOLEANS:
            token_type = TokenType.BOOLEANO
        elif lexeme in RESERVED_WORDS:
            token_type = TokenType.PALABRA_RESERVADA
        else:
            token_type = TokenType.IDENTIFICADOR
        self._add(token_type, lexeme, line, column)

    def _number(self, first: str, line: int, column: int) -> None:
        lexeme = first
        while not self._is_at_end() and self._peek().isdigit():
            lexeme += self._advance()

        if not self._is_at_end() and self._peek() == ".":
            lexeme += self._advance()
            if self._is_at_end() or not self._peek().isdigit():
                raise LexicalError("número decimal incompleto", line, column)
            while not self._is_at_end() and self._peek().isdigit():
                lexeme += self._advance()
            self._add(TokenType.NUMERO_DECIMAL, lexeme, line, column)
            return

        self._add(TokenType.NUMERO_ENTERO, lexeme, line, column)

    def _string(self, line: int, column: int) -> None:
        value = ""
        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\n":
                raise LexicalError("cadena sin cerrar", line, column)
            value += self._advance()

        if self._is_at_end():
            raise LexicalError("cadena sin cerrar", line, column)

        self._advance()
        self._add(TokenType.CADENA, f'"{value}"', line, column)

    def _operator_or_assignment(self, char: str, line: int, column: int) -> None:
        if char == "=":
            if self._match("="):
                self._add(TokenType.OPERADOR_RELACIONAL, "==", line, column)
            else:
                self._add(TokenType.ASIGNACION, "=", line, column)
            return

        if char == "!":
            if self._match("="):
                self._add(TokenType.OPERADOR_RELACIONAL, "!=", line, column)
                return
            raise LexicalError("se esperaba '=' después de '!'", line, column)

        lexeme = char + ("=" if self._match("=") else "")
        self._add(TokenType.OPERADOR_RELACIONAL, lexeme, line, column)

    def _skip_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _add(self, token_type: TokenType, lexeme: str, line: int, column: int) -> None:
        self.tokens.append(Token(token_type, lexeme, line, column))

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _peek(self) -> str:
        return "\0" if self._is_at_end() else self.source[self.current]

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)
