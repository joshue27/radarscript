# RadarScript — Compilador Educativo

RadarScript es un compilador didactico para un lenguaje imperativo de dominio especifico, inspirado en escenarios de monitoreo y alertas. Esta implementado en Python puro, sin dependencias externas, y sigue el pipeline clasico de compilacion: analisis lexico, sintactico, semantico, generacion de codigo intermedio, codigo objeto y ejecucion en una maquina virtual basada en pila.

## Caracteristicas del lenguaje

- Tipos de dato: `entero`, `decimal`, `cadena`, `booleano`.
- Declaraciones, asignaciones y expresiones aritmeticas con precedencia.
- Concatenacion de cadenas con `+`.
- Comparaciones: `>`, `<`, `==`, `>=`, `<=`, `!=`.
- Estructuras de control: `si ... entonces ... fin` y `mientras ... hacer ... fin`.
- Funciones integradas: `reporte(...)` y `alerta(...)`.
- Comentarios de linea con `//`.

## Ejecutar el compilador

### Consola

```bash
python main.py <archivo.rdr>
```

Ejemplo:

```bash
python main.py examples/monitoreo_clima.rdr
```

### Interfaz grafica

```bash
python gui.py
```

La GUI permite cargar un archivo `.rdr`, editarlo, compilar y visualizar los archivos intermedios en pestanas.

## Archivos generados

Tras compilar, la carpeta `output/` contiene:

- `.lex` — tokens reconocidos
- `.sym` — tabla de simbolos
- `.int` — codigo intermedio en cuadruplas
- `.obj` — codigo objeto para la VM
- `.err` — mensaje de error o "Sin errores."

## Estructura del proyecto

```
CompiladorRadar/
├── main.py                  # Punto de entrada (consola)
├── gui.py                   # Interfaz grafica (tkinter)
├── src/
│   ├── compiler.py          # Orquestador de fases
│   ├── lexer.py             # Analizador lexico
│   ├── parser.py            # Analizador sintactico (descendente recursivo)
│   ├── semantic.py          # Analizador semantico
│   ├── intermediate.py      # Generador de codigo intermedio
│   ├── object_code.py       # Generador de codigo objeto
│   ├── vm.py                # Maquina virtual basada en pila
│   ├── ast_nodes.py         # Nodos del AST
│   ├── tokens.py            # Definicion de tokens
│   ├── symbol_table.py      # Tabla de simbolos
│   └── errors.py            # Jerarquia de errores
├── examples/
│   ├── monitoreo_clima.rdr
│   ├── prueba_minima.rdr
│   ├── prueba_expresiones.rdr
│   ├── prueba_condicional.rdr
│   ├── prueba_mientras.rdr
│   └── errores/             # Ejemplos de errores lexicos, sintacticos y semanticos
├── docs/
│   ├── gramatica.md         # Gramatica completa, tokens y reglas de tipos
│   ├── manual_usuario.md    # Guia de uso, ejemplos validos y de error
│   └── manual_tecnico.md    # Arquitectura, modulos y VM
└── output/                  # Archivos generados por compilacion
```

## Documentacion

- `docs/gramatica.md` — gramatica formal BNF, palabras reservadas, tokens y reglas de tipos.
- `docs/manual_usuario.md` — como ejecutar, archivos generados y ejemplos.
- `docs/manual_tecnico.md` — arquitectura por fases, responsabilidades de modulos e instrucciones de la VM.

## Ejemplo basico

```radar
programa monitoreo_clima;

entero distancia;
decimal viento;
cadena zona;
booleano alerta_activa;

distancia = 120;
viento = 85.5;
zona = "NORTE";
alerta_activa = verdadero;

si viento > 70 entonces
    alerta("Tormenta detectada en " + zona);
fin

mientras distancia > 0 hacer
    distancia = distancia - 30;
fin

reporte("Proceso finalizado");
```

## Licencia

Proyecto academico para la materia Compiladores.
