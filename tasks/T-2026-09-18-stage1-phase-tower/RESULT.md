# 参照解決記録 — T-2026-09-18-stage1-phase-tower

完了。P\*-15 の三候補トーナメント 70 run を五折りで回し、val だけで recipe を確定し、確定塔の test を折りごとに一度だけ評価した。**P\*-21 は UNKNOWN**（追加 6 動画の画像が本ホストに無く、未測定）。

## 1. 解決された参照

- `context/conventions.md` 最終更新 commit: `e7a5100597a79b3b9c60935bf38d232f8ae96822`
- `runindex/experiments.csv` 最終更新 commit: `96eb3a1ca20ab7eb4b373d93304c9e6b33b733d5`

分母の実験 ID 完全一致は 1 件。以下は索引の値をそのまま転記。

```json
{
  "experiment_id": "phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42",
  "split": "val",
  "n_runs": "17",
  "n_seeds": "3",
  "seeds": "42,123,456",
  "runs_per_seed_max": "7",
  "accuracy_mean": "0.8973014948553679",
  "accuracy_pstd": "0.005917073407586465",
  "jaccard_mean": "0.6321606095182377",
  "jaccard_pstd": "0.021544225014892025",
  "jaccard_sstd": "0.022357498898394404",
  "jaccard_n": "14"
}
```

指定された phase_jaccard_mean 列は存在しない。jaccard との対応は未確定。契約本文の Jaccard 0.6447 ± 0.0146 と索引値は不一致。17 run の集計を 3 seed の独立な集計とはみなしていない。


<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |



<a id="issuer_cautions"></a>
## issuer_cautions

**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 4 | 仕組みの挙動は実装を読んでから信じる |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
| 7 | **丸めた表示を実数として扱わない** |
| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
| 11 | 測定の副作用が禁止領域へ触れないか確かめる |
| 12 | **判断の前に、いま見ているものが最新かを確かめる** |
| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。



<a id="folds"></a>
## folds

動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-18-fold-table` が確定）。
本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。

| 折り | test（3） | val（2） |
|---|---|---|
| A | 04, 05, 07 | 09, 10 |
| B | 01, 03, 14 | 02, 08 |
| C | 02, 08, 11 | 06, 12 |
| D | 06, 13, 15 | 04, 05 |
| E | 09, 10, 12 | 07, 15 |

train はその折りの test と val を除いた 10 本である。
**折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。
各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。

### 追加 6 動画

工程塔 P\*-21 は上の 15 動画に次の 6 動画を足す。

    17, 18, 19, 20, 21, 22

**用途は訓練のみである。どの折りの test にも val にも現れない。**
15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。

### 規律

**選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
test は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。

出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-18-fold-table`。


<a id="split"></a>
## split

論文準拠 split の動画 ID は次のとおり。

- train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
- val: `09`, `10`
- test: `04`, `05`, `07`

転記元: `data/splits/ego_train.txt`, `data/splits/ego_val.txt`, `data/splits/ego_test.txt`。
実装側の対応値は `src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS`。



<a id="eval_recipe"></a>
## eval_recipe

転記元: `src/egosurgery/utils/eval_recipe.py`。

- `LOCKED_DOWN_TEST_CFG`: `score_thr=1e-8`, `max_per_img=300`, `nms_pre=3000`, `nms_iou=0.6`
- `NMS_FREE_TEST_CFG`: `score_thr=0.0`, `max_per_img=300`, `nms_pre=None`, `nms_iou=None`
- `PHASE_EVAL_PROTOCOL`: `inference_protocol=online_causal`, `jaccard_mode=strict`

比較の三角形および DETR-family の公式評価は NMS-free とする。工程評価は online causal と Jaccard strict を固定する。`select_box_nums_for_evaluation` は転記元で定義されていないため `UNKNOWN（転記元未特定）`。



<a id="sigma"></a>
## sigma

sigma に関する列は 4 系統ある（backlog B-18）。

1. `{metric}_pstd` / `{metric}_sstd` — seed 間の sigma（母集団 / 標本）
2. `delta_pstd_{metric}` / `delta_sstd_{metric}` — 実験間 paired Delta の sigma
3. `sigma_source` — sigma の系統。値は paired_delta または within_run_seed_spread
4. `delta_sigma_source` — paired sigma の計算方法。値は paired または unpaired_pooled

