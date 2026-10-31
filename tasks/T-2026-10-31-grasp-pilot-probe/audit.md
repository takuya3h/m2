# audit — T-2026-10-31-grasp-pilot-probe（非公式の測定）

時刻は JST。ホストは andrew（`hostname` = Andrew）。版管理の外の置き場は
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe`。

## 0. 始める（手順書の 0〜4）

- 開始時の分岐は `feat/gaze-data-survey`（清浄）。`feat/grasp-pilot-probe` は手元にも遠隔にも無く、契約の履歴も `.sync-pause` も無かった
- `python3 scripts/task_start_classify.py` → 全区分 0 件、`[task-start] 分類: 通す`（比較先 origin/phase0 8d3a72b7）
- `make task-start` → `分岐を作成: feat/grasp-pilot-probe（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、`完了。`
- `make task-validate` → `OK`（WARN なし）、exit 0
- `make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL、exit 0。SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、
  P4 prereg_committed・P5 frozen_source_hash・P13・P14（kind=analysis で対象外）、P12 refs_resolved（解決前提の参照なし）

## Task A — 開始状態（G1）

### A-1 分岐と起点

    $ git branch --show-current; git rev-parse HEAD origin/phase0; git merge-base HEAD origin/phase0
    feat/grasp-pilot-probe
    8d3a72b7743a90432fa92444f820e01e07a96197   (HEAD)
    8d3a72b7743a90432fa92444f820e01e07a96197   (origin/phase0)
    8d3a72b7743a90432fa92444f820e01e07a96197   (merge-base)

### A-2 開始前から在る未追跡

- task-start の前の分類器: 追跡下の変更 0、無視されていない未追跡 0、無視された未追跡で phase0 に在るもの 0（無視・phase0 に無いものは数えない）
- task-start の後に在る無視されていない未追跡は、task-start が取り込んだ契約の 2 本だけ
  （`tasks/T-2026-10-31-grasp-pilot-probe/SPEC.md`、`spec.yaml`）。消していない

### A-3 compute プロセス（`$S/start/a3_procs.json`）

道具 `scripts/grasppilot/proc_enum.py`（本契約で新設。前回の `proc_enum.py` は残っていなかった）。`/proc/PID/exe` を解決し、
basename が python で始まるか、引数の要素が `torchrun`・`accelerate`・`deepspeed` と完全一致するか、nvidia-smi の compute の PID なら compute とする。

    $ python3 scripts/grasppilot/proc_enum.py
    n_proc 39 gpu [] n_compute 0
    exe_basenames: bash 5, codex 2, dash 3, node 6, python3.11 1（道具自身、除外）, sleep 2, ssh 1, syncthing 2, zmx 4, zsh 5, ほか claude 系
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh      → count 5（自分のシェル PID 401469 を含む）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9   → count 0

- `/proc/PID/exe` は他の利用者の PID を読めない。補完として `ps -eo pid,user,comm,args` で全利用者（root 2、ubuntu 50）の comm が
  python・torchrun で始まるものを数えた → 0 件
- nvidia-smi: GPU 0・1 とも 16 MiB 使用、compute アプリ 0 件
- **本契約以外の compute プロセスは 0 件**

### A-4 記憶領域

    $ df -B1 /home/ubuntu/slocal2
    /dev/sdc1  7937302376448  5858837729280  1678369779712  78%

空き 1,678,369,779,712 B。見積もり（上限側）: Mask2Former の新しい仮想環境 ≤ 15 GB、COCO の重み ≤ 3 GB（候補 2 つ）、
正解の信号（g・q・s・特徴の写し）≤ 2 GB、案 B の地図は保存せず注釈から都度作る、界面の重み 4 本 ≤ 1 GB、予測と記録 ≤ 5 GB。
合計 ≤ 26 GB（空きの 1.6%）。足りる。

### A-5 試験（開始時、`$S/start/a5_pytest_start.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 970 passed, 5 skipped, 26 warnings in 27.91s

失敗の名前（andrew の開始時の集合）:

    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

### A-6 既存の仮想環境のパッケージの一覧（`$S/start/a6_pkgs_*.txt`）

    $ uv pip list --python <venv>/bin/python --format freeze > ...; sha256sum
    .venv                 108 行  sha256 9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0
    .venv-relation-detr    72 行  sha256 a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090

### A-7 起票時の値

    $ git log -1 --format=%H -- context/conventions.md   → 2d946b07a57abebc4a8f66150d6dbaf2ccd22186（契約の conventions_rev と一致）
    $ git log -1 --format=%H -- runindex/                → 68befc3b62ffc071077cca446df5d3c83b8c38b9（created_from.runindex_commit と一致）
    行数（見出しを除く）: index 2363、experiments 1130、verdicts 1736（created_from.counts と一致）

