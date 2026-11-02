# Onyx Programming Language — Part 5 (Functions, Scope & Arrays)

## Overview
This is the complete Onyx interpreter for Part 5. It builds on the Part 4
control-structure interpreter and adds:

- **Functions** (`def`, parameters, `return`, calls as expressions and as statements)
- **Scope** — separate global and local (per-call) variable environments
- **Extension feature: Arrays** — literals, index reads, index assignment

## Architecture

| File | Purpose |
|---|---|
| `lexer.py` | Tokenizes source into tokens |
| `parser.py` | Recursive-descent parser → AST |
| `ast_nodes.py` | AST node classes |
| `interpreter.py` | Tree-walking interpreter with scoped environments |
| `run_tests.py` | Runs all test files in `tests/` |
| `GRAMMAR.md` | Full EBNF grammar for Part 5 |
| `tests/` | Part 4 regression tests + 5 Part 5 tests |

## Functions

```onyx
def add(a, b) {
    return a + b;
}
let result = add(10, 20);
print(result);      // 30
```

Functions can be called as expressions (`let x = add(1, 2);`) or as bare
statements (`add(1, 2);`). Recursion works:

```onyx
def fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
print(fact(5));     // 120
```

## Scope

Each `Environment` holds a `values` dict and an optional `parent` pointer.

- **Global scope** is one `Environment` created at interpreter startup.
- **Each function call** creates a fresh `Environment` whose parent is the
  **global** scope (not the caller's scope). So functions see globals and their
  own locals/parameters, but never the caller's locals.
- `let x = ...` calls `declare`, which writes to the *current* scope.
- Plain `x = ...` calls `assign`, which walks up parent links to update the
  nearest existing binding.
- Variable lookup (`get`) checks the current scope first, then walks up
  parents to globals.

Behavior this produces:

```onyx
let x = 10;
def test() {
    let x = 20;
    print(x);       // 20 — the local x shadows global x
}
test();
print(x);           // 10 — global x unaffected
```

## Extension: Arrays

```onyx
let a = [10, 20, 30];
print(a[0]);        // 10
print(a[2]);        // 30
a[1] = 99;
print(a[1]);        // 99
```

- Arrays are zero-indexed.
- Out-of-range access raises a runtime error.
- Indexing a non-array raises a runtime error.

## Running

```bash
python run_tests.py
```

Executes every `.txt` file in `tests/` through the full pipeline
(lex → parse → interpret) and prints the output buffer for each.

## Test files

Part 4 regression:
- `test_arithmetic.txt` → `['60']`
- `test_comparisons.txt` → `['1', '1', '0']`
- `test_conditional.txt` → `['0']`
- `test_error.txt` → `RuntimeError: division by zero`
- `test_loop.txt` → `['15']`

Part 5 new tests:
- `test_function_def_parse.txt` → `['30']`
- `test_functions.txt` → `['30']`
- `test_scope.txt` → `['20', '10']`
- `test_array_literal_parse.txt` → `['10', '30']`
- `test_index_assignment_parse.txt` → `['99']`
