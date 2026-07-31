# anomalies — 規約から外れたもの・判断を保留したもの

`tools/harvest_ledger.py` が自動生成する。手で編集しない。

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

確定不能 11 run / 全 573 run

| split_provenance | runs |
|---|---:|
| `not_determinable` | 11 |

大半は `phase_*` 系の指標しか持たない run である。`phase_` はタスク名であり
split ではないため、これらの run の評価 split は証拠ファイルからは決まらない。

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
再検証: `python tools/verify_no_dummy_metrics.py`

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

## 13. run_id の衝突

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

