#!/usr/bin/env python
"""T-2026-10-14-frame-signal-audit Task B — 方法 A: 注釈・manifest・画像の置き場を直接読む。

四つの集合（工程 CSV / 術具 COCO / ホスト上の画像 / 工程塔の manifest）を
(動画, 区間, 番号) の組で作り、動画ごと・区間ごとの集合差、片方にしか無いフレームの一覧、
塔が見るフレーム列の番号の飛び、画像の全数復号、要約値を出す。読むだけで data/ には書かない。

出力（experiments/analysis/frame_signal_audit/）:
  sets_by_clip.csv / sets_by_video.csv        集合の件数と集合差（方法 A）
  phase_only_frames.csv                        工程注釈だけがあるフレームと、配布物 2 か所での在否
  tool_zero_box_frames.csv                     術具注釈の画像のうち枠 0 個のもの
  gaps_<source>.csv                            区間ごとの番号の飛び（件数・最大・区分）
  gap_events_manifest15.csv                    manifest（15 動画）の飛びの一覧（秒換算は 0.5 fps の仮定）
  summary_method_a.json                        全体の値、起票者 §3.2 との照合、対照、復号、要約値

実行（本体 .venv、CPU のみ）:
  .venv/bin/python experiments/analysis/frame_signal_audit/tools/audit_frames.py [--no-decode]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, OrderedDict, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "experiments/analysis/frame_signal_audit"
PHASE_DIR = ROOT / "data/annotations/egosurgery_phase"
TOOL_DIR = ROOT / "data/annotations/egosurgery_tool"
EGO_ROOT = ROOT / "data/raw/ego"
EGO_SUBDIRS = ("train", "val", "test", "other(17~21)")
M15_DIR = ROOT / "data/processed/phase_manifest"
M20_DIR = ROOT / "data/processed/stage1_features/p20_manifest"
OPENSURGERY_FRAMES = ROOT / "data/raw/OpenSurgery_Dataset/01_frames/initial_videos"
HTS2_IMAGES = ROOT / "data/raw/EgoSurgery_HTS2/images"
PAT = re.compile(r"^(\d{2})_(\d+)_(\d{4})$")
ASSUMED_FPS = 0.5  # 仮定。根拠は REPORT.md の「時刻の根拠」を見よ
GAP_BINS = ((1, 1), (2, 4), (5, 14), (15, 59), (60, 10**9))

# 起票者が版管理の写しで数えた値（SPEC §3.2）。食い違えば実測を正とする。
ISSUER = {
    "phase_clips_01_15": 23, "phase_frames_01_15": 17233, "phase_frames_17_21": 10461,
    "tool_images_01_15": 15437, "tool_without_phase": 0, "phase_without_tool": 1796,
    "tool_zero_box": 123, "clip_03_3_phase": 168, "clip_03_3_tool": 0,
    "phase_gap_events_01_15": 547,
    "tool_seq_span_sum": 21880, "tool_seq_missing": 6443, "tool_seq_gap_events": 1013,
    "tool_seq_gap_bins": {"1": 526, "2-4": 286, "5-14": 118, "15-59": 60, "60+": 23},
    "per_video": {  # 動画: (工程, 術具, 差, 枠0)
        "01": (999, 913, 86, 0), "02": (529, 461, 68, 3), "03": (1363, 1089, 274, 0),
        "04": (1643, 1329, 314, 56), "05": (1318, 1225, 93, 2), "06": (1447, 1379, 68, 11),
        "07": (1788, 1711, 77, 26), "08": (1591, 1400, 191, 0), "09": (672, 518, 154, 0),
        "10": (1232, 997, 235, 0), "11": (865, 754, 111, 2), "12": (619, 609, 10, 1),
        "13": (843, 822, 21, 3), "14": (1858, 1810, 48, 15), "15": (466, 420, 46, 4),
    },
}


def key(stem: str):
    m = PAT.match(stem)
    return (m.group(1), int(m.group(2)), int(m.group(3))) if m else None


def clip_of(k):
    return f"{k[0]}_{k[1]}"


def read_phase():
    """工程 CSV → {clip: [(番号, 工程)]}（ファイルの行順のまま）。番号の形を満たさない行は記録する。"""
    clips, bad, dup = OrderedDict(), [], []
    for path in sorted(PHASE_DIR.glob("*.csv")):
        rows, seen = [], set()
        with path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                frame, phase = (r.get("Frame") or "").strip(), (r.get("Phase") or "").strip()
                k = key(frame)
                if not frame or not phase or k is None or clip_of(k) != path.stem:
                    bad.append((path.stem, frame, phase))
                    continue
                if k in seen:
                    dup.append(frame)
                seen.add(k)
                rows.append((k, phase))
        clips[path.stem] = rows
    return clips, bad, dup


def read_tool():
    """術具 COCO → 画像の集合、枠 0 個の画像、分割ごとの件数。file_name の stem を鍵にする。"""
    frames, zero, per_split, bad = {}, set(), {}, []
    for split in ("train", "val", "test"):
        d = json.loads((TOOL_DIR / f"instances_{split}.json").read_text())
        counts = Counter(a["image_id"] for a in d["annotations"])
        n_img = 0
        for im in d["images"]:
            k = key(Path(im["file_name"]).stem)
            if k is None:
                bad.append((split, im["file_name"]))
                continue
            if k in frames:
                bad.append((split, f"duplicate {im['file_name']}"))
            frames[k] = (split, im["file_name"], im["width"], im["height"])
            n_img += 1
            if counts.get(im["id"], 0) == 0:
                zero.add(k)
        per_split[split] = {"images": n_img, "annotations": len(d["annotations"]),
                            "zero_box": sum(1 for im in d["images"] if counts.get(im["id"], 0) == 0)}
    return frames, zero, per_split, bad


def scan_images(root: Path, subdirs=None):
    """置き場の画像を集める。シンボリックリンクを辿り、先頭がドットのものも数える。"""
    found, other, zero_bytes = {}, [], []
    dirs = [root / s for s in subdirs] if subdirs else [root]
    for d in dirs:
        if not d.exists():
            continue
        for dirpath, _, files in os.walk(d, followlinks=True):
            for name in files:
                p = Path(dirpath) / name
                stem, ext = os.path.splitext(name)
                k = key(stem) if ext.lower() in (".jpg", ".jpeg", ".png") else None
                if k is None:
                    other.append(str(p.relative_to(ROOT)))
                    continue
                if p.stat().st_size == 0:
                    zero_bytes.append(str(p.relative_to(ROOT)))
                found[k] = str(p.relative_to(ROOT))
    return found, other, zero_bytes


def read_manifest(mdir: Path):
    """manifest → {clip: [(番号, split, image_path)]}（manifest の順のまま）。"""
    clips = OrderedDict()
    for split in ("train", "val", "test"):
        d = json.loads((mdir / f"{split}.json").read_text())
        for c in d["clips"]:
            rows = []
            for f in c["frames"]:
                k = key(f["frame"])
                assert k is not None and clip_of(k) == c["clip_id"], (c["clip_id"], f["frame"])
                rows.append((k, split, f["image_path"]))
            assert c["clip_id"] not in clips, c["clip_id"]
            clips[c["clip_id"]] = rows
    return clips


def gaps_of(numbers):
    """番号列（並び順のまま）の飛び。(前の番号, 次の番号, 飛び=差-1) を返す。逆行も記録する。"""
    events, backward = [], 0
    for a, b in zip(numbers, numbers[1:]):
        if b < a:
            backward += 1
        elif b - a > 1:
            events.append((a, b, b - a - 1))
    return events, backward


def bin_name(g):
    for lo, hi in GAP_BINS:
        if lo <= g <= hi:
            return "60+" if hi >= 10**9 else (f"{lo}" if lo == hi else f"{lo}-{hi}")
    raise ValueError(g)


def gap_table(sequences: dict, name: str):
    """区間ごとの飛びの表と、飛びの一覧。sequences = {clip: [番号...]}。"""
    rows, events_all, bins = [], [], Counter()
    for clip, nums in sequences.items():
        ev, back = gaps_of(nums)
        c = Counter(bin_name(g) for _, _, g in ev)
        bins.update(c)
        rows.append({"clip": clip, "frames": len(nums), "first": nums[0] if nums else "",
                     "last": nums[-1] if nums else "", "span": (nums[-1] - nums[0] + 1) if nums else 0,
                     "missing_in_span": (nums[-1] - nums[0] + 1 - len(nums)) if nums else 0,
                     "gap_events": len(ev), "gap_max": max((g for _, _, g in ev), default=0),
                     "gap_sum": sum(g for _, _, g in ev), "backward_steps": back,
                     **{f"bin_{b}": c.get(b, 0) for b in ("1", "2-4", "5-14", "15-59", "60+")}})
        events_all.extend((clip, a, b, g) for a, b, g in ev)
    with (OUT / f"gaps_{name}.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    total = {"clips": len(rows), "frames": sum(r["frames"] for r in rows),
             "span_sum": sum(r["span"] for r in rows), "missing_in_span": sum(r["missing_in_span"] for r in rows),
             "gap_events": sum(r["gap_events"] for r in rows), "gap_sum": sum(r["gap_sum"] for r in rows),
             "gap_max": max((r["gap_max"] for r in rows), default=0),
             "backward_steps": sum(r["backward_steps"] for r in rows),
             "bins": {b: bins.get(b, 0) for b in ("1", "2-4", "5-14", "15-59", "60+")}}
    return total, events_all


def _decode(path):
    from PIL import Image
    try:
        with Image.open(path) as im:
            im.load()
            return (str(path), None, im.size)
    except Exception as e:  # noqa: BLE001  復号できない理由をそのまま残す
        return (str(path), repr(e), None)


def _digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return str(path), h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-decode", action="store_true", help="画像の全数復号と要約値を飛ばす")
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()

    phase, phase_bad, phase_dup = read_phase()
    tool, tool_zero, tool_split, tool_bad = read_tool()
    host, host_other, host_zero_bytes = scan_images(EGO_ROOT, EGO_SUBDIRS)
    m15 = read_manifest(M15_DIR)
    m20 = read_manifest(M20_DIR)
    opensurgery, _, _ = scan_images(OPENSURGERY_FRAMES)
    hts2, _, _ = scan_images(HTS2_IMAGES)

    P = {k for rows in phase.values() for k, _ in rows}
    T = set(tool)
    H = set(host)
    M15 = {k for rows in m15.values() for k, _, _ in rows}
    M20 = {k for rows in m20.values() for k, _, _ in rows}
    O, X = set(opensurgery), set(hts2)
    sets = {"phase": P, "tool": T, "host_img": H, "m15": M15, "m20": M20}

    # --- 区間ごと・動画ごとの表 -------------------------------------------------
    clips = sorted({clip_of(k) for s in sets.values() for k in s}, key=lambda c: (c.split("_")[0], int(c.split("_")[1])))
    pairs = [("phase", "tool"), ("tool", "phase"), ("phase", "host_img"), ("host_img", "phase"),
             ("tool", "host_img"), ("host_img", "tool"), ("phase", "m15"), ("m15", "phase"),
             ("phase", "m20"), ("m20", "phase"), ("m15", "tool"), ("tool", "m15"), ("m20", "host_img"), ("host_img", "m20")]

    def row_for(label, members):
        r = {"clip" if "_" in label else "video": label}
        for name, s in sets.items():
            r[name] = len(s & members)
        for a, b in pairs:
            r[f"{a}_minus_{b}"] = len((sets[a] - sets[b]) & members)
        r["tool_zero_box"] = len(tool_zero & members)
        po = (P - T) & members
        r["phase_only"] = len(po)
        r["phase_only_in_opensurgery_frames"] = len(po & O)
        r["phase_only_in_hts2"] = len(po & X)
        r["phase_only_in_neither"] = len(po - O - X)
        r["opensurgery_frames"] = len(O & members)
        r["hts2_images"] = len(X & members)
        return r

    universe = set().union(*sets.values()) | O | X
    by_clip = [row_for(c, {k for k in universe if clip_of(k) == c}) for c in clips]
    videos = sorted({c.split("_")[0] for c in clips})
    by_video = [row_for(v, {k for k in universe if k[0] == v}) for v in videos]
    for name, rows in (("sets_by_clip.csv", by_clip), ("sets_by_video.csv", by_video)):
        with (OUT / name).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    # --- 片方にしか無いフレームの一覧 -------------------------------------------
    phase_label = {k: ph for rows in phase.values() for k, ph in rows}
    with (OUT / "phase_only_frames.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "video", "clip", "phase", "in_opensurgery_frames", "in_hts2_images", "in_m15", "in_m20"])
        for k in sorted(P - T):
            w.writerow([f"{k[0]}_{k[1]}_{k[2]:04d}", k[0], clip_of(k), phase_label[k],
                        int(k in O), int(k in X), int(k in M15), int(k in M20)])
    with (OUT / "tool_zero_box_frames.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "video", "clip", "split", "phase"])
        for k in sorted(tool_zero):
            w.writerow([f"{k[0]}_{k[1]}_{k[2]:04d}", k[0], clip_of(k), tool[k][0], phase_label.get(k, "")])
    one_sided = {"tool_minus_phase": sorted(T - P), "host_minus_phase": sorted(H - P), "host_minus_tool": sorted(H - T),
                 "tool_minus_host": sorted(T - H), "m15_minus_phase": sorted(M15 - P), "m20_minus_phase": sorted(M20 - P),
                 "m15_minus_host": sorted(M15 - H), "m20_minus_host": sorted(M20 - H), "phase_minus_m20": sorted(P - M20)}

    # --- 塔が見るフレーム列の飛び --------------------------------------------------
    seq_phase = {c: [k[2] for k, _ in rows] for c, rows in phase.items()}
    seq_m15 = {c: [k[2] for k, _, _ in rows] for c, rows in m15.items()}
    seq_m20 = {c: [k[2] for k, _, _ in rows] for c, rows in m20.items()}
    seq_tool = defaultdict(list)
    for k in sorted(T):
        seq_tool[clip_of(k)].append(k[2])
    gap_phase, _ = gap_table(seq_phase, "phase_csv")
    gap_m15, ev15 = gap_table(seq_m15, "manifest15")
    gap_m20, ev20 = gap_table(seq_m20, "manifest20")
    gap_tool, _ = gap_table(dict(seq_tool), "tool_sorted")
    with (OUT / "gap_events_manifest15.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["clip", "from_frame", "to_frame", "gap_frames", "gap_seconds_at_assumed_0.5fps"])
        for clip, a, b, g in ev15:
            w.writerow([clip, a, b, g, g / ASSUMED_FPS])
    # manifest の順は番号順か（並びがそのまま時間か）
    order_ok = {name: all(nums == sorted(nums) for nums in seqs.values())
                for name, seqs in (("phase_csv", seq_phase), ("manifest15", seq_m15), ("manifest20", seq_m20))}
    # 動画が複数区間に分かれるとき、区間の境界をまたぐ番号の関係（連番が続くか、番号が戻るか）
    boundaries = []
    for src, seqs in (("manifest15", seq_m15), ("manifest20", seq_m20)):
        byv = defaultdict(list)
        for c, nums in seqs.items():
            byv[c.split("_")[0]].append((int(c.split("_")[1]), c, nums))
        for v, lst in byv.items():
            lst.sort()
            for (_, c1, n1), (_, c2, n2) in zip(lst, lst[1:]):
                boundaries.append({"source": src, "video": v, "from_clip": c1, "to_clip": c2,
                                   "last_of_from": n1[-1], "first_of_to": n2[0], "number_restarts": int(n2[0] <= n1[-1])})

    # --- 対照（陽性: 1 フレーム抜いた写しで差が 1 増える。陰性: 同じ集合どうしで 0）-------
    k0 = next(k for k in sorted(P & T))
    P_minus = P - {k0}
    T_minus = T - {k0}
    seq0 = seq_m15["01_1"]
    mid = next(i for i in range(1, len(seq0) - 1) if seq0[i] - seq0[i - 1] == 1 and seq0[i + 1] - seq0[i] == 1)
    seq_drop = seq0[:mid] + seq0[mid + 1:]
    controls = {
        "removed_frame": f"{k0[0]}_{k0[1]}_{k0[2]:04d}",
        "positive_tool_minus_phase_before_after": [len(T - P), len(T - P_minus)],
        "positive_phase_minus_tool_before_after": [len(P - T), len(P - T_minus)],
        "negative_phase_minus_phase": len(P - P), "negative_tool_minus_tool": len(T - T),
        "negative_same_count_phase_vs_copy": len(P - set(P)),
        "gap_control_clip": "01_1", "gap_control_dropped_number": seq0[mid],
        "gap_events_before_after": [len(gaps_of(seq0)[0]), len(gaps_of(seq_drop)[0])],
    }
    assert controls["positive_tool_minus_phase_before_after"][1] == controls["positive_tool_minus_phase_before_after"][0] + 1
    assert controls["positive_phase_minus_tool_before_after"][1] == controls["positive_phase_minus_tool_before_after"][0] + 1
    assert controls["gap_events_before_after"][1] == controls["gap_events_before_after"][0] + 1

    # --- 起票者 §3.2 との照合 -----------------------------------------------------
    v01_15 = {f"{i:02d}" for i in range(1, 16)}
    P15 = {k for k in P if k[0] in v01_15}
    T_only_seq = {c: n for c, n in seq_tool.items() if c.split("_")[0] in v01_15}
    gt, _ = gap_table(T_only_seq, "tool_sorted_01_15")
    measured = {
        "phase_clips_01_15": sum(1 for c in phase if c.split("_")[0] in v01_15),
        "phase_frames_01_15": len(P15),
        "phase_frames_17_21": len(P - P15),
        "tool_images_01_15": len(T),
        "tool_without_phase": len(T - P), "phase_without_tool": len(P15 - T),
        "tool_zero_box": len(tool_zero),
        "clip_03_3_phase": len(seq_phase.get("03_3", [])), "clip_03_3_tool": len(seq_tool.get("03_3", [])),
        "phase_gap_events_01_15": sum(len(gaps_of(n)[0]) for c, n in seq_phase.items() if c.split("_")[0] in v01_15),
        "tool_seq_span_sum": gt["span_sum"], "tool_seq_missing": gt["missing_in_span"],
        "tool_seq_gap_events": gt["gap_events"], "tool_seq_gap_bins": gt["bins"],
        "per_video": {r["video"]: (r["phase"], r["tool"], r["phase_minus_tool"] + r["tool_minus_phase"], r["tool_zero_box"])
                      for r in by_video if r["video"] in v01_15},
    }
    compare = {}
    for k, v in ISSUER.items():
        if k == "per_video":
            compare[k] = {vid: {"issuer": list(v[vid]), "measured": list(measured[k][vid]), "match": list(v[vid]) == list(measured[k][vid])}
                          for vid in v}
        else:
            compare[k] = {"issuer": v, "measured": measured[k], "match": v == measured[k]}

    # --- 画像の全数復号と要約値 ------------------------------------------------------
    decode = {"skipped": True}
    if not args.no_decode:
        paths = sorted(ROOT / p for p in host.values())
        with Pool(args.workers) as pool:
            results = pool.map(_decode, paths, chunksize=64)
            digests = pool.map(_digest, paths, chunksize=64)
        broken = [(p, e) for p, e, _ in results if e]
        sizes = Counter(s for _, e, s in results if not e)
        per_video = defaultdict(hashlib.sha256)
        total = hashlib.sha256()
        for p, d in sorted(digests):
            rel = str(Path(p).relative_to(ROOT))
            v = key(Path(p).stem)[0]
            per_video[v].update(f"{rel} {d}\n".encode())
            total.update(f"{rel} {d}\n".encode())
        decode = {"skipped": False, "images": len(paths), "undecodable": len(broken), "undecodable_list": broken[:50],
                  "sizes": {f"{w}x{h}": n for (w, h), n in sizes.items()},
                  "bytes_total": sum(Path(p).stat().st_size for p in paths),
                  "sha256_of_sorted_name_and_filehash": total.hexdigest(),
                  "sha256_per_video": {v: h.hexdigest() for v, h in sorted(per_video.items())},
                  "method": "各ファイルの sha256 を名前順に並べた行 '<相対パス> <sha256>\\n' の連結の sha256"}

    summary = {
        "task_id": "T-2026-10-14-frame-signal-audit", "method": "A: csv/json/os.walk で注釈・manifest・画像を直接読む",
        "elapsed_seconds": time.monotonic() - t0,
        "counts": {k: len(v) for k, v in sets.items()} | {"opensurgery_frames": len(O), "hts2_images": len(X)},
        "phase_rows_rejected": phase_bad, "phase_duplicate_frames": phase_dup, "tool_rejected": tool_bad,
        "host_non_frame_files": host_other, "host_zero_byte_files": host_zero_bytes,
        "tool_per_split": tool_split,
        "set_differences_total": {f"{a}_minus_{b}": len(sets[a] - sets[b]) for a, b in pairs},
        "one_sided_examples": {k: [f"{x[0]}_{x[1]}_{x[2]:04d}" for x in v[:5]] for k, v in one_sided.items()},
        "one_sided_counts": {k: len(v) for k, v in one_sided.items()},
        "phase_only": {"total": len(P - T), "in_opensurgery_frames": len((P - T) & O), "in_hts2_images": len((P - T) & X),
                       "in_neither": len((P - T) - O - X), "in_m15": len((P - T) & M15), "in_m20": len((P - T) & M20)},
        "m15_equals_tool_set": M15 == T, "m15_equals_host_01_15": M15 == {k for k in H if k[0] in v01_15},
        "m20_minus_m15_equals_host_17_21": (M20 - M15) == {k for k in H if k[0] not in v01_15},
        "m20_minus_m15_equals_phase_17_21": (M20 - M15) == (P - P15),
        "sequence_is_sorted": order_ok, "clip_boundaries": boundaries,
        "gaps": {"phase_csv": gap_phase, "manifest15": gap_m15, "manifest20": gap_m20, "tool_sorted": gap_tool,
                 "tool_sorted_01_15": gt, "assumed_fps": ASSUMED_FPS,
                 "note": "秒換算は 0.5 fps を仮定した値。根拠の有無は REPORT.md を見よ"},
        "controls": controls, "issuer_compare": compare, "decode": decode,
    }
    (OUT / "summary_method_a.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("counts", "set_differences_total", "phase_only", "controls")}, ensure_ascii=False, indent=1))
    print("decode:", {k: v for k, v in decode.items() if k not in ("undecodable_list", "sha256_per_video")})
    print("issuer mismatches:", [k for k, v in compare.items() if k != "per_video" and not v["match"]],
          [vid for vid, v in compare["per_video"].items() if not v["match"]])
    print(f"written -> {OUT} ({summary['elapsed_seconds']:.0f}s)")


if __name__ == "__main__":
    sys.exit(main())
