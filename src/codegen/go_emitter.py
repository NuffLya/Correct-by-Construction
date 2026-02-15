import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_project_root))

from src.dsl.type_system import resolve_go_type


def _to_camel(s: str) -> str:
    parts = re.sub(r"[_\s]+", " ", s).split()
    return "".join(p.capitalize() for p in parts) if parts else s


def _to_snake(s: str) -> str:
    s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def _invariant_to_go_check(inv: dict, entity_name: str, fields: list[dict]) -> str:
    expr = inv.get("expr", inv.get("expression", ""))
    name = inv.get("name", "inv")
    field_map = {f.get("name", ""): _to_camel(f.get("name", "")) for f in fields}
    balance_go = field_map.get("balance", "Balance")
    if "balance" in expr and ">=" in expr and "0" in expr:
        return f'''if e.{balance_go}.LessThan(decimal.Zero) {{
        return &ErrInvariantViolation{{Entity: "{entity_name}", Invariant: "{name}", Message: fmt.Sprintf("balance must be >= 0, got %s", e.{balance_go})}}
    }}'''
    if "balance" in expr and ">" in expr and "0" in expr:
        return f'''if !e.{balance_go}.GreaterThan(decimal.Zero) {{
        return &ErrInvariantViolation{{Entity: "{entity_name}", Invariant: "{name}", Message: "balance must be > 0"}}
    }}'''
    return ""


def _prepare_entity_for_template(entity: dict) -> dict:
    fields = entity.get("fields", [])
    enum_field = None
    enum_values = []
    for f in fields:
        if f.get("type", "").lower() == "enum" and f.get("values"):
            enum_field = f
            enum_values = f.get("values", [])
            break

    prepared_fields = []
    for f in fields:
        ftype = f.get("type", "String")
        type_go = resolve_go_type(
            ftype,
            length=f.get("length"),
            precision=f.get("precision"),
            scale=f.get("scale"),
        )
        if ftype.lower() == "enum" and enum_values and f.get("name") == (enum_field or {}).get("name"):
            type_go = f"{entity.get('name', 'Entity')}Status"
        prepared_fields.append({
            "name": f.get("name", ""),
            "name_go": _to_camel(f.get("name", "")),
            "name_snake": _to_snake(f.get("name", "")),
            "type_go": type_go,
            "json_tag": True,
        })

    invariants = []
    for inv in entity.get("invariants", []):
        invariants.append({
            "name": inv.get("name", ""),
            "expr": inv.get("expr", inv.get("expression", "")),
            "check_go": _invariant_to_go_check(inv, entity.get("name", ""), fields),
        })

    field_lines = []
    for f in prepared_fields:
        jtag = f' `json:"{f["name_snake"]}"`' if f.get("json_tag") else ""
        field_lines.append(f'    {f["name_go"]} {f["type_go"]} `db:"{f["name_snake"]}"`{jtag}')

    return {
        "name": entity.get("name", ""),
        "fields": prepared_fields,
        "field_lines": field_lines,
        "invariants": invariants,
        "enum_values": enum_values,
        "enum_field": enum_field,
    }


def _prepare_service_for_template(service: dict, spec: dict) -> dict:
    inputs = []
    for i in service.get("inputs", []):
        itype = i.get("type", "String")
        inputs.append({
            "name": i.get("name", ""),
            "name_go": _to_camel(i.get("name", "")),
            "type_go": resolve_go_type(itype),
        })

    pre_checks = []
    for pre in service.get("preconditions", []):
        pre_str = str(pre)
        if "amount" in pre_str and "> 0" in pre_str:
            pre_checks.append("if !req.Amount.GreaterThan(decimal.Zero) { return nil, errors.New(\"amount must be > 0\") }")
        elif "!=" in pre_str and "from" in pre_str.lower() and "to" in pre_str.lower():
            pre_checks.append("if req.FromWalletID == req.ToWalletID { return nil, errors.New(\"from and to must be different\") }")

    return {
        "name": service.get("name", ""),
        "inputs": inputs,
        "pre_checks": pre_checks,
    }


