# 実行監査

## 開始・参照・プリフライト

起点 HEAD=origin/phase0=6680a9aa63d03e944cdea57ca4b0354fbebb7cac。ホスト Bengio。作業ツリー清浄から task-start が feat/evidence-maps-revise と所有情報つき .sync-pause を作成。稼働同期の sync-pause 参照は2件。

make task-validate: exit 0、1 task(s), 0 failed。make task-preflight: exit 0、6 PASS / 0 WARN / 8 SKIP / 0 FAIL。SKIP=P2,P3,P4,P5,P11,P12,P13,P14。

記憶ツールと planning-with-files は利用不可。プランモードへ切り替える手段なし。契約の Phase A〜D を順守。

## A 起点の実測

測定方法: .venv の Python pathlib.read_bytes / hashlib.sha256。原測定と改訂前の照合結果は baseline.json（省略なし）。

```json
{
  "docs/evidence/2026-10-18-B-p2d-interface.md": {
    "bytes": 65725,
    "sha256": "1ab24a3cbfaba4f7b654c8fcd12a9deb9f9556c337b95392d10897011ee9ccca"
  },
  "docs/evidence/2026-10-18-C-d2p-interface.md": {
    "bytes": 71540,
    "sha256": "05a982ef4c8a9372a3855414393714c15cbb2cebabbbc6a07855eef22a5dc563"
  },
  "docs/evidence/2026-10-18-N-novelty.md": {
    "bytes": 31607,
    "sha256": "9bb804b2eacdaac8842e2fc952d70479e747c9657186909ea9740b9e0413e6c8"
  },
  "docs/evidence/reports/B-chatgpt.md": {
    "bytes": 38349,
    "sha256": "ef94ea71aba1b5e81dea60ae0b55581dfdfda7cf290fe29d56dcb20b7bc33dd9"
  },
  "docs/evidence/reports/N1-novelty-search-result.md": {
    "bytes": 37524,
    "sha256": "9e1dc1b7f9ad99faff469fa7aa001bfc586d98876677c52c2c1c1dcd83cfa3cd"
  },
  "docs/evidence/reports/R1-deep-research-report.md": {
    "bytes": 40202,
    "sha256": "1f95517bf4ce63015d9574ee7e3616859021882a7014feb4f261d76d9c49dce5"
  },
  "docs/evidence/reports/deep-research-report-B2.md": {
    "bytes": 72035,
    "sha256": "c7aad1c222d9159c1209a557f765e0400f85a3b6ccd8d92025683a2ce8102116"
  },
  "docs/evidence/reports/deep-research-report-C2.md": {
    "bytes": 72966,
    "sha256": "5d3c3ed514551cf11d1b75dcc8b6542b7fb5efefeedb91956a5d561284c141fd"
  },
  "docs/evidence/2026-09-16-A-phase-tower-candidates.md": {
    "bytes": 14167,
    "sha256": "9f723e4b17825b0854930b9a31c92fbf26cb298c20c0d4f133ff8883dfacddf0"
  },
  "docs/evidence/2026-09-16-B-p2d-interface.md": {
    "bytes": 12174,
    "sha256": "5aab3910cd8e4c04f77f795b8fc3d3930f0751e2a810da541568b53f6bbbad2d"
  },
  "docs/evidence/README.md": {
    "bytes": 9552,
    "sha256": "35a8922aa6f161bf383fe2eb443cef5aec20318312ddf8b52519c0ddedcdf11c"
  },
  "docs/evidence/_template.md": {
    "bytes": 4474,
    "sha256": "69e95ea37106fac90b463eabde7879cfc60df1575ffabdd10223f1c9f5b61376"
  },
  "tasks/T-2026-10-19-evidence-maps-revise/SPEC.md": {
    "bytes": 19772,
    "sha256": "fd8b3dbea0d7546892405316f6ac53e0b4456c92fc2b876ca2008fd93502ea22"
  }
}
```

パッチは repo 外で受領し tasks 内に写した。原本と写しは62122 bytes、sha256=fc9922526166c232c2d423dc8f6376b3126f46ecf42814e6c94001944d912444。

### A-5 到達確認

照合器の Client.get を既定設定で逐次呼び出した（連絡先なし）。

```json
[
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/TPAMI.2021.3055233",
    "at": "2026-10-19T03:30:51+09:00",
    "status": 200,
    "bytes": 9540
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/TPAMI.2021.3055233",
    "at": "2026-10-19T03:30:52+09:00",
    "status": 200,
    "bytes": 537
  },
  {
    "service": "datacite",
    "url": "https://api.datacite.org/dois/10.5281/zenodo.20086606",
    "at": "2026-10-19T03:30:52+09:00",
    "status": 200,
    "bytes": 12196
  },
  {
    "service": "arxiv",
    "url": "https://export.arxiv.org/api/query?id_list=2309.01093",
    "at": "2026-10-19T03:30:53+09:00",
    "status": 200,
    "bytes": 2841
  }
]
```

## B パッチ適用

git apply --check / git apply: ともに exit 0、標準出力なし。

docs/evidence/2026-10-18-C-d2p-interface.md: bytes=73074 sha256=80837fcf4ce2c49335f3d5578408645f34b4a8d6592b3bb0c1c102f726915630 一致

docs/evidence/2026-10-18-B-p2d-interface.md: bytes=69690 sha256=11d2e3efa80fa8ac1d6b595c9a75b56f84b218562e53a701402112303ce94caa 一致

docs/evidence/2026-10-18-N-novelty.md: bytes=39226 sha256=74ea24a6d18106fd2cbb99a2953a8282d996939cf744403e1a3b3b1db751fe4f 一致

git diff --name-only: 三つの地図だけ（未追跡の契約ファイルは別枠）。

```
41	40	docs/evidence/2026-10-18-B-p2d-interface.md
10	9	docs/evidence/2026-10-18-C-d2p-interface.md
36	12	docs/evidence/2026-10-18-N-novelty.md
```

起票者の予測は C +10/-9、B +41/-40、N +36/-12。

## C-1 様式検査

命令: .venv/bin/python tools/check_evidence_map.py docs/evidence/2026-10-18-C-d2p-interface.md docs/evidence/2026-10-18-B-p2d-interface.md docs/evidence/2026-10-18-N-novelty.md

```
検査 docs/evidence/2026-10-18-C-d2p-interface.md: 違反 0 件
検査 docs/evidence/2026-10-18-B-p2d-interface.md: 違反 0 件
検査 docs/evidence/2026-10-18-N-novelty.md: 違反 0 件

規約から読んだ禁止語 15 語 / reports/ のファイル 5 件
exit=0
```

