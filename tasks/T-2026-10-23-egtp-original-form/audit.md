# audit — T-2026-10-23-egtp-original-form

実行ホストは Bengio。時刻は JST。GPU を使う学習・実データ・外部への接続は使っていない（試験の 1 回目だけ GPU が見えていた。§A-2）。

## 0. 開始

- 開始時の分岐 `feat/evidence-map-a-revise`。`feat/egtp-original-form` は手元・遠隔とも無し、`tasks/T-2026-10-23-egtp-original-form` の履歴も無し、`.sync-pause` 無し。
- `git fetch origin && python3 scripts/task_start_classify.py`（比較先 origin/phase0 d013c5f1）→ 追跡下の変更 0、未追跡・起点に在り中身が同じ 3 件（`experiments/analysis/ptower_cand5_compute_probe/` の 3 件。通す）、ほか 0。`[task-start] 分類: 通す`。
- `make task-start` → `分岐を作成: feat/egtp-original-form（起点 origin/phase0）`、`[task-start] .sync-pause を作成`、`OK T-2026-10-23-egtp-original-form`、`[task-start] 完了。`。
- `make task-validate` → `OK`、exit 0。`make task-preflight` → `RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL`、exit 0（SKIP: P2・P3・P11 は plan.env.preflight に記載なし、P4・P5・P13・P14 は kind=impl、P12 は解決前提の参照なし）。
- 規約の版: spec の `conventions_rev` `ceb7ef0f88a3f30279930be96ab9a5722acc2f09` は commit ではなく blob だった（`git cat-file -t` → `blob`）。`git rev-parse HEAD:context/conventions.md` → `ceb7ef0f…` で、HEAD の規約そのものと一致する。検証器 L2-6（`tools/validate_task.py` `_warn_conventions_rev`）は `git diff --name-only ceb7ef0f..HEAD` を `check=False` で呼び、blob では git が失敗して標準出力が空になるため、警告を出さずに通る。

## A. 開始状態と基準値（G1）

- A-1: 分岐 `feat/egtp-original-form`、HEAD = origin/phase0 = `d013c5f14c47acd9778b1ff2a4a81e6e6fa2f5c0`。追跡下の変更 0（未追跡は本契約の SPEC.md・spec.yaml だけ）。G1: pass。
- A-2: 試験の失敗の集合。
  - 1 回目（GPU が見えていた）: `PYTHONPATH=src pytest tests/ -q --continue-on-collection-errors -rfE` → `11 failed, 946 passed, 27 warnings, 1 error`。ssm の GPU の試験と `test_two_epoch_smoke_leaves_no_checkpoint[ssm-cuda:0-extra4]` が GPU で走った。契約の「GPU を使わない」に反するため、以後は `CUDA_VISIBLE_DEVICES=""` で回し、1 回目は比較に使わない（記録は `fail-before-gpu-visible.txt`）。
  - 正とする回（`CUDA_VISIBLE_DEVICES=""`、15:56:28 に終了、編集の前）: `11 failed, 941 passed, 5 skipped, 26 warnings, 1 error`。失敗の名前の集合 12 件は [fail-before-cpu.txt](fail-before-cpu.txt)。1 回目と同じ集合だった。
  - 引数なしの `pytest tests/` は収集の段で止まる（`tests/test_stage1_dtower_convergence.py` が `third_party/Relation-DETR/util/convergence.py` を見つけられない）。このため `--continue-on-collection-errors` を付けた。
  - 変更前から落ちている `test_existing_candidates_match_baseline[linear|A|B|C]`: 試験の `output_digest` が bengio で返す値（linear `0235f4de…`、A・C `e4f2eed5…`、B `379cc43e…`）は、試験に書かれた `BASELINE`（linear `8b65f13b…`、A・C `a3cd6d08…`、B `0816c1e9…`）と違う。前の契約の基準値は別のホスト（andrew）で取られている。
