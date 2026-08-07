# 最小の学習を一本走らせ、自動同期と識別子の刻印が働くことを確かめる

**task_id:** `T-2026-08-09-run-wiring-verification`
**kind:** `impl`
**depends_on:** `T-2026-08-08-session-durability`（PR #50・マージ済み）
**実行ホスト:** `lecun`（これまでの契約はすべて別ホストで実行されている）

---

## Goal

学習を伴う配線のうち、**一度も発火していないもの**が3つある。

| # | 対象 | 現状 |
|---|---|---|
| 1 | `git_autosync.py`（502 行） | `finalize()` からの配線は済んでいるが**発火 0 件** |
| 2 | 配備鍵での遠隔操作 | これまでの実行ホストは通常鍵のため**未検証** |
| 3 | 契約の識別子を成果物へ刻む | 列は存在するが**該当 run が 0 件** |

**最小の学習を一本走らせて、3つを同時に検証する。**

## 起票者からの重要な注記

### 接頭辞について

利用者の当初案では動作確認用の接頭辞を付ける想定だったが、**本 task では付けない。**
その接頭辞は収穫器の除外規約に該当し、識別子を刻んでも索引に現れないため、
上記3の検証が成立しない。

索引に 1 行増えるが、対照実験の宣言を持たないため既存の比較には影響しない。
不要になれば後から除外規則を足せる。**この判断の是非を RESULT に記録すること。**

### 演算装置について

**本 task では装置 0 を使用してはならない。これは無条件の制約である。**

装置 0 は使用可否を判定しない。実測時点の使用量にかかわらず、また他の利用者の処理が
終了したように見えても、**装置 0 を選択肢から除外する。** 本 task は他の利用者の
作業状況を確認する手段を持たないため、空いているように見えることを根拠にできない。

起票時点で装置 0 は他の利用者が使用していた（約 13.8 GB）。ただし**これは禁止の理由で
あって条件ではない。** 使用量が減っていても禁止は解けない。

使うのは装置 1 のみ。`CUDA_VISIBLE_DEVICES` を明示的に固定する。
装置 0 に触れた場合は `other_user_gpu_touched` として即座に停止し報告する。

### 環境の差について

本 task はこれまでと異なるホストで実行される。基盤は取り込み済み（`behind` が 0）だが、
**それが実際に動くかは未確認である。** Phase A で確かめる。

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2 2>/dev/null || cd ~/m2
git branch --show-current    # exp/lecun-wip-20260703 のはず
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **装置 0 を使う（理由・使用量を問わず無条件で禁止）。他の利用者の処理に触れる** |
| 2 | `runindex/**` `context/auto/**` を手で編集する |
| 3 | 既存の `experiments/**` `transfer/**` を変更・削除する |
| 4 | `data/splits/**` を変更する |
| 5 | 学習・評価コードを変更する（**配線の確認が目的であり、修正ではない**） |
| 6 | `context/conventions.md` を変更する |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | 長時間の学習を回す（**目安 30 分以内**） |
| 9 | 分岐を統合する。遠隔へ強制的に書き込む |

### 起票者からの申し送り

過去 4 task で、起票者が書いた検証コマンドが検証対象を検証できていない誤りが連続した。
直近では、秘匿の混入検査が `sk-` を `task-id` の一部に一致させて偽陽性を出した。
**本 SPEC の検査も同型の誤りを含みうる。** 一致した件数だけで判断せず、
**何に一致したのかを目視で確かめてから結論を出すこと。**

---

# Phase A — 事前確認

## Task 1: 基盤が動くことを確かめる

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 分岐と基盤の状態**

```bash
git branch --show-current
git fetch origin
git rev-list --count HEAD..origin/phase0    # 0 のはず
git status --porcelain | head -20
```

**未コミットの変更があれば、内容を確認して RESULT へ記録する。** 触らない。

- [ ] **Step 2: 検証系が動くか**

```bash
make task-validate 2>&1 | tail -20; echo "exit=$?"
make task-preflight TASK=T-2026-08-09-run-wiring-verification 2>&1; echo "exit=$?"
ls -la tools/ | grep -E "validate_task|preflight_task|build_context|fetch_task|session_digest"
ls -d .claude/skills/task .codex/skills/task 2>&1
```

**動かなければ停止して報告する。** 基盤が届いていないことになる。

- [ ] **Step 3: 遠隔参照を試す（G1 の一部）**

