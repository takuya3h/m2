# 引き渡し: bengio で P3 の 4 本を回す（契約 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle の一部）

andrew の実行者（Claude Code）から bengio の実行者への依頼。**非公式の測定**で、関門の判定にも設計の判断にも使わない。
利用者が 2026-10-19 21:4x JST に、P3 の 4 本を別ホスト bengio で回すこと（逸脱）を承認した（`spec.yaml` の `meta.amendments` の 2 件目）。
説明は日本語、時刻は JST。数値を捏造しない。測っていない値は UNKNOWN と書く。

## 0. 役割の分担（決まっていること）

| 項目 | 決定 |
|---|---|
| bengio が回すもの | PD（工程から検出）の **P3 の 4 本**: 正解 `gt`、予測-CF `pred_CF`、正解予測-CF `gtpred_CF`、入れ替え `shuffle`。それ以外の run は足さない |
| andrew に残るもの | P3 の空・予測-noCF（andrew で学習中）、ほかの PD、集計・報告・PR・送出のすべて |
| 契約の手順 | bengio では `/task` を使わない。`make task-start`・`task-release`・`task-report`・PR の起票はしない（andrew が行う） |
| 分岐 | bengio の main の作業場所（`/home/ubuntu/slocal2/m2`）の分岐と作業ツリーには**触れない**。別の場所に **git worktree** を作り、そこで新しい分岐 `feat/stage2-pilot-fix-epoch4-shuffle-bengio` を使う |
| 抑止の目印 | 置かない。`m2-sync.sh` は `$M2DIR` に cd して今の分岐でだけ動くので、worktree には触れない（S1 で確かめる） |
| push | `feat/stage2-pilot-fix-epoch4-shuffle-bengio` だけを push する。`feat/stage2-pilot-fix-epoch4-shuffle`（andrew の分岐）には push しない。PR は作らない |
| 結果のくっつけ方 | andrew が `origin/feat/stage2-pilot-fix-epoch4-shuffle-bengio` を自分の分岐へ `git merge --no-ff` する。そのため bengio の commit は**新しいファイルだけ**を足し、既存の追跡ファイルを一つも変えない（衝突させない） |
| git の外の成果物 | 予測（`predictions/`）と重み（`FIX/pd_ckpt/`）は bengio に残す。sha256 の一覧を `audit_bengio.md` に書く。worktree は消さない |
| 利用者への報告 | (a) 準備と検査の終わり、(b) 4 本の起動、(c) 4 本の終わりと push の 3 回 |

## 1. 禁止事項

