import csv

import srt_tight_cues

SRT = """1
00:00:01,000 --> 00:00:03,000
Jin froze at the gate.

2
00:00:03,000 --> 00:00:04,000
Seo screamed at him to run, and the wall behind them gave way.

3
00:00:04,000 --> 00:00:04,000
<i>Run!</i>

4
01:00:00,500 --> 01:00:02,500
Twelve mana points left.
"""

VTT = """WEBVTT

intro
00:01.000 --> 00:02.000 align:start
One two three four five six.
"""


def test_finds_known_tight_cues(tmp_path, capsys):
    path = tmp_path / "ep.srt"
    path.write_text(SRT, encoding="utf-8")
    out_csv = tmp_path / "tight.csv"
    srt_tight_cues.main([str(path), "--csv", str(out_csv)])
    rows = list(csv.DictReader(open(out_csv, encoding="utf-8")))
    assert [r["cue"] for r in rows] == ["2", "3"]  # 13 words in 1 s, and a zero-length cue
    assert rows[0]["words"] == "13"
    assert "2 of 4 cues" in capsys.readouterr().out


def test_vtt_and_custom_limit():
    cues = srt_tight_cues.parse(VTT)
    assert len(cues) == 1 and cues[0]["text"] == "One two three four five six."
    assert srt_tight_cues.tight_cues(cues, 2.5)[0]["wps"] == 6.0
    assert srt_tight_cues.tight_cues(cues, 6.0) == []


def test_hour_timestamps_and_contractions():
    cues = srt_tight_cues.parse(SRT)
    assert cues[3]["start"] == 3600.5
    assert srt_tight_cues.count_words("I can't die yet.") == 4
