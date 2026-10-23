# RESULT — T-2026-10-22-tower-reselect-search-dlsta

## 判定

**partial（G3通過、探索継続中）。** 2026-10-23T17:08:23.930772+09:00時点で40設定中6設定、記録済み39 /260処理完了。GPU1–2で工程塔2番、GPU3–4で検出塔2番を実行中。進捗はlive_status.jsonを参照。
利用者承認により既存15,437枚＋不足1,796枚を使用。改訂preregは177e547f（2026-10-22 06:08:31 JST）。その後の短縮指示で学習後処理のGPU配置と空き判定を改善した。学習条件・本数・順位規則は維持。関連20試験と実機比較通過、検出評価の12指標・15クラスAPと時間ヘッド2構成の結果は旧実行と一致。監視を交代し、検出塔2番の学習は同じPID2607058で継続。証拠scheduler_revision.json・scheduler_handoff_evidence.json。
G4と最終集計は未評価。同期抑止維持。forbidden-checkは別作業の未追跡6ファイルに反応して未通過（本変更外、audit.md参照）。

## 1. 解決された参照

規約とsigmaの原文、索引の値は audit.md「1. 解決された参照」。索引の値と探索との比較は行っていない。
checkpointは195,421,066 bytes、SHA-256 `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824`で正本一致。

## 完了判定と実測

| 項目 | 実測・状態 |
|---|---|
| a | prereg e9f4e3b4、2026-10-22 04:55:13 JST。P4・P13・P14 PASS |
| b | 開始状態・環境・開始前試験を記録。924 passed /6 failed /1 skipped。小規模検証で全rankの実設定を記録 |
| c | 旧0b記録10,708,453,397 bytesを削除し不在確認。隣の可否確認記録は残存 |
| d | 入力の件数・ハッシュが前回記録と全一致。空き758,310,752,256 bytesで150GB超 |
| e | 既知不一致6,001を承認後のハッシュで固定。新manifest17,233枚＝既存15,437＋補完1,796、train10,580 /val1,904 /test4,749、trainの余り4 |
| f〜h | G2通過。検出0/13番の12stepで実更新6/7回、6群の値とclip確認。工程0/1番で2rank、実効batch64/32とweight decay確認。offline W&B別プロセス動作確認 |
| i〜n | 未達。順位なし、testのモデル評価なし、収穫・PR・台帳送信なし |

監査は `experiments/analysis/tower_reselect_search_dlsta/`。不一致内訳は train 3,998 /val 961 /test 1,042。
例: `01_1_0124.jpg` は raw側115,451 bytes、配布側44,300 bytes。両ハッシュは image_overlap_summary.json。
原因調査: 不一致6001対すべてで画素も異なる。raw側は共通のJFIFと品質95相当の量子化表、配布側はLavc形式。JPEG再符号化による別版を示唆するが実行経路は未確定。全47例の近隣比較では同名フレームが最小差。詳細は IMAGE_MISMATCH_ANALYSIS.md。
追加関門試験を含む関連14件、lint、shell構文検査は通過。変更後の全試験は927 passed /6 failed /1 skippedで、失敗名は開始前と同じ（新しい失敗0）。

## 起票者の誤りと未実行検査

P3は判定基準未確定で常にSKIPとなり、学習プロセスの決定性を検査しない。P2は指定なし、P12は解決前提参照なしでSKIP。P9 host_mismatchはWARN。いずれも合格の証明として使わない。

## 逸脱

転送先が~/third_partyだったため照合後にrepoへコピー（元は残存）。再開時の目印不在はスキルの例外で所有情報つきで設置。画像不一致で一度停止したが、利用者承認で契約とpreregを改訂して再開。小規模検証の記録は証拠としてscratchに保持。

## 想定外・UNKNOWN

誰が・いつ・どの処理で別のJPEG版を作ったか、モデル性能への影響、全フレームの時間対応、探索値と順位はUNKNOWN。入力条件は proposed_image_amendment.md の案1を承認・適用済み。

## 送出

PRなし、台帳送信未実施。探索進行中のためtask-releaseは未実行。
