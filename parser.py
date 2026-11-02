"""
Onyx Parser
Part 5 - Functions, Scope, and Arrays

Person A's Part 5 contribution:
- `def` function definitions with parameter lists
- `return` statements
- function calls (both as expressions and as bare statements)
- array literals, index reads, and index assignments
- one-token lookahead to disambiguate ID-started statements
  (x = ..., a[i] = ..., f(...); )
"""

from lexer import Lexer, LexerError
from ast_nodes import (
    ProgramNode,
    NumberNode,
    VariableNode,
    BinaryOpNode,
    AssignmentNode,
    PrintNode,
    IfNode,
    WhileNode,
    FunctionDefNode,
    FunctionCallNode,
    ReturnNode,
    ArrayNode,
    ArrayIndexNode,
    ArrayIndexAssignmentNode,
    print_ast,
)


class ParserError(Exception):
    """Raised when Onyx source contains invalid syntax."""

    def __init__(self, message, position=None, token=None):
        self.position = position
        self.token = token
        if position is not None:
            message = f"Syntax error at token {position}: {message}"
        super().__init__(message)


class Parser:
    """Recursive-descent parser for the Part 5 Onyx grammar."""

    OPERATOR_SYMBOLS = {
        "PLUS": "+",
        "MINUS": "-",
        "MULTIPLY": "*",
        "DIVIDE": "/",
    }

    COMPARISON_SYMBOLS = {
        "EQUAL_EQUAL": "==",
        "NOT_EQUAL": "!=",
        "LESS_THAN": "<",
        "GREATER_THAN": ">",
        "LESS_EQUAL": "<=",
        "GREATER_EQUAL": ">=",
    }

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    # ------------------------------------------------------------------ helpers
    def is_at_end(self):
        return self.position >= len(self.tokens)

    def current(self):
        return None if self.is_at_end() else self.tokens[self.position]

    def peek(self, offset=1):
        idx = self.position + offset
        if idx >= len(self.tokens):
            return None
        return self.tokens[idx]

    def advance(self):
        token = self.current()
        if not self.is_at_end():
            self.position += 1
        return token

    def check(self, token_type):
        token = self.current()
        return token is not None and token.token_type == token_type

    def match(self, *token_types):
        if self.current() is not None and self.current().token_type in token_types:
            return self.advance()
        return None

    @staticmethod
    def describe_token(token):
        if token is None:
            return "end of input"
        if token.value is not None:
            return f"{token.token_type}({token.value})"
        return token.token_type

    def expect(self, token_type, description=None):
        token = self.current()
        expected = description or token_type

        if token is None:
            raise ParserError(
                f"expected {expected}, but reached end of input.",
                self.position,
            )

        if token.token_type != token_type:
            raise ParserError(
                f"expected {expected}, found {self.describe_token(token)}.",
                self.position,
                token,
            )

        return self.advance()

    # ---------------------------------------------------------------- top-level
    def parse(self):
        """Parse the entire token stream and require complete consumption."""
        program = self.parse_program()
        if not self.is_at_end():
            token = self.current()
            raise ParserError(
                f"unexpected {self.describe_token(token)} after complete statement.",
                self.position,
                token,
            )
        return program

    def parse_program(self):
        """program ::= { statement }"""
        statements = []
        while not self.is_at_end():
            statements.append(self.parse_statement())
        return ProgramNode(statements)

    def parse_block(self):
        """Parse statements inside { ... } until '}'."""
        statements = []
        while not self.is_at_end() and not self.check("RBRACE"):
            statements.append(self.parse_statement())
        return ProgramNode(statements)

    # --------------------------------------------------------------- statements
    def parse_statement(self):
        if self.check("LET"):
            return self.parse_assignment(declaration=True)
        if self.check("PRINT"):
            return self.parse_print()
        if self.check("IF"):
            return self.parse_if()
        if self.check("WHILE"):
            return self.parse_while()
        if self.check("DEF"):
            return self.parse_function_def()
        if self.check("RETURN"):
            return self.parse_return()
        if self.check("ID"):
            return self.parse_id_statement()

        token = self.current()
        raise ParserError(
            "expected a statement (LET, PRINT, IF, WHILE, DEF, RETURN, "
            f"or identifier); found {self.describe_token(token)}.",
            self.position,
            token,
        )

    def parse_id_statement(self):
        """
        Disambiguate an ID-started statement by looking at the NEXT token:

            ID = expr ;              -> AssignmentNode(declaration=False)
            ID [ expr ] = expr ;     -> ArrayIndexAssignmentNode
            ID ( args ) ;            -> FunctionCallNode (bare statement)

        This is the one place where Part 4's "assume assignment" no longer works.
        """
        next_token = self.peek()
        if next_token is None:
            raise ParserError(
                "unexpected end of input after identifier.",
                self.position,
            )

        if next_token.token_type == "ASSIGN":
            return self.parse_assignment(declaration=False)

        if next_token.token_type == "LBRACKET":
            return self.parse_index_assignment()

        if next_token.token_type == "LPAREN":
            call = self.parse_call()
            self.expect("SEMICOLON", "';'")
            return call

        raise ParserError(
            "expected '=', '[', or '(' after identifier; "
            f"found {self.describe_token(next_token)}.",
            self.position,
            next_token,
        )

    def parse_assignment(self, declaration):
        """assignment ::= "let" identifier "=" expr ";" | identifier "=" expr ";" """
        if declaration:
            self.expect("LET", "'let'")

        name_token = self.expect("ID", "an identifier")
        self.expect("ASSIGN", "'='")
        expression = self.parse_expression()
        self.expect("SEMICOLON", "';'")

        return AssignmentNode(
            VariableNode(name_token.value),
            expression,
            declaration=declaration,
        )

    def parse_index_assignment(self):
        """identifier "[" expression "]" "=" expression ";" """
        name_token = self.expect("ID", "array name")
        self.expect("LBRACKET", "'['")
        index_expr = self.parse_expression()
        self.expect("RBRACKET", "']'")
        self.expect("ASSIGN", "'='")
        expression = self.parse_expression()
        self.expect("SEMICOLON", "';'")

        return ArrayIndexAssignmentNode(name_token.value, index_expr, expression)

    def parse_print(self):
        self.expect("PRINT", "'print'")
        self.expect("LPAREN", "'('")
        expression = self.parse_expression()
        self.expect("RPAREN", "')'")
        self.expect("SEMICOLON", "';'")
        return PrintNode(expression)

    def parse_if(self):
        self.expect("IF", "'if'")
        self.expect("LPAREN", "'('")
        condition = self.parse_expression()
        self.expect("RPAREN", "')'")

        self.expect("LBRACE", "'{'")
        if_body = self.parse_block()
        self.expect("RBRACE", "'}'")

        else_body = None
        if self.check("ELSE"):
            self.advance()
            self.expect("LBRACE", "'{'")
            else_body = self.parse_block()
            self.expect("RBRACE", "'}'")

        return IfNode(condition, if_body, else_body)

    def parse_while(self):
        self.expect("WHILE", "'while'")
        self.expect("LPAREN", "'('")
        condition = self.parse_expression()
        self.expect("RPAREN", "')'")

        self.expect("LBRACE", "'{'")
        body = self.parse_block()
        self.expect("RBRACE", "'}'")

        return WhileNode(condition, body)

    def parse_function_def(self):
        """def identifier ( [ parameter-list ] ) { program }"""
        self.expect("DEF", "'def'")
        name_token = self.expect("ID", "function name")
        self.expect("LPAREN", "'('")
        parameters = self.parse_parameter_list()
        self.expect("RPAREN", "')'")
        self.expect("LBRACE", "'{'")
        body = self.parse_block()
        self.expect("RBRACE", "'}'")
        return FunctionDefNode(name_token.value, parameters, body)

    def parse_parameter_list(self):
        """parameter-list ::= identifier { "," identifier } | ε"""
        parameters = []
        if self.check("ID"):
            parameters.append(self.advance().value)
            while self.match("COMMA"):
                name = self.expect("ID", "parameter name")
                parameters.append(name.value)
        return parameters

    def parse_return(self):
        self.expect("RETURN", "'return'")
        expression = self.parse_expression()
        self.expect("SEMICOLON", "';'")
        return ReturnNode(expression)

    # --------------------------------------------------------------- expressions
    def parse_expression(self):
        """expression ::= arithmetic-expr [ comparison-operator arithmetic-expr ]"""
        node = self.parse_arithmetic()

        comparison_tokens = list(self.COMPARISON_SYMBOLS.keys())
        operator = self.match(*comparison_tokens)
        if operator is not None:
            right = self.parse_arithmetic()
            node = BinaryOpNode(
                self.COMPARISON_SYMBOLS[operator.token_type],
                node,
                right,
            )
        return node

    def parse_arithmetic(self):
        node = self.parse_term()
        while True:
            operator = self.match("PLUS", "MINUS")
            if operator is None:
                break
            right = self.parse_term()
            node = BinaryOpNode(
                self.OPERATOR_SYMBOLS[operator.token_type],
                node,
                right,
            )
        return node

    def parse_term(self):
        node = self.parse_factor()
        while True:
            operator = self.match("MULTIPLY", "DIVIDE")
            if operator is None:
                break
            right = self.parse_factor()
            node = BinaryOpNode(
                self.OPERATOR_SYMBOLS[operator.token_type],
                node,
                right,
            )
        return node

    def parse_factor(self):
        """
        factor ::= number
                 | "[" [ argument-list ] "]"          (array literal)
                 | "(" expression ")"
                 | identifier "(" [ argument-list ] ")" (call)
                 | identifier "[" expression "]"       (index read)
                 | identifier
        """
        token = self.current()

        if token is None:
            raise ParserError(
                "expected a number, array, function call, index, variable, "
                "or parenthesized expression; reached end of input.",
                self.position,
            )

        if token.token_type == "NUMBER":
            self.advance()
            return NumberNode(token.value)

        if token.token_type == "LBRACKET":
            return self.parse_array()

        if token.token_type == "LPAREN":
            self.advance()
            expression = self.parse_expression()
            self.expect("RPAREN", "')'")
            return expression

        if token.token_type == "ID":
            next_token = self.peek()
            if next_token is not None and next_token.token_type == "LPAREN":
                return self.parse_call()
            if next_token is not None and next_token.token_type == "LBRACKET":
                return self.parse_index()
            self.advance()
            return VariableNode(token.value)

        raise ParserError(
            "expected a number, array, function call, index, variable, "
            f"or parenthesized expression; found {self.describe_token(token)}.",
            self.position,
            token,
        )

    def parse_call(self):
        """identifier "(" [ argument-list ] ")" """
        name_token = self.expect("ID", "function name")
        self.expect("LPAREN", "'('")
        arguments = self.parse_argument_list("RPAREN")
        self.expect("RPAREN", "')'")
        return FunctionCallNode(name_token.value, arguments)

    def parse_index(self):
        """identifier "[" expression "]" """
        name_token = self.expect("ID", "array name")
        self.expect("LBRACKET", "'['")
        index_expr = self.parse_expression()
        self.expect("RBRACKET", "']'")
        return ArrayIndexNode(name_token.value, index_expr)

    def parse_array(self):
        """array ::= "[" [ argument-list ] "]" """
        self.expect("LBRACKET", "'['")
        elements = self.parse_argument_list("RBRACKET")
        self.expect("RBRACKET", "']'")
        return ArrayNode(elements)

    def parse_argument_list(self, closing_token_type):
        """argument-list ::= expression { "," expression } | ε"""
        arguments = []
        if not self.check(closing_token_type):
            arguments.append(self.parse_expression())
            while self.match("COMMA"):
                arguments.append(self.parse_expression())
        return arguments


def parse_source(source):
    """Lex and parse one complete Onyx source string."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


# --------------------------------------------------------------- local smoke test
if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        # Parse-only mode: verify every .txt in the directory parses cleanly.
        # Usage: python parser.py tests
        test_dir = sys.argv[1]
        any_fail = False
        for file_name in sorted(os.listdir(test_dir)):
            if not file_name.endswith(".txt"):
                continue
            path = os.path.join(test_dir, file_name)
            print(f"\n--- Parsing {file_name} ---")
            try:
                with open(path) as f:
                    source = f.read()
                tree = parse_source(source)
                print(f"OK: parsed {len(tree.statements)} top-level statement(s)")
            except (LexerError, ParserError) as error:
                any_fail = True
                print(f"FAIL: {error}")
        sys.exit(1 if any_fail else 0)

    example = (
        "def add(a, b) {\n"
        "    return a + b;\n"
        "}\n"
        "let xs = [1, 2, 3];\n"
        "xs[0] = 10;\n"
        "print(add(xs[0], 20));\n"
    )
    print("Source:\n" + example)
    try:
        tree = parse_source(example)
        print_ast(tree)
    except (LexerError, ParserError) as error:
        print(error)