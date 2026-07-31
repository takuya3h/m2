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

## 2. split を確定できなかった run

指標キーの接頭辞から split を確定できない run。**推測していない**。

確定不能 490 run / 全 573 run

| split_provenance | runs |
|---|---:|
| `not_determinable` | 490 |

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

| per_class_kind | runs | 内容 |
|---|---:|---|
| `phase_metric` | 500 | 9 クラスの工程別指標（AP ではない。F1 の可能性が高い） |
| `tool_ap` | 62 | 15 クラスの術具 AP（本来の per-class AP） |
| `None` | 11 | per_class_ap.json が無い・空・パース失敗 |

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
`seed` フィールドには**末尾の `seed<N>` のみ**を採用し、補助 seed は
`aux_seeds` に分けて保持している。

該当 101 run

| path | seed (採用) | aux_seeds |
|---|---:|---|
| `experiments/transfer/b2a_base_oracle_noise_p010_001_b2a_base_oracle_noise_p010_seed42` | 42 | `{"p": 10}` |
| `experiments/transfer/b2a_base_oracle_noise_p010_002_b2a_base_oracle_noise_p010_seed123` | 123 | `{"p": 10}` |
| `experiments/transfer/b2a_base_oracle_noise_p010_003_b2a_base_oracle_noise_p010_seed456` | 456 | `{"p": 10}` |
| `experiments/transfer/b2a_base_oracle_noise_p020_001_b2a_base_oracle_noise_p020_seed42` | 42 | `{"p": 20}` |
| `experiments/transfer/b2a_base_oracle_noise_p020_002_b2a_base_oracle_noise_p020_seed123` | 123 | `{"p": 20}` |
| `experiments/transfer/b2a_base_oracle_noise_p020_003_b2a_base_oracle_noise_p020_seed456` | 456 | `{"p": 20}` |
| `experiments/transfer/b2a_base_oracle_noise_p030_001_b2a_base_oracle_noise_p030_seed42` | 42 | `{"p": 30}` |
| `experiments/transfer/b2a_base_oracle_noise_p030_002_b2a_base_oracle_noise_p030_seed123` | 123 | `{"p": 30}` |
| `experiments/transfer/b2a_base_oracle_noise_p030_003_b2a_base_oracle_noise_p030_seed456` | 456 | `{"p": 30}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p010_001_b2a_base_oracle_top3noise_p010_seed42` | 42 | `{"p": 10}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p010_002_b2a_base_oracle_top3noise_p010_seed123` | 123 | `{"p": 10}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p010_003_b2a_base_oracle_top3noise_p010_seed456` | 456 | `{"p": 10}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p020_001_b2a_base_oracle_top3noise_p020_seed42` | 42 | `{"p": 20}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p020_002_b2a_base_oracle_top3noise_p020_seed123` | 123 | `{"p": 20}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p020_003_b2a_base_oracle_top3noise_p020_seed456` | 456 | `{"p": 20}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p030_001_b2a_base_oracle_top3noise_p030_seed42` | 42 | `{"p": 30}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p030_002_b2a_base_oracle_top3noise_p030_seed123` | 123 | `{"p": 30}` |
| `experiments/transfer/b2a_base_oracle_top3noise_p030_003_b2a_base_oracle_top3noise_p030_seed456` | 456 | `{"p": 30}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p010_001_b2a_ro_oracle_bipolarnoise_p010_seed42` | 42 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p010_002_b2a_ro_oracle_bipolarnoise_p010_seed123` | 123 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p010_003_b2a_ro_oracle_bipolarnoise_p010_seed456` | 456 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p020_001_b2a_ro_oracle_bipolarnoise_p020_seed42` | 42 | `{"p": 20}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p020_002_b2a_ro_oracle_bipolarnoise_p020_seed123` | 123 | `{"p": 20}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p020_003_b2a_ro_oracle_bipolarnoise_p020_seed456` | 456 | `{"p": 20}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p030_001_b2a_ro_oracle_bipolarnoise_p030_seed42` | 42 | `{"p": 30}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p030_002_b2a_ro_oracle_bipolarnoise_p030_seed123` | 123 | `{"p": 30}` |
| `experiments/transfer/b2a_ro_oracle_bipolarnoise_p030_003_b2a_ro_oracle_bipolarnoise_p030_seed456` | 456 | `{"p": 30}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p010_001_b2a_ro_oracle_bsnoise_p010_seed42` | 42 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p010_002_b2a_ro_oracle_bsnoise_p010_seed123` | 123 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p010_003_b2a_ro_oracle_bsnoise_p010_seed456` | 456 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p020_001_b2a_ro_oracle_bsnoise_p020_seed42` | 42 | `{"p": 20}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p020_002_b2a_ro_oracle_bsnoise_p020_seed123` | 123 | `{"p": 20}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p020_003_b2a_ro_oracle_bsnoise_p020_seed456` | 456 | `{"p": 20}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p030_001_b2a_ro_oracle_bsnoise_p030_seed42` | 42 | `{"p": 30}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p030_002_b2a_ro_oracle_bsnoise_p030_seed123` | 123 | `{"p": 30}` |
| `experiments/transfer/b2a_ro_oracle_bsnoise_p030_003_b2a_ro_oracle_bsnoise_p030_seed456` | 456 | `{"p": 30}` |
| `experiments/transfer/b2a_ro_oracle_nhnoise_p010_001_b2a_ro_oracle_nhnoise_p010_seed42` | 42 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_nhnoise_p010_002_b2a_ro_oracle_nhnoise_p010_seed123` | 123 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_nhnoise_p010_003_b2a_ro_oracle_nhnoise_p010_seed456` | 456 | `{"p": 10}` |
| `experiments/transfer/b2a_ro_oracle_nhnoise_p020_001_b2a_ro_oracle_nhnoise_p020_seed42` | 42 | `{"p": 20}` |
| … 他 61 件 | | |

