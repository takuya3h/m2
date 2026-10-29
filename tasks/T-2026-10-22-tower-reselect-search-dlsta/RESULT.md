# RESULT — T-2026-10-22-tower-reselect-search-dlsta

## 判定

**pass。全探索・集計・索引登録・最終検証を完了。**
2026-10-29 01:18:38 JSTに全40設定・260処理を完了。G1〜G4 pass、発散0、上限36への到達0。GPU0使用0、test評価0。探索順位を記録し、処方の選定は行っていない。

## 完了判定

| # | 実測 |
|---|---|
| a | 改訂prereg177e547f、2026-10-22 06:08:31 JST。学習開始06:34:57より先。P4/P13/P14 pass |
| b | start/env/開始前試験を保存。全rankの実設定を別記録 |
| c | 旧0bを削除前10,708,453,397bytes、不在確認。隣の可否確認記録は残存 |
| d | 原画像とcheckpointのハッシュを照合。開始時空き758,310,752,256bytes |
| e | manifest17233枚=既存15437+補完1796。train10580/val1904/test4749、train余り4。画像照合82回pass |
| f | 検出の全点・全rankで6群の値とclip一致。既存学習ソースとthird_partyは不変 |
| g | 検出20、工程backbone20・特徴20・時間head200の260処理。点番号と値を全件照合 |
| h | metrics/posthoc/history/optimizerの全件照合。最終標的群APを原記録から補完。UNKNOWNとメタデータの制約は下記 |
| i | results_ptower.csv・results_dtower.csv各20行。順位変更・同点コピーの対照pass |
| j | 監視上のGPU0所有プロセス0。特徴はtrain+val12484枚でtest動画なし |
| k | checkpoint・特徴はrepo外。公開最大image_input_lock.json=5,660,823bytes |
| l | 対称性2表34行、UNKNOWN0。P13/P14破損コピーはFAIL。異常は下記 |
| m | runindexに本契約260行、経路集合一致。935 pass/6 fail/1 skip、新しい失敗0。開始時の確定起点で隔離forbidden-check pass、禁止ファイル追加対照はFAIL |
| n | PR #267、base phase0、feat/tower-reselect-search-dlsta、Draftではない |

## 実測

全てdlsta・fold A・seed42。工程の主指標は10時間headの最大val macro Jaccard、検出はval mAP。値の差は記録であり効果の判定に使わない。

| 塔 | 順位 | 点 | 主指標 | 0番との差 | 設定 |
|---|---:|---:|---:|---:|---|
| 工程塔 | 1 | 6 | 0.7301713551 | +0.0722342154 | lr 3.14e-05、wd 0.00057、時間ヘッドC/6/平滑0.15 |
| 工程塔 | 2 | 8 | 0.7214485635 | +0.0635114238 | lr 0.000113、wd 0.00152、時間ヘッドC/8/平滑0.15 |
| 工程塔 | 3 | 10 | 0.7209184926 | +0.0629813529 | lr 8.07e-05、wd 0.000128、時間ヘッドC/8/平滑0.15 |
| 検出塔 | 1 | 12 | 0.7373795627 | +0.0184642625 | lr 0.000307、wd 0.000337 |
| 検出塔 | 2 | 5 | 0.7350900855 | +0.0161747853 | lr 0.000219、wd 0.0124 |
| 検出塔 | 3 | 15 | 0.7348208695 | +0.0159055693 | lr 5.28e-05、wd 0.0234 |

0番は工程0.6579371397で16位、検出0.7189153002で19位。点の全表は `experiments/analysis/tower_reselect_search_dlsta/results_ptower.csv` と `results_dtower.csv`、全headはpoint_records.json。

一本の壁時計は工程1.97〜5.38h（平均3.71h、抽出とheadを含む）、検出7.79〜16.63h（平均11.99h）。最大確保は工程13.85GiB、検出12.53GiB。環境と二枚の道の記録はenv_dlsta.json・各rankの実記録。検出のepochは0始まり、工程は1始まり。

予測一は一致（両塔0番top3外）。発散0・上限到達0のため、予測二・三の偏りは評価不能。上位3件が全て上限へ達する異常も無い。

## 起票者の誤りと未実行検査

P3は決定性を検査せず常にSKIPのため、全rankの実値を別記録。P2/P12もSKIP、P9 host_mismatchはWARN。詳細と解決した参照の原文は [audit.md](audit.md)、最終監査は同ファイル587行以降。

## 逸脱

画像の既知6001対の差を利用者承認で許容し、既存画像を維持して補完1796枚を参照。preregを学習前に改訂。利用者の短縮指示でGPU配置と空き判定を改善し、実機で結果一致を確認。進行中の学習を再実行せず監視だけ交代。小規模対照はscratchに保持。

## 想定外・UNKNOWN

JPEG別版の生成経路と性能への影響は未特定。探索値は最大を取った値で上振れを含み、他ホストとは比較していない。索引のhost=null（rawはdlsta）、検出14有限クラスのkind=unknown、時間headのper-class誤分類F1は既存収穫器の制約で、原本はAP/Jaccardとして読める。head optimizer_recordのeffective_batchはbackboneの継承値であり、headの単位は動画1本。学習条件や一次指標は変更していない。

## 送出

PR #267。台帳送信と同期抑止解除の実測はaudit.mdと最終応答へ記録する。
