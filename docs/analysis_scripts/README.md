# docs/analysis_scripts — GPU 不要の分析スクリプト（2026-08-22）

`docs/research_review_and_next_plan_2026-08-22.md` の §3 の表を再生成する。
**すべて読み取り専用**で、`experiments/` にも `data/` にも書き込まない。

## 依存

`numpy` と `scikit-learn` のみ。プロジェクトの `.venv` があればそれで動く。
壊れている場合は一時環境で足りる:

```bash
uv venv /tmp/an --python 3.12
uv pip install --python /tmp/an/bin/python numpy scikit-learn
/tmp/an/bin/python docs/analysis_scripts/<script>.py
```

`proxy_*` は `src/egosurgery/metrics/phase.py` の `PhaseEvaluator` を import するため、
**リポジトリのルートで実行する**こと。

## 前提となるキャッシュ

| 用途 | パス |
|---|---|
| 予測 tool-presence（15-d sigmoid） | `data/processed/b2a_detsignal/relation_detr_seed42/{train,val,test}_toolpresence.npz` |
| GT tool-presence（15-d 0/1） | `data/processed/oracle_toolpresence/{train,val,test}_oracletool.npz` |
| GAP 特徴（2048-d） | `data/processed/stage1_features/relation_detr_seed42/{split}_gap.npz` |
| region-token（3840-d） | `data/processed/t1a_regiontoken/relation_detr_seed42/{split}_regiontoken.npz` |
| 工程 manifest | `data/processed/phase_manifest/{split}.json` + `phase_vocab.json` |

## スクリプト

| ファイル | 何を測るか | 目安時間 |
|---|---|---|
| `hmm_presence_filter.py` | 因果 HMM forward filter による presence デノイズの品質（§3.5） | 数秒 |
| `hmm_presence_fixed_lag.py` | 固定ラグ平滑化の品質/遅延曲線（§3.6） | 約 1 分 |
| `signal_video_identity_probe.py` | 各信号が動画 ID をどれだけ符号化しているか（§3.18） | 約 2 分 |
| `proxy_phase_presence_denoise.py` | GPU 不要のプロキシ工程認識器（陰性対照つき・§3.7） | 約 1 分 |
| `proxy_lovo_presence.py` | 15 動画 leave-one-video-out：生 / オラクル / デノイズ（§3.9） | 約 3 分 |
| `proxy_lovo_gap_vs_presence.py` | 同 LOVO：GAP / presence / GAP⊕presence / デノイズ（§3.9(d2)） | **約 70 分** |
| `proxy_noise_structure.py` | 同じ誤り率で iid ノイズ vs burst ノイズ（§3.10） | 約 10 分 |
| `proxy_lovo_noise_structure.py` | LOVO：iid ノイズ vs burst ノイズ（§3.10 後半・主たる根拠）。引数でノイズ seed 数（既定 1・報告値は 3） | 約 15 分（seed 3 本） |
| **`proxy_lovo_recommended.py`** | LOVO：**しきい値 `H > 0.45` で術具を落とす × 因果デノイズ の 4 腕**（§3.11・**正式な結果**） | 約 5 分 |
| `proxy_lovo_prune_by_entropy.py` | LOVO：順位ベースで上位 k 本を落とす掃引（§3.11・感度分析） | 約 5 分 |
| `proxy_lovo_prune_ubiquitous.py` | 同（手選びの初期版・参考） | 約 5 分 |
| `proxy_lovo_signal_form.py` | LOVO：「誤り除去」と「binary 化」の分離（§3.14） | 約 5 分 |
| `proxy_lovo_denoise_variants.py` | LOVO：デノイズの変種（非対称 HMM / max / 連結）と短工程 F1（§3.15） | 約 5 分 |
| `proxy_lovo_capacity_control.py` | LOVO：GT⊕生 の利得に対する容量対照（§3.14） | 約 5 分 |
| **`proxy_lovo_receptive_field_denoise.py`** | LOVO：**時間方向の受容野を与えるとデノイズ利得が消える**ことを示す（§3.16(d)・**最重要**） | 約 20 分 |
| **`proxy_lovo_receptive_field_prune.py`** | LOVO：**同じ受容野でも術具除去の利得は残る**ことを示す（§3.16(e)・**最重要**） | 約 25 分 |
| `proxy_lovo_capacity_of_head_denoise.py` | LOVO：分類器を線形 → MLP に替えてもデノイズの分節利得が残るか（§3.16(c)） | 約 5 分 |
| `proxy_lovo_capacity_of_head.py` | LOVO：per-frame 分類器を線形 → MLP に替えても術具除去の利得が残るか（§3.11） | 約 5 分 |
| `proxy_threshold_sweep.py` | 標準 split でエントロピーしきい値を掃引する感度分析（§3.11 の「参考」） | 約 3 分 |
| `proxy_lovo_noise_testonly.py` | LOVO：学習はクリーンのまま評価側だけを汚す（§3.10(c)。選択性が 7 倍に鋭くなる） | 約 5 分 |
| `proxy_lovo_prune_across_sources.py` | LOVO：6 つの凍結源で「高エントロピー術具の除去」の利得を測る（§3.16(b)） | 約 25 分 |
| `proxy_lovo_flicker_scaling.py` | LOVO：6 つの凍結源でデノイズ利得を測り、ちらつき倍率との関係を見る（§3.16(a)） | 約 25 分 |
| `per_video_difficulty.py` | 動画ごとの難しさの分解（多数決ベースライン・動画長・工程分布）。引数に `proxy_lovo_gap_vs_presence.py` のログ（§3.13） | 数十秒 |
| `signature_stability_correlation.py` | 動画ごとの `P(tool\|phase)` のずれ 4 指標が per-video 性能を説明するか（§3.12・ほぼ負の結果）。引数に `proxy_lovo_gap_vs_presence.py` のログを渡す | 数十秒 |

## 再現性の確認（2026-08-22）

本ディレクトリのスクリプトは、**報告書の表を出したときに実際に走らせたものと同一**である
（一時ディレクトリの実行版とバイト単位で一致することを確認済み）。
`python -m py_compile docs/analysis_scripts/*.py` は全本通る。

## 注意

- プロキシ（`proxy_*`）は **多項ロジスティック回帰 + 因果 phase HMM** であって **TeCNO ではない**。
  val では本番の acc / macro-F1 をよく再現するが、**edit は本番より 10 ほど低く出る**。
  **信号間の相対比較には使えるが、本番の絶対値の代用にはならない。**
- HMM の遷移・emission は **train の GT からのみ**推定する。val/test には適用のみ。
- 因果性（未来フレーム不使用）は `fixed_lag` の `L>0` を除いて厳守している。
  `L>0` は「L フレームの遅延を許す」という意味であり、オフラインではない。
