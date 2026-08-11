# T-2026-08-11-split-and-recipe-audit — 完了報告

分割と評価条件が、記録の上でも実体の上でも一貫していたかを実測した。読み取りのみ。

**結論を先に書く。** 分割の実体は健全であり、そこから汚染は生じていない。
一方、**S0 の検出器比較表は 6 種類の評価条件に跨っており、そのままでは検出器間の
差として読めない。** 起票者が疑った「ゼロのまま素通り」は仕組みとしては実在したが、
発火は 3 run だけで、工程側では 0 件だった。**工程側の真の問題は別にあった。
記録されている 9657 は実測ではなく定数の転記である。**

---

## 1. 解決された参照

`contract.inject_verbatim: [conventions#prohibitions]` — `context/conventions.md` の
`#prohibitions` アンカーの原文（`conventions_rev: d422b08`）:

> ## prohibitions
>
> - `runindex/**` と `context/auto/**` は生成物である。**手で編集しない。**
> - `experiments/**` `transfer/**` `data/**` は証跡である。**読み取りのみ。**
> - 未測定の値を書かない。測っていないものは `UNKNOWN` と書く。
> - 数値を捏造しない。環境制約で測れない場合は「測れない」と書く。

spec の `conventions_rev` は起票時 `UNKNOWN` だったため、実測した `d422b08` に置いた
（後述の逸脱 1）。`inputs.denominator` は本 spec に無いため参照解決は発生していない。

---

## 2. 検証と事前検査

| 段階 | 結果 |
|---|---|
| `make task-validate` | exit 0、WARN 0 件 |
| `make task-preflight` | **4 PASS / 4 SKIP / 0 FAIL** |

**SKIP は「合格」ではなく「実行されなかった」を意味する。** SKIP された 4 項目:
`P2 frozen_source_sha256`（spec に `frozen_source` が無い）、
`P3 denominator_resolvable`（`inputs.denominator` が無い）、
`P4 gpu_available`（全 phase が `gpu: false`）、
`P6 decisions_answered`（`decisions_required` が空）。

---

## 3. Phase A — 母集団と前提の確定（G1: pass）

| 項目 | 実測 |
|---|---|
| `runindex/index.csv` の行数 | **751** |
| 指すディレクトリが実在しない行 | **0 件**（`audit/missing_runs.txt` は空） |
| `runindex/experiments.csv` | **207** |
| `runindex/verdicts.csv` | **1038** |

G1 の検査「欠落が何件かを記録した」を満たす。欠落 0 は、751 行すべてについて
`Path(row["path"]).is_dir()` を評価した結果であり、対象の実在を件数で確かめている。

---

## 4. Phase B — データ実体の分割整合性（G2: pass）

### 4.1 起票者の走査は自明な 0 を返していた（重要）

SPEC の Phase B Step 1 は `Path.rglob` で画像を数えるが、**`rglob` はシンボリック
リンクのディレクトリを辿らない。** 動画ディレクトリは 15 本すべて symlink であり、
**指示どおり実行すると画像 0 枚・跨ぎ 0 件が返る。** これを「分割は健全」と読むと、
何も測らずに健全と結論することになる。`find -L` と `os.walk(..., followlinks=True)`
の 2 系統で測り直した。以下はすべて測り直した値である。

### 4.2 分割の実体

| split | 動画数 | 画像数 | 検出注釈 |
|---|---|---|---|
| train | 10 | **9657** | 9657 画像 / **32272** 注釈 |
| val | 2 | **1515** | 1515 画像 / **4707** 注釈 |
| test | 3 | **4265** | 4265 画像 / **12673** 注釈 |

- 総 `frame_id` **15437** = 9657 + 1515 + 4265（**厳密一致**）
- **split を跨ぐ重複 0 件。** 動画 ID の重なりも 0（集合演算とソート突合の 2 系統で一致）
- `data/splits/ego_{train,val,test}.txt` は動画 ID の一覧（10 / 2 / 3 行）であり、
  実体との**集合差は両方向とも 0**
- 検出注釈の内部重複 0 件、split 対ごとの重なり 0 件

### 4.3 陽性対照（G2 の検査）

重複検査に、既存の `frame_id` を 1 件複製した入力を与えた。
**期待「1 件検出」に対し、実測も 1 件検出。** 検査が空振りしていないことを確認した。

---

## 5. Phase C — 工程ラベルの母集団

