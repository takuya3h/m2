# audit.md — 証跡の記録

task_id: T-2026-08-26-denoise-falsification / 実行ホスト: `Andrew` / 分岐: `feat/denoise-falsification`

**すべて読み取りである。データにもキャッシュにも凍結源にも書き込んでいない。**
**雑音除去の実装は書き換えていない（実行前後の要約値で確認、L233）。**

---

## Task 1 — 開始の記録

### Step 1 開始時刻

```
$ TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S %Z'; date -u '+%Y-%m-%dT%H:%M:%SZ'; date +%s
2026-08-26 07:00:33 JST
2026-08-25T22:00:33Z
1787695233
```

締切は Phase A 開始から 14 時間 = 840 分。

### Step 2 作業ツリーの状態

```
$ git status --porcelain
?? tasks/T-2026-08-26-denoise-falsification/
$ git branch --show-current
feat/denoise-falsification
```

未追跡は**本契約の契約書そのもの 1 件のみ**。退避すべき汚れは無かったため退避していない。
契約書を退避すれば実行対象そのものが消えるため、退避は行わないことが正しい。

### Step 3 抑止の目印

```
$ touch .sync-pause && ls -la .sync-pause
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 25 22:00 .sync-pause
$ grep -c sync-pause ~/bin/m2-sync.sh
2
```

稼働中の常駐処理は目印に対応済み（0 なら未対応。実測は 2）。

---

## 検証（L1 + L2）

```
$ make task-validate TASK=T-2026-08-26-denoise-falsification; echo "EXIT=$?"
WARN [L2-8] index.csv: 起票時 751 → 現在 1177（分母が動いています）
WARN [L2-8] experiments.csv: 起票時 207 → 現在 213（分母が動いています）
OK   T-2026-08-26-denoise-falsification

1 task(s), 0 failed
EXIT=0
```

### WARN の実体を確かめる — 分母行そのものは動いていない

直近 8 コミットで分母行 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`
の値を追跡した。

```
7918b5d  rows=213  n_runs=17 n_seeds=3 accuracy_mean=0.8973014948553679 accuracy_sstd=0.006099179663503103 edit_score_mean=39.91661295170067 edit_score_sstd=2.621371700613755
3e15d09  rows=221  （同上・全項目一致）
592a4e1  rows=217  （同上・全項目一致）
64576f3  rows=207  （同上・全項目一致）
12cc0e8  rows=206  （同上・全項目一致）
fc057d1  rows=206  （同上・全項目一致）
5c34296  rows=206  （同上・全項目一致）
e65f03a  rows=194  （同上・全項目一致）
```

**8 コミット全てで分母行の値が一致した。** WARN は索引全体の行数増加（他契約の run 追加）に
反応した粗い検知であり、`escalate_if: denominator_moved` には該当しない。
利用者へ提示し「続行する」の回答を得た。

分母の要件充足: `n_seeds=3`（`>=3` を満たす）/ `accuracy_pstd` `accuracy_sstd` ともに存在（sigma present）/ `split=val`。

### 起票元の runindex commit を件数で同定

```
探索対象: index=751 experiments=207 verdicts=1038
        7918b5d 2026-08-16 idx=1177 exp=213 vrd=1038
        3e15d09 2026-08-15 idx=851  exp=221 vrd=1038
        8c13afb 2026-08-15 idx=791  exp=217 vrd=1038
        592a4e1 2026-08-15 idx=791  exp=217 vrd=1038
*MATCH* 44697d9 2026-08-11 idx=751  exp=207 vrd=1038
*MATCH* f96edc1 2026-08-09 idx=751  exp=207 vrd=1038
*MATCH* 64576f3 2026-08-08 idx=751  exp=207 vrd=1038
        12cc0e8 2026-08-06 idx=749  exp=206 vrd=1038
