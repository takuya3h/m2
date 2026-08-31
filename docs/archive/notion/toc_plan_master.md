# 旧マスター頁の見出し（未取得）

対象: `configs/notion.yaml` の `pages.plan_master` = `361ee4d4-7777-804f-b7e6-c023cf50267d`

**status: unreachable。** 2026-08-31 の実測で HTTP 404 `object_not_found` が返った。
Integration に共有されていないためであり、契約 §1 の罠 1 が発火した事例である。

    Could not find block with ID: 361ee4d4-7777-804f-b7e6-c023cf50267d.
    Make sure the relevant pages and databases are shared with your (integration)

**共有設定は利用者の操作領域**であり、実行者は記録するだけである（契約 §9）。
共有された後に同じ命令で取得できる。

    python docs/archive/notion/export_notion.py toc \
        --id 361ee4d4-7777-804f-b7e6-c023cf50267d \
        --out docs/archive/notion/toc_plan_master.md

見出しは一件も取得していない。**推定で埋めていない。**