差し替えは無い。`meta.amendments` は空のまま。

### G1 の判定

分岐 `feat/grasp-pilot-probe`、起点 origin/phase0 8d3a72b7、本契約以外の compute プロセス 0 件、空き・失敗の名前・仮想環境の要約値を記録した。**通過。**

## Task B — 注釈と材料（G2）

### B-1・B-2 把持の三種の注釈の同定（`$S/b/b1_ann_check.json`、道具 `scripts/grasppilot/ann_check.py`）

    $ PYTHONPATH=src .venv/bin/python scripts/grasppilot/ann_check.py --out $S/b/b1_ann_check.json
    hand_seg      train 9627 val 1515  matches ['hand_seg']           outside [] []
    hand_tool_seg train 9356 val 1514  matches ['hand_tool_seg_v2']   outside [] []
    tool_seg      train 9528 val 1512  matches ['tool_seg']           outside [] []

- フレーム数 = 注釈が 1 件以上ある画像の数（どのファイルも images の全件に注釈がある）。test と extra のファイルは開いていない
- **`hand_tool_seg/` のフレーム数は被覆の文書 §3 の現行版（`hand_tool_seg_v2`）の値と一致する。** 旧版（65.82%）の値ではない。
  `egosurgery_hts/README.md` §8 は 2026-07-31 に `hand_tool_seg_v2/` を `hand_tool_seg/` へ統合したと書く。`hand_tool_seg_v2/` というディレクトリは在処に無い
- クラス: 把持関係 5（1 自分の左手、2 自分の右手、3 Left Hand Tool、4 Right Hand Tool、5 Two Hands Tool）、手 4（自分の左・右、他者の左・右）、術具の分割 31
- 欠落の印 `hand_tool_seg/loss_mask/{train,val}.txt`（301・1 件）: 術具の枠のフレームのうち把持関係の注釈が無いフレームの一覧と**完全に一致**し、
  5 クラスの注釈のあるフレームとの共通は 0 件（README: Mouth Gag・Skewer だけを含む構造的欠落、学習時に除外）
- 使ったファイルの動画: train {01,02,03,06,08,11,12,13,14,15}、val {09,10}（三種とも）。折り A の train・val と一致、test との共通 0 件
- 空振りの確認: 5 クラスの train を 1 件除いた数では一致する文書の値が無くなる（`match_one_frame_dropped.hand_tool_seg = []`）。
  train に `04_1_0001` を足した写しでは外れが `['04']` の 1 件

### B-5 注釈のあるフレームの数

| split | 工程注釈のあるフレーム | うち注釈のあるフレーム | 術具注釈のあるフレーム | うち注釈のあるフレーム |
|---|---:|---:|---:|---:|
| train | 9,657 | 9,356 | 9,657 | 9,356 |
| val | 1,515 | 1,514 | 1,515 | 1,514 |

工程のマニフェスト（`data/processed/phase_manifest/{train,val}.json`）は術具の枠と同じフレーム集合である（工程注釈 CSV の 17,233 ではない）。
そのため注釈の無い工程のフレームは train 301（3.1%）・val 1（0.07%）で、SPEC §6.4 の「約 13%」（CSV を分母にした値）とは違う。

### B-3 材料（`experiments/analysis/grasp_pilot_probe/repro/b3_sha256.txt`）

| 材料 | sha256 | 記録 |
|---|---|---|
| `PT_CACHE` | c402e214…f172da | 一致（four の material_four.json） |
| `PT_HEAD_CKPT` | 0d76d446…c6ad6d | 一致（同） |
| `PT_FT_CKPT` | 79c2c478…f6b | folda の audit.md に在る |
| `DET_CKPT` | 30d199b1…682c4 | **`DET_SHA256` と一致** |
| マニフェスト vocab・train・val | ad3c1e4a…・f8bee9f9…・9f935375… | 一致（four の inputs/andrew_manifest.txt） |
| 術具の注釈 折り A train・val | fc63621e…・db605c06… | train は four の input_digest_bengio.json に在る。val は前回の記録に見当たらない（照合できない） |

### B-4 塔単独の val の再現（`experiments/analysis/grasp_pilot_probe/repro/run_repro.sh`）

