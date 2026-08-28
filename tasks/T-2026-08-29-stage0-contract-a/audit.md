# audit — T-2026-08-29-stage0-contract-a

証跡の記録。命令とその出力・照合の過程・対照の出力。事実の記録は `RESULT.md`。
**同じ内容を二度書かない。**

実行ホスト `philip` / repo `/home/ubuntu/slocal2/m2` / 分岐 `feat/stage0-contract-a`

---

## 取り込み

一度、作業ツリーの汚れ（`.sync-pause.released` 1 件）で止まった。退避してから再実行し exit 0。

    開始時刻: JST 2026-08-29 05:03:58 / UTC 2026-08-28T20:03:58Z / epoch=1787947438

---

## Step A-0 承認済みの退避の処分

### drop 前の一覧

    stash@{0}: On feat/projection-refresh: T-2026-08-29-stage0-contract-a: 契約開始前から在った .sync-pause.released（0B・前契約の判断待ち対象）
               作成 2026-08-28 20:03:42 / 追跡済み 0 件 / 未追跡 1 件
    stash@{1}: On feat/issuer-refs-to-repo: T-2026-08-29-projection-refresh: 契約開始前から在った汚れの退避（.stglobalignore の変更 + 未追跡 7 件）
               作成 2026-08-28 18:13:58 / 追跡済み 1 件 / 未追跡 23 件
    stash@{2}: On feat/error-shape-selectivity: pre-oracle-ceiling-lovo
               作成 2026-08-26 06:26:01 / 追跡済み 0 件 / 未追跡 10 件
    件数: 3

🔴 **SPEC §1 は「philip には退避が二件残っている」とするが、実測は三件だった。**
三件目（`stash@{0}`）は**本契約の取り込み直前に実行者が作ったもの**で、
中身は `.sync-pause.released` 1 件（前契約が「判断待ち」とした対象そのもの）。
利用者へ提示し、**三件とも drop する**回答を得た。

### drop 後

    $ git stash drop 'stash@{0}'  ×3
    Dropped stash@{0} (c854b5c5882b5ff13a3a7ae81a92a5bc54b4e914)
    Dropped stash@{0} (1eeab75ef71dff16acb26dab3d80da5122e3818e)
    Dropped stash@{0} (1c3b0b62e2422e42775d8af65fe2e32228832397)

    $ git --no-pager stash list
    件数: 0

**判定 f: drop 前 3 件 → 後 0 件。**

---

## Step A-1 事前記入値の照合

| 項目 | spec.yaml の記載 | 現物の実測 | 判定 |
|---|---|---|---|
| `runindex_commit` | `7918b5dd` | `7918b5dd` | 🟢 一致 |
| `conventions_rev` | `a8c07e81` | `a8c07e81` | 🟢 一致 |
| `counts` | index 1177 / experiments 213 / verdicts 1038 | 同一 | 🟢 一致 |

**置換不要。** SPEC の指示どおり短縮形のままにした。

    $ make task-validate TASK=T-2026-08-29-stage0-contract-a
    OK / 1 task(s), 0 failed / validate exit=0（WARN 無し）

### L3（回答前）

    P6 decisions_answered  FAIL 未回答 2 件: Cholec80 … ; K1 の出所照合の結果を方針文書へどう反映するか
    RESULT: 4 PASS / 0 WARN / 4 SKIP / 1 FAIL / preflight exit=2

**2 件とも実測が出てから初めて答えられる性質のため、Phase A/B を先に進めてから提示した。**

### L3（回答後）

    P6 decisions_answered  PASS decisions_required は空
    RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL / preflight exit=0

**SKIP は「合格」ではない。** P2 P3 P4 P5 は実行されていない。

### 解決した参照

    conventions#prohibitions      277 B / sha256 bc032d4d…
    conventions#issuer_cautions  1012 B / sha256 512f7bf5…
    conventions#naming            526 B / sha256 74956a03…

`inputs.data.split_files` は様式を満たすための記載であり、**本契約は分割の再定義をしていない**
（A4 では既存の分割ファイルの train 内で測った）。

---

## Step A-2 入力データの所在

全表は `docs/stage0/A0_data_inventory.md`。要点のみ。

    追加動画の探索:
      data/raw/OpenSurgery_Dataset/README.md:
        「動画 16〜22 は phase / tool_presence の CSV は存在するが、セグメンテーションは存在しない」
      $ ls .../annotations/phase/ | grep -E '^(1[6-9]|2[0-2])_'
        17_1 18_1 18_2 19_1..19_6 20_2,20_4..20_8 21_1..21_5 22_1..22_3
        動画数: 6（17,18,19,20,21,22）/ クリップ数: 23
      **16 は phase CSV が存在しない。** SPEC の「追加 6 動画」と実測が一致する。

    方針文書 research_policy_v2_2026-08-28.md:
      $ find . -iname '*policy*v2*' -o -iname '*research_policy*'
        ./tasks/T-2026-08-28-policy-v2-doc-sync
        ./tasks/inbox.d/T-2026-08-28-policy-v2-doc-sync.md
      **本体は未配置**（契約ディレクトリ名の一致のみ）。
      README の相対リンク 36 件はすべて実在（`docs/history/...` を含む）。

    Cholec80:
      $ find / -maxdepth 6 -iname '*cholec80*' → 0 件
      陰性対照 '*zzznosuchdataset*' → 0 件、`data/external/weights/` → 35 ファイル
      → 探索は働いている。**philip に無い。**

---

## Phase B の実測

