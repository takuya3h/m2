# audit — T-2026-11-02-bengio-andrew-env-survey

時刻は UTC で記録し、要所に JST を添える（JST = UTC+9）。出力の置き場 `$D = experiments/analysis/bengio_andrew_env_survey`。
andrew へ送った命令は全件 `andrew_cmds.log`（同じディレクトリ）にある。包みは `tools/A.sh`（`StrictHostKeyChecking=yes`、
`UpdateHostKeys=no`、`BatchMode=yes`。既知のホストの一覧を変えない形）。

## 0. 始める

- 2026-11-02 11:1x UTC（20:1x JST）。開始時の分岐 `feat/stage2-w23-bengio`、未追跡 32 件（`experiments/phase1/w23a_pd_*` の logs）。
- 分類 `scripts/task_start_classify.py`（比較先 origin/phase0 231c280e）: 32 件すべて「未追跡・起点に在り中身が同じ」→ **通す**。
- `make task-start`: 分岐 `feat/bengio-andrew-env-survey`（起点 origin/phase0）を作成、**`[task-start] .sync-pause を作成`**（この契約が置いた目印）、
  契約を取り込み `[task-start] 完了。`。
- `grep -c sync-pause ~/bin/m2-sync.sh` → 2（稼働中の版は抑止に対応済み）。
- `make task-validate` → OK。`make task-preflight` → 6 PASS / 0 WARN / 8 SKIP / 0 FAIL。
  SKIP: P2 cuda_ext_loaded、P3 deterministic_flags、P4 prereg_committed、P5 frozen_source_hash、P11 gpu_free、P12 refs_resolved、
  P13 symmetry_table_complete、P14 proposal_card_checked（いずれも契約に記載なし・kind 対象外）。P9 spec_lint は該当なし。

## Task A — 開始状態（G1）

### A-1・A-2 bengio（`$D/start/a_bengio_state.txt`、11:19:12 UTC）

    branch: feat/bengio-andrew-env-survey
    HEAD = origin/phase0 = merge-base = 231c280e3f78decd89c62027ca263e861a58ef9d
    未追跡 10 件（この時点で本契約が書いたものだけ: tasks/<id>/SPEC.md・spec.yaml・andrew_cmds.log・tools/A.sh、$D/start/ の 6 件）
    追跡下の変更 0 件
    .sync-pause: task_id=T-2026-11-02-bengio-andrew-env-survey / branch=feat/bengio-andrew-env-survey
    git worktree list:
      /home/ubuntu/slocal2/m2                 231c280e [feat/bengio-andrew-env-survey]
      /home/ubuntu/slocal2/m2-four            792527a7 [feat/stage2-pilot-four-new-types]
      /home/ubuntu/slocal2/m2-s2fix-bengio    78f8260b [feat/stage2-pilot-fix-epoch4-shuffle-bengio]
      /tmp/claude-1000/-home-ubuntu-slocal2-m2/75c88ccf-.../scratchpad/wt_phase0 67c4cc44 (detached HEAD)
    df -B1: /dev/sdb1 ext4（/home/ubuntu/slocal2） size 7937302376448 used 6122163478528 avail 1415044030464
            overlay（/、家と /tmp） size 1967317549056 used 466688114688 avail 1400619614208

### A-3 compute プロセス（bengio、`$D/start/a_procs.json`、道具 `scripts/grasppilot/proc_enum.py`）

    proc_enum.py                                   → n_processes 54、n_compute 0、gpu_pids []
    proc_enum.py --match-exe /usr/bin/zsh          → count 8（陽性対照）
    proc_enum.py --match-exe /nonexistent/bin/python9 → count 0（陰性対照）

**本契約は GPU を使わない。** 学習・推論をしない。torch を読み込む命令は `CUDA_VISIBLE_DEVICES=""` で起こす。`nvidia-smi` の問い合わせだけ使う。

### A-4 andrew（読むだけ。`andrew_cmds.log` の 1〜5 行）

    hostname: Andrew
    repo ~/slocal2/m2: branch feat/stage2-w23-andrew、HEAD a78e2f3cd2d0fffe211f8439123ea1f3a3749d9f
      （最新 commit 2026-11-02 06:52:29 +0000 "Merge pull request #280 from takuya3h/auto/regen-projections"）
    git status: 追跡下の変更 0 件、未追跡 41 件。.sync-pause 無し（andrew の自動同期は抑止されていない）
    proc_enum.py（標準入力で渡す）→ n_processes 33、n_compute 0、gpu_pids []

