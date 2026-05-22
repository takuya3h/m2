---
name: add-model-component
description: egosurgery_multitask の models/ に新しいモデル部品（backbone・検出ヘッド・temporal・feedback 等）を追加し、build.py・config・テストへ正しく配線する手順。
---

# モデル部品の追加手順

`src/egosurgery/models/` 配下に新コンポーネントを追加し、ファクトリ・設定・
テストへ一貫して組み込む手順。

## 1. 配置先を決める

仮説 H1〜H4 に対応するサブモジュールに置く:
`backbones/` `heads/` `temporal/` `object_token/` `feedback/` `relation/` `exo/`
`losses/`。新規ファイルは該当ディレクトリへ。

## 2. 実装の規約

- `nn.Module` 派生。`__init__` は config（DictConfig か dict）を受け、`.get()` で
  デフォルト付き読み出し（テストが素の dict を渡せるように）。
- 外部依存（detectron2 / mmdet 等）が要る部品は、**import 失敗時に警告して無効化**
  する防御的設計にする（`is_*_available()` パターン）。テスト環境で import が
  通ることを最優先。
- docstring に使い方の最小例を書く。コメント密度は周辺コードに合わせる。

## 3. ファクトリへ配線（build.py）

- `src/egosurgery/models/build.py` の対応するビルダ
  （`build_backbone` / `build_detection_head` / ...）に分岐を追加。
- config 文字列参照（例 `model.backbone=name`）は `_resolve_component_cfg` が
  `configs/model/{group}/{name}.yaml` を読む。新部品の YAML をそのディレクトリに作る。

## 4. config を作る

`configs/model/{group}/{name}.yaml` を作成。既存 YAML（例
`dinov2_vitl14_reg.yaml`）の粒度に合わせる。

## 5. テストを追加

- `tests/test_models.py`（または該当 test ファイル）に、ダミー入力での forward と
  出力 shape の検証を追加。
- 外部依存が要るものは、`pytest.mark.skipif` でなく**防御的設計で import 自体は
  通す**こと。ネットワーク必須（torch.hub 等）は取得失敗時 `pytest.skip`。
- `PYTHONPATH=src .venv/bin/python -m pytest tests/ -q` で全テスト緑を確認。

## 6. 仕上げ

- CodeGraph で `build_model` への影響範囲を確認。
- `README.md` に追加内容と現状を追記（CLAUDE.md の必須要件）。
- semgrep の誤検知に注意（クラス名に `eval` を含む部分文字列、`DataLoader` への
  pin_memory 指摘）。前者は import エイリアス、後者は `# nosemgrep` で回避する。
