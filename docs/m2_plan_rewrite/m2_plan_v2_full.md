# M2 研究計画
> M2 期間の研究計画を集約したマスタードキュメント。**術具検出 × 工程認識の 2 タスク結合**を中核に、**分析ファースト**（既存結合を複数試す → 単一タスクとの Δ を実測 → 差の要因を分析 → 観察から結合仮説を立てる）で**タスク結合の原理提案**を目指す。STEP 0–D の検証ロードマップと 7 分類のサーベイ計画を含む。前提・データ仕様・MTG 議事録は `研究方針_2026/05/14` を参照のこと。**本ページへの変更はすべて §0 「変更履歴」に逐次記録される**。
**〔2026-06-19 改訂版〕** 本計画は「タスク結合の原理提案 × 分析ファースト」フレーム。正本は §13（実行手順書）・§2（研究の問いと仮説プール）・§2.5(b)・§7。検出ベースラインは実測完了済み（**Relation-DETR mAP 0.730**、3-seed σ0.004、AP_rare 0.758）。手-術具関係（mask 依存）と Exo 多視点は **Phase-2（将来拡張）** に延期。旧フレーム版（〜2026-06-14）は凍結アーカイブ（`384ee4d4-7777-818c-9363-cea8a1170603`）を参照。
---
## 変更履歴(逐次更新) {toggle="true"}
	本ページの編集履歴を新しい順に記載する。**今後の変更はすべて、本セクションの冒頭に追記する**。記録項目は「日付 / 変更のサマリ・該当 § / 変更の要旨」の 3 点を原則とする。**〔2026-06-19 改訂〕本ページはタスク結合フレームへ全面改訂した。改訂前（旧フレーム期、〜2026-06-14）の詳細な編集履歴は凍結アーカイブ（M2研究計画_archive_2026-06-14、ID `384ee4d4-7777-818c-9363-cea8a1170603`）に逐語保存されており、本セクションは以降それを要約に縮約して保持する。**
	### 2026/06/19
	**§1〜§16 の枠組み章を「タスク結合の原理提案 × 分析ファースト」フレームへ全面改訂（外科的再構成・知識章は保全）**
	コア主張を「最良の組み合わせ発見」から **検出 × 工程の 2 タスク結合の原理提案**へ確定し、研究順序を **分析ファースト（STEP 0→A→B→C→D）** に統一した。主な変更：
	- **(a) §2 を「研究の問いと仮説プール」へ全面改稿**：中央 RQ ＋ 結合効果予測①②（旧フレームの主仮説を内包）＋ 仮説プール H-C / H-A / H-H（STEP C の観察で選ぶ/作り直す）＋ 手-術具関係・Exo を Phase-2 へ延期。
	- **(b) §1/§4/§5/§6/§8.1/§9/§12/§13 を新フレームで刷新**：§12/§13 を STEP 0–D 主構造に再編し、検出単独 S0-frozen・工程単独 S4 のみ名前を残して STEP に対応づけ、既存結合の比較群（4 層 6 手法）と「比較の三角形」を導入。
	- **(c) 知識章（§8.-1/§8.0/§10/§11/§14/§15/§16）は保全**：事実・数値・per-class AP・eval recipe 規則・DDP 規則・コードパス・サーベイ子ページ（§11 の 22 本）を保持し、旧フレームの概念参照（旧仮説ラベル・旧ステップ番号・旧「改善」表現）のみ新フレーム語へ翻訳。
	- **(d) 検出ベースラインの実態を反映**：DETR 系 10 モデルを実測完了し **Relation-DETR が mAP 0.730（3-seed 平均 0.727・σ0.004・AP_rare 0.758）で 1 位**であることを §4.2・§12・§13・§16 に反映（README 旧値は無効・更新済み）。
	- **(e) 冒頭バナー「研究方針の現在地」を縮約**：本文が新フレーム化したため短いポインタへ縮約。正本は §13（実行手順書）。旧フレーム版は凍結アーカイブ（384ee4d4）を参照。
	### 改訂前（旧フレーム期、2026/05/18〜2026/06/14）の要約 〔詳細は凍結アーカイブ 384ee4d4 を参照〕
	以下は要約であり、各変更の詳細（該当 § ・要旨）は凍結アーカイブの変更履歴に逐語保存されている。
	- **2026/06/14**：「研究方針の現在地」セクションを冒頭に新設し、タスク結合提案へのピボット（§13）と分析ファースト順序（2026-06-14 確定）を本体に反映。
	- **2026/06/01〜06/02**：§16「エポック数・再現性の検証ログ」を全面リライト、§10〜§12 の内部小見出し番号の不整合を修正、工程ベースライン（S4）設計を確定。
	- **2026/05/29**：エポック数の論文根拠・VFNet 再実験数値の妥当性検証を §16 として新設、AP_common 定義歪みの発見、バッチサイズ・エポック数・HPO 方針を確定。
	- **2026/05/23〜05/25**：§8.0 サーバー割り当て運用原則・DDP 2 GPU 実行許容条件を新設し実装を DDP 対応に改訂、実行サーバー名（bengio）の記録機構を導入。
	- **2026/05/24**：§15「Lessons Learned & 整合性検証規則」を新設（split 取り違え・test_cfg 不一致・catastrophic forgetting・class weight 崩壊の知見）、§8.-1 eval recipe 整合性規則を整備、術具クラス表の数値訂正（Forceps 1.22% → 12.21%）。
	- **2026/05/20〜05/21**：全 22 サーベイを反映、§13 実験実行手順書を新設、§0.1 データ可用性の 2 フェーズ構成（Phase-0 bbox／Phase-1 mask）を導入、§2.6 方法論的貢献 D-A/D-B を新設。
	- **2026/05/18〜05/19**：ページ名変更・変更履歴セクション新設、サーベイ結果セクション（§11）の新設。
---
## 0. 本計画の要点 {toggle="true"}
	- **工程(Phase)と動作(Action)は本来分けて扱うべきである**が、現段階では**動作ラベルは追加せず**、既存の EgoSurgery 系アノテーション(術具 bbox/mask、手 bbox/mask、工程ラベル)のみを用いる。
	- 当面の構築対象は「**術具・手・工程**の同時理解システム」に絞る。
	- 動作ラベル追加の可否は、現状の Phase ラベルが術具検出にどれだけ寄与し、また工程認識の到達精度がどの程度かを確認した上で**事後判断**する。
	- **Exo(俯瞰多視点)映像にはアノテーションを行わない**。**学習時のみの補助情報**として、自己教師あり学習・弱教師あり学習・蒸留・時間整合学習の素材に限定する。推論時は **Ego 単独で動作する**ことを必須要件とする。
	### 0.1 データ可用性の前提と 2 フェーズ構成〔2026/05/21 追加〕
	本計画は、現時点で利用可能なアノテーションと未準備のアノテーションを明確に区別し、研究を **2 フェーズ** で進める。
	- **現時点で利用可能**：術具 bbox（15 クラス）、手 bbox（4 クラス：own/other × L/R）、工程ラベル（9 クラス、0.5 fps）、Exo 多視点 raw 映像（無アノテーション）。
	- **現時点で未準備（M2 期間内に入手見込み、数ヶ月後、〔2026/05/21 更新〕）**：術具・手の **mask（instance segmentation）アノテーション**、および **hand-tool 関係アノテーション**（および mask から自動派生する関係疑似ラベル）。これらは現時点では未準備だが、M2 期間内（数ヶ月後）に準備できる見込みである。
	- **Phase-0（bbox フェーズ、現時点で全面実行可能）**：bbox 検出 + Phase ラベルのみで、**結合効果予測①②**（工程文脈→検出・object-centric 表現→工程）と方法論的貢献 **D-A・D-B** を一次検証する。object token は bbox 由来の特徴（ROI Align + bbox 位置 + クラス埋め込み）で構成し、mask shape 属性を使わずに結合効果②を成立させる。これが本計画の **主経路（検出 × 工程の 2 タスク結合）** である。
	- **Phase-1（mask フェーズ、mask / hand-tool アノテーション入手で起動する条件付き）**：mask 入手後に instance segmentation（旧 S1）と関係モジュール（Phase-2／mask 依存）を追加起動する。mask 由来の属性・関係疑似ラベルで object token を強化し、手-術具関係の結合を検証する。**この mask 依存の関係結合と Exo 多視点 SSL は当面のコア外＝将来拡張（本計画では「Phase-2」と呼ぶ）に位置づける**。mask は M2 期間内（数ヶ月後）に入手できる見込みであり、入手時点で Phase-1 を Phase-0 の上に統合する。万が一 mask が M2 期間内に入手できない場合でも、Phase-0 だけで 結合効果①②・D-A・D-B により研究と論文が成立するよう設計する。
	- この 2 フェーズ構成は §2.6 のフォールバック思想（Δ 非有意時も D-A・D-B で論文成立）と同じ設計原理であり、**「不確実な前提に依存する部分（mask）を条件分岐に隔離し、確実な前提（bbox・Phase）の上に主経路を組む」** ことでデータ準備リスクを構造的にヘッジする。
---
## 1. 研究のゴール {toggle="true"}
	### 1.1 最終ゴール(長期)
	開放手術の一人称視点(Ego)映像から、**術具・手・工程・動作・関係性**を AI が同時に認識するシステムの構築。これは 4 タスク（検出・手・工程・関係、および将来の動作）を統合する Ego 認識という長期ビジョンであり、本計画はその第一歩を担う。
	### 1.2 短期ゴール(現フェーズ、本方針のスコープ)
	**本計画のコアは「最良の組み合わせ発見」ではなく、術具検出 × 工程認識の 2 タスク結合の原理提案である**（指導コメント②への応答、§13）。既存の結合手法を複数実装して単一タスクとの精度差(Δ)を実測し、その差が**なぜ生じる/生じないか**を分析してから結合仮説を立てる **分析ファースト** の順序を採る（STEP A–D、§2・§12・§13）。タスクは §0.1 の 2 フェーズに対応させて明示する〔2026/05/21 再編：mask / hand-tool アノテーション不在の制約を反映。2026-06-19 タスク結合フレームへ改訂〕。
	- **Phase-0（bbox フェーズ、現時点で全面実行可能、本計画の必達分）**
		1. 術具の検出・分類（15 クラス、**bbox**）
		2. 手の検出・分類（4 クラス：own/other × left/right、**bbox**）。**手検出は検出タスク内の追加対象**であり、独立した第 3 の結合軸にはしない。
		3. 手術工程（9 クラス、フレーム単位、long-range time series）
		4. 上記のうち **検出 × 工程の 2 タスク結合**を主軸とし、**結合効果予測①**（工程文脈→検出、Δ mAP）・**②**（object-centric 表現→工程、Δ Phase F1）を検証する。bbox 由来の object token で結合効果②を成立させる。
	- **Phase-1（mask フェーズ、mask / hand-tool アノテーション入手で起動する条件付き分）**
		1. 術具・手の **mask**（instance segmentation、mask アノテーション入手で起動）
		2. 手と術具の接触・把持関係（hand-tool 関係アノテーションまたは mask 重なりからの自動生成）。この mask 依存の関係結合は **当面のコア外＝将来拡張（本計画では「Phase-2」と呼ぶ）** とする。
	- **フェーズ間の依存関係**：Phase-1 は Phase-0 の上に積み上げる増分であり、Phase-0 単独でも研究として成立する（§2.6 D-A/D-B と結合効果①②）。mask 入手時期に応じて Phase-1 を起動し、未入手のまま M2 を終えるシナリオでも論文が成立する。
	### 1.3 短期ゴールに含めないもの
	- 動作(Action / Primitive / Gesture)レベルの認識:今フェーズではスコープ外。
	- **手-術具関係（mask 依存）と Exo 多視点 SSL：当面のコア外＝将来拡張（Phase-2）**。2 タスク結合の確立後に検討する（§0.1 Phase-1 と整合）。**捨てるのではなく延期する**。
	- Exo 映像へのアノテーション付与:行わない。
	- 推論時の Exo 利用:行わない(Ego only inference)。
---
## 2. 研究の問いと仮説プール {toggle="true"}
	本研究は単に「複数のタスクを同時に解く」ことや「最良の組み合わせを発見する」ことを目的とするのではなく、**タスク結合（task coupling）がなぜ・どう効くのかの原理提案**を出発点とする。これまで術具 bbox アノテーションのみを用いた術具検出に取り組んできた経緯を踏まえ、当面は **術具検出 × 工程認識の 2 タスク結合**にスコープを絞る。
	### 2.0 中央の問いと方法論（分析ファースト）
	- **中央の問い (RQ)**：**異粒度（検出＝疎な instance × 工程＝時間区間）のタスク結合は、単一タスクに対し精度をどう・なぜ変えるか。その観察から、いつ・どう繋ぐべきかの結合原理を導けるか。**
	- **方法論（分析ファースト）**：新しい結合手法を先に発想するのではなく、**既存のタスク結合手法を複数実装する → 単一タスクとの精度差(Δ)を実測する → 差が生じる/生じない要因を分析する → その観察から結合仮説を立てる**順序を採用する（STEP A–D、§12・§13）。
	- **なぜ分析ファーストが強いか**：(1) 仮説の出所が「観察」になり、査読で評価される motivation が強い、(2) 異粒度結合の **negative transfer** を実測して初めて「いつ繋ぐかを動的に制御する」必要性が示せる、(3) 最悪でも既存結合の異粒度・open surgery 挙動の体系的分析が貢献になる（§2.6 二段構えと整合）。新結合に「先に 1 つ賭ける」方法論上の弱さを構造的に解消する転換である。
	### 2.1 結合効果予測①：工程文脈→検出（旧フレームの主仮説を内包・Δ mAP で測る）
	> **工程(Phase)文脈を検出器にフィードバックすることで、形状類似・遮蔽・クラス不均衡が強い open surgery の術具検出を改善できる**。すなわち、bbox 単独学習（S0-frozen）を上回る術具検出精度（Δ mAP > 0）が得られる、という結合効果の予測である。STEP B で既存結合を実装して実測し、STEP C で要因を分析する検証対象。
	根拠:
	- 開放手術では、ある工程で出現する術具は強く偏る(例:Dissection では剥離系、Closure では縫合系)。Phase 文脈は **事前分布** として検出器の予測を絞り込み、特に**クラス不均衡**の極端な稀少クラス(Skewer 0.7%、Syringe 1.17%)で誤分類を抑えられる可能性が高い。
	- **形状類似**の術具(例:Forceps / Tweezers / Needle Holders)は静的な視覚特徴だけでは区別が難しいが、工程文脈を補えば識別可能性が高まる。なお Forceps は 12.21% でトップ 3 に属する頻出クラスだが、頻出であっても形状類似による混同は工程文脈なしには解消困難である。
	- **遮蔽**が頻発する開放手術では、見た目の特徴だけで検出を確定するのは脆弱だが、工程文脈は遮蔽下でも候補絞り込みに寄与する。
	- これまでの bbox 単独学習で残っていた「稀少クラスの取りこぼし」「形状類似ペアの混同」「遮蔽による検出失敗」を直接ターゲットできる。
	### 2.2 結合効果予測②：object-centric 表現→工程（旧フレームの主仮説を内包・Δ Phase F1 で測る）
	> **open surgery の工程認識には、画像全体特徴(global image feature)よりも、手・術具・それらの相互作用に基づく object-centric temporal representation が有効である**。すなわち、物体中心の時系列表現を Phase head の主入力とすることで、global feature 単独の工程認識モデル（S4）を上回る精度（Δ Phase F1 > 0）が得られる、という結合効果の予測である。
	根拠:
	- Phase は本質的に「誰が何の術具で何をしているか」の集約であるため、画像全体の抽象特徴より、**術具・手の構成・相互作用の方が判定根拠として直接的**である。
	- Dissection / Closure は全体の約 8 割を占める長尺工程であり、工程境界の検出は画像特徴の差分だけでは弱い。**術具集合と手-術具相互作用の遷移**は明確な境界信号となる。
	- 物体中心表現は global feature と相補的であり、global feature が捉える「術野全体の様相」と組み合わせて使うことで一段強くなると期待できる(本研究では物体中心表現を主、global feature を副とする)。
	### 2.3 仮説プール（STEP C の観察で選ぶ/作り直す）
	分析ファーストへの転換に伴い、§13 の新結合仮説は「先に 1 つ賭けるコア仮説」から **STEP C の観察で選ぶ/作り直す仮説プール**に格下げする（ラベルは維持）。各仮説は STEP B の比較群（共有エンコーダ MTL〔必須・最初〕／片方向 pipeline〔必須〕／PAD-Net・MTI-Net 予測蒸留〔主要〕／MT4MTL-KD・SSG-Com ドメイン SOTA〔主要〕／Cross-Task Consistency〔余力〕／Cross-stitch・MTAN〔参考〕の 4 層）上に位置づけ、STEP D で「観察への解」として比較群に戻して同一土台で検証する。
	- **H-C（不確実性駆動の双方向結合）**：タスク自信（予測エントロピー）に応じて検出⇄工程の注入を動的に gating する双方向結合。negative transfer を「いつ繋ぐか」で制御する最大の新規性候補。§4.6 の予測相互作用（entropy gating / cross-attention / stop-gradient）に対応。
	- **H-A（トリプレット畳み込み）**：〈術具・手・工程〉のトリプレットを畳み込み的に結合する統一の土台。共有表現の設計を担う候補。
	- **H-H（ラベル効率結合）**：結合がラベル効率（少ラベルでの到達精度）をどう変えるかを示し、価値の出し方を補強する候補。
	- 勾配系（PCGrad / CAGrad / FAMO）は**併用アドオン**であり主軸に置かない（L4 最適化バランシングとして §5・§8.1 に整理）。
	### 2.4 当面のコア外＝将来拡張（Phase-2）：手-術具関係・Exo 多視点
	2 タスク結合の確立後に検討する将来拡張として、以下を **Phase-2** に位置づける（**捨てるのではなく延期**、§0.1 Phase-1 と整合）。
	- **手-術具関係（mask 依存）**：手-術具の関係（grasp / near-contact / handover / two-hand manipulation）は単なる物体共起を超える意味的中間表現を与え、結合効果①②を増幅しうる。ただし mask アノテーション（および mask から自動派生する関係疑似ラベル）を前提とするため、mask 入手後に起動する条件付き拡張とする。mask 不在時は bbox-IoU からの粗い near-contact 疑似ラベルでパイプライン動作確認のみ可能（grasp と near-contact の分離は bbox では原理的に困難）。
	- **Exo 多視点 view-consistent SSL**：無アノテーションの 25 fps Exo 多視点映像を view-consistent SSL（view-consistent contrastive / cross-view masked prediction / 同時刻 Ego-Exo 整合）に使い、低 fps(0.5 fps) Ego では学習しにくい動作・時間表現を獲得して Ego に蒸留転写する。**推論時は Ego 単独動作**の制約と矛盾しない（Exo は訓練時のみのリソース）。
	### 2.5 成功条件（比較の三角形）
	成功条件は「**タスク結合が単一タスク基準を上回るか（Δ > 0）**」に集約され、**比較の三角形**（同一土台＝凍結 backbone・初期化・解像度・検出ヘッド・各損失・スケジュール・データ/split・fps・eval recipe・seed を共有し、変えるのはタスク/結合の有無だけ）の上で測る。
	- **(a) 検出単独の分母 = S0-frozen**（凍結 backbone ＋ 検出ヘッド）。Δ_detection の分母①。
	- **(b) 工程単独の分母 = S4**（凍結 backbone ＋ 時系列ヘッド・TeCNO コア）。Δ_phase の分母②。設計確定済（§2.5(b)・§4.2）。
	- 結合手法（STEP B）が (a)(b) を**両方上回る**こと、すなわち Δ mAP > 0 かつ Δ Phase F1 > 0 を主マイルストーンとする。これらは Phase-0（bbox）で全面実行可能である。
	- **(c) Exo SSL 無し対照**は Phase-2 へ延期（Exo 結合の Δ 増幅は将来拡張で検証）。
	- 単独タスクの絶対精度は副次指標とし、Δ（タスク結合の効果幅）を主指標とする(§7 参照)。なお検出単独の絶対基準として検出ベースラインは実測完了済み（**Relation-DETR mAP 0.730**／3-seed 平均 0.727・σ0.004・AP_rare 0.758、§12・§13）。
	### 2.6 方法論的貢献としての設計仮説（D-A / D-B）〔§12 サーベイ反映：C3/C4/D2/G4 の批判的レビューで新設〕
	結合効果予測①②（および Phase-2 の関係・Exo）はいずれも「〜が改善する」という **現象仮説**であり、検証には Δ を統計的に有意に示す必要がある。しかし EgoSurgery は 21 動画・8 術者・1 施設と小規模であり（§12.24 G4）、Δ の variance が大きく「Δ が 1σ 以内なら改善と主張しない」基準（§10.1）に照らすと、現象仮説のみに依存すると研究が成立しないリスクが構造的に存在する。そこで、Δ の有意性に依存しない **方法論的貢献（アーキテクチャ貢献・ベンチマーク貢献）** をタスク結合の検証と並ぶ中核として明文化する。
	- **設計仮説 D-A（object-centric token × block-diagonal SSM アーキテクチャ）**：検出器由来の object token 列を、slot ごとに独立に時間発展させる block-diagonal Mamba（SlotSSMs 風）で処理する設計は、open surgery Ego の長距離工程認識に有効なアーキテクチャである。§12.15 C3・§12.17 D2・§12.23 C4 が一致して「検出器出力 token 列を後段 SSM/Mamba に流す分離型設計は surgical も general video も SlotSSMs 以外に未報告」と確認しており、結合効果（タスク結合の効果）の主張よりも defensible な novelty となる。検証は §8.1 A7 が担う。
	- **設計仮説 D-B（EgoSurgery-Phase 初の長距離時系列ベンチマーク）**：Surgformer / LoViT / SR-Mamba / SKiT / MuST / HID-SSM は EgoSurgery-Phase で未評価であり（§12.17 D2）、これらの初ベンチマーク自体が publishable な貢献となる。
	- **フォールバックの位置づけ**：仮に結合効果①②の Δ が有意に出なくても、D-A（初の object-token×SSM surgical アーキテクチャ）と D-B（初の EgoSurgery-Phase 長距離ベンチマーク）によって論文が成立する二段構えとする。これにより、タスク結合の効果を主張しつつも、小規模データで Δ が有意差に達しないシナリオに対するリスクヘッジを確保する。
