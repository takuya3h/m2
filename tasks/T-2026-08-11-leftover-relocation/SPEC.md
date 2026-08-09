# 実行ホストにのみ残る過去の run を退避し、索引が正本と一致することを示す

**task_id:** `T-2026-08-11-leftover-relocation`
**kind:** `impl`
**depends_on:** `T-2026-08-10-branch-naming-and-canonical-index`
**実行ホスト:** `lecun`（分岐 `exp/lecun`）

---

## Goal

このホストのディスクにのみ、過去の run が 34 件残っている。**版管理の追跡下には無い。**
収穫器はファイルシステムを直接走査するため、このホストで索引を再生成すると
他ホストより 35 行多くなる。

| 影響 | 内容 |
|---|---|
| 1 | 索引を再生成すると作業ツリーが汚れる |
| 2 | 汚れた状態は自動統合を止める（実測済み） |
| 3 | このホストは索引の正本を作れない |

**参照可能な場所へ退避し、索引が正本と一致することを示す。**

## 退避対象（先行調査による分類）

| 分類 | 件数 |
|---|---|
| 動作確認 | 19 |
| 置き換え済み | 6 |
| 失敗した run | 5 |
| 中断した run | 4 |
| **計** | **34** |

**全件が版管理の追跡下に無く、索引では除外済みである。**
ただし**本 task で一件ずつ再確認する。** 先行調査の数値を持ち込まない。

## 退避先

```
~/m2-archive/20260811/
```

repo の外へ出す。**削除しない。** 将来参照する可能性があるため、
元の場所との対応を記録する。

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git branch --show-current    # exp/lecun
git fetch origin
git checkout -b feat/leftover-relocation origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **追跡下の実験証跡を移動・削除・変更する** |
| 2 | 退避物を**削除する**（移動のみ） |
| 3 | `data/splits/**` `context/conventions.md` `src/**` を変更する |
| 4 | 学習・評価コードを変更する |
| 5 | `tools/**` を変更する（**本 task の範囲外**） |
| 6 | `tasks/README.md` `README.md` `OPERATION.md` を変更する |
| 7 | 演算装置を使う |
| 8 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 9 | 統合する。自動統合を有効化する |
| 10 | 他ホストへ書き込む |

### 並行して進む作業との衝突を避ける

別ホストで別の作業が並行して進んでいる。**次には触らないこと。**

- `tools/harvest_runindex.py`
- `tasks/README.md` `README.md`
- `configs/` `.gitignore`
- `src/egosurgery/utils/tracking.py`

**本 task が触るのは、このホストのディスクと自分の契約ディレクトリのみである。**

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが 8 task 連続で発生している。
**退避物の検索パターンも過去に不完全で、実行者が索引から逆引きして補正した。**

**本 SPEC の検査も同型の誤りを含みうる。** 次の点に注意すること。

| # | 注意 |
|---|---|
| 1 | 検索パターンが不完全な前提で、**複数の探し方で件数を照合する** |
| 2 | 一致件数が 0 のとき、別の探し方でも 0 になることを確かめる |
| 3 | 移動の前後で**ファイル数と容量を照合する** |

**取り返しがつかない操作である。控えを作ってから動かすこと。**

---

# Phase A — 対象の確定

## Task 1: 退避対象を一件ずつ確定する

**Files:**
- Create: `tasks/T-2026-08-11-leftover-relocation/relocation_log.md`

- [ ] **Step 1: 索引を再生成して差を測る**

```bash
BEFORE=$(( $(wc -l < runindex/index.csv) - 1 ))
md5sum runindex/*.csv > /tmp/idx_before.txt
make runindex 2>&1 | tail -10
AFTER=$(( $(wc -l < runindex/index.csv) - 1 ))
echo "索引: $BEFORE -> $AFTER (差 $((AFTER-BEFORE)))"
```

**この差が退避対象の規模である。** 先行調査の 34 という数と照合する。
食い違えば、**実測に従い記録する。**

- [ ] **Step 2: 増えた行を特定する**

