# ② clsbias-PE の **test split 追認**（eval-only・3seed）— overall + Scalpel/Skewer は保存、**Syringe は符号反転**

**日付**: 2026-07-08 ／ **データ**: 検出 **test** mAP（`instances_test.json`, 4265img）per-class AP、warm-start S0-frozen Relation-DETR seed{42,123,456}
**証跡**: `test_eval.json`（per-seed inj/ctrl per-class + §10.1 集計 + 整合ゲート記録）
**コード**: `scripts/eval_t1b_test.py`（eval-only, 再学習なし）／ 元 val 実験: `experiments/analysis/t1b_clsbias_pe/`
**checkpoint**: `/tmp/t1b_clsbias_pe_{,zeroctx_}seed{S}/best_t1b.pth`（best-epoch=2, **final は未保存**。frozen 検出器で best≈final を val 実測で確認済）

## 問い
②(clsbias-PE, frozen×phase-排他ゲート) の val 所見 — 注入3術具（Scalpel/Skewer/Syringe）全改善・overall +0.228pp✅・
Bipolar 除外中立 — が **test split でも成立するか**。rare は test の方が信頼できる（[[val_test_significance_gap]]）ため、
確定前の test 追認が残課題だった。checkpoint 残存を利用し **eval-only**（再学習なし・低コスト）で追認する。

## 方法（捏造防止の動作証明＝整合ゲートを前置）
- 残存 checkpoint（inj+ctrl×3seed）を **`T1B_RARE_SLOTS=9,11,13` で同一アーキ再構築** → **strict load**（missing/unexpected=0 を fail-loud 検査）。
- **整合ゲート**: reload したモデルを **val で再評価 → 保存済 best per-class と一致するか**を先に検証。
- ゲート通過後のみ test を評価。Δ_test = inj(real test ctx) − ctrl(zero ctx)。§10.1 は 3seed で `|mean|>pstdev ∧ 全seed同符号`。

### 整合ゲート結果 — **全6 checkpoint が val を bit-exact 再現**（max_per_class_diff = 0.0）
| seed | inj val 再現 | ctrl val 再現 | rare_mask |
|---|---|---|---|
| 42 | 0.732515 = 0.732515 | 0.730294 = 0.730294 | slot{9,11,13}=1（PE 確認） |
| 123 | 0.732269 = 0.732269 | 0.729188 = 0.729188 | slot{9,11,13}=1 |
| 456 | 0.723443 = 0.723443 | 0.721665 = 0.721665 | slot{9,11,13}=1 |

→ **再構築は忠実**（差 0.0）。以降の test 数値は本物の学習済モデルの実測（捏造なし）。

## 結果（test, §10.1, Δ=inj−ctrl, 3seed）
| 対象 | val(final) Δ | **test Δ** | test 有意 | 判定 |
|---|---:|---:|:--:|---|
| **overall mAP** | +0.228pp✅ | **+0.156pp**（pstd0.051, [0.23,0.13,0.11]） | ✅ sig | **保存**（弱まるが有意・正） |
| **Scalpel**（注入,slot9） | +1.21✅ | **+1.48pp**（[1.21,1.61,1.63]） | ✅ sig | **保存✅**（全seed正・堅牢） |
| **Skewer**（注入,slot11） | +0.77✅ | **+1.33pp**（[2.30,0.22,1.47]） | ✅ sig | **保存✅**（全seed正・分散大） |
| **Syringe**（注入,slot13） | +1.21✅ | **−0.49pp**（[−0.12,+0.06,−1.40]） | ❌ 非有意 | **符号反転❌**（val限定 artifact） |
| **Bipolar**（除外,slot0） | −0.00 | **−0.00pp**（[0,−0,−0]） | ❌ | 厳密中立（ゲート設計通り） |

- **test は難易度が高い**: 絶対 mAP は inj≈0.507 / ctrl≈0.506（val≈0.727）で **val→test 約 −22pp** 低下。ただし phase→det の主張は Δ(inj−ctrl) の符号・有意性で評価する。

## 判定 — **主張は部分的に test 再現：overall と Scalpel/Skewer は堅牢、Syringe は val 限定**
- **overall +0.156pp（sig✅）**: 注入が overall を非劣化どころか有意に押し上げる、という②の中核主張は **test で保存**（val +0.228 → test +0.156、弱まるが全seed正・有意）。
- **Scalpel/Skewer（注入2/3）が test で有意保存**: いずれも val→test で符号一致・§10.1 有意。**phase-排他ゲートによる直接 bias 注入が rare 工程特異術具を改善する、という機序は test でも支持**。
- **Syringe（注入1/3）は符号反転**: val +1.21 → test −0.49（非有意・符号不一致）。**val 限定の artifact** と判断。Syringe は val AP が3術具中最低（0.579）で分散が大きく、val の見かけ改善が test に載らなかった。
- **Bipolar 除外の厳密中立が test でも成立**: ゲート（slot{9,11,13} のみ注入）が意図通り機能。

## 解釈・位置づけ
②の「frozen×phase-排他ゲート」安全解は、**overall 押し上げと 2/3 注入術具の改善が test で再現**し、機序（工程特異な per-tool bias）の妥当性を test 追認できた。
一方 **Syringe の符号反転は [[val_test_significance_gap]] の警告が的中した実例**であり、rare-class の val 単独改善は test 追認まで暫定という運用則を裏づける。
①(camt-all, 可塑×広域CA) は checkpoint 消失で eval-only 不可 → test 追認には再学習が必要（別途判断）。

> ⚠ **誠実性**: checkpoint は best-epoch（final 未保存, frozen で best≈final を val 実測確認）。整合ゲートで val を bit-exact 再現し再構築忠実性を証明済。
> 数値は全て実測（捏造なし）。Syringe 反転・overall 減衰は隠さず報告。①の test 追認は未実施（要再学習）。
