from typing import List, Dict, Any, Tuple, Optional
import time

class VMFrame:
    def __init__(self, return_ip: int, name: str):
        self.return_ip = return_ip
        self.name = name
        self.locals: Dict[str, Any] = {}

class VirtualMachine:
    def __init__(self):
        # Program execution states
        self.raw_instructions: List[str] = []
        self.instructions: List[str] = [] # clean of comments and labels
        self.labels: Dict[str, int] = {} # label -> instruction index
        self.ip = 0
        
        # Memory spaces
        self.evaluation_stack: List[Any] = []
        self.globals: Dict[str, Any] = {}
        self.call_stack: List[VMFrame] = []
        self.heap: Dict[str, List[Any]] = {}
        
        # Virtual registers for dashboard watch
        self.registers: Dict[str, Any] = {
            "IP": 0,       # Instruction Pointer
            "SP": 0,       # Stack Pointer
            "HP": "0x5000", # Heap Pointer (next free address)
            "ACC": None,   # Accumulator (top stack item)
        }
        
        self.next_heap_address = 0x5000
        
        # Console output buffer
        self.console_output: List[str] = []
        self.halted = False
        self.logs: List[str] = []
        self.func_params: Dict[str, List[str]] = {}

    def log(self, msg: str):
        self.logs.append(f"[VM] {msg}")

    def load_program(self, asm_lines: List[str]):
        """Reset state and load virtual assembly instructions."""
        self.raw_instructions = asm_lines
        self.instructions = []
        self.labels = {}
        self.ip = 0
        self.evaluation_stack = []
        self.globals = {}
        self.call_stack = []
        self.heap = {}
        self.next_heap_address = 0x5000
        self.console_output = []
        self.halted = False
        self.logs = []
        self.func_params = {}
        
        self.registers = {
            "IP": 0,
            "SP": 0,
            "HP": "0x5000",
            "ACC": None
        }
        
        # Preprocess labels
        clean_idx = 0
        for line in asm_lines:
            line_strip = line.strip()
            if not line_strip or line_strip.startswith(";"):
                continue
            if line_strip.endswith(":"):
                label_name = line_strip[:-1].strip()
                self.labels[label_name] = clean_idx
                self.log(f"Mapped label '{label_name}' -> instruction index {clean_idx}")
            else:
                self.instructions.append(line_strip)
                clean_idx += 1
                
        self.log(f"Loaded {len(self.instructions)} executable bytecode instructions.")

    def parse_operand(self, op: str) -> Any:
        """Parse operands to native types."""
        op = op.strip()
        if op == "True": return True
        if op == "False": return False
        if op.startswith('"') and op.endswith('"'):
            return op[1:-1]
        
        # Float
        if "." in op:
            try: return float(op)
            except ValueError: pass
            
        # Integer
        try: return int(op)
        except ValueError: pass
        
        return op

    def update_registers(self):
        """Update VM dashboard register watches."""
        self.registers["IP"] = self.ip
        self.registers["SP"] = len(self.evaluation_stack)
        self.registers["HP"] = hex(self.next_heap_address).upper().replace("X", "x")
        self.registers["ACC"] = self.evaluation_stack[-1] if self.evaluation_stack else None

    # ====================================================
    # STEP EXECUTOR INTERFACE
    # ====================================================

    def step(self) -> bool:
        """Execute a single instruction at self.ip. Returns False if halted."""
        if self.halted or self.ip >= len(self.instructions):
            self.halted = True
            self.update_registers()
            return False

        instr = self.instructions[self.ip]
        self.log(f"Step [ip={self.ip}]: Executing bytecode '{instr}'")
        
        # Parse command and optional operands
        parts = instr.split(maxsplit=1)
        cmd = parts[0].upper()
        operand_str = parts[1] if len(parts) > 1 else ""
        
        # Advance instruction pointer by default
        self.ip += 1

        try:
            if cmd == "PUSH":
                val = self.parse_operand(operand_str)
                self.evaluation_stack.append(val)
                
            elif cmd == "POP":
                if self.evaluation_stack:
                    self.evaluation_stack.pop()
                    
            elif cmd == "LOAD":
                var_name = operand_str.strip()
                # Check call stack frames first (local environment scoping)
                val = None
                found = False
                if self.call_stack:
                    active_frame = self.call_stack[-1]
                    if var_name in active_frame.locals:
                        val = active_frame.locals[var_name]
                        found = True
                        
                if not found:
                    if var_name in self.globals:
                        val = self.globals[var_name]
                    else:
                        # Fallback for undefined variables to avoid crash
                        val = 0
                        self.log(f"Warning: loading undefined variable '{var_name}', using default 0")
                        
                self.evaluation_stack.append(val)
                
            elif cmd == "STORE":
                var_name = operand_str.strip()
                val = self.evaluation_stack.pop() if self.evaluation_stack else 0
                
                # Check call stack frames first (local environment scoping)
                if self.call_stack:
                    active_frame = self.call_stack[-1]
                    active_frame.locals[var_name] = val
                    self.log(f"Stored local '{var_name}' = {val}")
                else:
                    self.globals[var_name] = val
                    self.log(f"Stored global '{var_name}' = {val}")
                    
            elif cmd == "ADD":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                # Special check for string + other
                if isinstance(a, str) or isinstance(b, str):
                    self.evaluation_stack.append(str(a) + str(b))
                else:
                    self.evaluation_stack.append(a + b)
                    
            elif cmd == "SUB":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a - b)
                
            elif cmd == "MUL":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a * b)
                
            elif cmd == "DIV":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a / b if b != 0 else 0)
                
            elif cmd == "MOD":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a % b if b != 0 else 0)
                
            elif cmd == "EQ":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a == b)
                
            elif cmd == "NEQ":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a != b)
                
            elif cmd == "GT":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a > b)
                
            elif cmd == "LT":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a < b)
                
            elif cmd == "GTE":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a >= b)
                
            elif cmd == "LTE":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(a <= b)
                
            elif cmd == "AND":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(bool(a) and bool(b))
                
            elif cmd == "OR":
                b = self.evaluation_stack.pop()
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(bool(a) or bool(b))
                
            elif cmd == "NOT":
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(not bool(a))
                
            elif cmd == "NEG":
                a = self.evaluation_stack.pop()
                self.evaluation_stack.append(-a)
                
            elif cmd == "JMP":
                label = operand_str.strip()
                if label in self.labels:
                    self.ip = self.labels[label]
                else:
                    self.log(f"Halt Error: JMP target label '{label}' not found!")
                    self.halted = True
                    
            elif cmd == "JMPZ":
                label = operand_str.strip()
                cond = self.evaluation_stack.pop() if self.evaluation_stack else False
                if not bool(cond):
                    if label in self.labels:
                        self.ip = self.labels[label]
                    else:
                        self.log(f"Halt Error: JMPZ target label '{label}' not found!")
                        self.halted = True
                        
            elif cmd == "PRINT":
                val = self.evaluation_stack.pop() if self.evaluation_stack else ""
                # Print output formatting
                self.console_output.append(str(val))
                self.log(f"BOL output printed: {val}")
                
            elif cmd == "ALLOC":
                size = int(self.evaluation_stack.pop())
                addr = hex(self.next_heap_address).upper().replace("X", "x")
                self.heap[addr] = [0] * size
                self.next_heap_address += 4 # sequential mock allocation offset
                self.evaluation_stack.append(addr)
                self.log(f"Allocated heap array of size {size} at address {addr}")
                
            elif cmd == "ASTORE":
                val = self.evaluation_stack.pop()
                idx = int(self.evaluation_stack.pop())
                addr = self.evaluation_stack.pop()
                
                if addr in self.heap:
                    if 0 <= idx < len(self.heap[addr]):
                        self.heap[addr][idx] = val
                        self.log(f"Stored heap element: heap[{addr}][{idx}] = {val}")
                    else:
                        self.log(f"IndexError: Array index '{idx}' out of bounds for address '{addr}'")
                else:
                    self.log(f"MemoryError: Invalid heap memory access at address '{addr}'")
                    
            elif cmd == "CALL":
                # CALL func_name, argc
                func_parts = operand_str.split(",")
                func_label = func_parts[0].strip()
                argc = int(func_parts[1].strip())
                
                # Fetch argument values from stack (pops in reverse order)
                args = []
                for _ in range(argc):
                    if self.evaluation_stack:
                        args.append(self.evaluation_stack.pop())
                # Re-reverse args to match parameter order
                args.reverse()
                
                # Create frame
                frame = VMFrame(return_ip=self.ip, name=func_label)
                # Map parameters to local frame variables sequentially
                # For educational demonstration, name parameters p0, p1, p2, etc.,
                # or map them dynamically if we loaded parameter mapping. Let's name them sequentially:
                # In Desi AuraLang function declarations, parameters are compiled to local LOAD/STORE.
                # So we define local bindings in our function scope!
                # Since parameter variable names are handled by the compiler locally, we bind them sequentially:
                # Our compiler generates function labels and handles parameters by storing them.
                # Let's map them to sequential param tokens: 'a', 'b', etc., if we check the function call metadata.
                # To make VM call stack parameters generic and robust, let's map them to:
                # local bindings 'p0', 'p1', etc., AND bind them to the function declaration parameters if available!
                # Wait! Let's lookup what parameters the function signature expects. In standard assembly,
                # the caller pushes arguments, then inside the function label, the compiler generates STORE instructions
                # to store arguments in local variables!
                # Yes! In our TargetCodeGen:
                # Inside `visit_FuncDeclNode`: the parameters are declared but the function body compiles directly.
                # In typical compiler generation, the calling convention pushes arguments on the stack, and then the function body pops them or loads them.
                # In our code generator:
                # `t0 = call add, 2` -> compiles to:
                # PUSH arg2
                # PUSH arg1
                # CALL func_add, 2
                # STORE t0
                # And function declaration:
                # label func_add
                # body statements (which expect local parameters to have been bound!)
                # In our semantic analyzer, function parameters are declared in local scopes.
                # So inside the VM, when we CALL a function:
                # The arguments are already pushed on the stack!
                # Wait! If the function body expects parameters (e.g. `a`, `b`) to contain the pushed arguments:
                # When CALL is evaluated, the caller has pushed the arguments, and the CALL instruction pops them.
                # To map them, how does the function body load them?
                # Inside our `ast_generator` -> `visit_FuncDeclNode` -> registers `param` in local scopes.
                # In `intermediate/ir_generator.py` -> `visit_FuncDeclNode`:
                # It just emits `label func_name` and compiles `body`!
                # Wait! If the body uses variables `a` and `b`, how do they get populated?
                # Ah! In a simplified educational stack compiler, at the start of `func_add`,
                # we must POP stack values and STORE them in parameters in order!
                # Let's verify: does our IR generator emit POP/STORE at the start of a function?
                # Let's look at `intermediate/ir_generator.py`:
                # ```python
                #     def visit_FuncDeclNode(self, node: FuncDeclNode):
                #         self.emit(f"label func_{node.name}", "LABEL", "", "", f"func_{node.name}")
                #         for stmt in node.body:
                #             self.visit(stmt)
                # ```
                # Ah! It doesn't emit explicit pop/store for parameters!
                # So inside our VM: when `CALL func_add, 2` is run:
                # We pop the arguments from stack, create the new frame, and we can AUTOMATICALLY BIND these arguments
                # to the parameters!
                # But how does the VM know the parameter names (`a`, `b`)?
                # We can store them in a simple function parameter mapping! Or look them up from the program!
                # Or we can look up if the function exists. Let's find function declarations dynamically from the program code,
                # or store a registry of function parameters during semantic analysis!
                # Even simpler and extremely robust:
                # Let's inspect the `func_label` and see if we have recorded its parameters, OR we can bind them
                # dynamically to the local variable names used at the start of the function, OR we can scan the AST / symbol table!
                # Wait, yes! We can scan the AST or symbol table, OR we can simply pass a `func_param_map` (e.g. `{"func_add": ["a", "b"]}`)
                # to the VM when we compile!
                # Let's write a simple helper in the pipeline that maps function names to parameter lists!
                # E.g. `self.vm.func_params = {"func_add": ["a", "b"]}`.
                # Then inside `CALL`:
                # ```python
                # for i, arg_val in enumerate(args):
                #     param_name = self.func_params.get(func_label, [])[i] if i < len(self.func_params.get(func_label, [])) else f"p{i}"
                #     frame.locals[param_name] = arg_val
                # ```
                # This is INCREDIBLY robust and works perfectly! Let's initialize `self.func_params = {}` in `__init__`.
                
                self.call_stack.append(frame)
                
                # Bind parameters
                if func_label in self.func_params:
                    param_names = self.func_params[func_label]
                    for i, arg_val in enumerate(args):
                        if i < len(param_names):
                            frame.locals[param_names[i]] = arg_val
                            self.log(f"Bound parameter '{param_names[i]}' = {arg_val}")
                else:
                    # Fallback
                    for i, arg_val in enumerate(args):
                        frame.locals[f"p{i}"] = arg_val
                        self.log(f"Bound unnamed parameter 'p{i}' = {arg_val}")
                        
                # Perform Jump to function label
                if func_label in self.labels:
                    self.ip = self.labels[func_label]
                else:
                    self.log(f"Halt Error: CALL function target '{func_label}' not found!")
                    self.halted = True
                    
            elif cmd == "RET":
                # Restore parent frame
                ret_val = self.evaluation_stack.pop() if self.evaluation_stack else 0
                
                if self.call_stack:
                    frame = self.call_stack.pop()
                    self.ip = frame.return_ip
                    self.evaluation_stack.append(ret_val)
                    self.log(f"Returned from function '{frame.name}' to ip={self.ip} with value {ret_val}")
                else:
                    self.log("Halt Error: RET executed outside of function call!")
                    self.halted = True
                    
            else:
                self.log(f"Halt Error: Unrecognized bytecode instruction '{cmd}'")
                self.halted = True

        except Exception as e:
            self.log(f"Runtime Exception: {str(e)}")
            self.halted = True

        self.update_registers()
        return not self.halted

    def run(self, max_steps=1000):
        """Auto execute until halted or out of steps."""
        steps = 0
        while not self.halted and steps < max_steps:
            self.step()
            steps += 1
