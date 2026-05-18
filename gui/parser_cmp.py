import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any

class ParserComparisonDashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Grid layout
        self.grid_columnconfigure(0, weight=6) # Comparative grid & Bar chart
        self.grid_columnconfigure(1, weight=4) # Educational description cards
        self.grid_rowconfigure(0, weight=1)
        
        self.create_widgets()

    def create_widgets(self):
        # ----------------------------------------------------
        # LEFT PANEL: Comparative Matrix & Metrics Chart
        # ----------------------------------------------------
        self.left_panel = ctk.CTkScrollableFrame(self, fg_color="#141414", corner_radius=15)
        self.left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            self.left_panel, 
            text="📊 EDUCATIONAL PARSER COMPARISON DASHBOARD", 
            font=ctk.CTkFont(size=14, weight="bold"), 
            text_color="#f1c40f"
        ).pack(pady=10)
        
        # 1. Comparison Matrix Treeview
        self.table_frame = ctk.CTkFrame(self.left_panel, fg_color="#1c1c1f", corner_radius=10)
        self.table_frame.pack(fill="x", padx=15, pady=5)
        
        # Custom Treeview widget
        style = tk.ttk.Style()
        style.theme_use("default")
        style.configure(
            "CustomCompare.Treeview",
            background="#121214",
            foreground="#ecf0f1",
            rowheight=28,
            fieldbackground="#121214",
            bordercolor="#333",
            borderwidth=1,
            font=("Segoe UI", 10)
        )
        style.configure("CustomCompare.Treeview.Heading", background="#1c1c1f", foreground="#bdc3c7", font=("Segoe UI", 10, "bold"))
        
        self.tree = tk.ttk.Treeview(
            self.table_frame,
            columns=("Metric", "LL(1)", "SLR", "LALR"),
            show="headings",
            style="CustomCompare.Treeview",
            height=8
        )
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree.heading("Metric", text="Parser Metric")
        self.tree.heading("LL(1)", text="LL(1) (Top-Down)")
        self.tree.heading("SLR", text="SLR (Bottom-Up)")
        self.tree.heading("LALR", text="LALR (Bottom-Up)")
        
        self.tree.column("Metric", width=160, anchor="w")
        self.tree.column("LL(1)", width=130, anchor="center")
        self.tree.column("SLR", width=130, anchor="center")
        self.tree.column("LALR", width=130, anchor="center")
        
        # Populate Static Comparative rows
        self.populate_comparison_matrix(0, 0, 0, 0, 0, 0)
        
        # 2. Comparative Steps Bar Chart
        ctk.CTkLabel(
            self.left_panel, 
            text="📊 ACTIVE EXECUTION STEPS COMPARISON (LOWER IS MORE EFFICIENT)", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#3498db"
        ).pack(pady=(15, 5))
        
        self.canvas_frame = ctk.CTkFrame(self.left_panel, fg_color="#0e0e0f", corner_radius=10)
        self.canvas_frame.pack(fill="x", padx=15, pady=5)
        
        self.chart_canvas = tk.Canvas(self.canvas_frame, bg="#0e0e0f", highlightthickness=0, height=160)
        self.chart_canvas.pack(fill="x", padx=15, pady=10)
        self.draw_comparison_chart(0, 0, 0)

        # ----------------------------------------------------
        # RIGHT PANEL: Educational explanations
        # ----------------------------------------------------
        self.right_panel = ctk.CTkScrollableFrame(self, fg_color="#141414", corner_radius=15)
        self.right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            self.right_panel, 
            text="📘 PARSER KNOWLEDGE CARD", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color="#e67e22"
        ).pack(pady=10)
        
        self.create_explanation_card(
            self.right_panel, 
            "LL(1) PREDICTIVE PARSING", 
            "Top-down predictive parser that processes inputs left-to-right (L), building a Leftmost derivation (L) using exactly 1 lookahead token. It requires a non-left-recursive, fully factored grammar and makes production choices before reading the inner components.",
            "#3498db"
        )
        
        self.create_explanation_card(
            self.right_panel, 
            "SLR SHIFT-REDUCE PARSING", 
            "Simple LR parser that processes inputs left-to-right, building a Reverse Rightmost derivation. It computes canonical LR(0) states and GOTO transitions. Reductions are written strictly to follow sets (FOLLOW(A)) to keep the table compact.",
            "#9b59b6"
        )
        
        self.create_explanation_card(
            self.right_panel, 
            "LALR LOOKAHEAD LR PARSING", 
            "Look-Ahead LR parser created by merging LR(1) canonical states that share identical item cores (LR(0) configurations) but differ in lookahead sets. This maintains the compact state boundaries of SLR while providing powerful lookahead routing.",
            "#2ecc71"
        )

    def populate_comparison_matrix(self, ll1_steps=0, slr_steps=0, lalr_steps=0, slr_states=0, lalr_states=0, slr_conflicts=0, lalr_conflicts=0):
        # Clear previous rows
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add dynamic comparison values
        rows = [
            ("Strategy", "Top-Down Predictive", "Bottom-Up Shift-Reduce", "Bottom-Up Shift-Reduce"),
            ("Automaton States", "N/A (Recursive Stack)", f"{slr_states} LR(0) States", f"{lalr_states} Merged LR(1) States"),
            ("Shift Actions", "0 (Predictive Expansion)", "Shift to State", "Shift to State"),
            ("Reduce Actions", "0 (Expand Epsilon)", "Reduce on FOLLOW(A)", "Reduce on Lookahead"),
            ("Active Parse Steps", f"{ll1_steps} steps", f"{slr_steps} steps", f"{lalr_steps} steps"),
            ("Conflicts Detected", "LL(1) Overlaps: 0", f"SLR conflicts: {slr_conflicts}", f"LALR conflicts: {lalr_conflicts}"),
            ("Grammar Constraints", "No Left-Recursion", "Handles Left-Recursion", "Handles Left-Recursion"),
            ("Table Size Complexity", "O(V * T) cells - Low", "O(I * T) cells - Medium", "O(I * T) cells - Optimized")
        ]
        
        for idx, r in enumerate(rows):
            self.tree.insert("", "end", values=r)

    def create_explanation_card(self, parent, title: str, text: str, color: str):
        card = ctk.CTkFrame(parent, fg_color="#1c1c1f", corner_radius=10)
        card.pack(fill="x", pady=8, padx=10)
        
        header = ctk.CTkFrame(card, height=30, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
        marker = ctk.CTkFrame(header, width=4, height=18, fg_color=color)
        marker.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=color).pack(side="left")
        
        desc = ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=10), text_color="#95a5a6", wraplength=210, justify="left")
        desc.pack(fill="x", padx=15, pady=(2, 10), anchor="w")

    def draw_comparison_chart(self, ll1_steps: int, slr_steps: int, lalr_steps: int):
        self.chart_canvas.delete("all")
        w, h = 450, 160
        
        # Grid lines
        for i in range(1, 4):
            y = h - (h * i / 4)
            self.chart_canvas.create_line(40, y, w - 20, y, fill="#1c1c1f", width=1)
            
        # Draw axes
        self.chart_canvas.create_line(40, h - 20, w - 20, h - 20, fill="#333", width=2) # X
        self.chart_canvas.create_line(40, 10, 40, h - 20, fill="#333", width=2) # Y
        
        # Normalization scale
        max_val = max(ll1_steps, slr_steps, lalr_steps, 5)
        scale = (h - 40) / max_val
        
        h_ll1 = int(ll1_steps * scale)
        h_slr = int(slr_steps * scale)
        h_lalr = int(lalr_steps * scale)
        
        # Coordinates
        x_ll1 = 70; w_bar = 60
        x_slr = 190
        x_lalr = 310
        
        # Draw LL(1) Bar (Blue)
        self.chart_canvas.create_rectangle(x_ll1, h - 20 - h_ll1, x_ll1 + w_bar, h - 20, fill="#3498db", outline="")
        self.chart_canvas.create_text(x_ll1 + w_bar//2, h - 30 - h_ll1, text=f"{ll1_steps}", fill="#3498db", font=("Arial", 9, "bold"))
        self.chart_canvas.create_text(x_ll1 + w_bar//2, h - 10, text="LL(1)", fill="#bdc3c7", font=("Arial", 9))
        
        # Draw SLR Bar (Purple)
        self.chart_canvas.create_rectangle(x_slr, h - 20 - h_slr, x_slr + w_bar, h - 20, fill="#9b59b6", outline="")
        self.chart_canvas.create_text(x_slr + w_bar//2, h - 30 - h_slr, text=f"{slr_steps}", fill="#9b59b6", font=("Arial", 9, "bold"))
        self.chart_canvas.create_text(x_slr + w_bar//2, h - 10, text="SLR", fill="#bdc3c7", font=("Arial", 9))
        
        # Draw LALR Bar (Green)
        self.chart_canvas.create_rectangle(x_lalr, h - 20 - h_lalr, x_lalr + w_bar, h - 20, fill="#2ecc71", outline="")
        self.chart_canvas.create_text(x_lalr + w_bar//2, h - 30 - h_lalr, text=f"{lalr_steps}", fill="#2ecc71", font=("Arial", 9, "bold"))
        self.chart_canvas.create_text(x_lalr + w_bar//2, h - 10, text="LALR", fill="#bdc3c7", font=("Arial", 9))

    def update_metrics(self, ll1_steps: int, slr_steps: int, lalr_steps: int, slr_states=0, lalr_states=0, slr_conflicts=0, lalr_conflicts=0):
        self.populate_comparison_matrix(ll1_steps, slr_steps, lalr_steps, slr_states, lalr_states, slr_conflicts, lalr_conflicts)
        self.draw_comparison_chart(ll1_steps, slr_steps, lalr_steps)
