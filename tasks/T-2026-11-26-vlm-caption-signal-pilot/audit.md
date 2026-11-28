# VLM キャプション予備測定の監査記録

2026-11-27 03:19 JST

## 開始状態

- 利用者の指示で実行先を andrew から ilya に変更した。不足する材料は rsync で取得する。GPU は NVIDIA RTX 6000 Ada Generation 2 枚。
- `git branch --show-current` は `feat/vlm-caption-signal-pilot`、起点は `8395be39`。契約取得時に本タスク所有の `.sync-pause` を作成した。
- 開始前の未追跡は stage2_pilot_viz/tools/ の41件と stage2_slides_qual/tools/ の8件。個別除外は .gitignore 217行目が優先されて効かず、取り消した。利用者承認後、取得の間だけ2ディレクトリを除外した。取得直後に解除し、49/49件のSHA-256が取得前と一致した。
- `make task-validate` は契約取得時とホスト変更後の両方で1件合格、0件失敗。
- `nvidia-smi` のGPU 0・1はそれぞれ49,140 MiB、使用15 MiB、使用率0%、電力上限250 W。compute-apps は0行。slocal2 の空きは `df -h` で3.3 TiB。
- ilya のリポジトリには .venv が存在する。検出塔の前回の実行環境 .venv-relation-detr は存在しない。andrew には同環境があり、Python は3.11.16（x86_64）。
- runindex 最終コミットは `036d6a60`。CSV の見出しを除く件数は index 2,668、experiments 1,347、verdicts 2,067。規約の最終コミットは `2d946b07`。各値は起票値と一致。

## 前提の記録と入口

依存する6件について RESULT.md と result.yaml の両方を確認した。

- `T-2026-11-21-grasp-hand-graph-t2p-match`　確認済み
- `T-2026-10-19-stage2-pilot-fix-epoch4-shuffle`　確認済み
- `T-2026-11-01-stage2-w23-bengio`　確認済み
- `T-2026-11-01-stage2-w23-andrew`　確認済み
- `T-2026-11-09-stage2-pd-w3-lowlr-andrew`　確認済み
- `T-2026-10-18-stage2-pilot-folda`　確認済み

- `scripts/stage2pilot/dp_train.py`　確認済み
- `scripts/stage2pilot/dp_model.py`　確認済み
- `scripts/train_t1b.py`　確認済み
- `scripts/w23/run_pd_w23_andrew.sh`　確認済み
- `scripts/w23/run_pd_w23_bengio.sh`　確認済み

## 転送した材料

設定済みのSSHホスト名 andrew と bengio では一覧取得に成功した。andrew のIPを直接指定した照会は認証失敗。実転送は andrew から `rsync -rt --ignore-existing --files-from=-` で行い、`/home/ubuntu/slocal2/stage2pilot_store/` の下へ8ファイル、130,841,378バイトを取得した。転送元と転送先の相対パスは同じ。期待値は `experiments/phase1/stage2fix_dp_024_D2_pred_noCF_ep4_seed42/config.yaml` と `experiments/analysis/stage2_pilot_fix/shuffle/shuffle_record.json`。対応表は mapping_stats と同じ方法で正規化した。

| 保存先からの相対パス | バイト | 照合対象 | SHA-256 |
|---|---:|---|---|
| `T-2026-10-18-stage2-pilot-folda/efros_ptower/experiments/phase1/stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42/checkpoints/best.pth` | 1,610,970 | ファイル | `0d76d446796f855a51640d756d6d3436573ff40ed600915980021c5f4cc6ad6d` |
| `T-2026-10-18-stage2-pilot-folda/efros_ptower/data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz` | 127,016,156 | ファイル | `c402e214d28d32c68b396fe84bbefefffdf7577d9550c421364543af78f172da` |
| `T-2026-10-18-stage2-pilot-folda/signals/final/D0_train.npz` | 927,578 | ファイル | `cdecdb958fd97d0ab5848f89e914fe049ecd776a89391096eced9185241288da` |
| `T-2026-10-18-stage2-pilot-folda/signals/final/P0_train.npz` | 695,810 | ファイル | `e58308d39813b490de494c8bfaf5fa772c072e39e2c9d19bc011a2f96a056009` |
| `T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/mapping_train.json` | 289,796 | 対応表 9,657 件 | `c62727faebe022528164850af1dabfd52d4c1da43d9ef5de7abca1d249cf76f0` |
| `T-2026-10-18-stage2-pilot-folda/signals/final/D0_val.npz` | 145,946 | ファイル | `4403d1fed34e3115f23d972fa98887fc653209a2e00b995b8ff2d821af3f6650` |
| `T-2026-10-18-stage2-pilot-folda/signals/final/P0_val.npz` | 109,586 | ファイル | `082387a092fe456d349c8cc46d6344042396bc39911461d88d2c51841b03dae8` |
| `T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/mapping_val.json` | 45,536 | 対応表 1,515 件 | `ad9dec099a32e6836773dcd58e19f1ee3be447dfbd33cd95a3460e22b8083d52` |

