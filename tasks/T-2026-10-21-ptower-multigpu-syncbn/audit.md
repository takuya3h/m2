# audit — T-2026-10-21-ptower-multigpu-syncbn

時刻は UTC（容器の時計）。JST は +9 時間。大きな記録は repo の外 `$S = ~/m2-scratch/T-2026-10-21-ptower-multigpu-syncbn/` に置いた。
道具は `tasks/T-2026-10-21-ptower-multigpu-syncbn/tools/`（`$T`）。

## 利用者の指示（2026-10-21、/task の引数）

> 変更点なんだけど、GPU0だけ他ユーザーが使ってるから使用しないで

GPU0 は使わない。契約 §2 の「GPU0〜GPU4 のすべてを使ってよい」をこの指示で狭めた。

## Task A — 開始状態

### A.1 / A.2 分岐・起点・作業ツリー・目印

    git branch --show-current            → feat/ptower-multigpu-syncbn（feat/ で始まる）
    git merge-base HEAD origin/phase0    → 0a111a6eb9edde53e0118c46cfded37b6f6247b8
    git rev-parse origin/phase0          → 0a111a6eb9edde53e0118c46cfded37b6f6247b8（起点 = origin/phase0）
    git status --porcelain               → ?? tasks/T-2026-10-21-ptower-multigpu-syncbn/（task-start が取り込んだ契約だけ）
    .sync-pause                          → 開始前は無し。task-start が「.sync-pause を作成」と表示（この契約が置いた）
    grep -c sync-pause ~/bin/m2-sync.sh  → 2（稼働中の版は対応済み）
    ps（python / torchrun）              → 0 件（別の契約の処理は無い）

開始前の状態確認（`/task` の 0）: 現在の分岐 feat/dlsta-tower-feasibility、porcelain 0 行、feat/ptower-multigpu-syncbn は手元にも遠隔にも無し、
`tasks/<task_id>` の履歴無し → 「清浄」で task-start。`[task-start] 完了。` を確認。

ホスト: `hostname` → `4f3861ae8d3b`（容器の識別子。env-facts の「容器内で OS のホスト名は英数の識別子」と合う）、repo は `/home/ubuntu/local/m2`
（env-facts「dlsta のみ — ~/local/m2」と一致）。`nvidia-smi topo -m` は env-facts の dlsta の行と一致（NV4 は GPU1–GPU2 と GPU3–GPU4、
GPU0 は GPU1・GPU2 と NODE、NUMA 0 が GPU0〜2、NUMA 1 が GPU3〜4）。

### A.3 GPU の所有者と使用量

道具: `$T/gpu_owners.py`（`/proc/PID/exe` の解決と完全一致。部分一致は使わない）。使用量は 5 秒ごとに `$S/gpu_log.txt` へ記録し続けた。

開始時（08:36〜08:38）の採取:

| 時刻 | GPU0 | GPU1 | GPU2 | GPU3 | GPU4 |
|---|---|---|---|---|---|
| 08:36 | 99 MiB / 0 % | 442 MiB / 96 % | 22 / 0 | 22 / 0 | 22 / 0 |
| 08:37:15〜08:37:46 | 99 / 0 | 444 / 92〜96 % | 22 / 0 | 22 / 0 | 22 / 0 |
| 08:37:56 | 313 / 0 | 445 / 0 | 22 / 0 | 22 / 0 | 22 / 0 |
| 08:38:06 | 313 / 0 | 22 / 0 | 22 / 0 | 22 / 0 | 22 / 0 |
| 08:38〜（数分後） | 811〜813 MiB / 89〜94 % | 22 / 0 | 22 / 0 | 22 / 0 | 22 / 0 |

compute プロセスの一覧（`nvidia-smi --query-compute-apps`）は五枚とも 0 件、所有者の数え 0。**GPU0 と GPU1 の使用は容器の外のもの**
（自分の処理はこの時点で GPU を使っていない）。

