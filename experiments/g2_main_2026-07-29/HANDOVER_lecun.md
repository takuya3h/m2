# G-2 本実験 引継書 — efros → lecun

- 作成日: 2026-07-29 / 作成元ホスト: **efros** / 引継先: **lecun**
- 中断理由: efros の GPU を他ユーザーが占有（2 プロセス × 33.5GB / 使用率 90–100%）
- 本書だけで lecun 側の作業が完結するように書いています

---

## 0. 最初に知っておくべき 3 点

### 0.1 ★ 環境: 必ず venv を activate すること（違反すると全結果が無効）

```bash
source .venv-relation-detr/bin/activate      # ★ 必須
```

- **`.venv-relation-detr/bin/python` の直接呼び出しは禁止**
- 理由: `models/bricks/ms_deform_attn.py` は import 時に MSDeformAttn の CUDA 拡張を JIT ロードする。
  これには `ninja`（`.venv-relation-detr/bin` にのみ存在）が **PATH 上にある**必要がある。
  activate しないと `RuntimeError: Ninja is required to load C++ extensions` で失敗し、
  **警告だけ出して別実装にフォールバックし、全デコーダ層の数値が変わる**
- 成功時は `Loading extension module MultiScaleDeformableAttention...` が出る。
  `Failed to load MultiScaleDeformableAttention` が出たら**中断すること**
- 実装済みガード: `build_roi_channels.py` は冒頭でこれを検証し、失敗時は `AssertionError` で即停止する

> 2026-07-29 に efros でこの手順ミスにより **3 タスク分の誤った結論**を出した実績がある
> （「特徴が再現不能」「argmax 不安定」「checkpoint 不一致」— いずれも activate したら解消）。

### 0.2 ★ 未 push のコミットが 18 件ある

lecun で `git pull` する前に、efros 側から **push が必要**です。
**push は未実施**（外部公開にあたるため承認待ち）。

| コミット | 内容 |
|---|---|
| `45e899b` | **feat(g2): ROI channel builder と G-2 training script** ← 本実験の実装 |
| `2dc430b` | **prereg: G-2 事前登録**（学習前コミット・重要） |
| `7e07ad4` ほか 16 件 | 直近の監査タスク群（N1–N3, T1–T3, D1–D3） |

> ⚠️ `git remote -v` の fetch URL に **GitHub の PAT が平文で埋まっています**。
> 本書には転記していません。push 時は取り扱いに注意してください。

**push しない場合の代替**: 下記 2 ファイル＋事前登録を直接転送すれば動きます。
```
scripts/features/build_roi_channels.py
scripts/train_g2.py
experiments/g2_main_2026-07-29/prereg/g2_prediction.md
```

### 0.3 ★ 事前登録は学習より前にコミット済み（`2dc430b`）

指示書 §0.2 の「事前登録を commit する前に学習を 1 本も回さない」は**満たしています**。
lecun でも**予測を書き換えないこと**。git 履歴で「結果を見る前に書いた」ことが証明できる状態を保ちます。

---

## 1. 進捗状況

| Task | 状態 | 備考 |
|---|---|---|
| **P** 事前登録 | ✅ **完了・コミット済み**（`2dc430b`） | 書き換え禁止 |
| **F** ROI 3チャネル構築 | ⚠️ **val / test 完了、train 未完** | efros で中断。**lecun で全 split 作り直しを推奨**（§3.1） |
| **E** 12 run 学習 | ❌ **未実行** | スモークが OOM kill（他ユーザーとの競合）。lecun で実施 |
| **A** 解析 | ❌ 未実行 | `scripts/analysis/g2_report.py` は**未作成**（§4） |
| **S** ログ調査 | ✅ **完了** | 結果は §5 |

---

## 2. lecun で必要な前提の確認（最初に実行）

```bash
cd <repo>
source .venv-relation-detr/bin/activate

# (a) 環境
python -c "import torch;print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
which ninja        # .venv-relation-detr/bin/ninja が出ること
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv

# (b) 入力データ（efros 実測のサイズ）
du -sh data/processed/t1a_regiontoken/relation_detr_seed42     # 227M
du -sh data/processed/phase_manifest                            # 1.7M
du -sh data/annotations/egosurgery_tool                         # 22M
du -sh data/raw/ego                                             # 1.2G
du -sh data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer   # 82M
ls -l third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth   # 187M

# (c) checkpoint の同一性（efros と一致すること）
md5sum third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
#   期待値: 6a898a768eed39391b2afd784ebe254f
```

**(c) が一致しない場合は中断してください。** 凍結源が違うと比較が成立しません。

---

## 3. Task F: ROI チャネルの構築（GPU・所要 1〜2 時間）

### 3.1 efros の中間成果物は使わず、lecun で作り直すことを推奨

