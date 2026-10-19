# 実行監査

## 開始状態

開始前は feat/conventions-and-defect-records、作業ツリー清浄。対象の分岐・契約履歴なし、.sync-pause なし。
source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-19-proposal-gate-brief: exit 0、完了表示あり。
origin/phase0 起点で feat/proposal-gate-brief を作成し、本契約所有の .sync-pause を作成。秘密値は出力しなかった。
HEAD=origin/phase0=5a8baa790fa31ced4c8b891f7ee5ed5906c9d775。

## 契約検証と前提確認

命令: source .venv/bin/activate && CUDA_VISIBLE_DEVICES='' make task-validate TASK=T-2026-10-19-proposal-gate-brief

```text
OK   T-2026-10-19-proposal-gate-brief

1 task(s), 0 failed
exit=0
```

命令: git ls-tree -r --name-only HEAD -- tasks/T-2026-10-19-conventions-and-defect-records
結果: exit 0、出力0行。前提契約のディレクトリ・報告が起点にない。

命令: gh pr view 237 --json number,url,state,mergedAt,baseRefName,headRefName

```json
{"baseRefName":"phase0","headRefName":"feat/conventions-and-defect-records","mergedAt":null,"number":237,"state":"OPEN","url":"https://github.com/takuya3h/m2/pull/237"}
```

## 停止

G1: stop。前提契約が起点に統合されていない。SPEC の起動条件と想定外の扱いに従い、確認できた時点で停止。L3 プリフライト、Task Aの残り、B〜Dは未実行。
規約・手順の文書・雛形・検査器・既存カードは変更していない。試験・GPU計算・データアクセス・生成物の再生成も行っていない。
commit・push・本契約PR・台帳送出は未実行。既存PR #237の統合も実行していない。
停止後は task-release END=abort で本契約の抑止を解除する。結果は最終応答に残す。

## 利用者の統合連絡による再開

利用者:「統合したので再開して」。現在の分岐 feat/proposal-gate-brief、HEAD=origin/phase0=5a8baa790fa31ced4c8b891f7ee5ed5906c9d775。作業commitなし。

```text
?? tasks/T-2026-10-19-proposal-gate-brief/RESULT.md
?? tasks/T-2026-10-19-proposal-gate-brief/SPEC.md
?? tasks/T-2026-10-19-proposal-gate-brief/audit.md
?? tasks/T-2026-10-19-proposal-gate-brief/result.yaml
?? tasks/T-2026-10-19-proposal-gate-brief/spec.yaml
?? tasks/inbox.d/T-2026-10-19-proposal-gate-brief.md
```

.sync-pause は不在。同期ログにこの分岐の行は0件、先頭は停止時から変化なし。遠隔分岐なし、本契約のPR照会は[]。PR #237はMERGED、統合commit=05c7b85084bdc71ff09d80710d022c05db1d61d1、統合時刻2026-10-19 17:12:23 JST。

再開の例外規則により所有情報付きの.sync-pauseを作成し、更新したorigin/phase0へ自身のcommitのない分岐を早送りする。停止までの記録はそのまま保持する。

### 更新後の起点と再検証

HEAD=origin/phase0=8de3ac546568300ce8d2d4285dc0517793597b93。前提契約のRESULT.mdとresult.yamlがHEADに存在。早送りはexit 0。

命令: make task-validate TASK=T-2026-10-19-proposal-gate-brief

```text
OK   T-2026-10-19-proposal-gate-brief

1 task(s), 0 failed
WARN [L2-6] conventions.md が 5a8baa790fa31ced4c8b891f7ee5ed5906c9d775 以降に変更されています。差分を確認してください
exit=0
```

規約の差分をアンカーごとに比較: 変更=["naming", "folds", "symmetry", "crossfit"]、追加=["precision"]。本契約の注入対象prohibitions/issuer_cautionsは前後同一。

## L2-6警告の確認と利用者の続行許可

警告: WARN [L2-6] conventions.md が 5a8baa790fa31ced4c8b891f7ee5ed5906c9d775 以降に変更されています。差分を確認してください
変更節: naming / folds / symmetry / crossfit。新設: precision。前提契約の変更と一致。注入対象prohibitions/issuer_cautionsは文字列とSHA-256の前後比較で同一。
利用者は「警告を記録して続行する」と許可し、規約版の更新を指示した。起点8de3ac54で git log -1 --format=%H -- context/conventions.md を実行し、規約commit=7ba1d60db8c0ea8581bc03d79bafeaec56be1d1dと測定。contract.conventions_revをこの値へ更新し、meta.amendmentsに理由と差分を記録。

precisionはproposal_gate直後ではなくframe_sets後。C-1では規約から読む値を位置に依存せず前後比較する。

新規の未追跡: experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/eval_meta_val.json と val_metrics_by_epoch.json（各du=4.0K、未追跡・禁止領域）。移動・削除せず扱いを利用者へ確認中。

命令: make task-validate TASK=T-2026-10-19-proposal-gate-brief

```text
OK   T-2026-10-19-proposal-gate-brief

1 task(s), 0 failed
exit=0
```

命令: make task-preflight TASK=T-2026-10-19-proposal-gate-brief

```text
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS docs/proposals/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              PASS 規則 9 件を検査し該当なし
P10 preflight_names_known  PASS 宣言 1 件はすべて実装済み（既知: cuda_ext_loaded, deterministic_flags, gpu_free, venv_active）
P11 gpu_free               SKIP plan.env.preflight に gpu_free の記載なし
P12 refs_resolved          SKIP 解決前提の参照は無い
P13 symmetry_table_complete SKIP kind=impl のため対象外（exp のみ）
P14 proposal_card_checked  SKIP kind=impl のため対象外（exp のみ）

RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL
exit=0
```

## Task A 基準と G1

初回の基準記録処理ではnumeric_itemsの集合をJSONへ変換できずTypeErrorとなった。記録処理でsortedに変換して再実行し、対象文書・検査器は変更していない。
起点8de3ac54は前提契約のRESULT.mdとresult.yamlを含む。A-3: 生成の行はSPECの表と文字列一致。置き場と参照の全本文は起票時5a8baa79の本文と文字列一致。B.3の一行と雛形三行目もSPECの旧文言と一致。G1 pass。

生成の行:

| 生成 | 別会話。証拠地図だけを渡す | 提案カード三から五案。互いに排他的な方向 | 推奨・順位。repo の現状を見ること |

置き場と参照（起票時の本文と一致）:


- 提案カードは docs/proposals/YYYY-MM-DD-slug.md に置き、tools/check_proposal.py を通す
- 生成会話は候補を三案以上出す
- 批判会話は web 検索を必須とし、検索語と件数と見つかった否定例を却下表に書く
- exp 契約は spec.yaml の intent.proposal_card にカードの経路を書く。L3 の P14 が、カードの実在と検査の通過を確かめる。
  無い exp は起動できない
