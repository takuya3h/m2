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

## S6 試走: 未実施（利用者に諮る）

handoff の命令 `S2FIX_CODE=$WT CUDA_VISIBLE_DEVICES=0 bash scripts/stage2pilot/run_pd_four.sh DX gt smoke` の run の置き場
`$WT/experiments/phase1/stage2four_pd_DX_gt_ep4_seed42_smoke/` は、bengio の同じ試走として**分岐に commit 済み**（`server.txt` = bengio）。
`run_pd_four.sh` は置き場が在ると `既に在る` で exit 4 になり、通ったとしても既存の追跡ファイルを上書きする（handoff §0・§1-6 に反する）。
台本に名前を変える引数は無い（第 3 引数が `smoke` のときだけ試走になり、run 名は `_smoke` で決まる）。台本を変えず、既存のファイルを変えずに S6 を行う形を利用者に諮る。
本番の 6 本の置き場（`stage2four_pd_DX_<腕>_ep4_seed42`）は分岐に無く、ぶつからない。

## 記録の注意（run の `git_commit.txt`）

`scripts/run_artifacts.py` の `_git_commit()` は `EGO_BODY`（andrew では `$A`）で `git rev-parse HEAD` を取るので、andrew の run の `git_commit.txt` は
**main の作業場所の HEAD** を書く（worktree の HEAD ではない。bengio の run は重ねの BODY が git でないので `unknown`）。台本は変えず、run ごとの worktree の HEAD を本書に書く。
引き渡しの後の worktree の HEAD は `faa0f1aa`（S2）。
