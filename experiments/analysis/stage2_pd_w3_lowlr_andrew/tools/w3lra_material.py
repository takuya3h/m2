"""Task B-1: 本契約が読む信号・検出塔の重み・設定・学習のコードの在否と要約値を、前回の記録と照合する（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew）。

読むだけ。書くのは --out と、陽性対照の複製（--flip-dir の下）だけ。

記録（どれも前の契約が残したもの。本契約は書き換えない）:
  - 前回の andrew の契約の B-1: experiments/analysis/stage2_w23_andrew/material/material.json の rows（信号・検出塔）
  - 前回の bengio の契約の B-1: experiments/analysis/stage2_w23_bengio/material/material_check.json の files（信号・検出塔）
  - 前回の W3 の run の記録: experiments/phase1/w23a_pd_DX_W3_*/input_sha256.txt・code_sha256.txt（andrew の DX）、
    experiments/phase1/w23b_pd_*-W3_*/code_sha256.txt（bengio の P1・P2L・P3）
  - 設定とコード: 前回の andrew の W3 の run の code_commit.txt の版にある同じ経路の中身（git show）
  - seed 123 の検出塔（B-2 の対照だけ）: grasp_pilot_arms・grasp_pilot_d の repro の sha256 の記録

    python w3lra_material.py --out <json> --flip-dir <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

M = Path(__file__).resolve().parents[4]
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store")
OLD = STORE / "T-2026-10-18-stage2-pilot-folda"
FIX = STORE / "T-2026-10-19-stage2-pilot-fix-epoch4-shuffle"
TASK_ID = "T-2026-11-09-stage2-pd-w3-lowlr-andrew"

SIGNALS = [
    (OLD / "signals/final/P0_train.npz", "空・予測-noCF（train）"),
    (OLD / "signals/final/P0_val.npz", "空・予測-noCF（val）"),
    (OLD / "signals/final/P-GT_train.npz", "正解（train）"),
    (OLD / "signals/final/P-GT_val.npz", "正解（val）"),
    (FIX / "signals/shuffle/P0_train.npz", "入れ替え（train）"),
    (FIX / "signals/shuffle/P0_val.npz", "入れ替え（val）"),
]
DET = M / "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth"
DET_CONTROL = M / "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth"
CFGS = {t: M / f"configs/stage2pilot/pd_{i}_d9.py" for t, i in
        (("P1", "film"), ("P2L", "clsbias_lin"), ("P3", "query"), ("DX", "dec_xattn"))}
CODE = [M / "scripts/train_t1b.py", M / "scripts/stage2pilot/pd_model.py"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_sha_lines(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            h, p = line.split(maxsplit=1)
            out[p.strip()] = h
    return out


def records() -> dict[str, dict[str, str]]:
    """経路（絶対、または repo 相対）→ {記録の名前: sha256}。"""
    rec: dict[str, dict[str, str]] = {}

    def add(path: str, name: str, h: str):
        key = path if path.startswith("/") else str(M / path)
        key = key.replace("/home/ubuntu/slocal2/s2fix-bengio-body/", str(M) + "/")   # bengio の重ねの BODY の経路を andrew の main に読み替える
        rec.setdefault(key, {})[name] = h

    a = json.loads((M / "experiments/analysis/stage2_w23_andrew/material/material.json").read_text())
    for r in a["rows"]:
        add(r["path"], "w23_andrew_material", r["sha256"])
    b = json.loads((M / "experiments/analysis/stage2_w23_bengio/material/material_check.json").read_text())
    for r in b["files"]:
        for h in r["recorded_sha256"]:
            add(r["recorded_path"], "w23_bengio_material", h)
    for d in sorted((M / "experiments/phase1").glob("w23a_pd_DX_W3_*_ep4_seed42")):
        for p, h in read_sha_lines(d / "input_sha256.txt").items():
            add(p, f"run_input:{d.name}", h)
        for p, h in read_sha_lines(d / "code_sha256.txt").items():
            add(p, f"run_code:{d.name}", h)
    for d in sorted((M / "experiments/phase1").glob("w23b_pd_*-W3_*_ep4_seed42")):
        for p, h in read_sha_lines(d / "code_sha256.txt").items():
            add(p, f"run_code:{d.name}", h)
    # 設定とコードは版管理に在る。前回の andrew の W3 の run が記録した版（code_commit.txt）の同じ経路の中身を記録とする
    commits = sorted({(d / "code_commit.txt").read_text().strip()
                      for d in (M / "experiments/phase1").glob("w23a_pd_DX_W3_*_ep4_seed42")})
    for c in commits:
        for p in list(CFGS.values()) + CODE:
            rel = p.relative_to(M).as_posix()
            blob = subprocess.run(["git", "-C", str(M), "show", f"{c}:{rel}"], capture_output=True, check=True).stdout
            add(str(p), f"git_blob@{c[:8]}", hashlib.sha256(blob).hexdigest())
    # seed 123 の検出塔（B-2 の対照）: 前の契約の再現の記録
    for f in ("experiments/analysis/grasp_pilot_arms/repro/b2_sha256.txt", "experiments/analysis/grasp_pilot_d/repro/b1_sha256.txt"):
        for p, h in read_sha_lines(M / f).items():
            add(p, f"repro:{f.split('/')[2]}", h)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--flip-dir", required=True)
    a = ap.parse_args()
    rec = records()
    rows = []
    targets = [(p, k) for p, k in SIGNALS] + [(DET, "検出塔 D*-COCO 折り A seed 42"),
                                             (DET_CONTROL, "検出塔 seed 123（B-2 の対照だけ）")]
    targets += [(p, f"設定 {t}") for t, p in CFGS.items()] + [(p, "学習のコード") for p in CODE]
    for p, kind in targets:
        row = {"path": str(p), "kind": kind, "exists": p.is_file()}
        if row["exists"]:
            row["sha256"] = sha256(p)
            row["bytes"] = p.stat().st_size
        r = rec.get(str(p), {})
        row["recorded"] = r
        row["n_records"] = len(r)
        row["matches_all_records"] = bool(r) and row.get("sha256") is not None and all(h == row["sha256"] for h in r.values())
        rows.append(row)
    # 陽性対照: 複製の 1000 バイト目を反転すると記録と一致しない。変えない複製は一致する
    src = OLD / "signals/final/P0_val.npz"
    fd = Path(a.flip_dir)
    fd.mkdir(parents=True, exist_ok=True)
    same, flip = fd / "P0_val_copy.npz", fd / "P0_val_flip1000.npz"
    shutil.copyfile(src, same)
    shutil.copyfile(src, flip)
    with flip.open("r+b") as f:
        f.seek(1000)
        b = f.read(1)
        f.seek(1000)
        f.write(bytes([b[0] ^ 0xFF]))
    recorded = set(rec.get(str(src), {}).values())
    out = {"task_id": TASK_ID, "rows": rows,
           "all_exist": all(r["exists"] for r in rows),
           "all_with_record": all(r["n_records"] > 0 for r in rows),
           "all_match": all(r["matches_all_records"] for r in rows),
           "copy_control": {"sha256": sha256(same), "matches_record": sha256(same) in recorded},
           "flip_control": {"sha256": sha256(flip), "matches_record": sha256(flip) in recorded}}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for r in rows:
        print(f"{r['kind']:<28} exists={r['exists']} n_rec={r['n_records']} match={r['matches_all_records']} "
              f"{r.get('sha256', '')[:16]} {Path(r['path']).name}")
    print(json.dumps({k: out[k] for k in ("all_exist", "all_with_record", "all_match", "copy_control", "flip_control")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
