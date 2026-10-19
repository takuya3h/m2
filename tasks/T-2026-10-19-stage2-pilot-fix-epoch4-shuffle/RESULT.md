# 結果 — T-2026-10-19-stage2-pilot-fix-epoch4-shuffle

**非公式の測定。関門の判定と設計の判断に使わない。** 前回の予備測定（T-2026-10-18-stage2-pilot-folda、PR #235）の値を、学習を 4 epoch 終えた
時点の状態（最良の回を選ばない）で出し直し、全型に入れ替えの腕（予測-noCF と同じ値の集まりで、フレームとの対応だけを壊した腕）を足した。
全値と §5.2 の記述は `experiments/analysis/stage2_pilot_fix/REPORT.md`。命令と出力は `audit.md`（以下「audit NNN」は行番号）。

**status: 【最後に】。** G1〜G3 は pass。DP 26 本（回し直し 21・入れ替え 5）、PD 12 本と P2F の評価 1 本がそろった。DP の回し直しは前回の
epoch 1〜4 と完全一致した。P3 の予測-CF・正解予測-CF は利用者の承認で別ホスト bengio で回した（逸脱）。【最後に: 要点 2〜3 行】

## 1. 解決された参照

| 記載 | 解決先 |
|---|---|
| `contract.inject_verbatim` | `context/conventions.md` の 7 節（prohibitions、issuer_cautions、env_p0、folds、split、eval_recipe、det_groups）を原文のまま適用（audit 38-41） |
| `contract.conventions_rev` | 起票時 `4d42edb9` → 前回と同じ読み（`git log -1 -- context/conventions.md`）で実測 `b12eda6c`。内容は同一。差し替え（amendments 1 件目、audit 99-112） |
| `meta.created_from` | runindex 起票時 `31af81e7` → 実測 `63ae65da`（内容は同一、差し替え）。件数 1961 / 750 / 1506 は一致（audit 99-112） |
| `inputs.denominator` / `sigma_policy` / `frozen_source` | 契約に無し。前回の塔単独の値（工程 0.7762186、検出 0.7273450）を Task B で再現した |

## 2. 関門

| 関門 | 判定 | 実測 |
|---|---|---|
| G1（A の後） | **pass** | 分岐 `feat/stage2-pilot-fix-epoch4-shuffle`、起点 `origin/phase0` = `5a8baa79`、phase0 に `scripts/stage2pilot/` 28 ファイル、本契約以外の compute プロセス 0 件、空き 1,681 GB、失敗の名前 6 件（audit 43-121） |
| G2（B の後） | **pass** | 前回の信号 21 本と記録がすべて一致。工程 Jaccard 0.7762186・accuracy 0.8712871、検出 mAP 0.7273450・標的群 0.7950748・陰性対照群 0.6726632。前回との差は 0.0（標的群は −1.1e-16）（audit 123-180） |
| G3（C の後） | **pass** | 固定の長さが最後の epoch の状態を結果にし、既定の集計が前回の report.json を同値で再現（comparisons の並びだけが違う）、入れ替えた信号は値の集合を保ち対応だけを壊す、入れ替えの腕の学習前の出力が塔単独と差 0.0、test の動画との共通 0 件（audit 182-287） |

## 3. 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐・起点・前回の道具・退避 0 件・compute プロセス 0 件・空き 1,681,381,457,920 B・失敗の名前 6 件（audit 43-121） | 目印の bash を 1 件拾い、zsh 指定と存在しない exe で 0 件（audit 68-75） |
| b | 材料 | 信号 21 本の sha256 が前回の記録と一致、交差適合版は半分ずつから組み直しても一致、DP の history.json 63/63（audit 125-165） | 1 バイト変えた複製で不一致。存在しない run の名前で 0 件（audit 140-141, 148） |
| c | 塔単独の再現 | 工程・検出とも差 0.0（audit 167-176） | 別の時間ヘッドで Jaccard 0.6379、seed 123 の検出塔で mAP 0.7289 |
| d | 固定の長さ | PD・DP とも最後の epoch の状態が結果（試走で、前の epoch の方が高くても選ばない）。既定の集計は前回の report.json と同値（audit 184-253） | 作り物の記録（最良が epoch 1・2）から epoch 3・4 の値を取り、epoch 2 で止まった記録では None（audit 248-253） |
| e | 入れ替え | 値の集合が同じ、対応が変わった割合 train 1.000 / val 0.9987、同じ動画から来た割合 train 0.115 / val 0.556（audit 222-236） | 恒等の並べ替えで 0.0、値を一つ変えた写しで集合の一致 False |
| f | 入れ替えの腕の恒等性 | PD 4 構成・DP 5 型とも学習前の出力の差 0.0（audit 254-275） | 最後の層を N(0, 0.05²) にすると変わる（PD score 差 0.045〜0.94、DP ロジット差 0.14〜2.05） |
| g | 再計算の表 | 前回の 85 本の最良の値と 4 epoch 目の値（REPORT）。無い run は PD 8 本で理由つき（audit 144-165, 289-299） | 前回の最良の値は epoch ごとの記録の最大と全件一致（PD 20、DP 63） |
| h | 回し直し | DP 21 本は前回の epoch 1〜4 と完全一致。PD 8 本の再現の差は【最後に】 | 回し直した run の学習前の値はすべて塔単独と同値【最後に P3 を確かめる】 |
| i | 入れ替えの腕 | DP 5・PD 4・P2F 評価 1。【最後に】 | 入れ替えた信号の sha256 は元と違い、並べ直した値の要約値は一致（audit 230-233） |
| j | 記述 | REPORT §2（§5.2 の規則）【最後に】 | 表の Δ を各 run の記録から計算し直して食い違い 0 件（【最後に】件） |
| k | 中間記録 | DP の全腕（40a8146e）、P2F（84056eb5）、P1-W1（c0f11094）、P1-W2（bb0bf533）、【最後に P2L・P3】を push | push した commit が分岐の先頭の祖先【最後に確かめる】 |
| l | test 不使用 | 【最後に】 | `--inject 04` で共通 1 件 |
| m | 書き込みと試験 | 【最後に forbidden-check と試験】 | 同じ道具が本契約の新しいファイルを変更として拾う【最後に】 |
| n | PR | #240、base phase0、【最後に Draft を外す】 | 分岐名 `feat/stage2-pilot-fix-epoch4-shuffle` |

