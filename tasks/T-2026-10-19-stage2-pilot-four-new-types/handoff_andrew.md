# 引き渡し: andrew で decoder-xattn の 6 本を回す（契約 T-2026-10-19-stage2-pilot-four-new-types の一部）

bengio の実行者（Claude Code、主）から andrew の実行者（副）への依頼。**非公式の測定**で、関門の判定にも設計の判断にも使わない。
利用者の決定（2026-10-20 01:44 JST、`spec.yaml` の `meta.amendments` の 8 件目）で、工程から検出の **decoder-xattn（DX）の 6 本**を andrew で回す。
SPEC Task E-4 の形を主と副を入れ替えて使う。説明は日本語、時刻は JST。数値を捏造しない。測っていない値は UNKNOWN と書く。

## 0. 役割の分担（決まっていること）

| 項目 | 決定 |
|---|---|
| andrew が回すもの | PD の **decoder-xattn（DX）の 6 本**: 空 `empty`、予測-noCF `pred_noCF`、正解 `gt`、予測-CF `pred_CF`、正解予測-CF `gtpred_CF`、入れ替え `shuffle`。それ以外の run は足さない（試走 `DX gt smoke` は腕ではない） |
| bengio に残るもの | extra-queries の 6 本、検出から工程の 18 本、K3 の GRU、殺し実験、集計・報告・PR・送出のすべて |
| 契約の手順 | andrew では `/task`・`make task-start`・`make task-release`・`make task-report` を使わない。PR を作らない |
| 分岐 | andrew の main の作業場所（`/home/ubuntu/slocal2/m2`）の分岐と作業ツリーには**触れない**。別の場所に git worktree を作り、新しい分岐 `feat/stage2-pilot-four-new-types-andrew`（起点はこの文書を含む commit）を使う |
| 抑止の目印 | 置かない。`m2-sync.sh` は `$M2DIR` に cd して今の分岐でだけ動くので worktree には触れない（S1 で確かめる） |
| push | `feat/stage2-pilot-four-new-types-andrew` だけを push する。`feat/stage2-pilot-four-new-types`（bengio の分岐）には push しない |
| 結果のくっつけ方 | bengio が `origin/feat/stage2-pilot-four-new-types-andrew` を自分の分岐へ `git merge --no-ff` する。andrew の commit は**新しいファイルだけ**を足し、既存の追跡ファイルを一つも変えない |
| git の外の成果物 | 予測（run の `predictions/`）と界面の重み（`$FOUR/pd_ckpt/`）は andrew に残す。sha256 の一覧を `audit_andrew.md` に書く。worktree は消さない |
| 利用者への報告 | (a) 準備と検査の終わり（S1〜S7）、(b) 6 本の起動、(c) 6 本の終わりと push の 3 回 |
| 監査 | 命令と出力は `tasks/T-2026-10-19-stage2-pilot-four-new-types/audit_andrew.md`（新しいファイル）に書く |

## 1. 禁止事項

1. test の動画（04、05、07）を信号の作成・学習・評価に通さない（注釈は折り A の train と val だけを使う）
2. 前回と直しの契約の保存先（`/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/`、`.../T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/`）、
   前回と直しの run（`experiments/phase1/stage2pilot_*`、`stage2fix_*`）・集計（`experiments/analysis/stage2_pilot_folda/`、`stage2_pilot_fix/`）に書き込まない。読むだけ
3. 凍結源、既存の checkpoint（検出塔）、`data/raw`、`data/external`、注釈、`third_party/` を変えない
4. **efros と ilya に接続しない**。andrew の他のプロセスを止めない（本件以外の compute プロセスが居れば、止めずに利用者に諮る）
5. andrew の main の作業場所で分岐を切り替えない・commit しない・ファイルを足さない
6. 既存の追跡ファイルを変えない。新しいファイルだけを足す。ファイルを消さない
7. 外部への送信をしない（台帳への送り返しは bengio が `make task-report` で行う）。秘密の値を出力しない
8. 使う GPU は andrew の 2 枚だけ。1 枚に載せるのは 3 本まで（直しの契約では 3 本目の伸びが 3% 以下だった。本数は実測で決めてよい）

## 2. 前提（andrew の環境）

