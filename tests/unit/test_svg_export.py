"""
Regression tests for SVG export — palette-driven vector output.

Verifies the SVG exporter produces valid, complete SVG with:
  - Palette colors on nodes, edges, arcs
  - Multi-band ring (rose_gold, 4 bands)
  - Node glow halos
  - Arc bloom layers
  - Star field
  - Nebula clouds
  - Nib detail (outline, center line, ball)
  - Shimmer arcs on ring
"""

import math
import os
import re
import sys
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="module")
def schema():
    from p_logo import build_schema
    return build_schema()


@pytest.fixture(scope="module")
def svg_text(schema):
    from p_logo.exporters.svg_export import export_svg
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        tmp = f.name
    try:
        text = export_svg(schema, tmp)
        yield text
    finally:
        os.unlink(tmp)


@pytest.fixture(scope="module")
def palette():
    from p_logo_pipeline.palette import COLORS
    return COLORS


# ── Basic SVG validity ───────────────────────────────────────

class TestSvgValidity:
    def test_starts_with_xml_declaration(self, svg_text):
        assert svg_text.startswith("<?xml")

    def test_has_svg_root(self, svg_text):
        assert "<svg" in svg_text
        assert "</svg>" in svg_text

    def test_has_viewbox(self, svg_text):
        assert 'viewBox="0 0 2000 2000"' in svg_text

    def test_file_size_reasonable(self, schema):
        from p_logo.exporters.svg_export import export_svg
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            export_svg(schema, tmp)
            assert os.path.getsize(tmp) > 5000
        finally:
            os.unlink(tmp)

    def test_has_defs_section(self, svg_text):
        assert "<defs>" in svg_text
        assert "</defs>" in svg_text


# ── Background & circle fill ────────────────────────────────

class TestBackground:
    def test_uses_palette_background_color(self, svg_text, palette):
        bg_hex = palette["background"].hex
        assert f'fill="{bg_hex}"' in svg_text

    def test_uses_palette_deep_fill(self, svg_text, palette):
        deep_hex = palette["deep"].hex
        assert f'fill="{deep_hex}"' in svg_text


# ── Multi-band ring ─────────────────────────────────────────

class TestRing:
    def test_four_ring_bands(self, svg_text, palette):
        """Ring has 4 concentric bands, all rose_gold colored."""
        rose_gold = palette["rose_gold"].hex
        # Ring bands are <circle> with stroke=rose_gold and stroke-opacity
        ring_circles = re.findall(
            rf'<circle[^>]*stroke="{re.escape(rose_gold)}"[^>]*stroke-opacity="[^"]*"',
            svg_text,
        )
        assert len(ring_circles) == 4

    def test_ring_opacities_match_palette(self, svg_text, palette):
        from p_logo_pipeline.palette import OPACITY_DEFAULTS
        rose_gold = palette["rose_gold"].hex
        ring_opacities = OPACITY_DEFAULTS["ring"]

        # Extract opacity values from ring circles
        pattern = rf'<circle[^>]*stroke="{re.escape(rose_gold)}"[^>]*stroke-opacity="([^"]*)"'
        found = re.findall(pattern, svg_text)
        found_floats = [float(x) for x in found]

        expected = [
            ring_opacities["inner"],
            ring_opacities["mid_inner"],
            ring_opacities["mid_outer"],
            ring_opacities["outer"],
        ]
        assert found_floats == pytest.approx(expected, abs=0.01)


# ── Node colors ──────────────────────────────────────────────

