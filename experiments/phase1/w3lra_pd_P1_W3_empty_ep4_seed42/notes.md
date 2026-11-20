# 非公式（T-2026-11-09-stage2-pd-w3-lowlr-andrew） PD FiLM（P1） W3 empty seed 42

**非公式の測定。関門の判定と設計の判断に使わない。**

受け取り手は D*-COCO 折り A seed 42 の検出塔。受け取り手の学習率 1e-05（比 0.1 の群はその 0.1 倍）、界面 0.0005。学習範囲 W3（--trainable all、学ぶ要素 48738080、うち界面 266880）。4 epoch 学習し途中で止めない。結果は 4 epoch 目（epoch 3）の状態で、最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。

- overall mAP 0.713798、AP50 0.841858、標的群 AP 0.777521、陰性対照群 AP 0.663655
- 学習前 mAP 0.727345、学習前の塔単独との出力の差 {'comparable': True, 'max_abs_score_diff': 0.0, 'max_abs_bbox_diff_px': 0.0, 'label_mismatch': 0}
- epoch ごとの val（−1 は学習前）: {-1: (0.727345, 0.795075), 0: (0.725961, 0.791015), 1: (0.722427, 0.791332), 2: (0.724505, 0.79076), 3: (0.713798, 0.777521)}
- epoch ごとのゲート・界面の重み: {-1: None, 0: None, 1: None, 2: None, 3: None}
- 受け取り手の動いた量（L2、相対）: 6.31174、0.007382859875698628
- 動画ごとの mAP: {'09': 0.692067577838213, '10': 0.6331453944004739}
- 通した動画: train ['01', '02', '03', '06', '08', '11', '12', '13', '14', '15']、val ['09', '10']、test との共通 []
- 凍結部の要約値の前後一致: True
- 群の学習率（epoch ごと、記録 lr_groups.json）: {0: {'other': 1e-05, 'backbone': 1.0000000000000002e-06, 'backbone_norm': 1.0000000000000002e-06, 'linear_projection': 1.0000000000000002e-06, 'linear_projection_norm': 1.0000000000000002e-06, 'other_norm': 1e-05, 'phase': 0.0005}, 1: {'other': 1e-05, 'backbone': 1.0000000000000002e-06, 'backbone_norm': 1.0000000000000002e-06, 'linear_projection': 1.0000000000000002e-06, 'linear_projection_norm': 1.0000000000000002e-06, 'other_norm': 1e-05, 'phase': 0.0005}, 2: {'other': 1e-05, 'backbone': 1.0000000000000002e-06, 'backbone_norm': 1.0000000000000002e-06, 'linear_projection': 1.0000000000000002e-06, 'linear_projection_norm': 1.0000000000000002e-06, 'other_norm': 1e-05, 'phase': 0.0005}, 3: {'other': 1e-05, 'backbone': 1.0000000000000002e-06, 'backbone_norm': 1.0000000000000002e-06, 'linear_projection': 1.0000000000000002e-06, 'linear_projection_norm': 1.0000000000000002e-06, 'other_norm': 1e-05, 'phase': 0.0005}}
