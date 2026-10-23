# audit — T-2026-10-23-ptower-cand5-compute-probe

ホスト andrew（`hostname` = Andrew）、repo `~/slocal2/m2`。時刻は JST。

## A1. 開始状態（手順書「0. 始める」）

    $ git branch --show-current            → phase0（開始時）
    $ git status --porcelain --untracked-files=all  → 空
    $ git branch --list feat/ptower-cand5-compute-probe → 空 / ls-remote → 空 / log --all -- tasks/<id> → 空
    $ python3 scripts/task_start_classify.py
    [task-start] 分類（比較先 origin/phase0 bfe45510）
    [task-start]   追跡下の変更: 0 件 … 分類: 通す
    $ make task-start TASK=T-2026-10-23-ptower-cand5-compute-probe
    [task-start] 分岐を作成: feat/ptower-cand5-compute-probe（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら make task-release … END=complete）
    [task-start] 完了。分岐 feat/ptower-cand5-compute-probe で契約 … の作業を開始できます

起点 `origin/phase0` = `bfe45510f7c38008465ba811c9d7be73d28fd70b`。開始直後の作業ツリーは契約の 2 ファイル（task-start が取り込んだ未追跡）だけ。

## A2. 検証とプリフライト

    $ make task-validate TASK=…   → OK, 1 task(s), 0 failed
    $ make task-preflight TASK=…
    P1 venv_active PASS / P2 cuda_ext_loaded SKIP（記載なし） / P3 deterministic_flags SKIP（記載なし）
    P4 prereg_committed SKIP / P5 frozen_source_hash SKIP（analysis） / P6 decisions_answered PASS
    P7 destination_writable PASS / P8 contract_valid PASS / P9 spec_lint PASS（規則 9 件、該当なし）
    P10 preflight_names_known PASS / P11 gpu_free PASS（compute プロセス 0 件）/ P12 refs_resolved SKIP
    P13 symmetry_table_complete SKIP / P14 proposal_card_checked SKIP
    RESULT: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL, exit=0

## A3. 装置・版・空き容量

    $ nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader
    0, NVIDIA RTX A6000, 49140 MiB, 595.84
    1, NVIDIA RTX A6000, 49140 MiB, 595.84
    $ nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | wc -l → 0（二枚とも、各 GPU 段の直前にも 0）
    使う一枚: GPU 0（全試行 CUDA_VISIBLE_DEVICES=0）。GPU 1 は使っていない
    torch 2.1.2+cu118 / torchvision 0.16.2+cu118 / timm 1.0.27 / mamba_ssm 2.2.2 / causal_conv1d 1.4.0
    torch.version.cuda 11.8, cuda available True, cudnn 8700
    $ df -h . experiments  → /dev/sdc1 7.3T, used 5.4T, avail 1.6T（78%）。repo と experiments/ は同じ区画

## A4. manifest の枚数（二通り）

`data/processed/phase_manifest`（r3 の `manifest_dir`）は train 9,657 + val 1,515 + test 4,265 = 15,437 で 17,233 と一致しない。
`data/processed/phase_manifest_all_phase` は train 10,580 + val 1,904 + test 4,749 = 17,233 で一致した。こちらを使った。

    一通り目（clip の frames の数の和 = num_frames、assert 済み）: total 17233
    per_video {'01': 999, '02': 529, '03': 1363, '04': 1643, '05': 1318, '06': 1447, '07': 1788, '08': 1591,
               '09': 672, '10': 1232, '11': 865, '12': 619, '13': 843, '14': 1858, '15': 466}
    二通り目（折り A の train = 01 02 03 06 08 11 12 13 14 15 の動画ごとの和）: 10580
    manifest の train の num_frames: 10580（一致）
    phase_vocab.json のクラス数: 9
    17〜21 は manifest に無い。docs/phase_annotation_stats_videos17-21.md の 10,461 を使う

## A5. 試験の前の値

    $ CUDA_VISIBLE_DEVICES="" python -m pytest tests -q -p no:cacheprovider -rfE
    6 failed, 924 passed, 1 skipped, 22 warnings in 24.62s
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

