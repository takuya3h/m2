# dlsta で両塔を学べるかの実測 — REPORT

契約 `T-2026-10-19-dlsta-tower-feasibility`（kind: analysis）。ホスト dlsta（repo `~/local/m2`、RTX A5000 × 5）、2026-10-21。
**数値はすべて本ホストでの実測。前のホストの値から換算していない。** 未測定は UNKNOWN と書く。命令と出力は
`tasks/T-2026-10-19-dlsta-tower-feasibility/audit.md`。測定の値は選定と関門の判定に使わない。短い学習の損失と評価は報告しない。

## 1. 装置の構成

| GPU | 型 | 容量 | NVLink | NUMA | 本契約での扱い |
|---|---|---|---|---|---|
| 0 | RTX A5000 | 24,564 MiB | なし | 0 | 開始時 compute プロセス 0 なのに 99 MiB 確保（ほかは 22 MiB）。容器の外の確保とみて除外 → 利用者の許可（2026-10-21）で途中から使用 |
| 1 / 2 | RTX A5000 | 24,564 MiB | 1–2 が NV4 | 0 | 使用 |
| 3 / 4 | RTX A5000 | 24,564 MiB | 3–4 が NV4 | 1 | 使用 |

driver 595.84、torch 2.1.2+cu118（cuDNN 8700）、nvcc 12.9.86、gcc 13.3.0。repo の置き場の空き 2.53 TB（開始時、79%）。

## 2. 検出塔（D\*-COCO の処方: 2 プロセス、GPU ごとの batch 2、fp16、折り A、seed 42）

起動の引数は二周目の `command.sh` と同じ（port を除く）。一歩の時間は 100 歩目以降の窓平均（直近 20 歩）の平均。600 歩まで回した（1 epoch 2405 歩）。

| 構成 | 同時に動いていたもの | 一歩 (s) | torch max allocated rank0 / rank1 (bytes) | nvidia-smi 最大 (MiB) |
|---|---|---|---|---|
| NVLink の組 GPU1–2（D1） | なし | 0.59848 | 12,285,587,968 / 11,599,943,168 | 12,563 / 12,145 |
| NVLink 無し GPU1+GPU3、SYS（D6） | 工程塔の測定（GPU2・GPU4）、工程塔の評価（GPU0、一部） | 0.60637 | 12,287,053,824 / 11,600,070,144 | 12,453 / 12,073 |
| NVLink 無し GPU0+GPU1、NODE（D6b） | なし | 0.60044 | 12,279,308,288 / 11,594,992,128 | 12,529 / 12,073 |
| 2 本同時: GPU1–2（D7） | GPU3–4 の 1 本 | 0.59555 | 12,288,233,984 / 11,602,772,480 | 12,563 / 12,145 |
| 2 本同時: GPU3–4（D7） | GPU1–2 の 1 本 | 0.58633 | 12,289,270,784 / 11,594,959,872 | 12,559 / 12,145 |

- **通信の設定は要らない。** `NCCL_P2P_DISABLE` なしで、どの組も止まらずに進んだ（andrew では要った）。
- **2 本を二つの NVLink の組で同時に回しても一本あたりの一歩は遅くならない**（0.596 / 0.586 s、単独 0.598 s）。
- **GPU ごとの batch の上限**（処方の変更。探索の候補を決める材料）:

| GPU ごとの batch | 結果 | torch max allocated rank0 / rank1 (bytes) |
|---|---|---|
| 2（処方） | 600 歩まで収まる | 12,285,587,968 / 11,599,943,168 |
| 3 | 300 歩まで収まる | 17,886,560,256 / 17,149,070,848 |
| 4 | 50 歩に届く前に OOM | 21,258,942,976 / 20,272,091,136（OOM の時点） |
| 4 + `expandable_segments:True` | 300 歩まで収まる | 23,831,509,504 / 24,307,600,896（容量の 96%） |

  増強が画像ごとに大きさを変えるので、300 歩で出会わなかった大きさで batch 3 が溢れる可能性は残る（全 epoch は回していない）。

- **dlsta で既存のスクリプトをそのまま使うときの落とし穴**（実装の行。本契約では変えていない）:
  - `third_party/Relation-DETR/configs/train_config_egosurgery_seed42.py` の `EGO_ROOT` と `resume_from_checkpoint` の既定は
    `/home/ubuntu/slocal2/m2/...`（andrew の位置）。`scripts/run_stage1_dtower.sh` はどちらも与えない。`main.py` は
    `resume_from_checkpoint` がファイルでないと読み込みを飛ばして進むので、**dlsta では COCO の重みを読まない学習になりうる**。
    本契約は環境変数 `EGO_ROOT` と `RELDETR_COCO_CKPT` を与え、記録の `load pretrained from …/local/m2/…` で確かめた。
  - `scripts/eval_relation_detr_map.py` は `third_party/Relation-DETR` へ `chdir` する。checkpoint を repo 相対で渡すと
    `State dict is None, skip loading` のまま評価して **AP 0 を返す**（失敗にならない）。絶対経路で渡す。

