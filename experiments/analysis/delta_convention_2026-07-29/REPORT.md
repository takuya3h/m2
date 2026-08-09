# Δ 分母規約の確定・間引き規則の確認・GPU 環境と bit-exact 検証

- 実施日: 2026-07-29 / ホスト: efros
- 出力: `experiments/analysis/delta_convention_2026-07-29/`
- 実行範囲: **D1・D2・D3 すべて完了**（学習は 1 本も実行していない）
- 本レポートの数値はすべて実測値。推測値・概算は 0 件。測れなかったものは `UNKNOWN` / `UNEXPLAINED` と明記。
- **Δ の正本は決定していない**（推奨に留める。決定はユーザが行う）

---

## 0. 想定外の発見（最優先）

### 0.1 【重大・自己申告】前回レポートの「GPU 利用不可」は誤りだった

2026-07-29 の `g2_main` レポート §0.2 で「`torch.cuda.is_available() == False` のため GPU が使えない」と
報告したが、**これは誤りである**。検証済み環境は最初から存在していた。

| venv | Python | torch | CUDA | 作成 | CLAUDE.md 準拠 |
|---|---|---|---|---|---|
| **`.venv-relation-detr`** | **3.11.4** | **2.1.2+cu118** | **✅ True** | 2026-07-02 | **✅ 一致** |
| `.venv` | 3.12.13 | 2.13.0+cu130 | ❌ False | **2026-07-29 12:43** | ❌ 不一致 |

- 検出パイプライン（`verify_p0_init_identity.sh` 等）は `.venv-relation-detr` を使う実装になっている。
- `.venv` は **本セッションで私が実行した `uv run --with ...` が副次的に生成したもの**
  （`pyvenv.cfg` に `uv = 0.11.26`、作成時刻が該当コマンドの実行時刻と一致）。
  同時に `uv.lock` も生成された。
- **git 追跡ファイルへの影響は無い**（`.venv*/` は `.gitignore` 済み、`uv.lock` は untracked、
  `pyproject.toml` は 2026-07-01 から未変更）。

**結果として §1.4 の食い違いは解消した**: 「efros に `.venv` が無い」という記述は**当時は正しく**、
「`.venv` の torch が 2.13.0+cu130」という記述は**私が作った副産物を観測したもの**だった。

> ⚠️ **要判断**: 誤生成した `.venv`（Python 3.12・CUDA 不可）が残っている。
> `CLAUDE.md` は「`.venv` を有効化してから実行」と指示しているため、
> 次回以降のセッションがこの壊れた `.venv` を掴む危険がある。削除するかはユーザ判断を仰ぐ（§5）。

### 0.2 【重大】既存 T1a 特徴は現環境で再現できない（bit-exact FAIL）← **解決済み**

> 🔴 **2026-07-29 追記・訂正**: この FAIL は**手順ミスが原因**で、後続の
> `repro_variance_2026-07-29` タスクで解決した。
> `venv` を activate せず `.venv-relation-detr/bin/python` を直接呼んだため `ninja` が PATH に無く、
> **MSDeformAttn の CUDA 拡張がロードされず PyTorch フォールバック**で抽出していた。
> `source .venv-relation-detr/bin/activate` してから再抽出したところ、旧キャッシュと
> **完全 bit-exact（1,515/1,515、max_abs_diff = 0.0）**で一致した。
> **既存 T1a 特徴は再現可能であり、作り直す必要はない。** 詳細は
> `../repro_variance_2026-07-29/REPORT.md` §0.1。以下は当時の測定記録として残す。

D3 の判定は **FAIL**。詳細は §4。

### 0.3 D3-2 の `pip install` は実行していない

§0.1 のとおり復旧が不要と判明したため、**依存関係は一切変更していない**
（`before_pip_freeze.txt` は取得済みで可逆性は担保）。

---

## 1. タスク別ステータス

| Task | 内容 | ステータス | 判定 |
|---|---|---|---|
| D1 | Δ 分母規約の確定 | 完了 | 引用値 7 件中 **6 件 EXACT** / 1 件 NEAR |
| D2 | 間引き規則（仮説 H-e） | 完了 | **H-e 確定** |
| D3-1 | 環境の完全記録 | 完了 | §1.4 の食い違いを解消（§0.1） |
| D3-2/3 | GPU 復旧 | **SKIP（不要）** | 検証済み環境が既に存在（§0.1） |
| D3-4〜7 | bit-exact 検証 | 完了 | **FAIL** |

合成データによる検出能力の確認（Step D1-8 等）は D1・D2・D3 の全スクリプトで実施し、**全て PASS**。

---

