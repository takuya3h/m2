# 監査記録: bengio での P3 の 4 本（契約 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle の一部）

実行者: bengio の Claude Code（セッション 27406320-adb9-41c4-9a6b-6ce8161e609c）。手順は `handoff_bengio.md`。時刻は JST。
測っていない値は UNKNOWN と書く。

## 現況（2026-10-20 00:5x JST）

**終わった。** §7 のとおり bengio の担当は P3 の `pred_CF`・`gtpred_CF` の 2 本（`gt`・`shuffle` は andrew）。2 本とも rc=0 で、S10 の確認はすべて通った（末尾の「S10」）。
環境の直し（`.venv-relation-detr` の向け直し）・重ねの BODY・worktree は残してある（戻すかどうかは利用者が決める）。

## 22:27 JST の停止（記録）

22:27 JST に S4 で止めて利用者に諮った。その時点で本番は起動しておらず、S5 以降は未実施だった。

止めた理由（3 件。いずれも手順書の「止めて諮る」に当たる）:

1. **Relation-DETR のソースが andrew と違う**（S4）。違うファイルは 23 件（下の表）。手順書が学習に効くと名指しする
   `transforms/presets.py`・`optimizer/param_dict.py` を含む。直していない
2. **検出器の仮想環境 `.venv-relation-detr` が壊れている**。`bin/python` は `/home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11`
   への壊れたリンクで、bengio にこの python は無い。正式な S4・S5〜S8 はこの環境で回すため、回せない。直していない
3. **GPU 2 枚に本件以外の compute プロセスが居る**（S1）。止めていない

## S1 開始状態（読むだけ）

| 項目 | 値 |
|---|---|
| hostname | `Bengio` |
| 時刻 | 2026-10-19 22:22:44 JST |
| GPU | RTX A6000 × 2。**どちらも使用中**: GPU 0 38,835 MiB / 49,140 MiB・75%、GPU 1 38,832 MiB / 49,140 MiB・76% |
| compute プロセス | 2 件。PID 296512 `python3 /tmp/gpu_dummy_load.py 0`、PID 296513 `python3 /tmp/gpu_dummy_load.py 1`（`/proc/PID/exe` は `/usr/bin/python3.12`、cwd `/home/ubuntu`） |
| その起動元 | 親 PID 296510（`zsh -c` で `/tmp/gpu_dummy_load.py` を書き出して 2 本起こす）、その親 PID 64578 `codex app-server`（2026-10-19 03:29 JST から常駐）。起動は 2026-10-19 22:19:11 JST |
| その中身 | libcuda を直接呼び、各 GPU の全メモリの 80% を確保し、空回りのカーネルを目標の占有率 70% で回し続ける（`/tmp/gpu_dummy_{0,1}.log`: `GPU 0 allocated 38525 MiB, target duty 70%`、`GPU 1 allocated 38542 MiB, target duty 70%`） |
| `df -B1 /home/ubuntu/slocal2` | 総 7,937,302,376,448、使用 6,631,451,766,784、空き 905,755,742,208（88%） |
| `free -b` | 総 134,986,752,000、available 114,546,069,504。swap 2,147,479,552 のうち 2,146,299,904 使用 |
| main の作業場所 | 分岐 `feat/proposal-gate-brief`、`status --porcelain` 10 行（すべて `?? experiments/phase1/stage2fix_pd_*`。同期で配られた andrew の run）。**変えていない** |
| `grep -n 'cd "\$M2DIR"' ~/bin/m2-sync.sh` | `29:cd "$M2DIR" \|\| exit 1` |
| `grep -c worktree ~/bin/m2-sync.sh` | `0` |
| worktree を cwd にするプロセス | 0 件 |

## S2 worktree と分岐

**本セッションの前に既に作られていた**（`.git` の作成 2026-10-19 22:09:53 JST。作った者は UNKNOWN）。本セッションでは作り直していない。

    git -C /home/ubuntu/slocal2/m2 worktree list
    /home/ubuntu/slocal2/m2                 23183b42 [feat/proposal-gate-brief]
    /home/ubuntu/slocal2/m2-s2fix-bengio    707d9d4a [feat/stage2-pilot-fix-epoch4-shuffle-bengio]

