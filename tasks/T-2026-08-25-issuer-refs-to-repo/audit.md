# audit — T-2026-08-25-issuer-refs-to-repo

手続きの証跡。**出力を要約せず貼る。** 散文の報告は `RESULT.md`。

実行ホスト `philip` / repo `/home/ubuntu/slocal2/m2` / 分岐 `feat/issuer-refs-to-repo`

---

## 0. 前提

    $ touch .sync-pause && ls -la .sync-pause
    -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 25 15:13 .sync-pause

    $ grep -c "sync-pause" ~/bin/m2-sync.sh
    2

稼働中の常駐処理は抑止に対応済み（0 ではない）。

    $ git --no-pager status --porcelain | grep -c ''
    8

    $ git --no-pager status --porcelain
     M .stglobalignore
    ?? .sync-pause.released
    ?? context/env-facts.md
    ?? docs/issuer-defects.md
    ?? docs/sessions/digest/2026-08-22-d0076c74-6667-46a0-95fb-96d9c1d68f8c.md
    ?? docs/sessions/digest/2026-08-23-da7743d1-f487-4089-98e2-79391f7eb001.md
    ?? docs/sessions/digest/2026-08-24-32ddc4ea-b89f-4cf5-b828-6ef1483afe84.md
    ?? tasks/T-2026-08-25-issuer-refs-to-repo/

**開始前から在る。** `.stglobalignore` の変更と digest 3 件と `.sync-pause.released` は
本契約の産物ではない。**commit しない。** 分岐は既に在ったため `task-start` は再実行していない。

    $ git --no-pager reflog -1
    7c45bd7c HEAD@{0}: checkout: moving from feat/bengio-syncthing-node-2 to feat/issuer-refs-to-repo

---

## Task 1 Step 1 — 注入の実装を読む

### 節の識別

`tools/validate_task.py`

    28:CONVENTIONS_PATH = REPO_ROOT / "context" / "conventions.md"
    34:_ANCHOR_RE = re.compile(r'<a id="([a-z0-9_]+)"></a>')

    293:def conventions_anchors() -> set[str]:
    294:    if not CONVENTIONS_PATH.exists():
    295:        return set()
    296:    return set(_ANCHOR_RE.findall(CONVENTIONS_PATH.read_text(encoding="utf-8")))

**識別子は HTML のアンカー `<a id="..."></a>` である。Markdown の見出しではない。**
**使える文字は `[a-z0-9_]` のみ。ハイフンは通らない。**

### どこからどこまでを取るか

`tools/preflight_task.py`

    109:def _frozen_source_from_conventions() -> tuple[str | None, str | None]:
    110:    """conventions.md の frozen_source 節から (正本 SHA-256, ckpt パス) を読む。
    111:
    112:    節の切り出しは `<a id="frozen_source"></a>` から次の `<a id=` まで。
    113:    """
    ...
    117:    match = re.search(r'<a id="frozen_source"></a>(.*?)(?=<a id="|\Z)', text, re.S)

**アンカーから、次の `<a id="` またはファイル末尾まで。** 明示の終端記号は無い。
本文は生の切り出しであるため、**表も字下げもそのまま保たれる。**

### 参照が解決できないとき

`tools/validate_task.py`

    388:    anchors = conventions_anchors()
    389:    if not anchors:
    390:        findings.append(Finding("L2-5", "contract.inject_verbatim", "context/conventions.md が読めません"))
    391:    for ref in spec.get("contract", {}).get("inject_verbatim", []):
    392:        anchor = ref.split("#", 1)[1]
    393:        if anchors and anchor not in anchors:
    394:            findings.append(Finding("L2-5", "contract.inject_verbatim", f"アンカー {anchor} が存在しません"))

**静かに空にはならない。** アンカーが無ければ L2-5 が立ち、`make task-validate` が exit 1 で落ちる。
（本文の切り出し側は `frozen_source` 専用のため、一般の節の**本文抽出は機械化されていない**。
`context/conventions.md:5` は「CLI は実行直前にこのファイルから原文を読み」と書いており、
**抽出は実行者の手続きである。** 抽出側の壊れ方は測れない → その部分は `UNKNOWN`。）

