import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from preflight_task import (  # noqa: E402
    Check,
    decide_applicability,
    format_report,
    summarize,
)


def _spec(kind="impl", preflight=None, decisions=None):
    return {
        "meta": {"kind": kind},
        "plan": {"env": {"venv": ".venv", "preflight": preflight or ["venv_active"]}},
        "governance": {"decisions_required": decisions or []},
        "outputs": {"destination": "tools/"},
    }


def test_impl_skips_exp_only_checks():
    applicable = decide_applicability(_spec(kind="impl"))
    assert applicable["P4"] is False
    assert applicable["P5"] is False
    assert applicable["P1"] is True
    assert applicable["P8"] is True


def test_exp_applies_prereg_and_frozen():
    applicable = decide_applicability(_spec(kind="exp"))
    assert applicable["P4"] is True
    assert applicable["P5"] is True


def test_cuda_check_requires_explicit_listing():
    without = decide_applicability(_spec(kind="exp", preflight=["venv_active"]))
    assert without["P2"] is False
    with_it = decide_applicability(
        _spec(kind="exp", preflight=["venv_active", "cuda_ext_loaded"])
    )
    assert with_it["P2"] is True


def test_skip_is_not_pass():
    checks = [
        Check("P1", "venv_active", "PASS", "VIRTUAL_ENV=.venv"),
        Check("P2", "cuda_ext_loaded", "SKIP", "契約に未記載"),
    ]
    counts = summarize(checks)
    assert counts["PASS"] == 1
    assert counts["SKIP"] == 1
    assert counts["FAIL"] == 0


def test_any_fail_makes_exit_nonzero():
    checks = [
        Check("P1", "venv_active", "PASS", ""),
        Check("P6", "decisions_answered", "FAIL", "未回答が 1 件"),
    ]
    assert summarize(checks)["FAIL"] == 1


def test_report_is_machine_readable():
    checks = [
        Check("P1", "venv_active", "PASS", "VIRTUAL_ENV=/x/.venv"),
        Check("P2", "cuda_ext_loaded", "SKIP", "契約に未記載"),
    ]
    text = format_report(checks)
    lines = [line for line in text.splitlines() if line.startswith("P")]
    assert len(lines) == 2
    for line in lines:
        parts = line.split(None, 3)
        assert parts[0].startswith("P")
        assert parts[2] in {"PASS", "WARN", "SKIP", "FAIL"}
    assert "RESULT:" in text


def test_report_is_stable_across_runs():
    checks = [Check("P1", "venv_active", "PASS", "VIRTUAL_ENV=/x/.venv")]
    assert format_report(checks) == format_report(checks)


def test_destination_that_can_be_created_passes(tmp_path, monkeypatch):
    """まだ存在しないが作成できる出力先は PASS とする。

    新しい出力領域を作る契約では destination が実行前に存在しない。
    それを FAIL にすると、そうした契約すべてで偽陽性になる。
    """
    import preflight_task

    monkeypatch.setattr(preflight_task, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    spec = {"outputs": {"destination": "docs/sessions/"}}
    check = preflight_task.check_destination(spec)
    assert check.status == "PASS", check.detail
    assert "作成" in check.detail
    # 検査が実体を作ってしまわないこと
    assert not (tmp_path / "docs" / "sessions").exists()


def test_destination_that_cannot_be_created_fails(tmp_path, monkeypatch):
    """親も存在せず作成できない出力先は FAIL のままとする。陽性対照の対。"""
    import preflight_task

    monkeypatch.setattr(preflight_task, "REPO_ROOT", tmp_path)
    readonly = tmp_path / "locked"
    readonly.mkdir()
    readonly.chmod(0o500)
    spec = {"outputs": {"destination": "locked/nested/"}}
    try:
        check = preflight_task.check_destination(spec)
        assert check.status == "FAIL", check.detail
    finally:
        readonly.chmod(0o700)


def test_existing_destination_still_probed(tmp_path, monkeypatch):
    """既存の出力先は従来どおり実際に書いて消す検査を行う。"""
    import preflight_task

    monkeypatch.setattr(preflight_task, "REPO_ROOT", tmp_path)
    (tmp_path / "tools").mkdir()
    spec = {"outputs": {"destination": "tools/"}}
    check = preflight_task.check_destination(spec)
    assert check.status == "PASS"
    assert "書き込みと削除" in check.detail


# ------------------------------------------------ 層 4（実行直前の警告）
#
# 起票者が層 1 を回し忘れても、実行の直前に出る。**二重の網である。**
# 契約の誤りは実行者の責任ではないため、**終了コードを変えない。**

from preflight_task import STATUSES, check_spec_lint, main  # noqa: E402

HITTING_TASK = "T-2026-08-15-template-leak-and-autosync-conflict"


def test_warn_is_neither_pass_nor_fail():
    """WARN は合格でも失敗でもない。**SKIP と PASS を区別しているのと同じ扱いにする。**"""
    assert "WARN" in STATUSES
    checks = [
        Check("P1", "venv_active", "PASS", ""),
        Check("P9", "spec_lint", "WARN", "2 件が該当"),
    ]
    counts = summarize(checks)
    assert counts["PASS"] == 1
    assert counts["WARN"] == 1
    assert counts["FAIL"] == 0


def test_warn_does_not_change_exit_code():
    """判定は FAIL の数のみで決まる。**WARN をいくら足しても終了コードは動かない。**"""
    passing = [Check("P1", "venv_active", "PASS", "")]
    warning = passing + [Check("P9", "spec_lint", "WARN", "2 件が該当")]
    assert summarize(passing)["FAIL"] == summarize(warning)["FAIL"] == 0
    failing = warning + [Check("P6", "decisions_answered", "FAIL", "未回答")]
    assert summarize(failing)["FAIL"] == 1


def test_report_shows_warn_count():
    """警告の件数が合計に出る。**出ない警告は警告になっていない。**"""
    text = format_report([Check("P9", "spec_lint", "WARN", "2 件が該当")])
    assert "1 WARN" in text


def test_spec_lint_warns_on_hitting_contract():
    """該当する契約では警告が出る。"""
    check = check_spec_lint(HITTING_TASK)
    assert check.status == "WARN"
    assert "forbidden_vs_output" in check.detail or "integration" in check.detail
    assert "終了コードは変わらない" in check.detail


def test_spec_lint_passes_on_clean_contract(tmp_path, monkeypatch):
    """特定の実在契約に依存しない契約では警告が出ない。"""
    import check_spec

    task = "T-9999-99-99-clean-control"
    task_dir = tmp_path / task
    task_dir.mkdir()
    (task_dir / "SPEC.md").write_text("# clean contract\n", encoding="utf-8")
    (task_dir / "spec.yaml").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(check_spec, "TASKS_DIR", tmp_path)
    check = check_spec_lint(task)
    assert check.status == "PASS"
    assert "該当なし" in check.detail


def test_warn_and_pass_both_keep_zero_exit_code(monkeypatch, capsys):
    """P9 が PASS と WARN のどちらでも終了コードを変えない。"""
    for status in ("PASS", "WARN"):
        monkeypatch.setattr(
            "preflight_task.run_checks",
            lambda task, spec, status=status: [Check("P9", "spec_lint", status, "control")],
        )
        monkeypatch.setattr(sys, "argv", ["preflight_task.py", "--task", HITTING_TASK])
        assert main() == 0
        assert "P9 spec_lint" in capsys.readouterr().out
