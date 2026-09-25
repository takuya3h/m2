# 監査 — T-2026-09-19-stage1-phase-tower-r3

実測だけを書く。未測定は UNKNOWN と書く。

## 0. 検査の結果

| 層 | 命令 | 結果 |
|---|---|---|
| L1+L2 | `make task-validate` | exit 0。WARN 3 件（`created_from.counts` が起票時 0 のまま。index 0→1558 / experiments 0→476 / verdicts 0→1506）。利用者が承知のうえ続行を指示 |
| L3 | `make task-preflight` | 1 回目 exit 2（P4 FAIL: `prereg.commit` 未記入）。prereg を commit した後 **exit 0**（10 PASS / 0 WARN / 4 SKIP / 0 FAIL） |

L3 の SKIP 4 件（「合格」ではなく「実行されなかった」）:

- P2 `cuda_ext_loaded` — `plan.env.preflight` に記載なし
- P3 `deterministic_flags` — 判定基準が未確定（backlog B-20 が未解決）
- P12 `refs_resolved` — 解決前提の参照は無い
- **P14 `proposal_card_checked` — 導入前の契約のため対象外**

## 1. Task A — 事前登録と開始状態

### A-1 prereg の固定

| 項目 | 実測 |
|---|---|
| `prereg.commit` | `b663f214cf58458c478c13b69b74c236de468c75` |
| `prereg.committed_at` | `2026-09-22T16:33:50+00:00` |

### A-2 開始状態

| 項目 | 実測 |
|---|---|
| 分岐 | `feat/stage1-phase-tower-r3`（起点 `origin/phase0` = `cb3fcaa1`） |
| 作業ツリー | 取り込み時点で清浄（開始前の未追跡 3 件は別分岐で stash 退避、本分岐では触れていない） |
| 装置 | `SERVERNAME=ilya`（hostname `aolab`）。契約の指定と一致 |
| GPU | RTX 6000 Ada Generation 49,140 MiB × 2。開始時の compute プロセス 0 件（L3 の P11 が PASS） |
| `.sync-pause` | 設置済み。稼働中の keeper は対応版（`grep -c sync-pause ~/bin/m2-sync.sh` = 2） |

### A-3 二周目の道具と成果物

本分岐に在る。**ただし契約が指す entrypoint は一周目のものだった**（起票者の誤り §4 を見よ）。

| 実際に二周目が使った道具 | 契約 `inputs.code.entrypoints` の記載 |
|---|---|
| `scripts/stage1_ptower_r2.py` | `scripts/train_phase_tower_r50.py` |
| `scripts/run_stage1_ptower_r2.py` | `scripts/run_stage1_ptower.py` |
| `scripts/select_stage1_ptower_r2.py` | `scripts/select_stage1_ptower.py` |

成果物 `experiments/phase1/stage1_ptower_r2/` は在る。そこから読んだ確定塔の折りごと val macro Jaccard は
A 0.4679 / B 0.2464 / C 0.4265 / D 0.3184 / E 0.4763、5 折り平均 **0.3871**（契約の記載 0.387 と一致）。
一周目の確定塔は A 0.3669 / B 0.2025 / C 0.2400 / D 0.3856 / E 0.4496、平均 **0.3289**（契約の記載 0.329 と一致）。

### A-4 COCO 検出済み backbone（G1 / 完了判定 a）

D 塔が出発する checkpoint は `configs/detector_relation_detr/train_config_augstrong.py:55-57` と
`train_config_augstrong_hires.py:55-57` の `resume_from_checkpoint` が指す
`data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth`。
検出塔の契約の記録 `tasks/T-2026-09-18-stage1-detector-towers/audit.md:65` も同じファイル名と
196,140,106 bytes を記録している（**D 側は sha256 を残していなかったため、要約値は本契約で初めて測った**）。

