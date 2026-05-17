import tkinter as tk
import customtkinter as ctk
import math

class PipelineVisualizer(ctk.CTkFrame):
    def __init__(self, master, tab_jump_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        
        self.tab_jump_callback = tab_jump_callback
        self.is_detailed = tk.BooleanVar(value=True)

        # Header controls
        self.controls = ctk.CTkFrame(self, fg_color="#181818", corner_radius=12, height=45)
        self.controls.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.controls, text="📊 Live Pipeline Flow", 
                     font=ctk.CTkFont(size=15, weight="bold"), text_color="#3498db").pack(side="left", padx=15, pady=8)
        
        self.mode_toggle = ctk.CTkSwitch(
            self.controls, text="Detailed Engineering View", variable=self.is_detailed,
            font=ctk.CTkFont(size=12, weight="bold"), command=self.redraw_pipeline
        )
        self.mode_toggle.pack(side="right", padx=15, pady=8)

        # Main interactive Canvas
        self.canvas_bg = "#0d0d0d"
        self.canvas = tk.Canvas(self, bg=self.canvas_bg, highlightthickness=0, border=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # State configurations
        self.nodes = {}
        self.connections = []
        self.glow_circle = None
        self.glow_animating = False
        self.current_glow_step = 0
        self.active_glow_path = []
        
        # Color mapping for status: IDLE, ACTIVE, SUCCESS, FAILED
        self.colors = {
            "IDLE": {"border": "#333333", "bg": "#141414", "text": "#888888"},
            "ACTIVE": {"border": "#e67e22", "bg": "#2d1a0e", "text": "#e67e22"},
            "SUCCESS": {"border": "#2ecc71", "border_hex": "#2ecc71", "bg": "#122015", "text": "#2ecc71"},
            "FAILED": {"border": "#e74c3c", "bg": "#291515", "text": "#e74c3c"}
        }

        # Bind window resizing
        self.canvas.bind("<Configure>", lambda e: self.redraw_pipeline())
        
        # Tooltip overlays
        self.tooltip_id = None
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def define_layout(self):
        """
        Calculates grid paths and node structures dynamically based on current width/height.
        """
        w = max(600, self.canvas.winfo_width())
        h = max(400, self.canvas.winfo_height())
        
        # Define 9 pipeline steps
        # Grid Coordinates calculated in % of canvas dimensions
        self.node_defs = [
            # Row 1 (Left to Right)
            {"id": "src", "title": "1. Source Input", "sub": "Raw AuraLang Code", "x": 0.15, "y": 0.18, "tab": "code",
             "desc": "Input stream reading untyped South Asian vocabulary.", "in": "Keyboard Input", "out": "Source String"},
            {"id": "lex", "title": "2. Lexical Analyzer", "sub": "Token Stream", "x": 0.45, "y": 0.18, "tab": "token",
             "desc": "Groups characters into tokens, skips comments and spacing.", "in": "Source String", "out": "Token Stream"},
            {"id": "syn", "title": "3. LL(1) Parser", "sub": "Parse Tree", "x": 0.75, "y": 0.18, "tab": "tree",
             "desc": "Checks tokens against grammar rules using LL(1) stack trace.", "in": "Token Stream", "out": "Derivation Tree"},
             
            # Row 2 (Right to Left)
            {"id": "ast", "title": "4. AST Generator", "sub": "Simplified AST", "x": 0.75, "y": 0.50, "tab": "ast",
             "desc": "Recursive descent constructs Abstract Syntax Tree.", "in": "Token Stream", "out": "Abstract Syntax Tree"},
            {"id": "sem", "title": "5. Semantic Checker", "sub": "Type-Checked Symbol Table", "x": 0.45, "y": 0.50, "tab": "scoped_sym",
             "desc": "Verifies scope binding and enforces strict type matchings.", "in": "AST Tree", "out": "Verified AST & Symbols"},
            {"id": "ir",  "title": "6. TAC Generator", "sub": "Three-Address Code", "x": 0.15, "y": 0.50, "tab": "ir",
             "desc": "Translates code into linear quadruples/triples basic blocks.", "in": "Verified AST", "out": "Intermediate TAC"},
             
            # Row 3 (Left to Right)
            {"id": "opt", "title": "7. TAC Optimizer", "sub": "Constant Folded TAC", "x": 0.15, "y": 0.82, "tab": "opt",
             "desc": "Applies dead code extraction and constant reduction passes.", "in": "Intermediate TAC", "out": "Optimized TAC"},
            {"id": "tgt", "title": "8. Target Codegen", "sub": "Stack VM Assembly", "x": 0.45, "y": 0.82, "tab": "vm",
             "desc": "Translates optimized quadruples into custom assembler.", "in": "Optimized TAC", "out": "VM Assembler"},
            {"id": "vm",  "title": "9. Virtual Machine", "sub": "CPU Execution Simulator", "x": 0.75, "y": 0.82, "tab": "vm",
             "desc": "Step-by-step CPU debugger with Stack & Heap blocks.", "in": "VM Bytecode", "out": "System Output Console"},
        ]

        # Detailed view reveals extra middle checkpoints
        if self.is_detailed.get():
            self.node_defs.append({"id": "ff", "title": "FIRST/FOLLOW", "sub": "Grammar Tables", "x": 0.60, "y": 0.18, "tab": "cfg",
                                   "desc": "Calculates FIRST/FOLLOW sets dynamically to generate the LL(1) parse table.", "in": "CFG Rules", "out": "Parsing Table"})
            self.node_defs.append({"id": "sym_tab", "title": "Lex Symbol Table", "sub": "Lexeme Addresses", "x": 0.45, "y": 0.34, "tab": "sym",
                                   "desc": "Tracks basic identifiers, lexemes, and mapping addresses during lexical scan.", "in": "Token Stream", "out": "Lexeme Map"})
            self.node_defs.append({"id": "opt_cmp", "title": "Optimizer Comparison", "sub": "Quadruples Diff", "x": 0.30, "y": 0.82, "tab": "opt",
                                   "desc": "Illustrates comparative side-by-side instruction reductions.", "in": "Optimized TAC", "out": "Reduced Quads"})

    def redraw_pipeline(self):
        self.canvas.delete("all")
        self.define_layout()
        
        w = max(600, self.canvas.winfo_width())
        h = max(400, self.canvas.winfo_height())

        # Reset states
        self.nodes.clear()
        self.connections.clear()

        # Scale definitions coordinates to actual width and height
        for nd in self.node_defs:
            nd["ax"] = nd["x"] * w
            nd["ay"] = nd["y"] * h

        # 1. Draw Connections (Laser Lines)
        # Establish sorted path order
        path_ids = ["src", "lex", "ff", "syn", "ast", "sem", "ir", "opt", "tgt", "vm"]
        # Filter existing paths matching layout
        active_ids = [pid for pid in path_ids if any(nd["id"] == pid for nd in self.node_defs)]
        
        # Add special auxiliary table links if present
        for i in range(len(active_ids) - 1):
            n1 = next(nd for nd in self.node_defs if nd["id"] == active_ids[i])
            n2 = next(nd for nd in self.node_defs if nd["id"] == active_ids[i+1])
            
            # Draw connecting arrow line
            line_id = self.canvas.create_line(
                n1["ax"], n1["ay"], n2["ax"], n2["ay"],
                fill="#2c3e50", width=3, arrow="last", arrowshape=(10, 12, 5)
            )
            self.connections.append({
                "line_id": line_id, "from": n1["id"], "to": n2["id"],
                "x1": n1["ax"], "y1": n1["ay"], "x2": n2["ax"], "y2": n2["ay"]
            })

        # Draw extra auxiliary connecting nodes
        if self.is_detailed.get():
            # Connect Lexer -> Lex Symbol Table
            lex = next(nd for nd in self.node_defs if nd["id"] == "lex")
            symt = next(nd for nd in self.node_defs if nd["id"] == "sym_tab")
            self.canvas.create_line(lex["ax"], lex["ay"], symt["ax"], symt["ay"], fill="#2c3e50", width=2, dash=(4,4))

        # 2. Draw Nodes (Glassmorphic Cards)
        node_width = 135
        node_height = 55
        
        for nd in self.node_defs:
            x, y = nd["ax"], nd["ay"]
            
            # Check current node status
            status = getattr(nd, "status", "IDLE")
            style = self.colors.get(status, self.colors["IDLE"])
            
            # Determine card boundaries
            x1, y1 = x - node_width/2, y - node_height/2
            x2, y2 = x + node_width/2, y + node_height/2
            
            # Card Background
            rect_bg = self.canvas.create_rectangle(
                x1, y1, x2, y2, fill=style["bg"], 
                outline=style.get("border_hex", style["border"]), width=2, tags=(nd["id"], "node")
            )
            
            # Card Title text
            title_id = self.canvas.create_text(
                x, y - 10, text=nd["title"], fill=style["text"],
                font=("Consolas", 10, "bold"), justify="center", tags=(nd["id"], "node")
            )
            
            # Card Subtext
            sub_id = self.canvas.create_text(
                x, y + 12, text=nd["sub"], fill="#7f8c8d",
                font=("Consolas", 8), justify="center", tags=(nd["id"], "node")
            )
            
            # Save visual identifiers
            self.nodes[nd["id"]] = {
                "def": nd, "bg_id": rect_bg, "title_id": title_id, "sub_id": sub_id,
                "x1": x1, "y1": y1, "x2": x2, "y2": y2
            }
            
            # Bind direct double-click to jump to IDE Tab
            if nd.get("tab") and self.tab_jump_callback:
                self.canvas.tag_bind(nd["id"], "<Double-Button-1>", lambda e, t=nd["tab"]: self.tab_jump_callback(t))
                self.canvas.tag_bind(nd["id"], "<Button-1>", lambda e, t=nd["tab"]: self.tab_jump_callback(t))

    def update_node_status(self, node_id, status):
        """
        Dynamically updates a node's color style and redraws its state.
        """
        for nd in self.node_defs:
            if nd["id"] == node_id:
                nd["status"] = status
                break
        self.redraw_pipeline()

    # ---------- GLOW PULSE TRANSITION TRANSFERS ----------
    def animate_transition(self, from_id, to_id, callback=None):
        """
        Draws a glowing light pulse traveling down the connector line from `from_id` to `to_id`.
        """
        # Find active connection
        conn = None
        for c in self.connections:
            if c["from"] == from_id and c["to"] == to_id:
                conn = c
                break
                
        if not conn:
            if callback: callback()
            return
            
        # Draw glowing pulse circle
        self.glow_circle = self.canvas.create_oval(
            conn["x1"]-6, conn["y1"]-6, conn["x1"]+6, conn["y1"]+6,
            fill="#3498db", outline="#5dade2", width=2
        )
        
        self.glow_animating = True
        self.current_glow_step = 0
        self.active_glow_path = conn
        
        self._step_glow_animation(callback)

    def _step_glow_animation(self, callback):
        if not self.glow_animating or not self.active_glow_path:
            return
            
        conn = self.active_glow_path
        total_steps = 15
        
        # Calculate intermediate step coordinates
        self.current_glow_step += 1
        t = self.current_glow_step / total_steps
        
        # Linear interpolation
        cx = conn["x1"] + (conn["x2"] - conn["x1"]) * t
        cy = conn["y1"] + (conn["y2"] - conn["y1"]) * t
        
        # Move glow bubble
        self.canvas.coords(self.glow_circle, cx-6, cy-6, cx+6, cy+6)
        
        if self.current_glow_step >= total_steps:
            # End animation
            self.canvas.delete(self.glow_circle)
            self.glow_animating = False
            self.active_glow_path = []
            if callback:
                callback()
        else:
            self.canvas.after(25, lambda: self._step_glow_animation(callback))

    # ---------- INTERACTIVE HOVER TOOLTIPS ----------
    def on_mouse_move(self, event):
        # Clear existing tooltip
        if self.tooltip_id:
            self.canvas.delete(self.tooltip_id)
            self.tooltip_id = None
            
        # Detect if mouse is over any node
        x, y = event.x, event.y
        hovered_node = None
        
        for nid, ninfo in self.nodes.items():
            if ninfo["x1"] <= x <= ninfo["x2"] and ninfo["y1"] <= y <= ninfo["y2"]:
                hovered_node = ninfo["def"]
                break
                
        if not hovered_node:
            return
            
        # Draw dynamic pop-up tooltip window
        self.draw_tooltip(x, y, hovered_node)

    def draw_tooltip(self, mx, my, nd):
        tw, th = 280, 130
        
        # Determine positioning offsets
        tx = mx + 20
        ty = my + 20
        
        # Boundary limits
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if tx + tw > cw: tx = mx - tw - 20
        if ty + th > ch: ty = my - th - 20
        
        # Tooltip group ID
        self.tooltip_id = "tooltip"
        
        # Sleek glassmorphic backdrop
        self.canvas.create_rectangle(
            tx, ty, tx+tw, ty+th, fill="#1c1c1c", outline="#3498db", 
            width=2, tags=self.tooltip_id, stipple=""
        )
        
        # Title text
        self.canvas.create_text(
            tx + 15, ty + 15, text=nd["title"], fill="#3498db",
            font=("Consolas", 11, "bold"), anchor="w", tags=self.tooltip_id
        )
        
        # Description
        self.canvas.create_text(
            tx + 15, ty + 42, text=nd["desc"], fill="#ecf0f1",
            font=("Consolas", 9), anchor="w", width=250, tags=self.tooltip_id
        )
        
        # Technical Inputs/Outputs metadata
        self.canvas.create_text(
            tx + 15, ty + 85, text=f"📥 IN:  {nd['in']}", fill="#e67e22",
            font=("Consolas", 8, "bold"), anchor="w", tags=self.tooltip_id
        )
        self.canvas.create_text(
            tx + 15, ty + 105, text=f"📤 OUT: {nd['out']}", fill="#2ecc71",
            font=("Consolas", 8, "bold"), anchor="w", tags=self.tooltip_id
        )