以下 `A=/home/ubuntu/slocal2/m2`（andrew の main の作業場所。データ・仮想環境・Relation-DETR・検出塔の重みを**読むだけ**）、
`WT=/home/ubuntu/slocal2/m2-four-andrew`（S2 で作る worktree）、
`FOUR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types`（本契約の版管理外の置き場。無ければ作ってよい）。
`OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda`、`FIX=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle`。

| もの | 置き場（andrew） | bengio の値（照合の相手） |
|---|---|---|
| 検出塔の重み | `$A/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth` | sha256 `30d199b15201cf3c03954852d8acc6fb58fe5349baef2fd200e877237ff682c4` |
| Relation-DETR | `$A/third_party/Relation-DETR` | ソース 142 本（.py .cu .cuh .cpp .h。`input_digest.py` と同じ除外）の「sha256 経路」の一覧が `experiments/analysis/stage2_pilot_four/env/reldetr_src_bengio_overlay.txt` と一致（bengio の重ねの BODY は andrew のこの場所の写し。2026-10-20 01:25 JST に一致を確かめた） |
| 検出器の仮想環境 | `$A/.venv-relation-detr`（torch 2.1.2+cu118） | パッケージ 72 個の一覧が `env/venv_relation_detr_freeze_bengio_now.txt`（sha256 `2c7b070c93ca5a39…`）と一致 |
| 入力の要約値 | `$A/.venv-relation-detr/bin/python $WT/scripts/stage2pilot/input_digest.py --body $A --out <json>` | `env/input_digest_bengio.json` と、`relation_detr.commit`・`relation_detr.uncommitted`・`torch.gpus` を除く 167 個がすべて一致 |
| GPU | RTX A6000 × 2 を想定（S1 で実測。違えば止めて諮る） | bengio は RTX A6000 × 2 |

## 3. decoder-xattn が読む信号（andrew が写しの元なので、照合だけ）

| 経路 | sha256 | 使う腕 |
|---|---|---|
| `$OLD/signals/final/P0_train.npz` | e58308d39813b490de494c8bfaf5fa772c072e39e2c9d19bc011a2f96a056009 | 空（零にして使う）、予測-noCF（train） |
| `$OLD/signals/final/P0_val.npz` | 082387a092fe456d349c8cc46d6344042396bc39911461d88d2c51841b03dae8 | 空、予測-noCF、予測-CF（val）、陽性対照 |
| `$OLD/signals/final/P-GT_train.npz` | 6cb729a9724efdf51aa8d92e239d7755aa6d564fe4edd2ce1ba76b7e3cf79699 | 正解（train）、試走 |
| `$OLD/signals/final/P-GT_val.npz` | d21a3cf09246aece268a208ee6fe19ac40bbf561af202143ab3de2e196ccfd2a | 正解（val）、試走 |
| `$OLD/signals/cf/P0_train.npz` | e7b23991bce769abf6de804b59a9fd7813cca2f969d1655b9d2be0ef8e631cb8 | 予測-CF（train） |
| `$OLD/arms/PD/gtpred_CF_train.npz` | 6b0e99369b350caf4677f0861a0b93d7604d00ef0b81aeafaad0e7be30b19ac9 | 正解予測-CF（train） |
| `$OLD/arms/PD/gtpred_noCF_val.npz` | 5fe0a89c8402f455bbc0a3d85d7f00041f888e26fc334a62ab1c416ea94a5b8e | 正解予測-CF（val） |
| `$FIX/signals/shuffle/P0_train.npz` | 09814ab2f51153a8c4b3640de5613ed121b47bf7dafa6519014daef15598e843 | 入れ替え（train） |
| `$FIX/signals/shuffle/P0_val.npz` | 9ffc4e4d84a430106d12af43e6e26c81280e73e7ef7eddc850a0b2f93e01a113 | 入れ替え（val） |

この 9 本の値は bengio の `experiments/analysis/stage2_pilot_four/material/material_four.json`（直しの契約の記録との照合）と
`inputs/andrew_manifest.txt`（2026-10-20 01:2x JST に andrew で読んだ値）にある。**一つでも違えば止めて諮る。**

## 4. 型の実装（読んでおく）

