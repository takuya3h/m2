# RESULT — T-2026-09-19-stage1-detector-towers-r2

**判定: pass。** 全 14 run が収束基準で学習を終え、test を折りごとに一度（合計 10 回）評価した。
**収束まで学習しても両塔の差は縮まなかった。** 一周目の差は学習不足では説明されていない。

## 1. 解決された参照

| 参照 | 解決先 |
|---|---|
| `inputs.denominator.ref` = `exp:baselines/s0/relationdetr_bbox@val` | `runindex/experiments.csv` に在る。本契約は分母との差を主張しないため値は使っていない |
| `inputs.frozen_source` | P5 が `checkpoints/incoming/seed42/best_ap.pth` sha256 `03936318…5824` を照合し PASS。**変えていない** |
| `contract.conventions_rev` | 占位 → `c801e17c3231fe1f2b7c8072e1a960e6dbab8ca5`（`context/conventions.md` を最後に変えた commit） |
| `meta.created_from.runindex_commit` | 占位 → `4e97b3deae28e653948c19309d229c755587c42b` |
| `contract.inject_verbatim` 8 節 | `context/conventions.md` の原文を読んだ。`folds` の表は `scripts/verify_stage1_dtower_r2_folds.py` の `EXPECTED` にそのまま写してある |

## 2. 関門

| 関門 | 判定 | 実測 |
|---|---|---|
| G1（A の後） | pass | 一周目 14 run の `val/mAP` を TensorBoard の原値で読めた。規則は `main.py:211-215`（生成）と `main.py:249`（呼び出し）の各 1 箇所で、塔を見る分岐が無い。構文木の試験で確認 |
| G2（B の後） | pass | D\*-ImageNet 折り A seed 42 で学習率の低下 epoch 15、打ち切り epoch 28、最良 epoch 24。上限 36 に達していないため諮る条件に当たらない |
| G3（D の後） | pass | test 評価は台帳に **10 行**（両塔 × 5 折り、重複 0、task_id 一致 10）。確定塔以外 0 件 |

## 3. 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 低下と打ち切りが両塔で同一 | `main.py:211-215`・`229-230`・`241-252`・`263-264`。run ごとの低下・打ち切り・最良 epoch は §4 の表 | 生成 1 箇所・呼び出し 1 箇所を構文木で確認。**patience を 4→2 にすると低下 epoch が 8→6 へ動いた**（`test_patience_changes_the_timing_of_the_decay`） |
| b | 折り表に従う | 15 行（5 折り × train/val/test）すべて対称差 0 | 折り A の test を 07→11 に入れ替えると対称差 2 |
| c | 表と一周目の並置 | **14 行**。val mAP・AP_rare・AP_common・test mAP に一周目の同じ run（同じ評価 recipe の `eval_val.json`）を並置。`results_table.md` | 一周目の出所は `experiments/baselines/stage1_dtower/<run>/eval_val.json`。**標的群 AP は UNKNOWN**（§7） |
| d | 上がり幅と差の比較 | §4。差は 4.73 → 4.64 mAP（折り A）、4.52 → 4.38 mAP（5 折り） | 差の計算は `results.json` の `aggregates`。評価済み 2 run の時点で走らせると差は UNKNOWN と出た（未測定を数値で埋めない） |
| e | 上限に達した run | **D\*-COCO 0 件 / D\*-ImageNet 0 件**。低下を受けずに上限へ達した run も 0 件（最長 31 epoch） | 上がり続ける並びで `stopped_epoch` が None のまま残ることを試験で確認（`test_improvement_resets_the_counter`） |
| f | test は折りごとに一度 | 台帳 10 行、`eval_test.json` 10 個。確定塔以外 0 件 | 台帳の最終行を複製して 11 行にすると判定が落ちた |
| g | 所要時間と計算器 | 2 本同時 13 run 平均 **14.13 h**（9.97〜20.52）、`measured=True`、`--check-doc` 差 0。日数は §5 | 更新前の文書を新しい表で照合すると差が出た（exit 1） |
| h | 対称性の表 | prereg §3 に 15 行、UNKNOWN 0 件。**実行前の L3 で P13 PASS**（2026-09-22 16:2x UTC） | 起票時の列名（D\*-COCO / D\*-ImageNet）では P13 が FAIL した。報告後は完了済みとして SKIP になる（§6） |
| i | 刻印と収穫 | `make runindex` 後に `index.csv` で task_id 一致 **14 件** | 1 run の `config.yaml` から task_id を抜いた複製では 13/14 になった |
| j | PR | 送出後に記録（§8） | 分岐 `feat/stage1-detector-towers-r2`、base phase0 |

## 4. 実測

値は評価 recipe（`eval_relation_detr_map.py`、NMS-free）の出力。run ごとの全列は `experiments/baselines/stage1_dtower_r2/results_table.md`。

