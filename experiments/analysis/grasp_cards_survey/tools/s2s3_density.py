"""S2（把持の注釈の密度）と S3（術具注釈フレームの時間間隔）。注釈と目録だけを読む。画像は読まない。

T-2026-11-08-grasp-cards-survey。本体の .venv。

フレーム名は `<動画>_<クリップ>_<フレーム番号>`（例 09_1_0213）。フレーム番号は 0.5 fps の通し番号
（原論文の 25 fps を 0.5 fps に間引いた。docs/evidence/reports/A2-research_claude.md 46 行）なので、
同じクリップの中の番号の差 Δ は 2Δ 秒に当たる。クリップをまたぐ差は時刻が分からないので数えない（別に数を出す）。

集合（折り A の train と val、動画ごと）:
  tool      術具注釈の画像（egosurgery_tool_folds/A/instances_<part>.json の images）。box 1 個以上の画像も数える
  hts       把持関係の注釈の画像（egosurgery_hts/hand_tool_seg/<part>.json の images）。注釈 1 件以上、
            持つ術具（カテゴリ 3〜5）1 件以上も数える
  lossmask  構造的欠落（hand_tool_seg/loss_mask/<part>.txt）
  phase     工程塔の目録のフレーム（data/processed/phase_manifest/<part>.json の clips の frames）
  phase_csv 工程の注釈の全行（data/annotations/egosurgery_phase/<動画>_<クリップ>.csv。train と val の動画だけ開く）
  image     phase_csv のフレームのうち data/raw/ego/<part>/<動画>/<名前>.jpg が在るもの（在否を stat で見るだけ。読まない）

対照（SPEC §6 の c・d）:
  --control では、件数を数える関数に test の動画 04 を混ぜた集合、存在しない動画 99 を渡す。
  test の動画の件数を数えるときだけ test の注釈の目録（画像の名前の一覧）を開く。画像は読まない。
  S3 の対応は、術具注釈フレームの番号を 1 ずらした写しで崩れることを確かめる。

    python s2s3_density.py --out <json>
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
TOOL = ROOT / "data/annotations/egosurgery_tool_folds/A"
HTS = ROOT / "data/annotations/egosurgery_hts/hand_tool_seg"
PHASE = ROOT / "data/processed/phase_manifest"
PHASE_CSV = ROOT / "data/annotations/egosurgery_phase"
RAW = ROOT / "data/raw/ego"
FPS = 0.5
TEST = {"04", "05", "07"}
OPENED: list[str] = []
CSV_LABEL: dict[str, str] = {}      # 工程の CSV のフレーム名 → 工程名
MAN_LABEL: dict[str, str] = {}      # 工程塔の目録のフレーム名 → 工程名


def stem(name):
    return Path(name).stem


def video_of(s):
    return s.split("_")[0]


def parse(s):
    v, c, n = s.split("_")
    return v, int(c), int(n)


def load_json(path):
    OPENED.append(str(Path(path).relative_to(ROOT)))
    return json.loads(Path(path).read_text())


def sources(parts):
    """parts の注釈から、フレーム名の集合を種類ごとに作る。"""
    out = {k: set() for k in ("tool", "tool_box", "hts", "hts_ann", "hts_tool", "lossmask", "phase", "phase_csv", "image")}
    for part in parts:
        t = load_json(TOOL / f"instances_{part}.json")
        out["tool"] |= {stem(im["file_name"]) for im in t["images"]}
        boxed = {a["image_id"] for a in t["annotations"]}
        out["tool_box"] |= {stem(im["file_name"]) for im in t["images"] if im["id"] in boxed}
        h = load_json(HTS / f"{part}.json")
        name = {im["id"]: stem(im["file_name"]) for im in h["images"]}
        out["hts"] |= set(name.values())
        out["hts_ann"] |= {name[a["image_id"]] for a in h["annotations"]}
        out["hts_tool"] |= {name[a["image_id"]] for a in h["annotations"] if a["category_id"] in (3, 4, 5)}
        OPENED.append(str((HTS / "loss_mask" / f"{part}.txt").relative_to(ROOT)))
        out["lossmask"] |= set((HTS / "loss_mask" / f"{part}.txt").read_text().split())
        if part != "test":
            m = load_json(PHASE / f"{part}.json")
            out["phase"] |= {f["frame"] for c in m["clips"] for f in c["frames"]}
            MAN_LABEL.update({f["frame"]: f["phase"] for c in m["clips"] for f in c["frames"]})
            for v in sorted({c["video"] for c in m["clips"]}):
                for csv in sorted(PHASE_CSV.glob(f"{v}_*.csv")):
                    OPENED.append(str(csv.relative_to(ROOT)))
                    pairs = [r.split(",") for r in csv.read_text().splitlines()[1:] if r.strip()]
                    CSV_LABEL.update({f: ph for f, ph in pairs})
                    rows = [f for f, _ in pairs]
                    out["phase_csv"] |= set(rows)
                    out["image"] |= {f for f in rows if (RAW / part / v / f"{f}.jpg").exists()}
    return out


def per_video(src, videos):
    rows = {}
    for v in videos:
        s = {k: {f for f in x if video_of(f) == v} for k, x in src.items()}
        rows[v] = {
            "tool_frames": len(s["tool"]),
            "tool_frames_with_box": len(s["tool_box"]),
            "hts_frames": len(s["hts"]),
            "hts_frames_with_ann": len(s["hts_ann"]),
            "hts_frames_with_held_tool": len(s["hts_tool"]),
            "tool_and_hts": len(s["tool"] & s["hts"]),
            "lossmask_frames": len(s["lossmask"]),
            "lossmask_in_tool": len(s["lossmask"] & s["tool"]),
            "lossmask_in_hts": len(s["lossmask"] & s["hts"]),
            "phase_frames": len(s["phase"]),
            "phase_without_tool": len(s["phase"] - s["tool"]),
            "phase_without_hts": len(s["phase"] - s["hts"]),
            "phase_without_grasp_usable": len(s["phase"] - (s["hts"] - s["lossmask"])),
            "tool_not_in_phase": len(s["tool"] - s["phase"]),
            "phase_csv_frames": len(s["phase_csv"]),
            "phase_csv_with_image": len(s["image"]),
            "phase_csv_without_tool": len(s["phase_csv"] - s["tool"]),
            "phase_csv_without_grasp_usable": len(s["phase_csv"] - (s["hts"] - s["lossmask"])),
            "phase_csv_without_tool_with_image": len((s["phase_csv"] - s["tool"]) & s["image"]),
            "tool_not_in_phase_csv": len(s["tool"] - s["phase_csv"]),
            "hts_not_in_tool": len(s["hts"] - s["tool"]),
        }
    return rows


def total(rows):
    keys = next(iter(rows.values())).keys()
    return {k: int(sum(r[k] for r in rows.values())) for k in keys}


def quantiles(x):
    x = np.asarray(x, float)
    if not len(x):
        return None
    return {"n": int(len(x)), "min": float(x.min()), "p5": float(np.percentile(x, 5)),
            "median": float(np.median(x)), "p95": float(np.percentile(x, 95)), "max": float(x.max())}


def runs_of_missing(phase_frames, have):
    """工程のフレームを (クリップ, 番号) 順に並べ、have に無いフレームが連続する長さ（工程のフレームの数）の分布。"""
    by_clip = defaultdict(list)
    for f in phase_frames:
        v, c, n = parse(f)
        by_clip[(v, c)].append((n, f))
    lengths = []
    for key in sorted(by_clip):
        run = 0
        for _, f in sorted(by_clip[key]):
            if f in have:
                if run:
                    lengths.append(run)
                run = 0
            else:
                run += 1
        if run:
            lengths.append(run)
    q = quantiles(lengths)
    hist = {}
    for L in lengths:
        b = str(L) if L <= 5 else ("6-10" if L <= 10 else ("11-50" if L <= 50 else ">50"))
        hist[b] = hist.get(b, 0) + 1
    return {"runs": len(lengths), "frames": int(sum(lengths)), "length_quantiles": q, "length_hist": hist}


def gaps(frames):
    """同じクリップの中で隣り合うフレーム番号の差（Δ）と秒（Δ / FPS）。クリップの境目の数も返す。"""
    by_clip = defaultdict(list)
    for f in frames:
        v, c, n = parse(f)
        by_clip[(v, c)].append(n)
    d = []
    for key in sorted(by_clip):
        ns = sorted(by_clip[key])
        d += [b - a for a, b in zip(ns, ns[1:])]
    return np.asarray(d), len(by_clip)


def s3(src, videos):
    out = {}
    for v in videos:
        tool = sorted(f for f in src["tool"] if video_of(f) == v)
        phase = {f for f in src["phase"] if video_of(f) == v}
        pcsv = {f for f in src["phase_csv"] if video_of(f) == v}
        d, clips = gaps(tool)
        dp, _ = gaps(phase)
        dc, _ = gaps(pcsv)
        shifted = {f"{a}_{b}_{int(n) + 1:04d}" for a, b, n in (f.split("_") for f in tool)}
        out[v] = {
            "tool_frames": len(tool), "clips": clips,
            "delta_frames": quantiles(d), "delta_seconds": quantiles(d / FPS),
            "delta_eq_1": int((d == 1).sum()), "delta_gt_1": int((d > 1).sum()),
            "phase_delta_frames": quantiles(dp),
            "phase_csv_delta_frames": quantiles(dc),
            "tool_in_phase_csv": len(set(tool) & pcsv), "tool_not_in_phase_csv": len(set(tool) - pcsv),
            "tool_label_agrees_csv": sum(MAN_LABEL.get(f) == CSV_LABEL.get(f) for f in tool),
            "control_shift1_in_phase_csv": len(shifted & pcsv),
            "control_shift1_label_agrees_csv": sum(MAN_LABEL.get(f) == CSV_LABEL.get(g) for f, g in
                                                   zip(tool, (f"{a}_{b}_{int(n) + 1:04d}" for a, b, n in (x.split("_") for x in tool)))),
            "tool_in_phase": len(set(tool) & phase), "tool_not_in_phase": len(set(tool) - phase),
            "control_shift1_tool_in_phase": len(shifted & phase),
            "control_shift1_exact_same_frames": len(shifted & set(tool)),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    fold = {"train": ["01", "02", "03", "06", "08", "11", "12", "13", "14", "15"], "val": ["09", "10"]}
    # 折り A の動画は正本の表から（stage2pilot.common.fold_a と同じ読み方）
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from stage2pilot import common as C
    fa = C.fold_a()
    assert {k: sorted(v) for k, v in fa.items() if k != "test"} == {k: sorted(v) for k, v in fold.items()}
    src = sources(["train", "val"])
    vids = fold["train"] + fold["val"]
    assert not ({video_of(f) for x in src.values() for f in x} & TEST), "train/val の注釈に test の動画"
    rows = per_video(src, vids)
    res = {"fps": FPS, "fps_source": "docs/evidence/reports/A2-research_claude.md:46（25 fps を 0.5 fps に間引き）",
           "videos": fold, "per_video": rows,
           "total_train": total({v: rows[v] for v in fold["train"]}),
           "total_val": total({v: rows[v] for v in fold["val"]}),
           "runs_missing": {}, "s3": s3(src, vids)}
    for v in vids:
        ph = {f for f in src["phase"] if video_of(f) == v}
        pc = {f for f in src["phase_csv"] if video_of(f) == v}
        res["runs_missing"][v] = {
            "tool": runs_of_missing(ph, src["tool"]),
            "grasp_usable": runs_of_missing(ph, src["hts"] - src["lossmask"]),
            "csv_tool": runs_of_missing(pc, src["tool"]),
            "csv_grasp_usable": runs_of_missing(pc, src["hts"] - src["lossmask"]),
        }
    for part in ("train", "val"):
        allph = {f for f in src["phase"] if video_of(f) in fold[part]}
        allpc = {f for f in src["phase_csv"] if video_of(f) in fold[part]}
        res["runs_missing"][f"all_{part}"] = {
            "tool": runs_of_missing(allph, src["tool"]),
            "grasp_usable": runs_of_missing(allph, src["hts"] - src["lossmask"]),
            "csv_tool": runs_of_missing(allpc, src["tool"]),
            "csv_grasp_usable": runs_of_missing(allpc, src["hts"] - src["lossmask"]),
        }
        tool = [f for f in src["tool"] if video_of(f) in fold[part]]
        # 動画ごとにクリップの中の差を集める
        d = np.concatenate([gaps([f for f in tool if video_of(f) == v])[0] for v in fold[part]])
        res["s3"][f"all_{part}"] = {"delta_frames": quantiles(d), "delta_seconds": quantiles(d / FPS),
                                    "delta_eq_1_fraction": float((d == 1).mean())}
    # 対照（§6 c）。数える関数に集合を渡すだけ。test の件数は test の目録（画像の名前）から数える
    trainval = total(rows)
    src_ctl = sources(["train", "val", "test"])
    with_04 = total(per_video(src_ctl, vids + ["04"]))
    none_99 = total(per_video(src_ctl, ["99"]))
    res["controls"] = {
        "trainval_tool_frames": trainval["tool_frames"], "with_test_04_tool_frames": with_04["tool_frames"],
        "trainval_hts_frames": trainval["hts_frames"], "with_test_04_hts_frames": with_04["hts_frames"],
        "trainval_lossmask": trainval["lossmask_frames"], "with_test_04_lossmask": with_04["lossmask_frames"],
        "trainval_phase_csv": trainval["phase_csv_frames"], "with_test_04_phase_csv": with_04["phase_csv_frames"],
        "nonexistent_99": none_99,
        "note": "test の動画 04 の件数は test の術具・把持の注釈の目録の画像名と loss_mask/test.txt だけから数えた（工程の目録と CSV の test は開かないので、工程の件数は 04 を混ぜても変わらないはず）。画像は読んでいない",
    }
    res["opened_files"] = sorted(set(OPENED))
    res["images_read"] = 0
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("total_train", "total_val", "controls")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
