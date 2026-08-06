# context/ — 外部の面へ渡す縮尺図

`runindex/` は正本だが大きすぎて Claude アプリのプロジェクト知識に載らない
（実測では `runindex/` 単体でプロジェクト容量の 107% を占める）。
ここには「外に出す軽量ビュー」だけを置く。

## 2 種類ある。ディレクトリで分ける

| 種別 | 場所 | ファイル | 生成 |
|---|---|---|---|
| 自動生成 | `context/auto/` | `STATE.md`, `experiments_summary.csv`, `verdicts_summary.csv`, `open_questions.md` | `make context` |
| **人手管理** | `context/` 直下 | `conventions.md`, `glossary.md`, `plan_mirror.md` | 手で書く。`make context` は触らない |

自動生成側（`context/auto/`）は手で編集しない。人手管理側は自動生成の対象にしない。

## 使い方

    make runindex   # runindex/ を再生成（正本の更新）
    make context    # runindex/ から context/auto/ を再生成（make runindex の直後に実行する）

`context/auto/` を手で編集したかどうかは次で検出できる。

    make context-check   # 再生成して差分ゼロなら exit 0、差分があれば diff を出して exit 1

冪等性がある（同じ commit 状態なら `make context` を何度実行しても差分ゼロ）。
壁時計は使わず、各ファイルの先頭に `generated_from_commit` / `generated_from_date`
（HEAD のコミット・コミット日時）を埋め込むことで「どの状態を見ているか」を示す。

## `STATE.md` に判断を書かない理由

`STATE.md` は runindex の**数値の現在地のみ**を機械的に集計したものであり、
「主軸」「確定した結論」「次にやるべきこと」といった人の判断は一切含まない。
判断・解釈・評価が必要な研究方針は `context/plan_mirror.md`（人手管理）の役目である。
自動生成物に判断を混ぜると、生成の都度その判断が壁時計的に上書き・消失するため、
生成物と判断は最初からファイルを分けている。
