## 既知の限界（SPEC §6.4 と、利用者が 2026-10-20 に足した二点）

- 折りは 1 つ（A）、val は 2 動画（09・10）、seed は 1 つ。区間推定もクラスタの推論もできない。工程は動画 09 が塔単独で上限に近い（Jaccard 0.993）ので、検出から工程の差はほぼ動画 10 で決まる
- 4 epoch 目の値にも epoch ごとの揺れは残る（最良の回を選ばないが、epoch の選び方そのものの揺れは測っていない）
- カードの処方のうち、学習率の掃引、early stopping、5 折り、乱数入力・時間 shuffle・動画間 shuffle の腕、W2、増強なしは採っていない（SPEC §0 の 7）。
  入れ替えの腕は、フレームとの対応と時間方向のつながりを同時に壊す
- **入れ替えた信号は、val の 55.6%（train の 11.5%）のフレームが同じ動画の信号を受け取る**（直しの契約の audit 226〜229 行）。入れ替えの腕は「別の動画の信号」だけでできているわけではない
- 数値精度は規約の precision 節（界面の学習は TF32）ではなく、前回の経路のまま（工程から検出は bf16 の自動混合精度、評価は単精度。検出から工程は単精度）
- 工程から検出の二つの型はホストが違う（decoder-xattn は andrew、extra-queries は bengio）ので、型どうしの差にホストの差が混ざる
- **直しの契約の型は andrew（P3 の一部は bengio）、本契約の型は bengio（decoder-xattn は andrew）で回しており、型どうしの値を並べるときはホストの差を含む**。
  上の参考の表はホストの列を付けて並べただけで、処置の差として読まない（SPEC §6.2 の 7）
- 提案カードは repo に無く、関門（批判会話と利用者の判定）を通っていない。型の定義は SPEC §3 による
- 前回の限界（受け取り手も train で学習済み、工程塔は efros の塔の写し、工程注釈だけのフレームを使っていない、型ごとに学習率を探していない）はそのまま残る

## 型の定義の読み（SPEC §3 の範囲で実行者が決めたもの）

- decoder-xattn: 工程の token を key と value にそのまま使う（射影を挟まない）。部分層は decoder を通るすべての query（学習時の denoising と hybrid の経路を含む）に当てる
- extra-queries: 元の query の出力を構成で塔単独と同じに保つため、元の経路を D\* のまま回し、追加の query だけを各層で元の query の入力を key・value に加えて別に回す
  （mask を張った一つの計算と意味は同じで、丸めだけが違い得る）。学習では元の経路を評価と同じ形（denoising と hybrid なし）で勾配なしに回す。
  スコアの定数は一つのスカラーで全層の追加の出力に足す。e_i・u_i は正規分布で初期化
- logit-correction: b は W_in の bias に一つ。W_out と bias を零初期化
- tool-history: GRU の入力 W_in x + b_in は 64 次元。ゲートなし版は W_o と bias を零初期化
- 界面の初期化は固定の種で大域の乱数から切り離した（腕ごとに入力の次元が違っても、界面の他の部分の初期値と学習の乱数が同じ）

## 再現の手がかり

- 実装 `scripts/stage2pilot/{pd_four.py,dp_model.py,dp_train.py}`、起動 `run_pd_four.sh`・`run_dp_four.sh`、評価 `pd_four_eval.py`、見落とし `xq_missed.py`、
  殺し実験 `kill_four.py`、集計 `aggregate_four.py`。記録は `tasks/T-2026-10-19-stage2-pilot-four-new-types/{audit.md,audit_andrew.md}`
- 大きな生成物（D\* の train の出力、見落としの集合、界面の重み、寄与の評価の予測）は `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types/`（bengio。decoder-xattn の重みは andrew の同じ経路）
