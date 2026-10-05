# 結果 — T-2026-09-27-stage1-ptower-20

Stage 1 の工程塔 P\*-20（15 動画 ＋ 追加動画 17〜21 を train にだけ足す）を、三周目の確定 recipe のまま
二系統で確定した。あわせて、工程塔を送り手にしたときの train 動画と val 動画の予測の質の差を測った。
実測の詳細は `audit.md`、表は `docs/stage1/ptower_20.md`。数値はすべて実測で、未測定は UNKNOWN と書く。

**status: partial。** 塔は二系統とも確定し、test は折りごとに一度だけ評価した。送り手の差は 20 件すべてで
閾値を超えた。**ただし G2（ホスト差の対照）が不合格で、P\*-20（efros）と P\*-15（ilya）の差は
データ量の効果として読めない。** 利用者の決定で差を記録して続行した。

## 1. 解決された参照

| 記載 | 解決先 |
|---|---|
| `inputs.denominator.ref` | `runindex/experiments.csv` の `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`。split=val、n_seeds=3（42,123,456）、jaccard_mean 0.6322、jaccard_sstd 0.0224、jaccard_pstd 0.0215、jaccard_n 14、sigma_interpretation=unknown。三周目の RESULT は同じ参照を「折り A の 0.6447 ± 0.0119」と書いており食い違う。本契約は分母を判定に使わない |
| `inputs.sigma_policy` | 契約に記載なし。`conventions#sigma` の既定を継承（G2 の閾値は prereg が別に定める「折り A の seed 間 SD」を用いた） |
| `inputs.frozen_source.ref` | 契約に記載なし。L3 の P5 は `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`（sha256 `03936318…`）を照合して PASS |
| `contract.inject_verbatim` | `context/conventions.md` の 8 アンカー（prohibitions / issuer_cautions / folds / split / eval_recipe / sigma / symmetry / crossfit）を原文のまま適用（要約していない）。crossfit は PR #198 の統合後に存在 |
| `contract.conventions_rev` | 実測 `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6` |
| `meta.created_from.runindex_commit` | 実測 `2fb7c905b51aac5ec2b0ee5fe5c70e835f4024a8` |
| `prereg.commit` / `committed_at` | `0049f2fcf68028cccae2d184eab25b473b689055` / `2026-10-02T11:05:16+00:00` |

## 2. 関門

| 関門 | 判定 | 実測 |
|---|---|---|
| G1（A の後） | **pass**（二度停止の後） | 15 動画 15,437 枚、COCO 要約値 `a755b3eb…`、ImageNet 要約値 `4f6b5b62…`、三周目の確定構成が揃う。動画 20・21 のフレームが無く停止→利用者が移送。動画 19 の 1,932 枚の破損で停止→再送。最終的に追加 10,461 枚が全数デコードでき注釈と一致 |
| G2（C の後） | **ask → 利用者の決定で続行** | efros 0.7762 / ilya 0.7066、差 **+0.0696**、閾値 0.0372（SD 比 3.7） |
| G3（E の後） | **pass** | test 10 回（2 系統 × 5 折り）、台帳 10 件 completed、二重評価は FileExistsError |

## 3. 完了判定

| # | 判定 | 結果 | 実測 | 空振りでないことの確認 |
|---|---|---|---|---|
| a | 追加動画は train のみ、22 は除外 | **達成** | 5 折りとも train に 17〜21 だけが増え、val・test は不変、22 は無い（`p20_manifest/audit.json`） | 折り A の val に 17 を混ぜると、折り C の train に 22 を混ぜると照合が落ちる（試験） |
| b | recipe の一致 | **達成** | 実 run 28 本（fine-tune 14・時間ヘッド 14）を三周目の同じ系統・折り・seed と照合し recipe 項目の差 0 件。差は識別子・出力先・キャッシュ・manifest・GPU 番号・データ一覧と派生するクラス重み・`pin_memory` のみ | ft_accum_steps を 4→2 にすると差分 1 項目（試験） |
| c | ホスト差 | **達成（判定は不合格）** | efros 0.7762 / ilya 0.7066、差 +0.0696 | SD の出所は三周目の `_059_` / `_064_` / `_069_`（0.7066 / 0.6884 / 0.7255）、標本 SD 0.0186。規則は結果前に `host_control_rule.json` へ |
| d | 並置 | **達成** | `validation_runs.csv` 15 行（14 ＋ 対照 1）。test 10 行を P\*-15 と並置 | `table()` が行数 15 を assert |
| e | 送り手の train と val の差 | **達成** | 4 塔 × 5 折り = 20 件、全件閾値超え | train 動画は run の config に刻まれた train と assert で一致（20/20）。gap で計算した val J は学習時の val J と最大差 0。壊した入力での確認は UNKNOWN |
| f | test | **達成** | 10 回、台帳 10 件 | `open("x")` が FileExistsError |
| g | 対称性とカード | **達成** | prereg §3 の 16 行に UNKNOWN 0 件。L3 の P13・P14 が実行前（取り込み直後）と Task F で PASS | カードの経路を変えた一時契約での FAIL は UNKNOWN（作っていない） |
| h | 刻印と収穫 | **達成** | `make runindex` 後 task_id で引いて 50 行 = 実験フォルダ 50（完了 45 ＋ 未完了 5）。全 50 run の `contract_sha256` は現在の spec.yaml の `ffdc99e0…` と一致 | 行数の差ではなく task_id で照合 |
| i | PR | 本報告の commit 後に記入 | — | 分岐名 `feat/stage1-ptower-20` |

