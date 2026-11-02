# bengio を andrew に揃える: Relation-DETR の本体と拡張のビルド、Stage 2 の材料の写し、前の契約の残り物の片付け

**task_id:** T-2026-11-02-bengio-align-andrew  **kind:** impl

**実行ホスト:** `bengio`（repo は `~/slocal2/m2`。`context/env-facts.md`「repo の位置」）。
**基準:** `andrew`（repo は同じく `~/slocal2/m2`）。andrew は**読むだけ**。bengio から ssh で読み、写すときも andrew 側では読むだけにする。
**GPU:** Task C の検出塔の評価一本にだけ、bengio の GPU を 1 枚使ってよい（利用者の決定 2026-11-02）。学習はしない。ほかの Task では GPU を使用しない。

## 1. 背景と目的

利用者は、andrew と bengio のホスト差（同じ処方で学習したときの指標の差と、学習の速さの差）を測りたい。測る前に bengio を andrew に揃える（利用者の決定 2026-11-02）。

前の契約 `T-2026-11-02-bengio-andrew-env-survey`（PR #282、phase0 に統合済み）が、読むだけで違いを一覧にした。本契約はその一覧どおりに揃え、前の契約の残り物を片付ける。
調査の表は `experiments/analysis/bengio_andrew_env_survey/REPORT.md`、機械で読める値は同じ置き場の `b/`・`c/`・`d/`・`e/`・`f/`、報告は `tasks/T-2026-11-02-bengio-andrew-env-survey/RESULT.md`。

本契約の結果は、次の測定の契約を bengio で起票できるかの判断に使う。**関門の判定には使わない。**

## 2. 利用者の決定（本契約が従うもの）

| 日付 | 決定 | 本契約での扱い |
|---|---|---|
| 2026-11-02 | 基準は andrew。bengio を andrew に揃える | andrew は変えない。andrew の状態の正否は問わない |
| 2026-11-02 | 揃える対象は Relation-DETR の本体、仮想環境のパッケージ、データと checkpoint | 仮想環境とデータと塔の checkpoint は調査で一致済み（§3）。本契約で変えるのは Relation-DETR の本体と拡張のビルドだけ |
| 2026-11-02 | andrew にだけある Stage 2 の材料を bengio へ写す | Task D |
| 2026-11-02 | 前の契約の残り物を片付ける | Task E。対象は §5 Task E の表に挙げたものだけ |
| 2026-11-02 | `~/slocal2` 直下の 5 月の置き場 11 件は対象外 | 触らない（§4 の 2） |
| 2026-11-02 | `~/slocal2/stage2pilot_store` の bengio にだけある契約の出力は残す | 触らない（§4 の 2）。Task D は足すだけ |
| 2026-11-02 | 電力の上限は揃えない | 変えない |
| 2026-11-02 | 確かめに GPU を使ってよい（評価一本） | Task C |

## 3. 調査で分かったこと（Task A で今の状態と照合する。食い違えば実測を正とする）

出所はすべて `experiments/analysis/bengio_andrew_env_survey/REPORT.md`（以下「調査」）。

