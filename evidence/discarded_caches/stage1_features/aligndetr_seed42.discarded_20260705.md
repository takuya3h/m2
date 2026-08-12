# 破棄理由

破棄日: 2026-07-05（ディレクトリ mtime 09:13）
記録日: 2026-08-02（破棄から 4 週間後に `/tmp` の実行痕跡から再構成）

## 何が起きたか

2026-07-03 15:55 に AlignDETR-S0-frozen seed42 の学習を 2 GPU で開始したが、
16:25 に **NCCL ALLREDUCE タイムアウト**（`SeqNum=1` / 1800745ms → SIGABRT）で失敗した。
`SeqNum=1` は最初の collective でハングしたことを示し、学習は 1 step も進んでいない。

17:08 の `entry5.sh` は S0-frozen ckpt が無いため、**2026-05-31 の通常学習 AlignDETR ckpt**
(`/tmp/aligndetr_work_seed42/model_final.pth`) で代替して特徴抽出を実行した
（17:10-17:20、正常完了）。その特徴を使って 17:20-17:21 に TeCNO 3 seed 学習が走った。

抽出スクリプト `scripts/extract_stage1_features_aligndetr.py` が docstring / argparse で
要求する **config / ckpt / 出力先の 3 項目すべてに違反**していた。

| 項目 | スクリプトが要求 | `entry5.sh` が渡した値 |
|---|---|---|
| config | `..._egosurgery_s0_frozen.py` | `..._egosurgery.py`（通常版） |
| checkpoint | `/tmp/aligndetr_s0frozen_seed42_XXXX/model_final.pth` | `/tmp/aligndetr_work_seed42/model_final.pth`（2026-05-31） |
| 出力先 | `stage1_features/aligndetr_s0frozen_seed42/` | `stage1_features/aligndetr_seed42/` |

## 是正

07-05 本キャッシュを破棄 → 07-06 03:24 S0-frozen を 2 GPU DDP で再学習（v2、bbox AP 68.596）
→ 07-10 17:39-17:47 `stage1_features/aligndetr_s0frozen_seed42` を作り直し。

## 依拠した run の扱い

`experiments/phase1/s4_phase_baseline_{010,011,012}_frozen_tecno_phase_baseline_aligndetr_seed{42,123,456}`
は **無効**（2026-08-02 判定）。宣言している S0-frozen 条件で走っていないため。
各 run の `INVALID.md` を参照。数値記録そのものは健全であり、無効なのは実験条件である。

## キャッシュ自体は正常

抽出は完走しており frame 数・次元・サイズは正常。

```
val   1515 x 2048   (12,465,940 bytes)
test  4265 x 2048   (35,092,940 bytes)
train 9657 x 2048   (79,458,316 bytes)
C5 shape=(1, 2048, 34, 60)   GAP dim=2048
```

`relation_detr_seed42` と **1 バイト単位で一致**。
破棄理由は「抽出が壊れていた」ではなく「**入力 ckpt が意図と異なる**」である。
本ディレクトリの `*_extract.log` が正常完走の一次証拠。

## 判別できなかったこと

07-05 09:13 のリネームを**誰がどの判断で行ったかを示す記録は存在しない**。
上の時系列の各事象は実測だが、「NCCL 失敗を認識して是正した」という因果は
残存ファイルの時刻と内容からの**推定**である。

## 一次証拠

`evidence/aligndetr_s0frozen_incident_20260703/`
（`/tmp` にのみ存在した実行痕跡を 2026-08-02 に保全。`README.md` に全時系列）

---

## このファイルの git 追跡について

`.gitignore:15` の `data/processed/**` により本ファイルは **git で追跡されていない**。
同内容の追跡コピーが `evidence/discarded_caches/` にある（対応表は同ディレクトリの `README.md`）。
**両者が食い違った場合は `evidence/` 側を正とする。**