## 4. 実測

### ホスト差（Task C）

| | efros | ilya |
|---|---|---|
| 時間ヘッドを載せた val macro Jaccard | **0.7762** | 0.7066 |
| val frame accuracy | 0.8713 | 0.8416 |
| fine-tune 段階のフレーム単位 val J / acc | 0.6523 / 0.8607 | 0.6460 / 0.8521 |
| fine-tune の最良 epoch / 低下 / 打ち切り | 13 / 17 / 21 | 17 / 16 / 21 |
| fine-tune の所要 | 4.47 時間 | 3.11 時間 |

fine-tune 段階の差は +0.0063 と小さく、時間ヘッドで +0.0696 に広がった。efros の対照は 1 seed のみで、
恒常的なホスト差か揺れかは区別できない（UNKNOWN）。

### P\*-20 と P\*-15（5 折り平均。折り A は 3 seed の平均）

| 系統 | P\*-20 val J | P\*-15 val J | 差 | 差 / P\*-15 の折り間 SD | P\*-20 test J | P\*-15 test J | 差 | 差 / P\*-15 の折り間 SD |
|---|---|---|---|---|---|---|---|---|
| COCO | 0.7012 | 0.6558 | +0.0454 | 1.08 | 0.6402 | 0.5176 | +0.1226 | 3.02 |
| ImageNet | 0.5999 | 0.4785 | +0.1214 | 1.16 | 0.5317 | 0.4095 | +0.1222 | 2.03 |

co-primary（frame accuracy）: val は COCO 0.8767 / 0.8478、ImageNet 0.8395 / 0.7781。test は COCO 0.8551 / 0.7965、
ImageNet 0.8050 / 0.7618。主指標と同方向。

折りごとの val の差は COCO で +0.0251 / −0.0552 / +0.1149 / +0.0353 / +0.1069、ImageNet で +0.1380 / +0.0836 / +0.1134 /
+0.1048 / +0.1673。折り単位の符号は記述統計としてのみ記す（規約）。

**この差はホストをまたぐ。** 同一ホストの唯一の点（COCO・折り A・seed 42）で P\*-20 0.7461 は efros の P\*-15 0.7762 を
0.0301 下回る。

### 送り手の train と val の差（閾値 3pt = 0.03）

| 系統 | 設定 | 差 J の 5 折り平均 | 最小 | 最大 | 閾値超え |
|---|---|---|---|---|---|
| COCO | P\*-15 | +0.2521 | +0.1254 | +0.3259 | 5/5 |
| COCO | P\*-20 | +0.2510 | +0.1871 | +0.3376 | 5/5 |
| ImageNet | P\*-15 | +0.3968 | +0.2887 | +0.5626 | 5/5 |
| ImageNet | P\*-20 | +0.3449 | +0.2438 | +0.4622 | 5/5 |

frame accuracy の差も 20 件中 20 件が 0.03 を超えた（最小 +0.0477）。主指標と co-primary は食い違わない。
P\*-15 の塔は ilya で学習し efros で推論した。差は同じ塔の train と val の比較なのでホスト差を受けない。

### 所要時間