### 書式の制約（まとめ）

| 確かめること | 実測 |
|---|---|
| 節をどう識別するか | `<a id="[a-z0-9_]+"></a>`。**見出しは見ていない** |
| どこからどこまで | アンカー → 次の `<a id="` か EOF |
| 表・字下げ | 生の切り出しのため保たれる |
| 解決できないとき | L2-5 で FAIL、exit 1。**静かに空にならない** |
| 本文抽出の機械化 | **無い**（`frozen_source` 専用の実装のみ）→ `UNKNOWN` |

---

## Task 1 Step 2 — 既存の節を測る

    $ sha256sum context/conventions.md
    d281e5e30526ab5452f77b59b6792cc2095496122d9972f02932e4bda5ee4403  context/conventions.md

    $ grep -c '' context/conventions.md
    143
    $ wc -c < context/conventions.md
    6346

    $ grep -n '<a id=' context/conventions.md
    12:<a id="split"></a>
    24:<a id="eval_recipe"></a>
    35:<a id="frozen_source"></a>
    65:<a id="sigma"></a>
    98:<a id="prohibitions"></a>
    109:<a id="env_p0"></a>
    121:<a id="naming"></a>
    $ grep -c '<a id=' context/conventions.md
    7

`issuer-cautions` / `issuer` / `申し送り` / `caution` を名前に持つ節は**無い**。

    $ grep -in 'issuer\|申し送り\|caution' context/conventions.md
    (該当なし)

### 末尾の構造（追加位置の判断に要る）

    121:<a id="naming"></a>
    ...
    133:---
    134:
    135:## 変更履歴
    ...
    143:| 2026-08-07 | 290da51 | frozen_source に「検査の適用範囲」を追記。…… |

**`変更履歴` はアンカーを持たない。** 切り出し規則により、**`naming` 節の本文は
121 行から EOF（変更履歴を含む）まで**である。

これが追加位置を決める。

- **変更履歴の前へ入れると** `naming` の解決範囲が 132 行までへ縮み、**既存の節の中身が変わる。**
- **EOF へ足すと** `naming` は 121〜143 行のまま。**既存の解決結果は 1 バイトも変わらない。**

→ **EOF へ足す。**

### 変更履歴への追記について

`context/conventions.md:7` は「改訂したら末尾の変更履歴に追記すること」と定める。
一方 SPEC の禁止 1 は「既存の節を変更・削除しない（追加だけを行う）」と定める。
**変更履歴は `naming` 節の本文の一部**であるため、行を足せば `naming` の解決結果が変わる。
**両立しない。** 禁止 1 を優先し、変更履歴には追記しない。→ `issuer_defects` へ記録。

---

## Task 1 Step 3 — 置き場所の衝突

    $ git --no-pager cat-file -e HEAD:context/env-facts.md
    fatal: path 'context/env-facts.md' exists on disk, but not in 'HEAD'

    $ git --no-pager log --all --oneline -- context/env-facts.md docs/issuer-defects.md | grep -c ''
    0

    $ git check-ignore -v context/env-facts.md docs/issuer-defects.md; echo "exit=$?"
    exit=1

    $ ls -la context/env-facts.md docs/issuer-defects.md
    -rw-rw-r-- 1 ubuntu ubuntu 4919 Aug 25 15:08 context/env-facts.md
    -rw-rw-r-- 1 ubuntu ubuntu 5011 Aug 25 15:08 docs/issuer-defects.md

**版管理には無い。どの ref にも一度も現れていない。除外にも落ちない。**
**「既存の repo の内容との衝突」ではない。** 中身は配られた本文そのもので、
契約の展開（`tasks/…` は 15:12）より前の 15:08 に**版管理外で置かれていた**。

→ 上書きの危険は無い。**停止しない。** ただし「実行者が置いた」ではないため逸脱へ記録する。

---

## Task 1 Step 4 — 配られた本文と実測の突き合わせ

### 一致したもの（直さない）

