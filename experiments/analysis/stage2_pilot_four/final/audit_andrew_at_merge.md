# 監査記録（andrew、副の実行者）: T-2026-10-19-stage2-pilot-four-new-types（非公式の測定）

実行者: andrew の Claude Code（セッション a5e5d6c1-1c7f-4564-843b-dda59022aaf7）。時刻は JST。測っていない値は UNKNOWN と書く。
依頼は `handoff_andrew.md`（decoder-xattn〔DX〕の 6 本を andrew で回す。`spec.yaml` の `meta.amendments` 8 件目）。
以下 `A=/home/ubuntu/slocal2/m2`（andrew の main の作業場所。読むだけ）、`WT=/home/ubuntu/slocal2/m2-four-andrew`、
`FOUR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types`、
`OLD=…/T-2026-10-18-stage2-pilot-folda`、`FIX=…/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle`（どちらも `/home/ubuntu/slocal2/stage2pilot_store/` の下。読むだけ）。
生の出力は `experiments/analysis/stage2_pilot_four/andrew/`（引き渡しの後）と、引き渡しの前の準備の分は同じ親の `start/andrew_*`・`repro/*_andrew*` に置いた。

## 0. 引き渡しの前（利用者の指示 0・1、01:56〜02:07 JST）

- 指示 0（直しの契約の抑止の目印）: `$A/.sync-pause` は**無い**（`.sync-pause.released.*` も無い）。直しの契約の実行者のセッションが
  01:18:41 JST に `task-release: RELEASED task=T-2026-10-19-stage2-pilot-fix-epoch4-shuffle end=complete method=removed` を得ていた。
  条件（目印が在り、その契約の所有）を満たさないので `make task-release` は実行していない。記録は `start/andrew_sync_pause.txt`
- 指示 1: 遠隔の `feat/stage2-pilot-four-new-types`（先頭 `ed53c672`）を取得し、SPEC・spec.yaml・audit.md を読んだ。
  compute プロセス 0 件・空き 1,680,043,941,888 B（`start/andrew_procs_df.txt`、01:57:28 JST）
- worktree: `git -C $A worktree add -b feat/stage2-pilot-four-new-types-andrew $WT ed53c672`（引き渡しの前に作った）
- 検出塔の塔単独の val の再現（`repro/run_repro_andrew.sh`、02:03:57〜02:06:38 JST、GPU 2 枚に 1 本ずつ）: seed 42 の overall mAP 0.7273450248398429、
  標的群 0.7950748008550897、陰性対照群 0.6726631817581498。対照の seed 123 も含め bengio の `repro/dtower_val_*.json` と全項目が一致
  （`repro/dtower_compare_andrew_bengio.txt`）。予測 `$FOUR/identity/plain_val_preds.json.gz`（sha256 `258ebd7c9901706244e5015177ed71c9590c5710a49ff28dd7a3a14c0cd46385`）
- commit `1a66751b`（新しいファイル 10 本だけ）

## S1 開始状態（02:20:43 JST、`andrew/s1_s2_start.txt`）

- `hostname` = `Andrew`。`nvidia-smi`: GPU 0・1 とも RTX A6000、16 MiB、0%。`--query-compute-apps` は 0 行
- `proc_enum.py --summary`（`/proc/PID/exe` の解決）: python 系 **0 件**。在るのは bash・zsh・node・zmx・codex・syncthing・claude・git・ssh など（compute ではない）。
  **本件以外の compute プロセスは 0 件**
- 空振りでないこと: `bash -c 'sleep 15; :' zzz_four_marker &` の後に `--exe /usr/bin/bash --argv zzz_four_marker` は **count=1**、`--exe /nonexistent/bin/bash` は **count=0**
- `df -B1 /home/ubuntu/slocal2`: 空き **1,679,390,900,224 B**。`free -b`: available 87,924,731,904
- main の作業場所: 分岐 `feat/stage2-pilot-fix-epoch4-shuffle`、`status --porcelain` 0 行、HEAD `42070946`（**変えていない**）
- `grep -n 'cd "\$M2DIR"' ~/bin/m2-sync.sh` → `29:cd "$M2DIR" || exit 1`、`grep -c worktree ~/bin/m2-sync.sh` → **0**

