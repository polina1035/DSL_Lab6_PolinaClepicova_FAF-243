"""
Recursive-descent parser for mathematical expressions.

Grammar (in pseudo-BNF, highest precedence last):

    program      →  expression EOF
    expression   →  assignment | additive
    assignment   →  IDENT "=" expression
    additive     →  multiplicative ( ("+" | "-") multiplicative )*
    multiplicative → power ( ("*" | "/") power )*
    power        →  unary ( "^" power )?          # right-associative
    unary        →  ("-" | "+") unary | primary
    primary      →  NUMBER | FLOAT | PI | E
                  | function_call
                  | IDENT
                  | "(" expression ")"
    function_call → (SIN | COS) "(" arglist ")"
    arglist      →  expression ("," expression)*
"""

from __future__ import annotations

from lexer    import Lexer, Token, TokenType
from ast_nodes import (
    ASTNode,
    AssignNode,
    BinaryOpNode,
    ConstantNode,
    FunctionCallNode,
    IdentifierNode,
    NumberNode,
    UnaryOpNode,
)


# ---------------------------------------------------------------------------
# Parse error
# ---------------------------------------------------------------------------

class ParseError(Exception):
    def __init__(self, message: str, token: Token) -> None:
        self.token = token
        super().__init__(
            f"ParseError at line {token.line}, col {token.col}: "
            f"{message} (got {token.type.value} {repr(token.value)})"
        )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    """
    Transforms a flat token list produced by Lexer into an AST.

    Usage:
        tokens = Lexer("3 + 4 * 2").tokenize()
        ast    = Parser(tokens).parse()
    """

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos    = 0

    # ------------------------------------------------------------------
    # Token navigation helpers
    # ------------------------------------------------------------------

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def consume(self, expected: TokenType | None = None) -> Token:
        """Return current token and advance. Raises ParseError on mismatch."""
        token = self.current
        if expected is not None and token.type != expected:
            raise ParseError(
                f"expected {expected.value}", token
            )
        self.pos += 1
        return token

    def match(self, *types: TokenType) -> bool:
        return self.current.type in types

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self) -> ASTNode:
        """Parse a complete expression and assert EOF."""
        node = self._parse_expression()
        if self.current.type != TokenType.EOF:
            raise ParseError("unexpected token after expression", self.current)
        return node

    # ------------------------------------------------------------------
    # Grammar rules
    # ------------------------------------------------------------------

    def _parse_expression(self) -> ASTNode:
        """
        expression  →  IDENT "=" expression   (assignment)
                     | additive
        """
        # Look-ahead: IDENT followed by ASSIGN → assignment
        if (self.current.type == TokenType.IDENT
                and self.peek().type == TokenType.ASSIGN):
            name_token = self.consume()          # IDENT
            self.consume(TokenType.ASSIGN)       # =
            value = self._parse_expression()     # right-hand side (recursive)
            return AssignNode(name=name_token.value, value=value)

        return self._parse_additive()

    def _parse_additive(self) -> ASTNode:
        """
        additive  →  multiplicative ( ("+" | "-") multiplicative )*
        """
        left = self._parse_multiplicative()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op    = self.consume().value
            right = self._parse_multiplicative()
            left  = BinaryOpNode(operator=op, left=left, right=right)
        return left

    def _parse_multiplicative(self) -> ASTNode:
        """
        multiplicative  →  power ( ("*" | "/") power )*
        """
        left = self._parse_power()
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE):
            op    = self.consume().value
            right = self._parse_power()
            left  = BinaryOpNode(operator=op, left=left, right=right)
        return left

    def _parse_power(self) -> ASTNode:
        """
        power  →  unary ( "^" power )?    # right-associative
        """
        base = self._parse_unary()
        if self.match(TokenType.POWER):
            op       = self.consume().value
            exponent = self._parse_power()   # recursive call → right-assoc
            return BinaryOpNode(operator=op, left=base, right=exponent)
        return base

    def _parse_unary(self) -> ASTNode:
        """
        unary  →  ("-" | "+") unary | primary
        """
        if self.match(TokenType.MINUS):
            op      = self.consume().value
            operand = self._parse_unary()
            return UnaryOpNode(operator=op, operand=operand)
        if self.match(TokenType.PLUS):
            self.consume()           # unary "+" is a no-op, skip it
            return self._parse_unary()
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        """
        primary  →  INT | FLOAT | PI | E | function_call | IDENT | "(" expression ")"
        """
        token = self.current

        # Integer literal
        if token.type == TokenType.INT:
            self.consume()
            return NumberNode(value=int(token.value), raw=token.value)

        # Float literal
        if token.type == TokenType.FLOAT:
            self.consume()
            return NumberNode(value=float(token.value), raw=token.value)

        # Named constants
        if token.type == TokenType.PI:
            self.consume()
            return ConstantNode(name="pi")

        if token.type == TokenType.E:
            self.consume()
            return ConstantNode(name="e")

        # Built-in function call
        if token.type in (TokenType.SIN, TokenType.COS):
            return self._parse_function_call()

        # Generic identifier (variable)
        if token.type == TokenType.IDENT:
            self.consume()
            return IdentifierNode(name=token.value)

        # Parenthesised sub-expression
        if token.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            node = self._parse_expression()
            self.consume(TokenType.RPAREN)
            return node

        raise ParseError("unexpected token in primary expression", token)

    def _parse_function_call(self) -> FunctionCallNode:
        """
        function_call  →  (SIN | COS) "(" arglist ")"
        arglist        →  expression ("," expression)*
        """
        name_token = self.consume()                 # SIN | COS
        self.consume(TokenType.LPAREN)

        args: list[ASTNode] = []
        if not self.match(TokenType.RPAREN):        # non-empty argument list
            args.append(self._parse_expression())
            while self.match(TokenType.COMMA):
                self.consume()
                args.append(self._parse_expression())

        self.consume(TokenType.RPAREN)
        return FunctionCallNode(name=name_token.value, arguments=args)


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def parse(source: str) -> ASTNode:
    """Lex and parse *source*, returning the root ASTNode."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()
