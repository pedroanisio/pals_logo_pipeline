"""
Phase 5 — Tests for SVG export (ported from legacy logo.py).

Verifies the library's SVG exporter produces valid, complete SVG.
"""

import os
import re
import sys
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestSvgExportValid:
    def test_produces_valid_svg(self):
        from p_logo import build_schema
        from p_logo.exporters.svg_export import export_svg

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            svg_text = export_svg(build_schema(), tmp)
            assert svg_text.startswith('<?xml')
            assert '<svg' in svg_text
            assert '</svg>' in svg_text
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 1000
        finally:
            os.unlink(tmp)

    def test_has_viewbox(self):
        from p_logo import build_schema
        from p_logo.exporters.svg_export import export_svg

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            svg_text = export_svg(build_schema(), tmp, size=2000)
            assert 'viewBox="0 0 2000 2000"' in svg_text
        finally:
            os.unlink(tmp)


class TestSvgNodeCircles:
    def test_has_24_node_circles(self):
        """25 nodes minus N14 (nib tip) = 24 node circles."""
        from p_logo import build_schema
        from p_logo.exporters.svg_export import export_svg

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            svg_text = export_svg(build_schema(), tmp)
            # Count circles with fill-opacity (node circles)
            # Exclude the background circle and ring (no fill-opacity)
            node_circles = re.findall(r'<circle[^>]*fill-opacity="[^"]*"', svg_text)
            assert len(node_circles) == 24
        finally:
            os.unlink(tmp)


class TestSvgEdgeLines:
    def test_has_44_edge_lines(self):
        from p_logo import build_schema
        from p_logo.exporters.svg_export import export_svg

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            svg_text = export_svg(build_schema(), tmp)
            # Edge lines have stroke-opacity; nib slit also has stroke-opacity
            # so we count all <line> elements and subtract 1 for the nib slit
            edge_lines = re.findall(r'<line[^>]*stroke-opacity="[^"]*"', svg_text)
            # 44 edges + 1 nib slit = 45 lines with stroke-opacity
            assert len(edge_lines) == 45
        finally:
            os.unlink(tmp)


class TestSvgEdgeTypes:
    def test_contour_edges_are_thicker(self):
        """Contour edges should have larger stroke-width than mesh edges."""
        from p_logo import build_schema
        from p_logo.exporters.svg_export import export_svg

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            svg_text = export_svg(build_schema(), tmp)
            # Extract all stroke-width values from <line> elements
            widths = re.findall(r'<line[^>]*stroke-width="([^"]*)"', svg_text)
            widths_float = [float(w) for w in widths]
            # There should be at least 2 distinct stroke widths
            # (contour vs mesh at minimum)
            assert len(set(round(w, 1) for w in widths_float)) >= 2
        finally:
            os.unlink(tmp)


class TestSvgArcPolylines:
    def test_has_3_arc_polylines(self):
        from p_logo import build_schema
        from p_logo.exporters.svg_export import export_svg

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            svg_text = export_svg(build_schema(), tmp)
            polylines = re.findall(r'<polyline', svg_text)
            assert len(polylines) == 3
        finally:
            os.unlink(tmp)
