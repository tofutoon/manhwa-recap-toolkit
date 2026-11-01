#!/usr/bin/env python3
"""Split tall webtoon strips into panels, cutting only in blank gutters.

A gutter is a run of at least --min-gap rows where every row is one flat
colour (white, black or any other), within --tolerance. Each cut goes through
the middle of a gutter, so art and speech bubbles are never cut.

Examples:
    python scripts/slice_webtoon.py chapter.png -o pages
    python scripts/slice_webtoon.py chapter_folder/ -o pages --dry-run
    python scripts/slice_webtoon.py chapter.jpg -o pages --max-height 4000
"""

import argparse
import re
import sys
from pathlib import Path

from PIL import Image

# Webtoon strips are tall but narrow; 50,000 x 4,000 px is well above any real strip.
Image.MAX_IMAGE_PIXELS = 50_000 * 4_000

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
CHUNK_ROWS = 1024


def natural_key(text):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def row_stats(img):
    """Return (spread, colour) for every row.

    spread is the largest max-min range over the RGB bands of that row, so 0 means
    the row is one exact colour. The image is read in strips of CHUNK_ROWS rows,
    so only one strip is converted to RGB at a time.
    """
    width, height = img.size
    spreads, colours = [], []
    for top in range(0, height, CHUNK_ROWS):
        bottom = min(top + CHUNK_ROWS, height)
        strip = img.crop((0, top, width, bottom)).convert("RGB")
        for y in range(bottom - top):
            row = strip.crop((0, y, width, y + 1))
            extrema = row.getextrema()
            spreads.append(max(hi - lo for lo, hi in extrema))
            colours.append(tuple((lo + hi) // 2 for lo, hi in extrema))
    return spreads, colours


def find_gutters(spreads, colours, min_gap, tolerance):
    """Return (start, end) row ranges, end exclusive, of flat runs at least min_gap tall."""
    gutters = []
    start = None
    for y, spread in enumerate(spreads + [tolerance + 1]):
        flat = spread <= tolerance
        if flat and start is not None:
            # A gutter keeps one colour: a white gap next to a black gap is two gutters.
            if max(abs(a - b) for a, b in zip(colours[y], colours[start])) > tolerance:
                if y - start >= min_gap:
                    gutters.append((start, y))
                start = y
        elif flat:
            start = y
        elif start is not None:
            if y - start >= min_gap:
                gutters.append((start, y))
            start = None
    return gutters


def plan_cuts(spreads, colours, min_gap, tolerance, max_height=None):
    """Return (segments, forced) where segments are (top, bottom) ranges to save.

    Segments that are only gutter (blank margins) are dropped. forced lists the
    rows where a panel taller than max_height had to be split outside a gutter.
    """
    height = len(spreads)
    gutters = find_gutters(spreads, colours, min_gap, tolerance)
    cuts = [0] + [(a + b) // 2 for a, b in gutters] + [height]
    blank = set()
    for a, b in gutters:
        blank.update(range(a, b))

    segments, forced = [], []
    for top, bottom in zip(cuts, cuts[1:]):
        if all(y in blank for y in range(top, bottom)):
            continue
        while max_height and bottom - top > max_height:
            # Split at the flattest row in the lower half of the allowed window.
            low = top + max_height // 2
            high = top + max_height
            cut = min(range(low, high), key=lambda y: (spreads[y], -y))
            segments.append((top, cut))
            forced.append(cut)
            top = cut
        segments.append((top, bottom))
    return segments, forced


def list_inputs(path):
    if path.is_dir():
        files = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
        return sorted(files, key=lambda p: natural_key(p.name))
    if path.suffix.lower() not in IMAGE_EXTS:
        raise SystemExit(f"Not a PNG, JPG or WEBP image: {path}")
    return [path]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="an image, or a folder of images (natural sort order)")
    parser.add_argument("-o", "--out", type=Path, default=Path("pages"), help="output folder (default: pages)")
    parser.add_argument("--min-gap", type=int, default=20, help="minimum gutter height in px (default: 20)")
    parser.add_argument("--tolerance", type=int, default=8,
                        help="max colour spread in a gutter row, 0-255 (default: 8); raise it for scans or JPG noise")
    parser.add_argument("--max-height", type=int, default=None,
                        help="split panels taller than this at the flattest row, with a warning")
    parser.add_argument("--dry-run", action="store_true", help="print the planned cuts, write nothing")
    args = parser.parse_args(argv)

    if not args.input.exists():
        raise SystemExit(f"Not found: {args.input}")
    if args.max_height is not None and args.max_height < 2:
        raise SystemExit("--max-height must be at least 2")

    inputs = list_inputs(args.input)
    if not inputs:
        raise SystemExit(f"No PNG, JPG or WEBP images in {args.input}")
    if not args.dry_run:
        args.out.mkdir(parents=True, exist_ok=True)

    number = 0
    for path in inputs:
        with Image.open(path) as img:
            width, height = img.size
            spreads, colours = row_stats(img)
            segments, forced = plan_cuts(spreads, colours, args.min_gap, args.tolerance, args.max_height)
            print(f"{path.name}: {width}x{height}px -> {len(segments)} pages")
            for row in forced:
                print(f"  warning: no gutter within --max-height, cut at row {row} (flattest row found)",
                      file=sys.stderr)
            for top, bottom in segments:
                number += 1
                name = f"{number:03d}.png"
                print(f"  {name}  rows {top}-{bottom}  ({bottom - top}px)")
                if not args.dry_run:
                    img.crop((0, top, width, bottom)).save(args.out / name)
    if args.dry_run:
        print("Dry run: nothing written.")
    else:
        print(f"Wrote {number} pages to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
