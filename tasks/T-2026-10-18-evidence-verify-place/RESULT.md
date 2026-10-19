# RESULT — T-2026-10-18-evidence-verify-place

**実行者:** bengio（`hostname` は `Bengio`）/ `feat/evidence-verify-place` / 起点 origin/phase0 `40112290`
**実行日時:** 2026-10-19 01:1x〜（JST）
**判定:** PASS

命令と出力の全文は `audit.md` に置く（以下 `audit:行` で指す）。

## 1. 判定

**verdict: pass**

- **G1 pass**: 照合先の四系統（Crossref・doi.org・DataCite・arXiv の API）すべてに到達し、受け渡しの十件の sha256 とバイト数が SPEC の表と一致した（audit:119、audit:148）
- **G2 pass**: 照合器は実際の照合先と差し替えの HTTP の両方で五つの対照が期待どおり。様式の検査は零件と四種の一件ずつ。schema は正しい宣言を通し壊れた宣言 9 種を落とした（audit:247）
- **G3 pass**: 抽出した ID の集合が三つの地図とも起票者の一覧と一致した（差 0 件。audit:369）

解決された参照: `contract.conventions_rev` と `created_from.runindex_commit` は起点 `40112290` と同じ。`inject_verbatim`
（`conventions#prohibitions`、`conventions#issuer_cautions`）は原文を読み、操作の制約として使った（要約していない）。
`inputs.data.split_files` と `inputs.denominator` は**参照しなかった**。`decisions_required` 4 件は利用者が括弧のとおりで回答し、
`meta.amendments` に記録した（audit:99）。

## 2. 始める段

- 判定: 最初は**汚れ**（未追跡 14 件・ファイル 22 件、すべて `experiments/`）。手順書の選択肢 1 は退避の候補 0 件で、task-start は汚れの検査で止まった
- 利用者の判断で `.git/info/exclude` に 3 行と注記を足し（控え `~/m2-git-info-exclude.bak-20261019`）、`phase0` へ切り替えて清浄を確かめ、task-start を一度だけやり直した（audit:5–98）
- 目印の表示: **作成**（`task_id=…`・`branch=feat/evidence-verify-place` の 2 行）

## 3. 完了判定

| # | 期待 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 一つの命令で全 ID、三つの結果 | `make evidence-verify MAP=<地図>` で C・B・N を照合。結果は `docs/evidence/verification/` に 6 ファイル。分類の和 = 抽出した ID（29・34・36） | D-2 で集合の漏れ・余り 0。地図 B の写しに架空の arXiv ID を足すと不在が 0→1、ほかは不変（audit:431） |
| b | 照合器の対照 | Crossref DOI・arXiv ID 2 件が実在・書誌一致、DataCite DOI が実在（登録機関 DataCite）、架空の DOI・arXiv ID が不在、127.0.0.1:9 へ向けると到達不能 3／不在 0 | 実際の照合先と差し替えの HTTP の両方で測った（audit:249–275） |
| c | 様式の検査 | 三つの地図で違反 0（exit 0） | 地図 C の写しに四種を一種ずつ入れて各 1 件（exit 1）。雛形・旧地図・README・報告は対象外と表示（audit:277、audit:351） |
| d | schema | 正しい `bundle_extras` が L1 を通り、壊れた宣言 9 種が L1-1 で落ちる。全契約の `make task-validate` は前後とも 147 件 OK、契約ごとの成否の集合が同一（`diff` 空） | 変更前の schema で同じ正しい宣言が `L1-1 … ('bundle_extras' was unexpected)` で落ちることを先に再現した（audit:171） |
| e | 配置 | 地図 3・雛形を `docs/evidence/`、報告 5 を `reports/`、一覧を契約の下へ。要約値 10 件とも一致 | **置いた後のファイルから**計算した（audit:324） |
| f | 旧地図 | 旧地図 B の表題の直後に v1 の一文。`git diff --numstat` 追加 2・削除 0。旧地図 A の sha256 `9f723e4b…` 不変 | 一文は SPEC.md:112 と `grep -F` で一字一句一致（audit:346） |
| g | README | `docs/evidence/README.md`（C-4 の六項目） | README の命令を実行し終了コードを記録（evidence-check ×3 と抽出は 0、照合は C が make で 0、B・N が直接で 0。audit:351、audit:382） |
| h | 試験 | 新しい試験 76 件が通る。失敗の集合は変更前と同一の 8 件（名前で `diff` が空） | 照合器の試験は `urllib.request.urlopen` を塞ぐ仕掛けの下で通り、その仕掛けは実際の呼び出しを止めた。ネットワークを断つ `unshare -rn` はこのホストで許されない（§6） |
| i | 要約 | §4 | 地図三件の sha256 は照合の後も SPEC の表のまま（`1ab24a3c…`・`05a982ef…`・`9bb804b2…`） |
| j | PR | #231（`gh pr view` の応答: state OPEN、isDraft false、baseRefName phase0、headRefName feat/evidence-verify-place、headRefOid `db00963d`） | push しただけで終えていない。forbidden-check の違反 0 |

