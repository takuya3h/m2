# RESULT — T-2026-08-29-k1-verify-policy-place

命令とその出力の全文・再計算の過程・対照の出力は `audit.md` にある。本書からは節番号で指す。

## 判定

**status: partial。** 関門 G1 は pass（六 run の所在と読み取り可否が確定した）。
**K1 の照合は三値のうち「run が無い・読めない」で確定した。**

六 run は 6/6 実在するが、**metrics を一件も持たない**ため記録値との照合ができない。
一致とも不一致とも判定できない。SPEC §4 が求めた四つの再計算のうち三つは実行不能。

## 1. 解決された参照

| spec の記載 | 解決先 | 実測 |
|---|---|---|
| `meta.created_from.runindex_commit` | `runindex/` の最終変更 commit | `7918b5dd`（事前記入値と一致。置換不要） |
| `meta.created_from.counts` | `runindex/*.csv` の行数 | index 1177 / experiments 213 / verdicts 1038（すべて一致） |
| `contract.conventions_rev` | `context/conventions.md` の最終変更 commit | `a8c07e81`（一致） |
| `contract.inject_verbatim` | `context/conventions.md` の該当アンカーの原文 | `#prohibitions` `#issuer_cautions` `#naming` を原文のまま参照した（要約していない） |
| `inputs.sigma_policy`（省略） | `conventions#sigma` の既定を継承 | `series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired` |

`inputs.denominator.ref` と `inputs.frozen_source.ref` は本契約の spec に無い。

**解決した sigma_policy は実測でも裏付いた。** 記録の paired ばらつき 0.00949 は
`ddof=0`（pstd）で再現し、`ddof=1` では再現しない（audit §5.3）。

## 2. 完了判定（SPEC §5 Step C-1）

| # | 判定 | 実測の結果 | 空振りでないことの確認（実測） |
|---|---|---|---|
| a | K1 照合 | **「run が無い・読めない」で確定。** 再計算の全量は audit §5.3 の表と本書 §3 | 陽性: `mean(paired)` = −0.069067 が記録 −0.06909 の伝播区間内で一致、`acc_ali−acc_rel` = −0.069100 も一致。陰性: seed を一つ除く 3 通りで −0.07555 / −0.06730 / −0.06435 となり**3 通りとも不一致**。加えて値を一つ差し替えた 4 通り目も不一致。`ddof=1` は +0.011610 で不一致（系統に感応している）。出力全文 audit §5.3 |
| b | 特徴の由来 | **部分的。経路と日付は 07-06 以降を示すが、config 経由の直接の連結は UNKNOWN** | 実測値: 採用版 `data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42/` は **2026-07-10 17:39/17:41/17:47**、07-06 版は `.discarded_20260706` へ退避（07-06 03:26/03:32）。作り直し版の検出性能は `evidence/aligndetr_s0frozen_incident_20260703/aligndetr_s0frozen_v2_train_log.txt:1670` に **bbox AP 68.5960**。🔴 **六 run に `config.yaml` が無いため「config が指す特徴」は測れない → UNKNOWN**（audit §6.1） |
| c | 変更範囲 | **§2 の対象に限られる。** 差分の全量: `docs/stage0/A7_k1_provenance.md`(+146) / `docs/stage0/stage0_summary.md`(+27) / 未追跡 `tasks/T-2026-08-29-k1-verify-policy-place/` / 未追跡 `tasks/inbox.d/T-2026-08-29-k1-verify-policy-place.md` | `git status --porcelain` を `experiments/|data/|runindex/` で絞ると **0 件**。削除・置換は **0 行**（173 insertions / 0 deletions）で追記のみ（§6 禁止 5 を満たす） |
| d | 文書検査 | `make docs-check` `make agent-check` `make forbidden-check` `make taskindex-check` `make inbox-check` がすべて exit 0（本書 §7） | 対象件数を §7 に記載。**今回の変更ファイルが走査対象に入っていることを件数で示した** |
| e | 棚卸し | **追跡外 run: metrics 有り 61 件 / metrics 無し・checkpoints 有り 19 件。** 一覧は audit §4 | `git status --porcelain` の `runindex/` 該当は **0 件**（索引への書き込み零件）。同じ絞り込みを `docs/` へ当てると **2 件**出る（検査が空振りでない証拠） |

## 3. K1 の結論

**三値のうち「run が無い・読めない」。**

### 何がどこまで在ったか

