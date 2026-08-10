# 契約の配布を外部の共有台帳経由にし、実行時に取り込めるようにする

**task_id:** `T-2026-08-12-contract-distribution-via-notion`
**kind:** `impl`
**depends_on:** `T-2026-08-11-canonical-index-refresh`

---

## Goal

契約は現在、起票者が作った本文を人が貼り付けて渡している。**端末が使えない状況では
この経路が成立しない。**

一方、実行ホストには既に外部の共有台帳へ到達する資格情報と実装がある。

| 既存資産 | 内容 |
|---|---|
| 資格情報 | `NOTION_API_KEY`（`.env.gpg` に格納、`scripts/load_env.sh` が読む） |
| 識別子の登録簿 | `configs/notion.yaml`（非秘密・追跡下） |
| 読み書きの実装 | `src/egosurgery/utils/notion_logger.py` / `notion_ops.py` |

**起票者も同じ台帳へ書き込める。** 両側が到達できる共有ストアが既に存在していた。

## 配布先（起票者が作成済み）

| 項目 | 値 |
|---|---|
| 名前 | TASK配布 |
| database id | `3af70553-8f2d-45de-972a-c64b3127bb1a` |
| data source id | `b6ae4844-d6b8-433f-a07a-3882a534c9eb` |
| 親 | M2研究運用ハブ |

列は次のとおり。

| 列 | 型 | 用途 |
|---|---|---|
| `task_id` | title | **行の特定に使う** |
| `status` | select | distributed / fetched / done / superseded |
| `kind` | select | impl / exp / analysis |
| `issued_at` | date | 起票日 |
| `sha256` | text | **本文の要約値。往復の忠実性の照合に使う** |
| `bytes` | number | 本文のバイト数 |
| `target_host` | text | 実行を想定するホストの論理名 |
| `note` | text | 補足 |

**本文（バンドル全文）はページ本体に置く。**

## 目指す動作

```
起票者が台帳へ行を作る
      ↓（待ち時間なし）
実行者が識別子だけを与える
      ↓
手元に無ければ台帳から取得 → 既存の取り込み経路で検証 → 実行
```

