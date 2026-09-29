# audit — T-2026-09-19-stage1-detector-towers-r2

SPEC §3 が求める作業の記録。**測っていないことは測っていないと書く。**

## Task A — 事前登録と開始状態

### A-1 prereg の commit

| 項目 | 値 |
|---|---|
| commit | `d2f8ca2e5673864c89e9f2bf24c43ff4c1dec980` |
| committed_at | 2026-09-22T16:15:30+00:00 |
| 検査 | L3 の P4 prereg_committed が PASS |

commit の前に prereg §3 の対称性の表の列名を直した。起票時は
`条件 / D\*-COCO / D\*-ImageNet / 判定 / 理由` で、`conventions#symmetry` が
「列名はこのとおりにする（L3 の P13 が列名で表を探す）」と定める
`条件 / 腕1 / 腕2 / 判定 / 理由` と違っていたため、P13 が表を見つけられず FAIL していた
（`tools/preflight_task.py:78` の `^腕\d+$` に一致せず腕 0 列）。
**15 行の判定と理由は変えていない。** 腕の対応は表の直下に 1 行で置いた。
利用者の決定 2026-09-22。`meta.amendments` に記録済み。

### A-2 開始状態

| 項目 | 実測 |
|---|---|
| ホスト | efros（契約 `resources.server` と一致） |
| 装置 | NVIDIA RTX A6000 × 2、各 49140 MiB |
| 分岐 | `feat/stage1-detector-towers-r2`（起点 `origin/phase0` = 66855c5b） |
| 作業ツリー | 開始時に未追跡 3 件を stash へ退避（利用者の指示）。以降は清浄 |
| 他利用者の処理 | 0 件。開始時の占有は自分の GPU 保持プロセス 2 件（pid 366101/366102、各 40338 MiB）のみで、実験の直前に停止した |
| 同期の抑止 | `.sync-pause` を `make task-start` が設置。稼働中の `~/bin/m2-sync.sh` は対応済み（`grep -c sync-pause` = 2） |

装置の同定は `/proc/<pid>/cmdline` と `/proc/<pid>/environ` の完全一致で行った
（部分一致は使っていない。`conventions#issuer_cautions` 6）。停止した 2 件は
`CUDA_VISIBLE_DEVICES` が 0 と 1 の行列積の空回しで、起動の原文は退避してある。

### A-3 一周目の引き継ぎ

一周目の成果物 `experiments/baselines/stage1_dtower/` は本分岐に在る（PR #191、2026-09-21 統合）。
**14 run すべての TensorBoard `val/mAP` を float32 の原値で読めた。**
写しを `experiments/baselines/stage1_dtower_r2/round1_curves.json` に置いた（並置の材料）。

| run | 最良 val mAP | 最良 epoch（0 起点） | epoch 数 |
|---|---|---|---|
| dcoco_foldA_seed42 | 0.724414 | 11 | 12 |
| dcoco_foldA_seed123 | 0.724666 | 10 | 12 |
| dcoco_foldA_seed456 | 0.720883 | 11 | 12 |
| dcoco_foldB_seed42 | 0.476938 | 11 | 12 |
| dcoco_foldC_seed42 | 0.438561 | 10 | 12 |
| dcoco_foldD_seed42 | 0.496268 | 10 | 12 |
| dcoco_foldE_seed42 | 0.526389 | 6 | 12 |
| dimagenet_foldA_seed42 | 0.683405 | 11 | 12 |
| dimagenet_foldA_seed123 | 0.677809 | 10 | 12 |
| dimagenet_foldA_seed456 | 0.669449 | 10 | 12 |
| dimagenet_foldB_seed42 | 0.408203 | 10 | 12 |
| dimagenet_foldC_seed42 | 0.408841 | 10 | 12 |
| dimagenet_foldD_seed42 | 0.481146 | 11 | 12 |
| dimagenet_foldE_seed42 | 0.453982 | 10 | 12 |

SPEC §2 の表は最良 epoch を 1 起点で書いている（dcoco_foldA_seed42 が 12）。
上の表は 0 起点で、同じ epoch を指す。**値そのものは一致する。**

### A-4 学習率の低下と打ち切りの実装

規則は `third_party/Relation-DETR/util/convergence.py` の `PlateauSchedule` 1 本。
学習ループからの呼び出しは `third_party/Relation-DETR/main.py` の次の行だけである。