```bash
git config --get remote.origin.url
git config --get remote.origin.pushurl
git config --get core.sshCommand
echo "--- 遠隔参照 ---"
GIT_SSH_COMMAND="$(git config --get core.sshCommand)" git ls-remote origin HEAD 2>&1 | head -3
echo "exit=$?"
```

**失敗したら停止して報告する**（`remote_reference_failed`）。以降の自動送出が成立しない。

- [ ] **Step 4: 演算装置の空き（G1 の一部）**

```bash
nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv
```

**確認するのは装置 1 が空いているかどうかだけである。**

**装置 0 の使用量は記録するが、判定には使わない。** 装置 0 が空いていても使わない。
「空いたので使ってよい」という判断は本 task では成立しない。

装置 1 も使用中なら停止して報告する。**装置 0 へ振り替えない。**

- [ ] **Step 5: 最小の学習設定を特定する**

**推測で設定を選ばない。実測で最短のものを見つける。**

```bash
ls configs/ configs/experiment/ configs/train/ configs/stage/ 2>/dev/null
echo "===== 実験管理を経由する経路 ====="
grep -rn "ExperimentManager" src/ scripts/ --include=*.py | head -20
echo "===== finalize から自動同期への配線 ====="
grep -rn "git_autosync\|finalize" src/egosurgery/engines/*_trainer.py | head -20
echo "===== 短く回せそうな設定 ====="
grep -rln "max_epochs\|epochs" configs/ | head -20
```

**確認すべき点**

| # | 内容 |
|---|---|
| 1 | どの経路が `ExperimentManager` を通り、`finalize()` を呼ぶか |
| 2 | その経路で使う仮想環境はどちらか |
| 3 | 反復回数や学習量を小さくする指定方法 |
| 4 | 成果物の出力先 |

**`finalize()` を通らない経路を選ぶと、自動同期は発火しない。** ここが本 task の要である。

- [ ] **Step 6: 実行計画を提示する**

実行する具体的なコマンド、想定所要時間、生成される成果物の場所を**利用者へ提示し、
承認を得てから Phase B へ進む。** GPU を使う前の最後の確認点である。

RESULT §1 に、Step 1 から Step 5 の実測をすべて記録する。

---

# Phase B — 最小の学習

## Task 2: 一本走らせる

**Files:** 学習が生成する成果物のみ

- [ ] **Step 1: 識別子を刻む方法を確認する**

契約の識別子を生成物の設定へ入れる。`outputs.stamp.task_id_in` は `config.yaml` を指す。

```bash
grep -rn "config.yaml" src/egosurgery/ --include=*.py | head -10
grep -rn "def finalize" -A 30 src/egosurgery/engines/*_trainer.py | head -60
```

**設定の保存経路を実測してから決める。** 上書きの手段は次のいずれか。

| 案 | 方法 |
|---|---|
| A | 学習の起動時に設定へ `task_id` を渡す |
| B | 成果物の生成後に `config.yaml` へ追記する |

**A が望ましい。** B は生成物の後付け改変であり、再現性の観点で弱い。
A が使えない場合、B を採る理由を RESULT へ記録する。

- [ ] **Step 2: 装置を固定して起動する**

```bash
export CUDA_VISIBLE_DEVICES=1
nvidia-smi --query-gpu=index,memory.used --format=csv
# Phase A Step 6 で承認された経路と仮想環境で起動する
```

**`CUDA_VISIBLE_DEVICES=1` を必ず設定する。** 起動直後に装置 0 の使用量が
変わっていないことを確認する。

- [ ] **Step 3: 完走を待つ**

進行状況を記録する。**30 分を大きく超える場合は中断して報告する。**

- [ ] **Step 4: G2 ゲート — 成果物と刻印を確認する**

```bash
NEWDIR=$(ls -1dt experiments/*/*/ 2>/dev/null | head -1)
echo "NEWDIR=$NEWDIR"
ls -la "$NEWDIR"
echo "===== 六点の証跡 ====="
for f in config.yaml metrics.json notes.md; do
  printf "%-16s " "$f"; [ -f "$NEWDIR/$f" ] && echo "あり" || echo "なし"
done
ls -d "$NEWDIR"/{logs,checkpoints,predictions} 2>/dev/null
echo "===== 識別子の刻印 ====="
grep -n "task_id" "$NEWDIR/config.yaml" || echo "刻まれていない"
```

**刻まれていなければ停止して報告する。** 索引への反映が成立しない。

- [ ] **Step 5: 装置 0 に触れていないことを確認する**

```bash
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv
```