| 記述 | 突き合わせ先 | 実測 |
|---|---|---|
| `lecun` / `efros` の repo は `~/slocal/m2` | 過去の報告 | `T-2026-08-24-lecun-syncthing-node/RESULT.md:4` `repo: ~/slocal/m2`、`T-2026-08-12-sync-audit-efros/audit.md:3` `repo ~/slocal/m2` |
| 他は `~/slocal2/m2` | 同上 | `T-2026-08-24-lecun-syncthing-node/RESULT.md:55`「lecun だけ `~/slocal/m2`。他四台は `~/slocal2/m2`」 |
| 同期処理の版 `v2.1.3` / 実行ファイル `e8a08fdd…` | `T-2026-08-24-*` | `andrew-syncthing-node/RESULT.md:27`、`ilya-syncthing-node/RESULT.md:27` に同一値 |
| 相手の住所 `tcp://127.0.0.1:22001` | 同上 | `syncthing-config-survey/RESULT.md:76` |
| 中心 `192.168.196.150`、口 `50072` | 同上 | `andrew-syncthing-node/RESULT.md:52`、`lecun-syncthing-node/RESULT.md:26` |
| 住所の一覧は全 15 台 | `scripts/sync/hosts/` | `grep -c '^[[:space:]]*Host ' scripts/sync/hosts/ssh_config.d.snapshot.conf` = **15** |
| keeper は 30 分周期 | 実装 | `scripts/sync/keeper.sh:51` `sleep 1800` |
| 抑止は目印の**存在だけ**を見る | 実装 | `scripts/sync/m2-sync.sh:40` `if [ -f "$M2DIR/.sync-pause" ]; then` |
| 除外は 1 実効行 = 4 展開行 | 過去の報告 | `T-2026-08-25-sync-ignore-scope/RESULT.md:43`「`ignore` 68 行 → `expanded` 184 行。1 行が 4 行へ展開され `**/` が前置される」 |
| task 手順書は `.claude/skills/task/SKILL.md`（版管理下） | 実測 | `git ls-files .claude/skills/task/SKILL.md` に在り、本セッションが読んでいる |

### 食い違ったもの

#### D1 — バンドルは 5 ファイルを運べない（SPEC 本文）

SPEC.md「**バンドルには五つのファイルが入っている。**」

    $ sed -n '52p' tools/fetch_task.py
    ALLOWED_FILES = ("spec.yaml", "SPEC.md", "prereg.md")

    $ grep -n 'name not in ALLOWED_FILES' tools/fetch_task.py
    136:            if name not in ALLOWED_FILES:
    137:                raise BundleError(f"受け取れないファイルです: {name!r}（許可: {', '.join(ALLOWED_FILES)}）")

**取り込みが受け取れるのは 3 種のみ。** `env-facts.md` `issuer-defects.md` `issuer-cautions.md`
を含むバンドルは `BundleError` で拒否される。**5 ファイルのバンドルは存在し得ない。**

実際に届いたもの:

    $ ls tasks/T-2026-08-25-issuer-refs-to-repo/
    SPEC.md  spec.yaml            ← 15:12（取り込みが置いた）
    $ ls -la context/env-facts.md docs/issuer-defects.md
    …  Aug 25 15:08              ← 版管理外で別途置かれた

    $ find / -name "issuer-cautions*" -not -path "*/proc/*" 2>/dev/null
    (0 件)
    $ grep -rl "issuer-cautions" --exclude-dir=.git .
    tasks/T-2026-08-25-issuer-refs-to-repo/SPEC.md

**`issuer-cautions.md` はこのホストのどこにも無い。** 言及は SPEC 本文の 1 か所だけ。

#### D2 — `.codex/skills/task` は失われていない（env-facts.md:87）

配られた本文:

    87: - Codex 側の `.codex/skills/task` は `~/claude-sync/codex/` 経由の symlink。**保守で失われた**

実測:

    $ ls -la .codex/skills/
    lrwxrwxrwx 1 ubuntu ubuntu 25 Aug 22 06:54 task -> ../../.claude/skills/task
    $ git ls-files .codex/skills/task | grep -c ''
    1
    $ git --no-pager log --oneline -1 -- .codex/skills/task
    19341085 feat(codex): share the task procedure with a second agent via symlink
    $ [ -e .codex/skills/task/SKILL.md ] && echo yes
    yes
    $ ls -la ~/claude-sync/codex/
    ls: cannot access '/home/ubuntu/claude-sync/codex/': No such file or directory