**escalate_if の判定。** andrew は作業中の分岐 `feat/stage2-w23-andrew` に居る。作業の兆しを mtime と要約値で調べた:
`third_party/Relation-DETR` の最新のファイルは 2026-10-19 08:10（`per_class_coco_map/epoch_000.json`）、`.git` だけ 2026-10-31 16:12。
`.venv` の 2026-10-25 以降の変化は `__pycache__` のディレクトリ（2026-10-31 13:15）だけ。`.venv-relation-detr` は 2026-10-18 06:08 が最新。
要約値は §3.2 と一致した（A-6）。compute 0 件。**作業の兆しは無いと判定し、止めずに続けた。**

### A-5 認証情報の置き場（`$D/start/cred_before.txt`。名前・バイト数と、全行をまとめた sha256。値は出さない）

利用者の方針（秘密鍵への接触は事前確認）に従い確認し、「sha256 を取る」の回答を得て取った（11:2x UTC）。
`~/.ssh` の 14 ファイルと repo の `.env`（250 B、在る）・`.env.gpg`（296 B）。
ファイルごとの sha256 は取ったが、契約 §4（資格情報は在否と長さだけ）に合わせて公開の repo には置かず、bengio の scratchpad に置いた。repo には名前・バイト数と、名前・バイト数・sha256 の全行をまとめた sha256（9de4f44be4e772f6…）だけを残した。
なお Task A の接続設定の確認のため、`known_hosts` の sha256 を開始前に一度読んだ（接続の前後で同じ値）。

### A-6 前後比較の「前」の値

Relation-DETR と仮想環境（`reldetr_digest.py`、`--files`。andrew は `PYTHONDONTWRITEBYTECODE=1 python3 -B -I -` に標準入力で渡す）:

| 場所 | source_files | source_tree_sha256 | all_files | all_tree_sha256 | `.venv-relation-detr` | `.venv` |
|---|---|---|---|---|---|---|
| andrew main | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… | 72、8f08a2457e681d6d… | 108、9020a519e653562f… |
| bengio main | 127 | 3ade18f0709362fa… | 140 | 89dc93b4a82f1e06… | 72、8f08a2457e681d6d… | 108、9020a519e653562f… |
| bengio 重ねの BODY | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… | （main の venv へのリンク） | 同 |

（パッケージの列は `importlib.metadata` の「名前==版」の列の sha256。freeze の行の値とは取り方が違う。）

stat の木（`tools/stat_tree.py`。相対経路・種類・バイト数・mtime_ns・リンク先の列の sha256。中身は読まない）:
`$D/start/stat_before_main.json`、`stat_before_experiments.json`（本契約の置き場を除く）、`stat_before_tasks.json`（本契約を除く）。

| 名前 | entries | files | bytes | stat_tree_sha256 |
|---|---|---|---|---|
| data | 236796 | 236174 | 33359023580 | 08729bb041d54e3d… |
| third_party | 316 | 253 | 4388060372 | c50bac91ad15e600… |
| .venv | 37878 | 34264 | 6461113932 | c6ec6a7503dcdfe8… |
| .venv-relation-detr | 22733 | 20981 | 5035459935 | f2c740b0d5664251… |
| ~/slocal2/stage2pilot_store | 1975 | 1152 | 23180452876 | ad08d931f7477926… |
| ~/slocal2/m2-four | 26417 | 23212 | 858487796 | d3c6636e21361b5d… |
| ~/slocal2/m2-s2fix-bengio | 24821 | 21965 | 587164743 | 3bc57cad88e3a2da… |
| ~/slocal2/s2fix-bengio-body | 284 | 239 | 3097807 | 5c2ba98bfc9dd4d7… |
| ~/slocal2/m2-incoming | 31 | 27 | 2000925 | 34c10c9ddb7728a9… |
| third_party_snapshot | 92 | 72 | 247974 | b5da500f4e79b60d… |
| experiments（本契約の置き場を除く） | 35553 | 27754 | 132535676025 | f48db53fa435291c… |
| tasks（本契約を除く） | 2143 | 1770 | 111507078 | 2739c010ce29b6f8… |

### G1 の判定

分岐 `feat/bengio-andrew-env-survey`、起点 origin/phase0 231c280e。GPU を使わないことを記録した。andrew へ読むだけで届き、
分岐・HEAD・未追跡の件数を記録した。**通過。**

## Task B — Relation-DETR の本体（G2）