| 項目 | 調査の結果 |
|---|---|
| Relation-DETR の本体 | andrew main: source 142 / 2f08e5213cb5c377…、all 155 / 20f15c061b435ce4…。bengio main: 127 / 3ade18f0709362fa…、140 / 89dc93b4a82f1e06…。差は andrew だけ 15 件、中身が違う 8 件、bengio だけ 0 件（表 B-1） |
| 重ねの BODY `~/slocal2/s2fix-bengio-body/third_party/Relation-DETR` | andrew main と全 155 件一致 |
| 揃えると失われる bengio の中身 | `main.py` と `transforms/presets.py`（上流の原形。`third_party_snapshot/Bengio/` の tar に無い）。違う 8 件の bengio の版は `b/diffs_bengio_vs_andrew.patch` に差分として残っている |
| 除外した最上位（表 B-2・B-3） | `checkpoints` 12 件は両ホストで一致。`per_class_coco_map` は andrew 22 件、bengio main 0 件。`__pycache__` は件数が違う |
| MS-Deform-Attn の拡張（調査 Task C） | 置き場 `~/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/`。bengio の `build.ninja` の 27 行目は重ねの BODY の `.cu` を指す。`.so`・`.o` の要約値は andrew と違う |
| 仮想環境 | 二つともパッケージの差 0。python の実体は両ホスト同じ uv の 3.11.16。`pyvenv.cfg` は違う（andrew の `.venv` の `home` は存在しない pyenv を指す） |
| データ・塔の checkpoint・重み | 差 0 |
| Stage 2 の材料（`d/data_compare.json` の `files` の group `stage2`） | andrew だけ 17 件。うち 9 件 13,497,919,828 B は bengio に無い。残る 8 件は bengio の `stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/` に同じ中身の写しがある |
| 試験 | bengio は 11 failed・1 error。収集の失敗 `tests/test_stage1_dtower_convergence.py` は `util/convergence.py` が無いため |
| 同期 | repo の `.stignore`（phase0 の `.stglobalignore` と同じ）は `experiments/**/` の下の `*.py`・`*.npy`・`*.pt`・`*.pth`・`logs`・`checkpoints` などを同期する。前の契約は出力先に `.py` を置き、andrew へ渡った |

検出塔の評価の記録値（Task C で比べる）:

- overall AP 0.7273450248398429（`experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/eval_val.json` の `AP`）
- 標的群 AP 0.7950748009（`tasks/T-2026-11-01-stage2-w23-bengio/audit.md` B-2。同じ checkpoint を bengio の重ねの BODY で評価した値。記録の値との差 2.5e-8）
- ホストをまたいだ評価の差の実測は 2.5e-8（bengio、同上）と −2.31e−07（dlsta、`context/env-facts.md` の装置の節）。許容差 1e-6 はこの二つの実測から置いた

## 4. 禁止事項と申し送り

注入される規約（`conventions#prohibitions`、`conventions#issuer_cautions`、`conventions#env_p0`）に従う。加えて次を守る。

1. **andrew に何も書かない。** repo、家の下、`/tmp` のいずれにも書かない。写すときは andrew 側を読むだけの形にする。python は byte code を書かない形で起こす
2. **次を変えない。** bengio の `data/`、二つの仮想環境、塔の checkpoint と重み、`~/slocal2` 直下の 5 月の置き場 11 件（調査の表 E-4 で更新時刻が 2026-05 のもの）、`~/slocal2/stage2pilot_store` の既存のもの、家の直下の設定ファイル、Syncthing と ssh の設定。Task E の表に無いものは消さない
3. **本契約の出力を同期させない。** 出力先 `experiments/analysis/bengio_align_andrew/` に、`.stignore` の同期の型（`*.py`・`*.npy`・`*.pt`・`*.pth`・`*.pth.tar` など、`logs`・`checkpoints`・`predictions` などの名前のディレクトリ）を置かない。道具の台本は `tasks/T-2026-11-02-bengio-align-andrew/` の下に置く。置く前に `.stignore` を読み、置いた後に andrew に届いていないことを確かめる
4. **記号リンクの先を消さない。** 重ねの BODY と worktree は `~/slocal2/m2` の `.venv`・`data`・`experiments` などへの記号リンクを持つ。片付けでリンクをたどらない
5. GPU は Task C の評価一本だけ。電力の上限、クロックなど装置の設定を変えない
6. **生成物の再生成（`make taskindex`、`make inbox` など）と `*-check` を本契約の分岐で回さない。** `make forbidden-check TASK=...` は回してよい
7. 禁止は実行者の操作に対するものである。Syncthing などの同期処理が他のホストから配る変更は含まない。届いたものは届いたものとして記録する
8. 削除が実行基盤に拒まれたら、回避せず利用者に示して許諾を得る（退避は `mv`。env-facts「実行基盤の制約」）

**申し送り:**