| 塔 | 指標 | 再現 | 記録 | 差 |
|---|---|---:|---:|---:|
| 工程 | macro Jaccard | 0.7762185528 | 0.7762185528 | 0.0 |
| 工程 | frame accuracy | 0.8712871287 | 0.8712871287 | 0.0 |
| 検出 | overall mAP | 0.7273450248 | 0.7273450248 | 0.0 |
| 検出 | 標的群 AP | 0.7950748009 | 0.7950748 | < 1e-7 |
| 検出 | 陰性対照群 AP | 0.6726631818 | 0.6726632 | < 1e-7 |

- 拡張の読み込み: `[env] torch 2.1.2+cu118 cuda True ms_deform_attn_ext True`
- 対照（§8-c）: 別の時間ヘッド（P20 seed 42）で Jaccard 0.6379・accuracy 0.8528。別 seed（123）の検出塔で mAP 0.72886・標的群 0.82343・陰性対照群 0.67018。
  **値は変わる。ただし検出の overall mAP の差は +0.0015 で許容差 0.005 の中に入る**（overall mAP だけでは別 seed の塔を見分けられない。標的群 AP の差 +0.028 は超える）
- 検出塔の予測（上位 300、確信度の下限なし）を `$S/b/plain_val_preds.json.gz` に保存した（Task C-4 で使う）

### G2 の判定

注釈が在り、被覆の数で同定でき、使ったファイルの動画が折り A の train・val に含まれ、材料の要約値が記録と一致し、塔単独の val が差 0 で再現した。**通過。**

## Task C — 正解の信号と学習なしの測定

### C-1 正解の信号（`$S/signals/`、道具 `scripts/grasppilot/build_signals.py`・関数 `scripts/grasppilot/grasp_signals.py`）

    $ PYTHONPATH=src .venv/bin/python scripts/grasppilot/build_signals.py --out $S/signals --workers 16   （5 分 25 秒）

| 項目 | train | val |
|---|---:|---:|
| 動画 | 01,02,03,06,08,11,12,13,14,15 | 09,10 |
| g の行（工程注釈のある全フレーム） | 9,657 | 1,515 |
| g の旗 1（注釈のあるフレーム） | 9,356 | 1,514 |
| `g_{part}.npz` の sha256 | 741cecb5d42decd7… | 235e2c2bde3a0478… |
| 正解の枠（全件） / 注釈のあるフレームの枠 | 32,272 / 31,521 | 4,707 / 4,703 |
| `boxstate_{part}.npz` の sha256 | fb7af1a3db1398a3… | 70b3f5f4f0cb4d14… |
| 地図 m の対象（術具注釈のあるフレーム） / どれかのチャネルが非零 | 9,657 / 9,356 | 1,515 / 1,514 |
| m のチャネルが非零のフレーム（tool_L, tool_R, tool_B, hand_L, hand_R） | 7129, 7176, 952, 8659, 8386 | 1231, 1274, 176, 1491, 1463 |
| s(b) τ=0.1（左, 右, 両手, なし, 注釈なし） | 7083, 6069, 845, 17524, 751 | 1255, 851, 150, 2447, 4 |
| s(b) τ=0.05 | 8115, 8199, 1032, 14175, 751 | 1480, 1387, 168, 1668, 4 |
| s(b) τ=0.2 | 4693, 3115, 522, 23191, 751 | 904, 327, 97, 3375, 4 |
| Σ r_c > 1 で 1 に切った枠 | 3 | 0 |

- 関数の sha256: `grasp_signals.py` 5dcfbc1ae9d10938…、作る台本 b6e7936c030a3580…（全桁は `$S/signals/summary.json`）
- g の二値の 5 個の注釈のあるフレームでの正例率（val）: 左手 0.985、左の把持 0.813、右手 0.966、右の把持 0.841、両手 0.116
  （SPEC §2 の linear-probe の値と一致）
- フレームの対応は名前の stem。工程のフレームと術具のフレームの集合は同じで、対応の取れない数は 0。マスクと画像はどちらも 1920×1080
- m は保存しない。学習と評価のときに注釈から作る（`HTSIndex.map_channels`）
- 枠の画素: COCO の [x, y, w, h] の floor(x)..ceil(x+w)−1、floor(y)..ceil(y+h)−1（積分画像で数える）。重心は画素の中心 (i+0.5)/W
- **g の手の存在は把持関係 5 クラスの 1・2 から読んだ（解釈）。** 手 4 クラスの自分の手との IoU は、両方があるフレームで全件 1.0
  （E-2）なので、どちらから読んでも同じ値になる

### C-2 試験（`tests/test_grasppilot_signals.py`）

    $ CUDA_VISIBLE_DEVICES="" .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_grasppilot_signals.py
    5 passed

人工のマスク（矩形の面積・重心・枠との重なり、確率の地図の最大・和・重み付き重心、Σ>1 の切り）と、空のマスク（全 0）を当てた。

