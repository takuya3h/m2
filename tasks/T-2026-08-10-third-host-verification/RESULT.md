# RESULT — T-2026-08-10-third-host-verification

**実行ホスト:** `bengio`
**分岐:** `exp/Bengio-wip-20260703`
**実行日:** 2026-08-08 UTC
**判定:** **PASS（契約基準）** — 三台目ホストで基盤・最小学習・自動同期を再現し、追跡外退避物0件の索引を生成した。

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | 記載なし | 対象外 |
| `inputs.sigma_policy` | 記載なし | 対象外。数値の改善判定を行わない |
| `inputs.frozen_source.ref` | 記載なし | 対象外。preflight の P5 も `kind=impl` のため SKIP |
| `contract.conventions_rev` | `1201f4f` | `d422b08` へ実測置換 |
| `contract.inject_verbatim` | `conventions#env_p0`, `conventions#prohibitions`, `conventions#naming` | 下記に原文を転記 |

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

`1201f4f..d422b08` の差分は `frozen_source` の検査適用範囲と変更履歴への追記であり、上記3アンカーの原文には差分が無かった。

## 2. Phase A — 基盤の再現性

### 開始前の実測

| 項目 | 実測 |
|---|---|
| 分岐 | `exp/Bengio-wip-20260703` |
| 開始時 HEAD | `bcde0a0` |
| `tools/*.py` | 16 ファイル |
| task skill | `.claude/skills/task` と `.codex/skills/task` が存在 |
| `jsonschema` | 4.26.0 |
| `yaml` | 読み込み成功 |
| pytest 基準 | 5 failed、247 passed、23 warnings |

### 依存の一括導入

`make setup` は `uv pip install --python .venv/bin/python -e ".[dev]"` を選択した。1回目と2回目はいずれも exit 0 で、`jsonschema` と `yaml` の読み込みも成功した。実行前パッケージ一覧は108行、SHA-256 は `fbea96add4e53cca6fc580e45ec163984e643be207a283a9a76dac8fd1df14b5`。実行前後の一覧差分は0行だった。

`torch` は `2.1.2+cu118` のまま。`.venv/bin/python -m pip` は `No module named pip` で、lecun と同じく仮想環境外の `uv` が導入手段になった。

全13 task の検証は0 failed。本 task の preflight は `4 PASS / 4 SKIP / 0 FAIL`。SKIP は `cuda_ext_loaded`、`deterministic_flags`、`prereg_committed`、`frozen_source_hash` である。

**G1: PASS。** 一括導入、冪等性、依存読み込み、task 検証、preflight がすべて動いた。

## 3. Phase B — 最小の学習と配線

### 遠隔と装置

`git ls-remote origin HEAD` は exit 0 で `45eae0ad6880d5e0f75a851ab0b05d707638ab04` を返した。fetch と push の URL は `git@github.com:takuya3h/m2.git`、`core.sshCommand` は未設定だった。

最初の起動直前確認では GPU 0 と GPU 1 が各約6.5 GiB使用中だったため停止した。再開時の 2026-08-08T04:40:15Z は計算プロセス0件で、GPU 0 は 35 MiB、GPU 1 は 20 MiB。GPU 0 を固定した。

### 実行コマンド

```bash
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -m egosurgery.train \
  stage=s0_tool_baseline \
  +task_id=T-2026-08-10-third-host-verification \
  experiment.description=wiring_verification \
  train.real_detector=false model.backbone=dinov2_vits14_reg \
  data.limit=16 data.img_size=224 train.epochs=1 \
  train.freeze_backbone=true data.num_workers=0 \
  logging.wandb_enabled=false seed=42
```

### 成果物と所要時間

2026-08-08T04:40:34Z から 04:40:46Z まで12秒、exit 0。出力先は `experiments/baselines/s0_041_wiring_verification_seed42/`。`config.yaml`、`metrics.json`、`notes.md`、`command.sh`、`git_commit.txt`、`server.txt`、`per_class_ap.json` の7点が存在し、`config.yaml:103` に本 task ID、`server.txt` に `bengio` が記録された。

`metrics.json` の実測値は次のとおり。性能主張には使用しない。

| 指標 | 値 |
|---|---:|
| `epoch` | 1 |
| `mAP` | 4.98194465959574e-05 |
| `val/mAP` | 4.98194465959574e-05 |
| `val/mAP_50` | 0.0003802961261577104 |
| `val/mAP_75` | 5.277713272393338e-06 |
| `val/AP_rare` | 0.0003487361261717018 |
| `val/AP_common` | 0.0 |

`per_class_ap.json` は `Skewer` が 0.0006974722523434036、残る14クラスは0.0。内蔵 `SimpleDetectionHead` へのフォールバック警告があり、前例と同じ配線確認用の条件である。

### 自動同期

学習 run の自動同期は commit `5f7e255` を生成し、遠隔との差0まで送出した。索引再生成後まで再確認しても open PR は0件。GitHub Actions run `31240000157` は `AUTOSYNC_PR_TOKEN` が無効な状態として exit 1 だった。

最終 task commit `8083d5d` の push から45秒後、常駐 `m2-sync.sh` が Draft PR #53 を起票した。同じ push の Actions run `31240620351` は無効なトークンで失敗した。資格情報の値には触れていない。

**G2: PASS。** 必須成果物7点と task ID 刻印を実測した。自動記録と自動送出は再現し、起票不成立の理由も Actions の生ログで確認した。

