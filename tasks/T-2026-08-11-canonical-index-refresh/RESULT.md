# RESULT — T-2026-08-11-canonical-index-refresh

**実行者:** `lecun` / `feat/canonical-index-refresh` / `origin/phase0` の `510a5e8` から分岐
**実行日時:** 2026-08-09T18:34Z 〜 2026-08-09T18:50Z
**判定:** **PASS** — 追跡外 0 件のホストで生成し、**既存の値が一件も変わらず 2 列だけが増えた**ことを指紋で実証した。

| 受入基準 | 結果 |
|---|---|
| 追跡外の経路を持つ行が無いホストで生成されている | ✅ **0 件**（陽性対照で検査の有効性も確認） |
| 追加された列が索引に存在する | ✅ `wandb_run_id` / `wandb_run_url` |
| 既存の列の値が一件も変わっていない | ✅ **指紋が完全一致** |
| 軽量ビューが索引と整合している | ✅ `context-check` exit 0 |
| `make task-validate` が exit 0 | ✅ |
| `make task-preflight` が exit 0 | ✅ 4 PASS / 4 SKIP / 0 FAIL |

---

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | **記載なし** | 対象外（本契約に分母の宣言は無い） |
| `inputs.sigma_policy` | **記載なし** | 対象外（判定を行わない） |
| `inputs.frozen_source.ref` | **記載なし** | 対象外。preflight の `P5` も `kind=impl` のため SKIP |
| `contract.conventions_rev` | `1201f4f` | **`d422b08` へ実測置換**（SPEC Task 3 Step 1 の手順に従う） |
| `contract.inject_verbatim` | `conventions#prohibitions` | 下記に原文を転記 |

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

### `conventions_rev` の差分

`1201f4f` → `d422b08` は **+10 / −0**。差分ハンクは `frozen_source` 節（L56 に 9 行）と
変更履歴（L143 に 1 行）の 2 箇所のみ。**原文注入する `prohibitions`（L98–108）は無変更。**

---

## 2. 取り込みの完全性

バンドルは Write ツールで書き、シェルのヒアドキュメントを使っていない。

| 検査 | 実測 |
|---|---|
| 行数 | **397 行**（想定どおり） |
| 先頭行 | `#!TASK-BUNDLE v1 delim=TASKBUNDLEB5996C8A73AF0EEC627C89CF6F59F183C7BF1CCE` |
| 最終行 | `TASKBUNDLEB5996C8A73AF0EEC627C89CF6F59F183C7BF1CCE END` |
| 区切り文字の一致 | **一致** |
| `make task-fetch` | **exit 0** |
| 展開後の `spec.yaml` とバンドル内の本文 | **1719 字 / 完全一致** |
| 展開後の `SPEC.md` とバンドル内の本文 | **7442 字 / 完全一致** |

**取り込みで本文が壊れていないことを、区切りで切り出して突き合わせて確認した。**

---

## 3. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（after A） | **PASS** | 追跡外の経路を持つ行 **0 件**。陽性対照が反応した |
| **G2**（after B） | **PASS** | 追加 2 列 / 消えた列 0 / 行数不変 / 既存部分の指紋が一致 / 追加列が空でない行 0 |

---

## 4. Phase A — 条件の確認

### 4-1. 作業ツリーと同期の状態

| 項目 | 実測 |
|---|---|
| 分岐 | `feat/canonical-index-refresh`（`origin/phase0` の `510a5e8` から） |
| `HEAD..origin/phase0` | **0** |
| 未追跡 | 2 件のみ（下記） |

未追跡の 2 件はいずれも想定内である。

| 未追跡 | 素性 |
|---|---|
| `docs/sessions/digest/2026-08-02-846b93b9-…md` | **対話記録の抽出物**（先頭に「対話記録から機械的に抽出した要素のみ」と明記）。`tasks/README.md:146` の方針どおり本 task の記録と一緒に含める |
| `tasks/T-2026-08-11-canonical-index-refresh/` | 本 task の契約（取り込んだもの） |

**それ以外の差分は無く、停止条件に該当しなかった。**

### 4-2. G1 — 追跡外の経路

| 項目 | 実測 |
|---|---|
| 経路の列 | `['path']`（1 つのみ。曖昧さなし） |
| 行数 / 列数 | **751 行 / 89 列** |
| **追跡外の経路を持つ行** | **0 件** |

