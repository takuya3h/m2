# anomalies — 規約から外れたもの・判断を保留したもの

`tools/harvest_runindex.py` が自動生成する。手で編集しない。

## 1. 除外した run

`experiments/README.md` に `_` 接頭辞が「解析対象外」を意味するという規約は
**明文化されていない**。以下はディレクトリ名の意味からの判断であり、
規約に基づくものではない。**除外規約の明文化を推奨する。**

除外 19 run / 全 573 run（削除ではなくフラグ）

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

確定不能 6 run / 全 573 run

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

確定不能 28 run

| host_raw | runs | 理由 |
|---|---:|---|
| `None` | 18 | server.txt 欠損かつ eval_recipe.server_name 無し |
| `aolab` | 10 | philip / ilya の双方が返すコンテナ内 hostname のため一意に特定不能 |

## 4. per_class_ap.json のクラス体系が 2 種類ある

ファイル名は `per_class_ap.json` だが、中身は 2 つの異なる体系が混在する。
**横断比較の際に混ぜてはならない。**

**ファイル名が `per_class_ap.json` でありながら中身が F1 の群があるため、
`per_class_kind` だけでなく `per_class_metric` を必ず参照すること。**
`per_class_source` に読み取り元の相対パスを保持している。

| per_class_kind | per_class_metric | runs | 内容 | 根拠 |
|---|---|---:|---|---|
| `phase` | `F1` | 500 | 9 クラスの工程別 **F1**（AP ではない） | `scripts/train_{b2a,t1a,s4_tecno,haux,taux,t1a_boundary,t1a_regiontraj}.py` が `best.get("phase_per_class_f1", {})` を `log_per_class_ap()` に渡している |
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

## 7. ディレクトリ名に補助 seed を含む run

`det42` / `p123` のように、末尾の `seed<N>` とは別の seed が名前に含まれる run。
後段の paired 統計では比較単位が **(検出器 seed, 工程 seed) の組**であり、
末尾 seed だけでは基準点を特定できない。機械的に結合できるよう
`seed_detector` / `seed_phase` の専用フィールドに分離している。

該当 101 run

