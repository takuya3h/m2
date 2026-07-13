# T1b clsbias モデル/config の追跡コピー（再現性用）

`third_party/Relation-DETR/` は gitignore 配下のため、本実験の注入モデルと config を
再現性のためここに複製している（実行時は third_party 側に配置される）。

- `relation_detr_phaseclsbias.py.txt` → `third_party/Relation-DETR/models/detectors/`
- `relation_detr_resnet50_egosurgery_t1b_clsbias.py.txt` → `third_party/Relation-DETR/configs/relation_detr/`

実行: `bash scripts/run_t1b_clsbias_3seed_efros.sh`（`scripts/train_t1b.py --inject clsbias --trainable film`）。