- 揃える手段（重ねの BODY から写すか、andrew から写すか）、拡張の作り直しの方法、評価の入口（`scripts/eval_relation_detr_map.py` か `scripts/stage2pilot/pd_eval.py` か）は、実装を読んで実行者が決めてよい。選んだ理由を書く
- 評価の checkpoint は絶対経路で渡す（相対経路は読み込みを飛ばして AP 0 を返す。env-facts の装置の節）
- 一致 0 件・不在の報告は異質な二通りで確かめる。丸めた表示を実数として書かない
- プロセスの計数は `scripts/grasppilot/proc_enum.py`（`/proc/PID/exe`）を使う

## 5. Task

### Task A — 開始状態（G1）

1. 手順書の「0. 始める」に従う。分岐 `feat/bengio-align-andrew`、起点 `origin/phase0` を記録する
2. 本契約以外の compute の件数（陽性対照と陰性対照つき）、GPU の空き、記憶領域の空き（バイト）を記録する
3. 調査と同じ規則（`reldetr_digest.py`）で、bengio main・andrew main・重ねの BODY の要約値を取り、§3 と比べる
4. andrew の Stage 2 の材料 17 件の要約値を取り、調査の記録と比べる
5. **前後で比べる対象の要約値をここで取る**: bengio の `checkpoints` 12 件、二つの仮想環境のパッケージの列、データ（調査の Task D と同じ集合。画像は調査と同じ取り方の要約値）、`~/slocal2` 直下の各項目の大きさ、`stage2pilot_store` の既存の各ファイルの要約値か大きさ、試験の失敗の名前の集合
6. G1: 3 と 4 が調査の記録と一致したら通過。食い違ったら、どこが変わったかを書いて利用者に聞く

### Task B — Relation-DETR の本体を揃える（G2）

1. **揃える前に**、bengio main の中身が違う 8 件の今の版が、版管理下の `b/diffs_bengio_vs_andrew.patch` と andrew の版から戻せることを確かめる（戻した結果の要約値が今の bengio の版と一致すること）。戻せないファイルがあれば止めて利用者に聞く
2. bengio main の `third_party/Relation-DETR` を、調査の要約値の範囲（`reldetr_digest.py` の除外規則の内側）で andrew main と同じにする。除外した最上位（`checkpoints`・`per_class_coco_map`・`experiments`・入れ子の `third_party`・`__pycache__` など）は変えない。ただし Task E の表の `__pycache__` 4 件は片付ける
3. 揃えた後の source と all の要約値が andrew main と一致することを確かめる（G2）。`checkpoints` 12 件の要約値が前後で一致することを確かめる
4. 揃えた後の三分類（andrew だけ、bengio だけ、違う）がすべて 0 件であることを、調査と同じ道具で確かめる

### Task C — 拡張の作り直しと評価一本（G3）

1. MS-Deform-Attn の拡張を、bengio main の `third_party/Relation-DETR` の `.cu` から作り直す。作り直した後の `build.ninja` の差を andrew の `build.ninja`（調査の `c/andrew_build.ninja`）と比べ、差の行を全部書く。`.so` の要約値を andrew と比べて書く（一致しなくてよい。一致したかを書く）
2. 検出塔 D\*-COCO（折り A、seed 42）の checkpoint を、bengio main の Relation-DETR と検出の仮想環境で val について一本評価する。checkpoint は前の契約の記録と同じもの（w23-bengio の audit B-2 の 30d199b1…）。GPU は 1 枚
3. overall AP と標的群 AP を §3 の記録値と比べる。**差がどちらも 1e-6 以内なら G3 通過。** 超えたら止めて利用者に聞く（ホスト差の測定の前提が崩れるため）
4. 評価の記録に、拡張が読み込まれたこと（CPU へ落ちていないこと）と、checkpoint が読み込まれたことを残す
5. 評価の出力（予測など大きなもの）は repo の外の本契約の置き場に置き、出力先には要約値と値だけを置く

### Task D — Stage 2 の材料を写す

