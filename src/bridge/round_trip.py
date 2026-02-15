from typing import Any


def spec_to_natural_language(spec: dict[str, Any]) -> str:
    lines: list[str] = []

    name = spec.get("name", "System")
    lines.append(f"System specification: {name}")
    lines.append("")

    for entity in spec.get("entities", []):
        entity_name = entity.get("name", "Unknown")
        fields = entity.get("fields", [])
        invariants = entity.get("invariants", [])

        field_descs = ", ".join(f"{f.get('name', '')} ({f.get('type', '')})" for f in fields)
        lines.append(f"Entity «{entity_name}» has fields: {field_descs}.")

        for inv in invariants:
            expr = inv.get("expr", inv.get("expression", ""))
            inv_name = inv.get("name", "")
            if expr:
                lines.append(f"  — Invariant «{inv_name}»: always holds: {expr}")

        lines.append("")

    for service in spec.get("services", []):
        service_name = service.get("name", "Unknown")
        inputs = service.get("inputs", [])
        preconditions = service.get("preconditions", [])
        postconditions = service.get("postconditions", [])

        input_descs = ", ".join(f"{i.get('name', '')} ({i.get('type', '')})" for i in inputs)
        lines.append(f"Service «{service_name}» accepts: {input_descs}.")

        if preconditions:
            lines.append("  Preconditions:")
            for pre in preconditions:
                lines.append(f"    — {pre}")

        if postconditions:
            lines.append("  Postconditions:")
            for post in postconditions:
                lines.append(f"    — {post}")

        lines.append("")

    return "\n".join(lines).strip()


def generate_confirmation_questions(spec: dict[str, Any]) -> list[str]:
    questions: list[str] = []

    for entity in spec.get("entities", []):
        name = entity.get("name", "")
        for inv in entity.get("invariants", []):
            expr = inv.get("expr", inv.get("expression", ""))
            if expr and "balance" in expr.lower() and ">=" in expr:
                questions.append(
                    f"Do you confirm that in «{name}» balance can never be negative?"
                )
            elif expr and "!=" in expr or "!=" in expr:
                questions.append(
                    f"Do you confirm invariant «{name}»: {expr}?"
                )

    for service in spec.get("services", []):
        sname = service.get("name", "")
        pres = service.get("preconditions", [])
        if any("from" in str(p).lower() and "to" in str(p).lower() for p in pres):
            questions.append(
                f"Do you confirm that service «{sname}» prohibits transfer from wallet to same wallet?"
            )

    return questions
