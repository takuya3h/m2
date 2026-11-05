"""Task E: SPEC §6.1 の形で values.json を書く。値はすべて記録のファイルから読む。読めない欄は理由つきの UNKNOWN。

    python build_values.py            # values.json を書き、欠けの検査を回す
    python build_values.py --check    # 既存の values.json の欠けの検査だけ
    python build_values.py --selftest # キーを一つ消した写しが検査で欠けとして出ることを示す（完了判定 d の対照）
"""
from __future__ import annotations

import copy
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = "T-2026-11-02-hostdiff-bengio"
SCR = Path.home() / "m2-scratch" / TASK
OUT = ROOT / "experiments/analysis/hostdiff_andrew_bengio/bengio"
PHASE_PUB = ROOT / "experiments/phase1/stage1_ptower_hostdiff_bengio"
DET_PUB = ROOT / "experiments/baselines/stage1_dtower_hostdiff_bengio"
# 手本の 003〜012 の順（run_stage1_ptower_r3.heads() の順）
HEADS = ["A_L6_w0.0_h30", "A_L8_w0.0_h30", "B_L6_w0.0_h30", "B_L6_w0.0_h60", "C_L6_w0.15_h30",
         "C_L6_w0.3_h30", "B_L8_w0.0_h30", "B_L8_w0.0_h60", "C_L8_w0.15_h30", "C_L8_w0.3_h30"]
DET_RUNS = {"seed42a": ("42a", 42), "seed42b": ("42b", 42), "seed123": ("123", 123)}
GPU_FIELDS = ["power.draw", "clocks.sm", "clocks.mem", "utilization.gpu", "memory.used", "temperature.gpu"]
SKIP_STEPS = 50

PHASE_KEYS = ["J_heads", "J_mean", "J_max", "backbone_val_frame_acc", "lr_drop_epoch", "stop_epoch",
              "checkpoint_epoch", "cap_reached", "coco_loaded", "timing", "gpu", "foreign_gpu_use"]
DET_KEYS = ["mAP", "AP_signature", "AP_negative", "AP50", "lr_drop_epoch", "stop_epoch", "checkpoint_epoch",
            "cap_reached", "coco_loaded", "timing", "gpu", "foreign_gpu_use"]
TIMING_KEYS = ["wall_s", "train_s_per_epoch", "s_per_step_median", "eval_s"]
REQUIRED = {"": ["host", "task_id", "code_commit", "env", "determinism_check", "phase", "detector"],
            "phase": ["seed42", "seed123"], "detector": list(DET_RUNS)}


def unknown(reason):
    return f"UNKNOWN ({reason})"


def load(path):
    return json.loads(Path(path).read_text())


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def med(xs):
    return statistics.median(xs) if xs else unknown("標本なし")


def events(run):
    f = SCR / f"events_{run}.json"
    return load(f) if f.exists() else []


def window(evs, tag):
    s = next((e["t_mono"] for e in evs if e["kind"] == "start" and e["tag"] == tag), None)
    e = next((e["t_mono"] for e in evs if e["kind"] == "end" and e["tag"] == tag), None)
    return s, e


def gpu_summary(path, t0, t1):
    rows = [r for r in jsonl(path) if "gpus" in r and t0 <= r["t_mono"] <= t1]
    out = {"window": "学習のプロセスの起動から終わりまで", "n_samples": len(rows), "per_gpu": {}}
    for idx in sorted({g["index"] for r in rows for g in r["gpus"]}):
        stats = {}
        for f in GPU_FIELDS:
            xs = [float(g[f]) for r in rows for g in r["gpus"] if g["index"] == idx and g.get(f) not in (None, "", "[N/A]")]
            stats[f] = {"mean": statistics.fmean(xs), "median": statistics.median(xs)} if xs else unknown("標本なし")
        out["per_gpu"][idx] = stats
    return out


def foreign_intervals(path):
    """本契約以外のプロセスが GPU にいた標本を、続く標本ごとに区間へまとめる（標本の間隔は 10 秒）。"""
    spans, cur = [], None
    for r in jsonl(path):
        if "gpus" not in r:
            continue
        if r.get("foreign"):
            if cur is None:
                cur = {"start_utc": r["t_utc"], "end_utc": r["t_utc"], "n_samples": 0, "processes": []}
                spans.append(cur)
            cur["end_utc"] = r["t_utc"]
            cur["n_samples"] += 1
            for p in r["foreign"]:
                if p not in cur["processes"]:
                    cur["processes"].append(p)
        else:
            cur = None
    return spans


