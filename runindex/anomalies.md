# anomalies — 規約から外れたもの・判断を保留したもの

`tools/harvest_runindex.py` が自動生成する。手で編集しない。

## 1. 除外した run

`experiments/README.md` に `_` 接頭辞が「解析対象外」を意味するという規約は
**明文化されていない**。以下はディレクトリ名の意味からの判断であり、
規約に基づくものではない。**除外規約の明文化を推奨する。**

除外 48 run / 全 749 run（削除ではなくフラグ）

| exclusion_reason | runs | 対象 |
|---|---:|---|
| `failed_run` | 6 | `experiments/phase0/_failed_s3_weighted` |
| `identity_check` | 24 | `experiments/hand2det_dev`, `experiments/transfer` |
| `known_bad_split` | 6 | `experiments/baselines/_wrong_split_8_2_3` |
| `mislabeled_arm_all_not_film` | 2 | `experiments/transfer` |
| `smoke_test` | 7 | `experiments/_smoke_prior`, `experiments/baselines/_smoke_ddq` |
| `wrong_frozen_source` | 3 | `experiments/phase1` |

### 1.1 `phase0/_failed_s3_weighted/` の 6 run — 運用上の欠陥

**repo 上で失敗が確認できる唯一の run 群だが、Notion 実験Run台帳では
`Status='failed'` が 616 行中 0 件。失敗が台帳に反映されない運用上の欠陥がある。**

- 6 run とも `metrics.json` が空 `{}` で、学習が完走していない
- うち 3 つ（`_004_partial` / `_005_partial` / `_006_partial`）は命名規約にも従わない
- 成功 run だけが台帳に載る運用では、失敗率・試行回数・打ち切り理由を
  後から復元できない。Δ の解釈（何回試して何回失敗したか）が検証不能になる
- 対処案: `ExperimentManager` に失敗時の Status 書き込みを配線する、
  または収穫時に `metrics.json` 空を failed として台帳へ補完投稿する

## 2. split を確定できなかった run

指標キーの接頭辞から split を確定できない run。**推測していない**。

確定不能 35 run / 全 749 run

| split_provenance | runs |
|---|---:|
| `not_determinable_no_eval_recipe` | 29 |
| `not_determinable` | 6 |

残るのは **`metrics.json` が空 `{}` の run** である。指標が 1 つも無いため
「どの split で評価したか」が原理的に存在しない。正本 §16.7 の既定（§13）も
指標を持つ run にのみ適用しており、これらには適用していない。

| path | excluded | exclusion_reason |
|---|---|---|
| `experiments/phase0/_failed_s3_weighted/_004_partial` | True | `failed_run` |
| `experiments/phase0/_failed_s3_weighted/_005_partial` | True | `failed_run` |
| `experiments/phase0/_failed_s3_weighted/_006_partial` | True | `failed_run` |
| `experiments/phase0/_failed_s3_weighted/s3_001_phase_frame_seed42` | True | `failed_run` |
| `experiments/phase0/_failed_s3_weighted/s3_002_phase_frame_seed123` | True | `failed_run` |
| `experiments/phase0/_failed_s3_weighted/s3_003_phase_frame_seed456` | True | `failed_run` |
| `transfer/hc_seed123` | False | `None` |
| `transfer/hc_seed42` | False | `None` |
| `transfer/hc_seed456` | False | `None` |
| `transfer/oracle_phase_seed123` | False | `None` |
| `transfer/oracle_phase_seed42` | False | `None` |
| `transfer/oracle_phase_seed456` | False | `None` |
| `transfer/t1b_ca_seed123_lecun` | False | `None` |
| `transfer/t1b_ca_seed42` | False | `None` |
| `transfer/t1b_ca_seed42_bengio` | False | `None` |
| `transfer/t1b_ca_seed456_lecun` | False | `None` |
| `transfer/t1b_ca_zeroctx_seed42` | False | `None` |
| `transfer/t1b_camt_all_seed123_efros` | False | `None` |
| `transfer/t1b_camt_all_seed42_efros` | False | `None` |
| `transfer/t1b_camt_all_seed456_efros` | False | `None` |
| `transfer/t1b_camt_seed123_efros` | False | `None` |
| `transfer/t1b_camt_seed42_efros` | False | `None` |
| `transfer/t1b_camt_seed456_efros` | False | `None` |
| `transfer/t1b_clsbias_pe_seed123_efros` | False | `None` |
| `transfer/t1b_clsbias_pe_seed42_efros` | False | `None` |
| `transfer/t1b_clsbias_pe_seed456_efros` | False | `None` |
| `transfer/t1b_clsbias_seed123_efros` | False | `None` |
| `transfer/t1b_clsbias_seed42_efros` | False | `None` |
| `transfer/t1b_clsbias_seed456_efros` | False | `None` |
| `transfer/t1b_filmonly_seed123` | False | `None` |
| `transfer/t1b_filmonly_seed42` | False | `None` |
| `transfer/t1b_filmonly_seed456` | False | `None` |
| `transfer/t1b_seed42_bengio` | False | `None` |
| `transfer/t1c_bidir_pilot_seed42` | False | `None` |
| `transfer/t1c_bidir_v2_pilot_seed42` | False | `None` |

## 3. host を確定できなかった run

確定不能 41 run

| host_raw | runs | 理由 |
|---|---:|---|
| `None` | 31 | server.txt 欠損かつ eval_recipe.server_name 無し |
| `aolab` | 10 | philip / ilya の双方が返すコンテナ内 hostname のため一意に特定不能 |

## 4. per_class_ap.json のクラス体系が 2 種類ある

ファイル名は `per_class_ap.json` だが、中身は 2 つの異なる体系が混在する。
**横断比較の際に混ぜてはならない。**

**ファイル名が `per_class_ap.json` でありながら中身が F1 の群があるため、
`per_class_kind` だけでなく `per_class_metric` を必ず参照すること。**
`per_class_source` に読み取り元の相対パスを保持している。

| per_class_kind | per_class_metric | runs | 内容 | 根拠 |
|---|---|---:|---|---|
| `phase` | `F1` | 545 | 9 クラスの工程別 **F1**（AP ではない） | `scripts/train_{b2a,t1a,s4_tecno,haux,taux,t1a_boundary,t1a_regiontraj}.py` が `best.get("phase_per_class_f1", {})` を `log_per_class_ap()` に渡している |
| `None` | `None` | 117 | `per_class_ap.json` が無い・空・パース失敗 | — |
| `tool` | `AP` | 66 | 15 クラスの術具 AP | `per_class_coco_map` / `COCOeval.precision` 由来 |
| `coco_map` | `AP` | 21 |  |  |

### metric を確定できなかった run: 0

なし。

## 5. NaN を含む run

`NaN` は標準 JSON として不正なため出力では `null` に変換した。
どのクラスが `NaN` だったかは `per_class_nan_classes` に保持している。

### NaN の意味（コードとデータから確定済み）

**「そのクラスがその評価 split の GT に存在せず、AP が定義できない」**

根拠 3 点:

1. `scripts/post_process_sensex_codino.py:97` が全クラスを `float('nan')` で初期化し、
   mmdet のログ表に現れたクラスだけを上書きする。mmdet は COCO の precision が
   `-1`（GT 無し）のとき `nan` を出力する。
2. `data/annotations/egosurgery_tool/instances_val.json` を全数集計すると
   **`Retractor` の GT が val split に 0 件**（train 2079 / val 0 / test 325）。
3. NaN になるクラスの組が run 群と完全に対応する（下表）。split が壊れている
   `_wrong_split_8_2_3` の run だけ NaN のクラスが違うことは、
   「NaN = その split に GT が無い」以外では説明できない。

| NaN のクラス | runs | 該当群 |
|---|---:|---|
| `Retractor` | 75 | `experiments/baselines`, `experiments/baselines/_legacy_score_thr_0`, `experiments/baselines/_smoke_ddq`, `experiments/hand2det_dev`, `experiments/transfer`, `transfer` |
| `Mouth Gag`, `Skewer` | 6 | `experiments/baselines/_wrong_split_8_2_3` |

### 平均の取り方への含意

`NaN` を 0 として平均すると mAP を過小評価する。`per_class_valid_count` を
分母に使うこと（15 固定にしない）。

## 6. 命名規約から外れた run

`<step>_<seq3>_<desc>_seed<N>` に一致しない run: 78

- `experiments/phase0/_failed_s3_weighted/_004_partial`
- `experiments/phase0/_failed_s3_weighted/_005_partial`
- `experiments/phase0/_failed_s3_weighted/_006_partial`
- `experiments/selection_noise_2026-07-29/runs/base_seed123_rep1`
- `experiments/selection_noise_2026-07-29/runs/base_seed123_rep2`
- `experiments/selection_noise_2026-07-29/runs/base_seed123_rep3`
- `experiments/selection_noise_2026-07-29/runs/base_seed42_rep1`
- `experiments/selection_noise_2026-07-29/runs/base_seed42_rep2`
- `experiments/selection_noise_2026-07-29/runs/base_seed42_rep3`
- `experiments/selection_noise_2026-07-29/runs/base_seed456_rep1`
- `experiments/selection_noise_2026-07-29/runs/base_seed456_rep2`
- `experiments/selection_noise_2026-07-29/runs/base_seed456_rep3`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed123_rep1`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed123_rep2`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed123_rep3`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed42_rep1`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed42_rep2`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed42_rep3`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed456_rep1`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed456_rep2`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed456_rep3`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed123_rep1`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed123_rep2`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed123_rep3`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed42_rep1`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed42_rep2`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed42_rep3`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed456_rep1`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed456_rep2`
- `experiments/selection_noise_2026-07-29/runs/bboxROI_seed456_rep3`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed123_rep1`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed123_rep2`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed123_rep3`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed42_rep1`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed42_rep2`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed42_rep3`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed456_rep1`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed456_rep2`
- `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed456_rep3`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed123_rep1`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed123_rep2`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed123_rep3`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed42_rep1`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed42_rep2`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed42_rep3`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed456_rep1`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed456_rep2`
- `experiments/selection_noise_2026-07-29/runs/handROImask2_seed456_rep3`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed123_rep1`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed123_rep2`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed123_rep3`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed42_rep1`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed42_rep2`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed42_rep3`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed456_rep1`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed456_rep2`
- `experiments/selection_noise_2026-07-29/runs/maskROI_seed456_rep3`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed123_rep1`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed123_rep2`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed123_rep3`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed42_rep1`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed42_rep2`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed42_rep3`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed456_rep1`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed456_rep2`
- `experiments/selection_noise_2026-07-29/runs/randROI_seed456_rep3`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed123_rep1`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed123_rep2`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed123_rep3`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed42_rep1`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed42_rep2`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed42_rep3`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed456_rep1`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed456_rep2`
- `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed456_rep3`
- `experiments/transfer/b2b_rescore_alpha0.5`
- `experiments/transfer/b2b_rescore_alpha1.0`
- `experiments/transfer/b2b_rescore_alpha2.0`

## 7. ディレクトリ名の `det<N>` / `p<N>` トークン — 大半は seed ではない

### 7.1 🔴 修正済みの誤読: `p010` は seed ではなくノイズ率

以前の実装は `(det|p)(\d+)` にマッチした数値を無条件に補助 seed として扱い、
**81 run に `seed_phase` を付けていた。うち 72 件は誤り**である。

一次証拠 (`command.sh` の実引数):

```
b2a_base_oracle_noise_p010_001_b2a_base_oracle_noise_p010_seed42/command.sh
  python scripts/train_b2a.py --seed 42 --epochs 50 --tool-source oracle \
    --tool-noise-rate 0.10 --description-override b2a_base_oracle_noise_p010
