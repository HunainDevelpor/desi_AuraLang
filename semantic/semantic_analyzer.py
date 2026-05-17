from ast.ast_generator import *
from typing import List, Dict, Any, Optional

class SemanticError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(f"Semantic Error at Line {line}: {message}")
        self.line = line
        self.message = message

class Symbol:
    def __init__(self, name: str, datatype: str, scope: str, line: int, address: str, value: Any = None):
        self.name = name
        self.datatype = datatype
        self.scope = scope
        self.line = line
        self.address = address
        self.value = value

class Environment:
    def __init__(self, name: str, parent: Optional['Environment'] = None):
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, name: str, symbol: Symbol):
        self.symbols[name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

class SemanticAnalyzer:
    def __init__(self, error_manager: Optional[Any] = None):
        self.global_env = Environment("Global")
        self.current_env = self.global_env
        self.symbols_list: List[Symbol] = []
        self.trace: List[str] = []
        self.errors: List[str] = []
        self.next_mem_address = 0x2000
        self.scope_counter = 0
        self.error_manager = error_manager

    def alloc_address(self) -> str:
        addr = hex(self.next_mem_address).upper().replace("X", "x")
        self.next_mem_address += 4
        return addr

    def enter_scope(self, prefix: str):
        self.scope_counter += 1
        scope_name = f"{prefix}_{self.scope_counter}"
        new_env = Environment(scope_name, parent=self.current_env)
        self.current_env = new_env
        self.trace.append(f"[Trace] Entered scope '{scope_name}'")

    def exit_scope(self):
        parent_name = self.current_env.parent.name if self.current_env.parent else "None"
        self.trace.append(f"[Trace] Exited scope '{self.current_env.name}' returning to '{parent_name}'")
        self.current_env = self.current_env.parent

    def log_trace(self, msg: str):
        self.trace.append(f"[Trace] {msg}")

    # ====================================================
    # TRAVERSAL ENTRY POINT
    # ====================================================

    def analyze(self, program: ProgramNode) -> bool:
        self.symbols_list = []
        self.trace = []
        self.errors = []
        self.next_mem_address = 0x2000
        
        self.log_trace("Starting semantic analysis...")
        try:
            self.visit(program)
            self.log_trace("Semantic analysis finished.")
            if self.error_manager and self.error_manager.has_errors():
                return False
            return len(self.errors) == 0
        except SemanticError as e:
            if self.error_manager:
                self.error_manager.log_error(
                    phase="Semantic",
                    line=e.line,
                    column=1,
                    message=e.message,
                    suggested_fix="",
                    recovery_action="Analysis aborted due to semantic error.",
                    is_fatal=False
                )
            self.errors.append(str(e))
            self.log_trace(f"[Error] Analysis aborted due to: {e.message}")
            return False
        except Exception as e:
            self.errors.append(f"Internal Semantic Error: {str(e)}")
            self.log_trace(f"[Error] Uncaught exception: {str(e)}")
            return False

    def visit(self, node: ASTNode):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node: ASTNode):
        raise Exception(f"Semantic Analyzer Visitor not defined for: {type(node).__name__}")

    # ====================================================
    # NODE VISITORS
    # ====================================================

    def visit_block(self, statements: List[StmtNode]):
        for stmt in statements:
            try:
                self.visit(stmt)
            except SemanticError as e:
                if self.error_manager:
                    self.error_manager.log_error(
                        phase="Semantic",
                        line=e.line,
                        column=1,
                        message=e.message,
                        suggested_fix="",
                        recovery_action="Skipped statement and continued checker.",
                        is_fatal=False
                    )
                self.errors.append(str(e))
                self.log_trace(f"[Error] {e.message}")

    def visit_ProgramNode(self, node: ProgramNode):
        self.visit_block(node.statements)

    def visit_VarDeclNode(self, node: VarDeclNode):
        # 1. Evaluate right-hand expression type
        expr_type = self.eval_type(node.value)
        
        # 2. Check duplicate declarations in current scope
        if node.name in self.current_env.symbols:
            raise SemanticError(f"Duplicate declaration: Variable '{node.name}' is already declared in scope '{self.current_env.name}'.", node.line)

        # 3. Create and store symbol
        addr = self.alloc_address()
        # Grab a mock static value for literals
        mock_val = None
        if isinstance(node.value, LiteralNode):
            mock_val = node.value.value
            
        sym = Symbol(
            name=node.name,
            datatype=expr_type,
            scope=self.current_env.name,
            line=node.line,
            address=addr,
            value=mock_val
        )
        self.current_env.define(node.name, sym)
        self.symbols_list.append(sym)
        
        self.log_trace(f"Declared '{node.name}' of type '{expr_type}' at line {node.line}. Memory: {addr}")

    def visit_AssignNode(self, node: AssignNode):
        # 1. Lookup variable symbol
        sym = self.current_env.lookup(node.name)
        if not sym:
            raise SemanticError(f"Undeclared variable: Cannot assign value to '{node.name}' because it has not been declared.", node.line)

        # 2. Evaluate right-hand expression type
        expr_type = self.eval_type(node.value)

        # 3. Type check assignment compatibility
        if sym.datatype != expr_type:
            # Allow int to float assignment, otherwise error
            if sym.datatype == "float" and expr_type == "num":
                pass
            else:
                raise SemanticError(f"Type mismatch: Cannot assign value of type '{expr_type}' to variable '{node.name}' of type '{sym.datatype}'.", node.line)

        # Update symbol compile-time value if literal
        if isinstance(node.value, LiteralNode):
            sym.value = node.value.value

        self.log_trace(f"Type checked assignment to '{node.name}' at line {node.line}. Success.")

    def visit_PrintNode(self, node: PrintNode):
        expr_type = self.eval_type(node.expr)
        self.log_trace(f"Type checked print 'bol' with argument type '{expr_type}' at line {node.line}")

    def visit_IfNode(self, node: IfNode):
        cond_type = self.eval_type(node.cond)
        if cond_type != "bool":
            raise SemanticError(f"Type mismatch: Condition in 'agar' must evaluate to type 'bool', but got '{cond_type}'.", node.line)
        
        # Enter block scope
        self.enter_scope("agar_block")
        self.visit_block(node.then_branch)
        self.exit_scope()
        
        if node.else_branch:
            self.enter_scope("warna_block")
            self.visit_block(node.else_branch)
            self.exit_scope()

    def visit_WhileNode(self, node: WhileNode):
        cond_type = self.eval_type(node.cond)
        if cond_type != "bool":
            raise SemanticError(f"Type mismatch: Condition in 'jabtak' loop must evaluate to type 'bool', but got '{cond_type}'.", node.line)

        self.enter_scope("jabtak_block")
        self.visit_block(node.body)
        self.exit_scope()

    def visit_ForNode(self, node: ForNode):
        start_t = self.eval_type(node.start_val)
        end_t = self.eval_type(node.end_val)
        
        if start_t not in ("num", "float") or end_t not in ("num", "float"):
            raise SemanticError(f"Type mismatch: Loop boundaries in 'ghumo' must be numeric. Got start '{start_t}', end '{end_t}'.", node.line)

        self.enter_scope("ghumo_block")
        # Define loop variable in nested scope
        addr = self.alloc_address()
        sym = Symbol(
            name=node.var,
            datatype="num",
            scope=self.current_env.name,
            line=node.line,
            address=addr,
            value=0
        )
        self.current_env.define(node.var, sym)
        self.symbols_list.append(sym)
        self.log_trace(f"Declared loop control variable '{node.var}' in body at line {node.line}. Memory: {addr}")

        self.visit_block(node.body)
        self.exit_scope()

    def visit_FuncDeclNode(self, node: FuncDeclNode):
        # 1. Define function name in current environment (Global) to allow calls and recursion
        if node.name in self.current_env.symbols:
            raise SemanticError(f"Duplicate declaration: Function/variable '{node.name}' already declared.", node.line)
            
        addr = self.alloc_address()
        sym = Symbol(
            name=node.name,
            datatype="function",
            scope=self.current_env.name,
            line=node.line,
            address=addr,
            value=f"params: {', '.join(node.params)}"
        )
        self.current_env.define(node.name, sym)
        self.symbols_list.append(sym)
        self.log_trace(f"Registered function '{node.name}' with address: {addr}")

        # 2. Enter function scope
        self.enter_scope(f"func_{node.name}")
        for param in node.params:
            p_addr = self.alloc_address()
            p_sym = Symbol(
                name=param,
                datatype="num", # default parameter type in untyped parser
                scope=self.current_env.name,
                line=node.line,
                address=p_addr,
                value=None
            )
            self.current_env.define(param, p_sym)
            self.symbols_list.append(p_sym)
            self.log_trace(f"Defined function parameter '{param}' in local function scope. Memory: {p_addr}")
            
        self.visit_block(node.body)
        self.exit_scope()

    def visit_ReturnNode(self, node: ReturnNode):
        expr_type = self.eval_type(node.expr)
        self.log_trace(f"Type checked 'wapas' return value of type '{expr_type}' at line {node.line}")

    # ====================================================
    # EXPRESSION TYPE EVALUATION RULES
    # ====================================================

    def eval_type(self, node: ExprNode) -> str:
        if isinstance(node, LiteralNode):
            return node.type_name
            
        if isinstance(node, VarRefNode):
            sym = self.current_env.lookup(node.name)
            if not sym:
                raise SemanticError(f"Undeclared variable: '{node.name}' is referenced but has not been declared.", node.line)
            self.log_trace(f"Resolved variable reference '{node.name}' to type '{sym.datatype}' (line {node.line}).")
            return sym.datatype
            
        if isinstance(node, ArrayNode):
            # Check all elements
            if node.elements:
                first_type = self.eval_type(node.elements[0])
                for i, el in enumerate(node.elements[1:]):
                    t = self.eval_type(el)
                    if t != first_type:
                        raise SemanticError(f"Array Type mismatch: Array elements must be of consistent type. Element {i+1} got '{t}' but expected '{first_type}'.", node.line)
                return f"array[{first_type}]"
            return "array[empty]"
            
        if isinstance(node, BinaryOpNode):
            left_t = self.eval_type(node.left)
            right_t = self.eval_type(node.right)
            
            # 1. Logical operations: and, or
            if node.op in ("and", "or"):
                if left_t != "bool" or right_t != "bool":
                    raise SemanticError(f"Logical error: Operator '{node.op}' requires boolean operands. Got '{left_t}' and '{right_t}'.", node.line)
                return "bool"
                
            # 2. Relational operations: ==, !=, >, <, >=, <=
            if node.op in ("==", "!=", ">", "<", ">=", "<="):
                # Check compatibility
                is_num1 = left_t in ("num", "float")
                is_num2 = right_t in ("num", "float")
                if is_num1 != is_num2:
                    raise SemanticError(f"Comparison error: Cannot compare numeric value '{left_t}' with non-numeric value '{right_t}'.", node.line)
                if left_t == "string" and right_t != "string":
                     raise SemanticError(f"Comparison error: Cannot compare string with '{right_t}'.", node.line)
                return "bool"
                
            # 3. Arithmetic operations: +, -, *, /, %
            if node.op in ("+", "-", "*", "/", "%"):
                # Special rule: string + string is allowed (concatenation)
                if node.op == "+" and (left_t == "string" or right_t == "string"):
                    return "string"
                    
                # Standard math checks
                if left_t not in ("num", "float") or right_t not in ("num", "float"):
                    raise SemanticError(f"Arithmetic error: Operator '{node.op}' requires numeric operands. Got '{left_t}' and '{right_t}'.", node.line)
                
                # Coercion: if either is float, result is float
                if left_t == "float" or right_t == "float":
                    return "float"
                return "num"
                
        if isinstance(node, UnaryOpNode):
            inner_t = self.eval_type(node.expr)
            if node.op == "not":
                if inner_t != "bool":
                    raise SemanticError(f"Unary error: Operator 'not' requires boolean operand, got '{inner_t}'.", node.line)
                return "bool"
            elif node.op == "-":
                if inner_t not in ("num", "float"):
                    raise SemanticError(f"Unary error: Negation operator '-' requires numeric operand, got '{inner_t}'.", node.line)
                return inner_t
                
        if isinstance(node, FuncCallNode):
            sym = self.current_env.lookup(node.name)
            if not sym:
                raise SemanticError(f"Undeclared function: Function '{node.name}' is called but has not been defined.", node.line)
            if sym.datatype != "function":
                raise SemanticError(f"Invalid call: '{node.name}' is declared as variable '{sym.datatype}', not a function.", node.line)
            
            # Simple signature checking
            # Evaluate types of arguments
            for arg in node.args:
                self.eval_type(arg)
                
            self.log_trace(f"Type checked call to function '{node.name}' at line {node.line}")
            # Untyped functions return num
            return "num"
            
        raise Exception(f"Semantic evaluation not implemented for expression node: {type(node).__name__}")
