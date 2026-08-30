# RESULT — T-2026-08-30-tooling-fixes-five

kind: impl / host: andrew / branch: `feat/tooling-fixes-five` / GPU 不使用

## 判定

**status: pass。** G1・G2 とも通過。SPEC §5 の完了判定 a から h のうち **g を除く 7 件を充足**した。
g（全テストが通る）は**既存の失敗 6 件が残るため未充足**。6 件は修正前と同一で、
本契約の五件とは無関係である（§6 に実測の根拠）。

## 1. 解決された参照

- `contract.inject_verbatim` = `conventions#prohibitions` `conventions#issuer_cautions`
  → `context/conventions.md` の当該アンカーの原文をそのまま参照した。
- `conventions_rev: a8c07e81` → 実測と一致。置換不要。
- `created_from.counts`（index 1250 / experiments 277 / verdicts 1486）と
  `runindex_commit: 09fdefb3` → 実測と全一致。置換不要。
- 本契約に `denominator.ref` `frozen_source.ref` `sigma_policy` は無い。

## 2. 完了判定（SPEC §5）

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | F1 | 宣言ありで `runindex/` への書き込みが通る（許可 1 件） | 陽性: 宣言なしで同じ書き込みが違反 1 件。陰性: 宣言ありでも `data/` は違反、既存 run 配下も違反。audit §7 |
| b | F2 | 未知名 `zzz_not_a_check` を含む契約で P10 が FAIL | 陰性: 既存契約が使う 4 名だけなら PASS。`gpu_free` を使う既存契約は P11 込みで 7 PASS / 0 FAIL。audit §7 |
| c | F3 | 宣言つきの置換前提が設置でき、解決前は P12 が FAIL | 陽性: 宣言なしの `TBD` と `unresolved:` は従来どおり落ちる。陰性: 解決済みは PASS、参照が無ければ SKIP。audit §7 |
| d | F4 | `make harvest-verify` 一命令で前後比較。実 runindex で 4 表とも PASS | 陽性: 判定列を 1 箇所変えると FAIL、削除も FAIL、run 単位の既存行変更も FAIL。陰性: 同一入力の対と集計値のみの変更は PASS。audit §7 |
| e | F5 | 伏せ字表記 4 種が非検出 | 陽性: 合成の鍵 2 種・名前つきの値・伏せ字と本物が同居する行の 4 種を検出。出力に値の断片なし。audit §7 |
| f | 回帰 | 修正前後の L1 が `diff` で**完全一致** | 分母は非空（104 契約 / OK 103 / FAIL 1 / SKIP 1）で、件数が契約数 104 と一致。audit §3・§8 |
| g | 試験 | **未充足。** 509 passed（471 → 509、増分 38 = 本契約で足した試験の数と一致）だが 6 failed が残る | 増分は一致。失敗 6 件は修正を stash して修正前でも同じ 6 件が落ちることを実測。audit §8 |
| h | 変更範囲 | `git status --porcelain experiments/ data/ runindex/` が空 | 同じ絞り込みを `tools/` と `tasks/` に当てると 10 行出る。audit §9 |

## 3. 五件それぞれの採った方式と理由

- **F1** `contract.allow_write`（接頭辞の配列）を spec に足し、`check_forbidden.py --task` が読む。
  Makefile 変数ではなく契約に置いたのは、許可が契約の性質であって実行ホストの都合ではないため。
  **上限は経路そのものに当てる**（宣言の文字列で判定すると短い宣言が網をくぐる。実測で確認）。
- **F2** schema の `enum` と実行直前検査 `P10` の両方を置き、同じ集合であることを試験で縛った。
  既存契約が使う `gpu_free` は無視でも除外でもなく **`P11` として実装**した。
  §2 が「既存契約が使っている名前は引き続き PASS」を求めるため、実装以外に整合させる道が無い。
- **F3** 形式検査を緩めず、**宣言（`resolve_by_executor: true`）を要る方式**にした。
  緩めると宣言の無い `TBD` も通ってしまい、置換忘れを検出できなくなる。
  解決は `tasks/<id>/resolved.yaml` に置き、`P12` が済むまで止める。この対応表が
  RESULT の「解決された参照」の材料になる。
- **F4** `tools/verify_harvest.py` を新設し `make harvest-verify` から呼ぶ。判定列は
  名前の手がかり（`same_sign` `verdict` `agree` `reason` `n_seeds`）で見分ける。
  **一覧を手で持たない**のは、表が列を増やしたときに規則が古くなるのを避けるため。
