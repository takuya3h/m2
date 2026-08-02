# 破棄された特徴キャッシュの理由記録（git 追跡用コピー）

## なぜここにあるか

`.gitignore:15` の `data/processed/**` が `DISCARDED.md` にもマッチするため、
破棄済みキャッシュのディレクトリ内に置いた `DISCARDED.md` は **git で追跡できない**
（例外は `!data/processed/**/`（ディレクトリのみ）と `!data/processed/**/.gitkeep` の 2 つだけ）。

そこで **原本は破棄済みキャッシュのディレクトリ内に置き（ディスク上で発見できるように）、
同内容の追跡コピーを本ディレクトリに置く**という二重配置を採っている。
`.gitignore` は変更していない。

## 対応表

| 追跡コピー（本ディレクトリ） | 原本（未追跡・ディスク上） |
|---|---|
| `stage1_features/aligndetr_seed42.discarded_20260705.md` | `data/processed/stage1_features/aligndetr_seed42.discarded_20260705/DISCARDED.md` |
| `t1a_regiontoken/aligndetr_s0frozen_seed42.discarded_20260706.md` | `data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42.discarded_20260706/DISCARDED.md` |
| `b2a_detsignal/aligndetr_s0frozen_seed42.discarded_20260706.md` | `data/processed/b2a_detsignal/aligndetr_s0frozen_seed42.discarded_20260706/DISCARDED.md` |

原本は Syncthing で他サーバーへ配られる（`data/processed` は `.stignore` の許可リストに入っている）。
追跡コピーは git 経由で配られる。**内容が食い違ったら追跡コピー側を正とする。**

## 理由が判明している / していない

| キャッシュ | 破棄理由 |
|---|---|
| `stage1_features/aligndetr_seed42` (07-05) | **判明**。2026-07-03 の S0-frozen 学習が NCCL 障害で失敗し、通常学習 ckpt で代替されたため |
| `t1a_regiontoken/aligndetr_s0frozen_seed42` (07-06) | **判別不能**。後継との内容差（md5）は実測済み |
| `b2a_detsignal/aligndetr_s0frozen_seed42` (07-06) | **判別不能**。後継そのものが存在しない |

## 恒久対策の候補（未実施・要判断）

`.gitignore` に以下を追加すれば原本を直接追跡でき、二重配置が不要になる。

```
!data/processed/**/DISCARDED.md
```

`data/annotations/_deprecated/egosurgery_hand4/DEPRECATED.md` も同様に未追跡であり、
そちらにも同じ問題がある。backlog に起票済み。

## 関連

`evidence/aligndetr_s0frozen_incident_20260703/` — 07-03 インシデントの実行痕跡と全時系列