- 導入前の契約（T-2026-09-19-stage1-detector-towers-r2、T-2026-09-19-stage1-phase-tower-r3）は例外。三件目を足すときは本節を改訂する


測定:

```json
{
  "head": "8de3ac546568300ce8d2d4285dc0517793597b93",
  "hashes": {
    "context/conventions.md": "e1e8a1aef145151af13ce87d9602708c2f9bd43b023a50181f3475fddd45f541",
    "docs/proposal-gate.md": "18f7262b53253e05ba0aecf1286076d7e26011644fd3f1c6f2e76e92bc7e69a3",
    "docs/proposals/_template.md": "7f98e75debf25dbc2e6a90b39f00c5d5048dacceec0c6eb5e3d0493cb76eee17",
    "docs/proposals/2026-09-27-ptower-20.md": "b00a53029a5b3f64c1446a696cb0ddcd917a3afe075022d263c3c90b21d9181f",
    "tools/check_proposal.py": "a61abb5727c6582b3642eec8e7195b7a9d26b1ccddcdb482c6ec4ff6591088b8"
  },
  "read": {
    "forbidden_words": [
      "最大の新規性",
      "世界初",
      "画期的",
      "有望",
      "筋が良い",
      "本命",
      "未踏",
      "空白",
      "決定的",
      "確実に効く",
      "明らかに",
      "大幅",
      "劇的",
      "必ず改善",
      "唯一の"
    ],
    "card_items": {
      "1": "問い。yes/no で答えが出る一文",
      "2": "最も近い先行研究三件。著者・年・DOI か arXiv ID・設定・報告された効果量",
      "3": "先行研究がこれをやらなかった／効かなかった理由の推定",
      "4": "否定的な先行研究二件（効かなかった、負の転移の報告）",
      "5": "期待効果量（点）。#2 のどの値から外挿したか",
      "6": "成功確率（主観。0.0 から 1.0）",
      "7": "成功の閾値（主判定規則で書く）",
      "8": "失敗の閾値と、失敗時に捨てるもの（案／設計／問い のどれか）",
      "9": "この案を殺せる最安の実験（GPU 一日以内）",
      "10": "費用（run 本数 × 時間）",
      "11": "この案の結果でどの判断（関門・分岐）が変わるか",
      "12": "最も近い既存研究との差分一文",
      "13": "F の「却下」「予測外れ」と同型でないことの宣言。読んだ行の id",
      "14": "初回にセットで試す設定の掃引集合。掃引する主要因、固定する交互作用、固定の理由",
      "15": "この比較で揃えるべき条件の一覧と、両腕の実測値。conventions#symmetry の表の様式。UNKNOWN は先に測る",
      "16": "差を仮説の効果と読むために排除済みの交絡の一覧。排除していない交絡があれば、その影響の向き"
    },
    "numeric_items": [
      5,
      6,
      10
    ]
  },
  "spec_sha256": "77cbcc6ac7850dfbef1773f228e4893059f89a3917b8a89a49378abfd01ff2bc"
}
```

命令: .venv/bin/python tools/check_proposal.py docs/proposals/2026-09-27-ptower-20.md --json

```text
{
  "status": "pass",
  "path": "docs/proposals/2026-09-27-ptower-20.md",
  "only": "both",
  "words_checked": 15,
  "card_items": 16,
  "numeric_items": [
    5,
    6,
    10
  ],
  "hits": 0,
  "hits_by_kind": {
    "forbidden_word": 0,
    "missing_heading": 0,
    "missing_number": 0
  },
  "findings": [],
  "errors": []
}
exit=0
```

命令: .venv/bin/python tools/check_proposal.py docs/proposals/_template.md --json

```text
{
  "status": "fail",
  "path": "docs/proposals/_template.md",
  "only": "both",
  "words_checked": 15,
  "card_items": 16,
  "numeric_items": [
    5,
    6,
    10
  ],
  "hits": 3,
  "hits_by_kind": {
    "forbidden_word": 0,
    "missing_heading": 0,
    "missing_number": 3
  },
  "findings": [
    {
      "kind": "missing_number",
      "line": 36,
      "detail": "カード #5（期待効果量（点））の本文に数字が無い"
    },
    {
      "kind": "missing_number",
      "line": 38,
      "detail": "カード #6（成功確率（主観）の本文に数字が無い"
    },
    {
      "kind": "missing_number",
      "line": 46,
      "detail": "カード #10（費用（run 本数 × 時間））の本文に数字が無い"
    }
  ],
  "errors": []
}
exit=1
```

命令: .venv/bin/python -m pytest tests/test_check_proposal.py tests/test_proposal_card_gate.py --junitxml=tasks/T-2026-10-19-proposal-gate-brief/tests-before.xml -q

```text
...............................................                          [100%]
47 passed in 1.33s
exit=0
```

## Task A-6 二方式による残存検索

検索語: 証拠地図だけ / 地図だけ。git grepとPythonの独立した行走査は全追跡ファイルで結果完全一致。詳細はsearch-before.jsonに全件保存。

