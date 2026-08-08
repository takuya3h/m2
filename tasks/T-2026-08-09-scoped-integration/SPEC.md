# 派生物を除いた範囲で統合を起票し、実行ホストに残る退避物を棚卸しする

**task_id:** `T-2026-08-09-scoped-integration`
**kind:** `impl`
**depends_on:** `T-2026-08-09-wiring-followup-and-integration`
**実行ホスト:** `lecun`（分岐 `exp/lecun-wip-20260703`）

---

## Goal

既存の起票（10 コミット・73 ファイル）には、**実行ホスト固有の派生物が含まれている。**

別ホストでの実測により、索引の行数が実行ホストでのみ 35 行多いことが分かった。
追加分は**そのホストのディスクにだけ残る退避物**であり、他ホストには存在しない。
これを統合すると、**一つのホストの局所的な状態が全ホストの正本になる。**

利用者の判断により、**派生物を除いた範囲だけを統合する。**

## 除外するもの

| 対象 | 理由 |
|---|---|
| `runindex/` | 収穫器が各ホストで再生成する派生物。実行ホスト固有の退避物を含む |
| `context/auto/` | 索引から生成される派生物。**索引を除外して軽量ビューだけ配ると、他ホストで整合検査が必ず失敗する** |

## 統合するもの

| 対象 | 理由 |
|---|---|
| 継続的統合の設定 | 資格情報の失効検出 |
| ビルド定義 | 依存の一括導入 |
| 配線検証で生成された一次証跡 | **これが無いと他ホストで識別子の刻印を再現できない** |
| 契約の一式 | 記録と受け皿 |
| 収穫器 | 未解決事項の追記 |

## 統合後に各ホストで必要なこと

統合しても索引は更新されない。**各ホストで再生成が必要である。**

```
make runindex && make context
```

**退避物を持たないホストで再生成したものを、次の正本とするのが望ましい。**
その判断は本 task の範囲外であり、利用者へ委ねる。

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git branch --show-current    # exp/lecun-wip-20260703
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **退避物を移動・削除・改名する**（棚卸しのみ） |
| 2 | 統合を実行する。自動統合を有効化する |
| 3 | `runindex/**` `context/auto/**` を統合範囲へ含める |
| 4 | `data/splits/**` `context/conventions.md` `src/**` を変更する |
| 5 | 学習・評価コードを変更する |
| 6 | 演算装置を使う |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | 既存の起票を閉じる（利用者の判断領域） |

### 起票者からの申し送り

**起票者の検査コマンドが検証対象を検証できていない誤りが 6 task 連続で発生している。**
直近では、採番の走査が引用符の有無と修飾子の解釈で二重に外れ、指示どおりなら
未解決事項の一覧が全面的に衝突していた。

**本 SPEC の検査も同型の誤りを含みうる。** 特に次の 2 点に注意すること。

| # | 注意 |
|---|---|
| 1 | **一致件数が 0 のとき、それが「無い」のか「探し方が悪い」のかを必ず区別する。** 別の探し方でも 0 になることを確かめてから結論を出す |
| 2 | 表への追記は**列数を数えてから**書く。過去に 3 度、列が壊れている |

---

# Phase A — 統合範囲の切り出し

## Task 1: 統合用の分岐を作る

**Files:** 新しい分岐上の変更

- [ ] **Step 1: 現状を記録する**

```bash
git fetch origin
SRC=$(git branch --show-current)
echo "SRC=$SRC"
echo "===== 統合先に無いコミット ====="
git log --oneline origin/phase0.."$SRC"
echo "===== 変更ファイル（派生物を除く） ====="
git diff --name-only origin/phase0..."$SRC" | grep -vE '^(runindex/|context/auto/)'
echo "===== 除外される派生物 ====="
git diff --name-only origin/phase0..."$SRC" | grep -E '^(runindex/|context/auto/)' | wc -l
```

**この一覧を RESULT §1 へ記録する。** 統合される範囲の完全な記録になる。

- [ ] **Step 2: 統合用の分岐を作る**

