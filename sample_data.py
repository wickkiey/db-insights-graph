"""Fetch a small sample of rows for a table, safely, via reflected SQLAlchemy Table objects."""
from __future__ import annotations

from sqlalchemy import MetaData, Table
from sqlalchemy.engine import Engine

from db_introspect import TableInfo


def fetch_sample_rows(engine: Engine, table_info: TableInfo, limit: int) -> list[dict]:
    metadata = MetaData()
    # autoload_with reflects the real table object so column/table names are never string-formatted into SQL.
    table = Table(table_info.name, metadata, schema=table_info.schema, autoload_with=engine)

    with engine.connect() as connection:
        result = connection.execute(table.select().limit(limit))
        return [dict(row._mapping) for row in result]
