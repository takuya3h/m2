# P4 T1b Phase→Det 最小版（classification-only phase bias / clsbias）

**日付**: 2026-07-05 ／ **データ**: 検出 val per-class AP（COCO AP@[.5:.95]）, warm-start=S0-frozen Relation-DETR seed42/123/456
**証跡**: `results.json` / `REPORT.txt` ／ 生 run: `transfer/t1b_clsbias_seed{42,123,456}_efros/{injected,control}_result.json`（各 `per_epoch_eval` 付き）
**コード**: `scripts/{train_t1b.py --inject clsbias --trainable film, run_t1b_clsbias_3seed_efros.sh, analyze_t1b_clsbias.py}`
**モデル**: `third_party/Relation-DETR/models/detectors/relation_detr_phaseclsbias.py`（gitignore 配下）

## 問い
現行 T1b-CA（single-token・非選択的 cross-attention）より前に、**box 枝を一切触らず class logit にのみ**
phase 事後(9-d)→MLP(zero-init)→per-tool 15次元 residual を加える**最小注入**は、rare∧工程特異術具の検出を改善するか？
（COUPLING §4.2 の安全な下限対照。真の query-selective CA の効果の下界を測る。）

## 方法（設定は T1b-CA と完全一致・捏造防止ガード付き）
- **注入**: `phase posterior (B,9) → MLP(zero-init) → per-tool bias (B,15)`、decoder 各層 class logits に broadcast 加算。
  `_rare_mask` で **rare∧工程特異 4 術具のみ**通す: Bipolar(0)/Scalpel(9)/Skewer(11)/Syringe(13)。
- **trainable=film**（検出器完全凍結・注入層 1615 params のみ学習）＝最純粋な注入効果。epochs=6/lr=1e-4/film_lr=5e-4。
- **warm-start**=S0-frozen 各 seed。zero-init ゆえ学習前は S0-frozen と厳密恒等（init mAP=base と一致で検査）。
- **対照 (ctrl)** = `--zero-ctx`（phase context を 0 固定）。inj と同一 warm-start・同一学習量（6ep）。
- **judge**: 3-seed paired-σ（§10.1: |mean(Δ)|>pstdev かつ全 seed 同符号で有意）。**Δ=inj−ctrl@final epoch**（同一学習量で公平比較）。

### 対照 (zero-ctx) が per-class AP の完全 no-op である理由（重要）
zero-ctx の学習後 per-class AP は **base と厳密一致**（seed42 Bipolar 0.7793=base 等）。定数 bias は 1 クラスの全検出スコアを
等しくシフト＝クラス内順位不変＝AP 不変だから。ゆえに **Δ=inj−ctrl は「phase 条件づけ（画像ごとに変わる bias）」の正味効果**を厳密に分離する。

## 結果

### 恒等・非劣化ガード
- init mAP: 全 seed **inj=ctrl（diff=0.0000）**、base(0.7303/0.7292/0.7217)と一致 → warm-start+zero-init 恒等 OK。
- overall mAP Δ(inj−ctrl) mean **+0.003pp**（pstd 0.165, **非有意**）→ **overall 非劣化**（符号も seed 間不一致でノイズ）。

### rare-4 per-class AP Δ（inj−ctrl, 3-seed paired-σ）
| tool | base AP | Δseed42 | Δseed123 | Δseed456 | **mean(pp)** | pstd | 判定 |
|---|---:|---:|---:|---:|---:|---:|:--:|
| ★**Bipolar Forceps** (hemostasis) | 0.779 | −3.52 | −1.02 | −4.88 | **−3.14** | 1.60 | ✅有意**悪化** |
| ★**Scalpel** (incision) | 0.898 | +1.74 | +1.35 | +0.64 | **+1.25** | 0.45 | ✅有意改善 |
| ★**Skewer** (design) | 0.944 | +0.68 | +1.28 | +0.32 | **+0.76** | 0.40 | ✅有意改善 |
| ★**Syringe** (anesthesia) | 0.571 | +0.51 | +1.50 | +1.50 | **+1.17** | 0.47 | ✅有意改善 |

