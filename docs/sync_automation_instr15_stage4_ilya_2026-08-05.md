# 指示書 #15 段 4 — auto-PR 実装報告

| | |
|---|---|
| 実施 | ilya（hostname `aolab` / `SERVERNAME=ilya`）, 2026-08-05 |
| ブランチ | `feat/sync-automation-20260805`（起点 `origin/phase0` = `37126cc`） |
| 対象 | `scripts/sync/m2-sync.sh` |
| commit | `f8c80db` feat(sync): add auto-PR after auto-push |
| 一次データ | 変更 0 件 |
| `keeper.sh` | 変更 0 件 |
| 自動 commit | 実装なし |
| 実際に作成された PR | **#41**（Draft・本実装そのものの PR として維持） |

---

## 0. 位置づけ

指示書 #15 段 4。段 1（設計調査）・段 2（alert / `.servername` / auto-push）・
段 3（auto-merge）に続き、`m2-sync.sh` に **auto-PR**（push した内容を
`phase0` へ向けた Draft PR として自動起票する機能）を追加した。

順序は `fetch` → `auto-merge` → `auto-push` → **`auto-PR`**。

---

## 1. `git diff scripts/sync/m2-sync.sh`

auto-push の直後、ファイル末尾に追加。

```diff
+# --- auto-PR: push した内容を phase0 へ向けた Draft PR にする ---
+# Draft なので誤マージされない。人間が Draft を外すとマージ可能になる。
+# gh が無い / 認証されていない環境では静かに skip する。
+if [ "$BR" != "$MAIN" ] && command -v gh >/dev/null 2>&1; then
+  AHEAD_MAIN=$(git rev-list --count "origin/$MAIN..HEAD" 2>/dev/null || echo 0)
+  if [ "$AHEAD_MAIN" != "0" ] && git rev-parse --verify -q "origin/$BR" >/dev/null; then
+    # gh 呼び出しの失敗（ネットワーク断・認証切れ等）を "0" と誤判定して
+    # 重複起票しないよう、初期値を -1 にする。
+    EXISTING=$(gh pr list --head "$BR" --state open --json number --jq 'length' 2>/dev/null || echo -1)
+    if [ "$EXISTING" = "0" ]; then
+      if gh pr create --draft --base "$MAIN" --head "$BR" \
+           --title "auto: ${BR} -> ${MAIN}" \
+           --body "m2-sync.sh による自動起票（$(date '+%F %T')）。${AHEAD_MAIN} commits。
+
+内容を確認し、問題なければ Draft を外してください。" >/dev/null 2>&1; then
+        alert "auto-PR: ${BR} -> ${MAIN} (${AHEAD_MAIN} commits, draft)"
+      else
+        alert "auto-PR失敗: ${BR} -> ${MAIN} (${AHEAD_MAIN} commits)"
+      fi
+    fi
+  fi
+fi
```

`1 file changed, 23 insertions(+)`。指示書の実装をそのまま採用（`--draft` 必須、
`EXISTING` の初期値 `-1`、`origin/$BR` 存在チェックを含む）。

---

## 2. `gh` の可用性（keeper の最小環境）

稼働中の keeper（PID 73082、2026-07-04 起動）の実際の環境変数から `PATH` を
抽出して検証した。

```
PATH=/home/ubuntu/.cargo/bin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:
     /home/ubuntu/.pyenv/shims:/home/ubuntu/.pyenv/bin:/usr/local/cuda/bin:
     /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:
     /usr/local/games:/snap/bin

$ env -i HOME="$HOME" PATH="$kpath" bash -c 'command -v gh && gh auth status'
/home/linuxbrew/.linuxbrew/bin/gh
github.com
  ✓ Logged in to github.com account takuya3h (/home/ubuntu/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: ssh
```

`gh` は linuxbrew 経由でインストールされており keeper の PATH から到達可能、
認証も有効。ilya では auto-PR が機能する条件が揃っている。

---

## 3. auto-PR が走ること / 2 回目で重複しないことの実測

### 3.1 事前状態

```
gh pr list --head feat/sync-automation-20260805 --state open --json number
→ []   （既存 PR なし）
```

### 3.2 1 回目実行 — 新規作成

段 3・段 4 のコミット（7 commits ahead of phase0）を push した状態で実行。

