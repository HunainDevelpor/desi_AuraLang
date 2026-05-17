import tkinter as tk
import customtkinter as ctk

class TreeVisualizer(ctk.CTkCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#121212", highlightthickness=0)
        
        # Panning
        self.bind("<ButtonPress-1>", self.scroll_start)
        self.bind("<B1-Motion>", self.scroll_move)
        
        # Zooming
        self.bind("<Control-MouseWheel>", self.wheel_zoom)
        self.zoom_level = 1.0
        
        self.node_radius = 35
        self.y_dist = 120
        self.x_padding = 40

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
    def reset_view(self):
        self.zoom_level = 1.0
        self.delete("all")

    def clear(self):
        self.delete("all")
        self.zoom_level = 1.0

    def draw_tree(self, node):
        self.clear()
        if not node: return

        # 1. First pass: calculate dimensions (width needed for each subtree)
        def calc_width(n):
            if not n["children"]:
                n["_width"] = self.node_radius * 2 + self.x_padding
                return n["_width"]
            
            total_w = sum(calc_width(c) for c in n["children"])
            n["_width"] = max(total_w, self.node_radius * 2 + self.x_padding)
            return n["_width"]

        calc_width(node)

        # 2. Second pass: render with exclusive space for each subtree to avoid overlap
        def render(n, x_offset, depth):
            width = n["_width"]
            x = x_offset + width / 2
            y = 100 + depth * self.y_dist
            
            # Draw edges
            curr_x = x_offset
            for child in n["children"]:
                child_x = curr_x + child["_width"] / 2
                child_y = 100 + (depth + 1) * self.y_dist
                self.create_line(x, y, child_x, child_y, fill="#444", width=2, tags="tree_item")
                render(child, curr_x, depth + 1)
                curr_x += child["_width"]
            
            # Draw node
            color = "#e67e22" if any(c.islower() for c in n["name"]) else "#3498db"
            if n["name"] == "\u03b5": color = "#95a5a6"
            
            self.create_oval(x-self.node_radius, y-self.node_radius, 
                             x+self.node_radius, y+self.node_radius, 
                             fill="#2c3e50", outline=color, width=3, tags="tree_item")
            
            self.create_text(x, y, text=n["name"], fill="white", 
                             font=("Arial", 10, "bold"), width=self.node_radius*1.8, 
                             tags="tree_item")

        render(node, 100, 0)
        self.configure(scrollregion=self.bbox("all"))
