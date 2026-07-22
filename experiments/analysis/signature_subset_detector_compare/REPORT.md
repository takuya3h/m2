# signature 部分集合 per-class AP 比較: Relation-DETR vs Align-DETR

**日付**: 2026-07-05 ／ **データ**: val COCO bbox AP @IoU 0.5:0.95, S0 bbox baseline 3seed（§6 統制）
**証跡**: `results.json` / `REPORT.txt`（機械出力）／ 生 AP: `experiments/baselines/s0_{016,017,018}_relationdetr_*`, `s0_{028,029,030}_aligndetr_*`

## 問い（仮説）
overall mAP は Relation-DETR 首位(0.7268) だが **AP_rare は Align-DETR 首位(0.7868)**（experiment_log §検出器比較）。
希少・工程特異な **signature 術具**（EDA §8 / 利得則 `gain ≈ headroom × signature`, step_c §3.4）は phase 認識を決める。
→ **det→phase の観点では overall より signature 部分集合での検出品質が本質**。Align-DETR の希少術具優位は
signature 部分集合に効くのか、それとも Relation-DETR が依然優位か？

## 方法
- subset は EDA REPORT §8 の基準で定義（恣意性回避のため複数グルーピングを併記）:
  - **signature_narrow (4)**: §8(2)「各工程の signature tool」= Syringe(anesthesia)/Needle Holders(closure)/Skewer(design)/Scalpel(incision)
  - **signature_broad (9)**: +hemostasis(Bipolar)/dissection(Electric Cautery/Hook/Raspatory/Scissors)
  - **ubiquitous_ctrl (4)**: §8(4) 偏在術具（工程手掛かり弱い対照群）= Gauze/Mouth Gag/Suction Cannula/Tweezers
- Retractor は val instance 0（AP=NaN）→ 除外。
- seed42/123/456 を paired とみなし、detector-seed で paired-σ（§10.1: `|mean Δ|>pstdev(Δ)` かつ全 seed 同符号）。
- **サニティ**: 全15クラス平均が experiment_log の公式 mAP（Rel 72.68±0.34 / Align 71.33±1.15）と完全一致 → 手法は公式評価器と整合。

## 結果

### 部分集合サマリ（3seed 平均±pstdev, %）
| subset | Relation-DETR | Align-DETR | Δ(Rel−Align) | paired-σ 判定 |
|---|---:|---:|---:|---|
| **signature_narrow (4)** | 81.14±0.49 | **83.57±0.46** | **−2.43pp** | ✅**有意・Align-DETR 優位**（3seed 全負, σ0.59）|
| signature_broad (9) | 79.15±0.52 | 78.20±1.54 | +0.96pp | ❌非有意（符号不一致, σ1.11）|
| **ubiquitous_ctrl (4)** | **67.06±0.16** | 64.97±0.80 | +2.09pp | ✅**有意・Relation-DETR 優位**（3seed 全正, σ0.82）|
| all15（参考） | 72.68±0.34 | 71.33±1.15 | +1.35pp | — |

### per-class（3seed 平均 AP %, * = 3seed 全同符号＝頑健）
| class | 群 | Relation | Align | Δpp | 勝者 |
|---|---|---:|---:|---:|---|
| **Syringe** | signature | 55.64 | **62.29** | **−6.65** | Align* |
| **Scalpel** | signature | 90.28 | **92.38** | **−2.09** | Align* |
| Skewer | signature | 94.03 | 95.08 | −1.04 | Align |
| Needle Holders | signature | 84.62 | 84.55 | +0.07 | Rel |
| Bipolar Forceps | signature | 79.34 | 77.99 | +1.35 | Rel |
| Electric Cautery | signature | 96.32 | 96.26 | +0.05 | Rel |
| Hook | signature | 58.78 | 56.31 | +2.48 | Rel |
| Scissors | signature | 71.11 | 69.52 | +1.59 | Rel |
| **Raspatory** | signature | **82.25** | 69.39 | **+12.85** | Rel |
| Forceps | generic | 36.92 | 34.96 | +1.97 | Rel |
| Gauze | ctrl | 27.82 | 24.85 | +2.97 | Rel |
| Mouth Gag | ctrl | 80.79 | 79.46 | +1.33 | Rel* |
| Suction Cannula | ctrl | 81.51 | 79.71 | +1.81 | Rel* |
| Tweezers | ctrl | 78.10 | 75.86 | +2.24 | Rel* |
| Retractor | — | NaN | NaN | — | (val 0件) |