| 項目 | 実測 |
|---|---|
| ファイル bytes | 196,140,106（D 側の記録と一致） |
| ファイル sha256 | `2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff` |
| `backbone.*` の要素数 | 265。torchvision ResNet-50 の命名 |
| torchvision `resnet50` への適合 | `load_state_dict(strict=False)` の missing は `fc.weight` / `fc.bias` の 2 件のみ、unexpected 0 件 |
| **checkpoint から取り出した backbone の要約値** | `a755b3eb22a3c1996ff88bb5797690ceb5605eedef5c24f980e1cac4c07fc98f` |
| **P\*-COCO が実際に出発する重みの要約値** | `a755b3eb22a3c1996ff88bb5797690ceb5605eedef5c24f980e1cac4c07fc98f`（**一致**） |
| P\*-ImageNet が出発する重みの要約値 | `4f6b5b6209465abc4f7d35d2518bfae94f7972f9c1ea094e183d7d7e492563fd`（**異なる** = 空振りでない確認） |

要約値の定義は `scripts/stage1_ptower_r3.py` の `backbone_digest`: `fc.*` と
`num_batches_tracked` を除く全テンソルを、名前・形・float32 のバイト列の順で SHA-256 に入れる。
`num_batches_tracked`（53 件）を除くのは、どちらの checkpoint にも入っておらず
BatchNorm の後方互換の読み込みが 0 のまま残すためで、入れると checkpoint から直接取った
要約値と一致しなくなる。共通する 265 件は**すべて値が異なる**（COCO 検出を経た重みであることの確認）。

### A-5 追加 6 動画（17〜22）

| 項目 | 実測 |
|---|---|
| 工程注釈 | **在る**。`data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase/`（17_1 〜 22_3） |
| 画像 | **無い**。`data` 配下に 17〜22 のフレーム格納先は 0 件 |
| 帰結 | prereg §2 と SPEC §6 に従い **P\*-21 は UNKNOWN**。P\*-15 は続ける |

学習・評価に使う 15 動画のフレーム総数は 15,437。折りごとの内訳:

| 折り | train 動画 | train フレーム | val フレーム | test フレーム |
|---|---|---|---|---|
| A | 10 | 9,657 | 1,515 | 4,265 |
| B | 10 | 9,764 | 1,861 | 3,812 |
| C | 10 | 10,834 | 1,988 | 2,615 |
| D | 10 | 10,262 | 2,554 | 2,621 |
| E | 10 | 11,182 | 2,131 | 2,124 |

### A-6 前処理（完了判定 c）

二周目の前処理は `scripts/stage1_ptower_r2.py:39` の
`EVAL_TRANSFORM = ResNet50_Weights.IMAGENET1K_V1.transforms()`。実体は
`ImageClassification(resize_size=[256], crop_size=[224])` すなわち **短辺 256 → 中央 224 切り出し**。
1920×1080 は短辺 256 で 455×256 になり、224 を切り出すと横に残るのは **49.2%**
（prereg §1 の「49%」は実測と一致）。

三周目は `scripts/stage1_ptower_r3.py:48-54` に置き換えた。

    EVAL_TRANSFORM = transforms.Compose([
        transforms.Resize(SHORT_SIDE),   # SHORT_SIDE = 800。短辺を 800 へ、縦横比は保つ
        transforms.ToTensor(),
        NORMALIZE,
    ])

**`CenterCrop` を含む行は無い**（切り出しが入っていないことの実装上の根拠）。実測:

| 項目 | 実測 |
|---|---|
| 元画像 | 1920×1080 |
| 変換後 tensor | `(3, 800, 1422)` = 横 1422 × 縦 800 |
| 画面の残る割合 | **100.0%** |

学習側はここに `RandomHorizontalFlip` だけを足す（prereg の「増強は反転のみ」）。

### A-7 占位の差し替え

| 項目 | 実測値 |
|---|---|
| `meta.created_from.runindex_commit` | `4e97b3deae28e653948c19309d229c755587c42b` |
| `contract.conventions_rev` | `4369cf5e7b82a3043b9b00b998911c4efb856f69` |

`meta.created_from.counts` は**差し替えていない**。SPEC の A-7 が差し替えを求めるのは
この 2 つだけであり、counts は「起票時」の値なので実行時の値で上書きすると意味が変わる。
分母が動いたことは L2 の WARN として残し、利用者の承認を得て続行した。

## 2. G1（Task A の後）

契約の判定文: 「COCO 検出済み backbone の重みが実在し、その要約値が D 塔の初期化に使うものと
一致した。二周目の道具が本分岐にある」。