- **F5** 一致した**断片**に伏せ字の目印があれば拾わない。行全体を見ないのは、同じ行に
  本物の鍵があっても伏せ字が一つあるだけで見逃すため。目印は狭く取る
  （`xxxx` や `**` まで広げると合成鍵を伏せ字と誤認し、既存の試験を 1 件壊した）。

## 4. 実測（次の契約で使う値）

**許可の宣言の書き方**（`spec.yaml`）:

```yaml
contract:
  allow_write: [runindex/]      # 接頭辞の配列。無ければ欄ごと書かない
```

検査は `make forbidden-check TASK=<task_id>`。上限は `data/` 配下（常に不可）と、
`experiments/` `transfer/` のうち**起点に既に存在する経路**（既存 run 配下）。

**置換前提の参照の書き方**（`spec.yaml` と `tasks/<id>/resolved.yaml`）:

```yaml
inputs:
  denominator:
    ref: "unresolved:runindex/experiments.csv から s0 の分母を引く"
    resolve_by_executor: true
```
```yaml
inputs.denominator.ref:
  resolved_to: "exp:baselines/s0/relationdetr@mAP"
  how: "runindex/experiments.csv の experiment_id と照合した"
```

**収穫検証の命令名**: `make harvest-verify`（`BASE=<commit>` で起点を変えられる。既定は `HEAD`）。

**preflight に書いてよい名前**: `venv_active` `cuda_ext_loaded` `deterministic_flags` `gpu_free`
（`tools/preflight_task.py` の `KNOWN_PREFLIGHT_NAMES` と schema の `enum`。両者の一致は試験で縛った）。

## 5. 起票者の誤り

**なし。** 五件はすべて再現し、原因はいずれも道具の側にあった。規約の側に原因のあるものは無く、
schema の変更で既存契約が壊れたものも無い（L1 が修正前と完全一致）。

ただし SPEC §5-g の期待「全テストが通る」は、**起票時点で既に 6 件が落ちていた**ため
本契約の作業だけでは満たせない。これは契約の誤りではなく、分母の記載が無かったことによる。
次の契約では「実行前の失敗件数を分母として記録する」形にすると空振りを避けられる。

## 6. 逸脱・想定外・UNKNOWN・判断待ち

**逸脱 5 件。**

1. `judgement` — 開始時の未追跡ファイル（前契約と同じ 5 件）で `make task-start` が止まった。
   前契約でユーザーが選んだ「stash で一時退避」を同じ手順で適用した（`stash@{0}`）。
   **完了後に `git stash pop` で戻す必要がある。**
2. `judgement` — **対照の途中で実在ファイルを削除した。** F1 の検査に使った `touch`/`unlink` が
   `experiments/audit/l0_hts_acceptance/acceptance_report.json` を消した。`git checkout --` で復元し、
   要約値 `d9ac7ced89e5c574…` の一致と `git status` の差分零を確認済み。以降の対照は
   **控えを取って書き換え、必ず戻す**方式に変えた。
3. `judgement` — **自分の修正で既存の試験を 1 件壊し、直した。** F5 の伏せ字の目印を広く取りすぎ、
   合成鍵 `NOTION_API_KEY=` + `x`*40 を伏せ字と誤認した。目印を絞り込んで解消。
4. `judgement` — **自分の修正に穴があり、塞いだ。** F1 の上限を宣言の文字列で判定していたため
   `allow_write: ["d"]` が `data/` 配下を通した。経路ごとの判定に直し、5 通りを試験で固定。
5. `spec_defect` — 手順書（`.claude/skills/task/SKILL.md` 手順 6）は `make taskindex` /
   `make inbox` の実行を求めるが、**契約 §4-3 がこれらの再生成を禁止**している。契約を優先し
   実行しなかった。本報告は `context/auto/` の投影にまだ現れない。統合後に一台で再生成すること。

**想定外**: なし（SPEC §6 の 4 事象はいずれも起きなかった）。

**UNKNOWN**: `P3 deterministic_flags` は従来どおり判定基準が未確定で常に SKIP のまま
（backlog B-20）。本契約では触れていない。

**判断待ち**: 既存の失敗 6 件（`test_engines` 1 件・`test_fetch_task` 1 件・`test_research_logger` 4 件）を
別契約で直すか。`test_fetch_task.py::test_rejects_unknown_file_name` は
`tools/fetch_task.py` の誤り文言と試験の期待がずれているだけに見える
（期待「受け取れないファイル」／実際「経路として受け取れない名前です」）。

## 7. 送出

- PR: 本文末尾に番号を追記
- `make task-report` の終了コード: 本文末尾に追記
