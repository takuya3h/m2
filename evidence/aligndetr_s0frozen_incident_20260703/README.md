# AlignDETR S0-frozen インシデント（2026-07-03）

## 保全の経緯

2026-08-02、philip の `/tmp` に残っていた実行痕跡から再構成した。
破棄理由は git / `docs/` / `tasks/` のいずれにも記載が無く
（`data/processed/` は `.gitignore` 対象のため `git log -S` も効かない）、
`/tmp` の揮発性ファイルが偶然 40 日間生き残っていたことで判明した。
**再起動していれば永久に判明しなかった。**

## 時系列（すべて実測。証拠は本ディレクトリ内）

| 日時 (UTC) | 出来事 | 証拠ファイル |
|---|---|---|
| 07-03 15:55 | AlignDETR-S0-frozen seed42 の学習を 2 GPU で開始 | `aligndetr_s0frozen_seed42_20260703_155535.log` |
| 07-03 16:25 | **NCCL ALLREDUCE タイムアウトで失敗**（後述） | 同上 |
| 07-03 17:08 | `entry5.sh` 起動。S0-frozen ckpt が無いため 2026-05-31 の通常学習 AlignDETR ckpt で代替 | `entry5.sh` |
| 07-03 17:10-17:20 | 特徴抽出（正常完了） | `discarded_cache_{val,test,train}_extract.log` |
| 07-03 17:20-17:21 | TeCNO 3 seed 学習 → 問題の 3 run | `entry5_tecno_seed{42,123,456}.log` |
| 07-05 09:13 | キャッシュを `.discarded_20260705` へリネーム | ディレクトリ mtime |
| 07-06 03:24 | S0-frozen を再学習（v2）**成功**。bbox AP 68.596 | `aligndetr_s0frozen_v2_train_log.txt` |
| 07-10 17:39-17:47 | `stage1_features/aligndetr_s0frozen_seed42` を作り直し | `stage1_features/` mtime |

### 07-03 16:25 の失敗（一次証拠の抜粋）

```
[2026-07-03_15:55:35] === Starting AlignDETR-S0-frozen seed=42 (2gpu) ===
[E ProcessGroupNCCL.cpp:475] [Rank 1] Watchdog caught collective operation timeout:
  WorkNCCL(SeqNum=1, OpType=ALLREDUCE, NumelIn=1, NumelOut=1, Timeout(ms)=1800000)
  ran for 1800745 milliseconds before timing out.
[E ProcessGroupNCCL.cpp:495] To avoid data inconsistency, we are taking the entire process down.
torch.multiprocessing.spawn.ProcessExitedException: process 1 terminated with signal SIGABRT
```

`SeqNum=1` は**最初の collective で 30 分ハングした**ことを示す。学習は 1 step も進んでいない。

## 抽出スクリプトとの違反（実測）

`scripts/extract_stage1_features_aligndetr.py`（git 追跡・`891953c`）が docstring と
argparse ヘルプで要求する値に対し、`entry5.sh` が渡した値は **3 項目すべてで異なる**。

| 項目 | スクリプトが要求 | `entry5.sh` が渡した値 |
|---|---|---|
| config | `aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py` | `aligndetr_r50_4scale_12ep_egosurgery.py`（通常版） |
| checkpoint | `/tmp/aligndetr_s0frozen_seed42_XXXX/model_final.pth` | `/tmp/aligndetr_work_seed42/model_final.pth`（**2026-05-31**） |
| 出力先 | `stage1_features/aligndetr_s0frozen_seed42/` | `stage1_features/aligndetr_seed42/` |

07-10 に作られた置換キャッシュの名前は、スクリプトが文書化している出力先と完全一致する。

## キャッシュ自体は正常

抽出処理は完走しており、frame 数・次元・サイズは正常。

```
val   1515 x 2048    (12,465,940 bytes)
test  4265 x 2048    (35,092,940 bytes)
train 9657 x 2048    (79,458,316 bytes)
C5 shape=(1, 2048, 34, 60)   GAP dim=2048
```

`relation_detr_seed42` と **1 バイト単位で一致**。
破棄理由は「抽出が壊れていた」ではなく「**入力 ckpt が意図と異なる**」である。

## 依拠した run の扱い

`experiments/phase1/s4_phase_baseline_{010,011,012}_frozen_tecno_phase_baseline_aligndetr_seed{42,123,456}`
は **無効**（2026-08-02 判定）。各 run の `INVALID.md` を参照。
数値記録そのものは健全であり、無効なのは実験条件である。

## 判別できなかったこと

以下は 2026-08-02 時点で**判別不能**。推測で埋めていない。

1. **破棄を決めた主体と、その時点での理由の認識。**
   07-05 09:13 のリネームを誰がどういう判断で行ったかを示す記録は存在しない。
   上記の時系列は残存ファイルの mtime と内容から再構成したものであり、
   「NCCL 失敗を認識して是正した」という因果は**状況証拠による推定**である。
   （時系列の各事象そのものは実測。因果の結び付けが推定。）

2. **`stage1_features` 系列の非対称の意図。**
   AlignDETR は `_s0frozen` 版へ移行しているが、Relation-DETR 側には
   `relation_detr_s0frozen_*` が存在しない（`checkpoints/incoming/seed42/best_ap.pth`
   すなわち通常 S0 ckpt を使用）。これが設計変更の途中経過なのか、
   検出器ごとに異なるプロトコルを意図しているのかは判別できない。

3. **07-06 の 2 件（`b2a_detsignal` / `t1a_regiontoken` の `*_s0frozen_seed42`）の破棄理由。**
   各ディレクトリの `DISCARDED.md` に記載のとおり判別不能。

4. **`train_s4_tecno_aligndetr.py` が git に入らなかった理由。**
   `/tmp/queue_runner/` 配下で作成・実行されており、追跡対象にする意図があったかは不明。

## 収録ファイル

| ファイル | 内容 |
|---|---|
| `train_s4_tecno_aligndetr.py` | 3 run を生成した学習スクリプト。**git 全履歴に存在しない** |
| `entry5.sh` | 3 run を起動した本体（特徴抽出 → TeCNO 3 seed） |
| `entry5_tecno_seed{42,123,456}.log` | 全 50 epoch の学習記録 |
| `aligndetr_s0frozen_seed42_20260703_155535.log` | **NCCL 失敗の一次証拠** |
| `aligndetr_s0frozen_v2_train_log.txt` | 07-06 の再学習成功ログ（bbox AP 68.596） |
| `discarded_cache_{val,test,train}_extract.log` | 破棄キャッシュ内の抽出ログ（正常完走の証拠） |
| `queue3.sh` | 07-03 の検出器 test 再評価キュー |
| `queue4.sh` / `queue4_v2.sh` / `queue4_parallel_extract.sh` | 07-05〜06 の S0-frozen 再学習・抽出キュー |

`/tmp` の原本は削除・移動していない（コピーのみ）。ファイル mtime は `cp -p` で保全した。
