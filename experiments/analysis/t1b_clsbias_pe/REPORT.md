# T1b-clsbias-PE（phase-排他ゲート版 clsbias / P4 follow-up）

**日付**: 2026-07-07 ／ **データ**: 検出 **val** per-class AP（COCO AP@[.5:.95]）, warm-start=S0-frozen Relation-DETR seed42/123/456
**証跡**: `results.json` / `REPORT.txt` ／ 生 run: `transfer/t1b_clsbias_pe_seed{42,123,456}_efros/{injected,control}_result.json`（`per_epoch_eval` 付き）
**コード**: `scripts/{train_t1b.py --inject clsbias --trainable film, run_t1b_clsbias_pe_3seed_efros.sh, analyze_t1b_clsbias.py --tag clsbias_pe --which final}`
**設定差**: 元 clsbias（rare 4 全注入）に対し **`T1B_RARE_SLOTS=9,11,13`**（Scalpel/Skewer/Syringe のみ・**Bipolar slot0 を注入対象から除外**）。他は完全一致（trainable=film, epochs=6）。

## 問い
元 clsbias（P4）は rare 4 全注入で 3/4 改善だが **Bipolar Forceps が −3.14pp 有意悪化**（phase-spread 術具の off-signature 抑圧）し、
成功基準「rare 全 4 が有意に inj>ctrl」を満たさなかった。**Bipolar を注入対象から外せば**、残り 3 術具（phase-排他）は改善を保ち、
Bipolar は中立化し、**overall も非劣化以上**になるか？ ＝「注入は rare∧signature ではなく **rare∧phase-排他** に限定すべき」という設計原則の検証。

## 方法（元 clsbias と同一・唯一の差は注入対象術具）
- **注入**: `phase posterior (B,9) → MLP(zero-init) → per-tool bias (B,15)`、decoder 各層 class logits に broadcast 加算。
  `_rare_mask` を **Scalpel(9)/Skewer(11)/Syringe(13) のみ**通す（**Bipolar(0) を除外**）。
- **trainable=film**（検出器完全凍結・注入層のみ）。**対照 (ctrl)** = `--zero-ctx`。frozen ゆえ ctrl の per-class AP は base と厳密一致（no-op）。
- **judge**: 3-seed paired-σ（§10.1）、**Δ=inj−ctrl@final epoch**。

## 結果

### 恒等ガード
- init mAP 全 seed **inj=ctrl（diff=0.0000）**。ctrl final も base 据置（frozen no-op）。inj best は init を**上回る**（ep2/ep4/ep2, frozen で phase bias が overall を押上げ）。

### overall mAP Δ（inj−ctrl, @final, 3-seed paired-σ）
- inj : 0.7323 / 0.7323 / 0.7234　ctrl : 0.7303 / 0.7292 / 0.7217
- Δ = **+0.203 / +0.307 / +0.175 pp**、mean **+0.228pp**（pstd 0.057）→ **✅ 有意・非劣化**（init 超え）。

### rare-4 per-class AP Δ（inj−ctrl, @final, 3-seed paired-σ）
| tool | base AP | Δseed42 | Δseed123 | Δseed456 | **mean(pp)** | pstd | 判定 |
|---|---:|---:|---:|---:|---:|---:|:--:|
| ★Bipolar Forceps (**除外**) | 0.779 | +0.00 | −0.00 | −0.00 | **−0.00** | 0.00 | — **厳密中立** |
| ★**Scalpel** (incision) | 0.898 | +1.64 | +1.36 | +0.63 | **+1.21** | 0.42 | ✅有意改善 |
| ★**Skewer** (design) | 0.944 | +0.68 | +1.29 | +0.33 | **+0.77** | 0.39 | ✅有意改善 |
| ★**Syringe** (anesthesia) | 0.571 | +0.53 | +1.63 | +1.48 | **+1.21** | 0.49 | ✅有意改善 |

- **注入 3 術具すべて有意改善**（全 seed 同符号）、rare-4 平均 +0.80pp。**Bipolar は厳密中立**（除外ゆえ bias=0、全 epoch で Δ=0）。
- **非 rare 10 術具はすべて厳密 0.00**（frozen＋非注入 → 完全 no-op。⚠ は top-300 選択の浮動小数点 ε で実質ゼロ）。