def _needs_imports(entities: list[dict]) -> tuple[bool, bool, bool]:
    needs_uuid = needs_decimal = needs_time = False
    for e in entities:
        for f in e.get("fields", []):
            t = f.get("type", "").lower()
            if t in ("uuid",):
                needs_uuid = True
            if t in ("decimal",):
                needs_decimal = True
            if t in ("timestamp",):
                needs_time = True
    return needs_uuid, needs_decimal, needs_time


class GoCodeGenerator:

    def __init__(self, templates_dir: Path | None = None, module_path: str = "generated") -> None:
        self.templates_dir = templates_dir or Path(__file__).parent.parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.module_path = module_path

    def generate(
        self,
        spec: dict[str, Any],
        architecture: dict[str, Any] | None = None,
        output_dir: str | Path = "./generated",
    ) -> dict[str, Any]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / "entities").mkdir(exist_ok=True)
        (output / "services").mkdir(exist_ok=True)

        entities = spec.get("entities", [])
        services = spec.get("services", [])
        name = spec.get("name", "System")
        version = spec.get("version", "1.0.0")

        needs_uuid, needs_decimal, needs_time = _needs_imports(entities)

        prepared_entities = [_prepare_entity_for_template(e) for e in entities]

        ctx = {
            "spec_name": name,
            "spec_version": version,
            "entities": prepared_entities,
            "needs_uuid": needs_uuid,
            "needs_decimal": needs_decimal,
            "needs_time": needs_time,
            "module_path": self.module_path,
        }

        tmpl = self.env.get_template("entity.go.j2")
        entity_content = tmpl.render(**ctx)
        (output / "entities" / "entities.go").write_text(entity_content, encoding="utf-8")

        artifacts: dict[str, Any] = {"files": [str(output / "entities" / "entities.go")], "entities": [], "services": []}

        for service in services:
            svc_ctx = {
                "spec_name": name,
                "spec_version": version,
                "service": _prepare_service_for_template(service, spec),
                "module_path": self.module_path,
            }
            try:
                svc_tmpl = self.env.get_template("service.go.j2")
                svc_content = svc_tmpl.render(**svc_ctx)
                svc_name = service.get("name", "Unknown")
                fpath = output / "services" / f"{_to_snake(svc_name)}.go"
                fpath.write_text(svc_content, encoding="utf-8")
                artifacts["files"].append(str(fpath))
                artifacts["services"].append(str(fpath))
            except Exception:
                pass

        main_ctx = {"module_path": self.module_path}
        main_tmpl = self.env.get_template("main.go.j2")
        main_content = main_tmpl.render(**main_ctx)
        (output / "main.go").write_text(main_content, encoding="utf-8")
        artifacts["files"].append(str(output / "main.go"))

        (output / "go.mod").write_text(
            f"module {self.module_path}\n\ngo 1.21\n",
            encoding="utf-8",
        )
        artifacts["files"].append(str(output / "go.mod"))

        from .sql_generator import generate_migration_file
        from src.testgen.property_based import generate_all_property_tests

        test_files = generate_all_property_tests(spec)
        for fname, content in test_files.items():
            test_path = output / "entities" / fname
            test_path.write_text(content, encoding="utf-8")
            artifacts["files"].append(str(test_path))
        artifacts.setdefault("tests", [])
        artifacts["tests"] = [str(output / "entities" / f) for f in test_files]

        migrations_dir = output / "migrations"
        migrations_dir.mkdir(exist_ok=True)
        migration_content = generate_migration_file(spec)
        migration_path = migrations_dir / "001_initial.sql"
        migration_path.write_text(migration_content, encoding="utf-8")
        artifacts["files"].append(str(migration_path))
        artifacts["migrations"] = [str(migration_path)]

        return artifacts
