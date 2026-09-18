# 二周目の監査 — T-2026-09-19-stage1-phase-tower-r2

## Task A — 開始状態と材料

### 事前登録

`prereg.md` のみを学習開始前に commit した。commit `8aa636bf597abde3393405c59a8e94ad28d18288`、
時刻 `2026-09-18T13:32:26+09:00`（JST）。作業ファイルと commit の内容はバイト単位で一致する。
`spec.yaml` の占位はすべて実測値へ差し替えた。

| 項目 | 実測 |
|---|---|
| `conventions_rev` | `e7a5100597a79b3b9c60935bf38d232f8ae96822` |
| `runindex_commit` | `92508ff4bcada0f8c39a6f570f67c2f1a685f15a` |
| `created_from.counts` | index 1339 / experiments 338 / verdicts 1506 |

差し替え後の `make task-validate` は exit 0 で WARN 0 件（差し替え前は L2-8 の WARN 3 件。
利用者が了承したうえで差し替えた）。

### 開始状態

| 項目 | 実測 |
|---|---|
| 分岐 | `feat/stage1-phase-tower-r2`（起点 `origin/phase0`） |
| HEAD | `9fbf0d31`（PR #183 を phase0 へ併合した commit） |
| PR #183 の統合 | **統合済み**（`git merge-base --is-ancestor origin/feat/stage1-phase-tower HEAD` が真） |
| 一周目の道具 | `run_stage1_ptower.py` `select_stage1_ptower.py` `stage1_ptower.py` `train_phase_tower_r50.py` すべて在り |
| 一周目の成果物 | `experiments/phase1/stage1_ptower/` と 72 run |
| 装置 | RTX 6000 Ada ×2。compute プロセス 0 件（`nvidia-smi --query-compute-apps` と `/proc/PID/exe` の解決） |
| 作業ツリー | 契約ディレクトリ以外は清浄 |

### 追加 6 動画（17〜22）

**画像は 0 件。注釈は 23 csv が在る。**

- 探索範囲: `data/` 全体（`data/raw` `data/external` を含む）。ディレクトリ名 `17`〜`22` と
  ファイル名接頭辞 `1[789]_*.jpg` `2[012]_*.jpg` の両方
- 陽性対照: 同じ探索を動画 `01` に当てると 3254 件が当たり、ディレクトリも 2 件見つかる。
  **探索は空振りではない**
- 注釈の所在: `data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase/`
- 画像の所在は `data/raw/ego/{train,val,test}/{video}/` で、在るのは 15 動画（01〜15 のうち 15 本）のみ

したがって **P\*-21 は UNKNOWN**。契約 §6 の規定に従い停止せず P\*-15 を進めた。
一周目（2026-09-18）と同じ結論である。

### `train_phase_tower_r50.py` の既定（prereg §2 が参照する値）

| 項目 | 実測値 | 出所 |
|---|---|---|
| 凍結範囲 | **凍結なし**（`AdamW(model.parameters(), ...)`、`scripts/train_phase_tower_r50.py:126`） | 実装 |
| 学習率 | `1e-4`（`--lr` の既定、同 104 行） | 実装 |
| weight decay | `1e-4`（同 105 行） | 実装 |
| batch | `64`（同 106 行） | 実装 |
| 最適化器 | AdamW（同 126 行） | 実装 |
| 損失 | 重みなし CE（同 127 行） | 実装 |
| 増強 | `RandomHorizontalFlip` のみ（同 46〜48 行の `TF_TRAIN`） | 実装 |

凍結範囲が stem のみでないため、SPEC Task A-5 に従い **stem のみ凍結へ揃えた**。
実装は既存スクリプトを書き換えず、`scripts/stage1_ptower_r2.py` の `build_backbone` で
`model.conv1` と `model.bn1` の `requires_grad_(False)` を立て、`stem_eval` で凍結した
stem の batch 統計を固定する形にした。

学習率 2 水準は既定 `1e-4` を高い方、その 1/3 の `3.3333333333333335e-05` を低い方とした。

## Task B — backbone の fine-tune

### 凍結範囲の実測（判定 b）

`requires_grad` が True のパラメータ数を群ごとに数えた。

