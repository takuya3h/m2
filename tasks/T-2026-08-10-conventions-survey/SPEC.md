# 命名と配置と外部連携の実態を測り、変更前に依存関係を明らかにする

**task_id:** `T-2026-08-10-conventions-survey`
**kind:** `impl`
**depends_on:** `T-2026-08-09-scoped-integration`（PR #52・統合済み）

---

## Goal

利用者から 4 つの変更要望が出た。**いずれも実行すると連鎖的に他を壊す恐れがある。**

| # | 要望 | 判明している危険 |
|---|---|---|
| 1 | 分岐名から日付と作業状態の語を外し、`host/<名前>` へ | **自動同期が `exp/` で始まる分岐でのみ動作する。名前を変えると全ホストで止まる** |
| 2 | ホスト固有の内容を持つ追跡物を分離する | 対象が網羅されていない |
| 3 | 計算機の識別子の重複を解消する | 原因が構成上のものか設定上のものか未確定 |
| 4 | 外部記録との連携を整える | 設定の所在が未確認 |

さらに、`tasks/todo.md` が**誰によって更新されているか分かっていない。** 起票者が
作らせたものではなく、現在も更新され続けている。

**本 task は測るだけである。一切の変更を行わない。** 実装は別 task とする。

## なぜ分けるか

起票者の検査コマンドが検証対象を検証できていない誤りが **7 task 連続**で発生している。
実態を知らずに実装指示を書けば、同じ誤りが変更を伴う形で再発する。**測ってから書く。**

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git branch --show-current
git status --porcelain | head
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **あらゆるファイルを変更する**（本 task の記録を除く） |
| 2 | 分岐を作る、切り替える、名前を変える |
| 3 | **秘匿値を出力・記録する**（存在と所在のみ記録する） |
| 4 | 仮想環境の中身を変更する |
| 5 | 外部の記録先へ書き込む |
| 6 | 演算装置を使う |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | 他ホストへ書き込む |

### 探索の作法

**一致が 0 件のとき、それが「無い」のか「探し方が悪い」のか、また「対象が存在しない」
のかを区別すること。** 直前の調査で、あるスクリプトへの検索が何も返さなかったが、
それが該当なしなのかファイル自体が無いのか判別できなかった。

**必ず対象の存在を先に確認してから検索する。**

```bash
ls -la <対象> 2>&1 || echo "対象が存在しない"
```

### 秘匿の扱い

外部連携の設定には資格情報が含まれる。**値を画面に出さない。**
存在するか、どこにあるか、どの名前かのみを記録する。誤って出力した場合は
`secret_value_printed` として即座に報告する。

---

# Phase A — 作業一覧の更新経路

## Task 1: 誰が書き換えているかを特定する

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 対象の存在と中身を確認する**

```bash
ls -la tasks/todo.md 2>&1 || echo "存在しない"
wc -l tasks/todo.md
head -40 tasks/todo.md
echo "..."
tail -20 tasks/todo.md
```

- [ ] **Step 2: 変更履歴を追う**

```bash
git log --format='%h %an %cI %s' -- tasks/todo.md | head -30
echo "===== 変更の頻度 ====="
git log --format='%cI' -- tasks/todo.md | cut -c1-10 | sort | uniq -c | tail -20
echo "===== どの分岐で作られたか ====="
git log --format='%h %d %s' -- tasks/todo.md | head -10
```

- [ ] **Step 3: 書き換えている主体を探す**

**推測しない。実際に書いている箇所を探す。**

```bash
echo "===== 追跡下の参照 ====="
grep -rn "todo\.md" --include='*.py' --include='*.sh' --include='*.md' --include='*.yml' --include='*.yaml' . 2>/dev/null | grep -v '^\./\.git/' | head -30
echo "===== 手順書からの参照 ====="
grep -rn "todo" .claude/ .codex/ CLAUDE.md AGENTS.md 2>/dev/null | head -20
echo "===== 追跡外のスクリプト ====="
for f in ~/bin/*.sh ~/bin/* ; do
  [ -f "$f" ] || continue
  if grep -l "todo\.md" "$f" >/dev/null 2>&1; then echo "該当: $f"; fi
done
ls -la ~/bin/ 2>&1 | head -20
```