記録 `$S/gpu_log.txt` の集計（08:41:01〜08:52:09、132 採取。自分は GPU2〜4 だけを使った）:

| GPU | 使用の見えた採取 | 最大の記憶量 | 自分の使用 |
|---|---|---|---|
| GPU0 | 132 / 132 | 813 MiB | なし |
| GPU1 | 72 / 132（08:41:36〜08:50:58） | 737 MiB | **なし** |
| GPU2 | 37 | 9,188 MiB | あり（A.6〜B.3） |
| GPU3 / GPU4 | 2 | 497 MiB | あり（二枚の試験、08:49） |

判定: GPU0 は利用者の指示と観測の両方で使わない。**GPU1 も他の利用者の使用が断続的に見えるので使わない**（契約 A.3「他の利用者の使用が見える GPU は使わない」）。
**使う GPU は GPU2・GPU3・GPU4**（三枚。G1 の「二枚以上」を満たす）。

所有者の数えの対照（acceptance a）: GPU2 に自分の python を 1 本起こした状態で

    gpu_owners.py                                  → GPU2 の owners ['ubuntu']、exe /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11
    gpu_owners.py --count-exe <上の exe>            → count 1
    gpu_owners.py --count-exe /nonexistent/bin/python3.11 → count 0

### A.4 版

    torch 2.1.2+cu118 / CUDA 11.8（torch の） / NCCL 2.18.6 / cuDNN 8700 / driver 595.84 / git 2.43.0 / 論理 CPU 96（nproc）

### A.5 起点の実測

    git log -1 --format=%H -- context/conventions.md → 2d946b07a57abebc4a8f66150d6dbaf2ccd22186（起票時 2d946b07 と一致）
    git log -1 --format=%H -- runindex/              → 63ae65da8c7d32df591f5e2ee4358286b72c726b（起票時と一致）
    行数（見出しを除く） index 1961 / experiments 750 / verdicts 1506（起票時と一致）

差し替えは無い。`meta.amendments` は空のまま。

### A.6 試験（直す前）

    CUDA_VISIBLE_DEVICES=2 python -m pytest tests/ -q -p no:cacheprovider -rfEs   → 6 failed, 911 passed（55.14 s）

失敗の名前の集合（`$S/fail_names_before.txt`）:

    tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    tests/test_fetch_task.py::test_rejects_unknown_file_name
    tests/test_research_logger.py::test_log_run_idempotent
    tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

### A.7 一枚の道の「直す前」の値

道具: `$T/single_path.py`。実物の `stage1_ptower_r3.main` に設定を渡して `finetune` を通す（Hydra は設定を渡すと解析を飛ばして本体を呼ぶ）。
差し替えは `FoldFrames`（train 38 枚・val 8 枚の等間隔の部分集合）と `base.evidence`（repo の外の代役）だけ。
`ft_batch_size=4 ft_accum_steps=4 ft_epochs=1 workers=2`、seed 42、GPU2。1 epoch = 10 歩（末尾 2 枚、累積の端数 2 歩）。
要約値は保存した state dict の全 320 項目（running の統計と num_batches_tracked を含む）。

| 実行 | 直したか | ft_lr | state の要約値 | train_loss |
|---|---|---|---|---|
| before_1 | 前 | 0.0003 | 0e7bc8889d88b32783d59e4664ba215a711f62057f821d5e0878519bdc44e9ec | 2.038065947984394 |
| before_2 | 前 | 0.0003 | 0e7bc8889d88b32783d59e4664ba215a711f62057f821d5e0878519bdc44e9ec | 2.038065947984394 |
| before_lr（陽性対照） | 前 | 0.0001 | 98ea7600c1cf49d085fbcd841a358387d969392b7d3141587c6ee92e2af61b6c | 2.1112702896720483 |

