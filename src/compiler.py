from dataclasses import dataclass, field
from pathlib import Path

from src.errors import ErrorCollector, RadarScriptError
from src.intermediate import IntermediateGenerator, format_intermediate
from src.lexer import Lexer
from src.object_code import ObjectCodeGenerator
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.vm import VirtualMachine


@dataclass
class CompileResult:
    success: bool
    errors: list[RadarScriptError] = field(default_factory=list)
    vm_output: list[str] = field(default_factory=list)


class RadarCompiler:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def compile(self, source_path: Path) -> CompileResult:
        self.output_dir.mkdir(exist_ok=True)
        base_name = source_path.stem
        error_path = self.output_dir / f"{base_name}.err"

        try:
            source = source_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            message = f"No se encontró el archivo: {source_path}"
            self._write(error_path, message)
            return CompileResult(
                success=False,
                errors=[RadarScriptError(message)],
            )

        errors = ErrorCollector()

        # ── 1. Lexer ────────────────────────────────────────────────
        lexer = Lexer(source, errors)
        tokens = lexer.scan_tokens()
        self._write(
            self.output_dir / f"{base_name}.lex",
            "\n".join(token.display() for token in tokens if token.lexeme),
        )

        # ── 2. Parser ───────────────────────────────────────────────
        parser = Parser(tokens, errors)
        ast = parser.parse()

        # ── 3. Semántico ────────────────────────────────────────────
        semantic = SemanticAnalyzer(errors)
        symbol_table = semantic.analyze(ast)
        self._write(self.output_dir / f"{base_name}.sym", symbol_table.display())

        # ── Si hay errores o AST inválido, no generar código ──────
        if errors.has_errors() or ast is None:
            error_text = "\n".join(errors.as_display_list())
            self._write(error_path, error_text)
            return CompileResult(success=False, errors=errors.get_all())

        # ── 4. Generación de código ─────────────────────────────────
        try:
            intermediate_code = IntermediateGenerator().generate(ast)
            self._write(
                self.output_dir / f"{base_name}.int",
                format_intermediate(intermediate_code),
            )

            object_code = ObjectCodeGenerator().generate(intermediate_code)
            self._write(self.output_dir / f"{base_name}.obj", "\n".join(object_code))

            # ── 5. VM ───────────────────────────────────────────────
            vm_output = VirtualMachine().execute(object_code)
            self._write(error_path, "Sin errores.")
            return CompileResult(success=True, vm_output=vm_output)
        except RadarScriptError as e:
            errors.add(e)
            self._write(error_path, e.display())
            return CompileResult(success=False, errors=errors.get_all())

    def _write(self, path: Path, content: str) -> None:
        path.write_text(content + "\n", encoding="utf-8")