### 照合命令

.venv/bin/python tools/verify_evidence_ids.py docs/evidence/2026-10-18-C-d2p-interface.md

```
実在・書誌一致 29 / 実在・書誌に差 0 / 実在・照合不能 0 / 不在 0 / 到達不能 0（計 29）
結果: docs/evidence/verification/2026-10-18-C-d2p-interface.json、docs/evidence/verification/2026-10-18-C-d2p-interface.md
exit=0
```

### 照合命令

.venv/bin/python tools/verify_evidence_ids.py docs/evidence/2026-10-18-B-p2d-interface.md

```
実在・書誌一致 34 / 実在・書誌に差 0 / 実在・照合不能 0 / 不在 0 / 到達不能 0（計 34）
結果: docs/evidence/verification/2026-10-18-B-p2d-interface.json、docs/evidence/verification/2026-10-18-B-p2d-interface.md
exit=0
```

## 陽性対照（メモリ上のみ、追加通信なし）

```json
[
  {
    "judgement": "c: 様式検査",
    "breaking_input": "メモリ上で C の **版:** 行だけを除く",
    "observed": "原文は違反0、欠落入力は違反1: [{'kind': 'header_field', 'line': 0, 'detail': '見出しの前に **版:** の欄が無い'}]"
  },
  {
    "judgement": "d: ID 集合の差",
    "breaking_input": "メモリ上で arXiv 9999.99999 を一件追加する",
    "observed": "集合差が arxiv 9999.99999 の追加を検出した"
  },
  {
    "judgement": "a: SHA-256",
    "breaking_input": "パッチのメモリ上の写しに一バイトを追加する",
    "observed": "True（契約値と不一致）"
  }
]
```

### 照合命令

.venv/bin/python tools/verify_evidence_ids.py docs/evidence/2026-10-18-N-novelty.md

```
実在・書誌一致 37 / 実在・書誌に差 0 / 実在・照合不能 0 / 不在 0 / 到達不能 0（計 37）
結果: docs/evidence/verification/2026-10-18-N-novelty.json、docs/evidence/verification/2026-10-18-N-novelty.md
exit=0
```

## C-3〜5 ID 集合・予測・新規 ID・N の比較対象行

### 地図 N