ilya に既存の検出塔は `experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth`。195,421,066バイト、SHA-256 は `30d199b15201cf3c03954852d8acc6fb58fe5349baef2fd200e877237ff682c4`。`experiments/analysis/grasp_pilot_g/caseB/identity_pred_noCF.json` と一致した。

andrew と bengio の標準 Hugging Face キャッシュに、指定した2モデルのリポジトリ名は見つからなかった。標準外の置き場の有無は未確定。

## 解決した参照

様式用の data/splits/ego_val.txt は参照しなかった。指定コミット `2d946b07` の context/conventions.md から、契約が参照する7節の原文を以下に収録した。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

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

<a id="env_p0"></a>
## env_p0

学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
数値が変わったまま完走する。

    source .venv-relation-detr/bin/activate   # 検出系
    source .venv/bin/activate                 # 解析・工程系

拡張のロード確認をログに残すこと。

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

---

<a id="split"></a>
## split

論文準拠 split の動画 ID は次のとおり。

- train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
- val: `09`, `10`
- test: `04`, `05`, `07`

転記元: `data/splits/ego_train.txt`, `data/splits/ego_val.txt`, `data/splits/ego_test.txt`。
実装側の対応値は `src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS`。

<a id="symmetry"></a>
## symmetry

比較する腕の条件を、起票の前に並べて確かめる。差が出たとき、それを仮説の効果と読めるだけの対称性が
無ければ、その実験は測りたいものを測れない。

### 対象

exp 契約のすべて。比較の類型は三つ。

| 類型 | 腕 | 例 |
|---|---|---|
| 塔どうし | 同じ役割の塔の候補、または方向で対になる塔 | 検出塔 D と工程塔 P、P の候補 A と B |
| 送り手と受け取り手 | 信号を出す塔と受ける塔 | P→D の P と D |
| 腕と分母 | 処置あり と 空入力 | 予測段の界面 と 空入力界面 |

### 表の様式

prereg.md に次の表を置く。列名はこのとおりにする（L3 の P13 が列名で表を探す）。

| 条件 | 腕1 | 腕2 | 判定 | 理由 |
|---|---|---|---|---|

判定は三値。**揃える**／**意図的に変える**／**UNKNOWN**。
「意図的に変える」には理由を書く。理由は次の三つに限る。

1. 仮説の操作である
2. タスクの性質上避けられない
3. **各塔の構造の標準の処方である**（使い方は下の「各塔の構造の標準の処方」に従う）

**UNKNOWN が一件でもある契約は起票しない。** 先に測る。

### 各塔の構造の標準の処方

理由 3 は、塔どうしで最適化の細部を揃えないことを認める。主判定の差（方向ごとの Δ）は、比べる腕と分母が
同じ受け取り手を持つので、塔どうしの最適化の差を含まない。揃えるのは塔の知識の出どころと収束規則である。

| 項目 | 範囲 |
|---|---|
| 使える比較 | 類型「塔どうし」だけ |
| 使える行 | 正規化層の扱い、学習率、勾配の刈り込み、weight decay、実効 batch、数値精度、決定性、入力の縮小規則（短辺の目標と長辺の上限） |
| 使える条件 | その塔どうしの差が、主判定（方向ごとの Δ）に入らないこと。つまり、比べる腕と分母が同じ受け取り手を持つ設計であること。入力の縮小規則の行に使うときは、画面の残る割合（切り出し）が両腕で同じであること |
| 使えない行 | 初期化の鎖の各段、in-domain のデータの範囲、相手タスクのラベルを使わないこと、収束規則、入力の切り出し（画面の残る割合） |

- **同じ塔の変種どうし**（確定塔、交差適合用の塔、診断点の塔）には使わない。変える一点（データか初期化）以外を揃える
- 理由 3 を使った行は、表の理由の欄に「各塔の構造の標準の処方」と書き、両腕の実際の値を書く
- 入力の縮小規則に理由 3 を使うときは、「必ず置く行」の「入力解像度と切り出し」を二行に分ける。切り出しの行は「揃える」、縮小規則の行は「意図的に変える」で理由 3 とし、両腕の実際の大きさを書く
- 実例: 検出塔の評価時の入力は 1333×749（pad 後 1344×768）、工程塔は 800×1422。画面の残る割合はどちらも 100%。前者は `tasks/T-2026-10-17-tower-reselect-prereq/RESULT.md` §4、後者は `tasks/T-2026-09-19-stage1-phase-tower-r3/RESULT.md` 完了判定 c の実測。方向ごとの Δ は同じ受け取り手を持つ腕と分母の差なので、塔どうしの入力の大きさの差を含まない。界面が渡すのは塔の出力であり画像ではない
- 出所: 利用者の決定 2026-10-17（契約 `T-2026-10-17-tower-reselect-prereq` の SPEC §2）
- 入力の縮小規則の出所: 利用者の決定 2026-10-18（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）

