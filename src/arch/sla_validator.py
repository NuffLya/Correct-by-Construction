from typing import Any

from .components_db import get_component
from .constraint_solver import TopologyResult


def validate_topology_against_sla(
    topology: TopologyResult,
    requirements: dict[str, Any],
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    rps = requirements.get("rps_target", 100)
    consistency = requirements.get("consistency", "strong")
    durability = requirements.get("durability", "high")
    latency_p99 = requirements.get("latency_p99", 100)

    primary = get_component(topology.primary_store)
    if primary:
        if primary.max_rps < rps:
            errors.append(
                f"{topology.primary_store} max_rps={primary.max_rps} < required {rps}"
            )
        if consistency == "strong" and primary.consistency != "strong":
            errors.append(
                f"Strong consistency required, but {topology.primary_store} has {primary.consistency}"
            )
        if primary.latency_p99_ms > latency_p99:
            errors.append(
                f"{topology.primary_store} latency_p99={primary.latency_p99_ms}ms > {latency_p99}ms"
            )

    return (len(errors) == 0, errors)
