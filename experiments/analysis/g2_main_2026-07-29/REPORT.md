# EgoSurgery-HTS ─ tool mask 分母確定と G-2 実験 実測レポート

- 実施日: 2026-07-29
- ホスト: efros / 出力: `experiments/analysis/g2_main_2026-07-29/`
- 実行範囲: **Phase A（M1–M3）完了。Phase B（E1 学習）は未実行**（理由は §5）
- 本レポート中の数値はすべて実測値。推測値・概算は 0 件。測れなかったものは `UNKNOWN` / `SKIP` と明記。

---

## 0. 想定外の発見（最優先）

### 0.1 【重大】G-2 の指示された実装が現行パイプラインに適用できない

指示書 Step E1-2 は次の置換を指示している。

```
既存: ROI Align で bbox 内の特徴を平均
変更後: 同じ ROI 内で、mask == 1 の画素のみを平均（mask-weighted average pooling）
```

**しかし現行 T1a の region-token は ROI Align による画素プーリングではない。**
`scripts/extract_t1a_regiontoken.py` の実装（実測）:

| 項目 | 実体 |
|---|---|
| 捕捉点 | `model.transformer.decoder.class_head[-1]` の forward hook |
| 捕捉物 | `tokens (Q,256)` = DETR デコーダの **object-query 埋め込み**、`logits (Q,15)` |
| 合成 | `q* = argmax_q sigmoid(logits)[q,c]`、`region[c] = sigmoid(logits)[q*,c] · tokens[q*]` |
| 次元 | 15 クラス × 256 = **3,840-d** |
| 空間特徴マップの使用 | **なし**（ROI Align なし・画素平均なし） |

object-query 埋め込みは、特徴マップ全体への cross-attention の結果として得られる 256-d ベクトルであり、
**「ROI 内の画素」という平均対象が存在しない**。したがって指示された「pooling 段だけの差し替え」は、
差し替える pooling 段そのものが無いため実行できない。

これを実装するには region-token 抽出を ROI Align ベースに作り替える必要があるが、それは

- §0 の禁止事項「**region-token 抽出パイプラインを変更しないこと**」に抵触し、
- 表現そのものが別物になるため **T1a（+0.0497）との比較可能性が失われる**（I4 違反）

§5 の規定（推測で実装せず、観測された全パターンを列挙する）に従い、**実装は行っていない**。
選択肢は §5.2 に記載する。

### 0.2 【重大・2026-07-29 訂正済み】GPU が利用できない ← **この記述は誤りだった**

> 🔴 **訂正（同日 delta_convention タスクで判明）**: 本節の結論「GPU が使えない」は**誤り**である。
> 検証済み環境は **`.venv-relation-detr`**（Python 3.11.4 / torch 2.1.2+cu118 / **CUDA 有効**）として
> 最初から存在しており、検出パイプラインはそちらを使う実装になっていた。
> 下記で観測した `.venv` は、**本セッションの `uv run` が副次生成した別物**である。
> したがって **E1 のブロッカー 2 は存在しない**（ブロッカー 1「region-token に pooling 段が無い」は有効）。
> 詳細は `../delta_convention_2026-07-29/REPORT.md` §0.1。以下は当時の観測記録として残す。

| 項目 | 実測 |
|---|---|
| GPU | NVIDIA RTX A6000 × 2（いずれも idle、49GB） |
| ドライバ | **535.309.01**（CUDA 12.2 まで） |
| `.venv` の torch | **2.13.0+cu130**（CUDA 13.0 ビルド、driver ≥ 580 が必要） |
| `torch.cuda.is_available()` | **False** |
| `CLAUDE.md` の検証済み構成 | **torch 2.1.2+cu118** |

venv がドキュメント記載の検証済み構成から乖離しており、**GPU 推論・学習が一切実行できない**。
E1 は GPU を要するため、§0.1 が解決しても現状では実行できない。
復旧は依存関係の変更にあたるため、本タスクでは**実施していない**（要判断）。

### 0.3 §1.2 の Δ 値が、リポジトリ内の集約値と一致しない

`experiments/analysis/step_c_coupling_analysis/test_eval_det2phase.json`（s4/b2a/t1a × 3 seed）との照合:

| 対象 | §1.2 記載 | val accuracy 実測 | val macro-F1 実測 | **test accuracy 実測** |
|---|---:|---:|---:|---:|
| B2a Δ | +0.0383 | +0.0433 | +0.0855 | **−0.0081** |
| T1a Δ | +0.0497 | +0.0568 | +0.1071 | +0.0259 |
| S4 base acc | 0.8986 | 0.8928（3-seed 平均） | — | — |