- A-3: 前の契約の `BASELINE` は 4 候補だけで、bengio では一致しないため使えない。変更前に bengio で八候補の基準値を取った（台本 [baseline.py](baseline.py)、HEAD `d013c5f1`、`CUDA_VISIBLE_DEVICES=""`、4 CPU スレッド、パラメタ manual_seed(42)、入力 randn(1, 2048, 40) manual_seed(7)、既定の設定）。
  - 模型の出力（各段の要約値）: linear、A、B、C、memory、memory（memory_len 0）、progress、stabilize（base A・B・C、egtp 無し）の 10 通り
  - 復号: progress（transition_prior）の合成の折りでの出力の要約値、stabilize（egtp 無し）の規則の鍵が空であること
  - `scripts/stage1_ptower.py` の egtp 以外の最上位の定義ごとの `ast.dump` の sha256（関数 32、ほかの文 31）
  - ssm は CUDA が要る（`CUDA_VISIBLE_DEVICES=""` で `causal_conv1d_fwd` が `Expected x.is_cuda() to be true` で止まる）。GPU が禁じられているため出力は測っていない。関数単位のソースの一致で代える
  - 結果は [baseline-before.json](baseline-before.json)（sha256 `38c29fd31b340e522b89064ca288dde13ea80ff4dcfd885673b2d172b60b91a3`）

## B. 置き換え

`egtp` を `egtp_steps`（各時刻の (状態, E, n, σ, Z) を返す生成器）と、それを消費する `egtp` に分けた。`egtp(prob, k, starts=())` → `(prob, state)` の呼び口と `decoders` の接続は変えていない。原典が書いていない箇所の決め方:

| 箇所 | 決めた形 | 理由 |
|---|---|---|
| log の下限 | p を 1e-12 で下から切ってから float64 で log（`EGTP_P_FLOOR`） | softmax の 0 で発散させないため |
| n(c) | E(c) が最後に 0 だった後に積んだ δ(c) の個数。E(c) が 0 に切られたら 0 に戻す | SPEC §4 の例（累積が 0 に戻ってからの個数） |
| σ(c) | 同じ範囲の δ(c) の標本標準偏差（ddof 1、Welford の逐次） | Z が t 統計量の形（√n·平均/σ）になる |
| n < 2 | Z = 0（σ が定まらない） | 一つ目の証拠だけでは遷移しない |
| σ = 0 | σ を 1e-3 で下から切る（`EGTP_SIGMA_FLOOR`） | 一定の δ でも Z が有限のまま √n で増え、有限の時刻で遷移する |
| 遷移・starts・最初の時刻 | E・n・平均・σ をすべて 0 に戻す。状態の c は ŷ 自身を除く | SPEC §4 の 5 と 7 |

## C. 試験

