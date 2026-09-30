"""Persist named connection strings locally so multiple DBs can be reopened by name.

WARNING: connection strings (including any embedded password) are stored in
plain text under CONNECTIONS_FILE. Only use this on trusted machines/volumes.
"""
from __future__ import annotations

import json
from pathlib import Path

from schema_cache import CACHE_DIR, sanitize_name

CONNECTIONS_DIR = CACHE_DIR / "_connections"
CONNECTIONS_FILE = CONNECTIONS_DIR / "connections.json"


def _read_all() -> dict[str, str]:
    if not CONNECTIONS_FILE.exists():
        return {}
    return json.loads(CONNECTIONS_FILE.read_text(encoding="utf-8"))


def list_connection_names() -> list[str]:
    return sorted(_read_all().keys())


def save_connection(name: str, connection_string: str) -> None:
    key = sanitize_name(name)
    if not key:
        return
    CONNECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    connections = _read_all()
    connections[key] = connection_string
    CONNECTIONS_FILE.write_text(json.dumps(connections, indent=2), encoding="utf-8")


def load_connection(name: str) -> str | None:
    return _read_all().get(sanitize_name(name))


def delete_connection(name: str) -> None:
    connections = _read_all()
    connections.pop(sanitize_name(name), None)
    CONNECTIONS_FILE.write_text(json.dumps(connections, indent=2), encoding="utf-8")
