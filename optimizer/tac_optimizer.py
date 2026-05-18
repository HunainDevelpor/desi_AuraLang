from intermediate.ir_generator import Quadruple
from typing import List, Dict, Any, Tuple, Set

class TACOptimizer:
    def __init__(self):
        self.logs: List[str] = []

    def log(self, msg: str):
        self.logs.append(f"[Optimization] {msg}")

    def optimize(self, quadruples: List[Quadruple]) -> List[Quadruple]:
        self.logs = []
        self.log("Starting optimization engine...")
        
        current = quadruples
        iterations = 0
        max_iterations = 6
        
        while iterations < max_iterations:
            self.log(f"--- Running Optimization Pass {iterations + 1} ---")
            changed = False
            
            # 1. Constant & Copy Propagation
            current, pass_changed = self.pass_propagation(current)
            if pass_changed: changed = True
            
            # 2. Constant Folding & Algebraic Simplification
            current, pass_changed = self.pass_folding_and_simplification(current)
            if pass_changed: changed = True
            
            # 3. Common Subexpression Elimination (CSE)
            current, pass_changed = self.pass_cse(current)
            if pass_changed: changed = True
            
            # 4. Dead Store Elimination (DSE)
            current, pass_changed = self.pass_dse(current)
            if pass_changed: changed = True
            
            # 5. Dead Code Elimination (DCE)
            current, pass_changed = self.pass_dead_code_elimination(current)
            if pass_changed: changed = True
            
            if not changed:
                self.log(f"Optimization converged after {iterations + 1} passes.")
                break
                
            iterations += 1
            
        self.log("Optimization complete!")
        return current

    # ====================================================
    # PASS 1: CONSTANT & COPY PROPAGATION
    # ====================================================

    def pass_propagation(self, quadruples: List[Quadruple]) -> Tuple[List[Quadruple], bool]:
        changed = False
        optimized: List[Quadruple] = []
        
        # Count global assignments to each variable to identify loop-mutated or re-assigned variables
        assign_counts: Dict[str, int] = {}
        for q in quadruples:
            if q.op not in ("LABEL", "GOTO", "IF_FALSE", "PRINT", "RETURN", "PUSH", "ARRAY_SET"):
                if q.result:
                    assign_counts[q.result] = assign_counts.get(q.result, 0) + 1
                    
        # Maps variable name -> current constant value string or variable name copy
        bindings: Dict[str, str] = {}
        
        for q in quadruples:
            arg1 = q.arg1
            arg2 = q.arg2
            result = q.result
            
            # 1. Propagate into arg1
            if arg1 in bindings:
                propagated = bindings[arg1]
                self.log(f"Propagated '{propagated}' into '{arg1}' in statement: '{result or ''} = {arg1} {q.op} {arg2}'")
                arg1 = propagated
                changed = True
                
            # 2. Propagate into arg2
            if arg2 in bindings:
                propagated = bindings[arg2]
                self.log(f"Propagated '{propagated}' into '{arg2}' in statement: '{result or ''} = {arg1} {q.op} {arg2}'")
                arg2 = propagated
                changed = True
                
            # 3. Track new bindings
            if q.op == "=":
                # If result is a variable redefinition, clear its bindings
                if result in bindings:
                    del bindings[result]
                # Only propagate if the variable is assigned EXACTLY ONCE globally (guaranteeing loop/mutation safety)
                if assign_counts.get(result, 0) == 1:
                    if self.is_literal(arg1) or (arg1.isidentifier() and arg1 not in bindings):
                        bindings[result] = arg1
                        self.log(f"Recorded binding: '{result}' = '{arg1}'")
            else:
                # If variable is redefined in another op (e.g. x = x + 1), invalidate its bindings
                if result in bindings:
                    del bindings[result]
                    
            optimized.append(Quadruple(q.op, arg1, arg2, result))
            
        return optimized, changed

    # ====================================================
    # PASS 2: CONSTANT FOLDING & ALGEBRAIC SIMPLIFICATION
    # ====================================================

    def pass_folding_and_simplification(self, quadruples: List[Quadruple]) -> Tuple[List[Quadruple], bool]:
        changed = False
        optimized: List[Quadruple] = []
        
        for q in quadruples:
            op = q.op
            arg1 = q.arg1
            arg2 = q.arg2
            result = q.result
            
            # --- Constant Folding ---
            if op in ("+", "-", "*", "/", "%", "==", "!=", ">", "<", ">=", "<=", "and", "or"):
                if self.is_literal(arg1) and self.is_literal(arg2):
                    v1 = self.parse_literal(arg1)
                    v2 = self.parse_literal(arg2)
                    
                    try:
                        folded = None
                        if op == "+": folded = v1 + v2
                        elif op == "-": folded = v1 - v2
                        elif op == "*": folded = v1 * v2
                        elif op == "/": folded = v1 / v2 if v2 != 0 else 0
                        elif op == "%": folded = v1 % v2 if v2 != 0 else 0
                        elif op == "==": folded = v1 == v2
                        elif op == "!=": folded = v1 != v2
                        elif op == ">": folded = v1 > v2
                        elif op == "<": folded = v1 < v2
                        elif op == ">=": folded = v1 >= v2
                        elif op == "<=": folded = v1 <= v2
                        elif op == "and": folded = bool(v1) and bool(v2)
                        elif op == "or": folded = bool(v1) or bool(v2)
                        
                        if folded is not None:
                            # Convert back to literal string
                            folded_str = str(folded)
                            self.log(f"Folded constant expression: '{arg1} {op} {arg2}' into '{folded_str}'")
                            op = "="
                            arg1 = folded_str
                            arg2 = ""
                            changed = True
                    except Exception:
                        pass # avoid crash on mismatched types
                        
            # --- Algebraic Simplification ---
            if op == "+":
                if arg1 == "0":
                    self.log(f"Simplified '{result} = 0 + {arg2}' into '{result} = {arg2}'")
                    op = "="
                    arg1 = arg2
                    arg2 = ""
                    changed = True
                elif arg2 == "0":
                    self.log(f"Simplified '{result} = {arg1} + 0' into '{result} = {arg1}'")
                    op = "="
                    arg2 = ""
                    changed = True
            elif op == "*":
                if arg1 == "1":
                    self.log(f"Simplified '{result} = 1 * {arg2}' into '{result} = {arg2}'")
                    op = "="
                    arg1 = arg2
                    arg2 = ""
                    changed = True
                elif arg2 == "1":
                    self.log(f"Simplified '{result} = {arg1} * 1' into '{result} = {arg1}'")
                    op = "="
                    arg2 = ""
                    changed = True
                elif arg1 == "0" or arg2 == "0":
                    self.log(f"Simplified multiplication by zero into '{result} = 0'")
                    op = "="
                    arg1 = "0"
                    arg2 = ""
                    changed = True
                    
            optimized.append(Quadruple(op, arg1, arg2, result))
            
        return optimized, changed

    # ====================================================
    # PASS 3: DEAD CODE ELIMINATION (DCE)
    # ====================================================

    def pass_dead_code_elimination(self, quadruples: List[Quadruple]) -> Tuple[List[Quadruple], bool]:
        changed = False
        optimized: List[Quadruple] = []
        
        # Count usage of variables
        usage: Set[str] = set()
        for q in quadruples:
            if q.op not in ("LABEL", "LABEL_FUNC"): # Labels are not variables
                if q.arg1: usage.add(q.arg1)
                if q.arg2: usage.add(q.arg2)
                
        for q in quadruples:
            result = q.result
            op = q.op
            
            # We can safely eliminate dead assignments to any variable (temporaries or user variables)
            # if they are never used as arguments in subsequent statements.
            if op == "=" and result and result not in usage:
                self.log(f"Eliminated dead code assignment to unused variable: '{result} = {q.arg1}'")
                changed = True
                continue # Skip adding this statement (eliminates it!)
                
            optimized.append(q)
            
        return optimized, changed

    # ====================================================
    # UTILITY HELPERS
    # ====================================================

    def is_literal(self, val: str) -> bool:
        if not val:
            return False
        # Integer or Float
        if val.replace(".", "", 1).isdigit():
            return True
        # Booleans
        if val in ("True", "False", "sahi", "galat"):
            return True
        # Strings
        if val.startswith('"') and val.endswith('"'):
            return True
        return False

    def parse_literal(self, val: str) -> Any:
        if val in ("True", "sahi"): return True
        if val in ("False", "galat"): return False
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        if "." in val:
            return float(val)
        return int(val)

    @staticmethod
    def to_tac_string(quads: List[Quadruple]) -> List[str]:
        tac = []
        for q in quads:
            op = q.op
            if op == "=":
                tac.append(f"{q.result} = {q.arg1}")
            elif op == "LABEL":
                tac.append(f"label {q.result}")
            elif op == "GOTO":
                tac.append(f"goto {q.result}")
            elif op == "IF_FALSE":
                tac.append(f"if_false {q.arg1} goto {q.result}")
            elif op == "PRINT":
                tac.append(f"print {q.arg1}")
            elif op == "RETURN":
                tac.append(f"return {q.arg1}")
            elif op == "PUSH":
                tac.append(f"push {q.arg1}")
            elif op == "CALL":
                tac.append(f"{q.result} = call {q.arg1}, {q.arg2}")
            elif op == "ALLOC_ARRAY":
                tac.append(f"{q.result} = alloc_array {q.arg1}")
            elif op == "ARRAY_SET":
                tac.append(f"{q.result}[{q.arg2}] = {q.arg1}")
            else:
                # Binary or unary op
                if q.arg2:
                    tac.append(f"{q.result} = {q.arg1} {op} {q.arg2}")
                else:
                    tac.append(f"{q.result} = {op} {q.arg1}")
        return tac

    # ====================================================
    # PASS 4: COMMON SUBEXPRESSION ELIMINATION (CSE)
    # ====================================================

    def pass_cse(self, quadruples: List[Quadruple]) -> Tuple[List[Quadruple], bool]:
        changed = False
        optimized: List[Quadruple] = []
        
        # Maps expression tuple (op, arg1, arg2) -> temporary variable name holding its result
        expr_map: Dict[Tuple[str, str, str], str] = {}
        
        for q in quadruples:
            if q.op in ("LABEL", "GOTO", "IF_FALSE", "CALL", "LABEL_FUNC", "RETURN"):
                # Clear map on control flow boundaries to be safe
                expr_map.clear()
                optimized.append(q)
                continue
                
            # If any argument has been redefined, invalidate expressions containing it!
            if q.op == "=":
                to_del = [expr for expr in expr_map if expr[1] == q.result or expr[2] == q.result]
                for expr in to_del:
                    del expr_map[expr]
                optimized.append(q)
                continue
                
            # Check if this is a binary expression
            if q.op in ("+", "-", "*", "/", "%", "==", "!=", ">", "<", ">=", "<="):
                expr_key = (q.op, q.arg1, q.arg2)
                if expr_key in expr_map:
                    prev_temp = expr_map[expr_key]
                    self.log(f"Eliminated common subexpression: '{q.result} = {q.arg1} {q.op} {q.arg2}' replaced with copy: '{q.result} = {prev_temp}'")
                    optimized.append(Quadruple("=", prev_temp, "", q.result))
                    changed = True
                else:
                    expr_map[expr_key] = q.result
                    optimized.append(q)
            else:
                optimized.append(q)
                
        return optimized, changed

    # ====================================================
    # PASS 5: DEAD STORE ELIMINATION (DSE)
    # ====================================================

    def pass_dse(self, quadruples: List[Quadruple]) -> Tuple[List[Quadruple], bool]:
        changed = False
        optimized: List[Quadruple] = []
        
        # Partition into basic blocks for 100% safe within-block DSE optimization
        blocks: List[List[Quadruple]] = []
        current_block: List[Quadruple] = []
        
        for q in quadruples:
            if q.op in ("LABEL", "GOTO", "IF_FALSE", "LABEL_FUNC", "CALL", "RETURN"):
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                blocks.append([q])
            else:
                current_block.append(q)
        if current_block:
            blocks.append(current_block)
            
        for block in blocks:
            if len(block) <= 1:
                optimized.extend(block)
                continue
                
            block_opt: List[Quadruple] = []
            block_len = len(block)
            dead_indices = set()
            
            for i in range(block_len):
                q = block[i]
                if q.op == "=" and q.result and not q.result.startswith("func_"):
                    is_read_before_reassign = False
                    has_reassign = False
                    reassign_idx = -1
                    
                    for j in range(i + 1, block_len):
                        sub_q = block[j]
                        # Check if variable is read
                        if sub_q.arg1 == q.result or sub_q.arg2 == q.result or (sub_q.op in ("PRINT", "PUSH", "RETURN") and sub_q.arg1 == q.result):
                            is_read_before_reassign = True
                            break
                        # Check if variable is overwritten
                        if sub_q.result == q.result and sub_q.op not in ("ARRAY_SET",):
                            has_reassign = True
                            reassign_idx = j
                            break
                            
                    if has_reassign and not is_read_before_reassign:
                        self.log(f"Eliminated dead store to '{q.result}' (overwritten at statement index {reassign_idx} without being read)")
                        dead_indices.add(i)
                        changed = True
                        
            for i in range(block_len):
                if i not in dead_indices:
                    block_opt.append(block[i])
            optimized.extend(block_opt)
            
        return optimized, changed
