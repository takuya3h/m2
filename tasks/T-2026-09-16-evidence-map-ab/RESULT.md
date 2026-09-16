# RESULT — T-2026-09-16-evidence-map-ab

**実行者:** bengio / `feat/evidence-map-ab`
**実行:** 2026-09-17 00:42 JST 開始（Phase A 00:49）
**判定:** PASS（G1・G2 とも通過）
**成果:** `docs/evidence/2026-09-16-A-phase-tower-candidates.md` / `docs/evidence/2026-09-16-B-p2d-interface.md`
**証跡:** `audit.md`

## 冒頭に置く結論

**地図 A・B の全 26 行（A 15 / B 11）が実在し、書誌も地図の記載と一致した。**
不在 0 件、到達不能 0 件、書誌に差 0 件。**地図から外した行は無い。**

**著者未確認だった二件は埋まった。** SurgMAE は Muhammad Abdullah Jamal, Omid Mohareri、
SurgPETL は Shu Yang, Zhiyuan Cai, Luyang Luo, Ning Ma, Shuchang Xu, Hao Chen。UNKNOWN は無い。

**数値・表番号・設定の記述は一字も書き換えていない。** 印の列に照合結果を足しただけである。

## 1. 解決された参照

| spec の記載 | 解決先 | 値 |
|---|---|---|
| `contract.conventions_rev` | 実測 | `a8c07e813696d3720ceee648e8aa202224285955` |
| `created_from.runindex_commit` | 実測 | `96eb3a1ca20ab7eb4b373d93304c9e6b33b733d5` |
| `created_from.counts` | 本契約は runindex を参照しないため 0 のまま | 実測値は index 1266 / experiments 285 / verdicts 1506 |
| `contract.inject_verbatim` | `conventions#prohibitions` の原文 | `no_split_redefine` split を再定義しない / `no_raw_write` `data/raw` `data/external` に書き込まない / `no_estimated_values` 未測定の値を書かない。未測定は UNKNOWN / `no_runindex_hand_edit` `runindex/` を手で編集しない |
| 元の報告 | **repo に無い** | deep research の出力ファイルは存在せず、出所は SPEC.md の付録 A・B（30894 バイト、sha256 先頭 `c17c2d9961aeb979`） |

## 2. 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 全行の ID が照合を通る | **不通 0 件**（26/26 実在） | 零件のため b の陰性対照で照合器が落ちることを示した。外した行は無い |
| b | 照合器の対照 | 実在 DOI 2 件 HTTP 200 / 架空 DOI HTTP 404 | 両方の応答全文を `audit.md:23` に置いた。片方向だけでは「常に実在と返す壊れ方」と区別できない |
| c | 三方向の検索記録 | 両地図とも 3（同ドメイン・一般機構・隣接ドメイン） | 一方向の語を消すと 3 → 2 に落ちることを写しで確かめた（`audit.md:55`）。行番号 A:48-50 / B:44-46 |
| d | 設定距離 0〜1 の行 | **A 7 件**（距離0:1、距離1:6）/ **B 3 件**（距離1:3） | 距離の分布を全行から数えた。A {0:1,1:6,2:4,3:4} / B {1:3,2:5,3:3} |
| e | 未検証の組み合わせの表 | A は A.3（行59）、B は B.3 の「未」の表と B.5（行78） | 表を欠く本文では該当が 0 になる。行番号を記録した |
| f | citeturn の残骸 | **両地図 0 件** | 写しに 1 件混ぜると `grep -c` が 0 → 1 に変わった（終了コードではなく件数で数えた） |
| g | 著者未確認二件の補完 | 両件とも著者が埋まった。UNKNOWN 0 件 | 応答の該当箇所は `audit.md:118`。地図から「著者未確認」の語は 0 件になった |
| h | PR が Draft でなく存在する | **後述**（第 6 節） | 分岐名 `feat/evidence-map-ab` |

## 3. 実測

### 照合結果の四種

| 種別 | 件数 |
|---|---:|
| 実在・書誌一致 | **26** |
| 実在・書誌に差 | 0 |
| 不在 | 0 |
| 到達不能 | 0 |

**外した行:** 無し（不在が零件のため）。
**書誌に差のある行:** 無し。escalate_if の「差が三件以上」には該当しない。

