# RESULT: T-2026-10-07-drop-projection-check-in-contracts

**判定: pass。** 契約の流れで作り直しと鮮度の検査（`taskindex-check` `inbox-check`）を求めていたのは
**手順書の文言だけ**で、検証の道具（`task-validate` `task-preflight` `Makefile` の依存）には経路が無かった。
文言だけを直し、目標と道具は変えていない。実行ホスト bengio、分岐 `feat/drop-projection-check-in-contracts`、起点 `origin/phase0` = `67c4cc44`。

## 1. 解決された参照

- `contract.conventions_rev`: 契約の `073f9dc` を実測した。`context/conventions.md` の最終変更は `073f9dc0`（2026-10-02T10:46:49Z）で、以降の変更は無い。
- `inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）: **参照しなかった。** 本契約は文書と道具の呼び出しだけを扱う。
- `contract.inject_verbatim` の原文（`context/conventions.md:98-107`、`150-187` から写した）:

> <a id="prohibitions"></a>
> ## prohibitions
>
> | id | 禁止事項 |
> |---|---|
> | `no_split_redefine` | split を再定義しない |
> | `no_raw_write` | `data/raw` `data/external` に書き込まない |
> | `no_frozen_change` | 凍結源を変更しない |
> | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
> | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

> <a id="issuer_cautions"></a>
> ## issuer_cautions
>
> **起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
> 実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**
>
> | # | 注意 |
> |---|---|
> | 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
> | 2 | 一致 0 件なら別の異質な方法でも確認する |
> | 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
> | 4 | 仕組みの挙動は実装を読んでから信じる |
> | 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
> | 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
> | 7 | **丸めた表示を実数として扱わない** |
> | 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
> | 9 | 無変更は要約値で確かめる。表示属性では足りない |
> | 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
> | 11 | 測定の副作用が禁止領域へ触れないか確かめる |
> | 12 | **判断の前に、いま見ているものが最新かを確かめる** |
> | 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
> | 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |
>
> **注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
> 確かめると 3 件とも実在した。
>
> **注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
> （`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。
>
> **注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
> （自分の命令行にその語が含まれるため）。
>
> **注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。
>
> **シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
> 一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**
>
> **命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

## 2. 完了判定（実測値）

| # | 判定 | 実測 |
|---|---|---|
| A | 直接の呼び出しを行番号つきで列挙 | `audit.md` §2（S1 の検索） |
| B | 間接の経路を記録 | `audit.md` §3。Makefile の依存・道具の subprocess・フック・試験・Codex 経路を読み、**経路は 0 件**。名前以外の語（S4）でも 0 件 |
| C | 直す対象と残すものを分類 | `audit.md` §2。甲（作り直しを求める）2 箇所、乙（契約の中で回す）2 箇所、他は丙（残す） |
| D | 手順書から作り直しを外した | `SKILL.md:153-156` と `:176-180` を「作り直さない。統合の後に自動で作り直される」へ。理由（並行の衝突／自動化／分岐で回すと必ず落ちる）を添えた |
| E | 契約の検証から `*-check` を外した | 道具には呼び出しが無く、外したのは手順書 `SKILL.md:172-173` の「両方を回すこと」。`Makefile:121-138` の目標は残した。検証の数え方（PASS/WARN/SKIP/FAIL）は**変化なし**（5/1/8/0 のまま） |
| F | 運用文書を揃えた | `tasks/README.md:204` に「phase0 の上で使う。契約の分岐では回さない」を 2 行足した。道具の説明（`## 投影` `### 生成物の合流` `context/README.md`）は残した |
| G | 契約の検証が鮮度で落ちない | 受け皿を足して `inbox-check` が差分ありの状態で、`task-validate` exit 0、`task-preflight` exit 0（5 PASS / 1 WARN / 8 SKIP / 0 FAIL） |
| H | 他の検査が働き、`*-check` も単独で働く | §3 の陽性対照 |

## 3. 陽性対照（phase0 `67c4cc44` の作業木を scratchpad に置いて測った。本体の作業ツリーは不変）

| 判定 | 壊す入力 | 実測 |
|---|---|---|
| `taskindex-check` 単独 | phase0 素 / `context/auto/followups.md` に 1 行追記 | exit 0 / **exit 1**「差分あり: followups.md」 |
| `inbox-check` 単独 | phase0 素 / `tasks/inbox.md` に 1 行追記 | exit 0 / **exit 1**「差分あり: inbox.md」 |
| `inbox-check`（本分岐） | 受け皿 1 行を追加 | **exit 1**（make は 2） |
| `task-validate` | 本契約の写しの `meta.kind` を `bogus` に | 写し正常 exit 0 / **exit 1**（`[L1-1] meta.kind`） |
| `task-preflight` | 同じ壊した写し | **exit 1**（P8 FAIL） |
| `forbidden-check` | `runindex/anomalies.md` に 1 行追記 | **exit 1**（`禁止領域 runindex/ の内側`）。生成物への追記は exit 0（仕様どおり除外） |
| 禁止語・秘匿 | §6 | §6 |

関連の試験 5 本（`test_check_docs` `test_check_agent_docs` `test_build_taskindex` `test_build_inbox` `test_check_forbidden`）は
変更前（phase0 作業木）63 passed、変更後 63 passed。`docs-check` と `agent-check` は phase0 でも本分岐でも exit 1 で、
`agent-check` の出力は同一。`docs-check` の差は本体にだけある未追跡ファイルの有無によるもので、両方に共通する既存の 1 件
（`docs/proposal-gate.md:41`）だけが残る。本契約の変更による新しい失敗は無い。

