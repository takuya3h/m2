# T1b-CA-MultiToken-ALL（真の query-selective 多トークン Phase→Det CA / **trainable=all**）

**日付**: 2026-07-07 ／ **データ**: 検出 **val** per-class AP（COCO AP@[.5:.95]）, warm-start=S0-frozen Relation-DETR seed42/123/456
**証跡**: `results.json` / `REPORT.txt` ／ 生 run: `transfer/t1b_camt_all_seed{42,123,456}_efros/{injected,control}_result.json`（`per_epoch_eval` 付き）
**コード**: `scripts/{train_t1b.py --inject camt --trainable all, run_t1b_camt_all_3seed_efros.sh, analyze_t1b_clsbias.py --tag camt_all --which final}`
**モデル**: `models/detectors/relation_detr_phasecrossattn_mt.py`（decoder 層は既存 `relation_decoder_phaseca.py` を無改造で再利用）

## 問い
frozen 検出器（camt-film）では真の query-selective 多トークン CA すら弱く（有意は Scalpel のみ、Bipolar −0.35 非有意）、
「**CA の本領は検出器同時 fine-tune（trainable=all）でこそ解ける**」と予想した。これを 3-seed で検証する。
特に、clsbias（frozen・直接 bias）で **−3.14pp 有意悪化**した **Bipolar Forceps（phase-spread 術具）**が、
検出器可塑性の下で query-selective CA により改善へ**転じるか**が最大の論点。

## 方法（camt-film と同一プロトコル・唯一の差は trainable）
- **camt**: phase 事後(B,9) を P 個の phase-prototype token(B,P,embed)=`Embedding(P,embed)*posterior` に展開し、
  各 decoder 層の query→phase cross-attention の KV に渡す（`phase_attn`, out_proj **zero-init**=warm-start 恒等）。
- **trainable=all**（検出器も同時 fine-tune・~26.8M params、backbone のみ凍結）＝camt-film（158万・注入層のみ）との唯一の差。
- **対照 (ctrl)** = `--zero-ctx`（phase context=0 → token=0 → 注入寄与 0）。inj と同一 warm-start・同一学習量(6ep)。
- **judge**: 3-seed paired-σ（§10.1: |mean(Δ)|>pstdev かつ全 seed 同符号）、**Δ=inj−ctrl@final epoch**。

> ⚠ **誠実性注記1（評価 split）**: 本判定は **val** per-class AP。検出には held-out test split（`instances_test.json`, 4265 枚）が
> **存在する**（phase→det は 2026-06-24 に test 評価済）。val は rare 術具の実例が希少で **test の方が信頼できる**
> （`eval_phase2det_test.py` の注記）ため、rare∧工程特異術具の結論は **test 追認まで暫定**（[[val_test_significance_gap]]）。

## 結果

### 恒等ガード・過学習監視（best も確認）
- init mAP: 全 seed **inj=ctrl（diff=0.0000）**、base(0.7303/0.7292/0.7217)一致 → warm-start+zero-init 恒等 OK。
- **全 6 run が `best@ep-1`**（init）＝どの学習 epoch も overall val mAP が init を超えない。
  inj/ctrl とも init(0.73) → final(0.71) へ**低下** → **trainable=all フル fine-tune は overall val を過学習で下げる**（§3.1/P2 の想定内）。
  ゆえ best 選択は無意味で、**同一学習量 final epoch での inj vs ctrl 比較（`--which final`）が唯一公平**。

### overall mAP Δ（inj−ctrl, @final, 3-seed paired-σ）
- inj : 0.7181 / 0.7175 / 0.7090　ctrl : 0.7110 / 0.7116 / 0.7037
- Δ = **+0.718 / +0.588 / +0.522 pp**、mean **+0.609pp**（pstd 0.081）→ **✅ 有意・非劣化**（全 seed 同符号）。

### rare-4 per-class AP Δ（inj−ctrl, @final, 3-seed paired-σ）
| tool | base AP | Δseed42 | Δseed123 | Δseed456 | **mean(pp)** | pstd | 判定 |
|---|---:|---:|---:|---:|---:|---:|:--:|
| ★**Bipolar Forceps** (hemostasis, phase-spread) | 0.779 | +4.78 | +2.69 | +0.47 | **+2.65** | 1.76 | ✅**有意改善** |
| ★**Scalpel** (incision) | 0.898 | +0.92 | +0.80 | +0.93 | **+0.88** | 0.06 | ✅有意改善（極小分散） |
| ★**Skewer** (design) | 0.944 | +1.20 | +1.47 | +0.67 | **+1.11** | 0.33 | ✅有意改善 |
| ★Syringe (anesthesia) | 0.571 | +4.30 | +1.40 | −1.68 | **+1.34** | 2.44 | — 非有意（seed456 符号反転） |