## 3. 工程塔（三周目の処方: 物理 batch 16、累積 4、COCO 初期化、短辺 800 の全画面 = 800×1422）

| 構成（A5000 一枚） | 結果 | torch max allocated (bytes) | max reserved (bytes) | 一歩 (s/micro-step) |
|---|---|---|---|---|
| batch 16（処方そのまま） | **収まらない**。micro-step 1 の forward で OOM | 24,377,192,960（OOM の時点） | 24,779,948,032 | — |
| batch 14 | OOM（micro-step 1 の forward） | 24,819,349,504（同） | 24,876,417,024 | — |
| **batch 13（一枚の最大）** | 収まる | 23,689,911,808 | 24,641,536,000 | 1.2347 |
| batch 13 + `expandable_segments:True` | 収まる | 23,680,405,504 | 23,832,035,328 | 1.2743 |
| batch 12 | 収まる | 21,905,244,672 | 23,999,807,488 | 1.1689 |
| batch 8 | 収まる | 14,775,793,152 | 16,221,470,720 | 0.8031 |

一歩の時間は読み込みの待ちを含む 60 micro-step の平均（最初の 8 を除く）。**検出塔の測定（D6）、特徴の取り出し、工程塔の評価と同時に回した値**。
batch 13 以下は処方の変更であり（BN の統計の枚数が変わる）、記録だけにする。

| 特徴の取り出しと時間ヘッド（候補 A、三周目 005 の backbone） | 結果 |
|---|---|
| 取り出し（batch 16、15,437 フレーム） | 一枚に収まる。最大確保 4,103,955,968 bytes、400.70 s（D6 などと同時）。**特徴の要約値は三周目の記録（ilya）と bit 一致** |
| 時間ヘッドの学習（候補 A、L6、折り A） | 一枚に収まる。最大確保 103,205,376 bytes、22 epoch で 10.36 s |

特徴は repo の外に置いた（三周目の設定の `data/processed/` は使っていない）。

## 4. ホストをまたぐ評価（val、推論だけ）

| 塔 | 指標 | dlsta | 記録 | 差 |
|---|---|---|---|---|
| 工程塔 三周目 005（COCO、lr 1e-4、折り A、seed 42。記録 ilya） | phase_accuracy | 0.8521452145214522 | 0.8521452145214522 | 0 |
| 同 | phase_macro_f1 / jaccard / edit / seg_f1_10・25・50 | 記録と同じ | — | 0（7 指標とも全桁一致） |
| 検出塔 二周目 D\*-COCO 折り A seed 42（記録 andrew） | overall mAP | 0.7273447938494212 | 0.7273450248398429 | −2.310e−07 |
| 同 | 標的群 AP（Skewer, Bipolar Forceps, Scalpel, Syringe, Raspatory） | 0.7950740420442742 | 0.7950748008550899 | −7.588e−07 |
| 同 | 陰性対照群 AP（Gauze, Mouth Gag, Suction Cannula, Tweezers） | 0.6726633578860826 | 0.6726631817581498 | +1.761e−07 |

- 工程塔は全桁一致。検出塔は**全桁一致しない**。クラス AP で差があるのは Forceps、Gauze、Needle Holders、Syringe の 4 つで、最大は Syringe の −3.79e−06。
  記録の seed 間（42 / 123 / 456）の AP の標準偏差は 0.005322 で、AP の差はその約 4.3e−05 倍。**原因は測っていない（UNKNOWN）。**
- 比較が働いていることの対照: 折り B の塔を同じ折り A の val に当てると、工程塔 phase_accuracy 0.99406、検出塔 AP 0.92656 に変わる
  （折り A の val の動画 09・10 は折り B の train に含まれる）。

## 5. 工程塔を複数の GPU で回す道（実装を読んだだけ。変えていない）

**現状は対応していない。** `scripts/stage1_ptower_r3.py`（sha256 `3ee4325d…`）と `scripts/stage1_ptower.py`（`4ec5b574…`）に
分散の初期化、DDP、DataParallel、SyncBatchNorm、DistributedSampler は無い。装置は `configs/stage1_ptower_r3.yaml:36` の `device: cuda:0` 一つで、
模型は `stage1_ptower_r3.py:117` の `model.to(device)` で一枚に載る。

**正規化層**: ResNet-50 の BatchNorm2d 53 層のうち stem の `bn1` だけが eval（`stem_eval`、129–133 行）。layer1〜4 の 52 層は学習中に
**物理 batch 16 枚の統計**で正規化し running の統計を更新する。勾配の累積（221–224 行）はこの枚数を変えない。

**物理 batch 16 の統計を保ったまま 2 枚で回すために足すもの**（次の契約の材料。順不同）:

