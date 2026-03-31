"""
Regression tests for render.py:_build_html() / build_render().

Locks the exact HTML output before decomposing the 561-line god function
into focused sub-builders.  The refactor must not change any output.
"""

import json
import sys
import hashlib
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

BUILD_DIR = ROOT / "src" / "p_logo_pipeline" / "build"


@pytest.fixture(scope="module")
def pipeline_data():
    with open(BUILD_DIR / "palette.json") as f:
        palette = json.load(f)
    with open(BUILD_DIR / "layout.json") as f:
        layout = json.load(f)
    with open(BUILD_DIR / "animations.json") as f:
        anims = json.load(f)
    return palette, layout, anims


@pytest.fixture(scope="module")
def html(pipeline_data):
    from p_logo_pipeline.render import build_render
    palette, layout, anims = pipeline_data
    return build_render(palette, layout, anims)


# ── HTML structure ───────────────────────────────────────────────

class TestHtmlStructure:
    def test_starts_with_doctype(self, html):
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_has_closing_html(self, html):
        assert "</html>" in html

    def test_has_head_and_body(self, html):
        assert "<head>" in html
        assert "<body>" in html

    def test_has_threejs_import(self, html):
        assert "three.js/r128/three.min.js" in html

    def test_has_title(self, html):
        assert "<title>" in html
        assert "PAL" in html

    def test_has_style_block(self, html):
        assert "<style>" in html
        assert "</style>" in html

    def test_has_script_block(self, html):
        assert "<script>" in html
        assert "</script>" in html


# ── JS data blocks ───────────────────────────────────────────────

class TestJsDataBlocks:
    def test_has_palette(self, html):
        assert "const PAL" in html

    def test_has_nodes(self, html):
        assert "const NODES" in html

    def test_has_edges(self, html):
        assert "const EDGES" in html

    def test_has_arcs(self, html):
        assert "const ARCS" in html

    def test_has_nib(self, html):
        assert "const NIB" in html

    def test_has_runner_paths(self, html):
        assert "const RUNNER_PATHS" in html

    def test_has_ring(self, html):
        assert "const RING" in html

    def test_has_anim(self, html):
        assert "const ANIM" in html

    def test_has_adjacency(self, html):
        assert "const ADJ" in html

    def test_has_nebula(self, html):
        assert "NEBULA_COUNT" in html
        assert "NEBULA_COLORS" in html

    def test_has_star_count(self, html):
        assert "STAR_COUNT" in html

    def test_has_center_offset(self, html):
        assert "CENTER_OFFSET_Y" in html


# ── Three.js scene ───────────────────────────────────────────────

class TestThreejsScene:
    def test_has_scene_setup(self, html):
        assert "new THREE.Scene()" in html

    def test_has_camera(self, html):
        assert "OrthographicCamera" in html

    def test_has_renderer(self, html):
        assert "WebGLRenderer" in html

    def test_has_logo_group(self, html):
        assert "logoGroup" in html

    def test_has_ring_bands(self, html):
        assert "RingGeometry" in html

    def test_has_animate_function(self, html):
        assert "function animate()" in html

    def test_has_wave_trigger(self, html):
        assert "triggerWave" in html

    def test_has_breathing(self, html):
        assert "breathing" in html.lower() or "Breathing" in html


# ── No Python artifacts ──────────────────────────────────────────

class TestNoPythonArtifacts:
    def test_no_python_import(self, html):
        assert "import json" not in html
        assert "from pathlib" not in html

    def test_no_triple_quotes(self, html):
        # f-string delimiters should not leak
        assert "'''" not in html.split("<script>")[1].split("</script>")[0]


# ── Validation ───────────────────────────────────────────────────

class TestValidation:
    def test_validate_passes_good_data(self, pipeline_data):
        from p_logo_pipeline.render import validate
        palette, layout, anims = pipeline_data
        errors = validate(palette, layout, anims)
        assert errors == []

    def test_validate_catches_bad_layout_step(self, pipeline_data):
        from p_logo_pipeline.render import validate
        palette, layout, anims = pipeline_data
        bad_layout = {**layout, "_meta": {"step": 99}}
        errors = validate(palette, bad_layout, anims)
        assert any("layout" in e for e in errors)


# ── Determinism ──────────────────────────────────────────────────

class TestDeterminism:
    def test_output_is_deterministic(self, pipeline_data):
        from p_logo_pipeline.render import build_render
        palette, layout, anims = pipeline_data
        h1 = build_render(palette, layout, anims)
        h2 = build_render(palette, layout, anims)
        assert hashlib.sha256(h1.encode()).hexdigest() == \
               hashlib.sha256(h2.encode()).hexdigest()

    def test_output_length(self, html):
        # Guard against accidentally truncated or doubled output
        assert 25_000 < len(html) < 50_000

    def test_output_hash_matches_snapshot(self, html):
        h = hashlib.sha256(html.encode()).hexdigest()
        assert h[:16] == "48bbaa11d0e2ea0d"
