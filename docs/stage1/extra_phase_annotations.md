# 追加動画 17〜21 の工程の注釈（版管理に入れた 20 件）

契約 `T-2026-10-07-track-extra-phase-annotations`。efros にだけ未追跡で在った追加動画 17〜21 の工程の注釈 CSV 20 件を、
**今の場所（`data/annotations/egosurgery_phase/`）のまま**版管理に入れた。名前も内容も変えていない。

- 用途は工程塔 P\*-20 の訓練（`scripts/build_phase_manifest_p20.py` が動画 17〜21 を明示して読む）
- **動画 22 の注釈は含まない**（efros に無い。P\*-20 も動画 22 を使わない）。`context/conventions.md#folds` は追加動画を 17〜22 の 6 本と書くが、本契約は規約を変えていない
- 同じディレクトリには 15 動画の注釈（23 クリップ）も在る。ディレクトリを丸ごと読む道具の扱いは下の表を参照

## 一覧

出所: efros の `data/annotations/egosurgery_phase/` で 2026-10-07 に測った値（契約 `T-2026-10-07-design-val-subset-balance` の audit §2 の記録と一致）。
同じ内容の写しが `data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase/` と、
repo の外の `~/slocal2/EgoSurgery/annotations/coco_format/phase/` に 20 件とも在る（sha256 で一致）。

| 経路 | バイト | sha256 |
|---|---|---|
| `data/annotations/egosurgery_phase/17_1.csv` | 1172 | `847ba667fec2ece3b3734749d2594fe2275cf726b4bafdb7a77795bcc49dfe24` |
| `data/annotations/egosurgery_phase/18_1.csv` | 7684 | `9ee21848060fc1e0ae16036ba4ef37edce38e0acadc5d389cc5bca218b918433` |
| `data/annotations/egosurgery_phase/18_2.csv` | 11703 | `49b82ab82f5f7f4a8d472345fe7375b002158a9fd3c2b9f045f863107c90c632` |
| `data/annotations/egosurgery_phase/19_1.csv` | 28413 | `d71b7815046cab4c953e7e4e9cfdd3d5affbafcbc5cc8ba74eee309deaa49c10` |
| `data/annotations/egosurgery_phase/19_2.csv` | 8829 | `05843bef7c6445e242ce778313bf5cf83a57dcb7a9d14fe4e8228d6987ee035a` |
| `data/annotations/egosurgery_phase/19_3.csv` | 25929 | `59da9280e608f0fa67551cfb5951faaa3b7bc1d75840de1b1233d32e6eae4144` |
| `data/annotations/egosurgery_phase/19_4.csv` | 2238 | `177d3d06cd2aa96abce55d6e378fe500cb20aeb33a2ee3129007426f0ddf8f8e` |
| `data/annotations/egosurgery_phase/19_5.csv` | 11793 | `e38d49234eadf4fd20c484dfd40b30722081accc227af1d7123597ed3dbf15b1` |
| `data/annotations/egosurgery_phase/19_6.csv` | 27816 | `5ffb84449faf8ad2233fbd763cbce0f23f3c3948da1d61de0353d573a4b58d88` |
| `data/annotations/egosurgery_phase/20_2.csv` | 9399 | `84f7047653d03b448246b64cffcbeb35a1830c306e03dc001e4accad6e1e9a43` |
| `data/annotations/egosurgery_phase/20_4.csv` | 8706 | `4da37d58fd68bc224934595b605ef2935e7b1609c61ee4d62c837443bcbf113e` |
| `data/annotations/egosurgery_phase/20_5.csv` | 7047 | `792e85f385ba5b94b122676e14db3240b83e3ff97fe52f79301a21c2f7b306c3` |
| `data/annotations/egosurgery_phase/20_6.csv` | 5850 | `bf4def2b7ec833645df6eec49ee73017bef07c0759a55c24cba2d2d228ff9923` |
| `data/annotations/egosurgery_phase/20_7.csv` | 432 | `0f541540834ce9e3e510cc57c2c75da8c378eb06b911eeb037e07ea2ba7fc235` |
| `data/annotations/egosurgery_phase/20_8.csv` | 852 | `c1453c3409a5d66dd92bb7739e6ccaf3464d74472b9a457123e1663112026958` |
| `data/annotations/egosurgery_phase/21_1.csv` | 1185 | `9318a0c659432bd12ac767b70f1cbd4ea686607b15f7b276ea4cc54cf480d2f4` |
| `data/annotations/egosurgery_phase/21_2.csv` | 9672 | `6144b2bcda856632f77fec2f4933889372761492634e15266d1c411915b886e6` |
| `data/annotations/egosurgery_phase/21_3.csv` | 16611 | `620af49d4d0f8075a4516beb989a61ba7d9d14cc2809ee01b757a2454c667da1` |
| `data/annotations/egosurgery_phase/21_4.csv` | 21425 | `e3d01c25e928c623b275f30d3667b8613b416ecc7b6b251c02e2600fb493a072` |
| `data/annotations/egosurgery_phase/21_5.csv` | 3862 | `2acf8ed508f812f006cc813b6518329e871ba8b64ed947d3cdd929b9d7d9e700` |

