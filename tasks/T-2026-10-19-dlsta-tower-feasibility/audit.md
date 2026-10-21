# audit — T-2026-10-19-dlsta-tower-feasibility

実行ホスト dlsta（repo `~/local/m2`）。時刻は UTC（括弧で JST）。命令は要旨、出力は要点を原文のまま写す。
大きな出力（ログ、checkpoint、特徴）は repo の外 `~/m2-scratch/dlsta_tower_feasibility/`（以下 `$S`）に置いた。

## 0. 始める（task スキル）

- 2026-10-21 06:0x UTC（15:0x JST）。`git branch --show-current` → `feat/dlsta-tower-feasibility`。
  `status --porcelain` は未追跡 2 行（本契約の `SPEC.md` と `spec.yaml`）だけ。遠隔の分岐は無し。
  `tasks/T-2026-10-19-dlsta-tower-feasibility/` は在る → 手順の判定 1「再開」。
- `.sync-pause` は**無かった**（`cat .sync-pause` は空出力）。手順 5 の例外に従い、所有の記録つきで置いた:
  `task_id=T-2026-10-19-dlsta-tower-feasibility` / `branch=feat/dlsta-tower-feasibility`。
  稼働中の `~/bin/m2-sync.sh` の `grep -c sync-pause` → `2`（対応済み）。
- `make task-validate` → `OK`、`WARN [L2-6] conventions.md が 7ba1d60d… 以降に変更されています`。
  差分は `e1364772` と `5c0eaeeb` の 2 commit で、`proposal_gate` 節の生成会話の行と依頼文の小節、履歴表 1 行。
  注入する `prohibitions` `issuer_cautions` `env_p0` の本文は変わらない。利用者に示し「続行」の回答を得た。
- `make task-preflight` → `6 PASS / 0 WARN / 8 SKIP / 0 FAIL`。SKIP は P2 P3 P4 P5 P11 P12 P13 P14（宣言なし、または kind=analysis で対象外）。

## A. 開始状態

### A.1 分岐と起点

    git merge-base HEAD origin/phase0 → 3cb3db070eb0735b974933223e1fb8eb4dfb262b
    git rev-parse origin/phase0 HEAD → 3cb3db07… / 3cb3db07…（同一）

分岐は `feat/` で始まる。起点は `origin/phase0` の先頭そのもの。

### A.2 未追跡の退避

開始前の未追跡は本契約の `SPEC.md` と `spec.yaml` の 2 件だけで、これは契約そのものなので退避しない。退避 0 件。

### A.3 抑止の目印

開始前は無かった（§0）。前の契約（2026-10-05）とは違い、開始前から在る目印ではない。

### A.4 ホストの確認（OS のホスト名は使わない）

    pwd; realpath ~/local/m2 → /home/ubuntu/local/m2
    nvidia-smi --query-gpu=index,name,memory.total,... → 5 枚とも NVIDIA RTX A5000、24564 MiB

容器の中である（`/.dockerenv` が在り、`/proc/1/cgroup` が `/docker/b7381818…`）。

### A.5 GPU の型・容量・使用中のプロセスと所有者・NVLink

`experiments/analysis/dlsta_tower_feasibility/gpu_procs.py`（`nvidia-smi --query-compute-apps` の PID を
`/proc/PID` の uid と `/proc/PID/exe` の解決で所有者に引く。見えない PID は UNKNOWN と出す）。

2026-10-21 06:06 UTC（試験を回す前）:

| GPU | 型 | 容量 MiB | 使用 MiB | compute プロセス | bus |
|---|---|---|---|---|---|
| 0 | RTX A5000 | 24564 | 99 | なし（`Processes: None`） | 18:00.0 |
| 1 | RTX A5000 | 24564 | 22 | なし | 3B:00.0 |
| 2 | RTX A5000 | 24564 | 22 | なし | 5E:00.0 |
| 3 | RTX A5000 | 24564 | 22 | なし | 86:00.0 |
| 4 | RTX A5000 | 24564 | 22 | なし | D8:00.0 |

GPU0 は使用率 0%（14 秒の標本 71 個で最大 0%）だが、ほかの 4 枚より 77 MiB 多く確保されている。

    nvidia-smi topo -m
            GPU0  GPU1  GPU2  GPU3  GPU4  CPU Affinity  NUMA
    GPU0     X    NODE  NODE  SYS   SYS   0-23,48-71    0
    GPU1    NODE   X    NV4   SYS   SYS   0-23,48-71    0
    GPU2    NODE  NV4    X    SYS   SYS   0-23,48-71    0
    GPU3    SYS   SYS   SYS    X    NV4   24-47,72-95   1
    GPU4    SYS   SYS   SYS   NV4    X    24-47,72-95   1
    nvidia-smi nvlink -s → GPU0: all links are inActive / GPU1–4: Link 0–3 各 14.062 GB/s

NVLink の組は GPU1–GPU2 と GPU3–GPU4（NV4）。GPU0 は単独。

**数え方の対照**（06:1x UTC）: GPU2 に自分で python を一件起こした（`torch.ones(1, device="cuda")` を保持して 25 秒待つ）。

    GPU2 ... used=270MiB compute_procs=1
      pid=2164092 used=240MiB owner=ubuntu exe=/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11
    control pid=2164092 alive=1
    nonexistent pid 999999 alive=0
    nvidia-smi の PID 一覧での完全一致: 自分の PID → 1、999999 → 0
    終了後: GPU2 compute_procs=0、used=22MiB

（同時刻の GPU1 の 1 件は本契約の試験の pytest、所有者 ubuntu。）
容器の中でも自分のプロセスは `nvidia-smi` に見える。したがって **GPU0 の 77 MiB は本容器の PID 名前空間の外の
確保**であり、所有者は特定できない。前の契約（2026-10-05）では GPU0 に他の利用者の処理（4397 MiB、100%）が載っていた。
**GPU0 は他の利用者の確保が在るものとして以後使わない。使うのは GPU1〜4（4 枚）。** → 関門 G1 の「二枚以上」を満たす。

