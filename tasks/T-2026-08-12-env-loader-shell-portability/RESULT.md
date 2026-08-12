# RESULT — T-2026-08-12-env-loader-shell-portability

**実行者:** `lecun` / `feat/env-loader-portability` / `origin/phase0` の `5e07812` から分岐
**実行日時:** 2026-08-10T09:30Z 〜 2026-08-10T09:55Z
**判定:** **PASS（一部 UNKNOWN）** — 読み込みは両シェルで成立するようになった。
外部台帳の直近の投稿時刻は**この資格情報では到達できず `UNKNOWN`**。

| 受入基準 | 結果 |
|---|---|
| 対話シェルから読み込みが成立する | ✅ |
| 別のシェルからも従来どおり成立する | ✅ |
| 同型の書き方を持つ他の入口が調査されている | ✅ 23 ファイルを判定。修正要は 0 件 |
| 資格情報の値が出力にも記録にも含まれない | ✅ 有無のみ |
| 外部記録の直近の投稿時刻が実測されている | ⚠ **到達不能。`UNKNOWN`**（理由は実測） |
| `make task-validate` が exit 0 | ✅ |
| `make task-preflight` が exit 0 | ✅ 4 PASS / 4 SKIP / 0 FAIL |

---

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | **記載なし** | 対象外 |
| `inputs.sigma_policy` | **記載なし** | 対象外 |
| `inputs.frozen_source.ref` | **記載なし** | 対象外。preflight の `P5` も `kind=impl` のため SKIP |
| `contract.conventions_rev` | `1201f4f` | **`d422b08` へ実測置換**（SPEC Task 5 Step 1 の手順に従う） |
| `contract.inject_verbatim` | `conventions#prohibitions`, `conventions#env_p0` | 下記に原文を転記 |

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

`1201f4f` → `d422b08` は **+10 / −0**。差分ハンクは L56（`frozen_source` 節）と L143（変更履歴）の 2 箇所。
**原文注入する 2 アンカーはいずれも無変更**（`prohibitions` L98–108 / `env_p0` L109–119）。

---

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（after A） | **PASS** | 両方向の対照が働き、基点の実測値を得て、原因を実装から説明できた |
| **G2**（after B） | **PASS** | 両シェル＋repo 外の 4 ケースすべて成功。陰性対照も働いた |
| **G3**（after D） | **ask → UNKNOWN で記録**（利用者の判断） | 台帳へ到達できず、直近の投稿時刻は測定不能 |

---

## 3. Phase A — 再現と原因

### 3-1. 問題の行

`scripts/load_env.sh` の 19 行目（**関数 `_egosurgery_load_env` の内側**）。

```bash
root="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
```

### 3-2. 両方向の対照（実測）

| 呼び方 | 出力 |
|---|---|
| `zsh -ic 'cd <repo>; source scripts/load_env.sh'` | `[load_env] /home/ubuntu/slocal2/.env.gpg が無い。…` ❌ |
| `bash -lc 'cd <repo>; source scripts/load_env.sh'` | `[load_env] .env をロード（WANDB_API_KEY=set / NOTION_API_KEY=set）` ✅ |

**対照は両方向で働いた。** 出力は `set` / `unset` のみで、値は 1 文字も含まれない。

### 3-3. 基点の実測値

**SPEC の探査はファイルの最上位で測るが、実際の該当行は関数の内側にある。**
両方を並べて測った。

| 測り方 | シェル | `$0` | `BASH_SOURCE[0]` | 解決された基点 |
|---|---|---|---|---|
| **関数の内側**（実構造と同じ） | zsh | **`_probe_fn`** | **未定義** | **`/home/ubuntu/slocal2`**（CWD の 1 つ上）❌ |
| 関数の内側 | bash | `bash` | `/tmp/probe_func.sh` | `/`（probe の位置から正しく）✅ |
| ファイルの最上位（SPEC の探査） | zsh | `/tmp/probe_root.sh` | 未定義 | `/`（**正しく解決する**） |
| ファイルの最上位 | bash | `bash` | `/tmp/probe_root.sh` | `/` ✅ |

