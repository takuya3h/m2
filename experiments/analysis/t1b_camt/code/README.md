# T1b-CA-MultiToken(camt) モデル/config の追跡コピー（再現性用）

`third_party/Relation-DETR/` は gitignore 配下のため複製（実行時は third_party 側に配置）。
decoder 層は既存 `models/bricks/relation_decoder_phaseca.py`（single-token CA と共有）を無改造で再利用。

- `relation_detr_phasecrossattn_mt.py.txt` → `third_party/Relation-DETR/models/detectors/`（拡張子 .txt を除く）
- `relation_detr_resnet50_egosurgery_t1b_camt.py.txt` → `third_party/Relation-DETR/configs/relation_detr/`

実行: `bash scripts/run_t1b_camt_3seed_efros.sh`（`scripts/train_t1b.py --inject camt --trainable film`）。