## S2 worktree と分岐

- worktree は引き渡しの前（`ed53c672` 起点）に作ってあったので作り直さず、引き渡しの commit を取り込んだ:
  `git -C $WT merge --no-ff origin/feat/stage2-pilot-four-new-types`（`659378f6` 引き渡し、`0d717f09` phase0 の取り込み）→ **`faa0f1aa`**。衝突なし
- `git -C $WT rev-parse HEAD` = `faa0f1aa331a190cf28298e6e784171ee56e8f13`（この文書を含む commit の子孫）。
  `git diff --name-status origin/feat/stage2-pilot-four-new-types...HEAD` は `A`（新しいファイル）10 本だけ
- main の作業場所の分岐は変わっていない（S1）

## S3 環境の照合（02:21〜02:24 JST）

| # | 照合 | 結果 |
|---|---|---|
| 1 | `input_digest.py --body $A`（`andrew/input_digest_andrew.json`）と bengio の `env/input_digest_bengio.json` | `relation_detr.commit`・`relation_detr.uncommitted`・`torch.gpus` を除く **177 個の値がすべて一致**（入れ子を末端の値まで平らにして数えた。handoff の 167 個とは数え方が違う。不一致 0）。除いた値: andrew は commit `b485955c…`・未 commit 42、bengio は空・0（重ねの BODY は git でない）。GPU は両方 RTX A6000 × 2 |
| 2 | Relation-DETR のソースの一覧（handoff と同じ命令、`andrew/reldetr_src_andrew.txt`） | **142 行**、`env/reldetr_src_bengio_overlay.txt` と差 **0 行** |
| 3 | `.venv-relation-detr` のパッケージの一覧（同じ命令、`andrew/venv_relation_detr_freeze_andrew.txt`） | **72 行**、`env/venv_relation_detr_freeze_bengio_now.txt` と差 **0 行**、sha256 `2c7b070c93ca5a39…` |
| 4 | §3 の 9 本と検出塔の重みの `sha256sum -c`（`andrew/s3_4_expected.sha256`、`andrew/s3_4_check.txt`） | **10/10 OK**。陽性対照: 期待値の 1 文字を変えると `FAILED` |

S3-1 は `GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1` を付けて実行した（`input_digest.py` が `$A/third_party/Relation-DETR` で呼ぶ `git status` に index を書き直させず、
main の third_party に `.pyc` を書かないため。値には効かない）。`$A/third_party/Relation-DETR/.git/index` の更新時刻は実行の後も `2026-10-13 19:27:04` のまま。

## S4 塔単独の再現（検出塔、02:20:58〜02:23:37 JST、`andrew/dtower_val_seed42_andrew.json`・`andrew/s4_compare.txt`）

handoff の命令のとおり（`PYTHONDONTWRITEBYTECODE=1` だけ足した。main の third_party に `.pyc` を書かないため。値には効かない）。rc=0。

| 指標 | andrew | bengio（`repro/dtower_val_seed42.json`） | 差 |
|---|---|---|---|
| overall mAP | 0.7273450248398429 | 0.7273450248398429 | 0.0 |
| AP50 | 0.851807431425236 | 0.851807431425236 | 0.0 |
| 標的群 AP | 0.7950748008550897 | 0.7950748008550897 | 0.0 |
| 陰性対照群 AP | 0.6726631817581498 | 0.6726631817581498 | 0.0 |
| 動画ごと 09 / 10 | 0.704273483949694 / 0.6420973291237674 | 同じ | 0.0 |

許容差 0.005 の中。クラス別 AP・`non_interface_digest`・重みの sha256 も同一。基準の予測 `$FOUR/identity/plain_val_preds_andrew.json.gz`
（sha256 `22d8b5cae7056ff795922ca9b9cf4dbddb4f8df5fbd3e251267efc0e4d6e2a4f`）。展開した中身の sha256 `65610b5b932dd61b…` は 02:03 の再現の
`plain_val_preds.json.gz` と同じ（gzip の見出しの時刻だけが違う）。

## 副作用の記録: main の入れ子の repo の `.git` ディレクトリの更新時刻（実行者の誤り）