合計 20 件、210618 バイト。一覧の要約値（経路とタブと sha256 の 20 行を sha256 に通した値）は
`87f62aeef0985a9e3623f964df75a52b0b6945b536179b1ac93ac74e1996135d`。

`sha256sum -c` にそのまま渡せる形:

    847ba667fec2ece3b3734749d2594fe2275cf726b4bafdb7a77795bcc49dfe24  data/annotations/egosurgery_phase/17_1.csv
    9ee21848060fc1e0ae16036ba4ef37edce38e0acadc5d389cc5bca218b918433  data/annotations/egosurgery_phase/18_1.csv
    49b82ab82f5f7f4a8d472345fe7375b002158a9fd3c2b9f045f863107c90c632  data/annotations/egosurgery_phase/18_2.csv
    d71b7815046cab4c953e7e4e9cfdd3d5affbafcbc5cc8ba74eee309deaa49c10  data/annotations/egosurgery_phase/19_1.csv
    05843bef7c6445e242ce778313bf5cf83a57dcb7a9d14fe4e8228d6987ee035a  data/annotations/egosurgery_phase/19_2.csv
    59da9280e608f0fa67551cfb5951faaa3b7bc1d75840de1b1233d32e6eae4144  data/annotations/egosurgery_phase/19_3.csv
    177d3d06cd2aa96abce55d6e378fe500cb20aeb33a2ee3129007426f0ddf8f8e  data/annotations/egosurgery_phase/19_4.csv
    e38d49234eadf4fd20c484dfd40b30722081accc227af1d7123597ed3dbf15b1  data/annotations/egosurgery_phase/19_5.csv
    5ffb84449faf8ad2233fbd763cbce0f23f3c3948da1d61de0353d573a4b58d88  data/annotations/egosurgery_phase/19_6.csv
    84f7047653d03b448246b64cffcbeb35a1830c306e03dc001e4accad6e1e9a43  data/annotations/egosurgery_phase/20_2.csv
    4da37d58fd68bc224934595b605ef2935e7b1609c61ee4d62c837443bcbf113e  data/annotations/egosurgery_phase/20_4.csv
    792e85f385ba5b94b122676e14db3240b83e3ff97fe52f79301a21c2f7b306c3  data/annotations/egosurgery_phase/20_5.csv
    bf4def2b7ec833645df6eec49ee73017bef07c0759a55c24cba2d2d228ff9923  data/annotations/egosurgery_phase/20_6.csv
    0f541540834ce9e3e510cc57c2c75da8c378eb06b911eeb037e07ea2ba7fc235  data/annotations/egosurgery_phase/20_7.csv
    c1453c3409a5d66dd92bb7739e6ccaf3464d74472b9a457123e1663112026958  data/annotations/egosurgery_phase/20_8.csv
    9318a0c659432bd12ac767b70f1cbd4ea686607b15f7b276ea4cc54cf480d2f4  data/annotations/egosurgery_phase/21_1.csv
    6144b2bcda856632f77fec2f4933889372761492634e15266d1c411915b886e6  data/annotations/egosurgery_phase/21_2.csv
    620af49d4d0f8075a4516beb989a61ba7d9d14cc2809ee01b757a2454c667da1  data/annotations/egosurgery_phase/21_3.csv
    e3d01c25e928c623b275f30d3667b8613b416ecc7b6b251c02e2600fb493a072  data/annotations/egosurgery_phase/21_4.csv
    2acf8ed508f812f006cc813b6518329e871ba8b64ed947d3cdd929b9d7d9e700  data/annotations/egosurgery_phase/21_5.csv

## 注釈のディレクトリを読む箇所

「変わるか」は、15 動画の 23 件だけを置いたディレクトリと、20 件を足した実際のディレクトリ（43 件）で、各箇所の読み込みを動かして比べた結果である。

