# 計算機の論理名を注入し、外部記録との対応を索引へ載せ、収穫の範囲を明らかにする

**task_id:** `T-2026-08-11-identity-tracking-and-harvest-scope`
**kind:** `impl`
**depends_on:** `T-2026-08-10-branch-naming-and-canonical-index`
**実行ホスト:** `bengio`（分岐 `exp/bengio`）

---

## Goal

先行調査と別ホストでの実測により、3 つの未解決事項が判明している。

| # | 事項 | 実測された内容 |
|---|---|---|
| 1 | 実行元の識別子が重複する | 隔離環境で 2 台が同じ生の識別子を返す。索引の 10 行で正規化後が空 |
| 2 | 外部記録と証跡が結ばれていない | 索引に外部記録の識別子に相当する列が無い |
| 3 | 収穫が無視設定と一致しない | 無視設定済みのディレクトリ 37 件を収穫器が拾った |

**1 と 2 を仕組みで解決し、3 は起票して記録する。**

あわせて、対話記録の抽出物の追跡方針が未確定のまま残っており、**生成のたびに作業ツリーが
汚れる**状態になっている。これを確定させる。

## 判明している事実（推測ではない）

| 項目 | 実測値 |
|---|---|
| 識別子の解決順 | 環境変数 2 つ、設定の項目、最後に système の呼び出し |
| 索引の該当行 | 生の値が 10 行、正規化後は全て空 |
| 外部記録の設定 | 既定は無効。特定の段階の設定でのみ有効 |
| 資格情報 | 暗号化された設定と読込み入口が存在 |
| 収穫器の走査 | 版管理の無視設定を参照しない |

**上記は先行調査の実測である。実装を読んで確かめてから使うこと。**

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git branch --show-current    # exp/bengio
git fetch origin
git checkout -b feat/identity-and-tracking origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **既存の索引の数値を変える** |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |
| 3 | 学習・評価コードの動作を変える（**列の追加に必要な最小限を除く**） |
| 4 | `context/conventions.md` を変更する |
| 5 | **秘匿値を出力・記録する** |
| 6 | 外部サービスへ問い合わせる。過去の記録を遡って対応づける |
| 7 | 演算装置を使う |
| 8 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 9 | 統合する。自動統合を有効化する |
| 10 | **他ホストの設定を変更する** |

### 並行して進む作業との衝突を避ける

別ホストで退避物の処置が並行して進んでいる。**次には触らないこと。**

- `experiments/` 配下の既存ディレクトリ
- `runindex/` の記録（**再生成して確認するのは可。記録はしない**）

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが 8 task 連続で発生している。
直近では、常駐スクリプトへの検索が空を返したのを「該当なし」と扱った。

**本 SPEC の検査も同型の誤りを含みうる。** 次の点に注意すること。

| # | 注意 |
|---|---|
| 1 | 一致件数が 0 のとき、別の探し方でも 0 になることを確かめる |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 表への追記は列数を数えてから書く |
| 4 | 秘匿の検査では、何に一致したのかを目視する |

---

# Phase A — 論理名の注入

## Task 1: 解決順を実装から確かめる

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 実装を読む**

```bash
grep -rn "SERVERNAME\|EGOSURGERY_SERVER_NAME\|server_name\|gethostname" \
  src/ tools/ configs/ --include='*.py' --include='*.yaml' | head -30
```

**解決の順序と、どの段階でどの値が使われるかを実装から確かめる。**
先行調査の記述と食い違えば、**実装に従い記録する。**

- [ ] **Step 2: 証跡へ書かれる経路を読む**

```bash
grep -rn "server.txt" src/ tools/ --include='*.py' | head -10
grep -rn "host_raw\|host" tools/harvest_runindex.py | head -20
```

**証跡に書く側と、索引で正規化する側の両方を読む。**

- [ ] **Step 3: 現在の値を測る**

```bash
echo "SERVERNAME=[${SERVERNAME:-未設定}]"
echo "EGOSURGERY_SERVER_NAME=[${EGOSURGERY_SERVER_NAME:-未設定}]"
hostname
python - <<'PY'
import socket
print("gethostname:", socket.gethostname())
PY
```

- [ ] **Step 4: 索引の分布を確かめる**

