# 指示書 #09 — lecun 実施報告（2026-08-02）

全実験サーバーのリポジトリ同期（データ保全）キャンペーンにおける **lecun** の実施記録。
§3 調査（読み取り専用）→ §4 報告 → §5 実行 → film 6 run 回収 → `/tmp` 棚卸し、の順で実施した。

- 実施ホスト: `lecun` / `/home/ubuntu/slocal2/m2` / ブランチ `exp/lecun-wip-20260703`
- 作成コミット: `928060f`（third_party 保全）、`1ce32f6`（phase0 merge）、`0f6b565`（film 6 run 回収）
- PR: **#17 を更新**（base=phase0 / MERGEABLE / 未マージ）

---

## 0. 要約

lecun は実験の 59%（362 run）を保有する最大のホスト。**git 軽量層は完全に健全**だった
（完走 run 取りこぼし 0 / 来歴取りこぼし 0 / ディスク差 34 は全件が意図的除外）。

本タスクで解消した損失と、新たに判明した問題は以下。

| 区分 | 内容 | 状態 |
|---|---|---|
| 保全 | `third_party` の未追跡 28 実装（lecun のディスクにしか無かった） | ✅ `third_party_snapshot/lecun/` に保全 |
| 保全 | T1b-FiLM arm 6 run（experiments に未登録・Bengio 側で消失） | ✅ `/tmp` 原本から無損失回収 |
| 配布 | 分析システム `runindex/`（615 run） | ✅ merge により到着 |
| 秘密 | fetch URL の PAT 平文埋め込み | ✅ SSH 化（revoke は未実施） |
| 🔴 新規 | **B-25**: 退避 34 run が除外フラグ無しで解析対象に混入 | 未対応（報告のみ） |
| 🔴 新規 | **直下 `transfer/` 29 run が runindex から構造的に不可視** | 未対応（報告のみ） |
| 🔴 新規 | **B-20 の解釈訂正**: 評価は非決定的ではなく、評価系の版が 2 つある | README に記録 |
| ⚠️ 新規 | PR #1（→ master）が push で 6,369 ファイルに膨張 | 要判断 |
| ⚠️ 新規 | 指示書対象外のノードが 4 つ稼働、うち `aolab` は実データ保有 | 要判断 |

---

## 1. §3 調査結果（読み取り専用）

### 1.1 origin との関係
指示書の前提値と完全一致。`origin/phase0 = fdd3f01`、**ahead 7 / behind 29**、上流設定あり・未 push なし。
experiments 差分 506 ファイル（全て A＝新規、削除・変更ゼロ）。

### 1.2 取りこぼしの有無 — **ゼロ**

| 項目 | 実測 |
|---|---|
| 完走 run（metrics.json 持ち）で未追跡 | **0 件** |
| 未追跡の `git_commit.txt` / `server.txt` | **0 件**（`6d97e86` の 102 run 回収で解消済） |
| ディスク上 metrics.json | 721 |
| 追跡済み metrics.json | 687 |
| 差 | **34（全件が意図的除外）** |

差 34 の内訳（すべて `.gitignore:149-159` の退避フォルダ、除外規約キーワードに合致）:
`_prior_no_eval_recipe` 6 / `_pre_redo_s0_smoke` 6 / `_smoke_v2_part3` 6 /
`_smoke_prior_simplehead` 6 / `_failed_num_workers_zero` 5 / `_aborted_codetr_no_config` 3 /
`_smoke_e3` 1 / `_aborted_s0_cuda_visible_misconfig` 1

`.gitignore` 非該当 **0 件**、除外規約キーワード非合致 **0 件** を実測で確認。

### 1.3 未追跡 10 ディレクトリの正体
6 点証跡を持たないため上記の集計には現れないが、中身に val 指標と予測を保持していた。
**全 121 ファイルが `logs/` `predictions/` 配下にあり `.stignore` 43-51 行の同期対象**＝
既に Syncthing 層で保護されており、データ消失リスクは無い。

