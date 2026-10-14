#!/usr/bin/env python
"""T-2026-10-14-frame-signal-audit Task D — 送り手信号の時刻の判定と、その陽性対照。

判定の手順（装置も推論も使わない。キャッシュと正解だけを読む）:
  1. 受け手の照合規則（frame_id の名前の一致）で、送り手のキャッシュと受け手の鍵集合を突き合わせる
  2. 名前が一致した行の中身が、**同じ名前のフレームの正解**に対応するかを、区間内の並びを
     k フレームずらして比べる（k = -2..+2）。一致（正解から作る信号）または一致率（予測の信号）が
     最大になる k を「送り手が持つ情報の時刻のずれ」と判定する。k=0 なら同時刻
  3. 陽性対照: 送り手の frame_ids を区間内で 1 つ先の名前へ付け替えた写し（名前 t の行が t-1 の情報を持つ）
     を同じ手順に通し、k=-1（「一つ前の時刻まで」）と判定されることを確かめる。陰性対照: ずらさない写しで k=0
  k の符号: k = （行の中身が対応する時刻）−（行の名前の時刻）。負なら過去の情報、正なら未来の情報。

対象の送り手（val 分割。キャッシュが無いものは UNKNOWN）:
  phase_context（工程→検出、凍結 S4 の事後確率 9-d）  … 予測。正解は manifest の label
  b2a toolpresence（検出→工程、15-d 最大スコア）         … 予測。正解は COCO の枠のクラス集合
  t1a regiontoken（検出→工程、15×256-d）                … 予測。クラス別の norm>0 を存在とみなして正解と比べる
  oracle toolpresence（15-d one-hot）                    … 正解から作る
  oracle handfeature presence（4-d）                     … 正解から作る（egosurgery_tool_hand）
  oracle phase one-hot（train_t1b.load_oracle_phase_ctx）… 正解から作る（manifest の label）
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "experiments/analysis/frame_signal_audit"
SPLIT = "val"
OFFSETS = (-2, -1, 0, 1, 2)
NUM_TOOLS = 15


def manifest_clips():
    d = json.loads((ROOT / f"data/processed/phase_manifest/{SPLIT}.json").read_text())
    return [(c["clip_id"], [f["frame"] for f in c["frames"]], [int(f["label"]) for f in c["frames"]]) for c in d["clips"]]


def coco_gt(ann_path, cat_filter=None):
    """frame_id -> クラスの集合（0 始まりに正規化）。cat_filter で手クラスなどに絞る。"""
    d = json.loads(ann_path.read_text())
    cats = sorted(c["id"] for c in d["categories"])
    idx = {c: i for i, c in enumerate(cats if cat_filter is None else cat_filter)}
    stem = {im["id"]: Path(im["file_name"]).stem for im in d["images"]}
    out = {s: set() for s in stem.values()}
    for a in d["annotations"]:
        if cat_filter is None or a["category_id"] in cat_filter:
            out[stem[a["image_id"]]].add(idx[a["category_id"]])
    return out, len(idx)


def load_cache(path, key):
    if not path.exists():
        return None
    d = np.load(path)
    return {str(f): d[key][i] for i, f in enumerate(d["frame_ids"])}


def shifted_copy(cache, clips):
    """区間内で 1 つ先の名前へ付け替えた写し（最後の行は落ちる）。"""
    out = {}
    for _, frames, _ in clips:
        for a, b in zip(frames, frames[1:]):
            if a in cache:
                out[b] = cache[a]
    return out


def judge(cache, clips, truth_of, agree):
    """受け手の規則（名前の一致）で突き合わせ、並びを k ずらした一致率の最大の k を返す。"""
    keys = [f for _, frames, _ in clips for f in frames]
    matched = [f for f in keys if f in cache]
    scores = {}
    for k in OFFSETS:
        hits, n = 0.0, 0
        for _, frames, _ in clips:
            for i, f in enumerate(frames):
                j = i + k
                if f in cache and 0 <= j < len(frames):
                    hits += agree(cache[f], truth_of(frames[j]))
                    n += 1
        scores[k] = hits / n if n else float("nan")
    best = max(scores, key=lambda k: scores[k])
    return {"receiver_keys": len(keys), "matched_by_name": len(matched), "missing": len(keys) - len(matched),
            "agreement_by_offset": {str(k): round(v, 6) for k, v in scores.items()}, "judged_offset": best,
            "verdict": "同時刻" if best == 0 else f"ずらし({best:+d})"}


def main():
    clips = manifest_clips()
    label_of = {f: l for _, frames, labels in clips for f, l in zip(frames, labels)}
    tool_gt, _ = coco_gt(ROOT / f"data/annotations/egosurgery_tool/instances_{SPLIT}.json")
    hand_path = ROOT / f"data/annotations/egosurgery_tool_hand/instances_{SPLIT}.json"
    hand_gt = coco_gt(hand_path, cat_filter=[15, 16, 17, 18])[0] if hand_path.exists() else None

    senders = {
        "phase_context(P->D, S4 posterior 9d)": (
            ROOT / f"data/processed/phase_context/relation_detr_seed42/{SPLIT}_phasectx.npz", "ctx",
            lambda f: label_of[f], lambda row, y: float(int(np.argmax(row)) == y)),
        "b2a_toolpresence(D->P, 15d max score)": (
            ROOT / f"data/processed/b2a_detsignal/relation_detr_seed42/{SPLIT}_toolpresence.npz", "signal",
            lambda f: tool_gt[f], lambda row, s: float(np.mean([(row[c] > 0.5) == (c in s) for c in range(NUM_TOOLS)]))),
        "t1a_regiontoken(D->P, 15x256d)": (
            ROOT / f"data/processed/t1a_regiontoken/relation_detr_seed42/{SPLIT}_regiontoken.npz", "region",
            lambda f: tool_gt[f],
            lambda row, s: float(np.mean([(np.linalg.norm(row.reshape(15, 256)[c]) > 0.5 * np.linalg.norm(row.reshape(15, 256), axis=1).max()) == (c in s) for c in range(NUM_TOOLS)]))),
        "oracle_toolpresence(D->P, 15d one-hot)": (
            ROOT / f"data/processed/oracle_toolpresence/{SPLIT}_oracletool.npz", "signal",
            lambda f: tool_gt[f], lambda row, s: float(set(np.flatnonzero(row > 0.5).tolist()) == s)),
        "oracle_phase_onehot(P->D, 9d; train_t1b.load_oracle_phase_ctx)": (
            None, None, lambda f: label_of[f], lambda row, y: float(int(np.argmax(row)) == y)),
    }
    if hand_gt is not None:
        senders["oracle_handfeature_presence(D->P, 4d)"] = (
            ROOT / f"data/processed/oracle_handfeature/{SPLIT}_oraclehand_presence.npz", "signal",
            lambda f: hand_gt.get(f, set()), lambda row, s: float(set(np.flatnonzero(row > 0.5).tolist()) == s))

    report = {"split": SPLIT, "offsets": list(OFFSETS), "senders": {}}
    for name, (path, key, truth_of, agree) in senders.items():
        if path is None:  # 正解 one-hot は train_t1b と同じ作り方で manifest から組む
            cache = {}
            for f, l in label_of.items():
                v = np.zeros(9, dtype=np.float32)
                v[l] = 1.0
                cache[f] = v
            source = "manifest label (same construction as scripts/train_t1b.py:82-99)"
        else:
            cache = load_cache(path, key)
            source = str(path.relative_to(ROOT))
        if cache is None:
            report["senders"][name] = {"source": source, "status": "UNKNOWN (cache absent on this host)"}
            continue
        plain = judge(cache, clips, truth_of, agree)
        shifted = judge(shifted_copy(cache, clips), clips, truth_of, agree)
        margin = plain["agreement_by_offset"]["0"] - max(v for k, v in plain["agreement_by_offset"].items() if k != "0")
        report["senders"][name] = {"source": source, "rows": len(cache), "dim": int(next(iter(cache.values())).shape[0]),
                                   "unshifted": plain, "unshifted_margin_over_next_best": round(margin, 6),
                                   "shifted_control(name t holds t-1)": shifted,
                                   "control_ok": plain["judged_offset"] == 0 and shifted["judged_offset"] == -1}
    (OUT / "time_alignment_val.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for name, r in report["senders"].items():
        if "unshifted" in r:
            print(f"{name}: matched {r['unshifted']['matched_by_name']}/{r['unshifted']['receiver_keys']} "
                  f"verdict={r['unshifted']['verdict']} agree={r['unshifted']['agreement_by_offset']} | "
                  f"margin={r['unshifted_margin_over_next_best']} | shifted-> {r['shifted_control(name t holds t-1)']['verdict']} control_ok={r['control_ok']}")
        else:
            print(f"{name}: {r['status']}")


if __name__ == "__main__":
    sys.exit(main())
