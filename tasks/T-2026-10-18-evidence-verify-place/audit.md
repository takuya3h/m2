# audit — T-2026-10-18-evidence-verify-place

実行ホスト `bengio`（`hostname` は `Bengio`）。時刻は JST。命令と出力を節ごとに置く。

## 0. 始める段

### 0.1 最初の状態（2026-10-19 01:1x）

- 分岐 `feat/drop-projection-check-in-contracts`、`.sync-pause` 無し、`tasks/T-2026-10-18-evidence-verify-place/` 無し、
  `feat/evidence-verify-place` は手元・遠隔とも無し、契約の履歴無し
- 判定: **汚れ**。`git status --porcelain --untracked-files=all` が 22 行、`git status --porcelain` が 14 行。すべて未追跡（`??`）で禁止領域 `experiments/` の中
- 手順書の選択肢 1（禁止領域外の未追跡を退避）を利用者が選んだ。**退避の候補は 0 件**（`grep -v -E '^(experiments|data|runindex)/'` の件数 0）。何も移していない。`~/m2-evacuated/` は作っていない
- task-start を一度だけやり直した → `[task-start] 作業ツリーに未commitの変更が 14 件あります。片付けてから実行してください`（make の exit 2）。分岐・目印は作られていない

### 0.2 未追跡 14 件（`git status --porcelain`、利用者の判断で exclude に入れた）

利用者の説明: andrew の他の契約（T-2026-10-18-stage2-pilot-folda と T-2026-10-14-frame-signal-audit）の出力が Syncthing で届いたもの。移す・消す・stash・clean はしない。

```
?? experiments/analysis/frame_signal_audit/
?? experiments/analysis/stage2_pilot_folda/
?? experiments/phase1/stage2pilot_pd_P1-W1_empty_seed42/
?? experiments/phase1/stage2pilot_pd_P1-W1_gt_seed42/
?? experiments/phase1/stage2pilot_pd_P1-W1_gt_seed42_smoke/
?? experiments/phase1/stage2pilot_pd_P1-W1_pred_noCF_seed42/
?? experiments/phase1/stage2pilot_pd_P1-W2_gt_seed42_smoke/
?? experiments/phase1/stage2pilot_pd_P2F_gt_seed42/
?? experiments/phase1/stage2pilot_pd_P2F_pred_seed42/
?? experiments/phase1/stage2pilot_pd_P2L_empty_seed42/
?? experiments/phase1/stage2pilot_pd_P2L_gt_seed42/
?? experiments/phase1/stage2pilot_pd_P2L_gt_seed42_smoke/
?? experiments/phase1/stage2pilot_pd_P2L_pred_noCF_seed42/
?? experiments/phase1/stage2pilot_pd_P3_gt_seed42_smoke/
```

ファイル単位では 22 件（`frame_signal_audit/tools/` の .py 2 件、`stage2_pilot_folda/tools/proc_enum.py` 1 件、
`stage2pilot_pd_*/logs/` の `eval_meta_val.json` 11 件と `val_metrics_by_epoch.json` 8 件）。
`frame_signal_audit/tools/` の 2 件は origin/phase0 で追跡済みで中身も同一、残り 20 件は phase0 に無い（実験フォルダごと無い）。

### 0.3 `.git/info/exclude` への追加（利用者の指示、2026-10-19 01:29 頃）

- 控え: **有り**。元のファイル（565 バイト）を `cp -p` で `~/m2-git-info-exclude.bak-20261019` へ控え、`cmp` で一致を確かめた（sha256 先頭 `db8df0bae96c571c`）。控え先は事前に存在しなかった
- 足した行（末尾。21〜23 行目が規則）:

```
# 2026-10-19 bengio: Syncthing で届いた他契約の出力。消さないこと（T-2026-10-18-evidence-verify-place の起動のため）
experiments/analysis/frame_signal_audit/
experiments/analysis/stage2_pilot_folda/
experiments/phase1/stage2pilot_*/
```

- 追加の前後の行数:

| | `git status --porcelain` | `--untracked-files=all` |
|---|---|---|
| 前 | 14 | 22 |
| 後 | 0 | 0 |

- 効き方: `git check-ignore -v` で 3 経路がそれぞれ `.git/info/exclude:23` `:21` `:22` に当たった（`.gitignore:116` の `!` 規則に負けていない）。22 ファイルとも元の場所に実在することを確かめた
- 追加前に確かめたこと: `.gitignore` に、これらのフォルダ自体に当たる規則は無い。phase0 で追跡中の `stage2pilot_*` フォルダは 0 件
- **exclude の行は契約が終わっても消さずに残す**（利用者の指示）

### 0.4 常駐の同期の副作用（私の操作ではない）

exclude で作業ツリーが清浄になった後、常駐の同期が元の分岐を早送りで統合し push した。

```
2026-10-18 16:36:33 [bengio] auto-merge: feat/drop-projection-check-in-contracts <- origin/phase0 (11 commits)
2026-10-18 16:36:36 [bengio] auto-push: feat/drop-projection-check-in-contracts (11 commits)
2026-10-18 16:38:55 [efros] auto-merge skip: 未追跡 2 件が阻害 (behind 11) 手動対応が必要
```

（`~/claude-sync/sync-alerts.log` の時刻は UTC。JST では 01:36:33・01:36:36）

利用者の依頼による読み取りだけの確認（2026-10-19 02:0x。戻す・閉じるなどの操作はしていない）:

- `gh pr list --head feat/drop-projection-check-in-contracts --state all` → **開いている PR は無い**。在るのは #213（`MERGED`、base `phase0`、Draft でない、2026-10-07T09:02:22Z に統合、head `9ff2a9a8`）の 1 件だけ
- push の前後の先頭: **`57717f6c` → `40112290`**（手元の reflog `merge origin/phase0: Fast-forward` 01:36:33、遠隔追跡の reflog `update by push` 01:36:36）。遠隔の先頭は `ls-remote` で `40112290ed8e53165d9ea1a0dce6cdc7cddae2ce`

