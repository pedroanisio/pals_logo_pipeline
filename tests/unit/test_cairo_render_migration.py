"""
Phase 2 — Tests for cairo-render.py migration to p_logo library.

Locks the 25 node positions, 44 edges, arc radii, and nib geometry
against the values that were hardcoded in the standalone cairo-render.py.
Also tests that CairoCraftedRenderer produces output.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Hardcoded node positions from the standalone cairo-render.py (before migration)
CAIRO_NODES = [
    (0,  -1.3895,  2.6093),
    (1,   0.3504,  2.6093),
    (2,   1.2204,  1.7394),
    (3,   0.3504, -0.0006),
    (4,  -0.8799,  2.0997),
    (5,   0.3504,  1.7394),
    (6,   1.2204,  0.8694),
    (7,  -1.3895, -0.0006),
    (8,  -0.3703, -0.0006),
    (9,  -0.8799, -0.3609),
    (10, -0.3703, -0.8705),
    (11, -1.3895, -0.8705),
    (12, -0.8799, -1.5912),
    (13, -0.8799, -2.1008),
    (14, -0.8799, -3.1200),
    (15, -0.3703,  1.7394),
    (16, -0.3703, -0.8705),
    (17,  0.3504, -0.8705),
    (18,  0.3504, -0.3609),
    (19,  0.3504,  2.0997),
    (20,  2.0903,  0.8694),
    (21,  1.2204, -0.0006),
    (22, -1.3895, -1.5912),
    (23, -0.3703, -1.5912),
    (24, -0.8799, -1.2308),
]

CAIRO_ARC_RADII = [1.2303, 0.8699534728938093, 1.7399069457876188]
CAIRO_NIB = {"cx": -0.8799, "tip_y": -3.12, "top_y": -1.5912, "ctr_y": -2.1008}


class TestCairoNodeRegression:
    """Library node positions must match what cairo-render.py had hardcoded."""

    @pytest.mark.parametrize("idx,expected_x,expected_y", CAIRO_NODES)
    def test_node_position_matches_cairo(self, idx, expected_x, expected_y):
        from p_logo import build_schema
        schema = build_schema()
        node = schema.node(idx)
        assert node.x == pytest.approx(expected_x, abs=0.002)
        assert node.y == pytest.approx(expected_y, abs=0.002)


class TestCairoEdgeRegression:
    def test_node_count(self):
        from p_logo import build_schema
        assert build_schema().node_count == 25

    def test_edge_count(self):
        from p_logo import build_schema
        assert build_schema().edge_count == 44


class TestCairoArcRegression:
    @pytest.mark.parametrize("idx,expected_r", enumerate(CAIRO_ARC_RADII))
    def test_arc_radius(self, idx, expected_r):
        from p_logo import build_schema
        arc = build_schema().arcs[idx]
        assert arc.radius == pytest.approx(expected_r, abs=1e-6)

    def test_all_arcs_are_pi_semicircles(self):
        import math
        from p_logo import build_schema
        for arc in build_schema().arcs:
            assert arc.start_angle == pytest.approx(-math.pi / 2, abs=1e-6)
            assert arc.sweep_angle == pytest.approx(math.pi, abs=1e-6)


class TestCairoNibRegression:
    def test_nib_center_x(self):
        from p_logo import build_schema
        assert build_schema().nib.ball_pos[0] == pytest.approx(CAIRO_NIB["cx"], abs=0.002)

    def test_nib_ball_y(self):
        from p_logo import build_schema
        assert build_schema().nib.ball_pos[1] == pytest.approx(CAIRO_NIB["ctr_y"], abs=0.002)


class TestCairoRendererProducesOutput:
    def test_dark_render(self):
        from p_logo import build_schema
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer, HAS_CAIRO
        if not HAS_CAIRO:
            pytest.skip("pycairo not installed")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            CairoCraftedRenderer(build_schema()).render(tmp, size=600)
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 10000
        finally:
            os.unlink(tmp)

    def test_transparent_render(self):
        from p_logo import build_schema
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer, HAS_CAIRO
        if not HAS_CAIRO:
            pytest.skip("pycairo not installed")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            CairoCraftedRenderer(build_schema()).render(tmp, size=600, transparent=True)
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 5000
        finally:
            os.unlink(tmp)

    def test_debug_render(self):
        from p_logo import build_schema
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer, HAS_CAIRO
        if not HAS_CAIRO:
            pytest.skip("pycairo not installed")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            CairoCraftedRenderer(build_schema()).render(tmp, size=600, debug=True)
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 5000
        finally:
            os.unlink(tmp)
