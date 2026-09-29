# audit — T-2026-09-23-dlsta-host-fairness

実施ホスト `dlsta`（容器内。OS のホスト名は `4f3861ae8d3b`）。repo `~/local/m2`。
時刻は容器の時計（UTC）で測り、JST（+9h）を併記する。開始 2026-09-25 19:05 UTC 前後（JST 09-26 04:05）。
**数値はすべて実測である。未測定は UNKNOWN と書く。**

## 0. 開始状態

| 項目 | 実測 |
|---|---|
| 分岐 | `feat/dlsta-host-fairness`（HEAD `cb3fcaa1dc179bf54e1d201c613a4fad80b5d080`、2026-09-23 01:23 +0900） |
| `origin/phase0` | `9d6366d34c1b08002b3d742632a97c39ad3a79a4`（HEAD より先へ進んでいる。統合はしていない） |
| 開始時の変更（追跡対象） | 1 件: `docs/sessions/digest/2026-09-20-1764ac44-….md`（本契約の前から在った変更。触らず、commit に含めない） |
| 開始時の未追跡 | 1 件: `tasks/T-2026-09-23-dlsta-host-fairness/`（契約そのもの） |
| 開始前から在った未追跡で退避したもの | **0 件**（退避の必要が無かった） |
| 抑止の目印 `.sync-pause` | **開始前から在った**（mtime 2026-09-22 09:03）。契約 Task E Step 5 に従い**触らない** |
| 常駐の同期 | `~/bin/m2-sync.sh` の `sync-pause` 参照は 2 件（対応済み）。`sync-alerts.log` の `[dlsta] 一時停止中` が 18:29・18:59 UTC に出ている（抑止が効いている） |
| 装置 | RTX A5000 × 5（各 24564 MiB）。使用 22〜99 MiB、利用率 0%、**compute プロセス 0 件** |

## 1. 検証とプリフライト

- `make task-validate`: exit 0（占位の置換**前**に一度、置換後にもう一度。前者は SPEC §1 申し送りに反する。逸脱に記録）
- `make task-preflight`: exit 0。**5 PASS / 1 WARN / 8 SKIP / 0 FAIL**
  - WARN P9: `host_mismatch@SPEC.md:4`（宣言 `dlsta` と OS のホスト名 `4f3861ae8d3b` が違う。容器内であるため。
    GPU が A5000 × 5 で、`~/local/m2` が在るのは dlsta だけ〔`context/env-facts.md:21`〕なので当該ホストは dlsta と判断した）、
    `integration_prohibited_without_pause@SPEC.md:67`
  - SKIP: P2 cuda_ext_loaded / P3 deterministic_flags / P11 gpu_free（宣言なし）、P4 / P5 / P13 / P14（kind=impl）、P12（該当なし）

## Task A — 参照の特定と環境の照合

### A-1 占位の置換

| 項目 | 置換前 | 実測 |
|---|---|---|
| `contract.conventions_rev` | `UNMEASURED` | `4369cf5e7b82a3043b9b00b998911c4efb856f69`（`context/conventions.md` の最終更新 commit、2026-09-22 16:16 UTC） |
| `meta.created_from.runindex_commit` | `UNMEASURED` | `4e97b3deae28e653948c19309d229c755587c42b`（`runindex/` の最終更新 commit） |
| `meta.created_from.counts` | 0 / 0 / 0 | index 1558 / experiments 476 / verdicts 1506（`csv.DictReader` の行数） |

### A-2 参照の run

`runindex/index.csv` を `task_id` で絞った件数: 検出塔 **14**、工程塔 **168**。
**空振りでない確認**: 存在しない `T-2099-01-01-nonexistent` で絞ると **0** 件。

#### 検出塔（`T-2026-09-18-stage1-detector-towers`）

