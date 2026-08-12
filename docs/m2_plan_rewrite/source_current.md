Here is the result of "view" for the Page with URL https://app.notion.com/p/361ee4d47777804fb7e6c023cf50267d as of 2026-06-19T04:50:07.509Z:
<page url="https://app.notion.com/p/361ee4d47777804fb7e6c023cf50267d">
<ancestor-path></ancestor-path>
<properties>
{"title":"M2研究計画"}
</properties>
<content>
# M2 研究計画
> M2 期間の研究計画を集約したマスタードキュメント。タスク間相互改善(H1〜H4)を中核仮説とし、S0〜S9 の検証ロードマップと 7 分類のサーベイ計画を含む。前提・データ仕様・MTG 議事録は `研究方針_2026/05/14` を参照のこと。**本ページへの変更はすべて §0 「変更履歴」に逐次記録される**。**〔2026-06-14〕研究のコア主張は「タスク結合の原理提案（分析ファースト）」に転換済み。最新方針は直下の『研究方針の現在地』セクションと正本（§13 / §2.5(b) §7）を参照。§1〜§16 の H1〜H4 フレームは経緯・運用ルールの記録として保持。**
---
## 変更履歴(逐次更新) {toggle="true"}
	本ページの編集履歴を新しい順に記載する。**今後の変更はすべて、本セクションの冗頭に追記する**。記録項目は「日付 / 変更のサマリ・該当 § / 変更の要旨」の 3 点を原則とする。
	### 2026/06/14
	**「研究方針の現在地」セクションを冒頭に新設し、タスク結合提案へのピボット（§13）と分析ファースト順序（§2.5(b) §7、2026-06-14 確定）を本体に反映**
	本体は §2 中核仮説（H1〜H4「相互改善」）フレームのままで、(a) コア主張のタスク結合提案への転換、(b) 既存結合→差分分析→仮説の分析ファースト順序、(c) STEP A–D、(d) 検出ベースラインの実態（DETR 系 10 モデル完了・Relation-DETR 0.730 で 1 位、README 旧 0.327 は更新済）が未反映だった。冒頭（§0 の直前）に非折りたたみの「研究方針の現在地」セクションを新設し、最新のコア主張・研究順序（分析ファースト）・STEP A–D・最優先ブロッカー（eval recipe 一本化／凍結源確定）・実験の現状・旧 H1〜H4 フレームの位置づけを明記した。あわせて冒頭の概要ブロックに最新方針への注記を追加。正本は §13 研究方針再構成 / §2.5(b) §7、関連は意思決定ログ「研究順序を分析ファーストへ変更」。§1〜§16 の H1〜H4 記述と実験運用ルールは経緯・知見の記録として保持し、本文の全面再構成はマイルストーン単位で後追いする。
	### 2026/06/02
	**§10〜§12 の内部小見出し番号の不整合を修正（以前の章順入れ替え時に見出し番号本体だけが変わり、中身の小見出し番号が未同期だった件の修正）**
	以前の章順変更（2026/05/25、§12 を §10 に移動）で見出しの番号は付け替えたが、各セクション内部の小見出し番号が同期されておらず、§10「サーベイロードマップ」の中に `11.0 / 11.A〜G / 11.1〜11.3` という旧番号が、§11「サーベイ結果」の中に `12.21` が、§12「直近のマイルストーン」の中に `10.1` が残存していた。以下のとおり一括修正した。
	- §10 内部の小見出し: `11.0 全体構造(7 分類)` → `10.0`、`11.A〜11.G` → `10.A〜10.G`、`11.1 サーベイの実施順序` → `10.1`、`11.2 除外したが意識する価値のある分野` → `10.2`、`11.3 サーベイ運用の指針` → `10.3`。
	- §11 内部の小見出し: `12.21 サーベイ結果の横断的知見` → `11.21`。あわせて§11 凒頭の「§11 のサーベイロードマップに基づき」を「§10 のサーベイロードマップに基づき」に差し替え、「§10（サーベイロードマップ）→§11（サーベイ結果）」の参照関係を明示した。
	- §12 内部の小見出し: `10.1 詳細検証ロードマップ(S0〜S9)` → `12.1`。
	- **未修正の残課題（ユーザーへの報告）**：他セクション（§2・§3・§4・§5・§8・§9・§13・§14・§15・§16 他）からの「§10.1」「§12.21」「§11.1」等の参照表記は **未修正**。同じ記号でも今回の修正により指す先が変わったため、ケースごとに古い参照を新番号へ読み替える作業が今後必要。例：§2.5 末尾の「§7 参照」、§8.1 A1 の「§15.4 A」系の引用は現状の番号と一致しており手を入れないが、§13 や §14 内部にある「§10.1 S0 手順」「§10.1 共通設定の厳格化」等は現在§12.1 を指すため読み替えが必要。次回の壁打ちで手順を詰める。
	### 2026/06/01
	**§16「エポック数・再現性の検証ログ」の全面リライト（構造・表表記・認識誤りの修正）**
	§16 の Markdown 構造が壊れていた（改行が `nt` として文字列化、表が `\<table\>` としてエスケープ、toggle 構文が未完成 `\{\}`、末尾に `\</table\>` の余分な閉タグが複数残存）ため、§16 全体を以下の方針で全面リライトした。記録値（VFNet 12 epoch の実測表・クラス定義・per-class AP の数値・strict 3 条件の検証結果・修正方針等）はすべて原文を忠実に保持し、意味内容の変更は行わない。
	- **構造修復**：H2 トップレベル見出しを `## 16. ... {toggle="true"}` に正規化。§16.1〜§16.7 と§16.7.1〜§16.7.5 を Notion Markdown の見出し階層（H3 / H4）とタブインデントに復元。
	- **表の修復**：§16.2 VFNet 再実験数値表を、§8.1 などと同一の `<table fit-page-width="true" header-row="true">` 形式で復元。末尾に複数豊在していた `\</table\>` の余分な閉タグと `{toggle="true"}` の末尾付加を除去。
	- **表記誤りの訂正**：文脈から明らかに誤変換・脱字と判断される箇所のみを修正（例：「本型議」→「本議論」、「託かれる」→「問われる」、「選択肉 A」→「優先度 A」、「偊然」→「偶然」、「ざれる」→「ずれる」、「生したランドマーク」→「ランドマーク」、「態勢」→「事案」、「仍必要」→「なお必要」、「無関に」→「無関係に」、「同向で自然」→「不自然ではない」等）。数値・コードパス・クラス定義・検証結論は原文をそのまま保持している。
	- **冗長部分の整理**：§16.5 を番号付きリストに変換して読みやすくし、§16.7.3 の修正方針 4 点をサブリスト化した。わずかに文言を整えたが、記述の追加・削除は行っていない。
	### 2026/05/29（3）
	**§16.5 優先度 A 検証完了、AP_common 定義歪みの発見と §16.7 追加（claude との壁打ちを記録）**
	§16.5 優先度 A の 3 項目（1）eval_recipe 照合、（2）AP_rare/AP_common 定義確認、（3）全 15 クラス per-class AP を実行し、strict 3 条件はすべて PASSを確認。ただし仮定していなかった 2 点の発見があったため §16.7 として記録した。
	- **見つかり 1：AP_common の定義上の歪み**：mmdet_[components.py:87](http://components.py:87) が GT 不在クラスの NaN を 0.0 に倒して平均に算入しているため、Retractor（val GT 0 件）が -4.6pt の押し下げバイアスとして常時乗っている。COCO 全体 mAP は空クラスを除外するため「全体 mAP（0.618） \> AP_common（0.557）」という見た目の逆転が起き、論文記載時に reviewer からの託問リスクとなる。**対策**：(i) np.nanmean 化で COCO 慣行に揃える、(ii) eval_recipe に ap_common_aggregation フィールドを追加し mean_v1/nanmean_v2 の混在を InconsistentRecipeError で檢出、(iii) 過去実験は旧定義で凍結・per_class_ap.json から nanmean_v2 を併記する metrics 再計算（再学習不要）、(iv) 論文 Table II 脚注に「AP_common は GT 不在クラスを除外した macro 平均」と明記。
	- **見つかり 2：per-class AP の赤信号は Skewer 0.876 ではなく Forceps 0.238 / Gauze 0.202**：前回「Skewer test 29 instances」と懸念したのは val と test を取り違えた誤り（訂正）。val では Skewer = 103 instances とサンプルで、AP 0.876 は長尾対策効果として妥当。一方で Forceps AP 0.238（val 154 instances、データ量十分）と Gauze AP 0.202 が本当の低 AP。Forceps は Tweezers 0.687 / Needle Holders 0.812 にとられており、**これは §2.1 H1 の根拠「形状類似ペアの混同は静的視覚特徴のみでは識別困難」を実証し、S6 Phase→Detection で Forceps AP の改善幅に期待をもてるストーリーに整合**している。
	- **12 epoch 61.8 mAP の暗定結論**：eval_recipe とクラス定義、per-class 分布のいずれも妥当で、長尾対策の効果として 16pt 上回ること自体は仮説として受け入れられる。ただし確定には §16.5 優先度 B の検証（vanilla VFNet で長尾対策 OFF の再学習で 45.8 ±2pt に着地するか、論文著者への問い合わせ、Mask DINO/Co-DETR 並走の per-class 分布 sanity check）が仍必要。
	- **次のアクション**：AP_common の nanmean 化と eval_recipe のバージョン記録を実装、vanilla VFNet 再学習を bengio で並列実行、s0_004/005/006 の 3 seeds std をテーブル化、Fujii 氏への問い合わせドラフト。
	### 2026/05/29（2）
	**エポック数の論文根拠不足と VFNet 再実験数値の妥当性検証を §16 として新設（claude との壁打ちを記録）**
	S0 再実験（bengio の DDP 2 GPU 暫定運用、§8.0 条件下）の途中で、（1）「mmdet 基準の 12 epochs」の論文根拠が見つからない、（2）論文公式 SOTA 45.8 を 16pt 上回る 61.8 となったため再現性が不安、という 2 点の懸念が生じた。web search を用いて EgoSurgery-Tool 論文 arXiv:2406.03095v4 の §3.1 を直接確認し、論文に「エポック数・学習率・batch size・scheduler・augmentation の記述が一切ない」こと、Fujiry0/EgoSurgery リポジトリが「データセット配布のみで検出器学習コードが公開されていない」ことを確定させた。これを受け、§16 を新設して実計データ・乗り越えの説明候補の網羅・AP_rare \> AP_common の赤信号・検証アクションを記録した。
	- **エポック数の位置づけ修正**：§10.1 S0 手順の「完了判定」を「§15.4 A の strict 3 条件 + 12/24/36 epochs 複数 checkpoint 保存と early stopping + Δ 比較群内のエポック数統一 + VFNet 45.8 超え」に書き換える修正を次ステップで適用する（§16.1 参照）。mmdet 慣行の 1x = 12 epochs は暫定採用下、著者への問い合わせ結果を待つ。
	- **VFNet 公式 SOTA 45.8 を 16pt 上回る「乗り越え」の網羅的説明候補**（§16.3）：評価条件側（test_cfg.score_thr / max_per_img / IoU 閾値選択 / per-class AP 平均方法）、学習設定側（エポック数 / DDP effective batch size 倍化 + lr スケーリング適用 / augmentation / pretrain 重み / 長尾対策の有無）、データ側（公式 split 一致 / 画像解像度 / annotation バージョン）の 3 軸で説明を列挙。§10.1 S0 手順が Seesaw / RFS / Copy-Paste / Logit Adjustment を有効化しているため、論文素の VFNet を 10〜15pt 上回ること自体は不自然ではないと位置づける。
	- **AP_rare \> AP_common の赤信号**（§16.4）：§16.2 表で epoch 9 以降 AP_rare 0.706 / AP_common 0.557 と逆転しているため、警戒信号として記録。説明候補は (1) AP_rare / AP_common のクラス分類定義（train 頻度 vs test 頻度、Forceps の誤分類リスク）、(2) AP_rare の計算対象クラス数の少なさ（Skewer test 29 / Syringe test 141 とサンプル少、分散大）、(3) テストセットの構造的偏り、(4) データリークの 4 点。
	- **優先度 A 極限の検証アクション**（§16.5）：(1) eval_recipe の完全照合（COCO mAP IoU 0.5:0.95 の使用確認含む）、(2) AP_rare / AP_common の定義をコードで確認（train 頻度で rare 判定か、対象クラスリストは Skewer/Syringe 2 クラスのみか、計算式は）、(3) per-class AP を全 15 クラスで出力し 0.618 の内訳を確認。優先度 B：論文素 vanilla VFNet で長尾対策 OFF で再学習し 45.8 付近に着地するか検証、論文著者 Fujii 氏への問い合わせ。優先度 C：複数 seed で再実行 + Mask DINO/Co-DETR 並走の per-class 分布 sanity check。
	- **今後同様の記録は §16 に蓄積する**：§15 Lessons Learned の姉妹節として、今後同様の「仮定根拠不足・再現性警鐘」は §16 に蓄積する。
	### 2026/05/29
	**壁打ち結果：バッチサイズ・学習エポック数・HPO 戦略の方針確定（claude との壁打ちを記録）**
	バッチサイズ・学習エポック数・ハイパーパラメータ最適化（HPO）について、本研究の §8.0・§15.4・§10.1 が要求する Δ 整合性制約に即して方針を確定した。本記録は claude との壁打ちセッション結果であり、後続ステップで §8 または §13 へ正式に取り込むことを想定する。
	- **バッチサイズの決定原則**：同一 Δ 比較群内では batch size・effective batch size・lr・scheduler を完全に揃える（§8.0(4)〜(6) と §10.1 共通設定の厳格化の機械的適用）。決定は「ベースライン論文・先行サーベイ準拠 → 48GB OOM 限界の 8 割 → DDP 使用時は per-GPU 一定で effective を倍化、lr 線形スケーリング → config + eval_recipe に記録」の順で機械的に行い、HP として自由探索しない。
	- **ステップ別 batch size 初期値**（本研究の状況に即した）：S0 検出器（Mask DINO / VarifocalNet / Co-DETR、DDP 2 GPU）= per-GPU 2 / effective 4。S4 第 1 波（TeCNO / SR-Mamba、global feature 入力）= 32〜64。S4 第 2 波（HID-SSM / SKiT / Surgformer）= 8〜16。S5・S6（object token 入力時系列）= 8〜16。S8 Stage B（Exo SSL、A5000 ×5 DDP、5 fps サブサンプリング）= per-GPU 8 / effective 40。S8 Stage C（Ego-Exo 蒸留、A6000 ×2）= per-GPU 4 / effective 8。S9 Stage D（統合 fine-tuning）= S5/S6 と同一。
	- **学習エポック数の決定原則**：ステップごとに先行研究の標準スケジュールを準用し、early stopping（val 主要指標が 5 epoch 連続で plateau）で切り上げる。Δ 比較群内で total training steps を完全一致させること（§10.1 共通設定の厳格化）。
	- **ステップ別エポック数の目安**：S0 検出器 = 12 epochs (1x) or 36 epochs (3x、mmdet 標準)。S2 = S0 と同じ（forgetting 監視）。S3 = 20 epochs（パイプライン確認）。S4 第 1 波 = 50 epochs（TeCNO 公式）。S4 第 2 波 = 30〜50 epochs（各論文公式）。S5・S6 = 30〜50 epochs。S8 Stage B（Exo SSL）= 100〜400 epochs（VideoMAE v2 公式 800 をサブサンプリングで圧縮）。S8 Stage C = 30〜50 epochs（Quattrocchi 2024 準拠）。S9 Stage D = 20〜30 epochs（fine-tuning のため短め）。スケジューラは cosine annealing + linear warmup (1〜2 epoch)、optimizer は AdamW (lr=1e-4, weight_decay=0.05) を共通の出発点とする。
	- **HPO 戦略の決定原則**：本研究でフル HPO は不要かつ有害。理由は (i) §8.0・§15.4 の recipe 整合性要求により提案手法だけ HPO で稼ぐと Δ の正当性が崩壊する、(ii) 3 seeds × 50〜100 実験で既に計算予算逼迫、(iii) CVPR 査読で HPO 偏りは unfair comparison として指摘される、の 3 点。
	- **HPO の 3 層構造**：第 1 層（全実験で固定、HPO 対象外）= seed=42 / deterministic / cudnn.benchmark=False / optimizer=AdamW / scheduler=cosine+warmup / gradient clip=1.0 / locked-down test_cfg / 公式 split。第 2 層（軽く探索、ablation として組み込み）= 基本 lr の 3〜5 点 grid (1e-5, 3e-5, 1e-4, 3e-4)・MTL 損失重み付け方式 5 条件 (§8.2)・Phase→Det 注入方式 3 条件 (§4.6/§8.2)・時系列モデル選択 (§4.5 第 1 波 2 + 第 2 波 4)・temporal-consistent copy-paste 強度 4 点 (§3.3)。第 3 層（本研究では行わない）= Bayesian Optimization / Optuna 大規模探索 / Population Based Training / NAS。
	- **シード変動の扱い**：EgoSurgery は 21 動画・8 術者・1 施設と小規模（§12.24 G4）で variance が大きいため、最低 3 seeds、可能なら 5 seeds で mean±std を必ず報告。§15.4 C「1σ は同一 recipe での 3-seed std」を厳守し、paired bootstrap 信頼区間で Δ の有意差を判定（§10.1 S9）。
	- **§2.6 二段構えとの整合**：HPO 予算を抑えて D-A（設計仮説、ablation A7）・D-B（初の EgoSurgery-Phase 長距離ベンチマーク、S4 第 2 波）・転移検証（PhaKIR / CholecT45 / EgoExOR）の実験充実度に回す方が CVPR 戦略として強い。HPO で稼いだ Δ は reviewer に弱いが、D-A・D-B は Δ に依存しないため二段構えの後段として機能する。
	- **§14 で実証済みの失敗モード再発防止の再確認**：S2 catastrophic forgetting（tool mAP 0.3% 崩壊）対策として layer-wise lr / 段階的凍結解除 / tool head KD / 複合 best 指標（§10.1 S2 失敗時対応）、S3 class weights 崩壊（val acc 0.5% 崩壊）対策として class weights デフォルト無効化・上限 10 倍クリップ・label smoothing 0.1 常用（§3.3）を引き続き徹底する。
	- **次のアクション**：本回答の §2.2 / §3.2 の値を configs/default.yaml に固定値として記述、各ステップ着手時に eval_recipe へ batch size・epoch・lr・seed・GPU 構成を必ず記録、第 2 層 HPO は §8.2 ablation として統合する運用フローを確立する。本方針の §8 または §13 への正式取り込みは、次回の壁打ちで検討する。
	### 2026/05/25（4）
	**§10（直近のマイルストーン）を §13（実験実行手順書）の直前に移動**
	§10「直近のマイルストーン（各 M で検証する仮説を明示）」を §12「サーベイ結果」の後、§13「実験実行手順書」の直前に移動した。
	### 2026/05/25（3）
	**実装プロンプト全 6 ファイルを DDP 2 GPU 対応に改訂**
	§8.0 の DDP 運用条件追加と §13.2 の「DDP 2 GPU 運用の実装要件」新設を受け、コーディングエージェント向け実装プロンプト（フェーズ I patch + フェーズ II Part 1〜5）を DDP 2 GPU 対応に一括改訂した。
	- phase1_patch_eval_[recipe.md](http://recipe.md)（v2）: build_eval_recipe に gpu_count・effective_batch_size・lr_scaling を追加。recipes_match と compute_delta の照合対象に GPU 構成を含め、単一 GPU と DDP の混在を InconsistentRecipeError で検知する（§8.0 条件 (4)(5)）。
	- phase2_part1_data_pipeline_[v2.md](http://v2.md)（v2.1）: DataLoader が DistributedSampler を受け入れられる構造を明記。RFS は DistributedSampler との二重適用を避ける実装方針を追加。batch size を per-GPU / effective に区別。
	- phase2_part2_[models.md](http://models.md)（v2.2）: 各モデルの正規化層種別（BatchNorm / LayerNorm）を明記し、SyncBatchNorm の選択的適用（§13.2 (b)(iv)）の判断材料とした。
	- phase2_part3_s0_execution_[v2.md](http://v2.md)（v2.1）: MMDetTrainer を DDP 対応に全面書き換え（DistributedDataParallel / DistributedSampler 初期化、rank=0 のみ metrics 書き出し、SyncBatchNorm 選択適用、_resolve_lr による lr 線形スケーリング）。run_[s0.sh](http://s0.sh) を torchrun --nproc_per_node=2 化し、MASTER_PORT を seed/detector ごとにユニーク化。eval_recipe に DDP フィールドを記録。
	- phase2_part4_s2_s3_[v2.md](http://v2.md)（v2.2）: S2 の術具 mAP は S0 と Δ(S2-S0) を取るため、S2 も S0 と同一 GPU 構成（DDP 2 GPU）で学習することを必須化（§8.0 条件 (4)）。
	- phase2_part5_s4_[temporal.md](http://temporal.md)（v2.2）: TemporalTrainer を DDP 対応に。run_[s4.sh](http://s4.sh) を torchrun 化。特徴量抽出元 S0 checkpoint は DDP 2 GPU 版（gpu_count==2）でなければならないことを明記。
	- codetr_patch_part2_[part3.md](http://part3.md): 当初「進行中の単一 GPU 学習に干渉しない Co-DETR 差分」として作成したが、S0 全体を DDP で再実行する方針により前提が消滅。Co-DETR は Part 2 v2.2 / Part 3 v2.1 に統合済みとし、本ファイルは記録用に残すが投入には使わない。
	- やり直し範囲：S0 の学習（s0_001〜s0_009）は単一 GPU から DDP 2 GPU へ全 9 実験を再学習。進行中の単一 GPU 学習（Mask DINO val/mAP 0.509 を含む）は Δ 基準点に使用しない。コード修正は MMDetTrainer の DDP 対応を起点とし Part 3 を中心に、eval_recipe パッチ・Part 1/2/4/5 に波及。
	### 2026/05/25（2）
	**§8.0 に DDP 2 GPU での S0 実行許容条件を追加、§5・§10.1・§13・§14 に反映**
	VFNet の単一 GPU 学習に時間がかかりすぎるため、S0 全モデル（VFNet・Mask DINO・Co-DETR）を bengio（RTX A6000 ×2）の DDP 2 GPU で統一して再実行する方針に変更した。
	- §8.0「暫定運用」に DDP 運用条件を追記：(4) DDP 使用時は S0 内の全モデルを同一 GPU 構成（同一サーバーの同一 GPU 枚数・同一 DDP 設定）で揃える、(5) effective batch size（GPU 枚数 × per-GPU batch size）を metrics.json の eval_recipe に記録する、(6) learning rate の線形スケーリング適用有無を config に明記する。これらは既存 3 条件に追加される。
	- §5 Stage A0 に GPU 構成の運用注記を追加：DDP 使用時は S0 内全モデルを同一 GPU 構成で揃えること、effective batch size と lr スケーリングを記録することを明記。
	- §10.1 S0 ステップ詳細：実行サーバーの記述に DDP 暫定運用の条件を追記。注意事項に GPU 構成の整合性（単一 GPU と DDP の混在禁止）を追加。
	- §10.1 全体注意事項：「共通設定の厳格化」に GPU 構成を揃える要件を追加。「計算コストの見積もりと GPU 割り当て」に DDP 使用時の eval_recipe 記録要件を追加。
	- §13.0 計算環境の前提：暫定運用の条件数を旧 3 条件から 6 条件に更新し、DDP 運用条件 (4)(5)(6) を反映。
	- §13.2 S0 手順に「DDP 2 GPU 運用の実装要件」を新設：(a) effective batch size の倍化と lr 線形スケーリング、(b) `MMDetTrainer` への DDP 対応（`_build_eval_recipe` への `gpu_count`・`effective_batch_size` フィールド追加、`DistributedDataParallel` / `DistributedSampler` 初期化、rank=0 のみ `_write_metrics` 実行、`SyncBatchNorm` の選択的適用）、(c) `run_s0.sh` を `torchrun --nproc_per_node=2` に書き換え（`MASTER_PORT` のユニーク化含む）、(d) 全モデル統一の制約。
	- §14 bengio セクションに「S0 DDP 2 GPU 再実行予定」を追記。既存の単一 GPU 学習結果（進行中）は S0 内の全モデル整合性が取れないため破棄し、全モデルを DDP 2 GPU で 3 seeds × 12 epoch として再実行する旨を記録。
	- 設計根拠：§8.0 の既存原則「同一の Δ 比較群は必ず同一サーバー上で揃えて測定する」を GPU 構成にも拡張適用。単一 GPU vs 2 GPU DDP の混在は effective batch size・allreduce 非決定性・BN/LN 挙動の差異により Δ の意味を崩壊させるため、S0 全体を統一する。RTX 6000 Ada 配備後の再測定対象であることは既存条件 (3) で担保される。
	### 2026/05/25
	**§13.0 の計算環境の前提を §8.0 サーバー割り当て運用原則に整合させる修正**
	実装プロンプト（フェーズ I / フェーズ II Part 1〜5）と §13 手順計画の整合性分析の結果、§13.0「計算環境の前提」が「S0〜S9 の本実験は全て RTX 6000 Ada に統一」とのみ記載し、§8.0 の「暫定運用：RTX 6000 Ada 未配備期間は bengio での Δ 基準点学習を 3 条件付きで許容」を反映していなかったため、§13.0 を修正した。
	- §13.0 計算環境の前提に、サーバー割り当ての運用ルールは §8.0 を最優先の規範とする旨を明記。RTX 6000 Ada 未配備期間は bengio（A6000）での Δ 基準点学習を §8.0 の 3 条件（同一比較群は同一サーバー / eval_recipe.server_name・server.txt 記録 / Ada 配備後の再測定を §14 に明記）付きで許容することを §13.0 にも明示し、§14 の実態（bengio での修正後正式計測予定）と整合させた。
	- §13.2〜§13.4 の各ステップ記載の「実行サーバー」は RTX 6000 Ada 配備後の最終形であり、未配備期間は §8.0 暫定運用に読み替える旨を明記。
	### 2026/05/24
	**§15 の知見を §8・§10.1・§3.3 の本文へ波及させる整合性修正**
	§15「Lessons Learned」と §14 実験ログで記録された S0 完走後の知見（split 取り違え・test_cfg 不一致・catastrophic forgetting・class weights 崩壊）が、実験運用セクション §8 と検証ロードマップ §10.1 の本文に未反映であったため、以下の整合性修正を実施した。
	- §8 に「§8.-1 eval recipe 整合性の運用規則」を新設：eval recipe の定義、metrics.json への併記、locked-down test_cfg の強制、論文公式 split の固定、DeltaCalculator の recipe 照合（InconsistentRecipeError）を §15.4・§15.6 から運用ルールに落とし込み。
	- §8.0 に「暫定運用：RTX 6000 Ada 未配備期間」を追記：6000 Ada 未配備期間は bengio（A6000）での Δ 基準点学習を 3 条件付きで許容することを明文化し、§14 の実態と整合させた。
	- §8.1 A1 ablation の比較対象に、§15.4 A の strict 3 条件（公式 split / locked-down test_cfg / eval_recipe 一致）を満たす同一 recipe で比較する旨を明記。
	- §10.1 S0 の学習設定：Copy-Paste の対象稀少クラスを Skewer / Syringe の 2 クラスに明示（Forceps は 12.21% で対象外、§3.3 と整合）。評価条件として locked-down test_cfg と公式 split を明記。
	- §10.1 S0 の完了判定に strict 3 条件を追加：「VarifocalNet 45.8 を上回る」判定が公式 split・locked-down test_cfg・eval_recipe 一致のもとでのみ有効であることを明記。
	- §10.1 S2 の失敗時対応に catastrophic forgetting 対策を追加：§14 で tool mAP が 0.3% に崩壊した実例を踏まえ、layer-wise lr・backbone 段階的凍結解除・tool head KD・複合 best 指標の 4 対策を明記。
	- §10.1 S3 と §3.3 工程の項に class weights 崩壊の注意を追加：§14 で val accuracy が 0.5% に崩壊した実例を踏まえ、class weights のデフォルト無効化・weight 比の上限クリップ・崩壊検知セーフガードを明記。
	- §10.1 全体注意事項「基準点の信頼性」に strict 3 条件と「1σ は同一 recipe での 3-seed std」を追記。
	### 2026/05/24
	**術具クラス表の数値訂正（Forceps 1.22% → 12.21%）に伴う研究方針の修正**
	研究方針_2026/05/14 における術具クラス表の Forceps の出現割合が誤記（1.22%）であり、正しくは 12.21% であった。Forceps はワースト 3（稀少クラス）ではなくトップ 3（頻出クラス）に位置する。これを受け、以下の修正を実施。
	- §2.1 H1 の根拠：稀少クラス例から Forceps を削除し、Skewer 0.7% / Syringe 1.17% の 2 クラスに修正。形状類似の説明に Forceps が 12.21% で頻出クラスである旨を追記。
	- §3.3 クラス不均衡対応：術具不均衡の記述に Forceps = 12.21%（トップ 3）を明記。bbox-level Copy-Paste のターゲットから Forceps を削除（Skewer/Syringe のみ）。
	- §4.2 class-balanced denoising sampling：稀少クラス例から Forceps を削除（Skewer/Syringe のみ）。
	- §7.1 Δ mAP：稀少クラス mAP の中心から Forceps を削除。Forceps は形状類似ペアとしてのみ報告対象とする。
	- §8.1 A1 ablation：主要指標に稀少クラス（Skewer/Syringe）と形状類似ペア（Forceps/Tweezers/Needle Holders）を明示的に分離。
	- §8.2 長尾損失 ablation：報告対象 per-class AP から Forceps を削除。
	- §10.1 S0 / S6：稀少クラス例と報告指標から Forceps を削除、AP_common に分類する旨を明記。
	- §13.2 S0 手順：同様に修正。
	### 2026/05/24
	**実行サーバー名「bengio」を全実験ログに記録する仕組みを導入、§14 に bengio 実験記録を追加**
	M2研究計画§14「実験結果ログ（実行マシン別）」の運用と§13.8 GPU 割り当ての追跡性を強化するため、実行ホスト名をコード・証拠ファイル・W&B の 3 経路で一貫して記録する仕組みを導入した。
	- `src/egosurgery/utils/server_name.py` を新設：`EGOSURGERY_SERVER_NAME` 環境変数 → Hydra `logging.server_name` → `socket.gethostname()` の優先順で解決。
	- `configs/default.yaml` に `logging.server_name: bengio` を追加、`.env.example` に `EGOSURGERY_SERVER_NAME=bengio` を明記。
	- `MMDetTrainer.setup` / `PhaseTrainer.setup` で各実験フォルダに `server.txt` を記録。
	- `_init_wandb` で wandb run の tags に `server:{name}` を追加、config に `server_name` を含め W&B ダッシュボードでサーバー別フィルタ可能に。
	- `_build_eval_recipe` / `_write_metrics` で metrics.json の `eval_recipe.server_name` を併記。これにより `DeltaCalculator` は今後「同一サーバーでの測定同士」をチェックできる（§15.6 ルールに準拠）。
	- M2研究計画§14 に「### 実行マシン: bengio — egosurgery_multitask」セクションを追加し、旧 split S0 6 実験（退避）・S2 3 実験（退避）・S3 3 実験（phase_accuracy 0.593±0.008）・今後の修正後正式計測予定を明記。今後のすべての bengio 上の実験は本節に追記される。
	### 2026/05/24
	**§15「Lessons Learned & 整合性検証規則」を新設、A〜F の研究計画反映と G1〜G3 のコード改修を実施**
	S0 完走後に発覚したデータ split の取り違え（8 videos vs 論文公式 10 videos）と test_cfg の論文不一致（score_thr=0.05 vs 論文 1e-8）を契機に、Δ 評価方法論の前提条件を明文化し、再発防止策をコードと計画両側に反映した。
	- §15 を新設（関連ページの直前）：15.1 split 取り違えの根本原因とデータ証拠、 15.2 score_thr 不一致と実測影響、 15.3 再発防止策 G1〜G3、 15.4 研究計画への波及 A〜F（§2.5(a) / §7.1 / §10.1 / §13.6 / §13.1, §13.8 / §15 常設化）、 15.5 過去実験の扱い（旧 split / 旧 test_cfg は Δ 基準点使用不可）、 15.6 今後の運用ルール（DeltaCalculator の recipe 整合性検証拡張予定）を含む。
	- A. §2.5(a) S0 基準点の strict 3 条件を§15.4 で明記（公式 split / locked-down test_cfg / metrics.json の eval_recipe 一致）。
	- B. §7.1 Δ 計算の前提条件「同一 eval recipe」を§15.4 で明文化。
	- C. §10.1「1σ 以内は主張しない」の 1σ を「同一 recipe での 3-seed std」と§15.4 で限定。recipe 差由来の variance は含めず、別表として sensitivity 表を§3 に分離する視点を記載。
	- D. §13.6 標準スケジュール / 論文化時の§3 表の脚注に locked-down recipe を明記する規則を§15.4 で明記。
	- E. §13.1 / §13.8 Reproducibility 厳格化：`data/splits/ego_*.txt` を論文準拠で git 管理、`preprocess_ego.py` の assert_paper_split を起動時チェックに、`MMDetTrainer` が test_cfg を locked-down で上書きしなければならない、と§15.4 で規定。
	- F. 今後の整合性関連の発見・対処は§15 に蓄積することを§15.4 で定着。
	**G1〜G3：コードレポジトリへの反映済み（egosurgery_multitask）**
	- G1: `src/egosurgery/engines/mmdet_trainer.py::_build_mmdet_cfg` に test_cfg の locked-down 上書きを追加。全 detector・全 stage で `score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6` を強制。
	- G2: `scripts/preprocess_ego.py` に `PAPER_SPLIT_SIZES` と `assert_paper_split()` を追加（生成した instances_\*.json が論文 Table 3a と一致しなければ AssertionError）。最後に `assert_paper_split(args.output_dir, strict=True)` を呼ぶよう main() を更新。
	- G2 (付随): `data/splits/ego_train.txt` を 8 videos → 10 videos (14, 15 追加)、`ego_val.txt` を 14, 15 → 09, 10 に修正し、論文公式 split と完全一致させた。
	- G3: `MMDetTrainer._write_metrics` と新規 `_build_eval_recipe()` で `metrics.json` に `eval_recipe` field（test_cfg 全項目 + split image/annotation 数）を併記するよう拡張。
	- 退避: `experiments/baselines/_wrong_split_8_2_3/` に旧 split で学習した S0 6 実験を保存（Δ 基準点使用不可・実測記録としてのみ保存）。`data/annotations/egosurgery_tool/_wrong_split_8_2_3/` に旧 instances_*.json を保存。公式 **`tool/{train,val,test}.json`**（論文 Table 3a と完全一致 = 9657/1515/4265 images, 32272/4707/12673 annotations）を \`instances_*.json\` に置換し、統合 COCO も再生成。
	- 検証: ruff クリーン / pytest 28/28 パス / assert_paper_split が公式 split で OK / `eval_recipe` 構造を単体テストで確認済み。
	### 2026/05/23
	**§8・§10.1・§13 に各実験ステップの実行サーバー割り当てを追記**
	- §8 に「§8.0 サーバー割り当ての運用原則」を新設（RTX 6000 Ada = Δ 基準点専用、A6000 = 派生実験・基盤整備、A5000 = Exo SSL 専有、RTX 8000 = 軽量専用）。
	- §10.1 全体マッピング表に「実行サーバー」列を追加。S0〜S9 の各ステップ詳細に実行サーバーを明記。
	- §13.2〜§13.4（実験実行手順書）の各ステップに実行サーバーを追記。
	- 設計原則：Δ の分子・分母となる学習は世代の揃った単一 GPU（RTX 6000 Ada）に固定し、基準点に影響しない派生実験を A6000・A5000 に分散させることで、数値再現性と全体スループットを両立。
	**§12 サーベイ結果セクションの構造最適化（子ページ分割・目次化）**
	- §12（サーベイ結果）の本文インラインコンテンツをすべて子ページ（22件）に分割し、親ページを子ページリンクのみの軽量目次に変換した。
	- 目的：親ページのトークン消費削減（§12 が全体の50%以上を占めていたため）。
	- 各サーベイ（A1, A2, A4, B1, B5, B8, C6, E3, B2, B3, B4, B7, C1, C3, D1, D2, E2, E5, F1, C2, C4, G4）の詳細内容は対応する子ページに完全移行済み。
	### 2026/05/21
	**§13 実験実行手順書の新設と計算環境記述（§4.2・§10.1）の実環境への改訂**
	S0〜S9 を実行レベルに翻訳した実験実行手順書を §13 として新設した。あわせて、利用可能な計算環境（RTX 6000 Ada 48GB / RTX A6000×2 48GB / RTX A5000×5 24GB / Quadro RTX 8000×2 48GB）が判明したため、計画書中の A100 前提の記述を実環境に合わせて改訂した。
	- §13 を新設：§13.0 本手順書の位置づけと前提、§13.1 フェーズ I 基盤整備、§13.2 フェーズ II Phase-0 主経路（S0〜S4 実行手順）、§13.3 フェーズ III 中核検証（S5〜S6）、§13.4 フェーズ IV Exo 検証と Phase-1（S7.5〜S9、S1・S7 条件付き）、§13.5 フェーズ V 評価出力と CVPR 投稿、§13.6 標準スケジュール、§13.7 実験の 3 層分類、§13.8 GPU 割り当て。
	- §4.2：backbone fine-tuning の「QLoRA 量子化で A100 1 枚での実装を確保」を実環境（48GB 級は bf16 + 勾配チェックポイント、QLoRA はフォールバック）に改訂。Δ 基準点学習を RTX 6000 Ada に固定、Quadro RTX 8000 を bf16 非対応として基準点学習から除外する旨を明記。
	- §10.1 全体注意事項：計算コスト見積もりに GPU 割り当て（基準点 = RTX 6000 Ada、ablation・第 2 波・転移 = A6000×2、Stage B-C SSL = A5000×5 DDP、RTX 8000 = 軽量・推論専用）と、Stage B-C の Exo サブサンプリング前提を追記。
	**mask / hand-tool アノテーション不在の制約を踏まえた研究計画の 2 フェーズ化**
	現時点で術具・手の mask アノテーションおよび hand-tool 関係アノテーションが未準備であり、利用可能になるのは M2 期間内（数ヶ月後）の見込みであることが判明した。この制約を踏まえ、計画を mask 非依存の **Phase-0（bbox フェーズ）** と mask 入手で起動する **Phase-1（mask フェーズ）** の 2 フェーズに再編し、bbox + Phase ラベルのみで H1・H2・H4 を一次検証できる経路を主経路に据えた。mask を要する工程（instance segmentation・H3 関係モジュール）は計画から削除せず「mask 入手で起動する条件付きステップ」に格下げした。bbox は現時点で利用可能（EgoSurgery-Tool 想定通り）であり、mask 入手までは bbox ベースで研究を前進させ mask は入手後に統合する方針とする。
	- §0：本計画の要点に「データ可用性の前提」と 2 フェーズ構成を明記。
	- §1.2：短期ゴールを Phase-0 必達分（bbox 検出・工程認識・H1/H2/H4）と Phase-1 条件付き分（mask・hand-tool 関係・H3）に分離。
	- §2.3：H3 を「mask 入手を前提とする条件付き補助仮説」と再定義し、mask 不在時の代替（bbox-IoU からの粗い near/contact 疑似ラベル）を注記。§2.5：成功条件 (a) を bbox 版に修正。
	- §3.1：学習信号を「現時点で利用可能（bbox・Phase）」と「mask 入手後に追加」に整理。§3.3：工程不均衡の記述を維持しつつ、mask 系拡張（mask-aware/temporal-consistent copy-paste）を Phase-1 条件付きに注記。
	- §4.2/§4.3/§4.4/§4.5：検出ヘッドを bbox-only 構成で起動できるよう記述、object token の mask shape 属性を Phase-1 条件付き属性に変更、§4.4 関係モジュールを Phase-1 条件付きモジュールとして明記。
	- §5：Stage A を Stage A0（bbox）と Stage A1（mask、条件付き）に分離。§6：損失関数で L_mask・L_rel を条件付き項として明記。
	- §7：mIoU・関係 F1 を Phase-1 条件付き指標に。§8.1：A5（H3）を条件付き ablation に。
	- §9：判断ポイントに #9（mask/hand-tool アノテーション入手時の Phase-1 起動判断）を追加。
	- §10/§10.1：S1（mask 化）・S7（関係モジュール）を条件付きステップに格下げし、Phase-0 主経路（S0→S2′→S3→S4→S5→S6→S7.5→S8→S9）を確立。M1〜M5 を 2 フェーズに対応づけ。
	**§12 全 22 サーベイの批判的レビューに基づく研究方針・手法・アーキテクチャの再設計**
	2026/05/20 までに §12 サーベイ知見は本文に反映済みであったが、今回はその先の作業として、サーベイが明らかにした事実と現方針との間に残る「不整合・矛盾・撤退設計の欠落」を洗い出し、本文を更新した。優先度 高・中・低のすべてを反映。
	- 〔優先度:高〕§2.6 を新設：H1〜H4 の現象仮説に加え、方法論的貢献としての **設計仮説 D-A（object-centric token 列 + block-diagonal Mamba アーキテクチャ）・D-B（EgoSurgery-Phase 初の長距離時系列ベンチマーク）** を明文化。Δ が有意に出ない場合のフォールバックを確立。
	- 〔優先度:高〕§7.1：Δ を主指標とする方針に「Δ 非有意時のフォールバック（絶対精度 SOTA 更新 + 未ベンチマークモデルの初評価を貢献とする）」を追記。
	- 〔優先度:高〕§4.2：検出ヘッドの「Mask DINO 本命確定」を「S0 結果待ちの暫定第一候補」に格下げ。DETR 系が EgoSurgery-Tool で構造的に弱い（VarifocalNet 比 4〜16pt 劣）事実を明記し、Hungarian matching の長尾 quench 対策として **class-balanced denoising sampling を提案手法として追加**。MTLoRA の保守的フォールバック（task head 側限定）を併記。
	- 〔優先度:高〕§4.6：Phase→Detection 注入の primary/secondary を逆転し、**cross-attention 注入を primary、FiLM を軽量ベースライン/ablation 下限に再配置**。c_phase token に **entropy gating（phase 予測の不確実なフレームで注入を自動減衰）** を追加。
	- 〔優先度:中〕§4.5：S4 時系列モデルを「第 1 波（TeCNO + SR-Mamba）／第 2 波（HID-SSM 他）」の 2 段階運用に再編。SlotSSMs 風 block-diagonal Mamba と SR-Mamba を一本化し、serializer の要否を block-diagonal 採否で条件分岐。
	- 〔優先度:中〕§4.7・§9 #5：H4 の撤退ラインを 2 段階化（S7.5 予備診断での早期縮退 + S8 実測後の縮退）。§4.7 / §5 Stage B に **temporal hard negative**（同一視点内の異時刻フレームを hard negative に）を追加。
	- 〔優先度:中〕§3.3：低 fps での Copy-Paste 時系列一貫性問題に対し **temporal-consistent copy-paste** を提案手法として明記。長尾損失 ablation を独立 contribution に格上げ（§8.2）。
	- 〔優先度:低〕§5 に **Stage B′（未ラベル Exo での DINO/iBOT 継続事前学習）** を独立小節として明示。§9 判断ポイントの番号順（#4/#5）を修正。§10.1 S1 に EoMT/Mask2Former/Mask DINO の 3 ライン比較を追記、S7.5 を新設。§8.1 ablation に A7（設計仮説 D-A の検証）を追加。
	### 2026/05/20
	**全 22 サーベイを反映した研究方針・手法・アーキテクチャの更新**
	- §12 の全 22 サーベイ（特に 2026/05/20 追加の B2,B3,B4,B7,C1,C3,D1,D2,E2,E5,F1,C2,C4,G4 の 14 件）の知見を、§3・§4・§5・§9・§10 の本文に反映。
	- §3.3：クラス不均衡対策を F1 サーベイに基づき Logit Adjustment / Seesaw Loss / RFS / Simple Copy-Paste / Balanced Softmax に具体化、採用見送り手法を明記。
	- §4.2：backbone を **DINOv2 ViT-L/14-with-registers に主軸確定**（C1/E2）、Stage A の backbone 比較 ablation を明記、MTLoRA を plain ViT 用に porting + DoRA 化（heavy full FT 回避）。
	- §4.3：object token を Mask DINO query + ROI Align に確定、属性の次元を明記、slot attention を sub-stream（C4）として併走。
	- §4.4：関係モジュールを Mask DINO query をノードとする two-stage GNN（PViC + SSG-Com/MCIT-IG）に具体化、エッジ疑似ラベルの自動生成基準と HODN の stop-gradient 保護を追加（B7/B8）。
	- §4.5：S4 時系列モデル候補の優先順位を D2/C3 に基づき再編（TeCNO→SKiT→Surgformer→SR-Mamba→SPRMamba→HID-SSM）、SlotSSMs 風 block-diagonal Mamba を時系列化第1推奨に、causal/bidirectional 並行評価を明記。
	- §4.6：Phase→Detection 注入で C2 推奨の Mask DINO decoder cross-attention（c_phase token）を明記、S6 で FiLM vs cross-attention vs SAK adapter bias の 3 者比較を確定。
	- §4.7：Exo encoder を Hiera-B（VideoMAE V2 + Endo-FM warm-start）・Ego encoder を EgoVLPv2 に確定（D1）、Stage C 蒸留を Quattrocchi 2-level KD + AE2 temporal-alignment に更新（E2/E5）。
	- §5 Stage A：backbone/ヘッド/不均衡対策の具体手法を明記。Stage B：Stage B′（未ラベル Exo での DINO/iBOT 継続事前学習、E2）を追加。Stage C：Quattrocchi 逆方向適用の具体設計を明記。Stage D：Selective Task Group Updates 整合と半教師あり統合（Consistent-Teacher/SemiVT-Surge）を追加。
	- §9：判断ポイントに #6（検出ヘッド切替、C2/B2）・#7（backbone 主軸切替、C1）・#8（評価ベンチマークと Δ 指標確定、G4）の 3 項を追加。
	- §10.1：S0（モデル候補・ベンチマーク・sub-confusion matrix）・S4（時系列モデル 6 候補の優先順位）・S9（Table I/II + Supplementary の報告フォーマット、leave-one-surgeon-out）を更新。M1 に backbone 比較 ablation を明記。
	**§12 サーベイ結果セクションへの追加サーベイ C2, C4, G4 の反映**
	- §12.10〜§12.20（11 件）に加え、C2（検出/分割ヘッド）, C4（物体中心表現 / Slot Attention）, G4（手術ドメイン既存ベンチマーク）の 3 サーベイ結果を §12.22〜§12.24 として追加。いずれも §12.1〜§12.8 と同等の詳細度。
	- これにより §11 の高優先度細目のうち計 22 細目のサーベイが完了。S0〜S6 開始前に必要な高優先度サーベイはほぼ網羅。
	- §12.21 横断的知見を全 22 サーベイ版へ更新（新規性フックに phase トリガの query 条件付け・detector→SSM token 設計・三位一体ベンチマーク不在と Δ 指標未標準化の 3 点を追加、実装推奨に検出ヘッド・物体中心表現・評価ベンチマークを追加）。
	- §12 冒頭の導入文を 22 サーベイ構成に合わせて改訂。
	**§12 サーベイ結果セクションへの追加サーベイ 11 件の反映**
	- §11 サーベイロードマップのうち、2026/05/18 実施分（A1, A2, A4, B1, B5, B8, C6, E3）に加えて実施済みであった 11 細目のサーベイ結果を §12.10〜§12.20 として追加。対象は B2（術具検出）, B3（手検出・手姿勢推定）, B4（セグメンテーション）, B7（HOI）, C1（空間 backbone）, C3（時系列モデル）, D1（短期時間モデリング）, D2（長距離時間文脈）, E2（事前学習・Foundation Models）, E5（半教師あり学習）, F1（クラス不均衡対応）。
	- 各サーベイは §12.1〜§12.8 と同等の詳細度（調査範囲・主要手法の分類・代表的論文・研究ギャップ・本研究への示唆/採用方針）で記載。
	- これにより §11 の高優先度細目のうち計 19 細目のサーベイが完了。
	- 旧 §12.9（サーベイ横断的知見）を §12.21 に後送し、19 サーベイ全体を反映する内容へ更新（新規性フック 6 点の根拠サーベイを追補、実装・手法選定の横断的推奨を時系列モデル・segmentation ヘッド・PEFT 等で更新）。
	- §12 冒頭の導入文を 19 サーベイ構成に合わせて改訂。
	### 2026/05/19
	**§12 サーベイ結果セクションの新設**
	- 2026/05/18 に実施した 8 つのサーベイ（A1, A2, A4, B1, B5, B8, C6, E3）の詳細な結果を §12 として追加。
	- 各サーベイについて、調査範囲・主要手法の分類・代表的論文・研究ギャップ・本研究への具体的示唆を記載。
	- §12.9 にサーベイ横断的知見（新規性のフック 6 点 + 実装・手法選定の横断的推奨）を追加。
	**サーベイ結果に基づく研究方針の更新**
	- §4.2：backbone を **DINOv2（ViT-L/14）を第一候補**に確定（B1/E3 サーベイ）。MTLoRA による低ランク適応を追加（C6）。Co-DETR / DDQ-DETR の知見活用を明記。
	- §4.5：時系列モデル候補にサーベイに基づく優先順位を反映。TeCNO をベースライン、LoViT / SKiT を精度上限探索、SR-Mamba / HID-SSM を SSM 系候補として再編（B5）。
	- §4.6：Phase → Detection 注入の FiLM を primary、cross-attention を secondary として確定。SAK（ICLR 2025）の adapter bias 構想を追加（C6）。
	- §4.7：Exo 補助経路に 3 層構造（Exo 単独 SSL → 視点間 SSL → Ego-Exo 整合蒸留）を明記。fps 差への対処、branch-pruning 後の検証を追加（A4/E3）。
	- §5 Stage B：VideoMAE v2 + hand-tool-guided MAE + playback speed + temporal order + cross-view contrastive + view dropout の具体構成を確定（E3/A4）。
	- §5 Stage C：fps 差対処（Ego 1 フレームに Exo 25 フレームクリップ）、feature matching + KL の蒸留具体手法、SAK multi-teacher 統合の知見を確定（E3/A4/C6）。
	- §5 Stage D：FAMO + DB-MTL 対数変換を損失重み付けの第一候補として確定。GCond の勾配蓄積メカニズム、LibMTL の Δp 監視を追加（C6）。
	- §8.2：損失重み付け 5 条件 ablation、hand-tool-guided MAE vs random mask、FiLM vs cross-attention vs adapter bias、時系列モデル 4 候補比較を追加（C6/E3/B5）。
	- §9：H4 の撤退ライン（S8 でΔが 1σ 以内なら Exo を Phase label 転写のみに縮退）を #5 として追加（A4）。
	### 2026/05/18
	**ページ名変更と変更履歴セクションの新設**
	- ページ名を「研究方針_2026/05/18」→「**M2 研究計画**」に変更。本ページは M2 期間のマスタードキュメントとして運用する。
	- §0 として本「変更履歴」セクションを新設。以降の編集はすべてここに記録する。
	**§11 サーベイロードマップの新設**
	- 7 大分類(ドメイン / タスク / アーキテクチャ / 時間モデリング / 学習パラダイム / 学習信号設計 / 評価・ベンチマーク) × 約 45 細目。
	- 各細目に本研究での位置づけ(参照 § / 関連 H / 関連 S)と優先度(高/中/低)を併記。
	- S0〜S9 と連動した実施順序表と、除外分野(腹腔鏡・ロボット etc)、運用指針を含む。
	**§10.1 詳細検証ロードマップ(S0〜S9) の新設**
	- M1〜M5 を 10 ステップに細分化、各ステップで動かす軸を 1 本に絞り H1〜H4 を独立検証可能に。
	- 軸の凡例(タスク / 空間 / 時系列 / 方向性 / 関係 / 視点)、全体マッピング表、ステップ別詳細(目的/比較対象/主要指標/期待/失敗時対応/注意)、依存関係の根拠、全体注意事項を含む。
	**H4 の追加と仮説体系の再整備**
	- 補助仮説 **H4**(Exo 多視点 view-consistent SSL による Ego への動作・時間表現注入)を §2.4 に新設。
	- **H1 / H2 の wording を再定義**:H1 を「形状類似・遮蔽・クラス不均衡」の 3 failure mode に明示対応、H2 を「object-centric temporal representation vs global image feature」として明確化。
	- §2.5 成功条件に **(c) Exo SSL 無しの提案モデル** を追加(3 比較対象に拡張)。
	- §7.1 評価指標に H4 検証指標(Δ の上限引き上げ効果)追加、§8.1 Ablation **A6**(Exo SSL on/off)追加。
	- §8.2 補助 ablation に view-consistent SSL 構成要素分解と関係モジュールエッジ特徴選択を追加。
	- §10 M4 を H4 主検証ポイントに昇格、§9 #3 トリガーに H4 検証結果と view-consistent SSL を明示。
	- §4.1 設計思想を H1 / H2 / H3 / H4 の 4 経路に拡張、§4.7 を「H4 実現経路」として再定義。
	- §5 Stage D で「Stage B/C で獲得した Exo 由来の表現も統合」と明示。
	**中核仮説(H1 / H2 / H3)と双方向補完の確立**
	- §2 中核仮説セクションを新設(H1: Phase → 術具検出改善、H2: 術具検出 → Phase 改善、H3: 関係モジュールが両者を増幅)。
	- §2.5 成功条件として **(a) 術具検出単独モデル**、**(b) 工程認識単独モデル** を並置。
	- §4.1 設計思想「タスク間の相互補完を中核に据える」を独立節として確立。
	- §4.6 双方向補完を「中核モジュール」として拡張、FiLM / cross-attention 注入、stop-gradient、Ablation 容易性を明示。
	- §7.1 主要指標として「**相互改善幅(Δ)**」を新設(Δ mAP \> 0、Δ Phase F1 \> 0 を成功条件化)。
	- §8.1 中核 ablation A1〜A5 として H1 / H2 / H3 検証を再編。
	- §10 M1〜M5 マイルストーンに各検証仮説を紐付け。
	**初版作成**
	- 2026/05/14 ページの内容と MTG 結論を反映した初版を作成。
	- 動作ラベル方針:現段階では追加せず、既存 EgoSurgery 系アノテーションのみで「術具・手・工程の同時理解システム」を構築。
	- Exo 映像:アノテーションなし、学習補助のみ、推論時 Ego 単独。
	- §0〜§10(マイルストーン M1〜M5)の初期構成を確立。
---
## 研究方針の現在地（2026-06-14 更新）— タスク結合提案へのピボットと「分析ファースト」
本セクションは、§2（中核仮説 H1〜H4）以降の旧フレームに対する**現時点の最新サマリ**であり、ここが現在のコア主張・進め方の入口である。以下の §1〜§16 は H1〜H4「相互改善」フレームに基づく記述を多く含むが、それらは**経緯・実験運用ルール・サーベイ知見の記録**として保持する。正本は [§13 研究方針再構成](https://app.notion.com/p/36dee4d4777781788e8accde3fd966a6) と §2.5(b) 工程認識ベースライン設計 §7。
### 現在のコア主張：タスク結合の原理提案
指導教員コメント（①テーマが広すぎる／②組み合わせ発見からの脱却・新しい仮説／③ベースラインを絞りすぎない／④ドメイン独自性）を受け、研究のコアを「最良の組み合わせ発見」から**タスク結合の原理提案**へ転換した（§13、2026-05-28）。当面は**術具検出 × 工程認識の 2 タスク結合**に焦点を絞る。
### 研究順序：分析ファースト〔2026-06-14 確定〕
新結合手法を先に発想するのではなく、**既存のタスク結合手法を複数試す → 単一タスクとの精度差(Δ)がなぜ生じる/生じないかを分析する → その観察から結合仮説を立てる**順序を採用する。これは「既存結合を試さずに新結合を発想している」という方法論上の弱さを解消するための転換である。§13 の新結合仮説（**H-C** 不確実性駆動の双方向結合／**H-A** トリプレット畳み込み／**H-H** ラベル効率結合）は「先に 1 つ賭けるコア仮説」から「**STEP C の観察で選ぶ/作り直す仮説プール**」に格下げする。
**なぜ分析ファーストが強いか**：(1) 仮説の出所が「観察」になり査読で評価される motivation が強い、(2) 異粒度（検出 × 工程）の negative transfer を実測して初めて「いつ繋ぐかを動的制御する」必要性が示せる、(3) 最悪でも既存結合の異粒度・open surgery 挙動の体系的分析が貢献になる（§2.6 二段構えと整合）。
### 進め方：STEP A–D
<table fit-page-width="true" header-row="true">
<tr>
<td>STEP</td>
<td>内容</td>
<td>状態</td>
</tr>
<tr>
<td>**A**</td>
<td>単一タスク基準点を確定（検出 **S0-frozen** ＋ 工程 **S4** を同一凍結 backbone 上で）</td>
<td>ほぼ設計済（§2.5(b) §3.4・§4.2）</td>
</tr>
<tr>
<td>**B**</td>
<td>既存結合を「複数」実装し Δ を測る（共有エンコーダ MTL → 片方向 → PAD-Net 等、6 手法・4 層）</td>
<td>**いま着手**</td>
</tr>
<tr>
<td>**C**</td>
<td>Δ が出た/出ない理由を分析（per-class・工程境界・negative transfer・タスク自信の相補性）</td>
<td>—</td>
</tr>
<tr>
<td>**D**</td>
<td>観察から結合仮説を立てる（§13 候補を「この観察への解」として選ぶ/作り直す）</td>
<td>—</td>
</tr>
</table>
※ STEP D で立てた仮説は STEP B の比較群に「新手法」として戻し、同一土台で検証する（探索と検証が地続き）。STEP B の比較群は 4 層から選定：共有エンコーダ MTL〔必須・最初〕／片方向 pipeline〔必須〕／PAD-Net・MTI-Net 予測蒸留〔主要〕／MT4MTL-KD・SSG-Com ドメイン SOTA〔主要〕／Cross-Task Consistency〔余力〕／Cross-stitch・MTAN〔参考〕。勾配系（PCGrad/CAGrad/FAMO）は併用アドオンで主軸に置かない。
### 着手前の最優先ブロッカー（2 つ）
1. **eval recipe の公式一本化**（locked-down か score_thr=0.0 系か）。Δ の土台。失敗知見「S0 eval recipe 2 系統分裂」（P1・open、§8.-1/§15 と関連）。決定的な一手は 1 モデルを両 recipe で再 eval して Δ_recipe の実測値を出すこと（再学習不要）。
2. **凍結源 backbone の確定**（暫定 Relation-DETR）。これで S0-frozen / S4 / 結合手法が同一土台に載る。
### 実験の現状（旧 §13 ロードマップとの差分）
- **検出ベースライン**：旧 §13・§16 は「S0 で VarifocalNet 45.8 超え」を完了判定とする枠だったが、実際には **DETR 系 10 モデルを実測完了し、Relation-DETR が mAP 0.730（3-seed 平均 0.727、σ0.004、AP_rare 0.758）で 1 位**。README 旧値（maskdino 0.327）は更新済。§16 の VFNet 0.618 は旧 recipe での途中値で、現行の主基準は DETR 系上位群。
- **工程ベースライン**：S4 単独ベースライン設計を 2026-06-02 に確定（online／ResNet-50 凍結／コア=TeCNO ＋ SKiT・SPRMamba 必達／§2.5(b)）。実装はこれから。
- **比較の土台**：backbone 凍結方針に伴い、Δ_detection の分母は既存 S0(fine-tune) ではなく新設の **S0-frozen**（凍結 backbone ＋ 検出ヘッド、§2.5(b) §4）。
### 旧フレーム（H1〜H4）の位置づけ
- **H1（工程→検出）・H2（object-centric 表現→工程）** は、タスク結合で「何が改善するか」の予測として**結合仮説の検証対象に内包**される（H-C 等はその実現機構）。§7.1 の Δ 指標体系はそのまま使える。
- **§1〜§16 の実験運用ルール**（eval recipe 整合・公式 split・DDP・長尾対策・S2 catastrophic forgetting・S3 class weight 崩壊の知見、§8/§10.1/§15/§16）はフレーム転換後も**そのまま有効**。
- **H3（手-術具関係・mask 依存）・H4（Exo 多視点 SSL）** は当面のコアから外し、2 タスク結合の確立後に検討する（§0.1 Phase-1 と整合）。
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
	- **Phase-0（bbox フェーズ、現時点で全面実行可能）**：bbox 検出 + Phase ラベルのみで、中核仮説 **H1・H2・H4** と方法論的貢献 **D-A・D-B** を一次検証する。object token は bbox 由来の特徴（ROI Align + bbox 位置 + クラス埋め込み）で構成し、mask shape 属性を使わずに H2 を成立させる。これが本計画の **主経路** である。
	- **Phase-1（mask フェーズ、mask / hand-tool アノテーション入手で起動する条件付き）**：mask 入手後に instance segmentation（旧 S1）と H3 関係モジュール（旧 S7）を追加起動する。mask 由来の属性・関係疑似ラベルで object token を強化し、H3 を検証する。mask は M2 期間内（数ヶ月後）に入手できる見込みであり、入手時点で Phase-1 を Phase-0 の上に統合する。万が一 mask が M2 期間内に入手できない場合でも、Phase-0 だけで H1・H2・H4・D-A・D-B により研究と論文が成立するよう設計する。
	- この 2 フェーズ構成は §2.6 のフォールバック思想（Δ 非有意時も D-A・D-B で論文成立）と同じ設計原理であり、**「不確実な前提に依存する部分（mask）を条件分岐に隔離し、確実な前提（bbox・Phase）の上に主経路を組む」** ことでデータ準備リスクを構造的にヘッジする。
---
## 1. 研究のゴール {toggle="true"}
	### 1.1 最終ゴール(長期)
	開放手術の一人称視点(Ego)映像から、**術具・手・工程・動作・関係性**を AI が同時に認識するシステムの構築。
	### 1.2 短期ゴール(現フェーズ、本方針のスコープ)
	**現時点で利用可能なアノテーションを主軸に、Ego 映像から以下を同時認識する基盤モデルを構築する。タスクを §0.1 の 2 フェーズに対応させて明示する〔2026/05/21 再編：mask / hand-tool アノテーション不在の制約を反映〕。**
	- **Phase-0（bbox フェーズ、現時点で全面実行可能、本計画の必達分）**
		1. 術具の検出・分類（15 クラス、**bbox**）
		2. 手の検出・分類（4 クラス：own/other × left/right、**bbox**）
		3. 手術工程（9 クラス、フレーム単位、long-range time series）
		4. 上記を統合したマルチタスク認識と、H1（工程→検出改善）・H2（object-centric 表現→工程認識改善）・H4（Exo SSL による上限引き上げ）の検証。bbox 由来の object token で H2 を成立させる。
	- **Phase-1（mask フェーズ、mask / hand-tool アノテーション入手で起動する条件付き分）**
		1. 術具・手の **mask**（instance segmentation、mask アノテーション入手で起動）
		2. 手と術具の接触・把持関係（hand-tool 関係アノテーションまたは mask 重なりからの自動生成、H3 を検証）
	- **フェーズ間の依存関係**：Phase-1 は Phase-0 の上に積み上げる増分であり、Phase-0 単独でも研究として成立する（§2.6 D-A/D-B と H1/H2/H4）。mask 入手時期に応じて Phase-1 を起動し、未入手のまま M2 を終えるシナリオでも論文が成立する。
	### 1.3 短期ゴールに含めないもの
	- 動作(Action / Primitive / Gesture)レベルの認識:今フェーズではスコープ外。
	- Exo 映像へのアノテーション付与:行わない。
	- 推論時の Exo 利用:行わない(Ego only inference)。
---
## 2. 研究の中核仮説 {toggle="true"}
	本研究は単に「複数のタスクを同時に解く」ことを目的とするのではなく、**タスク間の相互改善**を出発点としている。これまで術具 bbox アノテーションのみを用いた術具検出に取り組んできた経緯を踏まえ、**主仮説 H1 / H2**(対称的なタスク間相互改善)、**補助仮説 H3**(関係モジュールによる増幅)、**補助仮説 H4**(Exo 多視点 SSL による上限引き上げ)の計 4 本を中核に据える。
	### 2.1 H1:工程文脈の検出器フィードバックが、形状類似・遮蔽・クラス不均衡の強い open surgery 術具検出を改善する
	> **工程(Phase)文脈を検出器にフィードバックすることで、形状類似・遮蔽・クラス不均衡が強い open surgery の術具検出を改善できる**。すなわち、これまでの bbox 単独学習を上回る術具検出精度が得られる。
	根拠:
	- 開放手術では、ある工程で出現する術具は強く偏る(例:Dissection では剥離系、Closure では縫合系)。Phase 文脈は **事前分布** として検出器の予測を絞り込み、特に**クラス不均衡**の極端な稀少クラス(Skewer 0.7%、Syringe 1.17%)で誤分類を抑えられる可能性が高い。
	- **形状類似**の術具(例:Forceps / Tweezers / Needle Holders)は静的な視覚特徴だけでは区別が難しいが、工程文脈を補えば識別可能性が高まる。なお Forceps は 12.21% でトップ 3 に属する頻出クラスだが、頻出であっても形状類似による混同は工程文脈なしには解消困難である。
	- **遮蔽**が頻発する開放手術では、見た目の特徴だけで検出を確定するのは脆弱だが、工程文脈は遮蔽下でも候補絞り込みに寄与する。
	- これまでの bbox 単独学習で残っていた「稀少クラスの取りこぼし」「形状類似ペアの混同」「遮蔽による検出失敗」を直接ターゲットできる。
	### 2.2 H2:object-centric temporal representation が global image feature より工程認識に有効である
	> **open surgery の工程認識には、画像全体特徴(global image feature)よりも、手・術具・それらの相互作用に基づく object-centric temporal representation が有効である**。すなわち、物体中心の時系列表現を Phase head の主入力とすることで、global feature 単独の工程認識モデルを上回る精度が得られる。
	根拠:
	- Phase は本質的に「誰が何の術具で何をしているか」の集約であるため、画像全体の抽象特徴より、**術具・手の構成・相互作用の方が判定根拠として直接的**である。
	- Dissection / Closure は全体の約 8 割を占める長尺工程であり、工程境界の検出は画像特徴の差分だけでは弱い。**術具集合と手-術具相互作用の遷移**は明確な境界信号となる。
	- 物体中心表現は global feature と相補的であり、global feature が捉える「術野全体の様相」と組み合わせて使うことで一段強くなると期待できる(本研究では物体中心表現を主、global feature を副とする)。
	### 2.3 補助仮説 H3（条件付き）:関係モジュールは H1 / H2 双方を増幅する〔mask 入手を前提とする条件付き仮説、§0.1 Phase-1〕
	> 手-術具の **関係モジュール**(grasp / near-contact / handover / two-hand manipulation)は、単なる物体共起では得られない意味的中間表現を提供し、H1・H2 双方の改善幅を増幅する。
	根拠:
	- 「Tweezers がフレームにある」より「右手が Tweezers で把持している」の方が phase の判定に強い手掛かりを与える。
	- Hand-Tool セグメンテーションから自動派生できるため、**関係ラベルの明示アノテーション無し**で導入可能である。
	- **検証の前提と条件付け〔2026/05/21 追加〕**：H3 の検証は mask アノテーション（およびそれから自動生成する hand-tool 関係疑似ラベル）を前提とするため、H3 は **§0.1 Phase-1 で起動する条件付き補助仮説** と位置づける。mask が M2 期間内に入手できない場合、H3 は本論文の中核主張から外し、Phase-0 の H1・H2・H4 と §2.6 D-A・D-B で論文を成立させる（§2.6 フォールバックと同じ設計原理）。したがって H3 は「入手できれば上乗せする補強仮説」として保持し、主張の成否を H3 に依存させない。
	- **mask 不在時の暖身（任意）〔2026/05/21 追加〕**：mask を待つ間も、bbox の重なり（bbox-IoU）・中心距離・包含関係から **粗い near-contact 疑似ラベル** を生成し、関係モジュールのパイプライン動作確認と予備実験に使うことはできる。ただし bbox は grasp と near-contact の分離が原理上困難（bbox 重なりだけでは接触を確定できない）なため、H3 の本格検証は mask 入手後とする。
	### 2.4 H4:Exo 多視点 view-consistent SSL は、Ego 単独では獲得困難な動作・時間表現を獲得できる
	> **アノテーションのない 25 fps Exo 多視点映像を、同期情報に基づく view-consistent self-supervised learning に使うことで、低 fps(0.5 fps)の Ego 一人称映像だけでは学習しにくい動作・時間表現を獲得できる**。これを Ego モデルに転写することで、H1 / H2 の改善幅をさらに拡大する。
	根拠:
	- Ego は 0.5 fps と時間解像度が低く、フレーム間の運動・速度・連続性が直接観測できない。対して Exo は 25 fps(50 倍)で同時刻の手元運動・術具操作を密に捉えている。
	- 5 視点の同期映像は、**view-consistent contrastive**・**cross-view masked prediction**・**同時刻 Ego-Exo 整合**の正例ペアを大量に生成できる。これらは無アノテーションでも有効な学習信号となる。
	- view-consistent SSL によって獲得した動作・時間表現は、teacher–student 蒸留や Phase ラベル転写を経由して Ego に注入できる(§3.2、§4.7、§5 Stage B / C 参照)。
	- **推論時は Ego 単独で動作する**制約と矛盾しない:Exo はあくまで**訓練時のみの表現学習リソース**として扱う。
	### 2.5 仮説と研究方針の対応(成功条件)
	H1 / H2 は「**マルチタスクモデルが、単一タスク特化モデルを上回る**」という主張に集約される。H3 はそれらの**増幅**、H4 はそれらの**上限引き上げ**に位置づく。したがって本研究の成功条件は以下のとおり明確化される。
	- **(a) 術具検出単独モデル**（bbox のみで学習した Mask DINO / VarifocalNet。mask 入手後は bbox + mask 版も併記、§0.1 Phase-1）
	- **(b) 工程認識単独モデル**(画像 global feature を入力とした TeCNO / LoViT)
	- **(c) Exo SSL 無しの提案モデル**(H4 検証用の対照)
	を **3 つの主要比較対象として並置** し、(a) と (b) は **両方を上回る**こと、(c) との比較で **Exo SSL による Δ の増幅**が観察されることをマイルストーンとする。これらの比較は Phase-0（bbox）で全面実行可能である。単独タスクの絶対精度は副次指標とし、Δ(改善幅)を主指標とする(§7 参照)。
	### 2.6 方法論的貢献としての設計仮説（D-A / D-B）〔§12 サーベイ反映：C3/C4/D2/G4 の批判的レビューで新設〕
	H1〜H4 はいずれも「〜が改善する」という **現象仮説**であり、検証には Δ を統計的に有意に示す必要がある。しかし EgoSurgery は 21 動画・8 術者・1 施設と小規模であり（§12.24 G4）、Δ の variance が大きく「Δ が 1σ 以内なら改善と主張しない」基準（§10.1）に照らすと、現象仮説のみに依存すると研究が成立しないリスクが構造的に存在する。そこで、Δ の有意性に依存しない **方法論的貢献（アーキテクチャ貢献・ベンチマーク貢献）** を H1〜H4 と並ぶ中核として明文化する。
	- **設計仮説 D-A（object-centric token × block-diagonal SSM アーキテクチャ）**：検出器由来の object token 列を、slot ごとに独立に時間発展させる block-diagonal Mamba（SlotSSMs 風）で処理する設計は、open surgery Ego の長距離工程認識に有効なアーキテクチャである。§12.15 C3・§12.17 D2・§12.23 C4 が一致して「検出器出力 token 列を後段 SSM/Mamba に流す分離型設計は surgical も general video も SlotSSMs 以外に未報告」と確認しており、H1/H2 の「相互改善」よりも defensible な novelty となる。検証は §8.1 A7 が担う。
	- **設計仮説 D-B（EgoSurgery-Phase 初の長距離時系列ベンチマーク）**：Surgformer / LoViT / SR-Mamba / SKiT / MuST / HID-SSM は EgoSurgery-Phase で未評価であり（§12.17 D2）、これらの初ベンチマーク自体が publishable な貢献となる。
	- **フォールバックの位置づけ**：仮に H1/H2 の Δ が有意に出なくても、D-A（初の object-token×SSM surgical アーキテクチャ）と D-B（初の EgoSurgery-Phase 長距離ベンチマーク）によって論文が成立する二段構えとする。これにより、H1〜H4 を主張しつつも、小規模データで Δ が有意差に達しないシナリオに対するリスクヘッジを確保する。
---
## 3. データ運用方針 {toggle="true"}
	### 3.1 Ego 映像(EgoSurgery 系)
	- 仕様は `研究方針_2026/05/14` の表に準拠(Train 10 / Val 2 / Test 3、0.5 fps)。
	- **現時点で利用可能な学習信号（Phase-0 主経路）**：
		- 術具 **bbox**（`EgoSurgery-Tool`、15 クラス）
		- 手 **bbox**（`EgoSurgery-Tool`、4 クラス：own/other × L/R）
		- 工程ラベル 9 クラス（`EgoSurgery-Phase`）
	- **mask / hand-tool アノテーションの状況〔2026/05/21 晠明記〕**：術具・手の **mask（instance segmentation）** および **Hand-Tool セグメンテーションから派生する手-術具関係** は、現時点で未準備であり、入手時期も不確定である。これらは **§0.1 Phase-1 で起動する条件付き学習信号** として扱い、mask 入手を待って instance segmentation（旧 S1）と H3 関係モジュール（旧 S7）に供給する。Phase-0 の主経路は mask を一切要求しない。
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
		- **検証推奨**（S5〜S6 ablation）:EQLv2 vs Seesaw vs Logit Adjustment の直接比較。これらの長尾損失・サンプリング・拡張の系統的比較は、F1 サーベイで「手術・Ego 映像での標準長尾損失の系統的ベンチマークが不在」と確認されたため、**それ自体を独立した contribution**（手術 Ego マルチタスク設定での初の長尾手法ベンチマーク）として §8.2 に位置づける。長尾損失・サンプリングの比較は bbox だけで実行できるため Phase-0 に属する。
		- **採用見送り**:Focal Loss 単独（頻度を直接扱わず弱い）、naive Class-Balanced Sampling 単独（backbone 表現を劣化）、DINOv2 の heavy full fine-tuning（LIFT が tail-class 悪化を示す—LoRA/Adapter 必須）、CutMix を形状類似ペアに直接適用（混同悪化、Remix を検討）、フレーム独立な naive Copy-Paste（上記 temporal-consistent 版で置換）。
	- 工程:Dissection 44.1% + Closure 34.3% で約 8 割。
		- Balanced Softmax（TeCNO/SR-Mamba の工程ヘッド）、temporal smoothing による境界正則化、LoViT 風 Asymmetric Gaussian heatmap の工程遷移 prior。
		- **class weights の実装上の注意〔2026/05/24 追加、§14 と整合〕**：§14 で S3 の Phase head に class weights を不適切に与えた結果、val accuracy が 0.5% に崩壊した実例がある。逆頻度ベースの class weight は、極端な値（Dissection と稀少工程の頻度比が大きい）が学習を不安定化させうる。Phase ヘッドの class weight はデフォルト無効とし、有効化する場合も weight の最大/最小比を上限（例 10 倍）でクリップする。label smoothing（0.1）は安定化のため常に併用する。Balanced Softmax を使う場合も同様に極端な補正を避ける。
---
## 4. アーキテクチャ設計 {toggle="true"}
	### 4.1 設計思想:タスク間の相互補完を中核に据える
	本アーキテクチャの中核は、§2 の H1 / H2 / H3 / H4 を実現する **双方向情報フロー + Exo 補助経路** である。すなわち:
	- **Detection → Phase(H2 実現経路)**:術具・手の object token を集約した**物体中心の時系列表現(object-centric temporal representation)**を Phase head の主入力とする。画像 global feature 単独ではなく、object-centric な構成・相互作用こそが工程の判定根拠であるという立場を取る。
	- **Phase → Detection(H1 実現経路)**:Phase 予測 / Phase embedding を detection head に戻し、検出ロジットおよび object query を refine する。工程文脈を事前分布として用い、bbox 単独学習で取り切れなかった**形状類似・遮蔽・クラス不均衡**の難ケースを救う。
	- **Relation as amplifier(H3 実現経路)**:手-術具の関係モジュールが両者の間に挟まり、単なる検出共起ではなく **意味的構成** を Phase head へ伝達する。
	- **Exo SSL as upper-bound lifter(H4 実現経路)**:Exo 多視点の view-consistent SSL によって動作・時間表現を獲得し、teacher–student 蒸留と Phase ラベル転写を経由して Ego モデルへ注入する。推論時は Ego 単独で動作する。
	この構成を成立させるため、共有 backbone の上に「物体中心表現 → 関係 → 時系列 Phase」という縦の流れと、「Phase embedding → detection refine」の横のフィードバックを併設し、別系統として **Exo encoder + 同時刻整合 + 蒸留** を訓練時のみ並走させる。短期ゴールに対応するアーキテクチャは、**共有空間 backbone + 物体中心表現 + 関係モジュール + 時系列 Phase head + 双方向フィードバック + Exo 補助経路(訓練時のみ)** の構成とする。
	### 4.2 空間 backbone（Ego 入力）〔§12 サーベイ反映：C1/E2/B1/B4/C2 で更新〕
	- 共有 backbone は **DINOv2 ViT-L/14-with-registers を主軸採用として確定**する（C1/E2 サーベイ）。register token 4 個で高ノルム artifact patch を除去でき、形状類似ペア（Forceps / Tweezers / Needle Holders）の識別と Mask DINO の小物体 mask 品質に効く。vanilla DINOv2 からの drop-in 置換で訓練コストは増えない。Swin-Transformer を計算コスト重視の代替候補として維持し、ConvNeXt は優先度を下げる。DINOv3 の distilled 重みが揃い次第 Stage A の ablation に追加する。
	- **Stage A の必須 ablation として backbone 比較表**（DINOv2 ViT-L vs ViT-B vs SurgeNetXL CAFormer-S18 vs EndoViT ViT-B vs Swin-L）を作成する。C1 サーベイで、開放手術 × Ego × 0.5 fps × multi-task の交差領域に foundation backbone 比較研究が皆無であり、DINOv2 ViT-L vs SurgeNetXL の直接数値比較が文献に存在しないことが判明したため、この ablation 自体が C1 の中核 contribution となる。
	- backbone fine-tuning は **heavy full fine-tuning を回避**し（F1 サーベイ：LIFT が「heavy fine-tuning hurts」＝tail-class 悪化を示す）、**MTLoRA を plain ViT 用に porting** して採用する。MTLoRA 原論文は階層 Swin 専用のため ViT-L への移植は本研究の貢献余地となる（C1/E2）。各 LoRA は DoRA（ICML 2024 Oral）で magnitude + direction 分解により強化する。**実行環境は RTX 6000 Ada（48GB）/ RTX A6000×2（48GB）/ RTX A5000×5（24GB）/ Quadro RTX 8000×2（48GB）であり〔2026/05/21 更新：旧記述「QLoRA 量子化で A100 1 枚での実装を確保」を実環境に合わせて改訂〕、48GB 級 GPU（RTX 6000 Ada / A6000）では DINOv2 ViT-L/14 + ViT-Adapter + Mask DINO を bf16 + 勾配チェックポイントで実行できる見込みであり、QLoRA 量子化は VRAM 不足時のフォールバックとする。24GB 級（A5000）単体で ViT-L を扱う場合は QLoRA + 勾配チェックポイントを併用する。Δ の基準点を作る学習（S0・S4・S5・S6）は世代の揃った単一 GPU モデル（RTX 6000 Ada を第一候補）に固定し、数値再現性を担保する。Quadro RTX 8000 は bf16 非対応（Turing 世代）のため、基準点学習には用いず軽量実験・推論評価・前処理に限定する。** MTLoRA-style の task-specific 低ランク枝は task head 側に限定するのが清潔（E2）。**保守的フォールバック（2026/05/21 追加）**：plain ViT への MTLoRA 移植が不安定な場合は、backbone を一度 LoRA-Q/V + 最終 2〜6 block のみ解凍し、MTLoRA-style の task-specific 低ランク枝を task head 側に限定する構成に退く（E2 サーベイ推奨の清潔な配置）。
	- 検出/分割ヘッドは **Mask DINO 系**（query ベースで box + mask を統一表現）を **S0 結果待ちの暫定第一候補**とする〔2026/05/21 格下げ：「本命確定」→「暫定第一候補」〕。C2 サーベイで、object token 共有・時系列接続容易性・phase 条件付け適性のいずれもで統合ヘッドが分離ヘッドを上回ることが確認され、アーキテクチャとしては Mask DINO が有力である。**ただし「本命確定」としない理由**：B2 サーベイが EgoSurgery-Tool 上で **DETR 系は構造的に弱い**ことを実証している（Deformable-DETR 30.0 \< DINO 39.7 \< DDQ 43.2 \< VarifocalNet 45.8、すなわち dense detector に 4〜16pt 劣る）。これは Hungarian matching の one-to-one マッチングが稀少クラスの query を早期に quench する構造的バイアスによると示唆されており、Mask DINO も DETR 系である以上同じリスクを背負う。よって **Mask DINO を本命と確定するのは S0 で Mask DINO（+ 長尾対策）が VarifocalNet を実際に上回った後とし、それまでは暫定位置づけに留める**。長尾 quench への直接対策として **class-balanced denoising sampling を提案手法として追加する〔2026/05/21 追加〕**—Mask DINO の denoising クエリ生成時に、GT ラベルのクラス頻度に反比例したサンプリング重みで稀少クラス（Skewer/Syringe）の noised GT クエリを優先的に水ましし、Hungarian マッチングの手前で稀少クラスに十分な勾配信号を与える（C2 サーベイで「30 倍長尾×15 クラスには class-balanced denoising sampling が必要だが未確立」と指摘された未開拓領域）。Co-DETR（ICCV 2023）を長尾耐性の対照候補、VarifocalNet + Mask2Former 完全分離ヘッドを撤退候補とする。再現性の高いベースラインとして **VarifocalNet（det）**を必ず並走させる（B2 サーベイ：EgoSurgery-Tool の実質 SOTA は VarifocalNet AP 45.8 であり、A1 でこれに勝てなければ主張が成立しない）。
	### 4.3 物体トークン抽出〔§12 サーベイ反映：C4/B4 で更新、2026/05/21 に mask 属性を Phase-1 条件付きに分離〕
	- 検出された各術具・手インスタンスから、**Mask DINO の object query 最終層出力**と ROI Align ベクトルを連結して **object token** を作成する（C4 サーベイ主推奨）。H2 の主張は「class / instance ID が事前定義された手・術具の物体中心表現が phase 認識に有効」であり、supervised な検出器ベース object token がこの仮説と最も整合する。
	- **object token の 2 フェーズ構成〔2026/05/21 再編：mask / hand-tool 不在の制約を反映〕**：
		- **Phase-0（bbox フェーズ、現時点で実行可）**：object token = \[visual feature (256), class embedding (64), bbox position (8), confidence (1), hand identity (2)\]。mask shape 属性を含まず、ROI Align + bbox 位置だけで H2 を成立させる。線形射影で d = 256〜512 に統一する。
		- **Phase-1（mask フェーズ、mask 入手で起動）**：mask 入手後に mask shape (64) と mask pooling ベクトルを object token に追加する。mask shape 属性の追加によるΔ Phase F1 は Phase-1 の ablation として計測する（§8.2）。
	- いずれのフェーズでも、各フレームで Max_K 個（8〜16：術具最大 3 + 両手 2 + scene slot 3〜11）の object token を抽出する。未検出スロットには learnable \[PAD\] token を割り当て、self-attention mask で除外する。
	- **slot attention を sub-stream として併走**させる（C4 サーベイ）。DINOv2 ViT-L/14 特徴上で VideoSAURv2 / SlotContrast 風の unsupervised slot attention を走らせ、(a) 検出器の miss 領域を補完する scene slot、(b) H2 の ablation 対照（unsupervised slot vs detector-based object token）、(c) 弱教師事前学習の pretext として用いる。**slot attention は mask アノテーションを要さず、Phase-0 でも実行可能**であり、mask 不在期間の scene 表現補完手段としても価値が高い。
	- mask query embedding は DVIS の referring tracker スタイルでそのまま時系列伝搬に渡せる設計とし、mask 重なり率・mask boundary 共有率を H3 関係モジュールへの prior として供給する（B4 サーベイ。これらは Phase-1 で起動）。
	### 4.4 手-術具関係モジュール〔§12 サーベイ反映：B7/B8 で更新、2026/05/21 に Phase-1 条件付きモジュールとして明記〕
	- **位置づけ：本モジュールは §0.1 Phase-1（mask 入手で起動）に属する**。エッジ疑似ラベルの主要生成源である mask-IoU が mask アノテーションを前提とするため、H3 検証は mask 入手後に起動する。mask が M2 期間内に入手できない場合は、本モジュールと H3 を本論文の中核主張から外し、Phase-0（H1・H2・H4・D-A・D-B）で論文を成立させる。
	- **Mask DINO の per-instance object query をグラフノード**とする two-stage GNN-on-detector-queries 設計とする（B7 サーベイ）。PViC（ICCV 2023）の cross-attention「predicate visual context」+ box-pair positional embedding を借用し、SSG-Com / MCIT-IG の bipartite / dynamic graph 構造（hand-identity ノード = Operator R/L・Assistant + action エッジ）を採用する。ノード（object query）と box-pair positional embedding は bbox でも構成可能だが、エッジ疑似ラベルの品質が mask 依存である。
	- エッジ特徴:中心距離、相対面積、IoU、最近傍距離、mask 接触率、過去フレーム継続性。（mask 接触率は Phase-1、それ以外は bbox でも計算可能。）
	- 出力:**grasp / near-contact / handover / two-hand manipulation** の 4 種を中心とする関係ラベル(疑似ラベルは Hand-Tool マスクから自動生成)。
	- **エッジ疑似ラベルの自動生成基準**（B7 サーベイ、EgoSurgery-HTS マスクから生成、Phase-1）：grasp = mask-IoU(hand, tool) ≥ 0.15 かつ接触が 3 フレーム継続、near-contact = 中心距離 ≤ k·√(area) かつ最近傍距離 ≤ d_max、handover = hand_i の mask-IoU 減少 + hand_j の増加が 5 フレーム継続、two-hand manipulation = 両手が同一 tool に grasp エッジ。focal loss（γ=2, α=0.25）でマルチラベル分類する。疑似ラベル精度は 200 フレームの人手検証で 80% 以上を担保ラインとし、下回れば mask-IoU 閾値を見直す。
	- **mask 入手前の代替〔2026/05/21 追加〕**：mask 入手前に関係モジュールのパイプラインを先行実装・動作確認したい場合は、bbox-IoU・中心距離・包含関係から生成した **粗い near-contact 疑似ラベル** を使う。ただし bbox だけでは grasp（接触）と near-contact（接近）の分離が原理上困難であり、H3 の本格検証には mask が必要である。
	- **HODN（IEEE TMM 2024）の stop-gradient** により、H3 の関係損失が H1 の box regression を汚染しないよう保護する（B7 サーベイ）。
	- 時系列文脈は LABRAD-OR 式の memory scene graph（前フレームのエッジ予測を入力に追加）で軽量に取り込む。
	- 本モジュールは Phase head への文脈として、また将来的な動作認識への接続点として機能する(H3 の中核)。
	### 4.5 工程（Phase）ヘッド：時間構造つき系列モデル〔§12 サーベイ反映：B5/C3/D2/C4 で更新〕
	- フレーム単位ではなく **object tokens over time → temporal model → phase sequence** で扱う（H2 実現経路）。**入力となる object token は §4.3 Phase-0 の bbox 由来 token（mask shape 属性なし）で成立するため、本ヘッドおよび H2 検証は mask 不在の Phase-0 で全面実行できる〔2026/05/21 確認〕**。mask 入手後（Phase-1）は object token に mask shape 属性が加わるが、時系列ヘッド自体の設計変更は不要である。
	- 0.5 fps の Ego を対象とし、**長距離コンテキスト**を捉える設計を採用する。B5/C3/D2 サーベイに基づく S4 候補を、2026/05/21 の見直しで **2 段階運用（第 1 波／第 2 波）** に再編する（全 6 候補を並列に並べると実験数が 50〜100 規模に膨張し、§10.1 の計算コスト見積もりと矛盾するため）。
		- **第 1 波（S4 本体、必須）**：TeCNO（causal dilated TCN、O(T)、online 友好、軽量、global feature 入力の §2.5 (b) 基準点）と SR-Mamba（MICCAI 2024、1 段階訓練、bidirectional Mamba decoder、線形計算コストで object-centric token 入力と最も適合）の 2 モデルに絞り、これを H2 検証（S5）の主軸とする。
		- **第 2 波（S4 安定後の上限探索・ベンチマーク拡充）**：HID-SSM（2025 SOTA、LA-SSM + GR-SSM、causal と contextual 両方）を主軸に、SKiT（online 上限・低計算）、Surgformer（offline 上限、divided ST attention + HTA）、SPRMamba（hybrid Mamba+Transformer）を順次追加する。これらは §2.6 の設計仮説 D-B（EgoSurgery-Phase 初の長距離時系列ベンチマーク）を直接裏付ける。Trans-SVNet、MuST は参考文献として保持。
		- **Surgformer / SR-Mamba / SPRMamba / HID-SSM は EgoSurgery-Phase で未評価であり、初ベンチマーク自体が publishable 貢献となる**（D2/C3 サーベイ、§2.6 D-B）。
	- **object-centric token 入力との適合性と時系列化設計**：Mamba 系が最も自然（線形計算量・長系列対応）。時系列ヘッドは heterogeneous token 列（per-frame global feature + per-frame top-K object tokens with type embeddings）を受け入れるよう設計する。**時系列化設計は SlotSSMs 風 block-diagonal Mamba に一本化し、SR-Mamba と一体の実装として扱う〔2026/05/21 見直し〕**—SlotSSMs 風の block-diagonal 構造は slot ごと独立に時間発展する SR-Mamba と見なせることができ、両者を別候補として並べるのではなく、SR-Mamba の Mamba decoder を block-diagonal 化したものを §2.6 D-A の主推奨アーキテクチャとする（C3-C4 結合の固有貢献ストーリー）。**serializer（raster / token-importance ordering）の要否は block-diagonal 採否で条件分岐する**：block-diagonal Mamba を採用する場合は slot ごとの独立 scan により 1-D 列への平坦化が不要となり serializer を省けるが、単一の selective scan（素の SR-Mamba / HID-SSM）を使う場合は object-centric token 列が 1-D でないため serializer を付す（D2 サーベイ）。第2推奨は Slot-BERT 風 bidirectional masked Transformer（C4 サーベイ）。
	- **常に causal 版と bidirectional 版を並行訓練・評価**する（D2 サーベイ：HID-SSM の公表値で約 1.7 pp accuracy gap を prior とし、透明に報告）。
	- 工程の順序性を反映する正則化を追加（B5 サーベイで支持）：
		- temporal smoothing loss
		- transition loss / impossible-transition penalty
		- phase order prior、および HID-SSM の continuous phase-progress regression branch を採用時系列モデルに移植し class-balanced focal loss と併用（D2 サーベイ）。
	### 4.6 双方向補完(Phase ⇄ Detection)— 中核モジュール
	本研究の主張(H1 / H2)を直接実現するモジュール。§4.1 の設計思想を実装レベルで具体化する。
	- **Phase → Detection（H1）**：Phase head の出力（logits または embedding）を detection head に注入する。**注入方式の primary/secondary を 2026/05/21 に逆転し、cross-attention 注入を primary、FiLM を軽量ベースライン / ablation 下限に再配置する**。**primary：cross-attention 注入**—C2 サーベイの推奨に従い、Mask DINO decoder の cross-attention 層に phase 分布を射影した c_phase トークンを追加 KV として注入する（c_phase_history で数フレーム前の phase memory も併用）。C2 サーベイは、FiLM が query 全体への affine で粒度が粗いのに対し cross-attention 注入は object query 単位の条件付けが可能であり、検出トークンと phase 文脈の結合に適していると評価している。**c_phase token に entropy gating を追加する〔2026/05/21 追加〕**—phase head の予測分布のエントロピーをゲート信号とし、phase 予測が不確実な（エントロピーの高い）フレームでは c_phase の注入強度を自動減衰させる。これにより Phase 側が未収束・課題の時期に誤った phase 文脈が検出を退化させるリスクを押さえ、stop-gradient（下記）と並んで Phase→Detection の安定化装置となる。**下限 / ablation ベースライン：FiLM 注入**—FiLM は低コストかつ安定で、C6 サーベイで MTRCNet-CL の correlation loss を feature-level 条件付けに拡張する位置づけとして推奨されたが、粒度が粗いため注入方式の **ablation 下限（これを上回らなければ cross-attention の価値がない）** として位置づける。**S6 で cross-attention（primary）vs FiLM（下限）vs SAK-style adapter bias の 3 者を厳密に比較検証する**。SAK（ICLR 2025）の Task-Specific Adapter Pool の思想を参考に、Phase embedding を「adapter bias」として detection head に注入する設計も検討する。ヘッドレベルの不均衡・類似・遮蔽対策として Co-DETR 補助 ATSS ヘッドの追加（Co-Mask-DINO 拡張）、Relation-DETR の position relation embedding 注入、MP-Former の mask-piloted denoising を併用する（C2 サーベイ）。
	- **Detection → Phase(H2)**:object token 列を Phase head の主入力とする。画像 global feature は補助入力に留め、**判定の主軸は物体中心表現**とする。
	- **学習スケジュール**:Stage A で detection を安定化 → Stage D で双方向フローを on にする(初期段階で grad を相互に入れると未収束の信号同士で破壊しあうため)。
	- **gradient 制御**:Phase → Detection 経路には stop-gradient のオプションを持たせ、Phase 側の不安定性が検出を退化させない設計とする。
	- **Ablation 容易性**:Phase → Detection、Detection → Phase は config で個別に on/off できる構造とし、§7.1 の A3 / A4 で片方向 vs 双方向の効果を厳密に分離評価する。
	### 4.7 Exo 補助経路（学習時のみ）— H4 実現経路〔§12 サーベイ反映：A4/D1/E2/E5 で更新〕
	H4（view-consistent SSL による動作・時間表現の獲得）を直接実現するモジュール。A4 サーベイで手術 OR setting での先行例がないことが確認され、本研究の独自性のフックとなる。
	- Exo 5 視点を **shared-weight encoder** で個別埋め込み → visibility-aware view gating で融合。**Exo encoder の第一候補は Hiera-B（VideoMAE V2 K710 + Endo-FM warm-start）**、Ego encoder は EgoVLPv2 初期化（D1 サーベイの最終推奨設計）。
	- **3 層構造の活用設計**（E3/A4/D1/E5 サーベイ統合）：
		1. **第 1 層：Exo 単独 SSL（Stage B 前半）**— VideoMAE v2 ベースの masked video modeling + playback speed prediction + temporal order prediction。hand-tool-guided MAE を併用。
		2. **第 2 層：Exo 視点間 view-consistent SSL（Stage B 後半）**— 5 視点間で同時刻の正例ペアを構成し、cross-view contrastive（PreViPS 式）を学習信号とする。view dropout（ランダムに 1–2 視点を落とす）で推論時の Exo 不在への汎化を促進。**temporal hard negative を追加する〔2026/05/21 追加〕**—同一視点内の異時刻フレーム（ただし同一工程内の近接時刻）を hard negative として contrastive 損失に加える。視点間正例だけでは表現が「視点不変」にはなるが「時刻弁別」にはならず、低 fps Ego の動作・時間表現獲得（H4）の目的とずれるため、時間方向の弁別性を与える temporal hard negative が必要となる。
		3. **第 3 層：Ego–Exo 間の整合と蒸留（Stage C）**— 時間同期 contrastive + Phase 分布整合 KL + tool-set 弱整合 + teacher–student distillation。
	- **fps 差への対処**（A4/D1 サーベイ）：Ego（0.5 fps）と Exo（25 fps）の fps 差 50 倍に対し、Ego 1 フレーム周辺 ±2 秒を 1 つの co-occurrence unit と定義し、Exo 側は対応時刻周辺の短いクリップを入力とする。SlowFast 的な dual-rate 構成も検討に値するが、SlowFast の原設計は α≤8 までであり α=50 は外挿領域である点に注意（D1 サーベイ）。
	- **Stage C の蒸留は Quattrocchi 式 2-level KD + AE2 / AlignEgoExo の temporal-alignment objective** を採用する（E2/E5/D1 サーベイ：unpaired ego-exo を temporal cycle consistency で扱う設計が 1 ego + 5 exo に合致。plain L2 feature distillation の代わりに使用）。同期が保証される場合 AE2 の DTW は過剰設計となりうるため、直接時刻マッピングで十分かを S8 で検証する。
	- **推論時は本経路を切り離す**(branch-pruning / weight discarding を学習後に明示)。**S8 で Exo 経路の重みを抹いた推論で性能を再測し、branch-pruning 後の性能劣化がないことを検証する**（A4 サーベイ推奨）。
	- **H4 の撤退ラインの 2 段階化〔2026/05/21 追加、§9 #5 と整合〕**：A4 サーベイは、Exo の画角が術野近傍に限定されるため Ego-Exo 間の視野重複が大きすぎ、view-consistent SSL の学習信号が弱い可能性を指摘した。このリスクに備え、S8 の本格検証の手前に **第 1 段階の予備診断（S7.5）** を設ける（§10.1 S7.5 参照）—少量の Exo サブセットで cross-view contrastive の表現品質（視点不変性・時刻弁別性）を診断し、視野重複が大きすぎて信号が得られないと判断されれば、S8 のフル SSL パイプラインを走らせる前に Exo の役割を「Phase label の弱教師あり転写のみ」に早期縮退する。**第 2 段階** は従来通り S8 実測後の縮退で、S8 で Δ mAP・Δ Phase F1 の追加改善幅が 1σ 以内の場合に Exo を SSL から弱教師転写のみに縮退する。
---
## 5. 学習スキーム(段階学習) {toggle="true"}
	```javascript
Stage A → Stage B → Stage C → Stage D
	```
	### Stage A:Ego 空間 multi-task の基礎学習〔§12 サーベイ反映、2026/05/21 に Stage A0/A1 に分離〕
	mask / hand-tool アノテーション不在の制約（§0.1）を反映し、Stage A を **Stage A0（bbox、現時点で実行可能）** と **Stage A1（mask、mask 入手で起動する条件付き）** に分離する。
	- **Stage A0（bbox 検出学習、Phase-0 主経路）**
		- 目的:術具・手の **box** を安定化させる。**ここで A1 比較対象（術具検出単独モデル、bbox 版）の数値を確定させる**。
		- 損失:`L_det`のみ。
		- 出力:bbox 検出の domain-specific strong baseline（Mask DINO の box ブランチ / VarifocalNet）。
	- **Stage A1（mask 学習、mask アノテーション入手で起動する条件付き）**
		- 目的:mask 入手後に術具・手の **mask** を安定化させ、instance segmentation の baseline（A1 比較対象の bbox + mask 版）を確定させる。
		- 損失:`L_det + L_mask`。
		- 出力:検出・分割の domain-specific strong baseline（Mask DINO / VarifocalNet / Mask2Former）。
		- mask が M2 期間内に入手できない場合は Stage A1 をスキップし、Stage A0 だけで後続 Stage（B〜D）に進む。
	### Stage B：Ego + Exo の自己教師あり事前学習〔§12 サーベイ反映〕
	- 目的：Exo の高 fps 情報から時間表現を獲得し、Ego へ転写可能な表現を作る。
	- **主損失：VideoMAE v2 ベースの masked video modeling**（E3 サーベイ第一候補）。Exo 5 視点 × 25 fps の大量無ラベル映像に適用。tube masking + 高マスク率（75–90%）。
	- **補助損失 1：playback speed prediction**（再生速度の識別タスク）。動作の速度感覚を獲得。
	- **補助損失 2：temporal order prediction**（フレーム順序の正誤判定）。時間的順序の表現を獲得。
	- **新規手法：hand-tool-guided MAE**。Stage A で得た Ego 側の検出結果（手・術具の mask）を Exo に射影し、手・術具領域を優先的に mask することで意味的に重要な領域の再構成を学習（E3 サーベイで先行例なしを確認、新規性あり）。ablation として random mask vs hand-tool-guided mask を比較する。
	- **Exo 視点間整合：cross-view contrastive learning**。5 視点間で同時刻の正例ペアを構成し、視点不変な行動表現を学習。view dropout（ランダムに 1–2 視点を落とす）で推論時の Exo 不在（=全視点 dropout）への汎化を促進（A4 サーベイ推奨）。**temporal hard negative**（2026/05/21 追加、§4.7 と整合）：同一視点内の同一工程内近接異時刻フレームを hard negative として contrastive 損失に加え、時間方向の弁別性を与える。
	### Stage B′：未ラベル Exo での DINO/iBOT 継続事前学習〔§12 サーベイ反映：E2、2026/05/21 に独立小節として明示〕
	- 目的：自然画像→手術ドメインの gap を埋める、最大レバレッジの介入。Stage B 本体（VideoMAE 系の masked video modeling）とは独立に、**DINOv2 ViT-L/14-with-registers backbone に対して未ラベル Exo 視点フレームで短い DINO/iBOT 継続事前学習を行う**（E2 サーベイ：SurgeNetXL が DINO 継続で示した大きなゲインを追試）。
	- 位置づけ：Stage A の backbone を一度凍結してから Stage B′ を行い、その出力を Stage A の検出ヘッド学習に戻す運用を推奨する（Stage A 初期化の前段としても適用可能）。
	- スキップ判定：Stage B′ の DINO 継続が held-out EgoSurgery split で DINOv2-with-registers 比 \<2% gain ならドメイン gap は小さく、Stage B′ をスキップ可能（E2 サーベイの判定閾値）。
	### Stage C：Ego–Exo cross-view alignment & 蒸留〔§12 サーベイ反映〕
	- 目的：Exo で得た文脈表現を Ego 学生モデルへ移す。
	- 損失：
		- **時間同期 contrastive**（同時刻 Ego/Exo を正、異時刻を負）。Ego 1 フレーム（0.5 fps）に対して Exo 側は対応時刻周辺の短いクリップ（前後 0.5 秒 = 25 フレーム）を入力とする（A4 サーベイ：fps 差 50 倍への対処）。TCC（Temporal Cycle Consistency）を時間アラインメントの基盤手法として参照。
		- **Phase 分布整合 KL**（同時刻の Phase logits を Ego ↔ Exo で揃える）。Ego の Phase ラベルを同時刻の Exo に転写し、Exo 側にも Phase head を持たせる（学習時のみ）。
		- **tool-set 弱整合**（Ego で観測された術具集合を Exo 側で PU loss で学習）。Exo 側の object-awareness を促進（B8 サーベイの知見と接続）。
		- **teacher–student distillation**（Exo teacher → Ego student）。feature matching（中間層の MSE / cosine similarity）+ KL divergence（Phase logits 整合）を基本としつつ、**Quattrocchi 式 2-level KD と AE2 / AlignEgoExo の temporal-alignment objective を plain L2 feature distillation の代わりに使用する**（E2/E5/D1 サーベイ）。Quattrocchi 方式の逆方向適用—ラベル付き Ego → 未ラベル同期 5 視点 Exo で Ego→Exo ブランチに蒸留し、Exo ブランチからの backprop で Ego エンコーダが多視点不変表現を獲得する設計とする（E5 サーベイ中核設計）。SAK（ICLR 2025）の multi-teacher 表現統合の知見を参考に、Exo teacher の表現を Ego student の backbone / Phase head の特定層に注入する。推論時は Exo ブランチを切り Ego 単独動作。
	### Stage D：Ego 教師あり統合 fine-tuning〔§12 サーベイ反映〕
	- 目的：本フェーズの短期ゴール（術具・手・工程の同時認識）に最適化する。**双方向フィードバックを on にし、Stage B / C で獲得した Exo 由来の表現も統合して、H1 / H2 / H3 / H4 を統合検証する。**
	- 同時最適化対象：検出 / 分割 / 関係 / 工程。
	- **損失重み付け：FAMO を第一候補、DB-MTL の対数変換を併用**（C6 サーベイ推奨）。O(1) コストで全タスク損失を均等降下させつつ、異なる損失スケール（CE / focal / BCE / temporal smooth）を対数変換で自動正規化。
	- **勾配制御：GCond（arXiv 2025）の勾配蓄積 + 適応的仲裁メカニズム**を Stage D の Phase → Detection 経路に導入し、Phase head の未収束信号が Detection head を退化させるリスクを低減（C6 サーベイ推奨）。
	- **negative transfer 監視：LibMTL の Δp 指標**（各タスクの単一タスク比改善率の平均）で Stage D fine-tuning 中の negative transfer をオンライン監視する。
	- 関係ラベルは Hand-Tool マスクから自動抽出する疑似ラベル（明示アノテーションなし）。
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
	- `L_contrast/MAE`:Exo 自己教師あり(Stage B/C で有効、Stage D では小さく維持)。
	- `L_distill`:Exo teacher → Ego student(KL / feature matching)。
	- `L_view_consist`:Ego–Exo 同時刻整合(Phase logits KL + tool-set PU)。
	**λ_mask と λ_rel は §0.1 Phase-1 で起動する条件付き項であり、mask / hand-tool アノテーションが入手されるまで 0 に固定する。Phase-0 の主経路は L_det・L_phase・L_temp_smooth・L_contrast/MAE・L_distill・L_view_consist で成立する。** **動作(Action)関連の損失は本フェーズでは設定しない。** 関係モジュールは将来的な動作認識への足場として残す。
---
## 7. 評価指標 {toggle="true"}
	### 7.1 主要指標:相互改善幅(Δ)
	本研究の成功条件は H1 / H2 の検証(およびそれを増幅する H3、上限を引き上げる H4 の検証)であるため、**最重要指標は単一タスクモデルに対する相互改善幅**である。
	- **Δ 非有意時のフォールバック〔2026/05/21 追加、§2.6 と整合〕**：EgoSurgery は 21 動画・8 術者・1 施設と小規模であり（§12.24 G4）、Δ の variance が大き「Δ が 1σ 以内なら改善と主張しない」基準（§10.1）に照らすと、Δ が有意差に達しないシナリオが現実的にありうる。その場合のフォールバックとして、(1) **単一タスクでの絶対精度 SOTA 更新**（EgoSurgery-Tool の VarifocalNet AP 45.8・EgoSurgery-Phase の既存 SOTA を上回ること自体）、(2) **未ベンチマークモデルの初評価**（§2.6 の設計仮説 D-A：object-centric token × block-diagonal SSM アーキテクチャ、および D-B：EgoSurgery-Phase 初の Surgformer/SR-Mamba/SKiT/MuST/HID-SSM 長距離ベンチマーク）を方法論的貢献とする。したがって、H1〜H4 のΔ を主張しつつも、Δ が有意差に達しない場合でも D-A・D-B によって論文が成立する二段構えとする。
	- **Δ mAP(H1 の検証指標)**
		- `Δ mAP = mAP(マルチタスクモデル) − mAP(術具検出単独モデル)`
		- 全体 mAP、稀少クラス mAP(Skewer / Syringe / Forceps を中心)、形状類似ペア(Forceps / Tweezers / Needle Holders)それぞれで分離して報告。
		- **本研究で最も重視する指標**。Δ mAP \> 0 を成功条件とする。
	- **Δ Phase F1(H2 の検証指標)**
		- `Δ Phase F1 = macro F1(マルチタスクモデル) − macro F1(工程認識単独モデル)`
		- 全体 macro F1、Dissection 内部の segmental F1@\{10, 25, 50\}、Closure 内部の segmental F1@\{10, 25, 50\} で報告。
		- Δ Phase F1 \> 0 を成功条件とする。
	- **Δ Edit score**(H2 の補助指標、工程境界の正確さを評価)。
	- **Δ の増幅効果(H3 の検証指標)**
		- 関係モジュール on/off で Δ mAP・Δ Phase F1 がどれだけ拡大するかを報告。
	- **Δ の上限引き上げ効果(H4 の検証指標)**
		- Exo SSL(Stage B / C) on/off で Δ mAP・Δ Phase F1 がどれだけ拡大するかを報告。
		- 加えて、Exo SSL 単独効果の診断指標として、Ego の時間方向タスク(例:工程境界フレーム周辺の予測安定性、隣接フレーム間の表現類似度)に対する改善も計測する。
	### 7.2 タスク単位の絶対指標(副次指標)
	- 術具・手検出:**mAP**(全体、クラス別、稀少クラス分離報告)。Phase-0 から計測可能。
	- 術具・手分割:**IoU / mIoU**。**§0.1 Phase-1 条件付き指標（mask アノテーション入手で計測、〔2026/05/21 注記〕）**。
	- 関係認識:**接触/把持の F1**(疑似ラベル基準の診断指標)。**§0.1 Phase-1 条件付き指標（mask / hand-tool アノテーション入手で計測、〔2026/05/21 注記〕）**。
	- 工程認識:**フレーム単位 accuracy、macro F1、Edit score、Segmental F1@k**。Phase-0 から計測可能。
	（§7.1 の Δ mAP は bbox mAP であり Phase-0 から計測可能。Δ の増幅効果（H3 検証指標）は Phase-1 条件付き。）
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
	- **RTX 6000 Ada ×1（Ada Lovelace, 48GB）— Δ 基準点専用**：S0・S4 第 1 波・S5・S6・S9 の本実験および S8 の Ego fine-tuning。Δ の分子・分母となる学習はすべてこの GPU に固定し、世代混在による浮動小数点丸め差異を排除する。
	- **RTX A6000 ×2（Ampere, 48GB）— 派生実験・基盤整備**：S2・S3（基盤整備）、S1・S7（Phase-1 条件付き）、S4 第 2 波（D-B ベンチマーク拡充）、S6 注入方式 ablation、S9 の ablation・転移検証。DDP 使用時は effective batch size を記録。基準点に直接影響しない実験のみここで実行する。
	- **RTX A5000 ×5（Ampere, 24GB）— Exo SSL 専有**：S7.5（予備診断、2〜3 枚）、S8 Stage B-C の Exo SSL 学習（5 枚 DDP）。Exo は 5 fps 程度にサブサンプリングして 24GB VRAM 制約と計算量を調整。
	- **Quadro RTX 8000 ×2（Turing, 48GB）— 軽量専用**：bf16 非対応のため基準点学習には使わない。推論評価・データ前処理・軽量なデバッグ実行に限定。
	- **並行実行の原則**：6000 Ada が S0 を回している間に A6000 で S2・S3 の基盤整備を並行、A5000 でデータ前処理を進めるなど、3 台のサーバーを同時稼働させて全体スループットを最大化する。ただし、Δ 基準点の実行は必ず 6000 Ada に固定する。
	- **暫定運用：RTX 6000 Ada 未配備期間〔2026/05/24 追記、2026/05/25 DDP 条件追加〕**：RTX 6000 Ada が未配備の期間は、Δ 基準点学習を `bengio`（RTX A6000 ×2）上で実行することを暫定的に許容する。その場合、以下の 6 条件をすべて満たすこと。(1) 同一の Δ 比較群（例：S0 の VarifocalNet と Mask DINO と Co-DETR、A1 の単独モデルとマルチタスクモデル）は必ず同一サーバー上で揃えて測定する、(2) `metrics.json` の `eval_recipe.server_name` と各実験フォルダの `server.txt` にサーバー名を記録する、(3) RTX 6000 Ada 配備後に Δ 基準点を再測定する必要が生じうることを §14 に明記する。**〔2026/05/25 追加〕** (4) DDP（複数 GPU）使用時は、同一 Δ 比較群内の全モデルを同一 GPU 構成（同一サーバーの同一 GPU 枚数・同一 DDP 設定）で揃える。単一 GPU と DDP の混在は effective batch size・NCCL allreduce 非決定性・BN/LN 挙動差により Δ の意味を崩壊させるため禁止する。(5) DDP 使用時は effective batch size（GPU 枚数 × per-GPU batch size）を `metrics.json` の `eval_recipe` に記録する（`eval_recipe.gpu_count`・`eval_recipe.effective_batch_size` フィールド）。(6) learning rate の線形スケーリング適用有無を config に明記する（DDP で effective batch size が変わる場合、lr を線形スケーリングするか per-GPU batch size を調整して effective batch size を維持するかを選択し、選択結果を記録する）。サーバー名の解決は `EGOSURGERY_SERVER_NAME` 環境変数 → Hydra `logging.server_name` → `socket.gethostname()` の優先順とする。
	### 8.1 中核 ablation(H1 / H2 / H3 / H4 の検証)
	本研究の主要 ablation は H1 / H2 / H3 / H4 の検証として再編する。
	<table fit-page-width="true" header-row="true">
<tr>
<td>Ablation</td>
<td>比較対象</td>
<td>検証する仮説</td>
<td>主要指標</td>
</tr>
<tr>
<td>**A1**</td>
<td>提案モデル vs **術具検出単独モデル**(Mask DINO / VarifocalNet を bbox + mask のみで学習)。比較は§15.4 A の strict 3 条件（公式 split / locked-down test_cfg / eval_recipe 一致）を満たす同一 recipe で行う</td>
<td>**H1**</td>
<td>Δ mAP、稀少クラス Δ mAP（Skewer / Syringe）、形状類似ペア Δ mAP（Forceps / Tweezers / Needle Holders）</td>
</tr>
<tr>
<td>**A2**</td>
<td>提案モデル vs **工程認識単独モデル**(画像 global feature + TeCNO / LoViT)</td>
<td>**H2**</td>
<td>Δ Phase F1、Dissection / Closure 内部 segmental F1@k</td>
</tr>
<tr>
<td>**A3**</td>
<td>Phase → Detection フィードバック on/off</td>
<td>**H1**(片方向 vs 双方向)</td>
<td>Δ mAP の差</td>
</tr>
<tr>
<td>**A4**</td>
<td>Detection → Phase 入力経路 on/off(object token vs global feature)</td>
<td>**H2**(片方向 vs 双方向)</td>
<td>Δ Phase F1 の差</td>
</tr>
<tr>
<td>**A5**</td>
<td>関係モジュール on/off（**§0.1 Phase-1 条件付き ablation、mask / hand-tool アノテーション入手で実施**）</td>
<td>**H3**</td>
<td>A1 / A2 の改善幅が増幅されるか</td>
</tr>
<tr>
<td>**A6**</td>
<td>Exo SSL(Stage B / C) on/off(提案モデル vs Exo SSL 無し提案モデル)</td>
<td>**H4**</td>
<td>Δ mAP・Δ Phase F1 の追加改善幅、工程境界周辺の予測安定性</td>
</tr>
<tr>
<td>**A7**</td>
<td>object-centric token + block-diagonal Mamba vs 通常 selective scan Mamba / global feature 入力</td>
<td>**D-A**（設計仮説、§2.6）</td>
<td>アーキテクチャの絶対精度・計算効率（Δ に依存しない方法論的貢献の検証）</td>
</tr>
	</table>
	### 8.2 補助 ablation〔§12 サーベイ反映〕
	アブレーションはフェーズ帰属を明示する：A1〜A4・A6・A7 と以下の長尾・損失・SSL 系 ablation は Phase-0（bbox）で実行可能。A5 と関係モジュールのエッジ特徴分解は Phase-1（mask 入手で起動）。
	- Stage 順序の入れ替え(A→D / A→B→D / A→B→C→D)。
	- **損失重み付け方式（5 条件）**（C6 サーベイ推奨）：(i) Equal Weighting, (ii) Uncertainty Weighting, (iii) FAMO, (iv) DB-MTL, (v) PCGrad + DB-MTL log transform。LibMTL で統一実行。
	- **view-consistent SSL の構成要素分解**(cross-view contrastive のみ / cross-view masked prediction のみ / Ego–Exo 同時刻整合のみ / 全部入り)— H4 の内部分解。
	- **hand-tool-guided MAE vs random mask**（E3 サーベイ推奨）：Stage B の masking strategy の効果を分離評価。
	- **関係モジュールのエッジ特徴選択**(位置のみ / mask 接触のみ / 運動量のみ / 全部入り)— H3 の内部分解。
	- **Phase → Detection 注入方式**（C6 サーベイ推奨）：FiLM vs cross-attention vs SAK-style adapter bias を S6 で比較。
	- **時系列モデル比較**（B5 サーベイ推奨）：TeCNO vs LoViT vs SKiT vs SR-Mamba を S4 で比較。入力長 / 計算量 / 精度 / online 対応で評価。
	- **長尾損失・拡張の独立 contribution〔2026/05/21 追加、§3.3 と整合〕**：EQLv2 vs Seesaw vs Logit Adjustment の長尾損失比較、Repeat Factor Sampling・Decoupled cRT のサンプリング比較、temporal-consistent copy-paste vs フレーム独立 naive Copy-Paste の拡張比較を S5〜S6 で実施する。F1 サーベイで「手術・Ego 映像での標準長尾損失の系統的ベンチマークが不在」と確認されたため、この長尾手法比較自体を、補助 ablation に留めず **手術 Ego マルチタスク設定での初の長尾手法ベンチマークという独立した contribution** として位置づける。報告は overall mAP に加え per-class AP（Skewer/Syringe 等の稀少クラス）と head/medium/tail 分割で行う。
---
## 9. 今後の判断ポイント(MTG での宿題) {toggle="true"}
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>判断項目</td>
<td>判断トリガー</td>
</tr>
<tr>
<td>1</td>
<td>**動作(Action)アノテーション追加の要否**</td>
<td>現フェーズで Phase ラベルが術具検出にどれだけ寄与するか(H1 の Δ mAP)、工程認識の到達精度(H2 の Δ Phase F1)が想定ラインに達するかを確認した時点</td>
</tr>
<tr>
<td>2</td>
<td>**工程ラベル細分化の要否(Dissection / Closure 内部)**</td>
<td>工程境界の誤りパターンを analyze し、特定の段階で再現性のある混同が発生する場合</td>
</tr>
<tr>
<td>3</td>
<td>**Exo の役割拡張（ラベル転写以上の使い方）**</td>
<td>H4 の検証結果として、現方針（view-consistent SSL + 蒸留）で得られる Ego 単独精度の上限が見えた段階</td>
</tr>
<tr>
<td>4</td>
<td>**評価軸の臨床的優先付け**(術後レビュー / 教育 / 記録自動化 / 医療安全 / 時間予測など)</td>
<td>先生方との次回相談時</td>
</tr>
<tr>
<td>5</td>
<td>**H4 の撤退ライン**（§12 サーベイ反映：A4 で手術 OR での Ego-Exo SSL は前例なしと確認）</td>
<td>2 段階の撤退ラインを事前設計する（§4.7・§10.1 S7.5 と整合）。**第 1 段階**：S7.5 予備診断で、少量 Exo サブセットの cross-view contrastive の表現品質（視点不変性・時刻弁別性）を診断し、視野重複が大きすぎて信号が得られなければ S8 のフル SSL の手前で Exo を「Phase label の弱教師転写のみ」に早期縮退。**第 2 段階**：S8 で Δ mAP・Δ Phase F1 の追加改善幅が 1σ 以内の場合、Exo の役割を「SSL のみ」から「Phase label の弱教師あり転写のみ」に縮退し計算コストを削減。Exo の画角が術野近傍に限定されているため Ego-Exo 間の視野重複が大きすぎ、学習信号が弱い可能性がある（A4 サーベイでの結論）</td>
</tr>
<tr>
<td>6</td>
<td>**Mask DINO 主軸からの検出ヘッド切替**（§12 サーベイ反映：C2/B2）</td>
<td>S0 完了時に Mask DINO vs Co-DETR を比較し APr（稀少クラス）で 3 ポイント以上の差が出れば S1 以降を Co-DETR ベースに切替。S3 で Mask DINO vs EoMT を比較し mask AP 同等以下なら EoMT（最大 4×高速）に切替。Mask DINO surgical Ego AP \< 50 なら detector ベースを諸め VideoSAURv2 + DINOv2 unsupervised slot に主軸切替（C4）</td>
</tr>
<tr>
<td>7</td>
<td>**backbone 主軸の切替**（§12 サーベイ反映：C1）</td>
<td>Stage A の backbone 比較 ablation で DINOv2 ViT-L が SurgeNetXL CAFormer に Phase Jaccard で 5pt 以上劣るなら主軸を SurgeNetXL に切替。UniSurg（V-JEPA ベース、EgoSurgery workflow で +14.6% F1）が ViT-L 重みを公開したら Stage A 初期化に優先検討（E2）</td>
</tr>
<tr>
<td>8</td>
<td>**評価ベンチマークと Δ 指標の確定**（§12 サーベイ反映：G4）</td>
<td>EgoSurgery-\{Phase, Tool, HTS\} を主ベンチマークとして確定済み。§11.A の「Open-MOH」は実在しないため MM-OR + EgoExOR へ置換を検討。転移検証用ベンチマーク（PhaKIR/GraSP/CholecT45/EgoExOR）のデータアクセス認証は取得に時間を要するため、S0 開始時点で申請手続きを開始する</td>
</tr>
<tr>
<td>9</td>
<td>**mask / hand-tool アノテーション入手時の Phase-1 起動判断**（§0.1 の 2 フェーズ構成、〔2026/05/21 追加〕）</td>
<td>mask / hand-tool アノテーションが利用可能になった時点で Phase-1 を起動する。具体的には instance segmentation（旧 S1、Stage A1）と H3 関係モジュール（旧 S7）を起動し、object token に mask shape 属性を追加、L_mask・L_rel の λ を 0 から立ち上げる。**判断トリガー**：(1) mask アノテーションの入手見込みが立った時点で、入手時期と Phase-0 の進捗を照らして Phase-1 をスケジュールに組み込む。(2) mask が M2 期間内に入手できないと判断された場合は、Phase-0（H1・H2・H4・D-A・D-B）のみで論文を構成し、H3 ・instance segmentation は「今後の課題」として位置づける。いずれの場合も、判断時点と根拠を §3.1 に記録する</td>
</tr>
	</table>
---
---
## 10. サーベイロードマップ {toggle="true"}
	本研究のアーキテクチャ設計と仮説検証(H1〜H4)に必要な最新研究のサーベイ対象を、**7 大分類 × 約 45 細目** に構造化する。各細目には本研究での位置づけ(参照する § / 関連する H / 関連する S)と優先度(高/中/低)を併記する。
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
<td>無影灯マルチカメラ、OR の固定カメラ、ego-exo pair 学習。H4 の直接の前提</td>
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
<td>B1 の手術特化。形状類似・遮蔽・class imbalance への対処。**S0、S6 の主役**</td>
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
<td>H3 関係モジュールの理論的基盤。HOI 検出、interaction prediction、affordance</td>
<td>高</td>
</tr>
<tr>
<td>**B8**</td>
<td>**手-術具関係認識(hand-tool relation)**</td>
<td>**S7 の主役**。grasp / handover / two-hand manipulation、egocentric H+O</td>
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
<td>§4.3、**H2 の核**。ROI Align、slot attention、object query を時系列化する手法</td>
<td>高</td>
</tr>
<tr>
<td>**C5**</td>
<td>**グラフニューラルネットワーク・関係推論**</td>
<td>§4.4、**H3 の核**。graph transformer、message passing、edge feature 設計</td>
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
<td>**§5 Stage B、H4 の核**。MAE / VideoMAE / MV2MAE、contrastive、playback speed、temporal order</td>
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
<td>**§5 Stage C、H4 の Ego 注入経路**。Soft Teacher、cross-view distillation、feature distillation</td>
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
<td>H4 の主損失。SimCLR、MoCo、CLIP、view-consistent contrastive、time-contrastive</td>
<td>高</td>
</tr>
<tr>
<td>**F4**</td>
<td>**masked modeling(MAE / VideoMAE / MV2MAE)**</td>
<td>H4 の主損失。Stage B の中核。hand-tool-guided MAE という派生</td>
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
<td>H4 関連の外部参照。Ego-Exo4D、Assembly101、CharadesEgo、H2O</td>
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
	### 10.1 サーベイの実施順序(S0〜S9 と連動)
	ロードマップを S0〜S9 のスケジュールに沿って前倒しで配置する。**各 S ステップを開始する前に、対応する細目のサーベイを終えていること**を目安とする。
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
<td>**S5〜S6 開始前**</td>
<td>C4, C6, C7, C9, F2</td>
<td>E1, E8</td>
</tr>
<tr>
<td>**S7 開始前**</td>
<td>B7, B8, B9, C5, F5, G3</td>
<td>B6</td>
</tr>
<tr>
<td>**S8 開始前**</td>
<td>A4, C8, D4, D5, E3, E5, E6, E7, F3, F4, G5</td>
<td>E4, E9</td>
</tr>
<tr>
<td>**S9・論文執筆段階**</td>
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
	2. **Object-centric temporal representation を Phase head の主入力とする設計**：B5 サーベイで先行例がほぼないことを確認（H2 の新規性）。C3/D2 サーベイで、検出由来の object token 列を長距離 SSM/Transformer に流し込む surgical 論文が 2026.05 時点で皆無であることが追加確認された。
	3. **Detection + Phase + Relation の三位一体 MTL**：C6 サーベイで既存文献は tool + phase の 2 タスクが最大であることを確認。E5 サーベイで、検出 × phase × 関係を同時に半教師ありで学習する公開研究も皆無であることが判明。
	4. **手術 OR での Ego-Exo view-consistent SSL**：A4 サーベイで手術 setting での先行例なしを確認（H4 の新規性）。D1/E2/E5 サーベイで、0.5 fps Ego ↔ 25 fps Exo の極端な fps 差をブリッジする手法が空白であり、Quattrocchi et al.（ECCV 2024）の exo→ego 蒸留が最も近い前例であることが特定された。
	5. **Segmentation マスクからの hand-tool 関係疑似ラベル自動生成**：B8 サーベイで先行例がほぼないことを確認（H3 関連）。B7 サーベイで、検出マスクから interaction triplet を自動生成する surgical HOI 論文も未発表であることが裏付けられた。
	6. **hand-tool-guided MAE**：E3 サーベイで object-centric SSL × masked modeling の交差領域に先行例なしを確認。
	7. **EgoSurgery-Phase に対する長距離時系列モデルの未ベンチマーク**：D2/C3 サーベイで、Surgformer・LoViT・SR-Mamba・SKiT・MuST・HID-SSM の EgoSurgery-Phase 数値が未発表であり、これらの初ベンチマーク自体が明確な publishable 貢献となることを確認。
	8. **0.5 fps 低 fps × 異種マルチタスクでの長尾協調学習**：F1 サーベイで、検出 + セグメンテーション + 長距離時系列という異種マルチタスクの per-task 長尾協調学習、および低 fps 動画での Copy-Paste/Mixup 時系列一貫性が未開拓であることを確認。
	9. **surgical phase をトリガとした検出ヘッドへの query 条件付け**：C2 サーベイで、外部 phase token を Mask DINO / Mask2Former decoder に注入する研究例が MICCAI 2023–2025 範囲で発見できず、§4.6 の双方向補完が defensible な novelty であることを裏付け。
	10. **外部 detector の object token 列を SSM/Mamba に流す設計**：C4 サーベイで、SlotSSMs（NeurIPS 2024）以外に slot×Mamba の直接結合例がなく、「検出器出力 token 列を後段 Mamba で処理」する分離型設計は surgical も general video も未報告であり、C3-C4 結合がそれ自体論文の story になりうることを確認。
	11. **検出+工程+関係を三位一体で評価する手術ベンチマークの不在と Δ 指標の未標準化**：G4 サーベイで、open surgery で検出+工程+関係を同一データセットで評価するベンチマークが存在せず、SAR-RARP50/GraSP/PhaKIR 等が multi-task \> single-task を定性的に述べるのみで Δ（相互改善）指標を形式化した例がないことを確認—§7.1 の Δ 指標はモデルだけでなくベンチマーク方法論としても貢献となりうる。
	**実装・手法選定の横断的推奨（22 サーベイ統合版）**：
	- 空間 backbone：**DINOv2 ViT-L/14-with-registers** を主軸採用として確定（C1/E2/E3/B1 共通推奨）。register token で artifact patch を除去し形状類似ペア識別を改善。DINOv3 distilled 重みは公開揃い次第 ablation に追加。Stage A 必須 ablation として DINOv2 vs SurgeNetXL vs EndoViT vs Swin-L の backbone 比較表を作成（C1）。
	- PEFT：MTLoRA を plain ViT 用に porting し DoRA で強化、VeRA は head 増殖時に検討（C1/E2/C6）。heavy full fine-tuning は LIFT の知見に基づき回避（F1）。
	- 検出ヘッド：**Mask DINO + Learnable Query Proposal Distillation**（B1/B2 推奨）。SurgicalSAM の Contrastive Prototype Head を分類ヘッドに移植（形状類似ペア対策、B2）。VarifocalNet を baseline として必ず並走（EgoSurgery-Tool 実 SOTA、B2）。C2 サーベイでも query-based 統合ヘッドの妥当性が裏付けられ（object token 共有・時系列接続容易性・phase 条件付け適性）、Co-DETR を長尾対照候補、VFNet+Mask2Former 完全分離ヘッドを撤退候補とする。Phase→Detection 注入は S6 で FiLM（§4.6 primary）vs Mask DINO decoder cross-attention（C2 推奨）を比較。
	- セグメンテーションヘッド：第 1 ライン **DINOv2 + EoMT decoder**、第 2 ライン DINOv2 + ViT-Adapter + Mask2Former（公式 SOTA 再現）、第 3 ライン Mask DINO、補助 SAM 2（B4 推奨）。
	- 手検出（S2）：own/other × L/R の 4 クラスに Mask DINO hand head を拡張、RoHan の Artificial Gloves augmentation + iterative 半教師ドメイン適応を再現。手姿勢推定は S3 以降に延期（B3）。
	- 時系列モデル：TeCNO をベースライン、SR-Mamba / SPRMamba / HID-SSM を SSM 系候補、SKiT を online 上限・低計算、Surgformer を offline 上限（B5/C3/D2 推奨）。object-centric token + Mamba の組合せ自体が論文の story（C3）。常に causal 版と bidirectional 版を並行訓練・評価（D2）。
	- 物体中心表現（object token 抽出）：Mask DINO object query + ROI Align/mask pooling を主トークン、DINOv2 上の VideoSAURv2/SlotContrast 風 unsupervised slot を ablation 対照・scene slot 補完・弱教師事前学習として併走。時系列化は SlotSSMs 風 block-diagonal Mamba を第1推奨、Slot-BERT 風 bidirectional masked Transformer を第2推奨、SlotContrast の object-level temporal contrastive loss を補助損失に併用（C4 推奨）。
	- HOI / 関係モジュール：Mask DINO query をノードとする two-stage GNN（PViC の cross-attention + SSG-Com/MCIT-IG の bipartite graph + hand-identity ノード）、HODN の stop-gradient で H3 損失が H1 を汚染しないよう保護（B7/B8 推奨）。
	- MTL 最適化：FAMO + DB-MTL 対数変換、GCond の勾配蓄積、LibMTL の Δp 監視（C6 推奨）。
	- SSL 事前学習：VideoMAE v2 + hand-tool-guided MAE、Exo encoder は Hiera-B（VideoMAE V2 + Endo-FM warm-start）、Ego encoder は EgoVLPv2 初期化（E3/D1 推奨）。
	- 半教師あり：Stage C で Quattrocchi 方式の逆方向適用（Ego→Exo 蒸留）、Stage D で Consistent-Teacher（検出）+ SemiVT-Surge（phase）+ Polite Teacher（分割）統合（E5 推奨）。
	- クラス不均衡：post-hoc Logit Adjustment（全分類ヘッド）+ Seesaw Loss（p=0.8, q=2.0）+ RFS（t=0.001）+ Simple Copy-Paste + Balanced Softmax（工程ヘッド）+ Decoupled cRT（F1 推奨）。
	- Stage C 蒸留：AE2 / AlignEgoExo の temporal-alignment objective を plain L2 feature distillation の代わりに使用（E2/E5 推奨）。
	- 実装基盤：LibMTL（MTL）、microsoft/SoftTeacher + Adamdad/ConsistentTeacher + LiheYoung/UniMatch + IntraSurge/SemiVT-Surge（半教師あり）、IDEA-Research/MaskDINO・martius-lab/slotcontrast・PCASOlab/Xslot（検出・slot）（C6/E5/C2/C4 推奨）。
	- 評価ベンチマーク：EgoSurgery-\{Phase, Tool, HTS\} を主ベンチマークとして確定し、PhaKIR・GraSP・CholecT45・EgoExOR を転移・外部妥当性検証用に追加。Δ mAP（per-class、AP_rare/AP_common 分割）+ Δ macro-F1/Jaccard/Edit/Segmental F1@\{10,25,50\} を主報告指標とし、形状類似 sub-confusion matrix と Phase-conditional AP を Supplementary に、leave-one-surgeon-out + paired bootstrap 信頼区間を必須とする（G4 推奨）。
## 12. 直近のマイルストーン(各 M で検証する仮説を明示) {toggle="true"}
	**〔2026/05/21 追記：mask / hand-tool アノテーション不在の制約を反映〕** M1〜M5 の主経路は §0.1 Phase-0（bbox）で完結するよう設計する。M1 の mask baseline（Stage A1）と M3 の関係モジュール部分は Phase-1（mask 入手で起動）に依存する。mask が M2 期間内に入手できない場合、M1〜M5 は Phase-0 部分（bbox 検出・工程認識・H1/H2/H4・D-A/D-B）のみで達成・論文化できる。
	- **M1**:Stage A0 完了 ― EgoSurgery-Tool で再現性のある **bbox 検出ベースライン**(DINOv2 ViT-L/14-with-registers + Mask DINO box ブランチ)を確立。**backbone 比較 ablation（DINOv2 vs SurgeNetXL vs EndoViT vs Swin-L）をここで実施**し、**A1 の比較対象「術具検出単独モデル（bbox 版）」の数値を確定**(H1 検証のための基準点)。mask 入手済みなら Stage A1（instance segmentation）を併して実施する。
	- **M2**:Stage A の出力に **Phase head(TeCNO ベース、global feature 入力)** を直結し、9 クラス工程認識の baseline を取得。**ここで A2 の比較対象「工程認識単独モデル」の数値を確定**(H2 検証のための基準点)。bbox だけで実行可能。
	- **M3**:**双方向フィードバック(Phase ⇄ Detection)** を追加し、object-centric な工程認識+検出補正の効果を ablation で評価。**H1 / H2 の一次検証ポイント**(Δ mAP と Δ Phase F1 をここで初めて測定)。**関係モジュールによる H3 検証は §0.1 Phase-1 に属し、mask 入手で起動する**（mask 未入手の場合 M3 は H1/H2 の一次検証までをスコープとする）。
	- **M4**:Stage B(Exo SSL)と Stage C(Ego–Exo 蒸留)を導入し、Ego 単独推論精度の改善幅を確認。**H4 の主検証ポイント**:view-consistent SSL によって動作・時間表現が獲得されたかを Δ mAP・Δ Phase F1 の追加改善幅および工程境界周辺の予測安定性で評価する。bbox 主経路で実行可能。
	- **M5**:Stage D で統合 fine-tuning、最終評価。**H1 / H2 / H4 （および mask 入手済みなら H3）の最終検証**を行い、動作ラベル導入の要否を判断する。
	### 12.1 詳細検証ロードマップ(S0〜S9)
	M1〜M5 のマイルストーンを 10 ステップに細分化し、各ステップで**動かす軸を 1 本に絞る**ことで、H1 / H2 / H3 / H4 を独立に検証可能にする実験順序。S0〜S9 は M1〜M5 と多対多に対応する(下表「対応 M」列参照)。
	**〔2026/05/21 再編：mask / hand-tool アノテーション不在の制約を反映〕** S0〜S9 を §0.1 の 2 フェーズに対応させ、**Phase-0 主経路を S0→S2→S3→S4→S5→S6→S7.5→S8→S9** とする（S2 の手検出は bbox で導入）。mask を要する **S1（bbox→mask）と S7（H3 関係モジュール）は「mask / hand-tool アノテーション入手で起動する Phase-1 条件付きステップ」に格下げ**する。Phase-0 主経路は bbox + Phase ラベルだけで H1・H2・H4・D-A・D-B を検証でき、mask が M2 期間内に入手できなくても研究と論文が成立する。S1・S7 は mask 入手時点で主経路に挿入する（S1 は S0 の後、S7 は S6 の後に対応）。
	#### 検証軸の凡例
	- **タスク**:`Tool`(術具検出のみ) / `Tool+Hand`(手検出を追加) / `Tool+Hand+Phase`(工程認識を追加)
	- **空間**:`bbox` / `mask`（mask は Phase-1 条件付き）
	- **時系列**:`frame`(フレーム単位の独立予測) / `短期`(数秒〜十数秒の clip) / `長距離`(分〜数十分の sequence)
	- **方向性**:`単方向`(detection 教師あり学習のみ、Phase head 無し) / `Det→Phase`(object token を Phase head へ、Phase 補助損失追加) / `Phase→Det`(Phase embedding を detection head へ FiLM / cross-attention で注入) / `双方向`(両経路 on)
	- **関係**:`無` / `有`(hand-tool graph による grasp / near-contact / handover / two-hand manipulation の同時推定、Phase-1 条件付き)
	- **視点**:`Ego` / `Ego+Exo`(Exo は view-consistent SSL と teacher-student 蒸留のみ、推論時 Ego only)
	- **フェーズ**:`Phase-0`（bbox、現時点で全面実行可能、主経路） / `Phase-1`（mask / hand-tool アノテーション入手で起動する条件付き）
	#### 全体マッピング(S0〜S9 × 軸 × 対応 M)
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
<td>**S0**</td>
<td>Tool</td>
<td>bbox</td>
<td>frame</td>
<td>単方向</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>§2.5 (a) 基準点</td>
<td>M1 前段</td>
<td>**6000 Ada ×1**（Δ 基準点）</td>
</tr>
<tr>
<td>**S1**（条件付き）</td>
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
<td>§2.5 (b) 基準点</td>
<td>M2 後段</td>
<td>**6000 Ada ×1**（Δ 基準点）/ 第 2 波は A6000</td>
</tr>
<tr>
<td>**S5**</td>
<td>Tool+Hand+Phase</td>
<td>bbox</td>
<td>長距離</td>
<td>**Det→Phase(object token 入力)**</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>**H2 一次検証**</td>
<td>M3 前半</td>
<td>**6000 Ada ×1**（Δ 基準点）</td>
</tr>
<tr>
<td>**S6**</td>
<td>Tool+Hand+Phase</td>
<td>bbox</td>
<td>長距離</td>
<td>**双方向**</td>
<td>無</td>
<td>Ego</td>
<td>Phase-0</td>
<td>**H1 一次検証**</td>
<td>M3 中盤</td>
<td>**6000 Ada ×1**（Δ 基準点）</td>
</tr>
<tr>
<td>**S7**（条件付き）</td>
<td>Tool+Hand+Phase</td>
<td>**mask**</td>
<td>長距離</td>
<td>双方向</td>
<td>**有**</td>
<td>Ego</td>
<td>**Phase-1**</td>
<td>**H3 検証**（mask / hand-tool 入手で起動）</td>
<td>M3 後半</td>
<td>A6000 ×1〜2（Phase-1 派生）</td>
</tr>
<tr>
<td>**S7.5**</td>
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
<td>**S8**</td>
<td>Tool+Hand+Phase</td>
<td>bbox</td>
<td>長距離 + Exo 高 fps</td>
<td>双方向</td>
<td>無</td>
<td>**Ego+Exo**</td>
<td>Phase-0</td>
<td>**H4 検証**</td>
<td>M4</td>
<td>**A5000 ×5 DDP**（SSL）+ 6000 Ada（Ego fine-tune）</td>
</tr>
<tr>
<td>**S9**</td>
<td>Tool+Hand+Phase</td>
<td>bbox（mask 入手時は + mask）</td>
<td>長距離 + Exo 高 fps</td>
<td>双方向</td>
<td>mask 入手時 有</td>
<td>Ego+Exo</td>
<td>Phase-0（+ 入手時 Phase-1）</td>
<td>**H1・H2・H4 最終検証（mask 入手時は H3 も）**</td>
<td>M5</td>
<td>**6000 Ada ×1**（最終 Δ）+ A6000（ablation 並行）</td>
</tr>
	</table>
	#### ステップ別詳細
	#### S0:術具検出ベースライン(§2.5 (a) 基準点)
	- **実行サーバー：RTX 6000 Ada ×1（Δ 基準点専用）**。S0 は全 Δ の分母となるため、世代の揃った単一 GPU に固定し数値再現性を死守する（§8.0・§13.8 と整合）。
	- **動かす軸**:なし(出発点)。
	- **目的**:過去の bbox 単独学習を新パイプライン上で再現し、**§2.5 (a) 術具検出単独モデルの比較基準点**を確立。
	- **比較対象**:なし(これ自体が基準)。
	- **主要指標**:全体 mAP、稀少クラス mAP(Skewer / Syringe)、形状類似ペア mAP(Forceps / Tweezers / Needle Holders)。
	- **学習設定**:Mask DINO（DINOv2 ViT-L/14-with-registers + ViT-Adapter）と VarifocalNet を bbox のみで学習。Co-DETR を長尾対照として並走。Seesaw Loss + RFS + bbox-level Simple Copy-Paste（貼り付け対象の稀少クラスは Skewer / Syringe の 2 クラスのみ。Forceps は 12.21% の頻出クラスのため対象外、§3.3 と整合） + post-hoc Logit Adjustment を有効化する（F1/C2/B2 サーベイ）。**評価条件は §8.-1 の locked-down test_cfg（score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6）を強制し、データ split は公式 split（train 9657 / val 1515 / test 4265 images）を使う（§15.1・§15.2）。**
	- **ベンチマーク**:EgoSurgery-Tool を主ベンチマークとし、VarifocalNet の公式 SOTA（tool mAP 45.8）を上回ることを S0 の最低達成ラインとする。Mask DINO / Co-DETR / DDQ-DETR は EgoSurgery-Tool で未評価であり、これらの初ベンチマーク自体が貢献となる（C2/B2 サーベイ）。
	- **注意**:S1〜S9 と**完全に同じ** optimizer / seed / scheduler / augmentation / batch size **/ GPU 構成（単一 GPU or DDP 枚数）** を使う。ここでの実装ミスが Δ 全体を汚染するため最も慎重に固める。**DDP 使用時は、同一 Δ 比較群内の全モデルを同一 GPU 構成で揃えること（§8.0 条件 (4)）が必須であり、effective batch size を eval_recipe に記録する（§8.0 条件 (5)）。単一 GPU と DDP の混在は Δ の意味を崩壊させるため禁止する〔2026/05/25 追記〕**。複数 seed(3 seeds 推奨)で variance を取り、平均±標準偏差を併記。per-class AP を全 15 クラスで報告し、AP_rare と AP_common を分離（Forceps は 12.21% で AP_common に分類、AP_rare は Skewer / Syringe の 2 クラスのみ）、Forceps × Tweezers × Needle Holders × Bipolar Forceps の 4×4 sub-confusion matrix を可視化する（G4/B2 サーベイ）。
	- **S0 を正当な Δ 基準点として採用する strict 3 条件〔2026/05/24 追加、§15.4 A と整合〕**：S0 の完了判定「VarifocalNet 公式 SOTA 45.8 を上回る」は、以下 3 条件を満たした上でのみ意味を持つ。(1) データ split が EgoSurgery-Tool 公式（train 9657 / val 1515 / test 4265 images）、(2) test_cfg が locked-down 値（score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6）、(3) metrics.json の `eval_recipe` がこれらと一致。この 3 条件を満たさない S0 は Δ 基準点として使用できず、VarifocalNet との比較自体が無効となる（§15.1・§15.2 の失敗事例を参照）。
	#### S1:空間 bbox → mask〔§0.1 Phase-1 条件付きステップ、mask アノテーション入手で起動〔2026/05/21 格下げ〕
	- **実行サーバー：RTX A6000 ×1〜2（Phase-1 派生実験）**
	- **位置づけ**：本ステップは mask アノテーションを前提とするため、**Phase-1（mask 入手で起動する条件付きステップ）** に格下げする。Phase-0 主経路は S0 から S2 へ直接進む（S1 をスキップ）。mask 入手時点で S1 を起動し、Stage A1（§5）と一体で実行する。
	- **動かす軸**:空間(bbox → mask)。
	- **目的**:mask 入力で、下流の関係モジュール（S7）に必要なノード特徴(mask shape, mask overlap)を確保。mask パイプラインの動作確認。
	- **比較対象**:S0（bbox 検出ベースライン）。
	- **主要指標**:Δ mAP(S1 − S0)、mIoU、稀少クラス mAP。
	- **採用アーキテクチャの 3 ライン比較〔§12.12 B4 と整合〕**：S1 では以下 3 ラインを比較する。第 1 ライン = DINOv2 ViT-L/14（frozen、後段で LoRA 解凍）+ EoMT decoder（adapter/pixel decoder 不要、推論時 Ego 単独・低 fps 運用に最適）。第 2 ライン = DINOv2 ViT-L/14 + ViT-Adapter + Mask2Former（EgoSurgery-HTS 公式 SOTA の再現）。第 3 ライン = Mask DINO（S0 検出器との連続性）。補助 = SAM 2（frozen, bbox prompt）で hand-tool mask を自動補完。EoMT が Mask2Former 公式値（tool 40.9 / hand-tool 56.6）を +2 ポイント以上上回らない場合は Mask2Former を第 1 ラインに格上げする（§9 #6 と整合）。
	- **期待**:mAP は同等もしくは微増。主目的は mask パイプラインの動作確認と、後段で使う mask 特徴の品質保証。
	- **失敗時**:mAP が大きく下がる場合、segmentation head の loss weight や収束を見直す。
	#### S2:タスク + 手検出
	- **実行サーバー：RTX A6000 ×1（基盤整備）**。S0 の重みを初期値として引き継ぐが、Δ 基準点には直接影響しないため A6000 で許容。
	- **動かす軸**:タスク(Tool → Tool+Hand)。空間は bbox のまま（Phase-0 主経路）。
	- **目的**:マルチタスク学習の最小単位を構築。手検出を入れても術具検出が劣化しないことを確認(negative transfer の有無)。
	- **比較対象**:S0（Phase-0 主経路では S0→S2 直行。mask 入手済みで S1 を実施した場合は S1 とも比較）。
	- **主要指標**:Δ mAP(S2 − S0)≈ 0、Hand 4 クラス mAP、own/other 区別精度。
	- **期待**:術具 mAP は維持。
	- **失敗時**:術具 mAP が S0 から大きく剤化した場合は catastrophic forgetting を疑う。§14 では S0 best から fine-tune した際に tool mAP が 0.3% まで崩壊した実例があり、loss weight 動的化だけでは不十分である。以下の構造的対策を順に試す：(1) layer-wise lr（backbone と既存 tool head の lr を S0 の 1/10 に下げ、新規 hand head のみ通常 lr）、(2) backbone の段階的凍結解除（最初の数 epoch は backbone を凍結し hand head のみ学習）、(3) tool head の出力保持のための KD（S0 を teacher とし tool クラスのロジットに KL 蜂注损失）、(4) best checkpoint 選択を hand mAP 単独ではなく tool 剤化にペナルティをかける複合指標とする。それでも未解決なら loss weight 動的化(uncertainty weighting / GradNorm)。
	#### S3:タスク + Phase head(frame-by-frame、弱ベースライン)
	- **実行サーバー：RTX A6000 ×1（パイプライン確認）**
	- **動かす軸**:タスク(+ Phase)+ 方向性(単方向 → Det→Phase 弱)。
	- **目的**:Phase head を載せるパイプラインの動作確認。**Phase 認識精度は低くてよい**(frame 単独で 9 クラスを当てるのは原理的に困難)。
	- **比較対象**:S2。
	- **主要指標**:Phase frame-accuracy(基準として記録のみ)、術具検出 Δ mAP(S3 − S2)。
	- **注意**:Phase 認識性能の絶対値はここでは評価しない。**長距離時系列を入れる S4 まで判定を保留**。
	- **実装上の注意：Phase head の class weights〔2026/05/24 追加、§14 と整合〕**：§14 で S3 初回実行時に class weights が不適切だったため val accuracy が 0.5% に崩壊した実例がある。class weights を無効化して回復し、frozen ResNet50 + PhaseHead で phase accuracy 0.593±0.008 を得た。したがって Phase 損失（`L_phase`）の class weights はデフォルト無効とし、有効化する場合も weight の最大/最小比を上限（例 10 倍）でクリップし、label smoothing（0.1）を常に併用する。学習初期（1、2 epoch）に val accuracy が極端に低い場合は class weights を自動無効化するセーフガードを入れる。
	#### S4:時系列 frame → 長距離(§2.5 (b) 基準点)
	- **実行サーバー：第 1 波（TeCNO・SR-Mamba）= RTX 6000 Ada ×1（Δ 基準点）、第 2 波（HID-SSM・SKiT・Surgformer 等）= RTX A6000 ×1〜2（D-B ベンチマーク拡充）**
	- **動かす軸**:時系列(frame → 長距離)。
	- **目的**:Phase 認識を成立させる長距離時系列モデルを導入。**§2.5 (b) 工程認識単独モデルの基準点を確定**。
	- **比較対象**:S3(frame 単独の弱基準)。
	- **主要指標**:Phase macro F1、Edit score、Segmental F1@\{10, 25, 50\}、Dissection / Closure 内部 F1。
	- **重要**:この段階の Phase head 入力は **画像 global feature**(object token はまだ使わない)。これが §2.5 (b) の基準点となる。
	- **モデル候補と優先順位**（D2/C3 サーベイ）:TeCNO（baseline）→ SKiT（online 上限・低計算）→ Surgformer（offline 上限）→ SR-Mamba（SSM baseline）→ SPRMamba → HID-SSM（2025 SOTA）。**Surgformer / SR-Mamba / SPRMamba / HID-SSM の初の EgoSurgery-Phase ベンチマークを走らせることが明確な publishable 貢献**。常に causal 版と bidirectional 版を並行訓練・評価する。
	#### S5:Det→Phase 完全版(H2 一次検証)
	- **実行サーバー：RTX 6000 Ada ×1（Δ 基準点）**
	- **動かす軸**:方向性(global feature 入力 → object token 入力に切替)。
	- **目的**:**H2 の一次検証**。object-centric temporal representation が global feature を上回るか。
	- **比較対象**:S4。
	- **主要指標**:**Δ Phase F1 = S5 − S4**、Dissection / Closure 内部 segmental F1@k の差分。
	- **成功条件**:Δ Phase F1 \> 0、特に Dissection / Closure 内部での改善が顕著。
	- **失敗時**:object token の品質(=検出 mAP)が低いと Phase 入力が悪化する。S2 / S0 の品質を再確認。
	#### S6:方向性 双方向(H1 一次検証)
	- **実行サーバー：RTX 6000 Ada ×1（Δ 基準点）**。S6 の ablation（FiLM vs cross-attention vs SAK）は RTX A6000 ×1〜2 で並行実行可。
	- **動かす軸**:方向性(Det→Phase → 双方向)。
	- **目的**:**H1 の一次検証**。Phase 文脈の検出器フィードバックが術具検出を改善するか。
	- **比較対象**:S0(術具検出単独、bbox)、および S5(片方向)。
	- **主要指標**:Δ mAP(S6 − S0)（全体・稀少クラス・形状類似ペア）、S6 − S5 の差分(双方向化の効果)。
	- **成功条件**:Δ mAP \> 0、稀少クラス（Skewer / Syringe）・形状類似ペア（Forceps / Tweezers / Needle Holders）で顕著。
	- **注意**:gradient 制御(stop-gradient、Phase 経路の loss weight ramp)で Phase 側の不安定性が Detection を退化させないようにする。**S5 が安定収束していることが前提**。
	#### S7:関係モジュール導入(H3 検証)〔§0.1 Phase-1 条件付きステップ、mask / hand-tool アノテーション入手で起動〔2026/05/21 格下げ〕
	- **実行サーバー：RTX A6000 ×1〜2（Phase-1 派生実験）**
	- **位置づけ**：本ステップは mask（および mask から生成する hand-tool 関係疑似ラベル）を前提とするため、**Phase-1（mask / hand-tool アノテーション入手で起動する条件付きステップ）** に格下げする。Phase-0 主経路は S6 から S7.5→S8 へ進み（S7 をスキップ）、mask 入手時点で S6 の後に S7 を挿入する。mask が M2 期間内に入手できない場合は S7 と H3 を本論文の中核主張から外し、Phase-0（H1・H2・H4・D-A・D-B）で論文を成立させる。
	- **動かす軸**:関係(無 → 有)。あわせて空間も bbox → mask となる（S1 と一体で起動）。
	- **目的**:**H3 の検証**。手-術具関係モジュールが H1 / H2 を増幅するか。
	- **比較対象**:S6(関係モジュール無)。
	- **主要指標**:Δ mAP・Δ Phase F1 が S6 比でさらに拡大するか。関係認識 F1(疑似ラベル基準、診断指標)。
	- **失敗時**:関係モジュールの過学習が疑われる場合、graph の hidden dim を下げる / dropout を増やす / 関係ラベル疑似生成の閾値を緩める。
	#### S7.5：Exo 視点多様性の予備診断〔2026/05/21 新設、§4.7・§9 #5 の 2 段階撤退ラインと整合〕
	- **実行サーバー：RTX A5000 ×2〜3（少量 Exo サブセットでの診断）**
	- **動かす軸**：なし（S8 の手前に挿入する診断ステップ）。
	- **目的**：S8 のフル SSL パイプラインを走らせる前に、Exo 多視点が view-consistent SSL の学習信号として成立するかを少量データで予備診断する。A4 サーベイは、Exo の画角が術野近傍に限定されるため Ego-Exo 間の視野重複が大きすぎ、view-consistent SSL の信号が弱い可能性を指摘している。
	- **診断内容**：少量の Exo サブセットで cross-view contrastive を試験的に学習し、表現品質を (a) 視点不変性（同時刻の異視点ペアの表現類似度）、(b) 時刻弁別性（temporal hard negative との分離度）の 2 軸で計測する。
	- **早期縮退の判定**：視野重複が大きすぎて (a)(b) のいずれも有意な信号が得られないと判断されれば、S8 のフル SSL を走らせる前に Exo の役割を「Phase label の弱教師あり転写のみ」に早期縮退する（§9 #5 の第 1 段階撤退ライン）。信号が得られれば予定通り S8 へ進む。
	#### S8:Exo 視点導入(H4 検証)
	- **実行サーバー：Stage B-C の Exo SSL 学習 = RTX A5000 ×5 DDP 専有、Ego fine-tuning およびΔ 測定 = RTX 6000 Ada ×1**
	- **動かす軸**:視点(Ego → Ego+Exo)、時系列(長距離 → 長距離 + Exo 高 fps)。
	- **目的**:**H4 の検証**。view-consistent SSL と teacher-student 蒸留で動作・時間表現を Ego に注入し、Δ をさらに引き上げる。
	- **比較対象**:S7(Exo SSL 無し)。
	- **主要指標**:
		- Δ mAP・Δ Phase F1 が S7 比でさらに拡大するか
		- Ego 単独推論時の **工程境界周辺の予測安定性**(境界フレーム前後 N フレームでの予測一致率)
		- **隣接フレーム間の表現類似度**(SSL で時間的に滑らかな表現が獲得されたかの診断)
	- **重要**:**推論時は Exo 経路を完全に切り離す**(branch-pruning)。学習時のみの効果であることを確認するため、Exo 経路の重みを抜いた推論で性能を再測する。
	#### S9:統合 fine-tuning と最終評価(H1・H2・H4 最終検証、mask 入手時は H3 も)
	- **実行サーバー：最終 Δ 測定用の本実験 = RTX 6000 Ada ×1、ablation・転移検証 = RTX A6000 ×1〜2 で並行実行**
	- **動かす軸**:なし(全要素 on で Stage D fine-tuning)。
	- **目的**:Stage D 統合 fine-tuning による最終性能の確定。Phase-0 主経路では H1・H2・H4 の最終結論を出し、mask 入手済みの場合は H3 も含めて最終検証する。動作ラベル追加(§9 #1)の要否を判断。
	- **比較対象**:S8(Stage C 終了直後)、および §2.5 (a)(b)(c) の全比較対象。
	- **主要指標**:全 Δ 指標、絶対精度、§7.3 内部診断、§7.4 臨床的視点。各タスクで Table I（絶対スコア）+ Table II（Δ 表、MT−ST、paired bootstrap で有意差をマーク）+ Supplementary（Phase-conditional AP heatmap、形状類似 sub-confusion matrix）の形式で報告する（G4 サーベイ）。EgoSurgery は 21 動画・8 術者・1 施設と小規模のため、leave-one-surgeon-out または stratified k-fold + paired bootstrap 信頼区間を必須とする。転移検証は PhaKIR（phase + instrument）・CholecT45（triplet）・EgoExOR（scene graph）で行う。
	#### 検証順序の依存関係(なぜこの順序か)
	- **S1 は Phase-1 条件付き(§0.1)**:mask は関係モジュール（S7）の semantic prior として必要。Phase-0 主経路では S0→S2 を直行し、mask 入手時点で S1 を S0 の後に挿入する。S1 を挿入する際は S2 より前（空間化先、手検出後）とし、S2 の結論が S1 の差分に汚染されないよう同一 backbone で再学習する。
	- **S4 → S5(長距離先、Det→Phase 切替後)**:Phase は本質的に時系列タスクであり、frame 単独で H2 を検証しても意味が無い。長距離時系列を共通基盤として先に確立する。
	- **S5 → S6(Det→Phase 先、Phase→Det 後)**:Det → Phase は片側の信号が弱くても破綻しにくいが、Phase → Det は Phase が未収束だと検出を退化させる(§4.6 の gradient 制御の理由)。先に Phase を安定化させる。
	- **S7 を H1 / H2 検証後に**:関係モジュールは H1 / H2 を増幅する仮説なので、まず素の H1 / H2 の効果を測ってから関係を入れる。先に入れると増幅効果が H1 / H2 本来の効果と分離できない。
	- **S8 を最後に**:Exo SSL は上限引き上げ仮説。素の Ego マルチタスクが H1 / H2 / H3 で動いていることを確認してから、Exo の上積みを評価する。
	#### 全体注意事項
	- **共通設定の厳格化**:S0〜S9 で `seed = 42`、optimizer、scheduler、augmentation、batch size、**GPU 構成（単一 GPU or DDP 枚数）** を完全に揃える。変える場合は明示的に注釈を付ける。**DDP 使用時は、同一 Δ 比較群内の全モデルを同一 GPU 構成で揃えること、effective batch size を eval_recipe に記録すること、lr スケーリングの適用有無を config に明記することが必須（§8.0 条件 (4)(5)(6)、2026/05/25 追記）**。
	- **基準点(S0, S4)の信頼性**:Δ の妥当性はこれらに依存するため、**複数 seed(最低 3 seeds)で variance を取り、平均±標準偏差を併記**する。Δ が 1σ 以内であれば改善と主張しない。ここでの 1σ は「同一 eval recipe での 3-seed std」であり、recipe 差由来の variance は含めない（§15.4 C）。**さらに S0 は §15.4 A の strict 3 条件（公式 split / locked-down test_cfg / metrics.json の eval_recipe 一致）を満たさなければ Δ 基準点として使用できない〔2026/05/24 追記、§15 と整合〕**。旧 split / 旧 test_cfg で測定した数値（§15.5 退避済み）は Δ 基準点に使えない。
	- **計算コストの見積もりと GPU 割り当て**〔2026/05/21 更新：旧記述の A100 前提を実環境に改訂〕:S0〜S9 を 3 seeds で回すと最小 30 実験、ablation 軸(A1〜A7)と組み合わせると 50〜100 実験規模。実行環境は RTX 6000 Ada（48GB）/ RTX A6000×2（48GB）/ RTX A5000×5（24GB）/ Quadro RTX 8000×2（48GB）。**Δ の基準点に影響する本実験（S0・S4 第 1 波・S5・S6）は RTX 6000 Ada に固定**し、ablation・第 2 波ベンチマーク・転移検証は A6000×2 に、Stage B-C の Exo SSL は A5000×5 を DDP 専有で割り当てる。Quadro RTX 8000 は bf16 非対応のため軽量実験・推論評価・前処理専用とする。**Stage B-C は §12.16 が想定する 4×A100 80GB×3 週間の環境には届かないため、Exo を全 25 fps ではなく Ego 同期窓内で 5 fps 程度にサブサンプリングして計算量を圧縮する**ことを前提とする。**S4 終了時点で実験管理パイプライン(Hydra + W&B、§8)を完全に整備**しておく。
	- **早期打ち切り基準**:
		- S5(H2 一次検証)で Δ Phase F1 ≤ 0 が出た場合 → object token 品質を疑い S1 / S2 に戻る
		- S6(H1 一次検証)で Δ mAP ≤ 0 → gradient 制御と loss weight を見直す
		- 仮説検証の早い段階で破綻が見えれば、無駄な後段実験を避けられる
	- **追加で回せる ablation セル**:S6(双方向)と S7(関係有)は config で個別 on/off できる構造のため、必要に応じて以下のセルも回せる。優先度は低いが、各仮説が機能する条件を絞り込むのに有用。
		- (双方向無 × 関係有):関係モジュールが片方向だけで効くか
		- (Det→Phase × 関係有):H2 + H3 のみの組み合わせ(H1 抜き)
		- (Phase→Det 単独 × 関係無):H1 のみの最小構成
	- **動作ラベル導入判断のタイミング**:S5 / S6 の結果が想定を下回った場合、§9 #1 の動作ラベル追加判断を **M5 まで待たずに前倒し** する選択肢を持つ。具体的には、Phase 認識精度が Dissection / Closure 内部で頭打ちなら、より細粒度の動作ラベルが必要というシグナル。
---
## 13. 実験実行手順書（S0→S9・CVPR 投稿まで） {toggle="true"}
	本セクションは §10.1（S0〜S9 ロードマップ）・§8（実験運用）・§12（サーベイ知見）を**実行レベルの手順**に翻訳したものである。§10.1 が「何を・どの順序で・何で測るか」を定めるのに対し、本 §13 は「実際に手を動かす順序と各ステップの完了判定」を定める。CVPR のようなトップティア国際会議への投稿を前提とする。
	### 13.0 本手順書の位置づけと前提
	- **3 つの最重要原則**：(1) Δ 指標の信頼性がすべての前提であり、S0/S4 の基準点が汚染されると全 Δ が無効化される（§10.1 共通設定の厳格化）。(2) §2.6 の二段構え（H1〜H4 の Δ が非有意でも D-A・D-B で論文成立）を常に意識し、両輪を同時に育てる。(3) §0.1 Phase-0 主経路（S0→S2→S3→S4→S5→S6→S7.5→S8→S9）を死守し、S1・S7 は mask 入手で起動する条件付きとする。
	- **データ可用性の前提**：mask / hand-tool アノテーションは M2 期間内（数ヶ月後）に入手見込み（§0.1）。Phase-0 主経路（S0〜S4）は mask を一切要さないため、最初の数ヶ月を Phase-0 に充て、その完了が mask 入手と重なるよう工程を組む。
	- **計算環境の前提〔2026/05/25 更新：§8.0 を最優先規範として明記〕**：RTX 6000 Ada（48GB、Ada 世代、Δ 基準点専用）/ RTX A6000×2（48GB、ablation・第 2 波・転移検証）/ RTX A5000×5（24GB、Stage B-C SSL を DDP 専有）/ Quadro RTX 8000×2（48GB、bf16 非対応のため軽量実験・推論・前処理専用）。S0〜S9 の本実験は原則 RTX 6000 Ada に統一し、世代混在による数値再現性の崩れを避ける（§4.2・§10.1 と整合）。**ただしサーバー割り当ての運用ルールは §8.0「サーバー割り当ての運用原則」を最優先の規範とする**。とりわけ §8.0 の「暫定運用：RTX 6000 Ada 未配備期間」の規定により、RTX 6000 Ada が未配備の期間は Δ 基準点学習（S0・S4 第 1 波・S5・S6 等）を bengio（RTX A6000×2）上で実行することを暫定的に許容する。暫定運用にあたっては §8.0 が定める 3 条件——(1) 同一の Δ 比較群（例：S0 の VarifocalNet・Mask DINO・Co-DETR、A1 の単独モデルとマルチタスクモデル）は必ず同一サーバー上で揃えて測定する、(2) metrics.json の eval_recipe.server_name と各実験フォルダの server.txt にサーバー名を記録する、(3) RTX 6000 Ada 配備後に Δ 基準点を再測定する必要が生じうることを §14 に明記する——をすべて満たすこと。§13.2〜§13.4 の各ステップに記載の「実行サーバー」は RTX 6000 Ada 配備後の最終形であり、未配備期間は上記 §8.0 暫定運用に読み替える。
	### 13.1 フェーズ I：基盤整備（S0 開始の 2〜3 週間前）
	- **I-1 計算環境とデータアクセスの確定**：(a) GPU 時間を確認し「3 seeds × 50〜100 実験」が収まるか逆算、収まらなければ §13.7 の 3 層分類で削る計画を先に立てる。(b) 転移検証用ベンチマーク（PhaKIR・GraSP・CholecT45・EgoExOR）のデータアクセス認証申請を**即日開始**（§9 #8）。(c) mask / hand-tool アノテーションの入手源と見込み時期を指導教員に確認し §3.1 に追記。
	- **I-2 実験管理パイプラインの構築**（§8 準拠、S0 開始前に前倒し完成）：Hydra で `model/data/train/stage` の 4 軸 config group、S6・S7 の on/off をフラグ化。W&B で全 Stage を同一 project・Stage 別 group、LibMTL の Δp 指標を統合。実験 ID は `timestamp_confighash`。`seed=42`・`deterministic=True`・`cudnn.benchmark=False` を固定。**CVPR 用に、per-class AP・confusion matrix・Δ 計算を自動で metrics.json に吐くスクリプトをこの段階で実装**（S9 で Table I/II/Supplementary を手作業で作ると破綻するため）。
	- **I-3 サーベイの最終確認**：§11.1 の実施順序表に従い、S0〜S2 開始前に必要な高優先細目（A1, A2, B1, B2, B3, B4, C1, C2, F1, G4）が §12 で網羅済みであることを確認。本研究は S0 に即着手可能な状態にある。
	- **完了判定**：ダミーの 1 エポック学習を流し、W&B に per-class 指標と Δ 計算枠が自動記録されることを確認できた時点。
	### 13.2 フェーズ II：Phase-0 主経路 — 基盤構築（S0〜S4）
	- **S0 術具検出ベースライン**【M1 前段・§2.5(a) 基準点、研究全体で最も慎重に固めるステップ】：**実行サーバー：RTX 6000 Ada ×1（Δ 基準点専用）**。Mask DINO（DINOv2 ViT-L/14-with-registers + ViT-Adapter）・VarifocalNet・Co-DETR を準備し bbox-only で学習。Seesaw Loss（p=0.8, q=2.0）+ RFS（t=0.001）+ bbox-level Simple Copy-Paste + post-hoc Logit Adjustment を有効化。3 seeds で variance を取り平均±標準偏差を併記。per-class AP を全 15 クラス、稀少クラス（Skewer / Syringe）と形状類似ペア（Forceps / Tweezers / Needle Holders / Bipolar Forceps）の 4×4 sub-confusion matrix を可視化。RTX 6000 Ada で bf16 + 勾配チェックポイント実行。**完了判定**：VarifocalNet 公式 SOTA（tool mAP 45.8）を上回ること。**判断ポイント #6**：Mask DINO vs Co-DETR を APr で比較し 3pt 以上差があれば S1 以降を Co-DETR ベースに切替。
		- **DDP 2 GPU 運用の実装要件〔2026/05/25 追記〕**：RTX 6000 Ada 未配備期間は bengio（A6000 ×2）で DDP 2 GPU 実行を許容する（§8.0 暫定運用）。実装上の対応は以下の通り。
			- **(a) effective batch size の倍化**：DDP 2 GPU では per-GPU batch size を単一 GPU 時と同じまま保ち、effective batch size を 2 倍にする。例：単一 GPU で batch_size=2 だった場合、DDP 2 GPU では effective batch size = 4。これに伴い learning rate を線形スケーリング（lr × 2）する。スケーリングの適用と effective batch size は config と `eval_recipe` に明記する（§8.0 条件 (5)(6)）。
			- **(b) ****`MMDetTrainer`**** への DDP 対応**：`MMDetTrainer` に以下の機能を追加する。(i) `_build_eval_recipe()` に `gpu_count`（`torch.cuda.device_count()` または `WORLD_SIZE` 環境変数）と `effective_batch_size`（`gpu_count × per_gpu_batch_size`）を記録するフィールドを追加。(ii) DDP 学習時に `DistributedDataParallel` の初期化と `DistributedSampler` の設定を `setup()` で行う。(iii) 評価時は rank=0 のみで `_write_metrics` を実行し、重複書き込みを防止。(iv) `SyncBatchNorm` への変換は BN を使うモデル（ViT-Adapter 等）でのみ適用し、LayerNorm 主体の ViT では不要。
			- **(c) ****`run_s0.sh`**** の DDP 起動への書き換え**：単一 GPU 起動（`python tools/train.py ...`）を `torchrun --nproc_per_node=2 tools/train.py ...` に書き換える。各 seed ・各 detector の学習ブロックをすべて `torchrun` 経由で起動する。`MASTER_PORT` は seed/detector ごとにユニークな値を設定し、並列実行時のポート競合を回避する。例：`MASTER_PORT=$((29500 + seed_index * 3 + detector_index)) torchrun --nproc_per_node=2 tools/train.py model=vfnet seed=42 ...`。
			- **(d) 全モデル統一**：上記 (a)(b)(c) を VFNet・Mask DINO・Co-DETR の全モデルに同一に適用する。特定のモデルのみ単一 GPU、他のモデルは DDP という混在は禁止（§8.0 条件 (4)）。
	- **S2 手検出の追加**【M1・Phase-0 版、S0→S2 直行】：**実行サーバー：RTX A6000 ×1（基盤整備）**。Mask DINO の hand head を own/other × L/R の 4 クラスに拡張。RoHan の Artificial Gloves augmentation + iterative 半教師ドメイン適応を再現。視野位置事前分布を spatial Gaussian prior として注入。手姿勢推定（keypoint/MANO）は導入しない（§12.11）。**完了判定**：hand mAP \> 65、own/other accuracy \> 90%、L/R accuracy \> 95%、かつ術具 mAP が S0 から劣化しない。
	- **S3 Phase head のパイプライン接続**【M2 前段】：**実行サーバー：RTX A6000 ×1（パイプライン確認）**。S2 出力に Phase head（frame-by-frame、弱ベースライン）を接続、方向性を Det→Phase 弱に。Phase 認識の絶対精度は評価しない（S4 まで保留）。**完了判定**：パイプライン動作、術具検出 Δ mAP が劣化しないこと。
	- **S4 長距離時系列モデルの導入**【M2 後段・§2.5(b) 基準点・D-B の中核、2 段階運用】：**実行サーバー：第 1 波（TeCNO・SR-Mamba）= RTX 6000 Ada ×1（Δ 基準点）、第 2 波（HID-SSM・SKiT・Surgformer 等）= RTX A6000 ×1〜2（D-B ベンチマーク拡充）**。第 1 波（必須）= TeCNO・SR-Mamba を causal/bidirectional 並行学習、Phase head 入力は画像 global feature。第 2 波（S4 安定後）= HID-SSM 主軸に SKiT・Surgformer・SPRMamba を順次追加（D-B 貢献）。temporal smoothing・transition loss・phase order prior を正則化に。**完了判定**：Phase macro F1・Edit score・Segmental F1@\{10,25,50\}・Dissection/Closure 内部 F1 が安定取得。TeCNO が Jaccard 70% 未満なら Mamba 系へ即移行。**S4 終了時点で §13.1 I-2 のパイプラインが完全整備されていることを再確認**。
	### 13.3 フェーズ III：中核仮説の検証（S5〜S6）
	- **S5 Det→Phase 完全版**【H2 一次検証・M3 前半】：**実行サーバー：RTX 6000 Ada ×1（Δ 基準点）**。Phase head 入力を global feature → object token（bbox 由来：ROI Align + bbox 位置 + クラス埋め込み、mask shape なし）に切替。3 段階比較（global feature baseline / unsupervised slot baseline / Proposed）。**完了判定（成功条件）**：Δ Phase F1 = S5 − S4 \> 0、global feature baseline に対し +5pt 以上。**早期打ち切り**：Δ Phase F1 ≤ 0 なら object token 品質を疑い S2/S0 に戻る。
	- **S6 双方向化**【H1 一次検証・M3 中盤】：**実行サーバー：本実験 = RTX 6000 Ada ×1（Δ 基準点）、注入方式 ablation（FiLM vs cross-attention vs SAK）= RTX A6000 ×1〜2 で並行**。方向性を双方向に。primary 注入は cross-attention（Mask DINO decoder に c_phase トークン）、entropy gating 実装、gradient 制御（stop-gradient・loss weight ramp）。ablation 下限として FiLM も実装。**完了判定（成功条件）**：Δ mAP = S6 − S0 \> 0、稀少クラス・形状類似ペアで顕著。**早期打ち切り**：Δ mAP ≤ 0 なら gradient 制御と loss weight を見直す。
	### 13.4 フェーズ IV：Exo 補助経路の検証と Phase-1（S7.5〜S9）
	- **【条件付き】S1・S7 Phase-1 の起動**：**実行サーバー：RTX A6000 ×1〜2（Phase-1 派生実験）**。mask / hand-tool アノテーション入手後に起動（§0.1・§9 #9）。S1（mask 化）= EoMT / Mask2Former / Mask DINO の 3 ライン比較 + SAM 2 補助。S7（関係モジュール）= Mask DINO query をノードとする two-stage GNN、エッジ疑似ラベルは mask-IoU から自動生成、200 フレーム人手検証で 80% 以上担保。mask 未入手の場合は S1・S7 をスキップし §2.6 の二段構え（H1・H2・H4 + D-A・D-B）で論文化。
	- **S7.5 Exo 視点多様性の予備診断**【撤退ライン第 1 段階】：**実行サーバー：RTX A5000 ×2〜3（少量 Exo サブセットでの診断）**。少量 Exo サブセットで cross-view contrastive を試験学習し、(a) 視点不変性・(b) 時刻弁別性の 2 軸で表現品質を計測。いずれも有意な信号が得られなければ S8 のフル SSL を走らせる前に Exo を「Phase label 弱教師転写のみ」に早期縮退（§9 #5 第 1 段階）。
	- **S8 Exo 視点導入**【H4 検証・M4、最大の難所】：**実行サーバー：Stage B-C の Exo SSL 学習 = RTX A5000 ×5 DDP 専有（Exo を 5 fps 程度にサブサンプリングして計算量圧縮）、Ego fine-tuning および Δ 測定 = RTX 6000 Ada ×1**。Stage B（VideoMAE v2 + hand-tool-guided MAE + cross-view contrastive + temporal hard negative）・Stage B′（DINO/iBOT 継続事前学習、\<2% gain ならスキップ）・Stage C（時間同期 contrastive + Phase 分布整合 KL + tool-set 弱整合 + Quattrocchi 式 2-level KD）。A5000×5 を DDP 専有、Exo を 5 fps 程度にサブサンプリングして計算量圧縮。**branch-pruning 検証**：推論時に Exo 経路の重みを抜いて性能を再測。**撤退ライン第 2 段階**：Δ の追加改善幅が 1σ 以内なら Exo を弱教師転写のみに縮退。
	- **S9 統合 fine-tuning と最終評価**【H1〜H4 最終検証・M5】：**実行サーバー：最終 Δ 測定用の本実験 = RTX 6000 Ada ×1、ablation（A1〜A7）・補助 ablation・転移検証 = RTX A6000 ×1〜2 で並行実行**。Stage D で全要素 on、損失重み付け FAMO + DB-MTL、勾配制御 GCond、LibMTL Δp 監視。中核 ablation A1〜A7 を完走。補助 ablation（損失重み付け 5 条件・SSL 構成要素分解・hand-tool-guided MAE vs random mask・長尾損失独立ベンチマーク等）。転移検証（PhaKIR・CholecT45・EgoExOR）。統計処理は leave-one-surgeon-out または stratified k-fold + paired bootstrap を必須。
	### 13.5 フェーズ V：評価結果の出力と CVPR 投稿
	- **報告フォーマット**（§10.1 S9・§12.24）：各タスクで Table I（絶対スコア）+ Table II（Δ 表、paired bootstrap で有意差マーク）+ Supplementary（Phase-conditional AP heatmap・形状類似 sub-confusion matrix）。
	- **貢献の二段構え**（§2.6・§7.1）：Δ が有意なら H1〜H4 を主貢献として前面に。Δ が 1σ 以内で非有意なら、(1) 単一タスク絶対精度 SOTA 更新、(2) D-A（object-centric token × block-diagonal SSM）、(3) D-B（EgoSurgery-Phase 初の長距離ベンチマーク）を方法論的貢献として主張。**A7（D-A 検証）と D-B（第 2 波ベンチマーク）は Δ の成否に関わらず必ず完走する**。
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
<td>S0（検出ベースライン）</td>
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
<td>S5（H2）・S6（H1）</td>
<td>入手済み</td>
</tr>
<tr>
<td>月 8〜9</td>
<td>Phase-1</td>
<td>S7（関係モジュール・H3）</td>
<td>入手済み</td>
</tr>
<tr>
<td>月 9〜10</td>
<td>Exo 検証</td>
<td>S7.5（予備診断）・S8（H4）</td>
<td>—</td>
</tr>
<tr>
<td>月 10〜12</td>
<td>統合</td>
<td>S9（統合 fine-tuning・全 ablation・転移検証）</td>
<td>—</td>
</tr>
<tr>
<td>月 12〜14</td>
<td>執筆</td>
<td>評価結果出力・論文執筆・rebuttal 準備</td>
<td>—</td>
</tr>
	</table>
	mask 入手（月 3〜4）と S0〜S3 完了がほぼ同期するため待ち時間ロスがほぼゼロになる。CVPR 締め切りが確定し次第この月割りを圧縮する（直近締め切りなら S6 完了 + D-B ベンチマークを必達ラインに絞る）。
	### 13.7 実験の 3 層分類（GPU 制約を反映）
	- **必達ライン（これがないと論文が成立しない）**：S0（VarifocalNet 45.8 超え + Mask DINO 初ベンチマーク）、S4 第 1 波（TeCNO + SR-Mamba、causal/bidirectional）、S5（H2 一次検証）、S6（H1 一次検証）、ablation A1・A2・A7（D-A）、D-B 最小ベンチマーク（HID-SSM 追加）。→ RTX 6000 Ada で確実に回し切る。
	- **努力ライン（あると論文が強くなる）**：S1・S7・H3（mask 入手後、ablation A5）、S8（H4、ablation A6）、S4 第 2 波の残り（SKiT・Surgformer・SPRMamba）、ablation A3・A4、長尾損失独立ベンチマーク。→ A6000×2 と A5000×5 に振り分け。
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
<td>**Δ 基準点専用**（S0・S4 第 1 波・S5・S6）。最優先・本実験の主戦場</td>
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
	- **位置づけの修正**：§10.1 S0 手順の「完了判定 = VarifocalNet 公式 SOTA 45.8 を上回る」は、**エポック数を含む学習設定が不明のまま**の状態では有意にならず、eval_recipe だけでは再現性を保証できない。今後 §10.1 S0 手順の「完了判定」を以下に書き換える（本節を根拠として次ステップで §10.1 を修正）：**(1) §15.4 A の strict 3 条件に加え、(2) 12 / 24 / 36 epochs の各時点で checkpoint を保存し val mAP で early stopping、3-seed std を併記、(3) Δ 比較群（S0 全 detector）で採用エポック数を統一、(4) VarifocalNet 公式 45.8 を上回ることを確認**。エポック数の論文公式値は 2026/05/29 時点で論文・公式リポジトリのいずれにも未公開であり、現状は mmdet 慣行の 1x = 12 epochs を暫定採用する。著者への問い合わせ結果は本節に追記する。
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
	- **真の異常値**：Forceps AP 0.238（val 154 instances、データ量は十分）と Gauze AP 0.202。Forceps は Tweezers 0.687 / Needle Holders 0.812 という高 AP クラスにとられている構造であり、Gauze は非剛体のため bbox 局在が原理的に困難。**これは §2.1 H1 の根拠「形状類似ペア（Forceps / Tweezers / Needle Holders）の混同は静的視覚特徴のみでは識別困難」を実証しており、S6（Phase→Detection）で Forceps AP の改善幅に期待をもてるストーリーに整合**する。
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