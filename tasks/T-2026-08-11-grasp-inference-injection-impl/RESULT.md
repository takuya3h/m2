# RESULT — 把持推論を工程入力へ渡す ctrl/inj 経路を実装

**task_id:** `T-2026-08-11-grasp-inference-injection-impl`  **kind:** `impl`
**host:** `lecun`  **branch:** `feat/grasp-inference-injection-impl`  **PR:** #105

## 1. 解決された参照

### 省略された `inputs.sigma_policy`

`context/conventions.md#sigma` の原文。

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

本契約は効果の統計判定を行わないため、この継承値は使用していない。

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md` の該当アンカーの原文。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

`inputs.denominator.ref` と `inputs.frozen_source.ref` は無く、追加解決はない。

## 2. 結論

結果は `pass`。凍結 Relation-DETR の GAP 2048 次元から `hand_tool_seg` の5クラス有無を
frame-wise に推論する独立枝を追加し、その sigmoid 出力を causal TeCNO の入力へ渡した。
inj は推論信号、ctrl は同形・同サイズの零信号を渡す。両腕の把持推論学習を同じにするため、
工程へ渡す信号は detach し、把持枝は両腕とも同じ masked BCE だけで学習する。

既定は無効で、既存 S4、B2a、T1b、検出側注入のファイルは変更していない。効果を測る本命実験は
実施しておらず、次の事前登録契約へ渡す。

## 3. Phase A — 既存経路と設計

### 既存注入の実測

- `runindex/experiments.csv` には `control_of` を持つ experiment が136件、`runindex/index.csv` には
  対応する run が439件あった。
- B2a は tool-presence 15次元を GAP 2048次元へ連結し、causal TeCNO の第1段へ渡す。
- legacy T1b は同じ seed・モデル・optimizer・学習量の二 run を使い、実 phase context 9次元と
  同形の零9次元を `set_phase_context` 直前で切り替える。
- 起票文の「同じ run の中で対にして」は実測で否定された。対は同一 seed の二 run、または
  `control_of` で別 experiment を指す形だった。

同じ機構へ乗せられると判定した。既存 B2a/T1b を変更せず、「同形の実信号/零信号を工程入力の
直前で切り替える」新規 signal-level 経路として追加した。

### 推論器の置き場所と無情報信号

- 推論器は凍結済み GAP 2048次元を受ける独立枝に置いた。工程 TeCNO と学習可能表現を共有しない。
- 無情報信号は全要素0。形 `(B,5,T)`、dtype、device は `zeros_like` で推論信号と一致し、
  frame内容を含まず、学習中ずっと同じ規則になる。
- `ctrl - A` は独立把持枝の容量と補助学習を追加した差を表す。ただし ctrl から工程への直接入力は
  常に零であり、把持枝と工程枝の間に工程損失の勾配は流れない。
- neck は無しを選んだ。既存の17-run S4 neck無し分母と同じ signal-level 土台へ載せ、
  neck容量を新しい軸として混ぜないためである。

### 教師と母集団

`hand_tool_seg/{train,val,test}.json` は category_id 1〜5 の COCO 形式だった。直接確認した train
image id 0 は `01_1_0124.jpg`、同 image の annotation id 0 は category_id 1。

| split | 注釈画像 | loss mask | 工程母集団 | 欠落/余分 |
|---|---:|---:|---:|---:|
| train | 9356 | 301 | 9657 | 0 / 0 |
| val | 1514 | 1 | 1515 | 0 / 0 |
| test | 4107 | 158 | 4265 | 0 / 0 |

目録から frame を落とさず、loss mask frame では把持 BCE だけを零にする。

## 4. Phase B — 実装

### 新規・変更箇所

- `src/egosurgery/datasets/grasp_targets.py`: COCO annotation を5次元 presence に変換し、mask frame を
  `valid=false` として返す。
- `src/egosurgery/models/temporal/grasp_inference_injection.py`: kernel 1 の frame-wise 把持枝、
  ctrl/inj 信号切替、causal TeCNO、masked BCE、5次元 accuracy。
- `src/egosurgery/models/build.py`: 文字列 config と dict/DictConfig の builder。
- `src/egosurgery/utils/grasp_phase_recipe.py`: 把持・arm設定を評価 recipe の外に置く。
- `configs/model/temporal/grasp_phase_injection.yaml`: 既定 `enabled: false`。
- `configs/stage/s4_grasp_injection_{ctrl,inj}.yaml`: 凍結源 seed42、neck無し、armだけ相違。
- `scripts/train_grasp_phase_injection.py`: W&B、ExperimentManager、Notion、task_id、smoke出力を配線。
- `scripts/audit_grasp_phase_injection.py` と `tests/test_grasp_inference_injection.py`: Phase C の検査。

把持の出来は5次元それぞれの binary accuracy として `grasp_accuracy_<dimension>` に記録する。

## 5. Phase C — 9項目の実測

出所は `audit/phase_c.json`、`pytest_before.txt`、`pytest_after.txt`。

| # | 検査 | 実測 |
|---:|---|---|
| 1 | 信号到達 | inj の最大絶対出力差 0.05775783956050873、ctrl 0.0 |
| 2 | 学習可能重み | A 397138、ctrl 528919、inj 528919、ctrl−A 131781 |
| 3 | recipe | baseline対ctrl/injは両方一致。num_layersを1増やした偽入力は不一致 |
| 4 | loss mask | mask把持損失0.0、注釈あり0.6931471824645996、同じmask frameの工程損失1.0986123085021973 |
| 5 | 母集団 | 9657 / 1515 / 4265。欠落・余分は全split 0 |
| 6 | 把持指標 |5次元すべてで数値が出た。未学習入力なので値の良否は判定しない |
| 7 | 既存挙動 | 無効時と既存 TeCNO の最大絶対差0.0。既存 B2a/T1b/FiLM/CA/S4 config差分0 |
| 8 | 因果性 | 未来の特徴・注入信号を変えた過去把持出力差0.0、過去工程出力差0.0 |
| 9 | 全テスト | 前5 failed/434 passed、後5 failed/443 passed。failure ID集合は完全一致、新規failure 0 |

変更前後の5 failure は `test_mmdet_trainer_eval_recipe_in_metrics` 1件と
`test_research_logger.py` 4件で、今回の変更前から存在する。新規近接テストは9件すべて通った。

## 6. Phase D — 短い試走

開始時、RTX A6000 の GPU 0/1 は使用率0%、計算process 0件だった。GPU 0だけを使い、seed 42、
train/val各1 clip、1 epochで ctrl/inj を各1本実行し、W&Bへ記録した。

| arm | 完了 | 工程損失 | 把持損失 | 所要時間 |
|---|---|---:|---:|---:|
| ctrl | true | 4.53012752532959 | 0.7004557847976685 | 2.471525396220386秒 |
| inj | true | 4.527888298034668 | 0.7004557847976685 | 2.211221544072032秒 |

1 epoch の精度値は評価していない。`make runindex` 後の索引総行数は751、task配下の smoke 混入は
0件だった。終了後の GPU 計算process は0件。

## 7. Gate と acceptance

| Gate | 判定 | 根拠 |
|---|---|---|
| G1 | pass | 既存 signal-level 注入と同じ原理の独立経路として追加できた |
| G2 | pass | inj差0.05775783956050873、ctrl差0.0 |
| G3 | pass | ctrl/inj重み528919で一致、baseline recipe一致、偽recipe不一致 |

`outputs.acceptance` の5項目はすべて実測で満たした。

## 8. 陽性対照

- 同じ重みの inj へ零信号と一信号を入れると工程出力差が0.05775783956050873へ変化し、同じ入力を
  ctrlへ入れても0.0だった。
- recipe の temporal `num_layers` を8から9へ変えると `recipes_match` は true から false へ反転した。
- maskを false から true へ変えると把持損失は0.0から0.6931471824645996へ変化した。
- 時刻5以降の特徴と信号だけを変えても時刻0〜4の把持・工程出力差は0.0だった。
- featureを無効にし、同じ TeCNO重みをロードした出力差は0.0だった。

## 9. 次の実験へ渡す材料

- 腕: ctrl / inj。seed 42/123/456 を想定し、腕あたり3本、合計6本。
- 分母: `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`。
  索引実測は17 run、3 seed、recipe id `e98ffddee042`。
- neck: 無し。
- 推論指標: 5次元それぞれの binary accuracy。
- 装置: RTX A6000 1台で smoke 完走。full 50 epoch の1本あたり所要時間は `UNKNOWN`。
- 本命の効果、3-seed差、sigma、有意性はすべて `UNKNOWN`。本契約では測っていない。

## 10. 起票者の誤り

`SPEC.md` は「既存の実験は注入と対照を同じ run の中で対にして差を測る」と断定したが、起票者の
申し送りどおり実装未確認の推測だった。実測では legacy T1b は同一 seed の二 run、現行索引は
`control_of` が別 experiment を参照する。指示どおり同一 run の分岐だけを探すと既存機構を誤認する。

## 11. 逸脱

- 環境差: `codegraph init` は既に初期化済みだったが、導入版に `codegraph watch` がなく
  `unknown command` となった。代わりに静的 explore/impact を使い、変更後は `codegraph sync` する。
- 契約誤記: 「同じ run 内」ではなく、実装で確認した二 run / `control_of` の対へ読み替えた。
- 判断: 無情報信号は零、推論器は独立枝、neckは無しを選んだ。理由は各節に記録した。
- 契約指定の `make runindex` は新規 trainer を決定性監査2生成物へ追加したが、後段の
  `forbidden-check` は runindex 生成物を除外せず違反とした。実行前に差分0だった対象2ファイルだけを
  `origin/phase0` へ戻し、禁止領域検査を再実行して通した。

## 12. 未解決事項

効果実験と full run 所要時間は本契約外のため `UNKNOWN`。次の事前登録契約で測る。

## 13. 記録と PR

- 実装・監査・報告 commit: `522e169`。
- branch `feat/grasp-inference-injection-impl` を origin へ push 済み。
- Draft PR #105。base `phase0`、head `feat/grasp-inference-injection-impl`、未マージ。