```json
{
  "before_total": 36,
  "before_counts": {
    "実在・書誌一致": 16,
    "実在・書誌に差": 2,
    "実在・照合不能": 18,
    "不在": 0,
    "到達不能": 0
  },
  "before_ids": [
    [
      "arxiv",
      "1602.03012"
    ],
    [
      "arxiv",
      "1610.08844"
    ],
    [
      "arxiv",
      "1610.08851"
    ],
    [
      "arxiv",
      "1708.00666"
    ],
    [
      "arxiv",
      "1804.08328"
    ],
    [
      "arxiv",
      "1805.04409"
    ],
    [
      "arxiv",
      "1904.01665"
    ],
    [
      "arxiv",
      "1907.06099"
    ],
    [
      "arxiv",
      "2001.06902"
    ],
    [
      "arxiv",
      "2003.10751"
    ],
    [
      "arxiv",
      "2006.04096"
    ],
    [
      "arxiv",
      "2106.07682"
    ],
    [
      "arxiv",
      "2107.04810"
    ],
    [
      "arxiv",
      "2109.14956"
    ],
    [
      "arxiv",
      "2305.13961"
    ],
    [
      "arxiv",
      "2307.07483"
    ],
    [
      "arxiv",
      "2401.11174"
    ],
    [
      "arxiv",
      "2405.19644"
    ],
    [
      "arxiv",
      "2406.01079"
    ],
    [
      "arxiv",
      "2406.03095"
    ],
    [
      "arxiv",
      "2411.16794"
    ],
    [
      "arxiv",
      "2501.11153"
    ],
    [
      "arxiv",
      "2503.18755"
    ],
    [
      "arxiv",
      "2507.16559"
    ],
    [
      "arxiv",
      "2511.06549"
    ],
    [
      "arxiv",
      "2512.14712"
    ],
    [
      "arxiv",
      "2603.12433"
    ],
    [
      "arxiv",
      "2606.26634"
    ],
    [
      "arxiv",
      "2606.29102"
    ],
    [
      "doi",
      "10.1016/j.media.2010.10.001"
    ],
    [
      "doi",
      "10.1016/j.media.2024.103366"
    ],
    [
      "doi",
      "10.1109/access.2025.3573264"
    ],
    [
      "doi",
      "10.1109/cvpr42600.2020.01121"
    ],
    [
      "doi",
      "10.1109/tmi.2016.2593957"
    ],
    [
      "doi",
      "10.3390/data10010007"
    ],
    [
      "doi",
      "10.5281/zenodo.20086606"
    ]
  ],
  "after_ids": [
    [
      "arxiv",
      "1602.03012"
    ],
    [
      "arxiv",
      "1610.08844"
    ],
    [
      "arxiv",
      "1610.08851"
    ],
    [
      "arxiv",
      "1708.00666"
    ],
    [
      "arxiv",
      "1804.08328"
    ],
    [
      "arxiv",
      "1805.04409"
    ],
    [
      "arxiv",
      "1904.01665"
    ],
    [
      "arxiv",
      "1907.06099"
    ],
    [
      "arxiv",
      "2001.06902"
    ],
    [
      "arxiv",
      "2003.10751"
    ],
    [
      "arxiv",
      "2006.04096"
    ],
    [
      "arxiv",
      "2106.07682"
    ],
    [
      "arxiv",
      "2107.04810"
    ],
    [
      "arxiv",
      "2109.14956"
    ],
    [
      "arxiv",
      "2305.13961"
    ],
    [
      "arxiv",
      "2307.07483"
    ],
    [
      "arxiv",
      "2401.11174"
    ],
    [
      "arxiv",
      "2405.19644"
    ],
    [
      "arxiv",
      "2406.01079"
    ],
    [
      "arxiv",
      "2406.03095"
    ],
    [
      "arxiv",
      "2411.16794"
    ],
    [
      "arxiv",
      "2501.11153"
    ],
    [
      "arxiv",
      "2503.18755"
    ],
    [
      "arxiv",
      "2507.16559"
    ],
    [
      "arxiv",
      "2511.06549"
    ],
    [
      "arxiv",
      "2512.14712"
    ],
    [
      "arxiv",
      "2603.12433"
    ],
    [
      "arxiv",
      "2606.26634"
    ],
    [
      "arxiv",
      "2606.29102"
    ],
    [
      "doi",
      "10.1016/j.media.2010.10.001"
    ],
    [
      "doi",
      "10.1016/j.media.2022.102611"
    ],
    [
      "doi",
      "10.1016/j.media.2024.103366"
    ],
    [
      "doi",
      "10.1109/access.2025.3573264"
    ],
    [
      "doi",
      "10.1109/cvpr42600.2020.01121"
    ],
    [
      "doi",
      "10.1109/tmi.2016.2593957"
    ],
    [
      "doi",
      "10.3390/data10010007"
    ],
    [
      "doi",
      "10.5281/zenodo.20086606"
    ]
  ],
  "removed": [],
  "added": [
    [
      "doi",
      "10.1016/j.media.2022.102611"
    ]
  ],
  "counts": {
    "実在・書誌一致": 37,
    "実在・書誌に差": 0,
    "実在・照合不能": 0,
    "不在": 0,
    "到達不能": 0
  },
  "predicted_match": 37,
  "prediction_differences": [],
  "new_ids": [
    {
      "kind": "doi",
      "id": "10.1016/j.media.2022.102611",
      "lines": [
        71
      ],
      "registry": "Crossref",
      "reference": {
        "title": "Anticipation for surgical workflow through instrument interaction and recognized Signals",
        "authors": [
          "Kun Yuan",
          "Matthew Holden",
          "Shijian Gao",
          "Wonsook Lee"
        ],
        "year": "2022",
        "venue": "Medical Image Analysis",
        "extra": {
          "type": "journal-article",
          "publisher": "Elsevier BV",
          "volume": "82",
          "page": "102611"
        }
      },
      "map_row": {
        "row_id": "N-15",
        "line": 71,
        "literature": "Yuan ほか 2022, Anticipation for surgical workflow through instrument interaction and recognized Signals",
        "venue": "Medical Image Analysis",
        "id_text": "DOI 10.1016/j.media.2022.102611（起票者が 2026-10-19 に Crossref の書誌検索で特定。報告は ID 未確認）"
      },
      "other_rows": [],
      "title": {
        "result": "一致",
        "detail": "全体",
        "map": "Anticipation for surgical workflow through instrument interaction and recognized Signals"
      },
      "authors": {
        "result": "一致",
        "detail": "先頭 1 名（ほか）",
        "map": [
          "Yuan"
        ],
        "et_al": true
      },
      "venue": {
        "reference": "Medical Image Analysis",
        "map": "Medical Image Analysis"
      },
      "note": "",
      "class": "実在・書誌一致"
    }
  ],
  "n_rows": [
    {
      "id": "1610.08844",
      "row_id": "N-44",
      "line": 106
    },
    {
      "id": "10.1109/TMI.2016.2593957",
      "row_id": "N-30",
      "line": 92
    },
    {
      "id": "1602.03012",
      "row_id": "N-30",
      "line": 92
    },
    {
      "id": "2406.03095",
      "row_id": "N-31",
      "line": 93
    },
    {
      "id": "10.3390/data10010007",
      "row_id": "N-32",
      "line": 94
    },
    {
      "id": "2411.16794",
      "row_id": "N-33",
      "line": 95
    },
    {
      "id": "1907.06099",
      "row_id": "N-34",
      "line": 96
    },
    {
      "id": "2305.13961",
      "row_id": "N-35",
      "line": 97
    },
    {
      "id": "2107.04810",
      "row_id": "N-36",
      "line": 98
    },
    {
      "id": "2512.14712",
      "row_id": "N-37",
      "line": 99
    },
    {
      "id": "2503.18755",
      "row_id": "N-38",
      "line": 100
    },
    {
      "id": "2405.19644",
      "row_id": "N-39",
      "line": 101
    },
    {
      "id": "2511.06549",
      "row_id": "N-40",
      "line": 102
    },
    {
      "id": "2507.16559",
      "row_id": "N-41",
      "line": 103
    },
    {
      "id": "2109.14956",
      "row_id": "N-42",
      "line": 104
    },
    {
      "id": "1610.08851",
      "row_id": "N-43",
      "line": 105
    },
    {
      "id": "10.1016/j.media.2024.103366",
      "row_id": "N-45",
      "line": 107
    },
    {
      "id": "2501.11153",
      "row_id": "N-46",
      "line": 108
    }
  ],
  "rows_without_id": []
}
```

問い合わせ実測（応答の抽出済み全書誌は verification/2026-10-18-N-novelty.json の results[].reference）：