### A.6 版と空き容量

    torch 2.1.2+cu118 / torch.version.cuda 11.8 / cuDNN 8700（.venv）
    nvcc: Cuda compilation tools, release 12.9, V12.9.86
    driver 595.84（nvidia-smi の「CUDA Version 13.2」は driver の API の版で、nvcc とは別）
    gcc 13.3.0
    df -B1 /home/ubuntu/local/m2 → /dev/sdb1 11998000558080 / used 9468260528128 / avail 2529740029952 (79%)
    df -B1 ~/m2-scratch           → overlay 965895782400 / used 194463637504 / avail 771432144896 (21%)

### A.7 外への到達（状態を変えない方法）

    git ls-remote https://github.com/xiuqhou/Relation-DETR.git HEAD → b485955c72452788240600da6d0f0b8cc49f33c7  HEAD（rc=0）
    curl -I https://pypi.org/simple/                 → 200 (0.057 s)
    curl -I https://download.pytorch.org/whl/cu118/  → 200 (0.634 s)
    curl -I https://files.pythonhosted.org/          → 404 (0.059 s。根は 404 を返す。名前解決と TLS は通った)

上流の HEAD は写しの記録する base commit と同じ。

### A.8 既知のホストの記録

    sha256sum ~/.ssh/known_hosts → dfe8b109831f503c0ed78f0f6cc4ef901336aa6097e70005732f19ff8426ea6e（21 行、6846 bytes）

実行基盤は読み取りを拒まなかった。値（ホストの鍵）は出力していない。

### A.9 data の一覧の要約値（前）

`find -L <dir> -printf '%P\t%s\n' | LC_ALL=C sort | sha256sum`（経路と大きさ。一覧は `$S/listing_before_*.tsv`）

| 経路 | 要約値 | ファイル数 | 合計 bytes |
|---|---|---|---|
| data/raw | db3efcf3a0e10717200039f0a544f657257c27c05b81f891d082640717518ef0 | 235716 | 10517239245 |
| data/external | 33d245518e01a5acda33a31eb4ce0b7a7a14ff4f31359d92885b3857e62bd81a | 38 | 9692981482 |

### A.11 規約の版と runindex

    git log -1 --format=%H -- context/conventions.md → 5c0eaeeb4551c66c9b854faaa7a5376dcf755ac7（起票時 7ba1d60d）
    git log -1 --format=%H -- runindex/              → 63ae65da8c7d32df591f5e2ee4358286b72c726b（起票時と同じ）
    行数 index 1961 / experiments 750 / verdicts 1506（起票時と同じ）

`contract.conventions_rev` を `5c0eaeeb…` に差し替え、`meta.amendments` に 1 件記録した。差し替え後の `make task-validate` → `OK`（WARN なし）。

### 同期処理（Task G.2 を先に見た。大きな出力の置き場を決めるため）

    ps → /home/ubuntu/bin/syncthing serve --no-browser（2 件）、/bin/bash /home/ubuntu/bin/keeper.sh
    ~/.local/state/syncthing/config.xml の folder の path（id と label は伏せた）:
      /home/ubuntu/.claude, /home/ubuntu/.codex, /home/ubuntu/.agents, /home/ubuntu/claude-sync,
      /home/ubuntu/local/m2, （path が空の 1 件）
    device 要素 14 件

dlsta では Syncthing が `~/local/m2` を同期している（`.stignore` の規則で gitignore された実験の成果物を配る）。
大きな出力は repo の外（`~/m2-scratch/`、overlay）に置く。

### A.10 試験（前）

    CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src pytest tests/ -q -p no:cacheprovider           （06:10:06–06:10:15 UTC）
      → ERROR tests/test_stage1_dtower_convergence.py - FileNotFoundError: ... third_party/Relation-DETR/util/convergence.py
        Interrupted: 1 error during collection（収集の段で全体が止まる）
    同 + --continue-on-collection-errors                                                  （06:10:24–06:11:43 UTC）
      → 6 failed, 879 passed, 22 warnings, 1 error in 74.79s

失敗と収集エラーの名前の集合（`$S/fail_before_full.txt`）:

    ERROR  tests/test_stage1_dtower_convergence.py
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

### 関門 G1 → pass

分岐 `feat/dlsta-tower-feasibility`、起点 `origin/phase0`（3cb3db07）、repo の位置 `/home/ubuntu/local/m2` と RTX A5000 × 5（24564 MiB）で dlsta。
他の利用者の確保が無い GPU は GPU1〜4 の 4 枚（GPU0 は容器の外の確保 77 MiB のため除外）。

## B. 入力の実在（読むだけ）

    python experiments/analysis/dlsta_tower_feasibility/inputs_inventory.py --out .../inputs_inventory.json --control
    （06:13–06:15 UTC、1 分 35 秒）→ 全 28 項目 OK、all_match True。項目ごとの値は `inputs_inventory.json`