```

一致は 3 件。最新は `44697d9`（2026-08-11）。**起票は 2026-08-25 だが、参照した索引は
2026-08-11 以前の状態である。**実体は 2026-08-16 の `7918b5d` まで進んでいた。

---

## 参照の解決

| spec の記載 | 解決先 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | `runindex/experiments.csv` | accuracy_mean=0.8973014948553679 / pstd=0.005917073407586465 / sstd=0.006099179663503103 / n_runs=17 / n_seeds=3 / seeds=42,123,456 / split=val / hosts=efros,lecun / arm=baseline / edit_score_mean=39.91661295170067 / edit_score_sstd=2.621371700613755 |
| `inputs.sigma_policy`（省略） | `context/conventions.md#sigma` の既定値を継承 | 下記の原文 |
| `inputs.frozen_source.ref` | ckpt の sha256 照合 | P5 が PASS（L214） |
| `contract.inject_verbatim` | `context/conventions.md` の原文 | 下記 6 節 |

### 継承した sigma_policy（`conventions#sigma` の原文・要約していない）

```
    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired
```

### `conventions#split` の原文

```
- train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
- val: `09`, `10`
- test: `04`, `05`, `07`
```

### `conventions#eval_recipe` の原文

```
- `LOCKED_DOWN_TEST_CFG`: `score_thr=1e-8`, `max_per_img=300`, `nms_pre=3000`, `nms_iou=0.6`
- `NMS_FREE_TEST_CFG`: `score_thr=0.0`, `max_per_img=300`, `nms_pre=None`, `nms_iou=None`
- `PHASE_EVAL_PROTOCOL`: `inference_protocol=online_causal`, `jaccard_mode=strict`
```

比較の三角形および DETR-family の公式評価は NMS-free とする。工程評価は online causal と
Jaccard strict を固定する。`select_box_nums_for_evaluation` は転記元で定義されていないため
`UNKNOWN（転記元未特定）`。

### `conventions#frozen_source` の原文（要点）

```
比較の三角形で認める凍結源は Relation-DETR seed42 完走 checkpoint。
同定パスは `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`。
checkpoint の正本 SHA-256:
    03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
サイズは 195421066 bytes。
`verify: ckpt_sha256` は全ホストで実行可能である。照合に失敗した場合は
`no_frozen_change` の違反として扱い、実行を中止して人へ escalate する。skip する経路は設けない。
```

### `conventions#prohibitions` の原文

```
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### `conventions#issuer_cautions` の原文（要点）

```
**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。
```

`grep -rn ... --include=*.py` が zsh で `no matches found` となり実行されなかった（実測）。
以後、グロブを含む語は引用符で囲んだ。

---

## L3 プリフライト

### 1 回目 — FAIL 2 件

```
$ source .venv/bin/activate && make task-preflight TASK=T-2026-08-26-denoise-falsification; echo "EXIT=$?"
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP UNKNOWN 判定基準が未確定。決定性設定は実行プロセス内で行われ外部から観測できない。backlog B-20 が未解決
P4 prereg_committed       FAIL prereg.commit が未記入
P5 frozen_source_hash     PASS third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth sha256=03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
P6 decisions_answered     FAIL 未回答 4 件: 当該ホストへ環境を新たに構築すること; 雑音除去の実装を書き換えること; 分母を別の実験へ移すこと; 本契約の範囲を越えて別の腕を追加すること
P7 destination_writable   PASS experiments/transfer/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              PASS 規則 8 件を検査し該当なし

RESULT: 5 PASS / 0 WARN / 2 SKIP / 2 FAIL
EXIT=2
```

**SKIP された項目**: P2 cuda_ext_loaded（契約の `plan.env.preflight` に記載が無いため実施されず）、
P3 deterministic_flags（判定基準が未確定・backlog B-20）。**SKIP は合格ではない。**

P6 の 4 件は利用者へ提示し、**4 件すべて「行わない」**の回答を得た。契約本文の禁止事項
（SPEC 第 4 節・第 5 節 7・prereg 第 7 節）と一致する。
P4 は prereg を版管理へ記録する承認を得て解消した。

### 2 回目 — FAIL 0 件

```
RESULT: 7 PASS / 0 WARN / 2 SKIP / 0 FAIL
EXIT=0
```

---

## Phase A — 環境の棚卸し（経過 18 分 30 秒 / 840 分）

### 1 仮想環境と道具

