# この run は無効です（2026-08-02 判定）

`config.yaml` は `frozen_source: align_detr` の **S0-frozen** を宣言しているが、
実体は **2026-05-31 の通常学習 AlignDETR ckpt**
(`/tmp/aligndetr_work_seed42/model_final.pth`) で抽出された特徴を使用している。

2026-07-03 15:55 に開始した S0-frozen 学習が 16:25 に NCCL ALLREDUCE タイムアウト
(`SeqNum=1` / 1800745ms → SIGABRT) で失敗したため、17:08 の `entry5.sh` が
代替 ckpt で走らせた結果である。

依拠した特徴キャッシュ `data/processed/stage1_features/aligndetr_seed42` は
2026-07-05 に破棄され（`.discarded_20260705`）、07-06 03:24 に S0-frozen が
2 GPU DDP で再学習（bbox AP 68.596）、07-10 17:39-17:47 に
`stage1_features/aligndetr_s0frozen_seed42` が作り直されている。

**Δ 分析に使用してはならない。**
runindex では `excluded=true` / `exclusion_reason='wrong_frozen_source'` とすべき。

## 数値記録自体は健全

本 run の `metrics.json` 実測値（2026-08-02 に philip で確認）:

```
epoch    = 36
phase_accuracy = 0.8422442244224423
phase_macro_f1 = 0.5828472115684166
```

ilya が checkpoint と `metrics.json` の全桁一致を 3 seed とも確認済み（2026-08-02）。
`per_class_ap.json` も checkpoint の `phase_per_class_f1` と完全一致（ilya 報告）。
`entry5_tecno_seed123.log` の学習記録とも整合する
（`evidence/aligndetr_s0frozen_incident_20260703/` に保全）。

**無効なのは実験条件であって、記録ではない。**

## 凍結源の記述矛盾（backlog B-25）

同一 run の 7 点証跡の内部で凍結源の記述が **3 対 2 に割れている**
（2026-08-02 に philip で実測）。

| 証跡 | 記述 |
|---|---|
| ディレクトリ名 | `aligndetr` |
| `command.sh` | `aligndetr`（`train_s4_tecno_aligndetr.py`） |
| `config.yaml` | `detector: align_detr` |
| `notes.md` 見出し | `# S4 phase baseline (frozen **Relation-DETR** + causal TeCNO)` |
| `metrics.json` | `eval_recipe.test_cfg.backbone = **relation_detr**_resnet50_frozen_seed42` |

時系列証拠（`entry5.sh` が AlignDETR ckpt を渡している）は **aligndetr を支持する**。
`notes.md` と `metrics.json` の `relation_detr` は、既存の
`s4_phase_baseline_001-003`（Relation-DETR 凍結源）のテンプレートを
流用した際の書き換え漏れと見られるが、**これは推定であり確証はない**。

## 変更していないもの

`metrics.json` / `config.yaml` / `notes.md` は**一切書き換えていない**。
実験時の記録として保存する。

## 詳細

- `evidence/aligndetr_s0frozen_incident_20260703/README.md` — 全時系列と一次証拠
- `evidence/discarded_caches/stage1_features/aligndetr_seed42.discarded_20260705.md` — 破棄理由
