"""
Regression tests for MEDIUM priority refactors:
  1. schema.py:build_schema()
  2. matplotlib_bw.py:render()
  3. gif_export.py:render_frame()
  4. layout.py:_build_nib_elements()

Locks current behavior before decomposition.
"""

import json
import sys
import hashlib
import tempfile
import math
import pytest
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

BUILD_DIR = ROOT / "src" / "p_logo_pipeline" / "build"


# ──────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def schema():
    from p_logo import build_schema
    return build_schema()


@pytest.fixture(scope="module")
def layout_data():
    data = {}
    for name in ("palette.json", "graph.json", "nib.json", "arcs.json"):
        with open(BUILD_DIR / name) as f:
            data[name] = json.load(f)
    return data


@pytest.fixture(scope="module")
def layout(layout_data):
    from p_logo_pipeline.layout import build_layout
    return build_layout(
        layout_data["palette.json"], layout_data["graph.json"],
        layout_data["nib.json"], layout_data["arcs.json"],
    )


# ══════════════════════════════════════════════════════
# 1. schema.py:build_schema()
# ══════════════════════════════════════════════════════

class TestSchemaStructure:
    def test_node_count(self, schema):
        assert len(schema.nodes) == 25

    def test_edge_count(self, schema):
        assert len(schema.edges) == 44

    def test_arc_count(self, schema):
        assert len(schema.arcs) == 3

    def test_nib_outline_length(self, schema):
        assert len(schema.nib.outline) == 5

    def test_nib_has_slit(self, schema):
        assert schema.nib.slit_start is not None
        assert schema.nib.slit_end is not None

    def test_nib_has_ball(self, schema):
        assert schema.nib.ball_pos is not None

    def test_has_composition(self, schema):
        assert schema.composition is not None
        assert "shapes" in schema.composition
        assert "points" in schema.composition


class TestSchemaSqrt2Chain:
    def test_r_blue(self, schema):
        assert schema.r_blue == pytest.approx(schema.r_green / math.sqrt(2))

    def test_r_gold(self, schema):
        assert schema.r_gold == pytest.approx(schema.r_green * math.sqrt(2))

    def test_r_vertex(self, schema):
        assert schema.r_vertex == pytest.approx(schema.r_gold - schema.r_green)

    def test_r_blue_value(self, schema):
        assert schema.r_blue == pytest.approx(0.869953472893809)

    def test_r_gold_value(self, schema):
        assert schema.r_gold == pytest.approx(1.7399069457876184)


class TestSchemaEdgeTypes:
    def test_contour_edges(self, schema):
        contour = [e for e in schema.edges if e.edge_type == "contour"]
        assert len(contour) == 6

    def test_struct_edges(self, schema):
        struct = [e for e in schema.edges if e.edge_type == "struct"]
        assert len(struct) == 4

    def test_nib_edges(self, schema):
        nib = [e for e in schema.edges if e.edge_type == "nib"]
        assert len(nib) == 14

    def test_mesh_edges(self, schema):
        mesh = [e for e in schema.edges if e.edge_type == "mesh"]
        assert len(mesh) == 20


class TestSchemaArcs:
    def test_arc_names(self, schema):
        names = [a.name for a in schema.arcs]
        assert names == ["Green", "Blue", "Gold"]

    def test_arcs_are_semicircles(self, schema):
        for arc in schema.arcs:
            assert arc.sweep_angle == pytest.approx(math.pi)


class TestSchemaDeterminism:
    def test_output_is_deterministic(self):
        from p_logo import build_schema
        s1 = build_schema()
        s2 = build_schema()
        assert s1.nodes == s2.nodes
        assert s1.edges == s2.edges
        assert s1.arcs == s2.arcs

    def test_custom_params(self):
        from p_logo import build_schema
        s = build_schema(center=(0.0, 0.0), r_green=1.0)
        assert len(s.nodes) == 25
        assert s.r_green == 1.0
        assert s.r_blue == pytest.approx(1.0 / math.sqrt(2))


# ══════════════════════════════════════════════════════
# 2. matplotlib_bw.py:render()
# ══════════════════════════════════════════════════════

class TestMatplotlibBWRenderer:
    def test_renders_dark(self, schema):
        from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer
        r = MatplotlibBWRenderer(schema)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            r.render(tmp, dpi=72, size=200)
            assert Path(tmp).stat().st_size > 3000
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_renders_inverted(self, schema):
        from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer
        r = MatplotlibBWRenderer(schema)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            r.render(tmp, dpi=72, size=200, bg="#ffffff", invert=True)
            assert Path(tmp).stat().st_size > 100
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_no_leftover_raw_file(self, schema):
        from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer
        r = MatplotlibBWRenderer(schema)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            r.render(tmp, dpi=72, size=200)
            assert not Path(tmp + "_raw.png").exists()
        finally:
            Path(tmp).unlink(missing_ok=True)


