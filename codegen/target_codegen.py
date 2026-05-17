from intermediate.ir_generator import Quadruple
from typing import List

class TargetCodeGen:
    def __init__(self):
        self.instructions: List[str] = []

    def load_operand(self, op: str) -> List[str]:
        """Generate LOAD or PUSH instruction for an operand."""
        if not op:
            return []
        
        # 1. Numeric constants
        if op.replace(".", "", 1).isdigit():
            return [f"PUSH {op}"]
            
        # 2. Boolean constants
        if op in ("True", "False", "sahi", "galat"):
            val = "True" if op in ("True", "sahi") else "False"
            return [f"PUSH {val}"]
            
        # 3. String literal constants
        if op.startswith('"') and op.endswith('"'):
            return [f"PUSH {op}"]
            
        # 4. Standard variables / temporaries
        return [f"LOAD {op}"]

    def generate(self, quadruples: List[Quadruple]) -> List[str]:
        self.instructions = []
        
        # 1. Find the boundary where all top-level function declarations end
        last_func_end = -1
        for idx, q in enumerate(quadruples):
            if q.op == "RETURN":
                last_func_end = idx
                
        has_functions = last_func_end != -1
        
        # 2. If functions exist, emit a jump at the very top to skip them
        if has_functions:
            self.instructions.append("; Route program entrance past function declarations")
            self.instructions.append("JMP main_entry")
            
        for idx, q in enumerate(quadruples):
            op = q.op
            arg1 = q.arg1
            arg2 = q.arg2
            result = q.result
            
            # If we just passed the last function declaration, insert the main entry label
            if has_functions and idx == last_func_end + 1:
                self.instructions.append("; Main Program Entry Point")
                self.instructions.append("main_entry:")
                
            self.instructions.append(f"; line {q.line}")
            self.instructions.append(f"; tac_idx {idx}")
            self.instructions.append(f"; TAC: {result or ''} = {arg1 or ''} {op or ''} {arg2 or ''}".strip("= "))
            
            if op == "=":
                # Direct assignment: result = arg1
                self.instructions.extend(self.load_operand(arg1))
                self.instructions.append(f"STORE {result}")
                
            elif op == "LABEL":
                self.instructions.append(f"{result}:")
                
            elif op == "GOTO":
                self.instructions.append(f"JMP {result}")
                
            elif op == "IF_FALSE":
                # Pop condition from stack, if false jump to result label
                self.instructions.extend(self.load_operand(arg1))
                self.instructions.append(f"JMPZ {result}")
                
            elif op == "PRINT":
                # Pop value and print
                self.instructions.extend(self.load_operand(arg1))
                self.instructions.append("PRINT")
                
            elif op == "RETURN":
                # Pop return value and RET
                self.instructions.extend(self.load_operand(arg1))
                self.instructions.append("RET")
                
            elif op == "PUSH":
                # Push argument value onto stack
                self.instructions.extend(self.load_operand(arg1))
                
            elif op == "CALL":
                # Call function target label with argument count
                self.instructions.append(f"CALL func_{arg1}, {arg2}")
                self.instructions.append(f"STORE {result}")
                
            elif op == "ALLOC_ARRAY":
                # Push length, call ALLOC heap, store heap address in result
                self.instructions.extend(self.load_operand(arg1))
                self.instructions.append("ALLOC")
                self.instructions.append(f"STORE {result}")
                
            elif op == "ARRAY_SET":
                # result[arg2] = arg1
                # 1. Load array address (stored in result)
                self.instructions.extend(self.load_operand(result))
                # 2. Push index (stored in arg2)
                self.instructions.extend(self.load_operand(arg2))
                # 3. Load value (stored in arg1)
                self.instructions.extend(self.load_operand(arg1))
                # 4. Store value in heap array element
                self.instructions.append("ASTORE")
                
            elif op in ("+", "-", "*", "/", "%", "==", "!=", ">", "<", ">=", "<=", "and", "or"):
                # Binary operations: result = arg1 op arg2
                self.instructions.extend(self.load_operand(arg1))
                self.instructions.extend(self.load_operand(arg2))
                
                op_map = {
                    "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD",
                    "==": "EQ", "!=": "NEQ", ">": "GT", "<": "LT", ">=": "GTE", "<=": "LTE",
                    "and": "AND", "or": "OR"
                }
                vm_op = op_map.get(op, "ADD")
                self.instructions.append(vm_op)
                self.instructions.append(f"STORE {result}")
                
            elif op in ("not", "NEG"):
                # Unary operations: result = op arg1
                self.instructions.extend(self.load_operand(arg1))
                vm_op = "NOT" if op == "not" else "NEG"
                self.instructions.append(vm_op)
                self.instructions.append(f"STORE {result}")
                
            else:
                self.instructions.append(f"; OP NOT MAPPED: {op}")
                
        return self.instructions
