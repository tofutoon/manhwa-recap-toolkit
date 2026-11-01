#!/usr/bin/env python3
"""List SRT or VTT cues with too many words for their time window.

A voice reading about 150 words per minute speaks 2.5 words per second. Cues above
--wps words per second will sound rushed, or overrun into the next cue.

Examples:
    python scripts/srt_tight_cues.py episode.srt
    python scripts/srt_tight_cues.py episode.vtt --wps 2.2 --csv tight.csv
"""

import argparse
import csv
import re
import sys
from pathlib import Path

TIME = r"(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})"
TIMING = re.compile(TIME + r"\s*-->\s*" + TIME)
TAG = re.compile(r"<[^>]+>|\{\\[^}]*\}")


def to_seconds(h, m, s, ms):
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def fmt(seconds):
    total_ms = round(seconds * 1000)
    h, rest = divmod(total_ms, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse(text):
    """Return a list of cues: dicts with index, start, end, text. Works for SRT and VTT."""
    cues = []
    blocks = re.split(r"\r?\n\s*\r?\n", text.lstrip("﻿").strip())
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            match = TIMING.search(line)
            if match:
                g = match.groups()
                body = " ".join(TAG.sub("", t) for t in lines[i + 1:])
                cues.append({"index": len(cues) + 1, "start": to_seconds(*g[:4]),
                             "end": to_seconds(*g[4:]), "text": body.strip()})
                break
    return cues


def count_words(text):
    return len(re.findall(r"[^\W_]+(?:['’-][^\W_]+)*", text))


def tight_cues(cues, wps):
    rows = []
    for cue in cues:
        words = count_words(cue["text"])
        seconds = cue["end"] - cue["start"]
        rate = words / seconds if seconds > 0 else float("inf")
        if words and rate > wps:
            rows.append({"cue": cue["index"], "start": fmt(cue["start"]), "end": fmt(cue["end"]),
                         "words": words, "seconds": round(seconds, 2), "wps": round(rate, 2),
                         "text": cue["text"]})
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("subtitle", type=Path, help="an .srt or .vtt file")
    parser.add_argument("--wps", type=float, default=2.5, help="words per second limit (default: 2.5, about 150 wpm)")
    parser.add_argument("--csv", type=Path, help="also write the table to this CSV file")
    args = parser.parse_args(argv)

    cues = parse(args.subtitle.read_text(encoding="utf-8-sig", errors="replace"))
    if not cues:
        raise SystemExit(f"No cues found in {args.subtitle}")
    rows = tight_cues(cues, args.wps)

    if rows:
        print(f"{'cue':>5}  {'start':<12}  {'words':>5}  {'sec':>6}  {'wps':>5}  text")
        for r in rows:
            wps = "inf" if r["wps"] == float("inf") else f"{r['wps']:.2f}"
            text = r["text"] if len(r["text"]) <= 50 else r["text"][:47] + "..."
            print(f"{r['cue']:>5}  {r['start']:<12}  {r['words']:>5}  {r['seconds']:>6.2f}  {wps:>5}  {text}")
    print(f"{len(rows)} of {len(cues)} cues are above {args.wps:g} words per second.")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["cue", "start", "end", "words", "seconds", "wps", "text"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
