# RESULT — T-2026-08-09-run-wiring-verification

**実行者:** `lecun` / `exp/lecun-wip-20260703` / `100abd0`
**実行日時:** 2026-08-07T21:06Z 〜 2026-08-07T21:25Z
**判定:** **PARTIAL** — 3 つの配線のうち 2 つが機能。3 つ目（下書きの起票）は既存障害を実測で特定した。

| # | 検証対象 | 結果 |
|---|---|---|
| 1 | `git_autosync.py` の発火 | ✅ **初発火**。commit + push まで到達 |
| 2 | 配備鍵での遠隔操作 | ✅ **成功**。`ls-remote` / `push` とも配備鍵で通った |
| 3 | 契約の識別子を成果物へ刻む | ✅ **成功**。索引・軽量ビューまで到達 |
| （付随） | 下書きの起票（`auto-draft-pr.yml`） | ❌ **失敗**。`AUTOSYNC_PR_TOKEN` が 401。lecun 固有ではない |

---

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | **記載なし** | 対象外（本契約に分母の宣言は無い） |
| `inputs.sigma_policy` | **記載なし** | 対象外（判定を行わないため継承の必要なし） |
| `inputs.frozen_source.ref` | **記載なし** | 対象外。ただし Phase D Step 5 で手動照合を実施（§5 参照） |
| `contract.conventions_rev` | `1201f4f` | **`d422b08` へ実測置換**（SPEC Task 5 Step 1 の手順に従う） |
| `contract.inject_verbatim` | `conventions#env_p0`, `#prohibitions`, `#naming` | 下記に原文を転記 |

### `conventions#prohibitions`（原文）

```
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### `conventions#env_p0`（原文）

```
<a id="env_p0"></a>
## env_p0

学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
数値が変わったまま完走する。

    source .venv-relation-detr/bin/activate   # 検出系
    source .venv/bin/activate                 # 解析・工程系

拡張のロード確認をログに残すこと。
```

### `conventions#naming`（原文）

```
<a id="naming"></a>
## naming

実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。

    {step}_{seq:03d}_{description}_seed{seed}

- `step`: `s0`〜`s9`、または `a1`〜`a7`
- `seq`: 同一 category と step 内の3桁ゼロ埋め連番
- `description`: 実験内容の短い説明
- `seed`: 乱数シード。既定42

転記元: `README.md` の「命名規則」。
```

### `conventions_rev` の差分（WARN の内容）

`1201f4f` → `d422b08` の差分は **+10 / −0**。変更は 2 箇所のみ。

| 箇所 | 内容 |
|---|---|
| `frozen_source` 節（L56 に 9 行追加） | 「検査の適用範囲」を追記。凍結源の照合は `kind: exp` に適用し、それ以外は適用対象外として未実施と記録する |
| 変更履歴テーブル（L143 に 1 行追加） | 上記の記録 |

**原文注入する 3 アンカーはいずれも無変更**（差分ハンクは L56 と L143 の 2 箇所のみ。`prohibitions` L98–108 / `env_p0` L109–119 / `naming` L121–133 のいずれにも掛からない）。
この差分は preflight の `P5 frozen_source_hash = SKIP（kind=impl のため対象外）` として実際に観測でき、**追記と実装が一致していることを実測で確認した**。

---

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（after A） | **PASS** | `git ls-remote origin HEAD` **exit 0** / `45eae0ad…`。装置1 = **17 MiB / 0 %** で空き |
| **G2**（after B） | **PASS** | 成果物 7 ファイル生成。`config.yaml:103` に `task_id: T-2026-08-09-run-wiring-verification` |
| **G3**（after C） | **PASS** | 自動同期は**働いた**。commit `25ea5ef` と push を実測（`on_fail: ask` は発動せず） |

---

## 3. Phase A — 事前確認の実測

### Step 1: 分岐と基盤

| 項目 | 実測 |
|---|---|
| 分岐 | `exp/lecun-wip-20260703` |
| `HEAD..origin/phase0` | **0**（ahead も 0） |
| 未コミットの変更 | 未追跡 2 件のみ。**触っていない** |