## 解釈
1. **Align-DETR の AP_rare 優位の正体は Syringe(−6.65pp) と Scalpel(−2.09pp)**＝rare∧phase-signature 術具（anesthesia/incision の signature）。この2術具で 3seed 一貫して Align-DETR が明確に勝つ。
2. **プロジェクト自身の「signature tool」定義（narrow 4クラス）では Align-DETR が有意に優位**（Δ=−2.43pp, 全 seed 負）。すなわち **phase を決める中核術具の検出品質は Align-DETR が上**。
3. 一方 **対照群（偏在術具）では Relation-DETR が有意に優位**（+2.09pp）。overall mAP 首位は主にこの汎用術具＋dissection の Raspatory(+12.85pp) が押し上げている。**Align-DETR の劣位は phase と無関係な術具に局在**。
4. **broad(9) は同率圏**：narrow の Align 優位が、dissection 系（特に Raspatory で Rel が大勝）で相殺されるため。結論は subset の取り方に依存する——per-class 表で透明化。

## det→phase への含意 — 既存の下流実験が「AP優位≠phase有用」を確定（最重要）
per-class AP だけ見ると「Align-DETR は signature 術具（Scalpel/Syringe）で優位 → phase を改善しうる」と読みたくなる。
**しかしこの仮説は既存の下流有用性比較①（台帳 completed, s4_001-003 vs s4_010-012）が明確に反証している**:

| frozen source → 同一TeCNO | phase acc | phase macroF1 |
|---|---:|---:|
| **Relation-DETR** | **0.8986** | **0.7086** |
| Align-DETR | 0.8464 | 0.6036 |
| **Δ(Rel−Align)** | **+5.2pp (8.7σ)** | **+10.5pp (3.5σ)** |

→ **signature 部分集合の検出 AP で Align が +2.43pp 勝っても、det→phase では Relation-DETR が圧勝**。
**検出 AP（とりわけ signature 部分集合 AP）は det→phase 有用性を予測しない**。凍結源の優劣を決めるのは
per-class AP ではなく **frozen 特徴の表現品質**（Align の後段特徴が phase 線形分離に劣る）。→ **凍結源は Relation-DETR で確定・維持**。

- 検証性: Rel 側（s4_001-003）はローカルで再現可能（acc 0.9023/0.8957/0.8977=mean 0.8986, 台帳と一致）。
  Align 側（s4_010-012）は efros で空 scaffold（別ホスト実行, [[adhoc_experiment_evidence_gap]]）→ 台帳値のみ・要ローカル再取得。
- この反証は「AP 差が phase に transfer する保証はない」（[[val_test_significance_gap]], B2a oracle gap 非閉塞）と整合。

## 位置づけ
本 per-class 分解の価値は「なぜ Align を選びたくなるか（signature AP 優位）」を定量化し、それが下流で覆ることを示す**対照証拠**。
「凍結源＝Relation-DETR」の判断を **overall mAP 首位＋下流 phase 圧勝**の二重根拠で補強する。

## 次（optional）
1. Align 側下流（s4_010-012）の metrics をローカル再取得し 8.7σ を efros で再現・証跡化。
2. per-class AP を test split（unified recipe）でも確認（台帳の overall test: Rel 0.507/Align 0.505, Δ+0.002）。
