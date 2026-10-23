# T-2026-10-23-gaze-data-survey audit

命令の出力をそのまま写す。出力の時刻は UTC で、本文では JST（+9 時間）に読み替えて書く。scratchpad の記録 `/tmp/claude-1000/-home-ubuntu-slocal2-m2/364893d6-9301-47b1-9367-6013879a4be8/scratchpad/gaze/` から転記した。B3b は表示のために各行を 400 バイトで切っている。

## A. 開始状態

### A0. 手順書「0. 始める」と task-start（JST 15:48）

    $ git branch --show-current ...（読み取りだけの確認）
    feat/ptower-cand5-heads-impl
    ls: cannot access 'tasks/T-2026-10-23-gaze-data-survey': No such file or directory
    cat: .sync-pause: No such file or directory
    $ git fetch origin && python3 scripts/task_start_classify.py
    [task-start] 分類（比較先 origin/phase0 d013c5f1）
    [task-start]   追跡下の変更: 0 件 / 未追跡・起点に無い: 0 件 / 無視・起点に在り中身が違う: 0 件
    [task-start] 分類: 通す
    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-23-gaze-data-survey
    [task-start] 分岐を作成: feat/gaze-data-survey（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら make task-release TASK=T-2026-10-23-gaze-data-survey END=complete）
    [task-start] 完了。分岐 feat/gaze-data-survey で契約 T-2026-10-23-gaze-data-survey の作業を開始できます
    $ make task-validate TASK=T-2026-10-23-gaze-data-survey   → OK, exit=0
    $ make task-preflight TASK=T-2026-10-23-gaze-data-survey
    P1 venv_active PASS / P6 decisions_answered PASS / P7 destination_writable PASS / P8 contract_valid PASS
    P9 spec_lint PASS 規則 9 件を検査し該当なし / P10 preflight_names_known PASS
    SKIP: P2 cuda_ext_loaded, P3 deterministic_flags, P4 prereg_committed, P5 frozen_source_hash,
          P11 gpu_free, P12 refs_resolved, P13 symmetry_table_complete, P14 proposal_card_checked
    RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL, exit=0

### A1. 分岐・起点・作業ツリー・空き容量（HEAD, origin/phase0, merge-base の順。porcelain の行数）

    ## branch
    feat/gaze-data-survey
    d013c5f14c47acd9778b1ff2a4a81e6e6fa2f5c0
    d013c5f14c47acd9778b1ff2a4a81e6e6fa2f5c0
    d013c5f14c47acd9778b1ff2a4a81e6e6fa2f5c0
    2
    ## df
    Filesystem      Size  Used Avail Use% Mounted on
    /dev/sdc1       7.3T  5.4T  1.6T  78% /home/ubuntu/slocal2
    /home/ubuntu/slocal2/m2/data
    ## manifest
    total 64
    drwxrwxr-x 16 ubuntu ubuntu 4096 Oct 21 21:10 .
    drwxrwxr-x  8 ubuntu ubuntu 4096 Oct  8 16:03 ..
    drwxrwxr-x 10 ubuntu ubuntu 4096 Jul  6 17:09 b2a_detsignal
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  4 07:47 c5neck
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  3 01:00 copypaste_bank
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  3 01:00 ego_frames
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  3 01:00 exo_clips
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  3 01:00 features
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  4 07:47 joint_manifest
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  4 07:37 oracle_handfeature
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  4 07:39 oracle_toolpresence
    drwxrwxr-x  3 ubuntu ubuntu 4096 Jul  4 07:31 phase_context
    drwxrwxr-x  2 ubuntu ubuntu 4096 Jul  4 07:29 phase_manifest
    drwxrwxr-x  2 ubuntu ubuntu 4096 Oct 21 21:10 phase_manifest_all_phase
    drwxrwxr-x 71 ubuntu ubuntu 4096 Oct  5 02:40 stage1_features
    drwxrwxr-x 12 ubuntu ubuntu 4096 Jul 29 16:34 t1a_regiontoken

    $ git status --porcelain --untracked-files=all
    ?? tasks/T-2026-10-23-gaze-data-survey/SPEC.md
    ?? tasks/T-2026-10-23-gaze-data-survey/spec.yaml

2 件は task-start が取り込んだ契約である。G1 は pass。

### A3. manifest と工程 CSV の行数（manifest を読む方法と、CSV の行を数える方法）

    train num_clips 14 14 num_frames 10580 counted 10580 videos ['01', '02', '03', '06', '08', '11', '12', '13', '14', '15']
    val num_clips 3 3 num_frames 1904 counted 1904 videos ['09', '10']
    test num_clips 6 6 num_frames 4749 counted 4749 videos ['04', '05', '07']
    manifest total 17233
     root data/raw/OpenSurgery_Dataset/01_frames/initial_videos 1796
     root data/raw/ego/test 4265
     root data/raw/ego/train 9657
     root data/raw/ego/val 1515
    01-15 csv 23 rows 17233
    17-21 csv 20 rows 10461
    ['Frame,Phase', '01_1_0001,disinfection', '01_1_0002,disinfection']
    ['Frame,Phase', '17_1_1504,dissection', '17_1_1505,dissection']

### A4. 試験の前（`PYTHONPATH=src python -m pytest tests -q -p no:cacheprovider -rf`）

    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics - Ass...
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name - AssertionEr...
    FAILED tests/test_research_logger.py::test_log_run_idempotent - AssertionErro...
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    FAILED tests/test_stage1_ptower_r3_dist.py::test_two_gpus_give_the_one_gpu_gradient_over_an_uneven_tail
    7 failed, 959 passed, 27 warnings in 1830.60s (0:30:30)
    exit=1

## B. 置き場の探索

### B1. 名前（data/ と ~/slocal2/ の深さ 3）

    ## B1 names in data/ (follow symlinks, include dotfiles)
    --- count (all matches incl. ego paths)
    0
    ## B1 names in ~/slocal2/ top (depth 3)
    /home/ubuntu/slocal2/m2/tasks/T-2026-10-23-gaze-data-survey

### B1w. 名前（追加: andrew の全装置。find -xdev、.venv・site-packages・node_modules・.git・wandb を除く）

    ### /home/ubuntu/slocal1
    exit=0
    ### /home/ubuntu/slocal2
    /home/ubuntu/slocal2/m2/tasks/T-2026-10-23-gaze-data-survey
    exit=0
    ### /home/ubuntu/local
    exit=0
    ### /home/ubuntu/m2-hold
    exit=0
    ### /home/ubuntu/m2-evacuated
    exit=0
    ### /mnt
    exit=0
    ### /media
    exit=0
    ### /srv
    exit=0
    ### /opt
    exit=0

