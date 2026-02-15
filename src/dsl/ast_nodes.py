from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionStrategy(str, Enum):
    SIMPLE = "Simple"
    ACID_TRANSACTION = "ACID_Transaction"
    IDEMPOTENT = "Idempotent"


@dataclass
class Field:
    name: str
    type: str
    primary_key: bool = False
    indexed: bool = False
    foreign_key: str | None = None
    precision: int | None = None
    scale: int | None = None
    length: int | None = None
    values: list[str] | None = None


@dataclass
class Invariant:
    name: str
    expr: str
    severity: str = "error"


@dataclass
class Entity:
    name: str
    fields: list[Field] = field(default_factory=list)
    invariants: list[Invariant] = field(default_factory=list)


@dataclass
class Parameter:
    name: str
    type: str


@dataclass
class Contract:
    inputs: list[Parameter] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)


@dataclass
class Service:
    name: str
    contract: Contract
    strategy: ExecutionStrategy = ExecutionStrategy.SIMPLE
    isolation: str | None = None
    timeout: int | None = None
    retry_policy: str | None = None


@dataclass
class OpaqueBlock:
    name: str
    signature: Contract
    implementation: str
    binding: str | None = None


@dataclass
class Specification:
    name: str
    version: str
    entities: list[Entity] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)
    opaque_blocks: list[OpaqueBlock] = field(default_factory=list)


def spec_dict_to_ast(spec: dict[str, Any]) -> Specification:
    entities = []
    for e in spec.get("entities", []):
        fields = [
            Field(
                name=f.get("name", ""),
                type=f.get("type", "String"),
                primary_key=f.get("primary_key", False),
                indexed=f.get("indexed", False),
                foreign_key=f.get("foreign_key"),
                precision=f.get("precision"),
                scale=f.get("scale"),
                length=f.get("length"),
                values=f.get("values"),
            )
            for f in e.get("fields", [])
        ]
        invariants = [
            Invariant(
                name=inv.get("name", ""),
                expr=inv.get("expr", inv.get("expression", "")),
                severity=inv.get("severity", "error"),
            )
            for inv in e.get("invariants", [])
        ]
        entities.append(Entity(name=e.get("name", ""), fields=fields, invariants=invariants))

    services = []
    for s in spec.get("services", []):
        inputs = [
            Parameter(name=i.get("name", ""), type=i.get("type", "String"))
            for i in s.get("inputs", [])
        ]
        contract = Contract(
            inputs=inputs,
            preconditions=s.get("preconditions", []),
            postconditions=s.get("postconditions", []),
        )
        strategy_str = s.get("strategy", "Simple")
        try:
            strategy = ExecutionStrategy(strategy_str)
        except ValueError:
            strategy = ExecutionStrategy.SIMPLE
        services.append(
            Service(
                name=s.get("name", ""),
                contract=contract,
                strategy=strategy,
                isolation=s.get("isolation"),
                timeout=s.get("timeout"),
                retry_policy=s.get("retry_policy"),
            )
        )

    return Specification(
        name=spec.get("name", "UnnamedSystem"),
        version=spec.get("version", "1.0.0"),
        entities=entities,
        services=services,
    )