**pass。** 重みは実在し（§A-4）、要約値は D 塔が出発する checkpoint から取ったものと完全に一致し、
二周目の道具は本分岐に在る（§A-3。ただし契約が指す名前とは違う）。

## 3. Task B — 一本目（所要時間と記憶領域）

### B-0 事前の実測（掃引の前に測った）

入力 1422×800、COCO 初期化の R50、stem 凍結、AdamW。装置 1 枚（47.37 GiB）。

決定性設定なし:

| batch | peak allocated | sec/iter | frames/s | 状態 |
|---|---|---|---|---|
| 64 | — | — | — | **OOM** |
| 32 | — | — | — | **OOM** |
| 16 | 26.93 GiB | 0.495 | 32.3 | OK |
| 8 | 13.62 GiB | 0.247 | 32.4 | OK |
| 4 | 7.07 GiB | 0.117 | 34.2 | OK |

`stage1_ptower.deterministic`（`torch.use_deterministic_algorithms(True)` ほか）を当てた後、batch 16:

| 項目 | 実測 |
|---|---|
| peak allocated | 26.88 GiB |
| peak reserved | 31.76 GiB |
| sec/iter | 0.764 |
| frames/s | 20.9 |
| 折り A の 1 epoch 見込み | 約 7.7 分 |
| 上限 36 epoch の見込み | 約 4.6 時間（val 評価を除く） |

**prereg の batch 64 は装置に収まらない。** 収まる最大は 16。
利用者に諮り（2026-09-23）、**batch 16 + 勾配累積 4 で実効 batch 64 を保つ**ことと、
**上限 36 epoch を変えない**ことの承認を得た。解像度を下げる案は SPEC の指示どおり出していない。

### B-1 一本目

`init=coco fold=A seed=42 ft_lr=3e-4 device=cuda:0`。
証跡 `experiments/phase1/stage1_ptower_r3_002_ft_coco_lr0.0003_foldA_seed42/`。

| 項目 | 実測 |
|---|---|
| 壁時計 | **8,513 秒 = 2.36 時間** |
| peak allocated | **27.06 GiB** |
| peak reserved | 31.81 GiB（装置 47.37 GiB） |
| 到達 epoch | **16**。上限 36 には**張り付いていない** |
| 学習率の低下 | **epoch 12** に 3e-4 → 3e-5（最良 epoch 8 から 4 停滞） |
| 打ち切り | **epoch 16**（低下の後さらに 4 停滞） |
| 最良 epoch | 8 |
| 最良 val frame accuracy | **0.8759** |
| val macro Jaccard | **0.6426** |
| backbone の初期値の要約値 | `a755b3eb…`（D\* の出発点と一致） |
| 実効 batch | 64（16 × 累積 4） |
| 学習する層 | stem 0 / layer1 215,808 / layer2 1,219,584 / layer3 7,098,368 / layer4 14,964,736 / fc 18,441 |

低下と打ち切りが**実際に働いた**（上限に張り付いて終わったのではない）。

#### 中断した run

`experiments/phase1/stage1_ptower_r3_001_ft_coco_lr0.0003_foldA_seed42/` は**未完了**である。
学習率の低下と打ち切りの規則が学習ループに直書きで単体試験できなかったため、
純関数 `plateau_action` に抽出し、**作業木の内容と実際に回った内容を一致させるために**
2 epoch の時点で止めて最初からやり直した。`metrics.json` は空のままなので、
掃引の再開判定（`run_stage1_ptower_r3.evidence_for`）はこれを完了と見なさない。

#### 二周目の同じ折りとの比較（停止条件の確認）

停止条件は「fine-tune 後の frame accuracy が二周目の同じ折りを下回る折りが一つでもあれば停止」。

| 周 | 構成 | 折り A の val frame accuracy | val macro Jaccard |
|---|---|---|---|
| 二周目 | lr 3.33e-5、seed 42 / 123 / 456 | 0.6759 / 0.6455 / 0.6792 | 0.3013 / 0.2807 / 0.3224 |
| 二周目 | lr 1e-4、seed 42 / 123 / 456 | 0.6825 / 0.7010 / **0.7149** | 0.3714 / 0.3285 / 0.3488 |
| 三周目 | COCO、lr 3e-4、seed 42 | **0.8759** | **0.6426** |

