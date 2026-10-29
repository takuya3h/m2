# Stage 1 r3 fine-tune coco fold A lr 0.000162

Short side 800, whole frame (no crop). Stem frozen; val picks the epoch; test unread.
2 GPUs x 8 frames, SyncBatchNorm in layer1-4.
Backbone init sha256: a755b3eb22a3c1996ff88bb5797690ceb5605eedef5c24f980e1cac4c07fc98f
Best epoch: 13
Val frame accuracy: 0.7941176470588235
Epochs completed: 17 (lr lowered at 11, stopped at 17)
Peak memory bytes per rank: [14869399040, 14869399040]
Elapsed seconds: 10170.676712479442

Artifacts, checkpoints and raw logs: /home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point16/runs/phase1/stage1_ptower_search_001_ft_coco_lr0.000162_foldA_point16_seed42