```

`p010` は `--tool-noise-rate 0.10`、すなわち**ノイズ率 0.10** であって seed ではない。
これを seed とみなすと、ノイズ水準という**条件**が反復軸に誤分類され、
`experiment_id` から剥がされて noise 0.10 / 0.20 / 0.30 が 1 実験に混ざる。

現在の判定は `command.sh` を一次証拠にする:

| 条件 | 判定 | provenance |
|---|---|---|
| `--tool-noise-rate` を持つ | ノイズ率。seed ではない | `p_token_is_noise_rate_by_command_sh` |
| `p<N>` == 末尾 `seed<N>` | 工程学習の seed (反復軸) | `p_token_equals_run_seed` |
| どちらでもない | **確定不能。null にする** | `p_token_not_determinable` |
| `det<N>` | 凍結検出器の指定 = **条件**。反復軸ではない | `det_token_is_backbone_condition` |

ノイズ系を除いた 27 run すべてで `p<N> == seed` であることを実測で確認した。

### 7.2 現在の内訳

| aux_token_provenance | run 数 |
|---|---:|

`seed_detector` または `seed_phase` が実際に付いた run: **29**

| path | seed (末尾) | seed_detector | seed_phase |
|---|---:|---:|---:|
| `experiments/transfer/hires_relation_detr_augstrong_hires_seed42_p123_001_hires_relation_detr_augstrong_hires_seed42_p123_seed123` | 123 | — | 123 |
| `experiments/transfer/hires_relation_detr_augstrong_hires_seed42_p42_001_hires_relation_detr_augstrong_hires_seed42_p42_seed42` | 42 | — | 42 |
| `experiments/transfer/hires_relation_detr_augstrong_hires_seed42_p456_001_hires_relation_detr_augstrong_hires_seed42_p456_seed456` | 456 | — | 456 |
| `experiments/transfer/hires_relation_detr_augstrong_seed42_p123_001_hires_relation_detr_augstrong_seed42_p123_seed123` | 123 | — | 123 |
| `experiments/transfer/hires_relation_detr_augstrong_seed42_p42_001_hires_relation_detr_augstrong_seed42_p42_seed42` | 42 | — | 42 |
| `experiments/transfer/hires_relation_detr_augstrong_seed42_p456_001_hires_relation_detr_augstrong_seed42_p456_seed456` | 456 | — | 456 |
| `experiments/transfer/hires_relation_detr_seed42_p123_001_hires_relation_detr_seed42_p123_seed123` | 123 | — | 123 |
| `experiments/transfer/hires_relation_detr_seed42_p42_001_hires_relation_detr_seed42_p42_seed42` | 42 | — | 42 |
| `experiments/transfer/hires_relation_detr_seed42_p456_001_hires_relation_detr_seed42_p456_seed456` | 456 | — | 456 |
| `experiments/transfer/t1a_3seed_det123_p123_aug_001_t1a_3seed_det123_p123_aug_seed123` | 123 | 123 | 123 |
| `experiments/transfer/t1a_3seed_det123_p123_frozen_001_t1a_3seed_det123_p123_frozen_seed123` | 123 | 123 | 123 |
| `experiments/transfer/t1a_3seed_det123_p42_aug_001_t1a_3seed_det123_p42_aug_seed42` | 42 | 123 | 42 |
| `experiments/transfer/t1a_3seed_det123_p42_frozen_001_t1a_3seed_det123_p42_frozen_seed42` | 42 | 123 | 42 |
| `experiments/transfer/t1a_3seed_det123_p456_aug_001_t1a_3seed_det123_p456_aug_seed456` | 456 | 123 | 456 |
| `experiments/transfer/t1a_3seed_det123_p456_frozen_001_t1a_3seed_det123_p456_frozen_seed456` | 456 | 123 | 456 |
| `experiments/transfer/t1a_3seed_det42_aug_001_t1a_3seed_det42_aug_seed42` | 42 | 42 | — |
| `experiments/transfer/t1a_3seed_det42_frozen_001_t1a_3seed_det42_frozen_seed42` | 42 | 42 | — |
| `experiments/transfer/t1a_3seed_det42_p123_aug_001_t1a_3seed_det42_p123_aug_seed123` | 123 | 42 | 123 |
| `experiments/transfer/t1a_3seed_det42_p123_frozen_001_t1a_3seed_det42_p123_frozen_seed123` | 123 | 42 | 123 |
| `experiments/transfer/t1a_3seed_det42_p42_aug_001_t1a_3seed_det42_p42_aug_seed42` | 42 | 42 | 42 |
| `experiments/transfer/t1a_3seed_det42_p42_frozen_001_t1a_3seed_det42_p42_frozen_seed42` | 42 | 42 | 42 |
| `experiments/transfer/t1a_3seed_det42_p456_aug_001_t1a_3seed_det42_p456_aug_seed456` | 456 | 42 | 456 |
| `experiments/transfer/t1a_3seed_det42_p456_frozen_001_t1a_3seed_det42_p456_frozen_seed456` | 456 | 42 | 456 |
| `experiments/transfer/t1a_3seed_det456_p123_aug_001_t1a_3seed_det456_p123_aug_seed123` | 123 | 456 | 123 |
| `experiments/transfer/t1a_3seed_det456_p123_frozen_001_t1a_3seed_det456_p123_frozen_seed123` | 123 | 456 | 123 |
| `experiments/transfer/t1a_3seed_det456_p42_aug_001_t1a_3seed_det456_p42_aug_seed42` | 42 | 456 | 42 |
| `experiments/transfer/t1a_3seed_det456_p42_frozen_001_t1a_3seed_det456_p42_frozen_seed42` | 42 | 456 | 42 |
| `experiments/transfer/t1a_3seed_det456_p456_aug_001_t1a_3seed_det456_p456_aug_seed456` | 456 | 456 | 456 |
| `experiments/transfer/t1a_3seed_det456_p456_frozen_001_t1a_3seed_det456_p456_frozen_seed456` | 456 | 456 | 456 |

### 7.3 🔴 未解決: `noise000` という名前が実態と食い違う

`b2a_ro_oracle_noise000` は名前が「ノイズ 0.00」を意味するように読めるが、
12 run の `command.sh` が渡している `--tool-noise-rate` は実際には
**0.05 / 0.10 / 0.20 / 0.30 の 4 通り**である。

- 名前を信じて「ゼロノイズの対照」として使うと、**4 水準の混合**と比較することになる。
- `description` が 1 つしか無いため、`experiment_id` はこの 12 run を 1 実験に束ねる。
  `n_command_variants` 列が 4 になるので機械的には検出できるが、
  **この実験の集約値 (mean / pstd) は 4 条件の混合であり、意味を持たない**。
- 規約と実データのどちらを正とするかは harvester が決めることではないため、
  ここに記録するに留める。ディレクトリ名の改名は `experiments/` の変更にあたる。

## 8. prefix 無しキーと prefix 付きキーの値が食い違った run

該当 0 run（食い違いがあれば両方を保持している）


## 9. 標準規約 (1 run 1 dir) に従わない群

`metrics.json` を持たないため run として収穫していない。
**取りこぼした run 数は 0**（これらの配下に `metrics.json` は 1 つも無い）。
個別 adapter は次段階に回す。

| group | ファイル数 | 中身の種別 | 術具 per-class 指標 |
|---|---:|---|---|
| `_orphan_no_metrics` | 9 | (未調査) | (未調査) |
| `_smoke_proptest_20260804_223211` | 0 | (未調査) | (未調査) |
| `ablations` | 1 | `.gitkeep` のみ | 未着手 scaffold |
| `analysis` | 96 | EDA レポート / 図 (png) / CSV / JSON | **あり**: `detector_sanity/reldetr_seed42_val_perclass.json` (COCO 形式 `AP`/`AP50`/`AP75`/`AP_s`/`AP_m` 等 13 キー)、`signature_subset_detector_compare/results.json` (`per_class` キー) |
| `audit` | 3 | `audit_report.json` × 3 | なし (`inject` / `trainable` / `n_trainable_params` 等の学習設定監査) |
| `detector_improve` | 118 | `label_names.txt` / `val_perclass.json` | **あり**: `augstrong_seed42/val_perclass.json` (COCO 形式 13 キー) |
| `final` | 1 | `.gitkeep` のみ | 未着手 scaffold |
| `g2_main_2026-07-29` | 5 | `csv/` `json/` `prereg/` `HANDOVER_lecun.md` | なし (`f_roi_stats_{val,test}.json` は ROI 統計) |

### 次段階への申し送り

**現在 `per_class_metric=AP` の run は 62 しか無い。**
上表の `val_perclass.json` 系は術具 per-class 指標を含むため、
adapter を書けば貴重な追加ソースになる。

また `analysis/step_c_coupling_analysis/*.json`（12 ファイル）は
`model` / `seed` / **`split`** / `ckpt` / `phase` / `mAP` を持ち、
**`split` を明示している**。split が確定できない run の補強材料になりうる。

## 10. 警告が出た run の内訳

| 警告 | 件数 |
|---|---:|
| run 名が命名規約 <step>_<seq3>_<desc>_seed<N> に一致しない | 78 |
| per_class_ap.json が存在しない | 75 |
| val と test の指標が共存する。primary（best 選択元）は val。test 側は metrics_by_split['...'] に保持している。 | 69 |
| per_class_ap.json が空 ({...}) | 34 |
| ディレクトリ名の p010 は seed ではない。command.sh が --tool-noise-rate を渡しており、ノイズ率 0.01 を指す。seed_phase には入れない。 | 24 |
| ディレクトリ名の p020 は seed ではない。command.sh が --tool-noise-rate を渡しており、ノイズ率 0.02 を指す。seed_phase には入れない。 | 24 |
| ディレクトリ名の p030 は seed ではない。command.sh が --tool-noise-rate を渡しており、ノイズ率 0.03 を指す。seed_phase には入れない。 | 24 |
| config.yaml のパースに失敗: ConstructorError | 15 |
| host '...' は実サーバーを一意に特定できない。host は null にした。 | 10 |
| run 名に seq (3 桁連番) が無い別系統の命名: base_seed<N>。step には description を充てた。 | 9 |
| run 名に seq (3 桁連番) が無い別系統の命名: bboxROI_seed<N>。step には description を充てた。 | 9 |
| 同一 (group, step, description, split) 内で eval_recipe_id が 2 通りに食い違う。評価条件が違う run を束ねないため experiment_id を #None で分離した。 | 6 |
| 同一 (group, step, description, split) 内で eval_recipe_id が 2 通りに食い違う。評価条件が違う run を束ねないため experiment_id を #a63aecae で分離した。 | 6 |
| metrics.json が空 ({...}) | 6 |
| ディレクトリ名の p0 が末尾 seed<N> と一致せず、command.sh にノイズ引数も無い。seed か否かを確定できないため seed_phase は null にした。 | 6 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1b_ca_seed<N>。step には description を充てた。 | 4 |
| config.yaml のパースに失敗: ParserError | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: shuffleROI_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: bboxROI_handROIbbox2_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: handPresence_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: handROIbbox2_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: handROIbbox4_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: handROImask2_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: maskROI_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: randROI_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: _identity_ctrl_4ch_real_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: _identity_ctrl_4ch_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: _identity_ctrl_5ch_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: _identity_inj_4ch_real_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: _identity_inj_4ch_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: _identity_inj_5ch_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: _p0_identity_ctrl_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: _p0_identity_inj_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: hc_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: oracle_phase_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1b_camt_all_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1b_camt_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1b_clsbias_pe_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1b_clsbias_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1b_filmonly_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: hand2det_1ep_4ch_all_seed<N>。step には description を充てた。 | 1 |
| run 名に seq (3 桁連番) が無い別系統の命名: hand2det_1ep_4ch_film_seed<N>。step には description を充てた。 | 1 |
| run 名に seq (3 桁連番) が無い別系統の命名: hand2det_4ch_film_inj_seed<N>。step には description を充てた。 | 1 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1b_ca_zeroctx_seed<N>。step には description を充てた。 | 1 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1b_seed<N>。step には description を充てた。 | 1 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1c_bidir_pilot_seed<N>。step には description を充てた。 | 1 |
| run 名に seq (3 桁連番) が無い別系統の命名: t1c_bidir_v2_pilot_seed<N>。step には description を充てた。 | 1 |

## 11. 🔴 要対処: 乱数で per-class AP を生成するコードが残っている

`src/egosurgery/engines/trainer.py:273-278`

```python
rng = np.random.default_rng(int(self.cfg.seed))
per_class_ap = {
    cls: round(float(rng.uniform(0.05, 0.85)), 4) for cls in TOOL_CLASSES
}
self.manager.log_per_class_ap(per_class_ap)
```

この dummy Trainer は **乱数を `mAP` として `metrics.json` に書く**。
`CLAUDE.md` の「metrics / mAP 等の数値を絶対に捏造しない」に照らして危険。
`cfg.experiment.step` が s0/s1/s2 以外のとき dummy Trainer が選ばれる。

### 現時点の混入は 0 件（検証済み）

`tools/verify_no_dummy_metrics.py` が 2 系統で検査する:

1. **語彙照合** — dummy 側の `TOOL_CLASSES` は `Needle_Holders` / `Retractors` /
   `Clip_Applier` / `Suction` / `Electrocautery` / `Needle` / `Thread` という
   **別の語彙**を使う。実データ 2 体系のどちらとも一致しない。
2. **値の再現照合** — 既知 seed で `np.random.default_rng(seed).uniform(0.05, 0.85)`
   を再現し、`per_class_ap.json` と完全一致するものを探す。

結果: **混入 0 件**。experiments/ の per-class 指標は全て実評価器由来。

**このタスクではコードを変更していない。**
dummy Trainer の削除またはガード追加は別タスクで検討すること。
再検証: `python tools/verify_no_dummy_metrics.py`（`make runindex` に組込済）

### 11.1 🔴 検査の死角 — mAP を持つが術具 per-class を持たない run

上の 2 系統（語彙照合・値再現）は **`per_class_ap.json` に依存する**。
mAP 系の指標を持つのに術具 per-class（15 クラス）を持たない run は、
どちらの検査でも判定できない。**個別確認が要る対象**として列挙する。

該当 39 run

| path | mAP 系のキー | entrypoint | commit |
|---|---|---|---|
| `experiments/hand2det_dev/_identity_ctrl_4ch_real_seed123` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_real_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_real_seed456` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_seed123` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_seed456` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_ctrl_5ch_seed123` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_ctrl_5ch_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_ctrl_5ch_seed456` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_4ch_real_seed123` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_4ch_real_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_4ch_real_seed456` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_4ch_seed123` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_4ch_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_4ch_seed456` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_5ch_seed123` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_5ch_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/_identity_inj_5ch_seed456` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/hand2det_1ep_4ch_all_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/hand2det_dev/hand2det_4ch_film_inj_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_hand2det.py` | `0ea33cac65` |
| `experiments/transfer/_p0_identity_ctrl_seed123` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_t1b.py` | `0ea33cac65` |
| `experiments/transfer/_p0_identity_ctrl_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_t1b.py` | `0ea33cac65` |
| `experiments/transfer/_p0_identity_ctrl_seed456` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_t1b.py` | `0ea33cac65` |
| `experiments/transfer/_p0_identity_inj_seed123` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_t1b.py` | `0ea33cac65` |
| `experiments/transfer/_p0_identity_inj_seed42` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_t1b.py` | `0ea33cac65` |
| `experiments/transfer/_p0_identity_inj_seed456` | `final_mAP`, `init_mAP`, `mAP` | `scripts/train_t1b.py` | `0ea33cac65` |
| `experiments/transfer/b2b_rescore_alpha0.5` | `mAP_baseline`, `mAP_rescored` | — | `a697d90b88` |
| `experiments/transfer/b2b_rescore_alpha1.0` | `mAP_baseline`, `mAP_rescored` | — | `a697d90b88` |
| `experiments/transfer/b2b_rescore_alpha2.0` | `mAP_baseline`, `mAP_rescored` | — | `a697d90b88` |
| `experiments/transfer/t1b_phasefilm_001_t1b_phasefilm_seed123` | `control_init_mAP`, `control_mAP`, `init_mAP`, `mAP` | `scripts/postprocess_t1b.py` | `a697d90b88` |
| `experiments/transfer/t1b_phasefilm_002_t1b_phasefilm_seed456` | `control_init_mAP`, `control_mAP`, `init_mAP`, `mAP` | `scripts/postprocess_t1b.py` | `a697d90b88` |
| `transfer/hc_seed42` | `control_init_mAP`, `control_mAP`, `init_mAP`, `mAP` | — | `—` |
| `transfer/t1b_ca_zeroctx_seed42` | `init_mAP`, `mAP` | — | `—` |
| `transfer/t1b_camt_all_seed123_efros` | `control_init_mAP`, `control_mAP`, `final_mAP`, `init_mAP`, `mAP` | — | `—` |
| `transfer/t1b_camt_all_seed42_efros` | `control_init_mAP`, `control_mAP`, `final_mAP`, `init_mAP`, `mAP` | — | `—` |
| `transfer/t1b_camt_all_seed456_efros` | `control_init_mAP`, `control_mAP`, `final_mAP`, `init_mAP`, `mAP` | — | `—` |
| `transfer/t1b_camt_seed42_efros` | `control_init_mAP`, `control_mAP`, `final_mAP`, `init_mAP`, `mAP` | — | `—` |
| `transfer/t1b_clsbias_seed456_efros` | `control_init_mAP`, `control_mAP`, `final_mAP`, `init_mAP`, `mAP` | — | `—` |
| `transfer/t1b_seed42_bengio` | `control_init_mAP`, `control_mAP`, `init_mAP`, `mAP` | — | `—` |

`tools/verify_no_dummy_metrics.py --strict` はこの死角が 1 件でもあれば
異常終了する。`make runindex` は非 strict で実行し、警告として表示する。

#### 11.1.1 `t1b_phasefilm_{001,002}` の個別確認結果

3 つの独立した検証（コード経路 / 値の性質 / 証跡の整合）を、いずれも
「実評価器由来である」という主張を**反証する**目的で実施した。
**3/3 が反証に失敗し、`real_evaluator`（確信度 high）で一致した。**

反証を退けた根拠:

1. **到達不能性** — `command.sh` は `python scripts/postprocess_t1b.py`。
   dummy Trainer は `src/egosurgery/train.py::_select_trainer` 経由でしか
   選ばれず、それは `python -m egosurgery.train` でしか実行されない。
2. **値域の外** — seed 0..100000 を全探索した結果、
   `np.random.default_rng(s).uniform(0.05,0.85,15).mean()` の最大値は
   **0.6907**（seed 98115）。**0.70 を超える seed は 1 つも存在しない**。
   観測値 0.7292 / 0.7217 は生成器の到達可能範囲の外にある。
   直接照合でも seed123 -> 0.45405 / seed456 -> 0.43498 で不一致。
3. **精度の不整合** — dummy は各クラス AP を 4 桁、mAP を 6 桁に丸める
   (`trainer.py:276,299`)。観測値は `0.7291778095772903` と float64 の全桁。
4. **キー形状の不一致** — dummy が返すのは `val/loss` `val/accuracy`
   `val/mAP` `mAP` のみ。観測されたのは `control_init_mAP` `delta_control`
   `injection_effect` 等で、契約が異なる。
5. **`epoch = -1`** — dummy は `for epoch in range(1, epochs+1)` なので
   0 以下を出せない。-1 は「warm-start init が best」を表す番兵値。
6. **ビットレベル再現** — `transfer/t1b_camt_all_seed456_efros/`
   `injected_result.json` の `init_per_class_coco_map` を `np.nanmean` すると
   **0.7216586914703580 と完全一致**。実 COCO per-class AP から再構成できる。
   その per-class は EgoSurgery-Tool の 15 クラスで `Retractor = NaN`（GT 0 件）。

**ただし証跡としては不完全である（3 レンズが独立に指摘）:**

- 🔴 **一次成果物が消失** — `postprocess_t1b.py` が読む
  `experiments/transfer/t1b_seed{123,456}/t1b_result.json` が存在せず、
  commit もされていない。再現には元データが要る。
- 🔴 **provenance の欠陥** — `git_commit.txt` は `a697d90` を記録するが、
  **その commit に `scripts/postprocess_t1b.py` は存在しない**
  (`git ls-tree -r a697d90 | grep t1b` が 0 件)。記録された commit では
  この run を再現できない。
- 🔴 **数値が退化している** — `mAP == init_mAP` かつ
  `delta_detection = delta_control = injection_effect = 0.0`、`epoch = -1`。
  これは T1b の訓練効果ではなく **warm-start(S0-frozen) 時点の評価**を
  そのまま記録したもの。改善の証拠として引用してはならない。
- `eval_recipe` が両 `metrics.json` に不在。学習/評価ログも残っていない
  （兄弟の camt / clsbias 系にはログがある）。

**結論**: 捏造値ではない（dummy Trainer 由来ではない）が、
**再現不能かつ Δ=0 の退化した記録**であり、解析に使う前に上記 3 点の解消が要る。

## 12. experiments/README.md と実態の乖離

README は step 識別子を **s0〜s9 / a1〜a7（17 種）** と規定しているが、
実測は **189 種**。README に無い以下の系統が存在する。

| 系統 | step 識別子の種類 | run 合計 | 例 |
|---|---:|---:|---|
| `b1` | 1 | 6 | `b1_mtl` |
| `b2a` | 74 | 265 | `b2a_det2phase_toolpresence`, `b2a_ro_oracle_noise000` |
| `t1a` | 56 | 132 | `t1a_deep_3s10l96f`, `t1a_region_only` |
| `t1b` | 9 | 23 | `t1b_ca`, `t1b_camt_all` |
| `taux` | 5 | 15 | `taux_mingru_nonek3`, `taux_tecno_deltak3` |
| `haux` | 6 | 18 | `haux_hand_count_oracle`, `haux_hand_geom_oracle` |
| `hires` | 9 | 9 | `hires_relation_detr_augstrong_hires_seed42_p123`, `hires_relation_detr_augstrong_hires_seed42_p42` |

また README は 6 カテゴリ（`baselines` / `phase0` / `phase1` / `ablations` /
`transfer` / `final`）を規定するが、実際に run があるのは 4 つで、
`ablations` と `final` は空。逆に README に無い `_smoke_prior` に run がある。

**このタスクでは README を変更していない。** 規約の更新は別タスク。

## 13. 正本 §16.7 の既定と、その例外である test 評価 run

M2研究計画 §16.7（優先度 A 検証結果, 2026/05/29 追加）§16.7.1 に記録がある:

> **§8 訓練スクリプトに関する補足**: val_evaluator の ann_file は
> `instances_val.json`、`prefix='val'`（mmdet_config.py:314-320）のため、
> `metrics.json` / `per_class_ap.json` はすべて **val split の数値**。
> test split は未評価（最終報告用に温存、Δ 判定は val で行う設計）。

ローカル写し: `docs/m2_plan_rewrite/sections/19_epoch_16.md` L161 /
`docs/m2_plan_rewrite/m2_plan_v2_full.md` L1561

これを split の既定値とし、`provenance.split = from_plan_section_16_7` を記録する。
ただし **指標が 1 つもない run には適用しない**（評価されていないため null のまま）。

既定を適用した run: 104

| path | 指標キー |
|---|---|
| `experiments/hand2det_dev/_identity_ctrl_4ch_real_seed123` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_real_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_real_seed456` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_seed123` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_ctrl_4ch_seed456` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_ctrl_5ch_seed123` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_ctrl_5ch_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_ctrl_5ch_seed456` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_4ch_real_seed123` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_4ch_real_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_4ch_real_seed456` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_4ch_seed123` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_4ch_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_4ch_seed456` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_5ch_seed123` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_5ch_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/_identity_inj_5ch_seed456` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/hand2det_1ep_4ch_all_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/hand2det_1ep_4ch_film_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/hand2det_dev/hand2det_4ch_film_inj_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/selection_noise_2026-07-29/runs/base_seed123_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/base_seed123_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/base_seed123_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/base_seed42_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/base_seed42_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/base_seed42_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/base_seed456_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/base_seed456_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/base_seed456_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed123_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed123_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed123_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed42_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed42_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed42_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed456_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed456_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_handROIbbox2_seed456_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed123_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed123_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed123_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed42_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed42_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed42_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed456_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed456_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/bboxROI_seed456_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed123_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed123_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed123_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed42_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed42_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed42_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed456_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed456_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROIbbox2_seed456_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed123_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed123_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed123_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed42_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed42_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed42_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed456_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed456_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/handROImask2_seed456_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed123_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed123_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed123_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed42_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed42_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed42_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed456_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed456_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/maskROI_seed456_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed123_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed123_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed123_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed42_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed42_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed42_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed456_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed456_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/randROI_seed456_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed123_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed123_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed123_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed42_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed42_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed42_rep3` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed456_rep1` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed456_rep2` | `rep` |
| `experiments/selection_noise_2026-07-29/runs/shuffleROI_seed456_rep3` | `rep` |
| `experiments/transfer/_p0_identity_ctrl_seed123` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/transfer/_p0_identity_ctrl_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/transfer/_p0_identity_ctrl_seed456` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/transfer/_p0_identity_inj_seed123` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/transfer/_p0_identity_inj_seed42` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/transfer/_p0_identity_inj_seed456` | `delta_detection`, `final_epoch`, `final_mAP`, `init_mAP`, `mAP` |
| `experiments/transfer/b2b_rescore_alpha0.5` | `alpha`, `delta_detection`, `mAP_baseline`, `mAP_rescored`, `miss_ctx` |
| `experiments/transfer/b2b_rescore_alpha1.0` | `alpha`, `delta_detection`, `mAP_baseline`, `mAP_rescored`, `miss_ctx` |
| `experiments/transfer/b2b_rescore_alpha2.0` | `alpha`, `delta_detection`, `mAP_baseline`, `mAP_rescored`, `miss_ctx` |
| `experiments/transfer/t1b_phasefilm_001_t1b_phasefilm_seed123` | `control_init_mAP`, `control_mAP`, `delta_control`, `delta_detection`, `init_mAP`, `injection_effect` |
| `experiments/transfer/t1b_phasefilm_002_t1b_phasefilm_seed456` | `control_init_mAP`, `control_mAP`, `delta_control`, `delta_detection`, `init_mAP`, `injection_effect` |

### 13.1 🔴 正本の記述の例外 — test 評価を持つ run

正本は「test split は未評価」と述べているが、その後 `--eval-test` が実装され、
**test 側の数値を持つ run が実在する**。正本の記述はこの時点より前のもの。

該当 69 run。全件の val/test 対応表は `anomalies/val_test_pairs.csv`。

**index.csv の `metric.<name>` 列は primary(val) の値である。**
test 側は `metric_test.<name>` 列に別出ししてある（`has_test` 列で絞り込める）。
この分離が無いと「split 列が val 一色 → test 評価は存在しない」と誤読される。

#### val / test の乖離（実測・全 69 run）

| 指標 | val 平均 | test 平均 | 差 (test - val) | n |
|---|---:|---:|---:|---:|
| `edit_score` | 42.7135 | 41.8604 | -0.8531 | 69 |
| `sticky_jaccard` | 0.7403 | 0.4563 | -0.2839 | 3 |
| `sticky_macro_f1` | 0.7864 | 0.5529 | -0.2335 | 3 |
| `jaccard` | 0.7509 | 0.5616 | -0.1893 | 69 |
| `sticky_accuracy` | 0.9362 | 0.7861 | -0.1501 | 3 |
| `macro_f1` | 0.7906 | 0.6496 | -0.1410 | 69 |
| `seg_f1_50` | 0.4806 | 0.3596 | -0.1210 | 69 |
| `accuracy` | 0.9406 | 0.8328 | -0.1078 | 69 |
| `sticky_seg_f1_50` | 0.5422 | 0.4854 | -0.0568 | 3 |
| `seg_f1_25` | 0.5093 | 0.4851 | -0.0242 | 69 |
| `seg_f1_10` | 0.5179 | 0.4984 | -0.0195 | 69 |
| `sticky_seg_f1_25` | 0.6029 | 0.6323 | +0.0293 | 3 |
| `sticky_seg_f1_10` | 0.6106 | 0.6411 | +0.0304 | 3 |
| `sticky_edit_score` | 50.5944 | 59.0140 | +8.4196 | 3 |

| path | seed | excluded |
|---|---:|---|
| `experiments/g2_followup_2026-07-29/s3/runs/base_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s3/runs/base_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s3/runs/base_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s3/runs/bboxROI_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s3/runs/bboxROI_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s3/runs/bboxROI_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s3/runs/shuffleROI_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s3/runs/shuffleROI_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s3/runs/shuffleROI_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/base_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/base_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/base_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/bboxROI_handROIbbox2_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/bboxROI_handROIbbox2_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/bboxROI_handROIbbox2_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/bboxROI_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/bboxROI_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/bboxROI_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handPresence_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handPresence_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handPresence_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROIbbox2_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROIbbox2_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROIbbox2_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROIbbox4_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROIbbox4_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROIbbox4_seed456` | 456 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROImask2_seed123` | 123 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROImask2_seed42` | 42 | False |
| `experiments/g2_followup_2026-07-29/s4/runs/handROImask2_seed456` | 456 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/base_seed123` | 123 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/base_seed42` | 42 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/base_seed456` | 456 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/bboxROI_seed123` | 123 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/bboxROI_seed42` | 42 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/bboxROI_seed456` | 456 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/maskROI_seed123` | 123 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/maskROI_seed42` | 42 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/maskROI_seed456` | 456 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/randROI_seed123` | 123 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/randROI_seed42` | 42 | False |
| `experiments/g2_main_2026-07-29_lecun/runs/randROI_seed456` | 456 | False |
| `experiments/phase1/s4_phase_baseline_044_frozen_tecno_phase_baseline_seed42` | 42 | False |
| `experiments/phase1/s4_phase_baseline_045_frozen_tecno_phase_baseline_seed42` | 42 | False |
| `experiments/phase1/s4_phase_baseline_046_frozen_tecno_phase_baseline_seed123` | 123 | False |
| `experiments/phase1/s4_phase_baseline_047_frozen_tecno_phase_baseline_seed123` | 123 | False |
| `experiments/phase1/s4_phase_baseline_048_frozen_tecno_phase_baseline_seed456` | 456 | False |
| `experiments/phase1/s4_phase_baseline_049_frozen_tecno_phase_baseline_seed456` | 456 | False |
| `experiments/phase1/s4_phase_baseline_050_frozen_tecno_phase_baseline_seed42` | 42 | False |
| `experiments/phase1/s4_phase_baseline_051_frozen_tecno_phase_baseline_seed42` | 42 | False |
| `experiments/phase1/s4_phase_baseline_052_frozen_tecno_phase_baseline_seed123` | 123 | False |
| `experiments/phase1/s4_phase_baseline_053_frozen_tecno_phase_baseline_seed123` | 123 | False |
| `experiments/phase1/s4_phase_baseline_054_frozen_tecno_phase_baseline_seed456` | 456 | False |
| `experiments/phase1/s4_phase_baseline_055_frozen_tecno_phase_baseline_seed456` | 456 | False |
| `experiments/phase1/s4_phase_baseline_056_frozen_tecno_phase_baseline_seed42` | 42 | False |
| `experiments/phase1/s4_phase_baseline_057_frozen_tecno_phase_baseline_seed42` | 42 | False |
| `experiments/phase1/s4_phase_baseline_058_frozen_tecno_phase_baseline_seed123` | 123 | False |
| `experiments/phase1/s4_phase_baseline_059_frozen_tecno_phase_baseline_seed123` | 123 | False |
| `experiments/phase1/s4_phase_baseline_060_frozen_tecno_phase_baseline_seed456` | 456 | False |
| `experiments/phase1/s4_phase_baseline_061_frozen_tecno_phase_baseline_seed456` | 456 | False |
| `experiments/transfer/t1a_appearance_001_t1a_appearance_seed42` | 42 | False |
| `experiments/transfer/t1a_appearance_002_t1a_appearance_seed123` | 123 | False |
| `experiments/transfer/t1a_appearance_003_t1a_appearance_seed456` | 456 | False |
| `experiments/transfer/t1a_base_test_001_t1a_base_test_seed42` | 42 | False |
| `experiments/transfer/t1a_base_test_002_t1a_base_test_seed123` | 123 | False |
| `experiments/transfer/t1a_base_test_003_t1a_base_test_seed456` | 456 | False |
| `experiments/transfer/t1a_regiontraj_test_001_t1a_regiontraj_test_seed42` | 42 | False |
| `experiments/transfer/t1a_regiontraj_test_002_t1a_regiontraj_test_seed123` | 123 | False |
| `experiments/transfer/t1a_regiontraj_test_003_t1a_regiontraj_test_seed456` | 456 | False |

## 14. Notion 実験Run台帳との照合 — 母数は未確定（結論保留）

台帳の行数について 2 つの実測値がある。**母数が確定するまで差分の結論は出さない。**

| 出所 | 実測 | 計測方法 |
|---|---:|---|
| ユーザー側 | 616 | `COUNT(*)` |
| Claude Code (MCP) | **739** | `SELECT COUNT(*)` via query_data_sources |

### 排除できた原因

| 仮説 | 検証結果 |
|---|---|
| 複数データソース | ❌ **データソースは 1 つ**（`collection://7bcf9406-…`） |
| フィルタ付きビューを見ていた | ❌ **ビューは 1 つ**（"Default view"）で Status 昇順ソートのみ・**フィルタなし** |
| 同名 DB の重複 | ❌ ワークスペース検索で `実験Run台帳` は **1 件のみ** |

### 残る候補（未検証）

- **計測時点の差**（台帳が増加した）: 作成日分布を取るクエリが
  Notion のクエリ利用上限に達し実行できなかった
- **アーカイブ行の扱い**: MCP の SQL モードは `is_archived` を受け付けず、
  アーカイブ行を含むか否かが仕様上未定義

### 確定した事実

| 項目 | 実測 |
|---|---:|
| 総行数（MCP 計測） | 739 |
| ユニークな Name | 738 |
| `Name LIKE '%_seed%'`（run 形式） | 712 |
| 散文タイトルの行 | 27 |
| **Status = `failed`** | **0** |
| Status = completed / planned / running / null | 733 / 4 / 1 / 1 |

**`failed` が 0 件であることは母数と無関係に確定している。**
repo 側には `metrics.json` が空の失敗 run が 6 件あるため、§1.1 の
運用欠陥（失敗が台帳に反映されない）はこの時点で成立する。

run_id 単位の 3 分類（記録漏れ / 成果物消失 / 数値の食い違い）は、
クエリ上限のため **未実施**。推測で埋めていない。

## 15. run_id の衝突

`run_id`（ディレクトリ名）は **12 種が複数箇所で衝突**する。
スキーマは `runs/<run_id>.json` を指定しているが、そのままではファイルが
上書きされるため、パス由来の `ledger_key` をファイル名に使い、
`run_id` はフィールドとして保持した。

| run_id | 箇所数 |
|---|---:|
| `base_seed123` | 3 |
| `base_seed42` | 3 |
| `base_seed456` | 3 |
| `bboxROI_seed123` | 3 |
| `bboxROI_seed42` | 3 |
| `bboxROI_seed456` | 3 |
| `s0_001_maskdino_bbox_seed42` | 3 |
| `s0_002_maskdino_bbox_seed123` | 3 |
| `s0_003_maskdino_bbox_seed456` | 3 |
| `s0_004_varifocanet_bbox_seed42` | 3 |
| `s0_005_varifocanet_bbox_seed123` | 3 |
| `s0_006_varifocanet_bbox_seed456` | 3 |

## 16. 🔴 修正済み: primary 指標に test の値が入っていた

### 16.1 症状

`has_test = true` の **27 run** で、`metrics.<name>`（primary）に
val ではなく **test の値**が入っていた。`split` 列は `val` のままだったため、
**「val と名乗る test の値」**という最も危険な不整合になっていた。
`index.csv` の `metric.*` と `metric_test.*` が全 27 run で完全一致し、
Δ が全て 0.00 に見えていた。

### 16.2 原因

`harvest_metrics()` が「どの split が primary か」を決める **前に**
primary の入れ物を埋めていた。同じ canonical 名を複数 split が書くと
`metrics.json` のキー順で **後に来た側が勝つ**。
`phase_accuracy` → `test_accuracy` の順に並ぶため test が残っていた。

```python
# 誤: split 判定より前に flat を埋めていた
if info['split']:
    by_split[info['split']][canon] = value
    flat[canon] = value          # <- 後勝ちで test が primary になる
...
evidence = {s for s in by_split if s != 'unknown'}   # <- 判定はこの後
```

追補 G で `split` の既定を val と宣言した時点で、宣言（`split` 列）と
実体（`metrics`）が別の場所で決まる構造が顕在化した。

### 16.3 対処

1. primary split を **先に**決め、その後で `flat` を充填する順序に変更した。
2. `metrics_primary_split` 列を追加し、`metrics` の出所を機械可読にした。
3. `tools/verify_runindex.py` を追加し `make runindex` に組み込んだ。
   C1〜C3 が同型の退行を検出する（`split` 列と出所の不一致、Δ が全て 0）。

## 17. 実験単位 (`experiment_id`) の導入と、その限界

`runs/*.json` には seed をまたいで run を束ねるフィールドが 1 つも無く、
573 run は「573 個の孤立した run」であって「N 個の実験」ではなかった。
seed 集約も Δ も paired-σ も機械的に計算できない状態だったため、
**run 名から機械的に導ける実験単位**を定義した。

```
experiment_id = <group>/<step>/<description(反復軸トークン除去)>@<split>~<frozen_source_tag>
                （同一 ID 内で eval_recipe_id が食い違う場合は #<hash8> を付与）
```

### 17.0 🔴 名前にも command.sh にも現れない条件軸がある

`s4_phase_baseline` の 55 run は当初「同一条件の 18 反復」に見えたが、そうではない。
真の条件軸は `config.yaml` の `frozen_source.cache_dir`（凍結特徴の抽出元）で **7 通り**あり、
これは環境変数 `RELDETR_FROZEN_TAG` で与えられるため
**run 名にも `command.sh` にも `eval_recipe` にも現れない**。

```python
# scripts/train_s4_tecno.py
_FROZEN_SRC = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")
```

`eval_recipe_id` は phase1/s4 の 61 run すべてで同一（`test_cfg.backbone` が
リテラル固定のため条件差が原理的に現れない）。つまり `eval_recipe_id` による分離だけでは
この交絡を防げない。`frozen_source_tag` を `experiment_id` に含めることで分離している。

`b2a` / `t1a` 系では同じ情報が `frozen_source.gap_cache` /
`frozen_source.tool_signal_cache` というキー名で入っているため、3 つのキーを順に見ている。

#### 🔴 証跡ファイルの記述が実態と食い違う（凍結源）

`s4_phase_baseline` の `notes.md` は **64 件すべてで**
「凍結源: Relation-DETR seed42」と断言するが、`config.yaml` の実際の
`frozen_source.cache_dir` がそれと異なる run が **41 件**ある
（step `s4_phase_baseline` の run 総数は 64）。`config.yaml` の `frozen_source.seed` も
`42` がハードコードされており同様に信用できない。
いずれも `scripts/train_s4_tecno.py` の固定文字列に由来する。

**したがって `frozen_source_tag` はキャッシュのパスからのみ導き、
`frozen_source.seed` と `notes.md` の記述は採用していない。**

- 実験数: **206** / run 数 749
- `experiment_id` を付けられなかった run: 78
  （run 名が命名規約に一致しない run）
- `eval_recipe_id` の食い違いで分離した base: 12
  - `baselines/s0/maskdino_bbox@val` -> ['None', 'a63aecae1158']
  - `baselines/s0/maskdino_bbox@val` -> ['None', 'a63aecae1158']
  - `baselines/s0/maskdino_bbox@val` -> ['None', 'a63aecae1158']
  - `baselines/s0/varifocanet_bbox@val` -> ['None', 'a63aecae1158']
  - `baselines/s0/varifocanet_bbox@val` -> ['None', 'a63aecae1158']
  - `baselines/s0/varifocanet_bbox@val` -> ['None', 'a63aecae1158']

### 17.1 🔴 限界: 名前が条件を一意に表さない実験がある

`experiment_id` は run 名から導く以上、**名前が条件を表していない場合は
異なる条件の run を 1 実験に束ねてしまう**。検出のため次の 2 列を出している。

| 列 | 意味 | 異常の徴候 |
|---|---|---|
| `n_command_variants` | seed/description を除いた `command.sh` 引数の種類数 | **> 1 なら条件が混在** |
| `runs_per_seed_max` | 同一 seed の run 数の最大 | > 1 なら再実行か条件違いが混在 |

実データで判明している最悪の例は §7.3 の `b2a_ro_oracle_noise000`
（1 つの名前に 4 通りのノイズ率）。**この実験の集約値は使ってはならない。**

### 17.2 🔴 逆向きの限界: 同一条件が別 experiment_id に分裂しうる

`step` は `ExperimentManager` に渡された文字列でしかなく
（`src/egosurgery/utils/experiment_id.py`）、同じ条件でも起動経路が違えば別の値になる。
`description` / `split` / `frozen_source_tag` が一致しているのに `step` だけが違う組を
機械的に検出した結果が次である。**同一条件が分裂している候補**として扱うこと。

該当 **3 組**

| group / description / split / frozen_source | 分裂した experiment_id |
|---|---|
| `baselines` / `maskdino_bbox` / `val` / `None` | `baselines/s0/maskdino_bbox@val#None`<br>`baselines/s0/maskdino_bbox@val#a63aecae` |
| `baselines` / `varifocanet_bbox` / `val` / `None` | `baselines/s0/varifocanet_bbox@val#None`<br>`baselines/s0/varifocanet_bbox@val#a63aecae` |
| `transfer` / `b2a_det2phase_toolpresence` / `val` / `relation_detr_seed42` | `transfer/b2a_det2phase/b2a_det2phase_toolpresence@val~relation_detr_seed42`<br>`transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_seed42` |

これらを 1 実験として束ねるべきかは、起動経路が同一かどうかの判断を伴うため
harvester では決めない。`experiments.csv` では別行のままにしてある。

## 18. 対照ペア (`arm` / `control_of`) — 確定できた範囲

### 18.1 一次証拠の探索結果

| 証拠源 | 結果 |
|---|---|
| `command.sh` の `--control` / `--baseline` / `--inject` / `--arm` | **0 件**。引数による対照指定は存在しない |
| **`config.yaml` の `delta:` ブロック** | **441 run** が保有。`phase_denominator` が分母を名指しする |
| `notes.md` の `## Δ` 節 | 439 run が保有。同じ内容を散文で書いたもの |

`config.yaml` の記述例（機械可読）:

```yaml
delta:
  phase_denominator: s4_phase_baseline (frozen_tecno_phase_baseline)
  denominator_value_lecun: 0.8986±0.0034
  note: Δ_phase = (T1a − S4 base). 別サーバー実行時は lecun 分母を流用し …
```

### 18.2 対照名の同定と、その裏付け

`config.yaml` の `delta.phase_denominator` は分母を **文字列で名指し**する。
実データに現れる 4 通り:

| 宣言 | run 数 | 解釈 |
|---|---:|---|
| `s4_phase_baseline (frozen_tecno_phase_baseline)` | 430 | step + description |
| `t1a_regiontoken base (同env efros paired)` | 6 | step のみ（括弧は散文） |
| `t1a_regiontoken base (同一環境 efros で再学習・paired)` | 3 | 同上 |
| `S0-frozen (=init mAP, within-run)` | 2 | **同一 run 内の初期値**。対照 run は存在しない |

#### 🔴 散文からの同定は誤る — config の宣言に従属させた

`notes.md` は分母を `T1a base[同env efros]` と書く。名前の近さだけで読むと
`step=t1a_base_env` に見えるが、**同じ run の `config.yaml` は
`t1a_regiontoken base` と宣言している**。両者は別の実験である。
そのため証拠の優先順を `config.yaml` → `notes.md` に固定した。

#### 🔴 同じ基準点が 2 通りのσで引用されている

`S4 base` は `±0.0034` (397 run) と `±0.0028` (33 run) の 2 通りで引用されている。
実測すると **同一の 3 run** に対する母集団σ (0.002766) と標本σ (0.003387) であり、
比は √(3/2) = 1.2247 である。
§10.1 の改善判定は `|Δ| > 1σ` を条件とするため、
**どちらのσを採るかで有意・非有意の判定が変わりうる**。σの規約は正本で統一が要る。

#### 分母が複数実験に該当するときの切り分け

`frozen_source_tag` で実験を分けた結果、`s4_phase_baseline` は 7 実験になった。
分母の宣言は 1 つなので、そのままでは確定しない。切り分けは 2 段構えで行う。

1. **凍結特徴ソースの一致** — `notes.md` が対照の条件を
   「同一土台（凍結backbone/GAP/recipe/seed・neck無し）」と明記している。
   凍結 backbone を揃えるのは研究者自身が宣言した規則なので、
   注入 run と同じ `frozen_source_tag` を持つ実験を分母とする。
2. **引用値による照合** — 1 で決まらないときのみ、
   `denominator_value_lecun` 等の引用値を再現する部分集合を探す。

### 18.3 確定できた件数

| 分類 | run 数 |
|---|---:|
| `injection_from_config_yaml` | 439 |
| `no_denominator_declared` | 308 |
| `baseline` | 17 |
| `within_run_baseline` | 2 |

**分母を宣言している run はすべて実験に解決できた（未解決 0 件）。**

`no_denominator_declared` の run は `config.yaml` にも `notes.md` にも
分母の記載が無い。推測で埋めず `control_of` は null のままにしてある。

#### 🔴 paired-σ がほぼ計算できない

`notes.md` は 439 run で「3-seed 揃ったら **paired-σ(対seed差)** で §10.1 判定」と
書いているが、実際に `paired` で計算できた実験は **わずか 1 件**である。

理由は基準点実験の構成にある:
`phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` は
**17 run / 3 seed（1 つの seed に最大 7 run）**であり、
seed ごとに 1 本ずつ対応させることができない。
どの run を代表とするかを決める規約はどの証跡ファイルにも無い。

したがって残り 155 実験は `unpaired`（平均の差のみ）とし、
**`delta_pstd_*` は空欄**にしてある。対応が取れない以上 paired-σ は定義できず、
それらしい数値を入れることは捏造にあたる。
**§10.1 の `|Δ| > 1σ` 判定は、現状の証跡では実行できない。**

### 18.4 `arm=control` を使っていない理由

スキーマは `injection` / `control` / `baseline` / `unknown` を許すが、
**自らを「対照」と宣言している run は 1 件も無い**。
実在するのは「Δ の基準点として参照されている実験」であり、これを `baseline` とした。
`control` を使うと、存在しない設計意図を捏造することになる。

### 18.5 Δ の計算方式

- `paired`: 注入側・対照側とも **seed ごとにちょうど 1 run** で seed 集合が一致するとき。
  seed ごとの差を取り、その平均を `delta_<metric>`、母集団σを `delta_pstd_<metric>` とする。
- `unpaired`: 上記を満たさないとき。平均の差だけを出し、
  **`delta_pstd_<metric>` は空欄**にする（対応が取れない以上 paired-σ は定義できない）。
- どちらで計算したかは `delta_method` 列に必ず記録する。混同してはならない。

## 19. `per_class.csv` を使うときの必須の注意

per-class の値は 573 個の JSON に分散していて横断分析に使えなかったため、
`runindex/per_class.csv` に long 形式（1 行 = 1 run × 1 クラス）で 1 ファイル化した。

- `per_class_kind=tool` : 66 run × 15 クラス（術具 **AP**）
- `per_class_kind=phase`: 545 run × 9 クラス（工程 **F1**）

**この 2 つを混ぜて集計してはならない。** 指標の種類が違う（AP と F1）。
ファイル名は両方とも `per_class_ap.json` なので、名前では判別できない。
必ず `per_class_kind` / `per_class_metric` で分離すること。

`value` が空欄の行は元が `NaN` だったもので、`is_nan=True` が立っている。
術具側の `NaN` は **val split に GT が 1 件も無いクラス**を意味する（0 ではない）。
平均を取るときは `nanmean` 相当（空欄を除外）にすること。

## 20. metrics.json / 命名規約に 2 系統ある

`g2_followup_2026-07-29` / `g2_main_2026-07-29_lecun` 群 (42 run) は
他の群と **スキーマも命名も違う**。

| 観点 | 主系統 | g2_* 系統 |
|---|---|---|
| ディレクトリ名 | `<step>_<seq3>_<desc>_seed<N>` | `<desc>_seed<N>`（seq が無い） |
| split の表現 | `val/<metric>` / `phase_<metric>` | `"val": {"phase_<metric>": …}` の入れ子 |
| per-class | `per_class_ap.json` | `val.phase_per_class_f1`（metrics.json 内） |
| 付随ファイル | `command.sh` / `config.yaml` / `notes.md` / `git_commit.txt` | `env.json` のみ |

両方を収穫できるようにした。出所は次の列で区別できる。

- `provenance.name` … `from_dirname_step_seq_desc_seed` / `from_dirname_desc_seed_no_seq`
- `per_class_source` … `…/per_class_ap.json` か `…/metrics.json#val.phase_per_class_f1`

**この群には `config.yaml` が無いため対照宣言も凍結源も取れない。**
`control_of` は null、`frozen_source_tag` も null である。
`metrics.json` の `system` フィールド（`base` / `bboxROI` / `shuffleROI`）が
arm を表している可能性があるが、対照関係を明示した記録ではないため採用していない。
値は `attributes` に保持してある。

### 20.1 🔴 指標でないものが `metric.*` 列に入っていた（修正済み）

`metrics.json` のネスト値と文字列値がそのまま `metrics` に入っていたため、
`index.csv` に `metric.val = {'phase_accuracy': …}` のような
**辞書リテラル**や `metric.system = base` のような文字列が書かれていた。
旧 573 run でも `b2b_rescore_*` の `denominator` / `method` が文字列で入っていた。

「指標とは数値である」という不変条件を実装に入れ、
数値以外は `attributes` / `metrics_nested` に分離した（情報は捨てていない）。

## 21. σ の定義 — 母集団σと標本σを両方出す

`<metric>_pstd` が母集団σか標本σか判別できず、`|Δ| > 1σ` 判定が
規約次第で反転しうる状態だった（§18.2）。両方を明示的に出すことにした。

| 列 | 定義 | Python |
|---|---|---|
| `<metric>_pstd` | **母集団σ** (ddof=0) | `statistics.pstdev` |
| `<metric>_sstd` | **標本σ** (ddof=1) | `statistics.stdev` |
| `<metric>_n` | 集約した値の個数 | |
| `delta_pstd_<metric>` | Δ の母集団σ | paired: 差の pstdev / unpaired: √(σ_inj²+σ_ctl²) |
| `delta_sstd_<metric>` | Δ の標本σ | 同上を標本σで |
| `abs_delta_over_sigma_<metric>` | **\|Δ\| / `delta_pstd_<metric>`** | 母集団σ基準 |

### 21.1 規約の違いが実際の判定に与える影響（実測）

`accuracy` について両方の規約で判定件数を出した。

| 閾値 | 母集団σ基準 | 標本σ基準 | 判定が反転 |
|---|---:|---:|---:|
| 1σ | 126 | 124 | **2** |
| 2σ | 124 | 123 | **1** |
| 3σ | 120 | 118 | **2** |

対象 134 実験。標本σ/母集団σ の実測中央値 = **1.2247**。

**§10.1 が使う 1σ 基準では、現在の実データで判定は 1 件も反転しない。**
理由は σ の合成にある。注入側は n=3（比 √(3/2)=1.2247）だが
対照側は n が大きく（比が 1 に近い）、合成 σ では差が薄まる。

ただし `notes.md` に手書きされた `0.8986±0.0028` と `±0.0034` は
**単一の集計値そのもの**なので 22% の差がそのまま出る。
手書きの値を引用するときは規約の確認が要る。

### 21.2 🔴 リポジトリ内に σ の規約が **2 系統併存**している

`scripts/` と `src/` を実測した結果:

| 規約 | 出現箇所 | 主な使用層 |
|---|---:|---|
| 母集団σ (`pstdev` / `pvariance`) | **48** | §10.1 判定・レポート生成 |
| 標本σ (`statistics.stdev` / `ddof=1`) | **16** | 解析・監査 (`scripts/analysis/*`) |

**§10.1 の判定を実装している箇所は母集団σで一致している:**

| ファイル:行 | 記述 |
|---|---|
| `scripts/paired_sigma_3seed.py:7,80` | \|mean(Δ)\| > pstdev(Δ) かつ 全 detector_seed 同符号 |
| `scripts/analyze_t1a_factorial_ablation.py:13,81` | §10.1: \|meanΔ\|>pstdev かつ全 seed 同符号 |
| `scripts/report_t1a_boundary.py:5,59` | \|mean\|>pstdev かつ 3-seed 同符号 |
| `scripts/report_daux_paired.py:69,114` | \|mean\|>pstdev かつ 3-seed 同符号 |
| `src/egosurgery/utils/transfer_delta_report.py` | pstdev（haux/taux 系レポートの単一情報源） |
| `scripts/run_haux_oracle_gate.sh:14` / `run_taux_problemA.sh:76` | 同上 |

**一方、解析・監査層は標本σを使っている:**
`scripts/analysis/delta_allrun_recompute.py:157` / `delta_convention_audit.py:132` /
`g1_power_analysis.py:68` / `g2_report.py:166,179,452`（`np.std(..., ddof=1)`）/
`scripts/analyze_phase_coupling.py:93,154,162`。

**「Δ の規約を監査する」スクリプト自身が、判定側と違うσを使っている。**

### 21.2.1 🔴 **明文の規約は ddof=1、実装は ddof=0** — 両者が逆を向いている

正本の研究計画（`docs/m2_plan_rewrite/`）は §10.1 の 1σ を
「同一 eval recipe での 3-seed std」としか書かず種類を明示していないが、
**スコープを限った明示宣言は複数あり、そのすべてが ddof=1（標本σ）を指す**:

| 出典 | 記述 |
|---|---|
| `scripts/analyze_phase_coupling.py:21` | 「改善主張は §10.1 に従い \|Δ\| > 1σ のときのみ。**1σ は base 3-seed の標本(n-1)標準偏差**」 |
| `src/egosurgery/metrics/delta.py:111,131` | 「標準偏差は**不偏標準偏差（ddof=1）**」/ `arr.std(ddof=1)` |
| `docs/experiment_log.md:1742` | 「n=3, **ddof=1**」 |

**実験ログの数値も ddof=1 で書かれている**（実測で照合）:

```
docs/experiment_log.md:440   S4' = acc 0.9142 ± 0.0017
  実測 (s4_phase_baseline_004/005/006 _neck):
    mean = 0.9142
    pstdev (ddof=0) = 0.001426   -> 0.0014  ✗ 一致しない
    stdev  (ddof=1) = 0.001746   -> 0.0017  ✅ 一致
```

一方 §10.1 の**判定を実装している** 7 箇所は `pstdev`（ddof=0）である。
つまり **文書が定めた規約と、判定コードが使っている規約が食い違っている。**
これは「どちらか未定」ではなく「二つが並存し矛盾している」状態である。

`abs_delta_over_sigma_<metric>` と `verdict_10_1` は **母集団σ**（ddof=0）を分母に、
`verdict_10_1_sstd` は **標本σ**（ddof=1）を分母にしている。
**どちらを正本とするかは harvester が決めることではない**ため両方出し、
結論が食い違う実験を `verdict_10_1_agree = False` で列挙している（backlog B-9 / B-18）。

なお件数の数え方に注意: 上の「48 / 16」は docstring・コメント・print 文を含む
全 grep ヒットである。実コード行だけに絞ると概ね 21 / 15 になる。

なお `notes.md` / `config.yaml` の `0.8986±0.0034` は書き出し時に計算された値ではなく、
`scripts/train_*.py` にハードコードされた文字列リテラルである。
値が更新されない構造なので、引用するときは実測と突き合わせること
（`experiments.csv` の `control_note_value` 列に保持してある）。

また `scripts/compute_delta.py` と `scripts/export_paper_tables.py` は
**0 バイトの空ファイル**（未実装 scaffold）である。`Makefile` の `delta` /
`tables` ターゲットはこれらを呼ぶので、現状では何もしない。

### 21.3 🔴 §10.1 は σ 条件だけではない — **同符号条件**がある

上記 7 箇所すべてが判定を **2 条件**で書いている:

> `|mean(Δ)| > pstdev(Δ)` **かつ** `全 seed 同符号`

第 2 条件は seed ごとの Δ が要るので **paired のときしか判定できない**。
`delta_same_sign_<metric>` 列に出しているが、埋まるのは paired の実験だけである。

**したがって `unpaired_pooled` の 131 実験は、σ 条件は評価できても
§10.1 の判定を完成させることができない。**
`abs_delta_over_sigma_*` が大きくても「§10.1 で有意」と結論してはいけない。

## 22. paired-σ の宣言と実行可能性の乖離

全件は `anomalies/paired_feasibility.csv`（1 行 = 1 実験）。

- `control_of` が確定した実験: **136**
- そのうち `notes.md` / `config.yaml` が **paired-σ 判定を宣言**: **136**
- 実際に paired-σ を計算できる: **5**
- **seed ごとに代表 1 本を選ぶ規約を入れれば計算できる: 134**

### 22.1 何が paired を阻んでいるか

| 原因 | 実験数 |
|---|---:|
| `control_multi_run_per_seed` | 125 |
| `both_multi_run_per_seed` | 6 |
| `(阻害なし)` | 5 |

**支配的原因は対照実験の再実行が畳まれていないこと**であり、
注入側の seed 記録誤りではない（§23 のとおり seed の食い違いは 0 件）。

注入側 run 439 本のうち、対照に同じ seed が存在するのは **427 本**。
残り 12 本は対照側に対応する seed が無く、畳んでも paired にできない。

### 22.2 🔴 「paired と宣言されているが unpaired でしか計算できない実験」

**131 実験**が該当する。§10.1 の判定を paired-σ で行ったと
読める記述が `notes.md` にあるが、実際にはできていない。

| 阻害原因 | 実験数 | 代表例 |
|---|---:|---|
| `control_multi_run_per_seed` | 125 | `transfer/b2a_base_oracle_noise_p010/b2a_base_oracle_noise_p010@val~relation_detr_seed42` |
| `both_multi_run_per_seed` | 6 | `transfer/b2a_det2phase_oracletool/b2a_det2phase_oracletool@val~relation_detr_seed42` |

現在の `experiments.csv` はこれらを `delta_method=unpaired` /
`delta_sigma_source=unpaired_pooled` と明示している。
unpaired の σ は paired-σ より大きく出る保守的な推定なので、
**σ 条件については unpaired で満たせば paired でも満たす**（逆は言えない）。
ただし §21.3 のとおり **同符号条件は unpaired では判定できない**ため、
これらの実験について §10.1 の判定を完成させることはできない。

### 22.3 paired が成立した実験の §10.1 判定

現時点で paired-σ を計算できるのは **5 実験**。
`accuracy` について 2 条件を両方適用した結果は次のとおり。

| experiment_id | Δacc | \|Δ\|/σ | 同符号 | §10.1 |
|---|---:|---:|---|---|
| `transfer/b2a_ro_oracle_nhnoise_p010/b2a_ro_oracle_nhnoise_p010@val~relation_detr_seed42` | +0.07068 | 26.75 | ✓ | **有意** |
| `transfer/b2a_regiononly_oracle/b2a_regiononly_oracle@val~relation_detr_seed42` | +0.06980 | 20.28 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_nhnoise_p020/b2a_ro_oracle_nhnoise_p020@val~relation_detr_seed42` | +0.06980 | 32.74 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_nhnoise_p030/b2a_ro_oracle_nhnoise_p030@val~relation_detr_seed42` | +0.06826 | 36.63 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_scalpelnoise_p010/b2a_ro_oracle_scalpelnoise_p010@val~relation_detr_seed42` | +0.06782 | 27.32 | ✓ | **有意** |
| `transfer/t1a_3seed_det456_frozen/t1a_3seed_det456_frozen@val~relation_detr_seed456` | +0.06425 | 6.00 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_scalpelnoise_p020/b2a_ro_oracle_scalpelnoise_p020@val~relation_detr_seed42` | +0.06342 | 32.80 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_03/b2a_oracle_mask_03@val~relation_detr_seed42` | +0.06276 | 15.46 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_02/b2a_oracle_mask_02@val~relation_detr_seed42` | +0.06210 | 11.26 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_04/b2a_oracle_mask_04@val~relation_detr_seed42` | +0.06188 | 15.54 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_08/b2a_oracle_mask_08@val~relation_detr_seed42` | +0.06188 | 12.30 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_11/b2a_oracle_mask_11@val~relation_detr_seed42` | +0.06166 | 12.83 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_01/b2a_oracle_mask_01@val~relation_detr_seed42` | +0.06144 | 12.13 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_05/b2a_oracle_mask_05@val~relation_detr_seed42` | +0.06100 | 10.05 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_10/b2a_oracle_mask_10@val~relation_detr_seed42` | +0.06100 | 10.11 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_12/b2a_oracle_mask_12@val~relation_detr_seed42` | +0.06100 | 11.45 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_bipolarnoise_p010/b2a_ro_oracle_bipolarnoise_p010@val~relation_detr_seed42` | +0.06100 | 15.85 | ✓ | **有意** |
| `transfer/t1a_3seed_det123_frozen/t1a_3seed_det123_frozen@val~relation_detr_seed123` | +0.06084 | 14.27 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_14/b2a_oracle_mask_14@val~relation_detr_seed42` | +0.06078 | 15.24 | ✓ | **有意** |
| `transfer/haux_hand_presence_oracle_withtooloracle/haux_hand_presence_oracle_withtooloracle@val~relation_detr_seed42` | +0.06012 | 11.77 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_13/b2a_oracle_mask_13@val~relation_detr_seed42` | +0.05990 | 13.77 | ✓ | **有意** |
| `transfer/b2a_det2phase_oracletool/b2a_det2phase_oracletool@val~relation_detr_seed42` | +0.05979 | 11.42 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_07/b2a_oracle_mask_07@val~relation_detr_seed42` | +0.05968 | 12.41 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_scalpelnoise_p030/b2a_ro_oracle_scalpelnoise_p030@val~relation_detr_seed42` | +0.05946 | 30.75 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_06/b2a_oracle_mask_06@val~relation_detr_seed42` | +0.05594 | 18.12 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_bsnoise_p010/b2a_ro_oracle_bsnoise_p010@val~relation_detr_seed42` | +0.05572 | 59.86 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_bipolarnoise_p020/b2a_ro_oracle_bipolarnoise_p020@val~relation_detr_seed42` | +0.05550 | 11.88 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_top3noise_p010/b2a_ro_oracle_top3noise_p010@val~relation_detr_seed42` | +0.05462 | 25.76 | ✓ | **有意** |
| `transfer/taux_tecno_windowk3/taux_tecno_windowk3@val~relation_detr_seed42` | +0.05374 | 23.06 | ✓ | **有意** |
| `transfer/taux_mingru_nonek3/taux_mingru_nonek3@val~relation_detr_seed42` | +0.05286 | 15.91 | ✓ | **有意** |
| `transfer/t1a_region_mask_02/t1a_region_mask_02@val~relation_detr_seed42` | +0.05264 | 12.05 | ✓ | **有意** |
| `transfer/t1a_appearance/t1a_appearance@val~relation_detr_seed42` | +0.05242 | 15.25 | ✓ | **有意** |
| `transfer/t1a_region_mask_14/t1a_region_mask_14@val~relation_detr_seed42` | +0.05220 | 14.16 | ✓ | **有意** |
| `transfer/taux_tecno_nonek3/taux_tecno_nonek3@val~relation_detr_seed42` | +0.05220 | 12.57 | ✓ | **有意** |
| `transfer/t1a_region_mask_03/t1a_region_mask_03@val~relation_detr_seed42` | +0.05198 | 15.81 | ✓ | **有意** |
| `transfer/t1a_region_mask_05/t1a_region_mask_05@val~relation_detr_seed42` | +0.05198 | 25.37 | ✓ | **有意** |
| `transfer/t1a_region_mask_08/t1a_region_mask_08@val~relation_detr_seed42` | +0.05198 | 18.91 | ✓ | **有意** |
| `transfer/t1a_region_mask_12/t1a_region_mask_12@val~relation_detr_seed42` | +0.05176 | 15.86 | ✓ | **有意** |
| `transfer/t1a_region_mask_13/t1a_region_mask_13@val~relation_detr_seed42` | +0.05176 | 18.06 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_03/b2a_regiononly_mask_03@val~relation_detr_seed42` | +0.05154 | 16.60 | ✓ | **有意** |
| `transfer/t1a_regiontoken/t1a_regiontoken@val~relation_detr_seed42` | +0.05154 | 23.73 | ✓ | **有意** |
| `transfer/t1a_3seed_det42_frozen/t1a_3seed_det42_frozen@val~relation_detr_seed42` | +0.05143 | 18.39 | ✓ | **有意** |
| `transfer/t1a_region_only/t1a_region_only@val~relation_detr_seed42` | +0.05132 | 13.21 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_07/b2a_regiononly_mask_07@val~relation_detr_seed42` | +0.05110 | 14.66 | ✓ | **有意** |
| `transfer/hires_relation_detr_seed42/hires_relation_detr_seed42@val~relation_detr_seed42` | +0.05110 | 17.83 | ✓ | **有意** |
| `transfer/t1a_combined_oracle_noise_p030/t1a_combined_oracle_noise_p030@val~relation_detr_seed42` | +0.05110 | 15.58 | ✓ | **有意** |
| `transfer/t1a_region_mask_11/t1a_region_mask_11@val~relation_detr_seed42` | +0.05110 | 30.67 | ✓ | **有意** |
| `transfer/t1a_base_test/t1a_base_test@val~relation_detr_seed42` | +0.05088 | 14.17 | ✓ | **有意** |
| `transfer/t1a_base_env/t1a_base_env@val~relation_detr_seed42` | +0.05088 | 19.11 | ✓ | **有意** |
| `transfer/t1a_deep_3s10l96f/t1a_deep_3s10l96f@val~relation_detr_seed42` | +0.05066 | 10.34 | ✓ | **有意** |
| `transfer/t1a_region_mask_01/t1a_region_mask_01@val~relation_detr_seed42` | +0.05066 | 17.05 | ✓ | **有意** |
| `transfer/t1a_combined_oracle/t1a_combined_oracle@val~relation_detr_seed42` | +0.05044 | 11.37 | ✓ | **有意** |
| `transfer/t1a_combined_oracle_noise_p010/t1a_combined_oracle_noise_p010@val~relation_detr_seed42` | +0.05044 | 13.34 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_09/b2a_oracle_mask_09@val~relation_detr_seed42` | +0.05022 | 9.72 | ✓ | **有意** |
| `transfer/t1a_region_mask_04/t1a_region_mask_04@val~relation_detr_seed42` | +0.05022 | 15.12 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_02/b2a_regiononly_mask_02@val~relation_detr_seed42` | +0.05000 | 12.27 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_bipolarnoise_p030/b2a_ro_oracle_bipolarnoise_p030@val~relation_detr_seed42` | +0.05000 | 14.64 | ✓ | **有意** |
| `transfer/t1a_b2a_combined/t1a_b2a_combined@val~relation_detr_seed42` | +0.04978 | 11.60 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_00/b2a_oracle_mask_00@val~relation_detr_seed42` | +0.04978 | 8.21 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_13/b2a_regiononly_mask_13@val~relation_detr_seed42` | +0.04978 | 12.93 | ✓ | **有意** |
| `transfer/t1a_combined_oracle_noise_p020/t1a_combined_oracle_noise_p020@val~relation_detr_seed42` | +0.04978 | 12.73 | ✓ | **有意** |
| `transfer/t1a_region_mask_07/t1a_region_mask_07@val~relation_detr_seed42` | +0.04978 | 13.17 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_05/b2a_regiononly_mask_05@val~relation_detr_seed42` | +0.04956 | 47.64 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_14/b2a_regiononly_mask_14@val~relation_detr_seed42` | +0.04934 | 12.65 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_12/b2a_regiononly_mask_12@val~relation_detr_seed42` | +0.04890 | 20.58 | ✓ | **有意** |
| `transfer/b2a_regiononly_pred/b2a_regiononly_pred@val~relation_detr_seed42` | +0.04890 | 10.85 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_08/b2a_regiononly_mask_08@val~relation_detr_seed42` | +0.04846 | 9.90 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_04/b2a_regiononly_mask_04@val~relation_detr_seed42` | +0.04846 | 11.09 | ✓ | **有意** |
| `transfer/t1a_region_mask_10/t1a_region_mask_10@val~relation_detr_seed42` | +0.04669 | 13.12 | ✓ | **有意** |
| `transfer/t1a_region_mask_06/t1a_region_mask_06@val~relation_detr_seed42` | +0.04647 | 18.60 | ✓ | **有意** |
| `transfer/taux_tecno_movavgk3/taux_tecno_movavgk3@val~relation_detr_seed42` | +0.04625 | 20.25 | ✓ | **有意** |
| `transfer/b2a_base_oracle_top3noise_p010/b2a_base_oracle_top3noise_p010@val~relation_detr_seed42` | +0.04471 | 7.54 | ✓ | **有意** |
| `transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_seed123` | +0.04389 | 10.49 | ✓ | **有意** |
| `transfer/t1a_region_mask_09/t1a_region_mask_09@val~relation_detr_seed42` | +0.04339 | 25.88 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_11/b2a_regiononly_mask_11@val~relation_detr_seed42` | +0.04295 | 13.71 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_bsnoise_p020/b2a_ro_oracle_bsnoise_p020@val~relation_detr_seed42` | +0.04295 | 11.37 | ✓ | **有意** |
| `transfer/t1a_3seed_det123_aug/t1a_3seed_det123_aug@val~relation_detr_augstrong_seed123` | +0.04279 | 6.67 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_01/b2a_regiononly_mask_01@val~relation_detr_seed42` | +0.04273 | 16.05 | ✓ | **有意** |
| `transfer/t1a_region_mask_00/t1a_region_mask_00@val~relation_detr_seed42` | +0.04251 | 15.50 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_09/b2a_regiononly_mask_09@val~relation_detr_seed42` | +0.04207 | 12.32 | ✓ | **有意** |
| `transfer/b2a_mask_dim_05/b2a_mask_dim_05@val~relation_detr_seed42` | +0.04097 | 5.06 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_10/b2a_regiononly_mask_10@val~relation_detr_seed42` | +0.04097 | 29.38 | ✓ | **有意** |
| `transfer/b2a_mask_dim_03/b2a_mask_dim_03@val~relation_detr_seed42` | +0.04031 | 7.07 | ✓ | **有意** |
| `transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_seed42` | +0.04013 | 10.18 | ✓ | **有意** |
| `transfer/b2a_det2phase/b2a_det2phase_toolpresence@val~relation_detr_seed42` | +0.04009 | 11.27 | ✓ | **有意** |
| `transfer/b2a_mask_dim_12/b2a_mask_dim_12@val~relation_detr_seed42` | +0.04009 | 14.58 | ✓ | **有意** |
| `transfer/b2a_mask_dim_13/b2a_mask_dim_13@val~relation_detr_seed42` | +0.04009 | 14.15 | ✓ | **有意** |
| `transfer/hires_relation_detr_augstrong_hires_seed42/hires_relation_detr_augstrong_hires_seed42@val~relation_detr_augstrong_hires_seed42` | +0.04004 | 13.49 | ✓ | **有意** |
| `transfer/b2a_mask_dim_01/b2a_mask_dim_01@val~relation_detr_seed42` | +0.03987 | 16.40 | ✓ | **有意** |
| `transfer/t1a_shuffle_oracle/t1a_shuffle_oracle@val~relation_detr_seed42` | +0.03987 | 8.88 | ✓ | **有意** |
| `transfer/b2a_mask_dim_14/b2a_mask_dim_14@val~relation_detr_seed42` | +0.03965 | 10.76 | ✓ | **有意** |
| `transfer/b2a_mask_dim_08/b2a_mask_dim_08@val~relation_detr_seed42` | +0.03921 | 9.91 | ✓ | **有意** |
| `transfer/b2a_mask_dim_04/b2a_mask_dim_04@val~relation_detr_seed42` | +0.03899 | 5.04 | ✓ | **有意** |
| `transfer/hires_relation_detr_augstrong_seed42/hires_relation_detr_augstrong_seed42@val~relation_detr_augstrong_seed42` | +0.03868 | 38.97 | ✓ | **有意** |
| `transfer/t1a_3seed_det42_aug/t1a_3seed_det42_aug@val~relation_detr_augstrong_seed42` | +0.03857 | 29.20 | ✓ | **有意** |
| `transfer/b2a_mask_dim_11/b2a_mask_dim_11@val~relation_detr_seed42` | +0.03833 | 5.59 | ✓ | **有意** |
| `transfer/b2a_mask_dim_02/b2a_mask_dim_02@val~relation_detr_seed42` | +0.03811 | 15.35 | ✓ | **有意** |
| `transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_seed456` | +0.03784 | 3.47 | ✓ | **有意** |
| `transfer/b2a_base_oracle_noise_p010/b2a_base_oracle_noise_p010@val~relation_detr_seed42` | +0.03701 | 5.69 | ✓ | **有意** |
| `transfer/b2a_base_oracle_top3noise_p020/b2a_base_oracle_top3noise_p020@val~relation_detr_seed42` | +0.03635 | 7.40 | ✓ | **有意** |
| `transfer/t1a_shuffle/t1a_shuffle@val~relation_detr_seed42` | -0.03625 | 9.97 | ✓ | **有意** |
| `transfer/b2a_mask_dim_07/b2a_mask_dim_07@val~relation_detr_seed42` | +0.03547 | 5.50 | ✓ | **有意** |
| `transfer/b2a_mask_dim_10/b2a_mask_dim_10@val~relation_detr_seed42` | +0.03525 | 5.61 | ✓ | **有意** |
| `transfer/t1a_3seed_det456_aug/t1a_3seed_det456_aug@val~relation_detr_augstrong_seed456` | +0.03454 | 18.83 | ✓ | **有意** |
| `transfer/b2a_mask_dim_06/b2a_mask_dim_06@val~relation_detr_seed42` | +0.03437 | 9.45 | ✓ | **有意** |
| `transfer/taux_tecno_deltak3/taux_tecno_deltak3@val~relation_detr_seed42` | +0.03327 | 5.74 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_top3noise_p020/b2a_ro_oracle_top3noise_p020@val~relation_detr_seed42` | +0.03195 | 28.32 | ✓ | **有意** |
| `transfer/b2a_mask_dim_00/b2a_mask_dim_00@val~relation_detr_seed42` | +0.03151 | 10.61 | ✓ | **有意** |
| `transfer/b2a_mask_dim_09/b2a_mask_dim_09@val~relation_detr_seed42` | +0.03063 | 10.10 | ✓ | **有意** |
| `transfer/b2a_base_oracle_top3noise_p030/b2a_base_oracle_top3noise_p030@val~relation_detr_seed42` | +0.03041 | 4.87 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_00/b2a_regiononly_mask_00@val~relation_detr_seed42` | +0.02887 | 11.63 | ✓ | **有意** |
| `transfer/b2a_regiononly_mask_06/b2a_regiononly_mask_06@val~relation_detr_seed42` | +0.02887 | 13.36 | ✓ | **有意** |
| `transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_augstrong_seed123` | +0.02673 | 2.70 | ✓ | **有意** |
| `transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_augstrong_seed42` | +0.02493 | 16.96 | ✓ | **有意** |
| `transfer/b2a_oracle_mask_top3_joint/b2a_oracle_mask_top3_joint@val~relation_detr_seed42` | +0.02403 | 15.70 | ✓ | **有意** |
| `transfer/t1a_combined_region_top3_mask/t1a_combined_region_top3_mask@val~relation_detr_seed42` | +0.02403 | 7.29 | ✓ | **有意** |
| `transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_augstrong_hires_seed42` | +0.02354 | 10.49 | ✓ | **有意** |
| `transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_augstrong_seed456` | +0.02134 | 6.07 | ✓ | **有意** |
| `transfer/t1a_region_mask_top3/t1a_region_mask_top3@val~relation_detr_seed42` | +0.01941 | 4.87 | ✓ | **有意** |
| `transfer/b2a_base_oracle_noise_p020/b2a_base_oracle_noise_p020@val~relation_detr_seed42` | +0.01897 | 2.64 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_bsnoise_p030/b2a_ro_oracle_bsnoise_p030@val~relation_detr_seed42` | +0.01897 | 7.90 | ✓ | **有意** |
| `transfer/b2a_regiononly_oracle_mask_top3/b2a_regiononly_oracle_mask_top3@val~relation_detr_seed42` | -0.01799 | 2.60 | ✓ | **有意** |
| `transfer/haux_hand_geom_oracle/haux_hand_geom_oracle@val~relation_detr_seed42` | +0.01391 | 2.03 | ✓ | **有意** |
| `transfer/b2a_base_oracle_noise_p030/b2a_base_oracle_noise_p030@val~relation_detr_seed42` | +0.01237 | 3.62 | ✓ | **有意** |
| `transfer/haux_hand_presence_oracle/haux_hand_presence_oracle@val~relation_detr_seed42` | +0.00665 | 0.74 | ✗ | 非有意 |
| `transfer/b2a_ro_oracle_noise000/b2a_ro_oracle_noise000@val~relation_detr_seed42` | +0.00605 | 1.06 | ✓ | **有意** |
| `transfer/b2a_ro_oracle_top3noise_p030/b2a_ro_oracle_top3noise_p030@val~relation_detr_seed42` | +0.00291 | 0.25 | ✗ | 非有意 |
| `transfer/t1a_boundary/t1a_boundary@val~relation_detr_seed42` | -0.00242 | 0.88 | ✗ | 非有意 |
| `transfer/haux_hand_count_oracle/haux_hand_count_oracle@val~relation_detr_seed42` | +0.00225 | 0.40 | ✗ | 非有意 |
| `transfer/haux_hand_own_other_oracle/haux_hand_own_other_oracle@val~relation_detr_seed42` | +0.00225 | 1.02 | ✗ | 非有意 |
| `transfer/haux_hand_presence_oracle_shuffle/haux_hand_presence_oracle_shuffle@val~relation_detr_seed42` | +0.00181 | 0.27 | ✗ | 非有意 |
| `transfer/t1a_regiontraj/t1a_regiontraj@val~relation_detr_seed42` | -0.00088 | 0.29 | ✗ | 非有意 |
| `transfer/t1a_regiontraj_test/t1a_regiontraj_test@val~relation_detr_seed42` | -0.00066 | 0.28 | ✗ | 非有意 |
| `transfer/t1a_region_only_mask_top3/t1a_region_only_mask_top3@val~relation_detr_seed42` | +0.00049 | 0.21 | ✗ | 非有意 |

これが現在の証跡で**実際に完成できる §10.1 判定のすべて**である。

## 23. seed の出所 — run の学習 seed に誤りは無い

§17.0 の「`notes.md` の凍結源 seed 記載が虚偽」を受けて、
**run 自身の学習 seed** が汚染されていないかを全件突き合わせた。
証拠は `command.sh` の `--seed` / `seed=`、`config.yaml` の `seed`、
そして `metrics.json` の `seed`（g2_* 群は前 2 つを持たないため）。
`notes.md` は虚偽の実績があるため証拠に使っていない。

| seed_agreement | run 数 | 意味 |
|---|---:|---|
| `agree` | 639 | ディレクトリ名と他証拠が一致 |
| `unverified_no_other_evidence` | 32 | `command.sh` も `config.yaml` も無い（g2_* 群） |
| `no_seed_in_dirname` | 78 | 命名規約外 |
| **`conflict`** | **0** | **食い違い** |

**食い違いは 0 件。** したがって Δ の seed 対応が誤っている可能性は排除できる。
§17.0 の誤記は**凍結検出器の seed** の話であって、run の学習 seed ではない。

### 23.1 `frozen_source.seed` は信用できない（実測）

- `config.yaml` に `frozen_source.seed` を持つ run: **503**
- そのうち実際の cache パスと**矛盾**する run: **48**

矛盾例: 宣言は `seed: 42` だが cache は `relation_detr_augstrong_seed123`。
`frozen_source_tag` は cache パスからのみ導いており、この宣言は採用していない。
値は矛盾検出のためだけに `frozen_source_seed_declared` に保持している。

### 23.2 分母が `s4_phase_baseline` である実験の一覧

`s4_phase_baseline` を `control_of` に持つ実験は **133**、run は **430**。

- 分母 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_augstrong_hires_seed42` … 2 実験
- 分母 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_augstrong_seed123` … 2 実験
- 分母 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_augstrong_seed42` … 4 実験
- 分母 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_augstrong_seed456` … 2 実験
- 分母 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed123` … 2 実験
- 分母 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` … 119 実験
- 分母 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed456` … 2 実験

§17.0 の凍結源誤記は**この分母実験そのもの**で起きている。ただし:

1. `frozen_source_tag` は `config.yaml` の cache パスから導いており、
   誤っている `notes.md` / `frozen_source.seed` は使っていない。
2. `experiment_id` は `frozen_source_tag` を含むので、
   異なる凍結源の run は**別の分母実験**に分かれている。

したがって Δ の分母は cache パス基準で正しく分離されている。
**残るリスクは cache パス自体が実行時の実態と違う場合**だが、
これを検証できる証跡（実行時の環境変数の記録）は repo に存在しない。

## 24. seed 代表値の畳み込み (dedup) と §10.1 判定

### 24.1 代表値の取り方

対照実験は 1 つの seed に最大 7 run を持つため、畳まないと seed 対応が付かず
paired-σ を計算できなかった（§22）。`experiments.csv` の Δ は
**`mean`** を既定として seed ごとに 1 値へ畳んでいる
（`delta_dedup_rule` 列に記録）。

| 規則 | 内容 | 採否 |
|---|---|---|
| `mean` | seed 内の全 run の平均 | **既定** |
| `latest` | seq が最大の run | 感度分析のみ |
| `first` | seq が最小の run | 感度分析のみ |
| `best` | 比較する指標が最良の run | **実装しない** |

`mean` を既定にした理由:

1. 順序に依存しない（`git_commit.txt` や seq の記録が信用できない run がある）
2. 特定の 1 本を選ばないので「どれを選ぶか」の恣意性が入らない
3. 再実行のばらつきを捨てずに平均へ織り込む

**`best` を実装しない理由**: 比較する指標そのもので代表を選ぶと Δ が
系統的に偏る（選択バイアス）。対照側で best を選べば Δ は大きく、
注入側で選べば小さく出る。研究公正性の観点から提供しない。

### 24.2 代表値の取り方は結論を変えない（感度分析）

3 規則すべてで §10.1 判定が一致する実験: **134 / 134**

ただし Δ の値自体は動く（`mean` との差の最大 = **0.093175**）。
判定が変わらないのは σ も同時にスケールするためである。
**Δ の絶対値を引用するときは `delta_dedup_rule` を併記すること。**

全件は `anomalies/dedup_sensitivity.csv`。

### 24.3 §10.1 判定の結果

判定条件は 2 つ（§21.3）。**両方**満たしたときだけ `significant`。

> `|mean(Δ)| > σ` **かつ** `全 seed 同符号`

| 判定 | 母集団σ (ddof=0) | 標本σ (ddof=1) |
|---|---:|---:|
| `significant` | 125 | 124 |
| `not_significant` | 9 | 10 |
| `undecidable` | 2 | 2 |

**σ の規約で結論が変わる実験: 1 件**

- `transfer/b2a_ro_oracle_noise000/b2a_ro_oracle_noise000@val~relation_detr_seed42`（指標 `accuracy`）
  - Δ = +0.006046 / 母集団σ = 0.005726 -> **significant** / 標本σ = 0.007013 -> **not_significant**

`undecidable` は 2 件。いずれも paired にできない実験である。
- `transfer/t1a_probe_aug/t1a_probe_aug@val~relation_detr_augstrong_seed42` … unpaired のため同符号条件を判定できない
- `transfer/t1a_probe_frozen/t1a_probe_frozen@val~relation_detr_seed42` … unpaired のため同符号条件を判定できない

`not_significant` 9 件のうち **1 件は同符号条件で落ちている**（σ 条件は満たしている）。
σ だけを見て有意と判断すると誤る典型である。

全指標の判定は `runindex/verdicts.csv`（1 行 = 1 実験 × 1 指標）。

## 25. 🔴🔴 最重要: paired-σ は seed 効果ではなく**非決定性**を測っている

§24 で paired-σ が計算できるようになったが、**その σ が何を測っているか**には
重大な但し書きがある。Δ を解釈する前に必ず読むこと。

### 25.1 同一条件が再現しない（実測）

`s4_phase_baseline_015` と `_017` は次がすべて一致する:

| 項目 | 値 |
|---|---|
| `git_commit.txt` | `bd0609749afdfa2a`（両者同一） |
| `config.yaml` の sha256 | `9cf8c2dde6920f01`（バイト一致） |
| `command.sh` | `python scripts/train_s4_tecno.py --seed 42`（同一） |
| `server.txt` | `efros`（同一） |

それでも結果は違う:

```
phase_accuracy   0.9042904290429042  vs  0.8970297029702970   (Δ = 0.00726)
phase_macro_f1   0.7405981456025096  vs  0.6571673826301749   (Δ = 0.08343)
epoch (best)     49                  vs  31
```

### 25.2 seed は分散を制御できていない

対照実験（17 run / seed42×7・123×5・456×5）で、
**同一 seed 内のばらつきが seed 間のばらつきを全指標で上回る**:

| 指標 | within-seed σ | between-seed σ | 比 |
|---|---:|---:|---:|
| accuracy | 0.004647 | 0.003385 | **1.37** |
| macro_f1 | 0.020214 | 0.008879 | **2.28** |
| jaccard | 0.019112 | 0.007814 | **2.45** |
| edit_score | 1.981335 | 1.478973 | **1.34** |
| seg_f1_50 | 0.031471 | 0.019595 | **1.61** |

### 25.3 原因 — GPU の決定性が一切制御されていない

```python
# scripts/train_s4_tecno.py:192-195
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
random.seed(args.seed)
np.random.seed(args.seed)
torch.manual_seed(args.seed)      # ← CPU 側のみ
```

`torch.cuda.manual_seed_all` / `torch.use_deterministic_algorithms` /
`cudnn.deterministic` / DataLoader の `worker_init_fn` / `generator` /
`PYTHONHASHSEED` は **1 つも設定されていない**。
さらに 50 epoch の best-of-N 選択（`:263`）が非決定性を増幅する
（best epoch が 31〜50 に散る）。

リポジトリ自身の診断ツール `scripts/analysis/diag_same_seed_variance.py` も
同じ結論を出す: `N1 VERDICT: CONFIG_DIFF + UNCONTROLLED_NONDETERMINISM`。

### 25.4 Δ の解釈への含意

1. **paired-σ は「seed を変えたときの変動」ではなく「同じ設定で回し直したときの
   変動」を主に測っている。** §10.1 の「3-seed の σ」という想定は成立していない。
2. `significant` と出た実験も、**測っているのは注入効果 + 非決定性**である。
   Δ が within-seed σ（accuracy で 0.0046）より小さい主張は特に慎重に扱うこと。
3. seed ごとに **1 本を選ぶ**代表規約（`latest` / `first` / mtime 最大）は、
   within-seed 分布から 1 標本を引くことに等しい。
   **`mean` を既定にしたのはこの理由による**（within-seed ノイズを平均で潰す）。
   同じ発想はリポジトリ内に先例がある —
   `scripts/paired_sigma_3seed.py:5`「phase_seed を平均 → phase 学習の非決定性を除去」。

### 25.5 代表選択の規約がリポジトリ内で 4 つに割れている

| 方式 | 出典 |
|---|---|
| seq 最大 | `src/egosurgery/utils/transfer_delta_report.py:55,86-87` |
| mtime 最大 | `scripts/report_daux_paired.py:12-13,43-47` |
| 辞書順末尾 | `scripts/report_t1a_boundary.py:46-49` / `compare_causal_decode.py:76` |
| 代表を選ばず平均 | `scripts/paired_sigma_3seed.py:5,59-60` |
| **規約を決めないと明記** | `scripts/analysis/delta_allrun_recompute.py:4-10` |

なお mtime 方式は使えない。`metrics.json` の mtime は git チェックアウト時刻
（全件 2026-07-31 14:49）であり実験の新旧を表していない。

**根本対処は「非決定性を制御して再実行する」ことであり、
代表値の選び方を工夫することではない。**（backlog B-20）

## 26. 非決定性の棚卸しと影響範囲

§25 の欠陥が `train_s4_tecno.py` 固有かを全スクリプトで確認した。
全件は `anomalies/determinism_audit.csv`。

### 26.1 🔴 決定的になり得る学習スクリプトは **1 本も無い**

監査 32 スクリプト / うち CUDA を使う **15** 本 / 
`can_be_deterministic = True` は **0** 本。

| 制御項目 | 設定している本数 |
|---|---:|
| `random_seed` | 15 / 15 |
| `numpy_seed` | 15 / 15 |
| `torch_manual_seed` | 15 / 15 |
| `cuda_manual_seed` | 2 / 15 |
| `use_deterministic_algorithms` | 0 / 15 |
| `cudnn_deterministic` | 2 / 15 |
| `cudnn_benchmark` | 2 / 15 |
| `pythonhashseed` | 2 / 15 |
| `dataloader_worker_init_fn` | 0 / 15 |
| `dataloader_generator` | 0 / 15 |
| `cublas_workspace_config` | 0 / 15 |

**`torch.use_deterministic_algorithms` はどのスクリプトも呼んでいない。**
これが無い限り GPU 上で bit 単位の再現は保証されないため、
`can_be_deterministic` は全件 `False` になる。

### 26.1.1 制御の張り方が 2 系統に分かれている

`seed_setup_via` 列で区別できる。

| seed_setup_via | 本数 | 意味 |
|---|---:|---|
| `direct` | 13 | ファイル内で直接 seed を張る（`scripts/train_*.py` 系）|
| `seed_everything` | 1 | `src/egosurgery/utils/seed.py` のヘルパ経由 |
| `seed_everything+delegates_to_engines` | 3 | ヘルパを呼びつつ更に委譲もする |
| `delegates_to_engines` | 1 | 自分では触らず trainer に委譲（`src/egosurgery/train.py`）|
| `none` | 5 | seed を張らない |

**`seed_everything()` は 6 項目を設定している**
（`random` / `PYTHONHASHSEED` / `numpy` / `torch.manual_seed` /
`torch.cuda.manual_seed_all` / `cudnn.deterministic=True` / `cudnn.benchmark=False`）。
したがって Hydra 経路（`src/egosurgery/`）は `scripts/train_*.py` 系より制御が厚い。

> ⚠️ **この表はファイル単位の静的解析である。** 委譲は 1 段だけ追っている
> （`seed_everything` の呼び出しと `_select_trainer` 系の委譲）。
> `src/egosurgery/train.py` の行は `delegates_to_engines` であり、
> 実際の制御状況は委譲先 `engines/*_trainer.py` の行を見ること。

一方 `scripts/train_*.py` 系（**`direct`**、run 数で見て大半）は
CPU 側 3 種のみで **GPU 側の制御が 1 つも無い**。

影響を受ける run: **527**（CUDA 学習スクリプトが entrypoint の run）

| スクリプト | run 数 | 欠落している必須項目 |
|---|---:|---|
| `scripts/train_b2a.py` | 265 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |
| `scripts/train_t1a.py` | 132 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |
| `scripts/train_s4_tecno.py` | 61 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |
| `scripts/train_hand2det.py` | 21 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |
| `scripts/train_haux.py` | 18 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |
| `scripts/train_taux.py` | 15 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |
| `scripts/train_t1a_regiontraj.py` | 6 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |
| `scripts/train_t1b.py` | 6 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |
| `scripts/train_t1a_boundary.py` | 3 | `cuda_manual_seed,use_deterministic_algorithms,cudnn_deterministic` |

### 26.2 監査できなかったもの

| スクリプト | 状態 | run 数 |
|---|---|---:|
| `src/egosurgery/engines/hooks.py` | `empty` | 0 |
| `src/egosurgery/engines/stage_b_trainer.py` | `empty` | 0 |
| `src/egosurgery/engines/stage_c_trainer.py` | `empty` | 0 |
| `src/egosurgery/engines/stage_d_trainer.py` | `empty` | 0 |
| `src/egosurgery/engines/validator.py` | `empty` | 0 |
| `tmp/queue_runner/train_s4_tecno_aligndetr.py` | `missing` | 3 |
| `tools/train.py` | `missing` | 1 |
| `tools/train_net_egosurgery.py` | `missing` | 3 |
| `train_net_egosurgery.py` | `missing` | 3 |

`empty` は 0 バイトの scaffold、`missing` は**この worktree に**実体が無いもの。

`missing` は「存在しない」ではなく「`third_party/` が同期対象外」である
（`.stglobalignore` が `third_party` を除外。入れ子 `.git` を含むため）。
本体側 `/home/ubuntu/slocal2/m2/third_party/` には Co-DETR / DAC-DETR /
DI-MaskDINO / MaskDINO / Mr.DETR / Relation-DETR / Stable-DINO / detrex がある。
**したがってこれらの run の決定性は runindex 単独では確認できない。**

### 26.2.1 第三者 entrypoint について分かっていること

本体側の実体を読んだ範囲では、制御の状況は自前スクリプトと異なる:

| entrypoint | 状況 |
|---|---|
| Relation-DETR | `main.py:123-127` に **完全な決定性ブロック**（`use_deterministic_algorithms` / `worker_init_fn` / `generator`）がある。ただし `--use-deterministic-algorithms` フラグでゲートされており、該当 run の `command.sh` は渡していない。さらに `--mixed-precision fp16` で走っている |
| detrex | detectron2 の `default_setup` が seed 系と `worker_init_fn` を張るが、`cudnn.deterministic` と `use_deterministic_algorithms` は設定しない |

**フラグ 1 つで決定的にできる経路が存在するのに使われていない**、というのが
Relation-DETR 経路の状況である。

### 26.2.2 監査表を読むときの注意

| 列 | 注意 |
|---|---|
| `dataloader_worker_init_fn` / `dataloader_generator` | **DataLoader を使わないスクリプトには該当しない。** 自前スクリプト 8 本は `DataLoader` を一切使わず、メモリ上の clip リストを `random.shuffle` で並べ替えている。`uses_dataloader` 列で判別すること |
| `pythonhashseed` | `os.environ["PYTHONHASHSEED"]` への**実行時代入は効かない**。CPython のハッシュ乱択はインタプリタ起動時に確定するため、既に走っているプロセスには影響しない。実効性は `pythonhashseed_effective` 列（シェル側の export を検出）で見ること。**実測では 0 / 20** |
| `explicitly_disables_determinism` | `src/egosurgery/engines/mmdet_trainer.py` は `mmcfg.randomness = dict(..., deterministic=False, ...)` を明示指定し、**mmengine 側の決定化を止めている**。制御が「無い」のではなく「切っている」 |

### 26.3 影響範囲の定量 — within-seed と between-seed の比較

全件は `anomalies/within_vs_between_seed.csv`（1 行 = 1 実験 × 1 指標）。

- 反復がある (実験 × 指標) の組: **101**
- そのうち **within > between**: **47**
  - 条件混在の交絡あり: 36
  - 交絡なし（純粋に非決定性）: **11**

**⚠️ 単純に「47 件で within が上回る」と読んではいけない。**
`b2a_ro_oracle_noise000` のように 1 つの名前に 4 水準の条件が混ざっている実験
（§7.3）では、within-seed のばらつきは非決定性ではなく**条件差**である。
`within_is_confounded_by_condition` 列で切り分けること。

| step | 組数 | 比の中央値 | 比の最大 |
|---|---:|---:|---:|
| `t1a_3seed_det42_aug` | 4 | 2.119 | 2.150 |
| `b2a_det2phase_toolpresence` | 2 | 1.423 | 1.439 |
| `base` | 2 | 1.192 | 1.260 |
| `t1a_3seed_det42_frozen` | 3 | 1.128 | 1.271 |

### 26.4 🔴 汚染された 1 つの分母が 117 実験に伝播している

Δ の σ は注入側と対照側の**合成**なので、対照が汚染されていれば
それを分母に使う全実験の σ が汚染される。

対照実験 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`
の within/between 比は **accuracy 1.373 / macro_f1 2.277**（交絡なし）。
この実験を `control_of` に持つ実験がその比を継承する。

| `sigma_interpretation` | 実験数 |
|---|---:|
| `mixed_with_nondeterminism` | 123 |
| `seed_effect` | 8 |
| `unknown` | 5 |

**`control_of` を持つ 136 実験のうち 123 の σ は seed 効果を測っていない。**

うち `verdict_10_1 = significant` は **115** 件。
これらは「§10.1 の条件は満たすが、σ が想定どおりのものではない」状態である。
**判定を無効とするか、非決定性を制御して再実行するかは研究上の判断**であり、
harvester は判定を消さずに `sigma_interpretation` で印を付けるに留める。

## 27. 論点: 「全 seed 同符号」条件は dedup 後も同じ意味か

**これは判断を仰ぐための論点整理であり、harvester は定義を変えていない。**

### 27.1 何が変わったか

§24 で seed ごとに複数 run がある場合 `mean` で畳むようにした。その結果:

| | 畳み込み前 | 畳み込み後（現在） |
|---|---|---|
| 「全 seed 同符号」の対象 | 個々の run の Δ | **seed 平均どうしの Δ** |
| 符号を見る個数 | run 数（対照側は最大 7）| seed 数（通常 3） |

### 27.2 🔴 そもそも正本に「同符号」の規定は無い

`docs/m2_plan_rewrite/` を全文検索しても **「同符号」は 0 件**である。
この条件は 2026-06-20 の運用判断として実験ログに導入された:

> `docs/experiment_log.md:527`
> 「`scripts/analyze_phase_coupling.py` を **paired-σ 判定に改修**
> （matched 差の有意性を base 群σでなく **対seed差σ + 全seed同符号**で判定）」

### 27.3 論点

1. **既存実装は「個々の run の Δ」の符号を見ている。**
   `scripts/report_t1a_boundary.py:57-61` / `report_daux_paired.py:66-73` /
   `analyze_t1a_factorial_ablation.py:124-125` はいずれも
   `d = [vals[s] - base[s] for s in SEEDS]`（seed ごとに 1 run）である。
   **平均してから符号を見る実装はリポジトリ内に無い**
   （`paired_sigma_3seed.py` は平均するが、平均する軸は phase_seed で
   符号を見る軸 detector_seed とは別軸）。
   したがって現在の runindex の方式（符号軸と同じ軸を mean で畳んでから
   符号を見る）には**先例が無い**。
2. **平均は符号のばらつきを隠す。** 同一 seed 内で Δ の符号が
   割れていても、平均の符号は片方に決まる。§25 のとおり同一条件反復の
   ばらつきが大きいため、これは実際に起こりうる。
3. **n=3 の同符号条件は偶然一致しやすい。** 効果が無くても
   3 つの符号が揃う確率は 2 × (1/2)^3 = **25%**。
   σ 条件と併せた偶然通過率も σ 条件単独からわずかしか下がらず、
   n=3 では検出力の裏付けとして弱い。
4. 代替案としては「全 run の Δ の符号が揃う」（より厳しい）、
   「符号一致率を出す」（連続量にする）などがありうる。

現状は `delta_same_sign_<metric>`（seed 平均ベース）を出しており、
`delta_n_seeds_<metric>` で何個の符号を見たかが分かる。

### 27.4 判断: **保留**（2026-08-01）

利用者の判断により定義変更は保留となった。理由:

> σ の 123/136 が `mixed_with_nondeterminism` である以上、
> どの定義を採っても σ そのものが汚染されている。
> **条件の定義より B-20（非決定性の解消）が先。**

参考として 3 案の実測値（`accuracy` / 134 実験）:

| 案 | 定義 | 同符号となる実験数 |
|---|---|---:|
| 現状 | seed 平均どうしの Δ の符号が揃う | **125** |
| 厳格 | 全 run 組合せの差の符号が揃う | 124 |
| 連続量 | 符号一致率（中央値 1.000 / 最小 0.529） | 一致率 100% が 124 |

3 案の差は 1 件しかない。**定義の選択より σ の汚染の方が影響が大きい**
という判断は実測に整合している。