## 2. D1: Δ 分母規約 — 引用値はほぼ完全に再現できた

棚卸し規模: `experiments/**/metrics.json` から **5,171 指標行**。
系統別 run 数（accuracy）: s4 **61** / b2a 257 / t1a 132 / h6 18 / oracle-tool 8 / その他 36。

### 2.1 矛盾 A の解決 — S4 ベースラインは「2 本」ではなく「同一系統の別集計」

| 引用値 | 出所（実測で特定） | 再計算値 | 残差 |
|---:|---|---:|---:|
| **0.8986** | `s4_phase_baseline_00{1,2,3}` の **val accuracy 3-seed 平均**<br>（seed 42/456/123、`_001`〜`_003`） | **0.898570** | **+0.000030** |
| **0.8928** | `experiments/analysis/step_c_coupling_analysis/test_eval_det2phase.json`<br>の val accuracy 3-seed 平均（**別途の再評価**） | **0.892849** | — |

答えるべき問いへの回答:

1. **0.8986 を出す S4 run は存在する** → `s4_phase_baseline_001/002/003`。
   0.8928 は run ディレクトリではなく **後日の再評価 JSON** に由来し、同じ run 集合ではない。
2. 0.8986 は **3-seed 平均**（単一 seed ではない）。
3. 2 本は「異なる実験」ではなく **同じ系統の異なる集計/再評価**。

**S4 は全 61 run 存在し、val accuracy は 0.8700〜0.9188 に分布する。**
0.8986 を与える 3-run 組み合わせは **349 通り**あり、値だけでは一意に定まらない。
ただし **canonical seed 3 つ組（42/123/456）かつ最小連番の family** という条件を課すと
`001/002/003` に定まる。

### 2.2 矛盾 B の解決 — 仮説 H-base は成立する（ただし H-6 だけ分母が違う）

**Δ = （系統の canonical triple の val accuracy 3-seed 平均） − （S4 canonical triple 平均 0.898570）**

| 系統 | 使用 run | 再計算 Δ | 研究計画 Δ | 残差 | 判定 |
|---|---|---:|---:|---:|---|
| B2a | `b2a_det2phase_00{1,2,3}` | **+0.038284** | +0.0383 | **+0.000016** | **EXACT** |
| T1a | `t1a_regiontoken_00{1,2,3}` | **+0.049725** | +0.0497 | **−0.000025** | **EXACT** |

残差は丸め誤差の範囲（< 3e-5）。**§1.1 が「近いが一致しない」とした残差 0.0008 / 0.0013 は、
比較対象を 0.8928（別集計）にしていたことが原因**であり、0.898570 を分母にすると消える。

### 2.3 H-6 の分母は S4 ではなく oracle-tool（実測で判明）

| 基準 | H-6 の Δ |
|---|---:|
| S4 canonical triple (0.898570) | **+0.058306** ← 引用値 +0.0004 と一致しない |
| **oracle-tool（3-run 平均 0.956436）** | **+0.000440** → **+0.0004** ✓ |

H-6（`haux_hand_presence_oracle_withtooloracle_00{1,2,3}`、val accuracy 平均 **0.956876**）の
引用 Δ を満たす分母 0.956476 に一致する oracle-tool の 3-run 組み合わせは **3 通り**存在し、
うち 1 つが **canonical seed 3 つ組（42/123/456）**である。

> **これが本監査の最重要の発見**: **系統によって Δ の分母が異なる**。
> B2a / T1a は S4 基準、H-6 は oracle-tool 基準。
> 現状のまま論文の Table を書くと「Δ が何に対する差か」を一意に書けない。

### 2.4 正誤表（`csv/d1_errata.csv`）

| 引用値 | 引用元 | 再計算 | 最も近い規約 | 残差 | status |
|---|---|---:|---|---:|---|
| S4 base accuracy 0.8986 | 研究計画 §1.2 | 0.898570 | S4 canonical triple val acc | +0.000030 | **EXACT** |
| B2a Δ +0.0383 | 研究計画 §1.2 | +0.038284 | 同上を分母とする差分 | +0.000016 | **EXACT** |
| T1a Δ +0.0497 | 研究計画 §1.2 | +0.049725 | 同上 | −0.000025 | **EXACT** |
| H-6 Δ +0.0004 | 研究計画 §1.2 | +0.000440 | **oracle-tool 基準**の差分 | −0.000040 | **EXACT** |
| oracle-tool macro-F1 0.823 | 研究計画 §1.2 | 0.823045 | oracle-tool 3-run val macro-F1 | −0.000045 | **EXACT** |
| S0-frozen mAP 0.7051 | 研究計画 §13.0′ | 0.705140 | `s0_frozen_00{1,2,3}` val mAP | −0.000040 | **EXACT** |
| oracle-tool acc 0.9583 | 研究計画 §1.2 | 0.958196 | oracle-tool 3-run val accuracy | +0.000104 | **NEAR** |