```
bash scripts/sync/m2-sync.sh   （6.19 秒）

ログ増分:
  2026-08-05 04:54:17 [ilya] auto-PR: feat/sync-automation-20260805 -> phase0 (7 commits, draft)

gh pr list --head feat/sync-automation-20260805 --state open --json number,isDraft,title
→ [{"isDraft":true,"number":41,"title":"auto: feat/sync-automation-20260805 -> phase0"}]
```

**PR #41 が Draft で作成された。**

### 3.3 2 回目実行 — 冪等性

```
bash scripts/sync/m2-sync.sh

PR 件数: 1（変化なし）✅
ログ増加: 0 行 ✅
```

`EXISTING = 1` となり `gh pr create` を呼ばないため、重複起票しない。

---

## 4. `gh` が無い環境で静かに skip することの実測

```
$ env -i PATH=/usr/bin:/bin bash -c 'command -v gh'
（該当なし。/usr/bin:/bin には gh が無いことを確認）

$ env -i HOME="$HOME" PATH=/usr/bin:/bin bash scripts/sync/m2-sync.sh
exit=0
ログ増加: 0 行
標準出力・標準エラー: エラーメッセージなし
```

`command -v gh >/dev/null 2>&1` が偽になり auto-PR ブロック全体がスキップされる。
エラーも出さず、アラートも残さない（設計どおり「静か」）。

> 補足: この検証中 `sync-alerts.log` に別ホストのアラート行
> （`[084f3b0911a2] fetch失敗`）が 1 件挿入されたが、これは自分の実行とは
> 無関係な同時実行（`~/claude-sync/` は 11 台共有のログファイル）であり、
> 自分の `env -i` 実行によるものではない。

---

## 5. 全体の実行時間（段 3 からの増分）

```
段 3（auto-merge まで）: 3.95〜6.12 秒
段 4（auto-PR 追加後）  : 4.35 秒（gh 呼び出しが発生しないケース）
                          6.19 秒（gh pr create が実際に走ったケース）
```

有意な増加は見られない。`gh pr list` / `gh pr create` のネットワーク往復が
`git fetch` と同程度のオーダーで収まっている。

---

## 6. 判断に迷って独自に決めたこと

**なし。** 指示書の実装をそのまま採用し、検証も指定された手順どおりに実施した。
段 3 までに確立した検証パターン（`env -i` での最小環境再現）を踏襲した。

---

## 7. 既存動作への影響確認

| 項目 | 状態 |
|---|---|
| `keeper.sh` | 一切触っていない ✅ |
| 自動 commit | 実装していない ✅ |
| 既存の役割（fetch / ff-only merge / 参照更新 / auto-merge / auto-push） | 不変 ✅ |
| アラート書式 | 不変（`alert()` ヘルパーをそのまま再利用）✅ |
| `phase0` 上での不実行 | `[ "$BR" != "$MAIN" ]` で先頭ガード ✅ |
| PR は必ず Draft | `gh pr create --draft` を実装・実測で確認 ✅ |

---

## 8. ⚠️ 重要 — PR #41 について

**手順どおり、検証で実際に PR #41（Draft）が作成された。** これは本実装
（段 2〜4 の `m2-sync.sh` への変更一式）そのものを指す PR であり、
指示書の指定どおり **段 7 まで Draft のまま維持する**。

```
#41  [Draft]  auto: feat/sync-automation-20260805 -> phase0
     https://github.com/takuya3h/m2/pull/41
```

手動で `gh pr create` する段 7 の手順は、この PR を Draft から通常 PR に
変える（`gh pr ready`）か、既存を使う形に読み替える必要がある。

---

## 9. 現在の状態

```
ブランチ  : feat/sync-automation-20260805
HEAD      : b65a23c
push 状態 : ahead(origin/$BR) 0（すべて push 済み）
作業ツリー: 追跡変更 0 件 / 未追跡 3 件（_smoke_* の除外規約該当）
PR        : #41（Draft・未マージ）
```

## 10. 次の段（未着手）

- **段 5**: `third_party/` 同期の設計案（3 案の比較、実装なし）
- **段 6**: GitHub の auto-merge 設定（人間が Web UI で実施）
- **段 7**: `.servername` の全台配布、PR の扱い（#41 を Draft 解除するか）