```json
[
  {
    "path": "context/conventions.md",
    "line": 268,
    "text": "| 生成 | 別会話。証拠地図だけを渡す | 提案カード三から五案。互いに排他的な方向 | 推奨・順位。repo の現状を見ること |"
  },
  {
    "path": "docs/proposal-gate.md",
    "line": 38,
    "text": "      → 生成会話: 地図だけから提案カード三から五案"
  },
  {
    "path": "tasks/T-2026-09-16-proposal-gate/SPEC.md",
    "line": 213,
    "text": "    | 生成 | 別会話。証拠地図だけを渡す | 提案カード三から五案。互いに排他的な方向 | 推奨・順位。repo の現状を見ること |"
  },
  {
    "path": "tasks/T-2026-09-16-proposal-gate/SPEC.md",
    "line": 262,
    "text": "          → 生成会話: 地図だけから提案カード三から五案"
  },
  {
    "path": "tasks/T-2026-10-19-conventions-and-defect-records/baseline.json",
    "line": 168,
    "text": "    \"context/conventions.md\": \"# conventions — 逐語で渡す規約\\n\\nこのファイルの各節は `spec.yaml` の `contract.inject_verbatim` から\\n`conventions#<anchor>` の形で参照される。**要約して渡してはならない。**\\nCLI は実行直前にこのファイルから原文を読み、指示に差し込む。\\n\\n改訂したら末尾の変更履歴に追記すること。参照側は `contract.conventions_rev` で\\n起票時点の commit を記録しており、差があれば検証時に差分が提示される。\\n\\n---\\n\\n<a id=\\\"split\\\"></a>\\n## split\\n\\n論文準拠 split の動画 ID は次のとおり。\\n\\n- train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`\\n- val: `09`, `10`\\n- test: `04`, `05`, `07`\\n\\n転記元: `data/splits/ego_train.txt`, `data/splits/ego_val.txt`, `data/splits/ego_test.txt`。\\n実装側の対応値は `src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS`。\\n\\n<a id=\\\"eval_recipe\\\"></a>\\n## eval_recipe\\n\\n転記元: `src/egosurgery/utils/eval_recipe.py`。\\n\\n- `LOCKED_DOWN_TEST_CFG`: `score_thr=1e-8`, `max_per_img=300`, `nms_pre=3000`, `nms_iou=0.6`\\n- `NMS_FREE_TEST_CFG`: `score_thr=0.0`, `max_per_img=300`, `nms_pre=None`, `nms_iou=None`\\n- `PHASE_EVAL_PROTOCOL`: `inference_protocol=online_causal`, `jaccard_mode=strict`\\n\\n比較の三角形および DETR-family の公式評価は NMS-free とする。工程評価は online causal と Jaccard strict を固定する。`select_box_nums_for_evaluation` は転記元で定義されていないため `UNKNOWN（転記元未特定）`。\\n\\n<a id=\\\"frozen_source\\\"></a>\\n## frozen_source\\n\\n比較の三角形で認める凍結源は Relation-DETR seed42 完走 checkpoint。\\n同定パスは `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`。\\n転記元: `docs/experiment_log.md` の STEP 0-2、および `configs/stage/s4_phase_baseline.yaml`。\\n\\n凍結源を変更してはならない。変更が必要な場合は別 task で判断を記録し、同じ凍結源を使う比較群と分母を再構成する。\\n\\ncheckpoint の正本 SHA-256 は次のとおり。\\n\\n    03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824\\n\\nサイズは 195421066 bytes。転記元は 2026-08-06 に実施した11ホストの ssh 一括監査であり、\\n11 ホスト全てで SHA-256 が一致し、mtime もナノ秒まで同一であった。\\n`third_party/` は git の追跡対象外だが、実体はホスト間で同期されている。\\n\\n`verify: ckpt_sha256` は全ホストで実行可能である。照合に失敗した場合は\\n`no_frozen_change` の違反として扱い、実行を中止して人へ escalate する。\\nskip する経路は設けない。\\n\\n### 検査の適用範囲\\n\\n凍結源の照合は、凍結源を使う契約に対して適用される。実行直前の検査では\\n`meta.kind` が `exp` の契約に対して実施し、それ以外は適用対象外として\\n未実施と記録する。\\n\\n**適用対象となった場合に、照合を省略する経路は存在しない。**\\n照合に失敗した場合は実行を中止し、人へ差し戻す。\\n\\n<a id=\\\"sigma\\\"></a>\\n## sigma\\n\\nsigma に関する列は 4 系統ある（backlog B-18）。\\n\\n1. `{metric}_pstd` / `{metric}_sstd` — seed 間の sigma（母集団 / 標本）\\n2. `delta_pstd_{metric}` / `delta_sstd_{metric}` — 実験間 paired Delta の sigma\\n3. `sigma_source` — sigma の系統。値は paired_delta または within_run_seed_spread\\n4. `delta_sigma_source` — paired sigma の計算方法。値は paired または unpaired_pooled\\n\\n3 と 4 は直交する（どの sigma を使ったか vs paired sigma をどう計算したか）。\\n\\n### 既定値（spec.yaml が sigma_policy を省略した場合に継承される値）\\n\\n    series: pstd\\n    sigma_source: paired_delta\\n    delta_sigma_source: paired\\n\\nこの既定は暫定である。正本（ddof=0 / ddof=1）は未決定であり、\\n決定され次第ここを変更する。変更時は過去の task を横断で再判定できるよう、\\n`RESULT.md` に解決済み sigma_policy が記録されていることを前提とする。\\n\\n### 判定規約の表記\\n\\n判定規約を `spec.yaml` や `prereg.md` に書くときは、絶対値を `abs(...)` の関数形で書く。\\n縦線による絶対値記法は markdown 表のセル区切りと衝突し、表を壊すため使わない\\n（backlog B-33 と同型の事故）。\\n\\n    正: abs(delta) / sigma >= 1 かつ 全 seed 同符号\\n    誤: 縦線で delta を囲む記法\\n\\n同じ理由で、区切りを表したいときは `/` かスラッシュ区切りの語を使う。\\n\\n<a id=\\\"prohibitions\\\"></a>\\n## prohibitions\\n\\n| id | 禁止事項 |\\n|---|---|\\n| `no_split_redefine` | split を再定義しない |\\n| `no_raw_write` | `data/raw` `data/external` に書き込まない |\\n| `no_frozen_change` | 凍結源を変更しない |\\n| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |\\n| `no_runindex_hand_edit` | `runindex/` を手で編集しない |\\n\\n<a id=\\\"env_p0\\\"></a>\\n## env_p0\\n\\n学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。\\nactivate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、\\n数値が変わったまま完走する。\\n\\n    source .venv-relation-detr/bin/activate   # 検出系\\n    source .venv/bin/activate                 # 解析・工程系\\n\\n拡張のロード確認をログに残すこと。\\n\\n<a id=\\\"naming\\\"></a>\\n## naming\\n\\n実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。\\n\\n    {step}_{seq:03d}_{description}_seed{seed}\\n\\n- `step`: `s0`〜`s9`、または `a1`〜`a7`\\n- `seq`: 同一 category と step 内の3桁ゼロ埋め連番\\n- `description`: 実験内容の短い説明\\n- `seed`: 乱数シード。既定42\\n\\n転記元: `README.md` の「命名規則」。\\n\\n---\\n\\n## 変更履歴\\n\\n| 日付 | commit | 変更 |\\n|---|---|---|\\n| 2026-08-03 | 8b17c4d | 新規作成。アンカー 7 節を定義 |\\n| 2026-08-06 | cac8147 | frozen_source の SHA-256 正本値を確定。sigma 節に判定規約の abs() 表記ルールを追加 |\\n| 2026-08-07 | 290da51 | frozen_source に「検査の適用範囲」を追記。実行直前検査での適用条件と、適用時に省略経路が無いことを明文化 |\\n| 2026-08-25 | a8c07e81 | issuer_cautions 節を追加。起票者の注意 13 件と、シェルの前提・命令ごとの読み込みを明文化 |\\n| 2026-09-16 | 6c95e4f | proposal_gate 節を追加。提案カード 14 項目・禁止語・設定/設計/問いの三水準・失敗時手順・引用規約・役割分離を定義。静的検査は tools/check_proposal.py、手順は docs/proposal-gate.md |\\n| 2026-09-17 | 537c968c | folds 節を追加。動画単位 5-fold の折り表（折り A は公式分割に固定）、追加 6 動画の用途、選定と test の規律を定義。正本は docs/stage0/A1_fold_table.md |\\n| 2026-09-19 | d6b37c79 | symmetry 節を追加。比較する腕の対称性の表の様式・必ず置く行・規則の読みを定義。proposal_gate のカードに #15 #16、issuer_cautions に注意 14 を追加。検査は L3 の P13 symmetry_table_complete、点検表は docs/symmetry-checklist.md |\\n| 2026-09-23 | ae76c1b9 | proposal_gate に「置き場と参照」を追加。カードは docs/proposals/ に置き check_proposal.py を通す、候補は三案以上、批判会話は web 検索必須、exp は intent.proposal_card で参照。検査は L3 の P14 proposal_card_checked、雛形は docs/proposals/_template.md |\\n| 2026-10-02 | 001b4309 | det_groups 節と crossfit 節を追加。検出の標的群 5 クラスと陰性対照群 4 クラス（研究方針 v2 §7.3）、送り手の交差適合の規則と閾値 3pt（研究方針 v2 §9.4、利用者の決定 2026-09-27）を定義。契約 T-2026-09-27-stage2-prep |\\n| 2026-10-17 | 2da88a8f | symmetry 節の「意図的に変える」の理由に 3「各塔の構造の標準の処方」を足し、使える比較・行・条件と使えない行、同じ塔の変種への不適用を定義。frame_sets 節を追加し、塔と界面が学習・評価に使うフレームの集合と規則を定義（利用者の決定 2026-10-16・2026-10-17）。契約 T-2026-10-17-tower-reselect-prereq |\\n<a id=\\\"issuer_cautions\\\"></a>\\n## issuer_cautions\\n\\n**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**\\n実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**\\n\\n| # | 注意 |\\n|---|---|\\n| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |\\n| 2 | 一致 0 件なら別の異質な方法でも確認する |\\n| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |\\n| 4 | 仕組みの挙動は実装を読んでから信じる |\\n| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |\\n| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |\\n| 7 | **丸めた表示を実数として扱わない** |\\n| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |\\n| 9 | 無変更は要約値で確かめる。表示属性では足りない |\\n| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |\\n| 11 | 測定の副作用が禁止領域へ触れないか確かめる |\\n| 12 | **判断の前に、いま見ているものが最新かを確かめる** |\\n| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |\\n| 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |\\n\\n**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、\\n確かめると 3 件とも実在した。\\n\\n**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した\\n（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。\\n\\n**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した\\n（自分の命令行にその語が含まれるため）。\\n\\n**注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。\\n\\n**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。\\n一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**\\n\\n**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。\\n\\n<a id=\\\"proposal_gate\\\"></a>\\n## proposal_gate\\n\\n手法・結合・補助信号・修正案の提案は、本節の関門を通ったものだけを契約に落とす。\\n関門は四つ。提案カードの充足／禁止語の不在／失敗時手順の履行／引用の照合。\\n\\n### 提案カード（全項目が埋まるまで推奨を書かない）\\n\\n| # | 項目 | 空欄を許す条件 |\\n|---|---|---|\\n| 1 | 問い。yes/no で答えが出る一文 | 許さない |\\n| 2 | 最も近い先行研究三件。著者・年・DOI か arXiv ID・設定・報告された効果量 | 三件未満なら「探して見つからなかった」と検索語を書く |\\n| 3 | 先行研究がこれをやらなかった／効かなかった理由の推定 | 許さない |\\n| 4 | 否定的な先行研究二件（効かなかった、負の転移の報告） | 同上の「探して見つからなかった」 |\\n| 5 | 期待効果量（点）。#2 のどの値から外挿したか | 許さない |\\n| 6 | 成功確率（主観。0.0 から 1.0） | 許さない |\\n| 7 | 成功の閾値（主判定規則で書く） | 許さない |\\n| 8 | 失敗の閾値と、失敗時に捨てるもの（案／設計／問い のどれか） | 許さない |\\n| 9 | この案を殺せる最安の実験（GPU 一日以内） | 無いなら「無い」と理由 |\\n| 10 | 費用（run 本数 × 時間） | 許さない |\\n| 11 | この案の結果でどの判断（関門・分岐）が変わるか | 変わらないなら提案しない |\\n| 12 | 最も近い既存研究との差分一文 | 許さない |\\n| 13 | F の「却下」「予測外れ」と同型でないことの宣言。読んだ行の id | 許さない |\\n| 14 | 初回にセットで試す設定の掃引集合。掃引する主要因、固定する交互作用、固定の理由 | 許さない |\\n| 15 | この比較で揃えるべき条件の一覧と、両腕の実測値。conventions#symmetry の表の様式。UNKNOWN は先に測る | 許さない |\\n| 16 | 差を仮説の効果と読むために排除済みの交絡の一覧。排除していない交絡があれば、その影響の向き | 許さない |\\n\\n#5 #6 #10 は数値で書く。#10 は #14 の掃引集合全体で見積もる。\\n#11 が空なら、新規性の有無によらず提案から外す。\\n\\n#15 の表に UNKNOWN が残る提案は、契約にせず先に調査契約を出す。\\n\\n### 禁止語（提案と契約の本文。完全一致で検査する）\\n\\n最大の新規性／世界初／画期的／有望／筋が良い／本命／未踏／空白／決定的／確実に効く／\\n明らかに／大幅／劇的／必ず改善／唯一の\\n\\n「未踏」「空白」を使う場合は禁止を解かず、「空白である理由の仮説（技術的困難／価値が無い／偶然）」を\\n添えた別の語で書く。形容詞の代わりに #5 #6 #10 の三数値を併記する。\\n\\n### 設定・設計・問いの三水準\\n\\n| 水準 | 含むもの | 変えるときの手続き |\\n|---|---|---|\\n| 設定 | 学習率・epoch・batch・seed、特徴の取り出し層、豊かさ L0 から L3、学習範囲 W1/W2、損失の重み、送り手の掃引点 | 初回の契約に掃引として入れる。後から足さない |\\n| 設計 | 界面の型、塔の選択、方向、信号の種類、時間文脈の与え方 | 提案カードを書き直し、批判会話を通す |\\n| 問い | どの仮説を測るか、相互改善の定義、論文の段 | 利用者が決める。関門で扱う |\\n\\n設定の掃引は初回にセットで試す。主要因は掃引し、交互作用は固定する。\\n何を固定したかと理由をカード #14 に書く。掃引集合はカードに書いた時点で固定する\\n（最良格子の選定は折り内 val、test は腕ごとに一度。conventions#split の規則に従う）。\\n\\n### 失敗時手順（修正案を書く前に、この順で書く）\\n\\n1. 失敗の定義は初回の契約にある閾値による。掃引のどの格子でも閾値に届かなければ、\\n   その設計の失敗である。格子を足すことは修正ではない\\n2. 原因候補を五区分で列挙する。測定器（eval・split・seed）／データ（ラベル・分布）／\\n   モデル・実装／仮説そのもの／問いの立て方\\n3. 区分ごとに識別実験を一つ書く（どの結果が出ればその区分だと分かるか）\\n4. 識別実験の結果で修正の水準を決める。測定器・データ・実装が原因なら、それを直して\\n   同じ設計を測り直す（設計は変えない）。仮説・問いが原因なら、設計か問いを変える\\n5. 設定水準の修正は選べない。例外は、初回に入れなかった設定があり、入れなかった理由が\\n   契約に書いてある場合のみ。その場合も後から足さず、掃引を再設計して一括で出す\\n6. 修正案に提案カードを付ける。設計変更一回の費用を #10 に含める\\n\\n### 引用規約\\n\\n- DOI か arXiv ID の無い引用は引用として扱わない\\n- 引用は機械で存在照合する。照合の出力を証跡に残す\\n- 数値つきで引く。「改善した」ではなく「指標・値・表番号・設定」\\n- 設定の違い（データセット・タスク粒度・入力）を必ず書く。「文献に数値がある」を「効く」と読み替えない\\n- 反証を先に探す。検索語・件数・見つかった否定例を記録する\\n\\n### 役割分離\\n\\n| 役割 | 会話 | 出力 | 禁止 |\\n|---|---|---|---|\\n| 生成 | 別会話。証拠地図だけを渡す | 提案カード三から五案。互いに排他的な方向 | 推奨・順位。repo の現状を見ること |\\n| 批判 | 別会話。カードだけを渡す | 却下表と順位。順位は期待情報量（#11）で付ける | 生成側の推奨文を読む |\\n| 判定 | 利用者 | 決定。F に一行 | — |\\n| 起票 | 別会話 | 契約 | 手法の変更 |\\n\\n生成と批判を同じ会話で行わない。批判は「やらない理由」から書く。\\n\\n### 置き場と参照（2026-09-23 追加）\\n\\n- 提案カードは docs/proposals/YYYY-MM-DD-slug.md に置き、tools/check_proposal.py を通す\\n- 生成会話は候補を三案以上出す\\n- 批判会話は web 検索を必須とし、検索語と件数と見つかった否定例を却下表に書く\\n- exp 契約は spec.yaml の intent.proposal_card にカードの経路を書く。L3 の P14 が、カードの実在と検査の通過を確かめる。\\n  無い exp は起動できない\\n- 導入前の契約（T-2026-09-19-stage1-detector-towers-r2、T-2026-09-19-stage1-phase-tower-r3）は例外。三件目を足すときは本節を改訂する\\n\\n---\\n\\n<a id=\\\"folds\\\"></a>\\n## folds\\n\\n動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-17-fold-table` が確定）。\\n本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。\\n\\n| 折り | test（3） | val（2） |\\n|---|---|---|\\n| A | 04, 05, 07 | 09, 10 |\\n| B | 01, 03, 14 | 02, 08 |\\n| C | 02, 08, 11 | 06, 12 |\\n| D | 06, 13, 15 | 04, 05 |\\n| E | 09, 10, 12 | 07, 15 |\\n\\ntrain はその折りの test と val を除いた 10 本である。\\n**折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。\\n各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。\\n\\n### 追加 6 動画\\n\\n工程塔 P\\\\*-21 は上の 15 動画に次の 6 動画を足す。\\n\\n    17, 18, 19, 20, 21, 22\\n\\n**用途は訓練のみである。どの折りの test にも val にも現れない。**\\n15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。\\n\\n### 規律\\n\\n**選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。\\ntest は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。\\n\\n出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-17-fold-table`。\\n\\n---\\n\\n<a id=\\\"symmetry\\\"></a>\\n## symmetry\\n\\n比較する腕の条件を、起票の前に並べて確かめる。差が出たとき、それを仮説の効果と読めるだけの対称性が\\n無ければ、その実験は測りたいものを測れない。\\n\\n### 対象\\n\\nexp 契約のすべて。比較の類型は三つ。\\n\\n| 類型 | 腕 | 例 |\\n|---|---|---|\\n| 塔どうし | 同じ役割の塔の候補、または方向で対になる塔 | 検出塔 D と工程塔 P、P の候補 A と B |\\n| 送り手と受け取り手 | 信号を出す塔と受ける塔 | P→D の P と D |\\n| 腕と分母 | 処置あり と 空入力 | 予測段の界面 と 空入力界面 |\\n\\n### 表の様式\\n\\nprereg.md に次の表を置く。列名はこのとおりにする（L3 の P13 が列名で表を探す）。\\n\\n| 条件 | 腕1 | 腕2 | 判定 | 理由 |\\n|---|---|---|---|---|\\n\\n判定は三値。**揃える**／**意図的に変える**／**UNKNOWN**。\\n「意図的に変える」には理由を書く。理由は次の三つに限る。\\n\\n1. 仮説の操作である\\n2. タスクの性質上避けられない\\n3. **各塔の構造の標準の処方である**（使い方は下の「各塔の構造の標準の処方」に従う）\\n\\n**UNKNOWN が一件でもある契約は起票しない。** 先に測る。\\n\\n### 各塔の構造の標準の処方\\n\\n理由 3 は、塔どうしで最適化の細部を揃えないことを認める。主判定の差（方向ごとの Δ）は、比べる腕と分母が\\n同じ受け取り手を持つので、塔どうしの最適化の差を含まない。揃えるのは塔の知識の出どころと収束規則である。\\n\\n| 項目 | 範囲 |\\n|---|---|\\n| 使える比較 | 類型「塔どうし」だけ |\\n| 使える行 | 正規化層の扱い、学習率、勾配の刈り込み、weight decay、実効 batch、数値精度、決定性 |\\n| 使える条件 | その塔どうしの差が、主判定（方向ごとの Δ）に入らないこと。つまり、比べる腕と分母が同じ受け取り手を持つ設計であること |\\n| 使えない行 | 初期化の鎖の各段、in-domain のデータの範囲、相手タスクのラベルを使わないこと、収束規則 |\\n\\n- **同じ塔の変種どうし**（確定塔、交差適合用の塔、診断点の塔）には使わない。変える一点（データか初期化）以外を揃える\\n- 理由 3 を使った行は、表の理由の欄に「各塔の構造の標準の処方」と書き、両腕の実際の値を書く\\n- 出所: 利用者の決定 2026-10-17（契約 `T-2026-10-17-tower-reselect-prereq` の SPEC §2）\\n\\n### 必ず置く行\\n\\n初期化の鎖の各段（ImageNet 分類、COCO 検出、中立 SSL、in-domain。段ごとに一行）／凍結範囲／\\n入力解像度と切り出し（画面の何割が残るか）／前処理・増強／教師の種類と密度／epoch と上限への張り付き／\\n学習率／実効 batch（単位が違うなら比較不能と書く）／数値精度／ヘッドの容量／ヘッドの epoch／評価 recipe。\\n\\n### 規則の読み\\n\\n規則の字面に複数の読みがあるとき、狭い読みを既定にしない。読みの候補を列挙し、利用者に諮る。\\n実測: 「P の初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、非対称を二周した。\\n\\n### 出所\\n\\nT-2026-09-19-symmetry-gate。実例は docs/symmetry-checklist.md。\\n\\n<a id=\\\"det_groups\\\"></a>\\n## det_groups\\n\\n検出の co-primary と陰性対照の集合。研究方針 v2 §7.3（2026-06-19 に EDA から事前登録。結果を見て選んだ群ではない）。\\n\\n| 群 | クラス | 用途 |\\n|---|---|---|\\n| 標的群 | Skewer、Bipolar Forceps、Scalpel、Syringe、Raspatory | 検出の co-primary（標的群 AP = 5 クラスの AP の平均） |\\n| 陰性対照群 | Gauze、Mouth Gag、Suction Cannula、Tweezers | Δ ≈ 0 であるべき群。動いたら交絡を疑う |\\n\\n- クラス名は検出塔の注釈と完全一致で照合する\\n- ある折りの評価集合に出現しないクラスは、その折りの群 AP から除き、除いたことを明記する。0 で埋めない\\n- AP rare（Skewer、Syringe）は副次指標として別に報告する\\n\\n<a id=\\\"crossfit\\\"></a>\\n## crossfit\\n\\n送り手の積み重ね漏れ（stacking leakage）の扱い。研究方針 v2 §9.4。閾値は利用者の決定（2026-09-27）。\\n\\n- 送り手が学習した train 動画で送り手が出す予測は過学習している。界面をその予測で学習すると、train と val・test で信号の質が違う\\n- **送り手の train 動画と val 動画の主指標の差が 3pt を超えれば、交差適合を適用する**\\n- 交差適合: 各折りの train 動画を動画単位で 2 分割し、一方で学習した送り手が他方に予測を出す。両方向で train 動画すべての予測を作る。\\n  val・test への予測は train 全体で学習した確定塔が出す\\n- 適用は送り手掃引の全点で統一する。主送り手だけに適用しない\\n- 交差適合版と非適用版の送り手の主指標を両方記録する\\n- 実測: 検出塔の送り手の差は約 11pt（Stage 0）。工程塔の送り手の差は T-2026-09-27-stage1-ptower-20 で測る\\n\\n<a id=\\\"frame_sets\\\"></a>\\n## frame_sets\\n\\n塔と界面が学習・評価に使うフレームの集合。数は `experiments/analysis/frame_signal_audit/REPORT.md` の実測。\\n\\n| 用途 | 集合 |\\n|---|---|\\n| 工程塔の学習と評価（主測定） | 動画 01〜15 の、工程注釈のある全フレーム（17,233。術具注釈の無い 1,796 を含む） |\\n| 検出塔の学習と評価 | 術具注釈のあるフレーム（15,437） |\\n| 工程の値（工程塔単独、D→P の予測段） | 工程注釈のある全フレーム。副次に、両タスクの注釈があるフレームでも出す |\\n| D→P の参照段（正解、正解と予測）と実現率 | 両タスクの注釈があるフレーム。比べる予測段の値も同じ集合で出す |\\n| P→D の界面の学習と評価 | 術具注釈のあるフレーム |\\n\\n### 規則\\n\\n- 各塔は、15 動画の折り（`conventions#folds`）の中にある自タスクの注釈を、すべて使う\\n- 追加動画 17〜21 は Stage 2 の主測定に入れない\\n- P→D の送り手を変えて測る比較に、**術具注釈のあるフレームだけで学んだ工程塔**を診断の一点として置く。関門の判定には使わない\\n- 出所: 利用者の決定 2026-10-16（契約 `T-2026-10-17-tower-reselect-prereq` の SPEC §2）\\n\","
  },
  {
    "path": "tasks/T-2026-10-19-evidence-maps-revise/SPEC.md",
    "line": 48,
    "text": "- パッチ: 受け渡しの名前 maps-2026-10-19.patch（62122 バイト、sha256 fc9922526166c232c2d423dc8f6376b3126f46ecf42814e6c94001944d912444）。**要約値で照合する。名前やバイト数だけで照合しない。** git の差分の形式で、三つの地図だけを変える。行の増減は C が追加 10・削除 9、B が追加 41・削除 40、N が追加 36・削除 12（起票者の手元での集計）"
  },
  {
    "path": "tasks/T-2026-10-19-evidence-maps-revise/SPEC.md",
    "line": 112,
    "text": "- B-3. 作業ツリーの変更が三つの地図だけであることを、git の変更の一覧（集合）で示す。行の増減を上の集計と並べる"
  },
  {
    "path": "tasks/T-2026-10-19-evidence-maps-revise/audit.md",
    "line": 121,
    "text": "git diff --name-only: 三つの地図だけ（未追跡の契約ファイルは別枠）。"
  },
  {
    "path": "tasks/T-2026-10-19-evidence-maps-revise/spec.yaml",
    "line": 39,
    "text": "    - {id: G2, after: B, check: \"パッチが当たり、改訂後の三つの地図の要約値が SPEC の表と一致し、変更が三つの地図だけ\", on_fail: stop}"
  },
  {
    "path": "tools/check_evidence_map.py",
    "line": 9,
    "text": "    python tools/check_evidence_map.py <地図>.md ...   # 指定した地図だけ"
  }
]
```

### 範囲外検索の分類と問い合わせ

全10行: 対象文書2行、範囲外の履歴3行、文脈上無関係5行。

```json
[
  {
    "path": "context/conventions.md",
    "line": 268,
    "classification": "変更対象の現行文書"
  },
  {
    "path": "docs/proposal-gate.md",
    "line": 38,
    "classification": "変更対象の現行文書"
  },
  {
    "path": "tasks/T-2026-09-16-proposal-gate/SPEC.md",
    "line": 213,
    "classification": "変更範囲外の履歴にある旧ルール"
  },
  {
    "path": "tasks/T-2026-09-16-proposal-gate/SPEC.md",
    "line": 262,
    "classification": "変更範囲外の履歴にある旧ルール"
  },
  {
    "path": "tasks/T-2026-10-19-conventions-and-defect-records/baseline.json",
    "line": 168,
    "classification": "変更範囲外の履歴にある旧ルール"
  },
  {
    "path": "tasks/T-2026-10-19-evidence-maps-revise/SPEC.md",
    "line": 48,
    "classification": "生成会話への入力とは無関係な語句一致"
  },
  {
    "path": "tasks/T-2026-10-19-evidence-maps-revise/SPEC.md",
    "line": 112,
    "classification": "生成会話への入力とは無関係な語句一致"
  },
  {
    "path": "tasks/T-2026-10-19-evidence-maps-revise/audit.md",
    "line": 121,
    "classification": "生成会話への入力とは無関係な語句一致"
  },
  {
    "path": "tasks/T-2026-10-19-evidence-maps-revise/spec.yaml",
    "line": 39,
    "classification": "生成会話への入力とは無関係な語句一致"
  },
  {
    "path": "tools/check_evidence_map.py",
    "line": 9,
    "classification": "生成会話への入力とは無関係な語句一致"
  }
]
```

範囲外の履歴は変更していない。これらを保持して報告へ列挙する扱いを利用者へ確認中。未追跡のexperiments二件も移動・削除せず、個別の.git/info/excludeへの追加を確認中。回答待ちのためPhase B以降は未実行、同期抑止は維持する。

## 利用者の追加判断

利用者の回答「yoi」を、直前に示した二点（実験ログ二件の個別除外・履歴三件の保持と報告）への許可として記録する。
.git/info/excludeの既存内容を保持し、次の二行だけを追加した。ファイルは移動・削除していない。戻すにはこの二行だけを除く。

```text
experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/eval_meta_val.json
experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/val_metrics_by_epoch.json
```

除外ファイルbefore sha256=623a73936202702d78b398f4f09b07bcefdb84cfc4a0e204577f1aa210c94fec / after sha256=24845f169f90d8418a3c70be64e9d0e190ad671cbffe8badd07d419d382bb090。実験ログ二件の内容ハッシュは操作前後で一致。
範囲外の履歴三行は変更せず最終報告へ列挙する。

## Phase B 文言の適用

生成の行・依頼文の六項目・変更履歴はSPECの文字列と照合して適用。B.3の一行を指定の三行へ置換し、指定行の末尾に依頼文の置き場を追記。雛形三行目だけに参照を追加。briefsディレクトリは作成していない。

## Phase C 文言・読みの照合

表は前後とも4行、生成の会話欄だけが変化。他の欄・批判/判定/起票の三行・表下の文は同一。指定の変更を逆に戻すと三文書とも基準全文へ完全一致するため、指定外の変更なし。

変更前の表:

| 生成 | 別会話。証拠地図だけを渡す | 提案カード三から五案。互いに排他的な方向 | 推奨・順位。repo の現状を見ること |
| 批判 | 別会話。カードだけを渡す | 却下表と順位。順位は期待情報量（#11）で付ける | 生成側の推奨文を読む |
| 判定 | 利用者 | 決定。F に一行 | — |
| 起票 | 別会話 | 契約 | 手法の変更 |

変更後の表（実ファイルから抽出）:

| 生成 | 別会話（プロジェクトの外）。証拠地図・カードの雛形・依頼文だけを渡す | 提案カード三から五案。互いに排他的な方向 | 推奨・順位。repo の現状を見ること |
| 批判 | 別会話。カードだけを渡す | 却下表と順位。順位は期待情報量（#11）で付ける | 生成側の推奨文を読む |
| 判定 | 利用者 | 決定。F に一行 | — |
| 起票 | 別会話 | 契約 | 手法の変更 |

依頼文の六項目はSPECから抽出した六項目と各文字列が完全一致:

### 生成会話への依頼文（2026-10-19 追加）

- 書いてよいものは二つ。F で状態が「有効」の決定の結論（行の日付を付ける）と、M の問い・判定規則。
- 書かないものは次のとおり。実測値、実装の状態、決定の理由のうち実装や実測に触れる部分、旧カード、報告者の解釈。
- 決定ごとに、どこまで縛るかを書く。カードの候補として開いているものも書く。
- 依頼文は渡す直前に F を読み直して、一から書く。前の依頼文を直して使わない。
- 依頼文は docs/proposals/briefs/ に置き、カードから参照する。
- 生成会話は、カード #10（費用）と #15（両腕の実測値）を UNKNOWN と書く。起票者が repo の実測で埋めてから批判会話へ回す。

変更後のB.3指定箇所:

```text
      → 起票者が依頼文を書く（conventions#proposal_gate「生成会話への依頼文」）
      → 生成会話（プロジェクトの外）: 地図・カードの雛形・依頼文から提案カード三から五案。#10 と #15 は UNKNOWN
      → 起票者が #10 と #15 を repo の実測で埋める
      → カードを docs/proposals/<YYYY-MM-DD>-<slug>.md に置き、check_proposal.py を通す。依頼文は docs/proposals/briefs/ に置く
