# T1b-CA-MultiToken（真の query-selective・多トークン Phase→Det CA）

**日付**: 2026-07-06 ／ **データ**: 検出 val per-class AP（COCO AP@[.5:.95]）, warm-start=S0-frozen Relation-DETR seed42/123/456
**証跡**: `results.json` / `REPORT.txt` ／ 生 run: `transfer/t1b_camt_seed{42,123,456}_efros/{injected,control}_result.json`（`per_epoch_eval` 付き）
**コード**: `scripts/{train_t1b.py --inject camt --trainable film, run_t1b_camt_3seed_efros.sh, analyze_t1b_clsbias.py --tag camt}`
**モデル**: `models/detectors/relation_detr_phasecrossattn_mt.py`（decoder 層は既存 `relation_decoder_phaseca.py` を無改造で再利用）

## 問い
clsbias（class logit への global per-tool bias・query 非依存）で見えた「phase-排他 rare は改善／Bipolar は工程跨り使用ゆえ悪化」を、
**真の query-selective・多トークン CA** なら克服できるか？ 各 query が「自分に関連する phase token」を **selective に attend** できれば、
Bipolar のような phase-spread 術具も off-signature 抑圧を回避して改善しうる、という仮説（Notion decision 394ee4d4-7777-81e8 の primary 拡張）。

## 方法（clsbias と同一プロトコル・唯一の差は注入機構）
- **camt**: phase 事後(B,9) を P 個の **phase-prototype token**(B,P,embed)=`Embedding(P,embed) * posterior` に展開し、
  各 decoder 層の query→phase cross-attention の KV に渡す（`phase_attn`, out_proj **zero-init**=warm-start 恒等）。
  single-token CA の「1 トークンへのゲート的注意」より、queries が phase を **選択的に attend** できる＝真の query-selective。
- **trainable=film**（検出器凍結・注入層 phase_* のみ 158万 params 学習）＝FiLM 下限・single-token CA・clsbias と同一の注入分離プロトコル。
- **対照 (ctrl)** = `--zero-ctx`（phase context=0 → token=0 → 注入寄与 0）。inj と同一 warm-start・同一学習量(6ep)。
- **judge**: 3-seed paired-σ（§10.1）、**Δ=inj−ctrl@final epoch**。評価は **val per-class AP**。

> ⚠ **誠実性注記**: 検出には held-out test split（`instances_test.json`, 4265 枚）が存在する（phase→det は 2026-06-24 に test 評価済）。本 rare-tool per-class 判定は **val のみ**で test 未検証。val は rare 術具の実例が希少で **test の方が信頼できる**（`eval_phase2det_test.py` の注記）ため、rare∧工程特異術具の結論は **test 追認まで暫定**（[[val_test_significance_gap]]）。

## 結果

### 恒等・非劣化ガード
- init mAP: 全 seed **inj=ctrl（diff=0.0000）**、base(0.7303/0.7292/0.7217)一致 → warm-start+zero-init 恒等 OK（full-val で厳密確認）。
- overall mAP Δ(inj−ctrl) mean **+0.052pp**（pstd 0.109, **非有意**）→ **非劣化**（seed42/123 は inj>ctrl、seed456 はわずかに逆で符号不一致）。

### rare-4 per-class AP Δ（inj−ctrl, 3-seed paired-σ）
| tool | base AP | Δseed42 | Δseed123 | Δseed456 | **mean(pp)** | pstd | 判定 |
|---|---:|---:|---:|---:|---:|---:|:--:|
| ★**Scalpel** (incision) | 0.898 | +1.25 | +1.13 | +0.28 | **+0.89** | 0.43 | ✅有意改善 |
| ★Bipolar Forceps (hemostasis) | 0.779 | −0.45 | +0.15 | −0.76 | −0.35 | 0.38 | — 非有意(符号反転) |
| ★Skewer (design) | 0.944 | −0.20 | +1.17 | −0.20 | +0.26 | 0.65 | — 非有意(符号反転) |
| ★Syringe (anesthesia) | 0.571 | −0.26 | +0.05 | +0.18 | −0.01 | 0.18 | — 非有意(ほぼ0) |

