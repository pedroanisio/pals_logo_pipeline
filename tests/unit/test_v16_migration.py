"""
Phase 3 — Tests for geometric_p_v16.py migration to p_logo library.

Verifies V16TechnicalRenderer produces output and consumes schema correctly.
"""

import os
import math
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestV16RendererProducesOutput:
    def test_render_creates_file(self):
        from p_logo import build_schema
        from p_logo.renderers.v16_technical import V16TechnicalRenderer

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            V16TechnicalRenderer(build_schema()).render(tmp, dpi=72)
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 10000
        finally:
            os.unlink(tmp)


class TestV16UsesSchemaCenter:
    def test_center_matches(self):
        from p_logo import build_schema
        schema = build_schema()
        assert schema.center == pytest.approx((0.3504, 0.8694), abs=1e-4)


class TestV16ConstructionGeometry:
    """Square.A and Square.D vertex positions must match the standalone script."""

    def test_square_a_vertices(self):
        from p_logo import build_schema
        s = build_schema()
        cx, cy = s.center
        expected_vx = cx + s.r_gold * np.cos(np.radians([45, 135, 225, 315]))
        expected_vy = cy + s.r_gold * np.sin(np.radians([45, 135, 225, 315]))

        # These are the same values geometric_p_v16.py computed as sq_A_vx/sq_A_vy
        assert expected_vx[0] == pytest.approx(1.5807, abs=0.002)  # 45°
        assert expected_vy[0] == pytest.approx(2.0997, abs=0.002)
        assert expected_vx[2] == pytest.approx(-0.8799, abs=0.002)  # 225°
        assert expected_vy[2] == pytest.approx(-0.3609, abs=0.002)

    def test_square_d_vertices(self):
        from p_logo import build_schema
        s = build_schema()
        cx, cy = s.center
        expected_vx = cx + s.r_green * np.cos(np.radians([45, 135, 225, 315]))
        expected_vy = cy + s.r_green * np.sin(np.radians([45, 135, 225, 315]))

        assert expected_vx[0] == pytest.approx(1.2204, abs=0.002)  # 45°
        assert expected_vy[0] == pytest.approx(1.7394, abs=0.002)


class TestV16NibFromSchema:
    """Nib outline must match the standalone script's values."""

    def test_nib_tip(self):
        from p_logo import build_schema
        nib = build_schema().nib
        # nib tip = Circ.Rect.V center y
        assert nib.outline[0][1] == pytest.approx(-3.12, abs=0.01)

    def test_nib_center_x(self):
        from p_logo import build_schema
        nib = build_schema().nib
        assert nib.ball_pos[0] == pytest.approx(-0.8799, abs=0.002)

    def test_nib_ball_y(self):
        from p_logo import build_schema
        nib = build_schema().nib
        # ball = Circ.Rect.I center
        assert nib.ball_pos[1] == pytest.approx(-2.1008, abs=0.002)

    def test_nib_waist_y(self):
        from p_logo import build_schema
        nib = build_schema().nib
        # waist = outline[1][1] = Circ.Rect.I top
        assert nib.outline[1][1] == pytest.approx(-1.5912, abs=0.002)
