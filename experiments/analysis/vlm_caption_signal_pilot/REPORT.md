# REPORT — VLM キャプション信号の予備測定（V→P 完了時点（途中版）、非公式 T-2026-11-26-vlm-caption-signal-pilot）

非公式の予備測定。関門の判定と設計の判断（案の採否を含む）には使わない。差を並べるだけで採否・順位は書かない。
ホスト ilya（RTX 6000 Ada × 2）、Fold A（train 10 本・val 09・10）、seed 42。V→P 完了 63/63 本、V→T 完了 0/42 本。
V→P の差の幅 ±0.015 の中は「読めない」と書き符号で解釈しない。V→T は揺れの幅を測っていない。

## 1. VLM 記述の統計（SPEC §3.6）

- 対象フレーム: 11172 枚（train 9657 / val 1515）、動画 ['01', '02', '03', '06', '08', '09', '10', '11', '12', '13', '14', '15']、test 重複 []
- 解析成功: 11104/11172（失敗 68、拒否 0）
- 繰り返し一致（val 50 枚）: raw 32/50 (0.6400)、parsed 32/50 (0.6400)
- 伏せ字ヒット数: 甲 {'wound': 2969, 'tissue_action': 715, 'surface': 3807} / 乙 {'wound': 3637, 'tissue_action': 1912, 'surface': 3824, 'attr_collapsed': 52} / 丙 {'wound': 2969, 'tissue_action': 715, 'surface': 3807}
- 1 フレーム所要: 1.632 秒

## 2. V→P の差（6 工程 Jaccard / frame accuracy / 7 工程 Jaccard）

### 2.1 V→P 4 epoch 目（主）

| W | 型 | 予測-甲 − 入替-甲 | 予測-乙 − 入替-乙 | 予測-丙 − 入替-丙 | 予測-甲 − 空 | 入替-甲 − 空 | 参考（前回 T→P ep4） |
|---|---|---|---|---|---|---|---|
| W1 | D1-L2 | +0.0004（読めない） / -0.0013 / -0.0085 | -0.0005（読めない） / -0.0020 / -0.0119 | +0.0034（読めない） / +0.0013 / +0.0057 | +0.0072（読めない） / +0.0079 / -0.0323 | +0.0068（読めない） / +0.0092 / -0.0237 | +0.0371 |
| W1 | D2 | +0.0026（読めない） / +0.0007 / +0.0041 | +0.0055（読めない） / +0.0020 / +0.0029 | +0.0011（読めない） / +0.0007 / -0.0028 | +0.0057（読めない） / -0.0007 / -0.0212 | +0.0031（読めない） / -0.0013 / -0.0253 | +0.0288 |
| W1 | D3-L2 | +0.0089（読めない） / +0.0033 / +0.0126 | +0.0101（読めない） / +0.0040 / +0.0137 | +0.0068（読めない） / +0.0026 / +0.0058 | +0.0114（読めない） / +0.0112 / -0.0171 | +0.0026（読めない） / +0.0079 / -0.0298 | +0.0480 |
| W2 | D1-L2 | +0.0028（読めない） / +0.0007 / +0.0024 | +0.0028（読めない） / +0.0007 / +0.0024 | +0.0006（読めない） / +0.0007 / +0.0005 | +0.0120（読めない） / +0.0066 / +0.0103 | +0.0093（読めない） / +0.0059 / +0.0079 | +0.0643 |
| W2 | D2 | +0.0017（読めない） / -0.0013 / +0.0015 | -0.0020（読めない） / -0.0026 / -0.0017 | +0.0061（読めない） / +0.0026 / +0.0052 | +0.0010（読めない） / +0.0007 / +0.0008 | -0.0007（読めない） / +0.0020 / -0.0006 | +0.0203 |
| W2 | D3-L2 | +0.0047（読めない） / +0.0020 / +0.0040 | +0.0047（読めない） / +0.0020 / +0.0040 | +0.0016（読めない） / +0.0013 / +0.0014 | +0.0137（読めない） / +0.0086 / +0.0117 | +0.0090（読めない） / +0.0066 / +0.0077 | +0.0665 |
| W3 | D1-L2 | -0.0053（読めない） / -0.0033 / -0.0045 | -0.0044（読めない） / -0.0007 / -0.0038 | +0.0008（読めない） / +0.0007 / +0.0007 | -0.0006（読めない） / -0.0020 / -0.0005 | +0.0046（読めない） / +0.0013 / +0.0040 | +0.0852 |
| W3 | D2 | -0.0014（読めない） / +0.0013 / -0.0012 | +0.0015（読めない） / +0.0020 / +0.0013 | -0.0021（読めない） / +0.0026 / -0.0018 | +0.0016（読めない） / +0.0013 / +0.0014 | +0.0031（読めない） / +0.0000 / +0.0026 | +0.0093 |
| W3 | D3-L2 | +0.0012（読めない） / +0.0007 / +0.0010 | +0.0007（読めない） / +0.0013 / +0.0006 | +0.0035（読めない） / +0.0033 / +0.0030 | +0.0099（読めない） / +0.0007 / +0.0084 | +0.0087（読めない） / +0.0000 / +0.0074 | +0.0200 |