### 必ず置く行

初期化の鎖の各段（ImageNet 分類、COCO 検出、中立 SSL、in-domain。段ごとに一行）／凍結範囲／
入力解像度と切り出し（画面の何割が残るか）／前処理・増強／教師の種類と密度／epoch と上限への張り付き／
学習率／実効 batch（単位が違うなら比較不能と書く）／数値精度／ヘッドの容量／ヘッドの epoch／評価 recipe／ホストと装置型。

### ホストと装置型

比べる腕と分母は、同じホスト・同じ装置型で回す。ホストの行は「揃える」以外にしない。理由 1〜3 のどれも使わない。
別のホストの値と比べる必要があるときは、同じ設定を両方のホストで回した対照を置き、対照の差を並べて書く。
対照の無いホストをまたぐ差を、処置の差として読まない。

実測: 同じ設定（P\*-15、COCO、折り A、seed 42）で efros 0.7762、ilya 0.7066、差 +0.0696。
折り A の seed 間の標本 SD 0.0186 の 3.7 倍（`tasks/T-2026-09-27-stage1-ptower-20/RESULT.md` 関門 G2・完了判定 c）。
出所: 利用者の決定 2026-10-06 と 2026-10-17（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）。

### 規則の読み

規則の字面に複数の読みがあるとき、狭い読みを既定にしない。読みの候補を列挙し、利用者に諮る。
実測: 「P の初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、非対称を二周した。

### 出所

T-2026-09-19-symmetry-gate。実例は docs/symmetry-checklist.md。

<a id="det_groups"></a>
## det_groups

検出の co-primary と陰性対照の集合。研究方針 v2 §7.3（2026-06-19 に EDA から事前登録。結果を見て選んだ群ではない）。

| 群 | クラス | 用途 |
|---|---|---|
| 標的群 | Skewer、Bipolar Forceps、Scalpel、Syringe、Raspatory | 検出の co-primary（標的群 AP = 5 クラスの AP の平均） |
| 陰性対照群 | Gauze、Mouth Gag、Suction Cannula、Tweezers | Δ ≈ 0 であるべき群。動いたら交絡を疑う |

- クラス名は検出塔の注釈と完全一致で照合する
- ある折りの評価集合に出現しないクラスは、その折りの群 AP から除き、除いたことを明記する。0 で埋めない
- AP rare（Skewer、Syringe）は副次指標として別に報告する

## 検出器の実装を取得

ilya の既存の third_party/Relation-DETR に main.py・models・datasets・util が欠けていた。andrew の基準コミット `b485955c72452788240600da6d0f0b8cc49f33c7` の作業版から、学習に使う実装、設定、ライセンスと requirements.txt を `rsync -rt --ignore-existing --files-from=-` で `/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot/inputs/third_party/Relation-DETR` に取得した。転送元の main.py、optimizer/param_dict.py、transforms/presets.py、util/engine.py は基準コミットから変更されている。ファイルの内容を含めて転送元と照合し、139/139件一致、合計1,293,378バイト。パスをキー、SHA-256を値としたソート済みJSONのSHA-256は `cca5177950f86de8c5fa63b3f6f3dd88911b5cf6a2570e18cd69b6f87f8f7570`。実行環境と組み合わせた動作確認は未実施。

## ilya のデータと計算プロセス

Fold A の対象動画ディレクトリで画像名を列挙した。train は 9,657 件、val は 1,515 件、形式確認用の追加5動画は 10,461 件。画像内容の読み込みと test ディレクトリ内のフレーム列挙は行っていない。

既存の `scripts/grasppilot/proc_enum.py` の単独実行は GPU のPID 0件、compute 0件。ローカルの資料確認と並列した最初の実行は Python 1件を計上した。再確認時に当該 PID は存在しなかった。存在しない実行ファイルの対照は0件。存在しないGPU番号7への照会はデバイスなしで終了コード6。

## プリフライトと開始前の基準

実行当日の同期対象は ~/.claude、~/.codex、~/.agents、~/claude-sync、~/slocal2/m2 の5件。モデル、推論・検出環境と取得時のキャッシュの置き場 ~/slocal2/vlm_caption_signal_pilot_runtime は全対象の外。パス照合は同期対象の子を陽性と判定した。開始時の空きは3,610,719,875,072バイト。

標準プリフライトは7 PASS、0 WARN、7 SKIP、0 FAIL。SKIP は P2 cuda_ext_loaded、P3 deterministic_flags（未指定）、P4 prereg_committed、P5 frozen_source_hash、P13 symmetry_table_complete、P14 proposal_card_checked（analysis は対象外）、P12 refs_resolved（検査対象の解決前提なし）。

