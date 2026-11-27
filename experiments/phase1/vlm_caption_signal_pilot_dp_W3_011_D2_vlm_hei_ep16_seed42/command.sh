#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-27T01:45:48+00:00
python /home/ubuntu/slocal2/m2/scripts/stage2pilot/dp_train.py train --type D2 --arm vlm_hei --seed 42 --scope W3 --fixed-epochs 16 --record-epochs 4 8 12 16 --save-last-probs --task-id T-2026-11-26-vlm-caption-signal-pilot --exp-prefix vlm_caption_signal_pilot_dp_W3 --vlm-dir /home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot/signals --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot/dp_ckpt
