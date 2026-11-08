# dtower-rerun 中間の記録（12 番 seed 42 の 5 本）

契約 T-2026-11-07-dtower-rerun の Task C-4。12 番（lr 3.07e-4、max_norm 0.059、S 4.976e-3）の seed 42 で、
折り A〜E の 5 本が 2026-11-08T10:25:52Z（19:25:52 JST）に揃った。残り 15 本（12 番 seed 123、0 番の両 seed）は学習中である。

**選定はしない**（prereg §3）。下の値は記録であり、凍結する塔は契約が始めから 12 番 seed 42 と決めている。
最終の表・記録・判定の材料は Task D の `REPORT.md` と `tasks/T-2026-11-07-dtower-rerun/RESULT.md` に書く。

## 凍結する塔（12 番 seed 42）

checkpoint は各折りの val mAP で選んだ `best_ap.pth`。同期の外（`/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-07-dtower-rerun/runs/<run>/best_ap.pth`）にあり、
大きさはどれも 195,421,066 bytes。sha256 は `sha256sum` で測った（〜2026-11-08T10:31Z）。

| 折り | run | val mAP | val AP_target | val AP_negative | 最良 epoch / 観測 epoch | sha256 |
|---|---|---|---|---|---|---|
| A | `dtowerrerun_p12_dcoco_foldA_seed42` | 0.7196251153 | 0.8044361925 | 0.6781756533 | 12 / 17 | `4c542a8b5977c13fa95556089b955fea5d0d0d51dde401cb0fc026f845b0ed42` |
| B | `dtowerrerun_p12_dcoco_foldB_seed42` | 0.4755093444 | 0.4900046104 | 0.6250579729 | 17 / 22 | `3d3035afb2973ce7941a6ba81c4a5166715ffd74350c90c5044465ba685e14d4` |
| C | `dtowerrerun_p12_dcoco_foldC_seed42` | 0.4427707417 | 0.5353496851 | 0.5068293267 | 11 / 16 | `a13be4d41e13a1380ce281595db821fd1293a40a3098f5116146a64c39aeedc2` |
| D | `dtowerrerun_p12_dcoco_foldD_seed42` | 0.5062879070 | 0.7086117215 | 0.5581371026 | 12 / 17 | `4e3829215b568e93331fcf67cb280722f7192561af05c7726f80aa31399972aa` |
| E | `dtowerrerun_p12_dcoco_foldE_seed42` | 0.5226364946 | 0.6778409427 | 0.4792722561 | 5 / 14 | `2ed21670bebd3cda4916c91dd0174b86867170b3ec915d3da9216f11b4027163` |

- どの run も epoch の上限 36 に届かずに止まった（patience 4、×0.1 を一度）
- 各 run の DataLoader の長さは実測の歩数（A 802・B 805・C 894・D 851・E 924）と一致し、学習率が目標に届いた歩はその歩数と一致した（`warmup_rank0.json`）
- COCO 1x の重みの読み込み（sha `2d2c19a7…`、一致したテンソル 596）が各 run の記録に在る
- 各 run の test（副次、prereg §2.4）は学習と val の評価の後に一度だけ評価した（`test_access.json` の `evaluations: 1`）。値は判定・選定に使わない

## 注意（評価の値の約束）

どの annotation ファイルにも `id: 0` の注釈が 1 つあり、pycocotools の COCOeval はそれに一致した検出を誤検出に数える。
上の val の値は前例と同じ評価器の値であり、この影響を注釈 1 つ分だけ含む（すべての run・すべての評価に一様にかかる）。
詳細は `tasks/T-2026-11-07-dtower-rerun/audit.md` §5 C-1。