1. andrew だけにある 17 件（調査の `d/data_compare.json` で group が `stage2`、判定が「andrew だけ」のもの）を、andrew と同じ経路で bengio に置く。このうち 8 件は bengio の `copied/` に同じ中身の写しがあるので、そこから置いてもよい
2. 置いた後、17 件すべての要約値が andrew と一致することを確かめる
3. 既存の `stage2pilot_store` のファイル（`copied/` を含む）は動かさない、消さない

### Task E — 前の契約の残り物を片付ける

**対象は次の表に挙げたものだけ。** 各項目に「片付けた」か「残した（理由）」を書く。根拠は調査の `e/leftovers_other.json` と `e/leftovers_repo_00.json`。

| # | 対象 | 片付ける条件 | 残す条件 |
|---|---|---|---|
| E1 | worktree `~/slocal2/m2-four`（`feat/stage2-pilot-four-new-types`） | commit されていない変更が 0 件で、分岐の commit がすべて遠隔か phase0 にある | どちらかに当たらない。使っているプロセスがある |
| E2 | worktree `~/slocal2/m2-s2fix-bengio`（`feat/stage2-pilot-fix-epoch4-shuffle-bengio`） | 同上 | 同上 |
| E3 | worktree `wt_phase0`（`/tmp/claude-1000/` の下の別のセッションの scratchpad、detached） | 同上。かつ、その置き場を cwd に持つプロセスが 0 件 | 同上 |
| E4 | E1・E2 の手元の分岐と、上流の無い手元の分岐 `chore/evidence-map-a-place-start` | 分岐の commit がすべて遠隔か phase0 にある | 当たらない |
| E5 | 重ねの BODY `~/slocal2/s2fix-bengio-body` | Task B・C が通過した後。拡張のビルドがこの置き場を指していない | ほかの置き場からの参照（記号リンク、設定）がある |
| E6 | `.git/info/exclude` の bengio だけの 5 行（調査の Task E の表） | 行を外しても `git status` に新しく現れるファイルが 0 件 | 現れるファイルがある（件数と経路を書いて利用者に聞く） |
| E7 | `~/m2-git-info-exclude.bak-20261019` | E6 を片付けた後 | E6 を残した |
| E8 | `third_party/Relation-DETR` の下の `__pycache__` の 4 件（調査の表 E-2） | Task B の後 | — |
| E9 | `.venv-relation-detr/pyvenv.cfg.before_s2fix`、`/tmp/pyvenv.cfg.bak` | `pyvenv.cfg` そのものは変えない。控えだけを片付ける | — |
| E10 | `/tmp` 直下の自分のもので、作った契約が記録（audit・inbox・RESULT）から特定できるもの | 特定の根拠を書ける。使っているプロセスが無い | 特定できない。道具の実行時の置き場（`mcp-*`・`pymp-*`・`ssh-*`・`code-*`・`cc-daemon-*` など）は残す |

worktree は git の手順で外し、登録も消す。消す前に、各項目の経路・大きさ・要約値か件数を記録する。

### Task F — 検証と報告

1. 試験を手順書と同じ形で回し、失敗と収集の失敗の名前の集合を取る。開始時との差を名前ごとに説明する（`tests/test_stage1_dtower_convergence.py` の収集の失敗は消える見込み）
2. Task A-5 の要約値を取り直し、前後で比べる。変わったものは本契約が変えたもの（Task B〜E）か同期で届いたものかを分けて書く
3. andrew に送った命令をすべて audit に残し、書き込みの向き先を持つ命令が 0 件であることを書く。本契約の出力先が andrew に現れていないことを、読むだけで確かめる
4. `make forbidden-check TASK=T-2026-11-02-bengio-align-andrew` を回す
5. 報告（§7）を書き、commit、push、PR を作る。**PR の base は phase0。** Draft を外す
6. `make task-report` で台帳へ返す。抑止の目印は手順書の「8. 終える」が外す