`untracked_path_found` は発生していない。

### 4-3. 検査が空振りでないことの確認（陽性対照）

| 入力 | 結果 |
|---|---|
| `tools/harvest_runindex.py`（実在） | **追跡下** |
| `no/such/path/at/all`（存在しない） | **追跡外** |

**両者が分かれたので、この検査は有効である。** 検査が常に「追跡下」を返すなら
0 件という結果に意味は無かった。

### 4-4. 生成前の控え

| 項目 | 値 |
|---|---|
| 行数 | **751** |
| 列数 | **89** |
| 指紋（sha256） | `7ab8e8b9bfe0ccd7d04e5c4a011bec6fa7d9acd0d611ec80d60b610b984bb8fe` |

控えは `/tmp/idx_refresh/` に `index_before.csv` / `md5_before.txt` / `before.json` として保存した。
**記録を作る流れに表示用の切り詰めを混ぜていない。**

---

## 5. Phase B — 生成と検査

### 5-1. G2 — 集合差による検査

**名前の部分一致は使っていない。新旧のヘッダの集合差で求めた。**

| 項目 | 期待 | 実測 |
|---|---|---|
| 追加された列 | 2 つ | **`wandb_run_id`, `wandb_run_url`** ✅ |
| 消えた列 | 無し | **なし** ✅ |
| 行数 | 不変 | **751 → 751** ✅ |
| 既存部分の指紋 | 一致 | **`7ab8e8b9bfe0ccd7…` == `7ab8e8b9bfe0ccd7…`** ✅ |
| 追加列が空でない行 | 0 | **0** ✅ |

指紋は「追加された列を除いた全セル」を `ledger_key` 順・キー名順に連結した sha256 である。
**一致は、751 行 × 89 列のすべての値が 1 文字も変わっていないことを意味する。**
`existing_values_changed` は発生していない。

追加列が全行で空であることは、**遡っての対応づけを行っていない**という前提と整合する。
外部サービスへの問い合わせは行っていない（禁止事項 5）。

### 5-2. 差分の内訳

| 対象 | 件数 | 内容 |
|---|---:|---|
| `runindex/runs/*.json` | **722** | 各 3 行の追加（下記） |
| `runindex/index.csv` | 1 | 2 列の追加（全行が書き換わるため 1504 行の差分に見える） |
| `runindex/anomalies/backlog.md` | 1 | **B-38 が新規に載る** |
| `runindex/anomalies.md` | 1 | **3 箇所**（下記） |
| `context/auto/**` | **0** | 差分なし（理由は §5-4） |

`runs/*.json` の変更は **722 件すべて同一**である。

```
-  "task_id": ""
+  "task_id": "",          ← 後続キーが増えたことによる区切り記号のみ
+  "wandb_run_id": null
+  "wandb_run_url": null
```

**値の変更は 1 件も無い。**

### 5-3. `index.csv` 以外の差分の特定

SPEC は「別ホスト固有の空のディレクトリに由来する行が消える」と予告していた。
**予告された 1 件に加え、予告されていない 2 件があった。** いずれも特定した。

| # | 変化 | 特定した原因 |
|---|---|---|
| 1 | `_smoke_proptest_20260804_223211` の行が**消える** | **予告どおり。** 正本を生成したホストにのみ存在した空ディレクトリ。lecun のディスクに存在せず、版管理の追跡下にも無い（0 ファイル・履歴なし）。前契約 `T-2026-08-11-leftover-relocation` §8 で特定済みのもの |
| 2 | `analysis` のファイル数 **96 → 176** | **予告なし。** `experiments/analysis` はディスク 176 / 追跡下 176 / **未追跡 0**。正本を生成した commit `64576f3` の時点では追跡下 96 だった。増分 80 は PR #56 で phase0 へ統合された追跡下のファイルである |
| 3 | `audit` のファイル数 **3 → 8** | **予告なし。** `experiments/audit` はディスク 8 / 追跡下 8 / **未追跡 0**。`64576f3` の時点では 3 だった。同様に統合済みの追跡下のファイル |

**2 と 3 はこのホスト固有の汚れではない。** 正本の `anomalies.md` が
`64576f3` 以降に統合された成果を反映しておらず、**古かった**というだけである。
両ディレクトリとも未追跡 0 件であり、G1 の判定は依然として有効である。