---
## 3. データ運用方針 {toggle="true"}
	### 3.1 Ego 映像(EgoSurgery 系)
	- 仕様は `研究方針_2026/05/14` の表に準拠(Train 10 / Val 2 / Test 3、0.5 fps)。
	- **現時点で利用可能な学習信号（Phase-0 主経路）**：
		- 術具 **bbox**（`EgoSurgery-Tool`、15 クラス）
		- 手 **bbox**（`EgoSurgery-Tool`、4 クラス：own/other × L/R）
		- 工程ラベル 9 クラス（`EgoSurgery-Phase`）
	- **mask / hand-tool アノテーションの状況〔2026/05/21 晠明記〕**：術具・手の **mask（instance segmentation）** および **Hand-Tool セグメンテーションから派生する手-術具関係** は、現時点で未準備であり、入手時期も不確定である。これらは **§0.1 Phase-1 で起動する条件付き学習信号** として扱い、mask 入手を待って instance segmentation（旧 S1）と関係モジュール（Phase-2＝将来拡張）に供給する。Phase-0 の主経路は mask を一切要求しない。
	- mask 入手時期の見込みが立ち次第、本節に実際の入手源（公開 EgoSurgery-HTS / 自施設アノテーション など）と見込み時期を追記する。
	### 3.2 Exo 映像(俯瞰多視点 Raw データ)
	- 5 視点、25 fps、640×540、画角は術野近傍のみ、アノテーションなし。
	- **本研究では一切アノテーションを行わない。**
	- 利用方法は以下の **補助タスク** に限定する。
		1. **自己教師あり事前学習**:VideoMAE 系の masked video modeling、playback speed prediction、temporal order prediction。
		2. **Ego–Exo 時間同期 contrastive learning**:同時刻の Ego フレームと Exo クリップを正例ペアとする。
		3. **弱教師あり学習(ラベル転写)**:Ego の Phase ラベルを同時刻の Exo に転写し、Exo 側にも Phase head を持たせる(Exo の Phase head は **学習時のみ** 使用)。
		4. **teacher–student 蒸留**:Exo 側で学習した時間表現を Ego 側に転写し、低 fps Ego の時間表現を強化する。
		5. **View dropout / visibility-aware fusion** による多視点冗長性の取り込み(Ego 表現の頑健性向上)。
	- 推論時には **Exo 経路を一切使わない**(該当パラメータは無効化または除去)。
	### 3.3 クラス不均衡対応〔§12 サーベイ反映：F1 で更新、2026/05/21 に temporal-consistent copy-paste を追加・mask 依存項を Phase-1 条件付きに明記〕
	クラス不均衡対策は、Phase-0（bbox）で完結する手法と、mask を要するため Phase-1 で起動する手法に分けて整理する。
	- 術具:最大 Tweezers 20.2% / 最小 Skewer 0.7%(約 30 倍差)。Forceps は 12.21% でトップ 3 に位置する頻出クラスであり、稀少クラスには該当しない〔2026/05/24 訂正：旧値 1.22% → 正値 12.21%〕。
		- **即時採用（Phase-0、bbox だけで実行可）**（F1 サーベイ）:post-hoc Logit Adjustment（全分類ヘッド、実装 1 行・コスト無し）、Seesaw Loss（p=0.8, q=2.0、検出器分類ヘッド）、Repeat Factor Sampling（t=0.001）、Decoupled cRT、bbox-level Copy-Paste（Skewer/Syringe を bbox crop として貼り付け、mask 不要の簡易版）。
		- **提案手法：temporal-consistent copy-paste（mask 入手で完全版起動、§0.1 Phase-1）**（2026/05/21 追加）。F1 サーベイは「0.5 fps 低 fps 動画での Copy-Paste/Mixup の時系列一貫性」が未開拓のギャップであると指摘した。naive な Simple Copy-Paste をフレーム独立に適用すると、貼り付けた稀少術具インスタンスがフレーム間で出現・消失を繰り返し、object token 列・時系列 Phase head（§4.5）の時間表現を汚染する。本研究では、稀少クラスのインスタンスを **同一クリップ内の連続フレームにわたって時間的に整合した位置・スケールで貼り付ける**（軌跡を線形補間し、隣接フレームで mask が連続するよう配置する）temporal-consistent copy-paste を提案手法とする。**mask を使う完全版は Phase-1 で起動する**が、Phase-0 でも bbox crop を用いた簡易版（軌跡補間は bbox 中心で行う）を先行実装できる。これにより S4 以降の時系列タスクと矛盾しない長尾拡張が可能となり、§8.2 の長尾損失 ablation の独立 contribution（下記）と接続する。
		- **検証推奨**（STEP B・§8.2 長尾 ablation）:EQLv2 vs Seesaw vs Logit Adjustment の直接比較。これらの長尾損失・サンプリング・拡張の系統的比較は、F1 サーベイで「手術・Ego 映像での標準長尾損失の系統的ベンチマークが不在」と確認されたため、**それ自体を独立した contribution**（手術 Ego マルチタスク設定での初の長尾手法ベンチマーク）として §8.2 に位置づける。長尾損失・サンプリングの比較は bbox だけで実行できるため Phase-0 に属する。
		- **採用見送り**:Focal Loss 単独（頻度を直接扱わず弱い）、naive Class-Balanced Sampling 単独（backbone 表現を劣化）、DINOv2 の heavy full fine-tuning（LIFT が tail-class 悪化を示す—LoRA/Adapter 必須）、CutMix を形状類似ペアに直接適用（混同悪化、Remix を検討）、フレーム独立な naive Copy-Paste（上記 temporal-consistent 版で置換）。
	- 工程:Dissection 44.1% + Closure 34.3% で約 8 割。
		- Balanced Softmax（TeCNO/SR-Mamba の工程ヘッド）、temporal smoothing による境界正則化、LoViT 風 Asymmetric Gaussian heatmap の工程遷移 prior。
		- **class weights の実装上の注意〔2026/05/24 追加、§14 と整合〕**：§14 で S3 の Phase head に class weights を不適切に与えた結果、val accuracy が 0.5% に崩壊した実例がある。逆頻度ベースの class weight は、極端な値（Dissection と稀少工程の頻度比が大きい）が学習を不安定化させうる。Phase ヘッドの class weight はデフォルト無効とし、有効化する場合も weight の最大/最小比を上限（例 10 倍）でクリップする。label smoothing（0.1）は安定化のため常に併用する。Balanced Softmax を使う場合も同様に極端な補正を避ける。
---
## 4. アーキテクチャ設計 {toggle="true"}
	### 4.1 設計思想:タスク結合の機構を中核に据える
	本アーキテクチャの中核は、§2 の **結合効果①②**（工程⇄検出の双方向結合）を実現する **双方向情報フロー** である。手-術具関係（増幅）と Exo 多視点（上限引き上げ）は **Phase-2 経路として残置**する。すなわち:
	- **Detection → Phase（結合効果②の実現経路）**:術具・手の object token を集約した**物体中心の時系列表現(object-centric temporal representation)**を Phase head の主入力とする。画像 global feature 単独ではなく、object-centric な構成・相互作用こそが工程の判定根拠であるという立場を取る。
	- **Phase → Detection（結合効果①の実現経路）**:Phase 予測 / Phase embedding を detection head に戻し、検出ロジットおよび object query を refine する。工程文脈を事前分布として用い、bbox 単独学習で取り切れなかった**形状類似・遮蔽・クラス不均衡**の難ケースを救う。
	- **Relation as amplifier（Phase-2／関係結合の経路、mask 入手で起動）**:手-術具の関係モジュールが両者の間に挟まり、単なる検出共起ではなく **意味的構成** を Phase head へ伝達する。
	- **Exo SSL as upper-bound lifter（Phase-2／Exo 経路、将来拡張）**:Exo 多視点の view-consistent SSL によって動作・時間表現を獲得し、teacher–student 蒸留と Phase ラベル転写を経由して Ego モデルへ注入する。推論時は Ego 単独で動作する。
	この構成を成立させるため、共有 backbone の上に「物体中心表現 → 関係 → 時系列 Phase」という縦の流れと、「Phase embedding → detection refine」の横のフィードバックを併設し、別系統として **Exo encoder + 同時刻整合 + 蒸留** を訓練時のみ並走させる。短期ゴールに対応するアーキテクチャは、**共有空間 backbone + 物体中心表現 + 関係モジュール + 時系列 Phase head + 双方向フィードバック + Exo 補助経路(訓練時のみ)** の構成とする。
	### 4.2 空間 backbone（Ego 入力）〔§12 サーベイ反映：C1/E2/B1/B4/C2 で更新〕
	- 共有 backbone は **DINOv2 ViT-L/14-with-registers を主軸採用として確定**する（C1/E2 サーベイ）。register token 4 個で高ノルム artifact patch を除去でき、形状類似ペア（Forceps / Tweezers / Needle Holders）の識別と Mask DINO の小物体 mask 品質に効く。vanilla DINOv2 からの drop-in 置換で訓練コストは増えない。Swin-Transformer を計算コスト重視の代替候補として維持し、ConvNeXt は優先度を下げる。DINOv3 の distilled 重みが揃い次第 Stage A の ablation に追加する。
	- **Stage A の必須 ablation として backbone 比較表**（DINOv2 ViT-L vs ViT-B vs SurgeNetXL CAFormer-S18 vs EndoViT ViT-B vs Swin-L）を作成する。C1 サーベイで、開放手術 × Ego × 0.5 fps × multi-task の交差領域に foundation backbone 比較研究が皆無であり、DINOv2 ViT-L vs SurgeNetXL の直接数値比較が文献に存在しないことが判明したため、この ablation 自体が C1 の中核 contribution となる。
	- backbone fine-tuning は **heavy full fine-tuning を回避**し（F1 サーベイ：LIFT が「heavy fine-tuning hurts」＝tail-class 悪化を示す）、**MTLoRA を plain ViT 用に porting** して採用する。MTLoRA 原論文は階層 Swin 専用のため ViT-L への移植は本研究の貢献余地となる（C1/E2）。各 LoRA は DoRA（ICML 2024 Oral）で magnitude + direction 分解により強化する。**実行環境は RTX 6000 Ada（48GB）/ RTX A6000×2（48GB）/ RTX A5000×5（24GB）/ Quadro RTX 8000×2（48GB）であり〔2026/05/21 更新：旧記述「QLoRA 量子化で A100 1 枚での実装を確保」を実環境に合わせて改訂〕、48GB 級 GPU（RTX 6000 Ada / A6000）では DINOv2 ViT-L/14 + ViT-Adapter + Mask DINO を bf16 + 勾配チェックポイントで実行できる見込みであり、QLoRA 量子化は VRAM 不足時のフォールバックとする。24GB 級（A5000）単体で ViT-L を扱う場合は QLoRA + 勾配チェックポイントを併用する。Δ の基準点を作る学習（S0-frozen・S4・STEP B の結合手法）は世代の揃った単一 GPU モデル（RTX 6000 Ada を第一候補）に固定し、数値再現性を担保する。Quadro RTX 8000 は bf16 非対応（Turing 世代）のため、基準点学習には用いず軽量実験・推論評価・前処理に限定する。** MTLoRA-style の task-specific 低ランク枝は task head 側に限定するのが清潔（E2）。**保守的フォールバック（2026/05/21 追加）**：plain ViT への MTLoRA 移植が不安定な場合は、backbone を一度 LoRA-Q/V + 最終 2〜6 block のみ解凍し、MTLoRA-style の task-specific 低ランク枝を task head 側に限定する構成に退く（E2 サーベイ推奨の清潔な配置）。
	- 検出/分割ヘッドは **Mask DINO 系**（query ベースで box + mask を統一表現）を **暫定第一候補**とする〔2026/05/21 格下げ：「本命確定」→「暫定第一候補」〕。C2 サーベイで、object token 共有・時系列接続容易性・phase 条件付け適性のいずれもで統合ヘッドが分離ヘッドを上回ることが確認され、アーキテクチャとしては Mask DINO が有力である。**ただし「本命確定」としない理由**：B2 サーベイが EgoSurgery-Tool 上で **DETR 系は構造的に弱い**ことを実証している（Deformable-DETR 30.0 \< DINO 39.7 \< DDQ 43.2 \< VarifocalNet 45.8、すなわち dense detector に 4〜16pt 劣る）。これは Hungarian matching の one-to-one マッチングが稀少クラスの query を早期に quench する構造的バイアスによると示唆されており、Mask DINO も DETR 系である以上同じリスクを背負う。よって **Mask DINO を本命と確定するのは、recipe 一本化（STEP 0）後に Mask DINO（+ 長尾対策）が現行上位（Relation-DETR / VarifocalNet）を実際に上回った後とし、それまでは暫定位置づけに留める**。長尾 quench への直接対策として **class-balanced denoising sampling を提案手法として追加する〔2026/05/21 追加〕**—Mask DINO の denoising クエリ生成時に、GT ラベルのクラス頻度に反比例したサンプリング重みで稀少クラス（Skewer/Syringe）の noised GT クエリを優先的に水ましし、Hungarian マッチングの手前で稀少クラスに十分な勾配信号を与える（C2 サーベイで「30 倍長尾×15 クラスには class-balanced denoising sampling が必要だが未確立」と指摘された未開拓領域）。Co-DETR（ICCV 2023）を長尾耐性の対照候補、VarifocalNet + Mask2Former 完全分離ヘッドを撤退候補とする。再現性の高いベースラインとして **VarifocalNet（det）**を必ず並走させる（B2 サーベイ：EgoSurgery-Tool の旧 recipe SOTA は VarifocalNet AP 45.8）。**〔2026-06-19 実測更新〕** その後 DETR 系を含む 10 モデルを実測した結果、**DETR 系の Relation-DETR が mAP 0.730（3-seed 平均 0.727・σ0.004・AP_rare 0.758）で 1 位**となり、「DETR 系は構造的に弱い」という B2 の懸念は本データ・現行 recipe では覆った。Relation-DETR を **凍結源 backbone の暫定第一候補**とする（§12・§13・§16。旧 recipe の VFNet 0.618／論文 45.8 とは eval recipe が異なるため STEP 0 で一本化して比較）。
	### 4.3 物体トークン抽出〔§12 サーベイ反映：C4/B4 で更新、2026/05/21 に mask 属性を Phase-1 条件付きに分離〕
	- 検出された各術具・手インスタンスから、**Mask DINO の object query 最終層出力**と ROI Align ベクトルを連結して **object token** を作成する（C4 サーベイ主推奨）。結合効果②の主張は「class / instance ID が事前定義された手・術具の物体中心表現が phase 認識に有効」であり、supervised な検出器ベース object token がこの仮説と最も整合する。
	- **object token の 2 フェーズ構成〔2026/05/21 再編：mask / hand-tool 不在の制約を反映〕**：
		- **Phase-0（bbox フェーズ、現時点で実行可）**：object token = \[visual feature (256), class embedding (64), bbox position (8), confidence (1), hand identity (2)\]。mask shape 属性を含まず、ROI Align + bbox 位置だけで結合効果②を成立させる。線形射影で d = 256〜512 に統一する。
		- **Phase-1（mask フェーズ、mask 入手で起動）**：mask 入手後に mask shape (64) と mask pooling ベクトルを object token に追加する。mask shape 属性の追加によるΔ Phase F1 は Phase-1 の ablation として計測する（§8.2）。
	- いずれのフェーズでも、各フレームで Max_K 個（8〜16：術具最大 3 + 両手 2 + scene slot 3〜11）の object token を抽出する。未検出スロットには learnable \[PAD\] token を割り当て、self-attention mask で除外する。
	- **slot attention を sub-stream として併走**させる（C4 サーベイ）。DINOv2 ViT-L/14 特徴上で VideoSAURv2 / SlotContrast 風の unsupervised slot attention を走らせ、(a) 検出器の miss 領域を補完する scene slot、(b) 結合効果②の ablation 対照（unsupervised slot vs detector-based object token）、(c) 弱教師事前学習の pretext として用いる。**slot attention は mask アノテーションを要さず、Phase-0 でも実行可能**であり、mask 不在期間の scene 表現補完手段としても価値が高い。
	- mask query embedding は DVIS の referring tracker スタイルでそのまま時系列伝搬に渡せる設計とし、mask 重なり率・mask boundary 共有率を関係モジュール（Phase-2）への prior として供給する（B4 サーベイ。これらは mask 入手後に起動）。
	### 4.4 手-術具関係モジュール（Phase-2／mask 入手で起動・将来拡張）〔§12 サーベイ反映：B7/B8 で更新、2026/05/21 に条件付きモジュールとして明記〕
	- **位置づけ：本モジュールは Phase-2（mask 入手で起動する将来拡張、§0.1 Phase-1）に属する**。エッジ疑似ラベルの主要生成源である mask-IoU が mask アノテーションを前提とするため、関係結合の検証は mask 入手後に起動する。mask が M2 期間内に入手できない場合は、本モジュールを本論文の中核主張から外し、Phase-0（結合効果①②・D-A・D-B）で論文を成立させる。
	- **Mask DINO の per-instance object query をグラフノード**とする two-stage GNN-on-detector-queries 設計とする（B7 サーベイ）。PViC（ICCV 2023）の cross-attention「predicate visual context」+ box-pair positional embedding を借用し、SSG-Com / MCIT-IG の bipartite / dynamic graph 構造（hand-identity ノード = Operator R/L・Assistant + action エッジ）を採用する。ノード（object query）と box-pair positional embedding は bbox でも構成可能だが、エッジ疑似ラベルの品質が mask 依存である。
	- エッジ特徴:中心距離、相対面積、IoU、最近傍距離、mask 接触率、過去フレーム継続性。（mask 接触率は Phase-1、それ以外は bbox でも計算可能。）
	- 出力:**grasp / near-contact / handover / two-hand manipulation** の 4 種を中心とする関係ラベル(疑似ラベルは Hand-Tool マスクから自動生成)。
	- **エッジ疑似ラベルの自動生成基準**（B7 サーベイ、EgoSurgery-HTS マスクから生成、Phase-1）：grasp = mask-IoU(hand, tool) ≥ 0.15 かつ接触が 3 フレーム継続、near-contact = 中心距離 ≤ k·√(area) かつ最近傍距離 ≤ d_max、handover = hand_i の mask-IoU 減少 + hand_j の増加が 5 フレーム継続、two-hand manipulation = 両手が同一 tool に grasp エッジ。focal loss（γ=2, α=0.25）でマルチラベル分類する。疑似ラベル精度は 200 フレームの人手検証で 80% 以上を担保ラインとし、下回れば mask-IoU 閾値を見直す。
	- **mask 入手前の代替〔2026/05/21 追加〕**：mask 入手前に関係モジュールのパイプラインを先行実装・動作確認したい場合は、bbox-IoU・中心距離・包含関係から生成した **粗い near-contact 疑似ラベル** を使う。ただし bbox だけでは grasp（接触）と near-contact（接近）の分離が原理上困難であり、関係結合（Phase-2）の本格検証には mask が必要である。
	- **HODN（IEEE TMM 2024）の stop-gradient** により、関係損失（Phase-2）が検出（結合効果①）の box regression を汚染しないよう保護する（B7 サーベイ）。
	- 時系列文脈は LABRAD-OR 式の memory scene graph（前フレームのエッジ予測を入力に追加）で軽量に取り込む。
	- 本モジュールは Phase head への文脈として、また将来的な動作認識への接続点として機能する（関係結合＝Phase-2 の中核）。
	### 4.5 工程（Phase）ヘッド：時間構造つき系列モデル〔§12 サーベイ反映：B5/C3/D2/C4 で更新〕
	- フレーム単位ではなく **object tokens over time → temporal model → phase sequence** で扱う（結合効果②の実現経路）。**入力となる object token は §4.3 Phase-0 の bbox 由来 token（mask shape 属性なし）で成立するため、本ヘッドおよび結合効果②の検証は mask 不在の Phase-0 で全面実行できる〔2026/05/21 確認〕**。mask 入手後（Phase-1）は object token に mask shape 属性が加わるが、時系列ヘッド自体の設計変更は不要である。
	- 0.5 fps の Ego を対象とし、**長距離コンテキスト**を捉える設計を採用する。B5/C3/D2 サーベイに基づく S4 候補を、2026/05/21 の見直しで **2 段階運用（第 1 波／第 2 波）** に再編する（全 6 候補を並列に並べると実験数が 50〜100 規模に膨張し、§10.1 の計算コスト見積もりと矛盾するため）。
		- **第 1 波（S4 本体、必須）**：TeCNO（causal dilated TCN、O(T)、online 友好、軽量、global feature 入力の §2.5 (b) 基準点）と SR-Mamba（MICCAI 2024、1 段階訓練、bidirectional Mamba decoder、線形計算コストで object-centric token 入力と最も適合）の 2 モデルに絞り、これを結合効果②検証（STEP B）の主軸とする。
		- **第 2 波（S4 安定後の上限探索・ベンチマーク拡充）**：HID-SSM（2025 SOTA、LA-SSM + GR-SSM、causal と contextual 両方）を主軸に、SKiT（online 上限・低計算）、Surgformer（offline 上限、divided ST attention + HTA）、SPRMamba（hybrid Mamba+Transformer）を順次追加する。これらは §2.6 の設計仮説 D-B（EgoSurgery-Phase 初の長距離時系列ベンチマーク）を直接裏付ける。Trans-SVNet、MuST は参考文献として保持。
		- **Surgformer / SR-Mamba / SPRMamba / HID-SSM は EgoSurgery-Phase で未評価であり、初ベンチマーク自体が publishable 貢献となる**（D2/C3 サーベイ、§2.6 D-B）。
	- **object-centric token 入力との適合性と時系列化設計**：Mamba 系が最も自然（線形計算量・長系列対応）。時系列ヘッドは heterogeneous token 列（per-frame global feature + per-frame top-K object tokens with type embeddings）を受け入れるよう設計する。**時系列化設計は SlotSSMs 風 block-diagonal Mamba に一本化し、SR-Mamba と一体の実装として扱う〔2026/05/21 見直し〕**—SlotSSMs 風の block-diagonal 構造は slot ごと独立に時間発展する SR-Mamba と見なせることができ、両者を別候補として並べるのではなく、SR-Mamba の Mamba decoder を block-diagonal 化したものを §2.6 D-A の主推奨アーキテクチャとする（C3-C4 結合の固有貢献ストーリー）。**serializer（raster / token-importance ordering）の要否は block-diagonal 採否で条件分岐する**：block-diagonal Mamba を採用する場合は slot ごとの独立 scan により 1-D 列への平坦化が不要となり serializer を省けるが、単一の selective scan（素の SR-Mamba / HID-SSM）を使う場合は object-centric token 列が 1-D でないため serializer を付す（D2 サーベイ）。第2推奨は Slot-BERT 風 bidirectional masked Transformer（C4 サーベイ）。
	- **常に causal 版と bidirectional 版を並行訓練・評価**する（D2 サーベイ：HID-SSM の公表値で約 1.7 pp accuracy gap を prior とし、透明に報告）。
	- 工程の順序性を反映する正則化を追加（B5 サーベイで支持）：
		- temporal smoothing loss
		- transition loss / impossible-transition penalty
		- phase order prior、および HID-SSM の continuous phase-progress regression branch を採用時系列モデルに移植し class-balanced focal loss と併用（D2 サーベイ）。
	### 4.6 双方向補完(Phase ⇄ Detection)— 中核モジュール
	本研究の主張（結合効果①②）を直接実現するモジュールであり、**STEP B の「予測相互作用」結合の自前実装**に対応する。§4.1 の設計思想を実装レベルで具体化する。
	- **Phase → Detection（結合効果①）**：Phase head の出力（logits または embedding）を detection head に注入する。**注入方式の primary/secondary を 2026/05/21 に逆転し、cross-attention 注入を primary、FiLM を軽量ベースライン / ablation 下限に再配置する**。**primary：cross-attention 注入**—C2 サーベイの推奨に従い、Mask DINO decoder の cross-attention 層に phase 分布を射影した c_phase トークンを追加 KV として注入する（c_phase_history で数フレーム前の phase memory も併用）。C2 サーベイは、FiLM が query 全体への affine で粒度が粗いのに対し cross-attention 注入は object query 単位の条件付けが可能であり、検出トークンと phase 文脈の結合に適していると評価している。**c_phase token に entropy gating を追加する〔2026/05/21 追加〕**—phase head の予測分布のエントロピーをゲート信号とし、phase 予測が不確実な（エントロピーの高い）フレームでは c_phase の注入強度を自動減衰させる。これにより Phase 側が未収束・課題の時期に誤った phase 文脈が検出を退化させるリスクを押さえ、stop-gradient（下記）と並んで Phase→Detection の安定化装置となる。**下限 / ablation ベースライン：FiLM 注入**—FiLM は低コストかつ安定で、C6 サーベイで MTRCNet-CL の correlation loss を feature-level 条件付けに拡張する位置づけとして推奨されたが、粒度が粗いため注入方式の **ablation 下限（これを上回らなければ cross-attention の価値がない）** として位置づける。**STEP B で cross-attention（primary）vs FiLM（下限）vs SAK-style adapter bias の 3 者を厳密に比較検証する**。SAK（ICLR 2025）の Task-Specific Adapter Pool の思想を参考に、Phase embedding を「adapter bias」として detection head に注入する設計も検討する。ヘッドレベルの不均衡・類似・遮蔽対策として Co-DETR 補助 ATSS ヘッドの追加（Co-Mask-DINO 拡張）、Relation-DETR の position relation embedding 注入、MP-Former の mask-piloted denoising を併用する（C2 サーベイ）。
	- **Detection → Phase（結合効果②）**:object token 列を Phase head の主入力とする。画像 global feature は補助入力に留め、**判定の主軸は物体中心表現**とする。
	- **学習スケジュール**:Stage A で detection を安定化 → Stage D で双方向フローを on にする(初期段階で grad を相互に入れると未収束の信号同士で破壊しあうため)。
	- **gradient 制御**:Phase → Detection 経路には stop-gradient のオプションを持たせ、Phase 側の不安定性が検出を退化させない設計とする。
	- **Ablation 容易性**:Phase → Detection、Detection → Phase は config で個別に on/off できる構造とし、§8.1 の STEP B（片方向 vs 双方向の比較）で効果を厳密に分離評価する。
	### 4.7 Exo 補助経路（学習時のみ）— Phase-2（Exo）の経路〔§12 サーベイ反映：A4/D1/E2/E5 で更新〕
	Exo 多視点 SSL（view-consistent SSL による動作・時間表現の獲得＝Phase-2）を直接実現するモジュール。A4 サーベイで手術 OR setting での先行例がないことが確認され、本研究の独自性のフックとなる。
	- Exo 5 視点を **shared-weight encoder** で個別埋め込み → visibility-aware view gating で融合。**Exo encoder の第一候補は Hiera-B（VideoMAE V2 K710 + Endo-FM warm-start）**、Ego encoder は EgoVLPv2 初期化（D1 サーベイの最終推奨設計）。
	- **3 層構造の活用設計**（E3/A4/D1/E5 サーベイ統合）：
		1. **第 1 層：Exo 単独 SSL（Stage B 前半）**— VideoMAE v2 ベースの masked video modeling + playback speed prediction + temporal order prediction。hand-tool-guided MAE を併用。
		2. **第 2 層：Exo 視点間 view-consistent SSL（Stage B 後半）**— 5 視点間で同時刻の正例ペアを構成し、cross-view contrastive（PreViPS 式）を学習信号とする。view dropout（ランダムに 1–2 視点を落とす）で推論時の Exo 不在への汎化を促進。**temporal hard negative を追加する〔2026/05/21 追加〕**—同一視点内の異時刻フレーム（ただし同一工程内の近接時刻）を hard negative として contrastive 損失に加える。視点間正例だけでは表現が「視点不変」にはなるが「時刻弁別」にはならず、低 fps Ego の動作・時間表現獲得（Exo＝Phase-2）の目的とずれるため、時間方向の弁別性を与える temporal hard negative が必要となる。
		3. **第 3 層：Ego–Exo 間の整合と蒸留（Stage C）**— 時間同期 contrastive + Phase 分布整合 KL + tool-set 弱整合 + teacher–student distillation。
	- **fps 差への対処**（A4/D1 サーベイ）：Ego（0.5 fps）と Exo（25 fps）の fps 差 50 倍に対し、Ego 1 フレーム周辺 ±2 秒を 1 つの co-occurrence unit と定義し、Exo 側は対応時刻周辺の短いクリップを入力とする。SlowFast 的な dual-rate 構成も検討に値するが、SlowFast の原設計は α≤8 までであり α=50 は外挿領域である点に注意（D1 サーベイ）。
	- **Stage C の蒸留は Quattrocchi 式 2-level KD + AE2 / AlignEgoExo の temporal-alignment objective** を採用する（E2/E5/D1 サーベイ：unpaired ego-exo を temporal cycle consistency で扱う設計が 1 ego + 5 exo に合致。plain L2 feature distillation の代わりに使用）。同期が保証される場合 AE2 の DTW は過剰設計となりうるため、直接時刻マッピングで十分かを Phase-2 で検証する。
	- **推論時は本経路を切り離す**(branch-pruning / weight discarding を学習後に明示)。**Phase-2 で Exo 経路の重みを除いた推論で性能を再測し、branch-pruning 後の性能劣化がないことを検証する**（A4 サーベイ推奨）。
	- **Exo（Phase-2）の撤退ラインの 2 段階化〔2026/05/21 追加、§9 と整合〕**：A4 サーベイは、Exo の画角が術野近傍に限定されるため Ego-Exo 間の視野重複が大きすぎ、view-consistent SSL の学習信号が弱い可能性を指摘した。このリスクに備え、本格検証の手前に **第 1 段階の予備診断** を設ける—少量の Exo サブセットで cross-view contrastive の表現品質（視点不変性・時刻弁別性）を診断し、視野重複が大きすぎて信号が得られないと判断されれば、フル SSL パイプラインを走らせる前に Exo の役割を「Phase label の弱教師あり転写のみ」に早期縮退する。**第 2 段階** は実測後の縮退で、Phase-2 で Δ mAP・Δ Phase F1 の追加改善幅が 1σ 以内の場合に Exo を SSL から弱教師転写のみに縮退する。