efros で val / test は完成していますが（`experiments/g2_main_2026-07-29/features/`）、**転送せず lecun で作り直してください**。

理由: 2026-07-29 に「別ホストで抽出した特徴が再現しない」問題を実際に踏んでいます
（原因は §0.1 の拡張フォールバック）。抽出から学習まで **lecun に統一**するのが安全です。
efros 側の成果物は保険として残してありますが、**混ぜて使わないでください**。

### 3.2 実行

```bash
source .venv-relation-detr/bin/activate
export OUT=experiments/g2_main_$(date +%Y-%m-%d)      # 日付が変わる場合は新しい OUT を使う
mkdir -p $OUT/{prereg,features,runs,csv,json}
git rev-parse HEAD > $OUT/commit.txt                   # 12 run すべてこの commit で回す
cp experiments/g2_main_2026-07-29/prereg/g2_prediction.md $OUT/prereg/   # 事前登録を引き継ぐ

python scripts/features/build_roi_channels.py --self-test    # 5 項目すべて OK を確認
for sp in val test train; do
  python scripts/features/build_roi_channels.py --split $sp --out $OUT
done
```

### 3.3 実装の要点（レビュー用）

| 項目 | 内容 |
|---|---|
| 特徴マップ | 検出器 **neck level0**（stride 8）。**D = 256**（実測）。出力は 15 クラス × 256 = **3840 次元** |
| box | **canonical VBS の GT box（15 クラス）**。検出器の予測 box は使わない |
| mask | `tool_seg_noskewer` を GT box に **IoU ≥ 0.5** で幾何マッチ |
| bboxROI | box 内の全画素平均 |
| maskROI | box 内かつ mask==1 の画素平均。**mask 無しは bbox にフォールバック**（= bboxROI と同一値） |
| randROI | box 内で mask と**同面積・同重心の連結ブロブ**。形状 seed は `RAND_SEED=20260729` 固定（3 seed で同一形状） |
| 座標変換 | `model.eval_transform` の出力形状を**実測**して使う。`min_size/max_size` からの再計算は丸めが 1px ずれるため禁止。padding は右下なので原点不変 |
| 未検出クラス | ゼロベクトルで埋め、ゼロ率を記録 |

### 3.4 efros で得られた実測値（lecun の結果と比較する基準）

| split | frames | boxes | fallback | fallback率 | zero_slot率 |
|---|---:|---:|---:|---:|---:|
| val | 1,515 | 4,707 | 1,134 | **0.2409** | 0.8080 |
| test | 4,265 | 12,673 | 1,484 | **0.1171** | 0.8357 |
| train | — | — | — | 未測定 | 未測定 |

**サニティチェックはすべて PASS**（`mask==bbox の box 数` = フォールバック数、`rand` の面積不一致 0 件）。

> ⚠️ **指示書 §1.1 の想定（約 12.7%）と val が食い違います。**
> 内訳: val のフォールバック 24.09% のうち **23.07% が Mouth Gag + Skewer**（マスクが原理的に無いクラス）、
> その他クラス由来はわずか 1.02%。test は 11.71%（うち 9.60% が Mouth Gag+Skewer）。
> つまり **フォールバック率は split 依存**で、val は Mouth Gag/Skewer の出現が多いだけです。
> 実装の欠陥ではありませんが、**val では約 1/4 の box で maskROI = bboxROI になる**ため、
> val 上の「mask vs bbox」のコントラストが弱まります。解釈時に必ず考慮してください。

---

## 4. Task E: 12 run 学習（GPU）

### 4.1 実行

```bash
source .venv-relation-detr/bin/activate
export OUT=<Task F で使ったのと同じ OUT>

# スモーク（1 本だけ・2 epoch）で疎通確認してから本番へ
python scripts/train_g2.py --system base --seed 42 --out $OUT --epochs 2 --smoke

# 本番 12 run（逐次実行を推奨。GPU 競合があれば 1 GPU に固定）
for sys in base bboxROI maskROI randROI; do
  for seed in 42 123 456; do
    CUDA_VISIBLE_DEVICES=0 python scripts/train_g2.py --system $sys --seed $seed --out $OUT
  done
done
```

### 4.2 系統と入力次元

| 系統 | 入力 | in_dim |
|---|---|---:|
| `base` | region-token のみ | 3,840 |
| `bboxROI` | region-token ⊕ bboxROI | 7,680 |
| `maskROI` | region-token ⊕ maskROI | 7,680 |
| `randROI` | region-token ⊕ randROI | 7,680 |

学習設定は `train_t1a.py` と同一に揃えてあります（TeCNO 2 stage / 8 layer / 64 f_maps、
lr 5e-4、weight_decay 0.01、epochs 50、smoothing 0.15、best epoch は val accuracy で選択）。

