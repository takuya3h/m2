# 三台目のホストで基盤と配線を再現し、索引の正本を作る

**task_id:** `T-2026-08-10-third-host-verification`
**kind:** `impl`
**depends_on:** `T-2026-08-09-scoped-integration`（PR #52・統合済み）
**実行ホスト:** `bengio`（分岐 `exp/Bengio-wip-20260703`）

---

## Goal

基盤はこれまで 2 台のホストでしか動いていない。**三台目で再現するかを確かめる。**

| # | 検証対象 | これまでの状況 |
|---|---|---|
| 1 | 依存の一括導入 | 一台でのみ確認。**他ホストは未検証**（前 task の申し送り） |
| 2 | 学習完了時の自動同期 | 一台でのみ発火。再現性は未確認 |
| 3 | 遠隔への送出 | 配備鍵のホストでのみ確認。**このホストは通常の鍵** |
| 4 | 索引の生成 | 一台に退避物が 34 件あり、索引が 35 行多い状態 |

**4 が本 task の最大の目的である。** このホストには退避物が無いことが実測済みであり、
ここで生成した索引は**退避物を含まない正本の候補**になる。

## このホストの既知の条件（実測済み）

| 項目 | 値 |
|---|---|
| 統合先との差 | 0（取り込み済み） |
| 仮想環境 | 2 種類あり |
| 仮想環境内の導入コマンド | **無い**（別の導入手段が必要） |
| 別の導入手段 | あり |
| 検証系の依存 | **未導入** |
| 遠隔操作の設定 | **通常の鍵**（配備鍵ではない） |
| 演算装置 | 2 基とも空き |
| 索引の行数 | 一台目と同一 |

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git branch --show-current    # exp/Bengio-wip-20260703
git log --oneline -1         # 統合先と一致しているはず
```

| # | 禁止 |
|---|---|
| 1 | 既存の `experiments/**` `transfer/**` を変更・削除する |
| 2 | `data/splits/**` `context/conventions.md` `src/**` を変更する |
| 3 | 学習・評価コードを変更する |
| 4 | `tools/**` を変更する（**本 task は再現の確認であり、修正ではない**） |
| 5 | 長時間の学習を回す（**目安 30 分以内**） |
| 6 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 7 | 統合する。自動統合を有効化する |
| 8 | 他ホストのファイルに触れる |

### 演算装置について

起票時点で 2 基とも空いている。**ただし他の利用者が使い始める可能性がある。**
起動前に必ず実測し、**使用中の装置には触れない。** 使う装置を明示的に固定すること。

### 起票者からの申し送り

**起票者の検査コマンドが検証対象を検証できていない誤りが 7 task 連続で発生している。**
直近では、退避物の検索パターンが不完全で、実行者が索引から逆引きして補正した。

**本 SPEC の検査も同型の誤りを含みうる。** 次の 2 点に注意すること。

| # | 注意 |
|---|---|
| 1 | **一致件数が 0 のとき、それが「無い」のか「探し方が悪い」のかを区別する。** 別の探し方でも 0 になることを確かめる |
| 2 | **仕組みの挙動は実装を読んでから信じる。** 記録の有無で発火を判定するような条件は、実装を読んで裏を取る |

---

# Phase A — 基盤の再現性

## Task 1: 依存の導入と検証系の確認

**Files:** なし（環境の変更のみ）

- [ ] **Step 1: 開始前の状態を測る**

```bash
git branch --show-current
git log --oneline -1
git status --porcelain | head -10
echo "===== 基盤 ====="
ls tools/*.py | wc -l
ls -d .claude/skills/task .codex/skills/task 2>&1
echo "===== 依存 ====="
.venv/bin/python -c "import jsonschema; print('jsonschema', jsonschema.__version__)" 2>&1 | tail -1
.venv/bin/python -c "import yaml; print('yaml OK')" 2>&1 | tail -1
echo "===== 試験の基準値 ====="
.venv/bin/python -m pytest tests/ -q 2>&1 | tail -3
```

**試験の失敗件数を必ず控える。** ホストによって基準が異なるため、
**別ホストの値と比較しない。** 本 task 開始前の値と比較する。

- [ ] **Step 2: 依存を一括導入する（G1 の一部）**

```bash
make setup 2>&1 | tail -30; echo "exit=$?"
```

**このホストで初めて実行される。** 前 task では別のホストでのみ確認された。

失敗した場合、**何が原因かを実装を読んで特定する。** `make setup` の中身を読み、
どの手段を試してどこで止まったかを記録する。**推測で代替コマンドを叩かない。**

- [ ] **Step 3: 導入されたことを確認する**

```bash
.venv/bin/python -c "import jsonschema, yaml; print('読み込み OK')"
echo "===== 冪等 ====="
make setup 2>&1 | tail -5; echo "exit=$?"
echo "===== 固定されている依存が動いていないか ====="
.venv/bin/python -c "import torch; print('torch', torch.__version__)" 2>&1 | tail -1
```

**導入コマンドが成功を返しても仮想環境に入っていない事例が実際に起きている。**
読み込みまで確認して初めて成功とする。

**固定されている依存が動いていたら停止して報告する。**

- [ ] **Step 4: 検証系が動くことを確認する（G1 の一部）**

```bash
make task-validate 2>&1 | tail -20; echo "exit=$?"
make task-preflight TASK=T-2026-08-10-third-host-verification 2>&1; echo "exit=$?"
```

Expected: 両方 `exit=0`。実行前検査は一部が未実施と表示される

- [ ] **Step 5: G1 ゲート**

`on_fail: ask` である。**動かなくても自動で停止せず、原因と代替案を提示して判断を仰ぐ。**

| 観測 | 対応 |
|---|---|
| すべて動いた | Phase B へ |
| 導入が失敗した | 原因を実装から特定し提示（`setup_failed_on_this_host`） |
| 検証系が動かない | 何が欠けているかを列挙して提示 |

---

# Phase B — 最小の学習

## Task 2: 配線が再現するか

**Files:** 学習が生成する成果物のみ

- [ ] **Step 1: 前例を読む**

**同じ検証が別ホストで実施済みである。手順を読んでから始める。**

```bash
sed -n '1,80p' tasks/T-2026-08-09-run-wiring-verification/RESULT.md
grep -n "実行したコマンド\|所要\|task_id" tasks/T-2026-08-09-run-wiring-verification/RESULT.md | head -20
cat experiments/baselines/s0_040_wiring_verification_seed42/command.sh
cat experiments/baselines/s0_040_wiring_verification_seed42/notes.md
```

**前例と同じ設定で回すのが望ましい。** 差が出た場合、それがホストの差である
ことを切り分けられる。設定を変える場合は理由を記録する。

- [ ] **Step 2: 遠隔操作を確認する**

```bash
git config --get remote.origin.url
git config --get remote.origin.pushurl
git config --get core.sshCommand
git ls-remote origin HEAD 2>&1 | head -3; echo "exit=$?"
```

**このホストは通常の鍵である。** 配備鍵のホストと経路が異なるため、
**自動送出が働くかは未知**である。失敗しても停止せず、記録して進む。

- [ ] **Step 3: 装置を確認して固定する**

```bash
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv
```

**空いている装置を一つ選び、明示的に固定する。** 使用中の装置には触れない。
選んだ装置と、その時点の使用量を記録する。

- [ ] **Step 4: 実行計画を提示する**

実行するコマンド、使う装置、想定所要時間、出力先を**利用者へ提示し、承認を得てから
進む。** 演算資源を使う前の最後の確認点である。

- [ ] **Step 5: 走らせる**

前例では極めて短時間で完了している。**大きく超える場合は中断して報告する。**

- [ ] **Step 6: G2 ゲート — 成果物と刻印**

```bash
NEWDIR=$(ls -1dt experiments/*/*/ 2>/dev/null | head -1)
echo "NEWDIR=$NEWDIR"
ls -la "$NEWDIR"
for f in config.yaml metrics.json notes.md command.sh git_commit.txt server.txt per_class_ap.json; do
  printf "%-18s " "$f"; [ -f "$NEWDIR/$f" ] && echo "あり" || echo "なし"