### 0.5 phase0 への切り替えと task-start

- 利用者の指示で `git checkout phase0`。切り替え前に `git diff --name-status HEAD phase0` が 0 件（HEAD・phase0・origin/phase0 がすべて `40112290`）であることを確かめた
- 読み取り命令の再実行: 分岐 `phase0`、`status --porcelain --untracked-files=all` 0 行 → 判定 **清浄**
- `source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-18-evidence-verify-place`:

```
[task-start] git fetch origin
[task-start] 分岐を作成: feat/evidence-verify-place（起点 origin/phase0）
[task-start] .sync-pause を作成（報告まで終えたら make task-release TASK=T-2026-10-18-evidence-verify-place END=complete）
[task-start] 契約を取り込みます: T-2026-10-18-evidence-verify-place
OK   T-2026-10-18-evidence-verify-place
1 task(s), 0 failed
取り込みました: tasks/T-2026-10-18-evidence-verify-place
[task-start] 完了。分岐 feat/evidence-verify-place で契約 T-2026-10-18-evidence-verify-place の作業を開始できます
```

- 目印: **作成**（この契約が置いた）。中身 `task_id=T-2026-10-18-evidence-verify-place` / `branch=feat/evidence-verify-place` の 2 行、77 バイト、01:42:12 作成。`grep -c sync-pause ~/bin/m2-sync.sh` = 2（対応済み）

### 0.6 検証とプリフライト

- `make task-validate`: `OK`（exit 0、WARN なし）
- `make task-preflight` 一回目: 5 PASS / 0 WARN / 8 SKIP / **1 FAIL**（`P6 decisions_answered` 未回答 4 件）→ 停止して利用者に提示
- 利用者の回答（2026-10-19）: 4 件とも括弧のとおり（外さない／反映しない／登録しない／入れない）。`spec.yaml` の `meta.amendments` に回答を追記し `governance.decisions_required` を `[]` にした（前例 T-2026-10-17-tower-reselect-prereq と同じ形）
- 再検証: `task-validate` OK（exit 0）。`task-preflight` 6 PASS / 0 WARN / 8 SKIP / 0 FAIL（exit 0）
- SKIP の一覧: P2 cuda_ext_loaded・P3 deterministic_flags・P11 gpu_free（宣言なし）、P4・P5・P13・P14（kind=impl）、P12（解決前提の参照なし）

## A. 起点の確認（Phase A）

### A-1 分岐と起点

```
branch=feat/evidence-verify-place
HEAD=40112290ed8e53165d9ea1a0dce6cdc7cddae2ce  origin/phase0=40112290ed8e53165d9ea1a0dce6cdc7cddae2ce  merge-base=40112290ed8e53165d9ea1a0dce6cdc7cddae2ce
40112290 2026-10-18T01:36:00Z Merge pull request #230 from takuya3h/auto/regen-projections
```

起点は origin/phase0 の `40112290`（spec の `created_from.runindex_commit`・`contract.conventions_rev` と同じ版）。

### A-2 受け渡しの十件

置き場 `realpath` = `/home/ubuntu/slocal2/m2-incoming/T-2026-10-18-evidence-verify-place`、repo の最上位 `/home/ubuntu/slocal2/m2` の下ではない（**repo の外**）。
SPEC の表を本文から機械で読み（10 行）、置き場のファイルから sha256 とバイト数を計算して比べた。

```
OK  2026-10-18-C-d2p-interface.md  71540  05a982ef4c8a9372a3855414393714c15cbb2cebabbbc6a07855eef22a5dc563  末尾改行=有
OK  2026-10-18-B-p2d-interface.md  65725  1ab24a3cbfaba4f7b654c8fcd12a9deb9f9556c337b95392d10897011ee9ccca  末尾改行=有
OK  2026-10-18-N-novelty.md        31607  9bb804b2eacdaac8842e2fc952d70479e747c9657186909ea9740b9e0413e6c8  末尾改行=有
OK  evidence-template.md            4474  69e95ea37106fac90b463eabde7879cfc60df1575ffabdd10223f1c9f5b61376  末尾改行=有
OK  deep-research-report-C2.md     72966  5d3c3ed514551cf11d1b75dcc8b6542b7fb5efefeedb91956a5d561284c141fd  末尾改行=無
OK  deep-research-report-B2.md     72035  c7aad1c222d9159c1209a557f765e0400f85a3b6ccd8d92025683a2ce8102116  末尾改行=無
OK  R1-deep-research-report.md     40202  1f95517bf4ce63015d9574ee7e3616859021882a7014feb4f261d76d9c49dce5  末尾改行=無
OK  B-chatgpt.md                   38349  ef94ea71aba1b5e81dea60ae0b55581dfdfda7cf290fe29d56dcb20b7bc33dd9  末尾改行=無
OK  N1-novelty-search-result.md    37524  9e1dc1b7f9ad99faff469fa7aa001bfc586d98876677c52c2c1c1dcd83cfa3cd  末尾改行=無
OK  expected-ids.txt                5231  df76bfcb0e995bb70d68cba7dbff0d644e950ecef040a0036a92f7084451b486  末尾改行=有
表に無いファイル: []
不一致: 0
```

元の報告五件は末尾改行なし（SPEC の記載どおり）。触る前（2026-10-19 01:2x）に控えた値とも同じ。

### A-3 既存の照合の道具（異質な二つの方法）