### A.8 集合（前）

    find experiments -printf '%P\n' | sort → 28,699 行、sha256 4432a56c29a8507ea31a910b169f0a908e8695d97308a8c54c37a457ababaf22
    find runindex    -printf '%P\n' | sort → 1,978 行、sha256 8b9a95dc317d531f5d756846e70df7833a5ad068267670bac53460c4710bb9be
    find -L data -printf '%P\t%s\t%T@\n' | sort → 236,663 行、sha256 20f001c05add6da0405a2ba6e89f6e60fc4174d2acceea12df9fe905845c753f

一覧は `$S/paths_before_{experiments,runindex}.txt`、`$S/listing_before_data.tsv`。

### プリフライト

    make task-validate → OK（WARN なし）
    make task-preflight → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL
      SKIP: P2 cuda_ext_loaded, P3 deterministic_flags（契約に記載なし）, P4 P5 P13 P14（exp のみ）, P12（参照なし）
      P11 gpu_free は PASS「compute プロセスは 0 件」。**容器の外の GPU0・GPU1 の使用は見ていない**（RESULT の起票者の誤り）

### 関門 G1 → 通過

分岐 feat/、起点 origin/phase0、作業ツリーは契約だけ、別の契約の作業なし、他の利用者が使っていない GPU は三枚（GPU2〜4）。

## Task B — 実装

変更範囲:

- 新規 `scripts/stage1_ptower_r3_dist.py`: 二枚以上の道（torchrun で `WORLD_SIZE>1` のときだけ）。layer1〜4 だけ SyncBatchNorm、DDP、
  累積の境以外は `no_sync`、大域 batch を一枚と同じに切って rank に分ける sampler（末尾は残し、大きさの差は 1 以内）、
  末尾の不均等を補う損失の尺度（`sum × world / count`）、rank ごとの増強の種（`seed×1000+rank`）、rank 0 だけの評価・保存・証拠・W&B、
  打ち切りの判断の broadcast、rank ごとの記憶量の最大と決定性の設定の読み出し
- `scripts/stage1_ptower_r3.py` の `main`: `WORLD_SIZE>1` のときだけ上へ振り分ける（finetune 以外は止める）。**一枚の道の関数は 1 行も変えていない**
- 新規 `tests/test_stage1_ptower_r3_dist.py`: CPU 13 件 + 二枚の GPU 1 件（二枚が無ければ skip）

### B.2 試験

    CUDA_VISIBLE_DEVICES="" pytest tests/test_stage1_ptower_r3_dist.py tests/test_stage1_ptower_r3.py → 38 passed, 1 skipped（needs two GPUs）
    CUDA_VISIBLE_DEVICES=3,4 pytest tests/test_stage1_ptower_r3_dist.py -k two_gpus                    → 1 passed（resnet18 の写しで勾配差 < 1e-4、SyncBN なしで > 1e-3）
    ruff check（変更した 3 ファイル）→ All checks passed

初回の CPU 試験で 1 件失敗した（試験の側の誤り。sampler の epoch を合わせ忘れていた）。直して再実行で通過。

### B.3 一枚の道（直した後）

| 実行 | ft_lr | state の要約値 | train_loss |
|---|---|---|---|
| after_1 | 0.0003 | 0e7bc8889d88b32783d59e4664ba215a711f62057f821d5e0878519bdc44e9ec | 2.038065947984394 |
| after_lr | 0.0001 | 98ea7600c1cf49d085fbcd841a358387d969392b7d3141587c6ee92e2af61b6c | 2.1112702896720483 |

直す前（A.7）と完全に一致。

### 試験全体（直した後）

    CUDA_VISIBLE_DEVICES=2 python -m pytest tests/ -q -p no:cacheprovider -rfEs → 6 failed, 924 passed, 1 skipped（59.81 s）
    comm -13 fail_names_before.txt fail_names_after_B.txt → 空（新しい失敗の名前 0）

### 関門 G2 → 通過

## Task C — 許容差（測る前に書いた。2026-10-21 08:53 UTC 以前、match.py を一度も走らせる前）

比べる量と測り方（`$T/match.py compare`）。参照 = 一枚・batch 8 の一度目。候補 = それ以外。

