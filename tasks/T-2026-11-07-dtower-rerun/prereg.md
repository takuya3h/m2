# 事前登録 — T-2026-11-07-dtower-rerun

学習開始より前に commit する。commit 後は変えない。変更は `meta.amendments` に追記する。

## 1. 問い（記録のため。判定は置かない）

探索の 1 位（12 番。学習率 3.07e-4、縮みの量 S 4.976e-3、刈り込み max_norm 0.059。`experiments/analysis/tower_reselect_search_dlsta/results_dtower.csv` の rank 1）の設定と、batch の探索（T-2026-11-06-dtower-batch-search、PR 299）で決めた GPU ごとの batch 6（2 枚で実効 12）で、5 折り × seed 42・123 の 10 本を andrew で学ぶ。0 番（現行の処方。学習率 1e-4、weight decay 1e-4、max_norm 0.1）も同じ batch と S の換算で 10 本学ぶ。

- 12 番の seed 42 の塔を折りごとに凍結し、Stage 2 以降の検出塔として使う。**選定は行わない**（カード五版 §7 の 4。採用は性能で決めない。F 2026-10-17）
- 記録: 12 番と 0 番の 10 本の平均の差（真の差と読まない）、折りごとの差、seed 間の SD（診断）
- 利用者の決定（2026-11-06、起票の会話。F 2026-11-06）: 回し直しは上位 1 件だけ、0 番は回す、seed 2 種は残す、カードの問い #1 は置かない、S を揃える、batch の探索を先に行う。batch の探索の結果（PR 299）: b6

## 2. 設計

### 2.1 水準（後から足さない）

| 点 | 学習率（本体の群） | 縮みの量 S | weight decay（batch 2 の値 → batch 6 の換算） | max_norm | 出所 |
|---|---|---|---|---|---|
| 12 番 | 3.07e-4 | 4.976e-3 | 3.37e-4 → 1.01058e-3 | 0.059 | 探索の rank 1（results_dtower.csv）。換算は PR 299 の prereg §2.1 と実測（audit:186-189） |
| 0 番 | 1e-4 | 4.81e-4 | 1e-4 → 2.998753e-4 | 0.1 | 探索の 0 番（results_dtower.csv の point 0。現行の処方 `stage1_dtower_r2`）。換算は同じ規則 |

- S の定義はカード §14（S = 学習率 × weight decay × 更新の歩数。歩数は 20 epoch 相当。本体の群）。batch 6 では 1 epoch が 802 歩（PR 299 の実測。train 9,620 枚、2 枚、drop なし）なので、weight decay は batch 2 の値 × 2,405 ÷ 802。実行者は実際の 1 epoch の歩数（DataLoader の長さ）から換算し直し、上の値と照合する。食い違えば実測の歩数の値を使い、記録する
- 折りが変わると train の枚数が変わる（各折りの train は動画 10 本で、枚数は折りごとに違う）。**歩数は折りごとに実測し、weight decay は折りごとに換算する。** 折り A 以外の換算の値は本契約で初めて測るので、各 run の記録に残す
- backbone と線形射影の群は学習率 0.1 倍（探索と同じ）。fp16、2 枚の道（accelerate、2 プロセス）、`NCCL_P2P_DISABLE=1`、presets.detr、COCO 1x の初期化、`num_workers` 4、`pin_memory` True。すべて batch の探索と同じ
- 収束規則: 停滞 4 epoch で学習率 0.1 倍を一度、再停滞 4 epoch で打ち切り、上限 36、val mAP で見る。checkpoint は val mAP が最良の epoch。探索と batch の探索と同じ（収束規則の見直しは別の決定であり、本契約では変えない）
- 立ち上げ: 上流の既定（第 0 epoch に最大 1,000 歩の線形）。batch 6 では第 0 epoch が 802 歩で立ち上げが 801 歩で終わる（PR 299）。変えない。何歩で終わったかを各 run で記録する
- seed 42 と 123。各点 × 5 折り × 2 seed = 20 本
- 2 枚を占有して 1 本ずつ順に回す。順番は 12 番の折り A → E の seed 42、次に seed 123、次に 0 番の同じ順。12 番の seed 42 の 5 本（凍結する塔）が先に揃う

### 2.2 固定する項目

探索の prereg §2.2 と batch の探索の prereg §2.2 のとおり（初期化、入力解像度と増強、収束規則、optimizer、backbone と線形射影の倍率、精度、フレーム集合）。ホストは andrew（A6000 × 2、電力の上限 300 W）。

### 2.3 測る量