**常駐処理による定期取得は行わない。** 人が起動した時点で取りに行く。

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git fetch origin
git checkout -b feat/notion-distribution origin/phase0
source .venv/bin/activate
source scripts/load_env.sh
```

| # | 禁止 |
|---|---|
| 1 | **資格情報を出力・記録する**（存在と有無のみ扱う） |
| 2 | 台帳の既存の行や他の管理データベースを変更・削除する |
| 3 | `runindex/**` `context/auto/**` を手で編集する |
| 4 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 5 | `context/conventions.md` を変更する |
| 6 | 学習・評価コードを変更する |
| 7 | 演算装置を使う |
| 8 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 9 | 統合する。自動統合を有効化する |

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが **10 task 連続**で発生している。
また実行環境の対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲むこと。**

**本 SPEC の検査も同型の誤りを含みうる。** 次を守ること。

| # | 注意 |
|---|---|
| 1 | 一致件数が 0 のとき、別の探し方でも 0 になることを確かめる |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 4 | 検査が空振りでないことを陽性対照で確かめる |

### 本 task に固有の危険

**外部サービスが本文を改変する可能性がある。** 見た目が同じでも、空白の除去・引用符の
変換・全角化・分割の境界で内容が変わりうる。**Phase B が通らなければ、この経路は使えない。**
その場合は素直に停止し、貼り付けによる配布を続ける。

---

# Phase A — 到達性の確認

## Task 1: 実行ホストの資格情報で台帳を読めるか

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 既存の実装を読む**

**推測で API を書かない。既存の呼び出し方に揃える。**

```bash
sed -n '1,60p' src/egosurgery/utils/notion_logger.py
grep -n "_API_BASE\|NOTION_VERSION\|headers\|Authorization" src/egosurgery/utils/notion_logger.py | head -20
sed -n '1,40p' configs/notion.yaml
```

**API の版・基底 URL・見出しの作り方を実装から取る。**

- [ ] **Step 2: 資格情報が読み込まれているか確認する**

**値を出さない。有無だけを見る。**

```bash
python - <<'PY'
import os
k = os.environ.get("NOTION_API_KEY", "")
print("NOTION_API_KEY:", "設定あり" if k else "未設定", f"(長さ {len(k)})" if k else "")
PY
```

**未設定なら `source scripts/load_env.sh` を実行してから再確認する。**
それでも未設定なら停止して報告する。

- [ ] **Step 3: 台帳へ到達できるか実測する**

```bash
python - <<'PY'
import json, os, urllib.request

DS = "b6ae4844-d6b8-433f-a07a-3882a534c9eb"
DB = "3af70553-8f2d-45de-972a-c64b3127bb1a"
key = os.environ.get("NOTION_API_KEY", "")
if not key:
    raise SystemExit("資格情報が未設定")

def call(url, body=None):
    req = urllib.request.Request(
        url, method="POST" if body is not None else "GET",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {key}",
                 "Notion-Version": "2022-06-28",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

for label, url in [("database 取得", f"https://api.notion.com/v1/databases/{DB}")]:
    st, body = call(url)
    print(f"{label}: HTTP {st}", body.get("code", ""), body.get("message", "")[:120])

st, body = call(f"https://api.notion.com/v1/databases/{DB}/query", {"page_size": 5})
print("query:", f"HTTP {st}", body.get("code", ""), body.get("message", "")[:120])
if st == 200:
    print("行数:", len(body.get("results", [])))
PY
```

**API の版は Step 1 で読んだ値に合わせること。** 上の `2022-06-28` は既存実装からの推定で
あり、**食い違えば実装に従う。**

- [ ] **Step 4: G1 ゲート — 判定する**

| 観測 | 対応 |
|---|---|
| HTTP 200 | Phase B へ |
| HTTP 404 | **台帳が Integration へ共有されていない。** 利用者へ共有操作を依頼して停止 |
| HTTP 401 | 資格情報が無効。停止して報告 |
| その他 | 応答をそのまま記録して停止 |

**404 の場合の依頼文を報告に含めること。** 利用者は Notion の画面で
「接続」から Integration を追加する必要がある。

`ledger_unreachable` として報告する。

---

# Phase B — 往復の忠実性

## Task 2: 書いた内容がそのまま読めるかを実測する

**Files:** なし（台帳へ一時的な行を作り、確認後に印を付ける）

**これが本 task の成否を決める。**

- [ ] **Step 1: 検査用の本文を作る**

**壊れやすい要素を意図的に含める。**

| 要素 | 理由 |
|---|---|
| 行末の空白 | 除去されやすい |
| 連続する空行 | まとめられやすい |
| 半角の引用符とバッククォート | 変換されやすい |
| 長い区切り文字 | 分割の境界に当たりやすい |
| 2000 字を超える連続した本文 | **分割が必要になる** |
| 日本語と英数字の混在 | 全角化の検出 |
| markdown の記号（`#` `-` `|`） | 書式として解釈されやすい |

```bash
python - <<'PY'
import hashlib, pathlib, secrets

delim = "PROBEDELIM" + secrets.token_hex(20).upper()
lines = [f"#!TASK-BUNDLE v1 delim={delim}", f"{delim} FILE probe.txt"]
lines.append("行末に空白がある行   ")
lines.append("")
lines.append("")
lines.append('引用符 " と \' とバッククォート ` を含む行')
lines.append("記号 # - | * _ ~ > を含む行")
lines.append("日本語と ASCII が mixed な行 12345")
# 2000 字を超える塊
lines.append("A" * 2500)
lines.append("".join(f"{i%10}" for i in range(2500)))
lines.append(f"{delim} END")
text = "\n".join(lines) + "\n"

p = pathlib.Path("/tmp/probe_bundle.txt")
p.write_text(text, encoding="utf-8")
print("バイト数:", len(text.encode()))
print("行数:", text.count("\n"))
print("sha256:", hashlib.sha256(text.encode()).hexdigest())
print("delim:", delim)
PY
```

**記録を作る流れに表示用の切り詰めを混ぜていない。**

- [ ] **Step 2: 台帳へ書き込む**

**本文をページ本体へ入れる。** 書式として解釈されないよう、**コードブロックへ入れる**。
2000 字の制限があるため**分割が必要**である。分割の方法を実装から決める。

```bash
grep -n "rich_text\|children\|paragraph\|code" src/egosurgery/utils/notion_ops.py | head -20
```

行の `task_id` は `T-2026-08-12-probe-roundtrip` とし、`status` は `superseded` にする。
**本番の契約と混ざらないようにする。**

`sha256` と `bytes` の列に Step 1 の値を入れる。

- [ ] **Step 3: 読み戻して照合する（G2）**

```bash
python - <<'PY'
import hashlib, pathlib
# 台帳から読み戻した本文を /tmp/probe_readback.txt へ保存してから実行する
orig = pathlib.Path("/tmp/probe_bundle.txt").read_bytes()
back = pathlib.Path("/tmp/probe_readback.txt").read_bytes()
print("元    :", len(orig), "bytes", hashlib.sha256(orig).hexdigest()[:16])
print("読戻し:", len(back), "bytes", hashlib.sha256(back).hexdigest()[:16])
print("一致  :", orig == back)
if orig != back:
    import difflib
    a = orig.decode("utf-8", "replace").splitlines()
    b = back.decode("utf-8", "replace").splitlines()
    for i, line in enumerate(difflib.unified_diff(a, b, lineterm="", n=1)):
        if i > 40:
            print("...")
            break
        print(line)
PY
```

Expected: **一致 True**

**一致しなければ、何がどう変わったかを記録して停止する**（`roundtrip_mismatch`）。

| 差の種類 | 対処の候補 |
|---|---|
| 行末の空白が消える | 本文を符号化してから格納する |
| 空行がまとまる | 同上 |
| 引用符が変換される | 同上 |
| 分割の境界で欠ける | 分割と再結合の実装を直す |

**符号化（base64 など）へ切り替える判断は、差の内容を見てから利用者へ提示する。**
勝手に方式を変えない。

- [ ] **Step 4: 検査が空振りでないことを確かめる**

**陽性対照を置く。**

```bash
python - <<'PY'
import hashlib, pathlib
orig = pathlib.Path("/tmp/probe_bundle.txt").read_bytes()
tampered = orig.replace(b"12345", b"12346", 1)
print("改変を検出できるか:", hashlib.sha256(orig).hexdigest() != hashlib.sha256(tampered).hexdigest())
PY
```

Expected: `True`

**False なら照合が無効である。** 停止して報告する。

---

# Phase C — 取り込み経路

## Task 3: 識別子だけで取り込めるようにする

**Files:**
- Modify: `tools/fetch_task.py`
- Modify: `Makefile`
- Modify: `configs/notion.yaml`
- Create: `tests/test_fetch_task_notion.py`

- [ ] **Step 1: 登録簿へ追記する**

`configs/notion.yaml` の `databases` に配布先を足す。**秘密は書かない。**

```yaml
  task_distribution: 3af70553-8f2d-45de-972a-c64b3127bb1a   # TASK配布（契約の受け渡し）
```

**コード内へ識別子を直書きしない。** 登録簿を単一の情報源とする既存方針に従う。

- [ ] **Step 2: 失敗する試験を書く**

```python
# tests/test_fetch_task_notion.py
# 外部サービスへは接続しない。応答を差し替えて経路だけを検査する。
```

最低限、次を検査する。

| # | 検査 |
|---|---|
| 1 | 識別子で行を特定できる |
| 2 | 見つからない識別子は明確な理由で失敗する |
| 3 | 要約値が一致しない本文は**受け付けずに失敗する** |
| 4 | 資格情報が未設定なら明確な理由で失敗する |
| 5 | 取得した本文は既存の取り込み経路へ渡される（**巻き戻しの実装を複製しない**） |

**3 が重要である。** 台帳が本文を改変した場合、要約値の不一致で検出できなければ
壊れた契約を取り込むことになる。

- [ ] **Step 3: 実装する**

```
python tools/fetch_task.py --notion <task_id>
```

要件は次のとおり。

| # | 要件 |
|---|---|
| 1 | 登録簿から配布先の識別子を読む |
| 2 | 資格情報が無ければ**明確な理由で失敗**する。黙って進まない |
| 3 | 識別子で行を照会し、本文を取得する |
| 4 | 取得した本文の要約値を計算し、**列の値と照合する** |
| 5 | 一致しなければ受け付けずに失敗する |
| 6 | 一致すれば**既存の取り込み経路へ渡す**（検証と巻き戻しを再利用） |
| 7 | 資格情報を出力しない |
| 8 | 頁送りに対応する（本文が複数の塊に分かれる） |

**要件 6 を守ること。** 取り込みと検証と巻き戻しは既に実装がある。**複製しない。**

- [ ] **Step 4: Makefile へ足す**

**挿入位置に注意。** 既存レシピの途中へ入れない。

```makefile
.PHONY: task-notion
task-notion:
	@.venv/bin/python tools/fetch_task.py --notion $(TASK)
```

- [ ] **Step 5: G3 ゲート — 実地で確認する**

**陽性対照を含める。**

```bash
BEFORE=$(ls -1d tasks/T-* | wc -l)

echo "===== 存在しない識別子 ====="
make task-notion TASK=T-2099-01-01-no-such-task; echo "exit=$?"

echo "===== 資格情報を外した場合 ====="
env -u NOTION_API_KEY make task-notion TASK=T-2026-08-12-probe-roundtrip; echo "exit=$?"

echo "===== 要約値が合わない場合 ====="
（台帳の probe 行の要約値を一時的に誤った値にして実行し、拒否されることを確認する。
　確認後は元へ戻す）

AFTER=$(ls -1d tasks/T-* | wc -l)
echo "before=$BEFORE after=$AFTER"
git status --porcelain tasks/
```

Expected: **すべて非ゼロで終了**し、件数が不変、作業領域が清潔

**一つでも成功する、または痕跡が残る場合は停止して報告する。**

---

# Phase D — 手順書と自己契約

## Task 4: 実行時に自動で取得させる

**Files:**
- Modify: `.claude/skills/task/SKILL.md`
- Modify: `tasks/README.md`

- [ ] **Step 1: 解決の手順へ足す**

`SKILL.md` の最初の段階（契約の解決）に、次を加える。

```markdown
契約が `tasks/<task_id>/` に無い場合、配布台帳から取得する。

    make task-notion TASK=<task_id>

取得と検証までを行う。失敗したらそこで停止し、出力をそのまま報告する。
**本文の要約値が一致しない場合は取り込まない。** 台帳が本文を改変した可能性がある。
```

**`.codex/skills/task` は symlink なので、1 箇所の更新で両方に反映される。**

- [ ] **Step 2: 受け渡しの説明を更新する**

`tasks/README.md` の「契約の受け取り」節へ、3 つ目の経路として加える。

```markdown
起票者が配布台帳へ置いた契約は、識別子だけで取り込める。

    make task-notion TASK=<task_id>

端末を操作できない場合の主経路である。貼り付けを必要としない。
```

- [ ] **Step 3: 検査用の行を片付ける**

Phase B で作った行の `status` を `superseded` にし、**削除はしない**。
往復の忠実性の証拠として残す。

- [ ] **Step 4: commit**

---

## Task 5: 完了判定と起票

**Files:**
- Create: `tasks/T-2026-08-12-contract-distribution-via-notion/RESULT.md`
- Create: `tasks/inbox.d/T-2026-08-12-contract-distribution-via-notion.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-12-contract-distribution-via-notion; echo "exit=$?"
make task-preflight TASK=T-2026-08-12-contract-distribution-via-notion; echo "exit=$?"
make inbox; make inbox-check; echo "exit=$?"
```

- [ ] **Step 3: 完了判定**

| # | 判定 | 期待 |
|---|---|---|
| 1 | 台帳へ到達できる | HTTP 200 |
| 2 | 往復で内容が変わらない | 要約値が一致 |
| 3 | 照合が空振りでない | 陽性対照が検出する |
| 4 | 識別子だけで取り込める | 成功する |
| 5 | 存在しない識別子を拒む | 非ゼロ |
| 6 | 資格情報が無いとき拒む | 非ゼロ |
| 7 | 要約値が合わないとき拒む | 非ゼロ |
| 8 | 失敗時に痕跡が残らない | 件数不変・作業領域が清潔 |
| 9 | 巻き戻しを複製していない | 既存経路を呼んでいる |
| 10 | 資格情報が出力に無い | 検査で 0 件 |
| 11 | 手順書が新しい経路を指す | 該当あり |
| 12 | 登録簿に配布先がある | 1 件 |
| 13 | 契約検証が通る | exit 0 |
| 14 | 実行前検査が通る | exit 0 |
| 15 | 試験が不変 | **開始前を先に測る** |
| 16 | 禁止領域が無変更 | 出力なし |

**判定10の検査では、何に一致したかを目視する。** 過去に無関係な語への一致で偽陽性が出ている。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- 台帳への到達性（HTTP の応答。**共有が必要だった場合はその旨**）
- **往復の忠実性の結果。一致しなかった場合は差の内容**
- 分割と再結合の方法
- 本文の格納形式（そのままか、符号化したか。**符号化した場合は理由**）
- 陽性対照の結果
- **`deviations` を空にしない**
- §6 に、貼り付けによる配布を残すかどうかの所見

- [ ] **Step 5: 起票**

```bash
git add tasks/ tools/ tests/ Makefile configs/notion.yaml .claude/
git commit -m "feat(tasks): distribute contracts through the shared ledger"
git push -u origin feat/notion-distribution
gh pr create --base phase0 \
  --title "feat(tasks): fetch contracts from the distribution ledger by task_id" \
  --body-file tasks/T-2026-08-12-contract-distribution-via-notion/RESULT.md
```

**統合しない。自動統合も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 台帳が 404 | **共有されていない。** 利用者へ依頼文を提示して停止 |
| 資格情報が 401 | 停止して報告。**再発行はしない**（利用者の操作領域） |
| 往復で内容が変わる | **G2 停止。** 差の内容を記録し、符号化の可否を提示する |
| 分割の境界で欠ける | 実装を直して再測定。**推測で境界を決めない** |
| 照合が空振りする | その検査は無効。停止して報告 |
| 既存の取り込み経路を再利用できない | **停止して報告。** 巻き戻しを複製しない |
| 資格情報が出力に混ざった | **即座に停止。** `secret_value_printed` |
| 試験の failed が開始前より増えた | 本 task が壊した。停止して報告 |
