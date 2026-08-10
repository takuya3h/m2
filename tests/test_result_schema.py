"""完了報告の構造化された対（result.yaml）の検証。

**通る例と通らない例の双方**を置く。通る例だけを試すと、
検査が何も拒まないまま「合格」を出していても気付けない。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import validate_task  # noqa: E402

DIR_NAME = "T-2026-01-01-example"


def _valid() -> dict:
    return {
        "result_version": 1,
        "task_id": DIR_NAME,
        "status": "pass",
        "host": "lecun",
        "branch": "feat/example",
        "pr": 99,
        "merged": False,
        "gates": [{"id": "G1", "verdict": "pass"}],
        "tests": {"before_failed": 5, "after_failed": 5, "after_passed": 271},
        "deviations": 2,
        "issuer_defects": [{"type": "check_does_not_check", "note": "探査が対象を測っていない"}],
        "followups": ["他ホストでの動作は未検証"],
        "unknowns": [],
        "commits": ["abc1234"],
    }


def _checks(result: dict, dir_name: str = DIR_NAME) -> set[str]:
    return {f.check for f in validate_task.validate_result(result, dir_name=dir_name)}


def test_valid_result_passes():
    assert validate_task.validate_result(_valid(), dir_name=DIR_NAME) == []


def test_task_id_must_match_directory_name():
    assert _checks(_valid(), dir_name="T-2026-01-02-other")


def test_unknown_defect_type_is_rejected():
    bad = _valid()
    bad["issuer_defects"] = [{"type": "typo_in_prose", "note": "列挙にない型"}]
    assert _checks(bad)


def test_stopped_without_reason_is_rejected():
    bad = _valid()
    bad["status"] = "stopped"
    bad["followups"] = []
    bad["unknowns"] = []
    assert _checks(bad)


def test_stopped_with_reason_passes():
    ok = _valid()
    ok["status"] = "stopped"
    ok["unknowns"] = ["台帳へ到達できず停止時期を測れない"]
    assert validate_task.validate_result(ok, dir_name=DIR_NAME) == []


def test_wrong_version_is_rejected():
    bad = _valid()
    bad["result_version"] = 2
    assert _checks(bad)


def test_unknown_gate_verdict_is_rejected():
    bad = _valid()
    bad["gates"] = [{"id": "G1", "verdict": "maybe"}]
    assert _checks(bad)


def test_missing_file_is_not_a_failure(tmp_path, monkeypatch):
    """対が無い契約は失敗にしない。起票直後には存在しない。"""
    tasks = tmp_path / "tasks"
    (tasks / DIR_NAME).mkdir(parents=True)
    (tasks / DIR_NAME / "spec.yaml").write_text("spec_version: 1\n", encoding="utf-8")
    monkeypatch.setattr(validate_task, "TASKS_DIR", tasks)
    assert validate_task.load_result(tasks / DIR_NAME) is None


def test_present_file_is_loaded(tmp_path):
    d = tmp_path / DIR_NAME
    d.mkdir()
    (d / "result.yaml").write_text("result_version: 1\ntask_id: x\n", encoding="utf-8")
    loaded = validate_task.load_result(d)
    assert loaded is not None and loaded["result_version"] == 1


@pytest.mark.parametrize(
    "defect_type",
    [
        "check_does_not_check",
        "asserted_without_measuring",
        "self_contradiction",
        "shell_assumption",
    ],
)
def test_every_listed_defect_type_is_accepted(defect_type):
    ok = _valid()
    ok["issuer_defects"] = [{"type": defect_type, "note": "例"}]
    assert validate_task.validate_result(ok, dir_name=DIR_NAME) == []
