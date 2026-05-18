import tkinter as tk
import customtkinter as ctk
import math
from typing import Dict, Any, List, Set, Tuple

class LrDfaVisualizer(ctk.CTkFrame):
    def __init__(self, parent, parser_manager=None):
        super().__init__(parent, fg_color="transparent")
        self.parser_manager = parser_manager
        
        # State tracking
        self.selected_state_idx = 0
        self.active_parser_type = "SLR"
        self.node_radius = 26
        
        # Grid layout
        self.grid_columnconfigure(0, weight=6) # DFA Canvas panel
        self.grid_columnconfigure(1, weight=4) # Items and Merging details inspector
        self.grid_rowconfigure(0, weight=1)
        
        self.create_widgets()

    def create_widgets(self):
        # ----------------------------------------------------
        # LEFT PANEL: DFA Canvas & Automaton
        # ----------------------------------------------------
        self.left_panel = ctk.CTkFrame(self, fg_color="#141414", corner_radius=15)
        self.left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=0) # Title / Selector
        self.left_panel.grid_rowconfigure(1, weight=1) # Scrollable canvas frame
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        # Header Toolbar
        self.toolbar = ctk.CTkFrame(self.left_panel, fg_color="transparent", height=45)
        self.toolbar.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")
        
        self.title_lbl = ctk.CTkLabel(
            self.toolbar, 
            text="🕸️ LR AUTOMATON DFA TRANSITION GRAPH", 
            font=ctk.CTkFont(size=14, weight="bold"), 
            text_color="#3498db"
        )
        self.title_lbl.pack(side="left", padx=5)
        
        self.help_lbl = ctk.CTkLabel(
            self.toolbar, 
            text="Double-click states to inspect items", 
            font=ctk.CTkFont(size=11, slant="italic"), 
            text_color="#7f8c8d"
        )
        self.help_lbl.pack(side="right", padx=10)
        
        # Canvas Container with Scrollbars for massive DFAs
        self.canvas_frame = ctk.CTkFrame(self.left_panel, fg_color="#0d0d0f", corner_radius=10)
        self.canvas_frame.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#0d0d0f", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        
        # Scrollbars
        self.v_scroll = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.v_scroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.v_scroll.set)
        
        # ----------------------------------------------------
        # RIGHT PANEL: Items & LALR Merge Log Inspector
        # ----------------------------------------------------
        self.right_panel = ctk.CTkFrame(self, fg_color="#141414", corner_radius=15)
        self.right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=1) # Items set inspector
        self.right_panel.grid_rowconfigure(1, weight=1) # LALR Merging logs
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        # 1. State Items List Inspector
        self.items_frame = ctk.CTkFrame(self.right_panel, fg_color="#1c1c1f", corner_radius=10)
        self.items_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="nsew")
        self.items_frame.grid_rowconfigure(0, weight=0)
        self.items_frame.grid_rowconfigure(1, weight=1)
        self.items_frame.grid_columnconfigure(0, weight=1)
        
        self.items_header = ctk.CTkLabel(
            self.items_frame, 
            text="🔎 STATE ITEMS SET INSPECTOR", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#e67e22"
        )
        self.items_header.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        self.items_textbox = ctk.CTkTextbox(
            self.items_frame, 
            fg_color="#101012", 
            font=("Consolas", 11),
            border_color="#2c3e50"
        )
        self.items_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.items_textbox.configure(state="disabled")
        
        # 2. State Merging Logs / Educational Info
        self.merges_frame = ctk.CTkFrame(self.right_panel, fg_color="#1c1c1f", corner_radius=10)
        self.merges_frame.grid(row=1, column=0, padx=15, pady=(10, 15), sticky="nsew")
        self.merges_frame.grid_rowconfigure(0, weight=0)
        self.merges_frame.grid_rowconfigure(1, weight=1)
        self.merges_frame.grid_columnconfigure(0, weight=1)
        
        self.merges_header = ctk.CTkLabel(
            self.merges_frame, 
            text="🔗 LALR STATE MERGING / LOGS", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#2ecc71"
        )
        self.merges_header.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        self.merges_textbox = ctk.CTkTextbox(
            self.merges_frame, 
            fg_color="#101012", 
            font=("Consolas", 11),
            border_color="#2c3e50"
        )
        self.merges_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.merges_textbox.configure(state="disabled")

        # Overlay frame to cover the view when LL(1) is selected
        self.overlay = ctk.CTkFrame(self, fg_color="#141414", corner_radius=15)
        self.overlay_lbl = ctk.CTkLabel(
            self.overlay, 
            text="⚠️ LR AUTOMATON DFA INOPERABLE IN LL(1) TOP-DOWN MODE\n\nPlease select SLR or LALR bottom-up parser modes in the sidebar.",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c"
        )
        self.overlay_lbl.pack(expand=True, padx=20, pady=20)
        
        # Setup sample view
        self.clear_views()

    def clear_views(self):
        self.canvas.delete("all")
        self.write_text(self.items_textbox, "Double-click an automaton state node to inspect item cores and transition targets.\n")
        self.write_text(self.merges_textbox, "LALR State merging reports and lookahead propagations will render here dynamically.\n")

    def write_text(self, text_widget, text: str):
        text_widget.configure(state="normal")
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, text)
        text_widget.configure(state="disabled")

    def draw_dfa(self, parser_type: str, states: list, transitions: dict, state_names: list = None, merge_logs: list = None):
        """Draws the panned/scrollable DFA transition graph on the Canvas."""
        self.overlay.place_forget() # Ensure it's hidden when drawing
        self.canvas.delete("all")
        self.active_parser_type = parser_type
        
        if not states:
            self.clear_views()
            return
            
        # Draw merge logs
        if parser_type == "LALR" and merge_logs:
            log_text = "\n".join(merge_logs)
            self.write_text(self.merges_textbox, f"=== LALR COMPRESSION DECK ===\n\n{log_text}\n")
        else:
            self.write_text(
                self.merges_textbox, 
                "=== SLR AUTOMATON PROFILE ===\n\n"
                "SLR uses standard LR(0) items without explicit lookaheads. "
                "Instead, it determines reductions strictly on grammar FOLLOW sets.\n\n"
                "No lookahead merges or propagations are required."
            )
            
        # Calculate coordinates for each state
        # Since we have many states, we arrange them in 4 columns grid:
        cols = 4
        spacing_x = 135
        spacing_y = 120
        start_x = 70
        start_y = 65
        
        state_coords = {}
        for idx in range(len(states)):
            r = idx // cols
            c = idx % cols
            
            # Simple alternating offsets to make diagonal transition arrows clearly readable
            offset_y = 20 if c % 2 == 1 else 0
            
            x = start_x + c * spacing_x
            y = start_y + r * spacing_y + offset_y
            state_coords[idx] = (x, y)
            
        # Set canvas scrolling region
        max_rows = math.ceil(len(states) / cols)
        total_h = start_y + max_rows * spacing_y + 100
        self.canvas.configure(scrollregion=(0, 0, 600, total_h))
        
        # 1. Draw Transition Arrows
        for (src, sym), dest in transitions.items():
            if src not in state_coords or dest not in state_coords:
                continue
            x1, y1 = state_coords[src]
            x2, y2 = state_coords[dest]
            
            # Highlight color defaults
            color = "#34495e"
            width = 1.5
            
            # If transition goes backwards, curve it slightly
            is_self_loop = (src == dest)
            
            if is_self_loop:
                self.draw_self_loop(x1, y1, sym, "#7f8c8d", 1.5)
            else:
                self.draw_transition_line(x1, y1, x2, y2, sym, color, width)

        # 2. Draw State Nodes
        for idx, state in enumerate(states):
            x, y = state_coords[idx]
            
            is_selected = (idx == self.selected_state_idx)
            outline_color = "#e67e22" if is_selected else "#2980b9"
            fill_color = "#2c3e50" if is_selected else "#1a1a1c"
            width = 3.5 if is_selected else 2
            
            # State label name
            lbl = state_names[idx] if state_names else f"I{idx}"
            
            # Create interactive oval
            node_tag = f"node_{idx}"
            self.canvas.create_oval(
                x - self.node_radius, y - self.node_radius,
                x + self.node_radius, y + self.node_radius,
                fill=fill_color, outline=outline_color, width=width,
                tags=("state_node", node_tag)
            )
            
            # Add state index inside circle
            self.canvas.create_text(
                x, y, text=lbl, fill="white", font=("Arial", 10, "bold"),
                tags=("state_lbl", node_tag)
            )
            
            # Bind events
            self.canvas.tag_bind(node_tag, "<Double-Button-1>", lambda e, idx=idx: self.select_state(idx, states, state_names))
            self.canvas.tag_bind(node_tag, "<Enter>", lambda e, tag=node_tag: self.canvas.configure(cursor="hand2"))
            self.canvas.tag_bind(node_tag, "<Leave>", lambda e, tag=node_tag: self.canvas.configure(cursor=""))
            
        # Draw selected state automatically on first load
        self.select_state(self.selected_state_idx, states, state_names)

    def draw_self_loop(self, x, y, label, color, width):
        r = 15
        cx = x
        cy = y - self.node_radius - r + 3
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=-30, extent=240, style="arc", outline=color, width=width
        )
        # Text label above loop
        self.canvas.create_text(
            cx, cy - r - 8, text=label, fill="#bdc3c7", font=("Consolas", 9)
        )

    def draw_transition_line(self, x1, y1, x2, y2, label, color, width):
        angle = math.atan2(y2 - y1, x2 - x1)
        
        # Offsets
        start_x = x1 + self.node_radius * math.cos(angle)
        start_y = y1 + self.node_radius * math.sin(angle)
        
        end_x = x2 - self.node_radius * math.cos(angle)
        end_y = y2 - self.node_radius * math.sin(angle)
        
        self.canvas.create_line(
            start_x, start_y, end_x, end_y,
            fill=color, width=width, arrow="last", arrowshape=(8, 10, 3)
        )
        
        # Label offset
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        offset_y = -8 if angle == 0 or abs(angle) < 0.2 else 8
        
        self.canvas.create_text(
            mid_x, mid_y + offset_y, text=label, fill="#7f8c8d", font=("Consolas", 9, "bold")
        )

    def select_state(self, idx: int, states: list, state_names: list = None):
        """Highlights the selected node on canvas and displays its items inside the inspector."""
        if idx >= len(states):
            idx = 0
        self.selected_state_idx = idx
        
        # Highlight selected node in canvas dynamically by updating outlines
        for item in self.canvas.find_withtag("state_node"):
            self.canvas.itemconfig(item, outline="#2980b9", width=2, fill="#1a1a1c")
            
        selected_tag = self.canvas.find_withtag(f"node_{idx}")
        for st in selected_tag:
            if self.canvas.type(st) == "oval":
                self.canvas.itemconfig(st, outline="#e67e22", width=3.5, fill="#2c3e50")
                
        # Populate Items textbox
        state = states[idx]
        name = state_names[idx] if state_names else f"I{idx}"
        
        text_content = f"=== ITEMS SET FOR STATE {name} ===\n\n"
        
        # Format items beautifully
        sorted_items = sorted(list(state), key=lambda x: (x[0], x[1], x[2]))
        
        # In LALR, items have 4 elements: (lhs, rhs, dot, la)
        # In SLR, items have 3 elements: (lhs, rhs, dot)
        for item in sorted_items:
            lhs = item[0]
            rhs = item[1]
            dot = item[2]
            
            # Format production with dot
            rhs_list = list(rhs)
            # Handle empty epsilons representation
            if not rhs_list:
                rhs_list = ["."]
            else:
                rhs_list.insert(dot, ".")
                
            prod_str = " ".join(rhs_list)
            
            if len(item) == 4: # LALR with Lookahead
                la = item[3]
                text_content += f"  [{lhs} -> {prod_str}  ,  '{la}']\n"
            else: # SLR
                text_content += f"  [{lhs} -> {prod_str}]\n"
                
        # Include GOTO transition targets from this state
        text_content += "\n=== GOTO STATE TRANSITIONS ===\n\n"
        has_trans = False
        
        # Check active parser type transitions
        if self.parser_manager:
            engine = self.parser_manager.slr_engine if self.active_parser_type == "SLR" else self.parser_manager.lalr_engine
            for (src, sym), dest in engine.transitions.items():
                if src == idx:
                    target_name = engine.state_names[dest] if hasattr(engine, "state_names") else f"I{dest}"
                    text_content += f"  On symbol '{sym:8}' ---> Goto {target_name}\n"
                    has_trans = True
                    
        if not has_trans:
            text_content += "  (No outgoing transitions - Trap State)\n"
            
        self.write_text(self.items_textbox, text_content)

    def show_overlay(self):
        """Covers visualizer with descriptive overlay warning if in LL(1) mode."""
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
