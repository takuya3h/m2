# 資格情報の読み込みを対話シェルでも成立させ、外部記録の停止期間を測る

**task_id:** `T-2026-08-12-env-loader-shell-portability`
**kind:** `impl`
**depends_on:** `T-2026-08-11-canonical-index-refresh`
**実行ホスト:** `lecun`

---

## Goal

資格情報を読み込む入口が、**対話シェルから呼ぶと失敗する。**

実測された挙動は次のとおり。

| 呼び方 | 結果 |
|---|---|
| 対話シェル（既定）から読み込む | **暗号化ファイルが見つからないと言って失敗** |
| 別のシェルを明示して読み込む | 成功し、資格情報が入る |

原因は入口の冒頭にある。

```bash
root="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
```

**全ホストの既定シェルは、この変数を持たない。** 代替として使われる値も、読み込みの
形態によってはスクリプトの場所を指さない。結果として **repo の 1 つ上**が基点になり、
暗号化ファイルに到達しない。

## 影響

資格情報が入らないと、外部への記録は**設計どおり黙って無効になる**。学習は止まらない。
**したがって、動いていないことに気づけない。**

| 対象 | 影響の可能性 |
|---|---|
| 実験の外部追跡 | 送信されていなかった可能性 |
| 実験台帳への自動投稿 | 同上 |
| 索引の外部記録の列 | 今後の run でも空のままになる |

**本 task では、直すことと、いつから止まっていたかを測ることの両方を行う。**

## 現在の前提（実測済み）

| 項目 | 状態 |
|---|---|
| 暗号化ファイル | 全 10 台に配布済み（追跡下） |
| パスフレーズ | 全 10 台に配置済み |
| 別のシェル経由での読み込み | **全 10 台で成功**（外部記録の鍵も入る） |
| 対話シェルからの読み込み | **失敗** |

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git fetch origin
git checkout -b feat/env-loader-portability origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **資格情報の値を出力・記録する**（有無のみ扱う） |
| 2 | **暗号化ファイルを変更・再生成する**（利用者の操作領域） |
| 3 | 平文の設定ファイルを版管理へ追加する |
| 4 | パスフレーズを表示・複製する |
| 5 | `runindex/**` `context/auto/**` を手で編集する |
| 6 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 7 | 学習・評価コードを変更する |
| 8 | 外部の記録先へ**書き込む**（読み取りのみ） |
| 9 | 演算装置を使う |
| 10 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 11 | 統合する。自動統合を有効化する |

### 本 task で解禁するもの

| 対象 | 範囲 |
|---|---|
| `scripts/load_env.sh` | **基点の解決方法のみ。** 復号の手順・変数の設定方法には触れない |
| `scripts/encrypt_env.sh` | Phase C で必要と判明した場合のみ、同じ範囲で |

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが **10 task 連続**で発生している。
実行環境の対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲むこと。**

**本 SPEC の検査も同型の誤りを含みうる。** 次を守ること。

| # | 注意 |
|---|---|
| 1 | 一致件数が 0 のとき、別の探し方でも 0 になることを確かめる |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 4 | 修正の前後で**両方向**を測る（直る前は失敗し、直った後は成功する） |

---

# Phase A — 再現と原因

## Task 1: 誤解決を再現する

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 入口の実装を読む**

```bash
sed -n '1,45p' scripts/load_env.sh
grep -n "BASH_SOURCE\|\$0\|root=\|pf=" scripts/load_env.sh
```

**基点をどう決めているかを、実装から正確に把握する。**

- [ ] **Step 2: 両方のシェルで基点を測る**

**陽性対照と陰性対照を並べる。**

```bash
cd /home/ubuntu/slocal2/m2

echo "===== 既定のシェルで source した場合 ====="
zsh -ic 'cd /home/ubuntu/slocal2/m2; source scripts/load_env.sh 2>&1 | tail -2' 2>&1 | tail -3

echo "===== 別のシェルで source した場合 ====="
bash -lc 'cd /home/ubuntu/slocal2/m2; source scripts/load_env.sh 2>&1 | tail -2' 2>&1 | tail -3
```

Expected: 前者が失敗、後者が成功

**両方とも同じ結果になるなら、この対照は無効である。** 停止して報告する。

- [ ] **Step 3: 基点が何になっているかを直接測る**

