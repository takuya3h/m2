# 特定ホストにのみ残る分析成果物を、重い中間物を除いて共有可能にする

**task_id:** `T-2026-08-10-analysis-artifact-integration`
**kind:** `impl`
**depends_on:** `T-2026-08-10-third-host-verification`
**実行ホスト:** `efros`（**repo の場所が他ホストと異なる**）

---

## Goal

このホストに、追跡されていない分析成果物が 19 経路残っている。実測された容量は次のとおり。

| 対象 | 容量 |
|---|---|
| 重い中間生成物を含む 1 経路 | **47M** |
| 残り 18 経路の合計 | 約 1M |

内訳には、凍結源の照合、比較量の規約、再現性の分散、診断など、**研究の判断に直結する
報告書と表**が含まれる。これらがこのホストに閉じているため、他のホストからも、
分析を行う側からも読めない。

**重い中間生成物を除いて共有可能にする。**

## 47M の内訳（実測済み）

```
reextract/  45M   ← 特徴量の再抽出結果 2 ファイル
csv/       1.6M
json/        40K
env/         36K
報告書       20K
```

**中間生成物は取り込まない。** 報告書の結論を読むのに不要であり、再生成できる。

## 本 task の性質

**追加のみを行う。既存の追跡物には一切触れない。**
索引の再生成と記録も行わない（正本は別ホストで生成する規約による）。

---

## 0. 前提と禁止事項

**このホストは repo の場所が標準と異なる。決め打ちしないこと。**

```bash
R=""
for c in ~/slocal/m2 ~/slocal2/m2 /home/ubuntu/slocal/m2 ~/m2; do
  [ -d "$c/.git" ] && R="$c" && break
done
[ -z "$R" ] && R=$(find ~ -maxdepth 4 -type d -name .git -path "*m2*" 2>/dev/null | head -1 | xargs -r dirname)
echo "repo=$R"
cd "$R"
git fetch origin
git checkout -b feat/analysis-artifacts origin/phase0
source .venv/bin/activate
```

**一部のマウントが応答しない。** 探索コマンドが `Host is down` を出しても、
それは対象外の場所なので無視してよい。ただし**その事実を記録すること。**

| # | 禁止 |
|---|---|
| 1 | **既存の追跡物を変更・削除・移動する** |
| 2 | 重い中間生成物を取り込む |
| 3 | `runindex/**` `context/auto/**` を記録する |
| 4 | `data/splits/**` `context/conventions.md` `src/**` `tools/**` を変更する |
| 5 | 他ホストが更新する運用手順書を変更する |
| 6 | 演算装置を使う |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | 統合する。自動統合を有効化する |
| 9 | **秘匿らしき内容を含むファイルを取り込む** |

### 触ってはいけない文書

並行して別の作業が進んでおり、次の文書は**他の変更と衝突する。触らないこと。**

- 運用手順書
- 中枢の説明書
- 常駐設定の導入手順
- 契約の説明書

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが 8 task 連続で発生している。
直近では、常駐スクリプトへの検索が空を返したのを「該当なし」と扱ったが、
**別の探し方では実際の依存が見つかった。**

**本 SPEC の検査も同型の誤りを含みうる。** 特に秘匿の検査では、
**一致件数だけで判断せず、何に一致したのかを目視すること。**
過去に、無関係な語に一致して偽陽性が出ている。

---

# Phase A — 棚卸しと除外の確定

## Task 1: 対象を確定する

**Files:**
- Create: `tasks/T-2026-08-10-analysis-artifact-integration/artifact_inventory.md`

- [ ] **Step 1: 追跡外の対象を列挙する**

```bash
git status --porcelain | grep '^??' | awk '{print $2}' | while read -r p; do
  printf "%-64s %8s  %s\n" "$p" "$(du -sh "$p" 2>/dev/null | cut -f1)" \
    "$(find "$p" -type f 2>/dev/null | wc -l) files"
done
```

- [ ] **Step 2: 大きなファイルを特定する**

```bash
echo "===== 1M を超えるファイル ====="
git status --porcelain | grep '^??' | awk '{print $2}' | while read -r p; do
  find "$p" -type f -size +1M 2>/dev/null
done | while read -r f; do printf "%10s  %s\n" "$(du -h "$f" | cut -f1)" "$f"; done
```

- [ ] **Step 3: 拡張子ごとの分布を見る**

```bash
git status --porcelain | grep '^??' | awk '{print $2}' | while read -r p; do
  find "$p" -type f 2>/dev/null
done | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
```

- [ ] **Step 4: 除外対象を決める**

**除外の基準を先に決め、それに照らして判定する。**