**下回っていない**（二周目の最良 0.7149 に対し 0.8759）。停止条件には触れない。
なお二周目の 1 本は 411〜562 秒で、三周目は 8,513 秒（画素数が約 22 倍、epoch が 12 → 16）。

## 3.5 G2（Task B の後）

契約の判定文: 「一本の所要時間が三時間以内で、記憶領域が装置に収まる」（`on_fail: ask`）。

**pass。** 2.36 時間 ≤ 3 時間、27.06 GiB ≤ 47.37 GiB。

起票前の見込み（決定性設定下で 20.9 frames/s、上限 36 epoch なら 5.5 時間）は
**上限に達しなかったため外れた**。打ち切りが 16 epoch で働いたことによる。
利用者には「3 時間を超える見込み」と伝えて上限 36 のままの続行の承認を得ていたが、
**実測では超えなかった**。

## 4. Task C — fine-tune 28 本

`scripts/run_stage1_ptower_r3.py FT`。2 枚で対ごとに投入し、証跡のある組は飛ばす。
掃引ログ `experiments/phase1/stage1_ptower_r3/logs/taskC_FT.log`。**28 本すべて完了**
（`GRID_COMPLETE FT runs=28`）。Task B の 1 本は再開判定で飛ばされ、掃引は 27 本を回した。

| init | lr | 折り | seed | val frame acc | val Jaccard | 二周目の同折り最良 | 判定 | epoch | 最良 | 低下 | 打切 | 秒 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| coco | 1e-4 | A | 42 | 0.8521 | 0.6460 | 0.7149 | OK | 21 | 17 | 16 | 21 | 11210 |
| coco | 1e-4 | A | 123 | 0.8488 | 0.6280 | 0.7149 | OK | 18 | 14 | 11 | 18 | 9967 |
| coco | 1e-4 | A | 456 | 0.8548 | 0.6329 | 0.7149 | OK | 16 | 8 | 12 | 16 | 8543 |
| coco | 1e-4 | B | 42 | 0.7560 | 0.4258 | 0.5846 | OK | 14 | 6 | 10 | 14 | 7904 |
| coco | 1e-4 | C | 42 | 0.7802 | 0.4833 | 0.6660 | OK | 18 | 14 | 7 | 18 | 10939 |
| coco | 1e-4 | D | 42 | 0.7455 | 0.3551 | 0.6132 | OK | 18 | 10 | 14 | 18 | 10913 |
| coco | 1e-4 | E | 42 | 0.8165 | 0.5268 | 0.7203 | OK | 21 | 17 | 11 | 21 | 13067 |
| coco | 3e-4 | A | 42 | 0.8759 | 0.6426 | 0.7149 | OK | 16 | 8 | 12 | 16 | 8513 |
| coco | 3e-4 | A | 123 | 0.8739 | 0.6531 | 0.7149 | OK | 22 | 18 | 11 | 22 | 11781 |
| coco | 3e-4 | A | 456 | 0.8680 | 0.6444 | 0.7149 | OK | 18 | 10 | 14 | 18 | 9982 |
| coco | 3e-4 | B | 42 | 0.7679 | 0.3917 | 0.5846 | OK | 17 | 13 | 11 | 17 | 9278 |
| coco | 3e-4 | C | 42 | 0.8275 | 0.5024 | 0.6660 | OK | 26 | 22 | 12 | 26 | 16240 |
| coco | 3e-4 | D | 42 | 0.7529 | 0.3909 | 0.6132 | OK | 19 | 15 | 8 | 19 | 11067 |
| coco | 3e-4 | E | 42 | 0.8198 | 0.5018 | 0.7203 | OK | 21 | 17 | 13 | 21 | 13572 |
| imagenet | 1e-4 | A | 42 | 0.8297 | 0.5650 | 0.7149 | OK | 28 | 24 | 12 | 28 | 14971 |
| imagenet | 1e-4 | A | 123 | 0.8092 | 0.4955 | 0.7149 | OK | 11 | 7 | 6 | 11 | 6103 |
| imagenet | 1e-4 | A | 456 | 0.8469 | 0.5787 | 0.7149 | OK | 29 | 25 | 7 | 29 | 15513 |
| imagenet | 1e-4 | B | 42 | 0.7211 | 0.3205 | 0.5846 | OK | 16 | 12 | 8 | 16 | 9072 |
| imagenet | 1e-4 | C | 42 | 0.8018 | 0.4182 | 0.6660 | OK | 14 | 10 | 6 | 14 | 8519 |
| imagenet | 1e-4 | D | 42 | 0.7451 | 0.3354 | 0.6132 | OK | 22 | 18 | 15 | 22 | 13301 |
| imagenet | 1e-4 | E | 42 | 0.7926 | 0.3964 | 0.7203 | OK | 16 | 12 | 11 | 16 | 10006 |
| imagenet | 3e-4 | A | 42 | 0.8112 | 0.4897 | 0.7149 | OK | 17 | 13 | 9 | 17 | 9445 |
| imagenet | 3e-4 | A | 123 | 0.8145 | 0.4986 | 0.7149 | OK | 16 | 12 | 6 | 16 | 8564 |
| imagenet | 3e-4 | A | 456 | 0.8343 | 0.5650 | 0.7149 | OK | 14 | 10 | 7 | 14 | 7766 |
| imagenet | 3e-4 | B | 42 | 0.6873 | 0.2580 | 0.5846 | OK | 11 | 3 | 7 | 11 | 6002 |
| imagenet | 3e-4 | C | 42 | 0.8073 | 0.3769 | 0.6660 | OK | 14 | 10 | 5 | 14 | 8759 |
| imagenet | 3e-4 | D | 42 | 0.7514 | 0.2938 | 0.6132 | OK | 12 | 4 | 8 | 12 | 6998 |
| imagenet | 3e-4 | E | 42 | 0.7865 | 0.3893 | 0.7203 | OK | 21 | 17 | 11 | 21 | 13567 |

