import datetime
from typing import List, Dict, Set, Tuple, Any
from ..first_follow import FirstFollow
from ..grammer import TERMINALS

class Node:
    def __init__(self, value):
        self.value = value
        self.children = []
    
    def add_child(self, node):
        self.children.append(node)
    
    def to_dict(self):
        return {
            "name": self.value,
            "children": [c.to_dict() for c in self.children]
        }

class SLRParser:
    def __init__(self, grammar: Dict[str, List[List[str]]], first: Dict[str, Set[str]], follow: Dict[str, Set[str]]):
        self.original_grammar = grammar
        self.first = first
        self.follow = follow
        
        # 1. Setup Augmented Grammar
        self.start_symbol = list(grammar.keys())[0]
        self.augmented_start = f"{self.start_symbol}'"
        
        self.grammar = {self.augmented_start: [[self.start_symbol]]}
        for nt, prods in grammar.items():
            self.grammar[nt] = prods
            
        self.non_terminals = list(self.grammar.keys())
        
        # Find all terminals
        self.terminals = set()
        for prods in self.grammar.values():
            for prod in prods:
                for sym in prod:
                    if sym not in self.grammar and sym != "ε":
                        self.terminals.add(sym)
        self.terminals.add("$")
        self.terminals = sorted(list(self.terminals))
        
        # Map item representations for comparisons
        self.states: List[Set[Tuple[str, Tuple[str, ...], int]]] = []
        self.transitions: Dict[Tuple[int, str], int] = {}
        self.action_table: Dict[Tuple[int, str], str] = {}
        self.goto_table: Dict[Tuple[int, str], int] = {}
        self.conflicts: List[str] = []
        
        # Build SLR automaton and tables
        self.build_automaton()
        self.build_tables()

    def closure(self, items: Set[Tuple[str, Tuple[str, ...], int]]) -> Set[Tuple[str, Tuple[str, ...], int]]:
        closure_set = set(items)
        changed = True
        while changed:
            changed = False
            current_items = list(closure_set)
            before_size = len(closure_set)
            
            for lhs, rhs, dot in current_items:
                if dot < len(rhs):
                    next_sym = rhs[dot]
                    if next_sym in self.grammar: # Non-terminal
                        for prod in self.grammar[next_sym]:
                            # If production is epsilon (empty), represent it as empty tuple
                            rhs_tuple = () if prod == ["ε"] else tuple(prod)
                            new_item = (next_sym, rhs_tuple, 0)
                            if new_item not in closure_set:
                                closure_set.add(new_item)
                                changed = True
                                
            if len(closure_set) > before_size:
                changed = True
        return closure_set

    def goto(self, items: Set[Tuple[str, Tuple[str, ...], int]], symbol: str) -> Set[Tuple[str, Tuple[str, ...], int]]:
        goto_set = set()
        for lhs, rhs, dot in items:
            if dot < len(rhs) and rhs[dot] == symbol:
                goto_set.add((lhs, rhs, dot + 1))
        return self.closure(goto_set)

    def build_automaton(self):
        # Initial State I0
        initial_item = (self.augmented_start, (self.start_symbol,), 0)
        i0 = self.closure({initial_item})
        self.states = [i0]
        self.transitions = {}
        
        changed = True
        while changed:
            changed = False
            for idx in range(len(self.states)):
                state = self.states[idx]
                # Find all symbols after dot in this state
                symbols = set()
                for lhs, rhs, dot in state:
                    if dot < len(rhs):
                        symbols.add(rhs[dot])
                        
                for sym in symbols:
                    next_state = self.goto(state, sym)
                    if not next_state:
                        continue
                    if next_state not in self.states:
                        self.states.append(next_state)
                        changed = True
                    
                    next_idx = self.states.index(next_state)
                    trans_key = (idx, sym)
                    if trans_key not in self.transitions:
                        self.transitions[trans_key] = next_idx
                        changed = True

    def build_tables(self):
        self.action_table = {}
        self.goto_table = {}
        self.conflicts = []
        
        for i, state in enumerate(self.states):
            for lhs, rhs, dot in state:
                if dot < len(rhs):
                    # Shift or Goto
                    sym = rhs[dot]
                    next_state = self.transitions.get((i, sym))
                    if next_state is not None:
                        if sym not in self.grammar: # Terminal
                            action_key = (i, sym)
                            new_action = f"S{next_state}"
                            if action_key in self.action_table:
                                old_action = self.action_table[action_key]
                                if old_action != new_action:
                                    conflict_msg = f"Shift-Reduce Conflict in State {i} on terminal '{sym}': " \
                                                   f"Can Shift to State {next_state} OR Reduce by rules."
                                    if conflict_msg not in self.conflicts:
                                        self.conflicts.append(conflict_msg)
                            else:
                                self.action_table[action_key] = new_action
                        else: # Non-terminal
                            self.goto_table[(i, sym)] = next_state
                else:
                    # Reduce or Accept
                    if lhs == self.augmented_start:
                        self.action_table[(i, "$")] = "Accept"
                    else:
                        # Reduce by A -> alpha
                        prod_str = " ".join(rhs) if rhs else "ε"
                        reduce_action = f"R {lhs} -> {prod_str}"
                        
                        # Get follow set for SLR
                        lhs_follow = self.follow.get(lhs, set())
                        for a in lhs_follow:
                            action_key = (i, a)
                            if action_key in self.action_table:
                                old_action = self.action_table[action_key]
                                if old_action != reduce_action:
                                    if old_action.startswith("S"):
                                        conflict_msg = f"Shift-Reduce Conflict in State {i} on terminal '{a}': " \
                                                       f"Can Shift ({old_action}) OR Reduce ({reduce_action})."
                                    else:
                                        conflict_msg = f"Reduce-Reduce Conflict in State {i} on terminal '{a}': " \
                                                       f"Can Reduce ({old_action}) OR Reduce ({reduce_action})."
                                    if conflict_msg not in self.conflicts:
                                        self.conflicts.append(conflict_msg)
                            else:
                                self.action_table[action_key] = reduce_action

    def parse(self, tokens_objs) -> Dict[str, Any]:
        # Convert lexer tokens to grammar terminals
        input_tokens = []
        for t in tokens_objs:
            g_terminal = TERMINALS.get(t.type.name)
            if g_terminal is None:
                g_terminal = str(t.value) if t.value is not None else t.type.name.lower()
            literal = str(t.value) if t.value is not None else g_terminal
            input_tokens.append((g_terminal, literal))
            
        if not input_tokens or input_tokens[-1][0] != "$":
            input_tokens.append(("$", "$"))
            
        state_stack = [0]
        node_stack = []
        trace = []
        error = None
        
        idx = 0
        limit_steps = 1000
        step = 0
        
        while step < limit_steps:
            step += 1
            curr_state = state_stack[-1]
            term, lit = input_tokens[idx]
            
            stack_view = " ".join(map(str, state_stack))
            input_view = " ".join([t[0] for t in input_tokens[idx:]])
            
            action_key = (curr_state, term)
            action = self.action_table.get(action_key)
            
            if action is None:
                expected_terms = [t for s, t in self.action_table.keys() if s == curr_state]
                error = f"SLR Syntax Error in State {curr_state}: Unexpected token '{term}' (expected one of: {', '.join(expected_terms)})"
                trace.append({
                    "stack": stack_view,
                    "input": input_view,
                    "action": f"ERROR: Expected one of {expected_terms}"
                })
                break
                
            if action.startswith("S"):
                # Shift
                next_state = int(action[1:])
                state_stack.append(next_state)
                # Create leaf node for shifted terminal
                node_val = f"{term} ({lit})" if lit != term else term
                node_stack.append(Node(node_val))
                
                trace.append({
                    "stack": stack_view,
                    "input": input_view,
                    "action": f"Shift to State {next_state}"
                })
                idx += 1
            elif action.startswith("R"):
                # Reduce
                # Format: R LHS -> Symbol1 Symbol2 ...
                prod_part = action[2:]
                lhs, rhs_part = prod_part.split(" -> ")
                rhs_symbols = [] if rhs_part == "ε" else rhs_part.split()
                
                k = len(rhs_symbols)
                parent_node = Node(lhs)
                popped_nodes = []
                for _ in range(k):
                    state_stack.pop()
                    if node_stack:
                        popped_nodes.append(node_stack.pop())
                        
                for child in reversed(popped_nodes):
                    parent_node.add_child(child)
                    
                if k == 0:
                    parent_node.add_child(Node("ε"))
                    
                # Push Goto State
                goto_state = state_stack[-1]
                next_state = self.goto_table.get((goto_state, lhs))
                if next_state is None:
                    error = f"SLR Internal Error: Missing Goto transition in State {goto_state} for non-terminal '{lhs}'"
                    break
                state_stack.append(next_state)
                node_stack.append(parent_node)
                
                trace.append({
                    "stack": stack_view,
                    "input": input_view,
                    "action": f"Reduce by {lhs} -> {rhs_part}"
                })
            elif action == "Accept":
                trace.append({
                    "stack": stack_view,
                    "input": input_view,
                    "action": "Accept (Parse Successful ✓)"
                })
                break
            else:
                error = f"SLR Syntax Error: Unknown action '{action}'"
                break
        else:
            error = "SLR Syntax Error: Parsing steps exceeded safety limit (potential infinite reduction loop)."
            
        root = node_stack[0] if not error and node_stack else None
        
        return {
            "success": error is None,
            "error": error,
            "trace": trace,
            "tree": root.to_dict() if root else None
        }
