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

class LALRParser:
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
        
        # LALR State & Table Structures
        self.lr1_states: List[Set[Tuple[str, Tuple[str, ...], int, str]]] = []
        self.states: List[Set[Tuple[str, Tuple[str, ...], int, str]]] = []
        self.transitions: Dict[Tuple[int, str], int] = {}
        self.action_table: Dict[Tuple[int, str], str] = {}
        self.goto_table: Dict[Tuple[int, str], int] = {}
        self.conflicts: List[str] = []
        
        # Merge logs and name maps for visualization
        self.merge_logs: List[str] = []
        self.state_names: List[str] = []
        
        # Build LALR tables
        self.build_lalr()

    def compute_first_sequence(self, sequence: Tuple[str, ...], la: str) -> Set[str]:
        first_set = set()
        for sym in sequence:
            if sym not in self.grammar: # Terminal
                first_set.add(sym)
                return first_set
            else:
                sym_first = self.first.get(sym, set())
                first_set.update(sym_first - {"ε"})
                if "ε" not in sym_first:
                    return first_set
        first_set.add(la)
        return first_set

    def lr1_closure(self, items: Set[Tuple[str, Tuple[str, ...], int, str]]) -> Set[Tuple[str, Tuple[str, ...], int, str]]:
        closure_set = set(items)
        changed = True
        while changed:
            changed = False
            current_items = list(closure_set)
            before_size = len(closure_set)
            
            for lhs, rhs, dot, la in current_items:
                if dot < len(rhs):
                    next_sym = rhs[dot]
                    if next_sym in self.grammar: # Non-terminal
                        beta = rhs[dot+1:]
                        first_beta_la = self.compute_first_sequence(beta, la)
                        
                        for prod in self.grammar[next_sym]:
                            rhs_tuple = () if prod == ["ε"] else tuple(prod)
                            for b in first_beta_la:
                                new_item = (next_sym, rhs_tuple, 0, b)
                                if new_item not in closure_set:
                                    closure_set.add(new_item)
                                    changed = True
                                    
            if len(closure_set) > before_size:
                changed = True
        return closure_set

    def lr1_goto(self, items: Set[Tuple[str, Tuple[str, ...], int, str]], symbol: str) -> Set[Tuple[str, Tuple[str, ...], int, str]]:
        goto_set = set()
        for lhs, rhs, dot, la in items:
            if dot < len(rhs) and rhs[dot] == symbol:
                goto_set.add((lhs, rhs, dot + 1, la))
        return self.lr1_closure(goto_set)

    def build_lalr(self):
        # 1. Build Canonical LR(1) Automaton
        initial_item = (self.augmented_start, (self.start_symbol,), 0, "$")
        j0 = self.lr1_closure({initial_item})
        self.lr1_states = [j0]
        lr1_transitions = {}
        
        changed = True
        while changed:
            changed = False
            for idx in range(len(self.lr1_states)):
                state = self.lr1_states[idx]
                symbols = set()
                for lhs, rhs, dot, la in state:
                    if dot < len(rhs):
                        symbols.add(rhs[dot])
                        
                for sym in symbols:
                    next_state = self.lr1_goto(state, sym)
                    if not next_state:
                        continue
                    if next_state not in self.lr1_states:
                        self.lr1_states.append(next_state)
                        changed = True
                        
                    next_idx = self.lr1_states.index(next_state)
                    trans_key = (idx, sym)
                    if trans_key not in lr1_transitions:
                        lr1_transitions[trans_key] = next_idx
                        changed = True

        # 2. Group LR(1) states by their LR(0) item cores
        core_groups: List[List[int]] = []
        core_to_group_idx = {}
        
        for k, lr1_state in enumerate(self.lr1_states):
            core = frozenset({(lhs, rhs, dot) for lhs, rhs, dot, la in lr1_state})
            if core in core_to_group_idx:
                g_idx = core_to_group_idx[core]
                core_groups[g_idx].append(k)
            else:
                core_to_group_idx[core] = len(core_groups)
                core_groups.append([k])
                
        # 3. Construct LALR States by merging lookaheads for cores
        self.states = []
        lr1_to_lalr = {}
        self.merge_logs = []
        self.state_names = []
        
        for g_idx, group in enumerate(core_groups):
            merged_items = set()
            for lr1_idx in group:
                merged_items.update(self.lr1_states[lr1_idx])
                lr1_to_lalr[lr1_idx] = g_idx
                
            self.states.append(merged_items)
            
            if len(group) > 1:
                name = "+" .join([f"I{x}" for x in sorted(group)])
                self.merge_logs.append(f"Merged states {', '.join([f'I{x}' for x in group])} -> LALR {name}")
                self.state_names.append(name)
            else:
                self.state_names.append(f"I{group[0]}")
                
        # 4. Construct LALR Transitions
        self.transitions = {}
        for (lr1_src, sym), lr1_dest in lr1_transitions.items():
            lalr_src = lr1_to_lalr[lr1_src]
            lalr_dest = lr1_to_lalr[lr1_dest]
            self.transitions[(lalr_src, sym)] = lalr_dest
            
        # 5. Build LALR ACTION and GOTO tables
        self.action_table = {}
        self.goto_table = {}
        self.conflicts = []
        
        for i, state in enumerate(self.states):
            for lhs, rhs, dot, la in state:
                if dot < len(rhs):
                    sym = rhs[dot]
                    next_state = self.transitions.get((i, sym))
                    if next_state is not None:
                        if sym not in self.original_grammar: # Terminal
                            action_key = (i, sym)
                            new_action = f"S{next_state}"
                            if action_key in self.action_table:
                                old_action = self.action_table[action_key]
                                if old_action != new_action:
                                    conflict_msg = f"LALR Shift-Reduce Conflict in State {self.state_names[i]} on '{sym}': " \
                                                   f"Shift to {self.state_names[next_state]} vs Reduce."
                                    if conflict_msg not in self.conflicts:
                                        self.conflicts.append(conflict_msg)
                            else:
                                self.action_table[action_key] = new_action
                        else: # Non-terminal
                            self.goto_table[(i, sym)] = next_state
                else:
                    if lhs == self.augmented_start:
                        self.action_table[(i, "$")] = "Accept"
                    else:
                        prod_str = " ".join(rhs) if rhs else "ε"
                        reduce_action = f"R {lhs} -> {prod_str}"
                        action_key = (i, la)
                        
                        if action_key in self.action_table:
                            old_action = self.action_table[action_key]
                            if old_action != reduce_action:
                                if old_action.startswith("S"):
                                    conflict_msg = f"LALR Shift-Reduce Conflict in State {self.state_names[i]} on lookahead '{la}': " \
                                                   f"Shift ({old_action}) vs Reduce ({reduce_action})."
                                else:
                                    conflict_msg = f"LALR Reduce-Reduce Conflict in State {self.state_names[i]} on lookahead '{la}': " \
                                                   f"Reduce ({old_action}) vs Reduce ({reduce_action})."
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
                error = f"LALR Syntax Error in State {self.state_names[curr_state]}: Unexpected token '{term}' (expected: {', '.join(expected_terms)})"
                trace.append({
                    "stack": stack_view,
                    "input": input_view,
                    "action": f"ERROR: Expected one of {expected_terms}"
                })
                break
                
            if action.startswith("S"):
                next_state = int(action[1:])
                state_stack.append(next_state)
                node_val = f"{term} ({lit})" if lit != term else term
                node_stack.append(Node(node_val))
                
                trace.append({
                    "stack": stack_view,
                    "input": input_view,
                    "action": f"Shift to State {self.state_names[next_state]}"
                })
                idx += 1
            elif action.startswith("R"):
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
                    
                goto_state = state_stack[-1]
                next_state = self.goto_table.get((goto_state, lhs))
                if next_state is None:
                    error = f"LALR Internal Error: Missing Goto transition in State {self.state_names[goto_state]} for non-terminal '{lhs}'"
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
                error = f"LALR Syntax Error: Unknown action '{action}'"
                break
        else:
            error = "LALR Syntax Error: Parsing steps exceeded safety limit (infinite reduction loop prevention)."
            
        root = node_stack[0] if not error and node_stack else None
        
        return {
            "success": error is None,
            "error": error,
            "trace": trace,
            "tree": root.to_dict() if root else None
        }
