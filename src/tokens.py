from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    PALABRA_RESERVADA = "PALABRA_RESERVADA"
    TIPO = "TIPO"
    IDENTIFICADOR = "IDENTIFICADOR"
    NUMERO_ENTERO = "NUMERO_ENTERO"
    NUMERO_DECIMAL = "NUMERO_DECIMAL"
    CADENA = "CADENA"
    BOOLEANO = "BOOLEANO"
    OPERADOR_ARITMETICO = "OPERADOR_ARITMETICO"
    OPERADOR_RELACIONAL = "OPERADOR_RELACIONAL"
    ASIGNACION = "ASIGNACION"
    PUNTO_Y_COMA = "PUNTO_Y_COMA"
    PARENTESIS_IZQ = "PARENTESIS_IZQ"
    PARENTESIS_DER = "PARENTESIS_DER"
    COMA = "COMA"
    EOF = "EOF"


TYPES = {"entero", "decimal", "cadena", "booleano"}
BOOLEANS = {"verdadero", "falso"}
RESERVED_WORDS = {
    "programa",
    "si",
    "entonces",
    "mientras",
    "hacer",
    "fin",
    "alerta",
    "reporte",
    *TYPES,
    *BOOLEANS,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int

    def display(self) -> str:
        return f"{self.type.value:<22} {self.lexeme:<25} línea {self.line}, columna {self.column}"
