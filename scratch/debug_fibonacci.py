import sys
import os

# Insert main project path
sys.path.insert(0, r"c:\Users\PMLS\Desktop\New folder\semester 7\CC\Project_CC\Gui_AuraLang")

from lexer.lexer import Lexer
from ast.ast_generator import ASTParser
from semantic.semantic_analyzer import SemanticAnalyzer
from semantic.error_manager import CompilerErrorManager

def debug_fib():
    fib_code = """tarkeeb fib(n) {
    agar (n <= 1) {
        wapas n;
    }
    wapas fib(n - 1) + fib(n - 2);
}

rakho res = fib(6);
bol res; // prints 8"""

    error_manager = CompilerErrorManager()
    
    # 1. Lexical
    lexer = Lexer(fib_code, error_manager)
    tokens = lexer.tokenize()
    
    # 2. AST Parse
    parser = ASTParser(tokens, error_manager)
    ast_program = parser.parse()
    
    # 3. Semantic
    semantic_analyzer = SemanticAnalyzer()
    semantic_analyzer.error_manager = error_manager
    semantic_analyzer.analyze(ast_program)
    
    # Dump errors (totally clean text)
    print("--- Diagnostic Report ---")
    print(f"Total Errors Found: {len(error_manager.errors)}")
    for i, err in enumerate(error_manager.errors):
        print(f"Error {i+1}:")
        print(f"  Phase: {err.phase}")
        print(f"  Line: {err.line}")
        print(f"  Column: {err.column}")
        print(f"  Message: {err.message}")
        print(f"  Suggestion: {err.suggested_fix}")
        print(f"  Recovery: {err.recovery_action}")
        print("-" * 30)

if __name__ == "__main__":
    debug_fib()
