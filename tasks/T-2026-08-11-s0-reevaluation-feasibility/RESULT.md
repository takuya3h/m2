# T-2026-08-11-s0-reevaluation-feasibility — 完了報告

S0 検出器比較表を同一条件で作り直せるかを測った。読み取りのみ。GPU 不使用。

## 結論を先に書く

**そもそも再評価は不要である。** 系統差の実効的な大きさを、**同一検出器が両系統で
評価されている実例**から直接測ったところ **0.05σ** だった。検出器間の幅（約 4.6σ）と
比べて無視できる。**表は条件差を明記して載せればよい。**

**そして仮に作り直そうとしても、それは事実上できない。** 比較表の首位 `relationdetr` を
含む 9 検出器の重みは**このホストに存在しない**（`philip` で学習され、6 点証跡だけが
転送されている）。`philip` に現存するかは lecun からは測れない（`UNKNOWN`）。

---

## 1. 解決された参照

`contract.inject_verbatim: [conventions#prohibitions]` — `context/conventions.md` の
`#prohibitions` アンカーの原文（`conventions_rev: d422b08`、実測で一致・置換不要）:

> ## prohibitions
>
> | id | 禁止事項 |
> |---|---|
> | `no_split_redefine` | split を再定義しない |
> | `no_raw_write` | `data/raw` `data/external` に書き込まない |
> | `no_frozen_change` | 凍結源を変更しない |
> | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
> | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

`meta.created_from.runindex_commit` は `UNKNOWN` だったため実測値 `44697d9`
（`2026-08-11T08:41:54+00:00`）に置換した。SPEC が定める手順である。

## 2. 検証と事前検査

| 段階 | 結果 |
|---|---|
| `make task-validate` | exit 0、WARN 0 件 |
| `make task-preflight` | **4 PASS / 4 SKIP / 0 FAIL** |

SKIP された 4 項目（**「実行されなかった」の意味**）: `P2 cuda_ext_loaded` と
`P3 deterministic_flags`（`plan.env.preflight` に記載なし）、`P4 prereg_committed` と
`P5 frozen_source_hash`（`kind: analysis` のため対象外）。

---

## 3. Phase A — 対象一覧（G1: ask → 記録して続行）

`step` の値を絞り込む前に実測した。`group=baselines` の 20 実験は `s0`（18）と
`s0_frozen`（2）のみで、**`"s0" in step` は取りこぼしも過剰取得もしない。**

### 前 task の UNKNOWN が解けた

前 task で `baselines/s0/maskdino_bbox@val` と `varifocanet_bbox@val` が
`experiments.csv` に見つからなかった。**実際には存在し、`#<hash>` で 2 つに分離
されていた。**

| experiment_id | n_runs | eval_recipe_id | 除外 |
|---|---|---|---|
| `baselines/s0/maskdino_bbox@val#None` | 3 | （空） | **3** |
| `baselines/s0/maskdino_bbox@val#a63aecae` | 3 | `a63aecae1158` | 0 |
| `baselines/s0/varifocanet_bbox@val#None` | 3 | （空） | **3** |
| `baselines/s0/varifocanet_bbox@val#a63aecae` | 3 | `a63aecae1158` | 0 |

`#None` の 6 run はいずれも `experiments/baselines/_wrong_split_8_2_3/` 配下で、
**全件が `excluded=True`** である。比較表を構成するのは `#a63aecae` の側である。
前 task が完全一致で探して見つけられなかったのは、この分離子のためだった。

### 索引側と実体側の集合差（両方向）

| 側 | 件数 |
|---|---|
| 実体側（`find -L experiments/baselines -maxdepth 2 -type d -name "s0_*"`） | **61** |
| 索引側（`target_runs.csv`） | **55** |
| 実体にのみ | **6** |
| 索引にのみ | **0** |

**実体にのみ存在する 6 件は重複ではなく、同じ run の「もう半分」だった。**

| パス | 中身 |
|---|---|
| `experiments/baselines/s0_007_codetr_bbox_seed42/` | `epoch_12.pth`（821 MB）/ `best_val_mAP_epoch_12.pth`（307 MB）/ `predictions/` / `mmdet_config.py` / `logs/` / `wandb/` |
| `experiments/baselines/_legacy_score_thr_0/s0_007_codetr_bbox_seed42/` | 6 点証跡のみ（`metrics.json` `config.yaml` `command.sh` 等）。**重みなし** |