| 項目 | 在否 | 件数（実測） | 期待 | 要約値・大きさ |
|---|---|---|---|---|
| B1 画像 01–15（`data/raw/ego/{train,val,test}`） | 在 | 15,437 | 15,437 | 45ee4cc2…（1,204,884,895 bytes）。動画ごとの内容の要約値が andrew の記録（frame_signal_audit `decode.sha256_per_video`）と **15/15 一致** |
| B2 工程注釈だけのフレーム（`OpenSurgery_Dataset/01_frames/initial_videos/<区間>/`） | 在 | 1,796 | 1,796 | 47773864…（134,760,136 bytes）。工程 CSV 01–15 の行 17,233 − 画像 15,437 |
| B3a 工程 CSV（01–15 の行） | 在 | 17,233 | 17,233 | CSV 43 件 |
| B3b 工程塔の manifest（`data/processed/phase_manifest/`） | 在 | 15,437 フレーム | 15,437 | train f8bee9f9… / val 9f935375… / test f2077541… / vocab ad3c1e4a…。image_path の欠け 0 |
| B3c 術具注釈 公式 train / val / test | 在 | 9,657/32,272、1,515/4,707、4,265/12,673 | 同（data/README の折り A） | file_name の画像の欠け 0 |
| B4 折りごとの術具注釈 A〜E × 3 分割 | 在（作っていない） | 15 件すべて表と一致 | `data/README.md` の表 | file_name の画像の欠け 0 |
| B5a COCO の初期化の重み | 在 | 196,140,106 bytes | 196,140,106 | — |
| B5b 同 backbone の要約値（`stage1_ptower_r3.backbone_digest`） | — | a755b3eb22a3…fc98f | 三周目 005 の config.yaml の `backbone_init_sha256` | 一致 |
| B6a 検出塔二周目 D\*-COCO 折り A seed 42 `best_ap.pth` | 在 | sha256 30d199b1… | test_access_ledger の `checkpoint_sha256` | 一致。195,421,066 bytes |
| B6a 同 折り B seed 42（対照用） | 在 | be84c64b… | 同 | 一致 |
| B6b 工程塔三周目 `005_ft_coco_lr0.0001_foldA_seed42` `best.pth` | 在 | a90cf04d… | `finetune_history.json` の `checkpoint_sha256` | 一致。94,405,478 bytes |
| B6b 同 `008_ft_coco_lr0.0001_foldB_seed42`（対照用） | 在 | 835d5568… | 同 | 一致 |

B.6 の選択の理由: 工程塔は **005**（COCO 初期化・lr 1e-4・折り A・seed 42）。検出塔の比較対象（D\*-COCO 折り A seed 42）と
折りと seed が同じで、`finetune_history.json` と `metrics.json` が揃い、checkpoint の要約値を記録と照合できる。
同じ折り A の 003（seed 123）は `metrics.json` が空 `{}` で記録の値と並べられないため選ばない。
対照（Task F.4）には折り B の 008 と D\*-COCO 折り B を使う。

対照: 画像の期待を 15,438 に変えた比較 → `match: False`。存在しない経路 `data/raw/ego_does_not_exist` の件数 → 0。

### 関門 G2 → pass

欠けなし。利用者へ諮る項目は無い。

## C. 検出塔の構築

