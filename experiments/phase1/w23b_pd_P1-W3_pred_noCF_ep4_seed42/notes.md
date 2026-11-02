# 非公式（T-2026-11-01-stage2-w23-bengio） PD P1 FiLM（P1） W3 pred_noCF seed 42

受け取り手は D*-COCO 折り A seed 42 の検出塔。学習範囲 W3（--trainable all。界面 ＋ 設定の凍結以外の検出器の全体）。4 epoch 学習し途中で止めない。結果は 4 epoch 目（epoch 3）の状態で、最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。

- overall mAP 0.694144、標的群 AP 0.781937、陰性対照群 AP 0.638281、AP50 0.838539（群に欠けたクラス: 標的群 []、陰性対照群 []）
- 学習前 mAP 0.727345、学習前の出力と塔単独の差: {'comparable': True, 'max_abs_score_diff': 0.0, 'max_abs_bbox_diff_px': 0.0, 'label_mismatch': 0}
- epoch ごとの val mAP（epoch は 0 始まり、−1 は学習前）: {-1: 0.7273450248398429, 0: 0.7012217196021673, 1: 0.6795661379602393, 2: 0.6893538579053349, 3: 0.6941439165258269}
- epoch ごとのゲート: {-1: None, 0: None, 1: None, 2: None, 3: None}
- 動画ごとの mAP: {'09': 0.6714153063782782, '10': 0.61618309757925}
- 凍結部の要約値の前後一致: True
- 予測は /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/pd_preds/w23b_pd_P1-W3_pred_noCF_ep4_seed42 へ移した（predictions_moved.json）
