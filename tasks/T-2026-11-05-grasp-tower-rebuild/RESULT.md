# RESULT — T-2026-11-05-grasp-tower-rebuild（非公式の測定。関門と設計の判断に使わない）

ホスト bengio、分岐 `feat/grasp-tower-rebuild`（andrew 版の中止の記録 2d87d79f の上に積んだ。起点 origin/phase0 89fe4a41）。時刻は JST。
命令と出力は `audit.md`（`audit.md:L`）、全値は `experiments/analysis/grasp_tower_rebuild/REPORT.md`、batch の計測は同じ場所の `batch_probe.md`。
andrew 版（status stopped、利用者の指示で Task C の途中に中止）の RESULT は commit 2d87d79f に残る。本書は bengio でやり直した結果である。

解決された参照（手順書 3）: `inject_verbatim` の 6 節（prohibitions・issuer_cautions・env_p0・folds・split・crossfit）の原文は audit.md の「解決された参照」に写した。
conventions の blob ceb7ef0f は契約の conventions_rev 2d946b07 と一致する。denominator・frozen_source・sigma_policy の参照は無い。

## 1. 判定

- status: **pass**。G の 3 本が収束規則で止まり、信号と標的と目録を作り、検査と対照をすべて行った
- G1 pass（audit.md:27-97）: 起点に二本目・三本目の内容、本契約以外の compute 0 件、空き 1,389,087,522,816 B、失敗 11 件、要約値、電力の上限 220 W × 2
- G2 pass（audit.md:105-139）: 5 クラスの注釈から元のマスクが 16/16 で戻る、反転の経路は 24/24 で 1↔2・3↔4 を入れ替え、入れ替えない写しと二本目の経路は 0/24
- G2b pass（audit.md:169-190、`batch_probe.md`）: 18 水準の表、読み込んだ枚数が batch と一致、利用者の回答（batch 8・bf16（変形注意だけ fp32）・学習率 1e-4）を記録
- G3 pass（audit.md:207-235）: 3 本が収束規則で止まり、選んだ epoch の値が学習前（0.0060）を上回り、反転の整合は入れ替えて 0.693・入れ替えない対照 0.118

## 2. 完了判定（SPEC §8）

| # | 実測 | 空振りでないことの確認（実測） |
|---|---|---|
| a | audit A-1〜A-7。分岐・起点・内容・未追跡 0 件（空の 3 フォルダ）・compute 0 件・空き・失敗 11 件・要約値・220 W（RTX A6000 × 2） | 列挙は zsh を 9 件拾い、存在しない実行ファイルの経路で 0 件 |
| b | 把持関係の注釈だけ。train 9,356 フレーム・32,408 インスタンス、val 1,514・5,653。戻したマスク 16/16 一致。印のフレームは注釈に 0 件（工程の経路の注釈の無いフレームの集合 = 印の集合） | 手 4 クラスを 1 件混ぜた写しで対応表の外れ 1 件。印のフレームを 1 件足した写しで学習が始まらずに止まった |
| c | 本契約の経路は 24/24 で入れ替え。整合の検査は学習後 swap 0.693・noswap 0.118 | 入れ替えない写しと二本目の G38 は取り出しで 0/24。整合の検査の noswap（入れ替えない写し）は 0.118 に下がる |
| d | 3 本の epoch ごとの記録（REPORT §2）、選んだ epoch 3・3・6、止まった epoch 7・7・10、所要 11,664・7,240・10,069 秒、COCO の重み 608 / 610 | 学習前の重みの値 0.0060 は選んだ epoch の 0.6460・0.5939・0.5814 と違う |
| e | g・m・q を作り sha256・フレーム数・値の範囲を目録に記録。val の比べ: g の ROC-AUC 0.740〜0.927、m の IoU 0.283〜0.846 | 確定の G の信号を 5 フレーム混ぜた写しで交差適合の外れ 5 件（本物は 0 件） |
| f | q の行の和が 1 を超えた枠: 交差適合の train 16,021 / 32,272（最大 1.546）、val 2,327 / 4,707（1.219）。正規化の後の誤差の最大 4.5e-8 | 値を一つ変えた写しで和の誤差 0.25、外れ |
| g | g・m: train は元と同じフレーム 0.000・同じ動画 0.115、val 0.001・0.556。q: 元と同じ枠 0.300・0.318 | seed 43 の写しで割合と並べ替えの要約値が変わった（train 0.0001・0.118） |
| h | G の学習 3 本と推論 4 つの動画の集合と {04, 05, 07} の共通 0 件 | 04 を混ぜた入力で共通 1 件 |
| i | 試験 11 → 11 failed（名前の集合が一致）、仮想環境の要約値一致、forbidden-check の本契約の経路の違反 0 件（下の注） | 道具は本契約の新しいファイル（run の記録 27 件）を変更として拾っている |
| j | PR #295（OPEN、base phase0、Draft でない）。同じ分岐の PR #289 は途中（ff954d9f まで）で利用者が統合済み | head は両方 `feat/grasp-tower-rebuild` |
| k | 12 水準＋bf16 の 6 水準の表（`batch_probe.md`）、枚数の一致、一本目との並べ、利用者の回答 | batch を変えると枚数が変わる（120・240・360・480・720）。重みを読まない写しで記憶は**変わらなかった**（起票者の誤り 3） |

