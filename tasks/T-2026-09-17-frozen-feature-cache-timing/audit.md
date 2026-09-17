# audit — T-2026-09-17-frozen-feature-cache-timing

実施ホスト `efros`（RTX A6000 × 2 / driver 595.84 / nvcc 12.9）。JST 2026-09-17。
**数値はすべて本ホストの実測である。未測定は UNKNOWN と書く。**

## Task A — 開始状態

### A-1 作業ツリー

| 項目 | 実測 |
|---|---|
| 開始時の HEAD | `4624b002c65acf263e8821dac943de23950c6f71`（分岐 `feat/efros-syncthing-join`） |
| 開始時の未追跡 | 1 件（`tasks/T-2026-09-17-frozen-feature-cache-timing/`。本契約の取り込み分） |
| 開始前から在った未追跡 | 2 件（`docs/sessions/digest/2026-09-17-*.md`）。**実行者の操作の前**（08:53:56 UTC）に `stash@{0}`（`pre-T-2026-09-17-frozen-feature-cache-timing`）へ退避済み |
| `git stash list` の件数 | 2 |

退避先は版管理内の stash であり、実行者は消していない。

### A-2 装置（開始前）

    index, memory.used [MiB], memory.total [MiB], utilization.gpu [%]
    0, 40361 MiB, 49140 MiB, 100 %
    1, 40381 MiB, 49140 MiB, 100 %
    pid, used_gpu_memory [MiB]
    106429, 40338 MiB
    106543, 40338 MiB

`/proc/PID/exe` で解決した実体は 2 件とも
`/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11`、
所有者 `ubuntu`、cwd は本 repo。命令行は 39 GiB を確保して行列積を無限に回す占有処理で、
**利用者が「他者に取られないための仮プロセス」として置いたもの**であった（対話で確認）。
利用者の明示の許可を得て実験直前に停止した。停止直前に同一性を再確認している
（`nvidia-smi --query-compute-apps` の PID と完全一致）。

停止後:

    0, 15 MiB, 49140 MiB, 0 %
    1, 35 MiB, 49140 MiB, 0 %
    compute プロセス件数: 0

**他利用者の処理は 0 件**（`nvidia-smi --query-compute-apps=pid --format=csv,noheader` の行数を
`grep -c` で数えた。終了コードを件数として使っていない）。

### A-3 基準 run

`runindex/index.csv` を `task_id` で絞ると T-2026-08-29 の run は 16 件。うち P→D は 4 件
（`pd_refin_{empty,pred,oracle,both}_seed42`）。本契約が基準に採るのは参照入力段が空の腕
`pd_refin_empty_seed42` である。

| 項目 | 実測（記録から） |
|---|---|
| 起動命令 | `python scripts/train_t1b.py --inject film --trainable film --phase-source real --zero-ctx --seed 42 --epochs 6 --task-id T-2026-08-29-lecun-detector-env-pd --run-name pd_refin_empty_seed42` |
| config | epochs 6 / inject film / trainable film / lr 1e-4 / film_lr 5e-4 / seed 42 / phase_source real / zero_ctx true / model_cfg `relation_detr_resnet50_egosurgery_t1b.py` |
| init_mAP | 0.7302938994613697 |
| best mAP | 0.7335755045381196（epoch 2） |
| final_mAP | 0.7313710102008648（epoch 5） |
| 実施ホスト | lecun（`server.txt`・`metrics.json` の artifacts 経路） |
| 壁時計 | **証跡に無い。** 散文のみ（`tasks/T-2026-08-29-lecun-detector-env-pd/RESULT.md`「2 本並行で 1 epoch 36〜40 分、6 epoch で 1 run 約 4 時間、単独時は 2.2 it/s」） |
| GPU 時間 | **記録が無い（UNKNOWN）** |

🔴 **完了判定 a が要求する「両方の run の壁時計と GPU 時間」は、基準側が原理的に埋まらない。**
基準 run の証跡（`config.yaml` / `metrics.json` / `t1b_result.json` / `logs/`）に時間の列が無い。

