# AlignDETR-S0-frozen: R50 backbone を全凍結 + head 学習の EgoSurgery 適応版。
#
# 台帳 Run「凍結源の下流有用性比較：Relation-DETR vs AlignDETR」用。
# Relation-DETR-S0-frozen (freeze_indices=(0,1,2,3)) と等価な条件 = backbone 全凍結
# (stem + res2 + res3 + res4 + res5) + head (class_embed 80→15) 再初期化。
#
# 継承元: aligndetr_r50_4scale_12ep_egosurgery.py (フル学習)。
# 変更点:
#   - backbone.freeze_at = 5 (全 5 stage 凍結)。stem は FrozenBN のまま。
#   - class_embed の 80→15 再初期化は継承 (COCO init が形状不一致で自動 skip)。
#   - train.output_dir を s0_frozen 系列に変更 (launcher が seed 別上書き)。
#   - wandb name を s0_frozen 系列に変更。
# 制約: 検出 mAP は S0-frozen (backbone 凍結) の下限性能を測るためのもので、
#   Relation-DETR-S0-frozen と同条件で 3-seed 比較する Δ 分母ではなく、
#   その後段の TeCNO downstream (工程 Δ) が主評価。
from .aligndetr_r50_4scale_12ep_egosurgery import (
    dataloader, optimizer, lr_multiplier, train, model,
)

# --- backbone 全凍結 ------------------------------------------------------ #
# detectron2 の ResNet.freeze_at: 5 = stem + res{2,3,4,5} 全 stage を凍結。
# BN は既存の "FrozenBN" のまま。
model.backbone.freeze_at = 5

# --- output_dir / wandb name (launcher が seed 別に再上書き) --------------- #
train.output_dir = "/tmp/aligndetr_s0frozen_work"
train.wandb.params.name = "aligndetr_s0frozen_r50_12ep"
train.wandb.params.dir = train.output_dir
dataloader.evaluator.output_dir = train.output_dir

# --- init: AlignDETR R50 COCO 12ep 重み (backbone+transformer をロード、
#     class_embed 80->15 は形状不一致で自動 skip) ---------------------------- #
# 継承元と同じ path のはずだが、明示保持で Fail Loud。
train.init_checkpoint = "/home/ubuntu/slocal2/m2/data/external/weights/aligndetr_r50_4scale_12ep_coco.pth"
