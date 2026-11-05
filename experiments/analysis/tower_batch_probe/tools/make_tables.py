"""Markdown tables for REPORT.md from summarize.py's levels.json (no value is typed by hand).

    python make_tables.py <levels.json> > tables.md

The projected epoch time is recomputed here as steps x mean step and checked against
summarize.py's value (acceptance f).
"""
from __future__ import annotations

import json
import sys

ORDER = ["det_b2", "det_b4", "det_b6", "det_b8", "ph2_b8", "ph2_b12", "ph2_b16",
         "ph1_b16", "ph1_b24", "ph1_b32"]


def fmt(value, digits=3):
    if value is None:
        return "UNKNOWN"
    return f"{value:,.{digits}f}" if isinstance(value, float) else f"{value:,}"


def main():
    levels = {l["level"]: l for l in json.load(open(sys.argv[1]))}
    print("| 水準 | GPU ごとの batch | 枚数 | 結果 | rank | torch 最大確保 (bytes) | torch 最大予約 (bytes) | "
          "nvidia-smi 最大 (MiB) | 一歩の平均 (s) | 標準偏差 (s) | 1 epoch の歩数 | 見込み (s) = 歩数 × 平均 | "
          "読み込んだ枚数 = batch | GPU 使用率の平均 (%, 参考) |")
    print("|" + "---|" * 14)
    for name in ORDER:
        level = levels[name]
        result = "収まった" if level["fitted"] else (
            "溢れた（歩 " + ", ".join(str(r["oom"]["step"]) for r in level["ranks"] if r["oom"]) + " で OOM）")
        for rank in level["ranks"]:
            gpu = level["gpus"].split(",")[int(rank["rank"])]
            smi = level["nvidia_smi"][gpu]
            mean = rank.get("step_seconds_mean")
            projected = rank.get("epoch_seconds_projected")
            if mean is not None:
                assert abs(rank["steps_per_epoch"] * mean - projected) < 1e-9
            print(f"| {name} | {level['batch_per_gpu']} | {len(level['gpus'].split(','))} | {result} | "
                  f"{rank['rank']} (GPU{gpu}) | {fmt(rank['max_memory_allocated_bytes'])} | "
                  f"{fmt(rank['max_memory_reserved_bytes'])} | {fmt(smi['peak_mib'])} | {fmt(mean, 4)} | "
                  f"{fmt(rank.get('step_seconds_sd'), 4)} | {fmt(rank['steps_per_epoch'])} | {fmt(projected, 1)} | "
                  f"{'一致' if rank['frames_match_batch'] else '不一致'}（{rank['steps_started']} 歩、"
                  f"各歩 {rank['frames_per_step_set']}） | {fmt(smi['util_mean_while_loaded'], 1)} |")
    print()
    print("| 水準 | 読んだ動画（フレーム数） | test {04,05,07} との共通 | 保存された重み |")
    print("|---|---|---|---|")
    for name in ORDER:
        level = levels[name]
        print(f"| {name} | {', '.join(f'{v}:{n}' for v, n in level['videos_read'].items())} | "
              f"{len(level['test_videos_read'])} 件 | {len(level['weight_files'])} 件 |")


if __name__ == "__main__":
    main()