1. **経路名での検索**: `git ls-files --cached --others` と `find`（`.venv*`・`.git`・`data` を除く）で `verif|crossref|arxiv|datacite|evidence|bibl|citation|doi` を探した。`tools/` に該当なし。当たったのは `docs/evidence/`、`./evidence/`（事故の記録。照合とは無関係）、各契約の `EVIDENCE.md`、`scripts/write_stage1_dtower_evidence.py`（stage1 の証拠の書き出し）など
2. **API の URL の文字列での検索**: `git grep -E 'api\.crossref\.org|export\.arxiv\.org|arxiv\.org/api|api\.datacite\.org|doi\.org/ra'`（`docs/archive` を除く）→ 3 ファイル。`docs/evidence/2026-09-16-*.md` の二件（照合の手段の記述）と `tasks/T-2026-09-16-evidence-map-ab/audit.md`（問い合わせの記録）。**コードは零件**

判断: 再利用できる照合器は無い。新しく書く。前回の照合器は UA に連絡先を入れていた（前回 audit.md:13）。本契約では決定 4 により入れない。

### A-4 照合先への到達（2026-10-19 02:1x、UA `egosurgery-evidence-verify/1.0`、連絡先なし、問い合わせの間 3.1 秒）

```
HTTP 200  8024B   0.68s  https://api.crossref.org/works/10.1109/TMI.2016.2593957
    {'x-rate-limit-limit': '5', 'x-rate-limit-interval': '1s', 'x-concurrency-limit': '1'}
HTTP 200  139B    0.11s  https://doi.org/doiRA/10.1109/TMI.2016.2593957,10.5281/zenodo.20086606
    [{"DOI": "10.1109/TMI.2016.2593957", "RA": "Crossref"}, {"DOI": "10.5281/zenodo.20086606", "RA": "DataCite"}]
HTTP 200  403B    0.12s  https://doi.org/api/handles/10.5281/zenodo.20086606   → {"responseCode":1, ...}
HTTP 200  12196B  1.26s  https://api.datacite.org/dois/10.5281/zenodo.20086606
HTTP 200  3170B   0.30s  https://export.arxiv.org/api/query?id_list=1602.03012
```

四系統（Crossref、DOI の登録機関の解決 doi.org、DataCite、arXiv の API）すべてに到達した。

各サービスの作法（文書を読んで確かめた。CLAUDE.md の `ctxpack` はこのホストに無いため WebFetch で読んだ）:

| 照合先 | 文書 | 作法 |
|---|---|---|
| Crossref | crossref.org の REST API「Access and authentication」「Tips for using」 | 公開の枠 5 件・同時 1 本（間隔は `x-rate-limit-interval`、実測 1s）。429 で後退。同じ問い合わせを繰り返さない。mailto は推奨だが決定 4 により入れない |
| arXiv | info.arxiv.org/help/api/tou.html | 「make no more than one request every three seconds, and limit requests to a single connection at a time」 |
| DataCite | support.datacite.org の rate limit の頁 | IP ごとに 5 分で 3000 件。失敗時は段階的に後退 |
| doi.org | doi.org の「DOI resolution documentation」 | `/api/handles/<DOI>`（responseCode 1=在る、100=無い）、`/doiRA/<DOI>`（登録機関、複数はカンマ区切り）。上限の記載なし |

### A-5 変更前の値

- 旧地図: `2026-09-16-A-phase-tower-candidates.md` 14167 B `9f723e4b17825b0854930b9a31c92fbf26cb298c20c0d4f133ff8883dfacddf0`、`2026-09-16-B-p2d-interface.md` 11981 B `02dda515179d0f1a669c9f562020f5df7a011b5e20bcbb6bdd5419c2844b3eaf`。**SPEC の表と一致**
- 全契約の `make task-validate`: 147 task(s), 0 failed（exit 0）。契約ごとの成否は 147 件すべて `OK`。WARN は L2-6（conventions.md の版差）と L2-8（分母の件数の移動）のみ
- `CUDA_VISIBLE_DEVICES= make test`: **収集の誤りで中断**（exit 2）。`tests/test_stage1_dtower_convergence.py` が `third_party/Relation-DETR/util/convergence.py` を読めない（`third_party/` は `.gitignore:134` で無視され、このホストの写しにはそのファイルが無い）。**試験は一件も実行されていない**
- そこで同じ引数に `--continue-on-collection-errors` を足して測った（逸脱。RESULT に記載）: **7 failed, 792 passed, 1 error**（58.29s）。失敗の集合（8 件）:

```
ERROR tests/test_stage1_dtower_convergence.py
FAILED tests/test_check_spec.py::test_teacher_detection_rate
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
```

`test_rejects_unknown_file_name` は `../../etc/passwd` を正しく拒むが、文言が「経路として受け取れない名前です」で、試験の期待「受け取れないファイル」と合わない（変更前から）。本契約では直さない。

- 変更前の schema で、形の正しい宣言 `inputs.bundle_extras: [{path: expected-ids.txt, sha256: df76bf…, bytes: 5231}]` を本契約の spec に足して `validate_l1` にかけた:

```
extras_from_spec: {'expected-ids.txt': {'sha256': 'df76bfcb…b486', 'bytes': 5231}}
変更前 L1: [L1-1] inputs: Additional properties are not allowed ('bundle_extras' was unexpected)
宣言なし L1: []
```

起票者の実測（環境の罠の一）を再現した。

### G1

**pass**。照合先の四系統に到達し、受け渡しの十件が SPEC の表の要約値・バイト数と一致した。

## B. 道具（Phase B）

### B.0 決めた手段と理由（SPEC「各 Task の手段は実装を読んで決めてよい。決めた手段と理由は audit.md に残す」）

