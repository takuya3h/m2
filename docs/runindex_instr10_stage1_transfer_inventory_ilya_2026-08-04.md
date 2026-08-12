# 指示書 #10 段 1 — 直下 `transfer/` の棚卸し（B-12 / BL-runs-outside-experiments-dir）

| | |
|---|---|
| 実施 | ilya（hostname `aolab` / `SERVERNAME=ilya`）, 2026-08-04 |
| ブランチ | `chore/runindex-fixes-20260803` |
| 実装 | **なし**（棚卸しと設計案の提示のみ。`EXPERIMENTS` は無変更） |
| 一次データ | 読み取りのみ。変更 0 件 |

---

## 1. run 数と群ごとの内訳 — **29 run**

| 群 | 件数 | 内容 |
|---|---:|---|
| `hc_*` | 3 | `inject=hc` / `trainable=film` / 6ep |
| `oracle_phase_*` | 3 | `inject=ca` / `trainable=film` / 6ep |
| `t1b_ca_*` | 4 | cross-attention 系 |
| `t1b_ca_zeroctx_*` | 1 | zero-ctx 対照 |
| `t1b_camt_*` | 3 | efros |
| `t1b_camt_all_*` | 3 | efros |
| `t1b_clsbias_*` | 3 | efros |
| `t1b_clsbias_pe_*` | 3 | efros |
| `t1b_filmonly_*` | 3 | **T1b-FiLM 本走**（B-26 の対になる正しい arm） |
| `t1b_seed42_bengio` | 1 | bengio |
| `t1c_bidir_pilot_seed42` | 1 | 双方向パイロット |
| `t1c_bidir_v2_pilot_seed42` | 1 | 同 v2 |

- **すべて git 追跡済み**（110 ファイル / 未追跡 0）
- **runindex 登録は全群 0 件**（`hc_` / `oracle_phase` / `t1b_ca` / `t1b_camt` / `t1b_clsbias` / `t1b_filmonly` / `t1c_bidir` のいずれも `index.csv` に 0 行）
- 原因は `tools/harvest_runindex.py:40` の `EXPERIMENTS = REPO_ROOT / "experiments"`

---

## 2. 6 点証跡の有無 — **0 / 29（1 つも無い）**

```
metrics.json       0/29        per_class_ap.json  0/29
config.yaml        0/29        notes.md           0/29
command.sh         0/29        server.txt         0/29
git_commit.txt     0/29
```

代わりに存在するもの:

| ファイル | 件数 |
|---|---:|
| `control_result.json` | 24 |
| `injected_result.json` | 24 |
| `*.log` | 52 |
| `README.txt` | 4 |
| その他 `*result*.json`（`t1b_result` 2 / `zeroctx_t1b_result` 1 / `injection_t1b_result` 1 / `bidir_result` 1 / `bidir_s4_result` 1 / `phasefrozen_result` 1 / `plasticphase_result` 1） | 8 |
| **`*result*.json` 合計** | **56** |
| `best_t1b.pth` | 1 |

---

## 3. `result.json` から `metrics.json` を生成できるか

### ✅ 生成できるもの

`result.json` は 7 スキーマに分かれるが、**全 56 ファイルが共通して**次を持つ。

```
mAP / init_mAP / best_epoch / seed / epochs / lr / film_lr /
trainable / denominator / delta_note / per_class_coco_map
```

群により `inject` / `arm` / `control_of` / `zero_ctx` / `final_mAP` /
`final_per_class_coco_map` / `per_epoch_eval` / `final_det_mAP` /
`final_phase_acc` / `lambda_phase` / `bidir_inject` / `phase2det_source` も持つ。

**`experiments.csv` の Δ 算出に必要な指標は揃っている。**

### ❌ 生成できないもの

| 必要な情報 | 状況 |
|---|---|
| `eval_recipe`（`server_name` / split 件数 / `test_cfg`） | **どこにも無い**。ログにも記録なし |
| `git_commit.txt` | **どこにも無い**。全ログを 40 桁ハッシュで検索 → **0 件** |
| `server.txt` | **無い**。ディレクトリ名から部分推定のみ |

### `per_class_ap.json` は 7 run で生成不可

```
result.json 56 件中: per_class あり 35 / 空 21

per_class が全て空の run（7 件）:
  hc_seed42
  t1b_ca_zeroctx_seed42
  t1b_seed42_bengio
  t1b_camt_seed42_efros
  t1b_camt_all_seed42_efros
  t1b_camt_all_seed123_efros
  t1b_camt_all_seed456_efros
```

`best_epoch = -1`（初期値を超えなかった run）では `per_class_coco_map = {}` になる規則に見える。

### ホスト帰属 — **16/29 のみ判別可能**

| 判別 | 件数 | run |
|---|---:|---|
| `efros` | 12 | `t1b_camt_*` / `t1b_camt_all_*` / `t1b_clsbias_*` / `t1b_clsbias_pe_*` |
| `lecun` | 2 | `t1b_ca_seed123_lecun` / `t1b_ca_seed456_lecun` |
| `bengio` | 2 | `t1b_seed42_bengio` / `t1b_ca_seed42_bengio` |
| **判別不能** | **13** | `hc_*` 3 / `oracle_phase_*` 3 / `t1b_filmonly_*` 3 / `t1b_ca_seed42` / `t1b_ca_zeroctx_seed42` / `t1c_bidir_pilot_seed42` / `t1c_bidir_v2_pilot_seed42` |

`t1b_filmonly_*` の `README.txt` は自身で
「**lecun 実行を強く示唆するが、`server.txt` が無く断定はできない**」
「throughput（1.0–1.7 it/s）は lecun の範囲（1.0–2.3）に入るが Bengio（1.8–2.9）と
重なるため判別材料にならない」と記録している。

