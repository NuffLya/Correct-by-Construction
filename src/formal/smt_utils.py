import re
from typing import Any

from z3 import And, Bool, BoolVal, Int, IntVal, Not, Or, Real, RealVal, Solver


def create_solver(timeout_ms: int = 5000) -> Solver:
    s = Solver()
    s.set("timeout", timeout_ms)
    return s


def expr_to_z3_vars(expr: str, context: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    expr = expr.strip()
    context = dict(context)

    operators = [
        (r"(\w+)\s*>=\s*(\d+(?:\.\d+)?)", ">="),
        (r"(\w+)\s*<=\s*(\d+(?:\.\d+)?)", "<="),
        (r"(\w+)\s*>\s*(\d+(?:\.\d+)?)", ">"),
        (r"(\w+)\s*<\s*(\d+(?:\.\d+)?)", "<"),
        (r"(\w+)\s*==\s*(\w+)", "=="),
        (r"(\w+)\s*!=\s*(\w+)", "!="),
    ]

    for pattern, op in operators:
        m = re.match(pattern, expr)
        if m:
            left_name, right_val = m.group(1), m.group(2)
            if left_name not in context:
                context[left_name] = Real(left_name) if "." in right_val else Int(left_name)
            left = context[left_name]

            try:
                if "." in right_val:
                    right = RealVal(float(right_val))
                else:
                    right = IntVal(int(right_val))
            except ValueError:
                right = context.get(right_val, Int(right_val))

            if op == ">=":
                return left >= right, context
            if op == "<=":
                return left <= right, context
            if op == ">":
                return left > right, context
            if op == "<":
                return left < right, context
            if op == "==":
                return left == right, context
            if op == "!=":
                return left != right, context

    return BoolVal(True), context


def simple_invariant_to_z3(expr: str, numeric_vars: dict[str, Any]) -> Any | None:
    expr = expr.strip()
    if not expr:
        return None

    for op_pattern, op_sym in [
        (r"(\w+)\s*>=\s*(\d+(?:\.\d+)?)", ">="),
        (r"(\w+)\s*<=\s*(\d+(?:\.\d+)?)", "<="),
        (r"(\w+)\s*>\s*(\d+(?:\.\d+)?)", ">"),
        (r"(\w+)\s*<\s*(\d+(?:\.\d+)?)", "<"),
    ]:
        m = re.match(op_pattern, expr)
        if m:
            var_name, val_str = m.group(1), m.group(2)
            var = numeric_vars.get(var_name)
            if var is None:
                var = Real(var_name) if "." in val_str else Int(var_name)
                numeric_vars[var_name] = var
            try:
                val = RealVal(float(val_str)) if "." in val_str else IntVal(int(val_str))
            except ValueError:
                return None
            if op_sym == ">=":
                return var >= val
            if op_sym == "<=":
                return var <= val
            if op_sym == ">":
                return var > val
            if op_sym == "<":
                return var < val

    return None
