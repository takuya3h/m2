# 非公式（grasp_hand_graph/repro_cmp） DP D2 pred_noCF seed 42 W3

受け取り手は確定塔の時間ヘッド（eval、dropout なし）。界面と時間ヘッドの全体を学ぶ（W3、受け取り手の学習率 0.0005）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 56（学習率を落とした epoch 64）。test は通していない。
best epoch 56 / val macro Jaccard 0.7304483966054434 / accuracy 0.9168316831683169
epochs 72（停止 72）、学習前 Jaccard 0.7762185528074379