## 4. Phase C — 退避物を含まない索引

### 再生成前後

| CSV | 再生成前の物理行数 | 再生成後の物理行数 | 再生成後 MD5 |
|---|---:|---:|---|
| `index.csv` | 750 | 752 | `33744b84345c81f55d91984ecfabb946` |
| `experiments.csv` | 207 | 208 | `ee39f7f40dc6d5ab6abee428162772bc` |
| `per_class.csv` | 6211 | 6241 | `1c7c94129eecc4bec10b2e7c68336c3c` |
| `verdicts.csv` | 1039 | 1039 | `96d714988b20733b234700b42c7b315e` |

run 数は749から751へ増加した。追加は統合で加わった `s0_040_wiring_verification_seed42` と本 task の `s0_041_wiring_verification_seed42` の各1件。削除0件、既存749行の変更0件だった。task ID を持つ行は2件。

除外理由は、理由なし703、`identity_check` 24、`smoke_test` 7、`known_bad_split` 6、`failed_run` 6、`wrong_frozen_source` 3、`mislabeled_arm_all_not_film` 2。全751行の path を Git 追跡状態と照合し、追跡外経路は0件だった。lecun 固有の退避34件は現れなかった。

`make context` と `make context-check` はともに exit 0。`context/auto/STATE.md` の task ID 充足率は `2 / 751 (0.3%)`。索引 commit は `64576f3`。

**G3: PASS。** 退避物0件を除外理由と Git 追跡状態の二経路で確認し、749から751への増分を一次証跡2件で説明した。

## 5. 完了判定

| # | 判定 | 実測 | 結果 |
|---:|---|---|---|
| 1 | 依存の一括導入 | `読み込み OK` | PASS |
| 2 | 冪等 | 2回目も exit 0 | PASS |
| 3 | 固定依存が不変 | `torch 2.1.2+cu118`、一覧差分0 | PASS |
| 4 | 検証系が動く | validateとpreflightがexit 0 | PASS |
| 5 | 学習が完走 | 12秒、exit 0 | PASS |
| 6 | 識別子が刻まれた | `config.yaml:103` | PASS |
| 7 | 自動同期の結果 | commitとpush成功、起票失敗理由を実測 | PASS |
| 8 | 記述が雛形でない | `notes.md` を実測値で更新 | PASS |
| 9 | 退避物が含まれない | 追跡外経路0 | PASS |
| 10 | 行数が説明できる | 749に2件追加、削除0、既存変更0 | PASS |
| 11 | 軽量ビューが整合 | context-check exit 0 | PASS |
| 12 | 充足率が動く | 0から0.3パーセント | PASS |
| 13 | 契約検証 | exit 0 | PASS |
| 14 | 実行前検査 | `4 PASS / 4 SKIP / 0 FAIL` | PASS |
| 15 | 試験の失敗数が不変 | 前後とも5 failed、247 passed | PASS |
| 16 | 禁止領域が無変更 | 契約基準、task開始基準、working treeの3基準で出力なし | PASS |

最終 pytest は `5 failed, 247 passed, 21 warnings`。開始前は警告23件だったため警告数は2件減ったが、失敗数と通過数は不変で、新規失敗は無い。

## 6. 残る未検証項目と申し送り

- bengio 生成版を索引の正本として採用する最終判断は利用者に委ねる。実測上は追跡外退避物0件で正本候補の条件を満たす。
- `AUTOSYNC_PR_TOKEN` の有効化後に Actions 経由の起票成功を再検証する必要がある。自動記録と自動送出は通常のSSH鍵経路でも成功済み。
- preflight の `cuda_ext_loaded` と `deterministic_flags` は契約指定が無く SKIP。`prereg_committed` と `frozen_source_hash` は impl のため対象外。
- 既存5テスト失敗は残っている。本 task 前後で件数は不変であり、本 task では修正していない。
- 本 run は前例との設定一致を優先して W&B を無効にしたため、W&B 上の追跡記録は無い。研究性能の測定には使えない。

## 7. deviations

1. `apply_patch` は環境の `bwrap` namespace エラーで使用不能だった。部分適用が無いことを確認し、同じ unified diff を `git apply` で適用した。
2. 最初の GPU 起動直前に両装置が使用中だったため、契約の停止条件に従って停止した。利用者の再開指示後、両装置が空いたことを再測定して GPU 0 で実行した。
3. SPEC の `make ... | tail; echo $?` はパイプ終端の終了コードを返しうるため、`set -o pipefail` を付けて make 本体の失敗を隠さない形で実行した。
4. Python 実行は環境規約に従い、裸の `python` ではなく `.venv/bin/python` または activate 済み venv を用いた。
5. 一般則では全実験をW&B追跡するが、本契約は前例と同じ最小配線設定を求め、前例コマンドが `logging.wandb_enabled=false` だったため、ホスト差の切り分けを優先して同じ設定を採用した。
6. 索引 commit 後の最終 `context-check` は、軽量ビューの生成元 commit が旧値だったため一度 exit 2 になった。`make context` で `64576f3` を反映し、再検査 exit 0 を確認した。

## 8. 証拠 commit

| commit | 内容 |
|---|---|
| `5f7e255` | 最小 wiring verification run の7点証跡を自動記録・送出 |
| `64576f3` | 退避物を含まない索引と軽量ビュー、host parity を記録 |
| `8083d5d` | RESULT、実験ログ、受け皿、最終 context provenance を記録 |