| 項目 | 実測 |
|---|---|
| CSV 本数 / 動画 ID 数 / 総行数 | 23 本 / 15 / **17233** |
| 語彙の項目数 | 9 |
| `PHASE_NAME_TO_ID` との集合差 | **両方向とも空** |
| `_build_frame_index` の件数 | **15437**（Phase B と一致） |
| 語彙外のラベル | **0 件** |
| 画像が存在しない行 | **1796** |
| split 別の採用数 | train **9657** / val **1515** / test **4265** |
| phase と tool の包含 | phase 17233 ⊃ tool 15437。tool のみ 0 件 / phase のみ **1796** 件 |

工程ラベルの採用数が Phase B の分割と**完全に一致**している。差の 1796 は
「注釈はあるが画像が無い行」であり、包含関係の差と厳密に一致する。

---

## 6. Phase D — 評価条件の記録と照合の実効性（G3: pass）

### 6.1 走査対象の根と母数

`experiments` だけを根と呼ばないこと、という SPEC の指示に従い根を実測した。
**根は `experiments` と `transfer` の 2 つ。** `metrics.json` は **722 件**、
うち `eval_recipe` を持つものが **550 件**。

### 6.2 記録されている split サイズ

| 区分 | 件数 | `split_train_images` |
|---|---|---|
| 工程（`test_cfg.task == "phase"`） | **503** | **全件 9657** |
| 検出（それ以外） | **47** | 9657 が 44、**0 が 3** |

- 公式値 `(9657, 1515, 4265)` と異なるのは **3 件**（`audit/nonofficial_split.txt`）
- `train` が 0 の 3 件はすべて
  `experiments/baselines/_legacy_score_thr_0/s0_00{7,8,9}_codetr_bbox_seed*`

### 6.3 照合関数の実挙動（G3・本 task の中心）

`recipes_match` の実装を先に読んだ。**起票者の記述「split サイズの一致を見る」は
不完全である。** 実装が見るのは (a) `test_cfg` の実効キー全て（`description` と
`note` のみ除外）、(b) split の train/val/test images、(c) `gpu_count` と
`effective_batch_size` の 3 系統であり、`server_name` の差は警告のみで判定に影響しない。

| 照合 | 実測 | 期待 |
|---|---|---|
| 公式 と 公式 | `True` | True |
| **ゼロ と ゼロ** | **`True`** | 要観察 |
| 公式 と ゼロ | `False` | False |
| 公式 と 誤分割 | **`False`** | False |

**「公式 と 誤分割」が `False` を返したため、照合そのものは機能している。G3 は停止しない。**

**「ゼロ と ゼロ」は `True` を返した。起票者の疑いは仕組みとして実在する。**
ただし実データでの発火は上記 codetr の 3 run のみで、しかも 3 件は同一実験
（`baselines/s0/codetr_bbox@val`）に属する。**工程側の該当は 0 件である。**
「公式 と ゼロ」が `False` を返すため、この 3 件が公式値の run と誤って一致することはない。

### 6.4 工程側が実際に記録しているもの

| 項目 | 分布（503 run） |
|---|---|
| `split_train_images` | 9657: 503 |
| `tc_inference_protocol` | `online_causal`: 503 |
| `tc_jaccard_mode` | `strict`: 503 |
| `server_name` | lecun 333 / efros 167 / philip 3 |

**工程側の評価条件は完全に均質である。** しかしその均質さの出所を確かめると、
検証機構が働いた結果ではなかった。

- `phase_trainer._build_eval_recipe`（`src/egosurgery/engines/phase_trainer.py:293-311`）は
  「ann_file 経由で split サイズを実測（捏造防止）」と書かれており、読めなければ
  `except: pass` で **`{"images": 0, "annotations": 0}` に落ちる**。
- その `ann_file` は `configs/stage/s4_phase_baseline.yaml:97-103` で
  `data/annotations/egosurgery_phase/instances_{train,val,test}.json` を指すが、
  **この 3 ファイルは存在しない**（設定にも「暫定プレースホルダ / TODO」と書かれている）。
- 実際に 503 run を生成した `scripts/train_s4_tecno.py:168` `train_b2a.py:206` 等は、
  `split_sizes=PAPER_SPLIT_SIZES`、すなわち
  `src/egosurgery/utils/eval_recipe.py:84-88` の**定数を渡している**。