- `git -C $WT rev-parse HEAD` = `707d9d4a9d10c38a5e80ea1c92e872a584be5d6a`（`handoff_bengio.md` を含む commit）
- `origin/feat/stage2-pilot-fix-epoch4-shuffle` は fetch 後 `c0f11094d4d7b37c6e07921e3c6b57eea60eef60`（andrew の P1-W1 の 3 本と中間記録を足した 1 commit が先にある）
- 前回の試みの残り: `experiments/analysis/stage2_pilot_fix/bengio/input_digest_bengio.log`（22:11:28 JST、92 バイト、未追跡）。中身は
  `(eval):1: no such file or directory: /home/ubuntu/slocal2/m2/.venv-relation-detr/bin/python`
- `$FIX/identity/`・`$FIX/pd_ckpt/`・`$FIX/queues/` は 22:11 JST に作られていた（どれも空）

## S3 信号

8 本とも既に同じ絶対経路にあった（本セッションでは写していない）。`sha256sum` は 8 本とも `input_digest_andrew.json` の `signals` と一致。
検出塔の重み `best_ap.pth` も `30d199b15201cf3c03954852d8acc6fb58fe5349baef2fd200e877237ff682c4` で一致。

## S4 入力の照合（予備。正式ではない）

`.venv-relation-detr` が壊れているため、**本体の `.venv`（torch 2.1.2+cu118、CUDA 11.8、cuDNN 8700）で予備的に**回した。出力は worktree ではなく scratchpad に置いた。
正式な S4 は `.venv-relation-detr` を直したあとに回し直す。

    /home/ubuntu/slocal2/m2/.venv/bin/python $WT/scripts/stage2pilot/input_digest.py --body /home/ubuntu/slocal2/m2 --out <scratchpad>/input_digest_bengio_prelim.json   # rc=0

andrew の値との突き合わせ:

| 項目 | 結果 |
|---|---|
| 信号 8 本 | 一致 |
| 検出塔の重み | 一致 |
| 注釈（train・val） | 一致 |
| 画像の列 | 一致（train 9,657 枚 `c5c27b85…`、val 1,515 枚 `025c644b…`、欠け 0） |
| MS-Deform-Attn の CUDA ソース | 一致（`307450b3…`） |
| torch・CUDA・cuDNN | 一致（本体 `.venv` での値。`.venv-relation-detr` では UNKNOWN） |
| **Relation-DETR `source_tree_sha256`** | **違う**: andrew `2f08e521…`、bengio `3ade18f0…` |
| **Relation-DETR `source_files`** | **違う**: andrew 142、bengio 127 |
| Relation-DETR `commit`・`uncommitted` | 違う（andrew `b485955c…`・42、bengio `23183b42…`・10）。ただし bengio の `third_party/Relation-DETR` には `.git` が無く、この 2 つは親の m2 の repo を読んだ値で、比べる意味が無い |

ファイルごとの違い（sha256 の先頭 16 桁）:

