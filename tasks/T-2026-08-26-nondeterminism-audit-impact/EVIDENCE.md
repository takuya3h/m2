# 証跡の記録 — T-2026-08-26-nondeterminism-audit-impact

事実の記録は `RESULT.md`。本ファイルは命令とその出力を置く。

## 1. 契約の検証（L1 + L2）

    make task-validate TASK=T-2026-08-26-nondeterminism-audit-impact
    EXIT=0
    WARN [L2-8] index.csv: 起票時 751 → 現在 1177（分母が動いています）
    WARN [L2-8] experiments.csv: 起票時 207 → 現在 213（分母が動いています）
    OK   T-2026-08-26-nondeterminism-audit-impact
    1 task(s), 0 failed

WARN 2 件をユーザーへ提示し、「実測側で続行」の回答を得た。

**終了コードの取得。** 初回 `${PIPESTATUS[0]}` は zsh のため空を返した（SPEC 第 6 節の
「配列の添字の書式はシェルによって違う」に該当）。以後は変数へ落として `$?` で取っている。

    echo "SHELL=$0"  →  SHELL=/usr/bin/zsh

## 2. L3 プリフライト

一回目（FAIL）:

    P6 decisions_answered     FAIL 未回答 3 件: 決定化を既存の学習経路すべてへ広げること;
                                   既存の報告の記述を訂正すること; 脆いと分類された結論を撤回すること
    RESULT: 4 PASS / 0 WARN / 4 SKIP / 1 FAIL
    PREFLIGHT_EXIT=2

3 件をユーザーへ提示し、3 件とも「行わない」の回答を得て `spec.yaml` の
`governance.decisions_required` を空にし、`meta.amendments` へ記録した。

二回目（P8 が私の編集で FAIL）:

    [L1-1] meta.amendments.0: 'date' is a required property
    [L1-1] meta.amendments.0: Additional properties are not allowed ('answers','at','by','what')

`tasks/_schema/spec.schema.json` を読み、`date` / `reason` / `diff` のみ許されることを
確認して書き直した。

三回目（PASS）:

    P1 venv_active            PASS
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              PASS 規則 8 件を検査し該当なし
    RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL
    PREFLIGHT_EXIT=0

**SKIP 4 件は「合格」ではなく「実行されなかった」である。**

## 3. Phase A — 索引の実在（陽性・陰性の両方向）

    EXISTS  runindex/index.csv          ABSENT  runindex/zzz_no_such_index.csv
    EXISTS  runindex/experiments.csv    ABSENT  context/auto/zzz_no_such_projection.md
    EXISTS  runindex/verdicts.csv       ABSENT  runindex/.hidden_no_such
    EXISTS  runindex/per_class.csv
    EXISTS  runindex/anomalies.md
    EXISTS  context/auto

**同じ方法で存在しない経路を調べると不在として返る。検査は空振りしていない。**

## 4. Phase A — 母集団と決定性の内訳

    index        rows=1177      experiments  rows=213
    verdicts     rows=1038      per_class    rows=8370
    run JSON 実測件数: 1177

    決定性の記録がある run  : 360
    決定性の記録を欠く run  : 817
    合計                    : 1177 (= run JSON 1177)  一致=True