- `transfer/_smoke_*` 3 dir — 除外規約該当、回収不要
- `transfer/_p0_identity_{ctrl,inj}_seed{42,123,456}` 6 dir — **`epochs:0` / `best_epoch:-1` /
  `best_is_init:true`、inj と ctrl の mAP が完全一致（0.7302938994613697）**＝
  学習ゼロの恒等性サニティチェック。研究結果ではなく実装検証。
- `hand2det_dev/` — 21 サブラン / 671M

### 1.4 自動同期（Syncthing keeper）— 健全
`keeper.sh`(pid 1071) + `syncthing serve`(pid 1079/1104) が 7/18 から常駐（flock 常駐・cron/systemd 不使用）。
`.stignore` は phase0 の `.stglobalignore` と一致。

構成: **星型トポロジ**（各ノード → philip へ SSH トンネル 22001→22000、コンテナ間は SSH 50072 のみ疎通）。
`m2-sync.sh`（25 行）は **commit/push/add を一切行わず**、作業ブランチ上では
`git fetch -q origin phase0:phase0` のみ＝ワークツリー不干渉。

---

## 2. §5 実行結果

### 2.1 手順 0 — remote の SSH 化
`ssh -T git@github.com` で "Hi takuya3h!" を確認後に `set-url`。
**fetch/push とも SSH**、`.git/config` の `github_pat` 出現数 **0**。GitHub 上の revoke は未実施。

**keeper への影響なし（実証済）**: `~/.ssh/config` に `IdentityFile ~/.ssh/id_ed25519_github` +
`IdentitiesOnly yes` があるため、**ssh-agent 無しの最小環境でも `git fetch` が exit=0**。
30 分毎の自動同期は継続する。

### 2.2 手順 2 — `third_party_snapshot/lecun/`（合計 76KB）

| repo | commit | patch | 保全ファイル | 備考 |
|---|---|---:|---:|---|
| Relation-DETR | `b485955` | 176 行 | **23** | **shallow clone** |
| detrex | `e244e6c` | 20 行 | **5** | **shallow clone** |
| outputs | — | — | SKIP | 独自 `.git` 無し（親 m2 の .git を拾うだけ） |

保全した実装（lecun のディスク以外に存在しなかったもの）:
- モデル 6 実装 `relation_decoder_phaseca` / `relation_detr_b1_mtl` / `_c5neck` /
  `_phase_hc` / `_phasecrossattn` / `_phasefilm`、`models/temporal/`、`per_class_coco_map/`、config 15
- 改変 3 ファイル `optimizer/param_dict.py` / `util/engine.py` /
  `focus_detr/.../foreground_supervision.py`
- detrex 側 5 件（AlignDETR・FocusDETR の egosurgery config、`tools/train_net_egosurgery.py`）

> **両 fork とも shallow clone** であることが provenance で判明した。pinned hash から履歴を
> 辿れないため、**patch 単位の保全が唯一の復元手段**であることが裏づけられた。

同一 upstream commit `b485955` でも dirty 数がホスト毎に異なる: **efros 35 / lecun 25 / philip 8**。
Bengio は `.git` 自体が無くバージョン記録不能。ilya / Andrew はソース不在（ckpt のみ）。

### 2.3 手順 3 — 大容量ファイルの穴 — **100MB 超なし**
`git add` で実際に入りうる総量は **1,424KB**（experiments 58 + node_modules 7 + package*.json 2）。
efros 414MB / philip 599MB とは状況が異なる。

⚠️ ただし潜在的な脆さ: `node_modules`（**145M**）は **ignore されていない**。中の 143M バイナリ
`@azure/mcp-linux-x64/dist/azmcp` は **`.gitignore:62` の `dist/` ルールに偶然マッチ**して
除外されているだけ。`.gitignore` の変更は規約変更のため独断せず報告に留めた。

### 2.4 手順 4 — merge — **衝突ゼロ**
merge-base `1561ae2` から見て lecun 側 522 / phase0 側 637 の変更があったが、**重複 0 件**。
`merge-tree` でも衝突マーカー 0。behind 29 → **0**、マーカー残存 **0**、unmerged パス **0**。

