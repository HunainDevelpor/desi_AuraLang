from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CompilerError:
    phase: str          # 'Lexical', 'Syntax', 'Semantic'
    line: int
    column: int
    message: str
    suggested_fix: str
    recovery_action: str
    is_fatal: bool = False

class CompilerErrorManager:
    def __init__(self):
        self.errors: List[CompilerError] = []
        self.warnings: List[str] = []

    def clear(self):
        self.errors.clear()
        self.warnings.clear()

    def log_error(self, phase: str, line: int, column: int, message: str, suggested_fix: str = "", recovery_action: str = "", is_fatal: bool = False):
        # Prevent exact duplicate logging
        for err in self.errors:
            if err.phase == phase and err.line == line and err.column == column and err.message == message:
                return
        
        # Generate smart heuristics for suggestions if none provided
        if not suggested_fix:
            suggested_fix = self._generate_suggested_fix(phase, message)
        if not recovery_action:
            recovery_action = self._generate_recovery_action(phase, is_fatal)

        self.errors.append(CompilerError(
            phase=phase,
            line=line,
            column=column,
            message=message,
            suggested_fix=suggested_fix,
            recovery_action=recovery_action,
            is_fatal=is_fatal
        ))

    def log_warning(self, message: str):
        self.warnings.append(message)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_fatal_errors(self) -> bool:
        return any(err.is_fatal for err in self.errors)

    def get_errors_by_phase(self, phase: str) -> List[CompilerError]:
        return [err for err in self.errors if err.phase.lower() == phase.lower()]

    def _generate_suggested_fix(self, phase: str, message: str) -> str:
        msg = message.lower()
        if phase == "Lexical":
            if "unexpected character" in msg:
                return "Remove or replace the character with a valid Desi AuraLang operator or identifier."
            if "unexpected '!'" in msg:
                return "Did you mean '!=' for inequality check?"
            return "Check source syntax at this location."
        
        elif phase == "Syntax":
            if "expected ';'" in msg:
                return "Insert a semicolon ';' at the end of the statement."
            if "expected ')'" in msg:
                return "Add a closing parenthesis ')' to complete the expression."
            if "expected '}'" in msg:
                return "Add a closing brace '}' to enclose the code block."
            if "expected identifier" in msg:
                return "Provide a valid variable name or function identifier."
            return "Correct the keyword order or structural expression layout."
        
        elif phase == "Semantic":
            if "duplicate declaration" in msg:
                return "Choose a unique name or remove the duplicate variable declaration."
            if "undeclared variable" in msg:
                return "Make sure the variable is declared using 'rakho' before referencing it."
            if "type mismatch" in msg:
                return "Cast values or align variables to matching types (e.g. num, bool, string)."
            return "Ensure scoping variables and operands follow strict Desi AuraLang typing rules."
        
        return "Inspect source statement logic."

    def _generate_recovery_action(self, phase: str, is_fatal: bool) -> str:
        if is_fatal:
            return "Abort compilation phase (Fatal)."
        
        if phase == "Lexical":
            return "Skipped invalid character to continue scanning."
        elif phase == "Syntax":
            return "Synchronized parser state to next statement boundary."
        elif phase == "Semantic":
            return "Skipped invalid statement and continued symbol check."
        return "Logged diagnostic message."
