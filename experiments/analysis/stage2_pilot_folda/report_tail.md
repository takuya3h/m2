## 構造上の注意（読むときに要る）

- **D1 と D3 の空の腕は、3 seed とも塔単独と同じ値になる。** 零の入力（D1）とトークン 0 個（D3）では、足した重みに勾配が届かない。
  そのため R = 0 で、「seed の幅を超える」は 3 つの Δ が同符号であればほぼ自動で付く。seed の揺れの目安にならない
- **FiLM の空の腕（D2、P1）は、界面が信号によらない定数の変調を学ぶ。** そのため空の腕の界面に予測の信号を入れると出力が変わる
  （D2 の陰性対照のロジット差の最大 0.0433、Jaccard 0.7733 → 0.7711）。D1・D3 の空の腕は変わらない（差 0.0）
- **PD は seed 1 つ。** R と §5.2 規則 2 の読み、実現率、型どうしの比較の幅の判定は出していない（UNKNOWN）。PD の Δ は 1 本ずつの差である
- **PD の上限 4 epoch。** 上限で止まった腕（表の「上限で停止」が True）は、規則で止まるより前の値である。
  上限 8 で起動していた P1-W1 の空と予測-noCF は、5 epoch 目の始まりで外から止め、4 epoch 目までの最良を結果にした（`cap_result.json`）。
  この 2 本は凍結部の要約値を学習の終わりに確かめていない（UNKNOWN）
- **D3 の予測のトークンは重複しない query の版（D0-INST-UQ）。** 字面どおりの版（D0-INST）では 1 つの query が複数のクラスで重複して入る

## §5.4 既知の限界

- 折りは 1 つ、val は 2 動画（09・10）。区間推定もクラスタの推論もできない。動画 09 の工程の Jaccard は塔単独で 0.993 と上限に近く、差はほぼ動画 10 で決まる
- 受け取り手も、界面の学習に使う train 動画で学習済みである（送り手の交差適合では直らない）
- 工程の確定塔は efros、交差適合用の塔（工程と検出）は andrew で学んだ
- **交差適合版の送り手は、確定塔の val より大きく弱い**。検出は train の overall mAP 0.4002（確定塔の val 0.7273）、工程は train の macro Jaccard 0.2449
  （確定塔の val 0.7762）。交差適合用の塔は train の半分で学び、検出の val AP は 0.6127 / 0.6584、工程の val の Jaccard は 0.5101 / 0.5109 に留まった。
  予測-CF の腕は、学習時は弱い信号、評価時は確定塔の強い信号を受けるため、noCF（学習時のほうが強い）とは逆向きの食い違いを持つ
- 今ある塔は工程注釈だけのフレームを使っていない。評価のフレーム集合は PR #229 の frame_sets 規則と違う
- 界面の型は提案の関門を通っていない。型ごとに学習率を探していない
- D0 と D1-L1 は枠の幾何を含まない。D3-L2 と D1-L2 は検出塔の内部の埋め込みを使う

## 置き場

- run: `experiments/phase1/stage2pilot_pd_*`、`experiments/phase1/stage2pilot_dp_*`、`experiments/phase1/stage2pilot_cf_ptower_*`、
  `experiments/baselines/stage2pilot_cf_dcoco_{H1,H2}_seed42`
- 大きな生成物（信号、checkpoint、交差適合用の検出塔の作業フォルダ）: `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/`（版管理と同期の外）
- 集計: `scripts/stage2pilot/aggregate.py`（本文書の表と `report.json` を作る）
- 命令と出力: `tasks/T-2026-10-18-stage2-pilot-folda/audit.md`
