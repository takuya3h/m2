# 設定に書いてある項目が実際に読まれているかを全て照合する — 報告

**task_id:** `T-2026-08-15-config-key-effectiveness-audit`  **kind:** `analysis`
**host:** `lecun`  **branch:** `feat/config-key-effectiveness-audit`
**読んだ実装の識別子:** `cf880db`（`origin/phase0` の先頭。並行契約が `src/` を変更中のため記録）

---

## 0. 冒頭 — `escalate_if` に該当する

契約の `escalate_if` の一つ目「工程や検出の条件に関わる項目が読まれておらず、過去の判断の
根拠が失われると判明した場合」に**該当する**。ただし**根拠は失われていない。**

**条件に関わる項目が読まれていない**ことは実挙動で確かめた。凍結源を指す 4 項目
（`frozen_source.detector` / `checkpoint` / `seed` / `cache_dir`）と評価規約を指す 3 項目
（`eval_recipe.protocol_source` / `inference_protocol` / `jaccard_mode`）は、S4 の学習入口から
**一度も読まれない。** 値を変えても結果は 1 bit も動かない。

**しかし、宣言された値と実挙動が食い違う run は 3 件しか無く、その 3 件も実験条件には影響しない。**
偶然、宣言値がすべて実挙動と一致していた。**仕組みは壊れているが、被害は出ていない。**

二つ目の `escalate_if`「読まれていない項目が多数あり、設定の記述全体が条件の記録として
使えないと判明した場合」も件数の上では該当する（40 項目中 14）。**が、記述が誤っている
わけではない。** 結論は §9 に置く。

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md` の該当アンカーの原文をそのまま引く（`conventions_rev` は
`d422b08`。**Task 1 で現在値を確認し、spec の記載と一致したため置換は不要だった**）。

```
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### その他の参照

| spec の記載 | 解決結果 |
|---|---|
| `inputs.denominator.ref` | **記載なし。** 本契約は分母を使わない |
| `inputs.sigma_policy` | **記載なし。** 判定に σ を使わず、揺れの実測値 0.0 を基準にした（§4） |
| `inputs.frozen_source.ref` | **記載なし。** ただし `frozen_source.*` そのものが本契約の題材である |
| `contract.conventions_rev` | `d422b08` = `git log -1 --format=%h -- context/conventions.md` の実測値。一致 |

### 実測した識別子

| 対象 | 値 |
|---|---|
| 読んだ実装（HEAD） | `cf880db` |
| `context/conventions.md` | `d422b08` |
| `runindex/` の最終更新 | `3e15d09` @ `2026-08-15T14:03:36+00:00` |
| `index.csv` の行数 | 851 |
| 常駐処理の抑止対応 | `grep -c sync-pause ~/bin/m2-sync.sh` = **2**（稼働中の版は対応済み） |

---

## 2. 対象範囲 — 何を対象にし、何を外したか

### 設定の側

`configs/` の `*.yaml` は **75 件**。うち **54 件は空の scaffold** で、実体があるのは **21 件**。
`configs/stage/` は 20 件中 **12 件が非空**。

契約は「学習の入口が読む設定に絞ってよい」としている。**実測に基づいて次のように絞った。**

| 対象 | 理由 |
|---|---|
| **対象にした** | 実際の 66 run が使った 8 つの設定（`tasks/T-2026-08-15-grasp-injection-effect/audit/run_{ctrl,inj}.yaml` と `tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_*.yaml` 6 件） |
| **参考として集めた** | `configs/stage/*.yaml` 12 件 + `configs/default.yaml`（Hydra 合成後の葉キーの和は **197**） |
| **外した** | 空の scaffold 54 件（項目が無い）、`configs/notion.yaml`（ID レジストリであり実験条件ではない） |
| **外した** | S0〜S3 の入口（`egosurgery.train` → `MMDetTrainer` / `StageATrainer` / `PhaseTrainer`）の挙動確認。**計算装置を使わずに走らせられないため**（禁止 10） |

**`configs/stage/*.yaml` そのものは、実際の run では使われていなかった。**
66 run の `command.sh` を読むと、すべて `tasks/*/audit/` 配下の写しを `--config` に渡している。
契約は `configs/` を入口として書いていたが、**実装（`command.sh` の実測）に従った。**

### 平坦化の表し方

