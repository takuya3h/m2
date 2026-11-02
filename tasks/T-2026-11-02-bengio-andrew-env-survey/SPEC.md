# bengio を andrew に揃える前の調査: Relation-DETR、仮想環境、データと checkpoint、前の契約の残り物、装置と系の違い

**task_id:** T-2026-11-02-bengio-andrew-env-survey  **kind:** analysis

**実行ホスト:** `bengio`（repo は `~/slocal2/m2`。`context/env-facts.md`「repo の位置」）。
**比べる相手:** `andrew`（repo は同じく `~/slocal2/m2`）。andrew は**読むだけ**で、bengio から ssh で命令を送り、結果を標準出力で受け取る。
**本契約では GPU を使用しない。** 学習も推論もしない。読む、数える、要約値を取る、突き合わせるだけである。

## 1. 背景と目的

利用者は、andrew と bengio のホスト差を二つ知りたい（2026-11-02）。

- (a) 同じ処方で学習したとき、指標の値がどれだけ違うか
- (b) 学習の速さがどれだけ違うか

測る前に、**bengio の環境を andrew に揃える**（利用者の決定 2026-11-02）。揃える作業は次の二つの契約に分ける（同日の決定）。

1. **本契約（調査）**: bengio と andrew の違いを、読むだけで一覧にする。何も揃えず、何も消さない
2. 後続の実装契約: 本契約の一覧をもとに、bengio を andrew に揃え、前の契約の残り物を片付ける

本契約の結果は、後続の実装契約の範囲と方法、および (a)(b) を測る契約の前提に使う。**関門の判定には使わない。**

## 2. 利用者の決定（本契約が従うもの）

| 日付 | 決定 | 本契約での扱い |
|---|---|---|
| 2026-11-02 | 基準は andrew。bengio を andrew に揃える | すべての表で andrew を基準の列に置く。andrew の状態の正否は問わない |
| 2026-11-02 | 揃える対象は Relation-DETR の本体、仮想環境のパッケージ、データと checkpoint | Task B・C・D。OS 側のライブラリは揃える対象ではないが、Task F で記録する |
| 2026-11-02 | 前の契約の残り物は後続の実装契約で片付ける | Task E で一覧にするだけ。**本契約では消さない、動かさない** |
| 2026-11-02 | 電力の上限は揃えず、(b) で差として測る | Task F で現在値・既定値・最大値を記録する。変更しない |
| 2026-11-02 | 調査と実装を二つの契約に分ける | 本契約は analysis。揃える操作をしない |

## 3. 確定した事実と直近の実測（Task で測り直す。食い違えば実測を正とする）

### 3.1 ホストによらない事実

- `third_party/` は git にも Syncthing にも乗らない（`scripts/restore_relation_detr_source.sh` の冒頭、`docs/third_party_sync_design_2026-08-05.md`）。ホストごとに中身が違いうる
- 同じ上流 commit でもホストごとに中身が違う。スナップショットは `third_party_snapshot/` にあり、Bengio の版は 2026-08-02 時点で `.git` が無く、mtime で選んだ 22 件を `project_files.tar.gz` に入れた（`third_party_snapshot/Bengio/README.md`）。Andrew の版は「保全対象のソースコードは存在しない」（`third_party_snapshot/Andrew/README.md`、2026-08-02）
- Relation-DETR の作業場所の要約値を取る道具は `scripts/grasppilot/reldetr_digest.py`。andrew では標準入力で台本を渡して回し、andrew に何も書かない形で前例がある（`tasks/T-2026-11-01-stage2-w23-bengio/audit.md` A-6）。規則（除外する最上位、拡張子）は台本の冒頭にある。**別の規則で取った値を前回の値と比べない**
- 工程塔と検出塔が学習・評価に使うフレームの集合は `conventions#frame_sets`。入力の要約値の取り方と、ホストによらない値（画像 15,437 枚、工程注釈だけのフレーム 1,796、manifest、術具注釈、折りごとの集合）の記録が `experiments/analysis/tower_reselect_search_dlsta/inputs_inventory.json` と `image_input_lock.json`（17,233 行、各画像の SHA-256）にある。**記録の取り方と同じ取り方なら、両ホストの値をこの記録とも照合できる**
- 仮想環境の要約値は二通りの取り方が記録にある。`uv pip list --format freeze` の行の sha256（w23 の audit A-4）と、`importlib.metadata` の「名前==版」の列の sha256（`reldetr_digest.py --venv`）。**取り方を書き添えずに並べない**