未追跡 2 件: `docs/sessions/digest/2026-08-02-846b93b9-4191-47ec-a603-8741c6ac4df8.md`（前セッションの digest）、`tasks/T-2026-08-09-run-wiring-verification/`（本 SPEC 自身）。

### Step 2: 検証系

| 項目 | 実測 |
|---|---|
| `make task-validate`（全 task） | **exit 0** / 10 task / 0 failed |
| `make task-preflight TASK=<本 task>` | **exit 0** / 4 PASS / 4 SKIP / 0 FAIL |
| `tools/` | `validate_task.py` `preflight_task.py` `build_context.py` `fetch_task.py` `session_digest.py` **5/5 存在** |
| skills | `.claude/skills/task` `.codex/skills/task` **両方存在** |

**基盤は届いている。**

### Step 3: 遠隔参照（G1 の一部）

| 項目 | 実測 |
|---|---|
| `remote.origin.url` | `git@github.com:takuya3h/m2.git`（SSH。平文 PAT なし） |
| `remote.origin.pushurl` | `git@github.com:takuya3h/m2.git` |
| `core.sshCommand` | `ssh -F /dev/null -i /home/ubuntu/.ssh/id_lecundeploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new` |
| `git ls-remote origin HEAD` | **exit 0** / `45eae0ad6880d5e0f75a851ab0b05d707638ab04` |

**配備鍵 `id_lecundeploy` での遠隔参照は成功する。** なお `GIT_SSH_COMMAND` を明示せず素の `git ls-remote` で成功した（§5 deviations 参照）。

### Step 4: 演算装置（G1 の一部）

| 装置 | memory.used | util | プロセス |
|---|---:|---:|---|
| **0** | 14354 MiB | **100 %** | PID 4168306（他の利用者）= 14326 MiB |
| **1** | **17 MiB** | **0 %** | なし |

UUID 対応（後段の判定に必須）: 装置0 = `GPU-a0279fdc-dc39-357a-d19f-f1c644bc328c` / 装置1 = `GPU-8f99ff6b-7241-ba0b-9137-879990b50906`。

**装置 0 は使用量にかかわらず選択肢から除外した。** 使ったのは装置 1 のみ。

### Step 5: 最小の学習設定の特定

**`finalize()` を呼ぶ経路は 4 つ**（実測）。

| 呼び出し元 | 行 | metric |
|---|---|---|
| `stage_a_trainer.py` | 554 | `("mAP", best_map)` |
| `phase_trainer.py` | 203 | `("phase_accuracy", …)` |
| `trainer.py` | 236 | `metric` |
| `mmdet_trainer.py` | 298 | `_metric` |

`ExperimentManager.finalize()`（`experiment_manager.py:235`）が `git_autosync.commit_and_push_evidence` を遅延 import する。

| 確認事項 | 実測 |
|---|---|
| 経路 | `train.py:_select_trainer` → step が `s0` かつ `train.real_detector=false` → **`StageATrainer`** → `run()` 末尾で `finalize()` |
| 仮想環境 | **`.venv`**（内蔵 `SimpleDetectionHead` 経路。`.venv-relation-detr` は不要） |
| 学習量の縮小 | `configs/stage/s0_tool_baseline.yaml` の冒頭コメントに記載の smoke override をそのまま使用 |
| 出力先 | `experiments/{category}/{exp_id}/`（`ExperimentManager.setup()` が採番） |
| backbone | `dinov2_vits14_reg4_pretrain.pth` が `~/.cache/torch/hub/checkpoints/` に**キャッシュ済み** → 網羅取得なし |

**`git_autosync` の見送り条件（実装から網羅的に特定）**

| ガード | 条件 | lecun での実測 |
|---|---|---|
| kill-switch | `EGOSURGERY_AUTOSYNC` ∈ {0,false,no,off} | 未設定 → 通過 |
| 1 | repo 内であること | 通過 |
| 2 | **`exp/*` ブランチであること** | `exp/lecun-wip-20260703` → 通過 |
| 3 | **deploy key 構成済み**（`GIT_SSH_COMMAND` / `remote.origin.pushurl` / `core.sshCommand` のいずれかが `--local` に存在） | `pushurl` と `core.sshCommand` の**両方**が local に存在 → 通過 |
| 4 | stage 差分が空でないこと | 7 ファイル → 通過 |