### A-4 凍結範囲とキャッシュ可能な境界（実装から）

| 事実 | 出所 |
|---|---|
| backbone は ResNet-50、`return_indices=(1, 2, 3)`（= layer2/3/4 = C3/C4/C5）、`freeze_indices=(0, 1, 2, 3)`（stem と 4 段すべて凍結） | `third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery_t1b.py:42-43` |
| 凍結の実装は stem と各 stage の `requires_grad` を落とす | `third_party/Relation-DETR/models/backbones/resnet.py:438,454-458` |
| FiLM は backbone 出力の**最終レベル（C5）だけ**に当たり、その後に neck → transformer が続く | `third_party/Relation-DETR/models/detectors/relation_detr_phasefilm.py:59-74` |
| W1（`--trainable film`）は `phase` を名に含む param だけ学習 | `scripts/train_t1b.py:252-261` |
| W2 相当（`--trainable all`）は **config の `freeze_indices` 以外すべて**を学習。backbone は凍結のまま | `scripts/train_t1b.py:261` |

**したがってキャッシュが効く境界は W1 と W2 で同一であり、backbone の layer2/3/4 出力までである。**
FiLM より後段（neck・encoder・decoder・head）は重みが凍結されていても、入力が界面の重みに
依存するため毎 step 計算するほかない。

学習時の前処理は `presets.detr`（`third_party/Relation-DETR/transforms/presets.py:60-74`）で、
**乱択の水平反転・11 段の乱択解像度・乱択 crop** を含む。したがって同じ画像でも epoch ごとに
別の入力になり、**キャッシュは epoch ごとに別物を要する。**

### A-5 大きさ（実測に基づく）

| 量 | 実測 |
|---|---|
| val（原解像度 1920×1080・増強なし）の 1 画像あたり | **57,802,752 bytes**（462,422,016 bytes / 8 画像） |
| 学習時（増強後）の 1 バッチ（2 枚）平均 | **91,566,899 bytes**（最小 47,939,584 / 最大 125,239,296、n=30） |
| 同 1 枚あたり | 45,783,450 bytes |
| 学習 1 epoch 分（9,618 枚） | 4.403452e11 bytes = **440.3 GB** |
| 6 epoch 分（増強が毎 epoch 乱択のため別物） | 2.642071e12 bytes = **2.64 TB** |
| 折り A の val（1,515 枚・原解像度） | 8.757117e10 bytes = 87.6 GB |
| 15 動画分（train 9,657 + val 1,515 + test 4,265 = 15,437 枚・原解像度） | 8.923011e11 bytes = **892.3 GB** |
| 配置先の空き | **6,718,071,545,856 bytes**（6.72 TB） |

6 epoch 分は空きの 39.3%。**空きは超えない**ため escalate_if の「見積もりが空き容量を超える」には
該当しない。ただし決定に従って `data/processed/` へ置くと `.stignore:61` の `!data/processed`
により**全ホストへ複製される**（`.stignore` の規約は「`!` 付き = 同期対象」）。

### A-6 占位の差し替え

| 項目 | 実測値 | 出所 |
|---|---|---|
| `contract.conventions_rev` | `e7a5100597a79b3b9c60935bf38d232f8ae96822` | `git log -1 -- context/conventions.md`（2026-09-16 20:30:48 +0000） |
| `meta.created_from.runindex_commit` | `96eb3a1ca20ab7eb4b373d93304c9e6b33b733d5` | `git log -1 -- runindex/`（2026-08-30 10:26:08 +0000） |
| `counts` | index 1266 / experiments 285 / verdicts 1506 | 各 CSV の行数からヘッダ 1 行を引いた値 |

## 逐語で受け取った規約

`contract.inject_verbatim` は `conventions#prohibitions` / `conventions#issuer_cautions` /
`conventions#frozen_source` の 3 件。原文は `context/conventions.md`（rev
`e7a5100597a79b3b9c60935bf38d232f8ae96822`）の該当アンカーである。要約していない。

