"""Generador de reportes HTML profesionales para la compilacion RadarScript."""

import re
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ReportData:
    source_code: str
    vm_output: list[str]
    errors: list[str]
    success: bool
    lex_content: str
    sym_content: str
    int_content: str
    obj_content: str
    err_content: str
    filename: str = ""


def generate_report(data: ReportData, output_path: Path) -> Path:
    """Genera un reporte HTML profesional y devuelve la ruta."""
    now = datetime.now().strftime("%d/%m/%Y a las %H:%M")
    status_color = "#4ec9b0" if data.success else "#f44747"
    status_text = "COMPILACION EXITOSA" if data.success else "ERROR DE COMPILACION"
    status_icon = "&#10004;" if data.success else "&#10006;"

    n_lines = len(data.source_code.split("\n"))
    n_tokens = len(data.lex_content.split("\n")) if data.lex_content.strip() else 0
    n_errors = len(data.errors)

    vm_text = "\n".join(data.vm_output) if data.vm_output else "(sin salida)"
    source_lines = data.source_code.split("\n")

    # Extraer lineas con error del .err
    error_lines = _parse_error_lines(data.err_content)

    # Iconos SVG inline
    icon_code = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>"""
    icon_error = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RadarScript — Reporte de Compilacion</title>
<style>
  *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0d1117;
    color: #d4d4d4;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
  }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
  ::-webkit-scrollbar-track {{ background: #161b22; }}
  ::-webkit-scrollbar-thumb {{ background: #30363d; border-radius: 4px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: #484f58; }}

  /* ── Header ── */
  .header {{
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1c2128 100%);
    border-bottom: 1px solid #30363d;
    padding: 32px 40px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
  }}
  .header-left {{ display: flex; align-items: center; gap: 18px; }}
  .logo {{
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #4ec9b0, #2d9d8a);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 800; color: #fff;
    box-shadow: 0 4px 12px rgba(78, 201, 176, 0.3);
  }}
  .header h1 {{ font-size: 24px; font-weight: 700; color: #e6edf3; }}
  .header .subtitle {{ font-size: 13px; color: #8b949e; margin-top: 3px; }}
  .header .subtitle span {{ color: #58a6ff; }}
  .badge-main {{
    display: inline-flex; align-items: center; gap: 10px;
    padding: 10px 24px; border-radius: 8px;
    font-weight: 700; font-size: 14px; letter-spacing: .5px;
    background: {status_color}14;
    color: {status_color};
    border: 1px solid {status_color}33;
    box-shadow: 0 2px 8px {status_color}11;
  }}

  /* ── Container ── */
  .container {{ max-width: 1140px; margin: 0 auto; padding: 28px 24px 60px; }}

  /* ── Summary grid ── */
  .summary-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px; margin-bottom: 32px;
  }}
  .summary-card {{
    background: #161b22; border-radius: 10px;
    padding: 20px 16px; text-align: center;
    border: 1px solid #30363d;
    transition: border-color .2s, transform .15s;
  }}
  .summary-card:hover {{
    border-color: #484f58; transform: translateY(-2px);
  }}
  .summary-card .icon {{ font-size: 20px; margin-bottom: 6px; }}
  .summary-card .value {{
    font-size: 28px; font-weight: 700; color: #e6edf3;
  }}
  .summary-card .label {{
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    color: #8b949e; margin-top: 6px;
  }}

  /* ── Error summary ── */
  .error-summary {{
    background: #1c1010; border: 1px solid #f4474744;
    border-radius: 10px; padding: 20px 24px; margin-bottom: 24px;
  }}
  .error-summary h3 {{
    color: #f44747; font-size: 15px; font-weight: 600;
    display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
  }}
  .error-summary ul {{ list-style: none; padding: 0; }}
  .error-summary li {{
    padding: 8px 12px; margin-bottom: 6px;
    background: #2d1515; border-radius: 6px;
    font-family: 'Consolas', monospace; font-size: 13px;
    border-left: 3px solid #f44747;
  }}
  .error-summary li .line-col {{
    color: #ff8a8a; font-weight: 600; margin-right: 8px;
  }}

  /* ── Section cards ── */
  .section {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    margin-bottom: 20px;
    overflow: hidden;
    transition: border-color .2s;
  }}
  .section:hover {{ border-color: #484f58; }}
  .section-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 20px;
    background: #1c2128;
    border-bottom: 1px solid #30363d;
    cursor: pointer;
    user-select: none;
    transition: background .15s;
  }}
  .section-header:hover {{ background: #21262d; }}
  .section-header h2 {{
    font-size: 14px; font-weight: 600; color: #e6edf3;
    display: flex; align-items: center; gap: 10px;
  }}
  .section-header h2 svg {{ color: #8b949e; }}
  .section-header .arrow {{
    color: #8b949e; font-size: 12px; transition: transform .2s;
  }}
  .section-body {{ padding: 0; display: none; }}
  .section-body.open {{ display: block; }}
  .section-header.active .arrow {{ transform: rotate(180deg); }}

  /* ── Source code ── */
  .source-box {{
    font-family: 'Consolas', 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 13px; line-height: 1.6; background: #0d1117;
    overflow-x: auto; border-radius: 0 0 10px 10px;
  }}
  .source-line {{
    display: flex; align-items: stretch;
    min-height: 24px; border-left: 3px solid transparent;
    transition: background .1s;
  }}
  .source-line:hover {{ background: #161b22; }}
  .source-line.error-line {{
    background: #2d1515; border-left-color: #f44747;
  }}
  .source-num {{
    width: 54px; min-width: 54px;
    padding: 0 14px 0 18px;
    color: #484f58; text-align: right; user-select: none;
    border-right: 1px solid #21262d;
    background: #0d1117;
  }}
  .source-line.error-line .source-num {{
    color: #f44747; background: #1c1010;
  }}
  .source-code {{
    padding: 0 18px; white-space: pre; tab-size: 4;
  }}

  /* ── Syntax colors (inline) ── */
  .kw  {{ color: #569cd6; }}  .bl  {{ color: #569cd6; }}
  .fn  {{ color: #dcdcaa; }}  .str {{ color: #ce9178; }}
  .cm  {{ color: #6a9955; }}  .num {{ color: #b5cea8; }}

  /* ── VM Output ── */
  .vm-block {{ background: #0d1117; padding: 16px 20px; }}
  .vm-line {{ padding: 2px 0; font-family: 'Consolas', monospace; font-size: 13px; }}
  .vm-success {{ color: #4ec9b0; }}
  .vm-error {{ color: #f44747; }}
  .vm-header {{ color: #8b949e; font-size: 11px; text-transform: uppercase;
               letter-spacing: 1px; margin-bottom: 8px; }}

  /* ── Code pre blocks (details) ── */
  .code-block {{
    padding: 16px 20px; font-family: 'Consolas', monospace; font-size: 13px;
    line-height: 1.6; overflow-x: auto; white-space: pre; tab-size: 4;
    background: #0d1117; color: #d4d4d4;
    border-radius: 0 0 10px 10px;
  }}

  /* ── Footer ── */
  .footer {{
    text-align: center; padding: 28px; color: #484f58;
    font-size: 12px; border-top: 1px solid #21262d;
    margin-top: 8px;
  }}

  /* ── Responsive ── */
  @media (max-width: 640px) {{
    .header {{ flex-direction: column; align-items: flex-start; padding: 20px; }}
    .container {{ padding: 16px; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="logo">R</div>
    <div>
      <h1>Reporte de Compilacion</h1>
      <div class="subtitle">
        RadarScript &mdash; <span>{data.filename or "sin nombre"}</span>
      </div>
    </div>
  </div>
  <div class="badge-main">{status_icon} {status_text}</div>
</div>

<div class="container">

  <!-- Summary -->
  <div class="summary-grid">
    <div class="summary-card">
      <div class="icon">&#128221;</div>
      <div class="value">{n_lines}</div>
      <div class="label">Lineas de codigo</div>
    </div>
    <div class="summary-card">
      <div class="icon">&#128214;</div>
      <div class="value">{n_tokens}</div>
      <div class="label">Tokens</div>
    </div>
    <div class="summary-card">
      <div class="icon">&#128200;</div>
      <div class="value">{len(data.vm_output)}</div>
      <div class="label">Salidas generadas</div>
    </div>
    <div class="summary-card">
      <div class="icon">{"&#9989;" if data.success else "&#10060;"}</div>
      <div class="value" style="color:{status_color}">{n_errors}</div>
      <div class="label">{"Errores" if not data.success else "Sin errores"}</div>
    </div>
  </div>

  <!-- Error block (solo si hay errores) -->
  {_build_error_block(data.err_content, error_lines) if not data.success else ""}

  <!-- VM Output -->
  <div class="section">
    <div class="section-header active" onclick="toggle(this)">
      <h2>{icon_code} Salida de la Maquina Virtual</h2>
      <span class="arrow">&#9660;</span>
    </div>
    <div class="section-body open">
      <div class="vm-block">
        {_render_vm_output(vm_text)}
      </div>
    </div>
  </div>

  <!-- Source Code -->
  <div class="section">
    <div class="section-header active" onclick="toggle(this)">
      <h2>{icon_code} Codigo Fuente</h2>
      <span class="arrow">&#9660;</span>
    </div>
    <div class="section-body open">
      <div class="source-box">
        {_render_source(source_lines, error_lines)}
      </div>
    </div>
  </div>
"""

    # Collapsible detail sections
    details = [
        ("Tokens (.lex)", data.lex_content),
        ("Tabla de Simbolos (.sym)", data.sym_content),
        ("Codigo Intermedio (.int)", data.int_content),
        ("Codigo Objeto (.obj)", data.obj_content),
        ("Errores (.err)", data.err_content),
    ]

    for title, content in details:
        display_content = content.strip() or "(vacio)"
        html += f"""
  <div class="section">
    <div class="section-header" onclick="toggle(this)">
      <h2>{icon_error if title == "Errores (.err)" and not data.success else icon_code} {title}</h2>
      <span class="arrow">&#9660;</span>
    </div>
    <div class="section-body">
      <div class="code-block">{_escape(display_content)}</div>
    </div>
  </div>
"""

    html += f"""
</div>

<div class="footer">
  RadarScript Compilador &mdash; Generado el {now}
</div>

<script>
function toggle(header) {{
  header.classList.toggle('active');
  const body = header.nextElementSibling;
  body.classList.toggle('open');
}}
</script>

</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    return output_path


def open_report(path: Path) -> None:
    """Abre el reporte HTML en el navegador predeterminado."""
    webbrowser.open(path.absolute().as_uri())


# ── Helpers ────────────────────────────────────────────────────────────


def _escape(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.replace("\t", "    ")


def _parse_error_lines(err_content: str) -> set[int]:
    """Extrae numeros de linea con error del contenido .err."""
    lines: set[int] = set()
    for m in re.finditer(r"\[l\s*ínea (\d+), columna (\d+)\]", err_content):
        lines.add(int(m.group(1)))
    return lines


def _build_error_summary(err_content: str) -> str:
    """Convierte el .err en una lista HTML de errores con linea/columna."""
    parts = []
    for line in err_content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Extraer [línea N, columna M] del mensaje
        m = re.match(r"^(.*?)\[l\s*ínea (\d+), columna (\d+)\](.*)$", line)
        if m:
            parts.append(
                f'<li><span class="line-col">[L:{m.group(2)} C:{m.group(3)}]</span>'
                f"{_escape(m.group(1).strip())}{_escape(m.group(4).strip())}</li>"
            )
        else:
            parts.append(f"<li>{_escape(line)}</li>")
    return "\n".join(parts)


def _build_error_block(err_content: str, error_lines: set[int]) -> str:
    """Bloque destacado de errores."""
    summary = _build_error_summary(err_content)
    n_err = len(error_lines)
    return f"""
  <div class="error-summary">
    <h3>&#10006; Se encontraron {n_err} error{"es" if n_err != 1 else ""}</h3>
    <ul>
      {summary}
    </ul>
  </div>