| 事項 | 実測 |
|---|---|
| 六 run | **6/6 実在。** 置き場は `experiments/_orphan_no_metrics/transfer/`（SPEC §1 の `experiments/transfer/` ではない） |
| 各 run のファイル | **`checkpoints/best_tecno.pth` 一つだけ**（六 run 合計 6 ファイル、各 2,599,650 バイト） |
| `metrics.json` / `config.yaml` / `command.sh` / `git_commit.txt` / `notes.md` | **0/6** |
| `predictions/` `visualizations/` | 存在するが**すべて空** |
| 学習ログ（`/tmp/gpu_waiter_logs/`） | **ディレクトリ自体が存在しない** |
| 索引 4 種への登録 | **0 件** |
| 同一性 | 隔離前の md5 記録（`experiments/analysis/t1a_diag_2026-07-29/csv/t2_ckpt_inventory.csv`）と **6/6 一致**。六つの md5 は互いに異なる（複製ではない） |

**遡れなかった理由は run 名ではなく metrics の欠落である。** `.gitignore:157-162` が
隔離の時点で「metrics.json/config.yaml/command.sh/git_commit.txt/notes.md がすべて無い」と
記録していた（audit §3.3）。

### 再計算できた分の対照表（記録の内部整合。run への遡及ではない）

許容差は入力の丸め幅を出力へ伝播させて取った（端点の総当たり）。

| 量 | 再計算 | 伝播区間 | 記録 | 判定 |
|---|---|---|---|---|
| mean(paired 3 件) | −0.069067 | [−0.069117, −0.069017] | −0.06909 | 一致 |
| pstdev(paired) ddof=0 | +0.009480 | [+0.009434, +0.009526] | 0.00949 | 一致 |
| stdev(paired) ddof=1 | +0.011610 | [+0.011555, +0.011666] | 0.00949 | **不一致** |
| acc_rel − 分母 | +0.049000 | [+0.048900, +0.049100] | +0.0490 | 一致 |
| acc_ali − 分母 | −0.020100 | [−0.020200, −0.020000] | −0.0201 | 一致 |
| acc_ali − acc_rel | −0.069100 | [−0.069200, −0.069000] | −0.06909 | 一致 |

**記録の三値は互いに整合しているが、整合は記録の中だけであり run の実測と結び付いていない。**

**実行できなかった再計算 3 件**（いずれも run の metrics を要するため）: 両側の 3-seed 平均 acc と
ばらつき / 両側の hemostasis F1 の 3-seed 平均とばらつき / seed 別の acc からの paired 差。

### 分母 0.8986（SPEC は「無ければ記録値のまま」としたが、在った）

`s4_phase_baseline_001/002/003`（seed42/456/123）の 3-seed 平均 = **0.8985698569856986 → 0.8986**。

🔴 **ただし一意ではない。** 同 description の 55 行から作れる 3 件組 26,235 通りのうち
**277 通り（1.06%）が 4 桁表示で 0.8986 になる**（audit §5.4）。数値の一致は特定の根拠に足りない。

## 4. 実測（次の契約で使う値）

| 項目 | 実測値 |
|---|---|
| ホスト | `lecun` |
| repo の位置 | **`/home/ubuntu/slocal/m2`**。🔴 記録の `/home/ubuntu/slocal2/m2` は**存在しない**（audit §1） |
| 分岐 | `feat/k1-verify-policy-place`（起点 `origin/phase0`） |
| 追跡外 run | **metrics 有り 61 件**（`b2a_lovo_v01..15` 30 / `b2a_seglovo_v01..15` 30 / `b2a_det2phase_oracletool_009` 1、いずれも 08-25〜08-28 生成）／**metrics 無し・checkpoints 有り 19 件** |
| GPU | **NVIDIA RTX A6000 × 2 枚。** 空き 48,507 MiB と 48,521 MiB、利用率 0% / 0%。**両枚とも空いている** |
| 六 run の checkpoint | 健在。各 2,599,650 バイト、md5 照合済み。**再評価による数値回復は原理的に可能** |

## 5. 起票者の誤り

| 型 | 内容 |
|---|---|
| `asserted_without_measuring` | SPEC §1 が証跡経路を `experiments/transfer/` 配下と書いたが、現物は `experiments/_orphan_no_metrics/transfer/` にある。指示どおり `experiments/transfer/` を見ると六 run は一件も見つからない |
| `asserted_without_measuring` | SPEC §0 が「lecun の run が索引に未収穫だから遡れないと推定される」としたが、実際の理由は **metrics の不在**である。指示どおり収穫を疑うと、収穫器が走査すらしない run を収穫できない理由の追跡に時間を費やす |
| `self_contradiction` | `governance.decisions_required` に「追跡外 run を収穫するか」を置いたが、§3 A-3 と §6 禁止 2 が本文で既に「収穫しない」と答えている。指示どおり実行すると L3 の P6 が FAIL し、本文が答えている問いで実行が止まる |
| `check_does_not_check` | SPEC §4 の検算器の対照「陽性は relationdetr 側の平均 acc が再計算で一致すること」は、記録側に seed 別の acc が無いため実行できない。指示どおりに組むと陽性対照が定義できず、対照の無い検算になる |