- `find -newer` で、`$A/third_party/Relation-DETR/.git`（ディレクトリ自体）の更新時刻が 02:21:04 と 02:25:27・02:25:39 JST に変わったことを見つけた。
  中のファイル（`index`・`HEAD`・`refs`・`objects` など）は**どれも変わっていない**（`find $A/third_party/Relation-DETR/.git -newermt '2026-10-19 17:00'` はディレクトリ自体の 1 件だけ。`index` は 2026-10-13 19:27:04 のまま）
- 原因: 私が S3-2 の命令（`cd $A/third_party/Relation-DETR && find …`）と調べものの命令で、セッションの作業場所を main の入れ子の repo に移した。
  Claude Code の状態行のスクリプト `~/.claude/statusline.sh`（37 行）は**セッションの作業場所で** `git status --porcelain` を走らせるので、その repo の `.git` に
  一時ファイル（index.lock）を作って消し、ディレクトリの更新時刻が変わった。写しの repo（scratchpad に rsync した写し）で、設定なしの `git status` は `.git` の
  更新時刻を変え、`GIT_OPTIONAL_LOCKS=0` の `git status`・`git rev-parse` は変えないことを確かめた（input_digest.py の呼び出しは原因でない）
- 対処: 以後は main の中へ `cd` しない（main の場所は絶対経路か、台本の中のサブシェルでだけ使う）。作業場所を戻した後、更新時刻が止まったことを確かめた（下記）
- 確認: 作業場所を戻した後、`stat -c %y $A/third_party/Relation-DETR/.git` は 02:25:39 JST のまま 90 秒以上動かなかった（02:27:19 JST に確認）

## S5 恒等性と陽性対照（decoder-xattn の全 6 腕と陽性対照、val 全 1,515 枚、02:26:07〜02:36:38 JST）

handoff の命令のとおり、2 レーン（GPU 0・1）で `run_pd_four_identity.sh 2 <L>` を回した（`PYTHONDONTWRITEBYTECODE=1` だけ足した。`S2FOUR_REF=$FOUR/identity/plain_val_preds_andrew.json.gz`、
出力 `andrew/identity/`、レーンの出力 `andrew/identity_lane{0,1}.out`）。7 本とも rc=0。bengio の `identity/pd_DX_*.json` との照合は `andrew/s5_compare.txt`。

| 腕 | 学習前の val mAP | score 差の最大 | box 差の最大（px） | ラベル不一致 | trainable.equal | 一つ混ぜると | 学習する数 | gates_init | bengio と同値 |
|---|---|---|---|---|---|---|---|---|---|
| empty | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | false | 210,374 | すべて 0 | true |
| pred_noCF | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | false | 210,374 | すべて 0 | true |
| gt | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | false | 210,374 | すべて 0 | true |
| pred_CF | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | false | 210,374 | すべて 0 | true |
| gtpred_CF | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | false | 210,662 | すべて 0 | true |
| shuffle | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | false | 210,374 | すべて 0 | true |
| positive_gate（α を零でない値に） | 0.7272701920052 | 0.007002487778663635 | 1955.0339889526367 | 161,010 | true | false | 210,374 | すべて 0（評価時の tanh(α_l) は 0.002307・0.020117・−0.050533・0.010836・−0.030604・0.025175） | true |

「bengio と同値」は、mAP・標的群 AP・陰性対照群 AP・クラス別 AP・`diff_vs_ref`・`gates_init`・`gates_eval`・学習する名前の一覧・`non_interface_digest`・信号の sha256 がすべて同じであること。
6 腕で差は 0、陽性対照で出力が変わる。**handoff の期待どおり。**

S4・S5 の後に、main の `third_party`・`experiments/baselines/stage1_dtower_r2`・`data/annotations`・`data/external` で基準時刻（02:20:58）より新しいファイルは
上記の `.git` ディレクトリ 1 件を除いて 0 件。main の `experiments/phase1` に `stage2four` の名前は 0 件。main の `status --porcelain` 0 行、分岐は不変。
前回と直しの保存先（`$OLD`・`$FIX`）で 01:56 JST より新しいものは 0 件。

## S6 試走（02:40:11〜02:40:22 JST、`andrew/smoke_DX_gt/`）