| 段 | 本数 | 1 本 | 合計 |
|---|---|---|---|
| fine-tune（P\*-20） | 14 | 4.06〜8.56 時間（8 時間超 2 本） | 90.0 GPU 時間 |
| fine-tune（対照） | 1 | 4.47 時間 | — |
| 特徴抽出 | 15 | 366〜1,833 秒（決定性の検証つき 1 本が最長） | — |
| 時間ヘッド | 15 | 7〜33 秒 | — |

到達 epoch 9〜18、上限 36 への張り付き 0/14、学習率の低下と打ち切りは 14/14 で働いた。記憶領域の最大は 27.06 GiB（装置 47.4 GiB）。
efros の A6000 は短辺 800・batch 16 で 14.2 フレーム/秒（ilya は 20.9）。物理 batch 16 × 累積 4（batch 32 は OOM）。

### 予測 5 項目の当たり・外れ

| # | 予測 | 結果 | 実測 |
|---|---|---|---|
| 1 | P\*-20 が両系統で P\*-15 を上回り、差は 0.01〜0.03 | **外れ** | 方向は両系統で上（+0.0454 / +0.1214）だが、大きさが範囲を超えた。ホスト差が混ざる |
| 2 | 上がり幅は COCO 系統の方が小さい | **当たり** | +0.0454 < +0.1214。ホスト差が混ざる |
| 3 | efros の P\*-15 は ilya と seed 間 SD の 2 倍以内で一致 | **外れ** | +0.0696（閾値 0.0372） |
| 4 | 送り手の train と val の差は 3pt を超える | **当たり** | 20/20、最小 +0.1254 |
| 5 | val と test の乖離は P\*-15 と同程度 | **外れ（片方）** | ImageNet は 0.0682 / 0.0690 で同程度。COCO は 0.0610 / 0.1382 で P\*-20 が半分以下 |

**予測外れは 3 件（1・3・5）。**

## 5. 起票者の誤り

`result.yaml` の `issuer_defects` に 5 件。要約すると、entrypoint が一周目の道具を指す（三周目と同じ誤り）、expected_runs 30 が
特徴抽出を数えていない（実装すると 45）、「ilya から移す」とするが ilya に動画 17〜22 の画像は無い、フレーム数の照合が画像の破損を
検査しない（動画 19 の 1,932 枚が通った）、created_from.counts が 0 のまま。

## 6. 逸脱

`result.yaml` の `deviations` に 10 件。**「逸脱なし」ではない。** 主なものは、G2 前に Task D を始めた（了承済み）、
G2 不合格を記録して続行（利用者の決定）、8 時間超の承認、P\*-20 だけ `pin_memory=False`、未完了 run 5 件、
`make forbidden-check` が未追跡の注釈 CSV 20 件で fail。

## 7. 想定外

1. **efros の cgroup 上限 52 GiB で OOM。** 2 本並べたとき、PyTorch 2.1 の pinned メモリのキャッシュが val 1 回で約 24 GiB まで
   積もって返らず、2 本とも SIGKILL された。原因を再現で特定し `pin_memory=False` で解消した（数値は同一）
2. **追加動画 19 の画像が切れていた。** 数は注釈と一致したが 1,932 枚が 262,144 バイトで途切れていた。最初の再送は 19 全体を消して
   途中で止まり、二度目で揃った
3. **実行者の起動方法の誤り。** Bash の背景実行は 30 分で子プロセスごと止まり、対照の一本目が 2 epoch で消えた。以後は setsid で切り離した
4. **G2 のホスト差が時間ヘッドで増幅された。** fine-tune 段階では +0.006 だった

## 8. 解釈と次

**塔は確定した。** P\*-20 の二系統（各 5 折り、折り A は 3 seed）が efros に揃い、test は折りごとに一度だけ評価した。

**データ量の効果はまだ言えない。** P\*-20 と P\*-15 の差（val で COCO +0.045、ImageNet +0.121）は、G2 で測ったホスト差（+0.070）と
同じ桁で、同一ホストの唯一の点では符号が逆になる。主張するには P\*-15 を efros で回し直す必要がある（14 本、2 枚で約 31 時間）。

**工程塔の送り手にも交差適合が要る。** train と val の差は 20 件すべてで 12〜56 点あり、閾値 3pt を大きく超える。検出塔の送り手の差
（約 11pt、Stage 0）より大きい。`conventions#crossfit` に従い、Stage 2 の P→D 側でも工程塔の送り手に交差適合を適用する。
この結論は同じ塔の train と val の比較なのでホスト差を受けない。

## 9. 送出

本報告の commit・push・PR の後に記入する。
