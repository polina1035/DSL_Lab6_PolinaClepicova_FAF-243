"""
Main demonstration script for the Parser & AST lab.

Runs all test cases, prints tokens, AST trees, and evaluated results.
"""

import sys
import os

# Make src/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lexer    import Lexer
from parser   import Parser, ParseError, parse
from visitors import ASTPrinter, Evaluator, EvalError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEPARATOR = "─" * 60

def section(title: str) -> None:
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print('═' * 60)

def run_test(label: str, source: str, evaluator: Evaluator | None = None) -> None:
    print(f"\n{SEPARATOR}")
    print(f"Test: {label}")
    print(f"Input: {repr(source)}")
    print(SEPARATOR)

    # --- Lexer ---
    tokens = Lexer(source).tokenize()
    print("\nTokens:")
    for tok in tokens:
        print(f"  {tok}")

    # --- Parser ---
    try:
        ast = Parser(tokens).parse()
    except ParseError as e:
        print(f"\n[ParseError] {e}")
        return

    # --- AST ---
    printer = ASTPrinter()
    print("\nAbstract Syntax Tree:")
    for line in printer.render(ast).splitlines():
        print(f"  {line}")

    # --- Evaluator ---
    if evaluator is not None:
        try:
            result = evaluator.evaluate(ast)
            print(f"\nEvaluated result: {result}")
        except EvalError as e:
            print(f"\n[EvalError] {e}")


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def main() -> None:
    ev = Evaluator()

    section("Lab 6 — Parser & AST Demo")

    run_test("Simple arithmetic",          "3 + 4 * 2",             ev)
    run_test("Trigonometric expression",   "sin(pi / 2) + cos(0)",  ev)
    run_test("Floating-point numbers",     "3.14 * 2.5 ^ 2",        ev)
    run_test("Complex expression",         "sin(pi * 0.5) + cos(pi) - 3.14", ev)
    run_test("Constants arithmetic",       "2 * pi * e",            ev)
    run_test("Variable assignment",        "x = 3 + 4",             ev)
    run_test("Nested power (right-assoc)", "2 ^ 3 ^ 2",             ev)   # = 2^(3^2) = 512
    run_test("Unary minus",               "-sin(pi / 6)",           ev)
    run_test("Reuse variable",            "x * 2",                  ev)   # x was set to 7 above


if __name__ == "__main__":
    main()
