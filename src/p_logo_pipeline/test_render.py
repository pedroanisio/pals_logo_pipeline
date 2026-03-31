"""
PAL's Notes Logo Pipeline — Step 6: Render — TEST SUITE (TDD)

Written BEFORE implementation.

Run:
    cd pals-logo-pipeline
    python -m pytest test_render.py -v

Requires: palette.json, layout.json, animations.json in build/

The renderer is the only step that knows about Three.js and HTML. It reads
all upstream data artifacts and produces a single self-contained HTML file
with embedded JavaScript. Since we can't run a browser in tests, we verify
the generated HTML string for structural correctness and data embedding.

What we CAN test (string/structural analysis):
  - HTML document structure (doctype, head, body, canvas elements)
  - Three.js CDN script inclusion
  - All palette colors embedded as JS hex literals
  - All node positions from layout embedded in JS
  - All edge pairs embedded
  - All animation system parameters embedded
  - Background/star/nebula config values present
  - Brand text element present
  - Ring parameters present
  - File is self-contained (only external dep is Three.js CDN)

What we CANNOT test (requires browser):
  - Visual rendering correctness
  - Animation smoothness
  - WebGL context creation
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def build_dir() -> Path:
    return Path(__file__).parent / "build"


@pytest.fixture(scope="session")
def palette(build_dir) -> dict:
    with open(build_dir / "palette.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def layout_data(build_dir) -> dict:
    with open(build_dir / "layout.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def anim_data(build_dir) -> dict:
    with open(build_dir / "animations.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def render_module():
    sys.path.insert(0, str(Path(__file__).parent))
    import render
    return render


@pytest.fixture(scope="session")
def rendered_html(render_module, palette, layout_data, anim_data) -> str:
    """The generated HTML string (not written to file yet)."""
    return render_module.build_render(palette, layout_data, anim_data)


@pytest.fixture(scope="session")
def rendered_path(render_module, palette, layout_data, anim_data) -> Path:
    return render_module.write_render(palette, layout_data, anim_data)


# ──────────────────────────────────────────────
# 1. MODULE INTERFACE
# ──────────────────────────────────────────────

class TestModuleInterface:

    def test_has_build_render(self, render_module):
        assert callable(getattr(render_module, "build_render", None))

    def test_has_write_render(self, render_module):
        assert callable(getattr(render_module, "write_render", None))

    def test_has_validate(self, render_module):
        assert callable(getattr(render_module, "validate", None))

    def test_build_returns_string(self, rendered_html):
        assert isinstance(rendered_html, str)
        assert len(rendered_html) > 1000, "HTML too short to be valid"


# ──────────────────────────────────────────────
# 2. HTML DOCUMENT STRUCTURE
# ──────────────────────────────────────────────

class TestHtmlStructure:

    def test_has_doctype(self, rendered_html):
        assert rendered_html.strip().startswith("<!DOCTYPE html")

    def test_has_html_tag(self, rendered_html):
        assert "<html" in rendered_html
        assert "</html>" in rendered_html

    def test_has_head(self, rendered_html):
        assert "<head>" in rendered_html or "<head " in rendered_html
        assert "</head>" in rendered_html

    def test_has_body(self, rendered_html):
        assert "<body>" in rendered_html or "<body " in rendered_html
        assert "</body>" in rendered_html

    def test_has_meta_charset(self, rendered_html):
        assert 'charset="UTF-8"' in rendered_html or "charset='UTF-8'" in rendered_html

    def test_has_title(self, rendered_html):
        assert "<title>" in rendered_html


# ──────────────────────────────────────────────
# 3. CANVAS ELEMENTS
# ──────────────────────────────────────────────

class TestCanvasElements:
    """The logo uses layered canvases: background, stars, Three.js."""

    def test_has_bg_canvas(self, rendered_html):
        assert 'id="bg-canvas"' in rendered_html

    def test_has_star_canvas(self, rendered_html):
        assert 'id="star-canvas"' in rendered_html

    def test_has_three_canvas(self, rendered_html):
        assert 'id="three-canvas"' in rendered_html

    def test_canvas_count(self, rendered_html):
        count = rendered_html.count("<canvas")
        assert count >= 3, f"Only {count} canvas elements, expected >= 3"


# ──────────────────────────────────────────────
# 4. THREE.JS INCLUSION
# ──────────────────────────────────────────────

class TestThreeJs:

    def test_three_js_cdn_script(self, rendered_html):
        assert "cdnjs.cloudflare.com" in rendered_html
        assert "three" in rendered_html.lower()

    def test_three_js_r128(self, rendered_html):
        """Must use Three.js r128 as specified."""
        assert "r128" in rendered_html

    def test_uses_orthographic_camera(self, rendered_html):
        assert "OrthographicCamera" in rendered_html

    def test_uses_webgl_renderer(self, rendered_html):
        assert "WebGLRenderer" in rendered_html


# ──────────────────────────────────────────────
# 5. PALETTE COLORS EMBEDDED
# ──────────────────────────────────────────────

class TestPaletteEmbedding:

    def test_all_hex_colors_present(self, rendered_html, palette):
        """Every palette color's hex value must appear in the JS."""
        for name, color in palette["colors"].items():
            hex_int = f"0x{color['hex'].lstrip('#')}"
            hex_str = color["hex"]
            present = (hex_int in rendered_html or
                       hex_int.lower() in rendered_html.lower() or
                       hex_str in rendered_html or
                       hex_str.lower() in rendered_html.lower())
            assert present, (
                f"Color '{name}' ({hex_str} / {hex_int}) not found in HTML"
            )

    def test_background_color_in_css(self, rendered_html, palette):
        bg_hex = palette["colors"]["background"]["hex"].lower()
        assert bg_hex in rendered_html.lower()