```bash
SRC=exp/lecun-wip-20260703
git checkout -b integrate/wiring-work-20260809 origin/phase0
git branch --show-current
git rev-list --count origin/phase0..HEAD    # 0 のはず
```

- [ ] **Step 3: 派生物を除いて取り込む**

**経路単位で取り込む。** 個々のコミットを移すのではなく、最終状態を取る。

```bash
SRC=exp/lecun-wip-20260703
for p in \
  .github/workflows/auto-draft-pr.yml \
  Makefile \
  experiments/baselines/s0_040_wiring_verification_seed42 \
  tasks \
  tools/harvest_runindex.py
do
  git checkout "$SRC" -- "$p" 2>&1 || echo "取り込めない: $p"
done
git status --porcelain | head -40
```

**Step 1 で列挙した経路がすべて含まれることを確認する。** 漏れがあれば追加する。
逆に、列挙していない経路が混ざっていないことも確認する。

- [ ] **Step 4: G1 ゲート — 派生物が混ざっていないことを実測する**

```bash
echo "===== 索引と軽量ビューが含まれていないか ====="
git diff --cached --name-only | grep -E '^(runindex/|context/auto/)' && echo "混入あり" || echo "混入なし"
git status --porcelain | grep -E '^(A|M|\?\?).*(runindex/|context/auto/)' && echo "作業ツリーに混入" || echo "作業ツリーは清潔"
echo "===== 統合される経路の一覧 ====="
git status --porcelain | awk '{print $2}' | sort
echo "===== 件数 ====="
git status --porcelain | wc -l
```

**混入があれば停止して報告する**（`derived_artifact_in_scope`）。

> 一致が 0 件のとき、探し方が悪い可能性を排除すること。上の 2 通りの検査が
> どちらも 0 件であることをもって「混入なし」とする。

- [ ] **Step 5: 記録して確定する**

```bash
git add .github/workflows/auto-draft-pr.yml Makefile \
        experiments/baselines/s0_040_wiring_verification_seed42 \
        tasks tools/harvest_runindex.py
git status --porcelain
```

コミットの説明に、**取り込み元のコミットの識別子**と、**除外した理由**を書く。
派生物を除いたことが後から分かるようにする。

```bash
git commit -F - <<'MSG'
feat: integrate wiring verification results without host-local derivatives

配線検証とその後始末の成果を統合する。索引と軽量ビューは各ホストで再生成される
派生物であり、実行ホストにのみ残る退避物を含むため除外した。

取り込み元: exp/lecun-wip-20260703
除外: runindex/ context/auto/

統合後、各ホストで make runindex と make context の実行が必要である。
退避物を持たないホストで再生成したものを正本とすることが望ましい。
MSG
git log --oneline -1
```

- [ ] **Step 6: 起票する**

```bash
git push -u origin integrate/wiring-work-20260809
gh pr create --base phase0 --head integrate/wiring-work-20260809 \
  --title "feat: integrate wiring verification results (derivatives excluded)" \
  --body-file /dev/stdin <<'BODY'
## 範囲

配線検証とその後始末の成果のうち、**各ホストで再生成される派生物を除いた**もの。

## 含むもの

（Task 1 Step 1 の一覧をここへ貼る）

## 除外したもの

- `runindex/` — 収穫器が各ホストで再生成する。実行ホストにのみ残る退避物 34 件を含む
- `context/auto/` — 索引からの派生物。索引と揃っていないと整合検査が失敗する

別ホストでの実測により、索引の行数は実行ホストでのみ 35 行多いことが確認されている。

## 統合後に必要なこと

各ホストで次を実行する。

    make setup
    make runindex && make context

**退避物を持たないホストで再生成したものを次の正本とすることが望ましい。**

## 既存の起票との関係

同じ内容を含む起票が別に存在する。**そちらは利用者が判断するまで閉じない。**
BODY
gh pr view --json number,url,isDraft,mergeable
```

**統合しない。自動統合も有効化しない。**

---

# Phase B — 退避物の棚卸し