| ファイル | andrew | bengio |
|---|---|---|
| `configs/relation_detr/relation_detr_resnet50_egosurgery_hand2det.py` | 19d9434d0398dddd | （無い） |
| `configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_camt.py` | 87494e07c555efac | （無い） |
| `configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_clsbias.py` | 044cdb02fa4d2c0f | （無い） |
| `configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_hc.py` | a3b895534e64a2fd | （無い） |
| `configs/train_config_egosurgery_s0_frozen.py` | 3a0e88485c16e528 | b30efda332d18f74 |
| `configs/train_config_egosurgery_s0_frozen_neck.py` | 841f1befdbce0296 | 6c5db4f370022117 |
| `configs/train_config_egosurgery_seed123.py` | 41a931aad26838a7 | 4943fa857ffeb0f3 |
| `configs/train_config_egosurgery_seed42.py` | 509c4a5923e49481 | 3f075f3751370e54 |
| `configs/train_config_egosurgery_seed42_augstrong.py` | 7d07d8a7799edc90 | （無い） |
| `configs/train_config_egosurgery_seed42_augstrong_hires.py` | c173d76e71486a07 | （無い） |
| `configs/train_config_egosurgery_seed42_hires.py` | ae93906a17e1e264 | （無い） |
| `configs/train_config_egosurgery_seed456.py` | 5efceac791433b63 | 8114e29ce65f1454 |
| `configs/train_config_egosurgery_stage1_imagenet_seed123.py` | 92275cc9548d1f9b | （無い） |
| `configs/train_config_egosurgery_stage1_imagenet_seed42.py` | c252e9c90329fe88 | （無い） |
| `configs/train_config_egosurgery_stage1_imagenet_seed456.py` | 8a72d01fce0fe820 | （無い） |
| `main.py` | ffbd6deb9ad48ec3 | 6c14063af155bea9 |
| `models/detectors/relation_detr_handprior.py` | d7976009465b3161 | （無い） |
| `models/detectors/relation_detr_phase_hc.py` | af5104bcd0915ca7 | （無い） |
| `models/detectors/relation_detr_phaseclsbias.py` | 7dbac50b1fb702db | （無い） |
| `models/detectors/relation_detr_phasecrossattn_mt.py` | 3c7eb208fd36ef61 | （無い） |
| `optimizer/param_dict.py` | d32e9f6b69dabddc | 4dfdcf00db849a9c |
| `transforms/presets.py` | 03812cf89589e0bf | b8080240ffa98306 |
| `util/convergence.py` | 299597a252674450 | （無い） |

見立て（確かめていない）: andrew の Relation-DETR の未 commit の変更（42 件）が bengio に運ばれていない。

## 仮想環境の状態（読むだけ）

- `.venv-relation-detr/pyvenv.cfg`: `home = /home/ubuntu/.pyenv/versions/3.11.4/bin`、`version_info = 3.11.4`。`/home/ubuntu/.pyenv/versions/` は bengio に無い
- uv の python は `cpython-3.11.16` だけ（3.11.4 は無い）
- nvcc: `/usr/local/cuda/bin/nvcc` 12.9（V12.9.86）がある

## S5〜S10（22:27 JST の時点）

未実施（上の 3 件の決着待ち）。

---

## 利用者の回答と再開（22:4x JST）

- 利用者の決定: bengio を直して回す。直し方は `handoff_bengio.md` §6（Relation-DETR は (b) 重ねの BODY、仮想環境は (a) uv の 3.11.16 へ向け直す）
- GPU の負荷: 利用者の指示「実験開始直前に `kill 296512 296513`」。GPU を使う最初の工程（R5）の直前に、PID の中身を確かめてから実行する
- 22:4x JST: 利用者の指示「P3 の gt と shuffle は andrew で始めたので、それ以外の 2 本だけ」。§7 の追補と同じ。
  本番は **GPU 0 に `P3 pred_CF`、GPU 1 に `P3 gtpred_CF`（1 枚に 1 本）**。試走は §7 のとおり `P3 gt smoke`

### 分岐を進める

worktree の分岐（ローカルの commit は無い）を origin の先頭へ早送りした（§6・§7 とパッケージの一覧を読むため）。

    git -C $WT merge --ff-only origin/feat/stage2-pilot-fix-epoch4-shuffle
    707d9d4a9d10c38a5e80ea1c92e872a584be5d6a → 6a9f99611b1637dafda8b9c8329cbe5d4953fc79（§7 の追補を含む）

main の作業場所は `feat/proposal-gate-brief` のまま（変えていない）。

### R1 仮想環境を直す（22:47 JST）

直す前:

    /home/ubuntu/slocal2/m2/.venv-relation-detr/bin/python -> /home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11
    python3 -> python、python3.11 -> python
    pyvenv.cfg: home = /home/ubuntu/.pyenv/versions/3.11.4/bin / implementation = CPython / uv = 0.11.15 / version_info = 3.11.4 / include-system-site-packages = false

