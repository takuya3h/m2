# Phase-0 / S0 検出器ベンチマーク拡張 実装計画

**作成日**: 2026-05-28
**対象**: 既存 S0 (Mask DINO + VFNet + Co-DETR ×3 seed = 9 ラン) に
新規 5 検出器 (ddq-detr / Sense-X co-dino 9enc / Relation-DETR / Stable-DINO / DI-MaskDINO)
を ×3 seed = 15 ラン追加し、計 14 検出器ファミリ → 8 ファミリのベンチマークに拡張する。

判定 #6 (Mask DINO vs Co-DETR の APr 比較で S1 主検出器を選定) を、
8 検出器 (Mask DINO / VFNet / Co-DETR / ddq-detr / Sense-X co-dino 9enc /
Relation-DETR / Stable-DINO / DI-MaskDINO) 版に拡張し、S1 主検出器を再選定する。

---

## 1. 重要な前提訂正 (本セッションで判明)

### 1.1 物理サーバーの実体

- `hostname`: **aolab**
- GPU: **NVIDIA RTX 6000 Ada Generation ×2** (compute_cap 8.9, 49 GB ea.)
- 既存 S0 全 9 件は `server.txt` = `aolab`、つまり最初から RTX 6000 Ada で測定済み

→ `scripts/run_s0.sh` のコメント「bengio = RTX A6000 ×2」、Notion「現在の研究状態」の
「bengio RTX A6000 x2 で統一」は実体と齟齬。本計画では **aolab/RTX 6000 Ada ×2** を
正として扱い、次回 commit のついでに run_s0.sh と Notion を訂正する。

### 1.2 同一サーバー条件は自動的に満たされる

新規 5 検出器も同じ aolab で走らせる前提なので、§8.0 条件 (1)「同一 Δ 比較群は
同一サーバーで測定」は新規追加でも自動的に保たれる。eval_recipe.gpu_count=2、
effective_batch_size=4、lr_scaling=linear_x2、server_name=aolab を全 24 ラン
(既存 9 + 新規 15) で揃える。

---

## 2. 5 検出器のフレームワーク互換性 (調査結果)

| # | 検出器 | フレームワーク | 既存 venv 互換性 | 推奨統合方式 |
|---|---|---|---|---|
| 1 | **ddq-detr** | mmdet 3.3.0 **同梱** | **OK** | MMDetTrainer に `detector="ddq"` 追加のみ |
| 2 | **Sense-X co-dino (9enc)** | mmdet **2.x** + mmcv_custom (repo 同梱) | **NG** (既存は mmdet 3.3.0) | 別 venv (mmdet 2.x) + 専用 trainer fork |
| 3 | **Relation-DETR** | **独自** (accelerate / albumentations / fvcore) | **NG** | 別 venv + 独自 main.py を fork |
| 4 | **Stable-DINO** | **detrex** (detectron2 拡張) | **NG** | 別 venv (detectron2 + detrex) + projects/stabledino fork |
| 5 | **DI-MaskDINO** | **detectron2** | **NG** | 別 venv (detectron2) + train_net.py fork |

### 2.1 既存環境との関係

既存 venv (`.venv/`, Python 3.11, mmdet 3.3.0, mmcv 2.1.0, torch 2.1.2+cu118) で
動くのは **ddq-detr のみ**。他 4 検出器はそれぞれ別 venv が必要で、追加で:

- **venv-mmdet2** (Sense-X Co-DETR): mmdet 2.x + mmcv-full 1.x + torch 1.13?
- **venv-relation-detr**: Relation-DETR repo の requirements.txt
- **venv-detectron2**: detectron2 + detrex + DI-MaskDINO/Stable-DINO 共通 (両者とも detectron2 ベースなので統合可能)

→ 既存 1 venv + 追加 3 venv = **計 4 venv 体制** になる。

### 2.2 各 repo の主要ファイル