**中断条件（アラートを書く）**: `git add` 失敗 / 秘匿パス denylist / 秘匿内容の正規表現一致 / staged 単一ファイル > 5 MB / commit 失敗 / push 失敗。

---

## 4. Phase B — 実行と刻印

### 識別子の刻印方法: **案A（起動時に設定へ渡す）**

`StageATrainer.setup()` は `manager.setup()` の直後に `manager.save_config(cfg)` を呼び、`save_config` は `OmegaConf.save(config, resolve=True)` で **Hydra cfg 全体をそのまま `config.yaml` に書き出す**。したがって CLI で `+task_id=…` を足せば刻印できる。**案B（生成後の追記）は採らなかった。**

GPU を使う前に `--cfg job` で合成のみ検証し、`task_id` が 103 行目に載ることを確認してから起動した。

### 実行したコマンド

```bash
export CUDA_VISIBLE_DEVICES=1
source .venv/bin/activate
PYTHONPATH=src python -m egosurgery.train \
  stage=s0_tool_baseline \
  +task_id=T-2026-08-09-run-wiring-verification \
  experiment.description=wiring_verification \
  train.real_detector=false model.backbone=dinov2_vits14_reg \
  data.limit=16 data.img_size=224 train.epochs=1 \
  train.freeze_backbone=true data.num_workers=0 \
  logging.wandb_enabled=false seed=42
```

### 所要時間（実測）

| 時刻 | 事象 |
|---|---|
| 21:16:59 | `env_p0` 拡張ロード確認を記録 |
| 21:17:01 | 学習開始 |
| 21:17:13 | `finalize()` → 自動 commit `25ea5ef` |
| 21:17:16 | 学習終了（**exit 0**） |

**学習の所要時間は 15 秒**（上限 30 分に対し大幅に下回る）。

### `env_p0` の要求（拡張のロード確認）

preflight の `P2 cuda_ext_loaded` は `plan.env.preflight` に記載が無いため **SKIP**（＝未実施）だった。規約は記録を要求しているため、手動でログに残した。

```
python: /home/ubuntu/slocal2/m2/.venv/bin/python
VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv
CUDA_VISIBLE_DEVICES=1
torch 2.1.2+cu118
cuda_available True
device_count 1
device_name NVIDIA RTX A6000
```

**無言の CPU フォールバックは起きていない。**

### 生成された成果物（G2）

`experiments/baselines/**s0_040_wiring_verification_seed42**/`

| ファイル | 有無 | bytes |
|---|---|---:|
| `config.yaml` | あり | 2110 |
| `metrics.json` | あり | 226 |
| `notes.md` | あり | 340 |
| `command.sh` | あり | 482 |
| `git_commit.txt` | あり | 41 |
| `per_class_ap.json` | あり | 324 |
| `server.txt` | あり（`lecun`） | 6 |

**刻印:** `config.yaml:103` → `task_id: T-2026-08-09-run-wiring-verification`

**指標（参考値。研究上の意味は無い）:** `mAP=0.0002771509158176216` / `epoch=1`。
16 枚・1 epoch・凍結 backbone・内蔵 `SimpleDetectionHead` による配線確認であり、**性能の主張には一切使えない。**

### 装置 0 への非接触（Phase B Step 5）

実行中の実測: 私のプロセス **PID 239225 は `GPU-8f99ff6b`（装置 1）** に割り当てられた。装置 0 には他の利用者の PID 4168306 のみ。
実行後の実測: 装置 0 は PID 4168306 のみ。**自分の処理は装置 0 に一度も現れていない。** `other_user_gpu_touched` は発生していない。

---

## 5. Phase C — 自動同期の実測

### 発火状況: **発火した**

