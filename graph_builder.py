"""Build a networkx graph from reflected tables and convert it for the 3D force-graph view."""
from __future__ import annotations

import networkx as nx

from db_introspect import TableInfo


def build_graph(tables: list[TableInfo]) -> nx.DiGraph:
    graph = nx.DiGraph()

    for table in tables:
        graph.add_node(table.qualified_name, table_info=table)

    for table in tables:
        for fk in table.foreign_keys:
            referred_qualified_name = (
                f"{fk.referred_schema}.{fk.referred_table}" if fk.referred_schema else fk.referred_table
            )
            if referred_qualified_name in graph.nodes:
                graph.add_edge(
                    table.qualified_name,
                    referred_qualified_name,
                    constrained_columns=fk.constrained_columns,
                    referred_columns=fk.referred_columns,
                )

    return graph


def to_force_graph_data(graph: nx.DiGraph) -> tuple[list[dict], list[dict]]:
    """Convert to the plain node/link dicts expected by 3d-force-graph."""
    nodes = [
        {"id": node_id, "label": node_id, "group": node_id.split(".")[0]}
        for node_id in graph.nodes
    ]

    links = [
        {
            "source": source,
            "target": target,
            "label": "→".join(data["constrained_columns"]),
        }
        for source, target, data in graph.edges(data=True)
    ]

    return nodes, links
