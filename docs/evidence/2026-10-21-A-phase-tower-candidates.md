# 証拠地図 A — 一人称の開放手術の online 工程認識で、工程塔の候補（時間モデル・事前学習・基盤モデル）をどう選ぶか

**版:** v2（下書き。2026-10-21 に地図 A の作り直しの会話が作成し、2026-10-22 に A2 の補足の報告〔A2s〕の行を足した。旧地図 A〔v1、2026-09-16、docs/evidence/2026-09-16-A-phase-tower-candidates.md〕の 15 行を移し、A2・A3 の報告六件の行を足した）
**種類:** 探索の地図
**状態:** 書誌の機械照合は未実施（作成した環境から照合先に届かなかったため。ID の抽出〔verify_evidence_ids.py --extract-only〕と様式の検査〔check_evidence_map.py〕だけを通した）。数値の原典確認は未実施。旧地図 A から移した 15 行は 2026-09-16 に Crossref と arXiv API で「実在・書誌一致」（旧地図の記載）。報告者の解釈と提案は地図に載せていない（§0.2）
**元の報告:**
- A2 の報告（ChatGPT の deep research。エンジンは利用者の記載）「A2-deep-research-report.md」（利用者の手元の名前は「A2-deep-research-report .md」。repo では名前の中の半角スペースを除く案）、68,253 バイト、828 行、sha256 6edb3e0773344f02bb4cfd3dacf966bd49d3a042b9d853b43addcbf37e2d7558。出所の記号は A2g
- A2 の報告（Claude の調査。同上）「A2-research_claude.md」、35,635 バイト、615 行、sha256 f2d829ba68f84c4e2097488aee1358f0faa46d07c4155b751771f9710b03ed3a。記号は A2c
- A2 の追加の問い (9)(10) の報告（Claude の調査。同上）「A2-research-follow_claude.md」、51,009 バイト、478 行、sha256 f777bf38992123f82fc88598de015d5dfac1d582d167c346ad49c040e9febc62。記号は A2f
- A2 の補足の報告（問い (9)(10) だけの依頼。ChatGPT の deep research。同上）「A2-supplement-deep-research-report.md」（利用者の手元の名前は「A2_supplimental_deep-research-report.md」。repo では改めた名前で置く。利用者の決定 2026-10-22）、86,003 バイト、726 行、sha256 61c269b33b5f8e8c4aa3d29724a2db3cbcfe8f5c51a11f7ae4704728c0a54535。記号は A2s
- A3 の報告（ChatGPT の deep research。同上）「A3-deep-research-report.md」、71,331 バイト、486 行、sha256 473ab3547fc772470807d1f7d88afdad49fab06c6be1013248bdf914c7723d53。記号は A3g
- A3 の報告（Claude の調査。同上）「A3-research_claude.md」、26,201 バイト、150 行、sha256 632a70011c4119fd526b80a6a833db96bd31cc52ff8a04544dddaeda35ca4446。記号は A3c
- 旧地図 A（v1）の 15 行。旧地図の出所は契約 T-2026-09-16-evidence-map-ab の SPEC の付録 A で、その元は ChatGPT の deep research の報告「A1」（A-chatgpt.md、42,307 バイト、99 行、sha256 2fd5e851851ca78f6df2bd5b9728a1f2c3e341066e0ff8ee587c06256290d0ca。利用者が 2026-10-21 に見つけた。旧地図の 15 行の元の行は A1 L21–L28、L38–L40、L52–L55）。出所の記号は「旧 A.1 の n 行目」（n は旧地図の表の行の順）と「A1 L」。v1 のファイルは置き換えずに repo に残し、表題の直後に v1 と後継を明記する（利用者の決定 2026-10-21。書き込みは配置と照合の契約で行う）

**検索日:** A2g は 2026-10-19（Asia/Tokyo）、A2c は 2026-10-08、A2f は 2026-10-21、A2s は 2026-10-21、A3g は 2026-10-05（日本時間）、A3c は 2026-10-08（いずれも報告の記載）。A1 は報告に検索日の記載が無い（旧地図の照合日は 2026-09-16）

---

## 0. この地図の読み方

### 0.1 問い

一人称視点の開放手術映像（EgoSurgery。21 本、0.5 fps、工程 9 種）で、online（過去のみ）の工程認識の工程塔を作るとき、時間モデル（A2）と、自己教師あり事前学習・手術基盤モデル（A3）の候補をどう選ぶか。現在の工程塔は、fine-tune した ResNet-50 の特徴に因果的な多段の時間畳み込み（TeCNO 型）を載せたもの（依頼文の背景）。

**A2（時間モデル）の問い**（報告の「問い (n)」「Q n」はこの番号）:

- (1) online（過去のみ）の工程認識・行動分割に使われる時間モデルの系統と現役度
- (2) 各系統が少数の動画（数十本以下）で効いたか・効かなかったか
- (3) 時間モデルの差とフレームごとの表現（backbone）の差の、どちらが性能を決めるかを切り分けた研究
- (4) EgoSurgery-Phase と開放手術の工程認識のすべての報告値（手法、指標、分割、online か）
- (5) 一人称の非手術映像の online の手順認識・行動分割で何が効いているか
- (6) 損失の工夫（平滑化、境界、クラスの不均衡）で効かなかった報告
- (7) offline の手法を online に直したときの性能の落ち方
- (8) 報告値が推論の規約、境界の緩和、数値の出所（原論文か再実装か）でどれだけ変わるか
- (9) 時間モデルの学習データが途中に欠けのある区間の列（注釈のある区間だけが残り、区間の境でフレームの連番が振り直される）のとき、区間の境を越えて文脈を引くか、区間ごとに状態を初期化するか。影響を測った研究
- (10) 同じ処方を別の計算機（GPU の種類、数値精度、ライブラリの版）で学習したときの値の散らばりと、seed 間の散らばりとの比較。手術映像・行動分割の報告を優先

**A3（事前学習・基盤モデル）の問い:**

- (1) 対象データが少ないとき、対象データ自身での自己教師あり事前学習は、一般の重み（ImageNet、Kinetics、DINO 系）からの fine-tune と比べてどれだけ効くか。設定への敏感さも含めて
- (2) マスクの選び方に事前知識（視線、動き、物体、顕著性）を使う事前学習の系統と効果
- (3) 公開されている手術基盤モデルの一覧（事前学習データの内訳、開放手術や一人称を含むか、重みの公開、ライセンス、backbone）
- (4) 手術基盤モデルを学習に使われていない種類の手術（開放、一人称、顕微鏡）に移したときの値と、一般の基盤モデル（DINOv3、V-JEPA 2、VideoMAE V2 など）との比較。凍結と fine-tune の両方
- (5) 公開の重みを初期値にして対象データで自己教師あり学習を続ける方法（領域適応としての事前学習）の効果
- (6) 手術映像での ResNet 系と ViT 系の自己教師あり学習の比較
- (7) 事前学習のデータに評価に使う動画（注釈なし）が含まれる場合の扱い
- (8) クリップを入力にする映像モデルを online（過去のみ）で使う方法と性能の落ち方
- (9) 一人称の非手術映像での事前学習を手術や別の一人称の課題に移した研究
- (10) 事前学習が効かなかった報告、一般の重みに負けた報告
- 特に確かめたい事実: GGMAE（arXiv 2405.19644）の Table 2 の各行の読み・事前学習の動画の範囲・seed の数／SurgMotion（arXiv 2602.05638）の Table 1 と Table 3、EndoFM の値が Cholec80 の値と同じに見える件、評価の分割と手順、査読の有無／SurgVISTA の事前学習データに開放手術や一人称が含まれるか

**問いの字面の出所。** 依頼文の最新版（プロジェクト文書 claude/literature_requests_2026-10-18.md）で確かめた。A3 は 10-03 版から変更なし、A2 は本文が変更なしで (9)(10) が 2026-10-18 に足された。上の字面は 10-18 版のとおり。共通ブロック（調査の作法）は 10-18 版で「0. 本研究の設定」「手術・医療の語を入れない探索」「数値に設定を一組で添える」「推奨と順位を書かない」が足されており、A2c・A3c（2026-10-08 の送信）は足される前の作法で投げられている。A2g・A2f・A3g がどちらの作法で投げられたかの記録は 10-18 版 §15 に無い。検索日から、A3g（2026-10-05）は 10-18 版の追加より前なので足される前の作法、A2g（2026-10-19）と A2f・A2s（2026-10-21）は足された後の作法で投げられたと本書は読む（運用会話の指摘 2026-10-22。利用者の 2026-10-21 の記憶「A2g・A3g は最新」は A3g について日付と合わない）。A2g は (9)(10) にも答えている（A2g L33–L34、L473–L495）が詳細記録は無く、(9)(10) だけの補足の依頼（10-18 版 §0.2 の形: 背景の再掲＋共通ブロック＋(9)(10)。依頼文は literature_request_A2_supplement_2026-10-21.md）を 2026-10-21 に送り、その報告が A2s（検索日 2026-10-21）。A2s は、既に持っている文献を系統表に含め、個別の記録は作らないという指定に従ったと書く（A2s L5）。A3 の本文（問いの字面）は 10-03 版から変わっていないので、A3g の問いは同じ。

旧地図 A（v1）の問いは「開放手術・一人称視点・15 から 21 動画・online-causal で、工程塔の候補（初期化源、凍結範囲、時間ヘッド、履歴長、段数、損失、補助教師）をどう決めるか」で、当時の利用者の決定（2026-09-16）により無ラベル動画の自己教師あり事前学習を候補から外していた（旧地図の記載）。その決定は F 2026-10-03 で置き換えられた。

### 0.2 規則

- 行は報告（または旧地図）に書かれた事実だけを載せる。数値・表番号は元のまま変えていない。報告に書かれた差のうち、差の両側の値が行に載っている 35 個の記述を本書の作成者が検算した。34 個が一致し、1 個（A-12 の特徴の拡張と平滑化損失による差の幅）は合わなかった（A-12 の §6 の符号の欄に注記）。両側の値が行に無い差（要旨の値など）は検算していない
- 報告が「不明」「未確認」とした欄は不明のまま残した。報告に項目が無いものは「報告に記載なし」、旧地図の様式に無かった項目は「旧地図に記載なし」と書いた。推測で埋めていない
- 現役度は報告の値（SOTA 級／定番の基準／新興／置き換え済み／不明）と理由。報告が五つの値の外の語（「現役」「定番」など）で書いたものは、その語のまま写した。報告どうしで値が違うときは両方を書いた
- 距離は一つの数字にしない。§3 の軸に分けた。探索の優先度には使わない。旧地図の距離 0〜3 は 2026-10-03 に定義ごと置き換えられたため移していない
- 報告者の解釈と提案（各報告の (6) の節、A2g の「解釈と提案」、A3g の「あなたの解釈と提案」、A2c・A2f・A3c の TL;DR のうち提案の行）と、報告者の読みを含む要約は地図に載せず、起票者用の文書に移した（F 2026-10-18）。旧地図の「A.4 起票者の読み」と「未検証の理由の仮説」も移していない
- 見つからなかったもの（§10）と未検証の組み合わせ（§11）は、その設計が新しい・価値があるという根拠として読まない。見つからない理由には、技術的な困難、価値が乏しいと見なされていること、偶然がありうる（F 2026-10-18）
- 出所の列（§2）の「A2g L」「A1 L」などは各報告の行番号（1 から数える）。報告の参照記号（citation の印）は除いた
- 二つ以上の報告が同じ文献を扱うときは一行にまとめ、値の後に出所の記号を書いた。報告どうしの値の食い違いは両方を残した
- 方向の番号は依頼文の 7 方向（一 同じデータ・同じ設定、二 手術一般、三 一人称の非手術、四 一般映像、五 機構の一般論、六 方法論、七 否定的な結果）
- 行の並び: A-01〜A-06 は EgoSurgery とその周辺、A-07〜A-22 は手術の時間モデル、A-23〜A-33 は非手術の時間モデル（行動分割・online 行動検出・一人称）、A-34〜A-52 は手術の事前学習・基盤モデル、A-53〜A-73 は一般・一人称の事前学習と視線、A-74〜A-93 は評価・区間の欠け・再現性（A2f まで）、A-94〜A-115 は A2s の詳細記録（A-94〜A-96 欠け・破損のある映像、A-97〜A-108 経過時間・連続時間・不規則時刻のモデル、A-109〜A-115 計算環境・決定性）。並びは優先度ではない

### 0.3 この地図にまだ入っていないもの

- **種のうち行にしていないもの。** SKiT（A2c は他の論文の引用から実在を確認、ID は未確認・本文は未読〔A2c L546〕。A2g は実在を確認した範囲に含める〔A2g L58〕が、詳細記録と ID は無い）。Assembly101、Ego4D、HoloAssist、EgoProceL（A2c は原典の ID を未確認〔A2c L547〕。A2g は実在を確認したとし、Assembly101 を 4,321 本・固定 8 視点と一人称 4 視点の同時撮影と書く〔A2g L58、L499〕が、詳細記録と ID は無い）
- **名前だけが挙がり、詳細記録も書誌 ID も無いもの。** 時間モデル: PhaseLSTM、PhaseNet、NETE（A-01 の Table 1 に値がある）、SV-RCNet（A-74 に再実装の値がある）、OperA、SAHC、MuST、HTT-Net、ReSW-VL、TeSTra、MAT、E2E-LOAD、OadTR、MATR、HAT、DiffAct、Meta-SurDiff、VidParse、OODL、PREGO・TI-PREGO、TOAD、SurgAtlas、SurgPLAN、EgoPER、IODA（A-80 の比較対象）。事前学習: PeskaVLP、OphCLIP、UMT、EgoExOR、EgoClip、LaViLa。評価: Metrics Reloaded（A3c は未確認と書く〔A3c L125〕。A2s も一次資料で書誌を再確認できず、効果量を使っていないと書く〔A2s L29、L543〕）。StableSPR（A-95）の plug-in 先の SKiT は上の種の項のとおり記録が無い
- **書誌 ID はあるが行にしていないもの。** ORQA（arXiv 2505.12890。A3c は EgoSurgery を QA のデータとして使うだけと書く〔A3c L123〕）
- **報告の名前が一意に定まらないもの。** 種の「Ego-Exo」を、A3c は Ego-Exo4D（CVPR 2024）と判断し（A3c L143）、A3g は原典を一意に確認できず記録から外した（A3g L272）。A2c・A2g は既に持っている文献として系統表に置いた。本書は旧地図の行（Li, Nagarajan, Xiong, Grauman 2021、arXiv 2104.07905）を A-61 に移し、Ego-Exo4D は A-30 に置いた
- **A1 の報告の本文の読み直し。** 旧地図の 15 行は旧地図の表から移し、A1 の報告（見つかったのは 2026-10-21）は行番号を出所に足しただけで、本文を地図に写し直していない。A1 の「設定類似度による最接近論文」（L83–L99）は報告者の読みを含み、起票者用の文書に置いた

---

## 1. 系統表

報告ごとに系統の切り方が違うため、問いの群ごとに四つの表に分けた。現役度と理由は報告の記載（記号つき）。報告の系統表に無く、詳細記録の系統の欄だけにあるものは「（詳細記録から）」と書いた。

### 1.1 時間モデルの系統（A2 の問い (1)〜(8)。A2c L10–L30、A2g L36–L58）

| 系統 | 代表 | 現役度（報告） | 理由（報告） | 本地図の行 |
|---|---|---|---|---|
| 因果的な時間畳み込み（多段の TCN） | TeCNO、MS-TCN、NETE、causal TCN（A2c）。OnlineTAS の causal TCN（A2g） | 定番の基準（A2c、A2g） | A2c: BernBypass70・AutoLaparo（MoSFormer Table 1）、EgoSurgery（EgoSurgery-Phase Table 1）、GTEA・EgoProceL・EgoPER（ProTAS Table 1）の比較表で使われる。A2g: TeCNO は 2024〜25 の比較でも使われ、一般の online の行動分割でも causal TCN が強い基準 | A-07、A-26、A-23、A-01、A-29 |
| 再帰型（LSTM／GRU） | EndoNet、PhaseLSTM、SV-RCNet、TMRNet、GRU、BN を使わない CNN-LSTM（A2c）。MiniROAD（A2g） | 定番の基準（A2c、A2g）。PhaseLSTM は EgoSurgery で置き換え済み（A2c） | A2c: AutoLaparo（MoSFormer Table 1）、Cholec80（TUNeS Table I）。PhaseLSTM は EgoSurgery-Phase Table 1 で Jaccard 21.9。A2g: 単独の LSTM は軽量の基準、GRU は記憶と組み合わせて使われる | A-10、A-11、A-25、A-75、A-74 |
| Transformer による集約（局所） | Trans-SVNet、OperA、ASFormer、SAHC（A2c）。Trans-SVNet、SKiT、Surgformer（A2g） | 定番の基準（Trans-SVNet。A2c、A2g） | A2c: Cholec80（TUNeS Table I・MoSFormer Table 1）、一人称（ProTAS Table 2）。A2g: SKiT・Surgformer は手術のベンチマークで比較対象に残るが、EgoSurgery の過去のみの条件では未検証 | A-08、A-27、A-14 |
| 長時間文脈・end-to-end の映像 Transformer | LoViT、SKiT、Surgformer、MoSFormer、TeSTra（A2c）。LoViT、LSTR、E2E-LOAD、MAT（A2g） | SOTA 級（A2c。Cholec80・AutoLaparo・BernBypass70 の online）。LSTR は online 行動検出の定番の基準（A2g） | A2c: MoSFormer Table 1（プレプリント）。EgoSurgery での報告なし。A2g: LoViT は手術工程の強い既存の基準。LSTR を一般の行動分割にそのまま移すと causal TCN より悪いという否定的な証拠がある | A-09、A-14、A-15、A-28 |
| 状態空間モデル（Mamba／SSM） | SR-Mamba、SPRMamba、HID-SSM、SurgicalMamba、EndoMamba（A2c）。＋ PhaseMamba（A2g） | 新興（A2c、A2g） | A2c: Cholec80・AutoLaparo・ESD385 の報告で、著者以外の追試なし。EndoMamba は EgoSurgery の凍結の探索で下位（SurgMotion Table 3、F1 13.90）。A2g: 2024〜26 に増えた。SR-Mamba は双方向の decoder を明記する。EgoSurgery の過去のみの条件での報告は 0 件 | A-16、A-17、A-18、A-19、A-20、A-43 |
| 記憶機構 | TMRNet、LSTR、OnlineTAS、MoSFormer（A2c）。＋ MAT（A2g） | TMRNet は定番の基準、OnlineTAS・MoSFormer は新興、LSTR は行動分割では弱い基準（A2c）。SOTA 級／定番（A2g） | A2c: LSTR は OnlineTAS Table 8・9。A2g: OnlineTAS は NeurIPS 2024 の online の行動分割で上位。TMRNet・LSTR は基準として使われ続ける | A-11、A-28、A-23、A-15 |
| 多尺度・階層 | MS-ASCT、MuST、TUNeS、Surgformer の HTA、SAHC（A2c）。MS-ASCT、LoViT、Surgformer、HID-SSM（A2g） | MS-ASCT・MuST は新興、TUNeS は Cholec80 の online で上位（A2c）。定番〜新興（A2g） | A2c: TUNeS Table I は著者自身の表。A2g: MS-ASCT は因果的な多尺度の注意を明示、HID-SSM は局所と大域の SSM | A-13、A-12、A-14、A-18、A-09 |
| 言語を使うもの | SurgVLP、HTT-Net、ReSW-VL、ORQA（A2c）。EgoVLP、SurgVLP、TI-PREGO、TOAD、SurgAtlas（A2g） | 新興（A2c）。新興〜定番（A2g） | A2c: SurgVLP は EgoSurgery の凍結の探索で中位（SurgMotion Table 3、F1 23.26）。A2g: 工程分割の因果的な（過去のみの）証拠は弱い | A-44、A-58、A-59 |
| 基盤モデル（backbone 側）・表現学習・end-to-end | SelfSupSurg・SurgMAE・GGMAE・SurgPETL、EndoViT、EndoFM、GSViT、SurgeNetXL、DINOv3、VideoMAE、SurgMotion（A2c）。EndoNet、SelfSupSurg、GGMAE、SurgMAE、SurgPETL、SurgMotion、SR-Mamba の single-step（A2g） | EgoSurgery では SurgMotion が SOTA 級、SelfSupSurg・SurgeNetXL は下位、SurgPETL は不明（A2c）。「現役」（A2g の語） | A2c: SurgMotion Table 3（プレプリント、事前学習に EgoSurgery を含む）。SurgMAE は EgoSurgery で VideoMAE V2 を下回った（EgoSurgery-Phase Table 2） | §1.4 の行 |
| 拡散モデル | DiffAct、Meta-SurDiff（A2c） | DiffAct は offline で SOTA 級、online 化は新興（A2c） | A2c: GTEA・50Salads・Breakfast（OnlineTAS Table 8・9） | A-77（詳細記録から） |
| 進捗予測・タスクグラフ・手順の事前知識 | ProTAS、OnlineTAS の後処理、VidParse（A2c）。ProTAS（A2g） | 新興（A2c）。定番の基準（一人称の online の手順。A2g） | A2c: 一人称の手順動画。A2g: CVPR 2024 の後も後続の文献が引用 | A-24、A-23 |
| 境界・構造化された遷移・後処理 | MS-TCN の平滑化の損失、OnlineTAS の後処理、CRF／HMM 系（A2g） | 「定番の補助手法」（A2g の語） | A2g: GTEA・50Salads で segment の指標を強く改善。時間の encoder の代わりではなく予測の正則化 | A-26、A-23 |
| online 行動検出の流用 | LSTR、TeSTra、MAT（A2c） | 行動分割では弱い（A2c） | A2c: OnlineTAS Table 8・9。手術では TeSTra が比較対象に残る（MoSFormer Table 1） | A-28、A-25 |
| 工程の区間の推定（phase proposal） | SurgPLAN、SurgPLAN++（A2g） | 新興／不明（A2g） | A2g: フレームごとの分類器を区間の提案に置き換える別の系統。一人称・開放手術では未検証 | A-21 |
| 視点の扱い（一人称特有） | Ego-Exo4D の VI Encoder・視点の蒸留、Dexterous Focus（A2c） | 新興（A2c） | A2c: Ego-Exo4D の keystep | A-30、A-31 |
| 視線・物体・動き・複数の信号による条件付け | GGMAE の視線、Ego-Exo、EgoSurgery-Tool／HTS、Ego4D 系（A2g） | 新興〜定番（A2g） | A2g: EgoSurgery の視線でマスクを選ぶ方式に直接の証拠 | A-01、A-61、A-03、A-04 |
| 一人称の表現・データ（既に持っている文献） | EgoVLP、Ego-Exo、EGTEA Gaze+、EPIC-KITCHENS（A2c） | EgoVLPv2 は Ego-Exo4D keystep の定番の基準。EGTEA・EPIC-KITCHENS はデータセットなので不明（A2c） | A2c: Ego-Exo4D Table 6 | A-58、A-59、A-61、A-62、A-63 |
| 評価の方法論 | Metrics Matter、BN の落とし穴、指標の系統的な分析（A2c） | 定番の参照先（A2c） | A2c: MoSFormer が非緩和の評価の根拠に引く | A-74、A-75、A-76 |
| その他（詳細記録から） | SemiVT-Surge（A3c の系統表 S10）、Ego-METAS、AHA、SURGE Phase 1、EgoSurgery の公式リポジトリ | 各行の §4 | — | A-22、A-32、A-33、A-05、A-06 |

報告の系統表の件数（各系統の文献が詳細記録に何件あるか）は、A2c が 2、4、3、2、4、3、3、0、2、0、2、1、2、0、3（A2c L16–L30。上の表とは系統の切り方が違う）、A2g が 2、1、1、1、4、3、2、1、0、1、2、3、1（A2g L42–L54）。A2g は既に持っている文献 15 件を系統表に置き、詳細記録を作っていないと書く（A2g L56）。

### 1.2 欠けのある区間の列の扱い（A2 の問い (9)。A2f L14–L23）

| 系統 | 代表 | 現役度（報告） | 理由（報告） | 本地図の行 |
|---|---|---|---|---|
| 9-A 区間・欠けをつないで一系列として扱う（暗黙の既定） | EgoSurgery-Phase（記載なし）、Zohar ほか（区間の除去） | 不明 | 扱いを明記した論文なし | A-01、A-02、A-81 |
| 9-B 区間・クリップごとに状態を初期化 | MiniROAD、Rivoir ほかの SWE、Ego-Exo4D | THUMOS'14 の online 行動検出では定番の基準。Cholec80 では SWE は置き換え済み | Rivoir ほか Table 3 | A-25、A-75、A-30、A-23 |
| 9-C 黒塗り等で時間軸を保つ | MultiBypass140、OoBNet、ROBAN、AHA | 手術データの配布の匿名化では定番 | 時間モデルへの効果の測定なし | A-79、A-78、A-80、A-33 |
| 9-D 欠けの長さ・時刻を入力に与える | GRU-D | 医療の時系列では定番 | 映像の工程認識での採用は見つからない | A-85 |
| 9-E 境を越えた注意を遮断（マスク） | INTRADoc、KORMo | LLM の事前学習で新興〜定番 | — | A-82、A-83 |
| 9-F 状態の持ち越し（stateful） | Rivoir ほかの CHE／CHT、Transformer-XL、OnlineTAS、SurgicalMamba | Cholec80 の online 工程認識で SOTA 級の構成要素。言語モデルでは定番 | Rivoir ほか Table 3 | A-75、A-84、A-23、A-19 |
| 9-G サンプリング間隔・時間分解能 | MS-TCN Table 6 | 行動分割で定番の基準 | — | A-26 |

A2g は問い (9) の系統表を作っていない。A2g は、実動画の不連続な区間をつないだときの影響を EgoSurgery で測った論文は見つからず、OnlineTAS は系列の始まりで記憶を初期化するが人工的な欠けの影響は未検証と書く（A2g L33、L473–L479）。A2s の系統表（問い (9)(10) を一つの表にしている）は §1.5。

### 1.3 計算機による値の散らばり（A2 の問い (10)。A2f L25–L35）

| 系統 | 代表 | 現役度（報告） | 理由（報告） | 本地図の行 |
|---|---|---|---|---|
| 10-A seed による差 | Summers & Dinneen、Bouthillier ほか、Jordan、C2F-TCN | 一般の機械学習の方法論として定番 | — | A-87、A-89、A-90、A-29 |
| 10-B 計算機・GPU の種類による差 | Zhuang ほか（P100／V100／RTX5000／T4／TPU） | 一般の機械学習の方法論 | 手術・行動分割では測定なし | A-86 |
| 10-C 数値精度（fp16／bf16／TF32） | 本文で確認できたものなし | 不明 | — | なし |
| 10-D ライブラリの版による差 | Pham ほか | ソフトウェア工学の方法論 | — | A-88 |
| 10-E 並列化（GPU 数・DDP・BN の同期） | Rivoir ほか（BN と batch の形）、Zhuang ほか（BN の有無） | 不明 | GPU 数を変えた測定は見つからない | A-75、A-86 |
| 10-F データ処理（デコーダ・リサイズ・読み込みの順） | Parmar ほか、Zhuang ほか（入力の順） | 生成モデルの評価で定番（clean-fid） | — | A-91、A-86 |
| 10-G 決定性の設定と費用 | Zhuang ほか（最大 746%）、Summers & Dinneen（約 15%） | 一般の機械学習の方法論 | — | A-86、A-87 |
| 10-H 再現性の総説・評価の不一致 | Renard ほか、Gundersen ほか、Metrics Matter、CPKD | 医用画像・手術の方法論 | — | A-92、A-93、A-74、A-77 |

A2g は問い (10) の系統表を作っていない。A2g は、GPU・CUDA の環境を変えた統制された再現性の研究は見つからず、GGMAE は TITAN RTX 3 枚、SurgMotion は H800 4 枚を使うが、計算機による差は測っていないと書く（A2g L34、L489–L495）。10-C（数値精度）は A2s でも手術・行動分割の同じ処方での fp16／bf16／TF32 の比較は見つからず（A2s L529）、浮動小数点の reduction の順序を扱う A-114 が近い。A2s の系統表は §1.5。

### 1.4 事前学習・基盤モデルの系統（A3 の問い。A3c L10–L24、A3g L3–L37）

| 系統 | 代表 | 現役度（報告） | 理由（報告） | 本地図の行 |
|---|---|---|---|---|
| 対象データ上の映像 MAE（マスク方式の改変）・手術の masked modeling | GGMAE、SurgMAE、VideoMAE（A3c S1）。VideoMAE、SurgMAE、EndoViT（A3g） | 新興（A3c。EgoSurgery、著者以外の追試なし）。定番の基準〜置き換えが進行中（A3g） | A3g: MAE は比較対象に残るが、2025〜2026 は蒸留・JEPA 系なども増えた | A-01、A-38、A-53、A-37 |
| 対象の手術データ上の画像 SSL | SelfSupSurg（A3g） | 定番の基準（A3g） | A3g: 後続の手術の基盤モデルの論文が比較と設計の根拠に引く | A-34、A-35 |
| 事前知識でマスクを選ぶ・損失に重みをつける（視線・動き・物体） | GGMAE、SurgMotion、MME（A3c S2）。GGMAE（視線）、SurgMotion（動き）、Object-Aware VLP（物体）（A3g） | 新興（A3c、A3g） | A3c: EgoSurgery と一般映像。A3g: EgoSurgery では視線に直接の肯定的な証拠がある | A-01、A-02、A-55、A-64 |
| 手術映像の大規模 SSL 基盤モデル | SurgMotion、SurgVISTA、Endo-FM、EndoMamba、GSViT（A3c S3）。Endo-FM、EndoViT、GSViT、SurgeNetXL、SurgVISTA、LemonFM、EndoMamba（A3g） | SOTA 級を主張（A3c）。「現役」。SurgeNetXL・SurgVISTA・LemonFM は直近の査読論文で上位（A3g） | A3c: Cholec80 ほか。査読つきの比較表は少ない | A-02、A-41、A-39、A-43、A-40、A-36、A-42、A-37 |
| 手術画像の SSL 基盤モデル | SelfSupSurg、EndoViT、SurgeNetXL、LemonFM、EndoSSL、GastroNet（A3c S4） | 定番の基準（A3c） | A3c: Cholec80、AutoLaparo | A-34、A-37、A-36、A-42、A-46、A-45、A-51 |
| 手術の映像と言語 | SurgVLP、PeskaVLP、OphCLIP（A3c S5）。SurgVLP、PeskaVLP 系（A3g） | 定番の基準（zero-shot。A3c）。定番になりつつある（A3g） | A3g: 視覚だけの下流にも比較対象として出る | A-44 |
| 一般の基盤モデル | DINOv3、V-JEPA 2、VideoMAE V2、UMT（A3c S6）。DINOv3、VideoMAE V2、V-JEPA 2（A3g） | 定番の基準（A3c）。SOTA 級／新興（A3g） | A3c: 手術の比較表で強い基準として使われる。A3g: EgoSurgery の凍結した転移では DINOv3 が多くの手術の基盤モデルを上回る | A-56、A-57、A-54、A-53 |
| 領域適応としての継続事前学習 | Roth 2024、SelfSupSurg（初期化の実験）、鳥類の音響の MAE（A3c S7） | 不明（A3c） | — | A-70、A-34、A-71、A-36、A-52 |
| 視線を注意の教師・入力に使う（一人称） | Li 2018、Min 2021、Gaze-guided surgical attention（A3c S8） | 定番（EGTEA。A3c） | — | A-65、A-66、A-67、A-68、A-69、A-62 |
| 一人称の非手術映像での事前学習 | EgoVLP、InternVideo-Ego4D（A3c S9）。EgoVLP、EgoVLPv2（A3g） | 定番（Ego4D、EPIC。A3c）。定番の基準（一人称の映像と言語。A3g） | A3g: 手術への直接の転移は未確認 | A-58、A-59、A-60、A-61 |
| クリップのモデルを online で使う・online／causal の手術工程 | Surgformer、SemiVT-Surge、SurgicalMamba（A3c S10）。TeCNO 系、LoViT、EndoMamba、GSViT（A3g） | SOTA 級（Cholec80。A3c）。「現役」（A3g） | A3g: クリップの基盤モデルの「未来あり」と「過去だけ」の直接の比較は乏しい | A-14、A-22、A-19、A-07、A-09、A-43、A-40 |
| 評価・統計・事前学習の漏れ | Metrics Matter、MoSFormer、SurgVISTA の分割の規約（A3c S11）。SurgVISTA の重なりの明示的な除去、EgoSurgery／SurgMotion の不明瞭な例（A3g） | 定番（A3c）。「重要性が上がっている」（A3g の語） | — | A-74、A-15、A-41、A-02、A-01、A-72、A-73 |
| 開放手術・顕微鏡の大規模データ・基盤モデル（詳細記録から） | AVOS、OVFM | 報告に記載なし | — | A-48、A-49 |
| 凍結と fine-tune の比較（詳細記録から） | OmniRAS、ZEN、DART | 報告に記載なし | — | A-50、A-51、A-52 |
| 凍結した ViT＋adapter（旧地図の系統） | SurgPETL | 旧地図に記載なし。A2c の系統表は不明 | — | A-47 |

報告の系統表の件数は、A3c が 3、3、6、6、2、3、4、5、2、3、4（A3c L14–L24）、A3g が 2、4、3、8、1、4、2、3、3（A3g L9–L17）。A3g は手術・内視鏡の基盤モデルの横断の一覧（事前学習データ、開放手術・一人称を含むか、backbone、公開の重みとライセンス）を別の表にしている（A3g L19–L37）。その中身は §3（データ規模）と §7（コード・重み・ライセンス）の各行に移した。

### 1.5 A2 の補足の報告の系統表（A2 の問い (9)(10)。A2s L9–L24）

