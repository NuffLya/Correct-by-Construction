from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldDiff:
    entity: str
    field: str
    action: str
    old_value: Any = None
    new_value: Any = None


@dataclass
class SpecDiff:
    added_entities: list[str] = field(default_factory=list)
    removed_entities: list[str] = field(default_factory=list)
    added_services: list[str] = field(default_factory=list)
    removed_services: list[str] = field(default_factory=list)
    field_changes: list[FieldDiff] = field(default_factory=list)


def compute_diff(spec_v1: dict[str, Any], spec_v2: dict[str, Any]) -> SpecDiff:
    diff = SpecDiff()

    entities_v1 = {e["name"]: e for e in spec_v1.get("entities", [])}
    entities_v2 = {e["name"]: e for e in spec_v2.get("entities", [])}
    diff.added_entities = [n for n in entities_v2 if n not in entities_v1]
    diff.removed_entities = [n for n in entities_v1 if n not in entities_v2]

    for name in set(entities_v1) & set(entities_v2):
        e1, e2 = entities_v1[name], entities_v2[name]
        fields1 = {f["name"]: f for f in e1.get("fields", [])}
        fields2 = {f["name"]: f for f in e2.get("fields", [])}
        for fn in fields2:
            if fn not in fields1:
                diff.field_changes.append(FieldDiff(entity=name, field=fn, action="added", new_value=fields2[fn]))
        for fn in fields1:
            if fn not in fields2:
                diff.field_changes.append(FieldDiff(entity=name, field=fn, action="removed", old_value=fields1[fn]))
            elif fields1[fn] != fields2[fn]:
                diff.field_changes.append(
                    FieldDiff(entity=name, field=fn, action="modified", old_value=fields1[fn], new_value=fields2[fn])
                )

    services_v1 = {s["name"] for s in spec_v1.get("services", [])}
    services_v2 = {s["name"] for s in spec_v2.get("services", [])}
    diff.added_services = list(services_v2 - services_v1)
    diff.removed_services = list(services_v1 - services_v2)

    return diff
