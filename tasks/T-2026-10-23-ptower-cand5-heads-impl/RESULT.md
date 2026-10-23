# T-2026-10-23-ptower-cand5-heads-impl 結果

## 判定

status: pass。G1・G2 は pass。候補 5 の時間ヘッド四案を `scripts/stage1_ptower.py` の時間ヘッドの道に足した。候補名は `ssm`、`memory`、
`progress`、`stabilize`。既存の四候補（linear、A、B、C）の出力は、変更の前に取った要約値とビット一致する。学習の道も一致した
（phase0 の版と比べ、合成データで 3 epoch 学んだ後の重みがビット一致）。実験は回しておらず、実データの特徴は読んでいない。
checkpoint は残していない。原典（OnlineTAS、StableSPR）は外部への接続を控えたため照合しておらず、記憶・TEC・EGTP の形は SPEC とカードの記述の範囲で決めた。

## 完了判定

| # | 実測 |
|---|---|
| a | 分岐 feat/ptower-cand5-heads-impl、起点 origin/phase0 = ea73a8ba、汚れは契約 2 件だけ、A6000 × 2（compute プロセス 0）。版は torch 2.1.2+cu118、mamba-ssm 2.2.2、causal-conv1d 1.4.0。試験の前は 6 failed / 924 passed（[audit.md](audit.md) L5〜L55）。基準値は HEAD ea73a8ba（scripts 未変更）で取り、二つのプロセスで同じ値だった。試験だけを置いた commit は ed0fee7a（L56〜L70） |
| b | 四候補の要約値が基準値と一致した（試験 4 件）。設定ファイルには注記を足しただけで、新しい鍵は無い（試験 1 件）。対照として A の `layers` を 7 にすると一致しない。学習の道も 4 候補で重みと epoch の記録がビット一致した（L108〜L151） |
| c | 17,233 の manifest で、23 クリップ、Δ が 1 の組 16,663 / 17,210 = 96.8%、最大 254 が再現した。不明は 23 箇所（動画の先頭 15、クリップ間 8）で、値は −1（既知の Δ は 1〜254）。陰性対照として、動画 03 の境を一つ無視した写しではクリップ間の不明が 7 になった（L72〜L87） |
| d | 四候補名で `build_model` が模型を返し、段ごとの 1 × 9 × T の列を返した。ssm は GPU で試した。対照として、存在しない候補名・`base_candidate`・`gap_input` で ValueError が出た |
| e | 四ヘッドで、t 以降の入力を変えても t より前の出力が厳密に一致した。stabilize は A・B・C の三つ、memory は `memory_len` 0 も試した。SSM の許容差は 0 で、GPU の実測の差 0.0 に合わせた。陽性対照の双方向 GRU は同じ検査で落ちた |
| f | `reset_at_clip` が真のとき、境の前を変えても境の後の出力は不変だった。偽のときは変わった。`gap_input` は `flag`（1 列）と `delta`（log Δ と不明の目印の 2 列）を切り替えられる |
| g | 進捗の教師は区間ごとに 0 から 1 へ単調で、クリップの境をまたぐ同じ工程は一つの区間になった。遷移行列は val を変えても不変で、train を変えると変わった。TEC は α が 0 のとき重み付き CE と一致し（相対差 1e-6 以内）、α を正にすると一致しない。重みは誤り区間の先頭 m フレームだけに付く。EGTP は確率を変えず、閾値まで状態を保つ。閾値を 0 にすると毎フレームの argmax になった。境での初期化も試した |
| h | 煙試験は 5 本（A、memory、progress、stabilize が CPU、ssm が GPU）。どれも 2 epoch 完走し、checkpoint を一時の置き場に書いた。置き場を消した後、`*.pth` は 0 件（L130〜L134） |
| i | 変更は scripts・configs・tests・README と、契約のディレクトリ・受け皿だけ（L164）。依存の差分なし。forbidden-check は pass。試験の後は 6 failed / 959 passed で、失敗の集合は前と同じ。陽性対照として、clone の写しの data/ に一件足すと fail・exit 1 になった（L153〜L162） |
| j | PR は audit「commit と送出」に記録する |

解決された参照（手順書 3）: `inject_verbatim` の 3 節（prohibitions、issuer_cautions、folds）の原文は audit.md の末尾に写した。conventions の blob ceb7ef0f は契約の conventions_rev と一致する。

## 実測

**設定の鍵**（既存の鍵の意味と既定値は変えていない。足した鍵は設定ファイルに書かず、無いときは次の既定で既存の挙動になる）

| 鍵 | 既定 | 実装 |
|---|---|---|
| `candidate` | — | `ssm` / `memory` / `progress` / `stabilize` を追加 |
| `boundary_flag` | false | どの候補でも、クリップの先頭の目印を 1 列連結する |
| `reset_at_clip` | false | クリップごとに模型全体を走らせる（どの候補でも使える） |
| `gap_input` | none | `flag` は不明の目印 1 列。`delta` は log Δ（不明は log 256）と不明の目印の 2 列 |
| `ssm_state_dim` / `ssm_layers` / `ssm_selective` | 64 / 2 / true | Mamba（d_conv 4、expand 2）、pre-norm の残差、dropout 0.5。selective が偽なら dt_proj の重みを 0 にして凍結する |
| `memory_len` | 128 | 現在を含む直近の GRU 状態を、因果の注意で読み、ゲートで混ぜる。0 なら GRU だけ |
| `progress_weight` / `transition_prior` | 0 / false | 進捗は工程ごとの sigmoid で、正解の工程の列に MSE をかける。遷移行列は自己遷移を含み、直前の予測から届かない工程を除外する |
| `base_candidate` | A | stabilize の模型（A / B / C。C なら平滑化の損失も付く） |
| `tec_alpha` / `tec_m` / `tec_sigma` | 0 / 8 / 1.5 | 各段の argmax の誤り区間ごとに重みをかける。正規化はクラス重みの和で行う |
| `egtp` / `egtp_k` / `egtp_reset_at_clip` | false / 必須 / false | val の `egtp/*` に ŷ_t の指標を足す。主の値と選び方は p_t の argmax のまま |

