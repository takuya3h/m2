import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_task import validate_l1  # noqa: E402


def _minimal_impl_spec() -> dict:
    return {
        "spec_version": 1,
        "meta": {
            "task_id": "T-2026-08-03-example-task",
            "kind": "impl",
            "title": "example",
            "origin": "claude-app",
            "created_at": "2026-08-03T00:00:00Z",
            "created_from": {
                "runindex_commit": "762a5c8",
                "counts": {"index": 749, "experiments": 206, "verdicts": 1038},
            },
        },
        "intent": {"question": "q", "decision_at_stake": "d"},
        "inputs": {
            "data": {"dataset": "egosurgery_phase_v1", "split_files": ["data/splits/ego_val.txt"]},
            "code": {"entrypoints": ["scripts/train_haux.py"]},
        },
        "contract": {
            "inject_verbatim": ["conventions#split"],
            "conventions_rev": "762a5c8",
            "prohibitions": ["no_split_redefine"],
            "verbatim_forbidden": True,
        },
        "plan": {
            "phases": [{"id": "A", "name": "impl", "gpu": False}],
            "env": {"venv": ".venv", "preflight": ["venv_active"]},
        },
        "outputs": {
            "must_have": ["notes.md"],
            "destination": "tools/",
            "acceptance": ["make task-validate が exit 0"],
        },
        "governance": {"deviations_required": True, "integrity": ["no_fabrication"]},
    }


def _ids(findings):
    return sorted({finding.check for finding in findings})


def test_minimal_impl_spec_passes():
    spec = _minimal_impl_spec()
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert findings == [], _ids(findings)


def test_exp_without_prereg_fails():
    spec = _minimal_impl_spec()
    spec["meta"]["kind"] = "exp"
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert "L1-1" in _ids(findings)


def test_unknown_key_fails():
    spec = _minimal_impl_spec()
    spec["meta"]["nickname"] = "boom"
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert "L1-1" in _ids(findings)


def test_bad_task_id_format_fails():
    spec = _minimal_impl_spec()
    spec["meta"]["task_id"] = "B-33"
    findings = validate_l1(spec, dir_name="B-33")
    assert "L1-1" in _ids(findings)


def test_dirname_mismatch_fails():
    spec = _minimal_impl_spec()
    findings = validate_l1(spec, dir_name="T-2026-08-03-other-name")
    assert "L1-2" in _ids(findings)


def test_pipe_in_string_fails():
    spec = _minimal_impl_spec()
    spec["intent"]["question"] = "paired_delta | within_run_seed_spread のどちらか"
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert "L1-3" in _ids(findings)


def test_bare_denominator_ref_fails():
    spec = _minimal_impl_spec()
    spec["inputs"]["denominator"] = {"ref": "s4_base_tecno", "metric": "accuracy"}
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert set(_ids(findings)) & {"L1-1", "L1-4"}


def test_verbatim_number_in_intent_fails():
    spec = _minimal_impl_spec()
    spec["intent"]["decision_at_stake"] = "分母は 0.8983 なので比較する"
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert "L1-5" in _ids(findings)
