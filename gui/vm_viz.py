import tkinter as tk
import customtkinter as ctk
import time

class VmDashboard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        
        # Keep track of previous stack state for push/pop animations
        self.last_stack = []
        self.animating_cards = {}
        
        # Build premium UI layout
        self.create_widgets()
        
    def create_widgets(self):
        # 1. TOP SECTION: CPU Registers watches
        self.regs_frame = ctk.CTkFrame(self, fg_color="#101010", corner_radius=15, height=90, border_width=1, border_color="#222")
        self.regs_frame.pack(fill="x", padx=10, pady=5)
        self.regs_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="equal")
        
        self.reg_cards = {}
        registers_metadata = [
            ("IP", "Instruction Pointer", "#f1c40f"),
            ("SP", "Stack Pointer", "#3498db"),
            ("HP", "Heap Pointer", "#e74c3c"),
            ("ACC", "Accumulator", "#2ecc71")
        ]
        
        for idx, (name, desc, color) in enumerate(registers_metadata):
            card = ctk.CTkFrame(self.regs_frame, fg_color="#181818", corner_radius=10, border_color="#333333", border_width=1)
            card.grid(row=0, column=idx, padx=10, pady=10, sticky="nsew")
            
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=13, weight="bold"), text_color=color).pack(pady=(6, 0))
            val_lbl = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ffffff")
            val_lbl.pack(pady=(0, 2))
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=8), text_color="#7f8c8d").pack(pady=(0, 6))
            
            self.reg_cards[name] = val_lbl

        # 2. MAIN BODY SECTION: Split (Stack | Heap | Variables)
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.body_frame.grid_columnconfigure(0, weight=3) # Evaluation Stack
        self.body_frame.grid_columnconfigure(1, weight=4) # Heap Grid
        self.body_frame.grid_columnconfigure(2, weight=4) # Scoped variables
        self.body_frame.grid_rowconfigure(0, weight=1)

        # Left Column: Evaluation Stack visualizer
        self.stack_panel = ctk.CTkFrame(self.body_frame, fg_color="#101010", corner_radius=15, border_width=1, border_color="#222")
        self.stack_panel.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(self.stack_panel, text="🥞 EVALUATION STACK", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3498db").pack(pady=10)
        
        self.stack_canvas_container = ctk.CTkFrame(self.stack_panel, fg_color="#090909", corner_radius=10)
        self.stack_canvas_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.stack_canvas = tk.Canvas(self.stack_canvas_container, bg="#090909", highlightthickness=0)
        self.stack_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.stack_canvas.bind("<Configure>", lambda e: self.draw_evaluation_stack(self.last_stack))

        # Middle Column: Heap Memory grid inspector (64 allocated grid blocks)
        self.heap_panel = ctk.CTkFrame(self.body_frame, fg_color="#101010", corner_radius=15, border_width=1, border_color="#222")
        self.heap_panel.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(self.heap_panel, text="💾 HEAP MEMORY GRID", font=ctk.CTkFont(size=12, weight="bold"), text_color="#e74c3c").pack(pady=10)
        
        # Grid Canvas
        self.heap_canvas_container = ctk.CTkFrame(self.heap_panel, fg_color="#090909", corner_radius=10)
        self.heap_canvas_container.pack(fill="both", expand=True, padx=12, pady=(0, 5))
        
        self.heap_canvas = tk.Canvas(self.heap_canvas_container, bg="#090909", highlightthickness=0)
        self.heap_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.heap_canvas.bind("<Configure>", lambda e: self.redraw_heap_grid())
        self.heap_canvas.bind("<Button-1>", self.on_heap_click)
        
        # Details bar at bottom
        self.heap_details = ctk.CTkLabel(self.heap_panel, text="Click an allocated block to inspect array details.", 
                                         font=ctk.CTkFont(size=10, slant="italic"), text_color="#7f8c8d")
        self.heap_details.pack(fill="x", side="bottom", pady=8)

        # Right Column: Variables & Call frames
        self.vars_panel = ctk.CTkFrame(self.body_frame, fg_color="#101010", corner_radius=15, border_width=1, border_color="#222")
        self.vars_panel.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(self.vars_panel, text="🔑 VARIABLE SCOPES & LIFETIMES", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2ecc71").pack(pady=10)
        
        self.vars_scroll = ctk.CTkScrollableFrame(self.vars_panel, fg_color="#090909", corner_radius=10)
        self.vars_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Memory grid state
        self.heap_cells = {}
        self.allocated_addresses = {}

    # ====================================================
    # REDRAW & SIMULATION INTERFACES
    # ====================================================
    def update_dashboard(self, vm):
        # 1. CPU registers update
        for name, label_widget in self.reg_cards.items():
            val = vm.registers.get(name, "0")
            label_widget.configure(text=str(val if val is not None else "Null"))

        # 2. Update Heap addresses
        self.allocated_addresses.clear()
        for addr, elements in vm.heap.items():
            # e.g., "0x1000" or raw int address
            try:
                base_addr = int(addr, 16) if isinstance(addr, str) and addr.startswith("0x") else int(addr)
            except ValueError:
                base_addr = 16 # fallback
                
            for idx, val in enumerate(elements):
                target_cell = (base_addr + idx) % 64
                self.allocated_addresses[target_cell] = {
                    "addr_label": f"0x{base_addr + idx:02X}",
                    "val": val,
                    "index": idx,
                    "base": f"0x{base_addr:02X}"
                }
        self.redraw_heap_grid()

        # 3. Update evaluation stack (with sliding animations)
        self.draw_evaluation_stack_animated(vm.evaluation_stack)

        # 4. Scoped variables update
        self.draw_vars_cards(vm)

    # ---------- STACK SLIDE PUSH/POP ANIMATIONS ----------
    def draw_evaluation_stack_animated(self, stack):
        # Identify push / pop action
        prev_len = len(self.last_stack)
        curr_len = len(stack)
        
        self.last_stack = list(stack)
        
        if curr_len > prev_len:
            # PUSH: Slide new element down from top (Y=15) to its correct stack Y index
            new_item = stack[-1]
            target_idx = curr_len - 1
            self.draw_evaluation_stack(stack[:-1]) # Draw prior static items
            
            # Animate the last item
            self.animate_push(target_idx, new_item, curr_len)
        elif curr_len < prev_len and prev_len > 0:
            # POP: Slide top element upwards and fade
            popped_item = self.last_stack[prev_len - 1] if prev_len - 1 < len(self.last_stack) else "?"
            self.draw_evaluation_stack(stack)
            self.animate_pop(prev_len - 1, popped_item, curr_len)
        else:
            self.draw_evaluation_stack(stack)

    def draw_evaluation_stack(self, stack):
        self.stack_canvas.delete("all")
        
        w = max(100, self.stack_canvas.winfo_width())
        h = max(200, self.stack_canvas.winfo_height())
        
        if not stack:
            self.stack_canvas.create_text(
                w / 2, h / 2,
                text="[Stack Empty]", fill="#555555",
                font=("Consolas", 11, "italic")
            )
            return

        card_h = 30
        spacing = 8
        margin = 12
        
        curr_y = h - margin - card_h
        
        for idx, item in enumerate(stack):
            if curr_y < 10:
                self.stack_canvas.create_text(
                    w / 2, 12,
                    text=f"+ {len(stack) - idx} elements", fill="#f1c40f",
                    font=("Consolas", 8, "bold")
                )
                break
                
            is_top = (idx == len(stack) - 1)
            fill_c = "#293d52" if is_top else "#141414"
            border_c = "#3498db" if is_top else "#333333"
            text_c = "#ffffff" if is_top else "#95a5a6"
            
            # Card rectangle
            self.stack_canvas.create_rectangle(
                margin, curr_y, w - margin, curr_y + card_h,
                fill=fill_c, outline=border_c, width=1.5 if is_top else 1,
                tags="stack_card"
            )
            # Index indicator
            self.stack_canvas.create_text(
                margin + 12, curr_y + card_h / 2,
                text=f"[{idx}]", fill="#7f8c8d",
                font=("Consolas", 8, "bold")
            )
            # Value
            self.stack_canvas.create_text(
                w / 2, curr_y + card_h / 2,
                text=str(item), fill=text_c,
                font=("Consolas", 9, "bold")
            )
            curr_y -= (card_h + spacing)

    def animate_push(self, target_idx, val, total_len):
        w = max(100, self.stack_canvas.winfo_width())
        h = max(200, self.stack_canvas.winfo_height())
        
        card_h = 30
        spacing = 8
        margin = 12
        
        # Calculate destination coordinate
        dest_y = h - margin - card_h - (target_idx * (card_h + spacing))
        
        if dest_y < 10:
            self.draw_evaluation_stack(self.last_stack)
            return
            
        start_y = 10
        steps = 8
        
        # Create animated box
        rect_id = self.stack_canvas.create_rectangle(
            margin, start_y, w - margin, start_y + card_h,
            fill="#2ecc71", outline="#2ecc71", width=1.5
        )
        text_id = self.stack_canvas.create_text(
            w / 2, start_y + card_h / 2,
            text=f"PUSH: {val}", fill="white", font=("Consolas", 9, "bold")
        )
        
        def run_step(step):
            if step >= steps:
                self.stack_canvas.delete(rect_id)
                self.stack_canvas.delete(text_id)
                self.draw_evaluation_stack(self.last_stack)
            else:
                y = start_y + (dest_y - start_y) * (step / steps)
                self.stack_canvas.coords(rect_id, margin, y, w - margin, y + card_h)
                self.stack_canvas.coords(text_id, w / 2, y + card_h / 2)
                self.stack_canvas.after(20, lambda: run_step(step + 1))
                
        run_step(0)

    def animate_pop(self, target_idx, val, total_len):
        w = max(100, self.stack_canvas.winfo_width())
        h = max(200, self.stack_canvas.winfo_height())
        
        card_h = 30
        spacing = 8
        margin = 12
        
        start_y = h - margin - card_h - (target_idx * (card_h + spacing))
        dest_y = 10
        steps = 8
        
        rect_id = self.stack_canvas.create_rectangle(
            margin, start_y, w - margin, start_y + card_h,
            fill="#e74c3c", outline="#e74c3c", width=1.5
        )
        text_id = self.stack_canvas.create_text(
            w / 2, start_y + card_h / 2,
            text=f"POP: {val}", fill="white", font=("Consolas", 9, "bold")
        )
        
        def run_step(step):
            if step >= steps:
                self.stack_canvas.delete(rect_id)
                self.stack_canvas.delete(text_id)
            else:
                y = start_y + (dest_y - start_y) * (step / steps)
                self.stack_canvas.coords(rect_id, margin, y, w - margin, y + card_h)
                self.stack_canvas.coords(text_id, w / 2, y + card_h / 2)
                self.stack_canvas.after(20, lambda: run_step(step + 1))
                
        run_step(0)

    # ---------- 64-CELL HEAP MEMORY GRID ----------
    def redraw_heap_grid(self):
        self.heap_canvas.delete("all")
        self.heap_cells.clear()
        
        w = max(180, self.heap_canvas.winfo_width())
        h = max(180, self.heap_canvas.winfo_height())
        
        rows, cols = 8, 8 # 8x8 = 64 cells representing heap address offsets 0x00 to 0x3F
        padding = 3
        
        cell_w = (w - (cols + 1) * padding) / cols
        cell_h = (h - (rows + 1) * padding) / rows
        
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                x1 = padding + c * (cell_w + padding)
                y1 = padding + r * (cell_h + padding)
                x2 = x1 + cell_w
                y2 = y1 + cell_h
                
                # Check if cell address is allocated on CPU heap
                is_allocated = idx in self.allocated_addresses
                
                if is_allocated:
                    fill_c = "#e67e22" # Orange allocated array element
                    outline_c = "#e74c3c"
                else:
                    fill_c = "#141414" # Unallocated space
                    outline_c = "#222"
                    
                rect_id = self.heap_canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill_c, outline=outline_c, width=1
                )
                
                # Tiny text indicator
                text_id = self.heap_canvas.create_text(
                    (x1+x2)/2, (y1+y2)/2, text=f"{idx:02X}", 
                    fill="#333" if not is_allocated else "#fff", 
                    font=("Consolas", 7)
                )
                
                self.heap_cells[idx] = {
                    "rect": rect_id, "text": text_id,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2
                }

    def on_heap_click(self, event):
        mx, my = event.x, event.y
        clicked_idx = None
        
        for idx, info in self.heap_cells.items():
            if info["x1"] <= mx <= info["x2"] and info["y1"] <= my <= info["y2"]:
                clicked_idx = idx
                break
                
        if clicked_idx is None:
            return
            
        if clicked_idx in self.allocated_addresses:
            data = self.allocated_addresses[clicked_idx]
            self.heap_details.configure(
                text=f"Address: {data['addr_label']} (Base: {data['base']}) | Element Index: {data['index']} | Value stored: {data['val']}",
                text_color="#e67e22"
            )
            # Highlight border temporally
            rect_id = self.heap_cells[clicked_idx]["rect"]
            self.heap_canvas.itemconfig(rect_id, outline="#f1c40f", width=2)
            self.after(500, lambda: self.heap_canvas.itemconfig(rect_id, outline="#e74c3c", width=1))
        else:
            self.heap_details.configure(
                text=f"Address: 0x{clicked_idx:02X} | Cell State: Free / Unallocated Memory block.",
                text_color="#7f8c8d"
            )

    # ---------- SCOPED VARIABLES CARDS ----------
    def draw_vars_cards(self, vm):
        # Clear scrollable frame widgets
        for widget in self.vars_scroll.winfo_children():
            widget.destroy()
            
        # Draw Scope Levels
        has_vars = False
        
        # 1. Global Variables Card Group
        global_vars = sorted(vm.globals.items())
        if global_vars:
            has_vars = True
            card = ctk.CTkFrame(self.vars_scroll, fg_color="#141414", corner_radius=10, border_width=1, border_color="#222")
            card.pack(fill="x", padx=5, pady=4)
            
            ctk.CTkLabel(card, text="🌐 GLOBAL SCOPE VARIABLES", font=ctk.CTkFont(size=10, weight="bold"), text_color="#3498db").pack(anchor="w", padx=12, pady=(8,2))
            
            for var_name, val in global_vars:
                item_frame = ctk.CTkFrame(card, fg_color="transparent")
                item_frame.pack(fill="x", padx=15, pady=3)
                
                # Var name
                ctk.CTkLabel(item_frame, text=var_name, font=ctk.CTkFont(size=12, family="Consolas", weight="bold"), text_color="#ecf0f1").pack(side="left")
                # Var type based on class type
                dtype = "num"
                if isinstance(val, bool): dtype = "bool"
                elif isinstance(val, float): dtype = "float"
                elif isinstance(val, str): dtype = "string"
                elif isinstance(val, list): dtype = "array"
                
                ctk.CTkLabel(item_frame, text=f"[{dtype}]", font=ctk.CTkFont(size=9, slant="italic"), text_color="#7f8c8d").pack(side="left", padx=5)
                
                # Var value badge
                badge = ctk.CTkFrame(item_frame, fg_color="#2c3e50", corner_radius=6)
                badge.pack(side="right")
                ctk.CTkLabel(badge, text=str(val), font=ctk.CTkFont(size=11, family="Consolas", weight="bold"), text_color="#ffffff", padx=6, pady=2).pack()

        # 2. Local Stack frames Card Group
        if vm.call_stack:
            active_frame = vm.call_stack[-1]
            local_vars = sorted(active_frame.locals.items())
            
            if local_vars:
                has_vars = True
                card = ctk.CTkFrame(self.vars_scroll, fg_color="#181818", corner_radius=10, border_width=1, border_color="#293d52")
                card.pack(fill="x", padx=5, pady=6)
                
                ctk.CTkLabel(card, text=f"📞 FRAME: {active_frame.name.upper()}()", 
                             font=ctk.CTkFont(size=10, weight="bold"), text_color="#e67e22").pack(anchor="w", padx=12, pady=(8,2))
                
                for var_name, val in local_vars:
                    item_frame = ctk.CTkFrame(card, fg_color="transparent")
                    item_frame.pack(fill="x", padx=15, pady=3)
                    
                    ctk.CTkLabel(item_frame, text=var_name, font=ctk.CTkFont(size=12, family="Consolas", weight="bold"), text_color="#ecf0f1").pack(side="left")
                    
                    dtype = "num"
                    if isinstance(val, bool): dtype = "bool"
                    elif isinstance(val, float): dtype = "float"
                    elif isinstance(val, str): dtype = "string"
                    elif isinstance(val, list): dtype = "array"
                    
                    ctk.CTkLabel(item_frame, text=f"[{dtype}]", font=ctk.CTkFont(size=9, slant="italic"), text_color="#7f8c8d").pack(side="left", padx=5)
                    
                    badge = ctk.CTkFrame(item_frame, fg_color="#d35400", corner_radius=6)
                    badge.pack(side="right")
                    ctk.CTkLabel(badge, text=str(val), font=ctk.CTkFont(size=11, family="Consolas", weight="bold"), text_color="#ffffff", padx=6, pady=2).pack()
                    
        if not has_vars:
            ctk.CTkLabel(self.vars_scroll, text="No active variables found in context scope.", 
                         font=ctk.CTkFont(size=11, slant="italic"), text_color="#555555").pack(pady=40)
