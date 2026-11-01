#!/usr/bin/env python3
"""Rename page images to 001.ext, 002.ext ... in natural order (2.jpg before 10.jpg).

Dry run by default: it prints the plan and changes nothing. Add --apply to rename.
Existing files are never overwritten, and renames.csv records old and new names.

Examples:
    python scripts/renumber_pages.py chapter-12/
    python scripts/renumber_pages.py chapter-12/ --apply
"""

import argparse
import csv
import re
import sys
import uuid
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".avif"}


def natural_key(text):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def plan(folder, start=1, digits=3):
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS
             and not p.name.startswith(".")]
    files.sort(key=lambda p: natural_key(p.name))
    width = max(digits, len(str(start + len(files) - 1))) if files else digits
    return [(p, folder / f"{i:0{width}d}{p.suffix.lower()}") for i, p in enumerate(files, start)]


def check(pairs):
    """Refuse a plan that would overwrite a file outside the rename set."""
    sources = {p.name.lower() for p, _ in pairs}
    targets = [t.name.lower() for _, t in pairs]
    if len(set(targets)) != len(targets):
        raise SystemExit("Two files would get the same name; nothing renamed.")
    for _, target in pairs:
        if target.exists() and target.name.lower() not in sources:
            raise SystemExit(f"{target.name} already exists and is not part of the rename; nothing renamed.")


def apply(pairs, folder):
    # Two passes through unique temporary names, so 2.jpg -> 001.jpg cannot clash
    # with a file that is itself about to be renamed.
    tag = uuid.uuid4().hex[:8]
    temps = []
    for i, (src, _) in enumerate(pairs):
        tmp = folder / f".renumber-{tag}-{i}{src.suffix}"
        src.rename(tmp)
        temps.append(tmp)
    for tmp, (_, target) in zip(temps, pairs):
        tmp.rename(target)
    with open(folder / "renames.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["old_name", "new_name"])
        writer.writerows((src.name, target.name) for src, target in pairs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--apply", action="store_true", help="actually rename (default is a dry run)")
    parser.add_argument("--start", type=int, default=1, help="first number (default: 1)")
    parser.add_argument("--digits", type=int, default=3, help="minimum digits (default: 3)")
    args = parser.parse_args(argv)

    if not args.folder.is_dir():
        raise SystemExit(f"Not a folder: {args.folder}")
    pairs = plan(args.folder, args.start, args.digits)
    if not pairs:
        raise SystemExit(f"No image files in {args.folder}")
    check(pairs)

    changes = [(s, t) for s, t in pairs if s.name != t.name]
    for src, target in pairs:
        mark = "  " if src.name == target.name else "->"
        print(f"{src.name:<40} {mark} {target.name}")
    if not changes:
        print("Already numbered; nothing to do.")
        return 0
    if not args.apply:
        print(f"Dry run: {len(changes)} files would be renamed. Add --apply to rename.")
        return 0
    apply(pairs, args.folder)
    print(f"Renamed {len(changes)} files. Old and new names are in {args.folder / 'renames.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
