# transfer_legacy の σ は出せるか — 調査報告

| | |
|---|---|
| 実施 | ilya（hostname `aolab` / `SERVERNAME=ilya`）, 2026-08-04 |
| ブランチ | `exp/ilya-wip-20260804`（phase0 = `29c7550`） |
| 種別 | **調査のみ。実装なし** |
| 一次データ | `transfer/` / `experiments/` とも読み取りのみ・変更 0 件 |
| `make runindex` | **未実行**（`runindex/` の未コミット変更 0 件） |

---

## 0. 結論（先に）

### 🔴 前提が 1 つ誤っていた。**σ は既に出ている。**

調査の出発点は「`eval_recipe_id` が null のため σ が出せず §10.1 の判定ができない」
というものだったが、**σ を止めていたのは `eval_recipe_id` ではない**。

```
transfer_legacy/oracle_phase/oracle_phase@None
  n_runs=3  n_seeds=3  seeds=42,123,456

  injection_effect  mean=+0.004032  pstd=0.000778  sstd=0.000953  n=3
  delta_detection   mean=+0.004127  pstd=0.000727  sstd=0.000890  n=3
  delta_control     mean=+0.000095  pstd=0.000134  sstd=0.000165  n=3
```

`eval_recipe_id` が null でも `experiment_id` は成立し、**3 seed は 1 実験に束ねられ、
seed 間の σ は `{metric}_pstd` として既に計算済み**である。

### §10.1 の材料は揃っている

| 群 | 純効果 mean | pstd (σ) | \|mean\|/σ | 全 seed 同符号 |
|---|---:|---:|---:|:--:|
| **`oracle_phase`** | **+0.004032** | 0.000778 | **5.18** | ✅ (+0.00513 / +0.00352 / +0.00343) |
| `t1b_filmonly` | +0.001852 | 0.001203 | 1.54 | ✅ (+0.0031 / +0.0022 / +0.0003) |
| `hc` | +0.000402 | 0.000360 | 1.12 | ⚠️ (+0.00087 / +0.00033 / **0.00000**) |

> ⚠️ この `|mean|/σ` は**本調査で実測値から計算した比**であって、harvester が
> `verdict_10_1` として出力したものではない。判定を正式化するには §6 の変更が要る。

---

## 1. `result.json` のキー組み合わせ — **8 種類**

| # | ファイル数 | 代表 | 特徴 |
|---:|---:|---|---|
| 1 | 24 | `t1b_camt_all_*/control_result.json` | `final_*` / `per_epoch_eval` を持つ最も豊富な型 |
| 2 | 20 | `hc_*/control_result.json` | 基本型（`inject` / `zero_ctx` あり） |
| 3 | 3 | `t1b_filmonly_*/injected_result.json` | `arm` / `recovered_*` あり |
| 4 | 2 | `t1b_filmonly_seed42/control_result.json` | 種類 3 + **`control_of`** |
| 5 | 2 | `t1b_seed42_bengio/injection_t1b_result.json` | `inject` / `zero_ctx` なし |
| 6 | 2 | `t1c_bidir_pilot/bidir_result.json` | 検出 + 工程の双方向型 |
| 7 | 2 | `t1c_bidir_v2_pilot/bidir_s4_result.json` | 種類 6 + `phase2det_source` |
| 8 | 1 | `t1b_filmonly_seed123/control_result.json` | 種類 4 + `per_class_note` |

🔴 **種類 3 / 4 / 8（計 6 ファイル）には `arm` と `control_of` が既に入っている。**
対照宣言の材料は一部の run に存在する。

### 全 8 種に共通するキー

```
best_epoch, epochs, init_mAP, lr, mAP, seed, trainable
```
（種類 6 / 7 は `final_det_mAP` / `init_det_mAP` という別名を使う）

---

## 2. `attributes` の分布（transfer_legacy 29 run）

段 6 で「指標として扱えなかった値」を退避したもの。

