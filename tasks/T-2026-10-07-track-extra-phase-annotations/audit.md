# audit — T-2026-10-07-track-extra-phase-annotations

ホスト efros、zsh、時刻は JST。秘密の値は出力していない。

## 1. 起動前と開始状態（Task A-1、A-2）

    git branch --show-current → feat/design-val-subset-balance（起動前）
    git status --porcelain --untracked-files=no → 0 行
    git ls-files --others --exclude-standard → 20 件（注釈 CSV のみ。digest・その他 0）
    .git/info/exclude に 21 行（注記 1 + 20 経路）を足した（前回と同じ方法）。退避は 0 件
    make task-start TASK=T-2026-10-07-track-extra-phase-annotations → 分岐 feat/track-extra-phase-annotations（起点 origin/phase0）
    HEAD = merge-base = origin/phase0 = b9272cfe9fdcfcfdb1c490e2c3e12fa7074446ed（PR #203 の統合）
    make task-validate → OK / make task-preflight → 6 PASS / 0 WARN / 8 SKIP / 0 FAIL
      SKIP: P2 P3 P11（plan.env.preflight に記載なし）、P4 P5 P13 P14（exp のみ）、P12（解決前提の参照なし）
    .sync-pause は task-start が作成。grep -c sync-pause ~/bin/m2-sync.sh → 2

## 2. 20 件の照合（Task A-3）

    件数 20、合計 210618 バイト、一覧の要約値 87f62aeef0985a9e3623f964df75a52b0b6945b536179b1ac93ac74e1996135d
    前の契約の記録（経路・バイト・sha256 の表）と cmp で同一
    名前の集合が §2 と一致。対照: 21_5 を 21_9 に変えた一覧で集合差 2 行（片側 1 ずつ）
    写し data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase: 20/20 一致
    写し /home/ubuntu/slocal2/EgoSurgery/annotations/coco_format/phase: 20/20 一致
    起点で追跡されている 17〜22 の CSV: 0 件

## 3. P*-20 の道具（Task A-4）

    git cat-file -e b9272cfe:<path> → scripts/stage1_ptower_20.py、scripts/run_stage1_ptower_20.py、
      scripts/select_stage1_ptower_20.py、configs/stage1_ptower_20.yaml すべて在る（PR #202 は a460cc33 で統合済み）

## 4. 試験の基準と占位（Task A-5、A-6）

    pytest tests/ -q -p no:cacheprovider → 6 failed, 699 passed
      失敗: test_engines::test_mmdet_trainer_eval_recipe_in_metrics、test_fetch_task::test_rejects_unknown_file_name、
            test_research_logger の 4 件（log_run_idempotent、invokes_log_run_on_finally、no_double_post_on_normal_exit、
            swallows_exception_in_user_block）
    conventions_rev 073f9dc0（git log -1 -- context/conventions.md）
    runindex_commit 63ae65da（git log -1 -- runindex/、作業ツリーと同一）
    counts: wc -l − 1 で index 1961、experiments 750、verdicts 1506（同じ数え方で 2fb7c905 が 1911/718/1506 を再現）

## 5. 読む側の洗い出し（Task B-1、B-2）