`runindex/anomalies/backlog.md` に B-38 が新規に載るのも同型である。B-38 は
別ホストの契約で `tools/harvest_runindex.py` へ追記されたが、**生成物である
`backlog.md` が再生成されていなかった。** 実測: commit 済みの `backlog.md` の
B-38 出現数 **0** → 再生成後 **1**。

### 5-4. 軽量ビューが不変だった理由

`make context` / `make context-check` はともに **exit 0**、`context/auto/` の差分は **0 件**。
「差分 0」は正しい結果と「コマンドが走っていない」の両方でありうるため、**別の方法で裏を取った。**

| 裏取り | 実測 |
|---|---|
| `make context` が実際に走ったか | 4 ファイルすべて mtime **18:42:32**（実行時刻）に更新 |
| `context/auto/open_questions.md` の B-38 | **既に 1 件あった**（commit 済みの状態で） |
| commit 済み `runindex/anomalies/backlog.md` の B-38 | **0 件** |

`open_questions.md` は `tools/harvest_runindex.py` の BACKLOG から直接生成されるため、
B-38 は既に載っていた。一方 `backlog.md` だけが古く、**2 つの生成物が食い違っていた。**
本 task の再生成でその齟齬が閉じた。

新しい 2 列が軽量ビューに現れないのは、`experiments_summary.csv` の列一覧が固定で
wandb を含まないためである（設計どおり）。

### 5-4b. 索引を commit した直後に軽量ビューが不整合になった

**SPEC の手順の順序は、構造的に整合を作れない。**

`make context` は生成物に「`runindex/` に触れた**最後の commit**」をスタンプする。
SPEC の順序は次のとおりである。

| 段階 | `runindex/` の最新 commit | スタンプされる値 |
|---|---|---|
| Step 4 で `make context` | `64576f3`（まだ commit していない） | `64576f3` |
| Step 5 で `runindex/` を commit | **`f96edc1`** | （据え置き `64576f3`） |

**commit した瞬間にスタンプが古くなる。** 実測でも Step 4 時点では
`context-check` が exit 0 だったが、Step 5 の commit 後に **exit 2**（検査器 1）へ変わった。

差分は**来歴スタンプの行だけ**で、内容は完全に同一だった。

```
-    generated_from_commit: 64576f3feb110a3db8642e06c59c7503b7d7740f
-    generated_from_date:   2026-08-08T04:48:37+00:00
+    generated_from_commit: f96edc1ccdda8d124e6069edeeac3ead8ec9cfdd
+    generated_from_date:   2026-08-09T18:43:15+00:00
```

`runindex_counts: index=751 experiments=207 verdicts=1038` は両側で同一であり、
**数値は一切動いていない。**

SPEC の想定外一覧は「軽量ビューが整合しない → 停止して報告」と定めるため、
**ここで止めて利用者へ提示し、`make context` を再実行して commit する判断を得た。**

解消は収束する。`runindex/` の commit 後に再生成するとスタンプが `f96edc1` になり、
その後 `context/auto/` だけを commit しても `runindex/` の最新は `f96edc1` のままなので、
再生成しても同じ結果になる。実測で確認した。

| 検査 | 実測 |
|---|---|
| 再生成後の `context-check` | **exit 0** |
| スタンプ | `f96edc1` = `runindex/` の最新 commit |
| 変更されたのはスタンプだけか | **4 ファイル / +6 −6 行**（すべて来歴の行） |
| commit 後にもう一度 `make context` | **md5 不変（冪等・収束した）** |

追加の commit: `e28f97f` chore(context): restamp the lightweight view after the index commit

### 5-5. 成果物間の非対称（発見）

`index.csv` は **全 751 行が 2 列を保持**する（欠く行 0 / 空でない行 0）。
一方、個別 JSON では **`transfer_legacy` 群の 29 件に 2 キーが出力されない。**

| 群 | 件数 | 2 キーの有無 |
|---|---:|---|
| `transfer_legacy`（リポジトリ直下 `transfer/` を B-12 で取り込んだもの） | **29** | **無し**（キー数 55） |
| その他すべて | 722 | 有り |

受入基準は索引側を問うため充足しているが、**生成経路が 2 系統あり、片方が新しい列を
出力していない**という事実である。`tools/**` は禁止事項 3 のため**修正していない。**

---

## 6. 完了判定