A2s は系統表の「下の新規記録」の列で、各系統の詳細記録の件数を書く（既に持っている文献は系統表に置くだけで記録を作らない〔A2s L5〕）。件数は 0、2、1、1、0、4、3、2、3、0、5、2、0、0（A2s L11–L24。合計 23。詳細記録の見出しは 22。本書の作成者は、StableSPR〔A-95〕が「OOB・プライバシー除去・不連続区間」と「因果 TCN・online」の両方に数えられていると読む〔評価の行に「StableSPR は上で計数」とある〕が、報告は各行の内訳を書いていない）。

| 系統（A2s の語） | 代表（A2s の記載） | 現役度と対象（A2s） | 理由（A2s） | 本地図の行 |
|---|---|---|---|---|
| EgoSurgery 系列そのもの | EgoSurgery-Phase、-Tool、-HTS、SurgMotion、公式リポジトリ | 新興: EgoSurgery benchmark | Phase 論文は 2024 年 MICCAI、21 本・15 h・9 工程の基準を定義。公式リポジトリが配布の窓口 | A-01、A-03、A-04、A-02、A-06 |
| 手術映像の OOB・プライバシー除去・不連続区間 | OoBNet、MultiBypass140、ROBAN、Zohar ほか、Rivoir ほか、Bayat ほか | 定番の基準＋不明: 腹腔鏡 workflow | OOB が通常の工程の系列に割り込む問題設定は複数の文献にあるが、未知の長さの削除区間で状態を持ち越すか初期化するかの比較は確認できなかった。Bayat ほかは OOB が時間モデルを害すると明示 | A-78、A-79、A-80、A-81、A-75、A-94 |
| 因果 TCN・online の工程・行動分割 | TeCNO、MS-TCN、MiniROAD、OnlineTAS、AHA、StableSPR | MS-TCN は定番の基準、2024〜26 の online 系は新興 | StableSPR は MICCAI 2026 で三つの online の工程認識の backbone に時間的な安定化の機構を当てる | A-07、A-26、A-25、A-23、A-33、A-95 |
| 一般映像の temporal corruption・dropped-frame robustness | Zeng ほか CVPR 2024 | 定番化途上: THUMOS14-C／ActivityNet-C | 7 つの時間的行動検出の手法を欠け・黒・ぼけ・packet loss 型の破損で比較。欠けたフレームに対する最も直接的な一般映像の証拠（A2s の語） | A-96 |
| 一人称の長時間手順・多尺度文脈 | Ego-Exo4D、Ego-METAS、Transformer-XL、INTRADoc、KORMo | Transformer-XL は長い文脈の定番、Ego-METAS・KORMo は新興 | EgoSurgery 型の「消去した実時間区間」の持ち越し・初期化の比較ではない。Ego-METAS は sampling rate と Edit の関係を実験 | A-30、A-32、A-84、A-82、A-83 |
| elapsed-time を入れる RNN・集合・時間埋込み | GRU-D、T-LSTM、mTAN、SeFT、Time2Vec | GRU-D は定番の基準、mTAN は継続参照、T-LSTM／SeFT／Time2Vec の現役度は benchmark 依存 | 2026 年の不規則時刻の文献も GRU-D・mTAN を系譜として扱う | A-85、A-98、A-97、A-100、A-99 |
| ODE・CDE による連続時間の状態の発展 | Latent ODE／ODE-RNN、GRU-ODE-Bayes、Neural CDE | 定番の基準: irregular time series | 2026 年の MASCIT・TIDES でも比較・関連研究として扱われる | A-101、A-102、A-103 |
| 不規則時刻の Transformer・graph attention | Raindrop、ContiFormer | Raindrop は定番の比較対象、ContiFormer は比較的新しい | MASCIT の Table 2 は Raindrop を含む 12 の基準を再比較 | A-104、A-105 |
| continuous／selective state-space model | S5、SurgicalMamba、TIDES、MASCIT | S5 は定番の基準、SurgicalMamba・TIDES・MASCIT は新興 | S5 は連続時間の離散化の Δ に実時間の間隔を与えられることが 2026 年の TIDES で明示的に再整理されている | A-106、A-19、A-107、A-108 |
| segment／boundary の評価 | MS-TCN の Edit・F1@k、Metrics Matter、C2F-TCN、StableSPR の TFI、Ego-METAS | 定番の評価＋新興の指標 | StableSPR は Edit が segment 内の時間的な不安定さを区別できない具体例を示し TFI を導入 | A-26、A-74、A-29、A-95、A-32 |
| 乱数・GPU・tooling による学習の変動 | Zhuang ほか、Summers & Dinneen、Pham ほか ASE 2020、Bouthillier ほか、Jordan、Gundersen ほか、Chen ほか、DEVIATE、Coakley ほか | 定番の基準: DL reproducibility | 2025 年の RepDL も Pham、Summers、Zhuang、Chen を問題設定の主要な先行研究として列挙 | A-86、A-87、A-88、A-89、A-90、A-93、A-109、A-112、A-110 |
| 決定性・浮動小数点の再現性 | Zhuang ほか、Chen ほか、Shanmugavelu ほか、RepDL | 定番＋新興 | 従来の決定性を固定した kernel のパッチは相当な計算の費用があり、RepDL は別の方向からビット単位の再現性を狙う | A-86、A-109、A-114、A-115 |
| 画像の decode・resize・JPEG と評価の実装 | Parmar ほか（clean-fid） | 画像生成の評価では定番、手術の工程認識への外挿は不明 | decord／PyAV／torchvision／OpenCV や JPEG の再圧縮だけを変えて同じ手術映像のモデルを再学習した定量の研究は確認できなかった | A-91 |
| 手術モデル自身の再現性・seed 感度 | Renard ほか、Metrics Matter、CPKD、C2F-TCN | 比較・再現性の資料として現役度は benchmark 依存 | seed や分割の問題は扱われるが、同じ seed を GPU／CUDA だけ変えて対応づける実験は確認できなかった | A-92、A-74、A-77、A-29 |

A2s は、S5 が実在する（arXiv 2208.04933、ICLR 2023）こと、種として挙げた mTAN、Latent ODE／ODE-RNN、GRU-ODE-Bayes、Neural CDE、Raindrop、ContiFormer、SeFT、Time2Vec、T-LSTM、S5、Towards Training Reproducible Deep Learning Models、DEVIATE の実在を確認したこと、Metrics Reloaded は一次資料で書誌を確認できなかったことを系統表の後に書く（A2s L26–L29）。A2s の記録の Shahriari ほか（A-111）と Ravi ほか（A-113）は系統表の代表に挙がっていない。

---

## 2. 行の一覧

「文献」の欄は「著者 年, 題名（注記）」の形で書いた（照合器が読む形）。報告に著者・題名が無いものは報告の呼び名を書き、全角の括弧の中にそう注記した。「読んだ範囲」は各報告の申告で、報告ごとに違う。

| ID | 文献 | 書誌 ID | 掲載先 | 方向 | 読んだ範囲 | 出所 |
|---|---|---|---|---|---|---|
| A-01 | Fujii, Hatano, Saito, Kajita 2024, EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos（GGMAE と同じ論文） | arXiv 2405.19644、DOI 10.1007/978-3-031-72089-5_18 | MICCAI 2024（査読つき、pp.187–196〔A3c〕） | 一 | A2c・A2f 本文。A2g arXiv HTML の本文と実験表、MICCAI の公式頁。A3c 本文全体（v3 PDF。補足資料は未読）。A3g 本文と実験表。旧 A は全文 | 旧 A.1 の 1 行目（A1 L21）、A2c L34–L81、A2f L43–L63、A2g L7、L30、L60–L81、L110–L137、L487、A3c L28–L36、A3g L41–L56。A2s L3、L11、L509、L577、L714 |
| A-02 | Wu, Holm, Chen ほか 2026, SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos（責任著者は Lei。v1 の題名は UniSurg〔A3c〕） | arXiv 2602.05638 | プレプリント（A2c は v2、A2f・A3c は v5〔2026-09-22〕、A3g は v2〔2026-03-24〕を読んだ。査読つきの掲載先は見つからない〔A3c、A3g〕） | 一・二・三・四・五・七（A2c は一・二、A2g は一・二・三・五、A3g は一・二・四・七） | A2c 本文（Table 7 まで）。A2f 要旨・1〜3.2 節・Table 1（EgoSurgery の結果の表は未読）。A2g HTML の本文・Table 3・事前学習の表。A3c 本文全体（v5 HTML）と README（サブエージェント経由）。A3g 本文・Table 1〜3 | A2c L83–L129、A2f L79–L99、A2g L15、L85–L102、L138–L165、A3c L38–L47、A3g L33、L167–L180。A2s L11 |
| A-03 | Fujii, Saito, Kajita 2024, EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos | arXiv 2406.03095 | プレプリント | 一 | A2c 要旨と抜粋。A2f 本文 2 節のスニペット。A3c は確認のみ | A2c L512–L522、A2f L73–L77、A3c L123。A2s L11 |
| A-04 | Fujii ほか 2025, EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos | arXiv 2503.18755、DOI 10.1049/htl2.70049 | Healthcare Technology Letters（査読つき）。DOI は A3c の記載 | 一 | A2c 要旨と抜粋。A2f は要旨の断片だけで未確認。A3c は確認のみ | A2c L524–L532、A2f L392、A3c L123。A2s L11 |
| A-05 | SURGE Phase 1: An AR/VR-Based Deep Learning Framework for Surgical Scene Analysis（著者と年は報告に無い） | DOI 10.1007/978-3-032-31119-1_38 | Springer の会議録 | 一 | 要旨のみ | A2c L534–L541 |
| A-06 | Fujii ほか, EgoSurgery 公式リポジトリ（GitHub Fujiry0/EgoSurgery の README） | なし（GitHub） | GitHub（査読なし） | 一 | README の全文 | A2f L65–L71。A2s L11 |
| A-07 | Czempiel ほか 2020（TeCNO。旧地図は題名を書いていない） | DOI 10.1007/978-3-030-59716-0_33、arXiv 2003.10751 | MICCAI 2020 | 二 | 全文（旧地図の印） | 旧 A.1 の 3 行目（A1 L23）。A2s L13 |
| A-08 | Gao, Jin, Long, Dou, Heng 2021（Trans-SVNet。旧地図は題名を書いていない） | arXiv 2103.09712 | MICCAI 2021 | 二 | 全文（旧地図の印） | 旧 A.1 の 4 行目（A1 L24） |
| A-09 | Liu, Boels, Garcia-Peraza-Herrera, Vercauteren, Dasgupta, Granados, Ourselin 2025（LoViT。旧地図は題名を書いていない） | DOI 10.1016/j.media.2024.103366、arXiv 2305.08989 | Medical Image Analysis 99, 103366（2024-10 にオンライン） | 二 | 全文（旧地図の印） | 旧 A.1 の 5 行目（A1 L25） |
| A-10 | Twinanda ほか 2016／2017（EndoNet。旧地図は題名を書いていない） | arXiv 1602.03012 | IEEE TMI | 二 | 全文（旧地図の印） | 旧 A.1 の 2 行目（A1 L22） |
| A-11 | 2021, TMRNet: Surgical Phase Recognition with Temporal Memory Relation Network（題名は A2g の記載） | arXiv 2103.16327 | IEEE TMI 系（A2g）。A2c は IEEE TMI 2021 と書き ID は未確認 | 二・六・七（A2g） | 要旨とリポジトリの評価の手順（A2g） | A2g L396–L422、A2c L546 |
| A-12 | Funke, Rivoir, Krell, Speidel 2023／2025, TUNeS: A Temporal U-Net with Self-Attention for Video-based Surgical Phase Recognition | arXiv 2307.09997 | IEEE TBME（査読つき、PubMed 40031317） | 二・六 | 本文（サブエージェントによる全文の読解を含む） | A2c L308–L351 |
| A-13 | Zhang, Meng, Cheng, Biskup, Petculescu, Chapman 2024, Friends Across Time: Multi-Scale Action Segmentation Transformer for Surgical Phase Recognition（MS-ASCT） | arXiv 2401.11644 | プレプリント（A2c）。査読版の DOI は不明（A2g） | 二・四 | A2c 要旨のみ。A2g arXiv HTML の本文と実験表の該当部 | A2c L226–L243、A2g L166–L192 |
| A-14 | Yang, Luo, Wang, Chen 2024, Surgformer: Surgical Transformer with Hierarchical Temporal Attention for Surgical Phase Recognition | arXiv 2408.03867、DOI 10.1007/978-3-031-72089-5_57 | MICCAI 2024（査読つき） | 二 | A2c 要旨と抜粋。A2g 要旨のみ。A3c は窓の規約の確認 | A2c L245–L269、A2g L423–L450、A3c L112 |
| A-15 | Ding, Lian, Unberath 2025, MoSFormer: Augmenting Temporal Context with Memory of Surgery for Surgical Phase Recognition | arXiv 2503.00695 | プレプリント | 二・六 | A2c 本文。A3c は評価の扱いの確認 | A2c L271–L306、A3c L113 |
| A-16 | Cao, Wang, Liu 2024, SR-Mamba: Effective Surgical Phase Recognition with State Space Model | arXiv 2407.08333 | プレプリント | 二・五 | A2c 要旨と抜粋。A2g 要旨と HTML の方法の概要（実験表は未読） | A2c L159–L182、A2g L220–L245 |
| A-17 | Zhang ほか 2024, SPRMamba: Surgical Phase Recognition for Endoscopic Submucosal Dissection with Mamba | arXiv 2409.12108 | プレプリント | 二 | A2c 要旨と抜粋。A2g 要旨と HTML の方法の概要 | A2c L184–L205、A2g L246–L271 |
| A-18 | Wu, Wang, Lechner, Hasani ほか 2025, Holistic Surgical Phase Recognition with Hierarchical Input Dependent State Space Models（HID-SSM） | arXiv 2506.21330 | プレプリント | 二・四・五 | A2c 要旨と方法の抜粋。A2g arXiv HTML の本文と実験の部 | A2c L207–L224、A2g L193–L219 |
| A-19 | Oh, Sun 2026, SurgicalMamba: Dual-Path SSD with State Regramming for Online Surgical Phase Recognition | arXiv 2605.14889 | プレプリント（A2c は v3。A2f は著者を未確認と書く） | 二（A2c、A2f）。四・六（A3c の記録 R13） | A2c 要旨と序論のみ。A2f 関連研究と付録 H のスニペット。A3c は窓の規約の確認 | A2c L131–L157、A2f L169–L175、A3c L112。A2s L19 |
| A-20 | PhaseMamba（報告の呼び名。題名・著者・ID は報告に無い。MICCAI 2026） | なし（報告に ID が無い） | MICCAI 2026（A2g の記載） | 二・五 | 報告に記載なし | A2g L11、L46 |
| A-21 | Zhen Chen, Xingjian Luo, Jinlin Wu ほか 2024, SurgPLAN++: Universal Surgical Phase Localization Network for Online and Offline Inference | arXiv 2409.12467 | IEEE ICRA 2025 に採択（A2c）。A2g はプレプリントと書く | 二・四・七 | A2c 抜粋のみ。A2g arXiv HTML の本文と online・offline の推論の手順 | A2c L498–L510、A2g L272–L298 |
| A-22 | SemiVT-Surge（報告の呼び名。題名と著者は報告に無い） | arXiv 2506.01471 | 報告に記載なし | 二 | 報告に記載なし（窓の規約の確認だけ） | A3c L112 |
| A-23 | Zhong, Ding, Yao 2024, OnlineTAS: An Online Baseline for Temporal Action Segmentation | arXiv 2411.01122、DOI 10.52202/079017-1881 | NeurIPS 2024（査読つき） | 三・四・五・七 | A2c 本文。A2f 本文の一部（スニペット、数値は未読）。A2g arXiv HTML の本文・付録・Table 1〜12 | A2c L395–L422、A2f L233–L238、A2g L13、L17、L299–L341、L451–L458。A2s L13 |
| A-24 | Shen, Elhamifar 2024, Progress-Aware Online Action Segmentation for Egocentric Procedural Task Videos（ProTAS） | DOI 10.1109/CVPR52733.2024.01722 | CVPR 2024（査読つき、pp. 18186–18197）。arXiv の ID は不明 | 三・四・五 | A2c 本文。A2g は CVPR の公式頁と公式コードの README（PDF の表は表番号つきで確かめられず数値を引かない） | A2c L8、L424–L455、A2g L342–L367 |
| A-25 | An, Kang, Han, Yang, Kim 2023, MiniROAD: Minimal RNN Framework for Online Action Detection | DOI 10.1109/ICCV51070.2023.00949 | ICCV 2023（arXiv の ID は見つからない。頁番号は CVF 版 10341–10350、IEEE CSDL 版 10307–10316 で違う） | 四 | 本文と補遺（サブエージェントの報告） | A2f L212–L231。A2s L13 |
| A-26 | Abu Farha, Gall 2019, MS-TCN: Multi-Stage Temporal Convolutional Network for Action Segmentation | arXiv 1903.01945 | CVPR 2019 | 四 | 旧 A は全文。A2f は Table 6 と Table 7（スニペット） | 旧 A.1 の 9 行目（A1 L38）、A2f L177–L196。A2s L13、L20 |
| A-27 | Yi, Wen, Jiang 2021（ASFormer。旧地図は題名を書いていない） | arXiv 2110.08568 | 旧地図に記載なし | 四 | 全文（旧地図の印） | 旧 A.1 の 10 行目（A1 L39）。因果化の比較は A-23 の行（A2g L328–L338） |
| A-28 | Xu, Gao, Chen, Davis, Crandall 2021（LSTR。旧地図の記載。旧地図は題名を書いていない） | arXiv 2107.03377 | 旧地図に記載なし | 四 | 全文（旧地図の印） | 旧 A.1 の 11 行目（A1 L40）、A2c L27、L417、A2g L45 |
| A-29 | Dipika Singhania, Rahul Rahaman, Angela Yao 2022, C2F-TCN: A Framework for Semi and Fully Supervised Temporal Action Segmentation | arXiv 2212.11078 | プレプリント | 四 | 付録 B.5 のスニペット | A2f L382–L386。A2s L20、L24、L527 |
| A-30 | Grauman ほか 2024, Ego-Exo4D: Understanding Skilled Human Activity from First- and Third-Person Perspectives | arXiv 2311.18259 | CVPR 2024（査読つき） | 三 | A2c 抜粋のみ。A2f 5.2 節のスニペットと公式の文書 | A2c L457–L468、A2f L198–L203。A2s L15、L579 |
| A-31 | Zachary Chavis, Stephen J. Guy, Hyun Soo Park 2025, Improving Keystep Recognition in Ego-Video via Dexterous Focus | arXiv 2506.00827 | EgoVis workshop の論文 | 三・七 | 数値は補助の取得経由（A2c） | A2c L470–L482 |
| A-32 | 2026, Ego-METAS: Egocentric online Multimodal Energy-efficient Temporal Action Segmentation benchmark | arXiv 2606.02246 | プレプリント（著者は未確認） | 三 | 付録 A.2 のスニペット | A2f L205–L210。A2s L15、L20、L582 |
| A-33 | 2025, AHA — Predicting What Matters Next: Online Highlight Detection Without Looking Ahead | arXiv 2509.16421 | プレプリント（著者は未確認） | 四 | 付録 E.1 のスニペット | A2f L240–L245。A2s L13 |
| A-34 | Ramesh ほか 2023, Dissecting Self-Supervised Learning Methods for Surgical Computer Vision（SelfSupSurg） | DOI 10.1016/j.media.2023.102844、arXiv 2207.00449 | Medical Image Analysis 88:102844（査読つき） | 二・七 | 旧 A は全文。A3c 要旨と本文の断片（後に全文で一文を確認）。A3g 本文・Tables 3–5・Fig. 12・汎化の節 | 旧 A.1 の 6 行目（A1 L26）、A3c L59–L63、L125、A3g L57–L70 |
| A-35 | Jaspers ほか 2024, Exploring the Effect of Dataset Diversity in Self-Supervised Learning for Surgical Computer Vision | arXiv 2407.17904、DOI 10.1007/978-3-031-73748-0_5 | DEMI 2024（LNCS 15265） | 二 | 要旨のみ | A3c L65–L69 |
| A-36 | Jaspers ほか 2026, Scaling up self-supervised learning for improved surgical foundation models（SurgeNetXL） | arXiv 2501.09436、DOI 10.1016/j.media.2025.103873 | Medical Image Analysis 108, 103873（A3g）。A3c は Medical Image Analysis 2025 と書く | 二・五・六 | A3c 要旨のみ。A3g 本文・Tables 1・3・補足の学習の詳細 | A3c L65–L69、A3g L28、L111–L123 |
| A-37 | Batić ほか 2024, EndoViT: pretraining vision transformers on a large collection of endoscopic images | DOI 10.1007/s11548-024-03091-5 | International Journal of Computer Assisted Radiology and Surgery 19:1085–1091（査読つき。A3g）。A3c は IJCARS 19(6) 2024 と書き ID は不明 | 二・七 | A3c 簡略の記録。A3g 本文・Tables 2–7 | A3c L80、A3g L25、L71–L82 |
| A-38 | Muhammad Abdullah Jamal, Omid Mohareri 2023, SurgMAE: Masked Autoencoders for Long Surgical Video Analysis | arXiv 2305.11451 | プレプリント | 二 | 旧 A は全文。A3g 要旨と EgoSurgery の側の再実装の比較 | 旧 A.1 の 7 行目（A1 L27）、A3g L83–L91 |
| A-39 | Wang, Liu, Zhang, Dou 2023, Foundation Model for Endoscopy Video Analysis via Large-scale Self-supervised Pre-train（Endo-FM） | arXiv 2306.16741、DOI 10.1007/978-3-031-43996-4_10 | MICCAI 2023（査読つき） | 二 | A3c 要旨。A3g 本文 | A3c L77、A3g L26、L92–L100 |
| A-40 | Schmidgall ほか 2024, General surgery vision transformer: A video pre-trained foundation model for general surgery（GSViT） | arXiv 2403.05949 | プレプリント（査読の掲載先は確認できず。A3g） | 二・八 | A3c 簡略の記録。A3g 本文 | A3c L79、A3g L27、L101–L110 |
| A-41 | Yang, Zhou, Mayer ほか 2025／2026, Large-scale self-supervised video foundation model for intelligent surgery（SurgVISTA） | arXiv 2506.02692、DOI 10.1038/s41746-026-02403-0 | npj Digital Medicine 2026（査読つき、訂正の告知あり。A3g）。A3c はプレプリント（掲載先は不明）と書く | 二・六 | A3c 本文と Extended Data Table 1〜12。A3g 本文・方法 | A3c L49–L57、A3g L29、L124–L136 |
| A-42 | Che ほか 2025, LEMON: A Large Endoscopic MONocular Dataset and Foundation Model for Perception in Surgical Settings（LemonFM） | arXiv 2503.19740 | CVPR 2026（査読つき） | 二・六・七 | A3c 要旨とリポジトリ。A3g 本文・Table 5 | A3c L71–L74、A3g L30、L137–L146 |
| A-43 | Tian ほか 2025, EndoMamba: An Efficient Foundation Model for Endoscopic Videos via Hierarchical Pre-training | arXiv 2502.19090、DOI 10.1007/978-3-032-05114-1_22 | MICCAI 2025（査読つき） | 二・五・八 | A3c 簡略の記録（Table 1）。A3g arXiv 本文と MICCAI の公式頁 | A3c L78、A3g L31、L147–L156 |
| A-44 | Yuan ほか 2025, Learning Multi-modal Representations by Watching Hundreds of Surgical Video Lectures（SurgVLP） | arXiv 2307.15220、DOI 10.1016/j.media.2025.103644 | Medical Image Analysis 105:103644（査読つき） | 二・五 | A3c 簡略の記録。A3g 本文 | A3c L83、A3g L32、L157–L166 |
| A-45 | GastroNet-5M（報告の呼び名。題名・著者・ID は報告に無い。Gastroenterology 2025〔A3c〕） | なし（報告に ID が無い） | Gastroenterology 2025（A3c） | 二・六 | A3c 簡略の記録。A3g 後続の査読論文の比較の記述と表 | A3c L82、A3g L34、L181–L188 |
| A-46 | Hirsch ほか 2023, Self-supervised learning for endoscopic video analysis（EndoSSL） | arXiv 2308.12394 | MICCAI 2023（A3c、A3g） | 二 | A3c 簡略の記録。A3g は本文を未精査（後続の論文の記述による） | A3c L81、A3g L35、L189–L195 |
| A-47 | Shu Yang, Zhiyuan Cai, Luyang Luo, Ning Ma, Shuchang Xu, Hao Chen 2024（SurgPETL。旧地図は題名を書いていない） | arXiv 2409.20083 | 旧地図に記載なし（arXiv の ID だけ） | 二 | 全文（旧地図の印） | 旧 A.1 の 8 行目（A1 L28） |
| A-48 | AVOS（報告の呼び名。題名と著者は報告に無い。JAMA Surgery 2024） | DOI 10.1001/jamasurg.2023.6262 | JAMA Surgery 159(2):185–192 | 二 | 本文（PMC10701669。A3c） | A3c L92–L93、A3g L33 |
| A-49 | OVFM（報告の呼び名。題名と著者は報告に無い。Nature Biomedical Engineering 2026） | DOI 10.1038/s41551-026-01622-w | Nature Biomedical Engineering 2026 | 二 | 要旨のみ | A3c L95–L96 |
| A-50 | OmniRAS（報告の呼び名。題名と著者は報告に無い） | arXiv 2608.31048 | 報告に記載なし | 二・七 | 要旨と一部 | A3c L86–L87、L90 |
| A-51 | ZEN（報告の呼び名。題名と著者は報告に無い） | arXiv 2602.13633 | 報告に記載なし | 二 | 一部 | A3c L88、L90 |
| A-52 | DART（報告の呼び名。題名と著者は報告に無い） | arXiv 2609.04555 | 報告に記載なし | 二・七 | 一部 | A3c L89–L90 |
| A-53 | 2022, VideoMAE: Masked Autoencoders are Data-Efficient Learners for Self-Supervised Video Pre-Training | arXiv 2203.12602 | NeurIPS 2022（査読つき） | 四 | A3g は元論文を読み直さず、EgoSurgery・SurgVISTA・SurgMotion の比較の側を確認。A3c は本文の表 | A3c L114、A3g L196–L203 |
| A-54 | 2023, VideoMAE V2: Scaling Video Masked Autoencoders with Dual Masking | arXiv 2303.16727 | CVPR 2023（査読つき） | 四 | 報告に記載なし（比較の側の確認） | A3g L204–L210 |
| A-55 | MME（報告の呼び名。題名と著者は報告に無い。CVPR 2023） | arXiv 2210.06096 | CVPR 2023 | 四・五 | 報告に記載なし | A3c L114、A3c L15 |
| A-56 | DINOv3（報告の呼び名。題名と著者は報告に無い。2025） | arXiv 2508.10104 | プレプリント（A3g は原論文の構造と評価の節を確認） | 四・五 | A3g は原論文の構造と評価の節、手術への転移は SurgMotion の表で確認。A3c は引用で実在を確認 | A3c L143、A3g L211–L219 |
| A-57 | 2025, V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning | arXiv 2506.09985 | プレプリント | 四・五 | 原論文の評価と構造の節（A3g）。A3c は引用で実在を確認 | A3c L143、A3g L220–L227 |
| A-58 | Lin ほか 2022, Egocentric Video-Language Pretraining（EgoVLP） | arXiv 2206.01670 | NeurIPS 2022（Spotlight。A3c） | 三 | 旧 A は全文。A3c 本文の記述。A3g は書誌と公式のコード・モデル（全表は未精査） | 旧 A.1 の 12 行目（A1 L52）、A3c L107、A3g L228–L235 |
| A-59 | 2023, EgoVLPv2: Egocentric Video-Language Pre-training with Fusion in the Backbone | arXiv 2307.05463 | ICCV 2023 | 三 | モデルとコードの情報（A3g） | A3g L236–L243、A2c L29 |
| A-60 | InternVideo-Ego4D（報告の呼び名。題名と著者は報告に無い） | arXiv 2211.09529 | 報告に記載なし | 三 | 報告に記載なし | A3c L108 |
| A-61 | Li, Nagarajan, Xiong, Grauman 2021（Ego-Exo。旧地図は題名を書いていない） | arXiv 2104.07905 | CVPR 2021 | 三 | 要旨（旧地図の印） | 旧 A.1 の 13 行目（A1 L53） |
| A-62 | Li, Liu, Rehg 2020（EGTEA Gaze+。旧地図は題名を書いていない） | arXiv 2006.00626 | 旧地図に記載なし | 三 | 要旨（旧地図の印） | 旧 A.1 の 14 行目（A1 L54） |
| A-63 | Damen ほか 2018（EPIC-KITCHENS。旧地図は題名を書いていない） | arXiv 1804.02748 | ECCV 2018 | 三 | 全文（旧地図の印） | 旧 A.1 の 15 行目（A1 L55） |
| A-64 | 2022, Object-Aware Video-Language Pre-training for Retrieval | arXiv 2112.00656 | CVPR 2022（査読つき） | 三・五 | 本文のマスクの方法の部分 | A3g L11、L244–L256 |
| A-65 | Li, Liu, Rehg 2018（In the Eye of Beholder。題名は報告の呼び方。ECCV 2018） | なし（報告に ID が無い） | ECCV 2018 | 三 | 報告に記載なし | A3c L99 |
| A-66 | Min, Corso 2021（題名は報告に無い。WACV 2021） | なし（報告に ID が無い） | WACV 2021 | 三 | 報告に記載なし | A3c L100 |
| A-67 | Can Gaze Inform Egocentric Action Recognition?（著者は報告に無い。ETRA 2022） | なし（報告に ID が無い） | ETRA 2022 | 三・七 | 要旨のみ | A3c L101 |
| A-68 | Human Gaze Guided Attention for Surgical Activity Recognition（著者と年は報告に無い） | arXiv 2203.04752 | 報告に記載なし | 二・三 | 報告に記載なし | A3c L102 |
| A-69 | G3Ego（報告の呼び名。題名と著者は報告に無い） | arXiv 2608.20157 | 報告に記載なし | 三 | 報告に記載なし | A3c L103 |
| A-70 | Roth ほか（題名は報告に無い。EVA-02 を内視鏡画像で継続事前学習） | arXiv 2410.21302 | 報告に記載なし | 二・五・六 | 報告に記載なし | A3c L117 |
| A-71 | 鳥類の音響の MAE（報告の呼び名。題名と著者は報告に無い） | arXiv 2605.14031 | 報告に記載なし | 五・七 | 報告に記載なし | A3c L118 |
| A-72 | Dive into the details of SSL（報告の呼び名。題名と著者は報告に無い。Medical Image Analysis 2023） | arXiv 2209.12157 | Medical Image Analysis 2023 | 六・七 | 報告に記載なし | A3c L119 |
| A-73 | Toward Clinically Ready FMs（報告の呼び名。題名と著者は報告に無い） | arXiv 2603.14271 | 報告に記載なし | 六 | 報告に記載なし | A3c L120 |
| A-74 | Funke, Rivoir, Speidel 2023, Metrics Matter in Surgical Phase Recognition | arXiv 2305.13961 | 技術報告（プレプリント） | 二・六・七 | A2c 本文（サブエージェントによる全文の読解）。A2f 5 節のスニペット。A2g arXiv HTML の本文 | A2c L353–L381、A2f L370–L374、A2g L368–L395、A3c L113。A2s L20、L24、L527 |
| A-75 | Rivoir, Funke, Speidel 2024, On the Pitfalls of Batch Normalization for End-to-End Video Learning: A Study on Surgical Workflow Analysis | arXiv 2203.07976、DOI 10.1016/j.media.2024.103126 | Medical Image Analysis 94:103126（査読つき） | 二（A2f）・六（A2c） | A2c 要旨のみ。A2f 要旨は自分で確認、表の数値は arXiv v5 の本文と付録を読んだサブエージェントの報告による | A2c L383–L393、A2f L144–L167。A2s L12、L561、L692 |
| A-76 | Özkurt, Bajraktari, Pott 2026, Systematic analysis of evaluation metrics for deep learning-based surgical phase recognition in laparoscopic cholecystectomy | なし（PMID 42488379、PMC13388889。DOI は報告に無い） | Frontiers in Artificial Intelligence 9:1873219（査読つき） | 六 | 要旨と抜粋のみ | A2c L484–L496 |
| A-77 | 2025, CPKD: Clinical Prior Knowledge-Constrained Diffusion Models for Surgical Phase Recognition in Endoscopic Submucosal Dissection | arXiv 2507.03295 | プレプリント（著者は未確認） | 二 | 比較の節のスニペット | A2f L376–L380。A2s L24、L527 |
| A-78 | Lavanchy ほか 2023, Preserving privacy in surgical video analysis using a deep learning classifier to identify out-of-body scenes in endoscopic videos（OoBNet） | DOI 10.1038/s41598-023-36453-1 | Scientific Reports（査読つき） | 二 | 要旨と本文の一部 | A2f L101–L119。A2s L12 |
| A-79 | Lavanchy, Ramesh, Dall'Alba, Gonzalez, Fiorini, Müller-Stich, Nett, Marescaux, Mutter, Padoy 2024, Challenges in multi-centric generalization: phase and step recognition in Roux-en-Y gastric bypass surgery（MultiBypass140） | DOI 10.1007/s11548-024-03166-3、arXiv 2312.11250 | IJCARS 19(11):2249–2257（査読つき、オープンアクセス） | 二 | データセットの節のスニペット | A2f L121–L127。A2s L12 |
| A-80 | De Backer ほか 2024, Privacy-proof Live Surgery Streaming: Development and Validation of a Low-cost, Real-time Robotic Surgery Anonymization Algorithm（ROBAN） | なし（PMC11161223。DOI は報告に無い） | Annals of Surgery 280(1):13–20（査読つき） | 二 | スニペット | A2f L129–L135。A2s L12 |
| A-81 | Zohar, Bar, Neimark, Hager, Asselmann 2020, Accurate Detection of Out of Body Segments in Surgical Video using Semi-Supervised Learning | なし（報告に ID が無い） | MIDL 2020（PMLR v121） | 二 | 要旨のみ | A2f L137–L142。A2s L12 |
| A-82 | Zhao, Qu, Staniszewski, Tworkowski, Liu, Miłoś, Wu, Minervini 2024, Analysing The Impact of Sequence Composition on Language Model Pre-Training（INTRADoc） | arXiv 2402.13991 | ACL 2024 | 五 | 本文（1〜4.2 節、Table 1〜4） | A2f L247–L267。A2s L15 |
| A-83 | 2025, KORMo: Korean Open Reasoning Model for Everyone | arXiv 2510.09426 | プレプリント（著者は未確認） | 五 | 2.3 節のスニペット | A2f L269–L274。A2s L15 |
| A-84 | Dai ほか 2019, Transformer-XL: Attentive Language Models Beyond a Fixed-Length Context | arXiv 1901.02860 | ACL 2019 | 五 | スニペットのみ（ablation の数値は未読） | A2f L276–L281。A2s L15 |
| A-85 | Che, Purushotham, Cho, Sontag, Liu 2018, Recurrent Neural Networks for Multivariate Time Series with Missing Values（GRU-D） | DOI 10.1038/s41598-018-24271-9、arXiv 1606.01865 | Scientific Reports | 五 | 要旨とスニペット（本文の取得は 429 の応答で失敗） | A2f L283–L289。A2s L16、L364 |
| A-86 | Zhuang, Zhang, Song, Hooker 2022, Randomness in Neural Network Training: Characterizing the Impact of Tooling | arXiv 2106.11872 | MLSys 2022 | 五・七 | 本文（1〜5 節） | A2f L293–L311。A2s L21、L22、L541、L597、L625、L708 |
| A-87 | Summers, Dinneen 2021, Nondeterminism and Instability in Neural Network Optimization | arXiv 2103.04514 | ICML 2021 | 五・七 | 本文（1〜4.1 節、Table 1・2） | A2f L313–L329。A2s L21、L597、L627 |
| A-88 | Pham, Qian, Wang, Lutellier, Rosenthal, Tan, Yu, Nagappan 2020, Problems and Opportunities in Training Deep Learning Software Systems: An Analysis of Variance | なし（IEEE Xplore 9286042。DOI は報告に無い） | ASE 2020 | 五 | 要旨のみ | A2f L331–L336。A2s L21 |
| A-89 | Bouthillier ほか 2021, Accounting for Variance in Machine Learning Benchmarks | arXiv 2103.03098 | MLSys 2021 | 五・六 | 要旨とスニペット | A2f L338–L343。A2s L21 |
| A-90 | Keller Jordan 2024, On the Variance of Neural Network Training with respect to Test Sets and Distributions | arXiv 2304.01910 | プレプリント（v4、2024-06-10） | 五 | スニペットのみ | A2f L345–L349。A2s L21 |
| A-91 | Parmar, Zhang, Zhu 2022, On Aliased Resizing and Surprising Subtleties in GAN Evaluation | arXiv 2104.11222、DOI 10.1109/CVPR52688.2022.01112 | CVPR 2022 | 五 | スニペットと公式の README | A2f L351–L356。A2s L23、L535、L563 |
| A-92 | Renard, Guedria, De Palma, Vuillerme 2020, Variability and reproducibility in deep learning for medical image segmentation | DOI 10.1038/s41598-020-69920-0 | Scientific Reports 10:13724 | 六 | 要旨と図の説明 | A2f L358–L362。A2s L24、L527 |
| A-93 | Gundersen ほか 2022, Sources of Irreproducibility in Machine Learning: A Review | arXiv 2204.07610 | プレプリント | 六 | 参考文献の部分のスニペットのみ | A2f L364–L368。A2s L21、L596 |
| A-94 | Bayat, Kirtac, Karagoz, Schwerin, Stenzel, Smit, Aspart 2022, Robustness Against Out of Distribution Video Frames in Online Surgical Workflow Recognition with Temporal Convolutional Networks | なし（報告は DOI・arXiv ID を確認できず。MIDL の公式プログラムでの掲載を確認） | MIDL 2022（short paper） | 二・七 | 要旨のみ（OpenReview の PDF は取得できず。A2s） | A2s L35–L61、L12、L511、L611 |
| A-95 | Liu, Zhu, Peng, Chen, Granados, Wang, Ourselin 2026, Stabilizing Temporal Inference Dynamics for Online Surgical Phase Recognition（StableSPR） | arXiv 2605.16387 | MICCAI 2026（査読つき。proceedings の DOI は調査時点で pending） | 二・六・七 | 本文 | A2s L63–L89、L13、L20、L513、L515、L635 |
| A-96 | Zeng, Chen, Liang, Wu, Cao, Guo 2024, Benchmarking the Robustness of Temporal Action Detection Models Against Temporal Corruptions | arXiv 2403.20254 | CVPR 2024（査読つき） | 四・六・七 | 本文 | A2s L93–L119、L14、L517、L555、L567、L611 |
| A-97 | Shukla, Marlin 2021, Multi-Time Attention Networks for Irregularly Sampled Time Series（mTAN） | arXiv 2101.10318 | ICLR 2021（査読つき） | 五 | 要旨・書誌 | A2s L123–L145、L16、L28 |
| A-98 | Baytas, Xiao, Zhang, Wang, Jain, Zhou 2017, Patient Subtyping via Time-Aware LSTM Networks（T-LSTM） | DOI 10.1145/3097983.3097997 | KDD 2017（査読つき） | 五 | 要旨・書誌 | A2s L147–L166、L16、L28、L519 |
| A-99 | Kazemi ほか 2019, Time2Vec: Learning a Vector Representation of Time | arXiv 1907.05321 | プレプリント | 五 | 要旨・書誌 | A2s L168–L186、L16、L28 |
| A-100 | Horn ほか 2020, Set Functions for Time Series（SeFT） | arXiv 1909.12064 | ICML 2020（査読つき） | 五 | 要旨 | A2s L188–L203、L16、L28 |
| A-101 | Rubanova, Chen, Duvenaud 2019, Latent ODEs for Irregularly-Sampled Time Series | arXiv 1907.03907 | NeurIPS 2019（査読つき） | 五 | 要旨 | A2s L207–L223、L17、L28、L519、L554 |
| A-102 | De Brouwer, Simm, Arany, Moreau 2019, GRU-ODE-Bayes: Continuous Modeling of Sporadically-Observed Time Series | arXiv 1905.12374 | NeurIPS 2019（査読つき） | 五 | 要旨 | A2s L225–L241、L17、L28 |
| A-103 | Kidger, Morrill, Foster, Lyons 2020, Neural Controlled Differential Equations for Irregular Time Series | arXiv 2005.08926 | NeurIPS 2020（査読つき） | 五 | 要旨。online の予測への派生論文（Neural CDEs for Online Prediction Tasks、arXiv 2106.11028。年は報告に無い）も確認（A2s） | A2s L243–L260、L17、L28、L554 |
| A-104 | Zhang ほか 2022, Raindrop: A Graph-Guided Network for Irregularly Sampled Multivariate Time Series | arXiv 2110.05357 | ICLR 2022（査読つき） | 五 | 要旨 | A2s L264–L282、L18、L28 |
| A-105 | ContiFormer: Continuous-Time Transformer for Irregular Time Series Modeling（著者と年は報告が確定できず。報告は 2023〜24、NeurIPS 系と書く） | arXiv 2402.10635 | NeurIPS 系（報告の記載） | 五 | 要旨 | A2s L284–L298、L18、L28 |
| A-106 | Smith, Warrington, Linderman 2023, Simplified State Space Layers for Sequence Modeling（S5） | arXiv 2208.04933 | ICLR 2023（査読つき） | 五（否定的な側面は TIDES〔A-107〕の解析として報告が書く） | 要旨、実装の appendix、後続の TIDES による機構の比較 | A2s L302–L322、L19、L26、L28、L519、L553 |
| A-107 | Soydan, Bessa, Mohr, Barreira 2026, TIDES: Implicit Time-Awareness in Selective State Space Models | arXiv 2605.09742 | プレプリント | 五・七 | 本文 | A2s L324–L348、L19、L26、L519、L553、L583 |
| A-108 | Jung, Kim, Park 2026, MASCIT: A Mask-Aware State Space Classifier for Naturally Irregular Time Series | arXiv 2609.34409 | プレプリント | 五・七 | 本文 | A2s L350–L374、L18、L19、L521、L552、L583 |
| A-109 | Chen, Wen, Shi, Lin, Rajbahadur, Jiang 2022, Towards Training Reproducible Deep Learning Models | arXiv 2202.02326、DOI 10.1145/3510003.3510163 | ICSE 2022（査読つき） | 五・六・七 | 本文 | A2s L378–L404、L21、L22、L28、L559、L623、L708 |
| A-110 | Coakley, Kirkpatrick, Gundersen 2022, Examining the Effect of Implementation Factors on Deep Learning Reproducibility | DOI 10.1109/eScience55777.2022.00056、arXiv 2312.06633 | IEEE eScience 2022（arXiv 掲載は 2023） | 五・六 | 本文 2 ページ | A2s L406–L423、L21、L596、L599、L682 |
| A-111 | Shahriari, Ramler, Fischer 2022, How Do Deep-Learning Framework Versions Affect the Reproducibility of Neural Network Models? | DOI 10.3390/make4040045 | Machine Learning and Knowledge Extraction 4(4), 888–911（査読つき） | 五・六 | 要旨・本文の冒頭 | A2s L425–L439、L687、L720 |
| A-112 | Pham, Kim, Tan, Yu, Nagappan 2021, DEVIATE: A Deep Learning Variance Testing Framework | DOI 10.1109/ASE51524.2021.9678540 | ASE 2021（査読つき） | 五・六 | 要旨・書誌 | A2s L441–L453、L21、L28、L596、L682 |
| A-113 | Ravi, Goel, Davis, Thiruvathukal 2025, Improving the Reproducibility of Deep Learning Software: An Initial Investigation through a Case Study Analysis | arXiv 2505.03165 | プレプリント | 六・七 | 要旨・HTML の case study の記述 | A2s L455–L469、L541、L597、L710 |
| A-114 | Shanmugavelu, Taillefumier, Culver, Hernandez, Coletti, Sedova 2024, Impacts of floating-point non-associativity on reproducibility for HPC and deep learning applications | arXiv 2408.05148 | プレプリント | 五・六・七 | 本文 | A2s L471–L486、L22、L529、L560、L720 |
| A-115 | Xie, Zhang, Chen 2025, RepDL: Bit-level Reproducible Deep Learning Training and Inference | arXiv 2510.09180 | プレプリント | 五・六 | 要旨・HTML | A2s L488–L503、L21、L22、L704 |