## Task 2: 所在と由来を記録する

**Files:**
- Create: `tasks/T-2026-08-09-scoped-integration/leftover_inventory.md`

**移動も削除もしない。記録のみ。**

- [ ] **Step 1: 元の分岐へ戻る**

```bash
git checkout exp/lecun-wip-20260703
git branch --show-current
```

- [ ] **Step 2: 退避物を特定する**

既存の起票で索引に加わった経路から、元となるディレクトリを割り出す。

```bash
git diff --name-only origin/phase0...exp/lecun-wip-20260703 \
  | grep '^runindex/runs/' | sed 's|runindex/runs/||; s|\.json$||' | sort
```

**この命名から元のディレクトリを機械的に導けるかを、収穫器の実装で確かめる。**
導けなければ、索引の該当行から経路の列を読む。**推測で対応づけない。**

- [ ] **Step 3: 実体を確認する**

```bash
python - <<'PY'
import csv, pathlib
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
key = next((c for c in cols if c.endswith("ledger_key")), None)
pathcols = [c for c in cols if any(k in c.lower() for k in ("path", "dir", "workdir"))]
print("経路らしき列:", pathcols)
targets = [r for r in rows if any(s in str(r.get(key, "")) for s in ("_smoke_e3", "_smoke_v2_part3", "pre_redo_s0_smoke", "prior_no_eval_recipe"))]
print(f"該当: {len(targets)} 件")
for r in targets[:40]:
    p = next((r.get(c) for c in pathcols if r.get(c)), "")
    exists = pathlib.Path(p).exists() if p else None
    print(" -", r.get(key), "|", p, "|", "実在" if exists else "不明")
PY
```

- [ ] **Step 4: 追跡状況を調べる**

```bash
for d in $(python - <<'PY'
import csv, pathlib
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
key = next((c for c in cols if c.endswith("ledger_key")), None)
pathcols = [c for c in cols if any(k in c.lower() for k in ("path","dir","workdir"))]
seen=set()
for r in rows:
    if any(s in str(r.get(key,"")) for s in ("_smoke_e3","_smoke_v2_part3","pre_redo_s0_smoke","prior_no_eval_recipe")):
        p = next((r.get(c) for c in pathcols if r.get(c)), "")
        if p:
            parent = str(pathlib.Path(p).parent)
            if parent not in seen:
                seen.add(parent); print(parent)
PY
); do
  printf "%-70s " "$d"
  if git ls-files --error-unmatch "$d" >/dev/null 2>&1; then echo "追跡"; else echo "未追跡"; fi
done
```

- [ ] **Step 5: 由来を調べる**

```bash
for d in $(ls -d experiments/*/*smoke* experiments/*/*pre_redo* experiments/*/*prior_no_eval* 2>/dev/null | head -20); do
  echo "=== $d ==="
  ls -la "$d" | head -3
  stat -c '%y' "$d" 2>/dev/null
done
```

- [ ] **Step 6: 記録する**

```markdown
# 実行ホストに残る退避物の棚卸し（2026-08-09）

## 背景

別ホストでの実測により、索引の行数は次のとおりであった。

| ホスト | 索引の行数 |
|---|---|
| （記入） | （記入） |

差分は、このホストのディスクにのみ残るディレクトリを収穫器が拾ったことによる。
すべて除外済みであり、解析対象には入っていない。

## 一覧

| 経路 | 追跡 | 最終更新 | 索引での扱い |
|---|---|---|---|

## 由来

（判明した範囲。不明なものは UNKNOWN と明記）

## 影響

このホストで収穫器を回すたびに索引が変化し、作業ツリーが汚れる。
汚れた状態は常駐スクリプトによる自動統合を妨げる。

## 処置の案

移動も削除も行っていない。処置は利用者の判断による。

| 案 | 内容 | 影響 |
|---|---|---|
| （記入） | | |
```

**3 案以上を挙げ、それぞれの影響を書く。自分で選ばない。**

- [ ] **Step 7: G2 ゲート — 何も動かしていないことを確認する**