## 8. prefix 無しキーと prefix 付きキーの値が食い違った run

該当 27 run（食い違いがあれば両方を保持している）

- `experiments/phase1/s4_phase_baseline_044_frozen_tecno_phase_baseline_seed42`: `[{"key": "accuracy", "bare_value": 0.904950495049505, "by_split": {"test": 0.7638921453692848}}, {"key": "edit_score", "bare_value": 42.323232323232325, "by_split": {"test": 42.86948724219451}}, {"key": "jaccard", "bare_value": 0.6437220707441275, "by_split": {"test": 0.4340480112133478}}, {"key": "macro_f1", "bare_value": 0.7037869747452711, "by_split": {"test": 0.5455032007630578}}, {"key": "seg_f1_10", "bare_value": 0.4960558936218165, "by_split": {"test": 0.5140279300125847}}, {"key": "seg_f1_25", "bare_value": 0.4845616407482532, "by_split": {"test": 0.48436244062842526}}, {"key": "seg_f1_50", "bare_value": 0.3959882803696191, "by_split": {"test": 0.3457841107457476}}]`
- `experiments/phase1/s4_phase_baseline_045_frozen_tecno_phase_baseline_seed42`: `[{"key": "accuracy", "bare_value": 0.9148514851485149, "by_split": {"test": 0.7718640093786635}}, {"key": "edit_score", "bare_value": 43.88888888888889, "by_split": {"test": 30.02623488893512}}, {"key": "jaccard", "bare_value": 0.7187030719378921, "by_split": {"test": 0.4260420138582295}}, {"key": "macro_f1", "bare_value": 0.7701303805384035, "by_split": {"test": 0.5380027875171514}}, {"key": "seg_f1_10", "bare_value": 0.5090909090909091, "by_split": {"test": 0.39553730265397774}}, {"key": "seg_f1_25", "bare_value": 0.48484848484848486, "by_split": {"test": 0.3746915414025693}}, {"key": "seg_f1_50", "bare_value": 0.43939393939393945, "by_split": {"test": 0.21773748403836066}}]`
- `experiments/phase1/s4_phase_baseline_046_frozen_tecno_phase_baseline_seed123`: `[{"key": "accuracy", "bare_value": 0.8917491749174917, "by_split": {"test": 0.811957796014068}}, {"key": "edit_score", "bare_value": 37.28654970760234, "by_split": {"test": 40.931874990474164}}, {"key": "jaccard", "bare_value": 0.6241655876164166, "by_split": {"test": 0.4472762328866372}}, {"key": "macro_f1", "bare_value": 0.694838845820316, "by_split": {"test": 0.5506544189675069}}, {"key": "seg_f1_10", "bare_value": 0.4145124716553288, "by_split": {"test": 0.4810320665493079}}, {"key": "seg_f1_25", "bare_value": 0.400907029478458, "by_split": {"test": 0.46653481067274166}}, {"key": "seg_f1_50", "bare_value": 0.31700680272108844, "by_split": {"test": 0.3172720996858928}}]`
- `experiments/phase1/s4_phase_baseline_047_frozen_tecno_phase_baseline_seed123`: `[{"key": "accuracy", "bare_value": 0.9122112211221122, "by_split": {"test": 0.7873388042203986}}, {"key": "edit_score", "bare_value": 40.239316239316246, "by_split": {"test": 29.740999740999744}}, {"key": "jaccard", "bare_value": 0.6812336671374198, "by_split": {"test": 0.45375975236025934}}, {"key": "macro_f1", "bare_value": 0.7323610356186087, "by_split": {"test": 0.5563461966077813}}, {"key": "seg_f1_10", "bare_value": 0.4263038548752835, "by_split": {"test": 0.3995170907869321}}, {"key": "seg_f1_25", "bare_value": 0.39909297052154197, "by_split": {"test": 0.39169816074577984}}, {"key": "seg_f1_50", "bare_value": 0.308843537414966, "by_split": {"test": 0.23921642731166537}}]`
- `experiments/phase1/s4_phase_baseline_048_frozen_tecno_phase_baseline_seed456`: `[{"key": "accuracy", "bare_value": 0.8963696369636963, "by_split": {"test": 0.8105509964830012}}, {"key": "edit_score", "bare_value": 40.888888888888886, "by_split": {"test": 44.274551444362764}}, {"key": "jaccard", "bare_value": 0.6346341848981408, "by_split": {"test": 0.462786424906394}}, {"key": "macro_f1", "bare_value": 0.694503384922233, "by_split": {"test": 0.5575637024781585}}, {"key": "seg_f1_10", "bare_value": 0.43871506049228204, "by_split": {"test": 0.5044575522516699}}, {"key": "seg_f1_25", "bare_value": 0.41034626616604086, "by_split": {"test": 0.4910085829203476}}, {"key": "seg_f1_50", "bare_value": 0.3481852315394243, "by_split": {"test": 0.3390621633268693}}]`
- `experiments/phase1/s4_phase_baseline_049_frozen_tecno_phase_baseline_seed456`: `[{"key": "accuracy", "bare_value": 0.9155115511551155, "by_split": {"test": 0.7524032825322392}}, {"key": "edit_score", "bare_value": 48.433048433048434, "by_split": {"test": 45.92123769338959}}, {"key": "jaccard", "bare_value": 0.6856488442916397, "by_split": {"test": 0.4399887902880658}}, {"key": "macro_f1", "bare_value": 0.7343478846754862, "by_split": {"test": 0.5433594623816483}}, {"key": "seg_f1_10", "bare_value": 0.5656565656565656, "by_split": {"test": 0.5303864025434092}}, {"key": "seg_f1_25", "bare_value": 0.5525846702317291, "by_split": {"test": 0.5172957256596288}}, {"key": "seg_f1_50", "bare_value": 0.49613784907902553, "by_split": {"test": 0.36175987065568876}}]`
- `experiments/phase1/s4_phase_baseline_050_frozen_tecno_phase_baseline_seed42`: `[{"key": "accuracy", "bare_value": 0.8943894389438944, "by_split": {"test": 0.7535756154747948}}, {"key": "edit_score", "bare_value": 34.53968253968254, "by_split": {"test": 41.72633181844391}}, {"key": "jaccard", "bare_value": 0.6361511932415491, "by_split": {"test": 0.3805011634381095}}, {"key": "macro_f1", "bare_value": 0.6817126885167962, "by_split": {"test": 0.49513884612348696}}, {"key": "seg_f1_10", "bare_value": 0.39999999999999997, "by_split": {"test": 0.4661608022204316}}, {"key": "seg_f1_25", "bare_value": 0.3666666666666667, "by_split": {"test": 0.4332900587936848}}, {"key": "seg_f1_50", "bare_value": 0.29583333333333334, "by_split": {"test": 0.2751738442713463}}]`
- `experiments/phase1/s4_phase_baseline_051_frozen_tecno_phase_baseline_seed42`: `[{"key": "accuracy", "bare_value": 0.9161716171617161, "by_split": {"test": 0.8133645955451348}}, {"key": "edit_score", "bare_value": 36.41025641025641, "by_split": {"test": 47.17583487295627}}, {"key": "jaccard", "bare_value": 0.6948700682016542, "by_split": {"test": 0.4394688769656825}}, {"key": "macro_f1", "bare_value": 0.7478153737859431, "by_split": {"test": 0.5521899923682838}}, {"key": "seg_f1_10", "bare_value": 0.415499533146592, "by_split": {"test": 0.5286462353970459}}, {"key": "seg_f1_25", "bare_value": 0.415499533146592, "by_split": {"test": 0.5147573465081571}}, {"key": "seg_f1_50", "bare_value": 0.3485060690943044, "by_split": {"test": 0.3726991233938895}}]`
- `experiments/phase1/s4_phase_baseline_052_frozen_tecno_phase_baseline_seed123`: `[{"key": "accuracy", "bare_value": 0.9042904290429042, "by_split": {"test": 0.7660023446658851}}, {"key": "edit_score", "bare_value": 43.77777777777777, "by_split": {"test": 39.43003955968352}}, {"key": "jaccard", "bare_value": 0.6648188924984354, "by_split": {"test": 0.3704756803042274}}, {"key": "macro_f1", "bare_value": 0.7184213787124055, "by_split": {"test": 0.48190035768354067}}, {"key": "seg_f1_10", "bare_value": 0.5035521454958795, "by_split": {"test": 0.44449528318552806}}, {"key": "seg_f1_25", "bare_value": 0.5035521454958795, "by_split": {"test": 0.41298645216251123}}, {"key": "seg_f1_50", "bare_value": 0.4549587951122478, "by_split": {"test": 0.27017866186152234}}]`
- `experiments/phase1/s4_phase_baseline_053_frozen_tecno_phase_baseline_seed123`: `[{"key": "accuracy", "bare_value": 0.900990099009901, "by_split": {"test": 0.7901524032825322}}, {"key": "edit_score", "bare_value": 48.06060606060606, "by_split": {"test": 46.86278407208639}}, {"key": "jaccard", "bare_value": 0.6459664915676043, "by_split": {"test": 0.4072919531427772}}, {"key": "macro_f1", "bare_value": 0.7134424041822957, "by_split": {"test": 0.520053988407163}}, {"key": "seg_f1_10", "bare_value": 0.5369075369075369, "by_split": {"test": 0.5271123834149044}}, {"key": "seg_f1_25", "bare_value": 0.5217560217560218, "by_split": {"test": 0.49852248591744397}}, {"key": "seg_f1_50", "bare_value": 0.45066045066045063, "by_split": {"test": 0.3573208770687762}}]`
- `experiments/phase1/s4_phase_baseline_054_frozen_tecno_phase_baseline_seed456`: `[{"key": "accuracy", "bare_value": 0.8937293729372937, "by_split": {"test": 0.7317702227432591}}, {"key": "edit_score", "bare_value": 43.5, "by_split": {"test": 42.50695508999035}}, {"key": "jaccard", "bare_value": 0.6504359680214252, "by_split": {"test": 0.3848723573723641}}, {"key": "macro_f1", "bare_value": 0.7087253966163348, "by_split": {"test": 0.4977367486961391}}, {"key": "seg_f1_10", "bare_value": 0.5096296296296297, "by_split": {"test": 0.4640842933525861}}, {"key": "seg_f1_25", "bare_value": 0.46444444444444444, "by_split": {"test": 0.45551474819767507}}, {"key": "seg_f1_50", "bare_value": 0.43777777777777777, "by_split": {"test": 0.3060604158165134}}]`
- `experiments/phase1/s4_phase_baseline_055_frozen_tecno_phase_baseline_seed456`: `[{"key": "accuracy", "bare_value": 0.9036303630363036, "by_split": {"test": 0.8105509964830012}}, {"key": "edit_score", "bare_value": 38.61988304093567, "by_split": {"test": 45.27615283267457}}, {"key": "jaccard", "bare_value": 0.6664483442570189, "by_split": {"test": 0.43865906361352214}}, {"key": "macro_f1", "bare_value": 0.7307028022659036, "by_split": {"test": 0.5454772729991842}}, {"key": "seg_f1_10", "bare_value": 0.4240981240981241, "by_split": {"test": 0.5246086230067923}}, {"key": "seg_f1_25", "bare_value": 0.4240981240981241, "by_split": {"test": 0.5103171576283705}}, {"key": "seg_f1_50", "bare_value": 0.39307359307359313, "by_split": {"test": 0.3683181383410217}}]`
- `experiments/phase1/s4_phase_baseline_056_frozen_tecno_phase_baseline_seed42`: `[{"key": "accuracy", "bare_value": 0.8983498349834983, "by_split": {"test": 0.7289566236811255}}, {"key": "edit_score", "bare_value": 36.060606060606055, "by_split": {"test": 48.455819426615314}}, {"key": "jaccard", "bare_value": 0.6320600948777605, "by_split": {"test": 0.3324124472763859}}, {"key": "macro_f1", "bare_value": 0.6693452134103115, "by_split": {"test": 0.429824974761169}}, {"key": "seg_f1_10", "bare_value": 0.5002249212775528, "by_split": {"test": 0.5285040001457911}}, {"key": "seg_f1_25", "bare_value": 0.48268106162843, "by_split": {"test": 0.4901044229402438}}, {"key": "seg_f1_50", "bare_value": 0.3868645973909131, "by_split": {"test": 0.34386127968217517}}]`
- `experiments/phase1/s4_phase_baseline_057_frozen_tecno_phase_baseline_seed42`: `[{"key": "accuracy", "bare_value": 0.9254125412541254, "by_split": {"test": 0.7971864009378663}}, {"key": "edit_score", "bare_value": 49.0, "by_split": {"test": 46.19690602727311}}, {"key": "jaccard", "bare_value": 0.7226118416313183, "by_split": {"test": 0.4348582181317794}}, {"key": "macro_f1", "bare_value": 0.7716705349405126, "by_split": {"test": 0.5475319104850003}}, {"key": "seg_f1_10", "bare_value": 0.6074074074074075, "by_split": {"test": 0.5361730387267368}}, {"key": "seg_f1_25", "bare_value": 0.6074074074074075, "by_split": {"test": 0.5191205321161924}}, {"key": "seg_f1_50", "bare_value": 0.5444444444444444, "by_split": {"test": 0.3723594813224918}}]`
- `experiments/phase1/s4_phase_baseline_058_frozen_tecno_phase_baseline_seed123`: `[{"key": "accuracy", "bare_value": 0.8739273927392739, "by_split": {"test": 0.738569753810082}}, {"key": "edit_score", "bare_value": 47.03703703703704, "by_split": {"test": 48.20261437908497}}, {"key": "jaccard", "bare_value": 0.6170343892105222, "by_split": {"test": 0.3622958427596263}}, {"key": "macro_f1", "bare_value": 0.6935602920898358, "by_split": {"test": 0.4759455928434414}}, {"key": "seg_f1_10", "bare_value": 0.5300236406619385, "by_split": {"test": 0.5203768104801733}}, {"key": "seg_f1_25", "bare_value": 0.5133569739952719, "by_split": {"test": 0.48487059098718}}, {"key": "seg_f1_50", "bare_value": 0.4708037825059102, "by_split": {"test": 0.3195681255478398}}]`
- `experiments/phase1/s4_phase_baseline_059_frozen_tecno_phase_baseline_seed123`: `[{"key": "accuracy", "bare_value": 0.9095709570957096, "by_split": {"test": 0.7266119577960141}}, {"key": "edit_score", "bare_value": 43.055555555555564, "by_split": {"test": 54.906162176478375}}, {"key": "jaccard", "bare_value": 0.6786756230381387, "by_split": {"test": 0.3742670760006537}}, {"key": "macro_f1", "bare_value": 0.7335901047786282, "by_split": {"test": 0.48915343306811154}}, {"key": "seg_f1_10", "bare_value": 0.5142450142450142, "by_split": {"test": 0.5851020408163264}}, {"key": "seg_f1_25", "bare_value": 0.5142450142450142, "by_split": {"test": 0.5620408163265306}}, {"key": "seg_f1_50", "bare_value": 0.4829059829059828, "by_split": {"test": 0.41954648526077093}}]`
- `experiments/phase1/s4_phase_baseline_060_frozen_tecno_phase_baseline_seed456`: `[{"key": "accuracy", "bare_value": 0.8917491749174917, "by_split": {"test": 0.7528722157092614}}, {"key": "edit_score", "bare_value": 43.5, "by_split": {"test": 46.775850039396836}}, {"key": "jaccard", "bare_value": 0.6605047609477738, "by_split": {"test": 0.38760852925223077}}, {"key": "macro_f1", "bare_value": 0.7229598486716059, "by_split": {"test": 0.4996362999225271}}, {"key": "seg_f1_10", "bare_value": 0.4962962962962963, "by_split": {"test": 0.5382823537599609}}, {"key": "seg_f1_25", "bare_value": 0.4962962962962963, "by_split": {"test": 0.5176566795420537}}, {"key": "seg_f1_50", "bare_value": 0.43777777777777777, "by_split": {"test": 0.36989838883669135}}]`
- `experiments/phase1/s4_phase_baseline_061_frozen_tecno_phase_baseline_seed456`: `[{"key": "accuracy", "bare_value": 0.9135313531353135, "by_split": {"test": 0.7992966002344666}}, {"key": "edit_score", "bare_value": 47.333333333333336, "by_split": {"test": 38.57396640826874}}, {"key": "jaccard", "bare_value": 0.6927705149358749, "by_split": {"test": 0.42969905123227403}}, {"key": "macro_f1", "bare_value": 0.7451167588231498, "by_split": {"test": 0.5375889313115498}}, {"key": "seg_f1_10", "bare_value": 0.5652173913043478, "by_split": {"test": 0.4884330925352596}}, {"key": "seg_f1_25", "bare_value": 0.5507246376811594, "by_split": {"test": 0.4698572411420709}}, {"key": "seg_f1_50", "bare_value": 0.4794685990338164, "by_split": {"test": 0.31443068455452355}}]`
- `experiments/transfer/t1a_appearance_001_t1a_appearance_seed42`: `[{"key": "accuracy", "bare_value": 0.9504950495049505, "by_split": {"test": 0.8152403282532239}}, {"key": "edit_score", "bare_value": 34.166666666666664, "by_split": {"test": 36.71888893991112}}, {"key": "jaccard", "bare_value": 0.7813188712598264, "by_split": {"test": 0.5329958444021909}}, {"key": "macro_f1", "bare_value": 0.8162734056221386, "by_split": {"test": 0.6307380341321444}}, {"key": "seg_f1_10", "bare_value": 0.4422466422466423, "by_split": {"test": 0.4364032056466436}}, {"key": "seg_f1_25", "bare_value": 0.4217338217338218, "by_split": {"test": 0.42005163019059055}}, {"key": "seg_f1_50", "bare_value": 0.4217338217338218, "by_split": {"test": 0.2857002344598845}}]`
- `experiments/transfer/t1a_appearance_002_t1a_appearance_seed123`: `[{"key": "accuracy", "bare_value": 0.9465346534653465, "by_split": {"test": 0.822274325908558}}, {"key": "edit_score", "bare_value": 35.58201058201058, "by_split": {"test": 38.92806878655936}}, {"key": "jaccard", "bare_value": 0.7545956697859814, "by_split": {"test": 0.5495297093699452}}, {"key": "macro_f1", "bare_value": 0.7969645008052287, "by_split": {"test": 0.6269775859327538}}, {"key": "seg_f1_10", "bare_value": 0.45122870496004824, "by_split": {"test": 0.4679942802614981}}, {"key": "seg_f1_25", "bare_value": 0.45122870496004824, "by_split": {"test": 0.46041086266796927}}, {"key": "seg_f1_50", "bare_value": 0.4213779586913915, "by_split": {"test": 0.3334460357888958}}]`
- `experiments/transfer/t1a_appearance_003_t1a_appearance_seed456`: `[{"key": "accuracy", "bare_value": 0.9504950495049505, "by_split": {"test": 0.8091441969519344}}, {"key": "edit_score", "bare_value": 59.37500000000001, "by_split": {"test": 45.87958717933045}}, {"key": "jaccard", "bare_value": 0.7754857216065117, "by_split": {"test": 0.5203276867077553}}, {"key": "macro_f1", "bare_value": 0.8125506379442964, "by_split": {"test": 0.6042656475610072}}, {"key": "seg_f1_10", "bare_value": 0.6573099415204678, "by_split": {"test": 0.5449042181261506}}, {"key": "seg_f1_25", "bare_value": 0.6573099415204678, "by_split": {"test": 0.5314518297854735}}, {"key": "seg_f1_50", "bare_value": 0.6456140350877194, "by_split": {"test": 0.3972677341277229}}]`
- `experiments/transfer/t1a_base_test_001_t1a_base_test_seed42`: `[{"key": "accuracy", "bare_value": 0.9471947194719472, "by_split": {"test": 0.8173505275498242}}, {"key": "edit_score", "bare_value": 34.51219512195122, "by_split": {"test": 53.23652935000309}}, {"key": "jaccard", "bare_value": 0.7611425277318641, "by_split": {"test": 0.5690620284081881}}, {"key": "macro_f1", "bare_value": 0.80276861640554, "by_split": {"test": 0.6700748330236684}}, {"key": "seg_f1_10", "bare_value": 0.4507936507936509, "by_split": {"test": 0.602266268826371}}, {"key": "seg_f1_25", "bare_value": 0.4406926406926408, "by_split": {"test": 0.5849625840674434}}, {"key": "seg_f1_50", "bare_value": 0.43059163059163064, "by_split": {"test": 0.45644714407502135}}]`
- `experiments/transfer/t1a_base_test_002_t1a_base_test_seed123`: `[{"key": "accuracy", "bare_value": 0.9485148514851485, "by_split": {"test": 0.8302461899179366}}, {"key": "edit_score", "bare_value": 31.80457052797478, "by_split": {"test": 50.18577313934339}}, {"key": "jaccard", "bare_value": 0.7671249201454028, "by_split": {"test": 0.600514260719424}}, {"key": "macro_f1", "bare_value": 0.8066393348436439, "by_split": {"test": 0.6932970793785072}}, {"key": "seg_f1_10", "bare_value": 0.4294131794131794, "by_split": {"test": 0.5557877670026393}}, {"key": "seg_f1_25", "bare_value": 0.42015392015392017, "by_split": {"test": 0.546365354679116}}, {"key": "seg_f1_50", "bare_value": 0.39237614237614243, "by_split": {"test": 0.5208924572071675}}]`
- `experiments/transfer/t1a_base_test_003_t1a_base_test_seed456`: `[{"key": "accuracy", "bare_value": 0.9471947194719472, "by_split": {"test": 0.8382180539273154}}, {"key": "edit_score", "bare_value": 40.63492063492063, "by_split": {"test": 53.52448703058459}}, {"key": "jaccard", "bare_value": 0.7529534250683285, "by_split": {"test": 0.6118934786380359}}, {"key": "macro_f1", "bare_value": 0.7963241850462713, "by_split": {"test": 0.6972613012080395}}, {"key": "seg_f1_10", "bare_value": 0.5071225071225071, "by_split": {"test": 0.6041861758736332}}, {"key": "seg_f1_25", "bare_value": 0.4968660968660969, "by_split": {"test": 0.5942342392041392}}, {"key": "seg_f1_50", "bare_value": 0.47635327635327646, "by_split": {"test": 0.4659897345368704}}]`
- `experiments/transfer/t1a_regiontraj_test_001_t1a_regiontraj_test_seed42`: `[{"key": "accuracy", "bare_value": 0.9511551155115512, "by_split": {"test": 0.8600234466588511}}, {"key": "edit_score", "bare_value": 41.449275362318836, "by_split": {"test": 45.54551332669573}}, {"key": "jaccard", "bare_value": 0.7827713529196976, "by_split": {"test": 0.5655965566740991}}, {"key": "macro_f1", "bare_value": 0.8165861788493901, "by_split": {"test": 0.6358997765060056}}, {"key": "seg_f1_10", "bare_value": 0.5586854460093896, "by_split": {"test": 0.5518406007267392}}, {"key": "seg_f1_25", "bare_value": 0.5492957746478874, "by_split": {"test": 0.5499466613327999}}, {"key": "seg_f1_50", "bare_value": 0.5027386541471048, "by_split": {"test": 0.4003046137947128}}, {"key": "sticky_accuracy", "bare_value": 0.928052805280528, "by_split": {"test": 0.7395076201641266}}, {"key": "sticky_edit_score", "bare_value": 54.19047619047618, "by_split": {"test": 54.6362894502116}}, {"key": "sticky_jaccard", "bare_value": 0.7320788809612998, "by_split": {"test": 0.4069962731219658}}, {"key": "sticky_macro_f1", "bare_value": 0.7812961310103008, "by_split": {"test": 0.5142457076274282}}, {"key": "sticky_seg_f1_10", "bare_value": 0.6503703703703704, "by_split": {"test": 0.6110046828437633}}, {"key": "sticky_seg_f1_25", "bare_value": 0.6503703703703704, "by_split": {"test": 0.6110046828437633}}, {"key": "sticky_seg_f1_50", "bare_value": 0.5866666666666666, "by_split": {"test": 0.4605683269476372}}]`
- `experiments/transfer/t1a_regiontraj_test_002_t1a_regiontraj_test_seed123`: `[{"key": "accuracy", "bare_value": 0.9491749174917492, "by_split": {"test": 0.8295427901524033}}, {"key": "edit_score", "bare_value": 32.36111111111111, "by_split": {"test": 52.381027187801095}}, {"key": "jaccard", "bare_value": 0.7702997958299107, "by_split": {"test": 0.48198069096990376}}, {"key": "macro_f1", "bare_value": 0.8083721689809815, "by_split": {"test": 0.5705131725695836}}, {"key": "seg_f1_10", "bare_value": 0.4477495107632094, "by_split": {"test": 0.5905192336342778}}, {"key": "seg_f1_25", "bare_value": 0.4386170906718853, "by_split": {"test": 0.5844855636006079}}, {"key": "seg_f1_50", "bare_value": 0.3961513372472277, "by_split": {"test": 0.44776484610112927}}, {"key": "sticky_accuracy", "bare_value": 0.9485148514851485, "by_split": {"test": 0.8096131301289566}}, {"key": "sticky_edit_score", "bare_value": 45.370370370370374, "by_split": {"test": 59.66200466200467}}, {"key": "sticky_jaccard", "bare_value": 0.7707461842287983, "by_split": {"test": 0.4583712132986175}}, {"key": "sticky_macro_f1", "bare_value": 0.8081364735701284, "by_split": {"test": 0.5534502794354794}}, {"key": "sticky_seg_f1_10", "bare_value": 0.5622950819672131, "by_split": {"test": 0.6536052961173734}}, {"key": "sticky_seg_f1_25", "bare_value": 0.5513661202185792, "by_split": {"test": 0.6405439255680802}}, {"key": "sticky_seg_f1_50", "bare_value": 0.49877049180327865, "by_split": {"test": 0.4953480050098407}}]`
- `experiments/transfer/t1a_regiontraj_test_003_t1a_regiontraj_test_seed456`: `[{"key": "accuracy", "bare_value": 0.9425742574257425, "by_split": {"test": 0.8011723329425556}}, {"key": "edit_score", "bare_value": 43.91534391534392, "by_split": {"test": 52.706669111394376}}, {"key": "jaccard", "bare_value": 0.7543336032980965, "by_split": {"test": 0.5033580350884154}}, {"key": "macro_f1", "bare_value": 0.7994252532653761, "by_split": {"test": 0.5916665718334579}}, {"key": "seg_f1_10", "bare_value": 0.5523895673149405, "by_split": {"test": 0.5888564415100728}}, {"key": "seg_f1_25", "bare_value": 0.5424393185587215, "by_split": {"test": 0.576893234016139}}, {"key": "seg_f1_50", "bare_value": 0.5021860394994723, "by_split": {"test": 0.4481053552282603}}, {"key": "sticky_accuracy", "bare_value": 0.932013201320132, "by_split": {"test": 0.8091441969519344}}, {"key": "sticky_edit_score", "bare_value": 52.22222222222223, "by_split": {"test": 62.743657308874695}}, {"key": "sticky_jaccard", "bare_value": 0.7179455498622082, "by_split": {"test": 0.5035662359292181}}, {"key": "sticky_macro_f1", "bare_value": 0.7697527677989501, "by_split": {"test": 0.5911093862873065}}, {"key": "sticky_seg_f1_10", "bare_value": 0.6191919191919192, "by_split": {"test": 0.6585406099276868}}, {"key": "sticky_seg_f1_25", "bare_value": 0.6070707070707071, "by_split": {"test": 0.6452749695739364}}, {"key": "sticky_seg_f1_50", "bare_value": 0.5411616161616162, "by_split": {"test": 0.500209111719324}}]`

