"""学習側の教師から、次元ごとの正例率と広がりを実測する。

揃えた値の形（standardized）の中心と広がり、および正解を渡す形（oracle）の
教師の無いフレームの埋め値は、**学習側から求める**（測る側から求めると漏れる）。
ここで求めた定数を設定ファイルへ書き、出所をこの記録に残す。

中心 = 学習側の正例率 p、広がり = sqrt(p(1-p))（二値の標準偏差）。
予測の分布そのものではなく教師の分布から取る。理由は、予測は学習中に動くため
定数として記録できず、測る側から取ると漏れるためである。
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from egosurgery.datasets.grasp_targets import (  # noqa: E402
    GRASP_LABEL_NAMES,
    load_grasp_target_index,
)

TARGET_ROOT = ROOT / "data" / "annotations" / "egosurgery_hts" / "hand_tool_seg"


def main() -> None:
    index = load_grasp_target_index("train", TARGET_ROOT)
    labeled = [index.target_for(stem) for stem in sorted(index.labels)]
    values = np.stack([t for t, valid in labeled if valid], axis=0)
    n_masked = len(index.masked_frames)

    p = values.mean(axis=0)
    scale = np.sqrt(p * (1.0 - p))

    stats = {
        "source": "train split grasp targets (labels, not predictions)",
        "n_frames_labeled": int(values.shape[0]),
        "n_frames_masked": int(n_masked),
        "dimensions": {
            name: {
                "positive_rate": float(p[i]),
                "bernoulli_std": float(scale[i]),
            }
            for i, name in enumerate(GRASP_LABEL_NAMES)
        },
        "signal_center": [round(float(x), 6) for x in p],
        "signal_scale": [round(float(x), 6) for x in scale],
        "oracle_missing_fill": [round(float(x), 6) for x in p],
    }
    (AUDIT / "train_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n")
    print(f"記録: {AUDIT / 'train_stats.json'}")
    print(f"学習側の教師つきフレーム = {values.shape[0]}  教師の無いフレーム = {n_masked}")
    for i, name in enumerate(GRASP_LABEL_NAMES):
        print(f"  {name:<18} p={p[i]:.6f}  sqrt(p(1-p))={scale[i]:.6f}")


if __name__ == "__main__":
    main()
