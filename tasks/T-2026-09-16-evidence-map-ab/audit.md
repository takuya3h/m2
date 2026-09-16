# audit — T-2026-09-16-evidence-map-ab

照合の問い合わせと応答の全文。事実の記録は `RESULT.md`。

## 1. 照合の手段

問い合わせ側は読み取りのみ（SPEC 禁止 7 の「照合の問い合わせは読み取りであり送信ではない」）。
User-Agent に連絡先を入れた（Crossref の作法）。

    Crossref : https://api.crossref.org/works/{DOI}
    arXiv    : http://export.arxiv.org/api/query?id_list={ID1,ID2,...}
    doi.org  : https://doi.org/{DOI}  （到達性の確認のみ）
    UA       : EvidenceMapCheck/1.0 (mailto:daky.o7600@gmail.com)

## 2. Task A — 到達性

    HTTP 200  https://api.crossref.org/works/10.1007/978-3-031-72089-5_18
    HTTP 200  https://doi.org/10.1007/978-3-031-72089-5_18
    HTTP 200  http://export.arxiv.org/api/query?id_list=2405.19644

三方向とも到達できた。escalate_if の「いずれにも到達できない場合」には該当しない。

## 3. Task A — 対照（両方向）

### 3.1 陽性対照 — 起票者が確認済みの DOI 二件

    DOI      10.1007/978-3-031-72089-5_18
    HTTP     200  -> 判定: 実在
    題       EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos
    著者     Fujii Ryo; Hatano Masashi; Saito Hideo; Kajita Hiroki
    年/種別  2024 / book-chapter
    掲載     Lecture Notes in Computer Science

    DOI      10.1016/j.media.2024.103366
    HTTP     200  -> 判定: 実在
    題       LoViT: Long Video Transformer for surgical phase recognition
    著者     Liu Yang; Boels Maxence; Garcia-Peraza-Herrera Luis C.; Vercauteren Tom; Dasgupta Prokar; Granados Alejandro; Ourselin Sébastien
    年/種別  2025 / journal-article
    掲載     Medical Image Analysis

### 3.2 陰性対照 — 架空の DOI

    DOI      10.1000/zz-not-a-real-doi-2026
    HTTP     404  -> 判定: 不在
    応答本文 Resource not found.

**両方向が揃った。** 実在 DOI が 200 で返り、架空 DOI が 404 で落ちる。
片方向だけでは「常に実在と返す壊れ方」と区別できない。

### 3.3 検査器の対照（成果物の検査が空振りでないこと）

地図の写しに `citeturn0search12` を一行足して数え直した。

    足す前: grep -c citeturn -> 0
    足した後: grep -c citeturn -> 1

三方向の検索記録の検査も同様に、一方向の語を消すと 3 から 2 へ落ちることを確かめた。

## 4. Task B — 全行の照合結果

26 行（地図 A 15 / 地図 B 11）。DOI 4 件は Crossref、arXiv ID 26 件は arXiv API。
両方を持つ行は両方を引いた。