**handoff からの逸脱（利用者の承認、02:38 JST 頃の回答「別の worktree で試走」）。** handoff の命令の run の置き場
`$WT/experiments/phase1/stage2four_pd_DX_gt_ep4_seed42_smoke/` は、bengio の同じ試走として分岐に commit 済み（`server.txt` = bengio）。
`run_pd_four.sh` は置き場が在ると `既に在る` で exit 4 になり、通っても既存の追跡ファイルを上書きする。台本に名前を変える引数は無い。
利用者に諮り、同じ commit の写しの別の場所で回す方針の承認を得た。git worktree として取り出すと bengio の試走の置き場も出てくるので
（消すとファイルの削除、sparse-checkout は共有の `.git/config` を変える）、次の形にした:

    mkdir /home/ubuntu/slocal2/m2-four-andrew-smoke && git -C $WT archive cf517ee5 | tar -x -C /home/ubuntu/slocal2/m2-four-andrew-smoke --exclude='experiments/phase1/stage2four_pd_DX_gt_ep4_seed42_smoke'
    → ファイル 22,294 本と記号リンク 4 本（追跡 22,316 から除いた 18 本を引いた数と一致）。run_pd_four.sh・train_t1b.py・pd_four.py・pd_dec_xattn_d9.py・pd_four_finalize.py は $WT と同一（cmp）
    (cd /home/ubuntu/slocal2/m2-four-andrew-smoke && S2FIX_CODE=/home/ubuntu/slocal2/m2-four-andrew-smoke PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=0 bash scripts/stage2pilot/run_pd_four.sh DX gt smoke)
    → [run_pd_four] stage2four_pd_DX_gt_ep4_seed42_smoke rc=0

run は写しの場所にできた。予測と `checkpoints/` を除く run のファイルを `andrew/smoke_DX_gt/run/` に写した（命令の出力と時刻は `andrew/smoke_DX_gt/`）。
写しの場所は git でないので、試走の自動同期は `exp_dir is not inside a git repository` で何もしない。`git_commit.txt` は `$A` の HEAD（42070946）。写しの場所は消していない。

| 項目 | andrew | bengio の試走（01:51 JST） |
|---|---|---|
| `env_check.txt` | `ms_deform_attn_ext True` | 同じ |
| `train.log` | `phase_grad=True init_mAP=0.8917 => PASS`、学習する数 210,374、det_steps/ep 4809 | 同じ |
| 最初の歩 | `L=25.823 2.3it/s` | `L=25.823 0.9it/s` |
| 学習前 mAP（val 20 枚） | 0.8916611661166115 | 0.8916611661166115 |
| 後処理の AP | 0.891661（`finalize.log`、diff 0.00e+00） | 0.891661 |
| 凍結部の要約値の前後一致 | true | true |
| epoch 0 の tanh(α_l) | 0.0011766・−0.0007764・−0.0012253・0.0009191・−0.0006288・0.0008164 | 0.0011710・−0.0007627・−0.0012172・0.0009392・−0.0006296・0.0008164 |

epoch 0 のゲートは 1e−5 ほど違う（bf16 の自動混合精度で 6 歩学習した後の値。装置の違いによる程度の差と見ている。原因は確かめていない）。
重み `$FOUR/pd_ckpt/stage2four_pd_DX_gt_ep4_seed42_smoke/best_t1b.pth` 853,896 B。
main の作業場所: 試走の後、`$A/experiments` に基準時刻（02:40 直前）より新しいファイル 0 件、`status --porcelain` 0 行。

## S8 本番の 6 本の起動

- 起動の直前（02:41 JST）: GPU の compute プロセス 0 件、python 系 0 件。worktree の HEAD `cf517ee5`（6 本とも同じ commit の台本で起動）
- 1 回目（02:41:16〜02:42:56 JST）: **失敗（実行者の誤り）**。zsh の `for spec in "0 empty" …; do set -- $spec` は引用符なしの変数を単語に分けないため、
  GPU 番号と腕の名前が一つの値のまま入り、腕が空になった。6 回とも `run_pd_four.sh: line 18: $2: unbound variable` で即座に止まった
  （run の置き場も重みも作られていない。残ったのは `$FOUR/queues/andrew_DX_.out` 1 本と `andrew_launch.txt` の記録）