- 道具: `tools/tree_files.py`（除外の規則は `reldetr_digest.py` と同じ。両ホストとも `python3 -B -I -` に標準入力で渡す）→ `$D/b/{andrew_main,bengio_main,bengio_overlay}_files.json`。
  比較 `tools/compare_reldetr.py` → `$D/b/reldetr_compare.json`。
- 三分類: andrew 155、bengio 140、和集合 155 = andrew だけ 15 + bengio だけ 0 + 違う 8 + 同じ 132。重ねの BODY と andrew main は 155 件すべて同じ。
- 陽性対照: `compare_reldetr.py --selftest`（bengio の 1 ファイルの sha256 を別の値に置き換えた写し）→ 違う 8 → 9。
- `checkpoints` の 12 件は両ホストで sha256 一致（表 B-3）。
- 違う 8 件の andrew の中身は `cat` で読み（`andrew_cmds.log`）、`$D/b/andrew_copies/` に置いた。読んだ中身の sha256 は andrew の digest の値と一致
  （例 main.py ffbd6deb9ad48ec3…）。diff の全文は `$D/b/diffs_bengio_vs_andrew.patch`（683 行。audit に同じ内容を二度書かないため経路で指す）。
- `main.py` は bengio だけ CRLF（213 行すべてに CR）。`--strip-trailing-cr` で比べると andrew だけ 68 行、bengio だけ 3 行
  （`from accelerate.utils import ProjectConfiguration`、`for epoch in range(cfg.starting_epoch, cfg.num_epochs):`、`lr_scheduler.step()`）。
- mtime（UTC）: bengio の `main.py`・`transforms/presets.py` は 2026-05-28 08:05:39（上流の展開の一括、`third_party_snapshot/Bengio/README.md` の表）。
  andrew の `main.py` は 2026-10-17 03:30:52、`presets.py`・`param_dict.py` は 2026-10-13 19:27:04、configs は 2026-07-28。
- スナップショット: `third_party_snapshot/Bengio/Relation-DETR/project_files.tar.gz` の 22 件の sha256 と照合。違う 8 件のうち 6 件は同じ経路・同じ中身で在る。
  `main.py` と `transforms/presets.py` は無い（tar に経路そのものが無い）。

### G2 の判定

andrew main・bengio main・重ねの BODY の要約値が §3.2 の記録と三つとも一致（source と all の両方）。**通過。**

## Task C — 二つの仮想環境

- パッケージ: `importlib.metadata` の列（`reldetr_digest.py --venv --files`、両ホスト）、dist-info 名の列（`ls site-packages`、両ホスト）、
  `uv pip list --format freeze`（bengio だけ。andrew では `uv pip` を回さず記録の値を使った。uv の cache への書き込みを避けるため。andrew で uv は `--version` だけ呼んだ）。
  比較 `tools/compare_pkgs.py` → 差 0。陽性対照 `--selftest`（bengio の列の 1 行に `.post999` を足す）→ 差に 1 件ずつ出た。
- 版: `tools/venv_probe.py` を `CUDA_VISIBLE_DEVICES= LD_LIBRARY_PATH=/usr/local/cuda/lib64 <venv>/bin/python -B -I - --load` で回した
  （`$D/c/{andrew,bengio}_{venv,venv-relation-detr}.json`）。4 つとも `cuda_is_available false`、`device_count 0`、`cuda_initialized` は前後とも false。
- `build.ninja` の差（`$D/c/build_ninja.diff`）は 27 行目の `.cu` の経路だけ。

## Task D — データと checkpoint

- 経路の一覧 `tools/lists.json`（`tools/build_lists.py` が作る。画像は `image_input_lock.json` の selected と counterpart の 32,670 経路）。
- 道具 `tools/data_inventory.py`。bengio は `--lists`、andrew は一覧を埋めた写し（scratchpad、bengio 側）を `python3 -B -I -` に標準入力で渡した。
  1 回目は `fold_report.json`（COCO 形式でない）で両ホストとも KeyError で止まり、直して 2 回目（11:29:14〜11:29:27 UTC、bengio 9 秒）。
- 突き合わせ `tools/compare_data.py` → `$D/d/data_compare.json`。B1 は andrew・bengio・記録の三者一致（動画ごとの 15 個も）。固定記録の 32,670 経路は両ホストとも欠け 0・不一致 0。
- 陽性対照: 記録の画像の一つの sha256 の先頭 1 文字を変えて比べる（`compare_data.py --selftest`）→ 不一致 1。
  存在しない経路: Stage 2 の材料の 17 経路は片方のホストで `exists false` と出た（表 D-2 の「andrew だけ」「bengio だけ」）。