- **3/4 が有意改善**（Scalpel/Skewer/Syringe）、**Bipolar のみ有意悪化**。全て all-seed 同符号。
- 非 rare 10 術具は全て mean ~0.00（設計通り中立。一部 ⚠ は top-300 選択のクラス間結合による微小値で実質ゼロ）。

### epoch 別軌跡（inj−ctrl mean over seeds, pp）
| tool | ep0 | ep1 | ep2 | ep3 | ep4 | ep5 |
|---|---:|---:|---:|---:|---:|---:|
| Bipolar | −1.94 | −2.47 | −2.60 | −3.33 | −3.19 | −3.14 | 単調悪化 |
| Scalpel | +0.97 | +1.12 | +1.21 | +1.22 | +1.23 | +1.25 | 単調改善で飽和 |
| Skewer | +0.68 | +0.71 | +0.74 | +0.75 | +0.76 | +0.76 | 即飽和 |
| Syringe | +1.47 | +1.34 | +1.29 | +1.24 | +1.21 | +1.17 | ep0 ピーク後微減 |

## 判定 — **部分的成功（3/4）／成功基準は不成立**
台帳 spec の成功基準「rare 全 4 の per-class AP が有意に inj>ctrl」は **Bipolar の有意悪化により不成立**。
一方 overall 非劣化・対照分離は満たし、**工程排他的な 3 術具では最小注入が確かに検出を改善**した。

> ⚠ **誠実性注記**: 本 rare-tool 判定は **val per-class AP** による。検出には held-out test split
> （`instances_test.json`, 4265 枚）が **存在する**（phase→det は 2026-06-24 に test 評価済）。
> val は rare 術具の実例が希少で **test の方が信頼できる**（`eval_phase2det_test.py` の注記）ため、
> Bipolar 悪化・3 術具改善を含む本 per-class 結論は **test 追認まで暫定**（[[val_test_significance_gap]]）。

## 解釈 — 利得則 `gain ≈ headroom × signature` の「phase 排他性」次元
- **改善 3 術具は工程排他的**: Syringe→anesthesia・Scalpel→incision・Skewer→design は EDA §8 で当該工程にほぼ排他。
  phase 事後が「その工程 → その術具が居る」を強く予測でき、class prior 加算が素直に効く。Syringe は headroom 最大(0.571)で
  絶対利得も最大級(+1.17)、利得則と整合。Skewer は飽和(0.944)ゆえ小幅(+0.76)。
- **Bipolar が悪化する機序 = 工程跨り使用**: Bipolar は hemostasis の signature だが**複数工程で出現**する（hemostasis 排他でない）。
  phase 条件 bias は「hemostasis 事後が高い時だけ Bipolar を押し上げ」を学習 → **off-signature 工程での Bipolar 検出スコアを相対的に抑圧** →
  当該フレームの検出が top-300 から押し出され per-class AP が低下。epoch 単調悪化がこの学習的抑圧を裏付ける。
- **設計含意**: 最小 phase→det 注入は有効だが、注入対象は **rare∧signature ではなく rare∧phase-排他** に限定すべき。
  Bipolar のような phase-spread 術具への一律注入は逆効果。→ 真の query-selective CA（multi-token）でも
  **phase-排他性で注入ゲートを掛ける**設計が要件。

## 位置づけ（P1–P3 との統一）
- det→phase 側（T1a）の知見「利得は confidence-weighted per-class appearance が担い、希釈すると汎化崩壊」に対し、
  phase→det 側（T1b 最小版）は「phase prior は phase-排他 rare に効き、phase-spread rare には逆効果」。
  **双方向とも『per-class の phase 特異性』が利得/損失の分岐点**という統一像。

## 次の一手（optional）
1. **rare_slots を phase-排他 3 術具に限定**して再実行 → Bipolar 悪化を除けば全改善で基準を満たすか検証（最小コスト follow-up）。
2. 有効性が確認できたので、真の query-selective CA（multi-token, box 枝も可変）へ拡張。ただし注入ゲートを phase-排他性で条件づける。
3. Bipolar の工程分布を EDA で定量（hemostasis 排他率）し、機序仮説を反証可能な形で確証。