### C.1 現状（復元の前）

    find third_party/Relation-DETR -name '*.py' | wc -l → 0
    find third_party/Relation-DETR -type f | wc -l     → 25（入れ子 third_party/Relation-DETR/data/processed/t1b_backbone_cache/_bench_w1m/*.bin）
    du -sb → 2235383808
    一覧（%P\t%s）の sha256 → 71451742440a50782367eecdb26a4618dd75636997a44ef763de28dcff6c06fd

ソースは一件も無い（在るのはキャッシュだけ）ので停止条件に当たらない。`third_party/` は `.gitignore:134` で無視される。

### C.2 復元（06:15:51–06:15:52 UTC）

    bash scripts/restore_relation_detr_source.sh efros/2026-10-17
    [restore-reldetr] 上流 b485955c72452788240600da6d0f0b8cc49f33c7 を取得（snapshot: efros/2026-10-17）
    [restore-reldetr] 完了: third_party/Relation-DETR
      上流 commit: b485955c72452788240600da6d0f0b8cc49f33c7
      上流への改変: 4 件 / .py: 140 件
    rc=0

取り寄せは上流（github）と repo の写しだけ。ほかのホストからは取り寄せていない。

### C.3 要約値の照合

    cd third_party/Relation-DETR && sha256sum -c ../../third_party_snapshot/efros/2026-10-17/Relation-DETR/sha256sums.txt
    → 39 行すべて ": OK"、rc=0（`$S/c3_sha256_check.txt`）

対照: 写しの 1 行目の先頭 1 文字を変えた `sha256sums_altered.txt`（repo の外）で照合 →
`configs/relation_detr/relation_detr_resnet50_egosurgery.py: FAILED` / `WARNING: 1 computed checksum did NOT match`。

### C.4 環境と拡張（06:16:09–06:19:44 UTC）

    CUDA_VISIBLE_DEVICES=1 bash scripts/setup_env_relation_detr.sh   （GPU0 を避けるため装置だけ指定。道具は変えていない）
    [setup-reldetr] nvcc(/usr/local/cuda): 12.9 / driver: 595.84
    ... 全 72 パッケージを厳密固定（fvcore, iopath, stringzilla を build）
      torch 2.1.2+cu118 / CUDA 11.8 / GPU NVIDIA RTX A5000
      torchvision 0.16.2+cu118 / accelerate 1.14.0
      import OK・CUDA 動作 OK
    [setup-reldetr] === 5. MS-Deform-Attn の JIT ビルド（nvcc 12.9）===
      MS-Deform-Attn ビルド OK・ロード OK
    rc=0

取り寄せは pypi.org と download.pytorch.org（公開の package index）だけ。

### C.5 収束規則の試験

    PYTHONPATH=src CUDA_VISIBLE_DEVICES=1 pytest tests/test_stage1_dtower_convergence.py -v
    → 9 passed in 0.03s（andrew の記録 9/9 と同じ）

A.10 では同じファイルが収集の段で `FileNotFoundError: .../third_party/Relation-DETR/util/convergence.py` で止まっていた。

### 関門 G3 → pass

要約値 39/39 一致、拡張の読み込み OK、収束規則の試験 9/9。

## D. 検出塔の記憶領域と処理量

道具（本契約の出力先 `tools/`。既存のスクリプトは変えていない）:

- `dtower_probe.sh <名前> <GPU> <port> <設定> <歩数> [環境変数]` — 二周目の `command.sh` と同じ `main.py` の引数で起動し、
  学習の記録が `[<歩数>/` に届いたら process group ごと止める。出力はすべて `$S/D/<名前>/`（repo の外）。
  nvidia-smi を 0.5 秒ごとに採る（`nvsmi.csv`）。起動の前後で `gpu_procs.py` を記録する（`probe.txt`）。
- `memprobe_main.py` — `main.py` を同じ引数のまま `runpy.run_path("main.py", run_name="__main__")` で動かし、
  各 rank の `torch.cuda.max_memory_allocated` / `max_memory_reserved` を bytes で 2 秒ごとに書く（学習の記録の `max mem` は MiB に丸められるため）。
- `summarize_dprobe.py` — rank 0 の `training.log` から 50 歩ごとの `iter_time`（直近 20 歩の窓平均）を取り、100 歩目以降の平均を定常の一歩とする。
  **定常の判定**: 最後の 3 つの窓平均がその平均の ±5% に入ること。回す長さは 600 歩（50 歩ごとの記録 12 点）とした。

### D.2 起動の引数の突き合わせ

    二周目（experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/command.sh）:
      accelerate launch --num_processes 2 --main_process_port 29711 main.py \
          --config-file configs/train_config_egosurgery_seed42.py --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36
    本契約 D1（probe.txt の command 行）:
      accelerate launch --num_processes 2 --main_process_port 29811 .../tools/memprobe_main.py \
          --config-file configs/train_config_egosurgery_seed42.py --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36

`main.py` への引数は port を除いて同一。違いは入口（`memprobe_main.py` が `main.py` をそのまま呼ぶ）と環境変数:
`EGO_ANN_DIR`（dlsta の位置の折り A）、`RELDETR_OUTPUT_DIR`（repo の外）、`CUDA_VISIBLE_DEVICES`、および二周目の `command.sh` に無い
`EGO_ROOT=~/local/m2/data/raw/ego` と `RELDETR_COCO_CKPT=~/local/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth`。
**設定の既定値はこの 2 つを andrew の位置 `/home/ubuntu/slocal2/m2/...` に置いている**（`configs/train_config_egosurgery_seed42.py` の
`EGO_ROOT` と `resume_from_checkpoint`）。dlsta に `~/slocal2` は無い。`main.py` は `resume_from_checkpoint` がファイルでないと
**読み込まずに先へ進む**（`if weight_path is not None and os.path.isfile(weight_path)`）ため、既存の `scripts/run_stage1_dtower.sh` を
dlsta でそのまま使うと COCO の重みを読まない学習になりうる。本契約は環境変数で与え、記録に
`[RANK 0] load pretrained from /home/ubuntu/local/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth` が出たことを確かめた。
画像の内容（B1）と COCO の重みの sha256 `2d2c19a7…`（二周目 r3 と前提契約の記録と一致）は andrew と同じ。1 epoch の歩数 2405 は二周目の記録と同じ。

### D.1 / D.3 / D.4 NVLink の組（GPU1–2）、処方そのまま（06:22–06:28 UTC）

    dtower_probe.sh d1_nv12_b2 1,2 29811 configs/train_config_egosurgery_seed42.py 600
    status=reached（600 歩）wall 394 s。終了後 GPU1〜4 の compute プロセス 0

| 量 | rank0（GPU1） | rank1（GPU2） |
|---|---|---|
| torch max_memory_allocated | 12,285,587,968 bytes | 11,599,943,168 bytes |
| torch max_memory_reserved | 12,633,243,648 bytes | 12,194,938,880 bytes |
| nvidia-smi memory.used の最大 | 12,563 MiB | 12,145 MiB |

窓平均の iter_time（0, 50, …, 600 歩）: 1.971, 0.6179, 0.5817, 0.609, 0.5837, 0.5998, 0.6173, 0.5904, 0.5941, 0.6079, 0.6198, 0.583, 0.5966 秒。
100 歩目以降の平均 **0.59848 s/歩**、最後の 3 点 0.6198 / 0.583 / 0.5966 は ±5% に入る（定常）。

**通信の設定**: `NCCL_P2P_DISABLE` を付けずに起動でき、600 歩まで止まらずに進んだ。dlsta では要らない（andrew では要った）。

### D.5 GPU ごとの batch の上限（処方の変更。選定には使わない）

batch だけを変えた設定の写しを repo の外に置いた（`$S/configs/train_config_egosurgery_seed42_bs{3,4,6,8}.py`。
`diff` は 15 行目 `batch_size = 2` → `batch_size = N` の 1 行だけ）。記憶領域だけを測るので batch 4 と 3 は同時に回した。

| 名前 | GPU | batch/GPU | 結果 | torch allocated 最大 rank0 / rank1 (bytes) | nvidia-smi 最大 (MiB) |
|---|---|---|---|---|---|
| d5_nv34_b3 | 3,4 | 3 | 300 歩まで収まる（1 epoch 1603 歩） | 17,886,560,256 / 17,149,070,848 | 18,667 / 18,403 |
| d5_nv12_b4 | 1,2 | 4 | **50 歩に届く前に OOM**（1 epoch 1202 歩） | 21,258,942,976 / 20,272,091,136 | 23,235 / 21,681 |

batch 4 の OOM: `torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 1.15 GiB. GPU 0 has a total capacty of 23.55 GiB of which
880.19 MiB is free. ... 19.64 GiB is allocated by PyTorch, and 2.55 GiB is reserved by PyTorch but unallocated.`（位置情報の埋め込み `pos_res`）。
batch 3 の窓平均（参考。batch 4 の起動と重なった区間がある）: 1.4976, 0.7528, 0.7539, 0.7136, 0.7779, 0.7186, 0.7598 秒。
**注意**: 学習の増強は画像ごとに大きさを変えるので、300 歩で出会わなかった大きな組み合わせで batch 3 が溢れる可能性は残る（全 epoch は回していない）。

## G. 受け渡しの経路（GPU を使わない）

### G.1 TCP の接続だけ（06:29:20 UTC）

住所は `scripts/sync/hosts/ssh_config.d.snapshot.conf`（andrew `192.168.196.190`、philip `192.168.196.150`、port 50072）。
python の `socket.connect_ex` だけを使い、認証も鍵の交換もしない（ssh を起動しないので既知のホストの記録に書く経路が無い）。

    andrew 192.168.196.190:50072 connect_ex=0 (connected) 0.898s banner=b'SSH-2.0-OpenSSH_9.6p'
    philip 192.168.196.150:50072 connect_ex=0 (connected) 0.001s banner=b'SSH-2.0-OpenSSH_9.6p'
    andrew-closed-port 192.168.196.190:1 connect_ex=111 (Connection refused) 0.000s
    philip-closed-port 192.168.196.150:1 connect_ex=111 (Connection refused) 0.000s
    sha256sum ~/.ssh/known_hosts 前 dfe8b109…ea6e / 後 dfe8b109…ea6e（A.8 と同じ）

### G.2 同期の処理

- プロセス: `syncthing serve --no-browser`（2 件）、`/bin/bash /home/ubuntu/bin/keeper.sh`、
  `ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i <key> ... ubuntu@192.168.196.150`（philip の Syncthing の port への常駐の中継）
- 目印: `~/.tunnel_to_philip` が在る（中身は読んでいない）
- Syncthing の folder（A 節の末尾）: `~/local/m2` を含む 6 件
- `~/claude-sync/sync-alerts.log`: `2026-10-21 06:17:32 [dlsta] 一時停止中: /home/ubuntu/local/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）`
  → 本契約の目印が効いている。

## E.5 工程塔を複数の GPU で回す対応（実装を読むだけ。変えていない）

対象ファイルの sha256（行番号はこの版のもの）:

    3ee4325d997eb82ef3689273b643a9e47e6683f77572b35c6a94a1f0a9216202  scripts/stage1_ptower_r3.py
    4ec5b57451f46d66473913361203e65ae1460222fd57860bd126e0d0ef2aeb5e  scripts/stage1_ptower.py
    b3480ca19defbdf4351a1fed91a36e898342e064bc1b721bd03fc76b01514b71  configs/stage1_ptower_r3.yaml

    grep -n -E "DistributedDataParallel|DataParallel|SyncBatchNorm|torch\.distributed|init_process_group|accelerate|LOCAL_RANK|world_size|DistributedSampler" \
        scripts/stage1_ptower_r3.py scripts/stage1_ptower.py → 該当なし（rc=1）

引いた行（`sed -n <行>p` の出力そのまま）:

    configs/stage1_ptower_r3.yaml:36  device: cuda:0
    configs/stage1_ptower_r3.yaml:14  ft_batch_size: 16
    configs/stage1_ptower_r3.yaml:15  ft_accum_steps: 4
    scripts/stage1_ptower_r3.py:117      return model.to(device), source, digest
    scripts/stage1_ptower_r3.py:197          "train": DataLoader(train_set, batch_size=cfg.ft_batch_size, shuffle=True,
    scripts/stage1_ptower_r3.py:216              images = images.to(cfg.device, non_blocking=True)
    scripts/stage1_ptower_r3.py:218              loss = ce(model(images), y)
    scripts/stage1_ptower_r3.py:221              (loss / accum).backward()
    scripts/stage1_ptower_r3.py:222              if step % accum == 0 or step == steps:
    scripts/stage1_ptower_r3.py:223                  optimizer.step()
    scripts/stage1_ptower_r3.py:115      for module in (model.conv1, model.bn1):
    scripts/stage1_ptower_r3.py:116          module.requires_grad_(False)
    scripts/stage1_ptower_r3.py:129  def stem_eval(model):
    scripts/stage1_ptower_r3.py:131      model.train()
    scripts/stage1_ptower_r3.py:132      model.conv1.eval()
    scripts/stage1_ptower_r3.py:133      model.bn1.eval()
    scripts/stage1_ptower_r3.py:211          stem_eval(model)

読み:

- **複数の GPU に対応していない。** 装置は設定の 1 つ（`device: cuda:0`）で、模型は `model.to(device)`（117 行）で 1 枚に載る。
  分散の初期化、DDP、DataParallel、SyncBatchNorm、DistributedSampler はどちらのファイルにも無い。
- **正規化層**: torchvision の ResNet-50 の BatchNorm2d は 53 層（実測: `sum(isinstance(m, nn.BatchNorm2d))` = 53）。
  stem の `bn1` だけが `eval`（132–133 行）で、残り 52 層（layer1〜4）は `model.train()`（131 行）で**物理 batch 16 枚の統計で正規化し、
  running の統計を micro-step ごとに更新する**。勾配の累積（221–224 行）は BN の統計の枚数を変えない（BN は 16 枚ずつ見る）。
  よって「物理 batch 16 の統計」が処方の一部である（SPEC §3.1 と一致）。

## 利用者の指示（2026-10-21 06:3x–06:4x UTC、会話）

- 「空いてるVRAM、GPUなどの計算資源はすべて使って最速で終わらせて」→ 以後、時間を測らない測定を並べて回した。
  時間の値には同時に何が動いていたかを併記する。
- 「GPU0もつかってよい」→ 以後 GPU0 も使う（A.5 の除外を利用者の許可で解いた）。使う直前に `gpu_procs.py` で compute プロセス 0 を確かめた。
- 「10分ごとにモニタリングして」→ セッション内の定期実行（毎時 3,13,23,33,43,53 分）で GPU と測定の状態を点検する。

### D.6 NVLink の無い組（GPU1+GPU3、SYS = NUMA をまたぐ）（06:39–06:45 UTC）

    dtower_probe.sh d6_sys13_b2 1,3 29831 configs/train_config_egosurgery_seed42.py 600 → status=reached wall 399 s
    窓平均: 1.2508, 0.6498, 0.5896, 0.6019, 0.5854, 0.6075, 0.6295, 0.5991, 0.6357, 0.6054, 0.6185, 0.5966, 0.6009
    100 歩目以降の平均 0.60637 s/歩（定常）。torch allocated 12,287,053,824 / 11,600,070,144 bytes、nvidia-smi 12,453 / 12,073 MiB

同時に動いていたもの: 06:40:51 以降 GPU2 で工程塔の特徴の取り出し、GPU4 で工程塔の一歩の測定、06:41:56–06:43:44 GPU0 で工程塔の評価。
（GPU0 の利用の許可はこの測定の起動の後に得た。GPU0 を含む組は D.6b で別に測る。）

### D.5 追加: batch 4 + `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`（GPU3,4、06:33–06:38 UTC）

    status=reached（300 歩）。torch allocated 23,831,509,504 / 24,307,600,896 bytes、reserved 24,138,219,520 / 24,641,536,000、nvidia-smi 23,533 / 24,013 MiB
    窓平均: 1.7735, 0.9922, 0.9591, 0.9687, 0.921, 0.98, 0.9862

記憶の確保の設定を足すと 300 歩は通ったが、最大確保は装置の容量（25,285,623,808 bytes）の 96% に達した。

## E. 工程塔の記憶領域と処理量（`tools/ptower_probe.py`。`stage1_ptower_r3` の関数をそのまま呼ぶ。出力は `$S/E/`）

### E.1 処方そのまま（batch 16、累積 4、COCO 初期化、800×1422）、GPU3、06:19 UTC

    {"oom": true, "oom_step": 1, "oom_phase": "forward", "oom_message": "CUDA out of memory. Tried to allocate 280.00 MiB. GPU 0 has a total capacty of 23.55 GiB
     of which 174.25 MiB is free. ... Of the allocated memory 22.70 GiB is allocated by PyTorch, and 384.10 MiB is reserved by PyTorch but unallocated. ...",
     "input_shape": [16, 3, 800, 1422], "backbone_init_sha256": "a755b3eb…", "train_frames": 9657, "micro_steps_per_epoch": 604,
     "max_memory_allocated_bytes": 24377192960, "max_memory_reserved_bytes": 24779948032, "device_total_bytes": 25285623808}

**収まらない。** 最初の micro-step の forward で止まる。

### E.2 一枚に収まる最大の物理 batch（処方の変更。記録だけ）

記憶領域（12 micro-step = optimizer の step 3 回を含む。GPU3、06:19–06:23 UTC）:

| batch | 結果 | max_memory_allocated (bytes) | max_memory_reserved (bytes) |
|---|---|---|---|
| 8 | 収まる | 14,775,793,152 | 16,221,470,720 |
| 9 | 収まる | 16,540,636,672 | 18,425,577,472 |
| 10 | 収まる | 18,339,510,272 | 21,166,555,136 |
| 11 | 収まる | 20,124,769,792 | 22,980,591,616 |
| 12 | 収まる | 21,905,244,672 | 23,999,807,488 |
| 13 | **収まる（最大）** | 23,689,911,808 | 24,641,536,000 |
| 14 | OOM（micro-step 1 の forward） | 24,819,349,504 | 24,876,417,024 |
| 16 | OOM（同） | 24,377,192,960 | 24,779,948,032 |

一歩の時間（60 micro-step、最初の 8 を除く平均。GPU4、06:40:51–06:45:48 UTC。**同時に D6（GPU1,3）、特徴の取り出し（GPU2）、06:41:56 以降は工程塔の評価（GPU0）が動いていた**）:

| batch | 計算だけ (s/micro-step) | 読み込みの待ちを含む (s/micro-step) | allocated (bytes) | reserved (bytes) |
|---|---|---|---|---|
| 13 | 1.233716 | 1.234639 | 23,689,911,808 | 24,641,536,000 |
| 12 | 1.168135 | 1.168881 | 21,905,244,672 | 23,999,807,488 |
| 8 | 0.802425 | 0.803125 | 14,775,793,152 | 16,221,470,720 |
| 13 + expandable_segments | 1.273527 | 1.274299 | 23,680,405,504 | 23,832,035,328 |

### E.4 記憶の確保の設定

`expandable_segments:True` で batch 13 の reserved は 24,641,536,000 → 23,832,035,328 bytes に減り、allocated はほぼ同じ（23,689,911,808 → 23,680,405,504）。
batch 14 以上が収まるかは試していない（allocated が装置の容量に近いため、E.2 の OOM は確保の断片化ではなく量による）。

### E.3 特徴の取り出しと時間ヘッド（GPU2）

    extract（06:40:51–06:47:38 UTC。同時に D6、GPU4 の測定、GPU0 の評価）:
      frames 15437, feature_shape [15437, 2048], elapsed_seconds 400.70, batch 16
      max_memory_allocated 4,103,955,968 bytes / reserved 6,182,404,096 bytes
      feature_sha256 5823279fe5e3c6ed3559b2ebf12d42fdd46ab577a0907ba0501fa94109938190
      cache_sha256   aa4aa85e81d5bd39033f9a016f15bcc763e86d41125fe220dd26ae14b69306f0（127,016,156 bytes）
    三周目の記録 experiments/phase1/stage1_ptower_r3_029_features_coco_lr0.0001_foldA_seed42/feature_audit.json（ilya）:
      feature_sha256 5823279f…0190 / cache_sha256 aa4aa85e…06f0 / cache_bytes 127016156 → **bit 一致**（記録の elapsed 743.55 s）

特徴は repo の外 `$S/E/features_005_foldA/all_gap.npz` に置いた（三周目の設定の `data/processed/` は使っていない）。

    head（候補 A、L6、06:48 UTC。同時に F の検出塔の評価 GPU0,1 / GPU3,4）:
      elapsed_seconds_train 10.36、epochs_completed 22、max_memory_allocated 103,205,376 bytes
    1 回目（06:47:38）は本契約の道具の誤り（CUDA の初期化前に `reset_peak_memory_stats`）で学習に入る前に落ちた。
    `torch.cuda.init()` を足して回し直した。

`base.evidence` は本プロセスの中だけ repo の外へ書く代わりのものに差し替えた（`experiments/phase1/` に実験フォルダを作らず、W&B にも送らない）。
学習の値（損失、Jaccard）は報告しない（SPEC §9）。

## F. ホストをまたぐ評価

### F.2 工程塔（GPU0、06:41:56–06:43:44 UTC）— `tools/ptower_eval.py`

`stage1_ptower_r3` の `FoldFrames`（val、評価の変換）、`build_backbone`、`frame_predictions`、`frame_accuracy` をそのまま使う
（`finetune` が最良 epoch で `metrics.json` に書いた評価と同じ）。batch 16（記録の `ft_batch_size`）。

| 指標 | dlsta | 記録（ilya） | 差 |
|---|---|---|---|
| phase_accuracy | 0.8521452145214522 | 0.8521452145214522 | 0.0 |
| phase_macro_f1 | 0.724317175199036 | 0.724317175199036 | 0.0 |
| phase_jaccard | 0.6459769332647092 | 0.6459769332647092 | 0.0 |
| phase_edit_score | 10.090090090090087 | 10.090090090090087 | 0.0 |
| phase_seg_f1_10 / 25 / 50 | 0.1762440758293839 / 0.13692239336492892 / 0.07723637440758295 | 同 | 0.0 |

**7 指標とも全桁一致。** best_epoch 17（記録 17）、val 1,515 フレーム、checkpoint sha256 a90cf04d…（B6b と同じ）。
対照（F.4）: 折り B の塔 008 を同じ折り A の val に当てると phase_accuracy 0.994059405940594、macro_f1 0.9865177313868766、
jaccard 0.9749831744935785（折り A の val の動画 09・10 は折り B の train に含まれる）。値は変わる。

### F.1 検出塔（D\*-COCO 折り A seed 42、`tools/dtower_eval.sh`、2 プロセス）

1 回目（06:45:43–06:47:31 UTC）は **AP 0.0**。ログに
`warnings.warn("Given string, only url and local path of weight are supported, skip loading.")` / `State dict is None, skip loading`。
checkpoint を repo 相対で渡したが、`scripts/eval_relation_detr_map.py` は `os.chdir(REPO)`（49 行、REPO = third_party/Relation-DETR）するため
経路が解決されず、**重みを読まずに評価して AP 0 を返した**（道具は失敗にしない）。記録の起動は絶対経路。出力は `$S/F/relative_path_failed/` に退けた。

2 回目（絶対経路。06:47:58–06:49:45 UTC、GPU0,1。対照は GPU3,4 で同時。同時に GPU2 で時間ヘッド）。両ログとも `skip loading` 0 件。

| 指標 | dlsta | 記録 eval_val.json | 差 |
|---|---|---|---|
| AP | 0.7273447938494212 | 0.7273450248398429 | −2.310e−07 |
| AP50 | 0.8518075762096913 | 0.851807431425236 | +1.448e−07 |
| AP75 | 0.7751047045426627 | 0.7751046134971612 | +9.105e−08 |
| AP_l | 0.7369515101597268 | 0.7369517644079752 | −2.542e−07 |
| AR100 | 0.8622362044555049 | 0.8623106092174095 | −7.440e−05 |
| AR_l | 0.8701806438439539 | 0.8702550486058586 | −7.440e−05 |
| AP_s, AP_m, AR1, AR10, AR_s, AR_m | 記録と同じ | — | 0 |
| 標的群 AP（Skewer, Bipolar Forceps, Scalpel, Syringe, Raspatory） | 0.7950740420442742 | 0.7950748008550899 | −7.588e−07 |
| 陰性対照群 AP（Gauze, Mouth Gag, Suction Cannula, Tweezers） | 0.6726633578860826 | 0.6726631817581498 | +1.761e−07 |

クラス AP で差があるのは Forceps −1.457e−07、Gauze +7.045e−07、Needle Holders +1.393e−09、Syringe −3.794e−06 の 4 つ。ほか 10 は同じ、Retractor は両方 NaN。
**全桁一致ではない。** 差の大きさを記録の seed 間と並べる: 折り A の D\*-COCO の val AP は seed 42 / 123 / 456 で
0.7273450248 / 0.7288631052 / 0.7189796812（標準偏差 0.005322、範囲 0.009883）。AP の差 2.31e−07 は標準偏差の約 4.3e−05 倍。
原因は測っていない（UNKNOWN）。

対照（F.4）: 折り B の D\*-COCO seed 42 を同じ折り A の val に当てると AP 0.9265627722967424（標的群 0.9490276787782449）。値は変わる。

### D.7 同じ処方の 2 本を二つの NVLink の組で同時に（06:49:58–06:56:32 UTC）

ほかに GPU を使うものは無い状態で同時に起動した（起動前 GPU0〜4 compute プロセス 0）。

| 名前 | GPU | 窓平均（0…600 歩） | 100 歩目以降の平均 | torch allocated rank0 / rank1 (bytes) | nvidia-smi (MiB) |
|---|---|---|---|---|---|
| d7_nv12_concurrent | 1,2 | 1.3405, 0.6722, 0.6357, 0.6323, 0.5686, 0.5871, 0.601, 0.5613, 0.5874, 0.5923, 0.5974, 0.6126, 0.5753 | 0.59555（定常） | 12,288,233,984 / 11,602,772,480 | 12,563 / 12,145 |
| d7_nv34_concurrent | 3,4 | 1.3125, 0.6399, 0.6065, 0.6168, 0.571, 0.5857, 0.5964, 0.5649, 0.5956, 0.5864, 0.5909, 0.5628, 0.5726 | 0.58633（定常） | 12,289,270,784 / 11,594,959,872 | 12,559 / 12,145 |

単独（D1、GPU1,2）の 0.59848 s/歩と並べると、2 本同時でも一本あたりの一歩は遅くならなかった（−0.5% / −2.0%）。

### G.3 checkpoint の大きさと空き容量（06:5x UTC）

Task D と E の測定は epoch の終わりに届く前に止めたので、検出塔と工程塔の backbone の checkpoint は出ていない
（出たのは時間ヘッドの `best.pth` 1,341,818 bytes だけ。repo の外）。既存の checkpoint の大きさ（`stat -c %s` / `du -sb`）:

| もの | 大きさ (bytes) |
|---|---|
| 検出塔 D\*-COCO 折り A seed 42 `work/best_ap.pth` | 195,421,066 |
| 同 `work/best_ap50.pth` | 195,422,778 |
| 同 `work/checkpoints/checkpoint_<epoch>/`（accelerate の状態一式。5 つ残る `total_limit=5`） | 各 583,539,300 |
| 同 `work/` 全体 | 3,314,951,357 |
| 工程塔三周目 005 `checkpoints/best.pth` | 94,405,478 |
| 本契約の `$S` 全体（特徴 127,016,156 を含む） | 145,612,791 |

    df -B1 /home/ubuntu/local/m2 → avail 2455952130048（80%。A.6 の 2529740029952 から約 74 GB 減。本契約の書き込みは repo の外 $S と
    third_party/Relation-DETR のソースと .venv-relation-detr。`du -sb`: .venv-relation-detr 5,036,875,209、third_party/Relation-DETR 2,239,243,471（うち C.1 の前から在ったキャッシュ 2,235,383,808）、~/.cache/torch_extensions 4,082,139。残りの減少は本契約の書き込みではない（出所は測っていない）。$S は overlay で別の装置）

### D.6b NVLink の無い組で GPU0 を含む組（GPU0+GPU1、NODE）（06:56:38–07:03:12 UTC）

利用者の許可で GPU0 を使った。起動前 GPU0〜4 の compute プロセス 0、ほかに GPU を使うものは無い。

    dtower_probe.sh d6b_node01_b2 0,1 29861 configs/train_config_egosurgery_seed42.py 600 → status=reached wall 394 s
    窓平均: 1.3296, 0.6578, 0.6067, 0.6285, 0.5742, 0.5915, 0.5902, 0.5772, 0.6177, 0.6067, 0.6124, 0.5935, 0.6062
    100 歩目以降の平均 0.60044 s/歩（定常）。torch allocated 12,279,308,288 / 11,594,992,128、reserved 12,597,592,064 / 12,199,133,184 bytes
    nvidia-smi 12,529 / 12,073 MiB。終了後 GPU0 used=99MiB compute_procs=0（開始時と同じ。77 MiB の上乗せは本契約と無関係に続く）

| 組 | 接続 | 一歩 (s) |
|---|---|---|
| GPU1–2 | NV4 | 0.59848 |
| GPU0+1 | NODE（NVLink 無し、同じ NUMA） | 0.60044 |
| GPU1+3 | SYS（NVLink 無し、NUMA をまたぐ。同時に別の測定あり） | 0.60637 |

## H. env-facts

`context/env-facts.md` の dlsta の記述 2 か所（19 行と 46 行）の**直後に**、日付と契約つきの行を 9 行足した。既存の行は一字も変えていない
（食い違う 2 行は、直後の行で「↑ 旧記述」と明記した）。

    git show HEAD:context/env-facts.md と現在の行の集合差: 消えた行 0 / 足した行 9
    対照: 現在の写しから既存の 46 行目を 1 行消すと、消えた行 1 を検出

## I. 検証と報告

### I.1 検査（07:03:44 UTC）

    make task-validate TASK=... → OK（1 task(s), 0 failed）
    make spec-check TASK=...    → "rules_checked": 9, "status": "pass"
    make forbidden-check TASK=... → status pass、changed 14、violations []、permitted は allow_write の 2 接頭辞だけ
    対照: changed_paths をプロセス内で差し替えて data/raw/ego/train/01/control_write.jpg を足す
          → status fail、violations [{'path': 'data/raw/ego/train/01/control_write.jpg', 'reason': '禁止領域 data/ の内側'}]（data には書いていない）

### I.2 試験（後）（06:46:42–06:47:37 UTC、CUDA_VISIBLE_DEVICES=4、--continue-on-collection-errors）

    6 failed, 888 passed, 22 warnings in 52.04s
    前と比べて増えた名前: なし。消えた名前: ERROR tests/test_stage1_dtower_convergence.py

### I.3 前後の要約値（07:03:44 UTC）

    data/raw      before=db3efcf3a0e10717… after=db3efcf3a0e10717…
    data/external before=33d245518e01a5ac… after=33d245518e01a5ac…
    known_hosts   dfe8b109831f503c0ed78f0f6cc4ef901336aa6097e70005732f19ff8426ea6e（A.8 と同じ）

### I.4 終了時の GPU（07:06 UTC）

    GPU0 used=99MiB compute_procs=0 / GPU1 22 / GPU2 444 / GPU3 22 / GPU4 22（いずれも compute_procs=0）
    本契約のプロセス（accelerate、memprobe、ptower_probe、nvidia-smi の採取）: 0 件
    GPU2 の 444 MiB は 2 秒後に 22 MiB に戻った（07:06:20 UTC の 3 回の採取: 444, 22, 22 MiB、使用率 0%）。
    本契約の処理が 0 件の時点で容器の外から一時的に確保されたもの。本契約の GPU の測定はすべて 07:03:12 UTC までに終わっていた。

### I.5 commit の前

`git add` の 1 回目は `fatal: Unable to create '.git/index.lock': File exists.` で失敗した。直後に `index.lock` は無く、
git のプロセスも見えなかった（ほかの git 操作と一時的に重なった）。もう一度実行した。

### I.6 送出（07:1x UTC）

    git push -u origin feat/dlsta-tower-feasibility → [new branch]、遠隔の先頭 1e2d7444ee92da3f07fc219af94e39f661d7c3a1
    gh pr create --base phase0 --head feat/dlsta-tower-feasibility → https://github.com/takuya3h/m2/pull/245
    gh pr view --json number,isDraft,baseRefName,headRefName
      → {"baseRefName":"phase0","headRefName":"feat/dlsta-tower-feasibility","isDraft":false,"number":245}

### I.7 台帳への送り返し（commit c19ccde3 を push した後）

    source scripts/load_env.sh && make task-report TASK=T-2026-10-19-dlsta-tower-feasibility → rc=0
    {"task_id": "T-2026-10-19-dlsta-tower-feasibility", "verdict": "pass", "n_issuer_defects": 2,
     "report_sha256": "f21f494d451591b99b6f951e1c27269d571eab598976b98cc1dc872f5e7a01a6", "report_bytes": 10032, "replaced_blocks": 0}

この節を足した commit を push した後に、定期監視を止め、`make task-release END=complete` で抑止を外す。