```bash
python - <<'PY'
import csv, collections
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
hc = [c for c in cols if any(k in c.lower() for k in ("host", "server"))]
print("該当列:", hc)
for c in hc:
    print(f"--- {c} ---")
    for k, v in collections.Counter(r.get(c, "") for r in rows).most_common(15):
        print(f"  {k or '(空)'}: {v}")
PY
```

---

## Task 2: 注入する手順を用意する

**Files:**
- Create または Modify: 常駐設定の導入を担う仕組み
- Modify: `README.md` の該当節（**運用手順のみ**）

**他ホストの設定は変更しない。手順とスクリプトを用意するだけである。**

- [ ] **Step 1: 既存の導入手順を読む**

```bash
sed -n '1,60p' scripts/sync/setup_host_autosync.sh
grep -n "export\|environment\|bashrc\|zshrc\|profile" scripts/sync/setup_host_autosync.sh | head -20
```

**環境変数を設定する既存の仕組みがあるかを確かめる。** あればそこへ足す。
無ければ独立した手順を作る。**推測で場所を決めない。**

- [ ] **Step 2: 注入の手順を実装する**

要件は次のとおり。

| # | 要件 |
|---|---|
| 1 | 論理名を引数で受け取り、妥当性を検査する（小文字英数とハイフン、2 文字以上 20 文字以下） |
| 2 | 対話シェルと非対話シェルの**両方**で有効になる場所へ書く |
| 3 | 既に同じ値が設定されていれば何もしない |
| 4 | 既に**異なる値**が設定されていれば、**上書きせず警告して終了する** |
| 5 | 空実行を用意する |
| 6 | 設定後に、実際に読めることを確認する |

**要件 2 が重要である。** 実測により、非対話シェルでは利用者の設定ファイルが
読まれないことが分かっている。学習は対話シェルから起動されるとは限らない。
**どこへ書けば両方で有効になるかを実測してから決める。**

- [ ] **Step 3: G1 ゲート — 設定の有無で値が変わることを確認する**

**陽性対照を置く。** 未設定のときと設定したときの両方を測る。

```bash
echo "===== 未設定のとき ====="
env -u SERVERNAME -u EGOSURGERY_SERVER_NAME python - <<'PY'
# 証跡へ書く関数を実装から特定して呼ぶ。無ければ解決順を再現する
import os, socket
print("解決結果:", os.environ.get("SERVERNAME") or os.environ.get("EGOSURGERY_SERVER_NAME") or socket.gethostname())
PY

echo "===== 設定したとき ====="
SERVERNAME=probe-host python - <<'PY'
import os, socket
print("解決結果:", os.environ.get("SERVERNAME") or os.environ.get("EGOSURGERY_SERVER_NAME") or socket.gethostname())
PY
```

**上は解決順の再現にすぎない。** 実際に証跡へ書く関数を呼べる場合は呼び、
その出力を記録する。**呼べない場合は、その旨を記録する。**

Expected: 未設定では計算機の名前、設定時は指定した値

**変わらなければ停止して報告する。**

- [ ] **Step 4: 空実行と誤入力を確認する**

```bash
# 不正な入力を拒むこと
for n in "Bengio" "a" "b engio" "bengio;rm -rf /" ""; do
  printf "%-20s " "$n"
  bash <導入スクリプト> --dry-run "$n" >/dev/null 2>&1 && echo "受理（要確認）" || echo "拒否"
done
```

**すべて拒否されること。** 一つでも受理されたら修正する。

- [ ] **Step 5: 自ホストへ適用する**

**自ホストのみ。他ホストへは適用しない。**

```bash
bash <導入スクリプト> bengio
echo "確認: SERVERNAME=[${SERVERNAME:-未設定}]"
# 新しいシェルで読めるかも確認する
bash -lc 'echo "対話: $SERVERNAME"'
bash -c 'echo "非対話: $SERVERNAME"'
```

**非対話シェルでも読めることを確認する。**

- [ ] **Step 6: 手順を文書化する**

`README.md` の運用手順の節へ、各ホストで実行する手順として記す。
**過去の記録には触れない。**

- [ ] **Step 7: commit**

---

# Phase B — 外部記録との対応

## Task 3: 識別子を証跡へ書く

**Files:**
- Modify: `src/egosurgery/utils/tracking.py`（または実測で特定した箇所）

**遡って対応づけない。今後の run から結ばれるようにする。**

- [ ] **Step 1: 外部記録の初期化を読む**