lecun が efros/philip/Andrew と違って `README.md` / `docs/experiment_log.md` の衝突を回避できた
理由は、両ファイルが merge-base 以降どちらの側でも未変更だったため。
**他ホストの追記は PR #19/#17/#10 が未マージのため phase0 に未到達**。
→ それらがマージされた後に lecun が再 merge すると、今度は衝突が起きる。

### 2.5 手順 5 — runindex 到着と B-25

`runindex/` 到着を確認（index 615 run / experiments 181 / per_class 5,808 / verdicts 964 —
指示書の数値と完全一致）。`make runindex-dry` は exit=0、`DRY-RUN: 何も書き出していない` を確認。
**`make runindex`（書き出し）は未実行**（`runindex/` の未コミット差分 0 で実証）。

```
走査した run 数 : 721 / 警告なし 435 / 警告あり 286 / 収穫失敗 0
除外フラグ付き  : 19  → 解析対象 702
```

#### 🔴 B-25 が lecun でも発生（指示書の見込み「問題は起きない」は外れ）

`tools/harvest_runindex.py:50-54` の `EXCLUSION_RULES` は **4 マーカーのみ**:
`_smoke_prior` / `_smoke_ddq` / `_wrong_split_8_2_3` / `_failed_s3_weighted`。
`classify_exclusion()`（同 235-240 行）は **パス構成要素の完全一致**（`part == marker`）で判定する。

→ lecun の退避 8 ディレクトリはどれも該当せず、**退避 34 run のうち除外されたのは 0 件**。
**34 run 全部が `excluded=False` で解析対象 702 に混入**している。
（`_smoke_prior_simplehead` は部分一致では拾われない。）

実害の痕跡: `anomalies.md`「metric を確定できなかった run: 6」は全て
`_pre_redo_s0_smoke` / `_prior_no_eval_recipe`。

harvester は git ではなく**ディスクを走査**する（走査 721 = ディスク実数）ため、
「git で退避した＝解析から除外される」は成り立たない。**二層は独立している。**

### 2.6 手順 6 — SERVERNAME
- 対話シェル: `SERVERNAME=lecun`（`~/.zshrc:2` で export）/ `hostname=lecun`
- **非対話シェルでは全滅**: `bash -c` / `bash -lc` / `zsh -c` / `zsh -lc` すべて未設定
  （`.zshrc` は対話 zsh でしか読まれないため）
- lecun は `hostname == lecun` なのでフォールバックで正しい値になり実害ゼロ

恒久対策は `~/.zshenv` への移設。hostname が実サーバー名と異なるホストでは実害が出る
（sync-alerts.log にコンテナ ID `084f3b0911a2` で記録された行がその実例）。

### 2.7 手順 7 — 解析実装 — 報告対象なし
`experiments/analysis/` 以外の未追跡 `.py` は **124 件**だが、全件が mmdet 派生
（`mmdet_config.py` / `vis_data/config.py` 91 + モデル名 config 33）。

Andrew の `.gitignore` 例外 `!experiments/analysis/**/*.py` は **phase0 に未到達**。
lecun には `experiments/analysis/` 配下に未追跡の解析実装 **4 件**があり、
Andrew の PR が phase0 に入った後の再 merge で救済可能になる:
`dataset_eda/analyze.py`(20K) / `frozen_source_perclass_ap_cpu/compute_cpu.py`(24K) /
`frozen_source_signature3_R_index/compute_R.py`(8K) / `repro_variance_2026-07-29/reextract/_tf32_wrap.py`(4K)

---

## 3. T1b-FiLM arm 6 run の回収

### 3.1 経緯
Bengio 側で消失していた film arm 6 run の構造化結果が、**lecun の `/tmp` に原本のまま残存**していた。
ログからの復元は不要となり、**16 桁精度・per-class AP・lr/film_lr がすべて無損失**で回収できた。

配置先: `transfer/t1b_filmonly_seed{42,123,456}/`
（`injected_result.json` / `control_result.json` / `README.txt` = 9 ファイル / 60K、commit `0f6b565`）

`inj/ctrl` は `zero_ctx` フラグで表現されている（`t1b_film_*` = inj / `t1b_film_zeroctx_*` = ctrl）。

### 3.2 実測値（原本 16 桁）