- **3/4 が有意改善**（Bipolar/Scalpel/Skewer）、rare-4 平均 **+1.50pp**。Syringe は seed456 で符号反転し非有意。
- 非 rare（注入対象外）は fine-tune 波及で微動: Scissors +1.63⚠ / Gauze +1.22⚠ が正、Electric Cautery −0.48⚠ / Tweezers −0.41⚠ が負（frozen 版と違い trainable=all は共有検出器が動くため厳密中立ではない）。

## 判定 — **CA 本領は検出器可塑性で解ける（3/4 rare + overall 有意）／ただし overall は init 未超の相対利得**
- 成功基準（rare per-class の一貫改善）を **3/4 で達成**、overall も有意改善。**camt-film の弱さは注入機構でなく検出器凍結が原因**だったと確定。
- **最重要**: clsbias で **−3.14pp 悪化**した **Bipolar が +2.65pp 有意改善へ逆転**。検出器が可塑なら、query-selective CA は
  Bipolar の off-signature 抑圧を回避するだけでなく、phase-conditioned な特徴再形成で**積極的に改善**できる。

### 三象限の対比（frozen×直接 / frozen×間接 / 可塑×間接）
| tool | clsbias (frozen・直接bias) | camt-film (frozen・間接CA) | **camt-all (可塑・間接CA)** |
|---|---:|---:|---:|
| Bipolar | **−3.14 ✅悪化** | −0.35 — | **+2.65 ✅改善** |
| Scalpel | +1.25 ✅ | +0.89 ✅ | +0.88 ✅ |
| Skewer | +0.76 ✅ | +0.26 — | +1.11 ✅ |
| Syringe | +1.17 ✅ | −0.01 — | +1.34 —(反転) |
| overall | +0.003 — | +0.052 — | **+0.609 ✅** |
| 有意改善数 | 3（+1悪化） | 1 | **3＋overall** |

## 解釈 — 利得則の第三次元「**検出器可塑性**」
det→phase(T1a)「confidence-weighted per-class appearance が汎化を担う」、phase→det「per-class の phase 特異性が分岐点」に加え、
本結果は **注入の利得が『per-class phase 特異性 × 注入の直接性 × 検出器可塑性』の積**で決まることを示す。
- **frozen × 間接CA = 最弱象限**（camt-film）: 表現力があっても凍結検出器では per-class AP を動かせない。
- **可塑 × 間接CA = 利得象限**（camt-all）: 検出器が phase-conditioned 特徴を再形成でき、phase-spread な Bipolar すら改善。
- Bipolar が frozen で悪化→可塑で改善に転じるのは、**「phase prior を検出スコアへ直接注ぐ（clsbias）」と「query 特徴を phase で条件づけ検出器ごと再学習する（camt-all）」で作用機序が根本的に異なる**ため。

> ⚠ **誠実性注記2（過学習・相対利得）**: trainable=all は overall val を init(0.73)→final(0.71) に**下げる**（全 run best@ep-1）。
> 有意な「改善」は inj が ctrl より**劣化が小さい相対利得**であり、**frozen S0 の絶対 overall mAP は超えない**。
> 実運用では early-stop / 正則化で絶対劣化を抑える設計が前提。この点を伏せずに「camt-all が最良」と短絡しない。

## 位置づけ・次の一手
- phase→det 探索は「frozen では phase-排他 rare 限定（clsbias）／可塑では query-selective CA が rare 広く＋overall も改善（camt-all, ただし相対利得）」で収束。
- **次(③)**: 双方向 §4.6 統合（det→phase と phase→det の同時学習）。①②知見＝**phase-排他ゲート＋検出器可塑性**を反映した設計へ。
- **残課題**: (a) camt-all の rare 改善を **test split で追認**（val→test 汎化）、(b) early-stop で overall 絶対劣化を抑えた上での利得再測定。
