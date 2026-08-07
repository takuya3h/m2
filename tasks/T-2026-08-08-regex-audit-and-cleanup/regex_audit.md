# 終端一致の棚卸し（2026-08-08）

実測ホスト: `ilya`（`hostname` は `aolab`）
対象: 契約検証系（`tools/validate_task.py` / `tools/preflight_task.py` /
`tools/build_context.py` / `tools/fetch_task.py` / `tasks/_schema/spec.schema.json`）

## 前提: どの書き方が危ないかを先に実測した

推測を避けるため、書き方の組み合わせごとに末尾改行の通過可否を測った。

| payload | `$` + `match` | `$` + `fullmatch` | `\Z` + `match` | `\Z` + `fullmatch` | JSON Schema `pattern` |
|---|---|---|---|---|---|
| 正常 | True | True | True | True | True |
| **末尾に改行 1 つ** | **True** | False | False | False | **True** |
| 中間に改行 + 後続文字 | False | False | False | False | False |
| 末尾に改行 2 つ | False | False | False | False | False |
| 末尾にキャリッジリターン | False | False | False | False | False |
| 末尾に空白 | False | False | False | False | False |

**危ないのは `$` + `match` と JSON Schema の `pattern` の 2 つだけである。**
`fullmatch` は `$` を使っていても文字列の真の末尾で固定されるため安全であった。
JSON Schema が危ないのは、`jsonschema` が `pattern` を Python の `re` で解釈するため、
ECMA-262 ではなく Python の `$` の意味論（末尾改行の直前にも一致する）が適用されるからである。

> **注意: 中間改行の payload では脆弱性を検出できない。**
> SPEC の Task 1 Step 3 が例示する `"T-2026-08-08-evil\nrm -rf /"` は改行の**後ろに文字がある**ため、
> `$` でも一致しない。この payload だけで測ると「安全」という誤った結論になる。
> 実際に悪用できるのは**末尾改行**であり、前 task で `fetch_task.py` に見つかったのもこの形である。
> 本棚卸しは両方を測った。

## 検証系の正規表現一覧

| ファイル | 定数名 | パターン | 呼び出し | 終端 | 末尾改行 | 判定 |
|---|---|---|---|---|---|---|
| `tools/validate_task.py:48` | `_PIPE_STRICT_PATHS[0]` | `^meta\.title$` | `match` | `$` | 通る | 影響なし（後述） |
| `tools/validate_task.py:49` | `_PIPE_STRICT_PATHS[1]` | `^intent\.(question…)$` | `match` | `$` | 通る | 影響なし |
| `tools/validate_task.py:50` | `_PIPE_STRICT_PATHS[2]` | `^plan\.phases\.\d+\.name$` | `match` | `$` | 通る | 影響なし |
| `tools/validate_task.py:51` | `_PIPE_STRICT_PATHS[3]` | `^plan\.gates\.\d+\.check$` | `match` | `$` | 通る | 影響なし |
| `tools/validate_task.py:52` | `_PIPE_STRICT_PATHS[4]` | `^outputs\.acceptance\.\d+$` | `match` | `$` | 通る | 影響なし |
| `tools/validate_task.py:119` | 無名 | `exp:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+` | `fullmatch` | なし | 拒否 | 安全 |
| `tools/validate_task.py:126` | 無名 | `run:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+` | `fullmatch` | なし | 拒否 | 安全 |
| `tools/validate_task.py:32` | `_ANCHOR_RE` | `<a id="([a-z0-9_]+)"></a>` | `findall` | なし | 該当なし | 抽出用。門番ではない |
| `tools/validate_task.py:37` | `_NUMBER_RE` | `(?<!…)(\d+\.\d+\|\d{4,})(?!…)` | `search` | なし | 該当なし | 検出用。部分一致が目的 |
| `tools/fetch_task.py:41` | `_DELIM_RE` | `^[A-Za-z0-9_-]+$` | `match` | `$` | 通る | 要修正（後述） |
| `tools/fetch_task.py:43` | `_HEADER_RE` | `…delim=(?P<delim>\S+)\s*$` | `match` | `$` | 到達不能 | 要修正（予防） |
| `tools/fetch_task.py:52` | `_TASK_ID_RE` | `^T-\d{4}-\d{2}-\d{2}-[a-z0-9-]+\Z` | `match` | `\Z` | 拒否 | 前 task で修正済み |
| `tools/fetch_task.py:53` | `_URL_RE` | `^https?://` | `match` | なし | 該当なし | 接頭辞判定が目的 |
| `tools/build_context.py:45` | `_BACKLOG_ID_RE` | `^\|\s*(~~)?(BL-…)` | `match` | なし | 該当なし | 接頭辞判定が目的 |
| `tools/preflight_task.py:113,117,118` | 無名 | 節・SHA・パスの抽出 | `search` | — | 該当なし | 抽出用。門番ではない |

