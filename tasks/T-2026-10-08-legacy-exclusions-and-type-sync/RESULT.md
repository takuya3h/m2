# RESULT — T-2026-10-08-legacy-exclusions-and-type-sync

実行ホスト efros / 分岐 feat/legacy-exclusions-and-type-sync / base phase0。コマンドと出力は `audit.md` に置き、節の見出しで指す。

## 判定

**verdict: pass。** G1 通過、G2 通過（P13・P14・spec-check の完了済みの判定は同じ関数）。
未解決の事項は「逸脱・想定外・UNKNOWN」を参照。

最初に: 未統合の PR の確認は実測した（開いている PR は #223 のみで、本契約の経路への変更は 0 件）。UNKNOWN ではない。

## 完了判定

| # | 実測値 |
|---|---|
| a | #194 の統合 commit cb3fcaa1 は origin/phase0 の祖先。存在しない名では exit 128。開始前の数値は audit A に実数で記録 |
| b | 取り込まない項目 3 件を読み取りのみで確認。**1 件は一部未達**（下記）。確認の前後で `git status` の要約値は同じ |
| c | 一覧の 1 件だけが除外。一文字違い・改行・半角スペース・大文字小文字・接頭辞・接尾辞の 6 入力はすべて除外されず FAIL。一覧に無い不適合の報告も FAIL（audit B） |
| d | 旧様式ファイルの md5 87d316d2… は前後で一致。同内容を別名で置くと除外されない |
| e | 様式エラーは {philip-hub-foundation: 16} → {}。旧様式以外の差は空集合 |
| f | 最終行は前後とも `144 task(s), N failed` の書式（L2: 1 failed → 0 failed）。除外の行は最終行ではない |
| g | 完了済みの除外は `preflight_task.completed_verdicts` を呼ぶ。常に空にする変異で spec-check 0→15、P13 SKIP→FAIL、P14 SKIP→FAIL が同時に起き、戻して一致 |
| h | 報告なし／gates なし／verdict 空／verdict キーなし／YAML 破損 × exp・impl の 10 入力はすべて検出。verdict が pass・ask・stop・skip の 8 入力は検出されない |
| i | 契約指定なし `allow_write_incomplete` 15 → 0（hits 232 → 217、rules_checked 9 → 9）。減った 15 件はすべて verdict あり、残りに verdict ありは 0、追加は 0 |
| j | 手順書・README・雛形が 6 語になり、build_taskindex と docs/issuer-defects.md と合わせて 5 つの写しが schema の列挙と同じ集合。個数の語句は型の区間で 0 |
| k | 変異 6 種すべてで落ち、戻して 51 passed。失敗名は audit D の表 |
| l | 試験の失敗 6 → 6、名前の集合差は空。通過 760 → 802 |
| m | 変更は宣言の内側のみ。`forbidden-check`（BASE=分岐点、省略の両方）は violations 0。既存行の削除は型の一覧の 3 行のみ |
| n | 禁止語 0 件。囮は 1 件検出。秘匿の検査は形と一致の有無だけを出力（audit E） |
| o | PR #224、base=phase0、draft=false、分岐 feat/legacy-exclusions-and-type-sync（API の値） |

## 変更前と変更後

| 項目 | 変更前 | 変更後 |
|---|---|---|
| 全契約の検証 | 144 task(s), 1 failed（philip-hub-foundation） | 144 task(s), 0 failed（L2、exit 0） |
| spec-check `allow_write_incomplete` | 15（exp 10、impl 5） | 0 |
| spec-check hits / rules | 232 / 9 | 217 / 9 |
| 報告の様式エラー | 16（1 契約） | 0 |
| 試験 | 6 failed / 760 passed | 6 failed / 802 passed |
| 型の集合（手順書・README・雛形） | 4 語 | 6 語（schema と一致） |

## 除外された契約の内訳

完了済みとして宣言漏れ検査から外れた 15 契約: status は pass 10、partial 4、stopped 1。
**pass 以外 5 件**: phase-baseline-power（partial）、denoise-falsification（stopped、gate に stop）、det2phase-segmentation-lovo（partial、gate に ask）、oracle-ceiling-and-tool-drop（partial）、stage0-contract-b（partial）。
定義（`gates[].verdict` に空でない値）は変えていない。stop と ask も完了に含まれる。

## 取り込まない項目の確認

| 項目 | 場所 | 結果 |
|---|---|---|
| digest の出力先 | `.gitignore:235-239`、`.claude/hooks/session_end.sh:15,18` | 達成 |
| 開始処理が止まるときの表示 | `scripts/task_start.sh:106-111` | **一部未達**。汚れた経路は表示するが、退避の方法と戻し方は表示しない |
| 投影の再生成の規則 | `.claude/skills/task/SKILL.md:208-210,233-234`、`tasks/README.md:229-232`、`regen-projections.yml` | 達成 |

## 起票者の誤り

- `check_does_not_check`: 申し送りは「全契約の `make task-validate` は変更前から 1 件失敗する（inbox.d に spec.yaml が無いため）」と述べる。実測では inbox.d は SKIP で失敗に数えられず、失敗は philip-hub-foundation の様式エラー 16 件だった。本契約でその失敗は消えた。
- `asserted_without_measuring`: 受け入れ基準は既存の試験の失敗数が増えないことを求めるが、教師データの試験が完了済みの実契約を入力にしており、除外で 1 件増えることを起票時に測っていない（SPEC §3 の想定外の行には載っていた）。

## 逸脱・想定外・UNKNOWN

- **教師データの試験の扱い（想定外の行に該当）。** `test_teacher_detection_rate` が検出 12 / 期待 15 で落ちた。期待値は変えず、その試験だけが使うフィクスチャで完了済みの判定を切った。**ツール側に除外を切る引数は足していない。** 規則の署名と数を動かさない方を採った。
- 取り込まない項目の「開始処理の表示」は一部未達のまま。契約どおり直していない。
- ルートの `README.md` と `docs/experiment_log.md` は更新していない。契約の `allow_write` に含まれず、実験を行っていないため。必要なら別途。
- 本契約自身の spec-check は 3 件（host_mismatch、integration_prohibited_without_pause、gate_requires_report_before_end）。プリフライト P9 も同じ 3 件を WARN。`allow_write_incomplete` は 0。起票者の規則と記述の食い違いで、実行を止めなかった。
- プリフライトの SKIP 8 件（P2〜P5、P11〜P14）は kind=impl または plan に記載が無いため。FAIL は 0。
- 作業中に変異試験の復元に失敗した（zsh が `$files` を単語分割せずバックアップが取れなかった）。変異した 4 ファイルを逆置換で戻し、`git diff` で意図した編集だけが残ることを確認した。以後の変異は Python でメモリ上のバックアップから復元し、前後の sha256 が一致した。**最終の成果物には影響しない。**
- 写しが allow_write の外にもある可能性: 版管理の一覧と全文検索の範囲では見つからなかった（0 件）。
- 他ホストでの動作は測っていない（UNKNOWN）。変更は統合後に各ホストへ届く。

## 送出

PR #224、base `phase0`、Draft ではない（API の値: base=phase0 draft=false）、分岐 `feat/legacy-exclusions-and-type-sync`。commit 4f4a2924。台帳への送出（`make task-report`）の結果は最後の応答で伝える。
