# RESULT — T-2026-08-25-issuer-refs-to-repo

**kind:** `impl` / 実行ホスト `philip` / repo `/home/ubuntu/slocal2/m2`
**分岐:** `feat/issuer-refs-to-repo` / 実行 `2026-08-25 15:13〜16:0x JST`

手続きの証跡は `audit.md`。**同じ内容を二度書かない。** 行番号で指す。

---

## 判定

**verdict: pass**（ただし `UNKNOWN` 3 件、逸脱 4 件）

| Gate | 結果 | 根拠 |
|---|---|---|
| G1 | **pass** | 注入の識別と範囲を実装から読んだ（`audit.md:40-99`）。既存 7 節の要約値・行数・一覧を追加前に取った（`audit.md:101-154`）。置き場所は版管理のどの ref にも無い（`audit.md:156-177`）。食い違い 5 件を列挙（`audit.md:179-293`） |
| G2 | **pass** | 二つを配置（`audit.md:331-344`）。申し送りの節を末尾へ追加（`audit.md:346-405`）。既存 7 節の**解決本文**が 1 バイトも変わらないことを要約値で示した（`audit.md:407-441`）。陽性 2・陰性 2 の対照を取った（`audit.md:443-505`） |

**本命は成立した。** `conventions#issuer_cautions` が解決し、13 項目の表がそのまま取れる。
**契約ごとの転記は不要になる。**

---

## 完了判定

| # | 判定 | 実測 |
|---|---|---|
| A | 注入の仕組みを実装から読んだ | 識別 `_ANCHOR_RE = re.compile(r'<a id="([a-z0-9_]+)"></a>')`（`tools/validate_task.py:34`）。範囲 `<a id="X"></a>(.*?)(?=<a id="|\Z)`（`tools/preflight_task.py:117`）。**本文抽出の汎用実装は無い** → 一部 `UNKNOWN` |
| B | 既存の節の要約値・行数・一覧 | 追加前 `143` 行 `6346` B `sha256 d281e5e3…`。アンカー 7 件（12/24/35/65/98/109/121 行） |
| C | 置き場所の衝突 | `git log --all -- context/env-facts.md docs/issuer-defects.md` = **0 件**。`HEAD` に無い。`git check-ignore` exit 1。**上書きしていない** |
| D | 食い違いの列挙 | **5 件**（D1〜D5）。うち 2 件を実測どおりに直した |
| E | 二つの文書を置いた | `context/env-facts.md` 89 行 `14b509d9…`（D2 を修正）、`docs/issuer-defects.md` 84 行 `7ca530b6…`（**無変更**） |
| F | 申し送りの節を末尾へ追加 | `<a id="issuer_cautions"></a>` を 144 行目に。見出しは既存に倣い `## issuer_cautions` |
| G | **既存の節が一行も変わっていない** | 既存 7 節の解決本文の `sha256` が**全て同一**。`git diff --numstat` = `35 0`、削除行 `0`、位置 `@@ -143,0 +144,35 @@` |
| H | 新しい参照が解決し中身が取れる | `conventions#issuer_cautions` → **1012 B / 空でない / sha256 512f7bf5…**。表と字下げが保たれる |
| I | **誤った参照が解決に失敗する** | 綴り違い `issuer_cautionz` → `[L2-5]` **exit 2**。配られたハイフン形 `issuer-cautions` → `[L1-1]` **exit 2**。**層が違う 2 種類とも落ちた** |
| J | 報告の構成と分量 | 構成は指定どおり 8 節。**本ファイル 193 行で目安 150 を 43 行超過している**。証跡は `audit.md` 628 行へ分離済み |
| K | 既存部分と禁止領域が無変更 | 上記 G。`runindex/**` `context/auto/**` は `git diff origin/phase0 --name-status` に**現れない**（差は `.stglobalignore` と `context/conventions.md` の 2 件のみ） |
| L | 秘匿検査を自分で行った | §送出 |
| M | 変更が契約の範囲に限られる | §送出 |
| N | 台帳へ返し、抑止を外し、退避を戻した | §送出 |

---