`make forbidden-check` は pass（変更 29、違反 0）。`make spec-check TASK=T-2026-10-18-evidence-verify-place` は該当 0。

## 4. 実測

照合の結果（2026-10-19 02:39〜02:40 JST。照合先は四系統とも 200、429 なし）:

| 地図 | 一致 | 差 | 照合不能 | 不在 | 到達不能 | 計（DOI・arXiv） | 書誌 ID の無い行 |
|---|---|---|---|---|---|---|---|
| C | 27 | 1 | 1 | 0 | 0 | 29（9・20） | C-24 |
| B | 29 | 5 | 0 | 0 | 0 | 34（4・30） | B-18 |
| N | 16 | 2 | 18 | 0 | 0 | 36（7・29） | N-15 |

差 8 件の内訳: 題名の欄が略称・説明の行 6 件（B-02 の 1610.08851・1610.08844、B-03、B-06、B-10、N-10。著者はすべて一致）、
題名の語の違い 1 件（C-21）、著者の欠け 1 件（N-01）。照合不能は、書誌 ID の列を持つ表の行が無い ID（C 1 件・N 17 件）と、
行に題名も著者も無い N-18。一件ずつ点検し、照合器の誤りは見つからなかった（audit:406）。地図は直していない。

D-4:

- **B-02 の 1610.08851** は「Single- and Multi-Task Architectures for Tool Presence Detection Challenge at M2CAI 2016」、
  **地図 N §8 の 1610.08844** は「Single- and Multi-Task Architectures for Surgical Workflow Challenge at M2CAI 2016」。
  別の文献で、著者はどちらも Twinanda, Mutter, Marescaux, de Mathelin, Padoy（2016）
- **N-01 の 10.5281/zenodo.20086606** は**実在**（doi.org の handle が responseCode 1）。登録機関は **DataCite**。題名は地図と全体一致、
  creators 6 名（Berk Ozmen ほか、Graham Schwarz は 6 番目）、publisher Zenodo、種類 ConferencePaper、`IsVersionOf 10.5281/zenodo.20086605`
- 書誌の欠けについて照合先が返した値:
  - C-06（2308.07918）著者: Chuhan Zhang, Ankush Gupta, Andrew Zisserman
  - C-13（10.1007/s11548-024-03063-9）著者: Georgii Kostiuchik, Lalith Sharan, Benedikt Mayer, Ivo Wolf, Bernhard Preim, Sandy Engelhardt
  - C-16（10.1109/WACV57701.2024.00641）題名: Egocentric Action Recognition by Capturing Hand-Object Contact and Object State
  - C-17（2102.00649）掲載先: arXiv の journal_ref は無し。comment「in IEEE Transactions on Pattern Analysis and Machine Intelligence, 2021」、arXiv の doi `10.1109/TPAMI.2021.3055233`
  - C-21（2410.20026）著者: Hao Ding, Yuqian Zhang, Wenzheng Cheng, Xinyu Wang, Xu Lian, Chenhao Yu, Hongchao Shu, Ji Woong Kim, Axel Krieger, Mathias Unberath
  - B-22（2407.07402、10.1007/978-3-031-72684-2_13）著者: Liangyang Ouyang, Ruicong Liu, Yifei Huang, Ryosuke Furuta, Yoichi Sato
  - N-18（1708.00666）題名: Temporal Dynamic Graph LSTM for Action-driven Video Object Detection。著者: Yuan Yuan, Xiaodan Liang, Xiaolong Wang, Dit-Yan Yeung, Abhinav Gupta