### 停止条件と規則の働き

| 項目 | 実測 |
|---|---|
| 二周目の同じ折りを**下回った** run | **0 件**（停止条件に触れない） |
| 上限 36 epoch に張り付いた run | **0 件**（到達 epoch は 11〜29） |
| 学習率の低下が起きた run | **28 件**（全 run） |
| 打ち切りが働いた run | **28 件**（全 run） |
| 所要時間 | 最小 6,002 秒 / 最大 16,240 秒 / 合計 **81.0 GPU 時間** |
| 3 時間（G2 の値）を超えた run | **12 件**（利用者の承認済み。上限 36 を変えない判断による） |
| 記憶領域の最大 | **27.06 GiB**（全 run 通して装置に収まった） |

**規則は全 run で同一に働いた**（低下 28/28、打ち切り 28/28、上限への張り付き 0/28）。
これは完了判定 b の「学習率の低下と打ち切りの規則が全 run で同一」の実測である。

損失は全 run で有限であった（`torch.isfinite` の検査が一度も発火していない。
発火すれば `RuntimeError` で run が落ち、掃引が止まる）。

### 実験フォルダの連番の重複

`_012_` `_013_` `_014_` `_025_` は 2 つずつある。`next_sequence` が走査した時点で
相手のフォルダがまだ無く、同時に始まる 2 本が同じ番号を取ったためである。
**同一性は連番ではなく config の識別鍵**（action・init・ft_lr・fold・seed）で取るため、
再開判定にも集計にも影響しない（`run_stage1_ptower_r3.IDENTITY`）。

## 5. Task D — 特徴抽出と決定性

`scripts/run_stage1_ptower_r3.py EX --verify-first`。掃引ログ
`experiments/phase1/stage1_ptower_r3/logs/taskD_EX.log`。**28 本すべて完了**
（`GRID_COMPLETE EX runs=28`）。1 本 277〜291 秒（決定性を検証した 1 本のみ 744 秒）。

fine-tune 後の backbone から、その折りの**全 15 動画**の C5 GAP 2048 次元を
短辺 800・全画面で取る。学習時と同じ前処理（反転なし）。