class TestNodeColors:
    def _get_node_circles(self, svg_text):
        """Extract node core circles (those with fill-opacity matching core opacity)."""
        from p_logo_pipeline.palette import OPACITY_DEFAULTS
        core_op = OPACITY_DEFAULTS["node_core"]["base"]
        pattern = rf'<circle[^>]*fill="([^"]*)"[^>]*fill-opacity="{core_op}"'
        return re.findall(pattern, svg_text)

    def test_24_node_core_circles(self, svg_text):
        """25 nodes minus N14 (nib tip) = 24 node circles."""
        cores = self._get_node_circles(svg_text)
        assert len(cores) == 24

    def test_has_copper_nodes(self, svg_text, palette):
        """Most nodes are copper (teal-green)."""
        cores = self._get_node_circles(svg_text)
        copper_hex = palette["copper"].hex
        copper_count = sum(1 for c in cores if c == copper_hex)
        assert copper_count >= 5

    def test_has_amber_nodes(self, svg_text, palette):
        """Key nodes get amber."""
        cores = self._get_node_circles(svg_text)
        amber_hex = palette["amber"].hex
        assert amber_hex in cores

    def test_has_bronze_nodes(self, svg_text, palette):
        """Arc anchor nodes get bronze."""
        cores = self._get_node_circles(svg_text)
        bronze_hex = palette["bronze"].hex
        assert bronze_hex in cores

    def test_has_blue_glow_node(self, svg_text, palette):
        """Node 0 (corner accent) gets blue_glow."""
        cores = self._get_node_circles(svg_text)
        blue_hex = palette["blue_glow"].hex
        assert blue_hex in cores

    def test_no_plain_white_nodes(self, svg_text):
        """No nodes should be plain white anymore."""
        cores = self._get_node_circles(svg_text)
        assert "#ffffff" not in cores
        assert "#FFFFFF" not in cores

    def test_color_consistency_with_html_export(self, schema):
        """SVG node colors match HTML export node colors exactly."""
        from p_logo.exporters.html_export import schema_to_js_data
        from p_logo.exporters.node_colors import resolve_node_color, COLOR_KEY_TO_PALETTE
        from p_logo_pipeline.palette import COLORS

        js_data = schema_to_js_data(schema)

        for i, node in enumerate(schema.nodes):
            if node.id == 14:
                continue
            html_key = js_data["wireNodes"][i]["col"]
            svg_key = resolve_node_color(node)
            assert html_key == svg_key, f"Node {i}: HTML={html_key}, SVG={svg_key}"


# ── Node glows ───────────────────────────────────────────────

class TestNodeGlows:
    def test_24_glow_halos(self, svg_text):
        """Each visible node has a glow halo (filter=glow)."""
        glow_circles = re.findall(r'<circle[^>]*filter="url\(#glow\)"', svg_text)
        # 24 node glows + nib ball glow = 25
        assert len(glow_circles) == 25

    def test_glow_filter_defined(self, svg_text):
        assert 'id="glow"' in svg_text
        assert "feGaussianBlur" in svg_text


# ── Edges ────────────────────────────────────────────────────

class TestEdges:
    def test_44_edge_lines(self, svg_text, palette):
        """44 edges, all copper-colored."""
        copper_hex = palette["copper"].hex
        # Edge lines: <line> with stroke=copper
        edge_lines = re.findall(
            rf'<line[^>]*stroke="{re.escape(copper_hex)}"[^>]*stroke-opacity="[^"]*"',
            svg_text,
        )
        assert len(edge_lines) == 44

    def test_contour_edges_thicker_than_mesh(self, svg_text, palette):
        """Contour edges have larger stroke-width than mesh edges."""
        copper_hex = palette["copper"].hex
        pattern = rf'<line[^>]*stroke="{re.escape(copper_hex)}"[^>]*stroke-width="([^"]*)"'
        widths = [float(w) for w in re.findall(pattern, svg_text)]
        # At least 2 distinct widths (contour vs mesh)
        assert len(set(round(w, 1) for w in widths)) >= 2

    def test_edge_type_opacity_variation(self, svg_text, palette):
        """Different edge types have different opacities."""
        copper_hex = palette["copper"].hex
        pattern = rf'<line[^>]*stroke="{re.escape(copper_hex)}"[^>]*stroke-opacity="([^"]*)"'
        opacities = [float(o) for o in re.findall(pattern, svg_text)]
        assert len(set(round(o, 2) for o in opacities)) >= 2


# ── Arcs ─────────────────────────────────────────────────────