- D-4 git の要約値: `git ls-tree origin/phase0` の blob と、両ホストで中身から計算した blob（`blob <len>\0<中身>` の sha1）が一致
  （`instances_train` 9344b792…、`instances_val` 84583a0d…、`instances_test` f16cc466…、`ego_train` 241129b7…、`ego_val` 76dfcc83…、`ego_test` 4dd2d487…、`A1_fold_table.md` 0b4d2e40…）。工程 CSV 43 件の blob は `data_compare.json` の `phase_csv.git_blobs`。
- `data/raw/ego` 全体の差は `find -printf "%P\t%s"` の一覧で取った: andrew だけ `train/.DS_Store` 12,292 B。

## Task E — 残り物

- 一覧: 両ホストで `find`（repo は `.git` を除く全件、`~/slocal2`・家・`/tmp` は直下）と git の管理情報（worktree、exclude、分岐）を取り、
  `tools/leftovers.py` で定義どおりに引いた（`$D/e/`）。phase0 の木は `git ls-tree -r --name-only origin/phase0`（28,874 経路）。
- 対照（`leftovers.py --selftest`）: andrew にもある `README.md` は出ない（false）。既知の残り物 `~/m2-git-info-exclude.bak-20261019` は出る（true）。
- 大きさは `du -sb --apparent-size`（`$D/e/sizes.json`）。ディレクトリ自身の 4,096 B を含む見かけの大きさ。
- 作った契約の手がかり（経路に識別子が無いもの）: `~/slocal2/m2-four` は worktree の分岐 `feat/stage2-pilot-four-new-types`（T-2026-10-19-stage2-pilot-four-new-types）、
  `~/slocal2/m2-s2fix-bengio` と `~/slocal2/s2fix-bengio-body` は分岐名と w23-bengio の audit 冒頭から T-2026-10-19-stage2-pilot-fix-epoch4-shuffle、
  `.venv-relation-detr/pyvenv.cfg.before_s2fix` も同じ契約（名前の `s2fix`）。ほかは UNKNOWN。
- `/tmp/sp.txt` は `ls`（No such file）と `find /tmp -maxdepth 1 -name sp.txt`（0 件）の二通りで無い。

## Task F — 装置と系

- 台本 `tools/sysinfo.sh` を bengio は `bash`、andrew は `bash -s` に標準入力で渡した（`$D/f/{andrew,bengio}_sysinfo.txt`、11:29:39〜40 UTC）。
- `dmesg` は両ホストとも出力なし（権限で読めない可能性。IOMMU の判断は `/sys` の二項目で行った）。
- 試験（bengio、11:32:59〜11:33:48 UTC）: `$D/f/bengio_pytest.txt`、名前 `$D/f/bengio_fail_names.txt`。
  `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/start/a4_pytest_fail_names.txt` と名前の集合が同じ（表記の接頭辞 FAILED/ERROR の有無だけ違う）。
  試験は `PYTHONDONTWRITEBYTECODE=1` で回した（`__pycache__` を repo に書かないため。手順書の形に足した）。
- 差の陽性対照: andrew の 6 件の集合に名前を 1 つ足すと、差（bengio − andrew）の件数が 6 → 5 に変わる（下の命令で確かめた）。

## Task G — 検証

### G-1 前後比較（`$D/end/`、11:34:38 UTC）

bengio: Relation-DETR の 3 か所（source・all・パッケージ）、stat の木 12 個（data、third_party、二つの仮想環境、stage2pilot_store、m2-four、m2-s2fix-bengio、
s2fix-bengio-body、m2-incoming、third_party_snapshot、experiments〈本契約を除く〉、tasks〈本契約を除く〉）、認証情報の置き場 16 件（ファイルごとの sha256 とまとめた値）が**すべて開始時と一致**。
andrew: Relation-DETR と二つの仮想環境の要約値が開始時と一致。HEAD a78e2f3c も同じ。
陽性対照: 同じ stat の木の取り方で、本契約の出力の置き場（`$D` と `tasks/<id>`）は 11:34 と 11:37 で違う値になった（`end/stat_own.json` と `stat_own2.json`）。

### G-2 andrew に送った命令