**自分の処理が装置 0 に現れていたら、即座に報告する**（`other_user_gpu_touched`）。

---

# Phase C — 自動同期の実測

## Task 3: 発火したかを測る

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 自動記録が走ったか**

```bash
git log --oneline -5
git status --porcelain | head -20
```

- [ ] **Step 2: 自動送出が走ったか**

```bash
BR=$(git branch --show-current)
git rev-list --count "origin/$BR..HEAD" 2>&1    # 0 なら送出済み
git log --oneline -1 "origin/$BR" 2>&1
```

- [ ] **Step 3: 記録を読む**

```bash
ls -la ~/claude-sync/ 2>/dev/null | head
grep 'git_autosync' ~/claude-sync/sync-alerts.log 2>/dev/null | tail -10 || echo "該当行なし"
echo "===== 直近の全行 ====="
tail -20 ~/claude-sync/sync-alerts.log 2>/dev/null
```

**「該当行なし」の場合、発火していない。** その事実をそのまま記録する。

- [ ] **Step 4: 不発火なら理由を特定する**

```bash
grep -n "AutoSyncResult\|reason\|skip" tools/git_autosync.py src/egosurgery/**/git_autosync.py 2>/dev/null | head -20
grep -rn "git_autosync" src/egosurgery/engines/*_trainer.py
```

**実装を読んで、どの条件で見送られるかを特定する。** 該当する条件を実測で確かめる。
特定できなければ `UNKNOWN` と記録し、**推測で理由を書かない。**

- [ ] **Step 5: 下書きの起票を確認する**

```bash
BR=$(git branch --show-current)
gh pr list --head "$BR" --state open --json number,isDraft,title 2>&1
ls .github/workflows/
```

- [ ] **Step 6: G3 ゲート — 結果を分類する**

| 観測 | 記録 |
|---|---|
| 記録・送出・起票がすべて走った | 配線は機能している |
| 一部だけ走った | どこで止まったかを特定 |
| 何も走らなかった | 理由を実装から特定。できなければ `UNKNOWN` |

`on_fail: ask` である。**発火しなくても自動で停止せず、結果と理由を提示して判断を仰ぐ。**
本 task の目的は実測であり、修正ではない。**この場で `git_autosync.py` を直さないこと。**

---

# Phase D — 索引への反映

## Task 4: 識別子が索引に載ることを確かめる

**Files:**
- Modify: `runindex/**`（`make runindex` による再生成）
- Modify: `context/auto/**`（`make context` による再生成）

- [ ] **Step 1: 再生成前の状態を保存する**

```bash
python - <<'PY'
import csv
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
n_task = sum(1 for r in rows if r.get("task_id"))
print(f"行数: {len(rows)}  task_id を持つ行: {n_task}")
PY
md5sum runindex/*.csv
```

- [ ] **Step 2: 再生成する**

```bash
make runindex 2>&1 | tail -20
```

- [ ] **Step 3: 反映を確認する**

```bash
python - <<'PY'
import csv
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
hits = [r for r in rows if r.get("task_id")]
print(f"行数: {len(rows)}  task_id を持つ行: {len(hits)}")
for r in hits:
    key = next((c for c in r if c.endswith("ledger_key")), None)
    print(" -", r.get(key), "->", r.get("task_id"))
PY
```

Expected: 行数が 1 増え、`task_id` を持つ行が 1 件現れる

**行数の増分が 1 でなければ報告する**（`index_row_count_unexpected`）。
除外された場合は、その理由も記録する。

- [ ] **Step 4: 軽量ビューへ反映する**

```bash
make context
make context-check; echo "exit=$?"
grep -n "task_id を持つ run" context/auto/STATE.md
grep -n "task_ids" context/auto/experiments_summary.csv | head -3
```

**充足率が 0 から動くことを確認する。** これが④の最終的な証拠である。

- [ ] **Step 5: 検査系の未確認経路を確かめる**

これまで実行前検査の一部は合格経路が未検証だった。**このホストには両方の仮想環境がある。**

```bash
echo "===== 拡張の読み込み ====="
bash -c 'source .venv-relation-detr/bin/activate 2>/dev/null && python -c "
import importlib
try:
    importlib.import_module(\"models.bricks.relation_transformer\")
    print(\"import: OK\")
except Exception as e:
    print(\"import: NG\", type(e).__name__, e)
"' || echo "仮想環境が無い"
echo "===== 凍結源の照合 ====="
CKPT=third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
[ -f "$CKPT" ] && sha256sum "$CKPT" || echo "見つからない"
grep -n "03936318" context/conventions.md | head -2
```