| 配線 | 結果 | 実測 |
|---|---|---|
| ① 自動記録（commit） | ✅ | `25ea5ef s0(wiring_verification): mAP=0.000277151 seed42 [auto-sync]` @ 21:17:13 |
| ② 自動送出（push） | ✅ | `origin/exp/lecun-wip-20260703` = `25ea5ef` / `origin..HEAD` = **0** |
| ③ 下書きの起票（PR） | ❌ | `gh pr list --head … --state open` → **空** |

自動 commit の内容（`add -A` していないことの証拠）:

```
Auto-committed by egosurgery finalize hook.
Sync-Source: lecun
Experiment: baselines/s0_040_wiring_verification_seed42

 7 files changed, 156 insertions(+)
```

`checkpoints/` `logs/` `predictions/` `visualizations/` `wandb/` は commit されていない（Syncthing 層の担当）。

### `sync-alerts.log`: `git_autosync` 行は **0 件**

**これは不発火の証拠ではない。** `git_autosync.py` は `_skipped()` でも成功時でも `_write_alert` を呼ばない。アラートが書かれるのは中断（`aborted` / `committed_no_push`）のときだけである。
したがって **0 件は「中断が一度も起きなかった」ことを意味する**。SPEC Phase C Step 3 の判定条件は誤りである（§7 deviations 参照）。

なお同ログには keeper 由来の `auto-push` / `auto-merge` 行が存在するが、これは `git_autosync` とは別系統である。

### ③ が止まった箇所: **`AUTOSYNC_PR_TOKEN` の失効（401）**

push は workflow を起動していた。**「走らなかった」のではなく「走って失敗した」。**

```
run 31219429949  auto-draft-pr  exp/lecun-wip-20260703  push  failure  12s  2026-08-07T21:17:20Z
```

失敗ログ（実測）:

```
GH_TOKEN: ***                                              ← secret は設定されている（-z ガードは通過）
HTTP 401: Bad credentials (https://api.github.com/graphql)
Try authenticating with:  gh auth login -h github.com
##[error]Process completed with exit code 1.
```

`.github/workflows/auto-draft-pr.yml` は「未設定なら明示エラー」の防御を持つが、**失効を検出する防御は持たない**。エラーメッセージは「secret AUTOSYNC_PR_TOKEN が未設定」と読めるが、実際には**設定済みかつ無効**である。

**lecun 固有ではない。** 直近 10 run が全て failure で、対象は `exp/efros-*` `exp/Andrew-*` `exp/Bengio-*` `exp/he-*` `exp/lecun-*` の全ホストに及ぶ。最古の確認は 2026-08-07T18:55Z。
**本 task はこれを直していない**（SPEC の指示どおり。修正は別 task）。

---

## 6. Phase D — 索引への反映

### 行数の変化: **749 → 784（+35）**。SPEC の期待（+1）と異なる

| ファイル | 前 → 後 | 差 |
|---|---|---:|
| `index.csv` | 749 → 784 | **+35** |
| `experiments.csv` | 206 → 215 | +9 |
| `per_class.csv` | 6210 → 6588 | +378 |
| `verdicts.csv` | 1038 → 1038 | **±0** |
| **解析対象（`excluded=False`）** | **701 → 702** | **+1** |

**+35 の内訳 = 私の run 1 件 + 退避済み 34 件（全て `excluded=True`）**

| 追加された 34 件 | 件数 | `exclusion_reason` |
|---|---:|---|
| `_smoke_prior_simplehead` / `_smoke_v2_part3` / `_smoke_e3` / `_pre_redo_s0_smoke` | 19 | `smoke_test` |
| `_prior_no_eval_recipe` | 6 | `superseded` |
| `_failed_num_workers_zero` | 5 | `failed_run` |
| `_aborted_codetr_no_config` / `_aborted_s0_cuda_visible_misconfig` | 4 | `aborted_run` |

削除された run は **0 件**。

**原因（実測に基づく）:** 収穫器は git ではなく**ディスクを走査**する（`EXPERIMENTS = REPO_ROOT / "experiments"`）。commit 済みの 749 行は、これら 34 個の退避ディレクトリを**持たないホスト**で生成されたものである。lecun のディスクには存在するため、lecun で再生成すると現れる。**私の run が増やしたものではない。**

