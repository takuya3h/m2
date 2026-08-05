# RESULT — <task_id>

**実行者:** <server> / <branch> / <commit>
**実行日時:** <ISO8601>
**判定:** PASS / FAIL / PARTIAL

## 1. 解決された参照（CLI が実行時に埋める）

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | exp:.../... | 実測値・n_seeds・split |
| sigma_policy.series | 省略（継承） | pstd |
| sigma_policy.sigma_source | 省略（継承） | paired_delta |
| sigma_policy.delta_sigma_source | 省略（継承） | paired |
| conventions_rev | <sha> | 差分の有無 |

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|

## 3. 成果物

| 種別 | パス | 件数 |
|---|---|---|

## 4. 受入基準の充足

| acceptance | 結果 |
|---|---|

## 5. deviations（指示書どおりにしなかった箇所）

**このセクションは空にしてはならない。** 逸脱が無い場合は「なし」と明記する。

- 指示:
- 実際:
- 理由:
- 分類: SPEC の欠陥 / 環境差 / 判断が必要だった

## 6. 未解決・申し送り

## 7. 数値の出所

すべての数値は実測である。未測定の項目は UNKNOWN と記載した。