3 と 4 は直交する（どの sigma を使ったか vs paired sigma をどう計算したか）。

### 既定値（spec.yaml が sigma_policy を省略した場合に継承される値）

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

この既定は暫定である。正本（ddof=0 / ddof=1）は未決定であり、
決定され次第ここを変更する。変更時は過去の task を横断で再判定できるよう、
`RESULT.md` に解決済み sigma_policy が記録されていることを前提とする。

### 判定規約の表記

判定規約を `spec.yaml` や `prereg.md` に書くときは、絶対値を `abs(...)` の関数形で書く。
縦線による絶対値記法は markdown 表のセル区切りと衝突し、表を壊すため使わない
（backlog B-33 と同型の事故）。

    正: abs(delta) / sigma >= 1 かつ 全 seed 同符号
    誤: 縦線で delta を囲む記法

同じ理由で、区切りを表したいときは `/` かスラッシュ区切りの語を使う。



## 逸脱・未解決

L2 の起票時件数 0 に関する WARN は利用者が続行を了承。参照解決時に数値の不一致を確認したため、分母の採用値は変更していない。spec.yaml の占位・事前登録は未変更。

## 事前登録と利用者回答

事前登録 commit: `1e586cf9672fb509d7c3704bb0a3c27cab2adf95`。時刻: `2026-09-18T00:31:50+09:00`（JST）。学習開始前に prereg.md のみを commit した。

利用者回答による条件分岐の確定。追加6動画が使えない場合はP*-15だけで進め、P*-21はUNKNOWNとする。Stage 2の主分母P*-21のため追加6動画を使えるようにする別契約が必要と報告し、P*-15のトーナメントで選んだrecipeをP*-21にも適用する。最良と次点がseed間SD以内かつ所要時間も同程度なら単純な構成を優先し、候補A > C > B、掃引点が同点なら受容野の短い方を選ぶ。Stage 2での解釈の容易さとW2の費用が理由。原契約の該当する停止条件・G1・選定規則に対する例外として適用する。

開始時点で `.sync-pause` は存在したため、新設・解除していない。

## L3 再検証

make task-preflight 終了コード 0。8 PASS / 0 WARN / 4 SKIP / 0 FAIL。P4・P6 は PASS。prereg.md の作業ファイルは記録した commit の内容とバイト単位で一致。

未実施: P2 cuda_ext_loaded（宣言なし）、P3 deterministic_flags（判定基準未確定）、P11 gpu_free（宣言なし）、P12 refs_resolved（unresolved: 形式の参照なし）。P12 SKIP は分母の意味的な解決を保証しない。

分母の索引と契約本文の数値の不一致は未解決。契約の escalate_if: denominator_moved に従い、学習を開始せず利用者判断を待つ。

## S4 参照調査の解決

旧3 run（001/002/003）の保存F1とGT存在クラスからJaccardを再構成し、平均 0.6447397621229328、pstd 0.011896230384401817、sstd 0.014569847152188916 を得た。契約の旧値を再現したため、S4参照にはこの3 runを採用する。索引の平均は後続14 runで再現し、集計対象が異なると確定。phase_jaccardの列名対応も正規化実装で解決。詳細は audit.md と s4_reference_audit.json。

追加6動画の注釈は実在するが探索範囲で画像は未発見。P*-21はUNKNOWNとし、追加画像を使えるようにする別契約が必要。利用者承認に従いP*-15のrecipeをP*-21にも適用する。材料検査は materials_audit.json。学習は未開始。

---

以下は学習・選定・test を実施したあとの追記である。上の「学習は未開始」「利用者判断を待つ」は
追記時点より前の状態を書いたものであり、書き換えない。分母の不一致は上の「S4 参照調査の解決」で
決着し、利用者承認のうえで学習へ進んだ。

## 2. Task B — 空間特徴の抽出

凍結 ImageNet-1K ResNet-50（torchvision `IMAGENET1K_V1`）の C5 GAP 2048 次元を 0.5 fps の全フレームで一度だけ抽出した。