---

## 3. 近さ（距離の軸）

| ID | 視点 | ドメイン | 課題の形 | 推論の規約 | データ規模 | モデルの状態（凍結の範囲） |
|---|---|---|---|---|---|---|
| A-01 | 一人称（術者の頭部の Tobii カメラ。A2c） | 開放手術（10 術式、術者 8 人） | RGB の映像（と視線）から 9 工程をフレームごとに予測する。GGMAE は 10 フレームのクリップ（224²）を入力にする（A2c、A3c、A3g） | 不明（全報告）。クリップの中で予測する時刻の位置と、比較手法を online で動かしたかの記載が無い。A2g は TeCNO を「構造は因果的だが、この表の評価規約の明記は不十分」と書く | 21 本（分割 14／2／5、交差検証なし）。25 fps・計 28 時間を 0.5 fps に間引き、個人を特定できるフレームを除いた。除いた後は平均 46 分・計 15 時間、注釈 27,694 フレーム（A2c）。本文は「20 videos」と書き、分割の和は 21（A2f、A3c、A3g）。A2g は「v1 は 21 本、後の版に 20 本の記述と 14／2／5 が同居」と書く。A2s も原論文の記載として、元映像 25 fps・計約 28 時間、0.5 fps へ間引き、患者の顔のぼかしとその他の個人情報を含むフレームの除外を経て約 15 時間、21 本・27,694 注釈フレーム・9 工程と書き、配布物での区間ごとの連番の振り直しは原論文の記述ではなく依頼者の確認した事実として区別する（A2s L3） | GGMAE は事前学習 800 epoch の後に全体を fine-tune（fine-tune 100 epoch、batch 256、マスク比 90%。A3g）。Table 2 は全行 ViT-S。比較手法の学習の状態は不明（A2c） |
| A-02 | 混在（一人称を含む） | 手術全般（低侵襲・開放・顕微鏡） | 事前学習の後、凍結した backbone に attentive probe（4 ブロック、16 の cross-attention head。A3g）を載せて工程などを分類する。A2c は 64 フレームのクリップを分類と書く | README によれば 64 フレーム（1 fps）の窓の最後のフレームを予測する online（A3c）。ほかの報告は不明（A2g は因果性を保証する記述を確認できずと書く） | 事前学習は SurgMotion-15M、約 3,658 時間・50 ソース。Table 1 の内訳（A3c、A3g）: 神経外科 2,860.85 h、AVOS 125.16 h（A3c は開放手術、A3g は abdominal と書く）、眼科 230.76 h（顕微鏡）、胃 252.10 h、胆嚢 77.51 h、大腸内視鏡 45 h、婦人科 23.12 h、泌尿器 20.45 h、肝 6.95 h、手技訓練 5.27 h、気管支鏡 50 h（非公開）、EgoSurgery 21 本・10.55 h（区分は「Breast surgery」「Mixed」。A2c、A3c） | 下流は backbone を凍結し probe だけを学ぶ。16 のヘッドを同時に学び最良の値を報告（A2c、A3c） |
| A-03 | 一人称 | 開放手術 | 器具 15 種・手 4 種の box 検出（フレーム単位） | 該当なし（フレーム単位の検出） | EgoSurgery-Phase を「21 videos、10 術式、15 時間、術者 8 人」と記載し、うち 15 本・15,437 枚に注釈（A2f） | 報告に記載なし |
| A-04 | 一人称 | 開放手術 | 手と器具の画素の分割 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-05 | 一人称（EgoSurgery で評価） | 開放手術 | 工程認識（詳細は報告に記載なし） | 不明 | EgoSurgery | 報告に記載なし |
| A-06 | 一人称 | 開放手術 | データの配布 | 該当なし | 該当なし | 該当なし |
| A-07 | 旧地図に記載なし（腹腔鏡） | 手術（Cholec80、Cholec51） | ResNet50 の特徴から多段の因果的な TCN で工程を予測 | 因果的と明記（旧地図） | Cholec80 40／8／32、Cholec51 25／8／18 | ResNet50 の特徴の上に TCN を学ぶ（重みつき CE、Adam 5e-4、25 epoch） |
| A-08 | 旧地図に記載なし（腹腔鏡） | 手術（Cholec80、M2CAI16） | 凍結した ResNet50 の特徴と TeCNO の埋め込みを、過去 30 step だけで Transformer で集約 | 過去のみ（30 step） | Cholec80 40／40、M2CAI16 27／14、1 fps | ResNet50 は ImageNet で固定 |
| A-09 | 旧地図に記載なし（腹腔鏡） | 手術（Cholec80、AutoLaparo） | ViT-B/16 のフレーム特徴から長短の Transformer で工程を予測 | online（現時刻までの履歴を処理する設計）。attention のマスクの種類は未確認（旧地図） | Cholec80 40／40、AutoLaparo 10／4／7、1 fps | ViT-B/16、ImageNet-1K で事前学習（利用者が掲載版で確認） |
| A-10 | 旧地図に記載なし（腹腔鏡） | 手術（Cholec80） | 共有の CNN で器具の在否と工程を同時に学び、HMM で工程を出す | online と offline の両方を HMM で評価 | Cholec80 40／40 | AlexNet、ImageNet で初期化 |
| A-11 | 腹腔鏡 | 手術（Cholec80、M2CAI） | CNN の特徴と長期の記憶の bank で工程を予測 | 長期の時間文脈を使う。厳密な因果性は実装ごとに確かめる必要がある（A2g） | Cholec80、M2CAI | CNN の特徴＋時間の記憶 |
| A-12 | 腹腔鏡 | 手術（Cholec80、AutoLaparo） | 二段階。特徴抽出器を L=1・8・64 フレームの時間文脈で学んで凍結し、その上で時間モデルを学ぶ | online と offline の両方 | Cholec80（32:8:40 と 40:40）、AutoLaparo | 抽出器は凍結。抽出器の隠れ状態の持ち越し（CHE）も試す |
| A-13 | 腹腔鏡（一般の行動分割も） | 手術、一般の行動分割（GTEA を含む） | フレームの特徴から多尺度の時間の self／cross-attention で工程・行動を予測 | MS-ASCT は online（因果的）、MS-AST は offline | Cholec80 など。GTEA でも評価 | ResNet50 または EfficientNetV2-M の特徴抽出器＋時間モデル |
| A-14 | 腹腔鏡 | 手術（Cholec80、AutoLaparo） | 疎なフレームの列（T=16、R=4）から階層的な時間の attention で工程を予測 | online の滑り窓（A2c）。窓の最後のフレームを予測する規約（A3c）。A2g は要旨だけでは厳密な因果性を判定できないと書く | Cholec80 は 40／40、AutoLaparo は 10／4／7 | end-to-end の映像 Transformer |
| A-15 | 腹腔鏡 | 手術（BernBypass70、Cholec80、AutoLaparo） | 長時間の文脈と記憶を持つ Transformer で工程を予測 | online。境界の緩和をやめた評価（A3c） | 3 データとも 1 fps。AutoLaparo は学習 10 本 | end-to-end で学習 |
| A-16 | 腹腔鏡・顕微鏡（CATARACTS） | 手術（Cholec80、CATARACTS） | ResNet34 の特徴（A2c）と長い系列を Mamba の decoder で工程に。補助課題に anticipation | 双方向の Mamba の decoder（未来を使う。A2c、A2g） | Cholec80、CATARACTS | 空間と時間を一段で同時に学ぶ（A2g） |
| A-17 | 内視鏡（ESD） | 手術（ESD385、Cholec80） | 空間時間の Mamba の枠組み（Scaled Residual TranMamba）と時間のサンプリングの工夫で工程を予測 | A2c は著者の主張として online。A2g は実時間を動機とするが、予測時刻に対する因果性は取得範囲で確認できず online は不明 | ESD385、Cholec80 | 報告に記載なし |
| A-18 | 腹腔鏡（A2c はロボット手術と書く） | 手術（Cholec80、MICCAI2016、HeiChole） | 間引いた全手術の映像 → 時間的に一貫した特徴 → 局所と大域の SSM → 工程と進捗 | 因果的な版を持ち、著者は全動画の online 工程認識と位置づける。文脈を使う双方向の版も別にある（A2g） | Cholec80、MICCAI2016（41 本、27／4／10 と書き最終の結果は 14 本で報告）、HeiChole | 二段階。時空間の事前学習を 1 epoch だけ行い時間的に一貫した抽出器を作る（A2c）。その上に SSM の頭を学ぶ（A2g） |
| A-19 | 内視鏡・腹腔鏡ほか | 手術（7 ベンチマーク。HeiCo は 30 本） | Mamba2 の SSD を二経路にし、遷移の強さに応じた時間刻みと Cayley 回転を使う | online・過去のみ（著者の主張。A2c）。窓の最後のフレームを予測する規約（A3c） | 7 ベンチマーク（Cholec80、AutoLaparo、HeiCo ほか） | ConvNeXt を一部凍結（A2c） |
| A-20 | 報告に記載なし | 手術 | 工程認識（SSM） | online を明示（A2g） | 報告に記載なし | 報告に記載なし |
| A-21 | 手術映像 | 手術（Cholec80、Cataract など） | フレームの分類ではなく工程の区間の候補（proposal）を生成する | online と offline を同じ構造で行う。online は流れてくる過去を反転・中央の複製・間引きで「擬似的に完全な系列」にし、現在の中心の候補を採る。offline は過去の予測を後から更新する（A2g） | Cholec80、Cataract など。詳細は不明（A2g） | 時間の検出器 |
| A-22 | 報告に記載なし | 手術 | 工程認識（クリップのモデル） | T=16 の窓をずらして online で評価。窓の最後のフレームを予測（A3c） | 報告に記載なし | 報告に記載なし |
| A-23 | GTEA は一人称。50Salads・Breakfast は一人称でない | 非医療（手順の動画） | 流れてくる手順の動画の密な行動分割 | strict-online（現在のフレームまで）と semi-online（窓ごとにまとめて予測）を分けて報告（A2g）。記憶は動画ごとで、動画の境で初期化する前提。区間の境の扱いは対象外（A2f） | GTEA 28 本・11 行動、50Salads 50 本・17 行動、Breakfast 1,712 本・48 行動（A2g）。I3D の特徴 | I3D の特徴は凍結。因果的な TCN＋GRU＋文脈を意識した特徴の増強＋適応的な記憶 |
| A-24 | 一人称 | 非医療の手順（GTEA、EgoProceL、EgoPER） | online の密な行動分割 | 因果的な backbone で過去のみ。因果的にすると全系列の predict と 1 フレームずつの predict_online が同じ結果になる（公式コード。A2g） | GTEA、EgoProceL、EgoPER | I3D は凍結。MS-TCN・ASFormer を因果的にし、行動の進捗の予測（APP）とタスクグラフ（TG）を足す |
| A-25 | 一人称でない | 非医療 | フレームの特徴から毎時刻の行動を予測（GRU） | online | THUMOS'14、TVSeries、FineAction | 特徴は凍結 |
| A-26 | GTEA は頭部カメラ（28 動画）。50Salads は一人称でない | 非医療（50Salads、GTEA、Breakfast） | I3D の特徴から行動のラベル | 因果的でない（acausal と明記） | 50Salads 50 本ほか | 特徴は凍結 |
| A-27 | 一人称でない（GTEA を含む） | 非医療（50Salads、GTEA、Breakfast） | I3D の特徴から局所・階層の attention で行動を分割 | 全系列を見る（因果的な版なし） | 50Salads、GTEA、Breakfast | 特徴は凍結 |
| A-28 | 一人称でない | 非医療（THUMOS'14、TVSeries、HACS） | 長期（512 s）と短期（8 s）の記憶の Transformer で online の行動検出 | online | THUMOS'14、TVSeries、HACS | 旧地図に記載なし |
| A-29 | 一人称でないものと一人称（GTEA） | 非医療 | 行動分割 | offline | 50Salads、Breakfast、GTEA | 報告に記載なし |
| A-30 | 一人称（学習で三人称も使う） | 非医療の熟練行動 | (a) 切り出したクリップから 689 の keystep を分類（クリップ単位）、(b) ストリームで毎フレーム 5 fps の keystep の予測（online）（A2f） | (a) はクリップ単位、(b) は online | Ego-Exo4D | 報告に記載なし |
| A-31 | 一人称 | 非医療 | 一人称の映像を手を中心に安定化した映像に変えて keystep を認識 | 報告に記載なし | Ego-Exo4D keystep | 報告に記載なし |
| A-32 | 一人称 | 非医療 | online の行動分割のベンチマーク | online | test の注釈が非公開のため validation を test に転用し、学習データを 80:20 に分けた。シナリオごとに学んで平均 | 報告に記載なし |
| A-33 | 一般の映像 | 非医療 | online のハイライト検出 | online（先を見ない） | 報告に記載なし | 報告に記載なし |
| A-34 | 腹腔鏡 | 手術（Cholec80 80 本・7 工程、HeiChole） | ResNet-50 で MoCo v2、SimCLR、DINO、SwAV を比べ、ハイパーパラメータ・ラベル量・無ラベルのデータ量を調べる | 時間ヘッドは TCN（因果は記載なし。旧地図） | Cholec80 のラベル 40／10／5 本、HeiChole 24／4／2。量の実験では Cholec80 の学習用の全体で SSL を行い、ラベルを 40／10／5 本に減らす（A3g） | 手術データで SSL の後に fine-tune |
| A-35 | 腹腔鏡・ロボット | 手術 | 手術データの多様性を変えた SSL | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-36 | 腹腔鏡・ロボット | 手術（23 超の術式） | DINO の SSL で手術の基盤モデルを学ぶ | 該当なし（下流の評価の規約は報告に記載なし） | 4,598 超の動画、4,711,024 フレーム、23 超の術式。YouTube の 2,074,234 フレームは低侵襲でない手術と体外のフレームを除いた（A3g） | ImageNet の重みから手術データで DINO を続ける（A3g）。主モデルは CAFormer-S18（24.3M）。ConvNeXt・PVTv2 も |
| A-37 | 内視鏡・腹腔鏡 | 手術 | Endo700k で MAE の事前学習をした ViT-B | 下流の工程は TeCNO の二段目（A3g） | Endo700k（公開の内視鏡データ 9 個、70 万枚超） | 報告に記載なし |
| A-38 | 手術室（OR-AR）、顕微鏡（Cataract-101） | 手術 | 長い手術動画の MAE。空間時間のトークンを多く取るマスク | offline の Bi-GRU（旧地図） | OR-AR 820 動画、Cataract-101 101 動画（旧地図） | ViT-B |
| A-39 | 内視鏡・腹腔鏡 | 手術・消化器内視鏡 | 教師と生徒の自己蒸留で映像の内視鏡基盤モデル | 報告に記載なし | 公開 9 個＋非公開 1 個（Renji 病院 Baoshan 分院）、33K 超のクリップ、最大約 5M フレーム。大腸内視鏡・胃内視鏡・腹腔鏡（A3c、A3g） | ViT-B/16 系、121M パラメータ（A3g） |
| A-40 | ロボット・腹腔鏡 | 手術（一般外科） | 次のフレームの予測で映像の基盤モデルを学ぶ | 実時間の応用を意識（A3g） | GenSurgery 680 時間、28 術式（LEMON の比較表では 3,182 本。A3g） | EfficientViT 系。後続の比較では EfficientViT-M5、12.1M（A3g） |
| A-41 | 内視鏡・腹腔鏡・ロボット（顕微鏡は評価だけ） | 手術（20 超の術式、10 超の部位） | 映像の手術基盤モデル（tube のマスク）。下流はクリップ（16 フレーム、間隔 4、1 fps）から工程（A3c） | 不明（A3c） | SurgPub は 8 データセット・274 本・約 1.20M フレーム（Cholec80、M2CAI16、HeiChole、PitVis、PSI-AVA、AutoLaparo、BernBypass70、StrasBypass70）。SurgWeb は 3,376 本・約 2.35M フレーム（A3c、A3g）。SurgWeb は術中の内視鏡の視野だけを残し外部カメラの視野を除いた（A3g）。SurgWeb の区分に「Others 1,554 本・974,770 フレーム」があり中身は不明（A3c） | ViT-B（encoder 87.4M、埋め込み 768）、ランダムに初期化してスクラッチから事前学習（A3c、A3g）。下流は end-to-end の fine-tune（A3c） |
| A-42 | 内視鏡 | 手術（35 術式） | 画像の手術基盤モデル（蒸留の目的） | 報告に記載なし | 4K 本・938 時間・35 術式、内視鏡の系統だけ（A3c）。事前学習の総本数は A3g は不明 | ConvNeXt-Large（学習の命令から確認。出力 1536 次元。A3c）。主結果は ConvNeXt-L、ViT-L も ablation（A3g） |
| A-43 | 内視鏡 | 手術・消化器内視鏡 | 空間は双方向の Mamba、時間は因果的な Mamba。マスクの再構成と一般の映像基盤モデルの特徴への合わせ込みで階層的に事前学習 | 時間方向は因果的（A3g） | A3c は MIX12（内視鏡 12 データセット、74,828 クリップ、11,303,853 フレーム。Table 1）と書く。A3g は MICCAI の公式頁が「12 endoscopic videos」と書くと書く | 教師は VideoMamba-S（α=0.25。A3c） |
| A-44 | 講義の手術動画（視点の集計なし） | 手術（肝胆膵、一般・消化器、肥満、ヘルニア、大腸ほか） | 手術の講義の動画と書き起こしの文の対比学習 | 報告に記載なし | 1,326 本の手術の講義の動画（A3g） | 映像と文の encoder |
| A-45 | 消化器内視鏡 | 消化器内視鏡（手術でない） | DINO で約 5M 枚の消化器内視鏡の画像を事前学習 | 報告に記載なし | 約 5M 枚 | ResNet50（23.5M）と ViT-S（21.1M）の版（A3g） |
| A-46 | 腹腔鏡 | 手術 | MSN による SSL（A3c） | 報告に記載なし | 非公開の腹腔鏡 7,877 本・約 23.3M フレーム、5 超の術式（後続の論文の記述。A3c、A3g） | ViT-L |
| A-47 | 腹腔鏡・顕微鏡 | 手術（Cholec80、AutoLaparo、Cataract-101） | 凍結した ViT-B／L に adapter と decoder だけを学ぶ（16×4 のクリップ） | 因果は記載なし（旧地図） | Cholec80 40／40、AutoLaparo 10／4／7、Cataract-101 | ViT は凍結、adapter と decoder だけを学ぶ |
| A-48 | 主に俯瞰。頭部装着カメラの映像も一部を含む（第三者の報告による。A3c） | 開放手術（23 術式、50 か国） | 開放手術の大規模な動画の集め。注釈つきの 343 本は毎秒の cutting／tying／suturing／background のラベル（注釈は arXiv 2112.07219。A3c） | 該当なし | YouTube の検索結果 9,197 件から 1,997 本の開放手術の動画を手で選んだ（A3c）。SurgMotion の事前学習に 125.16 h が入る（A-02） | 該当なし |
| A-49 | 顕微鏡（眼科） | 眼科手術 | 1.1M クリップ・144 術式の映像 Transformer。蒸留して顕微鏡の装置に載せる | 報告に記載なし | 1.1M クリップ、144 術式 | 報告に記載なし |
| A-50 | ロボット手術 | 手術 | 手術の基盤モデルの凍結と部分的な適応の比較 | 報告に記載なし | GraSP ほか | 凍結と上位 4 ブロックだけの fine-tune |
| A-51 | 低侵襲手術 | 手術 | 手術画像で事前学習した MIS-DINOv2 と既存の手術の基盤モデルの比較 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-52 | 手術 | 手術 | 手術画像で短く学んだ MAE・DINOv2 と公開の DINOv3 の重みの比較 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-53 | 一般の映像 | 非医療 | 映像のマスク再構成（tube のマスク） | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-54 | 一般の映像 | 非医療 | 二重のマスクの映像 MAE | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-55 | 一般の映像 | 非医療 | 映像のマスクの事前学習（動きの事前知識） | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-56 | 一般の画像 | 非医療 | 画像の基盤モデル（映像のモデルではない。A3g） | 該当なし | 報告に記載なし | 報告に記載なし |
| A-57 | 一般の映像 | 非医療 | 潜在空間の予測による映像の SSL | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-58 | 一人称 | 非医療（Ego4D、EPIC） | 一人称の映像と言語の事前学習 | offline（旧地図） | Ego4D から作った EgoClip（3.8M の clip-text の組、映像 2.9K 時間分。A3c） | TimeSformer、ImageNet-21K で初期化、4 フレーム 224（旧地図） |
| A-59 | 一人称 | 非医療 | 一人称の映像と言語の事前学習 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-60 | 一人称 | 非医療 | 一般の事前学習の backbone を Ego4D で fine-tune | 報告に記載なし | Ego4D | 一般の backbone を fine-tune |
| A-61 | 一人称（三人称から一人称への蒸留） | 非医療（Charades-Ego、EPIC-100） | 三人称の映像の表現を一人称へ移す | 旧地図に記載なし | Charades-Ego、EPIC-100 | 旧地図に記載なし |
| A-62 | 一人称（頭部カメラ、視線と手の mask つき） | 非医療 | 視線と行動の同時のモデル | 旧地図に記載なし | EGTEA Gaze+ | 旧地図に記載なし |
| A-63 | 一人称 | 非医療（台所） | データセット | 該当なし | 55 時間、参加者 32 人 | 該当なし |
| A-64 | 一般の映像 | 非医療（映像と言語の検索） | 物体の領域を使って物体で誘導したマスクをかける | 該当なし | 報告に記載なし | 報告に記載なし |
| A-65 | 一人称 | 非医療（EGTEA） | 視線を潜在の注意として扱い、確率のモデルで教師に使う | 報告に記載なし | EGTEA | 報告に記載なし |
| A-66 | 一人称 | 非医療 | 視線を注意機構に組み込む | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-67 | 一人称 | 非医療 | 推論時に視線を cross-modal attention で融合する | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-68 | 一人称（GTEA）から手術（JIGSAWS）へ | 手術（訓練の課題） | GTEA で学んだ視線の予測を JIGSAWS に移し、注意の教師に使う | 報告に記載なし | GTEA、JIGSAWS | 報告に記載なし |
| A-69 | 一人称 | 非医療 | 視線で場面グラフを枝刈りする | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-70 | 内視鏡 | 手術・内視鏡 | EVA-02 を内視鏡画像で継続事前学習 | 報告に記載なし | 報告に記載なし | 一般の重みから継続 |
| A-71 | 該当なし（音響） | 非医療（鳥類の音響） | 領域内のデータでの継続 SSL と、一般の重みからの教師ありの fine-tune の比較 | 該当なし | 中規模 | 報告に記載なし |
| A-72 | 医用画像 | その他の医療 | 医用画像の SSL の詳細の検討 | 該当なし | 報告に記載なし | 報告に記載なし |
| A-73 | 報告に記載なし | 医療 | 基盤モデルの臨床への準備の議論 | 該当なし | 報告に記載なし | 報告に記載なし |
| A-74 | 腹腔鏡 | 手術（Cholec80） | 工程認識の論文の間の指標・分割・評価の規約の違いの分析。SV-RCNet の再実装 | online の結果を整理 | Cholec80（32:8:40、40:40） | 該当なし |
| A-75 | 腹腔鏡（GTEA・50Salads も） | 手術、非医療 | フレームの列から CNN-LSTM で工程を予測 | online | Cholec80 80 本・7 工程。AutoLaparo、CATARACTS、GTEA、50Salads も | end-to-end（一部を凍結する設定あり） |
| A-76 | 腹腔鏡 | 手術（Cholec80） | 2016〜2025 年の Cholec80 の論文 50 本の評価指標の系統的な分析（PRISMA） | 該当なし | 研究 50 本 | 該当なし |
| A-77 | 内視鏡 | 手術（ESD） | 拡散モデルによる工程認識 | 報告に記載なし | ESD | 報告に記載なし |
| A-78 | 内視鏡・腹腔鏡 | 手術 | フレームから体外の場面を判定する | フレーム単位 | 社内の 12 術式と外部の多施設のデータ 2 つ | 独立に学習 |
| A-79 | 腹腔鏡 | 手術（胃バイパス） | 工程とステップの予測 | 不明 | StrasBypass70（Strasbourg）と BernBypass70（Bern）の 140 本、12 工程・46 ステップ | 報告に記載なし |
| A-80 | ロボットの内視鏡 | 手術（6 術式） | 体外の判定とぼかし（実時間） | online（実時間） | 4 種のロボットで撮った 63 本、496,828 画像 | 報告に記載なし |
| A-81 | 腹腔鏡 | 手術 | 秒単位で体外・無関係の区間を検出（半教師ありで反復学習） | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-82 | 該当なし | 非医療（言語） | 文書を詰めた系列で次のトークンを予測 | 因果的 | 150B トークン、1.3B パラメータ、文脈長 2K と 8K | 一から学習 |
| A-83 | 該当なし | 非医療（言語） | 系列を詰めた事前学習のマスクの比較 | 因果的 | 報告に記載なし | 小さな代理のモデル |
| A-84 | 該当なし | 非医療（言語） | 言語モデル | 因果的 | WikiText-103 ほか | 直前のセグメントの状態を勾配を止めて再利用 |
| A-85 | 該当なし | その他の医療（ICU の時系列） | 欠けのある時系列の分類 | 因果的 | ICU の時系列 | 報告に記載なし |
| A-86 | 該当なし | 非医療（画像分類） | 画像分類（CIFAR-10／100、ImageNet） | 該当なし | CIFAR-10／100、ImageNet | 一から学習 |
| A-87 | 該当なし | 非医療（画像分類、言語） | ResNet-14 の CIFAR-10、QRNN の PTB | 該当なし | CIFAR-10、PTB | 一から学習 |
| A-88 | 該当なし | 非医療（画像分類、3 データセット × 6 ネットワーク） | 同一の学習の繰り返しの分散の分析 | 該当なし | 3 データセット | 一から学習 |
| A-89 | 該当なし | 医療を含む 5 課題 | ベンチマークの分散の源の分解 | 該当なし | 5 課題 | 該当なし |
| A-90 | 該当なし | 非医療（CIFAR-10、ImageNet） | 学習の分散の分析 | 該当なし | CIFAR-10 | 一から学習 |
| A-91 | 該当なし | 非医療（生成モデルの評価） | リサイズの実装の差が FID に与える影響 | 該当なし | 報告に記載なし | 該当なし |
| A-92 | 該当なし | その他の医療（医用画像の分割） | 変動の源の総説 | 該当なし | 該当なし | 該当なし |
| A-93 | 該当なし | 非医療 | 再現できない源の総説 | 該当なし | 該当なし | 該当なし |
| A-94 | 内視鏡・腹腔鏡 | 低侵襲手術（腹腔鏡下胆嚢摘出） | フレームの特徴を時間畳み込みに与える online の工程認識。体外（OOB）のフレームが途中に挿入される実運用の条件 | online | 「large scale real-world dataset」（要旨の記載）。本数・時間・クラス数は不明 | 空間の抽出器＋時間モデルの二段。凍結の範囲は不明 |
| A-95 | 腹腔鏡 | 低侵襲手術 | online の工程認識で、時間方向の誤りの連鎖と短時間の工程の flicker を、学習の損失（TEC）と因果的な推論機構（EGTP）で抑える | online、過去のみ | Cholec80 80 本・7 工程（40 train／40 test）、AutoLaparo 21 本・7 工程（10 train／4 validation／7 test） | Trans-SVNet、SKiT、Surgformer の公式実装に plug-in |
| A-96 | 三人称・一般映像 | 非医療 | untrimmed 映像の時間的行動検出。black frame、motion blur、overexposure、occlusion、packet loss を一部のフレームに入れ、時間的な連続性を破る | ベンチマークに因果の制約はない（online ではない） | THUMOS14-C は注釈つきの test 213 本・20 のスポーツのクラス、ActivityNet-v1.3-C は約 5K の validation 本・200 クラス | BasicTAD、E2E-TAD、TemporalMaxer、ActionFormer、AFSD、TriDet、VSGN。end-to-end と凍結した特徴抽出器の双方 |
| A-97 | 該当なし | 非映像の時系列 | 不規則な観測の時刻を連続時間の埋め込みと注意で参照し、固定した参照時刻の上の表現に集約して分類・補間 | 原論文の主要な評価は厳密な online のフレームごとの認識ではない | 不明（本文の表は未確認） | end-to-end |
| A-98 | 該当なし | 医療の電子カルテ | LSTM の過去の記憶を経過時間に応じて減衰させ、不規則な受診の間隔を扱う | 因果的な再帰の形だが、フレームごとの online のベンチマークではない | 不明（本文未確認） | end-to-end |
| A-99 | 該当なし | 該当なし | スカラーの時刻を、学習できる周期・非周期の成分を持つベクトルに変換し、既存の系列モデルに時刻の情報として足す | backbone に依存 | 不明 | 時刻の encoder を一緒に学習 |
| A-100 | 該当なし | 非映像の不規則な時系列 | 不規則な観測を集合として符号化し、固定の時間刻みへの逐次の補間を必須としない | online の監視に展開できるとされるが、主要なベンチマークの厳密な因果の条件は不明 | 不明 | end-to-end |
| A-101 | 該当なし | 該当なし | ODE-RNN は観測の間を ODE で連続に発展させ、観測時に再帰の更新をする。Latent ODE は潜在の軌道そのものを連続時間で表す | ODE-RNN の部分は因果的に構成できる。Latent ODE の推論ネットワークは用途により系列全体を見るため、原論文の全体を online と同一視できない（A2s） | 不明 | 一緒に学習 |
| A-102 | 該当なし | 該当なし | 連続の GRU のダイナミクスを観測の間で進め、観測時にベイズ的に更新 | 因果的なフィルタリングの形に近い | 不明（本文の表は未確認） | 一緒に学習 |
| A-103 | 該当なし | 該当なし | timestamp つきの観測を補間した path として扱い、その path で隠れ状態を連続に駆動する | 原論文は用途に依存。派生研究に明示的な online の予測がある | 不明 | 一緒に学習 |
| A-104 | 該当なし | 該当なし | 非同期に観測される多変量のチャネルの時刻とセンサの関係を、グラフで導く注意で統合 | 系列の分類であり、厳密なフレームごとの online ではない | 不明（本文未確認） | 一緒に学習 |
| A-105 | 該当なし | 該当なし | Transformer の注意を連続時間の表現に拡張し、不規則な timestamp を扱う | 原論文のベンチマークは厳密な online の映像認識ではない | 詳細不明 | 詳細不明 |
| A-106 | 該当なし | 該当なし | S4 の多数の SISO の SSM を一つの MIMO の連続時間 SSM に整理し、parallel scan を使う | 再帰として因果的な状態の更新ができる。原論文のベンチマークは手術の online 認識ではない | Long Range Arena ほか（表番号は未確認のため数値なし） | 一緒に学習 |
| A-107 | 該当なし | 該当なし | S5 の物理的な Δ と Mamba の入力依存の選択性を両立させる選択的な SSM。Δ を学習したゲートにせず、実観測の間隔のまま離散化に使う | 因果的な再帰が可能。分類・回帰のベンチマーク自体はフレームごとの online ではない | UEA の分類、Physiome-ODE、統制した Fading Flash | 一緒に学習 |
| A-108 | 該当なし | 該当なし | 観測のマスクを選択的な SSM と pooling に与え、欠け・不均等・不揃いの時系列を分類 | backbone は浅い単方向だが、分類は系列水準の pooling の後なので、EgoSurgery のフレームごとの online の出力とは違う | PYRREGULAR の 34 データセット、12 の既発表の基準 | 一緒に学習 |
| A-109 | 該当なし | 一般の深層学習 | ソフトウェアの乱数と GPU のハードウェアの非決定性を分け、record-and-replay と、決定性の無い演算に対して決定性を固定するパッチを組み合わせる | 学習の再現性の研究 | 公開の 6 モデルと商用の 1 モデル。GPU は Tesla P100-16GB。TensorFlow 1.14 では CUDA 10.0.130／cuDNN 7.5.1、TensorFlow 2.1 では CUDA 10.1／cuDNN 7.6。各 setup 16 runs | 一から学習 |
| A-110 | 該当なし | 一般の深層学習 | ハードウェア・ソフトウェアの環境を変えたときの、決定性を固定した設定の深層学習の例の結果の変動 | 該当なし | 3 つの実験 × 5 回の反復 × 13 のハードウェア環境 × 4 のソフトウェア環境、計 780 の結果 | 簡単な CNN／MNIST、双方向 LSTM／IMDB、全結合／クレジットカードの不正検知 |
| A-111 | 該当なし | 一般の深層学習 | TensorFlow／PyTorch の版を変えたときの学習済みモデルの性能の再現性 | 該当なし | 報告に記載なし。GPU の要因を避けるため CPU の学習に限定（A2s） | 報告に記載なし |
| A-112 | 該当なし | 一般の深層学習 | 深層学習の学習の散らばりを自動で測り、統計的な判定を行う framework | 該当なし | 不明（本文未読） | 不明 |
| A-113 | 該当なし | 一般の深層学習 | ソフトウェア環境、学習のパイプライン、データ処理を固定・文書化した再現性の case study | 該当なし | TRUNK モデル（報告の記載） | 報告に記載なし |
| A-114 | 該当なし | HPC・一般の深層学習 | 浮動小数点の非結合性、GPU の atomic／reduction の順序、PyTorch の決定性のオプションによる run 間の変動 | 該当なし | NVIDIA／AMD／Groq を含む並列ハードウェアの microbenchmark と、深層学習に関する検証 | 該当なし |
| A-115 | 該当なし | 一般の深層学習 | 乱数の統制に加え、浮動小数点の計算の correct rounding と順序の不変性を実装し、同じ・異なる CPU／GPU の間でビット単位の一致を狙う | 該当なし | 報告に記載なし | 報告に記載なし |

