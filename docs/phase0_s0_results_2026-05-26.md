# Phase-0 / S0 ベースライン: 実験結果詳細レポート

**作成日**: 2026-05-26
**対象期間**: 2026-05-22 〜 2026-05-26 (現在進行中)
**ブランチ**: `phase2`
**実行サーバー**: aolab (bengio, RTX A6000 ×2)

このレポートは、Notion「M2研究計画v2 - 研究運用ハブ」が定める
**Phase-0「統一 DDP 2GPU 方針による S0 正式ベースライン確立」** に対する、
2026-05-26 時点の全実験と結果を、後続フェーズ (S1〜S9) の Δ 基準点として
使えるよう詳細に記録するものである。

---

## 1. 研究計画上の位置づけ

- **Phase**: Phase-0 (中核仮説の検証に入る前の基準点固定)
- **目的**: Δ (相互改善幅) の科学的妥当性を担保するため、
  3 検出器 × 3 seed の S0 を **同一規格** (同一 split / 同一 test_cfg /
  同一 GPU 構成 / 同一 eval_recipe) で完走させる
- **中核仮説** (Notion「現在の研究状態」): 術具検出 × 手・術具文脈 × 工程認識
  × 時間/Exo 文脈の相互作用で最終性能が改善する可能性 — S1 以降の Δ で検証
- **S0 直後の判断ポイント #6**: Mask DINO vs Co-DETR の APr (稀少クラス AP =
  Skewer / Syringe の平均) 比較で、S1 以降の主検出器を決定

---

## 2. S0 実験規格 (全 9 ラン共通)

| 項目 | 値 | 由来 |
|---|---|---|
| データ split | train 9657 / val 1515 / test 4265 | EgoSurgery 公式 (`data/annotations/egosurgery_tool/instances_*.json`) |
| クラス数 | 15 (TOOL_CLASSES) | `src/egosurgery/constants.py` |
| 稀少クラス (rare) | Skewer, Syringe | 同上 RARE_CLASSES |
| GPU 構成 | DDP 2 GPU (RTX A6000 ×2) | §8.0 暫定運用 (4) |
| per-GPU batch_size | 2 | run_s0.sh |
| effective batch size | **4** (= 2 × 2) | eval_recipe.effective_batch_size |
| lr_scaling | `linear_x2` | run_s0.sh, eval_recipe.lr_scaling |
| epochs | 12 | run_s0.sh |
| Optimizer | mmdet 公式既定値 (検出器ごと) | mmdet 3.3.0 |
| test_cfg (locked-down) | score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6 | §15.4 A / 論文 Fujii+ 2024 §3.1 |
| 評価器 | COCO `bbox` mAP + 自前 AP_rare / AP_common 集計 | `MMDetTrainer._collect_best_metrics` |
| 起動方式 | **手動 launcher** (各 rank に CUDA_VISIBLE_DEVICES 個別指定) | scripts/run_s0.sh (torchrun 不使用) |
| 実装フレームワーク | mmdet 3.3.0 Runner | spec §2.1 の「Runner 不使用」からは逸脱、実 SOTA 再現を優先 |

### 検出器ごとの事前学習重みと config

| 検出器 | mmdet config | COCO 重み |
|---|---|---|
| Mask DINO 枠 (代替: DINO-4scale) | `dino/dino-4scale_r50_8xb2-12e_coco.py` | `dino-4scale_r50_8xb2-12e_coco.pth` |
| VarifocalNet | `vfnet/vfnet_r50_fpn_1x_coco.py` | `vfnet_r50_fpn_1x_coco.pth` |
| Co-DETR (CoDINO 5-scale) | `codino/co_dino_5scale_r50_lsj_8xb2_1x_coco.py` | `co_dino_5scale_r50_1x_coco.pth` |

Co-DETR は mmdet pip 同梱に含まれないため、
`third_party/mmdetection/projects/CO-DETR/` を `git clone` で取得し、
`configs/codino/` を mmdet パッケージ内 `.mim/configs/codino/` にコピー、
`codetr` Python モジュールは `sys.path` 経由で `import` 発火させる
(MMDetTrainer.setup() 内)。

---

## 3. 完了した S0 実験 (7/9, 2026-05-26 時点)

### 3.1 Mask DINO 枠 (DINO-4scale) × 3 seeds — **完走済**

| 実験 ID | seed | val/mAP | val/mAP_50 | val/mAP_75 | AP_rare | AP_common | best epoch |
|---|---:|---:|---:|---:|---:|---:|---:|
| s0_001_maskdino_bbox_seed42 | 42 | 0.668 | 0.793 | 0.729 | 0.7625 | 0.6022 | 12 |
| s0_002_maskdino_bbox_seed123 | 123 | 0.677 | 0.808 | 0.731 | 0.7520 | 0.6130 | 12 |
| s0_003_maskdino_bbox_seed456 | 456 | 0.670 | 0.795 | 0.731 | 0.7775 | 0.6018 | 12 |
| **3-seed mean** | — | **0.672** | **0.799** | **0.730** | **0.7640** | **0.6056** | — |
| 標準偏差 σ | — | 0.005 | 0.008 | 0.001 | 0.013 | 0.006 | — |

