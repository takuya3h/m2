# context/ — 外部の面へ渡す縮尺図

`runindex/` は正本だが大きすぎて Claude アプリのプロジェクト知識に載らない。
ここには「外に出す軽量ビュー」だけを置く。

## 2 種類ある

| 種別 | ファイル | 生成 |
|---|---|---|
| 自動生成 | `STATE.md`, `experiments_summary.csv`, `verdicts_summary.csv`, `open_questions.md` | `make context`（未実装） |
| **人手管理** | `conventions.md`, `glossary.md`, `plan_mirror.md` | 手で書く。`make context` は触らない |

自動生成側は手で編集しない。人手管理側は自動生成の対象にしない。