---

## 4. 手法の位置

| ID | 系統 | 現役度（報告）と理由 | どのベンチマークの話か | 本研究の条件で測られたか（少数動画／online／一人称） |
|---|---|---|---|---|
| A-01 | 対象データ上の映像 MAE（マスク方式の改変）、視線でマスクを選ぶ事前学習。Table 1 は時間モデルの比較を含む（PhaseLSTM、PhaseNet、TeCNO、Trans-SVNet、NETE） | A2c は EgoSurgery の原典の基準値の群とし、ほかに原典の基準値の群は無いと書く。A2g は定番の基準（EgoSurgery の一次の基準）。A3c は新興（EgoSurgery の Table 1・2 で最上位、著者以外の追試なし）。A3g は不明（同条件の査読つき独立の再現を確認できず）。A2s は EgoSurgery の系列を「新興: EgoSurgery benchmark」とし、Phase 論文が 21 本・15 h・9 工程の基準を定義すると書く（A2s L11） | EgoSurgery-Phase（公式分割 14／2／5） | 少数動画・一人称で測った。online かは不明 |
| A-02 | 映像の手術基盤モデル（V-JEPA 系。動きで損失に重みをつける、空間時間の親和性の自己蒸留、特徴の多様性の正則化。A3g） | A2c は SOTA 級（EgoSurgery、Table 3。プレプリント）。A2f・A2g・A3c は新興（自身の表で最上位、著者以外の採用は未確認） | EgoSurgery、PitVis、Cholec80、AutoLaparo、CholecT50、AVOS ほか 17 のベンチマーク | EgoSurgery（一人称・少数動画）で凍結した probe の条件で測った |
| A-03 | データセット（一人称の開放手術） | 報告に記載なし | EgoSurgery-Tool | 工程認識では測っていない |
| A-04 | データセット（一人称の開放手術） | 報告に記載なし | EgoSurgery-HTS | 工程認識では測っていない |
| A-05 | 不明 | 報告に記載なし | EgoSurgery | 規約が不明 |
| A-06 | 該当なし | 報告に記載なし | 該当なし | 該当なし |
| A-07 | 因果的な時間畳み込み（多段） | 旧地図に記載なし。A2g の系統表は定番の基準（2024–25 の比較でも継続して使われる）。A2c の系統表も定番の基準。A2s は因果 TCN・online の系統で、MS-TCN は定番の基準、2024〜26 の online 系は新興と書く（A2s L13） | Cholec80、Cholec51 | online（因果的）。少数動画・一人称では測っていない |
| A-08 | Transformer による集約 | 旧地図に記載なし。A2c・A2g の系統表は定番の基準 | Cholec80、M2CAI16 | online。少数動画・一人称では測っていない |
| A-09 | 長時間文脈の Transformer | 旧地図に記載なし。A2g は手術工程の強い既存の基準と書く | Cholec80、AutoLaparo | online。AutoLaparo は学習 10 本 |
| A-10 | 再帰型以前の多タスク（HMM） | 旧地図に記載なし | Cholec80 | 学習動画 10／20／30／40 本の量の依存を示す（Fig. 10） |
| A-11 | 記憶機構 | 定番の基準（2025 の HID-SSM の比較の表に残る。A2g）。A2c の系統表も定番の基準 | Cholec80、M2CAI | EgoSurgery では測っていない |
| A-12 | 時間畳み込みの U-Net＋self-attention、多尺度 | Cholec80 の online で上位（著者自身の表。A2c） | Cholec80、AutoLaparo（図だけ） | online。少数動画・一人称では測っていない |
| A-13 | 多尺度・階層の Transformer | A2c は新興。A2g は定番の基準の候補（2024 の主要な因果的な多尺度のモデル） | Cholec80、GTEA ほか | online。EgoSurgery では測っていない |
| A-14 | end-to-end の映像 Transformer、多尺度・階層 | A2c は SOTA 級（MoSFormer の Table 1 で 2 位）。A2g は不明。A3c はクリップのモデルを online で使う系統で SOTA 級（Cholec80） | Cholec80、AutoLaparo | online（滑り窓）。EgoSurgery では測っていない |
| A-15 | 記憶機構＋長時間文脈の Transformer | Table 1 で上位（A2c） | BernBypass70、Cholec80、AutoLaparo | online。少数動画（AutoLaparo）を含む。一人称では測っていない |
| A-16 | 状態空間モデル（Mamba） | A2c は新興。A2g は SSM 系の定番の基準だが offline 系（後続の SurgicalMamba が最初期の手術の Mamba として位置づける） | Cholec80、CATARACTS | online ではない。一人称では測っていない |
| A-17 | 状態空間モデルと注意機構の混成 | A2c は新興。A2g は不明〜新興 | ESD385、Cholec80 | 一人称では測っていない |
| A-18 | 階層の入力依存の状態空間モデル（局所と大域の多尺度） | 新興（A2c、A2g） | Cholec80、MICCAI2016、HeiChole | online。一人称・EgoSurgery では測っていない |
| A-19 | 状態空間モデル、状態の持ち越し | 新興（A2c、A2f）。新興（A2s L19） | Cholec80、AutoLaparo、HeiCo ほか | online。一人称では測っていない |
| A-20 | 状態空間モデル | 新興（A2g の系統表の中で HID-SSM とともに最も直接的と書く） | 報告に記載なし | 報告に記載なし |
| A-21 | 工程の区間の推定（phase proposal） | 新興／不明（A2g） | Cholec80、Cataracts | online の版あり。一人称・開放手術では測っていない |
| A-22 | クリップのモデルを online で使う | A3c の系統表は SOTA 級（Cholec80） | 報告に記載なし | online |
| A-23 | 記憶機構、因果的な時間畳み込み、後処理 | A2c は新興。A2g は online の行動分割で SOTA 級（NeurIPS 2024 の Table 8・9）。A2s は 2024〜26 の online 系を新興と書く（A2s L13） | GTEA、50Salads、Breakfast | GTEA は少数動画・一人称・online を満たす（A2g） |
| A-24 | 進捗予測・タスクグラフ・手順の事前知識 | A2c は新興。A2g は定番の基準（一人称の online の手順の分割。後続の文献が引用） | GTEA、EgoProceL、EgoPER | 少数動画・一人称・online を満たす |
| A-25 | 再帰型、区間・クリップごとの初期化とその直し | THUMOS'14 で定番の基準（2024 年以降の比較表は未確認で、厳密には不明寄り。A2f）。A2s は 2024〜26 の online 系を新興と書く（A2s L13） | THUMOS'14、TVSeries、FineAction | online。少数動画・一人称では測っていない |
| A-26 | 多段の時間畳み込み（offline）、サンプリング間隔 | 行動分割で定番の基準（A2f）。定番の基準（A2s L13）。Edit・F1@k は段落の評価の定番（A2s L20） | 50Salads、GTEA、Breakfast | offline |
| A-27 | Transformer による集約（局所・階層） | 旧地図に記載なし。A2c の系統表は定番の基準 | 50Salads、GTEA、Breakfast | offline |
| A-28 | 長時間文脈の Transformer、記憶機構、online の行動検出の流用 | A2g は online の行動検出の定番の基準。一般の行動分割にそのまま移すのは不適合（A2g）。A2c は行動分割では弱い基準（OnlineTAS の Table 8・9） | THUMOS'14、TVSeries、HACS | online |
| A-29 | seed による差 | 50Salads・Breakfast で定番の基準（A2f）。A2s の系統表は C2F-TCN を段落・境界の評価と、手術モデル自身の再現性・seed 感度の系統に置き、後者の現役度を「benchmark 依存」と書く（A2s L20、L24） | 50Salads、Breakfast、GTEA | offline |
| A-30 | 視点の扱い（一人称特有）、区間・クリップごとの初期化 | A2c は新興。A2f は Ego-Exo4D keystep の公式の基準として定番。A2s の系統表（一人称の長時間手順・多尺度文脈）は Transformer-XL を定番、Ego-METAS・KORMo を新興とし、Ego-Exo4D の現役度は書いていない（A2s L15） | Ego-Exo4D keystep | 一人称。手術ではない |
| A-31 | 視点の扱い（入力側） | 新興（A2c の系統表） | Ego-Exo4D keystep | 一人称。手術ではない |
| A-32 | 該当なし（ベンチマーク） | 新興（A2f）。新興（A2s L15） | Ego-METAS | 一人称・online |
| A-33 | 黒塗り等で時間軸を保つ（学習時の blackout の拡張） | 新興（A2f）。A2s は 2024〜26 の online 系を新興と書く（A2s L13） | 報告に記載なし | online |
| A-34 | 対象の手術データ上の画像 SSL、領域適応としての継続事前学習（初期化の実験） | 定番の基準（後続の手術の基盤モデルの論文が比較と設計の根拠に引く。A3g）。A3c の系統表は定番の基準（Cholec80、AutoLaparo） | Cholec80、HeiChole | 少数ラベル（5・10 本）で測った。一人称・online では測っていない |
| A-35 | 手術画像の SSL、データの多様性 | 報告に記載なし | 3 課題（名前は報告に無い） | 一人称では測っていない |
| A-36 | 手術画像の SSL 基盤モデル、領域適応としての継続事前学習 | SOTA 級（MedIA 2026 の Table 3 で 6 つの下流・3 課題で上位 2 位以内。A3g） | AutoLaparo、RAMIE ほか | 一人称では測っていない（EgoSurgery は A-02 の表） |
| A-37 | 手術画像の SSL 基盤モデル（MAE） | 定番の基準（最近の比較表に登場。A3g） | Cholec80（工程）、CholecT45 系（action triplet）ほか | 少数動画（2・4・8 本）で測った。一人称は A-02 の表だけ |
| A-38 | 対象データ上の映像 MAE | 定番の比較対象程度（GGMAE が EgoSurgery の Table 2 で比較。A3g） | OR-AR、Cataract-101、EgoSurgery（A-01 の Table 2） | 一人称は A-01 の Table 2 だけ |
| A-39 | 映像の手術・内視鏡基盤モデル | 定番の基準（SurgeNetXL・SurgMotion などが比較に使う。A3g） | 内視鏡の下流。EgoSurgery は A-02 の表 | 一人称は A-02 の表だけ |
| A-40 | 映像の手術基盤モデル | 定番の比較対象。後続の比較では上位でない（SurgeNetXL の Table 3。A3g） | SurgeNetXL・SurgMotion の比較 | 一人称は A-02 の表だけ |
| A-41 | 映像の手術基盤モデル、評価と漏れの作法 | SOTA 級（2026 の査読つきの比較で手術の基盤モデルと自然領域の ViT-B を広く比べる。A3g）。A3c の系統表は SOTA 級を主張 | 13 データセット（長い動画 500 超、短いクリップ 600、66 万フレーム超）。学習に使わない種類は白内障・眼科、ESD を含み、開放・一人称は含まない（A3g） | 一人称・開放手術では測っていない |
| A-42 | 手術画像の SSL 基盤モデル | SOTA 級（A3g） | AutoLaparo、M2CAI16、Cholec80、CholecT50、CholecSeg8k ほか | 一人称では測っていない |
| A-43 | 映像の手術基盤モデル、状態空間モデル、クリップのモデルを online で使う | A2c の系統表は新興 | 内視鏡の下流。EgoSurgery は A-02 の表 | 一人称は A-02 の表だけ |
| A-44 | 映像と言語（手術） | A3c は定番の基準（zero-shot）。A3g は定番の比較対象。A2c の系統表は新興（EgoSurgery の凍結の探索で中位） | SurgMotion の比較（A-02）ほか | 一人称は A-02 の表だけ |
| A-45 | 手術・内視鏡画像の SSL 基盤モデル | 報告に記載なし | SurgeNetXL の比較、SurgMotion の比較 | 一人称は A-02 の表だけ |
| A-46 | 手術画像の SSL 基盤モデル | 報告に記載なし | SurgMotion の比較（A-02） | 一人称は A-02 の表だけ |
| A-47 | 凍結した ViT＋adapter（パラメータ効率の良い転移） | 旧地図に記載なし。A2c の系統表は不明 | Cholec80、AutoLaparo、Cataract-101 | 少数動画（AutoLaparo 10 本）。一人称では測っていない |
| A-48 | 開放手術の大規模データ | 報告に記載なし | SurgMotion の Table 5（A-02） | 該当なし |
| A-49 | 映像の手術基盤モデル（顕微鏡） | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-50 | 凍結と fine-tune の比較（評価） | 報告に記載なし | GraSP ほか | 一人称では測っていない |
| A-51 | 手術画像の SSL 基盤モデル（DINOv2 系） | 報告に記載なし | 報告に記載なし | 一人称では測っていない |
| A-52 | 領域適応としての継続事前学習、一般の基盤モデル | 報告に記載なし | 報告に記載なし | 一人称では測っていない |
| A-53 | 映像 MAE、一般の映像基盤モデル | 手術の基盤モデルの定番の基準（A3g） | EgoSurgery（A-01 の Table 2、A-02 の Table 3） | EgoSurgery で測られた値がある |
| A-54 | 一般の映像基盤モデル | A3g の系統表は SOTA 級／新興（一般の画像・映像の基盤モデル） | EgoSurgery（A-01 の Table 2） | EgoSurgery の Table 2 の値がある |
| A-55 | 事前知識でマスク・損失を選ぶ（動き） | A3c の系統表は新興（一般の映像） | 報告に記載なし | 該当なし |
| A-56 | 一般の基盤モデル（画像） | 一般の画像表現として SOTA 級、手術の側では新興の基準（A3g）。A3c の系統表は定番の基準 | EgoSurgery（A-02 の Table 3） | EgoSurgery で凍結の probe の値がある。fine-tune は測られていない（A3g） |
| A-57 | 一般の映像基盤モデル（予測型） | SOTA 級／新興（A3g） | 手術への転移の値は無い | EgoSurgery の比較表に V-JEPA 2 の単独の行は見つからない（A3g） |
| A-58 | 一人称の非手術映像の事前学習 | 定番の基準（一人称の映像と言語。A3g） | EgoMCQ、EPIC ほか 5 つの一人称のベンチマーク | 手術では測っていない |
| A-59 | 一人称の非手術映像の事前学習 | 定番の基準（EgoVLP の後継。A3g）。Ego-Exo4D keystep の定番の基準（A2c） | Ego-Exo4D keystep（A-30 の Table 6 で 38.76%） | 手術では測っていない |
| A-60 | 一人称の非手術映像の事前学習 | A3c の系統表は定番 | Ego4D | 手術では測っていない |
| A-61 | 一人称の非手術映像の事前学習 | 旧地図に記載なし | Charades-Ego、EPIC-100 | 手術では測っていない |
| A-62 | 視線を注意の教師・入力に使う | 旧地図に記載なし | EGTEA Gaze+ | 手術では測っていない |
| A-63 | データセット（一人称の非手術） | A2c の系統表はデータセットなので対象外（不明） | EPIC-KITCHENS | 該当なし |
| A-64 | 事前知識でマスクを選ぶ（物体） | 新興（A3g の系統表） | 映像と言語の検索 | 手術・EgoSurgery では測っていない |
| A-65 | 視線を注意の教師に使う | 定番（EGTEA。A3c の系統表） | EGTEA | 手術では測っていない |
| A-66 | 視線を注意の教師・入力に使う | 報告に記載なし | 報告に記載なし | 手術では測っていない |
| A-67 | 視線を入力に使う | 報告に記載なし | 報告に記載なし | 手術では測っていない |
| A-68 | 視線を注意の教師に使う（一人称から手術への転移） | 報告に記載なし | JIGSAWS | 開放手術・EgoSurgery では測っていない |
| A-69 | 視線を入力に使う | 報告に記載なし | 報告に記載なし | 手術では測っていない |
| A-70 | 領域適応としての継続事前学習 | 不明（A3c の系統表） | 報告に記載なし | 一人称では測っていない |
| A-71 | 領域適応としての継続事前学習 | 不明（A3c の系統表） | 報告に記載なし | 映像ではない |
| A-72 | 評価・漏れ | 報告に記載なし | 報告に記載なし | 映像ではない |
| A-73 | 評価・漏れ | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-74 | 評価の方法論、seed による差、再現性 | 定番の参照先（MoSFormer が非緩和の評価の根拠に引く。A2c）。評価の方法論の定番の基準（A2g）。段落・境界の評価の系統で「定番の評価」（A2s L20）。手術モデル自身の再現性・seed 感度の系統で「現役度は benchmark 依存」（A2s L24） | Cholec80 | 該当なし |
| A-75 | 再帰型、BN の扱い、区間・クリップごとの初期化（SWE）と状態の持ち越し（CHE・CHT） | Cholec80 の online の工程認識で SOTA 級（Table 3。A2f）。A2s の系統表（OOB・不連続区間の系統）の現役度は A-78 の行と同じ（A2s L12） | Cholec80、AutoLaparo、CATARACTS、GTEA、50Salads | online。一人称（GTEA）を含む |
| A-76 | 評価の方法論 | 報告に記載なし | Cholec80 | 該当なし |
| A-77 | 拡散モデル、再実装の値と転記の値の混在（評価の慣行） | 新興（A2f）。手術モデル自身の再現性・seed 感度の系統で「現役度は benchmark 依存」（A2s L24） | ESD | 一人称では測っていない |
| A-78 | 黒塗り・削除による匿名化の前処理 | 匿名化の前処理として定番（MultiBypass140 が採用、ROBAN が比較。A2f）。A2s は手術の OOB・プライバシー除去・不連続区間の系統を「定番の基準＋不明: 腹腔鏡 workflow」とし、未知の長さの削除区間で状態を持ち越すか初期化するかの比較は確認できなかったと書く（A2s L12） | 社内・外部のデータ | 該当なし |
| A-79 | 黒塗りで時間軸を保つ | 不明（A2f）。A2s の系統表の現役度は A-78 の行と同じ（A2s L12） | MultiBypass140 | 該当なし |
| A-80 | 黒塗り・ぼかしで時間軸を保つ | 新興（A2f）。A2s の系統表の現役度は A-78 の行と同じ（A2s L12） | 社内のデータ | 該当なし |
| A-81 | 区間を除いて詰める前処理 | 不明。A2s の系統表の現役度は A-78 の行と同じ（A2s L12） | 報告に記載なし | 該当なし |
| A-82 | 境を越えた注意を遮断（マスク）、区間をつなぐ（MIXChunk） | 新興〜定番（KORMo が採用。A2f）。A2s の系統表は INTRADoc の現役度を書かず、同じ系統の Transformer-XL を定番、Ego-METAS・KORMo を新興とする（A2s L15） | SlimPajama ほか | 映像ではない |
| A-83 | 境を越えた注意を遮断 | 新興（A2f）。新興（A2s L15） | 報告に記載なし | 映像ではない |
| A-84 | 状態の持ち越し | 定番（後続の手法が比較対象にする。A2f）。長い文脈の定番（A2s L15） | WikiText-103 | 映像ではない |
| A-85 | 欠けの長さ・時刻を入力に与える（mask と経過時間 δ で入力と隠れ状態を減衰） | 医療の時系列で定番（直近の比較表は未確認。A2f）。定番の基準（A2s L16。2026 年の不規則時刻の文献も GRU-D・mTAN を系譜として扱う）。MASCIT（A-108）の Table 2 の比較対象（A2s L364） | 報告に記載なし | 映像ではない |
| A-86 | 計算機・GPU の種類による差、データ処理（入力の順）、決定性を固定した実行の費用 | 再現性の研究の定番の参照先（A2f）。定番の基準（A2s L21。RepDL 2025 が Pham・Summers・Zhuang・Chen を問題設定の主要な先行研究として列挙） | CIFAR-10／100、ImageNet | 手術・行動分割ではない |
| A-87 | seed による差、決定性を固定した実行の設定 | 定番の参照先（A2f）。定番の基準（A2s L21） | CIFAR-10、PTB | 手術・行動分割ではない |
| A-88 | ライブラリの版による差 | ソフトウェア工学の参照先（後続の道具 DEVIATE。A2f）。定番の基準（A2s L21）。後続の DEVIATE は A-112 | 報告に記載なし | 手術・行動分割ではない |
| A-89 | seed による差、評価の方法論 | 評価の方法論の定番（A2f）。定番の基準（A2s L21） | 5 課題 | 手術・行動分割ではない |
| A-90 | seed による差 | 報告に記載なし。定番の基準（A2s L21） | CIFAR-10 | 手術・行動分割ではない |
| A-91 | データ処理（リサイズ）による差 | 生成モデルの評価で定番（clean-fid。A2f）。画像生成の評価では定番、手術の工程認識への外挿は不明（A2s L23） | FID | 分類の精度への影響は測っていない |
| A-92 | 再現性の総説 | 参照先（後続の文献が引用。A2f）。手術モデル自身の再現性・seed 感度の系統で「現役度は benchmark 依存」（A2s L24） | 該当なし | 該当なし |
| A-93 | 再現性の総説 | 不明（A2f）。定番の基準（A2s L21） | 該当なし | 該当なし |
| A-94 | 手術の体外フレーム・不連続な系列 | 不明（A2s。近い問題設定の代表例だが、直近二年の複数の比較表で基準として使われることは確認できず）。系統表では「定番の基準＋不明」（A2s の語） | 非公開の実データ（腹腔鏡下胆嚢摘出）。詳細不明 | online は該当。少数動画・一人称は不明・非該当 |
| A-95 | 因果的な時間状態の安定化 | 新興（A2s。MICCAI 2026 採択で、著者以外の追試は限定的） | Cholec80、AutoLaparo | AutoLaparo は 21 本、online。一人称ではない |
| A-96 | 時間的な破損への頑健性 | 定番の基準に近いが、直近の複数の論文での採用の確認が不足するため不明（A2s）。系統表では「定番化途上」（A2s の語） | THUMOS14-C、ActivityNet-v1.3-C | いずれも非該当 |
| A-97 | 時刻を使う注意（time-aware attention） | 不明。2026 年の TIDES が不規則時刻の系譜の代表として引用（A2s）。系統表では「継続参照」（A2s の語） | 不規則な臨床・時系列のベンチマーク。詳細不明 | 該当なし |
| A-98 | 経過時間による再帰の減衰 | 不明（A2s。概念的な基準としては存続するが、直近二年の複数の比較表での採用は確認できず）。系統表では「現役度は benchmark 依存」（A2s の語） | 報告に記載なし | 報告に記載なし |
| A-99 | 明示的な timestamp の位置符号化 | 不明（A2s）。系統表では「現役度は benchmark 依存」（A2s の語） | 報告に記載なし | EgoSurgery での測定なし |
| A-100 | 集合に基づく不規則時刻の表現 | 不明（A2s）。系統表では「現役度は benchmark 依存」（A2s の語） | 報告に記載なし | 該当なし |
| A-101 | 連続時間の潜在ダイナミクス | 定番の基準に近い（A2s。TIDES 2026 が不規則時刻の代表として参照） | 報告に記載なし | 該当なし |
| A-102 | 連続時間の再帰的なフィルタリング | 不明（A2s） | 報告に記載なし | online の考え方には近いが、映像のベンチマークは無い |
| A-103 | 制御微分方程式 | 定番の基準（A2s。MASCIT 2026 の Table 2 が不規則時刻のニューラルの基準として比較） | 報告に記載なし | 該当なし |
| A-104 | 不規則時刻のグラフ注意 | 定番の基準（A2s。MASCIT 2026 の Table 2 で比較対象） | 報告に記載なし | 該当なし |
| A-105 | 連続時間の Transformer | 不明（A2s）。系統表では「比較的新しい」（A2s の語） | 報告に記載なし | 該当なし |
| A-106 | 連続時間の SSM | 定番の基準（A2s。TIDES 2026 が S5 を基準・機構の比較に直接使う） | LRA ほか | ベンチマーク上は非該当 |
| A-107 | 時刻を使う選択的 SSM | 新興（A2s） | UEA、Physiome-ODE、Fading Flash | 非該当 |
| A-108 | マスクを使う選択的 SSM | 新興（A2s） | 34 の不規則な時系列のデータセット | 非該当 |
| A-109 | 決定性を固定した学習・散らばりの分解 | 定番の基準（A2s。RepDL 2025 が主要な関連研究として引用） | LeNet の変種、ResNet-38／56、WRN-28-10 ほか | 非該当 |
| A-110 | 環境をまたぐ再現性 | 定番の基準に近いが短報（A2s） | MNIST、IMDB、クレジットカードの不正検知 | 非該当 |
| A-111 | ライブラリの版の再現性 | 不明（A2s） | 報告に記載なし | 非該当 |
| A-112 | 散らばりの検査 | 定番の基準に近い（A2s。Pham ほかの ASE 2020〔A-88〕の散らばりの分析の後続） | 報告に記載なし | 非該当 |
| A-113 | ソフトウェアの再現性 | 新興（A2s） | 報告に記載なし | 非該当 |
| A-114 | 数値の非決定性 | 新興（A2s） | microbenchmark（FP64 の summation ほか） | 非該当 |
| A-115 | ハードウェアをまたぐ決定性を固定した算術 | 新興（A2s） | 報告に記載なし（benchmark の表は未精読） | 非該当 |