写し: `/home/ubuntu/slocal2/m2/.venv-relation-detr/pyvenv.cfg.before_s2fix`（`cp -p`）。

    U=/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin
    ln -sfn $U/python3.11 .venv-relation-detr/bin/python
    sed -i "s|^home = .*|home = $U|; s|^version_info = .*|version_info = 3.11.16|" .venv-relation-detr/pyvenv.cfg

（bengio の uv には `cpython-3.11-linux-x86_64-gnu` → `cpython-3.11.16-linux-x86_64-gnu` のリンクもある。bengio の本体の `.venv` と同じく実体の経路を使った）

確かめ: `3.11.16 (main, Aug 14 2026, 15:35:36) [Clang 22.1.3 ] 2.1.2+cu118 11.8 8700 True`

パッケージの一覧: `experiments/analysis/stage2_pilot_fix/bengio/venv_relation_detr_freeze_bengio.txt`（72 個、`(名前の小文字, 版)` の順に並べた）。
andrew の一覧と**全行一致**（両方とも sha256 `2c7b070c93ca5a3953b70336125279d0ac5e5970e060100718e999b76d2aa355`）。
はじめは「名前==版」の文字列で並べたため `markdown`／`markdown-it-py` と `tensorboard`／`tensorboard-data-server` の順だけが違った（中身は同じ）。andrew と同じく名前で並べて作り直した。

**元に戻すとき**: `cp -p pyvenv.cfg.before_s2fix pyvenv.cfg`、`ln -sfn /home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11 bin/python`。今は直したまま。

### R2 重ねの BODY（22:47 JST）

    OV=/home/ubuntu/slocal2/s2fix-bengio-body
    mkdir -p $OV/third_party
    ln -s /home/ubuntu/slocal2/m2/data $OV/data
    ln -s /home/ubuntu/slocal2/m2/experiments $OV/experiments
    ln -s /home/ubuntu/slocal2/m2/.venv $OV/.venv
    ln -s /home/ubuntu/slocal2/m2/.venv-relation-detr $OV/.venv-relation-detr
    rsync -a --exclude=/.git --exclude=/checkpoints --exclude=/experiments --exclude=/third_party --exclude=/per_class_coco_map \
      --exclude=/data --exclude=/outputs --exclude=/work_dirs --exclude=__pycache__ \
      andrew:/home/ubuntu/slocal2/m2/third_party/Relation-DETR/ $OV/third_party/Relation-DETR/      # rc=0

除外は照合の道具（`input_digest.py` の `SKIP_TOP` は最上位だけ）に合わせて最上位に限った。`__pycache__` はどの深さでも除いた。
写しは 2.2 MB、ソース（.py .cu .cuh .cpp .h）142 本。写した後は中身を変えていない。bengio の main の `third_party/Relation-DETR` は変えていない。

### R3 正式な S4（22:48 JST）

    $OV/.venv-relation-detr/bin/python $WT/scripts/stage2pilot/input_digest.py --body $OV --out $WT/experiments/analysis/stage2_pilot_fix/bengio/input_digest_bengio.json   # rc=0

標準出力は `input_digest_bengio_r3.log`（前回の試みの `input_digest_bengio.log` は残してある）。

andrew の `input_digest_andrew.json` と、`relation_detr.commit`・`relation_detr.uncommitted`・`torch.gpus` を除く **167 個の値がすべて一致**:
信号 8 本、検出塔の重み、注釈 2 本、画像の列（train 9,657 `c5c27b85…`、val 1,515 `025c644b…`、欠け 0）、
Relation-DETR `source_files` 142・`source_tree_sha256` `2f08e5213cb5c377c576172b0d39964f46fb6afb80532ce11f8bad7437f1e393`・ファイルごとの 142 個・MS-Deform-Attn `307450b3…`、
torch 2.1.2+cu118・CUDA 11.8・cuDNN 8700。比べない値: commit ""（andrew `b485955c…`）、uncommitted 0（andrew 42）、gpus（andrew `[]`、bengio A6000 × 2）。