def diffs_after(ts, skip):
    ts = sorted(ts)
    return [b - a for a, b in zip(ts[skip:], ts[skip + 1:])]


def phase_timing(work, evs):
    rows = jsonl(work / "steps/finetune_steps_rank0.jsonl")
    # epoch の境: 学習の区間は直前の val_end（初回は最初の記録）から val_start まで
    epochs, seg, micro_d, opt_d = [], [], [], []
    vals = []
    last_val_end = None
    for r in rows:
        if r["event"] == "val_start":
            if seg:
                start = last_val_end if last_val_end is not None else seg[0]["t"]
                epochs.append(r["t"] - start)
            micro = [x["t"] for x in seg if x["event"] == "micro"]
            opt = [x["t"] for x in seg if x["event"] == "optimizer"]
            micro_d.append(micro)
            opt_d.append(opt)
            seg = []
            vstart = r["t"]
        elif r["event"] == "val_end":
            vals.append(r["t"] - vstart)
            last_val_end = r["t"]
        else:
            seg.append(r)
    # 最初の 50 歩を除く: run の通しの番号で数え、val をまたぐ差は数えない
    def per_step(groups):
        out, n = [], 0
        for g in groups:
            g = sorted(g)
            for a, b in zip(g, g[1:]):
                n += 1
                if n > SKIP_STEPS:
                    out.append(b - a)
        return out
    t = load(work / "timing.json")
    return {
        "wall_s": t["wall_s"],
        "train_s_per_epoch": {"per_epoch": epochs, "median": med(epochs),
                              "definition": "rank0 の直前の val の終わり（初回は最初の micro-step）から val の始めまで"},
        "s_per_step_median": {"micro_step": med(per_step(micro_d)), "optimizer_step": med(per_step(opt_d)),
                              "definition": f"rank0、隣り合う記録の時刻の差、最初の {SKIP_STEPS} 歩を除く、val をまたぐ差は除く"},
        "eval_s": {"val_per_epoch": vals, "val_per_epoch_median": med(vals), "train_records_s": t["finetune_records_s"]},
        "finetune_s": t["finetune_s"], "features_s": t["features_s"], "heads_s": t["heads_s"], "head_s": t["head_s"],
    }


def phase_run(seed):
    run = f"phase{seed}"
    work = SCR / "phase" / f"seed{seed}"
    ft = PHASE_PUB / f"stage1_ptower_search_001_ft_coco_lr0.0001_foldA_point00_seed{seed}"
    if not (ft / "metrics.json").exists():
        return {k: unknown(f"{run} が未完了") for k in PHASE_KEYS}
    m = load(ft / "metrics.json")
    J = [load(PHASE_PUB / f"stage1_ptower_search_001_P15_{h}_foldA_point00_seed{seed}/metrics.json")["phase_jaccard"]
         for h in HEADS]
    log = (work / "finetune.log").read_text()
    coco = re.findall(r"load pretrained COCO backbone \S+ sha256=([0-9a-f]+)", log)
    evs = events(run)
    t0, t1 = window(evs, f"{run}_finetune")
    return {
        "J_heads": J, "J_heads_order": HEADS, "J_mean": statistics.fmean(J), "J_max": max(J),
        "backbone_val_frame_acc": m["phase_accuracy"], "backbone_val_macro_jaccard": m["phase_jaccard"],
        "lr_drop_epoch": m.get("lr_lowered_epoch"), "stop_epoch": m.get("early_stopped_epoch"),
        "checkpoint_epoch": m["epoch"], "epochs_completed": m["epochs_completed"],
        "epoch_numbering": "1 起点（学習の記録の epoch=）",
        "cap_reached": m["reached_epoch_cap"],
        "coco_loaded": {"value": len(coco) == 2, "sha256": sorted(set(coco)), "lines": len(coco)},
        "head_epochs": {h: {"checkpoint_epoch": d["epoch"], "epochs_completed": d["epochs_completed"]}
                        for h in HEADS
                        for d in [load(PHASE_PUB / f"stage1_ptower_search_001_P15_{h}_foldA_point00_seed{seed}/metrics.json")]},
        "timing": phase_timing(work, evs),
        "gpu": gpu_summary(work / "gpu.jsonl", t0, t1),
        "foreign_gpu_use": foreign_intervals(work / "gpu.jsonl"),
    }