| 群 | 学習対象のパラメータ数 |
|---|---|
| stem（conv1, bn1） | **0** |
| layer1 | 215,808 |
| layer2 | 1,219,584 |
| layer3 | 7,098,368 |
| layer4 | 14,964,736 |
| fc | 18,441 |

陽性対照: `model.conv1.requires_grad_(True)` に戻すと stem の数が非零になることを
試験 `test_only_the_stem_is_frozen` で確かめた。

### 1 本目の実測（所要時間の測定、SPEC Task B-2）

折り A・seed 42・lr 1e-4。

| 項目 | 実測 |
|---|---|
| 所要 | **411.39905246999115 秒**（12 epoch）。1 時間の停止条件に触れない |
| 最良 epoch | 5 / 12 |
| val frame accuracy | **0.6825082508250825** |
| 一周目の単フレーム線形対照 | 0.48382838283828383 |
| 差 | +0.1986798679867987 → **G2 を通過** |
| checkpoint sha256 | `7f4ab1f99a2ec03039581a9a773b7faef247191f2cf64a441d124ccbfd4bb170` |
| 損失 | epoch 1 の 0.509308 から epoch 12 の 0.009079 へ単調に近く低下。非有限 0 件 |

## 逸脱の記録（Task B の測定中に起きたこと）

**実行者の誤読 1 件。** 1 本目の実行中、出力ファイルに epoch 行が現れず GPU 利用率が 38% だったため、
「データ供給が律速」と判断して `workers` を上げようとした。**実際には出力の書き出しが遅れていただけで、
12 epoch は 411 秒で完走していた。** 停止と削除の命令を出したが、`pkill -f` の模様が
自分の命令行に部分一致して自滅し（`conventions#issuer_cautions` の注意 6 の型）、
後続の `rm -rf` に到達しなかった。**実験フォルダ・checkpoint・metrics はすべて無傷である。**
設定は変更していない。この経緯は隠さず記録する。

### fine-tune 14 本の実測（Task B 完了、G2）

一周目の単フレーム線形対照は val frame accuracy `0.48382838283828383`（折り A・seed 42）。

| lr | 折り | seed | val frame accuracy | 対照との差 | 最良 epoch | 所要（秒） |
|---|---|---|---|---|---|---|
| 1e-4 | A | 42 | 0.68251 | +0.19868 | 5 | 411 |
| 1e-4 | A | 123 | 0.70099 | +0.21716 | 3 | 417 |
| 1e-4 | A | 456 | 0.71485 | +0.23102 | 9 | 562 |
| 1e-4 | B | 42 | 0.52660 | +0.04277 | 2 | 590 |
| 1e-4 | C | 42 | 0.66600 | +0.18217 | 12 | 625 |
| 1e-4 | D | 42 | 0.61316 | +0.12933 | 3 | 644 |
| 1e-4 | E | 42 | 0.69639 | +0.21256 | 1 | 648 |
| 3.3333e-5 | A | 42 | 0.67591 | +0.19208 | 4 | 544 |
| 3.3333e-5 | A | 123 | 0.64554 | +0.16172 | 9 | 553 |
| 3.3333e-5 | A | 456 | 0.67921 | +0.19538 | 4 | 554 |
| 3.3333e-5 | B | 42 | 0.58463 | +0.10080 | 1 | 579 |
| 3.3333e-5 | C | 42 | 0.64286 | +0.15903 | 10 | 632 |
| 3.3333e-5 | D | 42 | 0.57126 | +0.08743 | 12 | 648 |
| 3.3333e-5 | E | 42 | 0.72032 | +0.23649 | 1 | 658 |

**G2 通過。対照を下回る run は 0 件**（最小の余裕は折り B・lr 1e-4 の +0.04277）。
所要は 1 本 411〜658 秒で、停止条件の 3600 秒に触れた run は無い。合計 8064 秒。
損失の非有限は 0 件（`finetune` が epoch ごとに `torch.isfinite` で検査し、
該当すれば `RuntimeError` で止める設計。止まった run は無い）。

学習率ごとの val frame accuracy の平均は lr 1e-4 が 0.65721、lr 3.3333e-5 が 0.64568 で、
**この段階では高い方がわずかに優勢**である。prereg §3 の予測 4（低い方が最良）と逆の向きだが、
判定は時間ヘッドを載せた 5 折り平均 val macro Jaccard で行うため、ここでは向きの記録に留める。

