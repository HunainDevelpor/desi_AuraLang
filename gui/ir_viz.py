import tkinter as tk
import customtkinter as ctk

class IrFlowVisualizer(ctk.CTkCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#101010", highlightthickness=0)
        
        # Panning bindings
        self.bind("<ButtonPress-1>", self.scroll_start)
        self.bind("<B1-Motion>", self.scroll_move)
        
        # Zooming bindings
        self.bind("<Control-MouseWheel>", self.wheel_zoom)
        self.zoom_level = 1.0
        
        # Dimensions configurations
        self.block_width = 240
        self.y_spacing = 90
        
    def scroll_start(self, event):
        self.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.scan_dragto(event.x, event.y, gain=1)

    def wheel_zoom(self, event):
        scale = 1.1 if event.delta > 0 else 0.9
        self.apply_zoom(scale, event.x, event.y)

    def apply_zoom(self, scale, x=None, y=None):
        if x is None: x = self.winfo_width() / 2
        if y is None: y = self.winfo_height() / 2
        
        self.zoom_level *= scale
        self.scale("all", x, y, scale, scale)
        self.configure(scrollregion=self.bbox("all"))

    def zoom_in(self): self.apply_zoom(1.2)
    def zoom_out(self): self.apply_zoom(0.8)
    def clear(self):
        self.delete("all")
        self.zoom_level = 1.0

    def draw_flow_graph(self, blocks):
        self.clear()
        if not blocks:
            # Draw placeholder message
            self.create_text(300, 200, text="No CFG data generated. Run compiler first.", fill="#7f8c8d", font=("Arial", 14), tags="bg_msg")
            return
            
        # 1. Calculate positions and heights of blocks
        # We will arrange blocks vertically
        positions = {}
        curr_y = 60
        x_center = 350
        
        block_heights = {}
        for block_id, block in sorted(blocks.items()):
            # Dynamic height based on instruction lines count
            h = 45 + max(1, len(block.instructions)) * 22
            block_heights[block_id] = h
            
            positions[block_id] = (x_center - self.block_width / 2, curr_y, h)
            curr_y += h + self.y_spacing

        # 2. Draw Basic Blocks boxes
        for block_id, block in sorted(blocks.items()):
            x, y, h = positions[block_id]
            x_end = x + self.block_width
            y_end = y + h
            
            # Outer block border & fill
            border_color = "#3498db" if block_id == 1 else "#555555"
            self.create_rectangle(
                x, y, x_end, y_end,
                fill="#161616", outline=border_color, width=2.5, tags="cfg_item"
            )
            
            # Title header
            self.create_text(
                x + 15, y + 20,
                text=f"Basic Block {block_id}", fill="#f1c40f",
                font=("Arial", 11, "bold"), anchor="w", tags="cfg_item"
            )
            
            # Instructions content
            y_text = y + 42
            if not block.instructions:
                self.create_text(
                    x + 15, y_text, text="[Empty Block]", fill="#7f8c8d",
                    font=("Consolas", 10), anchor="w", tags="cfg_item"
                )
            else:
                for instr in block.instructions:
                    # Clean visualization strings
                    self.create_text(
                        x + 15, y_text, text=instr, fill="#ecf0f1",
                        font=("Consolas", 10), anchor="w", tags="cfg_item"
                    )
                    y_text += 22

        # 3. Draw Flow edges
        for block_id, block in sorted(blocks.items()):
            x_src, y_src, h_src = positions[block_id]
            src_bottom_x = x_src + self.block_width / 2
            src_bottom_y = y_src + h_src
            
            num_succs = len(block.successors)
            for idx, succ_id in enumerate(block.successors):
                if succ_id not in positions:
                    continue
                x_dest, y_dest, h_dest = positions[succ_id]
                dest_top_x = x_dest + self.block_width / 2
                dest_top_y = y_dest
                
                # Colors based on branch types (conditional vs sequential fallthrough)
                color = "#7f8c8d"
                label = ""
                
                if num_succs > 1:
                    # Conditional branches from "if_false" or loops
                    if idx == 0:
                        # The jump branch (conditional branch: target of IF_FALSE is False)
                        color = "#e74c3c"
                        label = "False"
                    else:
                        # Fallthrough branch
                        color = "#2ecc71"
                        label = "True"
                else:
                    # Unconditional jump or default linear step
                    last_instr = block.instructions[-1] if block.instructions else ""
                    if "goto" in last_instr:
                        color = "#3498db"
                        label = "Goto"
                    else:
                        color = "#7f8c8d"
                        label = "Fallthrough"
                        
                # Draw lines. Offset points slightly if they connect non-sequentially or to avoid overlays
                if succ_id == block_id + 1:
                    # Sequential block directly below
                    self.draw_arrow(src_bottom_x, src_bottom_y, dest_top_x, dest_top_y, label, color)
                else:
                    # Curved jump arrow on the side
                    side_offset = -140 if succ_id < block_id else 140
                    mid_y = (src_bottom_y + dest_top_y) / 2
                    
                    self.draw_curved_arrow(
                        src_bottom_x, src_bottom_y, 
                        dest_top_x, dest_top_y, 
                        side_offset, label, color
                    )

        self.configure(scrollregion=self.bbox("all"))

    def draw_arrow(self, x1, y1, x2, y2, label, color):
        # Draw vertical straight connecting arrow
        self.create_line(
            x1, y1, x2, y2,
            fill=color, width=2.5, arrow="last", arrowshape=(8, 10, 3), tags="cfg_item"
        )
        
        # Label text background
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        self.create_text(
            mid_x + 35, mid_y, text=label, fill=color,
            font=("Arial", 9, "bold"), tags="cfg_item"
        )

    def draw_curved_arrow(self, x1, y1, x2, y2, side_offset, label, color):
        # Create a curved jump arrow routing around other blocks
        ctrl_x = x1 + side_offset
        ctrl_y = (y1 + y2) / 2
        
        # Draw 3-segment line or smooth spline
        points = [
            x1, y1,
            ctrl_x, y1 + 10,
            ctrl_x, y2 - 10,
            x2, y2
        ]
        
        self.create_line(
            *points, smooth=True,
            fill=color, width=2.2, arrow="last", arrowshape=(8, 10, 3), tags="cfg_item"
        )
        
        # Label text on the curve
        self.create_text(
            ctrl_x + (15 if side_offset > 0 else -15), ctrl_y,
            text=label, fill=color, font=("Arial", 9, "bold"), tags="cfg_item"
        )