## 4. 直した箇所

- `.claude/skills/task/SKILL.md`（Codex の `.codex/skills/task` はこのディレクトリへのリンクで、同じ文が効く）
  - 前: 「書いたら投影に現れることを確かめる。」+ `make taskindex` / `make taskindex-check`
    後: 「**生成物は作り直さない。phase0 への統合の後に自動で作り直される**（…）。契約の分岐で作り直すと並行する契約と衝突し、作り直さずに鮮度の検査を回すと自分の報告の分だけ必ず差分が出て落ちるためである。」
  - 前: 「…（`make taskindex-check` と `make inbox-check`）。両方を回すこと。」後: 「…**この 2 つは phase0 の上で使う道具であり、契約の分岐では回さない。**」
  - 前: 「併合の後は再生成すること。」+ `make taskindex && make inbox` 後: 「**契約の分岐では作り直さない。** 契約は統合を禁じるため分岐では併合が起きず、phase0 側の併合の後は自動で作り直される。」
  - 前: 「集約結果が衝突した場合は再生成すれば解消する。」後: 「集約結果は統合の後に自動で作り直される。」
- `tasks/README.md:204-205`: 2 行を追記。

## 5. 起票者の誤り

1. **asserted_without_measuring**: 「契約の検証で `*-check` が走る」「契約の検証から呼び出しを外す」と書いたが、検証の道具に `*-check` への経路は無い（`audit.md` §3）。指示どおり道具を探して外そうとすると、外す対象が無いか、無関係な道具を変えて禁止 7 に触れる。
2. **起票者の手順書**: 版管理の外にあり、このホストから読めない（UNKNOWN）。同趣旨の記述（「検証を通す」に `*-check` を含める等）があれば「phase0 の上で使う」に直すべきである。repo 内の雛形 `tasks/_templates/{impl,exp,analysis}/SPEC.md:27` は事実の説明だけで、直す必要は無いが同じ注記を添える候補である。

## 6. 規約の適用判定と送出物の検査

- `proposal_gate` の禁止語: `tools/check_proposal.py --only forbidden` を送出物 6 件（RESULT.md、result.yaml、audit.md、受け皿、SKILL.md、tasks/README.md）に当てた。契約の記録 4 件は 0 件。SKILL.md と tasks/README.md は**既存の文**で一致して exit 1 になるが、検出内容は phase0 版と同一で、追加した 12 行だけを当てると 0 件。陽性対照（禁止語 2 語の合成文）は 2 件を検出し exit 1。
- 秘匿: `tools/report_task.py` の `scan_secrets` を資格情報を読み込んだ環境で同じ 6 件に当てた。6 件とも 0 件。陽性対照は鍵の形をした合成文字列で 2 件、合成した環境値の直接照合で 1 件を検出した。出力は種別だけで、値は出していない。
- `folds` `symmetry`: **適用されない。** 本契約は腕の比較も折りの選定も行わない（kind=impl）。
- `issuer_cautions`: 注意 2（零件のとき別の方法で探す）は S1〜S8 で、注意 3（両方向の対照）は §3 で、注意 5（終了コードを件数と呼ばない）は zsh で `PIPESTATUS` が空になった測り直しで扱った。

## 7. 逸脱・想定外・UNKNOWN

- **逸脱（環境）**: 開始時は `feat/tier1-cost-estimate` 上にいて、`git checkout phase0` が未追跡の `experiments/transfer/pd_refin_empty_seed42_tf32/logs/{eval_meta_val,val_metrics_by_epoch}.json` に阻まれた。2 件は phase0 の追跡版と**内容が同一**（`git diff --no-index` で差 0）と確かめたうえで scratchpad へ移し、切替えで追跡版が同じ内容で置かれた。禁止 12（`experiments/**` の変更）に字面で触れたため記録する。退避の写しは scratchpad に残る。
- **逸脱（判断）**: 切替え後の三行目は 0 だった（`tasks/` 以外の未追跡物は phase0 の `.gitignore` で隠れた）。
- **逸脱（判断）**: プロジェクト規約は「変更後に README.md へ記録」を求めるが、契約が変更範囲を「直す対象・契約のディレクトリ・受け皿」に限るため README.md は変えていない。
- **想定外**: P1 `venv_active` は `VIRTUAL_ENV` が期待値と一致すれば、`sys.prefix` が別で期待の場所が実在しなくても PASS した（作業木での測定時）。道具は変えていない。
- **想定外**: P9 の WARN `separated_source@SPEC.md:39` は行末 `\` の継続行を別の命令と読んだ誤検知で、実際は一つの命令として動いた。
- **逸脱（判断）**: 送出の予行の命令に誤って `make task-report` を含め、commit の前に台帳へ一度送った。送信前の秘匿検査は通り、読み戻しの要約値は手元と一致した。`report_task.py` は既存の報告を置き換えるため、PR 番号を入れた後に送り直した。
- **UNKNOWN**: 起票者の手順書の中身。

## 8. 送出

PR・終了コードは result.yaml の `pr` と `commits`、および台帳への返送の終了コードを参照。