## 4. 実測

【最後に: 型ごとの予測-noCF と正解の Δ空・Δ入替・Δ前回の要約表（DP は Jaccard、PD は標的群 AP と overall mAP）】

- 塔単独の再現: 工程 Jaccard 0.7762185528074379 / accuracy 0.8712871287128713、検出 mAP 0.7273450248398429（audit 167-176）
- 入れ替え: 対応が変わった割合 train 1.000000 / val 0.998680、同じ動画から来た割合 train 0.115357 / val 0.556436（audit 226-229）
- 回し直しの再現: DP は差 0（21 本）。PD は epoch ごとの val mAP の差の最大 【最後に】
- 1 本の所要: DP は 10 秒前後（読み込み込み）。PD は andrew で 1 枚 2 本のとき 1 epoch 約 47 分（P1）、P3 は 1 本 2.6 it/s。【最後に壁時計の範囲】
- GPU 1 枚に 3 本目を足す試し: 合計の速さの伸びは GPU 0 で約 3%、GPU 1 で 0（audit 332-347）

## 5. 起票者の誤り

1. **asymmetric_comparison**: SPEC §1 の「P1-W1 の正解の標的群 AP の差は最良の回で +0.0195、最後の回で +0.0087」の後者は、正解の epoch 3 と空の epoch 2
   （空は前回の止め方で epoch 2 で止まった）の差だった。同じ epoch どうしでは epoch 2 で +0.0195、今回の 4 epoch 目どうしで +0.0197。欠陥 A の大きさを長さの違いで見積もっていた
2. **check_does_not_check**: 完了判定 f（入れ替えの腕の学習前の出力が塔単独と一致）は、零初期化の界面ではどんな信号を入れても成り立つ。入れ替えが正しく行われたかは確かめない
   （入れ替えそのものは e と i が確かめる）
3. **asserted_without_measuring**: SPEC §3 は split 全体で入れ替えれば「動画単位の情報を残さない」としたが、val は動画 2 本のため、入れ替えた後も 55.6% のフレームが同じ動画の信号を受け取る
4. **asserted_without_measuring**: `meta.created_from.runindex_commit` と `contract.conventions_rev` に、Task A-6 の読み（その経路の最新の commit）と違う値（起票時の phase0 の先頭）が書かれ、内容が同一でも差し替えが要った
5. 【最後に: ほかに見つかれば】

## 6. 逸脱

- **ホスト（利用者の承認）**: P3 の予測-CF と正解予測-CF を bengio で回した（amendments 2・3 件目、audit 348-384）。bengio は検出器の仮想環境の python のリンク先が無く、
  Relation-DETR のソースも 23 件違ったため、andrew の中身を別の場所に置いて参照させ、仮想環境を uv の 3.11.16 に向け直した（bengio の audit_bengio.md）
- **実行者の判断**: GPU 1 枚に 3 本目を 1 回だけ足して速さを測った（GPU 0 で P1-W2 入れ替え、GPU 1 で P3 予測-noCF。伸びが 1 割に届かず、それ以上は足さない）
- **実行者の誤り**: PD の試走の後処理が群の AP の None を書式で落とした（直して後処理だけ回し直した、audit 207-212）。
  andrew で P3 の 4 本を起こしかけた命令が途切れ、正解と予測-CF の 2 本が学習の前で止まった（フォルダは本契約の置き場へ移した、audit 371-377）
- 道具: `train_t1b.py`・`dp_train.py`・`run_pd_fix.sh` に引数と置き場の切り替えを足した（既定は変えない。試験で固定）
- 前回の `aggregate.py` の comparisons の並びは実行ごとに変わる（set の反復順。値は同じ）。直していない
- 【最後に】

## 7. 想定外・UNKNOWN

- 回し直さない PD の 8 本（P1-W1 の正解・予測-CF・正解予測-CF、P1-W2 の予測-noCF・正解・予測-CF、P2L の空・予測-CF）の動画ごとの 4 epoch 目の値:
  epoch 3 の予測と重みが残っていない（前回の最良が epoch 3 でない）
- 【最後に】

## 8. 送出

- PR: #240（https://github.com/takuya3h/m2/pull/240）
- `make task-report`: 【最後に】