**7 件中 6 件が EXACT（残差 < 5e-5）**。唯一 NEAR の oracle-tool accuracy も残差 0.0001 で、
かつ同じ丸め値を与える組み合わせが 42 通りあるため**一意には特定できない**（曖昧性を明記）。

### 2.5 規約別の Δ 再計算（`csv/d1_reconciliation.csv`）

MDE は α=0.05・n=3・t=4.3027 の paired 基準。

| 規約 | 分母 | B2a Δ | T1a Δ | H-6 Δ | oracle-tool Δ |
|---|---:|---:|---:|---:|---:|
| **K1′**（引用値の規約） | 0.898570 | +0.04121 | +0.04375 | +0.01269 | +0.05798 |
| K1（S4 全 val run 平均） | 0.903103 | +0.03668 | +0.03922 | +0.00816 | +0.05344 |
| K3（S4 全 test run 平均） | 0.903410 | UNKNOWN | +0.04474 | UNKNOWN | UNKNOWN |

MDE 超過フラグ: K1′ では 4 系統すべて超過。**K1 では H-6 のみ非超過**（Δ +0.00816 < MDE 0.01094）。
→ **分母の取り方によって H-6 の有意判定が反転する。**

※ この表の Δ は「系統の全 canonical-seed run の平均」であり、§2.2 の
「canonical triple のみ」とは母集団が異なるため値がずれる。両方を併記している。

### 2.6 矛盾 C の解決 — 検出側は「同一量の不一致」ではなかった

| 引用値 | 出所（実測で特定） | 再計算 | 残差 |
|---:|---|---:|---:|
| **0.7051 ± 0.0042** | `s0_frozen_00{1,2,3}_relationdetr_s0frozen_cocohead`（seed 42/123/456）<br>val mAP = 0.710008 / 0.699726 / 0.705687 | **平均 0.705140**<br>**母標準偏差 0.004215** | **+0.000040**<br>**+0.000015** |
| **0.7303** | `verify_p0_init_identity.sh` の init mAP seed42 | **0.730294** | **−0.000006** |

**平均も ± も一致した。** 2.2pt の差は測定誤差ではなく、**別のモデル構成の値**であることによる:

- **S0-frozen 0.7051** = backbone 凍結 + COCO head 系（`s0frozen_cocohead`）の 3-seed 平均
- **p0 init 0.7271** = Relation-DETR checkpoint そのものを `train_t1b.py --epochs 0` で評価した init 値
  （seed42 の 0.730294 は研究計画の「Relation-DETR val mAP 0.7303」と一致）

→ **同じ量を 2 通りに測って食い違ったのではなく、最初から別の量である。**
ただし研究計画上どちらを「Δ の分母」と呼ぶかは規約の問題であり、**決定はユーザが行う**。

### 2.7 推奨（決定はしない）

**K1′（S4 canonical triple = 0.898570 を分母、val、accuracy）を正本にすることを推奨する。**

根拠:
1. 引用値 S4 0.8986 / B2a +0.0383 / T1a +0.0497 が残差 5e-5 未満で再現する唯一の規約である。
2. 既存の全 Table をこの規約で読み直せば、**書き換えが必要な記述は原理的に 0 件**になる
   （H-6 と oracle-tool accuracy を除く）。

**ただし採用前に決めるべき論点**:

| 論点 | 実測に基づく材料 |
|---|---|
| **H-6 の分母をどうするか** | 現状は oracle-tool 基準（+0.0004）。S4 基準に統一すると **+0.0583** になり、<br>引用値と両立しない。**系統ごとに分母が違う現状は論文で説明できない** |
| **oracle-tool accuracy の曖昧性** | 0.9583 を与える 3-run 組み合わせは 42 通り（残差 < 2e-3）。<br>一意に特定できないため、正本 run を明示的に固定する必要がある |
| **主結果を val と test のどちらにするか** | val は **2 動画**（09,10）、test は **3 動画**（04,05,07）。<br>いずれも動画数が少なく MDE が大きい。<br>実測 MDE（K1′, accuracy）: b2a 0.00264 / t1a 0.00291 / h6 0.01094 / oracle-tool 0.00744。<br>H-6 の効果量（+0.0004）は **どの規約でも MDE を 1〜2 桁下回る** |

**決定はユーザが行う。**

---

## 3. D2: 間引き規則 — 仮説 H-e 確定

