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


def test_unknown_version_is_rejected():
    bad = _valid()
    bad["result_version"] = 3
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


# --- 版 2（拡張した様式） -------------------------------------------------
#
# 版で分ける理由: 過去の完了報告に拡張した様式を遡って適用しない。
# 版 1 の記述は今後も通り続けなければならない。

# 起票者の誤りの記述は「何が誤っていたか」と「指示どおり実行すると何が起きたか」の
# 2 つを含む。既存 15 件の長さは [76, 93, 94, ...] で、最短の 76 字は誤りの内容だけを
# 述べて結果を欠く。次に短いのが 93 字。80 はその間にあり、結果を述べない最短の例を
# 拒み、両方を述べた最短の例を通す。padding を強いない位置でもある。
DEFECT_NOTE = (
    "実態を測る指示が数字を含む対象を落としており、その一覧を信じると実在する操作を"
    "存在しないと誤判定する。指示どおり実行すると、正しい記述を誤りとして書き換えてしまう"
)


def _valid_v2() -> dict:
    return {
        "result_version": 2,
        "task_id": DIR_NAME,
        "status": "pass",
        "host": "lecun",
        "branch": "feat/example",
        "pr": 99,
        "merged": False,
        "gates": [{"id": "G1", "verdict": "pass", "note": "両方向で測り HEAD が不変だった"}],
        "tests": {"before_failed": 5, "after_failed": 5, "after_passed": 314},
        "deviations": [{"type": "spec_defect", "note": "契約の測り方が誤っていた"}],
        "issuer_defects": [{"type": "check_does_not_check", "note": DEFECT_NOTE}],
        "followups": ["他ホストでの動作は未検証"],
        "unknowns": [],
        "commits": ["abc1234"],
    }


def test_valid_v2_passes():
    assert validate_task.validate_result(_valid_v2(), dir_name=DIR_NAME) == []


def test_v2_requires_gate_note():
    bad = _valid_v2()
    bad["gates"] = [{"id": "G1", "verdict": "pass"}]
    assert _checks(bad)


def test_v2_rejects_empty_gate_note():
    bad = _valid_v2()
    bad["gates"] = [{"id": "G1", "verdict": "pass", "note": ""}]
    assert _checks(bad)


def test_v2_requires_deviations_as_list():
    bad = _valid_v2()
    bad["deviations"] = 3
    assert _checks(bad)


def test_v2_rejects_empty_deviations():
    bad = _valid_v2()
    bad["deviations"] = []
    assert _checks(bad)


def test_v2_rejects_unknown_deviation_type():
    bad = _valid_v2()
    bad["deviations"] = [{"type": "convenience", "note": "列挙にない型"}]
    assert _checks(bad)


@pytest.mark.parametrize("dev_type", ["spec_defect", "environment", "judgement"])
def test_v2_accepts_every_listed_deviation_type(dev_type):
    ok = _valid_v2()
    ok["deviations"] = [{"type": dev_type, "note": "理由"}]
    assert validate_task.validate_result(ok, dir_name=DIR_NAME) == []


def test_v2_rejects_short_defect_note():
    bad = _valid_v2()
    bad["issuer_defects"] = [{"type": "check_does_not_check", "note": "検査が甘い"}]
    assert _checks(bad)


# --- 版 1 を拒まないこと ---------------------------------------------------


def test_v1_still_passes_without_gate_note():
    """過去の報告は gates に note を持たない。拒んではならない。"""
    assert validate_task.validate_result(_valid(), dir_name=DIR_NAME) == []


def test_v1_still_accepts_integer_deviations_and_short_note():
    ok = _valid()
    ok["deviations"] = 0
    ok["issuer_defects"] = [{"type": "self_contradiction", "note": "短い"}]
    assert validate_task.validate_result(ok, dir_name=DIR_NAME) == []
