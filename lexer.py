"""
Lexer for mathematical expressions.
Uses regex-based token matching and a TokenType enum.
"""

import re
from enum import Enum
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Token Types
# ---------------------------------------------------------------------------

class TokenType(Enum):
    # Numbers
    INT      = "INT"
    FLOAT    = "FLOAT"
    # Operators
    PLUS     = "PLUS"
    MINUS    = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE   = "DIVIDE"
    POWER    = "POWER"
    ASSIGN   = "ASSIGN"
    # Trigonometric functions
    SIN      = "SIN"
    COS      = "COS"
    # Constants
    PI       = "PI"
    E        = "E"
    # Delimiters
    LPAREN   = "LPAREN"
    RPAREN   = "RPAREN"
    COMMA    = "COMMA"
    # Special
    IDENT    = "IDENT"
    EOF      = "EOF"
    ILLEGAL  = "ILLEGAL"


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------

@dataclass
class Token:
    type:  TokenType
    value: str
    line:  int
    col:   int

    def __repr__(self) -> str:
        return (
            f"Token({self.type.value:<10} "
            f"{repr(self.value):<10} "
            f"line={self.line}, col={self.col})"
        )


# ---------------------------------------------------------------------------
# Keyword lookup table
# ---------------------------------------------------------------------------

KEYWORDS: dict[str, TokenType] = {
    "sin": TokenType.SIN,
    "cos": TokenType.COS,
    "pi":  TokenType.PI,
    "e":   TokenType.E,
}

# ---------------------------------------------------------------------------
# Regex token patterns  (order matters — FLOAT before INT)
# ---------------------------------------------------------------------------

TOKEN_PATTERNS: list[tuple[TokenType, re.Pattern]] = [
    (TokenType.FLOAT,    re.compile(r"\d+\.\d+")),
    (TokenType.INT,      re.compile(r"\d+")),
    (TokenType.PLUS,     re.compile(r"\+")),
    (TokenType.MINUS,    re.compile(r"-")),
    (TokenType.MULTIPLY, re.compile(r"\*")),
    (TokenType.DIVIDE,   re.compile(r"/")),
    (TokenType.POWER,    re.compile(r"\^")),
    (TokenType.ASSIGN,   re.compile(r"=")),
    (TokenType.LPAREN,   re.compile(r"\(")),
    (TokenType.RPAREN,   re.compile(r"\)")),
    (TokenType.COMMA,    re.compile(r",")),
    (TokenType.IDENT,    re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")),
]

WHITESPACE = re.compile(r"[ \t\r]+")
NEWLINE    = re.compile(r"\n")


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

class Lexer:
    """
    Converts a source string into a flat list of Tokens.
    Uses compiled regex patterns for each token category.
    """

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos  = 0
        self.line = 1
        self.col  = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tokenize(self) -> list[Token]:
        """Return all tokens including a trailing EOF."""
        tokens: list[Token] = []
        while self.pos < len(self.text):
            token = self._next_token()
            if token is not None:
                tokens.append(token)
        tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return tokens

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_token(self) -> Token | None:
        """Try to match the next token at the current position."""

        # Skip whitespace (no newlines)
        m = WHITESPACE.match(self.text, self.pos)
        if m:
            self.col += m.end() - m.start()
            self.pos  = m.end()
            return None

        # Handle newlines (update line counter)
        m = NEWLINE.match(self.text, self.pos)
        if m:
            self.line += 1
            self.col   = 1
            self.pos   = m.end()
            return None

        saved_line = self.line
        saved_col  = self.col

        # Try each pattern in priority order
        for token_type, pattern in TOKEN_PATTERNS:
            m = pattern.match(self.text, self.pos)
            if m:
                value = m.group(0)
                # Resolve keyword vs generic identifier
                if token_type == TokenType.IDENT:
                    token_type = KEYWORDS.get(value, TokenType.IDENT)
                self.pos += len(value)
                self.col += len(value)
                return Token(token_type, value, saved_line, saved_col)

        # Nothing matched — emit ILLEGAL and advance one char
        char = self.text[self.pos]
        self.pos += 1
        self.col += 1
        return Token(TokenType.ILLEGAL, char, saved_line, saved_col)
