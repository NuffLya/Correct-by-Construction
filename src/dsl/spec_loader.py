from pathlib import Path
from typing import Any, Union

import yaml
from pydantic import BaseModel, Field, field_validator


class FieldSpec(BaseModel):
    name: str
    type: str = "String"
    primary_key: bool = False
    indexed: bool = False
    foreign_key: str | None = None
    precision: int | None = None
    scale: int | None = None
    length: int | None = None
    values: list[str] | None = None

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: Any) -> str:
        if isinstance(v, str):
            return v
        return str(v)


class InvariantSpec(BaseModel):
    name: str
    expr: str = Field(...)
    severity: str = "error"

    @field_validator("expr", mode="before")
    @classmethod
    def expr_from_expression(cls, v: Any) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, dict) and "expression" in v:
            return v["expression"]
        return str(v)


class EntitySpec(BaseModel):
    name: str
    fields: list[FieldSpec] = Field(default_factory=list)
    invariants: list[InvariantSpec] = Field(default_factory=list)


class InputSpec(BaseModel):
    name: str
    type: str = "String"


class ServiceSpec(BaseModel):
    name: str
    inputs: list[InputSpec] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    strategy: str = "Simple"
    isolation: str | None = None
    timeout: int | None = None
    retry_policy: str | None = None

    @field_validator("inputs", mode="before")
    @classmethod
    def normalize_inputs(cls, v: Any) -> list[dict]:
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    result.append(item)
                elif isinstance(item, str):
                    if ":" in item:
                        name, t = item.split(":", 1)
                        result.append({"name": name.strip(), "type": t.strip()})
                    else:
                        result.append({"name": item, "type": "String"})
            return result
        return v or []


class ArchitectureRequirements(BaseModel):
    rps_target: int = 100
    consistency: str = "strong"
    durability: str = "high"
    latency_p99: int = 100


class ArchitectureSpec(BaseModel):
    requirements: ArchitectureRequirements = Field(default_factory=ArchitectureRequirements)


class SpecModel(BaseModel):
    name: str = "UnnamedSystem"
    version: str = "1.0.0"
    entities: list[EntitySpec] = Field(default_factory=list)
    services: list[ServiceSpec] = Field(default_factory=list)
    architecture: ArchitectureSpec | None = None

    @field_validator("entities", mode="before")
    @classmethod
    def normalize_entities(cls, v: Any) -> list:
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    if "fields" in item:
                        result.append(item)
                    else:
                        result.append({"name": item.get("name", "Entity"), "fields": [], "invariants": []})
                else:
                    result.append({"name": str(item), "fields": [], "invariants": []})
            return result
        return []


def load_spec(source: Union[str, Path]) -> dict[str, Any]:
    if isinstance(source, Path):
        source = source.read_text(encoding="utf-8")
    elif isinstance(source, str) and Path(source).exists():
        source = Path(source).read_text(encoding="utf-8")

    try:
        raw = yaml.safe_load(source)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error: {e}") from e

    if not isinstance(raw, dict):
        raise ValueError("Specification must be a YAML object (dict)")

    model = SpecModel.model_validate(raw)
    return model.model_dump()


def validate_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        SpecModel.model_validate(spec)
    except Exception as e:
        errors.append(str(e))

    return errors