---
## 5. 学習スキーム(段階学習) {toggle="true"}
	2 タスク結合（検出 × 工程）の学習は、**単一タスク基準の確立（STEP A）→ 結合学習（STEP B）** に簡素化する。Exo 多視点を使う段階（旧 Stage B / B′ / C）は **Phase-2 拡張**として末尾に縮約して残す（削除しない）。
	```javascript
Stage A（単一タスク基準）→ Stage D（2 タスク結合学習）  ／  Exo SSL 段階は Phase-2 拡張
	```
	### Stage A:単一タスク基準の確立（STEP A・Phase-0 主経路）〔2026/05/21 に A0/A1 に分離〕
	mask / hand-tool アノテーション不在の制約（§0.1）を反映し、Stage A を **Stage A0（bbox、現時点で実行可能）** と **Stage A1（mask、mask 入手で起動する条件付き）** に分離する。**ここで比較の三角形の分母（検出単独 = S0-frozen、工程単独 = S4）を同一凍結 backbone 上で確定させる。**
	- **Stage A0（bbox 検出学習、Phase-0 主経路）**
		- 目的:術具・手の **box** を安定化させ、**検出単独基準 S0-frozen**（凍結 backbone ＋ 検出ヘッド）の数値を確定させる。
		- 損失:`L_det`のみ。
		- 出力:bbox 検出の domain-specific strong baseline（Mask DINO の box ブランチ / VarifocalNet。検出ベースラインは Relation-DETR mAP 0.730 が現行 1 位、§4.2・§12・§13）。
	- **Stage A1（mask 学習、mask アノテーション入手で起動する条件付き）**
		- 目的:mask 入手後に術具・手の **mask** を安定化させ、instance segmentation の baseline（bbox + mask 版）を確定させる。
		- 損失:`L_det + L_mask`。
		- 出力:検出・分割の domain-specific strong baseline（Mask DINO / VarifocalNet / Mask2Former）。
		- mask が M2 期間内に入手できない場合は Stage A1 をスキップし、Stage A0 だけで結合学習（Stage D）に進む。
	- **工程単独基準 S4**：Stage A と同一の凍結 backbone 上に時系列ヘッド（TeCNO コア＋第 2 波、§4.5）を載せ、global feature 入力の工程単独基準を確定させる（§2.5(b)）。
	### Stage D：2 タスク結合学習（STEP B の各手法）〔§12 サーベイ反映〕
	- 目的:検出 × 工程の結合を学習し、単一タスク基準（S0-frozen / S4）に対する Δ を測る。**双方向フィードバック（§4.6）を on にし、結合効果①②を統合検証する。** 関係・Exo（Phase-2）は当面 off（λ_rel = λ_view = 0）。
	- 結合手法は STEP B の比較群（共有エンコーダ MTL → 片方向 pipeline → PAD-Net/MTI-Net → MT4MTL-KD/SSG-Com、§2.3・§13）を順に実装し、各手法の Δ を同一土台で測る。
	- **損失重み付け（L4 最適化系の結合・併用アドオン）：FAMO を第一候補、DB-MTL の対数変換を併用**（C6 サーベイ推奨）。O(1) コストで全タスク損失を均等降下させつつ、異なる損失スケール（CE / focal / BCE / temporal smooth）を対数変換で自動正規化。勾配系（PCGrad / CAGrad / FAMO）は主軸ではなく**併用アドオン**と位置づける。
	- **勾配制御：GCond（arXiv 2025）の勾配蓄積 + 適応的仲裁メカニズム**を Phase → Detection 経路に導入し、Phase head の未収束信号が Detection head を退化させるリスクを低減（C6 サーベイ推奨）。
	- **negative transfer 監視：LibMTL の Δp 指標**（各タスクの単一タスク比改善率の平均）で結合学習中の negative transfer をオンライン監視する（STEP C 分析の入力）。
	### Phase-2 拡張（Exo 多視点 SSL）〔旧 Stage B / B′ / C を縮約。将来拡張・削除しない〕
	Exo 多視点を使う事前学習・整合・蒸留は **Phase-2 の将来拡張**として残す。要点のみ縮約して記す（詳細設計は §4.7、§12 A4/D1/E2/E5）。
	- **Exo 単独 SSL（旧 Stage B）**：VideoMAE v2 ベースの masked video modeling を主損失に、playback speed prediction・temporal order prediction を補助に、Exo 5 視点 × 25 fps の無ラベル映像へ適用。新規手法 **hand-tool-guided MAE**（手・術具領域を優先 mask、E3 サーベイで先行例なし）。Exo 視点間 cross-view contrastive + view dropout + temporal hard negative。
	- **未ラベル Exo での DINO/iBOT 継続事前学習（旧 Stage B′）**：DINOv2 ViT-L/14-with-registers backbone に短い DINO/iBOT 継続事前学習（E2 サーベイ：SurgeNetXL の追試）。held-out で 2% 未満の gain ならスキップ可。
	- **Ego–Exo cross-view alignment & 蒸留（旧 Stage C）**：時間同期 contrastive（fps 差 50 倍は Ego 1 フレーム ±2 秒を co-occurrence unit に）+ Phase 分布整合 KL + tool-set 弱整合（PU loss）+ teacher–student 蒸留（Quattrocchi 式 2-level KD + AE2 / AlignEgoExo temporal alignment、E2/E5/D1）。推論時は Exo ブランチを切り Ego 単独動作。
---
## 6. 損失関数(全体像) {toggle="true"}
	$$
	L = \lambda_{det} L_{det} + \lambda_{mask} L_{mask} + \lambda_{rel} L_{rel} + \lambda_{phase} L_{phase} + \lambda_{temp} L_{temp\\_smooth} + \lambda_{ssl} L_{contrast/MAE} + \lambda_{kd} L_{distill} + \lambda_{view} L_{view\\_consist}
	$$
	- `L_det`:Ego 検出(教師あり、bbox)。Phase-0 から有効。
	- `L_mask`:Ego 分割(教師あり)。**Phase-1 で起動する条件付き項〔mask アノテーション入手まで λ_mask = 0、2026/05/21 明記〕**。
	- `L_rel`:手-術具関係(疑似ラベル、BCE / focal)。**Phase-1 で起動する条件付き項〔mask / hand-tool アノテーション入手まで λ_rel = 0、2026/05/21 明記〕**。
	- `L_phase`:9 クラス CE(class weight、label smoothing)。Phase-0 から有効。
	- `L_temp_smooth`:近傍フレームの Phase 一貫性 + transition penalty。
	- **`L_couple`(2 タスク結合の損失・STEP B)**:結合手法に応じた予測蒸留/整合損失(PAD-Net/MTI-Net 型)と最適化バランシング(FAMO/DB-MTL、§5 Stage D)。これが「タスク結合の効果」を生む主機構。
	- `L_contrast/MAE`:Exo 自己教師あり(**Phase-2 項**、旧 Stage B/C で有効)。
	- `L_distill`:Exo teacher → Ego student(KL / feature matching)。
	- `L_view_consist`:Ego–Exo 同時刻整合(Phase logits KL + tool-set PU)。
	**λ_mask と λ_rel は Phase-2(mask / hand-tool アノテーション入手で起動)の条件付き項であり、入手まで 0 に固定する。同様に Exo 系(λ_ssl・λ_kd・λ_view)も Phase-2 項で当面 0。Phase-0 の主経路(検出 × 工程の 2 タスク結合)は `L_det`・`L_phase`・`L_temp_smooth`(＋ `L_couple`)で成立する。** **動作(Action)関連の損失は本フェーズでは設定しない。** 関係モジュールは将来的な動作認識への足場として残す。
---
## 7. 評価指標 {toggle="true"}
	### 7.1 主要指標:タスク結合の効果幅(Δ)
	本研究の成功条件は **結合効果予測①②** の検証(および将来拡張＝Phase-2 の関係結合・Exo の検証)であるため、**最重要指標は単一タスクモデルに対するタスク結合の効果幅**である。
	- **Δ 非有意時のフォールバック〔2026/05/21 追加、§2.6 と整合〕**：EgoSurgery は 21 動画・8 術者・1 施設と小規模であり（§12.24 G4）、Δ の variance が大き「Δ が 1σ 以内なら改善と主張しない」基準（§10.1）に照らすと、Δ が有意差に達しないシナリオが現実的にありうる。その場合のフォールバックとして、(1) **単一タスクでの絶対精度 SOTA 更新**（EgoSurgery-Tool の VarifocalNet AP 45.8・EgoSurgery-Phase の既存 SOTA を上回ること自体）、(2) **未ベンチマークモデルの初評価**（§2.6 の設計仮説 D-A：object-centric token × block-diagonal SSM アーキテクチャ、および D-B：EgoSurgery-Phase 初の Surgformer/SR-Mamba/SKiT/MuST/HID-SSM 長距離ベンチマーク）を方法論的貢献とする。したがって、結合効果①②（および Phase-2 の関係・Exo）のΔ を主張しつつも、Δ が有意差に達しない場合でも D-A・D-B によって論文が成立する二段構えとする。
	- **Δ mAP(結合効果①の検証指標)**
		- `Δ mAP = mAP(マルチタスクモデル) − mAP(術具検出単独モデル)`
		- 全体 mAP、稀少クラス mAP(Skewer / Syringe / Forceps を中心)、形状類似ペア(Forceps / Tweezers / Needle Holders)それぞれで分離して報告。
		- **本研究で最も重視する指標**。Δ mAP \> 0 を成功条件とする。
	- **Δ Phase F1(結合効果②の検証指標)**
		- `Δ Phase F1 = macro F1(マルチタスクモデル) − macro F1(工程認識単独モデル)`
		- 全体 macro F1、Dissection 内部の segmental F1@\{10, 25, 50\}、Closure 内部の segmental F1@\{10, 25, 50\} で報告。
		- Δ Phase F1 \> 0 を成功条件とする。
	- **Δ Edit score**(結合効果②の補助指標、工程境界の正確さを評価)。
	- **Δ の増幅効果(関係結合＝Phase-2 の検証指標)**
		- 関係モジュール on/off で Δ mAP・Δ Phase F1 がどれだけ拡大するかを報告。
	- **Δ の上限引き上げ効果(Exo＝Phase-2 の検証指標)**
		- Exo SSL(Stage B / C) on/off で Δ mAP・Δ Phase F1 がどれだけ拡大するかを報告。
		- 加えて、Exo SSL 単独効果の診断指標として、Ego の時間方向タスク(例:工程境界フレーム周辺の予測安定性、隣接フレーム間の表現類似度)に対する改善も計測する。
	### 7.2 タスク単位の絶対指標(副次指標)
	- 術具・手検出:**mAP**(全体、クラス別、稀少クラス分離報告)。Phase-0 から計測可能。
	- 術具・手分割:**IoU / mIoU**。**§0.1 Phase-1 条件付き指標（mask アノテーション入手で計測、〔2026/05/21 注記〕）**。
	- 関係認識:**接触/把持の F1**(疑似ラベル基準の診断指標)。**§0.1 Phase-1 条件付き指標（mask / hand-tool アノテーション入手で計測、〔2026/05/21 注記〕）**。
	- 工程認識:**フレーム単位 accuracy、macro F1、Edit score、Segmental F1@k**。Phase-0 から計測可能。
	（§7.1 の Δ mAP は bbox mAP であり Phase-0 から計測可能。Δ の増幅効果（関係結合＝Phase-2 の検証指標）は mask 入手後の条件付き。）
	### 7.3 内部診断(Phase ⇄ Detection の補完効果)
	- Phase 文脈を入れた場合/抜いた場合の稀少クラス mAP の差分プロット。
	- 工程境界フレーム周辺の検出精度推移。
	- Dissection / Closure 内部における誤検出パターンの定性比較。
	### 7.4 臨床的視点(別途、先生方と相談しながら整備)
	- 稀少術具の認識率、工程境界の正確さ、誤認識の臨床的影響度。
---
## 8. 実験運用(Hydra + W&B + 段階別実験 ID) {toggle="true"}
	- Hydra で `model / data / train / stage` を 4 軸の config group とする。
	- 各 Stage(A〜D)の結果は **同一 W&B project** に分離した group で集約。
	- 実験 ID は `timestamp_confighash` 形式とし、`experiments/{id}/` に config / metrics.json / checkpoints を保存。
	- 全実験で `seed = 42` を固定、`deterministic = True`、`cudnn.benchmark = False`。
	### 8.-1 eval recipe 整合性の運用規則〔2026/05/24 新設、§15 と整合〕
	S0 完走後に発覚した split 取り違え・test_cfg 不一致（§15.1・§15.2）を踏まえ、Δ 評価の前提となる「評価条件（eval recipe）」の運用を本節で明文化する。これは §15.4・§15.6 をルーティン運用に落とし込んだものである。
	- **eval recipe の定義**：データ split（train/val/test の image・annotation 数）+ 検出後処理 test_cfg（score_thr / max_per_img / nms_pre / nms_iou）+ 実行サーバー名。
	- **全実験で eval recipe を metrics.json に併記する**：`metrics.json` の `eval_recipe` field に上記を記録（§15.3 G3）。これがない実験は Δ 基準点として使用しない。
	- **locked-down test_cfg の強制**：全 detector・全 stage で `score_thr = 1e-8, max_per_img = 300, nms_pre = 3000, nms_iou = 0.6` を `MMDetTrainer` が強制上書きする（§15.3 G1）。detector ごとの mmdet default 差を排除する。
	- **論文公式 split の固定**：`data/splits/ego_*.txt` を EgoSurgery-Tool 公式 split（train 10 動画 = 9657 images / val 2 動画 \{09,10\} = 1515 images / test 3 動画 \{04,05,07\} = 4265 images）に固定して git 管理し、変更を禁止する。`preprocess_ego.py` の `assert_paper_split()` が論文 Table 3a と一致しなければ起動時に停止する（§15.3 G2）。
	- **Δ 計算時の recipe 照合**：`DeltaCalculator` は Δ を計算する 2 実験の `eval_recipe` を照合し、test_cfg または split サイズが不一致なら `InconsistentRecipeError` を送出する。recipe 差由来の比較は Δ 表に載せず、§3 の sensitivity 表として分離する（§15.4 B・C）。
	### 8.0 サーバー割り当ての運用原則〔2026/05/23 新設、2026/05/24 暫定運用を追記〕
	Δ 基準点の数値再現性を担保するため、以下の原則でサーバーを割り当てる。詳細は §13.8 GPU 割り当てと整合。
	- **RTX 6000 Ada ×1（Ada Lovelace, 48GB）— Δ 基準点専用**：S0-frozen・S4 第 1 波・STEP B(結合手法)・最終評価の本実験および Phase-2(Exo)の Ego fine-tuning。Δ の分子・分母となる学習はすべてこの GPU に固定し、世代混在による浮動小数点丸め差異を排除する。
	- **RTX A6000 ×2（Ampere, 48GB）— 派生実験・基盤整備**：S2・S3（基盤整備）、Phase-2（mask instance seg・関係モジュール、旧 S1）、S4 第 2 波（D-B ベンチマーク拡充）、STEP B 注入方式 ablation、最終評価の ablation・転移検証。DDP 使用時は effective batch size を記録。基準点に直接影響しない実験のみここで実行する。
	- **RTX A5000 ×5（Ampere, 24GB）— Exo SSL 専有（Phase-2）**：Phase-2 予備診断（2〜3 枚）、Phase-2 の Exo SSL 学習（旧 Stage B-C、5 枚 DDP）。Exo は 5 fps 程度にサブサンプリングして 24GB VRAM 制約と計算量を調整。
	- **Quadro RTX 8000 ×2（Turing, 48GB）— 軽量専用**：bf16 非対応のため基準点学習には使わない。推論評価・データ前処理・軽量なデバッグ実行に限定。
	- **並行実行の原則**：6000 Ada が S0-frozen を回している間に A6000 で S2・S3 の基盤整備を並行、A5000 でデータ前処理を進めるなど、3 台のサーバーを同時稼働させて全体スループットを最大化する。ただし、Δ 基準点の実行は必ず 6000 Ada に固定する。
	- **暫定運用：RTX 6000 Ada 未配備期間〔2026/05/24 追記、2026/05/25 DDP 条件追加〕**：RTX 6000 Ada が未配備の期間は、Δ 基準点学習を `bengio`（RTX A6000 ×2）上で実行することを暫定的に許容する。その場合、以下の 6 条件をすべて満たすこと。(1) 同一の Δ 比較群（例：S0-frozen の VarifocalNet と Mask DINO と Co-DETR、検出単独モデルと結合モデル）は必ず同一サーバー上で揃えて測定する、(2) `metrics.json` の `eval_recipe.server_name` と各実験フォルダの `server.txt` にサーバー名を記録する、(3) RTX 6000 Ada 配備後に Δ 基準点を再測定する必要が生じうることを §14 に明記する。**〔2026/05/25 追加〕** (4) DDP（複数 GPU）使用時は、同一 Δ 比較群内の全モデルを同一 GPU 構成（同一サーバーの同一 GPU 枚数・同一 DDP 設定）で揃える。単一 GPU と DDP の混在は effective batch size・NCCL allreduce 非決定性・BN/LN 挙動差により Δ の意味を崩壊させるため禁止する。(5) DDP 使用時は effective batch size（GPU 枚数 × per-GPU batch size）を `metrics.json` の `eval_recipe` に記録する（`eval_recipe.gpu_count`・`eval_recipe.effective_batch_size` フィールド）。(6) learning rate の線形スケーリング適用有無を config に明記する（DDP で effective batch size が変わる場合、lr を線形スケーリングするか per-GPU batch size を調整して effective batch size を維持するかを選択し、選択結果を記録する）。サーバー名の解決は `EGOSURGERY_SERVER_NAME` 環境変数 → Hydra `logging.server_name` → `socket.gethostname()` の優先順とする。
	### 8.1 中核 ablation(STEP B 比較群 × 単一タスク分母 の Δ 検証)
	本研究の主要 ablation は、旧 A1〜A7（旧フレームの仮説別検証）を **STEP B 比較群（既存結合 6 手法・4 層）× 単一タスク分母（S0-frozen / S4）の Δ 表** ＋ **STEP C 分析軸** ＋ **STEP D 仮説検証**へ再設計する。比較は §15.4 A の strict 3 条件（公式 split / locked-down test_cfg / eval_recipe 一致）を満たす同一土台（比較の三角形）で行う。
	**(1) STEP B：既存結合の比較群（層 × 手法 × 役割 × 優先度）**
	<table fit-page-width="true" header-row="true">
