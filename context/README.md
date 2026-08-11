# context/ — 外部の面へ渡す縮尺図

`runindex/` は正本だが大きすぎて Claude アプリのプロジェクト知識に載らない
（実測では `runindex/` 単体でプロジェクト容量の 107% を占める）。
ここには「外に出す軽量ビュー」だけを置く。

## 2 種類ある。ディレクトリで分ける

| 種別 | 場所 | ファイル | 生成 |
|---|---|---|---|
| 自動生成 | `context/auto/` | `STATE.md`, `experiments_summary.csv`, `verdicts_summary.csv`, `open_questions.md` | `make context`（`runindex/` から） |
| 自動生成 | `context/auto/` | `tasks_summary.csv`, `followups.md` | `make taskindex`（`tasks/*/result.yaml` から） |
| **人手管理** | `context/` 直下 | `conventions.md` | 手で書く。生成は触らない |

自動生成側（`context/auto/`）は手で編集しない。人手管理側は自動生成の対象にしない。

## 使い方

    make runindex   # runindex/ を再生成（正本の更新）
    make context    # runindex/ から context/auto/ を再生成（make runindex の直後に実行する）
    make taskindex  # tasks/*/result.yaml から tasks_summary.csv と followups.md を再生成

`context/auto/` を手で編集したかどうかは次で検出できる。

    make context-check     # make context の出力に差分が無ければ exit 0
    make taskindex-check   # make taskindex の出力に差分が無ければ exit 0

**それぞれの検査は自分の出力だけを見る。** `context/auto/` を 2 つの生成器が共有するため、
全ファイルを走査すると他方の出力を「未知の差分」として数えてしまう。生成器を足すときも
同じ方針にすること。

冪等性がある（同じ commit 状態なら `make context` を何度実行しても差分ゼロ）。
壁時計は使わず、各ファイルの先頭に `generated_from_commit` / `generated_from_date`
（HEAD のコミット・コミット日時）を埋め込むことで「どの状態を見ているか」を示す。

## `STATE.md` に判断を書かない理由

`STATE.md` は runindex の**数値の現在地のみ**を機械的に集計したものであり、
「主軸」「確定した結論」「次にやるべきこと」といった人の判断は一切含まない。
判断・解釈・評価が必要な研究方針は**外部の運用ハブ**（Notion「M2研究運用ハブ」と
「M2研究計画」）の役目である。ID の登録簿は `configs/notion.yaml`（非秘密）にあり、
読み書きの手順は `docs/notion_integration.md` にある。
規約だけは `context/conventions.md` に置く。
自動生成物に判断を混ぜると、生成の都度その判断が壁時計的に上書き・消失するため、
生成物と判断は最初からファイルを分けている。
