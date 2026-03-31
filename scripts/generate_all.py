#!/usr/bin/env python3
"""
Generate all P Logo outputs from the canonical p_logo library.

Regenerates into build/logos/:
  - p_logo_schema.json             (canonical schema)
  - p_logo_bw_dark.png / light.png (B&W 800×800)
  - p_logo_cairo_*.png             (Cairo: dark, transparent, debug)
  - p_logo_v16_technical.png       (technical drawing)
  - p_logo_vector.svg              (vector SVG)
  - p_logo_threejs.html            (Three.js animation)

Usage:
  python3 generate_all.py              # all outputs
  python3 generate_all.py --quick      # skip slow renders (GIF, debug)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import time
from p_logo import build_schema

LOGOS_DIR = Path(__file__).parent.parent / "build" / "logos"


def main():
    parser = argparse.ArgumentParser(description="Generate all P Logo outputs")
    parser.add_argument("--quick", action="store_true", help="Skip slow renders")
    args = parser.parse_args()

    LOGOS_DIR.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    schema = build_schema()
    print(f"Schema: {schema.node_count} nodes, {schema.edge_count} edges, {len(schema.arcs)} arcs")

    # 1. JSON schema
    from p_logo.exporters.json_export import export_json
    export_json(schema, str(LOGOS_DIR / "p_logo_schema.json"))
    print("  → p_logo_schema.json")

    # 2. B&W PNGs
    from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer
    bw = MatplotlibBWRenderer(schema)
    bw.render(str(LOGOS_DIR / "p_logo_bw_dark.png"), dpi=300)
    bw.render(str(LOGOS_DIR / "p_logo_bw_light.png"), dpi=300, invert=True)
    print("  → p_logo_bw_dark.png + p_logo_bw_light.png")

    # 3. SVG
    from p_logo.exporters.svg_export import export_svg
    export_svg(schema, str(LOGOS_DIR / "p_logo_vector.svg"))
    print("  → p_logo_vector.svg")

    # 4. HTML animation
    from p_logo.exporters.html_export import export_html
    export_html(schema, str(LOGOS_DIR / "p_logo_threejs.html"))
    print("  → p_logo_threejs.html")

    # 5. Cairo renders
    try:
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer
        cairo = CairoCraftedRenderer(schema)
        cairo.render(str(LOGOS_DIR / "p_logo_cairo_1200.png"), size=1200)
        cairo.render(str(LOGOS_DIR / "p_logo_cairo_1200_transparent.png"), size=1200, transparent=True)
        print("  → p_logo_cairo_1200.png + transparent")
        if not args.quick:
            cairo.render(str(LOGOS_DIR / "p_logo_cairo_debug_2400.png"), size=2400, debug=True)
            print("  → p_logo_cairo_debug_2400.png")
    except ImportError:
        print("  (skipping Cairo renders — pycairo not installed)")

    # 6. V16 technical drawing
    from p_logo.renderers.v16_technical import V16TechnicalRenderer
    V16TechnicalRenderer(schema).render(str(LOGOS_DIR / "p_logo_v16_technical.png"), dpi=200)
    print("  → p_logo_v16_technical.png")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s — all outputs in build/logos/")


if __name__ == "__main__":
    main()
