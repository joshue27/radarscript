"""Interfaz grafica para el compilador RadarScript.

Para mantener la integridad de los archivos originales del usuario, si el codigo
fuente se edita en el editor se guarda temporalmente en output/gui_temp.rdr antes
de compilar. Si no hay ediciones, se compila directamente el archivo seleccionado.
"""

import contextlib
import re
import sys
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import DANGER, INFO, PRIMARY, SECONDARY, SUCCESS

from run_obj import ObjRunnerDashboard
from src.compiler import RadarCompiler
from src.errors import RadarScriptError
from src.report_generator import ReportData, generate_report, open_report

# ── Paleta de colores para widgets tk nativos ──────────────────────────
COLORS = {
    "editor_bg": "#1e1e1e",
    "editor_fg": "#d4d4d4",
    "line_bg": "#252526",
    "line_fg": "#858585",
    "line_active_bg": "#2a2d2e",
    "line_active_fg": "#c6c6c6",
    "output_bg": "#1e1e1e",
    "output_fg": "#d4d4d4",
    "insert": "#aeafad",
    "select_bg": "#264f78",
    "select_fg": "#ffffff",
    "current_line_bg": "#2a2d2e",
}

# ── Colores de syntax highlighting ─────────────────────────────────────
SYNTAX_COLORS = {
    "keyword": "#569cd6",  # azul como VS Code
    "builtin": "#dcdcaa",  # amarillo
    "string": "#ce9178",  # naranja
    "comment": "#6a9955",  # verde
    "number": "#b5cea8",  # verde claro
    "boolean": "#569cd6",  # azul
    "operator": "#d4d4d4",  # blanco
}


