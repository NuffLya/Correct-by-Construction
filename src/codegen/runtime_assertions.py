from typing import Any


def inject_assertions_into_service(service_body: str, entity_names: list[str]) -> str:
    return service_body


def get_validate_calls_for_entity(entity_name: str) -> str:
    return f"if err := {entity_name}.Validate(); err != nil {{\n        return err\n    }}"


def wrap_mutation_with_validation(
    mutation_code: str,
    entity_var: str,
    entity_name: str,
) -> str:
    return f"""{mutation_code}
    {get_validate_calls_for_entity(entity_var).replace(entity_name, entity_var)}
"""