開始時の pytest は976 passed、6 failed、5 skipped、収集エラー1。完全なテスト名は専用の start/baseline.json に記録。

- `FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`
- `FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name`
- `FAILED tests/test_research_logger.py::test_log_run_idempotent`
- `FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally`
- `FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit`
- `FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block`
- `ERROR tests/test_stage1_dtower_convergence.py`

保護対象のサイズ・mtime_ns の初期目録は `/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot/start/protected_stat.jsonl`。239,407ファイル、31,891,561,560バイト、目録のSHA-256は `bfb28ad413083a5fda04068cc246a8fc3420a7e80fdefd680ed3407a2e054475`。既存 .venv の uv pip list のSHA-256は `9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0`。

## 重みの取得・仮想環境・G1 判定

- 同期対象外（`/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime`）に新しい仮想環境と重みを配置した。
  - VLM 用仮想環境: `/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime/vlm-venv`（Python 3.11.16、`torch==2.14.0+cu130`、`transformers==5.22.2`、`vllm==0.34.0`）。推論の道具は vLLM を選定（BF16・tensor parallel 2 枚で 11,172 枚のバッチ生成を安定かつ高速に実行できるため）。
  - 検出塔用仮想環境: `/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime/detr-venv`（andrew の `.venv-relation-detr` を同期対象外へ rsync、`torch==2.1.2+cu118`、CUDA 利用可、`MultiScaleDeformableAttention.so` を `torch-extensions/` にビルドし `ms_deform_attn_ext True` を確認済み）。
- 取得した 2 モデルの情報（全ファイルのバイト数と SHA-256 の完全一覧は `start/Qwen3.8-27B-manifest.json`・`start/Qwen3-Embedding-0.6B-manifest.json` に保存）:
  - VLM: `Qwen/Qwen3.8-27B`、revision `37561816e66b5b9153b1b64c10968c18c1e6f4a0`、license `apache-2.0`、配置 `/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime/models/Qwen3.8-27B`（52 GB、31 ファイル。`LICENSE` sha256 `bbedc3fda3305820b977265f01b8619d87570a6739de3a5582c3464840f1e57a`、`config.json` sha256 `191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`、`model.safetensors.index.json` sha256 `77042094076611b69791a610065f28b7013b8c621795fa86ddccc8bac7d1b9df`、18 シャードの sha256 はマニフェストに記録）。
  - 文埋め込み: `Qwen/Qwen3-Embedding-0.6B`、revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`、license `apache-2.0`、配置 `/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime/models/Qwen3-Embedding-0.6B`（1.2 GB、12 ファイル。`model.safetensors` sha256 `0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd`、`config.json` sha256 `b5bf1f51fc45be473a54718cef92448d90a1be001bf9b9a44b8c7f10a19feaa9`）。
- Gate G1: PASS（起点に前提の道具・記録あり、ilya の compute プロセス 0 件、2 モデルの重み取得済み、重みと仮想環境は同期対象外、空き十分）。

## Task B: 材料照合・塔単独評価・学習設定の写し・形式確認

- 材料照合（`task_b/materials.json`）: 9/9 件すべて記録（`stage2fix_dp_024/config.yaml`・`shuffle_record.json`・`grasp_pilot_g/caseB/identity_pred_noCF.json`）と一致。陽性対照（`D0_val.npz` の 1 バイト反転写し）は不一致を検出（`detected_mismatch=true`）。
- 工程塔単独 val 評価（`task_b/ptower_alone.json`、動画 09・10、`.venv`）: `phase_jaccard = 0.7762185528074379`（記録と差 `0.0`）、6 工程 Jaccard `0.7773831834035493`、`phase_accuracy = 0.8712871287128713`（差 `0.0`）、許容 0.005 以内。
- 検出塔単独 val 評価（`task_b/dtower_alone.json`、動画 09・10、1,515 枚、`detr-venv`、`ms_deform_attn_ext=True`）: `AP = 0.7276260094386302`（記録 `0.7273450` との差 `+0.000281`）、`target_AP = 0.7950925737196891`（記録 `0.7950748` との差 `+0.000018`）、`control_AP = 0.6728072214927379`（記録 `0.6726632` との差 `+0.000144`）、全項目許容 0.005 以内。基準予測を `identity/plain_val_preds.json.gz` に保存。
- §6.2 学習設定の写し（`task_b/settings.json`）:
  - V→P（`stage2fix_dp_*` W1、`w23b_dp_W2/W3_*` の D1-L2・D2・D3-L2）: 界面 lr `5e-4`・wd `0.01`、受け取り手（W2/W3）lr `5e-4`・wd `0.01`（AdamW 別群）、`smoothing_weight=0.3`、`fixed_epochs`（`lr_schedule=constant`）、`seed=42`。3 型間で食い違い 0 件。
  - V→T（W1 `stage2fix_pd_P1-W1/P2L`、W2 `stage2fix_pd_P1-W2` / `w23b_pd_P2L-W2`、W3 `w3lra_pd_P1/P2L`）: `trainable` = `film`/`w2`/`all`、界面 `film_lr=5e-4`、受け取り手 `lr` = W1/W2 `1e-4`・W3 `1e-5`（比 0.1 の群は `1e-6`）、`amp=bf16`、`tf32=False`、`fixed_epochs=True`（scheduler なし、一定学習率）、`seed=42`。2 型間で食い違い 0 件。
  - 陽性対照: V→P の W2 受け取り手 lr を `1e-4` に改変した写し・V→T の W2 受け取り手 lr を `1e-5` に改変した写しで、どちらも不一致を検出。
- §4.1 プロンプト選択肢の甲照合（`redact.py`）: 甲の語 44 件に対し §3.3 の 55 選択肢は一致 0 件。陽性対照（`"The surgeon uses a Scalpel near the skin."`）で `["Scalpel"]` 1 件を検出。乙の語幹で `cannot tell` に寄せる選択肢は `skin` の `"partly closed"`・`"fully closed"` と `action` の `"suck fluid"` の 3 件。
- §3.5 形式確認 第 1 回（元プロンプト sha256 `972ccbd589eac1dabd27e57fa658dd19ee45f0f67fae74956e09a8435468b20b`、追加動画 17〜21 の等間隔 30 フレーム）:
  - 動画集合 `["17","18","19","20","21"]`（陽性対照: 01 混入で `outside_allowed=["01"]` を検出）。プロンプト sha256 全件一致（陽性対照: 1 文字追加で不一致を検出）。
  - 前処理: 原寸 `1920×1080` → `grid_thw=[1,68,120]`、`pixels=2,088,960`、`image_tokens=2,040`。出力トークン 166〜226（平均 180.3）。
  - GPU ピーク記憶量: GPU 0 = 41,631 MiB、GPU 1 = 41,631 MiB（`vlm_format_gpu_mem.csv`）。
  - 所要: 30 枚 48.42 秒（`1.614 秒/フレーム`）、本番 11,172 枚の見積もり約 `5.01 時間`（18,032 秒）。
  - 解析: 29/30 成功、1 件失敗（`21_4_1185`、`parse_error="json"`、` ```json ` コードフェンスによる失敗）、拒否 0 件。伏せ字ヒット: 甲 `wound 7 / tissue_action 6 / surface 11`、乙 `11 / 11 / 11`＋属性寄せ 2、丙 `7 / 6 / 11`。
  - 形式修正（1 回目）: 6 行目を `Answer with one JSON object and nothing else, with these keys:` から `Answer with one raw JSON object and nothing else (no markdown code fences or backticks), with these keys:` へ変更（出力形式の指示のみ変更、記述内容の指示は不変。理由: コードフェンスによる JSON パース失敗の解消）。
