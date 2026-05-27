class RadarScriptError(Exception):
    """Error individual de compilación con ubicación en el código fuente."""

    phase: str = "general"

    def __init__(
        self, message: str, line: int | None = None, column: int | None = None
    ):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return self.message

    def display(self) -> str:
        """Formato completo para mostrar al usuario."""
        if self.line is not None and self.column is not None:
            return f"Error [línea {self.line}, columna {self.column}]: {self.message}"
        return f"Error: {self.message}"


class LexicalError(RadarScriptError):
    phase = "léxico"


class SyntaxRadarError(RadarScriptError):
    phase = "sintáctico"


class SemanticError(RadarScriptError):
    phase = "semántico"


class RuntimeRadarError(RadarScriptError):
    phase = "de ejecución"


class ErrorCollector:
    """Recolecta errores de todas las fases sin detener la compilación."""

    def __init__(self):
        self.errors: list[RadarScriptError] = []

    def add(self, error: RadarScriptError) -> None:
        self.errors.append(error)

    def add_error(
        self,
        phase: str,
        message: str,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """Crea y agrega un error genérico."""
        err = RadarScriptError(message, line, column)
        err.phase = phase
        self.errors.append(err)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def count(self) -> int:
        return len(self.errors)

    def get_all(self) -> list[RadarScriptError]:
        return self.errors

    def clear(self) -> None:
        self.errors.clear()

    def as_display_list(self) -> list[str]:
        return [err.display() for err in self.errors]
