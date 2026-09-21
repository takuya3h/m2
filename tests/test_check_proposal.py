"""提案文書の静的検査の試験。**対照は両方向に置く。**

判定が通ったことは、判定が働いていることを意味しない。したがって規則ごとに
「検出するはずの入力」と「検出しないはずの入力」を対で置き、件数を実測で固定する。

規約（`context/conventions.md` の `proposal_gate` 節）が正本であり、検査器は
写しを持たない。**試験は、検査器が規約から読めていることを先に確かめる。**
読めなくなれば禁止語 0 語で全件合格するため、そこが最初に壊れる場所である。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_proposal  # noqa: E402
from check_proposal import (  # noqa: E402
    card_items,
    check,
    check_card,
    check_forbidden,
    forbidden_words,
    main,
    numeric_items,
    section_text,
)

# 規約に載っている語。**検査器の中の写しではなく、規約から読めることを確かめる。**
FORBIDDEN_IN_CONVENTIONS = (
    "最大の新規性", "世界初", "画期的", "有望", "筋が良い", "本命", "未踏", "空白",
    "決定的", "確実に効く", "明らかに", "大幅", "劇的", "必ず改善", "唯一の",
)
CARD_COUNT = 16
NUMERIC_ITEMS = [5, 6, 10]


# --- 規約の読み取り -------------------------------------------------------

def test_section_is_readable():
    assert "## proposal_gate" in section_text()


def test_forbidden_words_come_from_conventions():
    assert tuple(forbidden_words()) == FORBIDDEN_IN_CONVENTIONS


def test_card_items_are_sixteen_and_numbered_one_to_sixteen():
    items = card_items()
    assert len(items) == CARD_COUNT
    assert sorted(items) == list(range(1, CARD_COUNT + 1))


def test_numeric_items_are_read_from_conventions():
    assert sorted(numeric_items()) == NUMERIC_ITEMS


def test_exemption_wording_exists_in_conventions():
    """免除の条件だけは実装側に置いている。**規約に根拠が在ることを確かめる。**"""
    section = section_text()
    assert check_proposal._EXEMPT_CONDITION in section
    for word in check_proposal._EXEMPT_WORDS:
        assert word in section


# --- 禁止語（完了判定 b） -------------------------------------------------

def test_forbidden_absent_gives_zero():
    """陰性対照。禁止語を含まない本文で 0 件。"""
    text = "本案は効果量 0.02 を見込む。根拠は先行研究の表 3 である。\n"
    assert check_forbidden(text, list(FORBIDDEN_IN_CONVENTIONS)) == []


def test_forbidden_one_word_gives_one():
    """陽性対照。禁止語を一語だけ含む本文で 1 件。"""
    text = "本案は画期的な結合である。\n"
    findings = check_forbidden(text, list(FORBIDDEN_IN_CONVENTIONS))
    assert len(findings) == 1
    assert findings[0].kind == "forbidden_word"
    assert "画期的" in findings[0].detail
    assert findings[0].line == 1


def test_forbidden_two_words_gives_two():
    """二語含む本文で 2 件。**1 件で頭打ちにならないことを確かめる。**"""
    text = "本案は画期的で、効果は決定的である。\n"
    findings = check_forbidden(text, list(FORBIDDEN_IN_CONVENTIONS))
    assert len(findings) == 2
    assert {f.detail for f in findings} == {"禁止語「画期的」", "禁止語「決定的」"}


def test_forbidden_reports_line_numbers():
    text = "一行目は無害である。\n二行目に有望と書く。\n"
    findings = check_forbidden(text, list(FORBIDDEN_IN_CONVENTIONS))
    assert [(f.line, f.detail) for f in findings] == [(2, "禁止語「有望」")]


# --- 境界（SPEC Task D-5 / docs/proposal-gate.md B.6） --------------------

def test_mitou_alone_is_detected():
    """免除の条件が無ければ「未踏」は検出する。"""
    text = "この領域は未踏である。\n"
    assert len(check_forbidden(text, list(FORBIDDEN_IN_CONVENTIONS))) == 1


def test_mitou_with_hypothesis_section_passes():
    """「空白である理由の仮説」がある本文は、形の検査では通す。"""
    text = (
        "この領域は未踏である。\n"
        "## 空白である理由の仮説\n"
        "技術的困難のため誰も測っていない、が第一候補。\n"
    )
    assert check_forbidden(text, list(FORBIDDEN_IN_CONVENTIONS)) == []


def test_exemption_does_not_cover_other_words():
    """免除は「未踏」「空白」だけ。**他の禁止語まで通してはならない。**"""
    text = (
        "この領域は未踏で、効果は決定的である。\n"
        "## 空白である理由の仮説\n"
        "価値が無いため、が第二候補。\n"
    )
    findings = check_forbidden(text, list(FORBIDDEN_IN_CONVENTIONS))
    assert [f.detail for f in findings] == ["禁止語「決定的」"]


# --- カードの充足（完了判定 c） -------------------------------------------

def _card(missing: int | None = None, blank_numbers: tuple[int, ...] = ()) -> str:
    """提案カードの本文を組み立てる。`missing` の見出しだけを落とす。"""
    lines = ["# 提案カード\n"]
    for num in range(1, CARD_COUNT + 1):
        if num == missing:
            continue
        lines.append(f"## #{num} 項目\n")
        body = "検討中。" if num in blank_numbers else "見積もりは 0.02 である。"
        lines.append(f"{body}\n")
    return "\n".join(lines)


def test_card_complete_gives_zero():
    """陰性対照。見出し 16 件で不足 0 件。"""
    assert check_card(_card(), card_items(), numeric_items()) == []


def test_card_missing_one_heading_gives_one():
    """陽性対照。見出しを 1 件落として不足 1 件。"""
    findings = check_card(_card(missing=7), card_items(), numeric_items())
    assert len(findings) == 1
    assert findings[0].kind == "missing_heading"
    assert "#7" in findings[0].detail


def test_card_effect_size_without_digit_gives_one():
    """期待効果量（#5）の本文に数字が無ければ不足 1 件。"""
    findings = check_card(_card(blank_numbers=(5,)), card_items(), numeric_items())
    assert len(findings) == 1
    assert findings[0].kind == "missing_number"
    assert "#5" in findings[0].detail


