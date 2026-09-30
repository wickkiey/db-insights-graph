"""Export reflected schema info into LLM-friendly Markdown and structured JSON."""
from __future__ import annotations

import json
from dataclasses import asdict

from db_introspect import TableInfo


def to_markdown(tables: list[TableInfo]) -> str:
    lines: list[str] = ["# Database Schema\n"]

    for table in tables:
        lines.append(f"## {table.qualified_name}\n")

        lines.append("| Column | Type | Nullable |")
        lines.append("|---|---|---|")
        for col in table.columns:
            lines.append(f"| {col.name} | {col.type} | {col.nullable} |")
        lines.append("")

        if table.pk_columns:
            lines.append(f"**Primary Key**: {', '.join(table.pk_columns)}\n")

        if table.foreign_keys:
            lines.append("**Foreign Keys**:")
            for fk in table.foreign_keys:
                referred = f"{fk.referred_schema}.{fk.referred_table}" if fk.referred_schema else fk.referred_table
                lines.append(
                    f"- {', '.join(fk.constrained_columns)} → {referred} ({', '.join(fk.referred_columns)})"
                )
            lines.append("")

    return "\n".join(lines)


def to_json(tables: list[TableInfo]) -> str:
    return json.dumps({"tables": [asdict(table) for table in tables]}, indent=2)
