from pathlib import Path
import sys

from src.compiler import RadarCompiler


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python main.py <archivo.rdr>")
        return 1

    source_path = Path(sys.argv[1])
    compiler = RadarCompiler(output_dir=Path("output"))
    result = compiler.compile(source_path)

    if result.success:
        print("Compilación exitosa.")
        if result.vm_output:
            print("\nSalida de la máquina virtual:")
            for line in result.vm_output:
                print(line)
        return 0

    print("Compilación fallida.")
    for error in result.errors:
        print(error.display())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