| 行 | 内容 |
|---|---|
| `main.py:211-215` | 規則を立てる**唯一の箇所**。`--convergence-schedule` のときだけ立つ |
| `main.py:216` | `--max-epochs` が epoch 数の上限を上書きする（既定は config の 12） |
| `main.py:229-230` | 規則が無いとき **だけ** config の `MultiStepLR` を進める |
| `main.py:241-242` | 規則が無ければここで次の epoch へ。以降は一周目と同じ経路 |
| `main.py:246-249` | 主過程の val mAP を配ってから判定する（DDP で片方だけ抜けないため） |
| `main.py:249` | 規則を呼ぶ**唯一の箇所** |
| `main.py:250-252` | 低下。全 param_group の lr に `--plateau-factor` を掛ける |
| `main.py:263-264` | 打ち切り |

**塔を見る分岐がこの経路に無い。** 塔の違いは config ファイル（COCO 重みを読むか否か）
だけで、学習の長さを決める経路は共有される。試験が構文木で
「`PlateauSchedule(` の生成 1 箇所・`observe(` の呼び出し 1 箇所」を確かめる。

写しは `experiments/baselines/stage1_dtower_r2/impl/` に置いた（`convergence.py.txt`。`experiments/**/*.py` も `.gitignore:39` で落ちるため拡張子を変えてある）
（`third_party/` は `.gitignore:133` により追跡外のため、PR には現れない）。

試験 `tests/test_stage1_dtower_convergence.py`（9 件すべて PASS）:

| 試験 | 何を示すか |
|---|---|
| `test_decays_once_then_stops` | 停滞 4 で低下（epoch 8）、その後の停滞 4 で打ち切り（epoch 12） |
| `test_patience_changes_the_timing_of_the_decay` | **陽性対照。** 同じ並びで patience を 2 にすると低下が epoch 6 へ動く |
| `test_improvement_resets_the_counter` | 上がり続ける並びでは低下も打ち切りも起きない |
| `test_the_decay_happens_only_once` | 低下は一度だけ。二度目の停滞は打ち切り |
| `test_the_best_is_not_rolled_back_by_the_decay` | 最良はさかのぼらない |
| `test_the_default_is_the_first_round` | **既定で一周目が再現する**（引数の既定値を構文木で読む） |
| `test_the_first_round_scheduler_still_steps_when_disabled` | 既定の経路で `lr_scheduler.step()` が毎 epoch 呼ばれる |
| `test_both_towers_take_the_same_path` | 生成 1 箇所・呼び出し 1 箇所 |
| `test_patience_must_be_positive` | patience 0 を拒む |

### A-5 折りの照合

`scripts/verify_stage1_dtower_r2_folds.py`。画像の `file_name` から動画 ID に戻し、
`conventions#folds` の表と比べた。結果は
`experiments/baselines/stage1_dtower_r2/fold_verification.json`。

**15 行（5 折り × train/val/test）すべて対称差 0。** train は各折り 10 本、val 2 本、test 3 本。

陰性対照: 折り A の test を `07` から `11` へ一本入れ替えた集合と照合すると
**対称差 2**（`['07', '11']`）。差 0 を出す照合が差を出せることを示した。

### A-6 占位の差し替え

| 項目 | 実測値 | 出所 |
|---|---|---|
| `contract.conventions_rev` | `c801e17c3231fe1f2b7c8072e1a960e6dbab8ca5` | `context/conventions.md` を最後に変えた commit |
| `meta.created_from.runindex_commit` | `4e97b3deae28e653948c19309d229c755587c42b` | `runindex/` を最後に変えた commit |
| `meta.created_from.counts` | 0 のまま | **起票時（2026-09-19）の値が記録されていない。** 推測で埋めない |

実行開始時点の実測は index 1558 / experiments 476 / verdicts 1506。
L2-8 はこの差を「分母が動いています」と WARN する。**起票時の値が占位だったことが原因で、
分母が実際に動いた証拠ではない。** 利用者の続行判断 2026-09-22。

### 関門 G1

| 要件 | 実測 | 判定 |
|---|---|---|
| 一周目の曲線が引き継がれる | 14/14 run の `val/mAP` を原値で読めた | PASS |
| 低下と打ち切りが両塔で同一であることを実装の行で示す | `main.py:211-215`・`249`（各 1 箇所）。試験が構文木で確認 | PASS |

