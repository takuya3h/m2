import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_task import (  # noqa: E402
    resolve_sigma_policy,
    task_id_conflicts,
    validate_l1,
)


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


def _hard(findings):
    return [f for f in findings if not f.check.endswith("W")]


def test_pipe_in_gate_check_fails():
    spec = _minimal_impl_spec()
    spec["plan"]["gates"] = [
        {"id": "G1", "after": "A", "check": "a と b のどちらか", "on_fail": "stop"}
    ]
    spec["plan"]["gates"][0]["check"] = "a " + chr(124) + " b のどちらか"
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert "L1-3" in {f.check for f in _hard(findings)}


def test_pipe_outside_table_fields_is_warning_only():
    spec = _minimal_impl_spec()
    spec["meta"]["kind"] = "exp"
    spec["inputs"]["denominator"] = {"ref": "exp:transfer/s4_base_tecno", "metric": "accuracy"}
    spec["outputs"]["expected_runs"] = 6
    spec["outputs"]["stamp"] = {"task_id_in": "config.yaml"}
    spec["prereg"] = {
        "prediction": "p",
        "primary_endpoint": "macro_f1",
        "decision_rule": "abs(delta) " + chr(124) + " sigma",
        "stop_conditions": ["s"],
        "committed_at": None,
        "commit": None,
    }
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert _hard(findings) == []
    assert "L1-3W" in {f.check for f in findings}


def test_abs_notation_decision_rule_passes():
    spec = _minimal_impl_spec()
    spec["meta"]["kind"] = "exp"
    spec["inputs"]["denominator"] = {"ref": "exp:transfer/s4_base_tecno", "metric": "accuracy"}
    spec["outputs"]["expected_runs"] = 6
    spec["outputs"]["stamp"] = {"task_id_in": "config.yaml"}
    spec["prereg"] = {
        "prediction": "非飽和域では正の差が出る",
        "primary_endpoint": "macro_f1",
        "decision_rule": "abs(delta) / sigma >= 1 かつ 全 seed 同符号",
        "stop_conditions": ["G1 不通過"],
        "committed_at": None,
        "commit": None,
    }
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert findings == [], [str(f) for f in findings]


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


def test_sigma_policy_defaults_are_inherited():
    spec = _minimal_impl_spec()
    resolved = resolve_sigma_policy(spec, defaults={
        "series": "pstd",
        "sigma_source": "paired_delta",
        "delta_sigma_source": "paired",
    })
    assert resolved == {
        "series": "pstd",
        "sigma_source": "paired_delta",
        "delta_sigma_source": "paired",
    }


def test_sigma_policy_explicit_overrides_default():
    spec = _minimal_impl_spec()
    spec["inputs"]["sigma_policy"] = {"series": "sstd"}
    resolved = resolve_sigma_policy(spec, defaults={
        "series": "pstd",
        "sigma_source": "paired_delta",
        "delta_sigma_source": "paired",
    })
    assert resolved["series"] == "sstd"
    assert resolved["sigma_source"] == "paired_delta"


def test_task_id_single_ref_is_not_conflict():
    identities = {"2026-08-05T09:00:00Z": ["refs/remotes/origin/phase0"]}
    assert task_id_conflicts("T-2026-08-05-example-task", identities) == []


def test_task_id_same_created_at_across_refs_is_not_conflict():
    """squash merge 後に旧ブランチが残っている状態の回帰テスト。"""
    identities = {
        "2026-08-05T09:00:00Z": [
            "refs/remotes/origin/phase0",
            "refs/remotes/origin/feat/task-contract-bootstrap",
        ]
    }
    assert task_id_conflicts("T-2026-08-05-example-task", identities) == []


def test_task_id_differing_created_at_is_conflict():
    """別ホストが同じ task_id を独立に起票した状態。"""
    identities = {
        "2026-08-05T09:00:00Z": ["refs/remotes/origin/phase0"],
        "2026-08-05T11:30:00Z": ["refs/remotes/origin/exp/lecun-foo"],
    }
    conflicts = task_id_conflicts("T-2026-08-05-example-task", identities)
    assert len(conflicts) == 2
    assert any("phase0" in c for c in conflicts)


def test_newline_in_task_id_is_rejected():
    """終端一致に改行が紛れ込む経路を塞ぐ。

    Python の $ は文字列末尾の改行に一致するため、改行入り識別子が
    検証を素通りしうる。fetch_task.py で実際に見つかった欠陥の水平展開。
    """
    spec = _minimal_impl_spec()
    evil = "T-2026-08-03-example-task\nmalicious"
    spec["meta"]["task_id"] = evil
    findings = validate_l1(spec, dir_name=evil)
    assert _hard(findings), "改行入り task_id が素通りしました"


def test_trailing_newline_only_is_rejected():
    """末尾の改行だけでも拒否する。これが実際に悪用できた形である。"""
    spec = _minimal_impl_spec()
    evil = "T-2026-08-03-example-task\n"
    spec["meta"]["task_id"] = evil
    findings = validate_l1(spec, dir_name=evil)
    assert _hard(findings), "末尾改行つき task_id が素通りしました"
