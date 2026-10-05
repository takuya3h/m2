# data/

データセット・注釈・前処理済みの成果物を置くディレクトリ。**大半は Git 管理しない**（§6）。

本書の数値は **2026-10-05 に aolab で実測した値**である（`du -shL`、`find -L -type f | wc -l`）。
`data/` の中身はホストごとに違い得る。他のホストでは §7 の手順で確かめること。
旧版（2026-07-01）は `raw/exo/`・擬似ラベル・外部データセットを前提にしていたが、
それらは**空のまま使われていない**ため本版で実態に合わせた。

---

## 1. 全体像

```
data/                          規模（aolab, 2026-10-05）
├── README.md                  本書（Git 管理）
├── splits/                    公式分割の動画 ID（Git 管理）              24K
├── raw/                       生のフレームとセグメンテーション         11G / 235,716 files
│   ├── ego/                   EgoSurgery のフレーム（主データ）        3.9G
│   ├── EgoSurgery_HTS2/       EgoSurgery-HTS（論文版レイアウトに再構成） 2.2G
│   ├── OpenSurgery_Dataset/   OpenSurgery 完全版（HTS の上位集合）      4.3G
│   └── exo/view_1..5/         空（.gitkeep のみ。未使用）
├── annotations/               注釈                                    517M
│   ├── egosurgery_tool/       術具検出 COCO（公式 3 分割）               42M
│   ├── egosurgery_tool_folds/ 術具検出 COCO（動画単位 5 折り A〜E）      68M
│   ├── egosurgery_tool_hand/  術具 15 + 手 4 クラスの COCO               37M
│   ├── egosurgery_phase/      工程ラベル CSV（Git 管理）               368K
│   ├── egosurgery_hts/        HTS の 3 種セグメンテーション（正本）     364M
│   └── _deprecated/           旧版の手 4 クラス注釈                     7.5M
├── processed/                 前処理済みの manifest・特徴・キャッシュ   12G
├── external/weights/          事前学習済みの重み                        9.1G
└── eval_staging/              COCO 評価器向けの配置（シンボリックリンク）
```

---

## 2. `splits/` — 公式分割（Git 管理）

| ファイル | 内容 |
|---|---|
| `ego_train.txt` | 01, 02, 03, 06, 08, 11, 12, 13, 14, 15（10 動画） |
| `ego_val.txt` | 09, 10（2 動画） |
| `ego_test.txt` | 04, 05, 07（3 動画） |
| `exo_sync_map.json` | `{}`（空。未使用） |
| `surgeon_folds.json` | `{}`（空。未使用） |

1 行 1 **動画 ID** である（フレーム ID ではない）。規約 `context/conventions.md#split` と
`src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS` が同じ値を持つ。

**動画単位 5 折りの正本は `docs/stage0/A1_fold_table.md`**（規約 `conventions#folds`）。
折り A は公式分割そのものである。折りの注釈は `annotations/egosurgery_tool_folds/` にある。
**分割を書き換えない**（契約の禁止事項 `no_split_redefine`）。

---

## 3. `raw/` — 生データ

### 3.1 `raw/ego/` — EgoSurgery のフレーム（主データ）

| 下位 | 動画 | 枚数 |
|---|---|---:|
| `train/` | 01 02 03 06 08 11 12 13 14 15 | 9,658 |
| `val/` | 09 10 | 1,516 |
| `test/` | 04 05 07 | 4,266 |
| `other(17~21)/` | 17 18 19 20 21（追加動画） | 10,461（17: 56 / 18: 946 / 19: 5,179 / 20: 1,560 / 21: 2,720） |

- 配置は `<分割>/<動画>/<動画>_<クリップ>_<フレーム番号>.jpg`（例 `train/01/01_1_0124.jpg`）
- 枚数には注釈の無いファイルも含む。注釈つきの数は §4 を正とする（例: train の COCO は 9,657 画像）
- `other(17~21)/` は工程塔 P\*-20 の追加の訓練動画（`conventions#folds` の「追加 6 動画」のうち 17〜21。
  22 はフレームが無い）。**どの折りの val・test にも使わない**。ディレクトリ名に括弧とチルダを含むため、
  シェルでは引用符で囲むこと

### 3.2 `raw/EgoSurgery_HTS2/` と `raw/OpenSurgery_Dataset/`

手・術具・把持関係のセグメンテーションの元データ。由来と論文値との照合は各ディレクトリの
`README.md`（OpenSurgery は `AUDIT.md`・`SCALE_VERIFICATION.md` も）にある。

