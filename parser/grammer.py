grammar = {
    "Program": [["StmtList"]],
    
    "StmtList": [["Stmt", "StmtList"], ["ε"]],
    
    "Stmt": [
        ["Assignment"],
        ["Print"],
        ["IfStmt"]
    ],
    
    "Assignment": [["rakho", "id", "=", "Exp", ";"]],
    
    "Print": [["bol", "Exp", ";"]],
    
    "IfStmt": [["agar", "(", "Exp", ")", "{", "StmtList", "}", "ElsePart"]],
    
    "ElsePart": [["warna", "{", "StmtList", "}"], ["ε"]],
    
    "Exp": [["Term", "Exp'"]],
    
    "Exp'": [["+", "Term", "Exp'"], ["-", "Term", "Exp'"], ["ε"]],
    
    "Term": [["Factor", "Term'"]],
    
    "Term'": [["*", "Factor", "Term'"], ["/", "Factor", "Term'"], ["ε"]],
    
    "Factor": [
        ["(", "Exp", ")"],
        ["id"],
        ["num"]
    ]
}

# Terminal mapping from Lexer tokens to Grammar strings
TERMINALS = {
    "RAKHO": "rakho",
    "BOL": "bol",
    "AGAR": "agar",
    "WARNA": "warna",
    "IDENT": "id",
    "NUMBER": "num",
    "PLUS": "+",
    "MINUS": "-",
    "STAR": "*",
    "SLASH": "/",
    "ASSIGN": "=",
    "LPAREN": "(",
    "RPAREN": ")",
    "LBRACE": "{",
    "RBRACE": "}",
    "SEMI": ";",
    "EOF": "$"
}