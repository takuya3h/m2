# RESULT — T-2026-08-09-wiring-followup-and-integration

**実行者:** `lecun` / `exp/lecun-wip-20260703` / `d30c413`
**実行日時:** 2026-08-07T21:43Z 〜 2026-08-07T22:16Z
**判定:** **PASS** — 4 つの未処理事項と 2 つの仕組みをすべて処理した。1 点のみ未検証（§6）。

| # | 事項 | 結果 |
|---|---|---|
| 1 | 生成された成果物の記述が雛形のまま | ✅ 埋めた。数値は不変（差分 0 行） |
| 2 | 収穫器が走査するホストによって索引が変わる | ✅ **B-36** として起票 |
| 3 | 依存導入の手順がホストによって異なる | ✅ `tasks/README.md` の既知差へ記録（lecun の実測） |
| 4 | 自動同期の記録が成功時には書かれない | ✅ **B-37** として起票。`tasks/README.md` にも確認方法を記載 |
| 5 | 依存の一括導入手段が無い | ✅ `make setup` を作り直し、実行ホストで動作を実測 |
| 6 | 資格情報の失効が未設定と区別されない | ✅ 検出を追加。**通過経路は未検証**（§5-3） |

---

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | **記載なし** | 対象外（本契約に分母の宣言は無い） |
| `inputs.sigma_policy` | **記載なし** | 対象外（判定を行わない） |
| `inputs.frozen_source.ref` | **記載なし** | 対象外。preflight でも `P5` は `kind=impl` のため SKIP |
| `contract.conventions_rev` | `1201f4f` | **`d422b08` へ実測置換**（SPEC Task 7 Step 1 の手順に従う） |
| `contract.inject_verbatim` | `conventions#prohibitions`, `#naming`, `#env_p0` | 下記に原文を転記 |

### `conventions#prohibitions`（原文）

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

### `conventions#naming`（原文）

```
<a id="naming"></a>
## naming

実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。

    {step}_{seq:03d}_{description}_seed{seed}

- `step`: `s0`〜`s9`、または `a1`〜`a7`
- `seq`: 同一 category と step 内の3桁ゼロ埋め連番
- `description`: 実験内容の短い説明
- `seed`: 乱数シード。既定42

転記元: `README.md` の「命名規則」。
```

### `conventions#env_p0`（原文）

```
<a id="env_p0"></a>
## env_p0

学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
数値が変わったまま完走する。

    source .venv-relation-detr/bin/activate   # 検出系
    source .venv/bin/activate                 # 解析・工程系

拡張のロード確認をログに残すこと。
```

### `conventions_rev` の差分

`1201f4f` → `d422b08` は **+10 / −0**。差分ハンクは `frozen_source` 節（L56 に 9 行）と
変更履歴（L143 に 1 行）の 2 箇所のみ。**原文注入する 3 アンカーはいずれも無変更**
（`prohibitions` L98–108 / `env_p0` L109–119 / `naming` L121–133）。

---

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（after A） | **PASS** | 統合対象は 3 コミットで想定と一致。`experiments/` の変更は配線検証の run のみ。`transfer/` は変更なし |
| **G2**（after C） | **PASS** | `make runindex` 後、**CSV 4 種の md5 が不変**。派生列も全て不変（詳細は §4-3） |
| **G3**（after D） | **PASS** | `make setup` が 2 回とも exit 0、読み込み確認まで成功。固定パッケージは不変 |

---

## 3. Phase A — 統合範囲の確認

### 統合対象（`origin/phase0..exp/lecun-wip-20260703`、Phase A 実施時点）

| commit | 内容 | 想定との対応 |
|---|---|---|
| `25ea5ef` | `s0(wiring_verification): mAP=0.000277151 seed42 [auto-sync]` | 自動同期によるもの ✅ |
| `100abd0` | `chore(runindex): reflect the wiring verification run` | 索引の再生成 ✅ |
| `3523293` | `docs(tasks): record the wiring verification run` | 記録 ✅ |

