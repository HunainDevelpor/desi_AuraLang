from typing import List, Dict, Any, Callable, Optional

class InteractiveDebugger:
    def __init__(self, vm):
        self.vm = vm
        self.is_running = False
        self.delay_ms = 400 # Speed of step-through execution
        
        # Symbol tables mapping clean instruction indices -> external coordinates
        self.ip_to_source_line: Dict[int, int] = {}
        self.ip_to_tac_line: Dict[int, int] = {}
        self.ip_to_asm_line: Dict[int, int] = {}
        
        self.raw_asm: List[str] = []
        self.on_step_callback: Optional[Callable[[], None]] = None
        self.after_id: Optional[str] = None
        self.master_widget = None # For schedule callbacks

    def load_program(self, raw_asm: List[str], master_widget=None):
        """Loads bytecode assembly and maps clean executable pointers to debugger symbols."""
        self.raw_asm = raw_asm
        self.master_widget = master_widget
        
        # Initialize VM program
        self.vm.load_program(raw_asm)
        self.is_running = False
        if self.after_id and self.master_widget:
            try:
                self.master_widget.after_cancel(self.after_id)
            except:
                pass
            self.after_id = None
            
        self.ip_to_source_line.clear()
        self.ip_to_tac_line.clear()
        self.ip_to_asm_line.clear()

        # Parse debugging symbol annotations from comments
        curr_src_line = 1
        curr_tac_idx = 0
        clean_idx = 0
        
        for raw_idx, line in enumerate(raw_asm):
            line_strip = line.strip()
            if not line_strip:
                continue
                
            if line_strip.startswith("; line"):
                try:
                    curr_src_line = int(line_strip.replace("; line", "").strip())
                except ValueError:
                    pass
            elif line_strip.startswith("; tac_idx"):
                try:
                    curr_tac_idx = int(line_strip.replace("; tac_idx", "").strip())
                except ValueError:
                    pass
            elif line_strip.startswith(";"):
                continue
            elif line_strip.endswith(":"):
                # label declaration
                continue
            else:
                # Clean executable instruction found!
                self.ip_to_source_line[clean_idx] = curr_src_line
                self.ip_to_tac_line[clean_idx] = curr_tac_idx
                self.ip_to_asm_line[clean_idx] = raw_idx + 1 # 1-based editor line number
                clean_idx += 1

    def get_current_source_line(self) -> int:
        """Get the active source code line corresponding to current VM IP."""
        return self.ip_to_source_line.get(self.vm.ip, 1)

    def get_current_tac_index(self) -> int:
        """Get the active TAC quadruple index corresponding to current VM IP."""
        return self.ip_to_tac_line.get(self.vm.ip, 0)

    def get_current_asm_line(self) -> int:
        """Get the active Assembly text line corresponding to current VM IP."""
        return self.ip_to_asm_line.get(self.vm.ip, 1)

    def step_into(self) -> bool:
        """Execute exactly one instruction, entering calls."""
        if self.vm.halted:
            return False
        success = self.vm.step()
        if self.on_step_callback:
            self.on_step_callback()
        return success

    def step_over(self) -> bool:
        """Execute one instruction. If it is a CALL, run until it returns to same call stack depth."""
        if self.vm.halted:
            return False
            
        # Check current instruction
        if self.vm.ip < len(self.vm.instructions):
            instr = self.vm.instructions[self.vm.ip]
            if instr.strip().upper().startswith("CALL"):
                # Track original frame depth
                target_depth = len(self.vm.call_stack)
                # Single step into the call
                self.vm.step()
                
                # Keep running until the call stack drops back or VM halts
                while not self.vm.halted and len(self.vm.call_stack) > target_depth:
                    self.vm.step()
                    
                if self.on_step_callback:
                    self.on_step_callback()
                return not self.vm.halted
                
        # Normal step if not a function call
        return self.step_into()

    def start_auto(self, callback: Callable[[], None]):
        """Initiate auto-stepping loop at constant clock intervals."""
        if self.vm.halted:
            return
            
        self.is_running = True
        self.on_step_callback = callback
        
        if self.after_id and self.master_widget:
            self.master_widget.after_cancel(self.after_id)
            
        self._auto_step_loop()

    def _auto_step_loop(self):
        if not self.is_running or self.vm.halted:
            self.is_running = False
            if self.on_step_callback:
                self.on_step_callback()
            return
            
        success = self.step_into()
        if success and not self.vm.halted and self.master_widget:
            self.after_id = self.master_widget.after(self.delay_ms, self._auto_step_loop)
        else:
            self.is_running = False
            if self.on_step_callback:
                self.on_step_callback()

    def pause(self):
        """Pause automated simulation execution."""
        self.is_running = False
        if self.after_id and self.master_widget:
            try:
                self.master_widget.after_cancel(self.after_id)
            except:
                pass
            self.after_id = None

    def reset(self):
        """Reset debugging pointer and clear memory structures."""
        self.pause()
        self.vm.load_program(self.raw_asm)
        if self.on_step_callback:
            self.on_step_callback()
