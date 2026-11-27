"""SPEC §3.5・§9 d: 形式確認（追加動画 17〜21 の 30 フレーム）の結果集計と陽性対照。"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import captions as cap
import redact as red

ALLOWED_FORMAT_VIDEOS = {"17", "18", "19", "20", "21"}


def check_format_videos(videos: list[str]) -> dict:
    vset = set(videos)
    outside = sorted(vset - ALLOWED_FORMAT_VIDEOS)
    return {"videos": sorted(vset), "outside_allowed": outside, "ok": len(outside) == 0}


def check_prompt_sha(rows: list[dict], expected_sha: str) -> dict:
    shas = sorted({r["prompt_sha256"] for r in rows})
    return {"expected": expected_sha, "observed": shas, "all_match": shas == [expected_sha]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True, help="captions/format-<sha256> ディレクトリ")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--total-prod-frames", type=int, default=11172)
    a = ap.parse_args()

    prompt = (a.dir / "prompt.txt").read_text()
    prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
    choices = cap.options()
    rows = []
    for part in sorted(a.dir.glob("part-*.jsonl")):
        rows.extend(json.loads(line) for line in part.read_text().splitlines())

    vid_chk = check_format_videos([r["video"] for r in rows])
    sha_chk = check_prompt_sha(rows, prompt_sha)

    # 陽性対照 (§9 d): 01 を混ぜた動画検査が外れを出す・プロンプト 1 文字改変で sha256 が食い違う
    vid_pos_ctrl = check_format_videos([r["video"] for r in rows] + ["01"])
    altered_sha = hashlib.sha256((prompt + " ").encode()).hexdigest()
    sha_pos_ctrl = check_prompt_sha(rows, altered_sha)

    parse_errors = Counter(r["parse_error"] for r in rows if r["parse_error"])
    refusals = sum(1 for r in rows if r["refusal"])
    red_counts = {"ko": Counter(), "otsu": Counter(), "hei": Counter()}
    for r in rows:
        for mode in ("ko", "otsu", "hei"):
            _, c = red.redact_record(r["parsed"], choices, mode)
            red_counts[mode].update(c)

    # バッチ単位の生成時間（各バッチで同一 batch_seconds が入っている）
    batch_times = []
    seen_batch = set()
    for i, r in enumerate(rows):
        bkey = (r["batch_seconds"], r["batch_size"])
        if bkey not in seen_batch:
            seen_batch.add(bkey)
            batch_times.append((r["batch_seconds"], r["batch_size"]))
    total_gen_sec = sum(t for t, _ in batch_times)
    total_gen_frames = sum(n for _, n in batch_times)
    sec_per_frame = total_gen_sec / max(total_gen_frames, 1)
    est_prod_sec = sec_per_frame * a.total_prod_frames

    visions = []
    for r in rows:
        if r["vision"] not in visions:
            visions.append(r["vision"])

    report = {
        "dir": str(a.dir),
        "n_frames": len(rows),
        "prompt_sha256": prompt_sha,
        "video_check": vid_chk,
        "prompt_sha_check": sha_chk,
        "positive_controls": {
            "mixed_video_01": vid_pos_ctrl,
            "altered_prompt_sha": sha_pos_ctrl,
        },
        "parse_ok": len(rows) - sum(parse_errors.values()),
        "parse_error_count": sum(parse_errors.values()),
        "parse_error_breakdown": dict(parse_errors),
        "refusals": refusals,
        "redaction_hits": {k: dict(v) for k, v in red_counts.items()},
        "vision_preproc": visions,
        "output_tokens": {
            "min": min(r["output_tokens"] for r in rows),
            "max": max(r["output_tokens"] for r in rows),
            "mean": sum(r["output_tokens"] for r in rows) / len(rows),
        },
        "timing": {
            "batch_times": [{"seconds": t, "batch_size": n} for t, n in batch_times],
            "total_gen_seconds": total_gen_sec,
            "seconds_per_frame": sec_per_frame,
            "estimated_prod_frames": a.total_prod_frames,
            "estimated_prod_seconds": est_prod_sec,
            "estimated_prod_hours": est_prod_sec / 3600.0,
        },
        "sample_errors": [
            {"frame": r["frame"], "parse_error": r["parse_error"], "raw": r["raw"][:400]}
            for r in rows if r["parse_error"]
        ][:5],
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