---

## 5. 証拠の質

| ID | 何と何を比べた差か | その要素だけを変えた比較か | 基準の強さ | seed・分割・検定 | 著者以外の追試・採用 |
|---|---|---|---|---|---|
| A-01 | Table 1 は手法の比較（backbone も手法ごとに違う）。Table 2 は ViT-S を固定し事前学習の方式だけを変えた比較。Table 3 はマスクの選び方・マスク比・温度 τ を変えた比較 | Table 1 はいいえ（backbone と時間モデルが同時に変わる。A2c、A2g）。Table 2・Table 3 ははい（A2g、A3c）。Table 2 の各行の事前学習のデータを明記した文は無い（A3c）。A3g は「同一 backbone・同一の学習手順で EgoSurgery-Phase の上の事前学習の方式とマスクを比べたもの」と書く。A3c は Table 3a の tube 0.90（29.8）が Table 2 の VideoMAE の行（29.8）と一致することを挙げる | Table 2 の基準は ViT-S のスクラッチ学習（表注に明記。A3c）。ImageNet や Kinetics で初期化した基準は無い（A3c）。Table 1 は当時の代表的な手法（A2f） | seed・標準偏差・検定の記載なし。分割は 1 つ（A2c、A2f、A3c、A3g）。ハイパーパラメータは coarse-to-fine の grid searchで、どのデータで選んだかの記載なし（A3c）。事前学習を学習用の 14 本に限ったとする記述は見つからない（A3g） | SurgMotion（A-02）が EgoSurgery を下流の評価に使う（A2f、A2g）。著者以外の追試は見つからない（A3c） |
| A-02 | Table 3 は同じ probe で backbone だけを変えた比較（A2c、A2g）。SurgMotion 自身の構成要素を分けた比較ではない（A3c、A3g） | 表現の比較としてははい（A2g）。SurgMotion の新要素は同時に入っている（A3g） | 基盤モデル 13 種（DINOv3、VideoMAE、EndoFM、SurgVLP ほか） | seed・評価の分割・検定は不明（全報告）。ハイパーパラメータの探索は記載あり（A2g）。16 ヘッドの最良を報告し、検証データで選んだとは書かれていない（A3c）。EgoSurgery の分割が公式分割か独自の分割かは特定できない（A3g） | 著者以外の採用は未確認（A2f、A3c） |
| A-03 | 工程認識に効くかを測った数値は無い（A2c） | 該当なし | 該当なし | 報告に記載なし | 報告に記載なし |
| A-04 | 工程認識への効果を測った数値は無い（A2c） | 該当なし | 該当なし | 報告に記載なし | 報告に記載なし |
| A-05 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-06 | 該当なし | 該当なし | 該当なし | 該当なし | 該当なし |
| A-07 | Table 1 は段の数の比較、Table 2 は手法の比較（旧地図） | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | EgoSurgery-Phase の Table 1（A-01）、MoSFormer の Table 1（A-15）、TUNeS の Table I（A-12）が比較に使う |
| A-08 | Table 1 は手法の比較。構成要素の比較（単純な連結、空間→空間）は旧地図が「Table 3」とする別の表（表番号は未確定） | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | EgoSurgery-Phase の Table 1（A-01）、MoSFormer の Table 1（A-15）、TUNeS の Table I（A-12）が比較に使う |
| A-09 | Table 1 は手法の比較 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | MoSFormer の Table 1（A-15）が比較に使う |
| A-10 | 手法の比較と学習量の比較 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし |
| A-11 | 緩和の有無を変えた比較ではない | 該当なし | 報告に記載なし | 不明 | 後続の論文が比較に使う（A2g）。公開の学習済みモデルの再現について GitHub の issue がある（A2g） |
| A-12 | Table I は抽出器の時間文脈 L と時間モデルを交差させた比較 | L だけ、時間モデルだけを変えた比較になる（はい） | TeCNO*、Trans-SVNet*、GRU、OperA、SAHC（* は特徴の拡張と平滑化損失を使わない版） | 抽出器 5 seed × 時間モデル 5 回の 25 run。標準偏差 ±0.005〜0.018。指標は動画ごとの Acc と macro Jaccard | 報告に記載なし |
| A-13 | 同じ MS-ASCT で ResNet50 と EfficientNetV2 を比べた比較がある（A2g） | backbone の比較はほぼはい（A2g） | 手術の SOTA の群（A2g） | 不明 | 後続の SSM 系の比較対象（A2g） |
| A-14 | 手法の比較 | いいえ | 報告に記載なし | 報告に記載なし | MoSFormer（A-15）が別の計算法で出し直した |
| A-15 | Table 1 は手法の比較（online・非緩和）。Table 2 は記憶だけを足した比較 | Table 2 ははい | TMRNet、TeCNO、TeSTra、Trans-SVNet、LoViT、SKiT、Surgformer | seed・検定の記載なし | 報告に記載なし |
| A-16 | 手法の比較（抜粋）と anticipation の損失の有無 | anticipation の有無ははい。双方向性と同時学習は混ざる（A2g） | 同時期の手術工程の手法 | 不明 | SurgicalMamba（A-19）などが引用（A2g） |
| A-17 | 手法の比較。Mamba の部品とサンプリングを同時に変える（A2g） | いいえ | 手術工程の SOTA | 不明 | 不明 |
| A-18 | 手法の比較。因果／文脈の版、局所／大域、抽出器の事前学習を同時に入れる（A2g） | いいえ（SSM 単独の効果とは分かれない。A2g） | TeCNO、SV-RCNet、TMRNet など | 不明 | 少ない（A2g） |
| A-19 | 手法の比較（これまでの最強の手法との差。要旨） | いいえ | これまでの最強の手法 | Cholec80 の動画ごとの Jaccard の SD は 8.1（緩和）、11.5（厳密）（A2f） | 不明 |
| A-20 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-21 | 同じ枠組みで online と offline を比べる（推論の手順が違う） | online／offline は同じ枠組みだが推論の手順が変わる（A2g） | TeCNO、Trans-SVNet | 不明 | 不明 |
| A-22 | 窓を短くしたときの落ち方を定量化した表は確認できない（A3c） | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-23 | 因果的な TCN と本手法と後処理の比較。成分を足していく比較。記憶長の比較。offline の手法との比較。付録 Table 12 は同じ ASFormer の offline と因果化の比較 | 成分の比較ははい。全体は GRU・特徴の増強・記憶の複合（A2g） | 因果的な TCN（強い簡潔な基準）。LSTR をそのまま移したものより強い（A2g） | seed の記載なし（A2c）。seed による有意差の検定は確認できない（A2g） | 2024 以後の online の行動分割の文献で基準になりつつある（A2g） |
| A-24 | Table 1（MS-TCN 系）は offline、offline で学んで online で推論、因果で学ぶ（CAS）、＋OODL、＋APP、＋APP＋TG を比べる。Table 2 は ASFormer 系。Table 3 は学べるタスクグラフ。Table 4 は offline への効果 | 成分を一つずつ足す比較ははい | MS-TCN、ASFormer | seed の記載なし（A2c） | 2025–26 の一人称の手順の文献が引用（A2g） |
| A-25 | 比較 1: 損失の重みを一様からクリップの最終時刻だけにかけるステップ関数へ（状態の初期化は変えない）。比較 2: ステップ関数と、動画全体で学ぶ（動画の中で初期化しない）の比較 | はい | 当時の Transformer 系の SOTA | run 数・分散の記載なし | OnlineTAS（A-23）が言及 |
| A-26 | Table 5 は後段に渡すもの（確率と特徴、確率のみ）の比較。Table 6 は同じ MS-TCN で入力を 1 fps と 15 fps にした比較 | Table 6 ははい（A2f）。Table 5 は旧地図に記載なし | 当時の SOTA | 記載なし | MS-TCN++ の Table 14 が採用（A2f） |
| A-27 | Table 1 は手法の比較。位置符号化と階層の有無の比較 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | OnlineTAS の付録 Table 12 が因果化して比べる（A-23）。TUNeS の Table II（A-12） |
| A-28 | Table 3 は長期の記憶の stride の比較 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | OnlineTAS が行動分割に移して比べる（A-23） |
| A-29 | 4 seed の平均±SD（Table T22、数値は未読） | 該当なし | 該当なし | 4 seed | 報告に記載なし |
| A-30 | Table 6 は ego の視点だけで推論したときの手法の比較 | いいえ | EgoVLPv2 ほか | 報告に記載なし | 後続の文献が基準に使う（A2f） |
| A-31 | Table 2 は入力（ego のみ、手のみ、ego＋手）の比較 | 入力の比較ははい | TimeSformer、VI Encoder | 報告に記載なし | 報告に記載なし |
| A-32 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-33 | 効果量は未読 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-34 | Table 3（単一フレーム）と Table 4（時間モデル）は ImageNet 上の SSL の重み（Base）と、そこから手術データで SSL を続けた重み（Ours）と ImageNet 教師あり（No SSL）の比較。Fig. 12 は SSL の初期化（スクラッチ／ImageNet SSL／ImageNet 教師あり）の比較 | Table 3・4 と Fig. 12 ははい | ImageNet 教師あり、ImageNet 上の SSL | 全設定の複数 seed はしていない。ランダムに選んだ一手法の 5 回の再実行で phase F1 の SD 約 0.7 pp（A3g、A3c 注 8）。分割の間の分散は少ラベルで手法間の差を上回りうる（§4.1。A3c） | 後続の手術の基盤モデル（SurgeNetXL など）が設計の根拠に引く（A3g） |
| A-35 | 同じ術式のデータだけの SSL と ImageNet 事前学習の比較、異種の手術データを加えた比較 | 報告に記載なし | ImageNet 事前学習 | 報告に記載なし | 報告に記載なし |
| A-36 | 最良の ImageNet の変種との比較。術式に絞った SurgeNetCholec との比較 | 初期化の比較としてはほぼはい | ImageNet、ImageNet21k、他の手術の基盤モデル | 下流は患者単位の交差検証、順位の安定性に 1,000 回のブートストラップ（A3g） | 報告に記載なし |
| A-37 | Table 6・7 は ImageNet の ViT と EndoViT を同じ TeCNO の二段目で比べる | はい | ImageNet の ViT、ResNet50 | 各設定 3 run の平均±SD。検定は確認できず（A3g） | 後続の比較表に登場（A3g） |
| A-38 | Table 7（Cataract-101）は事前学習の方式と初期化の比較 | SurgMAE の論文の Table 7 は旧地図に記載なし。EgoSurgery の Table 2 の SurgMAE の行は、同じ ViT-S・同じ学習の手順での比較（A3g。A-01） | SwAV、SimCLR、random MAE、VideoMAE、Kinetics-400 の初期化 | 旧地図に記載なし | GGMAE（A-01）が比較 |
| A-39 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | SurgeNetXL・SurgMotion の比較表（A3g） |
| A-40 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | SurgeNetXL・SurgMotion の比較（A3g） |
| A-41 | 手法の比較（95% 信頼区間と P 値つき。A3c） | いいえ | ImageNet の MAE、VideoMAE（K400）、ImageNet 教師あり、ImageNet の DINO、UMT（K710）、MVD。DINOv3 と V-JEPA 2 は表に無い（A3g） | 信頼区間と P 値（A3c） | 報告に記載なし |
| A-42 | Table 5 は backbone を凍結し、同じデータと蒸留の条件で ViT-L と ConvNeXt-L を比べる | はい | 既存の手術の基盤モデル | Table 5 の範囲で複数 seed の情報は確認できず（A3g） | 報告に記載なし |
| A-43 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | SurgMotion の比較（A-02） |
| A-44 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | SurgMotion の手術の基盤モデルの比較に入る（A3g） |
| A-45 | SurgeNetXL の Table 3 で同じ下流の流れで ResNet50 と ViT-S を比べる（A3g） | 同じ目的・データの ResNet と ViT の比較としては近いが、下流の構造まで揃えたとは言い切れない（A3g） | 報告に記載なし | 報告に記載なし | SurgeNetXL・SurgMotion の比較 |
| A-46 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | SurgVISTA・SurgMotion の記述 |
| A-47 | Table IV は adapter の比較、事前学習の量の比較 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし |
| A-48 | 該当なし | 該当なし | 該当なし | 該当なし | SurgMotion が事前学習と評価に使う（A-02） |
| A-49 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-50 | 凍結した encoder と、上位 4 ブロックを fine-tune した encoder の比較 | はい | 一般の基盤モデル | 報告に記載なし | 報告に記載なし |
| A-51 | 手法の比較 | 報告に記載なし | 既存の手術の基盤モデル | 報告に記載なし | 報告に記載なし |
| A-52 | 手法の比較 | 報告に記載なし | 公開の DINOv3 の重み | 報告に記載なし | 報告に記載なし |
| A-53 | 時間方向のサンプリング間隔の比較（A3c） | はい | 報告に記載なし | 報告に記載なし | GGMAE・SurgVISTA・SurgMotion の比較 |
| A-54 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | SurgVISTA が自然動画側の大規模な映像の事前学習の系統を基準に置く（A3g） |
| A-55 | サンプリング間隔の比較 | はい | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-56 | A-02 の Table 3（同じ probe） | 表現の比較としてははい | 手術の基盤モデル | 不明 | 報告に記載なし |
| A-57 | 該当なし | 該当なし | 該当なし | 該当なし | SurgMotion は JEPA 系の考えを採るが、V-JEPA 2 の重みの単純な転移の基準とは別（A3g） |
| A-58 | Table 10 は事前学習のデータと損失の比較（旧地図） | 旧地図に記載なし（Table 10 は事前学習のデータと損失が同時に変わる比較） | CC3M＋WebVid | 旧地図に記載なし | EgoVLPv2（A-59）が後継（A3g） |
| A-59 | 該当なし | 該当なし | 該当なし | 該当なし | Ego-Exo4D の基準（A-30） |
| A-60 | 一般の backbone をそのまま使う場合と Ego4D で fine-tune した場合 | 報告に記載なし | 一般の事前学習の backbone | 報告に記載なし | 報告に記載なし |
| A-61 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし |
| A-62 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし |
| A-63 | TSN の基準 | 該当なし | TSN | 旧地図に記載なし | 旧地図に記載なし |
| A-64 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-65 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-66 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-67 | 視線の融合の有無 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-68 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-69 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-70 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-71 | 継続 SSL と、一般の重みからの教師ありの fine-tune | 報告に記載なし | 一般の重みからの教師ありの fine-tune | 報告に記載なし | 報告に記載なし |
| A-72 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-73 | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-74 | 評価の規約だけを変えた差（A2c） | はい | SV-RCNet の再実装（5 seed） | 5 seed | 2026 の系統的な分析（A-76）が問題意識を引き継ぐ（A2g） |
| A-75 | 比較 1: ResNet-BN の end-to-end 4×16 で、評価のときの扱いだけを SWE（系列ごとに初期化して滑り窓で評価）から CHE（評価のときに動画全体へ状態を持ち越す）に変える。比較 2: 1×64 で CHE と CHT（学習のときも時刻順の batch で、勾配を切った状態を持ち越す） | はい | 二段の TeCNO の再実装 89.4±0.8（Table A.7） | 各 3 run（seed の値の記載なし）、分割 1 つ、検定なし | SurgicalMamba（A-19）が言及（A2f） |
| A-76 | 該当なし | 該当なし | 該当なし | 該当なし | 該当なし |
| A-77 | Table 3 で TeCNO と Trans-SVNet は著者提供の重みで再実装し、ほかの手法は原著の値を転記 | 該当なし | TeCNO、Trans-SVNet ほか | 報告に記載なし | 報告に記載なし |
| A-78 | 体外の検出の性能 | 該当なし | 該当なし | 不明 | MultiBypass140（A-79）、ROBAN（A-80） |
| A-79 | 不明（配布の形式の記述だけ） | 該当なし | 該当なし | 該当なし | 報告に記載なし |
| A-80 | ROBAN と OoBNet・IODA の比較 | 該当なし | OoBNet、IODA | 報告に記載なし | 報告に記載なし |
| A-81 | 検出の精度 | 該当なし | 該当なし | 報告に記載なし | 報告に記載なし |
| A-82 | 同じ文書の集合で、詰め方とマスクだけを変える | はい | 標準の詰め方 | 事前学習は各 1 回。Table 2 の ± はデモの選び方の 16 seed による散らばり。検定なし | KORMo（A-83） |
| A-83 | 同じ代理のモデルで 4 種のマスクを比べる | はい | causal のマスク | 不明 | 報告に記載なし |
| A-84 | 手法の比較 | いいえ | 報告に記載なし | 報告に記載なし | 後続の記憶の Transformer |
| A-85 | GRU-Mean、GRU-Forward、GRU-Simple、GRU-D の比較（Figure 4、数値は未読） | はい | 欠けを使わない GRU | 報告に記載なし | 第三者の実装あり（subramen/GRU-D） |
| A-86 | 同じ GPU の上で ALGO（seed だけ）、IMPL（seed を固定しハードとソフトの非決定性だけ）、ALGO+IMPL を各 10 run（ImageNet は 5 run） | はい | 該当なし | 10 run、検定なし | 多数（A2f） |
| A-87 | 乱雑さの源を一つだけ変え、ほかを固定して各 100 run | はい | 該当なし | 各 100 run、V100 2 枚、PyTorch | 報告に記載なし |
| A-88 | seed を固定した同一の学習の繰り返し | はい | 該当なし | 報告に記載なし | DEVIATE |
| A-89 | 各分散の源の大きさをブートストラップによる分散に対する割合で示す（Figure 1、数値は未読） | はい | 該当なし | 該当なし | 報告に記載なし |
| A-90 | 乱雑さの源を全部変える場合と一つだけ変える場合 | はい | 該当なし | 報告に記載なし | 報告に記載なし |
| A-91 | 同じ画像を各ライブラリの bicubic と PIL の bicubic でリサイズして比べる | はい | PIL の bicubic | 該当なし | 報告に記載なし |
| A-92 | 該当なし | 該当なし | 該当なし | 該当なし | 報告に記載なし |
| A-93 | 該当なし | 該当なし | 該当なし | 該当なし | 報告に記載なし |
| A-94 | 標準の二段の工程モデルと、体外フレームに対して頑健化した提案方式。本文未読のため腕の定義は不明 | 不明 | 不明 | 不明 | 確認できず |
| A-95 | 同じ backbone に TEC、EGTP、両方を足す ablation | はい（ablation は同じ backbone に TEC／EGTP を足す） | 代表的な online の工程認識の backbone 三つ | 読んだ範囲では seed 数・有意差の検定を確認できず | 2026 年時点では確認できず |
| A-96 | 同じ学習済みの検出器の clean の test と、5 種 × 3 段階の severity の corrupted test。さらに FrameDrop＋TRC の学習を同じモデルに足す | corruption の test は学習済みのモデルを固定して入力だけを変える（A2s は「比較的純粋」と書く） | 当時の主要な 7 手法 | seed 数・検定は読んだ範囲で不明 | 不明 |
| A-97 | 報告は表番号を未確認のため数値を記載していない | 不明 | 不明 | 不明 | TIDES など後続が方法の系譜として採用（A2s） |
| A-98 | 報告は表番号を未確認のため数値を記載していない | 不明 | 不明 | 不明 | 経過時間を使う RNN の先行例として後続の文献が広く参照（A2s） |
| A-99 | 報告は表を未読のため数値を記載していない | 不明 | 不明 | 不明 | 報告に記載なし |
| A-100 | 不明（本文未読） | 不明 | 不明 | 不明 | 報告に記載なし |
| A-101 | 報告は表番号を未確認のため数値を記載していない | 不明 | 不明 | 不明 | TIDES 2026 が参照（A2s） |
| A-102 | 詳細は未確認 | 不明 | 不明 | 不明 | 不明 |
| A-103 | 報告は原論文の表番号を未確認のため数値を記載していない | 不明 | 不明 | 不明 | 2026 年のベンチマーク（MASCIT、A-108）で採用 |
| A-104 | MASCIT の Table 2 の、MASCIT と既発表の基準とのベンチマーク水準の比較（時間の欠けの与え方だけを変えた比較ではない） | いいえ（時間の欠けの与え方だけを変えた比較ではない。A2s L276） | 不明 | MASCIT の側は benchmark の推奨の設定、確率的なニューラルの手法は 3 runs | MASCIT（A-108）が比較対象に採用 |
| A-105 | 報告は本文の表を未確認のため記載していない | 不明 | 不明 | 不明 | 不明 |
| A-106 | 原論文は S4 などとの系列モデルの比較。EgoSurgery の欠けは未評価 | 不明 | 不明 | 原論文は未確認 | TIDES（A-107）が基準と機構の比較に使う |
| A-107 | パラメータ数を揃えた S5、Mamba 系、TIDES で、不規則な Δ の in-distribution／out-of-distribution の外挿を比べる | 統制した toy の実験では比較的明確（A2s の語） | S5、Mamba-2／-3 など | Fading Flash は seed 0 の一回。UEA／Physiome の表は 5 independent runs の mean±SD | 2026 年のプレプリントのため著者以外の追試は限定的 |
| A-108 | MASCIT と KNN／SVM／LGBM／ROCKET／BORF／RIFC／BRITS／GRU-D／NCDE／Raindrop／SAITS／TimesNet のベンチマークの比較。さらに partial／full selectivity の factorial の ablation | 構造全体の差を含む。partial／full selectivity は ablation | 12 の基準を共通のベンチマークで比較 | ニューラル・確率的な手法は原則 3 runs、MASCIT は全 34 データセットで 3 seeds。Holm 補正の片側 Wilcoxon | 発表直後で不明 |
| A-109 | もとの決定性を固定しない条件、seed と record-and-replay によるソフトウェアの統制、決定性を固定するパッチによるハードウェアの統制、双方を統制した条件 | ソフトウェアとハードウェアを別の setup で遮断（A2s は「比較的明瞭」と書く） | 再現性を直接の目的にした統制実験 | 16 runs／setup。run の対応づけには seed 0 と 42 も使う。学習時間の比較には Wilcoxon rank-sum と Cliff's delta | RepDL など後続が問題設定を継承 |
| A-110 | 決定性を固定した設定の例の、ハードウェアとソフトウェアの環境を変える | ハードウェアとソフトウェアの両方を多数の環境で動かすため現実的だが、要因を完全に単独化した設計かは本文の短さから判断困難（A2s） | 該当なし | 各実験 5 回。分散の成分の検定の詳細は不明 | 報告に記載なし |
| A-111 | フレームワークの版を変える | 不明 | 不明 | 詳細不明 | 報告に記載なし |
| A-112 | 不明 | 不明 | 不明 | 不明（本文の表は未確認） | 報告に記載なし |
| A-113 | TRUNK モデルを同一のパイプライン・同一の seed・同一の GPU で再学習 | 報告に記載なし | 該当なし | 感度の分析を主張するが詳細は未確認 | 報告に記載なし |
| A-114 | 決定性を固定しない reduction と決定性を固定した代替 | 不明 | 該当なし | カーネルの実験は多数回の反復。深層学習の seed の散らばりとの直接の比較ではない | 報告に記載なし |
| A-115 | 従来の浮動小数点の実装と RepDL | 不明 | 不明 | 詳細不明 | 発表後一年以内で限定的 |

---

## 6. 効果（数値は報告のまま。指標名は原文）

EgoSurgery の値は A-01（原論文の Table 1〜3）と A-02（SurgMotion の Table 3。凍結した backbone と attentive probe）の二系統で、評価の条件が違う。A-02 の Table 3 の値は各モデルの行にも写した。

