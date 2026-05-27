#!/usr/bin/env python3
"""Ejecutor independiente de archivos .obj de RadarScript.

Uso:
    python run_obj.py <archivo.obj>

Asociación en Windows (doble clic):
    Ejecutar como administrador el archivo 'asociar_obj.bat'
    incluido en este mismo directorio.
"""

import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext, ttk

import ttkbootstrap as tb
from ttkbootstrap.constants import DANGER, INFO, SECONDARY, SUCCESS

from src.vm import VirtualMachine


# ── Paleta ──────────────────────────────────────────────────────────────
COLORS = {
    "bg_dark": "#1e1e1e",
    "bg_card": "#252526",
    "bg_header": "#2d2d2d",
    "fg": "#d4d4d4",
    "fg_muted": "#858585",
    "fg_success": "#4ec9b0",
    "fg_error": "#f44747",
    "border": "#3c3c3c",
    "accent": "#007acc",
}


class ObjRunnerDashboard:
    """Ventana dashboard que ejecuta y muestra el resultado de un .obj."""

    def __init__(self, obj_path: Path) -> None:
        self.obj_path = obj_path
        self.root = tb.Window(themename="darkly")
        self.root.title(f"RadarScript VM — {obj_path.name}")
        self.root.geometry("780x620")
        self.root.minsize(600, 450)
        self.root.iconbitmap(default="")  # sin icono personalizado

        # Centro en pantalla
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (780 // 2)
        y = (self.root.winfo_screenheight() // 2) - (620 // 2)
        self.root.geometry(f"+{x}+{y}")

        # ── Variables de estado ──────────────────────────────────────
        self.success = False
        self.output_lines: list[str] = []
        self.errors: list[str] = []
        self.instructions_count = 0
        self.elapsed_ms = 0

        # ── UI ───────────────────────────────────────────────────────
        self._build_ui()
        self._execute_and_show()

    # ── Construcción de UI ───────────────────────────────────────────

    def _build_ui(self) -> None:
        # Fondo global
        self.root.configure(background=COLORS["bg_dark"])

        # ── Frame principal con padding ────────────────────────────
        main = tb.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Header ─────────────────────────────────────────────────
        header = tb.Frame(main, bootstyle="dark")
        header.pack(fill=tk.X, pady=(0, 16))

        # ícono + filename
        self.lbl_icon = tb.Label(
            header,
            text="📡",
            font=("Segoe UI", 20),
            bootstyle="inverse-dark",
        )
        self.lbl_icon.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_filename = tb.Label(
            header,
            text=self.obj_path.name,
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-dark",
        )
        self.lbl_filename.pack(side=tk.LEFT)

        # status badge
        self.lbl_status = tb.Label(
            header,
            text="⏳ Ejecutando…",
            font=("Segoe UI", 11, "bold"),
            bootstyle="inverse-info",
            padding=(12, 4),
        )
        self.lbl_status.pack(side=tk.RIGHT)

        # ── Tarjeta de resumen ─────────────────────────────────────
        summary_frame = ttk.LabelFrame(
            main,
            text="Resumen de ejecución",
            padding=12,
        )
        summary_frame.pack(fill=tk.X, pady=(0, 12))

        self.summary_grid = tb.Frame(summary_frame)
        self.summary_grid.pack(fill=tk.X)

        self._summary_item(self.summary_grid, "Archivo", self.obj_path.name, 0)
        self._summary_item(self.summary_grid, "Instrucciones", "—", 1)
        self._summary_item(self.summary_grid, "Tiempo", "—", 2)
        self._summary_item(self.summary_grid, "Estado", "—", 3)

        # ── Área de salida ─────────────────────────────────────────
        output_frame = ttk.LabelFrame(
            main,
            text="Salida de la máquina virtual",
            padding=8,
        )
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        self.txt_output = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            background=COLORS["bg_card"],
            foreground=COLORS["fg"],
            insertbackground=COLORS["fg"],
            font=("Consolas", 13),
            relief=tk.FLAT,
            borderwidth=0,
            padx=12,
            pady=10,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.txt_output.pack(fill=tk.BOTH, expand=True)

        # tags para colorear salida
        self.txt_output.tag_configure("success", foreground=COLORS["fg_success"])
        self.txt_output.tag_configure("error", foreground=COLORS["fg_error"])
        self.txt_output.tag_configure("muted", foreground=COLORS["fg_muted"])
        self.txt_output.tag_configure(
            "header_line", foreground=COLORS["accent"], font=("Consolas", 13, "bold")
        )

        # ── Footer ─────────────────────────────────────────────────
        footer = tb.Frame(main)
        footer.pack(fill=tk.X)

        self.btn_rerun = tb.Button(
            footer,
            text="🔄 Ejecutar de nuevo",
            bootstyle="secondary-outline",
            command=self._rerun,
        )
        self.btn_rerun.pack(side=tk.LEFT)

        self.btn_close = tb.Button(
            footer,
            text="Cerrar",
            bootstyle="danger-outline",
            command=self.root.destroy,
        )
        self.btn_close.pack(side=tk.RIGHT)

    def _summary_item(self, parent: tb.Frame, label: str, value: str, col: int) -> None:
        """Agrega un item a la grilla de resumen."""
        lbl = tb.Label(
            parent,
            text=label,
            font=("Segoe UI", 9),
            bootstyle="secondary",
        )
        lbl.grid(row=0, column=col * 2, sticky="w", padx=(0, 4))

        val = tb.Label(
            parent,
            text=value,
            font=("Segoe UI", 10, "bold"),
            bootstyle="inverse-dark",
        )
        val.grid(row=1, column=col * 2, sticky="w", padx=(0, 24))

        # guardar referencia para actualizar después
        setattr(self, f"_summary_val_{col}", val)

    def _set_summary(self, col: int, value: str) -> None:
        attr = f"_summary_val_{col}"
        if hasattr(self, attr):
            getattr(self, attr).configure(text=value)

    # ── Ejecución ───────────────────────────────────────────────────

    def _execute_and_show(self) -> None:
        """Lee el .obj, lo ejecuta y muestra los resultados."""
        try:
            code = self.obj_path.read_text(encoding="utf-8")
        except Exception as e:
            self._show_error(f"No se pudo leer el archivo:\n{e}")
            return

        instructions = [
            line.strip()
            for line in code.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.instructions_count = len(instructions)

        start = time.perf_counter()
        try:
            vm = VirtualMachine()
            self.output_lines = vm.execute(instructions)
            self.elapsed_ms = (time.perf_counter() - start) * 1000
            self.success = True
        except Exception as e:
            self.elapsed_ms = (time.perf_counter() - start) * 1000
            self.success = False
            self.errors = [str(e)]

        self._render_results()

    def _rerun(self) -> None:
        self._reset_ui()
        self.root.update_idletasks()
        self._execute_and_show()

    def _reset_ui(self) -> None:
        self.txt_output.configure(state=tk.NORMAL)
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.configure(state=tk.DISABLED)
        self.lbl_status.configure(
            text="⏳ Ejecutando…",
            bootstyle="inverse-info",
        )
        self._set_summary(1, "—")
        self._set_summary(2, "—")
        self._set_summary(3, "—")

    # ── Render ──────────────────────────────────────────────────────

    def _render_results(self) -> None:
        # Header: status
        if self.success:
            self.lbl_status.configure(
                text="✅ Ejecución exitosa",
                bootstyle="inverse-success",
            )
        else:
            self.lbl_status.configure(
                text="❌ Error en ejecución",
                bootstyle="inverse-danger",
            )

        # Summary
        self._set_summary(1, f"{self.instructions_count} instrucciones")
        self._set_summary(
            2,
            f"{self.elapsed_ms:.1f} ms"
            if self.elapsed_ms < 1000
            else f"{self.elapsed_ms / 1000:.2f} s",
        )
        self._set_summary(3, "✅ Éxito" if self.success else "❌ Error")

        # Output area
        self.txt_output.configure(state=tk.NORMAL)
        self.txt_output.delete("1.0", tk.END)

        if self.success and self.output_lines:
            # Encabezado de salida
            self.txt_output.insert(
                tk.END, "═══ RESULTADO DE EJECUCIÓN ═══\n", "header_line"
            )
            self.txt_output.insert(tk.END, "\n")

            for line in self.output_lines:
                if line.startswith("ALERTA"):
                    self.txt_output.insert(tk.END, f"{line}\n", "error")
                elif line.startswith("REPORTE"):
                    self.txt_output.insert(tk.END, f"{line}\n", "success")
                else:
                    self.txt_output.insert(tk.END, f"{line}\n")

            self.txt_output.insert(tk.END, "\n")
            self.txt_output.insert(tk.END, "═══ FIN DE LA EJECUCIÓN ═══\n", "muted")

        elif self.success and not self.output_lines:
            self.txt_output.insert(
                tk.END, "✅ Programa ejecutado sin errores.\n", "success"
            )
            self.txt_output.insert(
                tk.END, "No generó salida (REPORTE/ALERTA).\n", "muted"
            )

        else:
            self.txt_output.insert(
                tk.END, "⛔ ERROR DURANTE LA EJECUCIÓN\n", "header_line"
            )
            self.txt_output.insert(tk.END, "\n")
            for err in self.errors:
                self.txt_output.insert(tk.END, f"  {err}\n", "error")

        self.txt_output.configure(state=tk.DISABLED)

    def _show_error(self, message: str) -> None:
        self.success = False
        self.errors = [message]
        self._render_results()

    def run(self) -> None:
        self.root.mainloop()


# ── Entry point ─────────────────────────────────────────────────────────


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python run_obj.py <archivo.obj>")
        print("  Ejecuta un archivo .obj de RadarScript en la MV.")
        return 1

    obj_path = Path(sys.argv[1])
    if not obj_path.exists():
        print(f"Error: no se encontró el archivo '{obj_path}'")
        return 1
    if obj_path.suffix.lower() != ".obj":
        print("Advertencia: el archivo no termina en .obj, pero se intentará ejecutar.")

    app = ObjRunnerDashboard(obj_path)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