- i の注: 違反 51 件のうち 24 件は同期で届いた別の契約のファイル（触れていない）、27 件は本契約の run の記録（`experiments/phase1/grasptower_G_*_seed42/`）。
  契約の `allow_write` に run の置き場が無い（起票者の誤り 1）。利用者の決定で `allow_write` に `experiments/phase1/grasptower` を足し（`meta.amendments`）、run の記録を commit した。
  足した後の作業ツリーの検査は違反 24 件（すべて別の契約のファイル）・本契約の経路の違反 0 件

## 3. 実測

- 注釈: 左手 8,704 / 1,505、右手 8,447 / 1,467、左手の器具 7,129 / 1,231、右手の器具 7,176 / 1,274、両手の器具 952 / 176（train / val のインスタンス）
- batch の計測（GPU 1 枚、60 ステップ）: fp32 は batch 2〜8 が収まり 12 以上で溢れた。fp16 は batch 4 以上で損失が非数（60 ステップ中 9〜58）。
  bf16（変形注意だけ fp32）は batch 2〜12 が収まり非数 0、batch 8 で 1 ステップ 1.230 秒・1 epoch 24.0 分（fp32 は 1.824 秒・35.5 分）
- G（val の 5 クラス mask mAP、印を除く / 含める）: 確定 epoch 3 で 0.6460 / 0.6459、H1 epoch 3 で 0.5939 / 0.5937、H2 epoch 6 で 0.5814 / 0.5813。学習前 0.0060
- クラス別 AP（確定）: 左手 0.7116、右手 0.8245、左手の器具 0.5306、右手の器具 0.6338、両手の器具 0.5296。右 − 左は手 +0.113・器具 +0.103（原因は UNKNOWN）
- 反転の整合（val 40 フレーム、soft IoU、swap / noswap）: 本契約 0.693 / 0.118、二本目の G 0.134 / 0.787、学習前 0.439 / 0.633
- 正解との比べ（val、確定の G）: ROC-AUC 左手 0.740・左把持 0.898・右手 0.861・右把持 0.860・両手 0.927。IoU 左器具 0.512・右器具 0.386・両手器具 0.283・左手 0.826・右手 0.846
- 交差適合の train（H1→H2 / H2→H1）: IoU 両手器具 0.067 / 0.074、手 0.717〜0.783。交差適合なし（学んだ動画）は ROC-AUC 0.884〜0.945
- 目録 `experiments/analysis/grasp_tower_rebuild/signals_manifest.json`（sha256 1717ae6963ef692faac5015ad9c14ba91162d7e9ad17db4447c874ecad26f090）。実体は `$S/signals/`
- 重み: 確定 5ea2cbf4…、H1 5cfa055c…、H2 efdefccd…（`$S/g/ckpt/{all,H1,H2}/best.pth`）
- 電力の上限: GPU 0・1 とも 220.00 W（既定・最大 300 W）、NVIDIA RTX A6000
- §6.3 の予測: 1 当たり（0.6460 > 0.6278）、2 当たり（0.693 > 0.134）、3 は器具 3 チャネルのうち左手の器具だけ当たり

## 4. 起票者の誤り

1. self_contradiction — SPEC §4 は run の置き場を `experiments/phase1/grasptower_` で始まる名前とするが、`allow_write` に入っていない。
   指示どおりに置くと forbidden-check が本契約の run の記録 27 件を違反とし、完了判定 i（本契約の経路の違反 0 件）と両立しない（二本目・三本目は allow_write に含めていた）
