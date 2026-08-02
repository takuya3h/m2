# s0_016_maskdino_bbox_nmsfree_seed456

作成日時: 2026-07-03T07:54:51+00:00

## 仮説
（ここに記入）

## 実験設定
- Category: baselines
- Step: s0
- Seed: 456
- Config: （config.yaml を参照）

## 結果
（実験完了後に記入）

## 解釈
（結果の意味、期待との差、原因の仮説）

## 次の行動
1.


## 再評価 (NMS-free)
- 元実験: `s0_003_maskdino_bbox_seed456`
- source_ckpt: `best_val_mAP_epoch_12.pth`
- test_cfg: score_thr=0.0, nms=None, nms_pre=None (NMS_FREE_TEST_CFG)
- val mAP=0.6690 / AP_rare=0.7590 / AP_common=0.6032
