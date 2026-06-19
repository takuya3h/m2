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