葉（スカラー・`null`・空コンテナ）までのドット区切り経路とした。リストは展開せず葉として扱う。
中間の節点は葉に数えない。

### 実装の側

`src/egosurgery/**` と `scripts/**` の `.py` **242 ファイル**を対象とした。

---

## 3. 四つの区分の件数

判定は **(設定ファイル, 入口) の組ごと**に決まる。同じ鍵でも入口が違えば結果が変わるためである。
代表として `inj` 腕の設定（葉キー 40）を両方の入口で示す。

| 区分 | 元の入口 | variants 入口 |
|---|---|---|
| **設定にあり実装が読む** | **25** | **26** |
| ├ うち 摂動で指標が動いた | 8 | 9 |
| ├ うち 摂動しても指標は不変（フォルダ名等を決める） | 2 | 2 |
| └ うち 指標への影響は**未測定** | 15 | 15 |
| **設定にあり実装が読まない**（実挙動で確認） | **14** | **13** |
| 設定にあり実装が読まない（**摂動未実施**） | 1 | 1 |
| **実装が読み設定に無い** | **3** | **4** |
| **判定できない** | **0** | **0** |

- 「実装が読み設定に無い」の内訳: 元の入口は `device` / `smoke_train_clips` / `smoke_val_clips`
  の 3 件で、**すべて CLI が実行時に注入する**もの（設定に無くて当然）。variants 入口はこれに
  `grasp_inference.staged` が加わる（`cfg.grasp_inference.get("staged", False)` で既定 `False`
  を取る。`inj` の設定には書かれていない）。
- 「判定できない」が 0 なのは、丸ごと渡す経路（`OmegaConf.to_container(cfg.model.temporal)` と
  `to_container(cfg.grasp_inference)`）の下にある鍵を、**すべて摂動で解決したため**である。
  静的解析では 4〜7 件が判定不能のまま残っていた。

### 両方向の集合差（実装の側の集め方）

「実装が読む項目」は**二つの異質な方法**で集め、突き合わせた。

| 方法 | 走査対象 | 検出した経路 | 一致 | 片側のみ |
|---|---|---|---|---|
| 構文木（`ast`） | 242 ファイル | 600 箇所 / 142 経路 | 126 | 16 |
| 字面（正規表現・字句でコメントと docstring を除去） | 242 ファイル | 378 箇所 / 127 経路 | 126 | 1 |

**食い違いは両方向とも実装を読んで裁定し、それぞれ別の欠陥を露呈させた。**

1. **字面の側の偽陽性（15 件 → 1 件）**: `src/egosurgery/models/build.py:12-16` や
   `src/egosurgery/train.py:3` の **docstring に書かれた `cfg.feedback.phase_to_det` などの
   説明文**を読み取りと誤認していた。字句解析でコメントと三重引用文字列を潰して解消した。
   残る 1 件は `experiment_manager.py:162` の文字列 `"config.yaml"`（`config` + `.yaml` に見える）。
2. **構文木の側の取りこぼし（初版）**: `_root_of` の走査が `self.cfg` を属性として食い潰し、
   根の判定に到達していなかった。**`self.cfg.data.get("img_size", 518)` の形の読み取りを
   すべて落としていた**（`stage_a_trainer.py:443`、`mmdet_trainer.py:353` 他）。修正後、
   検出は 426 箇所 → **600 箇所**、経路は 135 → **142** に増えた。
3. **どちらの方法でも解けない問題**: 根の同一性。`cfg` という名前が別物を指す箇所がある。
   `mmdet_trainer.py:681` の `cfg` は **mmengine の `Config`**、`draft_master_update.py:80` の
   `cfg` は **`configs/notion.yaml`**。名前の一致だけでは判定できない。
   **このため実行時の追跡を裁定者に据えた。**

---

## 4. 判定の基準 — 同じ設定で二度走らせた差

**基準を先に測った。**

| 入口 | 同一設定・同一 seed で 2 回 | 比較した指標の数 | 最大の絶対差 | 変化した指標 |
|---|---|---|---|---|
| 元の入口 | 実測 | 18 | **0.0** | **0 / 18** |
| variants 入口 | 実測 | 18 | **0.0** | **0 / 18** |

CPU・`seed` 固定（`random` / `numpy` / `torch` を `train()` 冒頭で設定）で **完全に決定的**だった。
したがって **非零の差はすべて本物**である。揺れより小さい差を根拠にした箇所は無い。