```

雛形三行目:

生成会話: （題名）／批判会話: （題名）／判定: 利用者（日付）／出所の証拠地図: docs/evidence/...／依頼文: docs/proposals/briefs/...

検査器の読取値は前後で全要素一致。禁止語15、カード16、数値必須5/6/10。precision節の位置に依存して読みが変わらないことも実測した。

命令: .venv/bin/python tools/check_proposal.py docs/proposals/2026-09-27-ptower-20.md --json

```text
{
  "status": "pass",
  "path": "docs/proposals/2026-09-27-ptower-20.md",
  "only": "both",
  "words_checked": 15,
  "card_items": 16,
  "numeric_items": [
    5,
    6,
    10
  ],
  "hits": 0,
  "hits_by_kind": {
    "forbidden_word": 0,
    "missing_heading": 0,
    "missing_number": 0
  },
  "findings": [],
  "errors": []
}
exit=0
```

命令: .venv/bin/python tools/check_proposal.py docs/proposals/_template.md --json

```text
{
  "status": "fail",
  "path": "docs/proposals/_template.md",
  "only": "both",
  "words_checked": 15,
  "card_items": 16,
  "numeric_items": [
    5,
    6,
    10
  ],
  "hits": 3,
  "hits_by_kind": {
    "forbidden_word": 0,
    "missing_heading": 0,
    "missing_number": 3
  },
  "findings": [
    {
      "kind": "missing_number",
      "line": 36,
      "detail": "カード #5（期待効果量（点））の本文に数字が無い"
    },
    {
      "kind": "missing_number",
      "line": 38,
      "detail": "カード #6（成功確率（主観）の本文に数字が無い"
    },
    {
      "kind": "missing_number",
      "line": 46,
      "detail": "カード #10（費用（run 本数 × 時間））の本文に数字が無い"
    }
  ],
  "errors": []
}
exit=1
```

### 費用UNKNOWNの陽性対照

既存カードの見出し##10と##11の間の本文だけをUNKNOWNへ置換した写しを本契約内へ保存（元カードは変更していない）。

```text
{
  "status": "fail",
  "path": "tasks/T-2026-10-19-proposal-gate-brief/positive-cost-unknown.md",
  "only": "both",
  "words_checked": 15,
  "card_items": 16,
  "numeric_items": [
    5,
    6,
    10
  ],
  "hits": 1,
  "hits_by_kind": {
    "forbidden_word": 0,
    "missing_heading": 0,
    "missing_number": 1
  },
  "findings": [
    {
      "kind": "missing_number",
      "line": 63,
      "detail": "カード #10（費用（run 本数 × 時間））の本文に数字が無い"
    }
  ],
  "errors": []
}
exit=1
```

命令: .venv/bin/python -m pytest tests/test_check_proposal.py tests/test_proposal_card_gate.py --junitxml=tasks/T-2026-10-19-proposal-gate-brief/tests-after.xml -q

```text
...............................................                          [100%]
47 passed in 0.97s
exit=0
```

## G2 変更範囲の保留と除外の優先順位

内容検証、読取値、47試験、残存検索は合格したが、範囲確認は実験ログ二件が未追跡に残ってassert失敗。続けて実行された契約指定forbidden-checkは違反2件・make exit2。規約の許可自体はpermittedとして報告された。

git check-ignore -v --non-matching の実測:

```text
.gitignore:116:!experiments/**/logs/eval_meta_*.json	experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/eval_meta_val.json
.gitignore:115:!experiments/**/logs/val_metrics_by_epoch.json	experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/val_metrics_by_epoch.json
```

.git/info/excludeの二行は存在するが、.gitignoreの再包含規則が優先される。元の判断ではこの優先順位の確認が不足した。実験ログは移動・削除していない。

提案は.gitignore末尾への二行だけ。契約範囲を広げるため、適用せず利用者へ確認する。戻し方は追加する二行だけを除くこと。共有される.gitignoreのため全ホストで同じ二経路の除外になる。

```diff
--- a/.gitignore
+++ b/.gitignore
@@ -253,3 +253,5 @@
 experiments/baselines/stage1_dtower/*/train.log
 experiments/baselines/stage1_dtower/*.boot.log
 experiments/baselines/stage1_dtower/*/eval_*.log
