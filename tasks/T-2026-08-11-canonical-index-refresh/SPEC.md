# 外部記録の列を含む索引を、条件を満たすホストで生成して正本とする

**task_id:** `T-2026-08-11-canonical-index-refresh`
**kind:** `impl`
**depends_on:** `T-2026-08-11-inbox-per-task-split`
**実行ホスト:** `lecun`（退避を終えて条件を満たしている）

---

## Goal

別ホストで索引へ 2 列が追加されたが、**まだ生成されていない。** 全行で空のままである。

`tasks/README.md` の「索引の正本」は、**全ての経路が版管理の追跡下にあるホストで
生成する**ことを定める。退避を終えたこのホストがその条件を満たす。

**追加された列を含む索引を生成し、正本として記録する。**

## 期待される結果

| 項目 | 期待 |
|---|---|
| 行数 | 変わらない |
| 列 | 2 つ増える |
| 既存の列の値 | **一件も変わらない** |
| 追加された列 | **全行で空**（遡っての対応づけは行っていないため） |

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git fetch origin
git checkout -b feat/canonical-index-refresh origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` を**手で**編集する（生成は可） |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 3 | `tools/**` `src/**` を変更する |
| 4 | `context/conventions.md` を変更する |
| 5 | 外部サービスへ問い合わせる。遡って対応づける |
| 6 | 演算装置を使う |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | 統合する。自動統合を有効化する |

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが **10 task 連続**で発生している。
直近では、追加された列を名前の部分一致で探すコマンドが**既存の列にも一致**し、
何も壊れていないのに不一致と判定させるものだった。

また実行環境の対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲むこと**
（`${VAR}:...`）。過去に 3 度、修飾子と解釈されて黙って空を返している。

**本 SPEC の検査も同型の誤りを含みうる。** 次を守ること。

| # | 注意 |
|---|---|
| 1 | 追加された列は**新旧のヘッダの集合差**で求める。名前の部分一致で探さない |
| 2 | 一致件数が 0 のとき、別の探し方でも 0 になることを確かめる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない |

---

# Phase A — 条件の確認

## Task 1: このホストが正本を生成できることを確かめる

- [ ] **Step 1: 作業ツリーと同期の状態**

```bash
git branch --show-current
git status --porcelain
git rev-list --count HEAD..origin/phase0
```

**未追跡の対話記録の抽出物があれば、本 task の記録と一緒に含める**（方針は文書化済み）。
それ以外の差分があれば停止して報告する。

- [ ] **Step 2: 追跡外の経路が無いことを確認する（G1）**

```bash
python - <<'PY'
import csv, subprocess
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
pathcols = [c for c in cols if any(k in c.lower() for k in ("path", "dir", "workdir"))]
print("経路の列:", pathcols)
bad = []
for r in rows:
    p = next((r.get(c) for c in pathcols if r.get(c)), "")
    if not p:
        continue
    if subprocess.run(["git", "ls-files", "--error-unmatch", p],
                      capture_output=True).returncode != 0:
        bad.append(p)
print("行数:", len(rows), "列数:", len(cols))
print("追跡外の経路を持つ行:", len(bad))
for p in bad[:10]:
    print("  ", p)
PY
```

Expected: **追跡外 0 件**

**0 件でなければ停止して報告する**（`untracked_path_found`）。

- [ ] **Step 3: 検査が空振りでないことを確かめる**

**陽性対照を置く。** 存在しない経路を混ぜて、検査が反応することを確認する。

```bash
python - <<'PY'
import subprocess
for p in ["tools/harvest_runindex.py", "no/such/path/at/all"]:
    rc = subprocess.run(["git", "ls-files", "--error-unmatch", p],
                        capture_output=True).returncode
    print(f"{p:40} -> {'追跡下' if rc == 0 else '追跡外'}")
PY
```

Expected: 前者が追跡下、**後者が追跡外**

**両方とも同じ結果になるなら、この検査は無効である。** 停止して報告する。

- [ ] **Step 4: 生成前の状態を控える**

```bash
mkdir -p /tmp/idx_refresh
cp runindex/index.csv /tmp/idx_refresh/index_before.csv
md5sum runindex/*.csv > /tmp/idx_refresh/md5_before.txt
python - <<'PY'
import csv, json, hashlib
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
key = next((c for c in cols if c.endswith("ledger_key")), None)
h = hashlib.sha256()
for r in sorted(rows, key=lambda x: x.get(key, "")):
    for k in sorted(r):
        h.update(f"{k}={r[k]}".encode())
snap = {"rows": len(rows), "cols": cols, "fingerprint": h.hexdigest()}
json.dump(snap, open("/tmp/idx_refresh/before.json", "w"), ensure_ascii=False, indent=2)
print("行数:", snap["rows"], "列数:", len(cols))
print("指紋:", snap["fingerprint"][:16])
PY
```

**記録を作る流れに表示用の切り詰めを混ぜていない。**

---

# Phase B — 生成と検査

## Task 2: 生成する

- [ ] **Step 1: 再生成**

```bash
make runindex 2>&1 | tail -20
```

- [ ] **Step 2: 追加された列を集合差で求める（G2）**

**名前の部分一致で探さない。**

```bash
python - <<'PY'
import csv, json, hashlib
before = json.load(open("/tmp/idx_refresh/before.json"))
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
key = next((c for c in cols if c.endswith("ledger_key")), None)

added = [c for c in cols if c not in before["cols"]]
removed = [c for c in before["cols"] if c not in cols]
print("追加された列:", added)
print("消えた列:", removed)
print("行数:", before["rows"], "->", len(rows))

# 追加分を除いた指紋を、両側から同じ列集合で計算する
h = hashlib.sha256()
for r in sorted(rows, key=lambda x: x.get(key, "")):
    for k in sorted(r):
        if k in added:
            continue
        h.update(f"{k}={r[k]}".encode())
print("既存部分の指紋:", h.hexdigest()[:16], "/ 生成前:", before["fingerprint"][:16])
print("一致:", h.hexdigest() == before["fingerprint"])
print("追加列が空でない行:", sum(1 for r in rows if any(r.get(c) for c in added)))
PY
```

Expected

| 項目 | 期待 |
|---|---|
| 追加された列 | 2 つ |
| 消えた列 | 無し |
| 行数 | 不変 |
| 既存部分の指紋 | **一致** |
| 追加列が空でない行 | **0** |

**一致しなければ停止して報告する**（`existing_values_changed`）。

- [ ] **Step 3: 差分の内訳を確認する**

```bash
git diff --stat runindex/
git status --porcelain runindex/ context/auto/
```

**`index.csv` 以外にも差分が出る場合、その内容を確認して記録する。**
別ホスト固有の空のディレクトリに由来する行が消えることが分かっている（先行の記録による）。
**消える場合は、それが何かを特定してから記録する。**

- [ ] **Step 4: 軽量ビューを生成する**

```bash
make context
make context-check; echo "exit=$?"
head -8 context/auto/STATE.md
```

Expected: `exit=0`

- [ ] **Step 5: 記録する**

```bash
git add runindex/ context/auto/
git commit -m "chore(runindex): regenerate the canonical index with tracking columns"
```

---

# Phase C — 記録と起票

## Task 3: 自己契約と起票

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-11-canonical-index-refresh; echo "exit=$?"
make task-preflight TASK=T-2026-08-11-canonical-index-refresh; echo "exit=$?"
make inbox-check; echo "exit=$?"
```

**母集団の警告が出るのは正常。** 契約の値は書き換えない。

- [ ] **Step 3: 完了判定**

| # | 判定 | 期待 |
|---|---|---|
| 1 | 追跡外の経路が無い | 0 件 |
| 2 | 検査が空振りでない | 陽性対照が反応する |
| 3 | 追加された列がある | 2 つ |
| 4 | 消えた列が無い | 無し |
| 5 | 行数が不変 | 不変 |
| 6 | 既存の値が不変 | 指紋が一致 |
| 7 | 追加列が全行で空 | 0 行 |
| 8 | 軽量ビューが整合 | `context-check` exit 0 |
| 9 | 契約検証が通る | exit 0 |
| 10 | 実行前検査が通る | exit 0 |
| 11 | 受け皿の集約が整合 | `inbox-check` exit 0 |
| 12 | 試験が不変 | **開始前を先に測る** |
| 13 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- experiments/ transfer/ data/splits/ tools/ src/ context/conventions.md` が空 |

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- 追跡外の経路の件数と、陽性対照の結果
- 生成前後の行数・列数・指紋
- 追加された列の名前
- `index.csv` 以外の差分の内訳（消えた行があれば、それが何か）
- **`deviations` を空にしない**

- [ ] **Step 5: 受け皿へ書く**

```bash
mkdir -p tasks/inbox.d
# tasks/inbox.d/T-2026-08-11-canonical-index-refresh.md へ 1 行以上
make inbox
make inbox-check; echo "exit=$?"
```

**集約結果を手で編集しない。**

- [ ] **Step 6: 起票**

```bash
git add tasks/ docs/sessions/ 2>/dev/null
git commit -m "docs(tasks): record the canonical index refresh"
git push -u origin feat/canonical-index-refresh
gh pr create --base phase0 \
  --title "chore(runindex): refresh the canonical index with tracking columns" \
  --body-file tasks/T-2026-08-11-canonical-index-refresh/RESULT.md
```

**統合しない。自動統合も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 追跡外の経路がある | **G1 停止。** このホストは条件を満たさない |
| 陽性対照が反応しない | **検査が無効。** 停止して報告 |
| 既存の値が変わった | **G2 停止。** `existing_values_changed` |
| 追加列に値が入った | 遡っていないはず。**どこから来たかを調べる** |
| 行が消えた | 何が消えたかを特定してから記録する |
| 軽量ビューが整合しない | 停止して報告 |
| 試験の failed が開始前より増えた | 本 task が壊した。停止して報告 |
