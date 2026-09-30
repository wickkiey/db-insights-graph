"""Persist reflected schema info to disk so repeat runs skip re-querying the database.

Point SCHEMA_CACHE_DIR at a mounted host folder (e.g. via `docker run -v`) to make
saved schemas survive container restarts.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict
from pathlib import Path

from db_introspect import ColumnInfo, ForeignKeyInfo, TableInfo

CACHE_DIR = Path(os.environ.get("SCHEMA_CACHE_DIR", "schema_cache"))

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_-]+")


def sanitize_name(name: str) -> str:
    # Collapse anything that isn't alnum/dash/underscore so names can't escape CACHE_DIR.
    cleaned = _SAFE_NAME_RE.sub("_", name.strip())
    return cleaned.strip("_.")


def _path_for(name: str) -> Path:
    return CACHE_DIR / f"{sanitize_name(name)}.json"


def list_cached_schemas() -> list[str]:
    if not CACHE_DIR.exists():
        return []
    return sorted(p.stem for p in CACHE_DIR.glob("*.json"))


def has_cached_schema(name: str) -> bool:
    return bool(name) and _path_for(name).exists()


def save_schema(name: str, tables: list[TableInfo]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"tables": [asdict(table) for table in tables]}
    _path_for(name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def delete_schema(name: str) -> None:
    _path_for(name).unlink(missing_ok=True)


def load_schema(name: str) -> list[TableInfo]:
    payload = json.loads(_path_for(name).read_text(encoding="utf-8"))
    tables = []
    for raw_table in payload["tables"]:
        tables.append(
            TableInfo(
                schema=raw_table["schema"],
                name=raw_table["name"],
                columns=[ColumnInfo(**col) for col in raw_table["columns"]],
                pk_columns=raw_table["pk_columns"],
                foreign_keys=[ForeignKeyInfo(**fk) for fk in raw_table["foreign_keys"]],
            )
        )
    return tables