### C-4 検出塔の誤りの数え上げ（`experiments/analysis/grasp_pilot_probe/taskC/c4_error_count.json`）

    $ PYTHONPATH=src .venv/bin/python scripts/grasppilot/error_count.py --preds $S/b/plain_val_preds.json.gz --boxstate $S/signals/boxstate_val.npz --out ...

- 予測は B-4 の塔単独の再現の予測（上位 300、確信度の下限なし）。正解の枠 4,707（全件に状態あり）
- 要約（τ=0.1、s*=0.3、全体）: 誤り 469、握られている枠が誤りに占める割合 0.4563、全枠に占める割合 0.4793
- 空振りの確認: 検出を 1 件（ann 318 を同じクラスで覆う唯一の検出）消すと、その枠が correct → missed へ移り、変わった枠は 1 件だけ。
  正解の枠を確信度 1 の検出として足すと、見逃しは 59 → 0

### C-3 工程塔の特徴から g を読む検査（`experiments/analysis/grasp_pilot_probe/taskC/c3_probe_phase.json`）

    $ PYTHONPATH=src OMP_NUM_THREADS=16 .venv/bin/python scripts/grasppilot/probe.py phase --signals $S/signals --out ...

- 特徴は `PT_CACHE` の注釈のあるフレーム（train 9,356、val 1,514）。train で標準化して当てはめ、val で測る
- 正則化は測る前に固定: ロジスティック回帰 C = 1.0、リッジ回帰 α = 1.0（max_iter 3000）。val の値で選び直していない
- 陽性対照は術具の正解の在否のうち train と val の両方で正例と負例のある 14 クラス（Retractor は除外。val に正例が無い）
- 値の表は REPORT.md に置く

## Task D — 案 A と案 B の空と正解の腕（G3）

### D-1 案 A の実装（`scripts/stage2pilot/dp_train.py` に型 `GA` と引数 `--grasp-signal-dir` を足した。既存の型の経路は変えない）

- x(t) 30 次元 = ［予測の半分 0..14（g の 14 と旗）｜正解の半分 15..29］。空の腕は全 0。正解の腕は正解の半分に g と旗（`g_{part}.npz` の flag）
- 界面は D1 concat（`DPReceiver(head, "concat", 30)`、`Conv1d(30, 64, 1, bias=False)`、零初期化、1,920 個）

### D-2 案 B の実装

- データ: `scripts/grasppilot/pd_grasp.py`（`presets.detr` の変換の列を最後の `SanitizeBoundingBox` を除いて使い、地図を `datapoints.Mask` として
  画像・枠・ラベルと同じ一度の呼び出しに入れる。Sanitize は元の位置で画像・枠・ラベルだけに当てる）
- 型: `scripts/grasppilot/pd_grasp_model.py`（`RelationDETRGraspMap`、`phase_iface = Conv2d(5, 2048, 1, bias=False)` 零初期化）。
  T の評価時の分（eval_transform と詰め物）はモデルの中で地図を `images.image_sizes` へ最近傍で合わせ、詰め物の部分を 0。
  **R は詰め物まで含めた格子から C5 の格子への `adaptive_avg_pool2d`（32×32 画素の平均）**
- 設定: `configs/stage2pilot/pd_graspmap_d5.py`（`pd_film_d9.py` の写しで検出器のクラスの行だけを変えた）
- 経路: `scripts/train_t1b.py` に `--grasp-map {zero,gt}` を足した（渡さなければ従来の経路のまま）。`eval_detection` は検出器が
  `set_grasp_maps` を持つときだけ地図を渡す
- 台本: `scripts/grasppilot/run_pd_grasp.sh`、後処理 `scripts/grasppilot/pd_grasp_finalize.py`

### D-3 地図の幾何の対応（`experiments/analysis/grasp_pilot_probe/geom/d3_geom_check.json`）

    $ CUDA_VISIBLE_DEVICES="" python scripts/grasppilot/geom_check.py --out ...    （.venv-relation-detr）

| 段 | 対応（平均 / 中央値） | 対照: 左右反転の地図 | n |
|---|---:|---:|---:|
| 学習時の変換の後（train 200 枚、seed 42） | 0.9771 / 0.99996 | 0.3926 / 0.3437 | 188 |
| 変換の前（同じ 200 枚） | 0.9772 / 0.9980 | 0.3855 / 0.3362 | 193 |
| 評価時の経路の C5 の格子（val 50 枚） | 0.9862 / 1.0 | 0.3373 / 0.2864 | 50 |

