# l0b — raw bundle 来歴監査 REPORT（2026-07-29）

読み取り専用監査。組み立て・変換・マスク生成は一切していない。数値は全て実測（`all_results.json` と各 `task*.json` に機械可読で保存）。再現: `PYTHONPATH=src .venv-relation-detr/bin/python scripts/audit_l0b_raw_provenance.py`。

---

## 0. 対象と結論の要旨

- raw bundle ルート = `data/raw/OpenSurgery_Dataset`（他に SAM 疑似ラベルの実体は**リポ内に無い**：`data/annotations/pseudo_labels/{hand_tool_relation,bbox_near_contact}` は空の .gitkeep のみ）。
- 器具/把持関係の raw coco JSON 日付 = **2025-02**（2026-07-10 SAM バンドルより前）。

**最重要（1 行）**
- **タスク2 の判定：形式上は (a)（RLE 真マスクが実在）。ただし master には矩形しか無く README 記載どおり「派生時に真マスクが挿入」されたもので、生成方法の来歴書が無い。**
- **タスク3 の判定：不合格寄りの「判定不能（要追加証拠）」。04_handtool マスクは master 原 bbox にほぼ完全内包（内包率 median 1.0）で IoU median 0.926 ≈ SAM 参照 0.927。bbox 由来生成の署名と強く整合する。**

→ この 2 点により、**「完全版 GT 組み立て」は無条件では進められない**（後述 7）。

---

## 1. raw bundle 全容（タスク1）

| サブセット | 主な中身 | seg 形式 |
|---|---|---|
| 00_master_annotations | 15 json（元データ・38クラス） | polygon **全4頂点＝矩形（bbox 相当）** |
| 01_frames | 27,535 jpg（1920×1080） | — |
| 02_hand | 54,371 PNG（手バイナリ）＋29 json | 手はバイナリ PNG／json |
| 03_tool | 35 json（14/15/31 クラス） | **RLE（真マスク）** |
| 04_handtool | 18,397 PNG（マルチクラス）＋32 json | **RLE（真マスク）** |

（表を使わない形の要約：master は矩形のみ、03_tool と 04_handtool だけが RLE の真マスクを持ち、02_hand の手はバイナリ PNG。SAM 疑似ラベルの pseudo_labels ディレクトリは空。）

## 2. ★C1-raw：真のインスタンスマスクは実在するか → **(a)（ただし来歴要確認）**

- 03_tool_14cls・04_handtool_5cls とも segmentation は **100% RLE**（polygon 0）。
- 充填率（mask_area / mask_bbox）median = 03_tool **0.298** / 04_handtool **0.412**（矩形なら 1.0 に張り付く。自由形状マスクである）。
- 一方 master は **polygon 全4頂点（矩形）のみ**。真マスクは master に存在しない。
- README 引用（`raw_readme.md`）：「以下の 02〜04 は全てこのファイル（master）から派生」「派生時に**真のマスクが挿入されている**」。**master に無いマスクが派生に在る＝マスクは別途生成された**。生成手段は README に記載なし。

→ 形式は (a) だが、**「どこから来た真マスクか」が未文書化**。これがタスク3 の焦点。

## 3. ★C4-provenance：SAM 由来指紋 → **判定不能（bbox 由来の疑い濃厚）**

派生 RLE マスクの外接矩形 vs **master 原 bbox**（独立アノテ）の分布（04_handtool_5cls, n=1500）：
- 内包率 area(∩)/area(mask_bbox)：min 0.711 / q1 0.993 / **median 1.000** / mean 0.987
- IoU：min 0.345 / q1 0.880 / **median 0.926** / q3 0.952 / mean 0.903

参照（2026-07-10 SAM バンドル実測）：内包率 mean ≈ 0.879 / IoU median ≈ 0.927。

- **IoU median 0.926 は SAM 参照 0.927 とほぼ一致。** 内包率は 0.987 と SAM の 0.879 より**さらに高く（＝master 箱にほぼ完全内包）**、bbox からマスクを起こした場合の典型（マスクが箱の内側に収まる）と整合。
- 03_tool は IoU median 0.887・内包率 mean 0.969 とやや広いが、やはり高内包。
- **鋭い SAM ピーク（0.879/0.927）に完全一致はしない**（内包率が違う）。分布はより広く裾を持つ。同一 SAM バンドルとは断定できないが、**bbox 由来生成の署名は明確に出ている**。
- 決定的な反証（＝人手アノテで真に独立という証拠）は得られていない。**生成方法の来歴書が無い限りクリア不可。**

