# Phase C — 基準点との条件一致度

数値はすべて `runindex/index.csv`（run 単位）と `runindex/experiments.csv`（集約）からの実測。
σ の系統は `spec.yaml` が `sigma_policy` を省略しているため `context/conventions.md#sigma` の
既定を継承する: **series = pstd / sigma_source = paired_delta / delta_sigma_source = paired**。

## 1. 既存の基準点（索引から実測）

`step` の値を一度出力してから絞った（名前の部分一致で探していない）。

| 基準点 | experiment_id | 主指標 | 値 | pstd | sstd | seeds | eval_recipe_id | frozen_source_tag | host |
|---|---|---|---|---:|---:|---|---|---|---|
| 検出 neck 無し | `baselines/s0_frozen/relationdetr_s0frozen_cocohead@val` | mAP | 0.7051403 | 0.0042154 | 0.0051628 | 42,123,456 | `250424985fbf` | **（空）** | lecun |
| 検出 neck 有り | `baselines/s0_frozen/relationdetr_s0frozen_neck_cocohead@val` | mAP | 0.7095447 | 0.0073983 | 0.0090611 | 42,123,456 | `250424985fbf` | **（空）** | lecun |
| 工程 neck 無し | `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` | accuracy | 0.8973015 | 0.0059171 | 0.0060992 | 42,123,456（17 run） | `e98ffddee042` | `relation_detr_seed42` | efros,lecun |
| 工程 neck 有り | `phase1/s4_phase_baseline/frozen_tecno_phase_baseline_neck@val~relation_detr_seed42` | accuracy | 0.9141914 | 0.0014259 | 0.0017464 | 42,123,456 | `e98ffddee042` | `relation_detr_seed42` | lecun |

### 4 つ以外に基準点として使われている実験

`control_of` を集計した結果、分母として宣言されている実験は **9 種類・計 136 回**で、
その内訳は次のとおり。

| 回数 | 分母 |
|---:|---|
| 119 | `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` |
| 4 | 同上 `~relation_detr_augstrong_seed42` |
| 3 | `transfer/t1a_regiontoken/t1a_regiontoken@val~relation_detr_seed42` |
| 2 × 5 | 同 baseline の `augstrong_hires_seed42` / `augstrong_seed123` / `augstrong_seed456` / `seed123` / `seed456` |

**重要: 検出側の S0-frozen は `control_of` の分母として 0 回しか現れない。**
検出の Δ は `delta_detection` / `injection_effect` のように **同一 run 内の inj − ctrl** で
測られており、S0-frozen は「絶対値の参照点」であって paired の分母ではない。
補助信号ありのモデルを S0-frozen と直接比べるのは、索引に前例が無い使い方である。

## 2. neck 追加の前例（Q9）— seed 対応 paired Δ を実測

`step` が同じで neck の有無だけが違う 2 実験を、共通 seed (42/123/456) で対応させて測った。

### 工程側

| seed | neck 無し | neck 有り | Δ |
|---|---:|---:|---:|
| 42 | 0.901367 | 0.914851 | +0.013484 |
| 123 | 0.895578 | 0.912211 | +0.016634 |
| 456 | 0.893333 | 0.915512 | +0.022178 |

- paired Δ 平均 = **+0.017432**
- paired Δ の pstd = 0.003594（sstd 0.004402）
- **abs(Δ)/σ = 4.850**（基準点の seed 間 pstd 0.003385 を使うと 5.150）
- **全 seed 同符号 = True**

→ 判定規約 `abs(delta) / sigma >= 1 かつ 全 seed 同符号` を**満たす**。
**工程側は neck の追加だけで有意に動く。** これが基準点を取り直した前例である。

### 検出側

| seed | neck 無し | neck 有り | Δ |
|---|---:|---:|---:|
| 42 | 0.710008 | 0.715881 | +0.005873 |
| 123 | 0.699726 | 0.699166 | **−0.000560** |
| 456 | 0.705687 | 0.713587 | +0.007900 |

- paired Δ 平均 = **+0.004404**
- paired Δ の pstd = 0.003607（sstd 0.004417）
- abs(Δ)/σ = **1.221**（基準点の seed 間 pstd 0.004215 を使うと 1.045）
- **全 seed 同符号 = False**（seed 123 が負）

