# RESULT — T-2026-08-12-contract-distribution-via-notion

**実行者:** `lecun` / `feat/notion-distribution` / `origin/phase0` の `dc13196` から分岐
**実行日時:** 2026-08-10T13:49Z 〜 2026-08-10T14:05Z
**判定:** **G1 不成立で停止（`ledger_unreachable`）** — 配布台帳へ到達できなかった。
**Phase B / C / D は未着手。コードは 1 行も変更していない。**

| 受入基準 | 結果 |
|---|---|
| 実行ホストの資格情報で台帳を照会できる | ❌ **HTTP 404**。共有されていない |
| 書き込みと読み戻しで内容が変わらないことが要約値で確認されている | **未検証**（Phase B へ到達せず） |
| 識別子だけを与えて契約を取り込める | **未着手**（Phase C） |
| 取り込みに失敗した場合に作業領域へ痕跡が残らない | **未着手**（Phase C） |
| 手元に契約が無いとき自動で取得する経路が手順書に書かれている | **未着手**（Phase D） |
| 資格情報が出力にも記録にも含まれない | ✅ 有無のみ扱った |
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

`1201f4f` → `d422b08` は **+10 / −0**。差分ハンクは L56（`frozen_source` 節）と L143（変更履歴）の 2 箇所。
**原文注入する `prohibitions`（L98–108）は無変更。**

---

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（after A） | **不成立 → 停止** | 台帳へ HTTP 404。`ledger_unreachable` |
| G2（after B） | **未評価** | Phase B へ到達せず |
| G3（after C） | **未評価** | Phase C へ到達せず |

---

## 3. Phase A — 到達性の確認

### 3-1. 既存実装から取った値（推測していない）

| 項目 | 値 | 出所 |
|---|---|---|
| API の版 | `2022-06-28` | `src/egosurgery/utils/notion_logger.py:35` の `NOTION_VERSION` |
| 基底 URL | `https://api.notion.com/v1` | 同 `:36` の `_API_BASE` |
| 見出しの作り方 | `Authorization: Bearer …` / `Notion-Version` / `Content-Type` | `notion_ops.py` の `_headers()` |

SPEC が「推定であり、食い違えば実装に従う」とした版は、**実装と一致していた。**

### 3-2. 資格情報

| 項目 | 実測 |
|---|---|
| `NOTION_API_KEY` | **設定あり** |
| 統合の素性（`/v1/users/me`） | **HTTP 200** / 種別 `bot` / 名前 **`AutoResearch`** |

**資格情報は有効である。** 値・長さともに出力していない（§7 D-1）。

### 3-3. 台帳への到達 — すべて HTTP 404

| 照会 | API の版 | 結果 |
|---|---|---|
| `databases/3af70553-8f2d-45de-972a-c64b3127bb1a`（SPEC の database id） | 2022-06-28 | **404 `object_not_found`** |
| `databases/{DB}/query` | 2022-06-28 | **404** |
| `databases/b6ae4844-d6b8-433f-a07a-3882a534c9eb`（SPEC の data source id） | 2022-06-28 | **404** |
| `data_sources/{DS}` | 2025-09-03 | **404** |
| `databases/{DB}` | 2025-09-03 | **404** |

応答本文は一貫して
`"Make sure the relevant pages and databases are shared with your integration."` である。

### 3-4. 統合から見えるものの実測

| 照会 | 結果 |
|---|---|
| `/v1/search`（`page_size` 10） | **1 件** / `has_more: false` |
| `/v1/search`（`page_size` 100・filter 無し） | **1 件**（研究とは別プロジェクトのページ 1 件のみ） |
| `/v1/search`（`filter: object=database`） | **database 0 件** |

**この統合から見える database は 1 件も無い。**

### 3-5. 数時間前との差（事実のみ）

先行する契約 `T-2026-08-12-env-loader-shell-portability` の実行中（本日 09:45 頃）、
同じ統合の `/v1/search` は **3 件**を返し、その中に **database「TASK配布」（2026-08-10 作成）**が
含まれていた。

**ただし当時その database の id は記録していない。** したがって
「SPEC が指す database と同一の物が見えなくなった」とは**断定できない**。

言えるのは次の 2 点だけである。

1. 本日 09:45 頃、この統合から「TASK配布」という名前の database が見えていた。
2. 本日 13:55 現在、この統合から見える database は **0 件**であり、
   SPEC の 2 つの識別子はいずれも 404 を返す。

**何が起きたかは `UNKNOWN` である。** 状況証拠から推測を書かない。

### 3-6. 検索インデックスの遅延では説明できない