| dir | seed | zero_ctx | best_epoch | mAP | per-class | ckpt |
|---|---:|---|---:|---|---:|---|
| `t1b_film_seed42` | 42 | false | 2 | 0.7368020015037875 | 15 | 有 |
| `t1b_film_seed123` | 123 | false | 5 | 0.731410166977743 | 15 | 有 |
| `t1b_film_seed456` | 456 | false | 1 | 0.7256822794945949 | 15 | 有 |
| `t1b_film_zeroctx_seed42` | 42 | true | 2 | 0.7336931058190956 | 15 | 有 |
| **`t1b_film_zeroctx_seed123`** | 123 | true | **-1** | 0.7291778095772903 | **0** | **無** |
| `t1b_film_zeroctx_seed456` | 456 | true | 1 | 0.7254479085888478 | 15 | 有 |

共通: `lr=0.0001` / `film_lr=0.0005` / `epochs=6` / `denominator="S0-frozen 0.7051±0.0052"`

### 3.3 原本無改変の担保（実測）
- 原本と追記メタを除いた比較で **6/6 一致**（`a==b` に加え `json.dumps(sort_keys=True)` の文字列一致も併用）
- `NaN` 出現 **5** / `null` 置換 **0** → **正規化していない**
- `init_mAP` は 6 ファイルで distinct **5 値**（seed42 のみ inj/ctrl 同値）→ **丸めていない**
- `zeroctx_seed123` の `per_class_coco_map = {}` は **空のまま**（`per_class_note` で「欠損ではなく結果」と明記）
- `/tmp` 原本 6/6 と ckpt 16/16 は **無傷**（削除・移動なし）

### 3.4 B-24 の裏づけ
`experiments/transfer/t1b_phasefilm_001_..._seed123/metrics.json` は
`init_mAP=control_mAP=mAP=0.7291778095772903 / epoch=-1`、per_class 空、`server.txt=lecun`。
これは `/tmp/t1b_seed123`（all/3ep）および `/tmp/t1b_zeroctx_seed123` の値と一致し、
film arm（`init=0.7291948117188538`）とは**別系統**であることが数値で確認できた。
→ 指示書の B-24 記述（phasefilm の実体は `trainable=all` / 3ep）は正しい。

---

## 4. `/tmp` 棚卸し（読み取り専用）

`/tmp` 直下 **594 dir**、`result.json` **37 件**（2026-06-20 19:17 〜 06-29 20:04）、
`best_t1b.pth` **16 本 = 3.0 GB**。

| 群 | /tmp 原本 | runindex 登録 |
|---|---:|---:|
| `hc_*`（ctrl3/inj3/measure3/smoke1） | 10 | **0** |
| `oracle_phase_*`（ctrl3/inj3/measure3） | 9 | **0** |
| `t1b_ca_*` | 6 | **0** |
| `t1b_film_*`（今回回収） | 6 | **0** |
| `t1b_seed*` / `t1b_zeroctx_*`（all/3ep） | 4 | 2（= `t1b_phasefilm`） |
| `t1b_work_*`（smoke・別データ init 0.8876） | 2 | 0 |

### 🔴 未登録の根因 — 直下 `transfer/` は runindex から構造的に不可視

リポジトリ直下 `transfer/` には既に **29 run / 56 個の result.json** が配置済み
（`hc_seed*` / `oracle_phase_seed*` / `t1b_ca_*_lecun` / `t1b_camt_*_efros` / `t1b_clsbias_*_efros` 等）。
しかし **`harvest_runindex.py` は `EXPERIMENTS = REPO_ROOT/"experiments"` のみを走査する**
（`tools/harvest_runindex.py:39-41`）。

→ 直下 `transfer/` の run は **runindex に永久に載らない**。`metrics.json` も 0 件で 6 点証跡ではない。
**回収はできているが解析に載っていない**状態。今回の film 6 run も同じ扱いになる。
解析対象にするには `experiments/transfer/` へ 6 点証跡を伴って昇格させる必要がある（別タスク）。

---

## 5. 🔴 B-20 の解釈訂正 — 評価は非決定的ではない

