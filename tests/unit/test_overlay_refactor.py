"""
Regression tests for render_overlay.py:build_overlay().

Locks the exact HTML output before decomposing the 660-line god function
into focused sub-builders.  The refactor must not change any output.
"""

import sys
import hashlib
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def overlay_html():
    from p_logo_pipeline.render_overlay import build_overlay
    return build_overlay()


# ── HTML structure ───────────────────────────────────────────────

class TestOverlayHtmlStructure:
    def test_starts_with_doctype(self, overlay_html):
        assert overlay_html.strip().startswith("<!DOCTYPE html>")

    def test_has_closing_html(self, overlay_html):
        assert "</html>" in overlay_html

    def test_has_head_and_body(self, overlay_html):
        assert "<head>" in overlay_html
        assert "<body>" in overlay_html

    def test_has_threejs_import(self, overlay_html):
        assert "three.js/r128/three.min.js" in overlay_html

    def test_has_title(self, overlay_html):
        assert "Construction Overlay" in overlay_html

    def test_has_style_block(self, overlay_html):
        assert "<style>" in overlay_html

    def test_has_script_block(self, overlay_html):
        assert "<script>" in overlay_html


# ── JS data blocks ───────────────────────────────────────────────

class TestOverlayDataBlocks:
    def test_has_color_map(self, overlay_html):
        assert "const CMAP" in overlay_html

    def test_has_field_shapes(self, overlay_html):
        assert "const FIELD_SHAPES" in overlay_html

    def test_has_field_points(self, overlay_html):
        assert "const FIELD_POINTS" in overlay_html

    def test_has_selected(self, overlay_html):
        assert "const SELECTED" in overlay_html

    def test_has_proj_edges(self, overlay_html):
        assert "const PROJ_EDGES" in overlay_html

    def test_has_nodes(self, overlay_html):
        assert "const NODES" in overlay_html

    def test_has_edges(self, overlay_html):
        assert "const EDGES" in overlay_html

    def test_has_arcs(self, overlay_html):
        assert "const ARCS" in overlay_html

    def test_has_nib(self, overlay_html):
        assert "const NIB" in overlay_html

    def test_has_ring(self, overlay_html):
        assert "const RING" in overlay_html

    def test_has_adjacency(self, overlay_html):
        assert "const ADJ" in overlay_html

    def test_has_nebula_colors(self, overlay_html):
        assert "NEBULA_COLORS" in overlay_html


# ── Canvas layers ────────────────────────────────────────────────

class TestOverlayCanvasLayers:
    def test_has_bg_canvas(self, overlay_html):
        assert "bg-canvas" in overlay_html

    def test_has_star_canvas(self, overlay_html):
        assert "star-canvas" in overlay_html

    def test_has_construct_canvas(self, overlay_html):
        assert "construct-canvas" in overlay_html

    def test_has_three_canvas(self, overlay_html):
        assert "three-canvas" in overlay_html


# ── Plane A: Construction ────────────────────────────────────────

class TestPlaneAConstruction:
    def test_has_draw_construction(self, overlay_html):
        assert "drawConstruction" in overlay_html

    def test_draws_circ_a(self, overlay_html):
        assert "Circ.A" in overlay_html

    def test_draws_square_b(self, overlay_html):
        assert "Square.B" in overlay_html

    def test_draws_square_c(self, overlay_html):
        assert "Square.C" in overlay_html

    def test_draws_vertex_circles(self, overlay_html):
        assert "Circ.V" in overlay_html

    def test_draws_field_points(self, overlay_html):
        assert "FIELD_POINTS" in overlay_html

    def test_draws_projection_edges(self, overlay_html):
        assert "PROJ_EDGES" in overlay_html


# ── Plane B: Logo ────────────────────────────────────────────────

class TestPlaneBLogo:
    def test_has_scene_setup(self, overlay_html):
        assert "new THREE.Scene()" in overlay_html

    def test_has_logo_group(self, overlay_html):
        assert "logoGroup" in overlay_html

    def test_has_ring_fill(self, overlay_html):
        assert "fill_radius" in overlay_html or "fillR" in overlay_html

    def test_has_node_meshes(self, overlay_html):
        assert "nodeMeshes" in overlay_html


# ── Phase management ─────────────────────────────────────────────

class TestPhaseManagement:
    def test_has_phase_times(self, overlay_html):
        assert "PHASE_TIMES" in overlay_html

    def test_has_phase_alphas(self, overlay_html):
        assert "getPhaseAlphas" in overlay_html

    def test_has_phase_label_fn(self, overlay_html):
        assert "getPhaseLabel" in overlay_html

    def test_phase_construct_in(self, overlay_html):
        assert "constructIn" in overlay_html

    def test_phase_highlight(self, overlay_html):
        assert "highlight" in overlay_html

    def test_phase_crossfade(self, overlay_html):
        assert "crossfade" in overlay_html

    def test_phase_logo_full(self, overlay_html):
        assert "logoFull" in overlay_html


# ── Animation ────────────────────────────────────────────────────

class TestOverlayAnimation:
    def test_has_animate_function(self, overlay_html):
        assert "function animate()" in overlay_html

    def test_has_wave_trigger(self, overlay_html):
        assert "triggerWave" in overlay_html

    def test_has_ink_drops(self, overlay_html):
        assert "inkDrops" in overlay_html

    def test_has_energy_rings(self, overlay_html):
        assert "energyRings" in overlay_html

    def test_has_shimmer(self, overlay_html):
        assert "shimmerArcs" in overlay_html


# ── No Python artifacts ──────────────────────────────────────────

class TestOverlayNoPythonArtifacts:
    def test_no_python_import(self, overlay_html):
        script_section = overlay_html.split("<script>")[1].split("</script>")[0]
        assert "import json" not in script_section
        assert "from pathlib" not in script_section


# ── Determinism ──────────────────────────────────────────────────

class TestOverlayDeterminism:
    def test_output_is_deterministic(self):
        from p_logo_pipeline.render_overlay import build_overlay
        h1 = build_overlay()
        h2 = build_overlay()
        assert hashlib.sha256(h1.encode()).hexdigest() == \
               hashlib.sha256(h2.encode()).hexdigest()

    def test_output_length(self, overlay_html):
        assert 40_000 < len(overlay_html) < 70_000

    def test_output_hash_matches_snapshot(self, overlay_html):
        h = hashlib.sha256(overlay_html.encode()).hexdigest()
        assert h[:16] == "6f08d753c615fa7e"