実行は `--smoke`（`ExperimentManager` と Notion 投稿を通らない既存の経路）で、
`--epochs 1 --device cpu --max-train-clips 2 --max-val-clips 2`、出力は `tasks/` 配下。
**本番規模は走らせていない。計算装置も使っていない。**

---

## 5. 読まれていない項目の一覧と、実挙動で確かめた結果

### 5.1 両方の入口で読まれない（14 件）

値を変えて短く走らせ、**18 指標すべてが 1 bit も動かなかった**もの。

| 項目 | 変えた値 | 結果 | 実挙動を決めているもの |
|---|---|---|---|
| `frozen_source.detector` | `relation_detr` → `align_detr` | 差 0.0 | `data.feature_cache` のパス |
| `frozen_source.checkpoint` | 存在しないパスへ | 差 0.0 | 学習時は読まない（特徴抽出時のみ） |
| `frozen_source.seed` | `42` → `999` | 差 0.0 | キャッシュのパス |
| `frozen_source.cache_dir` | 存在しないパスへ | 差 0.0 | `data.feature_cache` |
| `eval_recipe.protocol_source` | `PHASE_EVAL_PROTOCOL` → `BOGUS_PROTOCOL` | 差 0.0 | 定数 `PHASE_EVAL_PROTOCOL` |
| `eval_recipe.inference_protocol` | `online_causal` → `offline_full` | 差 0.0 | 同上 |
| `eval_recipe.jaccard_mode` | `strict` → `relaxed` | 差 0.0 | 同上 |
| `model.component` | `grasp_phase_injection` → `bogus_component` | 差 0.0 | 入口が `build_grasp_phase_injection` を直接呼ぶ |
| `train.batch_size` | `1` → `64` | 差 0.0 | clip 単位で固定 |
| `train.freeze_backbone` | `true` → `false` | 差 0.0 | 特徴が事前計算のため常に凍結 |
| `data.population.test` | `4265` → `1` | 差 0.0 | 学習時に test は読まない |
| `logging.wandb_project` | → `bogus_project` | 差 0.0 | 環境変数 `WANDB_PROJECT` |
| **`grasp_inference.detach_from_phase_loss`** | `true` → `false` | 差 0.0 | **実装が常に detach（ハードコード）** |
| **`grasp_inference.signal`**（元の入口のみ） | `predicted_sigmoid` → `raw_logits` | 差 0.0 | 既定値に固定 |

**`grasp_inference.detach_from_phase_loss` は本契約で新たに見つかったものである。**
実装（`src/` と `scripts/` の `.py`）に**一度も現れない**。設定ファイル 6 件が宣言しているだけである。
`grasp_inference_injection.py` の `_candidate()` は docstring に "always detached" と書き、
全分岐が `.detach()` を呼ぶ。**注入実験の中核的主張（勾配を工程損失から切り離す）を表す
条件が、設定からは制御できない。**

`model.component` も同様に、鍵アクセスの形（`.component` / `["component"]` / `get("component")`）が
**`.py` 全体で 0 件**である。

### 5.2 摂動していないもの（1 件）

| 項目 | 状態 |
|---|---|
| `logging.wandb_enabled` | 実行時追跡で **両入口とも触られない**。`tracking.enabled()` は環境変数 `WANDB_API_KEY` だけを見る。**ただし摂動は行っていない**（W&B へ実際に投稿させる必要があるため）。指標への影響は `UNKNOWN` |

なお `logging.wandb_enabled` は **S0〜S2 の入口では読まれる**（`stage_a_trainer.py:329`、
`trainer.py:131`、`mmdet_trainer.py:860`）。**読まれるかは入口に依存する。**

### 5.3 入口によって変わるもの

**`grasp_inference.signal` が本契約で最も重要な観測である。**

| 入口 | `signal` を `predicted_sigmoid` → `raw_logits` | 判定 |
|---|---|---|
| `train_grasp_phase_injection.py`（元） | **差 0.0** | **読まれない** |
| `train_grasp_phase_injection_variants.py` | **差 0.0014123916625976562** | **読まれる** |

同じ鍵、同じ摂動機構、同じ設定ファイルの写しである。**摂動が設定ファイルに書かれている
ことは直接確認した**（`audit/perturb_cfgs/original__grasp_inference_signal.yaml` に
`signal: raw_logits` が入っている）。それでも元の入口では結果が動かない。