### 2 方向の包含関係（Step D2-1）

| 検査 | 期待（H-e が正しい場合） | **実測** |
|---|---:|---:|
| canonical 15,437 のうち phase 未ラベル | 0 | **0** ✅ |
| phase ラベルを持つが canonical に含まれない（母集団 P 内） | 0 | **0** ✅ |
| 未採用 3,660 のうち未ラベル | 3,660 | **3,660** ✅ |

参考: phase CSV 全体では canonical 外のラベル付きが 15,345 件あるが、
これは動画 17–22 など**母集団 P（19,560）の外側**であり、H-e の検定範囲外。

### 分割表（Step D2-2、`csv/d2_label_crosstab.csv`）

| カテゴリ | ラベル有り | ラベル無し | 計 |
|---|---:|---:|---:|
| canonical | **15,437** | **0** | 15,437 |
| canonical セグメント内・未採用 | **0** | **3,660** | 3,660 |
| 除外セグメント（03_1 / 12_2 / 15_2） | **0** | **463** | 463 |

完全に分離している。さらに `data/processed/phase_manifest` と canonical は**両方向とも差 0**で一致。

### 判定（Step D2-3）

**H-e 確定。間引き規則は「phase ラベルの有無」。**
2026-07-29 の M3 が出した「規則不明」を**本レポートで訂正する**。
（M3 は時間サブサンプリング・品質フィルタ・ann 欠落・端切り落としの 4 仮説のみを検定し、
ラベルの有無という仮説を立てていなかった。）

### 未採用フレームの検出用途としての価値（Step D2-4）

未採用 3,660 枚のうち **3,391 枚が tool ann を持ち、合計 8,798 ann**。

| クラス | ann 数 |
|---|---:|
| **Mouth Gag** | **1,009** |
| Needle Holders（signature） | 473 |
| Scalpel（signature） | 59 |
| Bipolar Forceps（signature） | 17 |
| Skewer | 0 |

**用途の注記**: これらは phase 評価には使えない（ラベルが無い）が、**検出器の学習データとしては使える量**である。
ただし使用すると S0-frozen が変わり **I4 を破る**ため、現時点では採用不可。
将来「凍結源を取り直す」判断をする場合の材料として記録する。

---

## 4. D3: bit-exact 検証 — 判定 FAIL

### 実行条件

- 使用 venv: **`.venv-relation-detr`**（torch 2.1.2+cu118、CUDA 有効）
- スクリプト: `scripts/extract_t1a_regiontoken.py` を**一切改変せず**実行（出力先のみ env で切替）
- 対象: val 1,515 枚 / checkpoint: `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`
- 既存キャッシュ: `data/processed/t1a_regiontoken/relation_detr_seed42/val_regiontoken.npz`（2026-06-20 作成）

### 比較結果（Step D3-6）

| 項目 | 実測 |
|---|---|
| キー集合 / frame_ids / shape / dtype | **すべて一致** |
| **bit-exact** | **False** |
| max_abs_diff | **1.5553** |
| mean_abs_diff | 0.002064 |
| 不一致要素の割合 | **0.9999964** |
| **bit-exact フレーム数** | **0 / 1,515** |
| 相対誤差 p50 / p90 / p99 / max | 0.0106 / 0.0768 / 1.332 / 46,077 |

### 判定（Step D3-7）

| 判定 | 内容 |
|---|---|
| **FAIL** | 丸め誤差（max_abs_diff < 1e-5 かつ相対誤差 < 1e-4）を大きく超える。<br>**G-2 に進まない。** 原因調査を別タスクとして起票すべき |

### 原因の切り分け（実測のみ・断定はしない）

| 検査 | 実測結果 |
|---|---|
| **同一環境で 2 回抽出して比較** | **完全に bit-exact**（1,515/1,515 フレーム一致、max_abs_diff = 0） |
| 分布の類似度 | **相関係数 0.999791**、absmax 4.1177 vs 4.0915、mean/std ともほぼ同一 |
| 既存の他タグ（10 種）との照合 | **すべて不一致**。最も近いのが本来の `relation_detr_seed42`（max 1.5553） |
| 抽出スクリプトの計算式 | キャッシュ作成コミット（a697d90, 6/20）から **`region[c] = scores[q,c] * tokens[q]` は不変**。<br>変更は env 上書きと `--mode` 分岐の追加のみ |
| 抽出時の環境ログ | **存在しない**（キャッシュ隣にログファイル無し） |

→ **抽出は現環境で決定的であり、差は非決定性によるものではない。**
分布はほぼ同一だが要素単位では一致しない。**根本原因は断定せず**、D3-7 の規定に従い別タスクとして起票する。