```bash
git status --porcelain experiments/ | head -20
ls -d experiments/*/*smoke* experiments/*/*pre_redo* experiments/*/*prior_no_eval* 2>/dev/null | wc -l
```

**Step 3 で確認した件数と一致すること。** 減っていれば `leftover_moved_or_deleted` として
即座に報告する。

- [ ] **Step 8: 記録を確定する**

```bash
git add tasks/T-2026-08-09-scoped-integration/leftover_inventory.md
git commit -m "docs(tasks): inventory host-local leftovers without moving them"
```

---

# Phase C — 自己契約

## Task 3: 完了判定

**Files:**
- Create: `tasks/T-2026-08-09-scoped-integration/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-09-scoped-integration; echo "exit=$?"
make task-preflight TASK=T-2026-08-09-scoped-integration; echo "exit=$?"
```

**母集団の警告が出るのは正常。** 出力を記録する。

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 分岐が統合先から派生 | `git merge-base --is-ancestor origin/phase0 integrate/wiring-work-20260809; echo $?` | 0 |
| 2 | 索引が含まれない | `git diff --name-only origin/phase0...integrate/wiring-work-20260809 \| grep -c '^runindex/'` | 0 |
| 3 | 軽量ビューが含まれない | 同上を `context/auto/` で | 0 |
| 4 | 一次証跡が含まれる | 同上を `experiments/baselines/s0_040` で | 7 |
| 5 | 契約が含まれる | 同上を `tasks/` で | 1 以上 |
| 6 | 収穫器が含まれる | 同上を `tools/harvest` で | 1 |
| 7 | ビルド定義が含まれる | 同上を `Makefile` で | 1 |
| 8 | 継続的統合の設定が含まれる | 同上を `.github/` で | 1 |
| 9 | 起票が作られた | `gh pr list --head integrate/wiring-work-20260809` | 1 件 |
| 10 | 退避物が動いていない | Task 2 Step 7 | 件数不変 |
| 11 | 契約検証が通る | `make task-validate` | exit 0 |
| 12 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 13 | 全体テストが不変 | `python -m pytest tests/ -q` | **開始前を先に測る** |
| 14 | 禁止領域が無変更 | `git diff --name-only origin/phase0...integrate/wiring-work-20260809 -- data/splits/ context/conventions.md src/` | 出力なし |

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Task 1 Step 1 の一覧（統合される経路と、除外された件数）
- 統合用の分岐の識別子と、起票の番号
- 退避物の一覧と、追跡状況・由来
- **処置の案（3 案以上）と、選ばなかった理由**
- 既存の起票をどう扱うべきかの所見
- **`deviations` を空にしない**
- §6 に、統合後に各ホストで再生成が必要であることを申し送る

- [ ] **Step 5: 受け皿へ書く**

`tasks/inbox.md` へ本 task の判断を 1 行以上置く。

- [ ] **Step 6: 送出**

```bash
git checkout integrate/wiring-work-20260809
git checkout exp/lecun-wip-20260703 -- tasks/T-2026-08-09-scoped-integration tasks/inbox.md
git add tasks/
git commit -m "docs(tasks): record the scoped integration"
git push origin integrate/wiring-work-20260809
```

**統合は行わない。** 起票の内容を提示して判断を仰ぐ。

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 派生物が範囲へ混入した | **G1 停止。** `derived_artifact_in_scope` |
| 取り込めない経路がある | 停止して報告。**推測で別の経路を取らない** |
| 退避物の元ディレクトリを特定できない | `UNKNOWN` と記録。**推測で対応づけない** |
| 退避物の件数が減った | **即座に報告。** `leftover_moved_or_deleted` |
| 既存の起票と競合する | **既存を閉じない。** 併存させ、判断を仰ぐ |
| 検査の一致件数が 0 だった | **別の探し方でも 0 になることを確かめてから**「無い」と結論する |
| 表への追記で列が壊れた | 列数を数えてから書き直す |
| 全体テストの失敗が開始前より増えた | 本 task が壊した。停止して報告 |
