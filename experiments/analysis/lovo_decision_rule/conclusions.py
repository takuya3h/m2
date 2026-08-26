"""再判定の対象となる既存結論の一覧（Phase A の成果）。

SPEC.md Task 2 Step 2 が挙げた 7 種類を軸に、報告書 §3 の LOVO 由来の結論を並べる。
**この一覧は素の値の所在を実測してから作った。** 在ると仮定した行は無い。
"""

# kind: SPEC.md Task 2 Step 2 の 7 種類への割り当て
K_PASS = "術具の情報を工程認識へ渡すことの効果"
K_GAP = "全体平均の特徴を足すことの害"
K_ORACLE = "オラクルの術具存在を与えたときの追加の利得"
K_DENOISE = "入力側の雑音除去の効果"
K_PRUNE = "工程を弁別しない術具を落とすことの効果"
K_SHAPE = "誤りの形による壊れ方の違い"
K_SOURCES = "複数の凍結源にわたる再現性"
K_OTHER = "その他（上記 7 種類に入らない既存結論）"

METRICS = [
    ("phase_accuracy", "accuracy"),
    ("phase_macro_f1", "macro-F1"),
    ("phase_edit_score", "edit"),
    ("phase_seg_f1_50", "seg-F1@50"),
]

# id, kind, 台本, 処理側の腕, 基準側の腕, 報告書の該当節, 備考
CONCLUSIONS = [
    ("C01", K_PASS,    "gap_vs_presence", "pres", "gap", "§3.9(d2)", "予測 presence を渡す（対 GAP のみ）"),
    ("C02", K_PASS,    "gap_vs_presence", "hmm2", "gap", "§3.9(d2)", "デノイズ presence を渡す（対 GAP のみ）"),
    ("C03", K_GAP,     "gap_vs_presence", "gap+pres", "pres", "§3.9(d2)", "presence に GAP を足す（害の検査）"),
    ("C04", K_GAP,     "gap_vs_presence", "gap+pres", "gap", "§3.9(d2)", "GAP に presence を足す"),
    ("C05", K_ORACLE,  "presence", "gap-free oracle", "raw", "§3.9", "オラクル presence の追加利得"),
    ("C06", K_DENOISE, "presence", "HMM L=2", "raw", "§3.9", "因果デノイズ（遅延 2）"),
    ("C07", K_PRUNE,   "recommended", "B 生 −高エントロピー", "A 生", "§3.11", "生から高エントロピー術具を落とす"),
    ("C08", K_DENOISE, "recommended", "C デノイズ", "A 生", "§3.11", "デノイズのみ"),
    ("C09", K_PRUNE,   "recommended", "D デノイズ −高エントロピー（推奨）", "C デノイズ", "§3.11", "デノイズ済みから落とす"),
    ("C10", K_PRUNE,   "recommended", "D デノイズ −高エントロピー（推奨）", "A 生", "§3.11", "推奨構成（両方）"),
    ("C11", K_SHAPE,   "noise_structure", "burst L=32 p=0.10", "iid p=0.10", "§3.10", "同じ誤り率で形だけ違う（学習・評価とも汚す）"),
    ("C12", K_SHAPE,   "noise_structure", "burst L=32 p=0.05", "iid p=0.05", "§3.10", "同上・誤り率 0.05"),
    ("C13", K_SHAPE,   "noise_testonly", "burst L=32 p=0.10", "iid p=0.10", "§3.10(c)", "評価側だけ汚す"),
    ("C14", K_SHAPE,   "noise_testonly", "burst L=32 p=0.05", "iid p=0.05", "§3.10(c)", "同上・誤り率 0.05"),
    ("C15", K_OTHER,   "signal_form", "B_bin", "A_raw", "§3.14", "binary 化そのものの効果"),
    ("C16", K_OTHER,   "signal_form", "D_oracle", "A_raw", "§3.14", "誤り除去（オラクル化）"),
    ("C17", K_OTHER,   "signal_form", "E_oracle+raw", "A_raw", "§3.14", "オラクルと生の連結"),
    ("C18", K_OTHER,   "capacity_control", "E_oracle+raw", "F_raw+raw", "§3.14", "容量対照つきのオラクル利得"),
    ("C19", K_OTHER,   "capacity_control", "G_raw+rand", "F_raw+raw", "§3.14", "陰性側（乱数を連結）"),
    ("C20", K_OTHER,   "denoise_variants", "hmm2_asym", "hmm2", "§3.15", "非対称 HMM の変種"),
    ("C21", K_OTHER,   "denoise_variants", "max_raw_hmm", "raw", "§3.15", "生と HMM の最大値"),
    ("C22", K_OTHER,   "denoise_variants", "raw+hmm", "raw", "§3.15", "生と HMM の連結"),
    ("C23", K_PRUNE,   "prune_by_entropy", "(False, 3)", "(False, 0)", "§3.11", "順位で上位 3 本を落とす（生）"),
    ("C24", K_PRUNE,   "prune_by_entropy", "(True, 3)", "(True, 0)", "§3.11", "同（デノイズ済み）"),
    ("C25", K_PRUNE,   "prune_ubiquitous", "drop-ubiq", "raw", "§3.11", "手選びで汎用術具を落とす"),
    # --- 時間方向の受容野を与えたとき（§3.16(d)(e)）。契約 §1.1 が挙げた主路の根拠を含む。
    ("C26", K_PRUNE,   "receptive_field_prune", "K=0 pruned|r1", "K=0 pruned|r0", "§3.16(e)", "受容野 K=0 で術具除去"),
    ("C27", K_PRUNE,   "receptive_field_prune", "K=8 pruned|r1", "K=8 pruned|r0", "§3.16(e)", "受容野 K=8 で術具除去"),
    ("C28", K_PRUNE,   "receptive_field_prune", "K=32 pruned|r1", "K=32 pruned|r0", "§3.16(e)", "受容野 K=32 で術具除去"),
    ("C29", K_PRUNE,   "receptive_field_prune", "K=128 pruned|r1", "K=128 pruned|r0", "§3.16(e)", "受容野 K=128 で術具除去"),
    ("C30", K_DENOISE, "receptive_field_denoise", "K=0（文脈なし）|r|True", "K=0（文脈なし）|r|False", "§3.16(d)", "受容野 K=0（文脈なし） でデノイズ"),
    ("C31", K_DENOISE, "receptive_field_denoise", "K=8|r|True", "K=8|r|False", "§3.16(d)", "受容野 K=8 でデノイズ"),
    ("C32", K_DENOISE, "receptive_field_denoise", "K=32|r|True", "K=32|r|False", "§3.16(d)", "受容野 K=32 でデノイズ"),
    ("C33", K_DENOISE, "receptive_field_denoise", "K=128（TeCNO 相当）|r|True", "K=128（TeCNO 相当）|r|False", "§3.16(d)", "受容野 K=128（TeCNO 相当） でデノイズ"),
    ("C34", K_SOURCES, "prune_across_sources", "relation_detr_seed42|r1", "relation_detr_seed42|r0", "§3.16(b)", "凍結源 relation_detr_seed42 で術具除去"),
    ("C35", K_SOURCES, "prune_across_sources", "relation_detr_seed123|r1", "relation_detr_seed123|r0", "§3.16(b)", "凍結源 relation_detr_seed123 で術具除去"),
    ("C36", K_SOURCES, "prune_across_sources", "relation_detr_seed456|r1", "relation_detr_seed456|r0", "§3.16(b)", "凍結源 relation_detr_seed456 で術具除去"),
    ("C37", K_SOURCES, "prune_across_sources", "relation_detr_augstrong_seed42|r1", "relation_detr_augstrong_seed42|r0", "§3.16(b)", "凍結源 relation_detr_augstrong_seed42 で術具除去"),
    ("C38", K_SOURCES, "prune_across_sources", "relation_detr_augstrong_seed123|r1", "relation_detr_augstrong_seed123|r0", "§3.16(b)", "凍結源 relation_detr_augstrong_seed123 で術具除去"),
    ("C39", K_SOURCES, "prune_across_sources", "relation_detr_augstrong_seed456|r1", "relation_detr_augstrong_seed456|r0", "§3.16(b)", "凍結源 relation_detr_augstrong_seed456 で術具除去"),
    ("C40", K_SOURCES, "flicker_scaling", "relation_detr_seed42|r1", "relation_detr_seed42|r0", "§3.16(a)", "凍結源 relation_detr_seed42 でデノイズ"),
    ("C41", K_SOURCES, "flicker_scaling", "relation_detr_seed123|r1", "relation_detr_seed123|r0", "§3.16(a)", "凍結源 relation_detr_seed123 でデノイズ"),
    ("C42", K_SOURCES, "flicker_scaling", "relation_detr_seed456|r1", "relation_detr_seed456|r0", "§3.16(a)", "凍結源 relation_detr_seed456 でデノイズ"),
    ("C43", K_SOURCES, "flicker_scaling", "relation_detr_augstrong_seed42|r1", "relation_detr_augstrong_seed42|r0", "§3.16(a)", "凍結源 relation_detr_augstrong_seed42 でデノイズ"),
    ("C44", K_SOURCES, "flicker_scaling", "relation_detr_augstrong_seed123|r1", "relation_detr_augstrong_seed123|r0", "§3.16(a)", "凍結源 relation_detr_augstrong_seed123 でデノイズ"),
    ("C45", K_SOURCES, "flicker_scaling", "relation_detr_augstrong_seed456|r1", "relation_detr_augstrong_seed456|r0", "§3.16(a)", "凍結源 relation_detr_augstrong_seed456 でデノイズ"),
    ("C46", K_OTHER,   "capacity_of_head", "mlp|r1", "mlp|r0", "§3.16(c)", "分類器を MLP にしても術具除去の利得が残るか"),
    ("C47", K_OTHER,   "capacity_of_head_denoise", "linear|r|True", "linear|r|False", "§3.16(c)", "線形の分類器でデノイズ"),
    ("C48", K_OTHER,   "capacity_of_head_denoise", "mlp|r|True", "mlp|r|False", "§3.16(c)", "MLP の分類器でデノイズ"),
]

# 対照（CRITERIA.md 第 1 節で結果を見る前に固定した）
POSITIVE_CONTROL = ("C01", ["phase_edit_score", "phase_seg_f1_50"])
NEGATIVE_CONTROL = ("C05", ["phase_accuracy"])