### 意思決定事項（決定しない）

既存 T1a 特徴を使い続けるか、再抽出し直すかは**意思決定事項**である。
- 使い続ける場合: 今後の再抽出結果と混ぜられない（Δ が汚染される）
- 取り直す場合: T1a（+0.0497）を含む既存 Δ の再計算が必要

---

## 5. 完了条件の確認と要判断事項

### 完了条件

- [x] D1–D3 がステータス付きで記録されている
- [x] S4 ベースラインが何本存在し、0.8986 と 0.8928 がどの run に対応するか（§2.1）
- [x] 仮説 H-base の検定結果（§2.2、B2a/T1a とも EXACT）
- [x] 4 規約（＋K1′）での Δ 再計算表と MDE 超過フラグ（§2.5）
- [x] 検出側の差の説明（§2.6、別モデル構成であることを実測で特定）
- [x] 仮説 H-e の判定（§3、確定）
- [x] bit-exact 検証の結果（§4）と torch 復旧前後の pip freeze 差分（**復旧不要のため差分なし**）
- [x] `csv/d1_errata.csv` に全引用値の `status`
- [x] `env/before_pip_freeze.txt` が存在（可逆性担保）
- [x] 合成データによる検出能力の確認（全スクリプト PASS）
- [x] 数値はすべて実測値
- [x] **Δ の正本を決定していない**

### 要判断事項

1. **Δ の正本**（§2.7）— K1′ 推奨。ただし H-6 の分母（oracle-tool 基準のまま／S4 に統一）を決める必要がある
2. **誤生成した `.venv` の扱い**（§0.1）— 削除するか。`CLAUDE.md` の指示と衝突するため放置は危険
3. **T1a 特徴の再現性**（§4）— 既存キャッシュを使い続けるか再抽出するか
4. **oracle-tool の正本 run**（§2.4）— accuracy 0.9583 は 42 通りの組み合わせが同値を与え一意でない

---

## 6. 成果物一覧

| パス | 内容 |
|---|---|
| `json/d1_delta_audit.json` | 棚卸し・S4 特定・H-base・規約・検出側・正誤表・推奨 |
| `csv/d1_all_runs.csv` | 全 5,171 指標行の棚卸し |
| `csv/d1_reconciliation.csv` | 規約別 Δ 再計算（MDE 超過フラグ付き） |
| `csv/d1_errata.csv` | 引用値 7 件の正誤表 |
| `json/d2_thinning_rule.json` | H-e 検定・分割表・未採用の検出価値 |
| `csv/d2_label_crosstab.csv` / `d2_unused_tool_class.csv` | 分割表 / 未採用の tool クラス内訳 |
| `json/d3_bitexact.json` | bit-exact 比較 + 原因切り分け証拠 + 環境訂正 |
| `env/before_pip_freeze.txt` / `after_pip_freeze.txt` | 環境記録（**pip install 未実行のため同一**） |
| `env/system.txt` / `nvidia_smi.txt` / `venv_exists.txt` / `repo_state.txt` | D3-1 スナップショット |
| `reextract/val_regiontoken.npz` / `_run2.npz` | 再抽出結果（既存キャッシュは未変更） |

### 使用スクリプト（すべて `--self-test` 付き）

```bash
export OUT=experiments/analysis/delta_convention_2026-07-29
bash scripts/env/snapshot_env.sh $OUT/env
python3 scripts/analysis/delta_convention_audit.py --self-test && python3 scripts/analysis/delta_convention_audit.py --out $OUT
python3 scripts/analysis/verify_thinning_rule.py   --self-test && python3 scripts/analysis/verify_thinning_rule.py   --out $OUT
CUDA_VISIBLE_DEVICES=0 RELDETR_FROZEN_TAG=__reextract_verify \
  .venv-relation-detr/bin/python scripts/extract_t1a_regiontoken.py --subset val
python3 scripts/analysis/verify_feature_bitexact.py --self-test
python3 scripts/analysis/verify_feature_bitexact.py \
  --old data/processed/t1a_regiontoken/relation_detr_seed42/val_regiontoken.npz \
  --new $OUT/reextract/val_regiontoken.npz --out $OUT
```

### 変更していないもの

- 元データ `data/raw/OpenSurgery_Dataset/`（読み取りのみ）
- split 定義・術具クラス体系・凍結源
- 既存の実験結果（差異は記録のみ、再解釈なし）
- **依存関係**（`pip install` は実行していない）
- 既存の region-token キャッシュ（再抽出は別ディレクトリに出力）
- **学習は 1 本も実行していない**