```json
[
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.5281/zenodo.20086606",
    "at": "2026-10-19T03:31:41+09:00",
    "status": 200,
    "bytes": 403
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.5281/zenodo.20086606",
    "at": "2026-10-19T03:31:42+09:00",
    "status": 200,
    "bytes": 70
  },
  {
    "service": "datacite",
    "url": "https://api.datacite.org/dois/10.5281/zenodo.20086606",
    "at": "2026-10-19T03:31:42+09:00",
    "status": 200,
    "bytes": 12196
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/cvpr42600.2020.01121",
    "at": "2026-10-19T03:31:43+09:00",
    "status": 200,
    "bytes": 539
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1109/cvpr42600.2020.01121",
    "at": "2026-10-19T03:31:44+09:00",
    "status": 200,
    "bytes": 75
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/cvpr42600.2020.01121",
    "at": "2026-10-19T03:31:44+09:00",
    "status": 200,
    "bytes": 9670
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/ACCESS.2025.3573264",
    "at": "2026-10-19T03:31:45+09:00",
    "status": 200,
    "bytes": 540
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1109/ACCESS.2025.3573264",
    "at": "2026-10-19T03:31:46+09:00",
    "status": 200,
    "bytes": 74
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/ACCESS.2025.3573264",
    "at": "2026-10-19T03:31:46+09:00",
    "status": 200,
    "bytes": 11767
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1016/j.media.2010.10.001",
    "at": "2026-10-19T03:31:47+09:00",
    "status": 200,
    "bytes": 555
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1016/j.media.2010.10.001",
    "at": "2026-10-19T03:31:48+09:00",
    "status": 200,
    "bytes": 74
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1016/j.media.2010.10.001",
    "at": "2026-10-19T03:31:48+09:00",
    "status": 200,
    "bytes": 15844
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1016/j.media.2022.102611",
    "at": "2026-10-19T03:31:49+09:00",
    "status": 200,
    "bytes": 732
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1016/j.media.2022.102611",
    "at": "2026-10-19T03:31:50+09:00",
    "status": 200,
    "bytes": 74
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1016/j.media.2022.102611",
    "at": "2026-10-19T03:31:50+09:00",
    "status": 200,
    "bytes": 17660
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/TMI.2016.2593957",
    "at": "2026-10-19T03:31:51+09:00",
    "status": 200,
    "bytes": 534
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1109/TMI.2016.2593957",
    "at": "2026-10-19T03:31:52+09:00",
    "status": 200,
    "bytes": 71
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/TMI.2016.2593957",
    "at": "2026-10-19T03:31:52+09:00",
    "status": 200,
    "bytes": 8024
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.3390/data10010007",
    "at": "2026-10-19T03:31:53+09:00",
    "status": 200,
    "bytes": 524
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.3390/data10010007",
    "at": "2026-10-19T03:31:54+09:00",
    "status": 200,
    "bytes": 67
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.3390/data10010007",
    "at": "2026-10-19T03:31:54+09:00",
    "status": 200,
    "bytes": 10782
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1016/j.media.2024.103366",
    "at": "2026-10-19T03:31:55+09:00",
    "status": 200,
    "bytes": 732
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1016/j.media.2024.103366",
    "at": "2026-10-19T03:31:56+09:00",
    "status": 200,
    "bytes": 74
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1016/j.media.2024.103366",
    "at": "2026-10-19T03:31:56+09:00",
    "status": 200,
    "bytes": 19958
  },
  {
    "service": "arxiv",
    "url": "https://export.arxiv.org/api/query?id_list=1610.08844,1804.08328,2106.07682,2603.12433,2006.04096,1805.04409,2001.06902,2406.01079,2307.07483,2401.11174,2003.10751,1904.01665,2606.26634,2606.29102,1708.00666,1602.03012,2406.03095,2411.16794,1907.06099,2305.13961,2107.04810,2512.14712,2503.18755,2405.19644,2511.06549,2507.16559,2109.14956,1610.08851,2501.11153&max_results=29",
    "at": "2026-10-19T03:31:57+09:00",
    "status": 200,
    "bytes": 78799
  }
]
```
### 地図 C

```json
{
  "before_total": 29,
  "before_counts": {
    "実在・書誌一致": 27,
    "実在・書誌に差": 1,
    "実在・照合不能": 1,
    "不在": 0,
    "到達不能": 0
  },
  "before_ids": [
    [
      "arxiv",
      "1602.03012"
    ],
    [
      "arxiv",
      "1709.07871"
    ],
    [
      "arxiv",
      "1807.10565"
    ],
    [
      "arxiv",
      "1912.09930"
    ],
    [
      "arxiv",
      "2005.02190"
    ],
    [
      "arxiv",
      "2006.03201"
    ],
    [
      "arxiv",
      "2102.00649"
    ],
    [
      "arxiv",
      "2110.06915"
    ],
    [
      "arxiv",
      "2304.03959"
    ],
    [
      "arxiv",
      "2306.11726"
    ],
    [
      "arxiv",
      "2308.07918"
    ],
    [
      "arxiv",
      "2311.00180"
    ],
    [
      "arxiv",
      "2404.11903"
    ],
    [
      "arxiv",
      "2405.19644"
    ],
    [
      "arxiv",
      "2408.03867"
    ],
    [
      "arxiv",
      "2410.20026"
    ],
    [
      "arxiv",
      "2507.16559"
    ],
    [
      "arxiv",
      "2511.06549"
    ],
    [
      "arxiv",
      "2605.20901"
    ],
    [
      "arxiv",
      "2607.08514"
    ],
    [
      "doi",
      "10.1007/978-3-030-00937-3_31"
    ],
    [
      "doi",
      "10.1007/978-3-031-18814-5_2"
    ],
    [
      "doi",
      "10.1007/s11548-024-03063-9"
    ],
    [
      "doi",
      "10.1016/j.media.2026.103945"
    ],
    [
      "doi",
      "10.1109/tmi.2016.2593957"
    ],
    [
      "doi",
      "10.1109/tmm.2025.3543033"
    ],
    [
      "doi",
      "10.1109/tpami.2020.2992889"
    ],
    [
      "doi",
      "10.1109/wacv57701.2024.00641"
    ],
    [
      "doi",
      "10.1515/cdbme-2020-0037"
    ]
  ],
  "after_ids": [
    [
      "arxiv",
      "1602.03012"
    ],
    [
      "arxiv",
      "1709.07871"
    ],
    [
      "arxiv",
      "1807.10565"
    ],
    [
      "arxiv",
      "1912.09930"
    ],
    [
      "arxiv",
      "2005.02190"
    ],
    [
      "arxiv",
      "2006.03201"
    ],
    [
      "arxiv",
      "2102.00649"
    ],
    [
      "arxiv",
      "2110.06915"
    ],
    [
      "arxiv",
      "2304.03959"
    ],
    [
      "arxiv",
      "2306.11726"
    ],
    [
      "arxiv",
      "2308.07918"
    ],
    [
      "arxiv",
      "2311.00180"
    ],
    [
      "arxiv",
      "2404.11903"
    ],
    [
      "arxiv",
      "2405.19644"
    ],
    [
      "arxiv",
      "2408.03867"
    ],
    [
      "arxiv",
      "2410.20026"
    ],
    [
      "arxiv",
      "2507.16559"
    ],
    [
      "arxiv",
      "2605.20901"
    ],
    [
      "arxiv",
      "2607.08514"
    ],
    [
      "doi",
      "10.1007/978-3-030-00937-3_31"
    ],
    [
      "doi",
      "10.1007/978-3-031-18814-5_2"
    ],
    [
      "doi",
      "10.1007/s11548-024-03063-9"
    ],
    [
      "doi",
      "10.1016/j.media.2026.103945"
    ],
    [
      "doi",
      "10.1109/tmi.2016.2593957"
    ],
    [
      "doi",
      "10.1109/tmm.2025.3543033"
    ],
    [
      "doi",
      "10.1109/tpami.2020.2992889"
    ],
    [
      "doi",
      "10.1109/tpami.2021.3055233"
    ],
    [
      "doi",
      "10.1109/wacv57701.2024.00641"
    ],
    [
      "doi",
      "10.1515/cdbme-2020-0037"
    ]
  ],
  "removed": [
    [
      "arxiv",
      "2511.06549"
    ]
  ],
  "added": [
    [
      "doi",
      "10.1109/tpami.2021.3055233"
    ]
  ],
  "counts": {
    "実在・書誌一致": 29,
    "実在・書誌に差": 0,
    "実在・照合不能": 0,
    "不在": 0,
    "到達不能": 0
  },
  "predicted_match": 29,
  "prediction_differences": [],
  "new_ids": [
    {
      "kind": "doi",
      "id": "10.1109/TPAMI.2021.3055233",
      "lines": [
        94
      ],
      "registry": "Crossref",
      "reference": {
        "title": "Forecasting Action Through Contact Representations From First Person Video",
        "authors": [
          "Eadom Dessalene",
          "Chinmaya Devaraj",
          "Michael Maynord",
          "Cornelia Fermüller",
          "Yiannis Aloimonos"
        ],
        "year": "2023",
        "venue": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
        "extra": {
          "type": "journal-article",
          "publisher": "Institute of Electrical and Electronics Engineers (IEEE)",
          "volume": "45",
          "issue": "6",
          "page": "6703-6714"
        }
      },
      "map_row": {
        "row_id": "C-17",
        "line": 94,
        "literature": "Dessalene ほか, Forecasting Action through Contact Representations from First Person Video",
        "venue": "報告に掲載先の記載なし（L213 は「後続 TPAMI 論文」と書く）。照合: arXiv の comment は「in IEEE Transactions on Pattern Analysis and Machine Intelligence, 2021」",
        "id_text": "arXiv 2102.00649、DOI 10.1109/TPAMI.2021.3055233（DOI は照合〔2026-10-19〕で arXiv の doi 欄が返した値。報告には無い）"
      },
      "other_rows": [],
      "title": {
        "result": "一致",
        "detail": "全体",
        "map": "Forecasting Action through Contact Representations from First Person Video"
      },
      "authors": {
        "result": "一致",
        "detail": "先頭 1 名（ほか）",
        "map": [
          "Dessalene"
        ],
        "et_al": true
      },
      "venue": {
        "reference": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
        "map": "報告に掲載先の記載なし（L213 は「後続 TPAMI 論文」と書く）。照合: arXiv の comment は「in IEEE Transactions on Pattern Analysis and Machine Intelligence, 2021」"
      },
      "note": "",
      "class": "実在・書誌一致"
    }
  ],
  "n_rows": [],
  "rows_without_id": [
    "C-24"
  ]
}
```

