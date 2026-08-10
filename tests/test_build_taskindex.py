"""実装の投影（tasks_summary.csv / followups.md）の検査。

**壁時計を使わない**ため、同じ入力からは必ず同じ出力になる。
時刻が混ざると、検査が「手による編集」と「時刻の経過」を区別できない。
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_taskindex  # noqa: E402

SPEC = {
    "spec_version": 1,
    "meta": {"task_id": "T-2026-01-01-alpha", "kind": "impl", "depends_on": ["T-2025-12-31-zero"]},
}
RESULT = {
    "result_version": 1,
    "task_id": "T-2026-01-01-alpha",
    "status": "pass",
    "host": "lecun",
    "branch": "feat/alpha",
    "pr": 42,
    "merged": True,
    "gates": [
        {"id": "G1", "verdict": "pass"},
        {"id": "G2", "verdict": "ask"},
        {"id": "G3", "verdict": "stop"},
    ],
    "tests": {"before_failed": 5, "after_failed": 5, "after_passed": 100},
    "deviations": 3,
    "issuer_defects": [
        {"type": "check_does_not_check", "note": "a"},
        {"type": "check_does_not_check", "note": "b"},
        {"type": "shell_assumption", "note": "c"},
    ],
    "followups": ["他ホストでの動作は未検証である。統合後に各台で確認する"],
    "unknowns": ["停止時期は測れなかった"],
    "commits": ["abc1234"],
}


def _make(tmp_path, *, with_result=True, task_id="T-2026-01-01-alpha"):
    tasks = tmp_path / "tasks"
    d = tasks / task_id
    d.mkdir(parents=True)
    spec = dict(SPEC)
    spec["meta"] = dict(SPEC["meta"], task_id=task_id)
    (d / "spec.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    if with_result:
        res = dict(RESULT, task_id=task_id)
        (d / "result.yaml").write_text(yaml.safe_dump(res, allow_unicode=True), encoding="utf-8")
    return tasks


def test_contracts_without_a_result_do_not_appear(tmp_path):
    tasks = _make(tmp_path, with_result=False)
    assert build_taskindex.collect(tasks) == []


def test_render_is_deterministic(tmp_path):
    tasks = _make(tmp_path)
    rows = build_taskindex.collect(tasks)
    assert build_taskindex.render_summary(rows) == build_taskindex.render_summary(rows)
    assert build_taskindex.render_followups(rows) == build_taskindex.render_followups(rows)


def test_followup_text_is_transcribed_not_summarised(tmp_path):
    tasks = _make(tmp_path)
    text = build_taskindex.render_followups(build_taskindex.collect(tasks))
    assert "他ホストでの動作は未検証である。統合後に各台で確認する" in text
    assert "T-2026-01-01-alpha" in text


def test_defect_types_are_counted(tmp_path):
    tasks = _make(tmp_path)
    text = build_taskindex.render_followups(build_taskindex.collect(tasks))
    # check_does_not_check が 2 件、shell_assumption が 1 件
    assert "| `check_does_not_check` | 2 |" in text
    assert "| `shell_assumption` | 1 |" in text


def test_summary_counts_gate_verdicts(tmp_path):
    tasks = _make(tmp_path)
    csv_text = build_taskindex.render_summary(build_taskindex.collect(tasks))
    line = [ln for ln in csv_text.splitlines() if ln.startswith("T-2026-01-01-alpha")][0]
    cells = line.split(",")
    header = [ln for ln in csv_text.splitlines() if ln.startswith("task_id")][0].split(",")
    row = dict(zip(header, cells))
    assert row["gates_pass"] == "1" and row["gates_ask"] == "1" and row["gates_stop"] == "1"
    assert row["kind"] == "impl"
    assert row["depends_on"] == "T-2025-12-31-zero"
    assert row["n_issuer_defects"] == "3"


def test_empty_directory_does_not_crash(tmp_path):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    rows = build_taskindex.collect(tasks)
    assert isinstance(build_taskindex.render_summary(rows), str)
    assert isinstance(build_taskindex.render_followups(rows), str)


def test_generated_header_marks_it_as_generated(tmp_path):
    tasks = _make(tmp_path)
    rows = build_taskindex.collect(tasks)
    assert "生成" in build_taskindex.render_summary(rows)
    assert "生成" in build_taskindex.render_followups(rows)


def test_no_wall_clock_in_output(tmp_path):
    """壁時計を使わない。日時が混ざると検査が編集と時刻を区別できない。"""
    tasks = _make(tmp_path)
    rows = build_taskindex.collect(tasks)
    import re

    for text in (build_taskindex.render_summary(rows), build_taskindex.render_followups(rows)):
        assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text)