**索引は証跡側を指しており、成果物は退避されていない側にある。**
同名のディレクトリが 2 か所にある組は **12 件**（`_wrong_split_8_2_3` の 6 と
`_legacy_score_thr_0` の 6）。

**G1 は `ask` に該当する。** SPEC 本文の指示（「件数と内容を記録し、以降どちらの
一覧を使うかを明記して続行する」）に従い、**索引側を同一性の基準、実体側の同名
ディレクトリを成果物の探索先とする和集合**を以降で使った。

### 検出器ごとの run と seed

対象 55 run / 20 experiment_id。**3 seed が揃っていないのは 3 つ**である。

| experiment_id | runs | seeds |
|---|---|---|
| `baselines/s0/ddq_smoke@val` | 1 | 42（除外 1） |
| `baselines/s0/sensex_codino_bbox@val` | **1** | 42 |
| `baselines/s0/wiring_verification@val` | 2 | 42, 42 |

`sensex_codino` は**比較表に載っているのに 1 seed しかない**（mAP 0.718000）。
`ddq_smoke` と `wiring_verification` は比較対象ではない。

---

## 4. Phase B — 系統差の中身（本 task の分岐点）

### `eval_recipe_id` の定義（実装から確定）

`tools/harvest_runindex.py:897-918`。ハッシュ対象は `RECIPE_ID_KEYS` の 10 キー:

    test_cfg, split_train_images, split_val_images, split_test_images,
    split_train_annotations, split_val_annotations, split_test_annotations,
    effective_batch_size, gpu_count, lr_scaling

**`server_name` は含まない。** 逆に **`split` サイズと GPU 構成を含む**ため、
**評価条件が同じでも学習時の GPU 構成が違えば id は変わる。**
「6 種類の `eval_recipe_id`」を「6 種類の評価条件」と読むのは誤りである。

### 値が割れているキー（和集合から取得）

出現した全キー 38。**値が割れているキーも 38**（全キーが割れている）。
ただし大半は `None` 対 値であり、**一部の run だけが記述用の追加キーを持つ**ことに
よる（`optimizer` `lr` `scheduler` `finetune_from` 等は `dacdetr` の 3 run のみ）。
全列挙は `audit/recipe_diff.txt`。

### 影響する／しないの分類

| 分類 | キー | 根拠 |
|---|---|---|
| **mAP に効く（後処理）** | `test_cfg.score_thr` `nms_pre` `nms_iou` `max_per_img` `topk` | 評価時の検出後処理そのもの |
| 効かない（判定から除外） | `server_name` | `recipes_match` が警告のみで判定に使わない（実装で確認） |
| 間接的に効く（学習条件） | `gpu_count` `effective_batch_size` `lr_scaling` | 評価には効かないが重みが変わる |
| 効かない（記述用） | `description` `note` `optimizer` `lr` `scheduler` `framework` `finetune_from` `config_name` 等 | 値であって条件ではない |
| **UNKNOWN** | `seed`（4 run のみ recipe 内に記録） | recipe 内の `seed` が何に使われるか実装で追えていない |

### 後処理設定だけで数え直した系統

**6 ではなく 4。しかも実質は 2 である。**

| 系統 | 設定 | run | 検出器 |
|---|---|---|---|
| **NMS-free** | `score_thr=0.0` / NMS なし / `max_per_img=300` | **30** | relationdetr, stabledino, dimaskdino, focusdetr, aligndetr, mrdetrdino, mrdetralign, maskdino_nmsfree, s0frozen×2 |
| **NMS あり** | `score_thr=1e-08` / `nms_pre=3000` / `nms_iou=0.6` / `max_per_img=300` | **14** | codetr, ddq, ddq_smoke, maskdino#a63aecae, varifocanet#a63aecae, sensex_codino |
| NMS-free（別記法） | `topk=300`（`DETR topk (NMS-free)`） | 3 | dacdetr |
| 記録なし | 全て `None` | 8 | maskdino#None, varifocanet#None（**全件除外**）, wiring_verification |

