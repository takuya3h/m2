# A1 折りの材料（実測）

出所: `data/annotations/egosurgery_phase/*.csv`（23 クリップ）、
`data/annotations/egosurgery_tool/instances_{train,val,test}.json`（COCO・15 クラス）、
`data/annotations/egosurgery_hts/{hand_seg,hand_tool_seg,tool_seg}/*.json`

動画 15 / クリップ 23 / 工程 9 種 / 術具 15 クラス

## 動画ごとの工程フレーム数

| vid | split | clips | frames | anesthesia | closure | design | disinfection | dissection | dressing | hemostasis | incision | irrigation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | train | 1 | 999 | 36 | 508 | 56 | 16 | 131 | 0 | 157 | 95 | 0 |
| 02 | train | 1 | 529 | 49 | 181 | 84 | 44 | 96 | 0 | 44 | 22 | 9 |
| 03 | train | 2 | 1363 | 34 | 994 | 41 | 0 | 172 | 0 | 29 | 69 | 24 |
| 04 | test | 2 | 1643 | 56 | 636 | 177 | 17 | 530 | 74 | 50 | 42 | 61 |
| 05 | test | 2 | 1318 | 24 | 771 | 20 | 0 | 285 | 94 | 71 | 53 | 0 |
| 06 | train | 2 | 1447 | 28 | 657 | 30 | 11 | 550 | 0 | 99 | 72 | 0 |
| 07 | test | 2 | 1788 | 47 | 1108 | 24 | 19 | 361 | 0 | 124 | 70 | 35 |
| 08 | train | 2 | 1591 | 35 | 748 | 27 | 0 | 613 | 0 | 45 | 123 | 0 |
| 09 | val | 1 | 672 | 79 | 0 | 101 | 18 | 298 | 0 | 0 | 176 | 0 |
| 10 | val | 2 | 1232 | 40 | 665 | 20 | 0 | 297 | 116 | 60 | 34 | 0 |
| 11 | train | 1 | 865 | 12 | 232 | 33 | 0 | 446 | 37 | 81 | 11 | 13 |
| 12 | train | 1 | 619 | 27 | 266 | 0 | 0 | 178 | 0 | 21 | 99 | 28 |
| 13 | train | 1 | 843 | 14 | 465 | 21 | 0 | 164 | 0 | 30 | 149 | 0 |
| 14 | train | 2 | 1858 | 38 | 0 | 0 | 0 | 1352 | 0 | 358 | 63 | 47 |
| 15 | train | 1 | 466 | 36 | 0 | 12 | 0 | 326 | 0 | 0 | 92 | 0 |
| **計** | | 23 | 17233 | 555 | 7231 | 646 | 125 | 5799 | 321 | 1169 | 1170 | 217 |

## 動画ごとの術具（COCO）と HTS の有無

| vid | split | tool images | tool annotations | hand_seg | hand_tool_seg | tool_seg |
|---|---|---|---|---|---|---|
| 01 | train | 913 | 2412 | ✓ | ✓ | ✓ |
| 02 | train | 461 | 1203 | ✓ | ✓ | ✓ |
| 03 | train | 1089 | 2743 | ✓ | ✓ | ✓ |
| 04 | test | 1329 | 3038 | ✓ | ✓ | ✓ |
| 05 | test | 1225 | 2713 | ✓ | ✓ | ✓ |
| 06 | train | 1379 | 5045 | ✓ | ✓ | ✓ |
| 07 | test | 1711 | 6922 | ✓ | ✓ | ✓ |
| 08 | train | 1400 | 3719 | ✓ | ✓ | ✓ |
| 09 | val | 518 | 1471 | ✓ | ✓ | ✓ |
| 10 | val | 997 | 3236 | ✓ | ✓ | ✓ |
| 11 | train | 754 | 2445 | ✓ | ✓ | ✓ |
| 12 | train | 609 | 2471 | ✓ | ✓ | ✓ |
| 13 | train | 822 | 1950 | ✓ | ✓ | ✓ |
| 14 | train | 1810 | 8456 | ✓ | ✓ | ✓ |
| 15 | train | 420 | 1828 | ✓ | ✓ | ✓ |
| **計** | | 15437 | 49652 | 15 動画 | 15 動画 | 15 動画 |

術具クラス（15）: Bipolar Forceps, Electric Cautery, Forceps, Gauze, Hook, Mouth Gag, Needle Holders, Raspatory, Retractor, Scalpel, Scissors, Skewer, Suction Cannula, Syringe, Tweezers

**折りの設計は本契約では行わない。** 上表は材料である。