→ **不合格時のルール（L1/L2 実験ごと無効）に該当し得る。**手 mask を注入する L2 でも、マスクが tool bbox 由来なら間接的に tool 位置を漏らす。組み立て前に **OpenSurgery 原本のマスク生成来歴の確認が必須**。

## 4. C6：HTI ∧ phase 共存フレーム数（basename join）

- 共存フレーム = **9,106**（HTI 9,106 が全て phase 側に存在。phase 総数 17,233）。
- 9 工程別内訳：dissection 3,540 / closure 3,332 / incision 873 / hemostasis 663 / anesthesia 380 / design 137 / irrigation 117 / dressing 64。
- 注：join は basename（image_id join は test 約7割誤接続の既知バグのため不可）。

## 5. C7：クラス対応表（`C7_class_mapping.json`）

- raw `03_tool 14cls_cleaned` は Tool15 から **Mouth Gag を除いた 14 クラス**。
- **Bipolar Forceps は Forceps に統合されていない**（両者とも独立クラスとして存在）。per-class AP 比較は Tool15 基準で可能だが、Mouth Gag が raw14 に無い点に注意（15cls 版 or 31cls 版を使えば復活）。

## 6. C8：手 bbox 正本決定（3者比較）→ **推奨正本 = raw 02_hand**

要約（表を使わない）：
- raw 02_hand：手 **57,173** インスタンス／19,560 画像／**25 セグメント**（欠落は 03_3 のみ）。
- egosurgery_hand4：**46,320**／15,437 画像／22 セグメント。raw02 比の欠落 = 03_1・12_2・15_2。
- egosurgery_tool_hand（手）：hand4 と件数・動画・画像が**完全同一**（46,320／15,437／22）＝同世代。
- **03_3 は raw02 にも手アノテが無い**（frames はあるが GT 無し＝どの世代でも復活不能）。12_2 は 16 枚のみ。
- raw02 と hand4 の bbox：**完全一致 0.0%**、幾何 best-IoU median **0.523**（min 0・q3 0.88）。**両者は座標系が異なる別アノテ**（前回監査の「bbox_all vs hand4 完全一致20%・mean IoU 0.806」とは別ペアだが、世代間不整合という結論は同じ）。

→ **推奨正本 = raw 02_hand**（最完全・欠落は復活不能な 03_3 のみ）。ただし raw02 と hand4/tool_hand は座標系が食い違うため、正本を raw02 に一本化するなら **downstream（把持関係・bbox 等）を全て raw02 座標で再導出**すること。世代混在は S0 の Δ 基準点を汚染するため禁止。

## 7. init mAP と Δ 分母の照合（タスク5）

- T1b warm-start init mAP：seed42 0.7303 / 123 0.729 / 456 0.722（平均 **0.7271**）。source = `third_party/Relation-DETR/checkpoints/incoming/seed{S}/best_ap.pth`（**収束済み 15クラス検出器**、train_t1b.py L147-152）。
- S0-frozen 分母 **0.7051 ± 0.0042**：source = `experiments/baselines/s0_frozen_00{1,2,3}_..._cocohead_seed*`（**backbone 凍結 + COCO-init head を frozen-source 手順で再学習**した検出器）。
- eval recipe は両者とも公式（score_thr=0.0 / NMS 無 / top-k=300）・同一 split。**recipe 差ではない。**
- **約2.2pt差の原因＝別 checkpoint**。0.7271＝warm-start 源の収束済み full 検出器、0.7051＝S0-frozen 再学習検出器。T1b/L2 の Δ は **inj−ctrl（両者とも 0.7271 から warm-start）の paired 量**で測るのが規約で、絶対 mAP を 0.7051 と直接比較してはならない（§13 の 4 分母運用）。

## 8. 「完全版 GT 組み立て」実行可能性判定 → **条件付き可**

- **可能な部分**：手 bbox の正本一本化（raw 02_hand・57,173）、欠落動画 03_1/12_2/15_2 の復活、クラス対応（Tool15、Mouth Gag は 15/31cls 版で復活）、split 整合、phase 共存（9,106）。これらは形式変換・選別で安全に進められる。
- **条件（ブロッカー）**：
  1. **マスクの来歴確認が未了**（タスク3）。03_tool/04_handtool の RLE マスクは master 箱にほぼ完全内包・IoU≈0.93 で **bbox 由来生成の署名**が出ている。OpenSurgery 原本（Keio 2022）のマスク生成方法を文書で確認するまで、**マスクを使う組み立て（真マスク版 HTS・L2 の oracle 手 mask）は進めてはならない**。bbox 由来と判明したら L2/L1a の oracle-mask 前提は無効化。
  2. raw02 と派生の**座標系不一致**。正本を raw02 にするなら downstream 全再導出が必要。