### R4 拡張の読み込み（22:48〜22:50 JST）

1 回目（§6 の命令のとおり、venv を有効化せずに）: **失敗**。`Ninja is required to load C++ extensions` → `ms_deform_attn_ext False`（`r4_ext_load_bengio.log`）。
`ninja` は `.venv-relation-detr/bin/ninja` にだけあり、bengio のシステムの PATH には無い。

2 回目: `run_pd_fix.sh` と同じく `source $OV/.venv-relation-detr/bin/activate` してから同じ命令。
`~/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention` に nvcc でビルドし、**`ms_deform_attn_ext True`**（`r4_ext_load_bengio_activated.log`、rc=0）。
本番と試走は `run_pd_fix.sh` が venv を有効化するので、この違いは効かない。S6 の `pd_eval.py` も venv を有効化して回す。

### GPU の負荷を止める（22:51 JST）

止める直前に `ps -o pid,ppid,lstart,cmd -p 296512 296513` で S1 と同じもの（`python3 /tmp/gpu_dummy_load.py 0`／`1`、親 296510、起動 22:19:11 JST）であることを確かめ、
利用者の指示どおり `kill 296512 296513`（22:51:06 JST、rc=0）。直後: 両 PID と親 296510 は消え、GPU 0 39 MiB・0%、GPU 1 20 MiB・0%、compute プロセス 0 件。

### R5 塔単独の再現（22:51〜23:01 JST）

    cd $WT && source $OV/.venv-relation-detr/bin/activate && CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego \
      EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A CUDA_VISIBLE_DEVICES=0 \
      python scripts/stage2pilot/pd_eval.py --cfg plain --det-ckpt $OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth \
      --save-preds $FIX/identity/plain_val_preds_bengio.json.gz --out $WT/experiments/analysis/stage2_pilot_fix/bengio/pd_plain_bengio.json

- 1 回目（22:51〜22:54）: **rc=1**。評価は終わったが、`det_metrics.read_groups` が `context/conventions.md` を `read_text()` で読むところで
  `UnicodeDecodeError: 'ascii' codec can't decode byte 0xe2 in position 14`（`pd_plain_bengio_try1_failed.log`）。出力の json と予測は書かれていない。
  この回は bengio で初めて backbone の重み `resnet50-11ad3fa6.pth` を `~/.cache/torch/hub/checkpoints/` へ落とした回だった
- 調べたこと（scratchpad の調査用スクリプト。記録には使わない）: シェルは `LANG=C.UTF-8`。両 venv の python とも `locale.getencoding()` は UTF-8。
  pd_eval と同じ順（import、loader、build_model、`util.utils`、load_checkpoint、全件の評価）の各段で UTF-8 のまま。全件の評価の mAP は 0.7273450248398429。
  `read_groups()` を単独で呼ぶと読める。Python のコードと依存に `setlocale` を呼ぶ箇所は無い。**原因は確かめられていない**（初回のダウンロードとの関わりは推測）
- 2 回目（同じ命令、22:59〜23:01）: **rc=0**、`eval_detection_mAP` **0.7273450248398429**（andrew と差 0.0、許容差 0.005）、AP50 0.851807431425236、
  標的群 AP 0.7950748008550897、陰性対照群 AP 0.6726631817581498、1,515 枚、界面以外の重みの要約値 `4fed85166852…`（andrew の `pd_plain.json` と一致）

### S6 恒等性（23:02〜23:08 JST）

R5 と同じ環境で `pd_eval.py` を回した（GPU 0・1 に 2 本ずつ）。基準は R5 の予測 `$FIX/identity/plain_val_preds_bengio.json.gz`。
出力は `experiments/analysis/stage2_pilot_fix/bengio/` の各 json と log。