`/v1/search` は結果整合であり得るが、**`/v1/databases/{id}` の直接照会も 404** である。
直接照会は検索インデックスに依存しない。したがって遅延では説明がつかない。

また 401 ではなく 404 であり、`/v1/users/me` が 200 を返すことから、
**資格情報の無効化ではなく共有範囲の問題**である。

---

## 4. 利用者へのお願い（SPEC が報告へ含めるよう定めているもの）

Notion で **統合 `AutoResearch`** に、次を「接続」から追加してください。

| 対象 | 識別子 |
|---|---|
| database **「TASK配布」** | `3af70553-8f2d-45de-972a-c64b3127bb1a` |
| 親ページ **「M2研究運用ハブ」**（配下へ継承される） | `36bee4d4-7777-819c-8495-e48d1a71e500` |

手順: 対象を開く → 右上の `⋯` → **接続**（Connections）→ `AutoResearch` を追加。

**親ページを接続すれば配下へ継承される。** なお運用ハブ配下の登録簿 10 件は、
先行契約の実測でも全て 404 だった（`T-2026-08-12-env-loader-shell-portability` §6-3）。
**同じ操作で両方が解決する可能性がある。**

追加後は本契約の Phase A を再実行すれば到達性を確認できる。
`make task-notion` は Phase C が未着手のため**まだ存在しない。**

---

## 5. 未着手のまま残したもの

**G1 が `on_fail: stop` であるため、以降のフェーズには入っていない。**

| Phase | 内容 | 状態 |
|---|---|---|
| B | 往復の忠実性の検証 | **未着手。** 台帳へ書き込めないため検証できない |
| C | `tools/fetch_task.py --notion` の実装 | **未着手** |
| D | 手順書への組み込み | **未着手** |

`configs/notion.yaml` への配布先の追記（Phase C Step 1）も**行っていない。**
往復の忠実性（G2）が未検証のまま登録簿へ載せると、
**検証されていない経路を正式なものとして記録することになる**ためである。

**コードは 1 行も変更していない。** 作業ツリーの変更は本契約のディレクトリのみである。

---

## 6. 貼り付けによる配布を残すかどうかの所見

**当面は残すべきである。** 理由は 2 つ。

1. **台帳経由の経路はまだ 1 度も成立していない。** 到達性（G1）が確認できておらず、
   往復の忠実性（G2）に至っては測ってすらいない。
   SPEC 自身が「Phase B が通らなければ、この経路は使えない。その場合は素直に停止し、
   貼り付けによる配布を続ける」と定めている。
2. **共有設定は利用者の操作領域であり、実行側から復旧できない。**
   共有が外れれば経路は即座に使えなくなる。実際、本日 09:45 に見えていたものが
   13:55 には見えなくなっている（§3-5）。**単一の経路に寄せると、この種の変化で
   契約の受け渡し自体が止まる。**

貼り付けは端末が必要という制約はあるが、**外部サービスの状態に依存しない**という
強みがある。台帳経由が Phase B まで通ってから、主経路を切り替えるかを判断するのが妥当である。

---

## 7. deviations（指示書どおりにしなかった箇所）

### D-1. 資格情報の長さを出力しなかった

- **指示:** Phase A Step 2 は `print("NOTION_API_KEY:", …, f"(長さ {len(k)})" if k else "")`
- **実際:** **長さを出力しなかった。** 有無のみを出した。
- **理由:** 禁止事項 1 は「資格情報を出力・記録する（**存在と有無のみ**扱う）」と定める。
  長さは有無を超える情報であり、禁止事項の方が具体的である。
- **分類:** **SPEC の欠陥**（本文と検査コマンドが食い違っている）

### D-2. SPEC の探査が database id しか試していなかった

- **指示:** Phase A Step 3 の探査は `databases/{DB}` と `databases/{DB}/query` のみ
- **実際:** SPEC は **data source id も明示している**のに、探査はそれを使っていない。
  data source id での照会と、新しい API 版（`2025-09-03`）での `data_sources/{DS}` も試した。
  **いずれも 404** であり、結論は変わらなかったが、試さなければ
  「識別子の指定が違うだけかもしれない」という可能性を潰せなかった。
- **分類:** **SPEC の欠陥**

### D-3. 「共有されていない」と断定する前に別の測り方で照合した

- **指示:** G1 の判定表は「HTTP 404 → 台帳が Integration へ共有されていない」と直結する
- **実際:** 先行契約で「TASK配布 が見えていた」という実測があり、404 と矛盾する。
  `/v1/search`（3 通りの条件）と `/v1/users/me` を追加で測り、
  **「database が 1 件も見えない」「資格情報は有効」**を確かめてから結論を出した。
