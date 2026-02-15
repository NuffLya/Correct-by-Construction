import subprocess
import sys
from pathlib import Path

try:
    if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
        sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bridge.round_trip import spec_to_natural_language
from src.codegen.go_emitter import GoCodeGenerator
from src.dsl.spec_loader import load_spec
from src.formal.verifier import FormalVerifier
from src.arch.topology_generator import solve_and_generate


def main() -> None:
    spec_path = Path(__file__).parent / "wallet_system.yaml"
    if not spec_path.exists():
        print(f"File not found: {spec_path}")
        sys.exit(1)

    print("=== Correct-by-Construction: Wallet System Demo ===\n")

    print("1. Loading specification...")
    spec = load_spec(spec_path)
    print(f"   Loaded: {spec.get('name', '')} v{spec.get('version', '')}")
    print(f"   Entities: {[e['name'] for e in spec.get('entities', [])]}")
    print(f"   Services: {[s['name'] for s in spec.get('services', [])]}")

    print("\n2. Round-Trip: specification in natural language")
    explanation = spec_to_natural_language(spec)
    print(explanation[:500] + "..." if len(explanation) > 500 else explanation)

    print("\n3. Formal verification (Z3)...")
    verifier = FormalVerifier()
    result = verifier.verify(spec)
    if result.is_consistent:
        print("   ✓ Specification is consistent")
    else:
        print("   ✗ Error: specification is inconsistent")
        print(f"   {result.counterexample}")
        sys.exit(1)
    if result.is_complete:
        print("   ✓ Completeness check passed")

    print("\n4. Architecture solver...")
    arch_req = spec.get("architecture", {}).get("requirements", {})
    if not arch_req:
        arch_req = {"rps_target": 1000, "consistency": "strong", "durability": "high", "latency_p99": 100}
    topology = solve_and_generate(arch_req)
    print(f"   Selected: {topology.get('primary_store', 'postgres')}")
    if topology.get("cache"):
        print(f"   Cache: {topology['cache']}")
    print(f"   Reason: {topology.get('reason', '')}")

    print("\n5. Generating Go code...")
    output_dir = Path(__file__).parent.parent / "generated"
    codegen = GoCodeGenerator(module_path="generated")
    artifacts = codegen.generate(spec=spec, output_dir=output_dir)
    print(f"   Generated files: {len(artifacts['files'])}")
    for f in artifacts["files"]:
        print(f"   - {f}")

    print("\n6. Initializing Go module...")
    try:
        subprocess.run(
            ["go", "mod", "init", "generated"],
            cwd=output_dir,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["go", "get", "github.com/google/uuid", "github.com/shopspring/decimal"],
            cwd=output_dir,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        print("   Go not installed — skipping go mod init")

    print("\n7. Running tests...")
    try:
        r = subprocess.run(
            ["go", "test", "./..."],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            print("   ✓ All tests passed")
        else:
            print(f"   Output: {r.stderr or r.stdout}")
    except FileNotFoundError:
        print("   Go not installed — tests skipped")
    except subprocess.TimeoutExpired:
        print("   Timeout")

    print("\n=== Demo complete ===")


if __name__ == "__main__":
    main()