| | 構成 | 信号（val） | mAP | score 差の最大 | 枠の差の最大（px） | ラベル不一致 |
|---|---|---|---|---|---|---|
| 1 `pd_plain_bengio` | plain | なし | 0.7273450248398429 | — | — | — |
| 2 `pd_query_d9_gt_identity_bengio` | pd_query_d9 | P-GT_val | 0.7273450248398429 | 0.0 | 0.0 | 0 |
| 3 `pd_query_d9_shuffle_identity_bengio` | pd_query_d9 | 入れ替えた P0_val | 0.7273450248398429 | 0.0 | 0.0 | 0 |
| 4 `pd_query_d18_gtpred_noCF_identity_bengio` | pd_query_d18 | gtpred_noCF_val | 0.7273450248398429 | 0.0 | 0.0 | 0 |
| 5 `pd_query_d9_shuffle_positive_bengio`（`--perturb`） | pd_query_d9 | 入れ替えた P0_val | 0.7271372958311481 | 0.34662654995918274 | 1932.93 | 267,542 |

2〜4 は差 0（恒等性 pass）。5 は出力が変わる（陽性対照 pass）。5 の値は andrew の `identity/pd_query_d9_shuffle_positive.json` と全桁一致
（mAP 0.7271372958311481、score 差 0.34662654995918274、枠 1932.9268646240234、ラベル不一致 267,542）。界面の学習対象は d9 2,560、d18 4,864。
どの回も検出塔の重みで足りないのは界面（`phase*`）だけ。

### S7 試走（23:08:40〜23:08:55 JST）

    cd $WT && S2FIX_BODY=/home/ubuntu/slocal2/s2fix-bengio-body S2FIX_CODE=/home/ubuntu/slocal2/m2-s2fix-bengio CUDA_VISIBLE_DEVICES=0 \
      bash scripts/stage2pilot/run_pd_fix.sh P3 gt smoke > $FIX/queues/bengio_P3_gt_smoke.out 2>&1      # rc=0

- run: `$WT/experiments/phase1/stage2fix_pd_P3_gt_ep4_seed42_smoke/`。`env_check.txt` `[env] torch 2.1.2+cu118 cuda True ms_deform_attn_ext True`、`server.txt` `bengio`、`exit_code.txt` 0
- `train.log`: `total_trainable=1684883`、`miss_ctx(tr/va)=0/0`、`[t1b][smoke] phase_grad=True init_mAP=0.8917 => PASS`
- `finalize.log`: `AP=0.891661 target=0.891661 control=None result_epoch=0 diff=0.00e+00`
- `stage2fix_metrics.json`: 学習前 `init` 0.8916611661166115、`result_selection` final_epoch、`frozen_unchanged` true

| | 学習前 mAP（val 20 枚） | 後処理の AP |
|---|---|---|
| andrew（worktree から、21:54 JST） | 0.8916612 | 0.891661 |
| bengio（23:08 JST） | 0.8916611661166115 | 0.891661 |

main の作業場所の `experiments/` に bengio の run は増えていない（`experiments/phase1` の一覧は 22:47 と S7 の後で同じ）。
目印より新しいのは `stage2fix_pd_P3_shuffle_ep4_seed42/{predictions/val_inj_ep-1.json.gz,logs/eval_meta_val.json}`（22:49:44 JST）だけで、
これは andrew の本番の `P3 shuffle`（22:44 JST 起動）の学習前の評価が同期で届いたもの（フォルダは 22:45 JST からあった。その時刻に bengio は R4 で experiments に書いていない）。
main の分岐は `feat/proposal-gate-brief` のまま。

### S8 本番の 2 本の起動（23:10 JST）

§7 のとおり GPU 1 枚に 1 本。`P3 gt` と `P3 shuffle` は起こしていない（andrew で回っている）。起動の前に GPU 0 39 MiB・GPU 1 20 MiB、compute プロセス 0 件。

    cd $WT && S2FIX_BODY=/home/ubuntu/slocal2/s2fix-bengio-body S2FIX_CODE=/home/ubuntu/slocal2/m2-s2fix-bengio CUDA_VISIBLE_DEVICES=0 \
      nohup bash scripts/stage2pilot/run_pd_fix.sh P3 pred_CF > $FIX/queues/bengio_P3_pred_CF.out 2>&1 < /dev/null &
    （約 20 秒後）同じく CUDA_VISIBLE_DEVICES=1 で P3 gtpred_CF > $FIX/queues/bengio_P3_gtpred_CF.out

