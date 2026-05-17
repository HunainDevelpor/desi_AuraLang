import random

class Symbol:
    def __init__(self, name, symbol_type, scope, line):
        self.name = name
        self.type = symbol_type
        self.scope = scope
        self.line = line
        self.address = hex(random.randint(0x1000, 0xFFFF))

class SymbolTable:
    def __init__(self):
        self.symbols = {} # name -> Symbol object
        self.current_scope = "Global"

    def add(self, name, symbol_type, line):
        if name not in self.symbols:
            self.symbols[name] = Symbol(name, symbol_type, self.current_scope, line)

    def build(self, tokens):
        self.symbols = {}
        for t in tokens:
            if t.type.name == "IDENT":
                # Very simple heuristic: if it follows 'RAKHO', it's a declaration
                # In a real compiler, this would be driven by the parser
                self.add(t.value, "variable", t.line)

    def get_all(self):
        return list(self.symbols.values())