**版管理下の symlink で、`~/claude-sync/codex/` は経由していない。解決でき、失われていない。**
`~/claude-sync/codex/` のほうが存在しない。→ **実測を正として直す。**

#### D3 — `.env` の変数の件数は測れない（env-facts.md:54）

配られた本文:

    54: - `.env` の変数は **5 つ**（`WANDB_API_KEY` `WANDB_PROJECT` `WANDB_ENTITY` `DATA_ROOT` `NOTION_API_KEY`）

実行基盤が `.env*` の読み取りを拒んだ。

    $ grep -o '^[A-Za-z_][A-Za-z0-9_]*=' .env.example
    Permission to use Bash with command … has been denied.

版管理上の記述は `NOTION_DB_ID` も `.env` の変数として挙げる。

    $ grep -n "NOTION_DB_ID" CLAUDE.md docs/notion_integration.md
    CLAUDE.md:74:…認証 `NOTION_API_KEY`/`NOTION_DB_ID` は `.env`。…
    docs/notion_integration.md:30:#   NOTION_DB_ID=ef4ccd02-…          # 実験Run台帳 DB（notion_logger 用）

`scripts/load_env.sh` が名前を挙げるのは 2 つだけ（71 行の表示）。

読み込み後に**名前の有無だけ**を照合した（**値は出力していない**）。

    $ source scripts/load_env.sh >/dev/null 2>&1
    $ for v in WANDB_API_KEY WANDB_PROJECT WANDB_ENTITY DATA_ROOT NOTION_API_KEY NOTION_DB_ID; do \
        printf '%s=%s\n' "$v" "$(eval "[ -n \"\${$v:-}\" ]" && echo set || echo unset)"; done
    WANDB_API_KEY=set
    WANDB_PROJECT=set
    WANDB_ENTITY=set
    DATA_ROOT=set
    NOTION_API_KEY=set
    NOTION_DB_ID=unset

**配られた本文の 5 つの名前はすべて有効。`NOTION_DB_ID` は無い。→ env-facts.md は直さない。**

食い違っているのは**版管理側の文書**である。`CLAUDE.md:74` と
`docs/notion_integration.md:30` は `NOTION_DB_ID` を `.env` の変数として挙げるが、**設定されていない。**
**本契約の範囲外のため直さない。記録のみ。**

**残る `UNKNOWN`: 件数が「ちょうど 5」であることは測っていない。**
照合したのは配られた 5 つ + `NOTION_DB_ID` の計 6 名だけで、
**一覧に無い名前が他に在るかは確かめていない**（`.env` 本体の読み取りは実行基盤が拒否）。

#### D4 — 効果の見込み（671 行 → 341 行）は測れない

起票者の手順書は版管理の外にある。**このホストから測れない。** `UNKNOWN`。

---

## 検証（Task 1 時点）

    $ make task-validate TASK=T-2026-08-25-issuer-refs-to-repo
    OK   T-2026-08-25-issuer-refs-to-repo

    1 task(s), 0 failed
    exit=0

    $ source .venv/bin/activate && make task-preflight TASK=T-2026-08-25-issuer-refs-to-repo
    P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS tasks/T-2026-08-25-issuer-refs-to-repo/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              WARN 規則 8 件のうち 2 件が該当: separated_source@tasks/T-2026-08-25-issuer-refs-to-repo/SPEC.md:50, forbidden_vs_output@tasks/T-2026-08-25-issuer-refs-to-repo/SPEC.md:260（終了コードは変わらない）

    RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
    exit=0

**SKIP は「合格」ではない。** P2 P3 P4 P5 は実行されていない。

### `conventions_rev` の実測

    $ git --no-pager log -1 --format='%h %ad %s' --date=short -- context/conventions.md
    d422b087 2026-08-07 docs(context): backfill the changelog sha for the frozen-source scope note

    $ grep -n conventions_rev tasks/T-2026-08-25-issuer-refs-to-repo/spec.yaml
    32:  conventions_rev: "d422b08"

