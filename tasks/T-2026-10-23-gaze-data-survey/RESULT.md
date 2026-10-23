# T-2026-10-23-gaze-data-survey 結果

## 判定

- status: pass。G1 も pass。
- 視線データは `data/raw/gaze/` にある。csv 57 本、49,940 行で、見出しは `Frame,norm_pos_x,norm_pos_y`。
- 被覆は、01〜15 が注釈の行 17,233 枚の 100%、17〜21 が 10,461 枚のうち 10,453 枚（99.92%）。
- **全 49,940 行で `norm_pos_x == norm_pos_y` だった。** 届いた形のままでは 2 次元の視線点にならず、GGMAE 型のマスクの入力には足りない。書き出しの不具合が疑われる。利用者は「このまま記録して進める」を選んだ。
- 経緯: 三つの方法で探した時点（JST 15:49〜15:52）では、andrew のどこにも無かった。利用者に問い合わせ、利用者が調査の途中（ディレクトリの更新は JST 16:01）に送った。
- 本文は [REPORT.md](../../experiments/analysis/gaze_data_survey/REPORT.md)、命令と出力は [audit.md](audit.md) にある。

## 完了判定

| # | 実測 |
|---|---|
| a | 分岐は feat/gaze-data-survey、起点は origin/phase0 = d013c5f1。汚れは取り込んだ契約 2 件だけ。空き容量は 1.6 TB（/home/ubuntu/slocal2）。行数は manifest を読む方法と CSV を数える方法で一致し、17,233 と 10,461。試験の前は 7 failed / 959 passed（audit L5〜L92） |
| b | 名前・内容・記録の三つの方法で、data/ の全体と andrew の全 4 装置を探した。来る前は 0 件で、判定は「対象が無い」。分類 `Eye` は患者の目の物体注釈で、「条件に合わない」。陽性対照の `egosurgery_phase/*.csv` は三つの方法のすべてで見つかった。届いた後の置き場は data/raw/gaze/（57 本、1.7 MB、ファイルの更新日時 2024-07-26）。公式配布の README には視線の記載が無い（audit L93〜L833、REPORT L19〜L39） |
| c | 欄は 3 つ（`Frame` 文字列、`norm_pos_x`・`norm_pos_y` 実数）。写しも 3 欄だった。値は正規化座標 0.002〜0.99634。原点は UNKNOWN。1 フレーム 1 行で、鍵は `Frame`。NaN・空欄・範囲外はいずれも 0（audit L834〜L952、REPORT L40〜L61） |
| d | 動画ごとの表を作った。分母は注釈の行と、`raw/ego` の画像のファイル（01〜15 は 15,437 枚で全数が対応、17〜21 は 10,453 / 10,461）。画面内は 100%。1 フレームのサンプル数は 1。対照: 動画 05 を抜いた写しで 17,233 → 15,915、画面外の 1 点で 17,233 → 17,232（audit L953〜L1027、REPORT L62〜L110） |
| e | 01_1_0004 で、σ = 64 px（仮）の 1080 × 1920 のヒートマップを作った。最大値の位置 (1225, 689) は視線点 (1224.99, 689.06) と画素の単位で一致した。対照: 点を (0.2, 0.3) に移すと最大値の位置は (384, 324) に動いた。図は 1 枚（REPORT L111〜L120） |
| f | 追跡される変更は置き場、契約のディレクトリ、受け皿だけで、data/ への変更は無い（audit「F4」）。forbidden-check は pass（起点基準、audit「F1」）。陽性対照として clone の写しの data/ に 1 件足すと fail になった（audit「F2」）。試験の失敗の集合は audit「F3」 |
| g | PR #265。base は phase0、head は feat/gaze-data-survey、isDraft false、OPEN（audit「commit と送出」） |

解決された参照: `inject_verbatim` 3 節の原文は audit の末尾に写した。conventions の blob ceb7ef0f は契約の conventions_rev と一致する。

## 実測（次の契約で使う値）

- 経路は `data/raw/gaze/<クリップ>.csv`（`data/raw/**` は無視の一覧に入っていて追跡されない）。鍵は `Frame`（`VV_C_NNNN`）で、工程 CSV と manifest の `frame` と同じ。
- 座標は正規化の [0, 1]。原点は UNKNOWN。**y は x の写し。**
- レートは 1 フレーム 1 点で、0.5 fps のフレームに揃っている。元のサンプリングのレートは UNKNOWN。
- 解像度は 1920 × 1080 で、27,694 枚の全数を確かめた。
- 欠けは 8 枚（`20_6_0284`、`20_7_0092`〜`0098`）で、行が無い形で表れる。
- 対象の外にも視線がある。14 クリップ（03_1、12_2、15_2、16_*、17_2、20_3、20_9〜20_15）で、計 22,254 フレーム。

## 起票者の誤り

- `check_does_not_check`: Task B-2 の内容の探索は、対象を `raw/ego/` の各動画と `annotations/` に限っている。
  - 視線が実際に届いた `data/raw/gaze/` はこの集合の外にあり、書かれたとおりに探すと見落とす。
  - 実行では `data/raw` と `data/annotations` の全体に広げた。
- `asserted_without_measuring`: §3 は README の値を「確定した事実」として書いている。実測とは二点で食い違う。
  - 「raw/ego/ のファイル数は 01〜15 で 15,440」とあるが、jpg は 15,437 枚である。差の 3 は .gitkeep の数と同じだが、確かめていない。
  - 「フレームの置き場は data/raw/ego/」とあるが、manifest の 1,796 枚は `data/raw/OpenSurgery_Dataset/01_frames/initial_videos/` にある。

## 逸脱

- **探索の範囲を広げた。** 名前の探索は andrew の全装置とホームまで、内容の探索は data/raw と data/annotations の全体まで広げた。
- **視線データは契約の途中で届いた。** 利用者が送った。b の「対象が無い」は届く前の判定であり、c〜e は届いた版を測った。
- **公式配布は WebFetch で読んだ。** CLAUDE.md は先に `ctxpack` を使うよう求めるが、andrew に無かった。利用者の承認を得て、読むだけにした。
- **x==y のまま計測した。** 利用者の決定に従った。ヒートマップは原点を左上と仮定し、σ = 64 px は仮の値である。
- **forbidden-check の基準を起点に変えた。** origin/phase0 が開始の後に進んだ（PR #263・#264）ため、起点 d013c5f1 を基準にしても回した。
- **置き場に計測のスクリプト `survey.py` と、その出力 2 つ（summary.json、coverage_by_video.csv）を置いた。**
- **試験の前の失敗は 7 件だった。** 前の契約の 6 件に、2 GPU の試験 `test_stage1_ptower_r3_dist.py::test_two_gpus_give_the_one_gpu_gradient_over_an_uneven_tail` 1 件が加わっている。本契約の変更より前からある。

## 想定外・UNKNOWN

- 想定外は二つあった。
  - 全行で x==y だった。
  - 空振りの対照の一回目は無効だった（`rm` が確認を求めて写しから抜けず、書き換えたフレームは manifest の外だった）。直して二回目で有効になった。
- UNKNOWN は四つある。
  - 座標の原点
  - 元のサンプリングのレート
  - x と y のどちらが正しい値か
  - 15,440 と 15,437 の差の 3 が .gitkeep か

## 送出

PR #265（base phase0、Draft でない）。commit は eb36ef52、f4e7fb5c。task-report の終了コードと台帳の応答は audit「commit と送出」に記録する。
