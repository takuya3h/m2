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


# --- results_recent.md（報告の転記） ---------------------------------------
#
# **要約しない。転記する。** 散文の解釈は捏造を生むため、投影は構造化された
# 記述をそのまま写す。原文と一致しなければ要約が入っている。

GATE_NOTE = "目印ありで HEAD が不変、目印なしで merge と push が発火した"
DEFECT_NOTE = (
    "実態を測る指示が数字を含む対象を落としており、その一覧を信じると実在する操作を"
    "存在しないと誤判定する。指示どおり実行すると正しい記述を書き換えてしまう"
)
DEVIATION_NOTE = "契約の測り方が誤っていたため、実施せず元へ戻した"

RESULT_V2 = {
    "result_version": 2,
    "task_id": "T-2026-02-02-beta",
    "status": "pass",
    "host": "lecun",
    "branch": "feat/beta",
    "pr": 73,
    "merged": False,
    "gates": [{"id": "G1", "verdict": "pass", "note": GATE_NOTE}],
    "tests": {"before_failed": 5, "after_failed": 5, "after_passed": 314},
    "deviations": [{"type": "spec_defect", "note": DEVIATION_NOTE}],
    "issuer_defects": [{"type": "check_does_not_check", "note": DEFECT_NOTE}],
    "followups": ["数の主張に検査が無い"],
    "unknowns": ["他ホストでは未実行"],
    "commits": ["abc1234"],
}


def _make_v2(tmp_path, task_ids):
    tasks = tmp_path / "tasks"
    for task_id in task_ids:
        d = tasks / task_id
        d.mkdir(parents=True)
        spec = dict(SPEC, meta=dict(SPEC["meta"], task_id=task_id))
        (d / "spec.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
        res = dict(RESULT_V2, task_id=task_id)
        (d / "result.yaml").write_text(yaml.safe_dump(res, allow_unicode=True), encoding="utf-8")
    return tasks


def test_results_recent_transcribes_verbatim(tmp_path):
    tasks = _make_v2(tmp_path, ["T-2026-02-02-beta"])
    text = build_taskindex.render_results_recent(build_taskindex.collect(tasks))
    for original in (GATE_NOTE, DEFECT_NOTE, DEVIATION_NOTE, "数の主張に検査が無い", "他ホストでは未実行"):
        assert original in text, f"転記されていない: {original}"


def test_results_recent_marks_it_as_generated(tmp_path):
    """生成物であることが**冒頭**に書かれること。

    冒頭は「最初の契約の見出しより前」と定める。行数で測ると、書式を少し変える
    たびに試験が壊れて中身を確かめなくなる。
    """
    tasks = _make_v2(tmp_path, ["T-2026-02-02-beta"])
    text = build_taskindex.render_results_recent(build_taskindex.collect(tasks))
    head = text.split("\n## ", 1)[0]
    assert "生成" in head and "手で編集しない" in head


def test_results_recent_is_newest_first(tmp_path):
    tasks = _make_v2(tmp_path, ["T-2026-01-01-alpha", "T-2026-03-03-gamma"])
    text = build_taskindex.render_results_recent(build_taskindex.collect(tasks))
    assert text.index("T-2026-03-03-gamma") < text.index("T-2026-01-01-alpha")


def test_results_recent_limit_applies(tmp_path):
    ids = [f"T-2026-0{i}-01-task{i}" for i in range(1, 8)]
    tasks = _make_v2(tmp_path, ids)
    text = build_taskindex.render_results_recent(build_taskindex.collect(tasks), limit=3)
    assert text.count("## T-") == 3
    assert ids[-1] in text and ids[0] not in text


def test_results_recent_states_where_the_rest_is(tmp_path):
    ids = [f"T-2026-0{i}-01-task{i}" for i in range(1, 8)]
    tasks = _make_v2(tmp_path, ids)
    text = build_taskindex.render_results_recent(build_taskindex.collect(tasks), limit=3)
    head = "\n".join(text.splitlines()[:12])
    assert "result.yaml" in head and "3" in head


def test_results_recent_empty_does_not_crash(tmp_path):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    text = build_taskindex.render_results_recent(build_taskindex.collect(tasks))
    assert isinstance(text, str) and text


def test_results_recent_accepts_version_1(tmp_path):
    """版 1 は gates に note を持たず deviations が整数。落ちてはならない。"""
    tasks = _make(tmp_path)
    text = build_taskindex.render_results_recent(build_taskindex.collect(tasks))
    assert "T-2026-01-01-alpha" in text


def test_results_recent_is_deterministic_and_has_no_wall_clock(tmp_path):
    import re

    tasks = _make_v2(tmp_path, ["T-2026-02-02-beta"])
    rows = build_taskindex.collect(tasks)
    text = build_taskindex.render_results_recent(rows)
    assert text == build_taskindex.render_results_recent(rows)
    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text)