```bash
python - <<'PY'
import csv, subprocess, pathlib
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
key = next((c for c in cols if c.endswith("ledger_key")), None)
pathcols = [c for c in cols if any(k in c.lower() for k in ("path", "dir", "workdir"))]
untracked = []
for r in rows:
    p = next((r.get(c) for c in pathcols if r.get(c)), "")
    if not p:
        continue
    rc = subprocess.run(["git", "ls-files", "--error-unmatch", p],
                        capture_output=True).returncode
    if rc != 0:
        untracked.append((r.get(key), p))
print(f"追跡外の経路を持つ行: {len(untracked)}")
for k, p in untracked:
    print(f"  {k}\t{p}")
PY
```

**これが一次の一覧である。**

- [ ] **Step 3: 別の探し方で照合する**

**同じ探し方を繰り返さない。ディスク側から探す。**

```bash
echo "===== ディスク上の未追跡ディレクトリ ====="
find experiments transfer -maxdepth 3 -type d 2>/dev/null | while read -r d; do
  [ -f "$d/config.yaml" ] || continue
  git ls-files --error-unmatch "$d" >/dev/null 2>&1 || echo "$d"
done | sort
echo "===== 件数 ====="
find experiments transfer -maxdepth 3 -type d 2>/dev/null | while read -r d; do
  [ -f "$d/config.yaml" ] || continue
  git ls-files --error-unmatch "$d" >/dev/null 2>&1 || echo "$d"
done | wc -l
```

**Step 2 の件数と一致するか。** 一致しなければ、**どちらが正しいかを調べる。**
一致するまで先へ進まない。

- [ ] **Step 4: 追跡下のものが混ざっていないことを確認する**

```bash
# Step 2 と Step 3 で得た一覧の各経路について
while read -r d; do
  printf "%-70s " "$d"
  if git ls-files --error-unmatch "$d" >/dev/null 2>&1; then
    echo "!!! 追跡下（退避対象から外す）"
  else
    echo "未追跡"
  fi
done < /tmp/leftover_list.txt
```

**追跡下のものが1件でもあれば、その経路を退避対象から外す。**
`tracked_artifact_moved` を防ぐための最重要の確認である。

- [ ] **Step 5: 控えを作る**

```bash
mkdir -p ~/m2-archive/20260811
echo "===== 移動前の状態 ====="
while read -r d; do
  n=$(find "$d" -type f 2>/dev/null | wc -l)
  s=$(du -sk "$d" 2>/dev/null | cut -f1)
  printf "%-70s %6s files %8s KB\n" "$d" "$n" "$s"
done < /tmp/leftover_list.txt | tee ~/m2-archive/20260811/manifest_before.txt

echo "===== 合計 ====="
awk '{f+=$2; s+=$4} END {print "files:", f, " KB:", s}' ~/m2-archive/20260811/manifest_before.txt
```

**この控えが、移動後の照合の基準になる。**

- [ ] **Step 6: 索引を元へ戻す**

```bash
git checkout -- runindex/ context/auto/ 2>/dev/null
git status --porcelain --untracked-files=normal runindex/ | head
```

**新しく現れた未追跡の記録ファイルがあれば削除する。**

```bash
git status --porcelain runindex/ | grep '^??' | awk '{print $2}' | xargs -r rm -f
git status --porcelain | grep -E "runindex/|context/auto/" && echo "残っている" || echo "復元済み"
```

- [ ] **Step 7: G1 ゲート**

| 確認 | 期待 |
|---|---|
| 一覧の件数が 2 通りの探し方で一致 | 一致 |
| 追跡下のものが含まれない | 0 件 |
| 控えが作られた | ファイル数と容量が記録されている |
| 索引が復元された | 差分なし |

**一つでも満たさなければ停止して報告する。**

---

# Phase B — 退避と照合

## Task 2: 退避する

**Files:** このホストのディスクのみ

- [ ] **Step 1: 退避先を用意する**

```bash
mkdir -p ~/m2-archive/20260811
ls -la ~/m2-archive/20260811/
```

- [ ] **Step 2: 移動する**

**一件ずつ、元の階層構造を保って移す。**