### 3.2 直近の実測（2026-11-01〜02。出所つき）

| 項目 | andrew | bengio | 出所 |
|---|---|---|---|
| Relation-DETR main の source_files / source_tree_sha256 | 142 / 2f08e521… | 127 / 3ade18f0… | `tasks/T-2026-11-01-stage2-w23-bengio/audit.md` A-6 |
| 同 all_files / all_tree_sha256 | 155 / 20f15c06… | 140 / 89dc93b4… | 同上 |
| bengio の重ねの BODY（`~/slocal2/s2fix-bengio-body`） | — | andrew main と source・all とも一致 | 同上。重ねの BODY の `.venv-relation-detr` は bengio main の venv へのリンク |
| `.venv` の freeze の行 | 108 行 9c7be5c9… | 108 行 9c7be5c9… | andrew: `tasks/T-2026-11-01-stage2-w23-andrew/audit.md` 68〜70 行、bengio: w23-bengio audit A-4 |
| `.venv-relation-detr` の freeze の行 | 72 行 a74c9c78… | 72 行 a74c9c78… | 同上 |
| 試験 | 6 failed | 11 failed、1 error | andrew: w23-andrew audit 56〜57 行、bengio: w23-bengio audit A-4 |
| GPU と電力の上限 | RTX A6000 × 2 | RTX A6000 × 2、220 W（既定値・最大値 300 W） | bengio: w23-bengio audit A-4。andrew の上限は repo の記録で確かめていない |
| 検出塔の COCO の重み | 2d2c19a7… | 2d2c19a7… | `tasks/T-2026-11-01-grasp-pilot-d/RESULT.md` G1 |
| GPU 2 枚の DDP | `NCCL_P2P_DISABLE=1` が要る（IOMMU） | 未測定 | `tasks/inbox.d/T-2026-10-18-stage2-pilot-folda.md` |

**3.2 の値は前回の契約が取ったもので、本契約の開始時には変わっている可能性がある。** 測り直して並べる。

### 3.3 bengio の前の契約の残り物として記録にあるもの（手がかり。一覧の全部ではない）

- 記号リンク `.venv` と `data/processed/phase_manifest`（追跡外。worktree に足した）、前回・直しの契約の保存先の bengio の写しに andrew と同じ中身の 32 本（`tasks/inbox.d/T-2026-10-19-stage2-pilot-four-new-types.md`）
- `.git/info/exclude` に足した 3 経路と控え `~/m2-git-info-exclude.bak-20261019`（`tasks/inbox.d/T-2026-10-18-evidence-verify-place.md`）
- 仮想環境を uv の 3.11.16 に向け直したまま（`tasks/inbox.d/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle.md`）
- worktree `~/slocal2/m2-four`、重ねの BODY `~/slocal2/s2fix-bengio-body`、保存先 `~/slocal2/stage2pilot_store`（w23-bengio audit 冒頭、four-new-types audit 7 行）
- `/tmp/sp.txt`（`tasks/inbox.d/T-2026-08-11-sandbox-and-host-inventory.md`）

## 4. 禁止事項と申し送り

注入される規約（`conventions#prohibitions`、`conventions#issuer_cautions`、`conventions#env_p0`、`conventions#frame_sets`）に従う。加えて次を守る。

