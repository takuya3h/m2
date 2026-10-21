# EgoSurgery-HTS 注釈の EDA：hand_seg・tool_seg・hand_tool_seg と工程・術具 bbox の関係（動画 01〜15）

- 生成: 集計スクリプト `docs/analysis_scripts/hts_phase_tool_annotation_stats.py`（読み取り専用。数値はすべて注釈からの実測で、推定・補完はしない）
- 対象: `data/annotations/egosurgery_hts/` の 3 種。工程・術具 bbox と突き合わせるのは術具 bbox のある 15,437 フレーム（動画 01〜15）
- 先行 EDA（術具・工程・手）は [`phase_tool_annotation_stats.md`](phase_tool_annotation_stats.md)。手の在否と box での手–術具の近さはそちらにあり、本書はマスク・把持・工程の関係を扱う

## 目次

| 部 | 節 |
| --- | --- |
| [0. 母集団・入力・注釈どうしの構造](#s0) | [0.1](#s0-1) 入力と結合 · [0.2](#s0-2) 母集団の層 · [0.3](#s0-3) 注釈どうしの構造（実測） · [0.4](#s0-4) 用語と記号 |
| [1. 3 種の注釈の規模](#s1) | [1.1](#s1-1) ファイルごとの件数 · [1.2](#s1-2) hand_seg · [1.3](#s1-3) tool_seg · [1.4](#s1-4) hand_tool_seg |
| [2. tool_seg と術具 bbox の対応](#s2) | [2.1](#s2-1) クラスごとの対応 · [2.2](#s2-2) tool_seg の未注釈フレーム |
| [3. 工程との関係](#s3) | [3.1](#s3-1) 工程ごとの被覆 · [3.2](#s3-2) 工程ごとの欠け（術具 bbox のあるフレームを分母に） · [3.3](#s3-3) tool_seg だけにあるクラス × 工程 · [3.4](#s3-4) 手のマスクの面積 × 工程 · [3.5](#s3-5) 把持 × 工程 · [3.6](#s3-6) 工程ごとに持たれている術具のクラス · [3.7](#s3-7) 術具のクラスごとの把持 · [3.8](#s3-8) 工程との情報量（注釈のあいだの参考値） · [3.9](#s3-9) 工程の切り替わりと把持の変化 · [3.10](#s3-10) 手術の進行度と把持 · [3.11](#s3-11) 術具のマスクと手のマスクの重なり × 工程 |
| 付録 | [付録 A：既存の HTS 分析との対応](#sA) · [付録 B：再現](#sB) |

## 要点

**注釈の構造**（[§0](#s0)・[§2](#s2)）
1. **HTS で工程ラベルを持つのは、術具 bbox のある 15,437 フレームの分だけ**（うち 15,423 フレームに HTS の注釈がある）。
   工程だけのフレーム 1,796（disinfection は 125 行のうち 114）と
   extra のフレーム（3,420〜4,035）は、工程ラベルと HTS を同時には持たない（[§0.2](#s0-2)）
2. 3 種は互いに独立ではない。hand_seg の手は先行 EDA の手（raw02）と同じ、hand_tool_seg の自分の手は hand_seg の自分の手と同じマスク。
   tool_seg の Tool15 部分は Mouth Gag を除く 14 クラスで術具 bbox とインスタンス数・写るフレームが完全に同じで、**Mouth Gag は tool_seg に 1 件も無い**（[§0.3](#s0-3)・[§2.1](#s2-1)）
3. 未注釈のフレームは中身で決まっている。tool_seg の未注釈 470 は術具 bbox が Mouth Gag だけか 0 個のフレーム、
   hand_tool_seg の未注釈（loss_mask）460 は自分の手が写らないフレームと完全に一致する。README の「Mouth Gag / Skewer による除外」という説明に
   当てはまるのは loss_mask の 14.1% だけ（[§2.2](#s2-2)・[§3.2](#s3-2)）
4. **把持は box の重なりで決まっている。** 把持術具は同じ側の手と box の IoU が最大の術具と 97.4% 一致し、
   マスクの IoU が最大の術具とは 30.9% しか一致しない（[§0.3](#s0-3)）

**工程との関係**（[§3](#s3)）
5. 工程 CSV の行のうち 3 種すべての注釈があるのは 84.5%。低いのは
   disinfection 0%、dressing 26.8%、design 57.3%
   （[§3.1](#s3-1)）
6. tool_seg だけにある 8 クラスは工程に強く偏る（Pen → design、Cup → design、Petri Dish → dissection、Spoon → dissection、Kidney Dish → irrigation など）が、
   多くは 1〜3 動画にしか出ない（[§3.3](#s3-3)）
7. 両手の使い方が工程で違う。両手で 1 つを持つのは anesthesia 41.3%・design 30.2% に多く、
   closure は 4.9%。左右がともにふさがるのは incision・dissection・hemostasis で
   81.9〜82.0%。
   irrigation は何も持たないフレームが 13.6%（[§3.5](#s3-5)）
8. **右手の最多の術具は工程ごとに入れ替わり、左手の最多は工程によらず陰性対照群の術具。** 右手の最多は
   design Skewer 56.3%、anesthesia Syringe 38.3%、incision Scalpel 70.1%、
   dissection Scissors 31.3%、hemostasis Bipolar Forceps 54.8%、closure Needle Holders 55.2%。
   左手の最多は design Mouth Gag、anesthesia Gauze、incision Tweezers、dissection Tweezers、hemostasis Tweezers、irrigation Gauze、closure Tweezers、dressing Mouth Gag（[§3.6](#s3-6)）
9. 持つ手は動画をまたいで安定している。主に左で持つ動画: Tweezers 15/15。主に右で持つ動画:
   Scissors 14/15、Bipolar Forceps 11/11、
   Needle Holders 10/12（[§3.7](#s3-7)）
10. 動画一つ抜きで「値ごとの最多工程」を当てる規則では、持たれている（側, クラス）の集合 81.0% が
    写っている術具の集合（術具 bbox）75.6% より当たる。相互情報量は値の種類の多い後者が大きい
    （1.735 対 1.545 bit）。
    把持の状態（左・右・両手で持つか）だけでは 32.1% で、常に closure と答える基準 41.5% を下回る（[§3.8](#s3-8)）
11. 工程が変わる隣接フレームの 92.6% で把持が変わる（工程が同じなら 40.1%）。
    hemostasis → dissection で最も多く手放すのは 右手の Bipolar Forceps、
    最も多く持ち始めるのは 右手の Scissors（[§3.9](#s3-9)）

## <a id="s0"></a>0. 母集団・入力・注釈どうしの構造

### <a id="s0-1"></a>0.1 入力と結合

| データ | ファイル | 中身 |
| --- | --- | --- |
| hand_seg | `data/annotations/egosurgery_hts/hand_seg/{train,val,test,extra}.json` | 手 4 クラスのインスタンスマスク（RLE） |
| tool_seg | `data/annotations/egosurgery_hts/tool_seg/{train,val,test,extra}.json` | 術具 31 クラスのインスタンスマスク（RLE） |
| hand_tool_seg | `data/annotations/egosurgery_hts/hand_tool_seg/{train,val,test,extra}.json` と `loss_mask/` | 自分の左手・右手と、左手・右手・両手で持っている術具のマスク（5 クラス、RLE） |
| 工程 | `data/annotations/egosurgery_phase/*.csv`（動画 01〜15 の 23 本） | フレームごとの工程 |
| 術具 bbox | `data/processed/joint_manifest/{train,val,test}.json` | 術具 15 クラス（Tool15）の box。先行 EDA と同じ |
| HTS の元の注釈 | `data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/*/annotations.json` | 38 クラスの矩形。把持術具のクラスを決める最後の段だけに使う（§0.3） |

- 結合はすべてフレーム ID（ファイル名から拡張子を除いたもの、例 `01_1_0124`）で行う。HTS の train / val / test の各ファイルの画像は、術具 bbox の同じ split の画像に含まれる（検査済み）
- 先行 EDA（術具・工程・手、動画 01〜15）は [`phase_tool_annotation_stats.md`](phase_tool_annotation_stats.md)。本書の工程・術具 bbox の母集団はそれと同じ

### <a id="s0-2"></a>0.2 母集団の層

| 集合 | フレーム | 備考 |
| --- | ---: | --- |
| 元のフレーム画像（`01_frames/initial_videos/`、動画 01〜15） | 27,535 | 参考 |
| HTS の注釈があるフレーム（3 種 × 4 ファイルの和集合） | 19,496 | クリップ 03_3 を含まない |
| 工程 CSV の行（動画 01〜15） | 17,233 |  |
| 　うち術具 bbox が無い（工程だけ） | 1,796 | **HTS の注釈も 1 件も無い** |
| 　**うち術具 bbox がある（主な母集団）** | **15,437** | 工程・術具 bbox・HTS を突き合わせられるのはここだけ |
| 　　うち 3 種とも未注釈 | 14 |  |
| 　　うち hand_seg の注釈がある | 15,397（99.7%） |  |
| 　　うち tool_seg の注釈がある | 14,967（97.0%） |  |
| 　　うち hand_tool_seg の注釈がある | 14,977（97.0%） |  |
| 　　うち 3 種すべての注釈がある | 14,570（94.4%） |  |
| HTS の extra（hand_seg） | 4,035 | 術具 bbox の split に属さない。工程 CSV にあるもの 0 |
| HTS の extra（tool_seg） | 3,532 | 術具 bbox の split に属さない。工程 CSV にあるもの 0 |
| HTS の extra（hand_tool_seg） | 3,420 | 術具 bbox の split に属さない。工程 CSV にあるもの 0 |

- **HTS の注釈のうち工程ラベルを持つのは、術具 bbox のあるフレームの分だけ**（15,423 フレーム）。工程 CSV だけのフレームと extra のフレームには、それぞれ HTS と工程ラベルが無い
- 工程だけのフレーム 1,796 の工程の内訳: disinfection 114、design 268、anesthesia 56、incision 74、dissection 359、hemostasis 48、irrigation 40、closure 635、dressing 202。disinfection は工程 CSV の 125 行のうち 114 行に HTS が無い
- extra のフレームは工程ラベルを持たないので、本書の工程の分析には入らない。canonical の README は extra を学習に混ぜると術具 bbox の split へのリーク源になりうると注意している（`data/annotations/egosurgery_hts/hand_tool_seg/README.md` §8）
- HTS の動画は 01〜15 の 15 本で、動画 17〜21 は含まない

### <a id="s0-3"></a>0.3 注釈どうしの構造（実測）

| 関係 | 結果 |
| --- | --- |
| hand_seg の手 box と raw02（先行 EDA §4 の手） | フレームごとのクラスと box が 15,437/15,437 フレームで一致 |
| hand_tool_seg の自分の手マスクと hand_seg の自分の手マスク | 14,977/14,977 フレームでマスク（RLE）まで同一 |
| hand_tool_seg に他者の手 | クラスが無い（自分の手と、自分の手が持つ術具だけ） |
| tool_seg の Tool15 部分と術具 bbox | Mouth Gag 以外の 14 クラスで、クラスごとのインスタンス数・写るフレームが術具 bbox と**完全に同じ**。同じクラスどうし box IoU ≥ 0.5 で対応がつくのは 42,749/43,667（97.9%）。Mouth Gag は tool_seg に 0 件（[§2](#s2)） |
| tool_seg が未注釈のフレーム | 470 フレーム。すべて術具 bbox の術具が Mouth Gag だけか 0 個のフレーム（[§2.2](#s2-2)） |
| hand_tool_seg が未注釈のフレーム（loss_mask） | 460 フレーム。**hand_seg で自分の手が写らないフレームと完全に一致**（[§3.2](#s3-2)） |
| 把持術具のマスク（左手・右手・両手で持つ術具） | 24,515 個 |
| 　tool_seg のマスクと RLE まで同一 | 21,516（87.8%）→ tool_seg のクラスを使う |
| 　同一ではないが術具 bbox と box IoU ≥ 0.5 | 1,935（7.9%）→ 術具 bbox のクラスを使う。うち Mouth Gag 1,913 |
| 　どちらでもないが HTS の元の注釈（38 クラス）と box IoU ≥ 0.5 | 917（3.7%）→ 元の注釈のクラスを使う。Suture, Suture Needle 915、Bone Curette 1、Caliper 1 |
| 　どれとも対応がつかない | 147（0.6%）→ 「不明」 |
| 　同一ではない把持術具マスクの、同じフレームの tool_seg マスクとの IoU の最大値 | 中央値 0.000（2,621 個。tool_seg に同じ術具が無い） |
| 左手・右手の把持術具（tool_seg と同一の 20,346 個）は、同じ側の自分の手と |  |
| 　box の IoU が最大の tool_seg インスタンス | 19,826（97.4%） |
| 　マスクの IoU が最大の tool_seg インスタンス | 6,294（30.9%） |
| 　マスクが 1 画素も重ならない | 14,014（68.9%） |
| `bbox` 欄 = マスクの外接矩形（1 px 以内） | hand_seg 100.0%、tool_seg 100.0%。tool_seg の `area` 欄 = マスクの画素数: 100.0% |
| 画像として載るが注釈が 0 件のフレーム | hand_seg 0、tool_seg 0、hand_tool_seg 0（載っている画像 = 注釈のある画像） |

- **由来**: HTS のマスクは術具・手の box を SAM のプロンプトにして作られている（EgoSurgery-HTS 論文 arXiv:2503.18755。`docs/experiment_log.md` 2026-07-29）。把持術具は論文では「手のセグメンテーションとの IoU が最大の術具」とされる
- **実データでは、把持術具は同じ側の手と box の IoU が最大の術具とほぼ一致し（97.4%）、マスクの IoU が最大の術具とは 30.9% しか一致しない。把持術具の 68.9% は手のマスクと画素で重ならない。**hand_tool_seg の「把持」は手と術具の box の重なりから決まった量として読む。手と術具のマスクは物体ごとに描かれ、接していても境界で重ならないことがあるので、マスクが重ならないことは「触れていない」ことを意味しない
- 以降、把持術具のクラスは上の 4 段（tool_seg と同一 → 術具 bbox と対応 → 元の注釈と対応 → 不明）で決める。対応がついたのは 99.4%。tool_seg に 0 件の Mouth Gag と Suture, Suture Needle も、この段で把持術具として現れる

### <a id="s0-4"></a>0.4 用語と記号

| 記号 | 意味 |
| --- | --- |
| 注釈がある | その種類の注釈が 1 件以上あるフレーム。HTS の JSON は注釈のある画像だけを載せる（§0.3）ので、無いフレームは「未注釈」で、「写っていない」とは区別できない |
| 把持術具 | hand_tool_seg の Left Hand Tool（左）・Right Hand Tool（右）・Two Hands Tool（両手）。いずれも自分（カメラを着けた術者）の手 |
| Tool15 | 術具 bbox の 15 クラス。tool_seg の 31 クラスは Tool15 の 15 クラスをすべて含み、ほかに 16 クラスを持つ（Tool15 外） |
| 在率 | そのフレーム集合のうち、そのクラスが 1 つ以上あるフレームの割合 |
| † | 術具 bbox のあるフレームが 200 未満の工程（disinfection 11, irrigation 177, dressing 119）。割合は不安定 |
| 群 | `context/conventions.md#det_groups` の標的群・陰性対照群（Tool15 のみ） |
| 参照順・略号 | disinfection（DI） → design（DE） → anesthesia（AN） → incision（IN） → dissection（DS） → hemostasis（HE） → irrigation（IR） → closure（CL） → dressing（DR）。工程の列はこの順 |

## <a id="s1"></a>1. 3 種の注釈の規模

### <a id="s1-1"></a>1.1 ファイルごとの件数

| 種類 | ファイル | 注釈のあるフレーム | インスタンス | loss_mask のフレーム |
| --- | --- | ---: | ---: | ---: |
| hand_seg | train | 9,627 | 27,726 | — |
|  | val | 1,515 | 4,918 | — |
|  | test | 4,255 | 13,676 | — |
|  | extra | 4,035 | 10,853 | — |
| tool_seg | train | 9,528 | 30,493 | — |
|  | val | 1,512 | 3,733 | — |
|  | test | 3,927 | 11,574 | — |
|  | extra | 3,532 | 8,337 | — |
| hand_tool_seg | train | 9,356 | 32,408 | 301 |
|  | val | 1,514 | 5,653 | 1 |
|  | test | 4,107 | 14,081 | 158 |
|  | extra | 3,420 | 9,945 | — |

- loss_mask のフレームは、術具 bbox のあるフレームのうち hand_tool_seg の注釈が無いフレームと**全 split で一致**する

### <a id="s1-2"></a>1.2 hand_seg：クラスごとの件数とマスクの大きさ

| クラス | インスタンス | 写るフレーム | 在率 % | マスク面積の中央値 % | 四分位範囲 % | extra のインスタンス |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| 自分の左手 | 14,043 | 13,966 | 90.5 | 7.81 | 5.11–11.95 | 3,035 |
| 自分の右手 | 13,584 | 13,512 | 87.5 | 6.44 | 4.00–10.13 | 2,803 |
| 他者の左手 | 11,033 | 10,026 | 64.9 | 4.42 | 2.73–6.93 | 2,572 |
| 他者の右手 | 7,660 | 6,825 | 44.2 | 3.71 | 2.17–5.78 | 2,443 |

- 母集団 15,437 フレームでの値。面積は画像（1920×1080）に対する % 。手の在否の工程別の表は先行 EDA [§4.2](phase_tool_annotation_stats.md#s4-2)

### <a id="s1-3"></a>1.3 tool_seg：31 クラスの件数とマスクの大きさ

| クラス | 群 | インスタンス | 写るフレーム | 出現動画 | マスク面積の中央値 % | extra のインスタンス | 術具 bbox の box |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Tweezers | 陰性対照 | 10,012 | 9,086 | 15/15 | 0.89 | 2,054 | 10,012 |
| Gauze | 陰性対照 | 6,695 | 5,858 | 15/15 | 1.95 | 1,175 | 6,695 |
| Forceps | — | 6,063 | 3,219 | 13/15 | 0.55 | 1,015 | 6,063 |
| Needle Holders | — | 4,829 | 4,754 | 12/15 | 0.89 | 478 | 4,829 |
| Suction Cannula | 陰性対照 | 4,411 | 4,399 | 10/15 | 0.45 | 949 | 4,411 |
| Scissors | — | 2,736 | 2,733 | 15/15 | 0.63 | 175 | 2,736 |
| Retractor | — | 2,404 | 1,420 | 7/15 | 0.40 | 1,428 | 2,404 |
| Electric Cautery | — | 1,667 | 1,659 | 8/15 | 1.89 | 56 | 1,667 |
| Hook | — | 1,349 | 1,037 | 6/15 | 0.28 | 123 | 1,349 |
| Scalpel | 標的 | 1,066 | 1,065 | 15/15 | 1.08 | 59 | 1,066 |
| Raspatory | 標的 | 814 | 809 | 8/15 | 0.87 | 127 | 814 |
| Bipolar Forceps | 標的 | 696 | 694 | 12/15 | 1.61 | 17 | 696 |
| Syringe | 標的 | 581 | 564 | 15/15 | 0.77 | 6 | 581 |
| Skewer | 標的 | 344 | 343 | 9/15 | 0.45 | 0 | 344 |
| Mouth Gag | 陰性対照 | 0 | 0 | 0/15 | — | 0 | 5,985 |
| Nasogastric Tube | （Tool15 外） | 1,485 | 385 | 1/15 | 0.33 | 187 | — |
| BiClamp | （Tool15 外） | 289 | 289 | 1/15 | 1.71 | 8 | — |
| Petri Dish | （Tool15 外） | 102 | 102 | 1/15 | 4.74 | 48 | — |
| Cup | （Tool15 外） | 88 | 87 | 7/15 | 1.69 | 6 | — |
| Suction Tube | （Tool15 外） | 70 | 69 | 3/15 | 0.88 | 0 | — |
| Kidney Dish | （Tool15 外） | 67 | 67 | 2/15 | 5.78 | 0 | — |
| Pen | （Tool15 外） | 21 | 21 | 1/15 | 1.81 | 0 | — |
| Spoon | （Tool15 外） | 11 | 11 | 1/15 | 0.96 | 16 | — |
| Chisel | （Tool15 外） | 0 | 0 | 0/15 | — | 53 | — |
| Drill | （Tool15 外） | 0 | 0 | 0/15 | — | 75 | — |
| Hammer | （Tool15 外） | 0 | 0 | 0/15 | — | 28 | — |
| Malleable Retractor | （Tool15 外） | 0 | 0 | 0/15 | — | 121 | — |
| Ruler | （Tool15 外） | 0 | 0 | 0/15 | — | 14 | — |
| Screwdriver | （Tool15 外） | 0 | 0 | 0/15 | — | 79 | — |
| Suture, Suture Needle | （Tool15 外） | 0 | 0 | 0/15 | — | 0 | — |
| Trephine | （Tool15 外） | 0 | 0 | 0/15 | — | 40 | — |

- 上は Tool15 の 15 クラス（box の多い順でなく tool_seg のインスタンスの多い順）、下は Tool15 外の 16 クラス
- **注釈が 1 件も無いクラス**: Mouth Gag、Suture, Suture Needle。Mouth Gag は術具 bbox では 5,985 box ある（陰性対照群の 1 つが tool_seg には無い）

### <a id="s1-4"></a>1.4 hand_tool_seg：把持術具の数

| 1 フレームの把持術具の数 | フレーム | % |
| --- | ---: | ---: |
| 0 | 350 | 2.3 |
| 1 | 4,740 | 31.6 |
| 2 | 9,886 | 66.0 |
| 3 | 1 | <0.1 |

- 把持術具 24,515 個の内訳: 左 11,467、右 11,587、両手 1,461。同じ側で 2 つ以上を持つフレーム: 右 1。同じ側の自分の手が 2 つあるフレーム: 149
- 分母は hand_tool_seg の注釈がある 14,977 フレーム

## <a id="s2"></a>2. tool_seg と術具 bbox の対応

母集団: 術具 bbox のある 15,437 フレーム。tool_seg の各インスタンスの外接矩形と術具 bbox の box を、同じクラスどうし IoU の大きい順に 1 対 1 で対応づける（IoU ≥ 0.5）

### <a id="s2-1"></a>2.1 クラスごとの対応

| クラス | 群 | 術具 bbox の box | tool_seg のインスタンス | bbox のあるフレーム | tool_seg のあるフレーム | 対応のついた組 | box のうち対応あり % | 対応の IoU の中央値 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tweezers | 陰性対照 | 10,012 | 10,012 | 9,086 | 9,086 | 9,838 | 98.3 | 0.886 |
| Gauze | 陰性対照 | 6,695 | 6,695 | 5,858 | 5,858 | 6,645 | 99.3 | 0.889 |
| Forceps | — | 6,063 | 6,063 | 3,219 | 3,219 | 5,865 | 96.7 | 0.828 |
| Mouth Gag | 陰性対照 | 5,985 | 0 | 5,982 | 0 | 0 | 0 | — |
| Needle Holders | — | 4,829 | 4,829 | 4,754 | 4,754 | 4,747 | 98.3 | 0.900 |
| Suction Cannula | 陰性対照 | 4,411 | 4,411 | 4,399 | 4,399 | 4,302 | 97.5 | 0.906 |
| Scissors | — | 2,736 | 2,736 | 2,733 | 2,733 | 2,631 | 96.2 | 0.876 |
| Retractor | — | 2,404 | 2,404 | 1,420 | 1,420 | 2,357 | 98.0 | 0.879 |
| Electric Cautery | — | 1,667 | 1,667 | 1,659 | 1,659 | 1,662 | 99.7 | 0.925 |
| Hook | — | 1,349 | 1,349 | 1,037 | 1,037 | 1,310 | 97.1 | 0.899 |
| Scalpel | 標的 | 1,066 | 1,066 | 1,065 | 1,065 | 1,039 | 97.5 | 0.908 |
| Raspatory | 標的 | 814 | 814 | 809 | 809 | 773 | 95.0 | 0.860 |
| Bipolar Forceps | 標的 | 696 | 696 | 694 | 694 | 684 | 98.3 | 0.916 |
| Syringe | 標的 | 581 | 581 | 564 | 564 | 563 | 96.9 | 0.831 |
| Skewer | 標的 | 344 | 344 | 343 | 343 | 333 | 96.8 | 0.946 |
| **計（Mouth Gag を除く）** |  | 43,667 | 43,667 |  |  | 42,749 | 97.9 | 0.884 |

- **Mouth Gag 以外の 14 クラスは、インスタンス数も写るフレームも術具 bbox と同じ**（tool_seg の Tool15 部分は術具 bbox の box ごとにマスクを付けたものと読める）。Mouth Gag だけが tool_seg に 1 件も無い
- 件数が同じでも IoU ≥ 0.5 で対応がつかない box がある。対応の IoU の中央値も 1 にならず、tool_seg の外接矩形は元の box とは一致しない

### <a id="s2-2"></a>2.2 tool_seg の未注釈フレーム

<details><summary>動画ごとの tool_seg 未注釈フレーム（470 フレーム）</summary>

| 動画 | フレーム | tool_seg 未注釈 | % | うち術具 bbox の Mouth Gag が写る |
| --- | ---: | ---: | ---: | ---: |
| 01 | 913 | 0 | 0 | 0 |
| 02 | 461 | 0 | 0 | 0 |
| 03 | 1,089 | 23 | 2.1 | 23 |
| 04 | 1,329 | 51 | 3.8 | 0 |
| 05 | 1,225 | 261 | 21.3 | 259 |
| 06 | 1,379 | 26 | 1.9 | 15 |
| 07 | 1,711 | 26 | 1.5 | 0 |
| 08 | 1,400 | 66 | 4.7 | 66 |
| 09 | 518 | 0 | 0 | 0 |
| 10 | 997 | 3 | 0.3 | 3 |
| 11 | 754 | 2 | 0.3 | 0 |
| 12 | 609 | 1 | 0.2 | 0 |
| 13 | 822 | 3 | 0.4 | 0 |
| 14 | 1,810 | 4 | 0.2 | 0 |
| 15 | 420 | 4 | 1.0 | 0 |
| **計** | 15,437 | 470 | 3.0 | 366 |

</details>

- tool_seg が未注釈の 470 フレームは、術具 bbox の術具が **Mouth Gag だけ**のフレーム 366 と、術具 bbox が 0 個のフレーム 104 でできている。Mouth Gag は tool_seg に無いクラスなので、注釈が漏れたのではなく tool_seg に描くものが無いフレームである
- 術具 bbox が Mouth Gag だけか 0 個のフレームは 580 あり、残りの 110 には Tool15 外のクラスだけが tool_seg にある
- 動画 05 の未注釈が多いのは、Mouth Gag だけが写るフレームが多いため（表の右端の列）

## <a id="s3"></a>3. 工程との関係

母集団: 術具 bbox のある 15,437 フレーム（工程ラベルは全フレームにある）。工程の列は参照順

### <a id="s3-1"></a>3.1 工程ごとの被覆

工程 CSV の行に対する割合 %

| 工程 | 工程 CSV の行 | 術具 bbox のフレーム | 術具 bbox % | hand_seg % | tool_seg % | hand_tool_seg % | 3 種すべて % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| disinfection† | 125 | 11 | 8.8 | 8.8 | 0 | 8.0 | 0 |
| design | 646 | 378 | 58.5 | 58.5 | 57.3 | 58.5 | 57.3 |
| anesthesia | 555 | 499 | 89.9 | 89.7 | 88.5 | 83.8 | 82.3 |
| incision | 1,170 | 1,096 | 93.7 | 93.7 | 92.9 | 90.0 | 89.6 |
| dissection | 5,799 | 5,440 | 93.8 | 93.8 | 92.7 | 92.3 | 91.4 |
| hemostasis | 1,169 | 1,121 | 95.9 | 95.8 | 95.2 | 94.7 | 94.2 |
| irrigation† | 217 | 177 | 81.6 | 81.6 | 79.3 | 74.7 | 72.4 |
| closure | 7,231 | 6,596 | 91.2 | 90.8 | 86.7 | 87.7 | 83.7 |
| dressing† | 321 | 119 | 37.1 | 35.5 | 27.4 | 35.2 | 26.8 |
| **計** | 17,233 | 15,437 | 89.6 | 89.3 | 86.9 | 86.9 | 84.5 |

- HTS の被覆は術具 bbox の被覆を超えない（HTS は術具 bbox のあるフレームにしか付かない。[§0.2](#s0-2)）。被覆の低い工程は disinfection（術具 bbox 8.8%）、dressing（術具 bbox 37.1%）、design（術具 bbox 58.5%）
- 術具 bbox のあるフレームを分母にした値は [§3.2](#s3-2)

### <a id="s3-2"></a>3.2 工程ごとの欠け（術具 bbox のあるフレームを分母に）

| 工程 | フレーム | hand_seg 未注釈 | tool_seg 未注釈 | % | hand_tool_seg 未注釈（loss_mask） | % | tool_seg のあるフレームで術具 bbox の box に対応がある % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| disinfection† | 11 | 0 | 11 | 100.0 | 1 | 9.1 | — |
| design | 378 | 0 | 8 | 2.1 | 0 | 0 | 77.0 |
| anesthesia | 499 | 1 | 8 | 1.6 | 34 | 6.8 | 82.1 |
| incision | 1,096 | 0 | 9 | 0.8 | 43 | 3.9 | 88.4 |
| dissection | 5,440 | 2 | 65 | 1.2 | 90 | 1.7 | 90.2 |
| hemostasis | 1,121 | 1 | 8 | 0.7 | 14 | 1.2 | 91.9 |
| irrigation† | 177 | 0 | 5 | 2.8 | 15 | 8.5 | 94.1 |
| closure | 6,596 | 31 | 325 | 4.9 | 257 | 3.9 | 81.6 |
| dressing† | 119 | 5 | 31 | 26.1 | 6 | 5.0 | 56.2 |
| **計** | 15,437 | 40 | 470 | 3.0 | 460 | 3.0 | 86.7 |

- **hand_tool_seg の未注釈（loss_mask）460 フレームは、hand_seg で自分の手が写らないフレームと完全に一致する**。hand_tool_seg は自分の手とその手が持つ術具でできているので、自分の手が写らなければ注釈は作られない
- README（`hand_tool_seg/README.md` §4・§8）はこの欠落を「Mouth Gag / Skewer を含むフレームの構造的な除外」と説明しているが、loss_mask のうち術具 bbox の術具が Mouth Gag・Skewer だけ（または 0 個）のフレームは 65（14.1%）にとどまる。上位の組み合わせ: Mouth Gag 59、Mouth Gag + Suction Cannula 38、Forceps 36、Gauze + Syringe 26
- tool_seg の未注釈（術具 bbox が Mouth Gag だけか 0 個のフレーム、[§2.2](#s2-2)）の割合が高い工程: disinfection 100.0%、dressing 26.1%、closure 4.9%。disinfection の術具 bbox のあるフレームは術具が 0 個
- 右端の列は、tool_seg のあるフレームで、術具 bbox の box（Mouth Gag を含む全クラス）のうち同じクラスの tool_seg インスタンスと対応がつく割合。Mouth Gag の多い工程ほど下がる

### <a id="s3-3"></a>3.3 tool_seg だけにあるクラス × 工程

Tool15 外で母集団に現れる 8 クラス。P(工程 | クラス)（写るフレーム基準、行で 100%）

| クラス | 写るフレーム | 出現動画 | disinfection† | design | anesthesia | incision | dissection | hemostasis | irrigation† | closure | dressing† | 最頻工程での在率 % | 実効工程数 2^H |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Pen | 21 | 1/15 | 0 | 100.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | design 5.7 | 1.00 |
| Cup | 87 | 7/15 | 0 | 97.7 | 0 | 0 | 1.1 | 1.1 | 0 | 0 | 0 | design 23.0 | 1.13 |
| Petri Dish | 102 | 1/15 | 0 | 0 | 0 | 0 | 100.0 | 0 | 0 | 0 | 0 | dissection 1.9 | 1.00 |
| Spoon | 11 | 1/15 | 0 | 0 | 0 | 0 | 100.0 | 0 | 0 | 0 | 0 | dissection 0.2 | 1.00 |
| BiClamp | 289 | 1/15 | 0 | 0 | 0 | 0 | 45.7 | 54.3 | 0 | 0 | 0 | hemostasis 14.1 | 1.99 |
| Kidney Dish | 67 | 2/15 | 0 | 0 | 0 | 0 | 3.0 | 0 | 97.0 | 0 | 0 | irrigation† 37.8 | 1.14 |
| Suction Tube | 69 | 3/15 | 0 | 0 | 0 | 0 | 0 | 0 | 95.7 | 4.3 | 0 | irrigation† 38.4 | 1.20 |
| Nasogastric Tube | 385 | 1/15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0 | 0 | closure 6.1 | 1.00 |

- 最頻工程での在率の分母は、その工程の tool_seg のあるフレーム。実効工程数 = 2 の（P(工程 | クラス) のエントロピー）乗
- 90% 以上が 1 つの工程に集まるクラス: Pen → design、Cup → design、Petri Dish → dissection、Spoon → dissection、Kidney Dish → irrigation、Suction Tube → irrigation、Nasogastric Tube → closure。ただし多くは 1〜3 動画にしか出ない（出現動画の列）
- Tool15 の 14 クラスは写るフレームが術具 bbox と同じ（[§2.1](#s2-1)）なので、P(工程 | 術具) と在率は先行 EDA の [§3.1](phase_tool_annotation_stats.md#s3-1)・[§3.3](phase_tool_annotation_stats.md#s3-3) と同じになる
- Mouth Gag は術具 bbox では design 31.4%、dissection 32.3%、closure 47.0%、dressing 84.1% のフレームに写る（分母は tool_seg のあるフレーム）が、tool_seg には 1 件も無い

### <a id="s3-4"></a>3.4 手のマスクの面積 × 工程

| 工程 | hand_seg のあるフレーム | 手が覆う画素 % の平均 | 同・中央値 | 自分の手 % の平均 | 他者の手 % の平均 |
| --- | ---: | ---: | ---: | ---: | ---: |
| disinfection† | 11 | 4.5 | 3.2 | 4.3 | 0.2 |
| design | 378 | 22.0 | 22.6 | 20.8 | 1.2 |
| anesthesia | 498 | 15.0 | 12.8 | 12.5 | 2.4 |
| incision | 1,096 | 23.1 | 23.0 | 16.7 | 6.4 |
| dissection | 5,438 | 23.6 | 22.8 | 16.4 | 7.2 |
| hemostasis | 1,120 | 22.6 | 22.0 | 15.6 | 7.0 |
| irrigation† | 177 | 15.5 | 15.1 | 7.4 | 8.1 |
| closure | 6,565 | 20.1 | 18.8 | 14.0 | 6.0 |
| dressing† | 114 | 26.1 | 25.3 | 24.5 | 1.6 |
| **全体** | 15,397 | 21.6 | 20.5 | 15.3 | 6.3 |

- 手が覆う画素 = そのフレームの手のマスクの和集合が画像（1920×1080）に占める割合

### <a id="s3-5"></a>3.5 把持 × 工程

分母は hand_tool_seg のあるフレーム（工程ごと。どのフレームにも自分の手が写る）。各列はその状態のフレームの %

| 工程 | フレーム | 何かを持つ | 左手で持つ | 右手で持つ | 両手で持つ | 両手がふさがる | 何も持たない | 把持術具 / フレーム | 右手だけで持つ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| disinfection† | 10 | 0 | 0 | 0 | 0 | 0 | 100.0 | 0.00 | 0 |
| design | 378 | 98.1 | 31.7 | 66.9 | 30.2 | 60.8 | 1.9 | 1.29 | 36.2 |
| anesthesia | 465 | 97.4 | 39.8 | 42.6 | 41.3 | 67.5 | 2.6 | 1.24 | 16.3 |
| incision | 1,053 | 99.6 | 76.4 | 81.1 | 12.1 | 82.0 | 0.4 | 1.70 | 11.2 |
| dissection | 5,350 | 97.6 | 79.0 | 80.4 | 10.1 | 81.9 | 2.4 | 1.69 | 8.5 |
| hemostasis | 1,107 | 98.4 | 79.5 | 78.0 | 11.4 | 81.9 | 1.6 | 1.69 | 7.5 |
| irrigation† | 162 | 86.4 | 45.1 | 53.1 | 20.4 | 52.5 | 13.6 | 1.19 | 21.0 |
| closure | 6,339 | 97.8 | 80.8 | 78.1 | 4.9 | 70.9 | 2.2 | 1.64 | 12.1 |
| dressing† | 113 | 92.9 | 51.3 | 72.6 | 15.0 | 61.1 | 7.1 | 1.39 | 26.5 |
| **全体** | 14,977 | 97.7 | 76.6 | 77.4 | 9.8 | 75.8 | 2.3 | 1.64 | 11.3 |

- 両手がふさがる = 左手と右手がそれぞれ何かを持つ、または両手で 1 つを持つ。右手だけで持つ = 右手で持ち、左手・両手では持たない
- 「持つ」は box の重なりから決まった量（[§0.3](#s0-3)）

### <a id="s3-6"></a>3.6 工程ごとに持たれている術具のクラス

工程ごとの上位 3 クラス。数字はその工程の hand_tool_seg のあるフレームのうち、その側でそのクラスを持つ割合 %（1 フレームで同じ側が 2 つ持つことがあるので延べ数）

| 工程 | フレーム | 左手 | 右手 | 両手 |
| --- | ---: | --- | --- | --- |
| disinfection† | 10 | — | — | — |
| design | 378 | Mouth Gag 16.1、Tweezers 7.9、Gauze 5.6 | Skewer 56.3、Pen 5.6、Mouth Gag 3.4 | Skewer 24.6、Mouth Gag 5.6 |
| anesthesia | 465 | Gauze 19.8、Mouth Gag 16.8、Syringe 2.4 | Syringe 38.3、Mouth Gag 3.7、Tweezers 0.2 | Syringe 34.0、Mouth Gag 7.1、Gauze 0.2 |
| incision | 1,053 | Tweezers 30.5、Gauze 24.6、Mouth Gag 9.6 | Scalpel 70.1、Mouth Gag 5.8、Suction Cannula 3.8 | Scalpel 8.5、Mouth Gag 1.5、Suction Cannula 1.0 |
| dissection | 5,350 | Tweezers 39.1、Gauze 13.0、Suction Cannula 12.1 | Scissors 31.3、Electric Cautery 20.1、Raspatory 9.5 | Electric Cautery 4.5、Forceps 2.1、BiClamp 0.9 |
| hemostasis | 1,107 | Tweezers 32.4、Gauze 21.3、Suction Cannula 9.0 | Bipolar Forceps 54.8、Electric Cautery 10.4、BiClamp 6.8 | BiClamp 6.5、Electric Cautery 3.7、Gauze 0.5 |
| irrigation† | 162 | Gauze 16.7、Kidney Dish 12.3、Suction Tube 8.0 | Syringe 21.0、Gauze 10.5、Suction Cannula 8.0 | Syringe 7.4、Kidney Dish 6.8、Gauze 3.7 |
| closure | 6,339 | Tweezers 57.7、Mouth Gag 10.4、Suture, Suture Needle 4.1 | Needle Holders 55.2、Suture, Suture Needle 8.9、Gauze 2.8 | Mouth Gag 1.5、Suture, Suture Needle 1.4、Needle Holders 1.3 |
| dressing† | 113 | Mouth Gag 38.9、Tweezers 8.8、Gauze 2.7 | Tweezers 50.4、Mouth Gag 8.8、Scissors 5.3 | Mouth Gag 10.6、Gauze 2.7、Suction Cannula 0.9 |

### <a id="s3-7"></a>3.7 術具のクラスごとの把持

左の 4 列は hand_tool_seg のある全フレーム、「写るフレーム」と「把持率」は hand_tool_seg と tool_seg の両方があるフレーム（14,570）で数える

| クラス | 群 | 把持の件数 | 左 % | 右 % | 両手 % | 写るフレーム（tool_seg） | 把持率 % | 把持のある動画 | 主に左 / 右 / 両手で持つ動画の数 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Tweezers | 陰性対照 | 6,742 | 96.0 | 3.7 | 0.4 | 8,950 | 74.6 | 15 | 15 / 0 / 0 |
| Needle Holders | — | 3,658 | 2.0 | 95.8 | 2.2 | 4,631 | 78.8 | 12 | 2 / 10 / 0 |
| Gauze | 陰性対照 | 1,963 | 73.1 | 23.8 | 3.1 | 5,680 | 34.3 | 15 | 8 / 6 / 1 |
| Mouth Gag | 陰性対照 | 1,913 | 61.5 | 28.2 | 10.4 | 0 | — | 5 | 5 / 0 / 0 |
| Scissors | — | 1,812 | 1.4 | 97.3 | 1.3 | 2,724 | 66.5 | 15 | 1 / 14 / 0 |
| Electric Cautery | — | 1,499 | 1.6 | 79.5 | 18.9 | 1,641 | 91.3 | 6 | 0 / 6 / 0 |
| Suction Cannula | 陰性対照 | 1,286 | 69.8 | 25.8 | 4.4 | 4,259 | 30.1 | 10 | 7 / 3 / 0 |
| Forceps | — | 1,067 | 54.1 | 34.9 | 11.1 | 3,097 | 33.4 | 12 | 9 / 3 / 0 |
| Suture, Suture Needle | （Tool15 外） | 915 | 28.3 | 62.1 | 9.6 | 0 | — | 10 | 7 / 2 / 1 |
| Scalpel | 標的 | 841 | 0.7 | 88.7 | 10.6 | 1,034 | 81.3 | 14 | 0 / 13 / 1 |
| Bipolar Forceps | 標的 | 620 | 0.2 | 99.0 | 0.8 | 686 | 90.4 | 11 | 0 / 11 / 0 |
| Raspatory | 標的 | 552 | 1.8 | 92.0 | 6.2 | 804 | 68.4 | 6 | 0 / 6 / 0 |
| Syringe | 標的 | 394 | 3.0 | 53.8 | 43.1 | 532 | 74.1 | 14 | 1 / 9 / 4 |
| Skewer | 標的 | 307 | 0.3 | 69.4 | 30.3 | 343 | 89.5 | 9 | 0 / 8 / 1 |
| Retractor | — | 283 | 82.3 | 17.0 | 0.7 | 1,410 | 18.7 | 7 | 6 / 1 / 0 |
| BiClamp | （Tool15 外） | 275 | 2.5 | 54.5 | 42.9 | 289 | 95.2 | 1 | 0 / 1 / 0 |
| 不明 |  | 147 | 80.3 | 16.3 | 3.4 | — | — | 9 | 8 / 1 / 0 |
| Hook | — | 94 | 63.8 | 36.2 | 0 | 1,002 | 9.4 | 6 | 4 / 2 / 0 |
| Kidney Dish | （Tool15 外） | 43 | 48.8 | 25.6 | 25.6 | 66 | 65.2 | 2 | 2 / 0 / 0 |
| Nasogastric Tube | （Tool15 外） | 30 | 86.7 | 13.3 | 0 | 380 | 7.9 | 1 | 1 / 0 / 0 |
| Pen | （Tool15 外） | 21 | 0 | 100.0 | 0 | 21 | 100.0 | 1 | 0 / 1 / 0 |
| Petri Dish | （Tool15 外） | 18 | 88.9 | 5.6 | 5.6 | 102 | 17.6 | 1 | 1 / 0 / 0 |
| Suction Tube | （Tool15 外） | 18 | 72.2 | 22.2 | 5.6 | 65 | 27.7 | 3 | 1 / 2 / 0 |
| Spoon | （Tool15 外） | 11 | 0 | 90.9 | 9.1 | 11 | 100.0 | 1 | 0 / 1 / 0 |
| Cup | （Tool15 外） | 4 | 25.0 | 75.0 | 0 | 87 | 4.6 | 3 | 1 / 2 / 0 |
| Caliper | （Tool15 外） | 1 | 100.0 | 0 | 0 | 0 | — | 1 | 1 / 0 / 0 |
| Bone Curette | （Tool15 外） | 1 | 100.0 | 0 | 0 | 0 | — | 1 | 1 / 0 / 0 |

- 把持率 = そのクラスが tool_seg で写るフレームのうち、同じフレームでそのクラスが持たれている割合
- 主に〜で持つ動画の数 = 動画ごとに、そのクラスの把持の件数が最も多い側を数えたもの
- Mouth Gag と Suture, Suture Needle は tool_seg に無いので、写るフレームと把持率は測れない（—）。把持の件数は §0.3 の 4 段のうち術具 bbox・元の注釈との対応による

<details><summary>把持率 × 工程（把持の多い上位 15 クラス。· はその工程で写らない）</summary>

| クラス | disinfection† | design | anesthesia | incision | dissection | hemostasis | irrigation† | closure | dressing† |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tweezers | · | 81.6 | 11.8 | 70.8 | 70.6 | 47.3 | · | 82.1 | 95.8 |
| Needle Holders | · | · | · | · | 50.0 | · | · | 78.8 | · |
| Gauze | · | 59.0 | 47.5 | 59.2 | 35.5 | 34.1 | 55.6 | 19.9 | 100.0 |
| Mouth Gag | · | · | · | · | · | · | · | · | · |
| Scissors | · | · | · | 0 | 74.5 | 9.7 | · | 25.4 | 100.0 |
| Electric Cautery | · | · | · | 100.0 | 92.0 | 86.8 | 0 | · | · |
| Suction Cannula | · | · | 30.0 | 37.9 | 29.5 | 21.4 | 37.8 | 34.3 | 85.7 |
| Forceps | · | 46.2 | · | 28.1 | 40.7 | 12.1 | 0 | 28.0 | · |
| Suture, Suture Needle | · | · | · | · | · | · | · | · | · |
| Scalpel | · | · | · | 82.7 | 26.3 | 0 | · | 66.7 | · |
| Bipolar Forceps | · | · | · | · | 77.8 | 91.1 | · | 0 | · |
| Raspatory | · | · | · | · | 83.3 | 0 | · | 2.1 | · |
| Syringe | · | · | 78.2 | · | · | · | 54.0 | 0 | · |
| Skewer | · | 89.8 | · | 0 | · | · | · | · | · |
| Retractor | · | · | · | 2.3 | 15.9 | 42.5 | 34.2 | 50.0 | · |

</details>

### <a id="s3-8"></a>3.8 工程との情報量（注釈のあいだの参考値）

母集団: hand_tool_seg と tool_seg の両方があるフレーム 14,570。モデルの結果ではなく注釈のあいだの関係である。把持は手と術具の注釈から導かれた量（§0.3）なので、術具の集合と独立な情報ではない

| 変数 | 値の種類 | I(工程; 変数) [bit] | I / H(工程) % | 動画一つ抜きの frame accuracy % |
| --- | ---: | ---: | ---: | ---: |
| 自分・他者の手の在否（hand_seg、4 クラスの有無） | 12 | 0.118 | 5.8 | 43.7 |
| 把持の状態（左・右・両手のそれぞれで持つか） | 5 | 0.071 | 3.5 | 32.1 |
| 持たれている術具のクラスの集合（側を区別しない） | 135 | 1.490 | 73.9 | 80.3 |
| 持たれている術具の（側, クラス）の集合 | 229 | 1.545 | 76.6 | 81.0 |
| 写っている術具の集合（術具 bbox、Tool15） | 363 | 1.735 | 86.0 | 75.6 |
| 写っている術具の集合（tool_seg、31 クラス） | 378 | 1.755 | 87.0 | 76.4 |
| 術具 bbox の集合 + 把持の（側, クラス）の集合 | 1,708 | 1.872 | 92.8 | 68.4 |
| （基準）常に最多工程（closure） | 1 | 0 | 0 | 41.5 |

- H(工程) = 2.017 bit。I は平滑化なしの plug-in 推定で、値の種類が多い変数ほど上振れする。種類数の違う変数どうしは右端の列で比べる
- 動画一つ抜き = 1 動画を除いた 14 動画で「変数の値ごとの最多工程」を数え、除いた動画に当てはめる（未見の値は最多工程で埋める）。先行 EDA [§3.10](phase_tool_annotation_stats.md#s3-10) と同じ規則

### <a id="s3-9"></a>3.9 工程の切り替わりと把持の変化

| 隣接フレームの対 | 対の数 | 把持の（側, クラス）集合が変わる % | 術具 bbox の集合が変わる % |
| --- | ---: | ---: | ---: |
| 工程が変わる | 190 | 92.6 | 92.6 |
| 工程が同じ | 13,896 | 40.1 | 29.3 |

- 隣接 = 同じクリップの工程 CSV で連続する 2 行が、どちらも hand_tool_seg を持つ対

工程の切り替わりの多い順（上位 10）

| 工程の切り替わり | 対の数 | 把持が変わる % | 持ち始める（側:クラス、回数） | 手放す（側:クラス、回数） |
| --- | ---: | ---: | --- | --- |
| hemostasis → dissection | 39 | 94.9 | 右:Scissors(17)、右:Electric Cautery(6)、左:Tweezers(6) | 右:Bipolar Forceps(23)、左:Gauze(5)、両手:Electric Cautery(4) |
| dissection → hemostasis | 38 | 81.6 | 右:Bipolar Forceps(15)、左:Gauze(4)、左:Suction Cannula(4) | 右:Scissors(17)、左:Tweezers(5)、右:Electric Cautery(4) |
| incision → dissection | 28 | 100.0 | 右:Scissors(7)、右:Electric Cautery(6)、左:Tweezers(4) | 右:Scalpel(21)、両手:Scalpel(4)、左:Gauze(3) |
| dissection → incision | 21 | 90.5 | 右:Scalpel(10)、両手:Scalpel(2)、左:Tweezers(2) | 右:Scissors(5)、右:Electric Cautery(4)、右:Raspatory(4) |
| dissection → closure | 8 | 87.5 | 右:Needle Holders(5)、右:Suture, Suture Needle(1)、左:Tweezers(1) | 右:Electric Cautery(2)、右:Scissors(2)、右:Mouth Gag(1) |
| hemostasis → closure | 7 | 85.7 | 右:Needle Holders(5)、左:Tweezers(1) | 右:Bipolar Forceps(5)、右:Mouth Gag(1)、左:Mouth Gag(1) |
| closure → dissection | 7 | 100.0 | 右:Scissors(5)、左:Tweezers(3) | 右:Needle Holders(2)、右:Scissors(1)、右:Suture, Suture Needle(1) |
| closure → incision | 6 | 100.0 | 右:Scalpel(4)、左:Forceps(1) | 両手:Scissors(1)、右:Tweezers(1)、左:Suture, Suture Needle(1) |
| anesthesia → incision | 5 | 100.0 | 右:Scalpel(2)、左:Gauze(2)、両手:Gauze(1) | 右:Syringe(2)、左:Gauze(2)、両手:Gauze(1) |
| design → anesthesia | 4 | 100.0 | 両手:Syringe(2)、右:Syringe(1) | 右:Skewer(4) |

### <a id="s3-10"></a>3.10 手術の進行度と把持

| 進行度 | フレーム | 何かを持つ % | 左手 % | 右手 % | 両手 % | 右手の上位 2（%） | 左手の上位 2（%） |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 0–20% | 2,802 | 97.6 | 71.2 | 76.6 | 13.0 | Scissors 18.9、Scalpel 10.1 | Tweezers 24.1、Gauze 16.1 |
| 20–40% | 3,148 | 98.7 | 76.7 | 76.6 | 11.7 | Scissors 19.5、Needle Holders 10.6 | Tweezers 43.6、Gauze 9.4 |
| 40–60% | 3,119 | 96.4 | 77.7 | 77.7 | 8.5 | Needle Holders 24.2、Scissors 13.6 | Tweezers 45.8、Gauze 9.1 |
| 60–80% | 3,088 | 98.1 | 79.5 | 79.2 | 8.1 | Needle Holders 39.0、Suture, Suture Needle 6.6 | Tweezers 48.3、Gauze 8.8 |
| 80–100% | 2,820 | 97.5 | 77.2 | 76.5 | 7.7 | Needle Holders 42.3、Electric Cautery 10.2 | Tweezers 53.3、Mouth Gag 7.7 |

- 進行度 = 動画ごとに工程 CSV の全行を時系列に並べた順位を 0〜1 に正規化した値（先行 EDA と同じ）。分母は hand_tool_seg のあるフレーム

### <a id="s3-11"></a>3.11 術具のマスクと手のマスクの重なり × 工程

| 工程 | tool_seg のインスタンス | 手と重なる % | 自分の手と重なる % | 他者の手と重なる % | 把持術具である % | 把持術具のうち自分の手と重なる % | 自分の手と重なるが把持術具でない % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| disinfection† | 0 | — | — | — | — | — | — |
| design | 561 | 37.1 | 29.4 | 7.7 | 69.7 | 37.3 | 3.4 |
| anesthesia | 756 | 27.5 | 13.6 | 13.9 | 59.0 | 21.7 | 0.8 |
| incision | 3,013 | 24.3 | 15.3 | 9.2 | 53.0 | 27.4 | 0.8 |
| dissection | 20,268 | 22.2 | 15.1 | 7.2 | 42.6 | 33.1 | 1.1 |
| hemostasis | 4,226 | 20.1 | 12.4 | 7.8 | 42.0 | 26.5 | 1.3 |
| irrigation† | 528 | 33.9 | 10.6 | 24.1 | 36.0 | 24.2 | 1.9 |
| closure | 16,353 | 23.0 | 17.8 | 5.3 | 51.4 | 32.8 | 1.0 |
| dressing† | 95 | 14.7 | 14.7 | 0 | 93.7 | 15.7 | 0 |
| **全体** | 45,800 | 22.8 | 16.0 | 7.0 | 47.0 | 31.7 | 1.1 |

- 重なる = 術具のマスクと手（hand_seg）のマスクが 1 画素以上重なる。把持術具である = hand_tool_seg の把持術具のマスクと RLE まで同一
- マスクは物体ごとに描かれるので、手と術具が接していても重ならないことがある（[§0.3](#s0-3)）。重なりは接触の下限の目安で、box で数えた手と術具の近さは先行 EDA [§4.3](phase_tool_annotation_stats.md#s4-3)

## <a id="sA"></a>付録 A：既存の HTS 分析との対応

既存の HTS の監査は「どのフレームに注釈があるか」を主に扱っている。本書はそれを正本（`data/annotations/egosurgery_hts/`）で数え直し、注釈の中身と工程の関係を加えた

| 既存の分析 | 既存の値 | 本書の値 | 備考 |
| --- | --- | --- | --- |
| `egosurgery_hts/*/build_report.md`（split ごとの件数） | §1.1 の各行 | §1.1 | 同じファイルを数えている |
| `experiments/analysis/hts_coverage_2026-07-30/REPORT.md` 結論 2（術具 bbox に対する被覆） | hand 15,397 / tool 14,967 / hand-tool 14,977 | 15,397 / 14,967 / 14,977 | §0.2 |
| 同 結論 3（工程に対する真の欠落） | 1,796 | 1,796 | §0.2。術具 bbox の無い工程 CSV の行で、HTS の注釈も無い |
| 同 「3 タスク同時学習に使えるフレーム」（術具 bbox 内） | 14,570 | 14,570 | §0.2 |
| 同 HTS 対象フレーム | 19,560 | 19,496 | 既存値は raw の `json_per_video` が列挙する画像。うち 64 枚は 3 種とも注釈が 0 件（2026-10-21 に raw の json_per_video で確認。本スクリプトでは数えない）。正本は注釈のある画像だけを載せるので、本書の値は注釈のあるフレームの和集合 |
| `hand_tool_seg/README.md` の Two Hands Tool | train 952 / val 176 / test 333 / extra 560 | train 952 / val 176 / test 333 / extra 560 | §1.4 |
| `experiments/analysis/hts_raw_provenance_2026-07-29/REPORT.md` C6（把持 ∧ 工程の共存） | 9,106 | 14,977 | 9,106 は `04_handtool/coco_splits_5cls` の画像数（5,668 + 2,094 + 1,344）。この版は val と test が入れ替わり、動画 03・14 が抜けている（hts_coverage_2026-07-30 結論 5）。正本の hand_tool_seg では術具 bbox のあるフレームすべてに工程があるので、注釈のあるフレーム数がそのまま共存数になる |
| 同 C4・Task3（SAM 由来） | マスクは box からの SAM。把持 = 手のセグメンテーションと IoU 最大の術具 | box の IoU 最大と 97.4%、マスクの IoU 最大と 30.9% 一致 | §0.3。マスクの IoU では再現しない |
| `hand_tool_seg/README.md` §4・§8（loss_mask の理由） | Mouth Gag / Skewer による構造的な除外 | 自分の手が写らないフレームと完全に一致。Mouth Gag・Skewer だけのフレームは 14.1% | §3.2 |

## <a id="sB"></a>付録 B：再現

```bash
.venv/bin/python docs/analysis_scripts/hts_phase_tool_annotation_stats.py
```

- 読み取り専用で、`data/` には書き込まない。pycocotools で RLE のまま面積・重なりを計算する。10 秒ほどで終わる
- 引数で出力先を変えられる

