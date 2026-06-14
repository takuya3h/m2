# DAC-DETR 統合 再現ガイド (別サーバー / クリーン環境向け)

`third_party/` は `.gitignore` 済のため、DAC-DETR 本体 (huzhengdongcs/DAC-DETR) への
改修コードはこのリポジトリに含まれない。本ドキュメントと `docs/patches/dac_detr/*.patch`
を使えば、クリーンな clone から S0 ベンチ (s0_037-039) と同一構成を再現できる。

対象実験: **DAC-DETR / `dac_cdn_ice`** (= DAC + CDN denoising + ICE/IoU-aware
= 「DAC-DETR + Align」相当)。EgoSurgery-Tool 15 クラス, bbox-only, 統一 recipe。

リポジトリ内に既に含まれる関連物 (clone 不要):
- `scripts/post_process_dac_detr.py` — work_dir → EgoSurgery 標準証跡へ変換 (per-class AP / rare-common)
- `experiments/baselines/s0_037-039_dacdetr_bbox_seed*/` — 既存の証跡 (重み除く)
- `docs/patches/dac_detr/` — 本体改修パッチ 4 本

---

## 0. 環境 (検証済み)
- venv: `.venv-mmdet2` (Python 3.8, **torch 1.13.1+cu117**, mmcv-full 1.7, mmdet 2.25)。
- DAC-DETR は standalone Deformable-DETR 系 (mmdet/detrex 非依存。一部 util に mmcv/mmdet を使う)。
- GPU: 2x で DDP (per-GPU bs2 → effective bs4)。CUDA toolkit (nvcc) は torch の CUDA major と一致必須 (11.x)。

> 既存の `.venv-mmdet2` は Sense-X Co-DINO 9enc と共用。**`env_run.sh` は実行しないこと**
> (`pip install mmcv-full==1.7.1 mmdet==2.28.2` を含み既存環境を壊す)。op ビルドのみ手動で行う。

## 1. clone
```bash
cd third_party
git clone https://github.com/huzhengdongcs/DAC-DETR.git
cd DAC-DETR
```

## 2. 本体改修パッチを適用 (4 本)
リポジトリルートからの相対で `docs/patches/dac_detr/` にある。`third_party/DAC-DETR/` 直下で:
```bash
P=../../docs/patches/dac_detr
# git apply --recount は行番号に依存せず context で適用 (推奨)
git apply --recount "$P/01-main.py.patch"
git apply --recount "$P/02-models_deformable_detr.py.patch"
git apply --recount "$P/03-engine.py.patch"
git apply --recount "$P/04-models_backbone.py.patch"
# git 管理外/ずれる場合: patch -p1 --fuzz=5 < "$P/01-main.py.patch"  等
```
各パッチの内容:
| patch | ファイル | 変更 |
|---|---|---|
| 01 | `main.py` | `--num_classes` / `--finetune` 引数 + finetune ブロック (形状不一致キー除外で strict=False ロード, optimizer/epoch は読まない) |
| 02 | `models/deformable_detr.py` | `build()` で `args.num_classes` による num_classes 上書き |
| 03 | `engine.py` | `evaluate()` で COCOeval.precision から per-class AP を抽出し `per_class_ap_egosurgery.json` を dump |
| 04 | `models/backbone.py` | `import os` 追加 + ResNet50 ImageNet 重みをファイル欠如時 skip (COCO fine-tune が backbone を上書きするため) |

## 3. CUDA op (MultiScaleDeformableAttention) を py3.8 向けに再ビルド
```bash
cd models/ops
# setup.py 依存は torch/torchvision のみ → --no-deps で mmcv/mmdet 非接触 (既存環境保護)
TORCH_CUDA_ARCH_LIST="8.6" <repo>/.venv-mmdet2/bin/pip install . --no-build-isolation --no-deps -v
cd ../..
# 検証 (torch を先に import する。bare import は libc10.so 未解決で失敗=仕様):
<repo>/.venv-mmdet2/bin/python -c "import torch, MultiScaleDeformableAttention; print('op OK')"
```

## 4. EgoSurgery を COCO 形式に見せる symlink アダプタ
DAC-DETR の `datasets/coco.py` は `{coco_path}/train2017,val2017` と
`annotations/instances_{train,val}2017.json` を期待。EgoSurgery の `file_name` は
`val/09/..` のように split を含むため、画像 root は **両 split とも `data/raw/ego`** を指す。
```bash
M=<repo>            # 例: /home/ubuntu/slocal2/m2
cd third_party/DAC-DETR
mkdir -p data/egosurgery_coco/annotations
ln -sfn "$M/data/raw/ego" data/egosurgery_coco/train2017
ln -sfn "$M/data/raw/ego" data/egosurgery_coco/val2017
ln -sfn "$M/data/annotations/egosurgery_tool/instances_train.json" data/egosurgery_coco/annotations/instances_train2017.json
ln -sfn "$M/data/annotations/egosurgery_tool/instances_val.json"   data/egosurgery_coco/annotations/instances_val2017.json
```
EgoSurgery は 15 クラス (category id 0..14 連番) なので remap 不要。`--num_classes 15`。

