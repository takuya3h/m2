# 非公式（T-2026-11-26-vlm-caption-signal-pilot） DP D1-L2 vlm_ko seed 42 W2

受け取り手は確定塔の時間ヘッド（eval、dropout なし）。界面と時間ヘッドの最後の段を学ぶ（W2、受け取り手の学習率 0.0005）。16 epoch 学習し途中で止めない。結果は 16 epoch 目の状態（最良の回を選ばない）。test は通していない。
result epoch 16 / val macro Jaccard 0.6803187768390834 / accuracy 0.8752475247524752
epochs 16（停止 None）、学習前 Jaccard 0.7762185528074379
