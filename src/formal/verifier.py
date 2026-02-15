from dataclasses import dataclass, field
from typing import Any

from z3 import sat, unknown, unsat

from .z3_translator import build_consistency_solver, build_service_solver, translate_spec_to_z3


@dataclass
class VerificationResult:
    is_consistent: bool = True
    is_complete: bool = True
    counterexample: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class FormalVerifier:

    def __init__(self, timeout_ms: int = 5000) -> None:
        self.timeout_ms = timeout_ms

    def verify(self, spec: dict[str, Any]) -> VerificationResult:
        result = VerificationResult()

        consistency_result = self._check_consistency(spec)
        result.is_consistent = consistency_result.is_consistent
        result.counterexample = consistency_result.counterexample
        result.errors.extend(consistency_result.errors)

        if result.is_consistent:
            completeness_result = self._check_completeness(spec)
            result.is_complete = completeness_result.is_complete
            result.errors.extend(completeness_result.errors)
            result.warnings.extend(completeness_result.warnings)

        return result

    def _check_consistency(self, spec: dict[str, Any]) -> VerificationResult:
        result = VerificationResult()
        try:
            solver = build_consistency_solver(spec, self.timeout_ms)
            z3_result = solver.check()

            if z3_result == unsat:
                result.is_consistent = False
                result.errors.append("Invariants are inconsistent: no model exists")
                result.counterexample = "Solver returned UNSAT — invariants are incompatible"
            elif z3_result == unknown:
                result.warnings.append("Z3 could not determine within timeout")
            elif z3_result == sat:
                result.is_consistent = True
        except Exception as e:
            result.is_consistent = False
            result.errors.append(f"Verification error: {e}")
            result.counterexample = str(e)

        return result

    def _check_completeness(self, spec: dict[str, Any]) -> VerificationResult:
        result = VerificationResult()
        services = spec.get("services", [])

        if not services:
            result.warnings.append("No services for completeness check")

        for service in services:
            sname = service.get("name", "")
            try:
                solver = build_service_solver(
                    spec, sname, include_preconditions=True, timeout_ms=self.timeout_ms
                )
                z3_result = solver.check()

                if z3_result == unsat:
                    result.is_complete = False
                    result.errors.append(
                        f"Service «{sname}»: preconditions incompatible with invariants"
                    )
                elif z3_result == unknown:
                    result.warnings.append(
                        f"Service «{sname}»: could not verify within timeout"
                    )
            except Exception as e:
                result.warnings.append(f"Service «{sname}»: {e}")

        return result
