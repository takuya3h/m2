# T-2026-10-23-ptower-cand5-heads-impl 監査記録

ホスト andrew（`hostname` = Andrew）、repo `~/slocal2/m2`。時刻は JST。

## A1. 開始状態（手順書「0. 始める」）

- 2026-10-23、A3 の時刻（12:33:47 JST）より前（開始の時刻そのものは取っていない）。開始前の分岐は `feat/ptower-cand5-compute-probe`。`feat/ptower-cand5-heads-impl` は手元にも遠隔にも無く、
  `tasks/T-2026-10-23-ptower-cand5-heads-impl` の履歴も無く、`.sync-pause` も無かった
- 分類器（`scripts/task_start_classify.py`、比較先 origin/phase0 ea73a8ba）: 追跡下の変更 0、未追跡 0、無視・中身違い 0 → `分類: 通す`
- task-start の表示（抜粋）:

      [task-start] 分岐を作成: feat/ptower-cand5-heads-impl（起点 origin/phase0）
      [task-start] .sync-pause を作成（報告まで終えたら make task-release TASK=T-2026-10-23-ptower-cand5-heads-impl END=complete）
      OK   T-2026-10-23-ptower-cand5-heads-impl
      [task-start] 完了。分岐 feat/ptower-cand5-heads-impl で契約 T-2026-10-23-ptower-cand5-heads-impl の作業を開始できます

  目印は**この契約が作成した**もの

## A2. 検証とプリフライト

- `make task-validate`: `OK   T-2026-10-23-ptower-cand5-heads-impl` / `1 task(s), 0 failed`、exit 0
- `make task-preflight`: `RESULT: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL`、exit 0
  - PASS: P1 venv_active、P6 decisions_answered、P7 destination_writable、P8 contract_valid、P9 spec_lint（規則 9 件、該当なし）、
    P10 preflight_names_known、P11 gpu_free（compute プロセス 0 件）
  - SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（plan.env.preflight に記載なし）、P4 prereg_committed・P5 frozen_source_hash・
    P13 symmetry_table_complete・P14 proposal_card_checked（kind=impl のため対象外）、P12 refs_resolved（解決前提の参照なし）

## A3. 装置・版（2026-10-23 12:33:47 JST）

    feat/ptower-cand5-heads-impl
    HEAD = origin/phase0 = merge-base = ea73a8bace86bbd29f1a2b045078cb7133807066
    git status --porcelain: 2 行（task-start が取り込んだ SPEC.md と spec.yaml の未追跡だけ）
    0, NVIDIA RTX A6000, 49140 MiB, 16 MiB, 595.84
    1, NVIDIA RTX A6000, 49140 MiB, 16 MiB, 595.84
    compute プロセス: 0 件
    torch 2.1.2+cu118 cuda True
    mamba_ssm 2.2.2 causal_conv1d 1.4.0 timm 1.0.27 numpy 1.26.4
    Mamba import ok
    uv.lock       69212cb0ca8895aff8376d4aca0f6e11840d2ca5270fc2b01da034227e87f3e3
    pyproject.toml 4da5dfe36a8ff5c02d5d92a87e4efa4974f9b65170a0bf7c2f2ec8212e04af15

GPU を使った段（SSM の測定、試験の全件 3 回）はすべて `CUDA_VISIBLE_DEVICES=0`、直前の compute プロセスは 0 件。

## A4. 試験の前の値（ea73a8ba、変更前）

    CUDA_VISIBLE_DEVICES=0 python -m pytest tests -q -p no:cacheprovider
    SKIPPED [1] tests/test_stage1_ptower_r3_dist.py:298: needs two GPUs
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    6 failed, 924 passed, 1 skipped, 22 warnings in 25.20s

## A5. 既存の四候補の基準値（変更前）

- 取った時点の HEAD は **ea73a8ba**（`git diff --stat HEAD -- scripts configs src` は空。scripts は未変更）。
  基準値の試験だけを置いた commit が **ed0fee7a**（`tests/test_stage1_ptower_heads.py` と契約の 2 件。scripts は含まない）
- 方法: `configs/stage1_ptower.yaml` の既定（layers 6、maps 64、history 30）、`manual_seed(42)` で模型を作り eval、
  `manual_seed(7)` の `randn(1, 2048, 40)` を入れ、最終段の出力の sha256。CPU 4 スレッド