| path | seed (末尾) | seed_detector | seed_phase |
|---|---:|---:|---:|
| `experiments/transfer/b2a_base_oracle_noise_p010_001_b2a_base_oracle_noise_p010_seed42` | 42 | — | 10 |
| `experiments/transfer/b2a_base_oracle_noise_p010_002_b2a_base_oracle_noise_p010_seed123` | 123 | — | 10 |
| `experiments/transfer/b2a_base_oracle_noise_p010_003_b2a_base_oracle_noise_p010_seed456` | 456 | — | 10 |
| `experiments/transfer/b2a_base_oracle_noise_p020_001_b2a_base_oracle_noise_p020_seed42` | 42 | — | 20 |
| `experiments/transfer/b2a_base_oracle_noise_p020_002_b2a_base_oracle_noise_p020_seed123` | 123 | — | 20 |
| `experiments/transfer/b2a_base_oracle_noise_p020_003_b2a_base_oracle_noise_p020_seed456` | 456 | — | 20 |
| `experiments/transfer/b2a_base_oracle_noise_p030_001_b2a_base_oracle_noise_p030_seed42` | 42 | — | 30 |
| `experiments/transfer/b2a_base_oracle_noise_p030_002_b2a_base_oracle_noise_p030_seed123` | 123 | — | 30 |
| `experiments/transfer/b2a_base_oracle_noise_p030_003_b2a_base_oracle_noise_p030_seed456` | 456 | — | 30 |
| `experiments/transfer/b2a_base_oracle_top3noise_p010_001_b2a_base_oracle_top3noise_p010_seed42` | 42 | — | 10 |
| `experiments/transfer/b2a_base_oracle_top3noise_p010_002_b2a_base_oracle_top3noise_p010_seed123` | 123 | — | 10 |
| `experiments/transfer/b2a_base_oracle_top3noise_p010_003_b2a_base_oracle_top3noise_p010_seed456` | 456 | — | 10 |
| `experiments/transfer/b2a_base_oracle_top3noise_p020_001_b2a_base_oracle_top3noise_p020_seed42` | 42 | — | 20 |
| `experiments/transfer/b2a_base_oracle_top3noise_p020_002_b2a_base_oracle_top3noise_p020_seed123` | 123 | — | 20 |
| `experiments/transfer/b2a_base_oracle_top3noise_p020_003_b2a_base_oracle_top3noise_p020_seed456` | 456 | — | 20 |
| `experiments/transfer/b2a_base_oracle_top3noise_p030_001_b2a_base_oracle_top3noise_p030_seed42` | 42 | — | 30 |
| `experiments/transfer/b2a_base_oracle_top3noise_p030_002_b2a_base_oracle_top3noise_p030_seed123` | 123 | — | 30 |
| `experiments/transfer/b2a_base_oracle_top3noise_p030_003_b2a_base_oracle_top3noise_p030_seed456` | 456 | — | 30 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p010_001_b2a_ro_oracle_bipolarnoise_p010_seed42` | 42 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p010_002_b2a_ro_oracle_bipolarnoise_p010_seed123` | 123 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p010_003_b2a_ro_oracle_bipolarnoise_p010_seed456` | 456 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p020_001_b2a_ro_oracle_bipolarnoise_p020_seed42` | 42 | — | 20 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p020_002_b2a_ro_oracle_bipolarnoise_p020_seed123` | 123 | — | 20 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p020_003_b2a_ro_oracle_bipolarnoise_p020_seed456` | 456 | — | 20 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p030_001_b2a_ro_oracle_bipolarnoise_p030_seed42` | 42 | — | 30 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p030_002_b2a_ro_oracle_bipolarnoise_p030_seed123` | 123 | — | 30 |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p030_003_b2a_ro_oracle_bipolarnoise_p030_seed456` | 456 | — | 30 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p010_001_b2a_ro_oracle_bsnoise_p010_seed42` | 42 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p010_002_b2a_ro_oracle_bsnoise_p010_seed123` | 123 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p010_003_b2a_ro_oracle_bsnoise_p010_seed456` | 456 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p020_001_b2a_ro_oracle_bsnoise_p020_seed42` | 42 | — | 20 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p020_002_b2a_ro_oracle_bsnoise_p020_seed123` | 123 | — | 20 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p020_003_b2a_ro_oracle_bsnoise_p020_seed456` | 456 | — | 20 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p030_001_b2a_ro_oracle_bsnoise_p030_seed42` | 42 | — | 30 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p030_002_b2a_ro_oracle_bsnoise_p030_seed123` | 123 | — | 30 |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p030_003_b2a_ro_oracle_bsnoise_p030_seed456` | 456 | — | 30 |
| `experiments/transfer/b2a_ro_oracle_nhnoise_p010_001_b2a_ro_oracle_nhnoise_p010_seed42` | 42 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_nhnoise_p010_002_b2a_ro_oracle_nhnoise_p010_seed123` | 123 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_nhnoise_p010_003_b2a_ro_oracle_nhnoise_p010_seed456` | 456 | — | 10 |
| `experiments/transfer/b2a_ro_oracle_nhnoise_p020_001_b2a_ro_oracle_nhnoise_p020_seed42` | 42 | — | 20 |
| … 他 61 件 | | | |

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
| ディレクトリ名に補助 seed {...} が含まれる。seed には末尾の seed<N> のみを採用し、det/p は seed_detector / seed_phase に分離した。 | 101 |
| val と test の指標が共存する。primary（best 選択元）は val。test 側は metrics_by_split['...'] に保持している。 | 27 |
| host '...' は実サーバーを一意に特定できない。host は null にした。 | 10 |
| per_class_ap.json が空 ({...}) | 8 |
| run 名が命名規約 <step>_<seq3>_<desc>_seed<N> に一致しない | 6 |
| metrics.json が空 ({...}) | 6 |
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
実測は **156 種**。README に無い以下の系統が存在する。

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
| `experiments/transfer/b2b_rescore_alpha0.5` | `alpha`, `delta_detection`, `denominator`, `mAP_baseline`, `mAP_rescored`, `method` |
| `experiments/transfer/b2b_rescore_alpha1.0` | `alpha`, `delta_detection`, `denominator`, `mAP_baseline`, `mAP_rescored`, `method` |
| `experiments/transfer/b2b_rescore_alpha2.0` | `alpha`, `delta_detection`, `denominator`, `mAP_baseline`, `mAP_rescored`, `method` |
| `experiments/transfer/t1b_phasefilm_001_t1b_phasefilm_seed123` | `control_init_mAP`, `control_mAP`, `delta_control`, `delta_detection`, `init_mAP`, `injection_effect` |
| `experiments/transfer/t1b_phasefilm_002_t1b_phasefilm_seed456` | `control_init_mAP`, `control_mAP`, `delta_control`, `delta_detection`, `init_mAP`, `injection_effect` |

