"""契約の静的検査の試験。**件数は実測して記録する。**

3 つを固定する。

1. 教師データに対する検出率（`TEACHER`）。**分母を後から動かさないための固定である。**
2. 規則ごとの陽性対照。**規則の数だけ要る。** 1 つでも検出されない規則は無効である。
3. 誤検出。対応の無い該当を 1 件ずつ判定した結果を固定する。

`host_mismatch` は実行ホストに依存するため、期待値を hostname から計算する。
**固定値を書くと別のホストで落ちる。** これは検査の性質であり不具合ではない。
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_spec  # noqa: E402
from check_spec import (  # noqa: E402
    RULE_CLASSES,
    RULES,
    Contract,
    check,
    discover_contracts,
    load_contract,
)

# 教師データ（`defects.md` の syntactic と structural の全件）と、捕まえるべき規則。
# 規則が無いもの（None）は実装していない型である。**空欄にせず理由を残す。**
TEACHER: tuple[tuple[str, str | None, int | None, str], ...] = (
    ("T-2026-08-11-codex-parity#1", "separated_source", None,
     "誤りは監査対象の手順書側にあり SPEC 内の行を特定できない（教師データの箇所が UNKNOWN）"),
    ("T-2026-08-11-codex-parity#2", None, None,
     "Files 欄と検査の走査対象の対応が要る。検査の走査範囲を解決する道具が無い"),
    ("T-2026-08-11-codex-parity#4", "forbidden_vs_output", 348, ""),
    ("T-2026-08-11-hts-comparability-audit#2", "reverify_contradiction", 257, ""),
    ("T-2026-08-11-hts-comparability-audit#3", "unquoted_glob", 136, ""),
    ("T-2026-08-13-implementation-history-index#1", "forbidden_vs_output", 266, ""),
    ("T-2026-08-13-implementation-history-index#2", None, None,
     "Files 欄と検査の走査対象の対応が要る。codex-parity#2 と同じ理由"),
    ("T-2026-08-14-bundle-attachment-transport#3", "host_mismatch", 6, ""),
    ("T-2026-08-14-bundle-attachment-transport#5", "integration_prohibited_without_pause", 55, ""),
    ("T-2026-08-15-template-leak-and-autosync-conflict#1", "forbidden_vs_output", 206, ""),
    ("T-2026-08-15-template-leak-and-autosync-conflict#2",
     "integration_prohibited_without_pause", 47, ""),
    ("T-2026-08-15-template-leak-and-autosync-conflict#3", "forbidden_vs_output", 206, ""),
    ("T-2026-08-16-docs-reconciliation#2", None, None,
     "判定が空振りかを問う型。規則にせず Phase C の様式（陽性対照の欄）で構造的に防ぐ"),
    ("T-2026-08-16-docs-reconciliation#3", "host_mismatch", 6, ""),
    ("T-2026-08-17-report-projection-and-friction#1",
     "gate_requires_report_before_end", 41, ""),
    ("T-2026-08-17-report-projection-and-friction#2", "truncation_in_measurement", 279, ""),
)

# 教師データ（対）を持つ契約。対を持たない契約への該当は対応の有無を判定できない。
PAIRED = (
    "T-2026-08-11-artifact-merge-and-pause",
    "T-2026-08-11-codex-parity",
    "T-2026-08-11-hts-comparability-audit",
    "T-2026-08-11-make-task-start",
    "T-2026-08-11-s0-reevaluation-feasibility",
    "T-2026-08-11-split-and-recipe-audit",
    "T-2026-08-13-implementation-history-index",
    "T-2026-08-14-bundle-attachment-transport",
    "T-2026-08-15-template-leak-and-autosync-conflict",
    "T-2026-08-16-docs-reconciliation",
    "T-2026-08-17-report-projection-and-friction",
    "T-2026-08-18-report-back-to-ledger",
)

# 対応の無い該当を 1 件ずつ判定した結果（実測 2026-08-11 lecun）。
# 記録漏れ = 実在する誤りだが報告に書かれていない。**規則の誤りではない。**
UNRECORDED = (
    ("separated_source", "T-2026-08-11-make-task-start", 20),
    ("separated_source", "T-2026-08-11-make-task-start", 26),
    ("unquoted_glob", "T-2026-08-11-split-and-recipe-audit", 320),
    ("unquoted_glob", "T-2026-08-11-split-and-recipe-audit", 321),
    ("integration_prohibited_without_pause", "T-2026-08-13-implementation-history-index", 46),
    ("forbidden_vs_output", "T-2026-08-14-bundle-attachment-transport", 256),
    ("forbidden_vs_output", "T-2026-08-16-docs-reconciliation", 273),
    ("forbidden_vs_output", "T-2026-08-17-report-projection-and-friction", 368),
    ("forbidden_vs_output", "T-2026-08-18-report-back-to-ledger", 260),
)


def _host_expectation(task: str) -> bool:
    """その契約で host_mismatch が該当するはずかを、宣言と実行環境から決める。"""
    text = (REPO_ROOT / "tasks" / task / "SPEC.md").read_text(encoding="utf-8")
    match = check_spec._HOST_DECL.search(text)
    return bool(match) and match.group(1).strip() != socket.gethostname()


@pytest.fixture(scope="module")
def all_findings() -> list[dict]:
    payload = check([load_contract(t) for t in discover_contracts()])
    assert payload["errors"] == [], payload["errors"]
    return payload["findings"]


def _contract(tmp_path: Path, md: str, spec: str = "") -> Contract:
    md_path = tmp_path / "SPEC.md"
    md_path.write_text(md, encoding="utf-8")
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(spec, encoding="utf-8")
    import yaml

    return Contract(
        task="T-9999-99-99-positive-control",
        md_path=md_path,
        md_text=md,
        spec_path=spec_path,
        spec=yaml.safe_load(spec) or {},
    )


def _rules_hit(contract: Contract) -> set[str]:
    return {f["rule"] for f in check([contract])["findings"]}


# --------------------------------------------------------- 規則の一覧の健全性

def test_every_rule_is_classified():
    """規則の数と分類の数が一致する。**分類の無い規則を足せないようにする。**"""
    assert len(RULES) == len(RULE_CLASSES) == 8
    names = {r.__name__.removeprefix("rule_") for r in RULES}
    assert names == set(RULE_CLASSES)


def test_every_rule_is_backed_by_teacher_data():
    """全ての規則が教師データの少なくとも 1 件を裏付けに持つ。

    **裏付けの無い規則を足すと検出率の分母が動く。** ここで止める。
    """
    backed = {rule for _, rule, _, _ in TEACHER if rule}
    assert backed == set(RULE_CLASSES), f"裏付けの無い規則: {set(RULE_CLASSES) - backed}"


# ------------------------------------------------------------- 陽性対照（8 件）

def test_positive_control_truncation_in_measurement(tmp_path):
    assert "truncation_in_measurement" in _rules_hit(
        _contract(tmp_path, '# x\n\n    grep -rn "y" . | head\n')
    )


def test_positive_control_unquoted_glob(tmp_path):
    assert "unquoted_glob" in _rules_hit(
        _contract(tmp_path, '# x\n\n    grep -rn "y" --include=*.md .\n')
    )


def test_positive_control_separated_source(tmp_path):
    assert "separated_source" in _rules_hit(
        _contract(tmp_path, "# x\n\n    source .venv/bin/activate\n    make task-preflight TASK=y\n")
    )


def test_positive_control_forbidden_vs_output(tmp_path):
    md = (
        "# x\n\n| # | 禁止 |\n|---|---|\n| 1 | `context/auto/**` を編集する |\n\n"
        "| # | 判定 | 期待 |\n|---|---|---|\n| 1 | 禁止領域が無変更 | 出力なし |\n"
    )
    assert "forbidden_vs_output" in _rules_hit(_contract(tmp_path, md))


def test_positive_control_host_mismatch(tmp_path):
    md = "# x\n\n**実行ホスト:** `no-such-host-exists`\n"
    assert "host_mismatch" in _rules_hit(_contract(tmp_path, md))


def test_positive_control_integration_prohibited_without_pause(tmp_path):
    md = "# x\n\n| # | 禁止 |\n|---|---|\n| 1 | 統合する。自動統合を有効化する |\n"
    assert "integration_prohibited_without_pause" in _rules_hit(_contract(tmp_path, md))


def test_positive_control_gate_requires_report_before_end(tmp_path):
    spec = (
        "plan:\n"
        "  phases:\n"
        "    - {id: A, name: a}\n"
        "    - {id: B, name: b}\n"
        "  gates:\n"
        "    - id: G1\n"
        "      after: A\n"
        '      check: "本 task 自身の完了報告を書き、投影を生成した"\n'
    )
    assert "gate_requires_report_before_end" in _rules_hit(_contract(tmp_path, "# x\n", spec))


def test_positive_control_reverify_contradiction(tmp_path):
    md = (
        "# x\n\n### 先に確定していること（再検証しない）\n\n"
        "- 生成経路は **Skewer を構造的に除外**している。\n\n"
        "**本 task はこれらを再検証しない。**\n\n"
        "## Phase B\n\n- Skewer の内訳を数える。\n"
    )
    assert "reverify_contradiction" in _rules_hit(_contract(tmp_path, md))


# ------------------------------------------------------------------- 陰性対照

@pytest.mark.parametrize(
    "md,spec",
    [
        ('# x\n\n    grep -rn "y" . | head -30 | wc -l\n', ""),
        ('# x\n\n    grep -rn "y" "--include=*.md" .\n', ""),
        ("# x\n\n    source .venv/bin/activate && make task-preflight TASK=y\n", ""),
        # 生成物を除外する道具を指していれば誤りではない。
        (
            "# x\n\n| # | 禁止 |\n|---|---|\n| 1 | `context/auto/**` を編集する |\n\n"
            "| # | 判定 | 期待 |\n|---|---|---|\n| 1 | 禁止領域が無変更 | forbidden-check が exit 0 |\n",
            "",
        ),
        # 抑止の手順があれば誤りではない。
        (
            "# x\n\n    touch .sync-pause\n\n| # | 禁止 |\n|---|---|\n"
            "| 1 | 統合する。自動統合を有効化する |\n",
            "",
        ),
        # 読み込みが続くだけなら誤りではない。
        ("# x\n\n    source .venv/bin/activate\n    source scripts/load_env.sh\n", ""),
    ],
)
def test_negative_control(tmp_path, md, spec):
    """違反しない記述で該当が出ない。**陽性対照だけでは空振りを排除できない。**"""
    assert _rules_hit(_contract(tmp_path, md, spec)) == set()


def test_negative_control_gate_at_last_phase(tmp_path):
    """最終フェーズのゲートが報告を求めるのは正しい。該当してはならない。"""
    spec = (
        "plan:\n"
        "  phases:\n"
        "    - {id: A, name: a}\n"
        "    - {id: B, name: b}\n"
        "  gates:\n"
        "    - id: G1\n"
        "      after: B\n"
        '      check: "完了報告を書いた"\n'
    )
    assert _rules_hit(_contract(tmp_path, "# x\n", spec)) == set()


def test_clean_contract_has_no_hit(tmp_path):
    """特定の実在契約に依存しない最小契約では該当しない。"""
    payload = check([_contract(tmp_path, "# clean contract\n")])
    assert payload["hits"] == 0, payload["findings"]
    assert payload["status"] == "pass"


def test_host_mismatch_ignores_case_but_detects_other_host(tmp_path, monkeypatch):
    """大小文字だけの差を通し、別ホストは引き続き捕まえる。"""
    monkeypatch.setattr(socket, "gethostname", lambda: "efros")
    case_only = _contract(tmp_path, "# x\n\n**実行ホスト:** `Efros`\n")
    assert "host_mismatch" not in _rules_hit(case_only)
    other = _contract(tmp_path, "# x\n\n**実行ホスト:** `different-host`\n")
    assert "host_mismatch" in _rules_hit(other)


# ------------------------------------------------------------------- 検出率

def test_teacher_detection_rate(all_findings):
    """教師データ 16 件のうち 11 件を検出する（実測 2026-08-11 lecun）。

    `host_mismatch` の 2 件は実行ホストに依存する。宣言と一致するホストでは
    該当しないのが正しい。**期待値を hostname から計算する。**
    """
    detected, missed = [], []
    for key, rule, line, _ in TEACHER:
        task = key.rsplit("#", 1)[0]
        if rule is None:
            missed.append(key)
            continue
        hits = [f for f in all_findings if f["task"] == task and f["rule"] == rule]
        if rule == "host_mismatch" and not _host_expectation(task):
            missed.append(key)
            continue
        if not hits or (line is not None and line not in [h["line"] for h in hits]):
            missed.append(key)
            continue
        detected.append(key)

    expected_host_detected = sum(
        1 for key, rule, _, _ in TEACHER
        if rule == "host_mismatch" and _host_expectation(key.rsplit("#", 1)[0])
    )
    # 規則を持つ 13 件のうち、ホストに依存しないのは 11 件。そこから検出できない
    # codex-parity#1 を引いて 10 件。これにホストに依存する分を足す。
    expected = 10 + expected_host_detected
    assert len(detected) == expected, f"検出 {detected} / 未検出 {missed}"
    assert len(detected) + len(missed) == 16


def test_unrecorded_hits_are_pinned(all_findings):
    """対応の無い該当を固定する。**規則を足して数字を動かせないようにする。**

    `host_mismatch` の完了済み契約への該当は誤検出である（実行時点でのみ意味を持つ）。
    それ以外は実在する誤りだが報告に書かれていない（記録漏れ）。
    """
    matched_rules = {(k.rsplit("#", 1)[0], r) for k, r, _, _ in TEACHER if r}
    unmatched = [
        f for f in all_findings
        if f["task"] in PAIRED and (f["task"], f["rule"]) not in matched_rules
    ]
    false_positives = [f for f in unmatched if f["rule"] == "host_mismatch"]
    unrecorded = {(f["rule"], f["task"], f["line"]) for f in unmatched if f["rule"] != "host_mismatch"}

    assert unrecorded == set(UNRECORDED), unrecorded ^ set(UNRECORDED)
    # 完了済み契約への host_mismatch は、宣言が実行環境と異なるホストで測ったときだけ出る。
    for f in false_positives:
        assert _host_expectation(f["task"])


def test_rules_and_targets_are_reported(all_findings):
    """検査した規則の数と該当の件数の両方が出る。**片方だけでは空振りが分からない。**"""
    payload = check([load_contract(t) for t in discover_contracts()])
    assert payload["rules_checked"] == 8
    assert payload["targets"] == len(discover_contracts()) >= 35
    assert payload["hits"] == len(payload["findings"]) == len(all_findings)
    assert sum(payload["hits_by_rule"].values()) == payload["hits"]
