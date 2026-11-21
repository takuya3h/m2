# 非公式（T-2026-11-21-grasp-hand-irn-hice-htt-pilot） DP HiCE DG seed 42 W2

受け取り手は確定塔の時間ヘッド（eval、dropout なし）。界面と時間ヘッドの最後の段を学ぶ（W2、受け取り手の学習率 0.0005）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 11（学習率を落とした epoch 10）。test は通していない。
best epoch 11 / val macro Jaccard 0.6902280703961691 / accuracy 0.8864686468646865
epochs 19（停止 19）、学習前 Jaccard 0.7762185528074379