**したがって工程 503 run の 9657 は実測値ではなく定数の転記である。**
分割を取り違えて学習しても、この値は 9657 のまま記録される。
**工程側では `recipes_match` の split 比較は原理的に常に `True` になる。**

### 6.5 検出側は評価条件が 2 系統に分かれている

| 項目 | 分布（47 run） |
|---|---|
| `tc_score_thr` | `1e-08`: 14 / `0.0`: 30 / 空: 3 |
| `tc_nms_pre` | `3000`: 14 / 空: 33 |
| `tc_nms_iou` | `0.6`: 14 / 空: 33 |
| `tc_max_per_img` | `300`: 44 / 空: 3 |

`LOCKED_DOWN_TEST_CFG` は `score_thr = 1e-8` を定めている（§15.3 G1、
「mmdet default 0.05 と論文 1e-8 の乖離」の再発防止として導入されたもの）。
**`0.0` の 30 件はこの規約と異なる。**

**ディレクトリ名と中身が両方向で食い違っている:**
- `_legacy_score_thr_0` の中に `score_thr = 1e-08` の run が 3 件ある（codetr）
- `_legacy_score_thr_0` の外に `score_thr = 0.0` の run が 3 件ある（maskdino_nmsfree）

### 6.6 対照ペアの照合

`runindex/experiments.csv` の `control_of` が対照を名指しする組は **136 件**。
`experiment_id` から `index.csv` 経由で run のパスを引き、双方の `eval_recipe` を
`recipes_match` に通した。**引けない組は 0 件。**

| 結果 | 件数 |
|---|---|
| 一致 | **0** |
| 不一致 | **136** |

**この 136 件を「評価条件の不一致」と読んではならない。** 差分キーを実効比較キーの
全てで取り直したところ、原因は以下に限られていた:

| 原因キーの組み合わせ | 件数 |
|---|---|
| `coupling` / `in_dim` / `tool_signal_dim` | 80 |
| `coupling` / `in_dim` / `region_dim` | 41 |
| `coupling` / `hand_feature_dim` / `hand_source` / `in_dim` / `with_tool` | 6 |
| その他（`temporal_*` / `num_layers` 等を含む 5 通り） | 9 |

**すべて `test_cfg` に格納されたモデル構造パラメータである。**
**split サイズと GPU 構成のキーは、136 件のどれにも差分として現れなかった。**

実験群と対照群は定義上モデル構造が異なる。その構造が評価条件と同じ dict に
入っているため、**`recipes_match` は注入対照ペアに対して構造的に必ず `False` を返す。**
つまりこの照合は、対照ペアの「評価条件が揃っているか」の検査としては使えない。

### 6.7 照合は実運用の Δ 集計を通っていない

- `recipes_match` を呼ぶのは `src/egosurgery/metrics/delta.py:265` のみで、
  不一致なら `InconsistentRecipeError` を送出して Δ 計算を止める。
- `DeltaCalculator` の呼び出し元は `src/egosurgery/engines/trainer.py:381`、
  すなわち**学習時の経路**である。
- **`tools/harvest_runindex.py` は `recipes_match` を一切呼ばない。**
  `eval_recipe_id`（recipe のハッシュ）を計算し、
  同一 `(group, step, description, split)` 内で食い違う場合に
  `experiment_id` を `#<hash>` で**分離する**（`tools/harvest_runindex.py:1366-1383`）。

**`experiments.csv` の `delta_*` 列は照合を通らずに算出されている。**
分離規則は同一 `description` 内でしか働かないため、**検出器が違えば
`description` も違い、分離は起きない。**

### 6.8 退避ディレクトリの除外状況（BL-exclusion-rules-exact-match の実測）

アンダースコア始まりのディレクトリは **45 件**。`index.csv` に行を持つのは 12 件。

| ディレクトリ | index | 除外 |
|---|---|---|
| **`experiments/baselines/_legacy_score_thr_0`** | **33** | **0** ← 除外されていない |
| `experiments/_smoke_prior` | 6 | 6 |
| `experiments/baselines/_wrong_split_8_2_3` | 6 | 6 |
| `experiments/phase0/_failed_s3_weighted`（+ 配下 3） | 6 + 3 | 6 + 3 |
| `experiments/hand2det_dev/_identity_*`（18 件） | 各 1 | 各 1 |
| `experiments/transfer/_p0_identity_*`（6 件） | 各 1 | 各 1 |
| `experiments/baselines/_smoke_ddq` | 1 | 1 |