各項目の全表は `docs/stage0/` に置いた。ここには対照と手続きの要点のみ記す。

### A2 の陰性対照

    追加動画の集合に公式 test の `04` を混ぜて同じ集合演算 → 1 件（04）
    → 演算は重複を検出できる。実測の 0 件は「検出できていない」ではない。

### A3 の陽性対照

    `annotations.json` の images のキーから "file" を含むものを探す → ['file_name']
    → キー検索は働いている。surgeon/patient/case/subject/operator の 0 件は本物。

    data/splits/surgeon_folds.json: 3 バイト（`{}`）
      作成 commit: af1fc587 2026-05-21 "Scaffold egosurgery_multitask project structure"
    **scaffold 以来一度も中身が入っていない。**

### A4 の分割の扱い

val/test は動画単位で分かれておりクリップIDが train と重ならないため、
**分割の再定義を避けて** train 内を frame_id 昇順で偶数/奇数に決定的に二分した。

### A6 の基準の出所

    src/egosurgery/metrics/detection.py:184-226 `_compute_similar_confusion`
      「各 GT box を、最も IoU の高い予測 box（IoU >= 0.5）にマッチさせる」
    → **局在の合否は IoU 0.5。既存実装の値であり発明していない。**

    実行者が置いた値（既存実装に無い）:
      IoU 0.1 … 「予測が全く無い」と「ズレている」を分ける下限
      score >= 0.05 … mmdet の既定値。`eval_recipe.py:41` の論文設定 1e-8 では
                      1 画像あたり数百件の低スコア予測が残り最大IoUマッチが常に成立するため
    **どちらも実行者の判断である。結果の解釈に影響する。**

### A7 照合器の対照

    陽性: target=0.8973014948553679（分母の accuracy_mean）→ **1 件一致**
          phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42
    陰性: target=-0.0202 → **0 件**
    陰性: target=-0.0200 → **0 件**
    → **照合器は働いている。**

    許容差の根拠:
      Δ_phase の表示は 4 桁（-0.0201）→ 丸め前の実数は ±5e-5 の幅
      F1 の表示は 3 桁（0.801 / 0.179）→ ±5e-4
      **丸め表示を実数として扱っていない。**

    走査対象: experiments.csv 213 行 / index.csv 1177 行 / verdicts.csv 1038 行 / per_class.csv 8370 行

### A7 の系統別の実測

    系統1（無効判定の aligndetr 群）:
      phase1/s4_phase_baseline/frozen_tecno_phase_baseline_aligndetr@val~aligndetr...
        n_runs=3  n_runs_excluded=3  ← **全件が除外扱い**
        accuracy_mean=0.8464246424642464
        分母 0.8973014948553679 との差 Δ = -0.050877
        台帳の -0.0201 との差 = 0.030777（許容差 ±5e-5 の 600 倍以上）
      per_class の hemostasis F1（3 seed）: 0.0 / 0.16666… / 0.0（いずれも excluded=True）
      → **Δ も F1 も一致しない。**

    系統2（2026-07-10 以降の作り直し版）:
      索引に aligndetr を含む experiments 行は 2 件のみ
        baselines/s0/aligndetr_bbox@val （accuracy_mean が空）
        phase1/s4_phase_baseline/frozen_tecno_phase_baseline_aligndetr@val~...
      → **作り直し版として区別できる別行が索引に存在しない。**

    系統3（それ以外の一致）:
      per_class.csv 全走査で hemostasis F1 = 0.179 に一致する行が **1 件**
        ledger_key = transfer__b2a_ro_oracle_noise000_009_b2a_ro_oracle_noise000_seed456
        group/step = transfer / b2a_ro_oracle_noise000
        seed=456 split=val host=lecun excluded=False value=0.1794871794871795
      同じ step の hemostasis F1（seed 別）: 0.827 / 0.637 / 0.179 / 0.0 …とばらつく
      → **AlignDETR とは無関係のノイズ注入実験の 1 run。`0.801 → 0.179` の対を構成しない。**

      0.801 に一致した 9 件はいずれも別クラス
        （Suction Cannula / incision / Mouth Gag / Raspatory）。**hemostasis ではない。**

    AlignDETR の検出性能 0.686:
      baselines/s0/aligndetr_bbox@val の accuracy_mean は**空**。索引から特定できない。

---

## Phase C 完了判定

### 判定 c 出所の追跡（無作為に三つ）

    数値1: A1 の 動画14 dissection = 1352
      再計算: data/annotations/egosurgery_phase/14_*.csv から 1352  🟢 一致
    数値2: A5 の hemostasis の Σ H_b = 7.2284
      再計算: oracle_toolpresence + egosurgery_phase から 7.2284  🟢 一致
    数値3: A6 の分類誤り = 248
      出所: val_ctrl_best.json.gz + instances_val.json（IoU>=0.5・score>=0.05）
      基準は docs/stage0/A6_error_decomposition.md に明記

### 判定 e 読み取り専用

    experiments/ の変更: 0 件
    data/       の変更: 0 件
    runindex/   の変更: 0 件

    空振り確認（変更のある場所へ同じ検査）:
      docs/stage0                          の変更: 1 件
      tasks/T-2026-08-29-stage0-contract-a の変更: 1 件
    → **検査は働いている。**

### 判定 d 変更範囲

    $ git --no-pager status --porcelain
    ?? docs/stage0/
    ?? tasks/T-2026-08-29-stage0-contract-a/

**§2 の対象（docs/stage0/）と契約ディレクトリのみ。対象外 0 件。**