# ──────────────────────────────────────────────
# 6. NODE DATA EMBEDDED
# ──────────────────────────────────────────────

class TestNodeEmbedding:

    def test_node_count_in_js(self, rendered_html, layout_data):
        """The JS must contain data for all 23 nodes."""
        node_count = layout_data["inventory"].get("node", 0)
        # Check that positions are embedded — look for the first and last
        # node coordinates
        nodes = [el for el in layout_data["elements"] if el["type"] == "node"]
        assert len(nodes) == node_count

        # At least verify a sample of node X coordinates appear
        found = 0
        for node in nodes:
            # Format as JS would: e.g. -1.0 or 2.5
            x_str = f"{node['x']:.1f}"
            if x_str in rendered_html:
                found += 1
        assert found >= node_count * 0.5, (
            f"Only {found}/{node_count} node X coords found in HTML"
        )

    def test_node_colors_referenced(self, rendered_html):
        """Node color hex values must appear."""
        # copper is the dominant node color
        assert "0x6EC4A8" in rendered_html or "0x6ec4a8" in rendered_html


# ──────────────────────────────────────────────
# 7. EDGE DATA EMBEDDED
# ──────────────────────────────────────────────

class TestEdgeEmbedding:

    def test_edge_pairs_present(self, rendered_html, layout_data):
        """Edge connectivity data must be in the JS."""
        edges = [el for el in layout_data["elements"] if el["type"] == "edge"]
        # Edge format is now [a, b, "type"] — search for [a,b, or [a, b,
        found = 0
        for edge in edges:
            a, b = edge["a"], edge["b"]
            patterns = [f"[{a},{b},", f"[{a}, {b},",
                        f"[{a},{b}]", f"[{a}, {b}]"]
            if any(p in rendered_html for p in patterns):
                found += 1
        assert found >= len(edges) * 0.5, (
            f"Only {found}/{len(edges)} edge pairs found"
        )


# ──────────────────────────────────────────────
# 8. ARC DATA EMBEDDED
# ──────────────────────────────────────────────

class TestArcEmbedding:

    def test_arc_radii_present(self, rendered_html, layout_data):
        arcs = [el for el in layout_data["elements"] if el["type"] == "arc"]
        for arc in arcs:
            r_str = f"{arc['radius']:.2f}"
            assert r_str in rendered_html or str(arc["radius"]) in rendered_html, (
                f"Arc radius {arc['radius']} not found in HTML"
            )


# ──────────────────────────────────────────────
# 9. ANIMATION SYSTEMS EMBEDDED
# ──────────────────────────────────────────────

class TestAnimationEmbedding:

    def test_wave_interval(self, rendered_html, anim_data):
        interval = anim_data["systems"]["wave"]["interval"]
        assert str(interval) in rendered_html

    def test_wave_delay(self, rendered_html, anim_data):
        delay = anim_data["systems"]["wave"]["delay_per_hop"]
        assert str(delay) in rendered_html

    def test_pulse_count(self, rendered_html, anim_data):
        count = anim_data["systems"]["pulses"]["count"]
        # 12 is common, look for it in pulse context
        assert str(count) in rendered_html

    def test_breathing_amplitude(self, rendered_html, anim_data):
        amp = anim_data["systems"]["breathing"]["amplitude"]
        assert str(amp) in rendered_html

    def test_ink_pool_size(self, rendered_html, anim_data):
        pool = anim_data["systems"]["ink_drops"]["pool_size"]
        assert str(pool) in rendered_html

    def test_ink_gravity(self, rendered_html, anim_data):
        g = anim_data["systems"]["ink_drops"]["gravity"]
        assert str(abs(g)) in rendered_html

    def test_arc_runner_trail(self, rendered_html, anim_data):
        trail = anim_data["systems"]["arc_runners"]["trail_length"]
        assert str(trail) in rendered_html

    def test_energy_ring_interval(self, rendered_html, anim_data):
        interval = anim_data["systems"]["energy_rings"]["interval"]
        assert str(interval) in rendered_html


# ──────────────────────────────────────────────
# 10. BACKGROUND ELEMENTS
# ──────────────────────────────────────────────

