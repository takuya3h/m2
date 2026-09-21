"""比較の対称性の関門の試験（T-2026-09-19-symmetry-gate）。**対照は両方向に置く。**

判定が通ったことは、判定が働いていることを意味しない。したがって規則ごとに
「落ちるはずの入力」と「通るはずの入力」を対で置く。

正本は `context/conventions.md` の `symmetry` 節。検査器は写しを持たない。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_proposal  # noqa: E402
import preflight_task  # noqa: E402
import validate_task  # noqa: E402

TEMPLATE_PREREG = REPO_ROOT / "tasks" / "_templates" / "exp" / "prereg.md"
CHECKLIST = REPO_ROOT / "docs" / "symmetry-checklist.md"
DEFECTS = REPO_ROOT / "docs" / "issuer-defects.md"

HEADER = "| 条件 | 腕1 | 腕2 | 判定 | 理由 |\n|---|---|---|---|---|\n"


def _prereg(tmp_path: Path, task_id: str, body: str) -> Path:
    """契約の置き場に prereg.md を置く。P13 は task_id から場所を引く。"""
    task_dir = tmp_path / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "prereg.md").write_text(body, encoding="utf-8")
    return task_dir


@pytest.fixture
def tasks_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight_task, "TASKS_DIR", tmp_path)
    return tmp_path


# --- 規約 -----------------------------------------------------------------

def test_symmetry_anchor_exists():
    """完了判定 a。`conventions#symmetry` が L2 の解決先として引ける。"""
    assert "symmetry" in validate_task.conventions_anchors()


def test_absent_anchor_is_not_resolvable():
    """陽性対照。存在しない名では引けない。**常に真を返す壊れ方と区別する。**"""
    assert "symmetry_zz" not in validate_task.conventions_anchors()


def test_symmetry_section_states_the_column_names():
    text = (REPO_ROOT / "context" / "conventions.md").read_text(encoding="utf-8")
    section = text.split('<a id="symmetry"></a>', 1)[1]
    assert "| 条件 | 腕1 | 腕2 | 判定 | 理由 |" in section
    for verdict in preflight_task.SYMMETRY_VERDICTS:
        assert verdict in section


# --- P13 の適用範囲（完了判定 d） -----------------------------------------

@pytest.mark.parametrize("kind", ["impl", "analysis"])
def test_p13_skips_for_non_exp(kind):
    spec = {"meta": {"kind": kind}, "plan": {"env": {}}}
    assert preflight_task.decide_applicability(spec)["P13"] is False


def test_p13_applies_for_exp():
    spec = {"meta": {"kind": "exp"}, "plan": {"env": {}}}
    assert preflight_task.decide_applicability(spec)["P13"] is True


def test_p13_is_last_and_p1_to_p12_are_unchanged():
    """既存の番号・順序・名前を変えていない。"""
    ids = sorted(preflight_task.CHECK_NAMES, key=lambda c: int(c[1:]))
    assert ids[-1] == "P13"
    assert ids[:12] == [f"P{n}" for n in range(1, 13)]
    assert preflight_task.CHECK_NAMES["P13"] == "symmetry_table_complete"


# --- P13 の判定（完了判定 d） ---------------------------------------------

def test_p13_fails_without_prereg(tasks_dir):
    (tasks_dir / "T-x").mkdir()
    check = preflight_task.check_symmetry_table("T-x")
    assert check.status == "FAIL"
    assert "prereg.md" in check.detail


def test_p13_fails_without_table(tasks_dir):
    _prereg(tasks_dir, "T-x", "# 事前登録\n\n表は無い。\n")
    check = preflight_task.check_symmetry_table("T-x")
    assert check.status == "FAIL"
    assert "対称性の表が無い" in check.detail


def test_p13_fails_on_unknown_row(tasks_dir):
    body = HEADER + "| 凍結範囲 | stem | stem | 揃える | |\n| 学習率 | | | UNKNOWN | |\n"
    _prereg(tasks_dir, "T-x", body)
    check = preflight_task.check_symmetry_table("T-x")
    assert check.status == "FAIL"
    assert "UNKNOWN 1 行" in check.detail
    assert "学習率" in check.detail


def test_p13_fails_on_intended_without_reason(tasks_dir):
    body = HEADER + "| 前処理 | detr | 反転 | 意図的に変える | |\n"
    _prereg(tasks_dir, "T-x", body)
    check = preflight_task.check_symmetry_table("T-x")
    assert check.status == "FAIL"
    assert "理由が無い 1 行" in check.detail


def test_p13_fails_on_blank_verdict(tasks_dir):
    """判定が空欄の行を通さない。**空欄を許すと埋めないまま起票できる。**"""
    body = HEADER + "| 学習率 | 1e-4 | 1e-4 | | |\n"
    _prereg(tasks_dir, "T-x", body)
    check = preflight_task.check_symmetry_table("T-x")
    assert check.status == "FAIL"
    assert "三値でない" in check.detail


def test_p13_passes_when_complete(tasks_dir):
    body = HEADER + (
        "| 凍結範囲 | stem のみ | stem のみ | 揃える | |\n"
        "| 前処理 | presets.detr | 反転のみ | 意図的に変える | box 用の増強は工程に使わない |\n"
    )
    _prereg(tasks_dir, "T-x", body)
    check = preflight_task.check_symmetry_table("T-x")
    assert check.status == "PASS"
    assert "2 行" in check.detail


# --- 表の同定（完了判定 d の「部分一致で別の表を拾わない」） ---------------

def test_p13_does_not_pick_a_table_with_similar_column_names(tasks_dir):
    """列名が部分一致するだけの別の表を対称性の表と見なさない。"""
    body = (
        "| 条件の分類 | 腕の数 | 判定規約 | 理由の欄 |\n|---|---|---|---|\n"
        "| 主判定 | 2 | abs(delta)/sigma >= 1 | 事前登録 |\n"
    )
    _prereg(tasks_dir, "T-x", body)
    check = preflight_task.check_symmetry_table("T-x")
    assert check.status == "FAIL"
    assert "対称性の表が無い" in check.detail


def test_p13_finds_the_right_table_when_another_table_precedes(tasks_dir):
    """様式に合う表があれば、手前に別の表があっても拾う。**両方向で確かめる。**"""
    other = "| 指標 | 値 |\n|---|---|\n| val | 0.387 |\n\n"
    body = other + HEADER + "| 凍結範囲 | stem | stem | 揃える | |\n"
    _prereg(tasks_dir, "T-x", body)
    assert preflight_task.check_symmetry_table("T-x").status == "PASS"


def test_p13_requires_two_arms(tasks_dir):
    """腕が一つの表は比較の表ではない。"""
    body = "| 条件 | 腕1 | 判定 | 理由 |\n|---|---|---|---|\n| 凍結範囲 | stem | 揃える | |\n"
    _prereg(tasks_dir, "T-x", body)
    assert preflight_task.check_symmetry_table("T-x").status == "FAIL"


# --- 雛形（完了判定 f） ---------------------------------------------------

def test_template_has_the_skeleton():
    assert TEMPLATE_PREREG.exists()
    assert "conventions#symmetry" in TEMPLATE_PREREG.read_text(encoding="utf-8")


def test_template_prereg_fails_p13_with_every_row_unknown(tasks_dir):
    """雛形のままでは起票できない。FAIL の行数が表の行数と一致する。"""
    body = TEMPLATE_PREREG.read_text(encoding="utf-8")
    _prereg(tasks_dir, "T-x", body)
    check = preflight_task.check_symmetry_table("T-x")
    assert check.status == "FAIL"
    tables = preflight_task.symmetry_tables(body)
    rows = sum(len(b) for _, b in tables)
    assert rows == 15
    assert f"UNKNOWN {rows} 行" in check.detail


# --- 提案カード（完了判定 e） ---------------------------------------------

def test_conventions_card_has_fifteen_and_sixteen():
    items = check_proposal.card_items()
    assert sorted(items) == list(range(1, 17))
    assert "conventions#symmetry" in items[15]
    assert "交絡" in items[16]


def test_expected_card_items_matches_conventions():
    """検査器が持つ件数と規約が一致する。**片方だけ古くならないように縛る。**"""
    assert len(check_proposal.card_items()) == check_proposal.EXPECTED_CARD_ITEMS


def _card(missing: int | None = None) -> str:
    lines = ["# 提案カード\n"]
    for num in range(1, 17):
        if num == missing:
            continue
        lines.append(f"## #{num} 項目\n")
        lines.append("見積もりは 0.02 である。\n")
    return "\n".join(lines)


@pytest.mark.parametrize("num", [15, 16])
def test_card_missing_new_item_is_detected(num, tmp_path):
    """陽性対照。#15 か #16 を欠く文書で不足 1 件。"""
    path = tmp_path / "proposal.md"
    path.write_text(_card(missing=num), encoding="utf-8")
    report = check_proposal.check(path, only="card")
    assert report["hits_by_kind"]["missing_heading"] == 1
    assert f"#{num}" in report["findings"][0]["detail"]