zsh の `FUNCTION_ARGZERO` は **on**（実測）。

### 3-4. 原因（実装から説明）

1. `BASH_SOURCE` は bash 固有であり、zsh では未定義 → `${BASH_SOURCE[0]:-$0}` は `$0` に落ちる。
2. zsh は既定で `FUNCTION_ARGZERO` が有効なため、**関数の内側の `$0` は関数名**になる。
3. したがって `dirname "_egosurgery_load_env"` = `.` → `cd "./.."` が **CWD の 1 つ上**を指す。
4. CWD が repo 直下なら基点は repo の 1 つ上（`/home/ubuntu/slocal2`）になり、`.env.gpg` に到達しない。

**壊れるのは「関数の内側」だけである。** zsh でもファイルの最上位なら `$0` は
スクリプトのパスを指す（3-3 の実測）。この違いが解決方法の選択に直結した。

---

## 4. Phase B — 修正

### 4-1. 選んだ方法と、実測に基づく理由

**選択: 「最上位で自分の位置を捉えて関数へ渡す」**（SPEC の一覧に無い 4 番目の方法）。

SPEC は 3 番目（版管理の問い合わせで repo の根を取る）を推奨したが、
「実測してから決める」「推奨されたからではなく実測に基づく理由を書く」とも定めている。
実測の結果、次のとおり 4 番目が優った。

| 候補 | repo 内（zsh / bash） | **repo の外から絶対パスで source** | git 依存 | CWD 依存 |
|---|---|---|---|---|
| 3: `git rev-parse --show-toplevel` | ✅ `/home/ubuntu/slocal2/m2` | ❌ `fatal: not a git repository`（exit 128） | **あり** | **あり** |
| **4: 最上位で捕捉**（採用） | ✅ / ✅ | ✅ **`/home/ubuntu/slocal2/m2`**（両シェル） | なし | なし |

採用の理由は 4 つ。**いずれも実測に基づく。**

1. **repo の外から呼んでも正しい経路を返す。** 候補 3 はそこで失敗する（実測）。
2. **`git` の有無に依存しない。** 資格情報の読み込みは版管理と無関係の操作である。
3. **CWD に依存しない。** 候補 3 は CWD が repo 外なら別の repo を拾うか失敗する。
4. **元の意図をそのまま保つ。** 「スクリプトの場所 → その 1 つ上が repo」という
   既存の考え方を変えず、**式を関数の外へ出すだけ**で済む。

### 4-2. 変更内容

変えたのは基点の解決だけである。復号の手順・変数の設定方法・出力の文言には触れていない。

```
+_egosurgery_env_self="${BASH_SOURCE[0]:-$0}"      ← ファイルの最上位で捕捉
 _egosurgery_load_env() {
   local root pf
-  root="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
+  root="$(cd "$(dirname "${_egosurgery_env_self}")/.." && pwd)"
 …
 _egosurgery_load_env
+unset _egosurgery_env_self                        ← 呼び出し側の名前空間を汚さない
```

規模: **+10 / −1**（うち 6 行は原因を記した注記）。構文検査は **bash OK / zsh OK**。

### 4-3. G2 — 両方向の実測

| 呼び方 | 結果 |
|---|---|
| zsh / repo 内 | ✅ `WANDB_API_KEY=set / NOTION_API_KEY=set` |
| bash / repo 内 | ✅ 同上 |
| **zsh / repo の外（`cd /tmp`）から絶対パス** | ✅ 同上 |
| **bash / repo の外から絶対パス** | ✅ 同上 |

**repo の外から呼んでも成功する。** SPEC は「成功するか、明確な理由で失敗する」を
期待値としていたが、採用した方法では**失敗させる必要がなかった**。

出力に資格情報の値が含まれないことを目視で確認した。

### 4-4. 陰性対照

修正を対象ファイルだけ一時退避して再測定した。

