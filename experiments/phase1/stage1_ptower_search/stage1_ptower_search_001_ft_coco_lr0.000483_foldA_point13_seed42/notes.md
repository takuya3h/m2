# Stage 1 r3 fine-tune coco fold A lr 0.000483

Short side 800, whole frame (no crop). Stem frozen; val picks the epoch; test unread.
2 GPUs x 8 frames, SyncBatchNorm in layer1-4.
Backbone init sha256: a755b3eb22a3c1996ff88bb5797690ceb5605eedef5c24f980e1cac4c07fc98f
Best epoch: 15
Val frame accuracy: 0.803046218487395
Epochs completed: 19 (lr lowered at 14, stopped at 19)
Peak memory bytes per rank: [14869399040, 14869399040]
Elapsed seconds: 17272.253485770896

Artifacts, checkpoints and raw logs: /home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point13/runs/phase1/stage1_ptower_search_001_ft_coco_lr0.000483_foldA_point13_seed42
