# 実験設定の索引（現在従うべき値）

**この文書は正本ではない。** 各項目の正本は「出所」欄が指すファイルである。
値が食い違ったら**出所を正とする**。作成 2026-09-18（`T-2026-09-18-stage1-detector-towers` の
実行中に、利用者の求めでまとめた）。

未確認の項目は **UNKNOWN** と書く。推測で埋めない（`conventions#prohibitions` の `no_estimated_values`）。

---

## 0. この文書の読み方

| 記号 | 意味 |
|---|---|
| 🔴 | 契約や文書の記載と実測が食い違った箇所。**実測を正とする**（`conventions#issuer_cautions` 1） |
| ⚠️ | 正本が repo に無い、または未確定 |

---

# 1. 全実験に共通する規約

## 1.1 分割と折り

出所: `conventions#split` / `conventions#folds`。**折り表の正本は `docs/stage0/A1_fold_table.md`**
（契約 `T-2026-09-17-fold-table`、PR #176）。

動画単位の 5-fold。**折り A は公式分割そのもの**である。

| 折り | test（3） | val（2） | train（10） |
|---|---|---|---|
| A | 04, 05, 07 | 09, 10 | 01, 02, 03, 06, 08, 11, 12, 13, 14, 15 |
| B | 01, 03, 14 | 02, 08 | 04, 05, 06, 07, 09, 10, 11, 12, 13, 15 |
| C | 02, 08, 11 | 06, 12 | 01, 03, 04, 05, 07, 09, 10, 13, 14, 15 |
| D | 06, 13, 15 | 04, 05 | 01, 02, 03, 07, 08, 09, 10, 11, 12, 14 |
| E | 09, 10, 12 | 07, 15 | 01, 02, 03, 04, 05, 06, 08, 11, 13, 14 |

- 各動画は **test にちょうど一度**現れる。val は全折りを通じて**高々一度**しか使わない
- 公式分割（`data/splits/ego_{train,val,test}.txt`）は train `01 02 03 06 08 11 12 13 14 15` /
  val `09 10` / test `04 05 07`。**折り A と完全一致することを実測済み**（2026-09-18）
- **`data/splits/` の既存ファイルは変えない**
- 折りごとの注釈は `data/annotations/egosurgery_tool_folds/<fold>/instances_{train,val,test}.json`
  （`scripts/make_fold_annotations.py` が生成。`.gitignore:10` で追跡外）。
  **折り A は公式ファイルの複製で sha256 が一致する**

### 追加 6 動画

工程塔 P\*-21 のみ `17, 18, 19, 20, 21, 22` を足す。
**用途は訓練のみ。どの折りの test にも val にも現れない。**

### 動画あたりの規模（実測 2026-09-18）

15 動画の合計は **15,437 枚**（train 9,657 / val 1,515 / test 4,265）。
🔴 **公式 3 ファイルの `image_id` と `annotation_id` はいずれも 0 始まりで衝突する**
（image 4,265 件・annotation 12,673 件）。プールして使うときは振り直しが要る。

## 1.2 test の規律

出所: `conventions#folds` の「規律」。

> **選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
> test は腕ごとに一度だけ触る。折りをまたいで val を使い回さない。**

## 1.3 評価 recipe

出所: `conventions#eval_recipe`（転記元 `src/egosurgery/utils/eval_recipe.py`）。

| 名前 | 設定 | 使う場面 |
|---|---|---|
| `NMS_FREE_TEST_CFG` | `score_thr=0.0` / `max_per_img=300` / `nms_pre=None` / `nms_iou=None` | **比較の三角形と DETR-family の公式評価** |
| `LOCKED_DOWN_TEST_CFG` | `score_thr=1e-8` / `max_per_img=300` / `nms_pre=3000` / `nms_iou=0.6` | 上記以外 |
| `PHASE_EVAL_PROTOCOL` | `inference_protocol=online_causal` / `jaccard_mode=strict` | 工程評価（固定） |

⚠️ `select_box_nums_for_evaluation` は転記元に定義が無く **UNKNOWN（転記元未特定）**。

`runindex` に現れる `eval_recipe_id` の実例: 検出 val `b66459018a92` / 工程 `e98ffddee042` /
D→P 系 `4ac382e09c21`・`cef2b5817cdd`。