per_class_ap (s0_001 seed=42 を例示):

```
Bipolar Forceps : 0.577
Electric Cautery: 0.956
Forceps         : 0.307
Gauze           : 0.278
Hook            : 0.580
Mouth Gag       : 0.784
Needle Holders  : 0.818
Raspatory       : 0.473
Retractor       : NaN  (val に出現しない)
Scalpel         : 0.883
Scissors        : 0.652
Skewer          : 0.899   (rare)
Suction Cannula : 0.784
Syringe         : 0.626   (rare)
Tweezers        : 0.736
```

### 3.2 VarifocalNet × 3 seeds — **完走済 / 完了判定 #8 達成**

| 実験 ID | seed | val/mAP | val/mAP_50 | val/mAP_75 | AP_rare | AP_common | best epoch |
|---|---:|---:|---:|---:|---:|---:|---:|
| s0_004_varifocanet_bbox_seed42 | 42 | 0.618 | 0.757 | 0.681 | 0.7060 | 0.5566 | 12 |
| s0_005_varifocanet_bbox_seed123 | 123 | 0.616 | 0.758 | 0.672 | 0.6980 | 0.5557 | 12 |
| s0_006_varifocanet_bbox_seed456 | 456 | 0.614 | 0.751 | 0.674 | 0.7110 | 0.5519 | 12 |
| **3-seed mean** | — | **0.616** | **0.755** | **0.676** | **0.7050** | **0.5547** | — |
| 標準偏差 σ | — | 0.002 | 0.004 | 0.005 | 0.007 | 0.003 | — |

**完了判定 #8**: VarifocalNet mAP ≥ 0.458 → **達成** (3-seed 最低 0.614、しきい値を +15.6pt 上回る)

per_class_ap (s0_004 seed=42 を例示):

```
Bipolar Forceps : 0.480
Electric Cautery: 0.911
Forceps         : 0.238
Gauze           : 0.202
Hook            : 0.450
Mouth Gag       : 0.757
Needle Holders  : 0.812
Raspatory       : 0.509
Retractor       : NaN
Scalpel         : 0.842
Scissors        : 0.615
Skewer          : 0.876   (rare)
Suction Cannula : 0.733
Syringe         : 0.536   (rare)
Tweezers        : 0.687
```

### 3.3 Co-DETR (CoDINO 5-scale) × 3 seeds — **完走済**

| 実験 ID | seed | val/mAP | val/mAP_50 | val/mAP_75 | AP_rare | AP_common | best epoch |
|---|---:|---:|---:|---:|---:|---:|---:|
| s0_007_codetr_bbox_seed42 | 42 | 0.701 | 0.841 | 0.766 | 0.7515 | 0.6388 | 12 |
| s0_008_codetr_bbox_seed123 | 123 | 0.692 | — | — | 0.7340 | 0.6324 | 12 |
| s0_009_codetr_bbox_seed456 | 456 | 0.699 | — | — | 0.7420 | 0.6388 | 12 |
| **3-seed mean** | — | **0.697** | — | — | **0.7425** | **0.6366** | — |
| 標準偏差 σ | — | 0.005 | — | — | 0.009 | 0.004 | — |

per_class_ap (s0_007 seed=42、完走済):

```
Bipolar Forceps : 0.841
Electric Cautery: 0.896
Forceps         : 0.326
Gauze           : 0.275
Hook            : 0.582
Mouth Gag       : 0.787
Needle Holders  : 0.817
Raspatory       : 0.604
Retractor       : NaN
Scalpel         : 0.899
Scissors        : 0.704
Skewer          : 0.911   (rare)
Suction Cannula : 0.807
Syringe         : 0.592   (rare)
Tweezers        : 0.766
```

学習時間 (seed=42 実測): 04:32:56 開始 → 16:04:23 終了 = **約 11h31m / 12 epochs**。
GPU 0: ~67%, GPU 1: ~100% 利用、メモリ各 ~35 GB / 49 GB。

---

## 4. 検出器間 3-seed 比較 (全 9 件 完走後の確定値)

| 指標 | Mask DINO | VFNet | Co-DETR |
|---|---:|---:|---:|
| val/mAP (mean ± σ) | 0.672 ± 0.005 | 0.616 ± 0.002 | **0.697 ± 0.005** |
| **AP_rare** (Skewer + Syringe) | **0.764 ± 0.013** | 0.705 ± 0.007 | 0.743 ± 0.009 |
| AP_common (rare 以外 13 クラスの mean) | 0.606 ± 0.006 | 0.555 ± 0.003 | **0.637 ± 0.004** |

