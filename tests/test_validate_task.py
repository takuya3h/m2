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


import validate_task  # noqa: E402

# --- L2-8 母集団の移動 -----------------------------------------------------
#
# 契約を起票してから実行されるまでに母集団は動く。**分母を宣言しない契約では、
# その差は判定に影響しない。** それでも毎回警告が出ると、実行のたびに承認を求める
# ことになり、本当に見るべき警告（注入対象の変更）が埋もれる。

_IMPOSSIBLE_COUNTS = {"index": 1, "experiments": 1, "verdicts": 1}


def _spec_with_counts(*, denominator: bool) -> dict:
    spec = {
        "meta": {"created_from": {"counts": dict(_IMPOSSIBLE_COUNTS)}},
        "inputs": {"data": {"dataset": "x"}},
    }
    if denominator:
        spec["inputs"]["denominator"] = {"ref": "exp:transfer/example"}
    return spec


def test_population_drift_is_silent_without_denominator(capsys):
    validate_task._warn_population_drift(_spec_with_counts(denominator=False))
    assert "L2-8" not in capsys.readouterr().err


def test_population_drift_warns_with_denominator(capsys):
    """陰性側だけを見て満足しない。宣言した契約では従来どおり出ること。"""
    validate_task._warn_population_drift(_spec_with_counts(denominator=True))
    assert "L2-8" in capsys.readouterr().err


def test_conventions_rev_warning_does_not_depend_on_denominator(capsys):
    """注入対象が変わっていないかの確認は分母と無関係に意味がある。"""
    validate_task._warn_conventions_rev({"contract": {"conventions_rev": "1201f4f"}})
    assert "L2-6" in capsys.readouterr().err


# --------------------------------- 様式の版 2 と 3（陽性対照の強制）
#
# 判定が通ったことは、その判定が働いていることを意味しない。**空振りかどうかは
# 判定の外から確かめるしかない。** 版で分岐して既存の契約と報告を落とさない。

import json  # noqa: E402

from validate_task import POSITIVE_CONTROL_COLUMN, validate_spec_md  # noqa: E402

_TABLE_HEAD = f"| # | 判定 | 期待 | {POSITIVE_CONTROL_COLUMN} |\n|---|---|---|---|\n"


def _spec_md(tmp_path: Path, body: str) -> Path:
    (tmp_path / "SPEC.md").write_text(f"# x\n\n## 完了判定\n\n{body}", encoding="utf-8")
    return tmp_path


def test_v2_filled_positive_control_column_passes(tmp_path):
    body = _TABLE_HEAD + "| 1 | 検査が通る | exit 0 | 規則を 1 つ外すと落ちることを測った |\n"
    assert validate_spec_md({"spec_version": 2}, _spec_md(tmp_path, body)) == []


def test_v2_empty_positive_control_column_fails(tmp_path):
    """欄が空なら失敗する。**これが強制の本体である。**"""
    body = _TABLE_HEAD + "| 1 | 検査が通る | exit 0 |  |\n"
    findings = validate_spec_md({"spec_version": 2}, _spec_md(tmp_path, body))
    assert [f.check for f in findings] == ["L1-9"]
    assert POSITIVE_CONTROL_COLUMN in findings[0].message


def test_v2_missing_column_fails(tmp_path):
    body = "| # | 判定 | 期待 |\n|---|---|---|\n| 1 | 検査が通る | exit 0 |\n"
    findings = validate_spec_md({"spec_version": 2}, _spec_md(tmp_path, body))
    assert [f.check for f in findings] == ["L1-9"]


def test_v2_missing_table_fails(tmp_path):
    findings = validate_spec_md({"spec_version": 2}, _spec_md(tmp_path, "表が無い。\n"))
    assert [f.check for f in findings] == ["L1-9"]


def test_v2_dash_counts_as_filled(tmp_path):
    """適用外の明示は書き手の判断として通す。**欄が見えていることが目的である。**"""
    body = _TABLE_HEAD + "| 1 | 契約検証が通る | exit 0 | — |\n"
    assert validate_spec_md({"spec_version": 2}, _spec_md(tmp_path, body)) == []