## 6. 逸脱・想定外・UNKNOWN・判断待ち

**逸脱**

1. `judgement` — 作業ツリーに前セッションの未追跡 3 種（`docs/sessions/digest/2026-08-25-6ae159a7-*.md`、`.sync-pause.released`、`experiments/analysis/official_split_reassessment/*.py`）があり `task_start.sh` が実行できなかった。削除せずスクラッチパッドへ退避した。**うち .py 3 件は origin/phase0 と md5 同一のため無損失。digest 1 件は版管理に無く、退避したままである（申し送り）。**
2. `judgement` — `decisions_required` の 1 件を利用者へ提示し「収穫しない（棚卸しのみ）」の回答を得た。回答は `meta.amendments` へ記録し `decisions_required` を空にした（前例 `T-2026-08-26-lovo-decision-rule` に倣った）。
3. `spec_defect` — SPEC §4 の陽性対照が定義できないため、**記録側に seed 別で残る唯一の量（paired 差 3 件）**を陽性対照に置き換えた。陰性対照は指示どおり「seed を一つ除く」で取り、さらに値の差し替えを 1 件足した。
4. `judgement` — 検算器の許容差を最初は出力側にだけ適用し、入力の丸め表示を実数として扱っていた（`mean(paired)` が誤って不一致と出た）。`issuer_cautions` 注意 7 に反していたため、入力の丸め幅を伝播させる方式へ改めた（audit §5.2）。
5. `environment` — spec 記載の `prohibitions` のうち `no_runindex_regen` と `no_history_rewrite` は `conventions#prohibitions` の表に存在しない id である（表は `no_frozen_change` と `no_runindex_hand_edit` を持つ）。L2 は通るため停止せず、意味は SPEC §6 の本文で解した。

**UNKNOWN**

1. 六 run の**学習時刻と学習ホスト**。checkpoint の mtime は 49 秒に集中し、逐次 50 epoch × 6 run と両立しない。複製の時刻であり学習の時刻ではない（audit §3.5）。
2. aligndetr 側の**config が指す特徴ファイル**。config.yaml が無いため測れない（audit §6.1）。
3. 07-10 版の特徴が **v2 ckpt から出たこと**の直接の記録。抽出ログが無く、消去法による推定である（audit §6.4）。
4. 六 run の metrics が**いつ・なぜ失われたか**。隔離時点で既に無く、失敗ログも残っていない。

**判断待ち**

1. **追跡外 run の収穫可否** — 利用者の回答により本契約では収穫しない。61 件は索引の最終更新（08-16）より後の生成であり、`make runindex` で解消する。**別契約として起票するかは判断待ち。**
2. **六 run の checkpoint を再評価して K1 を回復するか** — checkpoint は健在で再評価は原理的に可能。GPU は 2 枚とも空いている。本契約は GPU 使用が禁止のため実施していない。
3. 退避したままの digest 1 件（`docs/sessions/digest/2026-08-25-6ae159a7-*.md`）を版管理へ入れるか。

## 7. 送出

検査（終了コードは zsh の配列添字を使わず個別に `$?` で取った。audit §7.2）:

| 検査 | 終了コード |
|---|---|
| `make taskindex-check` | 0 |
| `make inbox-check` | 0 |
| `make docs-check` | 0（対象 42 文書 / ターゲット 33 件） |
| `make agent-check` | 0（対象 109 件） |
| `make forbidden-check` | 0（変更 12 件中 生成物 4 件を除く 8 件を走査。A7 と総括を含む） |

**空振りでないことの確認**: `forbidden-check` を `experiments/` に変更のある起点へ当てると
**exit 2 / 違反 7 件**で落ちた（audit §7.4）。

| 項目 | 実測 |
|---|---|
| commit | `b8089bb7`（12 files changed, 1216 insertions, 55 deletions。うち削除 55 行はすべて投影の再生成分） |
| push | exit 0（`origin/feat/k1-verify-policy-place`） |
| PR | **#164**（base `phase0`。起点と同じ分岐） |
| 台帳への報告 | `make task-report` の結果を下に記す |
