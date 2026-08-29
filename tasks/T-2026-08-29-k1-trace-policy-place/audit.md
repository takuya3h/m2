# audit — T-2026-08-29-k1-trace-policy-place

証跡の記録。命令とその出力・捜索の過程・対照の出力・試験バンドルの内容。
事実の記録は `RESULT.md`。**同じ内容を二度書かない。**

実行ホスト `philip` / repo `/home/ubuntu/slocal2/m2` / 分岐 `feat/k1-trace-policy-place`

---

## 取り込みと検証

一度、作業ツリーの汚れ（`.sync-pause.released` 1 件）で止まった。退避してから再実行し exit 0。

    開始時刻: JST 2026-08-29 09:21:05 / epoch=1787962865
    起点: 5cc26050 Merge pull request #162 from takuya3h/feat/stage0-contract-a

    事前記入値の照合: runindex_commit 7918b5dd（一致）/ conventions_rev a8c07e81（一致）
                      counts index 1177 / experiments 213 / verdicts 1038（一致）→ 置換不要

    $ make task-validate  → OK / exit=0（WARN 無し）
    $ make task-preflight → 5 PASS / 0 WARN / 4 SKIP / 0 FAIL / exit=0
      SKIP は P2 P3 P4 P5。**「合格」ではなく実行されていない。**

---

## Phase A — K1 数値の初出の再捜索

### 試した表現の揺れ（一覧）

    -0.0201  0.0201  -0\.0201  2.01  2.01pt  -2.01
    0.801  0.179  0.686  68.6  80.1  17.9
    複合: '0.801→0.179'（矢印なし）/ '0.801 → 0.179'（空白つき矢印）

**試していない揺れ**: 有効数字を増やした形（例 -0.02010）、指数表記、
百分率での小数点以下 2 桁（例 2.010%）。これらは「探した」に数えない。

### 検索器の対照

    陽性: git log --all -S'0.050877'  → **4 commit**（前契約で実在が確定した値）
    陰性: git log --all -S'0.3971428571' → **0 commit**
    陰性: git log --all -S'-0.8264193'   → **0 commit**

**検索器は働いている。** 以降の零件は「検出できていない」ではない。

### 系統 1 版管理の全履歴

| 値 | `-S` で該当する commit 数 | 初出 |
|---|---|---|
| `0.0201` | 19 | 2a9ebb1d 2026-05-24 |
| `0.801` | 48 | 86d4427c 2026-05-07 |
| `0.179` | 28 | 2a9ebb1d 2026-05-24 |
| `0.686` | 37 | 2a9ebb1d 2026-05-24 |

**単独の数値は多数出るが、K1 の文脈ではない**（例: `docs/research_review_...md:1568` の
`+0.0201` は「GT ⊕ 生」の macro-F1 で**符号が逆**、別の実験）。

**K1 の対として（`0.801→0.179`）現れる初出:**

    909dd193  2026-08-02  chore(experiments): collect frozen_source_signature3_R_index analysis (24KB)
      experiments/analysis/frozen_source_signature3_R_index/REPORT.md:52

**この初出の本文（典拠を一段遡る）:**

    2. **hemostasis F1「0.801→0.179」の downstream 数値の直接検証**:
       `experiments/phase1/s4_phase_baseline_01{0,1,2}_frozen_tecno_phase_baseline_aligndetr_seed*`
       は checkpoints/logs/predictions/visualizations のみで metrics.json が空（efros で実行された空 scaffold）。
       **台帳記載値のみで、per-phase F1 の生数値はこのホストでは再現できない**

🔴 **初出の時点で既に「台帳記載値のみ」と書かれている。** この文書は数値の出所ではなく、
**出所が無いことを報告している文書**である。典拠の連鎖はここで止まる（これ以上遡る先が無い）。

### 系統 2 生ログとメトリクスの直接走査（索引を経由しない）

**限定した範囲**: `experiments/phase1/s4_phase_baseline_01{0,1,2}_frozen_tecno_phase_baseline*`
（aligndetr 群 3 件と対応する分母 3 件）。理由: 台帳の記述が名指ししている run である。

