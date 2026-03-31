#!/usr/bin/env python3
"""Render P-Glyph — Crafted Logic. Supports normal + debug + transparent modes.

Outputs to build/logos/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
from p_logo import build_schema
from p_logo.renderers.cairo_crafted import CairoCraftedRenderer

LOGOS_DIR = Path(__file__).parent.parent / "build" / "logos"


def main():
    parser = argparse.ArgumentParser(description="Render P-Glyph — Crafted Logic")
    parser.add_argument("--size", type=int, default=1200, help="Output size (default: 1200)")
    parser.add_argument("--debug-size", type=int, default=2400, help="Debug output size (default: 2400)")
    parser.add_argument("--no-debug", action="store_true", help="Skip debug render")
    args = parser.parse_args()

    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    schema = build_schema()
    renderer = CairoCraftedRenderer(schema)

    modes = [
        (LOGOS_DIR / f"p_logo_cairo_{args.size}.png", args.size, False, False, "dark"),
        (LOGOS_DIR / f"p_logo_cairo_{args.size}_transparent.png", args.size, False, True, "transparent"),
    ]
    if not args.no_debug:
        modes.append((LOGOS_DIR / f"p_logo_cairo_debug_{args.debug_size}.png", args.debug_size, True, False, "debug"))

    for out, dim, dbg, tr, label in modes:
        print(f"Rendering {dim}×{dim} ({label})...")
        renderer.render(str(out), size=dim, debug=dbg, transparent=tr)
        size_kb = out.stat().st_size / 1024
        print(f"  {out.name}: {size_kb:.0f} KB")

    print(f"Done — outputs in build/logos/")


if __name__ == "__main__":
    main()
