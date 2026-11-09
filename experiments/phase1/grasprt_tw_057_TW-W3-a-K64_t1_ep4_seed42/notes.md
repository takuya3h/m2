# 非公式（T-2026-11-09-grasp-roitoken-transition-pilot） DP TW t1 seed 42 W3

受け取り手は確定塔の時間ヘッド（eval、dropout なし）。界面と時間ヘッドの全体を学ぶ（W3、受け取り手の学習率 0.0005）。4 epoch 学習し途中で止めない。結果は 4 epoch 目の状態（最良の回を選ばない）。test は通していない。
result epoch 4 / val macro Jaccard 0.6503611060720713 / accuracy 0.8871287128712871
epochs 4（停止 None）、学習前 Jaccard 0.7762185528074379