## 1.4 指標

出所: `CLAUDE.md`（プロジェクト指示）。

- **工程**: **macro Jaccard**（同方向要件として frame accuracy を併記）
- **検出**: **overall mAP と標的群 AP の二本立て**（陰性対照群を添える）
- 効果量は**差そのもの**と、**分母の折り間の散らばりで割った値**の両方を併記

## 1.5 判定の規則

出所: `CLAUDE.md`。

1. 評価は**動画単位の五分割と五つの種**。**判定単位は動画で 15 個の対の差**
2. 主判定は**折りをクラスタとするブロック・ブートストラップの信頼区間が零を含まないこと**。
   同一折りの 3 動画は同じモデルで評価されるため独立ではない。**クラスタは折りに取る**
3. **主判定は一つだけ**置く。確認的な腕は事前に列挙し、族内で **Holm 補正**を当てる
4. **折り単位の全数同符号は主張に使わない**（五分割では符号検定の最小の値が原理的に有意へ届かない）。
   記述統計としてのみ併記する

## 1.6 σ（散らばり）

出所: `conventions#sigma`。`spec.yaml` が `sigma_policy` を省略した場合に継承される既定。

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

⚠️ **この既定は暫定**である（ddof=0 / ddof=1 の正本は未決定）。
判定規約を書くときは絶対値を `abs(...)` の関数形で書く（縦線は markdown 表を壊す）。

### 実測されている σ（2026-09-18 時点）

| 対象 | σ（pstd） | 出所 |
|---|---:|---|
| 検出塔 S0（3 seed） | 0.0033960155 | `runindex/experiments.csv` の `baselines/s0/relationdetr_bbox@val`（mAP 平均 0.7267943333） |
| W1 界面 run（3 seed） | 0.004540 | `runindex/index.csv` の step `t1b_filmonly`（mAP 0.736802 / 0.731410 / 0.725682） |

## 1.7 凍結源

出所: `conventions#frozen_source`。

    third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
    sha256 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    195,421,066 bytes

**変更してはならない。** 照合に失敗したら `no_frozen_change` の違反として実行を中止する。
**skip する経路は設けない。** 実行直前検査（P5）は `meta.kind: exp` の契約に適用される。

## 1.8 禁止事項

出所: `conventions#prohibitions`。

| id | 内容 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

## 1.9 命名と証跡

出所: `conventions#naming`（転記元 `README.md`）。

    {step}_{seq:03d}_{description}_seed{seed}

`ExperimentManager` が自動採番する。手作業で命名しない。
各実験に `config.yaml` / `command.sh` / `git_commit.txt` / `metrics.json` /
`per_class_ap.json` / `notes.md` を残す。

⚠️ `CLAUDE.md` は「旧規則の `{step}_{seq:03d}_{desc}_seed{seed}` は撤回された」とし、
**既存の実験フォルダ名は当時のまま**とする。`conventions#naming` との食い違いは未解決。

## 1.10 実行環境

出所: `conventions#env_p0`。

    source .venv-relation-detr/bin/activate   # 検出系
    source .venv/bin/activate                 # 解析・工程系

**activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へ落ちて数値が変わったまま完走する。**
拡張のロード確認をログに残すこと。

---

# 2. 実験の種類別の設定

## 2.1 検出塔の学習（D\*-COCO / D\*-ImageNet）

出所: `experiments/baselines/_legacy_score_thr_0/s0_016_relationdetr_bbox_seed42/`
の `command.sh` / `config.yaml` / `metrics.json`（凍結源を生んだ run）。

