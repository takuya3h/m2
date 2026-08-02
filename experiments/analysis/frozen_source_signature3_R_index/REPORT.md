# 凍結源の per-class AP 分解：AlignDETR の det→phase 負転移は signature 術具 AP の欠損で説明できるか

**日付**: 2026-07-13 ／ **台帳**: Notion 実験Run台帳（Step=S0, Tier=must, Server=philip (RTX 6000 Ada)）
**証跡**: `compute_R.py` / `results.json`。元データは `experiments/baselines/_legacy_score_thr_0/s0_{016,017,018}_relationdetr_bbox_seed*`
（Relation-DETR）と `s0_{028,029,030}_aligndetr_bbox_seed*`（Align-DETR）の `per_class_ap.json`
（3-seed・score_thr=0.0 NMS-free recipe・val split 1515枚。2026-07-05 の
`experiments/analysis/signature_subset_detector_compare/` で公式 mAP と完全一致をサニティ確認済み）。

## 仮説
overall mAP は Relation-DETR 首位だが、下流 S4 phase 実験（台帳 s4_001-003 vs s4_010-012）では
AlignDETR を凍結源にすると phase 性能が明確に劣化する（負転移）。この負転移が、phase を規定する
**signature 3 術具（Bipolar Forceps=hemostasis / Needle Holders=closure / Scalpel=incision）**の
検出 AP 欠損で説明できるかを、選択性指標 R で定量化する。

## 方法
- R = (signature3 の平均 AP 低下) ÷ (generic12 の平均 AP 低下)。AP 低下 = Relation-DETR AP − Align-DETR AP
  （正 = AlignDETR が劣化）。
- generic12 は台帳定義上 15−3=12 クラスだが、**Retractor は val instance 数 0 のため AP=NaN**
  （既存 signature_subset_detector_compare と同じ除外）→ 実質 generic11。
- seed42/123/456 を paired とみなし、R を seed 毎に計算 → mean・pstdev・同符号判定（§10.1 paired-σ）。

## 結果（val split・主判定）

| | seed42 | seed123 | seed456 | mean | pstdev | 同符号 |
|---|---:|---:|---:|---:|---:|---|
| signature3 AP低下 (pp) | −1.09 | +0.14 | +0.28 | −0.11 | — | ❌ |
| generic11 AP低下 (pp) | +1.65 | +0.61 | +3.08 | +1.78 | — | ✅（全正） |
| **R** | **−0.66** | **+0.22** | **+0.09** | **−0.11** | **0.39** | ❌ |

**R は seed 間で符号不一致（−0.66 / +0.22 / +0.09）かつ \|mean R\|=0.11 < pstdev=0.39 → 非有意**。

副次: Bipolar Forceps 単独の AP 低下 = 平均 +1.35pp（seed42 −1.03 / seed123 +1.94 / seed456 +3.16pp、
これも同符号ではない）。

## 解釈
1. **仮説は支持されない**。signature3（Bipolar/NeedleHolders/Scalpel）の AP 低下は seed 間で符号すら
   一致せず、量もほぼゼロ（−0.11pp）。一方 **generic11 は全 seed で正、平均+1.78pp と明確に AlignDETR が劣化**
   している。すなわち AlignDETR の検出弱点は signature 術具ではなく汎用術具に局在しており、
   2026-07-05 の `signature_subset_detector_compare`（narrow4/broad9/ctrl4 の粗い区分）の結論
   「Align-DETR の劣位は phase と無関係な術具に局在」と、より狭い signature3 定義でも整合する。
2. **Bipolar Forceps 単独でも AlignDETR が劣化している方向（+1.35pp）ではあるが、seed 間で符号不一致
   （seed42のみ負）であり、単独クラスでの結論も弱い**。したがって「hemostasis F1 崩壊は Bipolar Forceps
   の検出AP欠損で説明できる」という副次仮説も、val の検出 AP からは強く支持されない。
3. **det→phase の負転移は検出 AP の欠損では説明できない**という結果は、既存分析が示した
   「検出 AP（とりわけ signature 部分集合 AP）は det→phase 有用性を予測しない」という結論を、
   台帳が指定した具体的な3術具・R指標の形でも再確認するもの。凍結源＝Relation-DETR の判断を追加で補強する。

## 未実施（要判断）
1. **test split（4265枚）での確認**: `relationdetr`/`aligndetr` S0 の checkpoint(*.pth) 6件が
   本ホスト(andrew)に存在しない（`experiments/**/*.pth` は同期対象外、かつ台帳の Server=philip が
   実体を保持）。test split での頑健性確認には philip からの checkpoint 転送（またはphipでの実行）が必要。
2. **hemostasis F1「0.801→0.179」の downstream 数値の直接検証**: `experiments/phase1/s4_phase_baseline_01{0,1,2}_frozen_tecno_phase_baseline_aligndetr_seed*`
   は checkpoints/logs/predictions/visualizations のみで metrics.json が空（efros で実行された空 scaffold）。
   台帳記載値のみで、per-phase F1 の生数値はこのホストでは再現できない
   （`experiments/analysis/signature_subset_detector_compare/REPORT.md` の既知ギャップと同一）。
3. Primary Metric 中の「overall mAP 差 −0.0443 に対する signature3 の寄与率」は、
   -0.0443 がどの比較（S0 vs S0-frozen 等）を指すか本ホストの証跡から特定できず、未算出。