### B1c. 名前の陽性対照とホーム直下

    ### control: same find for *egosurgery_phase* in /home/ubuntu/slocal2
    /home/ubuntu/slocal2/m2-four-andrew/configs/data/egosurgery_phase.yaml
    /home/ubuntu/slocal2/m2-four-andrew/data/annotations/egosurgery_phase
    /home/ubuntu/slocal2/m2-four-andrew-smoke/configs/data/egosurgery_phase.yaml
    /home/ubuntu/slocal2/m2-four-andrew-smoke/data/annotations/egosurgery_phase
    /home/ubuntu/slocal2/m2-s2fix-wt-andrewtest/configs/data/egosurgery_phase.yaml
    /home/ubuntu/slocal2/m2-s2fix-wt-andrewtest/data/annotations/egosurgery_phase
    /home/ubuntu/slocal2/m2/configs/data/egosurgery_phase.yaml
    /home/ubuntu/slocal2/m2/data/annotations/egosurgery_phase
    ( timeout 900 find /home/ubuntu/slocal2 -xdev \( -path '*/.venv*' -o -path  -)  0.99s user 0.34s system 100% cpu 1.323 total
    ### /home/ubuntu (root fs, -xdev, incl dotdirs)
    ### file count of slocal2 walked
    580329

### B2. 内容（拡張子ごとの数）

    ## symlinks under data (depth 3)
    data/eval_staging/egosurgery_val/val2017 -> /home/ubuntu/slocal2/m2/data/raw/ego
    ## B2 extension census, non-jpg, per top dir of data/raw and data/annotations (follow symlinks, incl dotfiles)
    ### data/raw/EgoSurgery_HTS2
      72019 png
      19496 jpg
         12 json
          1 txt
          1 md
    ### data/raw/OpenSurgery_Dataset
      90416 png
      27535 jpg
        267 json
         46 csv
          7 md
          6 py
          3 zip
          1 txt
    ### data/raw/ego
      25898 jpg
          3 gitkeep
          1 ds_store
    ### data/raw/exo
          5 gitkeep
    ### data/raw/ego/other(17~21)
      10461 jpg
    ### data/raw/ego/train
       9657 jpg
          1 gitkeep
          1 ds_store
    ### data/raw/ego/val
       1515 jpg
          1 gitkeep
    ### data/raw/ego/test
       4265 jpg
          1 gitkeep
    ### data/annotations/_deprecated
          3 json
    ### data/annotations/egosurergyhts_open
          1 (noext)
    ### data/annotations/egosurgery_hts
         12 json
          5 md
          3 txt
          1 gitkeep
    ### data/annotations/egosurgery_hts2_coverage_report.md
          1 md
    ### data/annotations/egosurgery_hts_bak
         12 bak
    ### data/annotations/egosurgery_hts_current_coverage.md
          1 md
    ### data/annotations/egosurgery_hts_frame_coverage_report.md
          1 md
    ### data/annotations/egosurgery_phase
         43 csv
    ### data/annotations/egosurgery_tool
          6 json
    ### data/annotations/egosurgery_tool_folds
         16 json
    ### data/annotations/egosurgery_tool_hand
          6 json

### B2b. OpenSurgery_Dataset の構成と画像以外のファイル

    ## OpenSurgery_Dataset depth 2
    data/raw/OpenSurgery_Dataset
    data/raw/OpenSurgery_Dataset/00_master_annotations
    data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw
    data/raw/OpenSurgery_Dataset/01_frames
    data/raw/OpenSurgery_Dataset/01_frames/initial_videos
    data/raw/OpenSurgery_Dataset/02_hand
    data/raw/OpenSurgery_Dataset/02_hand/coco_splits_4cls
    data/raw/OpenSurgery_Dataset/02_hand/json_per_video
    data/raw/OpenSurgery_Dataset/02_hand/masks_per_class
    data/raw/OpenSurgery_Dataset/03_tool
    data/raw/OpenSurgery_Dataset/03_tool/coco_splits_14cls_cleaned
    data/raw/OpenSurgery_Dataset/03_tool/coco_splits_15cls_withkidney
    data/raw/OpenSurgery_Dataset/03_tool/coco_splits_31cls
    data/raw/OpenSurgery_Dataset/03_tool/json_per_video
    data/raw/OpenSurgery_Dataset/04_handtool
    data/raw/OpenSurgery_Dataset/04_handtool/coco_splits_5cls
    data/raw/OpenSurgery_Dataset/04_handtool/json_per_video
    data/raw/OpenSurgery_Dataset/04_handtool/masks
    data/raw/OpenSurgery_Dataset/04_handtool/seg_ann_4cls
    data/raw/OpenSurgery_Dataset/05_egosurgery_hts
    data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox
    data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion
    data/raw/OpenSurgery_Dataset/05_egosurgery_hts/handtool_masks_5cls
    data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls
    data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer
    data/raw/OpenSurgery_Dataset/AUDIT.md
    data/raw/OpenSurgery_Dataset/AUDIT.sync-conflict-20260917-082621-LW4CO4U.md
    data/raw/OpenSurgery_Dataset/AUDIT.sync-conflict-20260917-082628-LW4CO4U.md
    data/raw/OpenSurgery_Dataset/AUDIT.sync-conflict-20260917-082632-LW4CO4U.md
    data/raw/OpenSurgery_Dataset/AUDIT.sync-conflict-20260917-082640-LW4CO4U.md
    data/raw/OpenSurgery_Dataset/README.md
    data/raw/OpenSurgery_Dataset/SCALE_VERIFICATION.md
    data/raw/OpenSurgery_Dataset/copy_targets.txt
    ## non-image files (dirs collapsed)
          2 data/raw/EgoSurgery_HTS2
          4 data/raw/EgoSurgery_HTS2/hand_seg
          4 data/raw/EgoSurgery_HTS2/hand_tool_seg
          4 data/raw/EgoSurgery_HTS2/tool_seg
          8 data/raw/OpenSurgery_Dataset
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/01
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/02
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/03
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/04
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/05
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/06
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/07
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/08
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/09
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/10
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/11
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/12
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/13
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/14
          1 data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/15
          3 data/raw/OpenSurgery_Dataset/02_hand/coco_splits_4cls
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/01_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/02_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/03_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/03_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/03_3
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/04_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/04_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/05_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/05_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/06_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/06_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/07_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/07_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/08_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/08_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/09_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/10_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/10_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/11_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/12_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/12_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/13_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/14_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/14_2
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/15_1
          1 data/raw/OpenSurgery_Dataset/02_hand/json_per_video/15_2
          3 data/raw/OpenSurgery_Dataset/03_tool/coco_splits_14cls_cleaned
          3 data/raw/OpenSurgery_Dataset/03_tool/coco_splits_15cls_withkidney
          3 data/raw/OpenSurgery_Dataset/03_tool/coco_splits_31cls
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/01_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/02_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/03_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/03_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/03_3
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/04_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/04_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/05_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/05_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/06_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/06_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/07_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/07_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/08_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/08_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/09_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/10_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/10_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/11_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/12_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/12_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/13_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/14_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/14_2
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/15_1
          1 data/raw/OpenSurgery_Dataset/03_tool/json_per_video/15_2
          3 data/raw/OpenSurgery_Dataset/04_handtool/coco_splits_5cls
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/01_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/02_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/03_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/03_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/03_3
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/04_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/04_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/05_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/05_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/06_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/06_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/07_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/07_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/08_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/08_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/09_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/10_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/10_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/11_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/12_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/12_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/13_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/14_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/14_2
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/15_1
          1 data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/15_2
          3 data/raw/OpenSurgery_Dataset/04_handtool/seg_ann_4cls
          3 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_split/hands
          3 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_split/tools
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/01
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/02
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/03
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/04
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/05
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/06
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/07
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/08
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/09
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/10
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/11
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/12
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/13
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/14
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/hands/15
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/01
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/02
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/03
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/04
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/05
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/06
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/07
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/08
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/09
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/10
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/11
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/12
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/13
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/14
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/bbox/by_video/tool/15
         46 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase
         38 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion
         18 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all
         21 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/03_2
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/03_3
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/04_2
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/05_1
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/07_2
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/08_2
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/10_2
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/11_1
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/12_1
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/12_2
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/13_1
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/14_1
          2 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/14_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/01_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/02_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/03_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/03_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/03_3
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/04_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/04_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/05_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/05_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/06_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/06_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/07_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/07_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/08_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/08_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/09_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/10_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/10_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/11_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/12_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/12_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/13_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/14_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/14_2
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/15_1
          1 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/15_2
    ## zips
    2056152 2025-08-21 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/ht_split_check.zip
    43973861 2025-02-11 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all.zip
    51404512 2025-08-21 data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/fullann_ht.zip

### B2c. 画像以外の 464 本の見出し・鍵・zip の中身・語の出現

    ZIP data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/ht_split_check.zip 3 {'json': 3} name-hits []
    ZIP data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all.zip 17 {'json': 16} name-hits []
    ZIP data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/fullann_ht.zip 19 {'json': 18} name-hits []
    non-image files scanned 464
    CSV headers:
      89 Frame,Phase
    JSON top keys:
      138 ['annotations', 'categories', 'images', 'licenses']
      87 ['annotations', 'categories', 'images', 'info', 'licenses']
      66 ['annotations', 'categories', 'images']
      13 ['left hand', 'right hand']
      6 ['annotations', 'categories', 'images', 'info', 'licenses', 'videos']
      4 ['bipolar forceps', 'bone curette', 'caliper', 'chisel', 'cup', 'drill', 'electric cautery', 'forceps', 'gauze', 'hammer', 'hook', 'kidney dish', 'needle holders', 'raspatory', 'retractor', 'ruler', 'scalpel', 'scissors', 'screwdriver', 'suction cannula', 'suction tube', 'suture, suture needle', 'syringe', 'trephine', 'tweezers']
      2 ['bipolar forceps', 'bone curette', 'chisel', 'cup', 'drill', 'electric cautery', 'forceps', 'gauze', 'hammer', 'hook', 'needle holders', 'raspatory', 'retractor', 'ruler', 'scalpel', 'scissors', 'screwdriver', 'suction cannula', 'suction tube', 'suture, suture needle', 'syringe', 'trephine', 'tweezers']
      1 ['bipolar forceps', 'bone curette', 'caliper', 'chisel', 'cup', 'drill', 'electric cautery', 'forceps', 'gauze', 'hammer', 'hook', 'needle holders', 'raspatory', 'retractor', 'ruler', 'scalpel', 'scissors', 'screwdriver', 'suction cannula', 'suction tube', 'suture, suture needle', 'syringe', 'trephine', 'tweezers']
      1 ['bipolar forceps', 'bone curette', 'caliper', 'chisel', 'cup', 'drill', 'electric cautery', 'forceps', 'gauze', 'hammer', 'hook', 'kidney dish', 'malleable retractor', 'needle holders', 'raspatory', 'retractor', 'ruler', 'scalpel', 'scissors', 'screwdriver', 'suction cannula', 'suction tube', 'suture, suture needle', 'syringe', 'trephine', 'tweezers']
      1 ['bipolar forceps', 'bone curette', 'chisel', 'cup', 'drill', 'electric cautery', 'forceps', 'gauze', 'hammer', 'hook', 'needle holders', 'retractor', 'ruler', 'scalpel', 'scissors', 'screwdriver', 'suction cannula', 'suction tube', 'suture, suture needle', 'syringe', 'trephine', 'tweezers']
      1 ['bipolar forceps', 'forceps', 'gauze', 'hook', 'needle holders', 'scalpel', 'scissors', 'suction cannula', 'suction tube', 'suture, suture needle', 'syringe', 'tweezers']
      1 ['bipolar forceps', 'bone curette', 'chisel', 'cup', 'forceps', 'gauze', 'hammer', 'hook', 'needle holders', 'retractor', 'ruler', 'scalpel', 'scissors', 'suction cannula', 'suction tube', 'suture, suture needle', 'syringe', 'trephine', 'tweezers']
      1 ['folds', 'negative_control', 'pooled_images', 'videos']
    content hits (gaze words):
      ('data/raw/EgoSurgery_HTS2/tool_seg/train.json', 27, ['eye', 'gaze'])
      ('data/raw/EgoSurgery_HTS2/tool_seg/all.json', 49, ['eye', 'gaze'])
      ('data/raw/EgoSurgery_HTS2/tool_seg/test.json', 13, ['eye'])
      ('data/raw/EgoSurgery_HTS2/tool_seg/val.json', 9, ['eye'])
      ('data/raw/EgoSurgery_HTS2/hand_tool_seg/train.json', 164, ['eye', 'gaze'])
      ('data/raw/EgoSurgery_HTS2/hand_tool_seg/all.json', 300, ['eye', 'gaze'])
      ('data/raw/EgoSurgery_HTS2/hand_tool_seg/test.json', 60, ['eye'])
      ('data/raw/EgoSurgery_HTS2/hand_tool_seg/val.json', 27, ['eye'])
      ('data/raw/EgoSurgery_HTS2/hand_seg/train.json', 377, ['eye', 'gaze'])
      ('data/raw/EgoSurgery_HTS2/hand_seg/all.json', 540, ['eye', 'gaze'])
      ('data/raw/EgoSurgery_HTS2/hand_seg/test.json', 68, ['eye', 'gaze'])
      ('data/raw/EgoSurgery_HTS2/hand_seg/val.json', 66, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/08.json', 38, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/10.json', 47, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/06.json', 30, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/15.json', 29, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/07.json', 18, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/09.json', 17, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/04.json', 11, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/01.json', 15, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/02.json', 25, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/14_2/14_2toolscount_byhand.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/14_2/14_2.json', 18, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/12_1/12_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/13_1/13_1.json', 10, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/03_2/03_2toolscount_byhand.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/03_2/03_2.json', 40, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/04_2/04_2.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/05_1/05_1toolscount_byhand.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/05_1/05_1.json', 13, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/10_2/10_2toolscount_byhand.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/10_2/10_2.json', 5, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/08_2/08_2toolscount_byhand.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/08_2/08_2.json', 14, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/11_1/11_1.json', 19, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/07_2/07_2.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/07_2/07_2toolscount_byhand.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/14_1/14_1.json', 63, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/14_1/14_1toolscount_byhand.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/10_1/10_1.json', 3, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/14_2/14_2.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/08_1/08_1.json', 8, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/01_1/01_1.json', 4, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/12_1/12_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/06_1/06_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/06_2/06_2.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/03_2/03_2.json', 9, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/04_2/04_2.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/02_1/02_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/07_1/07_1.json', 11, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/05_1/05_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/09_1/09_1.json', 7, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/08_2/08_2.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/11_1/11_1.json', 3, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/07_2/07_2.json', 4, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer/14_1/14_1.json', 6, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/08.json', 38, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/10.json', 47, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/12_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/train_toolhand_withmask.json', 164, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/06.json', 30, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/test_toolhand_withmask.json', 27, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/train_toolhand_withmask_iscrowd.json', 164, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/15.json', 29, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/11_1.json', 19, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/val_toolhand_withmask.json', 60, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/test_toolhand.json', 27, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/13_1.json', 10, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/test_toolhand_withmask_iscrowd.json', 27, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/07.json', 18, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/09.json', 17, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/03_2.json', 40, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/train_toolhand.json', 164, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/merged_annotations.json', 300, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/val_toolhand.json', 60, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/04.json', 11, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/01.json', 15, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/02.json', 25, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/val_toolhand_withmask_iscrowd.json', 60, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/08.json', 38, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/10.json', 47, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/12_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/14_1.json', 63, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/06.json', 30, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/14_2.json', 18, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/15.json', 29, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/11_1.json', 19, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/13_1.json', 10, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/07.json', 18, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/09.json', 17, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/03_2.json', 40, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/04.json', 11, ['eye'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/01.json', 15, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/05_egosurgery_hts/fusion/all/02.json', 25, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_31cls/train.json', 43, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_31cls/test.json', 8, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_31cls/val.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/10_1/10_1.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/14_2/14_2.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/08_1/08_1.json', 8, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/01_1/01_1.json', 4, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/12_1/12_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/06_1/06_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/06_2/06_2.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/03_2/03_2.json', 3, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/04_2/04_2.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/02_1/02_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/07_1/07_1.json', 11, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/05_1/05_1.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/09_1/09_1.json', 7, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/08_2/08_2.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/11_1/11_1.json', 3, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/json_per_video/14_1/14_1.json', 6, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_14cls_cleaned/train.json', 27, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_14cls_cleaned/test.json', 13, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_14cls_cleaned/val.json', 9, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_15cls_withkidney/train.json', 27, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_15cls_withkidney/test.json', 13, ['eye'])
      ('data/raw/OpenSurgery_Dataset/03_tool/coco_splits_15cls_withkidney/val.json', 9, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/10_1/10_1.json', 47, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/15_1/15_1.json', 29, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/14_2/14_2.json', 15, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/08_1/08_1.json', 60, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/01_1/01_1.json', 15, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/12_1/12_1.json', 5, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/13_1/13_1.json', 14, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/06_1/06_1.json', 36, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/06_2/06_2.json', 39, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/03_2/03_2.json', 55, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/04_2/04_2.json', 8, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/02_1/02_1.json', 31, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/07_1/07_1.json', 18, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/05_1/05_1.json', 14, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/10_2/10_2.json', 3, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/15_2/15_2.json', 11, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/04_1/04_1.json', 12, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/09_1/09_1.json', 18, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/08_2/08_2.json', 19, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/11_1/11_1.json', 26, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/03_1/03_1.json', 6, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/07_2/07_2.json', 3, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/05_2/05_2.json', 4, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/json_per_video/14_1/14_1.json', 75, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/seg_ann_4cls/train.json', 202, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/seg_ann_4cls/test.json', 43, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/seg_ann_4cls/val.json', 56, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/coco_splits_5cls/train.json', 164, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/coco_splits_5cls/test.json', 60, ['eye'])
      ('data/raw/OpenSurgery_Dataset/04_handtool/coco_splits_5cls/val.json', 27, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/12/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/03/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/08/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/13/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/06/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/07/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/05/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/02/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/11/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/09/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/15/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/14/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/04/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/01/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/10/annotations.json', 1, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/coco_splits_4cls/train.json', 391, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/coco_splits_4cls/test.json', 68, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/coco_splits_4cls/val.json', 66, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/10_1/10_1.json', 48, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/15_1/15_1.json', 31, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/14_2/14_2.json', 17, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/08_1/08_1.json', 35, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/01_1/01_1.json', 12, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/12_1/12_1.json', 9, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/13_1/13_1.json', 15, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/06_1/06_1.json', 42, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/06_2/06_2.json', 39, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/03_2/03_2.json', 44, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/04_2/04_2.json', 7, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/02_1/02_1.json', 30, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/07_1/07_1.json', 22, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/05_1/05_1.json', 24, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/10_2/10_2.json', 3, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/15_2/15_2.json', 11, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/04_1/04_1.json', 13, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/09_1/09_1.json', 15, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/08_2/08_2.json', 18, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/11_1/11_1.json', 27, ['eye', 'gaze'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/03_1/03_1.json', 4, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/07_2/07_2.json', 2, ['eye'])
      ('data/raw/OpenSurgery_Dataset/02_hand/json_per_video/14_1/14_1.json', 72, ['eye'])
      ('data/annotations/egosurgery_hts/tool_seg/train.json', 25, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts/tool_seg/test.json', 13, ['eye'])
      ('data/annotations/egosurgery_hts/tool_seg/extra.json', 6, ['eye'])
      ('data/annotations/egosurgery_hts/tool_seg/val.json', 8, ['eye'])
      ('data/annotations/egosurgery_hts/hand_tool_seg/train.json', 367, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts/hand_tool_seg/test.json', 54, ['eye'])
      ('data/annotations/egosurgery_hts/hand_tool_seg/extra.json', 80, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts/hand_tool_seg/val.json', 62, ['eye'])
      ('data/annotations/egosurgery_hts/hand_seg/train.json', 342, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts/hand_seg/test.json', 56, ['eye'])
      ('data/annotations/egosurgery_hts/hand_seg/extra.json', 83, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts/hand_seg/val.json', 59, ['eye'])
      ('data/annotations/egosurgery_hts_bak/tool_seg/test.json.bak', 13, ['eye'])
      ('data/annotations/egosurgery_hts_bak/tool_seg/train.json.bak', 25, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts_bak/tool_seg/val.json.bak', 8, ['eye'])
      ('data/annotations/egosurgery_hts_bak/tool_seg/extra.json.bak', 6, ['eye'])
      ('data/annotations/egosurgery_hts_bak/hand_tool_seg/test.json.bak', 54, ['eye'])
      ('data/annotations/egosurgery_hts_bak/hand_tool_seg/train.json.bak', 367, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts_bak/hand_tool_seg/val.json.bak', 62, ['eye'])
      ('data/annotations/egosurgery_hts_bak/hand_tool_seg/extra.json.bak', 80, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts_bak/hand_seg/test.json.bak', 56, ['eye'])
      ('data/annotations/egosurgery_hts_bak/hand_seg/train.json.bak', 342, ['eye', 'gaze'])
      ('data/annotations/egosurgery_hts_bak/hand_seg/val.json.bak', 59, ['eye'])
      ('data/annotations/egosurgery_hts_bak/hand_seg/extra.json.bak', 83, ['eye', 'gaze'])

### B2d. 語の出現の分類（鍵・64 字以下の値・長い文字列）

    hit files 214
    keys matching: {'eye': 14}
    short string values matching:
      15 ('categories/[]/name', 'Eye')
    long strings (>64 chars) containing match, by json path:
      5759 []/segmentation/counts ctx: ';d:QE[Eo:e:REZEn:e:TEYEn:e:TEYEm:f:TEZEm:d:'

### B2e〜g. 鍵 eye と分類 Eye の中身

    data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/01/annotations.json ['images', 'categories', 'annotations', 'licenses', 'info']
    categories: [{'supercategory': '', 'id': 9, 'name': 'Eye'}] n_cat 38
    Eye anns 1698 {'id': 0, 'image_id': 0, 'category_id': 9, 'segmentation': '...', 'area': 6480.0, 'bbox': [978, 919, 108, 59], 'iscrowd': 0}
    KEY eye in data/raw/OpenSurgery_Dataset/05_egosurgery_hts/json_per_video_5cls/14_2/14_2toolscount_byhand.json [(('left hand', 'eye'), 0), (('right hand', 'eye'), 0)]

    categories: [(1, 'BiClamp'), (2, 'Bipolar Forceps'), (3, 'Bone Curette'), (4, 'Caliper'), (5, 'Chisel'), (6, 'Cup'), (7, 'Drill'), (8, 'Electric Cautery'), (9, 'Eye'), (10, "First Person's Left Hand"), (11, "First Person's Right Hand"), (12, 'Forceps'), (13, 'Gauze'), (14, 'Hammer'), (15, 'Hook'), (16, 'Kidney Dish'), (17, 'Malleable Retractor'), (18, 'Mouth Gag'), (19, 'Nasogastric Tube'), (20, 'Needle Holders'), (21, "Other Person's Left Hand"), (22, "Other Person's Right Hand"), (23, 'Pen'), (24, 'Petri Dish'), (25, 'Raspatory'), (26, 'Retractor'), (27, 'Ruler'), (28, 'Scalpel'), (29, 'Scissors'), (30, 'Screwdriver'), (31, 'Skewer'), (32, 'Spoon'), (33, 'Suction Cannula'), (34, 'Suction Tube'), (35, 'Suture, Suture Needle'), (36, 'Syringe'), (37, 'Trephine'), (38, 'Tweezers')]
    images 982 {'id': 0, 'width': 1920, 'height': 1080, 'file_name': '01_1_1041.jpg', 'license': None, 'flickr_url': None, 'coco_url': None, 'date_captured': None, 'flickr_640_url': None}

    video n_images imgs_with_Eye per_img_dist  bbox_w_median bbox_h_median
    01 982 951 {1: 205, 2: 745, 3: 1} 80.0 39.0
    02 531 321 {1: 202, 2: 119} 45.0 33.0
    03 1472 231 {1: 133, 2: 98} 116 36
    04 1415 0 {} - -
    05 1466 750 {1: 289, 2: 461} 131 55
    06 1905 758 {1: 410, 2: 347, 3: 1} 110 41
    07 2157 1 {1: 1} 337 321
    08 1603 196 {1: 128, 2: 68} 113.5 40.0
    09 591 0 {} - -
    10 1216 1047 {1: 355, 2: 691, 3: 1} 107.0 42.0
    11 888 0 {} - -
    12 1191 0 {} - -
    13 1056 0 {} - -
    14 1957 4 {1: 4} 419.0 427.5
    15 1130 880 {1: 350, 2: 530} 47.0 51.0

### B3. 記録（data/ の md、docs/、git log）

    ## B3 data/ の README・AUDIT・md
    --- md files scanned:
    20
    ## B3 docs/ (EgoSurgery の記述)
    docs/evidence/reports/A2-research-follow_claude.md
    docs/evidence/reports/A2-research_claude.md
    docs/evidence/2026-10-18-C-d2p-interface.md
    docs/evidence/verification/2026-10-21-A-phase-tower-candidates.md
    docs/evidence/reports/deep-research-report-C2.md
    docs/proposals/briefs/2026-10-23-ptower-pretraining-critique-brief.md
    docs/evidence/2026-09-16-A-phase-tower-candidates.md
    docs/evidence/reports/A-chatgpt.md
    docs/evidence/reports/A2-deep-research-report.md
    docs/evidence/reports/A3-research_claude.md
    docs/evidence/reports/A3-deep-research-report.md
    docs/evidence/2026-10-21-A-phase-tower-candidates.md
    docs/evidence/verification/2026-10-21-A-phase-tower-candidates.json
    docs/proposals/briefs/2026-10-23-ptower-pretraining-generation-brief.md
    docs/proposals/2026-10-23-ptower-pretraining.md
    ## B3 git log 文言
    --- count
    0

### B3b. docs/ の該当行（データの所在に関わるもの）

    docs/evidence/reports/A2-research_claude.md:548:- **EgoSurgery-Phase を評価に使った論文**：原論文と SurgMotion のほかには、規約がはっきりした報告はなかった（約 27 件を確認）。視線を時間モデルに入れた後続研究も見つからなかった
    docs/evidence/reports/A2-research-follow_claude.md:61:- コード・重み：データは R2 で配布、コードの記載なし／追加データ：視線／重なり：該当なし
    docs/evidence/2026-10-18-C-d2p-interface.md:57:| 一人称開放手術の工程認識・視線の補助表現（報告の系統表には無く、詳細記録の系統欄から起票者が足した） | EgoSurgery-Phase | 不明 | 2026 までの査読比較表を確認せず | C-02 |
    docs/evidence/2026-10-18-C-d2p-interface.md:110:| C-02 | 一人称（頭部装着カメラ） | 開放手術 | 工程認識。視線も提供し、GGMAE は視線を事前学習のマスクの事前分布に使う | 要旨では online／offline の因果の規約は不明 | 約 15 時間、9 工程。動画本数は報告が確認した要旨に記載なし | GGMAE と工程モデル。独立に
    docs/evidence/2026-10-18-C-d2p-interface.md:141:| C-02 | 一人称開放手術の工程認識／視線の補助表現 | 不明（2026 までの査読比較表を確認していない） | EgoSurgery-Phase | 一人称: 該当。少数動画: 依頼の設定には該当するが本文の動画本数を再確認できず。online: 不明 |
    docs/evidence/2026-10-18-C-d2p-interface.md:299:5. **EgoSurgery の 15 本の術具 box 注釈と 21 本の工程注釈を同じ研究で結ぶ既発表の論文。** 検索語: EgoSurgery tool detection／EgoSurgery instrument detection bounding box／EgoSurgery open surgery object detection／EgoSurgery phase tool。確認できた査読の一次文献は EgoSurgery-Phase（C-02）で、要旨
    docs/evidence/reports/deep-research-report-C2.md:55:- 課題の形: 頭部装着カメラの開放手術映像から surgical phase を認識。gaze も提供し、GGMAE では gaze を pretraining の masking prior に使う。 citeturn24view0
    docs/evidence/reports/deep-research-report-C2.md:421:ユーザー既所持の Digital-Twin-based Scene Representation を除くと、今回2024〜2026で確認した文献では、**strictな「instrument/object prediction output をphase recognizerへ明示入力」**を本文レベルで追加確認できなかった。PhaKIRは phase と instrument localization/segmentation を同じ13本で評
    docs/evidence/reports/deep-research-report-C2.md:427:検索語群は `EgoSurgery tool detection`, `EgoSurgery instrument detection bounding box`, `EgoSurgery open surgery object detection`, `EgoSurgery phase tool`。確認できた査読一次文献は EgoSurgery-Phase で、要旨ではphase recognitionとgazeを扱う。**ユーザーが記述した15本の術具box annotationを使い、tool de
    docs/evidence/reports/A3-research_claude.md:6:- 問い (1)(2)：EgoSurgery の上で SSL を行った唯一の研究が GGMAE である。視線でマスクを誘導すると Jaccard 33.9 で、ランダムマスク（30.6）より +3.3、スクラッチ学習（27.1）より +6.8 高い（Table 2・Table 3a）。ただし温度 τ=0.25 にすると 27.2 まで落ち、スクラッチ並みにな
    docs/evidence/reports/A3-research_claude.md:15:| S2 事前知識でマスクを選ぶ／損失に重みをつける（視線・動き） | GGMAE, SurgMotion, MME | 新興（EgoSurgery, 一般映像） | 3 |
    docs/evidence/reports/A3-research_claude.md:33:- 証拠: Table 2 の行の性質について。全行が ViT-S で、本文は "Employing the same backbone and training schema" と書いている。Table 3a のアブレーションで Tube 0.90 の Jaccard が 29.8 となり、Table 2 の VideoMAE 行の 29.8 と一致する。このことから、Table 2 の各行は「EgoSurgery の上でマス
    docs/evidence/reports/A3-research_claude.md:34:- 実装: データは公開（GitHub Fujiry0/EgoSurgery）。GGMAE のコードと重みは不明。追加で要るのは視線（Tobii）。事前学習に使った動画の範囲（学習用分割だけか）は不明。
    docs/evidence/reports/A3-research_claude.md:130:- DINOv3 や V-JEPA 2 の重みを初期値にして EgoSurgery 上で視線マスクの継続 SSL を行う組み合わせ。GGMAE はスクラッチの ViT-S しか試していない。
    docs/evidence/reports/A3-research_claude.md:148:- 提案 2: 腕として、①DINOv3 または VideoMAE V2 の重みから EgoSurgery で継続 SSL（ランダムマスクと視線マスク）、②視線 crop、③視線を注意の教師信号に使う、の 3 つを独立に足す。
    docs/proposals/briefs/2026-10-23-ptower-pretraining-critique-brief.md:32:7. **案 1**: マスク比・τ・マスクの選び方・epoch・データ範囲の 5 要因 48 点を初回にセットで回すこと。視線の無い動画（17〜21 に視線があるかはカードに無い）の扱い。A-38 の Kinetics 初期化の否定例に対して、Kinetics や ImageNet で初期化した映
    docs/evidence/reports/A-chatgpt.md:21:| **Gaze-Guided Masked Autoencoder for Surgical Phase Recognition in Open Surgery / EgoSurgery-Phase** | 著者名は今回の抽出では再確認不能。2024, MICCAI 2024. DOI `10.1007/978-3-031-72089-5_18`; arXiv `2405.19644`. citeturn1view0turn1view1 | **EgoSurgery-Phase**: open surgery、head-mounted egocentric video、10 surgery types、8 su
    docs/evidence/reports/A-chatgpt.md:87:1. **Gaze-Guided Masked Autoencoder / EgoSurgery-Phase** — open surgery、head-mounted egocentric、**14 training videos**という三点が対象設定と直接一致する。相違点は、提案法の10-frame clip が strict past-only と明記されていないことである。Table 1 と Table 2 は、同一14-video setting で TCN/Transformer/MAE vari
    docs/evidence/reports/A-chatgpt.md:99:したがって evidence map 上で tournament 候補を区別する軸は、結果順位ではなく、少なくとも **frame/clip encoder の初期化源、backbone の freeze 範囲、causal temporal head の種類、history length、multi-stage refinement の段数、smoothing/class-imbalance loss、tool/gaze auxiliary supervision の有無**である。
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:68:- 行の並び: A-01〜A-06 は EgoSurgery とその周辺、A-07〜A-22 は手術の時間モデル、A-23〜A-33 は非手術の時間モデル（行動分割・online 行動検出・一人称）、A-34〜A-52 は手術の事前学習・基盤モデル、A-53〜A-73 は一般・一人称の事前学習と視線、A-74〜A-93 は評価・区
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:103:| 視線・物体・動き・複数の信号による条件付け | GGMAE の視線、Ego-Exo、EgoSurgery-Tool／HTS、Ego4D 系（A2g） | 新興〜定番（A2g） | A2g: EgoSurgery の視線でマスクを選ぶ方式に直接の証拠 | A-01、A-61、A-03、A-04 |
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:145:| 事前知識でマスクを選ぶ・損失に重みをつける（視線・動き・物体） | GGMAE、SurgMotion、MME（A3c S2）。GGMAE（視線）、SurgMotion（動き）、Object-Aware VLP（物体）（A3g） | 新興（A3c、A3g） | A3c: EgoSurgery と一般映像。A3g: EgoSurgery では視線に直接の肯定的な証拠が
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:314:| A-01 | 一人称（術者の頭部の Tobii カメラ。A2c） | 開放手術（10 術式、術者 8 人） | RGB の映像（と視線）から 9 工程をフレームごとに予測する。GGMAE は 10 フレームのクリップ（224²）を入力にする（A2c、A3c、A3g） | 不明（全報告）。クリップの中で予測す
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:436:| A-01 | 対象データ上の映像 MAE（マスク方式の改変）、視線でマスクを選ぶ事前学習。Table 1 は時間モデルの比較を含む（PhaseLSTM、PhaseNet、TeCNO、Trans-SVNet、NETE） | A2c は EgoSurgery の原典の基準値の群とし、ほかに原典の基準値の群は無いと書く。A2g は定番の
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:503:| A-68 | 視線を注意の教師に使う（一人称から手術への転移） | 報告に記載なし | JIGSAWS | 開放手術・EgoSurgery では測っていない |
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:804:| A-01 | データは GitHub（Fujiry0/EgoSurgery）で配布（A2c は「公開予定と記載」。A-06）。GGMAE のコードと重みは不明（A3c）。A3g は公式の GitHub を確認したと書く。A2g はデータのリポジトリは公開、ライセンスは不明と書く | 視線のヒートマップ（Tobii）。クラス
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:967:- **EgoSurgery-Phase を評価に使った論文。** 原論文と SurgMotion のほかに、規約がはっきりした報告は無かった（約 27 件を確認）。視線を時間モデルに入れた後続の研究も見つからない
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:1096:2. DINOv3 や V-JEPA 2 の重みを初期値にし、EgoSurgery の上で視線マスクの継続 SSL を行う組み合わせ。GGMAE はスクラッチの ViT-S しか試していない
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:1139:組み合わせだけを移した（旧地図の「未検証の理由の仮説」は報告者の読みのため起票者用の文書に移した）: GGMAE／VideoMAE 系の対象領域の事前学習 ＋ 因果的な TeCNO／LoViT 型のヘッド（EgoSurgery-Phase）／手術の masked-video 事前学習 ＋ 凍結・部分凍結の backbo
    docs/evidence/2026-10-21-A-phase-tower-candidates.md:1267:検索日の記録は無い。検索語（旧地図の記載）: 同じ領域 — Trans-SVNet／LoViT／EndoNet／Dissecting SSL for surgical CV／EgoSurgery-Phase GGMAE／SurgMAE／surgical video pretraining／AutoLaparo／Cataract-101／surgical foundation video-language。一般の機構 — temporal action segmentation Breakfast 50Salad
    docs/evidence/reports/A3-deep-research-report.md:5:本調査では、**「対象データ自身での SSL」「手術ドメインの大規模事前学習」「一般画像・一般動画基盤モデル」「一人称動画基盤モデル」「視線・動き・物体を使う prior-guided masking」「online/causal 推論」「評価時のデータ漏れ」**を別系統として追った。特に
    docs/evidence/reports/A3-deep-research-report.md:11:| prior-guided masking / weighting | GGMAE（gaze）、SurgMotion（motion）、Object-Aware VLP（object） | **新興**。EgoSurgery では gaze に直接の positive evidence がある | 3 |
    docs/evidence/reports/A3-deep-research-report.md:54:- **[実装] コード・重み:** official GitHub を確認。視線データが追加で必要。citeturn1search2
    docs/evidence/reports/A3-deep-research-report.md:55:- **[要点]:** **GGMAE は同一 EgoSurgery 実験内で gaze masking の正の効果を示すが、「一般重みより良い」という実験ではなく、SSL に test videos が入っていないことも確認できない。**
    docs/evidence/reports/A3-deep-research-report.md:256:**prior-guided masking の中では、今回もっとも強く対象条件に一致する証拠は gaze**であり、EgoSurgery 上で random mask と mask ratio を揃えて +3.3 Jaccard。ただし temperature の選択だけで 6.7 pp 動く。motion は SurgMotion が有望だが複数の新要素を同時導入しており純粋効果を切
    docs/evidence/reports/A3-deep-research-report.md:374:視線 prior は「一般論として面白い」だけでなく、**まさに同一 dataset 上に controlled evidence が存在する**点で motion/object/saliency より優先度が高い。
    docs/evidence/reports/A3-deep-research-report.md:482:同時に、EgoSurgery 自身には **視線という、他の surgical foundation model が持っていない非常に強い domain prior** がある。GGMAE の +3.3 Jaccard という controlled mask result は、この signal を捨てる理由がないことを示す。citeturn4view0
    docs/evidence/reports/A2-deep-research-report.md:54:| **視線・物体・motion/multimodal conditioning** | GGMAE gaze, Ego-Exo, EgoSurgery-Tool/HTS, Ego4D 系 | temporal model とは直交 | EgoSurgery gaze-guided masking に直接証拠 | **新興～定番**。一人称では特に重要。citeturn19academia31turn21search21turn21search24 | 1 |
    docs/proposals/briefs/2026-10-23-ptower-pretraining-generation-brief.md:44:2. **初期化源は設計の水準で、カードと批判会話を通してから契約にする**（2026-10-03）。候補に入れてよいもの: 無ラベルの手術動画での自己教師あり事前学習（視線データは利用者が用意できる。視線でマスクを選ぶ型を含む）、内視鏡・腹
    docs/proposals/briefs/2026-10-23-ptower-pretraining-generation-brief.md:62:- 視線データの使い方（事前学習のマスクの選択に限る／入力やマスクの教師にも使う）。推論時に視線を使う案は、推論時の入力が RGB だけでない点を #16 に書く

### B-PC. 陽性対照 egosurgery_phase/*.csv（名前・記録。内容は B2c の `Frame,Phase` 89 本に含まれる）

    ## PC method1 names: same find form, pattern phase, csv
    43
    ## PC method3 records
    27:│   ├── egosurgery_phase/      工程ラベル CSV（Git 管理）               368K
    101:工程の frames は `annotations/egosurgery_phase/*.csv` の行数で、術具注釈の画像数とは数え方が違う。
    181:### 4.2 工程（`egosurgery_phase/`、Git 管理）
    248:| **管理する** | `data/README.md`、`data/splits/*`、`annotations/egosurgery_tool/instances_*.json`、`annotations/egosurgery_phase/*.csv`、`annotations/` 直下の監査 Markdown と `egosurergyhts_open`、`eval_staging/` の 2 リンク、空ディレクトリの `.gitkeep`（17 件） |
    d1199a38 feat(data): 追加動画 17〜21 の工程の注釈 20 件を今の場所のまま追跡し、折り表の生成器を 15 動画に絞る

### B4. 利用者への問い合わせと公式配布

- 問い（三つの方法で見つからなかった後）: 置き場の心当たり。答えは「data/rawに今送った」。外部の読み取りについての答えは「読んでよい（推奨）」
- `ctxpack` は andrew に無い（`ctxpack not found`）。WebFetch で読んだ（取得はしていない）
- `https://github.com/Fujiry0/EgoSurgery`: Gaze data provided / File format / Column names / Coordinate system / Units / Sampling rate / How gaze maps to frames / File sizes はすべて "Not mentioned"。"Please kindly fill out the google form" "We will send you a download link."
- `https://raw.githubusercontent.com/Fujiry0/EgoSurgery/main/README.md`: "The page does not mention gaze or eye tracking, annotation file formats, or directory structure, and it doesn't give a direct download URL."

### B5. 届いた data/raw/gaze/

    2026-10-23 07:10:46 UTC
    total 1724
    drwxrwxr-x 2 ubuntu ubuntu  4096 2024-07-26 12:00:16.000000000 +0000 .
    drwxrwxr-x 7 ubuntu ubuntu  4096 2026-10-23 07:01:04.626566557 +0000 ..
    -rw-rw-r-- 1 ubuntu ubuntu 42008 2024-07-26 11:56:34.000000000 +0000 01_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 26320 2024-07-26 11:56:34.000000000 +0000 02_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu  4992 2024-07-26 11:56:34.000000000 +0000 03_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 53650 2024-07-26 11:56:34.000000000 +0000 03_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu  8408 2024-07-26 11:56:34.000000000 +0000 03_3.csv
    -rw-rw-r-- 1 ubuntu ubuntu 53304 2024-07-26 11:56:34.000000000 +0000 04_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 17426 2024-07-26 11:56:34.000000000 +0000 04_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 53538 2024-07-26 11:56:34.000000000 +0000 05_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu  8642 2024-07-26 11:56:34.000000000 +0000 05_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 53060 2024-07-26 11:56:34.000000000 +0000 06_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 24246 2024-07-26 11:56:34.000000000 +0000 06_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 54638 2024-07-26 11:56:34.000000000 +0000 07_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 23254 2024-07-26 11:56:34.000000000 +0000 07_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 53448 2024-07-26 11:56:34.000000000 +0000 08_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 20458 2024-07-26 11:56:34.000000000 +0000 08_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 31624 2024-07-26 11:56:34.000000000 +0000 09_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 53140 2024-07-26 11:56:34.000000000 +0000 10_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu  9498 2024-07-26 11:56:34.000000000 +0000 10_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 43460 2024-07-26 11:56:34.000000000 +0000 11_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 59818 2024-07-26 11:56:34.000000000 +0000 12_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu  9110 2024-07-26 11:56:34.000000000 +0000 12_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 38344 2024-07-26 11:56:34.000000000 +0000 13_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 55272 2024-07-26 11:56:34.000000000 +0000 14_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 16704 2024-07-26 11:56:34.000000000 +0000 14_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 55474 2024-07-26 11:56:34.000000000 +0000 15_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 16558 2024-07-26 11:56:34.000000000 +0000 15_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 23642 2024-07-26 11:56:34.000000000 +0000 16_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu  8840 2024-07-26 11:56:34.000000000 +0000 16_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 53468 2024-07-26 11:56:34.000000000 +0000 17_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 17948 2024-07-26 11:56:34.000000000 +0000 17_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 22594 2024-07-26 11:56:34.000000000 +0000 18_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 23780 2024-07-26 11:56:34.000000000 +0000 18_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 54464 2024-07-26 11:56:34.000000000 +0000 19_1.csv
    -rw-rw-r-- 1 ubuntu ubuntu 16114 2024-07-26 11:56:34.000000000 +0000 19_2.csv
    -rw-rw-r-- 1 ubuntu ubuntu 48002 2024-07-26 11:56:34.000000000 +0000 19_3.csv
    -rw-rw-r-- 1 ubuntu ubuntu  3646 2024-07-26 11:56:34.000000000 +0000 19_4.csv
    -rw-rw-r-- 1 ubuntu ubuntu 19096 2024-07-26 11:56:34.000000000 +0000 19_5.csv
    files: 57
    1.7M	data/raw/gaze
         57 csv
    .gitignore:6:data/raw/**	data/raw/gaze/x

## C. 形式

    19_6.csv
    20_10.csv
    20_11.csv
    20_12.csv
    20_13.csv
    20_14.csv
    20_15.csv
    20_2.csv
    20_3.csv
    20_4.csv
    20_5.csv
    20_6.csv
    20_7.csv
    20_8.csv
    20_9.csv
    21_1.csv
    21_2.csv
    21_3.csv
    21_4.csv
    21_5.csv
    ## 01_1.csv head
    Frame,norm_pos_x,norm_pos_y
    01_1_0001,0.7777,0.7777
    01_1_0002,0.7777,0.7777
    01_1_0003,0.7026,0.7026
    01_1_0004,0.6380166666666667,0.6380166666666667
    01_1_0005,0.6571,0.6571
    01_1_0006,0.648275,0.648275
    01_1_0007,0.6867,0.6867
    ## tail
    01_1_1350,0.524375,0.524375
    01_1_1351,0.25505,0.25505
    01_1_1352,0.6406000000000001,0.6406000000000001
    ## 17_1.csv head
    Frame,norm_pos_x,norm_pos_y
    17_1_0001,0.5961,0.5961
    17_1_0002,0.491475,0.491475
    17_1_0003,0.65815,0.65815
    17_1_0004,0.5601,0.5601
    ## headers
         57 Frame,norm_pos_x,norm_pos_y
    (eval):1: command not found: file

### C2. 全行の x==y・NaN・重複・範囲

    rows 49940 x==y 49940 nan 0 empty 0 badlen 0 dupkeys 0 outside[0,1] 0 min [0.002, 0.002] max [0.99634, 0.99634]
    files where x!=y on some row: []
    per file (name,rows,x==y,nan,dup):
      ('01_1.csv', 1352, 1352, 0, 0)
      ('02_1.csv', 827, 827, 0, 0)
      ('03_1.csv', 156, 156, 0, 0)
      ('03_2.csv', 1687, 1687, 0, 0)
      ('03_3.csv', 261, 261, 0, 0)
      ('04_1.csv', 1684, 1684, 0, 0)
      ('04_2.csv', 536, 536, 0, 0)
      ('05_1.csv', 1682, 1682, 0, 0)
      ('05_2.csv', 266, 266, 0, 0)
      ('06_1.csv', 1679, 1679, 0, 0)
      ('06_2.csv', 748, 748, 0, 0)
      ('07_1.csv', 1689, 1689, 0, 0)
      ('07_2.csv', 720, 720, 0, 0)
      ('08_1.csv', 1681, 1681, 0, 0)
      ('08_2.csv', 643, 643, 0, 0)
      ('09_1.csv', 1022, 1022, 0, 0)
      ('10_1.csv', 1682, 1682, 0, 0)
      ('10_2.csv', 311, 311, 0, 0)
      ('11_1.csv', 1360, 1360, 0, 0)
      ('12_1.csv', 1689, 1689, 0, 0)
      ('12_2.csv', 269, 269, 0, 0)
      ('13_1.csv', 1189, 1189, 0, 0)
      ('14_1.csv', 1684, 1684, 0, 0)
      ('14_2.csv', 513, 513, 0, 0)
      ('15_1.csv', 1682, 1682, 0, 0)
      ('15_2.csv', 516, 516, 0, 0)
      ('16_1.csv', 741, 741, 0, 0)
      ('16_2.csv', 280, 280, 0, 0)
      ('17_1.csv', 1683, 1683, 0, 0)
      ('17_2.csv', 565, 565, 0, 0)
      ('18_1.csv', 581, 581, 0, 0)
      ('18_2.csv', 613, 613, 0, 0)
      ('19_1.csv', 1682, 1682, 0, 0)
      ('19_2.csv', 506, 506, 0, 0)
      ('19_3.csv', 1488, 1488, 0, 0)
      ('19_4.csv', 108, 108, 0, 0)
      ('19_5.csv', 590, 590, 0, 0)
      ('19_6.csv', 1692, 1692, 0, 0)
      ('20_10.csv', 772, 772, 0, 0)
      ('20_11.csv', 623, 623, 0, 0)
      ('20_12.csv', 1505, 1505, 0, 0)
      ('20_13.csv', 60, 60, 0, 0)
      ('20_14.csv', 296, 296, 0, 0)
      ('20_15.csv', 1649, 1649, 0, 0)
      ('20_2.csv', 686, 686, 0, 0)
      ('20_3.csv', 4, 4, 0, 0)
      ('20_4.csv', 417, 417, 0, 0)
      ('20_5.csv', 367, 367, 0, 0)
      ('20_6.csv', 283, 283, 0, 0)
      ('20_7.csv', 91, 91, 0, 0)
      ('20_8.csv', 64, 64, 0, 0)
      ('20_9.csv', 184, 184, 0, 0)
      ('21_1.csv', 104, 104, 0, 0)
      ('21_2.csv', 899, 899, 0, 0)
      ('21_3.csv', 1276, 1276, 0, 0)
      ('21_4.csv', 1686, 1686, 0, 0)
      ('21_5.csv', 917, 917, 0, 0)

### C3. 解像度（全数）

    missing manifest images 0
    ('01-15', (1920, 1080)) 17233
    17-21 jpg 10461
    ('17-21', (1920, 1080)) 10461

### C4. x==y の扱いの問い合わせ

問い: 全行で x==y であり、書き出しの不具合に見える。答えは「このまま記録して進める（推奨）」。

## D・E. 被覆・範囲・ヒートマップ（`.venv/bin/python experiments/analysis/gaze_data_survey/survey.py`）

    {"resolution": {"1920x1080": 17233}, "gaze_rows": 49940, "gaze_unique_frames": 49940, "samples_per_frame": {"min": 1, "median": 1.0, "max": 1}, "x_eq_y": 49940, "min_xy": [0.002, 0.002], "max_xy": [0.99634, 0.99634], "gaze_videos": {"01": 1352, "02": 827, "03": 2104, "04": 2220, "05": 1948, "06": 2427, "07": 2409, "08": 2324, "09": 1022, "10": 1993, "11": 1360, "12": 1958, "13": 1189, "14": 2197, "15": 2198, "16": 1021, "17": 2248, "18": 1194, "19": 6066, "20": 7001, "21": 4882}, "gaze_clips_outside_targets": ["03_1", "12_2", "15_2", "16_1", "16_2", "17_2", "20_10", "20_11", "20_12", "20_13", "20_14", "20_15", "20_3", "20_9"], "gaze_frames_not_in_targets": 22254, "01-15": {"ann_rows": 17233, "ann_with_gaze": 17233, "img_files": 15437, "img_with_gaze": 15437, "inside": 17233}, "17-21": {"ann_rows": 10461, "ann_with_gaze": 10453, "img_files": 10461, "img_with_gaze": 10453, "inside": 10453}, "heatmap": {"frame": "01_1_0004", "norm_xy": [0.6380166666666667, 0.6380166666666667], "sigma_px": 64.0, "shape_hw": [1080, 1920], "max": 0.9999995815430563, "argmax_xy_px": [1225, 689], "gaze_xy_px": [1224.992, 689.058]}}

### D2. 動画ごとの表、欠けた 8 枚、クリップごとの範囲

    video set ann_rows ann_with_gaze img_files img_with_gaze inside
    01 01-15 999 999 913 913 999
    02 01-15 529 529 461 461 529
    03 01-15 1363 1363 1089 1089 1363
    04 01-15 1643 1643 1329 1329 1643
    05 01-15 1318 1318 1225 1225 1318
    06 01-15 1447 1447 1379 1379 1447
    07 01-15 1788 1788 1711 1711 1788
    08 01-15 1591 1591 1400 1400 1591
    09 01-15 672 672 518 518 672
    10 01-15 1232 1232 997 997 1232
    11 01-15 865 865 754 754 865
    12 01-15 619 619 609 609 619
    13 01-15 843 843 822 822 843
    14 01-15 1858 1858 1810 1810 1858
    15 01-15 466 466 420 420 466
    17 17-21 56 56 56 56 56
    18 17-21 946 946 946 946 946
    19 17-21 5179 5179 5179 5179 5179
    20 17-21 1560 1552 1560 1552 1552
    21 17-21 2720 2720 2720 2720 2720
    17_1 phase 17_1_1504 .. 17_1_1569 56  gaze 17_1_0001 .. 17_1_1683 1683  missing 0
    18_1 phase 18_1_0080 .. 18_1_0581 388  gaze 18_1_0001 .. 18_1_0581 581  missing 0
    18_2 phase 18_2_0001 .. 18_2_0600 558  gaze 18_2_0001 .. 18_2_0613 613  missing 0
    19_1 phase 19_1_0100 .. 19_1_1681 1364  gaze 19_1_0001 .. 19_1_1682 1682  missing 0
    19_2 phase 19_2_0001 .. 19_2_0506 437  gaze 19_2_0001 .. 19_2_0506 506  missing 0
    19_3 phase 19_3_0008 .. 19_3_1488 1245  gaze 19_3_0001 .. 19_3_1488 1488  missing 0
    19_4 phase 19_4_0001 .. 19_4_0108 106  gaze 19_4_0001 .. 19_4_0108 108  missing 0
    19_5 phase 19_5_0001 .. 19_5_0590 561  gaze 19_5_0001 .. 19_5_0590 590  missing 0
    19_6 phase 19_6_0002 .. 19_6_1691 1466  gaze 19_6_0001 .. 19_6_1692 1692  missing 0
    20_2 phase 20_2_0064 .. 20_2_0686 473  gaze 20_2_0001 .. 20_2_0686 686  missing 0
    20_4 phase 20_4_0001 .. 20_4_0417 414  gaze 20_4_0001 .. 20_4_0417 417  missing 0
    20_5 phase 20_5_0001 .. 20_5_0367 335  gaze 20_5_0001 .. 20_5_0367 367  missing 0
    20_6 phase 20_6_0001 .. 20_6_0284 278  gaze 20_6_0001 .. 20_6_0283 283  missing 1
    20_7 phase 20_7_0079 .. 20_7_0098 20  gaze 20_7_0001 .. 20_7_0091 91  missing 7
    20_8 phase 20_8_0018 .. 20_8_0064 40  gaze 20_8_0001 .. 20_8_0064 64  missing 0
    21_1 phase 21_1_0001 .. 21_1_0090 69  gaze 21_1_0001 .. 21_1_0104 104  missing 0
    21_2 phase 21_2_0108 .. 21_2_0898 464  gaze 21_2_0001 .. 21_2_0899 899  missing 0
    21_3 phase 21_3_0001 .. 21_3_1276 862  gaze 21_3_0001 .. 21_3_1276 1276  missing 0
    21_4 phase 21_4_0001 .. 21_4_1685 1122  gaze 21_4_0001 .. 21_4_1686 1686  missing 0
    21_5 phase 21_5_0001 .. 21_5_0751 203  gaze 21_5_0001 .. 21_5_0917 917  missing 0
    missing frames: ['20_6_0284', '20_7_0092', '20_7_0093', '20_7_0094', '20_7_0095', '20_7_0096', '20_7_0097', '20_7_0098']
    {'frame': '01_1_0004', 'norm_xy': [0.6380166666666667, 0.6380166666666667], 'sigma_px': 64.0, 'shape_hw': [1080, 1920], 'max': 0.9999995815430563, 'argmax_xy_px': [1225, 689], 'gaze_xy_px': [1224.992, 689.058]}

### D3. 空振りでないことの確認

写しは scratchpad に置いた。一回目は無効だった。動画を抜く対照は rm が確認を求めて抜けず、画面外の対照で書き換えた 05_1_0001 は manifest に無いフレームだった。二回目が有効である。

    ## control drop video 05
    {'01-15': {'ann_rows': 17233, 'ann_with_gaze': 17233, 'img_files': 15437, 'img_with_gaze': 15437, 'inside': 17233}, '17-21': {'ann_rows': 10461, 'ann_with_gaze': 10453, 'img_files': 10461, 'img_with_gaze': 10453, 'inside': 10453}} [0.6380166666666667, 0.6380166666666667] [1225, 689]
    ## control out-of-screen 05_1_0001 -> (1.2,1.2)
    {'01-15': {'ann_rows': 17233, 'ann_with_gaze': 17233, 'img_files': 15437, 'img_with_gaze': 15437, 'inside': 17233}, '17-21': {'ann_rows': 10461, 'ann_with_gaze': 10453, 'img_files': 10461, 'img_with_gaze': 10453, 'inside': 10453}} [0.6380166666666667, 0.6380166666666667] [1225, 689]
    ## control move heat point to (0.2,0.3)
    {'01-15': {'ann_rows': 17233, 'ann_with_gaze': 17233, 'img_files': 15437, 'img_with_gaze': 15437, 'inside': 17233}, '17-21': {'ann_rows': 10461, 'ann_with_gaze': 10453, 'img_files': 10461, 'img_with_gaze': 10453, 'inside': 10453}} [0.2, 0.3] [384, 324]
    ## original data untouched
    0
    01c4c883200adf53b5707b92a51264ee  data/raw/gaze/05_1.csv
    ## control drop video 05 (05_1, 05_2 removed in copy)
    {'01-15': {'ann_rows': 17233, 'ann_with_gaze': 15915, 'img_files': 15437, 'img_with_gaze': 14212, 'inside': 15915}, '17-21': {'ann_rows': 10461, 'ann_with_gaze': 10453, 'img_files': 10461, 'img_with_gaze': 10453, 'inside': 10453}} [0.6380166666666667, 0.6380166666666667] [1225, 689]
    05,01-15,1318,0,1225,0,0
    ## control out-of-screen 05_1_0050 -> (1.2,1.2)
    {'01-15': {'ann_rows': 17233, 'ann_with_gaze': 17233, 'img_files': 15437, 'img_with_gaze': 15437, 'inside': 17232}, '17-21': {'ann_rows': 10461, 'ann_with_gaze': 10453, 'img_files': 10461, 'img_with_gaze': 10453, 'inside': 10453}} [0.6380166666666667, 0.6380166666666667] [1225, 689]
    05,01-15,1318,1318,1225,1225,1317
    ## original data untouched
    01c4c883200adf53b5707b92a51264ee  data/raw/gaze/05_1.csv
    57
    ## control x!=y on one row (01_1_0004 -> y=0.25)
    x_eq_y 49939 of 49940 heat [0.6380166666666667, 0.25] [1225, 270]

## F. 検証

### F1. forbidden-check（本体）

既定の基準 origin/phase0 は契約の開始の後に f3d5945f へ進み、PR #263・#264 の変更を含む。そのため起点 d013c5f1 を基準にしても回した。

    ## main repo
    {"base": "origin/phase0", "changed": 26, "checked": 22, "declared_allowances": ["experiments/analysis/gaze_data_survey"], "effective_allowances": ["experiments/analysis/gaze_data_survey"], "errors": [], "excluded": 4, "excluded_paths": ["context/auto/followups.md", "context/auto/results_recent.md", "context/auto/tasks_summary.csv", "tasks/inbox.md"], "generated_directories": ["context/auto/"], "ge …（status pass, violations []）
    exit=0
    ## main repo BASE=d013c5f1 (branch point)
    {'base': 'd013c5f1', 'changed': 7, 'checked': 7, 'excluded': 0, 'status': 'pass', 'violations': []}
    ['experiments/analysis/gaze_data_survey/REPORT.md', 'experiments/analysis/gaze_data_survey/coverage_by_video.csv', 'experiments/analysis/gaze_data_survey/fig_heatmap_01_1_0004.png', 'experiments/analysis/gaze_data_survey/summary.json', 'experiments/analysis/gaze_data_survey/survey.py']
    exit=0

### F2. forbidden-check の陽性対照（repo の外の clone の写し、HEAD eb36ef52、.venv は本体へのリンク。写しは削除した）

    ## clone HEAD eb36ef52, BASE=d013c5f1
    {'status': 'pass', 'violations': []}
    exit=0
    ## after git add -f data/zz_gaze_control.txt
    make: *** [Makefile:159: forbidden-check] Error 1
    {'status': 'fail', 'violations': [{'path': 'data/zz_gaze_control.txt', 'reason': '禁止領域 data/ の内側'}]}
    exit=2

### F3. 試験の後（同じ命令）

    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics - Ass...
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name - AssertionEr...
    FAILED tests/test_research_logger.py::test_log_run_idempotent - AssertionErro...
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    FAILED tests/test_stage1_ptower_r3_dist.py::test_two_gpus_give_the_one_gpu_gradient_over_an_uneven_tail
    7 failed, 959 passed, 27 warnings in 1830.90s (0:30:30)
    exit=1

### F4. 変更範囲（集合差）

    $ git diff --name-only d013c5f1 --cached（起点からの集合、commit 前の index）
    experiments/analysis/gaze_data_survey/REPORT.md
    experiments/analysis/gaze_data_survey/coverage_by_video.csv
    experiments/analysis/gaze_data_survey/fig_heatmap_01_1_0004.png
    experiments/analysis/gaze_data_survey/summary.json
    experiments/analysis/gaze_data_survey/survey.py
    tasks/T-2026-10-23-gaze-data-survey/RESULT.md
    tasks/T-2026-10-23-gaze-data-survey/SPEC.md
    tasks/T-2026-10-23-gaze-data-survey/audit.md
    tasks/T-2026-10-23-gaze-data-survey/result.yaml
    tasks/T-2026-10-23-gaze-data-survey/spec.yaml
    tasks/inbox.d/T-2026-10-23-gaze-data-survey.md
    $ 許可の外（置き場・契約のディレクトリ・受け皿の一件 以外）
    0
    $ data/ と runindex/ の変更
    0
    $ 依存の差
    NO_DEP_DIFF

## commit と送出

    $ git log --oneline d013c5f1..HEAD
    f4e7fb5c docs: report gaze data survey (T-2026-10-23-gaze-data-survey)
    eb36ef52 analysis: survey gaze data for candidate 5 pretraining plan 1
    $ gh pr view feat/gaze-data-survey --json number,baseRefName,headRefName,isDraft,state
    {"baseRefName":"phase0","headRefName":"feat/gaze-data-survey","isDraft":false,"number":265,"state":"OPEN"}

## 規約（inject_verbatim の原文。context/conventions.md、blob ceb7ef0f88a3f30279930be96ab9a5722acc2f09 は契約の conventions_rev と一致）

### conventions#prohibitions（L98〜L107）

    <a id="prohibitions"></a>
    ## prohibitions
    
    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### conventions#issuer_cautions（L154〜L191）

    <a id="issuer_cautions"></a>
    ## issuer_cautions
    
    **起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
    実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**
    
    | # | 注意 |
    |---|---|
    | 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
    | 2 | 一致 0 件なら別の異質な方法でも確認する |
    | 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
    | 4 | 仕組みの挙動は実装を読んでから信じる |
    | 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
    | 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
    | 7 | **丸めた表示を実数として扱わない** |
    | 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
    | 9 | 無変更は要約値で確かめる。表示属性では足りない |
    | 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
    | 11 | 測定の副作用が禁止領域へ触れないか確かめる |
    | 12 | **判断の前に、いま見ているものが最新かを確かめる** |
    | 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
    | 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |
    
    **注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
    確かめると 3 件とも実在した。
    
    **注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
    （`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。
    
    **注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
    （自分の命令行にその語が含まれるため）。
    
    **注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。
    
    **シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
    一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**
    
    **命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

### conventions#folds（L297〜L365）

    <a id="folds"></a>
    ## folds
    
    動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-17-fold-table` が確定）。
    本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。
    
    | 折り | test（3） | val（2） |
    |---|---|---|
    | A | 04, 05, 07 | 09, 10 |
    | B | 01, 03, 14 | 02, 08 |
    | C | 02, 08, 11 | 06, 12 |
    | D | 06, 13, 15 | 04, 05 |
    | E | 09, 10, 12 | 07, 15 |
    
    train はその折りの test と val を除いた 10 本である。
    **折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。
    各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。
    
    ### 追加 6 動画
    
    工程の注釈がある追加動画は次の 6 本である。
    
        17, 18, 19, 20, 21, 22
    
    **22 はフレーム画像が無く使えない。工程塔に足すのは 17〜21 の 5 本で、その塔を P\*-20 と呼ぶ。**
    旧称は P\*-21。古い記録の P\*-21 は P\*-20 と読み替える。
    出所: 利用者の確認と決定 2026-09-27（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、
    `tasks/T-2026-09-27-stage1-ptower-20/audit.md` の `verify_folds` の記録。
    
    **用途は訓練のみである。どの折りの test にも val にも現れない。**
    15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。
    
    ### 規律
    
    **選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
    test は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。
    
    出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-17-fold-table`。
    
    ### val と test の重なり
    
    各折りの val 2 本（計 10 本）は、どれもほかの折りの test に現れる。上の表から読める対応は次のとおり。
    
    | val の動画 | val に使う折り | test に持つ折り |
    |---|---|---|
    | 09, 10 | A | E |
    | 02, 08 | B | C |
    | 06 | C | D |
    | 12 | C | E |
    | 04, 05 | D | A |
    | 07 | E | A |
    | 15 | E | D |
    
    **val に一度も入らないのは 01・03・11・13・14 の 5 本**である。test としては折り B に 3 本（01・03・14）、
    C に 1 本（11）、D に 1 本（13）、A と E には 0 本。
    
    val で設定・処方・構造・型・止め方を選ぶ段（両塔の学び直しと Stage 2 以降）では、次の三つを守る。
    
    1. この重なりを prereg と報告に明記する
    2. test の値を報告するときは、val に一度も入らない 5 動画だけで集計した値を副次として添える。
       各動画の値は、その動画を test に持つ折りのモデルが出す。集計の仕方は prereg に書く
    3. 副次の値は、判定・関門・選定のどれにも使わない
    
    選ぶ規則（規律の小節。その折りの val で選ぶ）は変えない。
    
    出所: 利用者の決定 2026-10-19（契約 `T-2026-10-21-ops-taskstart-resume-folds-val` SPEC §2）、上の折りの表、
    `docs/stage1/design_val_subsets.md` 223 行。
    
    ---