- **有意なのは Scalpel(+0.89pp) のみ**。他 3 術具は seed 間で符号反転＝ノイズ。非 rare も実質中立（⚠ は |Δ|≲0.1pp）。

### epoch 別軌跡（inj−ctrl mean over seeds, pp）
| tool | ep0 | ep1 | ep2 | ep3 | ep4 | ep5 | 傾向 |
|---|---:|---:|---:|---:|---:|---:|---|
| Scalpel | +0.34 | +0.46 | +0.68 | +0.40 | +0.74 | +0.89 | 単調改善（学習的） |
| Syringe | +1.04 | +0.41 | +0.21 | −0.16 | −0.08 | −0.01 | ep0 ピーク→消失 |
| Bipolar | −0.22 | −0.67 | −0.04 | −0.74 | −0.64 | −0.35 | 小さく負で振動 |
| Skewer | +0.13 | +0.15 | +0.59 | +0.23 | +0.32 | +0.26 | 小さく正でノイジー |

## 判定 — **弱い/ほぼ null（有意は Scalpel のみ）／仮説は部分的にのみ支持**
- 成功基準（rare per-class の一貫改善）は **Scalpel 以外満たさず**。overall 非劣化のみ達成。
- 仮説「query-selective なら Bipolar も改善」は **部分的に支持**: Bipolar の悪化は clsbias **−3.14pp → camt −0.35pp（非有意）に大幅緩和**
  （query が phase 適合を選べ off-signature 抑圧を回避）。だが**同時に Skewer/Syringe の利得も消失**し、正味は Scalpel のみ残存。

### clsbias（狙い撃ち per-class bias）との対比（両者 film・frozen 検出器）
| tool | clsbias Δ | camt Δ |
|---|---:|---:|
| Scalpel | +1.25 ✅ | +0.89 ✅ |
| Skewer | +0.76 ✅ | +0.26 — |
| Syringe | +1.17 ✅ | −0.01 — |
| Bipolar | **−3.14 ✅(悪化)** | −0.35 — |
| 有意数 | **3改善+1悪化** | **1改善のみ** |

## 解釈 — frozen 検出器では「表現力の高い CA」＜「直接的 per-class bias」
- camt は clsbias より **穏やか**: Bipolar の抑圧を避ける代わりに、rare 各術具への集中的な利得も薄まる。
  **frozen 検出器では、query 特徴への拡散的な CA delta は per-class AP を一貫して動かせず**、直接 class logit を押す clsbias の方が
  （良くも悪くも）強いレバーになる。表現力（多トークン query-selective）の優位が **検出器凍結という制約下では利得に結びつかない**。
- Scalpel が唯一残るのは、incision の phase 排他性が高く phase→術具の写像が最も学習しやすいため（利得則の phase-排他性次元と整合）。
  Syringe が ep0 ピーク→消失するのは、frozen 検出器では初期の粗い注入が後続 epoch で希釈される（RegionTraj の val 過学習・希釈機序と同系）。
- **含意**: 真の query-selective CA の本領を測るには **trainable=all（検出器同時 fine-tune）** が要る可能性が高い。ただし §3.1/§P2 の
  過学習リスク（rich 注入→ val 過学習→ 汎化崩壊）を伴うため、慎重な正則化・早期停止と **test split（`instances_test.json`）での汎化追認** が前提。

## 位置づけ（P4 clsbias との統一）
det→phase(T1a) の「confidence-weighted per-class appearance が汎化を担う」、phase→det(clsbias) の「phase-排他 rare にのみ有効」、
そして camt の「frozen 検出器では query-selective CA すら Scalpel 以外は動かない」— **いずれも per-class の phase 特異性と、注入の
"直接性 × 検出器の可塑性" が利得を決める**という統一像。frozen×間接(CA) は最も弱い象限。

## 次の一手（optional・要判断）
1. **camt を trainable=all で再走**（検出器同時 fine-tune）— CA の本領検証。過学習監視（early-stop・overall mAP ガード）必須、~10-15h。
2. clsbias を **phase-排他3術具限定**で再走（中断済 follow-up の再開）— Bipolar 除外で clsbias の 3/4→基準充足かを確定、~8h。
3. ここで phase→det 探索を一旦収束させ、双方向 §4.6 の統合（det→phase と phase→det の同時学習）へ。
