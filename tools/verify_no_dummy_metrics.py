#!/usr/bin/env python3
"""experiments/ に dummy Trainer の乱数由来 per-class AP が混入していないか検査する。

背景
----
`src/egosurgery/engines/trainer.py` の dummy Trainer は、実データセットが未実装
だった時期の仮置きとして **乱数で per-class AP を生成し `mAP` として metrics.json
に書く**:

    rng = np.random.default_rng(int(self.cfg.seed))
    per_class_ap = {cls: round(float(rng.uniform(0.05, 0.85)), 4) for cls in TOOL_CLASSES}
    self.manager.log_per_class_ap(per_class_ap)

CLAUDE.md の「metrics / mAP 等の数値を絶対に捏造しない」に照らして危険なコードが
repo に残っているため、混入していないことを機械的に再検証できるようにする。

検査方法 (2 系統)
-----------------
1. **語彙照合**: dummy 側の TOOL_CLASSES は実データと異なる語彙
   (`Needle_Holders` / `Retractors` / `Clip_Applier` / `Suction` /
   `Electrocautery` / `Needle` / `Thread`) を使う。この集合と一致する
   per_class_ap.json があれば dummy 由来。
2. **値の再現照合**: 既知の seed で乱数列を再現し、per_class_ap.json と
   完全一致するものを探す。一致すれば dummy 由来。

使い方
------
    python tools/verify_no_dummy_metrics.py          # 検査のみ
    python tools/verify_no_dummy_metrics.py --json   # 機械可読な結果を出す

終了コード: 混入 0 件なら 0、1 件以上なら 1。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = REPO_ROOT / "experiments"

# src/egosurgery/engines/trainer.py の TOOL_CLASSES をそのまま写したもの。
# 実データの 15 術具クラスとは語彙が異なる (アンダースコア / 複数形 / 別名)。
DUMMY_TOOL_CLASSES = [
    "Tweezers", "Needle_Holders", "Scissors", "Forceps",
    "Bipolar_Forceps", "Retractors", "Clip_Applier", "Suction",
    "Scalpel", "Electrocautery", "Gauze", "Needle", "Thread",
    "Skewer", "Syringe",
]

# experiments/ に実在する seed (ディレクトリ名の末尾 seed / 補助 seed から収集)
KNOWN_SEEDS = [0, 1, 42, 123, 456, 789, 1000, 2024]


def dummy_per_class_ap(seed: int) -> dict[str, float]:
    """trainer.py の生成手順を完全に再現する。"""
    rng = np.random.default_rng(int(seed))
    return {c: round(float(rng.uniform(0.05, 0.85)), 4) for c in DUMMY_TOOL_CLASSES}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="結果を JSON で出力する")
    args = parser.parse_args()

    dummy_vocab = frozenset(DUMMY_TOOL_CLASSES)
    dummy_values = {s: dummy_per_class_ap(s) for s in KNOWN_SEEDS}

    scanned = 0
    vocab_hits: list[str] = []
    value_hits: list[dict[str, object]] = []

    for path in sorted(EXPERIMENTS.rglob("per_class_ap.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - 壊れたファイルは別途 harvester が記録する
            continue
        if not isinstance(data, dict) or not data:
            continue
        scanned += 1
        rel = str(path.relative_to(REPO_ROOT))

        if frozenset(data) == dummy_vocab:
            vocab_hits.append(rel)

        for seed, expected in dummy_values.items():
            if data == expected:
                value_hits.append({"path": rel, "seed": seed})
                break

    contaminated = sorted({*vocab_hits, *(h["path"] for h in value_hits)})
    result = {
        "scanned_files": scanned,
        "dummy_vocabulary_matches": vocab_hits,
        "dummy_value_matches": value_hits,
        "contaminated_count": len(contaminated),
        "contaminated_paths": contaminated,
        "seeds_checked": KNOWN_SEEDS,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"検査した per_class_ap.json : {scanned}")
        print(f"dummy 語彙と一致          : {len(vocab_hits)}")
        print(f"dummy 値と完全一致        : {len(value_hits)}  (seed {KNOWN_SEEDS} を照合)")
        print(f"混入と判定                : {len(contaminated)}")
        for p in contaminated:
            print(f"  - {p}")
        if not contaminated:
            print("\n混入 0 件。experiments/ の per-class 指標は全て実評価器由来。")
        else:
            print("\n混入を検出した。該当 run を解析から除外し、再評価すること。")

    return 1 if contaminated else 0


if __name__ == "__main__":
    sys.exit(main())
