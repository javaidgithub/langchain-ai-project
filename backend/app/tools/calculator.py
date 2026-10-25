import ast
import math
import operator as op

from langchain_core.tools import tool

_BIN = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
        ast.FloorDiv: op.floordiv, ast.Mod: op.mod, ast.Pow: op.pow}
_UNARY = {ast.UAdd: op.pos, ast.USub: op.neg}
_FUNCS = {n: getattr(math, n) for n in ("sqrt", "sin", "cos", "tan", "log", "log10", "exp", "floor", "ceil", "factorial")}
_FUNCS.update({"abs": abs, "round": round, "min": min, "max": max})
_CONSTS = {"pi": math.pi, "e": math.e}


def _eval(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent too large")
        return _BIN[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError("Unsupported expression")


def safe_eval(expression: str) -> float | int:
    return _eval(ast.parse(expression.strip(), mode="eval"))


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression exactly. Supports + - * / // % **, parentheses, pi, e and
    sqrt, sin, cos, tan, log, log10, exp, floor, ceil, factorial, abs, round, min, max.
    Example: "sqrt(144) + 2**10"."""
    try:
        return str(safe_eval(expression))
    except Exception as exc:
        return f"Could not evaluate '{expression}': {exc}"