1. test の動画（04、05、07）を信号の作成・学習・評価に通さない（注釈は折り A の train と val だけを使う）
2. 前回の置き場 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/` と、前回の run（`experiments/phase1/stage2pilot_*`）・前回の集計（`experiments/analysis/stage2_pilot_folda/`）に書き込まない。読むだけ
3. 凍結源、既存の checkpoint（検出塔）、`data/raw`、`data/external`、注釈を変えない
4. **efros と ilya に接続しない**。bengio の他のプロセスを止めない（本件以外の compute プロセスが居れば、止めずに利用者に諮る）
5. bengio の main の作業場所で分岐を切り替えない・commit しない・ファイルを足さない（同期 syncthing が `experiments/` の一部と `logs/` を全台へ配るため）
6. 既存の追跡ファイルを変えない。新しいファイルだけを足す。ファイルを消さない
7. 外部への送信をしない（台帳への送り返しは andrew が `make task-report` で行う）。秘密の値を出力しない

## 2. 前提（bengio の環境）

| もの | 置き場（bengio） | 確かめ方 |
|---|---|---|
| repo（main の作業場所） | `/home/ubuntu/slocal2/m2`（`S2FIX_BODY`）。**違う経路なら止めて諮る**（信号の置き場が絶対経路で書かれている） | `ls` |
| 画像 | `/home/ubuntu/slocal2/m2/data/raw/ego` | S4 の要約値 |
| 折り A の注釈 | `/home/ubuntu/slocal2/m2/data/annotations/egosurgery_tool_folds/A/instances_{train,val}.json`（同期で配られている） | S4 |
| 検出塔の重み | `/home/ubuntu/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth`（同期で配られている） | sha256 `30d199b15201cf3c03954852d8acc6fb58fe5349baef2fd200e877237ff682c4` |
| 検出器の仮想環境 | `/home/ubuntu/slocal2/m2/.venv-relation-detr`（torch 2.1.2+cu118、MS-Deform-Attn は nvcc で読み込み時にビルド） | `env_check.txt` に `ms_deform_attn_ext True` |
| 本体の仮想環境 | `/home/ubuntu/slocal2/m2/.venv`（後処理が使う） | `ls` |
| Relation-DETR | `/home/ubuntu/slocal2/m2/third_party/Relation-DETR`。**未 commit の変更を含めて andrew と同じ中身**であること（増強 `transforms/presets.py`、最適化の群 `optimizer/param_dict.py` などが学習に効く） | S4 の `source_tree_sha256` |
| GPU | RTX A6000 × 2、本件以外の compute プロセス 0 件 | S1 |

## 3. 送る信号（8 本、計 3.5 MB）

bengio の**同じ絶対経路**に置く。andrew から写す（bengio から andrew へ ssh で届くなら `rsync -a andrew:<経路> <経路>`。届かなければ利用者に運んでもらう）。
置いた後に sha256 を照合し、一つでも違えば止める。

| 経路 | sha256 | 使う run |
|---|---|---|
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P-GT_train.npz` | 6cb729a9724efdf51aa8d92e239d7755aa6d564fe4edd2ce1ba76b7e3cf79699 | gt（train）、試走 |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P-GT_val.npz` | S4 の `input_digest_andrew.json` の値 | gt（val）、試走、恒等性 |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P0_val.npz` | 同上 | pred_CF（val） |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/cf/P0_train.npz` | e7b23991bce769abf6de804b59a9fd7813cca2f969d1655b9d2be0ef8e631cb8 | pred_CF（train） |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/arms/PD/gtpred_CF_train.npz` | 6b0e99369b350caf4677f0861a0b93d7604d00ef0b81aeafaad0e7be30b19ac9 | gtpred_CF（train） |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/arms/PD/gtpred_noCF_val.npz` | 5fe0a89c8402f455bbc0a3d85d7f00041f888e26fc334a62ab1c416ea94a5b8e | gtpred_CF（val）、恒等性 |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/P0_train.npz` | S4 の値 | shuffle（train） |
| `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/P0_val.npz` | S4 の値 | shuffle（val）、恒等性 |

全 8 本の全桁の sha256 は `experiments/analysis/stage2_pilot_fix/bengio/input_digest_andrew.json` の `signals` にある（この分岐に commit 済み）。

## 4. 手順

**命令は単独で完結する形で書く（命令ごとにシェルが変わる実装系がある）。履歴を読む git は `git --no-pager`。** 命令と出力は `audit_bengio.md` に残す。
以下 `WT=/home/ubuntu/slocal2/m2-s2fix-bengio`、`FIX=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle`。

### S1 開始状態（読むだけ）

- `hostname`、時刻（JST）、`nvidia-smi`（GPU 2 枚、compute プロセス 0 件）、`df -B1 /home/ubuntu/slocal2`、`free -b`
- compute プロセスの列挙: `/proc/PID/exe` の解決で python 系を数える（andrew の道具 `experiments/analysis/stage2_pilot_folda/tools/proc_enum.py --summary` を worktree から読んで実行してよい）
- main の作業場所の分岐と状態（`git -C /home/ubuntu/slocal2/m2 branch --show-current`、`status --porcelain | wc -l`）を記録する。**変えない**
- `grep -n 'cd "\$M2DIR"' ~/bin/m2-sync.sh` と `grep -c worktree ~/bin/m2-sync.sh`（0 であること。worktree に触れないことの確認）

### S2 worktree と分岐

    git -C /home/ubuntu/slocal2/m2 fetch origin feat/stage2-pilot-fix-epoch4-shuffle
    git -C /home/ubuntu/slocal2/m2 worktree add -b feat/stage2-pilot-fix-epoch4-shuffle-bengio /home/ubuntu/slocal2/m2-s2fix-bengio origin/feat/stage2-pilot-fix-epoch4-shuffle

`git -C $WT rev-parse HEAD` を記録する（この文書を含む commit か、それ以降）。main の作業場所の分岐が変わっていないことを確かめる。

### S3 信号を置く

§3 の 8 本を同じ絶対経路へ置き、`sha256sum` で照合する。`$FIX/pd_ckpt/` と `$FIX/queues/` は無ければ作ってよい（本契約の置き場）。

### S4 入力の照合（andrew と同じ入力か）

    /home/ubuntu/slocal2/m2/.venv-relation-detr/bin/python $WT/scripts/stage2pilot/input_digest.py --body /home/ubuntu/slocal2/m2 --out $WT/experiments/analysis/stage2_pilot_fix/bengio/input_digest_bengio.json