```bash
sed -n '1,80p' src/egosurgery/utils/tracking.py
grep -rn "wandb.init\|wandb_enabled\|\.id\b\|get_url" src/egosurgery/ --include='*.py' | head -20
```

**識別子と参照先を取得できる箇所を特定する。**

- [ ] **Step 2: 証跡へ書く**

外部記録が有効なとき、その識別子と参照先を証跡へ書く。
**無効なときは何も書かない。** 空文字も書かない。

| 要件 | 内容 |
|---|---|
| 1 | 有効なときのみ書く |
| 2 | 資格情報そのものは書かない |
| 3 | 失敗しても学習を止めない |
| 4 | 書く場所は既存の証跡の様式に合わせる |

**要件 3 が重要である。** 外部サービスが落ちていても学習は続くべきである。

- [ ] **Step 3: 失敗する試験を書く**

```python
# tests/test_tracking_ids.py
def test_records_identifier_when_enabled():
    """外部記録が有効なとき、識別子が証跡へ渡る。"""


def test_records_nothing_when_disabled():
    """無効なときは何も書かない。空文字も書かない。"""


def test_failure_does_not_stop_training():
    """外部記録の取得に失敗しても例外を投げない。"""


def test_no_credentials_in_output():
    """資格情報が出力に含まれない。"""
```

**実装を読んでから、呼び出せる形で書くこと。** 外部サービスへは接続しない。

---

## Task 4: 索引へ列を足す

**Files:**
- Modify: `tools/harvest_runindex.py`

- [ ] **Step 1: 既存の列の追加方法を読む**

```bash
grep -n "COLUMNS\|fieldnames\|columns" tools/harvest_runindex.py | head -20
```

**既存の様式に合わせる。** 独自の方法を持ち込まない。

- [ ] **Step 2: 列を足す**

| 要件 | 内容 |
|---|---|
| 1 | 証跡に識別子があれば読む |
| 2 | 無ければ空にする |
| 3 | **既存の行の他の列を変えない** |
| 4 | 列の順序は末尾に足す |

- [ ] **Step 3: G2 ゲート — 有無で挙動が変わることを確認する**

```bash
BEFORE_ROWS=$(( $(wc -l < runindex/index.csv) - 1 ))
python - <<'PY'
import csv, hashlib
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
key = next((c for c in rows[0] if c.endswith("ledger_key")), None)
h = hashlib.sha256()
for r in sorted(rows, key=lambda x: x.get(key, "")):
    for k in sorted(r):
        h.update(f"{k}={r[k]}".encode())
print("既存内容の指紋:", h.hexdigest()[:16])
print("行数:", len(rows), "列数:", len(rows[0]))
PY

make runindex 2>&1 | tail -10

AFTER_ROWS=$(( $(wc -l < runindex/index.csv) - 1 ))
echo "行数: $BEFORE_ROWS -> $AFTER_ROWS"
python - <<'PY'
import csv, hashlib
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
key = next((c for c in rows[0] if c.endswith("ledger_key")), None)
newcols = [c for c in rows[0] if any(k in c.lower() for k in ("wandb", "tracking", "run_url", "run_id"))]
print("追加された列:", newcols)
h = hashlib.sha256()
for r in sorted(rows, key=lambda x: x.get(key, "")):
    for k in sorted(r):
        if k in newcols:
            continue
        h.update(f"{k}={r[k]}".encode())
print("既存内容の指紋:", h.hexdigest()[:16])
print("新しい列が空でない行:", sum(1 for r in rows if any(r.get(c) for c in newcols)))
PY
```

Expected: 行数が不変、**既存内容の指紋が一致**、新しい列が全行で空

**指紋が変われば停止して報告する**（`existing_index_values_changed`）。

**遡及していないので、新しい列は全行で空になるのが正しい。** 空でない行があれば、
どこから値が来たのかを調べて報告する。

- [ ] **Step 4: 索引を元へ戻す**

```bash
git checkout -- runindex/ context/auto/ 2>/dev/null
git status --porcelain | grep -E "runindex/|context/auto/" && echo "戻しきれていない" || echo "復元済み"
```

**索引は記録しない。** 正本は別の機会に、条件を満たすホストで生成する。

- [ ] **Step 5: commit**

---

# Phase C — 収穫の範囲と記録方針

## Task 5: 収穫と無視設定の不一致を起票する

**Files:**
- Modify: `tools/harvest_runindex.py`（未解決事項の一覧のみ）