| 項目 | 値 |
|---|---|
| 入口 | `accelerate launch --num_processes 2 main.py`（**`scripts/train_t1b.py` ではない**） |
| config | `configs/train_config_egosurgery_seed{42,123,456}.py` |
| **数値精度** | **fp16 の自動混合精度**（`--mixed-precision fp16`） |
| epoch | 12 |
| scheduler | `MultiStepLR(milestones=[10], gamma=0.1)` |
| batch | per-GPU 2 × 2 枚 = **実効 4**（`lr_scaling: linear_x2`） |
| lr | 1e-4 |
| 最適化器 | `AdamW(lr=1e-4, weight_decay=1e-4, betas=(0.9, 0.999))` |
| param_dicts | `param_dict.finetune_backbone_and_linear_projection(lr=1e-4)` |
| 勾配の刈り込み | `max_norm = 0.1` |
| 増強 | `presets.detr`（乱択 hflip・11 段の乱択解像度・乱択 crop） |
| 解像度 | 短辺 480〜800 の乱択、長辺 ≤1333 |
| model config | `configs/relation_detr/relation_detr_resnet50_egosurgery.py` |
| backbone の凍結 | `freeze_indices=(0,)` = **stem のみ凍結**（layer1〜4 は学習する） |
| 初期化（COCO 塔） | `data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth`（196,140,106 bytes）。class head を 91→15 で再初期化 |
| 初期化（ImageNet 塔） | `resume_from_checkpoint = None`。backbone は torchvision の ImageNet-1K、検出ヘッド（transformer・query・予測ヘッド）は乱数初期化 |
| num_workers / pin_memory | 4 / True |
| seed | 折り A は 42・123・456、折り B〜E は 42 |
| 到達点（凍結源） | val mAP **0.729749** / AP_rare 0.757599 / AP_common 0.725107（best epoch 12、host philip） |

🔴 **契約 `T-2026-09-18-stage1-detector-towers` は当初「全 run を TF32」と定めていたが誤りだった。**
`prereg.md` §2 は「凍結源は fp32 で学習されている」を前提にしていたが、実測は fp16 である。
`C2` の TF32 の測定は **fp32 の界面 run** が基準であり、検出塔のフル学習には当てはまらない。
利用者の判断（2026-09-18）で**全 run を凍結源と同じ fp16** とした。

### 同時実行の最適点（efros・A6000 2 枚・実測 2026-09-18）

| 同時本数 | 1 run の 1 step | 総処理量 | 単独比 |
|---:|---:|---:|---:|
| 1 | 0.554 s | 1.805 step/s | 1.00× |
| **2** | 約 0.92 s | **2.17 step/s** | **1.20×** |
| 3 | 約 1.37 s | 2.19 step/s | 1.21× |

**2 本で GPU が飽和する**（使用率の平均 91〜96%）。3 本目は総処理量を 1% しか増やさず
per-run を 1.5 倍遅くするだけなので採らない。1 epoch は 2405 step。

## 2.2 工程塔の学習（P\*）

出所: `docs/stage0/B_pd_b2_b4_results.md` §2.1。

| 項目 | 値 |
|---|---|
| 暫定塔 | ImageNet-R50 を **train の 10 動画のみ**の工程ラベルで微調整 |
| epoch / 時間 | 3 epoch / 105 秒 |
| 塔単体の val | accuracy **0.6924** / macro_f1 **0.4360**（フレーム単位・時系列ヘッド無し） |
| 時系列ヘッド | TeCNO（`s4_phase_baseline` 系） |
| 評価 | `online_causal` + `jaccard_mode=strict` |
| 1 run の所要時間 | 11.9〜30.0 秒（n=11、A6000 1 枚。`docs/stage0/B_contract_b_results.md` §3） |

⚠️ **Stage 1 の正式な P\* 塔の処方は repo に無く UNKNOWN。**
上は「暫定・一 seed」で、Stage 1 では epoch を増やす前提と明記されている。
正式版は `T-2026-09-18-stage1-phase-tower`（ilya）が確定中。

🔴 前契約の SPEC が「十五動画」で学習と書いたのは **val 2・test 3 を含む分割違反**であり、
訂正済み（同 §2.1）。

## 2.3 界面 run・工程→検出（P→D）

出所: `scripts/train_t1b.py` と `experiments/transfer/pd_refin_empty_seed42/config.yaml`。