index 全体の `excluded` は True 48 / False 703。
**退避ディレクトリのうち除外されていないのは `_legacy_score_thr_0` の 33 件だけである。**
`exclusion_reason` も 33 件すべて空。

**混入の有無を測った結果は、起票者の想定とは違っていた。**
退避配下の 11 個の `experiment_id` は、いずれも**退避外に同名が存在しない**
（混在 0 / 11）。したがって「同一実験の中で新旧の run が混ざる」形の混入は**起きていない**。

代わりに起きているのは別の形である。**この 9 検出器の唯一の記録が退避配下にあり、
それが `experiments.csv` に集約されて S0 の比較表を構成している。**

| experiment_id | n_runs | 除外 | mAP_mean | eval_recipe_id |
|---|---|---|---|---|
| `baselines/s0/relationdetr_bbox@val` | 3 | 0 | 0.726794 | `b66459018a92` |
| `baselines/s0/stabledino_bbox@val` | 3 | 0 | 0.719194 | `1cf2eece1cd3` |
| `baselines/s0/dimaskdino_bbox@val` | 3 | 0 | 0.385275 | `1cf2eece1cd3` |
| `baselines/s0/focusdetr_bbox@val` | 3 | 0 | 0.699119 | `1cf2eece1cd3` |
| `baselines/s0/aligndetr_bbox@val` | 3 | 0 | 0.713279 | `1cf2eece1cd3` |
| `baselines/s0/mrdetrdino_bbox@val` | 3 | 0 | 0.722314 | `1cf2eece1cd3` |
| `baselines/s0/mrdetralign_bbox@val` | 3 | 0 | 0.719462 | `1cf2eece1cd3` |
| `baselines/s0/dacdetr_bbox@val` | 3 | 0 | 0.716467 | `e82672cdfc7d` |
| `baselines/s0/codetr_bbox@val` | 3 | 0 | 0.697333 | `857cd0f5a5da` |
| `baselines/s0/ddq_bbox@val` | 3 | — | 0.718667 | `a63aecae1158` |
| `baselines/s0/sensex_codino_bbox@val` | 1 | — | 0.718000 | `4c38a4a7853f` |

**S0 の比較表は少なくとも 6 種類の `eval_recipe_id` に跨っている。**
上位 7 検出器の mAP は 0.6973〜0.7268 の範囲に収まっており、**その幅（約 0.03）は
評価条件の系統差と分離できていない。**

`baselines/s0/maskdino_bbox@val` と `baselines/s0/varifocanet_bbox@val` は
この `experiment_id` では `experiments.csv` に存在しなかった。別名で集約されているか
集約対象外かは本 task では特定していない（`UNKNOWN`）。

---

## 7. Phase E — 評価手順の構造的な偏り

### 7.1 最良 epoch の選び方と報告 split（実装から確定）

| 側 | 最良 epoch の選択指標 | 実装位置 |
|---|---|---|
| 検出 | **`val/mAP` の最大** | `src/egosurgery/engines/mmdet_trainer.py:611`（`max(records, key=lambda r: r.get("val/mAP", -1.0))`）。`stage_a_trainer.py:338` と `trainer.py:141` も `monitor="val/mAP"` |
| 工程 | **val の `phase_accuracy` の最大** | `src/egosurgery/engines/phase_trainer.py:190`、`scripts/train_s4_tecno.py:263` |

**両側とも検証 split で最良 epoch を選び、主たる報告値も検証 split の値である。**
試験 split は `--eval-test` 指定時に「val で選んだ最良モデル」を評価して
`test_*` として追記する形であり（`scripts/train_s4_tecno.py:271`）、
**選択と報告が同じ split の上で閉じている。** 検証側の値は楽観方向に偏る。

### 7.2 検証側と試験側の乖離の母数

| 項目 | 実測 |
|---|---|
| `runindex/anomalies/val_test_pairs.csv` | 70 行（ヘッダ込）= データ **69 行** |
| `index.csv` で `has_test == True` の run | **69** |

**一致する。** 乖離の集計はこの 69 run の上で行われている。
`index.csv` の解析対象 703 run に対し、**試験側の値を持つのは 69 run（約 9.8%）**である。

---

## 8. 結論 — 既存の基準点をそのまま論文の数値として使えるか

### 8.1 そのまま使える範囲

