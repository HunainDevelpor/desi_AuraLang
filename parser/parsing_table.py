class ParsingTable:
    def __init__(self, grammar, first, follow):
        self.grammar = grammar
        self.first = first
        self.follow = follow
        self.table = {}
        self.conflicts = []
        self.left_recursions = []

    def detect_left_recursion(self):
        self.left_recursions = []
        # 1. Immediate Left Recursion
        for nt, prods in self.grammar.items():
            for prod in prods:
                if prod and prod[0] == nt:
                    self.left_recursions.append(
                        f"Immediate Left Recursion found on non-terminal '{nt}': {nt} -> {' '.join(prod)}"
                    )
        
        # 2. Indirect Left Recursion
        for start_nt in self.grammar.keys():
            visited = set()
            path = [start_nt]
            
            def dfs(curr):
                if curr not in self.grammar:
                    return None
                for prod in self.grammar[curr]:
                    if not prod or prod == ["\u03b5"]:
                        continue
                    first_sym = prod[0]
                    if first_sym == start_nt:
                        return path + [first_sym]
                    if first_sym in self.grammar and first_sym not in visited:
                        visited.add(first_sym)
                        path.append(first_sym)
                        res = dfs(first_sym)
                        if res:
                            return res
                        path.pop()
                return None
            
            cycle = dfs(start_nt)
            if cycle:
                self.left_recursions.append(
                    f"Indirect Left Recursion cycle detected: {' -> '.join(cycle)}"
                )
                break
                
        return self.left_recursions

    def build(self):
        self.detect_left_recursion()
        self.conflicts = []
        
        # Initialize table cells
        for nt in self.grammar:
            self.table[nt] = {}

        for nt, productions in self.grammar.items():
            for prod in productions:
                # Calculate First(prod)
                first_alpha = set()
                if prod == ["\u03b5"]:
                    first_alpha.add("\u03b5")
                else:
                    for symbol in prod:
                        if symbol not in self.grammar:
                            first_alpha.add(symbol)
                            break
                        else:
                            first_alpha.update(self.first[symbol] - {"\u03b5"})
                            if "\u03b5" not in self.first[symbol]:
                                break
                    else:
                        first_alpha.add("\u03b5")
                
                # Rule 1 & 2
                for terminal in first_alpha:
                    if terminal != "\u03b5":
                        if terminal not in self.table[nt]:
                            self.table[nt][terminal] = prod
                        else:
                            conflict_prod = self.table[nt][terminal]
                            if conflict_prod != prod:
                                msg = f"FIRST/FIRST Conflict on '{nt}' with terminal '{terminal}': '{nt} -> {' '.join(conflict_prod)}' vs '{nt} -> {' '.join(prod)}'"
                                self.conflicts.append(msg)

                if "\u03b5" in first_alpha:
                    for terminal in self.follow[nt]:
                        if terminal not in self.table[nt]:
                            self.table[nt][terminal] = prod
                        else:
                            conflict_prod = self.table[nt][terminal]
                            if conflict_prod != prod:
                                msg = f"FIRST/FOLLOW Conflict on '{nt}' with terminal '{terminal}': '{nt} -> {' '.join(conflict_prod)}' vs '{nt} -> {' '.join(prod)}'"
                                self.conflicts.append(msg)
        return self.table