+/experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/eval_meta_val.json
+/experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/val_metrics_by_epoch.json
```

repo外の隔離した写し /tmp/m2-exclude-control-sl2bpe9j で元の.gitignoreにこの二行だけを足してgit check-ignore -vを実行。応答:

```text
.gitignore:256:/experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/eval_meta_val.json	experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/eval_meta_val.json
.gitignore:257:/experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/val_metrics_by_epoch.json	experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/val_metrics_by_epoch.json
exit=0
```

## .gitignore二行追加の許可と適用

利用者は「二行だけの .gitignore 追加を許可する」と明示。gitignore-exact-logs.patchをgit apply --check後に適用（両方exit0）。git check-ignore -vは.gitignore末尾の個別二経路を返した。実験ログの移動・削除なし。

追加許可を含む変更範囲の集合を再照合し、範囲外0件。

```text
.gitignore
context/conventions.md
docs/proposal-gate.md
docs/proposals/_template.md
tasks/T-2026-10-19-proposal-gate-brief/RESULT.md
tasks/T-2026-10-19-proposal-gate-brief/SPEC.md
tasks/T-2026-10-19-proposal-gate-brief/audit.md
tasks/T-2026-10-19-proposal-gate-brief/baseline.json
tasks/T-2026-10-19-proposal-gate-brief/gitignore-exact-logs.patch
tasks/T-2026-10-19-proposal-gate-brief/positive-controls.json
tasks/T-2026-10-19-proposal-gate-brief/positive-cost-unknown.md
tasks/T-2026-10-19-proposal-gate-brief/result.yaml
tasks/T-2026-10-19-proposal-gate-brief/search-after.json
tasks/T-2026-10-19-proposal-gate-brief/search-before.json
tasks/T-2026-10-19-proposal-gate-brief/search-classification.json
tasks/T-2026-10-19-proposal-gate-brief/spec.yaml
tasks/T-2026-10-19-proposal-gate-brief/tests-after.xml
tasks/T-2026-10-19-proposal-gate-brief/tests-before.xml
tasks/inbox.d/T-2026-10-19-proposal-gate-brief.md
```
既存カードと検査器のSHA-256は基準と一致。

## G2 最終判定

G2 pass。ユーザー承認済みの.gitignore追加を含む範囲へ再照合し、範囲外0。forbidden-check TASK指定: exit0 / status=pass / violations=[]、規約は契約allow_writeでpermitted。spec-check TASK指定: exit0 / hits0 / rules9。git diff --check: exit0。内容・読取値・対照・試験は直前に測定した前後同一の結果。

## Phase D 変更履歴のcommit記入

規約変更commit=e1364772ab5fe9c97d0578bc8aa9d459c9599033。その後のcommitで変更履歴の欄へe1364772を記入。git show --format= --name-only e1364772 -- context/conventions.md は context/conventions.md を返した。規約を変えたcommitを指すことを確認。

命令: make forbidden-check TASK=T-2026-10-19-proposal-gate-brief

```text
{"base": "origin/phase0", "changed": 19, "checked": 19, "declared_allowances": ["context/conventions.md", "docs/proposals/"], "effective_allowances": ["context/conventions.md", "docs/proposals/"], "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "permitted": [{"path": "context/conventions.md", "reason": "契約の allow_write context/conventions.md により許可"}], "rejected_allowances": [], "status": "pass", "task": "T-2026-10-19-proposal-gate-brief", "violations": []}
exit=0
```

命令: make spec-check TASK=T-2026-10-19-proposal-gate-brief

```text
{
  "errors": [],
  "findings": [],
  "hits": 0,
  "hits_by_rule": {
    "allow_write_incomplete": 0,
    "forbidden_vs_output": 0,
    "gate_requires_report_before_end": 0,
    "host_mismatch": 0,
    "integration_prohibited_without_pause": 0,
    "reverify_contradiction": 0,
    "separated_source": 0,
    "truncation_in_measurement": 0,
    "unquoted_glob": 0
  },
  "rules_checked": 9,
  "status": "pass",
  "targets": 1
}
exit=0
```

命令: git diff --check

```text
exit=0
```
