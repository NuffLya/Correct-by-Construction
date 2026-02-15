from typing import Any

from .ast_nodes import Entity, Service, Specification, spec_dict_to_ast


class ValidationError(Exception):
    def __init__(self, message: str, path: str = "") -> None:
        self.message = message
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)


def validate_specification(spec: dict[str, Any] | Specification) -> list[str]:
    errors: list[str] = []
    if isinstance(spec, dict):
        ast = spec_dict_to_ast(spec)
    else:
        ast = spec

    entity_names = {e.name for e in ast.entities}
    entity_field_map: dict[str, set[str]] = {}
    for e in ast.entities:
        entity_field_map[e.name] = {f.name for f in e.fields}

    for entity in ast.entities:
        for inv in entity.invariants:
            for f in entity.fields:
                if f.name in inv.expr and f.name not in entity_field_map.get(entity.name, set()):
                    pass
            for other in entity_names:
                if other != entity.name and f"{other}(" in inv.expr:
                    errors.append(
                        f"Entity {entity.name}, invariant {inv.name}: "
                        f"reference to {other} — use only your entity's fields"
                    )

    for service in ast.services:
        for pre in service.contract.preconditions:
            for ref in entity_names:
                if f"{ref}(" in pre:
                    if ref not in entity_names:
                        errors.append(
                            f"Service {service.name}: precondition references non-existent entity {ref}"
                        )
                    else:
                        if ")." in pre:
                            field_ref = pre.split(").")[-1].split(".")[-1].split(" ")[0]
                            if field_ref and entity_field_map.get(ref) and field_ref not in entity_field_map[ref]:
                                errors.append(
                                    f"Service {service.name}: precondition references non-existent field {field_ref}"
                                )

    for service in ast.services:
        for inp in service.contract.inputs:
            if not inp.name:
                errors.append(f"Service {service.name}: empty parameter name")
            if not inp.type:
                errors.append(f"Service {service.name}, input {inp.name}: type not specified")

    return errors