- **データ分割そのもの。** 9657 / 1515 / 4265 は実体と厳密に一致し、split を跨ぐ
  重複は 0 件、動画 ID の重なりも 0 件である（陽性対照つきで確認済み）。
  **分割の取り違えによる基準点の汚染は生じていない。**
- **工程ラベルの母集団。** 語彙外 0 件、split 別採用数が分割と完全一致。
- **工程側 503 run 相互の比較。** 推論手順（`online_causal`）と厳密性（`strict`）が
  503 件すべてで同一であり、評価条件の面では比較可能である。
  ただし split サイズの一致は 8.3 のとおり検証の結果ではない。

### 8.2 そのままでは使えない範囲

1. **S0 の検出器比較表。** 9 検出器が 6 種類の `eval_recipe_id` に跨り、
   `score_thr` が `1e-08` と `0.0` の 2 系統に分かれている。
   検出器間の mAP の差（約 0.03 の幅）を**検出器の優劣として報告できない。**
2. **codetr の値。** 3 run すべてが `split_train_images = 0` で記録されている。
   照合はゼロ同士で `True` を返すため、**この 3 件は互いに照合を素通りする。**
3. **`_legacy_score_thr_0` の 33 run。** 除外されておらず（`exclusion_reason` も空）、
   解析対象 703 件に含まれ、9 検出器の集約値を構成している。

### 8.3 数値は正しいが、正しさの根拠が記録に無い範囲

工程 503 run の `split_train_images = 9657` は**定数 `PAPER_SPLIT_SIZES` の転記**である。
値そのものは Phase B の実測と一致するため**誤ってはいない**。
しかしこれは検証を通った結果ではなく、**分割を取り違えても同じ値が記録される。**
「記録が一致しているから分割も一致していた」とは言えない。
今回は Phase B / C で実体を直接測ったため、**実体の側から一致が確認できている。**

---

## 9. 再取得に要する対象と規模

| 対象 | 規模 | 内容 |
|---|---|---|
| S0 検出器の再評価 | **9 検出器 × 3 seed = 27 run** | `LOCKED_DOWN_TEST_CFG`（`score_thr = 1e-8` / `nms_pre = 3000` / `nms_iou = 0.6` / `max_per_img = 300`）で統一して再評価 |
| codetr | 上記 27 run に含む | 併せて split サイズが実測で記録されること |

**再評価だけで足りるか（学習の再実行が要るか）は、対象 27 run の checkpoint が
現存するかに依存する。本 task は読み取りのみのため確認していない（`UNKNOWN`）。**
学習不要なら再評価のみ、必要なら 27 run の再学習となり規模が大きく変わる。

---

## 10. 起票者の推測のうち、実測で裏づけられたもの・否定されたもの

### 裏づけられた

| 推測 | 実測 |
|---|---|
| 「工程側の split には検証機構が無い」 | **その通り。** ただし理由は起票者の想定と異なる（下記） |
| 「記録された split サイズがゼロのまま照合を素通りしている恐れ」 | **仕組みとしては実在。** ゼロ同士は `True` を返す |
| `BL-exclusion-rules-exact-match`（除外規則の取りこぼし） | **実在。** `_legacy_score_thr_0` の 33 件が除外されていない |

### 否定された

| 推測 | 実測 |
|---|---|
| 分割の実体が定義と食い違っている可能性 | **否定。** 実体・注釈・split 定義ファイルが三重に厳密一致 |
| 「`recipes_match` は split サイズの一致を見る」 | **不完全。** `test_cfg` 実効キー全比較と GPU 構成も見る。SPEC 自身が「実装を読まずに書いた」と断っており、実装に従った |
| ゼロ素通りが工程側の問題である | **否定。** 工程側は 0 件。該当は検出側の codetr 3 件のみ |
| 退避 run が同一実験に混入している | **否定。** 混在 0 / 11。問題は混入ではなく「唯一の記録が退避配下にある」こと |

### 起票者が想定していなかった発見

1. **工程側の 9657 は定数の転記である**（§6.4）。実測経路は config の
   `ann_file` が実体の無いプレースホルダで、通っていない。
2. **`recipes_match` は注入対照ペアに対して構造的に常に `False` を返す**（§6.6）。
   独立変数であるモデル構造が評価条件と同じ dict に入っているため。
3. **実運用の Δ 集計は照合を通っていない**（§6.7）。照合は学習時経路のみ。
4. **S0 比較表が 6 系統の評価条件に跨っている**（§6.8）。これが本 task で見つかった
   最も影響の大きい事象である。

