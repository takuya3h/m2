# audit — T-2026-09-01-notion-retire-scripts-and-speccheck

実行ホスト `lecun` / 分岐 `feat/notion-retire-scripts-and-speccheck`。GPU 未使用。
**Notion への読み書きは行っていない**（退役の確認は乾燥走行と模擬）。

---

## 1. Task A 前提と門

### 1.1 退避（A-1）

`.sync-pause.released`（前契約の解除マーカー。同期対象外）をスクラッチパッドへ退避。**消していない。**

### 1.2 事前記入値（A-3）

    runindex: 96eb3a1c  conventions: a8c07e81
    index 1266 / experiments 285 / verdicts 1506

差し替え後 L1・L2 は exit 0。

**`make spec-check` は修正前 1 件で fail**（罠 5 のとおり記録して続けた）。

    integration_prohibited_without_pause @ SPEC.md:55

### 1.3 修正前の三本の陰性例（判定 E の反対側）

    T-2026-08-31-notion-legacy-toc-and-export       hits=2 status=fail lines=[74, 77]
    T-2026-08-31-notion-repo-followup-and-retire    hits=1 status=fail lines=[82]
    T-2026-09-01-notion-retire-scripts-and-speccheck hits=1 status=fail lines=[55]

**修正前は三本とも fail した（計 4 件）。**

### 1.4 門（A-4）

    origin/phase0 の configs/notion.yaml に claude_app_surfaces 節: あり
    空振り確認: 存在しない節名 NO_SUCH_SECTION では失敗する

### 1.5 試験の基準（A-5）

    6 failed, 509 passed

---

## 2. Task B 個別投稿スクリプトの退役

### 2.1 集合の列挙（B-1・異質な二通り）

**方法 1: 書き込み endpoint の文字列から**（`/pages` への POST/PATCH）

    scripts/post_eval_to_notion.py 2 / post_hc_to_notion.py 2 / post_t1b_ca_to_notion.py 2
    src/egosurgery/utils/notion_logger.py 2 / notion_ops.py 2
    tools/report_task.py 1

**方法 2: HTTP ライブラリの呼び出しから**（`requests.post|patch` / `method="POST|PATCH"`）

    上記に加えて draft_master_update.py 2 / notify_experiment.py 1 /
    retired/notion_context_pack.py 1 / tools/fetch_task.py 1

**差の内訳を実装で確かめた。**

| 差分 | 正体 | 扱い |
|---|---|---|
| `draft_master_update.py` | 94 は `databases/query`（読み）、**222 は `/pages/` への patch** | **退役対象** |
| `notify_experiment.py` | Slack の webhook（`SLACK_WEBHOOK_URL`）。Notion ではない | 対象外 |
| `retired/notion_context_pack.py` | `databases/query`（読み）。前契約で退役済み | 対象外 |
| `tools/fetch_task.py` | 配布台帳。`method=` が変数のため方法 1 で拾えなかった | 対象外（禁止 10） |
| `tools/report_task.py` | 配布台帳。`F._notion_call_method` 経由のため方法 2 で拾えなかった | 対象外（禁止 10） |

**退役対象は 4 本に確定した。**

    scripts/post_eval_to_notion.py
    scripts/post_hc_to_notion.py
    scripts/post_t1b_ca_to_notion.py
    scripts/draft_master_update.py

### 2.2 識別子の解決経路（B-2）

| スクリプト | 解決経路 |
|---|---|
| `post_eval_to_notion.py` | `NOTION_DB_ID` 環境変数（256-257 行） |
| `post_hc_to_notion.py` | `NOTION_DB_ID` 環境変数（159-160 行） |
| `post_t1b_ca_to_notion.py` | `NOTION_DB_ID` 環境変数（129-130 行） |
| `draft_master_update.py` | `configs/notion.yaml` を自前で読む（79, 200 行） |

🔴 **三本は環境変数を自前で読むため、登録簿の退役では止まらない。** 入口で止める必要がある。

### 2.3 退役（B-3）

4 本を `scripts/retired/` へ **`git mv`**（削除していない）。
各ファイルへ `RETIRED_SINCE` と `_retired_notice()` を置き、`__main__` を通知だけにした。
前契約の `RETIRED_DB_KEYS` と同じ考え方（**無言で成功したことにしない**）。

### 2.4 両方向の確認（B-4。送信していない）

