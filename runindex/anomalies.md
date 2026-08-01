# anomalies — 規約から外れたもの・判断を保留したもの

`tools/harvest_runindex.py` が自動生成する。手で編集しない。

## 1. 除外した run

`experiments/README.md` に `_` 接頭辞が「解析対象外」を意味するという規約は
**明文化されていない**。以下はディレクトリ名の意味からの判断であり、
規約に基づくものではない。**除外規約の明文化を推奨する。**

除外 19 run / 全 615 run（削除ではなくフラグ）

| exclusion_reason | runs | 対象 |
|---|---:|---|
| `failed_run` | 6 | `experiments/phase0/_failed_s3_weighted` |
| `known_bad_split` | 6 | `experiments/baselines/_wrong_split_8_2_3` |
| `smoke_test` | 7 | `experiments/_smoke_prior`, `experiments/baselines/_smoke_ddq` |

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

確定不能 6 run / 全 615 run

| split_provenance | runs |
|---|---:|
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

## 3. host を確定できなかった run

確定不能 58 run

| host_raw | runs | 理由 |
|---|---:|---|
| `None` | 48 | server.txt 欠損かつ eval_recipe.server_name 無し |
| `aolab` | 10 | philip / ilya の双方が返すコンテナ内 hostname のため一意に特定不能 |

## 4. per_class_ap.json のクラス体系が 2 種類ある

ファイル名は `per_class_ap.json` だが、中身は 2 つの異なる体系が混在する。
**横断比較の際に混ぜてはならない。**

**ファイル名が `per_class_ap.json` でありながら中身が F1 の群があるため、
`per_class_kind` だけでなく `per_class_metric` を必ず参照すること。**
`per_class_source` に読み取り元の相対パスを保持している。

| per_class_kind | per_class_metric | runs | 内容 | 根拠 |
|---|---|---:|---|---|
| `phase` | `F1` | 542 | 9 クラスの工程別 **F1**（AP ではない） | `scripts/train_{b2a,t1a,s4_tecno,haux,taux,t1a_boundary,t1a_regiontraj}.py` が `best.get("phase_per_class_f1", {})` を `log_per_class_ap()` に渡している |
| `tool` | `AP` | 62 | 15 クラスの術具 AP | `per_class_coco_map` / `COCOeval.precision` 由来 |
| `None` | `None` | 11 | `per_class_ap.json` が無い・空・パース失敗 | — |

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
| `Retractor` | 50 | `experiments/baselines`, `experiments/baselines/_smoke_ddq`, `experiments/transfer` |
| `Mouth Gag`, `Skewer` | 6 | `experiments/baselines/_wrong_split_8_2_3` |

### 平均の取り方への含意

`NaN` を 0 として平均すると mAP を過小評価する。`per_class_valid_count` を
分母に使うこと（15 固定にしない）。

## 6. 命名規約から外れた run

`<step>_<seq3>_<desc>_seed<N>` に一致しない run: 6

- `experiments/phase0/_failed_s3_weighted/_004_partial`
- `experiments/phase0/_failed_s3_weighted/_005_partial`
- `experiments/phase0/_failed_s3_weighted/_006_partial`
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
| `ablations` | 1 | `.gitkeep` のみ | 未着手 scaffold |
| `analysis` | 86 | EDA レポート / 図 (png) / CSV / JSON | **あり**: `detector_sanity/reldetr_seed42_val_perclass.json` (COCO 形式 `AP`/`AP50`/`AP75`/`AP_s`/`AP_m` 等 13 キー)、`signature_subset_detector_compare/results.json` (`per_class` キー) |
| `audit` | 3 | `audit_report.json` × 3 | なし (`inject` / `trainable` / `n_trainable_params` 等の学習設定監査) |
| `detector_improve` | 5 | `label_names.txt` / `val_perclass.json` | **あり**: `augstrong_seed42/val_perclass.json` (COCO 形式 13 キー) |
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
| val と test の指標が共存する。primary（best 選択元）は val。test 側は metrics_by_split['...'] に保持している。 | 69 |
| ディレクトリ名の p010 は seed ではない。command.sh が --tool-noise-rate を渡しており、ノイズ率 0.01 を指す。seed_phase には入れない。 | 24 |
| ディレクトリ名の p020 は seed ではない。command.sh が --tool-noise-rate を渡しており、ノイズ率 0.02 を指す。seed_phase には入れない。 | 24 |
| ディレクトリ名の p030 は seed ではない。command.sh が --tool-noise-rate を渡しており、ノイズ率 0.03 を指す。seed_phase には入れない。 | 24 |
| config.yaml のパースに失敗: ConstructorError | 15 |
| host '...' は実サーバーを一意に特定できない。host は null にした。 | 10 |
| run 名に seq (3 桁連番) が無い別系統の命名: base_seed<N>。step には description を充てた。 | 9 |
| run 名に seq (3 桁連番) が無い別系統の命名: bboxROI_seed<N>。step には description を充てた。 | 9 |
| per_class_ap.json が空 ({...}) | 8 |
| 同一 (group, step, description, split) 内で eval_recipe_id が 2 通りに食い違う。評価条件が違う run を束ねないため experiment_id を #None で分離した。 | 6 |
| 同一 (group, step, description, split) 内で eval_recipe_id が 2 通りに食い違う。評価条件が違う run を束ねないため experiment_id を #a63aecae で分離した。 | 6 |
| run 名が命名規約 <step>_<seq3>_<desc>_seed<N> に一致しない | 6 |
| metrics.json が空 ({...}) | 6 |
| config.yaml のパースに失敗: ParserError | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: shuffleROI_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: bboxROI_handROIbbox2_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: handPresence_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: handROIbbox2_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: handROIbbox4_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: handROImask2_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: maskROI_seed<N>。step には description を充てた。 | 3 |
| run 名に seq (3 桁連番) が無い別系統の命名: randROI_seed<N>。step には description を充てた。 | 3 |
| per_class_ap.json が存在しない | 3 |

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