| 量 | 測り方 | 許容差 |
|---|---|---|
| 損失 | 各 micro-step の大域 batch の平均損失の相対差 `|a−b|/|a|` の最大 | `loss_rel ≤ 1e-4` |
| 勾配 | 各更新の直前の勾配の、テンソルごとの `‖g_c−g_r‖/‖g_r‖` の最大（三回の更新の最大） | `grad_rel ≤ 1e-3` |
| 正規化層の running の統計 | layer1〜4 の 52 層の running_mean・running_var の、初期値からの変化量どうしの相対差 `‖Δ_c−Δ_r‖/‖Δ_r‖` の最大 | `bn_delta_rel ≤ 1e-3` |
| 更新後の重み | 学習するテンソルごとの、初期値からの更新量どうしの相対差の最大 | `weight_update_rel ≤ 1e-2` |
| stem の bn1 | running_mean と running_var が初期値とビット単位で同じか | 同じであること（別判定） |

根拠:

- fp32 の機械 ε は 1.19e-7。一枚と二枚の違いは足し合わせの順序だけ（SyncBatchNorm は rank ごとの和を集めてから平均と分散を作り、
  DDP は二つの rank の勾配を足して割る。一枚は cuDNN が 8 枚を一度に畳む）。一つの演算の相対誤差は 1e-6 程度で、50 層・3 回の更新を
  通しても 1e-4 を大きく超えないと見込んだ。損失は勾配より手前なので一桁厳しく 1e-4、勾配と統計は 1e-3。
- 更新後の重みだけ 1e-2 に緩めた。AdamW の最初の数歩は更新量が `lr·g/|g|` に近く、勾配が 0 に近い要素では、丸めの差で符号が反転すると
  その要素の更新量が 2·lr 動く。百万要素のテンソルで数要素の反転でも相対差は 1e-3 を超えうる。符号の反転は勾配の差の 1e-3 判定とは別の量である。
- 陽性対照（SyncBatchNorm を外す）は各 rank が 4 枚の統計で正規化する。8 枚と 4 枚の平均の差は特徴の散らばりと同じ桁なので、
  running の統計の変化量と勾配は 1e-1 の桁で違うと見込む。許容差との間に二桁以上の余裕がある。
- 判定の規則: 候補は四つの量がすべて許容差以内なら「収まる」、一つでも超えれば「外れる」。三者（陰性対照・陽性対照・本番）に同じ規則と同じ許容差を当てる。

## Task C — 照合（結果）

道具 `$T/match.py`。一枚 = GPU2、二枚 = GPU3+GPU4（NVLink）、`--master_port=29511`。fold A の train から固定の並べ替えで 77 枚、
増強は**外した**（`train=False`、§5.2.9）。B=4（一枚は batch 8）、累積 4、1 epoch = 10 歩、末尾 5 枚（rank に 3 / 2）、
更新は 4・8・10 歩目。各 run は `$S/match/<名前>/run.pt`、比較は `$S/match/cmp_*.json`。

### fp32（契約どおりの照合。参照 = single_1）

| 候補 | loss_rel | grad_rel（更新ごと） | bn_delta_rel | weight_update_rel | 判定（許容差） |
|---|---|---|---|---|---|
| single_2（陰性対照） | 0 | 0 / 0 / 0 | 0 | 0 | 収まる |
| dual_nosync（陽性対照: SyncBN なし） | 1.14e-02 | 1.4 / 1.3 / 1.3 | 1.82e-01 | 1.50 | 外れる |
| **dual_sync（本番）** | **3.98e-04** | **8.4e-03 / 1.4e-01 / 3.5e-01** | **9.07e-03** | **1.88e-01** | **外れる** |
| dual_sync_2（本番の再実行） | 同上 | 同上 | 同上 | 同上 | 外れる |
| dual_plainmean（末尾を rank ごとの平均） | 5.88e-03 | 8.4e-03 / 1.4e-01 / 3.9e-01 | 9.07e-03 | 1.93e-01 | 外れる |
| single_stemtrain（stem の bn1 を train） | 3.89e-02 | 1.6 / 1.6 / 1.7 | 9.86e-01 | 1.47 | 外れる |
| dual_nodet（決定性の設定を切る） | 2.77e-03 | 4.3e-01 / 6.9e-01 / 7.4e-01 | 6.51e-02 | 8.53e-01 | 外れる |