2. self_contradiction — SPEC §0 は二本目・一本目の保存先が bengio に無ければ andrew から「同じ経路で」写すと読めるが、§7-2 は版管理の外の保存先への書き込みを禁じる。
   同じ経路へ写すと二本目・一本目の保存先に書くことになるため、本契約の保存先 `$S/inputs/` へ写し、COCO の重みの経路を直した
3. check_does_not_check — Task B0-2 の対照「重みを読まない写しで記憶が変わる」は、重みの有無がパラメータの数と形を変えないため成り立たない。
   実測で最大確保は 9,895,972,352 B でバイトまで同じだった。違いは 1 ステップ目の損失（119.4 と 61.8）にだけ現れた
4. asserted_without_measuring — §3.1・Task B-4 は欠落の印の付いたフレームが学ぶフレームに入る前提（「印のフレームだけの数歩で損失が 0」）で書くが、
   印のフレームは把持関係の注釈ファイルに 1 件も無い。書かれた検査は実行できず、学ぶフレームから外れることと、足した写しで止まることで示した
5. check_does_not_check — Task A-3 の列挙は `/proc` を読むが、bengio はコンテナの中で、外のプロセスは見えない。学習の途中で GPU 1 を約 21 GB 使う一覧に出ない使用者が現れ、
   開始時の列挙では捕まえられなかった（nvidia-smi の全体の使用とプロセスの一覧の差で気づいた）

## 5. 逸脱

- judgement（利用者の決定）: andrew 版の分岐（中止の記録）の上に積み、PR #289 を使い続けた。実験は bengio で一からやり直した（andrew の途中の出力は使っていない）
- judgement（利用者の指示「読み直し」）: 台帳の改訂版（Task B0 を足した版）を途中で取り込んだ。旧版の条件（batch 2・fp32）で起動した 3 本は epoch 1 の途中で終了し、`$S/aborted/try1/` へ移した
- judgement（利用者の決定）: Task B0 に bf16 を足し、mmcv に bf16 の実装が無い変形注意だけ fp32 で計算した（`meta.amendments`）。batch 8・bf16（変形注意だけ fp32）・学習率 1e-4 で学んだ
- judgement: 写しは `$S/inputs/` に置き、`g5_train.py` の COCO の重みの経路と `g5_signals.py` の目録のホスト名を直した（f149c79d）
- judgement: batch 16・fp16 の 1 回目は cuDNN の初期化の失敗で記録が残らず、計測の道具がこの誤りも記録するよう直して測り直した
- judgement: 学習の打ち切りは学習の繰り返しの中で判定した（§3.2 が許す形。学習率は下げない）
- judgement: conventions#crossfit に従い、交差適合なしの train の比べも行った
- environment（利用者の決定）: 学習の途中で GPU 1 を本契約の外のプロセス（約 21 GB、使用者は不明）と共有した。利用者の決定でそのまま続けた。H1 の所要が延びた
- judgement（利用者の決定）: 契約の `allow_write` に run の置き場 `experiments/phase1/grasptower` を足し（`meta.amendments`）、run の記録を commit した
- environment: 作業ツリーの forbidden-check は、同期で届いた別の契約のファイル 24 件で違反を出す。届いたファイルには触れていない

## 6. 想定外・UNKNOWN

- GPU 1 の共有の相手（約 21 GB、03:2x〜04:2x JST ごろ）: UNKNOWN
- 左のクラスの AP が右より低い理由: UNKNOWN（反転の整合の左右の一致と val の左右のインスタンス数は近い）
- q の行の和が約半数の枠で 1 を超える（二本目は 11 枠）理由の切り分け（5 クラスの頭で器具の 3 クラスが同じ画素に重なる度合い）: 測っていない
- 同じ seed の run の間のビットの非決定性の大きさ: 測っていない
- fp16 の非数が長く学んだときにどうなるか、bf16（変形注意だけ fp32）の学習の質と fp32 の比べ: 測っていない

## 7. 送出

- PR: #295（https://github.com/takuya3h/m2/pull/295、base phase0、Draft でない、OPEN）。#289（同じ分岐）は 2026-11-06 03:39 JST に利用者が統合済み（head ff954d9f、batch の決定の記録まで）。
  #295 は残りの commit を足す。`README.md` と `docs/experiment_log.md` が phase0 と衝突する（両方とも末尾に節を足しただけ。両方を残すのが解き方。分岐では解いていない）
- `make task-report`: 終了コード 0（verdict pass、issuer_defects 5 件、本文 12,457 B、report_sha256 7a0824d3…。この行は送信の後に足した）
