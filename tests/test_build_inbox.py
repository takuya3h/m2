import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_inbox import collect, render  # noqa: E402


def test_collect_reads_every_file(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("- [ ] one\n", encoding="utf-8")
    (d / "T-2026-01-02-beta.md").write_text("- [ ] two\n- [x] three\n", encoding="utf-8")
    entries = collect(d)
    assert len(entries) == 3


def test_render_is_deterministic(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("- [ ] one\n", encoding="utf-8")
    (d / "T-2026-01-02-beta.md").write_text("- [ ] two\n", encoding="utf-8")
    assert render(collect(d)) == render(collect(d))


def test_render_separates_open_and_done(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("- [ ] open\n- [x] done\n", encoding="utf-8")
    text = render(collect(d))
    assert "open" in text and "done" in text


def test_empty_directory_does_not_crash(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    assert isinstance(render(collect(d)), str)


def test_malformed_lines_are_ignored(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("見出し\n- [ ] valid\n\n", encoding="utf-8")
    assert len(collect(d)) == 1


def test_generated_header_marks_it_as_generated(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("- [ ] x\n", encoding="utf-8")
    text = render(collect(d))
    assert "生成" in text
