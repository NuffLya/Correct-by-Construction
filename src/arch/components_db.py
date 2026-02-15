from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComponentSpec:
    name: str
    consistency: str
    max_rps: int
    durability: str
    latency_p99_ms: int
    throughput: str = "medium"
    ordering: bool = False


COMPONENTS: dict[str, ComponentSpec] = {
    "postgres": ComponentSpec(
        name="postgres",
        consistency="strong",
        max_rps=10000,
        durability="high",
        latency_p99_ms=50,
        throughput="medium",
    ),
    "redis": ComponentSpec(
        name="redis",
        consistency="eventual",
        max_rps=100000,
        durability="low",
        latency_p99_ms=1,
        throughput="high",
    ),
    "kafka": ComponentSpec(
        name="kafka",
        consistency="eventual",
        max_rps=500000,
        durability="high",
        latency_p99_ms=5,
        throughput="very_high",
        ordering=True,
    ),
}


def get_component(name: str) -> ComponentSpec | None:
    return COMPONENTS.get(name.lower())


def get_components_matching(
    rps_min: int = 0,
    consistency: str | None = None,
    durability: str | None = None,
    latency_max_ms: int | None = None,
) -> list[ComponentSpec]:
    result = []
    for comp in COMPONENTS.values():
        if comp.max_rps < rps_min:
            continue
        if consistency and comp.consistency != consistency:
            continue
        if durability and comp.durability != durability:
            continue
        if latency_max_ms and comp.latency_p99_ms > latency_max_ms:
            continue
        result.append(comp)
    return result