| 項目 | 値 |
|---|---|
| 入口 | `python scripts/train_t1b.py`（**単一プロセス。DDP 起動の記述はリポジトリ全域に 0 件**） |
| epoch | 6 |
| batch | **2**（実効 2） |
| lr / film_lr | 1e-4 / 5e-4 |
| 数値精度 | **fp32**（既定）。`--tf32` と `--amp {no,bf16,fp16}` は任意の引数で**既定 off** |
| 注入の型 | `film`（C5 に FiLM）/ `ca` / `camt` / `hc` / `clsbias` |
| 学習範囲 | W1 = `--trainable film`（266,880 param）／W2 相当 = `--trainable all`（25,505,568 param） |
| backbone | **W1・W2 とも `freeze_indices=(0,1,2,3)` で全段凍結**（キャッシュの境界も同一） |
| warm-start | `checkpoints/incoming/seed{seed}/best_ap.pth`。FiLM は zero-init = 恒等 |
| 参照入力段 | 空（`--zero-ctx`）／予測（`--phase-source real`）／正解（`oracle`）／正解⊕予測（`both`・18-d） |
| 工程 context | `data/processed/phase_context/relation_detr_seed42/{split}_phasectx.npz`（9 次元/frame） |
| 評価 | val、`score_thr=0.0`、topk 300 |

### 実測（efros・A6000 1 枚）

| 量 | 値 |
|---|---:|
| 1 step（fp32） | 0.4946 s（2.02 it/s） |
| 1 epoch | 4,809 step ≒ 39.6 分 ＋ val 評価 2.2 分 = **41.8 分** |
| 1 run（6 epoch） | **4.18 h** |
| 1 step（tf32） | 0.4225 s。run 全体で **1.171×** |

🔴 **UNKNOWN（未解決）**: t1b の実効バッチ **2** と S0 検出器学習の正本 **4**（per-GPU 2 × 2 枚 DDP）が
食い違う。四段の内部比較は同一条件で成立するが、**S0 との比較可能性は未確認**
（`T-2026-08-29-lecun-detector-env-pd` の UNKNOWN 1）。

## 2.4 界面 run・検出→工程（D→P）

出所: `runindex/experiments.csv`、`scripts/train_b2a.py` / `scripts/train_phase_tower_r50.py`。

- `transfer/b2a_det2phase_toolpresence` 系（`eval_recipe_id` `4ac382e09c21`）
- `transfer/b4_refin_{empty,pred,oracle,both}` 系（`empty/pred/oracle` は `4ac382e09c21`、`both` は `cef2b5817cdd`）
- seed 42 / 123 / 456。1 run 14.5〜32.2 秒、塔の学習 105 秒
- 送り手のタグ分離は `RELDETR_SIGNAL_TAG`

## 2.5 腕を区別する三つの軸

出所: `CLAUDE.md`。

| 軸 | 値 |
|---|---|
| 方向 | なし / 検出→工程 / 工程→検出 / 双方向 |
| 参照入力段 | 空 / 予測 / 正解 / 正解と予測の和 |
| 学習範囲 | W1（入力適合層のみ）/ W2（末端ブロックまで）/ W3（受け取り塔全体） |

- **上限として使えるのは参照入力段の最後の段だけ**（旧来の「上限」という語は廃止された）
- **受け取り手を全腕で揃える**: 塔と界面の型・容量・水準・スケジュール・種を同一にし、
  **変えるのは界面の入力だけ**にする

## 2.6 対照群

出所: `tools/estimate_tier_cost.py` の run 列挙。

| 対照 | 内容 |
|---|---|
| 乱数入力 | `t1_ctrl_random_pd` |
| 同量非関連特徴 | `t1_ctrl_unrelated`（P→D の L3） |
| 時間・動画間 shuffle | `t1_ctrl_shuffle_pd`（2 種） |
| 逆選別 | `t1_ctrl_reverse_pd` |
| 注入効果の分離 | `--zero-ctx`（context を 0 に固定した同スケジュール fine-tune） |

**陰性対照は両方向で取る**（`conventions#issuer_cautions` 3）。
片方向では「常に 0 を返す壊れ方」と区別できない。

---

# 3. 設定を変えるときの手続き

出所: `conventions#proposal_gate` の「設定・設計・問いの三水準」。

| 水準 | 含むもの | 変えるときの手続き |
|---|---|---|
| **設定** | 学習率・epoch・batch・seed、特徴の取り出し層、豊かさ L0〜L3、学習範囲 W1/W2、損失の重み、送り手の掃引点 | **初回の契約に掃引として入れる。後から足さない** |
| **設計** | 界面の型、塔の選択、方向、信号の種類、時間文脈の与え方 | 提案カードを書き直し、批判会話を通す |
| **問い** | どの仮説を測るか、相互改善の定義、論文の段 | 利用者が決める。関門で扱う |

