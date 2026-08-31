# audit — T-2026-08-31-notion-legacy-toc-and-export

実行ホスト `lecun` / repo `/home/ubuntu/slocal/m2` / 分岐 `feat/notion-legacy-toc-and-export`。
**読み取り専用。** Notion へ書いていない。GPU 未使用。

---

## 1. Task A-1 退避した未追跡（開始前から在ったもの）

退避先は `/tmp/claude-1000/.../scratchpad/parked/`。**消していない。**

| 対象 | 由来 | 扱い |
|---|---|---|
| `.sync-pause.released` | 前契約の抑止解除の残骸 | 退避（同期対象外なので他ホストに影響しない） |
| `experiments/analysis/hts_candidate_acceptance/*.py` 4 件 | 別契約 `T-2026-08-30-hts-candidate-acceptance` の成果が同期で配布されたもの | 退避。**`origin/phase0` に同一内容で commit 済み**（4/4 バイト一致）を確認したうえで動かした。phase0 へ切り替えると版管理側の正本が復元された |

🔴 **`.stignore:51` に `!experiments/**/*.py` があり、これらは同期対象である。**
版管理に正本が無ければ移動が他ホストの作業を消しうる（`T-2026-08-26-lovo-decision-rule` に実測）。
今回は `origin/phase0` に同一内容が在ることを先に確かめてから動かした。

作業後に `docs/archive/notion/__pycache__` が生成されたため、これも退避した（削除していない）。

## 2. Task A-3 事前記入値の差し替え

    runindex 最終変更: 96eb3a1c   conventions: a8c07e81
    index.csv 1266 / experiments.csv 285 / verdicts.csv 1506

`resolve-at-intake` の 2 箇所と `counts` の零を上記へ差し替え、L1・L2 は exit 0。

🔴 **`make spec-check` は 2 件で fail する。**

    integration_prohibited_without_pause @ SPEC.md:74  「3 context/auto と tasks/inbox.md の再生成…」
    integration_prohibited_without_pause @ SPEC.md:77  「6 統合（merge）。push と PR の作成は行う」

**実体は偽陽性である。** SPEC §5 A-2 に「`make task-start` で分岐と抑止を置く」、
E-5 に「抑止を**移動**で解除」、判定 M にも抑止の記載がある。検出器の語句パターンに
合致しなかっただけである。SPEC は起票者の本文であり書き換えない。
preflight の P9 では **WARN**（終了コードを変えない）として扱われた。

## 3. Task A-4 資格情報（有無と長さだけ）

    load_env.sh の終了コード: 0
    NOTION_API_KEY: 設定あり（長さ 50）
    WANDB_API_KEY : 設定あり（長さ 86）
    NOTION_DB_ID  : 未設定（本契約は登録簿の id を使うため影響しない）
    合言葉: ~/.config/egosurgery/env-passphrase に 15 バイト・-rw-------

**値は出力していない。** 成立したため停止条件の三つ目は発火しない。

## 4. Task A-5 既存実装の作法（踏襲した）

| 項目 | 実体 |
|---|---|
| API 版 | `2022-06-28`（`src/egosurgery/utils/notion_logger.py:35` ほか 3 箇所で一致） |
| HTTP | `urllib`（`tools/fetch_task.py:328` の `_notion_call_method`）。**新規パッケージを入れない** |
| 頁送り | `page_size` と `start_cursor`、`has_more` で継続（`tools/fetch_task.py:390-405`） |
| 認証 | `Authorization: Bearer` と `Notion-Version` の見出しのみ（`notion_ops._headers`） |
| 再試行 | 既存に 429 の扱いは**無かった**。本契約で追加した（§8） |

## 5. Task A-6 到達性

    plan_master   {"status": "unreachable", "error": "HTTP 404 object_not_found ..."}
    plan_current  {"status": "reachable", "object": "list"}
    run_ledger     {"status": "reachable", "last_edited_time": "2026-08-23T16:39:00.000Z"}
    decision_log   {"status": "reachable", "last_edited_time": "2026-05-25T14:34:00.000Z"}
    lessons        {"status": "reachable", "last_edited_time": "2026-05-25T14:34:00.000Z"}
    procedure_docs {"status": "reachable", "last_edited_time": "2026-05-31T08:39:00.000Z"}
    prompt_library {"status": "reachable", "last_edited_time": "2026-05-25T14:35:00.000Z"}

登録簿の DB キーは 5 件で、起票時点の記載と**差なし**。

## 6. Task B 見出し抽出

### 6.1 対照（判定 C）

    陽性フィクスチャ  -> 7 件
      H1 第一章 / H2 一節 / (入れ子) H3 toggle 見出しの内側 / H3 折りたたみの中の見出し
      H2 段組みの中の見出し / PAGE 子頁の題 / DB 子DBの題
      ※ child_page の内側の見出し b12 は拾っていない（降りない規則が効いている）
    陰性フィクスチャ  -> 0 件（段落・箇条書き・番号付き・コード）
    toggle 内側を 1 件落とした写し -> 7 件から 6 件へ減った