ilya 側でも新たな判別材料は見つからなかった。ログに現れる
`.venv-relation-detr` は全 240 箇所で同一でホスト差にならない。
**13 run は判別不能。**

---

## 4. `hc_*` / `oracle_phase_*` が何の実験か

`README.txt` は無いが、`result.json` から読み取れた。
どちらも **phase→det 方向の注入実験**で、`trainable=film` / 6ep /
同一の `init_mAP = 0.7303082181713886` を起点としている。

| | `inject` | ctrl（`zero_ctx=True`） | inj（`zero_ctx=False`） | Δ |
|---|---|---|---|---|
| **`hc_seed42`** | `hc` | `mAP=0.7303082181713886`<br>`best_epoch=-1` | `mAP=0.7303082181713886`<br>`best_epoch=-1` | **0.0000** |
| **`oracle_phase_seed42`** | `ca` | `mAP=0.7303082181713886`<br>`best_epoch=-1` | **`mAP=0.7354397307319163`**<br>`best_epoch=0` | **+0.0051** |

全 run に基準点も記録されている。

```
denominator = "S0-frozen 0.7051±0.0052"
delta_note  = "Δ_detection=(T1b − S0-frozen)"
```

**`oracle_phase`（オラクル工程ラベルを cross-attention で注入）だけが正の効果を示し、
`hc`（hard-code 注入）は完全に 0。**

研究計画 §Z.10.2 が「実質空白」と記録した phase→det 方向について、
**実測が既に存在する。**

> ⚠️ 数値はすべて `result.json` からの実測引用。Δ の有意性は σ が未算出のため
> **判定していない**（§10.1 の `|Δ| > 1σ` を満たすかは不明）。

---

## 5. 設計 3 案の比較

| | (a) 走査範囲を広げる | (b) `experiments/` へ昇格 | (c) 別インデックス |
|---|---|---|---|
| **作業量** | 中 | 大 | 小〜中 |
| **一次データ変更** | なし ✅ | **約 200 ファイルの新規作成** ⚠️ | なし ✅ |
| **`eval_recipe` 欠落の扱い** | `null` で登録し `evidence_level` 等で区別 | 生成時に「不明」を埋める必要 | 別スキーマなので自由 |
| **横断分析** | 1 系統のまま ✅ | 1 系統のまま ✅ | **2 系統に分裂** ❌ |
| **既存 720 run への影響** | `index.csv` が 720 → 約 749 行に増える | 同左 | なし ✅ |
| **冪等性** | 維持可 | 維持可 | 維持可 |
| **リスク** | `metrics.json` 非依存の読み取り経路を新設するため harvester の分岐が増える | 絶対規則 1 との緊張。「生成物」と明示しても一次データ領域に置く点が残る | `hc_*` / `oracle_phase_*` が Δ 分析の本流から外れ、**発見が埋もれる** |

### 推奨: **(a) 走査範囲を広げる**

1. **一次データを一切変更しない**（絶対規則 1 を完全に満たす）。
   (b) は 29 run × 7 ファイル ≒ 200 ファイルの新規作成を伴い、しかも
   `eval_recipe` / `git_commit` は**埋められない情報**なので、
   生成しても偽の完全性を与えるだけになる。
2. `hc_*` / `oracle_phase_*` は「実質空白」領域の実測であり、
   Δ 分析の本流に載せる価値が高い。(c) だと分析が 2 系統に割れ、この発見が埋もれる。
3. 実装は `EXPERIMENTS` の単一定数を「走査ルートのリスト」に変えるのが中心で、
   **既存 720 run の処理経路は変えずに済む**。

### (a) を採る場合に設計判断が要る点

1. **`metrics.json` が無い run をどう読むか** —
   `result.json` を `metrics.json` 相当として読む変換層が要る。
   `control_result.json` / `injected_result.json` の対を
   **1 run の 2 arm** として扱うか **2 run** として扱うかも決める必要がある
   （前者が自然に見える）。
2. **証跡の完全性をどう表現するか** —
   `eval_recipe` / `git_commit` / `server` が無いことを `index.csv` 上で
   明示する列（例: `evidence_level = full / partial`）が要る。
   これが無いと 720 run と同じ信頼度で混ざる。
3. **`experiment_id` の衝突** —
   直下 `transfer/t1b_ca_seed42` と `experiments/transfer/` の既存 run が
   同じ `experiment_id` にならないかの確認が必要（**未検証**）。

---

## 6. 指示書との差異

指示書 §1 の「直下 `transfer/` の 29 run」の群ごとの内訳が実測と異なった。

| 群 | 指示書（`/tmp` 原本） | 実測（直下 `transfer/`） |
|---|---:|---:|
| `hc_*` | 10 | **3** |
| `oracle_phase_*` | 9 | **3** |
| `t1b_ca_*` | 6 | **5**（`t1b_ca_*` 4 + `zeroctx` 1） |
| `t1b_film_*` | 6 | **3**（`t1b_filmonly_*`） |

指示書は `/tmp` 原本の**ファイル単位**（ctrl / inj / measure を別カウント）、
実測は**ディレクトリ単位**。総数 29 run は一致しており矛盾ではなく粒度の違い。

指示書に記載の無い群として `t1b_camt_*` 6 / `t1b_clsbias_*` 6 / `t1c_*` 2 も実在する。

---

## 7. 判断に迷って独自に決めたこと

**なし。** 段 1 は読み取りのみで、実装・変更は一切行っていない。