**G1 PASS。**

## Task B — ImageNet 初期化の一本目

| 項目 | 値 |
|---|---|
| run | `dimagenet_foldA_seed42` |
| 起動 | 2026-09-22 16:23 UTC |
| 引数 | `--convergence-schedule --max-epochs 36`（patience 4・factor 0.1 は既定） |
| 装置 | A6000 × 2（単独実行）、待受ポート 29701 |
| 初期の速さ | 0.573 s/iter・2405 iter/epoch ≒ 23 分/epoch（学習のみ。評価を含まない） |
| 終了 | 2026-09-23 04:45:47 UTC。**打ち切りで停止**（上限には達していない） |
| 壁時計 | 12:22:13（`Training time` の記録は 12:22:05） |
| GPU 時間 | 24.74 GPU 時間（2 枚 × 12.37 時間） |
| 1 epoch あたり | 0.4266 時間（評価を含む。単独実行） |

### B-1 規則が働いたか

| 項目 | 実測 |
|---|---|
| 学習率の低下 | **epoch 15**（epoch 11 の最良 0.6756 から 12・13・14・15 と 4 epoch 更新なし） |
| 低下の効果 | epoch 15 の 0.6625 から epoch 16 で 0.6821（**+1.96 mAP**） |
| 打ち切り | **epoch 28**（epoch 24 の最良から 25・26・27・28 と 4 epoch 更新なし） |
| 最良 epoch | **24**。上限 36 には達していない |
| 観測した epoch 数 | 29 |

**低下も打ち切りも設計どおりに働いた。** 低下の直後に伸びているので、
停滞の検出が早すぎたわけでもない。

### B-2 一周目との差

| | 一周目 | 二周目 |
|---|---|---|
| 最良 val mAP | 0.683405 | **0.686300** |
| 最良 epoch | 11（12 epoch で終了） | 24（29 epoch で打ち切り） |
| epoch 数 | 12 | 29 |

**上がり幅は +0.002895（0.29 mAP）である。** 一周目の最終 epoch が +0.0067 伸びて
いたことから期待された幅より小さい。epoch 12〜15 は一周目の 11 の値（0.6834）を
下回って推移し、学習率を下げてはじめて超えた（epoch 16 で 0.6821、epoch 18 で 0.6837）。
**12 epoch 版は見かけより収束に近かった。** prereg §4 の予測 1 は当たり（上がった）だが、
幅は小さい。予測 2（両塔の差が縮む）の判定には D\*-COCO の二周目が要る。

epoch ごとの val mAP は `work/convergence.json`（float の原値）にある。

### B-4 残り 13 run の見込み

単独実行の実測 0.4266 h/epoch に、一周目が測った 2 本同時の倍率
（1 本 0.554 s/step → 2 本 0.92 s/step、1.66 倍）を当てる。

| 条件 | 1 run あたり | 13 run の壁時計（2 本同時） |
|---|---|---|
| 29 epoch（本 run と同じ） | 20.5 時間 | 約 116 時間（4.8 日） |
| 36 epoch（上限に張り付く最悪） | 25.5 時間 | 約 166 時間（6.9 日） |

**上限に達した場合の 25.5 時間は停止条件の 27 時間を下回る**が、余裕は 6% しかない。
契約の見積（`resources.est_hours` 145）の範囲内である。

### 関門 G2

| 要件 | 実測 | 判定 |
|---|---|---|
| ImageNet 初期化の一本で学習率の低下が起きた | epoch 15 | PASS |
| 打ち切りか上限で止まった | 打ち切り epoch 28 | PASS |
| 最良 epoch が上限なら報告して諮る | 最良 epoch 24。上限 36 に達していないため諮る条件に当たらない | 該当なし |

**G2 PASS。** Task C へ進んだ。

## Task C — 残り 13 run

2026-09-23 05:27 UTC に待ち行列 a（7 run）と b（6 run）を起動。**常に 2 本同時。**
待受ポートは 29711〜29723 で、一周目（29531〜29641）と Task B（29701）と重ならない。

待ち行列 a は 2026-09-26 23:14:14 UTC、b は 2026-09-27 03:24:37 UTC に終了。**13 run すべて rc=0。**

### C-1〜C-3 実測（学習の記録 `work/convergence.json` から。Task B を含む 14 run）