- `scripts/stage2pilot/pd_four.py` の `PhaseDecoderXAttn` と `RelationDETRStage2Four`（interface `dec_xattn`）。SPEC §3.1 のとおり、decoder の全 6 層の各層の出力
  （FFN の後、その層の出力から box を精緻化する計算の前）に `h ← h + tanh(α_l) × W_out Attn(W_q LN(h), 工程の token)` を足す（forward hook）。
  工程の token は信号 → 32（入力適合層）→ 4 × 64、attention は 4 ヘッド。α_l は層ごとのスカラーで 0 から。decoder を通るすべての query
  （学習時の denoising と hybrid の経路を含む）に当てる。界面の初期化は固定の種で大域の乱数から切り離してある
- 構成 `configs/stage2pilot/pd_dec_xattn_d9.py`（正解予測-CF は `pd_dec_xattn_d18.py`）。学習する集合は名前が `phase_iface.` で始まる 210,374 個（d18 は 210,662 個）
- 起動 `scripts/stage2pilot/run_pd_four.sh DX <腕> [smoke]`（直しの契約の `run_pd_fix.sh` と同じ処方: `--trainable film`〔W1〕、`--epochs 4 --fixed-epochs`、
  `--amp bf16`、seed 42、`--save-trainable-only --ckpt-dir $FOUR/pd_ckpt/<run>`）。後処理 `pd_four_finalize.py` が `stage2four_metrics.json` と `notes.md` を書き、
  epoch ごとの層ごとの tanh(α_l) を `gates_by_epoch` に残す
- `S2FIX_BODY` を省くと `$A`（`/home/ubuntu/slocal2/m2`）を読む。`S2FIX_CODE=$WT` を渡すと run は worktree の `experiments/phase1/` にできる
- 学習後の自動同期（`train_t1b.py` の `_autosync_evidence`）は、分岐が `exp/*` でないので何もしない（`$A/.git/egosurgery-autosync.lock` を開くだけ）

## 5. 手順

**命令は単独で完結する形で書く（命令ごとにシェルが変わる実装系がある）。履歴を読む git は `git --no-pager`。** 命令と出力は `audit_andrew.md` に残す。

### S1 開始状態（読むだけ）

- `hostname`、時刻（JST）、`nvidia-smi`（装置の型と枚数、compute プロセス）、`df -B1 /home/ubuntu/slocal2`、`free -b`
- compute プロセスの列挙: `$WT/experiments/analysis/stage2_pilot_folda/tools/proc_enum.py --summary`（`/proc/PID/exe` の解決）。
  空振りでないことの確認: `bash -c 'sleep 15; :' zzz_four_marker &` の後に `--exe /usr/bin/bash --argv zzz_four_marker` が 1 件、`--exe /nonexistent/bin/bash` が 0 件
  （`bash -c 'sleep 15'` だと exec で置き換わって印が消える）。**本件以外の compute プロセスが一件でもあれば、止めずに利用者に諮る**
- main の作業場所の分岐と状態（`git -C $A branch --show-current`、`status --porcelain | wc -l`）を記録する。**変えない**
- `grep -n 'cd "\$M2DIR"' ~/bin/m2-sync.sh` と `grep -c worktree ~/bin/m2-sync.sh`（0 であること）

### S2 worktree と分岐

    git -C /home/ubuntu/slocal2/m2 fetch origin feat/stage2-pilot-four-new-types
    git -C /home/ubuntu/slocal2/m2 worktree add -b feat/stage2-pilot-four-new-types-andrew /home/ubuntu/slocal2/m2-four-andrew origin/feat/stage2-pilot-four-new-types

`git -C $WT rev-parse HEAD` を記録する（この文書を含む commit か、それ以降）。main の作業場所の分岐が変わっていないことを確かめる。

### S3 環境の照合（§2 の表）

1. `$A/.venv-relation-detr/bin/python $WT/scripts/stage2pilot/input_digest.py --body $A --out $WT/experiments/analysis/stage2_pilot_four/andrew/input_digest_andrew.json`
   → bengio の `env/input_digest_bengio.json` と、`relation_detr.commit`・`relation_detr.uncommitted`・`torch.gpus` を除くすべての値が一致
2. Relation-DETR のソースの一覧（bengio と同じ命令）:

       cd /home/ubuntu/slocal2/m2/third_party/Relation-DETR && find . -type f \( -name "*.py" -o -name "*.cu" -o -name "*.cuh" -o -name "*.cpp" -o -name "*.h" \) -not -path "*/__pycache__/*" | sed "s|^\./||" | grep -v -E "^(experiments|third_party|checkpoints|per_class_coco_map|data|outputs|work_dirs)/" | LC_ALL=C sort | xargs -d "\n" sha256sum > /home/ubuntu/slocal2/m2-four-andrew/experiments/analysis/stage2_pilot_four/andrew/reldetr_src_andrew.txt

   → `env/reldetr_src_bengio_overlay.txt` と全行一致（142 行）