| ディレクトリ | 内容 | 規模 |
|---|---|---|
| `EgoSurgery_HTS2/` | 論文（arXiv:2503.18755）のレイアウトに再構成。`images/` `hand_seg/` `tool_seg/` `hand_tool_seg/` `image_list.txt` | 2.2G / 91,529 files |
| `OpenSurgery_Dataset/` | `00_master_annotations/` `01_frames/` `02_hand/` `03_tool/` `04_handtool/` `05_egosurgery_hts/` | 4.3G / 118,281 files |

公式配布は https://github.com/Fujiry0/EgoSurgery （CC BY-NC-SA 4.0、学術・非商用）。
`OpenSurgery_Dataset/` には同期の衝突で生じた `AUDIT.sync-conflict-*.md` が 4 件ある（中身の整理は未了）。

### 3.3 `raw/exo/`

`view_1`〜`view_5` は `.gitkeep` だけの空ディレクトリである。Exo 映像は取得していない。

---

## 4. `annotations/` — 注釈

### 4.1 術具検出（COCO）

15 クラス: Bipolar Forceps, Electric Cautery, Forceps, Gauze, Hook, Mouth Gag, Needle Holders, Raspatory,
Retractor, Scalpel, Scissors, Skewer, Suction Cannula, Syringe, Tweezers。

| ディレクトリ | 内容 | 規模 |
|---|---|---|
| `egosurgery_tool/instances_{train,val,test}.json` | 公式 3 分割。train 9,657 画像 / 32,272 box、val 1,515 / 4,707、test 4,265 / 12,673。`file_name` は `train/01/01_1_0124.jpg` の形で `raw/ego/` からの相対。**Git 管理** | 42M |
| `egosurgery_tool/hand/{train,val,test}.json` | 手 4 クラス（Own/Other hands left/right）を術具の分割に合わせた COCO。train 9,627 画像 / 27,726 mask | — |
| `egosurgery_tool_folds/{A..E}/instances_{train,val,test}.json` | 動画単位 5 折り。`scripts/make_fold_annotations.py` が生成。折り A は公式ファイルの複製（sha256 一致）。生成の記録は `fold_report.json` | 68M |
| `egosurgery_tool_hand/instances_*.json` | 術具 15 + 手 4（Own/Other hands left/right）= 19 クラス | 37M |
| `egosurgery_tool_hand/{train,val,test}.json` | 手 4 クラスのみ | （同上） |

規約 `conventions#det_groups` の標的群・陰性対照群はこのクラス名と完全一致で照合する。
公式 3 ファイルは ID が 0 始まりで分割間で衝突するため、プールするときは振り直す
（`make_fold_annotations.py` の注記）。

### 4.2 工程（`egosurgery_phase/`、Git 管理）

23 個の CSV（`<動画>_<クリップ>.csv`、動画 01〜15）。列は `Frame,Phase`（例 `01_1_0001,disinfection`）。
9 工程: anesthesia, closure, design, disinfection, dissection, dressing, hemostasis, incision, irrigation
（番号は `processed/phase_manifest/phase_vocab.json`）。

### 4.3 手・術具・把持のセグメンテーション（`egosurgery_hts/`、正本）

`hand_seg/`（手 4 クラス）、`tool_seg/`（術具 31 クラス）、`hand_tool_seg/`（把持関係 5 クラス、
構造的欠落の `loss_mask/` つき）。各々 `train/val/test.json`（術具の分割に整合）と、どの分割にも属さない `extra.json`。
詳細は `egosurgery_hts/README.md` と各 `build_report.md`。

### 4.4 その他

| 経路 | 内容 |
|---|---|
| `_deprecated/egosurgery_hand4/` | 旧版の手 4 クラス注釈。`configs/stage/s2_hand_independent.yaml` と監査スクリプトが参照する。新規には使わない |
| `egosurgery_hts*_coverage_report.md`・`egosurgery_hts_current_coverage.md` | HTS の被覆の監査（Git 管理） |
| `egosurergyhts_open` | 拡張子の無い Markdown。EgoSurgery-HTS の論文値の抜き書き（Git 管理。名前は綴りが崩れているが参照元が不明のため残している） |

---

## 5. `processed/` と `external/` と `eval_staging/`

### 5.1 `processed/` — 前処理済み（12G、すべて再生成できる）