| 項目 | 決めた手段 | 理由 |
|---|---|---|
| 照合器の置き場と名前 | `tools/verify_evidence_ids.py`。`make evidence-verify MAP=<地図>` を足した | `tools/verify_*.py`（verify_harvest・verify_runindex）の並びに合わせた。make 経由は終了コードが 2 に潰れるため、README に直接の実行も書いた |
| 様式の検査の置き場と名前 | `tools/check_evidence_map.py`。`make evidence-check [MAP=...]` | `tools/check_*.py` の並び。禁止語は `check_proposal.forbidden_words` / `check_forbidden` を使い、写しを持たない |
| DOI の実在 | doi.org の handle（responseCode 1/100）を正とし、登録機関は `doiRA`、書誌は登録機関の API | 環境の罠の三。Crossref だけだと DataCite の DOI を不在と誤る。handle は登録機関によらない |
| arXiv | `export.arxiv.org/api/query?id_list=` に一つの地図の ID をまとめて一回 | 3 秒に 1 回の作法。問い合わせの数を最小にする |
| 不在と到達不能 | 照合先が「無い」と答えた場合だけ不在。接続できない・429/5xx が続く・想定外の応答は到達不能 | 完了判定 b。両者を混ぜると「届かないものを不在と呼ぶ」壊れ方になる |
| 地図の側の書誌 | `ID`・`文献`・書誌 ID の列を持つ表で、ID が書誌 ID の列にある最初の行 | 地図 C の C-12 の出所の欄に別の論文（2511.06549）が書かれている。行全体から拾うとその行の書誌と誤って比べる。地図 N §8 は書誌 ID の列を持たない |
| 正規化 | NFKD で発音記号を外し casefold、英数字以外を除く。両側に同じ関数 | 環境の罠の四（Abu Farha・Lüddecke の誤検出の再発を防ぐ） |
| 題名の一致 | 全体（照合先の題名を地図の題名が含む）と部分（地図の題名 4 文字以上が照合先の題名に含まれる）を一致とし、どちらかを結果に残す | 地図は略称（PAD-Net、TeCNO など）で書く行がある。略称は誤りではない。区別は結果の `title.detail` で読める |
| 著者の一致 | 「ほか」ありは先頭から同じ位置、なしは両方向で全員が当たること | 地図が著者を省いたことを差として拾う（地図に「ほか」が無いのに一部しか書いていない行） |
| 掲載先 | 比べず、照合先と地図の値を並べて残す | B-1「掲載先の違いは分類に入れず、参考として別の欄に記録する」 |
| 抽出の規則 | 起票者の規則（expected-ids.txt の注記）に、arXiv の前後の境界と DOI の範囲の除外を足した | 境界が無いと DOI の内側の数字列（`2016.25939`・`7701.2024` など 9 件）を arXiv ID と誤る。**起票者の一覧に合わせて調整したものではない**（D-2 で集合を比べる） |
| User-Agent | `egosurgery-evidence-verify/1.0`（連絡先なし） | 決定 4 |
| 試験のネットワーク | 照合器の試験は `urllib.request.urlopen` を塞ぐ autouse の仕掛けを持ち、HTTP は差し替えの関数で返す | 完了判定 h。差し替え忘れがあれば試験が落ちる |

schema（B-3）: `inputs.properties.bundle_extras` を足した。経路の正規表現は `fetch_task._EXTRA_PATH_RE` と同じ式を JSON Schema の終端の流儀（`(?![\s\S])`）で書き、既定の三種（spec.yaml・SPEC.md・prereg.md）を `not.enum` で拒む。sha256 は 64 桁の小文字十六進、bytes は非負整数。項目の追加の鍵は拒まない（`extras_from_spec` が拒まないため）。

**取り込みの側との差（観察。直していない）:** `extras_from_spec` は `bytes: true` を通す（Python では `isinstance(True, int)` が真）。schema は `True is not of type 'integer'` で落とす。schema の側が厳しい向きの差で、この宣言は取り込みのあと検証で巻き戻る。同じ経路の二度の宣言は JSON Schema で表せないため、`extras_from_spec` だけが拒む。

### B.1 arXiv の 429 の実測（2026-10-19 JST）

| 時刻 | 問い合わせ（id_list） | 応答 |
|---|---|---|
| 02:07 | 1602.03012 | 200（到達の確認。この応答は手前のキャッシュに残った） |
| 02:18 | 2601.99999 → 3.1 秒後 1602.03012,2601.99999 | 429 `Rate exceeded.` ×2（`Retry-After` なし） |
| 02:19 | 1602.03012,2601.99999（60 秒あけた） | 429 |
| 02:23 | 1602.03012,2601.99999（4 分あけた） | 429 |
| 02:24 | 1602.03012（30 秒あけた） | 200。ただし `X-Cache: …HIT`・`Age: 1048`（キャッシュの応答で、本体には届いていない） |
| 02:35 | 2405.19644（10 分あけた） | 200、`X-Cache: MISS` |
| 02:35 | 2601.99999（20 秒あけた） | 200、`totalResults` 0、entry なし |
| 02:36 | 1709.07871（20 秒あけた） | 200、`X-Cache: MISS`、FiLM の entry |

- 「架空の ID を含む問い合わせに 429 を返す」仮説は**否定された**（02:35 の架空だけの問い合わせが 200）。429 は数分続く間隔の制限と読む
- この台に arXiv へ問い合わせる他のプロセスは無かった（`ps`）。同じ出口の IP を使う他の台の影響かは**確かめていない**
- これを受けて 429・5xx の待ちを 10・30・60・120 秒から 10・30・60・120・300・600 秒へ延ばした（尽きるまで最長 約 18.7 分）
- arXiv の不在の形を実測した: **HTTP 200 で `totalResults` 0、entry なし**。照合器はこれを不在とする（feed に該当の entry が無い）

### B.2 対照（G2）

#### 照合器 — 実際の照合先（対照の地図は scratchpad。結果も scratchpad に書き、repo に置いていない）

DOI の対照（`control-doi.md`、問い合わせ 7 件: doi 200・doi 200・crossref 200・doi 200・doi 200・datacite 200・doi 404）:

| 対照 | ID | 分類 | 登録機関 | 期待 |
|---|---|---|---|---|
| 実在の Crossref 登録 DOI | 10.1109/TMI.2016.2593957 | 実在・書誌一致（題名 全体、著者 先頭 1 名〔ほか〕） | Crossref | 実在 ✓ |
| 実在の DataCite 登録 DOI | 10.5281/zenodo.20086606 | 実在・書誌に差（題名は全体一致。著者が地図 1 名・照合先 6 名） | DataCite | 不在にならない ✓ |
| 架空の DOI | 10.1109/egosurgery.nonexistent.2026 | 不在（handle が responseCode 100） | — | 不在 ✓ |