class TestArcs:
    def test_3_main_arc_polylines(self, svg_text):
        """3 colored arc strokes (no filter attribute)."""
        # Main arcs: polyline without filter attribute
        all_polylines = re.findall(r'<polyline[^>]*/>', svg_text)
        main_arcs = [p for p in all_polylines if 'filter=' not in p]
        assert len(main_arcs) == 3

    def test_3_bloom_arc_polylines(self, svg_text):
        """3 arc bloom layers (with arc-bloom filter)."""
        bloom_arcs = re.findall(r'<polyline[^>]*filter="url\(#arc-bloom\)"', svg_text)
        assert len(bloom_arcs) == 3

    def test_arc_colors_match_palette(self, svg_text, palette):
        """Arcs use amber, copper, bronze from palette."""
        amber = palette["amber"].hex
        copper = palette["copper"].hex
        bronze = palette["bronze"].hex

        # Main arcs (non-bloom polylines)
        all_polylines = re.findall(r'<polyline[^>]*/>', svg_text)
        main_arcs = [p for p in all_polylines if 'filter=' not in p]

        arc_colors = []
        for arc in main_arcs:
            m = re.search(r'stroke="([^"]*)"', arc)
            if m:
                arc_colors.append(m.group(1))

        assert arc_colors == [amber, copper, bronze]

    def test_bloom_filter_defined(self, svg_text):
        assert 'id="arc-bloom"' in svg_text


# ── Nib detail ───────────────────────────────────────────────

class TestNibDetail:
    def test_nib_outline_polygon(self, svg_text, palette):
        """Nib outline is rendered as a polygon with bronze stroke."""
        bronze = palette["bronze"].hex
        polygons = re.findall(rf'<polygon[^>]*stroke="{re.escape(bronze)}"', svg_text)
        assert len(polygons) == 1

    def test_nib_center_line_blue(self, svg_text, palette):
        """Nib center slit uses blue_glow color."""
        blue = palette["blue_glow"].hex
        blue_lines = re.findall(rf'<line[^>]*stroke="{re.escape(blue)}"', svg_text)
        assert len(blue_lines) == 1

    def test_nib_ball_warm_white(self, svg_text, palette):
        """Nib ball is warm_white: glow halo (with filter) + core (opacity 0.95)."""
        from p_logo_pipeline.palette import OPACITY_DEFAULTS
        warm = palette["warm_white"].hex
        core_op = OPACITY_DEFAULTS["nib_ball"]["core"]
        glow_op = OPACITY_DEFAULTS["nib_ball"]["glow"]

        # Glow halo: warm_white + filter=glow
        glow_circles = re.findall(
            rf'<circle[^>]*fill="{re.escape(warm)}"[^>]*filter="url\(#glow\)"',
            svg_text,
        )
        assert len(glow_circles) == 1

        # Core: warm_white + high opacity (0.95, distinct from star brightness max 0.8)
        core_circles = re.findall(
            rf'<circle[^>]*fill="{re.escape(warm)}"[^>]*fill-opacity="{core_op}"',
            svg_text,
        )
        assert len(core_circles) == 1


# ── Star field ───────────────────────────────────────────────

class TestStarField:
    def test_star_count(self, svg_text, palette):
        """180 star points inside the circle (warm_white, no filter, opacity < 0.9)."""
        from p_logo_pipeline.palette import STAR_SPECS
        warm = palette[STAR_SPECS["color"]].hex
        # Stars: warm_white circles without filter attribute
        # (nib glow has filter="url(#glow)", nib core has opacity 0.95)
        all_warm_circles = re.findall(
            rf'<circle[^>]*fill="{re.escape(warm)}"[^>]*/?>',
            svg_text,
        )
        stars = [c for c in all_warm_circles
                 if "filter=" not in c and 'fill-opacity="0.95"' not in c]
        assert len(stars) == STAR_SPECS["count"]

    def test_deterministic(self, schema):
        """Two exports produce identical SVG."""
        from p_logo.exporters.svg_export import export_svg
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f1:
            tmp1 = f1.name
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f2:
            tmp2 = f2.name
        try:
            svg1 = export_svg(schema, tmp1)
            svg2 = export_svg(schema, tmp2)
            assert svg1 == svg2
        finally:
            os.unlink(tmp1)
            os.unlink(tmp2)