**陽性側**

    post_eval_to_notion    exit=3  [retired] ... は 2026-09-01 に退役した。Notion へ投稿しない
    post_hc_to_notion      exit=3  同上
    post_t1b_ca_to_notion  exit=3  同上
    draft_master_update    exit=3  同上

**陰性側**（入口を外した写しを repo の外に作り `--dry-run` で走らせた）

    入口を外した写しの exit: 0
    出力: [hc-post] SKIP seed42: result.json 欠損 ...
    → 退役の入口を外すと元の処理へ進む。--dry-run のため投稿していない

### 2.5 参照の追随（B-5）

| 参照元 | 追随 |
|---|---|
| `scripts/eval_and_post.sh` | 投稿の呼び出しを退役の記述へ置換 |
| `docs/auto_logging.md` | 2 箇所を `scripts/retired/` へ更新し「2026-09-01 に退役」と明記 |

    make docs-check  -> exit=0（一度 exit 2 で docs/auto_logging.md:71 の残りを検出した）
    make agent-check -> exit=0

---

## 3. Task C spec-check の偽陽性の修正

### 3.1 検出器が見ていたもの（C-1）

    _PAUSE_MARK = ".sync-pause"
    if _PAUSE_MARK in c.md_text: return []

🔴 **本文に文字列 `.sync-pause` があるかだけを見ていた。**
三本の SPEC は抑止を日本語で書き（「`make task-start` で分岐と抑止を置く」
「抑止を移動で解除」）、目印の文字列を含まないため該当していた。

### 3.2 陽性と陰性の切り分け

「抑止」の語だけでは分けられない（陽性の `template-leak` にも 11 件ある）。
**使われ方が違う。**

| | 「抑止」の文脈 |
|---|---|
| 陽性（`template-leak`） | 「抑止**の手段を探す**」「抑止**できたか**は Phase B の成果」— 課題として扱う |
| 陰性（本契約ほか 2 本） | 「抑止を**置く**」「抑止を**移動で解除**」— **手順として書く** |

### 3.3 直した規則（C-3）

    _PAUSE_SET     = 抑止[^。\n]{0,20}(置く|設置|作成|付ける)
    _PAUSE_RELEASE = 抑止[^。\n]{0,20}(解除|外す|移動で解|消せば)

    def _has_pause_procedure(text):
        if _PAUSE_MARK in text: return True
        return bool(_PAUSE_SET.search(text) and _PAUSE_RELEASE.search(text))

**設置と解除の双方に触れる記述だけを抑止の手順とみなす。** 片方だけでは足りない。

**両方向の実測**

    陰性 3 件: すべて hits=0 status=pass
    陽性 3 件: bundle-attachment-transport 55 / template-leak 47 /
              implementation-history-index 46 ← いずれも従来と同じ行を検出

**空振りでないことの確認**: 陽性例の本文へ「抑止を置く／解除する」を足した写しでは
`_has_pause_procedure` が True になり該当しなくなる。**規則は本文に感応している。**

全契約での該当は **19 件 → 15 件**（減った 4 件は陰性 3 本ぶん）。

### 3.4 教師データ（C-2・C-4）

`tests/test_check_spec.py` の `TEACHER` へ陰性例 3 件（`rule=None`）を足し、
`PAUSE_PROCEDURE_NEGATIVE` に対象を機械で引ける一覧を置いた。

    test_teacher_detection_rate の分母を 16 → 19 へ更新
    **検出すべき件数（expected）は変えていない。** 陽性例を弱めていない。

    $ python -m pytest tests/test_check_spec.py -q
    22 passed

---

## 4. Task D 検査

### 4.1 試験（D-1・判定 G）

    前 6 failed / 509 passed  →  後 6 failed / 509 passed
    増えた 0 件 / 減った 0 件

### 4.2 forbidden-check（D-2・判定 I）

    {"base": "origin/phase0", "changed": 10, "checked": 10, "excluded": 0,
     "status": "pass", "violations": []}   exit=0

### 4.3 秘匿（D-3・判定 J）

変更ファイル 8 件を走査。**検査は値を出力していない。**

    token 接頭辞 0 件 / 鍵の書き出し 0 件 / Bearer 直書き 0 件
    空振り確認（合成フィクスチャ）: 3 規則とも 1 件ずつ検出

---

## 5. 末尾の再生成と送出

（D-5 以降をここへ置く。）