該当 5 run

| path | mAP 系のキー | entrypoint | commit |
|---|---|---|---|
| `experiments/transfer/b2b_rescore_alpha0.5` | `mAP_baseline`, `mAP_rescored` | — | `a697d90b88` |
| `experiments/transfer/b2b_rescore_alpha1.0` | `mAP_baseline`, `mAP_rescored` | — | `a697d90b88` |
| `experiments/transfer/b2b_rescore_alpha2.0` | `mAP_baseline`, `mAP_rescored` | — | `a697d90b88` |
| `experiments/transfer/t1b_phasefilm_001_t1b_phasefilm_seed123` | `control_init_mAP`, `control_mAP`, `init_mAP`, `mAP` | `scripts/postprocess_t1b.py` | `a697d90b88` |
| `experiments/transfer/t1b_phasefilm_002_t1b_phasefilm_seed456` | `control_init_mAP`, `control_mAP`, `init_mAP`, `mAP` | `scripts/postprocess_t1b.py` | `a697d90b88` |

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
実測は **166 種**。README に無い以下の系統が存在する。

| 系統 | step 識別子の種類 | run 合計 | 例 |
|---|---:|---:|---|
| `b1` | 1 | 6 | `b1_mtl` |
| `b2a` | 74 | 265 | `b2a_det2phase_toolpresence`, `b2a_ro_oracle_noise000` |
| `t1a` | 56 | 132 | `t1a_deep_3s10l96f`, `t1a_region_only` |
| `t1b` | 1 | 2 | `t1b_phasefilm` |
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

既定を適用した run: 5

| path | 指標キー |
|---|---|
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

`s4_phase_baseline` の `notes.md` は **55 件すべてで**
「凍結源: Relation-DETR seed42」と断言するが、`config.yaml` の実際の
`frozen_source.cache_dir` がそれと異なる run が **38 件**ある
（うち 24 件は検出器 seed が 123 / 456）。`config.yaml` の `frozen_source.seed` も
`42` がハードコードされており同様に信用できない。
いずれも `scripts/train_s4_tecno.py` の固定文字列に由来する。

**したがって `frozen_source_tag` はキャッシュのパスからのみ導き、
`frozen_source.seed` と `notes.md` の記述は採用していない。**

- 実験数: **181** / run 数 615
- `experiment_id` を付けられなかった run: 6
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
| `no_denominator_declared` | 174 |
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

- `per_class_kind=tool` : 62 run × 15 クラス（術具 **AP**）
- `per_class_kind=phase`: 542 run × 9 クラス（工程 **F1**）

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
| 1σ | 124 | 124 | **0** |
| 2σ | 122 | 122 | **0** |
| 3σ | 117 | 114 | **3** |

対象 134 実験。標本σ/母集団σ の実測中央値 = **1.0531**。

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

正本の研究計画（`docs/m2_plan_rewrite/`）は §10.1 の 1σ を
「同一 eval recipe での 3-seed std」としか書いておらず、**どちらか明示していない**。
したがって「どちらを使うべきか」の規範的根拠はリポジトリ内に存在しない。

`abs_delta_over_sigma_<metric>` は **母集団σ**（`delta_pstd_<metric>`）を分母にした。
§10.1 判定の実装側と揃えたためである。標本σで見たい場合は
`delta_sstd_<metric>` で割り直すこと（両方出してある）。
**規約の確定は正本側の作業であり、harvester が決めることではない（backlog B-9）。**

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
| `transfer/hires_relation_detr_augstrong_hires_seed42/hires_relation_detr_augstrong_hires_seed42@val~relation_detr_augstrong_hires_seed42` | +0.04004 | 13.49 | ✓ | **有意** |
| `transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_augstrong_hires_seed42` | +0.02354 | 10.49 | ✓ | **有意** |
| `transfer/t1a_boundary/t1a_boundary@val~relation_detr_seed42` | -0.00242 | 0.88 | ✗ | 非有意 |
| `transfer/t1a_regiontraj/t1a_regiontraj@val~relation_detr_seed42` | -0.00088 | 0.29 | ✗ | 非有意 |
| `transfer/t1a_regiontraj_test/t1a_regiontraj_test@val~relation_detr_seed42` | -0.00066 | 0.28 | ✗ | 非有意 |

これが現在の証跡で**実際に完成できる §10.1 判定のすべて**である。

## 23. seed の出所 — run の学習 seed に誤りは無い

§17.0 の「`notes.md` の凍結源 seed 記載が虚偽」を受けて、
**run 自身の学習 seed** が汚染されていないかを全件突き合わせた。
証拠は `command.sh` の `--seed` / `seed=` と `config.yaml` の `seed`。
`notes.md` は虚偽の実績があるため証拠に使っていない。

| seed_agreement | run 数 | 意味 |
|---|---:|---|
| `agree` | 567 | ディレクトリ名と他証拠が一致 |
| `unverified_no_other_evidence` | 42 | `command.sh` も `config.yaml` も無い（g2_* 群） |
| `no_seed_in_dirname` | 6 | 命名規約外 |
| **`conflict`** | **0** | **食い違い** |

**食い違いは 0 件。** したがって Δ の seed 対応が誤っている可能性は排除できる。
§17.0 の誤記は**凍結検出器の seed** の話であって、run の学習 seed ではない。

### 23.1 `frozen_source.seed` は信用できない（実測）

- `config.yaml` に `frozen_source.seed` を持つ run: **500**
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