- 200 枚すべてで変換の前後で大きさが変わった。器具の質量が 0 の枚（切り出しで落ちたものを含む）は除いた
- C5 への縮小の前後で質量の比は 1.0（50 枚すべて）

### D-4・D-5 学習する集合と恒等性

| 案 | 腕 | 学習前の val | 塔単独との差 | 陽性対照（重み N(0, 0.05²)） |
|---|---|---|---|---|
| A | 空 | Jaccard 0.7762185528（記録と同値） | ロジットの差の最大 0.0 | 零の信号では変わらない（差 0.0） |
| A | 正解 | 同上 | 0.0 | Jaccard 0.7630357、ロジットの差の最大 0.3322 |
| B | 空 | mAP 0.7273450248 | score・枠の差 0.0、ラベルの食い違い 0 | 零の地図では変わらない（差 0.0） |
| B | 正解 | mAP 0.7273450248 | 0.0、0 | mAP 0.7278873、score の差の最大 0.3827 |

- 学習する集合: 案 A `['iface.weight']`（受け取り手の 1 個を混ぜると不一致）、案 B `['phase_iface.weight']`（10,240 個。`backbone.conv1.weight` を混ぜると不一致）
- 記録: `experiments/analysis/grasp_pilot_probe/identity/`

### G3 の判定

全腕で学習前の出力が塔単独と一致し、陽性対照で出力が変わり、地図が学習時の変換に従うこと（対応 0.977 > 対照 0.393）を示し、
学習する集合が界面のパラメータだけで、通した動画は train {01,02,03,06,08,11,12,13,14,15}・val {09,10}。**通過。**

### D-6 run

- 案 A: `experiments/phase1/grasppilot_dp_001_GA_empty_ep4_seed42`、`grasppilot_dp_002_GA_gt_ep4_seed42`（GPU 0、各 0.75 秒の学習）
- 案 B: `experiments/phase1/grasppilot_pd_B_empty_ep4_seed42`（GPU 0）、`grasppilot_pd_B_gt_ep4_seed42`（GPU 1）。2026-10-31 22:09 JST に起動
- 試走（腕ではない）: `$S/smoke/grasppilot_pd_B_gt_ep4_seed42_smoke`（1 epoch・6 step・val 20 枚、`phase_grad=True`）
- 一度目の案 A の起動は `/usr/bin/time` が andrew に無く rc=127 で何も走らずに終わった（実験フォルダは作られていない）

### C-6 案 C の材料（`$S/signals/summary.json` の `caseC_*`）

- 術具の分割のクラス 31（id 13 Mouth Gag と 28 Suture, Suture Needle は注釈 0 件）。クラスごとのインスタンス数とフレーム数は summary.json
- 14 種か検出塔の 15 クラスへの対応を書いた文書: **在る**。`docs/hts_phase_tool_annotation_stats.md` §2（術具の分割の 31 クラスのうち 15 クラスの名前の部分は、
  Mouth Gag を除く 14 クラスで術具の枠とインスタンス数・写るフレームが完全に同じ。Mouth Gag は術具の分割に 0 件）。論文の 14 種との対応表は見つけていない
- 手ごとに握られている術具のクラス（M_h,器具 と重なりの画素が最大の術具の分割のインスタンス。`__not_grasping__` は M_h,器具 が空、`__none__` は重なり 0）:
  train 左 21 種（Tweezers 4130、not 2227、Gauze 1079、Suction Cannula 667、none 327、…）、右 24 種（not 2180、Needle Holders 2113、Scissors 1257、…）、
  両手 20 種（not 8404、Electric Cautery 280、BiClamp 118、…）。val 左 14・右 16・両手 12 種。全表は summary.json

## Task E — 調査

### E-2 三種の注釈を一つの塔で賄う形（`$S/signals/summary.json` の `combos_hts_hand_tool`・`E2_*`）

三種（把持関係 5・手 4・術具 31）の有無の組み合わせのフレーム数（術具注釈のあるフレームを母集団。並びは 把持関係・手・術具）:

| 組み合わせ | train | val |
|---|---:|---:|
| 111 | 9,269 | 1,511 |
| 110 | 87 | 3 |
| 011 | 236 | 1 |
| 010 | 35 | 0 |
| 001 | 23 | 0 |
| 000 | 7 | 0 |

- 把持関係の「扱う器具」のインスタンスと術具の分割のインスタンスの IoU の最大（train）: 左 n 7129、中央値 1.0、10% 点 0.114、≥0.5 が 6326、<0.1 が 696、
  術具のインスタンスの無いフレーム 36。右 n 7176、10% 点 1.0、<0.1 が 404。両手 n 952、10% 点 0.070、<0.1 が 110。val は左 <0.1 が 252/1231