## 5. COCO 事前学習重み (公式) を取得
`dac_cdn_ice r50 12ep` (COCO AP 50.9, log.txt の test_coco_eval_bbox[0]=0.5092 で provenance 確認可)。
Google Drive フォルダ `1BxzkDRsDDengzINr0jhVW-6Yp2OSOLs8` (README Models 表)。
```bash
<repo>/.venv/bin/python -m gdown --folder \
  "https://drive.google.com/drive/folders/1BxzkDRsDDengzINr0jhVW-6Yp2OSOLs8" \
  -O <repo>/data/external/weights/dac_cdn_ice_r50_12ep
# → checkpoint0011.pth (192MB)。*.pth は .gitignore 済 (リポジトリには含まれない)。
```
finetune 時に class_embed 28 キー (全 91 次元) が形状不一致で drop → reinit、残 604 tensor をロード。

## 6. 本番学習 (3 seed, DDP 2GPU, 12ep) — `/tmp/run_dac_prod.sh` 相当
seed ごとに以下を実行 (seed 42→s0_037, 123→s0_038, 456→s0_039):
```bash
cd third_party/DAC-DETR
W=<repo>/data/external/weights/dac_cdn_ice_r50_12ep/checkpoint0011.pth
CUDA_VISIBLE_DEVICES=0,1 <repo>/.venv-mmdet2/bin/python -m torch.distributed.run \
  --nproc_per_node=2 --master_port=29521 main.py \
  --output_dir /tmp/dac_work_seed42 --coco_path data/egosurgery_coco \
  --dataset_file coco --num_classes 15 --finetune "$W" \
  --with_box_refine --two_stage --dim_feedforward 2048 \
  --num_queries_one2one 900 --epochs 12 --lr_drop 11 --dropout 0.0 \
  --mixed_selection --look_forward_twice --batch_size 2 --num_workers 2 --seed 42
# 学習後 (本体 .venv で post-process → 標準証跡を生成):
<repo>/.venv/bin/python scripts/post_process_dac_detr.py \
  --work-dir /tmp/dac_work_seed42 \
  --exp-dir experiments/baselines/s0_037_dacdetr_bbox_seed42 \
  --command-sh "<上記コマンド>" --seed 42 --description dacdetr_bbox \
  --detector "DAC-DETR" --world-size 2 --server-name <host>
```
統一 recipe: AdamW lr 2e-4 (= 1e-4×linear_x2, backbone 0.1x) / effective bs4 /
12ep lr_drop@11 / eval=val / pycocotools は 0-1 スケール (detrex の 0-100 と違い /100 不要)。

## 7. ハマりどころ (再掲)
1. CUDA op は **py3.8 で再ビルド必須** (配布 build は py3.7)。import 時は torch 先読み。
2. `env_run.sh` 実行禁止 (mmcv/mmdet を上書きし 9enc 環境破壊)。op ビルドのみ。
3. `--resume` は strict=False でも class_embed 形状不一致 (91 vs 15) で落ちる →
   **`--finetune` を使う** (形状一致キーのみ keep, optimizer/epoch 読まない)。
4. `engine.evaluate` / 末尾は `model.module` 前提 = **DDP 必須**。単一プロセスだと
   AttributeError。スモークも `torch.distributed.run --nproc_per_node=1` で行う。
5. backbone は `./initmodel/resnet50-19c8e357.pth` を無条件 load → 欠如でクラッシュ →
   patch 04 で skip 可 (COCO fine-tune が backbone を上書きするので問題なし)。
6. dataset: `file_name` が split 込み → img root は両 split とも `data/raw/ego`。
7. per-class AP は DAC-DETR 標準出力に無い → patch 03 で COCOeval.precision から抽出。
8. metrics は val 評価。val 非存在クラス (Retractor 等) は per-class AP=NaN として
   rare/common 平均から除外 (post_process_dac_detr.py が処理)。

## 8. 他検出器について
Mr.DETR / Focus-DETR / Align-DETR / Stable-DINO / Relation-DETR / DI-MaskDINO も同様に
`third_party/` (gitignore) に置かれ、各 `scripts/post_process_*.py` で証跡化している。
これらの本体改修は本セッションでは未パッチ化 (DAC-DETR のみ)。必要なら同様に
`docs/patches/<detector>/` を追加する。