→ σ 条件は満たすが**符号条件で落ちる**ため、判定規約の AND は**満たさない**。
**検出側は neck 追加が有意とは言えない。**

### 含意（材料であって決定ではない）

補助課題のヘッドを足すと共有部分の容量が増える。上の前例は
**工程側では容量増だけで 4.85σ 動く**ことを示すため、補助信号の効果を主張するには
**「ヘッドはあるが補助教師を与えない」容量一致対照**が要る。
そうしないと Δ が補助信号の効果か容量増かを分離できない。
検出側は同じ操作で有意差が出ていないため、容量増の感度は低い。
**要否を決めるのは起票者と利用者である。**

## 3. 評価条件が同じか（実効キーで比較）

`src/egosurgery/utils/eval_recipe.py` の `recipes_match` は
**`test_cfg` の実効キーを全比較**する（記述用 `note` / `description` のみ除外）。
加えて split サイズ 3 種と GPU 構成（`gpu_count` / `effective_batch_size`）も比較する。

実記録（`metrics.json` の `eval_recipe`）:

| 基準点 | test_cfg（実効キー） | gpu_count | eff_bs | lr_scaling |
|---|---|---:|---:|---|
| 検出 S0-frozen | `score_thr=0.0, max_per_img=300, nms_pre=null, nms_iou=null`（**NMS-free 系統**） | 1 | 2 | linear_x2 |
| 工程 S4 neck | `task=phase, inference_protocol=online_causal, jaccard_mode=strict, temporal_head=tecno, backbone=relation_detr_resnet50_frozen_seed42, num_stages=2, num_layers=8, num_f_maps=64` | 1 | 1 | none |

- 検出側は `step=s0` 全体では recipe が **8 種類 + 空 14 run** に分裂しているが、
  S0-frozen の 6 run はすべて `250424985fbf` の 1 系統で揃っている。
- 工程側は `s4_phase*` の **64 run すべてが `e98ffddee042` の 1 系統**。

🔴 **設計上の強い制約が 1 つある。** 工程側の `test_cfg` には
**時系列ヘッドの構成キー（`temporal_head` / `num_stages` / `num_layers` / `num_f_maps` / `backbone`）が入っている。**
補助課題の追加でこれらのいずれかが変わると `recipes_match` が False を返し、
`DeltaCalculator` が `InconsistentRecipeError` を送出する。
つまり **Δ が統計的に疑わしくなる前に、計算そのものが拒否される。**
補助ヘッドは工程側の時系列ヘッド構成を**変えない形**で足す必要がある。

## 4. 学習の母集団が同じか（Q8）

### 主課題の母集団（実測）

`data/processed/phase_manifest/{train,val,test}.json`:

| split | num_frames | num_clips |
|---|---:|---:|
| train | 9,657 | 13 |
| val | 1,515 | 3 |
| test | 4,265 | 6 |
| 計 | **15,437** | 22 |

**工程学習の母集団は術具 bbox split と完全に同一の 15,437 枚**であり、
工程ラベルを持つ 17,233 枚ではない。clip 構成（13/3/6）は
hand_tool_seg のセグメント構成（train 13 / val 3 / test 6）と一致する。

### 補助課題を足したときの母集団の変化

| 種類 | train | val | test | 計 | 対 15,437 |
|---|---:|---:|---:|---:|---:|
| hand_seg | 9,627 | 1,515 | 4,255 | 15,397 | 99.74% |
| tool_seg | 9,528 | 1,512 | 3,927 | 14,967 | 96.96% |
| **hand_tool_seg** | 9,356 | 1,514 | 4,107 | **14,977** | **97.02%** |
| 欠落（loss_mask） | 301 | 1 | 158 | **460** | 2.98% |

**主課題の母集団が連動して変わるかは、実装上「変わらない」。**
`src/egosurgery/datasets/loss_mask.py` の `load_loss_mask` には
**呼び出し元が 1 つも無い**（`src/` と `configs/` で HTS を参照するのは同ファイルのみ、
`mask_dino_head.py` の `loss_mask` は Mask DINO の損失キー名で別物）。
現時点で除外機構は学習経路に配線されていないため、主課題の母集団は影響を受けない。

→ **設計の選択肢は 2 つある。**
(a) フレーム単位の有効フラグで補助損失だけを 0 にする（README §4.2 が想定する使い方）
  → 主課題の母集団は 15,437 のまま。**基準点と揃う。**