| run | 一周目 最良 | 二周目 最良 | 上がり幅 | 低下 | 打ち切り | 最良 epoch | epoch 数 | 壁時計 h | h/epoch |
|---|---|---|---|---|---|---|---|---|---|
| dcoco_foldA_seed42 | 0.7244 | 0.7275 | +0.0031 | 9 | 14 | 10 | 15 | 9.97 | 0.665 |
| dcoco_foldA_seed123 | 0.7247 | 0.7290 | +0.0043 | 9 | 17 | 13 | 18 | 11.96 | 0.665 |
| dcoco_foldA_seed456 | 0.7209 | 0.7193 | −0.0016 | 11 | 16 | 12 | 17 | 11.21 | 0.660 |
| dcoco_foldB_seed42 | 0.4769 | 0.4555 | **−0.0215** | 11 | 20 | 16 | 21 | 14.11 | 0.672 |
| dcoco_foldC_seed42 | 0.4386 | 0.4339 | −0.0046 | 9 | 14 | 10 | 15 | 11.16 | 0.744 |
| dcoco_foldD_seed42 | 0.4963 | 0.5115 | +0.0152 | 7 | 16 | 12 | 17 | 12.38 | 0.728 |
| dcoco_foldE_seed42 | 0.5264 | 0.5309 | +0.0045 | 10 | 16 | 12 | 17 | 13.14 | 0.773 |
| dimagenet_foldA_seed42 | 0.6834 | 0.6863 | +0.0029 | 15 | 28 | 24 | 29 | 12.37（単独） | 0.427 |
| dimagenet_foldA_seed123 | 0.6778 | 0.6753 | −0.0025 | 22 | 30 | 26 | 31 | 20.52 | 0.662 |
| dimagenet_foldA_seed456 | 0.6694 | 0.6758 | +0.0063 | 14 | 19 | 15 | 20 | 13.22 | 0.661 |
| dimagenet_foldB_seed42 | 0.4082 | 0.4084 | +0.0002 | 21 | 28 | 24 | 29 | 19.64 | 0.677 |
| dimagenet_foldC_seed42 | 0.4088 | 0.4068 | −0.0021 | 13 | 20 | 16 | 21 | 15.75 | 0.750 |
| dimagenet_foldD_seed42 | 0.4811 | 0.4729 | −0.0082 | 16 | 26 | 22 | 27 | 17.53 | 0.649 |
| dimagenet_foldE_seed42 | 0.4540 | 0.4642 | +0.0102 | 10 | 16 | 12 | 17 | 13.15 | 0.773 |

epoch は 0 起点。一周目の値は `round1_curves.json`（TensorBoard の原値）から。
壁時計は `start.txt` と `end.txt` の差で、Task B だけ単独実行、他 13 run は 2 本同時。
機械可読の写しは `summary_14runs.json`。

### 停止条件と規則の働き

| 条件 | 実測 |
|---|---|
| 上限 36 に達した run | **0 件**（最長 31 epoch） |
| 学習率の低下を受けずに上限へ達した run | **0 件**（全 14 run で低下が起きた） |
| 27 時間を超えた run | **0 件**（最長 20.52 時間、dimagenet_foldA_seed123） |
| 発散・非数 | **0 件** |

低下 epoch は D\*-COCO が 7〜11、D\*-ImageNet が 10〜22。打ち切りは D\*-COCO が 14〜20、
D\*-ImageNet が 16〜30。**同じ規則を通して塔ごとに違う時期に止まった**（prereg §2 の設計どおり）。

### 上がり幅と塔間の差（学習の記録の val mAP。評価 recipe による値は D で確定する）

| | D\*-COCO（7 run） | D\*-ImageNet（7 run） |
|---|---|---|
| 上がり幅の平均 | **−0.0001** | **+0.0010** |
| 範囲 | −0.0215〜+0.0152 | −0.0082〜+0.0102 |

| 塔間の差（COCO − ImageNet） | 一周目 | 二周目 |
|---|---|---|
| 折り A（3 seed の平均） | 0.7233 − 0.6769 = **4.64 mAP** | 0.7253 − 0.6791 = **4.61 mAP** |
| 5 折り seed 42 の平均 | **4.54 mAP**（A 4.10 / B 6.87 / C 2.97 / D 1.51 / E 7.24） | **4.41 mAP**（A 4.12 / B 4.71 / C 2.72 / D 3.86 / E 6.67） |