### 著者の補完

| 通称 | arXiv | 照合が返した著者 |
|---|---|---|
| SurgMAE | 2305.11451 | Muhammad Abdullah Jamal, Omid Mohareri |
| SurgPETL | 2409.20083 | Shu Yang, Zhiyuan Cai, Luyang Luo, Ning Ma, Shuchang Xu, Hao Chen |

### 検証の終了コード

| 検査 | 終了コード |
|---|---|
| `make task-validate` | 0（WARN なし） |
| `make task-preflight` | 0（6 PASS / 6 SKIP / 0 FAIL） |
| `make spec-check` | 0（規則 8 件すべて該当なし） |
| `make forbidden-check` | **0**（違反 0 件。変更 5 件のみ） |

## 4. 起票者の誤り

**無し。** 第 2 節の「確定した事実」は全て実測と一致した。
起票者が確認済みとした DOI 二件は実在し、書誌も一致した。
著者未確認とした二件は実際に arXiv の応答から埋まり、起票者の判断（未確認のまま渡す）は正しかった。

**一件だけ補足がある（誤りではない）。** SPEC Task C-2 は各ファイルの先頭に
「元の報告（ファイル名とバイト数）」を書けと指示するが、**deep research の出力ファイルは repo に無い。**
出所を SPEC.md の付録（30894 バイト、sha256 先頭 `c17c2d9961aeb979`）として記し、
ファイルが無いことを地図の冒頭に明記した。

## 5. 逸脱

1. **照合器の誤検出を一度出し、直した**（judgement）。最初の実装が MS-TCN と CLIPSeg を
   「書誌に差」と判定したが、**いずれも照合器側の正規化の誤りで地図の誤りではなかった**
   （複合姓「Abu Farha」の先頭語だけを取った、`ü` を片側だけ ASCII 化した）。
   両側に同じ正規化を当てて直し、二件とも「実在・書誌一致」になった。経緯は `audit.md:100`。
   **誤ったまま報告すれば「差 2 件」として地図に印が付き、起票者の写し誤りを疑わせるところだった。**
2. **地図 B に B.5 を足した**（judgement）。SPEC の付録 B には「未検証の組み合わせ」という
   独立の節が無く、B.3 の表の「未」のセルが実質それに当たる。完了判定 e を満たすため
   B.5 を末尾に置き、「B.3 の表で『未』と記されたセルが未検証の組み合わせである」と説明した。
   **B.3 の表そのものは書き換えていない。**
3. **印の列の読み方を冒頭に注記した**（judgement）。印には起票時の「未照合」が残り、
   その後ろに本契約の「照合2026-09-16:」が続くため、そのままでは矛盾して見える。
   **元の印を書き換えず**、読み方を冒頭で説明する形にした。
4. **`spec.yaml` を編集した**（judgement）。`REPLACE-BY-EXECUTOR` のプレースホルダ二件を
   実測値へ確定し、`meta.amendments` に記録した。
5. **`make taskindex` / `make inbox` を実行していない**（judgement）。SPEC 禁止 3 が
   並行契約との衝突を理由に再生成を禁じているため。**投影への反映は未確認である。**
6. **作業ツリーの退避は本契約の前に済んでいる**（environment）。開始時に追跡下 1 件・
   未追跡 39 ファイルがあり、`git stash push -u -m "pre-T-2026-09-16-evidence-map-ab"` で退避した。
   退避しないと `task_start.sh` が exit 3 で止まる実装である。

## 6. 想定外・UNKNOWN

- **元の報告ファイルが repo に無い**（第 4 節）。出所は SPEC.md の付録とした。
- **エンジン間の突き合わせは無い。** 地図の行は ChatGPT deep research 一エンジンの報告から
  写したものである（SPEC 第 2 節）。本契約は文献の**実在と書誌**を照合しただけで、
  **各文献の本文にその数値が書いてあるかは照合していない。** 数値の検証は利用者が
  八本について原典で行っている（SPEC 第 1 節）。残りの行の数値は UNKNOWN のままである。
- **投影への反映**（逸脱 5）。

## 7. 送出

（PR と台帳の結果をここに追記する）