| 状態 | zsh からの結果 |
|---|---|
| 修正前（`git stash push -- scripts/load_env.sh`） | `[load_env] /home/ubuntu/slocal2/.env.gpg が無い。…` ❌ |
| 復元後 | md5 が修正後と一致。stash の残り **0 件** |

**修正前は確かに失敗する。** この検査は有効である。

### 4-5. 平文と暗号化ファイル

| 検査 | 実測 |
|---|---|
| 作業ツリー | `scripts/load_env.sh` のみ変更 |
| `.env`（平文） | 存在するが**追跡下 0 件**。`.gitignore:79` で無視 |
| `.env.gpg` | **md5 一致・`git diff` 0 行**（不変） |

commit: `bb1f38a fix(scripts): resolve the repo root without depending on the shell`

---

## 5. Phase C — 同型の書き方

### 5-1. 件数と代替の有無

`BASH_SOURCE` を持つ追跡下の `.sh` は **23 本**。

| 分類 | 件数 |
|---|---|
| `${BASH_SOURCE[0]:-$0}` の**代替あり** | **1**（`scripts/load_env.sh`） |
| `${BASH_SOURCE[0]}` のみ（**代替なし**） | **22** |

**代替が無い方が条件は緩い。** zsh で source されると最上位でも空文字列になり、
`dirname ""` = `.` で同じ誤解決を起こす（`load_env.sh` は代替があったため
「関数の内側」という条件が付いていた）。

### 5-2. `source` されるかどうかの判定

repo 全体で `source` / `.` に続く `.sh` を 1 回の走査で集め、**22 行**を目視で確認した。

| 判定 | 件数 | 内訳 |
|---|---|---|
| **`source` される** | **1** | `scripts/load_env.sh`（`.env.example` / `CLAUDE.md` / `README.md` ×2 / `docs/secrets_and_tracking.md` / `src/egosurgery/utils/tracking.py` ×2 / 自身の docstring = 8 箇所で言及） |
| 直接実行される | 22 | 全て `#!/usr/bin/env bash` の shebang を持ち、`Makefile` / 文書 / 他スクリプトから `bash x.sh` 形式で呼ばれる |
| 判別できない | **0** | — |

`scripts/encrypt_env.sh` は `docs/secrets_and_tracking.md:20` に **`bash scripts/encrypt_env.sh`** と
記されており、**実行形式**である。SPEC が条件付きで解禁していたが、**修正は不要だった。**

**22 行のマッチの大半は偽陽性だった。** `2. \`command.sh\`` のような箇条書きが
正規表現の `(.)[[:space:]]+…sh` に一致していた。件数だけを見れば「21 本が source される」と
読めてしまうため、目視で 1 行ずつ確認して確定した。

### 5-3. 修正した件数と、壊れていないことの確認

**修正が必要なものは 0 件**（`scripts/load_env.sh` は Phase B で修正済み）。
解禁されているのは `load_env.sh` と `encrypt_env.sh` のみであり、
判別できた以上、他の 22 本には触れていない。

| 検査 | 実測 |
|---|---|
| `scripts/` 配下の bash 構文検査 | **89 本すべて OK** |
| `load_env.sh` / `encrypt_env.sh` の両シェル構文 | bash OK / zsh OK |

暗号化ファイルの再生成は行っていない。

**残る危険（未対処）**: 直接実行されるスクリプトも、`zsh scripts/run_s0.sh` のように
shebang を上書きして起動すれば同じ誤解決を起こす。文書化された起動方法は
`bash x.sh` であり、現状の運用では発生しない。

---

## 6. Phase D — 外部記録の稼働状況

### 6-1. 資格情報の読み込み（値は出さない）

| 変数 | 状態 |
|---|---|
| `WANDB_API_KEY` | **設定あり** |
| `NOTION_API_KEY` | **設定あり** |
| `NOTION_DB_ID` | 未設定（台帳 ID は `configs/notion.yaml` から取るため影響なし） |

### 6-2. 手元の痕跡（外部への送信とは区別する）

`wandb` ディレクトリは **13 件**。

