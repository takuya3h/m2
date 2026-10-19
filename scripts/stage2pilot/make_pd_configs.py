"""PD の界面つき検出塔のモデル設定を作る（非公式 T-2026-10-18-stage2-pilot-folda、Task D-3）。

検出塔（D*-COCO）のモデル設定 relation_detr_resnet50_egosurgery.py の本文を写し、
末尾の ``model = RelationDETR(...)`` だけを ``RelationDETRStage2Pilot(..., interface=, signal_dim=)`` に替える。
信号の次元は 9（予測か正解）と 18（正解と予測の連結）。出力は configs/stage2pilot/（版管理の中）。

    python scripts/stage2pilot/make_pd_configs.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery.py"
OUT = ROOT / "configs/stage2pilot"
VARIANTS = [("film", 9), ("film", 18), ("clsbias_lin", 9), ("clsbias_lin", 18),
            ("clsbias_fix", 9), ("query", 9), ("query", 18)]
OLD_IMPORT = "from models.detectors.relation_detr import RelationDETR\n"
OLD_MODEL = "model = RelationDETR(\n"
OLD_TAIL = "    denoising_nums=100, min_size=800, max_size=1333,\n)"


def main():
    text = SRC.read_text()
    src_sha = hashlib.sha256(text.encode()).hexdigest()
    assert text.count(OLD_IMPORT) == 1 and text.count(OLD_MODEL) == 1 and text.count(OLD_TAIL) == 1
    OUT.mkdir(parents=True, exist_ok=True)
    for interface, dim in VARIANTS:
        body = text.replace(OLD_IMPORT, OLD_IMPORT + "from stage2pilot.pd_model import RelationDETRStage2Pilot\n")
        body = body.replace(OLD_MODEL, "model = RelationDETRStage2Pilot(\n")
        body = body.replace(OLD_TAIL, "    denoising_nums=100, min_size=800, max_size=1333,\n"
                                      f"    interface=\"{interface}\", signal_dim={dim},\n)")
        head = (f"# 自動生成（scripts/stage2pilot/make_pd_configs.py）。非公式 T-2026-10-18-stage2-pilot-folda。\n"
                f"# 元: third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery.py"
                f"（sha256 {src_sha}）\n"
                f"# 差は検出器のクラスを RelationDETRStage2Pilot（interface={interface}, signal_dim={dim}）にした点だけ。\n"
                f"# import には sys.path に scripts/ が要る（train_t1b.py が通す）。\n")
        path = OUT / f"pd_{interface}_d{dim}.py"
        path.write_text(head + body)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
