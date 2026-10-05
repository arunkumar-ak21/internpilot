"""A deliberately small, safe arithmetic tool."""

import ast
import operator

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def calculate(expression: str) -> float:
    """Evaluate numeric arithmetic without executing arbitrary Python."""
    if len(expression) > 200:
        raise ValueError("Expression is too long")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError("Invalid arithmetic expression") from error

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](visit(node.operand))
        raise ValueError("Only numeric arithmetic is allowed")

    return visit(tree.body)
