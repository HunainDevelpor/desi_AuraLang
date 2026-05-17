from lexer.tokens import TokenType, Token
from typing import List, Set

class SyntaxRecovery:
    # Set of tokens that denote statement boundaries or major blocks
    SYNCHRONIZING_TOKENS: Set[TokenType] = {
        TokenType.SEMI,
        TokenType.RBRACE,
        TokenType.RAKHO,
        TokenType.BOL,
        TokenType.AGAR,
        TokenType.JABTAK,
        TokenType.TARKEEB,
        TokenType.WAPAS,
        TokenType.EOF
    }

    @staticmethod
    def synchronize(tokens: List[Token], current_pos: int) -> int:
        """
        Skip tokens until we reach a synchronization token boundary.
        Returns the new position to resume parsing from.
        """
        pos = current_pos
        while pos < len(tokens):
            tok = tokens[pos]
            
            # If we hit EOF, stop
            if tok.type == TokenType.EOF:
                return pos
                
            # If the current token is a semicolon, we can consume it and resume at the next token
            if tok.type == TokenType.SEMI:
                return pos + 1
                
            # If the next token is a major block keyword, we resume parsing right at that keyword
            if tok.type in SyntaxRecovery.SYNCHRONIZING_TOKENS:
                return pos
                
            pos += 1
            
        return len(tokens) - 1