**件数 3。想定と完全に一致し、想定外のコミットは 0 件。** `unexpected_commits_in_range` は発生していない。

ファイル階層でも照合した。

| 検査 | 実測 |
|---|---|
| 変更される最上位ディレクトリ | `runindex/runs` 47 / `experiments/baselines` 7 / `tasks/T-2026-08-09-run-wiring-verification` 3 / `runindex/anomalies` 2 / `context/auto` 2 / その他 4 |
| `experiments/` の変更 | **`s0_040_wiring_verification_seed42` の 7 ファイルのみ** |
| `transfer/` の変更 | **なし** |
| 配線検証以前の作業 | **含まれていない** |
| 遠隔との差 | `origin/exp/lecun-wip-20260703..HEAD` = **0**（常駐スクリプトが自動 push 済み） |

削除 1034 行の出所は `index.csv` 750 行と `experiments.csv` 207 行で、**CSV が行単位で丸ごと
書き換わるため**である。内容の消失ではない。

### 索引の現在の実測値（起票時との差）

| | 起票時（`created_from`） | 現在 | 差 |
|---|---:|---:|---:|
| `index.csv` | 749 | **784** | **+35** |
| `experiments.csv` | 206 | **215** | +9 |
| `verdicts.csv` | 1038 | **1038** | **±0** |
| `per_class.csv` | 記載なし | 6588 | — |
| `task_id` を持つ行 | 記載なし | **1** | — |
| 除外 / 解析対象 | 記載なし | **82 / 702** | — |

**契約の `created_from` は書き換えていない。** この食い違いは前 task で索引を再生成した結果であり、
SPEC が事前に正常と宣言したとおり `make task-validate` が L2-8 で警告を出す。原因は B-36 に起票した。

---

## 4. Phase B / C — 後始末と記録

### 4-1. 成果物の記述（`notes.md`）

雛形の 3 箇所（「（ここに記入）」等）を **0 件**にした。書いた内容の要点は次のとおり。

| # | 要求 | 記載 |
|---|---|---|
| 1 | 配線の確認が目的 | 「配線の確認を目的とした run である。研究上の測定ではない」と冒頭に明記し、確認した 3 項目を列挙 |
| 2 | 性能の主張に使えない | 「この run を何に使ってはならないか」の節を設け、性能の主張・基準点・他の S0 群との併合の 3 つを禁じた |
| 3 | 契約の識別子 | `T-2026-08-09-run-wiring-verification` と、`config.yaml` の `task_id` を参照する旨 |
| 4 | 対照実験の宣言を持たない | `config.yaml` に `delta` 宣言が無く、索引でも `arm=unknown` / `control_of` 空 / `pairing_provenance=not_determinable` である旨 |
| 5 | 実測された数値 | `metrics.json` の 7 値と `per_class_ap.json` の非ゼロ 1 値を**転記**。計算し直していない |
| 6 | 装置と所要時間 | 装置 1（UUID `GPU-8f99ff6b-…`）、`CUDA_VISIBLE_DEVICES=1`、15 秒（21:17:01 → 21:17:16） |

**評価・解釈・見込みは書いていない。**「解釈」の節には解釈しない旨とその理由を書いた。

転記の正確性を機械検証した。`metrics.json` の 7 値と `per_class_ap.json` の非ゼロ値が
すべて `notes.md` 中に**原文の文字列として存在する**ことを確認している。

**数値の不変（判定3）**

| 対象 | 差分 |
|---|---:|
| 作業ツリー vs `HEAD` の `metrics.json` | **0 行** |
| 本 task 開始（`3523293`）vs `HEAD` の `metrics.json` | **0 行** |
| 同 `per_class_ap.json` | **0 行** |
| 同 `config.yaml` | **0 行** |
| 本 task で `experiments/` に触れたファイル | **`notes.md` のみ** |

### 4-2. 起票した未解決事項