## 注入の書式（次の契約で使う）

| 項目 | 実測 |
|---|---|
| 参照の書き方 | `conventions#<anchor>`。様式の制約は `^conventions#[a-z0-9_]+`（`tasks/_schema/spec.schema.json:148`） |
| 節の識別 | **`<a id="<anchor>"></a>` の HTML アンカーのみ。`##` 見出しは見ていない** |
| 使える文字 | **`[a-z0-9_]` だけ。ハイフンは通らない**（L1 と L2 の両方で落ちる） |
| 解決される範囲 | **アンカー行の直後から、次の `<a id="` またはファイル末尾まで。** 明示の終端は無い |
| 表・字下げ | **保たれる**（生のスライス） |
| 解決できないとき | `[L2-5] アンカー X が存在しません` → `make task-validate` が **exit 2**。**静かに空にならない** |
| 追加位置 | **必ずファイル末尾へ、空行を挟まずに。** 手前へ入れると直前の節の解決範囲が縮む |
| 現在のアンカー | `split` `eval_recipe` `frozen_source` `sigma` `prohibitions` `env_p0` `naming` **`issuer_cautions`**（8 件） |

**注意**: 本文の切り出しを機械化した実装は `frozen_source` 専用の 1 か所だけである
（`tools/preflight_task.py:109-126`）。**一般の節の抽出は実行者の手続き**であり、
`context/conventions.md:5` が「CLI は実行直前に原文を読み」と定めているに留まる。
**抽出側の壊れ方は測れない** → `UNKNOWN`。

---

## 直した食い違い

| # | 場所 | 配られた本文 | 実測 | 扱い |
|---|---|---|---|---|
| D1 | `SPEC.md` | 「バンドルには五つのファイルが入っている」 | `ALLOWED_FILES = ("spec.yaml","SPEC.md","prereg.md")`（`tools/fetch_task.py:52`）。**5 ファイルのバンドルは `BundleError` で拒否される**。`issuer-cautions.md` はホストのどこにも無かった | **停止して利用者へ提示し、本文を受け取った**（`context/issuer-cautions.md`、13 項目） |
| D2 | `env-facts.md:87` | `.codex/skills/task` は `~/claude-sync/codex/` 経由の symlink。**保守で失われた** | 版管理下の symlink `../../.claude/skills/task`（commit `19341085`）。**解決でき失われていない**。`~/claude-sync/codex/` は**存在しない** | **直した** |
| D3 | `env-facts.md:54` | `.env` の変数は **5 つ** | 5 つの名前は**すべて有効**（値は出力せず有無だけ照合）。**直さない**。ただし `CLAUDE.md:74` と `docs/notion_integration.md:30` が挙げる `NOTION_DB_ID` は **unset** ＝ **版管理側の文書が古い**（本契約の範囲外） | 記録のみ |
| D4 | `SPEC.md` | 手順書 671 行 → 341 行 | 起票者の手順書は版管理の外。**このホストから測れない** | `UNKNOWN` |
| D5 | `issuer-cautions.md:1-2` | `<a id="issuer-cautions"></a>` / `## issuer-cautions` | **ハイフンは `_ANCHOR_RE` に一致しない。** そのまま連結するとアンカー集合は 7 件のままで、**追記したのに参照できない** | **`issuer_cautions` へ直した** |

---

## 実測（次の契約で使う値）

