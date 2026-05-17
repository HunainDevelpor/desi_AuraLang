from ast.ast_generator import *
from typing import List, Dict, Any, Tuple

class Quadruple:
    def __init__(self, op: str, arg1: str, arg2: str, result: str, line: int = 1):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.line = line

    def to_tuple(self) -> Tuple[str, str, str, str]:
        return (self.op, self.arg1, self.arg2, self.result)

class Triple:
    def __init__(self, index: int, op: str, arg1: str, arg2: str):
        self.index = index
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    def to_tuple(self) -> Tuple[str, str, str, str]:
        return (f"({self.index})", self.op, self.arg1, self.arg2)

class BasicBlock:
    def __init__(self, id_num: int):
        self.id = id_num
        self.instructions: List[str] = []
        self.successors: List[int] = [] # block IDs
        self.predecessors: List[int] = [] # block IDs
        self.label: str = "" # Label of block start if any

class IRGenerator:
    def __init__(self):
        self.tac_instructions: List[str] = []
        self.quadruples: List[Quadruple] = []
        self.triples: List[Triple] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.triple_counter = 0
        self.current_line = 1

    def new_temp(self) -> str:
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def new_label(self) -> str:
        l = f"L{self.label_counter}"
        self.label_counter += 1
        return l

    def emit(self, instr_str: str, op: str, arg1: str, arg2: str, result: str):
        self.tac_instructions.append(instr_str)
        self.quadruples.append(Quadruple(op, arg1, arg2, result, self.current_line))
        self.triples.append(Triple(self.triple_counter, op, arg1, arg2))
        self.triple_counter += 1

    # ====================================================
    # COMPILATION TO TAC
    # ====================================================

    def generate(self, program: ProgramNode):
        self.tac_instructions = []
        self.quadruples = []
        self.triples = []
        self.temp_counter = 0
        self.label_counter = 0
        self.triple_counter = 0
        self.current_line = 1
        
        self.visit(program)

    def visit(self, node: ASTNode) -> Any:
        if hasattr(node, "line") and getattr(node, "line") is not None:
            self.current_line = node.line
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        raise Exception(f"IR Generator Visitor not defined for: {type(node).__name__}")

    # ---------- STATEMENT VISITORS ----------

    def visit_ProgramNode(self, node: ProgramNode):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDeclNode(self, node: VarDeclNode):
        val_expr = self.visit(node.value)
        self.emit(f"{node.name} = {val_expr}", "=", val_expr, "", node.name)

    def visit_AssignNode(self, node: AssignNode):
        val_expr = self.visit(node.value)
        self.emit(f"{node.name} = {val_expr}", "=", val_expr, "", node.name)

    def visit_PrintNode(self, node: PrintNode):
        val_expr = self.visit(node.expr)
        self.emit(f"print {val_expr}", "PRINT", val_expr, "", "")

    def visit_IfNode(self, node: IfNode):
        l_else = self.new_label()
        l_end = self.new_label()
        
        cond_val = self.visit(node.cond)
        self.emit(f"if_false {cond_val} goto {l_else}", "IF_FALSE", cond_val, "", l_else)
        
        for stmt in node.then_branch:
            self.visit(stmt)
        self.emit(f"goto {l_end}", "GOTO", "", "", l_end)
        
        self.emit(f"label {l_else}", "LABEL", "", "", l_else)
        for stmt in node.else_branch:
            self.visit(stmt)
            
        self.emit(f"label {l_end}", "LABEL", "", "", l_end)

    def visit_WhileNode(self, node: WhileNode):
        l_start = self.new_label()
        l_end = self.new_label()
        
        self.emit(f"label {l_start}", "LABEL", "", "", l_start)
        cond_val = self.visit(node.cond)
        
        self.emit(f"if_false {cond_val} goto {l_end}", "IF_FALSE", cond_val, "", l_end)
        for stmt in node.body:
            self.visit(stmt)
            
        self.emit(f"goto {l_start}", "GOTO", "", "", l_start)
        self.emit(f"label {l_end}", "LABEL", "", "", l_end)

    def visit_ForNode(self, node: ForNode):
        l_start = self.new_label()
        l_end = self.new_label()
        
        start_val = self.visit(node.start_val)
        end_val = self.visit(node.end_val)
        
        # 1. Initialize loop control var
        self.emit(f"{node.var} = {start_val}", "=", start_val, "", node.var)
        self.emit(f"label {l_start}", "LABEL", "", "", l_start)
        
        # 2. Check boundary condition
        t_cond = self.new_temp()
        self.emit(f"{t_cond} = {node.var} <= {end_val}", "<=", node.var, end_val, t_cond)
        self.emit(f"if_false {t_cond} goto {l_end}", "IF_FALSE", t_cond, "", l_end)
        
        # 3. Body
        for stmt in node.body:
            self.visit(stmt)
            
        # 4. Increment and jump back
        self.emit(f"{node.var} = {node.var} + 1", "+", node.var, "1", node.var)
        self.emit(f"goto {l_start}", "GOTO", "", "", l_start)
        self.emit(f"label {l_end}", "LABEL", "", "", l_end)

    def visit_FuncDeclNode(self, node: FuncDeclNode):
        self.emit(f"label func_{node.name}", "LABEL", "", "", f"func_{node.name}")
        for stmt in node.body:
            self.visit(stmt)
        # Ensure return if none defined
        self.emit("return 0", "RETURN", "0", "", "")

    def visit_ReturnNode(self, node: ReturnNode):
        val_expr = self.visit(node.expr)
        self.emit(f"return {val_expr}", "RETURN", val_expr, "", "")

    # ---------- EXPRESSION VISITORS ----------

    def visit_ArrayNode(self, node: ArrayNode) -> str:
        # Array literal syntax. e.g. [1, 2, 3] -> allocates array pointer and assigns elements
        t_arr = self.new_temp()
        length = len(node.elements)
        self.emit(f"{t_arr} = alloc_array {length}", "ALLOC_ARRAY", str(length), "", t_arr)
        
        for i, el in enumerate(node.elements):
            val_el = self.visit(el)
            self.emit(f"{t_arr}[{i}] = {val_el}", "ARRAY_SET", val_el, str(i), t_arr)
            
        return t_arr

    def visit_BinaryOpNode(self, node: BinaryOpNode) -> str:
        l_val = self.visit(node.left)
        r_val = self.visit(node.right)
        t = self.new_temp()
        self.emit(f"{t} = {l_val} {node.op} {r_val}", node.op, l_val, r_val, t)
        return t

    def visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        val = self.visit(node.expr)
        t = self.new_temp()
        self.emit(f"{t} = {node.op} {val}", node.op, val, "", t)
        return t

    def visit_LiteralNode(self, node: LiteralNode) -> str:
        if node.type_name == "string":
            # quote string value in TAC
            return f'"{node.value}"'
        return str(node.value)

    def visit_VarRefNode(self, node: VarRefNode) -> str:
        return node.name

    def visit_FuncCallNode(self, node: FuncCallNode) -> str:
        # Push arguments in reverse order (standard call stack convention)
        for arg in reversed(node.args):
            val_arg = self.visit(arg)
            self.emit(f"push {val_arg}", "PUSH", val_arg, "", "")
            
        t = self.new_temp()
        self.emit(f"{t} = call {node.name}, {len(node.args)}", "CALL", node.name, str(len(node.args)), t)
        return t


    # ====================================================
    # BASIC BLOCKS & CONTROL FLOW GRAPH GENERATION
    # ====================================================

    def build_cfg(self) -> Dict[int, BasicBlock]:
        # 1. Identify Leaders
        leaders = set()
        if self.tac_instructions:
            leaders.add(0) # first instruction is always a leader

        # Identify targets of jumps and the sequential instruction following jumps
        for i, quadruple in enumerate(self.quadruples):
            if quadruple.op in ("GOTO", "IF_FALSE"):
                # The target label is a leader
                target_label = quadruple.result
                for j, q in enumerate(self.quadruples):
                    if q.op == "LABEL" and q.result == target_label:
                        leaders.add(j)
                        break
                # The instruction following the jump is a leader
                if i + 1 < len(self.quadruples):
                    leaders.add(i + 1)
            elif quadruple.op == "LABEL":
                leaders.add(i)

        sorted_leaders = sorted(list(leaders))
        
        # 2. Partition into Basic Blocks
        blocks: Dict[int, BasicBlock] = {}
        block_id_map: Dict[int, int] = {} # instruction index -> block ID
        
        for idx, leader_idx in enumerate(sorted_leaders):
            block = BasicBlock(idx + 1)
            start = leader_idx
            end = sorted_leaders[idx + 1] if idx + 1 < len(sorted_leaders) else len(self.tac_instructions)
            
            for k in range(start, end):
                block.instructions.append(self.tac_instructions[k])
                block_id_map[k] = block.id
                
            # If block starts with a label instruction, capture the label
            first_q = self.quadruples[start]
            if first_q.op == "LABEL":
                block.label = first_q.result
                
            blocks[block.id] = block

        # 3. Establish links (Successors and Predecessors)
        for block in blocks.values():
            # Find the last instruction of this block
            last_instr_idx = -1
            for k, b_id in block_id_map.items():
                if b_id == block.id:
                    last_instr_idx = max(last_instr_idx, k)
                    
            if last_instr_idx == -1:
                continue
                
            last_q = self.quadruples[last_instr_idx]
            
            if last_q.op == "GOTO":
                # Only successor is target block
                target_label = last_q.result
                for target_b in blocks.values():
                    if target_b.label == target_label:
                        block.successors.append(target_b.id)
                        target_b.predecessors.append(block.id)
                        break
            elif last_q.op == "IF_FALSE":
                # Successor 1: target block of jump
                target_label = last_q.result
                for target_b in blocks.values():
                    if target_b.label == target_label:
                        block.successors.append(target_b.id)
                        target_b.predecessors.append(block.id)
                        break
                # Successor 2: sequential fallthrough block
                next_block_id = block.id + 1
                if next_block_id in blocks:
                    block.successors.append(next_block_id)
                    blocks[next_block_id].predecessors.append(block.id)
            else:
                # Sequential fallthrough block
                next_block_id = block.id + 1
                if next_block_id in blocks:
                    block.successors.append(next_block_id)
                    blocks[next_block_id].predecessors.append(block.id)
                    
        return blocks