| 項目 | 実測 |
|---|---|
| 一度目の要約値 | `63cd91453b76bc8f28118494893ec59ce369a2f0e1175335cf4d0bab21de2d81` |
| 二度目の要約値 | `63cd91453b76bc8f28118494893ec59ce369a2f0e1175335cf4d0bab21de2d81`（一致） |
| 重みの要約値 | `0676ba61b6795bbe1773cffd859882e5e297624d384b6993f7c9e683e722fb8a` |
| キャッシュの要約値 | `cb3761c467f737bbd8dff2f5f3ebd468631b000f79b77d9a2907050c58f2469c` |
| 大きさ | 127016156 バイト |
| フレーム数 | 15437（15 動画） |
| 所要 | 91.09361817780882 秒 |

**抽出は 15 動画のみ**である。追加 6 動画（17〜22）の画像が本ホストに無いため 21 動画分にはなっていない。
置き場は `data/processed/stage1_features/imagenet_r50_v1_stage1/all_gap.npz`。

陰性対照は 2 つとも働いた。重みを変えると要約値が変わった（`weight_change_detected: true`）。
manifest から 1 動画を消すと集合差 1 が出た（`removed_video_detected: true`）。証跡は
`experiments/phase1/stage1_ptower_001_imagenet_r50_v1_features_P15_seed42/feature_audit.json`。

## 3. Task C・D — 学習格子（判定 c の表）

10 構成 × 5 折り（折り A は seed 42/123/456 の 3 本、B〜E は seed 42 の 1 本）= **70 run** をすべて完走した。
値は折り内 val の macro Jaccard（online-causal、Jaccard strict）。折り A 列は 3 seed の平均。

| 候補 | 層 | 平滑化 | 履歴 | A | B | C | D | E | 5折り平均 J | 5折り平均 acc | 折りA seed間 pstd | 平均秒 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | 8 | 0.15 | 30 | 0.3811 | 0.2218 | 0.2358 | 0.3820 | 0.4432 | **0.33280** | 0.60851 | 0.09596 | 4.503 |
| C | 8 | 0.30 | 30 | 0.3669 | 0.2025 | 0.2400 | 0.3856 | 0.4496 | **0.32891** | 0.60566 | 0.01232 | 4.732 |
| B | 8 | 0.00 | 30 | 0.3485 | 0.2421 | 0.2930 | 0.3691 | 0.3623 | **0.32300** | 0.51005 | 0.01761 | 7.153 |
| B | 8 | 0.00 | 60 | 0.3274 | 0.2027 | 0.2515 | 0.3653 | 0.4320 | **0.31578** | 0.56926 | 0.00281 | 5.743 |
| C | 6 | 0.30 | 30 | 0.3622 | 0.1985 | 0.2607 | 0.3584 | 0.3902 | **0.31400** | 0.58674 | 0.03372 | 4.463 |
| B | 6 | 0.00 | 60 | 0.3742 | 0.2252 | 0.2659 | 0.3496 | 0.3445 | **0.31186** | 0.54027 | 0.01216 | 6.526 |
| A | 6 | 0.00 | 30 | 0.3310 | 0.2406 | 0.2525 | 0.3763 | 0.3370 | **0.30747** | 0.55974 | 0.05488 | 4.257 |
| C | 6 | 0.15 | 30 | 0.3282 | 0.2265 | 0.2474 | 0.3436 | 0.3808 | **0.30529** | 0.53346 | 0.06715 | 4.560 |
| A | 8 | 0.00 | 30 | 0.3463 | 0.1861 | 0.2630 | 0.3594 | 0.3623 | **0.30341** | 0.59389 | 0.02133 | 4.880 |
| B | 6 | 0.00 | 30 | 0.3570 | 0.2072 | 0.2727 | 0.3085 | 0.3708 | **0.30323** | 0.55305 | 0.02177 | 5.789 |

**この表は P\*-15 の 1 データ設定のみである。** 判定 c が求める「× 2 データ設定」の
P\*-21 側は UNKNOWN（追加 6 動画の画像が無く未測定）。