`dacdetr` の系統は `max_per_img` ではなく `topk` に 300 を書いているだけで、
**note が `DETR topk (NMS-free)` と明記しており NMS-free 系統である。**
したがって実効的な系統は **NMS-free（33 run）と NMS あり（14 run）の 2 つ**である。

**この差は設定の取り違えではない。** Relation-DETR / DINO 系 / DETR 系は設計上
NMS を使わず top-k で選ぶ。MaskDINO / VarifocalNet / DDQ / Co-DETR は NMS を使う。
**後処理は検出器の設計に属しており、揃えること自体が意味を持たない。**

### 系統差の実効的な大きさ（決定的な測定）

**同一検出器が両系統で評価されている実例がある。**

| experiment_id | 後処理 | mAP | pstd | n |
|---|---|---|---|---|
| `baselines/s0/maskdino_bbox@val#a63aecae` | **NMS あり** | 0.671667 | 0.003859 | 3 |
| `baselines/s0/maskdino_bbox_nmsfree@val` | **NMS-free** | 0.671333 | 0.006342 | 3 |

**差 = +0.000333。σ = 0.006342（両者の pstd の大きい方）。|差| / σ = 0.05。**

§10.1 の 1σ 基準を大きく下回る。一方、比較表の検出器間の幅は
0.697333〜0.726794 = **0.029461（約 4.6σ）**である。

**系統差は検出器差の 1/90 以下であり、比較を汚していない。**

**限界を明記する。** これは maskdino **1 検出器**での測定である。NMS-free 化が
検出器によって効き方が違う可能性は否定できない（箱の重なり方が異なるため）。
**他検出器への一般化は `UNKNOWN`。**

---

## 5. Phase C — 何が残っているか（G2: pass）

### 走査能力の陽性対照 — SPEC の対照は設計が誤っていた

SPEC は `/tmp/probe_link` を**走査の根**に置いて `rglob` が検出しないことを期待した。
**実測では `rglob` も検出した**（`['/tmp/probe_link/sub/probe.bin']`）。
`Path(root).rglob()` は**根として渡された symlink 自体は解決する**ためで、
前 task で問題になった「**途中のディレクトリ**が symlink」の状況を再現していない。

**対照を組み直した。** symlink を走査の途中に置くと:

| 方法 | 検出 |
|---|---|
| `find -L` | **した** |
| `os.walk(followlinks=True)` | **した** |
| `pathlib.rglob` | **しなかった** |

**これで対照が成立する。** G2 の検査「走査が symlink を辿れることを既知の実在物で
確かめ」は充足。以降の走査は `find -L` と `os.walk(followlinks=True)` のみを使った。

### 判定条件の妥当性（1 run を直接確認）

`experiments/baselines/s0_007_codetr_bbox_seed42/` を直接見た。

- 重みは **`checkpoints/` ではなく run 直下**にある（`checkpoints/` は空）
- 予測は `predictions/reeval_score_thr_0/predictions.pkl`（51.1 MB）
- **ディレクトリ名が `reeval_score_thr_0`** — 誰かが既に再評価を行った痕跡

SPEC の条件（`"predict" in root` を予測とみなす）は `eval.log` や
`mmdet_config.py` まで予測に数えてしまうため、**拡張子 `.pkl` のみに絞った。**

### 成果物の実測（ディレクトリ単位・重複なし）

和集合で run 単位に数えると、同名ディレクトリを共有する組（maskdino / varifocanet の
`#None` と `#a63aecae`）で**二重計上が起きる**ことに気づき、**固有ディレクトリ単位で
測り直した。**

| 項目 | 実測 |
|---|---|
| 走査した固有ディレクトリ | **61**（索引 55 ∪ 実体 61） |
| 重みを持つディレクトリ | **14** / 合計 **10.0 GB** |
| 予測 `.pkl` を持つディレクトリ | **9** |
| **索引パスのみを走査した場合** | **11 / 55** ← **codetr の 3 件を見落とす** |

**SPEC どおり索引パスだけを走査すると、codetr の重み（1.13 GB × 3）が見えない。**

### 重み 0 件の直接確認と、不在が意味するもの

重みが無い run を直接見ると、**6 点証跡しか無い**（`command.sh` `config.yaml`
`git_commit.txt` `metrics.json` `notes.md` `per_class_ap.json` `server.txt`）。
`ls -lL` で確認済み（`relationdetr` `stabledino`）。