| 値 | 実測 |
|---|---|
| `conventions_rev` | **`d422b08`**（`git log -1 -- context/conventions.md` と一致。**置換は不要だった**）。本契約の追加で次は変わる |
| `context/conventions.md` | 追加後 **178 行 / 8694 B / `sha256 e2bc9a14a1c906e5…`** |
| `context/env-facts.md` | **89 行 / `14b509d9…`**（版管理入り） |
| `docs/issuer-defects.md` | **84 行 / `7ca530b6…`**（版管理入り） |
| `conventions#issuer_cautions` | **1012 B / 35 行 / `sha256 512f7bf5…`** |
| 抑止の対応状況 | `grep -c sync-pause ~/bin/m2-sync.sh` = **2**（稼働中の版は対応済み） |
| P9 spec_lint | **WARN 2 件**: `separated_source@SPEC.md:50`（行継続の `\` を挟んだ `source … && make` を分断と判定。**この契約では誤検出**）、`forbidden_vs_output@SPEC.md:260`（完了判定 K が `forbidden-check` を指していない。**該当は正しい**） |

---

## 起票者の誤り

1. **`asserted_without_measuring`** — 「バンドルには五つのファイルが入っている」。
   取り込みは 3 種しか受け取れず（`tools/fetch_task.py:52`）、5 ファイルのバンドルは構造上存在し得ない。
   **本命の `issuer-cautions.md` が届かず、実行が止まった。**
2. **`check_does_not_check`** — 配られた節のアンカーがハイフン形で、`_ANCHOR_RE` に一致しない。
   「末尾へ追記する」だけの指示に従うと、**アンカー行は在るのに節は集合に入らない。**
   静かに参照できない状態になる。**書式の実測を指示に含めるべきだった。**
3. **`self_contradiction`** — SPEC 禁止 1「既存の節を変更しない」と
   `context/conventions.md:7`「改訂したら変更履歴に追記」が両立しない。
   **変更履歴は `naming` 節の本文の内側**にあり、行を足せば解決結果が変わる。
4. **`check_does_not_check`** — 完了判定 G を `git diff` で測ると、**空行 1 つの挿入で
   `naming` の解決本文が 526→527 B に変わっても「削除 0 行」に見える。**
   行の差分は節の不変性を測っていない。**実際に一度踏んだ**（`audit.md:389-405`）。
5. **`asserted_without_measuring`** — `env-facts.md:87` の `.codex/skills/task` 喪失（D2）。
6. **`self_contradiction`** — SPEC 禁止 4「生成物を再生成しない」と
   手順書 §6「`make taskindex` / `make inbox` を回して投影に現れることを確かめる」が両立しない。

---

## 逸脱・想定外・UNKNOWN

### 逸脱

1. **二つの文書を「配置」していない。** 開始時点で 15:08 に版管理外へ置かれていた
   （契約の展開 15:12 より前）。**作り直さず、D2 の 1 行だけ直して受け入れた。**
   版管理のどの ref にも無いため上書きの危険は無いと判断した（`audit.md:156-177`）。
2. **`make taskindex` / `make inbox` を回していない。** SPEC 禁止 4 が明示的に禁じるため。
   手順書 §6 の要求とは食い違う。**契約を優先した。**
   → `tasks/inbox.d/` へは書いたが、`tasks/inbox.md` へは反映されていない。
3. **`context/conventions.md:7` が求める変更履歴への追記をしていない。** 禁止 1 を優先した。
4. **報告が目安の分量を超えた（193 行 / 目安 150）。** 起票者の誤り 6 件と UNKNOWN 3 件と
   逸脱 5 件を落とさずに書くと収まらなかった。**手続きの証跡は `audit.md` へ分離済み**で、
   残っているのは判断に要る事実だけである。**削るなら完了判定の表が候補。**
5. **`context/issuer-cautions.md` を残置した。** SPEC は「ファイルとして置かない」と定めるが、
   禁止 5 が未追跡の成果物の削除を禁じる。**commit していない。処分は起票者の判断に委ねる。**

### 想定外

- **`${PIPESTATUS[0]}` で終了コードが空になった。** 対話シェルは zsh。
  `context/env-facts.md:35` と `docs/issuer-defects.md:20` に既出の罠を、
  **その 2 文書を扱う契約の中で踏んだ。** `out=$(...); ec=$?` に直して取り直した。
- **`forbidden-check` が違反 1 件を報告した**（exit 2）。
  `{"path": "context/conventions.md", "reason": "禁止されたファイル context/conventions.md"}`
  **本契約は追加のみである。** 根拠: 削除行 `0`、位置は末尾 `@@ -143,0 +144,35 @@`、
  既存 7 節の解決本文の `sha256` が全て同一。**道具は「追加のみ」を判別しない。**
- 開始前から `.stglobalignore` の変更と digest 3 件と `.sync-pause.released` が在った。
  **本契約の産物ではない。commit していない。**

### UNKNOWN

| # | 測れなかったもの | 理由 |
|---|---|---|
| 1 | 一般の節の**本文抽出**の壊れ方 | 汎用実装が無い（`frozen_source` 専用の 1 か所のみ）。抽出は実行者の手続き |
| 2 | `.env` の変数が**ちょうど 5 件**か | 照合したのは 6 名だけ。`.env` 本体の読み取りは実行基盤が拒否した |
| 3 | 手順書 671 行 → 341 行の効果 | 起票者の手順書は版管理の外。このホストから測れない |

---

## 送出

| # | 実測 |
|---|---|
| commit | `a8c07e81`（9 ファイル）。**`.stglobalignore` の変更・digest 3 件・`.sync-pause.released`・`context/issuer-cautions.md` は段階に上げていない** |
| push | `origin/feat/issuer-refs-to-repo` **exit 0**（`* [new branch]`） |
| PR | **#151**（`feat/issuer-refs-to-repo` → `phase0`） |
| `make forbidden-check` | **exit 2**。`{"path": "context/conventions.md", "reason": "禁止されたファイル context/conventions.md"}`。**追加のみである根拠は §想定外** |
| `make task-validate` | **exit 0**（`OK`）。報告作成後は `WARN [L2-6] conventions.md が d422b08 以降に変更されています`。**本契約自身の追加が原因**であり、`conventions_rev` は起票時点の値として `d422b08` のまま残した（実測と一致していた） |
| `make task-preflight` | **exit 0**（4 PASS / 1 WARN / 4 SKIP / 0 FAIL） |
| `make taskindex` / `make inbox` | **回していない**（SPEC 禁止 4）。§逸脱 2 |
| `make task-report` | §末尾 |
| 抑止 | §末尾 |

### 秘匿の自主検査（完了判定 L）

**形の規則 5 件**（PEM 秘密鍵 / Notion トークン / 40 桁 16 進 / AWS 鍵 / 代入の形）と
**環境の実値との直接照合 4 本**（`WANDB_API_KEY` `NOTION_API_KEY` `WANDB_ENTITY` `DATA_ROOT`）。
**検査器は経路・規則名・件数しか出力しない。値を出す経路が無い。**

| 対照 | 対象 | 結果 |
|---|---|---|
| **陽性** | 実値を埋めた囮（**版管理外**） | `live:NOTION_API_KEY=1, live:WANDB_API_KEY=1, notion_token=1, pem_private_key=1` **exit 1** |
| **陰性** | 送出する 9 ファイル | 全件 `0`、合計 **0**、**exit 0** |

**囮は削除した。commit していない**（`git status` に `decoy` は 0 件）。詳細 `audit.md:556-612`。

🔴 **所見**: 陽性対照で `wandb_key_shape`（40 桁 16 進）は**一致しなかった**。
形の規則だけでは `WANDB_API_KEY` を捕まえられず、**実値との照合だけが効いた。**
形だけの検査は「規則が実値の形と合っていない」壊れ方に気づけない。

---

## 台帳と抑止

| # | 実測 |
|---|---|
| `make task-report` | **exit 0**。`{"task_id": "T-2026-08-25-issuer-refs-to-repo", "verdict": "pass", "n_issuer_defects": 6, "report_sha256": "2e480fa18cacdb62…", "report_bytes": 14369, "replaced_blocks": 0}` |
| 報告の commit | `7897db16`（push 済み。`a8c07e81..7897db16`） |
| `.sync-pause` | **外した**（`rm -f`、`[ -e .sync-pause ]` が偽）。抑止中の記録は `15:29:45 [philip] 一時停止中: …` の 1 件 |
| 退避したもの | **無い**（開始前の未追跡は退避せず、そのまま残した。**削除は 0 件**） |

**抑止の有効性の直接測定はしていない。** 稼働中の版が対応済みであること
（`grep -c sync-pause ~/bin/m2-sync.sh` = **2**）と、抑止中の記録が残ったことまで。