- 二つの別プロセスで同じ値:

      linear 8b65f13bc2a8612518d2e1306a60e0d2ee6a268ee9ada980671a612785f845ae
      A      a3cd6d08cad21667036787b836f4c971fb9c958d60741f7d7e632d1584c1a00f
      B      0816c1e9f71cbafb15a5ac1c0f9aa353d9e0583f797316819ed6f8023dc2a243
      C      a3cd6d08cad21667036787b836f4c971fb9c958d60741f7d7e632d1584c1a00f   （A と同じ模型。C は損失だけが違う）
      layers7 636de74d35d4438afd2221f5686073352d14b8b668bc4a018dcef4b233361c08 （A の layers を 7 にした対照）

- G1: 分岐 feat/、起点 origin/phase0 = ea73a8ba、契約 2 件以外の汚れ 0、四候補の基準値あり → **pass**

## B. 列の情報と manifest の検算

変更前の読み取り（`data/processed/phase_manifest_all_phase` の 3 split、フレーム番号は `frame` の末尾の `_` の後の整数。
`build_phase_manifest.py` は CSV の `Frame` をそのまま `frame` に入れ、`<clip_id>_<番号>` の形）:

    frames 17233 clips 23 videos 15 pairs 17210 eq1 16663 96.82 max 254 min 1
    クリップ数/動画: 01:1 02:1 03:2 04:2 05:2 06:2 07:2 08:2 09:1 10:2 11:1 12:1 13:1 14:2 15:1

実装後の試験 `test_manifest_gaps_reproduce_the_eda`（`gap_summary` は load_fold と同じクリップの順で動画をつなぐ）:

    {"videos": 15, "clips": 23, "frames": 17233, "pairs": 17210, "delta_one": 16663, "delta_max": 254,
     "unknown": 23, "unknown_between_clips": 8}      → 16663 / 17210 = 96.8 %
    陰性対照: 動画 03 の 2 クリップを 1 本につないだ写し → unknown_between_clips = 7

不明（`GAP_UNKNOWN` = −1）はクリップの先頭 23 箇所（動画の先頭 15 と、クリップ間 8）。Δ の既知の値は 1〜254 で、−1 と重ならない。
`load_fold(cfg)` の既定の三つ組は不変（`test_load_fold_info_is_additive`: 既定と `info=True` で video・x・y が一致）。

## C. 実装（commit 1afc4ad1、502e6af7）

- `scripts/stage1_ptower.py`: `sequence_info`・`gap_summary`・`input_dim`・`model_input`・`run_video`、`SelectiveSSM`・`MemoryTeCNO`・
  `ProgressTeCNO`、`build_model` の分岐（`stabilize` は `base_candidate` の模型）、`progress_target`・`transition_matrix`・
  `transition_decode`・`tec_weights`・`tec_loss`・`egtp`、`evaluate` の復号の引数、`train` の損失と復号
- 既存の行の変更は 11 箇所で、どれも既存の候補では同じ値になる形（`load_fold` の任意の引数、`LinearFrame` と `AggregatedTeCNO` と
  A・C の入力次元を `input_dim(cfg)`（鍵が無ければ 2048）、`evaluate` と `train` の取り出しを `*info` で受ける、
  `cfg.candidate == "C"` を `kind == "C"`（stabilize 以外では kind = candidate））
- `configs/stage1_ptower.yaml`: 注記（コメント）19 行だけ。鍵は足していない（`test_new_keys_are_absent_from_the_default_config`）
- 原典の照合: OnlineTAS（arXiv 2411.01122 §3.3）と StableSPR（arXiv 2605.16387 §2.1、式 (6)）は、外部への接続を事前の確認なしに
  行わない規約のため引いていない。記憶と TEC と EGTP は SPEC §4.3 とカードの記述の範囲で実装した

パラメータ数（`maps` 64、layers 6、既定の鍵。`params.txt`）:

    linear 18,441 / A 331,090 / B 382,299 / C 331,090 / stabilize(base C) 331,090 / A+boundary_flag 331,154
    ssm（state 64、2 層）234,121（学習 234,121）/ ssm_selective false 234,121（学習 232,841、dt_proj 1,280 を凍結）
    ssm（state 16、4 層）262,793 / memory（len 128）378,011 / memory_len 0 も 378,011（記憶の層は作るが使わない）
    progress 331,675 / progress+gap_input delta 331,803

## D. 試験

