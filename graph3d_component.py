"""Static (no-build) Streamlit component wrapping 3d-force-graph (three.js/WebGL)."""
import os

import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph3d_frontend")
_component_func = components.declare_component("graph3d", path=_COMPONENT_DIR)


def graph3d(nodes: list[dict], links: list[dict], height: int = 650, key: str | None = None):
    """Render a 3D force graph; returns the clicked node's id (or None)."""
    return _component_func(nodes=nodes, links=links, height=height, key=key, default=None)
