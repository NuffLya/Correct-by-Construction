from dataclasses import dataclass
from typing import Any

from .components_db import COMPONENTS, ComponentSpec, get_components_matching


@dataclass
class TopologyResult:
    primary_store: str
    cache: str | None
    message_queue: str | None
    satisfies_sla: bool
    reason: str


def solve_architecture(requirements: dict[str, Any]) -> TopologyResult:
    rps = requirements.get("rps_target", 100)
    consistency = requirements.get("consistency", "strong")
    durability = requirements.get("durability", "high")
    latency_p99 = requirements.get("latency_p99", 100)

    if consistency == "strong" and durability == "high":
        if rps <= 10000:
            return TopologyResult(
                primary_store="postgres",
                cache=None,
                message_queue=None,
                satisfies_sla=True,
                reason="Postgres satisfies: strong consistency, high durability, RPS",
            )
        if rps <= 100000:
            return TopologyResult(
                primary_store="postgres",
                cache="redis",
                message_queue=None,
                satisfies_sla=True,
                reason="Postgres + Redis: cache for higher RPS",
            )
        return TopologyResult(
            primary_store="postgres",
            cache="redis",
            message_queue="kafka",
            satisfies_sla=True,
            reason="Postgres + Redis + Kafka: high load",
        )

    if consistency == "eventual":
        if rps <= 100000:
            return TopologyResult(
                primary_store="redis",
                cache=None,
                message_queue=None,
                satisfies_sla=True,
                reason="Redis: eventual consistency, high RPS",
            )
        return TopologyResult(
            primary_store="redis",
            cache=None,
            message_queue="kafka",
            satisfies_sla=True,
            reason="Redis + Kafka: very high load",
        )

    return TopologyResult(
        primary_store="postgres",
        cache=None,
        message_queue=None,
        satisfies_sla=True,
        reason="Fallback: Postgres by default",
    )