| ID | 指標・値・表番号 | 符号 | 符号や大きさが変わる条件 |
|---|---|---|---|
| A-01 | Table 1（macro の P／R／J）: PhaseLSTM（AlexNet）36.3／33.1／21.9、PhaseNet（AlexNet）37.0／25.7／19.7、TeCNO（ResNet-50）47.7／39.2／27.3、Trans-SVNet（ResNet-50）41.8／35.9／23.1、NETE（Inception v3）43.7／35.2／27.5、GGMAE（ViT-S）51.7／45.6／33.9。Table 2（P／R／J）: スクラッチ 47.9／31.6／27.1、VideoMAE 49.3／41.6／29.8、VideoMAE V2 54.2／43.2／30.8、SurgMAE 52.2／41.9／27.8、GGMAE 51.7／45.6／33.9。Table 3a（J）: random 0.75 は 28.9、random 0.90 は 30.6、tube 0.90 は 29.8、視線 0.90 は 33.9。Table 3b（マスク比、J）: 0.95→31.2、0.90→33.9、0.85→31.6、0.80→31.5。Table 3c（τ、J）: 1.00→30.1、0.75→30.6、0.50→33.9、0.25→27.2 | Table 2 で GGMAE はスクラッチより J +6.8、VideoMAE V2 より +3.1。Table 3a で視線は random 0.90 より +3.3、tube より +4.1。同じ ResNet-50 の上で TeCNO は Trans-SVNet より J +4.2（seed 1 回、分散の報告なし。A2c） | τ=0.25 で 27.2（スクラッチは 27.1）。τ の選び方だけで 6.7 動く。マスク比 0.95 で −2.7。Precision は VideoMAE V2（54.2）が GGMAE（51.7）より高い（A3c）。本文の「スクラッチより 6%」は表から計算すると 6.8（A3c）。著者の今後の課題は動画数と視点の拡張（旧地図） |
| A-02 | Table 3（EgoSurgery、Acc／F1／J）: SurgMotion 75.57／50.72／42.95、DINOv3-L 75.37／32.43／26.03、DINOv3-H 70.08／36.34／29.03、VideoMAE-L 64.52／26.84／19.82、VideoMAE-G 62.25／20.40／16.13、EndoFM 54.85／36.13／26.42、SurgVLP 57.44／23.26／17.46、GastroNet 48.12／16.08／12.87、EndoMamba 53.30／13.90／10.32、EndoSSL 49.78／12.04／8.86、SelfSupSurg 36.03／7.38／5.22、SurgeNetXL 35.82／7.34／5.18、GSViT 35.74／7.33／5.17、EndoViT 32.32／9.29／6.31。本文の「F1 +14.6%」は EndoFM との差、「+18.3%」は DINOv3-L との差（A2c、A3c）。A2f は要旨の値として EgoSurgery で F1 +14.6%、PitVis で +10.3% と書く | 著者の主張は改善。DINOv3-H（F1 36.34）は EndoFM（36.13）より高い（A2c） | 不審点（報告の記載）: ①EndoFM の EgoSurgery の F1／J（36.13／26.42）が Table 2 の Cholec80 の値と一致し、Acc だけが違う（54.85 と 57.25。A2c、A3c、A3g）②Table 2 の AutoLaparo の EndoFM は J 47.84 が F1 35.77 を上回る（A2c、A3c）③EndoMamba の Table 5 の値が Table 6 の CholecT50 の値と一致（A2c、A3c）④Table 5 の AVOS で 6 モデルが 48.34／8.15 の同値（A2c、A3c）⑤Table 1 の時間の和 3,707.72 h が本文の 3,658 h と合わない（A3c）⑥EgoSurgery の「10.55 h」は原論文の 15 h と、「Breast surgery」は 10 術式と食い違う（A2c、A2f、A3c） |
| A-03 | 工程認識の数値は無い | 該当なし | 本数を 21 と明記し、EgoSurgery-Phase の本文の 20 と食い違う（A2f）。付随の情報を工程認識に使った報告はまだ無い（A2c） |
| A-04 | 工程認識の数値は無い | 該当なし | 他の論文が「15,437 timepoints」と書く量がある（A2c）。工程の注釈は 27,694 フレーム（A-01） |
| A-05 | EgoSurgery で工程認識の precision 0.88（A2c） | 該当なし | 原論文（A-01）の precision 51.7 と離れており、規約が不明なので比べられない（A2c） |
| A-06 | 該当なし | 該当なし | フレーム名に元の時刻が残っているか、除いた区間の情報が配布されるかは、公開の頁からは判断できない（A2f） |
| A-07 | Table 2（Cholec80）: Accuracy 88.56、Precision 81.64、Recall 85.24。Table 1: Stage I 88.35、Stage II 88.56、Stage III 86.49。TCN なしは 82.22／70.65／75.88（旧地図） | 段を増やすと III で低下 | 著者は train への過適合の可能性を示唆（実証ではない。旧地図）。EgoSurgery では J 27.3（A-01）。AutoLaparo では Acc 77.3／J 50.7（A-15 の表） |
| A-08 | Table 1（Cholec80）: Accuracy 90.3、Precision 90.7、Recall 88.8、Jaccard 79.3。構成要素の比較（旧地図は表番号を「Table 3」と書き、原 PDF の表番号の照合が要るとする）: TeCNO 75.1、ResNet と TeCNO の連結 73.0、空間→空間 60.8、提案 79.3。n=30 で 79.3、n=40 で 79.0（旧地図） | 単純な連結は低下 | EgoSurgery では同じ ResNet-50 の TeCNO（27.3）を下回る 23.1（A-01） |
| A-09 | Table 1（Cholec80、緩和あり）: Accuracy 92.4、Jaccard 81.2。AutoLaparo: Accuracy 81.4、Precision 85.1、Recall 65.9、Jaccard 56.0（主表。ablation の表には 55.9） | 該当なし | 自身の構成要素で低下したものは読んだ範囲に記載なし（旧地図）。通常と違う工程順の動画を誤認識しやすい。各時刻で過去の全特徴を入れるため長い手術で推論が遅くなる（旧地図、結論の節）。MoSFormer の非緩和の表では Cholec80 91.5／74.2、AutoLaparo 81.4／55.9（A-15） |
| A-10 | 工程（Overall-Online）: Precision 73.7、Recall 79.6、Accuracy 81.7。Offline の数値は無い。Fig. 10 の器具の在否: 10 本 65.9→62.0、20 本 70.9→67.5、30 本 73.6→77.5、40 本 80.9→81.0（ToolNet→EndoNet） | 器具の側は 10・20 本で EndoNet が低い | 工程の側の負の結果は記載なし（旧地図） |
| A-11 | MoSFormer の表（A-15）で AutoLaparo Acc 78.2／J 49.6 | 不明 | 公式の評価コードは境界を緩和する設定で計算する（A2g）。緩和の有無による同じモデルの差は表番号つきで確認できていない（A2g） |
| A-12 | Table I（Cholec80、online、32:8:40、Acc／J）: 抽出器単体 L=1 0.816／0.591、L=8 0.865／0.693、L=64 0.901／0.758。TeCNO* 0.877／0.705、0.883／0.721、0.898／0.750。Trans-SVNet* 0.879／0.705、0.889／0.723、0.898／0.749。GRU 0.875／0.701、0.879／0.704、0.901／0.759。OperA 0.863／0.659、0.880／0.680、0.898／0.745。SAHC 0.882／0.718、0.892／0.736、0.913／0.779。TeCNO（特徴の拡張＋平滑化損失）0.891／0.730、0.900／0.750、0.906／0.768。TUNeS 0.901／0.746、0.915／0.768、0.922／0.783。Table II（offline、L=64、J）: TeCNO 0.807、ASFormer 0.824、TUNeS 0.823 | L=1→64 で J が +0.037〜+0.086（同じ L の中の時間モデルの幅と同程度以上）。L=64 では TeCNO*・Trans-SVNet*・GRU・OperA が抽出器単体とほぼ同じか下回る。特徴の拡張と平滑化損失で +0.018〜+0.025（本書の作成者の検算: 表の値からは L=1 で +0.025、L=8 で +0.029、L=64 で +0.018 で、報告の幅と合わない） | CHE は L=8 で改善（0.693→0.713）、L=64 で悪化（0.758→0.723）。offline→online の落差（L=64、J）は TeCNO −0.039、TUNeS −0.040。offline の edit score は 0.556〜0.758。本文は「TUT は L=64 で良い」と書くが表では L=8 が最良（不審点）。40:40 では TeCNO の値が論文ごとに違う（Czempiel 2022 は Acc 0.874、Chen 2022 は 0.900）。AutoLaparo は Fig. 17 だけで、本文の数値は Acc 0.851・f-Jaccard 0.609 |
| A-13 | EfficientNetV2 の方が一貫して高い。HTML の該当行に精度 93.58 と 94.59 などがあるが、表番号を確定できず A2g は数値を根拠に使わない | backbone を強くすると改善（A2g） | 報告に記載なし |
| A-14 | MoSFormer が出し直した値（A-15）: Cholec80 Acc 92.3／J 77.8、AutoLaparo Acc 86.1／J 62.4。BernBypass70 Acc 85.9／F1 62.5 | 該当なし | 原論文の値は MoSFormer と別の計算法で出したもの（A2c） |
| A-15 | Table 1（online・非緩和、Acc／J）: AutoLaparo は TMRNet 78.2／49.6、TeCNO 77.3／50.7、Trans-SVNet 78.3／50.7、LoViT 81.4／55.9、SKiT 82.9／59.9、Surgformer 86.1／62.4、MoSFormer 88.0／66.2。Cholec80 は TeSTra 90.1／71.6、Trans-SVNet 89.1／72.5、LoViT 91.5／74.2、SKiT 92.5／76.7、Surgformer 92.3／77.8、MoSFormer 93.2／78.7。BernBypass70（Acc／F1）: TeCNO 83.8／59.2、MTMS-TCN 85.3／62.4、Surgformer 85.9／62.5、MoSFormer 88.0／66.3。Table 2（BernBypass70 の Acc）: 記憶なし 85.9 → 記憶あり 88.0、正解の履歴を与えると 89.2 | 記憶を足して +2.1（Acc）。AutoLaparo で TeCNO と Surgformer の差は J 11.7、Cholec80 の Trans-SVNet と Surgformer の差（5.3）より大きい（A2c） | 1 fps の内視鏡で ViT を end-to-end で学んだ条件（A2c） |
| A-16 | Cholec80 で AC 92.6±8.6、JA 81.5±8.6（A2c、抜粋）。anticipation の損失の有無で AC・JA とも約 +0.5 pp | 改善（著者の報告） | AC と JA の標準偏差がどちらも 8.6 で一致（不審点。A2c） |
| A-17 | ESD385 で平均正解率が 72.31% から 87.64% に上がった（何と比べたかは抜粋から不明。A2c） | 改善（著者の報告） | 「Mamba を使った最初の工程認識」と主張するが、SR-Mamba（A-16）が先に出ている（A2c） |
| A-18 | 要旨で従来の最良に対し Cholec80 +2.8%、MICCAI2016 +4.3%、HeiChole +12.9%（要旨の値で、A2g は定量の根拠に採らない）。A2c は数値を未読 | 改善（著者の報告） | 報告に記載なし |
| A-19 | 要旨: Cholec80 Acc 94.6・Jaccard 82.7（+0.7・+2.2 pp）、AutoLaparo Acc 89.5・Jaccard 68.9（+1.7・+2.0 pp）（A2c）。HeiCo で Jaccard +3.3 pp（Table 7。A2f）。著者は「margins are widest on the smallest and most domain-shifted sets, and narrowest where … the test split is small」（改善幅は最も小さく領域のずれの大きい集合で最も広く、test の分割が小さいところで最も狭い）と書く（A2f） | 改善（著者の主張） | 要旨は厳密な online の評価と書くが、GitHub の README は 10 秒の境界の緩和の規約に従うと書く。速度も版によって 238.74 fps と 312.88 fps で違う（不審点。A2c） |
| A-20 | 数値は報告に無い | 報告に記載なし | 報告に記載なし |
| A-21 | Cataracts で offline Acc 84.3／Jaccard 68.4、online 76.7／66.8（Acc −7.6、Jaccard −1.6。A2c）。offline は Fig. 3 で TeCNO・Trans-SVNet より正解に近い（定性の比較。A2g） | offline の方が高い | offline→online の落差は Jaccard より Acc の方が大きい（A2c） |
| A-22 | 数値は報告に無い | 報告に記載なし | 報告に記載なし |
| A-23 | A2c の読み: Table 1（online、Acc／Edit／F1@50）GTEA 因果 TCN 74.4／66.6／57.2、本手法 76.2／63.5／58.8、本手法＋後処理 74.4／70.3／67.7。Breakfast 55.3／18.7／8.3、56.7／19.3／9.3、52.9／55.7／30.5。Table 2（50Salads、Acc）75.2 → GRU のみ 78.1 → 全成分 82.4。Table 5（記憶長）256 で 128 より Acc が下がる（82.4→80.7）。Table 8・9 Breakfast の F1@50 は offline の MS-TCN 47.5、因果 TCN 8.3。LSTR は 50Salads で Edit 5.0。A2g の読み: Table 8（strict-online）GTEA 因果 TCN 74.4／66.6／57.2 → 本手法 75.8／66.8／60.3 → 後処理 73.5／75.4／66.6。50Salads 75.2／19.6／19.6 → 79.1／29.0／28.3 → 後処理 76.7／69.2／62.8。付録 Table 12（ASFormer の offline → strict-online、Acc／Edit／F1@50）GTEA 79.7／84.6／79.2 → 75.0／69.7／62.0、50Salads 85.6／79.6／76.0 → 77.5／29.1／28.6、Breakfast 73.5／75.0／57.4 → 64.9／32.1／20.2。Table 6 は確信度の閾値を上げると segment の指標が上がり Acc が 82.5 付近から 79.4 へ下がる | 記憶を足すと改善（segment の指標で大きい）。後処理は Edit・F1 を上げ Acc を 1.8〜3.8 下げる（A2c）。因果化で ASFormer の F1@50 は GTEA −17.2、50Salads −47.4、Breakfast −37.2（A2g） | GTEA ではフレーム精度の上積みは小さく、segment の指標の改善が大きい（A2g）。不審点: Table 8 の「Ours online」の行が Table 1 の「TCN・semi-online」の行と同じ値（A2c）。GTEA の本手法の値が A2c（Table 1: 76.2／63.5／58.8）と A2g（Table 8: 75.8／66.8／60.3）で違い、50Salads の全成分の Acc も A2c（82.4）と A2g（79.1）で違う |
| A-24 | Table 1（F1@50）EgoProceL: offline 45.9、offline 学習→online 推論 8.8、CAS 33.0、＋OODL 30.5、＋APP 35.2、＋APP＋TG 35.7。EgoPER: 77.3、11.9、39.4、40.0、43.4、46.3。GTEA（Acc／Edit／F1@50）: offline 76.3／79.0／69.8、offline 学習→online 推論 47.0／58.8／38.7、CAS 74.0／64.4／56.0、＋OODL で F1@50 54.1、＋TG で Acc 74.3（APP 時の 76.0 から低下）。Table 2: offline 学習→online 推論の Acc は EgoProceL 13.2、EgoPER 19.8。GTEA で CAS 77.2／73.3／65.0 → ＋TG 77.0／74.1／66.1。Table 3: EgoProceL で学べるタスクグラフは F1@50 35.7→34.8。Table 4（offline の EgoProceL）: F1@50 45.9→46.1（A2c） | 報告に符号の一括の記載なし（値は §6 の指標の欄）。OODL は GTEA と EgoProceL で F1@50 を下げた（Table 1。A2c） | 学べるタスクグラフは EgoProceL で下がる（A2c） |
| A-25 | 比較 1: mAP 66.4→71.8（Table 4a／4b、Kinetics の特徴）。比較 2: THUMOS Kinetics 71.8 と 72.0、THUMOS Anet 69.3 と 69.6、TVSeries Anet 88.5 と 88.3、FineAction 37.1 と 38.0（補遺 Table 1） | 比較 1 は改善。比較 2 はほぼ差なし（差は 0.9 以内） | クリップ長 32 秒で頭打ち（Fig. 4）。動画全体での学習は batch を組めず勾配の分散が大きい |
| A-26 | Table 9（GTEA）F1@10／25／50 85.8／83.4／69.8、Edit 79.0、Acc 76.3。Table 5: 後段に確率＋特徴を渡すと 56.2／53.7／45.8、確率のみで 76.3／74.0／64.5（旧地図）。Table 6（50Salads、1 fps と 15 fps）: F1@10 77.8 と 76.3、F1@50 64.0 と 64.5、Edit 70.7 と 67.9、Acc 78.6 と 80.7（A2f） | 特徴の転送は低下。1 fps では Edit と F1@10 が上がり Acc が下がる | 著者は「1 fps では過分割は減るが、境界の位置の精度と短い区間を失う」と解釈（A2f） |
| A-27 | Table 1（50Salads）F1@10／25／50 85.1／83.4／76.0、Edit 79.6、Acc 85.6。標準の位置符号化で encoder 80.2／78.0／70.0、decoder 78.1／76.7／69.4。非階層は 64.2／61.5／55.1（旧地図） | 標準の位置符号化と非階層は全指標で低下 | 旧地図に記載なし（因果化した比較は A-23 の付録 Table 12） |
| A-28 | Table 1: THUMOS mAP 65.3（ActivityNet の特徴）、69.5（Kinetics の特徴）。Table 3: 長期の stride 1／2／4 は 69.5、8 で 69.2、128 で 65.9（旧地図）。OnlineTAS の表で 50Salads の Edit 5.0（A2c） | 圧縮は途中まで零、その先で低下 | 一般の行動分割にそのまま移すと causal TCN より悪い（A2g L45）。OnlineTAS の表で、50Salads の LSTR の Edit は 5.0（A2c L417）、因果 TCN の Edit は 19.6（A2g L314、A-23） |
| A-29 | 数値は未読 | 該当なし | 最も小さい GTEA で結果の振れが大きい（A2f） |
| A-30 | Table 6（ego のみ、Top-1）VI Encoder 41.53%、視点の蒸留 39.49%、EgoVLPv2 38.76%（A2c） | Table 6 では VI Encoder が視点の蒸留と EgoVLPv2 より高い（A2c） | クラス数を決める閾値の数え方にフォーラムで疑問が出ている（A2c） |
| A-31 | Table 2（Top-1）TimeSformer* ego のみ 39.18%、手のみ 45.81%、ego＋手 47.75%、VI Encoder 40.34% | 手の映像を加えると改善 | ここに転記された VI Encoder の値（40.34%）が A-30 の 41.53% と合わない（不審点。A2c） |
| A-32 | 数値は報告に無い | 該当なし | 欠けやクリップの扱いは読んだ範囲に記載なし（A2f）。A2s は、Ego-METAS が sampling rate と Edit の関係を実験しており評価の面で重要と書く（A2s L15、L582） |
| A-33 | 数値は未読 | 該当なし | 動画の 5〜20% の区間を劣化させる（全画素ゼロを含む）。連続する blackout は X フレーム（例 1 fps で 5）まで（A2f） |
| A-34 | Table 4（時間モデル、5 本、Base→Ours）: DINO 61.1→65.0、MoCo v2 63.4→66.1、SimCLR 63.6→66.6、SwAV 60.9→68.3。No SSL 62.3。10 本: DINO 71.3→70.4、MoCo +5.0、SimCLR +3.3、SwAV +2.7（A3g）。Table 3（単一フレーム、5 本）: DINO 51.4→56.3、MoCo 52.1→58.1、SimCLR 51.3→57.2、SwAV 50.9→57.1。40 本の DINO の Ours 71.1、Base 71.6、ImageNet 教師あり 71.5（A3g）。少ラベルで最大 +6.1 F1（5 本、単一フレーム、MoCo v2）、+6.0（時間モデル、SwAV）（旧 A、A3c）。Table 8（HeiChole）MoCo v2 phase F1 64.7（旧 A） | 5 本では手術データの SSL で改善。10 本の DINO は −0.9。40 本ではほぼ差なし（A3c は最大 −1.2%）。ImageNet 上の SSL の重みは 36 比較中 7 でしか教師ありを改善せず、phase F1 は最大 −1.9、tool mAP は最大 −11.2（A3g、旧 A） | SSL の前の初期化は ImageNet 教師ありがすべての SSL で最良。MoCo v2 で最大 phase F1 約 +12、tool mAP +11（Fig. 12。A3g、A3c）。batch 128〜1024 は比較的頑健、100 epoch 以降は飽和（A3g）。旧地図は Fig. 9 で batch 256→1024 で F1 −5.5、Fig. 10 で 100 epoch 超で最大 −2 と書く（A3g の記載と並べた。両立するかは原典で確かめる）。ハイパーパラメータの探索は約 7,000 GPU 時間（A3g） |
| A-35 | 同じ術式のデータだけの SSL は ImageNet 事前学習より 3 課題で +13.8%、+9.5%、+36.8%。異種の手術データを加えるとさらに +5.0、+5.2、+2.5%（要旨） | 改善 | 報告に記載なし |
| A-36 | 最良の ImageNet の変種より工程の精度が 2 データで +2.9、+2.7 pp。Table 3: AutoLaparo（Acc／F1）ImageNet21k 0.83／0.70 → SurgeNetXL 0.85／0.74、RAMIE 0.80／0.72 → 0.82／0.75（A3g）。EgoSurgery（A-02 の Table 3）F1 7.34／J 5.18 | 低侵襲の下流では改善。EgoSurgery の凍結の probe では低い | 術式に絞った SurgeNetCholec より多様な SurgeNetXL が胆嚢摘出の下流を含め大半で上（A3g） |
| A-37 | Table 7（工程、TeCNO の二段目、ImageNet の ViT → EndoViT）: 2 本 77.05→78.89（+1.84）、4 本 80.00→80.28（+0.28）、8 本 84.10→84.68（+0.58）。Table 6（全データ、二段目）89.56±0.65 → 89.37±0.95（−0.19）。一段目の 8 本は 75.50 → 75.30。Table 5（triplet、2 本、mAP）ResNet50 10.88±0.50、ImageNet の ViT 12.22±1.78、EndoViT 17.59±2.94。EgoSurgery（A-02）F1 9.29／J 6.31 | 工程では少数でわずかに改善、全データではわずかに低下。triplet では改善 | 報告に記載なし |
| A-38 | Table 7（Cataract-101、mAP）SwAV 83.61、SimCLR 83.20、random MAE 86.43、VideoMAE 85.05、SurgMAE 87.78、Kinetics-400 の初期化 92.85（旧地図）。EgoSurgery の Table 2 で J 27.8（A-01） | 小データの Cataract-101 では自然動画の Kinetics の初期化が SurgMAE を上回る。EgoSurgery では VideoMAE（29.8）・VideoMAE V2（30.8）より低い | 著者は小データでの ViT の事前学習の難しさを明記（旧地図）。旧地図の別の行（A-01 の元の行）は「SurgMAE 初期化は scratch と 0.7 pt 差」と書く。A3c・A3g は EgoSurgery の Table 2 を同じ ViT-S・同じ手順での事前学習の方式の比較と読む（A-01） |
| A-39 | EgoSurgery（A-02 の Table 3、凍結の probe）Acc 54.85／F1 36.13／J 26.42 | EgoSurgery の凍結の probe で、手術の基盤モデルのうち F1 は EndoFM が SurgMotion の次（A-02 の Table 3） | この F1／J は SurgMotion の Table 2 の Cholec80 の値と一致する（A-02 の不審点①） |
| A-40 | EgoSurgery（A-02）F1 7.33／J 5.17 | EgoSurgery の凍結の probe では低い | 報告に記載なし |
| A-41 | CATARACTS（J）SurgVISTA 63.6、ImageNet の MAE 61.6、VideoMAE K400 60.7、ImageNet 教師あり 52.5（Ext. Table 9）。Cataract-101（J）SurgVISTA 87.6、UMT K710 87.1、ImageNet 教師あり 79.2、ImageNet の DINO 53.8（Ext. Table 10）（A3c） | 学習に使わない種類（眼科）で、SurgVISTA の J は表の一般の映像モデル（ImageNet の MAE、VideoMAE K400、UMT K710）より 0.5〜2.0 点高い（A3c。値は §6 の指標の欄） | DINO の行の信頼区間（52.8, 64.7）は点推定に対して非対称（不審点。A3c） |
| A-42 | 既存の手術の基盤モデルに対し工程の J で AutoLaparo +9.5、M2CAI16 +9.4、Cholec80 +8.4 pp、CholecT50 の action mAP +4.4（著者の報告）。Table 5（凍結）AutoLaparo Acc／F1 は ViT-L 75.6／66.1、ConvNeXt-L 76.4／66.9（各 +0.8）。CholecSeg8k の mDice 61.2→71.9（+10.7） | ConvNeXt が ViT を上回る | 凍結の条件では生成・MAE 系より識別的な目的が上と著者は報告（A3g） |
| A-43 | EgoSurgery（A-02、凍結の probe）Acc 53.30／F1 13.90／J 10.32 | EgoSurgery の凍結の probe では低い | SurgMotion の Table 5 の EndoMamba の値が Table 6 の値と一致（A-02 の不審点③） |
| A-44 | EgoSurgery（A-02）Acc 57.44／F1 23.26／J 17.46 | Endo-FM・DINOv3 より低い | 報告に記載なし |
| A-45 | SurgeNetXL の Table 3: AutoLaparo の F1 は ResNet50 0.58、ViT-S 0.54。RAMIE の F1 は 0.64 と 0.61。EgoSurgery（A-02）F1 16.08／J 12.87 | 工程では ResNet50 の版が高い | 分割の課題ではデータによって入れ替わる（A3g） |
| A-46 | EgoSurgery（A-02）Acc 49.78／F1 12.04／J 8.86 | EgoSurgery の凍結の probe では低い | A3g は arXiv の ID を確定できなかったと書き、A3c は arXiv 2308.12394 を挙げる |
| A-47 | Table VI（AutoLaparo）Accuracy 85.0、Precision 82.6、Recall 74.7、Jaccard 66.1。Table V（Cholec80）緩和の Jaccard 83.8、非緩和 79.1（旧地図） | 自然画像の事前学習量を 400M→2B にしても全 adapter で改善せず。STA は AIM に対し F1 同値、Jaccard +0.1 | 複数の adapter を足しても一貫した上積みなし（旧地図） |
| A-48 | 工程認識の数値は報告に無い | 該当なし | SurgMotion の Table 5 の AVOS で 6 モデルが同値（A-02 の不審点④）。視点の種類は一部不明（A3g） |
| A-49 | 数値は報告に無い | 該当なし | 報告に記載なし |
| A-50 | 数値は報告に無い | 凍結の比較は「mixed」。上位 4 ブロックだけを fine-tune すると手術の事前学習の利点がはっきりした（A3c） | GraSP では凍結のときの順位が逆転した。凍結と部分的な適応の両方を報告するよう提言（A3c） |
| A-51 | 数値は報告に無い | MIS-DINOv2 が既存の手術の基盤モデルを多くの課題で上回った（A3c） | 報告に記載なし |
| A-52 | 数値は報告に無い | 手術画像で少し学んだ MAE や DINOv2 が、公開の DINOv3 の重みを上回る傾向（A3c） | 報告に記載なし |
| A-53 | 半分の間隔では 68.9 に下がる（本文の表。A3c）。EgoSurgery の Table 2（A-01）J 29.8。SurgMotion の Table 3（A-02）VideoMAE-L F1／J 26.84／19.82、VideoMAE-G 20.40／16.13 | 間隔に敏感。大きい G が L より低い（A3g） | A-01 の Table 2 の 29.8 は公開の Kinetics の重みを読み込んだ値ではなく、EgoSurgery の共通の事前学習の手順の中の値（A3g） |
| A-54 | EgoSurgery の Table 2（A-01）J 30.8（GGMAE 33.9 より −3.1） | 該当なし | この 30.8 は公開の一般の重みからの転移の比較ではなく、EgoSurgery の共通の学習の手順の中の比較（A3g）。SurgMotion の Table 3 に VideoMAE V2 の行は無い（A3g） |
| A-55 | 間隔 s=2 が最良（A3c） | 該当なし | 報告に記載なし |
| A-56 | EgoSurgery（A-02）DINOv3-L Acc 75.37／F1 32.43／J 26.03、DINOv3-H 70.08／36.34／29.03 | EndoViT・GSViT・EndoMamba・SurgeNetXL・SurgVLP を上回り、Endo-FM を J で上回る（A3g） | 凍結の probe だけの比較で、fine-tune での順位は未測定（A3g） |
| A-57 | 手術の数値は無い | 該当なし | 報告に記載なし |
| A-58 | Table 10（EgoMCQ、intra／inter）EgoClip＋EgoNCE 90.6／57.2、CC3M＋WebVid 62.5／27.4（旧地図）。5 つの一人称のベンチマークで改善（A3c） | 改善 | HowTo100M の事前学習は EPIC の検索で「事前学習なし」と同程度の曲線（旧地図）。手術への直接の転移は見つからない（A3g） |
| A-59 | A-30 の Table 6（ego のみ）38.76% | 該当なし | 手術への直接の転移は見つからない（A3g） |
| A-60 | 数値は報告に無い | 一般の backbone をそのまま使うと一人称で性能が落ち、Ego4D で fine-tune して差を縮めた（A3c） | 報告に記載なし |
| A-61 | 数値は無い（要旨） | 該当なし | 旧地図に記載なし |
| A-62 | 数値は無い（要旨） | 該当なし | 旧地図に記載なし |
| A-63 | 数値は無い（表の頭が抽出で欠落。旧地図） | 該当なし | 旧地図に記載なし |
| A-64 | 数値は報告に無い | 該当なし | 物体を事前知識にしたマスクの系統はあるが、手術での検証は見つからない（A3g） |
| A-65 | 数値は報告に無い | 該当なし | 報告に記載なし |
| A-66 | 数値は報告に無い | 該当なし | 報告に記載なし |
| A-67 | 数値は報告に無い | 改善しなかった（否定的な結果。A3c） | 報告に記載なし |
| A-68 | 数値は報告に無い | 報告に記載なし | Ego4D・EPIC で事前学習した重みを手術に移した研究は、この視線の予測の転用を除き見つからない（A3c） |
| A-69 | 数値は報告に無い | 報告に記載なし | 視線のマスク（A-01）とこれらの使い方を同じデータで比べた研究は見つからない（A3c） |
| A-70 | 数値は報告に無い | 報告に記載なし | 報告に記載なし |
| A-71 | 数値は報告に無い | 継続 SSL の上積みは「marginal」で、中規模のデータでは一般の重みからの教師ありの fine-tune が上（否定的な結果。A3c） | 報告に記載なし |
| A-72 | 数値は報告に無い | SSL が常に効くわけではないと報告（A3c） | 報告に記載なし |
| A-73 | 数値は報告に無い | 該当なし | 報告に記載なし |
| A-74 | 欠けた工程の扱い Jaccard .681→.692（Table 3）。F1 の計算法 .785〜.821（Table 4）。frame-wise と video-wise .670 と .692（Table 6）。境界の緩和 .690→.726（+.036。Table 5・7・8）。seed の差 .017（Table 9）。分割を 40:40 に変えて .692→.707（Table 10）。同じ手法の論文ごとの値: SV-RCNet の R-Acc .853〜.913（Table 11）、TeCNO の Jaccard .696 と .723（Table 12）（A2c） | 報告に符号の一括の記載なし（各表の差は指標の欄） | 緩和の指標は 1 を超えうる（Fig. 4）。MATLAB の評価スクリプトに不具合（A2c）。多くの手法でコードが公開されず、変動の指標（SD_V、SD_P、SD_R）や Jaccard・F1 の報告が欠けていることが多い（A2f）。緩和がどれだけ値を上げるかの統一の値は表番号つきで取れず不明（A2g） |
| A-75 | 比較 1: Accuracy 86.6→89.3、Jaccard 66.3→70.4、緩和の Jaccard 73.1→77.5（Table 3、32/8/40）。比較 2: 動画ごとの精度 ConvNeXt 89.5→92.3、GN 89.3→90.5、BN 59.7→55.6（Table A.7、40/8/32） | CHE は改善。CHT は BN を使わない場合は改善、BN では悪化 | BN で 1×64 にすると崩れる（SWE 57.2）。FrozenBN は lr 1e-5 で CHT が 39.8 に崩れる（Table A.9）。GTEA と 50Salads でも GN と ConvNeXt では CHT が CHE を上回る（Table B.10／B.11）。本文は同じ結果を Fig. 2b と Fig. 3 の両方で参照し、図番号が食い違う（A2f）。著者の主張: BN を使わない backbone で end-to-end に学ぶと単純な CNN-LSTM でも 3 ベンチマークで SOTA を超え、online の課題では BN で未来の情報が漏れる（A2c）。A2s は、GPU 数を変えた結果 BatchNorm の実効の batch が変わる場合、本論文の BN の問題と計算機の効果が分離できなくなると書く（A2s L692） |
| A-76 | 緩和した境界での結果は標準偏差が大きい傾向（A2c） | 該当なし | 2023 年ごろから segment の指標の使用が増えている（本文。A2c） |
| A-77 | 再実装の値と転記の値の差は未読 | 該当なし | 再実装の値と転記の値が同じ表に混在する慣行の例（A2f） |
| A-78 | 社内のテストで ROC AUC 99.97%（要旨） | 該当なし | 体外のフレームが体内に似ていると見逃す。匿名化の手段として「ぼかす」と「削除する」の両方を挙げるが、その後の時間モデルへの影響は測っていない（A2f） |
| A-79 | 該当なし | 該当なし | 体外のフレームを削除せず黒塗りにして時間軸を保った（A2f） |
| A-80 | フレームごとの匿名化で未知の術式に ROC AUC 99.46%、後処理で 99.89%（要旨）。RTX3090 の推論 ROBAN 0.96 ms／フレーム、OoBNet 2.2 ms、IODA 0.57 ms。実時間でない用途で 2 秒の窓の後処理により陰性的中率 99.9953% | 感度は ROBAN が上、特異度・適合率は OoBNet が上 | 運用では削除せずにぼかすので、運用の映像は連続のまま（A2f） |
| A-81 | 精度 97% 超。recall 97% のとき precision 83.5%（要旨） | 該当なし | 目的は除去と匿名化の迅速化。除いた後の時間モデルへの影響は扱っていない（A2f） |
| A-82 | 平均 PPL は 2K で 9.172 と 8.410、8K で 9.065 と 8.079（Table 1）。ICL の平均は 2K で 63.54 と 70.52、8K で 62.43 と 71.23（Table 2）。閉じた QA の EM は 8K で 7.99 と 10.99（Table 3） | 境を遮断すると改善 | 関連する文書を詰めた BM25Chunk は 2K の ICL で 70.91 と遮断（70.52）に並ぶ。遮断の費用は実行時間 +4%（A2f） |
| A-83 | intra-doc 44.48%、causal 43.38%（Table 3） | 遮断が +1.1 pt | 著者以外による INTRADoc（A-82）の小規模な再現（A2f） |
| A-84 | WikiText-103 の PPL 20.5→18.3（Table 1） | 改善 | 相対位置の符号化が無いと状態の再利用は時刻の混乱を招く（A2f） |
| A-85 | 数値は未読 | 欠けを使わない GRU-Mean と GRU-Forward はほぼ同じ。GRU-D は 24 時間を超える系列で GRU-Simple を上回る（A2f） | 映像の工程認識で除いた区間の長さを入力に与えた研究は見つからない（A2f） |
| A-86 | V100 の ResNet-18 CIFAR-10: 93.32±0.17、93.44±0.05、93.41±0.13。V100 の ResNet-50 ImageNet: 76.58±0.10、76.61±0.10、76.60±0.05（Table 2）。churn は ImageNet で IMPL 14.68%、ALGO 14.89%（3.1 節）。決定性を固定した実行による時間の増加は最大で P100 746%、V100 241%、T4 196%（Fig. 8）。SmallCNN の ALGO+IMPL は P100 62.28、RTX5000 62.24、V100 62.03（Table 2） | top-line の SD は 1% 未満で小さい。churn とクラス別の精度では IMPL も ALGO と同程度 | BN の無い小さな CNN は散らばりが大きく、BN を入れると SD 0.86%→0.30%（Fig. 2）。CUDA コアの多い V100 で発散が大きい。TPU は churn が小さいが SD は変わらない（Fig. 5）。入力の順が変わると浮動小数の集約の順が変わり TPU でも非決定になる（Fig. 6）。分散学習は対象外と明記。3.1 節の「ResNet-10 trained on ImageNet」は Table 2 では ResNet-50（誤記とみられる。A2f）。A2s の読み: accelerator を変えても top-line の accuracy の SD の差が小さい条件がある一方、prediction churn や parameter 空間の距離では implementation／hardware の源が algorithmic randomness と同程度になりうる。一つの非決定性の源を除くだけでは stability が大きく改善しない条件も報告。決定性を固定した実装の費用は accelerator により大きく変わり最大で数倍の規模（A2s L625、L708） |
| A-87 | 精度の SD は初期化 0.23±0.02、データの順 0.25±0.02、増強 0.23±0.02、cuDNN 0.22±0.01、すべて 0.26±0.02（Table 1）。PTB の PPL の SD は初期化 0.20、すべて 0.18（Table 2） | どの源も同程度（相対差 20% 以内） | 初期値の 1 ビットの変化でも、すべての源を合わせたのとほぼ同じ散らばりになる（4.1 節）。cuDNN の決定性を固定した実行は約 15% 遅い。cuDNN は seed で固定できず、オンかオフしか選べない（A2f）。A2s の読み: 乱数の源やごく小さな初期の摂動が最適化の軌道を分岐させ、異なる非決定性の源の影響が似た規模になりうる（A2s L627） |
| A-88 | 実装の要因だけで精度の差が最大 2.9%、クラス別の精度の差が最大 52.4%、収束時間の差が最大 145.3%（要旨） | 該当なし | TensorFlow、CNTK、Theano と cuDNN の評価したすべての版で分散が出た。2.9% は最大値で典型値ではない（A2f） |
| A-89 | 多くの分散の源を乱数化した推定量は、計算量 51 分の 1 で理想の推定量に近づく（要旨） | 該当なし | データの分割、初期化、ハイパーパラメータの選び方が結果に強く効く。初期化だけを変える推定量 FixHOptEst(k, Init) が最も悪い（A2f） |
| A-90 | 1 epoch の学習で、3 つの源を全部変えると精度の SD 1.33%、一つだけ変えると分散は 25〜40% 小さい（付録 D.1） | 該当なし | 学習の途中で小さな摂動を与えると最終の結果が大きく変わる（Figure 12）。要旨は標準の CIFAR-10・ImageNet の学習は基の分布の上の性能の分散が小さいと書く（A2f） |
| A-91 | OpenCV、PyTorch、TF と PIL の間で FID が 6 以上。PIL のほかのフィルタどうしでは 0.75 以下（README の表） | 該当なし | OpenCV、TF、PyTorch はフィルタの幅が固定でエイリアスが出る（A2f） |
| A-92 | 数値の測定はない | 該当なし | 変動の源をデータセット、構造、最適化、ハイパーパラメータ、実装・基盤の 5 つに分類し、「実装・基盤」の大きさは測っていない（A2f） |
| A-93 | 該当なし | 該当なし | 参考文献にフレームワークの版と再現性を扱った論文（Machine Learning and Knowledge Extraction 4(4), 2022）があるが、その論文は未確認で記録は無い（A2f）。その論文（Shahriari ほか 2022）は A2s が記録を作った（A-111） |
| A-94 | 本文の表番号を確認できないため、報告は数値を採用していない | 著者の要旨は改善と述べる。効果量は不明 | 不明 |
| A-95 | Table 1。Cholec80 の Trans-SVNet は基準が Accuracy 88.61／Edit 12.54／TFI 6.42、TEC＋EGTP で 89.13／54.97／1.16。AutoLaparo の同じ backbone は 80.16／2.94／18.80 から 83.79／55.60／0.26。欠けた区間での初期化の比較ではなく、同じ online の時間状態での誤りの伝播を抑える比較（A2s） | 時間的な安定性は改善 | Table 2 では TEC の α により Accuracy・Edit・TFI の最良値が一致しない。AutoLaparo の Trans-SVNet で α=3 と α=11 は Edit がほぼ同程度でも TFI の順位が異なる |
| A-96 | Table 1（THUMOS14-C）。ActionFormer＋I3D は clean の mAP 61.53 から corrupted で 50.61（差 −10.92）、TriDet＋VideoMAEv2 は 75.16 から 61.10（差 −14.06）。同じ TriDet に頑健化の学習を足すと corrupted 68.28、clean 75.60。Table 2（ActivityNet-v1.3-C）で ActionFormer＋TSP は 36.50 から 27.79 | corruption で悪化、頑健化の学習で改善 | Figure 5 では corruption が行動の中央に近いほど悪化が大きい一方、境界の近くへの black frame の挿入では clean より良くなる場合もあった（著者は black frame を境界の手がかりとして誤って使った可能性を挙げる）。Figure 4 では corruption による悪化の主因は分類の誤りより位置の誤り（A2s L517） |
| A-97 | 記載なし（表番号未確認） | 著者の要旨では不規則なサンプリングに有効 | 不明 |
| A-98 | 記載なし（表番号未確認） | 報告に記載なし（実時間の欠けを入力できることが前提、と報告は書く） | 不明 |
| A-99 | 記載なし（表未読） | 報告に記載なし | 不明 |
| A-100 | 不明（本文未読） | 報告に記載なし | 不明 |
| A-101 | 記載なし（表番号未確認） | 報告に記載なし | 不明 |
| A-102 | 不明（本文の表は未確認） | 報告に記載なし | 不明 |
| A-103 | 記載なし（表番号未確認） | 報告に記載なし | 不明 |
| A-104 | MASCIT の Table 2 で、34 の不規則なデータセットの available-case の平均 macro-F1 が Raindrop 55.232、MASCIT 69.200（A2s L276。A-108 の行では報告自身が Table 2 の列の対応の読み違いを避けるとして NCDE・Raindrop の値を採用していない〔A2s L365〕） | MASCIT の集計の比較では低い | データセットの構成に依存する |
| A-105 | 記載なし（本文の表は未確認） | 報告に記載なし | 不明 |
| A-106 | 報告は表番号つきで再確認していないため省略 | 報告に記載なし | TIDES の解析では、S5 は物理的な Δ を保持して不規則な間隔に外挿する一方、LTI のため入力に条件づけられたダイナミクスを表せない（否定的な側面。A2s） |
| A-107 | Appendix D／Figure 7 に対応する Fading Flash の sweep で、test Δ=0.1 の relative error は TIDES 6.56、Mamba-3 141.20、Mamba-2 154.08（seed 0 の一回） | TIDES は改善。S5 は Δ の外挿は保つが zone-dependent decay の表現力が足りず、Mamba は学習時の Δ の範囲の外で誤差が急増する（二種類の否定的な結果） | test 時の Δ が学習時の分布から外れるかどうか |
| A-108 | Table 2 の available-case の平均 macro-F1 は MASCIT 69.200、ROCKET 66.890（報告は表の列の対応の読み違いを避けるため、MASCIT と最も近い集計の競合 ROCKET の値だけを採用）。平均 rank は 3.118 と 4.118。MASCIT と ROCKET の Holm 補正の Wilcoxon は p=.394 | 集計の点推定は改善だが、ROCKET との差は統計的に有意でない | データセットの構成により ROCKET の集計の rank が大きく変わる。partial selectivity が full selectivity より有利な傾向 |
| A-109 | §5.1／Table 4。ResNet-38 の overall accuracy の著者のいう largest variance は、もとの条件 2.0%、software randomness 1.4%、hardware nondeterminism 1.2%。per-class accuracy では 10.1%、6.8%、4.9%。inconsistent predictions は 219、216、209。報告の計算では hardware と software の比は overall で約 0.86、per-class で約 0.72、prediction-count で約 0.97（A2s L393。本書の作成者の検算: 1.2／1.4=0.857、4.9／6.8=0.721、209／216=0.968）。決定性の費用: Table 3 で決定性を固定するパッチ＋record-and-replay の学習時間の overhead は著者の集計で 24%〜114%（ResNet-38 1.243 h→1.561 h、WRN-28-10 7.08 h→14.979 h）。record-and-replay 単独の overhead は統計的に有意でなかった | ハードウェアの非決定性は seed／乱数を抑えても残る | モデルと指標に依存。software randomness は seed だけの純粋な分散の成分ではない（A2s） |
| A-110 | 要旨に環境の違いだけで大きな accuracy の範囲があったとの数値の記載があるが、対応する表番号を二ページの本文で確認できなかったため、報告は定量の効果量として採用していない | 環境の変更で結果が変わる | 不明 |
| A-111 | 報告は対応する表を精読していないため数値なし | 版の変更で散らばりが生じうるという結論 | 不明 |
| A-112 | 不明（本文の表は未確認） | 報告に記載なし | 不明 |
| A-113 | Figure 8 で、同じパイプライン・seed・GPU でも異なる木の構造が得られたと記載。score の数値差は報告が未確認 | seed と GPU を固定しても完全には再現しない（否定的な結果） | 条件は end-to-end のソフトウェアのパイプライン（A2s） |
| A-114 | Table 4 の FP64 の summation の microbenchmark で、V100 では SPA 6.456 ms に対し固定順序の AO 87.204 ms（100 sums）。学習の overhead ではなく reduction の kernel の microbenchmark（A2s） | 決定性を固定した演算は再現性を上げうる一方、演算により速度の費用が大きくなりうる | テンソルの次元、reduction の比、演算、ハードウェアに依存 |
| A-115 | 報告は benchmark の表を精読していないため数値なし | プラットフォームをまたぐビット単位の再現性を達成すると報告 | 不明 |