**`~/bin/` の存在自体を先に確認すること。** 存在しなければ、そう記録する。

- [ ] **Step 4: 常駐している処理を確認する**

```bash
crontab -l 2>/dev/null | head -20 || echo "定期実行の設定なし"
systemctl --user list-timers --no-pager 2>/dev/null | head -10 || echo "利用者単位のタイマーなし"
ps -eo pid,etimes,args | grep -iE "keeper|sync|watch" | grep -v grep | head -10
```

**プロセスの計数に一致検索を使わない。** 検索自身に一致する（既知の落とし穴）。

- [ ] **Step 5: G1 ゲート**

| 観測 | 記録 |
|---|---|
| 書き換えている箇所が特定できた | その場所と契機を記録 |
| 特定できない | **`UNKNOWN` と明記する。** 推測で「おそらく」と書かない |

`on_fail: ask` である。特定できなくても停止せず、調べた範囲を提示して判断を仰ぐ。

---

# Phase B — ホスト固有の追跡物

## Task 2: 何がホストによって異なるかを洗い出す

**Files:** なし（読み取りのみ）

伝播は全ホスト共有である。**ホストによって内容が異なるべきものが追跡されていると、
必ず衝突する。**

- [ ] **Step 1: ホスト名や機体固有の語を含む追跡物を探す**

```bash
echo "===== 名前にホストを含むもの ====="
git ls-files | grep -iE "lecun|philip|ilya|bengio|andrew|adam|hinton|efros|dlsta|aolab" | head -30
echo "===== 中身にホストを含むもの ====="
git grep -ilE "lecun|philip|ilya|bengio|aolab" -- '*.md' '*.yaml' '*.yml' '*.txt' '*.json' 2>/dev/null | head -40
```

- [ ] **Step 2: 実行環境に依存する内容を持つものを探す**

```bash
echo "===== 経路を含む追跡物 ====="
git grep -ln "/home/ubuntu\|/mnt/\|\$HOME" -- '*.md' '*.yaml' '*.yml' '*.sh' 2>/dev/null | head -30
echo "===== 装置や資源に言及するもの ====="
git grep -ln "CUDA_VISIBLE\|nvidia-smi\|GPU" -- '*.md' '*.yaml' 2>/dev/null | head -20
```

- [ ] **Step 3: 実際に食い違っているものを確かめる**

**中身にホスト名が出るだけでは、ホスト固有とは限らない。** 記録として妥当な場合もある。
**食い違いが問題になるのは、各ホストが独立に書き換えるものである。**

各候補について次を確認する。

| 判定 | 意味 |
|---|---|
| 複数ホストが独立に書き換える | **ホスト固有。分離の対象** |
| 特定ホストで生成され共有される | 記録。分離不要 |
| 生成物 | 派生物。別の扱い |

```bash
for f in $(git ls-files | grep -E "todo|inbox|operation|server" | head -20); do
  printf "%-50s " "$f"
  n=$(git log --format='%an' -- "$f" | sort -u | wc -l)
  echo "書き手 $n 名 / 変更 $(git log --oneline -- "$f" | wc -l) 回"
done
```

- [ ] **Step 4: 記録する**

`survey.md` の該当節へ、**分離すべきもの / 記録として残すもの / 判断保留**の3分類で
一覧する。**判断保留のものは理由を書く。**

---

# Phase C — 分岐名への依存

## Task 3: 名前を変えたら何が壊れるかを列挙する

**Files:** なし（読み取りのみ）

**判明している依存が 1 件ある。** 自動同期は分岐名が特定の接頭辞で始まることを
条件にしている。他にも同種の依存がないかを網羅する。

- [ ] **Step 1: 追跡下を探す**