## 6. 完了判定

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐・起点・compute・GPU の空き・記憶領域の空き、Task A-5 の前の値が記録されている | プロセスの計数で、実在する実行ファイルが 1 以上、存在しない経路が 0 |
| b | Relation-DETR | bengio main の source と all の要約値が andrew main と一致、三分類がすべて 0 件。揃える前の 8 件が差分から戻せた | 揃える前の bengio main で同じ比べをすると「違う」が 8 件出る（調査と同じ）。戻した版の 1 バイトを変えると要約値が一致しない |
| c | 拡張と評価 | `build.ninja` が bengio main の `.cu` を指す。overall AP と標的群 AP が記録との差 1e-6 以内。拡張と checkpoint が読み込まれた記録がある | checkpoint の経路を存在しない経路にすると、読み込みの記録が出ないか評価が失敗する（実行の要否は実行者が決める。行わない場合は既知の挙動として env-facts を引く） |
| d | Stage 2 の材料 | 17 件が andrew と同じ経路にあり、要約値が一致 | 存在しない経路を一つ混ぜると「無い」と出る |
| e | 片付け | E1〜E10 の各項目に、片付けたか残したかと理由がある | 片付けた項目は、片付けた後に異質な二通りで「無い」と確かめる。残した項目は在ることを確かめる |
| f | 対象外の無変更 | Task A-5 の値が前後で一致（本契約が変えたものと同期で届いたものを除く） | 同じ取り方で、本契約が変えた bengio main の Relation-DETR は前後で違うと出る |
| g | 試験 | 名前の集合と、開始時との差の説明がある | 差の計算に名前を一つ足した集合を入れると差に出る |
| h | andrew と同期 | andrew への書き込みの命令 0 件。本契約の出力先が andrew に無い | andrew にある既知の経路を同じ確かめ方で調べると「在る」と出る |
| i | PR | PR が存在し、base が phase0、分岐が `feat/bengio-align-andrew`、Draft でない | — |

## 7. 報告の構成

### 7.1 `RESULT.md`（目安 150 行以内）

| 節 | 内容 | 入れないもの |
|---|---|---|
| 判定 | verdict と G1〜G3 の結果 | 手続きの全文 |
| 完了判定 | §6 の表。各項目に実測値 | 命令の全文 |
| 実測 | 次の測定の契約で使う値: 揃えた後の要約値、評価の値と差、拡張の `.so` の一致の有無、片付けた項目と残した項目の表、残った違い（電力・CPU・PCIe・IOMMU など調査の Task F の差は再掲しない。変わったものだけ） | 経過の説明 |
| 起票者の誤り | 型と内容。一件 3 行以内 | 引用の全文 |
| 逸脱 | 何をなぜ | 手順の再掲 |
| 想定外・UNKNOWN | 測れなかったものと理由 | 不要なログ |
| 送出 | PR 番号、`make task-report` の終了コードだけ | 出力の全文 |

### 7.2 `audit.md`

命令とその出力、andrew に送った命令の全件、要約値の全件、片付けの前の記録、検証の出力、変更範囲の一覧、台帳の応答。`RESULT.md` からは行番号で指す。

### 7.3 `experiments/analysis/bengio_align_andrew/`

`REPORT.md` と、要約値の表（JSON か TSV）。§4 の 3 の同期の型を置かない。

## 8. 想定外のときの扱い

- Task A で調査の記録と食い違った: どこが変わったかを書いて利用者に聞く（andrew の基準が動いた可能性がある）
- 揃える前の bengio の版が差分から戻せない: 揃えずに止めて利用者に聞く
- 評価の差が 1e-6 を超えた: 止めて利用者に聞く。重ねの BODY はまだ消さない
- 片付けの条件に当たらない項目: 残し、理由を書く。escalate_if に当たるものは利用者に聞く
- 拡張の作り直しに失敗した: 重ねの BODY を消さずに止め、利用者に聞く

## 9. 参照しなかった項目

- 分母: 本契約は比べる実験を持たないので `inputs.denominator` を置かない。報告に「参照しなかった」と書く
- 規約の版 `contract.conventions_rev` と `meta.created_from.runindex_commit` は起票時の値。実行者が実測して差し替える