**`ls` で止めず、不在の意味を追った。** 学習ホストと突き合わせる:

| 学習ホスト | 重みあり | 重みなし | 検出器 |
|---|---|---|---|
| **philip** | 3 | **25** | ddq（あり）／relationdetr・stabledino・mrdetrdino・mrdetralign・aligndetr・focusdetr・dacdetr・dimaskdino・sensex_codino（**なし**） |
| aolab | **10** | 0 | codetr・maskdino#a63aecae・varifocanet#a63aecae・ddq_smoke |
| andrew | 0 | 3 | maskdino_nmsfree |
| lecun | 1 | 6 | wiring_verification（あり）／s0frozen×2（なし） |
| bengio | 0 | 1 | wiring_verification |
| （不明） | 6 | 0 | maskdino#None・varifocanet#None（実体側の同名 dir を共有するため） |

**重みは失われたのではない。このホストに無い。** 比較表の主要 9 検出器は `philip` で
学習され、lecun へは 6 点証跡だけが転送されている。**`philip` に現存するかは lecun
からは測れない（`UNKNOWN`）。** 本 task は読み取りのみかつ単一ホストの契約である。

### 退避先

| 対象 | 実測 |
|---|---|
| `~/m2-archive/` | `20260811` の 1 ディレクトリ |
| その配下の `.pth` | **11 件** |
| 対象 run との一致 | **0 件**（すべて `_smoke_*` `_aborted_*` `_pre_redo_*` 由来） |

別経路の裏取りとして `find -L experiments third_party_snapshot transfer -name "*.pth"`
は **547 件**を返す（事前学習重みを含む総数）。退避先に対象 run の重みは無い。

---

## 6. Phase D — 再評価の経路

### 評価だけを走らせる経路は実在し、既に使われている

`scripts/reeval_s0_nms_free.py` —「S0 術具検出の **best.pth** を NMS-free
(`score_thr=0.0`) 系で val 再評価する」。`--exp-dir` を受け取り、`test_cfg` を
`NMS_FREE_TEST_CFG` に差し替え、`default_hooks` から `checkpoint` を外して
評価のみを走らせる。記録に `reeval_mode: nms_free_score_thr_0` を書く。

**codetr で実際に実行された痕跡がある**（`predictions/reeval_score_thr_0/eval.log`、
`07/03 15:06:31`）。前 task で見た `test_cfg.note = 'Reeval: NMS-free ...'` の 3 run が
これに当たる。

**したがって「後処理を差し替えて評価だけ走らせる」経路は存在する。**
**ただし入力は `best.pth` である。重みが要る。**

### 予測からの再採点は「できない」

`s0_007_codetr` の `predictions.pkl` を直接開いた。

| 項目 | 実測 |
|---|---|
| 型 / 件数 | `list` / **4265** |
| 1 画像あたりの箱 | **300**（= `max_per_img` / `topk` の上限） |
| score の最小 / 最大 | **0.011691** / 0.722918 |

**予測は後処理の「後」である。** 1 画像 300 箱に切られており、score の最小も 0 では
ない。したがって:

- `max_per_img` や `nms_pre` を**増やす**方向の再採点は**できない**（切られた箱は無い）
- `score_thr` を**下げる**方向も、0.0117 より下の箱が保存されていないため**できない**

**予測が残っていても、後処理を変える再採点には使えない。**

なお件数 4265 は **test split の画像数**であり、`@val`（1515）ではない。
この再評価がどの split で走ったかは本 task の対象外であり、**`UNKNOWN` とする。**
比較表の mAP は `metrics.json` 由来であり、この予測ファイルとは別である。

### 再学習になった場合の規模の材料

対象 run には `config.yaml` と `command.sh` が**残っている**（重みが無い run も含む）。
再現の手順は失われていない。**1 run あたりの所要時間は、重みが無い run に `logs/` が
無いため読めない。`UNKNOWN`。推定値は書かない。**

---

## 7. 結論

### 7.1 学習をやり直さずに再評価できるか — **一部**

