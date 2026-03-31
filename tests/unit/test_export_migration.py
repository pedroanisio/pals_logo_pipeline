"""
Phase 4 — Tests for export_p_logo.py migration to p_logo library.

Verifies GIF export and render_frame produce correct output.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestRenderFrame:
    def test_returns_correct_size(self):
        from p_logo import build_schema
        from p_logo.exporters.gif_export import render_frame

        img = render_frame(build_schema(), phase=0.0, size=400, dpi=50)
        assert img.size == (400, 400)

    def test_multiple_phases(self):
        from p_logo import build_schema
        from p_logo.exporters.gif_export import render_frame

        schema = build_schema()
        for phase in [0.0, 0.25, 0.5, 0.75]:
            img = render_frame(schema, phase=phase, size=200, dpi=50)
            assert img.size == (200, 200)

    def test_returns_rgb_image(self):
        from p_logo import build_schema
        from p_logo.exporters.gif_export import render_frame

        img = render_frame(build_schema(), size=200, dpi=50)
        assert img.mode == "RGB"


class TestGifExport:
    def test_produces_file(self):
        from p_logo import build_schema
        from p_logo.exporters.gif_export import export_gif

        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
            tmp = f.name
        try:
            export_gif(build_schema(), tmp, n_frames=4, size=200, dpi=50)
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 5000
        finally:
            os.unlink(tmp)

    def test_gif_is_valid_image(self):
        from PIL import Image
        from p_logo import build_schema
        from p_logo.exporters.gif_export import export_gif

        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
            tmp = f.name
        try:
            export_gif(build_schema(), tmp, n_frames=3, size=200, dpi=50)
            img = Image.open(tmp)
            assert img.format == "GIF"
            assert img.n_frames == 3
        finally:
            os.unlink(tmp)


class TestStaticPngFromRenderer:
    def test_crafted_renderer_for_static(self):
        from p_logo import build_schema
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer, HAS_CAIRO

        if not HAS_CAIRO:
            pytest.skip("pycairo not installed")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            CairoCraftedRenderer(build_schema()).render(tmp, size=800)
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 20000
        finally:
            os.unlink(tmp)
