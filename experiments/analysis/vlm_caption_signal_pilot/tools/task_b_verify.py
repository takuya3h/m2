"""Task B: 材料照合・§6.2 学習設定照合・工程塔単独 val 評価（陽性対照つき）。"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-26-vlm-caption-signal-pilot"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store")
OUT = STORE / "vlm_caption_signal_pilot" / "task_b"
OUT.mkdir(parents=True, exist_ok=True)


def mapping_digest(path: Path) -> tuple[str, int]:
    from stage2pilot.shuffle_signals import mapping_stats
    mp = json.loads(path.read_text())["mapping"]
    st = mapping_stats(mp)
    return st["mapping_sha256"], st["frames"]


def verify_materials() -> dict:
    dp_cfg = yaml.safe_load((ROOT / "experiments/phase1/stage2fix_dp_024_D2_pred_noCF_ep4_seed42/config.yaml").read_text())
    shuf_rec = json.loads((ROOT / "experiments/analysis/stage2_pilot_fix/shuffle/shuffle_record.json").read_text())
    det_ref = json.loads((ROOT / "experiments/analysis/grasp_pilot_g/caseB/identity_pred_noCF.json").read_text())

    checks = []
    file_specs = [
        ("ptower_head_ckpt", C.PT_HEAD_CKPT, dp_cfg["receiver"]["head_sha256"], "stage2fix_dp_024/config.yaml"),
        ("ptower_feat_cache", C.PT_CACHE, dp_cfg["receiver"]["cache_sha256"], "stage2fix_dp_024/config.yaml"),
        ("D0_train", C.STORE / "signals/final/D0_train.npz", dp_cfg["signals_train"][0]["sha256"], "stage2fix_dp_024/config.yaml"),
        ("D0_val", C.STORE / "signals/final/D0_val.npz", dp_cfg["signals_val"][0]["sha256"], "stage2fix_dp_024/config.yaml"),
        ("dtower_ckpt", C.DET_CKPT, det_ref["det_ckpt_sha256"], "grasp_pilot_g/caseB/identity_pred_noCF.json"),
    ]
    for name, path, expected, source in file_specs:
        actual = C.sha256(path)
        checks.append({
            "name": name, "path": str(path), "source": source,
            "expected": expected, "actual": actual, "match": actual == expected,
        })

    # P0_train / P0_val: shuffle_record.json の source_sha256 と照合
    for split in ("train", "val"):
        p0_path = C.STORE / f"signals/final/P0_{split}.npz"
        expected = shuf_rec["parts"][split]["signals"]["P0"]["source_sha256"]
        actual = C.sha256(p0_path)
        checks.append({
            "name": f"P0_{split}", "path": str(p0_path), "source": "shuffle_record.json",
            "expected": expected, "actual": actual, "match": actual == expected,
        })

    # mapping_{train,val}.json
    for split in ("train", "val"):
        mpath = C.FIX_STORE / f"signals/shuffle/mapping_{split}.json"
        expected = shuf_rec["parts"][split]["mapping_sha256"]
        actual, n_entries = mapping_digest(mpath)
        checks.append({
            "name": f"mapping_{split}", "path": str(mpath), "source": "shuffle_record.json",
            "expected": expected, "actual": actual, "match": actual == expected,
            "n_entries": n_entries,
        })

    # 陽性対照: 1 バイト変えた写しで照合が食い違いを出す
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "tampered.bin"
        raw = bytearray((C.STORE / "signals/final/D0_val.npz").read_bytes())
        raw[0] ^= 0x01
        tmp.write_bytes(bytes(raw))
        tampered_sha = C.sha256(tmp)
        expected_sha = dp_cfg["signals_val"][0]["sha256"]
        pos_ctrl = {
            "target": "D0_val.npz (1 byte flipped)",
            "expected": expected_sha,
            "actual": tampered_sha,
            "match": tampered_sha == expected_sha,
            "detected_mismatch": tampered_sha != expected_sha,
        }

    return {"checks": checks, "all_match": all(c["match"] for c in checks), "positive_control": pos_ctrl}


def extract_dp_setting(run_dir: Path) -> dict:
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    sr = cfg["stop_rule"]
    ro = cfg.get("receiver_optim")
    return {
        "run": run_dir.name,
        "type": cfg["type"],
        "scope": cfg["scope"],
        "iface_lr": sr["lr"],
        "iface_weight_decay": sr["weight_decay"],
        "receiver_lr": None if ro is None else ro["lr"],
        "receiver_weight_decay": None if ro is None else ro["weight_decay"],
        "smoothing_weight": sr["smoothing_weight"],
        "fixed_epochs": sr["fixed_epochs"],
        "lr_schedule": sr["lr_schedule"],
        "seed": cfg["seed"],
    }


def extract_pd_setting(run_dir: Path) -> dict:
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    s2 = cfg["stage2pilot"]
    return {
        "run": run_dir.name,
        "trainable": cfg["trainable"],
        "lr": cfg["lr"],
        "film_lr": cfg["film_lr"],
        "amp": cfg["amp"],
        "tf32": cfg["tf32"],
        "fixed_epochs": s2["fixed_epochs"],
        "epochs": cfg["epochs"],
        "seed": cfg["seed"],
    }


def check_consistency(groups: dict[str, list[dict]], keys: tuple[str, ...]) -> dict:
    res = {}
    all_ok = True
    for gname, rows in groups.items():
        ref = {k: rows[0][k] for k in keys}
        diffs = []
        for r in rows[1:]:
            cur = {k: r[k] for k in keys}
            if cur != ref:
                diffs.append({"run": r["run"], "expected": ref, "actual": cur})
        ok = len(diffs) == 0
        all_ok = all_ok and ok
        res[gname] = {"consistent": ok, "canonical": ref, "sources": [r["run"] for r in rows], "diffs": diffs}
    return {"all_consistent": all_ok, "groups": res}


def verify_settings() -> dict:
    p1 = ROOT / "experiments/phase1"
    dp_groups = {
        "V2P_W1": [extract_dp_setting(p1 / r) for r in (
            "stage2fix_dp_016_D1-L2_pred_noCF_ep4_seed42",
            "stage2fix_dp_024_D2_pred_noCF_ep4_seed42",
            "stage2fix_dp_023_D3-L2_pred_noCF_ep4_seed42",
        )],
        "V2P_W2": [extract_dp_setting(p1 / r) for r in (
            "w23b_dp_W2_007_D1-L2_pred_noCF_ep4_seed42",
            "w23b_dp_W2_009_D2_pred_noCF_ep4_seed42",
            "w23b_dp_W2_024_D3-L2_pred_noCF_ep4_seed42",
        )],
        "V2P_W3": [extract_dp_setting(p1 / r) for r in (
            "w23b_dp_W3_007_D1-L2_pred_noCF_ep4_seed42",
            "w23b_dp_W3_012_D2_pred_noCF_ep4_seed42",
            "w23b_dp_W3_028_D3-L2_pred_noCF_ep4_seed42",
        )],
    }
    dp_keys = ("scope", "iface_lr", "iface_weight_decay", "receiver_lr", "receiver_weight_decay",
               "smoothing_weight", "fixed_epochs", "lr_schedule", "seed")
    dp_chk = check_consistency(dp_groups, dp_keys)

    pd_groups = {
        "V2T_W1": [extract_pd_setting(p1 / r) for r in (
            "stage2fix_pd_P1-W1_pred_noCF_ep4_seed42",
            "stage2fix_pd_P2L_shuffle_ep4_seed42",
        )],
        "V2T_W2": [extract_pd_setting(p1 / r) for r in (
            "stage2fix_pd_P1-W2_empty_ep4_seed42",
            "w23b_pd_P2L-W2_pred_noCF_ep4_seed42",
        )],
        "V2T_W3": [extract_pd_setting(p1 / r) for r in (
            "w3lra_pd_P1_W3_pred_noCF_ep4_seed42",
            "w3lra_pd_P2L_W3_pred_noCF_ep4_seed42",
        )],
    }
    pd_keys = ("trainable", "lr", "film_lr", "amp", "tf32", "fixed_epochs", "epochs", "seed")
    pd_chk = check_consistency(pd_groups, pd_keys)

    # 陽性対照: 学習率を一つ変えた写しで不一致を検出
    tampered_pd = copy.deepcopy(pd_groups)
    tampered_pd["V2T_W2"][1]["lr"] = 1e-5
    pos_ctrl_pd = check_consistency(tampered_pd, pd_keys)

    tampered_dp = copy.deepcopy(dp_groups)
    tampered_dp["V2P_W2"][1]["receiver_lr"] = 1e-4
    pos_ctrl_dp = check_consistency(tampered_dp, dp_keys)

    return {
        "v2p": dp_chk,
        "v2t": pd_chk,
        "positive_controls": {
            "v2p_lr_tampered_consistent": pos_ctrl_dp["all_consistent"],
            "v2p_diffs": pos_ctrl_dp["groups"]["V2P_W2"]["diffs"],
            "v2t_lr_tampered_consistent": pos_ctrl_pd["all_consistent"],
            "v2t_diffs": pos_ctrl_pd["groups"]["V2T_W2"]["diffs"],
        },
    }


@torch.no_grad()
def eval_ptower_alone() -> dict:
    import stage1_ptower as base
    base.deterministic(42)
    names = C.phase_names()
    split = C.fold_a()
    val_videos = C.assert_no_test(split["val"], "task_b/ptower_alone")
    feats = C.load_features()
    head = C.load_ptower_head(device="cuda").eval()
    ev = PhaseEvaluator(num_classes=len(names), class_names=names)
    per_video = {}
    probs = {}
    present_idx = set()
    for video, frames, labels in C.phase_sequences(split["val"]):
        present_idx.update(int(x) for x in np.unique(labels))
        x = torch.from_numpy(np.stack([feats[f] for f in frames])).cuda()
        out = head(x.T[None])[-1][0]
        pred = out.argmax(0).cpu().numpy()
        ev.update(pred, labels, video_id=video)
        one = PhaseEvaluator(num_classes=len(names), class_names=names)
        one.update(pred, labels, video_id=video)
        r = one.compute()
        per_video[video] = {"phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"],
                            "per_class": r["phase_per_class_jaccard"]}
        probs[video] = torch.softmax(out, 0).T.cpu().numpy().astype(np.float32)
    res = ev.compute()
    pc = res["phase_per_class_jaccard"]
    present = [names[i] for i in sorted(present_idx)]
    six = [k for k in present if k != "dressing"]
    j6 = float(np.mean([pc[k] for k in six]))
    j7 = float(np.mean([pc[k] for k in present]))
    np.savez(OUT / "ptower_alone_val_probs.npz", **probs)
    out = {
        "task_id": TASK,
        "videos": val_videos,
        "phase_jaccard": res["phase_jaccard"],
        "phase_jaccard_6": j6,
        "phase_jaccard_7": j7,
        "phase_accuracy": res["phase_accuracy"],
        "phase_per_class_jaccard": pc,
        "per_video": per_video,
        "record": C.PT_RECORD,
        "diff_jaccard": res["phase_jaccard"] - C.PT_RECORD["phase_jaccard"],
        "diff_accuracy": res["phase_accuracy"] - C.PT_RECORD["phase_accuracy"],
        "within_0.005": abs(res["phase_jaccard"] - C.PT_RECORD["phase_jaccard"]) <= 0.005,
    }
    return out


def main():
    mats = verify_materials()
    sets = verify_settings()
    pt = eval_ptower_alone()
    C.write_json(OUT / "materials.json", mats)
    C.write_json(OUT / "settings.json", sets)
    C.write_json(OUT / "ptower_alone.json", pt)
    print(json.dumps({
        "materials_all_match": mats["all_match"],
        "materials_pos_ctrl_detected": mats["positive_control"]["detected_mismatch"],
        "v2p_settings_consistent": sets["v2p"]["all_consistent"],
        "v2t_settings_consistent": sets["v2t"]["all_consistent"],
        "settings_pos_ctrl_detected": (not sets["positive_controls"]["v2p_lr_tampered_consistent"]
                                       and not sets["positive_controls"]["v2t_lr_tampered_consistent"]),
        "ptower_jaccard": pt["phase_jaccard"],
        "ptower_jaccard_6": pt["phase_jaccard_6"],
        "ptower_accuracy": pt["phase_accuracy"],
        "ptower_diff_jaccard": pt["diff_jaccard"],
        "ptower_within_0.005": pt["within_0.005"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
