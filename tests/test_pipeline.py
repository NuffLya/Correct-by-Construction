import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dsl.spec_loader import load_spec, validate_spec
from src.formal.verifier import FormalVerifier
from src.formal.counterexample_finder import CounterexampleFinder
from src.bridge.round_trip import spec_to_natural_language
from src.arch.topology_generator import solve_and_generate
from src.codegen.go_emitter import GoCodeGenerator
from src.migration.diff_analyzer import compute_diff


def test_load_wallet_spec():
    spec_path = Path(__file__).parent.parent / "examples" / "wallet_system.yaml"
    spec = load_spec(spec_path)
    assert spec["name"] == "WalletSystem"
    assert len(spec["entities"]) == 2
    assert len(spec["services"]) == 2
    assert spec["entities"][0]["name"] == "Wallet"
    assert spec["entities"][0]["invariants"][0]["expr"] == "balance >= 0"


def test_verifier_consistency():
    spec_path = Path(__file__).parent.parent / "examples" / "wallet_system.yaml"
    spec = load_spec(spec_path)
    verifier = FormalVerifier()
    result = verifier.verify(spec)
    assert result.is_consistent
    assert result.is_complete


def test_round_trip():
    spec_path = Path(__file__).parent.parent / "examples" / "wallet_system.yaml"
    spec = load_spec(spec_path)
    text = spec_to_natural_language(spec)
    assert "Wallet" in text
    assert "balance" in text
    assert "Transfer" in text


def test_arch_solver():
    req = {"rps_target": 1000, "consistency": "strong", "durability": "high"}
    topo = solve_and_generate(req)
    assert topo["primary_store"] == "postgres"
    assert topo["satisfies_sla"]


def test_code_generation():
    spec_path = Path(__file__).parent.parent / "examples" / "wallet_system.yaml"
    spec = load_spec(spec_path)
    output = Path(__file__).parent.parent / "generated_test"
    codegen = GoCodeGenerator(module_path="generated_test")
    artifacts = codegen.generate(spec=spec, output_dir=output)
    assert len(artifacts["files"]) >= 5
    assert (output / "entities" / "entities.go").exists()
    assert (output / "main.go").exists()
    assert (output / "migrations" / "001_initial.sql").exists()


def test_migration_diff():
    spec_v1 = {
        "entities": [
            {"name": "Wallet", "fields": [{"name": "id", "type": "UUID"}, {"name": "balance", "type": "Decimal"}]}
        ],
        "services": [],
    }
    spec_v2 = {
        "entities": [
            {
                "name": "Wallet",
                "fields": [
                    {"name": "id", "type": "UUID"},
                    {"name": "balance", "type": "Decimal"},
                    {"name": "currency", "type": "String"},
                ],
            }
        ],
        "services": [],
    }
    diff = compute_diff(spec_v1, spec_v2)
    assert len(diff.field_changes) >= 1
    assert any(fc.field == "currency" and fc.action == "added" for fc in diff.field_changes)