🔴 **文書の記述「metrics.json が空」は philip では成り立たない。実体がある。**

    s4_phase_baseline_010_..._aligndetr_seed42   metrics.json 918 B / per_class_ap.json 274 B
    s4_phase_baseline_011_..._aligndetr_seed123  metrics.json 918 B / per_class_ap.json 258 B
    s4_phase_baseline_012_..._aligndetr_seed456  metrics.json 920 B / per_class_ap.json 256 B

**config が宣言する凍結条件（重要）:**

    aligndetr 群 3 件とも  test_cfg.backbone = relation_detr_resnet50_frozen_seed42
    分母側     3 件とも  test_cfg.backbone = relation_detr_resnet50_frozen_seed42

🔴 **名前は `aligndetr` だが、config の backbone は Relation-DETR の凍結源である。**
これが 2026-07-03 の「AlignDETR 学習失敗 → 通常学習の ckpt で代替」の実体であり、
索引が `n_runs_excluded=3` として無効判定した根拠と整合する。

**hemostasis の per-phase F1（生値）:**

    aligndetr: seed42 0.16666666666666666 / seed123 0.0 / seed456 0.0
    分母    : seed42 0.34782608695652173 / seed123 0.3333333333333333 / seed456 0.125

**台帳の 0.801 にも 0.179 にも一致しない**（許容差 ±5e-4）。

**accuracy と Δ_phase（生ログから直接計算）:**

    分母(relation_detr): 0.900330 / 0.908251 / 0.886469  平均 0.898350
    aligndetr        : 0.856766 / 0.842244 / 0.840264  平均 0.846425
    Δ_phase = -0.051925
    台帳の -0.0201 との差 = 0.031825

    seed ごとの対の差: -0.043564 / -0.066007 / -0.046205（**どれも -0.0201 ではない**）

索引経由の前契約の値（-0.050877）とわずかに違うのは、索引が母集団に含める run の範囲が
異なるためである。**いずれにせよ -0.0201 とは 0.03 以上離れている。**

### 系統 3 外部の実験記録（読み取りのみ）

**照会できた。** 環境に設定済みの資格情報の範囲で読み取りのみ実行し、
**新規の設定・書き込み・資格情報の出力は行っていない。**

    走査した run: 479
    K1 の値に一致（±5e-5 / ±5e-4）: 3 件
      frozen_tecno_grasp_inference_inj_seed456        phase_macro_f1 = 0.6857927551282464  (target 0.686)
      frozen_tecno_grasp_inference_inj_standar...     phase_jaccard  = 0.6858897291925616  (target 0.686)
      frozen_tecno_grasp_inference_inj_standar...     phase_jaccard  = 0.6856640216000025  (target 0.686)

**3 件とも `grasp_inference` の別実験**であり、AlignDETR の検出性能ではない。
**`-0.0201` `0.801` `0.179` は 0 件。**

### 系統 4 リポジトリ内の文書・スライド・ノート（現在版）

`0.801` と `0.179` の両方を含む版管理下の文書は 11 件。出所記述の有無で分類する。

| 文書 | 出所の記述 |
|---|---|
| `experiments/analysis/frozen_source_signature3_R_index/REPORT.md:52` | **「台帳記載値のみ」と明記**（＝出所を持たない） |
| `docs/experiment_log.md:2068` | 同じ趣旨を引用 |
| `docs/history/README_log_2026-05_to_2026-08.md:409` | 同じ趣旨を引用 |
| `docs/stage0/A7_k1_provenance.md` | 前契約の照合結果（本契約の前段） |
| `tasks/T-2026-08-29-stage0-contract-a/{RESULT,SPEC,audit}.md`、`tasks/inbox.d/...`、`tasks/inbox.md` | 前契約の記録 |
| `context/auto/{followups,results_recent}.md` | 前契約の報告からの投影（生成物） |

**出所を主張している文書は一つも無い。** すべてが「台帳にある」と述べるか、
前契約の照合結果を引いているだけである。

### 結論（二値）

**遡れない（確定）。**