```
EXISTS .venv  python=Python 3.11.16
MISSING .venv-relation-detr
  OK      torch == 2.1.2+cu118        OK      mmengine == 0.10.7    OK      pyyaml == 6.0.3
  OK      torchvision == 0.16.2+cu118 OK      numpy == 1.26.4       OK      pandas == 3.0.3
  OK      mmcv == 2.1.0               OK      hydra-core == 1.3.2   OK      scipy == 1.17.1
  OK      mmdet == 3.3.0              OK      wandb == 0.27.0       OK      transformers == 4.44.2
```

`.venv-relation-detr` は不在だが**後続に不要である**。`scripts/train_b2a.py` の冒頭に
「本体 .venv で実行（Relation-DETR 非依存・キャッシュのみ読む）」と明記されており、
実装も GAP と tool-presence のキャッシュしか開かない。

### 2 本番の時系列モデルの入口

```
$ ls -la scripts/train_b2a.py
-rw-rw-r-- 1 ubuntu ubuntu 19568 Jul  6 00:46 scripts/train_b2a.py
```

実装の冒頭より:

```
B2a 片方向結合（検出→工程・Tier-0 必須・①信号レベル系統）= Δ_phase を測る結合本体。
    入力 = concat([ GAP(C5) 2048-d , tool_presence 15-d ]) = 2063-d  → 素の causal TeCNO
```

**契約が挙げた入口は正しい。** 併存する `scripts/train_s4_tecno.py` は GAP 2048 次元のみを
読む分母側（S4 base）であり、術具存在信号を受け取らないため雑音除去の対象にならない。

### 3 凍結源の重みと要約値

P5 が正本 SHA-256 と一致（上記 L214）。

### 4 術具存在の信号と前提キャッシュ

```
EXISTS  data/processed/b2a_detsignal/relation_detr_seed42  (3 件)
          test_toolpresence.npz 409956 / train_toolpresence.npz 927588 / val_toolpresence.npz 145956
EXISTS  data/processed/oracle_toolpresence  (3 件)
EXISTS  data/processed/stage1_features/relation_detr_seed42  (3 件)  train_gap.npz 79458316
EXISTS  data/processed/t1a_regiontoken/relation_detr_seed42  (3 件)
EXISTS  data/processed/phase_manifest  (4 件)  phase_vocab.json / train.json / val.json / test.json
```

**契約は `inputs.caches: []` と宣言していたが、後続は上記 5 系統のキャッシュを必要とする。**

### 5 分割の定義

```
EXISTS  data/splits/ego_train.txt  (10 行): 01 02 03 06 08 11 12 13 14 15
EXISTS  data/splits/ego_val.txt  (2 行): 09 10
EXISTS  data/splits/ego_test.txt  (3 行): 04 05 07
```

`conventions#split` の原文と一字一句一致する。

### 6 計算資源

```
index, name, memory.total [MiB], memory.used [MiB], utilization.gpu [%]
0, NVIDIA RTX A6000, 49140 MiB, 15 MiB, 0 %
1, NVIDIA RTX A6000, 49140 MiB, 15 MiB, 0 %
--- GPU を使っているプロセス ---
pid, process_name, used_gpu_memory [MiB]
（0 件）
cuda_available= True n= 2 NVIDIA RTX A6000
$ hostname
Andrew
```

**他の利用者との競合は無い。** 契約の `plan.resources.server: andrew` と一致。

### 7 欠けているもの — 本番入口から呼べる雑音除去の腕

雑音除去の実体は `docs/analysis_scripts/hmm_presence_filter.py`
（per-tool 2 状態 HMM の因果 forward filter。train の GT presence から遷移行列、
train の予測 sigmoid を GT で条件づけたヒストグラムから emission を推定し、
val に forward filtering を掛ける）。**代理側の分析スクリプト置き場にしかない。**

#### 方法 1 — 語による探索（本番側 243 ファイル）