```
epochs        29件  {'6': 29}                                   ← 全 run 同一
seed          29件  {'42': 13, '123': 8, '456': 8}
trainable     29件  {'film': 23, 'all': 6}
best_epoch    27件  {'-1': 8, '0': 5, '5': 4, '1': 4, '2': 4, '3': 1}
delta_note    27件  {'Δ_detection=(T1b − S0-frozen)': 27}       ← 全 run 同一
denominator   27件  {'S0-frozen 0.7051±0.0052': 27}             ← 全 run 同一
film_lr       27件  {'0.0005': 27}                              ← 全 run 同一
lr            27件  {'0.0001': 27}                              ← 全 run 同一
zero_ctx      27件  {'False': 26, 'True': 1}
inject        23件  {'ca': 8, 'camt': 6, 'clsbias': 6, 'hc': 3}
arm            3件  {'injection': 3}
recovered_at   3件  {'2026-08-02': 3}
recovered_from 3件  {'/tmp/t1b_film_seed{42,123,456}/t1b_result.json'}
recovery_note  3件  （原本 JSON。ログからの復元ではない旨）
bidir_inject   2件  {'True': 2}
lambda_phase   2件  {'1.0': 2}
final_det_mAP  2件 / final_phase_acc 2件 / init_det_mAP 2件 / init_phase_acc 2件
phase2det_source 1件  {'s4': 1}
```

**`epochs` / `lr` / `film_lr` / `denominator` / `delta_note` は全 run で同一**のため、
これらから ID を合成しても全 run が 1 つに潰れ、群の区別ができない。
群を区別できるのは `inject`（4 値）と `trainable`（2 値）のみ。

---

## 3. 既存 `eval_recipe_id` の生成ロジックと実測値

```python
# tools/harvest_runindex.py
RECIPE_ID_KEYS = (
    "test_cfg",
    "split_train_images", "split_val_images", "split_test_images",
    "split_train_annotations", "split_val_annotations", "split_test_annotations",
    "effective_batch_size", "gpu_count", "lr_scaling",
)

def eval_recipe_id(recipe):
    """同一評価条件の run を束ねる安定ハッシュ。server_name は条件に含めない。"""
    if not isinstance(recipe, dict):
        return None
    subset = {k: recipe[k] for k in RECIPE_ID_KEYS if k in recipe}
    if not subset:
        return None
    return _stable_hash(_denan(subset))
```

実測（`index.csv` 749 run）:

```
eval_recipe_id の種類: 27（+ null）
  4ac382e09c21  265
  (null)        199
  78e50862a7b3   98
  e98ffddee042   64
  25494806e106   21
  1cf2eece1cd3   18
  a63aecae1158   10
  …
```

### 🔴 `eval_recipe_id` が null なのは transfer_legacy だけではない

```
eval_recipe_id が null: 199 run
  selection_noise_2026-07-29  72
  g2_followup_2026-07-29      30
  transfer_legacy             29     ← 今回追加分
  hand2det_dev                21
  transfer                    17
  g2_main_2026-07-29_lecun    12
  _smoke_prior / baselines / phase0  各 6
```

**既存 720 run のうち 170 run が同じ状態を許容している。** transfer_legacy 固有の欠陥ではない。

---

## 4. 合成可能性の判定

### 合成できるか — **技術的には可能。ただし意味がない**

`RECIPE_ID_KEYS` の 10 キーは **`result.json` に 1 つも存在しない**。
`epochs` / `lr` / `film_lr` / `trainable` / `inject` から別種のハッシュを作ることはできるが:

| 論点 | 判定 |
|---|---|
| 既存 720 run の `eval_recipe_id` と衝突するか | **ハッシュ空間の衝突はほぼ起きない**。だが**意味の衝突**が起きる。同じ列に「評価条件のハッシュ」と「学習条件のハッシュ」が混ざり、比較不能になる |
| 別の名前空間が必要か | **必要**。混ぜるなら `eval_recipe_id_source` のような出所列が要る |
| **合成すれば σ が出るか** | 🔴 **出ない。** σ をブロックしているのは `eval_recipe_id` ではない（§5） |

**結論: 合成しても目的（σ を出す）を達成しないため、行うべきでない。**

---

## 5. なぜ `verdicts.csv` に載らないのか — 真の原因

`tools/harvest_runindex.py` の `build_experiments`:

```python
ctrl = controls[0] if len(controls) == 1 else None
if ctrl and ctrl in agg_by_exp:
    ...
    # ここで初めて delta_pstd_* / delta_sstd_* / delta_same_sign_* が入る
```

