"""Task B-1・B-2（T-2026-11-09-grasp-roitoken-transition-pilot）。本体の .venv。学習しない。

B-1 目録の G の見取り（B_m の pred_noCF・pred_CF・shuffle・shuffle_CF の train/val。見取りの json と地図の npy）と
    P の重み（fine-tune の checkpoint・時間ヘッド）・特徴のキャッシュの sha256 を記録の値と照合する。
    対照: 1 バイト変えた写し（小さい見取りの json を写して 1 バイト反転）で不一致になる。
B-2 塔単独（時間ヘッドだけ、キャッシュの特徴）の val の macro Jaccard と accuracy を記録（common.PT_RECORD）と比べる（差 1e-6 以内）。
    対照: 別 seed の塔（runindex の stage1_ptower_r3 seed 123 の記録）の値との差は許容差を超える。

    .venv/bin/python b12_inputs.py --out <S>/b/b12.json
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from stage2pilot import common as C  # noqa: E402

MANIFEST = ROOT / "experiments/analysis/grasp_tower_rebuild/signals_manifest.json"
P_FT = ROOT / "experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42/checkpoints/best.pth"
# 記録の値: fine-tune は T-2026-11-08 audit 102 行（キャッシュを作った run の checkpoint_sha256）、
# 時間ヘッドとキャッシュは四本目の run の config（grasparms_dp_001_GA-noflag_empty_ep4_seed42/config.yaml 15・17 行）
REC = {
    "P_ft": "79c2c4782458c981b347e424a7b27dd81166e9721317d6dc569e8d92241acf6b",
    "P_head": "0d76d446796f855a51640d756d6d3436573ff40ed600915980021c5f4cc6ad6d",
    "P_cache": "c402e214d28d32c68b396fe84bbefefffdf7577d9550c421364543af78f172da",
}
ARMS = ("pred_noCF_train", "pred_noCF_val", "pred_CF_train", "pred_CF_val",
        "shuffle_train", "shuffle_val", "shuffle_CF_train", "shuffle_CF_val")
TOL = 1e-6


def check_inputs(scratch):
    man = json.loads(MANIFEST.read_text())
    rows, digests = [], {}
    for arm in ARMS:
        e = man["B_m"][arm]
        for kind in ("view", "maps"):
            path = e[kind]
            want = e[f"{kind}_sha256"]
            got = digests.get(path) or C.sha256(path)
            digests[path] = got
            rows.append({"item": f"B_m.{arm}.{kind}", "path": path, "want": want, "got": got, "match": got == want})
    for key, path in (("P_ft", P_FT), ("P_head", C.PT_HEAD_CKPT), ("P_cache", C.PT_CACHE)):
        got = C.sha256(path)
        rows.append({"item": key, "path": str(path), "want": REC[key], "got": got, "match": got == REC[key]})
    # 対照: 1 バイト変えた写し
    src = Path(man["B_m"]["pred_noCF_val"]["view"])
    copy = Path(scratch) / "view_flipped.json"
    copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, copy)
    data = bytearray(copy.read_bytes())
    data[100] ^= 0x01
    copy.write_bytes(bytes(data))
    flipped = C.sha256(copy)
    control = {"source": str(src), "copy": str(copy), "byte_flipped": 100, "sha256": flipped,
               "want": man["B_m"]["pred_noCF_val"]["view_sha256"],
               "match": flipped == man["B_m"]["pred_noCF_val"]["view_sha256"]}
    copy.unlink()
    return rows, control


def tower_alone():
    import torch

    from egosurgery.metrics.phase import PhaseEvaluator
    import stage1_ptower as base
    base.deterministic(42)
    names = C.phase_names()
    split = C.fold_a()
    videos = C.assert_no_test(split["val"], "b12 tower")
    feats = C.load_features()
    head = C.load_ptower_head(device="cuda")
    ev = PhaseEvaluator(num_classes=len(names), class_names=names)
    with torch.no_grad():
        for video, frames, labels in C.phase_sequences(split["val"]):
            x = torch.from_numpy(np.stack([feats[f] for f in frames])).cuda()
            pred = head(x.T[None])[-1][0].argmax(0).cpu().numpy()
            ev.update(pred, labels, video_id=video)
    r = ev.compute()
    dj = r["phase_jaccard"] - C.PT_RECORD["phase_jaccard"]
    da = r["phase_accuracy"] - C.PT_RECORD["phase_accuracy"]
    other = next(row for row in csv.DictReader((ROOT / "runindex/index.csv").open())
                 if row["path"].endswith("stage1_ptower_r3_064_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed123"))
    oj, oa = float(other["metric.jaccard"]), float(other["metric.accuracy"])
    return {"videos": videos, "phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"],
            "per_class_jaccard": r["phase_per_class_jaccard"], "record": C.PT_RECORD,
            "diff_jaccard": dj, "diff_accuracy": da, "tolerance": TOL,
            "within_tolerance": abs(dj) <= TOL and abs(da) <= TOL,
            "control_other_seed": {"path": other["path"], "seed": other["seed"], "jaccard": oj, "accuracy": oa,
                                   "diff_jaccard": r["phase_jaccard"] - oj, "diff_accuracy": r["phase_accuracy"] - oa,
                                   "within_tolerance": abs(r["phase_jaccard"] - oj) <= TOL and abs(r["phase_accuracy"] - oa) <= TOL}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows, control = check_inputs(Path(a.out).parent / "scratch")
    tower = tower_alone()
    out = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "inputs": rows,
           "inputs_all_match": all(r["match"] for r in rows), "n_inputs": len(rows),
           "n_match": sum(r["match"] for r in rows), "control_flipped_copy": control, "tower_alone_val": tower}
    C.write_json(a.out, out)
    print(json.dumps({k: v for k, v in out.items() if k != "inputs"}, ensure_ascii=False, indent=1))
    for r in rows:
        print(r["item"], r["match"], r["got"][:16])


if __name__ == "__main__":
    main()
