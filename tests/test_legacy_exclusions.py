"""旧様式の報告の除外（validate_task）と、完了済み契約の宣言漏れ検査の除外（check_spec）。

**除外される入力と除外されない入力の両方向**を置く。除外される例だけを試すと、
「常に除外する」壊れ方と区別できない。一時の木は tmp_path に作り、tasks/ の中に置かない。
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
import validate_task  # noqa: E402

LEGACY = "T-2026-08-22-philip-hub-foundation"
LEGACY_RESULT = REPO_ROOT / "tasks" / LEGACY / "result.yaml"
# 契約の本文として形が正しい実物（本契約）。task_id だけ差し替えて一時の木へ置く。
THIS_TASK = "T-2026-10-08-legacy-exclusions-and-type-sync"
LAST_LINE = re.compile(r"^\d+ task\(s\), \d+ failed$")


def _make_tree(tmp_path: Path, dir_name: str, result_text: str | None) -> Path:
    tasks = tmp_path / "tasks"
    d = tasks / dir_name
    d.mkdir(parents=True)
    src = REPO_ROOT / "tasks" / THIS_TASK
    spec = (src / "spec.yaml").read_text(encoding="utf-8").replace(THIS_TASK, dir_name)
    (d / "spec.yaml").write_text(spec, encoding="utf-8")
    shutil.copy(src / "SPEC.md", d / "SPEC.md")
    if result_text is not None:
        (d / "result.yaml").write_text(result_text, encoding="utf-8")
    return tasks


def _run(monkeypatch, capsys, tasks: Path) -> tuple[int, str]:
    monkeypatch.setattr(validate_task, "TASKS_DIR", tasks)
    monkeypatch.setattr(sys, "argv", ["validate_task.py", "--level", "l1"])
    code = validate_task.main()
    return code, capsys.readouterr().out


def test_the_list_holds_exactly_the_one_legacy_report():
    assert list(validate_task.load_legacy_result_exclusions()) == [LEGACY]
    assert validate_task.load_legacy_result_exclusions()[LEGACY]  # 理由が空でない


def test_the_legacy_report_itself_is_excluded_and_named(tmp_path, monkeypatch, capsys):
    tasks = _make_tree(tmp_path, LEGACY, LEGACY_RESULT.read_text(encoding="utf-8"))
    code, out = _run(monkeypatch, capsys, tasks)
    assert f"除外（旧様式） {LEGACY}" in out
    assert "FAIL" not in out and code == 0
    assert LAST_LINE.match(out.strip().splitlines()[-1])


def test_the_legacy_report_is_not_excluded_from_the_spec_check(tmp_path, monkeypatch, capsys):
    """外すのは報告の様式の検査だけ。spec の誤りは従来どおり落ちる。"""
    tasks = _make_tree(tmp_path, LEGACY, LEGACY_RESULT.read_text(encoding="utf-8"))
    spec_path = tasks / LEGACY / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    spec["meta"]["kind"] = "not-a-kind"
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    code, out = _run(monkeypatch, capsys, tasks)
    assert "除外（旧様式）" in out and code == 1 and f"FAIL {LEGACY}" in out


@pytest.mark.parametrize(
    "name",
    [
        LEGACY[:-1] + "m",  # 一文字違い（末尾は n なので別の文字にする）
        LEGACY + "\n",  # 末尾の改行
        LEGACY + " ",  # 末尾の半角スペース
        LEGACY.lower(),  # 大文字小文字
        LEGACY[: len(LEGACY) // 2],  # 接頭辞のみ
        LEGACY + "-r2",  # 接尾辞つき
    ],
    ids=["one-char", "newline", "space", "case", "prefix", "suffix"],
)
def test_near_misses_are_not_excluded(name, tmp_path, monkeypatch, capsys):
    """同じ内容の旧様式の報告を別名で置く。照合が名前であり、内容でないことも示す。"""
    tasks = _make_tree(tmp_path, name, LEGACY_RESULT.read_text(encoding="utf-8"))
    code, out = _run(monkeypatch, capsys, tasks)
    assert "除外（旧様式）" not in out
    assert code == 1 and "L1-6" in out
    assert LAST_LINE.match(out.strip().splitlines()[-1])


def test_an_unlisted_nonconforming_report_still_fails(tmp_path, monkeypatch, capsys):
    tasks = _make_tree(tmp_path, "T-2026-01-01-unlisted", "result_version: 3\ntask_id: T-2026-01-01-unlisted\n")
    code, out = _run(monkeypatch, capsys, tasks)
    assert "除外（旧様式）" not in out and code == 1 and "FAIL T-2026-01-01-unlisted" in out


def test_a_conforming_report_for_an_unlisted_task_is_untouched(tmp_path, monkeypatch, capsys):
    """除外の有無が結果を変えない入力: 報告が無い契約は従来どおり OK。"""
    tasks = _make_tree(tmp_path, "T-2026-01-02-no-report", None)
    code, out = _run(monkeypatch, capsys, tasks)
    assert code == 0 and "OK   T-2026-01-02-no-report" in out and "除外" not in out


def test_the_schema_directory_scanners_do_not_mistake_the_list_for_a_schema():
    """tasks/_schema/ の走査は *.schema.json だけを schema とみなす。新しい yaml は schema ではない。"""
    names = sorted(p.name for p in (REPO_ROOT / "tasks" / "_schema").iterdir())
    assert "result_legacy_exclusions.yaml" in names
    assert [n for n in names if n.endswith(".schema.json")] == ["result.schema.json", "spec.schema.json"]


# --- 完了済みの契約を宣言漏れ検査（allow_write_incomplete）から外す ---------

import check_spec  # noqa: E402
import preflight_task  # noqa: E402

DONE = {"gates": [{"id": "G1", "verdict": "pass"}]}


def _contract_tree(tmp_path, monkeypatch, task, kind, result):
    """宣言を欠く契約（destination を覆う allow_write が無い）を一時の木に置く。

    result は dict（yaml にして書く）、文字列（そのまま書く）、None（書かない）。
    """
    d = tmp_path / "tasks" / task
    d.mkdir(parents=True)
    spec = {
        "meta": {"task_id": task, "kind": kind},
        "outputs": {"destination": f"tasks/{task}/"},
        "contract": {"allow_write": ["somewhere/else/"]},
    }
    (d / "spec.yaml").write_text(yaml.safe_dump(spec), encoding="utf-8")
    (d / "SPEC.md").write_text("# x\n", encoding="utf-8")
    if isinstance(result, dict):
        (d / "result.yaml").write_text(yaml.safe_dump(result), encoding="utf-8")
    elif isinstance(result, str):
        (d / "result.yaml").write_text(result, encoding="utf-8")
    monkeypatch.setattr(check_spec, "TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(preflight_task, "TASKS_DIR", tmp_path / "tasks")
    return check_spec.load_contract(task)


def _detected(contract) -> bool:
    return bool(check_spec.rule_allow_write_incomplete(contract))


@pytest.mark.parametrize(
    "result",
    [
        None,  # result.yaml が無い
        {"result_version": 3},  # gates が無い
        {"gates": [{"id": "G1", "verdict": ""}]},  # verdict が空
        {"gates": [{"id": "G1"}]},  # verdict キーが無い
        "gates: [unclosed\n",  # YAML が壊れている
    ],
    ids=["no-file", "no-gates", "empty-verdict", "no-verdict-key", "broken-yaml"],
)
@pytest.mark.parametrize("kind", ["exp", "impl"])
def test_incomplete_contracts_are_still_detected(tmp_path, monkeypatch, kind, result):
    assert _detected(_contract_tree(tmp_path, monkeypatch, "T-2026-01-01-x", kind, result))


@pytest.mark.parametrize("verdict", ["pass", "ask", "stop", "skip"])
@pytest.mark.parametrize("kind", ["exp", "impl"])
def test_completed_contracts_are_not_detected(tmp_path, monkeypatch, kind, verdict):
    """verdict に空でない値があれば完了（stop・ask を含む。定義は変えない）。"""
    done = {"gates": [{"id": "G1", "verdict": verdict}]}
    assert not _detected(_contract_tree(tmp_path, monkeypatch, "T-2026-01-01-x", kind, done))


def test_a_contract_without_the_omission_is_never_detected(tmp_path, monkeypatch):
    c = _contract_tree(tmp_path, monkeypatch, "T-2026-01-01-x", "impl", None)
    spec = dict(c.spec)
    spec["contract"] = {"allow_write": ["tasks/T-2026-01-01-x/"]}
    fine = check_spec.Contract(c.task, c.md_path, c.md_text, c.spec_path, spec)
    assert not _detected(fine)


def test_the_scope_of_the_rule_is_unchanged(tmp_path, monkeypatch):
    """exp は無条件、他の kind は allow_write を宣言している契約だけ。"""
    c = _contract_tree(tmp_path, monkeypatch, "T-2026-01-01-x", "impl", None)
    spec = dict(c.spec)
    spec["contract"] = {}
    undeclared = check_spec.Contract(c.task, c.md_path, c.md_text, c.spec_path, spec)
    assert not _detected(undeclared)  # impl で宣言なし: 対象外
    exp = check_spec.Contract(c.task, c.md_path, c.md_text, c.spec_path, {**spec, "meta": {"kind": "exp"}})
    assert _detected(exp)  # exp は宣言なしでも検出


def test_the_completed_check_is_the_same_function_as_p13_and_p14(tmp_path, monkeypatch):
    """判定関数を常に偽にする変異: spec-check の除外と P13 の SKIP が同時に消える。"""
    task = "T-2026-01-02-y"
    c = _contract_tree(tmp_path, monkeypatch, task, "exp", DONE)
    spec = {"meta": {"kind": "exp"}}
    p13 = lambda: preflight_task.check_symmetry_table(task).status  # noqa: E731
    p14 = lambda: preflight_task.check_proposal_card(task, spec).status  # noqa: E731

    assert not _detected(c) and p13() == "SKIP" and p14() == "SKIP"  # 変異前

    monkeypatch.setattr(preflight_task, "completed_verdicts", lambda task_id: [])
    assert _detected(c)  # 除外が消えた
    assert p13() != "SKIP" and p14() != "SKIP"  # P13・P14 の SKIP も同時に消えた