問い合わせ実測（応答の抽出済み全書誌は verification/2026-10-18-C-d2p-interface.json の results[].reference）：

```json
[
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/TMI.2016.2593957",
    "at": "2026-10-19T03:31:13+09:00",
    "status": 200,
    "bytes": 534
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1109/TMI.2016.2593957",
    "at": "2026-10-19T03:31:14+09:00",
    "status": 200,
    "bytes": 71
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/TMI.2016.2593957",
    "at": "2026-10-19T03:31:14+09:00",
    "status": 200,
    "bytes": 8024
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/TPAMI.2020.2992889",
    "at": "2026-10-19T03:31:15+09:00",
    "status": 200,
    "bytes": 537
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1109/TPAMI.2020.2992889",
    "at": "2026-10-19T03:31:16+09:00",
    "status": 200,
    "bytes": 73
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/TPAMI.2020.2992889",
    "at": "2026-10-19T03:31:16+09:00",
    "status": 200,
    "bytes": 11027
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1016/j.media.2026.103945",
    "at": "2026-10-19T03:31:17+09:00",
    "status": 200,
    "bytes": 732
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1016/j.media.2026.103945",
    "at": "2026-10-19T03:31:18+09:00",
    "status": 200,
    "bytes": 74
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1016/j.media.2026.103945",
    "at": "2026-10-19T03:31:18+09:00",
    "status": 200,
    "bytes": 45955
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1007/s11548-024-03063-9",
    "at": "2026-10-19T03:31:19+09:00",
    "status": 200,
    "bytes": 544
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1007/s11548-024-03063-9",
    "at": "2026-10-19T03:31:20+09:00",
    "status": 200,
    "bytes": 73
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1007/s11548-024-03063-9",
    "at": "2026-10-19T03:31:20+09:00",
    "status": 200,
    "bytes": 27198
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/WACV57701.2024.00641",
    "at": "2026-10-19T03:31:21+09:00",
    "status": 200,
    "bytes": 541
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1109/WACV57701.2024.00641",
    "at": "2026-10-19T03:31:22+09:00",
    "status": 200,
    "bytes": 75
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/WACV57701.2024.00641",
    "at": "2026-10-19T03:31:22+09:00",
    "status": 200,
    "bytes": 8925
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/TPAMI.2021.3055233",
    "at": "2026-10-19T03:31:23+09:00",
    "status": 200,
    "bytes": 537
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1109/TPAMI.2021.3055233",
    "at": "2026-10-19T03:31:24+09:00",
    "status": 200,
    "bytes": 73
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/TPAMI.2021.3055233",
    "at": "2026-10-19T03:31:24+09:00",
    "status": 200,
    "bytes": 9540
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1515/cdbme-2020-0037",
    "at": "2026-10-19T03:31:25+09:00",
    "status": 200,
    "bytes": 558
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1515/cdbme-2020-0037",
    "at": "2026-10-19T03:31:26+09:00",
    "status": 200,
    "bytes": 70
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1515/cdbme-2020-0037",
    "at": "2026-10-19T03:31:26+09:00",
    "status": 200,
    "bytes": 9329
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1007/978-3-030-00937-3_31",
    "at": "2026-10-19T03:31:27+09:00",
    "status": 200,
    "bytes": 548
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1007/978-3-030-00937-3_31",
    "at": "2026-10-19T03:31:28+09:00",
    "status": 200,
    "bytes": 75
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1007/978-3-030-00937-3_31",
    "at": "2026-10-19T03:31:28+09:00",
    "status": 200,
    "bytes": 11522
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1007/978-3-031-18814-5_2",
    "at": "2026-10-19T03:31:29+09:00",
    "status": 200,
    "bytes": 546
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1007/978-3-031-18814-5_2",
    "at": "2026-10-19T03:31:30+09:00",
    "status": 200,
    "bytes": 74
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1007/978-3-031-18814-5_2",
    "at": "2026-10-19T03:31:30+09:00",
    "status": 200,
    "bytes": 19378
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1109/TMM.2025.3543033",
    "at": "2026-10-19T03:31:31+09:00",
    "status": 200,
    "bytes": 537
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1109/TMM.2025.3543033",
    "at": "2026-10-19T03:31:32+09:00",
    "status": 200,
    "bytes": 71
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1109/TMM.2025.3543033",
    "at": "2026-10-19T03:31:32+09:00",
    "status": 200,
    "bytes": 10768
  },
  {
    "service": "arxiv",
    "url": "https://export.arxiv.org/api/query?id_list=1602.03012,2405.19644,2005.02190,1912.09930,2110.06915,2308.07918,2006.03201,2311.00180,2304.03959,2605.20901,2607.08514,2507.16559,2408.03867,1709.07871,2102.00649,1807.10565,2410.20026,2306.11726,2404.11903&max_results=19",
    "at": "2026-10-19T03:31:32+09:00",
    "status": 200,
    "bytes": 50983
  }
]
```
### 地図 B

