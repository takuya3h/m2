# 検出器改善レシピ（Relation-DETR / EgoSurgery tool）

`third_party/Relation-DETR/` は **設計上 git 管理外**（`.gitignore:113 third_party/`）のため、
検出器学習 config の実体をここへミラーして再現性を担保する。実行時に参照される正本は
`third_party/Relation-DETR/configs/train_config_egosurgery_seed42_augstrong{,_hires}.py`。

## 基準レシピ（S0 parity・全 seed/手法で固定）

| 項目 | 値 |
|---|---|
| モデル | Relation-DETR ResNet50（`configs/relation_detr/relation_detr_resnet50_egosurgery.py`, 15クラス。正本は third_party 配下 <!-- docs-check: ignore-line -->） |
| 初期化 | COCO 事前学習 `relation_detr_resnet50_800_1333_coco_1x.pth`（class head のみ 91→15 で再初期化） |
| epochs | 12（LR step @10, ×0.1） |
| batch | per-GPU 2 × **2 GPU DDP = 実効 bs 4** |
| optimizer | AdamW lr=1e-4 wd=1e-4 betas=(0.9,0.999), max_norm=0.1 |
| precision | **fp32（mixed_precision='no'）** ← seed42 実測に一致。fp16 ではない |
| データ | EgoSurgery tool COCO（train 9657img/32272ann, val 1515） |

## 変更軸（比較トライアングル §6：1軸のみ変更）

- **frozen（源/baseline）**: `presets.detr`（S0 既定 aug）。ckpt = `checkpoints/incoming/seed{42,123,456}/best_ap.pth`。seed42 mAP=0.7303。
- **Method A（augstrong）**: `transforms=presets.strong_album`。**aug 強度のみ**変更（同解像度）。seed42 mAP=**0.7426**（+0.0124）。→ `train_config_augstrong.py`
- **Method C（augstrong+hires）**: `transforms=presets.strong_album_1200_2000`。aug＋**高解像度**（short-side〜1200, max2000）。→ `train_config_augstrong_hires.py`
- **Method B（hires のみ）** 参考: `presets.detr_1200`（解像度のみクリーン軸、`transforms/presets.py` に追加）。

## 起動コマンド（3-seed 反復）

```bash
cd third_party/Relation-DETR
RELDETR_OUTPUT_DIR=<PROJ>/experiments/detector_improve/augstrong_seed<SEED> \
EGO_ROOT=<PROJ>/data/raw/ego \
EGO_ANN_DIR=<PROJ>/data/annotations/egosurgery_tool \
RELDETR_COCO_CKPT=<PROJ>/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth \
CUDA_VISIBLE_DEVICES=0,1 ../../.venv-relation-detr/bin/accelerate launch --num_processes 2 \
    main.py --config-file configs/train_config_egosurgery_seed42_augstrong.py --seed <SEED>
```

`output_dir` は `RELDETR_OUTPUT_DIR` で env 上書き可能（1 config で seed42/123/456 を回す）。
オーケストレーションは `scripts/_detector_full_study.sh`（Phase I=Method A 3-seed / Phase II=hires C）。
特徴再抽出は `scripts/_extract_improved.sh <tag> <ckpt>`、phase 評価は `scripts/_run_phase_probe_3seed.sh` → `scripts/paired_sigma_3seed.py`（paired-σ §10.1）。
