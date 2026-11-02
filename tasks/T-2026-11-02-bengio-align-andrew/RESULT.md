# RESULT — T-2026-11-02-bengio-align-andrew

実行ホスト bengio、基準 andrew（読むだけ）。2026-11-02 12:13〜12:53 UTC（21:13〜21:53 JST）。表は `experiments/analysis/bengio_align_andrew/REPORT.md`、手続きは `audit.md`（行番号で指す）。

## 1. 判定

**pass。** G1 通過（audit 31〜33 行）、G2 通過（audit 44〜46 行）、G3 通過（audit 66〜68 行）。
解決した参照: 注入の 3 アンカーの原文は `resolved_refs.md`。`conventions_rev` b59081e0 は phase0 の #282 の統合で、`context/conventions.md` の中身は今と同じ（最後の commit は 2d946b07）。
runindex 68befc3b・2363/1130/1736 は起票時と同じ。分母は本契約に無い（`inputs.denominator` を参照しなかった）。

**次の測定の契約を bengio で起票できる前提は満たした。** Relation-DETR の本体は andrew と一致し、検出塔の評価は記録と差 0.0（overall）・−4.49e-11（標的群）で一致した。

## 2. 完了判定（§6）

| # | 期待 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐 `feat/bengio-align-andrew`、起点 = HEAD = origin/phase0 d145854e、本契約以外の compute 0、GPU 2 枚とも使用率 0%・compute 0、空き 1,415,039,631,360 B。A-5 の値は `$D/start/`（audit 16〜30 行） | zsh 8、存在しない経路 0 |
| b | Relation-DETR | source 142・all 155 が andrew main と一致、三分類 0・0・0。揃える前の 8 件は差分から 8/8 戻せた | 揃える前の比べでは「違う」8・「andrew だけ」15。戻した版の 1 バイトを変えると不一致 |
| c | 拡張と評価 | `build.ninja` は bengio main の `.cu` を指し andrew と差 0 行。overall 差 0.0、標的群差 −4.49e-11。拡張（`ms_deform_attn_ext True`）と checkpoint（`warm-start from`）の読み込みが記録にある | 存在しない checkpoint の経路では回していない（GPU は評価一本）。既知の挙動として env-facts の装置の節（相対経路で AP 0） |
| d | Stage 2 の材料 | 17 件が andrew と同じ経路にあり、17/17 がバイト数と sha256 で一致 | 存在しない経路 `.../signals/no_such_file.npz` は「無い」 |
| e | 片付け | E1〜E10 の各項目に結果と理由（REPORT の片付けの表）。片付けた 29 件（ファイル 28・分岐 1）、残した項目は REPORT の表 | 片付けたファイル 28 件は `test -e` と `find`、分岐は `rev-parse` と `for-each-ref` で無い。残した項目は在る |
| f | 対象外の無変更 | data・`.venv`・入れ子の third_party・checkpoints・仮想環境の列・保存先の既存部分は前後一致。差は Task B〜E で変えたものだけ。同期で届いた差 0 | 同じ取り方で bengio main の Relation-DETR は 89dc93b4… → 20f15c06… と違う |
| g | 試験 | 開始時 名前 12（11 failed・1 error）→ 終了時 名前 11（11 failed）。差は `tests/test_stage1_dtower_convergence.py` の収集の失敗が消えた 1 件（`util/convergence.py` が入った） | 終了時の集合に名前を 1 つ足すと差に出る |
| h | andrew と同期 | andrew への書き込みの向き先を持つ命令 0（13 行）。出力に同期の対象の型 0 件。andrew に本契約の出力先は無い（`ls` と `find`） | andrew の既知の `experiments/analysis/bengio_andrew_env_survey` は「在る」。同期の照合で `experiments/x/foo.py` は「当たる」 |
| i | PR | 本ファイルの 7. | — |

## 3. 実測（次の測定の契約で使う値）

- 揃えた後の Relation-DETR（bengio main）: source 142 / 2f08e5213cb5c377…、all 155 / 20f15c061b435ce4…（andrew main と同じ）
- 評価: overall AP 0.7273450248398429（差 0.0）、標的群 AP 0.7950748008550897（差 −4.49e-11）、陰性対照群 0.6726631817581498、AP50 0.851807431425236
- 拡張: `build.ninja` は andrew と同一（f72b62a0…）。`.so` は 1a05ed5b…で andrew の 79b55a8a…と**不一致**（同じ入力から別に作ったビルド物）
- Stage 2 の材料: andrew だけだった 17 件（13,502,221,812 B）を同じ経路に置いた
- 片付け: 片付けた = 分岐 `chore/evidence-map-a-place-start`、`__pycache__` 4 件、控え 2 件、`/tmp` の 22 件。
  残した = worktree 3（m2-four・m2-s2fix-bengio・wt_phase0）と E1・E2 の分岐、重ねの BODY、除外の 5 行と控え、`/tmp` の特定できない 17 件と道具の置き場
- 変わった違い: Relation-DETR の本体の違いは無くなった。拡張の `.so` の要約値の違いは残る。`pyvenv.cfg` の違いは変えていない

## 4. 起票者の誤り

- asserted_without_measuring: E5 の片付ける条件を「拡張のビルドがこの置き場を指していない」だけで書いたが、版管理下の台本 4 本が BODY の経路を既定値に持つことを確かめていなかった。条件どおりに消すと、その台本が動かなくなる
- rule_read_narrowly: E1〜E3 の条件「commit されていない変更が 0 件」は追跡下の変更だけを指すように読めるが、worktree には無視された未追跡に m2 本体に無い実験の出力（計 365 MB）があった。追跡下だけで判定して外すと失われる

## 5. 逸脱

- E1・E2・E3・E6（と E7）は利用者に諮り、残した（escalate_if の「commit されていない変更」「現れるファイルがある」）
- 開始時の試験の終わり 5 秒が Task B の写しと重なった（収集は写しの前。結果は調査時と同じ）
- Task D の一回目で andrew 側の `~` が展開されず、本契約が作った 0 バイトのファイル 1 件を `/bin/rm -f` で消した（`rm` は対話の確認の別名で止まった。実行基盤の拒否ではない）
- c の陰性対照（存在しない checkpoint）は回さず、既知の挙動を引いた
- `README.md`・`docs/experiment_log.md` は更新していない（契約の allow_write が出力先に限る）

## 6. 想定外・UNKNOWN

- `.so` の要約値が andrew と違うことが数値に影響するか: 評価一本では差 0.0。学習での影響は測っていない（UNKNOWN）
- 作り直す前のビルド物は scratchpad（このセッションの間だけ在る）に写しただけで、版管理には要約値だけを残した

## 7. 送出

- PR #284（base phase0、分岐 feat/bengio-align-andrew、Draft でない）
- `make task-report`: 送信の後に audit の末尾へ記録する