- §3.5 形式確認 第 2 回（修正第 1 版 sha256 `3aa5390416a17556edd01526d5e3fffaea6d87c8db7c1f1823c393c53d561b5b`、追加動画 17〜21 の同じ 30 フレーム、`task_b/format_report_rev1.json`）:
  - 動画集合 `["17","18","19","20","21"]`（陽性対照 01 混入で外れ検出）、プロンプト sha256 全件一致（陽性対照 1 文字改変で不一致検出）。
  - 解析: **30/30 成功**（パースエラー 0、拒否 0）。出力トークン 186〜221（平均 195.9）。
  - 所要: 30 枚 49.01 秒（`1.634 秒/フレーム`）、本番 11,172 枚の見積もり約 `5.07 時間`（18,251 秒）。
  - 伏せ字ヒット: 甲 `wound 19 / tissue_action 5 / surface 10`、乙 `21 / 11 / 10`＋属性寄せ 1、丙 `19 / 5 / 10`。
  - 以上により `3aa5390416a17556edd01526d5e3fffaea6d87c8db7c1f1823c393c53d561b5b` を本番用固定プロンプトとして `frozen_prompt.txt` / `frozen_prompt.sha256` に確定した。
- Gate G2: PASS（材料 9/9 一致、両塔単独 val が記録と 0.005 以内、学習設定食い違い 0、VLM が ilya GPU 2 枚 BF16 で 30/30 正常 JSON を返却）。

## 利用者の判断委任（2026-11-27 10:02 JST）

- 利用者より「暫く見れないので、判断事項はまかせる。とにかく進めておいて」との指示を受領。Gate の FAIL・捏造禁止・`allow_write` 外・他契約の compute プロセス以外の判断は実行者が自律決定し、逸脱として記録して完走まで進める。

## Task C: 全フレーム生成・繰り返し確認・信号と入れ替えの作成