本番の歩ごとの損失の相対差: 1〜4 歩目 2.2e-07 / 1.1e-07 / 0 / 1.1e-07（最初の更新の前は一致）、5〜8 歩目 1.4e-05〜3.1e-05、9〜10 歩目 3.5e-04〜4.0e-04。
最初の更新の勾配差はテンソルの中央値で 5.1e-03（特定の層に偏らない）。更新を重ねるごとに広がる（AdamW は最初の数歩で更新量が `lr·g/|g|` に近く、
0 に近い要素の丸めの差が更新の符号を変える）。最大の重みの差は 5.3·lr。

そのほかの確かめ（本番 dual_sync）:

- 決定性の設定: 両 rank で `deterministic_algorithms=True, cudnn_deterministic=True, cudnn_benchmark=False, matmul_tf32=False, cudnn_tf32=False,
  CUBLAS_WORKSPACE_CONFIG=:4096:8`。**止まった演算 0 件。** 切った写し（dual_nodet）では両 rank で `deterministic_algorithms=False` と読み出された
- 再現: dual_sync と dual_sync_2 の要約値がともに `21d48f6e4cd45e954cc105d8707203f25da9d31228890187b2175e92d552a108`、比較はすべて 0。
  両 rank の最終の要約値も同じ
- 割り振り: 両 rank の添字を合わせると大域 batch の集合と一致、重複 0、末尾は 3 / 2
- stem の bn1: 一枚・二枚とも running_mean と running_var が初期値とビット単位で同じ。stem を train にした写しでは変わる
- 末尾の重み: dual_sync と dual_plainmean の差は最後の更新（末尾を含む）だけに出る（0 / 0 / 2.1e-01）
- 記憶量の最大: 一枚 batch 8 = 14,774,590,976 bytes、二枚 4 枚ずつ = 各 rank 7,724,205,568 bytes

**関門 G3: 本番が許容差を外れた → 停止して諮る（on_fail: ask）。** 許容差は変えていない。

### 診断（許容差の判定ではない。原因の切り分けのため）

float64 で同じ比較を小さく回した（一枚 batch 4、二枚 2 枚ずつ、22 枚 = 6 歩・更新 4 と 6 歩目・末尾 2 枚 1/1。23 枚は末尾 3 枚 2/1）。

| 参照 → 候補 | loss_rel | grad_rel（更新ごと） | bn_delta_rel | weight_update_rel |
|---|---|---|---|---|
| s64 → d64（二枚 float64） | 2.4e-16 | 1.4e-13 / 3.1e-13 | 3.0e-13 | 8.4e-11 |
| s64 → d64_nosync（陽性対照） | 1.2e-02 | 1.5 / 1.7 | 4.1e-01 | 1.5 |
| s64u → d64u（末尾 2/1） | 2.4e-16 | 1.4e-13 / 5.4e-13 | 3.1e-13 | 1.8e-10 |
| s64u → d64u_plain（末尾を rank ごとの平均、2/1） | 2.5e-02 | 1.4e-13 / **3.1e-01** | 3.1e-13 | 1.7e-01 |
| s64 → s32（**一枚どうし**、fp32 と float64） | 1.7e-05 | **1.1e-02** / 2.1e-01 | 5.3e-03 | 1.7e-01 |
| s64 → d32（二枚 fp32） | 2.0e-05 | 1.5e-02 / 2.6e-01 | 5.5e-03 | 1.8e-01 |
| s32 → d32（一枚 fp32 → 二枚 fp32） | 9.7e-06 | 1.3e-02 / 2.8e-01 | 5.0e-03 | 1.9e-01 |