| 時期 | 件数の目安 |
|---|---|
| 2026-08-07 | 1 件（`s0_040_wiring_verification_seed42`） |
| 2026-05-25 〜 2026-05-28 | 12 件 |

**手元に痕跡があることは、外部へ送信されたことを意味しない。**
実際、2026-08-07 の 1 件は `logging.wandb_enabled=false` で実行した配線確認の run であり、
ディレクトリは作られるが送信は無効化されていた（`T-2026-08-09-run-wiring-verification` の記録）。
**2026-05-28 から 2026-08-07 までの間に新しい痕跡が無い**ことは事実だが、
これが送信の停止を意味するかは本 task では測っていない。

### 6-3. 外部台帳への到達 — **失敗（HTTP 404）**

API の版と台帳 ID の取り方は既存実装に合わせた（`src/egosurgery/utils/notion_logger.py:35`
の `NOTION_VERSION = "2022-06-28"` と一致。台帳 ID は `configs/notion.yaml` の
`databases.run_ledger`）。

```
HTTP 404 {"object":"error","status":404,"code":"object_not_found",
 "message":"Could not find database with ID: … Make sure the relevant pages and
 databases are shared with your integration."}
```

**理由を切り分けた（すべて読み取りのみ）。**

| 検査 | 実測 |
|---|---|
| トークンの有効性（`/v1/users/me`） | **HTTP 200**。種別 `bot` / 名前 **`AutoResearch`** |
| 登録簿の全 10 ID への到達 | **10 件すべて HTTP 404 `object_not_found`**（DB 5 + ページ 5） |
| この統合から見えるもの（`/v1/search`） | **3 件**。いずれも**登録簿に無い** |

見えた 3 件は次のとおり。

| 種別 | 作成 | 備考 |
|---|---|---|
| database | 2026-08-10 | 「TASK配布」 |
| page | 2026-08-10 | 無題 |
| page | 2026-06-01 | 研究運用ハブとは別プロジェクトのページ |

**結論（実測）**: 資格情報は有効だが、**この統合には研究運用ハブの 10 オブジェクトが
共有されていない。** トークンが無効なら 401 が返るところ、404 が返り、かつ
`/v1/users/me` が 200 を返すことがその根拠である。

### 6-4. 版管理の履歴との突き合わせ

| 対象 | 履歴 |
|---|---|
| `scripts/load_env.sh` | `ba3df41` 2026-06-22 → `bb1f38a` 2026-08-10（本 task） |
| `.env.gpg` | `907c8ae` 2026-06-22 → **`7502407` 2026-08-10T08:57:59「notion_api_key add」** |
| 索引の外部記録の列 | 全 **751 行中 0 行**が埋まっている |

### 6-5. G3 — 停止期間: **UNKNOWN**

**外部台帳の直近の投稿時刻は測定できなかった。** したがって
「いつから止まっていたか」は **`UNKNOWN`** である。

`.env.gpg` が 2026-08-10T08:57 に更新された事実はあるが、**それが停止の原因かは
測っていない。** 旧資格情報での到達可否を測れば確定できる可能性があるが、
利用者の判断により**本 task では行わず、`UNKNOWN` と記録する**こととした。

**状況証拠からの推測は書かない。**

---

## 7. 完了判定

