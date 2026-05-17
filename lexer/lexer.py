from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from .tokens import Token, TokenType


class LexError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"[LexError] Line {line}, Col {col}: {message}")
        self.line = line
        self.col = col


@dataclass
class Lexer:
    source: str
    error_manager: Optional[Any] = None

    def __post_init__(self):
        self.pos = 0
        self.line = 1
        self.col = 1
        self.comments = []

        # keyword table: word -> TokenType
        self.keywords = {
            "rakho": TokenType.RAKHO,
            "bol": TokenType.BOL,
            "agar": TokenType.AGAR,
            "warna": TokenType.WARNA,
            "ghumo": TokenType.GHUMO,
            "jabtak": TokenType.JABTAK,
            "tarkeeb": TokenType.TARKEEB,
            "wapas": TokenType.WAPAS,
            "sahi": TokenType.SAHI,
            "galat": TokenType.GALAT,
            "and": TokenType.AND,
            "or": TokenType.OR,
            "not": TokenType.NOT,
            "from": TokenType.FROM,
            "to": TokenType.TO,
        }

    # ---------- basic character helpers ----------
    def _at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _peek(self) -> str:
        if self._at_end():
            return "\0"
        return self.source[self.pos]

    def _peek_next(self) -> str:
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        """Consume and return current char, updating line/col."""
        ch = self._peek()
        self.pos += 1

        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1

        return ch

    def _match(self, expected: str) -> bool:
        """If next char equals expected, consume it and return True."""
        if self._peek() != expected:
            return False
        self._advance()
        return True

    # ---------- skipping whitespace/comments ----------
    def _skip_ignored(self) -> None:
        while True:
            ch = self._peek()

            # whitespace
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
                continue

            # comment: # ... end of line
            if ch == "#":
                comment_text = ""
                self._advance() # consume '#'
                while self._peek() not in ("\n", "\0"):
                    comment_text += self._advance()
                self.comments.append(comment_text)
                continue

            break

    # ---------- token scanners ----------
    def _scan_identifier_or_keyword(self) -> Token:
        start_line, start_col = self.line, self.col
        text = ""

        # first char already confirmed as letter/_ by caller
        while (self._peek().isalnum() or self._peek() == "_"):
            text += self._advance()

        ttype = self.keywords.get(text, TokenType.IDENT)

        # booleans are keywords but also literal values; we keep value as Python bool
        if ttype == TokenType.SAHI:
            return Token(TokenType.SAHI, True, start_line, start_col)
        if ttype == TokenType.GALAT:
            return Token(TokenType.GALAT, False, start_line, start_col)

        # for other keywords/idents store text
        return Token(ttype, text, start_line, start_col)

    def _scan_number(self) -> Token:
        start_line, start_col = self.line, self.col
        text = ""

        while self._peek().isdigit():
            text += self._advance()

        # float part
        if self._peek() == "." and self._peek_next().isdigit():
            text += self._advance()  # consume '.'
            while self._peek().isdigit():
                text += self._advance()
            return Token(TokenType.NUMBER, float(text), start_line, start_col)

        return Token(TokenType.NUMBER, int(text), start_line, start_col)

    def _scan_string(self) -> Token:
        start_line, start_col = self.line, self.col

        self._advance()  # consume opening quote "
        out = ""

        escapes = {
            "n": "\n",
            "t": "\t",
            '"': '"',
            "\\": "\\",
        }

        while True:
            ch = self._peek()

            if ch == "\0":
                raise LexError("Unterminated string literal", start_line, start_col)

            if ch == '"':
                self._advance()  # consume closing quote
                break

            if ch == "\\":
                self._advance()  # consume backslash
                esc = self._peek()
                if esc == "\0":
                    raise LexError("Unterminated escape sequence", self.line, self.col)
                if esc not in escapes:
                    raise LexError(f"Unknown escape '\\{esc}'", self.line, self.col)
                out += escapes[esc]
                self._advance()
                continue

            out += self._advance()

        return Token(TokenType.STRING, out, start_line, start_col)

    # ---------- main tokenize ----------
    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while not self._at_end():
            self._skip_ignored()

            if self._at_end():
                break

            ch = self._peek()
            start_line, start_col = self.line, self.col

            try:
                # identifier/keyword
                if ch.isalpha() or ch == "_":
                    tokens.append(self._scan_identifier_or_keyword())
                    continue

                # number
                if ch.isdigit():
                    tokens.append(self._scan_number())
                    continue

                # string
                if ch == '"':
                    tokens.append(self._scan_string())
                    continue

                # operators & punctuation (single or double char)
                if ch == "+":
                    self._advance()
                    tokens.append(Token(TokenType.PLUS, None, start_line, start_col))
                    continue

                if ch == "-":
                    self._advance()
                    tokens.append(Token(TokenType.MINUS, None, start_line, start_col))
                    continue

                if ch == "*":
                    self._advance()
                    tokens.append(Token(TokenType.STAR, None, start_line, start_col))
                    continue

                if ch == "/":
                    self._advance()
                    tokens.append(Token(TokenType.SLASH, None, start_line, start_col))
                    continue

                if ch == "%":
                    self._advance()
                    tokens.append(Token(TokenType.PERCENT, None, start_line, start_col))
                    continue

                if ch == "=":
                    self._advance()
                    if self._match("="):
                        tokens.append(Token(TokenType.EQ, None, start_line, start_col))
                    else:
                        tokens.append(Token(TokenType.ASSIGN, None, start_line, start_col))
                    continue

                if ch == "!":
                    self._advance()
                    if self._match("="):
                        tokens.append(Token(TokenType.NEQ, None, start_line, start_col))
                    else:
                        raise LexError("Unexpected '!'. Did you mean '!=' ?", start_line, start_col)
                    continue

                if ch == ">":
                    self._advance()
                    if self._match("="):
                        tokens.append(Token(TokenType.GTE, None, start_line, start_col))
                    else:
                        tokens.append(Token(TokenType.GT, None, start_line, start_col))
                    continue

                if ch == "<":
                    self._advance()
                    if self._match("="):
                        tokens.append(Token(TokenType.LTE, None, start_line, start_col))
                    else:
                        tokens.append(Token(TokenType.LT, None, start_line, start_col))
                    continue

                if ch == "(":
                    self._advance()
                    tokens.append(Token(TokenType.LPAREN, None, start_line, start_col))
                    continue

                if ch == ")":
                    self._advance()
                    tokens.append(Token(TokenType.RPAREN, None, start_line, start_col))
                    continue

                if ch == "{":
                    self._advance()
                    tokens.append(Token(TokenType.LBRACE, None, start_line, start_col))
                    continue

                if ch == "}":
                    self._advance()
                    tokens.append(Token(TokenType.RBRACE, None, start_line, start_col))
                    continue

                if ch == "[":
                    self._advance()
                    tokens.append(Token(TokenType.LBRACKET, None, start_line, start_col))
                    continue

                if ch == "]":
                    self._advance()
                    tokens.append(Token(TokenType.RBRACKET, None, start_line, start_col))
                    continue

                if ch == ",":
                    self._advance()
                    tokens.append(Token(TokenType.COMMA, None, start_line, start_col))
                    continue

                if ch == ";":
                    self._advance()
                    tokens.append(Token(TokenType.SEMI, None, start_line, start_col))
                    continue

                # unknown character
                raise LexError(f"Unexpected character '{ch}'", start_line, start_col)

            except LexError as e:
                if self.error_manager:
                    self.error_manager.log_error(
                        phase="Lexical",
                        line=e.line,
                        column=e.col,
                        message=str(e),
                        suggested_fix="",
                        recovery_action="Skipped invalid character.",
                        is_fatal=False
                    )
                    self._advance() # Skip bad character
                else:
                    raise e

        # EOF token
        tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return tokens