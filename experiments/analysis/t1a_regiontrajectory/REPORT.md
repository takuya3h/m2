# T1a-RegionTrajectory: Temporal Object-Set Fusion（COUPLING §4.1 優先度1）

**日付**: 2026-07-05 ／ **データ**: val phase（online causal）, frozen=relation_detr_seed42, phase-seed 42/123/456, epochs=50
**証跡**: `results.json` / `REPORT.txt` ／ run: `experiments/transfer/t1a_regiontraj_*_seed{42,123,456}`
**コード**: `scripts/train_t1a_regiontraj.py`（新規実装）, `scripts/analyze_regiontraj.py`

## 問い・仮説
T1a base は region-token(15×256) を **flat 連結**で TeCNO に渡すため frame ごとの術具出現変動に過敏で、
frame acc は高いが **edit score が悪化・過分節**（§3.1）。§4.1 の役割分離アーキ
（Set encoder → gated residual → causal temporal attention → TeCNO + boundary head）で
**acc を維持しつつ edit/seg-F1（時間的一貫性）を改善できるか**。

## 手法（§4.1 Temporal Object-Set Fusion, 新規実装）
```
region tokens(15×256)
  → Set encoder（per-token 共有MLP + 学習可能 class 埋め込み + attention pool = 置換不変集約, 3840→128）
  → 二経路 gated residual（安定 tool-presence(15-d) が rich region を sigmoid ゲート）
  → [GAP2048 ⊕ region_gated ⊕ presence] → d_model=256
  → causal temporal attention（短期 object memory, 因果マスク）
  → SingleStageTCN(TeCNO) + refine
    ├ phase head
    └ boundary head（class-agnostic）→ sticky decode（因果 boundary-gated, τ=0.5）
```
土台・ハイパー（epochs50/lr5e-4/stages2/layers8/f64/boundary_w1.0）は T1a base / T1a-Boundary と統一。
paired-σ §10.1（|meanΔ|>pstdev かつ全 seed 同符号）。

> **⚠️ 結論（先出し）**: val では §4.1 成功基準を全て満たすが、**held-out test で非確証**。
> test で macro-F1 が **−8.75pp 有意低下**（全seed負）・edit 改善は消失（符号混在）・seg-F1@50 も有意悪化。
> **RegionTrajectory（この実装）は val に overfit し、汎化しない**。→ 確定改善として採用不可。詳細は末尾「test 確認」。

## 結果 — val: §4.1 成功基準を全て充足（が test で覆る）

### plain decode（per-frame argmax, base と同じ推論）vs T1a base
| metric | base平均 | RT平均 | Δ mean | σ | 判定 |
|---|---:|---:|---:|---:|---|
| acc | 94.79 | 94.74 | **−0.04pp** | 0.27 | ✅維持 |
| macro-F1 | 80.80 | 80.87 | **+0.08pp** | 0.53 | ✅維持 |
| **edit** | 36.19 | 40.27 | **+4.08** | 2.80 | ✅**有意改善**（全seed正）|
| **seg-F1@10/25/50** | .469/.459/.439 | .548/.534/.477 | **+.08/+.08/+.04** | .02 | ✅**有意改善**（全seed正）|

### sticky decode（因果 boundary-gated）vs T1a base plain
| metric | Δ mean | 判定 |
|---|---:|---|
| acc | −0.44pp | ✅維持（符号混在）|
| macro-F1 | −0.86pp | ✅維持（非有意, 微圧縮）|
| **edit** | **+15.69** | ✅**有意改善** |
| **seg-F1@10/25/50** | **+.15/+.15/+.10** | ✅**有意改善** |

## 解釈
1. **§4.1 の予言通り**：acc/macro-F1 を維持しつつ **edit を有意改善**（plain +4.08, sticky +15.69）・
   seg-F1 も有意改善。過分節/flicker が減り時間的一貫性が上がった。
2. **境界 head 単独では効かない**：T1a-Boundary の plain edit は 33-35＝base(36) と同等。
   **Set encoder＋temporal attention＋gated residual の表現統合が boundary を機能させた**（アーキの寄与）。
   → 「単純連結でなく役割分離が必要」（§3.1）を実証。
3. **plain を主推奨**：acc/macro-F1 を確実に維持しつつ edit を有意改善。
   sticky は edit を最大化（+15.69）するが macro-F1 を微圧縮（−0.86pp, 非有意）＝時間一貫性を最優先する場合の選択肢。

## test 確認（決定的・val の結論を覆す）
同一 efros 環境で RegionTraj/base の 3seed を `--eval-test` で fresh 学習→test 評価（phase-seed paired）。

| 指標 | test RT平均 | test base平均 | Δ mean | σ | 判定 |
|---|---:|---:|---:|---:|---|
| acc | 83.02 | 82.86 | +0.16pp | 3.25 | ✅維持（符号混在・noisy）|
| **macro-F1** | 59.94 | 68.69 | **−8.75pp** | 3.84 | ⚠️**有意低下（全seed負）**|
| edit | 50.21 | 52.32 | −2.10 | 4.14 | ○非有意（**val の +4.08 が消失**, 符号混在）|
| **seg-F1@50** | 0.432 | 0.481 | **−0.05** | 0.02 | ⚠️**有意悪化（全seed負）**|

**結論**: val で示した edit/seg-F1 改善は **held-out test に transfer せず**、逆に **macro-F1 を有意に悪化**させる。
`acc` は維持されるが、**長尾工程を捉える macro-F1 と時間分節 seg-F1 が test で有意低下** ＝ RegionTraj は val に overfit。

**機序（仮説）**: Set encoder の attention pool が region 15×256=3840-d を **128-d に圧縮**するため、
val は fit できるが、rare/長尾工程の識別に要る per-tool 詳細が失われ test 汎化が劣化。
flat-concat の T1a base は全 15×256 を保持し test でより頑健。→ **「圧縮しすぎ」が主因の仮説**。

## 位置づけ・次
- **確定改善として採用不可**（[[val_test_significance_gap]] の教訓が的中：val 有意→test 非確証）。
- 反証可能な次段: (a) 圧縮緩和＝flat region を pooled summary と**併存**（情報非破壊）or tok_dim/d_model 拡大、
  (b) 正則化強化、(c) boundary/sticky と Set encoder を**分離 ablation**（どちらが overfit 源か）。
- edit 改善が欲しいだけなら T1a-Boundary の sticky decode 単体（acc 影響小）を検討。
- 本結果は「region を naive に時間統合すると汎化を損なう」という**負の知見**として COUPLING §4.1 にフィードバック価値あり。
