"""Streamlit app: connect to any SQLAlchemy DB, explore its schema graph, export for LLMs."""
from __future__ import annotations

import os

import streamlit as st
from sqlalchemy.engine.url import make_url

from connections import delete_connection, list_connection_names, load_connection, save_connection
from db_introspect import TableInfo, connect_engine, reflect_all
from exporters import to_json, to_markdown
from graph3d_component import graph3d
from graph_builder import build_graph, to_force_graph_data
from sample_data import fetch_sample_rows
from schema_cache import delete_schema, has_cached_schema, list_cached_schemas, load_schema, save_schema

st.set_page_config(page_title="DB Relations Graph", layout="wide")

if "tables" not in st.session_state:
    st.session_state.tables = None
    st.session_state.engine = None
    st.session_state.selected_node = None
    st.session_state.auto_connect_attempted = False

# Allow the connection string/schema name to be provided via env vars (e.g. set by
# the Docker entrypoint) so the container can auto-connect on first load.
env_connection_string = os.environ.get("DB_CONNECTION_STRING", "")
env_schema_name = os.environ.get("SCHEMA_NAME", "")

if "conn_str_input" not in st.session_state:
    st.session_state.conn_str_input = env_connection_string
if "schema_name_input" not in st.session_state:
    st.session_state.schema_name_input = env_schema_name


def _load_saved_connection() -> None:
    name = st.session_state.get("saved_connection_picker")
    if name:
        st.session_state.conn_str_input = load_connection(name) or ""
        st.session_state.schema_name_input = name


with st.sidebar:
    st.header("Connection")
    connection_string = st.text_input(
        "SQLAlchemy connection string", key="conn_str_input", type="password"
    )
    schema_name = st.text_input(
        "Name (used to save/load both the connection and its cached graph)",
        key="schema_name_input",
    )
    connect_clicked = st.button("Connect")
    refresh_clicked = st.button("Refresh from database", help="Ignore any cached copy and re-fetch from the DB.")

    saved_connection_names = list_connection_names()
    if saved_connection_names:
        st.header("Saved connections")
        st.selectbox("Previously saved connections", saved_connection_names, key="saved_connection_picker")
        load_col, delete_col = st.columns(2)
        load_col.button("Load", key="load_saved_connection", on_click=_load_saved_connection)
        if delete_col.button("Delete", key="delete_saved_connection"):
            delete_connection(st.session_state.saved_connection_picker)
            st.rerun()

    cached_names = list_cached_schemas()
    if cached_names:
        st.header("Saved schema graphs")
        selected_cached_name = st.selectbox("Previously saved schema graphs", cached_names)
        load_col, delete_col = st.columns(2)
        load_cached_clicked = load_col.button("Load", key="load_saved_schema")
        if delete_col.button("Delete", key="delete_saved_schema"):
            delete_schema(selected_cached_name)
            st.rerun()
    else:
        selected_cached_name = None
        load_cached_clicked = False

    st.header("Sample rows")
    show_samples = st.toggle("Fetch sample rows", value=True)
    sample_limit = st.number_input("Rows to fetch", min_value=1, max_value=100, value=5)

auto_connect = (
    not st.session_state.auto_connect_attempted
    and env_connection_string
    and st.session_state.tables is None
)

if load_cached_clicked and selected_cached_name:
    st.session_state.tables = load_schema(selected_cached_name)
    st.session_state.engine = None
    st.session_state.selected_node = None

if connect_clicked or refresh_clicked or auto_connect:
    st.session_state.auto_connect_attempted = True
    active_connection_string = connection_string or env_connection_string
    if not active_connection_string:
        st.sidebar.error("Enter a connection string first.")
    elif not refresh_clicked and schema_name and has_cached_schema(schema_name):
        # Reuse the cached reflection — still connect (cheap, lazy) so sample rows work.
        st.session_state.tables = load_schema(schema_name)
        st.session_state.engine = connect_engine(active_connection_string)
        st.session_state.selected_node = None
        save_connection(schema_name, active_connection_string)
    else:
        try:
            engine = connect_engine(active_connection_string)
            tables = reflect_all(engine)
            st.session_state.tables = tables
            st.session_state.engine = engine
            st.session_state.selected_node = None
            if schema_name:
                save_schema(schema_name, tables)
                save_connection(schema_name, active_connection_string)
        except Exception as exc:
            # Never echo the raw connection string back — it may contain a password.
            safe_url = make_url(active_connection_string).render_as_string(hide_password=True)
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
                if st.session_state.engine is None:
                    st.info("No live database connection (loaded from a saved schema) — sample rows unavailable.")
                else:
                    try:
                        rows = fetch_sample_rows(st.session_state.engine, table, int(sample_limit))
                        st.dataframe(rows)
                    except Exception as exc:
                        st.error(f"Could not fetch sample rows: {exc}")