当初 finding ③（同一 seed で `init_mAP` が inj/ctrl 一致しない）は
「**評価そのものが非決定的**な証拠」と解されていたが、`/tmp` 全 37 件の実測はこれを支持しない。

### 実測
`init_mAP` は seed ごとに **ちょうど 2 値**しか現れず、**群内では独立実行の run どうしが
16 桁でビット一致**し、2 群は **mtime で完全分離**する。

| seed | 値 | n | mtime 範囲 |
|---:|---|---:|---|
| 123 | `0.7291778095772903` | 3 | 06-21 22:15 〜 06-22 **05:55** |
| 123 | `0.7291948117188538` | 10 | 06-22 **06:42** 〜 06-29 16:10 |
| 456 | `0.7216586914703580` | 3 | 06-21 22:09 〜 06-22 **05:57** |
| 456 | `0.7216619814840780` | 10 | 06-22 **06:41** 〜 06-29 20:04 |
| 42 | `0.7303082181713886` | 8 | 06-22 17:18 以降のみ |

※ seed42 の `0.8876398918087298` は work/smoke 系（別データ）で本走とは無関係。

### 結論
評価が非決定的なら 13 通りの異なる値が出るはず。実際は **2 値・群内完全一致・mtime で完全分離**。
→ **評価は決定的であり、2026-06-22 の 05:57〜06:41 に評価系へ変更が入った**と読むのが実測に整合する。

この解釈は **seed42 だけが一致した理由も説明する**。seed42 の inj/ctrl は**両方とも境界より後**
（06-22 17:18 / 17:19）に実行されている。一方 seed123/456 は **ctrl が境界より前、inj が後**。

### 帰結（重要）
🔴 **seed123/456 の inj−ctrl 差は時期の交絡を含む。交絡がないのは seed42 のみ。**
Δ_inj−Δ_ctrl を 3 seed で平均する際は、この非対称を必ず明記すること。

変更の中身は未特定。warm-start ckpt（`third_party/Relation-DETR/checkpoints/incoming/seed*/best_ap.pth`）は
3 seed とも mtime 2026-05-30 で境界前後を通じて不変であり、**ckpt 差し替えが原因ではない**。

> この訂正は `transfer/t1b_filmonly_seed42/README.txt` の「注意 3 点」に
> 「■ 2026-08-02 追記」として記録済み。元の 3 seed のデータはそのまま残し、結論部のみ更新した。

---

## 6. 指示書に無い発見（要判断）

### 6.1 ⚠️ PR #1（→ master）が push で膨張
`exp/lecun-wip-20260703` を head とする PR が **#17（→ phase0）と #1（→ master）の 2 本**存在する。
本ブランチへの push は **両方に波及**し、PR #1 は現在 **6,369 ファイル / +1,877,189 行**。
誤マージされると master に全量が流入する。古い残骸の疑いがあり、**close の判断を推奨**。

### 6.2 ⚠️ 指示書の対象に含まれないノードが 4 つ稼働（`aolab` は実データ保有）
`~/claude-sync/`（Syncthing 共有）の `sync-alerts.log` に全ノードのアラートが集約されており、
指示書記載の 5 サーバー以外に **`he` / `adam` / `aolab` / `Hinton`** が keeper を稼働させている。
うち **`aolab` は追跡済み run の `server.txt` に 10 件**あり、**実データ生成ノード**。

追跡済み run の生成サーバー分布: lecun 464 / efros 167 / philip 28 / **aolab 10**。

### 6.3 ⚠️ 4 ノードが fetch 失敗中（PAT 期限切れの疑い）
2026-08-02 05:38〜05:48 に **`Andrew` / `aolab` / `Hinton` / `Bengio`** が
`fetch失敗(PAT期限切れ?)` を記録。**最難関の Andrew（behind 106）が origin と通信できていない**
可能性が高く、巡回順序・実行可否に直結する。lecun は SSH 化により解消済み。

### 6.4 欠落 fork に依存する本番 baseline 12 run（調査段階の発見・philip で保全済）
追跡済み・非隔離の S0 baseline 12 run が、lecun に存在しない 4 fork を参照していた。
12 run はすべて `server.txt = philip` / `git_commit = 4327348e`。