| 項目 | 値 | 出所 |
|---|---|---|
| run 名 | `dcoco_foldA_seed42`（D\*-COCO・折り A・seed 42。前契約が折り A の確定塔とした） | `test_access_ledger.csv`、audit `:238` |
| checkpoint | `experiments/baselines/stage1_dtower/dcoco_foldA_seed42/work/best_ap.pth`、sha256 `4f599354e842d35325613d7dec9de60112cb81e2cbb34895ad7f1958c4e23471`、**当該ホストに在る**。台帳の記録と一致 | 実測 `sha256sum` |
| 枚数 | 2（`accelerate launch --num_processes 2`） | `command.sh` |
| per-GPU batch / 実効 batch | 2 / 4 | `config.yaml` |
| 数値精度 | fp16 自動混合精度（`--mixed-precision fp16`）。TF32 は使わない（前契約 audit `:75-81`） | `command.sh`、前契約 audit |
| 解像度 | `presets.detr`（Relation-DETR の変換）。数値は設定ファイル側にあり**当該ホストに設定が無いため UNKNOWN** | `config.yaml` |
| 学習率 / epoch / 種 | 1e-4（milestone 10、γ 0.1）/ 12 / 42 | `config.yaml` |
| 記録されたホスト | **efros**（`server.txt` は空。`tf_log/events.out.tfevents.1789684007.efros.263975.0` と前契約 audit `:3`） | ファイル名、audit |
| 一歩ごとの損失 | **在る**。`work/training.log` に 50 step 間隔（epoch あたり 2405 step） | 実測 |
| step 時間の記録 | 在る。`iter_time`（例 epoch 0 の 50 step 目 0.5849 s） | `training.log` |

#### 工程塔（`T-2026-09-19-stage1-phase-tower-r2`、確定 recipe）

確定 recipe は「候補 C・6 層・平滑化 0.15・履歴 30・backbone 学習率 1e-4」（前契約 RESULT `:269`）。
塔は二段: backbone の fine-tune（run 001）→ 特徴の抽出（run 014）→ 時間ヘッドの学習（run 028）。

| 項目 | 値 | 出所 |
|---|---|---|
| run 名 | fine-tune `stage1_ptower_r2_001_ft_lr0.0001_foldA_seed42`、ヘッド `stage1_ptower_r2_028_P15_C_L6_w0.15_h30_foldA_lr0.0001_seed42` | `runindex/index.csv` |
| checkpoint | backbone `…_001_…/checkpoints/best.pth` sha256 `7f4ab1f99a2ec03039581a9a773b7faef247191f2cf64a441d124ccbfd4bb170`（前契約 audit `:94` と**一致**）、ヘッド `…_028_…/checkpoints/best.pth` sha256 `630fe5a9a639b0bfb3c64e9fa01c9ce820544cf77c0379e268c4fa82cb1f6230`（記録に比較対象なし）。**どちらも当該ホストに在る** | 実測 |
| 枚数 | 1（`device=cuda:0`） | `command.sh` |
| per-GPU batch / 実効 batch | fine-tune 64 / 64。ヘッドは 1 動画 = 1 batch | `config.yaml` |
| 数値精度 | fp32。TF32 は matmul・cuDNN とも**能動的に False**、`use_deterministic_algorithms(True)`、`cudnn.benchmark=False` | `scripts/stage1_ptower.py:93-104`（コードが設定するため当該ホストでも同じ） |
| 解像度 | 224（resize 256 → crop 224） | `config.yaml` の `transform_train` |
| 学習率 / epoch / 種 | backbone 1e-4（wd 1e-4、12 epoch、AdamW）/ ヘッド 5e-4 / 種 42 | `config.yaml` |
| 記録されたホスト | **ilya**（`server.txt`） | 実測 |
| 一歩ごとの損失 | **無い**。epoch 平均だけ（`finetune_history.json`、W&B も `step=epoch`。`scripts/stage1_ptower_r2.py:155`） | 実装と記録 |
| 所要 | fine-tune 411.39905246999115 秒（12 epoch、val 評価を含む） | `metrics.json` |
| 実行時のコード | `stage1_ptower.py` の sha256 `4ec5b574…` は記録の `source_sha256` と**一致**。`stage1_ptower_r2.py` は記録の `git_commit.txt`（8aa636bf）に**まだ無く**、変更した commit は 029b5315 の 1 件だけ。**実行時点の要約値は UNKNOWN** | `git log`、実測 |

