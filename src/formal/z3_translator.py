import re
from typing import Any

from z3 import And, Int, IntVal, Real, RealVal, Solver

from .smt_utils import create_solver, simple_invariant_to_z3


class Z3TranslationResult:

    def __init__(self) -> None:
        self.invariant_formulas: list[Any] = []
        self.precondition_formulas: dict[str, list[Any]] = {}
        self.variables: dict[str, Any] = {}
        self.entity_vars: dict[str, dict[str, Any]] = {}


def _parse_simple_comparison(expr: str, vars_ctx: dict[str, Any]) -> Any | None:
    expr = expr.strip()
    patterns = [
        (r"(\w+)\s*>=\s*(\d+(?:\.\d+)?)", ">=", True),
        (r"(\w+)\s*<=\s*(\d+(?:\.\d+)?)", "<=", True),
        (r"(\w+)\s*>\s*(\d+(?:\.\d+)?)", ">", True),
        (r"(\w+)\s*<\s*(\d+(?:\.\d+)?)", "<", True),
        (r"(\w+)\s*==\s*(\d+(?:\.\d+)?)", "==", True),
        (r"(\w+)\s*!=\s*(\w+)", "!=", False),
        (r"(\w+)\s*==\s*(\w+)", "==", False),
    ]
    for pattern, op, right_is_num in patterns:
        m = re.match(pattern, expr)
        if m:
            left_name, right_str = m.group(1), m.group(2)
            if left_name not in vars_ctx:
                vars_ctx[left_name] = Real(left_name) if "." in right_str else Int(left_name)
            left = vars_ctx[left_name]
            if right_is_num:
                try:
                    right = RealVal(float(right_str)) if "." in right_str else IntVal(int(right_str))
                except ValueError:
                    right = IntVal(0)
            else:
                right = vars_ctx.get(right_str, Int(right_str))
            if op == ">=":
                return left >= right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            if op == "<":
                return left < right
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
    return None


def translate_spec_to_z3(spec: dict[str, Any]) -> Z3TranslationResult:
    result = Z3TranslationResult()
    vars_ctx = result.variables

    for entity in spec.get("entities", []):
        entity_name = entity.get("name", "")
        entity_vars: dict[str, Any] = {}
        result.entity_vars[entity_name] = entity_vars

        for field in entity.get("fields", []):
            fname = field.get("name", "")
            ftype = field.get("type", "String").lower()
            var_name = f"{entity_name}_{fname}" if entity_name else fname
            if ftype in ("decimal", "real", "float"):
                entity_vars[fname] = Real(var_name)
                vars_ctx[var_name] = entity_vars[fname]
            elif ftype in ("int", "integer", "int64"):
                entity_vars[fname] = Int(var_name)
                vars_ctx[var_name] = entity_vars[fname]
            else:
                entity_vars[fname] = Int(var_name)
                vars_ctx[var_name] = entity_vars[fname]

        for inv in entity.get("invariants", []):
            expr = inv.get("expr", inv.get("expression", ""))
            if expr:
                inv_ctx = {**vars_ctx, **entity_vars}
                formula = _parse_simple_comparison(expr, inv_ctx)
                if formula is None:
                    formula = simple_invariant_to_z3(expr, entity_vars)
                if formula is not None:
                    result.invariant_formulas.append(formula)

    for service in spec.get("services", []):
        sname = service.get("name", "")
        pre_formulas: list[Any] = []

        for inp in service.get("inputs", []):
            iname = inp.get("name", "")
            itype = inp.get("type", "String").lower()
            var_name = f"{sname}_{iname}"
            if itype in ("decimal", "real", "float"):
                vars_ctx[var_name] = Real(var_name)
            else:
                vars_ctx[var_name] = Int(var_name)

        for pre in service.get("preconditions", []):
            if isinstance(pre, str):
                formula = _parse_simple_comparison(pre, vars_ctx)
                if formula is not None:
                    pre_formulas.append(formula)
                else:
                    for entity_name, entity_vars in result.entity_vars.items():
                        if f"{entity_name}(" in pre:
                            for fname, var in entity_vars.items():
                                if fname in pre:
                                    formula = _parse_simple_comparison(
                                        pre.replace(f"{entity_name}(", "").replace(")", "").replace(".", "_"),
                                        {**vars_ctx, **entity_vars},
                                    )
                                    if formula is not None:
                                        pre_formulas.append(formula)
                                    break

        result.precondition_formulas[sname] = pre_formulas

    return result


def build_consistency_solver(spec: dict[str, Any], timeout_ms: int = 5000) -> Solver:
    result = translate_spec_to_z3(spec)
    solver = create_solver(timeout_ms)
    for f in result.invariant_formulas:
        solver.add(f)
    return solver


def build_service_solver(
    spec: dict[str, Any],
    service_name: str,
    include_preconditions: bool = True,
    timeout_ms: int = 5000,
) -> Solver:
    result = translate_spec_to_z3(spec)
    solver = create_solver(timeout_ms)
    for f in result.invariant_formulas:
        solver.add(f)
    if include_preconditions and service_name in result.precondition_formulas:
        for f in result.precondition_formulas[service_name]:
            solver.add(f)
    return solver