<tr>
<td>層</td>
<td>手法</td>
<td>役割</td>
<td>優先度</td>
</tr>
<tr>
<td>L1 共有表現</td>
<td>共有エンコーダ MTL</td>
<td>最も素朴な結合の下限。negative transfer の有無をまず可視化</td>
<td>必須・最初</td>
</tr>
<tr>
<td>L2 片方向</td>
<td>片方向 pipeline（検出→工程 / 工程→検出）</td>
<td>方向ごとの効果を分離。双方向の前提</td>
<td>必須</td>
</tr>
<tr>
<td>L3 予測相互作用</td>
<td>PAD-Net・MTI-Net（予測蒸留）／§4.6 双方向（自前実装）</td>
<td>予測を相互に注入する主要群。結合効果①②の主検証</td>
<td>主要</td>
</tr>
<tr>
<td>L3 予測相互作用</td>
<td>MT4MTL-KD・SSG-Com（ドメイン SOTA）</td>
<td>手術ドメインの結合 SOTA との比較</td>
<td>主要</td>
</tr>
<tr>
<td>L3/L4</td>
<td>Cross-Task Consistency</td>
<td>整合制約による結合</td>
<td>余力</td>
</tr>
<tr>
<td>L1 共有表現</td>
<td>Cross-stitch・MTAN</td>
<td>古典的 soft-parameter sharing の参考点</td>
<td>参考</td>
</tr>
</table>
	※ 勾配系（PCGrad / CAGrad / FAMO）は結合手法そのものではなく **L4 最適化バランシングの併用アドオン**であり、主軸には置かない（§5 Stage D・§8.2）。
	**(2) 単一タスク分母に対する Δ 表（結合効果①②の指標）**
	<table fit-page-width="true" header-row="true">
<tr>
<td>Ablation</td>
<td>比較対象（分母）</td>
<td>検証する結合効果</td>
<td>主要指標</td>
</tr>
<tr>
<td>**B-det**</td>
<td>各結合手法 vs **検出単独 = S0-frozen**（凍結 backbone + 検出ヘッド）。同一 recipe（strict 3 条件）</td>
<td>**結合効果①**（工程文脈→検出）</td>
<td>Δ mAP、稀少クラス Δ mAP（Skewer / Syringe）、形状類似ペア Δ mAP（Forceps / Tweezers / Needle Holders）</td>
</tr>
<tr>
<td>**B-phase**</td>
<td>各結合手法 vs **工程単独 = S4**（凍結 backbone + TeCNO、global feature）</td>
<td>**結合効果②**（object-centric→工程）</td>
<td>Δ Phase F1、Dissection / Closure 内部 segmental F1@k</td>
</tr>
<tr>
<td>**B-dir**</td>
<td>片方向 vs 双方向（§4.6 の Phase→Detection・Detection→Phase を個別 on/off）</td>
<td>方向性の寄与（結合効果①②）</td>
<td>Δ mAP・Δ Phase F1 の差</td>
</tr>
<tr>
<td>**A7**</td>
<td>object-centric token + block-diagonal Mamba vs 通常 selective scan Mamba / global feature 入力</td>
<td>**D-A**（設計仮説、§2.6・Δ 非依存）</td>
<td>アーキテクチャの絶対精度・計算効率（方法論的貢献の検証）</td>
</tr>
</table>
	※ A7（D-A 検証）は Δ の有意性に依存しない方法論的貢献として**保持**する（二段構えの後段、§2.6）。
	**(3) STEP C：差の要因分析（Δ がなぜ出た/出ないか）**
	- **per-class 分析**：稀少クラス（Skewer / Syringe）・形状類似ペア（Forceps / Tweezers / Needle Holders）で Δ がどう分布するか。
	- **工程境界分析**：Dissection / Closure の境界周辺で Δ Phase F1・segmental F1@k がどう動くか。
	- **negative transfer 分析**：LibMTL の Δp 指標で、どの手法・どのタスクで負の転移が出るか（§5）。
	- **タスク自信の相補性**：検出と工程の予測エントロピーの相補関係（一方が不確実な局面でもう一方が効くか）。これが H-C（不確実性駆動の双方向結合）の動機になる。
	**(4) STEP D：観察から仮説（比較群へ戻して検証）**
	- STEP C の観察を「この観察への解」として、仮説プール（H-C / H-A / H-H、§2.3）から選ぶ/作り直す。
	- 立てた仮説を STEP B の比較群に「新手法」として戻し、同一土台（比較の三角形）で Δ を測る。探索と検証を地続きにする。
	- **関係結合（mask 依存）・Exo SSL の ablation は Phase-2** に置く（mask / Exo 入手で起動。旧 A5/A6 に相当）。
	### 8.2 補助 ablation〔§12 サーベイ反映〕
	アブレーションはフェーズ帰属を明示する：STEP B の Δ 表（B-det/B-phase/B-dir）・A7 と以下の長尾・損失系 ablation は Phase-0（bbox）で実行可能。関係モジュールのエッジ特徴分解と Exo SSL の分解は Phase-2（mask / Exo 入手で起動）。
	- Stage 順序の入れ替え(A→D / A→B→D / A→B→C→D)。
	- **損失重み付け方式（5 条件）**（C6 サーベイ推奨）：(i) Equal Weighting, (ii) Uncertainty Weighting, (iii) FAMO, (iv) DB-MTL, (v) PCGrad + DB-MTL log transform。LibMTL で統一実行。
	- **view-consistent SSL の構成要素分解**(cross-view contrastive のみ / cross-view masked prediction のみ / Ego–Exo 同時刻整合のみ / 全部入り)— Exo（Phase-2）の内部分解。
	- **hand-tool-guided MAE vs random mask**（E3 サーベイ推奨）：Stage B の masking strategy の効果を分離評価。
	- **関係モジュールのエッジ特徴選択**(位置のみ / mask 接触のみ / 運動量のみ / 全部入り)— 関係結合（Phase-2）の内部分解。
	- **Phase → Detection 注入方式**（C6 サーベイ推奨）：FiLM vs cross-attention vs SAK-style adapter bias を STEP B で比較。
	- **時系列モデル比較**（B5 サーベイ推奨）：TeCNO vs LoViT vs SKiT vs SR-Mamba を S4 で比較。入力長 / 計算量 / 精度 / online 対応で評価。
	- **長尾損失・拡張の独立 contribution〔2026/05/21 追加、§3.3 と整合〕**：EQLv2 vs Seesaw vs Logit Adjustment の長尾損失比較、Repeat Factor Sampling・Decoupled cRT のサンプリング比較、temporal-consistent copy-paste vs フレーム独立 naive Copy-Paste の拡張比較を STEP B で実施する。F1 サーベイで「手術・Ego 映像での標準長尾損失の系統的ベンチマークが不在」と確認されたため、この長尾手法比較自体を、補助 ablation に留めず **手術 Ego マルチタスク設定での初の長尾手法ベンチマークという独立した contribution** として位置づける。報告は overall mAP に加え per-class AP（Skewer/Syringe 等の稀少クラス）と head/medium/tail 分割で行う。
---
---
## 9. 今後の判断ポイント(MTG での宿題) {toggle="true"}
	判断ポイントを新フレーム（分析ファースト・タスク結合）に合わせて再編する。**STEP 0 ブロッカー（eval recipe 一本化・凍結源確定）と STEP C 後の仮説選択を新設**し、検出ヘッド/backbone/ベンチ確定の運用判断（旧 #6〜#8）は保持、動作・関係・Exo の判断は Phase-2（将来判断）へ移す。
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>判断項目</td>
<td>判断トリガー</td>
</tr>
<tr>
<td>N1</td>
<td>**eval recipe の公式一本化**（STEP 0 ブロッカー・最優先）</td>
<td>1 モデルを 2 系統の recipe（locked-down test_cfg 系 / score_thr=0.0 系）で再 eval し Δ_recipe を実測（再学習不要）→ 公式 recipe を決定 → `build_eval_recipe` を一本化 → `DeltaCalculator` 保護を検出・工程の両方に適用（§8.-1・§13・§15.4）。Δ の土台が固まるまで結合の Δ 主張はしない</td>
</tr>
<tr>
<td>N2</td>
<td>**凍結源 backbone の確定**（STEP 0 ブロッカー）</td>
<td>暫定第一候補は **Relation-DETR（mAP 0.730）**。recipe 一本化後、S0-frozen / S4 / 結合手法が同一土台に載ることを確認して確定する（§4.2・§13）</td>
</tr>
<tr>
<td>N3</td>
<td>**STEP C 後の結合原理（仮説）の選択**</td>
<td>STEP B の Δ 表と STEP C の分析（per-class / 工程境界 / negative transfer / タスク自信の相補性）が出そろった時点で、仮説プール（H-C / H-A / H-H、§2.3）から「観察への解」を選ぶ/作り直し、STEP B 比較群に戻して同一土台で検証する（§8.1）</td>
</tr>
<tr>
<td>N4</td>
<td>**既存結合で Δ≈0 だった場合の主貢献の置き方**</td>
<td>STEP B で Δ が「1σ 以内」（§10.1）に留まる場合、主貢献を (1) D-A（object-centric token × block-diagonal SSM アーキ）、(2) D-B（EgoSurgery-Phase 初の長距離時系列ベンチマーク）、(3) 既存結合の異粒度・open surgery 挙動の体系的分析（negative transfer の実証）へ移す二段構え（§2.6）</td>
</tr>
<tr>
<td>6</td>
<td>**Mask DINO 主軸からの検出ヘッド切替**（§12 サーベイ反映：C2/B2）</td>
<td>検出ベースライン（recipe 一本化後）で Mask DINO vs Co-DETR を比較し APr（稀少クラス）で 3 ポイント以上の差が出れば mask フェーズ以降を Co-DETR ベースに切替。Mask DINO vs EoMT を比較し mask AP 同等以下なら EoMT（最大 4×高速）に切替。Mask DINO surgical Ego AP \< 50 なら detector ベースを諦め VideoSAURv2 + DINOv2 unsupervised slot に主軸切替（C4）</td>
</tr>
<tr>
<td>7</td>
<td>**backbone 主軸の切替**（§12 サーベイ反映：C1）</td>
<td>Stage A の backbone 比較 ablation で DINOv2 ViT-L が SurgeNetXL CAFormer に Phase Jaccard で 5pt 以上劣るなら主軸を SurgeNetXL に切替。UniSurg（V-JEPA ベース、EgoSurgery workflow で +14.6% F1）が ViT-L 重みを公開したら Stage A 初期化に優先検討（E2）</td>
</tr>
<tr>
<td>8</td>
<td>**評価ベンチマークと Δ 指標の確定**（§12 サーベイ反映：G4）</td>
<td>EgoSurgery-\{Phase, Tool, HTS\} を主ベンチマークとして確定済み。§11.A の「Open-MOH」は実在しないため MM-OR + EgoExOR へ置換を検討。転移検証用ベンチマーク（PhaKIR/GraSP/CholecT45/EgoExOR）のデータアクセス認証は取得に時間を要するため、STEP A 開始時点で申請手続きを開始する</td>
</tr>
<tr>
<td>2</td>
<td>**工程ラベル細分化の要否(Dissection / Closure 内部)**</td>
<td>工程境界の誤りパターンを analyze し、特定の段階で再現性のある混同が発生する場合（STEP C 工程境界分析と連動）</td>
</tr>
<tr>
<td>4</td>
<td>**評価軸の臨床的優先付け**(術後レビュー / 教育 / 記録自動化 / 医療安全 / 時間予測など)</td>
<td>先生方との次回相談時</td>
</tr>
<tr>
<td>P-1</td>
<td>**【Phase-2／将来判断】動作(Action)アノテーション追加の要否**</td>
<td>現フェーズで Phase ラベルが術具検出にどれだけ寄与するか（結合効果①の Δ mAP）、工程認識の到達精度（結合効果②の Δ Phase F1）が想定ラインに達するかを確認した時点で事後判断</td>
</tr>
<tr>
<td>P-2</td>
<td>**【Phase-2／将来判断】mask / hand-tool アノテーション入手時の関係結合の起動**（§0.1 の 2 フェーズ構成）</td>
<td>mask / hand-tool アノテーションが利用可能になった時点で Phase-2（mask 依存の関係結合）を起動する。具体的には instance segmentation（旧 S1、Stage A1）と関係モジュールを起動し、object token に mask shape 属性を追加、L_mask・L_rel の λ を 0 から立ち上げる。**判断トリガー**：(1) mask 入手見込みが立った時点で Phase-0 の進捗と照らしてスケジュールに組み込む。(2) M2 期間内に入手できないと判断された場合は、Phase-0（結合効果①②・D-A・D-B）のみで論文を構成し、関係結合・instance segmentation は「今後の課題」とする。判断時点と根拠を §3.1 に記録する</td>
</tr>
<tr>
<td>P-3</td>
<td>**【Phase-2／将来判断】Exo の役割拡張と撤退ライン**（§12 サーベイ反映：A4 で手術 OR での Ego-Exo SSL は前例なしと確認）</td>
<td>2 段階の撤退ラインを事前設計する（§4.7 と整合）。**第 1 段階**：予備診断で、少量 Exo サブセットの cross-view contrastive の表現品質（視点不変性・時刻弁別性）を診断し、視野重複が大きすぎて信号が得られなければフル SSL の手前で Exo を「Phase label の弱教師転写のみ」に早期縮退。**第 2 段階**：実測後に Δ mAP・Δ Phase F1 の追加改善幅が 1σ 以内なら Exo を「SSL のみ」から「弱教師転写のみ」に縮退し計算コストを削減。Exo の画角が術野近傍に限定され Ego-Exo 視野重複が大きすぎて学習信号が弱い可能性がある（A4 サーベイ結論）</td>
</tr>
</table>
---
## 10. サーベイロードマップ {toggle="true"}
	本研究のアーキテクチャ設計と仮説検証(結合効果①②＋将来拡張＝Phase-2)に必要な最新研究のサーベイ対象を、**7 大分類 × 約 45 細目** に構造化する。各細目には本研究での位置づけ(参照する § / 関連する結合仮説 / 関連する STEP)と優先度(高/中/低)を併記する。
	### 10.0 全体構造(7 分類)
	<table fit-page-width="true" header-row="true">