**利用者の判断（2026-09-26 JST）**: 一歩ごとの損失が無いため停止して諮った。**epoch 平均損失（12 点）で代替する**と決まった。

**選んだ理由**: 検出塔は前契約が確定塔とした折り A seed 42。工程塔は確定 recipe の折り A seed 42（ヘッド 028 が使う backbone は 001 と同じ種）。
二周目の検出塔 `experiments/baselines/stage1_dtower_r2/` は `work/` だけで索引に 0 件であり、参照にしない。

### A-3 版の比較

| 項目 | dlsta（実測） | efros（検出塔の参照） | ilya（工程塔の参照） |
|---|---|---|---|
| 装置 | RTX A5000 × 5（24564 MiB） | RTX A6000 × 2（前契約 audit `:3`） | RTX 6000 Ada × 2（r2 audit `:29`、一周目 audit `:28`） |
| driver | 595.84（`nvidia-smi` の CUDA 表示 13.2） | 595.84 | **UNKNOWN** |
| nvcc | 12.9（V12.9.86） | 12.9 | **UNKNOWN** |
| torch | 2.1.2+cu118（CUDA 11.8） | 2.1.2+cu118 | **UNKNOWN** |
| cuDNN | 8700 | **UNKNOWN** | **UNKNOWN** |
| torchvision | 0.16.2+cu118 | **UNKNOWN** | **UNKNOWN** |
| mmcv / mmdet | 2.1.0 / 3.3.0 | **UNKNOWN**（検出塔は別 venv の Relation-DETR で動き、mmdet を使わない） | **UNKNOWN** |
| Python | 3.11.16 | **UNKNOWN** | **UNKNOWN** |
| repo の commit | `cb3fcaa1`（HEAD） | `feat/stage1-detector-towers` の先頭（`git_commit.txt` は ref だけで要約値なし）→ **UNKNOWN** | `8aa636bf`（`git_commit.txt`。ただし実行コードは未 commit を含む） |
| lock の要約値 | `uv.lock` sha256 `69212cb0ca8895aff8376d4aca0f6e11840d2ca5270fc2b01da034227e87f3e3` | **UNKNOWN** | **UNKNOWN** |
| 学習コード | **検出塔: 無い**（`third_party/Relation-DETR` はキャッシュの残骸 25 ファイルだけで `main.py` も設定も無い）。工程塔: 在る | 在る | 在る |

**差分の列挙**（記録が在る項目だけ）:
1. 装置の型番: dlsta A5000 / efros A6000 / ilya 6000 Ada（3 台とも異なる）
2. 記憶容量: dlsta 24 GB / efros 48 GB（A6000 の仕様。記録は型番のみ）/ ilya 48 GB（同）
3. 検出塔の学習コードの有無: dlsta に無い
4. 枚数: dlsta 5 / efros 2 / ilya 2
driver・nvcc・torch は dlsta と efros で一致。ilya は記録が型番だけで比べられない。

### A-4 データと凍結源

| 対象 | dlsta の sha256 | 記録 | 判定 |
|---|---|---|---|
| 検出の折り A 注釈 train | `fc63621ea496ccdc7f49099b1f0b58763d3302e13611f40d6812e258f829db2f` | `fc63621ea496ccdc…`（検出塔 audit `:113`） | 一致（先頭 16 桁） |
| 同 val | `db605c06626ff82407f88d9342af339914bda1c24c2ee291fc860cd46542c615` | `db605c06626ff824…` | 一致（先頭 16 桁） |
| 同 test | `f4ce5243fd01fc6e856a5747de6ef38f8e91eec7e7c17da1de25178b011cfa88` | `f4ce5243fd01fc6e…` | 一致（先頭 16 桁） |
| 工程の特徴キャッシュ（折り A seed 42） | `3c5f9a12e6e38477d4ed24b4b307d0c6e239f8515545b48f28eaa9a0dcf56c37` | ヘッド 028 の `cache_sha256` | 一致（全桁） |
| 工程 backbone ckpt | `7f4ab1f9…`（上記） | r2 audit `:94` | 一致（全桁） |
| 検出塔 ckpt | `4f599354…`（上記） | `test_access_ledger.csv` | 一致（全桁） |
| 凍結源（`conventions#frozen_source`） | **当該ホストに無い**（同定パス `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth` が不在） | `03936318…` | **照合不能**。本契約は凍結源を読まない（検出塔の短い学習の初期値は COCO 重み）ため停止しなかった |
| 工程マニフェスト | train `f8bee9f9…` / val `9f935375…` / test `f2077541…` / vocab `ad3c1e4a…` | 要約値の記録なし。件数は記録 train 9657 / val 1515（run 001 `config.yaml`） | 件数の照合は Task C の実行ログで行う |
| 折り表 `docs/stage0/A1_fold_table.md` | `eb66170a…` | 記録なし | — |