**実測結果を RESULT へ記録する。** 一致しなければ報告する。この Step は
検査系の合格経路が実在することを示すためのものであり、契約の検査そのものではない。

- [ ] **Step 6: commit**

```bash
git add runindex/ context/auto/
git commit -m "chore(runindex): reflect the wiring verification run"
```

**自動記録が既に走っている場合、対象が重複しないか確認する。**

---

## Task 5: 自己契約の完了判定

**Files:**
- Create: `tasks/T-2026-08-09-run-wiring-verification/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-09-run-wiring-verification; echo "exit=$?"
make task-preflight TASK=T-2026-08-09-run-wiring-verification; echo "exit=$?"
```

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 基盤が動く | Task 1 Step 2 | 両方 exit 0 |
| 2 | 遠隔参照が成功 | Task 1 Step 3 | 成功 |
| 3 | 学習が完走 | Task 2 Step 4 | 成果物あり |
| 4 | 識別子が刻まれた | 同上 | `config.yaml` に含まれる |
| 5 | 装置 0 に触れていない | Task 2 Step 5 | 自分の処理が無い |
| 6 | 自動同期の結果が記録 | Task 3 Step 6 | 発火または理由 |
| 7 | 索引に載る | Task 4 Step 3 | 1 件 |
| 8 | 充足率が動く | Task 4 Step 4 | 0 から変化 |
| 9 | 軽量ビューが整合 | 同上 | `context-check` が 0 |
| 10 | 契約検証が通る | `make task-validate` | exit 0 |
| 11 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 12 | 全体テストが不変 | `python -m pytest tests/ -q` | **このホストでの実測値を記録** |
| 13 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- data/splits/ context/conventions.md src/` | 出力なし |

**判定12に注意**: 失敗件数の基準はホストによって異なりうる。**別ホストの値と比較せず、
本 task 開始前の値を先に測ってから比較する。** 開始前を測っていなければ `UNKNOWN` と記録する。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Phase A の実測すべて（分岐・基盤・遠隔参照・装置・最小設定の特定）
- 実行した具体的なコマンドと所要時間
- 識別子の刻印方法（A か B か、B ならその理由）
- **自動同期の発火状況。不発火なら理由、特定できなければ `UNKNOWN`**
- 索引の行数の変化と、載った行の識別子
- 検査系の未確認経路の実測（拡張の読み込み・凍結源の照合）
- 接頭辞を付けなかった判断の是非についての所見
- **`deviations` を空にしない**
- §6 に、後始末（生成した成果物を残すか消すか）の判断を仰ぐ旨を書く

- [ ] **Step 5: 受け皿へ書く**

`tasks/inbox.md` へ本 task の判断を 1 行以上置く。無ければ「なし」と明記する。

- [ ] **Step 6: 報告する**

**この task では PR を作らない。** 実行ホストが異なり、分岐も異なるため、
統合の方針を利用者へ確認してから決める。RESULT を提示して判断を仰ぐ。

```bash
git add tasks/T-2026-08-09-run-wiring-verification/ tasks/inbox.md
git commit -m "docs(tasks): record the wiring verification run"
git log --oneline -5
git rev-list --count "origin/$(git branch --show-current)..HEAD"
```

**後始末は指示を待つ。** 生成した成果物を自分の判断で削除しないこと。

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 基盤が動かない | **停止。** 何が欠けているかを列挙して報告 |
| 遠隔参照が失敗 | **G1 停止。** `remote_reference_failed` |
| 装置 1 も使用中 | **停止。** 他の利用者の処理を待つ。**装置 0 へ振り替えない** |
| 装置 0 が空いているように見える | **使わない。** 禁止は使用量を条件としない |
| 自分の処理が装置 0 に現れた | **即座に停止。** `other_user_gpu_touched` |
| `finalize()` を通る経路が特定できない | **停止して報告。** 通らない経路で走らせても本 task の目的を果たさない |
| 学習が 30 分を大きく超える | 中断して報告。設定を小さくする案を提示 |
| 識別子を刻めない | **G2 停止。** 刻印の経路が無いことは重要な発見であり、そのまま報告 |
| 自動同期が発火しない | **修正しない。** 理由を実測で特定し記録する。修正は別 task |
| 索引の行数が 1 以外の増分 | 報告。除外された場合は理由も |
| 全体テストの失敗が開始前より増えた | 本 task が壊した。停止して報告 |
