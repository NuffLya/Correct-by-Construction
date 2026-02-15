from typing import Any


def generate_state_machine_test(spec: dict[str, Any]) -> str:
    services = spec.get("services", [])
    service_names = [s.get("name", "") for s in services]

    lines = [
        "package entities",
        "",
        "import (",
        '    "testing"',
        '    "github.com/google/uuid"',
        '    "github.com/shopspring/decimal"',
        ")",
        "",
        "func TestStateMachineInvariants(t *testing.T) {",
        "    var w Wallet",
        "    w.ID = uuid.New()",
        "    w.Balance = decimal.Zero",
        "    ",
        "    if err := w.Validate(); err != nil {",
        "        t.Fatalf(\"initial state invalid: %v\", err)",
        "    }",
        "    ",
        "    _ = w",
        "}",
        "",
    ]

    return "\n".join(lines)
