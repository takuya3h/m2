"""Phase A Step 3 / Phase C Step 4 — 第一層と第二層の排他を実挙動で測る。

**説明文ではなく実挙動で確かめる。** 正規表現を目で追うのではなく、
実装の `validate_l1` と `validate_l2` に spec を与えて出た指摘を数える。

直す前は「二区画は第一層を通り第二層で落ちる」「完全形は第一層で落ちる」が
両立する（＝排他）。直した後は完全形が両層とも通る。同じ測定器を前後で使う。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

from validate_task import conventions_anchors, validate_l1, validate_l2  # noqa: E402

DIR_NAME = "T-2026-08-03-example-task"

TWO_SEGMENT = "exp:phase1/s4_phase_baseline"
FULL_FORM = "exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42"


def _exp_spec(ref: str) -> dict:
    """指摘ゼロになる exp の spec に、分母の参照だけを差し替えて返す。

    土台は試験が「指摘ゼロ」を主張している形に合わせる。**分母以外で指摘が出ると
    測定が濁る**ため、逐語の錨は実在するものから取る。
    """
    anchor = "split" if "split" in conventions_anchors() else sorted(conventions_anchors())[0]
    return {
        "spec_version": 1,
        "meta": {
            "task_id": DIR_NAME,
            "kind": "exp",
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
            "denominator": {"ref": ref, "metric": "accuracy"},
        },
        "contract": {
            "inject_verbatim": [f"conventions#{anchor}"],
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
            "expected_runs": 6,
            "stamp": {"task_id_in": "config.yaml"},
        },
        "prereg": {
            "prediction": "非飽和域では正の差が出る",
            "primary_endpoint": "macro_f1",
            "decision_rule": "abs(delta) / sigma >= 1 かつ 全 seed 同符号",
            "stop_conditions": ["G1 不通過"],
            "committed_at": None,
            "commit": None,
        },
        "governance": {"deviations_required": True, "integrity": ["no_fabrication"]},
    }


def _dump(findings) -> list[dict]:
    return [{"check": f.check, "path": f.path, "message": f.message} for f in findings]


def measure(ref: str) -> dict:
    spec = _exp_spec(ref)
    l1 = validate_l1(spec, dir_name=DIR_NAME)
    l2 = validate_l2(spec)
    # 警告（末尾 W）は停止の根拠ではないため、通過判定からは外す。
    l1_hard = [f for f in l1 if not f.check.endswith("W")]
    l2_hard = [f for f in l2 if not f.check.endswith("W")]
    return {
        "ref": ref,
        "l1_findings": _dump(l1),
        "l2_findings": _dump(l2),
        "l1_passes": l1_hard == [],
        "l2_passes": l2_hard == [],
        "has_L1_4": any(f.check == "L1-4" for f in l1),
        "has_L2_2": any(f.check == "L2-2" for f in l2),
    }


def main() -> None:
    out_name = sys.argv[1] if len(sys.argv) > 1 else "exclusivity.json"
    result = {"two_segment": measure(TWO_SEGMENT), "full_form": measure(FULL_FORM)}
    result["exclusive"] = (
        result["two_segment"]["l1_passes"]
        and not result["two_segment"]["l2_passes"]
        and not result["full_form"]["l1_passes"]
    )
    result["full_form_passes_both"] = (
        result["full_form"]["l1_passes"] and result["full_form"]["l2_passes"]
    )
    (AUDIT / out_name).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / out_name}")
    for key in ("two_segment", "full_form"):
        r = result[key]
        print()
        print(f"[{key}] {r['ref']}")
        print(f"  第一層: {'通る' if r['l1_passes'] else '落ちる'}   第二層: {'通る' if r['l2_passes'] else '落ちる'}")
        for f in r["l1_findings"] + r["l2_findings"]:
            print(f"    {f['check']:<6} {f['path']}: {f['message']}")
    print()
    print(f"排他が成立している（直す前の期待）: {result['exclusive']}")
    print(f"完全形が両層とも通る（直した後の期待）: {result['full_form_passes_both']}")


if __name__ == "__main__":
    main()