- フレーム集合の照合（`frame_coverage.json`）: V→P 特徴キャッシュと V→T Fold A COCO のフレーム集合は train 9,657・val 1,515（計 11,172）で完全一致（差集合 0）。
- 本番生成（`captions/generate-3aa53904...`、固定プロンプト sha256 `3aa5390416a17556edd01526d5e3fffaea6d87c8db7c1f1823c393c53d561b5b`、全 699 チャンク、`caption_stats.json`）:
  - 被覆: 11,172/11,172 完全一致（陽性対照: 1 件削除で `missing_count=1` 検出）。動画集合 `01,02,03,06,08,09,10,11,12,13,14,15`、test 動画 `{04,05,07}` との共通 0（陽性対照: `04` 混入で例外検出）。全件の `prompt_sha256` が固定値と一致。
  - 解析: 成功 11,104 / 11,172（99.39%）、失敗 68 件（`depth: 49`, `top-level keys: 17`, `action: 2`、JSON 構文エラー 0）、拒否 0 件。
  - テキスト重複（解析成功 11,104 件中の一意数）: `wound` 1,774、`tissue_action` 3,310、`surface` 5,938。
  - 伏せ字ヒット数: 甲 `wound 2,969 / tissue_action 715 / surface 3,807`、乙 `3,637 / 1,912 / 3,824`＋属性寄せ `52`、丙 `2,969 / 715 / 3,807`（丙では `tissue_action` 文と属性 `action`/`target` を信号から除外）。
  - 繰り返し一致（val 等間隔 50 フレーム、`captions/repeat-3aa53904...`）: raw 完全一致 `32/50`（0.6400）、parsed 完全一致 `32/50`（0.6400）。
  - 所要: 壁時計 18,329.08 秒（5.09 時間）、バッチ合計 18,237.95 秒（`1.632 秒/フレーム`）。
- 数値信号と入れ替え信号（`signals_manifest.json`、`signals/` 以下 24 ファイル）:
  - 文埋め込み: `Qwen/Qwen3-Embedding-0.6B`（ローカルロード、`padding_side='left'`、`last_token_pool`、指示文なし、L2 正規化）。一意テキスト 11,548 件、ノルム範囲 `1.000000〜1.000000`。
  - 次元: 1 本ベクトル型 `3128`（`3×1024 + 55 + 1`）、集合型 `4×1024`（丙は `tissue_action` トークンを `mask=False`・零ベクトル）。三通りで次元・並び一致、NaN/Inf なし。
  - 入れ替え: 既存の `mapping_{train,val}.json`（seed 42、9,657 件 / 1,515 件）が本契約のフレーム集合をちょうど覆うためそのまま使用。全信号で逆並べ替えによる完全一致・`sorted_digest` 一致・train/val 跨ぎなしを確認。
- Gate G3: PASS（train・val 全フレームに記述と三通りの信号あり、test 動画 0 件、入れ替えの値の集合一致）。

## Task D: 道具の拡張と確かめ（既定挙動・恒等性・陽性対照・学習集合）

- V→P 拡張: `scripts/stage2pilot/dp_train.py` へ既定 `None` の `--vlm-dir` と VLM 腕 6 種を追加（未指定時は既存経路を一切変更しない）。
- V→T 拡張: `scripts/train_t1b.py` 本体は無変更（`git diff` 0 行）。記録用ラッパー `experiments/analysis/vlm_caption_signal_pilot/tools/v2t_wrap.py` と新 config 2 件（`configs/stage2pilot/pd_film_d3128.py`・`pd_clsbias_lin_d3128.py`）を追加。
- config 差分検査（`task_d/task_d_summary.json`）: `pd_film_d9.py` vs `d3128.py`・`pd_clsbias_lin_d9.py` vs `d3128.py` ともに 97 行目の `signal_dim=9` → `signal_dim=3128` の 1 行のみで他差分 0。
- V→P 既定挙動の確かめ（`vlm_caption_signal_pilot_dp_defaultchk_002_D2_pred_noCF_ep4_seed42` vs 前回 `stage2fix_dp_024`）: `phase_jaccard = 0.7658485501436472`（差 `0.0`）、val 確率の最大差 `3.576e-7`（andrew RTX A6000 と ilya RTX 6000 Ada の浮動小数点丸め差）。陽性対照（`1e-6` ずらし）で `9.98e-7` を検出。
- V→T 既定挙動の確かめ（P1・予測-noCF・W1・1 epoch 6 step smoke、`direct_train_t1b` 2 回 vs `wrapped_v2t_wrap`）:
  - `init_mAP` はすべて `0.8916611661166115`、`init` 予測の direct vs wrapped 差 `max_abs_score_diff=0.0, max_abs_bbox_diff_px=0.0, label_mismatch=0`（陽性対照 `1e-6` シフトで `1.000e-6` 検出）。
  - `step 0` 損失は 3 回とも `15.797` で完全一致、`ep0_mAP` も 3 回とも `0.8907087024491922` で一致。step 1 以降の損失（direct1 `[15.797, 10.692, ...]`、direct2 `[15.797, 10.674, ...]`、wrapped `[15.797, 10.689, ...]`）と ep0 予測の微小差は、同一の `train_t1b.py` を 2 回実行した direct1 vs direct2 でも同規模（`max_abs_score_diff=0.0222` vs direct1 vs wrapped `0.0109`）で生じる CUDA backward 非決定性によるものと確認。