## B. 較正（G2）

    $ python experiments/analysis/ptower_cand5_compute_probe/run_probe.py calib
    ok ('calib', '--batch', '1') 2.05GiB 0.09676515059545636
    ok ('calib', '--batch', '2') 4.14GiB 0.17089255880564452
    ok ('calib', '--batch', '16') 26.97GiB 1.0659250373952092

G2: 26.97 GiB と三周目の記録 27.06 GiB（`tasks/T-2026-09-19-stage1-phase-tower-r3/RESULT.md` L25・L53）は同じ桁。2.05 < 4.14 < 26.97 で単調。pass。
（この前に動作確認として batch 1 を `probe.py` で直接一度流した。2.05 GiB・0.0967 s。`results.jsonl` には入れていない）

## C〜F. 本測定（背景で一括）

    $ for p in vit moco vmae mamba; do python …/run_probe.py $p; done
    → results.jsonl に 21 行（ViT 18、MoCo 1、MAE 1、mamba 1）。較正の 3 行と合わせて 24 行。打ち切り 0、error 0

## 対照の試行（目標の一つ上と、mamba の再現）

    $ python …/run_probe.py control
    oom ('vit', '--size', 'large', '--res', '800', '--scope', 'full', '--batch', '8') 46.46GiB
    oom ('moco', '--batch', '512') 44.98GiB
    oom ('vmae', '--batch', '512') 46.58GiB
    ok ('mamba',)  → 三行とも一回目と同じ値（5.684341886080802e-14 / 1.1368683772161603e-13 / 1.2721866369247437e-06・1.1990778148174286e-07）

results.jsonl は計 28 行。最初の試行の終了 2026-10-23 05:59:23、最後 06:07:32。壁時計の和 470.3 秒。

## mamba の勾配差の切り分け（パラメータごと、決定論的な設定で同じ seed の二度）

    名前                   最大絶対差               その勾配の最大絶対値
    1.dt_proj.weight       1.3877787807814457e-17   1.306220687169457e-10
    1.dt_proj.bias         5.551115123125783e-17    5.965793969942013e-10
    1.out_proj.weight      2.842170943040401e-14    4.573376486405323e-07
    2.in_proj.weight       4.440892098500626e-16    5.258194732959964e-07
    2.conv1d.weight        1.1102230246251565e-16   3.3889591133373642e-09
    2.conv1d.bias          1.4210854715202004e-14   3.7004033970333694e-07
    2.x_proj.weight        1.5265566588595902e-15   1.4126489977783763e-09
    （ここに出ないパラメータ、0.* と 3.* の Linear を含む、はビット一致）

（この切り分けを流したとき、置き場の集計スクリプトの旧名 `tabulate.py` が pip の tabulate を隠し、torch の終了処理が
`AttributeError: module 'tabulate' has no attribute 'tabulate'` を出した。測定値には関わらない。`make_tables.py` へ改名した）

## G. 検証

    $ CUDA_VISIBLE_DEVICES="" python -m pytest tests -q -p no:cacheprovider -rfE
    6 failed, 924 passed, 1 skipped, 22 warnings in 25.18s
    失敗の名前の集合: A5 と diff 0（同一）
    $ make forbidden-check TASK=T-2026-10-23-ptower-cand5-compute-probe
    "status": "pass", "violations": [], "permitted": 置き場の 4 件, exit 0
    checkpoint（*.pt* / *.ckpt）: 置き場に 0 件

forbidden-check の陽性対照（repo の外の clone の写し、起点 bfe45510 を checkout）:

    足す前:                 status pass, violations [], exit 0
    data/zz_probe_control.txt を git add -f した後: status fail,
      violations [{'path': 'data/zz_probe_control.txt', 'reason': '禁止領域 data/ の内側'}], exit 1
    写しは削除（ls → No such file or directory）

一回目の陽性対照は無効だった。`--task` を渡したが写しに未 commit の契約ファイルが無く読み込みで落ち（status fail、violations []、exit 2）、
さらに `rm` が対話の確認を求めて控えのファイルが消えなかった。`--task` を外し `command rm` で取り直したのが上の結果。

