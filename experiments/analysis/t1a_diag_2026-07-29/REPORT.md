# T1a 差分の機構診断・checkpoint 同一性・oracle-tool 正本固定

- 実施日: 2026-07-29 / ホスト: efros / 出力: `experiments/analysis/t1a_diag_2026-07-29/`
- 実行範囲: **T1・T2・T3 すべて完了**。学習・再抽出は一切行っていない（既存 npz の静的比較のみ）
- 数値はすべて実測値。推測値 0 件。測れなかったものは `UNKNOWN`
- **正本は決定していない**（推奨に留める。決定はユーザが行う）

---

> 🔴 **2026-07-29 追記・本レポートの結論は後続タスクで解決済み**
> 本レポートの T1（UNEXPLAINED）と T2（PROVENANCE_UNVERIFIABLE）の未解明は、
> 同日の `repro_variance_2026-07-29` タスクで**原因が特定され解消した**。
> 原因は checkpoint 差でも argmax 不安定性でもなく、**MSDeformAttn の CUDA 拡張がロードされず
> PyTorch フォールバックで抽出していた**こと（`venv` を activate せず `python` を直接呼んだため
> `ninja` が PATH に無かった）。venv を activate して再抽出したところ旧キャッシュと
> **完全 bit-exact（1,515/1,515）**で一致した。**checkpoint は同一**である。
> 詳細は `../repro_variance_2026-07-29/REPORT.md` §0.1。以下は当時の測定記録として残す。

## 0. 想定外の発見（最優先）

### 0.1 【重大】§1.2 の「相対誤差 max 46,077」は機構の証拠にならない

指示書 §1.2 は「分布はほぼ同一・一部要素の相対誤差が 4 桁」という組み合わせを
**浮動小数点誤差では説明できない根拠**として提示しているが、実測するとこの統計は誤解を招くものだった。

| 実測 | 値 |
|---|---:|
| 相対誤差 > 10,000 の要素数 | **わずか 4 個**（全 5,817,600 要素中） |
| その 4 要素の \|A\| の中央値 | **8.62e-07**（ほぼゼロ） |
| その 4 要素の \|diff\| の中央値 | 2.27e-02 |

→ 46,077 という値は**分母が極小の要素で相対誤差が発散したもの**であり、
特別な機構を示唆しない。実際、相対誤差 max を出したスロット（`09_1_0217` / Retractor）は
**FLIPPED ではなく SAME_TOKEN（cos 0.99994）**だった。

### 0.2 ただし差は浮動小数点の丸めでは説明できない（結論は維持される）

§1.2 の**結論自体は正しい**が、根拠は別のところにある。

| 実測 | 値 |
|---|---:|
| float32 の eps | 1.19e-07 |
| \|A\| > 0.1 に限った相対誤差の**中央値** | **7.15e-03（0.7%）** |
| 同 p99 | 1.26e-01 |
| 絶対差の中央値 | 3.20e-04 |
| **SAME_TOKEN スロット内**の絶対差 中央値 | **3.06e-04** |

→ 十分に大きい要素だけを見ても相対誤差の中央値は **float32 eps の約 6 万倍**。
差は丸め誤差ではなく実質的である。かつ **token が同じスロットでも同程度に差がある**ため、
差は FLIPPED に局在していない。

---

## 1. タスク別ステータス

| Task | 内容 | ステータス | 判定 |
|---|---|---|---|
| T1 | スロット別 cos 類似度診断 | 完了 | **UNEXPLAINED**（判定表に無いパターン） |
| T2 | checkpoint 同一性 | 完了 | **PROVENANCE_UNVERIFIABLE**（判定表に無い第 3 パターン） |
| T3 | oracle-tool 正本固定 | 完了 | **UNDETERMINED**（一意に定まらない） |

合成データによる検出能力の確認（T1-6）は実施し **PASS**（T3 も同等の自己検証を実施）。

---

## 2. T1: スロット別 cos 診断 — 判定 UNEXPLAINED