| 基準 | 内容 |
|---|---|
| 1 | 単一ファイルが 1M を超える中間生成物 |
| 2 | 再生成できる特徴量や重み |
| 3 | 秘匿らしき内容を含むもの（Phase B で判定） |

**報告書と表と設定は残す。** 結論を読むために必要である。

- [ ] **Step 5: G1 ゲート — 一覧を作る**

```markdown
# 分析成果物の棚卸し（2026-08-10）

## 取り込む対象

| 経路 | 容量 | ファイル数 | 内容の要点 |
|---|---|---|---|

## 除外する対象

| 経路 | 容量 | 除外の理由 |
|---|---|---|

## 判断に迷ったもの

（あれば。理由とともに）
```

**表の列数を数えてから書く。本文に半角パイプを書かない。**

除外対象が 1 件も無い、あるいは想定より大幅に多い場合は、**停止して報告する。**

---

# Phase B — 秘匿と肥大の検査

## Task 2: 取り込んではいけない内容が無いか調べる

**Files:** なし（読み取りのみ）

一覧の中に、環境設定を保存したとみられるディレクトリがある。**資格情報が含まれうる。**

- [ ] **Step 1: 環境設定らしきものの中身を確認する**

```bash
find . -path ./.git -prune -o -type d -name "env" -print 2>/dev/null | while read -r d; do
  git ls-files --error-unmatch "$d" >/dev/null 2>&1 && continue
  echo "===== $d ====="
  ls -la "$d"
done
```

**ファイル名を先に見る。** いきなり中身を出力しない。

- [ ] **Step 2: 秘匿らしき代入を探す**

```bash
git status --porcelain | grep '^??' | awk '{print $2}' | while read -r p; do
  grep -rlIE "(API[_-]?KEY|SECRET|TOKEN|PASSWORD|PRIVATE[_-]?KEY)" "$p" 2>/dev/null
done | sort -u
```

**一致したファイルがあれば、その行を確認する。**

```bash
# 上で出たファイルについて、一致行の前後だけを見る
# 値そのものを画面へ出さないよう、変数名だけを確認すること
```

- [ ] **Step 3: 値らしき文字列を探す**

```bash
git status --porcelain | grep '^??' | awk '{print $2}' | while read -r p; do
  grep -rnIE "[A-Za-z0-9_-]{32,}" "$p" 2>/dev/null | head -20
done | head -40
```

**一致件数だけで判断しない。** ハッシュ値や識別子にも一致する。
**何に一致したのかを目視し、秘匿かどうかを判別する。**

- [ ] **Step 4: G2 ゲート — 判定する**

| 観測 | 対応 |
|---|---|
| 秘匿らしき値が無い | Phase C へ |
| 秘匿らしき値がある | **そのファイルまたはディレクトリを除外**し、一覧へ理由を記録 |
| 判別できない | **除外する。** 迷ったら取り込まない |

**取り込んでから消すことはできない。判別できないものは除外する。**

秘匿を発見した場合は `secret_found_in_artifact` として報告する。**値は書かない。**

---

# Phase C — 取り込みと索引への影響

## Task 3: 取り込む

**Files:**
- Add: Phase A と B で確定した対象のみ

- [ ] **Step 1: 除外を先に設定する**

除外対象が今後も生成される場合、`.gitignore` へ加える。

**パターンは狭くする。** 過去に、広いパターンが既存の追跡証跡を巻き込む事故が起きている。
**該当する経路を明示列挙するか、確実に限定される書き方にすること。**

```bash
git check-ignore -v <除外対象の経路> || echo "無視されていない"
```

- [ ] **Step 2: 取り込む**

```bash
# Phase A で確定した対象のみを個別に指定する
# git add . を使わないこと
```

**`git add .` を使わない。** 除外対象を巻き込む。

- [ ] **Step 3: 既存の追跡物に触れていないことを確認する**

```bash
echo "===== 変更または削除された既存物 ====="
git diff --cached --name-status | grep -vE "^A" && echo "!!! 追加以外がある" || echo "追加のみ"
echo "===== 容量 ====="
git diff --cached --stat | tail -3
```

**追加以外の操作があれば停止して報告する**（`existing_file_modified`）。

- [ ] **Step 4: 大きなファイルが混ざっていないことを確認する**

```bash
git diff --cached --name-only | while read -r f; do
  s=$(du -k "$f" 2>/dev/null | cut -f1)
  [ -n "$s" ] && [ "$s" -gt 1024 ] && printf "%8s KB  %s\n" "$s" "$f"
done
echo "（何も出なければ 1M 超は無い）"
```