## 変更範囲（集合差）

commit 前の `git status --porcelain --untracked-files=all`（11 件、すべて未追跡の新規）:

    experiments/analysis/ptower_cand5_compute_probe/{REPORT.md, make_tables.py, probe.py, results.jsonl, run_probe.py}
    tasks/T-2026-10-23-ptower-cand5-compute-probe/{RESULT.md, SPEC.md, audit.md, result.yaml, spec.yaml}
    tasks/inbox.d/T-2026-10-23-ptower-cand5-compute-probe.md

許可された集合（置き場・契約のディレクトリ・受け皿の一件）を引いた差: 0 件。追跡下のファイルの変更: 0 件。
`scripts/`・`src/`・`configs/`・`data/`・`runindex/`・`docs/proposals/`・`context/` への変更: 0 件。

## commit と送出

    commit 165cd94c（主作業）→ git push -u origin feat/ptower-cand5-compute-probe（新しい分岐）
    $ gh pr view feat/ptower-cand5-compute-probe --json number,baseRefName,headRefName,isDraft,state
    {"baseRefName":"phase0","headRefName":"feat/ptower-cand5-compute-probe","isDraft":false,"number":259,"state":"OPEN"}
    commit fbb7a46f（PR 番号の記帳）→ push
    $ source scripts/load_env.sh && make task-report TASK=T-2026-10-23-ptower-cand5-compute-probe   → exit 0
    {"task_id": "T-2026-10-23-ptower-cand5-compute-probe", "verdict": "pass", "n_issuer_defects": 3,
     "report_sha256": "37faa4a74e9928648df31d59c6deeb510e8824282c447b6a600eb725fe51ab93", "report_bytes": 8428, "replaced_blocks": 0}

## 解決された参照（手順書 3。原文、conventions_rev ceb7ef0f と blob 一致）

`git rev-parse HEAD:context/conventions.md` = `git hash-object context/conventions.md` = ceb7ef0f88a3f30279930be96ab9a5722acc2f09。下は各アンカーの節の原文をそのまま写したもの。

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
    

### conventions#precision（L489〜L503、ファイル末尾）

    <a id="precision"></a>
    ## precision
    
    | 対象 | 精度 | 出所 |
    |---|---|---|
    | 界面の学習（`train_t1b.py` 系。既定は fp32） | TF32。Tier 1 の全腕（分母の空入力界面を含む）で同じ設定にする | `tasks/T-2026-09-17-amp-compile-timing/RESULT.md`、利用者の決定 2026-09-18 |
    | 検出塔のフル学習 | fp16 の autocast。凍結源と同じ。TF32 の採用の範囲に入らない | `tasks/T-2026-09-18-stage1-detector-towers/RESULT.md`、利用者の判断 2026-09-18 |
    
    - `torch.compile` は使わない。compile 系の条件は完走しなかった
    - 界面の学習に TF32 を当てる前に、その学習が fp32 で始まることを実測する
    - `train_t1b.py --tf32` は `torch.backends.cuda.matmul.allow_tf32 = True` により行列積の TF32 を許す。`torch.backends.cudnn.allow_tf32` は変更せず、実測した既定は True（畳み込み側）。`--amp no` で autocast と GradScaler を作らない。設定は同じ過程の評価にも効く（`scripts/train_t1b.py`、`tasks/T-2026-09-17-amp-compile-timing/audit.md`）
    - 計算器は TF32 を持たない。計算器の日数は単精度の値として読む（`tasks/T-2026-09-27-stage2-prep/RESULT.md` §3）
    - 工程塔の学習の精度は本節で定めない
    - 実測: TF32 は W1 で 1.182 倍、W2 で 1.286 倍速く、主指標の差は 0.030σ（`tasks/T-2026-09-17-amp-compile-timing/RESULT.md` §2・§3）
    - 出所: 利用者の決定と訂正 2026-09-18（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、上記三契約の報告

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
    