## 9. 標準規約 (1 run 1 dir) に従わない群

`metrics.json` を持たないため run として収穫していない。
**取りこぼした run 数は 0**（これらの配下に `metrics.json` は 1 つも無い）。
個別 adapter は次段階に回す。

| group | ファイル数 | 備考 |
|---|---:|---|
| `ablations` | 1 | 未着手 scaffold (.gitkeep のみ) |
| `analysis` | 86 | 非 run の成果物。次段階で adapter が必要 |
| `audit` | 3 | 非 run の成果物。次段階で adapter が必要 |
| `detector_improve` | 5 | 非 run の成果物。次段階で adapter が必要 |
| `final` | 1 | 未着手 scaffold (.gitkeep のみ) |
| `g2_main_2026-07-29` | 5 | 非 run の成果物。次段階で adapter が必要 |

## 10. 警告が出た run の内訳

| 警告 | 件数 |
|---|---:|
| ディレクトリ名に補助 seed {...} が含まれる。seed には末尾の seed<N> のみを採用した。 | 101 |
| host '...' は実サーバーを一意に特定できない。host は null にした。 | 10 |
| per_class_ap.json が空 ({...}) | 8 |
| run 名が命名規約 <step>_<seq3>_<desc>_seed<N> に一致しない | 6 |
| metrics.json が空 ({...}) | 6 |
| per_class_ap.json が存在しない | 3 |

