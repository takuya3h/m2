# RESULT — T-2026-10-07-track-extra-phase-annotations

ホスト efros、分岐 `feat/track-extra-phase-annotations`（起点 origin/phase0 `b9272cfe`）。GPU 不使用。
命令と出力の全文は `audit.md`。本書は節番号で指す。

## 判定

**verdict: pass。** G1 pass（`audit.md` §2–3）。G2 ask。8 本を利用者に諮り、「直さず表に残す」の回答を得た（§7）。

## 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 20 件の照合 | 件数 20、名前の集合一致、210618 バイト、要約値 `87f62aee…`。写し 2 か所と 20/20 一致 | 名前を一つ変えた一覧で集合差が出る |
| b | 読む側の分類 | 2 通りで探し、2 状態で動かして分類した。判断できない 8 本は G2 で決着し、未決は 0 | 既知の `load_phase` が両方の探し方に載り、DIFF と出る |
| c | 折り表の生成器 | 止まらず exit 0。要約値 `237837fa…976b` が記録と一致。`docs/stage0/` の差分 0 | 直す前は IndexError。一行変えると要約値が変わる |
| d | 部分集合の道具 | 回し直して md・csv の差分 0 行 | 一行変えると csv の要約値が変わる |
| e | P\*-20 が読む集合 | 追加 20 clip（17〜21）で変わらない。15 動画側は `data/processed` の manifest | 21_5 を除くと 19 clip になる |
| f | 追跡 | 20 件が index にあり、blob のバイトと sha256 が Task A と同一。除外の該当行 0 | 存在しない経路では 0 件 |
| g | 禁止領域の検査 | 違反 20 で、追跡した 20 件と集合として一致。それ以外 0 | 両方向の集合差 0 |
| h | 試験 | 6 failed / 699 passed。失敗の名前の集合が前後で同一 | 名前で比較した |
| i | 他ホスト向けの文書 | `docs/stage1/extra_phase_annotations.md`（一覧、表、手順、動画 22 の注記） | 一覧から計算した要約値が a と一致。一文字変えると `sha256sum -c` が FAILED |
| j | PR | 下の「送出」。分岐名は `feat/` で始まる | — |

## 実測

**読む側の表**（全文は `docs/stage1/extra_phase_annotations.md`、計測は `audit.md` §5）

- 直した: `a1_fold_table.load_phase` に `videos` を足し、`main` が公式分割の 15 動画を渡す
- 変わらない（変えない）:
  - `design_val_subsets`
  - `build_phase_manifest_p20`（17〜21 を明示）
  - `build_phase_manifest`（PAPER_SPLIT_VIDEOS で絞る）
  - `PhaseImageDataset`・`phase_trainer`・s3 設定（画像の索引で絞る）
  - thinning 2 本と `hts_phase_coverage` の両ディレクトリを読む呼び出し（raw に同じ写しがある）
  - diag（術具のフレームで引く）
  - s4 設定の `phase_label_dir`（読むコードが無い）
- 値が変わるが、利用者の判断で変えない 8 本:
  - `hts_phase_coverage` のプロジェクト側だけの集計（23 → 43 セグメント）
  - EDA 3 本（23 → 43 セッション、17233 → 27694 フレーム）
  - `audit_hts_coverage_export`・`audit_hts_vs_tool_phase`（工程のフレーム集合が変わる。術具との交わりは 15437 で不変）
  - `audit_l0_hts_acceptance` の c6（23 → 43）
  - `audit_l0b_raw_provenance`（`phase_frames` 17233 → 27694）

**禁止領域の検査**: 違反 20 件で、すべて追跡した 20 件の経路だった（契約の想定どおり。統合は利用者が判断する）。

**他ホストで要る手順**: 同じ経路に未追跡の写しがあるホストでは、同期の前に `sha256sum -c` で一覧と照合する。
20 件すべて一致すれば、写しを repo の外へ移してから同期する。一つでも違えば、何も消さずに止めて報告する。
git は、内容が同一でも未追跡のファイルを上書きしない。

## 起票者の誤り

1. asserted_without_measuring — 「動画 22 の注釈は efros に無い」としたが、`data/raw/…/annotations/phase/` には 22_1〜22_3 がある。無いのは本ディレクトリだけで、生成器の出力にも差は出なかった。
2. self_contradiction — Task B-3 は、直した後に生成物が変わらないことの確認を求める。しかし該当の監査と EDA の出力先は experiments/ で、禁止 5 に当たる。G2 で諮った。

## 逸脱

`result.yaml` の deviations 8 件。主なものは次の 3 つ。
- G2 で利用者に諮った
- audit 系は丸ごと動かさず、読み込み部分を写して計測した
- 実行者の誤りが 2 件あった（出所の比較の誤りと、README の行の二重化）。どちらも直した

## 想定外と UNKNOWN

UNKNOWN は無い。想定外は動画 22 の注釈が raw にあったこと（上記）。

## 送出

PR #204（base phase0、Draft でない、分岐 feat/track-extra-phase-annotations）。commit d1199a38、723f2341。
`make task-report` は exit 0（verdict pass、起票者の誤り 2、4986 バイト、report_sha256 e6b5369a…）。