def test_card_with_both_new_items_is_zero(tmp_path):
    """陰性対照。#15 と #16 が揃えば不足 0 件。"""
    path = tmp_path / "proposal.md"
    path.write_text(_card(), encoding="utf-8")
    report = check_proposal.check(path, only="card")
    assert report["hits"] == 0
    assert report["errors"] == []


def test_numeric_items_did_not_change():
    """#15 の注記を足しても、数値を求める項目は #5 #6 #10 のままである。"""
    assert sorted(check_proposal.numeric_items()) == [5, 6, 10]


def test_forbidden_words_did_not_change():
    assert len(check_proposal.forbidden_words()) == 15


# --- 点検表と欠陥記録（完了判定 g） ---------------------------------------

def test_checklist_exists_and_points_at_the_convention():
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "context/conventions.md の symmetry 節" in text
    assert "symmetry_table_complete" in text


@pytest.mark.parametrize("name", ["asymmetric_comparison", "rule_read_narrowly"])
def test_issuer_defects_has_the_new_types(name):
    assert name in DEFECTS.read_text(encoding="utf-8")


# --- 完了済み契約は P13 の対象外（T-2026-09-19-p13-skip-and-enum） ----------
#
# 関門はこれから起票する契約に効かせるものであり、過去の契約の再現や追試を妨げない。
# **対照は両方向に置く。** 印があれば SKIP、無ければ従来どおり検査する。