- §1.2 の Δ に最も近いのは **val accuracy**（差 +0.0050 / +0.0071）だが完全一致はしない。
- **test では B2a の accuracy が負（−0.0081）**であり、§1.2 の +0.0383 と符号が逆。
  これは指示書 §E1-3 が警告する「val→test の反転」に該当する。

§0 の「既存の実験結果を再解釈しないこと」に従い、**差異の記録に留め、再解釈は行っていない**。

### 0.4 per-frame の phase 予測がディスク上に存在しない

M2 が前提とする per-frame 予測は、**リポジトリ上のどこにも存在しない**（実測）。

| 探索パターン | ヒットしたパス数 | 非空 |
|---|---:|---:|
| `experiments/phase1/s4_phase_baseline_*/predictions/` | 64 | **0** |
| `experiments/transfer/b2a_det2phase_*/predictions/` | 43 | **0** |
| `experiments/transfer/t1a_regiontoken_*/predictions/` | 5 | **0** |
| `experiments/transfer/haux_..._withtooloracle_*/predictions/` | 3 | **0** |
| `**/phase_val_preds*.json` | 0 | 0 |

原因: phase trainer は `preds = logits.argmax(0)` を評価器に渡した直後に破棄し、
`predictions/` は `ExperimentManager` が作成するのみで書き込まれない。

---

## 1. タスク別ステータス

| Task | 内容 | ステータス | 判定 |
|---|---|---|---|
| M1 | tool mask のフレーム水準被覆率 | 完了 | **PASS** |
| M2 | G-1 の検出力の事前計算 | **SKIP（指示手法）+ 部分実測** | **NOT_MEASURABLE** |
| M3 | canonical split の間引き規則 | 完了 | **規則不明 / 評価枠拡張: 拡張不可** |
| E1 | G-2 実験 | **未実行** | ゲート外のブロッカー（§5） |

合成データによる検出能力の確認（Step M1-6 等）は M1・M2・M3 の全スクリプトで実施し、**全て PASS**。

---

## 2. M1: tool mask の被覆率 — 判定 PASS

### 3 つの被覆率（IoU 閾値 0.5、完了条件で明記が要求されている値）

| split | canonical フレーム | mask あり | **cov_frame** | cov_ann | **cov_ann_maskable** | クラス食い違い率 |
|---|---:|---:|---:|---:|---:|---:|
| train | 9,657 | 9,472 | **0.9808** | 0.8589 | 0.9804 | 0.0009 |
| val | 1,515 | 1,427 | **0.9419** | 0.7591 | 0.9867 | 0.0022 |
| test | 4,265 | 4,118 | **0.9655** | 0.8829 | 0.9766 | 0.0010 |
| **計** | **15,437** | **15,017** | **0.9728** | **0.8556** | **0.9799** | **0.0010** |

- `cov_frame` = mask を 1 件以上持つ canonical フレーム / canonical フレーム（**主指標**）
- `cov_ann` = マッチした VBS box / VBS box 総数
- `cov_ann_maskable` = 同上を、mask 側に実データが無い `Mouth Gag` / `Skewer` を分子・分母双方から除いて再計算
- 参考: `cov_frame_matched`（VBS box とマッチした mask を持つフレーム基準）= **0.9399**

### 閾値感度（Step M1-3）

| IoU 閾値 | cov_frame | cov_frame_matched | cov_ann | cov_ann_maskable | 食い違い率 | 判定 |
|---:|---:|---:|---:|---:|---:|---|
| 0.3 | 0.9728 | 0.9433 | 0.8727 | 0.9969 | 0.0036 | PASS |
| **0.5** | **0.9728** | 0.9399 | 0.8556 | 0.9799 | 0.0010 | **PASS** |
| 0.7 | 0.9728 | 0.9222 | 0.7782 | 0.8917 | 0.0005 | PASS |
| 0.9 | 0.9728 | 0.6982 | 0.3738 | 0.4284 | 0.0004 | PASS |

**判定は 4 閾値すべてで PASS（安定）**。`cov_frame` は主指標の定義上マッチ閾値に依存しない。

### 未マッチの内訳（Step M1-4）

未マッチ VBS box 7,172 件（thr=0.5）の内訳:

