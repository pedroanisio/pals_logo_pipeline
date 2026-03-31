"""
Regression tests for HIGH priority refactors:
  1. cairo_crafted.py:_draw()
  2. v16_technical.py:render()
  3. point_field.py:generate_field()
  4. validate_step.py:_run_checks()

Each test locks current behavior before the refactor.
"""

import json
import sys
import hashlib
import tempfile
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

BUILD_DIR = ROOT / "src" / "p_logo_pipeline" / "build"
LOGOS_DIR = ROOT / "build" / "logos"


# ──────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def schema():
    from p_logo import build_schema
    return build_schema()


@pytest.fixture(scope="module")
def field():
    from p_logo_pipeline.point_field import generate_field
    return generate_field()


@pytest.fixture(scope="module")
def pipeline_data():
    data = {}
    for name in ("palette.json", "graph.json", "nib.json", "arcs.json",
                  "layout.json", "animations.json"):
        with open(BUILD_DIR / name) as f:
            data[name] = json.load(f)
    return data


@pytest.fixture(scope="module")
def validation_report(pipeline_data):
    from p_logo_pipeline.validate_step import build_report
    with open(LOGOS_DIR / "p_logo_pipeline.html") as f:
        html = f.read()
    return build_report(
        pipeline_data["palette.json"], pipeline_data["graph.json"],
        pipeline_data["nib.json"], pipeline_data["arcs.json"],
        pipeline_data["layout.json"], pipeline_data["animations.json"],
        html,
    )


# ══════════════════════════════════════════════════════
# 1. CairoCraftedRenderer
# ══════════════════════════════════════════════════════

class TestCairoCraftedRenderer:
    def _skip_if_no_cairo(self):
        from p_logo.renderers.cairo_crafted import HAS_CAIRO
        if not HAS_CAIRO:
            pytest.skip("pycairo not installed")

    def test_renders_dark_mode(self, schema):
        self._skip_if_no_cairo()
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer
        r = CairoCraftedRenderer(schema)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            r.render(tmp, size=400)
            assert Path(tmp).stat().st_size > 5000
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_renders_transparent(self, schema):
        self._skip_if_no_cairo()
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer
        r = CairoCraftedRenderer(schema)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            r.render(tmp, size=400, transparent=True)
            assert Path(tmp).stat().st_size > 3000
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_renders_debug(self, schema):
        self._skip_if_no_cairo()
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer
        r = CairoCraftedRenderer(schema)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            r.render(tmp, size=400, debug=True)
            assert Path(tmp).stat().st_size > 3000
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_has_expected_methods(self, schema):
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer
        r = CairoCraftedRenderer(schema)
        assert hasattr(r, 'render')
        assert hasattr(r, '_draw')


# ══════════════════════════════════════════════════════
# 2. V16TechnicalRenderer
# ══════════════════════════════════════════════════════

class TestV16TechnicalRenderer:
    def test_renders_default(self, schema):
        from p_logo.renderers.v16_technical import V16TechnicalRenderer
        r = V16TechnicalRenderer(schema)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            r.render(tmp, dpi=72)
            assert Path(tmp).stat().st_size > 10000
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_has_expected_methods(self, schema):
        from p_logo.renderers.v16_technical import V16TechnicalRenderer
        r = V16TechnicalRenderer(schema)
        assert hasattr(r, 'render')


# ══════════════════════════════════════════════════════
# 3. point_field.generate_field()
# ══════════════════════════════════════════════════════

class TestPointFieldStructure:
    def test_shape_count(self, field):
        assert len(field["shapes"]) == 9

    def test_point_count(self, field):
        assert len(field["points"]) == 76

    def test_has_metadata(self, field):
        assert "metadata" in field
        m = field["metadata"]
        assert m["counts"]["shapes"] == 9
        assert m["counts"]["points"] == 76

    def test_has_meta_descriptor(self, field):
        assert field["_meta"]["name"] == "point_field"

    def test_shape_keys(self, field):
        expected = {"Circ.A", "Circ.Bounds.A", "Circ.D", "Square.B",
                    "Square.A", "Square.D", "Rect.1", "Circ.Rect.I", "Circ.Rect.V"}
        assert set(field["shapes"].keys()) == expected


class TestPointFieldGeometry:
    def test_sqrt2_chain(self, field):
        m = field["metadata"]
        RG = m["root"]["R_GREEN"]
        assert m["derived"]["R_D"] == pytest.approx(RG / 1.4142135623730951, rel=1e-4)
        assert m["derived"]["R_A"] == pytest.approx(RG * 1.4142135623730951, rel=1e-4)

    def test_center(self, field):
        m = field["metadata"]
        assert m["root"]["cx"] == pytest.approx(0.3504)
        assert m["root"]["cy"] == pytest.approx(0.8694)

    def test_grid_crossings_exist(self, field):
        grid_pts = [k for k in field["points"] if k.startswith("P.GRID.")]
        assert len(grid_pts) >= 30

    def test_tangent_points_exist(self, field):
        tan_pts = [k for k in field["points"]
                   if "TAN" in k]
        assert len(tan_pts) >= 10

    def test_nib_points_exist(self, field):
        nib_pts = [k for k in field["points"] if "NIB" in k]
        assert len(nib_pts) >= 5