全件 `andrew_cmds.log`。読み取り（`git`・`ls`・`find`・`cat`・`nvidia-smi`・`lscpu`・`df` など）と、標準入力で渡した python（`-B -I`、`PYTHONDONTWRITEBYTECODE=1`）だけ。
書き込みを起こす命令は送っていない。`>`・`mv`・`rm`・`cp`・`tee`・`touch`・`mkdir`・`uv`・`pip`・`pytest` を grep すると 34 行中 9 行に当たるが、`2>&1`・`2>/dev/null`・`=>` を除くと 2 行（15・20 行）が残る。残りは echo の文字列 `->` と、`uv --version`（15 行は PATH に uv が無く実行されず、20 行は `~/.local/bin/uv --version` で版を表示しただけ）。`uv pip` は andrew で回していない。ファイルへの書き込みの向き先を持つ命令は 0 件。
python の台本は結果を標準出力へ出すだけで、ファイルを開いて書く処理を持たない。

**想定外（同期による副作用）**: andrew の 11:15 以降の更新を読んだところ（`$D/end/andrew_after.txt`）、repo の中に
`experiments/analysis/bengio_andrew_env_survey/b/andrew_copies/*.py` の 8 件（11:23）があった。本契約が bengio の置き場に書いた写しが、
`.stignore` の `!experiments/**/*.py` により Syncthing で andrew へ渡ったもの。andrew の未追跡が 41 → 49 件になった差はこの 8 件。
家の下の更新は Syncthing の索引・`.claude/settings.json`・`.codex` の記録など、本契約の命令によらないもの。`/tmp` の自分のものは 0 件。
利用者に諮り（11:3x UTC）、「拡張子を変えて同期から外す」の回答を得て、bengio 側で 8 件を `.py.txt` に改名した（11:37:01 UTC）。
改名の後の andrew の状態は G-2b に書く。

### G-3 禁止領域

`make forbidden-check`（TASK 指定なし）は `status fail`・違反 59（すべて本契約の `experiments/analysis/bengio_andrew_env_survey/`。TASK を渡さないと allow_write が効かない）。
`make forbidden-check TASK=T-2026-11-02-bengio-andrew-env-survey` は `status pass`、changed 77、violations 0、permitted 59。
同期で届いた他の契約のファイルによる違反は 0 件（changed の 77 件はすべて本契約の経路）。

### G-2b 改名の後の andrew（読むだけ、`$D/end/andrew_after_rename{,2}.txt`）

- 11:37:25 UTC: まだ 8 件が在り、未追跡 49 件（改名から 24 秒）。
- 11:40:37 UTC: `experiments/analysis/bengio_andrew_env_survey/` の下のファイル 0 件、**未追跡 41 件（開始時と同じ）**、HEAD a78e2f3c（同じ）。
  同期が削除を andrew へ渡した。
- 11:44:49 UTC（`andrew_cmds.log` 34 行）: andrew に**空のディレクトリが 3 つ残る**（`experiments/analysis/bengio_andrew_env_survey/`・`b/`・`b/andrew_copies/`、同期が 11:23 に作り、`andrew_copies` は 11:38 に中身が消えた）。ファイルは 0、未追跡は 41 件のまま（git は空のディレクトリを数えない）。andrew には書かない約束なので消していない。phase0 への統合の後は、同じ経路に本契約の記録が git で届く。
- 改名した `.py.txt` は `.stignore` の同期対象に当たらない（`**` で無視）。本契約の置き場のほかのファイル（`.json`・`.txt`・`.md`・`.patch`・`.tsv`・`.ninja`・`.diff`・`.err`）も当たらない。

## 変更範囲

本契約が書いたのは `tasks/T-2026-11-02-bengio-andrew-env-survey/` と `experiments/analysis/bengio_andrew_env_survey/` だけ（`make forbidden-check TASK=...` で pass）。
ほかに bengio の scratchpad（`/tmp/claude-1000/.../scratchpad/`）に一時ファイル（andrew へ渡す一覧を埋めた台本、両ホストの一覧の生の出力）を置いた。
`.sync-pause` は task-start が置いた。試験は `/tmp` に pytest の一時ディレクトリを作る（bengio）。

## 送出

- PR #282（base phase0、head feat/bengio-andrew-env-survey、isDraft false、OPEN）。
- `make task-report`（2026-11-02 11:4x UTC）: 終了コード 0。台帳の応答 `verdict pass`、`n_issuer_defects 2`、`report_sha256 0f9be6c1e9cc237e…`、`report_bytes 9303`、`replaced_blocks 0`。