原因は実装にある。元の入口の `build_component_cfg()`（`train_grasp_phase_injection.py:112-122`）は
モデルへ渡す dict を**明示的に組み直しており、`signal` を含めない。** 一方モデル側は
`cfg.get("signal", "predicted_sigmoid")` で既定値を拾う（`grasp_inference_injection.py:95`）。
variants 側は `build_component_cfg_variants()` が `SIGNAL_CFG_KEYS` を明示的に転送する
（前の契約で入った修正）。

---

## 6. 対照 — 読まれる項目で値を変えると変わること

**これを確かめなければ、測り方が壊れていて何を変えても変わらない場合と区別できない。**

| 項目 | 変えた値 | 元の入口の最大差 | variants 入口の最大差 |
|---|---|---|---|
| `train.lr` | `0.0005` → `0.005` | **0.550279…** | **0.550279…** |
| `train.smoothing_weight` | `0.15` → `0.9` | **0.073610…** | **0.073610…** |
| `grasp_inference.hidden_dim` | `64` → `32` | **0.308443…** | **0.308443…** |
| `seed` | `42` → `43` | **14.5** | **14.5** |

**4 項目すべてが変化した。G2 の停止条件（読まれる項目でも変わらない）には該当しない。**

さらに、丸ごと渡す経路の下にあって静的には判定できなかった 4 項目も、摂動で**すべて
「読まれる」と確定**した。

| 項目 | 変えた値 | 最大差 |
|---|---|---|
| `model.temporal.num_stages` | `2` → `1` | 2.240973… |
| `model.temporal.num_layers` | `8` → `4` | 0.325191… |
| `model.temporal.num_f_maps` | `64` → `32` | 3.999999… |
| `model.temporal.dropout` | `0.5` → `0.1` | 0.036792… |

---

## 7. 過去の記録で、記述と実挙動が食い違う run

走査は**象徴的な繋がりを辿った**（`os.walk(followlinks=True)`）。索引の経路には絞っていない。

| 走査結果 | 件数 |
|---|---|
| `config.yaml` を持つ run ディレクトリ | **677** |
| うち辞書として読めた | **656** |
| 解析に失敗（旧様式の python タグ等。`experiments/baselines/_legacy_score_thr_0/` 配下） | **18** |
| 読めたが中身が `null` | **3**（`s0_014/015/016_maskdino_bbox_nmsfree_seed*`） |
| `index.csv` の行数 | **851** |

読めなかった 21 件に、監査対象のキー（`grasp_inference` / `eval_recipe` / `frozen_source`）は
**生文字列でも 0 件**である。取りこぼしていない。

### 出現件数と食い違い件数

| 項目 | 出現した run | **食い違った run** |
|---|---|---|
| `frozen_source.detector` | 569 | **0** |
| `frozen_source.seed` | 569 | **0** |
| `frozen_source.cache_dir` | 130 | **0** |
| `frozen_source.checkpoint` | 66 | **0** |
| `eval_recipe.protocol_source` / `inference_protocol` / `jaccard_mode` | 各 66 | **各 0** |
| `model.component` | 66 | **0** |
| `train.batch_size` | 99 | **0** |
| `train.freeze_backbone` | 602 | **0** |
| `data.population.test` | 66 | **0** |
| `logging.wandb_enabled` / `wandb_project` | 各 99 | **各 0** |
| `grasp_inference.detach_from_phase_loss` | 66 | **0** |
| **`grasp_inference.signal`** | 66 | **3** |

突き合わせの相手は次のとおり。`frozen_source.cache_dir` は `data.feature_cache`（読まれる側）と、
`eval_recipe.*` と `detach_from_phase_loss` は実装が固定している値と、`signal` は入口ごとの
実効値と比較した。**突き合わせる相手が無い項目（`frozen_source.detector` など、実挙動を
決める設定自体が存在しないもの）は食い違いに数えていない。**

### 食い違った 3 件

| run | 入口 | 宣言 | 実効 |
|---|---|---|---|
| `experiments/phase1/s4_grasp_injection_001_frozen_tecno_grasp_inference_ctrl_seed42` | 元 | `zeros` | `predicted_sigmoid` |
| `experiments/phase1/s4_grasp_injection_003_frozen_tecno_grasp_inference_ctrl_seed123` | 元 | `zeros` | `predicted_sigmoid` |
| `experiments/phase1/s4_grasp_injection_005_frozen_tecno_grasp_inference_ctrl_seed456` | 元 | `zeros` | `predicted_sigmoid` |