---

## 11. 判断が要る事項

**本 task は読み取りのみであり、以下はいずれも決めていない。**

1. **S0 比較表をどうするか。** (a) 27 run を統一条件で再評価する、
   (b) 論文から S0 の検出器横断比較を落とす、(c) 評価条件の差を明記して載せる。
2. **`_legacy_score_thr_0` の 33 件を `excluded` にするか。**
   除外すると 9 検出器の記録が索引から消える（唯一の記録であるため）。
   `runindex/` と `tools/harvest_runindex.py` は本 task の禁止事項であり触れていない。
3. **`test_cfg` にモデル構造を入れる設計を続けるか。**
   続けるなら `recipes_match` は対照ペアの検査に使えないことを規約に明記する必要がある。
4. **工程側の split サイズを実測経路に戻すか。**
   `configs/stage/s4_phase_baseline.yaml` の `ann_file` を実体のある manifest に
   置き換えるか、定数転記であることを規約として認めるか。

---

## 12. escalate_if の該当

spec の `governance.escalate_if` 3 項目のうち、**第 2 項が部分的に該当する。**

> 「評価条件の照合が素通りしていたことが確認され、既存の差分の妥当性が崩れる場合」

- **照合の素通りは確認された**（ゼロ同士 `True`、実運用の Δ 集計は照合を通らない）。
- ただし **Δ（注入 − 対照）の妥当性そのものは崩れていない。**
  136 の対照ペアで split と GPU 構成は 1 件も食い違っておらず、
  不一致の原因はすべて実験の独立変数だった。
- **崩れるのは Δ ではなく S0 の検出器横断比較である。** これは Δ ではなく
  基準点の絶対値どうしの比較であり、照合の対象外だった。

第 1 項（分割の実体の食い違い）と第 3 項（変更なしでは測れない項目）は**該当しない**。

---

## 13. deviations（逸脱）

1. **`conventions_rev` を UNKNOWN から `d422b08` に置いた。**（judgement）
   spec には起票時の値が入っていなかった。原文を引くには版が要るため、
   `context/conventions.md` の現在の commit を実測して用いた。
2. **Phase B Step 1 の走査方法を変えた。**（spec_defect）
   SPEC の `Path.rglob` は symlink を辿らず画像 0 枚を返す。
   `find -L` と `os.walk(followlinks=True)` の 2 系統で測り直した。
   **指示どおり実行していれば「分割は健全」と誤って結論していた。**
3. **Phase D Step 5 の照合を自分で実装した。**（judgement）
   SPEC は列の存在確認までしか書いていない。`experiment_id` → `index.csv` →
   run パス → `metrics.json` の経路を組んだ。
4. **一度出した「136 件不一致」の解釈を訂正した。**（judgement）
   最初は差分キーを 5 個に絞って表示したため原因が見えず、評価条件の不一致と
   読みかけた。`recipes_match` の実装を読み、実効比較キーの全てで取り直した結果、
   原因はモデル構造パラメータだと判明した。**SPEC の「実装を先に読むこと」に
   従っていれば最初から避けられた。**
5. **`data/annotations/egosurgery_phase/instances_train.json` の不在を、
   そこで止めずに追跡した。**（spec_defect）
   SPEC は `ls` して「存在しない」と出すだけで、その意味を問うていない。
   不在は工程側 503 run の 9657 の出所という核心に直結していた。
6. **文脈が上限に達したため、作業を中断して再開した。**（environment）
   Phase D Step 4 の直前で圧縮した。`audit/` の実測ファイルと作業ツリーが
   残っていたため、測り直さずに再開できている。**再開後に再測した値は無い。**

---

## 14. 生成物

`tasks/T-2026-08-11-split-and-recipe-audit/audit/` 配下:

| ファイル | 内容 |
|---|---|
| `missing_runs.txt` | 実在しない run（空 = 0 件） |
| `split_entity.txt` / `split_entity_recheck.txt` / `split_entity_b234.txt` | 分割実体の測定と再確認 |
| `phase_entity.txt` | 工程ラベルの母集団 |
| `eval_recipe.csv` | 722 件の `metrics.json` から抽出した評価条件（106 KB） |
| `nonofficial_split.txt` | 公式値と異なる 3 件 |
| `g3_recipes_match.txt` | G3 の 4 ケース |
| `control_pair_mismatch.txt` | 136 の対照ペアと不一致の原因キー |