1. **andrew に何も書かない。** repo、家の下、`/tmp` のいずれにも書かない。python は byte code を書かない形で起こす。試験を andrew で回すと書き込みが起きる場合は回さず、記録の値を使う（Task F）
2. **bengio の data 配下、`third_party/`、二つの仮想環境、他の契約の置き場、前の契約の残り物を変えない。** 消さない、動かさない、権限を変えない。本契約が書くのは `experiments/analysis/bengio_andrew_env_survey/` と `tasks/T-2026-11-02-bengio-andrew-env-survey/` だけ
3. **GPU を使わない。** torch を読み込む命令は CUDA の装置を見せない形で起こす。`nvidia-smi` による問い合わせは使ってよい
4. **認証情報の置き場（`~/.ssh/` など）を変えない。** 初めての接続で既知のホストの一覧が変わる形の接続をしない。一覧への接触が実行基盤に拒まれたら、回避せず利用者に示して許諾を得る
5. 電力の上限、クロック、永続モードなど装置の設定を変えない
6. **生成物の再生成（`make taskindex`、`make inbox` など）と `*-check` を本契約の分岐で回さない**（`docs/issuer-defects.md`、自動の再生成が phase0 への統合のたびに走る）。`make forbidden-check` は回してよい
7. 禁止は実行者の操作に対するものである。**Syncthing などの同期処理が他のホストから配る変更は含まない。** 同期で届いた変更は、届いたものとして記録する

**申し送り:**

- コマンドの形、走査の方法、要約値の取り方の細部は、実装と記録を読んで実行者が決めてよい。§3 と規則を揃えることだけを求める
- 一致 0 件・不在の報告は、異質な二通りで確かめてから書く。先頭がドットのものを含める
- 丸めた表示（`du -h` など）を実数として書かない。バイト数で書く
- プロセスの計数は `scripts/grasppilot/proc_enum.py`（`/proc/PID/exe` を見る）を使う
- `.env` の値、鍵、資格情報を報告にも記録にも出さない。要るのは在否と長さだけ

## 5. Task

### Task A — 開始状態（G1）

1. 手順書の「0. 始める」に従う。分岐が `feat/bengio-andrew-env-survey`、起点が `origin/phase0` であることを記録する
2. bengio の repo の HEAD、未追跡の件数、`.sync-pause` の有無、`git worktree list` の結果、記憶領域の空き（バイト）を記録する
3. 本契約以外の compute プロセスの件数を `proc_enum.py` で数え、陽性対照（実在する実行ファイル）と陰性対照（存在しない経路）を添える
4. andrew へ読むだけで届くことを確かめる。andrew の repo の分岐、HEAD、変更と未追跡の件数、`.sync-pause` の有無、走っている compute プロセスの件数を記録する。**andrew が作業中の分岐にあり third_party か仮想環境が変わる兆しがあれば、escalate_if に従って止めて利用者に伝える**
5. 認証情報の置き場の要約値（ファイル名とその sha256）を、読めるなら開始時に取る。読めなければ UNKNOWN と書き、拒まれた事実を記録する
6. 後で前後比較する対象の要約値を、ここで取る: bengio の `third_party/Relation-DETR`（main と重ねの BODY）、二つの仮想環境のパッケージの列、`data/` のうち Task D で見る集合、前の契約の残り物の経路と大きさ。**比べる前の値をここで必ず取る**（後で取ると比べられない）

G1: 上の 1〜4 が記録され、GPU を使わないことを報告に書いたら通過。andrew に届かなければ停止する。

### Task B — Relation-DETR の本体（G2）