- V→P 恒等性・陽性対照・学習集合・信号出どころ（全 63 組 = 3 型 × 3 W × 7 腕）:
  - 学習前出力と塔単独のロジット差最大 `0.0`（63/63 完全一致）。
  - 陽性対照 `N(0, 0.05^2)`: 入力のある全 54 組＋D2 `empty` 3 組の計 57/63 組で出力変化を確認。不変の 6 組は構造上入力が届かない D1-L2・D3-L2 の `empty`（同じ型の `vlm_ko` 等で変化を確認済み）。
  - 信号出どころ違反 `0` 件、W2・W3 の学習集合検査すべて一致（定義外 1 個混入の陽性対照は全件不一致）。
- V→T 学習集合（6 組）・恒等性（14 組）・陽性対照（14 組）:
  - 学習集合（P1・P2L × W1・W2・W3）6/6 一致・定義外混入の陽性対照 6/6 不一致検出。
  - 学習前出力（2 型 × 7 腕 = 14 組）すべて基準予測 `plain_val_preds.json.gz` と `max_abs_score_diff=0.0, max_abs_bbox_diff_px=0.0, label_mismatch=0`。
  - 陽性対照 `N(0, 0.05^2)` は 14/14 組すべてで出力変化を確認。
- Gate G4: PASS。

## Task E: V→P 全本学習（63 本＋4 epoch 止め確かめ 3 本）と途中集計

- 実行設定: `run_v2p_all.py --workers-per-gpu 4`（GPU 2 枚 × 4 本 = 8 並行）、`--fixed-epochs 16 --record-epochs 4 8 12 16 --save-last-probs --seed 42`、W&B は `WANDB_MODE=offline`。
- 4 epoch 止め確かめ（W1/W2/W3 の D2 予測-甲、`task_e/ep4_compare.json`）: 3/3 すべて `probs_max_abs_diff = 0.0`・`jaccard_diff = 0.0` で一致。陽性対照（4 vs 8 epoch 確率比較）は W1 `0.2658`・W2 `0.4476`・W3 `0.8581` で差を検出。
- 本番 63 本（3 型 × 3 W × 7 腕）＋確かめ 3 本＝全 66 本が終了コード 0 で完了（壁時計約 7 分）。
- 確率からの再計算検証（`aggregate_report.py`）: 全 63 本 × 4 epoch = 252 組で最大ずれ `0.0`、`1e-6` シフト陽性対照 252/252 検出。
- 途中版集計 `experiments/analysis/vlm_caption_signal_pilot/REPORT.md` と `diffs.csv` を生成し、分岐 `feat/vlm-caption-signal-pilot` へ commit・push。
- Gate G5: PASS（63/63 本＋確かめ 3 本終了、4・8・12・16 epoch の値・確率・零初期化層 L2 がすべて揃う）。

## Task F: V→T 学習の 2 ホスト分割方針（2026-11-27 11:08 JST 利用者指示）

- 利用者指示により、空いた andrew（RTX A6000 × 2、compute-apps 0 件）と ilya（RTX 6000 Ada × 2）の 2 ホストで V→T（42 本＋4 epoch 止め確かめ 1 本 = 43 本）を分割並列実行する。
- `conventions#symmetry`（比べる腕と分母は同じホスト・同じ装置型で揃える）および SPEC §7（同じ型・同じ W・同じ epoch の中だけで比べる）を厳守するため、W 単位でホストを完全に揃える分割を採用した:
  - **ilya（RTX 6000 Ada × 2、各 2 本 = 4 並列）**: W1（P1・P2L 各 7 腕＋P1 ep4 確かめ 1 本 = 15 本）および W3（P1・P2L 各 7 腕 = 14 本）、計 29 本。
  - **andrew（RTX A6000 × 2、各 2 本 = 4 並列）**: W2（P1・P2L 各 7 腕 = 14 本）。