別ホストでの実測により、**無視設定済みのディレクトリ 37 件を収穫器が拾った**ことが
確認されている。収穫器はファイルシステムを直接走査し、版管理の無視設定を参照しない。

- [ ] **Step 1: 自ホストで再現するか確かめる**

```bash
echo "===== 無視されている実験ディレクトリ ====="
git status --porcelain --ignored experiments/ 2>/dev/null | grep '^!!' | head -20
git status --porcelain --ignored experiments/ 2>/dev/null | grep -c '^!!'
```

**別ホストの結果を持ち込まない。自ホストで測る。**

- [ ] **Step 2: 採番の衝突を避ける**

```bash
git fetch origin
for ref in $(git for-each-ref --format='%(refname)' refs/remotes/origin | grep -v HEAD); do
  n=$(git show "$ref:tools/harvest_runindex.py" 2>/dev/null | grep -oE 'B-[0-9]+' | sed 's/B-//' | sort -n | tail -1)
  [ -n "$n" ] && printf "%-50s B-%s\n" "$ref" "$n"
done | sort -k2 -V | tail -5
```

**引用符の有無に依存しない探し方をしている。** 実表記を確認してから採番する。

- [ ] **Step 3: 起票する**

**本文に半角パイプを書かない。列数を数えてから書く。**

内容の要点。

| 項目 | 内容 |
|---|---|
| 事象 | 収穫器がファイルシステムを直接走査し、版管理の無視設定を参照しない |
| 影響 | 無視設定は索引を保護しない。過去に追加した無視設定は作業ツリーにのみ効く |
| 実測 | 別ホストで 37 件、自ホストで（実測値） |
| 対処案 | 走査時に無視設定を参照する案、除外規約へ移す案、正本ホストの条件で担保する案 |

**3 案以上を挙げ、選ばない。**

- [ ] **Step 4: 構文と表の整合を確認する**

```bash
python -m py_compile tools/harvest_runindex.py && echo "構文 OK"
python - <<'PY'
import re, pathlib
src = pathlib.Path("tools/harvest_runindex.py").read_text(encoding="utf-8")
m = re.search(r"^BACKLOG\s*=\s*", src, re.M)
seg = src[m.start():] if m else ""
rows = [ln for ln in seg.splitlines() if ln.strip().startswith("|")]
cols = {ln.count("|") for ln in rows}
print("表の行数:", len(rows), "区切りの種類:", cols)
assert len(cols) <= 1, f"列数が揃っていない: {cols}"
print("列数 OK")
PY
```

- [ ] **Step 5: 再生成で索引が壊れないことを確認する**

```bash
md5sum runindex/*.csv > /tmp/bl_before.txt
make runindex >/dev/null 2>&1
md5sum runindex/*.csv > /tmp/bl_after.txt
diff /tmp/bl_before.txt /tmp/bl_after.txt && echo "不変" || echo "変化した"
git checkout -- runindex/ context/auto/ 2>/dev/null
```

**Phase B で列を足しているため、列は増える。** 行数と既存の値が変わらないことを見る。

- [ ] **Step 6: commit**

---

## Task 6: 対話記録の抽出物の追跡方針

**Files:**
- Modify: `docs/sessions/README.md`
- Modify: `tasks/README.md`

抽出物は生成のたびに作業ツリーを汚し、**自動統合を妨げる**。方針が未確定のまま
放置されている。

**方針: 記録する。** 機械抽出のテキストであり量が小さく、他ホストから検索できる価値がある。

- [ ] **Step 1: 現状を測る**

```bash
ls -1 docs/sessions/digest/ | wc -l
du -sh docs/sessions/digest/
git ls-files docs/sessions/digest/ | wc -l
git status --porcelain docs/sessions/ | head
```

**追跡済みと未追跡の件数を分けて記録する。**

- [ ] **Step 2: 方針を文書化する**

```markdown
## 抽出物の扱い

対話記録の抽出物は**版管理へ記録する。**

機械抽出のテキストであり、会話本文も要約も含まない。量が小さく、
他のホストからも検索できる価値がある。

生成のたびに作業ツリーへ現れるため、**次の契約の記録と一緒に含める。**
放置すると自動統合が止まる。

    git add docs/sessions/digest/
```

- [ ] **Step 3: 未追跡の抽出物を記録する**

```bash
git add docs/sessions/digest/
git status --porcelain docs/sessions/
```