読み: float64 では二枚の道は一枚と 1e-13 の桁で一致し（陽性対照は 1.5）、末尾の重みの対照は末尾の更新だけで 0.31 外れる。
**fp32 では一枚の道そのものが float64 から最初の更新で 1.1e-2 ずれる。** 本番の二枚の差（8.4e-3、小さい設定で 1.3e-2）はこの fp32 の丸めの床と同じ桁である。
測る前に書いた許容差（勾配 1e-3）は fp32 の丸めの床より一桁厳しかった（見積もりの誤り。逸脱に記録する）。

### 利用者の判断（関門 G3、2026-10-21。Task D の開始 09:35 UTC = 18:35 JST より前）

問い: 本番が fp32 の許容差を外れ、float64 では 1e-13 で一致する。どう扱うか。
答え: **「float64 で判定し続行」**。実装の同等性は float64 の照合で判定し、fp32 の照合は記述として併記する。測る前に書いた許容差は変えない。

同じ問いの機会に GPU1 の扱いを尋ね、利用者は **「1-2, 3-4を確実に使って良い」** と答えた。GPU1 の外部使用は記録を続けたうえで、
Task E は契約どおり GPU1–GPU2、GPU1+GPU3、二本同時（GPU1–2 と GPU3–4）で測った。GPU0 を含む NODE の組は利用者の指示により測らない。

## Task D — 通し

道具 `$T/flow.py`。実物の `stage1_ptower_r3.main` を torchrun で起こし、`stage1_ptower_r3_dist.finetune` を通す。差し替えは
`FoldFrames`（train 38・val 8、反転の引きを rank ごとに記録）、`ExperimentManager` の置き場（`./experiments`、repo の外）、
`base.evidence`・`torch.save`・`tracking.init/log/finish` の呼び出しの記録だけ。W&B は **オフライン**（`WANDB_MODE=offline`、
`WANDB_DIR` は repo の外）で、**送っていない**。`ft_batch_size=4`（GPU ごと 2）、累積 4、GPU3+GPU4、`--master_port=29521`。

### D.1 / D.2 学習率の低下と打ち切り（`$S/flow/d1`、`--lr 0 --patience 1 --epochs 10`）

    [default0]:epoch=1 lr=0 loss=2.152647 val_accuracy=0.000000
    [default0]:epoch=2 lr=0 loss=2.149720 val_accuracy=0.000000
    [default0]:rank=0 lr lowered at epoch=2 to 0
    [default1]:rank=1 lr lowered at epoch=2 to 0
    [default0]:epoch=3 lr=0 loss=2.154113 val_accuracy=0.125000
    [default0]:epoch=4 lr=0 loss=2.147037 val_accuracy=0.125000
    [default0]:rank=0 early stop at epoch=4
    [default1]:rank=1 early stop at epoch=4

rank ごとの呼び出しの記録（`calls/rank<r>.jsonl`）:

| rank | base.evidence | tracking.init | tracking.log | torch.save | tracking.finish |
|---|---|---|---|---|---|
| 0 | 1 | 1 | 4 | 2（epoch 1 と 3 で改善） | 1 |
| 1 | 0 | 0 | 0 | 0 | 0（記録ファイル自体が無い） |

作られたもの: 実験フォルダ 1 件（`experiments/phase1/stage1_ptower_r3_001_ft_coco_lr0_foldA_seed42/`、10 ファイル。checkpoint 1 件）、
W&B のオフライン run 1 件（`wandb/offline-run-20261021_093518-5yo8fsfi`）。`finetune_history.json` に world_size 2、per_gpu_batch_size 2、
effective_batch_size 16（= 4 × 4）、lr_lowered_epoch 2、early_stopped_epoch 4、rank ごとの記憶量の最大と決定性の設定（両 rank とも True）。

