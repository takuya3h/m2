# Stage 1 r3 fine-tune coco fold A lr 0.0001

Short side 800, whole frame (no crop). Stem frozen; val picks the epoch; test unread.
2 GPUs x 8 frames, SyncBatchNorm in layer1-4.
Backbone init sha256: a755b3eb22a3c1996ff88bb5797690ceb5605eedef5c24f980e1cac4c07fc98f
Best epoch: 19
Val frame accuracy: 0.7956932773109243
Epochs completed: 23 (lr lowered at 12, stopped at 23)
Peak memory bytes per rank: [14868907520, 14868907520]
Elapsed seconds: 11708.8126220759

Artifacts, checkpoints and raw logs: /home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/phase/seed123/runs/phase1/stage1_ptower_search_001_ft_coco_lr0.0001_foldA_point00_seed123