| 場所 | 読む動画の決め方 | 20 件で読む集合が変わるか | 用途 | 扱い |
|---|---|---|---|---|
| `scripts/analysis/a1_fold_table.py` `load_phase` | 列挙した全部 → 本契約で `videos` を明示して絞る | 変わる（15 → 20 動画。生成器が `IndexError` で止まる） | 15 動画の折り表 | **直した**。`main` が公式分割の 15 動画を渡す。表の要約値 `237837fa…976b` が一致、`docs/stage0/` は不変 |
| `scripts/analysis/design_val_subsets.py` | 折り表の 15 動画に絞る | 変わらない | 15 動画 | 変えない（回し直して文書と csv の差分 0 行） |
| `scripts/build_phase_manifest_p20.py` `extra_clips` | 動画 17〜21 を明示 | 変わらない（efros では 20 clip のまま） | P\*-20 の追加動画 | 変えない。**他ホストでは 20 件が届いて初めて作れる** |
| `scripts/build_phase_manifest.py` `build` | 列挙した全部、`PAPER_SPLIT_VIDEOS` の 15 動画で絞る | 変わらない（残す clip と語彙が同一） | 15 動画の manifest | 変えない |
| `src/egosurgery/datasets/phase_dataset.py` `PhaseImageDataset` | 列挙した全部、`data/raw/ego/{train,val,test}` の画像の索引で絞る | 変わらない（3 split の samples が同一） | 15 動画の工程学習 | 変えない |
| `src/egosurgery/engines/phase_trainer.py`、`configs/stage/s3_phase_frame.yaml` `phase_ann_dir` | `PhaseImageDataset` に渡す | 変わらない | 同上 | 変えない |
| `configs/stage/s4_phase_baseline.yaml` `phase_label_dir` | 読むコードが無い | — | — | 変えない |
| `scripts/analysis/split_thinning_rule.py` `load_phase`、`scripts/analysis/verify_thinning_rule.py` `load_phase_labels` | 本ディレクトリと raw の `annotations/phase/` の両方 | 変わらない（raw に同じ写し。ラベルが同一。`verify_thinning_rule` の出所の記録は 17〜21 の 10461 フレームで変わるが、出所は使われていない） | 間引き規則 | 変えない |
| `scripts/analysis/hts_phase_coverage.py` `load_phase([PROJECT, HTS])` | 両方 | 変わらない | HTS の工程被覆 | 変えない |
| `scripts/diag_hand_tool_consistency.py` `load_phase` | 列挙した全部 | 写像は変わるが、15 動画の術具のフレームで引くため出力に届かない | 手と術具の整合 | 変えない |
| `scripts/analysis/hts_phase_coverage.py` `load_phase([PROJECT])` | 本ディレクトリだけ | **変わる**（23 → 43 セグメント） | 7 月の監査（被覆の記録） | 利用者の判断で変えない |
| `scripts/analyze_annotations_{eda,advanced,extra}.py` | 列挙した全部 | **変わる**（23 → 43 セッション、17233 → 27694 フレーム） | 15 動画の EDA | 利用者の判断で変えない |
| `scripts/audit_hts_coverage_export.py`、`scripts/audit_hts_vs_tool_phase.py` | 列挙した全部 | **変わる**（工程のフレーム集合 17233 → 27694。術具のフレームとの交わりは 15437 で不変） | 7 月の監査 | 利用者の判断で変えない |
| `scripts/audit_l0_hts_acceptance.py` `check_c6_phase_coexist` | 列挙した全部 | **変わる**（`phase_video_segments` 23 → 43） | 7 月の監査 | 利用者の判断で変えない |
| `scripts/audit_l0b_raw_provenance.py` | 列挙した全部 | **変わる**（`phase_frames` 17233 → 27694） | 7 月の監査 | 利用者の判断で変えない |

対象外: `scripts/audit_hts_acceptance.py` は raw 側の `annotations/phase/` を読む（本ディレクトリを読まない）。
`scripts/preprocess_ego.py` は本ディレクトリへ `phases_{split}.json` を書く側で、CSV を列挙しない。

**「利用者の判断で変えない」の 8 本は、20 件の追跡の後に再実行すると 17〜21 が入り、`experiments/analysis/` に記録済みの値と変わる。**
再実行して 15 動画の値を得たいときは、読む動画を 15 本に絞ってから回すこと。

## 同じ経路に未追跡の写しを持つホストでの手順

`git merge` / `git pull` は、未追跡のファイルを上書きしない（**内容が同一でも拒否する**）。
同じ経路に未追跡の写しがあるホストでは、同期の前に次を行う。

1. 写しを上の一覧と照合する（repo 直下で、一覧を `/tmp/extra_phase.sha256` などへ保存して `sha256sum -c`）
2. **20 件すべてが一致する場合**: 写しを repo の外へ移してから同期する。同期の後、もう一度 `sha256sum -c` で 20 件が一致することを確かめる。移した写しは同じ内容なので、確かめた後は消してよい
3. **一つでも一致しない、または一覧に無い名前の CSV がある場合**: 何も消さず、何も移さず、止めて利用者に報告する
