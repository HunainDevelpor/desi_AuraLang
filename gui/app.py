import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import random

# Imports from existing phases
from lexer.lexer import Lexer
from parser.grammer import grammar, TERMINALS
from parser.first_follow import FirstFollow
from parser.parsing_table import ParsingTable
from parser.ll1_parser import LL1Parser
from symbol_table.symbol_table import SymbolTable
from .tree_viz import TreeVisualizer

# Imports from new educational parsing abstraction layer
from parser.parser_manager import ParserManager
from gui.lr_dfa_viz import LrDfaVisualizer
from gui.parser_cmp import ParserComparisonDashboard

# Imports from newly implemented backend phases
from gui.dfa_viz import DfaVisualizer
from ast.ast_generator import ASTParser
from semantic.semantic_analyzer import SemanticAnalyzer
from intermediate.ir_generator import IRGenerator
from gui.ir_viz import IrFlowVisualizer
from optimizer.tac_optimizer import TACOptimizer
from codegen.target_codegen import TargetCodeGen
from vm.virtual_machine import VirtualMachine
from gui.vm_viz import VmDashboard
from runtime.debugger import InteractiveDebugger
from settings.theme_manager import ThemeManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

LANGUAGE_GUIDE = [
    {"word": "rakho", "original": "let / var", "meaning": "Variable Declaration", "example": "rakho x = 10;", "desc": "Used to declare a new variable and assign it a value."},
    {"word": "bol", "original": "print", "meaning": "Print Output", "example": "bol \"Hello\";", "desc": "Outputs values or text to the console display."},
    {"word": "agar", "original": "if", "meaning": "If Condition", "example": "agar (x > 5) {\n    bol 1;\n} warna {\n    bol 0;\n}", "desc": "Starts a conditional block that runs if the expression is true."},
    {"word": "warna", "original": "else", "meaning": "Else Block", "example": "warna { ... }", "desc": "Optional block after 'agar' that runs if condition is false."},
    {"word": "jabtak", "original": "while", "meaning": "While Loop", "example": "jabtak (x < 10) {\n    x = x + 1;\n}", "desc": "Repeats the code block as long as the condition holds."},
    {"word": "ghumo", "original": "for", "meaning": "For Loop", "example": "ghumo i from 1 to 5 {\n    bol i;\n}", "desc": "Iterates an identifier over a specified range."},
    {"word": "sahi", "original": "true", "meaning": "Boolean True", "example": "rakho flag = sahi;", "desc": "Literal value representing logical truth."},
    {"word": "galat", "original": "false", "meaning": "Boolean False", "example": "rakho flag = galat;", "desc": "Literal value representing logical falsehood."},
    {"word": "tarkeeb", "original": "function / def", "meaning": "Function/Method", "example": "tarkeeb add(a, b) {\n    wapas a + b;\n}\n\nrakho res = add(5, 10);\nbol res;", "desc": "Defines a reusable block of logic with scope-aware parameters."},
    {"word": "wapas", "original": "return", "meaning": "Return Statement", "example": "wapas x;", "desc": "Returns a value from a function."},
]

class CompilerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Desi AuraLang — Ultimate Educational Compiler Visualizer")
        self.geometry("1600x990")

        # Set up grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------
        # 1. SIDEBAR NAVIGATION
        # ----------------------------------------------------
        self.sidebar_canvas_frame = ctk.CTkScrollableFrame(self, width=280, corner_radius=0, fg_color="#0a0a0a")
        self.sidebar_canvas_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_canvas_frame, text="AURA ENGINE", 
                                      font=ctk.CTkFont(size=26, weight="bold"), text_color="#3498db")
        self.logo_label.pack(pady=(30, 20))

        self.nav_buttons = {}
        
        self.create_sidebar_header("GENERAL")
        self.create_nav_button("  Dashboard", "dash", self.show_dash_tab)
        self.create_nav_button("  Lang Guide", "guide", self.show_guide_tab)
        self.create_nav_button("  Code Editor", "code", self.show_code_tab)
        self.create_nav_button("  System Logs & Console", "console", self.show_console_tab)
        self.create_nav_button("  Compiler Analytics", "analytics", self.show_analytics_tab)
        self.create_nav_button("  About Project", "about", self.show_about_tab)
        
        self.create_sidebar_header("PHASE 1: LEXICAL ANALYSIS")
        self.create_nav_button("  Tokens Stream", "token", self.show_token_tab)
        self.create_nav_button("  Basic Symbol Table", "sym", self.show_sym_tab)
        self.create_nav_button("  Interactive DFA Simulator", "dfa", self.show_dfa_tab)
        
        self.create_sidebar_header("PHASE 2: SYNTAX ANALYSIS")
        self.create_nav_button("  CFG Grammar sets", "cfg", self.show_cfg_tab)
        self.create_nav_button("  Parser Stack Trace", "trace", self.show_trace_tab)
        self.create_nav_button("  Visual Parse Tree", "tree", self.show_tree_tab)
        self.create_nav_button("  LR DFA & States", "lr_dfa", self.show_lr_dfa_tab)
        self.create_nav_button("  Parser Comparison", "parser_cmp", self.show_parser_cmp_tab)
        
        # Parser selector dropdown in sidebar
        parser_sel_frame = ctk.CTkFrame(self.sidebar_canvas_frame, fg_color="transparent")
        parser_sel_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(parser_sel_frame, text="Parser Mode:", font=ctk.CTkFont(size=11), text_color="#95a5a6").pack(side="left")
        self.parser_menu = ctk.CTkOptionMenu(parser_sel_frame, values=["LL(1)", "SLR", "LALR"], width=120, command=self.change_parser_mode)
        self.parser_menu.pack(side="right")
        self.parser_menu.set("LL(1)")

        self.create_sidebar_header("PHASE 3: SEMANTIC ANALYSIS")
        self.create_nav_button("  Simplified AST Tree", "ast", self.show_ast_tab)
        self.create_nav_button("  Scoped Symbols Table", "scoped_sym", self.show_scoped_sym_tab)

        self.create_sidebar_header("PHASE 4: INTERMEDIATE CODE")
        self.create_nav_button("  CFG Basic Blocks", "ir", self.show_ir_tab)

        self.create_sidebar_header("PHASE 5: CODE OPTIMIZER")
        self.create_nav_button("  Comparative TAC View", "opt", self.show_opt_tab)

        self.create_sidebar_header("PHASE 6: TARGET MACHINE")
        self.create_nav_button("  VM Execution Dashboard", "vm", self.show_vm_tab)

        self.create_sidebar_header("THEME & SETTINGS")
        
        # Theme dropdown
        theme_frame = ctk.CTkFrame(self.sidebar_canvas_frame, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(theme_frame, text="Theme:", font=ctk.CTkFont(size=11), text_color="#95a5a6").pack(side="left")
        self.theme_menu = ctk.CTkOptionMenu(theme_frame, values=["Dark", "Light"], width=120, command=self.change_theme)
        self.theme_menu.pack(side="right")
        self.theme_menu.set("Dark")

        # Clock Speed Slider
        speed_frame = ctk.CTkFrame(self.sidebar_canvas_frame, fg_color="transparent")
        speed_frame.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkLabel(speed_frame, text="VM Step Delay (ms):", font=ctk.CTkFont(size=11), text_color="#95a5a6").pack(anchor="w")
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=50, to=1500, number_of_steps=29, command=self.change_sim_speed)
        self.speed_slider.pack(fill="x", pady=5)
        self.speed_slider.set(400)

        # Removed compilation button from sidebar (placed inside code editor toolbar)

        # ----------------------------------------------------
        # 2. MAIN LAYOUT SYSTEM (TAB AREA & CONSOLE PANEL)
        # ----------------------------------------------------
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_container.grid_columnconfigure(0, weight=1)
        self.right_container.grid_rowconfigure(0, weight=1)

        # Container for different visualizer tabs
        self.main_content = ctk.CTkFrame(self.right_container, corner_radius=20, fg_color="#121212")
        self.main_content.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)

        self.tabs = {}
        self.current_tab_name = None

        # Backend compilers instances
        self.semantic_analyzer = SemanticAnalyzer()
        self.ir_generator = IRGenerator()
        self.tac_optimizer = TACOptimizer()
        self.target_codegen = TargetCodeGen()
        self.vm = VirtualMachine()
        self.debugger = InteractiveDebugger(self.vm)
        self.theme_manager = ThemeManager(self)
        self.vm_is_running = False

        # Instantiate unified parser manager
        self.parser_manager = ParserManager(grammar)

        self.init_tabs()
        # Shared state storage
        self.tokens = []
        self.symbol_table = SymbolTable()
        self.first = {}
        self.follow = {}
        self.table = {}
        self.parse_result = None
        
        self.show_dash_tab()

    def create_sidebar_header(self, text):
        lbl = ctk.CTkLabel(self.sidebar_canvas_frame, text=text, font=ctk.CTkFont(size=10, weight="bold"), text_color="#7f8c8d", anchor="w")
        lbl.pack(fill="x", padx=20, pady=(15, 2))

    def create_nav_button(self, name, key, command):
        btn = ctk.CTkButton(self.sidebar_canvas_frame, text=name, command=command, 
                            corner_radius=12, height=36, font=ctk.CTkFont(size=11, weight="bold"),
                            fg_color="transparent", text_color="#95a5a6", anchor="w")
        btn.pack(fill="x", padx=10, pady=1)
        self.nav_buttons[key] = btn

    # ====================================================
    # TABS INITIALIZERS
    # ====================================================
    def init_tabs(self):
        # 1. Dashboard Tab
        self.tabs["dash"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        
        # Split layout configuration
        self.tabs["dash"].grid_columnconfigure(0, weight=4) # Card checklist left
        self.tabs["dash"].grid_columnconfigure(1, weight=6) # Interactive winding canvas right
        self.tabs["dash"].grid_rowconfigure(0, weight=1)

        # Left side panel for checklist
        left_panel = ctk.CTkFrame(self.tabs["dash"], fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(left_panel, text="DESI AURALANG PIPELINE", 
                     font=ctk.CTkFont(size=18, weight="bold"), text_color="#3498db").pack(pady=(10, 2))
        ctk.CTkLabel(left_panel, text="Checklist Status Tracker", 
                     font=ctk.CTkFont(size=12, slant="italic"), text_color="#95a5a6").pack(pady=(0, 5))
        
        self.map_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.map_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Right side panel for interactive winding flow
        right_panel = ctk.CTkFrame(self.tabs["dash"], fg_color="#0e0e0e", corner_radius=20, border_width=1, border_color="#222")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        from gui.pipeline_viz import PipelineVisualizer
        self.pipeline_viz = PipelineVisualizer(right_panel, tab_jump_callback=self.show_tab)
        self.pipeline_viz.pack(fill="both", expand=True, padx=10, pady=10)
        
        def create_pipeline_step(parent, title, desc, status_text="IDLE", status_color="#95a5a6"):
            card = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1a1a1a", border_width=1, border_color="#333")
            card.pack(fill="x", padx=10, pady=4)
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=10, fill="both", expand=True)
            ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color="#ecf0f1", anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text=desc, font=ctk.CTkFont(size=10), text_color="#95a5a6", anchor="w", justify="left").pack(fill="x", pady=(2,0))
            status_lbl = ctk.CTkLabel(card, text=status_text, font=ctk.CTkFont(size=13, weight="bold"), text_color=status_color, width=90)
            status_lbl.pack(side="right", padx=15)
            return status_lbl
            
        self.stat_src = create_pipeline_step(self.map_scroll, "1. Source Code Input", "Reads South Asian vocabulary syntax.", "READY", "#3498db")
        self.stat_lex = create_pipeline_step(self.map_scroll, "2. Lexical Analyzer (Phase 1)", "Generates token stream and lexeme table.")
        self.stat_cfg = create_pipeline_step(self.map_scroll, "3. LL(1) Grammar Builder", "Computes FIRST / FOLLOW sets.", "READY", "#3498db")
        self.stat_syn = create_pipeline_step(self.map_scroll, "4. LL(1) Parser (Phase 2)", "Matches token stack for syntax validation.")
        self.stat_ast = create_pipeline_step(self.map_scroll, "5. Recursive AST Parser", "Constructs simplified abstract grammar tree.")
        self.stat_sem = create_pipeline_step(self.map_scroll, "6. Scoped Semantic Checker", "Enforces strict type checks and scoping scopes.")
        self.stat_ir  = create_pipeline_step(self.map_scroll, "7. TAC & Basic Blocks", "Emits quadruples basic blocks intermediate flow.")
        self.stat_opt = create_pipeline_step(self.map_scroll, "8. Compiler Optimizer", "Applies folding and dead-code exclusions.")
        self.stat_tgt = create_pipeline_step(self.map_scroll, "9. Target Code Generator", "Assembles optimized TAC into VM bytecode assembler.")
        self.stat_vm  = create_pipeline_step(self.map_scroll, "10. Virtual Machine Runtime", "Simulates step debug VM cpu execution.")

        # 2. Language Guide Tab
        self.tabs["guide"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["guide"].grid_columnconfigure(0, weight=1)
        self.tabs["guide"].grid_columnconfigure(1, weight=1)
        self.tabs["guide"].grid_rowconfigure(0, weight=1)

        # Left Column: Keyword Guide
        left_guide = ctk.CTkFrame(self.tabs["guide"], fg_color="transparent")
        left_guide.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(left_guide, text="📖 DESI AURA KEYWORD DICTIONARY", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3498db").pack(pady=(10, 5))
        
        self.guide_scroll = ctk.CTkScrollableFrame(left_guide, fg_color="#1a1a1a")
        self.guide_scroll.pack(fill="both", expand=True, pady=10)
        self.populate_guide()

        # Right Column: Educational Examples Library
        right_guide = ctk.CTkFrame(self.tabs["guide"], fg_color="transparent")
        right_guide.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(right_guide, text="🎓 EDUCATIONAL SCRIPT CATALOGUE", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2ecc71").pack(pady=(10, 5))
        
        self.examples_scroll = ctk.CTkScrollableFrame(right_guide, fg_color="#1a1a1a")
        self.examples_scroll.pack(fill="both", expand=True, pady=10)
        self.populate_examples_library()

        # 3. Code Editor Tab
        self.tabs["code"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        
        # Sleek IDE toolbar
        editor_toolbar = ctk.CTkFrame(self.tabs["code"], height=40, fg_color="#181818", corner_radius=10)
        editor_toolbar.pack(fill="x", side="top", padx=25, pady=(20, 0))
        
        # 🚀 Execute Code Button added directly to toolbar
        ctk.CTkButton(editor_toolbar, text="🚀 Execute Code", width=120, height=28, 
                      font=ctk.CTkFont(size=11, weight="bold"),
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=self.run_compiler).pack(side="left", padx=5, pady=6)
                      
        ctk.CTkButton(editor_toolbar, text="✨ Auto-Format", width=100, height=28, 
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=lambda: self.code_editor.auto_format_code()).pack(side="left", padx=5, pady=6)
                      
        ctk.CTkButton(editor_toolbar, text="🗑️ Clear Editor", width=100, height=28, 
                      font=ctk.CTkFont(size=11, weight="bold"),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=lambda: self.code_editor.delete("1.0", tk.END)).pack(side="left", padx=5, pady=6)

        ctk.CTkButton(editor_toolbar, text="📥 Export Report", width=115, height=28, 
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self.export_compiler_report).pack(side="left", padx=5, pady=6)
                      
        ctk.CTkLabel(editor_toolbar, text="💡 Ctrl + / to comment | Ctrl + F to find", 
                     text_color="#95a5a6", font=ctk.CTkFont(size=10, slant="italic")).pack(side="right", padx=10, pady=6)

        # Editor Frame on top (holds editor widget)
        editor_frame = ctk.CTkFrame(self.tabs["code"], fg_color="transparent")
        editor_frame.pack(fill="both", expand=True, padx=25, pady=(10, 5))

        from gui.code_editor import CustomCodeEditor
        self.code_editor = CustomCodeEditor(editor_frame)
        self.code_editor.pack(fill="both", expand=True)

        # Output Terminal on bottom (with border and header)
        output_frame = ctk.CTkFrame(self.tabs["code"], height=160, fg_color="#070707", corner_radius=15, border_width=1, border_color="#222222")
        output_frame.pack(fill="x", side="bottom", padx=25, pady=(5, 25))
        
        output_header = ctk.CTkFrame(output_frame, height=30, fg_color="#121212", corner_radius=8)
        output_header.pack(fill="x", side="top", padx=8, pady=6)
        
        ctk.CTkLabel(output_header, text="💻 DESI AURALANG OUTPUT TERMINAL", font=ctk.CTkFont(size=10, weight="bold"), text_color="#3498db").pack(side="left", padx=10)
        
        # Clear button
        ctk.CTkButton(output_header, text="Clear", width=50, height=20, font=ctk.CTkFont(size=9, weight="bold"),
                      command=self.clear_output_terminal).pack(side="right", padx=10)

        self.output_terminal = ctk.CTkTextbox(output_frame, font=("Consolas", 12), fg_color="#020202", text_color="#2ecc71")
        self.output_terminal.pack(fill="both", expand=True, padx=8, pady=(2, 8))
        self.output_terminal.insert("1.0", "Terminal initialized. Write code and click '🚀 Execute Code' to see output...\n")
        self.output_terminal.configure(state="disabled")

        # 4. Token Stream Tab
        self.tabs["token"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.token_tree = self.create_styled_tree(self.tabs["token"], ("No.", "Token Type", "Lexeme Value", "Line", "Column"))
        
        # 5. Basic Symbol Table Tab
        self.tabs["sym"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.sym_tree = self.create_styled_tree(self.tabs["sym"], ("Name", "Type", "Scope", "Address", "Line"))

        # 6. Interactive DFA Tab
        self.tabs["dfa"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.dfa_viz = DfaVisualizer(self.tabs["dfa"])
        self.dfa_viz.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 7. CFG Grammar sets Tab
        self.tabs["cfg"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.cfg_scroll = ctk.CTkScrollableFrame(self.tabs["cfg"], fg_color="#181818")
        self.cfg_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        for t, k in [("0. CFG PRODUCTIONS (NO LEFT RECURSION)", "cfg_rules"), ("1. FIRST SETS", "first"), ("2. FOLLOW SETS", "follow"), ("3. PARSING TABLE", "table")]:
            ctk.CTkLabel(self.cfg_scroll, text=t, text_color="#3498db", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4), anchor="w")
            txt = ctk.CTkTextbox(self.cfg_scroll, height=180, font=("Consolas", 11)); txt.pack(fill="x", pady=4)
            setattr(self, f"{k}_text", txt)

        # 8. LL(1) Stack Trace Tab
        self.tabs["trace"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.trace_tree = self.create_styled_tree(self.tabs["trace"], ("Stack State", "Input Token Buffer", "Parser Action"))

        # 9. Visual Parse Tree Tab
        self.tabs["tree"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tree_control_frame = ctk.CTkFrame(self.tabs["tree"], height=50, fg_color="#1a1a1a")
        self.tree_control_frame.pack(fill="x", side="top", padx=10, pady=5)
        
        ctk.CTkButton(self.tree_control_frame, text="+", width=40, command=lambda: self.tree_viz.zoom_in()).pack(side="right", padx=5)
        ctk.CTkButton(self.tree_control_frame, text="-", width=40, command=lambda: self.tree_viz.zoom_out()).pack(side="right", padx=5)
        ctk.CTkLabel(self.tree_control_frame, text="ZOOM (CTRL + WHEEL)", text_color="#7f8c8d").pack(side="right", padx=20)
        
        self.tree_viz = TreeVisualizer(self.tabs["tree"])
        self.tree_viz.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 10. Simplified AST Tree Tab
        self.tabs["ast"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.ast_control_frame = ctk.CTkFrame(self.tabs["ast"], height=50, fg_color="#1a1a1a")
        self.ast_control_frame.pack(fill="x", side="top", padx=10, pady=5)
        
        ctk.CTkButton(self.ast_control_frame, text="+", width=40, command=lambda: self.ast_viz.zoom_in()).pack(side="right", padx=5)
        ctk.CTkButton(self.ast_control_frame, text="-", width=40, command=lambda: self.ast_viz.zoom_out()).pack(side="right", padx=5)
        ctk.CTkLabel(self.ast_control_frame, text="ZOOM (CTRL + WHEEL)", text_color="#7f8c8d").pack(side="right", padx=20)
        
        self.ast_viz = TreeVisualizer(self.tabs["ast"])
        self.ast_viz.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 11. Scoped Symbols Table Tab
        self.tabs["scoped_sym"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.scoped_sym_tree = self.create_styled_tree(self.tabs["scoped_sym"], ("Name Symbol", "Datatype", "Scope Level", "Mock Value", "Mem Address", "Line No"))

        # 12. Intermediate CFG Flow Graph Tab
        self.tabs["ir"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["ir"].grid_columnconfigure(0, weight=1)
        self.tabs["ir"].grid_columnconfigure(1, weight=1)
        self.tabs["ir"].grid_rowconfigure(0, weight=1)
        
        # Left Panel (Tabview)
        ir_tabview = ctk.CTkTabview(self.tabs["ir"], fg_color="#141414", corner_radius=15)
        ir_tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        tab_tac = ir_tabview.add("TAC Statements")
        tab_quad = ir_tabview.add("Quadruples Table")
        tab_triple = ir_tabview.add("Triples Table")
        
        self.tac_textbox = ctk.CTkTextbox(tab_tac, font=("Consolas", 12), fg_color="#101010")
        self.tac_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.tac_textbox.configure(state="disabled")
        
        self.quad_tree = self.create_styled_tree(tab_quad, ("Operator", "Arg 1", "Arg 2", "Result"))
        self.triple_tree = self.create_styled_tree(tab_triple, ("Index", "Operator", "Arg 1", "Arg 2"))
        
        # Right Panel (Flow Visualizer)
        cfg_viz_container = ctk.CTkFrame(self.tabs["ir"], fg_color="#141414", corner_radius=15)
        cfg_viz_container.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(cfg_viz_container, text="CFG FLOW GRAPH OF BASIC BLOCKS", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3498db").pack(pady=10)
        
        self.cfg_flow_viz = IrFlowVisualizer(cfg_viz_container)
        self.cfg_flow_viz.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 13. Code Comparative Optimizer Tab
        self.tabs["opt"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["opt"].grid_columnconfigure(0, weight=1)
        self.tabs["opt"].grid_columnconfigure(1, weight=1)
        self.tabs["opt"].grid_rowconfigure(0, weight=2)
        self.tabs["opt"].grid_rowconfigure(1, weight=1)
        
        # Left
        orig_frame = ctk.CTkFrame(self.tabs["opt"], fg_color="#141414", corner_radius=15)
        orig_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(orig_frame, text="ORIGINAL TAC", font=ctk.CTkFont(size=13, weight="bold"), text_color="#95a5a6").pack(pady=10)
        self.orig_tac_text = ctk.CTkTextbox(orig_frame, font=("Consolas", 12), fg_color="#101010")
        self.orig_tac_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.orig_tac_text.configure(state="disabled")
        
        # Right
        opt_frame = ctk.CTkFrame(self.tabs["opt"], fg_color="#141414", corner_radius=15)
        opt_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(opt_frame, text="OPTIMIZED TAC", font=ctk.CTkFont(size=13, weight="bold"), text_color="#2ecc71").pack(pady=10)
        self.opt_tac_text = ctk.CTkTextbox(opt_frame, font=("Consolas", 12), fg_color="#101010")
        self.opt_tac_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.opt_tac_text.configure(state="disabled")
        
        # Bottom Optimizer action logs
        log_frame = ctk.CTkFrame(self.tabs["opt"], fg_color="#141414", corner_radius=15)
        log_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(log_frame, text="OPTIMIZATION LOGS & MOVES", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f1c40f").pack(pady=5)
        self.opt_log_text = ctk.CTkTextbox(log_frame, font=("Consolas", 11), fg_color="#101010")
        self.opt_log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.opt_log_text.configure(state="disabled")

        # 14. VM Dashboard Debugger Tab
        self.tabs["vm"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["vm"].grid_columnconfigure(0, weight=3) # Assembly stream
        self.tabs["vm"].grid_columnconfigure(1, weight=7) # VmDashboard
        self.tabs["vm"].grid_rowconfigure(0, weight=4)    # Content
        self.tabs["vm"].grid_rowconfigure(1, weight=1)    # Controls
        
        # Left Panel (Asm list)
        asm_frame = ctk.CTkFrame(self.tabs["vm"], fg_color="#141414", corner_radius=15)
        asm_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(asm_frame, text="TARGET CODE (STACK VM ASSEMBLY)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e67e22").pack(pady=10)
        self.asm_textbox = ctk.CTkTextbox(asm_frame, font=("Consolas", 12), fg_color="#101010")
        self.asm_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.asm_textbox.configure(state="disabled")
        
        # Right Panel (CPU Visuals Dashboard)
        self.vm_dash = VmDashboard(self.tabs["vm"])
        self.vm_dash.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Bottom controls and VM console output
        vm_bottom = ctk.CTkFrame(self.tabs["vm"], fg_color="#141414", corner_radius=15)
        vm_bottom.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        vm_bottom.grid_columnconfigure(0, weight=3)
        vm_bottom.grid_columnconfigure(1, weight=7)
        vm_bottom.grid_rowconfigure(0, weight=1)
        
        # Controls panel
        ctrl_panel = ctk.CTkFrame(vm_bottom, fg_color="transparent")
        ctrl_panel.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        ctk.CTkLabel(ctrl_panel, text="DEBUGGER CONTROLS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f1c40f").pack(anchor="w", pady=(0, 5))
        
        btn_subframe = ctk.CTkFrame(ctrl_panel, fg_color="transparent")
        btn_subframe.pack(fill="both", expand=True)
        
        self.btn_vm_step = ctk.CTkButton(btn_subframe, text="Step Into", width=80, command=self.step_vm)
        self.btn_vm_step.pack(side="left", padx=3)
        self.btn_vm_step_over = ctk.CTkButton(btn_subframe, text="Step Over", width=80, command=self.step_over_vm)
        self.btn_vm_step_over.pack(side="left", padx=3)
        self.btn_vm_run = ctk.CTkButton(btn_subframe, text="Auto Run", width=80, fg_color="#2ecc71", hover_color="#27ae60", command=self.toggle_vm_auto_run)
        self.btn_vm_run.pack(side="left", padx=3)
        self.btn_vm_reset = ctk.CTkButton(btn_subframe, text="Reset", width=60, fg_color="#e74c3c", hover_color="#c0392b", command=self.reset_vm_simulation)
        self.btn_vm_reset.pack(side="left", padx=3)
        
        # Console output
        console_frame = ctk.CTkFrame(vm_bottom, fg_color="transparent")
        console_frame.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        ctk.CTkLabel(console_frame, text="REAL-TIME MACHINE CONSOLE OUTPUT", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2ecc71").pack(anchor="w", pady=(0, 5))
        self.vm_console_text = ctk.CTkTextbox(console_frame, font=("Consolas", 12), fg_color="#0a0a0a", text_color="#2ecc71")
        self.vm_console_text.pack(fill="both", expand=True)
        self.vm_console_text.configure(state="disabled")

        # 15. About Project Tab
        self.tabs["about"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        ctk.CTkLabel(self.tabs["about"], text="PROJECT CREDITS", font=ctk.CTkFont(size=26, weight="bold"), text_color="#3498db").pack(pady=(20, 5))
        ctk.CTkLabel(self.tabs["about"], text="AuraLang Compiler Engine System Identity Validation", font=ctk.CTkFont(size=13, slant="italic"), text_color="#95a5a6").pack(pady=(0, 20))
        
        lang_card = ctk.CTkFrame(self.tabs["about"], corner_radius=12, fg_color="#1a1a1a", border_width=2, border_color="#e67e22")
        lang_card.pack(pady=(0, 15), padx=80, fill="x")
        ctk.CTkLabel(lang_card, text="About DesiAura Language", font=ctk.CTkFont(size=20, weight="bold"), text_color="#e67e22").pack(pady=(15, 5))
        desc_text = (
            "DesiAura is a custom, statically typed, educational programming language designed with "
            "South Asian (Desi) syntax keywords. It bridges the gap for local developers to learn "
            "programming logic using native, relatable terminology (like 'rakho', 'bol', 'agar').\n\n"
            "This compiler frontend strictly parses DesiAura code through robust Lexical, LL(1) Syntax, "
            "AST Simplification, Semantic Checks, TAC Generations, multi-pass Optimizations, and Stack VM debug outputs."
        )
        ctk.CTkLabel(lang_card, text=desc_text, font=ctk.CTkFont(size=15), text_color="#ffffff", justify="left", wraplength=800).pack(pady=(0, 15), padx=30, fill="x")
        
        auth_card = ctk.CTkFrame(self.tabs["about"], corner_radius=12, fg_color="#1a1a1a", border_width=2, border_color="#3498db")
        auth_card.pack(pady=(0, 15), padx=80, fill="both", expand=True)
        
        info = [
            ("Developer Name:", "Hunain Ahmed"),
            ("Registration No:", "Sp23-Bcs-053"),
            ("Subject Name:", "Compiler Construction"),
            ("Project Level:", "FULL COMPILER & INTERACTIVE VISUALIZER IMPLEMENTATION")
        ]
        for label, val in info:
            row = ctk.CTkFrame(auth_card, fg_color="transparent")
            row.pack(fill="x", pady=10, padx=30)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=16, weight="bold"), text_color="#bdc3c7", width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=17, weight="bold"), text_color="#ffffff", anchor="w", justify="left", wraplength=550).pack(side="left", padx=10)
            
        ctk.CTkLabel(auth_card, text="Verified and Authenticated Engine \u2714", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2ecc71").pack(side="bottom", pady=20)

        # 16. Analytics Tab
        from gui.analytics_dashboard import AnalyticsDashboard
        self.tabs["analytics"] = AnalyticsDashboard(self.main_content)

        # ----------------------------------------------------
        # 3. UNIFIED DEDICATED CONSOLE PAGE (LOGS & ERRORS)
        # ----------------------------------------------------
        self.tabs["console"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["console"].grid_columnconfigure(0, weight=1)
        self.tabs["console"].grid_columnconfigure(1, weight=1)
        self.tabs["console"].grid_rowconfigure(0, weight=1)
        
        # Keep reference to self.console_panel for backward theme manager compatibility
        self.console_panel = self.tabs["console"]
        
        # Left Panel (Compiler Action Logs)
        logs_container = ctk.CTkFrame(self.tabs["console"], fg_color="#141416", corner_radius=20, border_width=1, border_color="#222")
        logs_container.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(logs_container, text="⚙️ COMPILER SYSTEM ACTION LOGS", 
                     font=ctk.CTkFont(size=16, weight="bold"), text_color="#3498db").pack(pady=(20, 2))
        ctk.CTkLabel(logs_container, text="Trace logs showing internal compiler step executions", 
                     font=ctk.CTkFont(size=11, slant="italic"), text_color="#95a5a6").pack(pady=(0, 15))
                     
        self.log_terminal = ctk.CTkTextbox(logs_container, font=("Consolas", 12), fg_color="#0a0a0a", text_color="#ecf0f1")
        self.log_terminal.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_terminal.insert("1.0", ">>> Aura Compiler System Initialized. Write code and click Execute Compiler.\n")
        self.log_terminal.configure(state="disabled")
        
        # Right Panel (Warnings & Errors)
        errs_container = ctk.CTkFrame(self.tabs["console"], fg_color="#141416", corner_radius=20, border_width=1, border_color="#222")
        errs_container.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(errs_container, text="⚠️ SYSTEM WARNINGS & ERRORS", 
                     font=ctk.CTkFont(size=16, weight="bold"), text_color="#e74c3c").pack(pady=(20, 2))
        ctk.CTkLabel(errs_container, text="Syntax anomalies, type mismatches, and semantic violations", 
                     font=ctk.CTkFont(size=11, slant="italic"), text_color="#95a5a6").pack(pady=(0, 15))
                     
        self.err_terminal = ctk.CTkTextbox(errs_container, font=("Consolas", 12), fg_color="#0a0a0a", text_color="#e74c3c")
        self.err_terminal.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.err_terminal.insert("1.0", "No errors or warnings currently logged.\n")
        self.err_terminal.configure(state="disabled")

        # 17. LR DFA Automata Tab
        self.tabs["lr_dfa"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.lr_dfa_viz = LrDfaVisualizer(self.tabs["lr_dfa"], self.parser_manager)
        self.lr_dfa_viz.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 18. Parser Comparison Tab
        self.tabs["parser_cmp"] = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.parser_cmp_viz = ParserComparisonDashboard(self.tabs["parser_cmp"])
        self.parser_cmp_viz.pack(fill="both", expand=True, padx=15, pady=15)

    # ====================================================
    # UTILITY LOGGERS & HELPERS
    # ====================================================

    def log_compiler(self, message):
        self.log_terminal.configure(state="normal")
        self.log_terminal.insert(tk.END, f"[System] {message}\n")
        self.log_terminal.see(tk.END)
        self.log_terminal.configure(state="disabled")

    def log_error(self, message):
        self.err_terminal.configure(state="normal")
        # Clear default placeholder if first error
        if "No errors or warnings currently logged." in self.err_terminal.get("1.0", tk.END):
            self.err_terminal.delete("1.0", tk.END)
        self.err_terminal.insert(tk.END, f"[Error/Warning] {message}\n")
        self.err_terminal.see(tk.END)
        self.err_terminal.configure(state="disabled")

    def clear_terminals(self):
        self.log_terminal.configure(state="normal")
        self.log_terminal.delete("1.0", tk.END)
        self.log_terminal.insert("1.0", "--- NEW COMPILATION ACTION LOGS ---\n")
        self.log_terminal.configure(state="disabled")
        
        self.err_terminal.configure(state="normal")
        self.err_terminal.delete("1.0", tk.END)
        self.err_terminal.insert("1.0", "--- NEW SYSTEM WARNINGS & ERRORS ---\n")
        self.err_terminal.configure(state="disabled")

        if hasattr(self, "output_terminal"):
            self.clear_output_terminal()

    def clear_output_terminal(self):
        self.output_terminal.configure(state="normal")
        self.output_terminal.delete("1.0", tk.END)
        self.output_terminal.insert("1.0", "--- Program Output Console ---\n")
        self.output_terminal.configure(state="disabled")

    def populate_guide(self):
        header = ctk.CTkFrame(self.guide_scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10), padx=10)
        ctk.CTkLabel(header, text="Aura Keyword", font=ctk.CTkFont(size=13, weight="bold"), text_color="#7f8c8d", width=120).pack(side="left", padx=20)
        ctk.CTkLabel(header, text="Std. Keyword", font=ctk.CTkFont(size=13, weight="bold"), text_color="#7f8c8d", width=120).pack(side="left", padx=10)
        ctk.CTkLabel(header, text="Meaning", font=ctk.CTkFont(size=13, weight="bold"), text_color="#7f8c8d", width=150).pack(side="left", padx=10)
        ctk.CTkLabel(header, text="Description", font=ctk.CTkFont(size=13, weight="bold"), text_color="#7f8c8d", anchor="w").pack(side="left", fill="x", expand=True)

        for item in LANGUAGE_GUIDE:
            row = ctk.CTkFrame(self.guide_scroll, fg_color="#262626", corner_radius=10)
            row.pack(fill="x", pady=4, padx=10)
            
            ctk.CTkLabel(row, text=item["word"], font=ctk.CTkFont(size=13, weight="bold"), text_color="#3498db", width=120).pack(side="left", padx=20, pady=12)
            ctk.CTkLabel(row, text=item.get("original", "-"), font=ctk.CTkFont(size=13, weight="bold"), text_color="#e67e22", width=120).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=item["meaning"], font=ctk.CTkFont(size=11, weight="bold"), width=150).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=item["desc"], font=ctk.CTkFont(size=11), anchor="w").pack(side="left", fill="x", expand=True)
            
            ctk.CTkButton(row, text="TRY SNIPPET", width=95, font=ctk.CTkFont(size=9, weight="bold"),
                          command=lambda s=item["example"]: self.load_example(s)).pack(side="right", padx=20)

    def load_example(self, snippet):
        self.code_editor.delete("1.0", tk.END)
        self.code_editor.insert("1.0", snippet)
        self.show_code_tab()
        self.log_compiler("Loaded guide code snippet into Editor.")

    def populate_examples_library(self):
        examples = [
            {
                "title": "Factorial Calculation (Recursion)",
                "difficulty": "Easy",
                "diff_color": "#2ecc71",
                "tags": ["Math", "Recursion"],
                "desc": "Calculates factorial dynamically using standard stack frame recursion.",
                "code": (
                    "tarkeeb fact(n) {\n"
                    "    agar (n <= 1) {\n"
                    "        wapas 1;\n"
                    "    }\n"
                    "    wapas n * fact(n - 1);\n"
                    "}\n\n"
                    "rakho result = fact(5);\n"
                    "bol result; // prints 120\n"
                )
            },
            {
                "title": "Fibonacci Sequence Loop",
                "difficulty": "Medium",
                "diff_color": "#f1c40f",
                "tags": ["Recursion", "Sequence"],
                "desc": "Computes the Nth Fibonacci number in South Asian syntax blocks.",
                "code": (
                    "tarkeeb fib(n) {\n"
                    "    agar (n <= 1) {\n"
                    "        wapas n;\n"
                    "    }\n"
                    "    wapas fib(n - 1) + fib(n - 2);\n"
                    "}\n\n"
                    "rakho res = fib(6);\n"
                    "bol res; // prints 8\n"
                )
            },
            {
                "title": "Nested Loops Multiplier",
                "difficulty": "Medium",
                "diff_color": "#f1c40f",
                "tags": ["Loops", "Nested Scope"],
                "desc": "Runs double nested 'ghumo' loops to print products recursively.",
                "code": (
                    "rakho limit = 3;\n"
                    "ghumo i from 1 to limit {\n"
                    "    ghumo j from 1 to limit {\n"
                    "        bol i * j;\n"
                    "    }\n"
                    "}\n"
                )
            },
            {
                "title": "Array Initialization & Operations",
                "difficulty": "Hard",
                "diff_color": "#e74c3c",
                "tags": ["Heap", "Arrays"],
                "desc": "Allocates dynamic arrays in the 64-cell Heap space.",
                "code": (
                    "rakho list = [10, 20, 30];\n"
                    "bol list[0];\n"
                    "bol list[1];\n"
                    "bol list[2];\n"
                )
            },
            {
                "title": "Compiler Semantic Diagnostics",
                "difficulty": "Diagnostic",
                "diff_color": "#e67e22",
                "tags": ["Validation", "Errors"],
                "desc": "Trigger semantic checks to demo the pipeline diagnostics recovery.",
                "code": (
                    "rakho val = 42;\n"
                    "val = sahi + 5; // Semantic check error!\n"
                )
            }
        ]

        for item in examples:
            card = ctk.CTkFrame(self.examples_scroll, fg_color="#262626", corner_radius=12)
            card.pack(fill="x", pady=6, padx=10)
            
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=15, pady=(10, 2))
            
            ctk.CTkLabel(header, text=item["title"], font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff", anchor="w").pack(side="left")
            
            # Badge
            badge_frame = ctk.CTkFrame(header, fg_color=item["diff_color"], corner_radius=6)
            badge_frame.pack(side="right", padx=5)
            ctk.CTkLabel(badge_frame, text=item["difficulty"], font=ctk.CTkFont(size=9, weight="bold"), text_color="#121212").pack(padx=6, pady=2)
            
            # Tags row
            tags_frame = ctk.CTkFrame(card, fg_color="transparent")
            tags_frame.pack(fill="x", padx=15, pady=2)
            for t in item["tags"]:
                tag_lbl = ctk.CTkLabel(tags_frame, text=f" #{t}", font=ctk.CTkFont(size=9, slant="italic"), text_color="#3498db")
                tag_lbl.pack(side="left", padx=2)
                
            # Description
            ctk.CTkLabel(card, text=item["desc"], font=ctk.CTkFont(size=11), text_color="#bdc3c7", justify="left", anchor="w", wraplength=350).pack(fill="x", padx=15, pady=(2, 10))
            
            # Load snippet button
            ctk.CTkButton(card, text="🔌 LOAD PROGRAM", height=28, font=ctk.CTkFont(size=10, weight="bold"),
                          fg_color="#27ae60", hover_color="#219653",
                          command=lambda s=item["code"]: self.load_example(s)).pack(fill="x", padx=15, pady=(0, 10))

    def create_styled_tree(self, parent, columns):
        c = ctk.CTkFrame(parent, fg_color="transparent"); c.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Style treeview dark
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#181818", 
                        foreground="#ffffff", 
                        fieldbackground="#181818", 
                        bordercolor="#333", 
                        rowheight=24)
        style.map("Treeview", background=[("selected", "#3498db")])
        style.configure("Treeview.Heading", background="#0a0a0a", foreground="#ffffff", font=("Arial", 11, "bold"))
        
        tree = ttk.Treeview(c, columns=columns, show="headings")
        for col in columns: 
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=120)
            
        tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(c, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        return tree

    def show_tab(self, tab_name):
        if self.current_tab_name:
            self.tabs[self.current_tab_name].grid_forget()
            self.nav_buttons[self.current_tab_name].configure(fg_color="transparent", text_color="#95a5a6")
        self.tabs[tab_name].grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.nav_buttons[tab_name].configure(fg_color="#3498db", text_color="white")
        self.current_tab_name = tab_name

    def show_dash_tab(self): self.show_tab("dash")
    def show_guide_tab(self): self.show_tab("guide")
    def show_code_tab(self): self.show_tab("code")
    def show_token_tab(self): self.show_tab("token")
    def show_sym_tab(self): self.show_tab("sym")
    def show_dfa_tab(self): self.show_tab("dfa")
    def show_cfg_tab(self): self.show_tab("cfg")
    def show_trace_tab(self): self.show_tab("trace")
    
    def show_lr_dfa_tab(self):
        self.show_tab("lr_dfa")
        active_mode = self.parser_manager.get_active_parser_name()
        if active_mode != "LL(1)":
            engine = self.parser_manager.slr_engine if active_mode == "SLR" else self.parser_manager.lalr_engine
            state_names = engine.state_names if hasattr(engine, "state_names") else None
            merge_logs = engine.merge_logs if hasattr(engine, "merge_logs") else None
            self.lr_dfa_viz.draw_dfa(active_mode, engine.states, engine.transitions, state_names, merge_logs)
        else:
            self.lr_dfa_viz.show_overlay()

    def show_parser_cmp_tab(self):
        self.show_tab("parser_cmp")
        self.update_parser_comparison_metrics()
    def show_tree_tab(self): self.show_tab("tree")
    def show_ast_tab(self): self.show_tab("ast")
    def show_scoped_sym_tab(self): self.show_tab("scoped_sym")
    def show_ir_tab(self): self.show_tab("ir")
    def show_opt_tab(self): self.show_tab("opt")
    def show_vm_tab(self): self.show_tab("vm")
    def show_about_tab(self): self.show_tab("about")
    def show_analytics_tab(self): self.show_tab("analytics")
    def show_console_tab(self): self.show_tab("console")

    # ====================================================
    # PIPELINE EXECUTION CONTROLLER
    # ====================================================

    def run_compiler(self):
        source = self.code_editor.get("1.0", tk.END).strip()
        if not source: 
            messagebox.showwarning("Warning", "Editor is empty. Write or load some AuraLang code first.")
            return

        import time
        start_time = time.perf_counter()
        self.clear_terminals()
        if hasattr(self, "output_terminal"):
            self.clear_output_terminal()
        self.log_compiler("Firing Desi AuraLang compilation execution chain...")
        
        # Reset card status to default
        default_color = "#95a5a6"
        for stat in [self.stat_lex, self.stat_syn, self.stat_ast, self.stat_sem, self.stat_ir, self.stat_opt, self.stat_tgt, self.stat_vm]:
            stat.configure(text="READY", text_color=default_color)

        # Reset pipeline_viz node states
        for nid in ["src", "lex", "ff", "syn", "ast", "sem", "ir", "opt", "tgt", "vm", "sym_tab", "opt_cmp"]:
            self.pipeline_viz.update_node_status(nid, "IDLE")

        self.pipeline_viz.update_node_status("src", "SUCCESS")

        from semantic.error_manager import CompilerErrorManager
        error_manager = CompilerErrorManager()

        try:
            # 1. Lexical Analysis
            self.log_compiler("[Phase 1] Scanning lexical lexemes...")
            lexer = Lexer(source, error_manager)
            self.tokens = lexer.tokenize()
            self.update_token_display()
            
            if error_manager.get_errors_by_phase("Lexical"):
                self.stat_lex.configure(text="WARNING", text_color="#e67e22")
                self.pipeline_viz.update_node_status("lex", "FAILED")
                self.log_compiler(f"[Phase 1] Lexical scanning completed with recoverable errors.")
            else:
                self.stat_lex.configure(text="SUCCESSFUL", text_color="#2ecc71")
                self.pipeline_viz.update_node_status("lex", "SUCCESS")
                if self.pipeline_viz.is_detailed.get():
                    self.pipeline_viz.update_node_status("sym_tab", "SUCCESS")
                self.log_compiler(f"[Phase 1] Scanning completed successfully. Generated {len(self.tokens)} tokens.")

            # Build basic symbol table
            self.symbol_table.build(self.tokens)
            self.update_sym_display()

            # 2. Grammarsets & Conflict Checking
            self.log_compiler("[Phase 2] Analyzing declarative LL(1) grammar...")
            ff = FirstFollow(grammar)
            self.first = ff.compute_first()
            self.follow = ff.compute_follow()
            self.pipeline_viz.update_node_status("ff", "SUCCESS")
            
            pt = ParsingTable(grammar, self.first, self.follow)
            self.table = pt.build()
            self.update_cfg_display()
            
            # Print educational left recursions warnings or table cell conflicts
            if pt.left_recursions:
                self.log_compiler(f"[Warning] Grammar has {len(pt.left_recursions)} Left Recursion anomalies.")
                for lr in pt.left_recursions:
                    self.log_error(lr)
            if pt.conflicts:
                self.log_compiler(f"[Warning] Grammar has {len(pt.conflicts)} LL(1) parse table cell conflicts.")
                for conf in pt.conflicts:
                    self.log_error(conf)

            # Filter tokens for educational LL(1) Parser to keep it within the CFG declarative grammar bounds
            educational_tokens = []
            temp_stmt = []
            in_if = False
            brace_depth = 0
            
            for t in self.tokens:
                temp_stmt.append(t)
                if t.type.name == "SEMI" and not in_if:
                    # Check for unsupported tokens like LBRACKET, COMMA, TARKEEB, GHUMO, JABTAK, WAPAS
                    has_unsupported = any(tok.type.name in ("LBRACKET", "RBRACKET", "COMMA", "TARKEEB", "GHUMO", "JABTAK", "WAPAS") for tok in temp_stmt)
                    if not has_unsupported:
                        educational_tokens.extend(temp_stmt)
                    temp_stmt = []
                elif t.type.name == "LBRACE":
                    brace_depth += 1
                    in_if = True
                elif t.type.name == "RBRACE":
                    brace_depth -= 1
                    if brace_depth == 0:
                        in_if = False
                        has_unsupported = any(tok.type.name in ("LBRACKET", "RBRACKET", "COMMA", "TARKEEB", "GHUMO", "JABTAK", "WAPAS") for tok in temp_stmt)
                        if not has_unsupported:
                            educational_tokens.extend(temp_stmt)
                        temp_stmt = []

            # Dyn Parser Manager Routing
            self.educational_tokens = educational_tokens
            self.parse_result = self.parser_manager.parse(educational_tokens)
            
            # Double safety fallback
            if not self.parse_result["success"] or len(educational_tokens) == 0:
                baseline_source = "rakho limit = 4;\nbol limit;"
                baseline_lexer = Lexer(baseline_source, error_manager)
                baseline_tokens = baseline_lexer.tokenize()
                self.parse_result = self.parser_manager.parse(baseline_tokens)
                
            self.update_trace_display()
            self.tree_viz.draw_tree(self.parse_result["tree"])
            
            # Refresh LR DFA view if needed
            active_mode = self.parser_manager.get_active_parser_name()
            if active_mode != "LL(1)":
                engine = self.parser_manager.slr_engine if active_mode == "SLR" else self.parser_manager.lalr_engine
                state_names = engine.state_names if hasattr(engine, "state_names") else None
                merge_logs = engine.merge_logs if hasattr(engine, "merge_logs") else None
                self.lr_dfa_viz.draw_dfa(active_mode, engine.states, engine.transitions, state_names, merge_logs)
            else:
                self.lr_dfa_viz.show_overlay()
                
            self.update_parser_comparison_metrics()
            
            self.stat_syn.configure(text="VERIFIED", text_color="#2ecc71")
            self.pipeline_viz.update_node_status("syn", "SUCCESS")
            self.log_compiler(f"[Phase 2] Educational {active_mode} Parse Tree & Stack Trace rendered successfully.")

            # 3. Recursive Descent AST Parser
            self.log_compiler("[Phase 3] Invoking recursive descent AST parser...")
            ast_parser = ASTParser(self.tokens, error_manager)
            ast_program = ast_parser.parse()
            self.ast_viz.draw_tree(ast_program.to_dict())
            
            if error_manager.get_errors_by_phase("Syntax"):
                self.stat_ast.configure(text="WARNING", text_color="#e67e22")
                self.pipeline_viz.update_node_status("ast", "FAILED")
                self.log_compiler("[Phase 3] AST parsing completed with recovered issues.")
            else:
                self.stat_ast.configure(text="SUCCESSFUL", text_color="#2ecc71")
                self.pipeline_viz.update_node_status("ast", "SUCCESS")
                self.log_compiler("[Phase 3] Simplified Abstract Syntax Tree generated successfully.")

            # 4. Scoped Semantic Analyzer
            self.log_compiler("[Phase 4] Launching Scoped Semantic Analyzer...")
            self.semantic_analyzer.error_manager = error_manager
            sem_success = self.semantic_analyzer.analyze(ast_program)
            
            # Dump to terminal scoped traces
            for trace_line in self.semantic_analyzer.trace:
                self.log_terminal.configure(state="normal")
                self.log_terminal.insert(tk.END, f"{trace_line}\n")
                self.log_terminal.configure(state="disabled")
                
            self.update_scoped_symbols_display()

            if error_manager.get_errors_by_phase("Semantic"):
                self.stat_sem.configure(text="FAILED", text_color="#e74c3c")
                self.pipeline_viz.update_node_status("sem", "FAILED")
            else:
                self.stat_sem.configure(text="SUCCESSFUL", text_color="#2ecc71")
                self.pipeline_viz.update_node_status("sem", "SUCCESS")

            # Check if editor needs highlighting
            err_lines = {err.line for err in error_manager.errors if err.line > 0}
            self.code_editor.underline_errors(err_lines)

            # Check for error manager blockages
            if error_manager.has_errors():
                self.log_error(f"--- COMPILATION HALTED: {len(error_manager.errors)} DIAGNOSTICS DETECTED ---")
                
                # Print compilation failure inside output terminal
                self.output_terminal.configure(state="normal")
                self.output_terminal.delete("1.0", tk.END)
                self.output_terminal.insert(tk.END, f"❌ COMPILATION HALTED: {len(error_manager.errors)} errors detected:\n\n")
                
                for err in error_manager.errors:
                    self.log_error(f"[{err.phase} Error] Line {err.line}, Col {err.column}: {err.message}")
                    self.log_error(f"   💡 Suggestion: {err.suggested_fix}")
                    self.log_error(f"   🔧 Recovery: {err.recovery_action}")
                    self.log_error("")
                    
                    self.output_terminal.insert(tk.END, f"[{err.phase} Error] Line {err.line}, Col {err.column}: {err.message}\n")
                    self.output_terminal.insert(tk.END, f"   💡 Suggestion: {err.suggested_fix}\n\n")
                    
                self.output_terminal.configure(state="disabled")

                messagebox.showerror(
                    "Compilation Diagnostic Failures", 
                    f"AuraLang engine failed to produce bytecode due to {len(error_manager.errors)} front-end errors.\n"
                    "We have highlighted the diagnostic errors inside the IDE text editor panel. Please check Warnings & Errors tab below."
                )
                self.show_code_tab()
                return

            self.log_compiler("[Phase 4] Semantic analyzer passed with zero diagnostics.")

            # 5. Three Address Code (TAC) and Flow Graph
            self.log_compiler("[Phase 5] Compiling to Intermediate Representation (TAC)...")
            self.ir_generator.generate(ast_program)
            orig_tac_lines = self.ir_generator.tac_instructions
            
            # Draw CFG Graph
            cfg_blocks = self.ir_generator.build_cfg()
            self.cfg_flow_viz.draw_flow_graph(cfg_blocks)
            self.stat_ir.configure(text="SUCCESSFUL", text_color="#2ecc71")
            self.pipeline_viz.update_node_status("ir", "SUCCESS")
            self.log_compiler(f"[Phase 5] Emitted {len(orig_tac_lines)} intermediate operations. Basic blocks calculated.")

            # 6. TAC Multi-Pass Optimizer
            self.log_compiler("[Phase 6] Starting multi-pass TAC Optimizer passes...")
            opt_quads = self.tac_optimizer.optimize(self.ir_generator.quadruples)
            opt_tac_lines = TACOptimizer.to_tac_string(opt_quads)
            
            self.update_optimizer_comparisons(orig_tac_lines, opt_tac_lines)
            self.stat_opt.configure(text="OPTIMIZED", text_color="#2ecc71")
            self.pipeline_viz.update_node_status("opt", "SUCCESS")
            if self.pipeline_viz.is_detailed.get():
                self.pipeline_viz.update_node_status("opt_cmp", "SUCCESS")
            self.log_compiler(f"[Phase 6] Code optimization completed. Removed redundant computations.")

            # Update IR tab views
            self.update_ir_tab_views(opt_tac_lines, opt_quads)

            # 7. Target VM Bytecode assembly Code Generation
            self.log_compiler("[Phase 7] Generating Stack VM Virtual Assembly...")
            asm_code = self.target_codegen.generate(opt_quads)
            self.update_asm_textbox(asm_code)
            self.stat_tgt.configure(text="COMPILED", text_color="#2ecc71")
            self.pipeline_viz.update_node_status("tgt", "SUCCESS")
            self.log_compiler(f"[Phase 7] Assembly generated successfully ({len(asm_code)} lines).")

            # 8. Load into Virtual Machine
            self.log_compiler("[VM] Loading target bytecode program into stack CPU runtime...")
            self.vm.load_program(asm_code)
            
            # Feed function parameter declarations mappings
            func_param_map = {}
            for sym in self.semantic_analyzer.symbols_list:
                if sym.datatype == "function" and sym.value:
                    if "params: " in str(sym.value):
                        param_str = sym.value.replace("params: ", "").strip()
                        func_param_map[sym.name] = [p.strip() for p in param_str.split(",") if p.strip()]
            self.vm.func_params = func_param_map
            
            self.reset_vm_simulation()
            self.stat_vm.configure(text="READY", text_color="#3498db")
            self.pipeline_viz.update_node_status("vm", "SUCCESS")
            self.log_compiler("[VM] Virtual machine CPU successfully loaded and ready for step execution.")
            
            # Trigger dynamic path glow animation
            self.run_pipeline_glow_animation()

            # Calculate dynamic compiler telemetry
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # AST tree complexity paths
            max_depth = self.get_ast_depth(ast_program)
            ast_depth_path = [self.get_ast_depth(stmt) for stmt in ast_program.statements] if hasattr(ast_program, "statements") else [max_depth]
            
            orig_len = len(orig_tac_lines)
            opt_len = len(opt_tac_lines)
            reduction_pct = ((orig_len - opt_len) / max(orig_len, 1)) * 100 if orig_len > 0 else 0
            opt_ratio = orig_len / max(opt_len, 1)
            
            # Build active profile text for card
            active_mode = self.parser_manager.get_active_parser_name()
            if active_mode == "LL(1)":
                profile = "LL(1) (Top-Down)"
            else:
                engine = self.parser_manager.slr_engine if active_mode == "SLR" else self.parser_manager.lalr_engine
                profile = f"{active_mode} ({len(engine.states)} States, {len(engine.conflicts)} Conflicts)"

            metrics = {
                "tokens": len(self.tokens),
                "parser_time": elapsed_ms,
                "ast_depth": max_depth,
                "ast_depth_path": ast_depth_path,
                "orig_tac_len": orig_len,
                "opt_tac_len": opt_len,
                "opt_ratio": opt_ratio,
                "reduction": reduction_pct,
                "cycles": len(self.vm.instructions),
                "parser_profile": profile
            }
            self.tabs["analytics"].update_telemetry(metrics)

            # 9. RUN TO COMPLETION & CAPTURE OUTPUTS FOR INTEGRATED TERMINAL
            self.log_compiler("[VM] Automatically executing stack bytecode to completion...")
            self.vm.run(max_steps=5000)
            
            # Print execution outputs inside Output Terminal
            self.output_terminal.configure(state="normal")
            self.output_terminal.delete("1.0", tk.END)
            self.output_terminal.insert(tk.END, "--- Execution Started ---\n")
            if self.vm.console_output:
                for line in self.vm.console_output:
                    self.output_terminal.insert(tk.END, f"{line}\n")
            else:
                self.output_terminal.insert(tk.END, "[No outputs printed. Use 'bol' statement to print variables!]\n")
            self.output_terminal.insert(tk.END, "\n--- Execution Finished successfully ---\n")
            self.output_terminal.configure(state="disabled")
            
            self.log_compiler(f"[VM] Program executed successfully. Output captured in editor terminal.")
            
            # Reset VM so step debugger is fresh and loaded
            self.reset_vm_simulation()

            messagebox.showinfo("Pipeline Success", "Desi AuraLang compiled and executed successfully! Outputs are printed in Output Terminal below.")

        except Exception as e:
            self.log_compiler(f"Internal compiler crash: {str(e)}")
            self.log_error(f"Compiler System Error: {str(e)}")
            
            # Show crash in output terminal
            if hasattr(self, "output_terminal"):
                self.output_terminal.configure(state="normal")
                self.output_terminal.delete("1.0", tk.END)
                self.output_terminal.insert(tk.END, f"❌ Compiler System Crash: {str(e)}\n")
                self.output_terminal.configure(state="disabled")
            
            messagebox.showerror("Compiler Crash", f"Pipeline aborted: {str(e)}")

    def run_pipeline_glow_animation(self):
        if self.pipeline_viz.is_detailed.get():
            path = [
                ("src", "lex"), ("lex", "ff"), ("ff", "syn"), 
                ("syn", "ast"), ("ast", "sem"), ("sem", "ir"), 
                ("ir", "opt"), ("opt", "tgt"), ("tgt", "vm")
            ]
        else:
            path = [
                ("src", "lex"), ("lex", "syn"), ("syn", "ast"), 
                ("ast", "sem"), ("sem", "ir"), ("ir", "opt"), 
                ("opt", "tgt"), ("tgt", "vm")
            ]
            
        def run_step(idx):
            if idx >= len(path):
                return
            from_node, to_node = path[idx]
            self.pipeline_viz.animate_transition(from_node, to_node, lambda: run_step(idx + 1))
            
        run_step(0)

    # ====================================================
    # UI PANELS POPULATORS
    # ====================================================

    def update_token_display(self):
        for item in self.token_tree.get_children(): self.token_tree.delete(item)
        for i, t in enumerate(self.tokens): 
            self.token_tree.insert("", "end", values=(i+1, t.type.name, t.value, t.line, t.col))

    def update_sym_display(self):
        for item in self.sym_tree.get_children(): self.sym_tree.delete(item)
        for s in self.symbol_table.get_all(): 
            self.sym_tree.insert("", "end", values=(s.name, s.type, s.scope, s.address, s.line))

    def update_cfg_display(self):
        active_mode = self.parser_manager.get_active_parser_name()
        
        self.cfg_rules_text.configure(state="normal")
        self.cfg_rules_text.delete("1.0", tk.END)
        
        if active_mode == "LL(1)":
            for nt, prods in grammar.items():
                rhs = " | ".join([" ".join(p) for p in prods])
                self.cfg_rules_text.insert(tk.END, f"{nt} -> {rhs}\n")
        else:
            engine = self.parser_manager.slr_engine if active_mode == "SLR" else self.parser_manager.lalr_engine
            for nt, prods in engine.grammar.items():
                rhs = " | ".join([" ".join(p) for p in prods])
                self.cfg_rules_text.insert(tk.END, f"{nt} -> {rhs}\n")
        self.cfg_rules_text.configure(state="disabled")

        self.first_text.configure(state="normal")
        self.first_text.delete("1.0", tk.END)
        self.follow_text.configure(state="normal")
        self.follow_text.delete("1.0", tk.END)
        self.table_text.configure(state="normal")
        self.table_text.delete("1.0", tk.END)
        
        if active_mode == "LL(1)":
            for nt, first_set in sorted(self.first.items()):
                self.first_text.insert(tk.END, f"FIRST({nt:15}) = {{ {', '.join(sorted(first_set))} }}\n")
            for nt, follow_set in sorted(self.follow.items()):
                self.follow_text.insert(tk.END, f"FOLLOW({nt:14}) = {{ {', '.join(sorted(follow_set))} }}\n")
            for nt, row in sorted(self.table.items()):
                for term, prod in sorted(row.items()):
                    self.table_text.insert(tk.END, f"Table[{nt:15}, {term:10}] = {' '.join(prod)}\n")
        else:
            engine = self.parser_manager.slr_engine if active_mode == "SLR" else self.parser_manager.lalr_engine
            
            self.first_text.insert(tk.END, f"=== CANONICAL STATES COLLECTION ({len(engine.states)} States) ===\n\n")
            for idx, state in enumerate(engine.states):
                name = engine.state_names[idx] if hasattr(engine, "state_names") else f"I{idx}"
                self.first_text.insert(tk.END, f"State {name}:\n")
                for item in sorted(list(state)):
                    lhs, rhs, dot = item[0], item[1], item[2]
                    rhs_l = list(rhs)
                    rhs_l.insert(dot, ".")
                    prod_str = " ".join(rhs_l)
                    
                    if len(item) == 4: # LALR
                        self.first_text.insert(tk.END, f"  [{lhs} -> {prod_str} , '{item[3]}']\n")
                    else: # SLR
                        self.first_text.insert(tk.END, f"  [{lhs} -> {prod_str}]\n")
                self.first_text.insert(tk.END, "\n")
                
            self.follow_text.insert(tk.END, "=== GRAMMAR FIRST SETS ===\n")
            for nt, first_set in sorted(self.first.items()):
                self.follow_text.insert(tk.END, f"FIRST({nt:15}) = {{ {', '.join(sorted(first_set))} }}\n")
            self.follow_text.insert(tk.END, "\n=== GRAMMAR FOLLOW SETS ===\n")
            for nt, follow_set in sorted(self.follow.items()):
                self.follow_text.insert(tk.END, f"FOLLOW({nt:14}) = {{ {', '.join(sorted(follow_set))} }}\n")
                
            self.table_text.insert(tk.END, f"=== LR ACTION & GOTO PARSING TABLES ===\n\n")
            for (st, term), act in sorted(engine.action_table.items()):
                st_name = engine.state_names[st] if hasattr(engine, "state_names") else f"I{st}"
                self.table_text.insert(tk.END, f"ACTION[{st_name:8}, {term:8}] = {act}\n")
            self.table_text.insert(tk.END, "\n")
            for (st, nt), nxt_st in sorted(engine.goto_table.items()):
                st_name = engine.state_names[st] if hasattr(engine, "state_names") else f"I{st}"
                nxt_name = engine.state_names[nxt_st] if hasattr(engine, "state_names") else f"I{nxt_st}"
                self.table_text.insert(tk.END, f"GOTO  [{st_name:8}, {nt:8}] = {nxt_name}\n")
                
        self.first_text.configure(state="disabled")
        self.follow_text.configure(state="disabled")
        self.table_text.configure(state="disabled")

    def change_parser_mode(self, choice):
        self.parser_manager.set_parser_mode(choice)
        self.log_compiler(f"Active syntax analyzer switched to: {choice}")
        self.nav_buttons["trace"].configure(text=f"  {choice} Stack Trace")
        
        if hasattr(self, "tokens") and self.tokens:
            self.run_syntax_phase_only()

    def run_syntax_phase_only(self):
        if not hasattr(self, "educational_tokens") or not self.educational_tokens:
            return
            
        active_mode = self.parser_manager.get_active_parser_name()
        self.parse_result = self.parser_manager.parse(self.educational_tokens)
        
        if not self.parse_result["success"] or len(self.educational_tokens) == 0:
            baseline_source = "rakho limit = 4;\nbol limit;"
            from semantic.error_manager import CompilerErrorManager
            err_mgr = CompilerErrorManager()
            baseline_lexer = Lexer(baseline_source, err_mgr)
            baseline_tokens = baseline_lexer.tokenize()
            self.parse_result = self.parser_manager.parse(baseline_tokens)
            
        self.update_trace_display()
        self.tree_viz.draw_tree(self.parse_result["tree"])
        self.update_cfg_display()
        
        if active_mode != "LL(1)":
            engine = self.parser_manager.slr_engine if active_mode == "SLR" else self.parser_manager.lalr_engine
            state_names = engine.state_names if hasattr(engine, "state_names") else None
            merge_logs = engine.merge_logs if hasattr(engine, "merge_logs") else None
            self.lr_dfa_viz.draw_dfa(active_mode, engine.states, engine.transitions, state_names, merge_logs)
        else:
            self.lr_dfa_viz.show_overlay()
            
        self.update_parser_comparison_metrics()
        self.refresh_analytics_telemetry()

    def update_parser_comparison_metrics(self):
        if not hasattr(self, "educational_tokens") or not self.educational_tokens:
            self.parser_cmp_viz.update_metrics(0, 0, 0, 0, 0, 0, 0)
            return
            
        ll1_res = self.parser_manager.ll1_engine.parse(self.educational_tokens)
        slr_res = self.parser_manager.slr_engine.parse(self.educational_tokens)
        lalr_res = self.parser_manager.lalr_engine.parse(self.educational_tokens)
        
        ll1_steps = len(ll1_res["trace"]) if "trace" in ll1_res else 0
        slr_steps = len(slr_res["trace"]) if "trace" in slr_res else 0
        lalr_steps = len(lalr_res["trace"]) if "trace" in lalr_res else 0
        
        slr_states = len(self.parser_manager.slr_engine.states)
        lalr_states = len(self.parser_manager.lalr_engine.states)
        
        slr_conf = len(self.parser_manager.slr_engine.conflicts)
        lalr_conf = len(self.parser_manager.lalr_engine.conflicts)
        
        self.parser_cmp_viz.update_metrics(
            ll1_steps, slr_steps, lalr_steps, 
            slr_states, lalr_states, 
            slr_conf, lalr_conf
        )

    def refresh_analytics_telemetry(self):
        if not hasattr(self, "parse_result") or not self.parse_result:
            return
            
        active_mode = self.parser_manager.get_active_parser_name()
        if active_mode == "LL(1)":
            profile = "LL(1) (Top-Down)"
        else:
            engine = self.parser_manager.slr_engine if active_mode == "SLR" else self.parser_manager.lalr_engine
            profile = f"{active_mode} ({len(engine.states)} States, {len(engine.conflicts)} Conflicts)"

        # Read active metrics values safely
        metrics = {
            "tokens": len(self.tokens),
            "parser_time": getattr(self, "elapsed_ms", 0.0),
            "ast_depth": getattr(self, "max_depth", 0),
            "ast_depth_path": getattr(self, "ast_depth_path", [0]),
            "orig_tac_len": len(getattr(self, "orig_tac_lines", [])),
            "opt_tac_len": len(getattr(self, "opt_tac_lines", [])),
            "opt_ratio": getattr(self, "opt_ratio", 1.0),
            "reduction": getattr(self, "reduction_pct", 0.0),
            "cycles": len(self.vm.instructions),
            "parser_profile": profile
        }
        self.tabs["analytics"].update_telemetry(metrics)

    def update_trace_display(self):
        for item in self.trace_tree.get_children(): self.trace_tree.delete(item)
        if self.parse_result and "trace" in self.parse_result:
            for s in self.parse_result["trace"]: 
                self.trace_tree.insert("", "end", values=(s["stack"], s["input"], s["action"]))

    def update_scoped_symbols_display(self):
        for item in self.scoped_sym_tree.get_children(): self.scoped_sym_tree.delete(item)
        for sym in self.semantic_analyzer.symbols_list:
            mock_val = sym.value if sym.value is not None else "-"
            self.scoped_sym_tree.insert("", "end", values=(sym.name, sym.datatype, sym.scope, str(mock_val), sym.address, sym.line))

    def update_ir_tab_views(self, tac_lines, quadruples):
        # 1. TAC text
        self.tac_textbox.configure(state="normal")
        self.tac_textbox.delete("1.0", tk.END)
        for line in tac_lines:
            self.tac_textbox.insert(tk.END, f"{line}\n")
        self.tac_textbox.configure(state="disabled")

        # 2. Quadruples Tree
        for item in self.quad_tree.get_children(): self.quad_tree.delete(item)
        for q in quadruples:
            self.quad_tree.insert("", "end", values=q.to_tuple())
            
        # 3. Triples Tree
        for item in self.triple_tree.get_children(): self.triple_tree.delete(item)
        for idx, q in enumerate(quadruples):
            self.triple_tree.insert("", "end", values=(f"({idx})", q.op, q.arg1, q.arg2))

    def update_optimizer_comparisons(self, orig_tac, opt_tac):
        self.orig_tac_text.configure(state="normal")
        self.orig_tac_text.delete("1.0", tk.END)
        for line in orig_tac: self.orig_tac_text.insert(tk.END, f"{line}\n")
        self.orig_tac_text.configure(state="disabled")
        
        self.opt_tac_text.configure(state="normal")
        self.opt_tac_text.delete("1.0", tk.END)
        for line in opt_tac: self.opt_tac_text.insert(tk.END, f"{line}\n")
        self.opt_tac_text.configure(state="disabled")
        
        self.opt_log_text.configure(state="normal")
        self.opt_log_text.delete("1.0", tk.END)
        for log in self.tac_optimizer.logs: self.opt_log_text.insert(tk.END, f"{log}\n")
        self.opt_log_text.configure(state="disabled")

    def update_asm_textbox(self, asm_lines):
        self.asm_textbox.configure(state="normal")
        self.asm_textbox.delete("1.0", tk.END)
        for line in asm_lines: self.asm_textbox.insert(tk.END, f"{line}\n")
        self.asm_textbox.configure(state="disabled")

    # ====================================================
    # VM ASSEMBLY STEP DEBUGGER ACTIONS
    # ====================================================

    def reset_vm_simulation(self):
        raw_asm_lines = self.asm_textbox.get("1.0", tk.END).splitlines()
        self.debugger.load_program(raw_asm_lines, master_widget=self)
        self.vm_is_running = False
        self.btn_vm_run.configure(text="Auto Run", fg_color="#2ecc71", hover_color="#27ae60")
        
        # Reset console textbox
        self.vm_console_text.configure(state="normal")
        self.vm_console_text.delete("1.0", tk.END)
        self.vm_console_text.insert(tk.END, "--- VM Stack Machine Log Console initialized ---\n")
        self.vm_console_text.configure(state="disabled")
        
        self.update_debugger_highlights()
        self.vm_dash.update_dashboard(self.vm)

    def update_debugger_highlights(self):
        # 1. Highlight Assembly active line
        asm_line = self.debugger.get_current_asm_line()
        self.asm_textbox.configure(state="normal")
        self.asm_textbox.tag_remove("active_line", "1.0", tk.END)
        if not self.vm.halted:
            self.asm_textbox.tag_add("active_line", f"{asm_line}.0", f"{asm_line}.end")
            self.asm_textbox.tag_config("active_line", background="#293d52", foreground="#f1c40f")
            self.asm_textbox.see(f"{asm_line}.0")
        self.asm_textbox.configure(state="disabled")

        # 2. Highlight Source Code active line
        src_line = self.debugger.get_current_source_line()
        self.code_editor.editor.tag_remove("active_line", "1.0", tk.END)
        if not self.vm.halted:
            self.code_editor.editor.tag_add("active_line", f"{src_line}.0", f"{src_line}.end")
            self.code_editor.editor.tag_config("active_line", background="#2a2a2a")
            self.code_editor.editor.see(f"{src_line}.0")

        # 3. Highlight TAC active line
        tac_idx = self.debugger.get_current_tac_index()
        self.tac_textbox.configure(state="normal")
        self.tac_textbox.tag_remove("active_line", "1.0", tk.END)
        if not self.vm.halted:
            self.tac_textbox.tag_add("active_line", f"{tac_idx + 1}.0", f"{tac_idx + 1}.end")
            self.tac_textbox.tag_config("active_line", background="#293d52", foreground="#f1c40f")
            self.tac_textbox.see(f"{tac_idx + 1}.0")
        self.tac_textbox.configure(state="disabled")

    def on_debugger_step(self):
        # Update VM console with printed contents
        self.vm_console_text.configure(state="normal")
        self.vm_console_text.delete("1.0", tk.END)
        self.vm_console_text.insert(tk.END, "--- Real-Time Console Output ---\n")
        for line in self.vm.console_output:
            self.vm_console_text.insert(tk.END, f"> {line}\n")
            
        # Append debug step log
        if self.vm.logs:
            self.vm_console_text.insert(tk.END, f"\nExecution Step: {self.vm.logs[-1]}\n")
            
        self.vm_console_text.configure(state="disabled")
        
        self.update_debugger_highlights()
        self.vm_dash.update_dashboard(self.vm)
        
        if self.vm.halted:
            self.vm_is_running = False
            self.btn_vm_run.configure(text="Auto Run", fg_color="#2ecc71", hover_color="#27ae60")
            self.stat_vm.configure(text="HALTED", text_color="#e74c3c")
            messagebox.showinfo("VM State", "Program finished running successfully! Execution halted.")

    def step_vm(self):
        if self.vm.halted:
            messagebox.showinfo("VM State", "Program execution halted or completed. Click Reset to start again.")
            return

        success = self.debugger.step_into()
        self.on_debugger_step()

    def step_over_vm(self):
        if self.vm.halted:
            messagebox.showinfo("VM State", "Program execution halted or completed. Click Reset to start again.")
            return

        success = self.debugger.step_over()
        self.on_debugger_step()

    def toggle_vm_auto_run(self):
        if self.vm_is_running:
            self.vm_is_running = False
            self.debugger.pause()
            self.btn_vm_run.configure(text="Auto Run", fg_color="#2ecc71", hover_color="#27ae60")
        else:
            if self.vm.halted:
                messagebox.showinfo("VM State", "Program already halted. Click Reset.")
                return
            self.vm_is_running = True
            self.btn_vm_run.configure(text="Pause", fg_color="#e67e22", hover_color="#d35400")
            self.debugger.start_auto(self.on_debugger_step)

    def export_compiler_report(self):
        from tkinter import filedialog
        from utils.report_generator import CompilerReportGenerator
        
        path = filedialog.asksaveasfilename(
            title="Export Compiler Analysis Dossier",
            defaultextension=".txt",
            filetypes=[
                ("Text Engineering Report", "*.txt"),
                ("HTML Interactive Dossier", "*.html")
            ]
        )
        if not path:
            return
            
        # Collect pipeline metadata
        data = {
            "source_code": self.code_editor.get("1.0", tk.END),
            "tokens": self.tokens,
            "symbols": self.semantic_analyzer.symbols_list,
            "first": self.first,
            "follow": self.follow,
            "tac_lines": self.ir_generator.tac_instructions,
            "asm_lines": self.asm_textbox.get("1.0", tk.END).splitlines(),
            "vm_console": self.vm.console_output,
            "vm_logs": self.vm.logs
        }
        
        try:
            if path.lower().endswith(".html"):
                content = CompilerReportGenerator.generate_html(data)
            else:
                content = CompilerReportGenerator.generate_txt(data)
                
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
                
            messagebox.showinfo("Export Success", "Desi AuraLang compilation dossier successfully exported!")
            self.log_compiler(f"Exported compiler analysis dossier to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save report: {str(e)}")
            self.log_error(f"Report export failed: {str(e)}")

    def change_theme(self, theme_name):
        self.theme_manager.apply_theme(theme_name)
        
    def change_sim_speed(self, val):
        self.debugger.delay_ms = int(float(val))

    def get_ast_depth(self, node):
        if not node:
            return 0
        node_class = node.__class__.__name__
        if node_class == "ProgramNode":
            return 1 + max([self.get_ast_depth(s) for s in getattr(node, "statements", [])], default=0)
        elif node_class in ("VarDeclNode", "AssignNode"):
            return 1 + self.get_ast_depth(getattr(node, "value", None))
        elif node_class in ("PrintNode", "ReturnNode"):
            return 1 + self.get_ast_depth(getattr(node, "expr", None))
        elif node_class in ("IfNode", "WhileNode"):
            cond_d = self.get_ast_depth(getattr(node, "cond", None))
            then_branch = getattr(node, "then_branch", [])
            else_branch = getattr(node, "else_branch", [])
            body = getattr(node, "body", [])
            then_d = max([self.get_ast_depth(s) for s in then_branch], default=0)
            else_d = max([self.get_ast_depth(s) for s in else_branch], default=0)
            body_d = max([self.get_ast_depth(s) for s in body], default=0)
            return 1 + max(cond_d, then_d, else_d, body_d)
        elif node_class == "BinaryOpNode":
            return 1 + max(self.get_ast_depth(getattr(node, "left", None)), self.get_ast_depth(getattr(node, "right", None)))
        elif node_class == "FuncCallNode":
            return 1 + max([self.get_ast_depth(arg) for arg in getattr(node, "args", [])], default=0)
        elif node_class == "FuncDeclNode":
            body = getattr(node, "body", [])
            return 1 + max([self.get_ast_depth(s) for s in body], default=0)
        return 1

def run_app():
    app = CompilerApp(); app.mainloop()

if __name__ == "__main__":
    run_app()