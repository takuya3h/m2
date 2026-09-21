# notes — T-2026-09-19-p13-skip-and-enum

変更の要点。詳細は `RESULT.md`、証跡は `audit.md`。

## 1. P13 を完了済み契約で SKIP にした

`tools/preflight_task.py`

- 追加: `completed_verdicts(task_id)` — `tasks/<task_id>/result.yaml` の
  `gates[].verdict` のうち空でない値を返す。読めない・様式に合わない場合は空を返す
  （**推測で補わない**。印が無ければ未完了として従来どおり検査する）。
- `check_symmetry_table` の冒頭で印を見る。印があれば
  `SKIP 完了済み（result.yaml に verdict あり: N 件）のため対象外`。
- **判定に使うのは `result.yaml` の実在と verdict の有無だけ**である。名前の部分一致・
  日付・配布台帳は使わない。
- 未完了の契約に対する挙動は 1 行も変えていない。P1〜P12 も触れていない。

🔴 **`verdict` は最上位の項目ではない。** 契約は「`result.yaml` を持ち `verdict` が
入っている」と書くが、`result.schema.json` が持つのは `gates[].verdict` であり、
最上位は `status` である。最上位を見る実装にすると完了済みが 0 件になる（実測）。

## 2. 起票者の欠陥の型を機械可読にした

- `tasks/_schema/result.schema.json` の `issuer_defects[].type` の列挙に
  `asymmetric_comparison` と `rule_read_narrowly` を足した（4 → 6 種）。既存の語は不変。
- `docs/issuer-defects.md` の「`result.yaml` の enum には未追加」の注記と、それを受ける
  「（同上）」を消した。
- `tools/build_taskindex.py` の `DEFECT_TYPES` も 6 種に揃えた。**契約の Task B には
  無いが、この一覧は「result.schema.json の列挙と同じ」と自ら宣言している。**
  片方だけ増やすと、新しい型の欠陥が投影の集計表から黙って落ちる。

## 3. 試験

`tests/test_symmetry_gate.py` に 14 件追加（42 件が通る）。

- 完了済みで SKIP、理由に「完了済み」が出ること
- **陽性対照 6 種**: `gates: []` / verdict が空文字 / verdict の項目が無い /
  `gates` 自体が無い / 壊れた YAML / 最上位が辞書でない → すべて FAIL のまま
- 名前が完了済み契約を含む未完了の契約 → FAIL（部分一致で誤認しない）
- 様式と投影の列挙が一致すること（片方だけ増やすと落ちる）