<tr>
<td>分類</td>
<td>何を問うサーベイか</td>
</tr>
<tr>
<td>**A. ドメイン軸**</td>
<td>どの「映像」「手術」「視点」がターゲットか</td>
</tr>
<tr>
<td>**B. タスク軸**</td>
<td>何を認識するか(検出 / 分割 / 工程 / 関係 / 動作)</td>
</tr>
<tr>
<td>**C. アーキテクチャ軸**</td>
<td>どう構成するか(backbone / 検出 / 時系列 / 関係 / マルチタスク)</td>
</tr>
<tr>
<td>**D. 時間モデリング軸**</td>
<td>どう時間を扱うか(短期 / 長距離 / 階層)</td>
</tr>
<tr>
<td>**E. 学習パラダイム軸**</td>
<td>どう学習するか(教師あり / 事前学習 / SSL / 半教師 / 弱教師 / 蒸留)</td>
</tr>
<tr>
<td>**F. 学習信号設計軸**</td>
<td>どんな損失・データ整形で学ぶか</td>
</tr>
<tr>
<td>**G. 評価・ベンチマーク軸**</td>
<td>何で測るか、どのデータセットで比較するか</td>
</tr>
	</table>
	### 10.A ドメイン軸(対象領域)
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**A1**</td>
<td>**open surgery 映像解析**</td>
<td>本研究の対象ドメインそのもの。腹腔鏡 / 内視鏡との差(遮蔽・照明変動・同時出現物体数・class imbalance)を理解する</td>
<td>高</td>
</tr>
<tr>
<td>**A2**</td>
<td>**手術映像解析(腹腔鏡・内視鏡以外)**</td>
<td>開放手術、整形外科、皮膚外科、ロボット支援外科など。OR scene understanding 全般</td>
<td>高</td>
</tr>
<tr>
<td>**A3**</td>
<td>**一人称視点(egocentric)映像解析**</td>
<td>Ego の特性(視野移動、頭部運動、frame rate の低さ)。Ego4D、EPIC-KITCHENS 等の一般 ego 研究も含む</td>
<td>高</td>
</tr>
<tr>
<td>**A4**</td>
<td>**多視点(multi-view)手術映像 / Ego–Exo learning**</td>
<td>無影灯マルチカメラ、OR の固定カメラ、ego-exo pair 学習。Exo（Phase-2）の直接の前提</td>
<td>高</td>
</tr>
<tr>
<td>**A5**</td>
<td>**医療映像解析の一般動向(foundation models 含む)**</td>
<td>SurgVLP、Endo-FM、SAM 系の医療応用。本研究を一般潮流に位置づけるための背景</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:EgoSurgery、Open-MOH(open multi-view OR Hospital)、GraSP、PhaKIR、SurgVLP、Endo-FM、Cholec80(対照群)、MICCAI EndoVis Challenges、Ego4D。
	### 10.B タスク軸(認識対象)
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**B1**</td>
<td>**物体検出(汎用)**</td>
<td>アーキテクチャの基盤。query-based(DETR / DINO 系)、anchor-based(VarifocalNet 系)、set prediction 全般</td>
<td>高</td>
</tr>
<tr>
<td>**B2**</td>
<td>**術具検出(surgical-specific)**</td>
<td>B1 の手術特化。形状類似・遮蔽・class imbalance への対処。**検出ベースライン・STEP B の主役**</td>
<td>高</td>
</tr>
<tr>
<td>**B3**</td>
<td>**手検出・手姿勢推定**</td>
<td>**S2 で導入**。own/other × left/right 区別、surgical glove 下の検出、egocentric hand-pose</td>
<td>高</td>
</tr>
<tr>
<td>**B4**</td>
<td>**セグメンテーション(instance / semantic / panoptic)**</td>
<td>**S1 の主役**。Mask2Former、Mask DINO、SAM 系。器具・組織・背景の同時分割</td>
<td>高</td>
</tr>
<tr>
<td>**B5**</td>
<td>**工程認識(phase recognition)**</td>
<td>**S4 以降の主役**。手術工程の長距離時系列分類</td>
<td>高</td>
</tr>
<tr>
<td>**B6**</td>
<td>**動作認識(action / gesture / surgical activity)**</td>
<td>現フェーズではスコープ外だが、§9 #1 の判断材料および将来拡張のため背景理解は必要。action triplet、JIGSAWS、Action Genome 系</td>
<td>中</td>
</tr>
<tr>
<td>**B7**</td>
<td>**HOI(Human-Object Interaction)**</td>
<td>関係モジュール（Phase-2）の理論的基盤。HOI 検出、interaction prediction、affordance</td>
<td>高</td>
</tr>
<tr>
<td>**B8**</td>
<td>**手-術具関係認識(hand-tool relation)**</td>
<td>**Phase-2（関係）の主役**。grasp / handover / two-hand manipulation、egocentric H+O</td>
<td>高</td>
</tr>
<tr>
<td>**B9**</td>
<td>**Scene graph generation(SGG)**</td>
<td>関係推論をグラフ構造で扱う潮流。surgical scene graph(SSG-Com)、MCIT-IG</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:Mask DINO、Co-DETR、QueryInst、Mask2Former、TeCNO、Trans-SVNet、SR-Mamba、LoViT、Surgformer、MuST、SKiT、HID-SSM、H+O、MCIT-IG、SSG-Com、SemiVT-Surge、GraSP。
	### 10.C アーキテクチャ軸(モデル構成要素)
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**C1**</td>
<td>**空間 backbone**</td>
<td>§4.2。Swin / ConvNeXt / DINOv2 / SAM encoder の比較。事前学習済み backbone の手術ドメインへの適応性</td>
<td>高</td>
</tr>
<tr>
<td>**C2**</td>
<td>**検出 / 分割ヘッド**</td>
<td>§4.2。query-based 統合ヘッド(Mask DINO)vs 分離ヘッド(VarifocalNet + Mask2Former)</td>
<td>高</td>
</tr>
<tr>
<td>**C3**</td>
<td>**時系列モデル(TCN / Transformer / SSM-Mamba)**</td>
<td>§4.5。フレーム列を入力に sequence 予測。各アーキテクチャの計算量・長距離性能のトレードオフ</td>
<td>高</td>
</tr>
<tr>
<td>**C4**</td>
<td>**物体中心表現(object-centric representation / slot attention)**</td>
<td>§4.3、**結合効果②の核**。ROI Align、slot attention、object query を時系列化する手法</td>
<td>高</td>
</tr>
<tr>
<td>**C5**</td>
<td>**グラフニューラルネットワーク・関係推論**</td>
<td>§4.4、**関係結合（Phase-2）の核**。graph transformer、message passing、edge feature 設計</td>
<td>高</td>
</tr>
<tr>
<td>**C6**</td>
<td>**マルチタスク学習**</td>
<td>研究全体の構造。head 分離 vs 共有 backbone、negative transfer 対策、§8 の動的重み付け</td>
<td>高</td>
</tr>
<tr>
<td>**C7**</td>
<td>**双方向補完(mutual / cross-task feedback)**</td>
<td>§4.6 の核。phase ⇄ detection、mutual learning、co-training architectures</td>
<td>高</td>
</tr>
<tr>
<td>**C8**</td>
<td>**多視点融合(view-gating / cross-view fusion)**</td>
<td>§4.7。visibility-aware fusion、view dropout、PreViPS</td>
<td>高</td>
</tr>
<tr>
<td>**C9**</td>
<td>**条件付け機構(FiLM / cross-attention / adapter)**</td>
<td>§4.6 の Phase → Detection 注入の実装手段</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:DINOv2、SAM、Mask DINO、Co-DETR、Slot Attention、Object-Centric Learning、Graph Transformer、MTL with Task Affinity、Mutual Learning、Deep Mutual Learning、PreViPS、MV2MAE、FiLM、Perceiver、Cross-Attention Adapter。
	### 10.D 時間モデリング軸
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**D1**</td>
<td>**短期時間モデリング(short clip)**</td>
<td>Exo の数秒区間の動作表現。video transformer、TimeSformer、VideoSwin</td>
<td>中</td>
</tr>
<tr>
<td>**D2**</td>
<td>**時間的な長距離文脈の獲得**</td>
<td>**S4 の核**。手術全体(分〜数十分)。causal TCN、long-range transformer、SSM(Mamba)、key-information pooling(SKiT)、hierarchical attention</td>
<td>高</td>
</tr>
<tr>
<td>**D3**</td>
<td>**オンライン vs オフライン推論**</td>
<td>推論時の causal 制約。online phase recognition、TeCNO、causal Mamba</td>
<td>中</td>
</tr>
<tr>
<td>**D4**</td>
<td>**階層的(slow / fast)時間モデリング**</td>
<td>Exo 高 fps と Ego 低 fps の二層構成。SlowFast、Dual-rate temporal modeling</td>
<td>高</td>
</tr>
<tr>
<td>**D5**</td>
<td>**時間アラインメント・同期学習**</td>
<td>Ego–Exo の anchor-based 学習。temporal alignment、TCC(Temporal Cycle Consistency)</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:TeCNO、Trans-SVNet、LoViT、Surgformer、MuST、SKiT、HID-SSM、SR-Mamba、SlowFast、TimeSformer、VideoSwin、TCC、Anchor-based contrastive。
	### 10.E 学習パラダイム軸
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**E1**</td>
<td>**教師あり学習(マルチタスク監視)**</td>
<td>§5 Stage A / D の基本枠組み</td>
<td>高</td>
</tr>
<tr>
<td>**E2**</td>
<td>**事前学習(pre-training / foundation models)**</td>
<td>backbone 初期化(DINOv2、SAM、CLIP、SurgVLP)。医療 foundation model の最新動向</td>
<td>高</td>
</tr>
<tr>
<td>**E3**</td>
<td>**自己教師あり学習(SSL)**</td>
<td>**§5 Phase-2（Exo 拡張）の核**。MAE / VideoMAE / MV2MAE、contrastive、playback speed、temporal order</td>
<td>高</td>
</tr>
<tr>
<td>**E4**</td>
<td>**教師なし学習**</td>
<td>クラスタリング、prototype learning、deep clustering(SwAV、DINO)</td>
<td>中</td>
</tr>
<tr>
<td>**E5**</td>
<td>**半教師あり学習**</td>
<td>Mean Teacher、FixMatch、SemiVT-Surge。少量 Ego ラベル + 多量 Exo 無ラベル</td>
<td>高</td>
</tr>
<tr>
<td>**E6**</td>
<td>**弱教師あり学習**</td>
<td>Ego の Phase ラベルを Exo に転写(§3.2 (3))。timestamp supervision、SkipTag</td>
<td>高</td>
</tr>
<tr>
<td>**E7**</td>
<td>**知識蒸留(teacher–student / cross-view distillation)**</td>
<td>**§5 Phase-2（Exo 拡張）の Ego 注入経路**。Soft Teacher、cross-view distillation、feature distillation</td>
<td>高</td>
</tr>
<tr>
<td>**E8**</td>
<td>**ドメイン適応・転移学習**</td>
<td>手術ドメインへの一般動画モデルの適応、Ego-Exo domain gap、test-time adaptation</td>
<td>中</td>
</tr>
<tr>
<td>**E9**</td>
<td>**アクティブラーニング**</td>
<td>動作ラベル追加(§9 #1)の効率化、uncertainty sampling、step-aware AL</td>
<td>低</td>
</tr>
	</table>
	**代表キーワード**:DINOv2、SAM、CLIP、SurgVLP、Endo-FM、VideoMAE、MV2MAE、MoCo、SimCLR、SwAV、SimMIM、Mean Teacher、FixMatch、SemiVT-Surge、Soft Teacher、Cross-View Distillation、DeiT-Distill、AdaMatch。
	### 10.F 学習信号設計軸
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**F1**</td>
<td>**クラス不均衡対応**</td>
<td>§3.3、稀少術具・工程偏り。focal loss、class-balanced sampling、copy-paste、稀少クラス sampling temperature、long-tailed recognition</td>
<td>高</td>
</tr>
<tr>
<td>**F2**</td>
<td>**マルチタスク損失バランシング**</td>
<td>§5 Stage D。uncertainty weighting、GradNorm、PCGrad、CAGrad、Auto-λ、negative transfer 対策</td>
<td>高</td>
</tr>
<tr>
<td>**F3**</td>
<td>**contrastive learning(image / video / cross-view)**</td>
<td>Exo（Phase-2）の主損失。SimCLR、MoCo、CLIP、view-consistent contrastive、time-contrastive</td>
<td>高</td>
</tr>
<tr>
<td>**F4**</td>
<td>**masked modeling(MAE / VideoMAE / MV2MAE)**</td>
<td>Exo（Phase-2）の主損失。Phase-2 拡張の中核。hand-tool-guided MAE という派生</td>
<td>高</td>
</tr>
<tr>
<td>**F5**</td>
<td>**疑似ラベル生成・整合性損失**</td>
<td>Phase ラベル転写、関係疑似ラベル(Hand-Tool マスクから生成)、PU loss、down-weighted BCE</td>
<td>高</td>
</tr>
<tr>
<td>**F6**</td>
<td>**時系列正則化(transition / smoothing / CTC)**</td>
<td>§4.5。順序制約、impossible-transition、temporal smoothing、phase order prior</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:Focal Loss、Class-Balanced Loss、Copy-Paste、Equalization Loss、Uncertainty Weighting、GradNorm、PCGrad、CAGrad、SimCLR、MoCo v3、VideoMAE、SimMIM、PU Learning、CTC、Edit-Loss。
	### 10.G 評価・ベンチマーク軸
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**G1**</td>
<td>**検出・分割の評価指標**</td>
<td>§7.2。COCO mAP、稀少クラス mAP の慣行、panoptic quality、boundary IoU</td>
<td>中</td>
</tr>
<tr>
<td>**G2**</td>
<td>**時系列認識の評価指標**</td>
<td>§7.2。Edit score、Segmental F1@k、relaxed accuracy、phase transition error</td>
<td>中</td>
</tr>
<tr>
<td>**G3**</td>
<td>**関係認識・HOI の評価指標**</td>
<td>§7.2。HOI mAP、triplet AP、interaction recall、SGG metrics</td>
<td>中</td>
</tr>
<tr>
<td>**G4**</td>
<td>**手術ドメイン既存ベンチマーク**</td>
<td>比較基準としての先行ベンチマーク。EgoSurgery、GraSP、PhaKIR、MICCAI EndoVis Challenges、Cholec80(対比用)</td>
<td>高</td>
</tr>
<tr>
<td>**G5**</td>
<td>**Ego-Exo / multi-view 系ベンチマーク**</td>
<td>Exo（Phase-2）関連の外部参照。Ego-Exo4D、Assembly101、CharadesEgo、H2O</td>
<td>中</td>
</tr>
<tr>
<td>**G6**</td>
<td>**長尾・希少クラス評価の慣行**</td>
<td>稀少クラス Δ mAP の正しい報告方法、tail-class metric、effective number-based weighting</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:Edit score、Segmental F1@k、Boundary IoU、HOI mAP、Action Triplet AP、Ego-Exo4D、EndoVis、Assembly101、CharadesEgo、Long-tailed Recognition Benchmarks。
	### 10.1 サーベイの実施順序(STEP 0–D と連動)
	ロードマップを STEP 0–D のスケジュールに沿って前倒しで配置する。**各 STEP を開始する前に、対応する細目のサーベイを終えていること**を目安とする。
	<table fit-page-width="true" header-row="true">
<tr>
<td>サーベイ完了目標</td>
<td>必読(高優先度)</td>
<td>副読(中優先度)</td>
</tr>
<tr>
<td>**S0〜S2 開始前(今)**</td>
<td>A1, A2, B1, B2, B3, B4, C1, C2, F1, G4</td>
<td>A3, A5, E2, G1</td>
</tr>
<tr>
<td>**S3〜S4 開始前**</td>
<td>B5, C3, D2, F6, G2</td>
<td>D1, D3, D4</td>
</tr>
<tr>
<td>**STEP B 開始前**</td>
<td>C4, C6, C7, C9, F2</td>
<td>E1, E8</td>
</tr>
<tr>
<td>**Phase-2（関係）開始前**</td>
<td>B7, B8, B9, C5, F5, G3</td>
<td>B6</td>
</tr>
<tr>
<td>**Phase-2（Exo）開始前**</td>
<td>A4, C8, D4, D5, E3, E5, E6, E7, F3, F4, G5</td>
<td>E4, E9</td>
</tr>
<tr>
<td>**最終評価・論文執筆段階**</td>
<td>G6、自分の Δ 値を既存ベンチに位置づけるためのメタサーベイ</td>
<td>—</td>
</tr>
	</table>
	### 10.2 補足:除外したが意識する価値のある分野
	- **腹腔鏡 / 内視鏡映像解析**:本研究のドメインからは除外しているが、**手法レベルの転用は非常に多い**(Cholec80、Trans-SVNet、SR-Mamba、SKiT などはほぼすべて腹腔鏡発)。ドメインとしては読まないが、**手法だけ抽出する読み方**で C3 / D2 / E5 のサーベイに織り込むのが現実的。
	- **手術ロボット・遠隔操作系(da Vinci、RAS)**:JIGSAWS など。動作粒度の理論的背景として B6 で軽く触れる程度でよい。
	- **一般映像認識・スポーツ映像解析**:長距離時系列モデル(MuST、Surgformer)の原型はスポーツ映像で先行することが多く、手法の背景理解として有用。
	### 10.3 サーベイ運用の指針
	- **読書ノートの一元管理**:本ページか別 Notion DB に「論文 ID / トピック / S 対応 / 一行要約 / 自分の研究への引用方針」を蓄積。後に §1.1 の関連研究や論文の Related Work 節に流用できる。
	- **比較表の早期作成**:同一カテゴリ内の手法(例:C3 の TeCNO vs LoViT vs SKiT vs HID-SSM)は、論文を読んだ時点で「入力長 / 計算量 / 精度 / online対応」を表に追記しておく。M3 で実装候補を選ぶ際の判断材料となる。
	- **必読論文数の目安**:各細目あたり 3〜10 本程度。優先度高は重点的に、優先度中は survey 1 本 + 代表 2〜3 本で充足する。
	- **更新リズム**:M1 / M3 / M5 のタイミングでサーベイ自体を見直し、進捗に応じて優先度・追加トピックを再評価する。
---
## 11. サーベイ結果 {toggle="true"}
	§10 のサーベイロードマップに基づき、2023 年〜2026 年 5 月の最新研究動向を調査した。22 細目のサーベイが完了。各サーベイの詳細は以下の子ページを参照。
	<page url="https://app.notion.com/p/368ee4d47777813e893be630ef77b9a7">§12.1 A1：open surgery 映像解析</page>
	<page url="https://app.notion.com/p/368ee4d4777781639fa9e38099748937">§12.2 A2：手術映像解析（腹腔鏡・内視鏡以外）</page>
	<page url="https://app.notion.com/p/368ee4d47777814db929d669de17fd8c">§12.3 A4：多視点手術映像 / Ego–Exo learning</page>
	<page url="https://app.notion.com/p/368ee4d477778145875bf53ad42a4573">§12.4 B1：物体検出（汎用）</page>
	<page url="https://app.notion.com/p/368ee4d4777781758912e5e2aa0c1f7e">§12.5 B5：工程認識（Phase Recognition）</page>
	<page url="https://app.notion.com/p/368ee4d477778106ac9efb750b05566d">§12.6 B8：手-術具関係認識（Hand-Tool Relation）</page>
	<page url="https://app.notion.com/p/368ee4d4777781a3aebdf39aad8d3ca7">§12.7 C6：マルチタスク学習（Multi-Task Learning）</page>
	<page url="https://app.notion.com/p/368ee4d477778141803ee9543b053265">§12.8 E3：自己教師あり学習（SSL）</page>
	<page url="https://app.notion.com/p/368ee4d477778168bcb7ef858c877971">§12.10 B2：術具検出（Surgical-specific Instrument Detection）</page>
	<page url="https://app.notion.com/p/368ee4d47777810d9879e6aa6ba2945b">§12.11 B3：手検出・手姿勢推定（Hand Detection & Pose Estimation）</page>
	<page url="https://app.notion.com/p/368ee4d477778198b022f5306622ab7f">§12.12 B4：セグメンテーション（Instance / Semantic / Panoptic Segmentation）</page>
	<page url="https://app.notion.com/p/368ee4d4777781a38647df4b4617698e">§12.13 B7：HOI（Human-Object Interaction Detection）</page>
	<page url="https://app.notion.com/p/368ee4d47777812aa1c0f321b2d275a6">§12.14 C1：空間 backbone（Spatial Backbone）</page>
	<page url="https://app.notion.com/p/368ee4d4777781b7ae14d7935af236df">§12.15 C3：時系列モデル（TCN / Transformer / SSM-Mamba）</page>
	<page url="https://app.notion.com/p/368ee4d47777819890c1f2de4633c654">§12.16 D1：短期時間モデリング（Short Clip Modeling）</page>
	<page url="https://app.notion.com/p/368ee4d4777781269287e50faa6199d0">§12.17 D2：長距離時間文脈（Long-Range Temporal Context）</page>
	<page url="https://app.notion.com/p/368ee4d477778173a3e7d9037118c96f">§12.18 E2：事前学習・Foundation Models（Pre-training & Foundation Models）</page>
	<page url="https://app.notion.com/p/368ee4d4777781fda80cf3d26e29fc06">§12.19 E5：半教師あり学習（Semi-Supervised Learning）</page>
	<page url="https://app.notion.com/p/368ee4d4777781619c8bcaf165833792">§12.20 F1：クラス不均衡対応（Class Imbalance / Long-Tailed Recognition）</page>
	<page url="https://app.notion.com/p/368ee4d4777781de9385c120a08f6a84">§12.21 サーベイ結果の横断的知見（全 22 サーベイ）</page>
	<page url="https://app.notion.com/p/368ee4d477778188832aef679b02f05c">§12.22 C2：検出 / 分割ヘッド（Detection / Segmentation Head）</page>
	<page url="https://app.notion.com/p/368ee4d4777781319d9fe1070f143611">§12.23 C4：物体中心表現 / Slot Attention（Object-Centric Representation）</page>
	<page url="https://app.notion.com/p/368ee4d47777819c9464fe08428cb57f">§12.24 G4：手術ドメイン既存ベンチマーク（Surgical Benchmarks）</page>
	---
	### 11.21 サーベイ結果の横断的知見（全 22 サーベイ）
	2026/05/18 実施分 8 件（A1, A2, A4, B1, B5, B8, C6, E3）、2026/05/20 追加分 11 件（B2, B3, B4, B7, C1, C3, D1, D2, E2, E5, F1）、さらに C2, C4, G4 の 3 件を加えた計 22 サーベイを横断して得られた主要な知見を以下にまとめる。
	**本研究の新規性のフック（サーベイで確認された空白領域）**：
	1. **一人称視点 × 開放手術 × マルチタスク（検出 + 工程 + 関係）の同時認識**：A1/A2 サーベイで先行例なしを確認。B2/B3/B4 サーベイでも、形状類似ペア対策・glove 下手検出・SAM 系セグメンテーションがいずれも腹腔鏡 EndoVis 評価に偏り、open surgery × egocentric では未検証であることが裏付けられた。
	2. **Object-centric temporal representation を Phase head の主入力とする設計**：B5 サーベイで先行例がほぼないことを確認（結合効果②の新規性）。C3/D2 サーベイで、検出由来の object token 列を長距離 SSM/Transformer に流し込む surgical 論文が 2026.05 時点で皆無であることが追加確認された。
	3. **Detection + Phase + Relation の三位一体 MTL**：C6 サーベイで既存文献は tool + phase の 2 タスクが最大であることを確認。E5 サーベイで、検出 × phase × 関係を同時に半教師ありで学習する公開研究も皆無であることが判明。
	4. **手術 OR での Ego-Exo view-consistent SSL**：A4 サーベイで手術 setting での先行例なしを確認（Exo＝Phase-2 の新規性）。D1/E2/E5 サーベイで、0.5 fps Ego ↔ 25 fps Exo の極端な fps 差をブリッジする手法が空白であり、Quattrocchi et al.（ECCV 2024）の exo→ego 蒸留が最も近い前例であることが特定された。
	5. **Segmentation マスクからの hand-tool 関係疑似ラベル自動生成**：B8 サーベイで先行例がほぼないことを確認（関係結合＝Phase-2 関連）。B7 サーベイで、検出マスクから interaction triplet を自動生成する surgical HOI 論文も未発表であることが裏付けられた。
	6. **hand-tool-guided MAE**：E3 サーベイで object-centric SSL × masked modeling の交差領域に先行例なしを確認。
	7. **EgoSurgery-Phase に対する長距離時系列モデルの未ベンチマーク**：D2/C3 サーベイで、Surgformer・LoViT・SR-Mamba・SKiT・MuST・HID-SSM の EgoSurgery-Phase 数値が未発表であり、これらの初ベンチマーク自体が明確な publishable 貢献となることを確認。
	8. **0.5 fps 低 fps × 異種マルチタスクでの長尾協調学習**：F1 サーベイで、検出 + セグメンテーション + 長距離時系列という異種マルチタスクの per-task 長尾協調学習、および低 fps 動画での Copy-Paste/Mixup 時系列一貫性が未開拓であることを確認。
	9. **surgical phase をトリガとした検出ヘッドへの query 条件付け**：C2 サーベイで、外部 phase token を Mask DINO / Mask2Former decoder に注入する研究例が MICCAI 2023–2025 範囲で発見できず、§4.6 の双方向補完が defensible な novelty であることを裏付け。
	10. **外部 detector の object token 列を SSM/Mamba に流す設計**：C4 サーベイで、SlotSSMs（NeurIPS 2024）以外に slot×Mamba の直接結合例がなく、「検出器出力 token 列を後段 Mamba で処理」する分離型設計は surgical も general video も未報告であり、C3-C4 結合がそれ自体論文の story になりうることを確認。
	11. **検出+工程+関係を三位一体で評価する手術ベンチマークの不在と Δ 指標の未標準化**：G4 サーベイで、open surgery で検出+工程+関係を同一データセットで評価するベンチマークが存在せず、SAR-RARP50/GraSP/PhaKIR 等が multi-task \> single-task を定性的に述べるのみで Δ（タスク結合の効果）指標を形式化した例がないことを確認—§7.1 の Δ 指標はモデルだけでなくベンチマーク方法論としても貢献となりうる。
	**実装・手法選定の横断的推奨（22 サーベイ統合版）**：
	- 空間 backbone：**DINOv2 ViT-L/14-with-registers** を主軸採用として確定（C1/E2/E3/B1 共通推奨）。register token で artifact patch を除去し形状類似ペア識別を改善。DINOv3 distilled 重みは公開揃い次第 ablation に追加。Stage A 必須 ablation として DINOv2 vs SurgeNetXL vs EndoViT vs Swin-L の backbone 比較表を作成（C1）。
	- PEFT：MTLoRA を plain ViT 用に porting し DoRA で強化、VeRA は head 増殖時に検討（C1/E2/C6）。heavy full fine-tuning は LIFT の知見に基づき回避（F1）。
	- 検出ヘッド：**Mask DINO + Learnable Query Proposal Distillation**（B1/B2 推奨）。SurgicalSAM の Contrastive Prototype Head を分類ヘッドに移植（形状類似ペア対策、B2）。VarifocalNet を baseline として必ず並走（EgoSurgery-Tool 実 SOTA、B2）。C2 サーベイでも query-based 統合ヘッドの妥当性が裏付けられ（object token 共有・時系列接続容易性・phase 条件付け適性）、Co-DETR を長尾対照候補、VFNet+Mask2Former 完全分離ヘッドを撤退候補とする。Phase→Detection 注入は STEP B で FiLM（§4.6 primary）vs Mask DINO decoder cross-attention（C2 推奨）を比較。
	- セグメンテーションヘッド：第 1 ライン **DINOv2 + EoMT decoder**、第 2 ライン DINOv2 + ViT-Adapter + Mask2Former（公式 SOTA 再現）、第 3 ライン Mask DINO、補助 SAM 2（B4 推奨）。
	- 手検出（S2）：own/other × L/R の 4 クラスに Mask DINO hand head を拡張、RoHan の Artificial Gloves augmentation + iterative 半教師ドメイン適応を再現。手姿勢推定は S3 以降に延期（B3）。
	- 時系列モデル：TeCNO をベースライン、SR-Mamba / SPRMamba / HID-SSM を SSM 系候補、SKiT を online 上限・低計算、Surgformer を offline 上限（B5/C3/D2 推奨）。object-centric token + Mamba の組合せ自体が論文の story（C3）。常に causal 版と bidirectional 版を並行訓練・評価（D2）。
	- 物体中心表現（object token 抽出）：Mask DINO object query + ROI Align/mask pooling を主トークン、DINOv2 上の VideoSAURv2/SlotContrast 風 unsupervised slot を ablation 対照・scene slot 補完・弱教師事前学習として併走。時系列化は SlotSSMs 風 block-diagonal Mamba を第1推奨、Slot-BERT 風 bidirectional masked Transformer を第2推奨、SlotContrast の object-level temporal contrastive loss を補助損失に併用（C4 推奨）。
	- HOI / 関係モジュール：Mask DINO query をノードとする two-stage GNN（PViC の cross-attention + SSG-Com/MCIT-IG の bipartite graph + hand-identity ノード）、HODN の stop-gradient で関係損失（Phase-2）が検出側（結合効果①）を汚染しないよう保護（B7/B8 推奨）。
	- MTL 最適化：FAMO + DB-MTL 対数変換、GCond の勾配蓄積、LibMTL の Δp 監視（C6 推奨）。
	- SSL 事前学習：VideoMAE v2 + hand-tool-guided MAE、Exo encoder は Hiera-B（VideoMAE V2 + Endo-FM warm-start）、Ego encoder は EgoVLPv2 初期化（E3/D1 推奨）。
	- 半教師あり：Stage C で Quattrocchi 方式の逆方向適用（Ego→Exo 蒸留）、Stage D で Consistent-Teacher（検出）+ SemiVT-Surge（phase）+ Polite Teacher（分割）統合（E5 推奨）。
	- クラス不均衡：post-hoc Logit Adjustment（全分類ヘッド）+ Seesaw Loss（p=0.8, q=2.0）+ RFS（t=0.001）+ Simple Copy-Paste + Balanced Softmax（工程ヘッド）+ Decoupled cRT（F1 推奨）。
	- Stage C 蒸留：AE2 / AlignEgoExo の temporal-alignment objective を plain L2 feature distillation の代わりに使用（E2/E5 推奨）。
	- 実装基盤：LibMTL（MTL）、microsoft/SoftTeacher + Adamdad/ConsistentTeacher + LiheYoung/UniMatch + IntraSurge/SemiVT-Surge（半教師あり）、IDEA-Research/MaskDINO・martius-lab/slotcontrast・PCASOlab/Xslot（検出・slot）（C6/E5/C2/C4 推奨）。
	- 評価ベンチマーク：EgoSurgery-\{Phase, Tool, HTS\} を主ベンチマークとして確定し、PhaKIR・GraSP・CholecT45・EgoExOR を転移・外部妥当性検証用に追加。Δ mAP（per-class、AP_rare/AP_common 分割）+ Δ macro-F1/Jaccard/Edit/Segmental F1@\{10,25,50\} を主報告指標とし、形状類似 sub-confusion matrix と Phase-conditional AP を Supplementary に、leave-one-surgeon-out + paired bootstrap 信頼区間を必須とする（G4 推奨）。
## 12. 直近のマイルストーン(各 M で検証する仮説を明示) {toggle="true"}
	**〔2026/05/21 追記：mask / hand-tool アノテーション不在の制約を反映〕** M1〜M5 の主経路は §0.1 Phase-0（bbox）で完結するよう設計する。M1 の mask baseline（Stage A1）と M3 の関係モジュール部分は Phase-1（mask 入手で起動）に依存する。mask が M2 期間内に入手できない場合、M1〜M5 は Phase-0 部分（bbox 検出・工程認識・結合効果①②・D-A/D-B）のみで達成・論文化できる。
	- **M1**:Stage A0 完了 ― EgoSurgery-Tool で再現性のある **bbox 検出ベースライン**(DINOv2 ViT-L/14-with-registers + Mask DINO box ブランチ)を確立。**backbone 比較 ablation（DINOv2 vs SurgeNetXL vs EndoViT vs Swin-L）をここで実施**し、**検出単独基準 S0-frozen「術具検出単独モデル（bbox 版）」の数値を確定**(結合効果①検証のための分母①)。mask 入手済みなら Stage A1（instance segmentation）を併して実施する。
	- **M2**:Stage A の出力に **Phase head(TeCNO ベース、global feature 入力)** を直結し、9 クラス工程認識の baseline を取得。**ここで工程単独基準 S4「工程認識単独モデル」の数値を確定**(結合効果②検証のための分母②)。bbox だけで実行可能。
	- **M3**:**双方向フィードバック(Phase ⇄ Detection)** を追加し、object-centric な工程認識+検出補正の効果を ablation で評価。**結合効果①②の一次検証ポイント**(Δ mAP と Δ Phase F1 をここで初めて測定)。**関係モジュールによる検証は Phase-2 に属し、mask 入手で起動する**（mask 未入手の場合 M3 は結合効果①②の一次検証までをスコープとする）。
	- **M4**:Stage B(Exo SSL)と Stage C(Ego–Exo 蒸留)を導入し、Ego 単独推論精度の改善幅を確認。**Exo（Phase-2）の主検証ポイント**:view-consistent SSL によって動作・時間表現が獲得されたかを Δ mAP・Δ Phase F1 の追加改善幅および工程境界周辺の予測安定性で評価する。bbox 主経路で実行可能。
	- **M5**:Stage D で統合 fine-tuning、最終評価。**結合効果①②（および mask 入手済みなら関係結合）の最終検証**を行い、動作ラベル導入の要否を判断する。
	### 12.1 詳細検証ロードマップ(STEP 0–D)
	M1〜M5 のマイルストーンを 10 ステップに細分化し、各ステップで**動かす軸を 1 本に絞る**ことで、結合効果①②（および Phase-2 の関係・Exo）を独立に検証可能にする実験順序。各ステップは M1〜M5 と多対多に対応する(下表「対応 M」列参照)。
	**〔2026/05/21 再編：mask / hand-tool アノテーション不在の制約を反映〕** 全 STEP（S0-frozen〜最終評価）を §0.1 の 2 フェーズに対応させ、**Phase-0 主経路を S0-frozen→S2→S3→S4→STEP B→STEP C→STEP D（最終評価）** とする（S2 の手検出は bbox で導入）。mask を要する mask 化・関係モジュール（旧 S1・関係）は **Phase-2（mask / hand-tool アノテーション入手で起動する条件付き拡張）に格下げ**する。Phase-0 主経路は bbox + Phase ラベルだけで 結合効果①②・D-A・D-B を検証でき、mask が M2 期間内に入手できなくても研究と論文が成立する。Phase-2 は mask 入手時点で主経路に挿入する（mask 化は S0-frozen の後、関係モジュールは結合効果①検証の後に対応）。
	#### 検証軸の凡例
	- **タスク**:`Tool`(術具検出のみ) / `Tool+Hand`(手検出を追加) / `Tool+Hand+Phase`(工程認識を追加)
	- **空間**:`bbox` / `mask`（mask は Phase-1 条件付き）
	- **時系列**:`frame`(フレーム単位の独立予測) / `短期`(数秒〜十数秒の clip) / `長距離`(分〜数十分の sequence)
	- **方向性**:`単方向`(detection 教師あり学習のみ、Phase head 無し) / `Det→Phase`(object token を Phase head へ、Phase 補助損失追加) / `Phase→Det`(Phase embedding を detection head へ FiLM / cross-attention で注入) / `双方向`(両経路 on)
	- **関係**:`無` / `有`(hand-tool graph による grasp / near-contact / handover / two-hand manipulation の同時推定、Phase-1 条件付き)
	- **視点**:`Ego` / `Ego+Exo`(Exo は view-consistent SSL と teacher-student 蒸留のみ、推論時 Ego only)
	- **フェーズ**:`Phase-0`（bbox、現時点で全面実行可能、主経路） / `Phase-1`（mask / hand-tool アノテーション入手で起動する条件付き）
	#### 全体マッピング(全 STEP × 軸 × 対応 M)
	太字は「直前ステップから動かす軸」。**フェーズ列**は §0.1 の 2 フェーズ対応を示す。
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>タスク</td>
<td>空間</td>
<td>時系列</td>
<td>方向性</td>
<td>関係</td>
<td>視点</td>
<td>フェーズ</td>
<td>検証する仮説</td>
<td>対応 M</td>
<td>実行サーバー</td>
</tr>
<tr>
<td>**S0-frozen**</td>
<td>Tool</td>
<td>bbox</td>
<td>frame</td>
<td>単方向</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>§2.5 (a) 分母①(S0-frozen)</td>
<td>M1 前段</td>
<td>**6000 Ada ×1**（Δ 基準点）</td>
</tr>
<tr>
<td>**【Phase-2】mask 化**</td>
<td>Tool</td>
<td>**mask**</td>
<td>frame</td>
<td>単方向</td>
<td>無</td>
<td>Ego</td>
<td>**Phase-1**</td>
<td>—(基盤整備、mask 入手で起動)</td>
<td>M1</td>
<td>A6000 ×1〜2（派生実験）</td>
</tr>
<tr>
<td>**S2**</td>
<td>**Tool+Hand**</td>
<td>bbox</td>
<td>frame</td>
<td>単方向</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>—(基盤整備)</td>
<td>M1</td>
<td>A6000 ×1（基盤整備）</td>
</tr>
<tr>
<td>**S3**</td>
<td>**Tool+Hand+Phase**</td>
<td>bbox</td>
<td>frame</td>
<td>**Det→Phase(弱)**</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>—(パイプライン確認)</td>
<td>M2 前段</td>
<td>A6000 ×1（パイプライン確認）</td>
</tr>
<tr>
<td>**S4**</td>
<td>Tool+Hand+Phase</td>
<td>bbox</td>
<td>**長距離**</td>
<td>Det→Phase(global feature 入力)</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>§2.5 (b) 分母②(S4)</td>
<td>M2 後段</td>
<td>**6000 Ada ×1**（Δ 基準点）/ 第 2 波は A6000</td>
</tr>
<tr>
<td>**【STEP B】②**</td>
<td>Tool+Hand+Phase</td>
<td>bbox</td>
<td>長距離</td>
<td>**Det→Phase(object token 入力)**</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>**結合効果②一次検証**</td>
<td>M3 前半</td>
<td>**6000 Ada ×1**（Δ 基準点）</td>
</tr>
<tr>
<td>**【STEP B】①**</td>
<td>Tool+Hand+Phase</td>
<td>bbox</td>
<td>長距離</td>
<td>**双方向**</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>**結合効果①一次検証**</td>
<td>M3 中盤</td>
<td>**6000 Ada ×1**（Δ 基準点）</td>
</tr>
<tr>
<td>**【Phase-2】関係**</td>
<td>Tool+Hand+Phase</td>
<td>**mask**</td>
<td>長距離</td>
<td>双方向</td>
<td>**有**</td>
<td>Ego</td>
<td>**Phase-1**</td>
<td>**関係結合の検証**（mask / hand-tool 入手で起動）</td>
<td>M3 後半</td>
<td>A6000 ×1〜2（Phase-1 派生）</td>
</tr>
<tr>
<td>**【Phase-2】Exo 診断**</td>
<td>—</td>
<td>—</td>
<td>—</td>
<td>—</td>
<td>—</td>
<td>Ego+Exo</td>
<td>Phase-0</td>
<td>Exo 視点多様性の予備診断</td>
<td>M4 前段</td>
<td>A5000 ×2〜3（少量 Exo 診断）</td>
</tr>
<tr>
<td>**【Phase-2】Exo**</td>
<td>Tool+Hand+Phase</td>
<td>bbox</td>
<td>長距離 + Exo 高 fps</td>
<td>双方向</td>
<td>無</td>
<td>**Ego+Exo**</td>
<td>Phase-0</td>
<td>**Exo の検証**</td>
<td>M4</td>
<td>**A5000 ×5 DDP**（SSL）+ 6000 Ada（Ego fine-tune）</td>
</tr>
<tr>
<td>**【STEP D】最終**</td>
<td>Tool+Hand+Phase</td>
<td>bbox（mask 入手時は + mask）</td>
<td>長距離 + Exo 高 fps</td>
<td>双方向</td>
<td>mask 入手時 有</td>
<td>Ego+Exo</td>
<td>Phase-0（+ 入手時 Phase-1）</td>
<td>**結合効果①②の最終検証（mask 入手時は関係結合も）**</td>
<td>M5</td>
<td>**6000 Ada ×1**（最終 Δ）+ A6000（ablation 並行）</td>
</tr>
	</table>
	#### STEP 別の実行詳細（実行手順の正本は §13）
	各ステップの具体的な学習設定・完了判定・失敗時対応・実行サーバーは **§13（実験実行手順書）を正本**とする。ここでは STEP 構造と単一タスク基準の位置づけのみ示す。
	- **STEP 0（土台）**：eval recipe 一本化＋凍結源 backbone 確定（暫定 Relation-DETR、mAP 0.730）。§13.2。
	- **STEP A（単一タスク基準）**：S0-frozen（検出単独＝§2.5(a) 分母①）／S2 手検出（検出タスク内）／S3 Phase head パイプライン接続／S4（工程単独＝§2.5(b) 分母②、global feature 入力）。比較の三角形の分母をここで確定。§13.2。
	- **STEP B（既存結合）**：結合効果②（object token→工程、対 S4）→ 結合効果①（工程→検出 双方向、対 S0-frozen）を 6 手法・4 層で実装し Δ を測定。§13.3。
	- **STEP C（要因分析）**：per-class／工程境界／negative transfer／タスク自信の相補性。§13.3。
	- **STEP D（仮説）／最終評価**：仮説プールから観察への解を選び比較群へ戻す。Stage D 統合 fine-tuning、全 ablation（§8.1）、転移検証（PhaKIR・CholecT45・EgoExOR）、leave-one-surgeon-out / paired bootstrap。§13.3。
	- **Phase-2（mask / Exo 入手で起動・条件付き）**：mask 化・関係モジュール（mask 依存）、Exo 予備診断・Exo 多視点導入。未入手なら §2.6 二段構え（結合効果①②・D-A・D-B）で論文化。§13.4。
	- 各 STEP の知見・失敗モード（S2 catastrophic forgetting・S3 class weights 崩壊等）は §14・§15 に、長尾対策は §3.3・§8.2 に保持。
	#### 検証順序の依存関係(なぜこの順序か)
	- **mask 化は Phase-2 条件付き(§0.1)**:mask は関係モジュール（Phase-2）の semantic prior として必要。Phase-0 主経路では S0-frozen→S2 を直行し、mask 入手時点で mask 化を S0-frozen の後に挿入する。挿入する際は S2 より前（空間化先、手検出後）とし、S2 の結論が mask 化の差分に汚染されないよう同一 backbone で再学習する。
	- **S4 → STEP B(長距離先、Det→Phase 切替後)**:Phase は本質的に時系列タスクであり、frame 単独で結合効果②を検証しても意味が無い。長距離時系列を共通基盤として先に確立する。
	- **STEP B 内(Det→Phase 先、Phase→Det 後)**:Det → Phase は片側の信号が弱くても破綻しにくいが、Phase → Det は Phase が未収束だと検出を退化させる(§4.6 の gradient 制御の理由)。先に Phase を安定化させる。
	- **関係モジュール（Phase-2）を STEP B 後に**:関係モジュールは結合効果①②を増幅する仮説なので、まず素の結合効果①②を測ってから関係を入れる。先に入れると増幅効果が本来の効果と分離できない。
	- **Exo（Phase-2）を最後に**:Exo SSL は上限引き上げ仮説。素の Ego マルチタスク（結合効果①②）が動いていることを確認してから、Exo の上積みを評価する。
	#### 全体注意事項
	- **共通設定の厳格化**:全 STEP（S0-frozen〜最終評価）で `seed = 42`、optimizer、scheduler、augmentation、batch size、**GPU 構成（単一 GPU or DDP 枚数）** を完全に揃える。変える場合は明示的に注釈を付ける。**DDP 使用時は、同一 Δ 比較群内の全モデルを同一 GPU 構成で揃えること、effective batch size を eval_recipe に記録すること、lr スケーリングの適用有無を config に明記することが必須（§8.0 条件 (4)(5)(6)、2026/05/25 追記）**。
	- **基準点(S0-frozen, S4)の信頼性**:Δ の妥当性はこれらに依存するため、**複数 seed(最低 3 seeds)で variance を取り、平均±標準偏差を併記**する。Δ が 1σ 以内であれば改善と主張しない。ここでの 1σ は「同一 eval recipe での 3-seed std」であり、recipe 差由来の variance は含めない（§15.4 C）。**さらに S0-frozen は §15.4 A の strict 3 条件（公式 split / locked-down test_cfg / metrics.json の eval_recipe 一致）を満たさなければ Δ 基準点として使用できない〔2026/05/24 追記、§15 と整合〕**。旧 split / 旧 test_cfg で測定した数値（§15.5 退避済み）は Δ 基準点に使えない。
	- **計算コストの見積もりと GPU 割り当て**〔2026/05/21 更新：旧記述の A100 前提を実環境に改訂〕:全 STEP を 3 seeds で回すと最小 30 実験、ablation 軸と組み合わせると数十実験規模。実行環境は RTX 6000 Ada（48GB）/ RTX A6000×2（48GB）/ RTX A5000×5（24GB）/ Quadro RTX 8000×2（48GB）。**Δ の基準点に影響する本実験（S0-frozen・S4 第 1 波・STEP B）は RTX 6000 Ada に固定**し、ablation・第 2 波ベンチマーク・転移検証は A6000×2 に、Exo SSL（Phase-2）は A5000×5 を DDP 専有で割り当てる。Quadro RTX 8000 は bf16 非対応のため軽量実験・推論評価・前処理専用とする。**Exo SSL（Phase-2）は §12.16 が想定する 4×A100 80GB×3 週間の環境には届かないため、Exo を全 25 fps ではなく Ego 同期窓内で 5 fps 程度にサブサンプリングして計算量を圧縮する**ことを前提とする。**S4 終了時点で実験管理パイプライン(Hydra + W&B、§8)を完全に整備**しておく。
	- **早期打ち切り基準**:
		- 結合効果②（STEP B）で Δ Phase F1 ≤ 0 → object token 品質を疑い S2 / S0-frozen に戻る
		- 結合効果①（STEP B）で Δ mAP ≤ 0 → gradient 制御と loss weight を見直す
		- 仮説検証の早い段階で破綻が見えれば、無駄な後段実験を避けられる
	- **追加で回せる ablation セル**:双方向（結合効果①）と関係有（Phase-2）は config で個別 on/off できる構造のため、必要に応じて以下のセルも回せる。優先度は低いが、各仮説が機能する条件を絞り込むのに有用。
		- (双方向無 × 関係有):関係モジュールが片方向だけで効くか
		- (Det→Phase × 関係有):結合効果② + 関係結合 のみの組み合わせ(結合効果① 抜き)
		- (Phase→Det 単独 × 関係無):結合効果① のみの最小構成
	- **動作ラベル導入判断のタイミング**:STEP B（結合効果①②）の結果が想定を下回った場合、§9 P-1 の動作ラベル追加判断を **最終評価まで待たずに前倒し** する選択肢を持つ。具体的には、Phase 認識精度が Dissection / Closure 内部で頭打ちなら、より細粒度の動作ラベルが必要というシグナル。
---
## 13. 実験実行手順書（STEP 0→D・CVPR 投稿まで） {toggle="true"}
	本セクションは §12（マイルストーン＋STEP 0–D ロードマップ）・§8（実験運用）・§10/§11（サーベイ知見）を**実行レベルの手順**に翻訳した、実験実行の**正本**である。§12 が「何を・どの順序で・何で測るか」を定めるのに対し、本 §13 は「実際に手を動かす順序と各 STEP の完了判定」を定める。CVPR のようなトップティア国際会議への投稿を前提とする。
	### 13.0 本手順書の位置づけと前提
	- **3 つの最重要原則**：(1) Δ 指標の信頼性がすべての前提であり、S0-frozen / S4 の単一タスク基準点が汚染されると全 Δ が無効化される（§10.1 共通設定の厳格化・比較の三角形）。(2) §2.6 の二段構え（結合効果①②の Δ が非有意でも D-A・D-B で論文成立）を常に意識し、両輪を同時に育てる。(3) Phase-0 主経路（STEP 0→A→B→C→D）を死守し、関係結合（mask 依存）・Exo は **Phase-2** として mask / Exo 入手で起動する条件付きとする。
	- **データ可用性の前提**：mask / hand-tool アノテーションは M2 期間内（数ヶ月後）に入手見込み（§0.1）。Phase-0 主経路（STEP 0–D）は mask を一切要さないため、最初の数ヶ月を Phase-0 に充て、その完了が mask 入手と重なるよう工程を組む。
	- **計算環境の前提〔2026/05/25 更新：§8.0 を最優先規範として明記〕**：RTX 6000 Ada（48GB、Ada 世代、Δ 基準点専用）/ RTX A6000×2（48GB、ablation・第 2 波・転移検証）/ RTX A5000×5（24GB、Exo SSL を DDP 専有）/ Quadro RTX 8000×2（48GB、bf16 非対応のため軽量実験・推論・前処理専用）。STEP 0–D の本実験は原則 RTX 6000 Ada に統一し、世代混在による数値再現性の崩れを避ける（§4.2・§8.0 と整合）。**ただしサーバー割り当ての運用ルールは §8.0「サーバー割り当ての運用原則」を最優先の規範とする**。とりわけ §8.0 の「暫定運用：RTX 6000 Ada 未配備期間」の規定により、RTX 6000 Ada が未配備の期間は Δ 基準点学習（S0-frozen・S4 第 1 波・STEP B の結合手法等）を bengio（RTX A6000×2）上で実行することを暫定的に許容する。暫定運用にあたっては §8.0 が定める条件——同一の Δ 比較群は必ず同一サーバー上で揃えて測定する、metrics.json の eval_recipe.server_name と各実験フォルダの server.txt にサーバー名を記録する、RTX 6000 Ada 配備後に Δ 基準点を再測定する必要が生じうることを §14 に明記する、DDP 使用時は GPU 構成を比較群内で揃え effective batch size と lr スケーリングを記録する——をすべて満たすこと。
	### 13.1 STEP 前の基盤整備（STEP 0 開始の 2〜3 週間前）
	- **I-1 計算環境とデータアクセスの確定**：(a) GPU 時間を確認し「3 seeds × 数十実験」が収まるか逆算、収まらなければ §13.7 の 3 層分類で削る計画を先に立てる。(b) 転移検証用ベンチマーク（PhaKIR・GraSP・CholecT45・EgoExOR）のデータアクセス認証申請を**即日開始**（§9 #8）。(c) mask / hand-tool アノテーションの入手源と見込み時期を指導教員に確認し §3.1 に追記。
	- **I-2 実験管理パイプラインの構築**（§8 準拠、STEP 0 開始前に前倒し完成）：Hydra で `model/data/train/stage` の 4 軸 config group、結合機構（§4.6）の on/off をフラグ化。W&B で全 Stage を同一 project・Stage 別 group、LibMTL の Δp 指標を統合。実験 ID は `timestamp_confighash`。`seed=42`・`deterministic=True`・`cudnn.benchmark=False` を固定。**CVPR 用に、per-class AP・confusion matrix・Δ 計算を自動で metrics.json に吐くスクリプトをこの段階で実装**（最終評価で Table I/II/Supplementary を手作業で作ると破綻するため）。
	- **I-3 サーベイの最終確認**：§10.1 の実施順序表に従い、STEP 0–A 開始前に必要な高優先細目（A1, A2, B1, B2, B3, B4, C1, C2, F1, G4）が §11/§12 で網羅済みであることを確認。
	- **完了判定**：ダミーの 1 エポック学習を流し、W&B に per-class 指標と Δ 計算枠が自動記録されることを確認できた時点。
	### 13.2 STEP 0（土台）＋ STEP A（単一タスク基準）— Phase-0 主経路
	#### STEP 0：eval recipe 一本化＋凍結源 backbone の確定（最優先ブロッカー）
	Δ のすべての前提を固める（§9 N1/N2・§8.-1）。
	- **STEP 0a eval recipe の公式一本化**：1 モデルを 2 系統の recipe（locked-down test_cfg 系 / score_thr=0.0 系）で**再 eval して Δ_recipe を実測**（再学習不要）→ 公式 recipe を決定 → `build_eval_recipe` を一本化 → `DeltaCalculator` 保護を**検出・工程の両方**に適用する（§8.-1・§15.4）。これが済むまで結合の Δ 主張はしない。
	- **STEP 0b 凍結源 backbone の確定**：検出ベンチは実測完了済みで、**Relation-DETR が mAP 0.730（3-seed 平均 0.727・σ0.004・AP_rare 0.758）で 1 位**。これを凍結源 backbone の**暫定第一候補**とし、recipe 一本化後に S0-frozen / S4 / 結合手法が同一土台（比較の三角形）に載ることを確認して確定する（§4.2）。
	- **完了判定**：公式 recipe が文書化され、`DeltaCalculator` が検出・工程の両方で recipe 照合 → `InconsistentRecipeError` を送出する状態。凍結源 backbone が固定された状態。
	#### STEP A：単一タスク基準点の確立（比較の三角形の分母）
	- **S0-frozen 検出単独基準**【§2.5(a) 分母①・最も慎重に固める】：**実行サーバー：RTX 6000 Ada ×1（Δ 基準点専用）**。凍結 backbone ＋ 検出ヘッド（Mask DINO〔DINOv2 ViT-L/14-with-registers + ViT-Adapter〕・VarifocalNet・Co-DETR）を bbox-only で学習。Seesaw Loss（p=0.8, q=2.0）+ RFS（t=0.001）+ bbox-level Simple Copy-Paste + post-hoc Logit Adjustment を有効化。3 seeds で variance を取り平均±標準偏差を併記。per-class AP を全 15 クラス、稀少クラス（Skewer / Syringe）と形状類似ペア（Forceps / Tweezers / Needle Holders / Bipolar Forceps）の 4×4 sub-confusion matrix を可視化。RTX 6000 Ada で bf16 + 勾配チェックポイント実行。**完了判定**：凍結 backbone 上で検出単独の Δ 分母が安定確定すること（旧基準の VarifocalNet 公式 SOTA tool mAP 45.8 は参考値。現行の主基準は recipe 一本化後の DETR 系上位＝Relation-DETR 0.730、§16）。**判断ポイント #6**：Mask DINO vs Co-DETR を APr で比較し 3pt 以上差があれば以降を Co-DETR ベースに切替。
		- **DDP 2 GPU 運用の実装要件〔2026/05/25 追記〕**：RTX 6000 Ada 未配備期間は bengio（A6000 ×2）で DDP 2 GPU 実行を許容する（§8.0 暫定運用）。実装上の対応は以下の通り。
			- **(a) effective batch size の倍化**：DDP 2 GPU では per-GPU batch size を単一 GPU 時と同じまま保ち、effective batch size を 2 倍にする。例：単一 GPU で batch_size=2 だった場合、DDP 2 GPU では effective batch size = 4。これに伴い learning rate を線形スケーリング（lr × 2）する。スケーリングの適用と effective batch size は config と `eval_recipe` に明記する（§8.0 条件 (5)(6)）。
			- **(b) ****`MMDetTrainer`**** への DDP 対応**：`MMDetTrainer` に以下の機能を追加する。(i) `_build_eval_recipe()` に `gpu_count`（`torch.cuda.device_count()` または `WORLD_SIZE` 環境変数）と `effective_batch_size`（`gpu_count × per_gpu_batch_size`）を記録するフィールドを追加。(ii) DDP 学習時に `DistributedDataParallel` の初期化と `DistributedSampler` の設定を `setup()` で行う。(iii) 評価時は rank=0 のみで `_write_metrics` を実行し、重複書き込みを防止。(iv) `SyncBatchNorm` への変換は BN を使うモデル（ViT-Adapter 等）でのみ適用し、LayerNorm 主体の ViT では不要。
			- **(c) ****`run_s0.sh`**** の DDP 起動への書き換え**：単一 GPU 起動（`python tools/train.py ...`）を `torchrun --nproc_per_node=2 tools/train.py ...` に書き換える。各 seed ・各 detector の学習ブロックをすべて `torchrun` 経由で起動する。`MASTER_PORT` は seed/detector ごとにユニークな値を設定し、並列実行時のポート競合を回避する。例：`MASTER_PORT=$((29500 + seed_index * 3 + detector_index)) torchrun --nproc_per_node=2 tools/train.py model=vfnet seed=42 ...`。
			- **(d) 全モデル統一**：上記 (a)(b)(c) を VFNet・Mask DINO・Co-DETR の全モデルに同一に適用する。特定のモデルのみ単一 GPU、他のモデルは DDP という混在は禁止（§8.0 条件 (4)）。
	- **S2 手検出の追加（検出タスク内）**【Phase-0】：**実行サーバー：RTX A6000 ×1（基盤整備）**。Mask DINO の hand head を own/other × L/R の 4 クラスに拡張。RoHan の Artificial Gloves augmentation + iterative 半教師ドメイン適応を再現。視野位置事前分布を spatial Gaussian prior として注入。手姿勢推定（keypoint/MANO）は導入しない（§12.11）。**完了判定**：hand mAP \> 65、own/other accuracy \> 90%、L/R accuracy \> 95%、かつ術具 mAP が S0-frozen から劣化しない。
	- **S3 Phase head のパイプライン接続**【STEP A→B 橋渡し】：**実行サーバー：RTX A6000 ×1（パイプライン確認）**。検出出力に Phase head（frame-by-frame、弱ベースライン）を接続、方向性を Det→Phase 弱に。Phase 認識の絶対精度は評価しない（S4 まで保留）。**完了判定**：パイプライン動作、術具検出 Δ mAP が劣化しないこと。
	- **S4 工程単独基準（長距離時系列）**【§2.5(b) 分母②・D-B の中核、2 段階運用】：**実行サーバー：第 1 波（TeCNO・SR-Mamba）= RTX 6000 Ada ×1（Δ 基準点）、第 2 波（HID-SSM・SKiT・Surgformer 等）= RTX A6000 ×1〜2（D-B ベンチマーク拡充）**。第 1 波（必須）= TeCNO・SR-Mamba を causal/bidirectional 並行学習、Phase head 入力は画像 global feature（工程単独の分母）。第 2 波（S4 安定後）= HID-SSM 主軸に SKiT・Surgformer・SPRMamba を順次追加（D-B 貢献）。temporal smoothing・transition loss・phase order prior を正則化に。**完了判定**：Phase macro F1・Edit score・Segmental F1@\{10,25,50\}・Dissection/Closure 内部 F1 が安定取得。TeCNO が Jaccard 70% 未満なら Mamba 系へ即移行。**STEP A 終了時点で §13.1 I-2 のパイプラインが完全整備されていることを再確認**。
	### 13.3 STEP B（既存結合の比較群）＋ STEP C（要因分析）＋ STEP D（仮説）
	#### STEP B：既存結合の比較群（6 手法・4 層）の Δ 測定
	**実行サーバー：本実験 = RTX 6000 Ada ×1（Δ 基準点）、注入方式 ablation = RTX A6000 ×1〜2 で並行**。既存結合を **共有エンコーダ MTL → 片方向 pipeline → PAD-Net/MTI-Net 予測蒸留 → MT4MTL-KD/SSG-Com ドメイン SOTA** の順に実装し、各手法の Δ を同一土台（比較の三角形）で測る（§2.3・§8.1）。
	- **結合効果②（object-centric→工程）の検証**：Phase head 入力を global feature → object token（bbox 由来：ROI Align + bbox 位置 + クラス埋め込み、mask shape なし）に切替。3 段階比較（global feature 分母 S4 / unsupervised slot baseline / 結合手法）。**完了判定（成功条件）**：Δ Phase F1 = 結合 − S4 \> 0、global feature 分母に対し +5pt 以上。**早期打ち切り**：Δ Phase F1 ≤ 0 なら object token 品質を疑い S2 / S0-frozen に戻る。
	- **結合効果①（工程文脈→検出）の検証**：§4.6 の双方向化。primary 注入は cross-attention（Mask DINO decoder に c_phase トークン）、entropy gating 実装、gradient 制御（stop-gradient・loss weight ramp）。ablation 下限として FiLM も実装し、cross-attention vs FiLM vs SAK-style adapter bias を比較。**完了判定（成功条件）**：Δ mAP = 結合 − S0-frozen \> 0、稀少クラス・形状類似ペアで顕著。**早期打ち切り**：Δ mAP ≤ 0 なら gradient 制御と loss weight を見直す。
	- 損失重み付けは FAMO 第一候補 + DB-MTL（併用アドオン、§5 Stage D）。negative transfer を LibMTL Δp で監視（STEP C の入力）。
	#### STEP C：差の要因分析
	**実行サーバー：RTX A6000 ×1〜2（分析・可視化）**。STEP B の Δ がなぜ出た/出ないかを分析する（§8.1(3)）。
	- **per-class**：稀少クラス（Skewer / Syringe）・形状類似ペア（Forceps / Tweezers / Needle Holders）での Δ 分布。
	- **工程境界**：Dissection / Closure 境界周辺の Δ Phase F1・segmental F1@k。
	- **negative transfer**：LibMTL Δp で手法×タスクの負転移を特定。
	- **タスク自信の相補性**：検出・工程の予測エントロピーの相補関係（H-C の動機）。
	#### STEP D：観察から結合仮説（比較群へ戻して検証）
	**実行サーバー：本実験 = RTX 6000 Ada ×1、ablation = RTX A6000 ×1〜2**。STEP C の観察を「この観察への解」として仮説プール（H-C / H-A / H-H、§2.3）から選ぶ/作り直し、STEP B 比較群に「新手法」として戻して同一土台で Δ を測る。中核 ablation（§8.1：B-det / B-phase / B-dir / A7）と補助 ablation（損失重み付け 5 条件・長尾損失独立ベンチ等）を完走。統計処理は leave-one-surgeon-out または stratified k-fold + paired bootstrap を必須。**A7（D-A 検証）と D-B（第 2 波ベンチマーク）は Δ の成否に関わらず必ず完走する**。
	### 13.4 Phase-2（将来拡張）：関係結合・Exo 多視点〔mask / Exo 入手で起動・条件付き〕
	Phase-0（STEP 0–D）確立後、mask / Exo 入手で起動する条件付き拡張（§0.1・§9 P-2/P-3）。未入手なら本節をスキップし §2.6 二段構え（結合効果①②・D-A・D-B）で論文化する。
	- **【条件付き】関係結合（mask 入手で起動）**：**実行サーバー：RTX A6000 ×1〜2**。instance segmentation（旧 S1）= EoMT / Mask2Former / Mask DINO の 3 ライン比較 + SAM 2 補助。関係モジュール（Phase-2）= Mask DINO query をノードとする two-stage GNN、エッジ疑似ラベルは mask-IoU から自動生成、200 フレーム人手検証で 80% 以上担保。
	- **Exo 予備診断（撤退ライン第 1 段階）**：**実行サーバー：RTX A5000 ×2〜3**。少量 Exo サブセットで cross-view contrastive を試験学習し、視点不変性・時刻弁別性の 2 軸で表現品質を計測。信号が得られなければフル SSL の手前で Exo を「Phase label 弱教師転写のみ」に早期縮退（§9 P-3 第 1 段階）。
	- **Exo 多視点導入（最大の難所）**：**実行サーバー：Exo SSL = RTX A5000 ×5 DDP 専有（Exo を 5 fps 程度にサブサンプリング）、Ego fine-tuning および Δ 測定 = RTX 6000 Ada ×1**。Exo 単独 SSL（VideoMAE v2 + hand-tool-guided MAE + cross-view contrastive + temporal hard negative）・DINO/iBOT 継続事前学習（2% 未満の gain ならスキップ）・Ego–Exo 整合と蒸留（時間同期 contrastive + Phase 分布整合 KL + tool-set 弱整合 + Quattrocchi 式 2-level KD）。**branch-pruning 検証**：推論時に Exo 経路の重みを抜いて性能再測。**撤退ライン第 2 段階**：Δ の追加改善幅が 1σ 以内なら Exo を弱教師転写のみに縮退。
	### 13.5 評価結果の出力と CVPR 投稿
	- **報告フォーマット**（§7.1・§12）：各タスクで Table I（絶対スコア）+ Table II（Δ 表、paired bootstrap で有意差マーク）+ Supplementary（Phase-conditional AP heatmap・形状類似 sub-confusion matrix）。
	- **貢献の二段構え**（§2.6・§7.1）：Δ が有意なら結合効果①②（タスク結合の効果）を主貢献として前面に。Δ が 1σ 以内で非有意なら、(1) 単一タスク絶対精度 SOTA 更新、(2) D-A（object-centric token × block-diagonal SSM）、(3) D-B（EgoSurgery-Phase 初の長距離ベンチマーク）を方法論的貢献として主張。**A7（D-A 検証）と D-B（第 2 波ベンチマーク）は Δ の成否に関わらず必ず完走する**。
	### 13.6 標準スケジュール（CVPR 締め切り未定 → 標準 12〜14 か月想定）
	<table fit-page-width="true" header-row="true">
<tr>
<td>期間</td>
<td>フェーズ</td>
<td>ステップ</td>
<td>mask 状況</td>
</tr>
<tr>
<td>月 1</td>
<td>基盤整備</td>
<td>I-1〜I-3（環境・パイプライン・データ申請）</td>
<td>入手待ち</td>
</tr>
<tr>
<td>月 2〜3</td>
<td>Phase-0</td>
<td>S0-frozen（検出単独基準）</td>
<td>入手待ち</td>
</tr>
<tr>
<td>月 3〜4</td>
<td>Phase-0</td>
<td>S2（手検出）・S3（Phase 接続）</td>
<td>**この頃 mask 入手**</td>
</tr>
<tr>
<td>月 4〜6</td>
<td>Phase-0/1</td>
<td>S4（長距離時系列・D-B 第 1 波）+ S1（mask 化）を並行</td>
<td>入手済み</td>
</tr>
<tr>
<td>月 6〜8</td>
<td>中核検証</td>
<td>STEP B（結合効果②・①）</td>
<td>入手済み</td>
</tr>
<tr>
<td>月 8〜9</td>
<td>Phase-1</td>
<td>Phase-2（関係モジュール）</td>
<td>入手済み</td>
</tr>
<tr>
<td>月 9〜10</td>
<td>Exo 検証</td>
<td>Phase-2（Exo 予備診断・本検証）</td>
<td>—</td>
</tr>
<tr>
<td>月 10〜12</td>
<td>統合</td>
<td>STEP D（統合 fine-tuning・全 ablation・転移検証）</td>
<td>—</td>
</tr>
<tr>
<td>月 12〜14</td>
<td>執筆</td>
<td>評価結果出力・論文執筆・rebuttal 準備</td>
<td>—</td>
</tr>
	</table>
	mask 入手（月 3〜4）と STEP A の S0-frozen〜S3 完了がほぼ同期するため待ち時間ロスがほぼゼロになる。CVPR 締め切りが確定し次第この月割りを圧縮する（直近締め切りなら STEP B 完了 + D-B ベンチマークを必達ラインに絞る）。
	### 13.7 実験の 3 層分類（GPU 制約を反映）
	- **必達ライン（これがないと論文が成立しない）**：S0-frozen（検出単独基準。現行上位 Relation-DETR 0.730、旧 VFNet 45.8 は参考）、S4 第 1 波（TeCNO + SR-Mamba、causal/bidirectional）、STEP B（結合効果①②の一次検証）、ablation（B-det・B-phase・A7=D-A）、D-B 最小ベンチマーク（HID-SSM 追加）。→ RTX 6000 Ada で確実に回し切る。
	- **努力ライン（あると論文が強くなる）**：Phase-2 の関係結合（mask 入手後、instance seg・関係モジュール）、Phase-2 の Exo 検証、S4 第 2 波の残り（SKiT・Surgformer・SPRMamba）、片方向 vs 双方向 ablation（B-dir）、長尾損失独立ベンチマーク。→ A6000×2 と A5000×5 に振り分け。
	- **カットライン（GPU/時間が逼迫したら削る）**：Stage B′（\<2% gain ならスキップ）、補助 ablation の一部、転移検証の一部（PhaKIR 優先、CholecT45・EgoExOR は余力次第）。
	### 13.8 GPU 割り当て
	<table fit-page-width="true" header-row="true">
<tr>
<td>GPU</td>
<td>VRAM</td>
<td>世代</td>
<td>割り当て</td>
</tr>
<tr>
<td>RTX 6000 Ada</td>
<td>48GB</td>
<td>Ada Lovelace</td>
<td>**Δ 基準点専用**（S0-frozen・S4 第 1 波・STEP B）。最優先・本実験の主戦場</td>
</tr>
<tr>
<td>RTX A6000×2</td>
<td>48GB</td>
<td>Ampere</td>
<td>ablation・第 2 波ベンチマーク・転移検証（基準点に影響しない派生実験）を DDP で</td>
</tr>
<tr>
<td>RTX A5000×5</td>
<td>24GB</td>
<td>Ampere</td>
<td>Stage B-C の Exo SSL を DDP 専有。Exo は 5 fps 程度にサブサンプリング</td>
</tr>
<tr>
<td>Quadro RTX 8000×2</td>
<td>48GB</td>
<td>Turing</td>
<td>bf16 非対応のため軽量実験・推論評価・データ前処理専用。基準点学習には使わない</td>
</tr>
	</table>
	**運用原則**：Δ 基準点に影響する学習は世代の揃った単一 GPU モデル（RTX 6000 Ada）に固定し、§10.1「共通設定の厳格化」をハードウェアにも適用する。必達ライン（RTX 6000 Ada）と努力ライン以下（A6000/A5000）を物理的に分離することで GPU 待ちのボトルネックを緩和する。
---
## 14. 実験結果ログ（実行マシン別） {toggle="true"}
	本セクションは各実行マシンで得られた実験結果を記録する台帳である。Δ 基準点（§7.1）の正式値ではなく、各実行の実測値と位置づけを残す。
	### 実行マシン: RTX A6000 — egosurgery_multitask
	- GPU: NVIDIA RTX A6000 (48GB) ×1
	- torch / CUDA: 2.1.2+cu118 / システム nvcc 11.8 / Ubuntu 22.04
	- コード: egosurgery_multitask @ commit d1bcc8a（phase2 ブランチ）
	#### S0 — DDP 2 GPU 再実行予定（2026-05-25 方針決定）
	**⚠️ 方針変更**: 単一 GPU での VFNet 学習に時間がかかりすぎるため、**S0 全モデル（VFNet・Mask DINO・Co-DETR）を bengio の RTX A6000 ×2 DDP で統一して再実行する**方針に変更した。
	**変更の根拠**: §8.0 条件 (4)「同一 Δ 比較群内の全モデルを同一 GPU 構成で揃える」に基づき、VFNet のみ 2 GPU に切り替えることは不可。S0 全体を 2 GPU DDP で統一することで Δ の整合性を保つ。
	**実行条件**: §8.0 暫定運用の 6 条件すべてを満たすこと。特に (4) 全モデル同一 GPU 構成、(5) effective batch size を eval_recipe に記録、(6) lr スケーリングの選択を config に明記。公式 split × locked-down test_cfg を使用。
	**既存結果の扱い**: 進行中の単一 GPU 学習結果は、S0 内のモデル間で GPU 構成が揃わないため、Δ 基準点としては使用しない。DDP 2 GPU での再実行結果を正式な S0 基準点とする。
	**RTX 6000 Ada 配備後**: §8.0 条件 (3) に基づき、Ada 配備後に単一 GPU での S0 再測定を検討する。
	**証拠・トレーサビリティ**: experiments/_smoke_prior/ / experiments/baselines/_wrong_split_8_2_3/ / experiments/phase0/s2_00* / experiments/phase0/s3_00* / experiments/phase0/_failed_s3_weighted/ 、各フォルダの server.txt + metrics.json + git_commit.txt を参照。
---
## 15. Lessons Learned & 整合性検証規則 {toggle="true"}
	本節は S0 完走後に発覚した split 取り違えと評価条件不整合を契機に、Δ 評価方法論の前提条件を明文化したものである（2026-05-24 追加）。研究計画の他節（§2.5 / §7.1 / §10.1 / §13.1 / §13.6 / §13.8）への波及は §15.4 を参照。
	### 15.1 失敗事象 #1：データ split の取り違え（最重要）
	- **症状**: S0 (VarifocalNet seed42) test mAP = **0.388**、公式 SOTA 0.458 まで -7pt。当初は recipe（schedule・augmentation・長尾対策）の差と仮定していた。
	- **発覚契機**: 論文 §2.1 と Table 3a の data split サイズを手元の `instances_*.json` と突き合わせた結果、train/val が論文と異なることを発見。
	- **根本原因**:
		- `data/splits/ego_train.txt` が **8 videos** (01,02,03,06,08,11,12,13)、`ego_val.txt` が **2 videos** (14,15)、`ego_test.txt` が 3 videos (04,05,07) になっていた。
		- 論文公式は **train=10 videos** (上記 8 + 14, 15) / **val=2 videos** (09, 10) / **test=3 videos** (04, 05, 07)。
		- ディスク (`data/raw/ego/{train,val,test}/`) と hand 注釈 (`hand/*.json`) は論文準拠だが、tool 注釈 (`instances_*.json`) のみ独自再分割していた。
		- 結果として **train が 23% 不足**（9,657 → 7,427 imgs、32,272 → 21,988 anns）、**val は別動画（14,15 vs 09,10）** で論文比較不能。
	- **データ証拠**: 公式 tool 注釈は `data/annotations/egosurgery_tool/tool/{train,val,test}.json` に存在していた（image=9657/1515/4265、annotation=32272/4707/12673 で論文 Table 3a と完全一致）。前チームはこれを参照せず独自再分割していた。
	- **影響**: 旧 split で学習した S0 6 実験（_wrong_split_8_2_3 へ退避）は Δ 基準点として使用不可。
	### 15.2 失敗事象 #2：test_cfg score_thr が論文と不一致
	- **症状**: mmdet VFNet の `test_cfg.score_thr = 0.05`（mmdet detector default）。論文 §3.1 末尾は `confidence = 10^-8` を使用。
	- **実測影響**: 0.388 → 0.389（+0.1pt のみ）。`nms_pre=1000 → NMS → max_per_img=100` で top-100 cap が支配的なため。
	- **真の効果は ****`max_per_img`**** 拡張**: dense シーン（11-15 instances/img × 506 枚、論文 Table 2）で 100 cap が低 confidence True Positive を切る可能性。
	- **対処**: G1 で `score_thr=1e-8, max_per_img=300, nms_pre=3000` を全 detector で強制統一。
	### 15.3 再発防止策（G1-G3、コード反映済み）
	- **G1: ****`MMDetTrainer._build_mmdet_cfg`**** で test_cfg を locked-down 上書き**
		- 全 detector・全 stage で `score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6` を強制。
		- detector ごとの mmdet default 差が Δ 計算に混入することを防ぐ。
	- **G2: ****`scripts/preprocess_ego.py`**** に論文 Table 3a 整合性 assertion**
		- 生成された `instances_*.json` の (image, annotation, video) 数が論文値と一致しなければ `AssertionError`。
		- `data/splits/ego_*.txt` も論文準拠（train=10, val=\{09,10\}, test=\{04,05,07\}）に修正済み。
	- **G3: ****`metrics.json`**** に ****`eval_recipe`**** field を併記**
		- `test_cfg` 全項目 + train/val/test の image・annotation 数を記録。
		- Δ 計算時に異なる recipe での比較を自動拒否できる土台。
	### 15.4 研究計画への反映（A〜F）
	- **A. §2.5(a) S0 基準点定義の strict 化**
		- S0 は以下 3 条件すべてを満たすときに正当な Δ 基準点として採用する:
			1. データ split が EgoSurgery-Tool 公式 (train 9657 / val 1515 / test 4265)
			2. test_cfg が G1 の locked-down 値
			3. metrics.json の `eval_recipe` がこれらと一致
		- 既存 §2.5 の「成功条件 (a)(b)(c)」を補強する位置づけ。
	- **B. §7.1 Δ 計算の前提条件**
		- Δ は **同一 eval recipe で測定された値同士でのみ意味を持つ**。`DeltaCalculator` は両 metrics.json の `eval_recipe` を比較し、不一致時は例外（実装予定: pipeline_implementation_[prompt.md](http://prompt.md) §2.7 拡張）。
		- 旧 split で測った S0 (mAP 0.278 val / 0.388 test) は基準点に使えない。
	- **C. §10.1「Δ が 1σ 以内なら改善と主張しない」の補足**
		- ここでいう 1σ は **同一 eval recipe での 3-seed std**。recipe 差由来の variance は 1σ に含めない。
		- recipe を変えるアブレーション（例: `score_thr × max_per_img` sensitivity）は §3 で **別表として分離**して報告する。
	- **D. §13.6 標準スケジュール / §3 実験テーブル footnote**
		- 論文化を想定した全実験表に、locked-down recipe（score_thr / max_per_img / nms / split sizes）を脚注で明記する。reviewer が Δ improvement の正当性を検証可能にする。
	- **E. §13.1 / §13.8 Reproducibility 厳格化**
		- `data/splits/ego_*.txt` を論文準拠で git 管理（変更禁止）。
		- `preprocess_ego.py` の assert_paper_split が CI / 起動時チェックの最後の砦。
		- `MMDetTrainer` が test_cfg を locked-down で上書きする運用を明文化。
	- **F. 本節（§15）の常設化**
		- 今後の整合性関連の発見・対処は §15 に蓄積する。研究 integrity を honest に開示する位置として論文 supplementary に展開可能。
	### 15.5 過去実験の扱い
	- 旧 split / 旧 test_cfg で測定した数値は **Δ 基準点として使用不可**。
	- 退避場所:
		- `experiments/baselines/_wrong_split_8_2_3/`（S0 6 実験、旧 split）
		- `experiments/phase0/_failed_s3_weighted/`（S3 初回・class weights 不適切）
	- 各失敗実験は scientific record として保存（捏造でなく実測値）。論文では "prior measurement" として明示するか、撤回する。
	### 15.6 今後の運用ルール
	- 全新規実験で `MMDetTrainer`（test_cfg locked-down）+ `assert_paper_split` + `eval_recipe` 併記が必須。
	- `DeltaCalculator` 実装拡張: `compute_delta()` で両側の `eval_recipe` を比較し、不一致なら `InconsistentRecipeError`。
	- M3 / 論文 supplementary に Failure mode セクション (§15.1-15.2) を honest 開示として組み込む。
---
## 関連ページ {toggle="true"}
	- 前提・データ仕様・MTG 議事録:[研究方針_2026/05/14](https://www.notion.so/35fee4d4777780a8ae24f7b1246490e8)
<page url="https://app.notion.com/p/36dee4d4777781788e8accde3fd966a6">§13 研究方針再構成 - 壁打ち結果 (2026-05-28)</page>
## 16. エポック数・再現性の検証ログ {toggle="true"}
	本節は S0 再実験（§8.0 暫定運用、bengio で DDP 2 GPU 実行）の途中で発見された「エポック数の仮定根拠不足」と「論文 SOTA を大きく上回る数値の妥当性検証」を claude との壁打ちで整理したものである。§15 Lessons Learned の姉妹節として位置づけ、今後同様の「学習設定の仮定根拠不足」「再現性の警鐘」「評価条件の歪み」は本節に蓄積する。
	### 16.1 EgoSurgery-Tool 論文にエポック数の記載がない事実
	- arXiv:2406.03095v4 §3.1 Experimental setups を直接確認した結果、記載は「MMDetection 使用」「MS-COCO 事前学習から fine-tuning」「backbone parameters を寄せる」「confidence 10\^-8 で評価」の 4 点のみ。**エポック数・学習率・batch size・scheduler・augmentation の記述は一切ない**。
	- Fujiry0/EgoSurgery 公式リポジトリは**データセット配布のみで、検出器の学習コード・config が公開されていない**ことを確認。
	- mmdet 公式の 1x スケジュールだけは 12 epochs と定義されているが、これを論文の採用値と認める根拠は論文・公式リポジトリのいずれにもない。
	- **位置づけの修正**：§10.1 S0 手順の「完了判定 = VarifocalNet 公式 SOTA 45.8 を上回る」は、**エポック数を含む学習設定が不明のまま**の状態では有意にならず、eval_recipe だけでは再現性を保証できない。**〔2026-06-19 追記〕** 検出ベースラインはその後 DETR 系 10 モデルで実測完了し、現行の主基準は **Relation-DETR mAP 0.730**（3-seed 平均 0.727・σ0.004・AP_rare 0.758、§12/§13）。本 §16 の VFNet 0.618／論文 45.8 は旧 recipe の途中値・長尾検証の知見として保持する。今後 §10.1 S0 手順の「完了判定」を以下に書き換える（本節を根拠として次ステップで §10.1 を修正）：**(1) §15.4 A の strict 3 条件に加え、(2) 12 / 24 / 36 epochs の各時点で checkpoint を保存し val mAP で early stopping、3-seed std を併記、(3) Δ 比較群（S0 全 detector）で採用エポック数を統一、(4) VarifocalNet 公式 45.8 を上回ることを確認**。エポック数の論文公式値は 2026/05/29 時点で論文・公式リポジトリのいずれにも未公開であり、現状は mmdet 慣行の 1x = 12 epochs を暫定採用する。著者への問い合わせ結果は本節に追記する。
	### 16.2 VFNet 再実験の数値（2026/05/29 実測、bengio DDP 2 GPU）
	<table fit-page-width="true" header-row="true">
<tr>
<td>epoch</td>
<td>iter</td>
<td>mAP</td>
<td>mAP_50</td>
<td>mAP_75</td>
<td>AP_rare</td>
<td>AP_common</td>
</tr>
<tr>
<td>1</td>
<td>2,405</td>
<td>0.361</td>
<td>0.486</td>
<td>0.411</td>
<td>0.237</td>
<td>0.352</td>
</tr>
<tr>
<td>2</td>
<td>4,810</td>
<td>0.460</td>
<td>0.602</td>
<td>0.511</td>
<td>0.537</td>
<td>0.413</td>
</tr>
<tr>
<td>3</td>
<td>7,215</td>
<td>0.432</td>
<td>0.571</td>
<td>0.481</td>
<td>0.428</td>
<td>0.400</td>
</tr>
<tr>
<td>4</td>
<td>9,620</td>
<td>0.495</td>
<td>0.646</td>
<td>0.552</td>
<td>0.436</td>
<td>0.466</td>
</tr>
<tr>
<td>5</td>
<td>12,025</td>
<td>0.512</td>
<td>0.655</td>
<td>0.568</td>
<td>0.560</td>
<td>0.465</td>
</tr>
<tr>
<td>6</td>
<td>14,430</td>
<td>0.513</td>
<td>0.655</td>
<td>0.572</td>
<td>0.502</td>
<td>0.476</td>
</tr>
<tr>
<td>7</td>
<td>16,835</td>
<td>0.522</td>
<td>0.666</td>
<td>0.590</td>
<td>0.546</td>
<td>0.478</td>
</tr>
<tr>
<td>8</td>
<td>19,240</td>
<td>0.532</td>
<td>0.685</td>
<td>0.591</td>
<td>0.558</td>
<td>0.488</td>
</tr>
<tr>
<td>9</td>
<td>21,645</td>
<td>0.610</td>
<td>0.748</td>
<td>0.671</td>
<td>0.698</td>
<td>0.550</td>
</tr>
<tr>
<td>10</td>
<td>24,050</td>
<td>0.614</td>
<td>0.753</td>
<td>0.675</td>
<td>0.697</td>
<td>0.554</td>
</tr>
<tr>
<td>11</td>
<td>26,455</td>
<td>0.616</td>
<td>0.753</td>
<td>0.677</td>
<td>0.710</td>
<td>0.554</td>
</tr>
<tr>
<td>12</td>
<td>28,860</td>
<td>**0.618**</td>
<td>0.757</td>
<td>0.681</td>
<td>**0.706**</td>
<td>**0.557**</td>
</tr>
	</table>
	### 16.3 「乗り越え」の説明候補の網羅的列挙
	12 epoch で mAP 0.618 となり、論文公式 VFNet の 45.8 より 16pt 高い。以下の要因が単独・複合で作用した可能性がある。
	- **A. 評価条件側（最も疑わしい）**：(1) test_cfg.score_thr（論文 10\^-8 vs mmdet default 0.05）、(2) max_per_img（論文側は不明 vs locked-down 300）、(3) nms_pre・nms_iou の default 差、(4) COCO evaluation の IoU 閾値 0.5:0.95 vs 0.5 単独を誤って使うと過大評価、(5) per-class AP の平均方法 macro vs micro の取り違え。
	- **B. 学習設定側**：(1) エポック数 12 vs 24 vs 36、(2) batch size / lr と DDP 2 GPU での effective batch size 倍化 + lr 線形スケーリングの適用有無、(3) augmentation（mstrain / RandomCrop を使うと +2〜3pt）、(4) pretrain 重み torchvision vs open-mmlab、backbone R-50 vs R-50-DCN vs R-101、(5) **長尾対策の有無**：§10.1 S0 手順は Seesaw Loss・RFS・bbox-level Copy-Paste・post-hoc Logit Adjustment を有効化しているため、論文素の VFNet 45.8 を 10〜15pt 上回ること自体は不自然ではない。
	- **C. データ側**：(1) §15.4 の公式 split との一致 / assert_paper_split の pass、(2) 画像解像度設定、(3) annotation バージョン。
	### 16.4 警戒：AP_rare \> AP_common は通常起きない――赤信号
	§16.2 の表で epoch 9 以降 AP_rare が AP_common を常に上回り、最終 AP_rare 0.706 / AP_common 0.557 となった。通常は稀少クラスの AP は頻出クラスより低くなるため、この逆転は重大な警戒信号として記録し、§16.5 優先度 A の検証アクションに位置づける。説明候補は以下の 4 点。
	- (1) **AP_rare / AP_common のクラス分類定義が間違っている**：Forceps は train 2,534 / val 154 / test 3,375 instances と分布を持ち、12.21% の頻出クラスに属するが、test 頻度で rare 判定してしまうと誤って rare に含めてしまうケースがある。
	- (2) **AP_rare の計算対象クラスが極めて少なく分散が大きい**：Skewer test 29 instances / Syringe test 141 instances とサンプル数が小さいため、偶然に高くなりうる。
	- (3) **テストセットの構造的偏り**：稀少クラスが特定 video に集中しており、その video でだけうまく動いた可能性。
	- (4) **データリーク**：稀少クラスが train / val / test の同じ video に出ている可能性。
	### 16.5 検証アクション（優先度順）
	- **優先度 A（即時実行）**：
		1. eval_recipe の完全照合（§15.4 A strict 3 条件、COCO mAP IoU 0.5:0.95 で計算しているかを含む）。
		2. **AP_rare / AP_common の定義をコードで確認**（train 頻度で rare 判定しているか、対象クラスリストは Skewer/Syringe の 2 クラスのみか、計算式は per-class AP の単純平均か instance-weighted か）。
		3. **per-class AP を全 15 クラスで出力**し、全体 0.618 の内訳を確認。
	- **優先度 B（数日以内）**：
		1. **論文素の VFNet vanilla config で再現実験**（長尾対策を全部 OFF にして再学習）し 45.8 付近に着地するかを検証。着地すれば長尾対策で 16pt 上がったと説明でき、ずれるなら環境・データ・eval 側の問題。
		2. **学習曲線の loss 成分を確認**（cls / bbox / iou loss の収束、9 epoch 目の jump が lr decay 起因か）。
		3. **論文著者 Fujii 氏への問い合わせ**：公開 config・学習スクリプト公開予定、エポック数の明記、以上の点を含む厳密仕様の確認。
	- **優先度 C（長期）**：
		1. 複数 seed で再実行、3-seed std を併記し 61.8 が再現するか確認。
		2. Mask DINO / Co-DETR と並走して per-class AP 分布が一貫しているか sanity check。VFNet だけ異常に高い場合は VFNet 特異な実装問題を疑う。
	### 16.6 本節と §10.1 / §15 / §8 との関係
	- **§10.1 S0 手順**：「完了判定」の記述を §16.1 の 4 条件へ書き換える修正を次ステップで適用する。
	- **§15 Lessons Learned**：本節は §15 と並ぶ「評価条件・学習設定の仮定根拠不足・再現性」のランドマークとして位置づける。今後同様の事案は §16 に蓄積する。
	- **§8.-1 eval recipe 整合性の運用規則**：本節は §8.-1 を strict に遵守する趣旨であり、§8.-1 の規則自体は変更しない。
	### 16.7 優先度 A 検証結果（2026/05/29 追加）
	§16.5 優先度 A の (1)〜(3) を実行した結果を記録する。eval_recipe の strict 3 条件はすべて PASS。ただし (i) AP_common の定義上の歪み、(ii) Forceps / Gauze の低 AP という 2 点の重要な発見があった。
	#### 16.7.1 strict 3 条件の照合結果
	- **条件 ① データ split**：train 9,657 / val 1,515 / test 4,265 images、ann 32,272 / 4,707 / 12,673 で論文 Table 3a と完全一致。**PASS**。
	- **条件 ② test_cfg**：score_thr=1e-08、max_per_img=300、nms_pre=3000、nms_iou=0.6 を確認。**PASS**。
	- **条件 ③ 評価指標**：bbox_mAP（mmdet CocoMetric が IoU 0.50:0.95 の 10 点平均で出す標準 COCO AP）を mAP にミラーし、AP_50 は別キーに併記。ヘッドライン 0.618 は AP_50 ではなくフルレンジ COCO mAP。**PASS（フルレンジ）**。
	- **§8 訓練スクリプトに関する補足**：val_evaluator の ann_file は instances_val.json、prefix='val'（mmdet_[config.py:314](http://config.py:314)-320）のため、metrics.json / per_class_ap.json はすべて val split の数値。test split は未評価（最終報告用に温存、Δ 判定は val で行う設計）。
	#### 16.7.2 AP_rare / AP_common の定義検証結果
	- **クラスリスト**：`RARE_CLASSES = ["Skewer", "Syringe"]`（2 クラスのみ、Forceps は含まない）。[constants.py:71](http://constants.py:71) と mmdet_[config.py:321](http://config.py:321)-324 でコード上確認。Forceps は 12.21% でトップ 3 の頻出クラスとして CONFUSABLE_CLASSES（§3.3 と整合）に収められている。
	- **頻度判定基準**：train 頻度（0.7% / 1.17%）。test 頻度で判定している誤りはない。
	- **計算式**：per-class AP の単純平均（macro / 非加重、`np.mean`）。再現計算で AP_rare = mean(Skewer 0.876, Syringe 0.536) = 0.706、AP_common = 残り 13 クラス平均 = 0.5566 と metrics.json 一致。
	#### 16.7.3 見つかり 1：AP_common の定義上の歪み（要修正）
	mmdet_[components.py:87](http://components.py:87) は GT 不在クラスの NaN を 0.0 に倒して AP_common に算入している。そのため Retractor（val GT 0 件）が AP=NaN→0.0 として平均に加わる。COCO 全体 mAP は GT 不在クラスを除外して平均するため、**「全体 mAP は空クラスを除外、AP_common は 0.0 で罰する」という非対称**が生じている。
	- AP_common = 0.557（現状、Retractor 0.0 を含む）、Retractor を除外した nanmean なら 0.603、全体 mAP = 0.6177 ≈ 0.618 で検証済み。
	- **影響**：Δ 判定で AP_common を使う際、Retractor が val に出ない限り全 seed・全モデルで同じ -4.6pt バイアスが乗るため、**相対比較（Δ）は保たれる**。ただし絶対値の解釈（論文記載時に reviewer から「なぜ全体 mAP より AP_common が低いのか？」と問われるリスク）と、Phase-1 で mask 入手後に Retractor が val に現れるバージョンとの比較、の 2 点で問題となる。
	- **修正方針**：
		1. mmdet_[components.py:87](http://components.py:87) を `np.nanmean` に変更して空クラスを除外し、COCO 慣行と整合させる。
		2. eval_recipe に `ap_common_aggregation` フィールドを追加し、`mean_v1`（旧）と `nanmean_v2`（新）の混在を `InconsistentRecipeError` で検出する。
		3. 過去実験（s0_004/005/006 他）は旧定義 `mean_v1` で凍結し、per_class_ap.json から `nanmean_v2` も併記するよう metrics 再計算を走らせる（再学習は不要）。
		4. 論文 Table II 脚注に「AP_common は GT 不在クラスを除外した macro 平均」と明記する。
	#### 16.7.4 見つかり 2：AP_rare \> AP_common の「赤信号」は誤警報、真の異常は Forceps / Gauze
	- **AP_rare 0.706 の中身**：Skewer 0.876 と Syringe 0.536 の平均。以前の「Skewer test 29 instances」の懸念は test split 統計に基づくものだったが、評価が走っているのは val であり、val では Skewer = 103 instances と十分なサンプル数がある。**前回の「Skewer test 29」懸念は val と test を取り違えた誤りであり、ここで訂正する**。ただし少数クラスの AP が高分散になるリスクは val 内で本当に少ない Bipolar Forceps (55) / Raspatory (76) / Syringe (96) に依然として存在し、これらは ±0.05〜0.1 規模で AP が振れうる。
	- **真の異常値**：Forceps AP 0.238（val 154 instances、データ量は十分）と Gauze AP 0.202。Forceps は Tweezers 0.687 / Needle Holders 0.812 という高 AP クラスにとられている構造であり、Gauze は非剛体のため bbox 局在が原理的に困難。**これは §2 結合効果①の根拠「形状類似ペア（Forceps / Tweezers / Needle Holders）の混同は静的視覚特徴のみでは識別困難」を実証しており、タスク結合（工程文脈→検出）で Forceps AP の改善幅に期待をもてるストーリーに整合**する。
	- **高 AP 群**：Electric Cautery 0.911 / Scalpel 0.842 / Mouth Gag 0.757 / Suction Cannula 0.733 は形状が独特で他クラスにとられにくい剛体術具であり、長尾対策と独立に高くなって自然である。
	- **Retractor = NaN**：val に GT が 0 件のため COCO が AP を定義できずに NaN を返すだけで、モデル不具合ではない。
	#### 16.7.5 12 epoch 61.8 mAP の妥当性に関する暫定結論
	- **実装ミス・評価誤りではない**：eval_recipe は strict 3 条件で論文に照合済み、評価指標は COCO mAP IoU 0.50:0.95 で AP_50 単独ではない、高 AP 群は形状が独特な剛体術具で長尾対策と無関係に高くなり自然、低 AP 群 Forceps / Gauze は構造的困難と一致、Phase 文脈の援護なしの S0 段階として妥当に低い。
	- **長尾対策の効果**：Seesaw + RFS + Copy-Paste + Logit Adjustment が Skewer/Syringe を底上げし、論文素の VFNet 45.8 を 10〜15pt 上回ること自体は仮説として受け入れられる。
	- **ただし「実装に問題がない」と確定するには §16.5 優先度 B の検証がなお必要**：
		1. (B-1) vanilla VFNet（長尾対策をすべて OFF）で 45.8 ±2pt に着地するか検証する。着地すれば長尾対策の効果が本物。
		2. (B-2) 3 seeds で std を取り、少数クラス（Bipolar Forceps / Raspatory / Syringe）の std を点検する。
		3. (B-3) 著者 Fujii 氏への問い合わせ。
		4. (C) Mask DINO / Co-DETR と並走で per-class AP 分布が一貫しているか sanity check する。
</content>
</page>