**記載と実測が一致している。置換は不要。**

---

## Task 2 Step 1 — 独立した二つを置く

**両方とも 15:08 に版管理外で置かれていた**（Task 1 Step 3）。**作り直していない。**
食い違い D2 のみを直した。

    $ sed -n '86,89p' context/env-facts.md
    - task 手順書は **`.claude/skills/task/SKILL.md`（repo 内）。** 版管理下にあり保守で失われなかった
    - Codex 側の `.codex/skills/task` も**版管理下の symlink**（`../../.claude/skills/task`、commit `19341085`）。
      **解決でき、保守で失われていない**（2026-08-25 philip 実測）。`~/claude-sync/codex/` は**存在しない**
    - Codex のシェルは命令ごとに新しくなる場合がある

`docs/issuer-defects.md` は食い違いが見つからなかった。**無変更で置いた。**

---

## Task 2 Step 2 — 申し送りの節を追加する

### 配布された本文の受領

`issuer-cautions.md` は当初どこにも無かった（D1）。利用者へ提示して受け取った。

    $ ls -la context/issuer-cautions.md
    -rw-rw-r-- 1 ubuntu ubuntu 2348 Aug 25 15:15 context/issuer-cautions.md

**13 項目**。`intent.decision_at_stake` の「十三項目」と一致する。

### D5 — 配られた本文のアンカーは仕組みに一致しない

配られた本文の 1〜2 行目:

    <a id="issuer-cautions"></a>
    ## issuer-cautions

**ハイフンは `_ANCHOR_RE = re.compile(r'<a id="([a-z0-9_]+)"></a>')` に一致しない。**
そのまま連結して実測した。

    $ cat context/conventions.md > $S/hyphen.md; printf '\n' >> $S/hyphen.md
    $ cat context/issuer-cautions.md >> $S/hyphen.md
    $ python -c '<_ANCHOR_RE で走査>' $S/hyphen.md
    配られた本文をそのまま連結した場合のアンカー集合:
    ['env_p0', 'eval_recipe', 'frozen_source', 'naming', 'prohibitions', 'sigma', 'split']
    issuer-cautions が集合に在るか: False
    issuer_cautions が集合に在るか: False
    --- 本文中の実際のアンカー行 ---
    '<a id="split"></a>'
    ...
    '<a id="issuer-cautions"></a>'

**アンカー行は本文に在るのに、集合には入らない。静かに見えなくなる。**
節の数は 7 のままで、**「追加したのに参照できない」壊れ方になる。**

L1 の様式も同じ制約を持つ（`tasks/_schema/spec.schema.json:148`）。

    "items": { "type": "string", "pattern": "^conventions#[a-z0-9_]+(?![\\s\\S])" }

→ **実測を正として `issuer_cautions` へ直した。** 見出しも既存に倣い `## issuer_cautions`
（既存は `## split` `## env_p0` `## frozen_source` のようにアンカー名をそのまま使う）。

### 追加位置 — 空行を挟まないこと

最初は既存の末尾との間に空行を 1 つ入れた。**既存の `naming` 節が変わった。**

    naming  74956a03…  526 B  23 改行     ← 追加前
    naming  65f5b182…  527 B  24 改行     ← 空行を挟んだ追加後

**切り出しは「アンカー → 次の `<a id="`」であり、`naming` は EOF まで伸びている。**
間に置いた空行は `naming` の本文に入る。`git diff` では削除 0 行に見えるが、
**解決される本文は 1 バイト増えていた。** 表示上の差分では捕まらない。

    $ git checkout -- context/conventions.md
    revert: d281e5e30526ab54

空行を挟まずに追加し直した。

---

## Task 2 Step 3 — 既存が無傷であることの確認

節ごとの要約値（切り出し規則は実装と同一）。

    $ diff before.txt <(python sections.py context/conventions.md | head -7)
    （差なし）