- **理由:** 申し送りの「一致件数が 0 のとき、別の探し方でも 0 になることを確かめる」。
  404 だけを見て報告していたら、前回の実測との矛盾に気付けなかった。
- **分類:** **判断が必要だった**

### D-4. 停止後に記録を残して起票した

- **指示:** G1 は `on_fail: stop`。SPEC は停止後の記録・起票の手順を定めていない
- **実際:** 利用者へ提示し、**停止の記録を RESULT へ残して PR にする**判断を得た。
  コードは変更していないため、PR に含まれるのは契約と記録のみである。
- **分類:** **判断が必要だった**

### D-5. commit と PR の題を実態に合わせた

- **指示:** Phase D Task 5 Step 5 は
  commit `feat(tasks): distribute contracts through the shared ledger` /
  PR `feat(tasks): fetch contracts from the distribution ledger by task_id`
- **実際:** **実装は 1 行も行っていない**ため、この題では
  「機能が入った」という誤った記録になる。実態に合う題へ変えた。
- **分類:** **判断が必要だった**（SPEC は完走を前提に題を書いており、停止時の題を定めていない）

### D-6. `conventions_rev` を実測値へ置換した

- **指示:** SPEC Task 5 Step 1 が「実行者が実測して置換する。**これは逸脱ではなく手順である**」と明記
- **実際:** `1201f4f` → `d422b08` に更新した
- **分類:** 手順どおり（記録のため列挙）

---

## 8. 完了判定（到達した範囲のみ）

| # | 判定 | 期待 | 実測 |
|---|---|---|---|
| 1 | 台帳へ到達できる | HTTP 200 | ❌ **404**（5 通りの照会すべて） |
| 2–9 | 往復・取り込み・巻き戻し | — | **未評価**（Phase B/C へ到達せず） |
| 10 | 資格情報が出力に無い | 検査で 0 件 | ✅ 有無のみ。値も長さも出していない |
| 11 | 手順書が新しい経路を指す | 該当あり | **未着手**（Phase D） |
| 12 | 登録簿に配布先がある | 1 件 | **未着手**（§5 の理由により意図的） |
| 13 | 契約検証が通る | exit 0 | ✅ exit 0（WARN 2 件は L2-8 の分母変動） |
| 14 | 実行前検査が通る | exit 0 | ✅ 4 PASS / 4 SKIP / 0 FAIL |
| 15 | 試験が不変 | 開始前と比較 | ✅ **前 5 failed, 264 passed → 後 同一**。失敗テスト名も同一 |
| 16 | 禁止領域が無変更 | 出力なし | ✅ 出力なし |

**判定15 の基準点（本 task 開始前・2026-08-10 13:50 実測）**

```
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
5 failed, 264 passed, 22 warnings in 25.90s
```

コードを変更していないため、試験が動く余地は無い。実測でも不変である。

### preflight で SKIP された項目（合格ではない）

| 項目 | 理由 |
|---|---|
| `P2 cuda_ext_loaded` | `plan.env.preflight` に記載なし → **未実施** |
| `P3 deterministic_flags` | `plan.env.preflight` に記載なし → 未実施 |
| `P4 prereg_committed` | `kind=impl` のため対象外 |
| `P5 frozen_source_hash` | `kind=impl` のため対象外 |

---

## 9. 未解決・申し送り

### 9-1. 共有が復旧したら本契約を再実行できる

コードを変更していないため、**同じ契約をそのまま再実行すればよい。**
Phase A から順に進み、G1 が 200 になれば Phase B 以降へ入れる。

### 9-2. 見え方が数時間で変わった原因は `UNKNOWN`

§3-5 のとおり。前回 database の id を記録していなかったため、
同一物の可視性が変わったのかを確かめられない。
**今後は見えたオブジェクトの id も記録する**ことで、次回は切り分けられる。

### 9-3. 研究運用ハブの登録簿 10 件も 404 のまま

先行契約 `T-2026-08-12-env-loader-shell-portability` §6-3 の実測。
親ページを接続すれば配下へ継承されるため、**同じ操作で両方が解決する可能性がある**が、
**継承の有無は測っていない。**

### 9-4. 配布経路を単一化する危険

§6 のとおり。共有設定は実行側から復旧できず、実際に数時間で状態が変わった。
**主経路を台帳へ寄せる判断は、Phase B が通ってからにすべきである。**

---

## 10. 数値の出所

**すべての数値は本ホスト（lecun）での実測である。**
測定できなかった項目（往復の忠実性、取り込み経路の動作、可視性が変わった原因、
親ページ接続の継承）は **未評価または `UNKNOWN` と明記**しており、推測で補っていない。
**資格情報は値も長さも出力していない。** 扱ったのは有無だけである。