採番は全 33 遠隔分岐を走査して実在の最大 **B-35** を確認し、その次から採った（走査コマンドの
欠陥については §5 D-1）。

| # | slug | 内容 |
|---|---|---|
| **B-36** | `BL-harvester-scan-is-host-dependent` | 収穫器はディスクを走査するため、同じ commit でもホストによって索引の行数が変わる。解析対象の行は除外規約により保護されるが、**索引の同一性は保証されない** |
| **B-37** | `BL-autosync-log-only-on-abort` | 自動同期の記録は中断時にのみ書かれる。**記録が無いことは不発火を意味しない**。発火の確認には commit の履歴を見る |

両方に再現手順と実測値を含めた。推測は書いていない。

**表の整合**: `py_compile` は通過。列数の検査は表 39 行すべてが区切り 6 個（5 列）で
**種類が 1 つ**。新規 2 行も 5 列。半角パイプの混入は無い。

### 4-3. G2 — 再生成の影響（実測）

| 対象 | 結果 |
|---|---|
| `runindex/*.csv` 4 種の md5 | **不変** ✅ |
| `runindex/anomalies/backlog.md` | 変化（+2 行。起票した 2 件） |
| `runindex/runs/baselines__s0_040_wiring_verification_seed42.json` | 変化（**`notes` フィールドのみ**） |
| `arm` / `control_of` / `pairing_provenance` / `control_note_value` | **すべて不変** |
| `excluded` / `task_id` / `experiment_id` | **すべて不変** |

run JSON の変化は Phase B で解禁された `notes.md` 追記が生の本文として格納されたもので、
**派生値は 1 つも動いていない**。`harvester_output_changed_beyond_backlog` には該当しない。

この結果は偶然ではない。`notes.md` を書く前に収穫器の実装を読み、`notes.md` から値を
取り出す 3 つの正規表現（`DELTA_SECTION_RE` / `CONTROL_VALUE_RE` / `PAIRED_DECLARED_RE`）を
特定し、**`## Δ` 見出しを作らないこと**を条件として本文を設計した。書いた後に
同じ正規表現で自己検査し、3 つとも不一致であることを確認してから `make runindex` を回している。

**軽量ビュー**: `make context` exit 0 / `make context-check` exit 0。
`context/auto/open_questions.md` の `^| BL-` は **34 → 36（+2）**。

`context/auto/*.csv` と `STATE.md` も変化したが、差分は `generated_from_commit` の
来歴スタンプ（`12cc0e8` → `100abd0`）のみである。

### 4-4. 依存導入の既知差（実測）

lecun で測定した結果は次のとおり。**SPEC が記述した事象がこのホストで再現した。**

| 実測 | 結果 |
|---|---|
| `.venv/bin/` の `pip` | **存在しない** |
| `.venv/bin/python -m pip --version` | `No module named pip` |
| `which pip`（`.venv` 有効時） | **`/home/ubuntu/.pyenv/shims/pip`** |
| `which python`（`.venv` 有効時） | `/home/ubuntu/slocal2/m2/.venv/bin/python` |

`python` は `.venv` を指すが `pip` は pyenv の shim を指すという非対称な状態であり、
**`pip install` は成功を表示しながら `.venv` 以外へ入る**。`tasks/README.md` の
「ホスト環境の既知差」へ lecun の行として記録し、一般則と他ホスト未検証である旨を散文で補った。

---

## 5. Phase D — 仕組み

### 5-1. 依存の一括導入（`make setup`）

**`make setup` は既に存在しており、その中身（`pip install -e ".[dev]"`）が
まさに問題の当事者だった。** SPEC は「追加する」と指示していたが、実装に従って置き換えた（§5 D-3）。

使えた導入手段の実測:

| 手段 | 実測 |
|---|---|
| `uv` | **`/home/ubuntu/.local/bin/uv` に 0.11.21 が存在** → これを採用 |
| `.venv/bin/python -m pip` | `No module named pip`（`ensurepip` は `pip 23.1.2` を持つが未導入） |
| 素の `pip` | pyenv の shim。**採用しない** |

