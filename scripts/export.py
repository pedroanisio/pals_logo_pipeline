#!/usr/bin/env python3
"""
Export P Logo — static 2000×2000 PNG + animated GIF.

Thin wrapper around p_logo library. Outputs to build/logos/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
from p_logo import build_schema
from p_logo.renderers.cairo_crafted import CairoCraftedRenderer, HAS_CAIRO
from p_logo.exporters.gif_export import export_gif

LOGOS_DIR = Path(__file__).parent.parent / "build" / "logos"


def main():
    parser = argparse.ArgumentParser(description="Export P Logo — static PNG + animated GIF")
    parser.add_argument("--static-size", type=int, default=2000)
    parser.add_argument("--gif-size", type=int, default=800)
    parser.add_argument("--frames", type=int, default=180)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--no-gif", action="store_true")
    parser.add_argument("--no-static", action="store_true")
    args = parser.parse_args()

    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    schema = build_schema()

    if not args.no_static:
        if HAS_CAIRO:
            out_name = f"p_logo_cairo_{args.static_size}.png"
            print(f"Rendering static {args.static_size}×{args.static_size} PNG...")
            CairoCraftedRenderer(schema).render(str(LOGOS_DIR / out_name), size=args.static_size)
            print(f"  → {out_name}")
        else:
            print("Skipping static PNG (pycairo not installed)")

    if not args.no_gif:
        duration_ms = max(1, 1000 // args.fps)
        out_name = "p_logo_animated.gif"
        print(f"Rendering {args.frames}-frame animated GIF at {args.gif_size}×{args.gif_size} (~{args.fps} FPS)...")
        export_gif(schema, str(LOGOS_DIR / out_name),
                   n_frames=args.frames, duration_ms=duration_ms, size=args.gif_size)
        print(f"  → {out_name} ({args.frames} frames, {duration_ms}ms/frame)")

    print("Done — outputs in build/logos/")


if __name__ == "__main__":
    main()
