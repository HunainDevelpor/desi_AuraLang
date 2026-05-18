import sys
import os

# Insert main project path
sys.path.insert(0, r"c:\Users\PMLS\Desktop\New folder\semester 7\CC\Project_CC\Gui_AuraLang")

import re
from lexer.lexer import Lexer
from lexer.tokens import TokenType
from semantic.error_manager import CompilerErrorManager

class MockApp:
    class MockEditor:
        def __init__(self, code):
            self.code = code
        class MockText:
            def __init__(self, code):
                self.code = code
            def get(self, start, end):
                return self.code
        @property
        def editor(self):
            return self.MockText(self.code)
    def __init__(self, code):
        self.code_editor = self.MockEditor(code)

def get_lexeme_from_code(app, selection):
    default_inputs = {
        "Identifier": "x_var",
        "Number (Int/Float)": "30",
        "String Literal": '"AuraLang"',
        "Comment": "# desi_comment"
    }
    
    if not app or not hasattr(app, "code_editor"):
        return default_inputs.get(selection)
        
    code = app.code_editor.editor.get("1.0", "end")
    
    try:
        err_mgr = CompilerErrorManager()
        lexer = Lexer(code, err_mgr)
        tokens = lexer.tokenize()
    except Exception as e:
        print(f"Lexer failed: {e}")
        tokens = []
        
    if selection == "Identifier":
        idents = [t.value for t in tokens if t.type == TokenType.IDENT]
        if idents:
            return idents[0]
        idents_re = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", code)
        keywords = {"rakho", "bol", "agar", "warna", "ghumo", "jabtak", "tarkeeb", "wapas", "sahi", "galat", "and", "or", "not", "from", "to"}
        idents_re = [x for x in idents_re if x not in keywords]
        if idents_re:
            return idents_re[0]
            
    elif selection == "Number (Int/Float)":
        nums = [str(t.value) for t in tokens if t.type == TokenType.NUMBER]
        if nums:
            return nums[0]
        nums_re = re.findall(r"\b\d+(?:\.\d+)?\b", code)
        if nums_re:
            return nums_re[0]
            
    elif selection == "String Literal":
        strings = [f'"{t.value}"' for t in tokens if t.type == TokenType.STRING]
        if strings:
            return strings[0]
        strings_re = re.findall(r'"[^"\n]*"', code)
        if strings_re:
            return strings_re[0]
            
    elif selection == "Comment":
        comments_re = re.findall(r"(?:#|//).*$", code, re.MULTILINE)
        if comments_re:
            return comments_re[0].strip()
            
    return default_inputs.get(selection)

def run_test():
    code = """# Dynamic test comment
rakho count = 42;
rakho name = "AuraVisuals";
// Another comment
"""
    app = MockApp(code)
    
    print("Testing extraction from AuraLang code:")
    print(f"Identifier: {get_lexeme_from_code(app, 'Identifier')}")
    print(f"Number (Int/Float): {get_lexeme_from_code(app, 'Number (Int/Float)')}")
    print(f"String Literal: {get_lexeme_from_code(app, 'String Literal')}")
    print(f"Comment: {get_lexeme_from_code(app, 'Comment')}")

if __name__ == "__main__":
    run_test()