```bash
echo "===== 接頭辞への依存 ====="
git grep -n "exp/" -- '*.py' '*.sh' '*.yml' '*.yaml' '*.toml' 2>/dev/null | head -40
echo "===== 分岐名を取得している箇所 ====="
git grep -n "branch --show-current\|rev-parse --abbrev-ref\|current_branch\|HEAD_REF\|GITHUB_REF" 2>/dev/null | head -30
echo "===== 作業状態の語への依存 ====="
git grep -n "wip" -- '*.py' '*.sh' '*.yml' '*.yaml' 2>/dev/null | head -20
```

- [ ] **Step 2: 追跡外を探す**

**存在を先に確認してから検索する。**

```bash
for f in ~/bin/keeper.sh ~/bin/m2-sync.sh ~/bin/*.sh; do
  [ -e "$f" ] || { echo "存在しない: $f"; continue; }
  echo "===== $f ====="
  grep -nE "exp/|wip|branch|--show-current|abbrev-ref" "$f" | head -10 || echo "  該当なし"
done
ls -la ~/bin/ 2>&1 | head -20
ls -la ~/claude-sync/ 2>&1 | head -20
```

- [ ] **Step 3: 継続的統合の設定を探す**

```bash
for f in .github/workflows/*.yml .github/workflows/*.yaml; do
  [ -e "$f" ] || continue
  echo "===== $f ====="
  grep -nE "branches|exp/|head_ref|ref_name" "$f" | head -10 || echo "  該当なし"
done
```

- [ ] **Step 4: 手順書と規約を探す**

```bash
git grep -n "exp/" -- '*.md' 2>/dev/null | head -30
```

- [ ] **Step 5: G2 ゲート — 探索の漏れを別の手段で確かめる**

**同じ探し方を繰り返しても漏れは見つからない。別の角度から確かめる。**

```bash
echo "===== 全追跡物から接頭辞を含む行を数える ====="
git grep -c "exp/" 2>/dev/null | head -20
echo "===== 拡張子を限定しない全文検索 ====="
git grep -l "exp/" 2>/dev/null | wc -l
echo "===== Step 1 で拡張子を限定した結果との差 ====="
git grep -l "exp/" 2>/dev/null | grep -vE '\.(py|sh|yml|yaml|toml|md)$' | head -20
```

**拡張子を限定した検索で漏れた経路があれば、それが漏れの実例である。**
Step 1 から Step 4 の結果と突き合わせ、**差があれば追加で調べる。**

漏れの確認ができなければ停止して報告する。

- [ ] **Step 6: 影響を分類する**

| 分類 | 意味 |
|---|---|
| **致命** | 名前を変えると機能が停止する |
| 表示 | 文言が古くなるだけ |
| 記録 | 過去の記述。変更不要 |

**致命に分類したものごとに、同時に直すべき箇所を明記する。**

---

# Phase D — 計算機の識別子

## Task 4: 重複の原因を確かめる

**Files:** なし（読み取りのみ）

2 つのホストが同じ識別子を報告している。**構成によるものか設定によるものかで
対処が変わる。**

- [ ] **Step 1: 自ホストの実態を測る**

```bash
echo "=== 識別子 ==="
hostname
cat /etc/hostname 2>/dev/null
hostnamectl 2>/dev/null | head -5 || echo "hostnamectl なし"
echo "=== 隔離環境かどうか ==="
ls /.dockerenv 2>/dev/null && echo "隔離環境の指標あり" || echo "指標なし"
head -3 /proc/1/cgroup 2>/dev/null
cat /proc/1/comm 2>/dev/null
echo "=== 網 ==="
ip -4 addr show 2>/dev/null | grep inet | head -5
```

- [ ] **Step 2: 証跡に書かれる識別子の出所を探す**

```bash
git grep -n "hostname\|gethostname\|server\.txt\|uname" -- '*.py' 2>/dev/null | head -20
echo "===== 実際の証跡 ====="
for f in $(git ls-files | grep "server.txt" | head -10); do
  printf "%-70s %s\n" "$f" "$(cat "$f")"
done
```

- [ ] **Step 3: 索引に記録されている識別子の分布を見る**

