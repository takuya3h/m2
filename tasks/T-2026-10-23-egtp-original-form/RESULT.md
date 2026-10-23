# T-2026-10-23-egtp-original-form 結果

## 判定

status: partial。EGTP を原典（StableSPR 式 3〜6）の形に置き換え、確率の不変・因果性・閾値・初期化・starts の試験が通った。G1・G2 は pass。ssm の出力だけは GPU 禁止のため測っておらず、関数単位のソースの一致で代えた（完了判定 d）。

## 完了判定

| # | 実測 |
|---|---|
| a | HEAD `d013c5f1` で、試験の失敗の集合 12 件と 10 通りの出力の要約値を変更前に取った（[audit.md](audit.md) L13） |
| b | 手で導いた E・n・Z（t=2 の Z = (d1+d2)/(d2−d1) = 2.9597、t=3 の Z = 4.9396）と状態の列に、1e-12 で一致。期待値を一つ変えると落ちる（L41、L55） |
| c | 確率は同一の物として返る。t=120 より後を変えても前の状態は同じ。k 1e9 では状態が一つ、一定の反証では有限の時刻で遷移する。遷移の時刻に E・n・σ が 0 になる。starts の位置は argmax から始まる |
| d | 10 通り（linear・A・B・C・memory 2 通り・progress・stabilize A/B/C、egtp 無し）の出力と復号がビット一致。ssm は UNKNOWN（CUDA が要る）。egtp 以外の関数 32 件のソースは同一（L41） |
| e | 変更は README.md・scripts/・tests/・本契約のディレクトリ・受け皿だけ。依存の差分 0。forbidden-check pass。失敗の集合は前後で同じ 12 件（L65） |
| f | PR #263 は OPEN・Draft でない・base phase0・head feat/egtp-original-form（gh pr view の応答） |

## 実測

- **n と σ:** E(c) が最後に 0 だった後に積んだ δ(c) の個数と標本標準偏差（ddof 1、Welford の逐次）。E(c) が 0 に切られたら 0 に戻す。n < 2 の間は Z = 0。σ の下限は 1e-3（一定の δ でも Z が有限）
- **初期化:** 遷移の後と、starts・最初の時刻では E・n・σ を 0 に戻す
- **log の下限:** p を 1e-12 で下から切ってから float64 で log を取る
- **試験の期待値:** 二クラスの列で δ を `math.log`、σ を `statistics.stdev` から書いた閉じた形（L41）
- **k = 0 の対照:** 遷移は最初の反証（t=1）ではなく 2 つ目（t=2）。n < 2 で Z = 0 と決めたため（L41）
- **変更前から落ちていた試験:** `test_existing_candidates_match_baseline` の 4 件。前の契約の基準値は andrew で取られ、bengio では一致しない。比較は bengio で取った変更前後の値で行い、`BASELINE` の値は変えていない

## 起票者の誤り

- `check_does_not_check`: `conventions_rev` に commit ではなく blob（HEAD の規約の blob、`ceb7ef0f`）が書かれていた。検証器 L2-6 は `git diff` の失敗を黙って空として扱い、警告せずに通した。中身が同じことは手で確かめた（L5）
- `asserted_without_measuring`: SPEC §3 は八候補のビット不変を求め、試験の基準値の流用を勧めた。しかし既存の `BASELINE` は 4 候補だけで、bengio では変更前から一致しない。ssm は CPU では動かず、GPU 禁止の下では測れない
- `self_contradiction`: Task C-8 の「試験を全件回す」は ssm の GPU 試験を含み、§6 の「GPU を使わない」とぶつかる

## 逸脱

- environment: 試験の 1 回目は GPU が見えた状態で回り、ssm の試験が cuda で走った。以後は `CUDA_VISIBLE_DEVICES=""` で回し、比較はその条件の前後だけで行った
- environment: 引数なしの pytest は収集で止まるため（third_party の欠落）、`--continue-on-collection-errors` を付けた
- judgement: 試験で E と Z を見るため、補助の生成器 `egtp_steps` と定数 2 つを足した。`egtp` の呼び口は変えていない
- judgement: 規約の原文を写す要件を優先したため、本報告は 60 行の目安を超える

## 想定外・UNKNOWN

- ssm の出力のビット一致: UNKNOWN（測るには GPU が要る）
- 原典の n と σ の定義そのもの: 原典に書かれていないため、上の形は実装者が選んだ

## 送出

PR #263。forbidden-check・spec-check・task-validate は exit 0。pytest は exit 1（変更前と同じ 12 件の失敗）。台帳への送り返しの結果は audit の「E. 送出」に記録する。

## 1. 解決された参照

- `inputs.data.split_files`: schema の必須項目として置かれているが、参照しなかった。`inputs.denominator` と `inputs.frozen_source` は指定なし。`inputs.sigma_policy` は省略のため `conventions#sigma` を継承する（数値の判定には使わない）
- `contract.inject_verbatim`: `context/conventions.md`（blob ceb7ef0f）の原文を次に写す

## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |


## issuer_cautions

**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 4 | 仕組みの挙動は実装を読んでから信じる |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
| 7 | **丸めた表示を実数として扱わない** |
| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
| 11 | 測定の副作用が禁止領域へ触れないか確かめる |
| 12 | **判断の前に、いま見ているものが最新かを確かめる** |
| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
| 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