def det_timing(work):
    rows = jsonl(work / "steps/detector_steps_rank0.jsonl")
    starts = {r["epoch"]: r["t"] for r in rows if r["event"] == "epoch_start"}
    ends = {r["epoch"]: r["t"] for r in rows if r["event"] == "epoch_end"}
    per_epoch = [ends[e] - starts[e] for e in sorted(ends) if e in starts]
    between = [starts[e + 1] - ends[e] for e in sorted(ends) if e + 1 in starts]
    clips = {}
    for r in rows:
        if r["event"] == "clip":
            clips.setdefault(r["epoch"], []).append(r["t"])
    n, d = 0, []
    for e in sorted(clips):
        g = sorted(clips[e])
        for a, b in zip(g, g[1:]):
            n += 1
            if n > SKIP_STEPS:
                d.append(b - a)
    t = load(work / "timing.json")
    return {
        "wall_s": t["wall_s"],
        "train_s_per_epoch": {"per_epoch": per_epoch, "median": med(per_epoch),
                              "definition": "rank0 の epoch の始めから終わりまで（val は epoch の外）"},
        "s_per_step_median": {"optimizer_step": med(d),
                              "definition": f"rank0、勾配のクリップの記録（一歩に一度）の時刻の差、最初の {SKIP_STEPS} 歩を除く、epoch をまたぐ差は除く"},
        "eval_s": {"between_epochs": between, "between_epochs_median": med(between),
                   "between_epochs_definition": "epoch の終わりから次の始めまで（学習中の val と checkpoint の保存を含む）",
                   "final_val_s": t["eval_val_s"], "final_train_s": t["eval_train_s"]},
        "train_s": t["train_s"],
    }


def det_run(key):
    label, seed = DET_RUNS[key]
    run = f"det{label}"
    work = SCR / "detector" / label
    pub = DET_PUB / f"{label}_dcoco_foldA_seed{seed}"
    if not (pub / "metrics.json").exists():
        return {k: unknown(f"{run} が未完了") for k in DET_KEYS}
    m = load(pub / "metrics.json")
    conv = load(pub / "convergence.json")
    ev = load(work / "eval_val.json")
    init = load(work / "initialization_rank0.json")
    evs = events(run)
    t0, t1 = window(evs, label)
    return {
        "mAP": m["mAP"], "AP_signature": m["AP_target"], "AP_negative": m["AP_negative"], "AP50": ev["AP50"],
        "AP75": ev["AP75"], "train_mAP": m["train_mAP"],
        "lr_drop_epoch": conv["decayed_epoch"], "stop_epoch": conv["stopped_epoch"],
        "checkpoint_epoch": conv["best_epoch"], "epochs_completed": conv["observed_epochs"],
        "epoch_numbering": "0 起点（convergence.json）",
        "val_ap_per_epoch": conv["val_ap_per_epoch"],
        "cap_reached": m["reached_epoch_cap"],
        "coco_loaded": {"value": init.get("matched") is True,
                        "source": "initialization_rank0.json の matched",
                        "detail": {k: v for k, v in init.items() if not isinstance(v, (dict, list))}},
        "timing": det_timing(work),
        "gpu": gpu_summary(work / "gpu.jsonl", t0, t1),
        "foreign_gpu_use": foreign_intervals(work / "gpu.jsonl"),
    }


def env():
    static = load(OUT / "a_env_static.json")
    runtime = {}
    for name, f in [("phase_seed42", SCR / "phase/seed42/finetune_optimizer_rank0.json"),
                    ("phase_seed123", SCR / "phase/seed123/finetune_optimizer_rank0.json"),
                    ("detector_42a", SCR / "detector/42a/optimizer_rank0.json"),
                    ("detector_42b", SCR / "detector/42b/optimizer_rank0.json"),
                    ("detector_123", SCR / "detector/123/optimizer_rank0.json")]:
        if f.exists():
            d = load(f)
            runtime[name] = {"runtime": d.get("runtime"), **({"autocast": d["autocast"]} if "autocast" in d else {})}
        else:
            runtime[name] = unknown("記録なし（run が未完了）")
    smi = static["nvidia_smi"][0].split(", ")
    nccl = sorted({line for f in SCR.glob("*/**/*.command.sh") for line in f.read_text().splitlines()
                   if "NCCL_P2P_DISABLE" in line})
    return {
        "driver": smi[2], "cuda_runtime": static["body"]["cuda_runtime"], "cudnn": static["body"]["cudnn"],
        "nccl": static["body"]["nccl"], "torch": static["body"]["torch"], "torchvision": static["body"]["torchvision"],
        "accelerate": {"body": static["body"]["accelerate"], "detector": static["detector"]["accelerate"]},
        "image_decode": {"backend": static["body"]["torchvision_image_backend"], "PIL": static["body"]["PIL"],
                         "libjpeg_turbo": static["body"]["pil_libjpeg_turbo"], "jpg_version": static["body"]["pil_jpg_version"]},
        "tf32_default": {"matmul": static["body"]["tf32_matmul_default"], "cudnn": static["body"]["tf32_cudnn_default"]},
        "NCCL_P2P_DISABLE": nccl,
        "power_limit": {"enforced": smi[3], "default": smi[4], "max": smi[5]},
        "process_runtime": runtime,
        "static_source": "a_env_static.json",
    }


