"""Task B-1 / B-2: 前回の材料の在否と要約値の照合（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）。

前回（T-2026-10-18-stage2-pilot-folda）の信号・腕の信号・run の epoch ごとの記録を読むだけで調べる。書き込みは --out と
--flip-dir（陽性対照の複製）だけ。

- 確定塔の信号: 実体の sha256 を、前回の記録（工程は版管理下の record_phase_*.json、検出は STORE の record_*.json）と、
  DP の run の config.yaml に残る sha256 の両方と比べる
- 交差適合版の train の信号: DP の run の config.yaml（検出）と合わせ込みのログ（工程）の sha256 と比べ、加えて半分ずつの
  信号（sha256 は版管理下の crossfit/record_*_from_H*.json と比べる）から中身を組み直して突き合わせる
- PD の正解予測の腕の信号: 合わせ込みのログの sha256 と比べ、元の信号から連結し直して中身を突き合わせる
- DP の run の logs/history.json と、PD の run の logs/val_metrics_by_epoch.json の 4 epoch 目の行の在否

    python scripts/stage2pilot/material_check.py --out <json> [--flip-dir <dir>] [--count-run <名前> ...]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402

OLD = C.STORE
FINAL = OLD / "signals/final"
CF = OLD / "signals/cf"
CROSS = C.ANALYSIS / "crossfit"
PHASE_SIGS = ("P0", "P-GT")
DET_SIGS = ("D0", "D-GT", "D0-RT", "D0-INST-UQ", "D-GT-INST")
CF_DET = ("D0", "D0-RT", "D0-INST-UQ")
MERGE_LOG = OLD / "queues/cf_ptower_merge.log"
AUDIT_PREFIX = {"P0": "e7b23991"}          # 前回の audit.md の E-6 の続き（合わせ込み）に書いた先頭 8 桁


def by_frame(path):
    with np.load(path) as d:
        x = d["x"]
        cnt = d["count"] if "count" in d else None
        ids = [str(f) for f in d["frame_ids"]]
    return {f: (x[i], None if cnt is None else cnt[i]) for i, f in enumerate(ids)}


def same_content(a: dict, b: dict) -> dict:
    """フレーム名で引いた二つの信号が、フレームの集合も値も同じか。"""
    if set(a) != set(b):
        return {"same": False, "frames_only_in_one": len(set(a) ^ set(b))}
    bad = sum(1 for f in a if not (np.array_equal(a[f][0], b[f][0])
                                   and (a[f][1] is None) == (b[f][1] is None)
                                   and (a[f][1] is None or a[f][1] == b[f][1])))
    return {"same": bad == 0, "frames": len(a), "frames_differ": bad}


def config_digests():
    """DP の run の config.yaml に残る信号の経路 → sha256 の集合。"""
    out = {}
    for p in sorted((C.ROOT / "experiments/phase1").glob("stage2pilot_dp_*/config.yaml")):
        cfg = yaml.safe_load(p.read_text())
        for key in ("signals_train", "signals_val"):
            for f in cfg.get(key) or []:
                out.setdefault(f["path"], set()).add(f["sha256"])
    return out


def merge_log_digests():
    out = {}
    for line in MERGE_LOG.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            out[parts[1]] = parts[0]
    return out


def check_signals():
    cfgd = config_digests()
    logd = merge_log_digests()
    rows = []

    def row(name, part, path, recorded: dict):
        r = {"signal": name, "part": part, "path": str(path), "exists": path.exists()}
        if path.exists():
            r["sha256"] = C.sha256(path)
            r["recorded"] = recorded
            r["match"] = all(v == r["sha256"] for v in recorded.values()) and bool(recorded)
        rows.append(r)
        return r

    for part in ("train", "val"):
        rec_p = json.loads((C.ANALYSIS / f"signals/record_phase_{part}.json").read_text())["files"]
        rec_d = json.loads((FINAL / f"record_{part}.json").read_text())["files"]
        for s in PHASE_SIGS:
            p = FINAL / f"{s}_{part}.npz"
            row(s, part, p, {"record_phase": rec_p[s]["sha256"]})
        for s in DET_SIGS:
            p = FINAL / f"{s}_{part}.npz"
            rec = {"record_det": rec_d[s]["sha256"]}
            for i, d in enumerate(sorted(cfgd.get(str(p), set()))):
                rec[f"dp_config_{i}"] = d
            row(s, part, p, rec)
    # 交差適合版の train
    for s in CF_DET:
        p = CF / f"{s}_train.npz"
        rec = {f"dp_config_{i}": d for i, d in enumerate(sorted(cfgd.get(str(p), set())))}
        r = row(f"{s}（交差適合版）", "train", p, rec)
        halves = []
        for h in ("H1", "H2"):
            hp = OLD / f"signals/cf_det_from_{h}/{s}_train.npz"
            hrec = json.loads((CROSS / f"record_det_from_{h}.json").read_text())["files"][s]["sha256"]
            halves.append({"half": h, "sha256": C.sha256(hp), "recorded": hrec, "match": C.sha256(hp) == hrec})
            hd = by_frame(hp)
            r.setdefault("_merged", {}).update(hd)
        r["halves"] = halves
        r["rebuilt_from_halves"] = same_content(r.pop("_merged"), by_frame(p))
    p = CF / "P0_train.npz"
    r = row("P0（交差適合版）", "train", p, {"merge_log": logd.get(str(p))})
    r["audit_prefix_match"] = r["sha256"].startswith(AUDIT_PREFIX["P0"])
    merged, halves = {}, []
    for h in ("H1", "H2"):
        hp = OLD / f"signals/cf_phase_from_{h}/P0_train.npz"
        hrec = json.loads((CROSS / f"record_phase_from_{h}.json").read_text())["files"]["P0"]["sha256"]
        halves.append({"half": h, "sha256": C.sha256(hp), "recorded": hrec, "match": C.sha256(hp) == hrec})
        merged.update(by_frame(hp))
    r["halves"] = halves
    r["rebuilt_from_halves"] = same_content(merged, by_frame(p))
    # PD の正解予測の腕（正解が先）
    for name, gt, pred in (("gtpred_CF_train", FINAL / "P-GT_train.npz", CF / "P0_train.npz"),
                           ("gtpred_noCF_val", FINAL / "P-GT_val.npz", FINAL / "P0_val.npz")):
        p = OLD / f"arms/PD/{name}.npz"
        rec = {"merge_log": logd[str(p)]} if str(p) in logd else {}
        r = row(f"PD {name}", name.rsplit("_", 1)[1], p, rec)
        if not rec:
            r["match"] = None
            r["note"] = "前回の記録に sha256 が無い。中身の組み直しだけで確かめる"
        g, q = by_frame(gt), by_frame(pred)
        rebuilt = {f: (np.concatenate([g[f][0], q[f][0]]).astype(np.float32), None) for f in g}
        r["rebuilt_from_sources"] = same_content(rebuilt, by_frame(p))
    return rows


def check_histories(extra_names):
    dp, missing, no_ep4 = [], [], []
    for d in sorted((C.ROOT / "experiments/phase1").glob("stage2pilot_dp_*_seed*")):
        cfgp = d / "config.yaml"
        if not cfgp.exists() or yaml.safe_load(cfgp.read_text()).get("smoke"):
            continue
        dp.append(d.name)
        h = d / "logs/history.json"
        if not h.exists():
            missing.append(d.name)
        elif not any(r.get("epoch") == 4 for r in json.loads(h.read_text())):
            no_ep4.append(d.name)
    pd = {}
    for d in sorted((C.ROOT / "experiments/phase1").glob("stage2pilot_pd_*_seed42")):
        f = d / "logs/val_metrics_by_epoch.json"
        res = next((p for p in (d / "t1b_result.json", d / "cap_result.json") if p.exists()), None)
        best = json.loads(res.read_text())["best_epoch"] if res else None
        if not f.exists():
            pd[d.name] = {"by_epoch_file": False, "epoch3": False, "best_epoch": best}
            continue
        ep = {e["epoch"]: e for e in json.loads(f.read_text())["epochs_eval"]}
        pd[d.name] = {"by_epoch_file": True, "epoch3": 3 in ep and bool(ep[3].get("per_class_coco_map")),
                      "epochs": sorted(ep), "best_epoch": best}
    counted = {n: sum(1 for _ in (C.ROOT / "experiments/phase1").glob(f"{n}/logs/history.json")) for n in extra_names}
    return {"dp_runs": len(dp), "dp_with_history": len(dp) - len(missing), "dp_missing_history": missing,
            "dp_without_epoch4": no_ep4, "pd": pd, "count_named_runs": counted}


def flip_control(rows, flip_dir):
    """陽性対照: 信号の一つを 1 バイト変えた複製の sha256 が記録と一致しなくなるか。"""
    src = FINAL / "D0_val.npz"
    dst = Path(flip_dir) / "D0_val_flipped.npz"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    with dst.open("r+b") as f:
        f.seek(-100, 2)
        b = f.read(1)
        f.seek(-100, 2)
        f.write(bytes([b[0] ^ 0xFF]))
    rec = next(r for r in rows if r["signal"] == "D0" and r["part"] == "val")
    got = C.sha256(dst)
    return {"copy": str(dst), "sha256": got, "recorded": rec["recorded"]["record_det"],
            "match": got == rec["recorded"]["record_det"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--flip-dir", default=None)
    ap.add_argument("--count-run", nargs="*", default=[])
    a = ap.parse_args()
    rows = check_signals()
    res = {"task_id": C.FIX_TASK_ID, "signals": rows,
           "all_exist": all(r["exists"] for r in rows),
           "all_recorded_match": all(r.get("match") is not False for r in rows),
           "histories": check_histories(a.count_run)}
    if a.flip_dir:
        res["flip_control"] = flip_control(rows, a.flip_dir)
    C.write_json(a.out, res)
    for r in rows:
        extra = ""
        if "rebuilt_from_halves" in r:
            extra = f" 半分の記録一致 {[h['match'] for h in r['halves']]} 組み直し {r['rebuilt_from_halves']}"
        if "rebuilt_from_sources" in r:
            extra = f" 組み直し {r['rebuilt_from_sources']}"
        print(f"{r['signal']:<24} {r['part']:<5} 在る {r['exists']} 一致 {r.get('match')} "
              f"照合先 {sorted(r.get('recorded', {}))}{extra}")
    h = res["histories"]
    print(f"DP {h['dp_runs']} 本、history.json 在る {h['dp_with_history']}、無い {h['dp_missing_history']}、"
          f"epoch 4 の行が無い {h['dp_without_epoch4']}、名指しの数え {h['count_named_runs']}")
    for n, v in h["pd"].items():
        print(f"PD {n}: 記録 {v['by_epoch_file']} epoch3 {v['epoch3']} 最良 {v['best_epoch']}")
    if a.flip_dir:
        print(f"陽性対照（1 バイト変えた複製）: 一致 {res['flip_control']['match']}")
    print(f"全件在る {res['all_exist']}、記録と全件一致 {res['all_recorded_match']}")


if __name__ == "__main__":
    main()