# ── Nebula clouds ────────────────────────────────────────────

class TestNebulaClouds:
    def test_nebula_count(self, svg_text):
        from p_logo_pipeline.palette import NEBULA_SPECS
        nebula_refs = re.findall(r'fill="url\(#nebula-\d+\)"', svg_text)
        assert len(nebula_refs) == NEBULA_SPECS["count"]

    def test_nebula_gradients_defined(self, svg_text):
        from p_logo_pipeline.palette import NEBULA_SPECS
        for i in range(NEBULA_SPECS["count"]):
            assert f'id="nebula-{i}"' in svg_text


# ── Shimmer arcs ─────────────────────────────────────────────

class TestShimmerArcs:
    def test_shimmer_count(self, svg_text):
        from p_logo_pipeline.palette import SHIMMER_SPECS
        shimmer_paths = re.findall(r'<path[^>]*stroke-opacity="0\.035"', svg_text)
        assert len(shimmer_paths) == SHIMMER_SPECS["count"]


# ── No white-only remnants ───────────────────────────────────

class TestNoMonochrome:
    def test_no_ffffff_node_fill(self, svg_text):
        """Nodes must not be plain #ffffff (old monochrome behavior)."""
        from p_logo_pipeline.palette import OPACITY_DEFAULTS
        core_op = OPACITY_DEFAULTS["node_core"]["base"]
        pattern = rf'<circle[^>]*fill="#ffffff"[^>]*fill-opacity="{core_op}"'
        assert not re.findall(pattern, svg_text)

    def test_no_ffffff_edge_stroke(self, svg_text):
        """Edges must not be plain #ffffff."""
        white_edges = re.findall(r'<line[^>]*stroke="#ffffff"', svg_text)
        assert len(white_edges) == 0

    def test_no_ffffff_arc_stroke(self, svg_text):
        """Arcs must not be plain #ffffff."""
        white_arcs = re.findall(r'<polyline[^>]*stroke="#ffffff"', svg_text)
        assert len(white_arcs) == 0


# ── Shared color module ──────────────────────────────────────

class TestNodeColorModule:
    """Verify the shared node_colors module works identically for both exporters."""

    def test_resolve_returns_valid_keys(self, schema):
        from p_logo.exporters.node_colors import resolve_node_color, COLOR_KEY_TO_PALETTE
        for node in schema.nodes:
            key = resolve_node_color(node)
            assert key in COLOR_KEY_TO_PALETTE, f"Unknown color key: {key}"

    def test_node_0_blueglow(self, schema):
        from p_logo.exporters.node_colors import resolve_node_color
        assert resolve_node_color(schema.node(0)) == "BLUEGLOW"

    def test_node_1_amber(self, schema):
        from p_logo.exporters.node_colors import resolve_node_color
        assert resolve_node_color(schema.node(1)) == "AMBER"

    def test_node_14_warmwht(self, schema):
        from p_logo.exporters.node_colors import resolve_node_color
        assert resolve_node_color(schema.node(14)) == "WARMWHT"

    def test_node_17_bronze(self, schema):
        from p_logo.exporters.node_colors import resolve_node_color
        assert resolve_node_color(schema.node(17)) == "BRONZE"

    def test_node_24_amber(self, schema):
        from p_logo.exporters.node_colors import resolve_node_color
        assert resolve_node_color(schema.node(24)) == "AMBER"

    def test_arc_styles_count(self):
        from p_logo.exporters.node_colors import ARC_STYLES
        assert len(ARC_STYLES) == 3

    def test_arc_styles_colors(self):
        from p_logo.exporters.node_colors import ARC_STYLES
        assert ARC_STYLES[0]["color"] == "AMBER"
        assert ARC_STYLES[1]["color"] == "COPPER"
        assert ARC_STYLES[2]["color"] == "BRONZE"