| 項目 | 実測 |
|---|---|
| キャッシュ件数 | 28 |
| 各キャッシュのフレーム数 | 15,437（動画 15 本。`video_counts` が manifest の数と一致することを実装が assert する） |
| 各キャッシュの大きさ | 約 127 MB |
| **特徴の要約値が相異なる** | 28 / 28 |
| **checkpoint の要約値が相異なる** | 28 / 28 |

### 決定性（完了判定 d）

`verify_determinism` を立てた 1 本（`r3_coco_lr0.0001_foldA_seed42`）の実測:

| 項目 | 実測 |
|---|---|
| 1 度目の特徴の要約値 | `5823279fe5e3c6ed3559b2ebf12d42fdd46ab577a0907ba0501fa94109938190` |
| **2 度目の特徴の要約値** | `5823279fe5e3c6ed3559b2ebf12d42fdd46ab577a0907ba0501fa94109938190`（**一致**） |
| **backbone を変えたとき** | `weight_change_detected: true`（`conv1.weight` を 0 にすると特徴が変わる） |

2 度目の一致だけでは「検査が働いている」ことにならないため、実装は同じ run の中で
**重みを壊して特徴が変わることも測る**（`scripts/stage1_ptower_r3.py` の `extract`）。
どちらかが崩れれば `assert` で run が落ちる。

## 6. Task D — 時間ヘッド 280 本

`scripts/run_stage1_ptower_r3.py HEAD`。**280 本すべて完了**（`GRID_COMPLETE HEAD runs=280`）。
一周目・二周目と同じ 10 構成（候補 A 2・B 4・C 4）を 28 の特徴集合の上で回す。
1 本 3 秒前後。表は `experiments/phase1/stage1_ptower_r3/validation_recipes.csv`
（**40 行** = 系統 2 × 学習率 2 × 構成 10）と `validation_runs.csv`（**280 行**）。

## 7. Task E — 選定・test・並置

### 選定（val のみ。test は見ていない）

| 系統 | 確定 recipe | 5 折り平均 val J | 同 acc | 理由 |
|---|---|---|---|---|
| **P\*-COCO** | 候補 C / 8 層 / 平滑 0.30 / 履歴 30 / lr 1e-4 | **0.6558** | 0.8478 | 同点規則（SD 内・所要時間 20% 内・同候補同受容野 → 折り A の seed 間 pstd が小さい方） |
| **P\*-ImageNet** | 候補 B / 8 層 / 平滑 0.00 / 履歴 30 / lr 1e-4 | **0.4785** | 0.7781 | 同上。**co-primary の食い違いを記録したうえで**同点規則へ進めた |

#### prereg が定めていなかった場合に当たった

ImageNet 系統は主指標の最良（J 0.4785 / acc 0.7781）と次点（J 0.4757 / acc 0.7858）で
**co-primary の向きが食い違う**。prereg §6-1 は「macro Jaccard が最大で co-primary が
同方向のもの」と書くだけで、食い違った場合を定めていない。一周目から共有している
`select()` はこの場合に `ValueError` を投げて止まる。

SPEC の Task E-1「一意に決まらなければ諮る」に従って利用者へ出し、
**食い違いを記録したうえで同点規則へ進める**判断を得た（2026-09-25）。根拠として示した実測:

- 差 0.0028 は折り A の seed 間 SD 0.0294 の**内側**で、両者は区別がつかない
- prereg §6-2 の「受容野の短い方」を字義どおり当てても同じ行（履歴 30 < 60）
- 実装の同点規則（折り A の seed 間 pstd）も同じ行

三つの読みが一致するため、どの読みでも `B/8 層/w0.0/h30/lr1e-4` になる。
食い違いそのものは `selection.json` の `co_primary_disagreement` に残した。
共有の `select()` には既定を変えない分岐（`co_primary="stop"` が従来どおり）だけを足し、
一周目・二周目の振る舞いは変えていない（試験 17 件で確認）。

### 折りごとの val macro Jaccard（確定塔）