最良 epoch は 1〜12 に散らばり、折り B と折り E は両水準とも 1〜2 で早い。
**上限 12 に張り付いた run は 3 件**（lr 1e-4 の折り C、lr 3.3333e-5 の折り D、
および lr 3.3333e-5 の折り C が 10）。上限を増やせばさらに上がる余地は残る。
prereg は上限 12 を D\* と揃えて固定しているため、本契約では増やさない。

## Task C — 特徴の抽出（判定 c）

fine-tune 後の各 backbone から、その折りの全動画（train・val・test の 15 動画）の C5 GAP 2048 次元を
抽出した。前処理は**一周目と同一**（`ResNet50_Weights.IMAGENET1K_V1.transforms()`）で、
増強は入れない。これにより一周目との差が backbone の重みだけになる。

### 決定性と陰性対照（折り A・seed 42・lr 1e-4 で実測）

| 検査 | 実測 |
|---|---|
| 一度目の要約値 | `f91d6c9f51191a0ffafed63743b08f5acabd5facb828832345601ae115f43e0e` |
| 二度目の要約値 | 同じ値（**一致**） |
| 重みを変えると変わるか | `weight_change_detected: true`（`conv1.weight` を零にして戻す陽性対照） |
| 別の backbone だと変わるか | 折り A・seed 123 は `3648feedec85c76c1ba10d32c325b3dddf57189829f52fbff9302b8f5a4c1cbd` で**異なる** |
| フレーム数 | 15 動画 15437 フレーム（一周目の抽出と同数） |
| 大きさ | 127016156 バイト（1 本あたり） |
| 所要 | 決定性を検査した 1 本が 148.92 秒（4 回のフルパス）、検査なしの 1 本が 54.87 秒 |

置き場は `data/processed/stage1_features/r2_ft_lr{lr}_fold{F}_seed{S}/all_gap.npz`。
**`data/processed/**` と `*.npz` は `.gitignore` 済みで追跡 0 件**のため、版管理の差分には現れない。

### 実行者の誤り（記録）

`COMPLETE` の通知を受けて 1 本目の完了を報告したが、**実際にはまだ走行中**で
`metrics.json` は空、特徴ファイルも無かった。実験ディレクトリと `EX.log` を確かめて誤りに気づいた。
`conventions#issuer_cautions` の注意 12（判断の前に、いま見ているものが最新かを確かめる）の型である。
**通知を完了の証拠として扱わない。証跡のファイルで確かめる。**

### 14 本すべての要約値（判定 c の「別の backbone で変わる」）

`EX` は 14/14 が完走し、**特徴の要約値は 14 種すべて互いに異なる**。
1 本あたり 127,016,156 バイト、合計およそ 1.78 GB。所要は 54.9〜148.9 秒。

| backbone | feature_sha256（先頭 16 桁） |
|---|---|
| lr 1e-4 折り A seed 42 | `f91d6c9f51191a0f` |
| lr 1e-4 折り A seed 123 | `3648feedec85c76c` |
| lr 1e-4 折り A seed 456 | `d8672e1d7edb5664` |
| lr 1e-4 折り B seed 42 | `a243b4675e849430` |
| lr 1e-4 折り C seed 42 | `bce761e2f4b0f96d` |
| lr 1e-4 折り D seed 42 | `e29eca80c2fe3e8b` |
| lr 1e-4 折り E seed 42 | `77c1db602a01db3a` |
| lr 3.3333e-5 折り A seed 42 | `affcad6d459fa805` |
| lr 3.3333e-5 折り A seed 123 | `933c32b5abcd8693` |
| lr 3.3333e-5 折り A seed 456 | `becebf8910f59e86` |
| lr 3.3333e-5 折り B seed 42 | `bf18b3a6108d2e0f` |
| lr 3.3333e-5 折り C seed 42 | `44fa23e4d8b6062c` |
| lr 3.3333e-5 折り D seed 42 | `d90e5d9bf0f0d4dc` |
| lr 3.3333e-5 折り E seed 42 | `8c8042a22d892406` |
