# RESULT — T-2026-08-22-philip-hub-foundation

**実行者:** philip / feat/philip-hub-foundation / 8fcbe69
**実行日時:** 2026-08-22T06:20:00+09:00 (JST)
**判定:** PARTIAL

Phase A / B は全項目を実測で充足した（G1・G2 とも通過）。
Phase C は契約が指す make ターゲットの一部が repo に存在せず実行できず、さらに **push が実行エージェント側の権限で遮断された**ため PARTIAL とする。
詳細は §5 deviations。実出力は同ディレクトリの `audit.md` に要約せず貼ってある。

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `contract.conventions_rev` | `d422b08` | **実測 `1201f4f` へ置換**（SPEC の手順どおり。逸脱ではない） |
| `contract.inject_verbatim` | `conventions#prohibitions` | 下記に原文を逐語で転記 |
| `inputs.denominator.ref` | 記載なし | 該当なし（kind: impl。分母を使う主張をしない） |
| `inputs.sigma_policy` | 記載なし | 該当なし（同上） |
| `inputs.frozen_source.ref` | 記載なし | 該当なし（同上） |
| `meta.created_from.runindex_commit` | `f96edc1` | **repo 内に存在しない**（§5-6） |

### `context/conventions.md#prohibitions`（逐語・要約禁止）

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

**遵守状況**: split 未変更 / `data/**` 未書き込み / 凍結源未変更 / 未測定は UNKNOWN 表記 / `runindex/**` 未編集。
spec の `prohibitions` は 5 件だが conventions 側の表は同 5 件で、spec が挙げる
`no_runindex_hand_edit` を含め全て対応がある。

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| G1 (after A) | **PASS** | 基準の未追跡 `base_untracked_start=7` / `base_untracked_now=7`、`diff` は空。`which python=/home/ubuntu/slocal2/m2/.venv/bin/python`。`SERVERNAME`: zsh=philip / bash -lc=philip |
| G2 (after B) | **PASS** | 配布物 sha256 が上流公表値と一致、版 v1.27.10。展開物=配置物 `match_exit=0`。`device_ids/philip.txt` `lines=1` `format_ok=1`。`syncthing_procs=0` `port_22000=-` `port_8384=-` |

## 3. 成果物

| 種別 | パス | 件数・実測 |
|---|---|---|
| 監査ログ | `tasks/T-2026-08-22-philip-hub-foundation/audit.md` | 全コマンドの実出力（要約なし） |
| 本報告 | `tasks/T-2026-08-22-philip-hub-foundation/RESULT.md` | 本ファイル |
| 機械可読の要約 | `tasks/T-2026-08-22-philip-hub-foundation/result.yaml` | 1 ファイル |
| **識別子（版管理）** | `scripts/sync/device_ids/philip.txt` | 1 行 / 64 バイト |
| 実行ファイル（版管理外） | `~/bin/syncthing` | mode 755 / v1.27.10 |
| 設定と鍵（版管理外・非公開） | `~/.local/state/syncthing/{config.xml,cert.pem,key.pem}` | 3 件（中身は記録しない） |
| シェル設定（版管理外） | `~/.zshenv`, `~/.profile` | 各 4 行追記 |

## 4. 受入基準の充足

| # | acceptance | 結果 | 実測 |
|---|---|---|---|
| 1 | 開始時の家の直下と鍵と受け入れ一覧と未追跡の件数を記録している | **充足** | `home_entries=25` / `~/.ssh/` 4 エントリ / `authorized_keys_entries=1` (`SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU dakyo-mba@dmba.local`, RSA 4096) / `wt0_untracked=8`（うち基準 7） |
| 2 | 分岐を切ったあとも未追跡が失われていないことを件数で示している | **充足（条件つき）** | `wt0=7` / `wt1=7` / `diff` 空。ただし分岐は本作業の開始前に既に切られていた（§5-1） |
| 3 | 実行環境を作り、経路が仮想環境を指していることを示している | **充足** | `Python 3.11.16` / `which python=/home/ubuntu/slocal2/m2/.venv/bin/python` |
| 4 | 論理名の追記内容を記録し、新しいシェルの両方の形態で解決されることを示している | **充足** | 追記 4 行を `.zshenv`/`.profile` に。`diff -u` を audit に。zsh -c/-lc, bash -lc, sh -lc = philip。陰性対照 bash -c / zsh -fc / bash --noprofile = unset |
| 5 | 同期処理の配布物の版と要約値を記録し、配置物と展開物が一致することを示している | **充足** | v1.27.10 / tar `c04ffbde...5fd60`（上流公表値と一致）/ bin `32ab747e...ca1dd` が展開物と `match_exit=0` |
| 6 | 識別子を発行し、既存があれば上書きしていない | **充足** | 発行前 `ls ~/.local/state/syncthing → No such file or directory` `exists=no`。上書きは発生していない |
| 7 | 識別子を版管理へ一行で公開している | **充足** | `scripts/sync/device_ids/philip.txt` `lines=1` `bytes=64` `trailing_ws=0` `format_ok=1` |
| 8 | 同期処理が起動していないことを待ち受けの不在で示している | **充足** | `port_22000=-` `port_22001=-` `port_8384=-` / `syncthing_procs=0`（`pgrep -x`、陽性対照 `zsh_procs=5`・陰性対照 `nosuchproc_procs=0`） |
| 9 | 送信前の秘匿検査を自分で行い、陽性対照つきで示している | **充足** | 本検査 `hits=10`、いずれも変数名・説明文・検査正規表現そのもの。鍵の書き出し行としての一致は 0 件。陽性対照 `pos_hits=4`、陰性対照 `neg_hits=0`。囮は `/tmp/phf_decoy.md`（repo 外） |
| 10 | 開始時の未追跡がすべて残っており、変更が契約の範囲に限られ、分岐が送出されている | **部分充足** | 未追跡 `base_untracked_start=7` / `base_untracked_end=7` / `diff_exit=0`。追跡下の変更は `scripts/sync/device_ids/philip.txt` と契約ディレクトリのみ。commit `bf6cd4a` 済。**push は未実施**（§5-10） |

