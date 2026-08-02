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