andrew の `$WT/experiments/analysis/stage2_pilot_fix/bengio/input_digest_andrew.json` と比べる。**`torch.gpus` 以外のすべての値が一致**すること
（信号 8 本、検出塔の重み、注釈 2 本、画像の列の要約値と枚数〔train 9,657、val 1,515、欠け 0〕、Relation-DETR の commit・未 commit の件数〔42〕・
MS-Deform-Attn のソース・`source_tree_sha256`〔2f08e5213cb5c377c576172b0d39964f46fb6afb80532ce11f8bad7437f1e393〕、torch 2.1.2+cu118・CUDA 11.8・cuDNN 8700）。
**一つでも違えば止める。** Relation-DETR が違うときは `source_file_sha256` をファイルごとに比べて違うファイルの名前を列挙し、利用者に諮る（直さない）。

### S5 塔単独の再現（G2 と同じ）

検出塔単独の val の overall mAP が andrew の値 **0.7273450248398429** と一致するか（許容差 0.005。andrew では差 0.0）。

    bash $WT/experiments/analysis/stage2_pilot_folda/repro/eval_dtower_val.sh /home/ubuntu/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth $WT/experiments/analysis/stage2_pilot_fix/bengio/dtower_val_seed42_bengio.json 29771

（この台本は GPU 2 枚・`NCCL_P2P_DISABLE=1`、main の作業場所の `scripts/eval_relation_detr_map.py` を使う。出力は worktree。1〜2 分）。超えたら止めて諮る。

### S6 恒等性（零初期化の界面で、学習前の出力が塔単独と一致するか）

worktree の `scripts/stage2pilot/pd_eval.py` を、`.venv-relation-detr` で、環境 `CUDA_HOME=/usr/local/cuda EGO_BODY=/home/ubuntu/slocal2/m2
EGO_ROOT=/home/ubuntu/slocal2/m2/data/raw/ego EGO_ANN_DIR=/home/ubuntu/slocal2/m2/data/annotations/egosurgery_tool_folds/A` と
`--det-ckpt <検出塔の重み>` を付けて回す（`--det-ckpt` を省くと worktree の中の経路を探して失敗する）。出力は `$WT/experiments/analysis/stage2_pilot_fix/bengio/`。

1. `--cfg plain --save-preds $FIX/identity/plain_val_preds_bengio.json.gz --out .../pd_plain_bengio.json`（塔単独の基準。mAP 0.7273450）
2. `--cfg configs/stage2pilot/pd_query_d9.py --signal-val <P-GT_val.npz> --ref-preds <1 の予測>` → 差 0.0（score・枠・ラベル）
3. `--cfg configs/stage2pilot/pd_query_d9.py --signal-val <入れ替えた P0_val.npz> --ref-preds <1>` → 差 0.0
4. `--cfg configs/stage2pilot/pd_query_d18.py --signal-val <gtpred_noCF_val.npz> --ref-preds <1>` → 差 0.0
5. 陽性対照: 3 に `--perturb` を付ける → 出力が変わる（andrew では mAP 0.7271373、score 差の最大 0.3466）

差が 0 でなければ止めて諮る。

### S7 試走（端から端まで動くこと）

    cd $WT && S2FIX_CODE=$WT CUDA_VISIBLE_DEVICES=0 bash scripts/stage2pilot/run_pd_fix.sh P3 gt smoke

rc=0、`$WT/experiments/phase1/stage2fix_pd_P3_gt_ep4_seed42_smoke/` に run ができ、`finalize.log` が通り、`env_check.txt` が `ms_deform_attn_ext True`。
andrew の同じ試走（worktree から、21:54 JST）は学習前 mAP 0.8916612（val 20 枚）、後処理の AP 0.891661 だった。並べて記録する。
**main の作業場所の `experiments/` に何も増えていないこと**を確かめる。

### S8 本番の 4 本を起動する（GPU 1 枚に 2 本ずつ）

| GPU | run |
|---|---|
| 0 | `P3 gt`、`P3 pred_CF` |
| 1 | `P3 gtpred_CF`、`P3 shuffle` |

それぞれ 20 秒ずつずらして、裏で起こす（例）:

    cd /home/ubuntu/slocal2/m2-s2fix-bengio && S2FIX_CODE=/home/ubuntu/slocal2/m2-s2fix-bengio CUDA_VISIBLE_DEVICES=0 nohup bash scripts/stage2pilot/run_pd_fix.sh P3 gt > /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/queues/bengio_P3_gt.out 2>&1 &

