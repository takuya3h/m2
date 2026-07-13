# T1a 利得源の因果分解 (a) per-tool-slot ablation ＋ shuffle 対照

**日付**: 2026-07-05 ／ **データ**: val phase acc/macro-F1（online causal）, det42-frozen, phase-seed 42/123/456
**証跡**: `results.json` / `REPORT.txt` ／ 生 run: `experiments/transfer/t1a_region_mask_{00..14}_*`（45, 全 valid）, baseline `t1a_3seed_det42_p{42,123,456}_frozen_*`, 対照 `t1a_shuffle_00{1,2,3}_*`
**コード**: `scripts/analyze_t1a_factorial_ablation.py`（既存 45 run の解析。再学習なし）

## 問い
T1a の phase 利得（region-token ⊕ GAP → TeCNO）**+4.93pp**（0.9479 vs S4 GAP-base 0.8986）は、**どの tool-slot が因果的に担うのか**？
region-token(15×256) の各 tool-slot を 1 点ずつ 0 除去し、除去による低下 Δ_slot=mask−baseline を測る。

## 方法
- 既存 45 run（15 slot × 3 phase-seed, `train_t1a.py --mask-region-tool-dim`）を再利用。全 run が
  frozen=relation_detr_seed42 / epochs=50 / in_dim=5888 で一致（config 検証済）。
- baseline = det42-frozen no-mask の pXX_frozen 三点（acc 0.9479/0.9492/0.9465, 命名一貫。
  重複 p42 run 0.9498 も存在＝phase 学習非決定性 ~0.2pp、結論に影響なし）。
- phase-seed を paired とみなし paired-σ（§10.1: |meanΔ|>pstdev かつ全 seed 同符号で有意）。
- positive control: `t1a_shuffle`（region の frame 対応を破壊）。

## 結果

### positive control（region 情報の実在性）
region の frame 対応を破壊すると acc **0.9479 → 0.8605**（−8.73pp）、**S4 GAP-base 0.8986 すら −3.81pp** 下回る。
→ region 情報の寄与は実在し、frame 整合（どのフレームにどの器具か）が本質。単なる容量増ではない。

### per-slot 除去 Δ（★=signature 術具）
| slot | tool | Δacc(pp) | σ | ΔmacroF1(pp) | 判定 |
|---:|---|---:|---:|---:|---|
| 0★ | **Bipolar Forceps** (hemostasis) | **−0.86** | 0.19 | **−3.11** | ✅有意DROP |
| 9★ | **Scalpel** (incision) | **−0.77** | 0.19 | −1.15 | ✅有意DROP |
| 6★ | **Needle Holders** (closure) | **−0.46** | 0.14 | −0.28 | ✅有意DROP |
| 10 | Scissors (dissection特異) | −0.44 | 0.22 | −0.73 | ✅有意DROP |
| 11★ | Skewer (design) | −0.00 | 0.22 | +0.05 | 非有意 |
| 13★ | Syringe (anesthesia) | +0.07 | 0.09 | +0.12 | 非有意 |
| 他9 | 非signature（Gauze/MouthGag/…） | −0.13〜+0.15 | — | — | ほぼ中立 |

**signature 5slot: Δacc mean −0.40pp（3/5 有意DROP）** vs **非signature 10slot: −0.01pp（1/10）**。
除去影響 Top: Bipolar(−0.86) > Scalpel(−0.77) > NeedleHolders(−0.46) > Scissors(−0.44)。

## 解釈 — 利得則 `gain ≈ headroom × signature` を因果的に確証
- **利得の因果源は signature 術具の region 表現**：hemostasis(Bipolar)/incision(Scalpel)/closure(NeedleHolders) の
  除去で phase が有意低下。相関だった step_c §3.4 の機構が **ablation（因果）で確定**。
- **Skewer/Syringe が落ちない理由 = 対応工程の飽和**：design(Skewer) は F1≈1.0・anesthesia(Syringe) も高く
  **headroom≈0** → signature でも除去して落ちない。これは利得則 `gain≈headroom×signature` の予言通り
  （signature があっても headroom が無ければ寄与しない）。→ 利得則を **反証可能な形で満たす**。
- **Scissors(−0.44)** は EDA §8(1) の dissection 特異術具（Scissors→dissection 84%）で、狭義 signature 4 には
  入らないが process-specific。その低下も機構と整合。
- **macro-F1 の低下が acc より大**（Bipolar −3.11pp）＝長尾工程（hemostasis 等）を直撃＝利得は多数派水増しでない。

---

# (b) 入力成分 factorial（appearance / confidence / class の寄与）

**証跡**: `factorial_b_results.json` ／ run: `t1a_appearance_*_seed{42,123,456}`（appearance-only 再抽出）,
`t1a_base_test_*`（current=appearance×conf, val+test）, `b2a_det2phase_toolpresence_*`（class-only, val）
**コード**: `scripts/{extract_t1a_regiontoken.py --mode appearance, analyze_t1a_factorial_b.py}`, `train_t1a.py --eval-test/RELDETR_REGION_TAG`

同一 q*(argmax score) 選択で region-token の**値の合成のみ**を変えて成分を分離:
class-only(presence 15-d, =B2a) → +appearance(256-d 埋め込み) → +confidence(score 重み, =現行 T1a)。

### 成分の価値（3-seed paired-σ）
| 成分 | 指標 | val Δ | test Δ | 判定 |
|---|---|---:|---:|---|
| **appearance** (current − class-only) | acc / macroF1 | **+1.17 / +1.19pp** ✅ | (B2a test無) | 埋め込みが frame 識別を上げる |
| | **edit** | **−11.25** ✅ | — | **過分節を招く（§3.1 の rich→edt悪化を定量）** |
| **confidence 重み** (current − appearance-only) | acc / macroF1 | −0.15 / −0.67pp ○ | **+1.31 / +6.62pp** ✅ | **test 汎化の鍵（val 不可視）** |
| | edit | −7.39 ○ | **+11.81** ✅ | test で時間一貫性も confidence 依存 |

### 解釈 — confidence 重みが「val 不可視・test 必須」の汎化成分
1. **appearance 埋め込み**：presence スカラ(B2a)比で frame acc/macro-F1 を有意改善(+1.2pp)するが、**edit を有意悪化(−11.25)**
   ＝ rich な物体特徴が per-frame 識別を上げる一方で時間的過分節を招く（§3.1 のトレードオフを因果的に定量）。
2. **confidence 重み(score gate)**：**val では中立**（appearance-only と差なし）だが、**held-out test では acc/macroF1/edit を全て有意改善**
   （macroF1 +6.62pp）。confidence が低い検出の埋め込みを減衰させることが**test 汎化に必須の正則化**として働く。
3. **P2 RegionTrajectory の失敗機序と一致**：RegionTraj（Set encoder 圧縮）も appearance-only も **val に overfit → test で macro-F1 低下**。
   両者の共通因子は「per-class confidence 信号の希釈/喪失」。→ **T1a 利得の汎化は confidence-weighted per-class appearance が担う**という統一的知見。

### 未実施（optional）
- **class+bbox / +truncation** 成分は bbox hook 追加＋再抽出が必要（本 (b) では appearance/confidence を優先）。
- class-only(B2a) の **test** 評価（現状 val のみ）を足せば appearance の edit 悪化を test でも確証できる。