各 epoch の画像の集合（反転の記録の frame から）: 4 epoch とも rank 0 が 19 枚・rank 1 が 19 枚、合わせて 38 枚・重複 0（train の部分集合と一致）。
反転の列: rank 間で 4 epoch とも列は一致せず、同じ位置で一致したのは 44 / 76（偶然の水準）。

### D.3 checkpoint を一枚の道で読む（`$S/flow/extract`）

`flow.py extract --checkpoint <d1 の best.pth>`（普通の起動、GPU3）。実物の `stage1_ptower_r3.extract`（`torch.load(weights_only=True)` →
`build_backbone` → `load_state_dict`、strict）を通した。manifest は各クリップの先頭 1 枚（22 枚）。出力 `features/all_gap.npz` は repo の外。

    EXTRACT_COMPLETE …/flow/extract/features/all_gap.npz sha=2834706f29ed88305d7b6c946d0a1b70d29954de1d53ec82babaa55642ed3492
    ckpt keys 320 / one-gpu model keys 320 / only_ckpt 0 / only_model 0 / <All keys matched successfully>

### 再現（§5.2.8、acceptance e。本番の二枚の道、反転あり、`--epochs 1 --lr 0.0003`）

| 実行 | seed | checkpoint の state の要約値 | 反転と画像の列 |
|---|---|---|---|
| r42a | 42 | f43442a634cbf78407a3b8d20076e1b876da4428a2bc97371394acd5654947bb | — |
| r42b | 42 | f43442a634cbf78407a3b8d20076e1b876da4428a2bc97371394acd5654947bb | r42a と同一 |
| r43 | 43 | 7fb6b73f7a33ebe3e38cc6e372c630551c6ca6578d7024a9284967c34e0e21b6 | r42a と異なる |

## Task E — 処方のままの記憶量と時間

道具 `$T/measure.py`。`stage1_ptower_r3_dist` の `setup`・`wrap`・`ShardedBatches`・`micro_step` を使い、設定ファイルの値のまま
（ft_batch_size 16 → GPU ごと 8、累積 4、800×1422、fp32、決定性の設定あり、fold A の train 9,657 枚、反転あり、workers 4）。
68 micro-step、最初の 8 を除いた平均。`wall` は前の歩の終わりから（読み込みの待ちを含む。REPORT §3 と同じ取り方）、`compute` は batch が届いてから。
各測定の間、五枚の使用量を 1 秒ごとに `$S/measure/<名前>.smi.txt` へ記録した。

| 構成 | GPU | wall 平均 [s] | wall 中央 [s] | compute 平均 [s] | torch 最大確保 [bytes]（各 rank） | 予約 [bytes] | nvidia-smi 最大 [MiB] | OOM |
|---|---|---|---|---|---|---|---|---|
| NVLink | GPU1–GPU2 | 0.7938 | 0.7948 | 0.7932 | 14,873,543,680 / 14,873,543,680 | 16,315,842,560 | 16,167 / 16,167 | なし |
| NVLink | GPU3–GPU4 | 0.7913 | 0.7903 / 0.7900 | 0.7907 | 14,873,543,680 / 14,873,543,680 | 16,315,842,560 | 16,167 / 16,167 | なし |
| SYS | GPU1+GPU3 | 0.8014 | 0.8006 / 0.8007 | 0.8007 | 14,868,907,008 / 14,868,907,008 | 16,336,814,080 | 16,097 / 16,097 | なし |
| NODE | GPU0+GPU1 | UNKNOWN | — | — | — | — | — | 利用者の指示で GPU0 を使わない |
| 二本同時 | GPU1–GPU2 | 0.8219 | 0.8219 / 0.8220 | 0.8213 | 14,873,543,680 / 14,868,907,008 | 16,315,842,560 / 16,336,814,080 | 16,167 / 16,187 | なし |
| 二本同時 | GPU3–GPU4 | 0.8064 | 0.8066 / 0.8067 | 0.8058 | 14,873,543,680 / 14,873,543,680 | 16,315,842,560 | 16,167 / 16,167 | なし |

