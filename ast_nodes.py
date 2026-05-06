"""
Abstract Syntax Tree (AST) node definitions.

Every node inherits from ASTNode and implements the Visitor pattern
via an `accept(visitor)` method.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol


# ---------------------------------------------------------------------------
# Visitor protocol (for type-checking)
# ---------------------------------------------------------------------------

class ASTVisitor(Protocol):
    def visit_number(self, node: NumberNode): ...
    def visit_constant(self, node: ConstantNode): ...
    def visit_identifier(self, node: IdentifierNode): ...
    def visit_unary_op(self, node: UnaryOpNode): ...
    def visit_binary_op(self, node: BinaryOpNode): ...
    def visit_function_call(self, node: FunctionCallNode): ...
    def visit_assign(self, node: AssignNode): ...


# ---------------------------------------------------------------------------
# Base node
# ---------------------------------------------------------------------------

class ASTNode:
    """Base class for every node in the Abstract Syntax Tree."""

    def accept(self, visitor: ASTVisitor):
        raise NotImplementedError(
            f"{type(self).__name__} does not implement accept()"
        )


# ---------------------------------------------------------------------------
# Leaf nodes
# ---------------------------------------------------------------------------

@dataclass
class NumberNode(ASTNode):
    """
    An integer or floating-point literal.

    Examples: 42, 3.14
    """
    value: float   # Python numeric value
    raw:   str     # Original source text ("3.14")

    def accept(self, visitor):
        return visitor.visit_number(self)

    def __repr__(self) -> str:
        return f"Number({self.raw})"


@dataclass
class ConstantNode(ASTNode):
    """
    A named mathematical constant.

    Examples: pi, e
    """
    name: str   # "pi" | "e"

    def accept(self, visitor):
        return visitor.visit_constant(self)

    def __repr__(self) -> str:
        return f"Constant({self.name})"


@dataclass
class IdentifierNode(ASTNode):
    """
    A user-defined variable name.

    Example: x, result, my_var
    """
    name: str

    def accept(self, visitor):
        return visitor.visit_identifier(self)

    def __repr__(self) -> str:
        return f"Identifier({self.name})"


# ---------------------------------------------------------------------------
# Operator nodes
# ---------------------------------------------------------------------------

@dataclass
class UnaryOpNode(ASTNode):
    """
    A unary operator applied to a single operand.

    Example:  -3  →  UnaryOp('-', Number(3))
    """
    operator: str    # "-" | "+"
    operand:  ASTNode

    def accept(self, visitor):
        return visitor.visit_unary_op(self)

    def __repr__(self) -> str:
        return f"UnaryOp('{self.operator}', {self.operand})"


@dataclass
class BinaryOpNode(ASTNode):
    """
    A binary operator applied to two operands.

    Example:  3 + 4  →  BinaryOp('+', Number(3), Number(4))
    """
    operator: str     # "+", "-", "*", "/", "^"
    left:     ASTNode
    right:    ASTNode

    def accept(self, visitor):
        return visitor.visit_binary_op(self)

    def __repr__(self) -> str:
        return f"BinaryOp('{self.operator}', {self.left}, {self.right})"


# ---------------------------------------------------------------------------
# Function call node
# ---------------------------------------------------------------------------

@dataclass
class FunctionCallNode(ASTNode):
    """
    A call to a built-in function.

    Example:  sin(pi / 2)  →  FunctionCall('sin', [BinaryOp('/', Constant(pi), Number(2))])
    """
    name:      str            # "sin" | "cos"
    arguments: list[ASTNode] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_function_call(self)

    def __repr__(self) -> str:
        args = ", ".join(repr(a) for a in self.arguments)
        return f"FunctionCall('{self.name}', [{args}])"


# ---------------------------------------------------------------------------
# Assignment node
# ---------------------------------------------------------------------------

@dataclass
class AssignNode(ASTNode):
    """
    A variable assignment statement.

    Example:  x = 3 + 4  →  Assign('x', BinaryOp('+', Number(3), Number(4)))
    """
    name:  str     # variable name
    value: ASTNode # right-hand side expression

    def accept(self, visitor):
        return visitor.visit_assign(self)

    def __repr__(self) -> str:
        return f"Assign('{self.name}', {self.value})"
