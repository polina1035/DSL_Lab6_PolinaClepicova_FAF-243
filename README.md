# Laboratory Work Report: Parser & Abstract Syntax Tree

### Course: Formal Languages & Finite Automata
### Author: Clepicova Polina FAF-243

---

## Topic: Parser & Building an Abstract Syntax Tree

---

## Objectives

1. Get familiar with parsing and how it can be programmed
2. Get familiar with the concept of an Abstract Syntax Tree (AST)
3. Extend the lexer from Lab 3 with a proper `TokenType` enum and regex-based token matching
4. Implement AST node data structures suitable for the mathematical expression language
5. Implement a recursive-descent parser that converts a token stream into an AST

---

## Theoretical Background

**Parsing** (syntactic analysis) is the process of analysing a sequence of tokens to determine its grammatical structure according to a formal grammar. It is the second phase of a typical compiler pipeline, following lexical analysis.

Key concepts:

* **Parse tree** — a concrete tree that shows every grammar rule applied during parsing, including all terminals and non-terminals.
* **Abstract Syntax Tree (AST)** — a simplified, hierarchical representation of the source code. Unlike a parse tree it discards redundant syntactic details (parentheses, commas, keywords that carry no semantic information) and retains only the structural relationships needed by later compiler phases.
* **Recursive-descent parser** — a top-down parser where each non-terminal in the grammar is implemented as a function that calls other functions for its sub-rules. It is simple to write by hand and easy to extend.
* **Operator precedence** — the grammar must encode the conventional precedence of operators (e.g. `*` before `+`) through the nesting of grammar rules.
* **Associativity** — left-associative operators (`+`, `-`, `*`, `/`) are handled by a `while` loop in the parsing function; right-associative operators (`^`) are handled by a recursive call.
* **Visitor pattern** — a design pattern that separates an algorithm (e.g. evaluation, pretty-printing) from the data structure it operates on (the AST nodes).

### Grammar used in this implementation

```
program        →  expression EOF
expression     →  IDENT "=" expression     (assignment, right-assoc)
               |  additive
additive       →  multiplicative ( ("+" | "-") multiplicative )*
multiplicative →  power ( ("*" | "/") power )*
power          →  unary ( "^" power )?     (right-associative)
unary          →  ("-" | "+") unary | primary
primary        →  INT | FLOAT | PI | E
               |  function_call
               |  IDENT
               |  "(" expression ")"
function_call  →  (SIN | COS) "(" arglist ")"
arglist        →  expression ("," expression)*
```

---

## Implementation

The project is split into four source files inside `src/`:

| File | Responsibility |
|---|---|
| `lexer.py` | `TokenType` enum, `Token` dataclass, regex-based `Lexer` |
| `ast_nodes.py` | All AST node classes |
| `parser.py` | Recursive-descent `Parser` |
| `visitors.py` | `ASTPrinter` and `Evaluator` visitors |

### 1. TokenType Enum and Regex Lexer

The previous lab's lexer was rewritten to use a `TokenType` enum and a list of compiled `re.Pattern` objects, matching one token at a time from the current position.

```python
class TokenType(Enum):
    INT = "INT";   FLOAT = "FLOAT"
    PLUS = "PLUS"; MINUS = "MINUS"; MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"; POWER = "POWER"; ASSIGN = "ASSIGN"
    SIN = "SIN";   COS = "COS"
    PI = "PI";     E = "E"
    LPAREN = "LPAREN"; RPAREN = "RPAREN"; COMMA = "COMMA"
    IDENT = "IDENT"; EOF = "EOF"; ILLEGAL = "ILLEGAL"

TOKEN_PATTERNS = [
    (TokenType.FLOAT,    re.compile(r"\d+\.\d+")),   # must come before INT
    (TokenType.INT,      re.compile(r"\d+")),
    (TokenType.PLUS,     re.compile(r"\+")),
    ...
    (TokenType.IDENT,    re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")),
]
```

After matching an `IDENT`, the lexer checks a `KEYWORDS` dictionary to promote `sin`, `cos`, `pi`, and `e` to their dedicated token types.

### 2. AST Node Hierarchy

Each node class is a `@dataclass` that inherits from `ASTNode` and implements `accept(visitor)`:

