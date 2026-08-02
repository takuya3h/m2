# third_party スナップショット（Andrew）

## 結論: 保全対象のソースコードは存在しない

captured_at: 2026-08-02T10:21:34+00:00
captured_on: Andrew

## 実測
- Relation-DETR
  - .git: **なし**
  - size: 2.1G
  - files: 12
  - .py: 0
- outputs
  - .git: **なし**
  - size: 28K
  - files: 4
  - .py: 0

## 注意
指示書の `git -C third_party/<d> log` は .git が無い場合
親リポジトリ（m2）まで遡って親の hash を返す。commit hash を
そのまま転記すると誤記録になる。**記録不能**が正しい。

compute_R.py の docstring が「relationdetr/aligndetr の checkpoint は
本ホスト(andrew)に存在しない（Server=philip の資産）」と記録しており、
Andrew での検出側実験は既存 per_class_ap.json からの再計算に限られる。
third_party 不在は Andrew では既知の制約として扱われていた。

## 付記: 未追跡 run 30 件は Syncthing 層で保全されている（git 未回収は「価値なし」の意味ではない）

`experiments/hand2det_dev/_identity_*` 18 / `hand2det_1ep_*`・`hand2det_4ch_film_inj_*` 3 /
`experiments/transfer/_p0_identity_*` 6 / `experiments/transfer/_smoke_*` 3 = 計 30 ディレクトリ・約 896MB は
git に回収していない。理由は 6 点証跡（metrics.json / config.yaml / command.sh / git_commit.txt /
per_class_ap.json / notes.md）を一切持たず、実体の大半が `predictions/*.json.gz` であるため、
二層設計上 **Syncthing 層（`predictions` / `logs` / `checkpoints`）で既に保護されている**から。
git に載せるべき軽量証跡が存在しない、という理由であって、内容に価値が無いからではない。

内容は `val_metrics_by_epoch.json` を実読して確認済み: `epochs: 0` / `best_epoch: -1` /
`best_is_init: true`、val mAP は identity 系 18 件すべて `0.7302938994613697` で完全一致する。
すなわち**恒等写像として注入した追加チャネル（4ch/5ch, ctrl/inj）が baseline の推論を
bit 一致で再現することの証拠**であり、G-2 系 ROI チャネル注入の健全性検査として再現性上の価値がある。
非 `_` prefix の 3 件のみ 1 epoch 学習済み（`hand2det_1ep_4ch_film_seed42` は `best_is_init: false`,
`hand2det_4ch_film_inj_seed42` は val mAP 0.88764）。
将来これらを正式 run に昇格させる場合は ExperimentManager 経由で再実行し、6 点証跡を伴わせること。