**除外規約は正しく働いた。** 34 件すべてに `excluded=True` と理由が付き、解析対象には入っていない。除外マーカーは 16 件あり、末尾 `_` のものは前方一致（B-25 / B-29 の修正が入っている）。

既存 run の JSON 12 件も変更されたが、**変更は `harvest_warnings` の文言のみ**（「eval_recipe_id が 2 通り → 3 通り」）。数値・指標・`experiment_id` の分離子はいずれも不変。

この事象は `make task-validate` でも機械的に検出された:

```
WARN [L2-8] index.csv:       起票時 749 → 現在 784（分母が動いています）
WARN [L2-8] experiments.csv: 起票時 206 → 現在 215（分母が動いています）
```

**利用者へ提示し、SPEC どおり全て commit する判断を得た。**

### 索引に載った行

```
ledger_key : baselines__s0_040_wiring_verification_seed42
task_id    : T-2026-08-09-run-wiring-verification
excluded   : False        exclusion_reason: (空)
host       : lecun        step: s0        description: wiring_verification
```

### 軽量ビューの充足率: **0.0% → 0.1%**

| 項目 | 前 | 後 |
|---|---|---|
| `context/auto/STATE.md` | `- task_id を持つ run: 0 / 749 (0.0%)` | `- task_id を持つ run: 1 / 784 (0.1%)` |
| `make context` | — | **exit 0** |
| `make context-check` | — | **exit 0** |

`context/auto/experiments_summary.csv` に独立グループが出現:

```
baselines/s0/wiring_verification@val , … , T-2026-08-09-run-wiring-verification , n_runs=1 , n_seeds=1 , hosts=lecun , split=val
```

### Step 5: 検査系の未確認経路

| 項目 | 実測 | 判定 |
|---|---|---|
| 拡張の読み込み（`.venv-relation-detr`） | `import: OK` + `Loading extension module MultiScaleDeformableAttention...` | ✅ **合格経路は実在する** |
| 凍結源の sha256 | `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` | ✅ `conventions.md:46` と**一致** |
| 凍結源のサイズ | `195421066` bytes | ✅ `conventions.md` の記載と**一致** |

**拡張の読み込みは、SPEC のコマンドをそのまま実行すると `ModuleNotFoundError: No module named 'models'` になる。** これは仮想環境の欠落ではなく `cwd` の不足による偽陰性である。`models` は `third_party/Relation-DETR/` 配下のパッケージのため、`cd third_party/Relation-DETR` してから実行する必要がある。正しい `cwd` では CUDA 拡張のロードまで到達する（§7 deviations 参照）。

---

## 7. 接頭辞を付けなかった判断についての所見

**起票者の判断（動作確認用の接頭辞を付けない）は正しかった。** 実測で裏づけられる。

- 収穫器の `EXCLUSION_RULES` は 16 マーカーを持ち、`_smoke_prior_simplehead` `_smoke_v2_part3` `_smoke_e3` `_pre_redo_s0_smoke` 等がすべて含まれる。接頭辞を付けていたら `excluded=True` となり、**索引に載っても解析対象から外れ、充足率は 0.0% のまま動かなかった**。検証③は成立しなかった。
- 実際、今回の再生成で拾われた退避 34 件がまさにその状態であり、**接頭辞を付けた場合に何が起きるかを同じ索引の中で観測できた**。

**ただし、接頭辞を外すだけでは不十分だった。** 起票者の想定どおり既定の `description` のままだと実験フォルダは `s0_0NN_tool_baseline_seed42` となり、**本物の S0 基準点 run と名前で区別できない**。`experiment_id` は `<group>/<step>/<description>@<split>~<frozen_source_tag>` で構成されるため、同じ `description` を使うと**同一グループに束ねられ、Δ 基準点群を汚染しうる**。

そこで `experiment.description=wiring_verification` を指定した。結果として:

- 除外マーカーのいずれにも一致しない → 索引に載る（③ が成立）
- `experiment_id` が `baselines/s0/wiring_verification@val` として**独立**する → 既存の `tool_baseline` 群に混ざらない
- 対照実験の宣言（`delta`）を持たないため、既存の比較に影響しない