def test_v1_without_column_is_untouched(tmp_path):
    """既存の契約を落とさない。**過去を書き換えて通す方法は採らない。**"""
    body = "| # | 判定 | 期待 |\n|---|---|---|\n| 1 | 検査が通る | exit 0 |\n"
    assert validate_spec_md({"spec_version": 1}, _spec_md(tmp_path, body)) == []
    assert validate_spec_md({}, _spec_md(tmp_path, body)) == []


def _result_validator():
    from jsonschema import Draft202012Validator

    path = Path(__file__).resolve().parents[1] / "tasks" / "_schema" / "result.schema.json"
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def _result(**over) -> dict:
    base = {
        "task_id": "T-2026-08-11-positive-control",
        "status": "pass",
        "host": "h",
        "branch": "b",
        "pr": None,
        "merged": False,
        "gates": [{"id": "G1", "verdict": "pass", "note": "実測した"}],
        "tests": {"before_failed": 5, "after_failed": 5, "after_passed": 404},
        "deviations": [{"type": "judgement", "note": "n"}],
        "issuer_defects": [],
        "followups": [],
        "unknowns": [],
        "commits": ["abc1234"],
    }
    base.update(over)
    return base


_PC = [{"judgement": "判定 4", "breaking_input": "規則を 1 つ外す", "observed": "11/16 から 10/16 へ落ちた"}]


def test_result_v3_with_positive_controls_passes():
    assert not list(_result_validator().iter_errors(
        _result(result_version=3, positive_controls=_PC)
    ))


def test_result_v3_without_positive_controls_fails():
    """項目そのものが無ければ失敗する。"""
    errors = list(_result_validator().iter_errors(_result(result_version=3)))
    assert any("positive_controls" in e.message for e in errors)


def test_result_v3_empty_positive_controls_fails():
    """空配列も失敗する。**空にできるなら強制になっていない。**"""
    errors = list(_result_validator().iter_errors(
        _result(result_version=3, positive_controls=[])
    ))
    assert any("non-empty" in e.message for e in errors)


def test_result_v3_empty_observed_fails():
    """実測の欄が空なら失敗する。期待だけ書いて測らないことを許さない。"""
    bad = [{"judgement": "a", "breaking_input": "b", "observed": ""}]
    errors = list(_result_validator().iter_errors(
        _result(result_version=3, positive_controls=bad)
    ))
    assert any("non-empty" in e.message for e in errors)


def test_result_v3_inherits_v2_requirements():
    """版 3 は版 2 の要件を含む。**minimum で受けているため const 2 に戻すと失われる。**"""
    errors = list(_result_validator().iter_errors(
        _result(result_version=3, positive_controls=_PC,
                gates=[{"id": "G1", "verdict": "pass"}])
    ))
    assert any("note" in e.message for e in errors)


def test_result_v1_and_v2_do_not_require_positive_controls():
    """既存の報告が落ちない。**過去の記録は教師データであり履歴である。**"""
    validator = _result_validator()
    assert not list(validator.iter_errors(_result(result_version=2)))
    assert not list(validator.iter_errors(
        _result(result_version=1, deviations=3, gates=[{"id": "G1", "verdict": "pass"}])
    ))


def test_v2_ignores_indented_example_table(tmp_path):
    """字下げされた例示の表を本物と誤認しない。

    契約は新しい欄の書き方を字下げして載せる。それを拾うと、後続の行が表でないため
    走査が即座に終わり、**本物の完了判定表を一度も検査しないまま合格する。**
    本契約の SPEC.md で実際に起きた。ここで固定する。
    """
    body = (
        f"    | # | 判定 | 期待 | {POSITIVE_CONTROL_COLUMN} |\n\n"
        "本物の表は次である。\n\n"
        + _TABLE_HEAD
        + "| 1 | 検査が通る | exit 0 |  |\n"
    )
    findings = validate_spec_md({"spec_version": 2}, _spec_md(tmp_path, body))
    assert [f.check for f in findings] == ["L1-9"], "例示を拾って本物を検査していない"