```bash
while read -r d; do
  dest=~/m2-archive/20260811/"$d"
  mkdir -p "$(dirname "$dest")"
  mv "$d" "$dest" || { echo "!!! 移動に失敗: $d"; break; }
  echo "moved: $d -> $dest"
done < /tmp/leftover_list.txt
```

**失敗したらそこで止める。** 中途半端な状態を作らない。

- [ ] **Step 3: 移動後の照合**

```bash
echo "===== 移動後の状態 ====="
while read -r d; do
  dest=~/m2-archive/20260811/"$d"
  n=$(find "$dest" -type f 2>/dev/null | wc -l)
  s=$(du -sk "$dest" 2>/dev/null | cut -f1)
  printf "%-70s %6s files %8s KB\n" "$d" "$n" "$s"
done < /tmp/leftover_list.txt | tee ~/m2-archive/20260811/manifest_after.txt

echo "===== 照合 ====="
diff <(awk '{print $1, $2, $4}' ~/m2-archive/20260811/manifest_before.txt) \
     <(awk '{print $1, $2, $4}' ~/m2-archive/20260811/manifest_after.txt) \
  && echo "一致" || echo "!!! 不一致"
```

**不一致なら停止して報告する**（`file_count_mismatch`）。

- [ ] **Step 4: 元の場所が空になったことを確認する**

```bash
while read -r d; do
  [ -e "$d" ] && echo "!!! まだ存在する: $d"
done < /tmp/leftover_list.txt
echo "（何も出なければ移動完了）"
```

- [ ] **Step 5: 追跡下のものが動いていないことを確認する**

```bash
git status --porcelain | grep -E "^ D|^D " && echo "!!! 追跡下のものが消えている" || echo "追跡下は無事"
git status --porcelain | head -20
```

**削除された追跡物があれば、即座に戻して報告する**（`tracked_artifact_moved`）。

```bash
# 戻す場合
# git checkout -- <経路>
```

---

## Task 3: 索引が正本と一致することを示す

- [ ] **Step 1: 再生成する**

```bash
make runindex 2>&1 | tail -10
ROWS=$(( $(wc -l < runindex/index.csv) - 1 ))
echo "行数: $ROWS"
```

- [ ] **Step 2: 正本と照合する**

```bash
echo "===== 正本（統合先）との差 ====="
git diff --stat runindex/index.csv
git status --porcelain runindex/ context/auto/
```

Expected: **差分なし**

差分がある場合、**行数だけでなく内容の差を調べる。**

```bash
git diff runindex/index.csv | head -40
```

- [ ] **Step 3: 追跡外の経路を持つ行が無いことを確認する**

```bash
python - <<'PY'
import csv, subprocess
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
pathcols = [c for c in cols if any(k in c.lower() for k in ("path", "dir", "workdir"))]
n = 0
for r in rows:
    p = next((r.get(c) for c in pathcols if r.get(c)), "")
    if not p:
        continue
    if subprocess.run(["git", "ls-files", "--error-unmatch", p],
                      capture_output=True).returncode != 0:
        n += 1
        if n <= 10:
            print("追跡外:", p)
print(f"追跡外の経路を持つ行: {n}")
PY
```

Expected: **0 件**

**0 件になれば、このホストは正本を生成できる条件を満たす。**

- [ ] **Step 4: G2 ゲート**

| 確認 | 期待 |
|---|---|
| 索引に差分が無い | 差分なし |
| 追跡外の経路が 0 件 | 0 |
| 作業ツリーが清潔 | 契約の記録以外なし |

**満たさなければ停止して報告する**（`index_mismatch_after_relocation`）。

---

# Phase C — 記録

## Task 4: 記録して起票する

**Files:**
- Create: `tasks/T-2026-08-11-leftover-relocation/{relocation_log.md,RESULT.md}`

- [ ] **Step 1: 退避の記録を書く**

**表の列数を数えてから書く。本文に半角パイプを書かない。**