| 区分 | 件数 | 内容 |
|---|---:|---|
| **mask 側に実データが無いクラス** | **6,302** | `Mouth Gag` 5,958 / `Skewer` 344 → **原理的に埋まらない** |
| その他のクラス | 870 | Forceps 185 / Tweezers 168 / Suction Cannula 105 / Scissors 102 / Needle Holders 79 / Gauze 50 / 他 |

「その他 870 件」は VBS box 総数 49,652 の **1.8%** であり、特定動画への偏りは見られなかった
（`m1_unmatched_by_class.csv` および JSON の `unmatched_by_segment` 参照）。

### クラス整合（Step M1-2）

マッチ 42,480 件のうちクラス食い違いは **43 件（0.0010 = 0.10%）**。
ゲート条件「5% 未満」を大きく下回るため、**mask を VBS box に貼り付ける設計は妥当**と判断できる。

### 判定

| 実測 `cov_frame` | 判定 | G-2 の設計 |
|---:|---|---|
| **0.9728**（≥ 0.95） | **PASS** | **分母は canonical 15,437。T1a（+0.0497）と直接比較可能。I1 を破らない** |

出力: `subsets/subset_toolmask_{train,val,test}.txt` = **9,472 / 1,427 / 4,118（計 15,017）**

### 実装上の注意（発見した不具合）

初回実装では `cov_ann_maskable` が **1.0001** となった。分母から `Mouth Gag`/`Skewer` を除きながら、
分子（マッチ数）には「`Mouth Gag` の box が別クラスの mask とマッチした 27 件」が残っていたため。
分子・分母を同じ母集団に揃えて修正し、**被覆率が [0,1] を外れたら停止する assert を追加**した。
閾値感度分析（0.3）を行っていなければ 0.98 という尤もらしい値のまま見逃していた。

---

## 3. M2: G-1 の検出力 — 判定 NOT_MEASURABLE

### 指示された手法は SKIP

Step M2-2 の「per-frame 予測を 9,106 枚部分集合に限定した動画単位クラスタ・ブートストラップ（B=2,000）」は、
**per-frame 予測が存在しない**ため実行できない（§0.4）。Step M2-1 の規定に従い `UNKNOWN` として SKIP。

### 実際に測定した量（代用ではなく別の量）

存在が確認できた 3-seed の集約値から、**seed 水準のペア差分**による MDE（α=0.05, n=3, t=4.3027）を算出した。
要求された量との違いは以下のとおりで、**この MDE は真の MDE の下限**である（真値はこれ以上に大きい）。

- 分母は canonical 15,437 枚であり 9,106 枚部分集合ではない
- 変動源は seed のみで、動画単位のリサンプルを含まない

| split | 対比 | 指標 | 平均差 | sd | **MDE** | H-6 Δ(0.0004) の何倍 |
|---|---|---|---:|---:|---:|---:|
| val | b2a−s4 | accuracy | +0.0433 | 0.0010 | **0.0025** | **6×** |
| val | t1a−s4 | accuracy | +0.0568 | 0.0018 | 0.0043 | 11× |
| val | t1a−b2a | accuracy | +0.0134 | 0.0028 | 0.0068 | 17× |
| test | t1a−s4 | macro-F1 | +0.1641 | 0.0053 | 0.0133 | 33× |
| test | t1a−s4 | accuracy | +0.0259 | 0.0091 | 0.0226 | 56× |
| test | b2a−s4 | accuracy | −0.0081 | 0.0139 | 0.0346 | 87× |
| test | t1a−b2a | accuracy | +0.0340 | 0.0226 | 0.0562 | 141× |

※ §1.2 の Δ が accuracy 基準か macro-F1 基準か指示書からは確定できないため、両方で算出した。

### 判定

**最小の MDE（最も有利な条件・かつ下限）でも 0.0025 で、H-6 の Δ（+0.0004）の 6 倍。**
test では 56–141 倍。

| 判定 | 内容 |
|---|---|
| **NOT_MEASURABLE** | **G-1 は「H-6 を上回るか」を判定できない。** 実行しても結論が出ないため、設計変更か撤退の検討が必要 |

補足: 同じ枠組みで B2a / T1a 規模の効果（+0.04〜+0.06）は val で検出可能（MDE 0.0025–0.0068）。
したがって「この実験系に検出力が無い」のではなく、**H-6 の +0.0004 という目標効果量が小さすぎる**。

### 再生成の道筋（未実施）