def build():
    commit = subprocess.run(["git", "-C", str(ROOT), "--no-pager", "log", "-1", "--format=%H"],
                            capture_output=True, text=True, check=True).stdout.strip()
    per_run = {p.parent.name: p.read_text().strip()
               for p in sorted(list(PHASE_PUB.glob("*/git_commit.txt")) + list(DET_PUB.glob("*/git_commit.txt")))}
    det = load(OUT / "b_determinism.json")
    return {
        "host": "bengio", "task_id": TASK,
        "code_commit": {"code": "22ce24b268f29563857b11ddab325e45076ec074",
                        "note": ("phase42 の backbone（14:00:17 UTC 起動）は起動時の HEAD 8aefdce3 を記録した。道具の変更は起動前"
                                 "（最後の変更 13:59:16 UTC）に作業ツリーにあり、14:01:26 UTC に 22ce24b2 として commit した。"
                                 "5 本とも 22ce24b2 の内容で動いた"),
                        "merge_note": ("5 本の後に origin/phase0（#286 hostdiff-andrew の統合後、89fe4a41）を分岐へ取り込んだ（c518bf6d）。"
                                       "scripts/run_ptower_search.py・tower_search_common.py・train_relation_detr_search.py は phase0 の版を採った。"
                                       "分岐の先頭の scripts/ は run が使った版ではない。run が使った版は 22ce24b2"),
                        "recorded_per_run": per_run, "values_built_at": commit},
        "env": env(),
        "determinism_check": {"identical": det["identical"],
                              "per_rank": {r: {"sha256": v["sha256"][0], "micro_steps": v["micro_steps"][0],
                                               "optimizer_steps": v["optimizer_steps"][0], "identical": v["identical"]}
                                           for r, v in det["per_rank"].items()},
                              "source": "b_determinism.json"},
        "phase": {"seed42": phase_run(42), "seed123": phase_run(123)},
        "detector": {k: det_run(k) for k in DET_RUNS},
    }


def missing(v):
    out = [f"/{k}" for k in REQUIRED[""] if k not in v]
    for top in ("phase", "detector"):
        for k in REQUIRED[top]:
            run = v.get(top, {}).get(k)
            if run is None:
                out.append(f"/{top}/{k}")
                continue
            for key in (PHASE_KEYS if top == "phase" else DET_KEYS):
                if key not in run:
                    out.append(f"/{top}/{k}/{key}")
            if isinstance(run.get("timing"), dict):
                extra = ["features_s", "heads_s"] if top == "phase" else []
                out += [f"/{top}/{k}/timing/{t}" for t in TIMING_KEYS + extra if t not in run["timing"]]
    return out


def main():
    if "--selftest" in sys.argv:
        v = load(OUT / "values.json")
        broken = copy.deepcopy(v)
        del broken["detector"]["seed42b"]["AP50"]
        print(json.dumps({"intact_missing": missing(v), "broken_missing": missing(broken)}, ensure_ascii=False))
        return
    if "--check" not in sys.argv:
        (OUT / "values.json").write_text(json.dumps(build(), ensure_ascii=False, indent=1))
    v = load(OUT / "values.json")
    gaps = missing(v)
    unk = re.findall(r'"([^"]+)": "UNKNOWN \(([^)]*)\)"', (OUT / "values.json").read_text())
    print(json.dumps({"missing": gaps, "unknown": unk}, ensure_ascii=False, indent=1))
    sys.exit(1 if gaps else 0)


if __name__ == "__main__":
    main()