1. `reldetr_digest.py` で、andrew main、bengio main、bengio の重ねの BODY の三つの要約値を取る。前回（§3.2）と同じ規則で取る
2. 三つの値を §3.2 と比べる。**一致しなければ G2 で止めて利用者に聞く**（基準が動いた可能性がある）。止める前に、どのファイルが変わったかと、変わった時期の手がかり（mtime、記録）を書く
3. ファイル単位の一覧を作る。両ホストの全ファイル（除外の規則は台本と同じ。除外したものは別表で大きさだけ）について、相対経路・バイト数・sha256 を取り、次の三つに分ける: andrew にだけある、bengio にだけある、両方にあるが中身が違う
4. bengio にだけある中身と、bengio の中身が違うものについて、`third_party_snapshot/Bengio/`（2026-08-02）の tar に同じ中身があるかをファイルごとに書く。**無いものは、揃えると失われる中身として印を付ける**
5. 重ねの BODY を揃える材料に使えるか（andrew main と全ファイルで一致するか）を書く。使えない場合は理由
6. 違うファイルのうち、学習の挙動に関わりうるもの（増強、最適化の群、収束規則、評価）を、ファイル名と diff の要約（何行、どの関数）で示す。**意味の解釈は書かなくてよい。** diff の全文は audit へ
7. 除外した最上位（checkpoints など）にあるファイルは、経路・バイト数・sha256 を両ホストで並べる（Task D の checkpoint と重なってよい）

G2: 2 が一致したら通過。食い違ったら利用者に聞く。

### Task C — 二つの仮想環境

両ホストで、`.venv` と `.venv-relation-detr` について次を並べる。

1. パッケージの列の差（名前と版）。§3.1 の二通りの取り方のどちらで取ったかを書く。可能なら両方
2. `bin/python` の記号リンクの解決先、実体の python の版（patch 番号まで）、`pyvenv.cfg` の `home` と `version` の行
3. 実体の python が uv の管理下か、ほかの経路か。uv の実体の置き場の一覧（env-facts「実行環境」）
4. CUDA の拡張（Relation-DETR の多尺度の deformable attention など、仮想環境か third_party の下でビルドされたもの）のビルド物の経路と sha256。**ビルドし直さない**
5. torch・torchvision の版、torch が報告する CUDA・cuDNN・NCCL の版。CUDA の装置を見せない形で読む。読めない値は UNKNOWN
6. 読み込みの確認として、検出の仮想環境で拡張を import できるかを、CUDA の装置を見せない形で試す。装置が要るため試せない場合は UNKNOWN とし、理由を書く

### Task D — データと checkpoint

1. **集合を実装から決める。** 工程塔の学習と評価（`scripts/stage1_ptower_r3.py` と、その二枚の道）、検出塔の学習と評価（`scripts/run_stage1_dtower.sh`、`configs/` の該当の設定、`scripts/eval_relation_detr_map.py`）、Stage 2 の予備測定の入口（w23 の二つの契約が読んだもの）が読むファイルを、実装の行と既定値（環境変数の既定を含む）から列挙する。根拠の行を表に書く
2. 少なくとも次を含める（実装で読まないと分かったものは理由を書いて外す）:
   - フレーム画像（術具注釈の 15,437 枚と工程注釈だけの 1,796 枚。`conventions#frame_sets`）
   - 工程の manifest、術具注釈の公式分割と折りごとの注釈、`data/splits/`
   - 検出塔の COCO の重み、工程塔の初期化に使う重み（COCO 系統）
   - Stage 2 の予備測定が読む確定塔と送り手の checkpoint と信号（w23 の二つの契約の記録にある一覧）
3. 項目ごとに、両ホストの在否、件数、バイト数、要約値、一致の判定を並べる。画像の集合は `inputs_inventory.json` と同じ取り方で取り、記録の値とも照合する
4. 版管理下の注釈は git の要約値と照合する。版管理外のものは sha256
5. bengio だけで別の経路に置かれているもの（記号リンク、写し）は、実体の経路を書く。Task E と重なってよい
6. 大きさの合計（バイト）を項目ごとに書く。後続の実装契約で写す量の見積もりに使う

### Task E — 前の契約の残り物（bengio）

**残り物の定義（集合で決める）:** bengio の次の範囲にあって、(1) 版管理の起点に無く、(2) andrew の同じ相対経路に無いもの。

- repo の作業ツリーの下（無視されたものを含む）
- `~/slocal2/` の直下
- 家の直下
- `/tmp` の直下のうち、所有者が自分のもの
- git の管理情報: `git worktree list` の worktree、`.git/info/exclude` の行、上流の無い手元の分岐