**3 件とも `ctrl` 腕である。実験条件には影響しない。** `ctrl` 腕では
`phase_signal = torch.zeros_like(candidate)` により信号が腕の側で零に置き換わるため、
`signal` が何であっても工程頭に届くものは変わらない。**これは実挙動で確かめた。**

| 入口 | `signal` | 基準との最大差 |
|---|---|---|
| 元 / variants | `zeros` | **0** / **0** |
| 元 / variants | `predicted_sigmoid` | **0** / **0** |
| 元 / variants | `raw_logits` | **0** / **0** |

6 通りすべてが完全に同一である。**記録は文字どおりには不正確だが、条件としての実害は無い。**

---

## 8. 条件として引用された形跡

| 項目 | 散文（`docs/` `tasks/*/RESULT.md` `README.md` `paper/`）での引用 |
|---|---|
| `grasp_inference.detach_from_phase_loss` | **0 件** |
| `frozen_source.detector` | **0 件** |
| `frozen_source.seed` | **0 件** |
| `eval_recipe.jaccard_mode` | **0 件** |
| `model.component` | 2 件。**いずれも `add-model-component` スキルの話であり、設定の鍵ではない**（偽陽性） |
| `train.freeze_backbone` | 3 件。**いずれも S0〜S2 の Hydra コマンド列**（`train.freeze_backbone=true data.limit=16 …`）。そこでは `stage_a_trainer.py:344` が実際に読む。**正当な引用である** |

**読まれていない項目を条件として引用した誤りは、散文には見つからなかった。**

---

## 9. 索引の列に取り込まれているか — ここが最も重い

**取り込まれている。波及は文書に留まらない。**

| 索引の列 | 導出元 | 読まれるか |
|---|---|---|
| `frozen_source_tag`（`index.csv` 第 23 列） | `frozen_source.cache_dir`（無ければ `gap_cache` / `tool_signal_cache`）— `tools/harvest_runindex.py:788-791` | **読まれない** |
| `eval_recipe_id`（第 28 列） | 証跡 `eval_recipe.json`。その中身は定数 `PHASE_EVAL_PROTOCOL` + `model.temporal.*` から作られる（`grasp_phase_recipe.py:18-38`） | 元は**読まれる**。`cfg.eval_recipe.*` は**通っていない** |

`frozen_source_tag` は**実験の束ね方と分母の決定に使われている**
（`harvest_runindex.py:1362-1363` が実験 ID に `~{frozen_source_tag}` を付け、
`1505-1507` が分母の候補をこのタグで絞る）。**索引を条件の照合に使ったすべての判断が、
実装から読まれない設定項目に依存している。**

`index.csv` 851 行のうち `frozen_source_tag` が非 null なのは **569 行**である。

**先例がある。** `harvest_runindex.py:792-795` に次の注記が既にある。

> `★ frozen_source.seed は信用できない。scripts/train_s4_tecno.py が 42 をハードコードしており、
> cache_dir と矛盾する run が実在する。実態はキャッシュのパスから取り、こちらは矛盾検出の
> ためだけに保持する。`

**同種の欠陥が過去に一度発見され、`seed` については対処されていた。**
`cache_dir` と `detector` については対処されていない。本契約はその穴を測ったことになる。

### 索引の網羅性

| 比較 | 件数 |
|---|---|
| `index.csv` の一意な `path` | 851 |
| ディスク上の run ディレクトリ（リンクを辿る） | 812 |
| ディスクのみ | 24 — **すべて `wandb/latest-run/files` 等の W&B 生成物**。run ではない |
| 索引のみ | 63 — `_aborted_*` / `_failed_*` 配下で `config.yaml` も `metrics.json` も持たない |

**索引が指さない場所に隠れた run は見つからなかった。**

---

## 10. 結論 — 設定の記述を条件の記録として、どこまで信じてよいか

### **一部信じられない。**

件数を根拠に述べる。