## 5. deviations（指示書どおりにしなかった箇所）

**1. 分岐と契約の配置は本作業の開始前に完了していた**
- 指示: SPEC §0 の `git checkout -b feat/philip-hub-foundation origin/phase0` を実行し、切る前後で未追跡件数を比較する。
- 実際: 開始時点で既に `feat/philip-hub-foundation`（`origin/phase0` 追跡、`8fcbe69`）にあり、契約ディレクトリも配置済みだった。`git reflog` に `checkout: moving from exp/philip-wip-20260703 to feat/philip-hub-foundation` が残る。
- 理由: 切る**前**の状態は既に観測できないため、Step 1 と Step 2 の件数比較は同一時点の測定になり、独立な前後比較になっていない。reflog と基準 7 件の実在で事後確認した。
- 分類: 環境差

**2. `.venv` を作り直さず、インタプリタを貼り直した**
- 指示: Task 1 Step 3「README の手順に従う」（`uv venv .venv --python 3.11` から始まる）。
- 実際: `uv venv` は既存 venv を理由に停止。`--clear` を使わず、`.venv/bin/python` の symlink と `pyvenv.cfg` の `home`/`version_info` を uv 管理の CPython 3.11.16 へ貼り直した。
- 理由: 壊れていたのは `/home/ubuntu/.pyenv/versions/3.11.4/` を指す symlink だけで、`site-packages` は 289 エントリ・6.3GB が健在だった（torch 2.1.2+cu118 / mmengine / mamba_ssm 2.2.2 / causal_conv1d 1.4.0 等）。`--clear` は導入済みスタックを破棄する。3.11.4→3.11.16 は同一マイナー版で cp311 ABI 互換。実際に `torch.cuda.is_available()=True` を確認した。
- 分類: 判断が必要だった

**3. `jsonschema` を追加導入した**
- 指示: 依存の追加は契約に無い。
- 実際: `make task-validate` が `jsonschema が必要です` で Error 1 となったため `uv pip install "jsonschema>=4"` を実行（attrs / jsonschema 4.26.0 / jsonschema-specifications / referencing / rpds-py の 5 件）。
- 理由: 契約自身が要求する検証を通すために必要。利用者の承認を得た「最小構成＋契約ツール依存」の範囲。
- 分類: 環境差

**4. `scripts/sync/setup_host_servername.sh` を使わず手で追記した**
- 指示: Task 2 Step 2 で当該スクリプトを `cat` して読み、使う場合は差分を記録する。
- 実際: 当該ファイルは**存在しない**（`exists=no` / `readable=no`。「読めない」ではなく「無い」）。`scripts/sync/` の実体は `keeper.sh` `m2-sync.sh` `new_experiment_branch.sh` `setup_host_autosync.sh` の 4 件。契約が許す手動追記に切り替え、`diff -u` を記録した。`setup_host_autosync.sh` は SERVERNAME 規約の根拠として読むに留め、常駐を起こすため実行していない（禁止 6）。
- 分類: SPEC の欠陥

