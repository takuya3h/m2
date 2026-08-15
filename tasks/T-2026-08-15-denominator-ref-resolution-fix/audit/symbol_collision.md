# Phase A Step 4 — 記号の衝突の判断

## 何が衝突しうるか

逐語の引用 `contract.inject_verbatim` は `conventions#prohibitions` の形を取り、
**最初の `#` で二分する**（`tools/validate_task.py:381` の `ref.split("#", 1)[1]`）。

分母の参照 `inputs.denominator.ref` にも `#` が現れうる。索引の識別子のうち
`#` を含むものが実在するためである。

## 実測

| 測るもの | 実測 |
|---|---|
| `#` を含む識別子 | 4 / 207 |
| `~` を含む識別子 | 146 / 207 |
| `~` と `#` の両方を含む識別子 | 0 |
| どちらも含まない識別子 | 57 / 207 |
| `#` を分解に使っている箇所 | 1 箇所（`validate_task.py:381`） |
| 参照を種別によらず解釈する共通関数 | 無し |

`#` を含む 4 件は次のとおり。

    baselines/s0/maskdino_bbox@val#None
    baselines/s0/maskdino_bbox@val#a63aecae
    baselines/s0/varifocanet_bbox@val#None
    baselines/s0/varifocanet_bbox@val#a63aecae

`#a63aecae` は当該行の `eval_recipe_id` = `a63aecae1158` の**先頭 8 桁への切り詰め**であり、
`#None` は `eval_recipe_id` が空の行に **Python の空値が文字列化して混入**したものである。

## 判断

**種別ごとに解釈を分ける必要は無い。Phase B で分けない。**

根拠は、衝突が成立する条件が満たされないためである。`#` を分解に使う箇所は
`contract.inject_verbatim` の要素だけを見ており、`inputs.denominator.ref` は
その経路へ入らない。参照を種別によらず解く共通の関数は存在せず、**種別ごとに
既に別の経路で解釈されている。** したがって `#` を含む分母の参照を受け付けても、
逐語の引用の錨として誤解釈されることはない。

**ただし危険は残る。** 将来、参照の解釈を一つの関数へ束ねた場合、
`#` の意味が種別によって違う（区切り／錨の境）ことが表面化する。
束ねる時点で種別ごとの解釈が必要になる。**受け皿へ起票する。**

## 逸脱

無し。契約の `escalate_if`「参照の記号が他の種別の参照と衝突し、種別ごとに解釈を
分けなければ直せないと判明した場合」には**該当しない**（分けなくても直せる）。
