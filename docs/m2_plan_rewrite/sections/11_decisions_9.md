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
