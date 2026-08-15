"""線形 probe の生成物を独立に再読込して整合性を検証する。"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np


AUDIT = Path(__file__).resolve().parent


def rows(name: str) -> list[dict[str, str]]:
    with (AUDIT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    probe = rows("probe_result.csv")
    control = rows("control.csv")
    phase_a = json.loads((AUDIT / "phase_a.json").read_text(encoding="utf-8"))
    summary = json.loads((AUDIT / "summary.json").read_text(encoding="utf-8"))
    checks: list[tuple[str, Callable[[], bool]]] = [
        ("CSV_BOM", lambda: all((AUDIT / name).read_bytes().startswith(b"\xef\xbb\xbf") for name in ("probe_result.csv", "control.csv"))),
        ("PROBE_5_ROWS", lambda: len(probe) == 5),
        ("CONTROL_30_ROWS", lambda: len(control) == 30),
        ("NO_CONVERGENCE_WARNING", lambda: sum(int(r["convergence_warnings"]) for r in probe + control) == 0),
        ("METRICS_BOUNDED", lambda: all(0.0 <= float(r[k]) <= 1.0 for r in probe + control for k in ("roc_auc", "average_precision"))),
        ("ALIGNMENT_COUNTS", lambda: [(phase_a["splits"][s]["teacher_without_feature"], phase_a["splits"][s]["feature_without_teacher"]) for s in ("train", "val", "test")] == [(0, 301), (0, 1), (0, 158)]),
        ("TEST_NOT_MODELED", lambda: summary["method"]["test_used_for_modeling"] is False),
        ("RANDOM_AT_CHANCE", lambda: abs(summary["negative_controls"]["random_features"]["auc_mean"] - 0.5) <= 0.05),
        ("SHUFFLE_AT_CHANCE", lambda: abs(summary["negative_controls"]["shuffled_train_teachers"]["auc_mean"] - 0.5) <= 0.05),
        ("PRESCRIBED_CONTROL_INVALID", lambda: summary["prescribed_positive_control"]["roc_auc"] == "UNKNOWN" and summary["prescribed_positive_control"]["val_positive"] == summary["prescribed_positive_control"]["val_total"]),
        ("SUPPLEMENTAL_CONTROL_WORKS", lambda: float(summary["supplemental_positive_control"]["roc_auc"]) > max(float(r["roc_auc"]) for r in control)),
        ("GROUP_MEANS_RECOMPUTE", lambda: np.isclose(np.mean([float(probe[i]["roc_auc"]) for i in (0, 1)]), summary["actual_group_comparison"]["visibility_mean_roc_auc"]) and np.isclose(np.mean([float(probe[i]["roc_auc"]) for i in (2, 3, 4)]), summary["actual_group_comparison"]["grasp_mean_roc_auc"])),
    ]
    failures = []
    for name, check in checks:
        ok = bool(check())
        print(("PASS" if ok else "FAIL"), name)
        if not ok:
            failures.append(name)
    print(f"RESULT: {len(checks) - len(failures)} PASS / {len(failures)} FAIL")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
