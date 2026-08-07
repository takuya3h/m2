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
        assert parts[2] in {"PASS", "SKIP", "FAIL"}
    assert "RESULT:" in text


def test_report_is_stable_across_runs():
    checks = [Check("P1", "venv_active", "PASS", "VIRTUAL_ENV=/x/.venv")]
    assert format_report(checks) == format_report(checks)