### A-5 装置間の接続（`nvidia-smi topo -m`）

| | GPU0 | GPU1 | GPU2 | GPU3 | GPU4 | NUMA |
|---|---|---|---|---|---|---|
| GPU0 | X | NODE | NODE | SYS | SYS | 0 |
| GPU1 | NODE | X | **NV4** | SYS | SYS | 0 |
| GPU2 | NODE | **NV4** | X | SYS | SYS | 0 |
| GPU3 | SYS | SYS | SYS | X | **NV4** | 1 |
| GPU4 | SYS | SYS | SYS | **NV4** | X | 1 |

NVLink（4 本束）で結ばれた対は GPU1–GPU2 と GPU3–GPU4 の 2 組。GPU0 は NVLink を持たない。
二枚の処方を回すなら対（1,2）か（3,4）に置けば同じ形になる。参照ホスト側の接続の記録は **UNKNOWN**。

### A-6 使う画像の集合（工程塔・折り A）

| 項目 | 実測 |
|---|---|
| train + val の画像 | 11172 枚（train 9657 + val 1515。記録 run 001 の `config.yaml` と一致）、**欠損 0** |
| パス集合の sha256 | `c72e2cab03819932bad7e09de16ca52ad4c374454dc52b08e44ef9ba81778eb1`（パスの一覧の要約値。画像の中身の要約値ではない） |
| 陽性対照（先頭 1 件を除いた集合） | `5283360f42c551eb46e0447ce3ec4f1be3b3416af8a73b0640ba51fe095c92d8`（**変わった**） |
| 記録側の同じ要約値 | **UNKNOWN**（記録に無い。件数だけを照合した） |

## 利用者の判断（2026-09-26 JST、対話）

1. 工程塔 Task C: 一歩ごとの損失が無い → **epoch 平均損失 12 点で代替**
2. 検出塔: 当該ホストに Relation-DETR の本体が無い → **取り寄せず「判定不能」**
3. 工程塔: 出力先が `experiments/` 固定・W&B 必須 → **コードを変えず repo 外の写しからオフラインで実行**

## 実行の仕組み（判断 3 の実装）

- 写し: `git archive HEAD scripts src configs docs/stage0/A1_fold_table.md tasks/T-2026-09-19-stage1-phase-tower-r2/spec.yaml` を
  セッションの scratch（`/tmp/claude-1000/…/scratchpad/fair/repo`）へ展開。写しの `stage1_ptower.py` / `stage1_ptower_r2.py` の sha256 は元と一致
- データ: `data/raw`・`data/splits`・`data/processed/phase_manifest` へのシンボリックリンク（読むだけ。書き込み先は写しの `experiments/`）
- W&B: `WANDB_MODE=offline`、`WANDB_API_KEY` は**秘匿でない占位文字列**（実鍵は読んでいない。`load_env.sh` も使っていない）、`WANDB_DIR` は scratch。
  `wandb_run.json` に `run_url` が無く、`offline-run-20260925_191659-oql7ti4w` が作られた（送信なし）
- 記録上のサーバー名は `dlsta`（写しの run の `server.txt`）
- 評価と step 時間は写しに置いたハーネス 2 本（`eval_phase_tower.py`・`step_time_phase.py`）で測った。**既存関数を import するだけで学習・評価コードは変更していない**

## Task B — 評価の再現（工程塔）