```
$ grep -rniE "denoise|denoising|hmm|viterbi|forward_filter|fixed_lag" scripts src \
    | grep -viE "class_balanced_denoising|contrastive denoising|CDN denoising|denoising_nums|\.pyc"
scripts/post_process_dac_detr.py:163: … dac_cdn_ice = DAC + CDN(対照denoising) + ICE …
src/egosurgery_multitask.egg-info/PKG-INFO:624: … cls_branches 以外の denoising / query embedding …
src/egosurgery/models/heads/mask_dino_head.py:88: d2_cfg.MODEL.MaskDINO.DN = "cdn" if …
$ find scripts src -name '*.py' | wc -l
243
```

残った 3 件はいずれも DETR の学習内部で使う contrastive denoising（query の雑音付与）であり、
術具存在信号の雑音除去とは無関係である。**術具存在信号の雑音除去の腕は 0 件。**

`train_b2a.py` の術具信号に関する腕の全一覧（`grep -n "add_argument"` より）:

```
--tool-source {pred,oracle}   --mask-tool-dim   --mask-tool-dims
--drop-gap                    --tool-noise-rate --tool-noise-dims
```

`--tool-noise-*` は雑音を**加える**腕であり、除去する腕ではない。

#### 方法 1 の対照（両方向）

```
$ grep -rncE "tool-noise" scripts/train_b2a.py
scripts/train_b2a.py:3          ← 陽性対照。探索式は実在する語を引ける
$ grep -rncE "zzz_no_such_arm_token_xyz" scripts/train_b2a.py
scripts/train_b2a.py:0          ← 陰性対照。存在しない語では 0 を返す
```

#### 方法 2 — 構文木による import 解析（語による探索とは異質）

```
構文木を解析した本番側ファイル: 243 件
docs/analysis_scripts 系を import している本番側ファイル: 0 件

陽性対照 (egosurgery.models.heads.tecno_head を import): 13 件
    scripts/audit_grasp_phase_injection.py / scripts/eval_test_split.py
    scripts/extract_phase_context.py / scripts/train_b2a.py / scripts/train_g2.py / scripts/train_g2_m2.py …
陰性対照 (存在しない module): 0 件
```

**二つの異質な方法が一致して 0 件。対照は両方向で働いた。**

#### デノイズ済みキャッシュも存在しない

`train_b2a.py` は `SIGNAL_DIR = data/processed/b2a_detsignal/$RELDETR_FROZEN_TAG` を読むため、
デノイズ済みキャッシュが既にあれば実装を書かずに腕が立つ。確かめた。

```
$ ls -a data/processed/b2a_detsignal/
aligndetr_s0frozen_seed42.discarded_20260706  relation_detr_augstrong_hires_seed42
relation_detr_augstrong_seed123  relation_detr_augstrong_seed42  relation_detr_augstrong_seed456
relation_detr_seed123  relation_detr_seed42  relation_detr_seed456
$ find data/processed -maxdepth 3 -iname '*denois*' -o -maxdepth 3 -iname '*hmm*' -o -maxdepth 3 -iname '*filter*'
（0 件）
$ find data/processed -maxdepth 3 -iname '*toolpresence*' | head -4     ← 陽性対照
data/processed/oracle_toolpresence
data/processed/b2a_detsignal/relation_detr_seed42/test_toolpresence.npz
…
```

タグはすべて凍結源の変種であり、雑音除去の変種は 1 件も無い。

### 8 いま見ているものが最新かを確かめる — 自分の誤りを 1 件検出した

`conventions#issuer_cautions` の注意 12「判断の前に、いま見ているものが最新かを確かめる」に
従って確かめたところ、**作業分岐が `origin/phase0` より古かった。**

```
$ git --no-pager log -1 --format='%h %ad %s' --date=short origin/phase0
9963035 2026-08-26 Merge pull request #152 from takuya3h/feat/oracle-ceiling-and-tool-drop
$ git --no-pager diff --name-status origin/phase0..HEAD -- scripts/train_b2a.py
M	scripts/train_b2a.py
```

同時に走っていた契約 `T-2026-08-26-oracle-ceiling-and-tool-drop` が PR #152 で統合され、
`scripts/train_b2a.py` に `--task-id` と `--deterministic` を**追加していた。**

#### 誤りだった所見（古い版で測ったもの）

作業分岐の版で測り、「`train_b2a.py` と `ExperimentManager` に task_id を刻む経路が無い」と
記録した。**これは誤りである。**最新の版には存在する。