| 地図 | 行 | 通称 | 照会 ID | 判定 | 照合が返した第一著者 | 年 |
|---|---|---|---|---|---|---|
| A | 135 | GGMAE／EgoSurgery-Phase | DOI 10.1007/978-3-031-72089-5_18 / arXiv 2405.19644 | 実在・書誌一致 | Fujii Ryo | 2024 |
| A | 136 | EndoNet | arXiv 1602.03012 | 実在・書誌一致 | Andru P. Twinanda | 2016 |
| A | 137 | TeCNO | DOI 10.1007/978-3-030-59716-0_33 / arXiv 2003.10751 | 実在・書誌一致 | Czempiel Tobias | 2020 |
| A | 138 | Trans-SVNet | arXiv 2103.09712 | 実在・書誌一致 | Xiaojie Gao | 2021 |
| A | 139 | LoViT | DOI 10.1016/j.media.2024.103366 / arXiv 2305.08989 | 実在・書誌一致 | Liu Yang | 2025 |
| A | 140 | Ramesh ほか 2023 Medical Ima | DOI 10.1016/j.media.2023.102844 / arXiv 2207.00449 | 実在・書誌一致 | Ramesh Sanat | 2023 |
| A | 141 | SurgMAE | arXiv 2305.11451 | 実在・書誌一致 | Muhammad Abdullah Jamal | 2023 |
| A | 142 | SurgPETL | arXiv 2409.20083 | 実在・書誌一致 | Shu Yang | 2024 |
| A | 143 | MS-TCN | arXiv 1903.01945 | 実在・書誌一致 | Yazan Abu Farha | 2019 |
| A | 144 | ASFormer | arXiv 2110.08568 | 実在・書誌一致 | Fangqiu Yi | 2021 |
| A | 145 | LSTR | arXiv 2107.03377 | 実在・書誌一致 | Mingze Xu | 2021 |
| A | 146 | EgoVLP | arXiv 2206.01670 | 実在・書誌一致 | Kevin Qinghong Lin | 2022 |
| A | 147 | Ego-Exo | arXiv 2104.07905 | 実在・書誌一致 | Yanghao Li | 2021 |
| A | 148 | EGTEA Gaze+ | arXiv 2006.00626 | 実在・書誌一致 | Yin Li | 2020 |
| A | 149 | EPIC-KITCHENS | arXiv 1804.02748 | 実在・書誌一致 | Dima Damen | 2018 |
| B | 193 | EndoNet | arXiv 1602.03012 | 実在・書誌一致 | Andru P. Twinanda | 2016 |
| B | 194 | Twinanda ほか 2016 M2CAI 技術報 | arXiv 1610.08851 | 実在・書誌一致 | Andru P. Twinanda | 2016 |
| B | 195 | MTRCNet-CL | arXiv 1907.06099 | 実在・書誌一致 | Yueming Jin | 2019 |
| B | 196 | Perez | arXiv 1709.07871 | 実在・書誌一致 | Ethan Perez | 2017 |
| B | 197 | LAVT | arXiv 2112.02244 | 実在・書誌一致 | Zhao Yang | 2021 |
| B | 198 | CLIPSeg | arXiv 2112.10003 | 実在・書誌一致 | Timo Lüddecke | 2021 |
| B | 199 | MDETR | arXiv 2104.12763 | 実在・書誌一致 | Aishwarya Kamath | 2021 |
| B | 200 | Standley | arXiv 1905.07553 | 実在・書誌一致 | Trevor Standley | 2019 |
| B | 201 | Context R-CNN | arXiv 1912.03538 | 実在・書誌一致 | Sara Beery | 2019 |
| B | 202 | SELSA | arXiv 1907.06390 | 実在・書誌一致 | Haiping Wu | 2019 |
| B | 203 | SIN | arXiv 1807.00119 | 実在・書誌一致 | Yong Liu | 2018 |

**四種の件数**

    実在・書誌一致 : 26
    実在・書誌に差 : 0
    不在           : 0
    到達不能       : 0

不在が零件のため、地図から外した行は無い。
**零件が空振りでないことは 3.2 の陰性対照が示す**（照合器は不在を不在と返す）。

書誌の差が零件のため、escalate_if の「差が三件以上」には該当しない。

### 4.1 いったん差と誤検出し、取り消した二件

最初の照合器は次の二件を「書誌に差」と出したが、**いずれも照合器側の正規化の誤りであり、
地図の誤りではなかった。**

    MS-TCN  : 地図の「Abu Farha」は複合姓。照合器が先頭語 Abu だけを取り、
              照合側は末尾語 farha を取ったため一致しなかった
    CLIPSeg : 地図の「Lüddecke」を照合側だけ ASCII 化して luddecke にし、
              地図側は ü のまま小文字化したため一致しなかった

両側に同じ正規化（NFKD -> ASCII -> 小文字）を当て、著者列の全語と照合側の全語で
突き合わせる方式に直したところ、二件とも「実在・書誌一致」になった。

## 5. Task B-5 — 著者未確認二件の補完

### SurgMAE（arXiv 2305.11451）

    題   SurgMAE: Masked Autoencoders for Long Surgical Video Analysis
    著者 Muhammad Abdullah Jamal; Omid Mohareri
    年   2023

### SurgPETL（arXiv 2409.20083）

    題   SurgPETL: Parameter-Efficient Image-to-Surgical-Video Transfer Learning for Surgical Phase Recognition
    著者 Shu Yang; Zhiyuan Cai; Luyang Luo; Ning Ma; Shuchang Xu; Hao Chen
    年   2024

両件とも応答に著者があり、UNKNOWN にはならなかった。地図の文献欄の「著者未確認」を
この著者名で置き換えた（SPEC Task B-5 の指示）。印の列の起票時の状態は書き換えていない。