---

## 7. 実装

| ID | コード・重み・ライセンス | 追加データ・注釈 | 事前学習と評価データの重なり |
|---|---|---|---|
| A-01 | データは GitHub（Fujiry0/EgoSurgery）で配布（A2c は「公開予定と記載」。A-06）。GGMAE のコードと重みは不明（A3c）。A3g は公式の GitHub を確認したと書く。A2g はデータのリポジトリは公開、ライセンスは不明と書く | 視線のヒートマップ（Tobii）。クラスの不均衡はリサンプリングで扱う（A2c）。リサンプリングなしの対照は無い（A2g） | 事前学習に使った動画の範囲（学習用の分割だけか）は不明（A3c、A3g） |
| A-02 | GitHub CAIR-HKISI/SurgMotion（Apache-2.0。A2g、A3c）。重みは Hugging Face（A2c、A3g）、申請制で ViT-L（300M）と ViT-g（1B）、Table 3 がどちらの規模かは不明（A3c）。重みのライセンスは不明、論文は CC BY 4.0（A3g）。Hugging Face で同じ ID が「UniSurg」の題で表示される（A2f） | 大規模な手術動画 | 事前学習（Table 1）に EgoSurgery の 21 本が入る。評価に使う動画を除いたとする記述は見つからない（全報告）。事前学習は 1 fps で、EgoSurgery の 0.5 fps と合わない（A3c） |
| A-03 | データは公式のリポジトリ（A-06） | 器具と手の box | 該当なし |
| A-04 | 報告に記載なし | 手と器具の mask | 該当なし |
| A-05 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-06 | Google フォームで申請するとダウンロードのリンクが届く。CC BY-NC-SA 4.0。リポジトリにあるのは assets、LICENSE.txt、README.md だけ（A2f） | 該当なし | 該当なし |
| A-07 | 旧地図に記載なし | 不要 | 該当なし |
| A-08 | 旧地図に記載なし | 不要 | 該当なし |
| A-09 | 旧地図に記載なし | 不要 | 該当なし |
| A-10 | 旧地図に記載なし | 器具の在否の注釈 | 該当なし |
| A-11 | GitHub で公開、ライセンスは不明（A2g） | 不要 | 不明 |
| A-12 | 報告に記載なし | 不要 | 該当なし |
| A-13 | 不明 | 不要 | 不明 |
| A-14 | GitHub（isyangshu/Surgformer） | 不要 | 不明 |
| A-15 | 報告に記載なし | 不要 | 不明 |
| A-16 | GitHub（rcao-hk/SR-Mamba） | 不要 | 不明 |
| A-17 | GitHub（Zxnyyyyy/SPRMamba。A2c）。A2g は不明 | 不要 | 不明 |
| A-18 | v1 では受理の後に公開予定（取得時点の公開の状態は確証なし。A2g） | 工程の進捗の教師 | 不明 |
| A-19 | GitHub（sukjuoh/Surgical-Mamba。A2c）。A2f は不明 | 不要 | 不明 |
| A-20 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-21 | GitHub（lxj22/SurgPLAN-Plus。A2c） | 不要 | 不明 |
| A-22 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-23 | 公式コードのライセンスは取得範囲で不明（A2g） | 不要 | I3D の事前学習が評価データを含むかは論文で問題にしていない（A2g） |
| A-24 | GitHub（Yuhan-Shen/ProTAS）。大部分が MS-TCN のコードから派生、ライセンスは不明（A2g） | 行動の進捗、タスクの構造 | 不明 |
| A-25 | GitHub（jbistanbul/MiniROAD） | 不要 | 該当なし |
| A-26 | 公開（A2f） | 不要 | 該当なし |
| A-27 | 旧地図に記載なし | 不要 | 該当なし |
| A-28 | 旧地図に記載なし | 不要 | 該当なし |
| A-29 | 報告に記載なし | 不要 | 該当なし |
| A-30 | 報告に記載なし | 三人称の映像（学習時） | 報告に記載なし |
| A-31 | 報告に記載なし | 手の位置 | 報告に記載なし |
| A-32 | 報告に記載なし | マルチモーダル | 報告に記載なし |
| A-33 | 報告に記載なし | 不要 | 該当なし |
| A-34 | 報告に記載なし | 不要 | 量の実験は学習用の全体で SSL（A3g） |
| A-35 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-36 | モデルとデータの一部を公開、GitHub は MIT（A3g） | 不要 | 報告に記載なし |
| A-37 | コードと事前学習済みモデルを公開。論文は CC BY 4.0、重みのライセンスは不明（A3g） | 不要 | 報告に記載なし |
| A-38 | 旧地図に記載なし | 不要 | 該当なし |
| A-39 | 公式のコード・データ・モデル。リポジトリは Apache-2.0（A3c、A3g） | 不要 | 開放・一人称の記載なし |
| A-40 | コードと GSViT の重みを公開。重みのライセンスは確認できず（A3g） | 不要 | 開放・一人称は報告されない |
| A-41 | A3c は GitHub で公開予定、ライセンスは不明。A3g はリポジトリとモデルカードはあるが重みの公開は未完了の記載があり、ライセンスの表記も食い違う | 不要 | 評価に使うテスト動画を事前学習と fine-tune から除いたと明記。M2CAI16 と重なる Cholec80 のテスト動画 5 本（73、77、78、79、80）を除いて評価した（A3c、A3g） |
| A-42 | データ・コード・重み（Hugging Face）を公開（A3c）。重みのライセンスは不明（A3c、A3g） | 不要 | 開放・一人称の報告なし |
| A-43 | 公式の実装を確認、リポジトリは Apache-2.0（A3g）。重みは公開予定（A3c） | 不要 | 開放・一人称なし（A3g） |
| A-44 | コードは公開。重みとライセンスは未確定（A3g） | 書き起こしの文 | 開放・一人称の割合は不明（A3g） |
| A-45 | 公開の詳細は未確定（A3g） | 不要 | 手術の開放・一人称なし |
| A-46 | 重みとライセンスは確認できず（A3g） | 不要 | 報告に記載なし |
| A-47 | 旧地図に記載なし | 不要 | 旧地図に記載なし |
| A-48 | 報告に記載なし | 該当なし | 該当なし |
| A-49 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-50 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-51 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-52 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-53 | 報告に記載なし | 不要 | 該当なし |
| A-54 | 報告に記載なし | 不要 | 該当なし |
| A-55 | 報告に記載なし | 報告に記載なし | 該当なし |
| A-56 | 報告に記載なし | 不要 | 報告に記載なし |
| A-57 | 報告に記載なし | 不要 | 報告に記載なし |
| A-58 | 公式のコードとモデル（A3g） | 文 | 該当なし |
| A-59 | 報告に記載なし | 文 | 該当なし |
| A-60 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-61 | 旧地図に記載なし | 旧地図に記載なし | 該当なし |
| A-62 | 旧地図に記載なし | 視線、手の mask | 該当なし |
| A-63 | 旧地図に記載なし | 該当なし | 該当なし |
| A-64 | 報告に記載なし | 物体の領域 | 該当なし |
| A-65 | 報告に記載なし | 視線 | 該当なし |
| A-66 | 報告に記載なし | 視線 | 該当なし |
| A-67 | 報告に記載なし | 視線 | 該当なし |
| A-68 | 報告に記載なし | 視線（予測） | 該当なし |
| A-69 | 報告に記載なし | 視線 | 該当なし |
| A-70 | 報告に記載なし | 報告に記載なし | 分割をまたがないよう患者単位で管理（A3c） |
| A-71 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-72 | 報告に記載なし | 報告に記載なし | 事前学習のデータとテストのデータを重ねないと明記（A3c） |
| A-73 | 報告に記載なし | 報告に記載なし | 対象の領域の注釈のないデータを SSL に使うことを、暗黙の漏れとして論じる（A3c） |
| A-74 | 不明 | 不要 | 該当なし |
| A-75 | GitLab（nct_tso_public/pitfalls_bn）、ライセンスは不明 | 不要 | 該当なし |
| A-76 | 該当なし | 該当なし | 該当なし |
| A-77 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| A-78 | 公開（CAMMA-public/out-of-body-detector）、ライセンスは不明 | 体外の注釈 | 該当なし |
| A-79 | OoBNet による検出と目視の確認 | 該当なし | 該当なし |
| A-80 | 不明 | 該当なし | 該当なし |
| A-81 | 報告に記載なし | 該当なし | 該当なし |
| A-82 | GitHub（yuzhaouoe/pretraining-data-packing） | 不要 | 該当なし |
| A-83 | 報告に記載なし | 不要 | 該当なし |
| A-84 | 報告に記載なし | 不要 | 該当なし |
| A-85 | 第三者の実装（subramen/GRU-D） | 欠けの mask と経過時間 | 該当なし |
| A-86 | GitHub（usyd-fsalab/NeuralNetworkRandomness）。TF 2.4.1、CUDA 11、cuDNN 8 に固定（版の差は測っていない） | 不要 | 該当なし |
| A-87 | GitHub（ceciliaresearch/nondeterminism_instability） | 不要 | 該当なし |
| A-88 | 報告に記載なし | 不要 | 該当なし |
| A-89 | 報告に記載なし | 不要 | 該当なし |
| A-90 | 報告に記載なし | 不要 | 該当なし |
| A-91 | GitHub（GaParmar/clean-fid） | 不要 | 該当なし |
| A-92 | 該当なし | 該当なし | 該当なし |
| A-93 | 該当なし | 該当なし | 該当なし |
| A-94 | 確認できず | 体外フレームの扱いが要る。追加注釈の詳細は不明 | 不明 |
| A-95 | MICCAI の公式ページから StableSPR のリポジトリへのリンクあり。ライセンスは未確認 | 追加注釈なし | 不明 |
| A-96 | code／models の公開を論文が明記。ライセンス不明 | corruption は人工生成 | I3D、VideoMAEv2、TSP の事前学習済みの特徴を使う条件あり。評価データとの重なりの検証は不明 |
| A-97 | 未確認 | 観測時刻が必要 | 該当なし |
| A-98 | 不明 | timestamp／経過時間 | 該当なし |
| A-99 | 不明 | timestamp が必要 | 該当なし |
| A-100 | 不明 | 観測時刻を保持する形式が基本 | 該当なし |
| A-101 | 不明 | 観測の timestamp | 該当なし |
| A-102 | 不明 | timestamp | 該当なし |
| A-103 | 不明 | timestamp | 該当なし |
| A-104 | 未確認 | 不規則な timestamp／センサの識別 | 該当なし |
| A-105 | 不明 | timestamp | 該当なし |
| A-106 | JAX の実装が appendix にある。ライセンスの詳細は不明 | 不規則なサンプリングとして使う場合は真の Δ | 該当なし |
| A-107 | リポジトリの公開を本文が明記。ライセンス不明 | 実 timestamp から得る Δ が必要 | 該当なし |
| A-108 | 確認できず | この実装は経過時間の入力を使わない。timestamp の和集合を連番に詰めるため、事象の順序とマスクの形は残るが物理的な欠けの長さは失われる（著者自身が明記。A2s L373） | 該当なし |
| A-109 | framework を提案。ライセンスの詳細は不明 | 不要 | 主対象ではない |
| A-110 | 不明 | 不要 | 該当なし |
| A-111 | 論文は CC BY。コードは不明 | 不要 | 該当なし |
| A-112 | 不明 | 不要 | 該当なし |
| A-113 | 不明 | 不要 | 該当なし |
| A-114 | リポジトリを論文が参照。ライセンス不明 | 不要 | 該当なし |
| A-115 | Microsoft の RepDL リポジトリを公開。研究用途・非 production とリポジトリが明記。ライセンスは未確認 | 不要 | 該当なし |

---

## 8. 本研究との関係

報告者の一行（各行の本研究との関係についての報告者の要約。A2c・A2f・A3c の詳細記録の [要点] の欄のうち読みを含むもの、A2g・A3g の各記録の末尾の段落）は、報告者の読みを含むため地図から外し、起票者用の文書に移した（F 2026-10-18）。事実としての近さは §3（距離の軸）と §4 の「本研究の条件で測られたか」に書いてある。

本研究の条件（依頼文の背景）: 一人称・開放手術・21 本（主測定は 15 本の動画単位の交差検証）・0.5 fps・online（過去のみ）・ResNet-50 の特徴に因果的な多段の時間畳み込み。区間の境でフレームの連番が振り直される（A2 の問い (9) の字面）。

---

## 9. 依頼文の問い → 行（本書の作成者が行から組んだ索引）

行の選び方は作成者の読みで、報告の答えではない。各問いへの報告の答えの要約は報告者の読みを含むため、起票者用の文書に置いた。

| 問い | 主な行 | 見つからなかったもの・未検証の組み合わせ |
|---|---|---|
| A2 (1) 時間モデルの系統 | §1.1 の全系統 | — |
| A2 (2) 少数動画での効き方 | §4 の「本研究の条件で測られたか」に少数動画とある行: A-01、A-02、A-07、A-08、A-12、A-15、A-23、A-24、A-25、A-34、A-37、A-47。学習の動画数を変えた行: A-10（10〜40 本）、A-34（5・10・40 本）、A-37（2・4・8 本） | §10.1（系統ごとの少数動画の学習曲線）、§11.1 |
| A2 (3) 時間モデルの差と backbone の差 | A-12（Table I）、A-02（Table 3）、A-01（Table 1・2） | §10.2（EgoSurgery で同じ特徴のまま時間モデルを差し替えた研究） |
| A2 (4) EgoSurgery-Phase の報告値 | A-01（Table 1〜3）、A-02（Table 3）。A-36、A-37、A-39、A-40、A-43〜A-46、A-53、A-56 の §6 に A-02 の Table 3 の値を転記 | §10.1、§10.4 |
| A2 (5) 一人称の非手術の online | A-23、A-24、A-30、A-31、A-32、A-33 | §10.2（一人称の大型データの過去のみの密な分割） |
| A2 (6) 損失の工夫が効かなかった報告 | A-23（後処理で Acc が下がる）、A-12（特徴の拡張と平滑化損失）、A-26、A-01（リサンプリングの対照なし） | §10.1、§10.2（損失の否定的な ablation） |
| A2 (7) offline → online の落ち方 | A-23（付録 Table 12）、A-24（offline 学習 → online 推論）、A-12（Table I と Table II）、A-21 | §11.2 |
| A2 (8) 評価の規約・境界の緩和・数値の出所 | A-74、A-76、A-77、A-11、A-15、A-19 | — |
| A2 (9) 欠けのある区間の列 | §1.2 の行。A-01・A-06（EgoSurgery の欠けの記載）。A2s の行: A-94〜A-96（欠け・破損のある映像）、A-97〜A-108（経過時間・連続時間・不規則時刻のモデル。A-108 は経過時間を使わない例） | §10.2・§10.3・§10.7、§11.3・§11.7 |
| A2 (10) 計算機による散らばり | §1.3 の行。A2s の行: A-109〜A-115（A-109 はソフトウェアとハードウェアの散らばりの分解の数値、A-113 は同じ seed・GPU でも再現しない例） | §10.2・§10.3・§10.7、§11.3・§11.7 |
| A3 (1) 対象データ上の SSL と一般の重み | A-01、A-34、A-35、A-37、A-38 | §10.4、§11.4・§11.5 |
| A3 (2) 事前知識でマスクを選ぶ | A-01、A-02、A-55、A-64 | §10.5（顕著性だけでマスクを選ぶ手術の MAE） |
| A3 (3) 手術基盤モデルの一覧 | §1.4 の行。各行の §3（データ規模）と §7 | §10.5（AVOS の原典） |
| A3 (4) 学習に使われていない種類の手術への転移 | A-02（Table 3）、A-41（眼科）、A-49（顕微鏡）、A-50（凍結と fine-tune） | §10.5、§11.5 |
| A3 (5) 領域適応としての継続事前学習 | A-34、A-36、A-52、A-70、A-71（否定的な結果） | §11.4・§11.5 |
| A3 (6) ResNet 系と ViT 系 | A-45、A-42、A-36、A-34 | §10.5 |
| A3 (7) 評価に使う動画が事前学習に入る場合 | A-02、A-41、A-01、A-72、A-73 | §10.5、§11.4・§11.5 |
| A3 (8) クリップのモデルを online で使う | A-14、A-22、A-19、A-43、A-09 | §10.5、§11.4 |
| A3 (9) 一人称の非手術の事前学習の転移 | A-58、A-59、A-60、A-61、A-68 | §10.5 |
| A3 (10) 事前学習が効かなかった報告 | A-34、A-37、A-38、A-01（τ）、A-42、A-02（手術の基盤モデルと DINOv3）、A-71、A-72 | §12.5 の否定的な結果の一覧 |
| A3 特に確かめたい事実 | GGMAE の Table 2 は A-01、SurgMotion は A-02、SurgVISTA は A-41 | §10.4・§10.5 |

---

## 10. 見つからなかったもの

「見つからなかった」は、報告がその手段・検索語・範囲で確認できなかったという意味で、存在しないという主張ではない（各報告の定義。F 2026-10-18）。件数は報告の記載で、定義は報告ごとに違う（§12）。

### 10.1 A2c（L543–L555）

- **種の実在の確認。** 実在と ID を確認できたもの: SR-Mamba、SPRMamba、HID-SSM、MS-ASCT、Surgformer、SurgMotion、Ego-Exo4D。SKiT（ICCV 2023）と TMRNet（IEEE TMI 2021）は他の論文の引用から実在を確認したが、ID は未確認で本文も未読。Assembly101・Ego4D・HoloAssist・EgoProceL は原典の ID を未確認（検索の予算切れ。検索語「Assembly101 CVPR 2022 arXiv」「HoloAssist ICCV 2023 arXiv」「EgoProceL ECCV 2022」）
- **EgoSurgery-Phase を評価に使った論文。** 原論文と SurgMotion のほかに、規約がはっきりした報告は無かった（約 27 件を確認）。視線を時間モデルに入れた後続の研究も見つからない
- **約 9 件ずつ確認して該当が無かったもの。** 系統ごとの少数動画での学習曲線／0.5 fps の ablation／focal loss・class-balanced loss が効かなかったという表／二段階の学習での特徴の過適合を定量化した研究／21 本規模での分散の推定／一人称特有の要因が手術の時間モデルの選択に与える影響

### 10.2 A2g（L451–L501）

- **EgoSurgery の過去のみの条件で、構造を統制した研究。** 検索語: EgoSurgery online phase recognition causal／EgoSurgery temporal model／EgoSurgery Mamba／EgoSurgery Transformer／EgoSurgery state space model／EgoSurgery TeCNO。見つからなかったもの: 同じ ResNet-50／ViT、同じ特徴、同じ train／val／test の分割のまま、TeCNO、因果的な Transformer、記憶、前向きの Mamba を差し替えた研究。原論文の Table 1 は backbone と時間モデルが同時に変わる
- **EgoSurgery での SSM／Mamba。** 検索語: EgoSurgery Mamba／EgoSurgery SSM／open surgery Mamba phase recognition。EgoSurgery-Phase に厳密に因果的な Mamba／SSM を当てた表番号つきの報告は見つからない。SR-Mamba・SPRMamba・HID-SSM・PhaseMamba はすべて他の手術データ
- **実際の欠け・区間の切れ目を統制した研究。** 検索語の概念: discontinuous surgical video temporal model／video gaps causal temporal segmentation／reset hidden state surgical phase／missing interval Mamba TCN／streaming action segmentation interrupted actions。OnlineTAS は途切れた行動を限界として挙げ、無限長の stream の記憶の管理を未解決の課題とするが、人工的な欠けを入れて性能を測る実験はしていない。「30 秒／1 分／5 分の欠落」「動画の断片をつなぐ」「欠けの token」「隠れ状態の初期化」の有無を独立変数にした EgoSurgery または手術工程の研究は見つからない
- **損失の否定的な ablation。** 検索語の概念: surgical phase recognition smoothing loss ablation／boundary loss no improvement surgical phase／class imbalance weighting phase recognition ablation／MS-TCN smoothing loss negative result。同じ構造・同じ分割のまま平滑化の損失・境界の損失・クラスの重みを一つずつ入れ切りし、「有意に悪化」「差なし」と結論した近年の手術工程の論文は見つからない。A2g はこれを「効く」という意味ではなく、論文が ablation を報告していないという意味だと書く（L453）。EgoSurgery はクラスの不均衡にリサンプリングを使うが、リサンプリングなしの基準を示していないため、効いた量は不明
- **計算環境の差を統制した再現性の研究。** 検索語の概念: surgical phase recognition reproducibility GPU seed／TeCNO reproducibility CUDA／TMRNet reproduce results／temporal action segmentation seed variance。同じ checkpoint・学習コードを TITAN RTX／A100／H100／H800、異なる CUDA／cuDNN で繰り返し、計算機による工程の指標の散らばりを表にした研究は見つからない。見つかったのは計算機の仕様の記載と個別の再現の issue まで
- **一人称の大型データの、過去のみの密な分割。** Assembly101（4,321 本、固定 8 視点＋一人称 4 視点）、Ego4D、Ego-Exo4D、HoloAssist、EPIC-KITCHENS は、確認した範囲で EgoSurgery と完全に同じ過去のみの密な手順の分割を標準のベンチマークにしているわけではない

### 10.3 A2f（L390–L399）

- **EgoSurgery-Phase を使った論文で、欠けの扱いを明記したもの。** 検索語「EgoSurgery-Phase phase recognition open surgery egocentric」「EgoSurgery-Phase benchmark phase recognition results 2025」「SurgMotion arXiv 2602.05638」。約 25 件を確認し 4 件（A-01、A-06、A-03、A-02）を読んで 0 件。EgoSurgery-HTS は要旨の断片しか見られず未確認
- **配布データのフレーム名・元の時刻。** README に記載なし。申請制のため確認できず不明
- **黒塗りと削除を時間モデルの性能で比べた研究。** 検索語「out-of-body detection anonymization laparoscopic video OoBNet」で約 8 件を確認して 0 件
- **欠けの中の工程の境界による Edit・F1@k のゆれ、欠けが残り時間の推定や ProTAS の経過時間をずらす問題。** 専用の検索は予算不足で実施できず、関連の検索の範囲では 0 件
- **手術映像・行動分割で、GPU・精度・版による散らばりを seed による差と分けた研究。** 検索語「MS-TCN reproduce results different GPU variance temporal action segmentation seeds」「surgical phase recognition reproducibility reimplementation results differ reported Cholec80 benchmark」で約 18 件を確認して 0 件
- **混合精度、DDP の GPU 数、BN の同期、worker 数、動画のデコーダ（ffmpeg・decord・PyAV・OpenCV）の影響。** 本文で確認できたものは 0 件。Zhuang ほか（A-86）は分散学習を対象外と明記
- **チャレンジ（EndoVis、PitVis、SurgVU、HeiChole）での再実行の差、GitHub の issue での環境の差。** 0 件（GitHub の issue の検索は未実施）
- **方向七の独立の検索。** 検索の予算（18 回）を使い切ったため実施できなかった。否定的・中立的な所見は既読の文献から拾った（A-75 の BN での CHT の悪化、A-25 の動画全体での学習でほぼ差なし、A-82 の BM25Chunk が INTRADoc と同等、A-86 の top-line への影響の小ささ）

### 10.4 A3c（L122–L126）

- **「EgoSurgery」「egocentric open surgery phase」（2 回、計約 20 件）。** SurgMotion のほかに EgoSurgery-Phase の工程認識の値を報告した論文は見つからない。ORQA は QA のデータとして使うだけで、EgoSurgery-Tool と EgoSurgery-HTS は検出・分割の課題
- **「frame rate sampling stride video MAE low fps」（約 8 件）。** 1 fps 以下で映像の SSL や基盤モデルを評価した研究、フレームレートの不一致が転移に与える影響を測った研究は見つからない
- **「variance across splits seeds surgical phase」。** 検索の予算が尽きて実行できなかった。SelfSupSurg §4.1 に、少データの設定では分割の間の性能のばらつきが手法の間の差を上回りうるという記述がある。同じ論文の注 8 では再実行 5 回の標準偏差が phase F1 で 0.7%。ばらつきを主題にした独立の文献と Metrics Reloaded は未確認
- **術者・施設をまたぐ漏れ。** EgoSurgery の術者 8 人・術式 10 種はデータセット論文に記載がある。どの動画がどの術者のものかの対応表と、術者単位で分割した評価は見つからない

### 10.5 A3g（L258–L282）

- **GGMAE の事前学習を折りの学習用の動画に限ったとする記述。** EgoSurgery GGMAE pretrain split train test／EgoSurgery self-supervised pretraining train split／2405.19644 seed／pretrain split で本文を追ったが、SSL を学習用の 14 本に限る、test の 5 本を SSL にも使わない、とする文章を確認できなかった。seed の数も確認できない
- **SurgMotion の EgoSurgery の評価の手順。** EgoSurgery split／fold／train split／test split／seed／exclude を確認したが、Table 3 が公式分割か独自の分割か、5 分割かを特定できない。事前学習の Table 1 には EgoSurgery が明記される
- **SurgMotion の査読版。** 2026-10-05 の時点で、題名・arXiv・掲載先の検索から査読つきの会議・論文誌の版を確認できなかった
- **DINOv3・V-JEPA 2・VideoMAE V2・手術の基盤モデルを同じ EgoSurgery の 5 分割で、凍結と全体の fine-tune の両方まで揃えた研究。** 見つからない。SurgMotion は DINOv3 と VideoMAE を凍結の probe で比べるが V-JEPA 2・VideoMAE V2 が無く、全体の fine-tune も無い。EgoSurgery-Phase は VideoMAE V2 を含むが、公開の一般の checkpoint の比較ではなく、対象データ上の事前学習とマスクの比較
- **汚染の無い、手術の基盤モデルから一人称の開放手術への転移。** SurgMotion 自身は EgoSurgery を事前学習に含む。EndoFM などには EgoSurgery の混入の証拠は無いが、評価の分割が十分に記述されていない
- **EgoVLP／EgoVLPv2 から手術の工程認識への転移。** EgoVLP surgery／Ego4D surgical transfer／EPIC-KITCHENS surgical video pretraining／egocentric pretrained surgical phase recognition の系を追ったが、公開の重みをそのまま EgoSurgery・開放手術に移す直接の研究を確認できない
- **種の「Ego-Exo」。** どの論文を指すかを原典まで一意に確認できず、実在未確認として記録から外した
- **顕著性でマスクを選ぶ手術の MAE。** saliency-guided masking surgical MAE／surgical video saliency masked autoencoder／object guided surgical masking を検索した。物体で選ぶ一般映像の論文、視線の GGMAE、動きの SurgMotion は見つかったが、視覚の顕著性の地図だけを事前知識にして手術の MAE のマスクを選び、random／tube と統制して比べた査読論文は見つからない
- **過去だけの clip と未来を含む clip の性能差。** online surgical phase recognition causal future frames／causal vs offline surgical phase recognition／trailing clip surgical phase recognition を検索し、LoViT や EndoMamba などの因果的な系統は確認したが、同じ映像の基盤モデル・同じ分割・同じ clip の長さで「中央に置く・未来あり」と「過去だけ」を一要素だけ変えた劣化の表は見つからない
- **同じ手術のコーパス・同じ SSL の損失・同じ増強・同じパラメータ数での ResNet-50 対 ViT。** GastroNet の ResNet50／ViT-S、LEMON の ConvNeXt／ViT、SurgeNetXL の ConvNeXt／PVTv2／CAFormer は近いが、要求を完全に満たす統制された比較は見つからない
- **AVOS の原典と視点の構成。** SurgMotion の Table 1 に AVOS が出ることは確認したが、AVOS の元のデータセットの論文、DOI／arXiv ID、開放・内視鏡・三人称の内訳を原典まで追い切れなかった
- **走査の偏り（報告の自己申告、L282）。** MICCAI、CVPR、NeurIPS、MedIA、npj Digital Medicine、IJCARS の関連の原著は本文まで確認した。IPCAI、ICCV、ECCV、ICLR、IEEE TMI の 2024〜2026 の全号を会議・論文誌ごとに走査するところまでは完了していない

### 10.7 A2s（L505–L543）

欠けのある系列について（L507–L521）:

- **EgoSurgery で「注釈の区間をつないで時間状態を持ち越す」対「各区間で初期化」を同じモデル・同じ分割で直接 ablate した論文。** 検索語: EgoSurgery missing frames temporal state reset／EgoSurgery discontinuous clips causal TCN／surgical phase recognition out-of-body reset hidden state／surgical workflow removed frames temporal continuity。EgoSurgery の論文は個人情報のフレームの除去と 0.5 fps の間引きを説明するが、その結果の配布の系列の欠けの境で因果的な時間状態をどう扱うかの ablation は本文に無い（報告の記載）。同じ設定の EgoSurgery の文献 4 件、近い手術の OOB・プライバシーの文献を少なくとも 8 件確認して、直接の比較は 0 件。Bayat ほか（A-94）は OOB が時間モデルに悪影響を与えるところまでは直接扱う
- **削除区間をまたいだ注意・状態の持ち越しを禁じても改善しなかった、あるいは悪化したという手術工程の否定的な ablation。** 確認できず。方向七の検索では代わりに StableSPR（A-95）の過去の状態の誤りの前方への伝播と、一般の時間的行動検出（A-96）の corruption の位置で効果の符号が変わる現象が見つかった
- **Edit・F1@k を「残った区間ごと」に算出した場合と「欠けを消してつないだ一本の系列」として算出した場合を、同じ予測で直接比べた研究。** 確認できず。StableSPR は別の問題として、Edit が圧縮した segment のトークンだけを評価するため、segment 内の時間的な不安定さが異なる二つの予測に同じ Edit を与えうることを具体例で示す
- **欠けの中に工程の遷移がある場合の境界の誤りの identifiability を手術工程のベンチマークで定量化した研究。** 確認できず。一般の時間的行動検出では Zeng ほか（A-96）が corruption の主な悪化を分類の誤りより位置の誤りに帰す（Figure 4）
- **残り時間の予測や経過時間の特徴が、未知の長さの削除区間でどれだけずれるかを EgoSurgery 型のデータで測った研究。** 確認できず。T-LSTM、mTAN、Latent ODE、S5、TIDES は timestamp がある場合の解決法で、消えた欠けの長さを推定する方法ではない（報告の記載）。MASCIT（A-108）は timestamp を連番に置き換えるため経過時間の欠けを失い、物理的な欠けをモデル化しないと著者が明記する

計算環境差について（L523–L543）:

