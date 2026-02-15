from enum import Enum
from typing import Any


class BaseType(str, Enum):
    UUID = "UUID"
    STRING = "String"
    INT = "Int"
    INT64 = "Int64"
    DECIMAL = "Decimal"
    BOOLEAN = "Boolean"
    TIMESTAMP = "Timestamp"
    ENUM = "Enum"


GO_TYPE_MAP = {
    "UUID": "uuid.UUID",
    "uuid": "uuid.UUID",
    "String": "string",
    "string": "string",
    "Int": "int64",
    "int64": "int64",
    "Int64": "int64",
    "Decimal": "decimal.Decimal",
    "decimal": "decimal.Decimal",
    "Boolean": "bool",
    "bool": "bool",
    "Timestamp": "time.Time",
    "timestamp": "time.Time",
    "Enum": "string",
    "enum": "string",
}

SQL_TYPE_MAP = {
    "UUID": "UUID",
    "uuid": "UUID",
    "String": "VARCHAR(255)",
    "string": "VARCHAR(255)",
    "Int": "BIGINT",
    "int64": "BIGINT",
    "Int64": "BIGINT",
    "Decimal": "DECIMAL(18,2)",
    "decimal": "DECIMAL(18,2)",
    "Boolean": "BOOLEAN",
    "bool": "BOOLEAN",
    "Timestamp": "TIMESTAMP",
    "timestamp": "TIMESTAMP",
    "Enum": "VARCHAR(50)",
    "enum": "VARCHAR(50)",
}


def resolve_go_type(field_type: str, length: int | None = None, precision: int | None = None, scale: int | None = None) -> str:
    t = field_type.strip()
    base = GO_TYPE_MAP.get(t, "string")

    if t.lower() == "string" and length:
        return "string"
    if t.lower() in ("decimal", "decimal") and precision is not None and scale is not None:
        return "decimal.Decimal"
    if t.lower() == "enum":
        return "string"

    return base


def resolve_sql_type(
    field_type: str,
    length: int | None = None,
    precision: int | None = None,
    scale: int | None = None,
) -> str:
    t = field_type.strip().lower()
    if t == "string" and length:
        return f"VARCHAR({length})"
    if t in ("decimal", "decimal"):
        p, s = precision or 18, scale or 2
        return f"DECIMAL({p},{s})"
    return SQL_TYPE_MAP.get(field_type, "VARCHAR(255)")


def is_numeric_type(field_type: str) -> bool:
    t = field_type.lower()
    return t in ("int", "int64", "decimal", "real", "float")


def is_reference_type(field_type: str) -> bool:
    t = field_type.lower()
    return t in ("uuid",)


def normalize_type(field_type: str) -> str:
    t = field_type.strip()
    for k in GO_TYPE_MAP:
        if k.lower() == t.lower():
            return k
    return t