### 4.3 各 run が残すもの（`$OUT/runs/<system>_seed<N>/`）

| ファイル | 内容 |
|---|---|
| `metrics.json` | val/test の全指標、best_epoch、in_dim、ROI フォールバック率、学習秒数 |
| `env.json` | torch / CUDA / GPU 名 / cudnn / host / **commit** / ninja パス / **拡張ロード成否** |
| `predictions/val_preds.json` | **per-frame 予測**（`basename` / `clip_id` / `gt` / `pred`） |
| `predictions/test_preds.json` | 同上 |

> per-frame 予測の保存は**本実験の必須要件**です。既存の phase trainer は `argmax` 直後に予測を破棄しており、
> 過去の run は per-phase の内訳もブートストラップも一切できません。ここで初めて残します。

### 4.4 完走後に必ず確認すること

```bash
# 12 run すべてが同一 commit・同一ホスト・拡張ロード成功であること
for d in $OUT/runs/*/; do
  python -c "
import json,sys
e=json.load(open('$d/env.json'))
print('$d', e['commit'][:8], e['host'], 'ext=', e['msdeformattn_extension_loaded'])
"
done
```

**拡張ロードが False の run があれば無効として除外し、レポートに明記してください。**

---

## 5. Task S の結果（完了済み・本実験の判定には影響しない）

`experiments/**/*.log` を `Failed to load MultiScaleDeformableAttention` / `Ninja is required` で走査（252 ファイル）:

- **ヒット 12 件 / 6 run ディレクトリ**: `transfer/oracle_phase_seed{42,123,456}`、`transfer/hc_seed{42,123,456}`
- **`aligndetr_*` タグの該当は 0 件**
- 出力: `experiments/g2_main_2026-07-29/csv/s_extension_fallback_runs.csv`

これらの過去 run は拡張フォールバック下で実行された可能性があります。**解釈は別途**。

---

## 6. Task A: 解析（未着手・`scripts/analysis/g2_report.py` を新規作成する）

### 6.1 出すもの

| 差分 | 意味 |
|---|---|
| 2 − 1（bboxROI − base） | チャネル追加そのものの効果 |
| **3 − 2（maskROI − bboxROI）** | **背景除去の純効果 = 本実験の答え** |
| 4 − 2（randROI − bboxROI） | 形 vs 画素数の分離 |

overall（accuracy / macro-F1）と **per-phase F1（9 工程）**の両方。**主指標は per-phase F1**。

### 6.2 誤差推定（★ 過去の sd・MDE を使わないこと）

事前登録で固定した判定閾値:

1. **2 標本の標準誤差** `SE = sqrt(sd_A²/n_A + sd_B²/n_B)`（n=3）で `|差| > t(0.975, df) × SE`（Welch の df）
   - `sqrt(2/n)` 型の等サイズ前提の式は使わない
2. **動画単位クラスタ・ブートストラップ（B=2,000）**の 95%CI が 0 を跨がない
   - `predictions/{val,test}_preds.json` の per-frame 予測を使う
   - test は **3 動画しかない**ため CI が広くなる。幅をそのまま報告する
3. **両方を満たしたときのみ「超えた」と判定**。片方だけなら「不一致」として結論を保留

### 6.3 その他

- **A-3**: フォールバック率と効果の関係（動画別・クラス別の散布図と相関）
- **A-4**: 事前登録の予測 1〜4 と **1 対 1 で照合**し、当たり外れを明示
- **A-5**: **系統 1（base）の 3 seed の sd を明記**。これが本実験における「真の再現ばらつき」の推定値であり、
  今後すべての実験の基準になる

---

## 7. 引き継ぎ時点の未解決事項

| # | 内容 |
|---|---|
| 1 | **push 未実施**（18 コミット）。lecun が `git pull` する前に承認・push が必要（§0.2） |
| 2 | Task F の train split が未完（lecun で全 split 作り直しを推奨） |
| 3 | `scripts/analysis/g2_report.py` が未作成 |
| 4 | val のフォールバック率が想定の約 2 倍（§3.4）。解釈時に考慮が必要 |
| 5 | efros 側 `experiments/g2_main_2026-07-29/` の中間成果物は**未コミット**（features/ は npz で大きい） |

---

## 8. 絶対に守ること（再掲）

- `source .venv-relation-detr/bin/activate` してから実行する（§0.1）
- **事前登録を書き換えない**
- 12 run を**同一 commit・同一ホスト**で回す。途中でコード変更しない
- 元データ・split・クラス体系・凍結源・既存の region-token 抽出コードを変更しない
- 既存キャッシュを上書きしない
- 推測値を書かない。測れなければ `UNKNOWN`
- 統計量には必ず **n と分母の定義**を併記する
