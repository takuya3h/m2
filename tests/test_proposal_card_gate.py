"""提案カードの置き場と参照の関門の試験（T-2026-09-23-ops-and-proposal-card-gate）。

**対照は両方向に置く。** 判定が通ったことは、判定が働いていることを意味しない。
規則ごとに「落ちるはずの入力」と「通るはずの入力」を対で置く。

正本は `context/conventions.md` の `proposal_gate` 節「置き場と参照」。
検査器（`tools/check_proposal.py`）も雛形も、項目の写しを持たない。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_proposal  # noqa: E402
import preflight_task  # noqa: E402

CONVENTIONS = REPO_ROOT / "context" / "conventions.md"
TEMPLATE = REPO_ROOT / "docs" / "proposals" / "_template.md"
SPEC_SCHEMA = REPO_ROOT / "tasks" / "_schema" / "spec.schema.json"

# 雛形のままで落ちるはずの項目。規約が数値を求める項目と一致する。
TEMPLATE_EMPTY_NUMERIC = (5, 6, 10)


@pytest.fixture
def tasks_dir(tmp_path, monkeypatch):
    """P14 が完了済みを引く場所を一時ディレクトリへ移す。"""
    monkeypatch.setattr(preflight_task, "TASKS_DIR", tmp_path)
    return tmp_path


def _spec(card: str | None = None, kind: str = "exp") -> dict:
    intent: dict = {"question": "q", "decision_at_stake": "d"}
    if card is not None:
        intent["proposal_card"] = card
    return {"meta": {"kind": kind}, "intent": intent, "plan": {"env": {}}}


def _filled_card(tmp_path: Path) -> Path:
    """検査を通るカード。雛形の空欄のうち数値を求める三項目だけを埋める。"""
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace(
        "## 5. 期待効果量（点）と外挿の出所\n",
        "## 5. 期待効果量（点）と外挿の出所\n\n0.8 ポイント（先行研究の 1.5 ポイントから外挿）。\n",
    )
    text = text.replace(
        "## 6. 成功確率（零から一のあいだ）\n",
        "## 6. 成功確率（零から一のあいだ）\n\n0.35\n",
    )
    text = text.replace(
        "## 10. 費用（run 本数 × 時間）\n",
        "## 10. 費用（run 本数 × 時間）\n\n4 run × 6 時間。\n",
    )
    path = tmp_path / "filled.md"
    path.write_text(text, encoding="utf-8")
    return path


# --- 規約（完了判定 b） ---------------------------------------------------

def test_conventions_states_the_placement_rules():
    """置き場・候補数の下限・web 検索・参照・例外の五つが規約から読める。"""
    section = CONVENTIONS.read_text(encoding="utf-8").split('<a id="proposal_gate"></a>', 1)[1]
    section = section.split('<a id="folds"></a>', 1)[0]
    assert "docs/proposals/YYYY-MM-DD-slug.md" in section
    assert "三案以上" in section
    assert "web 検索を必須" in section
    assert "intent.proposal_card" in section
    for task_id in preflight_task.PRE_GATE_EXEMPT_TASKS:
        assert task_id in section


def test_card_items_are_still_read_from_conventions():
    """追記で規約の読み取りが壊れていない。**検査器は写しを持たない。**"""
    assert len(check_proposal.card_items()) == check_proposal.EXPECTED_CARD_ITEMS
    assert check_proposal.forbidden_words()
    assert set(check_proposal.numeric_items()) == set(TEMPLATE_EMPTY_NUMERIC)


# --- 雛形（完了判定 a） ---------------------------------------------------

def test_template_has_all_card_headings():
    """雛形は規約の全項目の見出しを持つ。**表だけでは検査に見えない。**"""
    bodies = check_proposal._bodies_by_number(TEMPLATE.read_text(encoding="utf-8"))
    assert set(check_proposal.card_items()) <= set(bodies)


def test_template_itself_fails_because_items_are_empty():
    """雛形そのものは落ちる。落ちる理由は数値を求める項目が空であること。"""
    report = check_proposal.check(TEMPLATE)
    assert report["status"] == "fail"
    assert report["hits_by_kind"]["missing_heading"] == 0
    assert report["hits_by_kind"]["forbidden_word"] == 0
    assert report["hits_by_kind"]["missing_number"] == len(TEMPLATE_EMPTY_NUMERIC)


def test_filled_card_passes(tmp_path):
    """陽性対照の対。**埋めれば通る。** 通らないなら雛形の形が誤っている。"""
    assert check_proposal.check(_filled_card(tmp_path))["status"] == "pass"


# --- schema（完了判定 c） -------------------------------------------------

def test_schema_accepts_proposal_card_as_optional_string():
    from jsonschema import Draft202012Validator

    schema = json.loads(SPEC_SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["intent"]["properties"]["proposal_card"]["type"] == "string"
    assert "proposal_card" not in schema["properties"]["intent"]["required"]

    sample = yaml.safe_load(
        (REPO_ROOT / "tasks" / "T-2026-09-23-ops-and-proposal-card-gate" / "spec.yaml")
        .read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    sample["intent"]["proposal_card"] = "docs/proposals/2026-09-23-x.md"
    assert list(validator.iter_errors(sample)) == []
    sample["intent"]["proposal_card"] = 3
    assert list(validator.iter_errors(sample)), "文字列以外が通ってしまう"


def test_all_existing_specs_still_validate():
    """既存の契約が遡って落ちない。**任意項目の追加で過去を落とさない。**"""
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(json.loads(SPEC_SCHEMA.read_text(encoding="utf-8")))
    failed = [
        path.parent.name
        for path in sorted(REPO_ROOT.glob("tasks/T-*/spec.yaml"))
        if list(validator.iter_errors(yaml.safe_load(path.read_text(encoding="utf-8"))))
    ]
    assert failed == []


# --- P14 の適用範囲（完了判定 d） -----------------------------------------

@pytest.mark.parametrize("kind", ["impl", "analysis"])
def test_p14_skips_for_non_exp(kind):
    assert preflight_task.decide_applicability(_spec(kind=kind))["P14"] is False


def test_p14_applies_to_exp():
    assert preflight_task.decide_applicability(_spec())["P14"] is True


def test_p14_skips_for_completed_contract(tasks_dir):
    """完了済みは対象外。判定は `result.yaml` の `gates[].verdict` だけに委ねる。"""
    task_id = "T-2026-09-23-completed"
    (tasks_dir / task_id).mkdir()
    (tasks_dir / task_id / "result.yaml").write_text(
        "gates:\n  - {id: G1, verdict: pass}\n", encoding="utf-8"
    )
    check = preflight_task.check_proposal_card(task_id, _spec())
    assert check.status == "SKIP"
    assert "完了済み" in check.detail


@pytest.mark.parametrize("task_id", sorted(preflight_task.PRE_GATE_EXEMPT_TASKS))
def test_p14_skips_for_pre_gate_contracts(tasks_dir, task_id):
    check = preflight_task.check_proposal_card(task_id, _spec())
    assert check.status == "SKIP"
    assert preflight_task.PRE_GATE_EXEMPT_REASON in check.detail


@pytest.mark.parametrize(
    "task_id",
    [
        "T-2026-09-19-stage1-detector-towers-r3",  # 一文字違い
        "T-2026-09-19-stage1-detector-towers-r2-followup",  # 例外を接頭辞に持つ
        "stage1-detector-towers-r2",  # 例外の部分列
    ],
)
def test_p14_exemption_is_exact_match_only(tasks_dir, task_id):
    """陽性対照。**部分一致にすると無関係な契約まで免除する。**"""
    check = preflight_task.check_proposal_card(task_id, _spec())
    assert check.status == "FAIL", check.detail


# --- P14 の判定（完了判定 d） ---------------------------------------------

def test_p14_fails_without_proposal_card(tasks_dir):
    check = preflight_task.check_proposal_card("T-2026-09-23-no-card", _spec(card=None))
    assert check.status == "FAIL"
    assert "intent.proposal_card" in check.detail


def test_p14_fails_when_card_is_missing(tasks_dir):
    check = preflight_task.check_proposal_card(
        "T-2026-09-23-absent", _spec(card="docs/proposals/2026-01-01-no-such-card.md")
    )
    assert check.status == "FAIL"
    assert "提案カードが無い" in check.detail


def test_p14_fails_when_card_does_not_pass_check_proposal(tasks_dir):
    """雛形そのものを指した場合。**置いただけでは通らない。**"""
    check = preflight_task.check_proposal_card(
        "T-2026-09-23-template", _spec(card="docs/proposals/_template.md")
    )
    assert check.status == "FAIL"
    assert "check_proposal.py を通らない" in check.detail


def test_p14_passes_with_a_checked_card(tasks_dir, tmp_path):
    check = preflight_task.check_proposal_card(
        "T-2026-09-23-ok", _spec(card=str(_filled_card(tmp_path)))
    )
    assert check.status == "PASS", check.detail


# --- 既存の検査を動かしていないこと ---------------------------------------

def test_p1_to_p13_are_unchanged():
    """P14 は末尾に足すだけ。**番号と順序と名前を動かさない。**"""
    assert preflight_task.CHECK_NAMES["P14"] == "proposal_card_checked"
    assert [c for c in preflight_task.CHECK_NAMES] == [f"P{i}" for i in range(1, 15)]
    assert preflight_task.EXP_ONLY == {"P4", "P5", "P13", "P14"}
