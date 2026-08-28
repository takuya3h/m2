# A7 K1 の出所照合

## 結論（三値のうち）

**「実在の run に遡れない」。**

台帳の K1 の数値（Δ_phase = **-0.0201**、hemostasis F1 が **0.801 → 0.179**）は、
**索引の三つの csv のいずれにも、丸め幅の許容差では存在しない。**

## 照合の規約

| 項目 | 値 |
|---|---|
| Δ_phase の目標 | -0.0201（表示 4 桁） |
| 許容差 | **±5e-5**（表示 4 桁の丸め幅。丸め表示を実数として扱わないため） |
| F1 の目標 | 0.801 / 0.179（表示 3 桁） |
| 許容差 | **±5e-4**（同じ理由） |
| 走査対象 | `runindex/experiments.csv`（213 行）・`runindex/index.csv`（1177 行）・`runindex/verdicts.csv`（1038 行）・`runindex/per_class.csv`（8370 行） |

## 照合器の対照（空振りでないことの確認）

| 対照 | 入力 | 結果 |
|---|---|---|
| **陽性** | 索引に確実に存在する既知の値 `0.8973014948553679`（分母の accuracy_mean） | **1 件一致** — `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` の `accuracy_mean` |
| **陰性** | 最終桁を一つ変えた `-0.0202` | **0 件** |
| **陰性** | 最終桁を一つ変えた `-0.0200` | **0 件** |

**照合器は働いている。** 下の 0 件は「検出できていない」ではない。

## 候補系統ごとの結果

### 系統1: 無効判定された 010-012 の aligndetr seed 群

| 項目 | 実測 |
|---|---|
| 行 | `phase1/s4_phase_baseline/frozen_tecno_phase_baseline_aligndetr@val~aligndetr...` |
| n_runs / n_runs_excluded | **3 / 3（全件が除外扱い）** |
| accuracy_mean | 0.8464246424642464 |
| 分母との差 | **Δ = -0.050877** |
| 台帳の -0.0201 との差 | **0.030777**（許容差 ±5e-5 の 600 倍以上） |
| hemostasis F1（per_class・3 seed） | 0.0 / **0.16666…** / 0.0（いずれも `excluded=True`） |

**0.801 にも 0.179 にも一致しない。Δ も一致しない。**

### 系統2: 2026-07-10 以降の作り直し版

索引に `aligndetr` を含む experiments 行は **2 件のみ**（`baselines/s0/aligndetr_bbox@val` と
上記の phase 行）。**作り直し版として区別できる別行は索引に存在しない。**
`baselines/s0/aligndetr_bbox@val` は `accuracy_mean` が空である。

### 系統3: それ以外の一致

`per_class.csv` を全走査したところ、**`hemostasis` の F1 で 0.179 に一致する行が 1 件**あった。

| 項目 | 実測 |
|---|---|
| ledger_key | `transfer__b2a_ro_oracle_noise000_009_b2a_ro_oracle_noise000_seed456` |
| group / step | `transfer` / `b2a_ro_oracle_noise000` |
| seed / split / host | 456 / val / lecun |
| excluded | **False** |
| value | 0.1794871794871795 |

**これは AlignDETR 凍結源とは無関係の、ノイズ注入実験（`b2a_ro_oracle_noise000`）の 1 run である。**
同じ step の hemostasis F1 は seed ごとに 0.827 / 0.637 / 0.179 / 0.0 とばらついており、
**`0.801 → 0.179` という対を構成しない。** 偶然の一致である。

`0.801` に一致した 9 件はいずれも別クラス（Suction Cannula / incision / Mouth Gag / Raspatory）で、
**hemostasis ではない。**

## AlignDETR の検出性能 0.686 に対応する値

`baselines/s0/aligndetr_bbox@val` の `accuracy_mean` は**空**であり、
検出性能を示す値がこの行に入っていない。**0.686 の所在は索引からは特定できない。**

## K1 を実測扱いにできるか

**できない。** 台帳の数値は、許容差を明示した照合では**索引のどの run にも遡れない**。
唯一の数値一致（hemostasis 0.179）は別系統の実験の偶然の一致であり、
Δ_phase も対になる 0.801 も伴わない。

**複数系統が同じ数値を持つ状況ではないため、escalate の条件には当たらない。**