対象: 1,515 frames × 15 classes = **22,725 スロット**（frame_ids は完全一致・順序も同一）。

**クラス順序の確定**: `data/annotations/egosurgery_tool` の category id は **0-indexed**（0..14）で、
検出器 config も `num_classes = 15  # ids 0..14`。したがって `region[c]` は category id `c` に対応する。
（1-indexed と誤ると signature 3 術具の診断が別クラスにすり替わるため、assert で固定した。）

### 2.1 分類結果（T1-3）

| 区分 | 条件 | 件数 | 割合 |
|---|---|---:|---:|
| `SAME_TOKEN` | cos > 0.999 | **22,171** | **97.56%** |
| `NEAR` | 0.9 < cos ≤ 0.999 | 343 | 1.51% |
| **`FLIPPED`** | cos ≤ 0.9 | **211** | **0.93%** |
| 除外（ゼロスロット） | — | **0** | — |

- cos: median **0.999970** / min −0.082245
- norm_ratio: median **1.000007** / mean 1.000064 / sd 0.022527 / 範囲 [0.5066, 2.3005]
- norm_ratio が 1 の ±1% 以内: **80.95%** / 1 未満の割合: **49.58%**

### 2.2 signature 3 術具（個別報告）

| 術具 | 有効スロット | FLIPPED | 割合 | cos median |
|---|---:|---:|---:|---:|
| **Bipolar Forceps** | 1,515 | 30 | **1.98%** | 0.999971 |
| **Scalpel** | 1,515 | 24 | **1.58%** | 0.999963 |
| **Needle Holders** | 1,515 | 8 | **0.53%** | 0.999975 |

signature 3 術具はいずれも全体（0.93%）と同オーダーで、特異な偏りは見られない。
クラス別の全 15 クラスは `csv/t1_by_class.csv` を参照。

### 2.3 相対誤差との対応（T1-4）

相対誤差 上位 20 スロットのうち **FLIPPED は 6 件**（残り 14 件は SAME_TOKEN / NEAR）。

| frame | class | rel_err_max | cos | label |
|---|---|---:|---:|---|
| 09_1_0217 | Retractor | **46,076.8** | 0.999942 | **SAME_TOKEN** |
| 09_1_0985 | Electric Cautery | 31,695.0 | 0.281803 | FLIPPED |
| 09_1_0871 | Forceps | 25,409.7 | 0.392306 | FLIPPED |
| 09_1_0424 | Scissors | 10,661.4 | 0.103350 | FLIPPED |
| 09_1_0397 | Retractor | 9,277.2 | 0.999906 | SAME_TOKEN |

→ **最大の相対誤差は argmax の飛びではなく、ほぼゼロの要素で発生している**（§0.1）。
「相対誤差が大きい ＝ argmax が飛んだ」という対応は成立しない。

### 2.4 判定（T1-5）

| 条件 | 実測 | 該当 |
|---|---|---|
| `FLIPPED` ≥ 5% → ARGMAX_INSTABILITY | 0.93% | ✗ |
| `FLIPPED` < 5% かつ SAME_TOKEN 支配的 かつ **norm_ratio が 1 から系統的にずれる** → CHECKPOINT_DIFF | FLIPPED 0.93% ✓ / SAME_TOKEN 97.56% ✓ / **norm_ratio median 1.000007（系統的ずれ無し）** ✗ | ✗ |

→ **UNEXPLAINED**。§6 に従い、観測された全パターンをそのまま列挙する:

1. スロットの **97.56% は同じ token を選んでおり**、向きはほぼ完全に保たれている
2. ノルム比は **1 を中心に対称に散らばる**（median 1.000007、1 未満 49.6%）。
   重みが一律に違う場合に期待される**系統的な拡大・縮小は観測されない**
3. それでも **SAME_TOKEN スロット内の絶対差は 3.06e-04**（float32 eps の 3 桁以上上）
4. **0.93%（211 スロット）で argmax が別 query に飛んでいる**
5. 最大の相対誤差は FLIPPED ではなく near-zero 要素に由来する（§0.1）