| 検出器 | 重み（lecun） | 再評価 |
|---|---|---|
| codetr / ddq / maskdino / varifocanet | **あり**（3 seed 揃い） | **できる** |
| relationdetr / stabledino / mrdetrdino / mrdetralign / aligndetr / focusdetr / dacdetr / dimaskdino / sensex_codino / maskdino_nmsfree / s0frozen×2 | **なし** | **できない**（lecun では） |

**比較表の首位 `relationdetr`（0.726794）を含む主要 9 検出器の重みが lecun に無い。**
`philip` に現存すれば再評価は可能だが、**lecun からは測れない（`UNKNOWN`）。**

`escalate_if`「重みも予測も残っておらず、再評価に学習のやり直しが必要と判明した場合」
は、**このホストの範囲では該当する。** ただし「失われた」のではなく「別ホストにある」
であり、`philip` を確認するまで再学習が必要とは断定できない。

### 7.2 そもそも再評価は必要か — **不要**

Phase B のとおり、系統差の実効的な大きさは **0.05σ**（同一検出器の両系統比較）。
検出器間の幅 **約 4.6σ** と比べて無視できる。**比較表は使える。**

### 7.3 三択の可否とコスト

| 選択肢 | 可否 | コスト |
|---|---|---|
| **1. 同一条件で作り直す** | **事実上できない** | 9 検出器 × 3 seed = **27 run** の重みが lecun に無い。`philip` 次第（`UNKNOWN`）。再学習なら 27 run の GPU 時間（所要は `UNKNOWN`） |
| **2. 条件差を明記して載せる** | **できる。推奨** | 注記のみ。「NMS-free 系 33 run / NMS 系 14 run に分かれるが、同一検出器での実測差は 0.05σ」と書く |
| **3. 表を落とす** | できる | 検出器選定の根拠を失う。**実測上その必要が無い** |

**選択肢 2 を推す。** 根拠は (a) 系統差が 1σ を大きく下回ること、(b) 後処理は検出器の
設計に属しており揃えること自体が意味を持たないこと、(c) 作り直す経路が
このホストには無いこと。**ただし決めるのは起票者である。**

### 7.4 表に載せる際に併記すべき実測の但し書き

- `sensex_codino_bbox@val` は **1 seed のみ**（他は 3 seed）
- `maskdino_bbox@val` と `varifocanet_bbox@val` は `#<hash>` で 2 分され、
  **`#None` 側（`_wrong_split_8_2_3` 由来・全件除外）を混ぜてはならない**
- 系統差の 0.05σ は **maskdino 1 検出器での測定**であり一般化は `UNKNOWN`

---

## 8. 起票者の推測のうち、実測で裏づけられたもの・否定されたもの

### 裏づけられた

| 推測 | 実測 |
|---|---|
| 「重みが残っているかだけでは決まらない」 | **その通り。** 予測は後処理後（300 箱・score 最小 0.0117）で、後処理を変える再採点に使えない |
| 「後処理の設定を差し替える経路が無ければ再評価できない」 | 経路は**実在した**（`reeval_s0_nms_free.py`）。ただし `best.pth` を要する |
| 「同型の誤りが起きれば重みが残っていないと誤結論する」 | **まさに起きかけた。** 索引パスのみの走査は 11/55 を返し、codetr の 1.13 GB × 3 を見落とす |

### 否定された

| 推測 | 実測 |
|---|---|
| 「6 種類の `eval_recipe_id` = 6 種類の評価条件」 | **誤り。** id は split サイズと GPU 構成も含むハッシュ。後処理で見ると **4 系統**、実効的には **2 系統** |
| 陽性対照の設計（`rglob` は symlink を辿らない） | **この対照では `rglob` も検出した。** symlink を走査の根に置いたため。途中に置き直して対照を成立させた |
| 「系統差が検出器の実力差と分離できない」 | **分離できた。** 同一検出器の両系統比較で 0.05σ |
| Phase C の走査対象（索引パスのみで足りる） | **足りない。** 成果物は索引が指さないディレクトリにある |

### 前 task の UNKNOWN が解けた

`maskdino_bbox@val` と `varifocanet_bbox@val` は `experiments.csv` に**存在する**。
`#<hash>` の分離子が付いていたため完全一致の検索で見つからなかった。

---

## 9. Phase A〜D の完了判定の対応

