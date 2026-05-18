import tkinter as tk
import customtkinter as ctk
import math
import time

class DfaVisualizer(ctk.CTkFrame):
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.app = app

        # Configurations
        self.node_radius = 28
        self.active_dfa = "Identifier"
        
        # State tracking
        self.current_state = "q0"
        self.input_string = ""
        self.char_index = 0
        self.step_history = []
        self.is_running = False

        # Build UI layout
        self.create_widgets()
        self.select_dfa("Identifier")

    def create_widgets(self):
        # 1. Top Control Panel
        self.control_frame = ctk.CTkFrame(self, fg_color="#181818", corner_radius=15, height=60)
        self.control_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.control_frame, text="DFA Type:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(20, 5))
        
        self.dfa_selector = ctk.CTkOptionMenu(
            self.control_frame, 
            values=["Identifier", "Number (Int/Float)", "String Literal", "Comment"],
            command=self.select_dfa,
            width=170
        )
        self.dfa_selector.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.control_frame, text="Input Text:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(20, 5))
        self.input_entry = ctk.CTkEntry(self.control_frame, placeholder_text="e.g. x1_var", width=180)
        self.input_entry.pack(side="left", padx=5)
        self.input_entry.insert(0, "rakho_var")

        self.btn_extract = ctk.CTkButton(
            self.control_frame, 
            text="🔄 Extract from Editor", 
            width=150, 
            fg_color="#3498db", 
            hover_color="#2980b9", 
            command=self.extract_lexeme_action
        )
        self.btn_extract.pack(side="left", padx=5)
        
        self.btn_step = ctk.CTkButton(self.control_frame, text="Step", width=70, command=self.step_dfa)
        self.btn_step.pack(side="left", padx=5)

        self.btn_run = ctk.CTkButton(self.control_frame, text="Auto Run", width=90, fg_color="#2ecc71", hover_color="#27ae60", command=self.toggle_auto_run)
        self.btn_run.pack(side="left", padx=5)

        self.btn_reset = ctk.CTkButton(self.control_frame, text="Reset", width=70, fg_color="#e74c3c", hover_color="#c0392b", command=self.reset_simulation)
        self.btn_reset.pack(side="left", padx=5)

        # 2. Main Visual Canvas
        self.canvas_container = ctk.CTkFrame(self, fg_color="#101010", corner_radius=15)
        self.canvas_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_container, bg="#101010", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # 3. Bottom Output Console
        self.output_frame = ctk.CTkFrame(self, fg_color="#181818", corner_radius=15, height=150)
        self.output_frame.pack(fill="x", padx=10, pady=5)
        
        # Grid layout for console
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(1, weight=1)
        
        # Left side: Current char & active state display
        self.status_panel = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        self.status_panel.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")
        
        self.char_lbl = ctk.CTkLabel(self.status_panel, text="Input Status: Idle", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3498db", anchor="w")
        self.char_lbl.pack(fill="x", pady=2)
        
        self.state_lbl = ctk.CTkLabel(self.status_panel, text="Active State: q0", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ecf0f1", anchor="w")
        self.state_lbl.pack(fill="x", pady=2)
        
        self.result_lbl = ctk.CTkLabel(self.status_panel, text="Result: IDLE", font=ctk.CTkFont(size=16, weight="bold"), text_color="#95a5a6", anchor="w")
        self.result_lbl.pack(fill="x", pady=5)
        
        # Right side: Trace Log Textbox
        self.log_textbox = ctk.CTkTextbox(self.output_frame, height=110, fg_color="#121212", font=("Consolas", 11))
        self.log_textbox.grid(row=0, column=1, padx=20, pady=15, sticky="nsew")
        self.log_textbox.insert("1.0", "--- DFA Simulation Trace Log ---\nSelect DFA and click Step or Auto Run to start.\n")
        self.log_textbox.configure(state="disabled")

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert(tk.END, message + "\n")
        self.log_textbox.see(tk.END)
        self.log_textbox.configure(state="disabled")

    def clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        self.log_textbox.insert("1.0", "--- DFA Simulation Trace Log ---\n")
        self.log_textbox.configure(state="disabled")

    def select_dfa(self, selection):
        self.active_dfa = selection
        self.reset_simulation()
        
        lexeme = self.get_lexeme_from_code(selection)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, lexeme)
        
        self.draw_dfa_graph()

    def get_lexeme_from_code(self, selection):
        import re
        from lexer.tokens import TokenType
        
        default_inputs = {
            "Identifier": "x_var",
            "Number (Int/Float)": "30",
            "String Literal": '"AuraLang"',
            "Comment": "# desi_comment"
        }
        
        if not self.app or not hasattr(self.app, "code_editor"):
            return default_inputs.get(selection)
            
        code = self.app.code_editor.editor.get("1.0", tk.END)
        
        try:
            from lexer.lexer import Lexer
            from semantic.error_manager import CompilerErrorManager
            err_mgr = CompilerErrorManager()
            lexer = Lexer(code, err_mgr)
            tokens = lexer.tokenize()
        except Exception:
            tokens = []
            
        if selection == "Identifier":
            idents = [t.value for t in tokens if t.type == TokenType.IDENT]
            if idents:
                return idents[0]
            # Fallback regex
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

    def extract_lexeme_action(self):
        selection = self.dfa_selector.get()
        lexeme = self.get_lexeme_from_code(selection)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, lexeme)
        self.reset_simulation()
        self.log(f"Extracted '{lexeme}' from your current code editor for '{selection}' DFA.")

    def reset_simulation(self):
        self.current_state = "q0"
        self.char_index = 0
        self.is_running = False
        self.btn_run.configure(text="Auto Run", fg_color="#2ecc71", hover_color="#27ae60")
        self.input_string = self.input_entry.get().strip()
        self.step_history = []
        self.clear_log()
        
        self.char_lbl.configure(text=f"Input String: '{self.input_string}'", text_color="#3498db")
        self.state_lbl.configure(text="Active State: q0", text_color="#ecf0f1")
        self.result_lbl.configure(text="Result: IDLE (Step to start)", text_color="#95a5a6")
        
        self.draw_dfa_graph()

    def toggle_auto_run(self):
        if self.is_running:
            self.is_running = False
            self.btn_run.configure(text="Auto Run", fg_color="#2ecc71", hover_color="#27ae60")
        else:
            self.is_running = True
            self.btn_run.configure(text="Pause", fg_color="#e67e22", hover_color="#d35400")
            self.run_auto_loop()

    def run_auto_loop(self):
        if not self.is_running:
            return
        if self.char_index < len(self.input_string):
            self.step_dfa()
            self.after(800, self.run_auto_loop)
        else:
            self.is_running = False
            self.btn_run.configure(text="Auto Run", fg_color="#2ecc71", hover_color="#27ae60")

    def step_dfa(self):
        self.input_string = self.input_entry.get()
        if self.char_index == 0 and not self.step_history:
            self.log(f"Starting simulation of string: '{self.input_string}'")
            
        if self.char_index >= len(self.input_string):
            # Already at end, evaluate final acceptance
            self.evaluate_acceptance()
            return

        ch = self.input_string[self.char_index]
        prev_state = self.current_state
        next_state = self.get_transition(prev_state, ch)
        
        self.step_history.append((prev_state, ch, next_state))
        self.current_state = next_state
        self.char_index += 1
        
        # Log and display
        rem_str = self.input_string[self.char_index:]
        proc_str = self.input_string[:self.char_index]
        self.char_lbl.configure(text=f"Processed: '{proc_str}' | Remaining: '{rem_str}'", text_color="#f1c40f")
        self.state_lbl.configure(text=f"Active State: {self.current_state}", text_color="#e67e22")
        
        self.log(f"Step {self.char_index}: State {prev_state} -- '{ch}' --> State {next_state}")
        
        # Highlight active elements on canvas
        self.draw_dfa_graph()
        
        if self.current_state == "error":
            self.evaluate_acceptance()
            self.is_running = False
            self.btn_run.configure(text="Auto Run", fg_color="#2ecc71", hover_color="#27ae60")

        # If we just reached the end of the string, evaluate acceptance immediately
        if self.char_index >= len(self.input_string):
            self.evaluate_acceptance()

    def get_transition(self, state, ch):
        if state == "error":
            return "error"
            
        if self.active_dfa == "Identifier":
            if state == "q0":
                if ch.isalpha() or ch == "_":
                    return "q1"
                return "error"
            elif state == "q1":
                if ch.isalnum() or ch == "_":
                    return "q1"
                return "error"
                
        elif self.active_dfa == "Number (Int/Float)":
            if state == "q0":
                if ch.isdigit():
                    return "q1"
                return "error"
            elif state == "q1":
                if ch.isdigit():
                    return "q1"
                elif ch == ".":
                    return "q2"
                return "error"
            elif state == "q2":
                if ch.isdigit():
                    return "q3"
                return "error"
            elif state == "q3":
                if ch.isdigit():
                    return "q3"
                return "error"
                
        elif self.active_dfa == "String Literal":
            if state == "q0":
                if ch == '"':
                    return "q1"
                return "error"
            elif state == "q1":
                if ch == '"':
                    return "q2"
                return "q1" # keep in string body
            elif state == "q2":
                return "error" # characters after closing quote in same lexeme are errors
                
        elif self.active_dfa == "Comment":
            if state == "q0":
                if ch == "#":
                    return "q1"
                return "error"
            elif state == "q1":
                if ch == "\n":
                    return "q0" # reset at newline or continue
                return "q1" # continue comment body
                
        return "error"

    def evaluate_acceptance(self):
        accepted = False
        if self.active_dfa == "Identifier":
            accepted = (self.current_state == "q1")
        elif self.active_dfa == "Number (Int/Float)":
            accepted = (self.current_state in ("q1", "q3"))
        elif self.active_dfa == "String Literal":
            accepted = (self.current_state == "q2")
        elif self.active_dfa == "Comment":
            accepted = (self.current_state == "q1")

        if accepted:
            self.result_lbl.configure(text="Result: ACCEPTED ✓", text_color="#2ecc71")
            self.log(">>> Simulation Finished: LEXEME ACCEPTED! ✓")
        else:
            self.result_lbl.configure(text="Result: REJECTED ✗", text_color="#e74c3c")
            self.log(">>> Simulation Finished: LEXEME REJECTED! ✗")
            
        self.draw_dfa_graph()

    def draw_dfa_graph(self):
        self.canvas.delete("all")
        
        # Precompute positions of states based on active DFA
        states = {}
        accept_states = set()
        
        if self.active_dfa == "Identifier":
            states = {
                "q0": (150, 160, "Start State"),
                "q1": (450, 160, "Identifier Accepted")
            }
            accept_states = {"q1"}
            transitions = [
                ("q0", "q1", "[a-zA-Z_]", "straight"),
                ("q1", "q1", "[a-zA-Z0-9_]", "loop")
            ]
        elif self.active_dfa == "Number (Int/Float)":
            states = {
                "q0": (120, 160, "Start"),
                "q1": (280, 160, "Integer Part"),
                "q2": (440, 160, "Decimal Dot"),
                "q3": (600, 160, "Float Part")
            }
            accept_states = {"q1", "q3"}
            transitions = [
                ("q0", "q1", "[0-9]", "straight"),
                ("q1", "q1", "[0-9]", "loop"),
                ("q1", "q2", ".", "straight"),
                ("q2", "q3", "[0-9]", "straight"),
                ("q3", "q3", "[0-9]", "loop")
            ]
        elif self.active_dfa == "String Literal":
            states = {
                "q0": (150, 160, "Start"),
                "q1": (350, 160, "Inside String"),
                "q2": (550, 160, "String End")
            }
            accept_states = {"q2"}
            transitions = [
                ("q0", "q1", '"', "straight"),
                ("q1", "q1", 'any except "', "loop"),
                ("q1", "q2", '"', "straight")
            ]
        elif self.active_dfa == "Comment":
            states = {
                "q0": (150, 160, "Start"),
                "q1": (450, 160, "Comment Body")
            }
            accept_states = {"q1"}
            transitions = [
                ("q0", "q1", "#", "straight"),
                ("q1", "q1", "any except \\n", "loop")
            ]

        # Draw Error state if active
        if self.current_state == "error":
            states["error"] = (300, 290, "Trap State (Error)")
            # Add implicit error transition
            # Find the state that errored
            if self.step_history:
                last_valid = self.step_history[-1][0]
                transitions.append((last_valid, "error", f"'{self.step_history[-1][1]}'", "straight"))

        # Draw Transition Arrows first so they sit below nodes
        for src, dest, label, arrow_type in transitions:
            if src not in states or dest not in states:
                continue
            x1, y1, _ = states[src]
            x2, y2, _ = states[dest]
            
            # Determine color: highlight if it was the last transition executed
            is_active_transition = False
            if self.step_history:
                last_step = self.step_history[-1]
                if last_step[0] == src and last_step[2] == dest and last_step[1] in label:
                    is_active_transition = True
                # Helper for brackets/class labels
                elif last_step[0] == src and last_step[2] == dest:
                    if label.startswith("[") or "any" in label:
                        is_active_transition = True
                        
            color = "#f1c40f" if is_active_transition else "#444444"
            width = 3 if is_active_transition else 1.5
            
            if arrow_type == "loop":
                # Draw circular self loop at the top
                self.draw_self_loop(x1, y1 - self.node_radius, label, color, width)
            elif arrow_type == "straight":
                # Draw straight line with an arrow head, offsetting points to node boundaries
                self.draw_transition_line(x1, y1, x2, y2, label, color, width)

        # Draw States Nodes
        for state_name, (x, y, desc) in states.items():
            is_active = (state_name == self.current_state)
            is_accept = (state_name in accept_states)
            
            # Determine colors based on active/accept states
            outline_color = "#3498db"
            fill_color = "#1a1a1a"
            thickness = 2
            
            if is_active:
                outline_color = "#e67e22"
                fill_color = "#2c3e50"
                thickness = 4
            elif is_accept:
                outline_color = "#2ecc71"
                
            if state_name == "error":
                outline_color = "#e74c3c"
                fill_color = "#3c1a1a"
            
            # Draw outer node circle
            self.canvas.create_oval(
                x - self.node_radius, y - self.node_radius,
                x + self.node_radius, y + self.node_radius,
                fill=fill_color, outline=outline_color, width=thickness, tags="state"
            )
            
            # Draw double circle for accept states
            if is_accept:
                inner_r = self.node_radius - 5
                self.canvas.create_oval(
                    x - inner_r, y - inner_r,
                    x + inner_r, y + inner_r,
                    fill="", outline=outline_color, width=1.5, tags="state"
                )
                
            # State label inside
            self.canvas.create_text(
                x, y, text=state_name, fill="white", font=("Arial", 11, "bold")
            )
            
            # Description below node
            self.canvas.create_text(
                x, y + self.node_radius + 15, text=desc, fill="#7f8c8d", font=("Arial", 9)
            )

    def draw_self_loop(self, x, y, label, color, width):
        # Create a visual loop (arc) at the top of a node
        r = 20
        cx = x
        cy = y - r + 5
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=-30, extent=240, style="arc", outline=color, width=width
        )
        # Draw arrow head
        # End point of loop at -30 deg: x = cx + r*cos(-30), y = cy + r*sin(-30)
        theta = math.radians(-25)
        arrow_x = cx + r * math.cos(theta)
        arrow_y = cy - r * math.sin(theta)
        self.canvas.create_line(
            arrow_x - 3, arrow_y - 6, arrow_x, arrow_y, fill=color, width=width
        )
        self.canvas.create_line(
            arrow_x + 5, arrow_y - 3, arrow_x, arrow_y, fill=color, width=width
        )
        # Text label above loop
        self.canvas.create_text(
            cx, cy - r - 10, text=label, fill="#bdc3c7", font=("Consolas", 10)
        )

    def draw_transition_line(self, x1, y1, x2, y2, label, color, width):
        # Calculate angle of transition line
        angle = math.atan2(y2 - y1, x2 - x1)
        
        # Calculate intersections at boundaries of state circles
        start_x = x1 + self.node_radius * math.cos(angle)
        start_y = y1 + self.node_radius * math.sin(angle)
        
        end_x = x2 - self.node_radius * math.cos(angle)
        end_y = y2 - self.node_radius * math.sin(angle)
        
        # Draw transition arrow line
        self.canvas.create_line(
            start_x, start_y, end_x, end_y,
            fill=color, width=width, arrow="last", arrowshape=(10, 12, 4)
        )
        
        # Label in the middle with background rectangle
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # Offset label vertically slightly to not sit on line
        offset_y = -12 if angle == 0 else 12
        
        self.canvas.create_text(
            mid_x, mid_y + offset_y, text=label, fill="#bdc3c7", font=("Consolas", 10)
        )