**この 5 点は「同じ重みで同じ token を選びつつ、数値が ~1% 水準でずれ、その結果ごく一部で
argmax の順位が入れ替わった」という観測に一致するが、原因の断定は本タスクの測定範囲を超える。**

---

## 3. T2: checkpoint 同一性 — 判定 PROVENANCE_UNVERIFIABLE

### 3.1 棚卸し（T2-1）

`third_party/Relation-DETR/checkpoints/**` と `experiments/**/checkpoints/**` から **527 個の `.pth`**
を md5 / size / mtime で棚卸し（`csv/t2_ckpt_inventory.csv`）。

対象 ckpt: `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`
- md5 **`6a898a768eed39391b2afd784ebe254f`** / 195,421,066 bytes / mtime **2026-05-30T07:42:27Z**
- **同一 md5 のファイル**: `…/relation_detr_resnet50_egosurgery/train/seed42/best_ap.pth`（2 ファイル）

### 3.2 時系列（T2-2）

| 検査 | 実測 |
|---|---|
| キャッシュ npz の mtime | **2026-06-20T18:24:54Z**（train 18:21 / test 18:34） |
| Relation-DETR ckpt の mtime | **すべて 2026-05-30**（キャッシュより**前**） |
| キャッシュ作成後に更新された Relation-DETR ckpt | **0 件** |
| 抽出スクリプトのコミット a697d90 | 2026-06-20T19:32:40Z（**キャッシュ作成より後**） |

**「ckpt の mtime が 6/20 より後なら差し替わっている」という T2-2 の仮説は支持されなかった。**

> ⚠️ **ただし mtime は同一性の証拠にならない**: `docs/t1a_server_b_runsheet.md` STEP 1 が指定する
> 転送手順は **`rsync -aL`** であり、`-a` は **mtime を保存する**。
> したがって mtime は「いつこのホストに置かれたか」を示さない。
> 195MB のため git 管理外で、履歴による検証もできない。

### 3.3 抽出ホスト（T2-3）— **UNKNOWN**

| 見つかった証拠 | 内容 |
|---|---|
| `docs/t1a_server_b_runsheet.md` | 「T1a を**別サーバー(server B)**で走らせる」と明記 |
| 同 STEP 0 | server B 上で **venv を再構築**する手順（`setup_env_relation_detr.sh`） |
| 同 STEP 1 | 凍結 ckpt と画像を **lecun から `rsync -aL` で転送** |
| 同 STEP 4 | 分母に lecun 実測値を流用し「**サーバー差を §8.0 明記**」と記載 |

| 見つからなかった証拠 | 内容 |
|---|---|
| キャッシュ隣のログ | **無し**（他タグ `aligndetr_*` には `.log` があるが本タグには無い） |
| 2026-06-18〜23 の metrics.json | **0 件**（`server_name` を取得できない） |
| 抽出時の torch / CUDA / cuDNN | **記録なし** |

→ **server B が efros であったかは特定できない。** 推測でホスト名は書かない（T2-3 の指示）。
ただしプロジェクト文書は「**別サーバーで実行し、環境は各自再構築し、サーバー差は明記する**」
という運用を前提にしていた。

### 3.4 判定（T2-4）

判定表の 2 択（「md5 一致」/「md5 が違う・失われている」）の**どちらにも当てはまらない第 3 のパターン**。

**PROVENANCE_UNVERIFIABLE** — ckpt ファイル自体は存在し md5 も取得できるが、
**6/20 の抽出に使われた ckpt がこれと同一である証拠が無い**。
mtime は `rsync -a` により保存されるため判定に使えず、当時の md5 記録も存在しない。

**含意**: checkpoint 差を原因として**肯定も否定もできない**。
T1 の実測（SAME_TOKEN 97.56% / norm_ratio 中央値 1.000007）は重みの系統的な違いを示さないが、
これは checkpoint 同一性の証明ではない。

---

## 4. T3: oracle-tool の正本 — 判定 UNDETERMINED