```bash
python - <<'PY'
import csv, collections
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
hostcols = [c for c in cols if any(k in c.lower() for k in ("host", "server", "machine", "node"))]
print("識別子らしき列:", hostcols)
for c in hostcols:
    print(f"--- {c} ---")
    for k, v in collections.Counter(r.get(c, "") for r in rows).most_common(15):
        print(f"  {k or '(空)'}: {v}")
PY
```

**同じ識別子に複数の実体が混ざっているかを、この分布から判断する。**

- [ ] **Step 4: 記録する**

| 判明したこと | 対処の方向 |
|---|---|
| 隔離環境で親と識別子を共有している | **識別子は変えられない。論理名を別に持つ** |
| 単に同じ名前が設定されている | 設定変更が可能。ただし影響範囲は要調査 |
| 判別できない | `UNKNOWN` |

---

# Phase E — 外部記録との連携

## Task 5: 設定の所在を確かめる

**Files:** なし（読み取りのみ）

**資格情報の値を一切出力しない。** 存在と所在と名前のみ。

- [ ] **Step 1: 設定の場所を探す**

```bash
echo "===== 追跡下の設定 ====="
git grep -ln "wandb\|WANDB" -- '*.py' '*.yaml' '*.yml' '*.toml' '*.md' 2>/dev/null | head -20
echo "===== 設定項目の名前だけ ====="
git grep -hoE "(project|entity|WANDB_[A-Z_]+)\s*[:=]" -- '*.yaml' '*.yml' '*.py' 2>/dev/null | sort -u | head -20
echo "===== 仮想環境の中の資格情報らしきものの所在 ====="
find .venv -maxdepth 3 -name "*.netrc" -o -maxdepth 3 -name "*wandb*" 2>/dev/null | head -10
ls -la .venv/.netrc ~/.netrc 2>&1 | head -5
```

**中身を `cat` しない。** 存在の有無とパスだけを見る。

- [ ] **Step 2: 環境変数の名前だけを確認する**

```bash
env | grep -oE "^WANDB[A-Z_]*" | sort -u || echo "該当する環境変数なし"
```

**値を含む形で出力しない。** 名前のみ。

- [ ] **Step 3: 記録済みの件数を確かめる**

**外部へ問い合わせない。** 手元の記録から数える。

```bash
python - <<'PY'
import csv
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
wcols = [c for c in cols if any(k in c.lower() for k in ("wandb", "run_url", "tracking"))]
print("外部記録らしき列:", wcols)
for c in wcols:
    n = sum(1 for r in rows if r.get(c))
    print(f"  {c}: 非空 {n} 件 / 全 {len(rows)} 件")
PY
find experiments transfer -maxdepth 3 -name "wandb" -type d 2>/dev/null | wc -l
```

- [ ] **Step 4: 無効化の経路を確かめる**

配線検証の run では外部記録が無効化された。**どの経路で無効化されるかを実装から確かめる。**

```bash
git grep -n "WANDB_MODE\|wandb.*disabled\|use_wandb\|enable_wandb" -- '*.py' '*.yaml' 2>/dev/null | head -20
grep -n "wandb\|W&B" CLAUDE.md 2>/dev/null | head -10
```

- [ ] **Step 5: G3 ゲート — 秘匿を出していないことを確認する**

```bash
echo "===== 本 task の出力に秘匿らしき文字列が無いか ====="
grep -nE "(api[_-]?key|token|secret|password)[\"'[:space:]]*[:=][\"'[:space:]]*[A-Za-z0-9_-]{16,}" \
  tasks/T-2026-08-10-conventions-survey/*.md 2>/dev/null | head
echo "（何も出なければ良い。ただし何に一致しているかを目視で確認すること）"
```

**一致があれば、それが本物の秘匿かどうかを目視で確認する。**
過去に、無関係な語に一致して偽陽性が出ている。**件数だけで判断しない。**

秘匿が混入していれば `secret_value_printed` として即座に報告し、当該記録を破棄する。

---

# Phase F — 記録

## Task 6: 調査結果をまとめる