**申し送り:** 今後同種の「配線確認 run」を作る場合、`description` を用途が分かる語にする規約を設けるべきである。除外規約に頼ると索引から消え、既定名に頼ると本走と混ざる。**両方を避ける唯一の手段が `description` の指定である。**

---

## 8. 受入基準の充足

| # | acceptance | 結果 | 実測 |
|---|---|---|---|
| 1 | 配備鍵での遠隔参照が成功する | ✅ | `ls-remote` exit 0 / `id_lecundeploy` |
| 2 | 最小の学習が一本完走し成果物が生成される | ✅ | exit 0 / 15 秒 / 7 ファイル |
| 3 | 生成された設定に契約の識別子が含まれる | ✅ | `config.yaml:103` |
| 4 | 自動同期の発火または不発火の理由が実測で記録されている | ✅ | 発火。`25ea5ef` + push |
| 5 | 索引に契約の識別子を持つ行が現れる | ✅ | 1 件 / `excluded=False` |
| 6 | 軽量ビューの契約充足率が更新される | ✅ | 0.0% → 0.1% |
| 7 | `make task-validate` が exit 0 | ✅ | exit 0（WARN 2 件は §6 の分母変動） |
| 8 | `make task-preflight` が exit 0 | ✅ | 4 PASS / 4 SKIP / 0 FAIL |

## 9. 完了判定（SPEC Task 5 Step 3）

| # | 判定 | 期待 | 実測 |
|---|---|---|---|
| 1 | 基盤が動く | 両方 exit 0 | ✅ validate exit 0 / preflight exit 0 |
| 2 | 遠隔参照が成功 | 成功 | ✅ exit 0 |
| 3 | 学習が完走 | 成果物あり | ✅ 7 ファイル |
| 4 | 識別子が刻まれた | `config.yaml` に含まれる | ✅ L103 |
| 5 | 装置 0 に触れていない | 自分の処理が無い | ✅ UUID で確認 |
| 6 | 自動同期の結果が記録 | 発火または理由 | ✅ 発火 |
| 7 | 索引に載る | 1 件 | ✅ 1 件（**総行数は +35。§6 参照**） |
| 8 | 充足率が動く | 0 から変化 | ✅ 0.0% → 0.1% |
| 9 | 軽量ビューが整合 | `context-check` が 0 | ✅ exit 0 |
| 10 | 契約検証が通る | exit 0 | ✅ exit 0 |
| 11 | 実行前検査が通る | exit 0 | ✅ exit 0 |
| 12 | 全体テストが不変 | **本ホストでの実測値** | ✅ **前 5 failed, 247 passed → 後 5 failed, 247 passed**。失敗テスト名も同一の 5 件 |
| 13 | 禁止領域が無変更 | 出力なし | ✅ 出力なし |

**判定12 の基準点（本 task 開始前・2026-08-07 21:07 実測）**

```
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
5 failed, 247 passed, 22 warnings in 29.25s
```

開始前に測ったため、別ホストの値とは比較していない。**5 件は本 task 着手前から赤であり、本 task は増やしていない。** 学習・評価コードを変更していないため修正もしていない。

### preflight で SKIP された項目（合格ではない）

| 項目 | 理由 |
|---|---|
| `P2 cuda_ext_loaded` | `plan.env.preflight` に記載なし → **未実施**。§4 で手動記録した |
| `P3 deterministic_flags` | `plan.env.preflight` に記載なし → 未実施 |
| `P4 prereg_committed` | `kind=impl` のため対象外 |
| `P5 frozen_source_hash` | `kind=impl` のため対象外。§6 Step 5 で手動照合した |

---

## 10. deviations（指示書どおりにしなかった箇所）

### D-1. SPEC の判定条件が誤っていた — 自動同期の発火判定

