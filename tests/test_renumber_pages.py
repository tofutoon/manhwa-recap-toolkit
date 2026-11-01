import csv

import pytest

import renumber_pages


def make(folder, names):
    for name in names:
        (folder / name).write_bytes(name.encode())


def test_natural_order_dry_run(tmp_path, capsys):
    make(tmp_path, ["10.jpg", "2.jpg", "1.jpg", "notes.txt"])
    renumber_pages.main([str(tmp_path)])
    assert sorted(p.name for p in tmp_path.iterdir()) == ["1.jpg", "10.jpg", "2.jpg", "notes.txt"]
    out = capsys.readouterr().out
    assert out.index("2.jpg") < out.index("10.jpg")


def test_apply_renames_and_logs(tmp_path):
    make(tmp_path, ["page 10.JPG", "page 2.jpg", "page 1.png"])
    renumber_pages.main([str(tmp_path), "--apply"])
    assert (tmp_path / "001.png").read_bytes() == b"page 1.png"
    assert (tmp_path / "002.jpg").read_bytes() == b"page 2.jpg"
    assert (tmp_path / "003.jpg").read_bytes() == b"page 10.JPG"
    rows = list(csv.reader(open(tmp_path / "renames.csv", encoding="utf-8")))
    assert rows[0] == ["old_name", "new_name"] and len(rows) == 4


def test_swap_inside_set_is_safe(tmp_path):
    # 2.jpg must become 001.jpg while 001.jpg itself moves to 002.jpg.
    make(tmp_path, ["001.jpg", "0.jpg"])
    renumber_pages.main([str(tmp_path), "--apply"])
    assert (tmp_path / "001.jpg").read_bytes() == b"0.jpg"
    assert (tmp_path / "002.jpg").read_bytes() == b"001.jpg"


def test_never_overwrites_outside_file(tmp_path):
    make(tmp_path, ["a.jpg", "b.png"])
    (tmp_path / "001.jpg").mkdir()  # not a file, so not in the set, but the name is taken
    with pytest.raises(SystemExit):
        renumber_pages.main([str(tmp_path), "--apply"])
    assert (tmp_path / "a.jpg").exists()


def test_wide_numbers(tmp_path):
    make(tmp_path, [f"{i}.png" for i in range(1, 1002)])
    pairs = renumber_pages.plan(tmp_path)
    assert pairs[0][1].name == "0001.png" and pairs[-1][1].name == "1001.png"
