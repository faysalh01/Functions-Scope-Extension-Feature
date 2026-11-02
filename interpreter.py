# Onyx Interpreter and Environment
# Part 5 - Functions, Scope, and Arrays

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
)


class ReturnSignal(Exception):
    """Raised by `return` to unwind a function body. Caught only in visit_FunctionCallNode."""
    def __init__(self, value):
        self.value = value


class Environment:
    """Scope: each Environment may have a parent. Lookup walks up; declare is local."""
    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise RuntimeError(f"Runtime error: undefined variable '{name}'.")

    def declare(self, name, value):
        # Used by `let x = ...` and `def f(...)` — always writes to current scope.
        self.values[name] = value

    def assign(self, name, value):
        # Used by plain `x = ...` — updates the nearest existing binding.
        if name in self.values:
            self.values[name] = value
        elif self.parent is not None:
            self.parent.assign(name, value)
        else:
            raise RuntimeError(f"Runtime error: undefined variable '{name}'.")


class Interpreter:
    """Executes the Onyx AST."""

    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals
        self.output_buffer = []

    # ---------------------------------------------------------------- driver
    def interpret(self, node):
        self.output_buffer = []
        self.environment = self.globals
        try:
            self.visit(node)
        except ReturnSignal:
            raise RuntimeError("Runtime error: 'return' outside of a function.")
        return self.output_buffer

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.no_visit_method)
        return visitor(node)

    def no_visit_method(self, node):
        raise RuntimeError(
            f"No visit_{type(node).__name__} method defined for AST node."
        )

    # ------------------------------------------------------- Part 4 nodes
    def visit_ProgramNode(self, node):
        for statement in node.statements:
            self.visit(statement)

    def visit_NumberNode(self, node):
        return node.value

    def visit_VariableNode(self, node):
        return self.environment.get(node.name)

    def visit_BinaryOpNode(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        if node.operator == '+':
            return left_val + right_val
        elif node.operator == '-':
            return left_val - right_val
        elif node.operator == '*':
            return left_val * right_val
        elif node.operator == '/':
            if right_val == 0:
                raise RuntimeError("Runtime error: division by zero.")
            return left_val // int(right_val)
        elif node.operator == '==':
            return 1 if left_val == right_val else 0
        elif node.operator == '!=':
            return 1 if left_val != right_val else 0
        elif node.operator == '<':
            return 1 if left_val < right_val else 0
        elif node.operator == '>':
            return 1 if left_val > right_val else 0
        elif node.operator == '<=':
            return 1 if left_val <= right_val else 0
        elif node.operator == '>=':
            return 1 if left_val >= right_val else 0
        else:
            raise RuntimeError(f"Runtime error: unknown operator '{node.operator}'.")

    def visit_AssignmentNode(self, node):
        value = self.visit(node.expression)
        if node.declaration:
            self.environment.declare(node.variable.name, value)
        else:
            self.environment.assign(node.variable.name, value)

    def visit_PrintNode(self, node):
        value = self.visit(node.expression)
        self.output_buffer.append(str(value))
        print(value)

    def visit_IfNode(self, node):
        cond_val = self.visit(node.condition)
        if cond_val != 0:
            self.visit(node.if_body)
        elif node.else_body is not None:
            self.visit(node.else_body)

    def visit_WhileNode(self, node):
        while self.visit(node.condition) != 0:
            self.visit(node.body)

    # ------------------------------------------------------- Part 5 nodes
    def visit_FunctionDefNode(self, node):
        # Store the definition itself in the current scope. Calling it later
        # just looks this up.
        self.environment.declare(node.name, node)

    def visit_FunctionCallNode(self, node):
        callee = self.environment.get(node.name)
        if not isinstance(callee, FunctionDefNode):
            raise RuntimeError(
                f"Runtime error: '{node.name}' is not a function."
            )
        if len(node.arguments) != len(callee.parameters):
            raise RuntimeError(
                f"Runtime error: function '{node.name}' expects "
                f"{len(callee.parameters)} argument(s), got {len(node.arguments)}."
            )

        # Evaluate args in caller's scope BEFORE swapping environments.
        args = [self.visit(arg) for arg in node.arguments]

        # Local scope: parent is globals, not the caller. This is what gives
        # the required scope behavior (20 then 10) and free recursion.
        local_env = Environment(parent=self.globals)
        for param, value in zip(callee.parameters, args):
            local_env.declare(param, value)

        saved_env = self.environment
        self.environment = local_env
        try:
            self.visit(callee.body)
            result = None
        except ReturnSignal as signal:
            result = signal.value
        finally:
            self.environment = saved_env

        return result

    def visit_ReturnNode(self, node):
        raise ReturnSignal(self.visit(node.expression))

    def visit_ArrayNode(self, node):
        return [self.visit(elem) for elem in node.elements]

    def visit_ArrayIndexNode(self, node):
        array = self.environment.get(node.array_name)
        if not isinstance(array, list):
            raise RuntimeError(
                f"Runtime error: '{node.array_name}' is not an array."
            )
        index = self.visit(node.index_expr)
        if not isinstance(index, int):
            raise RuntimeError("Runtime error: array index must be an integer.")
        if index < 0 or index >= len(array):
            raise RuntimeError(
                f"Runtime error: array index {index} out of bounds "
                f"for array of length {len(array)}."
            )
        return array[index]

    def visit_ArrayIndexAssignmentNode(self, node):
        array = self.environment.get(node.array_name)
        if not isinstance(array, list):
            raise RuntimeError(
                f"Runtime error: '{node.array_name}' is not an array."
            )
        index = self.visit(node.index_expr)
        if not isinstance(index, int):
            raise RuntimeError("Runtime error: array index must be an integer.")
        if index < 0 or index >= len(array):
            raise RuntimeError(
                f"Runtime error: array index {index} out of bounds "
                f"for array of length {len(array)}."
            )
        array[index] = self.visit(node.expression)