```
$ git show origin/phase0:scripts/train_b2a.py | sed -n '414,419p'
    p.add_argument(
        "--task-id",
        type=str,
        default="",
        help="契約の識別子。config.yaml の最上位へ書き出し、run と指示書を結ぶ。",
    )
$ git --no-pager grep -ln "task_id" origin/phase0 -- 'scripts/*' 'src/*'
origin/phase0:scripts/task_start.sh
origin/phase0:scripts/train_b2a.py                     ← 作業分岐の版には無かった
origin/phase0:scripts/train_grasp_phase_injection.py
origin/phase0:scripts/train_grasp_phase_injection_variants.py
```

**したがって `outputs.stamp.task_id_in: config.yaml` は最新の版で充足できる。**
後続に足りないものから task_id の配線は外れる。

#### 核心の所見を最新の版で測り直す — 結論は変わらない

```
$ git --no-pager grep -niE "denoise|denoising|hmm|viterbi|forward_filter|fixed_lag" origin/phase0     -- 'scripts/*' 'src/*' | grep -viE "class_balanced_denoising|contrastive denoising|CDN denoising|denoising_nums"
origin/phase0:scripts/post_process_dac_detr.py:163: … dac_cdn_ice = DAC + CDN(対照denoising) + ICE …
origin/phase0:src/egosurgery/models/heads/mask_dino_head.py:88: … MaskDINO.DN = "cdn" …
$ git show origin/phase0:scripts/train_b2a.py | grep -ncE "tool-noise"
3                                                      ← 陽性対照
$ git --no-pager grep -c "tool-presence" origin/phase0 -- 'scripts/train_b2a.py'
origin/phase0:scripts/train_b2a.py:11                  ← 陽性対照
```

残った 2 件はいずれも DETR の contrastive denoising であり、術具存在信号とは無関係である。
**最新の版でも、本番入口から呼べる雑音除去の腕は 0 件。判定 G1 の FAIL は変わらない。**

**古い版で測ったことによる誤りは、この 1 件だけであった。**核心の所見は最新版で測り直して
維持された。統合は行っていない（PR で統合する）。

### 9 分岐名の規定

```
$ grep -n "branch=\"feat/" scripts/task_start.sh
94:    branch="feat/${BASH_REMATCH[1]}"
52: 分岐名は識別子から機械的に導く（feat/<slug>）。人が打たない。
```

`T-2026-08-26-denoise-falsification` → slug `denoise-falsification` → `feat/denoise-falsification`。
現在の分岐と一致する。**慣行ではなく機械的な規定に照らして確認した。**

### 判定 G1 — FAIL

後続に必要なもののうち**「本番入口から呼べる雑音除去の腕」が実在しない。**
SPEC 第 8 節 3「代理側にしか無い場合は、そこで止めて報告すること」に該当する。

---

## Phase B — 雑音除去が信号を変えていることの確認（経過 22 分 / 840 分）

利用者の承認を得て、停止条件に該当した後も補足として実施した（GPU 不要・読み取り専用）。

### 実装を書き換えずに走らせる

```
$ sha256sum docs/analysis_scripts/hmm_presence_filter.py        ← 実行前
1e166f977249ad7cfd3cd13c802801009e8cf274b5789e1f9037e990566ab518
$ .venv/bin/python docs/analysis_scripts/hmm_presence_filter.py <scratchpad>/hmm_val.npz
=== val (1515 frames, 3 videos) ===
raw sigmoid                macroF1=0.9103 err= 2.81% exact=69.17% ham=0.393 trans=0.5959 (GT 0.3419)
causal HMM filter          macroF1=0.9238 err= 2.39% exact=72.15% ham=0.334 trans=0.3545 (GT 0.3419)
per-class F1 (raw -> HMM):  Hook 0.777 -> 0.828 (+5.07pp) / Scalpel 0.915 -> 0.953 (+3.82pp) /
  Forceps 0.768 -> 0.791 (+2.30pp) / … / Scissors 0.853 -> 0.850 (-0.29pp)
real 0.198 total
$ sha256sum docs/analysis_scripts/hmm_presence_filter.py        ← 実行後
1e166f977249ad7cfd3cd13c802801009e8cf274b5789e1f9037e990566ab518
```