- [ ] **Step 5: 記録する**

```bash
git commit -m "docs(analysis): share analysis reports and tables from a single host"
```

- [ ] **Step 6: G3 ゲート — 索引が変わらないことを確認する**

分析成果物は実験の証跡とは形式が異なるため、収穫器の対象外のはずである。
**しかし確かめる。**

```bash
BEFORE=$(( $(wc -l < runindex/index.csv) - 1 ))
md5sum runindex/*.csv > /tmp/idx_before.txt
make runindex 2>&1 | tail -5
AFTER=$(( $(wc -l < runindex/index.csv) - 1 ))
md5sum runindex/*.csv > /tmp/idx_after.txt
echo "行数: $BEFORE -> $AFTER"
diff /tmp/idx_before.txt /tmp/idx_after.txt && echo "索引 不変" || echo "索引が変化した"
git checkout -- runindex/ context/auto/ 2>/dev/null
git status --porcelain | grep -E "runindex/|context/auto/" && echo "!!! 戻しきれていない" || echo "復元済み"
```

Expected: 行数が変わらず、索引が不変

**変化した場合は停止して報告する**（`index_changed_by_artifacts`）。収穫器が分析成果物を
実験として拾っていることになり、**正本の定義に影響する。**

`on_fail: ask` である。判断を仰ぐ。

**索引と軽量ビューは記録しない。** 正本は別ホストで生成する規約による。

---

## Task 4: 自己契約と起票

**Files:**
- Create: `tasks/T-2026-08-10-analysis-artifact-integration/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-10-analysis-artifact-integration; echo "exit=$?"
make task-preflight TASK=T-2026-08-10-analysis-artifact-integration; echo "exit=$?"
```

**依存が入っていない場合は `make setup` を先に実行する。**

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 一覧が容量つきで作られた | `artifact_inventory.md` | 表が埋まっている |
| 2 | 重い中間物が入っていない | Task 3 Step 4 | 1M 超が 0 件 |
| 3 | 秘匿の検査を目視で行った | `RESULT.md` | 一致内容が記録されている |
| 4 | 追加のみ | Task 3 Step 3 | 追加以外なし |
| 5 | 索引が不変 | Task 3 Step 6 | 不変 |
| 6 | 索引を記録していない | `git diff --name-only origin/phase0...HEAD \| grep -c runindex` | 0 |
| 7 | 手順書に触れていない | `git diff --name-only origin/phase0...HEAD \| grep -cE "OPERATION.md\|README.md\|tasks/README.md\|host_autosync"` | 0 |
| 8 | 契約検証が通る | `make task-validate` | exit 0 |
| 9 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 10 | 試験が不変 | `python -m pytest tests/ -q` | **開始前を先に測る** |
| 11 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- data/splits/ context/conventions.md src/ tools/` | 出力なし |

**判定7が重要である。** 並行して進む作業と衝突しないことを保証する。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- repo の場所（標準と異なるため）
- 応答しないマウントがあった事実
- 取り込んだ対象と除外した対象の一覧
- **秘匿の検査で何に一致し、それをどう判別したか**
- 索引が変わらなかったことの実測
- 取り込んだ報告書の**表題の一覧**（何が読めるようになったか）
- **`deviations` を空にしない**
- §6 に、重い中間生成物がこのホストにのみ残ることを申し送る

- [ ] **Step 5: 受け皿へ書く**

`tasks/inbox.md` へ本 task の判断を 1 行以上置く。

- [ ] **Step 6: 起票**

```bash
git add tasks/T-2026-08-10-analysis-artifact-integration/ tasks/inbox.md
git commit -m "docs(tasks): record the analysis artifact integration"
git push -u origin feat/analysis-artifacts
gh pr create --base phase0 \
  --title "docs(analysis): share analysis reports from a single host" \
  --body-file tasks/T-2026-08-10-analysis-artifact-integration/RESULT.md
```

**統合しない。自動統合も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| repo が見つからない | 探索の結果を報告して停止 |
| マウントが応答しない | 対象外の場所なら無視し、事実を記録 |
| 秘匿らしき内容がある | **そのファイルを除外。** 値は書かない |
| 判別できない内容がある | **除外する。** 迷ったら取り込まない |
| 索引が変化した | **G3。** 判断を仰ぐ。**自分で規約を変えない** |
| 既存の追跡物に差分が出た | **即座に停止。** 追加のみのはずである |
| 除外対象が想定より多い | 一覧を提示して判断を仰ぐ |
| 依存が入っていない | `make setup` を実行し、結果を記録する |
| 試験の failed が開始前より増えた | 本 task が壊した。停止して報告 |