**1 枚に 3 本以上載せない**（andrew の実測で合計の速さが伸びなかった。GPU 0 で 3%、GPU 1 で 0%）。

`run_pd_fix.sh` が行う設定（andrew の P3 と同じ。変えない）:

| 項目 | 値 |
|---|---|
| 受け取り手 | 検出塔 D*-COCO 折り A seed 42（上の重み）。構成 `configs/stage2pilot/pd_query_d9.py`（gtpred_CF は `pd_query_d18.py`、信号 18 次元） |
| 界面と学習範囲 | query 条件付け、`--trainable w2`（界面と decoder の最終層とそのクラス・枠のヘッド）、学習対象 1,684,883 |
| 長さと選び方 | `--epochs 4 --fixed-epochs`（4 epoch を止めずに学び、4 epoch 目〔epoch 3〕の状態を結果にする。学習率は一定） |
| 数値精度 | `--amp bf16`（学習の順伝播）。評価は単精度 |
| seed | 42 |
| 信号（train / val） | gt: P-GT_train / P-GT_val、pred_CF: 交差適合版 P0_train / P0_val、gtpred_CF: gtpred_CF_train / gtpred_noCF_val、shuffle: 入れ替えた P0_train / P0_val |
| 保存 | `--save-trainable-only --ckpt-dir $FIX/pd_ckpt/<run>`、run は `$WT/experiments/phase1/stage2fix_pd_P3_<腕>_ep4_seed42/` |
| 後処理 | `pd_fix_finalize.py`（結果が epoch 3 の状態であることを確かめ、群の AP・動画ごとの mAP・notes.md を書く） |

### S9 見守り（10 分ごと）

学習ログ（各 run の `train.log`）に `Traceback`・`CUDA out of memory`・`not finite` が無いか、step の行が 15 分以上止まっていないか、`exit_code.txt`。
異常があれば**その腕を止めて記録し、利用者に諮る**（ほかの腕は続ける）。所要の見込み: 1 本約 2.4 時間（2 本ずつで 2.6 it/s 前後、1 epoch 4,809 step、評価 5 回）。

### S10 終わったら

4 本とも rc=0 になったら、run ごとに確かめて `audit_bengio.md` に書く:

- `t1b_result.json` の `result_selection` が `final_epoch`、`best_epoch` = `final_epoch` = 3、`mAP` = `final_mAP`
- `stage2fix_metrics.json` の `init`（学習前の overall mAP）が **0.7273450248398429**、`frozen_unchanged` が true
- `env_check.txt` の `ms_deform_attn_ext True`、`server.txt` が bengio
- epoch ごとの val mAP（`notes.md`）、1 本の所要（`start.txt`・`end.txt`）
- git の外の成果物の sha256（`predictions/*.json.gz`、`$FIX/pd_ckpt/<run>/best_t1b.pth`）

commit するもの（**新しいファイルだけ**。既存の追跡ファイルは変えない）:

- `experiments/phase1/stage2fix_pd_P3_{gt,pred_CF,gtpred_CF,shuffle}_ep4_seed42/` と試走 `stage2fix_pd_P3_gt_ep4_seed42_smoke/`（git が追うファイルだけが入る）
- `experiments/analysis/stage2_pilot_fix/bengio/`（入力の照合、再現、恒等性の json と log）
- `tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/audit_bengio.md`

commit の文の末尾には bengio のセッションの帰属の行を付ける。`git -C $WT push -u origin feat/stage2-pilot-fix-epoch4-shuffle-bengio`。
**`git -C $WT diff --stat origin/feat/stage2-pilot-fix-epoch4-shuffle...HEAD` が上の新しいファイルだけ**であることを確かめてから push する。
最後に、利用者へ分岐の名前・先頭の commit・4 本の結果（overall mAP・標的群 AP・陰性対照群 AP）を報告する。worktree は消さない。

## 5. andrew が行うこと（参考）

- bengio の push の後、`origin/feat/stage2-pilot-fix-epoch4-shuffle-bengio` を fetch し、新しいファイルだけであることを確かめて `git merge --no-ff` で統合する
- `aggregate_fix.py` で P3 の表を作る。P3 の空・予測-noCF は andrew、他の 4 本は bengio で回ったこと（`server.txt`）を報告の限界と逸脱に書く
- `test_audit_fix.py`・`make forbidden-check`・報告・PR・`make task-report`・`make task-release`