- 書き直した・足した試験（`tests/test_stage1_ptower_heads.py`）: `test_egtp_keeps_probabilities_and_matches_the_hand_computed_evidence`、`test_egtp_restarts_the_statistics_after_a_switch`、`test_egtp_is_causal`、`test_egtp_threshold_holds_or_lets_the_state_move`、`test_egtp_starts_restart_from_argmax`。旧 `test_egtp_keeps_probabilities_and_holds_the_state` は置き換えた。
- 期待値の出し方: p1 = (0.4, 0.55, 0.6, 0.6, 0.8)、p0 = 1 − p1。状態は t=0 の argmax で 0。d1 = log(0.55/0.45)、d2 = d3 = log(0.6/0.4)。t=1: E = d1、n = 1、Z = 0。t=2: E = d1 + d2、σ = |d2 − d1|/√2 より Z = (d1 + d2)/(d2 − d1) = 2.9597。t=3: Z = (d1+d2+d3)/(√3·stdev(d1, d2, d3)) = 4.9396。k = 3 なら t=3 で遷移して [0, 0, 0, 1, 1]、k = 2.9 なら t=2 で遷移して [0, 0, 1, 1, 1]。試験はこれを `math.log` と `statistics.stdev` で書き、実装の値と 1e-12 で比べる。
- 実装の各時刻の値（k 3）: t1 E[1] 0.2006707・n 1・Z 0、t2 E[1] 0.6061358・n 2・Z 2.95972823、t3 遷移して E・n 0、Z 4.93959234。
- 初期化: p1 = (0.4, 0.55, 0.6, 0.6, 0.3)、k 2.9 → 状態 [0, 0, 1, 1, 1]。遷移の時刻 t=2 で E・n・σ がすべて 0、t=3 の class 0 は E 0・n 0、t=4 は E = log(0.7/0.3)・n 1（遷移前の累積は残らない）。
- k = 0 の対照: 一定の反証 p1 = (0.4, 0.6, 0.6, 0.6, 0.6) で k 0 → [0, 0, 1, 1, 1]（2 つ目の反証の t=2 で遷移。n < 2 の間は Z = 0 のため、最初の反証の t=1 では遷移しない）、k 5 → 同じ、k 1e9 → [0] × 5。
- 実装の途中で、n = 0 の位置の 0/0 で RuntimeWarning が出ていた（値は np.where で 0 になり結果は同じ）。分母の n に下限 1 を入れて、警告が出ない式にした。EGTP の試験は `-W error::RuntimeWarning` で 5 件とも通る。
- 遷移の時刻に返す σ が初期化の前の値だった。E・n と揃えて 0 を返すようにした（Z は遷移を起こした値を返す）。
- 変更後（最終の版）の基準値 [baseline-after.json](baseline-after.json): 模型の出力 10 通りと復号が変更前とビット一致（`models` と `decoders` の辞書が等しい）。関数の要約値は変更前の 32 件がすべて同じで、増えたのは `egtp_steps` だけ。ほかの文は変更前の 31 件がすべて残り、増えたのは 2 件（`EGTP_P_FLOOR` と `EGTP_SIGMA_FLOOR` の代入）。
- 試験の全件（`CUDA_VISIBLE_DEVICES=""`、最終の版）: `11 failed, 945 passed, 5 skipped, 26 warnings, 1 error`。失敗の名前の集合は [fail-after-cpu.txt](fail-after-cpu.txt) で、変更前の集合と `diff` で同じ（12 件）。通った数の 941 → 945 は、旧 EGTP の試験 1 件が 5 件になった分。
- ruff（`scripts/stage1_ptower.py`、`tests/test_stage1_ptower_heads.py`）: All checks passed。
- G2: pass（ssm の出力は測っていない。関数単位のソースの一致で代えた）。

### 陽性対照

| 判定 | 壊す入力 | 結果 |
|---|---|---|
| b 期待値 | repo の外の写しで、状態の期待 [0, 0, 0, 1, 1] を [0, 0, 1, 1, 1] に変える | 1 failed, 4 passed。変えない写しは 5 passed |
| b 期待値 | 写しで Z の期待に 1e-9 を足す | 1 failed, 4 passed |
| c 閾値 | k 0 と k 1e9 を同じ乱数の確率列に当てる（試験の中） | k 1e9 は状態が一つ、k 0 は複数 |
| d 不変 | A を `layers=7` で作る | 要約値 `4a386c8c…` が基準値 `e4f2eed5…` と一致しない |
| e 禁止領域 | repo の外の clone（`--base d013c5f1`）で `data/positive-control.txt` を足す | 足す前は `status pass`・exit 0、足した後は `status fail`・違反 `data/positive-control.txt（禁止領域 data/ の内側）`・exit 1。clone は消した |

## D. 検証

- `make forbidden-check` → `"status": "pass"`、`"changed": 5`、`"violations": []`、exit 0。
- `make spec-check TASK=T-2026-10-23-egtp-original-form` → `"status": "pass"`、`"hits": 0`。
- 依存: `git diff origin/phase0 -- pyproject.toml uv.lock requirements*.txt` は 0 行。追加の import は試験の標準ライブラリ `math` と `statistics` だけ。
- 追跡されるファイルの変更（commit 前）: `README.md`、`scripts/stage1_ptower.py`、`tests/test_stage1_ptower_heads.py`。ほかは `tasks/T-2026-10-23-egtp-original-form/` と `tasks/inbox.d/T-2026-10-23-egtp-original-form.md`。許される集合との差は 0。設定の既定値（`configs/stage1_ptower.yaml`）は変えていない。

## E. 送出