### 2.2 V→P 8 epoch 目（副次）

| W | 型 | 予測-甲 − 入替-甲 | 予測-乙 − 入替-乙 | 予測-丙 − 入替-丙 | 予測-甲 − 空 | 入替-甲 − 空 | 参考（前回 T→P ep4） |
|---|---|---|---|---|---|---|---|
| W1 | D1-L2 | +0.0059（読めない） / -0.0040 / -0.0159 | +0.0079（読めない） / -0.0026 / -0.0121 | +0.0018（読めない） / -0.0007 / -0.0114 | +0.0127（読めない） / +0.0066 / -0.0527 | +0.0068（読めない） / +0.0106 / -0.0368 | — |
| W1 | D2 | +0.0015（読めない） / +0.0000 / -0.0044 | +0.0031（読めない） / +0.0007 / -0.0031 | -0.0015（読めない） / -0.0007 / -0.0013 | -0.0111（読めない） / -0.0119 / +0.0187 | -0.0126（読めない） / -0.0119 / +0.0232 | — |
| W1 | D3-L2 | -0.0108（読めない） / -0.0033 / -0.0009 | -0.0131（読めない） / -0.0040 / -0.0030 | -0.0164 / -0.0086 / +0.0086 | +0.0130（読めない） / +0.0092 / -0.0618 | +0.0238 / +0.0125 / -0.0609 | — |
| W2 | D1-L2 | +0.0060（読めない） / +0.0013 / +0.0051 | +0.0078（読めない） / +0.0013 / +0.0067 | +0.0073（読めない） / +0.0013 / +0.0062 | +0.0160 / +0.0079 / +0.0137 | +0.0100（読めない） / +0.0066 / +0.0086 | — |
| W2 | D2 | -0.0002（読めない） / -0.0020 / -0.0002 | -0.0051（読めない） / -0.0026 / -0.0044 | -0.0020（読めない） / -0.0013 / -0.0017 | -0.0134（読めない） / -0.0119 / -0.0115 | -0.0132（読めない） / -0.0099 / -0.0113 | — |
| W2 | D3-L2 | +0.0059（読めない） / +0.0026 / +0.0051 | +0.0046（読めない） / +0.0007 / +0.0040 | +0.0048（読めない） / +0.0007 / +0.0041 | +0.0171 / +0.0073 / +0.0147 | +0.0112（読めない） / +0.0046 / +0.0096 | — |
| W3 | D1-L2 | +0.0112（読めない） / +0.0053 / +0.0096 | +0.0140（読めない） / +0.0046 / +0.0120 | +0.0040（読めない） / +0.0046 / +0.0034 | +0.0081（読めない） / +0.0040 / +0.0069 | -0.0031（読めない） / -0.0013 / -0.0027 | — |
| W3 | D2 | +0.0007（読めない） / +0.0007 / +0.0006 | -0.0019（読めない） / +0.0007 / -0.0016 | -0.0007（読めない） / +0.0013 / -0.0006 | -0.0027（読めない） / +0.0000 / -0.0023 | -0.0033（読めない） / -0.0007 / -0.0029 | — |
| W3 | D3-L2 | -0.0020（読めない） / -0.0033 / -0.0017 | -0.0026（読めない） / -0.0007 / -0.0022 | -0.0061（読めない） / -0.0040 / -0.0052 | -0.0094（読めない） / -0.0020 / -0.0081 | -0.0075（読めない） / +0.0013 / -0.0064 | — |

