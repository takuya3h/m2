# Stage 1 r3 fine-tune coco fold A lr 0.000113

Short side 800, whole frame (no crop). Stem frozen; val picks the epoch; test unread.
2 GPUs x 8 frames, SyncBatchNorm in layer1-4.
Backbone init sha256: a755b3eb22a3c1996ff88bb5797690ceb5605eedef5c24f980e1cac4c07fc98f
Best epoch: 8
Val frame accuracy: 0.7804621848739496
Epochs completed: 16 (lr lowered at 12, stopped at 16)
Peak memory bytes per rank: [14868907520, 14869399040]
Elapsed seconds: 9888.662159081548

Artifacts, checkpoints and raw logs: /home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point08/runs/phase1/stage1_ptower_search_001_ft_coco_lr0.000113_foldA_point08_seed42
