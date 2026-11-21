"""Task A: 保存先の信号と前回の組み立ての出力を前回の目録の要約値と照らす（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、SPEC §1.3・§9 a）。

    .venv/bin/python experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/a_check.py --out <T>/start/a_check.json --scratch <T>/start/ctrl

読むだけ。書くのは --out と対照の写しの置き場 --scratch だけ。
  1. 前回の目録 signals_manifest.json の要約値（前回の RESULT §3 の 24d9139d…）と、目録が名指す 14 のグラフ・4 つの検出の配列・
     8 つの G3・H4 の推論の要約値
  2. 前回の組み立ての報告 assemble_report.json の要約値（前回の RESULT §3 の 1e0f052f…）
  3. 工程塔の重みと特徴のキャッシュの要約値（前回のグラフの run の config の値）
  4. 対照: $O の 1 ファイル（グラフ D_val）の写しを 1 バイト変えると照合が外れを数える
"""
from __future__ import annotations

import argparse
import glob
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-21-grasp-hand-irn-hice-htt-pilot"
S = Path("/home/ubuntu/slocal2/stage2pilot_store")
MANIFEST = ROOT / "experiments/analysis/grasp_hand_graph_pilot/signals_manifest.json"
MANIFEST_SHA = "24d9139d3487ee5533d7b26ec9fcff7134cda386619aee3b23fab990c01a1bbd"  # 前回の RESULT §3
ASSEMBLE_PREFIX = "1e0f052f"                                                       # 前回の RESULT §3（先頭 8 桁）


def check_file(path, want):
    got = C.sha256(path)
    return {"path": str(path), "want": want, "got": got, "match": got == want}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    man_sha = C.sha256(MANIFEST)
    man = json.loads(MANIFEST.read_text())
    files = []
    for part, arms in man["graph"].items():
        for arm, v in arms.items():
            files.append({"kind": f"graph/{arm}_{part}", "frames": v["frames"], **check_file(Path(v["path"]), v["sha256"])})
    for k, v in man["det"].items():
        files.append({"kind": f"det/{k}", **check_file(Path(v["npz"]), v["npz_sha256"])})
    for k, v in man["raw_signals"].items():
        files.append({"kind": f"raw/{k}", **check_file(Path(v["npz"]), v["sha256"])})
    asm = Path(man["assemble_report"])
    asm_sha = C.sha256(asm)
    run = Path(sorted(glob.glob(str(ROOT / "experiments/phase1/grasp_hand_graph_arm_*_GR-W1-N10-L1_DGH_conv_seed42")))[0])
    cfg = yaml.safe_load((run / "config.yaml").read_text())
    recv = [check_file(Path(cfg["receiver"]["head"]), cfg["receiver"]["head_sha256"]),
            check_file(Path(cfg["receiver"]["cache"]), cfg["receiver"]["cache_sha256"])]
    scr = Path(a.scratch)
    scr.mkdir(parents=True, exist_ok=True)
    src = Path(man["graph"]["val"]["D"]["path"])
    dst = scr / "D_val_flip.npz"
    shutil.copyfile(src, dst)
    b = bytearray(dst.read_bytes())
    b[len(b) // 2] ^= 0x01
    dst.write_bytes(bytes(b))
    ctrl_files = [dict(f) for f in files]
    for f in ctrl_files:
        if f["kind"] == "graph/D_val":
            f.update(check_file(dst, f["want"]))
    out = {"task_id": TASK, "unofficial": True,
           "manifest": {"path": str(MANIFEST), "want": MANIFEST_SHA, "got": man_sha, "match": man_sha == MANIFEST_SHA},
           "assemble_report": {"path": str(asm), "sha256": asm_sha, "want_prefix": ASSEMBLE_PREFIX,
                               "match": asm_sha.startswith(ASSEMBLE_PREFIX)},
           "files": files, "n": len(files), "n_mismatch": sum(not f["match"] for f in files),
           "receiver": {"run": run.name, "files": recv, "match": all(r["match"] for r in recv)},
           "control_one_byte": {"file": str(dst), "n_mismatch": sum(not f["match"] for f in ctrl_files)}}
    C.write_json(a.out, out)
    print(json.dumps({"manifest": out["manifest"]["match"], "assemble": out["assemble_report"]["match"], "n": out["n"],
                      "n_mismatch": out["n_mismatch"], "receiver": out["receiver"]["match"],
                      "control_n_mismatch": out["control_one_byte"]["n_mismatch"]}))


if __name__ == "__main__":
    main()