@pytest.mark.parametrize("num", NUMERIC_ITEMS)
def test_each_numeric_item_is_checked(num):
    """#5 #6 #10 の三項目すべてが見られている。**一つだけ効いて通らない。**"""
    findings = check_card(_card(blank_numbers=(num,)), card_items(), numeric_items())
    assert [f.kind for f in findings] == ["missing_number"]
    assert f"#{num}" in findings[0].detail


def test_card_accepts_numbered_heading_without_hash():
    """`5. 期待効果量` の書き方も番号として読む。"""
    text = "\n".join(f"## {n}. 項目\n値は 0.02 である。\n" for n in range(1, CARD_COUNT + 1))
    assert check_card(text, card_items(), numeric_items()) == []


def test_missing_heading_and_missing_number_are_counted_together():
    findings = check_card(_card(missing=3, blank_numbers=(10,)), card_items(), numeric_items())
    assert sorted(f.kind for f in findings) == ["missing_heading", "missing_number"]


# --- 入口と終了コード -----------------------------------------------------

def test_check_reports_counts(tmp_path):
    path = tmp_path / "proposal.md"
    path.write_text(_card(), encoding="utf-8")
    report = check(path)
    assert report["status"] == "pass"
    assert report["hits"] == 0
    assert report["errors"] == []
    assert report["words_checked"] == len(FORBIDDEN_IN_CONVENTIONS)
    assert report["card_items"] == CARD_COUNT
    assert report["numeric_items"] == NUMERIC_ITEMS


def test_only_forbidden_ignores_card(tmp_path):
    """片方だけを回せる。**カードが空でも禁止語の件数は動かない。**"""
    path = tmp_path / "proposal.md"
    path.write_text("本案は有望である。\n", encoding="utf-8")
    assert check(path, only="forbidden")["hits"] == 1
    assert check(path, only="card")["hits"] == CARD_COUNT


def test_exit_code_is_zero_when_clean(tmp_path):
    path = tmp_path / "proposal.md"
    path.write_text(_card(), encoding="utf-8")
    assert main([str(path)]) == 0


def test_exit_code_is_nonzero_when_detected(tmp_path):
    path = tmp_path / "proposal.md"
    path.write_text("本案は世界初である。\n", encoding="utf-8")
    assert main([str(path)]) != 0


def test_missing_file_is_not_silently_passed(tmp_path):
    assert main([str(tmp_path / "no_such.md")]) == 2


def test_empty_word_list_is_an_error_not_a_pass(monkeypatch, tmp_path):
    """**規約を読めなくなったとき、0 件で合格にしない。**"""
    monkeypatch.setattr(check_proposal, "section_text", lambda: "")
    path = tmp_path / "proposal.md"
    path.write_text("本案は世界初である。\n", encoding="utf-8")
    report = check(path)
    assert report["status"] == "fail"
    assert report["errors"]