### epoch 別軌跡（inj−ctrl mean over seeds, pp）
| tool | ep0 | ep1 | ep2 | ep3 | ep4 | ep5 | 傾向 |
|---|---:|---:|---:|---:|---:|---:|---|
| Bipolar | −0.00 | −0.00 | −0.00 | −0.00 | −0.00 | −0.00 | 完全中立（除外） |
| Scalpel | +0.94 | +1.09 | +1.17 | +1.18 | +1.20 | +1.21 | 単調改善で飽和 |
| Skewer | +0.68 | +0.72 | +0.75 | +0.75 | +0.77 | +0.77 | 即飽和 |
| Syringe | +1.50 | +1.37 | +1.33 | +1.23 | +1.23 | +1.21 | ep0 ピーク後微減 |

## 判定 — **成功基準クリア（phase-排他ゲートは clean に効く）**
- 「注入対象術具が全て有意に inj>ctrl」＋「overall 非劣化」＋「非注入は厳密中立」を **全て満たす**。
- 元 clsbias との差分は決定的: **Bipolar 除外で 3 術具の利得は保存され、Bipolar の −3.14pp が消滅し、
  overall が +0.003（非有意）→ +0.228（✅有意）に転じた**。→ **Bipolar の backfire が overall を引き下げていた**ことの逆説的証明。

### 対比 — clsbias(full rare) / clsbias-PE(phase-排他) / camt-all(可塑)
| tool | clsbias(full, frozen) | **clsbias-PE(phase-排他, frozen)** | camt-all(可塑) |
|---|---:|---:|---:|
| Bipolar | **−3.14 ✅悪化** | **−0.00（除外＝中立）** | +2.65 ✅ |
| Scalpel | +1.25 ✅ | +1.21 ✅ | +0.88 ✅ |
| Skewer | +0.76 ✅ | +0.77 ✅ | +1.11 ✅ |
| Syringe | +1.17 ✅ | +1.21 ✅ | +1.34 —(反転) |
| overall | +0.003 — | **+0.228 ✅** | +0.609 ✅（ただし絶対劣化） |
| overall 絶対 | 非劣化 | **非劣化・init 超え** | init 未超（相対利得） |

## 解釈 — 二つの正解経路（frozen×ゲート / 可塑×広域）
phase→det 注入には **設計の異なる二つの有効解**があると確定した:
- **frozen × phase-排他ゲート（clsbias-PE）**: 検出器を凍結したまま、**注入を phase-排他術具に限定**すれば clean に効く。
  overall は init を超え、非注入は厳密中立、副作用ゼロ。**低コスト・安全・解釈明瞭**だが Bipolar のような phase-spread 術具は救えない。
- **可塑 × 広域（camt-all）**: 検出器を fine-tune すれば query-selective CA が phase-spread な Bipolar すら改善できる（広域）。
  ただし **overall は絶対劣化**（相対利得）し、過学習監視・early-stop が要る。**高コスト・広域・要正則化**。
- 両者は「**per-class phase 特異性 × 注入の直接性 × 検出器可塑性**」の利得則で統一的に説明できる:
  frozen では phase-排他性が必須ゲート、可塑にすれば phase-spread の壁を越えられる。

> ⚠ **誠実性注記**: 本判定は **val** per-class AP。検出には held-out test split（`instances_test.json`, 4265 枚）が**存在する**
> （phase→det は 2026-06-24 に test 評価済）。val は rare 術具の実例が希少で **test の方が信頼できる**（`eval_phase2det_test.py`）
> ため、rare∧工程特異術具の結論は **test 追認まで暫定**（[[val_test_significance_gap]]）。

## 位置づけ・次の一手
- phase→det 探索は本 follow-up で収束: **frozen なら phase-排他ゲート、可塑なら広域 CA**。どちらも 3seed §10.1 で有意。
- **次(③)**: 双方向 §4.6 統合（det→phase と phase→det の同時学習）。①②知見＝**phase-排他ゲート（低コスト安全解）＋検出器可塑性（広域解）**の
  どちらを phase→det 側に採るかを含め設計。残課題: 両系の rare 改善を **test split で追認**。