class RadarGUI:
    def __init__(self, root: tb.Window) -> None:
        self.root = root
        self.root.title("RadarScript — Compilador")
        self.root.geometry("1300x800")
        self.root.minsize(1000, 650)

        self.source_path: Path | None = None
        self.original_source: str = ""
        self.edited_since_load: bool = False
        self.output_dir = Path("output")
        self.compiler = RadarCompiler(output_dir=self.output_dir)

        # Debouncer para syntax highlighting
        self._highlight_after_id: str | None = None
        self._last_report_path: Path | None = None
        self._output_frames: list[tb.Frame] = []

        # Errores de compilacion y navegacion
        self._compile_errors: list[RadarScriptError] = []
        self._current_error_idx: int = -1

        self._build_ui()
        self._apply_style_overrides()
        self._configure_syntax_tags()

    # ── Construccion de la interfaz ────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Barra de herramientas ──
        self._build_toolbar()

        # ── Panel principal dividido ──
        paned = tb.Panedwindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # ── Panel izquierdo: editor ──
        self._build_editor(paned)

        # ── Panel derecho: resultados ──
        self._build_results(paned)

        # ── Barra de estado inferior ──
        bottom_frame = tb.Frame(self.root)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_bottom = tb.Label(
            bottom_frame,
            text="Listo",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(8, 3),
            bootstyle=SECONDARY,
        )
        self.lbl_bottom.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ── Navegacion de errores ──
        nav_frame = tk.Frame(bottom_frame, relief=tk.SUNKEN, bd=1)
        nav_frame.pack(side=tk.RIGHT, fill=tk.Y)
        # Mismo ancho que lbl_cursor (~44 caracteres Consolas 9)
        nav_frame.configure(width=280)
        nav_frame.pack_propagate(False)

        self.btn_prev_error = tb.Button(
            nav_frame,
            text="◀",
            bootstyle="secondary-outline",
            command=self._prev_error,
            state=tk.DISABLED,
            padding=(4, 2),
        )
        self.btn_prev_error.pack(side=tk.LEFT, padx=(8, 2), pady=2)

        self.lbl_error_count = tb.Label(
            nav_frame,
            text="",
            anchor=tk.CENTER,
            font=("Consolas", 9),
            padding=(4, 0),
        )
        self.lbl_error_count.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=2)

        self.btn_next_error = tb.Button(
            nav_frame,
            text="▶",
            bootstyle="secondary-outline",
            command=self._next_error,
            state=tk.DISABLED,
            padding=(4, 2),
        )
        self.btn_next_error.pack(side=tk.LEFT, padx=(2, 8), pady=2)

        self.lbl_cursor = tb.Label(
            bottom_frame,
            text="Ln 1, Col 1",
            relief=tk.SUNKEN,
            anchor=tk.E,
            padding=(10, 3),
            bootstyle=SECONDARY,
            font=("Consolas", 9),
            width=44,
        )
        self.lbl_cursor.pack(side=tk.RIGHT)

    def _build_toolbar(self) -> None:
        toolbar = tb.Frame(self.root, padding=8)
        toolbar.pack(fill=tk.X)

        # Grupo izquierdo
        self.btn_load = tb.Button(
            toolbar,
            text="Cargar archivo",
            bootstyle=PRIMARY,
            command=self._load_file,
        )
        self.btn_load.pack(side=tk.LEFT, padx=(0, 4))

        # Separador vertical
        tb.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        self.lbl_path = tb.Label(toolbar, text="Ningun archivo cargado")
        self.lbl_path.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        # Grupo derecho
        self.btn_compile = tb.Button(
            toolbar,
            text="Compilar y ejecutar",
            bootstyle=SUCCESS,
            command=self._compile,
        )
        self.btn_compile.pack(side=tk.RIGHT, padx=(4, 0))

        # boton reporte HTML
        self.btn_report = tb.Button(
            toolbar,
            text="Ver reporte HTML",
            bootstyle=INFO,
            command=self._open_report,
            state=tk.DISABLED,
        )
        self.btn_report.pack(side=tk.RIGHT, padx=(4, 0))

        # boton para limpiar
        self.btn_clear = tb.Button(
            toolbar,
            text="Limpiar salida",
            bootstyle=SECONDARY,
            command=self._clear_outputs,
        )
        self.btn_clear.pack(side=tk.RIGHT, padx=(4, 0))

    def _build_editor(self, paned: tb.Panedwindow) -> None:
        left_frame = tb.Labelframe(paned, text="Codigo fuente", padding=0)
        paned.add(left_frame, weight=1)

        editor_container = tb.Frame(left_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)

        # Numeros de linea
        self.txt_lines = tk.Text(
            editor_container,
            width=5,
            padx=6,
            pady=8,
            takefocus=0,
            border=0,
            background=COLORS["line_bg"],
            foreground=COLORS["line_fg"],
            state=tk.DISABLED,
            wrap=tk.NONE,
            font=("Consolas", 12),
            cursor="arrow",
            highlightthickness=0,
        )
        self.txt_lines.pack(side=tk.LEFT, fill=tk.Y)

        # Separador
        sep = tk.Frame(editor_container, width=1, bg="#3c3c3c")
        sep.pack(side=tk.LEFT, fill=tk.Y)

        # Editor
        self.txt_source = tk.Text(
            editor_container,
            wrap=tk.NONE,
            undo=True,
            padx=12,
            pady=8,
            border=0,
            background=COLORS["editor_bg"],
            foreground=COLORS["editor_fg"],
            insertbackground=COLORS["insert"],
            selectbackground=COLORS["select_bg"],
            selectforeground=COLORS["select_fg"],
            font=("Consolas", 12),
            relief=tk.FLAT,
            highlightthickness=0,
            tabs=("36", "72"),
        )
        self.txt_source.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        scroll_y = tb.Scrollbar(
            editor_container, orient=tk.VERTICAL, command=self._scroll_source_y
        )
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x = tb.Scrollbar(
            left_frame, orient=tk.HORIZONTAL, command=self.txt_source.xview
        )
        scroll_x.pack(fill=tk.X)

        self.txt_source.configure(
            yscrollcommand=lambda first, last: self._on_source_scroll(
                first, last, scroll_y
            ),
            xscrollcommand=scroll_x.set,
        )

        # Eventos del editor
        self.txt_source.bind("<KeyRelease>", lambda e: self._on_editor_keyrelease(e))
        self.txt_source.bind(
            "<MouseWheel>", lambda e: self.root.after_idle(self._sync_line_numbers)
        )
        self.txt_source.bind(
            "<ButtonRelease-1>", lambda e: self.root.after_idle(self._on_cursor_move)
        )
        self.txt_source.bind("<<Modified>>", lambda e: self._on_source_changed())
        self.txt_source.bind(
            "<ButtonRelease-3>",
            lambda e: self.root.after_idle(self._update_cursor_info),
        )

    def _build_results(self, paned: tb.Panedwindow) -> None:
        right_frame = tb.Frame(paned, padding=0)
        paned.add(right_frame, weight=2)

        # Status + indicador
        status_row = tb.Frame(right_frame)
        status_row.pack(fill=tk.X, pady=(0, 6))

        tb.Label(status_row, text="Estado:", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.lbl_status_val = tb.Label(
            status_row,
            text="listo",
            font=("Segoe UI", 10, "bold"),
            bootstyle=SECONDARY,
        )
        self.lbl_status_val.pack(side=tk.LEFT, padx=(4, 0))

        # Separador
        tb.Separator(status_row, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=10
        )

        tb.Label(status_row, text="Archivo:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.lbl_status_file = tb.Label(status_row, text="-", font=("Segoe UI", 9))
        self.lbl_status_file.pack(side=tk.LEFT, padx=(4, 0))

        # Notebook
        self.notebook = tb.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.txt_vm = self._create_output_tab("Salida VM")
        self.txt_lex = self._create_output_tab("Tokens (.lex)")
        self.txt_sym = self._create_output_tab("Simbolos (.sym)")
        self.txt_int = self._create_output_tab("Intermedio (.int)")
        self.txt_obj = self._create_output_tab("Objeto (.obj)")
        self.txt_err = self._create_output_tab("Errores (.err)")

    # ── Syntax highlighting ────────────────────────────────────────────

    def _configure_syntax_tags(self) -> None:
        for tag, color in SYNTAX_COLORS.items():
            self.txt_source.tag_configure(tag, foreground=color)

        self.txt_source.tag_configure(
            "current_line", background=COLORS["current_line_bg"]
        )
        # La linea activa va por debajo del syntax highlighting
        self.txt_source.tag_lower("current_line")

        # Error highlighting
        self.txt_source.tag_configure("error_line", background="#5a1d1d")
        self.txt_source.tag_configure(
            "error_column",
            background="#7a2a2a",
            underline=True,
        )
        self.txt_lines.tag_configure("error_gutter", foreground="#f44747")

    def _schedule_highlight(self) -> None:
        if self._highlight_after_id:
            self.root.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.root.after(250, self._highlight_syntax)

    def _highlight_syntax(self) -> None:
        """Aplica syntax highlighting con regex sobre el contenido."""
        self._highlight_after_id = None

        # Limpiar tags anteriores
        for tag in SYNTAX_COLORS:
            self.txt_source.tag_remove(tag, "1.0", tk.END)

        content = self.txt_source.get("1.0", tk.END)

        # Orden de aplicacion: los ultimos tienen prioridad
        # 1. Strings (""), 2. Comentarios (//), 3. Numeros
        # 4. Keywords, 5. Builtins, 6. Booleanos

        self._highlight_pattern(content, r'"[^"]*"', "string")
        self._highlight_pattern(content, r"'[^']*'", "string")
        self._highlight_pattern(content, r"//[^\n]*", "comment")
        self._highlight_pattern(content, r"\b\d+(\.\d+)?\b", "number")
        self._highlight_pattern(
            content,
            r"\b(programa|entero|decimal|cadena|booleano"
            r"|si|entonces|fin|mientras|hacer)\b",
            "keyword",
        )
        self._highlight_pattern(content, r"\b(reporte|alerta)\b", "builtin")
        self._highlight_pattern(content, r"\b(verdadero|falso)\b", "boolean")
        self._highlight_pattern(content, r"[=+\-*/<>!]+", "operator")

    def _highlight_pattern(self, content: str, pattern: str, tag: str) -> None:
        for match in re.finditer(pattern, content):
            start = match.start()
            end = match.end()
            idx_start = f"1.0+{start}c"
            idx_end = f"1.0+{end}c"
            with contextlib.suppress(tk.TclError):
                self.txt_source.tag_add(tag, idx_start, idx_end)

    # ── Linea activa ───────────────────────────────────────────────────

    def _on_editor_keyrelease(self, event: tk.Event) -> None:
        self._schedule_highlight()
        self.root.after_idle(self._update_cursor_info)

    def _on_cursor_move(self) -> None:
        self._highlight_current_line()
        self._sync_line_numbers_status()
        self._update_cursor_info()

    def _highlight_current_line(self) -> None:
        self.txt_source.tag_remove("current_line", "1.0", tk.END)
        cursor = self.txt_source.index(tk.INSERT)
        line = cursor.split(".")[0]
        self.txt_source.tag_add("current_line", f"{line}.0", f"{line}.0 lineend+1c")

    # ── Sync linea activa en numeros ───────────────────────────────────

    def _update_cursor_info(self) -> None:
        """Actualiza la barra inferior con Ln/Col, espacios y seleccion."""
        cursor = self.txt_source.index(tk.INSERT)
        line_str, col_str = cursor.split(".")
        col = int(col_str) + 1

        # Espacios al inicio de la linea actual
        line_text = self.txt_source.get(f"{line_str}.0", f"{line_str}.0 lineend")
        spaces = len(line_text) - len(line_text.lstrip())

        # Longitud de seleccion
        sel_text = ""
        try:
            sel_start = self.txt_source.index(tk.SEL_FIRST)
            sel_end = self.txt_source.index(tk.SEL_LAST)
            sel_len = len(self.txt_source.get(sel_start, sel_end))
            sel_text = f" | Sel: {sel_len}"
        except tk.TclError:
            pass

        self.lbl_cursor.configure(
            text=f"Ln {line_str}, Col {col} | Spaces: {spaces}{sel_text}"
        )

    def _sync_line_numbers_status(self) -> None:
        """Resalta el numero de linea actual en el panel de numeros."""
        cursor = self.txt_source.index(tk.INSERT)
        line = cursor.split(".")[0]

        self.txt_lines.configure(state=tk.NORMAL)

        # Resetear todos los numeros a color normal
        total = int(self.txt_source.index("end-1c").split(".")[0])
        for i in range(1, total + 1):
            self.txt_lines.tag_remove("active", f"{i}.0", f"{i}.0 lineend")

        # Resaltar linea actual
        self.txt_lines.tag_configure("active", foreground=COLORS["line_active_fg"])
        self.txt_lines.tag_add("active", f"{line}.0", f"{line}.0 lineend")

        self.txt_lines.configure(state=tk.DISABLED)

    # ── Estilos extra ──────────────────────────────────────────────────

    def _apply_style_overrides(self) -> None:
        style = tb.Style.get_instance()
        if style:
            style.configure("TPanedwindow", background="#3c3c3c")
            style.configure("TLabelframe", background="#2b2b2b")
            style.configure("TNotebook.Tab", padding=[14, 6])
            style.configure("TButton", padding=(8, 4))

    # ── Helpers de UI ──────────────────────────────────────────────────

    def _create_output_tab(self, title: str) -> scrolledtext.ScrolledText:
        frame = tb.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        self._output_frames.append(frame)
        txt = scrolledtext.ScrolledText(
            frame,
            wrap=tk.NONE,
            state=tk.DISABLED,
            padx=10,
            pady=8,
            border=0,
            background=COLORS["output_bg"],
            foreground=COLORS["output_fg"],
            font=("Consolas", 11),
            insertbackground=COLORS["insert"],
            selectbackground=COLORS["select_bg"],
            selectforeground=COLORS["select_fg"],
            relief=tk.FLAT,
            highlightthickness=0,
        )
        txt.pack(fill=tk.BOTH, expand=True)
        return txt

    @staticmethod
    def _set_text(widget: scrolledtext.ScrolledText, content: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state=tk.DISABLED)

    def _set_status(self, text: str, bootstyle: str = SECONDARY) -> None:
        self.lbl_status_val.configure(text=text, bootstyle=bootstyle)

    def _select_tab(self, index: int) -> None:
        """Selecciona una pestana del notebook por indice."""
        if 0 <= index < len(self._output_frames):
            self.notebook.select(self._output_frames[index])

    # ── Sincronizacion de scroll ───────────────────────────────────────

    def _scroll_source_y(self, *args: str) -> None:
        self.txt_source.yview(*args)
        self.txt_lines.yview(*args)

    def _on_source_scroll(
        self, first: float, last: float, scrollbar: tb.Scrollbar
    ) -> None:
        scrollbar.set(first, last)
        self.txt_lines.yview_moveto(first)  # type: ignore[arg-type]

    def _sync_line_numbers(self) -> None:
        total_lines = int(self.txt_source.index("end-1c").split(".")[0])
        numbers = "\n".join(str(line) for line in range(1, total_lines + 1))

        self.txt_lines.configure(state=tk.NORMAL)
        self.txt_lines.delete("1.0", tk.END)
        self.txt_lines.insert(tk.END, numbers)
        self.txt_lines.configure(state=tk.DISABLED)
        self.txt_lines.yview_moveto(self.txt_source.yview()[0])  # type: ignore[arg-type]

    # ── Eventos ────────────────────────────────────────────────────────

    def _on_source_changed(self) -> None:
        if self.txt_source.edit_modified():
            self.edited_since_load = True
            self.lbl_bottom.configure(
                text="Codigo modificado (se usara archivo temporal al compilar)"
            )
            self._sync_line_numbers()
            self._schedule_highlight()
            self.txt_source.edit_modified(False)

    # ── Carga de archivo ───────────────────────────────────────────────

    def _load_file(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Seleccionar archivo RadarScript",
            filetypes=[
                ("Archivos RadarScript", "*.rdr"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path_str:
            return

        self.source_path = Path(path_str)
        try:
            content = self.source_path.read_text(encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{exc}")
            return

        self.original_source = content
        self.edited_since_load = False

        self.txt_source.delete("1.0", tk.END)
        self.txt_source.insert(tk.END, content)
        self.txt_source.edit_modified(False)
        self._sync_line_numbers()
        self._highlight_syntax()
        self._on_cursor_move()

        self.lbl_path.configure(text=str(self.source_path))
        self.lbl_status_file.configure(text=self.source_path.name)
        self.lbl_bottom.configure(text=f"Archivo cargado: {self.source_path.name}")
        self._clear_editor_errors()
        self._clear_outputs()
        self._set_status("listo", SECONDARY)

    # ── Navegacion de errores ───────────────────────────────────────

    def _setup_error_nav(self) -> None:
        """Activa la navegacion de errores con los errores actuales."""
        count = len(self._compile_errors)
        if count == 0:
            self._reset_error_nav()
            return
        self._current_error_idx = 0
        self.btn_prev_error.configure(state=tk.DISABLED if count <= 1 else tk.NORMAL)
        self.btn_next_error.configure(state=tk.DISABLED if count <= 1 else tk.NORMAL)
        self._update_error_count_label()

    def _reset_error_nav(self) -> None:
        """Desactiva la navegacion de errores."""
        self._current_error_idx = -1
        self.btn_prev_error.configure(state=tk.DISABLED)
        self.btn_next_error.configure(state=tk.DISABLED)
        self.lbl_error_count.configure(text="")

    def _update_error_count_label(self) -> None:
        total = len(self._compile_errors)
        if total == 0 or self._current_error_idx < 0:
            self.lbl_error_count.configure(text="")
            return
        current = self._current_error_idx + 1
        self.lbl_error_count.configure(
            text=f"Error {current} de {total}",
        )

    def _next_error(self) -> None:
        if not self._compile_errors:
            return
        total = len(self._compile_errors)
        self._current_error_idx = (self._current_error_idx + 1) % total
        self._update_error_count_label()
        self._highlight_current_error()

    def _prev_error(self) -> None:
        if not self._compile_errors:
            return
        total = len(self._compile_errors)
        self._current_error_idx = (self._current_error_idx - 1) % total
        self._update_error_count_label()
        self._highlight_current_error()

    def _highlight_current_error(self) -> None:
        """Resalta SOLO el error actual en el editor, uno a la vez."""
        self._clear_editor_errors()

        if self._current_error_idx < 0 or not self._compile_errors:
            return

        err = self._compile_errors[self._current_error_idx]
        if err.line is None or err.column is None:
            return

        line = err.line
        col = err.column

        # Marcar linea completa en el editor
        self.txt_source.tag_add("error_line", f"{line}.0", f"{line}.0 lineend+1c")

        # Marcar columna exacta (interseccion x,y)
        self.txt_source.tag_add("error_column", f"{line}.{col - 1}", f"{line}.{col}")

        # Marcar numero de linea en rojo
        self.txt_lines.tag_add("error_gutter", f"{line}.0", f"{line}.0 lineend")

        # Scroll para que la linea sea visible
        self.txt_source.see(f"{line}.0")

    def _clear_editor_errors(self) -> None:
        """Limpia marcas de error del editor."""
        self.txt_source.tag_remove("error_line", "1.0", tk.END)
        self.txt_source.tag_remove("error_column", "1.0", tk.END)
        self.txt_lines.tag_remove("error_gutter", "1.0", tk.END)

    def _clear_outputs(self) -> None:
        for txt in (
            self.txt_vm,
            self.txt_lex,
            self.txt_sym,
            self.txt_int,
            self.txt_obj,
            self.txt_err,
        ):
            self._set_text(txt, "")
        self.btn_report.configure(state=tk.DISABLED)
        self._last_report_path = None

    def _open_report(self) -> None:
        """Abre el ultimo reporte HTML generado en el navegador."""
        if self._last_report_path and self._last_report_path.exists():
            open_report(self._last_report_path)
            self.lbl_bottom.configure(
                text=f"Reporte abierto: {self._last_report_path.name}"
            )

    # ── Compilacion ────────────────────────────────────────────────────

    def _compile(self) -> None:
        if self.source_path is None:
            messagebox.showwarning("Atencion", "Primero carga un archivo .rdr")
            return

        current_source = self.txt_source.get("1.0", tk.END)
        if current_source.endswith("\n"):
            current_source = current_source[:-1]

        self._set_status("compilando...", INFO)
        self.lbl_bottom.configure(text="Compilando...")
        self.root.update_idletasks()

        if not self.edited_since_load:
            compile_path = self.source_path
            base_name = self.source_path.stem
            self.lbl_bottom.configure(text=f"Compilando: {self.source_path.name}")
        else:
            self.output_dir.mkdir(exist_ok=True)
            compile_path = self.output_dir / "gui_temp.rdr"
            compile_path.write_text(current_source + "\n", encoding="utf-8")
            base_name = compile_path.stem
            self.lbl_bottom.configure(
                text="Compilando desde archivo temporal (codigo editado)"
            )

        result = self.compiler.compile(compile_path)

        # Guardar errores estructurados para navegacion
        self._compile_errors = result.errors.copy() if result.errors else []
        self._current_error_idx = -1

        if result.success:
            self._set_status("exito", SUCCESS)
            self._set_text(self.txt_vm, "\n".join(result.vm_output))
            self._select_tab(0)
            self._reset_error_nav()
        else:
            self._set_status("error", DANGER)
            # Mostrar todos los errores en la pestania de errores
            error_display = "\n".join(err.display() for err in result.errors)
            self._set_text(self.txt_err, error_display)
            self._select_tab(5)
            self._setup_error_nav()
            self._highlight_current_error()

        self._load_output(f"{base_name}.lex", self.txt_lex)
        self._load_output(f"{base_name}.sym", self.txt_sym)
        self._load_output(f"{base_name}.int", self.txt_int)
        self._load_output(f"{base_name}.obj", self.txt_obj)
        if result.success:
            self._load_output(f"{base_name}.err", self.txt_err)

        # Generar reporte HTML
        self._last_report_path = self.output_dir / f"{base_name}_report.html"
        report_data = ReportData(
            source_code=current_source,
            vm_output=result.vm_output,
            errors=[err.display() for err in result.errors],
            success=result.success,
            lex_content=self.txt_lex.get("1.0", tk.END).strip(),
            sym_content=self.txt_sym.get("1.0", tk.END).strip(),
            int_content=self.txt_int.get("1.0", tk.END).strip(),
            obj_content=self.txt_obj.get("1.0", tk.END).strip(),
            err_content=self.txt_err.get("1.0", tk.END).strip(),
            filename=base_name,
        )
        generate_report(report_data, self._last_report_path)
        self.btn_report.configure(state=tk.NORMAL)

        if result.success:
            self._clear_editor_errors()

        self.lbl_bottom.configure(text="Compilacion finalizada")

    def _load_output(self, filename: str, widget: scrolledtext.ScrolledText) -> None:
        path = self.output_dir / filename
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                content = "[Error al leer el archivo]"
        else:
            content = "[Archivo no generado]"
        self._set_text(widget, content)


def main() -> None:
    # Si se pasa un archivo .obj como argumento, abrir el dashboard de la MV
    if len(sys.argv) == 2:
        arg_path = Path(sys.argv[1])
        if arg_path.suffix.lower() == ".obj" and arg_path.exists():
            app = ObjRunnerDashboard(arg_path)
            app.run()
            return

    # Caso normal: abrir el editor del compilador
    root = tb.Window(themename="darkly")
    _ = RadarGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
