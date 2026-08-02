# third_party スナップショット（lecun）

`third_party/` は `.gitignore:136` と `.stignore:35` の両方で除外されており、
git にも Syncthing にも乗っていない。各サーバーが独立に clone しているため、
同じ upstream commit でも載っている実装が食い違う。

## lecun に何があるか
- Relation-DETR（b485955）: 改変 2（optimizer/param_dict.py, util/engine.py）
  + 未追跡 23 = モデル 6 実装（relation_decoder_phaseca / relation_detr_b1_mtl /
  _c5neck / _phase_hc / _phasecrossattn / _phasefilm）、models/temporal/、
  per_class_coco_map/、config 15
- detrex（e244e6c）: 改変 1（focus_detr/.../foreground_supervision.py）
  + 未追跡 5（AlignDETR/FocusDETR の egosurgery config、tools/train_net_egosurgery.py）

## ホスト間の食い違い（2026-08-02 時点の実測）
同じ upstream commit b485955 の Relation-DETR で dirty 数が異なる:
efros 35 / lecun 25 / philip 8。
Bengio は .git 自体が無くバージョン記録不能。ilya / Andrew はソース不在（ckpt のみ）。

## 注意
これは**保全用スナップショットであり、正式な管理方法ではない**。
サブモジュール化 / src/ への移設 / 別リポジトリ化のいずれにするかは、
全サーバーの報告が揃ってから決定する。