- 掲載先として照合先が返した値: **C-05（ORViT、2110.06915）** は journal_ref 無し、comment「CVPR 2022」（地図は「ECCV 2022 系」）。
  **C-14（Surgformer、2408.03867）** は journal_ref も comment も無い

照合器の命令の形: `make evidence-verify MAP=<地図>`、または `.venv/bin/python tools/verify_evidence_ids.py <地図>`（終了コード 0 / 1 不在 / 2 使い方 / 3 到達不能）。
様式の検査は `make evidence-check [MAP=<地図>]`。到達できた照合先: api.crossref.org、doi.org（handle・doiRA）、api.datacite.org、export.arxiv.org。

## 5. 起票者の誤り

1. **check_does_not_check**: E-1 は bengio で `make test` の失敗の集合を比べるとしたが、bengio の `make test` は
   `third_party/Relation-DETR/util/convergence.py` が無く収集で中断し、試験を一件も実行しない。比べても前後とも「収集の誤り 1 件」で一致するだけになる。
   同じ引数に `--continue-on-collection-errors` を足して測り直した（audit:171）
2. **check_does_not_check**: E-1 の `make spec-check` は TASK を付けていない。字面どおりに打つと全 147 契約が対象になり、過去の契約の 210 件の該当で exit 2 になる。
   本契約の検査としては働かない（Makefile の注記も TASK の指定を求める）。`TASK=` 付きで回して該当 0 を確かめた

## 6. 逸脱

- **environment**: 作業ツリーに Syncthing で届いた他契約の出力（未追跡 14 件）があり task-start が止まった。利用者の判断で `.git/info/exclude` に足し、phase0 へ切り替えてから task-start をやり直した（audit:5–98）
- **environment**: bengio の `make test` が収集で中断するため、変更前後の失敗の集合は `--continue-on-collection-errors` を足した pytest で比べた（`make test` そのものの結果も前後で同じ）
- **judgement**: 試験は `CUDA_VISIBLE_DEVICES=` で GPU を見せずに回した（契約は GPU を使わない。前後とも同じ条件）
- **environment**: CLAUDE.md の `ctxpack` がこのホストに無く、各サービスの作法の文書は WebFetch で読んだ
- **environment**: arXiv の API が数分間 429 を返し続けた。照合器の 429・5xx の待ちを 10・30・60・120 秒から 10〜600 秒の六段へ延ばした（audit:229）
- **judgement**: 題名の欄が略称・説明の行を「差」とする規則を、結果を見た後に緩めなかった（audit:406）
- **judgement**: ネットワークを断った状態の確認は `unshare -rn` が許されず取れなかった。通信の口を塞ぐ仕掛けで示した
- **judgement**: 対照の地図と結果は scratchpad に置き、repo には三つの地図の結果だけを置いた。試験の副産物 `.coverage`（未追跡）は commit していない

## 7. 想定外・UNKNOWN

- 常駐の同期が、exclude の追加で清浄になった元の分岐 `feat/drop-projection-check-in-contracts` を 01:36 JST に origin/phase0 へ早送りで統合し push した（`57717f6c` → `40112290`）。この分岐に開いている PR は無い（在るのは #213 MERGED のみ）。戻す・閉じるなどの操作はしていない（audit:63）
- arXiv の 429 が同じ出口の IP の他の台によるものかは **UNKNOWN**（この台には他のプロセスが無かった）
- 新しい試験がネットワークを断った状態でも通るかは **UNKNOWN**（`unshare` 不可）。差し替えの確認で代えた

## 8. 送出

- PR: #231（base phase0、Draft でない）。作業の commit `db00963d`
- `make task-report`: 送出の結果は audit.md の末尾に記録する（送るのはこの報告を commit した後）