"""


def _render_vm_output(text: str) -> str:
    """Renderiza la salida de la VM con colores."""
    lines = text.split("\n")
    result = []
    for line in lines:
        escaped = _escape(line)
        if line.startswith("ALERTA:"):
            result.append(f'<div class="vm-line vm-error">{escaped}</div>')
        elif line.startswith("REPORTE:"):
            result.append(f'<div class="vm-line vm-success">{escaped}</div>')
        else:
            result.append(f'<div class="vm-line">{escaped}</div>')
    return "".join(result)


def _render_source(lines: list[str], error_lines: set[int]) -> str:
    """Renderiza el codigo fuente con numeracion y errores resaltados."""
    result = []
    for i, line in enumerate(lines, 1):
        cls = "error-line" if i in error_lines else ""
        highlighted = _highlight_line(line)
        result.append(
            f'        <div class="source-line {cls}">'
            f'<span class="source-num">{i}</span>'
            f'<span class="source-code">{highlighted}</span>'
            f"</div>\n"
        )
    return "".join(result)


def _highlight_line(line: str) -> str:
    """Aplica colores syntax a una linea de codigo RadarScript.
    Colecta todas las coincidencias sobre el texto CRUDO, resuelve
    superposiciones (comentarios > strings > keywords) y construye
    el HTML final escapando solo el texto no marcado."""
    patterns: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"//.*"), "cm"),
        (re.compile(r'"(?:[^"]*)"'), "str"),
        (re.compile(r"\b(reporte|alerta)\b"), "fn"),
        (re.compile(r"\b(verdadero|falso)\b"), "bl"),
        (
            re.compile(
                r"\b(programa|entero|decimal|cadena|booleano"
                r"|si|entonces|fin|mientras|hacer)\b"
            ),
            "kw",
        ),
        (re.compile(r"\b(\d+(?:\.\d+)?)\b"), "num"),
    ]

    raw_matches: list[tuple[int, int, str]] = []
    for pat, cls in patterns:
        for m in pat.finditer(line):
            raw_matches.append((m.start(), m.end(), cls))

    raw_matches.sort(key=lambda x: x[0])

    clean_matches: list[tuple[int, int, str]] = []
    last_end = 0
    for start, end, cls in raw_matches:
        if start < last_end:
            continue
        clean_matches.append((start, end, cls))
        last_end = end

    result: list[str] = []
    pos = 0
    for start, end, cls in clean_matches:
        if start > pos:
            result.append(_escape(line[pos:start]))
        result.append(f'<span class="{cls}">{_escape(line[start:end])}</span>')
        pos = end

    if pos < len(line):
        result.append(_escape(line[pos:]))

    return "".join(result)
