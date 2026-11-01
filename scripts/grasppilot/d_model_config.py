# 非公式 T-2026-11-01-grasp-pilot-d — 案 D の模型設定（main.py の model_path が指す）。
# 検出塔の模型設定 configs/relation_detr/relation_detr_resnet50_egosurgery.py を**そのまま実行**して
# 元と同じ乱数の流れで RelationDETR を作り、補助の頭だけを足す（grasp_aux_d.attach_grasp_head）。
# cwd は third_party/Relation-DETR（main.py の前提）。重ねの BODY の中身を読む。
import os
import runpy
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grasp_aux_d  # noqa: E402

_BASE_MODEL_CFG = os.path.abspath("configs/relation_detr/relation_detr_resnet50_egosurgery.py")
_ns = runpy.run_path(_BASE_MODEL_CFG)
_s = grasp_aux_d.env_settings()
model = grasp_aux_d.attach_grasp_head(_ns["model"], weight=_s["weight"], steplog=_s["steplog"])
del _ns, _s