- **指示:** Phase C Step 3「`sync-alerts.log` に『該当行なし』の場合、発火していない。その事実をそのまま記録する」
- **実際:** 該当行は 0 件だったが、**自動同期は発火していた**。判定条件を「commit subject に `[auto-sync]` が入るか（`git_autosync.py:417`）＋ `origin..HEAD` の増分」に置き換えて測定した。
- **理由:** `git_autosync.py` は `_skipped()` でも成功時でも `_write_alert` を呼ばない。アラートが書かれるのは中断時のみ。SPEC の条件に従っていた場合、**発火したのに「不発火」と誤報告していた。**
- **分類:** **SPEC の欠陥**（起票者が申し送りで警告していた「同型の誤り」に該当）

### D-2. SPEC の検査コマンドが偽陰性を出した — 拡張の読み込み

- **指示:** Phase D Step 5 の `bash -c 'source .venv-relation-detr/bin/activate && python -c "importlib.import_module(\"models.bricks.relation_transformer\")"'` をリポジトリ直下で実行
- **実際:** `ModuleNotFoundError: No module named 'models'` となる。`cd third_party/Relation-DETR` を足して再測定したところ `import: OK` かつ CUDA 拡張 `MultiScaleDeformableAttention` のロードまで到達した。
- **理由:** `models` は `third_party/Relation-DETR/` 配下のパッケージであり、リポジトリ直下からは import パスに乗らない。仮想環境の問題ではない。
- **分類:** **SPEC の欠陥**

### D-3. `description` を既定値から変更した

- **指示:** SPEC は接頭辞を付けないことのみ指定し、`description` には言及していない
- **実際:** `experiment.description=wiring_verification` を指定した（既定は `tool_baseline`）
- **理由:** 既定のままだと `s0_0NN_tool_baseline_seed42` となり本物の S0 基準点と名前で区別できず、`experiment_id` が同一グループに束ねられて Δ 基準点群を汚染しうる。**利用者へ提示し承認を得た。**
- **分類:** **判断が必要だった**

### D-4. W&B / Notion の追跡を無効にした

- **指示:** SPEC は言及なし。ただし `CLAUDE.md` は「W&B で**必ず**全ての実験を追跡」と定める
- **実際:** `logging.wandb_enabled=false` で実行し、`.env` / `scripts/load_env.sh` に触れなかった（`configs/stage/s0_tool_baseline.yaml` の既定は `wandb_enabled: true`）
- **理由:** 本 task の目的は git 自動同期の配線検証であり、未認証の W&B（`~/.netrc` なし・`WANDB_API_KEY` 未設定）を絡めると無関係な失敗要因が入る。また `.env` への接触は `CLAUDE.md` の要承認事項。実験Run台帳への投稿も、研究 run ではないため見送った。**利用者へ提示し承認を得た。**
- **分類:** **判断が必要だった**

### D-5. 発火前の基準点の採取が 9 秒遅れた

- **指示:** Phase C は発火後の観測を求めるのみで、事前基準点の採取時刻は指定されていない
- **実際:** `git log` / `sync-alerts.log` の「発火前」値を 21:17:22 に採取したが、実際の発火は 21:17:13 だった。**採取値は事後のものである。**
- **理由:** 学習が 15 秒で完走することを見込めておらず、実行中に採取するつもりが間に合わなかった。
- **影響:** 復元可能。`25ea5ef^ == c905f19`（セッション開始時の HEAD）かつ `[auto-sync]` を含む commit は `25ea5ef` の 1 件のみのため、**発火前は 0 件と確定できる**。数値の捏造はしていない。
- **分類:** **判断が必要だった**（測定手順の不備）

### D-6. 遠隔参照で `GIT_SSH_COMMAND` を明示しなかった

- **指示:** `GIT_SSH_COMMAND="$(git config --get core.sshCommand)" git ls-remote origin HEAD`
- **実際:** 素の `git ls-remote origin HEAD` を実行した（exit 0）
- **理由:** `core.sshCommand` は git config に入っているため環境変数で包む必要がなく、**包まない方が「通常運用で配備鍵が効くか」の検証として厳密**である。包んだ場合、`_deploy_key_configured` の 3 経路のうち `GIT_SSH_COMMAND` 経路だけを検証したことになりかねない。
- **分類:** **判断が必要だった**