3. パッケージの一覧（bengio と同じ命令）:

       /home/ubuntu/slocal2/m2/.venv-relation-detr/bin/python -c "import importlib.metadata as m; [print(f'{n}=={v}') for n,v in sorted({(d.metadata['Name'].lower(), d.version) for d in m.distributions()})]" > /home/ubuntu/slocal2/m2-four-andrew/experiments/analysis/stage2_pilot_four/andrew/venv_relation_detr_freeze_andrew.txt

   → `env/venv_relation_detr_freeze_bengio_now.txt` と全行一致（72 行）
4. §3 の 9 本と検出塔の重みの `sha256sum` が §3・§2 の値と一致

**一つでも違えば止めて諮る（直さない）。**

### S4 塔単独の再現（検出塔、許容差 0.005）

    cd $WT && source $A/.venv-relation-detr/bin/activate && CUDA_HOME=/usr/local/cuda EGO_BODY=$A EGO_ROOT=$A/data/raw/ego \
      EGO_ANN_DIR=$A/data/annotations/egosurgery_tool_folds/A PYTHONUTF8=1 CUDA_VISIBLE_DEVICES=0 \
      python scripts/stage2pilot/pd_eval.py --cfg plain --det-ckpt $A/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth \
      --save-preds $FOUR/identity/plain_val_preds_andrew.json.gz --out $WT/experiments/analysis/stage2_pilot_four/andrew/dtower_val_seed42_andrew.json

`metrics` の overall mAP が bengio の **0.7273450248398429**（標的群 AP 0.7950748008550897、陰性対照群 AP 0.6726631817581498）と許容差 0.005 の中にあるか。
超えたら止めて諮る。`mkdir -p $FOUR/identity $WT/experiments/analysis/stage2_pilot_four/andrew` は先に行ってよい。

### S5 恒等性と陽性対照（decoder-xattn の全 6 腕、val 全 1,515 枚）

    cd $WT && for L in 0 1; do S2FIX_BODY=/home/ubuntu/slocal2/m2 S2FOUR_REF=$FOUR/identity/plain_val_preds_andrew.json.gz \
      S2FOUR_OUT=$WT/experiments/analysis/stage2_pilot_four/andrew/identity S2FOUR_TYPES=DX \
      nohup bash scripts/stage2pilot/run_pd_four_identity.sh 2 $L > $WT/experiments/analysis/stage2_pilot_four/andrew/identity_lane$L.out 2>&1 < /dev/null & done

期待（bengio の `experiments/analysis/stage2_pilot_four/identity/pd_DX_*.json` と同じ形）:
- 6 腕とも `final.eval_detection_mAP` = 0.7273450248398429、`final.diff_vs_ref` の score・box の差の最大 0.0、ラベル不一致 0、
  `trainable.equal` true、`trainable.equal_with_one_detector_param_mixed` false、`gates_init` がすべて 0
- `pd_DX_positive_gate.json`（α を零でない値にする）で出力が変わる（`diff_vs_ref` の差が 0 でない）

**差が 0 でなければ止めて諮る。** bengio の同じ名前の json と値を並べて `audit_andrew.md` に書く。

### S6 試走（端から端まで動くこと）

    cd $WT && S2FIX_CODE=$WT CUDA_VISIBLE_DEVICES=0 bash scripts/stage2pilot/run_pd_four.sh DX gt smoke

rc=0、`$WT/experiments/phase1/stage2four_pd_DX_gt_ep4_seed42_smoke/` に run ができ、`env_check.txt` が `ms_deform_attn_ext True`、`train.log` に
`phase_grad=True`、`finalize.log` が通ること。bengio の同じ試走（2026-10-20 01:51 JST）は学習前 mAP 0.8916611661166115（val 20 枚）、後処理の AP 0.891661、
epoch 0 の tanh(α_l) が ±0.0006〜0.0012 だった。並べて記録する。**main の作業場所の `experiments/` に何も増えていないこと**を確かめる。

### S7 準備の記録の push（中間記録 1）