- 2 回目（02:43:44〜02:45:24 JST）: 起動の手順を bash の台本にして実行した（handoff の命令と同じ形。`PYTHONDONTWRITEBYTECODE=1` を足した）。
  `(cd $WT && S2FIX_CODE=$WT PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=<G> nohup bash scripts/stage2pilot/run_pd_four.sh DX <腕> > $FOUR/queues/andrew_DX_<腕>.out 2>&1 < /dev/null &)`、20 秒ずつずらした

| GPU | run（起動の時刻 JST） |
|---|---|
| 0 | `DX empty`（02:43:44）、`DX pred_noCF`（02:44:04）、`DX gt`（02:44:24） |
| 1 | `DX pred_CF`（02:44:44）、`DX gtpred_CF`（02:45:04）、`DX shuffle`（02:45:24） |

- 1 枚 3 本にした理由: 6 本が一度に揃い、2 本ずつ 2 回に分けるより早く終わる見込みのため（直しの契約では 3 本目の伸びが 3% 以下。handoff §1-8）。
  記憶は起動直後（学習前の評価中）で 1 本 1,592 MiB ほど。学習中の値と速さは下に足す
- 6 本とも `env_check.txt` は `ms_deform_attn_ext True`、`server.txt` は `andrew`

## 記録の注意（run の `git_commit.txt`）

`scripts/run_artifacts.py` の `_git_commit()` は `EGO_BODY`（andrew では `$A`）で `git rev-parse HEAD` を取るので、andrew の run の `git_commit.txt` は
**main の作業場所の HEAD** を書く（worktree の HEAD ではない。bengio の run は重ねの BODY が git でないので `unknown`）。台本は変えず、run ごとの worktree の HEAD を本書に書く。
引き渡しの後の worktree の HEAD は `faa0f1aa`（S2）。

## S9 見守り

- 02:55 JST: GPU 0 の 3 本は ep0 500/4809 歩（1.5・1.7・1.7 it/s）、GPU 1 の 3 本は ep0 0/4809 歩（評価を終えて学習に入ったところ）
- 02:56 JST: `nvidia-smi` で 1 本 4,434〜4,450 MiB、GPU ごとに 13,383 / 13,364 MiB（49,140 MiB 中）、使用率 98〜100%。`free -b` の available 68,468,060,160
- 見込み: 4 epoch × 4,809 歩 = 19,236 歩を 1 本 1.5〜1.7 it/s で約 3.2〜3.6 時間（epoch ごとの val 評価を除く）。測った値ではない
- 6 本とも rc=0（06:31〜06:36 JST に終了）。見守りの間に `Traceback`・`CUDA out of memory`・`not finite`・`Error` の行は 0 件、15 分以上の停止は 0 件。速さは 1 本 1.5〜1.7 it/s（epoch の始めの評価の直後だけ 0.8〜1.2 it/s）。1 epoch は学習と評価でおよそ 55 分

## S10 終わりの確認（06:37 JST、`andrew/check_dx6.py` → `andrew/s10_check.json`）

確認した項目（6 本ともすべて true）: `exit_code.txt` が 0、`t1b_result.json` の `result_selection` が `final_epoch`、`best_epoch` = `final_epoch` = 3、`mAP` = `final_mAP`、`stage2four_metrics.json` の `init` が 0.7273450248398429、`frozen_unchanged` が true、`env_check.txt` に `ms_deform_attn_ext True`、`server.txt` が andrew、学習前のゲート（`gates_by_epoch` の −1）がすべて 0。

### 4 epoch 目の値（val、動画 09・10。非公式。表の値は `stage2four_metrics.json` のまま）

