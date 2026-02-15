from dataclasses import dataclass
from typing import Any

from z3 import sat, Solver

from .z3_translator import translate_spec_to_z3


@dataclass
class SuspiciousState:
    description: str
    entity_name: str
    variable_values: dict[str, Any]
    prevention_rule: str | None = None


SUSPICIOUS_PATTERNS = [
    {
        "name": "negative_balance_active",
        "description": "Negative balance with Active status",
        "condition": "balance < 0 AND status == Active",
        "prevention": "balance >= 0",
    },
    {
        "name": "zero_amount_transfer",
        "description": "Zero-amount transaction",
        "condition": "amount == 0",
        "prevention": "amount > 0",
    },
    {
        "name": "self_transfer",
        "description": "Transfer from wallet to same wallet",
        "condition": "from_id == to_id",
        "prevention": "from_id != to_id",
    },
]


class CounterexampleFinder:

    def __init__(self, timeout_ms: int = 3000) -> None:
        self.timeout_ms = timeout_ms

    def find_suspicious_states(self, spec: dict[str, Any]) -> list[SuspiciousState]:
        result = translate_spec_to_z3(spec)
        found: list[SuspiciousState] = []

        solver = Solver()
        solver.set("timeout", self.timeout_ms)

        for formula in result.invariant_formulas:
            solver.add(formula)

        for entity_name, entity_vars in result.entity_vars.items():
            if "balance" in entity_vars:
                balance_var = entity_vars["balance"]
                try:
                    solver.push()
                    solver.add(balance_var == 0)
                    if solver.check() == sat:
                        model = solver.model()
                        values = {str(v): str(model.eval(v)) for v in entity_vars.values()}
                        found.append(
                            SuspiciousState(
                                description="Edge case: balance equals zero",
                                entity_name=entity_name,
                                variable_values=values,
                                prevention_rule=None,
                            )
                        )
                except Exception:
                    pass
                finally:
                    solver.pop()

        return found

    def find_counterexample_for_invariant(
        self,
        spec: dict[str, Any],
        entity_name: str,
        invariant_expr: str,
    ) -> SuspiciousState | None:
        result = translate_spec_to_z3(spec)
        entity_vars = result.entity_vars.get(entity_name)
        if not entity_vars:
            return None

        from z3 import Not

        solver = Solver()
        solver.set("timeout", self.timeout_ms)

        for f in result.invariant_formulas:
            solver.add(f)

        negation = None
        for fname, var in entity_vars.items():
            if fname in invariant_expr:
                if ">=" in invariant_expr and "0" in invariant_expr:
                    negation = var < 0
                    break
                if ">" in invariant_expr and "0" in invariant_expr:
                    negation = var <= 0
                    break

        if negation is not None:
            solver.add(negation)
            if solver.check() == sat:
                model = solver.model()
                values = {str(v): str(model.eval(v)) for v in entity_vars.values()}
                return SuspiciousState(
                    description=f"Invariant violation: {invariant_expr}",
                    entity_name=entity_name,
                    variable_values=values,
                    prevention_rule=invariant_expr,
                )

        return None