要件の充足:

| # | 要件 | 実装 |
|---|---|---|
| 1 | 導入先を仮想環境へ明示 | `VENV_PY := .venv/bin/python` を定義し `uv pip install --python "$(VENV_PY)"` で明示。環境変数の状態に依存しない |
| 2 | 使えない場合は明確なエラーで停止 | `uv` も `.venv` 内 `pip` も無ければ理由を出して `exit 1`。**素の `pip` へは退避しない** |
| 3 | 導入後に読み込みを確認 | `"$(VENV_PY)" -c "import jsonschema, yaml"` を必ず実行 |
| 4 | 何度実行しても同じ結果 | 2 回目の新規導入は 0 件（§下表） |

**実行前に `--dry-run` で影響を確認し、利用者の承認を得てから実行した**（§5 D-6）。

| 実行 | exit | 変化 |
|---|---|---|
| dry-run | 0 | `+ coverage==7.15.4` / `+ pytest-cov==7.1.0` / `egosurgery-multitask` の再登録 |
| 1 回目 | **0** | 上記のとおり。`読み込み OK` |
| 2 回目 | **0** | 新規導入 **0 件**（`egosurgery-multitask` の再登録のみ）。`読み込み OK` |

**固定パッケージは前後で不変**: `torch=2.1.2+cu118` / `numpy=1.26.4` /
`transformers=4.44.2` / `mmcv=2.1.0` / `mmdet=3.3.0` / `mmengine=0.10.7`。

なお 2 回目も `egosurgery-multitask` の再登録だけは走る。これは `-e .` が editable wheel を
毎回ビルドし直す性質によるもので、**到達する状態は同一**である。純粋な no-op ではない点は事実として記す。

**他ホストでの動作は未検証である。**`uv` の有無・`.venv` の作られ方はホストによって異なる。

### 5-2. 資格情報の失効検出

| 状態 | 変更前 | 変更後 |
|---|---|---|
| 未設定 | 検出される | そのまま（変更していない） |
| 設定済みだが失効 | **未設定として報告** | **失効として報告** |
| 設定済みだが権限不足 | 未設定として報告 | **権限不足として報告** |
| 対象リポジトリ未選択 | 未設定として報告 | **到達不能として報告** |
| 有効 | 通過 | そのまま |

`gh api "repos/${GITHUB_REPOSITORY}"` を確認の呼び出しとし、応答の種別で文言を分けた。
**値そのものは出力しない。** `${{ }}` 展開ではなくシェル環境変数を使っており、注入経路は増やしていない。

分岐の実測（実際の失敗ログから採った応答文字列を流した結果）:

| 入力 | 出力される文言 |
|---|---|
| `gh: HTTP 401: Bad credentials (https://api.github.com/graphql)` | **失効** |
| `gh: HTTP 403: Resource not accessible by personal access token` | 権限不足 |
| `gh: HTTP 404: Not Found` | 到達不能 |
| `dial tcp: lookup api.github.com: no such host` | 判別不能（応答を併記） |

YAML の構文検査は通過（`jobs: ['draft-pr']` / `steps: 2`）。

### 5-3. 検証の限界

**有効な資格情報が無いため、通過経路（HTTP 200 で PR を起票する経路）は検証できない。**
本 task で確認したのは、401 の応答に対して失効の文言が出ることまでである。
403 / 404 / 判別不能の分岐も、応答文字列を流した論理検証にとどまり、
**実際の API 応答での確認はしていない。** 通過経路は資格情報の再発行後に確認が必要である。
**「動くはず」とは書かない。**

なお `AUTOSYNC_PR_TOKEN` そのものは変更していない（利用者の操作領域）。
2026-08-07T21:49:25Z の実行も 401 で失敗しており、失効は継続している。

---

## 6. 完了判定