def _result(tasks_dir: Path, task_id: str, body: str) -> None:
    task_dir = tasks_dir / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "result.yaml").write_text(body, encoding="utf-8")


def test_completed_contract_is_skipped(tasks_dir):
    """完了判定 a。verdict があれば表を見ずに SKIP し、理由に完了済みと出す。"""
    _prereg(tasks_dir, "T-2026-08-01-done", "表なし\n")
    _result(tasks_dir, "T-2026-08-01-done", "gates:\n  - {id: G1, verdict: pass}\n")
    check = preflight_task.check_symmetry_table("T-2026-08-01-done")
    assert check.status == "SKIP"
    assert "完了済み" in check.detail


@pytest.mark.parametrize(
    "body",
    [
        "gates: []\n",                            # 表はあるが verdict が無い
        'gates:\n  - {id: G1, verdict: ""}\n',    # verdict が空文字
        "gates:\n  - {id: G1}\n",                 # verdict の項目が無い
        "status: pass\n",                         # gates 自体が無い
        "gates: [ {id: G1,\n",                    # 壊れた YAML
        "- これは対応表ではない\n",                # 最上位が辞書でない
    ],
)
def test_result_without_verdict_is_not_treated_as_completed(tasks_dir, body):
    """完了判定 c の陽性対照。**印が無ければ従来どおり FAIL する。**

    印を読み損ねたときに黙って SKIP へ倒れると、関門が誰も救わないまま通る。
    """
    _prereg(tasks_dir, "T-2026-08-01-half", "表なし\n")
    _result(tasks_dir, "T-2026-08-01-half", body)
    assert preflight_task.check_symmetry_table("T-2026-08-01-half").status == "FAIL"


def test_name_containing_a_completed_task_id_is_not_completed(tasks_dir):
    """完了判定 c。**名前の部分一致で完了済みと誤認しない。**"""
    _result(tasks_dir, "T-2026-08-01-done", "gates:\n  - {id: G1, verdict: pass}\n")
    _prereg(tasks_dir, "T-2026-08-01-done-followup", "表なし\n")
    check = preflight_task.check_symmetry_table("T-2026-08-01-done-followup")
    assert check.status == "FAIL"


def test_incomplete_contract_keeps_passing_when_the_table_is_filled(tasks_dir):
    """完了判定 b。未完了の挙動は変えない。埋まった表は従来どおり PASS。"""
    body = HEADER + "| 学習率 | 1e-4 | 1e-4 | 揃える |  |\n"
    _prereg(tasks_dir, "T-2026-09-20-new", body)
    assert preflight_task.check_symmetry_table("T-2026-09-20-new").status == "PASS"


def test_completed_verdicts_reads_only_the_gates(tasks_dir):
    """印の出どころを固定する。**`verdict` は最上位の項目ではない。**"""
    _result(tasks_dir, "T-2026-08-01-x", "status: pass\ngates:\n  - {id: G1, verdict: stop}\n")
    assert preflight_task.completed_verdicts("T-2026-08-01-x") == ["stop"]
    assert preflight_task.completed_verdicts("T-2026-08-01-missing") == []


# --- 二型が様式の列挙に入った（完了判定 d・e） -----------------------------

@pytest.mark.parametrize("name", ["asymmetric_comparison", "rule_read_narrowly"])
def test_new_defect_types_are_in_the_result_schema(name):
    import json

    schema = json.loads(
        (REPO_ROOT / "tasks" / "_schema" / "result.schema.json").read_text(encoding="utf-8")
    )
    enum = schema["properties"]["issuer_defects"]["items"]["properties"]["type"]["enum"]
    assert name in enum
    assert "zz_unknown" not in enum


def test_defect_types_in_the_projection_match_the_schema():
    """**片方だけ増やすと集計から落ちる。** 様式と投影の列挙を一致で縛る。"""
    import json

    import build_taskindex

    schema = json.loads(
        (REPO_ROOT / "tasks" / "_schema" / "result.schema.json").read_text(encoding="utf-8")
    )
    enum = schema["properties"]["issuer_defects"]["items"]["properties"]["type"]["enum"]
    assert sorted(build_taskindex.DEFECT_TYPES) == sorted(enum)


def test_issuer_defects_no_longer_says_the_enum_lacks_them():
    """完了判定 e。注記が消えている。変更前は 1 件あった。"""
    text = DEFECTS.read_text(encoding="utf-8")
    assert "enum には未追加" not in text