`inputs.sigma_policy` は省略されているため `conventions#sigma` の既定値を継承する
（`series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired`）。
**本契約は sigma を使う判定を持たないため、継承したのみで適用していない。**

凍結源の照合（`conventions#frozen_source`）は `meta.kind: impl` のため preflight では
適用対象外（P5 SKIP）だが、実装の確認の過程で実測した。

    sha256: 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    bytes : 195421066

**規約の記載と完全一致**。凍結源は変更していない。

## Task B — キャッシュの生成と決定性

`scripts/t1b_backbone_cache.py build` を用いた。前処理（正規化・詰め物・mask 生成）は検出器の
`forward` の内側にあるため、**backbone を直接呼ばず実経路を走らせて hook で出力を受ける**。
これを最初に誤り、`RuntimeError: Input type (torch.cuda.ByteTensor) and weight type
(torch.cuda.FloatTensor) should be the same` で停止した。処方を変えずに同じ値を得る経路は
これだけである。

鍵は塔の識別子・凍結源の sha256 と bytes・model_cfg・backbone の構成・前処理・分割・dtype から作る。

| 生成 | 塔 | cache_key | aggregate_sha256 | bytes |
|---|---|---|---|---|
| probe_a | seed42 | `16e889a328f921c037e6d46756c59f802d8a6339b12f966e7e845a17dc7ae19e` | `96ab87b8abfae5ba662b47991bd7fb890b4806ad95e75195806a7604d3183e84` | 462,422,016 |
| probe_b | seed42 | 同上 | **同上** | 462,422,016 |
| probe_c | seed123 | `ff5f072967dfa828c6f444aaccc0b7950172c7ea5b69a87166ed588c74789677` | `5db5f7ef47dfc554e5a1a86b9de4520fffe7ad4e7f76592b6e7e425f84ad8105` | 462,422,016 |

- **G2（決定性）**: 別過程で二度生成し、鍵も要約値も一致した。
- **陰性対照**: 塔の識別子を seed42 → seed123 に変えると、鍵も要約値も変わった。
  **両方向で取っている**（同じ入力 → 同じ要約値／違う塔 → 違う要約値）。「常に同じ値を返す
  壊れ方」と区別できる。

対象は val の先頭 8 画像（`transforms=None` で前処理が決定的な分割）。
学習側は増強が乱択のため、同じ意味での二度生成の一致は定義できない。

## Task C — キャッシュを読む経路の比較

`scripts/t1b_backbone_cache.py bench`。**同一のバッチ集合**を両経路へ与え、同一過程内で測る。
データ供給の時間は両経路から等しく除かれる（別測で 1 step の 0.51%）。
読み出しは `posix_fadvise(POSIX_FADV_DONTNEED)` で頁キャッシュを落としてから測る
（実寸のキャッシュは実装のメモリ 67 GB に収まらないため、温まった頁キャッシュの値を
代表値として扱ってはならない）。

| 条件 | n | 塔を計算 | 読み出し | 読み後の step | キャッシュ経路 計 | 塔の順伝播 | 上限倍率 | 実測倍率 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| W1 順=計算先 | 30 | 0.4379 s | 0.2494 s | 0.4130 s | 0.6624 s | 0.0250 s (5.70%) | 1.060× | **0.661×** |
| W1 順=キャッシュ先 | 30 | 0.4315 s | 0.2482 s | 0.4115 s | 0.6597 s | 0.0200 s (4.63%) | 1.049× | **0.654×** |
| W1（W2 と同一バッチ） | 20 | 0.4345 s | 0.3712 s | 0.4073 s | 0.7785 s | 0.0272 s (6.25%) | 1.067× | **0.558×** |
| W2（`--trainable all`） | 20 | 0.5234 s | 0.3466 s | 0.4832 s | 0.8297 s | 0.0402 s (7.68%) | 1.083× | **0.631×** |

順序を入れ替えても結論は動かない（対照は両方向）。学習対象は W1 が 266,880 param、
W2 が 25,505,568 param。

**キャッシュを読む経路は速くならず、1.5〜1.8 倍遅い。**