### 13.1 🔴 正本の記述の例外 — test 評価を持つ run

正本は「test split は未評価」と述べているが、その後 `--eval-test` が実装され、
**test 側の数値を持つ run が実在する**。正本の記述はこの時点より前のもの。

該当 27 run。全件の val/test 対応表は `anomalies/val_test_pairs.csv`。

**index.csv の `metric.<name>` 列は primary(val) の値である。**
test 側は `metric_test.<name>` 列に別出ししてある（`has_test` 列で絞り込める）。
この分離が無いと「split 列が val 一色 → test 評価は存在しない」と誤読される。

#### val / test の乖離（実測・全 27 run）

| 指標 | val 平均 | test 平均 | 差 (test - val) | n |
|---|---:|---:|---:|---:|
| `sticky_jaccard` | 0.7403 | 0.4563 | -0.2839 | 3 |
| `jaccard` | 0.6982 | 0.4571 | -0.2411 | 27 |
| `sticky_macro_f1` | 0.7864 | 0.5529 | -0.2335 | 3 |
| `macro_f1` | 0.7490 | 0.5587 | -0.1903 | 27 |
| `sticky_accuracy` | 0.9362 | 0.7861 | -0.1501 | 3 |
| `accuracy` | 0.9183 | 0.7900 | -0.1283 | 27 |
| `seg_f1_50` | 0.4325 | 0.3580 | -0.0745 | 27 |
| `sticky_seg_f1_50` | 0.5422 | 0.4854 | -0.0568 | 3 |
| `seg_f1_25` | 0.4819 | 0.4979 | +0.0160 | 27 |
| `seg_f1_10` | 0.4945 | 0.5155 | +0.0211 | 27 |
| `sticky_seg_f1_25` | 0.6029 | 0.6323 | +0.0293 | 3 |
| `sticky_seg_f1_10` | 0.6106 | 0.6411 | +0.0304 | 3 |
| `edit_score` | 41.3984 | 44.7763 | +3.3779 | 27 |
| `sticky_edit_score` | 50.5944 | 59.0140 | +8.4196 | 3 |

| path | seed | excluded |
|---|---:|---|
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

`run_id`（ディレクトリ名）は **6 種が複数箇所で衝突**する。
スキーマは `runs/<run_id>.json` を指定しているが、そのままではファイルが
上書きされるため、パス由来の `ledger_key` をファイル名に使い、
`run_id` はフィールドとして保持した。

| run_id | 箇所数 |
|---|---:|
| `s0_001_maskdino_bbox_seed42` | 3 |
| `s0_002_maskdino_bbox_seed123` | 3 |
| `s0_003_maskdino_bbox_seed456` | 3 |
| `s0_004_varifocanet_bbox_seed42` | 3 |
| `s0_005_varifocanet_bbox_seed123` | 3 |
| `s0_006_varifocanet_bbox_seed456` | 3 |

