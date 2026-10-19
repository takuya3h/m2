"""PD の新しい型のモデル設定を作る（非公式 T-2026-10-19-stage2-pilot-four-new-types、Task C-1）。

前回の生成済みの設定 configs/stage2pilot/pd_query_d9.py（検出塔 D*-COCO の relation_detr_resnet50_egosurgery.py の写しで、
差は検出器のクラスだけ）を元にし、検出器のクラスを RelationDETRStage2Four（interface=, signal_dim=）に替える。
信号の次元は 9（予測か正解）と 18（正解と予測の連結）。出力は configs/stage2pilot/（版管理の中）。

    python scripts/stage2pilot/make_pd_four_configs.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "configs/stage2pilot/pd_query_d9.py"
OUT = ROOT / "configs/stage2pilot"
VARIANTS = [("dec_xattn", 9), ("dec_xattn", 18), ("extra_q", 9), ("extra_q", 18)]
OLD_IMPORT = "from stage2pilot.pd_model import RelationDETRStage2Pilot\n"
OLD_MODEL = "model = RelationDETRStage2Pilot(\n"
OLD_ARGS = '    interface="query", signal_dim=9,\n)'


def main():
    text = SRC.read_text()
    src_sha = hashlib.sha256(text.encode()).hexdigest()
    head_end = text.index("# DRAFT")                   # 元の生成器の見出し（4 行）を除いた本文
    body0 = text[head_end:]
    assert body0.count(OLD_IMPORT) == 1 and body0.count(OLD_MODEL) == 1 and body0.count(OLD_ARGS) == 1
    for interface, dim in VARIANTS:
        body = body0.replace(OLD_IMPORT, "from stage2pilot.pd_four import RelationDETRStage2Four\n")
        body = body.replace(OLD_MODEL, "model = RelationDETRStage2Four(\n")
        body = body.replace(OLD_ARGS, f'    interface="{interface}", signal_dim={dim},\n)')
        head = (f"# 自動生成（scripts/stage2pilot/make_pd_four_configs.py）。非公式 T-2026-10-19-stage2-pilot-four-new-types。\n"
                f"# 元: configs/stage2pilot/pd_query_d9.py（sha256 {src_sha}）の本文。その元は\n"
                f"#     third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery.py\n"
                f"# 差は検出器のクラスを RelationDETRStage2Four（interface={interface}, signal_dim={dim}）にした点だけ。\n"
                f"# import には sys.path に scripts/ が要る（train_t1b.py が通す）。\n")
        path = OUT / f"pd_{interface}_d{dim}.py"
        path.write_text(head + body)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