| 判断 | 根拠 |
|---|---|
| **記述された値そのものは、現時点では信じてよい** | 監査した 15 項目・出現のべ 1,900 件超のうち、**実挙動と食い違うのは 3 件（0.16%）** であり、その 3 件も実験条件には影響しない |
| **「設定にこう書いてあるから条件はこうだった」という読み方は成り立たない** | 40 項目中 **14 項目（35%）** は値を変えても挙動が 1 bit も動かない。記述と挙動の一致は**実装が保証していない。偶然である** |
| **とくに凍結源と評価規約は信じてはならない** | Δ 基準点の汚染防止に直結する 7 項目（`frozen_source.*` 4 件、`eval_recipe.*` 3 件）が**すべて読まれない** |
| **索引の `frozen_source_tag` を条件の照合に使う判断は、根拠が一段弱い** | 導出元が読まれない項目である。569 行が該当。現時点で食い違いは 0 だが、**保証する仕組みが無い** |
| **入口を書かずに「設定はこうだった」と述べてはならない** | `grasp_inference.signal` は元の入口で読まれず variants 入口で読まれる。`logging.wandb_enabled` と `train.freeze_backbone` は S0〜S2 で読まれ S4 で読まれない。**読まれるかは (鍵, 入口) の組で決まる** |

言い換えると、**過去の記録は「宣言」であって「実効条件」ではない。** 今回はその二つが
たまたま一致していた。一致を保証する仕組みは無く、**次に誰かが値を変えたとき、記録だけが
変わって挙動が変わらない。**

---

## 11. 起票者の推測のうち、実測で裏づけられたもの・否定されたもの

### 裏づけられたもの

| 起票者の記述 | 実測 |
|---|---|
| 「同じことが他の項目で起きていないかは、誰も調べていない」 | **裏づけ。** `detach_from_phase_loss` と `model.component` を新たに検出した |
| 「3 が最も重い（引用されているものが読まれていないなら、その引用は誤り）」 | **裏づけ。** ただし散文の引用は 0 件で、重かったのは**索引の列**だった（§9） |
| 「読まれていることを、名前の一致だけで判定しない」 | **裏づけ。** 名前の一致で判定すると `cfg` の根の同一性で誤る（mmengine の `Config`、`notion.yaml`） |
| 「検査が空振りでないことを対照で確かめる」 | **裏づけ。** 対照が無ければ、揺れ 0.0 と「測り方が壊れて全部 0」を区別できなかった |
| 「実行環境の対話シェルは bash ではない」 | **裏づけ。** `grep --include=*.py` を引用せずに実行して zsh のグロブに食われ、一致 0 になった |

### 否定されたもの / 実装と食い違ったもの

| 起票者の記述 | 実測 |
|---|---|
| 「`configs/`」を探索の入口として指定 | **実際の 66 run は `configs/stage/*.yaml` を使っていない。** すべて `tasks/*/audit/` 配下の写しである。実装（`command.sh`）に従った |
| 「過去の run は 851 件ある。その記録が条件を正しく表しているかを確かめる」 | **851 は索引の行数であり、`config.yaml` を持つ run は 677 件。** 監査対象のキーが現れるのは最大 602 件（`train.freeze_backbone`） |
| 「Phase B: 非決定の大きさは並行する契約で測られている。同じ設定で二度走らせた差を先に測り、それを判定の基準にすること」 | 実測した結果 **揺れは 0.0（完全決定的）** だった。並行契約の測定を待つ必要は無かった |

### 起票者が読み落としていた構造

**「読まれるか」は鍵の属性ではなく (鍵, 入口) の組の属性である。** 契約は「設定に現れるのに
実装から読まれていない項目はどれか」と一意に決まる問いとして書いているが、実装はそうなって
いない。同じ `grasp_inference.signal` が、入口を替えるだけで読まれたり読まれなかったりする。

---

## 12. 判断が要る事項

**本契約では直していない**（禁止 11）。`tasks/inbox.d/` に起票した。優先度つきで §13 に再掲する。

---

## 13. 受け皿へ回したもの（優先度つき）