per-frame 予測の再生成に必要な材料はすべて存在する:
checkpoint（`best_tecno.pth`、B2a/T1a/H-6/S4 の 3-seed 分）、キャッシュ特徴
（`data/processed/{b2a_detsignal,t1a_regiontoken,oracle_*}`）、frame ID と GT
（`data/processed/phase_manifest/{split}.json`）、ローダ（`scripts/eval_det2phase_test.py`、
`IN_DIM: s4=2048 / b2a=2063 / t1a=5888`）。
ただし推論に GPU を要するため §0.2 のブロッカーが解決するまで実行できない。

---

## 4. M3: canonical split の間引き規則 — 規則不明 / 評価枠拡張は不可

### 未採用フレームの特定（Step M3-1）

| 項目 | 実測 | 期待 |
|---|---:|---:|
| 母集団 P | 19,560 | 19,560 |
| canonical A | 15,437 | 15,437 |
| 除外セグメント（03_1 / 12_2 / 15_2） | 463 | 463 |
| **未採用フレーム** | **3,660** | **3,660 ✓ 一致** |

### 4 仮説の検定（Step M3-2）

| 仮説 | 実測 | 判定 |
|---|---|---|
| **H-a** 時間的サブサンプリング | 採用フレームの隣接差分の最頻値は **1**（14,402 回）。等間隔の周期構造なし | **不支持** |
| **H-b** 品質フィルタ | bbox 面積 median: 未採用 **74,700** vs 採用 **102,345**（相対差 **0.270**） | **境界値**（基準 0.30 に未達） |
| **H-c** annotation 欠落 | 未採用 3,660 枚のうち **3,391 枚（92.7%）が tool ann を持つ**。hands ファイルにも 3,583 枚収録、うち 3,544 枚が hand ann あり | **不支持** |
| **H-d** セグメント端の切り落とし | 未採用が端 10% に入る率 **0.246**（一様なら 0.2） | **不支持** |

→ **規則は同定できなかった（規則不明）。** §5 に従い無理な説明はつけない。
唯一 H-b が境界値で、未採用フレームは採用フレームより bbox が 27% 小さい傾向がある。

### 工程分布（Step M3-3）

| 対象 | 枚数 | phase ラベル |
|---|---:|---|
| 未採用フレーム | 3,660 | **全件 未ラベル**（`__UNLABELED__` 3,660） |
| rare 3 工程（disinfection / dressing / irrigation） | — | **0 / 0 / 0** |

### 判定（Step M3-4）

**評価枠拡張は不可。以後この論点は閉じる。**

未採用フレームは tool ann を 92.7% 持つ（＝ H-c の「ann が無い」には該当しない）が、
**phase ラベルが 1 件も存在しない**ため工程評価に使えない。

> 指示書 M3-4 の判定表は「ann の有無」で分岐するが、実データは
> **「ann はあるが phase ラベルが無い」という表に無いパターン**だった。§5 に従い、そのまま記録する。

---

## 5. Phase B（E1）を実行しなかった理由

### 5.1 ゲート判定

| ゲート条件 | 実測 | 通過 |
|---|---|---|
| M1 が PASS または WARN | **PASS**（cov_frame 0.9728） | ✅ |
| M1 のクラス食い違い率が 5% 未満 | **0.10%** | ✅ |
| 予測の事前登録が完了しコミット済み | **完了**（commit `904c578`、学習前） | ✅ |

**ゲートは 3 つとも通過している。** それにもかかわらず E1 を実行しなかったのは、
ゲートの外側にある以下 2 つのブロッカーによる。

### 5.2 ブロッカー 1: 指示された実装が現行パイプラインに存在しない（§0.1）

現行 region-token は DETR object-query 埋め込みであり、mask で重み付けすべき「ROI 内の画素」が無い。
考えられる選択肢は以下のとおりだが、**いずれも意思決定を要するため実装していない**。

| 選択肢 | 内容 | 問題 |
|---|---|---|
| A | region-token 抽出を ROI Align + mask pooling に作り替える | §0 の「region-token 抽出パイプラインを変更しないこと」に抵触。<br>表現が別物になり T1a(+0.0497) と比較不能（I4 違反） |
| B | mask を cross-attention の重みに反映させる | 指示された設計と異なる。効果の解釈が「背景除去」ではなくなる |
| C | mask 由来の特徴を**追加チャネル**として連結する（既存 token は不変） | 凍結源を壊さないが、「pooling の置換」ではないため<br>予測 1–3（背景除去の効果）を検証したことにならない |
| D | 対象を region-token 以外（例: B2a の presence 信号）に変える | G-2 の問い（region-token の質）そのものが変わる |