- 主指標: 各 run の val mAP（`conventions#eval_recipe` の NMS-free の規約）。checkpoint の値
- co-primary: val 標的群 AP。陰性対照群 AP も記録（`conventions#det_groups`）
- クラス別 AP（`per_class_ap.json`）、動画ごとの val mAP

### 2.4 test の扱い（副次。`conventions#folds` の val と test の重なりの規律）

- 各 run で、学習の後に checkpoint で**その折りの test 3 本を一度だけ**評価し、`eval_test.json` に記録する（二周目 `stage1_dtower_r2` と同じ形）
- 各折りの val 2 本は他の折りの test に現れる（09・10 → E、02・08 → C、06 → D、12 → E、04・05 → A、07 → A、15 → D）。この重なりを報告に明記する
- **副次の値**: val に一度も入らない 5 動画（01・03・11・13・14）だけで集計する。各動画の値は、その動画を test に持つ折りのモデル（01・03・14 は折り B、11 は折り C、13 は折り D）が出す。集計は、5 動画の予測を一つの集合にまとめて評価する mAP と、動画ごとの mAP の両方を、点ごと・seed ごとに記録する
- 副次の値は判定・関門・選定のどれにも使わない。本契約に判定は無いが、12 番と 0 番の差を test で読まない

## 3. 記録の規則（判定は無い）

1. 点ごとに 10 本の val mAP の平均と、折りごとの 2 本の平均を出す
2. 12 番 − 0 番 の差を、10 本の平均と折りごとに書く。**真の差と読まない**（12 番は折り A の val で選ばれた点であり、折り A の値は上振れする。他の 4 折りの差は選択に使っていない値どうしの差）
3. seed 間の SD（点ごと・折りごとの 2 本の差の絶対値、および 10 本からの推定）を診断として記録する
4. 折り A の 12 番の 2 本と batch の探索の b6 の 2 本（0.7385・0.7328）の差を記録する。同点幅 0.0076（PR 299 の prereg §3。`baselines/dcoco_foldA/dcoco_foldA@val` の mAP_sstd 0.0037965 の 2 倍）の内かを書く。同じホスト・同じ設定・同じ seed なので、差は非決定性の目安
5. 折り B〜E の値は、二周目の 0 番の塔（`stage1_dtower_r2/dcoco_fold{B,C,D,E}_seed42`。val mAP 0.41〜0.51）と並べて記録する。処方と batch が違うので処置の差として読まない。折りで値が大きく違うことを限界に書く
6. 凍結する塔: 12 番 seed 42 の 5 本。checkpoint の経路・sha256・checkpoint の epoch・val の値を一覧にする。登録（`scripts/stage2pilot/common.py` の要約値の差し替えなど）は本契約で行わない（別の契約）

### 3.1 予測（当たり外れを F に積む）

1. 12 番の 10 本の val mAP の平均は 0 番の 10 本の平均より大きい（探索の折り A では +0.0185）
2. 折り A の 12 番の 2 本は、batch の探索の b6 の 2 本と差の絶対値が 0.0076 以内
3. 折り B〜E では 12 番 − 0 番 の差が折り A より小さい（折り A は 12 番を選んだ折りで上振れする）
4. 発散・非数・溢れは無い（学習率と batch は探索と batch の探索で通った値）

### 3.2 読みの規則

- 値は処方の効果として読まない。採用は性能で決めない
- dlsta の探索の値（12 番 0.7374、0 番 0.7189）と並べない（ホストが違う。F 2026-10-21）
- 折りをまたいで val を使い回さない。各折りの checkpoint はその折りの val で選ぶ

## 4. 対称性の表（conventions#symmetry。UNKNOWN が残る間は起票しない）

**同じ塔の設定どうし（腕1 = 12 番、腕2 = 0 番。D\*-COCO、GPU ごとの batch 6、andrew）**