Syncthing で他のホストから届くもの（両ホストにある）は (2) で外れる。同期の途中で片方にだけあるものは、`.stignore` と同期の記録から見分けて別の欄に書く。

1. 一覧を作る。欄は「経路」「種類（ファイル、ディレクトリ、記号リンクとその先、worktree、除外の行、分岐）」「バイト数」「更新時刻」「作った契約（記録の根拠つき。分からなければ UNKNOWN）」「参照しているもの（記号リンク、worktree の登録、設定の既定値、走っているプロセス）」「同期で他のホストへ渡るか」
2. §3.3 の手がかりがそれぞれ一覧に載ったか、載らなければなぜ（既に無い、など）かを書く
3. repo の作業ツリーの下の違いは件数が多くなりうる。全件は JSON で残し、REPORT には最上位のディレクトリごとの件数とバイト数、experiments 以外の全件を載せる
4. **消さない。動かさない。** 片付けの順序や方法の提案も書かなくてよい（後続の契約の起票者が書く）

### Task F — 装置と系の設定、試験

両ホストで次を並べる。値は問い合わせの出力から取り、丸めない。

1. GPU: 型、UUID、VBIOS の版、driver、メモリ、電力の上限の現在値・既定値・最大値、最大クロック（SM とメモリ）、永続モード、ECC、PCIe の世代と幅（現在値と最大値を分けて書く。負荷の無いときは世代が下がることがあるので、測ったときの負荷も書く）
2. GPU 間の接続（`nvidia-smi topo -m` の行列）、NUMA の割り当て
3. IOMMU の状態の手がかり（読める範囲で。kernel の起動引数、`/sys` の該当の項目。読めなければ UNKNOWN）
4. CPU の型と論理 CPU 数、メモリの総量と cgroup の上限、記憶領域（repo と data がある file system の種類、総量、空き）、kernel の版、容器の中かどうか、nvcc と gcc の版
5. 試験: bengio では手順書と同じ形で試験を回し、失敗と収集の失敗の名前の集合を取る。andrew では書き込みを起こさずに回せる場合だけ回し、回せないなら直近の andrew の契約の記録（§3.2 の出所）の名前の集合を使い、どちらを使ったかを書く
6. 両ホストの失敗の名前の差について、Relation-DETR の違い（Task B）で説明が付くかを名前ごとに書く

### Task G — 検証と報告

1. Task A-6 で取った要約値を取り直し、前後で一致することを確かめる（acceptance h）
2. andrew に送った命令をすべて audit に残し、書き込みを起こす命令が無いことを書く
3. `make forbidden-check` を回す。同期で届いた他の契約のファイルによる違反は、本契約の経路と分けて件数を書く
4. 報告（§7）を書き、commit、push、PR を作る。**PR の base は phase0。** Draft を外す
5. `make task-report` で台帳へ返す。抑止の目印は手順書の「8. 終える」が外す