| # | 判定 | 期待 | 実測 |
|---|---|---|---|
| 1 | 追跡外の経路が無い | 0 件 | ✅ **0 件** |
| 2 | 検査が空振りでない | 陽性対照が反応する | ✅ 実在→追跡下 / 不在→追跡外 |
| 3 | 追加された列がある | 2 つ | ✅ `wandb_run_id` `wandb_run_url` |
| 4 | 消えた列が無い | 無し | ✅ なし |
| 5 | 行数が不変 | 不変 | ✅ 751 → 751 |
| 6 | 既存の値が不変 | 指紋が一致 | ✅ **一致** |
| 7 | 追加列が全行で空 | 0 行 | ✅ **0 行** |
| 8 | 軽量ビューが整合 | exit 0 | ✅ `context-check` exit 0（**索引の commit 後に再生成が要った。§5-4b**） |
| 9 | 契約検証が通る | exit 0 | ✅ exit 0（WARN 2 件は L2-8 の分母変動） |
| 10 | 実行前検査が通る | exit 0 | ✅ 4 PASS / 4 SKIP / 0 FAIL |
| 11 | 受け皿の集約が整合 | exit 0 | ✅ `inbox-check` exit 0 |
| 12 | 試験が不変 | 開始前と比較 | ✅ **前 5 failed, 264 passed → 後 5 failed, 264 passed**。失敗テスト名も同一 |
| 13 | 禁止領域が無変更 | 空 | ✅ **出力なし** |

**判定12 の基準点（本 task 開始前・2026-08-09 18:36 実測）**

```
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
5 failed, 264 passed, 22 warnings in 24.36s
```

**5 件は本 task 着手前から赤であり、増えていない。**

### preflight で SKIP された項目（合格ではない）

| 項目 | 理由 |
|---|---|
| `P2 cuda_ext_loaded` | `plan.env.preflight` に記載なし → **未実施** |
| `P3 deterministic_flags` | `plan.env.preflight` に記載なし → 未実施 |
| `P4 prereg_committed` | `kind=impl` のため対象外 |
| `P5 frozen_source_hash` | `kind=impl` のため対象外 |

本 task は演算装置を使わないため、`P2` `P3` の未実施に実害は無い。

---

## 7. deviations（指示書どおりにしなかった箇所）

### D-1. SPEC が予告していない差分が 2 件あった

- **指示:** Phase B Step 3「別ホスト固有の空のディレクトリに由来する行が消えることが
  分かっている。**消える場合は、それが何かを特定してから記録する**」
- **実際:** 予告された 1 件（`_smoke_proptest_20260804_223211`）に加え、
  **予告のない変化が 2 件**あった（`analysis` 96→176、`audit` 3→8）。
  いずれも「行が消える」ではなく「ファイル数が増える」変化である。
- **対応:** 断定せず、追跡状態を実測して切り分けた。両ディレクトリとも**未追跡 0 件**で、
  増分は `64576f3` 以降に phase0 へ統合された追跡下のファイルだった。
  **このホスト固有の汚れではない。**
- **分類:** **SPEC の欠陥**（予告が不完全だった）

### D-2. 差分表示のコマンドが巨大な出力を生んだ

- **実際:** Phase B Step 3 で全変更ファイルの差分を展開したところ **234KB** になり、
  読み取れなかった。分類の集計と対象を絞った表示に切り替えて測り直した。
- **影響:** 記録には影響しない（表示のみ）。ただし SPEC の申し送り「記録を作る流れに
  表示用の切り詰めを混ぜない」の裏返しとして、**表示側でも件数を見積もってから展開すべき**だった。
- **分類:** **判断が必要だった**

### D-3. 索引の commit 後に `make context` を再実行し、追加で commit した

- **指示:** Phase B は Step 4 で `make context` → Step 5 で `runindex/` と `context/auto/` を
  同時に commit する順序である。追加の再生成は指示されていない。
- **実際:** Step 5 の commit 直後に `context-check` が **exit 2 へ変わった**（§5-4b）。
  SPEC の想定外一覧「軽量ビューが整合しない → 停止して報告」に従い**停止して報告し**、
  利用者から `make context` を再実行して commit する判断を得た。
- **理由:** `make context` は「`runindex/` に触れた最後の commit」をスタンプするため、
  **SPEC の順序では commit した瞬間にスタンプが古くなる。** 順序を入れ替えても
  原理的に解消しない（スタンプは常に直前の commit を指す）。
  再生成して `context/auto/` だけを commit すると収束する。