照合器の終了コード 1（不在が一件）。DataCite の DOI の「書誌に差」は、対照の行を地図 N の N-01 と同じく著者 1 名（Graham Schwarz）で書いたため。照合先の creators は 6 名で Graham Schwarz は最後。照合器の誤りではない。

arXiv の対照（`control-arxiv.md`、問い合わせ 1 件: `id_list=1602.03012,2405.19644,2601.99999&max_results=3` → 200）:

| 対照 | ID | 分類 | 期待 |
|---|---|---|---|
| 実在の arXiv ID | 1602.03012 | 実在・書誌一致（題名 全体、著者 先頭 1 名〔ほか〕） | 実在 ✓ |
| 実在の arXiv ID | 2405.19644 | 実在・書誌一致（題名 全体、著者 全 4 名） | 実在 ✓ |
| 架空の arXiv ID | 2601.99999 | 不在（応答の feed に entry が無い） | 不在 ✓ |

#### 照合器 — 到達できない照合先

`--endpoint doi=http://127.0.0.1:9`（DOI の三件）と `--endpoint arxiv=http://127.0.0.1:9`（arXiv の三件）。どちらも **到達不能 3 / 不在 0**、終了コード 3。DOI の側は `URLError: <urlopen error [Errno 111] Connection refused>`、5 秒待って一度引き直してから到達不能（17.1 秒）。

#### 照合器 — 差し替えた HTTP（`tests/test_verify_evidence_ids.py`、ネットワークを塞いだ状態）

`test_controls_exist_absent_and_registry`（Crossref・DataCite・arXiv が実在、架空の DOI・arXiv が不在）、`test_unreachable_is_not_absent`、`test_persistent_429_becomes_unreachable_after_backing_off`、`test_adding_a_fake_id_adds_exactly_one_absent` が通る。実際の照合先と差し替えの**両方**で五つの対照が期待どおり（完了判定 b の空振りの確認）。

#### 様式の検査（地図 C の写しに一種ずつ。reports は受け渡しの五件の写し）

| 写し | 入れた違反 | 検出 | 終了コード |
|---|---|---|---|
| 0-clean | なし | 0 件 | 0 |
| 1-citation | §0.1 に `citeturn1view1` | `citation_residue` 1 件（L19 `turn1view1`） | 1 |
| 2-section | `## 7. 実装` の見出しを削除 | `missing_section` 1 件（「実装」） | 1 |
| 3-forbidden | §0.1 に「有望」 | `forbidden_word` 1 件（L19） | 1 |
| 4-sha256 | C2 の sha256 の末尾を d→e | `report_sha256` 1 件（L7、reports/ に一致なし） | 1 |

**私の命令の誤り（記録）**: 最初は `echo "$(basename $f) exit=$?"` で終了コードを表示し、5 件とも 0 と出た。`$?` が `$(basename …)` の後に評価されるためで、検査器の値ではない（`--json` で単独に見ると 1）。終了コードを直後に変数へ取る形で取り直したのが上の表である。

受け渡しの地図 3 件の原本は 0 件（`--reports-dir` は受け渡しの五件の写し）。雛形と旧地図 2 件は「対象外」と表示された。

#### 様式の検査 — 雛形との食い違い

雛形の試験 4 件（`test_template_*`）を、受け渡しの雛形（`evidence-template.md`、置き場の写しと同じ sha256 `69e95ea3…`）に向けて回し、4 件とも通った。repo の試験は `docs/evidence/_template.md` を読むため、Phase C の配置までは FileNotFoundError で落ちる（想定どおり）。

#### schema

変更前（A-5）: 形の正しい宣言が `[L1-1] inputs: Additional properties are not allowed ('bundle_extras' was unexpected)`。変更後:

```
正しい宣言                  -> 通る
sha256 が 63 桁            -> 落ちる [L1-1] … does not match '^[0-9a-f]{64}(?![\s\S])'
sha256 が大文字            -> 落ちる [L1-1]
sha256 の末尾に改行        -> 落ちる [L1-1]
path が ../ で脱出          -> 落ちる [L1-1] … does not match '^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*(?![\s\S])'
path が絶対                -> 落ちる [L1-1]
path が spec.yaml          -> 落ちる [L1-1] … should not be valid under {'enum': ['spec.yaml', 'SPEC.md', 'prereg.md']}
bytes が負                 -> 落ちる [L1-1]
bytes が真偽値             -> 落ちる [L1-1] True is not of type 'integer'
path が欠ける              -> 落ちる [L1-1] 'path' is a required property
```

取り込みを通した端から端まで（`tests/test_bundle_extras_schema.py`）: 宣言つきのバンドルが `fetch()` で取り込まれ、L1 の検査（同じ schema）を通り、追加ファイルの要約値が宣言どおり（`test_declared_bundle_is_installed_and_validates`）。要約値を改変したバンドルは「追加ファイルの要約値が宣言と一致しません」で拒まれ、何も残らない（`test_tampered_bundle_is_rejected_and_leaves_nothing`）。経路の規則は 12 の標本で `_EXTRA_PATH_RE` と一致した。

#### 新しい試験の結果（Phase B の終わり）

`pytest tests/test_verify_evidence_ids.py tests/test_check_evidence_map.py tests/test_bundle_extras_schema.py`: **72 passed, 4 failed**（失敗は雛形の 4 件で、上のとおり配置待ち）。`ruff check` は 5 ファイルとも通過。

### G2

**pass**。照合器（実際の照合先と差し替えの両方で五つの対照）、様式の検査（零件と四種の一件ずつ、雛形との一致）、schema（正しい宣言が通り、壊れた宣言が落ちる、端から端まで）が期待どおり。