| 優先度 | 内容 |
|---|---|
| **最高** | `frozen_source.cache_dir` が読まれないまま索引の `frozen_source_tag`（569 行）を作り、実験の束ね方と分母を決めている。`data.feature_cache` との一致を機械で強制するか、タグの導出元を読まれる側へ移す |
| **高** | `grasp_inference.detach_from_phase_loss` が実装に一度も現れない。注入実験の中核的主張を表す条件が設定から制御できない。読むようにするか、設定から消す |
| **高** | `eval_recipe.*` 3 件が読まれず、実効値は定数 `PHASE_EVAL_PROTOCOL`。宣言と定数が食い違ったときに落ちる仕組みが無い |
| **中** | `model.component` が読まれない。入口が部品を直接 import しており、設定は注釈 |
| **中** | 設定に書いた鍵が実装から読まれないことを検出する仕組みが無い。本契約の追跡器（`audit/trace_reads.py`）を試験に組み込めば回帰として検出できる |
| **中** | `configs/stage/*.yaml` 20 件中 4 件（`s4_grasp_injection_{raw_logits,staged,standardized,oracle_upper_bound_only}.yaml`）に `# @package _global_` が無い。**現在は `OmegaConf.load` 直読みのため無害**だが、`python -m egosurgery.train stage=…` で読むと全キーが `stage.*` 配下に落ちて一切効かない |
| **低** | `train.batch_size` / `train.freeze_backbone` / `data.population.test` / `logging.wandb_*` が S4 の入口で読まれない。害は小さいが、条件として引用しないよう明示が要る |
| **低** | `experiments/baselines/_legacy_score_thr_0/` の 18 件と `s0_01{4,5,6}_maskdino_bbox_nmsfree_seed*` の 3 件は `config.yaml` が機械で読めない |

---

## 14. 逸脱

| # | 種別 | 内容 |
|---|---|---|
| 1 | judgement | 契約は探索の入口を `configs/` としていたが、実際の 66 run は `tasks/*/audit/` 配下の写しを使っていた。**実装（`command.sh` の実測）に従い、対象を実際に使われた 8 設定に変えた** |
| 2 | judgement | S0〜S3 の入口の挙動確認を行っていない。**計算装置を使わずに走らせられないため**（禁止 10）。静的解析と実行時追跡の対象には含めた |
| 3 | judgement | 摂動試験で W&B への投稿を止めるため `WANDB_API_KEY` を外して実行した。`cfg.logging.*` は当該入口が読まないため、キー読み取りの測定には影響しない |
| 4 | judgement | 非 smoke 経路の追跡で `ExperimentManager` と `log_experiment_to_notion` を実行時に差し替えた。**`experiments/` への書き込みと外部投稿を止めるため。** 学習コードは変更していない（`git status` で確認済み） |
| 5 | judgement | `logging.wandb_enabled` は摂動していない。実挙動を測るには W&B へ実際に投稿させる必要があり、外部への副作用を避けた。**指標への影響は `UNKNOWN`** |

**常駐処理による統合は発生しなかった**（`git status` の変更は `tasks/` 配下のみ）。

---

## 15. 再現手順

```
source .venv/bin/activate
A=tasks/T-2026-08-15-config-key-effectiveness-audit/audit

python $A/collect_config_keys.py     # 設定側の集合
python $A/collect_impl_reads.py      # 実装側（構文木 + 字面）
python $A/trace_reads.py --selftest  # 追跡器が空振りでないことの対照
python $A/classify.py                # 四区分（静的 + smoke 追跡）
cd $A && PYTHONPATH=$PWD python probe_nonsmoke.py original   # 非 smoke 経路
cd $A && PYTHONPATH=$PWD python probe_nonsmoke.py variants
python $A/perturb.py                 # 摂動（揺れの実測を含む）
python $A/impact.py                  # 過去の記録への波及
python $A/finalize.py                # 四区分の確定
```

生成物は `audit/` 配下（`config_keys.json` / `impl_reads.json` / `categories.json` /
`effectiveness.json` / `impact.json` / `summary.json` / `traces/` / `runs/`）。

## 16. 試験

| | 件数 |
|---|---|
| 開始前の失敗 | 5 |
| 終了後の失敗 | 5 |
| 終了後の成功 | 469 |

失敗 5 件は `tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics` と
`tests/test_research_logger.py` の 4 件である。

**開始前の値は測っていない。実行後に一度だけ測った。**
開始前を同じ値と書ける根拠は、`git --no-pager status --porcelain` が示すとおり
**追跡下のファイルに変更が 1 件も無い**ことである（追加は `tasks/` 配下の未追跡ファイルのみ）。
`src/` `tests/` の内容は `origin/phase0` の時点とバイト単位で同一であり、
開始前の試験結果は実行後と一致する。**測ったのは後だけである、と明記しておく。**