損益分岐: 1 step で読む 91,566,899 bytes を塔の順伝播の時間内に読み切る必要がある。
必要な読み速度は 2.28〜4.58 GB/s。実測は 0.367 GB/s（bench 内）／0.472 GB/s（`dd` の
逐次読み、`iflag=direct`、4 GiB）。**一桁足りない。** fp16 にしても半分にしかならず届かない。

## Task C 補足 — hook による計測の副作用

別に `scripts/profile_t1b_step.py` で 1 step を要素分解した（hook 内で同期して帰属）。

    step 0.4937 s (2.03 it/s) / data 0.0025 s (0.51%) / forward 0.3087 s (62.52%)
    backbone 0.0728 s (14.74%) / backward 0.1800 s (36.45%) / optim 0.0026 s (0.52%)
    eval 0.0877 s/枚 (n=60)

🔴 **hook 内の同期は backbone へ過大に帰属する。** 同期は直前までに積まれた仕事（前処理等）の
完了を待つため、その待ちが backbone の時間に入る。**差分法（塔を計算する step − キャッシュを
読んだ step）による 0.020〜0.040 s を正とする。** 両者を併記し、14.74% を結論に使っていない。

1 epoch の換算（差分法と無関係な全体量）: 4,809 step × 0.4937 s = 2,374 s（39.6 分）
＋ val 評価 1,515 枚 × 0.0877 s = 133 s（2.2 分）= **41.8 分/epoch**、6 epoch で **4.18 h**。
記録の「1 epoch 36〜40 分・1 run 約 4 時間」と整合する。

## Task D — Tier 1 計算器への差し戻し

`tools/estimate_tier_cost.py`（T-2026-09-17-tier1-cost-estimate が置いた計算器）。

| 入力 | 現行の値 | 本契約の実測 |
|---|---|---|
| `det_iface_w1`（検出側 W1 界面 run） | 4.00 h（実測・lecun） | 4.18 h（efros・単独）。**整合。変更しない** |
| `det_iface_w2`（検出側 W2 界面 run） | 4.00 h（**代理**・UNKNOWN #2） | W2/W1 の 1 step 比 **1.205**（同一バッチ・n=20）→ 4.82 h |

キャッシュ経路は短縮しないため、**Tier 1 の日数は変わらない**。

    縮退なし（既定 K=3・装置 2・24h/日）: 153.1〜208.7 日（deadline 節）
    同上（degrade 節の日数列）        : 84.1〜111.9 日

上界の感度として、**塔の順伝播が完全に無料になったと仮定**して全行へ 1.06× を当てても
（`--duration-scale 0.943`）79.3〜105.5 日にしかならず、IPCAI 2027 intention（残 39 日）にも
long abstract（残 121 日）にも届かない。**実装水準の手当てでは締切に届かない。**

## Task E — 検証

| 検査 | 結果 |
|---|---|
| L1 + L2（`make task-validate`） | exit 0 / `OK` |
| L3（`make task-preflight`、`.venv-relation-detr`） | **exit 0**。7 PASS / 0 WARN / 5 SKIP / 0 FAIL |
| SKIP された項目 | P3 deterministic_flags・P4 prereg_committed・P5 frozen_source_hash・P11 gpu_free・P12 refs_resolved |
| 試験（変更前・HEAD の worktree） | 6 failed / 536 passed / 14 skipped |
| 試験（変更後） | 6 failed / 550 passed |
| 失敗の増加 | **0**。6 件は同一で、いずれも `tests/test_engines.py` `tests/test_fetch_task.py` `tests/test_research_logger.py` の既存失敗（本契約の変更と無関係） |
| `make forbidden-check` | 別掲（RESULT.md 送出節） |
| ruff（新設 2 件） | All checks passed |

変更前の失敗数は HEAD の detached worktree を作って測った（推測していない）。
変更後に passed が 14 増えたのは、worktree 側に `third_party/` と `.venv-relation-detr` が
無く skip されていた試験が本体側では走って通ったためである。
