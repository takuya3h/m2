# audit — T-2026-11-08-grasp-cards-survey（調査。学習なし。案の採否・推奨は扱わない）

ホスト bengio（`hostname` = `Bengio`）。時刻は JST。
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-08-grasp-cards-survey`（大きな生成物と記録の原本）、
`A=experiments/analysis/grasp_cards_survey`（道具と表）。

## 0. 始める（手順書の 0〜4）

- 開始時の分岐は `feat/grasp-pilot-d-rerun`（前の契約）。`feat/grasp-cards-survey` は手元にも遠隔にも無く、契約の履歴も無い
- `scripts/task_start_classify.py` が「止める」: 未追跡・起点に無い 12 件（`experiments/analysis/dtower_rerun/tools/*.py`、4.0K〜24K、すべて禁止領域 `experiments/`）
  - 12 件とも `origin/feat/dtower-rerun`（bcebb702、T-2026-11-07-dtower-rerun）の同じ経路と中身が一致（`git show bcebb702:<経路> | cmp`）。統合前の他の契約の出力が同期で届いたもの
  - 利用者に選択肢を示し、利用者が「4 で無視に足す」を選んだ（2026-11-08 20:0x JST）。`.git/info/exclude` に次の 2 行を足した。ファイルは消していない・動かしていない

        # T-2026-11-08-grasp-cards-survey: 未統合の T-2026-11-07-dtower-rerun の出力（phase0 に無い）
        experiments/analysis/dtower_rerun/tools/

  - 分類をやり直して「通す」→ `make task-start`: `分岐を作成: feat/grasp-cards-survey（起点 origin/phase0）`、`.sync-pause を作成`、契約の取り込み `OK`、`完了`
- `make task-validate`: `OK`（0 failed）
- `make task-preflight`: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL。SKIP は P2 cuda_ext_loaded・P3 deterministic_flags（宣言なし）、P4・P5・P13・P14（analysis は対象外）、P12（解決前提の参照なし）。P9 spec_lint は該当なし

## Task A — 開始状態（G1）

記録の原本は `$S/start/`。

### A-1 分岐と起点、未追跡（`$S/start/a1_branch.txt`）

    $ git branch --show-current
    feat/grasp-cards-survey
    $ git merge-base HEAD origin/phase0; git rev-parse origin/phase0 HEAD
    a68672f1f44a94a6b8fdc41c4d6a0a918dbebf9e（3 つとも同じ）
    $ git status --porcelain --untracked-files=all
    ?? experiments/analysis/grasp_cards_survey/tools/digests.py（本契約の道具）
    ?? tasks/T-2026-11-08-grasp-cards-survey/SPEC.md、spec.yaml（取り込んだ契約）
    $ git status --porcelain --untracked-files=all --ignored -- experiments/analysis/dtower_rerun
    !! 12 件（上の 0. の 12 件。無視の一覧に入った）
    $ cat .sync-pause
    task_id=T-2026-11-08-grasp-cards-survey / branch=feat/grasp-cards-survey

### A-2 GPU（`$S/start/a3_gpu.txt`）

    $ nvidia-smi --query-gpu=index,name,uuid,memory.used,memory.total,utilization.gpu,power.limit,power.default_limit --format=csv
    0, NVIDIA RTX A6000, GPU-1b153400…, 39 MiB, 49140 MiB, 0 %, 220.00 W, 300.00 W
    1, NVIDIA RTX A6000, GPU-525aae08…, 37 MiB, 49140 MiB, 0 %, 220.00 W, 300.00 W
    $ nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv
    （見出し行だけ。grep -c . で 0 件）
    $ nvidia-smi -i 7 --query-gpu=index --format=csv,noheader     （存在しない GPU 番号の対照）
    No devices were found（rc 6）、数字で始まる行 0 件
    $ python3 scripts/grasppilot/proc_enum.py
    n_processes 67、gpu_pids []、n_compute 2（どちらも本契約の要約値の計算と、この表示の python3 -c）
    $ proc_enum.py --match-exe /usr/bin/zsh → count 9 ／ --match-exe /nonexistent/bin/python9 → count 0

- 全体量 39・37 MiB と一覧の和 0 MiB の差は 39・37 MiB。前の契約（四本目・五本目）の開始時と同じ値で、空きの装置の常駐分とみる。**本契約以外の使用なし**

### A-3 記憶領域（`$S/start/a4_df.txt`）

    $ df -B1 /home/ubuntu/slocal2 /home/ubuntu
    /dev/sdb1  Available 1,250,936,692,736 B（使用 84%）
    overlay    Available 1,372,778,037,248 B（使用 27%）

### A-4 試験と仮想環境（`$S/start/a5_pytest_start.txt`・`a5_fail_names.txt`・`a5_pkgs_*.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 980 passed, 5 skipped, 26 warnings in 48.99s
    失敗の名前（11）: test_check_spec::test_teacher_detection_rate、test_engines::test_mmdet_trainer_eval_recipe_in_metrics、
      test_fetch_task::test_rejects_unknown_file_name、test_research_logger の 4 件（test_log_run_idempotent、
      test_run_logging_invokes_log_run_on_finally、test_run_logging_no_double_post_on_normal_exit、
      test_run_logging_swallows_exception_in_user_block）、test_stage1_ptower_heads::test_existing_candidates_match_baseline[A,B,C,linear]
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 108 行 9c7be5c99d6b768a…a6682f94c0、.venv-relation-detr 72 行 a74c9c787e79f014…ad5b090（T-2026-11-05 の記録の値と一致）

- 失敗の 11 件は T-2026-11-05-grasp-tower-rebuild の開始時の 11 件と名前が同じ

### A-5 禁止の場所・重ねの BODY・重みの開始時の要約値（`$S/start/digests_start.json`、道具 `$A/tools/digests.py`）

各根の下の全ファイルを中身で sha256 し、(相対経路, 大きさ, sha256) の並びをもう一度 sha256。シンボリックリンクは辿らずリンク先の文字列で数える。
`tasks` の根は本契約のフォルダを除く。

| 根（§5 の番号） | ファイル | 大きさ B | sha256 の先頭 |
|---|---:|---:|---|
| third_party（4） | 268 | 4,388,156,080 | ebfc6fe08c6f53ba |
| 重ねの BODY `/home/ubuntu/slocal2/s2fix-bengio-body`（4） | 243 | 3,097,796 | 667933c84fdbaec3 |
| scripts（4） | 412 | 3,947,286 | 5e56a3dda26a327c |
| configs（4） | 104 | 153,073 | 8b6360005bf11707 |
| data/raw（3） | 235,773 | 10,518,871,982 | 0048147de668afd9 |
| data/external（3） | 38 | 9,692,981,482 | 37acfc82cc14610e |
| data/annotations（3） | 111 | 950,979,054 | 3d1e52b1c3fb23de |
| data/processed（3） | 246 | 12,196,174,327 | 45d582f115877b6c |
| data/splits（3） | 5 | 51 | a757e013e4e6dd5f |
| experiments/phase1/stage1_ptower_20_005_ft_…_foldA_seed42（2） | 10 | 94,413,766 | bab579d8329ef9a0 |
| experiments/phase1/grasptower_G_all_seed42（2） | 10 | 11,295 | 87d9a1cda54f9a09 |
| experiments/phase1/grasptower_G_H1_seed42（2） | 10 | 11,201 | ad7a62be86f0daa6 |
| experiments/phase1/grasptower_G_H2_seed42（2） | 10 | 13,458 | 752f993ea572bf16 |
| experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42（2） | 53 | 3,316,993,212 | 12a38ea4ed9563a6 |
| experiments/analysis/grasp_tower_rebuild（2） | 3 | 38,433 | dbeb548e43eaea2c |
| experiments/analysis/stage2_pilot_folda（2） | 107 | 594,176 | 06c2a2e3a4c2aeb5 |
| tasks（本契約を除く。2） | 1,870 | 114,310,380 | 9573527f3ece2de0 |
| 保存先 T-2026-11-05-grasp-tower-rebuild（2） | 190 | 22,410,806,115 | 1a778ed32893d3b3 |
| 保存先 T-2026-10-18-stage2-pilot-folda（2） | 30 | 1,144,270,644 | a400c01308c43a19 |

| 重み（読むだけ） | sha256 の先頭 | 照合先 |
|---|---|---|
| 工程塔の fine-tune `experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42/checkpoints/best.pth` | 79c2c4782458c981 | キャッシュを作った run（`…20_008_features…/config.yaml`）の `checkpoint_sha256` と一致。T-2026-10-18 audit 173 行とも一致 |
| 検出塔 `experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth` | 30d199b15201cf3c | `common.py` の `DET_SHA256` と一致 |
| G 確定 `…/T-2026-11-05-grasp-tower-rebuild/g/ckpt/all/best.pth` | 5ea2cbf479254d78 | 目録 `signals_manifest.json` の `g_runs.all` と一致 |
| G H1 | 5cfa055cbc72329c | 目録の `g_runs.H1` と一致 |
| G H2 | efdefccd4484fc6a | 目録の `g_runs.H2` と一致 |
| 工程塔のキャッシュ `…/efros_ptower/data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz` | c402e214d28d32c6 | — |

| 仮想環境（`uv pip freeze` の整列と site-packages の走査） | 行 | freeze の sha256 の先頭 | site-packages の sha256 の先頭 |
|---|---:|---|---|
| .venv | 108 | f6c43729f527d6f6 | 06068852c74b0712 |
| .venv-relation-detr | 72 | d072487642c095f9 | 4f0538a32b37948b |

- **工程塔の fine-tune の checkpoint の経路**: `common.py` の `PT_FT_CKPT`（`$STORE/efros_ptower/experiments/phase1/stage1_ptower_20_005_ft…/checkpoints/best.pth`）は bengio に無い（写しの置き場には 009 の時間ヘッドとキャッシュだけ）。
  repo の同じ相対経路 `experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42/checkpoints/best.pth` に在り、sha256 がキャッシュを作った run の `checkpoint_sha256` と一致したので、これを読む（読み込みの既定は変えない）

### A-6 契約の版

- `contract.conventions_rev` 2d946b07 = `git log -1 -- context/conventions.md`（一致）
- `meta.created_from.runindex_commit` 68befc3b（2026-10-29）≠ `git log -1 -- runindex/` d3e319ac（2026-11-07）。件数（見出し行を除く）も 2,363/1,130/1,736 ≠ 2,623/1,305/1,947。
  68befc3b での件数は 2,363/1,130/1,736 で起票時の値と一致したので、起票者は 10-29 の版の値を写したとみる。**実測で差し替え、`meta.amendments` に 1 件を足した**。差し替え後の `make task-validate` は `OK`

**G1: pass**（分岐 `feat/grasp-cards-survey`・起点 origin/phase0 a68672f1・開始前の未追跡は無視の一覧に入れて触れていない・本契約以外の GPU の使用なし・空き・失敗の名前・仮想環境と禁止の場所と重ねの BODY の要約値・電力の上限 220 W × 2 を記録）

## Task B — 記録と注釈から（G2）

記録の原本は `$S/b/`。表の全値は `$A/REPORT.md`。

### B-1 S2・S3（`$S/b/s2s3.json`・`s2s3.log`、道具 `$A/tools/s2s3_density.py`）

    $ .venv/bin/python -I $A/tools/s2s3_density.py --out $S/b/s2s3.json
    rc 0

- 開いたファイル（`opened_files`）: `egosurgery_tool_folds/A/instances_{train,val,test}.json`、`egosurgery_hts/hand_tool_seg/{train,val,test}.json`・`loss_mask/{train,val,test}.txt`、
  `phase_manifest/{train,val}.json`、`egosurgery_phase/<train と val の動画>_*.csv`。**test の 3 ファイルは対照（04 を混ぜた件数）のためだけに開き、画像の名前を数えた。** 画像は 1 枚も読んでいない（`images_read` 0。画像の在否は train と val の経路の stat だけ）
- フレームの数え方の二つの読み: 工程塔の目録 `phase_manifest` のフレームは術具注釈のフレームと**同じ集合**（train 9,657・val 1,515、差 0）。
  工程の CSV の全行は train 10,580・val 1,904 で、術具注釈の無い行（train 923・val 389）は `data/raw/ego/` に画像が無い（`phase_csv_without_tool_with_image` 0）。両方を表にした
- 合計（train / val）: 術具注釈 9,657 / 1,515、把持の注釈 9,356 / 1,514（持つ術具 3〜5 の注釈 1 件以上 9,164 / 1,508）、loss_mask 301 / 1（すべて術具注釈のフレームで、把持の注釈の画像とは重ならない）、
  CSV の行のうち使える把持の注釈が無い 1,224 / 390（11.6% / 20.5%。合わせて 1,614 / 12,484 = 12.9%。一本目 SPEC 251 行の「約 13%」と合う）
- S3: クリップの中で隣り合う術具注釈フレームの番号の差 Δ（0.5 fps なので 2Δ 秒）は train で n 9,644・最小 1・5% 1・中央 1・95% 2・最大 254（2〜508 秒）、val で n 1,512・1・1・1・2・189（2〜378 秒）。Δ=1 の割合 0.939 / 0.872。
  術具注釈フレームはすべて CSV の行に在り、工程の名前が目録と CSV で全件一致
- 対照: 件数の関数に test の 04 を混ぜると術具 11,172 → 12,501・把持 10,870 → 12,189・loss_mask 302 → 312（工程は test を開かないので 12,484 のまま）。存在しない 99 で全列 0。
  1 フレームずらした写しは、CSV に在る数が例えば 01 で 913 → 884、工程の名前の一致が 913 → 877 に下がる（全動画で下がる）

### B-2 S7（`$S/b/s7.json`・`s7.log`、道具 `$A/tools/s7_costs.py`）

    $ .venv/bin/python -I $A/tools/s7_costs.py --out $S/b/s7.json
    phase_iface_W1_fourth 6 本 elapsed 11.90〜187.24 s（bengio）
    phase_head_W2_GA 6 本 1.48〜6.64 s / phase_head_W3_GA 6 本 1.74〜6.68 s / W2 全型 50 本 1.38〜9.97 s / W3 全型 50 本 1.59〜7.01 s（bengio）
    phase_head_scratch_P15 1 本 7.10 s（efros、18 epoch）
    det_iface_W1_fourth 6 本 wall 18,951〜19,960 s、同時最大 6（bengio）／ det_iface_W1_fifth 2 本 14,357〜15,395 s、同時 2（五本目の分岐の版）
    det_relearn_third 3 本 36,305〜37,560 s、同時最大 2（bengio）／ det_relearn_fifth 2 本 58,830〜60,715 s、同時 2（五本目の分岐の版）
    phase_finetune_P15 16,076.4 s、21 epoch（765.5 s/epoch）、山 29.05 GB、cuda:0 1 枚（efros）
    phase_finetune_bengio_hostdiff 9,631.3 s、19 epoch（506.9 s/epoch）、山 14.87 GB/rank、2 GPU（bengio、phase_manifest_all_phase）

- 値は各契約の報告と一致: 四本目 RESULT 63 行（案 A 11.9〜187.2 秒、案 B 5 時間 15 分〜5 時間 33 分・GPU 1 枚に 3 本並行）、五本目 RESULT 47 行（案 D 16 時間 51 分・16 時間 20 分、案 B 空 4 時間 16 分・正解 3 時間 59 分）、
  三本目（`grasppilot3_d_*` の start/end、10 時間 05 分〜10 時間 26 分。五本目 RESULT の「単独 約 10 時間」）、三周目 RESULT 51 行（fine-tune 1 本 6,002〜16,240 秒）
- 五本目（T-2026-11-06-grasp-pilot-d-rerun）は phase0 に未統合なので `origin/feat/grasp-pilot-d-rerun` の版から `git show` で読んだ
- 対照: 道具は記録が無い run を値なし（None）にする。存在しない run 名では行が空（`summary` が None）

### B-3 実装を読む部分（S1-1・S4-1・S6-1・S6-3）

- S1-1: `PT_CACHE`（`all_gap.npz`、sha256 c402e214…＝作った run の `feature_audit.json` の `cache_sha256`）は `frame_ids (15437,) <U9` と `features (15437, 2048) float32` だけ。**空間の軸は無い。**
  作った台本は `scripts/stage1_ptower_20.py action=extract`（→ `stage1_ptower_r3.extract`）。`model.fc = nn.Identity()`（r3 312 行）なので特徴は torchvision ResNet-50 の layer4 の出力の全体平均（avgpool）。
  入力は `EVAL_TRANSFORM`（短辺 800、切り出しなし、ImageNet の平均と分散。r3 47〜53 行）。抽出は efros で 365.9 秒／15,437 フレーム（`feature_audit.json`）。
  キャッシュは test の動画のフレームの特徴を含む（名前だけ数えた。特徴は `common.load_features` と同じく test を除いて使う）
- S4-1: NMS は使わない。`third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery.py` 83〜84 行 `PostProcess(select_box_nums_for_evaluation=300, nms_iou_threshold=-1, confidence_score=-1)`、
  `models/bricks/post_process.py` 28〜33 行（900 query × 15 クラスの sigmoid を平らにして上位 300）、47 行と 51 行（`confidence_score > 0`・`nms_iou_threshold > 0` のときだけ絞る。-1 なので通らない）。query 数は同 config 25 行 `num_queries = 900`
- S6-1: 入力チャネル数を受ける引数は無い。画像は `im.convert("RGB")`（r3 73 行）、正規化は 3 チャネルの平均と分散（48 行）、
  backbone は torchvision `resnet50`（103・106 行）で COCO の `backbone.*` を `strict=False` で読み、欠けを `fc` だけと検査する（107〜109 行）。8 チャネルにするには conv1 の形（64, 3, 7, 7）、正規化、データの読み込み（マスクの連結）の三か所を変える
- S6-3: stem は凍結（r3 115〜116 行 `for module in (model.conv1, model.bn1): module.requires_grad_(False)`、129〜133 行で学習中も eval、185 行で stem の学習パラメータ 0 を assert）。
  `requires_grad` はテンソル単位なので、conv1 の追加チャネルだけを学ぶには、conv1 を学ぶ設定にして RGB の 3 チャネル分の勾配を 0 にする hook を掛けるか、追加チャネル用の別の畳み込みを足して和を取る形になる（S6-2 で前者の形を確かめる）。どちらにするかは決めない
- S6-4: 1 epoch の見込み（記録から）: efros の確定の fine-tune 765.5 秒/epoch（16,076.4 秒 ÷ 21、各 epoch の val を含む、1 GPU、実効 batch 64）、bengio の再実行 506.9 秒/epoch（9,631.3 秒 ÷ 19、2 GPU、手本は `phase_manifest_all_phase` で別のデータの集合）

**G2: pass**（S2・S3・S7 の表が埋まり、対照: test の 04 を混ぜると件数が増え、存在しない 99 で 0 件、1 フレームずらすと対応が崩れる）

## Task C — モデルを動かして（G3）

記録の原本は `$S/c/`。学習は一歩も行っていない（optimizer を作らない。各道具が重みの state_dict の要約値を前後で取る）。

### C-1 S1 工程塔の空間特徴（`$S/c/s1/`、道具 `$A/tools/s1_pmap.py`、GPU 0、2026-11-08 20:5x JST）

    $ cd $S/c && CUDA_VISIBLE_DEVICES=0 .venv/bin/python -I $A/tools/s1_pmap.py --video 09 --out-dir $S/c/s1
    rc 0
    input_chw [3, 800, 1422]、map_chw [2048, 25, 45]、縮小率 32.0・31.6（入力）、43.2・42.67（元の 1080×1920）
    forward 0.01932 s/フレーム（batch 16）、0.02168 s（batch 1、20 回の中央）、読み込みを含む 34.76 s / 518 フレーム
    保存: fp32 4,773,888,128 B（9,216,000 B/フレーム）、fp16 2,386,944,128 B（4,608,000 B/フレーム）
    対照: 空間平均とキャッシュの相対 L2 最大 7.23e-07（1e-3 超 0 件）、fp16 4.24e-05（0 件）、avgpool とキャッシュ 7.28e-07
          1 つずらしたフレームとは最小 0.0912・中央 0.2979（1e-3 以下 0 件）
    weights_unchanged true（ec1eb1cc… → ec1eb1cc…）、read_videos ['09']

- 読み込みはキャッシュを作った `stage1_ptower_r3.extract` と同じ手順（`build_backbone` → `load_state_dict` → `fc = Identity` → `eval`）、決定性は `stage1_ptower.deterministic(42)`。checkpoint の読み込みの既定は変えていない
- 目録は val のものだけを開いた（`base.manifests` は test の目録も開くので使わず、`val.json` の clips を `FoldFrames` に渡した）
- 地図は `$S/c/s1/p_layer4_09_{fp32,fp16}.npy` に置いた（版管理と同期の外）

### C-2 S5 把持塔の中間特徴（`$S/c/s5/`、道具 `$A/tools/s5_gfeat.py`、GPU 0）

    $ cd $S/c/s5 && CUDA_VISIBLE_DEVICES=0 .venv/bin/python -I $A/tools/s5_gfeat.py --out $S/c/s5/s5_record.json
    rc 0、frames 100（val 09・10 の工程の経路から seed 42）、入力 [3, 768, 1344]、weights_unchanged all/all2/H1/H2 すべて true
    backbone_C5          2048 × 24×42   ～0.0134 s     確定 vs H1 の対応する次元の r 中央 0.493（5% 0.174・95% 0.760）、|r|<0.3 317/2048
    pixdec_mask_features  256 × 192×336 ～0.0419 s     中央 0.821（0.631・0.913）、|r|<0.3 0/256
    pixdec_memory_coarse  256 × 24×42   ～0.0419 s     中央 0.682（0.498・0.813）、|r|<0.3 0/256
    decoder_last_query    256 × 100 query ～0.0713 s   中央 0.255（0.128・0.396）、|r|<0.3 183/256
    対照（確定どうし all vs all2）: 4 層とも r の最小 1.000000
    相手の全次元で最大の |r| の中央は対応する次元の r とほぼ同じ（C5 0.494、mask_features 0.822、memory 0.682、query 0.275）

- 候補は mmdet 3.3.0 の `Mask2FormerHead.forward`（402 行 `self.pixel_decoder(x)`、441〜451 行の decoder の各層、`_forward_head` 358・362・364 行の post_norm → mask_embed → mask_features との積）を読んで、マスクの出力より前から選んだ
- `load_model` は `g5_signals.load_model`（infer と同じ）。前処理は `G38(train=False)`・`to_inputs`（infer と同じ）
- backbone C5 の 2 次元は確定の G で分散 0（r を定義できない）。分布から除いた
- **SPEC の期待「対応する次元の相関が低い」は層によって成り立ち方が違う。** decoder の query は低い（中央 0.255）、C5 は中程度（0.49）、pixel decoder の 2 つは高い（0.68・0.82）。次元の並べ替えで一致する形でもない。そのまま記録した

### C-3 S6 工程塔の入力層の変更（`$S/c/s6/`、道具 `$A/tools/s6_inputlayer.py`、GPU 0）

    $ cd $S/c/s6 && CUDA_VISIBLE_DEVICES=0 .venv/bin/python -I $A/tools/s6_inputlayer.py --out $S/c/s6/s6_record.json
    rc 0、init ResNet50_Weights.IMAGENET1K_V1（~/.cache/torch/hub/checkpoints/resnet50-0676ba61.pth、手元の写し。通信なし）
    conv1 [64, 3, 7, 7] → [64, 8, 7, 7]、入力 [2, 8, 800, 1422]
    (a) stem 凍結: loss 2.13244、conv1_grad_is_none true、layer1 に勾配あり、山 3,986,409,984 B
    (b) conv1 を学ぶ設定 + RGB の勾配を 0 にする hook: 勾配 [64, 8, 7, 7]、RGB の |g| の和 0.0、追加 98.799（非零 15,435/15,680）
    対照: 追加チャネル 0 の写しと元の 3 チャネルの出力の差 0.0、7 チャネルの入力は RuntimeError
          "Given groups=1, weight of size [64, 8, 7, 7], expected input[2, 7, 800, 1422] to have 8 channels, but got 7 channels instead"
    optimizer を作っていない。重みと buffer の要約値 86f3666e… → 86f3666e…（時間を測った後も一致）
    参考: 順伝播と逆伝播 1 回（batch 2、eval）3 チャネル 0.0985 s、8 チャネル 0.0994 s

- BN の統計を動かさないよう eval で回した。train（BN の統計の更新）での挙動は確かめていない

### C-4 S4 検出塔の出力の形と較正（`$S/c/s4/`、道具 `$A/tools/s4_det_calib.py`、GPU 1、`.venv-relation-detr`）

    $ cd $S/c/s4 && source .venv-relation-detr/bin/activate && CUDA_VISIBLE_DEVICES=1 python $A/tools/s4_det_calib.py --part val --out-dir $S/c/s4
    [s4] part=val frames=1515 videos=['09', '10'] ms_deform_attn_ext=True select=300 nms=-1 conf=-1
    val rc=0
    $ CUDA_VISIBLE_DEVICES=1 python $A/tools/s4_det_calib.py --part train --sample 1000 --seed 42 --out-dir $S/c/s4
    train rc=0
    class head の出力 [1, 900, 15]、各フレームの出力 300 本・枠 [300, 4]（val・train とも全フレーム）
    val: ECE（全出力 454,500 件）0.018489、得点 ≥ 0.05（26,830 件）0.077351、対応 4,628/正解 4,707、各フレームの最大の得点 中央 0.948
    train: ECE 0.018268、得点 ≥ 0.05（15,671 件）0.081969、対応 3,306/3,315、中央 0.954
    対照: 得点を 1 にした写し ECE 0.9898（val）・0.9890（train）、得点を対応の 0/1 にした写し 0.0・0.0
    経路の同一性: val の出力の COCO mAP 0.7273450248398429 = 記録 DET_RECORD 0.7273450248398429（差 0）
    順伝播 1 フレーム（batch 1、fp32）中央 0.0830 s（val）・0.0835 s（train）
    weights_unchanged true（fbd40112… → fbd40112…）

- 学習エンジン（`util.engine`）は使わない。作業ディレクトリは `$S/c/s4`、`RELDETR_EVIDENCE_DIR=$S/c/s4/evidence`（何も書かれず、フォルダも作られなかった）
- 読み方は `extract_det_signals.py` と同じ（`Config(MODEL_CFG).model` → `load_checkpoint` → `load_state_dict`、画像は `ImageReadMode.RGB`）。本体の `third_party/Relation-DETR` はソースが重ねの BODY（andrew と一致）と同じ（`diff -rq` で違いは本体だけにある `data`・`third_party` の 2 件）なので本体を読んだ
- train の 1,000 フレームは `instances_train.json` の画像を id 順に並べ、`np.random.default_rng(42).choice(9657, 1000, replace=False)`

**G3: pass**（S1・S4・S5・S6 を実測。学習は 0 歩。各道具の重みの要約値が前後で一致）

## Task D — 表・検証・報告

### D-1 終了時の検査（`$S/final/`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 980 passed, 5 skipped, 26 warnings in 47.19s（失敗の名前は開始時と diff 0 行）
    $ make forbidden-check TASK=T-2026-11-08-grasp-cards-survey
    status pass、changed 12、violations []、permitted 9（experiments/analysis/grasp_cards_survey/ の REPORT.md と tools/ の 8 件）
    $ .venv/bin/python tools/check_forbidden.py     （陽性対照: 契約の許可を読まない）
    status fail、violations 9（本契約の同じ 9 件）
    $ .venv/bin/python -I $A/tools/digests.py --out $S/final/digests_end.json   → $S/final/digests_compare.txt
    27 項目のうち 25 同じ、2 違う（scripts と tasks）

| 違った根 | 開始 → 終了 | 原因（特定した方法） |
|---|---|---|
| tasks（本契約のフォルダを除く） | 1,870 件・114,310,380 B → 1,871 件・114,311,651 B | `tasks/inbox.d/T-2026-11-08-grasp-cards-survey.md`（1,271 B、差とちょうど一致）。契約が求める書き込み |
| scripts | 412 件・3,947,286 B → 413 件・4,006,635 B | `scripts/grasppilot/__pycache__/g5_signals.cpython-311.pyc`（59,349 B、差とちょうど一致、11-08 20:23 JST）。S5 で `g5_signals` を import したときに Python が書いたバイトコードのキャッシュ（`find scripts -newer <開始の記録>` で 1 件だけ）。git の無視の対象。台本の .py は変わっていない |

- third_party・重ねの BODY・configs・data の 5 根・前の run の置き場と保存先・使った重み 6 件・二つの仮想環境は前後で一致

### D-2 .pyc の扱い（利用者の決定「1 消して測り直す」、2026-11-08）

- 停止して諮った（契約の escalate_if「測定の副作用が禁止の場所に書く場合」）。利用者の選択で消した

      $ sha256sum scripts/grasppilot/__pycache__/g5_signals.cpython-311.pyc   → $S/final/removed_pyc_sha256.txt
      92028ea8d6f5e6d6c8ea60e7a8dc331a9a8a66c352ff568a475ab4f44cd3fc8f
      $ rm -f -- scripts/grasppilot/__pycache__/g5_signals.cpython-311.pyc
      $ PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -c '…digests.walk/summary で scripts と tasks を測り直す…'   → $S/final/digests_recheck.{json,txt}
      scripts 412 件・3,947,286 B・5e56a3dda26a327c… = 開始時（一致）
      tasks   1,871 件・114,311,651 B（差は inbox.d の 1 件だけ。上の表）

- 測り直しはバイトコードを書かない設定（`PYTHONDONTWRITEBYTECODE=1`・`sys.dont_write_bytecode`）で走らせた。道具の置き場にも `__pycache__` は無い
- 原因: S5 の道具が `scripts/grasppilot/g5_signals.py` を import した（それまで bytecode が無かった）。他の import した台本は既存の .pyc が新しく、書き直されなかった

### D-3 test 不使用の対照（`$S/final/i_control.txt`）

    $ PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -c '… common.assert_no_test(['09_1_0213','10_1_0001']) / (['09_1_0213','04_1_0001']) …'
    ok ['09', '10']
    raised [ctl] test の動画が混入: ['04']

- 読んだ動画の集合（各道具の `read_videos`）: S1 {09}、S4 val {09,10}、S4 train {01,02,03,06,08,11,12,13,14,15}、S5 {09,10}、S6 {09}、S2・S3 は画像 0 枚。和集合と {04,05,07} の共通 0 件
- この対照は bytecode を書かない設定で走らせ、`scripts/` に新しいファイルが無いことを `find -newer` で確かめた

## 送出

    $ git push -u origin feat/grasp-cards-survey      （93834768）
    $ gh pr create --base phase0 --head feat/grasp-cards-survey …   → https://github.com/takuya3h/m2/pull/302
    $ gh pr view 302 --json number,isDraft,baseRefName,headRefName,state
    {"baseRefName":"phase0","headRefName":"feat/grasp-cards-survey","isDraft":false,"number":302,"state":"OPEN"}
    $ source scripts/load_env.sh && make task-report TASK=T-2026-11-08-grasp-cards-survey
    {"task_id": "T-2026-11-08-grasp-cards-survey", "verdict": "pass", "n_issuer_defects": 4, "report_sha256": "5a74125d545b067d23a165f27d6859ff15ac989f67889f7e0a1d803e51aecf70", "report_bytes": 9998, "replaced_blocks": 0}
    終了コード 0