四系統すべてで、K1 の三値を**同時に**説明する出所は見つからなかった。
初出（909dd193）は数値の出所ではなく、**出所が無いことを報告している文書**である。

**互いに矛盾する複数の出所へは遡っていないため、escalate の条件に当たらない。**

---

## Phase B Task 1 — 方針文書の配置（**実行できず停止**）

### 取得と検証

    行 T-2026-08-28-policy-v2-doc-sync の property sha256（宣言）: 182d152ff00c4549…
    添付: あり
    取得物の要約値（実測）                                    : 182d152ff00c4549…
    一致: 🟢  取得物の大きさ: 19354 バイト

**取得物全体の要約値は一致した。** 改竄はされていない。

### 区画への分割

    一行目: #!TASK-BUNDLE v1 delim=BUNDLE-378eef9428be1d5d47c05f41c7ba8b75655bee72（47 文字）

    区画の標識:
      行2   FILE spec.yaml
      行58  FILE SPEC.md
      行321 END

    parse_bundle が返した区画: ['spec.yaml', 'SPEC.md']
      spec.yaml : 2267 バイト  sha256 5edcfc2c67d937e2…
      SPEC.md   : 16840 バイト  sha256 e118137cf0dafddc…

🔴 **バンドルは二区画しか持たない。三つ目の区画 `research_policy_v2_2026-08-28.md` は存在しない。**

**陽性対照**: 同じ抽出器（`ft.parse_bundle`）が実在する二区画は正しく取り出せている。
→ **抽出器は働いている。** 三区画目の不在は抽出の失敗ではない。

### SPEC の宣言値の照合

SPEC §1 は「バンドル内の三つ目の区画 … の要約値と大きさは、**同バンドル内の SPEC.md の §1 に宣言済み**
（短縮形で 2eb9c882、60490 バイト）」とする。**旧バンドル内 SPEC.md の §1 の全文:**

    ## 1. 確定している事実（ホストに依存しない値のみ）

    - 方針 v2 の正本は外部の記録場所（研究計画の子ページ「研究方針 v2」）にある。
      **実行者はそこへ到達できない前提で書く。** 書くべき内容はすべて §1.2 に列挙してある
    - README とCLAUDE.md の現在の内容・構造は、起票者は投影経由の抜粋でしか見ていない。
      節の実在・見出しの文言・行の範囲は**すべて実行者が現物で実測する**こと

🔴 **`2eb9c882` も `60490` も `research_policy_v2` の文字列も、旧 SPEC.md のどこにも無い**
（正規表現で全文走査して 0 件）。**宣言値そのものが存在しない。**

### 他の行の確認（別経路の可能性）

    T-2026-08-28-policy-v2-doc-sync : 添付あり 19354 バイト（上記）
    T-2026-08-29-stage0-contract-a  : 添付あり 16075 バイト
    T-2026-08-29-k1-trace-policy-place: 添付あり 16044 バイト

いずれも二区画のバンドルであり、方針文書の本文を含む添付は無い。

### 判断

SPEC §7 の「旧バンドルの添付が取得できない・要約値不一致 → **配置せず停止して報告**
（Phase A と Task 2・3 は続けてよい。**部分完了として報告**）」に従う。

**配置していない。手で本文を書き起こしてもいない**（禁止 1「配置する方針文書本文の編集」と
整合性の要求から、存在しない本文を創作することは許されない）。

---

## Phase B Task 2 — 取り込みの追加ファイル対応

### 設計

`spec.yaml` の `inputs.bundle_extras` に {経路・要約値・大きさ} を宣言する方式にした。
**宣言が無ければ従来どおり三種のみ**（後方互換）。

実装上の要点（`tools/fetch_task.py`）:

- `parse_bundle` から許可判定を外した。**追加ファイルの可否は spec.yaml を読まないと決まらない**
  ため、順序を逆にできない。経路の形（`_EXTRA_PATH_RE`）だけは先に拒み、脱出を後段へ持ち越さない
- `extras_from_spec` が宣言を読む。**宣言の形が壊れていたら取り込みを止める**
  （黙って無視すると、宣言したつもりのファイルが未宣言として弾かれ原因が読めなくなる）
