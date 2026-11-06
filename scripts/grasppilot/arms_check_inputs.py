"""材料の照合（非公式 T-2026-11-06-grasp-pilot-arms、Task B-1）。読むだけ。

目録 signals_manifest.json の信号（案 A の g、案 B の m の view と地図）、G の重み 3 本、一本目の正解の g を sha256 で照合し、
案 A の g はフレーム数・次元・旗の有無、view は地図の経路とフレーム数も比べる。

    python scripts/grasppilot/arms_check_inputs.py --out <json>
    python scripts/grasppilot/arms_check_inputs.py --corrupt-copy <dir> --out <json>   # 対照: 1 バイト変えた写しで不一致になること
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

M = Path(__file__).resolve().parents[2]
MANIFEST = M / "experiments/analysis/grasp_tower_rebuild/signals_manifest.json"
R = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild")
PROBE = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe")
# 一本目の正解の g（tasks/T-2026-10-31-grasp-pilot-probe/audit.md 158 行は先頭 16 桁。全桁は前契約の写しの照合で一致した値）
GT_PREFIX = {"g_train.npz": "741cecb5d42decd7", "g_val.npz": "235e2c2bde3a0478"}


def sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--corrupt-copy", default=None, help="対照: 案 A の g の一つを写して 1 バイト変え、照合する")
    a = p.parse_args()
    man = json.loads(MANIFEST.read_text())
    rows = []

    def add(kind, name, path, want, **extra):
        got = sha(path) if Path(path).exists() else None
        rows.append(dict(kind=kind, name=name, path=str(path), want=want, got=got, match=got == want, **extra))

    for run, d in man["g_runs"].items():
        add("G_ckpt", run, R / f"g/ckpt/{run}/best.pth", d["best_ckpt_sha256"])
    for name, d in man["A_g"].items():
        if name == "made_by":
            continue
        path = d["path"]
        if a.corrupt_copy and name == "pred_noCF_val":
            dst = Path(a.corrupt_copy) / Path(path).name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dst)
            with open(dst, "r+b") as f:
                f.seek(100)
                b = f.read(1)
                f.seek(100)
                f.write(bytes([b[0] ^ 0xFF]))
            path = dst
        z = np.load(path)
        x = z["x"]
        add("A_g", name, path, d["sha256"], frames=int(x.shape[0]), dims=int(x.shape[1]),
            frames_ok=int(x.shape[0]) == d["frames"] and int(x.shape[1]) == d["dims"],
            has_flag="flag" in z.files, range=[float(x.min()), float(x.max())])
    seen = set()
    for name, d in man["B_m"].items():
        add("B_view", name, d["view"], d["view_sha256"])
        v = json.loads(Path(d["view"]).read_text())
        rows[-1].update(view_maps=v["maps"], view_maps_ok=v["maps"] == d["maps"], view_frames=len(v["frame_ids"]),
                        view_frames_ok=len(v["frame_ids"]) == d["frames"], mapping=v.get("mapping") is not None)
        if d["maps"] not in seen:
            seen.add(d["maps"])
            mm = np.load(d["maps"], mmap_mode="r")
            add("B_maps", name, d["maps"], d["maps_sha256"], shape=list(mm.shape), dtype=str(mm.dtype))
    for f, pre in GT_PREFIX.items():
        for base in (R / "inputs/probe_signals", PROBE / "signals"):
            got = sha(base / f) if (base / f).exists() else None
            rows.append(dict(kind="GT_g", name=f, path=str(base / f), want=pre + "…", got=got,
                             match=got is not None and got.startswith(pre)))
    out = dict(manifest=str(MANIFEST), manifest_sha256=sha(MANIFEST), corrupt_copy=a.corrupt_copy,
               n=len(rows), n_match=sum(r["match"] for r in rows), rows=rows)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for r in rows:
        print(f"{'OK ' if r['match'] else 'NG '} {r['kind']:7s} {r['name']:18s} {r['got'][:16] if r['got'] else None}"
              + "".join(f" {k}={r[k]}" for k in ("frames", "dims", "has_flag", "frames_ok", "view_frames_ok", "view_maps_ok",
                                                 "shape") if k in r))
    print(f"一致 {out['n_match']} / {out['n']}")


if __name__ == "__main__":
    main()
