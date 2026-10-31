"""案 D の 3 腕の集計（非公式 T-2026-11-01-grasp-pilot-d、Task E・SPEC §6）。.venv で回す。

- 腕ごとの val の overall mAP・標的群 AP・陰性対照群 AP・クラス別 AP・動画ごとの mAP（各 run の metrics.json）
- 差: G を教師 − 補助損失なし、入れ替えた教師 − 補助損失なし、G を教師 − 入れ替えた教師（1 本ずつの差。§6.2）
- 検算: 各 run の保存した予測から det_metrics.summary で計算し直し、metrics.json の値と一致するか
- 設定の差分: config.yaml と command.sh の行のうち、腕で違う行
- test 不使用: 通した動画の集合と {04, 05, 07} の共通（陽性対照として 04 を混ぜた集合で 1 件になるか）
- 予測（§6.3）との照合

    python scripts/grasppilot/d_aggregate.py --out experiments/analysis/grasp_pilot_d/report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

M = Path("/home/ubuntu/slocal2/m2")
sys.path.insert(0, str(M / "scripts"))
from stage2pilot import det_metrics as DM  # noqa: E402

TEST_VIDEOS = {"04", "05", "07"}
ARMS = {"none": "grasppilot3_d_none_ep15_seed42", "gteach": "grasppilot3_d_gteach_ep15_seed42",
        "shuf": "grasppilot3_d_shuf_ep15_seed42"}
PAIRS = [("gteach", "none"), ("shuf", "none"), ("gteach", "shuf")]
ANN_VAL = Path("/home/ubuntu/slocal2/s2fix-bengio-body/data/annotations/egosurgery_tool_folds/A/instances_val.json")


def test_overlap(videos) -> list:
    return sorted(set(videos) & TEST_VIDEOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--arms", default="none,gteach,shuf")
    a = ap.parse_args()
    arms = a.arms.split(",")
    runs = {k: json.loads((M / "experiments/phase1" / ARMS[k] / "metrics.json").read_text()) for k in arms}
    res = {"task_id": "T-2026-11-01-grasp-pilot-d", "unofficial": True, "arms": {}, "diffs": {}, "recompute": {}}
    for k, r in runs.items():
        v = r["val"]
        pc = json.loads((M / "experiments/phase1" / ARMS[k] / "per_class_ap.json").read_text())
        last = r["epochs"][-1]
        res["arms"][k] = {"run": r["run"], "aux_weight": r["aux_weight"], "mAP": v["mAP"], "target_AP": v["target_AP"],
                          "control_AP": v["control_AP"], "per_video_AP": v["per_video_AP"], "per_class_AP": pc,
                          "final_epoch": r["result_state"]["epoch"], "n_epochs": r["n_epochs"],
                          "last_epoch_aux_ce": last.get("step_aux_ce_mean"), "last_epoch_aux_acc": last.get("step_aux_acc_matched"),
                          "aux_ce_by_epoch": [e.get("step_aux_ce_mean") for e in r["epochs"]],
                          "inloop_val_mAP_by_epoch": [e.get("val_mAP_inloop") for e in r["epochs"]],
                          "lr_by_epoch": [e.get("lr_at_step0") for e in r["epochs"]],
                          "det_loss_by_epoch": [e.get("avg_loss_det") for e in r["epochs"]],
                          "videos_passed": r["videos_passed"]}
        # 検算: 保存した予測から計算し直す
        s = DM.summary(ANN_VAL, DM.load_results(r["val_preds"]))
        res["recompute"][k] = {"mAP": s["AP"], "target_AP": s["target_AP"], "control_AP": s["control_AP"],
                               "matches": all(abs(s[x] - v[y]) < 1e-12 for x, y in
                                              (("AP", "mAP"), ("target_AP", "target_AP"), ("control_AP", "control_AP")))
                               and all(abs(s["per_video_AP"][vv] - v["per_video_AP"][vv]) < 1e-12 for vv in v["per_video_AP"])}
    for x, y in PAIRS:
        if x in runs and y in runs:
            A, B = res["arms"][x], res["arms"][y]
            res["diffs"][f"{x}-{y}"] = {
                "mAP": A["mAP"] - B["mAP"], "target_AP": A["target_AP"] - B["target_AP"], "control_AP": A["control_AP"] - B["control_AP"],
                "per_video_AP": {vv: A["per_video_AP"][vv] - B["per_video_AP"][vv] for vv in A["per_video_AP"]},
                "per_class_AP": {c: (A["per_class_AP"][c] - B["per_class_AP"][c]) for c in A["per_class_AP"]
                                 if A["per_class_AP"][c] == A["per_class_AP"][c] and B["per_class_AP"][c] == B["per_class_AP"][c]}}
    # 設定の差分
    cfg = {k: (M / "experiments/phase1" / ARMS[k] / "config.yaml").read_text().splitlines() for k in arms}
    cmd = {k: (M / "experiments/phase1" / ARMS[k] / "command.sh").read_text().splitlines() for k in arms}
    codes = {k: (M / "experiments/phase1" / ARMS[k] / "code_sha256.txt").read_text() for k in arms}

    def differing(d):
        keys = sorted({ln.split(":")[0].split("=")[0] for v in d.values() for ln in v})
        out = []
        for key in keys:
            vals = {k: [ln for ln in v if ln.split(":")[0].split("=")[0] == key] for k, v in d.items()}
            if len({json.dumps(x) for x in vals.values()}) > 1:
                out.append({"key": key, "values": vals})
        return out
    res["config_diff"] = differing(cfg)
    res["command_diff"] = differing(cmd)
    res["code_identical"] = len(set(codes.values())) == 1
    vids = set()
    for r in runs.values():
        vids |= set(r["videos_passed"]["train"]) | set(r["videos_passed"]["val"])
    res["videos_passed_all"] = sorted(vids)
    res["test_overlap"] = test_overlap(vids)
    res["test_overlap_control_with_04"] = test_overlap(vids | {"04"})
    if "gteach" in runs and "none" in runs:
        d = res["diffs"]["gteach-none"]["mAP"]
        res["prediction_1"] = {"text": "G を教師 − 補助損失なし の overall mAP の絶対値は 0.01 未満", "value": d, "held": abs(d) < 0.01}
    if "gteach" in runs and "shuf" in runs:
        g, s = res["arms"]["gteach"]["last_epoch_aux_ce"], res["arms"]["shuf"]["last_epoch_aux_ce"]
        res["prediction_2"] = {"text": "入れ替えた教師の腕の補助損失は、G を教師の腕より最後の epoch で大きい",
                               "gteach": g, "shuf": s, "held": (s is not None and g is not None and s > g)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("diffs", "test_overlap", "test_overlap_control_with_04", "code_identical")}
                     | {"recompute_ok": {k: v["matches"] for k, v in res["recompute"].items()}}, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
