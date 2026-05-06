"""
Visitors that operate on the AST.

1. ASTPrinter  — renders the tree as an indented string (for display).
2. Evaluator   — walks the tree and computes a numeric result.
"""

from __future__ import annotations

import math
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
# AST Pretty-Printer
# ---------------------------------------------------------------------------

class ASTPrinter:
    """
    Converts an AST into a human-readable tree string.

    Example output:
        BinaryOp '+'
        ├── Number(3)
        └── BinaryOp '*'
            ├── Number(4)
            └── Number(2)
    """

    def print(self, node: ASTNode, indent: str = "", is_last: bool = True) -> str:
        prefix      = indent + ("└── " if is_last else "├── ")
        child_indent = indent + ("    " if is_last else "│   ")

        lines: list[str] = []

        if isinstance(node, NumberNode):
            lines.append(f"{prefix}Number({node.raw})")

        elif isinstance(node, ConstantNode):
            lines.append(f"{prefix}Constant({node.name})")

        elif isinstance(node, IdentifierNode):
            lines.append(f"{prefix}Identifier({node.name})")

        elif isinstance(node, UnaryOpNode):
            lines.append(f"{prefix}UnaryOp('{node.operator}')")
            lines.append(self.print(node.operand, child_indent, is_last=True))

        elif isinstance(node, BinaryOpNode):
            lines.append(f"{prefix}BinaryOp('{node.operator}')")
            lines.append(self.print(node.left,  child_indent, is_last=False))
            lines.append(self.print(node.right, child_indent, is_last=True))

        elif isinstance(node, FunctionCallNode):
            lines.append(f"{prefix}FunctionCall('{node.name}')")
            for i, arg in enumerate(node.arguments):
                last = (i == len(node.arguments) - 1)
                lines.append(self.print(arg, child_indent, is_last=last))

        elif isinstance(node, AssignNode):
            lines.append(f"{prefix}Assign('{node.name}')")
            lines.append(self.print(node.value, child_indent, is_last=True))

        else:
            lines.append(f"{prefix}<Unknown node: {type(node).__name__}>")

        return "\n".join(lines)

    def render(self, node: ASTNode) -> str:
        """Return the full tree string (without the leading connector)."""
        # Use print() but strip the root prefix
        raw = self.print(node, indent="", is_last=True)
        # Remove "└── " from the very first line
        first, *rest = raw.split("\n")
        first = first.replace("└── ", "", 1).replace("├── ", "", 1)
        return "\n".join([first] + rest)


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class EvalError(Exception):
    pass


CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e":  math.e,
}

FUNCTIONS: dict[str, callable] = {
    "sin": math.sin,
    "cos": math.cos,
}

BINARY_OPS: dict[str, callable] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "^": lambda a, b: a ** b,
}


class Evaluator:
    """
    Walks an AST and evaluates it to a float.
    Supports variable storage for assignment nodes.
    """

    def __init__(self) -> None:
        self.env: dict[str, float] = {}

    def evaluate(self, node: ASTNode) -> float:
        return node.accept(self)

    # ------------------------------------------------------------------
    # Visitor methods
    # ------------------------------------------------------------------

    def visit_number(self, node: NumberNode) -> float:
        return float(node.value)

    def visit_constant(self, node: ConstantNode) -> float:
        try:
            return CONSTANTS[node.name]
        except KeyError:
            raise EvalError(f"Unknown constant: {node.name}")

    def visit_identifier(self, node: IdentifierNode) -> float:
        try:
            return self.env[node.name]
        except KeyError:
            raise EvalError(f"Undefined variable: {node.name}")

    def visit_unary_op(self, node: UnaryOpNode) -> float:
        val = self.evaluate(node.operand)
        if node.operator == "-":
            return -val
        return val  # unary "+"

    def visit_binary_op(self, node: BinaryOpNode) -> float:
        left  = self.evaluate(node.left)
        right = self.evaluate(node.right)
        try:
            return BINARY_OPS[node.operator](left, right)
        except ZeroDivisionError:
            raise EvalError("Division by zero")

    def visit_function_call(self, node: FunctionCallNode) -> float:
        fn = FUNCTIONS.get(node.name)
        if fn is None:
            raise EvalError(f"Unknown function: {node.name}")
        args = [self.evaluate(a) for a in node.arguments]
        return fn(*args)

    def visit_assign(self, node: AssignNode) -> float:
        val = self.evaluate(node.value)
        self.env[node.name] = val
        return val