**Files:**
- Create: `tasks/T-2026-08-10-conventions-survey/survey.md`
- Create: `tasks/T-2026-08-10-conventions-survey/RESULT.md`

- [ ] **Step 1: `survey.md` を書く**

**表の列数を数えてから書く。本文に半角パイプを書かない。**

```markdown
# 命名と配置と外部連携の実態（2026-08-10）

## 1. 作業一覧の更新経路

（特定できた主体、または UNKNOWN）

## 2. ホスト固有の内容を持つ追跡物

| 経路 | 判定 | 根拠 |
|---|---|---|

判定は、分離すべきもの / 記録として残すもの / 判断保留 のいずれか。

## 3. 分岐名への依存

| 経路 | 行 | 依存の内容 | 分類 |
|---|---|---|---|

分類は、致命 / 表示 / 記録 のいずれか。

### 名前を変える場合に同時に直すべき箇所

（致命に分類したものを列挙）

### 探索の漏れの確認

（別の手段で確かめた結果）

## 4. 計算機の識別子

（重複の原因。構成上か設定上か、または UNKNOWN）

## 5. 外部記録との連携

| 項目 | 所在 | 状態 |
|---|---|---|

**資格情報の値は記載しない。**

## 6. 変更を行う場合の順序

（依存関係から導かれる安全な順序。判断は利用者へ委ねる）
```

- [ ] **Step 2: 何も変更していないことを確認する**

```bash
git status --porcelain | grep -v "^?? tasks/T-2026-08-10-conventions-survey/" | head -20
```

**本 task の記録以外に変更があれば `unexpected_write_detected` として報告する。**

- [ ] **Step 3: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 4: 自己検証**

```bash
make task-validate TASK=T-2026-08-10-conventions-survey; echo "exit=$?"
make task-preflight TASK=T-2026-08-10-conventions-survey; echo "exit=$?"
```

- [ ] **Step 5: 完了判定**

| # | 判定 | 期待 |
|---|---|---|
| 1 | 更新主体が特定または UNKNOWN と明記 | どちらか |
| 2 | ホスト固有の候補が3分類で列挙 | 表が埋まっている |
| 3 | 分岐名への依存が列挙 | 表が埋まっている |
| 4 | 致命に分類したものが明示 | 1 件以上（判明済みのものがある） |
| 5 | 探索の漏れを別手段で確認 | 結果が記録されている |
| 6 | 識別子の重複の原因 | 説明または UNKNOWN |
| 7 | 外部連携の所在が記録 | 表が埋まっている |
| 8 | **秘匿値が含まれない** | 目視確認済み |
| 9 | **記録以外の変更が無い** | `git status` が記録のみ |
| 10 | 契約検証が通る | exit 0 |
| 11 | 実行前検査が通る | exit 0 |

- [ ] **Step 6: `RESULT.md` を書く**

必ず含めるもの。

- 各 Phase の**生の出力**（秘匿を除く）
- 存在しなかった対象の一覧（「該当なし」と「対象なし」を区別して）
- 特定できなかったものと、その理由
- **変更を行う場合に、起票者へ伝えるべき注意点**
- **`deviations` を空にしない**

- [ ] **Step 7: 記録して報告する**

```bash
git add tasks/T-2026-08-10-conventions-survey/
git commit -m "docs(tasks): survey naming, placement, and external tracking"
git status --porcelain
```

**送出も起票も行わない。** 調査結果を提示して判断を仰ぐ。

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 更新主体が特定できない | `UNKNOWN` と明記。**「おそらく」と書かない** |
| 対象のファイルやディレクトリが存在しない | **「該当なし」ではなく「対象なし」と記録する** |
| 探索の漏れが見つかった | 追加で調べ、**漏れた理由も記録する** |
| 秘匿値を出力してしまった | **即座に報告。** 当該記録を破棄してやり直す |
| 記録以外の変更が発生した | **即座に報告。** 本 task は読み取り専用である |
| 分岐名への依存が想定より多い | 全て列挙する。**件数を減らさない** |
| 外部連携の設定が見つからない | `UNKNOWN`。**推測で場所を書かない** |