| # | 判定 | 期待 | 実測 |
|---|---|---|---|
| 1 | 誤解決を再現した | 両方向の対照が働いた | ✅ zsh 失敗 / bash 成功 |
| 2 | 基点の実測値を得た | 値が記録されている | ✅ §3-3 の 4 通り |
| 3 | 既定のシェルで読み込める | 成功 | ✅ |
| 4 | 別のシェルでも読み込める | 成功 | ✅ |
| 5 | 修正前は失敗する | 陰性対照が働く | ✅ |
| 6 | 同型の書き方を調査した | 件数と判定が記録されている | ✅ 23 本 / source 1・実行 22・判別不能 0 |
| 7 | 直接実行が壊れていない | 構文検査が通る | ✅ 89 本すべて OK |
| 8 | **資格情報の値が出ていない** | 目視確認済み | ✅ 有無のみ |
| 9 | 暗号化ファイルが不変 | `git diff` が空 | ✅ md5 一致 / 0 行 |
| 10 | 平文が版管理外 | 追跡されていない | ✅ 0 件 |
| 11 | 外部台帳の直近の投稿を測った | 記録あり、または `UNKNOWN` | ✅ **`UNKNOWN`**（理由は実測） |
| 12 | 契約検証が通る | exit 0 | ✅（WARN 2 件は L2-8 の分母変動） |
| 13 | 実行前検査が通る | exit 0 | ✅ 4 PASS / 4 SKIP / 0 FAIL |
| 14 | 試験が不変 | 開始前と比較 | ✅ **前 5 failed, 264 passed → 後 5 failed, 264 passed**。失敗テスト名も同一 |
| 15 | 禁止領域が無変更 | 出力なし | ✅ 出力なし |

**判定14 の基準点（本 task 開始前・2026-08-10 09:31 実測）**

```
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
5 failed, 264 passed, 22 warnings in 28.75s
```

### preflight で SKIP された項目（合格ではない）

| 項目 | 理由 |
|---|---|
| `P2 cuda_ext_loaded` | `plan.env.preflight` に記載なし → **未実施** |
| `P3 deterministic_flags` | `plan.env.preflight` に記載なし → 未実施 |
| `P4 prereg_committed` | `kind=impl` のため対象外 |
| `P5 frozen_source_hash` | `kind=impl` のため対象外 |

---

## 8. deviations（指示書どおりにしなかった箇所）

### D-1. SPEC が推奨した方法を採らなかった

- **指示:** Phase B Step 1「**3 番目を推奨する**が、次の点を実測してから決める」
- **実際:** 一覧に無い 4 番目（最上位で捕捉して関数へ渡す）を採った。
- **理由:** §4-1 の実測。候補 3 は repo の外から呼ぶと `fatal: not a git repository`（exit 128）で
  失敗するが、候補 4 は両シェル・repo 内外の 4 ケースすべてで正しい経路を返した。
  SPEC 自身が「実測してから決める」「推奨されたからではなく実測に基づく理由を書く」と
  定めており、その指示に従った結果である。
- **分類:** **判断が必要だった**

### D-2. SPEC の探査が原因を捉えられない位置で測っていた

- **指示:** Phase A Step 3 の `probe_root.sh` は `$0` を**ファイルの最上位**で測る
- **実際:** 実際の該当行は**関数の内側**にある。最上位では zsh も正しく解決するため
  （実測: `$0=/tmp/probe_root.sh`）、**SPEC の探査だけでは原因が見えなかった。**
  関数の内側で測る探査を追加し、`$0=_probe_fn` / 基点 `/home/ubuntu/slocal2` を得た。
- **分類:** **SPEC の欠陥**

### D-3. 表示用のパイプが環境変数の読み込みを壊した

- **指示:** Phase D Step 1 は `source scripts/load_env.sh`（パイプ無し）
- **実際:** 表示のために `| tail -1` を足した結果、`source` が subshell で実行され、
  export が親シェルへ届かなかった。**`load_env.sh` 自身は subshell 内で正常に動き
  `set / set` と出力するのに、親では未設定**という紛らわしい状態になった。
  パイプを外して測り直した。
- **重大さ:** 出力だけを見ていたら「読み込めている」と誤判定していた。
  SPEC の申し送り「記録を作る流れに表示用の切り詰めを混ぜない」と同型の誤りである。
- **分類:** **判断が必要だった**（自分で気付いて正した）

### D-4. `source` 検索の正規表現が箇条書きに偽陽性を出した

- **実際:** `(source|\.)[[:space:]]+…\.sh` が `2. \`command.sh\`` のような箇条書きに一致し、
  22 行のマッチのうち大半が偽陽性だった。**件数だけを見れば「21 本が source される」と
  読めてしまう。** 22 行を目視で 1 行ずつ確認して 1 本と確定した。
- **注記:** 過剰に拾う方向の誤りであり、取りこぼしよりは安全側である。
- **分類:** **判断が必要だった**

