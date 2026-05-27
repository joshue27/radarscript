from src.errors import RuntimeRadarError


class VirtualMachine:
    def __init__(self):
        self.memory: dict[str, object] = {}
        self.stack: list[object] = []
        self.output: list[str] = []

    def execute(self, instructions: list[str]) -> list[str]:
        label_map = {}
        for i, instruction in enumerate(instructions):
            stripped = instruction.strip()
            if stripped.endswith(":"):
                label_map[stripped[:-1]] = i

        pc = 0
        while pc < len(instructions):
            instruction = instructions[pc].strip()
            if not instruction or instruction.endswith(":"):
                pc += 1
                continue

            if instruction.startswith("MOV "):
                variable, raw_value = instruction[4:].split(",", 1)
                self.memory[variable.strip()] = self._resolve_operand(raw_value.strip())
            elif instruction.startswith("LOAD "):
                operand = instruction[5:].strip()
                self.stack.append(self._resolve_operand(operand))
            elif instruction == "REPORTE":
                if not self.stack:
                    raise RuntimeRadarError("la pila está vacía para REPORTE")
                self.output.append(f"REPORTE: {self.stack.pop()}")
            elif instruction == "ALERTA":
                if not self.stack:
                    raise RuntimeRadarError("la pila está vacía para ALERTA")
                self.output.append(f"ALERTA: {self.stack.pop()}")
            elif instruction.startswith("JMPF "):
                label = instruction[5:].strip()
                condition = self.stack.pop()
                if not condition:
                    pc = label_map[label]
                    continue
            elif instruction.startswith("JMP "):
                label = instruction[4:].strip()
                pc = label_map[label]
                continue
            elif instruction == "ADD":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)
            elif instruction == "SUB":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)
            elif instruction == "MUL":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
            elif instruction == "DIV":
                b = self.stack.pop()
                a = self.stack.pop()
                if b == 0:
                    raise RuntimeRadarError("división por cero")
                self.stack.append(a / b)
            elif instruction == "CONCAT":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(str(a) + str(b))
            elif instruction == "GT":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a > b)
            elif instruction == "LT":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a < b)
            elif instruction == "EQ":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a == b)
            elif instruction == "GE":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a >= b)
            elif instruction == "LE":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a <= b)
            elif instruction == "NE":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a != b)
            elif instruction.startswith("STORE "):
                var = instruction[6:].strip()
                self.memory[var] = self.stack.pop()
            elif instruction == "HALT":
                break
            else:
                raise RuntimeRadarError(f"instrucción no soportada '{instruction}'")
            pc += 1
        return self.output

    def _resolve_operand(self, operand: str):
        if operand in self.memory:
            return self.memory[operand]
        return self._parse_value(operand)

    def _parse_value(self, raw: str):
        if raw.startswith('"') and raw.endswith('"'):
            return raw[1:-1]
        if raw == "verdadero":
            return True
        if raw == "falso":
            return False
        if "." in raw:
            return float(raw)
        try:
            return int(raw)
        except ValueError:
            return raw
