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

**この表は Phase A 時点、すなわち修正前の状態を記録したものである。**
Phase B で `$` を `\Z` へ、`match` を `fullmatch` へ統一し、JSON Schema の 4 パターンには
否定先読みを入れた。現在のコードはこの表とは異なる。

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
| `tools/validate_task.py:37` | `_NUMBER_RE` | 小数または 4 桁以上の数値を選択で拾う。前後は否定先読み | `search` | なし | 該当なし | 検出用。部分一致が目的 |
| `tools/fetch_task.py:41` | `_DELIM_RE` | `^[A-Za-z0-9_-]+$` | `match` | `$` | 通る | 要修正（後述） |
| `tools/fetch_task.py:43` | `_HEADER_RE` | `…delim=(?P<delim>\S+)\s*$` | `match` | `$` | 到達不能 | 要修正（予防） |
| `tools/fetch_task.py:52` | `_TASK_ID_RE` | `^T-\d{4}-\d{2}-\d{2}-[a-z0-9-]+\Z` | `match` | `\Z` | 拒否 | 前 task で修正済み |
| `tools/fetch_task.py:53` | `_URL_RE` | `^https?://` | `match` | なし | 該当なし | 接頭辞判定が目的 |
| `tools/build_context.py:45` | `_BACKLOG_ID_RE` | 行頭の表区切りに続く `BL-` 識別子 | `match` | なし | 該当なし | 接頭辞判定が目的 |
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

---

# 凍結源の取り違えで除外された run（2026-08-08）

## 実列名の確認（推測せず実測）

`runindex/index.csv` の除外関連の列は **`excluded` と `exclusion_reason` の 2 つ**。
前 task（`pth_inventory.md`）の記録と食い違いは無かった。

## 除外された run

`exclusion_reason == "wrong_frozen_source"` は **3 件**。いずれも `host = philip`。

| ledger_key | config の凍結源記載 | 対応する候補 | 正本と一致するか |
|---|---|---|---|
| `phase1__s4_phase_baseline_010_frozen_tecno_phase_baseline_aligndetr_seed42` | `detector: align_detr` / `seed: 42` / `backbone: resnet50` / `cache_dir: data/processed/stage1_features/aligndetr_seed42` | **UNKNOWN**（理由は下記） | **一致しない** |
| `phase1__s4_phase_baseline_011_frozen_tecno_phase_baseline_aligndetr_seed123` | 同上（3 run とも同一の記載） | **UNKNOWN** | **一致しない** |
| `phase1__s4_phase_baseline_012_frozen_tecno_phase_baseline_aligndetr_seed456` | 同上 | **UNKNOWN** | **一致しない** |

`index.csv` の `frozen_source_tag` も 3 件とも `aligndetr_seed42` であった。

## 除外理由は特定できた

`config.yaml` が指す凍結源は checkpoint ファイルではなく**特徴キャッシュのディレクトリ**である。
そのキャッシュの素性は、破棄記録
`evidence/discarded_caches/stage1_features/aligndetr_seed42.discarded_20260705.md` に残っていた。

- 2026-07-03 15:55 に AlignDETR-S0-frozen seed42 の学習を開始したが、16:25 に NCCL ALLREDUCE
  タイムアウト（`SeqNum=1`）で失敗し、1 step も進んでいない。
- 17:08 の `entry5.sh` が S0-frozen ckpt の代わりに **2026-05-31 の通常学習 AlignDETR ckpt**
  （`/tmp/aligndetr_work_seed42/model_final.pth`）で特徴抽出を実行した。
- その特徴を使って 17:20-17:21 に TeCNO 3 seed 学習が走った。それが上記 3 run である。

すなわち除外理由は「**宣言している S0-frozen 条件で走っていない**」であり、
数値記録そのものが壊れているわけではない。キャッシュ自体も抽出は完走している。

## 4 候補との対応が UNKNOWN である理由

前 task の `pth_inventory.md` は「サイズが正本と同じ 195421066 バイトだが SHA-256 が異なる」
紛らわしい候補を挙げている。この 3 run との対応は、次の 2 点により**本 task でも特定できない**。

| # | 障害 | 実測 |
|---|---|---|
| 1 | 実際に使われた checkpoint が現存しない | `/tmp/aligndetr_work_seed42/model_final.pth` は存在しない（`/tmp` は揮発する）。`evidence/aligndetr_s0frozen_incident_20260703/` に保全されているのは実行痕跡（ログ・スクリプト・合計 788KB）のみで、checkpoint 本体は含まれない |
| 2 | 証跡に checkpoint のハッシュもサイズも記録が無い | `evidence/aligndetr_s0frozen_incident_20260703/` の全ログと `entry5.sh` を検索したが、記録されているのはパス `CKPT=/tmp/aligndetr_work_seed42/model_final.pth` だけで、SHA-256 もバイト数も残っていない |

加えて、候補側の 4 件（`experiments/detector_improve/augstrong_*/best_ap.pth` と
`third_party/Relation-DETR/.../train/2026-05-30-04_24_20/best_ap.pth`）は
**`config.yaml` を持たない**ため、どの detector で学習されたものかを実測で確認できない。
パス上は Relation-DETR 系だが、これは名前からの推定にすぎないため断定しない。

**したがって「どの候補か」は UNKNOWN と記録する。推測で対応づけない。**

## 正本と一致しないことは確定している

対応先が UNKNOWN であることと、正本と一致しないことは別である。後者は確定している。

- 正本は Relation-DETR seed42 の S0 完走 checkpoint（SHA-256 `03936318…e824`）。
- 3 run が依拠したのは **AlignDETR** の、しかも **S0-frozen ではない** 2026-05-31 の通常学習
  checkpoint から作られた特徴である。
- 検出器の系統も学習条件も異なるため、正本と一致する余地は無い。

この結論は破棄記録の一次証跡に基づくもので、ハッシュ照合を要しない。

## 残る未解決

実際に使われた checkpoint を同定するには、`philip` 上に当時の `/tmp` が残っているか、
あるいは 2026-05-31 の AlignDETR 通常学習の成果物が別の場所に保存されているかを
確認する必要がある。**本 task の実測ホストからは philip へ到達できないため未実施。**
backlog B-25 および B-27 の管轄として残す。
