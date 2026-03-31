"""
Phase 1 — Tests for geometric_p_logo.py migration to p_logo library.

These tests verify that the library can fully replace geometric_p_logo.py:
- build_schema() produces identical data to the current JSON on disk
- Renderers produce output files
- JSON export roundtrip matches
"""

import json
import os
import sys
import tempfile
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))


class TestSchemaMatchesCurrentFile:
    """build_schema() + schema_to_dict() must match p_logo_schema.json on disk."""

    def test_json_roundtrip_matches_current(self):
        from p_logo import build_schema
        from p_logo.exporters.json_export import export_json

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = f.name
        try:
            export_json(build_schema(), tmp)

            with open(tmp) as f:
                new = json.load(f)
            with open(ROOT / "build" / "logos" / "p_logo_schema.json") as f:
                old = json.load(f)

            # Node positions
            for o, n in zip(old["graph"]["nodes"], new["graph"]["nodes"]):
                assert abs(o["x"] - n["x"]) < 0.002
                assert abs(o["y"] - n["y"]) < 0.002

            # Edge set
            old_e = set((e["from"], e["to"]) for e in old["graph"]["edges"])
            new_e = set((e["from"], e["to"]) for e in new["graph"]["edges"])
            assert old_e == new_e

            # Arc radii
            for o, n in zip(old["geometry"]["arcs"], new["geometry"]["arcs"]):
                assert abs(o["radius"] - n["radius"]) < 1e-3
        finally:
            os.unlink(tmp)

    def test_export_json_overwrites_schema_identically(self):
        """Export to a new file, then compare structure."""
        from p_logo import build_schema
        from p_logo.exporters.json_export import schema_to_dict

        new = schema_to_dict(build_schema())
        with open(ROOT / "build" / "logos" / "p_logo_schema.json") as f:
            old = json.load(f)

        assert len(new["graph"]["nodes"]) == len(old["graph"]["nodes"])
        assert len(new["graph"]["edges"]) == len(old["graph"]["edges"])
        assert len(new["geometry"]["arcs"]) == len(old["geometry"]["arcs"])


class TestBWRendererProducesOutput:
    def test_wb_render(self):
        from p_logo import build_schema
        from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            MatplotlibBWRenderer(build_schema()).render(tmp, dpi=72, size=400)
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 5000  # at least 5KB
        finally:
            os.unlink(tmp)

    def test_bw_inverted_render(self):
        from p_logo import build_schema
        from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            MatplotlibBWRenderer(build_schema()).render(tmp, dpi=72, size=400, invert=True)
            assert os.path.exists(tmp)
            assert os.path.getsize(tmp) > 5000
        finally:
            os.unlink(tmp)


class TestOverlayRendering:
    def test_overlay_no_exceptions(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from p_logo import build_schema
        from p_logo.overlay import render_overlay

        schema = build_schema()
        fig, ax = plt.subplots()
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        render_overlay(ax, schema)
        plt.close(fig)