| | A | B | C | D | E | 平均 |
|---|---|---|---|---|---|---|
| **P\*-COCO** | 0.7068 | 0.6718 | 0.6094 | 0.6152 | 0.6757 | **0.6558** |
| **P\*-ImageNet** | 0.6162 | 0.3584 | 0.4305 | 0.4330 | 0.5542 | **0.4785** |
| 二周目の確定塔 | 0.4679 | 0.2464 | 0.4265 | 0.3184 | 0.4763 | 0.3871 |
| 一周目の確定塔 | 0.3669 | 0.2025 | 0.2400 | 0.3856 | 0.4496 | 0.3289 |

効果量（二周目との差。差そのものと、折り間の散らばりで割った値の両方）:

| 系統 | 折りごとの差 | 平均 | 折り間 SD | 標準化 |
|---|---|---|---|---|
| P\*-COCO | +0.2389 / +0.4254 / +0.1829 / +0.2968 / +0.1994 | **+0.2687** | 0.0980 | +2.74 |
| P\*-ImageNet | +0.1483 / +0.1120 / +0.0040 / +0.1146 / +0.0779 | **+0.0914** | 0.0548 | +1.67 |

**5 折りとも二周目を上回る。** ただし折り単位の全数同符号は主張に使わない（規約どおり記述統計）。

### test（確定塔について折りごとに一度。G3）

| | A | B | C | D | E | 平均 |
|---|---|---|---|---|---|---|
| **P\*-COCO** | 0.4680 | 0.5500 | 0.4830 | 0.5268 | 0.5603 | **0.5176** |
| **P\*-ImageNet** | 0.3587 | 0.4646 | 0.3427 | 0.4760 | 0.4054 | **0.4095** |
| 二周目 | — | — | — | — | — | 0.256（契約 §2 の記載） |
| 一周目 | — | — | — | — | — | 0.225（契約 §2 の記載） |

台帳 `test_access_<系統>_<折り>.json` は **10 行ちょうど**（確定塔 2 × 5 折り）、すべて
`status: completed`。確定塔以外の test 評価は 0 件。二重評価は `open("x")` が
`FileExistsError` で拒む（実際に投げることを確かめた）。

### 折り A と S4 の並置（判定には使わない）

| | 折り A の val J | S4（0.6447 ± 0.0119）との差 | S4 の SD の何倍 |
|---|---|---|---|
| **P\*-COCO** | 0.7068 | **-0.0621（上回る）** | 5.2 |
| **P\*-ImageNet** | 0.6162 | +0.0285 | 2.4 |
| 二周目 | 0.4679 | +0.1768（契約の記載 0.177） | 14.9 |

### P\*-21

**UNKNOWN。** 追加 6 動画の画像がこのホストに無い（§A-5）。注釈だけでは学習できない。

## 8. Task F — 検証

| 検査 | 結果 |
|---|---|
| L1+L2 `make task-validate` | exit 0（WARN 3 件は起票時の分母が占位 0。承認済み） |
| L3 `make task-preflight` | **exit 0**。10 PASS / 0 WARN / **4 SKIP** / 0 FAIL |
| `make spec-check` | pass。9 規則で hits 0 |
| `make forbidden-check TASK=…` | **pass**。violations 0 / permitted 2,801 / 却下された宣言 0 |
| 試験 `pytest tests/` | **669 通過 / 6 失敗**。6 件は**いずれも分岐点 `cb3fcaa1` でも失敗する既存の失敗**（作業木を分岐点に立てて実測した） |
| `make runindex` | 混入 0 件。本契約の task_id を持つ行は **339**（fine-tune 31 = 完了 28 + 未完了 3、特徴抽出 28、時間ヘッド 280） |

L3 の SKIP 4 件は P2 `cuda_ext_loaded` / P3 `deterministic_flags` / P12 `refs_resolved` /
**P14 `proposal_card_checked`（導入前の契約のため対象外）**。SKIP は合格ではなく
「実行されなかった」である。

#### 報告を書いた後は P13 と P14 が SKIP に変わる

`result.yaml` に関門の判定を書いた後に L3 を回すと、P13 と P14 は
「完了済み（result.yaml に verdict あり: 3 件）のため対象外」で SKIP になり、
**9 PASS / 0 WARN / 5 SKIP / 0 FAIL** になる。

