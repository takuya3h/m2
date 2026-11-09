# 非公式（T-2026-11-09-grasp-pilot-converge） DP TW perm seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 11（学習率を落とした epoch 19）。test は通していない。
best epoch 11 / val macro Jaccard 0.7808243452068222 / accuracy 0.8844884488448845
epochs 27（停止 27）、学習前 Jaccard 0.7762185528074379
