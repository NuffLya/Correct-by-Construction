from typing import Any


def can_migrate_data(diff: Any, spec_v2: dict[str, Any]) -> tuple[bool, list[str]]:
    errors = []
    for fc in diff.field_changes:
        if fc.action == "removed":
            errors.append(f"Removing field {fc.entity}.{fc.field} may lead to data loss")
        if fc.action == "modified":
            old_t = (fc.old_value or {}).get("type", "")
            new_t = (fc.new_value or {}).get("type", "")
            if old_t != new_t:
                errors.append(f"Type change {fc.entity}.{fc.field}: {old_t} -> {new_t}")
    return len(errors) == 0, errors
