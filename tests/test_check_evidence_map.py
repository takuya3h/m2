"""証拠地図の様式の検査の試験。**対照は両方向に置く。**

違反の無い地図で零件、四種の違反を一種ずつ入れた写しでそれぞれ一件。雛形と旧様式の地図は
対象外。雛形（docs/evidence/_template.md）の「検査が見る項目」と検査器の項目が食い違わない
ことをここで縛る。
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_evidence_map as c  # noqa: E402

TEMPLATE = REPO_ROOT / "docs" / "evidence" / "_template.md"
REPORT_BODY = b"report body without trailing newline"
REPORT_SHA = hashlib.sha256(REPORT_BODY).hexdigest()

SECTIONS = "\n\n".join(f"## {i}. {word}\n\n本文" for i, word in enumerate(c.REQUIRED_SECTIONS["探索の地図"], 1))
CLEAN = f"""# 証拠地図 X — 試験

**版:** v1
**種類:** 探索の地図
**状態:** 試験
**元の報告:**
- 報告（r.md、{len(REPORT_BODY)} バイト、sha256 {REPORT_SHA}）
**検索日:** 2026-10-19

---

{SECTIONS}
"""


@pytest.fixture()
def reports(tmp_path):
    d = tmp_path / "reports"
    d.mkdir()
    (d / "r.md").write_bytes(REPORT_BODY)
    return c.report_digests(d)


@pytest.fixture()
def words():
    found = c.forbidden_words()
    assert found, "規約から禁止語を読めない"
    return found


def _kinds(text, words, reports):
    return [f.kind for f in c.check_text(text, words, reports)]


def test_clean_map_has_no_violation(words, reports):
    assert _kinds(CLEAN, words, reports) == []


def test_citation_residue_is_detected_once(words, reports):
    text = CLEAN.replace("本文", "本文 citeturn1view1", 1)
    assert _kinds(text, words, reports) == ["citation_residue"]


def test_private_use_and_non_bmp_are_detected(words, reports):
    text = CLEAN.replace("## 1. 系統表\n\n本文", "## 1. 系統表\n\n本文").replace(
        "## 2. 行の一覧\n\n本文", "## 2. 行の一覧\n\n本文\U0001F600"
    )
    assert sorted(_kinds(text, words, reports)) == ["non_bmp", "private_use"]


def test_missing_section_is_detected_once(words, reports):
    text = CLEAN.replace("## 6. 効果\n", "## 6. 数値\n")
    assert _kinds(text, words, reports) == ["missing_section"]


def test_forbidden_word_is_detected_once(words, reports):
    text = CLEAN.replace("本文", f"本文 {words[0]}", 1)
    assert _kinds(text, words, reports) == ["forbidden_word"]


def test_one_character_change_in_sha256_is_detected(words, reports):
    flipped = REPORT_SHA[:-1] + ("0" if REPORT_SHA[-1] != "0" else "1")
    assert _kinds(CLEAN.replace(REPORT_SHA, flipped), words, reports) == ["report_sha256"]
    # 十六進でない文字へ変えても見逃さない（64 桁の十六進を探すだけだと黙って消える）
    assert _kinds(CLEAN.replace(REPORT_SHA, REPORT_SHA[:-1] + "g"), words, reports) == ["report_sha256"]


def test_missing_header_field_and_unknown_kind(words, reports):
    assert _kinds(CLEAN.replace("**検索日:** 2026-10-19\n", ""), words, reports) == ["header_field"]
    assert "header_kind" in _kinds(CLEAN.replace("探索の地図", "地図"), words, reports)


def test_novelty_kind_requires_its_own_sections(words, reports):
    text = CLEAN.replace("探索の地図", "新規性の照合")
    missing = [f.detail for f in c.check_text(text, words, reports) if f.kind == "missing_section"]
    assert len(missing) == 2 and any("照合表" in m for m in missing)


def test_headings_inside_fences_do_not_count(words, reports):
    text = CLEAN.replace("## 1. 系統表\n", "```\n## 1. 系統表\n```\n")
    assert _kinds(text, words, reports) == ["missing_section"]


def test_files_without_kind_field_are_not_targets(tmp_path):
    old = tmp_path / "old.md"
    old.write_text("# 旧地図\n\n**照合の手段:** Crossref\n\n## 1. 表\n", encoding="utf-8")
    template_like = tmp_path / "template.md"
    template_like.write_text("# 雛形\n\n説明\n\n## 項目\n\n    **種類:** 探索の地図\n", encoding="utf-8")
    report = c.run([old, template_like], tmp_path)
    assert report["checked"] == [] and len(report["skipped"]) == 2


def test_unreadable_forbidden_words_is_an_error(monkeypatch, tmp_path):
    monkeypatch.setattr(c, "forbidden_words", lambda: [])
    path = tmp_path / "m.md"
    path.write_text(CLEAN, encoding="utf-8")
    assert c.run([path], tmp_path)["status"] == "error"


def test_main_exit_codes(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "r.md").write_bytes(REPORT_BODY)
    good = tmp_path / "good.md"
    good.write_text(CLEAN, encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text(CLEAN.replace("本文", "本文 citeturn2search3", 1), encoding="utf-8")
    assert c.main([str(good), "--reports-dir", str(reports_dir)]) == 0
    assert c.main([str(bad), "--reports-dir", str(reports_dir)]) == 1


# --- 雛形と検査器の項目が食い違わない -------------------------------------------------

def _template_section() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    start = text.index("## 検査が見る項目")
    return text[start : text.index("## 雛形", start)]


def test_template_header_fields_match_checker():
    section = _template_section()
    block = section[section.index("### 見出しの前の欄") : section.index("### 種類ごとの必須の節")]
    first_line = next(line for line in block.split("\n") if "**版:**" in line)
    assert tuple(re.findall(r"`\*\*([^*:]+):\*\*`", first_line)) == c.HEADER_FIELDS
    kinds = tuple(re.findall(r"^- `([^`]+)`", block, re.M))
    assert kinds == tuple(c.REQUIRED_SECTIONS)


def test_template_required_sections_match_checker():
    section = _template_section()
    rows = dict(re.findall(r"^\| (探索の地図|新規性の照合) \| ([^|]+) \|$", section, re.M))
    assert {kind: tuple(w.strip() for w in words.split("／")) for kind, words in rows.items()} == c.REQUIRED_SECTIONS


def test_template_body_checks_match_checker():
    section = _template_section()
    bullets = re.findall(r"^- (.+)$", section[section.index("### 本文の全体") :], re.M)
    assert len(bullets) == 4
    covered = {
        "citation_residue": "citation" in bullets[0],
        "private_use": "私用領域" in bullets[0],
        "non_bmp": "BMP 外" in bullets[1],
        "forbidden_word": "禁止語" in bullets[2] and "proposal_gate" in bullets[2],
        "report_sha256": "sha256" in bullets[3] and "docs/evidence/reports/" in bullets[3],
    }
    assert tuple(covered) == c.BODY_CHECKS and all(covered.values()), covered


def test_template_itself_is_not_a_target():
    assert not c.is_target(TEMPLATE.read_text(encoding="utf-8"))