### 4.1 全 run（T3-1）

oracle-tool 系統の val run は **8 件**（`csv/t3_oracle_runs.csv`）。

| run | seed | canonical seed | val acc | val macro-F1 |
|---|---|---|---:|---:|
| `b2a_det2phase_oracletool_001` | **789** | ✗ | 0.961716 | 0.8301 |
| `b2a_det2phase_oracletool_002` | **1000** | ✗ | 0.959736 | 0.8257 |
| `b2a_det2phase_oracletool_003` | 123 | ✓ | 0.960396 | 0.8253 |
| `b2a_det2phase_oracletool_004` | 42 | ✓ | 0.951815 | 0.8182 |
| `b2a_det2phase_oracletool_005` | 456 | ✓ | 0.957756 | 0.8256 |
| `b2a_det2phase_oracletool_006` | 42 | ✓ | 0.955776 | 0.8209 |
| `b2a_det2phase_oracletool_007` | 123 | ✓ | 0.959076 | 0.8261 |
| `b2a_det2phase_oracletool_008` | 456 | ✓ | 0.954455 | 0.8235 |

> **重要**: oracle-tool の `_001/_002/_003`（最小連番 family）の seed は **789 / 1000 / 123** であり、
> **canonical seed（42/123/456）ではない**。他系統（s4 / b2a / t1a / h6）とは連番と seed の対応が異なる。

### 4.2 2 つの平均値の出所（T3-2）

| 目標値 | 3-run 組み合わせ総数 | canonical 3 つ組 **かつ** 最小連番 | 一意に定まるか |
|---|---:|---:|---|
| 0.958196（引用 0.9583） | 2 通り | **0 通り** | **✗** |
| 0.956436（H-6 の分母） | 3 通り | **0 通り** | **✗** |

§4.1 のとおり最小連番 family が canonical seed でないため、
**どちらの目標値も「canonical seed 3 つ組かつ最小連番」では一意に定まらない**。

### 4.3 分母候補別の H-6 Δ（T3-3）

| 分母候補 | H-6 Δ | MDE（0.01094）超過 | 引用 +0.0004 と一致 |
|---|---:|---|---|
| oracle-tool 0.958196 | −0.001320 | **✗** | ✗ |
| **oracle-tool 0.956436** | **+0.000440** | **✗** | **✓** |
| S4 canonical 0.898570 | +0.058306 | **✓** | ✗ |

> 🔴 **決定的な発見**: 引用値 **+0.0004 を再現する分母（0.956436）では、H-6 の Δ は MDE を超えない**。
> つまり **H-6 の効果は統計的にゼロと区別できない**。
> MDE を超えるのは S4 を分母にした場合（+0.0583）だけだが、その値は引用値と両立しない。

### 4.4 run 選択の振れ幅（T3-4）

「canonical triple の Δ」と「全 canonical-seed run 平均の Δ」の差（**分母は S4 canonical に固定**し、
分子の run 選択だけを変えた場合）:

| 系統 | Δ（canonical triple） | Δ（全 canonical-seed run） | 差 | MDE | 超過 | MDE 比 |
|---|---:|---:|---:|---:|---|---:|
| b2a | +0.038284 | +0.041204 | −0.002920 | 0.00264 | **✓** | 1.1× |
| t1a | +0.049725 | +0.043798 | +0.005927 | 0.00291 | **✓** | **2.0×** |
| h6 | +0.058306 | +0.012688 | +0.045618 | 0.01094 | **✓** | **4.2×** |
| oracle-tool | +0.062046 | +0.057976 | +0.004070 | 0.00744 | ✗ | 0.5× |

**4 系統中 3 系統で、run 選択の違いによる Δ の変動が MDE を超える。**
（指示書の既知例「T1a は MDE の 2 倍」と一致した。）

→ **規約は「どの run を canonical とするか」を明示しなければ、結論そのものが変わりうる。**

### 4.5 規約案（T3-5・決定はしない）

**oracle-tool の正本推奨: `UNDETERMINED`**