(b) 注釈が無いフレームを manifest から落とす
  → 主課題の母集団が 14,977 に縮み、**既存の全基準点と揃わなくなる。**

## 5. 推論手順の制約（Q10）

- 工程側は `PHASE_EVAL_PROTOCOL = {"inference_protocol": "online_causal", "jaccard_mode": "strict"}`
  で固定され、`s4_phase*` の 64 run すべてが同一 recipe（`e98ffddee042`）である。
- **流用できる同型の検証が実在する。** `tests/test_tecno.py::test_tecno_is_causal` は
  「時刻 `t_cut` 以降の入力だけを差し替え、`t_cut` より前の出力が変わらないこと」を
  `torch.allclose` で検証し、さらに「`t_cut` 以降は変わること」を健全性チェックとして併記する。
  入出力が `(B, C, T)` の時系列ヘッドであれば**ヘッドの中身に依らず適用できる**構造なので、
  把持関係ヘッドが時間方向の情報を使う場合はそのまま流用できる。
- `tests/test_delta.py:357` に工程 recipe ロック（online_causal / strict の差を不整合として
  検出する）のテストがある。

### 検出側の評価系統

検出の locked-down 系統は 2 つ定義されている（`eval_recipe.py`）。

| 定数 | score_thr | nms_pre | nms_iou | max_per_img |
|---|---:|---|---|---:|
| `LOCKED_DOWN_TEST_CFG` | 1e-8 | 3000 | 0.6 | 300 |
| `NMS_FREE_TEST_CFG` | 0.0 | null | null | 300 |

実装のコメントに、比較の三角形（凍結源 = Relation-DETR 単一 backbone）の検出ヘッドへ
locked-down の NMS@0.6 を適用すると **−4.5pt mAP** になる実測が記録されている。
S0-frozen の 6 run はすべて **NMS-free 系統**で記録されている。

→ 補助信号ありの検出モデルは **NMS-free 系統で評価する**のが既存基準点と揃う唯一の選択。

## 6. 比較可否の分類

| 基準点 | 凍結源 | 評価条件 | 共有容量 | 学習母集団 | 比較可否 |
|---|---|---|---|---|---|
| 検出 neck 無し `s0_frozen_cocohead` | tag 空（S0-frozen 自身が凍結源の生成側） | NMS-free で揃う | neck 無しに揃える必要 | 15,437 で揃う（設計 (a) なら） | **可**（ただし paired 分母の前例が無く、絶対値比較になる） |
| 検出 neck 有り `s0_frozen_neck_cocohead` | 同上 | 同上 | neck 有りに揃える必要 | 同上 | **可**。neck 追加自体は有意でない（1.22σ・符号不一致）ため、容量増の織り込みは検出側では必須でない |
| 工程 neck 無し `frozen_tecno_phase_baseline~relation_detr_seed42` | `relation_detr_seed42` で揃えられる | `e98ffddee042` で揃う。**時系列ヘッド構成キーを変えないこと**が条件 | neck 無し | 15,437 で揃う（設計 (a) なら） | **可**（119 回の分母実績あり） |
| 工程 neck 有り `frozen_tecno_phase_baseline_neck~relation_detr_seed42` | 同上 | 同上 | neck 有り | 同上 | **可**。ただし補助ヘッドの容量増は neck と同型の交絡になり得る（前例 4.85σ）ため容量一致対照が要る |

### 「補助信号を足す以外は同一」が成立する組

**成立する**: 工程側 `frozen_tecno_phase_baseline~relation_detr_seed42`（および `_neck` 版）との比較。
条件は 3 つ — (1) 凍結源を `relation_detr_seed42` に固定、(2) 工程側 `test_cfg` の
時系列ヘッド構成キーを変えない、(3) 補助損失をフレーム単位フラグで無効化し manifest を縮めない。

**成立しない**: 上記 3 条件のいずれかを崩した場合。特に (2) は
**Δ の計算自体が拒否される**ため、統計以前の問題になる。

**条件付き**: 検出側 S0-frozen との比較。凍結源・評価条件・母集団は揃えられるが、
**paired 分母として使われた前例が索引に無い**（`control_of` 0 回）。
既存の検出 Δ は同一 run 内の inj − ctrl で測られており、
S0-frozen との比較は unpaired の絶対値比較になる。