コマンド（写しの中、GPU2）:
`python eval_phase_tower.py stage1_ptower_r2_001_ft_lr0.0001_foldA_seed42 stage1_ptower_r2_028_P15_C_L6_w0.15_h30_foldA_lr0.0001_seed42 out.json` を 2 回。
backbone で fold A val（09・10）の 1515 フレームの特徴を作り、ヘッドを当てる。test 動画は読み込まない。

| | J | acc | 特徴の要約値（先頭 16） |
|---|---|---|---|
| 一回目 | 0.5089659192972632 | 0.7927392739273927 | `ba85558c9f2d2855` |
| 二回目 | 0.5089659192972632 | 0.7927392739273927 | `ba85558c9f2d2855` |
| 記録の特徴で同じヘッド | 0.5089659192972632 | 0.7927392739273927 | `d656f131042c414b`（記録キャッシュの同じ 1515 行） |
| 陽性対照: 折り B の塔（003 + 043） | 0.9543047316703157 | 0.9815181518151815 | `78cd52d87bb9c6a4` |

記録の seed 間 pstd: seed 42 / 123 / 456 のヘッド（run 028 / 033 / 038）の J から `statistics.pstdev` で 0.029117551357664122
（r2 RESULT の「最良の折り A seed 間 pstd 0.02911755」と一致）。

## Task C — 短い学習（工程塔）

コマンド（写しの中）: `python scripts/stage1_ptower_r2.py action=finetune fold=A seed=<S> ft_lr=0.0001 device=cuda:0`
（記録の `command.sh` と同じ引数）。N = 12 epoch（1812 step）。**選んだ理由**: 記録と共通する点は epoch の境目だけで 12 点しかなく、
それより短くすると共通点が減る。1 回の所要が 705.59 秒で目安の 30 分以内に収まる。

| run | GPU | 同時実行 | EXIT | checkpoint sha256 | 所要 |
|---|---|---|---|---|---|
| seed 42 一回目 | 0 | なし（単独） | 0 | `69b7682bdc91dc52a45c58c12cf55b8b84c469d67a3ce0d6f3274aac47adfa07` | 705.5881491606124 s |
| seed 42 二回目 | 1 | seed 123・評価と同時 | 0 | 一回目と同じ | `phase_tower_values.json` |
| seed 123 | 3 | seed 42 二回目・評価と同時 | 0 | `phase_tower_values.json` | 同 |

非有限の損失 0 件（スクリプトは非有限で例外を出す。3 本とも EXIT 0）。

## Task D — 記憶量と処理量（工程塔）

- ピーク: seed 42 一回目（単独）の間 `nvidia-smi -lms 500` で GPU0 を記録。最大 6355 MiB / 24564 MiB、1423 標本
- step 時間: 他の run が無い状態（compute プロセス 0 件を確認）で `step_time_phase.py 151` を GPU0 で実行。
  各 step を `cuda.synchronize` で区切る。1 step 目 1.9405 s を含む先頭 10 step と、端数 batch（57 枚）の最終 step を除き 140 step の平均 0.30079340446474295 s
- TF32 は matmul・cuDNN とも False、`are_deterministic_algorithms_enabled()` は True（ハーネスの出力で確認）
- 参照（ilya）の step 時間: **UNKNOWN**（epoch 単位の記録のみ）。全所要の比は 1.715094249547598（参考）
- 検出塔: **UNKNOWN**（コードが無い）。参照の efros の `iter_time` 中央値は 0.92575 s（`training.log` の 588 点）
- **r3 の工程塔（短辺 800・全画面）には本 Task の記憶量・処理量は当てはまらない**

## 実行者の誤り

1. **占位の置換前に L1 を回した。** 手順書の順（検証 → 実行）に従い、SPEC §1 申し送りの「置換の前に L1 を回さない」に反した。置換後にもう一度回して exit 0
2. **一回目の起動が失敗した。** 写しに `data/splits` のリンクを張り忘れ `FileNotFoundError`。リンクを足して再実行し、失敗した出力は scratch から消した（repo の外）
3. **`pkill -f "lms 500"` が自分のシェルにも一致した。** 背景処理の終了コードが 144 になった。学習自体は EXIT=0 で完走しており、`nvidia-smi` の記録も残っていた。`conventions#issuer_cautions` 注意 6 の型
