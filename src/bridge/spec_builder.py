import re
from typing import Any


def parse_entity_from_text(text: str) -> dict[str, Any] | None:
    lines = text.strip().split("\n")
    name = None
    fields: list[dict] = []
    invariants: list[dict] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        name_match = re.match(r"^(?:entity\s+)?(\w+)\s*:?\s*$", line, re.I)
        if name_match and name is None:
            name = name_match.group(1)
            continue

        field_match = re.match(
            r"^[-*]?\s*(\w+)\s*[:(]\s*(\w+)(?:\))?\s*$",
            line,
            re.I,
        )
        if field_match:
            fields.append({
                "name": field_match.group(1),
                "type": field_match.group(2),
            })
            continue

        inv_match = re.match(
            r"^[-*]?\s*(?:invariant\s*:?\s*)?(.+)$",
            line,
            re.I,
        )
        if inv_match:
            expr = inv_match.group(1).strip()
            if ">=" in expr or "<=" in expr or "==" in expr or "!=" in expr or ">" in expr or "<" in expr:
                invariants.append({
                    "name": f"inv_{len(invariants)}",
                    "expr": expr,
                })

    if name:
        result: dict[str, Any] = {"name": name, "fields": fields}
        if invariants:
            result["invariants"] = invariants
        return result
    return None


def parse_service_from_text(text: str) -> dict[str, Any] | None:
    lines = text.strip().split("\n")
    name = None
    inputs: list[dict] = []
    preconditions: list[str] = []
    postconditions: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        name_match = re.match(r"^(?:service\s+)?(\w+)\s*:?\s*$", line, re.I)
        if name_match and name is None:
            name = name_match.group(1)
            continue

        input_match = re.match(r"^[-*]?\s*(\w+)\s*[:(]\s*(\w+)", line, re.I)
        if input_match and "pre" not in line.lower() and "post" not in line.lower():
            inputs.append({
                "name": input_match.group(1),
                "type": input_match.group(2),
            })
            continue

        if "pre" in line.lower() or "precondition" in line.lower():
            expr = re.sub(r"^[-*]?\s*(?:pre|precondition)\s*:?\s*", "", line, flags=re.I).strip()
            if expr and len(expr) > 2:
                preconditions.append(expr)
        elif "post" in line.lower() or "postcondition" in line.lower():
            expr = re.sub(r"^[-*]?\s*(?:post|postcondition)\s*:?\s*", "", line, flags=re.I).strip()
            if expr and len(expr) > 2:
                postconditions.append(expr)

    if name:
        result: dict[str, Any] = {"name": name, "inputs": inputs}
        if preconditions:
            result["preconditions"] = preconditions
        if postconditions:
            result["postconditions"] = postconditions
        return result
    return None


def build_spec_from_llm_response(
    domain: str,
    entities_text: str,
    services_text: str,
) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "name": _domain_to_name(domain),
        "version": "1.0.0",
        "entities": [],
        "services": [],
    }

    for block in _split_blocks(entities_text):
        entity = parse_entity_from_text(block)
        if entity:
            spec["entities"].append(entity)

    for block in _split_blocks(services_text):
        service = parse_service_from_text(block)
        if service:
            spec["services"].append(service)

    return spec


def _domain_to_name(domain: str) -> str:
    words = re.findall(r"\w+", domain)
    if not words:
        return "UnknownSystem"
    return "".join(w.capitalize() for w in words[:3])


def _split_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.split("\n"):
        if line.strip() == "" and current:
            blocks.append("\n".join(current))
            current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks
