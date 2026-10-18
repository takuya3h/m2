# T-2026-10-19-evidence-maps-revise

## 1. 解決された参照

inputs.data.split_files と inputs.denominator は参照しなかった。frozen_source は指定なし。sigma_policy は既定の series: pstd / sigma_source: paired_delta / delta_sigma_source: paired を継承するが、本契約の計算には使用しない。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

<a id="issuer_cautions"></a>
## issuer_cautions

**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 4 | 仕組みの挙動は実装を読んでから信じる |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
| 7 | **丸めた表示を実数として扱わない** |
| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
| 11 | 測定の副作用が禁止領域へ触れないか確かめる |
| 12 | **判断の前に、いま見ているものが最新かを確かめる** |
| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
| 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

## 判定・完了判定

G1・G2・G3 は pass。PR・送出・抑止解除は後述。

a: 改訂前後の三件のバイト数・SHA-256 は SPEC の値と一致。b: 変更範囲と無変更九件は audit の最終検証に記録。c: 三件とも検査対象となり違反 0。d: 分類の和は C=29 / B=34 / N=37、ID 集合の差は予測と一致。e: 予測外の ID はなし。f: 新規三件は下表。g: N-30〜N-46 の全17行・18 ID がその行と比較された。h: 最終の PR 応答と forbidden-check は audit に記録。

起点・改訂前の測定は [audit.md:11](audit.md#L11)、改訂後は [audit.md:111](audit.md#L111)、様式検査は [audit.md:131](audit.md#L131)、ID ごとの集合比較と実際の問い合わせ・応答由来の書誌は [audit.md:196](audit.md#L196)。原測定は baseline.json、比較の構造化記録は comparison.json。

## 実測と事前予測

|地図|書誌一致 予測→実測|書誌に差|照合不能|不在|到達不能|ID のない行|
|---|---|---|---|---|---|---|
|C|29→29|0→0|0→0|0→0|0→0|C-24|
|B|34→34|0→0|0→0|0→0|0→0|なし|
|N|37→37|0→0|0→0|0→0|0→0|なし|

C: arXiv 2511.06549 を除き DOI 10.1109/TPAMI.2021.3055233 を追加。B: arXiv 1610.08844 を除き 2309.01093 を追加。N: DOI 10.1016/j.media.2022.102611 の追加のみ。

|行・新規 ID|分類|照合先の題名|著者|掲載先|
|---|---|---|---|---|
|C-17 10.1109/TPAMI.2021.3055233|実在・書誌一致|Forecasting Action Through Contact Representations From First Person Video|Eadom Dessalene, Chinmaya Devaraj, Michael Maynord, Cornelia Fermüller, Yiannis Aloimonos|IEEE Transactions on Pattern Analysis and Machine Intelligence|
|B-18 2309.01093|実在・書誌一致|CoTDet: Affordance Knowledge Prompting for Task Driven Object Detection|Jiajin Tang, Ge Zheng, Jingyi Yu, Sibei Yang|専用欄は null。comment: Accepted by ICCV 2023|
|N-15 10.1016/j.media.2022.102611|実在・書誌一致|Anticipation for surgical workflow through instrument interaction and recognized Signals|Kun Yuan, Matthew Holden, Shijian Gao, Wonsook Lee|Medical Image Analysis|

## 起票者の誤り・逸脱・UNKNOWN

書誌の予測の誤りは観測されなかった。起票者の誤り（self_contradiction）: 契約の変更範囲と task スキルの inbox.d 必須記録が衝突。利用者の回答「1」により、本契約の inbox.d 一件の追加を許可された。変更範囲 b はこの承認済み例外を含めて評価する。
Default モード固定でプランモードへの切替手段がなく、planning-with-files と agentmemory も利用不可のため、契約のフェーズ順と本契約内の記録で進行した。コード変更なしのため README 更新は対象外。GPU・実験・pytest は契約どおり未実行。生成物は再生成していない。
プリフライトは 6 PASS / 0 WARN / 8 SKIP / 0 FAIL。SKIP は P2 CUDA 拡張、P3 決定性、P4 事前登録、P5 凍結源、P11 GPU 空き、P12 解決対象参照、P13 対称性表、P14 提案カード。
陽性対照は版欠落・余分な ID・一バイト変更を検出した（audit:164）。B-18 の掲載先の専用欄は null。原典の内容・研究文脈の正しさは今回の照合の検証対象外。

## 送出

PR と台帳送出の結果は、確定後ここに記録する。