### 判断ポイント #6 (Mask DINO vs Co-DETR の APr 比較) — 確定

- APr(Mask DINO, 3-seed mean) = **0.7640**
- APr(Co-DETR,   3-seed mean) = **0.7425**
- **ΔAPr = APr(Co-DETR) − APr(Mask DINO) = −0.0215 (-2.15 pt)**
- 判定基準 (`prompts/phase2_part3_s0_execution_v2.md` §9 #6): |ΔAPr| ≥ 3pt なら
  S1 以降を Co-DETR に切替、それ未満なら Mask DINO 継続
- **結論: |ΔAPr| = 2.15 pt < 3 pt → S1 以降の主検出器は Mask DINO を継続**

副次的な観察:
- Co-DETR は mAP / AP_common で最良 (それぞれ +2.5pt / +3.1pt) だが、rare では Mask DINO に劣後
- 研究計画が稀少クラスの改善 (中核仮説の手・術具文脈 → 稀少クラス向上) を志向するため、
  rare で最良の Mask DINO を S1 以降のベースとする選択は仮説検証に整合的
- 上記は Notion「意思決定ログ」へ別途記録予定

---

## 5. 過去の失敗・退避フォルダ (履歴記録)

`experiments/baselines/_*` 配下は、いずれも Δ 比較には使えないが、
何が失敗してどう修正したかの監査用に保存している。

| 退避フォルダ | 内容 | 退避理由 |
|---|---|---|
| `_aborted_codetr_no_config` | s0_007〜009 旧 | Co-DETR config 不在で setup() 失敗 (mmdet 3.3.0 pip 同梱に projects/CO-DETR 含まれず) |
| `_aborted_s0_cuda_visible_misconfig` | 旧 S0 各種 | `.env` の `CUDA_VISIBLE_DEVICES=0` リークで全 rank が GPU0 集中 |
| `_failed_num_workers_zero` | 旧スモーク | num_workers=0 で hang |
| `_smoke_e3` | smoke_e3 1 epoch | E プラン手動 launcher の動作検証用スモーク (検証成功後に本番起動) |
| `_smoke_prior_simplehead` | 旧内蔵 SimpleDetectionHead 時代 | mAP 1.4% で実 SOTA 規格に届かず破棄 |
| `_smoke_v2_part3` | phase2 v2 prompts 時代 | DDP 化前の単 GPU 実験 |
| `_wrong_split_8_2_3` | 旧 8:2:3 split | 公式 EgoSurgery split (9657/1515/4265) に統一する前の実験 |

### 5.1 本セッションで踏んだ実装上のハマりどころ (修正済)

1. **`torchrun` で両 rank が GPU 0 に集中** — `LOCAL_RANK` 環境変数だけでは
   `torch.cuda.set_device()` が確実に効かない事象。各 rank を個別プロセスで
   起動し、`CUDA_VISIBLE_DEVICES` を rank 別に固定する **E プラン (手動 launcher)** に
   切り替えて解消 (`scripts/run_s0.sh`)。
2. **フォルダ重複生成 (s0_002 + s0_003 が同 seed で 2 個できる)** —
   両 rank が `ExperimentManager.setup()` を呼んだため。`MMDetTrainer.setup()` に
   `if self.rank == 0:` ガード + `broadcast_object_list` で exp_dir を rank 間共有。
3. **rank 1 が `self.manager = None` のまま `_write_metrics()` 到達して AttributeError** —
   `run()` 冒頭にも `if self.rank != 0 or self.manager is None: return {}` を追加。
4. **Co-DETR の `config` が mmdet pip pkg に同梱されない** —
   `third_party/mmdetection` を shallow clone、`projects/CO-DETR/configs/codino/` を
   mmdet pkg 内にコピー、`custom_imports` を `['codetr']` に書き換え、`sys.path` 経由で
   `import codetr` を発火。
5. **Co-DETR の `model.bbox_head` / `test_cfg` が list[N] (multi-head 構造)** —
   `_build_mmdet_cfg` と `_build_eval_recipe` を Co-DETR 分岐対応。
   eval_module='detr' に従い test_cfg list の index 0 (detr branch) を locked-down 上書き。

---

## 6. 完了判定の達成状況 (`prompts/phase2_part3_s0_execution_v2.md`)

| # | 判定内容 | 状態 | 根拠 |
|---|---|---|---|
| #2 | `bash scripts/run_s0.sh` が 9 実験を DDP 2 GPU で完走 | **OK** | Mask DINO ×3 + VFNet ×3 + Co-DETR ×3 全完走 |
| #3 | `s0_001_` 〜 `s0_009_` 存在 | **OK** | active 9 フォルダ揃う |
| #4 | 必須ファイル (config.yaml / metrics.json / per_class_ap.json / notes.md / server.txt / confusion_matrix.npy) | **OK** | 全 9 件で揃う |
| #8 | VarifocalNet mAP ≥ 0.458 | **OK** | 3-seed 最低 0.614 (+15.6pt) |
| #9 | Mask DINO の mAP が計測されている | **OK** | 3-seed mean 0.672 ± 0.005 |
| #10 | Co-DETR の mAP が計測されている | **OK** | 3-seed mean 0.697 ± 0.005 |
| #16 | 全 9 実験が同一 GPU 構成 (gpu_count=2) で測定 | **OK** | 全 9 件 gpu_count=2, effective_bs=4, lr_scaling=linear_x2, server=aolab 統一 |

**GPU 依存 7 判定 (#2/#3/#4/#8/#9/#10/#16) は全て達成。Phase-0 の S0 基準点が確定した。**

非 GPU 系判定 (#1/#5/#6/#7/#11〜#15/#17 等) は本セッション前に充足済の前提
(プロンプト Part 1/2 完了)。本レポートは GPU 依存 7 項目に絞って状態を示す。

---

## 7. 次の研究的アクション

1. ~~判定 #10 確定~~ — **済 (mean 0.697 ± 0.005)**
2. ~~判断ポイント #6 実行~~ — **済 (ΔAPr = -2.15pt < 3pt → Mask DINO 継続)**
3. **Notion「意思決定ログ」に S1 主検出器決定を記録** — 上記 #6 の結果と、
   rare/common のトレードオフ観察を 1 エントリとして残す。
4. **Phase-0 → Phase-1 への移行** — 中核仮説 (検出 × 手・術具文脈 ×
   工程認識 × 時間/Exo 文脈の相互作用) の最初の Δ 検証 (S1) に着手。
   Notion「現在の研究状態」に従い bbox + phase ラベルで進める。
   S1 のレシピは新規 `docs/phase1_s1_*.md` で計画する。
5. **既存失敗知見の回避ガード** — S2 (Tool+Hand fine-tuning) の
   catastrophic forgetting、S3 (class weights) の崩壊を、S1 着手時に
   設計レベルで避ける (unweighted baseline をデフォルト)。
6. **本レポートの凍結** — S1 着手時に本ファイルを「Phase-0 完了レポート」
   として凍結し、以降の変更は新規ファイルで行う。

---

## 8. 証跡 (再現性のためのファイル所在)

| 種別 | パス |
|---|---|
| 実験フォルダ (active) | `experiments/baselines/s0_001_` 〜 `s0_009_` |
| 退避フォルダ | `experiments/baselines/_*` (gitignore 対象) |
| 学習エントリーポイント | `python -m egosurgery.train stage=s0_tool_baseline ...` |
| 本番起動スクリプト | `scripts/run_s0.sh` (Mask DINO + VFNet + Co-DETR 9 実験) |
| Co-DETR 再走スクリプト | `/tmp/run_codetr_only.sh` (Co-DETR 3 seed のみ) |
| トレーナー本体 | `src/egosurgery/engines/mmdet_trainer.py` |
| 評価レシピ | `src/egosurgery/utils/eval_recipe.py` |
| 全実験共通 logs | `/tmp/s0_logs/<head>_seed<seed>_rank{0,1}.log` (本番) / `<head>_rerun_seed<seed>_rank{0,1}.log` (Co-DETR 再走) |
| 直近本番メインログ | `/tmp/s0_ddp_prod3.log` (Mask DINO+VFNet+旧 Co-DETR) / `/tmp/codetr_rerun.log` (Co-DETR 再走) |

### 関連 commit (主要)

- `e5d6dac` phase2 part3 DDP: MMDetTrainer DDP 対応 + run_s0.sh torchrun 化 + Co-DETR S0 追加
- `9c79822` phase2 part2 DDP: CoDETRHead 実装 + SyncBN 方針
- `bfabae1` phase2 part1 DDP: DistributedRepeatFactorSampler
- `3bf48a1` phase1 patch DDP: eval_recipe v2 (gpu_count/effective_batch_size/lr_scaling)
- `f9d055d` chore(env): .env.example から CUDA_VISIBLE_DEVICES=0 を削除 (事故再発防止)
- `d957c6b` chore(experiments): S0 やり直し前提で旧実験を退避

---

## 9. このレポートの更新ルール

- Co-DETR seed=123 / 456 完走時に「3.3 Co-DETR」表と「4. 検出器間比較」を更新する。
- 判断ポイント #6 確定時に「7. 次の研究的アクション」を確定値で書き直す。
- Phase-1 (S1) 着手時には本レポートは凍結し、新規 `docs/phase1_s1_results_*.md` を起こす。
