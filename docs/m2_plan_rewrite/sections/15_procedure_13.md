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