| 腕 | GPU | overall mAP | 標的群 AP | 陰性対照群 AP | 動画 09 | 動画 10 | 起動〜終了（JST） | 所要（時間） |
|---|---|---|---|---|---|---|---|---|
| empty | 0 | 0.7286351809653658 | 0.7971802124759885 | 0.674744871212618 | 0.7046779783477529 | 0.6426769384452503 | 02:43:44〜06:30:43 | 3.783 |
| pred_noCF | 0 | 0.7285507127170769 | 0.7977964150437383 | 0.6743162666121828 | 0.7045593499920725 | 0.6454434789599283 | 02:44:04〜06:31:00 | 3.782 |
| gt | 0 | 0.7307424633845512 | 0.8023051689913743 | 0.6748186678418289 | 0.7052871016926068 | 0.6471674397790789 | 02:44:24〜06:31:57 | 3.792 |
| pred_CF | 1 | 0.7280597990708618 | 0.7956651065025846 | 0.674161721518428 | 0.7045969947183123 | 0.6424095936034077 | 02:44:44〜06:34:50 | 3.835 |
| gtpred_CF | 1 | 0.7304329266677848 | 0.8002190391680053 | 0.6743968833150071 | 0.7071988489831421 | 0.6460686371249901 | 02:45:04〜06:35:06 | 3.834 |
| shuffle | 1 | 0.728501777648758 | 0.7968013222990057 | 0.6745119663775374 | 0.704305336656446 | 0.6438449077268178 | 02:45:24〜06:35:59 | 3.843 |

GPU ごとの本数: GPU 0 に 3 本（empty・pred_noCF・gt）、GPU 1 に 3 本（pred_CF・gtpred_CF・shuffle）。

### epoch ごとの val の overall mAP（−1 は学習前）

| 腕 | −1 | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| empty | 0.7273450248398429 | 0.7281964925627056 | 0.7284762770570204 | 0.7281527176385221 | 0.7286351809653658 |
| pred_noCF | 0.7273450248398429 | 0.7275298498760622 | 0.7277902902596856 | 0.7278654175953629 | 0.7285507127170769 |
| gt | 0.7273450248398429 | 0.7282817761342244 | 0.7296023034121155 | 0.7300764882110159 | 0.7307424633845512 |
| pred_CF | 0.7273450248398429 | 0.7283179598495638 | 0.7284101221735505 | 0.7283356924939556 | 0.7280597990708618 |
| gtpred_CF | 0.7273450248398429 | 0.7276023078920366 | 0.7287565183052361 | 0.7289712955964566 | 0.7304329266677848 |
| shuffle | 0.7273450248398429 | 0.7280328186798748 | 0.7284286880071634 | 0.7280319768663919 | 0.728501777648758 |

### epoch ごとの層ごとの tanh(α_l)（層 1〜6。−1 は学習前で 6 本ともすべて 0）

| 腕 | epoch | 層 1 | 層 2 | 層 3 | 層 4 | 層 5 | 層 6 |
|---|---|---|---|---|---|---|---|
| empty | 0 | 0.049459 | -0.049042 | -0.061284 | -0.030936 | 0.043932 | 0.026038 |
| empty | 1 | 0.056248 | -0.058086 | -0.074088 | -0.052001 | 0.055913 | 0.037380 |
| empty | 2 | 0.051472 | -0.071715 | -0.086606 | -0.069651 | 0.061804 | 0.029051 |
| empty | 3 | 0.060689 | -0.080099 | -0.092224 | -0.076897 | 0.067752 | 0.046411 |
| pred_noCF | 0 | 0.049624 | -0.043820 | -0.054026 | -0.042910 | 0.039128 | 0.025657 |
| pred_noCF | 1 | 0.064854 | -0.060664 | -0.067823 | -0.062642 | 0.066285 | 0.038477 |
| pred_noCF | 2 | 0.066382 | -0.078937 | -0.090216 | -0.090367 | 0.072748 | 0.040423 |
| pred_noCF | 3 | 0.082923 | -0.086064 | -0.099763 | -0.093686 | 0.082100 | 0.057186 |
| gt | 0 | 0.048883 | -0.045762 | -0.052765 | -0.043206 | 0.037998 | -0.032631 |
| gt | 1 | 0.063444 | -0.061688 | -0.072891 | -0.061628 | 0.058610 | -0.051329 |
| gt | 2 | 0.063395 | -0.078262 | -0.078263 | -0.098088 | 0.077000 | -0.056612 |
| gt | 3 | 0.076465 | -0.091421 | -0.088309 | -0.097042 | 0.077875 | -0.075848 |
| pred_CF | 0 | 0.047034 | -0.047373 | -0.051623 | -0.035312 | 0.049602 | -0.009096 |
| pred_CF | 1 | 0.058789 | -0.058010 | -0.070051 | -0.052178 | 0.055809 | -0.026150 |
| pred_CF | 2 | 0.059170 | -0.072426 | -0.089088 | -0.083398 | 0.072012 | -0.027182 |
| pred_CF | 3 | 0.073020 | -0.086956 | -0.098745 | -0.093171 | 0.076854 | -0.047999 |
| gtpred_CF | 0 | 0.062597 | -0.043804 | -0.048476 | -0.048162 | 0.048591 | 0.028265 |
| gtpred_CF | 1 | 0.071746 | -0.069547 | -0.078879 | -0.070149 | 0.067749 | 0.038522 |
| gtpred_CF | 2 | 0.080907 | -0.084737 | -0.098870 | -0.096550 | 0.083152 | 0.047486 |
| gtpred_CF | 3 | 0.094462 | -0.091529 | -0.122448 | -0.103655 | 0.098819 | 0.064245 |
| shuffle | 0 | 0.049912 | -0.040539 | -0.053178 | -0.038285 | 0.044301 | 0.024829 |
| shuffle | 1 | 0.058515 | -0.055871 | -0.069255 | -0.049912 | 0.042240 | 0.034434 |
| shuffle | 2 | 0.049329 | -0.059079 | -0.075911 | -0.069180 | 0.051043 | 0.028116 |
| shuffle | 3 | 0.060523 | -0.064800 | -0.080617 | -0.066017 | 0.077178 | 0.043109 |