class TestPointFieldDeterminism:
    def test_output_is_deterministic(self):
        from p_logo_pipeline.point_field import generate_field
        f1 = generate_field()
        f2 = generate_field()
        h1 = hashlib.sha256(json.dumps(f1, sort_keys=True).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(f2, sort_keys=True).encode()).hexdigest()
        assert h1 == h2

    def test_hash_matches_snapshot(self, field):
        h = hashlib.sha256(json.dumps(field, sort_keys=True).encode()).hexdigest()
        assert h[:16] == "b4a9d913ac92cf7f"


class TestPointFieldCustomParams:
    def test_custom_params(self):
        from p_logo_pipeline.point_field import generate_field, FieldParams
        params = FieldParams(cx=0.0, cy=0.0, R_GREEN=1.0)
        result = generate_field(params)
        assert len(result["shapes"]) == 9
        assert result["metadata"]["root"]["R_GREEN"] == 1.0


# ══════════════════════════════════════════════════════
# 4. validate_step._run_checks()
# ══════════════════════════════════════════════════════

class TestValidationReport:
    def test_all_checks_pass(self, validation_report):
        assert validation_report["passed"] is True

    def test_check_count(self, validation_report):
        assert len(validation_report["checks"]) == 16

    def test_all_check_names_present(self, validation_report):
        expected = {
            "palette_step_0", "graph_step_1", "layout_step_4",
            "animation_systems_count", "graph_connected",
            "node_count_25", "edge_count_44", "max_degree_6",
            "node_positions_vs_schema",
            "layout_element_count", "html_valid_structure",
            "html_no_nan", "threejs_included",
            "total_renderable_range", "palette_colors_in_html",
            "brand_text_present",
        }
        actual = {c["name"] for c in validation_report["checks"]}
        assert actual == expected

    def test_all_statuses_pass(self, validation_report):
        for c in validation_report["checks"]:
            assert c["status"] in ("pass", "warn"), \
                f"Check {c['name']} has status {c['status']}: {c['detail']}"

    def test_total_renderable_in_range(self, validation_report):
        assert 250 <= validation_report["total_renderable"] <= 550


class TestValidationInventory:
    def test_inventory_keys(self, validation_report):
        inv = validation_report["inventory"]
        expected_keys = {
            "background", "stars", "circle_fill", "ring", "shimmer_arcs",
            "edges", "nodes", "bowl_arcs", "arc_runners", "nib",
            "ink_drops", "particles", "pulses", "energy_rings", "brand_text",
        }
        assert set(inv.keys()) == expected_keys

    def test_node_count_is_3x(self, validation_report):
        inv = validation_report["inventory"]
        assert inv["nodes"] % 3 == 0  # core + glow + bloom


class TestGraphMetrics:
    def test_node_count(self, validation_report):
        assert validation_report["graph_metrics"]["node_count"] == 25

    def test_edge_count(self, validation_report):
        assert validation_report["graph_metrics"]["edge_count"] == 44

    def test_connected(self, validation_report):
        assert validation_report["graph_metrics"]["connected"] is True

    def test_max_degree(self, validation_report):
        assert validation_report["graph_metrics"]["max_degree"] == 6


class TestValidationDeterminism:
    def test_report_deterministic(self, pipeline_data):
        from p_logo_pipeline.validate_step import build_report
        with open(LOGOS_DIR / "p_logo_pipeline.html") as f:
            html = f.read()
        r1 = build_report(
            pipeline_data["palette.json"], pipeline_data["graph.json"],
            pipeline_data["nib.json"], pipeline_data["arcs.json"],
            pipeline_data["layout.json"], pipeline_data["animations.json"], html)
        r2 = build_report(
            pipeline_data["palette.json"], pipeline_data["graph.json"],
            pipeline_data["nib.json"], pipeline_data["arcs.json"],
            pipeline_data["layout.json"], pipeline_data["animations.json"], html)
        h1 = hashlib.sha256(json.dumps(r1, sort_keys=True).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(r2, sort_keys=True).encode()).hexdigest()
        assert h1 == h2

    def test_report_hash_matches_snapshot(self, validation_report):
        h = hashlib.sha256(
            json.dumps(validation_report, sort_keys=True).encode()
        ).hexdigest()
        assert h[:16] == "b7e35ecb4d42473e"