| GPU | run | start.txt | 学習対象 | env_check |
|---|---|---|---|---|
| 0 | `stage2fix_pd_P3_pred_CF_ep4_seed42` | 2026-10-19 14:10:22 UTC（23:10:22 JST） | 1,684,883（界面 2,560） | `ms_deform_attn_ext True` |
| 1 | `stage2fix_pd_P3_gtpred_CF_ep4_seed42` | 2026-10-19 14:10:50 UTC（23:10:50 JST） | 1,687,187（界面 4,864） | `ms_deform_attn_ext True` |

両方とも `miss_ctx(tr/va)=0/0`。

### S9 見守り

scratchpad の見守り役（10 分ごと。`train.log` の `Traceback`・`CUDA out of memory`・`not finite`、15 分を超える停止、`exit_code.txt`、プロセスの有無）が
`$FIX/queues/bengio_watch.log` に記録する。異常語は、andrew の完了した run（`stage2fix_pd_P1-W2_shuffle_ep4_seed42/train.log`）で 0 件であることを確かめてから使った。

見守りの記録（`$FIX/queues/bengio_watch.log`）: 23:11〜00:51 JST の 11 回で、異常語 0、15 分を超える停止 0、プロセスの消失 0。23:44〜00:54 JST は利用者の指示で 10 分ごとに状況を報告した。
速さは 1 本あたり 3.6〜3.8 it/s（1 epoch 約 21 分）。GPU の使用率は瞬間値で 23〜97% と揺れ、CPU は 7〜8 割が空いていた。
読み込みの worker・batch・GPU の分け方を変えると増強の乱数の並びやスケジュールが andrew の腕と揃わなくなるため、早める手は取っていない。

## S10 確認と commit（00:5x JST）

確認は scratchpad の読むだけの道具で行った（各 run の `t1b_result.json`・`stage2fix_metrics.json`・`env_check.txt`・`server.txt`・`exit_code.txt`・`start.txt`・`end.txt` と、git の外の成果物の sha256）。

### stage2fix_pd_P3_pred_CF_ep4_seed42

確認: rc=0 OK、result_selection=final_epoch OK、best_epoch=final_epoch=3 OK、mAP=final_mAP OK、init=0.7273450248398429 OK、frozen_unchanged OK、ms_deform_attn_ext True OK、server=bengio OK、diff_vs_eval=0 OK

- overall mAP 0.7257542556839381、標的群 AP 0.7938630711330552、陰性対照群 AP 0.6729980900055019（欠け: 標的群 []、陰性対照群 []）、AP50 0.8503897868282081
- 学習前 0.7273450248398429（標的群 0.7950748008550897、陰性対照群 0.6726631817581498）
- epoch ごとの val mAP: {'-1': 0.7273450248398429, '0': 0.726206312298229, '1': 0.7239282105716128, '2': 0.7247228837729589, '3': 0.7257542556839381}
- 動画ごとの mAP: {'09': 0.7025632861011694, '10': 0.640447182975101}
- 所要: 23:10:22〜00:52:42 JST（1.71 時間）、frozen_digest 972cb1bd83f7e975…

### stage2fix_pd_P3_gtpred_CF_ep4_seed42

確認: rc=0 OK、result_selection=final_epoch OK、best_epoch=final_epoch=3 OK、mAP=final_mAP OK、init=0.7273450248398429 OK、frozen_unchanged OK、ms_deform_attn_ext True OK、server=bengio OK、diff_vs_eval=0 OK