- **影響:** 数値は一切変わらない。変更は来歴の行のみ（4 ファイル / +6 −6）。
- **分類:** **SPEC の欠陥**（手順の順序が整合を作れない）

### D-4. `transfer_legacy` 群の非対称を発見したが修正していない

- **実際:** 個別 JSON の生成経路が 2 系統あり、`transfer_legacy` の 29 件には
  新しい 2 キーが出力されない（§5-5）。
- **対応:** 禁止事項 3「`tools/**` `src/**` を変更する」に従い**修正していない。**
  事実として記録し、§8 へ申し送る。
- **分類:** **判断が必要だった**

### D-5. 一時ファイルの置き場は SPEC の指定に従った

- **実際:** `/tmp/task.bundle.txt`（利用者の明示指示）と `/tmp/idx_refresh/`（SPEC の指定）を
  そのまま使った。直前の 2 契約では作業領域へ置き換えていたが、本 task では
  **指示が明示的なため従った。**
- **分類:** 手順どおり（記録のため列挙）

### D-6. `conventions_rev` を実測値へ置換した

- **指示:** SPEC Task 3 Step 1 が「実行者が実測して置換する。**これは逸脱ではなく手順である**」と明記
- **実際:** `1201f4f` → `d422b08` に更新した
- **分類:** 手順どおり（記録のため列挙）

### 事前の懸念が外れた点（逸脱ではないが記録する）

`make context` の差分が 0 件だったとき、「コマンドが走っていない」可能性を疑って
mtime と B-38 の所在を確かめた。**結果は「正しく不変」であり、懸念は外れた。**
ただし確かめる前に「整合している」と書いていたら、根拠のない主張になっていた。

---

## 8. 未解決・申し送り

### 8-1. 個別 JSON の生成経路が新しい列に追随していない

`transfer_legacy` の 29 件は `wandb_run_id` / `wandb_run_url` を持たない（§5-5）。
索引 `index.csv` は全行が 2 列を保持するため解析には影響しないが、
**個別 JSON を直接読む利用者は群によって鍵の有無が違うことに気付けない。**
`tools/**` は本 task の範囲外のため未修正。

### 8-2. 生成物どうしが食い違う状態が起きうる

`context/auto/open_questions.md` には B-38 があり、`runindex/anomalies/backlog.md` には
無かった（§5-3）。**同じ出所から作られる 2 つの生成物が、再生成の有無で食い違う。**
`make runindex` と `make context` の実行を対にする規約は明文化されていない。

### 8-2b. 軽量ビューの来歴スタンプが常に 1 commit 遅れる

§5-4b のとおり、`make context` は「`runindex/` に触れた最後の commit」をスタンプするため、
**索引を commit した直後は必ず `context-check` が失敗する。** 順序を入れ替えても解消しない。

現状の回避策は「索引を commit したあとにもう一度 `make context` して、
`context/auto/` だけを別 commit にする」ことである。本 task ではそうした。

**手順として明文化するか、スタンプの取り方を変えるかの判断が要る。**
取りうる案は、(i) スタンプを `runindex/index.csv` の内容ハッシュにする、
(ii) 索引と軽量ビューを 1 commit にまとめたうえでスタンプを省く、
(iii) 現状の 2 段 commit を規約として `tasks/README.md` へ書く、の 3 つ。
本 task では `tools/**` が範囲外のため (iii) も含めて着手していない。

### 8-3. 正本の鮮度を測る手段が無い

`anomalies.md` のファイル数が古かったこと（§5-3 の 2 と 3）は、
再生成して差分を見るまで分からなかった。**正本がいつの時点の disk 状態を反映しているかを
示す情報が生成物に無い。** `context/auto/` は `generated_from_commit` を持つが、
`runindex/` 側には無い。

### 8-4. 追加列は今後の run にのみ入る

`wandb_run_id` / `wandb_run_url` は全 751 行で空である。
遡っての対応づけは行っていない（禁止事項 5）。値が入るのは今後の run からであり、
過去分を埋めるには外部サービスへの問い合わせを許す別契約が要る。

---

## 9. 数値の出所

**すべての数値は本ホスト（lecun）での実測である。** 未測定の項目は無い。
指紋の一致は 751 行 × 89 列のすべての値を連結した sha256 の比較であり、
標本ではなく全件の照合である。推測で補った箇所は無い。