- 把持関係の手（1・2）と手 4 クラスの自分の手: 両方があるフレームで IoU は全件 1.0（train 左 8659・右 8386、片方だけのフレーム 0）。同じマスクである

ラベルの集合の作り方の候補（**選ばない**）:

| 候補 | 使えるフレーム（train / val） | 賄える信号 | 実装の可否 |
|---|---|---|---|
| 1. 把持関係 5 クラスだけ | 9,356 / 1,514 | 案 A・B（手の 2 チャネルは同一マスク）・D。案 C の術具の種類は出ない | 両候補とも既存の頭のクラス数を変えるだけ（E-1 で一歩を測った集合） |
| 2. 三種を合わせた一つの集合（把持関係 5 + 他者の手 2 + 術具 31、自分の手は把持関係の 1・2 と同一なので一度だけ） | 三種すべて 9,269 / 1,511 | 四案すべて | クラス数 38 の instance の頭。器具は「扱う器具」と術具の分割で同じ画素が二つのインスタンスになる（IoU 中央値 1.0）ため、重なりを許す instance の形にする |
| 3. 候補 2 の集合で、欠けた種類のクラスを損失から外す | いずれか一つ 9,650 / 1,515 | 四案すべて | 種類ごとに照合と損失を分ける印が要る。mmdet・HF とも頭の損失を写した派生の型が要る（third_party・既存の環境は変えずに書ける見込み。未実装） |

### E-1 G の構造の候補（`experiments/analysis/grasp_pilot_probe/taskE/`、道具 `scripts/grasppilot/g_bench.py`）

| 候補 | 出所と版 | 使用許諾 | 独自の CUDA の演算 | COCO の重み | 取得元・andrew から | sha256 |
|---|---|---|---|---|---|---|
| mmdet | mmdet 3.3.0 / mmcv 2.1.0（**既存の `.venv` をそのまま使う。変えない**）、設定 `mask2former_r50_8xb2-lsj-50e_coco.py` | Apache-2.0（mmdet・mmcv） | 要（mmcv の `MultiScaleDeformableAttention`）。導入済みの mmcv の `_ext` に `ms_deform_attn_forward` が在り、読み込めた（組み立ては不要） | instance、R50、lsj 50e | download.openmmlab.com、HTTP 200 | 41b088b62838c986…（ファイル名の 41b088b6 と一致） |
| hf | transformers 4.44.2（既存の `.venv`）、`Mask2FormerForUniversalSegmentation` | Apache-2.0（transformers）。重みのカードの許諾は確かめていない | 不要（変形注意は PyTorch の実装） | instance、Swin-T（`facebook/mask2former-swin-tiny-coco-instance`。HF に R50 の COCO instance は無い） | huggingface.co、HTTP 200 | model.safetensors 3550e8b21381d082… |
| official | facebookresearch/Mask2Former（detectron2 と独自の MSDeformAttn の組み立て） | MIT（Mask2Former） | 要（組み立てが要る） | — | — | **未測定**: 本契約の保存先の下の新しい仮想環境で取得と組み立てを試みる命令を、実行基盤が「外部のコード」として拒んだ。回避していない |

- 重みは `$S/e/weights/` に置いた（既存の場所を使っていない）。HF は `HF_HUB_OFFLINE=1` で保存先から読んだ
- 推論の確認（val の 09_1_0446 の 1 枚、`e1_check_*.json`）: mmdet は 610 個の重みを全部読み、100 件の予測のうち score ≥ 0.5 が 3 件、
  マスク 100 × 750 × 1333。HF は 100 query のうち ≥ 0.5 が 7 件（上位は person・bed）。どちらも通った
- 重みの照合の空振りの確認: 期待の値を 1 文字変えた照合は拒まれる（`weight_tampered_copy_rejected: true`）
- 一歩と推論の速さの計測は、案 B の学習と GPU を分けると歪むため、案 B の学習の後に行う（下に追記）

### E-3 学び直しの費用（記録から）

