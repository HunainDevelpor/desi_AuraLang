import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any

class AnalyticsDashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Grid layout: 2 rows, 2 columns
        self.grid_columnconfigure(0, weight=4) # Gauge cards
        self.grid_columnconfigure(1, weight=6) # Live graphs canvas
        self.grid_rowconfigure(0, weight=1)
        
        # Left Panel (Gauge Cards list)
        self.gauges_frame = ctk.CTkScrollableFrame(self, fg_color="#141414", corner_radius=15)
        self.gauges_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.gauges_frame, text="⚡ REAL-TIME COMPILER TELEMETRY", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f1c40f").pack(pady=10)
        
        # Instantiate dynamic cards
        self.card_tokens = self.create_gauge_card(self.gauges_frame, "Tokens Scanned", "0", "#3498db")
        self.card_time = self.create_gauge_card(self.gauges_frame, "Parser Compile Time", "0.0 ms", "#9b59b6")
        self.card_depth = self.create_gauge_card(self.gauges_frame, "AST Depth", "0", "#e67e22")
        self.card_ratio = self.create_gauge_card(self.gauges_frame, "Optimization Ratio", "1.00x", "#2ecc71")
        self.card_reduction = self.create_gauge_card(self.gauges_frame, "TAC Size Reduction", "0 %", "#e74c3c")
        self.card_cycles = self.create_gauge_card(self.gauges_frame, "VM Instructions Run", "0 cycles", "#1abc9c")
        self.card_parser = self.create_gauge_card(self.gauges_frame, "Parser Active Profile", "LL(1) (Top-Down)", "#f1c40f")
        
        # Right Panel (Custom Canvas charts)
        self.chart_frame = ctk.CTkFrame(self, fg_color="#141414", corner_radius=15)
        self.chart_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(1, weight=1)
        
        # Chart 1: TAC Instructions Count (Original vs Optimized)
        self.bar_chart_title = ctk.CTkLabel(self.chart_frame, text="📊 COMPILATION INSTRUCTION EFFICIENCY", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3498db")
        self.bar_chart_title.pack(pady=(10, 0))
        
        self.bar_canvas = tk.Canvas(self.chart_frame, bg="#0e0e0f", highlightthickness=0, height=180)
        self.bar_canvas.pack(fill="x", padx=20, pady=10)
        
        # Chart 2: AST Complexity Scale
        self.line_chart_title = ctk.CTkLabel(self.chart_frame, text="📈 AST GRAMMATICAL COMPLEXITY PATH", font=ctk.CTkFont(size=13, weight="bold"), text_color="#2ecc71")
        self.line_chart_title.pack(pady=(10, 0))
        
        self.line_canvas = tk.Canvas(self.chart_frame, bg="#0e0e0f", highlightthickness=0, height=180)
        self.line_canvas.pack(fill="x", padx=20, pady=10)

        # Initial charts load
        self.draw_bar_chart(0, 0)
        self.draw_line_chart([0])

    def create_gauge_card(self, parent, title: str, value: str, color: str) -> Dict[str, Any]:
        card = ctk.CTkFrame(parent, fg_color="#1c1c1e", corner_radius=10, height=65)
        card.pack(fill="x", pady=5, padx=10)
        card.pack_propagate(False)
        
        marker = ctk.CTkFrame(card, width=5, fg_color=color, corner_radius=0)
        marker.pack(side="left", fill="y")
        
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        title_lbl = ctk.CTkLabel(text_frame, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color="#7f8c8d", anchor="w")
        title_lbl.pack(fill="x", pady=(8, 0))
        
        val_lbl = ctk.CTkLabel(text_frame, text=value, font=ctk.CTkFont(size=18, weight="bold"), text_color=color, anchor="w")
        val_lbl.pack(fill="x")
        
        return {"value_lbl": val_lbl}

    def update_telemetry(self, metrics: Dict[str, Any]):
        """Updates numeric values of metrics dynamically."""
        self.card_tokens["value_lbl"].configure(text=str(metrics.get("tokens", 0)))
        self.card_time["value_lbl"].configure(text=f"{metrics.get('parser_time', 0.0):.2f} ms")
        self.card_depth["value_lbl"].configure(text=str(metrics.get("ast_depth", 0)))
        
        ratio = metrics.get("opt_ratio", 1.0)
        self.card_ratio["value_lbl"].configure(text=f"{ratio:.2f}x")
        
        reduction = metrics.get("reduction", 0.0)
        self.card_reduction["value_lbl"].configure(text=f"{reduction:.1f} %")
        
        cycles = metrics.get("cycles", 0)
        self.card_cycles["value_lbl"].configure(text=f"{cycles} instrs")
        
        parser_profile = metrics.get("parser_profile", "LL(1) (Top-Down)")
        self.card_parser["value_lbl"].configure(text=str(parser_profile))
        
        # Redraw charts with active metrics
        self.draw_bar_chart(metrics.get("orig_tac_len", 0), metrics.get("opt_tac_len", 0))
        
        ast_depths = metrics.get("ast_depth_path", [0])
        self.draw_line_chart(ast_depths)

    def draw_bar_chart(self, orig_len: int, opt_len: int):
        """Draws comparative vertical bar chart representing instruction minimization."""
        self.bar_canvas.delete("all")
        w, h = 450, 160
        
        # Draw background grid lines
        for i in range(1, 4):
            y = h - (h * i / 4)
            self.bar_canvas.create_line(40, y, w - 20, y, fill="#1c1c1f", width=1)
            
        # Draw axes
        self.bar_canvas.create_line(40, h - 20, w - 20, h - 20, fill="#333", width=2) # X
        self.bar_canvas.create_line(40, 10, 40, h - 20, fill="#333", width=2) # Y
        
        # Calculate heights relative to max
        max_len = max(orig_len, opt_len, 5)
        scale = (h - 40) / max_len
        
        h_orig = int(orig_len * scale)
        h_opt = int(opt_len * scale)
        
        # Bar coordinates
        x1_orig, x2_orig = 100, 180
        y1_orig = h - 20 - h_orig
        
        x1_opt, x2_opt = 260, 340
        y1_opt = h - 20 - h_opt
        
        # Draw Original TAC Bar (Red-Orange accent)
        self.bar_canvas.create_rectangle(x1_orig, y1_orig, x2_orig, h - 20, fill="#e67e22", outline="", width=0)
        self.bar_canvas.create_text((x1_orig + x2_orig) // 2, y1_orig - 10, text=f"{orig_len}", fill="#e67e22", font=("Arial", 9, "bold"))
        self.bar_canvas.create_text((x1_orig + x2_orig) // 2, h - 10, text="Original TAC", fill="#7f8c8d", font=("Arial", 9))
        
        # Draw Optimized TAC Bar (Green accent)
        self.bar_canvas.create_rectangle(x1_opt, y1_opt, x2_opt, h - 20, fill="#2ecc71", outline="", width=0)
        self.bar_canvas.create_text((x1_opt + x2_opt) // 2, y1_opt - 10, text=f"{opt_len}", fill="#2ecc71", font=("Arial", 9, "bold"))
        self.bar_canvas.create_text((x1_opt + x2_opt) // 2, h - 10, text="Optimized TAC", fill="#7f8c8d", font=("Arial", 9))

    def draw_line_chart(self, values: list):
        """Draws line chart representing depth scale values of statements parsing."""
        self.line_canvas.delete("all")
        w, h = 450, 160
        
        if not values or len(values) == 0:
            values = [0]
            
        # Draw background grid
        for i in range(1, 4):
            y = h - (h * i / 4)
            self.line_canvas.create_line(40, y, w - 20, y, fill="#1c1c1f", width=1)
            
        # Draw axes
        self.line_canvas.create_line(40, h - 20, w - 20, h - 20, fill="#333", width=2) # X
        self.line_canvas.create_line(40, 10, 40, h - 20, fill="#333", width=2) # Y
        
        max_val = max(max(values), 5)
        y_scale = (h - 40) / max_val
        
        # Calculate step width based on length
        num_pts = len(values)
        x_step = (w - 80) / max(num_pts - 1, 1)
        
        points = []
        for idx, val in enumerate(values):
            x = 40 + idx * x_step
            y = h - 20 - (val * y_scale)
            points.append((x, y))
            
        # Draw dynamic connecting lines
        for idx in range(len(points) - 1):
            p1 = points[idx]
            p2 = points[idx + 1]
            self.line_canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#2ecc71", width=2)
            # Subtle node circle
            self.line_canvas.create_oval(p1[0] - 3, p1[1] - 3, p1[0] + 3, p1[1] + 3, fill="#ffffff", outline="#2ecc71")
            
        # Draw last point circle
        if points:
            lp = points[-1]
            self.line_canvas.create_oval(lp[0] - 3, lp[1] - 3, lp[0] + 3, lp[1] + 3, fill="#ffffff", outline="#2ecc71")
            self.line_canvas.create_text(lp[0], lp[1] - 12, text=f"D:{values[-1]}", fill="#ffffff", font=("Arial", 8, "bold"))
            
        self.line_canvas.create_text(w // 2, h - 5, text="AST Statements (Sequential Traverse)", fill="#7f8c8d", font=("Arial", 9))