探し方 1: git grep "egosurgery_phase"（*.py *.yaml *.yml *.sh *.json Makefile、tasks・experiments・docs を除く）→ 21 ファイル
探し方 2: git grep -E "(glob|rglob|listdir|iterdir|scandir|os\.walk)\(" で phase・ann・csv を含む行
両方に既知の a1_fold_table.py load_phase が載った。各箇所を読み、読み込み部分を次の 2 状態で動かした
（スクリプトは scratchpad の measure.py。repo へは書かない）:
  A = 追跡済み 23 件だけを写した scratchpad のディレクトリ、B = 実際のディレクトリ（43 件）

    DIFF a1_fold_table.load_phase | 15 -> 20 videos
    DIFF hts_phase_coverage.load_phase([PHASE_PROJECT]) | 23 -> 43 segments
    SAME hts_phase_coverage.load_phase([PROJECT, HTS]) | 46 segments, labels equal=True
    SAME split_thinning_rule.load_phase (PROJECT+raw) | 30782 frames
    SAME verify_thinning_rule.load_phase_labels: labels | 30782 frames
    verify_thinning_rule src（経路を揃えて比較）: 10461 フレーム（動画 17〜21）で変わる。lab_src は 174 行で代入されるだけで使われない
    DIFF frame->phase map (glob all; EDA x3 / l0b / diag / coverage_export / vs_tool_phase) | 17233 -> 27694 frames
    DIFF analyze_annotations_eda.phase_temporal input (sessions) | 23 -> 43 sessions
    SAME   ... ∩ tool frames | 15437
    DIFF audit_l0_hts_acceptance.c6: phase_video_segments | 23 -> 43
    SAME build_phase_manifest.build: clips kept by PAPER_SPLIT_VIDEOS + vocab
    SAME build_phase_manifest_p20.extra_clips (B) vs expected 17-21 | 20 clips
    SAME PhaseImageDataset(train/val/test).samples | 9657 / 1515 / 4265

初回の計測では verify_thinning_rule の src を A と B の経路のまま比べ、27694 件の差と出た（比較の誤り）。経路を揃えて測り直した。
diag_hand_tool_consistency は contact_stats が術具のフレーム（15 動画）から工程を引くため、出力に届かない（実装を読んで判断）。
s4_phase_baseline.yaml の phase_label_dir は読むコードが git grep で 0 件。
表は docs/stage1/extra_phase_annotations.md。

## 6. 生成器の修正（Task B-4、B-5）

    直す前: python scripts/analysis/a1_fold_table.py → exit 1、IndexError: list index out of range
    docs/stage0/A1_fold_table.md の sha256 eb66170a8565b9937133bd99503a04823039278efefe035f74f3b6b555452b2c（前後で同一）
    直した後: exit 0。標準出力と docs/stage0/A1_fold_table.md の差は末尾の空行 1 行（print の改行）のみ
    table_digest = 237837faa843e1b3da77f669039129e5ffbfde732f3a7869d07756206746976b（記録と一致）
    対照: 動画 01 の工程の一つに +100000（記憶上）→ 要約値が変わる
    ruff: F541 が 2 件（555・578 行）。起点の版でも同じ 2 件で、本契約の変更行ではない

## 7. Gate G2

扱いを決められない 8 本（hts_phase_coverage のプロジェクト側だけの集計、EDA 3 本、audit_hts_coverage_export、
audit_hts_vs_tool_phase、audit_l0_hts_acceptance c6、audit_l0b_raw_provenance）を利用者に諮った。
回答: 「直さず表に残す」。

## 8. 追跡（Task C）

    .git/info/exclude を起動前の写しに戻した → 該当行 0
    git check-ignore で 20 件とも無視されていない（0 件）
    git add -- <20 経路>（-f なし）→ 追跡 20 件。存在しない経路 99_9.csv では 0 件
    ステージの経路の集合 = 20 件の一覧
    index の blob のバイトと sha256（git cat-file）= Task A の表と cmp で同一

## 9. 検証（Task D）

    P*-20: build_phase_manifest_p20 の追加動画の clip は 20 件、動画 17〜21。対照: 21_5 を除くと 19 件で集合が変わる。
      15 動画側は data/processed/phase_manifest（本ディレクトリを読まない）。P*-20 の道具と設定の差分 0
    design_val_subsets.py --write → exit 0、FAIL 0、docs/stage1/design_val_subsets.{md,csv} の差分 0 行。
      対照（道具の内部）: 入力を一行変えると csv の要約値が変わる
    pytest → 6 failed, 699 passed。失敗の名前の集合が §4 と同一
    python tools/check_forbidden.py --base b9272cfe --task … → status fail、changed 23、violations 20。
      違反の経路の集合 = 追跡した 20 件（両方向の集合差 0）。それ以外の違反 0
    文書の一覧から計算し直した要約値 87f62aee…（a と一致）、sha256sum -c で 20 件 OK。
      対照: 先頭の一文字を変えた一覧で FAILED 1