```bash
cd /home/ubuntu/slocal2/m2

echo "===== 既定のシェル ====="
zsh -ic 'echo "0=[$0]"; echo "BASH_SOURCE=[${BASH_SOURCE[0]:-未定義}]"' 2>&1 | tail -2

echo "===== 別のシェル ====="
bash -lc 'echo "0=[$0]"; echo "BASH_SOURCE=[${BASH_SOURCE[0]:-未定義}]"' 2>&1 | tail -2

echo "===== source した内側で測る ====="
cat > /tmp/probe_root.sh <<'PROBE'
echo "inner 0=[$0]"
echo "inner BASH_SOURCE=[${BASH_SOURCE[0]:-未定義}]"
echo "inner resolved=[$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." 2>/dev/null && pwd)]"
PROBE
zsh -ic 'cd /home/ubuntu/slocal2/m2; source /tmp/probe_root.sh' 2>&1 | tail -3
bash -lc 'cd /home/ubuntu/slocal2/m2; source /tmp/probe_root.sh' 2>&1 | tail -3
```

**推測ではなく、実際の値を記録する。**

- [ ] **Step 4: G1 ゲート**

| 確認 | 期待 |
|---|---|
| 対照が両方向で働く | 既定で失敗、別のシェルで成功 |
| 基点の実測値が得られた | 値が記録されている |
| 原因が実装から説明できる | 説明が書ける |

**満たさなければ停止して報告する。**

---

# Phase B — 修正

## Task 2: シェルに依存しない解決へ

**Files:**
- Modify: `scripts/load_env.sh`（**基点の解決のみ**）

- [ ] **Step 1: 方法を選ぶ**

**候補は少なくとも 3 つある。実装を読んだうえで選ぶこと。**

| 方法 | 性質 |
|---|---|
| 既定のシェル固有の記法を使う | そのシェルでしか動かない |
| 両方の記法を条件分岐で使い分ける | 一方で構文誤りになりうる |
| **版管理の問い合わせで repo の根を取る** | **シェルに依存しない** |

**3 番目を推奨するが、次の点を実測してから決める。**

```bash
cd /home/ubuntu/slocal2/m2
git rev-parse --show-toplevel
cd /tmp && git rev-parse --show-toplevel 2>&1 | head -1
```

**repo の外から呼ばれた場合にどうなるかを確かめる。** 失敗するなら、その場合の
振る舞いを決めてから実装する（明確な理由で失敗させるのが望ましい）。

選んだ理由を RESULT に書く。**「推奨されたから」ではなく、実測に基づく理由を書く。**

- [ ] **Step 2: 修正する**

**変えるのは基点の解決だけ。** 復号の手順・変数の設定方法・出力の文言には触れない。

- [ ] **Step 3: G2 ゲート — 両方向で測る**

```bash
cd /home/ubuntu/slocal2/m2

echo "===== 既定のシェル（修正後は成功するはず） ====="
zsh -ic 'cd /home/ubuntu/slocal2/m2; source scripts/load_env.sh 2>&1 | tail -1' 2>&1 | tail -2

echo "===== 別のシェル（従来どおり成功するはず） ====="
bash -lc 'cd /home/ubuntu/slocal2/m2; source scripts/load_env.sh 2>&1 | tail -1' 2>&1 | tail -2

echo "===== repo の外から呼んだ場合 ====="
zsh -ic 'cd /tmp; source /home/ubuntu/slocal2/m2/scripts/load_env.sh 2>&1 | tail -1' 2>&1 | tail -2
```

Expected: 最初の 2 つが成功。3 つ目は**成功するか、明確な理由で失敗する**

**出力に資格情報の値が含まれないことを目視で確認する。**

- [ ] **Step 4: 修正前の状態でも測る**

**陰性対照。** 修正を一時的に戻し、既定のシェルで失敗することを再確認する。

```bash
git stash
zsh -ic 'cd /home/ubuntu/slocal2/m2; source scripts/load_env.sh 2>&1 | tail -1' 2>&1 | tail -2
git stash pop
```

**修正前に成功してしまうなら、この検査は無効である。** 停止して報告する。

- [ ] **Step 5: 平文が残っていないことを確認する**

```bash
git status --porcelain | head
ls -la .env 2>&1
git ls-files --error-unmatch .env 2>&1 | head -1
```

**平文の設定ファイルが版管理へ入っていないことを確認する。**