| ディレクトリ | 内容 | 生成するスクリプト |
|---|---|---|
| `phase_manifest/` | 工程の manifest（train 13 クリップ / 9,657 フレーム、val 3 / 1,515、test 6 / 4,265）と `phase_vocab.json` | `scripts/build_phase_manifest.py` |
| `joint_manifest/` | 工程と術具 box を束ねた manifest と `tool_categories.json` | `scripts/build_joint_manifest.py` |
| `stage1_features/<run>/` | 工程塔の凍結特徴のキャッシュ（`all_gap.npz` と出所の json）。run 名は塔・lr・折り・seed | `scripts/stage1_ptower*.py`、`scripts/extract_stage1_features*.py` |
| `t1a_regiontoken/<run>/` | 検出器の領域トークン | `scripts/extract_t1a_regiontoken_aligndetr.py` ほか |
| `b2a_detsignal/<run>/` | 検出器の術具存在信号 | `scripts/extract_b2a_toolpresence_aligndetr.py` ほか |
| `phase_context/<run>/` | P→D 界面用の工程文脈 | `scripts/extract_phase_context.py` |
| `oracle_toolpresence/`・`oracle_handfeature/` | 正解から作った術具存在・手特徴（参照入力段の「正解」） | `scripts/build_oracle_toolpresence.py`・`build_oracle_handfeature.py` |
| `c5neck/` | C5 neck の重み（seed 42/123/456） | `scripts/extract_c5neck.py` |
| `ego_frames/` `exo_clips/` `features/` `copypaste_bank/` | 空（`.gitkeep` のみ。未使用） | — |

名前の末尾が `.discarded_<日付>` のものは**破棄済み**の成果物で、使わない。

### 5.2 `external/weights/` — 事前学習済みの重み（9.1G）

COCO で学習した検出器の重み（Relation-DETR、DINO、Align-DETR、Co-DINO、DDQ、Focus-DETR、MR-DETR、VFNet など）と、
凍結源・初期化の重み（`relation_detr_s0frozen_init_seed42.pth`、`aligndetr_s0frozen_*`、`sensex_codino_seed42/` など）。
工程塔の COCO 初期化は `relation_detr_resnet50_800_1333_coco_1x.pth` を使う（`scripts/stage1_ptower_r3.py`）。
凍結源の sha256 の正本は `conventions#frozen_source`。**上書きしない。**

`external/cholect45/` `egoexor/` `phakir/` は空（`.gitkeep` のみ。未取得）。

### 5.3 `eval_staging/egosurgery_val/`

COCO 形式の評価器が期待する `val2017/` と `annotations/instances_val2017.json` の配置を、
シンボリックリンクで作ったもの（`scripts/extract_stage1_features.py` が使う）。

- `val2017` → `/home/ubuntu/slocal2/m2/data/raw/ego`
- `annotations/instances_val2017.json` → `/home/ubuntu/slocal2/m2/data/annotations/egosurgery_tool/instances_val.json`

🔴 **リンクは絶対パスで Git 管理されている。** 経路の違うホストでは切れる。

---

## 6. Git 管理

ルートの `.gitignore` が実装している。

| 区分 | 対象 |
|---|---|
| **管理する** | `data/README.md`、`data/splits/*`、`annotations/egosurgery_tool/instances_*.json`、`annotations/egosurgery_phase/*.csv`、`annotations/` 直下の監査 Markdown と `egosurergyhts_open`、`eval_staging/` の 2 リンク、空ディレクトリの `.gitkeep`（17 件） |
| **管理しない** | `raw/**`、`processed/**`、`external/**`、`annotations/**/*.json`（上の例外を除く）、`annotations/egosurgery_hts/**` |

管理しないものは**ホスト間で中身が揃っている保証が無い**。実験の前に必要なファイルの有無と
sha256（凍結源・キャッシュは出所の json に記録がある）を確かめること。

**契約は `data/**` に書き込まない**（`tools/check_forbidden.py` が常に禁止する）。
注釈の生成や配置の変更は、契約の外で利用者の判断を経て行う。

---

## 7. 確かめ方

```bash
cd data
du -shL raw/* annotations/* processed/* external/*      # 規模
find -L raw/ego -type f | wc -l                         # 枚数
git ls-files . | grep -v '\.gitkeep$'                   # Git 管理の対象
python - <<'EOF'
import json
for s in ("train", "val", "test"):
    d = json.load(open(f"annotations/egosurgery_tool/instances_{s}.json"))
    print(s, len(d["images"]), len(d["annotations"]))
EOF
```