### 2.3 V→P 12 epoch 目（副次）

| W | 型 | 予測-甲 − 入替-甲 | 予測-乙 − 入替-乙 | 予測-丙 − 入替-丙 | 予測-甲 − 空 | 入替-甲 − 空 | 参考（前回 T→P ep4） |
|---|---|---|---|---|---|---|---|
| W1 | D1-L2 | +0.0130（読めない） / +0.0026 / +0.0042 | +0.0123（読めない） / +0.0040 / +0.0135 | +0.0034（読めない） / +0.0000 / -0.0001 | +0.0123（読めない） / +0.0099 / -0.0205 | -0.0007（読めない） / +0.0073 / -0.0248 | — |
| W1 | D2 | +0.0031（読めない） / -0.0007 / -0.0286 | +0.0011（読めない） / -0.0013 / -0.0286 | +0.0055（読めない） / +0.0007 / -0.0057 | -0.0121（読めない） / -0.0059 / -0.0782 | -0.0152 / -0.0053 / -0.0496 | — |
| W1 | D3-L2 | +0.0020（読めない） / +0.0040 / -0.0442 | -0.0000（読めない） / +0.0040 / -0.0531 | +0.0039（読めない） / -0.0040 / +0.0095 | +0.0114（読めない） / +0.0099 / -0.0663 | +0.0094（読めない） / +0.0059 / -0.0220 | — |
| W2 | D1-L2 | -0.0015（読めない） / -0.0020 / -0.0013 | -0.0008（読めない） / -0.0013 / -0.0007 | -0.0043（読めない） / -0.0026 / -0.0037 | +0.0054（読めない） / +0.0026 / +0.0046 | +0.0069（読めない） / +0.0046 / +0.0059 | — |
| W2 | D2 | +0.0036（読めない） / +0.0007 / +0.0031 | -0.0001（読めない） / -0.0020 / -0.0001 | +0.0088（読めない） / +0.0053 / +0.0075 | +0.0215 / +0.0185 / +0.0184 | +0.0179 / +0.0178 / +0.0153 | — |
| W2 | D3-L2 | +0.0289 / +0.0205 / +0.0248 | +0.0327 / +0.0231 / +0.0280 | +0.0138（読めない） / +0.0073 / +0.0118 | +0.0142（読めない） / +0.0099 / +0.0121 | -0.0147（読めない） / -0.0106 / -0.0126 | — |
| W3 | D1-L2 | +0.0054（読めない） / -0.0020 / +0.0046 | -0.0013（読めない） / -0.0033 / -0.0011 | +0.0011（読めない） / +0.0033 / +0.0010 | -0.0039（読めない） / -0.0079 / -0.0033 | -0.0093（読めない） / -0.0059 / -0.0080 | — |
| W3 | D2 | -0.0026（読めない） / +0.0000 / -0.0022 | -0.0081（読めない） / -0.0059 / -0.0069 | +0.0017（読めない） / +0.0000 / +0.0014 | +0.0009（読めない） / +0.0007 / +0.0007 | +0.0034（読めない） / +0.0007 / +0.0029 | — |
| W3 | D3-L2 | -0.0047（読めない） / -0.0040 / -0.0040 | +0.0035（読めない） / +0.0040 / +0.0030 | +0.0017（読めない） / +0.0007 / +0.0015 | -0.0076（読めない） / -0.0053 / -0.0065 | -0.0029（読めない） / -0.0013 / -0.0025 | — |

### 2.4 V→P 16 epoch 目（副次）