```markdown
# 退避の記録（2026-08-11）

## 退避先

    ~/m2-archive/20260811/

元の階層構造を保って移動した。**削除していない。**

## 対応表

| 元の場所 | ファイル数 | 容量 | 分類 |
|---|---|---|---|

## 照合

| 項目 | 移動前 | 移動後 |
|---|---|---|
| 合計ファイル数 | | |
| 合計容量 | | |

## 索引への影響

| 項目 | 退避前 | 退避後 |
|---|---|---|
| 行数 | | |
| 追跡外の経路を持つ行 | | |

## 戻す方法

    # 必要になった場合
    cd ~/m2-archive/20260811
    # 元の相対パスへ戻す
```

**戻す手順を必ず書く。** 退避は不可逆であってはならない。

- [ ] **Step 2: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 3: 自己検証**

```bash
make task-validate TASK=T-2026-08-11-leftover-relocation; echo "exit=$?"
make task-preflight TASK=T-2026-08-11-leftover-relocation; echo "exit=$?"
```

- [ ] **Step 4: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 2 通りの探し方で件数が一致 | Task 1 Step 3 | 一致 |
| 2 | 追跡下のものを含まない | Task 1 Step 4 | 0 件 |
| 3 | 控えが作られた | `ls ~/m2-archive/20260811/manifest_before.txt` | 存在 |
| 4 | 移動前後でファイル数が一致 | Task 2 Step 3 | 一致 |
| 5 | 元の場所が空 | Task 2 Step 4 | 何も出ない |
| 6 | 追跡下が削除されていない | Task 2 Step 5 | 削除なし |
| 7 | 索引に差分が無い | Task 3 Step 2 | 差分なし |
| 8 | 追跡外の経路が 0 件 | Task 3 Step 3 | 0 |
| 9 | 退避物が残っている | `du -sh ~/m2-archive/20260811` | 容量あり |
| 10 | 戻す手順が書かれている | `relocation_log.md` | 記載あり |
| 11 | 契約検証が通る | `make task-validate` | exit 0 |
| 12 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 13 | 試験が不変 | `pytest tests/ -q` | **開始前を先に測る** |
| 14 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- data/splits/ context/conventions.md src/ tools/ tasks/README.md README.md OPERATION.md configs/` | 出力なし |

**判定14で、並行作業との衝突がないことを確認する。**

- [ ] **Step 5: `RESULT.md` を書く**

必ず含めるもの。

- 索引の差（実測値。先行調査の数と食い違えば明示）
- 2 通りの探し方の件数と、一致しなかった場合の調査
- 退避した経路の一覧と分類
- 移動前後の照合結果
- 退避後の索引の行数と、追跡外の経路の件数
- **このホストが正本を生成できる条件を満たしたか**
- **`deviations` を空にしない**
- §6 に、既存の起票の扱いについての所見を書く

- [ ] **Step 6: 受け皿へ書く**

`tasks/inbox.md` へ本 task の判断を 1 行以上置く。

- [ ] **Step 7: 起票**

```bash
git add tasks/T-2026-08-11-leftover-relocation/ tasks/inbox.md
git commit -m "docs(tasks): relocate host-local leftovers and verify index parity"
git push -u origin feat/leftover-relocation
gh pr create --base phase0 \
  --title "chore: relocate host-local leftovers so the index matches the canonical one" \
  --body-file tasks/T-2026-08-11-leftover-relocation/RESULT.md
```

**統合しない。自動統合も有効化しない。**

**索引は記録しない。** 差分が無いことを確認するのが目的であり、記録する必要は無い。

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 2 通りの探し方で件数が違う | **停止。** どちらが正しいかを調べてから進む |
| 追跡下のものが一覧に含まれる | **退避対象から外す。** 件数を減らして記録する |
| 移動に失敗した | **そこで止める。** 中途半端な状態を報告 |
| 移動前後でファイル数が違う | **G2 停止。** `file_count_mismatch` |
| 追跡下のものが消えた | **即座に戻して報告。** `tracked_artifact_moved` |
| 退避後も索引に差分がある | **G2 停止。** 差分の内容を調べて報告 |
| 追跡外の経路が 0 にならない | 残った経路を列挙して報告。**追加で退避しない** |
| 退避先に空き容量が無い | 停止して報告。**削除で対処しない** |
| 試験の failed が開始前より増えた | 本 task が壊した。停止して報告 |