| # | 判定 | 期待 | 実測 |
|---|---|---|---|
| 1 | 統合範囲が想定どおり | 想定外なし | ✅ 3 コミット・想定外 0 件 |
| 2 | 記述が埋まった | 雛形でない | ✅ 雛形の文言 **0 件** |
| 3 | 数値が不変 | 出力なし | ✅ **0 行**（作業ツリー・task 開始時比とも） |
| 4 | 未解決事項が 2 件増えた | 前より 2 増 | ✅ **34 → 36** |
| 5 | 表の列が揃っている | 列数の種類が 1 | ✅ 39 行すべて 6 区切り |
| 6 | 収穫器の出力が不変 | CSV 不変 | ✅ md5 4 種とも不変 |
| 7 | 軽量ビューが整合 | exit 0 | ✅ `context-check` exit 0 |
| 8 | 依存導入が動く | 読み込み OK | ✅ exit 0 / `読み込み OK` |
| 9 | 依存導入が冪等 | 2 回目も exit 0 | ✅ exit 0 / 新規導入 0 件 |
| 10 | 失効の文言が分かれた | 実装に反映 | ✅ 401 / 403 / 404 / その他の 4 分岐 |
| 11 | 既知差が記録された | 1 件 | ✅ 1 件 |
| 12 | 契約検証が通る | exit 0 | ✅ exit 0（WARN 2 件は母集団の変動。SPEC が正常と宣言） |
| 13 | 実行前検査が通る | exit 0 | ✅ 4 PASS / 4 SKIP / 0 FAIL |
| 14 | 全体テストが不変 | 開始前と比較 | ✅ **前 5 failed, 247 passed → 後 5 failed, 247 passed**。失敗テスト名も同一 |
| 15 | 禁止領域が無変更 | 出力なし | ✅ 出力なし |

**判定14 の基準点（本 task 開始前・2026-08-07 21:43 実測）**

```
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
5 failed, 247 passed, 22 warnings in 24.34s
```

開始前に本ホストで測ってから比較した。**5 件は本 task 着手前から赤であり、増えていない。**
`make setup` で `pytest-cov` と `coverage` が入ったが、件数・テスト名とも変化しなかった。

### preflight で SKIP された項目（合格ではない）

| 項目 | 理由 |
|---|---|
| `P2 cuda_ext_loaded` | `plan.env.preflight` に記載なし → **未実施** |
| `P3 deterministic_flags` | `plan.env.preflight` に記載なし → 未実施 |
| `P4 prereg_committed` | `kind=impl` のため対象外 |
| `P5 frozen_source_hash` | `kind=impl` のため対象外 |

本 task は演算装置を使わないため、`P2` / `P3` の未実施は実害が無い。

---

## 7. deviations（指示書どおりにしなかった箇所）

### D-1. SPEC の採番走査コマンドが 2 つの欠陥で何も返さなかった

- **指示:** Phase C Step 1 の
  `n=$(git show "$ref:tools/harvest_runindex.py" | grep -oE '"B-[0-9]+"' | tr -d '"B-' | ...)`
- **実際:** そのまま実行すると全 33 分岐で**何も出力されなかった**。原因は 2 つある。
  - **(a)** 実表記は引用符無しの `B-N` である（`| BL-… | B-25 | …` という Markdown 表のセル）。
    `grep -oE '"B-[0-9]+"'` は **0 件**を返す。
  - **(b)** 本ホストのシェルは zsh であり、`"$ref:tools/…"` の `:t` が**変数展開修飾子**として
    解釈される。`refs/remotes/origin/phase0` が `phase0` に変換され、
    `fatal: ambiguous argument 'phase0ools/harvest_runindex.py'` となる。
- **修正:** パターンを `grep -oE 'B-[0-9]+'` に、変数参照を `"${ref}:tools/…"` に変えて再走査した。
- **影響の重大さ:** 2 つの欠陥は**同じ症状**（何も出ない）を示す。指示どおりなら「他分岐に採番なし」と
  読み、**B-1 から採番して既存 35 件と全面衝突**していた。SPEC 自身が「過去に採番の衝突が起きている」と
  警告していた事故を、SPEC のコマンドが再生産するところだった。