**5. 契約記載の `device-id` サブコマンドが存在せず、`serve --device-id` を用いた**
- 指示: `~/bin/syncthing --home ... device-id`。
- 実際: `syncthing: error: unexpected argument device-id`（exit=1）。`--help` のコマンド一覧（serve / generate / decrypt / cli / install-completions）に device 系は無く、`serve --help` の `--device-id  Show the device ID` を発見して使用。generate のログ・`serve --device-id`・`config.xml` の `<device>` id 属性の三者一致を確認した。
- 分類: SPEC の欠陥

**6. WARN 2 件を承知のうえで続行した**
- 指示: 検証を通す。
- 実際: `validate_exit=0` だが `WARN [L2-8] index.csv: 起票時 751 → 現在 749` / `experiments.csv: 207 → 206`。`meta.created_from.runindex_commit: f96edc1` は **repo の全 304 commit のどこにも存在しない**（`git cat-file -t f96edc1 → Not a valid object name`）。`verdicts` は 1038 で一致。
- 理由: 起票側が phase0 と別系列を見ていると考えられる。本契約は kind: impl で分母を数値主張に用いないため影響しない。利用者の判断を仰いだうえで続行した。
- 分類: SPEC の欠陥

**7. `make taskindex` `make inbox` `make forbidden-check` `make task-preflight` を実行できなかった**
- 指示: Task 4 Step 3/4。
- 実際: Makefile に**いずれのターゲットも存在しない**（`task-validate` `context` `context-check` 等は存在）。`tasks/inbox.d/` `tasks/inbox.md` も存在しない。よって `inbox` 系の生成物は作られず、結果は **UNKNOWN**。
- 分類: SPEC の欠陥

**8. `context/auto/` を再生成しなかった**
- 指示: Task 4 Step 4 で生成物を再生成し、Step 6 で `context/auto/` を staging する。
- 実際: 再生成コマンド（`make taskindex`/`make inbox`）が無い。代替となる `make context-check` を読み取り検査として実行したところ `Error 1`（差分あり: STATE.md, experiments_summary.csv, open_questions.md, verdicts_summary.csv）。ただし差分は `diff_lines=12` のうち `stamp_lines=12` で、`generated_from_commit`/`generated_from_date`/`AUTO-GENERATED` 行のみ。**データ行の差分はゼロ**。
- 理由: 陳腐化は `2b353f6 → 8fcbe69` の merge に由来し本契約以前から存在する。契約が指示していない `make context` を走らせると、契約と無関係な churn を commit に混ぜることになるため実行しなかった。
- 分類: 判断が必要だった

**9. Notion 台帳へ記録していない**
- 指示: `outputs.report_to: []`、SPEC「台帳へは返さない。合言葉が無いため送れない」。
- 実際: 記録していない。`NOTION_API_KEY=unset` `NOTION_DB_ID=unset` `WANDB_API_KEY=unset`。`source scripts/load_env.sh` は `/home/ubuntu/slocal2/.env.gpg が無い` で失敗。
- 理由: 契約の指定どおり。認証が無いため `notion_ops` は no-op になる。
- 分類: 環境差（既知・契約が織り込み済み）

**10. push できていない（分岐が送出されていない）**
- 指示: Task 4 Step 6 で `git push -u origin HEAD`、可能なら PR を作成する。
- 実際: `git push` は **Claude Code の auto mode 分類器に遮断された**（`Permission for this action was denied by the Claude Code auto mode classifier. Reason: Blocked by classifier.`）。commit `bf6cd4a` はローカルに存在するが `origin` へ送出されていない。`gh` は不在（`gh_exit=1`）のため PR も作成できない。
- 理由: 実行エージェント側の権限制御。GitHub の認証可否や remote の受け入れ可否は**測っていないため UNKNOWN**。remote は `git@github.com:takuya3h/m2.git`。
- 分類: 環境差
- 対応: 契約の指示（「push できない → 記録を repo に残し、状況を報告する」）に従い本記録を残した。**起票者は版管理から読む前提のため、送出されるまで本契約の成果は他ホストから見えない。**

**11. git の身元がホストから失われていた**
- 指示: 記載なし。
- 実際: 1 回目の commit が `Author identity unknown` / `fatal: unable to auto-detect email address (got 'ubuntu@aolab.(none)')` で `commit_exit=128`。`~/.gitconfig` が存在しない。過去 200 commit の author 最頻値 `takuya3h <daky.o7600@gmail.com>`（167 件）に合わせ、**このリポジトリだけ**に `git config user.name/user.email` を設定した（`~/.gitconfig` は作っていない）。
- 理由: 身元が無いと commit できない。他リポジトリへ影響させないため repo-local に留めた。
- 分類: 環境差（**他台でも同じはず。申し送り事項**）

