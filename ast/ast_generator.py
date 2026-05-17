from lexer.tokens import TokenType, Token
from typing import List, Any, Dict, Optional

# ====================================================
# AST NODE ABSTRACTIONS
# ====================================================

class ASTNode:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError()

class StmtNode(ASTNode):
    pass

class ExprNode(ASTNode):
    pass

class ProgramNode(ASTNode):
    def __init__(self, statements: List[StmtNode]):
        self.statements = statements

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": "Program",
            "children": [stmt.to_dict() for stmt in self.statements]
        }

class VarDeclNode(StmtNode):
    def __init__(self, name: str, value: ExprNode, line: int):
        self.name = name
        self.value = value
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": f"Decl (rakho {self.name})",
            "children": [self.value.to_dict()]
        }

class AssignNode(StmtNode):
    def __init__(self, name: str, value: ExprNode, line: int):
        self.name = name
        self.value = value
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": f"Assign ({self.name} =)",
            "children": [self.value.to_dict()]
        }

class PrintNode(StmtNode):
    def __init__(self, expr: ExprNode, line: int):
        self.expr = expr
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": "Print (bol)",
            "children": [self.expr.to_dict()]
        }

class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_branch: List[StmtNode], else_branch: List[StmtNode], line: int):
        self.cond = cond
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        children = [self.cond.to_dict()]
        
        then_children = [s.to_dict() for s in self.then_branch]
        then_node = {"name": "Then Block", "children": then_children}
        children.append(then_node)
        
        if self.else_branch:
            else_children = [s.to_dict() for s in self.else_branch]
            else_node = {"name": "Else Block", "children": else_children}
            children.append(else_node)
            
        return {
            "name": "If (agar)",
            "children": children
        }

class WhileNode(StmtNode):
    def __init__(self, cond: ExprNode, body: List[StmtNode], line: int):
        self.cond = cond
        self.body = body
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        body_children = [s.to_dict() for s in self.body]
        return {
            "name": "While (jabtak)",
            "children": [
                self.cond.to_dict(),
                {"name": "Body", "children": body_children}
            ]
        }

class ForNode(StmtNode):
    def __init__(self, var: str, start_val: ExprNode, end_val: ExprNode, body: List[StmtNode], line: int):
        self.var = var
        self.start_val = start_val
        self.end_val = end_val
        self.body = body
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        body_children = [s.to_dict() for s in self.body]
        return {
            "name": f"For (ghumo {self.var})",
            "children": [
                {"name": "Range", "children": [self.start_val.to_dict(), self.end_val.to_dict()]},
                {"name": "Body", "children": body_children}
            ]
        }

class FuncDeclNode(StmtNode):
    def __init__(self, name: str, params: List[str], body: List[StmtNode], line: int):
        self.name = name
        self.params = params
        self.body = body
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        body_children = [s.to_dict() for s in self.body]
        param_nodes = [{"name": f"Param: {p}", "children": []} for p in self.params]
        return {
            "name": f"FuncDecl ({self.name})",
            "children": [
                {"name": "Params", "children": param_nodes},
                {"name": "Body", "children": body_children}
            ]
        }

class ReturnNode(StmtNode):
    def __init__(self, expr: ExprNode, line: int):
        self.expr = expr
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": "Return (wapas)",
            "children": [self.expr.to_dict()]
        }

# Expressions
class ArrayNode(ExprNode):
    def __init__(self, elements: List[ExprNode], line: int):
        self.elements = elements
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": "Array Literal []",
            "children": [el.to_dict() for el in self.elements]
        }

class BinaryOpNode(ExprNode):
    def __init__(self, op: str, left: ExprNode, right: ExprNode, line: int):
        self.op = op
        self.left = left
        self.right = right
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": f"Op ({self.op})",
            "children": [self.left.to_dict(), self.right.to_dict()]
        }

class UnaryOpNode(ExprNode):
    def __init__(self, op: str, expr: ExprNode, line: int):
        self.op = op
        self.expr = expr
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": f"Unary ({self.op})",
            "children": [self.expr.to_dict()]
        }