run ごとの値は `experiments/phase1/stage1_ptower/validation_runs.csv`（70 行）、
構成ごとの集計は同ディレクトリの `validation_recipes.csv`（10 行）。

所要時間は最長でも 1 run あたり数秒であり、停止条件「1 run が 1 時間を超える」には触れていない
（`run_stage1_ptower.py` が run ごとに `elapsed_seconds > 3600` を検査し、いずれも通過）。

### 対照（判定 g）

折り A・seed 42 で、同じ特徴・同じ折りの単フレーム線形分類を 1 件回した。

| 腕 | val macro Jaccard | val accuracy |
|---|---|---|
| 単フレーム線形 | 0.2249520391321694 | 0.48382838283828383 |
| 候補 A（6 層）折り A の最小 seed | 0.2591324981513034 | — |
| 候補 A（8 層）折り A の最小 seed | 0.32527680342996407 | — |

候補 A の折り A の 6 run（2 掃引点 × 3 seed）はすべて線形対照を上回った。最小の差は 0.0341804590191340。
停止条件「候補 A が単フレーム線形分類を下回る」には触れていない。証跡は `initial_gate.json`。

## 4. Task E — 選定と test

### 選定（判定 d）

事前登録 §6 の規則を `scripts/select_stage1_ptower.py` が機械で当てた。**規則は最初の適用で決着しなかった。**

1. 5 折り平均 val Jaccard 最大は C・8 層・平滑化 0.15（0.33280）、次点は C・8 層・平滑化 0.30（0.32891）
2. co-primary（accuracy）は同方向（0.60851 > 0.60566）
3. 差 0.003889677441420769 は最良の折り A seed 間 pstd 0.09595915486783717 **以内**
4. 所要時間 4.732185166927853 秒 / 4.503101239646120 秒 = 1.0509 で **±20% 以内（同程度）**
5. 2026-09-18 の修正条項の同点規則（候補 A > C > B、次に受容野の短い方）は、**両者が同一候補・同一受容野**のため決着しない

事前登録 §6.3（決まらなければ諮る）に従い停止して利用者に諮り、**平滑化 0.30 を確定**した
（2026-09-18 の修正条項）。以後の同点規則として「同一候補・同一受容野で残る同点は折り A の
seed 間 pstd が小さい方を採る」を置いた。理由は Stage 2 の送り手として再現性を優先するため。

**確定 recipe: 候補 C（平滑化損失）・8 層（受容野 1021 フレーム）・平滑化重み 0.30・履歴 30。**

選定に test は使っていない。根拠は 3 つある。
`validation_recipes.csv` の 19 列に test 由来の列が **0 列**である（列名に `test` を含む件数 0）。
`selection.json` の作成時刻 16:10:45 は、最初の test アクセス台帳 16:11:02 より **前**である。
学習経路 `stage1_ptower.train` は `load_fold(cfg)` を既定の `parts=("train","val")` で呼ぶため
test を読み込まない（実装で確認）。

### test（判定 e）

確定塔について折りごとに一度だけ評価した。台帳は `experiments/phase1/stage1_ptower/test_access_{A..E}.json`
（作成は `open("x")` で、二度目の評価は台帳の衝突で失敗する）。

| 折り | val J | val acc | test J | test acc | 元 run |
|---|---|---|---|---|---|
| A | 0.36689 | 0.66975 | 0.16759 | 0.61243 | `stage1_ptower_040_P15_C_L8_w0.3_h30_foldA_seed42` |
| B | 0.20246 | 0.51478 | 0.25233 | 0.41737 | `stage1_ptower_042_..._foldB_seed42` |
| C | 0.23998 | 0.63783 | 0.15608 | 0.49407 | `stage1_ptower_043_..._foldC_seed42` |
| D | 0.38561 | 0.51096 | 0.32592 | 0.64403 | `stage1_ptower_044_..._foldD_seed42` |
| E | 0.44960 | 0.69498 | 0.22168 | 0.55885 | `stage1_ptower_044_..._foldE_seed42` |
| 平均 | 0.32891 | 0.60566 | **0.22472** | **0.54535** | — |