```json
{
  "before_total": 34,
  "before_counts": {
    "実在・書誌一致": 29,
    "実在・書誌に差": 5,
    "実在・照合不能": 0,
    "不在": 0,
    "到達不能": 0
  },
  "before_ids": [
    [
      "arxiv",
      "1602.03012"
    ],
    [
      "arxiv",
      "1610.08844"
    ],
    [
      "arxiv",
      "1610.08851"
    ],
    [
      "arxiv",
      "1706.07581"
    ],
    [
      "arxiv",
      "1709.07871"
    ],
    [
      "arxiv",
      "1711.05471"
    ],
    [
      "arxiv",
      "1807.00119"
    ],
    [
      "arxiv",
      "1904.03000"
    ],
    [
      "arxiv",
      "1905.07553"
    ],
    [
      "arxiv",
      "1907.06099"
    ],
    [
      "arxiv",
      "1907.06390"
    ],
    [
      "arxiv",
      "1912.03538"
    ],
    [
      "arxiv",
      "2001.03152"
    ],
    [
      "arxiv",
      "2104.12763"
    ],
    [
      "arxiv",
      "2104.13582"
    ],
    [
      "arxiv",
      "2108.06152"
    ],
    [
      "arxiv",
      "2112.02244"
    ],
    [
      "arxiv",
      "2112.03857"
    ],
    [
      "arxiv",
      "2112.10003"
    ],
    [
      "arxiv",
      "2207.10433"
    ],
    [
      "arxiv",
      "2210.10775"
    ],
    [
      "arxiv",
      "2210.15518"
    ],
    [
      "arxiv",
      "2303.05499"
    ],
    [
      "arxiv",
      "2303.17144"
    ],
    [
      "arxiv",
      "2405.19644"
    ],
    [
      "arxiv",
      "2406.03095"
    ],
    [
      "arxiv",
      "2407.07402"
    ],
    [
      "arxiv",
      "2411.16794"
    ],
    [
      "arxiv",
      "2503.18755"
    ],
    [
      "arxiv",
      "2602.06474"
    ],
    [
      "doi",
      "10.1007/978-3-031-72684-2_13"
    ],
    [
      "doi",
      "10.1007/978-3-032-05114-1_43"
    ],
    [
      "doi",
      "10.1016/j.neuroimage.2017.06.061"
    ],
    [
      "doi",
      "10.24963/ijcai.2023/90"
    ]
  ],
  "after_ids": [
    [
      "arxiv",
      "1602.03012"
    ],
    [
      "arxiv",
      "1610.08851"
    ],
    [
      "arxiv",
      "1706.07581"
    ],
    [
      "arxiv",
      "1709.07871"
    ],
    [
      "arxiv",
      "1711.05471"
    ],
    [
      "arxiv",
      "1807.00119"
    ],
    [
      "arxiv",
      "1904.03000"
    ],
    [
      "arxiv",
      "1905.07553"
    ],
    [
      "arxiv",
      "1907.06099"
    ],
    [
      "arxiv",
      "1907.06390"
    ],
    [
      "arxiv",
      "1912.03538"
    ],
    [
      "arxiv",
      "2001.03152"
    ],
    [
      "arxiv",
      "2104.12763"
    ],
    [
      "arxiv",
      "2104.13582"
    ],
    [
      "arxiv",
      "2108.06152"
    ],
    [
      "arxiv",
      "2112.02244"
    ],
    [
      "arxiv",
      "2112.03857"
    ],
    [
      "arxiv",
      "2112.10003"
    ],
    [
      "arxiv",
      "2207.10433"
    ],
    [
      "arxiv",
      "2210.10775"
    ],
    [
      "arxiv",
      "2210.15518"
    ],
    [
      "arxiv",
      "2303.05499"
    ],
    [
      "arxiv",
      "2303.17144"
    ],
    [
      "arxiv",
      "2309.01093"
    ],
    [
      "arxiv",
      "2405.19644"
    ],
    [
      "arxiv",
      "2406.03095"
    ],
    [
      "arxiv",
      "2407.07402"
    ],
    [
      "arxiv",
      "2411.16794"
    ],
    [
      "arxiv",
      "2503.18755"
    ],
    [
      "arxiv",
      "2602.06474"
    ],
    [
      "doi",
      "10.1007/978-3-031-72684-2_13"
    ],
    [
      "doi",
      "10.1007/978-3-032-05114-1_43"
    ],
    [
      "doi",
      "10.1016/j.neuroimage.2017.06.061"
    ],
    [
      "doi",
      "10.24963/ijcai.2023/90"
    ]
  ],
  "removed": [
    [
      "arxiv",
      "1610.08844"
    ]
  ],
  "added": [
    [
      "arxiv",
      "2309.01093"
    ]
  ],
  "counts": {
    "実在・書誌一致": 34,
    "実在・書誌に差": 0,
    "実在・照合不能": 0,
    "不在": 0,
    "到達不能": 0
  },
  "predicted_match": 34,
  "prediction_differences": [],
  "new_ids": [
    {
      "kind": "arxiv",
      "id": "2309.01093",
      "lines": [
        37,
        86
      ],
      "registry": "arXiv",
      "reference": {
        "title": "CoTDet: Affordance Knowledge Prompting for Task Driven Object Detection",
        "authors": [
          "Jiajin Tang",
          "Ge Zheng",
          "Jingyi Yu",
          "Sibei Yang"
        ],
        "year": "2023",
        "venue": null,
        "extra": {
          "comment": "Accepted by ICCV 2023"
        }
      },
      "map_row": {
        "row_id": "B-18",
        "line": 86,
        "literature": "Jiajin Tang, Ge Zheng, Jingyi Yu, Sibei Yang 2023, CoTDet: Affordance Knowledge Prompting for Task Driven Object Detection",
        "venue": "ICCV 2023（査読）",
        "id_text": "arXiv 2309.01093（起票者が 2026-10-19 に web 検索で特定。報告は ID を確定できなかった）"
      },
      "other_rows": [],
      "title": {
        "result": "一致",
        "detail": "全体",
        "map": "CoTDet: Affordance Knowledge Prompting for Task Driven Object Detection"
      },
      "authors": {
        "result": "一致",
        "detail": "全 4 名",
        "map": [
          "Jiajin Tang",
          "Ge Zheng",
          "Jingyi Yu",
          "Sibei Yang"
        ],
        "et_al": false
      },
      "venue": {
        "reference": null,
        "map": "ICCV 2023（査読）"
      },
      "note": "",
      "class": "実在・書誌一致"
    }
  ],
  "n_rows": [],
  "rows_without_id": []
}
```