| Node class | Represents | Example |
|---|---|---|
| `NumberNode` | Integer or float literal | `42`, `3.14` |
| `ConstantNode` | Named constant | `pi`, `e` |
| `IdentifierNode` | User-defined variable | `x`, `result` |
| `UnaryOpNode` | Unary operator | `-x` |
| `BinaryOpNode` | Binary operator | `a + b`, `x ^ 2` |
| `FunctionCallNode` | Built-in function call | `sin(pi/2)` |
| `AssignNode` | Variable assignment | `x = 3 + 4` |

### 3. Recursive-Descent Parser

The parser consumes the token list produced by the lexer and builds an AST bottom-up through mutual recursion. Each grammar rule maps to exactly one method:

| Method | Grammar rule |
|---|---|
| `_parse_expression()` | assignment or additive |
| `_parse_additive()` | handles `+` and `-` (left-assoc, lowest precedence) |
| `_parse_multiplicative()` | handles `*` and `/` (left-assoc) |
| `_parse_power()` | handles `^` (right-assoc via recursive call) |
| `_parse_unary()` | handles unary `-` and `+` |
| `_parse_primary()` | literals, constants, identifiers, parentheses |
| `_parse_function_call()` | `sin(…)` / `cos(…)` with argument list |

**Right-associativity for exponentiation** is achieved naturally by making `_parse_power` call itself recursively for the exponent rather than looping:

```python
def _parse_power(self) -> ASTNode:
    base = self._parse_unary()
    if self.match(TokenType.POWER):
        op       = self.consume().value
        exponent = self._parse_power()   # recursive → right-associative
        return BinaryOpNode(op, base, exponent)
    return base
```

### 4. Visitors

Two visitors are implemented in `visitors.py`:

**`ASTPrinter`** — renders the tree using Unicode box-drawing characters for clear hierarchical display.

**`Evaluator`** — traverses the AST and computes the numeric result. It maintains an `env` dictionary so that values assigned to variables can be referenced in later expressions.

---

## Testing Results

### Test 1: Simple Arithmetic — `"3 + 4 * 2"`

```
Tokens:
  Token(INT        '3'   line=1, col=1)
  Token(PLUS       '+'   line=1, col=3)
  Token(INT        '4'   line=1, col=5)
  Token(MULTIPLY   '*'   line=1, col=7)
  Token(INT        '2'   line=1, col=9)
  Token(EOF        ''    line=1, col=10)

Abstract Syntax Tree:
  BinaryOp('+')
      ├── Number(3)
      └── BinaryOp('*')
          ├── Number(4)
          └── Number(2)

Evaluated result: 11.0
```

The AST correctly places `*` deeper than `+`, demonstrating that operator precedence is encoded in the grammar.

---

### Test 2: Trigonometric Expression — `"sin(pi / 2) + cos(0)"`

```
Abstract Syntax Tree:
  BinaryOp('+')
      ├── FunctionCall('sin')
      │   └── BinaryOp('/')
      │       ├── Constant(pi)
      │       └── Number(2)
      └── FunctionCall('cos')
          └── Number(0)

Evaluated result: 2.0
```

Function calls become `FunctionCallNode` with their argument sub-trees. The result `sin(π/2) + cos(0) = 1 + 1 = 2` is correct.

---

### Test 3: Floating-Point Numbers — `"3.14 * 2.5 ^ 2"`

```
Abstract Syntax Tree:
  BinaryOp('*')
      ├── Number(3.14)
      └── BinaryOp('^')
          ├── Number(2.5)
          └── Number(2)

Evaluated result: 19.625
```

`^` has higher precedence than `*`, which is reflected in the tree structure.

---

### Test 4: Complex Expression — `"sin(pi * 0.5) + cos(pi) - 3.14"`

```
Abstract Syntax Tree:
  BinaryOp('-')
      ├── BinaryOp('+')
      │   ├── FunctionCall('sin')
      │   │   └── BinaryOp('*')
      │   │       ├── Constant(pi)
      │   │       └── Number(0.5)
      │   └── FunctionCall('cos')
      │       └── Constant(pi)
      └── Number(3.14)

Evaluated result: -3.14
```

`sin(π · 0.5) = 1`, `cos(π) = -1`, so `1 + (−1) − 3.14 = −3.14`. ✓

---

### Test 5: Variable Assignment — `"x = 3 + 4"`