## 6. 完了判定

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 両ホストの分岐・HEAD・変更と未追跡の件数、bengio の compute 0 件、空き（バイト）が記録されている | プロセスの計数で、実在する実行ファイルが 1 以上、存在しない経路が 0 |
| b | Relation-DETR | 三つの場所の要約値が §3.2 と並び、ファイル単位の三分類と、bengio の中身の保全の可否がファイルごとにある | 三分類の件数の和が、両ホストのファイル数の和集合と一致する。1 バイト変えた写しを道具が「違う」と分ける |
| c | 仮想環境 | 二つの仮想環境の五項目（パッケージの差、python の実体と版、pyvenv.cfg、拡張のビルド物、CUDA・cuDNN・NCCL）が両ホストで並ぶ | パッケージの列の比較に、一行を書き換えた写しを入れると差として出る |
| d | データと checkpoint | 集合が実装の行を根拠に列挙され、項目ごとに在否・件数・バイト数・要約値・判定がある。画像は記録とも照合されている | 記録の画像の一つを選び、要約値を一文字変えた値と比べると不一致になる。存在しない経路は「無い」と出る |
| e | 残り物 | 定義の範囲の全件が JSON にあり、REPORT に欄つきの一覧がある。§3.3 の手がかりの行方が書かれている | andrew にもある既知のファイルを一つ選び、一覧に出ないことを確かめる。§3.3 の既知の残り物が一覧に出ることを確かめる |
| f | 装置と系 | Task F の 1〜4 が両ホストで並ぶ。読めない値は理由つきの UNKNOWN | 同じ問い合わせで、存在しない GPU の番号を指定すると失敗になる |
| g | 試験 | 両ホストの失敗の名前の集合と差、差ごとの説明の可否がある | 差の計算に、名前を一つ足した集合を入れると差に出る |
| h | 無変更 | andrew に書き込む命令が 0 件。bengio の data・third_party・仮想環境・他の契約の置き場・残り物の要約値が前後で一致 | 同じ要約値の取り方で、本契約の出力の置き場は前後で違うと出る |
| i | GPU 不使用 | 本契約のプロセスが GPU の compute に現れない。torch を読む命令は装置を見せない形で起こした | 列挙の道具が、実在のプロセスを 1 以上、存在しない経路を 0 と数える |
| j | PR | PR が存在し、base が phase0、分岐が `feat/bengio-andrew-env-survey`、Draft でない | — |

## 7. 報告の構成

### 7.1 `RESULT.md`（起票者が判断に使う事実だけ。目安 150 行以内）

| 節 | 内容 | 入れないもの |
|---|---|---|
| 判定 | verdict と G1・G2 の結果 | 手続きの全文 |
| 完了判定 | §6 の表。各項目に実測値 | 命令の全文 |
| 実測 | 後続の契約で使う値: 揃える必要のある項目の一覧（B・C・D の不一致）、揃えると失われる中身、写す量（バイト）、残り物の件数と最上位ごとの内訳、装置と系の差の表 | 経過の説明 |
| 起票者の誤り | 型と内容。一件 3 行以内 | 引用の全文 |
| 逸脱 | 何をなぜ | 手順の再掲 |
| 想定外・UNKNOWN | 測れなかったものと理由 | 不要なログ |
| 送出 | PR 番号、`make task-report` の終了コードだけ | 出力の全文 |

### 7.2 `audit.md`

命令とその出力、andrew に送った命令の全件、要約値の全件、diff の全文、検証の出力、変更範囲の一覧、台帳の応答。
`RESULT.md` からは行番号で指す。同じ内容を二度書かない。

### 7.3 `experiments/analysis/bengio_andrew_env_survey/`

`REPORT.md`（Task B〜F の表）と、機械で読める JSON（Relation-DETR のファイル単位の表、仮想環境のパッケージの列、データの項目の表、残り物の全件、装置と系の値）。
大きな出力は 1 ファイル 5 MB を超えないように分ける。

## 8. 想定外のときの扱い

- andrew の repo が作業中の分岐にある: 分岐名と、third_party・仮想環境に作業の兆し（直近の mtime）があるかを記録し、兆しがあれば止めて利用者に伝える
- andrew で読むために書き込みが要る（一時ファイルなど）: その項目は UNKNOWN にするか止めて利用者に伝える。書かない
- 認証情報の置き場への接触が拒まれた: 回避しない。利用者に示して許諾を得る
- 要約値を取るために data 配下へ書く必要が出た: 書かない。止めて利用者に伝える
- 走査が長くなる（画像の要約値など）: 待ってよい。所要時間を記録する。本契約の範囲を狭めて短くしない
- 試験が収集の段階で止まる: 止まった名前を記録して続ける（bengio では既知。`tasks/inbox.d/T-2026-10-18-evidence-verify-place.md`）

## 9. 参照しなかった項目

- 分母: 本契約は比べる実験を持たないので `inputs.denominator` を置かない。報告に「参照しなかった」と書く
- 規約の版 `contract.conventions_rev` と `meta.created_from.runindex_commit` は起票時の値。実行者が実測して差し替える