class TestBackgroundElements:

    def test_nebula_cloud_count(self, rendered_html, palette):
        count = palette["nebula"]["count"]
        # Should have a loop or array creating 7 clouds
        assert str(count) in rendered_html

    def test_star_count(self, rendered_html, palette):
        count = palette["stars"]["count"]
        assert str(count) in rendered_html

    def test_has_vignette(self, rendered_html):
        """Background should include a vignette gradient."""
        assert "vignette" in rendered_html.lower() or "Vignette" in rendered_html or \
               "createRadialGradient" in rendered_html


# ──────────────────────────────────────────────
# 11. BRAND TEXT
# ──────────────────────────────────────────────

class TestBrandText:

    def test_brand_text_present(self, rendered_html):
        """'PAL's Notes' appears as a separate brand line.'"""
        assert "PAL" in rendered_html
        assert "Notes" in rendered_html

    def test_brand_text_element(self, rendered_html):
        assert "brand-text" in rendered_html

    def test_brand_text_animated(self, rendered_html):
        """Brand text should have a fade-in animation."""
        assert "brandFadeIn" in rendered_html or "brand" in rendered_html.lower()


# ──────────────────────────────────────────────
# 12. RING DATA
# ──────────────────────────────────────────────

class TestRingData:

    def test_ring_radii_present(self, rendered_html, layout_data):
        ring = layout_data["ring"]
        for band in ring["bands"]:
            ir = f"{band['inner_r']:.2f}"
            found = ir in rendered_html or str(band["inner_r"]) in rendered_html
            assert found, f"Ring inner_r {band['inner_r']} not found"

    def test_fill_radius_present(self, rendered_html, layout_data):
        fr = layout_data["ring"]["fill_radius"]
        assert str(fr) in rendered_html


# ──────────────────────────────────────────────
# 13. SELF-CONTAINMENT
# ──────────────────────────────────────────────

class TestSelfContainment:

    def test_only_external_dep_is_threejs(self, rendered_html):
        """The only external script should be the Three.js CDN."""
        # Find all script src attributes
        srcs = re.findall(r'src=["\']([^"\']+)["\']', rendered_html)
        external = [s for s in srcs if s.startswith("http")]
        for src in external:
            assert "three" in src.lower() or "cdnjs" in src.lower(), (
                f"Unexpected external dependency: {src}"
            )

    def test_no_external_css(self, rendered_html):
        """No external CSS files — all styles should be inline."""
        link_tags = re.findall(r'<link[^>]+rel=["\']stylesheet["\']', rendered_html)
        assert len(link_tags) == 0, f"Found {len(link_tags)} external stylesheets"

    def test_css_is_embedded(self, rendered_html):
        assert "<style>" in rendered_html


# ──────────────────────────────────────────────
# 14. CENTER OFFSET APPLIED
# ──────────────────────────────────────────────

class TestCenterOffset:

    def test_offset_y_in_js(self, rendered_html, layout_data):
        """The center offset Y should appear in the JS for group positioning."""
        oy = layout_data["center_offset"]["y"]
        # Could be as logoGroup.position.y = X or as an embedded value
        assert str(round(oy, 2)) in rendered_html or str(oy) in rendered_html


# ──────────────────────────────────────────────
# 15. VALIDATION
# ──────────────────────────────────────────────

class TestValidation:

    def test_validate_passes(self, render_module, palette, layout_data, anim_data):
        errors = render_module.validate(palette, layout_data, anim_data)
        assert errors == []


# ──────────────────────────────────────────────
# 16. FILE OUTPUT
# ──────────────────────────────────────────────

class TestFileOutput:

    def test_file_created(self, rendered_path):
        assert rendered_path.exists()
        assert rendered_path.name == "p_logo_pipeline.html"

    def test_file_in_logos_dir(self, rendered_path):
        assert rendered_path.parent.name == "logos"

    def test_file_is_nonempty(self, rendered_path):
        assert rendered_path.stat().st_size > 1000

    def test_file_matches_build(self, rendered_path, rendered_html):
        with open(rendered_path) as f:
            from_file = f.read()
        assert from_file == rendered_html

    def test_file_is_valid_html(self, rendered_path):
        with open(rendered_path) as f:
            content = f.read()
        assert "<!DOCTYPE html" in content
        assert "</html>" in content


# ──────────────────────────────────────────────
# 17. NIB DATA EMBEDDED
# ──────────────────────────────────────────────

class TestNibEmbedding:

    def test_nib_lines_in_js(self, rendered_html, layout_data):
        """Fan + outline + center lines should be in the output."""
        fan_count = layout_data["inventory"].get("nib_fan_line", 0)
        assert fan_count > 0
        # Verify the nib junction ball warm_white color is present
        assert "0xFFF0D8" in rendered_html or "0xfff0d8" in rendered_html

    def test_ink_origin_in_js(self, rendered_html, layout_data):
        ink = [el for el in layout_data["elements"] if el["type"] == "ink_origin"][0]
        x_str = f"{ink['x']:.1f}"
        y_str = f"{ink['y']:.1f}"
        assert x_str in rendered_html or str(ink["x"]) in rendered_html
        assert y_str in rendered_html or str(ink["y"]) in rendered_html