設定の掃引は初回にセットで試す。主要因は掃引し、交互作用は固定する。
何を固定したかと理由をカード #14 に書く。**掃引集合はカードに書いた時点で固定する。**
最良格子の選定は折り内 val、test は腕ごとに一度。

---

# 4. 所要時間の正本（`tools/estimate_tier_cost.py`）

| run 型 | 時間 | 実測/代理 | 出所 |
|---|---:|---|---|
| 工程側の界面 run（50 epoch） | 30.0 s | 実測 | `docs/stage0/B_contract_b_results.md` §3 |
| 工程塔の学習（3 epoch・1 seed） | 105 s | 実測 | `docs/stage0/B_pd_b2_b4_results.md` §2.1 |
| 工程側の評価のみ run | 30.0 s | **代理（上界）** | 評価だけを分離した計測が無い |
| 検出側の W1 界面 run（6 epoch） | 4.00 h | 実測 | `T-2026-08-29` RESULT.md:88 |
| 検出側の W2 界面 run | **4.82 h** | **代理** | W2/W1 の 1 step 比 1.205（`T-2026-09-17-frozen-feature-cache-timing` の実測）× 4.00 h |
| 検出塔の学習（12 epoch） | 8.00 h | **代理（下界）** | フル学習の計時が repo に無い。**本契約で実測中** |
| 検出側の W3 界面 run | 8.00 h | **代理（下界/上界）** | 塔全体を更新するため検出塔学習の代理と同じ値 |
| 検出側の評価のみ run | — | **代理（上界）** | 評価だけを分離した計測が無い。学習 1 epoch 分を代理に置く |
| クリップ ID 識別プローブ | 30 s | **代理（下界/上界）** | プローブ単体の計時が無い。工程側の界面 run を代理に置く |

**検出側の行が GPU 時間の 99.9% を占める**（実測）。

### Tier 1 の日数（2026-09-18 時点）

| 前提 | 縮退なし |
|---|---:|
| 24h/日・Stage 1 + Tier 1〜3 の全体 | 87.5〜116.6 日 |
| 12h/日・Stage 1 + Tier 1 のみ | 159.9〜218.2 日 |

🔴 **節ごとに前提が違う。** `degrade` 節は 24h/日・全体、`deadline_sensitivity` 節は
12h/日・Stage 1 + Tier 1 のみである。**数字を引くときは必ず節と前提を添える。**
（`C1` §7 がこの取り違えをした。`C2` §6 で訂正済み）

---

# 5. 出所が repo に無いもの（UNKNOWN）

| # | 項目 | 理由 |
|---|---|---|
| 1 | **マスター計画 M 本体**（§5.1 の recipe 同一要件、§5.2 の塔の要求、Tier 表） | Claude アプリの面にあり CLI は読めない（`configs/notion.yaml` の `claude_app_surfaces`）。**コードから解決してはならない** |
| 2 | Stage 1 の正式な工程塔の処方 | `T-2026-09-18-stage1-phase-tower`（ilya）が確定中 |
| 3 | `select_box_nums_for_evaluation` | `eval_recipe.py` に定義が無い |
| 4 | t1b の実効バッチ 2 と S0 の 4 の不一致の扱い | `T-2026-08-29` の UNKNOWN 1。未解決 |
| 5 | σ の正本（ddof=0 / ddof=1） | `conventions#sigma` が「暫定」と明記 |
| 6 | 決定性設定の判定基準 | backlog B-20。preflight の P3 は宣言しても SKIP になる |
| 7 | 検出塔のフル学習の所要時間 | `T-2026-09-18-stage1-detector-towers` で実測中 |

---

# 6. 更新の作法

- **この文書の値を手で書き換えない。** 正本（出所欄）を直してから、この索引を合わせる
- 新しい実測が出たら、その契約の `RESULT.md` を出所として追記する
- 🔴 と ⚠️ は解消したら消す。**解消の根拠（契約 ID と実測）を添える**