**収束まで学習しても塔間の差は縮まなかった。** 一周目の差は学習不足では説明されていない。

### 計時

| 条件 | 値 |
|---|---|
| 2 本同時の 13 run の壁時計 | 平均 **14.13 時間**、範囲 9.97〜20.52、合計 183.7 run 時間 |
| 単独の Task B | 12.37 時間（29 epoch、0.427 h/epoch） |
| 2 本同時の 1 epoch | 0.649〜0.773 時間（折りにより train の枚数が違う） |
| 14 run の GPU 時間 | (183.7 + 12.37) × 2 枚 = **392.1 GPU 時間** |
| Task C の経過 | 2026-09-23 05:27 → 09-27 03:24 UTC = 94.0 時間（13 run × 14.13 / 2 本 = 91.9 と整合） |

Task B（05:07〜09-23 04:45）を含む学習全体の経過は 2026-09-22 16:23 → 09-27 03:24 UTC = **107.0 時間（4.46 日）**。
GPU が空転したのは Task B 終了後の約 40 分だけである（待受の自己一致、実行者の誤り）。

## Task D — test と対照

2026-09-27 03:26 UTC に `eval_stage1_dtower.sh all` を起動（val 14 回 → test 10 回、待受ポート 29731）。
04:23:09 UTC に終了、失敗 0、約 57 分。

### D-1 test の回数（関門 G3、完了判定 f）

| 項目 | 実測 |
|---|---|
| `test_access_ledger.csv` の test 行 | **10**（coco / imagenet × A〜E、seed 42） |
| 重複する（塔, 折り） | 0 |
| task_id 一致 | 10 / 10 |
| `eval_test.json` | 10 個。確定塔以外（折り A の seed 123・456）には無い |

陽性対照: 最終行を複製して 11 行にした複製では判定が落ちた。

### D-2〜D-5 表

`scripts/build_stage1_dtower_r2_table.py` が `results_table.md` と `results.json` を書く。要点は RESULT §4。
標的群 AP は集合の定義が無いため UNKNOWN（利用者の決定 2026-09-25）。per-class AP 15 クラスを代わりに置いた。

### D-6 所要時間表

`tools/estimate_tier_cost.py` の `det_tower_train` を 8.35 h → **14.13 h**（2 本同時の 13 run の平均）に更新、
`measured=True`。文書 `docs/stage0/B1_tier1_cost_estimate.md` の埋め込み 8 節を `--section` の出力で再生成し、
`--check-doc` で **差 0**。更新前の文書を新しい表で照合すると差を検出した（exit 1）。試験 15 件 PASS。

| 日数（K=2、装置 2 枚、24 h/日、縮退なし） | 更新前 | 更新後 |
|---|---|---|
| Stage 1 | 4.9 | **8.3** |
| Stage 1 + Tier 1 | 77.8〜107.0 | **81.2〜110.4** |
| 全体 | 85.4〜114.6 | **88.8〜118.0** |

## Task E — 検証と報告

| 検査 | 結果 |
|---|---|
| L1/L2 `make task-validate` | OK。L2-8 WARN 3 件（占位の分母、RESULT §6） |
| L3 `make task-preflight`（実行前 2026-09-22） | 11 PASS / 0 FAIL / 2 SKIP（P3 決定性、P12 参照なし） |
| L3（報告後 2026-09-27） | 9 PASS / 1 FAIL / 3 SKIP。FAIL は P11（復元したダミー GPU 保持 2 件）、追加の SKIP は P13（完了済み） |
| `make forbidden-check TASK=… BASE=66855c5b` | pass、違反 0（引数なしでは phase0 の前進分を拾い fail） |
| `make spec-check` | pass、規則 8 件 |
| 試験 | 6 failed / 618 passed。失敗 6 件は既存（test_engines 1・test_fetch_task 1・test_research_logger 4、いずれも本契約の未変更ファイル）。前契約の記録は 6 failed / 609 passed で、合格 +9 は本契約の新規試験 |
| `make runindex` | OK。`index.csv` で task_id 一致 **14 件** |
| 証跡 | metrics.json / per_class_ap.json / config.yaml / notes.md 各 14 / 14、task_id 刻印 14 / 14 |

GPU 保持のダミープロセス 2 件は 04:2x UTC に退避した原文から復元した（pid 483516 / 483518、各 40338 MiB）。