SSM の因果性の差の実測（GPU 0、変更後、eval・no_grad、後半の入力に +50）:

    selective True  T=60  prefix maxdiff 0.0  suffix maxdiff 31.18  repeat 0.0
    selective True  T=700 prefix maxdiff 0.0  suffix maxdiff 31.21  repeat 0.0
    selective False T=60  prefix maxdiff 0.0  suffix maxdiff 31.18  repeat 0.0
    selective False T=700 prefix maxdiff 0.0  suffix maxdiff 31.21  repeat 0.0

→ 許容差は 0（`torch.equal`）にした。CPU のヘッドも `torch.equal`。

`tests/test_stage1_ptower_heads.py` 35 件（502e6af7、`CUDA_VISIBLE_DEVICES=0`）: **35 passed in 3.40s**。内訳:

    基準値 4 + layers を変えた対照 1 + 既定の設定に新しい鍵が無い 1
    manifest の検算と境を一つ無視した対照 1、Δ の不明の区別 1、load_fold の添え方 1
    CPU ヘッドの呼び口と因果性 6（memory、memory_len 0、progress、stabilize の A・B・C）、progress の頭の因果性 1
    SSM の呼び口と因果性 2（selective 真偽、GPU）、ssm_selective 偽で Δ が凍結 1、双方向 GRU が因果性の検査で落ちる 1
    存在しない候補名・base_candidate・gap_input で ValueError 1
    reset_at_clip 真で境の後が境の前に依らず、偽で依る 2、gap_input の flag と delta の列 1
    進捗の教師 1、遷移行列が train だけから作られる 1、遷移による復号 1、TEC の重みの範囲 1、TEC の α 0 と正 1、EGTP 1
    煙試験 5（A、memory、progress、stabilize は CPU、ssm は GPU。各 2 epoch）

煙試験の所要時間（call）: memory 0.34 s、ssm 0.26 s、stabilize 0.18 s、A 0.18 s、progress 0.18 s。
煙試験は `evidence` を一時の置き場（`tempfile.TemporaryDirectory`）の `ExperimentManager` に差し替え、`load_fold` を合成の
特徴（学習 4 動画・val 2 動画、各 200〜320 フレーム、2 クリップ、9 クラス）に差し替えた。checkpoint の存在を確かめた後、
置き場を消して `*.pth` が 0 件であることを確かめる。実装の誤り 1 件（train のクラス数の集計が 3 要素で取り出していた）を
煙試験が最初の回で捕まえ、直した（1afc4ad1 に含む）。

全件（502e6af7 相当の作業ツリー、`CUDA_VISIBLE_DEVICES=0`）:

    SKIPPED [1] tests/test_stage1_ptower_r3_dist.py:298: needs two GPUs
    （FAILED は A4 と同じ 6 件）
    6 failed, 959 passed, 1 skipped, 27 warnings in 27.23s
    diff A_failed_before.txt D_failed_after.txt → 差なし（SAME_FAILURE_SET）

旧版との学習の一致（scratchpad の `train_equiv.py`。`git show origin/phase0:scripts/stage1_ptower.py` と現在の版で、同じ合成の
fold・同じ乱数の種で 3 epoch を学び、best.pth の state_dict を比べた）:

    linear weights_bit_identical True epoch_logs_identical True epoch=3 val_jaccard=0.068763 accuracy=0.142857
    A      weights_bit_identical True epoch_logs_identical True epoch=3 val_jaccard=0.057394 accuracy=0.146667
    B      weights_bit_identical True epoch_logs_identical True epoch=3 val_jaccard=0.042515 accuracy=0.177143
    C      weights_bit_identical True epoch_logs_identical True epoch=3 val_jaccard=0.055550 accuracy=0.144762

G2: 四候補の出力が基準値とビット一致、四ヘッドが因果性の試験を通過、双方向 GRU が同じ検査で落ちる → **pass**

## F. 検証

- 依存: `git diff --quiet origin/phase0 -- uv.lock pyproject.toml` → 差なし（NO_DEP_DIFF）。要約値は A3 と同じ
- 禁止領域: `find experiments runindex data -newer tasks/.../spec.yaml -type f` → 0 件。
  `find / -xdev -name best.pth -newer ...` で見つかった 2 件は既存の試験（`test_pipeline.py` の Stage A と dummy trainer）が
  `/tmp/pytest-of-ubuntu/pytest-44/` に作ったもので、本契約の煙試験のものではない