- [ ] **Step 6: commit**

```bash
git add scripts/load_env.sh
git commit -m "fix(scripts): resolve the repo root without depending on the shell"
```

---

# Phase C — 同型の書き方

## Task 3: 他の入口を調べる

**Files:**
- Modify: Phase C で必要と判明したもののみ

- [ ] **Step 1: 同じ書き方を探す**

```bash
grep -rn "BASH_SOURCE" scripts/ tools/ .claude/ 2>/dev/null
echo "===== 件数 ====="
grep -rl "BASH_SOURCE" scripts/ tools/ .claude/ 2>/dev/null | wc -l
```

- [ ] **Step 2: 呼ばれ方を確かめる**

**同じ書き方でも、`source` されるものだけが影響を受ける。**
直接実行されるものは問題にならない。

各該当箇所について、次を判定する。

| 判定 | 意味 |
|---|---|
| `source` される | **修正が要る** |
| 直接実行される | 影響なし |
| 判別できない | **修正する**（安全側） |

```bash
grep -rn "source scripts/\|\. scripts/" README.md OPERATION.md docs/ scripts/ 2>/dev/null | head -20
```

**文書と実装の両方から呼ばれ方を調べる。** 一方だけでは足りない。

- [ ] **Step 3: 必要なものを修正する**

**同じ方法で揃える。** 場所によって違う方法を使わない。

- [ ] **Step 4: 直接実行されるものが壊れていないことを確認する**

```bash
bash -n scripts/*.sh && echo "構文 OK"
```

修正した各スクリプトについて、**従来どおり直接実行できることを確認する。**
ただし**暗号化ファイルを再生成しない**。空実行や構文検査で足りる範囲に留める。

- [ ] **Step 5: commit**

---

# Phase D — 外部記録の稼働状況

## Task 4: いつから止まっていたかを測る

**Files:** なし（読み取りのみ）

**外部の記録先へ書き込まない。読むだけ。**

- [ ] **Step 1: 資格情報を読み込む**

```bash
cd /home/ubuntu/slocal2/m2
source scripts/load_env.sh
python - <<'PY'
import os
for k in ("WANDB_API_KEY", "NOTION_API_KEY"):
    v = os.environ.get(k, "")
    print(f"{k}: {'設定あり' if v else '未設定'}")
PY
```

**値を出さない。**

- [ ] **Step 2: 手元の外部記録の痕跡を測る**

```bash
echo "===== 追跡用ディレクトリ ====="
find experiments transfer -maxdepth 3 -type d -name "wandb" 2>/dev/null | wc -l
find experiments transfer -maxdepth 3 -type d -name "wandb" 2>/dev/null | head -10

echo "===== 最終更新が新しい順 ====="
find experiments transfer -maxdepth 3 -type d -name "wandb" -printf '%T@ %TY-%Tm-%Td %p\n' 2>/dev/null \
  | sort -rn | head -10
```

**手元に痕跡があることは、外部へ送信されたことを意味しない。** 区別して記録する。

- [ ] **Step 3: 外部の台帳の直近の投稿を測る**

**読み取りのみ。書き込まない。**

```bash
python - <<'PY'
import json, os, urllib.request, yaml, pathlib

key = os.environ.get("NOTION_API_KEY", "")
if not key:
    raise SystemExit("資格情報が未設定。Step 1 を先に行う")

reg = yaml.safe_load(pathlib.Path("configs/notion.yaml").read_text(encoding="utf-8"))
db = reg["databases"]["run_ledger"]

req = urllib.request.Request(
    f"https://api.notion.com/v1/databases/{db}/query",
    data=json.dumps({"page_size": 5,
                     "sorts": [{"timestamp": "created_time", "direction": "descending"}]}).encode(),
    method="POST",
    headers={"Authorization": f"Bearer {key}",
             "Notion-Version": "2022-06-28",
             "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        body = json.loads(r.read())
    rows = body.get("results", [])
    print("取得件数:", len(rows))
    for p in rows:
        title = ""
        for v in p.get("properties", {}).values():
            if v.get("type") == "title":
                title = "".join(t.get("plain_text", "") for t in v.get("title", []))
                break
        print(" ", p.get("created_time", "")[:19], title[:60])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, (e.read() or b"")[:200].decode("utf-8", "replace"))
PY
```

