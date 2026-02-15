import re
from pathlib import Path
from typing import Any

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_project_root))

from src.dsl.type_system import resolve_sql_type


def _to_snake(s: str) -> str:
    s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def _table_name(entity_name: str) -> str:
    return _to_snake(entity_name) + "s"


def generate_ddl(spec: dict[str, Any]) -> str:
    lines = []

    for entity in spec.get("entities", []):
        table = _table_name(entity.get("name", "entity"))
        lines.append(f"CREATE TABLE IF NOT EXISTS {table} (")
        cols = []
        for f in entity.get("fields", []):
            name = _to_snake(f.get("name", ""))
            sql_type = resolve_sql_type(
                f.get("type", "String"),
                length=f.get("length"),
                precision=f.get("precision"),
                scale=f.get("scale"),
            )
            constraints = []
            if f.get("primary_key"):
                constraints.append("PRIMARY KEY")
            if f.get("indexed"):
                constraints.append("")
            col = f"    {name} {sql_type}"
            if constraints:
                col += " " + " ".join(c for c in constraints if c)
            cols.append(col)
        lines.append(",\n".join(cols))
        lines.append(");")
        lines.append("")

    return "\n".join(lines)


def generate_migration_file(spec: dict[str, Any], version: str = "001") -> str:
    ddl = generate_ddl(spec)
    return f"""BEGIN;

{ddl}

COMMIT;
"""