| run | val 一周目 | val 二周目 | 上がり幅 | test 一周目 | test 二周目 | 低下 | 打ち切り | 最良 | epoch |
|---|---|---|---|---|---|---|---|---|---|
| dcoco_foldA_seed42 | 0.7244 | 0.7273 | +0.0029 | 0.5117 | 0.5085 | 9 | 14 | 10 | 15 |
| dcoco_foldA_seed123 | 0.7254 | 0.7289 | +0.0035 | — | — | 9 | 17 | 13 | 18 |
| dcoco_foldA_seed456 | 0.7208 | 0.7190 | −0.0018 | — | — | 11 | 16 | 12 | 17 |
| dcoco_foldB_seed42 | 0.4762 | 0.4557 | **−0.0205** | 0.4384 | 0.4324 | 11 | 20 | 16 | 21 |
| dcoco_foldC_seed42 | 0.4385 | 0.4339 | −0.0045 | 0.5011 | 0.4803 | 9 | 14 | 10 | 15 |
| dcoco_foldD_seed42 | 0.4967 | 0.5117 | +0.0150 | 0.5558 | 0.5724 | 7 | 16 | 12 | 17 |
| dcoco_foldE_seed42 | 0.5272 | 0.5312 | +0.0040 | 0.5841 | 0.5938 | 10 | 16 | 12 | 17 |
| dimagenet_foldA_seed42 | 0.6853 | 0.6855 | +0.0003 | 0.4724 | 0.4739 | 15 | 28 | 24 | 29 |
| dimagenet_foldA_seed123 | 0.6774 | 0.6750 | −0.0024 | — | — | 22 | 30 | 26 | 31 |
| dimagenet_foldA_seed456 | 0.6660 | 0.6755 | +0.0095 | — | — | 14 | 19 | 15 | 20 |
| dimagenet_foldB_seed42 | 0.4084 | 0.4087 | +0.0002 | 0.4064 | 0.3979 | 21 | 28 | 24 | 29 |
| dimagenet_foldC_seed42 | 0.4093 | 0.4088 | −0.0005 | 0.4802 | 0.4624 | 13 | 20 | 16 | 21 |
| dimagenet_foldD_seed42 | 0.4801 | 0.4733 | −0.0068 | 0.5164 | 0.5172 | 16 | 26 | 22 | 27 |
| dimagenet_foldE_seed42 | 0.4538 | 0.4646 | +0.0107 | 0.5655 | 0.5569 | 10 | 16 | 12 | 17 |

epoch は 0 起点。AP_rare（Skewer・Syringe）と全 15 クラスの per-class AP は `results_table.md`。

| 折り A（3 seed） | 一周目 | 二周目 |
|---|---|---|
| D\*-COCO 平均 (SD) | 0.7235 (0.0024) | 0.7251 (0.0053) |
| D\*-ImageNet 平均 (SD) | 0.6762 (0.0097) | 0.6787 (0.0059) |
| **差（COCO − ImageNet）** | **4.73 mAP** | **4.64 mAP** |

| 塔間の差 | 一周目 | 二周目 |
|---|---|---|
| val、5 折り seed 42 の平均 | 4.52 mAP（A 3.92 / B 6.77 / C 2.92 / D 1.66 / E 7.33） | 4.38 mAP（A 4.18 / B 4.70 / C 2.52 / D 3.84 / E 6.66） |
| test、5 折りの平均 | 3.00 mAP | 3.58 mAP |

| 上がり幅（7 run） | 平均 | 範囲 | 上がった run |
|---|---|---|---|
| D\*-COCO | **−0.0002** | −0.0205〜+0.0150 | 4 / 7 |
| D\*-ImageNet | **+0.0016** | −0.0068〜+0.0107 | 4 / 7 |

**上がり幅は両塔とも折り A の seed 間 SD（0.005〜0.006）を下回る。** 一周目の 12 epoch 版は見かけより収束に近く、
D\*-ImageNet も epoch 12〜15 は一周目の最良を下回って推移し、学習率を下げてはじめて超えた（audit §B-2）。
`dcoco_foldB_seed42` の −2.05 mAP は同一 seed の再現幅（epoch 0 で 0.014 のずれを実測、P3 は SKIP）と切り分けられない。

### prereg §4 の予測

| 予測 | 実測 | 当たり外れ |
|---|---|---|
| 1 D\*-ImageNet は上がる | 折り A 平均 +0.0025、7 run 平均 +0.0016、上がった run 4/7 | **方向は当たり、幅は seed 間 SD 以下**。実質は外れ |
| 2 差は縮むが零にならない | 折り A 4.73 → 4.64、5 折り 4.52 → 4.38、test は 3.00 → 3.58 | 零にならないは当たり。**縮むは外れ**（val −0.1 mAP、test は広がった） |
| 3 D\*-COCO は ±1 mAP 以内 | 平均 −0.0002。ただし折り B が −2.05 mAP | 平均は当たり、**1 run が外れ** |
| 4 ImageNet の低下と打ち切りは遅い | 低下 7〜11 対 10〜22、打ち切り 14〜20 対 16〜30。折りの対で 6/7 が遅く、E は同じ | **当たり** |
| 5 折り B〜E は A より低い | COCO 0.434〜0.531 対 0.725、ImageNet 0.409〜0.473 対 0.679 | **当たり** |