### 判定不能だった項目（憶測で埋めない）
- マスクの最終的な真贋（人手 or 生成）：master 側に真マスクが無く、来歴書も無いため **監査だけでは断定不能**。IoU/内包の署名は bbox 由来を示唆するが、OpenSurgery 原本の配布物にマスクが含まれていた可能性を排除できない。→ **原本の来歴（配布物一覧・生成スクリプト）の入手が必要。**

---

## 更新（2026-07-29 追記・ユーザ確定情報反映）

### Task3 判定を「SAM 由来と**確定**」に更新
EgoSurgery-HTS 論文（arXiv:2503.18755）に手法が明記: **SAM に術具・手の bbox を prompt として与えマスク生成**、hand-tool 相互作用術具は「**手セグメンテーションとの IoU が最大の術具**」で決定。本監査の実測（04_handtool 内包率≈1.0・IoU median 0.926）はデータセット設計そのものを正しく捉えていた。→ 「判定不能」を撤回し **SAM 由来で確定**。

含意:
- **(1) L2 は安全・ブロッカー解除**: 手マスクは**手 bbox 由来**なので術具情報を漏らさない。L2(4ch・手 mask のみ注入)は前提健全。
- **(2) L1a は現設計で無効**: HTI(把持フラグ)は **GT 術具 bbox の決定論的関数=リーク**。→ **5ch(把持フラグ)版は実装・使用しない**。`scripts/train_hand2det.py` は 5ch を既定で `SystemExit` 拒否（`--allow-leaky-hti` は機構検証再現のみ）。4ch で進める。

### 座標系不一致の診断（`hand_coord_mismatch.json` / `scripts/diag_hand_coord_mismatch.py`）
- raw02 と hand4 は**同一ピクセル空間**（両者 1920×1080・範囲 [0,0,1920,1080]）。カテゴリは raw02 = hand4 + 1。
- per-axis 相似変換（最小二乗, fit 対 37,006 組）: scale (0.935, 0.883) / offset (62.0, 66.9)。恒等でない。
- **IoU は変換で改善せず悪化**: median 0.518 → **0.437**（跳ねない）。手数が一致するフレームは 62.3% のみ。
- **判定: 別世代の独立アノテーション**。座標規約の違いではない。**写像だけで欠落動画は復活できない** → 完全版は **raw02 を正本に全 downstream を再導出**する必要がある（hand4/tool_hand への写像流用は不可）。

### 第2注入機構の事前計画（単一機構の陰性の非同定性回避・§7.5 が4機構要したのと同理由）
- 第1機構（実装済）= C5 単一点・zero-init 残差（FiLM パリティ）。
- 第2機構（要実装・候補）: (a) **neck 全レベルへの多スケール注入**（各 FPN レベルに同一 zero-init 残差、空間 prior を多解像度で）、または (b) **decoder query 側注入**（query に手 prior を条件付け＝CA パリティ）。機構パリティは phase→det の既存機構と揃えること。

---

## 追記（2026-07-29・タスク1: 手-tool 整合性で正本確定）

同一 tool box（`egosurgery_tool_hand` tool IDs=EDA と同一入力）に対し手を入替えて接触統計を再現（`scripts/diag_hand_tool_consistency.py` / `hand_tool_consistency.json`）。
- 検証: hand4 は参照値を完全再現（overlap 0.561 / near 0.596 / mean_max_iou 0.162）＝計算が EDA 忠実。EDA 接触値の出所 = `stats_extra.json 18_hand_tool_contact`（hand4 世代）。
- **raw02 が全指標で勝利**: overlap **0.603**>0.561 / near **0.646**>0.596 / mean_max_iou **0.181**>0.162 / 能動工程接触 **0.934**>0.893 / 中心距離 median **267px**<286。→ raw02 の手箱が tool により整合（物理事前分布をより良く再現）。
- **時刻ずれ無し**: IoU peak は offset 0（0.599）、±1/±2/±5/±10 は単調低下。IoU median 0.60 は独立アノテ間の真の箱差（frame は整合）。
- **結論: 正本 = raw02（整合性・完全性の両方で勝ち）。** L2 は raw02 手 bbox を注入する。
