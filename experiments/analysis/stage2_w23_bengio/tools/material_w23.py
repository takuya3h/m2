"""本契約が使う信号と checkpoint の在否と要約値の照合（非公式 T-2026-11-01-stage2-w23-bengio、Task B-1）。

読むだけ。参照の要約値は各契約の記録から取る（他のホストの値は写さない。値は bengio で測る）:

- DP と GA: W1 の run の ``config.yaml`` の ``signals_train``・``signals_val``（経路と sha256）、``receiver.head_sha256``・``cache_sha256``
- PD: 直しの契約の ``material/material_check.json`` と ``bengio/input_digest_bengio.json``（信号と検出塔の重み）、
  EQ の ``missed_train.json`` は版管理下の写し ``experiments/analysis/stage2_pilot_four/xq/missed_train.json``
- GA の信号は andrew から本契約の置き場へ写したもの（``COPIED``）。記録の経路を写しの経路へ読み替えて照合する

    python experiments/analysis/stage2_w23_bengio/tools/material_w23.py --out <json> [--flip-control <scratch dir>]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store")
S = STORE / "T-2026-11-01-stage2-w23-bengio"
COPIED = {str(STORE / "T-2026-10-31-grasp-pilot-probe/signals"): str(S / "copied/grasp-pilot-probe/signals"),
          str(STORE / "T-2026-11-01-grasp-pilot-g/signals"): str(S / "copied/grasp-pilot-g/signals")}
DP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L1", "D3-L2", "LC", "TH", "TH-NG", "GA")
DP_RUN_GLOBS = ("stage2fix_dp_*_{t}_*_ep4_seed42", "stage2four_dp_*_{t}_*_ep4_seed42",
                "grasppilot_dp_*_{t}_*_ep4_seed42", "grasppilot2_dp_*_{t}_*_ep4_seed42")
FIX_AN = ROOT / "experiments/analysis/stage2_pilot_fix"
OLD = STORE / "T-2026-10-18-stage2-pilot-folda"
FIX = STORE / "T-2026-10-19-stage2-pilot-fix-epoch4-shuffle"
FOUR = STORE / "T-2026-10-19-stage2-pilot-four-new-types"
# PD の台本（run_pd_fix.sh・run_pd_four.sh）が読む信号
PD_SIGNALS = [OLD / "signals/final/P0_train.npz", OLD / "signals/final/P0_val.npz",
              OLD / "signals/final/P-GT_train.npz", OLD / "signals/final/P-GT_val.npz",
              OLD / "signals/cf/P0_train.npz", OLD / "arms/PD/gtpred_CF_train.npz", OLD / "arms/PD/gtpred_noCF_val.npz",
              FIX / "signals/shuffle/P0_train.npz", FIX / "signals/shuffle/P0_val.npz"]
DET_CKPT = ROOT / "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth"
MISSED = FOUR / "xq/missed_train.json"
MISSED_COPY = ROOT / "experiments/analysis/stage2_pilot_four/xq/missed_train.json"


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def local_path(p: str) -> str:
    for src, dst in COPIED.items():
        if p.startswith(src + "/"):
            return dst + p[len(src):]
    return p


def add(refs, path, digest, source):
    refs.setdefault(str(path), {}).setdefault(digest, []).append(source)


def collect():
    refs, runs = {}, {}
    for t in DP_TYPES:
        for g in DP_RUN_GLOBS:
            for d in sorted(glob.glob(str(ROOT / "experiments/phase1" / g.format(t=t)))):
                if d.endswith("_smoke"):
                    continue
                cfg = yaml.safe_load(Path(d, "config.yaml").read_text())
                if cfg.get("type") != t:
                    continue
                name = Path(d).name
                runs.setdefault(t, []).append(name)
                for part in ("signals_train", "signals_val"):
                    for s in cfg.get(part) or []:
                        add(refs, s["path"], s["sha256"], name)
                rec = cfg["receiver"]
                add(refs, rec["head"], rec["head_sha256"], name)
                add(refs, rec["cache"], rec["cache_sha256"], name)
    mc = json.loads((FIX_AN / "material/material_check.json").read_text())
    for s in mc["signals"]:
        add(refs, s["path"], s["sha256"], "stage2_pilot_fix/material/material_check.json")
    ib = json.loads((FIX_AN / "bengio/input_digest_bengio.json").read_text())
    for p, h in ib["signals"].items():
        add(refs, p, h, "stage2_pilot_fix/bengio/input_digest_bengio.json")
    add(refs, DET_CKPT, ib["det_ckpt"], "stage2_pilot_fix/bengio/input_digest_bengio.json")
    add(refs, MISSED, sha256(MISSED_COPY), "experiments/analysis/stage2_pilot_four/xq/missed_train.json（版管理下の写し）")
    return refs, runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--flip-control", default=None, help="1 バイト変えた写しを置く scratch（陽性対照）")
    a = ap.parse_args()
    refs, runs = collect()
    rows = []
    for p in sorted(refs):
        lp = local_path(p)
        exists = Path(lp).is_file()
        got = sha256(lp) if exists else None
        recorded = refs[p]
        rows.append({"recorded_path": p, "local_path": lp, "exists": exists, "sha256": got,
                     "recorded_sha256": sorted(recorded), "n_records": sum(len(v) for v in recorded.values()),
                     "records_agree": len(recorded) == 1, "match": exists and got in recorded and len(recorded) == 1})
    missing_ref = [str(p) for p in PD_SIGNALS if str(p) not in refs]
    out = {"task_id": "T-2026-11-01-stage2-w23-bengio", "n_files": len(rows),
           "all_exist": all(r["exists"] for r in rows), "all_match": all(r["match"] for r in rows),
           "pd_signals_without_record": missing_ref, "dp_runs_read": runs, "files": rows}
    if a.flip_control:
        src = Path(rows[0]["local_path"])
        dst = Path(a.flip_control) / ("flipped_" + src.name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        b = bytearray(dst.read_bytes())
        b[len(b) // 2] ^= 0x01
        dst.write_bytes(bytes(b))
        got = sha256(dst)
        out["flip_control"] = {"source": str(src), "copy": str(dst), "sha256": got,
                               "matches_record": got in refs[rows[0]["recorded_path"]]}
        dst.unlink()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ("files", "dp_runs_read")}, ensure_ascii=False))
    print({t: len(v) for t, v in runs.items()})
    for r in rows:
        if not r["match"]:
            print("MISMATCH", r)


if __name__ == "__main__":
    main()