## C. 配置（Phase C）

### C-1 十件の配置

`~/slocal2/m2-incoming/T-2026-10-18-evidence-verify-place/` から `cp -p` で写した（**移していない**。置き場の十件は残っている）。
写す前に置き場に同名のファイルが無いことを確かめた（`docs/evidence/reports/` と `verification/` も無かった）。
**配置後のファイルから**要約値とバイト数を計算し、SPEC の表と比べた:

```
OK  docs/evidence/2026-10-18-C-d2p-interface.md 71540 05a982ef4c8a9372a3855414393714c15cbb2cebabbbc6a07855eef22a5dc563
OK  docs/evidence/2026-10-18-B-p2d-interface.md 65725 1ab24a3cbfaba4f7b654c8fcd12a9deb9f9556c337b95392d10897011ee9ccca
OK  docs/evidence/2026-10-18-N-novelty.md 31607 9bb804b2eacdaac8842e2fc952d70479e747c9657186909ea9740b9e0413e6c8
OK  docs/evidence/_template.md 4474 69e95ea37106fac90b463eabde7879cfc60df1575ffabdd10223f1c9f5b61376
OK  docs/evidence/reports/deep-research-report-C2.md 72966 5d3c3ed514551cf11d1b75dcc8b6542b7fb5efefeedb91956a5d561284c141fd
OK  docs/evidence/reports/deep-research-report-B2.md 72035 c7aad1c222d9159c1209a557f765e0400f85a3b6ccd8d92025683a2ce8102116
OK  docs/evidence/reports/R1-deep-research-report.md 40202 1f95517bf4ce63015d9574ee7e3616859021882a7014feb4f261d76d9c49dce5
OK  docs/evidence/reports/B-chatgpt.md 38349 ef94ea71aba1b5e81dea60ae0b55581dfdfda7cf290fe29d56dcb20b7bc33dd9
OK  docs/evidence/reports/N1-novelty-search-result.md 37524 9e1dc1b7f9ad99faff469fa7aa001bfc586d98876677c52c2c1c1dcd83cfa3cd
OK  tasks/T-2026-10-18-evidence-verify-place/expected-ids.txt 5231 df76bfcb0e995bb70d68cba7dbff0d644e950ecef040a0036a92f7084451b486
配置後の不一致: 0
```

版管理の側: `git check-ignore` は十件とも無視されない（exit 1）。`git check-attr -a` は何も返さない（改行の正規化の属性なし）。CR は十件とも 0 件。

### C-2・C-3 旧地図

- 旧地図 B: 表題の行（1 行目）の直後に、空行と SPEC の一文を挿入した。`git diff --numstat` = **追加 2 / 削除 0**。挿入した行は SPEC.md:112 の一文と `grep -F` で一字一句一致
- 旧地図 A: 無変更。sha256 `9f723e4b17825b0854930b9a31c92fbf26cb298c20c0d4f133ff8883dfacddf0`（A-5 と一致）

### C-4・C-5 README と命令の実行

`docs/evidence/README.md`（125 行）を置いた。中身は C-4 の六項目（置き場の構成／命名の規則／照合と様式の検査の命令と結果の読み方〔五つの分類・書誌一致の判定規則〕／v1 の扱い／元の報告は手を加えない／起票者用の文書を置かない）。
README に書いた命令を実行した終了コード:

| 命令 | 終了コード | 出力の要点 |
|---|---|---|
| `make evidence-check` | 0 | 地図 3 件 違反 0。対象外 9 件（旧地図 2、README、雛形、報告 5） |
| `make evidence-check MAP=docs/evidence/2026-10-18-N-novelty.md` | 0 | 違反 0 |
| `.venv/bin/python tools/check_evidence_map.py docs/evidence/2026-10-18-C-d2p-interface.md docs/evidence/2026-10-18-B-p2d-interface.md` | 0 | 違反 0・0 |
| `.venv/bin/python tools/verify_evidence_ids.py --extract-only docs/evidence/2026-10-18-N-novelty.md` | 0 | 36 行 |
| `make evidence-verify MAP=docs/evidence/2026-10-18-C-d2p-interface.md` | D-1 に記録 | |
| `.venv/bin/python tools/verify_evidence_ids.py docs/evidence/<地図>.md`（B・N） | D-1 に記録 | |

雛形の試験 4 件は、配置後の `docs/evidence/_template.md` で通った（`tests/test_check_evidence_map.py` 16 passed）。

## D. 照合（Phase D）

### D-2 抽出した ID の集合と起票者の一覧（配置後の地図で）

`--extract-only` の出力（99 行）と `tasks/T-2026-10-18-evidence-verify-place/expected-ids.txt`（注記を除く 99 行）を、地図ごとに (種別, ID) の集合で比べた（DOI は小文字にして比べた）:

```
2026-10-18-C-d2p-interface.md: 抽出 29（doi 9, arxiv 20）/ 一覧 29 / 抽出のみ [] / 一覧のみ []
2026-10-18-B-p2d-interface.md: 抽出 34（doi 4, arxiv 30）/ 一覧 34 / 抽出のみ [] / 一覧のみ []
2026-10-18-N-novelty.md: 抽出 36（doi 7, arxiv 29）/ 一覧 36 / 抽出のみ [] / 一覧のみ []
大文字小文字まで含めた差: []
```

**差は零件**。照合器の抽出の規則は起票者の一覧に合わせて調整していない（B.0 の抽出の規則。境界の条件は DOI の内側の数字列を拾わないためのもので、落とした数字列は地図 C で 5 件・N で 4 件、すべて DOI の部分列）。

### D-1 三つの地図の照合（2026-10-19 02:39:53〜02:40:33 JST、bengio）