| 欠落 fork | 依存 run | mAP |
|---|---|---|
| `Mr.DETR` | s0_031–036（6 run） | 0.7155–0.7304 |
| `DI-MaskDINO` | s0_022–024（3 run） | 0.3337–0.4285 |
| `Stable-DINO` | s0_020–021（2 run） | 0.7200–0.7254 |
| `Co-DETR` | s0_013_sensex_codino（1 run） | val/mAP 記録あり |

→ philip の `third_party_snapshot` を最優先にする根拠となり、既に保全完了（PR #10）。

---

## 7. 独自に決めたこと

1. **tar に `--exclude='__pycache__' --exclude='*.pyc'` を追加**
   `git status --porcelain` は `models/temporal/` を**ディレクトリ 1 エントリ**で返すため、
   スクリプトの `grep -v __pycache__` フィルタが内部の `.pyc` に効かない。
   スクリプトの意図に実装を一致させる補正。
2. **`.gitignore` を変更しなかった**（node_modules の件）。100MB 超ではなく、規約変更に当たるため。
3. **harvester を修正しなかった**（B-25）。解析系の仕様変更のため。
4. **PR #1 に触れなかった**。close の判断は人間に委ねる。
5. **README「注意 3」の結論を実測に基づき更新**（§5 参照）。
   実測と矛盾する断定は書けないと判断。データはそのまま残し結論部のみ更新した。
6. **film の配置先を指示通りリポジトリ直下 `transfer/` にした**。
   既存 26 run が同一構成で並ぶ確立された回収置き場だと確認できたため。
   ただし runindex 不可視である旨を README に明記した。
7. **出力スタイルを原本に合わせた**（`indent=2` / `ensure_ascii=False`）。
   追記なしならバイト単位一致することを事前検証済み。

---

## 8. 完了状態（機械検証済み）

| 項目 | 実測 |
|---|---|
| remote が fetch/push とも SSH | ✅ 2/2、`.git/config` の PAT 出現数 0 |
| `third_party_snapshot/lecun/` push | ✅ 11 ファイル、`third_party/` 本体の追跡 0 件 |
| behind / 衝突マーカー / 未 push | ✅ 0 / 0 / 0 |
| `runindex/` 到着 | ✅ 615 run |
| ディスク / 追跡済み / 退避 | 721 / 687 / 34 |
| `make runindex` 未実行 | ✅ `runindex/` 差分 0 |
| film 6 run + README 配置 | ✅ 9 ファイル、原本と 6/6 一致 |
| `/tmp` 原本 | ✅ 6/6 無傷、ckpt 16/16 無傷 |
| `.gitignore` 無変更 | ✅ 自分のコミットで未接触 |
| PR #17 | ✅ 更新・**未マージ**（base=phase0 / MERGEABLE / 531 files） |

---

## 9. 次のサーバーへの申し送り

1. **PR #1（→ master）への波及に注意**。`exp/*` ブランチへの push が master 向け PR も更新する。
2. **README/experiment_log の衝突は「まだ」起きないだけ**。PR #19/#17/#10 がマージされ
   他ホストの追記が phase0 に入った後、再 merge すると衝突する。
3. **B-25 は lecun でも発生**。退避 dir を増やすたびに `EXCLUSION_RULES` への追加が必要。
   恒久対策は「規約プレフィックスでの前方一致」への変更だが、承認が要る。
4. **Andrew の `.gitignore` 例外は phase0 に未到達**。各ホストの `experiments/analysis/` 配下に
   未追跡の解析実装が無いか、merge 後に再確認すること。
5. **SSH 化は keeper を壊さない**（lecun で実証済）。`~/.ssh/config` に `IdentityFile` +
   `IdentitiesOnly yes` があるか確認すれば安全に移行できる。
6. **`SERVERNAME` は `~/.zshrc` ではなく `~/.zshenv`** に置くべき。非対話シェルに継承されない。
7. **直下 `transfer/` に置いた回収原本は runindex に載らない**。
   解析に載せるには `experiments/transfer/` への 6 点証跡付き昇格が別途必要。

---

## 10. 未対応・要判断リスト

