import sys
import os

# Insert main project path
sys.path.insert(0, r"c:\Users\PMLS\Desktop\New folder\semester 7\CC\Project_CC\Gui_AuraLang")

from lexer.lexer import Lexer
from ast.ast_generator import ASTParser
from semantic.semantic_analyzer import SemanticAnalyzer
from semantic.error_manager import CompilerErrorManager
from intermediate.ir_generator import IRGenerator
from optimizer.tac_optimizer import TACOptimizer
from codegen.target_codegen import TargetCodeGen
from vm.virtual_machine import VirtualMachine

def test_opt():
    source = """# AuraLang Optimization & Calculation Demo
rakho x = 10;
rakho y = 20;
rakho a = x + y;            # Constant folding -> 30
rakho b = x + y;            # CSE -> 30
rakho unused = 50 * x;      # Unused -> gets eliminated!
rakho final1 = a + 0;       # Algebraic simplification -> 30
rakho final2 = b * 1;       # Algebraic simplification -> 30
rakho final3 = a * 0;       # Multiplication by zero -> 0

bol final1;                 # Prints 30
bol final2;                 # Prints 30
bol final3;                 # Prints 0

# Dynamic calculation
rakho limit = 4;
rakho sum = 0;
ghumo i from 1 to limit {
    sum = sum + i;
}
bol sum;                    # Prints 10"""

    error_manager = CompilerErrorManager()
    
    # 1. Lexer
    lexer = Lexer(source, error_manager)
    tokens = lexer.tokenize()
    
    # 2. AST Parser
    parser = ASTParser(tokens, error_manager)
    ast_program = parser.parse()
    
    # 3. Semantic
    semantic = SemanticAnalyzer()
    semantic.error_manager = error_manager
    semantic.analyze(ast_program)
    
    if error_manager.has_errors():
        print("Compilation Failed!")
        for err in error_manager.errors:
            print(f"Error: {err.message} at line {err.line}")
        return
        
    # 4. IR
    ir = IRGenerator()
    ir.generate(ast_program)
    orig_tac = ir.tac_instructions
    
    # 5. Optimize
    opt = TACOptimizer()
    opt_quads = opt.optimize(ir.quadruples)
    opt_tac = TACOptimizer.to_tac_string(opt_quads)
    
    # 6. Codegen & VM
    codegen = TargetCodeGen()
    asm = codegen.generate(opt_quads)
    
    vm = VirtualMachine()
    vm.load_program(asm)
    vm.run()
    
    print("\n--- Summary ---")
    print(f"Original TAC lines: {len(orig_tac)}")
    print(f"Optimized TAC lines: {len(opt_tac)}")
    print(f"Reduced TAC lines: {len(orig_tac) - len(opt_tac)}")
    print(f"VM Console Outputs: {vm.console_output}")

if __name__ == "__main__":
    test_opt()