```
=== make evidence-verify MAP=docs/evidence/2026-10-18-C-d2p-interface.md
実在・書誌一致 27 / 実在・書誌に差 1 / 実在・照合不能 1 / 不在 0 / 到達不能 0（計 29）
exit=0
=== .venv/bin/python tools/verify_evidence_ids.py docs/evidence/2026-10-18-B-p2d-interface.md
実在・書誌一致 29 / 実在・書誌に差 5 / 実在・照合不能 0 / 不在 0 / 到達不能 0（計 34）
exit=0
=== .venv/bin/python tools/verify_evidence_ids.py docs/evidence/2026-10-18-N-novelty.md
実在・書誌一致 16 / 実在・書誌に差 2 / 実在・照合不能 18 / 不在 0 / 到達不能 0（計 36）
exit=0
```

（C-5 の照合の命令の終了コードはこの表のとおり。make の形も直接の形も 0）

| 地図 | 地図の sha256（照合の時） | 問い合わせ（照合先, HTTP: 件数） | 分類の件数の和 = 抽出した ID | 書誌 ID の無い行 |
|---|---|---|---|---|
| C | 05a982ef4c8a… | doi 200: 18、crossref 200: 9、arxiv 200: 1 | 29 = 29（DOI 9、arXiv 20） | C-24 |
| B | 1ab24a3cbfab… | doi 200: 8、crossref 200: 4、arxiv 200: 1 | 34 = 34（DOI 4、arXiv 30） | B-18 |
| N | 9bb804b2eacd… | doi 200: 14、crossref 200: 6、datacite 200: 1、arxiv 200: 1 | 36 = 36（DOI 7、arXiv 29） | N-15 |

結果は `docs/evidence/verification/2026-10-18-{C-d2p-interface,B-p2d-interface,N-novelty}.{json,md}`。全問い合わせが 200 で、429 は出なかった。

#### 差と照合不能の一件ずつの点検（照合器の誤りかどうか）

照合器の誤り（抽出・正規化・行の取り違え）は**見つからなかった**。いずれも規則どおりの判定で、理由は次のとおり。

| 地図 | ID | 行 | 分類 | 理由（地図の記載 → 照合先） |
|---|---|---|---|---|
| C | 2410.20026 | C-21 | 差 | 題名の語が違う。「…via Digital Twin-based Scene Representation」→ arXiv「…via Digital Twin Representation」。著者（Ding ほか）は一致 |
| C | 2511.06549 | — | 照合不能 | C-12 の出所の欄にだけ現れる別の論文（PhaKIR のデータセットの論文）。書誌 ID の列に無い |
| B | 1610.08851 | B-02 | 差 | 題名の欄が「M2CAI 技術報告」（説明）。照合先は「Single- and Multi-Task Architectures for Tool Presence Detection Challenge at M2CAI 2016」。著者一致 |
| B | 1610.08844 | B-02 | 差 | B-02 の書誌 ID の欄に「N1 は 1610.08844 と書く」とある。題名の欄は同じく説明。照合先は「…for Surgical Workflow Challenge at M2CAI 2016」。著者一致 |
| B | 1907.06099 | B-03 | 差 | 題名の欄が略称「MTRCNet-CL」。照合先の題名に含まれない。著者 7 名一致 |
| B | 2112.10003 | B-06 | 差 | 題名の欄が略称「CLIPSeg」。照合先「Image Segmentation Using Text and Image Prompts」。著者（Lüddecke, Ecker）一致（**発音記号の正規化は働いた**） |
| B | 1907.06390 | B-10 | 差 | 題名の欄が略称「SELSA」。照合先「Sequence Level Semantics Aggregation for Video Object Detection」。著者 4 名一致 |
| N | 10.5281/zenodo.20086606 | N-01 | 差 | 題名は全体一致。著者が地図 1 名（Graham Schwarz、「ほか」なし）・照合先 6 名（Graham Schwarz は 6 番目） |
| N | 2501.11153 | N-10 | 差 | 題名の欄が略称「KAFR」。照合先「Efficient Frame Extraction: A Novel Approach Through Frame Similarity and Surgical Tool Tracking for Video Segmentation」。著者（Nguyen ほか）一致 |
| N | 1708.00666 | N-18 | 照合不能 | 文献の欄が「TD-Graph LSTM（題名・著者は報告に無い）」で、題名も著者も無い |
| N | ほか 17 件 | — | 照合不能 | §3〜§8 の表（書誌 ID の列を持たない）か本文にだけ現れる: 10.1109/TMI.2016.2593957、2406.03095、10.3390/data10010007、1602.03012、2411.16794、1907.06099、2305.13961、2107.04810、2512.14712、2503.18755、2405.19644、2511.06549、2109.14956、2507.16559、1610.08851、1610.08844、10.1016/j.media.2024.103366 |

**規則を結果に合わせて変えなかった。** 略称の行（B-03・B-06・B-10・N-10）と説明の行（B-02）は、著者が一致しても題名の欄が照合先の題名に含まれないため「差」になる。題名の欄に照合先の題名が書かれていないことは書誌の欠けとして起票者に見えるべきだと判断し、略称を一致とみなす規則は足していない。
README の判定規則（地図の題名 4 文字以上が照合先の題名に含まれれば部分一致）は、略称が題名の中に現れる場合（例 TeCNO、PAD-Net）だけを一致にする。

#### 地図 N の 2512.14712

本文 L114 に現れる arXiv 2512.14712 は、照合先の題名が「SepsisSuite: Beyond Risk Stratification -- A Comparative Analysis of Deep Fusion vs. Expert Stacking for Prescriptive Sepsis AI」（著者 Ryan Cartularo）で、手術映像の文献ではない。地図の L114 は §4 の表の行で「別分野（敗血症、N が 1 万未満）の報告」と書いており、**照合先の題名と食い違わない**。書誌 ID の列を持つ表の行が無いため照合不能に分類した。

### D-1 の対照（完了判定 a の空振りの確認）

