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

結果は実測後に追記する。