### D-7. 終了コードの測定方法を変えた

- **指示:** `make task-validate 2>&1 | tail -20; echo "exit=$?"`
- **実際:** ファイルへリダイレクトしてから `echo "exit=$?"` で測定した
- **理由:** 本ホストのシェルは zsh であり、`$?` はパイプ末尾（`tail`）の終了コードを返す。SPEC の書き方では `make` の終了コードを測れない。
- **分類:** **環境差**

### D-8. `conventions_rev` を実測値へ置換した

- **指示:** SPEC Task 5 Step 1 が「実行者が実測して置換する。**これは逸脱ではなく手順である**」と明記
- **実際:** `spec.yaml` の `conventions_rev` を `1201f4f` → `d422b08` に更新した
- **分類:** 手順どおり（記録のため列挙）

---

## 11. 未解決・申し送り

### 11.1 `AUTOSYNC_PR_TOKEN` の失効（全ホスト影響）

`.github/workflows/auto-draft-pr.yml` が全ホストで failure。secret は設定済みだが **401 Bad credentials**。fine-grained PAT の再発行と Actions secret の更新が必要。
**ワークフロー側の防御にも欠落がある**: 未設定は検出するが失効は検出せず、エラーメッセージが「未設定」と誤誘導する。**修正は別 task**（本 task は修正しない指示）。

### 11.2 索引の分母がホスト依存である

収穫器はディスクを走査するため、退避ディレクトリの有無で `index.csv` の行数がホストごとに変わる。今回 lecun で再生成したことで +34 行が入った。他ホストで再生成すると再び消え、往復する可能性がある。
**解析対象（`excluded=False`）は影響を受けない**が、`created_from.counts` を根拠にする検査（L2-8）は今後もホスト差で WARN を出す。運用方針の決定が必要。

### 11.3 生成した run の `notes.md` が雛形のまま

`ExperimentManager` が置く雛形（「（ここに記入）」）のまま自動 commit された。`description` と `config.yaml`（`data.limit=16` / `epochs=1`）から用途は追えるが、`mAP=0.000277` を実験結果と誤読される余地はある。埋めるべきかは §12 の後始末の判断に含めて仰ぐ。

### 11.4 `plan.env.preflight` に `cuda_ext_loaded` が無い

GPU 学習を伴う契約でありながら、CUDA 拡張のロード検査が契約側で要求されていない（P2 が SKIP）。`env_p0` は記録を要求しているため、**検査器と規約の間に隙間がある**。今回は手動で埋めた。今後 GPU を使う契約では `plan.env.preflight` に `cuda_ext_loaded` を入れることを推奨する。

---

## 12. 後始末について（判断を仰ぐ）

**生成した成果物を残すか消すかは、指示を待つ。自分の判断で削除しない。**

対象:

| 対象 | 状態 |
|---|---|
| `experiments/baselines/s0_040_wiring_verification_seed42/` | 証跡 7 ファイルは `25ea5ef` で commit 済み・push 済み |
| 同 `checkpoints/` `logs/` `predictions/` `visualizations/` `wandb/` | 未追跡（Syncthing 層）。ローカルに残存 |
| `runindex/` `context/auto/` | `100abd0` で commit 済み（+34 行の退避 run を含む） |

判断が必要な点:

1. この run を索引に残すか、除外規則（`RUN_EXCLUSIONS` 等）を足して解析対象から外すか
2. 外す場合、`context/auto` の充足率は再び 0.0% に戻る（③ の証拠が消える）
3. `notes.md` を埋めるか（§11.3）
4. `100abd0` を他ホストへ配るか（+34 行の扱い）

---

## 13. 数値の出所

**すべての数値は本ホスト（lecun）での実測である。** 未測定の項目は無い。
`mAP=0.0002771509158176216` は 16 枚・1 epoch・凍結 backbone・内蔵 `SimpleDetectionHead` による配線確認の副産物であり、**研究上の性能主張には使えない。**
記憶や他ホストの値を根拠にした箇所は無い（判定12 は開始前に本ホストで測り直した）。