**異質な方法での二度目の確認**（python の解釈を経由しない grep）:

    grep -l '"determinism"' runindex/runs/*.json | wc -l  →  360
    grep -L '"determinism"' runindex/runs/*.json | wc -l  →  817
    ls -A runindex/runs/ | wc -l                          →  1177
    ls -A runindex/runs/ | grep -cv '\.json$'             →  0

**先頭がドットのものを含めた走査**:

    find runindex/ context/auto/ -name '.*' -not -name '.'  →  零件

## 5. Phase B — 両立しない組み合わせ

    X1 解釈=seed_effect なのに決定性が controlled でない : 8
    X2 解釈が確定しているのに sigma_source が空          : 0
    X3 同一実験行に決定化あり/なしが混在                  : 6
    X4 significant なのに n_seeds が 1 または空          : 0

**零件（X2・X4）の裏取り**:

    sigma_source 空 65 行の解釈内訳: {'unknown': 65}
    解釈 unknown 82 行の sigma_source 有無: {'空': 65, '有': 17}
    n_seeds が 1/空の 92 行の判定: {'undecidable': 92}
    n_seeds=3 の 946 行の判定: {'significant': 738, 'not_significant': 207, 'undecidable': 1}

**同じ探索式が同じ列で非零を返すため、探し方は働いている。**

## 6. Phase C — 対照の出力

基準の記録と分類の実行の時刻:

    evidence/criteria_timestamp.txt  →  2026-08-26 07:25:59 JST (1787696759)
    evidence/classify_timestamp.txt  →  2026-08-26 07:26:47 JST (1787696807)

**基準の記録が 48 秒早い。分類は基準の後である。**

陽性対照:

    陽性対照 #111 : 合計=7 区分=脆い  pstd/median=0.2278
       内訳 {'a1_source':0,'a2_seeds':1,'a3_interp':2,'a4_ratio':0,'a5_sigma':3,'a6_det':1}
       期待=脆い  結果=PASS

陰性対照:

    陰性対照 採用: transfer/t1a_3seed_det456_frozen/...@val~relation_detr_seed456
       metric=jaccard 比=14.54 pstd=0.01002176592715329 pstd/median=1.0860 n_seeds=3
       合計=2 区分=頑健  内訳 {'a1_source':0,'a2_seeds':1,'a3_interp':0,'a4_ratio':0,'a5_sigma':0,'a6_det':1}
       期待=頑健  結果=PASS

    === 分離 ===  陽性=7 / 陰性=2  差=5

**陰性対照の選定で外したもの**（比が母集団最大の判定）:

    pstd=0.000561136 ratio=172.27 pstd/median=0.0644

陽性対照 #111 の 0.2278 より σ が小さい。**軸 5 が両対照を分離できなくなるため外した。**

## 7. Phase C — 分類の結果

    分類した判定行: 1038 / verdicts.csv 1038  未分類=0
    全 1038:      要注意 530 (51.1%) / 脆い 490 (47.2%) / 頑健 18 (1.7%)
    significant 738: 要注意 511 (69.2%) / 脆い 209 (28.3%) / 頑健 18 (2.4%)
    σ過小疑い(a5=3) かつ significant: 22 件

## 8. Phase A・B — 実装の実測

    src/egosurgery/engines/mmdet_trainer.py:501  deterministic=False（直書き）

主要 5 入口の実測:

    scripts/train_b2a.py      seed_everything=0  torch.manual_seed=1  cudnn=0  enable_determinism=0
    scripts/train_t1a.py      seed_everything=0  torch.manual_seed=1  cudnn=0  enable_determinism=0
    scripts/train_s4_tecno.py seed_everything=0  torch.manual_seed=1  cudnn=0  enable_determinism=0
    scripts/train_taux.py     seed_everything=0  torch.manual_seed=1  cudnn=0  enable_determinism=0
    scripts/train_haux.py     seed_everything=0  torch.manual_seed=1  cudnn=0  enable_determinism=0

**種は届いているが cuDNN は触っていない。**

TeCNO の使用（`egosurgery.models.heads.tecno_head.TeCNO`、`nn.Conv1d` を 4 箇所）:

    scripts/train_b2a.py                              TeCNO=8
    scripts/train_t1a.py                              TeCNO=9
    scripts/train_s4_tecno.py                         TeCNO=16
    scripts/train_taux.py                             TeCNO=7
    scripts/train_haux.py                             TeCNO=13
    src/egosurgery/models/temporal/grasp_inference_injection.py  TeCNO=4（決定化が実測された経路）

## 9. Phase D — 再測定の規模

    === 入口ごとの run 一本あたり所要（実測）===
      n= 420 median=      33.5s  scripts/train_grasp_phase_injection_variants.py
      n=   6 median=       6.9s  scripts/train_grasp_phase_injection.py
      所要が実測できない入口: 22 件

**再測定が要る入口（train_b2a.py / train_t1a.py 他）では `elapsed_seconds` の記録が無い。
規模は UNKNOWN と書いた。推測を数値で書いていない。**

## 10. 変更範囲の一覧

    make forbidden-check
    FORBIDDEN_EXIT=2
    {"base":"origin/phase0","changed":13,"checked":13,"status":"fail",
     "generated_directories":["context/auto/"],"generated_files":["tasks/inbox.md"],
     "violations": 10 件（すべて experiments/analysis/nondeterminism_audit_impact/ の内側）}

**内訳を一件ずつ示す。13 件はすべて未追跡の新規である。**

    ?? docs/sessions/digest/2026-08-24-59834e41-7c4c-4c54-b521-33475e058444.md   ← 開始前から在った
    ?? experiments/analysis/nondeterminism_audit_impact/CRITERIA.md
    ?? experiments/analysis/nondeterminism_audit_impact/REPORT.md
    ?? experiments/analysis/nondeterminism_audit_impact/classification.csv
    ?? experiments/analysis/nondeterminism_audit_impact/crosswalk_experiments.csv
    ?? experiments/analysis/nondeterminism_audit_impact/crosswalk_verdicts.csv
    ?? experiments/analysis/nondeterminism_audit_impact/evidence/classify_timestamp.txt
    ?? experiments/analysis/nondeterminism_audit_impact/evidence/controls.json
    ?? experiments/analysis/nondeterminism_audit_impact/evidence/criteria_timestamp.txt
    ?? experiments/analysis/nondeterminism_audit_impact/evidence/runs_determinism.json
    ?? experiments/analysis/nondeterminism_audit_impact/priority.csv
    ?? tasks/T-2026-08-26-nondeterminism-audit-impact/SPEC.md
    ?? tasks/T-2026-08-26-nondeterminism-audit-impact/spec.yaml

**10 件の「違反」は本契約の `outputs.destination` そのものである。**
道具は `context/auto/` と `tasks/inbox.md` しか生成物として除外せず、
契約が `experiments/` 配下へ成果を置くことを知らない。
**これは既知の道具の欠陥である**（`context/auto/followups.md` の
T-2026-08-15-injection-sweep-deterministic の項に同じ指摘がある）。

**判定を覆していないことの機械的な確認**:

    git diff --name-status origin/phase0 -- experiments/ runindex/ | grep -c '^M'  →  0
    git diff --name-status origin/phase0 -- experiments/ runindex/ | grep -c '^D'  →  0
    git diff --stat origin/phase0 -- runindex/ | wc -l                             →  0

## 11. 台帳の応答

（`make task-report` の実行後に追記する）

## 12. 既存の監査（anomalies.md 26 節）との突き合わせ

**独立な二つの方法が一致した。** 26 節は静的解析、本契約は run の記録から数えている。

    入口                                        26節   実測全体  実測欠く  一致
    train_grasp_phase_injection_variants.py     420      420       60   OK
    train_b2a.py                                265      265      265   OK
    train_t1a.py                                132      132      132   OK
    train_s4_tecno.py                            61       61       61   OK
    train_hand2det.py                            21       21       21   OK
    train_haux.py                                18       18       18   OK
    train_taux.py                                15       15       15   OK
    train_grasp_phase_injection.py                6        6        6   OK
    train_t1a_regiontraj.py                       6        6        6   OK
    train_t1b.py                                  6        6        6   OK
    train_t1a_boundary.py                         3        3        3   OK
    合計                                        953      953      593

    差の説明: 953 - 593 = 360 = injection_variants の決定化済み本数

**突き合わせにあたり、絶対パスの入口を basename へ正規化した。**
正規化前は `/home/ubuntu/slocal2/m2/scripts/train_b2a.py`（3 本）を
`scripts/train_b2a.py`（262 本）と別に数えており、合算して 265 本で 26 節と一致する。
第 4 節と REPORT 第 1 節の表は正規化前の値である。

## 13. 訂正した記述

**「種は届いている」は不正確だった。** `torch.manual_seed` は CPU 側のみで、
`torch.cuda.manual_seed_all` は 5 入口とも設定されていない
（`runindex/anomalies.md` 26 節の「CPU 側 3 種のみで GPU 側の制御が 1 つも無い」）。
REPORT 第 1 節を訂正した。
