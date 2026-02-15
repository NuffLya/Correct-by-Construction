# Correct-by-Construction

> **Prototype** of a deterministic software development system where source code is a secondary projection of a formal model. Principle: *Correct-by-Construction* — the LLM does not generate executable code directly but participates in building and refining the specification.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Prototype Limitations

**Note:** This is a research prototype, not a production-ready solution.

- Limited set of data types (Int, String, Decimal, UUID, Enum, Timestamp)
- Z3 is effective for specifications with a small number of variables (~100)
- Target generation language: Go only
- Architectural solver uses a simplified model (Postgres, Redis, Kafka)
- Local LLM (Ollama) may require more refinement iterations than cloud models

---

## Architecture

```
Natural Language ──► LLM Bridge ──► Formal Spec ──► Z3 Solver ──► Arch Solver ──► DSL Core
                                                         │
                                                         ▼
                              Code / Tests / Migrations ◄── Code Generator
```

| Stage | Description |
|-------|-------------|
| **LLM Bridge** | Expert interview, extraction of entities and business rules, round-trip translation |
| **Formal Spec** | YAML specification with entities, invariants, pre/postconditions |
| **Z3 Solver** | Consistency and completeness checks, boundary case discovery |
| **Arch Solver** | Topology selection (Postgres/Redis/Kafka) based on SLA |
| **Code Generator** | Jinja2 templates → Go code, SQL DDL, migrations, property-based tests |

---

## Installation

```bash
git clone https://github.com/NuffLya/correct-by-construction.git
cd correct-by-construction

pip install -r requirements.txt
```

**Optional (for full pipeline):**

- [Ollama](https://ollama.com/download) — local LLM for interviews: `ollama pull llama3.1:8b`
- [Go](https://go.dev/dl/) — for building and testing generated code

---

## Usage

**Wallet System demo (full pipeline):**

```bash
python -m examples.wallet_demo
```

**Code generation only from existing specification:**

```bash
python -c "
from pathlib import Path
from src.dsl.spec_loader import load_spec
from src.codegen.go_emitter import GoCodeGenerator

spec = load_spec(Path('examples/wallet_system.yaml'))
GoCodeGenerator(module_path='generated').generate(spec, output_dir='./generated')
"
```

---

## Specification Example

```yaml
name: WalletSystem
version: "1.0.0"

entities:
  - name: Wallet
    fields:
      - {name: id, type: UUID, primary_key: true}
      - {name: balance, type: Decimal, precision: 18, scale: 2}
      - {name: status, type: Enum, values: [Active, Frozen, Closed]}
    invariants:
      - name: positive_balance
        expr: "balance >= 0"
        severity: critical

services:
  - name: Transfer
    inputs:
      - {name: from_wallet_id, type: UUID}
      - {name: to_wallet_id, type: UUID}
      - {name: amount, type: Decimal}
    preconditions:
      - "amount > 0"
      - "from_wallet_id != to_wallet_id"
    strategy: ACID_Transaction
```

---

## Project Structure

```
correct-by-construction/
├── src/
│   ├── bridge/         # LLM (Ollama), interviews, round-trip
│   ├── formal/         # Z3 verification, counter-examples
│   ├── arch/           # Constraint solver (Postgres, Redis, Kafka)
│   ├── dsl/            # AST, YAML parser, type system
│   ├── codegen/        # Go generation, SQL DDL
│   ├── testgen/        # Property-based tests
│   └── migration/      # Diff, SQL migrations
├── templates/          # Jinja2 templates (Go)
├── examples/           # wallet_system.yaml, wallet_demo.py
├── tests/              # Integration tests
└── generated/          # Generated Go code (created on demo run)
```

---

## Tech Stack

- **Python 3.10+** — orchestration
- **Z3** (z3-solver) — formal verification
- **Jinja2** — code generation templates
- **Pydantic** — specification validation
- **Ollama** — local LLM (optional)

---

## Possible Extensions

- [ ] Temporal logic (LTL) for "eventually" properties
- [ ] Support for Python/Java as target languages
- [ ] Incremental verification on specification changes
- [ ] GUI for visual specification editing

---

## Author

**[@NuffLya](https://github.com/NuffLya)**

---

## License

MIT License — see [LICENSE](LICENSE).