**要約値が実行前後で一致。実装は書き換えていない。** 所要 0.198 秒。

### 施さない腕が信号へ加工を入れないことを実装で確認

`scripts/train_b2a.py` の `load_clips` は既定値
（`tool_source="pred"` / `mask_tool_dim=None` / `noise_rate=0.0`）のとき
`sig_by_frame[fid]` を npz から取り出したまま連結する。**変換は一つも通らない。**

### 変化の量を集合の差で測る

```
対象: val  frames=1515  dims=15  cells=22725
整列: frame_ids 一致 = True

=== 1. 連続値のまま: 値が変わったセルの集合 ===
  値が変わったセル = 22725 / 22725  (100.00%)
  最大の変化幅 = 0.800449   平均 = 0.062747

=== 2. 二値化して集合の差（実装が自ら選んだしきい値） ===
    |raw|=6107  |denoised|=4468   (件数の差 = -1639)
    集合の差 raw\den = 2013   den\raw = 374   対称差 = 2387
    → 件数の差 1639 に対し対称差 2387。入れ替わりが 748 セル分ある

=== 3. 二値化して集合の差（しきい値 0.5 固定・選び方に依らない確認） ===
    |raw|=4352  |denoised|=4444   (件数の差 = +92)
    集合の差 raw\den = 108   den\raw = 200   対称差 = 308
    → 件数の差 92 に対し対称差 308。入れ替わりが 216 セル分ある

=== 4. 信号が向きを変える回数（動画境界をまたがない） ===
  動画区間 = 3 件 [518, 915, 82]
  raw = 1618 回   denoised = 542 回   減り = 1076 回 (66.5% 減)

=== 5. 陰性対照: 施さない腕の信号は元の信号と一致するか ===
  集合の差 = 0 セル  → 一致（意図しない加工なし）
  要約値でも確認: raw=4807.2875671387  arm=4807.2875671387  一致=True

=== 6. 計数そのものの対照（prereg §5） ===
  陰性: 同一の配列どうしの集合の差 = 0  （0 であるべき）
  陽性: 1 セルだけ変えた配列との集合の差 = 1  （1 以上であるべき）
```

**契約が「部分一致で数えてはならない」と命じた理由が実際に現れた。**
しきい値 0.5 では件数の差が +92 しかないのに対称差は 308 である。
件数だけを見ていれば変化量を **3.3 倍過小に** 報告していた。

### 判定 G2 — PASS

雑音除去は信号を確かに変えている。したがって、もし対測定で効果が見えなかったとしても
「雑音除去が働いていなかった」という説明は排除できる。

---

## Phase C / D — 実施していない

判定 G1 が FAIL であり、SPEC 第 8 節 3 と prereg 第 6 節 1 の停止条件に該当するため、
**学習は一本も走らせていない。**したがって次は測っていない。

- 学習一本の所要時間 — **UNKNOWN（測っていない）**
- 残り時間で入る対の組数 — **UNKNOWN（所要時間が無いため計算できない）**
- 見える効果の大きさの下限 — **UNKNOWN（本数が 0 のため求まらない）**
- 効果量 / 改善側へ倒れた対の個数 — **UNKNOWN（対測定を行っていない）**
- 実行の順序 — **該当なし（腕を 1 本も走らせていない）**

**効果について何も測っていないため、「効果が見えなかった」とも書かない。**
見えなかったのではなく、**測っていない。**

---

## 変更範囲の一覧

```
$ git --no-pager diff --stat e040a5f~1..HEAD
（下記の commit を参照）
```

| 経路 | 変更 |
|---|---|
| `tasks/T-2026-08-26-denoise-falsification/spec.yaml` | PENDING 2 欄を実測値へ / decisions_required を空へ / prereg.commit を記入 / amendments 2 件 |
| `tasks/T-2026-08-26-denoise-falsification/SPEC.md` | 新規（配布された契約書。無変更で追加） |
| `tasks/T-2026-08-26-denoise-falsification/prereg.md` | 新規（配布された契約書。無変更で追加） |
| `tasks/T-2026-08-26-denoise-falsification/RESULT.md` | 新規 |
| `tasks/T-2026-08-26-denoise-falsification/audit.md` | 新規（本ファイル） |
| `tasks/T-2026-08-26-denoise-falsification/result.yaml` | 新規 |
| `tasks/inbox.d/T-2026-08-26-denoise-falsification.md` | 新規 |

