"""Reflect schemas/tables/columns/PK/FK from any SQLAlchemy-supported database."""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import inspect
from sqlalchemy.engine import Engine, create_engine


@dataclass
class ForeignKeyInfo:
    constrained_columns: list[str]
    referred_schema: str | None
    referred_table: str
    referred_columns: list[str]


@dataclass
class ColumnInfo:
    name: str
    type: str
    nullable: bool


@dataclass
class TableInfo:
    schema: str | None
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    pk_columns: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        return f"{self.schema}.{self.name}" if self.schema else self.name


def connect_engine(connection_string: str) -> Engine:
    return create_engine(connection_string, pool_pre_ping=True)


def _get_schema_names(inspector) -> list[str | None]:
    # Not every dialect supports multiple schemas (e.g. SQLite) — fall back to default.
    try:
        schemas = inspector.get_schema_names()
        return list(schemas) if schemas else [None]
    except NotImplementedError:
        return [None]


def reflect_all(engine: Engine) -> list[TableInfo]:
    inspector = inspect(engine)
    tables: list[TableInfo] = []

    for schema in _get_schema_names(inspector):
        for table_name in inspector.get_table_names(schema=schema):
            columns = [
                ColumnInfo(name=col["name"], type=str(col["type"]), nullable=col.get("nullable", True))
                for col in inspector.get_columns(table_name, schema=schema)
            ]

            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
            pk_columns = pk_constraint.get("constrained_columns") or []

            foreign_keys = [
                ForeignKeyInfo(
                    constrained_columns=fk["constrained_columns"],
                    referred_schema=fk.get("referred_schema"),
                    referred_table=fk["referred_table"],
                    referred_columns=fk["referred_columns"],
                )
                for fk in inspector.get_foreign_keys(table_name, schema=schema)
            ]

            tables.append(
                TableInfo(
                    schema=schema,
                    name=table_name,
                    columns=columns,
                    pk_columns=pk_columns,
                    foreign_keys=foreign_keys,
                )
            )

    return tables