**API の版は既存実装に合わせる。** 上の値は推定であり、食い違えば実装に従う。

- [ ] **Step 4: 版管理の履歴と突き合わせる**

```bash
echo "===== 資格情報の入口が最後に変更された時期 ====="
git log --format='%h %cI %s' -- scripts/load_env.sh | head -5
echo "===== 暗号化ファイルの更新履歴 ====="
git log --format='%h %cI %s' -- .env.gpg | head -10
```

- [ ] **Step 5: G3 ゲート — 記録する**

| 観測 | 記録 |
|---|---|
| 台帳の直近の投稿が新しい | 止まっていなかった可能性。**別経路で読み込まれていた** |
| 台帳の直近の投稿が古い | いつからかを記録 |
| 台帳へ到達できない | 理由を記録。**推測しない** |

`on_fail: ask` である。**判断が要る場合は提示して仰ぐ。**

**「いつから止まっていたか」を断定できない場合は `UNKNOWN` と書く。**
状況証拠から推測を書かない。

---

## Task 5: 自己契約と起票

**Files:**
- Create: `tasks/T-2026-08-12-env-loader-shell-portability/RESULT.md`
- Create: `tasks/inbox.d/T-2026-08-12-env-loader-shell-portability.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-12-env-loader-shell-portability; echo "exit=$?"
make task-preflight TASK=T-2026-08-12-env-loader-shell-portability; echo "exit=$?"
make inbox; make inbox-check; echo "exit=$?"
```

- [ ] **Step 3: 完了判定**

| # | 判定 | 期待 |
|---|---|---|
| 1 | 誤解決を再現した | 両方向の対照が働いた |
| 2 | 基点の実測値を得た | 値が記録されている |
| 3 | 既定のシェルで読み込める | 成功 |
| 4 | 別のシェルでも読み込める | 成功 |
| 5 | 修正前は失敗する | 陰性対照が働く |
| 6 | 同型の書き方を調査した | 件数と判定が記録されている |
| 7 | 直接実行が壊れていない | 構文検査が通る |
| 8 | **資格情報の値が出ていない** | 目視確認済み |
| 9 | 暗号化ファイルが不変 | `git diff` が空 |
| 10 | 平文が版管理外 | 追跡されていない |
| 11 | 外部台帳の直近の投稿を測った | 記録あり、または `UNKNOWN` |
| 12 | 契約検証が通る | exit 0 |
| 13 | 実行前検査が通る | exit 0 |
| 14 | 試験が不変 | **開始前を先に測る** |
| 15 | 禁止領域が無変更 | 出力なし |

**判定9が重要である。** 暗号化ファイルの再生成は利用者の操作領域である。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- 基点の実測値（両方のシェルで）
- 選んだ解決方法と、**実測に基づく理由**
- repo の外から呼ばれた場合の振る舞い
- 同型の書き方の件数と、`source` されるかどうかの判定
- **外部台帳の直近の投稿時刻**。断定できなければ `UNKNOWN`
- 手元の痕跡と外部への送信を**区別した記述**
- **`deviations` を空にしない**
- §6 に、他ホストへの展開が別作業であることを申し送る

- [ ] **Step 5: 起票**

```bash
git add scripts/ tasks/
git commit -m "docs(tasks): record the env loader portability fix"
git push -u origin feat/env-loader-portability
gh pr create --base phase0 \
  --title "fix(scripts): make the env loader work from the default shell" \
  --body-file tasks/T-2026-08-12-env-loader-shell-portability/RESULT.md
```

**統合しない。自動統合も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 対照が両方向で働かない | **G1 停止。** その対照は無効 |
| repo の外から呼ぶと壊れる | 明確な理由で失敗させる。**黙って別の場所を見ない** |
| 修正前でも成功してしまう | **G2 停止。** 前提が違う |
| 同型の書き方が多数見つかる | 全て記録し、`source` されるものだけ直す |
| 資格情報が出力に混ざった | **即座に停止。** `secret_value_printed` |
| 暗号化ファイルに差分が出た | **即座に戻す。** `encrypted_env_modified` |
| 外部台帳へ到達できない | 理由を記録。**推測しない** |
| 停止期間を特定できない | `UNKNOWN` と書く。**状況証拠で断定しない** |
| 試験の failed が開始前より増えた | 本 task が壊した。停止して報告 |