**`data/` `runindex/` `experiments/` `third_party/` `docs/` `src/` `scripts/` は一切変更していない。**

---

## 禁止領域の検査

```
$ source .venv/bin/activate && make forbidden-check; echo "EXIT=$?"
{"base": "origin/phase0", "changed": 31, "checked": 31, "errors": [], "excluded": 0,
 "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"],
 "status": "fail", "violations": [ … 19 件 … ]}
EXIT=2
```

**失敗した。SPEC 第 6 節のとおり、失敗そのものは契約違反ではない。内訳を一件ずつ示す。**

比較の基準は `origin/phase0` である。`origin/phase0` は本契約の実行中に PR #152 で
進んだため、**差分の大半は「相手側にあって作業分岐に無いもの」＝ D（削除扱い）である。**
作業分岐が消したのではない。

| # | 経路 | 差分の向き | 出所 | 私の変更か |
|---|---|---|---|---|
| 1–7 | `experiments/transfer/b2a_det2phase_oracletool_009_…/` の 7 ファイル（command.sh / config.yaml / git_commit.txt / metrics.json / notes.md / per_class_ap.json / server.txt） | **D** | 契約 `T-2026-08-26-oracle-ceiling-and-tool-drop` が PR #152 で phase0 へ入れた run | **違う** |
| 8–12 | `experiments/analysis/lovo_decision_rule/` の 5 ファイル（analyze.py / conclusions.py / dump_folds.py / replicate_lovo.py / rules.py） | 未追跡 | 同時に走る判定則の契約の生成物。同期で届いたもの | **違う** |
| 13–19 | `experiments/analysis/error_shape_selectivity/` の 7 ファイル（aggregate.py / breakdown.py / compare_arms.py / sweep_error_shape_selectivity.py / verify_axis2.py / verify_err_rate.py / verify_zero_noise.py） | 未追跡 | 同時に走る別契約の生成物。同期で届いたもの | **違う** |

```
$ git --no-pager diff --name-status origin/phase0..HEAD | grep '^D' | wc -l
13
$ git status --porcelain | grep '^??'
?? experiments/analysis/error_shape_selectivity/
?? experiments/analysis/lovo_decision_rule/
?? tasks/T-2026-08-26-denoise-falsification/audit.md
```

**19 件の違反のうち、本契約が作ったものは 0 件である。**
本契約は `experiments/` へ 1 バイトも書いていない（学習を走らせていないため run が無い）。
未追跡の 2 ディレクトリは他ホストから同期で届いたものであり、**触れていない。**

`M scripts/train_b2a.py` は作業分岐が古いことによる差分であり、作業分岐側の変更ではない
（上記 L363–）。

---

## 台帳への送出

```
$ source scripts/load_env.sh && source .venv/bin/activate && make task-report TASK=T-2026-08-26-denoise-falsification; echo "EXIT=$?"
{
  "task_id": "T-2026-08-26-denoise-falsification",
  "verdict": "stopped",
  "n_issuer_defects": 4,
  "report_sha256": "22995a83c46846e75752bb558e9c1ba72e95b7c6e5ce74e7ab54fbfd2d97cde1",
  "report_bytes": 13513,
  "replaced_blocks": 0
}
EXIT=0
```

**送出は成功した。** 秘匿の検査で止まっていない。資格情報の有無だけを確かめてから送った
（`NOTION_API_KEY` は設定あり・`NOTION_DB_ID` は未設定。**値は出力していない**）。

## PR

```
$ gh pr create --base phase0 --head feat/denoise-falsification …
https://github.com/takuya3h/m2/pull/155
```

**PR #155。送り出しただけの状態ではなく、起票まで完了している。**
分岐 `feat/denoise-falsification` は規定の接頭辞 `feat/` で始まる（L419–428）。