| 節 | sha256（本文） | 大きさ | 追加後 |
|---|---|---|---|
| `split` | `1a92c51ab4d579f0…` | 311 B | 同一 |
| `eval_recipe` | `d7542439fc2eccf1…` | 483 B | 同一 |
| `frozen_source` | `0de38e6b0acedc4a…` | 826 B | 同一 |
| `sigma` | `b537ada68a02bb41…` | 903 B | 同一 |
| `prohibitions` | `bc032d4d93e7194e…` | 277 B | 同一 |
| `env_p0` | `e885412c066fbf26…` | 253 B | 同一 |
| `naming` | `74956a03c4828e22…` | 526 B | 同一 |
| `issuer_cautions` | `512f7bf5e84a4489…` | 1012 B | **新規** |

差分は末尾への追加のみ。

    $ git --no-pager diff --numstat context/conventions.md
    35	0	context/conventions.md
    $ git --no-pager diff -U0 context/conventions.md | grep -c '^-[^-]'
    0
    $ git --no-pager diff -U0 context/conventions.md | grep '^@@'
    @@ -143,0 +144,35 @@ …

**削除 0 行。追加 35 行。位置は 143 行の直後（ファイル末尾）。**

### 変更履歴へは追記していない

`context/conventions.md:7` は追記を求めるが、**変更履歴は `naming` 節の本文の内側**であり、
行を足せば `naming` の解決結果が変わる。SPEC 禁止 1 と両立しない。**禁止 1 を優先した。**

---

## Task 2 Step 4 — 注入が働くことの確認（両方向）

本契約自身の `inject_verbatim` を差し替えて、`make task-validate` の終了コードを見た。

**注意**: 最初 `${PIPESTATUS[0]}` で終了コードを取ろうとして**空になった**。
対話シェルは zsh で配列添字が使えない（`context/env-facts.md:35`、
`docs/issuer-defects.md:20` に既出の罠）。`out=$(...); ec=$?` に直して取り直した。

    ===== 対照 A (陽性・既存のみ) =====
      inject_verbatim: [conventions#prohibitions]
      OK   T-2026-08-25-issuer-refs-to-repo
      1 task(s), 0 failed
      exit=0

    ===== 対照 B (陽性・新規を追加) =====
      inject_verbatim: [conventions#prohibitions, conventions#issuer_cautions]
      OK   T-2026-08-25-issuer-refs-to-repo
      1 task(s), 0 failed
      exit=0

    ===== 対照 C (陰性・綴り違い) =====
      inject_verbatim: [conventions#prohibitions, conventions#issuer_cautionz]
      FAIL T-2026-08-25-issuer-refs-to-repo
        [L2-5] contract.inject_verbatim: アンカー issuer_cautionz が存在しません
      1 task(s), 1 failed
      exit=2

    ===== 対照 D (陰性・配られたハイフン形) =====
      inject_verbatim: [conventions#prohibitions, conventions#issuer-cautions]
      FAIL T-2026-08-25-issuer-refs-to-repo
        [L1-1] contract.inject_verbatim.1: 'conventions#issuer-cautions' does not match '^conventions#[a-z0-9_]+(?![\s\S])'
      1 task(s), 1 failed
      exit=2

**陰性が 2 種類とも落ちた。「常に成功を返す」壊れ方ではない。**
**C は L2 で、D は L1 で落ちる。層が違う。**

### 中身が取れること

    conventions#prohibitions           ->   277 B / 空でない=True / sha256=bc032d4d93e7194e
    conventions#issuer_cautions        ->  1012 B / 空でない=True / sha256=512f7bf5e84a4489
    conventions#issuer_cautionz        -> 解決しない（None）

    === conventions#issuer_cautions の原文（先頭 12 行）===
      |
      |## issuer_cautions
      |
      |**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
      |実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**
      |
      || # | 注意 |
      ||---|---|
      || 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
      || 2 | 一致 0 件なら別の異質な方法でも確認する |
      || 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
      || 4 | 仕組みの挙動は実装を読んでから信じる |
      … 全 35 行

**表がそのまま取れている。字下げも保たれる。** 切り出しは生のスライスである。

`spec.yaml` の最終状態:

    31:  inject_verbatim: [conventions#prohibitions, conventions#issuer_cautions]