### git の外の成果物（andrew に残す）

| 腕 | ファイル | 大きさ（B） | sha256 |
|---|---|---|---|
| empty | `$WT/experiments/phase1/stage2four_pd_DX_empty_ep4_seed42/predictions/val_ctrl_best.json.gz` | 13048844 | `23db3023804d5bcdb39d601b4f92bd5ba277bb688c6d52dda5952826b8072673` |
| empty | `$WT/experiments/phase1/stage2four_pd_DX_empty_ep4_seed42/predictions/val_ctrl_ep-1.json.gz` | 13032761 | `0ac1aae518f8e69d1f8dc0d5f315c1a8285051d3782b73b1d358e6094dcaba19` |
| empty | `$FOUR/pd_ckpt/stage2four_pd_DX_empty_ep4_seed42/best_t1b.pth` | 853896 | `58a702d3394265d00b375c458c013991a4cbb320d1e5a535048dd98ea6e1f714` |
| pred_noCF | `$WT/experiments/phase1/stage2four_pd_DX_pred_noCF_ep4_seed42/predictions/val_inj_best.json.gz` | 12971635 | `9405f94be5238c98aa0ea5efc5553bf3873840e6af2ede581c1dd0e6b958a445` |
| pred_noCF | `$WT/experiments/phase1/stage2four_pd_DX_pred_noCF_ep4_seed42/predictions/val_inj_ep-1.json.gz` | 13032761 | `0ac1aae518f8e69d1f8dc0d5f315c1a8285051d3782b73b1d358e6094dcaba19` |
| pred_noCF | `$FOUR/pd_ckpt/stage2four_pd_DX_pred_noCF_ep4_seed42/best_t1b.pth` | 853896 | `351ee53fa90e54e2f98277250d14ec8cd6d68dd9daf9da6510b681784bb754df` |
| gt | `$WT/experiments/phase1/stage2four_pd_DX_gt_ep4_seed42/predictions/val_inj_best.json.gz` | 12638284 | `e1257886fd3b3f6065701514d917ecd6811cdc93a7d0266a4f108f10967ba739` |
| gt | `$WT/experiments/phase1/stage2four_pd_DX_gt_ep4_seed42/predictions/val_inj_ep-1.json.gz` | 13032761 | `0ac1aae518f8e69d1f8dc0d5f315c1a8285051d3782b73b1d358e6094dcaba19` |
| gt | `$FOUR/pd_ckpt/stage2four_pd_DX_gt_ep4_seed42/best_t1b.pth` | 853896 | `dfd4837e5c4bc8232aa60a1a78854b55248a0458303a2b5c75c5a5089e0ab1e6` |
| pred_CF | `$WT/experiments/phase1/stage2four_pd_DX_pred_CF_ep4_seed42/predictions/val_inj_best.json.gz` | 12875866 | `e5df068577cd874e0127c21fcbc558dd6a0fcc535d91fa54f634ee2cfc564ace` |
| pred_CF | `$WT/experiments/phase1/stage2four_pd_DX_pred_CF_ep4_seed42/predictions/val_inj_ep-1.json.gz` | 13032761 | `0ac1aae518f8e69d1f8dc0d5f315c1a8285051d3782b73b1d358e6094dcaba19` |
| pred_CF | `$FOUR/pd_ckpt/stage2four_pd_DX_pred_CF_ep4_seed42/best_t1b.pth` | 853896 | `d90d60732091bfd8e1de24edeb471c08a62866fbdebdaea480d17bc6f251e618` |
| gtpred_CF | `$WT/experiments/phase1/stage2four_pd_DX_gtpred_CF_ep4_seed42/predictions/val_inj_best.json.gz` | 13072124 | `6066ec54bf298e5fc3062fd73e574ef9c0aafb70c7fc14f3ea63b1612680d605` |
| gtpred_CF | `$WT/experiments/phase1/stage2four_pd_DX_gtpred_CF_ep4_seed42/predictions/val_inj_ep-1.json.gz` | 13032761 | `0ac1aae518f8e69d1f8dc0d5f315c1a8285051d3782b73b1d358e6094dcaba19` |
| gtpred_CF | `$FOUR/pd_ckpt/stage2four_pd_DX_gtpred_CF_ep4_seed42/best_t1b.pth` | 855048 | `c4d08c774eef5664a03ded6edd32d9e2345c2c37567bd6690e38f6d53df43278` |
| shuffle | `$WT/experiments/phase1/stage2four_pd_DX_shuffle_ep4_seed42/predictions/val_inj_best.json.gz` | 13176817 | `ae4c099fbfd6f31f4c178c3d5c320d3d59e03d13e08e0603ebb724cce15387eb` |
| shuffle | `$WT/experiments/phase1/stage2four_pd_DX_shuffle_ep4_seed42/predictions/val_inj_ep-1.json.gz` | 13032761 | `0ac1aae518f8e69d1f8dc0d5f315c1a8285051d3782b73b1d358e6094dcaba19` |
| shuffle | `$FOUR/pd_ckpt/stage2four_pd_DX_shuffle_ep4_seed42/best_t1b.pth` | 853896 | `ea37e1abee616ed9d08e41f906fd49b16fc0d027e1769b04dffa4eacebd8ff39` |