**完了判定 i が根拠にする P13 の PASS は、報告を書く前の実測である**（本契約では
取り込み直後と Task F の検証の二度、いずれも `対称性の表 1 個 / 15 行に UNKNOWN と
理由欠落は無い` で PASS した）。対称性の表そのものは変わっていない。

### 既存の失敗 6 件（本契約と無関係）

`tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`、
`tests/test_fetch_task.py::test_rejects_unknown_file_name`、
`tests/test_research_logger.py` の 4 件。分岐点でも同じく失敗する。

## 9. spec.yaml の差し替えが一度失われた件

Task A-1 と A-7 の差し替えは 2026-09-22 に入れ、L3 の P4 も一度 PASS した。
しかし Task F の検証で P4 が再び FAIL し、`spec.yaml` が占位に戻っていた。

reflog:

    b663f214 HEAD@{7}: commit: 契約の取り込みと prereg の固定
    b663f214 HEAD@{6}: reset: moving to HEAD          ← ここで失われた
    cb3fcaa1 HEAD@{5}: checkout: moving from feat/stage1-phase-tower-r3 to phase0
    b663f214 HEAD@{4}: checkout: moving from phase0 to feat/stage1-phase-tower-r3

**この reset と往復は実行者の操作ではない。** 本ホストの keeper でもない:
keeper の直前の動作は 2026-09-22 16:24:33 で、本 commit は 16:33:50、以降
16:54:33 から `一時停止中` と記録され続けている（`~/claude-sync/sync-alerts.log`）。
誰が行ったかは特定できていない。

**run どうしの整合は保たれている。** 全 run が記録した `contract_sha256` は
差し替え前の `b7d070f5…` で揃っており、消失は最初の run より前に起きた。
差し替え直しの後、最終の `spec.yaml` は run の記録と食い違う。これは
**契約が実行者に `spec.yaml` の編集を求める（Task A-1・A-7）以上、
正しい順序で実行しても run の記録は編集後の値になるはず**だったもので、
外部の reset によって編集前の値で記録された。

**実行者の落ち度は、差し替えが commit に入ったことを再確認しなかった点である。**
`git add tasks/<task_id>/` を含む commit を行った時点で作業木は既に戻っており、
差分が無いため何も staging されなかった。直した後は `git show HEAD:<path>` で
commit の中身を直接読んで確かめた。

## 4. 起票者の誤り

| # | 型 | 内容 |
|---|---|---|
| 1 | `asserted_without_measuring` | SPEC §2 と `inputs.code.entrypoints` が二周目の道具を `train_phase_tower_r50.py` / `run_stage1_ptower.py` / `select_stage1_ptower.py` と書くが、これらは**一周目**のもの。二周目が実際に使ったのは `stage1_ptower_r2.py` / `run_stage1_ptower_r2.py` / `select_stage1_ptower_r2.py`。なお `train_phase_tower_r50.py` の前処理は `Resize((224,224))`（正方への圧縮、切り出しなし）で、SPEC が「実測」と書く「短辺 256 → 中央 224」ではない。前処理の記述そのものは**二周目の実物に対しては正しい** |
| 2 | `self_contradiction` | `outputs.expected_runs: 308` は fine-tune 28 + 時間ヘッド 280 の和だが、SPEC の Task D-1 が求める特徴抽出 28 本を数えていない。掃引を実装すると run は **336** になる |
| 3 | `asserted_without_measuring` | prereg §2 の「既定（batch 64）」が装置に収まらない。起票時に記憶領域を測っていない。SPEC §2 は「所要時間と記憶領域は Task B で実測する」と書くので**停止条件としては想定内**だが、既定値そのものが実行不能である点は記録に残す |
| 4 | `asserted_without_measuring` | SPEC §2 と prereg §3 が腕1 を「T-2026-09-19-stage1-detector-towers-r2 の処方」と呼ぶが、その契約は存在しない。実在するのは `tasks/T-2026-09-18-stage1-detector-towers`。参照先の中身（COCO 初期化）は一致している |
| 5 | `asserted_without_measuring` | SPEC §2 は「追加 6 動画（17〜22）の注釈は ilya に在る」と書く。注釈は在るが**画像が無い**ため P\*-21 は UNKNOWN になる。起票時に画像の有無は測られていない |