`audit_andrew.md`（S1〜S6）、`experiments/analysis/stage2_pilot_four/andrew/`、試走の run を commit して `feat/stage2-pilot-four-new-types-andrew` に push し、利用者に (a) を報告する。

### S8 本番の 6 本を起動する

1 枚に 3 本まで。例（1 枚に 3 本ずつ、20 秒ずつずらして裏で起こす）:

| GPU | run |
|---|---|
| 0 | `DX empty`、`DX pred_noCF`、`DX gt` |
| 1 | `DX pred_CF`、`DX gtpred_CF`、`DX shuffle` |

    cd /home/ubuntu/slocal2/m2-four-andrew && S2FIX_CODE=/home/ubuntu/slocal2/m2-four-andrew CUDA_VISIBLE_DEVICES=0 nohup bash scripts/stage2pilot/run_pd_four.sh DX empty > /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types/queues/andrew_DX_empty.out 2>&1 < /dev/null &

（`$FOUR/queues` は先に作る。2 本ずつ回して 2 回に分けるか 3 本ずつ 1 回で回すかは、S6 か最初の数分の it/s で決めてよい。決めた理由を記録する）

run の置き場: 版管理下は `$WT/experiments/phase1/stage2four_pd_DX_<腕>_ep4_seed42/`（git が追うファイル）、版管理外は同じ run の `predictions/` と
`$FOUR/pd_ckpt/stage2four_pd_DX_<腕>_ep4_seed42/best_t1b.pth`。利用者に (b) を報告する。

### S9 見守り（10 分ごと）

各 run の `train.log` に `Traceback`・`CUDA out of memory`・`not finite` が無いか、step の行が 15 分以上止まっていないか、`exit_code.txt`。
異常があれば**その腕を止めて記録し、利用者に諮る**（ほかの腕は続ける）。所要の見込み: 1 本 2〜4 時間（直しの契約の andrew の P3 W2 は 1 枚 2〜3 本で 2.45〜3.44 時間。
DX は W1 で decoder の後ろだけに勾配が流れる。測っていない）。

### S10 終わったら（中間記録 2）

6 本とも rc=0 になったら、run ごとに確かめて `audit_andrew.md` に書く:

- `t1b_result.json` の `result_selection` が `final_epoch`、`best_epoch` = `final_epoch` = 3、`mAP` = `final_mAP`
- `stage2four_metrics.json` の `init`（学習前の overall mAP）が **0.7273450248398429**、`frozen_unchanged` が true
- `gates_by_epoch`（学習前と epoch 0〜3 の層ごとの tanh(α_l)）
- `env_check.txt` の `ms_deform_attn_ext True`、`server.txt` が andrew
- epoch ごとの val mAP（`notes.md`）、1 本の所要（`start.txt`・`end.txt`）、GPU ごとの本数
- git の外の成果物の sha256（`predictions/*.json.gz`、`$FOUR/pd_ckpt/<run>/best_t1b.pth`）

commit するもの（**新しいファイルだけ**）: `experiments/phase1/stage2four_pd_DX_*_ep4_seed42/` と試走、`experiments/analysis/stage2_pilot_four/andrew/`、
`tasks/T-2026-10-19-stage2-pilot-four-new-types/audit_andrew.md`。commit の文の末尾には andrew のセッションの帰属の行を付ける。

    git -C $WT diff --stat origin/feat/stage2-pilot-four-new-types...HEAD      # 上の新しいファイルだけであること
    git -C $WT push -u origin feat/stage2-pilot-four-new-types-andrew

最後に利用者へ (c) として、分岐の名前・先頭の commit・6 本の結果（overall mAP・標的群 AP・陰性対照群 AP・4 epoch 目の層ごとの tanh(α_l)）を報告する。worktree は消さない。

## 6. bengio が行うこと（参考）

- andrew の push の後、`origin/feat/stage2-pilot-four-new-types-andrew` を fetch し、新しいファイルだけであることを確かめて `git merge --no-ff` で統合する
- andrew の記録（恒等性、再現、要約値、所要時間）を `audit.md` に写し、`aggregate_four.py` で decoder-xattn の表を作る。decoder-xattn（andrew）と
  extra-queries（bengio）の比較はホストをまたぐので、SPEC §6.2 の 7 のとおりホストの列を付けた参考の表にだけ置く
- `test_audit_four.py`・`make forbidden-check`・報告・PR・`make task-report`
