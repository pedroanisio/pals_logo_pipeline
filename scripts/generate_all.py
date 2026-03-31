#!/usr/bin/env python3
"""
Generate all P Logo outputs from the canonical p_logo library.

Regenerates:
  - p_logo_schema.json          (canonical schema)
  - p_logo_wb.png / p_logo_bw.png  (B&W 800×800)
  - p-logo-crafted-logic-*.png  (Cairo: dark, transparent, debug)
  - geometric_p_v16.png         (technical drawing)
  - p_logo.svg                  (vector SVG)
  - animated-p-logo-revision.html (Three.js animation)

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


def main():
    parser = argparse.ArgumentParser(description="Generate all P Logo outputs")
    parser.add_argument("--quick", action="store_true", help="Skip slow renders")
    args = parser.parse_args()

    t0 = time.time()
    schema = build_schema()
    print(f"Schema: {schema.node_count} nodes, {schema.edge_count} edges, {len(schema.arcs)} arcs")

    # 1. JSON schema
    from p_logo.exporters.json_export import export_json
    export_json(schema, "p_logo_schema.json")
    print("  → p_logo_schema.json")

    # 2. B&W PNGs
    from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer
    bw = MatplotlibBWRenderer(schema)
    bw.render("p_logo_wb.png", dpi=300)
    bw.render("p_logo_bw.png", dpi=300, invert=True)
    print("  → p_logo_wb.png + p_logo_bw.png")

    # 3. SVG
    from p_logo.exporters.svg_export import export_svg
    export_svg(schema, "p_logo.svg")
    print("  → p_logo.svg")

    # 4. HTML animation
    from p_logo.exporters.html_export import export_html
    export_html(schema, "animated-p-logo-revision.html")
    print("  → animated-p-logo-revision.html")

    # 5. Cairo renders
    try:
        from p_logo.renderers.cairo_crafted import CairoCraftedRenderer
        cairo = CairoCraftedRenderer(schema)
        cairo.render("p-logo-crafted-logic-1200.png", size=1200)
        cairo.render("p-logo-crafted-logic-1200-transparent.png", size=1200, transparent=True)
        print("  → p-logo-crafted-logic-1200.png + transparent")
        if not args.quick:
            cairo.render("p-logo-crafted-logic-debug.png", size=2400, debug=True)
            print("  → p-logo-crafted-logic-debug.png")
    except ImportError:
        print("  (skipping Cairo renders — pycairo not installed)")

    # 6. V16 technical drawing
    from p_logo.renderers.v16_technical import V16TechnicalRenderer
    V16TechnicalRenderer(schema).render("geometric_p_v16.png", dpi=200)
    print("  → geometric_p_v16.png")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