- 転送したファイルは数値化済みの埋め込み信号 `vec_*.npz`（12 ファイル）・基準予測 `plain_val_preds.json.gz`・新 config 2 本・実行スクリプトのみ（画像・生の記述は送っていない）。andrew 側も `WANDB_MODE=offline` で外部送信なし。
- 同じ `(型, W)` の 7 腕は全 6 ブロックとも 100% 同一ホスト・同一装置型で揃う。W1・W3 と W2 の間はホストが異なることを REPORT・RESULT の対称性表と逸脱に明記する。
- **追記（2026-11-28 14:47 JST 利用者決定）**: 利用者より「同一ホストで揃えるの無視して良い」との明示承認を受け、全体完了を約 5〜7 時間短縮するため W3（14 本）を以下のとおり ilya 10 本・andrew 4 本に分割した（W1 15 本は ilya、W2 14 本は andrew のまま変更なし）。
  - W3 ilya 担当（10 本、`task_f/w3_ilya_subset.json`）: P1 `empty, vlm_ko, vlm_otsu, vlm_hei`（4 本）、P2L `vlm_ko, vlm_otsu, vlm_hei, vlm_ko_shuf, vlm_otsu_shuf, vlm_hei_shuf`（6 本）。
  - W3 andrew 担当（4 本、`auto_w3_andrew.sh`）: P1 `vlm_ko_shuf, vlm_otsu_shuf, vlm_hei_shuf`（3 本）、P2L `empty`（1 本）。
  - W3 では同一 `(型, W)` 内に ilya と andrew の混在が生じるため、REPORT・RESULT の対称性表および逸脱に本決定と各腕の実行ホストを明記する。
- **インシデント・復旧記録（2026-11-28 18:40–18:49 JST）**: 2026-11-28 14:44 JST 頃に `run_v2t_one.sh` へ `flock` / GPU 空き待ちガードをインプレース編集で追記した影響により、編集前から稼働していた ilya 上の bash プロセス（`P2L W1 vlm_otsu_shuf`, 03:09 UTC 起動）が `v2t_wrap.py` の全 16 epoch 学習正常終了（09:35 UTC）後に読込オフセットずれを起こし、`train.log` を上書きして `v2t_finalize.py` 未実行のまま `exit_code=127` で終了した。全 16 epoch 予測（`val_inj_ep-1.json.gz`〜`ep15.json.gz`, `val_inj_best.json.gz`）・`t1b_result.json`・`v2t_wrap.json`・`logs/val_metrics_by_epoch.json`・`best_t1b.pth` が完全出力されていたことを確認の上、`v2t_finalize.py` を手動実行して `v2t_metrics.json`（ep4 AP=0.726190 / target=0.793042、final AP=0.724808 / target=0.790252、init_diff=0.0）を生成し `exit_code.txt=0` へ復旧した。なお andrew 側は `rsync` によるアトミック置換のため既存 4 プロセスは旧 inode `(deleted)` を保持しており影響なしを確認済み。
- **インシデント・復旧記録 2 および W1 全 15 本完了（2026-11-28 19:49–19:56 JST）**: 同じ編集前世代の `P2L W1 vlm_hei_shuf`（04:16 UTC 起動）も 10:43 UTC（19:43 JST）に全 16 epoch 学習を正常終了後、同一の読込オフセットずれで `exit_code=127` 終了したため、全予測・結果 JSON・チェックポイントの完全出力を確認の上で `v2t_finalize.py` を手動実行し、`v2t_metrics.json`（ep4 AP=0.726382 / target=0.792612、final AP=0.725307 / target=0.790927、init_diff=0.0）生成・`exit_code.txt=0` へ復旧した。これにより **V→T W1 全 15 本（本番 14 本＋4 epoch 止め確かめ 1 本）が完了**。
- **V→T 4 epoch 止め確かめ（`v2t_ep4_compare.py`, `task_f/v2t_ep4_compare.json`）**:
  - `P1 W1 予測-甲`（`--fixed-epochs` のため `train_t1b.py:L399-400` で `sched=None`・学習率完全一定）の 4 epoch 止め vs 16 epoch 学習の 4 epoch 目を比較。
  - `ep4` (`AP=0.729509`, `target_AP=0.799557`, `control_AP=0.675232`) vs `ep16@ep4` (`AP=0.728867`, `target_AP=0.798505`, `control_AP=0.675529`) の差は `AP +0.000642`, `target_AP +0.001052`, `control_AP -0.000296`（Task D で実証済みの CUDA backward 非決定性による実行間揺らぎの範囲内）。
  - 陽性対照（4 epoch vs 8 epoch）の差は `AP +0.005381`, `target_AP +0.006853`, `control_AP +0.004038` と約 6〜10 倍大きく、epoch 差を確実に検出。
- **W1 完了時点途中版レポート**: `aggregate_report.py --stage-label "V→T W1 完了時点（途中版）"` で `REPORT.md`（150 行）・`diffs.csv`（484 行）を更新（SPEC §7.1 予測 4「V→T W1 の 2 型で `予測-甲−入替-甲 < 前回 P→T`」は 2/2）。同時に ilya で `run_v2t_stage.py --w W3 --workers-per-gpu 2`（10 本サブセット）を `setsid nohup` 起動（全 4 スロット稼働）。
