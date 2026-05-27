class ObjectCodeGenerator:
    _OP_MAP = {
        "+": "ADD",
        "-": "SUB",
        "*": "MUL",
        "/": "DIV",
        "CONCAT": "CONCAT",
        ">": "GT",
        "<": "LT",
        "==": "EQ",
        ">=": "GE",
        "<=": "LE",
        "!=": "NE",
    }

    def generate(self, intermediate_code: list[tuple[str, str, str, str]]) -> list[str]:
        instructions: list[str] = []
        for op, arg1, arg2, result in intermediate_code:
            if op == "=":
                instructions.append(f"MOV {result}, {arg1}")
            elif op == "REPORTE":
                instructions.append(f"LOAD {arg1}")
                instructions.append("REPORTE")
            elif op == "ALERTA":
                instructions.append(f"LOAD {arg1}")
                instructions.append("ALERTA")
            elif op == "JF":
                instructions.append(f"LOAD {arg1}")
                instructions.append(f"JMPF {result}")
            elif op == "JMP":
                instructions.append(f"JMP {result}")
            elif op == "LABEL":
                instructions.append(f"{result}:")
            elif op in self._OP_MAP:
                instructions.append(f"LOAD {arg1}")
                instructions.append(f"LOAD {arg2}")
                instructions.append(self._OP_MAP[op])
                instructions.append(f"STORE {result}")
            else:
                raise ValueError(f"operación intermedia no soportada: {op}")
        instructions.append("HALT")
        return instructions
