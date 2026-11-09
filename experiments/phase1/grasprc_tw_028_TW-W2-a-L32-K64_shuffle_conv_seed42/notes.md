# 非公式（T-2026-11-09-grasp-pilot-converge） DP TW shuffle seed 42 W2

受け取り手は確定塔の時間ヘッド（eval、dropout なし）。界面と時間ヘッドの最後の段を学ぶ（W2、受け取り手の学習率 0.0005）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 18（学習率を落とした epoch 26）。test は通していない。
best epoch 18 / val macro Jaccard 0.695447640612661 / accuracy 0.8917491749174917
epochs 34（停止 34）、学習前 Jaccard 0.7762185528074379