| W | 型 | 予測-甲 − 入替-甲 | 予測-乙 − 入替-乙 | 予測-丙 − 入替-丙 | 予測-甲 − 空 | 入替-甲 − 空 | 参考（前回 T→P ep4） |
|---|---|---|---|---|---|---|---|
| W1 | D1-L2 | +0.0060（読めない） / -0.0040 / -0.0091 | +0.0052（読めない） / -0.0046 / -0.0098 | -0.0003（読めない） / -0.0053 / -0.0190 | +0.0138（読めない） / +0.0066 / -0.0474 | +0.0078（読めない） / +0.0106 / -0.0383 | — |
| W1 | D2 | +0.0212 / +0.0053 / -0.0640 | +0.0198 / +0.0066 / -0.0469 | +0.0106（読めない） / +0.0040 / -0.0338 | -0.0092（読めない） / -0.0086 / -0.0504 | -0.0304 / -0.0139 / +0.0136 | — |
| W1 | D3-L2 | +0.0002（読めない） / +0.0000 / -0.0005 | +0.0089（読めない） / +0.0026 / +0.0083 | -0.0126（読めない） / -0.0145 / +0.0226 | +0.0048（読めない） / +0.0013 / -0.0613 | +0.0046（読めない） / +0.0013 / -0.0608 | — |
| W2 | D1-L2 | +0.0033（読めない） / -0.0020 / +0.0028 | +0.0022（読めない） / -0.0020 / +0.0019 | +0.0038（読めない） / -0.0007 / +0.0032 | +0.0082（読めない） / +0.0013 / +0.0070 | +0.0049（読めない） / +0.0033 / +0.0042 | — |
| W2 | D2 | +0.0059（読めない） / +0.0007 / +0.0051 | -0.0009（読めない） / -0.0033 / -0.0008 | -0.0008（読めない） / -0.0013 / -0.0007 | -0.0087（読めない） / -0.0046 / -0.0074 | -0.0146（読めない） / -0.0053 / -0.0125 | — |
| W2 | D3-L2 | +0.0058（読めない） / +0.0033 / +0.0049 | +0.0071（読めない） / +0.0092 / +0.0061 | +0.0140（読めない） / +0.0046 / +0.0120 | +0.0089（読めない） / +0.0059 / +0.0076 | +0.0031（読めない） / +0.0026 / +0.0027 | — |
| W3 | D1-L2 | +0.0040（読めない） / +0.0033 / +0.0034 | +0.0073（読めない） / +0.0026 / +0.0063 | +0.0004（読めない） / -0.0007 / +0.0003 | +0.0176 / +0.0119 / +0.0151 | +0.0136（読めない） / +0.0086 / +0.0117 | — |
| W3 | D2 | -0.0053（読めない） / -0.0026 / -0.0045 | +0.0003（読めない） / -0.0020 / +0.0002 | +0.0009（読めない） / +0.0000 / +0.0008 | -0.0027（読めない） / -0.0026 / -0.0023 | +0.0026（読めない） / +0.0000 / +0.0022 | — |
| W3 | D3-L2 | +0.0034（読めない） / +0.0000 / +0.0029 | +0.0055（読めない） / +0.0020 / +0.0047 | +0.0055（読めない） / +0.0020 / +0.0047 | +0.0049（読めない） / +0.0033 / +0.0042 | +0.0015（読めない） / +0.0033 / +0.0013 | — |

## 4. 予測（SPEC §7.1）の当たり外れ（4 epoch 目）

1. V→P 9 組のうち過半で 予測-甲−入替-甲 ≥ 予測-乙−入替-乙: 5/9
2. V→P 9 組のうち過半で 予測-甲−入替-甲 ≥ 予測-丙−入替-丙: 5/9
3. V→P W1 の 3 型で 予測-甲−入替-甲 < 前回 T→P: 3/3
4. V→T W1 の 2 型で 予測-甲−入替-甲 < 前回 P→T: 0/0

## 5. val フレームの記述例 20 件（甲の伏せ字後）

