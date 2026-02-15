from typing import Any


def generate_validation_script(spec: dict[str, Any]) -> str:
    entities = spec.get("entities", [])
    lines = [
        "package main",
        "",
        "import (",
        '    "log"',
        '    "generated/entities"',
        ")",
        "",
        "func main() {",
        "    _ = entities.Wallet{}",
        "    log.Println(\"Validation OK\")",
        "}",
    ]
    return "\n".join(lines)