1. 分散の起動（`torchrun` か accelerate）と `torch.distributed` の初期化、装置を rank ごとに決める（`cfg.device` の固定をやめる）
2. 模型を DDP で包む。GPU ごとの batch 8 × 2 枚 = 16 枚で一歩（batch 8 は一枚に収まる: 最大確保 14,775,793,152 bytes）
3. **layer1〜4 の BN を SyncBatchNorm に変える**（2 枚の 8 枚ずつを合わせた 16 枚で平均と分散を取る）。`convert_sync_batchnorm` は stem の `bn1` も
   変えるので、`stem_eval` の `bn1.eval()` が引き続き効くこと（eval の SyncBatchNorm は running の統計を使う）を確かめる
4. 勾配の累積 4 は DDP の `no_sync` で包み、4 歩目だけ all-reduce する（実効 batch 64 を保つ）。損失は rank ごとの平均で、DDP の平均と合わせて 16 枚の平均になる
5. 学習の画像の割り振りを `DistributedSampler` にする（順序は一枚のときの `RandomSampler` と同じにはならない）。epoch ごとに `set_epoch`
6. val の評価、checkpoint の保存、記録（`ExperimentManager`、W&B）を rank 0 だけにする。val の評価は今の `frame_predictions` を一枚で回す形のままでよい
7. 記憶領域の最大の記録（`peak_memory_bytes`）を rank ごとに取る
8. 決定性の設定（`use_deterministic_algorithms(True)`）のもとで SyncBatchNorm と NCCL の all-reduce が動くかを確かめる（動かない演算があれば止まる）

別の道として、一枚のまま batch 16 を保つ方法（activation の checkpoint）は、BN を含む区間を再計算すると running の統計が二重に更新されるので
そのままでは処方が変わる。fp16 の autocast は数値の処方を変える（三周目は fp32）。どちらも処方の変更として区別が要る。

**一枚と複数枚で同じ学び方になることの確かめ方の案**:

- 一枚に収まる大きさで比べる: 一枚・batch 8 と、2 枚・GPU ごとの batch 4 + SyncBatchNorm を、**同じ画像の並び**（両方に同じ添字の列を与える）で
  数歩回し、損失、勾配、BN の running の統計、更新後の重みを許容差つきで比べる
- 陽性対照: SyncBatchNorm を外した 2 枚（BN が 4 枚ずつの統計になる）では BN の running の統計がずれることを同じ比較で示す
- 処方の大きさで: 2 枚・GPU ごとの batch 8 + SyncBatchNorm の記憶領域と一歩の時間を測り、一枚の batch 16 が載る装置の記録（27.06 GiB）と別に記録する

## 6. 受け渡しの道（決めない。並べるだけ）

| 道 | 実測で分かったこと | 分かっていないこと |
|---|---|---|
| Syncthing（中心 philip 経由） | dlsta で `syncthing` と `keeper.sh` が動き、`~/local/m2` が同期の対象。philip への常駐の中継（手元 22001 → philip 22000）が在る。`.stignore` は `experiments/**/*.pth` と `experiments/**/checkpoints` を配る対象に含む | andrew が同じ folder に参加しているか、どれだけで届くか（測っていない）。全台に複製される |
| dlsta → andrew へ直接の転送（SSH の port） | `192.168.196.190:50072` に TCP で届き `SSH-2.0-OpenSSH_9.6p` を返す | 認証が通るか（認証していない）、速さ |
| dlsta → philip → andrew（中継） | `192.168.196.150:50072` に TCP で届く。dlsta に philip 宛ての鍵の名前のファイルと常駐の中継が在る | philip から andrew への転送の可否と速さ |
| andrew 側から dlsta を取りに行く | — | andrew から dlsta（`192.168.196.54`）へ届くか（本契約は dlsta から外へしか測っていない） |

渡す大きさ: 検出塔 `best_ap.pth` 195,421,066 bytes（`work/` 全体は accelerate の状態 583,539,300 bytes × 5 を含み 3,314,951,357 bytes）、
工程塔三周目 `best.pth` 94,405,478 bytes、特徴のキャッシュ 127,016,156 bytes。

## 7. 入力の実在

両塔の学び直しに要る入力は**すべて在り、欠けは無い**（28 項目すべて期待と一致。`inputs_inventory.json`）。
画像 15,437 枚の内容は動画ごとに andrew の記録と一致（15/15）。工程注釈だけの 1,796 フレームは
`data/raw/OpenSurgery_Dataset/01_frames/initial_videos/` に在る。折りごとの術具注釈 A〜E は既に在った（作っていない）。

## 8. 出力の置き場

repo の下（本ディレクトリ）: `REPORT.md`、`inputs_inventory.py` / `.json`、`gpu_procs.py`、`tools/`（測定の道具）。
repo の外 `~/m2-scratch/dlsta_tower_feasibility/`（145,612,791 bytes）: 学習と評価のログ、nvidia-smi の採取、特徴のキャッシュ、時間ヘッドの checkpoint。
既存の `experiments/` のほかの場所には何も作っていない。
