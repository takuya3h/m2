"""P3 の 4 本を別ホストで回す前に、入力が andrew と同じかを確かめる要約値（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）。

読むだけ。両方のホストで同じ命令を回し、出力の json を突き合わせる（値が一致すれば同じ入力）。

- 信号 8 本（P3 の正解・予測-CF・正解予測-CF・入れ替えが読むもの）の sha256
- 検出塔の重み、折り A の注釈（train・val）の sha256
- 注釈が指す画像（train・val。test の動画は注釈に無い）を名前の順に「名前 sha256」で並べた列の sha256 と枚数
- third_party/Relation-DETR の commit と未 commit の変更の件数、MS-Deform-Attn の CUDA ソースの sha256、
  作業場所のソース（.py .cu .cuh .cpp .h。experiments・入れ子の third_party・checkpoints などは除く）のファイルごとの sha256 と全体の要約値
- torch・CUDA の版（.venv-relation-detr で回したとき）

    <S2FIX_BODY>/.venv-relation-detr/bin/python scripts/stage2pilot/input_digest.py --body <S2FIX_BODY> --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

OLD = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda")
FIX = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle")
SIGNALS = [OLD / "signals/final/P-GT_train.npz", OLD / "signals/final/P-GT_val.npz", OLD / "signals/final/P0_val.npz",
           OLD / "signals/cf/P0_train.npz", OLD / "arms/PD/gtpred_CF_train.npz", OLD / "arms/PD/gtpred_noCF_val.npz",
           FIX / "signals/shuffle/P0_train.npz", FIX / "signals/shuffle/P0_val.npz"]
TEST_VIDEOS = {"04", "05", "07"}
SRC_SUFFIX = {".py", ".cu", ".cuh", ".cpp", ".h"}
SKIP_TOP = {"experiments", "third_party", "checkpoints", "per_class_coco_map", "data", "outputs", "work_dirs"}


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", default="/home/ubuntu/slocal2/m2")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    body = Path(a.body)
    ann_dir = body / "data/annotations/egosurgery_tool_folds/A"
    res = {"signals": {str(p): (sha256(p) if p.exists() else None) for p in SIGNALS},
           "det_ckpt": sha256(body / "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth"),
           "annotations": {p: sha256(ann_dir / p) for p in ("instances_train.json", "instances_val.json")},
           "images": {}}
    for part in ("train", "val"):
        names = sorted(im["file_name"] for im in json.loads((ann_dir / f"instances_{part}.json").read_text())["images"])
        videos = {Path(n).parent.name for n in names}
        assert not videos & TEST_VIDEOS, videos & TEST_VIDEOS
        lines = []
        missing = 0
        for n in names:
            p = body / "data/raw/ego" / n
            if not p.exists():
                missing += 1
                continue
            lines.append(f"{n} {sha256(p)}")
        res["images"][part] = {"count": len(names), "missing": missing, "videos": sorted(videos),
                               "list_sha256": hashlib.sha256("\n".join(lines).encode()).hexdigest()}
    rel = body / "third_party/Relation-DETR"
    git = lambda *args: subprocess.run(["git", "-C", str(rel), *args], capture_output=True, text=True).stdout.strip()  # noqa: E731
    # 未 commit の変更（増強・最適化の群など）を含む作業場所のソースそのもの。commit が同じでも中身が違えば別の模型になる
    files = {}
    for f in sorted(rel.rglob("*")):
        r = f.relative_to(rel)
        if r.parts[0] in SKIP_TOP or "__pycache__" in r.parts or not f.is_file() or f.suffix not in SRC_SUFFIX:
            continue
        files[str(r)] = sha256(f)
    res["relation_detr"] = {"commit": git("rev-parse", "HEAD"),
                            "uncommitted": len([x for x in git("status", "--porcelain").splitlines() if x.strip()]),
                            "msda_cuda_sha256": sha256(rel / "models/bricks/ops/cuda/ms_deform_attn_cuda.cu"),
                            "source_files": len(files),
                            "source_tree_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
                            "source_file_sha256": files}
    try:
        import torch
        res["torch"] = {"version": torch.__version__, "cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
                        "gpus": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]}
    except ImportError:
        res["torch"] = None
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    show = {**res, "relation_detr": {k: v for k, v in res["relation_detr"].items() if k != "source_file_sha256"}}
    print(json.dumps(show, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