- **分類:** **SPEC の欠陥**（(a)）+ **環境差**（(b)。bash では `:t` は修飾子ではない）

### D-2. SPEC が示した既知差の追記例が表を壊す

- **指示:** Phase C Task 4 Step 1 の `| 依存の導入 | …長文… |`
- **実際:** この例は**セルが 2 つ**だが、既知差の表は `| ホスト | 差分 | 影響 |` の **3 列**である。
  そのまま貼ると列数が壊れる。また第 1 列は「ホスト」なので「依存の導入」は意味が合わない。
- **修正:** 実測したホスト名（`lecun`）を第 1 列とする 3 列の行にし、一般則と他ホスト未検証である旨は
  散文で補った。列数は表全体で 4 区切りに揃っている。
- **分類:** **SPEC の欠陥**（B-33 で起票済みのパイプ事故と同型）

### D-3. `make setup` を追加ではなく置き換えた

- **指示:** Phase D Task 5 Step 2「ターゲットを追加する。挿入位置に注意。既存レシピの途中へ入れない」
- **実際:** `make setup` は `Makefile:3-4` に既に存在し、中身は `pip install -e ".[dev]"` だった。
  **これが問題の当事者そのもの**である（素の `pip` が pyenv の shim へ解決される）。
  追加すると同名ターゲットが重複するため、既存レシピを要件 4 件を満たす形へ置き換えた。
- **分類:** **SPEC の欠陥**（想定外規定「実装が SPEC の想定と食い違う → 実装に従う」に従った）

### D-4. 依存の導入前に影響を実測し、承認を得た

- **指示:** SPEC は `make setup` の実行を求めるのみで、事前確認は指示していない
- **実際:** 実行前に `uv pip install --dry-run` を回し、変化が `coverage` と `pytest-cov` の
  2 件追加のみで固定パッケージが動かないことを確認したうえで、利用者の承認を得てから実行した。
- **理由:** `CLAUDE.md` は依存の追加を無断実行禁止としており、また `.venv` を
  「検証済み構成・再構築しないこと」と定めている。**`make setup` が今まで環境を壊さなかったのは、
  pip が別環境へ入っていたからである。** 直した瞬間に初めて `.venv` へ届くため、
  ここが最も環境を壊しやすい一歩だった。
- **分類:** **判断が必要だった**

### D-5. `notes.md` を書く前に収穫器の抽出パターンを実装から特定した

- **指示:** Phase B は記述を埋めることのみを求め、収穫器への影響には触れていない
- **実際:** 書く前に `harvest_runindex.py` を読み、`notes.md` から値を取り出す 3 つの正規表現
  （`DELTA_SECTION_RE` / `CONTROL_VALUE_RE` / `PAIRED_DECLARED_RE`）を特定し、
  `## Δ` 見出しを作らないことを設計条件にした。書いた後に同じ正規表現で自己検査した。
- **理由:** Phase B の追記が索引の派生列を動かすと、Phase C の **G2 が落ちる**。
  「動かないはず」という推測のまま `make runindex` を回すと、落ちてから原因を探すことになる。
- **分類:** **判断が必要だった**

### D-6. 判定3 の測り方を途中で正した

- **指示:** 完了判定 3「数値が不変 / `git diff <run>/metrics.json` / 出力なし」
- **実際:** 最初に `git diff origin/phase0...HEAD -- <run>/metrics.json` で測り **15 行**を得たが、
  これは誤りだった。当該ファイルは自動同期 `25ea5ef` で**初めて git に入った新規ファイル**であり、
  `origin/phase0` 比では全行が追加として数えられる。数値の変更ではない。
  作業ツリー比と本 task 開始（`3523293`）比で測り直し、**いずれも 0 行**を確認した。
- **分類:** **判断が必要だった**（測定基準の誤り。自分で気付いて正した）

### D-7. `conventions_rev` を実測値へ置換した

