# 非公式（T-2026-11-09-stage2-pd-w3-lowlr-andrew） PD FiLM（P1） W3 gt seed 42

**非公式の測定。関門の判定と設計の判断に使わない。**

受け取り手は D*-COCO 折り A seed 42 の検出塔。受け取り手の学習率 1e-05（比 0.1 の群はその 0.1 倍）、界面 0.0005。学習範囲 W3（--trainable all、学ぶ要素 48738080、うち界面 266880）。4 epoch 学習し途中で止めない。結果は 4 epoch 目（epoch 3）の状態で、最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。

- overall mAP 0.726269、AP50 0.852938、標的群 AP 0.807659、陰性対照群 AP 0.663910
- 学習前 mAP 0.727345、学習前の塔単独との出力の差 {'comparable': True, 'max_abs_score_diff': 0.0, 'max_abs_bbox_diff_px': 0.0, 'label_mismatch': 0}
- epoch ごとの val（−1 は学習前）: {-1: (0.727345, 0.795075), 0: (0.732726, 0.80909), 1: (0.733953, 0.821727), 2: (0.736299, 0.81898), 3: (0.726269, 0.807659)}
- epoch ごとのゲート・界面の重み: {-1: None, 0: None, 1: None, 2: None, 3: None}
- 受け取り手の動いた量（L2、相対）: 6.30953、0.0073802805384060866
- 動画ごとの mAP: {'09': 0.6956436437366951, '10': 0.6513991737751601}
- 通した動画: train ['01', '02', '03', '06', '08', '11', '12', '13', '14', '15']、val ['09', '10']、test との共通 []
- 凍結部の要約値の前後一致: True
- 群の学習率（epoch ごと、記録 lr_groups.json）: {0: {'other': 1e-05, 'backbone': 1.0000000000000002e-06, 'backbone_norm': 1.0000000000000002e-06, 'linear_projection': 1.0000000000000002e-06, 'linear_projection_norm': 1.0000000000000002e-06, 'other_norm': 1e-05, 'phase': 0.0005}, 1: {'other': 1e-05, 'backbone': 1.0000000000000002e-06, 'backbone_norm': 1.0000000000000002e-06, 'linear_projection': 1.0000000000000002e-06, 'linear_projection_norm': 1.0000000000000002e-06, 'other_norm': 1e-05, 'phase': 0.0005}, 2: {'other': 1e-05, 'backbone': 1.0000000000000002e-06, 'backbone_norm': 1.0000000000000002e-06, 'linear_projection': 1.0000000000000002e-06, 'linear_projection_norm': 1.0000000000000002e-06, 'other_norm': 1e-05, 'phase': 0.0005}, 3: {'other': 1e-05, 'backbone': 1.0000000000000002e-06, 'backbone_norm': 1.0000000000000002e-06, 'linear_projection': 1.0000000000000002e-06, 'linear_projection_norm': 1.0000000000000002e-06, 'other_norm': 1e-05, 'phase': 0.0005}}