理由: §4.2 のとおり、どちらの目標値も「canonical seed 3 つ組かつ最小連番」という
他系統と同じ規則では一意に定まらないため、**規則から自動的に導けない**。
正本を定めるには、以下いずれかのユーザ判断が必要:

| 選択肢 | 内容 | 帰結 |
|---|---|---|
| A | seed 42/123/456 を使う 3 run を明示指定（例: `_004/_003/_005` または `_006/_007/_008`） | 他系統と seed 条件が揃う。ただし引用値 0.9583 と一致しない可能性 |
| B | 引用値 0.9583 に対応する組み合わせを正本にする | 引用値は保たれるが seed が canonical でない run を含む |
| C | H-6 の分母 0.956436 を与える組み合わせを正本にする | H-6 の +0.0004 が保たれるが、その Δ は MDE 未満 |

**H-6 の分母をどうするか**:

| 選択肢 | H-6 Δ | 引用値と一致 | 書き換えが必要な記述 | 問題点 |
|---|---:|---|---:|---|
| oracle-tool 基準を維持 | +0.000440 | ✓ | **0 件** | 系統ごとに分母が異なる状態が残り、論文で Δ の定義を一意に書けない。<br>さらに **Δ が MDE 未満**で有意性を主張できない |
| S4 基準に統一 | +0.058306 | ✗ | **1 件**（H-6 の Δ） | 分母は統一されるが引用値 +0.0004 が +0.0583 に変わる |

**canonical run 指定を規約に含めるべきか**: §4.4 より **含めるべき**（3/4 系統で MDE 超過）。
含めない場合に動く数値は §4.4 の表のとおり。

**決定はユーザが行う。**

---

## 5. 完了条件

- [x] T1–T3 がステータス付きで記録され、判定が書かれている
- [x] T1 の `FLIPPED` 割合（全体 0.93% / クラス別 CSV / signature 3 術具を個別）
- [x] T2 の checkpoint md5 一覧（527 件）と 6/20 との時系列整合の判定
- [x] T3 に oracle-tool 候補ごとの H-6 Δ と MDE フラグ、run 選択の振れ幅
- [x] 合成データによる検出能力の確認（T1-6）— PASS
- [x] 数値はすべて実測値
- [x] **正本を決定していない**

---

## 6. 成果物一覧

| パス | 内容 |
|---|---|
| `json/t1_slot_diag.json` | スロット分類・クラス別・相対誤差対応・数値特徴づけ addendum |
| `csv/t1_by_class.csv` | 15 クラス別の SAME_TOKEN / NEAR / FLIPPED と cos・norm_ratio |
| `csv/t1_slots.csv` | FLIPPED 全 211 スロット + 相対誤差上位 |
| `json/t2_ckpt_provenance.json` | ckpt 同一性・時系列・抽出ホスト・判定 |
| `csv/t2_ckpt_inventory.csv` | 527 個の `.pth` の md5 / size / mtime |
| `json/t3_oracle_canonical.json` | oracle-tool 候補・H-6 Δ・振れ幅・規約案 |
| `csv/t3_oracle_runs.csv` | oracle-tool 全 8 run |

### 使用スクリプト（すべて `--self-test` 付き）

```bash
export OUT=experiments/analysis/t1a_diag_2026-07-29
python3 scripts/analysis/diag_regiontoken_slots.py --self-test
python3 scripts/analysis/diag_regiontoken_slots.py \
  --old data/processed/t1a_regiontoken/relation_detr_seed42/val_regiontoken.npz \
  --new experiments/analysis/delta_convention_2026-07-29/reextract/val_regiontoken.npz --out $OUT
python3 scripts/analysis/fix_oracle_canonical.py --self-test
python3 scripts/analysis/fix_oracle_canonical.py --out $OUT
```

### 変更していないもの

学習・再抽出（**未実行**）／元データ・split・クラス体系・凍結源・依存関係／既存の実験結果
／既存キャッシュ。誤生成された `.venv` は使用していない（本タスクは system `python3` のみで完結）。
