# 非公式（T-2026-11-21-grasp-hand-irn-hice-htt-pilot） DP HTT DGH-GT seed 42 W3

受け取り手は確定塔の時間ヘッド（eval、dropout なし）。界面と時間ヘッドの全体を学ぶ（W3、受け取り手の学習率 0.0005）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 40（学習率を落とした epoch 48）。test は通していない。
best epoch 40 / val macro Jaccard 0.7246784703112544 / accuracy 0.9075907590759076
epochs 56（停止 56）、学習前 Jaccard 0.7762185528074379
