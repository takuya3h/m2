# 非公式（T-2026-11-21-grasp-hand-graph-t2p-match） DP GR DH-CF seed 42 W3

受け取り手は確定塔の時間ヘッド（eval、dropout なし）。界面と時間ヘッドの全体を学ぶ（W3、受け取り手の学習率 0.0005）。16 epoch 学習し途中で止めない。結果は 16 epoch 目の状態（最良の回を選ばない）。test は通していない。
result epoch 16 / val macro Jaccard 0.6762874283304896 / accuracy 0.8706270627062707
epochs 16（停止 None）、学習前 Jaccard 0.7762185528074379