| 検出器 | 公式 trainer エントリーポイント | EgoSurgery 適応で書き換える主な箇所 |
|---|---|---|
| ddq-detr | mmdet Runner (MMDetTrainer 統合可) | num_classes / test_cfg / data pipeline |
| Sense-X co-dino (9enc) | `tools/train.py` (mmdet 2.x) | num_classes / data root / lr scaling / test_cfg |
| Relation-DETR | `main.py` (accelerate launch) | configs/`*.py` の num_classes / dataset path |
| Stable-DINO | `tools/train_net.py` (detectron2) | `projects/stabledino/configs/stabledino_r50_4scale_12ep.py` |
| DI-MaskDINO | `train_net.py` (detectron2) | `configs/dimaskdino_r50_4scale_bs16_12ep.yaml` |

---

## 3. 統合方針

### 3.1 出力形式の統一 (ExperimentManager 互換 layer)

既存 9 ランの証跡フォーマットを 新規 15 ランでも維持する:

```
experiments/baselines/s0_NNN_<head>_bbox_seed<seed>/
├── config.yaml          # Hydra resolved config (もしくは framework 標準 config を yaml dump)
├── command.sh           # 起動コマンド再現
├── git_commit.txt       # commit SHA
├── metrics.json         # eval_recipe + val/mAP, val/mAP_50, val/mAP_75, AP_rare, AP_common
├── per_class_ap.json    # 15 クラス × bbox AP
├── notes.md             # 仮説 + 設定 + 結果 + 解釈
├── server.txt           # "aolab"
└── visualizations/
    └── confusion_matrix.npy
```

各 framework の標準出力をこのフォーマットに変換する thin wrapper を実装する。

### 3.2 採番計画

- s0_001〜009: 既存 (Mask DINO + VFNet + Co-DETR の old 8xb2 variant)
- **s0_010〜012**: ddq-detr × 3 seed
- **s0_013〜015**: Sense-X co-dino (9encoder) × 3 seed
- **s0_016〜018**: Relation-DETR × 3 seed
- **s0_019〜021**: Stable-DINO × 3 seed
- **s0_022〜024**: DI-MaskDINO × 3 seed

### 3.3 共通設定 (既存 S0 と揃える)

| 項目 | 値 |
|---|---|
| データ split | EgoSurgery 公式 (train 9657 / val 1515 / test 4265) |
| クラス数 | 15 (TOOL_CLASSES) |
| rare classes | Skewer, Syringe |
| GPU 構成 | DDP 2 GPU (aolab, RTX 6000 Ada) |
| per-GPU batch_size | 2 (effective 4) |
| lr_scaling | linear_x2 |
| epochs | 12 |
| test_cfg | locked-down (score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6) |
| Optimizer | 各 framework の COCO 用既定値 (`paper-faithful`) |

---

## 4. 着手順 (推奨)

**順序を「易→難」に並べる**ことで、フローを固めながら段階的に拡張する。
Co-DETR 統合で踏んだ罠 (multi-head / list test_cfg / num_classes 伝播) を
4 回繰り返さないため、各検出器で必ずスモーク (1 epoch / 1 seed) を打ってから本番。

### Phase A (既存 venv 内・最簡): ddq-detr

1. MMDetTrainer に `detector="ddq"` を追加 (_BASE_CFG / _WEIGHTS / aliases)
2. test_cfg / num_classes の分岐対応 (DDQ-DETR は単 head 構造のはず)
3. スモーク 1 epoch (~30-40 min)
4. 本番 3 seed (~25-30 h)
5. judge #6 を 4 検出器版に拡張して暫定再評価

### Phase B (別 venv 構築・mmdet 2.x): Sense-X co-dino (9encoder)

1. `venv-mmdet2` を `uv venv` で作成、Sense-X repo の requirements インストール
2. config 修正 (num_classes=15, data root, locked-down test_cfg, lr_scaling)
3. ExperimentManager 互換 wrapper (metrics.json / per_class_ap.json 出力)
4. スモーク → 本番 3 seed (~80 h、9encoder は重い)

### Phase C (別 venv: detectron2 共通): Stable-DINO + DI-MaskDINO

1. `venv-detectron2` を構築 (detectron2 + detrex)
2. **Stable-DINO**: projects/stabledino fork → config 修正 → スモーク → 本番 3 seed (~30 h)
3. **DI-MaskDINO**: configs/yaml 修正 → スモーク → 本番 3 seed (~40 h)
4. ExperimentManager 互換 wrapper は両者で共通化 (detectron2 標準の `metrics.json` ↔ EgoSurgery `metrics.json` 変換)