test の macro Jaccard の折り間 pstd は 0.06162368547190434。
**test 評価は 5 回**（P\*-15 の 5 折りのみ）で、上限 10 回を超えていない。P\*-21 は塔が無いため 0 回。

### 折り A と Stage 0 の S4 の並置（判定 f、判定には使わない）

| 塔 | 特徴の出所 | 折り A val J | 折り A val acc | 折り A test J |
|---|---|---|---|---|
| S4 凍結工程塔（Stage 0） | Relation-DETR backbone | 0.6447397621229328 ± 0.011896230384401817（3 seed、pstd） | 0.8985698569856986 | 未評価 |
| 本契約の P\*-15（確定塔） | 凍結 ImageNet-1K R50 | 0.3668916054250826（3 seed 平均、pstd 0.012320789810365542） | 0.6697469746974698 | 0.16758590262489526 |

S4 の出所は `runindex` の実験 ID `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`
のうち **当初 3 run（001/002/003）**であり、索引の 17 run 集計（Jaccard 0.6321606095182377）とは
集計対象が異なる。差の内訳は `audit.md` と `s4_reference_audit.json` にある。

**差は 0.2779 で大きい。** 本契約はこの比較を判定に使わない（事前登録 §4-5 のとおり記録のみ）。

## 5. 事前登録 §4 の予測の当たり・外れ

| # | 予測 | 判定 | 実測 |
|---|---|---|---|
| 1 | 候補 A が 5 折り平均 val Jaccard で最良 | **外れ** | A の最良 0.30747 は 10 構成中 **7 位**。最良は候補 C の 0.33280 |
| 2 | 候補 B は A より低い | **外れ** | B の最良 0.32300 > A の最良 0.30747。B の 4 構成の平均 0.31347 も A の 2 構成の平均 0.30544 を上回る |
| 3 | 候補 C は A との差が折り A の seed 間 SD の内側 | **当たり** | 差 0.0253246571186177 < A（6 層）の折り A seed 間 pstd 0.054876786293487245 |
| 4 | P\*-21 は P\*-15 より高い | **UNKNOWN** | 追加 6 動画の画像が本ホストに無く、P\*-21 を学習していない |
| 5 | 折り A の P\* は S4 より低いか同程度 | **当たり** | 0.36689 < 0.6447（低い） |

外れ 2 件は「ImageNet 凍結特徴の上では時間ヘッドの序列が S4 の検出 backbone 特徴の上と同じにならない」
ことを示す。特に予測 2 の根拠にした同ドメインの否定例（Trans-SVNet 23.1 < TeCNO 27.3）は、
本設定（凍結 ImageNet 特徴・0.5 fps・15 動画・5 折り）では再現しなかった。
`tasks/lessons.md` への教訓として `tasks/inbox.d/` に記録する。

## 6. 完了判定 a〜i

| # | 判定 | 結果 | 実測と空振りでないことの確認 |
|---|---|---|---|
| a | 特徴抽出が一度、決定的 | **部分**（21 動画分は未達） | 二度の要約値が一致。フレーム数 15437 が manifest と一致。陰性対照 2 件がともに検出。**追加 6 動画は画像が無く抽出できていない** |
| b | 全 run が折り表に従う | **達成** | 71 train run（70 格子 + 線形対照 1）の train・val・test 集合が規約の表と集合差 0。陽性対照として 1 run の test を 07→11 に差し替えると差が出た |
| c | 候補 × 掃引点の表 | **部分** | 10 構成 × 1 データ設定の表を §3 に置いた。折り A は 3 seed の平均と pstd つき。**P\*-21 側は UNKNOWN** |
| d | 選定が一意で test を使わない | **達成** | 規則を機械で当てて 1 構成。表の 19 列に test 由来の列は 0 列。selection.json は test 台帳より前に作成 |
| e | test は確定塔のみ折りごとに一度 | **部分** | 評価 5 回、台帳 5 件。学習経路は test を読まない（実装で確認）。**P\*-21 分の 5 回は未実施** |
| f | 折り A と S4 の並置 | **部分** | val は両方、test は P\*-15 のみ（S4 の test は未評価）。S4 の出所の実験 ID を明記 |
| g | 単フレーム線形の対照 | **達成** | 対照 0.22495 に対し候補 A の折り A 6 run すべてが上回る。最小の差 0.03418 |
| h | task_id の刻印と収穫 | **達成** | `make runindex` で index.csv 1267→1339 行（+72 = 71 train + 1 extract）、experiments.csv 286→339 行（+53）。task_id を持つ行は 72 件 |
| i | PR | **達成** | PR #183。実測で `draft=false` `base=phase0` `head=feat/stage1-phase-tower` `state=OPEN`。commit `92508ff4` |