| # | 項目 | 判断者 |
|---|---|---|
| 1 | B-25: `EXCLUSION_RULES` を前方一致へ変更するか | 人間 |
| 2 | 直下 `transfer/` 29 run を `experiments/transfer/` へ昇格させるか | 人間 |
| 3 | PR #1（→ master）を close するか | 人間 |
| 4 | `node_modules` を `.gitignore` に追加するか | 人間 |
| 5 | 対象外ノード（`he` / `adam` / `aolab` / `Hinton`）を巡回対象に加えるか | 人間 |
| 6 | PAT 失効 4 ノードの復旧（SSH 化の横展開） | 人間 |
| 7 | `third_party` の正式な管理方法（submodule / `src/` 移設 / 別リポ） | 全サーバー報告後 |
| 8 | `_orphan_no_metrics/` 6 run の複製判定（sha256 は報告済み） | 人間 |

---

## 11. 追記（2026-08-02 19:37）— phase0 の取り込み完了と Syncthing 競合

統合後の phase0 を lecun に取り込んだ（**fast-forward**、behind 64 → 0、HEAD = `213b52b`）。
マージコミットは発生していない。

### 11.1 未追跡ファイル 54 件の衝突

phase0 が新規追加するファイルのうち **54 件が lecun のローカル未追跡ファイルと同名**で、
`error: The following untracked working tree files would be overwritten by merge` により merge が拒否された。

- 対象: `experiments/hand2det_dev/*/logs/` 42 件 + `experiments/transfer/_p0_identity_*/logs/` 12 件
- **blob hash は全 54 件が一致（相違 0）** → 削除しても merge が同一バイトを復元するため情報損失なし
- 経緯: §1.3 で「未追跡だが Syncthing 層で保護されている」と報告した run 群が、
  他ホスト経由で phase0 に取り込まれた結果、「ローカルでは未追跡 / phase0 では追跡済み」となった
- → §6 で保留としていた「`_p0_identity_*` と `hand2det_dev` の帰属」は、**git に載って永続化された**ことで解消

### 11.2 🔴 Syncthing が削除を巻き戻す（他ホストでも再現する見込み）

`rm` で 54 件を削除した直後、**Syncthing が約 40 秒後にすべて復元した**（mtime 19:35:54 を実測）。
`.stignore:44` の `!experiments/**/logs` により当該パスは同期対象であり、
他ノードが原本を保持しているため削除が巻き戻る。

この結果、「削除 → （別要因で merge 中断）→ 再 merge」という手順を踏むと、
中断中に復元され **2 回目の merge も同じ衝突で失敗する**。

**対処**: Syncthing を停止する必要はない。
`git restore` → `rm` → `git merge` を **単一コマンド内で連続実行**すれば、
復元（約 40 秒）に対しミリ秒単位で先行できる。lecun では rm 完了から merge 完了まで **264ms** で通過した。

### 11.3 併発した第二の要因 — `auto_notion_sync.log`

`.claude/hooks/auto_notion_sync.log` は Notion 同期フックが動作するたびに追記されるため、
`git restore` しても時間が経つと再び変更され、`Your local changes would be overwritten by merge` で
merge が中断する。phase0 で `.gitignore` に入るため、**merge さえ通れば以後は再発しない**。
上記の単一コマンド化はこの競合も同時に回避する。

### 11.4 取り込み後の実測

| 項目 | 値 |
|---|---|
| behind | **0** |
| `runindex/index.csv` | **721 行（720 run）** |
| `runindex/experiments.csv` | 195 |
| `runindex/per_class.csv` | 5,896 |
| `runindex/verdicts.csv` | 1,028 |
| backlog B-24〜B-29 | **6 件** |
| `runindex/` 未コミット差分 | **0**（`make runindex` 未実行） |
| `third_party_snapshot/` | **5 ホスト**（Andrew / Bengio / efros / lecun / philip） |
| ディスク / 追跡済み / 退避 | **754 / 720 / 34** |

54 件の復元検証: **未復元 0 件 / 内容不一致 0 件 / 54 件すべて追跡対象化**。
`§2.3` 時点の 3 数値（721 / 687 / 34）から、統合により +33 run が届いた。