bengio の `aggregate_four.py` は PD の予測を run の `predictions/val_inj_best.json.gz`（empty は `val_ctrl_best.json.gz`）から読んで値を計算し直す。予測は git に載らないので、bengio で計算し直すときは上の経路を andrew から写し、sha256 を照合すること。

### run の commit

6 本の run の `git_commit.txt` は `42070946a9e7a4d513712f29c094d86ff83debf5`（**main の作業場所の HEAD**。記録の注意を参照）。6 本を起動した時点の worktree の HEAD は `cf517ee5e47056dc9142816b874ed552eecea502`（`$FOUR/queues/andrew_launch.txt`）で、台本・構成はその commit のもの。

### 書き込みの確認（06:37 JST）

main の `third_party`・`experiments`・`data/annotations`・`data/external` で 02:40 より新しいファイル 0 件。`status --porcelain` 0 行、分岐 `feat/stage2-pilot-fix-epoch4-shuffle`、HEAD `42070946`（開始時と同じ）。`$A/third_party/Relation-DETR/.git` の更新時刻は 02:25:39 JST のまま。前回と直しの保存先（`$OLD`・`$FIX`）で 01:56 JST より新しいもの 0 件。書いたのは worktree、写しの場所 `/home/ubuntu/slocal2/m2-four-andrew-smoke`、本契約の置き場 `$FOUR`（`identity/`・`pd_ckpt/`・`queues/`）だけ。
