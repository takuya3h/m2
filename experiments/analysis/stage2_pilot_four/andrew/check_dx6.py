"""andrew の decoder-xattn 6 本の終わりの確認（非公式 T-2026-10-19-stage2-pilot-four-new-types、handoff_andrew.md S10）。

本体の .venv で動かす。読むだけ。結果を標準出力に JSON で出す（andrew/s10_check.json に保存する）。

    /home/ubuntu/slocal2/m2/.venv/bin/python -I check_dx6.py > s10_check.json
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

WT = Path("/home/ubuntu/slocal2/m2-four-andrew")
FOUR = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types")
ARMS = [("empty", 0), ("pred_noCF", 0), ("gt", 0), ("pred_CF", 1), ("gtpred_CF", 1), ("shuffle", 1)]
INIT = 0.7273450248398429


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def utc(p: Path) -> datetime:
    return datetime.strptime(p.read_text().strip(), "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)


out = {}
for arm, gpu in ARMS:
    run = f"stage2four_pd_DX_{arm}_ep4_seed42"
    r = WT / "experiments/phase1" / run
    t = json.loads((r / "t1b_result.json").read_text())
    m = json.loads((r / "stage2four_metrics.json").read_text())
    ckpt = FOUR / "pd_ckpt" / run / "best_t1b.pth"
    hours = (utc(r / "end.txt") - utc(r / "start.txt")).total_seconds() / 3600
    checks = {
        "exit_code_0": (r / "exit_code.txt").read_text().strip() == "0",
        "result_selection_final_epoch": t["result_selection"] == "final_epoch",
        "best_eq_final_eq_3": t["best_epoch"] == t["final_epoch"] == 3,
        "mAP_eq_final_mAP": t["mAP"] == t["final_mAP"],
        "init_eq_tower": m["init"] == INIT,
        "frozen_unchanged": m["frozen_unchanged"] is True,
        "ms_deform_attn_ext_True": "ms_deform_attn_ext True" in (r / "env_check.txt").read_text(),
        "server_andrew": (r / "server.txt").read_text().strip().lower() == "andrew",
        "gates_init_zero": all(v == 0.0 for v in m["gates_by_epoch"]["-1"]["tanh_alpha"]),
    }
    out[arm] = {
        "run": run,
        "gpu": gpu,
        "checks": checks,
        "all_checks": all(checks.values()),
        "overall_mAP": m["AP"],
        "target_AP": m["target_AP"],
        "control_AP": m["control_AP"],
        "per_video_AP": m["per_video_AP"],
        "per_epoch_mAP": m["per_epoch_mAP"],
        "gates_by_epoch": m["gates_by_epoch"],
        "hours": round(hours, 3),
        "start_utc": (r / "start.txt").read_text().strip(),
        "end_utc": (r / "end.txt").read_text().strip(),
        "git_commit_txt": (r / "git_commit.txt").read_text().strip(),
        "predictions_sha256": {p.name: sha256(p) for p in sorted((r / "predictions").glob("*.json.gz"))},
        "ckpt": str(ckpt),
        "ckpt_bytes": ckpt.stat().st_size,
        "ckpt_sha256": sha256(ckpt),
    }
print(json.dumps(out, ensure_ascii=False, indent=2))