- overall mAP 0.7254988345581337、標的群 AP 0.7910986571916249、陰性対照群 AP 0.675991920878969（欠け: 標的群 []、陰性対照群 []）、AP50 0.8489892204405158
- 学習前 0.7273450248398429（標的群 0.7950748008550897、陰性対照群 0.6726631817581498）
- epoch ごとの val mAP: {'-1': 0.7273450248398429, '0': 0.728307338278499, '1': 0.726785299835692, '2': 0.7254774067395594, '3': 0.7254988345581337}
- 動画ごとの mAP: {'09': 0.6995826130530416, '10': 0.6419597477348019}
- 所要: 23:10:50〜00:51:26 JST（1.68 時間）、frozen_digest 972cb1bd83f7e975…

### git の外の成果物の sha256

| ファイル | バイト | sha256 |
|---|---|---|
| `/home/ubuntu/slocal2/m2-s2fix-bengio/experiments/phase1/stage2fix_pd_P3_pred_CF_ep4_seed42/predictions/val_inj_best.json.gz` | 11,875,248 | `a327023870680cfebe4544faae2da0ab901bec74b39f395230673dedec0f9958` |
| `/home/ubuntu/slocal2/m2-s2fix-bengio/experiments/phase1/stage2fix_pd_P3_pred_CF_ep4_seed42/predictions/val_inj_ep-1.json.gz` | 13,032,761 | `0ac1aae518f8e69d1f8dc0d5f315c1a8285051d3782b73b1d358e6094dcaba19` |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/pd_ckpt/stage2fix_pd_P3_pred_CF_ep4_seed42/best_t1b.pth` | 6,749,978 | `ead3312783a95454ab98b59f27b41de0db7a93452a17b5a429cf2b5786c0df0a` |
| `/home/ubuntu/slocal2/m2-s2fix-bengio/experiments/phase1/stage2fix_pd_P3_gtpred_CF_ep4_seed42/predictions/val_inj_best.json.gz` | 12,528,234 | `e0f1a8da346f7c6761550ddfd4d1bb10c551258df1abafff063e83ba61a6540e` |
| `/home/ubuntu/slocal2/m2-s2fix-bengio/experiments/phase1/stage2fix_pd_P3_gtpred_CF_ep4_seed42/predictions/val_inj_ep-1.json.gz` | 13,032,761 | `0ac1aae518f8e69d1f8dc0d5f315c1a8285051d3782b73b1d358e6094dcaba19` |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/pd_ckpt/stage2fix_pd_P3_gtpred_CF_ep4_seed42/best_t1b.pth` | 6,759,194 | `518f9882f4017c016d8700f07f83d069a9516d65fb6e2f91c686639a6d4100f5` |

### 要約（val、4 epoch 目の状態）

| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP |
|---|---|---|---|
| pred_CF | 0.725754 | 0.793863 | 0.672998 |
| gtpred_CF | 0.725499 | 0.791099 | 0.675992 |


2 本とも上の確認は全項目 OK。学習前の予測 `val_inj_ep-1.json.gz` は 2 本で sha256 が同じ（零初期化の界面で学習前の出力が信号によらないことと合う）。
凍結部の要約値 `972cb1bd83f7e975…` は andrew の W2 の run（`stage2fix_pd_P1-W2_shuffle_ep4_seed42`）と同じ。

試走の成果物（git の外）: `$FIX/pd_ckpt/stage2fix_pd_P3_gt_ep4_seed42_smoke/`、`$WT/experiments/phase1/stage2fix_pd_P3_gt_ep4_seed42_smoke/predictions/`。

### 残してあるもの（戻すかどうかは利用者が決める）

- `.venv-relation-detr` は直したまま（python → uv の 3.11.16。戻すときは `pyvenv.cfg.before_s2fix` と元のリンク先 `/home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11`）
- 重ねの BODY `/home/ubuntu/slocal2/s2fix-bengio-body`（Relation-DETR の写し 2.2 MB と symlink 4 本）
- worktree `/home/ubuntu/slocal2/m2-s2fix-bengio`、拡張のビルド `~/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention`、backbone の重み `~/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth`
- 予測と重み（上の表）は bengio に置いたまま
- GPU のダミー負荷（`/tmp/gpu_dummy_load.py`）は 22:51 JST に止めたまま、起こし直していない
