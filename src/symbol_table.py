from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str
    var_type: str


class SymbolTable:
    def __init__(self):
        self.symbols: dict[str, Symbol] = {}

    def define(self, name: str, var_type: str) -> None:
        self.symbols[name] = Symbol(name, var_type)

    def exists(self, name: str) -> bool:
        return name in self.symbols

    def get_type(self, name: str) -> str:
        return self.symbols[name].var_type

    def display(self) -> str:
        lines = ["Nombre              Tipo", "------------------------"]
        for symbol in self.symbols.values():
            lines.append(f"{symbol.name:<19} {symbol.var_type}")
        return "\n".join(lines)