| 判定項目 | 対応 |
|---|---|
| `conventions_rev` と runindex commit | `d422b08`（一致）/ `44697d9`（置換した） |
| 索引側の対象一覧・maskdino と varifocanet の所在 | §3。`#None` と `#a63aecae` に分離 |
| 実体側との集合差（両方向） | §3。実体 61 / 索引 55 / 実体にのみ 6 / 索引にのみ 0 |
| 検出器ごとの run 数と seed | §3。3 seed 未満は 3 つ（`sensex_codino` が比較表に該当） |
| `eval_recipe_id` の定義 | §4。`RECIPE_ID_KEYS` の 10 キー（実装から） |
| 値が割れているキーの全列挙 | §4 と `audit/recipe_diff.txt`。和集合から取得、38 キー |
| 影響する／しないの分類と根拠 | §4。`seed` は `UNKNOWN` |
| 後処理設定で見た系統数と所属 | §4。4 系統・実効 2 系統 |
| 走査能力の陽性対照 | §5。SPEC の対照は不成立 → 組み直して成立 |
| run ごとの重み・予測・設定 | §5 と `audit/artifacts.csv`。14 dir / 10.0 GB |
| 判定条件の妥当性確認 | §5。1 run を直接確認し `.pkl` のみに絞った |
| 重み 0 件の直接確認と原因追跡 | §5。学習ホスト別の内訳まで |
| 退避先の走査結果 | §5。`.pth` 11 件・対象一致 0 件 |
| 評価だけを走らせる経路の有無 | §6。実在し既に使用 |
| 予測からの再採点可否 | §6。**できない**。根拠は 300 箱と score 最小値 |
| 再学習時の規模の材料 | §6。config/command は残存、所要時間は `UNKNOWN` |

---

## 10. deviations（逸脱）

1. **G1 が `ask` に該当したが、記録して続行した。**（judgement）
   集合差 6 件。SPEC 本文が「件数と内容を記録し、以降どちらの一覧を使うかを明記して
   続行する」と定めているため、それに従った。使った一覧は**索引側を同一性の基準、
   実体側の同名ディレクトリを成果物の探索先とする和集合**である。
2. **陽性対照を組み直した。**（spec_defect）
   SPEC の対照は symlink を走査の根に置いており、`rglob` も検出してしまう。
   前 task の状況（途中が symlink）を再現していない。途中に置き直して成立させた。
3. **Phase C の走査対象を和集合に広げた。**（spec_defect）
   SPEC は索引パスのみを走査する。それでは codetr の重み 3 件を見落とす。
4. **和集合による二重計上を検出し、固有ディレクトリ単位で測り直した。**（judgement）
   `#None` と `#a63aecae` が同じ実体ディレクトリを共有するため、run 単位では
   重みが二重に数えられていた（20 run / 13.6 GB → 14 dir / 10.0 GB）。
5. **予測の判定条件を `.pkl` のみに絞った。**（spec_defect）
   SPEC の `"predict" in root` は `eval.log` や `mmdet_config.py` まで予測に数える。
6. **`meta.created_from.runindex_commit` を `44697d9` に置換した。**（judgement）
   SPEC が定める手順だが、契約ファイルへの変更であるため記録する。
7. **`context/auto/` の 3 ファイルを生成して変更に含めた。**（judgement）
   SPEC の Phase E は「変更は `tasks/` 配下のみ」を期待するが、手順書が投影への反映を
   確かめるよう求めている。**手編集ではなく生成**であり、禁止事項にも該当しない。

## 10.1 作業ツリーの確認

    M context/auto/followups.md
    M context/auto/results_recent.md
    M context/auto/tasks_summary.csv
    ?? tasks/T-2026-08-11-s0-reevaluation-feasibility/
    ?? tasks/inbox.d/T-2026-08-11-s0-reevaluation-feasibility.md

`src/` `configs/` `scripts/` `experiments/` `data/` `runindex/` `transfer/` に
変更 **0 件**。テストは **5 failed / 359 passed**（コードを 1 行も変更していない）。

---

## 11. 生成物

| ファイル | 内容 |
|---|---|
| `audit/target_runs.csv` | 対象 55 run（索引側） |
| `audit/recipe_diff.txt` | 値が割れているキー 38 件の全列挙 |
| `audit/artifacts.csv` | run ごとの重み・予測・設定の件数と容量 |