### D-5. 走査コマンドが時間切れになった

- **実際:** ファイルごとに `git grep` を回す構成にしたため 2 分で打ち切られ、
  部分結果しか得られなかった。1 回の走査で全件を集める構成に変えて測り直した。
- **注記:** 部分結果のまま判定していたら、後半のファイルを未検査のまま
  「source されない」と結論するところだった。
- **分類:** **判断が必要だった**

### D-6. 試験結果を書き込み完了前に読んだ

- **実際:** 判定14 の比較を、背景で走らせた `pytest` の出力が書き終わる前に実行し、
  `FAILED` が 0 行に見えた。ファイルの状態を確認して測り直し、
  **`5 failed, 264 passed`（不変）**を得た。
- **重大さ:** そのまま報告していたら「試験が全て通るようになった」と誤報告していた。
- **分類:** **判断が必要だった**（自分で気付いて正した）

### D-7. Phase C で commit を作らなかった

- **指示:** Phase C Step 5「commit」
- **実際:** 修正が必要なものが **0 件**だったため、commit する変更が無かった。
- **分類:** 手順どおり（該当なし）

### D-8. `conventions_rev` を実測値へ置換した

- **指示:** SPEC Task 5 Step 1 が「実行者が実測して置換する。**これは逸脱ではなく手順である**」と明記
- **実際:** `1201f4f` → `d422b08` に更新した
- **分類:** 手順どおり（記録のため列挙）

---

## 9. 未解決・申し送り

### 9-1. 他ホストへの展開は別作業である

**本 task が直したのは lecun の作業ツリーにある `scripts/load_env.sh` である。**
他の 9 台へは、この変更が統合され、各ホストが取り込んで初めて届く。

**他ホストで対話シェルからの読み込みが成立するかは未検証である。**
統合後に各台で次を確認する必要がある。

    zsh -ic 'cd <repo>; source scripts/load_env.sh'

なお修正前でも**別のシェル経由なら全 10 台で成功していた**（SPEC の前提として記載）。
したがって本 task の修正は「対話シェルからも使えるようにする」ものであり、
**資格情報が全く入らない状態を解消するものではない。**

### 9-2. 外部台帳の共有範囲（利用者の操作領域）

§6-3 のとおり、資格情報は有効だが**研究運用ハブの 10 オブジェクトがこの統合に
共有されていない。** 統合の名前は `AutoResearch` で、見えるのは別の 3 オブジェクトである。

Notion 側の共有設定は**利用者の操作領域**であり、本 task では変更していない
（禁止事項 8「外部の記録先へ書き込む」に該当するため）。

**共有が復旧するまで、実験台帳への自動投稿は届かない。** ただし
`notion_logger` は資格情報が無ければ no-op の設計であり、**学習は止まらない。**

### 9-3. 停止期間が `UNKNOWN` のまま

§6-5 のとおり。旧資格情報での到達可否を測れば確定できる可能性があるが、
本 task では行っていない。確定させる場合は、過去の資格情報を扱う別契約が要る。

### 9-4. 索引の外部記録の列は依然として全行が空

751 行中 0 行。今後の run で埋まるかは、W&B 側の送信が成立するかに依存する。
**W&B への送信が実際に届いているかは本 task では測っていない**
（測ったのは Notion 台帳のみ）。

### 9-5. shebang を上書きした起動は未対処

直接実行される 22 本も `zsh scripts/run_s0.sh` のように起動すれば同じ誤解決を起こす。
文書化された起動方法は `bash x.sh` であり現状は発生しないが、
**解禁範囲外のため触れていない。**

---

## 10. 数値の出所

**すべての数値は本ホスト（lecun）での実測である。**
測定できなかった項目（外部台帳の直近の投稿時刻、停止期間、他ホストでの動作、
W&B 送信の到達）は **`UNKNOWN` または未検証と明記**しており、推測で補っていない。
**資格情報の値は出力にも記録にも含まれていない。** 扱ったのは有無だけである。