- `make forbidden-check`: `"status": "pass"`、`"violations": []`（実装の commit の後と、memory_len 0 の変更の後の二度）
- 陽性対照（repo の外の clone の写し、HEAD 1afc4ad1、origin/phase0 を ea73a8ba に合わせた）:
  足す前 `"status": "pass"`・exit 0、`data/zz_heads_control.txt` を `git add -f` した後
  `"status": "fail"`・exit 1・`{"path": "data/zz_heads_control.txt", "reason": "禁止領域 data/ の内側"}`。写しは削除した

## 変更範囲（集合差）

`git diff --name-only origin/phase0 HEAD` と未追跡（報告を書いた後）の和、10 件:

    README.md
    configs/stage1_ptower.yaml
    scripts/stage1_ptower.py
    tasks/T-2026-10-23-ptower-cand5-heads-impl/{RESULT.md, SPEC.md, audit.md, result.yaml, spec.yaml}
    tasks/inbox.d/T-2026-10-23-ptower-cand5-heads-impl.md
    tests/test_stage1_ptower_heads.py

許可（scripts/・configs/・tests/・README.md・契約のディレクトリ・受け皿の一件）の外: 0 件。
experiments/・runindex/・data/・docs/proposals/ の内側: 0 件。`make task-validate` は報告を書いた後に `1 task(s), 0 failed`
（一度目は result.yaml の値の中の「 #」が YAML のコメントとして切れて L1-6 で落ち、引用符で囲んで直した）。

## commit と送出

## 解決された参照（手順書 3。原文、conventions_rev ceb7ef0f と blob 一致）

`git hash-object context/conventions.md` = ceb7ef0f88a3f30279930be96ab9a5722acc2f09（契約の conventions_rev と一致）。
denominator・sigma_policy・frozen_source の参照は無い。

### conventions#prohibitions（L98〜L108）

    <a id="prohibitions"></a>
    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |


### conventions#issuer_cautions（L154〜L192）

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


### conventions#folds（L297〜L364）

    <a id="folds"></a>
    ## folds

    動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-17-fold-table` が確定）。
    本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。

    | 折り | test（3） | val（2） |
    |---|---|---|
    | A | 04, 05, 07 | 09, 10 |
    | B | 01, 03, 14 | 02, 08 |
    | C | 02, 08, 11 | 06, 12 |
    | D | 06, 13, 15 | 04, 05 |
    | E | 09, 10, 12 | 07, 15 |

    train はその折りの test と val を除いた 10 本である。
    **折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。
    各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。

    ### 追加 6 動画

    工程の注釈がある追加動画は次の 6 本である。

        17, 18, 19, 20, 21, 22

    **22 はフレーム画像が無く使えない。工程塔に足すのは 17〜21 の 5 本で、その塔を P\*-20 と呼ぶ。**
    旧称は P\*-21。古い記録の P\*-21 は P\*-20 と読み替える。
    出所: 利用者の確認と決定 2026-09-27（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、
    `tasks/T-2026-09-27-stage1-ptower-20/audit.md` の `verify_folds` の記録。

    **用途は訓練のみである。どの折りの test にも val にも現れない。**
    15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。

    ### 規律

    **選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
    test は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。

    出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-17-fold-table`。

    ### val と test の重なり

    各折りの val 2 本（計 10 本）は、どれもほかの折りの test に現れる。上の表から読める対応は次のとおり。

    | val の動画 | val に使う折り | test に持つ折り |
    |---|---|---|
    | 09, 10 | A | E |
    | 02, 08 | B | C |
    | 06 | C | D |
    | 12 | C | E |
    | 04, 05 | D | A |
    | 07 | E | A |
    | 15 | E | D |

    **val に一度も入らないのは 01・03・11・13・14 の 5 本**である。test としては折り B に 3 本（01・03・14）、
    C に 1 本（11）、D に 1 本（13）、A と E には 0 本。

    val で設定・処方・構造・型・止め方を選ぶ段（両塔の学び直しと Stage 2 以降）では、次の三つを守る。

    1. この重なりを prereg と報告に明記する
    2. test の値を報告するときは、val に一度も入らない 5 動画だけで集計した値を副次として添える。
       各動画の値は、その動画を test に持つ折りのモデルが出す。集計の仕方は prereg に書く
    3. 副次の値は、判定・関門・選定のどれにも使わない

    選ぶ規則（規律の小節。その折りの val で選ぶ）は変えない。

    出所: 利用者の決定 2026-10-19（契約 `T-2026-10-21-ops-taskstart-resume-folds-val` SPEC §2）、上の折りの表、
    `docs/stage1/design_val_subsets.md` 223 行。

