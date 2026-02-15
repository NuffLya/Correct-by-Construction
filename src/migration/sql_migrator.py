from pathlib import Path
from typing import Any

from .diff_analyzer import FieldDiff, SpecDiff, compute_diff


def _to_snake(s: str) -> str:
    import re
    s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def _table_name(entity: str) -> str:
    return _to_snake(entity) + "s"


def generate_migration_sql(diff: SpecDiff, spec_v2: dict[str, Any]) -> str:
    lines = ["BEGIN;", ""]

    for entity in diff.added_entities:
        for e in spec_v2.get("entities", []):
            if e["name"] == entity:
                table = _table_name(entity)
                cols = []
                for f in e.get("fields", []):
                    name = _to_snake(f.get("name", ""))
                    ftype = f.get("type", "String")
                    if ftype.lower() == "uuid":
                        col_type = "UUID"
                    elif ftype.lower() == "decimal":
                        p, s = f.get("precision", 18), f.get("scale", 2)
                        col_type = f"DECIMAL({p},{s})"
                    elif ftype.lower() == "string":
                        col_type = f"VARCHAR({f.get('length', 255)})"
                    else:
                        col_type = "VARCHAR(255)"
                    cols.append(f"    {name} {col_type}")
                lines.append(f"CREATE TABLE IF NOT EXISTS {table} (")
                lines.append(",\n".join(cols))
                lines.append(");")
                lines.append("")
                break

    for fc in diff.field_changes:
        if fc.action == "added":
            table = _table_name(fc.entity)
            name = _to_snake(fc.field)
            new_val = fc.new_value or {}
            ftype = new_val.get("type", "String")
            default = new_val.get("default", "''")
            if ftype.lower() == "decimal":
                col_type = "DECIMAL(18,2)"
            elif ftype.lower() == "uuid":
                col_type = "UUID"
            else:
                col_type = "VARCHAR(255)"
            lines.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {col_type} DEFAULT {default};")
            lines.append("")

    lines.append("COMMIT;")
    return "\n".join(lines)


def create_migration_file(spec_v1: dict[str, Any], spec_v2: dict[str, Any], version: str = "002") -> str:
    diff = compute_diff(spec_v1, spec_v2)
    return generate_migration_sql(diff, spec_v2)