- **EgoSurgery、Cholec80、AutoLaparo などで、折りと seed を完全に対応させながら GPU の型だけを変え、macro Jaccard／accuracy の計算機の散らばりと seed の散らばりを分散の成分として同時に推定した研究。** 検索語: surgical phase recognition GPU reproducibility seed standard deviation／Cholec80 hardware reproducibility CUDA／action segmentation GPU seed variance／temporal action segmentation deterministic GPU。Renard（A-92）、Metrics Matter（A-74）、C2F-TCN（A-29）、CPKD（A-77）などの周辺の資料は確認したが、直接の実験は 0 件
- **fp16 対 bf16 対 TF32 を手術の工程・行動分割の同じ処方で比べた報告。** 確認できず。一般の深層学習では精度と累算の順序が再現性の源になることは確認できる（A-114）が、少数動画の工程モデルに移したときの pp 単位の値は文献からは出せない（報告の記載）
- **GPU 数、per-GPU の batch、global batch、DDP の reduction、SyncBatchNorm のうち一要素だけを変えた手術・行動分割の再現性の研究。** 確認できず。PyTorch のコミュニティに multi-GPU の乱数の再現性の問題の実例はあるが、査読つきの手術のベンチマークの効果量には使えない
- **decord、PyAV、torchvision、OpenCV の decoder だけを変えて手術・行動認識の値を比べた査読研究。** 確認できず（decoder の性能〔performance〕の benchmark は見つかったが、モデルの精度の統制された比較ではない）
- **resize の実装、anti-alias、JPEG の再圧縮を手術の工程モデルで単独化した研究。** 確認できず。Parmar ほか（A-91）は前処理の実装が下流の指標を変える既存の例だが、工程認識の直接の証拠ではない。一般の画像認識では JPEG の圧縮が精度を変える研究があるため「影響なし」とは言えないが、EgoSurgery の効果量への換算はできない（報告の記載）
- **EndoVis、PitVis、SurgVU、HeiChole で同じ submission／container を異なる計算機で再実行した値の差の系統的な報告。** 確認できず。SurgToolLoc／SurgVU のチャレンジの報告は Grand Challenge の container による標準化した実行を採るが、同じ container を二つのハードウェアで走らせた差の定量の表は確認できなかった
- **公開リポジトリの issue。** NVIDIA framework-reproducibility に TensorFlow 2.5 で同じ data／model／loop／seed でも再現しない issue はあるが、手術映像のリポジトリの定量の再現の issue は見つからなかった
- **「決定性のフラグを入れても手術映像の値の散らばりが減らなかった」という直接の否定的な結果。** 確認できず。一般の深層学習では Zhuang ほか（A-86）が一つの源だけを除いても stability がほとんど改善しない場合を、Ravi ほか（A-113）が同じ seed・同じ GPU でも構造の差が残る場合を報告
- **Metrics Reloaded。** DOI／arXiv を一次資料で再確認できず、書誌・数値は使っていない（検索語: "Metrics Reloaded" recommendations image analysis validation DOI／"Metrics Reloaded" metric selection segmentation）

### 10.6 旧地図 A（v1）の A.2

旧地図の見つからなかったもの（検索語は §12.6）: EgoSurgery-Phase／開放手術の一人称で、未来のフレームを明示的に禁じた厳密に因果的なモデルの表／EgoSurgery-Tool と EgoSurgery-Phase を同じ因果的なネットワークで同時に学習し、14 から 21 動画で Jaccard・F1 を報告した研究／同じ構成・同じ分割で非因果と厳密に因果を一表で比べた行動分割の研究／Ego4D・EPIC・EGTEA で事前学習した一人称の backbone を小規模の手術工程へ移して因果的に測った研究。（本書の作成者の注記: このうち三つ目に近い比較として、A2g が OnlineTAS の付録 Table 12〔同じ ASFormer の offline と過去のみ〕を記録している。A-23）

---

## 11. 未検証の組み合わせ

報告が確認した文献の集合を並べたとき、その条件を同時に満たす測定を確認できなかった組み合わせ。誰も行っていないという意味ではない（報告の定義。F 2026-10-18）。

### 11.1 A2c（L557–L566）

1. EgoSurgery で、同じ ResNet-50 のまま時間モデルだけを変える比較
2. EgoSurgery × 時間文脈つきの抽出器（L=8〜64）
3. EgoSurgery × ProTAS 型の進捗予測とタスクグラフ
4. EgoSurgery × online の後処理 × Edit／F1@k での評価
5. 0.5 fps × 長時間文脈・多尺度・SSM
6. 学習 10〜15 本 × SSM
7. 凍結した映像の基盤モデル × 因果的な時間ヘッド
8. 視線・手・器具の情報を時間モデルに入力する
9. EgoSurgery × 複数の seed・交差検証

### 11.2 A2g（L503–L530）

いずれも「既存の片側の証拠」はあるが EgoSurgery では未検証と A2g は書く（片側の証拠は括弧の中）。

1. ResNet-50 の特徴 × 因果的な前向きの Mamba（HID-SSM・PhaseMamba が手術の online の SSM の根拠）
2. ResNet-50 の特徴 × OnlineTAS 型の適応的な記憶（GTEA・50Salads の過去のみの条件で改善）
3. ResNet-50 × MS-ASCT 型の因果的な多尺度の注意（手術の online の多尺度 Transformer の根拠）
4. TeCNO × 明示的な長期の記憶（因果 TCN と記憶はそれぞれ別に強い）
5. TeCNO × 進捗予測（ProTAS が非手術の一人称で支持）
6. TeCNO × 手術のタスクグラフ（ProTAS のタスクグラフが一人称の手順で支持）
7. 因果的な SSM × 進捗の教師（HID-SSM が近いが複数の要素が交絡）
8. 因果的な時間モデル × 視線の特徴（GGMAE は視線を事前学習のマスクに使う。online の時間の条件付けは未検証）
9. 時間ヘッドを固定 × GGMAE／SurgMotion／SelfSupSurg の特徴（表現の差は既に大きい）
10. 同じ backbone × TCN／RNN／Transformer／SSM（一般の行動分割には部分的な証拠）
11. 欠けを意識した初期化 × SSM（SSM は状態を保持できる）
12. 欠けを意識した初期化 × 因果 TCN（受容野は有限）
13. 因果的なモデル × 境界を意識した損失（行動分割では境界の問題が大きい）
14. 因果的なモデル × 確信度による online の後処理（OnlineTAS Table 8 で segment の指標が改善）
15. 言語・VLM の意味の事前知識 × 因果的な時間ヘッド（EgoVLP／SurgVLP／TOAD／PREGO 系に周辺の証拠）
16. 物体・器具の状態 × 工程モデル（EgoSurgery-Tool／HTS が同じ映像の領域に在る）
17. 術者を分けた分割 × 時間モデルの構造（21 本・術者 8 人）
18. 術式を外した分割 × 時間モデルの構造（10 術式）
19. 5 seed × 固定の分割（多くの論文は 1 回の run か seed が不明）
20. 5 分割 × 5 seed
21. TITAN RTX／Ampere／Hopper × 厳密に決定性を固定した設定（計算機は論文ごとに違う）

### 11.3 A2f（L403–L412）

1. 連番を振り直した区間の列 × 因果 TCN（TeCNO 型）× 「つなぐ／区間ごとに初期化／つないで欠けの長さを与える」。A-75 は連続動画の LSTM、A-25 は連続動画の GRU、A-82 は文書の列の Transformer を扱う
2. Δt の埋め込み（A-85 の系統）× 映像の工程認識
3. 黒塗りで保った時間軸（A-79）× 時間モデルで黒塗りのフレームを入力するかマスクするか
4. 欠けのある系列での学習・評価 × 連続映像での運用のずれ。A-25 はクリップと連続のずれを測ったが、欠けの有無によるずれは測っていない
5. A-82 の「関連性が高ければ境を越えても害が小さい」を、同じ手術の中の区間で確かめたもの
6. GPU・精度・版による散らばり × 手術工程認識・行動分割 × テスト 5 本
7. 二段階の学習（抽出器の fine-tune → 特徴の保存 → 時間モデル）で、計算機による差がどちらの段で生じるかの分解。A-12 の 5×5 の設計は seed だけを変えている
8. GPU 数による BN の統計 × 抽出器の fine-tune × 下流の時間モデルの散らばり

### 11.4 A3c（L128–L133）

1. 0.5 fps × クリップのモデル（tubelet 2）× online。GGMAE の 10 フレームのクリップは 20 秒分に当たるが、推論の規約は不明
2. DINOv3 や V-JEPA 2 の重みを初期値にし、EgoSurgery の上で視線マスクの継続 SSL を行う組み合わせ。GGMAE はスクラッチの ViT-S しか試していない
3. ResNet-50 の SSL（SelfSupSurg 型）と ViT の MAE を、EgoSurgery で同じ条件で比べた研究
4. 視線をマスクに使う場合と、crop・注意の教師・入力のチャネルに使う場合を、同じ分割で比べた研究
5. 評価の動画を事前学習に含める場合と除く場合を、EgoSurgery で並べた研究

### 11.5 A3g（L284–L308）

1. 一般の基盤モデル・手術の基盤モデル・一人称の基盤モデルを、同じ 5 分割の動画単位の分割で比べる実験。現状、GGMAE は対象領域のマスクの比較、SurgMotion は凍結の attentive probe、EndoViT・SelfSupSurg は腹腔鏡のデータ、EgoVLP は非医療の一人称のデータで、評価の規約が分かれている
2. DINOv3 から、EgoSurgery の学習用の折りだけでの SSL の継続
3. 公開の V-JEPA 2 の重みを EgoSurgery で凍結・fine-tune した比較（SurgMotion は JEPA 系だが EgoSurgery を含むコーパスで新たに事前学習した別のモデル）
4. VideoMAE V2 の公開の一般の checkpoint と、EgoSurgery だけでの VideoMAE V2 の SSL の直接の比較（GGMAE の VideoMAE V2 の行は後者に近い）
5. EgoVLP／EgoVLPv2 から開放手術へ（「手術の領域は違うが視点は近い」事前学習と「手術の領域は近いが内視鏡の視点は違う」事前学習の比較）
6. 視線で導く SSL を強い事前学習の初期値から始める実験（GGMAE の +3.3 Jaccard は ImageNet や DINOv3・V-JEPA 2 の初期値と組み合わせていない）
7. random／視線／動き／視線＋動きを、backbone・マスク比・学習の計算量を固定して比べる研究
8. 一人称の開放手術に対する手術の基盤モデルの全体の fine-tune（SurgMotion Table 3 は凍結の転移だけ）
9. 顕微鏡の手術への転移（SurgVISTA は事前学習から分離した眼科・白内障のデータを分布外のベンチマークに含むが、DINOv3・V-JEPA 2・SurgMotion などまで同じ条件で揃えた比較ではない）
10. 同じ映像の基盤モデルを「未来を含む clip」と「現在までの clip」で比べる online の劣化の実験
11. 各折りの学習用の動画だけで SSL する場合と、test の折りもラベルを隠して SSL に使う場合の同条件の比較（SurgVISTA は前者を守る例、SurgMotion は評価のデータが事前学習に入る例）

### 11.7 A2s（L545–L567）

報告は「存在しない」と断定せず、確認した文献群で対応する統制実験を確認できなかった組み合わせとして表にしている（左が組み合わせ、中が文献で片側まで分かっていること、右が未検証の部分）。

1. EgoSurgery × 状態の持ち越し／初期化。片側: EgoSurgery は個人情報のフレームの除去を行う（A-01）。未検証: 同じ因果 TeCNO で欠けの境だけを変えた macro Jaccard／accuracy
2. EgoSurgery × 境のマスクだけ。片側: MASCIT（A-108）はマスクの形を使える。未検証: 実時間の長さの無い二値の不連続のフラグが工程認識に何をするか
3. EgoSurgery × 真の Δ を使う S5／TIDES（A-106、A-107）。片側: 物理的な Δ を状態の離散化に使える。未検証: 配布物では Δ が不明。元の timestamp を回収した場合の比較
4. EgoSurgery × Neural CDE／Latent ODE（A-103、A-101）。片側: 不規則な timestamp 自体は扱える。未検証: 開放手術の online 工程認識への適用
5. 手術の工程 × FrameDrop の頑健化の学習。片側: CVPR 2024 の時間的行動検出（A-96）では破損したフレームへの頑健性が上がる。未検証: 0.5 fps の手術の疎なフレームで同じ符号か
6. 欠けの中の遷移 × Edit／F1@k。片側: Edit は圧縮した segment の列を見るため内部の時間的な不安定さを失う（A-95）。未検証: 欠けを消したつないだ評価と区間別の評価の定量の差
7. 欠けの中の遷移 × macro Jaccard。片側: Jaccard は観測したフレームの confusion を評価できる。未検証: 予測の状態を同じに固定した場合、評価の境の処理そのものの影響はどこまであるか
8. 未知の欠け × 残り時間。片側: 経過時間を使うモデルは timestamp があれば使える。未検証: 欠けの長さそのものが欠落した場合の識別不能性を手術のベンチマークで測った研究
9. 手術映像 × GPU の型と seed の交差。片側: 一般の深層学習ではハードウェアの効果がソフトウェアの乱数と同じ桁の例（A-109）。未検証: Cholec80／EgoSurgery の工程の指標での分散の成分
10. 手術映像 × fp32／fp16／bf16／TF32。片側: 数値精度と reduction の順序は一般の深層学習で要因（A-114）。未検証: macro Jaccard／accuracy への定量の効果
11. 手術映像 × 一つの GPU／複数の GPU＋SyncBN。片側: BatchNorm と映像の学習の相互作用は Rivoir ほか（A-75）が扱う。未検証: 計算機の数だけを変えた対応づけた再実行
12. 手術映像 × decoder の実装。片側: decoder の実装差は存在する。未検証: decord／PyAV／torchvision／OpenCV の同じ decoded frame の hash と最終の値の比較
13. 手術映像 × resize／JPEG のパイプライン。片側: clean-fid（A-91）などは前処理の実装差の重要性を示す。未検証: 同じ EgoSurgery の分割・モデルでパイプラインだけを変えた差
14. 決定性のモード × seed の SD の減少。片側: 決定性を固定するパッチは費用があり、全ての源を一つずつ消しても stability が単純には改善しない研究がある（行の対応づけ A-109・A-86 は本書の作成者。報告のこの項には引用が無い）。未検証: 手術工程認識で seed の SD の何 % が減るか
15. チャレンジの container × 異種の GPU での再実行。片側: SurgVU 系のチャレンジは container で標準化した実行を採る。未検証: GPU を変えた同じ container の値のずれ

報告は表の後に、Zeng ほか（A-96）の Figure 5 で行動の境界の近くの black frame が逆に位置の推定を助ける場合があり、欠け・境の人工物自体が近道の手がかりになりうると書く（L567）。

### 11.6 旧地図 A（v1）の A.3

組み合わせだけを移した（旧地図の「未検証の理由の仮説」は報告者の読みのため起票者用の文書に移した）: GGMAE／VideoMAE 系の対象領域の事前学習 ＋ 因果的な TeCNO／LoViT 型のヘッド（EgoSurgery-Phase）／手術の masked-video 事前学習 ＋ 凍結・部分凍結の backbone ＋ 因果的なヘッド／EgoVLP・EgoClip の初期化 ＋ 開放手術の工程／EgoSurgery-Tool の補助教師 ＋ EgoSurgery-Phase ＋ 因果的な推論／ASFormer 型の局所・階層の注意を因果的なマスクにする／MS-TCN の truncated-MSE の平滑化損失 ＋ EgoSurgery の因果 TCN／視線を事前学習だけに使い、推論は RGB だけの因果的な長い履歴のモデル

---

## 12. 検索記録

### 12.1 A2c

**検索日:** 2026-10-08。web_search 18 回（うち 1 回は予算切れで失敗）（L569）。報告の冒頭に、検索の上限（18 回）に届いたため方向三〜五と七は依頼された深さまで読み切れていない、Assembly101・Ego4D・HoloAssist・EgoProceL・SKiT・TMRNet の原典の ID も確認できていない、記録 16〜21 は 50,000 字の制限に合わせて欄をまとめた形にした、と書く（L3）。

| 方向 | 検索回数 | 関連した件数 | 記録したもの |
|---|---|---|---|
| 一 EgoSurgery | 4 | 約 15 | 5（A-01、A-02、A-03、A-04、A-05） |
| 二 手術一般 | 8 | 約 40 | 9（A-19、A-16、A-17、A-18、A-13、A-14、A-15、A-12、A-21） |
| 三 一人称の非手術 | 2 | 約 12 | 3（A-24、A-30、A-31） |
| 四 一般映像 | 2（うち 1 回失敗） | 約 8 | 1（A-23） |
| 五 機構の一般論 | 0 | — | 0（関連の話題は A-24・A-30 の記録の中で扱った） |
| 六 方法論 | 3 | 約 20 | 3（A-74、A-75、A-76） |
| 七 否定的な結果 | 1 | — | 他の記録から抽出。網羅できていない |

### 12.2 A2g

**検索日:** 2026-10-19（Asia/Tokyo）。件数は検索結果の総数ではなく、実在を確認し、本文・要旨・公式のリポジトリのいずれかまで関連性を判定した一意の文献・資料の数（報告の定義、L535）。

| 方向 | 主な検索語（報告の記載） | 件数 | 主な発見（報告の記載） |
|---|---|---|---|
| 一 同じデータ・一人称の開放手術 | EgoSurgery phase recognition／EgoSurgery temporal／EgoSurgery Mamba／open surgery egocentric phase／SurgMotion EgoSurgery | 6 | EgoSurgery-Phase、リポジトリ、EgoSurgery-Tool、HTS、SurgMotion、SurgAtlas。過去のみの SSM は 0 件 |
| 二 手術一般 | surgical phase online transformer／causal surgical phase／Mamba surgical phase／state space surgical phase／multi-scale surgical phase | 16 | TeCNO、Trans-SVNet、LoViT、TMRNet、MS-ASCT、Surgformer、SR-Mamba、SPRMamba、HID-SSM、PhaseMamba、SurgicalMamba、SurgPLAN++、MoSFormer など |
| 三 一人称の非手術 | egocentric online action segmentation／ProTAS GTEA EgoProceL／online procedural video／Ego4D procedural／Assembly101 online segmentation | 12 | ProTAS。GTEA／OnlineTAS、Assembly101、Ego4D、Ego-Exo4D、PREGO／TI-PREGO を確認 |
| 四 一般映像 | online temporal action segmentation／online action detection transformer memory／causal TAS／streaming action segmentation | 14 | OnlineTAS、LSTR、MiniROAD、OadTR、MAT、E2E-LOAD、MATR、HAT、TeSTra など |
| 五 機構の一般論 | task graph online segmentation／progress action segmentation／video language online action detection／memory state space long video／distillation online action detection | 10 | 明示的な記憶、タスクグラフ・進捗、言語、未来の教師・蒸留がそれぞれ独立の系統 |
| 六 方法論 | Metrics Matter surgical phase／relaxed boundary phase recognition／evaluation protocol Cholec80／reproducibility surgical phase | 4 | Metrics Matter、2026 の指標の総説、公式の評価のリポジトリなど |
| 七 否定的な結果・追試 | causal vs offline action segmentation／failed smoothing loss action segmentation／cannot reproduce surgical phase／online LSTR TAS poor | 7 | LSTR を行動分割に移したときの不適合、offline → online の segment の指標の低下、後処理による Acc の低下、TMRNet の再現の issue。損失だけの否定的な研究は 0 件 |

報告が書いた引用の追跡（L547–L555）: EgoSurgery-Phase から TeCNO・Trans-SVNet・NETE・GGMAE を逆に引き、後続の SurgMotion から EgoSurgery を使う基盤モデルを追った。TeCNO・TMRNet・Trans-SVNet の系を 2025 の HID-SSM の関連研究と Table I から確かめた。一般の行動分割では OnlineTAS から MS-TCN、ASFormer、LSTR、MAT、DiffAct などを逆に追った。一人称では ProTAS を起点に GTEA、EgoProceL、EgoPER と後続の一人称の手順の研究を追った。

### 12.3 A2f

**検索日:** すべて 2026-10-21。各検索で上位 8〜10 件を確認（L416）。検索は 18 回とサブエージェント 1 回（MiniROAD の本文と補遺、Rivoir ほかの付録の表）。

| # | 検索語（報告の記載） | 問い・方向 | 行 |
|---|---|---|---|
| 1 | EgoSurgery-Phase phase recognition open surgery egocentric | (9)、一 | A-01、A-06 |
| 2 | Randomness in Neural Network Training… Tooling | (10)、五 | A-86、A-90 |
| 3 | Analysing The Impact of Sequence Composition… intra-document causal masking | (9)、五 | A-82、A-83 |
| 4 | online temporal action segmentation OnlineTAS memory reset video boundary | (9)、四 | A-23 |
| 5 | out-of-body detection anonymization laparoscopic video OoBNet | (9)、二 | A-78、A-79、A-80、A-81 |
| 6 | EgoSurgery-Phase benchmark phase recognition results 2025 | (9)、一 | A-03、A-19 |
| 7 | SurgMotion arXiv 2602.05638 | (9)、一 | A-02 |
| 8 | online action detection robustness frame drop missing frames streaming video | (9)、四 | A-33 |
| 9 | Renard Variability and reproducibility… Scientific Reports 2020 | (10)、六 | A-92 |
| 10 | GRU-D… missing values time interval decay | (9)、五 | A-85 |
| 11 | Transformer-XL segment-level recurrence ablation state reuse | (9)、五 | A-84 |
| 12 | MS-TCN reproduce results different GPU variance… seeds | (10)、四 | A-26、A-29 |
| 13 | Pham Problems and Opportunities… Analysis of Variance | (10)、五 | A-88、A-93 |
| 14 | Bouthillier Accounting for Variance… | (10)、五・六 | A-89 |
| 15 | surgical phase recognition reproducibility reimplementation… Cholec80 | (10)、二 | A-74、A-77 |
| 16 | On Aliased Resizing and Surprising Subtleties in GAN Evaluation | (10)、五 | A-91 |
| 17 | Rivoir pitfalls batch normalization… Cholec80 | (9)・(10)、二 | A-75、A-19 |
| 18 | online procedural step recognition egocentric… Ego-Exo4D keystep | (9)、三 | A-30、A-32 |

方向ごとの記録の件数（L438–L440）: 問い (9) は方向一 4、二 6、三 2、四 4、五 4。方向六は専用の記録 0（A-75・A-26 の中で扱った）。方向七は独立の検索 0 回で、否定的な所見 3（A-75、A-25、A-82 の中）。問い (10) は方向一 0（#1・#6・#7 の範囲で該当なし）、二 3（A-75、A-74、A-77）、三 0（専用の検索は未実施）、四 1（A-29）、五 6（A-86、A-87、A-88、A-90、A-91、A-93）、六 2（A-89、A-92）。方向七は独立の検索 0 回で、中立的な所見 2（A-86、A-87）。

### 12.4 A3c

**検索日:** 2026-10-08。web_search 18 回、web_fetch 6 回、サブエージェント 1 回（L135）。

- 方向一: 3 回、確認 6 件（A-01・A-02、EgoSurgery-Tool・HTS、ORQA、EgoExOR）
- 方向二: 8 回、記録 R3〜R10（A-41、A-34、A-35・A-36、A-42、簡略の記録の A-39・A-43・A-40・A-37・A-46・A-45・A-44、A-50〜A-52、A-48、A-49）
- 方向三: 2 回、記録 R11・R12（7 件。A-65〜A-69、A-58、A-60）
- 方向四: 2 回、記録 R13 の VideoMAE・MME・online 化（5 件。R13 の行は A-14、A-22、A-19、A-74、A-15、A-53、A-55）
- 方向五: 1 回、記録 R14（2 件。R14 の行は A-70〜A-73）
- 方向六: 2 回、記録 4 件
- 方向七: 独立の検索 1 回と各記録からの抽出で 6 件（GGMAE の τ=0.25、SurgMotion の表での手術の基盤モデルの値、OmniRAS の凍結の条件での不一致、Can Gaze、鳥類の MAE、SelfSupSurg の多ラベルの条件）
- 種のうち実在を確認したもの（L143）: GGMAE、SurgMAE（引用で確認）、VideoMAE、VideoMAE V2、V-JEPA 2（引用で確認）、DINOv3（引用で確認）、SurgMotion、SurgVISTA、EndoViT、Endo-FM、GSViT、SurgeNetXL、LemonFM、SurgVLP、EndoMamba、GastroNet、SelfSupSurg、AVOS、EgoVLP。「Ego-Exo」は Ego-Exo4D（CVPR 2024、引用で確認）と判断した

### 12.5 A3g

**検索日:** 2026-10-05（日本時間）。件数は検索エンジンの総数ではなく、重複を除いて題名・要旨・本文または比較表まで確認し、判断の材料として保持した文献・モデルの論文の概数。一つの文献が複数の方向に属する（L312）。

| 方向 | 主な検索語（報告の記載） | 件数 | 結果（報告の記載） |
|---|---|---|---|
| 一 EgoSurgery・一人称の開放手術 | EgoSurgery Phase／GGMAE 2405.19644／EgoSurgery foundation model／SurgMotion EgoSurgery | 2〜3 | GGMAE と SurgMotion が中心。汚染の無い 5 分割の基盤モデルの比較は見つからない |
| 二 手術一般 | surgical foundation model／endoscopic video foundation model／self-supervised surgical video／MICCAI surgical foundation model／各種の名前 | 14 以上 | Endo-FM、EndoViT、SelfSupSurg、SurgMAE、GSViT、SurgeNetXL、SurgVISTA、LEMON、EndoMamba、SurgVLP、EndoSSL、GastroNet、SurgMotion など |
| 三 非手術の一人称 | EgoVLP／EgoVLPv2／Ego4D transfer／EPIC-KITCHENS transfer／egocentric pretraining surgery／Ego-Exo | 4 程度 | EgoVLP の系を確認。手術への直接の転移は見つからない。Ego-Exo は原典を一意に確認できず |
| 四 一般動画 | VideoMAE V2／V-JEPA 2／DINOv3 video transfer／online action recognition causal／object-aware video pretraining | 7 以上 | 一般の基盤モデルは多いが、EgoSurgery への揃った比較が無い |
| 五 機構一般 | gaze guided masking／motion guided masking／object guided masking／saliency masking MAE／domain adaptation self-supervised pretraining | 6 以上 | 視線・動き・物体は確認。手術の顕著性の統制された研究は見つからない |
| 六 評価・漏れ | self-supervised test set leakage／pretraining downstream test overlap／surgical pretraining leakage／各論文の split・test・exclude | 主要な例 3 | SurgVISTA が明確な除外の例。GGMAE・SurgMotion は重要な情報が不明 |
| 七 否定的な結果 | 各論文の ImageNet／random initialization／few shot／ablation／frozen／Table／negative／worse | 6 以上 | SelfSupSurg、EndoViT、SurgMAE／GGMAE、LEMON、SurgMotion の比較から複数の負の例 |

報告が書いた引用の追跡（L324）: SelfSupSurg から手術の領域の SSL と初期化、SurgeNetXL・SurgVISTA・SurgMotion の比較の表から Endo-FM、EndoViT、GSViT、GastroNet、EndoSSL などへ逆に引いた。データセットからの逆引きとして EgoSurgery、Cholec80、AutoLaparo、RAMIE を軸に比較の表を確かめた。

否定的な結果として保持したもの（報告の記載、L326）: SelfSupSurg（一般の ImageNet の SSL が教師ありの ImageNet より最大 −1.9 phase-F1、−11.2 tool-mAP。A-34）／EndoViT（全データの工程認識で ImageNet の ViT に −0.19 accuracy。A-37）／GGMAE の ablation（τ=0.25 で Jaccard 27.2、最適の 0.50 の 33.9 から −6.7。A-01）／SurgMAE（EgoSurgery で VideoMAE・VideoMAE V2 より低い。A-01、A-38）／LEMON（凍結した転移で ViT・生成の目的が ConvNeXt・識別の目的に大きく負ける条件がある。A-42）／SurgMotion のベンチマーク（EndoViT、GSViT、SurgeNetXL などが一人称の開放手術の EgoSurgery で DINOv3 を大きく下回る。A-02）。値は A-02 の Table 3 の F1 で、EndoViT・GSViT・SurgeNetXL が 7.33〜9.29、DINOv3 が 32.43・36.34（L326 の記載ではなく、本書の作成者が A-02 の値を添えた）。

### 12.7 A2s

**検索日:** すべて 2026-10-21（L571）。件数の欄は「関連する資料の数／その問いを直接測った資料の数」で、同じ論文が複数の方向に当たるため方向の間で排他ではない（L571）。「件数」は検索エンジンの生のヒット数ではなく、本文・要旨・公式ページのいずれかまで確認して関連すると判定した一意の資料の数（L5）。

欠けのある系列（問い (9)。L575–L585）:

| 方向 | 主な検索語（報告の記載） | 確認件数 | 結果（報告の記載） | 行 |
|---|---|---|---|---|
| 一 同じデータ・EgoSurgery | EgoSurgery missing frames temporal state reset／EgoSurgery discontinuous clips causal／EgoSurgery privacy frame removal phase | 4／0 | Phase／Tool／HTS／SurgMotion を確認。持ち越し・初期化の ablation は無し。Phase の原論文は 25 fps→0.5 fps と個人情報のフレームの除去を明記 | A-01、A-03、A-04、A-02 |
| 二 手術一般 | surgical phase recognition out-of-body temporal continuity／online surgical workflow OOB temporal convolution／privacy removed frames surgical workflow | 8／2 | Bayat の OOB と時間モデル、StableSPR の状態の誤りの連鎖が特に近い | A-94、A-95 |
| 三 一人称・非手術 | egocentric procedural recognition missing clips discontinuity／egocentric action segmentation sparse frames | 2／0 | Ego-Exo4D、Ego-METAS 系を確認。未知の長さの欠けの初期化・持ち越しの直接の比較は無し | A-30、A-32 |
| 四 一般映像 | temporal action detection missing frames robustness／dropped frames online action detection／temporal corruption action localization | 6／1 | Zeng ほか CVPR 2024 が直接的。少数の corruption でも位置の推定が大きく悪化 | A-96 |
| 五 機構一般 | irregularly sampled time series elapsed time RNN／continuous time transformer irregular timestamps／state space model irregular sampling S5／Mamba physical delta irregular time／Neural CDE online | 17／13 | mTAN、T-LSTM、Time2Vec、SeFT、Latent ODE、GRU-ODE-Bayes、NCDE、Raindrop、ContiFormer、S5、TIDES、MASCIT など | A-97〜A-108 |
| 六 評価・統計 | action segmentation edit score missing frames／segment F1 gap concatenated clips／surgical phase temporal fragmentation metric／remaining time missing intervals | 5／2 | StableSPR が Edit の盲点、Ego-METAS がフレームレートと Edit の相互作用を扱う。欠けをつないだ評価と区間別の評価は未発見 | A-95、A-32 |
| 七 否定的な結果 | state carry reset no improvement temporal model／irregular time Mamba failure extrapolation／frame drop worsens action detection／attention mask discontinuity no improvement | 6／4 | TIDES: Mamba の分布外の Δ での失敗と S5 の LTI の限界、MASCIT: full selectivity が不利、Zeng: corruption への脆弱さ、StableSPR: Edit と安定性の不一致 | A-107、A-108、A-96、A-95 |

方向五では手術・医療の語を入れない検索を独立に行い、S5／TIDES、mTAN、Latent ODE、GRU-ODE-Bayes、Neural CDE、Raindrop、ContiFormer、SeFT などを拾った（L585）。

計算環境差（問い (10)。L589–L599）:

| 方向 | 主な検索語（報告の記載） | 確認件数 | 結果（報告の記載） | 行 |
|---|---|---|---|---|
| 一 EgoSurgery | EgoSurgery reproducibility seed GPU／EgoSurgery same seed different GPU | 4／0 | データセット・モデルの論文はあるが、計算機をまたいで対応づけた再実行は未発見 | — |
| 二 手術一般 | surgical phase recognition reproducibility seed GPU／Cholec80 hardware reproducibility／EndoVis rerun GPU difference／SurgVU reproducibility container | 5／0 | seed・分割・再現の周辺の文献はあるが、GPU／CUDA の要因を直接測るものは無し。SurgVU は container による標準化 | A-74、A-77、A-92 |
| 三 一人称・非手術 | egocentric video recognition hardware reproducibility／procedural action segmentation GPU seed variance | 0／0 | 問いに答える査読研究を確認できず | — |
| 四 一般映像 | video recognition decoder reproducibility PyAV decord／action segmentation JPEG resize reproducibility／video model different GPU same seed | 4／0 | decoder・圧縮・前処理の周辺の研究はあるが、行動分割で計算機 × seed を直接比べるものは無し | A-91 |
| 五 機構一般 | deep learning hardware nondeterminism GPU seed variance／floating point non-associativity reproducibility／framework version reproducibility deep learning／bitwise cross GPU training | 13／8 | Zhuang、Summers、Pham、Bouthillier、Chen、Coakley、Shahriari、Shanmugavelu、RepDL など | A-86、A-87、A-88、A-89、A-109、A-110、A-111、A-114、A-115 |
| 六 方法論 | variance decomposition deep learning seed hardware／reproducibility reporting machine learning multiple seeds hardware／deterministic training overhead | 10／7 | Chen のソフトウェア／ハードウェアの分解、DEVIATE、Coakley の多環境の設計、Gundersen の総説など | A-109、A-112、A-110、A-93 |
| 七 否定的な結果 | deterministic training does not reduce variance／same seed same GPU different result／different GPU minimal accuracy difference／reproducibility one bit perturbation | 7／5 | Zhuang: 集計の指標の差が小さくてもモデルの不一致が残る、Summers: 微小な摂動が異なる解を生む、Ravi: 同じ seed／GPU でも構造の差、Chen: ハードウェアの成分が残る | A-86、A-87、A-113、A-109 |

ここでも手術の語を含めない探索を独立に行い、ハードウェア・ソフトウェア・乱数の要因の分離に関する証拠がソフトウェア工学・一般の深層学習の側に集中していることが分かったと書く（L599）。

### 12.6 旧地図 A（v1）の A.2

検索日の記録は無い。検索語（旧地図の記載）: 同じ領域 — Trans-SVNet／LoViT／EndoNet／Dissecting SSL for surgical CV／EgoSurgery-Phase GGMAE／SurgMAE／surgical video pretraining／AutoLaparo／Cataract-101／surgical foundation video-language。一般の機構 — temporal action segmentation Breakfast 50Salads GTEA causal online／online action detection THUMOS TVSeries LSTR／ASFormer／MS-TCN。隣接の領域 — egocentric action recognition EPIC-Kitchens Ego4D pretraining EgoVLP LaViLa／Ego-Exo／EPIC-Kitchens／EGTEA gaze。旧地図の探索は当時の設計（2026-09-16）の前で、七方向の探索ではない。