```
Abstract Syntax Tree:
  Assign('x')
      └── BinaryOp('+')
          ├── Number(3)
          └── Number(4)

Evaluated result: 7.0
```

The evaluator stores `x = 7` in its environment dictionary.

---

### Test 6: Right-Associative Exponentiation — `"2 ^ 3 ^ 2"`

```
Abstract Syntax Tree:
  BinaryOp('^')
      ├── Number(2)
      └── BinaryOp('^')
          ├── Number(3)
          └── Number(2)

Evaluated result: 512.0
```

`2 ^ (3 ^ 2) = 2^9 = 512`, not `(2^3)^2 = 64`. Right-associativity is working correctly.

---

### Test 7: Unary Minus — `"-sin(pi / 6)"`

```
Abstract Syntax Tree:
  UnaryOp('-')
      └── FunctionCall('sin')
          └── BinaryOp('/')
              ├── Constant(pi)
              └── Number(6)

Evaluated result: -0.5
```

---

### Test 8: Variable Reuse — `"x * 2"` (after Test 5)

```
Abstract Syntax Tree:
  BinaryOp('*')
      ├── Identifier(x)
      └── Number(2)

Evaluated result: 14.0
```

The evaluator correctly looks up `x = 7` from the environment and computes `7 * 2 = 14`.

---

## Difficulties Encountered

* **Operator precedence encoding** — Getting the grammar layering right (additive → multiplicative → power → unary → primary) required careful planning. A wrong order makes expressions like `3 + 4 * 2` parse as `(3 + 4) * 2`.

* **Right-associativity of `^`** — Most operators are left-associative and handled with a `while` loop. Exponentiation required switching to a recursive call, which was a conceptual shift.

* **Assignment look-ahead** — Distinguishing `x = expr` (assignment) from `x` as a plain identifier required a one-token look-ahead: checking that the *next* token is `=` before committing to the assignment rule.

* **Visitor pattern wiring** — Each new node class required a corresponding `visit_*` method in every visitor. Forgetting one causes a `NotImplementedError` at runtime rather than at compile time in Python, so tests were essential.

* **Unary `+` handling** — Unary plus is syntactically valid (`+3`, `+sin(x)`) but semantically a no-op; silently consuming it without creating a `UnaryOpNode` kept the AST clean.

---

## Conclusions

In this laboratory work:

* The lexer from Lab 3 was upgraded with a `TokenType` enum and regex-based pattern matching, making it more robust and easier to extend
* A complete set of AST node classes was designed using Python dataclasses and the Visitor pattern
* A recursive-descent parser was implemented that correctly handles operator precedence (additive < multiplicative < power < unary), right-associativity for exponentiation, unary operators, function calls, parenthesised sub-expressions, and variable assignment
* Two visitors were implemented: an `ASTPrinter` for human-readable tree display, and an `Evaluator` that computes numeric results while maintaining a variable environment
* All nine test cases produced correct parse trees and evaluated values

The parser can be naturally extended to support:

* Additional functions (`tan`, `log`, `sqrt`, `abs`)
* Boolean operators and comparisons
* Multi-statement programs (newline or `;` separated)
* A type-checker visitor that validates expression types before evaluation
* A code-generator visitor that emits bytecode or target assembly

---

## References

1. [Parsing — Wikipedia](https://en.wikipedia.org/wiki/Parsing)
2. [Abstract Syntax Tree — Wikipedia](https://en.wikipedia.org/wiki/Abstract_syntax_tree)
3. [Crafting Interpreters — Parsing Expressions](https://craftinginterpreters.com/parsing-expressions.html)
4. [Recursive Descent Parsing — Eli Bendersky's website](https://eli.thegreenplace.net/2008/09/26/recursive-descent-combinator-in-python)

---

## Appendix: AST Node Summary

| Node class | Fields | Description |
|---|---|---|
| `NumberNode` | `value`, `raw` | Integer or float literal |
| `ConstantNode` | `name` | Named constant (`pi`, `e`) |
| `IdentifierNode` | `name` | User-defined variable |
| `UnaryOpNode` | `operator`, `operand` | Unary `-` or `+` |
| `BinaryOpNode` | `operator`, `left`, `right` | `+`, `-`, `*`, `/`, `^` |
| `FunctionCallNode` | `name`, `arguments` | `sin(…)`, `cos(…)` |
| `AssignNode` | `name`, `value` | Variable assignment |