### 決定への含意（`intent.decision_at_stake`）

一周目の差 4.1〜4.7 mAP は初期化源（COCO 検出の事前学習の有無）の効果であり、学習不足の分は測定限界以下である。
D\*-ImageNet は **表現の違う塔として H3 の腕に使える**。差の大きさは既知量として持ち越す。

## 5. 所要時間

| 項目 | 実測 |
|---|---|
| 2 本同時の 13 run | 平均 14.13 h、範囲 9.97〜20.52、合計 183.7 run 時間。1 epoch 0.649〜0.773 h |
| 単独の Task B | 12.37 h（29 epoch、0.427 h/epoch）。平均には含めない |
| GPU 時間 | 学習 392.1 GPU 時間 + 評価 24 回 約 57 分 × 2 枚 |
| 経過 | 学習 2026-09-22 16:23 → 09-27 03:24 UTC = **107.0 h（4.46 日）**。契約の見積 145 h の内側 |
| 停止条件 | 27 h 超 0 件、上限到達 0 件、発散 0 件 |
| 計算器 | `det_tower_train` 8.35 → 14.13 h。**Stage 1 は 4.9 → 8.3 日、全体（K=2、24 h/日、縮退なし）は 85.4〜114.6 → 88.8〜118.0 日** |

## 6. 起票者の誤り

| 型 | 内容 |
|---|---|
| asserted_without_measuring | prereg §3 の列名が `D\*-COCO / D\*-ImageNet` で、自ら注入した `conventions#symmetry` の `腕1 / 腕2` と違い P13 が FAIL。列名だけ直した（利用者の決定） |
| asserted_without_measuring | 「2026-06-19 に事前登録した標的群」の集合が repo のどこにも無い。UNKNOWN で報告（利用者の決定） |
| self_contradiction | `created_from.counts` を占位 0 のまま渡しつつ `escalate_if` に `denominator_moved` を置くため、L2-8 が必ず WARN する。起票時の値は測られていない |
| self_contradiction | 完了判定 h が「L3 の P13 が PASS」を求めるが、報告を書くと完了済みとして SKIP になる（T-2026-09-19-p13-skip-and-enum）。実行前の PASS を証拠にした |
| check_does_not_check | `allow_write` が実験フォルダと `runindex/` だけを挙げるが、Task A-4・D-6・E は `third_party/`・`tools/`・`docs/stage0/`・`tests/`・`scripts/` の変更を求める。禁止領域の外だったため `forbidden-check` は通った |

## 7. 逸脱と UNKNOWN

| 種別 | 内容 |
|---|---|
| spec_defect | prereg §3 の列名を正本へ直した（15 行の判定と理由は無改変。`meta.amendments` に記録） |
| spec_defect | 標的群 AP は **UNKNOWN**。全 15 クラスの per-class AP と AP_rare / AP_common を代わりに出した。集合が決まれば GPU なしで再計算できる |
| environment | `third_party/` は `.gitignore:133` で追跡外のため実装本体が PR に現れない。写しを `experiments/baselines/stage1_dtower_r2/impl/*.txt` に置いた |
| environment | 開始時の未追跡 3 件を利用者の指示で `git stash` へ退避。GPU 保持のダミープロセス 2 件を実験前に停止し、評価後に原文から復元した |
| judgement | `make forbidden-check` は分岐点 `66855c5b` を `BASE` に、契約を `TASK` に与えて pass。引数なしでは phase0 の前進分を違反に数える |
| judgement | 計算器の平均から単独実行の Task B を除いた（2 本同時の条件が違う） |
| judgement（実行者の誤り） | Task B の完了を待つ `pgrep -f` が自分自身に一致して眠り、**GPU が約 40 分空転し「走行中」と誤報告した**。pid と `done.txt` を見る形に替えた。Task B の `end.txt` も 05:27 → 04:45:47 に訂正 |
| UNKNOWN | 標的群 AP。決定性（P3 SKIP、同一 seed で epoch 0 が 0.014 ずれる）。`dcoco_foldB_seed42` の −2.05 mAP が再現幅の内か外か |

## 8. 送出

L1/L2 validate OK（L2-8 WARN 3 件は §6）、L3 preflight は実行前 11 PASS / 0 FAIL / 2 SKIP、報告後は 9 PASS / 1 FAIL / 3 SKIP（FAIL は復元したダミー GPU 保持プロセスによる P11、SKIP の追加は完了済みによる P13）、`forbidden-check` pass、`spec-check` pass、
試験 6 failed / 618 passed（失敗 6 件は既存で本契約の未変更ファイル。合格 +9）、`make runindex` OK。
PR 番号・commit・`task-report` の結果は送出後に追記する。