**内容に秘匿が含まれないことを確認してから記録する。**

```bash
git diff --cached docs/sessions/digest/ | \
  grep -nE "(API[_-]?KEY|SECRET|TOKEN|PASSWORD)[\"'[:space:]]*[:=]" | head
echo "（一致があれば、何に一致したかを目視すること）"
```

- [ ] **Step 4: G3 ゲート**

`on_fail: ask` である。**判断が要る場合は提示して仰ぐ。**

- [ ] **Step 5: commit**

---

## Task 7: 自己契約と起票

**Files:**
- Create: `tasks/T-2026-08-11-identity-tracking-and-harvest-scope/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-11-identity-tracking-and-harvest-scope; echo "exit=$?"
make task-preflight TASK=T-2026-08-11-identity-tracking-and-harvest-scope; echo "exit=$?"
```

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 解決順を実装から確認 | `RESULT.md` | 記録あり |
| 2 | 設定の有無で値が変わる | Task 2 Step 3 | 変わる |
| 3 | 誤入力を拒む | Task 2 Step 4 | すべて拒否 |
| 4 | 非対話シェルでも読める | Task 2 Step 5 | 読める |
| 5 | 識別子を書く経路がある | Task 3 | 実装済み |
| 6 | 無効時は何も書かない | 試験 | pass |
| 7 | 索引に列が増えた | Task 4 Step 3 | 追加された |
| 8 | 既存の値が不変 | 同上 | 指紋が一致 |
| 9 | 新しい列は全行で空 | 同上 | 空 |
| 10 | 収穫の範囲が起票された | `grep -c "^| BL-" context/auto/open_questions.md` | 前より増 |
| 11 | 表の列が揃っている | Task 5 Step 4 | 列数の種類が 1 |
| 12 | 抽出物の方針が文書化 | `grep -n "抽出物の扱い" docs/sessions/README.md` | 1 件 |
| 13 | 索引を記録していない | `git diff --name-only origin/phase0...HEAD \| grep -c "^runindex/"` | 0 |
| 14 | 契約検証が通る | `make task-validate` | exit 0 |
| 15 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 16 | 試験が不変 | `pytest tests/ -q` | **開始前を先に測る** |
| 17 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- experiments/ transfer/ data/splits/ context/conventions.md` | 出力なし |

**判定13が重要である。** 索引の記録は正本ホストの条件を満たす機会に行う。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- 解決順の実測（先行調査と食い違った点があれば明示）
- 環境変数を書く場所と、**なぜそこなら非対話シェルでも読めるのか**
- 外部記録の識別子を取得する経路
- 索引の指紋の比較結果
- 自ホストで無視設定済みのディレクトリが何件あったか
- 起票した未解決事項の番号と slug
- 抽出物の件数（追跡済みと未追跡を分けて）
- **`deviations` を空にしない**
- §6 に、遡っての対応づけが別途必要であることを申し送る

- [ ] **Step 5: 受け皿へ書く**

`tasks/inbox.md` へ本 task の判断を 1 行以上置く。

- [ ] **Step 6: 起票**

```bash
git add tasks/T-2026-08-11-identity-tracking-and-harvest-scope/ tasks/inbox.md docs/sessions/
git commit -m "docs(tasks): record identity injection and tracking linkage"
git push -u origin feat/identity-and-tracking
gh pr create --base phase0 \
  --title "feat: inject logical host name and link external tracking to the index" \
  --body-file tasks/T-2026-08-11-identity-tracking-and-harvest-scope/RESULT.md
```

**統合しない。自動統合も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 解決順が先行調査と違う | **実装に従う。** 食い違いを記録する |
| 非対話シェルで読める場所が見つからない | **停止して報告。** 代替案を提示する |
| 外部記録の識別子を取得できない | 経路が無いことを記録し、**推測で実装しない** |
| 既存の索引の値が変わった | **G2 停止。** `existing_index_values_changed` |
| 新しい列に値が入った | 遡及していないはず。**どこから来たかを調べる** |
| 無視設定済みが自ホストで 0 件 | それも実測結果。**別ホストの値を持ち込まない** |
| 抽出物に秘匿が含まれる | **記録しない。** `secret_value_printed` として報告 |
| 表の列が壊れた | 列数を数えてから書き直す |
| 試験の failed が開始前より増えた | 本 task が壊した。停止して報告 |
