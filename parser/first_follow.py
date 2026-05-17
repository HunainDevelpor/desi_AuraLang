class FirstFollow:
    def __init__(self, grammar):
        self.grammar = grammar
        self.first = {}
        self.follow = {}
        self.non_terminals = list(grammar.keys())

    def compute_first(self):
        for nt in self.non_terminals:
            self.first[nt] = set()

        changed = True
        while changed:
            changed = False
            for nt, productions in self.grammar.items():
                for prod in productions:
                    # prod is a list of symbols
                    before_size = len(self.first[nt])
                    
                    if prod == ["\u03b5"]: # handle epsilon
                        self.first[nt].add("\u03b5")
                    else:
                        for symbol in prod:
                            if symbol not in self.grammar: # Terminal
                                self.first[nt].add(symbol)
                                break
                            else: # Non-terminal
                                symbol_first = self.first[symbol]
                                self.first[nt].update(symbol_first - {"\u03b5"})
                                if "\u03b5" not in symbol_first:
                                    break
                        else:
                            # if we reached here, all symbols in production had epsilon
                            self.first[nt].add("\u03b5")
                    
                    if len(self.first[nt]) > before_size:
                        changed = True
        return self.first

    def compute_follow(self):
        for nt in self.non_terminals:
            self.follow[nt] = set()

        start_symbol = self.non_terminals[0]
        self.follow[start_symbol].add("$")

        changed = True
        while changed:
            changed = False
            for nt, productions in self.grammar.items():
                for prod in productions:
                    for i, symbol in enumerate(prod):
                        if symbol in self.grammar: # Non-terminal B
                            before_size = len(self.follow[symbol])
                            
                            # Rule: A -> alpha B beta 
                            # everything in First(beta) except epsilon goes into Follow(B)
                            following_symbols = prod[i+1:]
                            if not following_symbols:
                                # A -> alpha B
                                self.follow[symbol].update(self.follow[nt])
                            else:
                                # A -> alpha B beta
                                epsilon_in_all = True
                                for f_symbol in following_symbols:
                                    if f_symbol not in self.grammar:
                                        self.follow[symbol].add(f_symbol)
                                        epsilon_in_all = False
                                        break
                                    else:
                                        self.follow[symbol].update(self.first[f_symbol] - {"\u03b5"})
                                        if "\u03b5" not in self.first[f_symbol]:
                                            epsilon_in_all = False
                                            break
                                if epsilon_in_all:
                                    self.follow[symbol].update(self.follow[nt])
                            
                            if len(self.follow[symbol]) > before_size:
                                changed = True
        return self.follow