class LiteralNode(ExprNode):
    def __init__(self, value: Any, type_name: str, line: int):
        self.value = value
        self.type_name = type_name # 'num', 'float', 'bool', 'string'
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": f"Literal: {self.value} ({self.type_name})",
            "children": []
        }

class VarRefNode(ExprNode):
    def __init__(self, name: str, line: int):
        self.name = name
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": f"VarRef ({self.name})",
            "children": []
        }

class FuncCallNode(ExprNode):
    def __init__(self, name: str, args: List[ExprNode], line: int):
        self.name = name
        self.args = args
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": f"Call ({self.name})",
            "children": [arg.to_dict() for arg in self.args]
        }


from parser.error_recovery import SyntaxRecovery

# ====================================================
# AST PARSER IMPLEMENTATION (RECURSIVE DESCENT)
# ====================================================

class ASTParser:
    def __init__(self, tokens: List[Token], error_manager: Optional[Any] = None):
        self.tokens = tokens
        self.pos = 0
        self.error_manager = error_manager

    def _peek(self) -> Token:
        if self._at_end():
            return Token(TokenType.EOF, None, -1, -1)
        return self.tokens[self.pos]

    def _at_end(self) -> bool:
        return self.pos >= len(self.tokens) or self.tokens[self.pos].type == TokenType.EOF

    def _previous(self) -> Token:
        return self.tokens[self.pos - 1]

    def _advance(self) -> Token:
        if not self._at_end():
            self.pos += 1
        return self._previous()

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, ttype: TokenType) -> bool:
        if self._at_end():
            return False
        return self._peek().type == ttype

    def _consume(self, ttype: TokenType, err_msg: str) -> Token:
        if self._check(ttype):
            return self._advance()
        raise Exception(f"Parser Error (Line {self._peek().line}, Col {self._peek().col}): {err_msg}")

    # ---------- PARSE RULES ----------

    def parse(self) -> ProgramNode:
        statements = []
        while not self._at_end():
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except Exception as e:
                if self.error_manager:
                    # Capture line/col from current peek token
                    curr = self._peek()
                    line = curr.line if curr else -1
                    col = curr.col if curr else -1
                    
                    # Clean the error message from standard wrapper text
                    clean_msg = str(e).replace("Exception: ", "")
                    
                    self.error_manager.log_error(
                        phase="Syntax",
                        line=line,
                        column=col,
                        message=clean_msg,
                        suggested_fix="",
                        recovery_action="Synchronized using synchronization tokens.",
                        is_fatal=False
                    )
                    
                    # Synchronize the parser to continue compiling subsequent lines
                    self.pos = SyntaxRecovery.synchronize(self.tokens, self.pos)
                else:
                    raise e
        return ProgramNode(statements)

    def parse_statement(self) -> Optional[StmtNode]:
        if self._match(TokenType.RAKHO):
            return self.parse_var_decl()
        if self._match(TokenType.BOL):
            return self.parse_print()
        if self._match(TokenType.AGAR):
            return self.parse_if()
        if self._match(TokenType.JABTAK):
            return self.parse_while()
        if self._match(TokenType.GHUMO):
            return self.parse_for()
        if self._match(TokenType.TARKEEB):
            return self.parse_func_decl()
        if self._match(TokenType.WAPAS):
            return self.parse_return()
            
        # Try assignment or standalone expression statement
        if self._check(TokenType.IDENT):
            # peek ahead to check for '='
            next_t = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_t and next_t.type == TokenType.ASSIGN:
                return self.parse_assign()
                
        # Standalone expression
        expr = self.parse_expr()
        self._consume(TokenType.SEMI, "Expected ';' after expression statement.")
        return expr

    def parse_var_decl(self) -> StmtNode:
        ident_tok = self._consume(TokenType.IDENT, "Expected identifier name after 'rakho'.")
        self._consume(TokenType.ASSIGN, "Expected '=' in variable declaration.")
        
        # Check if array declaration
        if self._match(TokenType.LBRACKET):
            expr = self.parse_array_literal()
        else:
            expr = self.parse_expr()
            
        self._consume(TokenType.SEMI, "Expected ';' at the end of declaration.")
        return VarDeclNode(ident_tok.value, expr, ident_tok.line)

    def parse_assign(self) -> StmtNode:
        ident_tok = self._consume(TokenType.IDENT, "Expected identifier.")
        self._consume(TokenType.ASSIGN, "Expected '=' in assignment.")
        expr = self.parse_expr()
        self._consume(TokenType.SEMI, "Expected ';' after assignment.")
        return AssignNode(ident_tok.value, expr, ident_tok.line)

    def parse_array_literal(self) -> ExprNode:
        line = self._previous().line
        elements = []
        if not self._check(TokenType.RBRACKET):
            elements.append(self.parse_expr())
            while self._match(TokenType.COMMA):
                elements.append(self.parse_expr())
        self._consume(TokenType.RBRACKET, "Expected ']' at the end of array literal.")
        return ArrayNode(elements, line)

    def parse_print(self) -> StmtNode:
        line = self._previous().line
        expr = self.parse_expr()
        self._consume(TokenType.SEMI, "Expected ';' after print value.")
        return PrintNode(expr, line)

    def parse_if(self) -> StmtNode:
        line = self._previous().line
        self._consume(TokenType.LPAREN, "Expected '(' after 'agar'.")
        cond = self.parse_expr()
        self._consume(TokenType.RPAREN, "Expected ')' after condition.")
        
        self._consume(TokenType.LBRACE, "Expected '{' to start 'then' block.")
        then_branch = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            stmt = self.parse_statement()
            if stmt: then_branch.append(stmt)
        self._consume(TokenType.RBRACE, "Expected '}' to close 'then' block.")
        
        else_branch = []
        if self._match(TokenType.WARNA):
            self._consume(TokenType.LBRACE, "Expected '{' to start 'warna' block.")
            while not self._check(TokenType.RBRACE) and not self._at_end():
                stmt = self.parse_statement()
                if stmt: else_branch.append(stmt)
            self._consume(TokenType.RBRACE, "Expected '}' to close 'warna' block.")
            
        return IfNode(cond, then_branch, else_branch, line)

    def parse_while(self) -> StmtNode:
        line = self._previous().line
        self._consume(TokenType.LPAREN, "Expected '(' after 'jabtak'.")
        cond = self.parse_expr()
        self._consume(TokenType.RPAREN, "Expected ')' after condition.")
        
        self._consume(TokenType.LBRACE, "Expected '{' to start 'jabtak' loop body.")
        body = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            stmt = self.parse_statement()
            if stmt: body.append(stmt)
        self._consume(TokenType.RBRACE, "Expected '}' to close 'jabtak' loop body.")
        
        return WhileNode(cond, body, line)

    def parse_for(self) -> StmtNode:
        line = self._previous().line
        ident_tok = self._consume(TokenType.IDENT, "Expected loop variable name after 'ghumo'.")
        self._consume(TokenType.FROM, "Expected 'from' in for loop.")
        start_val = self.parse_expr()
        self._consume(TokenType.TO, "Expected 'to' in for loop.")
        end_val = self.parse_expr()
        
        self._consume(TokenType.LBRACE, "Expected '{' to start loop body.")
        body = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            stmt = self.parse_statement()
            if stmt: body.append(stmt)
        self._consume(TokenType.RBRACE, "Expected '}' to close loop body.")
        
        return ForNode(ident_tok.value, start_val, end_val, body, line)

    def parse_func_decl(self) -> StmtNode:
        line = self._previous().line
        name_tok = self._consume(TokenType.IDENT, "Expected function name after 'tarkeeb'.")
        self._consume(TokenType.LPAREN, "Expected '(' for parameters list.")
        params = []
        if not self._check(TokenType.RPAREN):
            p_tok = self._consume(TokenType.IDENT, "Expected parameter identifier.")
            params.append(p_tok.value)
            while self._match(TokenType.COMMA):
                p_tok = self._consume(TokenType.IDENT, "Expected parameter identifier.")
                params.append(p_tok.value)
        self._consume(TokenType.RPAREN, "Expected ')' after parameters list.")
        
        self._consume(TokenType.LBRACE, "Expected '{' to start function body.")
        body = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            stmt = self.parse_statement()
            if stmt: body.append(stmt)
        self._consume(TokenType.RBRACE, "Expected '}' to close function body.")
        
        return FuncDeclNode(name_tok.value, params, body, line)

    def parse_return(self) -> StmtNode:
        line = self._previous().line
        expr = self.parse_expr()
        self._consume(TokenType.SEMI, "Expected ';' after return value.")
        return ReturnNode(expr, line)

    # ---------- EXPRESSION PARSING (PRECEDENCE) ----------

    def parse_expr(self) -> ExprNode:
        return self.parse_logical_or()

    def parse_logical_or(self) -> ExprNode:
        expr = self.parse_logical_and()
        while self._match(TokenType.OR):
            op = self._previous().value or "or"
            right = self.parse_logical_and()
            expr = BinaryOpNode(op, expr, right, self._previous().line)
        return expr

    def parse_logical_and(self) -> ExprNode:
        expr = self.parse_comparison()
        while self._match(TokenType.AND):
            op = self._previous().value or "and"
            right = self.parse_comparison()
            expr = BinaryOpNode(op, expr, right, self._previous().line)
        return expr

    def parse_comparison(self) -> ExprNode:
        expr = self.parse_term()
        while self._match(TokenType.EQ, TokenType.NEQ, TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE):
            op_tok = self._previous()
            op = op_tok.type.name
            if op_tok.value: op = op_tok.value
            else:
                op_map = {
                    TokenType.EQ: "==", TokenType.NEQ: "!=",
                    TokenType.GT: ">", TokenType.LT: "<",
                    TokenType.GTE: ">=", TokenType.LTE: "<="
                }
                op = op_map.get(op_tok.type, "==")
            right = self.parse_term()
            expr = BinaryOpNode(op, expr, right, op_tok.line)
        return expr

    def parse_term(self) -> ExprNode:
        expr = self.parse_factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op_tok = self._previous()
            op = "+" if op_tok.type == TokenType.PLUS else "-"
            right = self.parse_factor()
            expr = BinaryOpNode(op, expr, right, op_tok.line)
        return expr

    def parse_factor(self) -> ExprNode:
        expr = self.parse_unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_tok = self._previous()
            op_map = {TokenType.STAR: "*", TokenType.SLASH: "/", TokenType.PERCENT: "%"}
            op = op_map[op_tok.type]
            right = self.parse_unary()
            expr = BinaryOpNode(op, expr, right, op_tok.line)
        return expr

    def parse_unary(self) -> ExprNode:
        if self._match(TokenType.NOT, TokenType.MINUS):
            op_tok = self._previous()
            op = "not" if op_tok.type == TokenType.NOT else "-"
            expr = self.parse_unary()
            return UnaryOpNode(op, expr, op_tok.line)
        return self.parse_primary()

    def parse_primary(self) -> ExprNode:
        if self._match(TokenType.NUMBER):
            val = self._previous().value
            t = "num" if isinstance(val, int) else "float"
            return LiteralNode(val, t, self._previous().line)
            
        if self._match(TokenType.STRING):
            return LiteralNode(self._previous().value, "string", self._previous().line)
            
        if self._match(TokenType.SAHI, TokenType.GALAT):
            return LiteralNode(self._previous().value, "bool", self._previous().line)
            
        if self._match(TokenType.IDENT):
            ident_tok = self._previous()
            # Check for function call
            if self._match(TokenType.LPAREN):
                args = []
                if not self._check(TokenType.RPAREN):
                    args.append(self.parse_expr())
                    while self._match(TokenType.COMMA):
                        args.append(self.parse_expr())
                self._consume(TokenType.RPAREN, "Expected ')' after arguments list.")
                return FuncCallNode(ident_tok.value, args, ident_tok.line)
            return VarRefNode(ident_tok.value, ident_tok.line)
            
        if self._match(TokenType.LPAREN):
            expr = self.parse_expr()
            self._consume(TokenType.RPAREN, "Expected ')' after grouped expression.")
            return expr
            
        raise Exception(f"Parser Error (Line {self._peek().line}, Col {self._peek().col}): Unexpected token '{self._peek().type.name}'.")
