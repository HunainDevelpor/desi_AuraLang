import tkinter as tk
import customtkinter as ctk
import re

class CustomCodeEditor(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#0a0a0a")

        # Color definitions matching our elegant dark theme
        self.bg_color = "#0a0a0a"
        self.text_bg = "#121212"
        self.line_num_bg = "#080808"
        self.line_num_fg = "#555555"
        self.line_num_active = "#3498db"
        self.current_line_bg = "#1e1e1e"
        
        # Keywords table
        self.keywords = [
            "rakho", "bol", "agar", "warna", "jabtak", "ghumo", "tarkeeb", 
            "wapas", "sahi", "galat", "and", "or", "not", "from", "to",
            "num", "float", "bool", "string"
        ]

        # Layout Split: Sidebar Line Numbers + Main Editor
        self.grid_columnconfigure(0, weight=0) # line numbers
        self.grid_columnconfigure(1, weight=1) # editor
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar Line Numbers Text widget (Synchronized scrolling)
        self.line_nums = tk.Text(
            self, width=4, padx=5, pady=10, takefocus=0, border=0,
            background=self.line_num_bg, foreground=self.line_num_fg,
            state="disabled", font=("Consolas", 13), wrap="none"
        )
        self.line_nums.grid(row=0, column=0, sticky="ns")

        # 2. Main Editor Text Box
        self.editor = tk.Text(
            self, wrap="none", background=self.text_bg, foreground="#ecf0f1",
            insertbackground="#3498db", relief="flat", border=0, padx=10, pady=10,
            font=("Consolas", 13), undo=True, maxundo=50
        )
        self.editor.grid(row=0, column=1, sticky="nsew")

        # Scrollbar integration
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.on_scrollbar)
        self.scrollbar.grid(row=0, column=2, sticky="ns")
        self.editor.configure(yscrollcommand=self.scrollbar.set)

        # Autocomplete dropdown (initially hidden)
        self.ac_listbox = None
        self.ac_active = False

        # Find & Replace Panel (initially hidden)
        self.fr_panel = None

        # Bind events
        self.editor.bind("<KeyRelease>", self.on_key_release)
        self.editor.bind("<Button-1>", self.on_click)
        self.editor.bind("<Configure>", lambda e: self.update_line_numbers())
        self.editor.bind("<Tab>", self.on_tab)
        self.editor.bind("<Return>", self.on_return)
        self.editor.bind("<Control-slash>", self.toggle_comments)
        self.editor.bind("<Control-f>", self.show_find_replace)
        self.editor.bind("<Control-F>", self.show_find_replace)

        # Synchronize horizontal scroll of line numbers
        self.editor.bind("<MouseWheel>", self.on_mousewheel)

        # Setup Tag configs for syntax coloring
        self.setup_tags()

        # Current line highlight state
        self.active_line_tag = "active_line"
        
        # Load starting text
        self.insert_default_code()
        
        # Run initial formatting & coloring
        self.editor.after(100, self.full_coloring)
        self.editor.after(150, self.update_line_numbers)

    # ---------- DEFAULT CODE ----------
    def insert_default_code(self):
        code = (
            "# Desi AuraLang Optimization & Calculation Demo\n"
            "rakho x = 10;\n"
            "rakho y = 20;\n"
            "rakho a = x + y;            # Constant folding -> 30\n"
            "rakho b = x + y;            # CSE -> 30\n"
            "rakho unused = 50 * x;      # Unused -> gets eliminated!\n"
            "rakho final1 = a + 0;       # Algebraic simplification -> 30\n"
            "rakho final2 = b * 1;       # Algebraic simplification -> 30\n"
            "rakho final3 = a * 0;       # Multiplication by zero -> 0\n"
            "\n"
            "bol final1;                 # Prints 30\n"
            "bol final2;                 # Prints 30\n"
            "bol final3;                 # Prints 0\n"
            "\n"
            "# Dynamic Loop Calculation\n"
            "rakho limit = 4;\n"
            "rakho sum = 0;\n"
            "ghumo i from 1 to limit {\n"
            "    sum = sum + i;\n"
            "}\n"
            "bol sum;                    # Prints 10"
        )
        self.editor.insert("1.0", code)

    # ---------- SYNTAX HIGHLIGHTING ENGINE ----------
    def setup_tags(self):
        # Configure coloring styles
        self.editor.tag_config("keyword", foreground="#3498db") # Bright cyan-blue
        self.editor.tag_config("number", foreground="#e67e22")  # Orange
        self.editor.tag_config("string", foreground="#2ecc71")  # Green
        self.editor.tag_config("comment", foreground="#7f8c8d", font=("Consolas", 13, "italic")) # Slate gray
        self.editor.tag_config("operator", foreground="#e74c3c") # Red
        self.editor.tag_config("bracket_match", background="#2980b9", foreground="white") # Soft blue highlight
        self.editor.tag_config("active_line", background=self.current_line_bg)
        self.editor.tag_config("error_underline", underline=True, underlinefg="red")

    def full_coloring(self, event=None):
        # Clear tags
        for t in ["keyword", "number", "string", "comment", "operator", "error_underline"]:
            self.editor.tag_remove(t, "1.0", tk.END)

        code = self.editor.get("1.0", tk.END)

        # 1. Colors comments (# ...)
        for match in re.finditer(r"#[^\n]*", code):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("comment", start, end)

        # 2. Colors string literals ("...")
        for match in re.finditer(r'"[^"\n]*"', code):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("string", start, end)

        # 3. Colors keywords
        for kw in self.keywords:
            for match in re.finditer(rf"\b{kw}\b", code):
                start = f"1.0 + {match.start()} chars"
                end = f"1.0 + {match.end()} chars"
                self.editor.tag_add("keyword", start, end)

        # 4. Colors numbers (integers & floats)
        for match in re.finditer(r"\b\d+(\.\d+)?\b", code):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("number", start, end)

        # 5. Colors operators
        for match in re.finditer(r"[\+\-\*\/\%\=\!\>\<\,\|\&]", code):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("operator", start, end)

    # ---------- SYNCHRONIZED LINE NUMBERS ----------
    def on_scrollbar(self, *args):
        self.editor.yview(*args)
        self.line_nums.yview(*args)

    def on_mousewheel(self, event):
        self.line_nums.yview_scroll(int(-1*(event.delta/120)), "units")
        self.update_line_numbers()

    def update_line_numbers(self):
        self.line_nums.configure(state="normal")
        self.line_nums.delete("1.0", tk.END)

        # Get number of lines in editor
        line_count = int(self.editor.index("end-1c").split(".")[0])
        line_num_str = "\n".join(str(i) for i in range(1, line_count + 1))
        
        self.line_nums.insert("1.0", line_num_str)
        self.line_nums.configure(state="disabled")

        # Keep line numbers in perfect scroll alignment
        self.line_nums.yview_moveto(self.editor.yview()[0])

    # ---------- KEY EVENTS & RECOVERY ACTIONS ----------
    def on_key_release(self, event):
        # Trigger syntax highlighting
        self.full_coloring()
        
        # Trigger line numbers update
        self.update_line_numbers()
        
        # Highlight active line
        self.highlight_current_line()
        
        # Match brackets
        self.highlight_matching_brackets()

        # Handle autocomplete trigger
        self.trigger_autocomplete(event)

    def on_click(self, event):
        self.editor.after(10, self.highlight_current_line)
        self.editor.after(15, self.highlight_matching_brackets)
        if self.ac_listbox:
            self.hide_autocomplete()

    # ---------- CURRENT LINE HIGHLIGHT ----------
    def highlight_current_line(self):
        self.editor.tag_remove("active_line", "1.0", tk.END)
        # Get active line index
        line_idx = self.editor.index("insert").split(".")[0]
        start = f"{line_idx}.0"
        end = f"{line_idx}.end+1c"
        self.editor.tag_add("active_line", start, end)

    # ---------- BRACKET MATCHING ----------
    def highlight_matching_brackets(self):
        self.editor.tag_remove("bracket_match", "1.0", tk.END)
        
        insert_pos = self.editor.index("insert")
        curr_char = self.editor.get(insert_pos)
        prev_char = self.editor.get(f"{insert_pos}-1c")
        
        pairs = {
            "(": ")", ")": "(",
            "{": "}", "}": "{",
            "[": "]", "]": "["
        }

        # Check if cursor is right next to a bracket
        target_pos = None
        bracket = None
        
        if curr_char in pairs:
            target_pos = insert_pos
            bracket = curr_char
        elif prev_char in pairs:
            target_pos = f"{insert_pos}-1c"
            bracket = prev_char
            
        if not target_pos:
            return

        # Scan to find match
        closing = pairs[bracket]
        direction = 1 if bracket in ("(", "{", "[") else -1
        
        depth = 0
        search_idx = target_pos
        
        limit = 500 # Max search characters to avoid freeze
        count = 0
        
        while count < limit:
            search_idx = f"{search_idx}+{direction}c" if direction > 0 else f"{search_idx}-{abs(direction)}c"
            char = self.editor.get(search_idx)
            
            if char == "":
                break
                
            if char == bracket:
                depth += 1
            elif char == closing:
                if depth == 0:
                    # Found match! Highlight both brackets
                    self.editor.tag_add("bracket_match", target_pos, f"{target_pos}+1c")
                    self.editor.tag_add("bracket_match", search_idx, f"{search_idx}+1c")
                    break
                else:
                    depth -= 1
            count += 1

    # ---------- SMART TABS ----------
    def on_tab(self, event):
        # Insert 4 spaces instead of a raw tab character
        self.editor.insert("insert", "    ")
        self.full_coloring()
        return "break" # Intercept standard Tab action

    # ---------- AUTO INDENTATION ----------
    def on_return(self, event):
        # Find active line's indentation level
        curr_line = self.editor.index("insert").split(".")[0]
        line_content = self.editor.get(f"{curr_line}.0", f"{curr_line}.end")
        
        # Check leading spacing
        indent = re.match(r"^\s*", line_content).group(0)
        
        # If the line ends with an opening brace, add 4 extra spaces on next line
        extra_indent = ""
        if line_content.rstrip().endswith("{"):
            extra_indent = "    "
            
        # Insert newline and auto spacing
        self.editor.insert("insert", f"\n{indent}{extra_indent}")
        self.editor.see("insert")
        
        self.editor.after(10, self.update_line_numbers)
        self.editor.after(20, self.full_coloring)
        
        return "break" # Intercept standard return action

    # ---------- COMMENT TOGGLE (CTRL + /) ----------
    def toggle_comments(self, event):
        try:
            sel_start = self.editor.index("sel.first")
            sel_end = self.editor.index("sel.last")
        except tk.TclError:
            # No selection, use cursor line
            cursor_pos = self.editor.index("insert")
            line = cursor_pos.split(".")[0]
            sel_start = f"{line}.0"
            sel_end = f"{line}.end"

        start_line = int(sel_start.split(".")[0])
        end_line = int(sel_end.split(".")[0])

        for line_num in range(start_line, end_line + 1):
            line_start = f"{line_num}.0"
            char_check = self.editor.get(line_start, f"{line_start}+2c")
            
            if char_check.startswith("# "):
                self.editor.delete(line_start, f"{line_start}+2c")
            elif char_check.startswith("#"):
                self.editor.delete(line_start, f"{line_start}+1c")
            else:
                self.editor.insert(line_start, "# ")
                
        self.full_coloring()
        return "break"

    # ---------- KEYWORD AUTO-COMPLETE DROPDOWN ----------
    def trigger_autocomplete(self, event):
        # Hide autocomplete on navigation keys
        if event.keysym in ("Up", "Down", "Left", "Right", "Return", "Escape", "space"):
            self.hide_autocomplete()
            return

        # Get word currently being typed before the cursor
        cursor_pos = self.editor.index("insert")
        line_start = f"{cursor_pos.split('.')[0]}.0"
        line_text = self.editor.get(line_start, cursor_pos)
        
        word_match = re.search(r"\b([a-zA-Z_]+)$", line_text)
        if not word_match:
            self.hide_autocomplete()
            return
            
        typed_fragment = word_match.group(1).lower()
        
        # Match matches
        matches = [kw for kw in self.keywords if kw.startswith(typed_fragment) and kw != typed_fragment]
        if not matches:
            self.hide_autocomplete()
            return
            
        # Draw dynamic pop-up dropdown listbox right under the text cursor location
        self.show_autocomplete_dropdown(cursor_pos, typed_fragment, matches)

    def show_autocomplete_dropdown(self, cursor_pos, typed_fragment, matches):
        if not self.ac_listbox:
            # Create a small floating Listbox
            self.ac_listbox = tk.Listbox(
                self, background="#1b1b1b", foreground="white",
                selectbackground="#3498db", selectforeground="white",
                font=("Consolas", 10), border=1, relief="solid", highlightthickness=0
            )
            # Bind selection
            self.ac_listbox.bind("<Double-Button-1>", lambda e: self.insert_completion(typed_fragment))
            self.editor.bind("<KeyPress-Down>", self.focus_ac_dropdown)
            self.ac_listbox.bind("<Return>", lambda e: self.insert_completion(typed_fragment))
            self.ac_listbox.bind("<FocusOut>", lambda e: self.hide_autocomplete())
            
        self.ac_listbox.delete(0, tk.END)
        for m in matches:
            self.ac_listbox.insert(tk.END, m)
            
        # Position dropdown directly under the active text cursor line
        x, y, w, h = self.editor.bbox("insert")
        
        # Offset to place listbox properly
        self.ac_listbox.place(x=x + 40, y=y + h + 20, width=120, height=min(80, len(matches)*18))
        self.ac_active = True

    def focus_ac_dropdown(self, event):
        if self.ac_active and self.ac_listbox:
            self.ac_listbox.focus_set()
            self.ac_listbox.selection_set(0)
            return "break"

    def insert_completion(self, fragment):
        if not self.ac_listbox:
            return
        selected = self.ac_listbox.get(self.ac_listbox.curselection()[0])
        
        # Complete typing
        cursor_pos = self.editor.index("insert")
        frag_len = len(fragment)
        self.editor.delete(f"{cursor_pos}-{frag_len}c", cursor_pos)
        self.editor.insert("insert", selected)
        
        self.hide_autocomplete()
        self.editor.focus_set()
        self.full_coloring()

    def hide_autocomplete(self):
        if self.ac_listbox:
            self.ac_listbox.place_forget()
            self.ac_listbox = None
        self.ac_active = False

    # ---------- RETRACTABLE FIND & REPLACE PANEL ----------
    def show_find_replace(self, event=None):
        if self.fr_panel:
            self.hide_find_replace()
            return "break"

        # Create sleek panel at the top
        self.fr_panel = ctk.CTkFrame(self, fg_color="#181818", corner_radius=10, height=45)
        self.fr_panel.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(self.fr_panel, text="Find:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(15, 5))
        self.find_entry = ctk.CTkEntry(self.fr_panel, width=130, height=24)
        self.find_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.fr_panel, text="Replace:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(15, 5))
        self.replace_entry = ctk.CTkEntry(self.fr_panel, width=130, height=24)
        self.replace_entry.pack(side="left", padx=5)

        self.btn_find = ctk.CTkButton(self.fr_panel, text="Find Next", width=70, height=24, command=self.find_text)
        self.btn_find.pack(side="left", padx=5)

        self.btn_replace = ctk.CTkButton(self.fr_panel, text="Replace", width=60, height=24, fg_color="#e67e22", hover_color="#d35400", command=self.replace_text)
        self.btn_replace.pack(side="left", padx=5)

        self.btn_close = ctk.CTkButton(self.fr_panel, text="X", width=25, height=24, fg_color="#e74c3c", hover_color="#c0392b", command=self.hide_find_replace)
        self.btn_close.pack(side="right", padx=10)
        
        self.find_entry.focus_set()
        return "break"

    def hide_find_replace(self):
        if self.fr_panel:
            self.fr_panel.grid_forget()
            self.fr_panel = None
        self.editor.tag_remove("find_match", "1.0", tk.END)

    def find_text(self):
        self.editor.tag_remove("find_match", "1.0", tk.END)
        query = self.find_entry.get()
        if not query:
            return
            
        # Search editor
        start_pos = "1.0"
        idx = self.editor.search(query, start_pos, stopindex=tk.END)
        if idx:
            end_idx = f"{idx}+{len(query)}c"
            self.editor.tag_config("find_match", background="#d35400", foreground="white")
            self.editor.tag_add("find_match", idx, end_idx)
            self.editor.mark_set("insert", idx)
            self.editor.see(idx)

    def replace_text(self):
        query = self.find_entry.get()
        replacement = self.replace_entry.get()
        if not query:
            return
            
        cursor_pos = self.editor.index("insert")
        idx = self.editor.search(query, cursor_pos, stopindex=tk.END)
        if not idx:
            # Try from start
            idx = self.editor.search(query, "1.0", stopindex=tk.END)
            
        if idx:
            end_idx = f"{idx}+{len(query)}c"
            self.editor.delete(idx, end_idx)
            self.editor.insert(idx, replacement)
            self.full_coloring()
            # Highlight next
            self.find_text()

    # ---------- AST AUTO-FORMATTING ----------
    def auto_format_code(self):
        """
        Runs a pretty-print pass aligning indentation, braces, semicolons and spaces.
        """
        code = self.editor.get("1.0", "end-1c")
        lines = code.split("\n")
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append("")
                continue
                
            # If closing brace, decrement indent level first
            if stripped.startswith("}"):
                indent_level = max(0, indent_level - 1)
                
            indent_spaces = "    " * indent_level
            
            # Format operators spacing (basic regex cleaner)
            clean_line = stripped
            clean_line = re.sub(r"\s*([\+\-\*\/%]=|[\+\-\*\/\%><\=]=?)\s*", r" \1 ", clean_line)
            clean_line = re.sub(r"\s*,\s*", r", ", clean_line)
            clean_line = re.sub(r"\s*;\s*$", r";", clean_line)
            clean_line = re.sub(r"\s+", " ", clean_line)
            
            # Re-apply spacing for braces
            clean_line = clean_line.replace("{", " {")
            
            formatted_lines.append(f"{indent_spaces}{clean_line}")
            
            # If opening brace, increment indent level for next lines
            if stripped.endswith("{"):
                indent_level += 1
                
        formatted_code = "\n".join(formatted_lines)
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", formatted_code)
        
        self.update_line_numbers()
        self.full_coloring()

    # ---------- LIVE ERROR UNDERLINE ----------
    def underline_errors(self, error_lines):
        self.editor.tag_remove("error_underline", "1.0", tk.END)
        for line in error_lines:
            start = f"{line}.0"
            end = f"{line}.end"
            self.editor.tag_add("error_underline", start, end)

    # ---------- STANDARD INTERFACE HOOKS ----------
    def get(self, *args, **kwargs):
        return self.editor.get(*args, **kwargs)

    def insert(self, *args, **kwargs):
        self.editor.insert(*args, **kwargs)
        self.update_line_numbers()
        self.full_coloring()

    def delete(self, *args, **kwargs):
        self.editor.delete(*args, **kwargs)
        self.update_line_numbers()
        self.full_coloring()