done
echo "===== 識別子 ====="
grep -n "task_id" "$NEWDIR/config.yaml" || echo "刻まれていない"
echo "===== ホスト名 ====="
cat "$NEWDIR/server.txt" 2>/dev/null
```

**刻まれていなければ停止して報告する。**

- [ ] **Step 7: 自動同期を測る**

**記録の有無で判定しない。** 別ホストでの実測により、その記録は中断時にのみ
書かれることが分かっている（未解決事項に起票済み）。

```bash
git log --oneline -5
git status --porcelain | head -10
BR=$(git branch --show-current)
git rev-list --count "origin/$BR..HEAD" 2>&1
echo "===== 遠隔の先頭 ====="
git log --oneline -1 "origin/$BR" 2>&1
echo "===== 起票 ====="
gh pr list --head "$BR" --state open --json number,isDraft,title 2>&1
```

| 観測 | 意味 |
|---|---|
| 新しいコミットがある | 自動記録が働いた |
| 遠隔との差が 0 | 自動送出も働いた |
| 差が残っている | 記録は働いたが送出は働かなかった |
| コミットが無い | 発火していない。**実装を読んで理由を特定する** |

**不発火なら `autosync_not_reproduced` として報告する。修正はしない。**

- [ ] **Step 8: 成果物の記述を埋める**

雛形のまま索引に載せない。**別ホストの前例に倣う。**

```bash
cat experiments/baselines/s0_040_wiring_verification_seed42/notes.md
```

**必ず含める**もの。

| # | 内容 |
|---|---|
| 1 | 配線の再現確認が目的であること |
| 2 | **性能の主張には使えない**こと |
| 3 | 対応する契約の識別子 |
| 4 | 対照実験の宣言を持たないこと |
| 5 | 実測値の転記（計算し直さない） |
| 6 | 使用した装置と所要時間 |

**収穫器が値を拾う書式に触れないよう、前例と同じ構成にすること。**
自動記録が既に走っている場合、追記が新たな差分になる点に注意する。

---

# Phase C — 索引の正本

## Task 3: 退避物を含まない索引を作る

**Files:**
- Modify: `runindex/**`（再生成）
- Modify: `context/auto/**`（再生成）
- Create: `tasks/T-2026-08-10-third-host-verification/host_parity.md`

- [ ] **Step 1: 再生成前を測る**

```bash
wc -l runindex/*.csv
python - <<'PY'
import csv
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
print("index の run 数:", len(rows))
print("識別子を持つ行:", sum(1 for r in rows if r.get("task_id")))
PY
md5sum runindex/*.csv
```

- [ ] **Step 2: 再生成する**

```bash
make runindex 2>&1 | tail -20
```

- [ ] **Step 3: G3 ゲート — 退避物が含まれないことを実測する**

```bash
python - <<'PY'
import csv, collections
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
key = next((c for c in cols if c.endswith("ledger_key")), None)
reason = "exclusion_reason" if "exclusion_reason" in cols else None
print("run 数:", len(rows))
print("識別子を持つ行:", sum(1 for r in rows if r.get("task_id")))
if reason:
    c = collections.Counter(r.get(reason, "") for r in rows)
    print("除外理由の内訳:")
    for k, v in c.most_common():
        print(f"  {k or '(なし)'}: {v}")
print("--- 追跡外の経路を含む行 ---")
import subprocess, pathlib
pathcols = [c for c in cols if any(k in c.lower() for k in ("path", "dir", "workdir"))]
untracked = 0
for r in rows:
    p = next((r.get(c) for c in pathcols if r.get(c)), "")
    if not p:
        continue
    rc = subprocess.run(["git", "ls-files", "--error-unmatch", p],
                        capture_output=True).returncode
    if rc != 0:
        untracked += 1
print("追跡外の経路を持つ行:", untracked)
PY
```

**別ホストで確認された退避物 34 件が現れないことを確かめる。**
現れたら停止して報告する（`index_contains_leftovers`）。

> 一致が 0 件のとき、探し方が悪い可能性を排除すること。除外理由の内訳と
> 追跡状況の両方から確かめる。

- [ ] **Step 4: 行数を説明する**

**増分を実測で説明できることが本 task の核心である。**

| 項目 | 期待 |
|---|---|
| 統合前のこのホストの run 数 | Step 1 の値 |
| 統合で加わった一次証跡 | 1 件 |
| 本 task で生成した run | 1 件 |
| **合計** | 説明できる値 |

**説明できない差があれば、その内訳を調べて記録する。**

- [ ] **Step 5: 軽量ビューを再生成する**

```bash
make context
make context-check; echo "exit=$?"
grep -n "task_id を持つ run" context/auto/STATE.md
head -8 context/auto/STATE.md
```

- [ ] **Step 6: ホスト間の差を記録する**

```markdown
# ホスト間の索引の差（2026-08-10）

## 実測

| ホスト | run 数 | 識別子を持つ行 | 退避物 | 測定日 |
|---|---|---|---|---|

## このホストで生成した索引の性質

（追跡外の経路を含むか、除外理由の内訳）

## 正本としての適否

（このホストで生成した索引を正本とすることの是非。**判断は利用者へ委ねる**）

## 依存導入の再現性

| ホスト | 仮想環境内の導入コマンド | 一括導入の結果 |
|---|---|---|

## 自動同期の再現性

| ホスト | 鍵の種類 | 自動記録 | 自動送出 | 起票 |
|---|---|---|---|---|
```

**表の列数を数えてから書く。本文に半角パイプを書かない。**

- [ ] **Step 7: 記録を確定する**

```bash
git add runindex/ context/auto/ tasks/T-2026-08-10-third-host-verification/host_parity.md
git status --porcelain | head -20
git commit -m "chore(runindex): regenerate the index on a host without leftovers"
```

---

## Task 4: 自己契約と完了判定

**Files:**
- Create: `tasks/T-2026-08-10-third-host-verification/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-10-third-host-verification; echo "exit=$?"
make task-preflight TASK=T-2026-08-10-third-host-verification; echo "exit=$?"
```

**母集団の警告が出るのは正常。**

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 依存の一括導入が働く | Task 1 Step 3 | 読み込み OK |
| 2 | 冪等 | 同上 | 2 回目も exit 0 |
| 3 | 固定依存が不変 | 同上 | 版が変わらない |
| 4 | 検証系が動く | Task 1 Step 4 | 両方 exit 0 |
| 5 | 学習が完走 | Task 2 Step 6 | 成果物あり |
| 6 | 識別子が刻まれた | 同上 | `config.yaml` に含まれる |
| 7 | 自動同期の結果が記録 | Task 2 Step 7 | 発火または理由 |
| 8 | 記述が雛形でない | `cat <run>/notes.md` | 埋まっている |
| 9 | 退避物が含まれない | Task 3 Step 3 | 該当 0 件 |
| 10 | 行数が説明できる | Task 3 Step 4 | 内訳が一致 |
| 11 | 軽量ビューが整合 | Task 3 Step 5 | exit 0 |
| 12 | 充足率が動く | 同上 | 0 でない |
| 13 | 契約検証が通る | `make task-validate` | exit 0 |
| 14 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 15 | 試験が不変 | `.venv/bin/python -m pytest tests/ -q` | **Task 1 Step 1 の値と一致** |
| 16 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- data/splits/ context/conventions.md src/ tools/` | 出力なし |

**判定15に注意**: 基準は Task 1 Step 1 で測った値である。**別ホストの値と比較しない。**

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Task 1 の実測（依存の状態・一括導入の出力・試験の基準値）
- 実行したコマンドと所要時間、使った装置
- 自動同期の結果。**不発火なら実装から特定した理由**
- 索引の行数と、その内訳の説明
- 追跡外の経路を持つ行の件数
- **前例のホストとの差**（あれば、それが何に由来するか）
- **`deviations` を空にしない**
- §6 に、残る未検証項目を申し送る

- [ ] **Step 5: 受け皿へ書く**

`tasks/inbox.md` へ本 task の判断を 1 行以上置く。

- [ ] **Step 6: 送出と起票**

```bash
git add tasks/T-2026-08-10-third-host-verification/ tasks/inbox.md
git commit -m "docs(tasks): record the third host verification"
BR=$(git branch --show-current)
git push origin "$BR" 2>&1 | tail -5
gh pr list --head "$BR" --state open --json number,url,title 2>&1
```

既に起票がある場合は**新たに作らず、内容を更新する。**

**統合は行わない。自動統合も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 依存の一括導入が失敗 | **G1。** 実装を読んで原因を特定し提示。**推測で代替を叩かない** |
| 固定されている依存の版が動いた | **停止して報告。** 環境を壊す一歩手前 |
| 装置が両方とも使用中 | **停止。** 他の利用者を待つ |
| 前例と同じ設定で回せない | 理由を記録し、変更点を明示して進む |
| 自動同期が発火しない | **修正しない。** 理由を実測で特定し記録 |
| 送出が失敗する | 鍵の種類の差による可能性。**記録して進む。停止しない** |
| 索引に退避物が現れた | **G3 停止。** このホストにも残置物がある |
| 行数が説明できない | 内訳を調べて記録。**推測で埋めない** |
| 試験の失敗が開始前より増えた | 本 task が壊した。停止して報告 |
