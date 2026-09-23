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

## 4. 起票者の誤り

| # | 型 | 内容 |
|---|---|---|
| 1 | `asserted_without_measuring` | SPEC §2 と `inputs.code.entrypoints` が二周目の道具を `train_phase_tower_r50.py` / `run_stage1_ptower.py` / `select_stage1_ptower.py` と書くが、これらは**一周目**のもの。二周目が実際に使ったのは `stage1_ptower_r2.py` / `run_stage1_ptower_r2.py` / `select_stage1_ptower_r2.py`。なお `train_phase_tower_r50.py` の前処理は `Resize((224,224))`（正方への圧縮、切り出しなし）で、SPEC が「実測」と書く「短辺 256 → 中央 224」ではない。前処理の記述そのものは**二周目の実物に対しては正しい** |
| 2 | `self_contradiction` | `outputs.expected_runs: 308` は fine-tune 28 + 時間ヘッド 280 の和だが、SPEC の Task D-1 が求める特徴抽出 28 本を数えていない。掃引を実装すると run は **336** になる |
| 3 | `asserted_without_measuring` | prereg §2 の「既定（batch 64）」が装置に収まらない。起票時に記憶領域を測っていない。SPEC §2 は「所要時間と記憶領域は Task B で実測する」と書くので**停止条件としては想定内**だが、既定値そのものが実行不能である点は記録に残す |
| 4 | `asserted_without_measuring` | SPEC §2 と prereg §3 が腕1 を「T-2026-09-19-stage1-detector-towers-r2 の処方」と呼ぶが、その契約は存在しない。実在するのは `tasks/T-2026-09-18-stage1-detector-towers`。参照先の中身（COCO 初期化）は一致している |
| 5 | `asserted_without_measuring` | SPEC §2 は「追加 6 動画（17〜22）の注釈は ilya に在る」と書く。注釈は在るが**画像が無い**ため P\*-21 は UNKNOWN になる。起票時に画像の有無は測られていない |