### Phase D (別 venv・独自): Relation-DETR

1. `venv-relation-detr` を構築
2. configs/`relation_detr/relation_detr_resnet50_800_1333_coco_1x.py` を fork
3. ExperimentManager 互換 wrapper (Relation-DETR の main.py 出力を変換)
4. スモーク → 本番 3 seed (~30-40 h)

### 全体所要時間 (機械時間のみ、人手作業時間は別)

| Phase | 検出器 | per-seed 学習時間 (推定) | 3 seed 合計 |
|---|---|---|---|
| A | ddq-detr | ~9 h | **~27 h** |
| B | Sense-X co-dino 9enc | ~26 h (既存 codetr 11.5h × 1.5×2 = encoder layer 9/6 比 + 8xb2/8xb2) | **~80 h** |
| C-1 | Stable-DINO | ~10 h | **~30 h** |
| C-2 | DI-MaskDINO | ~13 h | **~40 h** |
| D | Relation-DETR | ~10-12 h | **~30-36 h** |
| **合計** | — | — | **~200-220 h ≒ 8-9 日** |

(judge6 再評価は各 Phase 完走時に自動実行)

---

## 5. リスクと対策

| リスク | 影響度 | 対策 |
|---|---|---|
| Sense-X の mmdet 2.x が CUDA 11.8 / torch 2.1 と非互換 | 高 | `venv-mmdet2` は torch 1.13.1 + CUDA 11.7 で構築 (mmcv-full 1.7.x 用) |
| detectron2 が CUDA 11.8 でビルド失敗 | 中 | `pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu118/torch2.1/index.html` の pre-built wheel を使う |
| Relation-DETR の独自 main.py が DDP 起動と相性悪 | 中 | accelerate launch を試す。NG なら single GPU で 6 epoch × 2 = 12 epoch 相当に分割実行 |
| Stable-DINO / DI-MaskDINO が detrex の特定 commit に依存 | 中 | 各 repo の README が指定する detrex commit hash を pin |
| 学習時間が 1 週間超 → 共有サーバーで他ユーザーに迷惑 | 中 | 1 検出器ずつ逐次。各検出器の間に状況確認を入れる |
| Co-DETR 統合と同様の罠 (multi-head / list test_cfg) | 高 | 各検出器のスモーク 1 epoch を必ず先に実行。本番起動前に metrics.json が正しい形で出ることを確認 |

---

## 6. 判断ポイント #6 の拡張版

既存判定:
- ΔAPr(Co-DETR vs Mask DINO) = -2.15 pt < 3 pt → S1 は Mask DINO 継続

拡張後 (8 検出器版):
- 8 検出器の APr (Skewer + Syringe mean) を 3-seed mean で比較
- 最高 APr の検出器を S1 主検出器に選定
- ただし mAP も同時に評価し、AP_rare と mAP のどちらを重視するかは
  Notion「意思決定ログ」で別途記録

予想される傾向 (調査時点の知識):
- Stable-DINO は DINO ベースで稀少クラスに強い可能性
- DI-MaskDINO は detection-segmentation 統合で稀少クラスの再現性向上の主張
- Relation-DETR は relation prior で稀少クラス改善の見込み
- → どれが最良か事前予測困難なので実測が意味を持つ

---

## 7. ユーザ承認が必要な意思決定

1. **本計画全体の方針承認** (Phase A→B→C→D の順、4 venv 体制、~200-220 h GPU 占有)
2. **各 Phase 完走時に judge #6 を更新する運用承認** (中間結果が出るたび主検出器候補が変動する可能性)
3. **学習時間 1 週間超を許容するか** (S1 着手はこれが終わるまで停止)
4. **Sense-X co-dino (9enc) と既存 codetr (s0_007-009) は別検出器として併存** で良いか (重複ではない、encoder layer 数が違う variant)

---

## 8. 証跡 (Phase A 着手時に追記予定)

- ddq-detr 統合の MMDetTrainer 差分: TBD
- 各 venv の構築 lockfile: TBD
- 各 framework 用 wrapper: TBD