### 5.3 ブロッカー 2: GPU が使えない（§0.2）← **撤回。実際には使える**

> 🔴 **訂正**: `.venv-relation-detr` で CUDA が使えることを実測で確認済み（§0.2 の訂正参照）。
> **このブロッカーは存在しない。** E1 を止めているのはブロッカー 1 のみである。
> 以下は当時の（誤った）記述。

`torch.cuda.is_available() == False`（torch 2.13.0+cu130 vs driver 535）。
E1 は region-token の再抽出（15,437 フレームの検出器推論）と TeCNO の 3-seed × 4 系統の学習を要するため、
GPU 無しでは実行できない。venv の復旧は依存関係の変更にあたるため未実施。

### 5.4 事前登録の状態

指示書 §E1-1 の要件「学習より前のコミットに事前登録が存在すること」は**満たしている**
（commit `904c578`、この時点で学習は 1 本も実行していない）。
ブロッカーが解決した時点で、予測を書き換えることなく E1 に進める。

---

## 6. 不変量への影響

| 不変量 | 再評価 | 根拠 |
|---|---|---|
| **I1** 評価フレーム集合の一致 | **G-2 では成立見込み** | tool mask の cov_frame 0.9728。分母を canonical 15,437 に保てる（M1 PASS）。<br>※ G-1 は 9,106 枚（59.0%）のままで不成立 |
| **I2** split 定義 | **成立** | canonical split を一切変更していない。未採用フレームの追加も行っていない（M3 で不可と判定） |
| **I3** クラス体系 | **成立** | VBS 15 クラスで固定。mask 貼り付け時のクラス食い違いは 0.10% |
| **I4** 凍結源・抽出パイプライン | **成立（変更なし）** | §0.1 のとおり、変更が必要になる実装は**行わなかった**。<br>選択肢 A を採る場合は I4 を破る点に注意 |
| **I5** 統計手続き | **未評価（SKIP）** | E1 未実行のため。M2 で n=3 seed の MDE を実測（§3） |

---

## 7. 成果物一覧

| パス | 内容 |
|---|---|
| `json/m1_tool_mask_coverage.json` | M1 の 3 被覆率・閾値感度・未マッチ内訳・判定 |
| `csv/m1_coverage_by_split.csv` | 閾値 × split の被覆率 |
| `csv/m1_coverage_by_video.csv` | 動画別 cov_frame |
| `csv/m1_unmatched_by_class.csv` | クラス別 未マッチ / マッチ / mask データ有無 |
| `subsets/subset_toolmask_{train,val,test}.txt` | mask を持つ canonical フレーム（9,472 / 1,427 / 4,118） |
| `json/m2_power.json` | M2 の探索記録・MDE・判定・再生成の道筋 |
| `csv/m2_power_by_phase.csv` | 対比 × 指標 × per-phase の MDE |
| `json/m3_thinning.json` | M3 の 4 仮説検定・工程分布・判定 |
| `csv/m3_unused_frames_by_phase.csv` | 未採用 / 採用 の工程別枚数 |
| `csv/m3_segment_detail.csv` | セグメント別の採用・未採用フレーム範囲 |
| `preregistration/g2_prediction.md` | **G-2 事前登録（学習前コミット `904c578`）** |

### 使用スクリプト（すべて `--self-test` 付き）

```bash
export OUT=experiments/analysis/g2_main_2026-07-29
uv run --with 'numpy<2' --with pycocotools python3 scripts/analysis/g2_denominator.py --self-test
uv run --with 'numpy<2' --with pycocotools python3 scripts/analysis/g2_denominator.py --out $OUT
python3 scripts/analysis/g1_power_analysis.py  --self-test && python3 scripts/analysis/g1_power_analysis.py  --out $OUT
python3 scripts/analysis/split_thinning_rule.py --self-test && python3 scripts/analysis/split_thinning_rule.py --out $OUT
```

環境注記: `.venv` は CUDA が使えない状態（§0.2）のため、Phase A は CPU のみで実行した。
pycocotools を要する M1 は `uv` の一時オーバーレイ（`numpy<2` 固定）で実行している。

### 元データへの変更

**なし。** `data/raw/OpenSurgery_Dataset/05_egosurgery_hts/` は読み取りのみ。
split の再定義・術具クラス体系の変更・凍結源の変更は、いずれも行っていない。
