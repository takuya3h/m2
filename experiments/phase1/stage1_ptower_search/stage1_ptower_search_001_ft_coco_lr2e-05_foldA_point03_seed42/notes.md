# Stage 1 r3 fine-tune coco fold A lr 2e-05

Short side 800, whole frame (no crop). Stem frozen; val picks the epoch; test unread.
2 GPUs x 8 frames, SyncBatchNorm in layer1-4.
Backbone init sha256: a755b3eb22a3c1996ff88bb5797690ceb5605eedef5c24f980e1cac4c07fc98f
Best epoch: 18
Val frame accuracy: 0.7347689075630253
Epochs completed: 26 (lr lowered at 22, stopped at 26)
Peak memory bytes per rank: [14869399040, 14868907520]
Elapsed seconds: 15503.717078844085

Artifacts, checkpoints and raw logs: /home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point03/runs/phase1/stage1_ptower_search_001_ft_coco_lr2e-05_foldA_point03_seed42