# ══════════════════════════════════════════════════════
# 3. gif_export.py:render_frame()
# ══════════════════════════════════════════════════════

class TestRenderFrame:
    def test_returns_rgb_image(self, schema):
        from p_logo.exporters.gif_export import render_frame
        img = render_frame(schema, phase=0.0, size=200, dpi=50)
        assert img.mode == "RGB"

    def test_correct_size(self, schema):
        from p_logo.exporters.gif_export import render_frame
        img = render_frame(schema, phase=0.0, size=200, dpi=50)
        assert img.size == (200, 200)

    def test_works_across_phases(self, schema):
        from p_logo.exporters.gif_export import render_frame
        for phase in [0.0, 0.25, 0.5, 0.75]:
            img = render_frame(schema, phase=phase, size=100, dpi=50)
            assert img.size == (100, 100)

    def test_custom_palette(self, schema):
        from p_logo.exporters.gif_export import render_frame
        palette = {
            "copper": "#5a9e8c", "amber": "#e8a84c", "bronze": "#b87a4e",
            "rosegold": "#c4876e", "warmwht": "#ffecd2", "blueglow": "#5b8fd4",
        }
        img = render_frame(schema, phase=0.0, size=100, dpi=50, palette=palette)
        assert img.size == (100, 100)


class TestExportGif:
    def test_creates_gif_file(self, schema):
        from p_logo.exporters.gif_export import export_gif
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
            tmp = f.name
        try:
            export_gif(schema, tmp, n_frames=4, size=100, dpi=50)
            assert Path(tmp).stat().st_size > 1000
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_gif_is_valid(self, schema):
        from p_logo.exporters.gif_export import export_gif
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
            tmp = f.name
        try:
            export_gif(schema, tmp, n_frames=4, size=100, dpi=50)
            img = Image.open(tmp)
            assert img.format == "GIF"
        finally:
            Path(tmp).unlink(missing_ok=True)


# ══════════════════════════════════════════════════════
# 4. layout.py:_build_nib_elements()
# ══════════════════════════════════════════════════════

class TestNibElements:
    def test_total_nib_element_count(self, layout):
        nib_types = {"nib_fan_line", "nib_outline_line", "nib_center_line",
                     "nib_accent_node", "junction_ball", "ink_origin"}
        nib_els = [e for e in layout["elements"] if e["type"] in nib_types]
        assert len(nib_els) == 17

    def test_fan_line_count(self, layout):
        fans = [e for e in layout["elements"] if e["type"] == "nib_fan_line"]
        assert len(fans) == 6

    def test_outline_line_count(self, layout):
        outlines = [e for e in layout["elements"] if e["type"] == "nib_outline_line"]
        assert len(outlines) == 4

    def test_center_line_count(self, layout):
        centers = [e for e in layout["elements"] if e["type"] == "nib_center_line"]
        assert len(centers) == 1

    def test_accent_node_count(self, layout):
        accents = [e for e in layout["elements"] if e["type"] == "nib_accent_node"]
        assert len(accents) == 4

    def test_junction_ball_count(self, layout):
        balls = [e for e in layout["elements"] if e["type"] == "junction_ball"]
        assert len(balls) == 1

    def test_ink_origin_count(self, layout):
        origins = [e for e in layout["elements"] if e["type"] == "ink_origin"]
        assert len(origins) == 1

    def test_all_nib_elements_have_z(self, layout):
        nib_types = {"nib_fan_line", "nib_outline_line", "nib_center_line",
                     "nib_accent_node", "junction_ball", "ink_origin"}
        for e in layout["elements"]:
            if e["type"] in nib_types:
                assert "z" in e, f"Element {e['type']} missing z"

    def test_junction_ball_has_glow_fields(self, layout):
        ball = [e for e in layout["elements"] if e["type"] == "junction_ball"][0]
        assert "glow_size" in ball
        assert "glow_color" in ball
        assert "bloom_size" in ball


class TestLayoutDeterminism:
    def test_layout_hash(self, layout):
        h = hashlib.sha256(json.dumps(layout, sort_keys=True).encode()).hexdigest()
        assert h[:16] == "e0b13732d87d7227"
