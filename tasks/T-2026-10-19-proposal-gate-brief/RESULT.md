# T-2026-10-19-proposal-gate-brief

## 1. 解決された参照

inputs.data.split_files と inputs.denominator は参照しなかった。frozen_source は指定なし。sigma_policy は既定の series: pstd / sigma_source: paired_delta / delta_sigma_source: paired を継承するが、本契約で未使用。以下は起点から解決した原文。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

<a id="issuer_cautions"></a>
## issuer_cautions

**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 4 | 仕組みの挙動は実装を読んでから信じる |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
| 7 | **丸めた表示を実数として扱わない** |
| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
| 11 | 測定の副作用が禁止領域へ触れないか確かめる |
| 12 | **判断の前に、いま見ているものが最新かを確かめる** |
| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
| 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。


## 判定

verdict: pass。G1・G2 pass。前提PR #237統合後、起点を8de3ac54へ更新した。対象文言はSPECと一致し、読みと試験は前後同一。

## 完了判定

|項目|実測|
|---|---|
|a|役割分離は前後4行。生成の会話欄だけ変更。他欄・三行・表下の文は同一|
|b|依頼文の六項目をSPECと一項目ずつ文字列比較し、すべて一致。置き場と参照の直後に配置|
|c|変更履歴の末尾にe1364772を記入。git showでそのcommitに規約変更が含まれることを確認|
|d|B.3と雛形三行目はSPECどおり。対象三文書の旧文言は二方式とも残存0|
|e|禁止語15・カード16・数値必須5/6/10は前後同一。既存カード0件、雛形の数字欠落3件は不変。費用UNKNOWNの写しは欠落1件|
|f|二試験ファイルは前後とも47件合格。同じ試験名集合で収集0ではない|
|g|三文書・本契約内・受け皿と許可された.gitignoreだけ変更。既存カードと検査器の要約値は前後同一|
|h|通常PR #239、base=phase0、head=feat/proposal-gate-brief、Draft=false。契約指定forbidden-checkは違反0、規約はallow_writeで許可|

詳細: [audit.md:111](audit.md#L111) Task A 基準と G1、[audit.md:402](audit.md#L402) Phase C 文言・読みの照合、[audit.md:619](audit.md#L619) G2 最終判定、[audit.md:623](audit.md#L623) Phase D 変更履歴のcommit記入。基準はbaseline.json、試験名集合と結果はtests-before.xml / tests-after.xml、全検索結果はsearch-before.json / search-after.json。三文書の指定変更を逆に戻すと基準全文へ一致することも確認した。

## L2-6警告と規約版

警告「conventions.md が5a8baa79以降に更新」を記録。差分は前提契約のnaming / folds / symmetry / crossfitと新設precision。注入対象prohibitions / issuer_cautionsは前後同一。利用者の指示で続行し、contract.conventions_revを起点で測った規約commit 7ba1d60db8c0ea8581bc03d79bafeaec56be1d1dへamendments付きで更新した。再検証は警告なし。
precisionは末尾に位置し、proposal_gateの直後ではない。C-1で読取値の全要素が変わらないことを実測した。

## 範囲外の旧ルール

|ファイル・行|扱い|
|---|---|
|tasks/T-2026-09-16-proposal-gate/SPEC.md:213|旧生成の行。利用者の許可により履歴を保持|
|tasks/T-2026-09-16-proposal-gate/SPEC.md:262|旧B.3の引用。同上|
|tasks/T-2026-10-19-conventions-and-defect-records/baseline.json:168|旧規約の基準記録。同上|

二方式は変更前10行で完全一致（対象2、履歴3、無関係5）。変更後は対象0、範囲外8行が前後同一。範囲外のファイルは無変更。

## 起票者の誤り・逸脱・UNKNOWN

起票者の誤りは観測していない。初回G1停止と再開はaudit.mdに連続記録。SPEC.mdは無変更。
同期で現れた未追跡の実験ログ二件を許可に基づき.git/info/excludeへ個別追加したが、.gitignoreの再包含が優先し禁止検査が違反2件となった。優先順位の事前確認が不足したため、利用者の追加許可を得て.gitignore末尾へ同じ二経路だけを追加し、違反0を確認した。実験ファイルは移動・削除していない。追加した二行を除けば元に戻せる。
基準記録の集合型のJSON変換漏れは記録処理で修正した。検査器・試験は未変更。生成物は再生成していない。
プリフライト6 PASS / 0 WARN / 8 SKIP / 0 FAIL。SKIP=P2/P3/P4/P5/P11/P12/P13/P14（未実行）。planning-with-files・プランモード切替手段・agentmemoryは利用不可で、契約のフェーズ順と契約内記録で進めた。

## 送出

PR [#239](https://github.com/takuya3h/m2/pull/239)。台帳送出の終了コードと応答はaudit.md末尾へ追記する。同期抑止解除の状態表示は最終応答に残す。
