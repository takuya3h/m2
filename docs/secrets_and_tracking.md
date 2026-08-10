# 秘密情報の暗号化 git 管理 + 全マシン自動追跡（W&B / Notion）

公開リポでも安全に、**どのマシンでも `git clone` → 復号 → 実験すれば自動で W&B 監視・Notion 記録**される仕組み。

## 方針
- **平文 `.env` は絶対に commit しない**（公開リポ → 即漏洩）。`.gitignore` で `.env` / `.env.*` / `*passphrase*` / `*.key` を除外。
- 認証は **gpg 対称暗号で `.env.gpg`**（暗号文）を commit。各マシンは**パスフレーズ（別経路で配布・git に入れない）**で復号。
- ローテーション時は `.env` を更新 → 再暗号化 → commit、で全マシンに伝播。API 鍵そのものは git に残らない。

## 初回セットアップ（1 回）
```bash
# 1) パスフレーズを各マシンに置く（全マシン同一・別経路で配布。git に入れない）
mkdir -p ~/.config/egosurgery
(umask 077; printf '%s' 'STRONG_PASSPHRASE' > ~/.config/egosurgery/env-passphrase)

# 2) .env を用意（.env.example を元に実値を記入）。NOTION_DB_ID は database id (ef4ccd02…)。
cp .env.example .env && $EDITOR .env

# 3) 暗号化して commit（暗号文 .env.gpg のみ・平文 .env は commit されない）
bash scripts/encrypt_env.sh
git add .env.gpg .env.example .gitignore && git commit -m "chore(secrets): add encrypted env" && git push
```

## 各マシンでの利用（毎セッション／実験前）
```bash
source scripts/load_env.sh    # .env.gpg を復号 → 現在のシェルに env をロード
# → WANDB_API_KEY / NOTION_API_KEY 等が有効化。以降の学習が自動で W&B 追跡 + Notion 記録。
```
- `load_env.sh` は **source** すること（env を現在シェルに入れるため）。
- パスフレーズが無ければ明確なエラーで停止（誤って平文を扱わない）。

### 編集と再暗号化の順序（この順を守る）

`.env` を書き換えたら、**読み込み直す前に再暗号化する**。順序を逆にすると伝播しない。

```bash
$EDITOR .env                  # 1) 平文を編集する
bash scripts/encrypt_env.sh   # 2) 先に再暗号化する（飛ばすと編集は他マシンへ伝わらない）
git add .env.gpg && git commit -m "chore(secrets): rotate" && git push
source scripts/load_env.sh    # 3) 読み込み直す
```

`load_env.sh` は平文が暗号文と食い違うとき、**上書きせず警告する**（2026-08-10 変更）。
以前は読み込みのたびに平文を上書きしていたため、`.env` への編集が黙って消えていた。
警告が出たら、どちらを正とするかを選ぶ:

- **暗号文を正とする**（他マシンで鍵が更新された）: `rm .env` してから `source scripts/load_env.sh`
- **手元の編集を正とする**: `bash scripts/encrypt_env.sh` で再暗号化して commit

**警告を放置すると、そのマシンだけ古い資格情報で走り続ける。** 上書きしない代償なので、
出たら必ずどちらかを選ぶこと。

## 自動追跡の配線状況
| 系統 | スクリプト | W&B | Notion |
|---|---|---|---|
| 工程分母 S4 / S4′ | `train_s4_tecno.py` | ✅ `tracking.init/log/finish` | ✅ |
| B2a det→phase | `train_b2a.py` | ✅ | ✅ |
| T1a region→phase | `train_t1a.py` | ✅ | ✅ |
| B1 / T1b（検出側・`.venv-relation-detr`） | `train_b1_mtl.py` / `train_t1b.py` | ⚠ 未（後述） | ✅（postprocess 経由） |
| 検出器ベンチ S0 | 旧 `MMDetTrainer` | ✅（既存） | ✅（既存） |

- `tracking.py`（`egosurgery.utils.tracking`）は **WANDB_API_KEY 未設定 / wandb 未導入なら no-op**（学習を止めない）。
- **検出側 trainer（B1/T1b）の W&B 未配線**: これらは `.venv-relation-detr` で動き egosurgery を import しない＋同 venv に wandb 未導入。
  対応するには `.venv-relation-detr` に `wandb` を入れ、`train_b1_mtl.py`/`train_t1b.py` に直接 `wandb.init/log` を足す（TODO）。
- Notion の詳細は [`docs/notion_integration.md`](notion_integration.md)。バックフィルは `scripts/post_experiments_to_notion.py`。

## セキュリティ要点（厳守）
- `.gitignore` の挙動は**必ず検証**する（行末 `#` コメントはパターンを壊す）。検証: `git check-ignore .env`（IGNORED であること）。
- commit してよいのは `.env.gpg`（暗号文）/ `.env.example`（テンプレ）のみ。`.env`・パスフレーズ・鍵は禁止。
- 万一 `.env` が過去に commit/push されたら、**鍵を即ローテーション**し、履歴を `git filter-repo` 等で除去 + force push。
- リポが PUBLIC であることを常に意識する（`gh repo view --json visibility`）。