- `check_extras` が四つを拒否する: 未宣言の区画・宣言された経路の欠落・要約値の不一致・大きさの不一致
- `pack_bundle` も同じ基準を使う。**組み立ての順序を固定**した（同じ入力から同じバンドルが出る）
- 設置は経路を持つファイルに対応（親を作ってから書く）

### 判定 c の三対照（試験バンドルは版管理に入れていない）

    === 陽性: 宣言済み追加ファイルつきバンドル ===
      区画: ['SPEC.md', 'extra_doc.md', 'spec.yaml']
      → 検証を通過 🟢

    === 陰性1: 未宣言の区画 ===
      拒否 🟢: 宣言されていないファイルです: 'extra_doc.md'（spec.yaml の inputs.bundle_extras に宣言してください）

    === 陰性2: 要約値を改竄した追加ファイル ===
      拒否 🟢: 追加ファイルの要約値が宣言と一致しません: extra_doc.md

    === 判定 d 後方互換: 三種のみの既存形式 ===
      区画: ['SPEC.md', 'spec.yaml']  宣言: {}
      → 通過 🟢

### 判定 d 実在するバンドルでの後方互換

    T-2026-08-29-k1-trace-policy-place  区画 ['SPEC.md','spec.yaml'] → 検証通過 🟢
    T-2026-08-28-policy-v2-doc-sync     区画 ['SPEC.md','spec.yaml'] → 検証通過 🟢
    T-2026-08-29-stage0-contract-a      区画 ['SPEC.md','spec.yaml'] → 検証通過 🟢

**既存の三バンドルとも従来どおり通る。**

### 試験の途中で見つけた自分の誤り

最初の試験で陽性対照が落ちた。`pack_bundle` の組み立てループが `ALLOWED_FILES` のみを
回っており、宣言済みの追加ファイルを詰めていなかった。**検証側だけ直して組み立て側を
見落としていた。** 直してから四試験とも通した。

また、要約値の数え方を `parse_bundle` の正規化（末尾の改行を 1 つに揃える）と
揃えないと必ず不一致になる。**この規約を tasks/README.md に明記した。**

---

## Phase B Task 3 — Stage 0 記録の完成

    A3 追記: 削除行 0（追記のみ）  sha256 6e42bebf… → 8dfe1e33…
    A7 追記: 削除行 0（追記のみ）  159 行
    A9 新設: 38 行
    総括新設: 44 行（相対リンク 10 件すべて実在）

### 判定 f 三種の出所の種別

    docs/stage0/A7_k1_provenance.md:87   出所の種別: リポジトリ内の実測（系統 1・2・4）と外部の実験記録の読み取り照会（系統 3）
    docs/stage0/A3_attribute_overlap.md:48 出所の種別: 利用者経由の提供元回答。リポジトリ内の実測ではない
    docs/stage0/A9_inference_protocol.md:3 出所の種別: 起票者の文献確認（2026-08-29）。リポジトリ内の実測ではない

**三種すべてが実際に現れている。**

---

## Phase C 検査

    $ make docs-check       → exit=0（対象 42 文書・食い違いなし）
    $ make agent-check      → exit=0（targets 107・violations 0）
    $ make forbidden-check  → exit=0（changed=9 checked=9 violations=0）

    リンク検査（README.md / tasks/README.md / docs/stage0/*.md）
      相対リンク 57 件 / 実在しない 0 件  exit=0
    空振り確認: 実在しない経路 zzz_no_such.md を含む一時複製 → 検出 exit=1（複製は削除）

### 変更範囲

     M docs/stage0/A3_attribute_overlap.md
     M docs/stage0/A7_k1_provenance.md
     M tasks/README.md
     M tools/fetch_task.py
    ?? docs/stage0/A9_inference_protocol.md
    ?? docs/stage0/stage0_summary.md
    ?? tasks/T-2026-08-29-k1-trace-policy-place/

**§2 の対象のみ。対象外 0 件。**

    読み取り専用: experiments 0 件 / data 0 件 / runindex 0 件
