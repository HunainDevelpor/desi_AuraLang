from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    # Keywords
    RAKHO = auto()
    BOL = auto()
    AGAR = auto()
    WARNA = auto()
    GHUMO = auto()
    JABTAK = auto()
    TARKEEB = auto()
    WAPAS = auto()
    SAHI = auto()
    GALAT = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    FROM = auto()
    TO = auto()

    # Identifiers + literals
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()

    # Comparisons
    EQ = auto()     # ==
    NEQ = auto()    # !=
    GT = auto()     # >
    LT = auto()     # <
    GTE = auto()    # >=
    LTE = auto()    # <=

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMI = auto()

    # End marker
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    line: int
    col: int

    def __repr__(self) -> str:
        if self.value is None:
            return f"{self.type.name} @({self.line}:{self.col})"
        return f"{self.type.name}({self.value}) @({self.line}:{self.col})"