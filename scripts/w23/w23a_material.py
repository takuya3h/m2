"""Task B-1: 本契約が読む信号と checkpoint の在否と要約値の照合（非公式 T-2026-11-01-stage2-w23-andrew）。

読むだけ。書き込みは --out と --flip-dir（陽性対照の複製）だけ。

記録（どれも前の契約が残したもの。本契約は書き換えない）:
  - PD の信号 9 本: experiments/analysis/stage2_pilot_four/material/material_four.json（four-new-types の B-1。直しの契約の記録と照合済み）
  - 検出塔の重み: experiments/analysis/stage2_pilot_fix/bengio/input_digest_andrew.json の det_ckpt
  - 案 B の見取りと地図: 二本目の $G/signals/assemble_report.json の B、版管理下の experiments/phase1/grasppilot2_B_*/view_sha256.txt
  - 把持の注釈（正解の地図の出所）: 版管理下の記録の本文に要約値の先頭 16 桁が現れるかを探す（異質な二つ目の方法）

    python scripts/w23/w23a_material.py --out <json> [--flip-dir <dir>]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

M = Path(__file__).resolve().parents[2]
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store")
OLD = STORE / "T-2026-10-18-stage2-pilot-folda"
FIX = STORE / "T-2026-10-19-stage2-pilot-fix-epoch4-shuffle"
G = STORE / "T-2026-11-01-grasp-pilot-g"
DET_CKPT = M / "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth"
HTS = M / "data/annotations/egosurgery_hts"

PD_SIGNALS = [
    (OLD / "signals/final/P0_train.npz", "PD 予測-noCF・空（train）"),
    (OLD / "signals/final/P0_val.npz", "PD 予測-noCF・予測-CF・空（val）"),
    (OLD / "signals/final/P-GT_train.npz", "PD 正解（train）"),
    (OLD / "signals/final/P-GT_val.npz", "PD 正解（val）"),
    (OLD / "signals/cf/P0_train.npz", "PD 予測-CF（train）"),
    (OLD / "arms/PD/gtpred_CF_train.npz", "PD 正解予測-CF（train）"),
    (OLD / "arms/PD/gtpred_noCF_val.npz", "PD 正解予測-CF（val）"),
    (FIX / "signals/shuffle/P0_train.npz", "PD 入れ替え（train）"),
    (FIX / "signals/shuffle/P0_val.npz", "PD 入れ替え（val）"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def records():
    """経路 → {記録の名前: 要約値}。"""
    rec: dict[str, dict[str, str]] = {}

    def put(path, name, digest):
        rec.setdefault(str(path), {})[name] = digest

    four = json.loads((M / "experiments/analysis/stage2_pilot_four/material/material_four.json").read_text())
    for r in four["rows"]:
        if r.get("match"):
            put(r["path"], "four_material", r["sha256"])
    dig = json.loads((M / "experiments/analysis/stage2_pilot_fix/bengio/input_digest_andrew.json").read_text())
    put(DET_CKPT, "fix_input_digest_andrew", dig["det_ckpt"])
    asm = json.loads((G / "signals/assemble_report.json").read_text())
    for v in asm["B"].values():
        put(v["view"], "g_assemble_report", v["view_sha256"])
        put(v["maps"], "g_assemble_report", v["maps_sha256"])
    for f in sorted((M / "experiments/phase1").glob("grasppilot2_B_*_ep4_seed42/view_sha256.txt")):
        for line in f.read_text().splitlines():
            d, p = line.split()
            put(p, f"run_view_sha256:{f.parent.name}", d)
    return rec


def text_search(prefix: str) -> list[str]:
    """版管理下の記録（tasks/ と experiments/analysis/）の本文に要約値の先頭が現れるファイル。"""
    r = subprocess.run(["git", "-C", str(M), "grep", "-l", "-F", prefix, "--", "tasks", "experiments/analysis"],
                       capture_output=True, text=True)
    return [x for x in r.stdout.splitlines() if x]


def b_inputs():
    asm = json.loads((G / "signals/assemble_report.json").read_text())
    rows = []
    for key, v in asm["B"].items():
        rows.append((Path(v["view"]), f"案 B 見取り {key}"))
    for p in sorted({v["maps"] for v in asm["B"].values()}):
        rows.append((Path(p), "案 B 予測の地図"))
    for kind in ("hand_tool_seg", "hand_seg", "tool_seg"):
        for part in ("train", "val"):
            rows.append((HTS / kind / f"{part}.json", f"把持の注釈 {kind}/{part}（正解の地図の出所）"))
    return rows


def check(rows, rec):
    out = []
    for path, use in rows:
        row = {"path": str(path), "use": use, "exists": path.exists()}
        if path.exists():
            row["bytes"] = path.stat().st_size
            row["sha256"] = sha256(path)
            row["recorded"] = rec.get(str(path), {})
            row["n_records"] = len(row["recorded"])
            row["match"] = bool(row["recorded"]) and all(v == row["sha256"] for v in row["recorded"].values())
            if not row["recorded"]:
                row["text_hits"] = text_search(row["sha256"][:16])
        out.append(row)
    return out


HTS_RECORD = STORE / "T-2026-10-31-grasp-pilot-probe/b/b1_ann_check.json"            # 一本目の B-1 の数え
HTS_ACCEPT = M / "experiments/analysis/grasp_pilot_g/c3/acceptance_report.json"      # 二本目の B-3（C1・C2）


def hts_profile(path: Path) -> dict:
    d = json.loads(path.read_text())
    with_ann = {a["image_id"] for a in d["annotations"]}
    vids = sorted({Path(im["file_name"]).stem.split("_")[0] for im in d["images"]})
    return {"n_images": len(d["images"]), "n_frames": len(with_ann & {im["id"] for im in d["images"]}),
            "n_anns": len(d["annotations"]), "videos": vids,
            "categories": [[c["id"], c["name"]] for c in d["categories"]],
            "n_rle": sum(1 for a in d["annotations"] if isinstance(a.get("segmentation"), dict)),
            "cat_counts": {str(k): v for k, v in sorted(collections.Counter(
                a["category_id"] for a in d["annotations"]).items())}}


def hts_content(drop_one: bool = False) -> dict:
    """把持の注釈（train と val だけ。test と extra は開かない）の中身を、一本目と二本目の記録の数えと比べる（異質な二つ目の方法）。"""
    rec = json.loads(HTS_RECORD.read_text())["dirs"]
    acc = json.loads(HTS_ACCEPT.read_text())["checks"]
    rows, ok = [], True
    for kind in ("hand_tool_seg", "hand_seg", "tool_seg"):
        for part in ("train", "val"):
            p = hts_profile(HTS / kind / f"{part}.json")
            if drop_one and kind == "tool_seg" and part == "val":
                p["n_anns"] -= 1                                  # 陽性対照: 注釈を 1 件除いた数
            r = rec[kind][part]
            cmp = {k: (p[k], r[k]) for k in ("n_images", "n_frames", "n_anns", "videos")}
            cmp["categories"] = (p["categories"], rec[kind]["categories"])
            if kind == "hand_tool_seg" and part == "train":
                cmp["n_rle_C1"] = (p["n_rle"], acc["C1_polygon_points"]["toolhand_seg_types"].get("rle"))
                cmp["cat5_count_C2"] = (p["cat_counts"].get("5"), acc["C2_value5_two_hands_tool"]["toolhand_cat5_count"])
            match = all(a == b for a, b in cmp.values())
            ok &= match
            rows.append({"file": f"{kind}/{part}.json", "match": match,
                         "mismatch": {k: v for k, v in cmp.items() if v[0] != v[1]}, "profile": p})
    return {"records": [str(HTS_RECORD), str(HTS_ACCEPT)], "all_match": ok, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--flip-dir")
    args = ap.parse_args()
    rec = records()
    rows = check(PD_SIGNALS + [(DET_CKPT, "検出塔 D*-COCO 折り A seed 42")] + b_inputs(), rec)
    hts = hts_content()
    hts_ctl = hts_content(drop_one=True)
    res = {"task_id": "T-2026-11-01-stage2-w23-andrew", "rows": rows,
           "all_exist": all(r["exists"] for r in rows),
           "with_record": sum(1 for r in rows if r.get("n_records")),
           "all_recorded_match": all(r["match"] for r in rows if r.get("n_records")),
           "no_record": [r["path"] for r in rows if r["exists"] and not r.get("n_records")],
           "hts_content": hts, "hts_content_control_drop_one": {"all_match": hts_ctl["all_match"],
                                                                "mismatch": [r for r in hts_ctl["rows"] if not r["match"]]}}
    if args.flip_dir:
        # 陽性対照: 記録のある小さいファイルの複製の 1 バイトを変えると照合が落ちること
        src = OLD / "signals/final/P0_val.npz"
        dst = Path(args.flip_dir) / "P0_val_flipped.npz"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        b = bytearray(dst.read_bytes())
        b[1000] ^= 0xFF
        dst.write_bytes(bytes(b))
        d = sha256(dst)
        res["flip_control"] = {"source": str(src), "copy": str(dst), "sha256": d,
                               "matches_record": all(v == d for v in rec[str(src)].values())}
        # 陰性側: 変えない複製は一致すること
        same = Path(args.flip_dir) / "P0_val_copy.npz"
        shutil.copyfile(src, same)
        res["copy_control"] = {"copy": str(same),
                               "matches_record": all(v == sha256(same) for v in rec[str(src)].values())}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for r in rows:
        print(f"{'OK ' if r.get('match') else ('NOREC' if r['exists'] else 'MISSING')} "
              f"{r.get('sha256', '')[:12]} n={r.get('n_records', 0)} {r['path']} {r.get('text_hits', '')}")
    for r in hts["rows"]:
        print(f"HTS {'OK ' if r['match'] else 'DIFF'} {r['file']} {r['mismatch']}")
    print({k: v for k, v in res.items() if k not in ("rows", "hts_content", "hts_content_control_drop_one")},
          "hts_all_match", hts["all_match"], "control_all_match", hts_ctl["all_match"])


if __name__ == "__main__":
    main()