**12. 囮の原文を一度 `audit.md` に貼ってしまい、伏せ字化した**
- 指示: Task 4 Step 2「**囮は版管理へ入れない。**」
- 実際: 秘匿検査の陽性対照の出力を「要約せず貼る」（申し送り #8）に従って `audit.md` へ貼った結果、囮の 4 行（鍵の書き出し行を含む）が版管理対象のファイルに入り、commit `bf6cd4a` に含まれてしまった。再検査で `hits=3 → 14` に増えたことで気づき、囮部分を `<囮1: 鍵名の語 + 区切り + 偽の値>` の形へ伏せ字化して `hits=10` に戻した。原文は `/tmp/phf_decoy.md` にのみ残る。
- 理由: 「出力を要約せず貼る」と「囮は版管理へ入れない」が衝突する。後者を優先した。**囮の出力だけは件数と形の説明に留めるべきである。**
- 分類: 判断が必要だった（SPEC の指示どうしの衝突）
- 補足: commit `bf6cd4a` は未 push のため `--amend` で修正した。囮は偽の値のみで実在の秘匿は含まない。

## 6. 未解決・申し送り（次の契約で使う情報）

| 項目 | 内容 |
|---|---|
| **同期処理の版** | `syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64)` |
| **配布物の要約値** | tar: `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60`（上流公表値と一致） |
| **実行ファイルの要約値** | `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd`（`~/bin/syncthing`, mode 755） |
| **philip の識別子** | `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE` |
| **識別子の場所** | `scripts/sync/device_ids/philip.txt`（1 行）。他台も同じ規則で置くこと |
| **識別子の取り方** | `syncthing serve --home ~/.local/state/syncthing --device-id`（`device-id` サブコマンドは無い） |
| **設定の場所** | `~/.local/state/syncthing/`（`--home` で明示。既定パスではない） |
| **論理名の設定方法** | `~/.zshenv` と `~/.profile` の両方に `export SERVERNAME=philip`。`.zshenv` は zsh 全形態、`.profile` は bash ログイン時。`~/.bash_profile` `~/.bash_login` が無いことが `.profile` 読込の条件 |
| **実行環境の作り方** | README の `uv venv` は既存 venv があると停止する。**壊れているのが symlink だけなら貼り直しで足りる**（`--clear` は 6.3GB を破棄する）。uv 管理の CPython は `~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11` |
| **つまずいた点 1** | `.venv/bin/python` が `~/.pyenv/versions/3.11.4/` を指す dangling symlink。pyenv ごと消滅。**他台でも同じはず** |
| **つまずいた点 2** | `mmcv` / `mmdet` が `ImportError: libGL.so.1` で import 不可。**OS 側のライブラリ欠落**であり venv の問題ではない。本契約は gpu:false のため修復していない。GPU 実験を再開する前に `sudo apt install libgl1` 相当が要る。**他台でも同じはず** |
| **つまずいた点 3** | `make task-validate` は `jsonschema` を要求する。venv 再構築後は追加導入が要る |
| **つまずいた点 4** | `pgrep -af syncthing` は**自分のコマンド行を拾う偽陽性**を出す。`pgrep -x` を使うこと |
| **つまずいた点 5** | `scripts/sync/setup_host_servername.sh` は存在しない。SPEC の記述が実体と合っていない |
| **未解決** | `meta.created_from.runindex_commit: f96edc1` が repo に存在しない。起票側の参照系列の確認が要る |
| **未解決** | Makefile に `taskindex` / `inbox` / `forbidden-check` / `task-preflight` が無い。SPEC が前提とする契約システムが未実装 |
| **つまずいた点 6** | `~/.gitconfig` が失われており commit 前に `git config user.name/user.email` の設定が要る。**他台でも同じはず** |
| **要対応** | 本 commit `bf6cd4a` は **push されていない**。送出しないと他ホストが philip の識別子を読めない |
| **次の契約へ** | 他台の識別子が `scripts/sync/device_ids/*.txt` に揃ったら、登録・中継・常駐の起動を行う（本契約では禁止 4/5/6/7） |

## 7. 数値の出所

すべての数値は本ホスト上の実測である。未測定・実行不能の項目は UNKNOWN と記載した。
推定値・代表値・他ホストからの転記は含まない。実出力は `audit.md` に要約せず貼ってある。

| 実行できなかった検査 | 結果 |
|---|---|
| `make forbidden-check` | **UNKNOWN**（ターゲットが存在しない） |
| `make taskindex` / `make taskindex-check` | **UNKNOWN**（同上） |
| `make inbox` / `make inbox-check` | **UNKNOWN**（同上） |
| `make task-preflight` | **UNKNOWN**（同上） |
| `git push` の成否 | **UNKNOWN**（分類器に遮断され実行に至っていない。認証可否は未測定） |
| PR の番号 | **UNKNOWN**（`gh` 不在かつ push 未実施） |