地図 B の写しの末尾に「対照のために足した架空の ID: arXiv 2601.99999」を足して照合した（02:42、結果は scratchpad）:

```
写し: {'実在・書誌一致': 29, '実在・書誌に差': 5, '実在・照合不能': 0, '不在': 1, '到達不能': 0} 35
本番: {'実在・書誌一致': 29, '実在・書誌に差': 5, '実在・照合不能': 0, '不在': 0, '到達不能': 0} 34
分類の差: 不在 +1、ほか 0
ID ごとに変わったもの: {'2601.99999': (None, '不在')}
```

終了コード 1。

### D-3 様式の検査

C-5 の `make evidence-check` のとおり、三つの地図とも**違反 0 件**（exit 0）。地図は直していない。

### G3

**pass**。抽出した ID の集合が三つの地図とも起票者の一覧と一致した（D-2、差 0 件）。

## E. 検証（Phase E）

### E-1

- `CUDA_VISIBLE_DEVICES= make test`: 変更前と同じく収集の誤りで中断（exit 2、`ERROR tests/test_stage1_dtower_convergence.py` の 1 件だけ）
- `CUDA_VISIBLE_DEVICES= pytest tests/ -v --cov=src/egosurgery --continue-on-collection-errors`: **7 failed, 868 passed, 22 warnings, 1 error**（81.60s）。
  変更前は 7 failed, 792 passed, 1 error。失敗の集合（8 件）を試験名で `diff` して**空**（A-5 の一覧と同一）。増えた 76 件は新しい三つの試験ファイルの PASSED の数（`grep -c` = 76）と一致
- `make task-validate`（全契約）: **147 task(s), 0 failed**（exit 0）。契約ごとの成否（`OK <task_id>`）の集合を変更前と `diff` して空。WARN の行の集合も同一
- `make forbidden-check`: `"status": "pass"`、changed 29・checked 29・violations []（exit 0）。29 件には未追跡の `.coverage` を含む
- `make spec-check TASK=T-2026-10-18-evidence-verify-place`: hits 0、status pass（exit 0）
- `make spec-check`（SPEC の字面どおり TASK なし）: targets 147、hits 210（forbidden_vs_output 18、gate_requires_report_before_end 4、host_mismatch 74、integration_prohibited_without_pause 19、reverify_contradiction 1、separated_source 78、truncation_in_measurement 6、unquoted_glob 10）で **exit 2**。本契約の該当は 0 件

### E-2

- 旧地図 A: sha256 `9f723e4b17825b0854930b9a31c92fbf26cb298c20c0d4f133ff8883dfacddf0`（A-5 と一致）
- 旧地図 B: `git diff --numstat` = 追加 2・削除 0。変更後の sha256 `5aab3910cd8e4c04f77f795b8fc3d3930f0751e2a810da541568b53f6bbbad2d`
- 地図三件・雛形・報告五件・一覧の sha256 は照合と検査の後も SPEC の表のまま（完了判定 i の書き換えていない証拠）
- 追跡下の変更は 4 ファイル（Makefile・README.md・旧地図 B・`tasks/_schema/spec.schema.json`）で、追加 67・削除 0

### 陽性対照の追加の実測

- 通信の口を塞ぐ仕掛け（試験の autouse と同じ関数）の下で `Client().get("doi", …)` を呼ぶと `AssertionError: 試験がネットワークへ出ようとした` で止まった
- `unshare -rn true` → `unshare: unshare failed: Operation not permitted`。ネットワークを断った名前空間での実行は取れなかった
- 雛形の写しから「／未検証の組み合わせ」を消して `test_template_required_sections_match_checker` を回すと AssertionError で落ちた（雛形と検査器の食い違いを試験が捕まえる）

### 変更範囲の一覧

| 種類 | 経路 |
|---|---|
| 新規（道具） | `tools/verify_evidence_ids.py`、`tools/check_evidence_map.py` |
| 新規（試験） | `tests/test_verify_evidence_ids.py`、`tests/test_check_evidence_map.py`、`tests/test_bundle_extras_schema.py` |
| 新規（文書） | `docs/evidence/README.md`、`docs/evidence/_template.md`、`docs/evidence/2026-10-18-{C-d2p-interface,B-p2d-interface,N-novelty}.md`、`docs/evidence/reports/` の 5 件 |
| 新規（結果） | `docs/evidence/verification/2026-10-18-{C-d2p-interface,B-p2d-interface,N-novelty}.{json,md}` |
| 新規（契約） | `tasks/T-2026-10-18-evidence-verify-place/`（spec.yaml・SPEC.md・expected-ids.txt・RESULT.md・result.yaml・audit.md）、`tasks/inbox.d/T-2026-10-18-evidence-verify-place.md` |
| 変更（追加のみ） | `Makefile`（evidence-verify・evidence-check）、`tasks/_schema/spec.schema.json`（bundle_extras）、`docs/evidence/2026-09-16-B-p2d-interface.md`（v1 の一文）、`README.md`（本契約の節） |
| 変更（契約） | `tasks/T-2026-10-18-evidence-verify-place/spec.yaml`（amendment の追記と decisions_required を空に） |
| repo の外 | `.git/info/exclude`（3 行と注記。控え `~/m2-git-info-exclude.bak-20261019`） |

## F. 送出

- PR: #231（`gh pr view`: state OPEN、isDraft false、base phase0、head feat/evidence-verify-place）
- `source scripts/load_env.sh && make task-report TASK=T-2026-10-18-evidence-verify-place`（2026-10-19 02:5x JST、commit `13db8643` の報告を送った）の台帳の応答:

```
{
  "task_id": "T-2026-10-18-evidence-verify-place",
  "verdict": "pass",
  "n_issuer_defects": 2,
  "report_sha256": "d91f0276f33498a38514ebb5398b2fe1e549df45cfd5d50d76ec1eb31b443068",
  "report_bytes": 11368,
  "replaced_blocks": 0
}
exit=0
```