**パラメータ数（maps 64、layers 6）**
- 既存: linear 18,441、A と C 331,090、B 382,299
- ssm 234,121。selective が偽のときは学習される数が 232,841
- memory 378,011
- progress 331,675（`delta` を入れると 331,803）
- stabilize は base の候補と同じ数

**因果性の許容差**: CPU も GPU も 0（`torch.equal`）。GPU の SSM の実測の差は、長さ 60 と 700、selective の真と偽のどれでも 0.0 だった。

**煙試験の所要時間（合成データ、2 epoch）**: memory 0.34 s、ssm 0.26 s（GPU）、stabilize・A・progress は各 0.18 s。

**原典での確かめ**: 確かめられた形は無い。次の 3 点は UNKNOWN で、照合していない。
- OnlineTAS の記憶（§3.3）
- StableSPR の TEC（§2.1）と EGTP（式 (6)）
- ProTAS の進捗の頭

## 起票者の誤り

- `self_contradiction`: SPEC §4.3 は P-B の初期化を「クリップの先頭で GRU の状態と記憶を初期化する」と書く。一方、完了判定 f は「境の後の出力が境の前のフレームに依らない」を求める。
  - GRU と記憶だけを初期化しても、下の TCN（受容野 253 フレーム）が境をまたぐ。§4.3 のとおりに作ると f は落ちる。
  - 模型全体をクリップごとに走らせて f を満たした。
- `asserted_without_measuring`: Task D-7 は、煙試験を「`train` の道で 2 epoch 学び、checkpoint は一時の置き場に書く」とする。
  - 実際の `train` は `evidence()` を通る。この関数は `experiments/` に実験フォルダを作り（禁止領域）、W&B が始まらなければ RuntimeError を出す。指示どおりに呼ぶと、禁止領域に書くか、失敗する。
  - 試験の中で `evidence` と `load_fold` を差し替えた。
- `self_contradiction`: 設計の出所であるカードの中に、三版の改訂と古い記述の食い違いが三つ残る。どの値を使うかは exp の起票で決める必要がある。
  - P-C: #14 の改訂は MSE、固定の行と #15 は L1。SPEC は MSE を採った。
  - P-D: #14 の改訂は α {7, 19}、掃引の行と #15 は {3, 11}。
  - P-B: #9 の改訂は GRU 単独の腕を足すが、備考は入れないと書く。
- `self_contradiction`: §4.1 は、クリップの先頭とクリップをまたぐ位置を不明とする。数えると 23 箇所になる。一方、完了判定 c は「クリップ間 8 箇所が不明」とし、対照を「不明の数が 7」とする。両方を数えて書いた（全体 23、クリップ間 8 → 7）。

## 逸脱

- judgement: `reset_at_clip` はクリップごとに模型全体を走らせる形にした（上の誤りの 1 件目）。どの候補でも使える（P-B のカードは腕 1 の学び直しにも同じ区切りを求める）
- judgement: `gap_input: flag` は不明の目印（＝クリップの先頭）1 列とした（カードの「境の二値フラグ」）。`delta` で不明の Δ に入れる値は 256（観測の最大 254 の上）
- judgement: 記憶は B の形に倣い、TCN の最終段の出力を埋め込んで GRU に入れた。読み出しは直近 `memory_len` 状態への因果の注意とゲート。`memory_len` 0 の GRU だけの腕を足した（カード P-B #9 の三版）
- judgement: 進捗の頭は stage 1 の内部の特徴から工程ごとに出し、正解の工程の列に MSE をかけた。区間が 1 フレームのときの教師は 0
- judgement: TEC の誤り区間は各段の argmax から取り、正規化はクラス重みの和にした。α が 0 のとき `train` は既存の CE の道を通る。EGTP の証拠の積み方（max(0, e + p_c − p_state)）は実装者の設計で、`egtp_k` には既定値を置かず、`egtp` が真のとき必須とした（原典の既定が UNKNOWN のため）
- judgement: SPEC に既定の無い鍵は、カードの殺し実験の中央の点に合わせた（state 64、2 層、記憶 128）。`base_candidate` の既定は A
- judgement: 原典（arXiv 2411.01122、2605.16387）は、外部への接続を事前の確認なしに行わない規約のため引いていない
- judgement: 煙試験に既存の A を足し、phase0 の版との学習の一致を scratchpad で確かめた（SPEC に無い追加の確認）
- judgement: CLAUDE.md の experiment_log と W&B は適用していない（実験を回していない。Task E-2）。README には節を足した

## 想定外・UNKNOWN

- 想定外: 実装の誤り 1 件（train のクラス数の集計が 3 要素で取り出していた）を、煙試験が最初の回で捕まえた
- UNKNOWN: 原典の形との一致、実データでの所要時間、SSM の逆伝播の決定性（前の契約で非決定 5.7e-14 と測られている）

## 送出

PR と task-report の終了コードは audit.md の「commit と送出」に記録する。
