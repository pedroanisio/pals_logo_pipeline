#!/usr/bin/env python3
"""Render P-Glyph — Crafted Logic. Supports normal + debug + transparent modes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
from pathlib import Path
from p_logo import build_schema
from p_logo.renderers.cairo_crafted import CairoCraftedRenderer


def main():
    parser = argparse.ArgumentParser(description="Render P-Glyph — Crafted Logic")
    parser.add_argument("--size", type=int, default=1200, help="Output size (default: 1200)")
    parser.add_argument("--debug-size", type=int, default=2400, help="Debug output size (default: 2400)")
    parser.add_argument("--no-debug", action="store_true", help="Skip debug render")
    args = parser.parse_args()

    schema = build_schema()
    renderer = CairoCraftedRenderer(schema)

    modes = [
        (f"p-logo-crafted-logic-{args.size}.png", args.size, False, False, "dark"),
        (f"p-logo-crafted-logic-{args.size}-transparent.png", args.size, False, True, "transparent"),
    ]
    if not args.no_debug:
        modes.append((f"p-logo-crafted-logic-debug.png", args.debug_size, True, False, "debug"))

    for out, dim, dbg, tr, label in modes:
        print(f"Rendering {dim}×{dim} ({label})...")
        renderer.render(out, size=dim, debug=dbg, transparent=tr)
        size_kb = Path(out).stat().st_size / 1024
        print(f"  {out}: {size_kb:.0f} KB")

    print("Done.")


if __name__ == "__main__":
    main()