**a・c・e・f の未達は、いずれも追加 6 動画の画像が本ホストに無いことに由来する。**
数値を補わず UNKNOWN のままにした。

## 7. 検証

| 検査 | 結果 |
|---|---|
| `make task-validate` | exit 0。WARN 3 件は L2-8（起票時件数 0 → 現在、分母が動いた）で、開始時に利用者が続行を了承済み |
| `make forbidden-check TASK=...` | exit 0、status pass。773 変更中 672 件が宣言による許可、違反 0 件 |
| `make spec-check TASK=...` | exit 0、status pass。8 規則、hits 0 |
| 試験 | 開始前 6 失敗 / 536 通過（`origin/phase0` の worktree で実測）→ 終了後 6 失敗 / 557 通過。**失敗は増えていない**。失敗 6 件は同一（test_engines 1 / test_fetch_task 1 / test_research_logger 4）。本契約で追加した 7 件はすべて通過 |
| `make runindex` | 新実験 53 行が現れた |

## 8. 逸脱

**逸脱は 6 件ある。「なし」ではない。**

1. **判断** — 選定規則が最後まで決着しなかった（§4）。事前登録 §6.3 に従い停止して利用者に諮り、
   平滑化 0.30 を確定した。規則を先に `spec.yaml` の修正条項と `select()` に置いてから機械で当て直した。
   結果を見たあとに規則を足しているため、**この同点規則は事前登録されていない**。
   ただし当てた対象は val だけで、test は選定後に一度だけ触っている。
2. **契約の誤り** — `contract.allow_write` が無く、契約が求める `make forbidden-check` が
   契約自身の出力（`experiments/phase1/` と `make runindex` の再生成）で必ず落ちた。
   `["experiments/phase1/stage1_ptower", "runindex/"]` を宣言して通した（§7）。
3. **環境** — 追加 6 動画（17〜22）の画像が本ホストに無く、**P\*-21 を一切学習していない**。
   契約の 140 run のうち実施は 70 run。利用者承認済みの例外（2026-09-18 の修正条項）。
   Stage 2 の主分母 P\*-21 のためには、追加 6 動画の画像を使えるようにする**別契約が要る**。
4. **判断** — 分岐は開始時点から `feat/stage1-phase-tower` であり、`phase0` を起点にしていない。
   原契約の Task A-1 が求める「HEAD が phase0」を満たしていない。PR の base は `phase0` にする。
5. **判断** — 本ファイルの前半（「学習は未開始」「利用者判断を待つ」）は追記時点より前の状態を
   書いたものだが、**書き換えずに残した**。時系列の記録を壊さないため。§2 以降が現在の状態である。
6. **判断** — 本契約で `select_stage1_ptower.py` の同点規則と、それを覆う試験 1 件を追加した。
   契約は Task E を「規則を機械で当てる」としか書いておらず、実装の追加は実行者の判断である。

## 9. 起票者の誤り

1. **check_does_not_check** — 契約は `outputs.destination` を `experiments/phase1/stage1_ptower/` に置き、
   Task F で `make runindex` と `make forbidden-check` の両方を求めているのに、`contract.allow_write` を
   宣言していない。指示どおり実行すると、契約自身が作った 672 件の出力が「禁止領域の内側」として
   違反に数えられ、`make forbidden-check` が status fail・違反 672 件で落ちる。
2. **self_contradiction** — 完了判定 c は「表の行数 = 10 構成 × 2 データ設定」を求めるが、
   同じ契約の 2026-09-18 の修正条項が「追加画像未発見の例外により学習格子は 70 run」「P\*-21 は UNKNOWN」と
   確定している。指示どおり実行すると判定 c は原理的に達成できず、判定 a・e・f も同じ理由で部分達成になる。