| 塔・段 | 処方 | 上限 | 収束規則 | 回した | 最良 | 壁時計・ホスト |
|---|---|---:|---|---:|---:|---|
| 工程塔 fine-tune（`STORE/efros_ptower/.../stage1_ptower_20_005_...`） | R50 COCO 初期化、stem 凍結、短辺 800、反転、batch 16 × accum 4、AdamW lr 1e-4 wd 1e-4、単精度、選択は val frame accuracy | 36 | 停滞 4 で lr × 0.1、再停滞で打ち切り | 21（lr 低下 17） | 13 | 16,076 秒（4.47 時間）、efros、最大確保 29.05 GB |
| 工程塔 特徴（`..._008_features...`） | fine-tune の best で 15,437 フレームの GAP | — | — | — | — | 366 秒、efros |
| 工程塔 時間ヘッド（`..._009_P15_C_L8...`） | TeCNO C 8 層、lr 5e-4 wd 0.01、平滑化 0.3、warmup 2、選択は val Jaccard | 50 | 停滞 10 で打ち切り | 18 | 8 | 7.1 秒、efros |
| 検出塔（`experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42`） | Relation-DETR R50、COCO 1x 初期化、presets.detr、2 GPU × batch 2、AdamW lr 1e-4 wd 1e-4、fp16、max_norm 0.1 | 36 | 停滞 4 で lr × 0.1（epoch 9）、再停滞で打ち切り（epoch 14） | 15（0〜14） | 10 | 9:58:04（2 GPU）。**ホストは記録に無い（UNKNOWN）** |

### E-4 補助の頭の付け所（実装はしない）

- 案 C・fine-tune の段: `scripts/stage1_ptower_r3.py:100-118`（`build_backbone` が torchvision R50 の `fc` を工程 9 の線形に替える）、損失は
  `scripts/stage1_ptower_r3.py:218`（`loss = ce(model(images), y)`）。`model` を包む派生（`fc` の前の GAP 特徴に 45 次元の線形の頭を並べ、損失を足す）を
  別の台本に書けば、既定の挙動と third_party を変えずに付けられる。学び直しの後は特徴の取り出し（`stage1_ptower_r3.py:290-296` `_features`、
  記録 366 秒）と時間ヘッドの学習（7.1 秒）をやり直す要がある
- 案 C・時間ヘッドの段: `scripts/stage1_ptower.py:578-635`（`train`。損失は 619-631 行）。凍結特徴の上の頭なので学び直しは数秒だが、
  特徴そのもの（fine-tune の段）は変わらない
- 案 D・照合の結果: `third_party/Relation-DETR/models/bricks/set_criterion.py:120-128`（`calculate_loss` の中で `self.matcher` が indices を返す）。
  `HungarianMatcher` の forward に前向きのフックを掛けるか、`RelationDETR` の派生（`scripts/` に置く。`pd_grasp_model.py` と同じ作法）で
  `criterion` を包めば、third_party を変えずに主経路の indices を取れる
- 案 D・対応した query の decoder の出力: `third_party/Relation-DETR/models/bricks/relation_transformer.py:357`（`class_head[layer_idx](self.norm(query))`）。
  C-5 と同じく最終層の `class_head[-1]` の入力をフックで取れる。学習時の decoder の入力は denoising の query が主経路の 900 の前に連結され
  （`relation_detr.py:99-107` の `dn_post_process` が分ける）、hybrid の経路（`relation_transformer.py:145`、`skip_relation=True`）は decoder を
  もう一度呼ぶ。フックは一度の順伝播で 2 回呼ばれるため、`skip_relation` を見て主経路だけを取り、主経路の出力の末尾 900 個に照合の indices を当てる
- 検出塔の学習は third_party の `main.py`（accelerate、`util/engine.py:19` `train_one_epoch_acc`）で回した。補助の頭を付けるなら、検出器の派生を
  設定で指す形にすれば `main.py` を変えずに済む見込み（未確認）

### E-1・E-3 の計測（`experiments/analysis/grasp_pilot_probe/taskE/run_bench.sh`。**案 B の学習と同じ GPU で並べて測った**（利用者の指示「計算リソースすべて使ってなるべく早く」、`gpu_shared_with_other_runs: true`）。専有の値より遅い側に偏りうる）

| 計測 | 一歩（平均 / 中央値） | batch・入力 | 最大確保 | 推論 |
|---|---|---|---|---|
| G 候補 mmdet（R50、把持関係 5 クラス、fp32） | 0.7772 / 0.7770 秒 | 2、短辺 800（32 の倍数へ詰める） | 10.02 GB | 4.21 枚/秒（batch 1） |
| G 候補 hf（Swin-T、同） | 1.0585 / 1.0724 秒 | 同 | 14.62 GB | 4.62 枚/秒 |
| 工程塔 fine-tune | 0.9978 / 1.0014 秒（batch 16 の順・逆伝播。4 歩ごとに更新） | 16 × 3 × 800 × 1422 | 28.80 GB | — |
| 検出塔 全体（fp16、1 GPU） | 0.6421 / 0.6477 秒 | 2（presets.detr） | 12.54 GB | — |

