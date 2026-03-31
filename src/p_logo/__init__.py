"""P Logo — geometric construction of the letter P.

Usage:
    from p_logo import build_schema
    schema = build_schema()

    # Export
    from p_logo.exporters.json_export import export_json
    from p_logo.exporters.svg_export import export_svg
    from p_logo.exporters.gif_export import export_gif

    # Render
    from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer
    from p_logo.renderers.cairo_crafted import CairoCraftedRenderer
    from p_logo.renderers.v16_technical import V16TechnicalRenderer
"""

from p_logo.types import Node, Edge, Arc, NibGeometry, PLogoSchema
from p_logo.schema import build_schema

__all__ = [
    "build_schema",
    "PLogoSchema", "Node", "Edge", "Arc", "NibGeometry",
]
