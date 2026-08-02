# third_party スナップショット（Bengio）

## 🔴 バージョンが記録不能

`third_party/Relation-DETR/` に `.git` が存在しない。したがって
origin URL / commit hash / dirty 状態のいずれも記録できない。

**注意**: `git -C third_party/Relation-DETR log` は親リポジトリ（m2）まで遡って
親の hash（5ff0120 / dirty 4）を返す。**これは偽の値であり採用してはならない。**
`[ -d "$d/.git" ]` を先に確認すること。

## 保全した内容と、その方法の限界

`.git` が無いため `git diff`（upstream 改変）と `git status --porcelain`（新規追加）を
分離できない。代わりに **pristine 展開バッチより新しいファイルを mtime で列挙**した。

### 閾値の実測根拠（指示書の値から補正）

mtime 分布を実測したところ、以下のように明確に分離していた:

| 時刻 | 件数 | 内容 |
|---|---|---|
| `2026-05-28 08:05:39.47`（サブ秒の単一バッチ） | 118 | pristine 展開 |
| （約 2 日の谷） | — | — |
| `2026-05-30 04:21:37` 〜 `2026-06-22 12:38` | 22 | ローカル編集・新規追加 |

指示書が指定した閾値 `2026-05-28 08:05` は **08:05:00 より新しい**の意味になり、
同一分内（08:05:39）の pristine 118 件を巻き込んで **140 件**になった。
そのため **`2026-05-28 08:05:40`** に補正し、22 件を得た。
この 22 件は §3 調査時の独立な計測（閾値 `2026-05-29`）と完全に一致する。

### tar に混在するもの

`project_files.tar.gz` には以下が混在する:
- 本研究の独自実装（新規追加）
- upstream ファイルへの改変（他ホストでは patch として分離できていたもの）

**他ホストの `upstream_mods.patch` と突き合わせれば分離できる。**
とくに `optimizer/param_dict.py` と `util/engine.py` は efros / lecun / philip の
3 台すべてで改変が確認されており、Bengio でも同じ 2 ファイルが列挙されている。

## 主要な独自実装（失われると T1b 系・B1 系が再現不能）

`models/bricks/relation_decoder_phaseca.py` /
`models/detectors/relation_detr_{b1_mtl,c5neck,phasecrossattn,phasefilm}.py` /
`models/temporal/tecno_mirror.py` /
`configs/relation_detr/*_egosurgery_{b1_mtl,lockeddown,s0_frozen,s0_frozen_neck,t1b,t1b_ca}.py` /
`configs/train_config_egosurgery*.py`

## ホスト間の状況（2026-08-02 実測）

| host | third_party | .git | 実装数 |
|---|---|---|---|
| philip | 9 fork | あり | 42 file |
| efros | Relation-DETR | あり | dirty 35 |
| lecun | Relation-DETR + detrex | あり | 28 |
| **Bengio** | Relation-DETR | **なし** | 22（mtime 推定） |
| ilya / Andrew | ソース不在（ckpt のみ） | — | 0 |

## 収録ファイル

- `Relation-DETR/project_files.tar.gz` — 22 実装ファイル
- `Relation-DETR/file_list.txt` — 列挙結果
- `Relation-DETR/tar_contents.txt` — tar 実内容（照合用）
- `Relation-DETR/provenance.txt` — 記録不能である事実と閾値の根拠
- `outputs-provenance.txt` — `third_party/outputs/`（28K・Hydra 遺留物）の記録

  ⚠️ 指示書は `outputs/provenance.txt` を指定していたが、`.gitignore:118` の `outputs/`
  （先頭 `/` なし＝どの階層の `outputs` ディレクトリにもマッチ）に弾かれて追跡できなかった。
  `git add -f` で強行すると「無視ディレクトリ内の追跡ファイル」となり、今回 `logs/` で
  事故を起こしたのと同じ二重管理を新規に作ってしまうため、**ディレクトリを作らず
  ファイル名を `outputs-provenance.txt` に改めた。**

## 注意

これは**保全用スナップショットであり、正式な管理方法ではない**。
