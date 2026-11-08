"""S7 費用の単価。前の契約の run の記録だけを読む（GPU は使わない）。T-2026-11-08-grasp-cards-survey。

各行は run の記録の中の値（metrics.json の elapsed_seconds、または start.txt と end.txt の差）から作り、
出所の経路を付ける。五本目（T-2026-11-06-grasp-pilot-d-rerun）は phase0 に未統合なので、
遠隔の分岐 origin/feat/grasp-pilot-d-rerun の版から git show で読む（作業ツリーの写しは使わない）。
同じ組の run の壁時計の区間が重なる数（同時に走った本数の最大）も記録から数える。

    python s7_costs.py --out <json>
"""
from __future__ import annotations

import argparse
import glob
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
P1 = "experiments/phase1"
REF5 = "origin/feat/grasp-pilot-d-rerun"
HOSTDIFF = "/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/phase/seed42"


def read(path, ref=None):
    if ref:
        r = subprocess.run(["git", "--no-pager", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    p = Path(path) if path.startswith("/") else ROOT / path
    return p.read_text() if p.exists() else None


def ts(text):
    return datetime.strptime(text.strip().replace(" UTC", ""), "%Y-%m-%d %H:%M:%S")


def run_row(run, ref=None):
    base = f"{P1}/{run}"
    row = {"run": run, "source": (f"{ref}:" if ref else "") + base}
    m = read(f"{base}/metrics.json", ref)
    if m:
        d = json.loads(m)
        if "elapsed_seconds" in d:
            row["elapsed_seconds"] = d["elapsed_seconds"]
            row["elapsed_from"] = "metrics.json:elapsed_seconds"
    s, e = read(f"{base}/start.txt", ref), read(f"{base}/end.txt", ref)
    if s and e:
        row["start_utc"], row["end_utc"] = s.strip(), e.strip()
        row["wall_seconds"] = (ts(e) - ts(s)).total_seconds()
        row["wall_from"] = "start.txt / end.txt"
    srv = read(f"{base}/server.txt", ref)
    row["server"] = srv.strip() if srv else None
    return row


def overlap(rows):
    iv = [(ts(r["start_utc"]), ts(r["end_utc"])) for r in rows if "start_utc" in r]
    if not iv:
        return None
    pts = sorted([(a, 1) for a, _ in iv] + [(b, -1) for _, b in iv], key=lambda x: (x[0], x[1]))
    cur = best = 0
    for _, k in pts:
        cur += k
        best = max(best, cur)
    return best


def summary(rows, key):
    v = [r[key] for r in rows if key in r]
    return {"n": len(v), "min": min(v), "max": max(v)} if v else None


def names(pattern, ref=None):
    if ref:
        r = subprocess.run(["git", "--no-pager", "ls-tree", "-d", "--name-only", f"{ref}:{P1}"], cwd=ROOT,
                           capture_output=True, text=True, check=True)
        import fnmatch
        return sorted(n for n in r.stdout.split() if fnmatch.fnmatch(n, pattern))
    return sorted(Path(p).name for p in glob.glob(str(ROOT / P1 / pattern)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    groups = {
        "phase_iface_W1_fourth": {"runs": [run_row(n) for n in names("grasparms_dp_00*_GA-noflag_*_ep4_seed42")],
                                  "contract": "T-2026-11-06-grasp-pilot-arms（四本目）"},
        "phase_head_W2_GA": {"runs": [run_row(n) for n in names("w23b_dp_W2_*_GA_*_ep4_seed42")],
                             "contract": "T-2026-11-01-stage2-w23-bengio"},
        "phase_head_W3_GA": {"runs": [run_row(n) for n in names("w23b_dp_W3_*_GA_*_ep4_seed42")],
                             "contract": "T-2026-11-01-stage2-w23-bengio"},
        "phase_head_W2_all": {"runs": [run_row(n) for n in names("w23b_dp_W2_*_ep4_seed42")],
                              "contract": "T-2026-11-01-stage2-w23-bengio"},
        "phase_head_W3_all": {"runs": [run_row(n) for n in names("w23b_dp_W3_*_ep4_seed42")],
                              "contract": "T-2026-11-01-stage2-w23-bengio"},
        "phase_head_scratch_P15": {"runs": [run_row("stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42")],
                                   "contract": "T-2026-09-27-stage1-ptower-20（確定の時間ヘッド）"},
        "det_iface_W1_fourth": {"runs": [run_row(n) for n in names("grasparms_B_*_ep4_seed42")
                                         if read(f"{P1}/{n}/start.txt") and n not in
                                         ("grasparms_B_empty_ep4_seed42", "grasparms_B_gt_ep4_seed42")],
                                "contract": "T-2026-11-06-grasp-pilot-arms（四本目）"},
        "det_iface_W1_fifth": {"runs": [run_row(n, REF5) for n in ("grasparms_B_empty_ep4_seed42", "grasparms_B_gt_ep4_seed42")],
                               "contract": "T-2026-11-06-grasp-pilot-d-rerun（五本目、分岐の版）"},
        "det_relearn_third": {"runs": [run_row(n) for n in ("grasppilot3_d_gteach_ep15_seed42", "grasppilot3_d_none_ep15_seed42",
                                                            "grasppilot3_d_shuf_ep15_seed42")],
                              "contract": "T-2026-11-01-grasp-pilot-d（三本目）"},
        "det_relearn_fifth": {"runs": [run_row(n, REF5) for n in ("graspd2_gteach_ep15_seed42", "graspd2_shuf_ep15_seed42")],
                              "contract": "T-2026-11-06-grasp-pilot-d-rerun（五本目、分岐の版）"},
        "phase_finetune_P15": {"runs": [run_row("stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42")],
                               "contract": "T-2026-09-27-stage1-ptower-20（確定の工程塔、efros）"},
    }
    # bengio の fine-tune（T-2026-11-02-hostdiff-bengio。2 GPU、phase_manifest_all_phase。版管理の外）
    hd = glob.glob(f"{HOSTDIFF}/runs/phase1/*_ft_*/metrics.json")[0]
    d = json.loads(Path(hd).read_text())
    t = json.loads(Path(f"{HOSTDIFF}/timing.json").read_text())
    groups["phase_finetune_bengio_hostdiff"] = {
        "contract": "T-2026-11-02-hostdiff-bengio", "runs": [{
            "run": Path(hd).parent.name, "source": hd, "elapsed_seconds": d["elapsed_seconds"],
            "elapsed_from": "metrics.json:elapsed_seconds", "epochs_completed": d["epochs_completed"],
            "peak_memory_bytes": d["peak_memory_bytes"], "timing_json_finetune_s": t["finetune_s"],
            "timing_json_heads_s": t["heads_s"], "timing_json_head_s_range": [min(t["head_s"]), max(t["head_s"])],
            "server": "bengio（finetune.command.sh: torch.distributed.run --nproc_per_node=2）"}]}
    ft = json.loads((ROOT / P1 / "stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42/metrics.json").read_text())
    groups["phase_finetune_P15"]["runs"][0].update(
        epochs_completed=ft["epochs_completed"], peak_memory_bytes=ft["peak_memory_bytes"],
        seconds_per_epoch=ft["elapsed_seconds"] / ft["epochs_completed"], device="cuda:0（config.yaml）")
    hr = groups["phase_finetune_bengio_hostdiff"]["runs"][0]
    hr["seconds_per_epoch"] = hr["elapsed_seconds"] / hr["epochs_completed"]
    for g in groups.values():
        g["elapsed_seconds"] = summary(g["runs"], "elapsed_seconds")
        g["wall_seconds"] = summary(g["runs"], "wall_seconds")
        g["max_concurrent_in_group"] = overlap(g["runs"])
        g["servers"] = sorted({str(r.get("server")) for r in g["runs"]})
    Path(a.out).write_text(json.dumps(groups, ensure_ascii=False, indent=1) + "\n")
    for k, g in groups.items():
        print(k, len(g["runs"]), g["elapsed_seconds"], g["wall_seconds"], g["max_concurrent_in_group"], g["servers"])


if __name__ == "__main__":
    main()