- 立ち上がり 10 歩を除いた 60 歩。データの読み込みの待ちは含まない（GPU の計算だけ）
- mmdet の一回目は `gt_sem_seg = None` を入れられず、二回目は LSJ の設定の前処理が 1024×1024 へ詰めるため入力と合わず失敗した（`e1_bench_mmdet_try{1,2}_failed.log`）。
  三回目は前処理の batch_augments を外し、hf と同じ入力で測った

費用の式（E = epoch 数。ラベルの集合は把持関係 5 クラス、batch 2、1 GPU、上の一歩の時間。読み込みの待ちを含まない）:

- 一 epoch の歩数: 確定の G 9,356 枚 → 4,678 歩、H1 3,913 枚 → 1,957 歩、H2 5,443 枚 → 2,722 歩（注釈のあるフレーム）
- mmdet: 確定 3,635 秒 + H1 1,521 秒 + H2 2,115 秒 = **7,271 秒 × E（2.02 時間 × E）**
- hf: 4,949 + 2,071 + 2,880 = **9,900 秒 × E（2.75 時間 × E）**
- 信号を作る推論: 確定の G で train と val の 11,172 枚（工程注釈と術具注釈のフレームは同じ集合）、交差適合の半分で train の 9,657 枚、計 20,829 枚
  → mmdet 4,947 秒（1.37 時間）、hf 4,508 秒（1.25 時間）
- 学び直し（「今の塔の処方の長さ」= 記録の回した epoch 数）:
  - 工程塔 fine-tune: 604 歩/epoch × 1.00 秒 = 604 秒/epoch、21 epoch で **12,684 秒（3.52 時間）/ 本**（記録の efros は 16,076 秒）。
    これに特徴の取り出し（記録 366 秒）と時間ヘッド（7 秒）。3 腕で 10.6 時間（1 GPU ずつ並べれば壁時計は 1 本分）
  - 検出塔: 4,809 歩/epoch × 0.642 秒 = 3,088 秒/epoch（1 GPU）、15 epoch で **46,320 秒（12.9 時間）/ 本**。3 腕で 38.6 GPU 時間
    （記録は 2 GPU で 9:58:04）。最良の epoch（工程 13、検出 10）で止める長さなら、工程 13 × 604 = 7,852 秒、検出 11 × 3,088 = 33,968 秒
- 検算: 上の積は記録した一歩の時間と歩数から計算し直したもの（REPORT.md の表と同じ）

## Task D（続き）— 案 B の二腕の終了

- 空: 起動 22:09:24、終了 00:02:29（2026-11-01）、rc 0、GPU 0。val mAP は ep0〜3 とも 0.7273450（塔単独と同値）、界面の重みは全 epoch で 0、凍結部の一致 True
- 正解: 起動 22:09:24、終了 00:05:11、rc 0、GPU 1。val mAP 0.7342 → 0.7349 → 0.7360 → 0.7366、界面の重みの L2 4.86 → 9.72、凍結部の一致 True
- 中間記録の commit 1f4af29e の push（22:24:05）は案 B の最後の run の終了（00:05:11）より前

## Task F — 集計・検証・報告

    $ .venv/bin/python scripts/grasppilot/aggregate.py --with-b --signals $S/signals --out experiments/analysis/grasp_pilot_probe/report.json
    A gt all (0.7790407, 0.8792079, d_empty J +0.0028222 acc +0.0079208) recompute_matches_record True
    B gt AP 0.7366077 target 0.8103401 control 0.6766663, d_empty +0.0092627 / +0.0152653 / +0.0040031
    $ .venv/bin/python scripts/grasppilot/make_report.py experiments/analysis/grasp_pilot_probe/report.json > .../report_tables.md

- 表の Δ は各 run の記録（案 A は予測の npz、案 B は grasppilot_metrics.json）から計算し直した。案 A の計算し直しは記録の値と一致（`recompute_matches_record: true`）
- 試験（終了時、`$S/final/pytest_end.txt`）: `6 failed, 975 passed, 5 skipped`。失敗の名前の集合は A-5 と同じ 6 件（増えていない。passed の 5 件の増加は `tests/test_grasppilot_signals.py`）
- 既存の仮想環境のパッケージの一覧の要約値（Task F で再測）: `.venv` 9c7be5c9…94c0、`.venv-relation-detr` a74c9c78…b090。A-6 と一致
- `make forbidden-check TASK=T-2026-10-31-grasp-pilot-probe` → `status: pass`、changed 131・checked 131、violations []。
  空振りの確認: 本契約の新しいファイル（REPORT.md、run の記録など）が変更として拾われ、allow_write によって許可された一覧に名前で出る
