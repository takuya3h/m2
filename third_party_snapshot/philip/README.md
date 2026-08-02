# third_party スナップショット（philip）

`third_party/` は git と Syncthing の両方から除外されており、どちらにも乗っていない。

- git: `.gitignore:112` の `third_party/` で明示除外
- Syncthing: `.stignore` はホワイトリスト方式で、末尾の `**` が許可されていないものを
  全除外する。`third_party` は `!` 許可リストに無いため除外される
  （同ファイル 35 行目に「外部fork（入れ子.gitを含むため同期不可。各サーバーでclone）」と明記）

各サーバーが独立に clone しているため、同じ upstream commit でも載っている実装が食い違う。

## なぜ philip が最重要か

runindex の実測で、検出側 51 run のうち 28（55%）が philip 由来。
S0 検出ベースラインは 20 種の検出器を比較しており、そのうち
Mr.DETR / Stable-DINO / DI-MaskDINO / Co-DETR の 4 fork は
**philip にのみ実在する**（lecun には存在しない）。

これらに依存する 12 run は runindex 上で `excluded=false` であり、解析対象に入っている。

| run | 依存 fork | mAP |
|---|---|---|
| `s0_031-033_mrdetrdino` | Mr.DETR | 0.7154–0.7304 |
| `s0_034-036_mrdetralign` | Mr.DETR | 0.7189–0.7200 |
| `s0_020-021_stabledino` | Stable-DINO | 0.7200–0.7254 |
| `s0_022-024_dimaskdino` | DI-MaskDINO | 0.3337–0.4285 |
| `s0_013_sensex_codino` | Co-DETR | 0.7180 |

同じ upstream commit `b485955` の Relation-DETR でも、ホスト間で載っている実装が異なる
（efros: dirty 35 / lecun: 25 / philip: 8）。ホスト別に保全する設計はこのため。

## 収録内容

リポジトリごとに:

- `provenance.txt` — origin URL / commit / branch / shallow か / 取得日時 / 取得ホスト
- `upstream_mods.patch` — 追跡ファイルへの改変（`git diff` 出力）
- `project_files.tar.gz` + `file_list.txt` + `tar_contents.txt` — 未追跡の実装・config

ビルド生成物（`__pycache__` / `*.pyc` / `*.so` / `build/` / `*.egg-info` /
`*.pth` / `*.ckpt` / `outputs/`）は除外している。

### 収録した 9 リポジトリ

| repo | upstream commit | patch 行数 | 未追跡ファイル |
|---|---|---|---|
| Co-DETR | `2665352` | 0 | 1 |
| DAC-DETR | `a186a20` | 135 | 3 |
| DI-MaskDINO | `6a321a5` | 13 | 5 |
| MaskDINO | `3831d85` | 0 | 0 |
| Mr.DETR | `287c693` | 0 | 3 |
| Relation-DETR | `b485955` | 41 | 7 |
| Stable-DINO | `e3a5400` | 0 | 1 |
| detrex | `e244e6c` | 20 | 5 |
| mmdetection | `cfd5d3a` | 0 | 0 |

upstream 改変が確認されているのは DAC-DETR / DI-MaskDINO / Relation-DETR / detrex の 4 本、
計 7 ファイル:

- DAC-DETR: `engine.py` / `main.py` / `models/backbone.py` / `models/deformable_detr.py`
  （+ `models/ops/MultiScaleDeformableAttention.egg-info/SOURCES.txt` はビルド副産物）
- DI-MaskDINO: `train_net.py`
- Relation-DETR: `util/engine.py`
- detrex: `projects/focus_detr/modeling/foreground_supervision.py`

### DAC-DETR の `data/` について

`data/` はデータセットへの symlink アダプタであり、実データは含まない。
tar は symlink をリンクのまま保存しているため、リンク先のパス構造が保全されている
（実ファイルは smoke 用の annotation JSON 2 件のみ）。

## 注意

これは**保全用スナップショットであり、正式な管理方法ではない**。
サブモジュール化 / `src/` への移設 / 別リポジトリ化のいずれにするかは、
全サーバーの報告が揃ってから決定する。
このスナップショットから直接ビルド・実行することを想定していない。