| # | frame | visibility | wound | tissue_action | surface |
|---|---|---|---|---|---|
| 1 | 09_1_0213 | field visible | A linear something is visible on the skin, appearing closed or nearly closed. | No active manipulation of tissue is visible in this frame. | The skin is exposed within a rectangular drape opening, with no visible blood or fluid. |
| 2 | 09_1_0308 | field visible | The skin is intact with a purple, wavy outline drawn on the surface, and no something is visible. | An instrument is being used to draw a line on the skin surface. | The skin is marked with a purple outline and a series of small dots, and the surrounding area is covered with blue drapes. |
| 3 | 09_1_0481 | field visible | The skin is incised with a visible linear cut and a dark marking line running along the something. | An instrument is being used to manipulate the tissue at the edge of the something. | The skin surface is dry with a dark surgical marking line and small puncture dots visible. |
| 4 | 09_1_0583 | field visible | The skin is cut and open, revealing a small something with visible tissue and blood. | An instrument is being used to manipulate or work within the open wound. | The operative field is illuminated by a bright light, with a white pad placed on the skin and small amounts of blood visible. |
| 5 | 09_1_0680 | field visible | The skin is cut and open, revealing a deep something with visible internal tissue. | Multiple hands are manipulating the wound edges and internal tissue using instruments. | The operative field is wet with blood, and a white something pad is placed on the skin near the something. |
| 6 | 09_1_0790 | field visible | The skin is cut and open, revealing a deep something with visible internal tissue. | An instrument is being used to manipulate or dissect tissue within the open wound. | The operative field is wet with blood, and a white drape is placed on the skin surrounding the something. |
| 7 | 09_1_0892 | field visible | The skin is cut and open, revealing a small something with visible red tissue at the edges. | A gloved hand is pressing or wiping the wound area while another hand holds an instrument near the opening. | The operative field is brightly illuminated, showing a small amount of blood at the wound site and a blue tube lying on the drape to the right. |
| 8 | 10_1_0286 | field visible | The mouth is held open, revealing the teeth and gums, with no external skin something visible. | An instrument is being held near the upper teeth, and the tissue is not being actively manipulated in a way that is clearly visible. | The oral cavity is wet, with a clear, transparent device holding the mouth open. |
| 9 | 10_1_0414 | field visible | The oral cavity is open, revealing the teeth and gums with a localized area of redness and tissue exposure. | An instrument is being used to manipulate or retract tissue within the mouth. | The operative field is wet with visible blood and tissue fluids. |
| 10 | 10_1_0510 | field visible | The skin is cut and open, revealing a deep surgical cavity with visible internal structures. | An instrument is being manipulated within the wound, appearing to grasp or adjust tissue. | The operative field is wet with blood and fluid, and a clear tube is visible within the cavity. |
| 11 | 10_1_0596 | field visible | The skin is cut and open, revealing the underlying tissue and teeth. | An instrument is manipulating tissue within the open wound. | The operative field is wet with pooled blood. |
| 12 | 10_1_0739 | field visible | The oral mucosa is incised and open, revealing the underlying bone and soft tissue structures. | Instruments are manipulating the tissue and bone within the open surgical site. | The operative field is wet with blood and tissue fluids, and a clear something is present. |
| 13 | 10_1_0838 | field visible | The skin is cut and open, revealing the underlying tissue and teeth. | An instrument is grasping tissue within the open wound. | The operative field is wet with pooled blood and fluid. |
| 14 | 10_1_0943 | field visible | The skin is cut and open, revealing the underlying tissue and teeth. | An instrument is grasping tissue within the open wound. | The operative field is wet with pooled blood and fluid. |
| 15 | 10_1_1072 | field visible | The skin is cut and open, revealing a deep cavity with exposed tissue and bone. | An instrument is manipulating tissue within the open wound. | The operative field is wet with pooled blood and contains a clear plastic device holding the area open. |
| 16 | 10_1_1198 | field visible | The skin is cut and open, revealing a deep cavity with exposed internal structures. | An instrument is being manipulated within the wound while another instrument holds the tissue edges apart. | The operative field is wet with visible blood and fluid, and a blue tube lies across the lower right area. |
| 17 | 10_1_1479 | field visible | The skin is cut and open, revealing the underlying tissue and bone structure. | An instrument is grasping tissue within the open wound. | The operative field is wet with blood and fluid, and a clear device is placed over the area. |
| 18 | 10_1_1580 | field visible | The oral cavity is open, revealing the upper and lower teeth and the surrounding gum tissue. | An instrument is being used to manipulate the gum tissue near the upper teeth. | The operative field is wet with blood and saliva, and a clear plastic device is placed over the patient's face. |
| 19 | 10_2_0004 | field visible | The oral cavity is held open, revealing the teeth and gums with visible redness and blood in the lower region. | A hand is holding the upper lip and gum area to maintain exposure of the teeth. | The operative field is wet with blood and saliva, and a clear plastic device is placed over the upper teeth. |
| 20 | 10_2_0299 | field visible | The skin is cut and open, revealing the underlying tissue and teeth. | An instrument is being used to manipulate tissue within the open wound. | The operative field is wet with blood and fluid. |

