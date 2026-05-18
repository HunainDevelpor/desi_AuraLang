from typing import Dict, List, Any, Set
from .ll1_parser import LL1Parser
from .slr.slr_parser import SLRParser
from .lalr.lalr_parser import LALRParser
from .first_follow import FirstFollow
from .parsing_table import ParsingTable

class ParserManager:
    def __init__(self, grammar: Dict[str, List[List[str]]]):
        self.grammar = grammar
        self.mode = "LL(1)" # Default mode
        
        # Build LL(1) defaults
        self.ff = FirstFollow(self.grammar)
        self.first = self.ff.compute_first()
        self.follow = self.ff.compute_follow()
        
        self.pt = ParsingTable(self.grammar, self.first, self.follow)
        self.ll1_table = self.pt.build()
        
        # Instantiate Engines on demand
        self.ll1_engine = LL1Parser(self.ll1_table, self.grammar)
        self.slr_engine = SLRParser(self.grammar, self.first, self.follow)
        self.lalr_engine = LALRParser(self.grammar, self.first, self.follow)

    def set_parser_mode(self, mode: str):
        if mode in ("LL(1)", "SLR", "LALR"):
            self.mode = mode

    def get_active_parser_name(self) -> str:
        return self.mode

    def parse(self, tokens) -> Dict[str, Any]:
        """Routes compilation to selected parsing engine and returns unified results."""
        if self.mode == "LL(1)":
            res = self.ll1_engine.parse(tokens)
            # Add LL(1) specific properties
            res["parser_type"] = "LL(1)"
            res["states_count"] = 0 # Top-down has no state automaton
            res["table_size"] = len(self.ll1_table) * len(self.ll1_engine.grammar) # Approximation
            res["conflicts_count"] = len(self.pt.conflicts)
            res["shift_count"] = 0
            res["reduce_count"] = 0
            res["steps_count"] = len(res["trace"]) if "trace" in res else 0
            return res
            
        elif self.mode == "SLR":
            res = self.slr_engine.parse(tokens)
            res["parser_type"] = "SLR"
            res["states_count"] = len(self.slr_engine.states)
            res["table_size"] = len(self.slr_engine.action_table) + len(self.slr_engine.goto_table)
            res["conflicts_count"] = len(self.slr_engine.conflicts)
            
            # Extract shift and reduce metrics
            shifts = 0
            reductions = 0
            if "trace" in res:
                for step in res["trace"]:
                    if "Shift" in step["action"]: shifts += 1
                    elif "Reduce" in step["action"]: reductions += 1
                    
            res["shift_count"] = shifts
            res["reduce_count"] = reductions
            res["steps_count"] = len(res["trace"]) if "trace" in res else 0
            return res
            
        elif self.mode == "LALR":
            res = self.lalr_engine.parse(tokens)
            res["parser_type"] = "LALR"
            res["states_count"] = len(self.lalr_engine.states)
            res["table_size"] = len(self.lalr_engine.action_table) + len(self.lalr_engine.goto_table)
            res["conflicts_count"] = len(self.lalr_engine.conflicts)
            
            # Extract shift and reduce metrics
            shifts = 0
            reductions = 0
            if "trace" in res:
                for step in res["trace"]:
                    if "Shift" in step["action"]: shifts += 1
                    elif "Reduce" in step["action"]: reductions += 1
                    
            res["shift_count"] = shifts
            res["reduce_count"] = reductions
            res["steps_count"] = len(res["trace"]) if "trace" in res else 0
            return res
            
        raise ValueError(f"Unknown parser mode '{self.mode}'")