| 条件 | 腕1 | 腕2 | 判定 | 理由 |
|---|---|---|---|---|
| 初期化: ImageNet 分類 | あり | あり | 揃える |  |
| 初期化: COCO 検出 | Relation-DETR R50 COCO 1x | 同じ | 揃える | 同じ checkpoint（要約値を記録） |
| 初期化: 中立 SSL | なし | なし | 揃える |  |
| 初期化: in-domain の教師 | box、収束規則まで | 同じ | 揃える |  |
| 凍結範囲 | stem のみ（backbone の BN は凍結） | 同じ | 揃える |  |
| 入力解像度と切り出し（残る割合） | 学習時 短辺 480〜800 の乱択、評価 1333×749、100% | 同じ | 揃える |  |
| 前処理・増強 | presets.detr | 同じ | 揃える |  |
| 教師の種類と密度 | box とクラス、折りごとの train の全フレーム | 同じ | 揃える | 枚数は折りで違うが腕で同じ |
| データと折り | 5 折り A〜E | 同じ | 揃える |  |
| epoch と上限への張り付き | 収束規則（val mAP）、上限 36 | 同じ | 揃える | epoch 単位 |
| 学習率 | 3.07e-4（backbone と線形射影 0.1 倍） | 1e-4（同じ倍率） | 意図的に変える | 設定の差そのもの（探索の 1 位と現行） |
| weight decay | 1.01058e-3 | 2.998753e-4 | 意図的に変える | 設定の差そのもの。どちらも S を batch 6 の歩数で換算 |
| 縮みの量 S | 4.976e-3 | 4.81e-4 | 意図的に変える | 設定の差そのもの |
| 勾配の刈り込み | max_norm 0.059 | 0.1 | 意図的に変える | 設定の差そのもの |
| 実効 batch | 12（GPU ごと 6） | 同じ | 揃える | batch の探索の結果（PR 299） |
| 1 epoch の更新回数 | 折りごとの枚数 ÷ 12 | 同じ | 揃える | 同じ折りで同じ |
| 立ち上げ | 上流の既定（最大 1,000 歩） | 同じ | 揃える | 801 歩で終わる（PR 299） |
| 数値精度 | fp16 | 同じ | 揃える |  |
| 決定性 | 非決定 | 同じ | 揃える | seed 2 本の揺れに含まれる |
| ヘッドの容量 | Relation-DETR の既定 | 同じ | 揃える |  |
| ヘッドの epoch | backbone と同時 | 同じ | 揃える |  |
| seed と本数 | 42・123、各折り 1 本ずつ | 同じ | 揃える |  |
| 評価 recipe | conventions#eval_recipe | 同じ | 揃える |  |
| test の扱い | 各 run で一度、副次 | 同じ | 揃える |  |
| ホストと装置型 | andrew A6000 × 2、2 枚の道 | 同じ | 揃える | 20 本を同じ装置で順に |
| GPU の記憶 | 38.0〜38.7 GB/枚（PR 299 の b6） | 同じ見込み | 揃える | 設定が記憶を変えない見込み。実測で記録 |

**UNKNOWN は 0 件。** 腕と baseline（`baselines/dcoco_foldA/dcoco_foldA@val`、二周目の 0 番の処方、batch 2、折り A の 3 seed）は batch と weight decay が違うので値を比べない。baseline は同点幅の出所（mAP_sstd）としてだけ使う。

## 5. 記録する量（各 run）

1. 学習率を下げた epoch、打ち切った epoch、上限 36 への到達、checkpoint の epoch、総 epoch 数
2. checkpoint の epoch と最終 epoch の val mAP と標的群 AP
3. checkpoint での train mAP と val mAP の差（train の評価は規約の recipe で、train の全フレーム）
4. 立ち上げの歩数、1 epoch の歩数、総更新回数、換算した weight decay の実際の値
5. 発散・非数の有無と起きた歩。fp16 の scaler が飛ばした歩の数
6. epoch あたりの時間（学習と評価を分けて）、rank ごとの記憶量の最大
7. optimizer の群ごとの学習率と weight decay の実際の値、DataLoader の batch の値
8. 刈り込む前の勾配のノルムの分位点（5・50・95%）と、刈り込みが働いた歩の割合
9. test の評価の時刻と回数（一度であること）、読んだ動画の集合

## 6. 停止条件

- COCO の重みを読んだ行が無い、または読んだ重みの要約値が checkpoint と違う: 停止して諮る
- 評価の道具が checkpoint を読まずに値を返した: 停止して諮る
- 設定（学習率、weight decay、max_norm、batch）が optimizer の群か DataLoader に届かない: 停止して諮る
- 発散・非数が 1 本でも出た: 停止して諮る
- GPU の記憶が溢れた: 停止して諮る。batch を落として続けない（batch は水準として固定されている）
- 折りの注釈の train・val・test の動画の集合が規約の表と違う: 停止して諮る
- 記憶領域の空きが見込みの 2 倍を下回る、1 本の壁時計が見込みの上限（9 時間）の 2 倍を超える: 諮る

## 7. 環境の記録

driver、CUDA、cuDNN、NCCL、torch、torchvision、accelerate、画像の復号の実装、TF32 の設定、電力の上限。batch の探索（PR 299）の値と並べて記録する（同じホストなので一致を確かめる）。

## 8. val と test の重なり（規約 folds）

§2.4 のとおり。各折りの val は他の折りの test に現れる。本契約は val で checkpoint を選び、test は副次としてだけ記録する。
