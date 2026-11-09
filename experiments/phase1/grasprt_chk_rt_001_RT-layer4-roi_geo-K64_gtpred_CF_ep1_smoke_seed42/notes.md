# 非公式（T-2026-11-09-grasp-roitoken-transition-pilot） DP RT gtpred_CF seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。1 epoch 学習し途中で止めない。結果は 1 epoch 目の状態（最良の回を選ばない）。test は通していない。
result epoch 1 / val macro Jaccard 0.7866693286448575 / accuracy 0.8824306472919419
epochs 1（停止 None）、学習前 Jaccard 0.7770292529590558
