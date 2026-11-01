import random

from PIL import Image, ImageDraw

import slice_webtoon


def noisy_panel(width, height, seed):
    rng = random.Random(seed)
    # A left-to-right gradient, like shaded art: no row inside the panel is flat.
    img = Image.linear_gradient("L").transpose(Image.Transpose.ROTATE_90).resize((width, height)).convert("RGB")
    draw = ImageDraw.Draw(img)
    for _ in range(80):
        x, y = rng.randrange(width), rng.randrange(height)
        draw.ellipse((x, y, x + 12, y + 12), fill=(rng.randrange(256), 0, rng.randrange(256)))
    # A speech bubble with a white middle: flat rows inside it must not become a cut.
    draw.ellipse((10, height // 2 - 30, width - 10, height // 2 + 30), fill="white", outline="black", width=3)
    return img


def build_strip(panel_heights, gap, colour=(255, 255, 255), width=200):
    total = sum(panel_heights) + gap * (len(panel_heights) + 1)
    strip = Image.new("RGB", (width, total), colour)
    y = gap
    bounds = []
    for i, h in enumerate(panel_heights):
        strip.paste(noisy_panel(width, h, i), (0, y))
        bounds.append((y, y + h))
        y += h + gap
    return strip, bounds


def test_cuts_only_in_gutters(tmp_path):
    strip, bounds = build_strip([300, 450, 250], gap=40)
    path = tmp_path / "strip.png"
    strip.save(path)
    out = tmp_path / "pages"
    assert slice_webtoon.main([str(path), "-o", str(out)]) == 0
    files = sorted(out.iterdir())
    assert [f.name for f in files] == ["001.png", "002.png", "003.png"]
    spreads, colours = slice_webtoon.row_stats(strip)
    segments, forced = slice_webtoon.plan_cuts(spreads, colours, 20, 8)
    assert forced == []
    for (top, bottom), (p_top, p_bottom) in zip(segments, bounds):
        assert top <= p_top and bottom >= p_bottom  # whole panel kept
        assert p_top - top < 40 and bottom - p_bottom < 40  # cut inside the gutter


def test_black_gutters_and_small_gap_ignored():
    strip, _ = build_strip([200, 200], gap=30, colour=(0, 0, 0))
    spreads, colours = slice_webtoon.row_stats(strip)
    segments, _ = slice_webtoon.plan_cuts(spreads, colours, 20, 8)
    assert len(segments) == 2
    segments, _ = slice_webtoon.plan_cuts(spreads, colours, 40, 8)  # gap smaller than --min-gap
    assert len(segments) == 1


def test_max_height_splits_and_warns(tmp_path, capsys):
    strip, _ = build_strip([300, 1500], gap=40)
    path = tmp_path / "tall.png"
    strip.save(path)
    out = tmp_path / "pages"
    slice_webtoon.main([str(path), "-o", str(out), "--max-height", "600"])
    captured = capsys.readouterr()
    assert "warning" in captured.err
    heights = [Image.open(f).height for f in sorted(out.iterdir())]
    assert all(h <= 600 for h in heights)
    assert sum(heights) <= strip.height


def test_dry_run_writes_nothing(tmp_path, capsys):
    strip, _ = build_strip([200, 200], gap=30)
    path = tmp_path / "s.jpg"
    strip.save(path, quality=95)
    out = tmp_path / "pages"
    slice_webtoon.main([str(path), "-o", str(out), "--dry-run", "--tolerance", "20"])
    assert not out.exists()
    assert "002.png" in capsys.readouterr().out


def test_folder_input_natural_order(tmp_path):
    folder = tmp_path / "in"
    folder.mkdir()
    for name, h in [("10.png", 100), ("2.png", 200)]:
        build_strip([h], gap=30)[0].save(folder / name)
    out = tmp_path / "pages"
    slice_webtoon.main([str(folder), "-o", str(out)])
    # 2.png comes first, so 001.png holds the 200 px panel.
    assert Image.open(out / "001.png").height > Image.open(out / "002.png").height


def test_very_tall_strip_row_stats():
    img = Image.new("RGB", (64, 50_000), "white")
    spreads, _ = slice_webtoon.row_stats(img)
    assert len(spreads) == 50_000 and max(spreads) == 0