### 6.2 実対象（判定 D）

    page_size=100 -> {"rows": 199, "retries": 0}
    page_size=7   -> {"rows": 199, "retries": 2}
    diff -> 一致

途中で打ち切った写し（150 行）と比べると**不一致**になる（検査が働いている）。

種別の内訳: H1 7 / H2 72 / H3 119 / PAGE 1 / DB 0。
形式検査（`^(  )*(H1|H2|H3|PAGE|DB)\t`）で不適合 **0 件**。
段落を 1 行足した写しでは**不適合 1 件**を検出した（判定 B の空振り確認）。

## 7. Task C DB の export

    run_ledger     {"n_items": 767, "retries": 5}
    decision_log   {"n_items": 65,  "retries": 0}
    lessons        {"n_items": 31,  "retries": 1}
    procedure_docs {"n_items": 6,   "retries": 0}
    prompt_library {"n_items": 3,   "retries": 0}

判定 E（レコード数の一致）:

    run_ledger      manifest= 767 raw= 767 props= 767 bodies= 767  一致
    decision_log    manifest=  65 raw=  65 props=  65 bodies=  65  一致
    lessons         manifest=  31 raw=  31 props=  31 bodies=  31  一致
    procedure_docs  manifest=   6 raw=   6 props=   6 bodies=   6  一致
    prompt_library  manifest=   3 raw=   3 props=   3 bodies=   3  一致

🔴 **`wc -l` で数えて一度「不一致」と誤判定した**（decision_log 65 に対し `wc -l` は 848）。
`properties.csv` のセルに改行を含む本文があるためで、**CSV として読めば一致する**。
実行者の数え方の誤りであり、生成物の欠陥ではない。

判定 F（再現性）: `prompt_library` と `procedure_docs` を二回 export し、
`raw.jsonl` `properties.csv` `bodies.jsonl` の **6 ファイルすべて sha256 一致**。

判定 G: 存在しない id `00000000-...` は `unreachable` として失敗記録（零件の成功にならない）。
陽性側として `task_distribution` に本契約の行が **1 件**あることを確かめた（export はしていない）。

## 8. 実装で足したもの

`docs/archive/notion/export_notion.py` は本契約の生成物である（§3 が生成物として挙げている）。

`page_size=7` の走行が読み取りタイムアウトで 2 度落ちたため、**再試行の対象を
429 だけでなく `OSError`（タイムアウトを含む）へ広げた**。契約 §1 の罠 6 が
「実装を読み、待って再試行する」と定めており、その範囲である。待ちは 2・4・6・8 秒。

## 9. Task D 検査

### 9.1 秘匿（値を出していない）

    notion token の接頭辞 : 0 件
    鍵の書き出し          : 0 件
    Bearer の直書き       : 0 件
    長い符号化文字列       : 8 件  ← 何に一致したのかを目視した（下記）
    合計                  : 8 件

**8 件はすべて偽陽性である。**

    manifest.csv:3-8  長さ=64 16進のみ=True   → 本契約が書いた sha256
    lessons raw/props 長さ=63 16進のみ=False  → 本文中の長い語（英小40/数19/記号4）
    環境の資格情報との完全一致: 0 件

**空振りでないことの確認**: 合成フィクスチャ（`secret_AAA...` / `-----BEGIN RSA PRIVATE KEY-----` /
`taro.yamada@example.com`）で 3 規則とも 1 件ずつ検出した。フィクスチャは一時ファイルで削除済み。

### 9.2 個人情報（判定 I）

    電子メールの形: 0 件（走査 20 ファイル）

停止条件は発火しない。

### 9.3 サイズ（判定 J）

    合計 5,627,935 バイト = 5.37 MB / 閾値 50 MB → 以下
    閾値を実測値の半分に置くと発火する（停止条件が働くことの確認）

### 9.4 forbidden-check（判定 L）

    {"base": "origin/phase0", "changed": 23, "checked": 23, "excluded": 0,
     "status": "pass", "violations": []}
    exit=0

**開始前から在った未追跡は §1 で退避済みのため、罠 10 の fail は起きなかった。**

### 9.5 副作用の不在（判定 K）

5 DB の `last_edited_time` を Task A と Task D で照合し、**5/5 で不変**。
読み取りだけで Notion 側の値が変わっていないことの実測である。

## 10. 変更範囲

    docs/archive/notion/  （生成物。REPORT.md / manifest.csv / toc_plan_*.md /
                            export_notion.py / controls/ / db/）
    tasks/T-2026-08-31-notion-legacy-toc-and-export/  （契約ディレクトリ）
    tasks/inbox.d/T-2026-08-31-notion-legacy-toc-and-export.md  （受け皿）

契約 §4 禁止 3 に従い `make context` `make taskindex` `make inbox` とその check は**回していない**。
`runindex/` は触っていない。上記以外の repo 領域は変更していない。

## 11. 送出

（Phase E の出力をここへ置く。）