- **指示:** SPEC Task 7 Step 1 が「実行者が実測して置換する。**これは逸脱ではなく手順である**」と明記
- **実際:** `spec.yaml` の `conventions_rev` を `1201f4f` → `d422b08` に更新した
- **分類:** 手順どおり（記録のため列挙）

---

## 8. 未解決・申し送り

### 8-1. 他ホストでの `make setup` の動作確認が未達

**本 task で確認したのは lecun のみである。** `uv` の有無、`.venv` の作られ方、
`ensurepip` の可否はホストによって異なる。実装は
「`uv` → `.venv` 内 `pip` → 明確なエラーで停止」の順に退避するが、
**`uv` も `.venv` 内 `pip` も無いホストでは停止する。** そのホストでは
`.venv` の作り直しか `uv` の導入が別途必要になる。

統合後、各ホストで `make setup` を一度回して結果を持ち寄る必要がある。

### 8-2. 資格情報の通過経路が未検証

§5-3 のとおり。**有効な資格情報が無いため 200 の経路は確認できていない。**
`AUTOSYNC_PR_TOKEN` の再発行は利用者の操作領域であり、本 task では触れていない。
再発行後に、下書きの起票が実際に成功することの確認が必要である。

### 8-3. 索引の同一性（B-36）の方針が未定

収穫器がディスクを走査する性質は起票したが、**どう扱うかは決まっていない**。
取りうる 3 案（走査を git 追跡下に限る / 退避一覧を規約化する / 正本ホストを定める）は
B-36 に記載した。決まるまで `meta.created_from.counts` を根拠にする L2-8 は
ホスト差で警告を出し続ける。

### 8-4. 自動同期の記録の設計（B-37）の方針が未定

「成功時にも記録を書く」か「記録の意味を文書化して commit 履歴で判定する」かのうち、
**後者は本 task で着手済み**（`tasks/README.md` に「自動同期の確認方法」を追加）。
前者を採る場合は、Syncthing で全台に配られる記録の肥大（現状 826 行）への対処が要る。

### 8-5. `plan.env.preflight` に `cuda_ext_loaded` が無い

前 task から継続する事項。本 task は演算装置を使わないため実害は無いが、
GPU を使う契約では `plan.env.preflight` に `cuda_ext_loaded` を入れる必要がある。

---

## 9. 統合対象の一覧（PR 本文と同じ内容）

`origin/phase0...HEAD` = **73 files changed, 6456 insertions(+), 1043 deletions(-)**

| commit | 内容 |
|---|---|
| `25ea5ef` | 配線検証の run の証跡 7 ファイル（自動同期が生成） |
| `100abd0` | 索引の再生成（`runindex/` と `context/auto/`） |
| `3523293` | 前 task の記録（`tasks/` と `tasks/inbox.md`） |
| `183ae50` | 配線検証の run の記述（`notes.md`。数値は不変） |
| `6340808` | 未解決事項 B-36 / B-37 の起票と索引・軽量ビューへの反映 |
| `a059e2e` | ホスト環境の既知差と自動同期の確認方法（`tasks/README.md`） |
| `8d45db9` | `make setup` の作り直し（`Makefile` / `tasks/README.md`） |
| `d30c413` | 資格情報の失効検出（`.github/workflows/auto-draft-pr.yml`） |

**全ホストへ配られるもの**: 索引の +35 行（うち 34 行は lecun のディスクにのみ存在する
退避 run で、すべて `excluded=True`。解析対象の増分は +1）、未解決事項 2 件、
`make setup`、既知差の記録、失効検出。

**`data/splits/` `context/conventions.md` `src/` は無変更**である。

---

## 10. 数値の出所

**すべての数値は本ホスト（lecun）での実測である。** 未測定の項目は無い。
検証できなかった事項（他ホストの `make setup`、資格情報の通過経路）は
**未検証と明記**しており、推測で補っていない。
`mAP=0.0002771509158176216` は配線確認の副産物であり、性能の主張には使えない。