問い合わせ実測（応答の抽出済み全書誌は verification/2026-10-18-B-p2d-interface.json の results[].reference）：

```json
[
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1007/978-3-032-05114-1_43",
    "at": "2026-10-19T03:31:33+09:00",
    "status": 200,
    "bytes": 548
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1007/978-3-032-05114-1_43",
    "at": "2026-10-19T03:31:34+09:00",
    "status": 200,
    "bytes": 75
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1007/978-3-032-05114-1_43",
    "at": "2026-10-19T03:31:34+09:00",
    "status": 200,
    "bytes": 14455
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1007/978-3-031-72684-2_13",
    "at": "2026-10-19T03:31:35+09:00",
    "status": 200,
    "bytes": 548
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1007/978-3-031-72684-2_13",
    "at": "2026-10-19T03:31:36+09:00",
    "status": 200,
    "bytes": 75
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1007/978-3-031-72684-2_13",
    "at": "2026-10-19T03:31:36+09:00",
    "status": 200,
    "bytes": 30424
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.24963/ijcai.2023/90",
    "at": "2026-10-19T03:31:37+09:00",
    "status": 200,
    "bytes": 527
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.24963/ijcai.2023/90",
    "at": "2026-10-19T03:31:38+09:00",
    "status": 200,
    "bytes": 69
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.24963/ijcai.2023/90",
    "at": "2026-10-19T03:31:38+09:00",
    "status": 200,
    "bytes": 4456
  },
  {
    "service": "doi",
    "url": "https://doi.org/api/handles/10.1016/j.neuroimage.2017.06.061",
    "at": "2026-10-19T03:31:39+09:00",
    "status": 200,
    "bytes": 737
  },
  {
    "service": "doi",
    "url": "https://doi.org/doiRA/10.1016/j.neuroimage.2017.06.061",
    "at": "2026-10-19T03:31:40+09:00",
    "status": 200,
    "bytes": 79
  },
  {
    "service": "crossref",
    "url": "https://api.crossref.org/works/10.1016/j.neuroimage.2017.06.061",
    "at": "2026-10-19T03:31:40+09:00",
    "status": 200,
    "bytes": 19882
  },
  {
    "service": "arxiv",
    "url": "https://export.arxiv.org/api/query?id_list=2309.01093,1602.03012,1610.08851,1907.06099,1709.07871,2112.02244,2112.10003,2104.12763,1905.07553,1912.03538,1907.06390,1807.00119,2406.03095,2405.19644,2503.18755,2411.16794,1904.03000,2210.10775,2303.05499,2112.03857,2108.06152,2407.07402,2207.10433,2210.15518,2303.17144,1711.05471,2001.03152,2104.13582,2602.06474,1706.07581&max_results=30",
    "at": "2026-10-19T03:31:41+09:00",
    "status": 200,
    "bytes": 72262
  }
]
```
無変更確認: docs/evidence/reports/B-chatgpt.md sha256=ef94ea71aba1b5e81dea60ae0b55581dfdfda7cf290fe29d56dcb20b7bc33dd9 一致

無変更確認: docs/evidence/reports/N1-novelty-search-result.md sha256=9e1dc1b7f9ad99faff469fa7aa001bfc586d98876677c52c2c1c1dcd83cfa3cd 一致

無変更確認: docs/evidence/reports/R1-deep-research-report.md sha256=1f95517bf4ce63015d9574ee7e3616859021882a7014feb4f261d76d9c49dce5 一致

無変更確認: docs/evidence/reports/deep-research-report-B2.md sha256=c7aad1c222d9159c1209a557f765e0400f85a3b6ccd8d92025683a2ce8102116 一致

無変更確認: docs/evidence/reports/deep-research-report-C2.md sha256=5d3c3ed514551cf11d1b75dcc8b6542b7fb5efefeedb91956a5d561284c141fd 一致

無変更確認: docs/evidence/2026-09-16-A-phase-tower-candidates.md sha256=9f723e4b17825b0854930b9a31c92fbf26cb298c20c0d4f133ff8883dfacddf0 一致

無変更確認: docs/evidence/2026-09-16-B-p2d-interface.md sha256=5aab3910cd8e4c04f77f795b8fc3d3930f0751e2a810da541568b53f6bbbad2d 一致

無変更確認: docs/evidence/README.md sha256=35a8922aa6f161bf383fe2eb443cef5aec20318312ddf8b52519c0ddedcdf11c 一致

無変更確認: docs/evidence/_template.md sha256=69e95ea37106fac90b463eabde7879cfc60df1575ffabdd10223f1c9f5b61376 一致

無変更確認: tasks/T-2026-10-19-evidence-maps-revise/SPEC.md sha256=fd8b3dbea0d7546892405316f6ac53e0b4456c92fc2b876ca2008fd93502ea22 一致


## D 初回検証

make forbidden-check: exit 0、status=pass、violations=[]。make spec-check TASK=T-2026-10-19-evidence-maps-revise: exit 0、rules_checked=9、hits=0。git diff --check: exit 0。pytestは契約の指定により未実行（testsの0は実行件数ではない）。

## 利用者の判断（2026-10-19T03:53:16+09:00）

利用者の回答: 1。tasks/inbox.d/T-2026-10-19-evidence-maps-revise.md 一件の追加を許可。契約の変更範囲に対する承認済み例外として記録した。

## D 最終変更範囲・要約値

git status --porcelain --untracked-files=all の経路集合を、地図3件・照合結果6件・本契約内・許可されたinbox.d一件と照合し、余分なし。