`_PIPE_STRICT_PATHS` を「影響なし」とした理由。これらは**契約の入力値ではなく、
`_walk_strings` が組み立てた内部の経路文字列**に対して照合する。かつ、末尾改行が
通ることで判定は「厳格側」に倒れる（半角パイプの検出が WARN ではなく FAIL になる）。
攻撃者が厳格判定を**回避する**方向には使えない。ただし書き方としては同型なので統一する。

`tools/harvest_runindex.py` にも `$` 終端が 3 件あるが（`RUN_NAME_RE` 等）、
**本 task の禁止事項 3 により変更しない。** これらはディスク上のディレクトリ名を解析するもので、
契約検証の門番ではない。棚卸しの対象外として記録する。

## JSON Schema 側

`jsonschema` は `pattern` を Python の `re` で解釈するため、**4 件すべてが末尾改行を通す。**

| 場所 | パターン | 正常 | 末尾改行 | Python 側の二重防御 | 総合判定 |
|---|---|---|---|---|---|
| `spec.schema.json:15` `meta.task_id` | `^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,60}$` | True | **True** | **無し** | 🔴 **悪用可能** |
| `spec.schema.json:86` `inputs.denominator.ref` | `^exp:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$` | True | True | あり（L1-4 の `fullmatch`） | 塞がっている |
| `spec.schema.json:113` `inputs.frozen_source.ref` | `^run:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$` | True | True | あり（L1-4 の `fullmatch`） | 塞がっている |
| `spec.schema.json:145` `contract.inject_verbatim` | `^conventions#[a-z0-9_]+$` | True | True | あり（L2-5 のアンカー照合） | 塞がっている |

二重防御は実測で確認した。

    denominator.ref  末尾改行 -> [L1-4] inputs.denominator.ref: exp:<group>/<experiment_id> の形式が必要です
    frozen_source.ref 末尾改行 -> [L1-4] inputs.frozen_source.ref: run:<group>/<run_name> の形式が必要です
    inject_verbatim  末尾改行 -> L1 は素通り。L2 で [L2-5] アンカー split（改行つき）が存在しません

`meta.task_id` だけは Python 側に対応する正規表現が存在せず、**Schema が唯一の門番**である。
L1-2 は `task_id != dir_name` の文字列比較であり、両方に同じ改行が入っていれば一致してしまう。

## 実際の検証系への攻撃入力

`validate_l1` に契約を丸ごと通した実測（生の出力）。

    SPEC の payload（中間改行）: hard findings = ["[L1-1] meta.task_id: 'T-2026-08-08-evil\\nmalicious' does not match '^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,60}$'"]
    末尾改行（実際の悪用形）: hard findings = なし（=素通り）

**`task_id` の末尾に改行を付けた契約は、`validate_l1` を hard finding ゼロで通過する。**

## 結論

| 項目 | 実測 |
|---|---|
| 棚卸しした正規表現 | Python 側 15 箇所 + JSON Schema 側 4 箇所 |
| 末尾改行が通る箇所 | Python 側 7 箇所（うち `_PIPE_STRICT_PATHS` 5 + `fetch_task` 2）、JSON Schema 側 4 箇所 |
| **実際に悪用可能な箇所** | **1 箇所。`spec.schema.json:15` の `meta.task_id`** |
| 影響範囲 | 改行入り `task_id` を持つ契約が L1 を通過する。前 task で `fetch_task.py` を修正済みのため、`make task-fetch` 経由では取り込めない。ただし `tasks/` へ直接置かれた契約は `make task-validate` を通過する |
| これまでの検証結果への影響 | **無い。実測で確認した。** 既存 7 契約すべての `spec.yaml` から `meta.task_id` を読み出し、`re.fullmatch(r"T-\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,60}")`（改行を許さない形）で照合したところ、**改行等を含むものは 0 件**であった |

`escalate_if: additional_bypass_found` に該当するため、件数と場所を隠さず記録した。
G1 の判定は「悪用可能な箇所がある」であり、SPEC の指示どおり停止せず Phase B へ進む。
