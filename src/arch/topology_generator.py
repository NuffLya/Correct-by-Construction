from typing import Any

from .constraint_solver import TopologyResult, solve_architecture


def generate_topology_spec(result: TopologyResult) -> dict[str, Any]:
    components = [result.primary_store]
    if result.cache:
        components.append(result.cache)
    if result.message_queue:
        components.append(result.message_queue)

    return {
        "primary_store": result.primary_store,
        "cache": result.cache,
        "message_queue": result.message_queue,
        "components": components,
        "satisfies_sla": result.satisfies_sla,
        "reason": result.reason,
    }


def solve_and_generate(requirements: dict[str, Any]) -> dict[str, Any]:
    result = solve_architecture(requirements)
    return generate_topology_spec(result)