```
docs/evidence/2026-10-18-B-p2d-interface.md
docs/evidence/2026-10-18-C-d2p-interface.md
docs/evidence/2026-10-18-N-novelty.md
docs/evidence/verification/2026-10-18-B-p2d-interface.json
docs/evidence/verification/2026-10-18-B-p2d-interface.md
docs/evidence/verification/2026-10-18-C-d2p-interface.json
docs/evidence/verification/2026-10-18-C-d2p-interface.md
docs/evidence/verification/2026-10-18-N-novelty.json
docs/evidence/verification/2026-10-18-N-novelty.md
tasks/T-2026-10-19-evidence-maps-revise/RESULT.md
tasks/T-2026-10-19-evidence-maps-revise/SPEC.md
tasks/T-2026-10-19-evidence-maps-revise/audit.md
tasks/T-2026-10-19-evidence-maps-revise/baseline.json
tasks/T-2026-10-19-evidence-maps-revise/comparison.json
tasks/T-2026-10-19-evidence-maps-revise/maps-2026-10-19.patch
tasks/T-2026-10-19-evidence-maps-revise/positive-controls.json
tasks/T-2026-10-19-evidence-maps-revise/reachability.json
tasks/T-2026-10-19-evidence-maps-revise/result.yaml
tasks/T-2026-10-19-evidence-maps-revise/spec.yaml
tasks/inbox.d/T-2026-10-19-evidence-maps-revise.md
```
無変更: docs/evidence/reports/B-chatgpt.md ef94ea71aba1b5e81dea60ae0b55581dfdfda7cf290fe29d56dcb20b7bc33dd9

無変更: docs/evidence/reports/N1-novelty-search-result.md 9e1dc1b7f9ad99faff469fa7aa001bfc586d98876677c52c2c1c1dcd83cfa3cd

無変更: docs/evidence/reports/R1-deep-research-report.md 1f95517bf4ce63015d9574ee7e3616859021882a7014feb4f261d76d9c49dce5

無変更: docs/evidence/reports/deep-research-report-B2.md c7aad1c222d9159c1209a557f765e0400f85a3b6ccd8d92025683a2ce8102116

無変更: docs/evidence/reports/deep-research-report-C2.md 5d3c3ed514551cf11d1b75dcc8b6542b7fb5efefeedb91956a5d561284c141fd

無変更: docs/evidence/2026-09-16-A-phase-tower-candidates.md 9f723e4b17825b0854930b9a31c92fbf26cb298c20c0d4f133ff8883dfacddf0

無変更: docs/evidence/2026-09-16-B-p2d-interface.md 5aab3910cd8e4c04f77f795b8fc3d3930f0751e2a810da541568b53f6bbbad2d

無変更: docs/evidence/README.md 35a8922aa6f161bf383fe2eb443cef5aec20318312ddf8b52519c0ddedcdf11c

無変更: docs/evidence/_template.md 69e95ea37106fac90b463eabde7879cfc60df1575ffabdd10223f1c9f5b61376

無変更: tasks/T-2026-10-19-evidence-maps-revise/SPEC.md fd8b3dbea0d7546892405316f6ac53e0b4456c92fc2b876ca2008fd93502ea22


### D 最終検証の結果

make task-validate TASK=T-2026-10-19-evidence-maps-revise: exit 0、OK、1 task(s), 0 failed。
make forbidden-check: exit 0、changed=20、checked=20、status=pass、violations=[]。
make spec-check TASK=T-2026-10-19-evidence-maps-revise: exit 0、rules_checked=9、hits=0、findings=[]。
git diff --check: exit 0、出力なし。

## D 版管理・PR

初回 commit: d8c2c265cdfcdeb2ccec5cd4a7f9616dcaf02d6a。git push -u origin feat/evidence-maps-revise: exit 0。
gh pr create --base phase0 --head feat/evidence-maps-revise --title <題名> --body-file /tmp/evidence-maps-revise-pr.md: exit 0。
gh pr view feat/evidence-maps-revise --json number,url,baseRefName,headRefName,isDraft,state: exit 0、応答:

```json
{
  "baseRefName": "phase0",
  "headRefName": "feat/evidence-maps-revise",
  "isDraft": false,
  "number": 233,
  "state": "OPEN",
  "url": "https://github.com/takuya3h/m2/pull/233"
}
```

## D 台帳送出

命令: source .venv/bin/activate && source scripts/load_env.sh && make task-report TASK=T-2026-10-19-evidence-maps-revise

exit=0。資格情報の値は出力しない。秘匿検査を経て送信。応答:

```json
{
  "task_id": "T-2026-10-19-evidence-maps-revise",
  "verdict": "pass",
  "n_issuer_defects": 1,
  "report_sha256": "8374fb7b542b5a1aed022e427d56c913fd30d0f4a9f6be045b69fe47da28ff12",
  "report_bytes": 6981,
  "replaced_blocks": 0
}
```

送出した RESULT.md の SHA-256 は上記と一致（送出後も本文を変更していない）。同期抑止解除は全 commit・push の後に task-release で行い、結果は最終応答に残す。

最終の origin/phase0 との差分経路集合（承認済みの範囲のみ、20件）:

```
docs/evidence/2026-10-18-B-p2d-interface.md
docs/evidence/2026-10-18-C-d2p-interface.md
docs/evidence/2026-10-18-N-novelty.md
docs/evidence/verification/2026-10-18-B-p2d-interface.json
docs/evidence/verification/2026-10-18-B-p2d-interface.md
docs/evidence/verification/2026-10-18-C-d2p-interface.json
docs/evidence/verification/2026-10-18-C-d2p-interface.md
docs/evidence/verification/2026-10-18-N-novelty.json
docs/evidence/verification/2026-10-18-N-novelty.md
tasks/T-2026-10-19-evidence-maps-revise/RESULT.md
tasks/T-2026-10-19-evidence-maps-revise/SPEC.md
tasks/T-2026-10-19-evidence-maps-revise/audit.md
tasks/T-2026-10-19-evidence-maps-revise/baseline.json
tasks/T-2026-10-19-evidence-maps-revise/comparison.json
tasks/T-2026-10-19-evidence-maps-revise/maps-2026-10-19.patch
tasks/T-2026-10-19-evidence-maps-revise/positive-controls.json
tasks/T-2026-10-19-evidence-maps-revise/reachability.json
tasks/T-2026-10-19-evidence-maps-revise/result.yaml
tasks/T-2026-10-19-evidence-maps-revise/spec.yaml
tasks/inbox.d/T-2026-10-19-evidence-maps-revise.md
```

変えない九件と SPEC.md の SHA-256 は baseline.json とすべて一致。
