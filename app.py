"""Streamlit app: connect to any SQLAlchemy DB, explore its schema graph, export for LLMs."""
from __future__ import annotations

import streamlit as st
from sqlalchemy.engine.url import make_url

from db_introspect import TableInfo, connect_engine, reflect_all
from exporters import to_json, to_markdown
from graph3d_component import graph3d
from graph_builder import build_graph, to_force_graph_data
from sample_data import fetch_sample_rows

st.set_page_config(page_title="DB Relations Graph", layout="wide")

if "tables" not in st.session_state:
    st.session_state.tables = None
    st.session_state.engine = None
    st.session_state.selected_node = None

with st.sidebar:
    st.header("Connection")
    connection_string = st.text_input("SQLAlchemy connection string", type="password")
    connect_clicked = st.button("Connect")

    st.header("Sample rows")
    show_samples = st.toggle("Fetch sample rows", value=True)
    sample_limit = st.number_input("Rows to fetch", min_value=1, max_value=100, value=5)

if connect_clicked:
    if not connection_string:
        st.sidebar.error("Enter a connection string first.")
    else:
        try:
            engine = connect_engine(connection_string)
            st.session_state.tables = reflect_all(engine)
            st.session_state.engine = engine
            st.session_state.selected_node = None
        except Exception as exc:
            # Never echo the raw connection string back — it may contain a password.
            safe_url = make_url(connection_string).render_as_string(hide_password=True)
            st.sidebar.error(f"Failed to connect to {safe_url}: {exc}")

tables: list[TableInfo] | None = st.session_state.tables

if not tables:
    st.info("Enter a connection string and click Connect to get started.")
else:
    tables_by_name = {t.qualified_name: t for t in tables}
    graph = build_graph(tables)
    nodes, links = to_force_graph_data(graph)

    with st.sidebar:
        st.header("Export for LLM")
        st.download_button("Download Markdown", to_markdown(tables), file_name="schema.md")
        st.download_button("Download JSON", to_json(tables), file_name="schema.json")

    if len(tables) > 150:
        st.warning(f"{len(tables)} tables reflected — graph rendering may be slow.")

    # Full-width WebGL 3D graph (three.js via 3d-force-graph) — drag to orbit, scroll to zoom, click a node to inspect it.
    clicked_node = graph3d(nodes=nodes, links=links, height=650, key="graph3d")
    if clicked_node:
        st.session_state.selected_node = clicked_node

    st.divider()

    detail_col, _spacer = st.columns([2, 1])
    with detail_col:
        st.subheader("Table details")
        selected_name = st.session_state.selected_node
        if not selected_name or selected_name not in tables_by_name:
            st.write("Click a node in the graph to see its details.")
        else:
            table = tables_by_name[selected_name]
            st.markdown(f"### {table.qualified_name}")

            st.write("**Columns**")
            st.table(
                [{"name": c.name, "type": c.type, "nullable": c.nullable} for c in table.columns]
            )

            if table.pk_columns:
                st.write(f"**Primary Key**: {', '.join(table.pk_columns)}")

            if table.foreign_keys:
                st.write("**References (outgoing)**")
                for fk in table.foreign_keys:
                    referred = (
                        f"{fk.referred_schema}.{fk.referred_table}" if fk.referred_schema else fk.referred_table
                    )
                    st.write(f"- {', '.join(fk.constrained_columns)} → {referred} ({', '.join(fk.referred_columns)})")

            incoming = [
                (other.qualified_name, fk)
                for other in tables
                for fk in other.foreign_keys
                if (f"{fk.referred_schema}.{fk.referred_table}" if fk.referred_schema else fk.referred_table)
                == selected_name
            ]
            if incoming:
                st.write("**Referenced by (incoming)**")
                for other_name, fk in incoming:
                    st.write(f"- {other_name} ({', '.join(fk.constrained_columns)} → {', '.join(fk.referred_columns)})")

            if show_samples:
                st.write("**Sample rows**")
                try:
                    rows = fetch_sample_rows(st.session_state.engine, table, int(sample_limit))
                    st.dataframe(rows)
                except Exception as exc:
                    st.error(f"Could not fetch sample rows: {exc}")
