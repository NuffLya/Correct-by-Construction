from typing import Any


def _to_snake(s: str) -> str:
    import re
    s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def generate_entity_property_test(entity: dict) -> str:
    name = entity.get("name", "Entity")
    has_balance = any(f.get("name") == "balance" for f in entity.get("fields", []))
    has_status = any(f.get("name") == "status" for f in entity.get("fields", []))
    status_values = []
    for f in entity.get("fields", []):
        if f.get("name") == "status" and f.get("values"):
            status_values = f.get("values", [])
            break
    invariants = entity.get("invariants", [])

    lines = [
        "package entities",
        "",
        "import (",
        '    "testing"',
        '    "testing/quick"',
        '    "github.com/google/uuid"',
        '    "github.com/shopspring/decimal"',
        ")",
        "",
        f"func Test{name}InvariantsHold(t *testing.T) {{",
    ]

    if has_balance and any("balance" in inv.get("expr", "") and ">=" in inv.get("expr", "") for inv in invariants):
        struct_fields = ["ID: uuid.New()", "Balance: decimal.NewFromInt(balance)"]
        if has_status and status_values:
            struct_fields.append(f"Status: {name}{status_values[0]}")
        lines.extend([
            "    f := func(balance int64) bool {",
            f"        e := {name}{{",
            "            " + ",\n            ".join(struct_fields),
            "        }",
            "        ",
            "        err := e.Validate()",
            "        ",
            "        if balance >= 0 {",
            "            return err == nil",
            "        }",
            "        return err != nil",
            "    }",
            "    ",
            "    if err := quick.Check(f, nil); err != nil {",
            "        t.Error(err)",
            "    }",
            "}",
        ])
    else:
        lines.extend([
            f"    e := {name}{{}}",
            "    _ = e.Validate()",
            "}",
        ])

    return "\n".join(lines)


def generate_all_property_tests(spec: dict[str, Any]) -> dict[str, str]:
    result = {}
    for entity in spec.get("entities", []):
        name = entity.get("name", "Entity")
        content = generate_entity_property_test(entity)
        result[f"{_to_snake(name)}_property_test.go"] = content
    return result