**`delta_pstd_*` は「対照実験がちょうど 1 つ宣言されている」ときだけ計算される。**
transfer_legacy は `arm='unknown'` / `control_of=''` なのでこの分岐に入らない。

### 実測による裏づけ

```
eval_recipe_id が null かつ n_seeds>=2 の実験: 36 件 → delta_pstd が出ているもの   0 件
eval_recipe_id あり  かつ n_seeds>=2 の実験:159 件 → delta_pstd が出ているもの 134 件
                                                     出ていないもの            25 件
```

null 側 36 件は**すべて `arm='unknown'`**（唯一の例外 `transfer/t1b_phasefilm` は
`arm='injection'` だが対照が宣言されておらず、同じく σ なし）。

`g2_*` 30 実験・`hand2det_dev` 6 実験・`selection_noise` なども同じ状態で、
**既存 720 run 側にも同じ構造の実験が 34 件ある。**

### 2 種類の σ は別物

| 列 | 意味 | 前提 |
|---|---|---|
| `delta_pstd_{metric}` | **実験間** paired Δ の σ | 対照実験の宣言が必要 |
| `{metric}_pstd` | **seed 間**の σ（同一実験内） | `n_seeds >= 2` のみ |

`injection_effect` は `result.json` 内で既に `Δ_inj − Δ_ctrl` が引かれた値なので、
**`injection_effect_pstd` がそのまま「注入純効果の seed 間ばらつき」になる。**
§10.1 が要求するのはこちら。

---

## 6. 代替案の検討 — **借用も推定も不要**

σ は既に存在する。必要なのは「それを §10.1 の判定に載せる」ことだけ。

| 案 | 内容 | 影響 |
|---|---|---|
| **(A) 対照を別 run として登録** | `control_result.json` を独立 run にし `arm='control'` / `control_of` を付けて既存の paired 経路へ載せる | transfer_legacy が 29 → 最大 53 run。既存の Δ 定義と完全に整合 |
| **(B) `injection_effect` を主指標として判定** | run 内で完結した純効果の seed 間 σ で §10.1 を判定。`sigma_source` 列で出所を明示 | run 数は不変。**Δ の定義が既存 720 run と異なる**ことの明記が必要 |

### 推奨: **(B)**

1. `injection_effect = Δ_inj − Δ_ctrl` は `result.json` 内で**既に対照が引かれた値**であり、
   paired Δ と数学的に同じもの。(A) で再構成しても同じ数字になる
2. (A) は 24 個の `control_result.json` を run として登録するため、
   `index.csv` の run 数の意味（= 実行された学習）が変わる。
   **対照は同じ実験の別 arm であって別 run ではない**
3. (B) なら `oracle_phase` は **5.18σ / 全 seed 同符号**で即座に §10.1 を満たす

### (B) の注意点

🔴 **σ の出所が既存 720 run と異なる。** `verdicts.csv` に出所列
（例: `sigma_source = 'paired_delta' | 'within_run_seed_spread'`）を足して区別しないと、
**B-18（σ 規約の 2 系統併存）と同じ問題を増やす**ことになる。

### 検討したが不要と判断した案

| 案 | 判定 |
|---|---|
| 既存 720 run の同種実験（`b2a_*` の oracle 注入等）から σ を借用 | **不要**。自前の σ が n=3 で出ている。借用は推定であり、実測がある以上採るべきでない |
| `control_result.json` の複数 run から within-condition 分散を推定 | **不要**。同上。加えて `delta_control_pstd` として既に計算されている（`oracle_phase`: 0.000134） |

---

## 7. 副次的に見つけたこと

### `ledger_key` の衝突リスク（現時点では未発生）

直下 `transfer/hc_seed42` と `experiments/transfer/hc_seed42` はどちらも
`transfer__hc_seed42` という `ledger_key` になる。

```
index.csv の ledger_key 重複: 0 件（実測）
```

現在は run 名が重ならないため衝突していないが、将来 `experiments/transfer/` に
同名 run が作られると `runindex/runs/*.json` が**上書きされる**。
`transfer_legacy__` 接頭辞にするなど、名前空間を分けておく方が安全。

---

## 8. 実施内容

すべて読み取り専用。以下は行っていない。

- 実装・コード変更
- 一次データ（`transfer/` / `experiments/`）の変更
- `make runindex` の実行
- GPU への接触

判断に迷って独自に決めたことは**なし**。