3. **asserted_without_measuring** — 契約 §2 は S4 の分母を「val Jaccard 0.6447 ± 0.0146」と
   「確定した事実」として書いたが、同じ実験 ID を `runindex` で引くと 0.6322 ± 0.0215 が返る。
   指示どおり実行すると分母の照合が食い違って止まる。調査の結果、前者は当初 3 run、後者は後続 14 run の
   集計であり、集計対象の相違だと判明した（`audit.md`）。契約はこの相違を測らずに一方だけを断定していた。
4. **self_contradiction** — 完了判定 d は「選ばれた recipe が一意に決まり」を求めるが、
   事前登録 §6.3 と 2026-09-18 の修正条項の同点規則は、**同一候補・同一受容野で残る同点**を解けない。
   指示どおり実行すると、実際に候補 C・8 層で 0.15 と 0.30 が並び、選定器が例外で停止した。
   判定 d は「諮って決めた」場合の一意性を覆っていない。

## 10. 陽性対照（判定が空振りでないことの確認）

| 判定 | 何を入力すれば失敗するはずか | 実際に何が起きたか |
|---|---|---|
| a 特徴抽出の決定性 | backbone の重みを変える | 要約値が変わった（`weight_change_detected: true`） |
| a フレーム数の一致 | manifest から 1 動画を消す | 集合差 1 を検出（`removed_video_detected: true`） |
| b 折り表への適合 | 1 run の config の test 動画を 07 から 11 に差し替える | 集合差が出て検出。無改変の 71 run は違反 0 件 |
| d 選定が test に依存しない | 表に test 由来の列を足して選定を回す | 試験 `test_simple_candidate_within_twenty_percent_and_no_test_dependency` が、`test_jaccard` を ±100 で足しても選定が変わらないことを確認 |
| d 同点規則（新規） | 同一候補・同一受容野で、seed 間 pstd の小さい方を次点側に置く | 次点が選ばれた。逆向き（pstd の小さい方が最良側）では最良が残った。試験 `test_same_candidate_and_receptive_field_prefers_steadier_seeds` |
| e test の二重評価 | 同じ折りの台帳をもう一度作る | `FileExistsError` で停止。台帳 269 バイトは無傷 |
| g 時間ヘッドが働いている | 候補 A が単フレーム線形を下回る | 折り A の候補 A 6 run すべてが上回った（最小の差 0.03418）。下回った run は 0 件 |
| 試験が増えていないこと | 失敗する試験を持ち込む | `origin/phase0` の worktree で 6 失敗を実測。終了後も同じ 6 件で、件数も内訳も一致 |

## 11. 報告後の実測（2026-09-18 JST）

- PR #183。実測で `draft=false` `base=phase0` `head=feat/stage1-phase-tower` `state=OPEN`。
  commit は `92508ff4`（本体）と `310fb493`（PR 番号の記録）。
- `make task-report` は exit 0。`verdict: partial`、`n_issuer_defects: 4`、
  `report_sha256: 21d3aeb012865707fdb362c25617930d14ad302e5c5dfac4e842ecbe60ca1492`、28484 バイト。
- `.sync-pause` を `.sync-pause.released.20260918` へ移して自動同期を戻した。
  稼働中の `~/bin/m2-sync.sh` は抑止に対応済み（`grep -c sync-pause` が 2）。
- **報告を書いたあとに `make forbidden-check` の結果が変わった。** 22:01 UTC 時点で
  status fail・違反 2 件。内訳は `experiments/transfer/pd_refin_empty_seed42_tf32/logs/` の
  2 ファイルで、いずれも 21:58:17 UTC に**別の処理**が書いたものである（本契約の commit 16:25 UTC より後）。
  本契約の出力ではないため触っていない（禁止事項 8「開始前から在る未追跡を消さない」、
  9「他利用者の処理を止めない」）。§7 の pass は本契約の作業が終わった時点の実測である。
- push は `https` の遠隔が対話的な資格情報を要求して失敗したため、`git@github.com:takuya3h/m2.git`
  を明示して行った。`origin` の fetch は ssh、push は https に設定されている。