二本同時は単独より GPU1–2 で +3.5 %（0.7938 → 0.8219）、GPU3–4 で +1.9 %（0.7913 → 0.8064）。両 rank とも決定性の設定は True。

一 epoch の歩の数 604（= ⌈9657 / 16⌉、末尾 9 枚は 5 / 4）。**一 epoch の学習の時間（計算値、val を含まない）**: 604 × 0.7938 = 479.5 s（GPU1–2 単独）、
604 × 0.8219 = 496.4 s（二本同時の GPU1–2）。

各測定の間の五枚（1 秒ごと、各 60 採取）: 使っていない GPU は 22 MiB・0 % のまま（GPU0 は 99 MiB・0 % のまま。開始時からの容器の外の確保）。
使った GPU の最大（16,097〜16,187 MiB）は自分の予約（約 15,560 MiB）と CUDA の文脈の和の桁で、他の利用者の使用が混ざった形跡は無い。

## Task F — env-facts

`context/env-facts.md` の装置の dlsta の行の下に 2 行を足した（Task E の値と版、GPU1 の容器の外の使用）。
`git diff --numstat` → 2 追加 / 0 削除。行の集合差（`LC_ALL=C sort` と `comm`）: 消えた行 0、足した行 2。

## Task G — 検証

    make task-validate TASK=…   → OK
    make forbidden-check TASK=… → status pass、changed 13、violations []
    make spec-check TASK=…      → status pass、rules_checked 9
    CUDA_VISIBLE_DEVICES=2 python -m pytest tests/ -q -p no:cacheprovider -rfEs → 6 failed, 924 passed, 1 skipped（58.17 s）
      新しい失敗の名前 0（`$S/fail_names_after_G.txt` と開始前の集合の差）。skip 1 は二枚の試験（GPU を一枚だけ見せたため）
    CUDA_VISIBLE_DEVICES=3,4 python -m pytest tests/test_stage1_ptower_r3_dist.py → 14 passed

forbidden-check の陽性対照: repo の外の worktree の写し（HEAD + 本契約のディレクトリ）で、`data/splits/control_write.txt` を足す前は
`pass []`、足すと `fail [{'path': 'data/splits/control_write.txt', 'reason': '禁止領域 data/ の内側'}]`。写しは `git worktree remove` で消した。

集合差（A.8 と終了時）:

    experiments: 追加 0 / 削除 0（sha256 4432a56c… 同じ）
    runindex:    追加 0 / 削除 0（sha256 8b9a95dc… 同じ）
    data:        経路・大きさ・更新時刻の一覧の差 0 行（sha256 20f001c0… 同じ）

接続: `origin` からの取得（task-start の fetch）、push、PR の作成、`make task-report` 以外の外への接続は行っていない。W&B はオフラインで送っていない。

`inputs.data.split_files`（`data/splits/ego_train.txt`、`ego_val.txt`）: 本契約の道具は直接読まない。`base.folds()`（`scripts/stage1_ptower.py`）が
折りの表を公式の分割と照合するときに読む（間接）。

変更範囲: `scripts/stage1_ptower_r3.py`（main の振り分け、+7 行 −1 行）、`scripts/stage1_ptower_r3_dist.py`（新規）、`tests/test_stage1_ptower_r3_dist.py`（新規）、
`README.md`（節を追記）、`context/env-facts.md`（2 行追記）、`tasks/T-2026-10-21-ptower-multigpu-syncbn/`（契約・道具・報告）。

repo の外に残したもの: `~/m2-scratch/T-2026-10-21-ptower-multigpu-syncbn/`（照合の run、通しの実験フォルダと checkpoint、測定、GPU の記録）。

行の集合差の陽性対照: 現在の env-facts から既存の 48 行目（dlsta の装置の行）を消した写し（repo の外の scratchpad）では、消えた行 1・足した行 2。本物は消えた行 0・足した行 2。
