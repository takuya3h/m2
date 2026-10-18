"""証拠地図の照合器の試験。**ネットワークに依存しない**（HTTP は差し替える）。

判定が通ったことは、判定が働いていることを意味しない。「常に実在と返す」壊れ方と
区別するため、対照は両方向に置く（実在するはずの ID と、不在・到達不能になるはずの ID）。
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import verify_evidence_ids as v  # noqa: E402


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """実際の通信の口を塞ぐ。差し替え忘れがあればここで落ちる。"""

    def _refuse(*_args, **_kwargs):
        raise AssertionError("試験がネットワークへ出ようとした")

    monkeypatch.setattr(urllib.request, "urlopen", _refuse)


CROSSREF_DOI = "10.1109/TMI.2016.2593957"
DATACITE_DOI = "10.5281/zenodo.20086606"
ARXIV_ID = "1602.03012"
FAKE_DOI = "10.1109/egosurgery.nonexistent.2026"
FAKE_ARXIV = "2601.99999"


def _atom(entries: list[tuple[str, str, list[str]]]) -> bytes:
    body = "".join(
        f"<entry><id>http://arxiv.org/abs/{i}v2</id><title>{t}</title>"
        + "".join(f"<author><name>{a}</name></author>" for a in authors)
        + "<published>2016-02-09T00:00:00Z</published></entry>"
        for i, t, authors in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">'
        f"{body}</feed>"
    ).encode()


ENDONET = "EndoNet: A Deep Architecture for Recognition Tasks on Laparoscopic Videos"
TWINANDA = ["Andru P. Twinanda", "Sherif Shehata", "Didier Mutter"]


def fake_service(url: str) -> tuple[int, bytes]:
    """照合先の振る舞いの写し。応答の形は 2026-10-19 に実際の照合先で測ったもの。"""
    if url.startswith("https://doi.org/api/handles/"):
        doi = url.rsplit("/api/handles/", 1)[1]
        if doi in (CROSSREF_DOI, DATACITE_DOI):
            return 200, json.dumps({"responseCode": 1, "handle": doi}).encode()
        return 404, json.dumps({"responseCode": 100, "handle": doi}).encode()
    if url.startswith("https://doi.org/doiRA/"):
        doi = url.rsplit("/doiRA/", 1)[1]
        ra = {CROSSREF_DOI: "Crossref", DATACITE_DOI: "DataCite"}.get(doi)
        return 200, json.dumps([{"DOI": doi, "RA": ra} if ra else {"DOI": doi, "status": "DOI does not exist"}]).encode()
    if url.startswith("https://api.crossref.org/works/"):
        return 200, json.dumps(
            {
                "message": {
                    "title": [ENDONET],
                    "author": [{"given": "Andru P.", "family": "Twinanda"}, {"given": "Sherif", "family": "Shehata"}],
                    "issued": {"date-parts": [[2017, 1]]},
                    "container-title": ["IEEE Transactions on Medical Imaging"],
                }
            }
        ).encode()
    if url.startswith("https://api.datacite.org/dois/"):
        return 200, json.dumps(
            {
                "data": {
                    "attributes": {
                        "titles": [{"title": "Automated Surgical Phase Recognition"}],
                        "creators": [{"name": "Schwarz, Graham", "givenName": "Graham", "familyName": "Schwarz"}],
                        "publicationYear": 2026,
                        "publisher": "Zenodo",
                        "url": "https://zenodo.org/doi/10.5281/zenodo.20086606",
                    }
                }
            }
        ).encode()
    if url.startswith("https://export.arxiv.org/api/query"):
        known = {ARXIV_ID: (ENDONET, TWINANDA)}
        ids = url.split("id_list=", 1)[1].split("&", 1)[0].split(",")
        return 200, _atom([(i, *known[i]) for i in ids if i in known])
    raise AssertionError(f"想定外の URL: {url}")


def _client(fetch=fake_service, **kwargs) -> v.Client:
    return v.Client(fetch=fetch, sleep=lambda _s: None, **kwargs)


MAP = f"""# 証拠地図 X — 試験

## 2. 行の一覧

| ID | 文献 | 書誌 ID | 掲載先 | 出所 |
|---|---|---|---|---|
| X-01 | Twinanda ほか, {ENDONET}（注記） | arXiv {ARXIV_ID}、DOI {CROSSREF_DOI} | IEEE TMI | L1 |
| X-02 | Graham Schwarz 2026, Automated Surgical Phase Recognition（抄録） | 報告は DOI {DATACITE_DOI} を挙げる | Zenodo | L2 |
| X-03 | （著者・題名は報告に無い）TD-Graph | なし | 不明 | L3 |
"""


# --- 抽出 ---------------------------------------------------------------------

def test_extract_keeps_doi_whole_and_skips_numbers_inside_it():
    found = v.extract_ids("DOI 10.1109/WACV57701.2024.00641（注記）と 10.1016/j.media.2026.103945、")
    assert [(f.kind, f.id) for f in found] == [
        ("doi", "10.1109/WACV57701.2024.00641"),
        ("doi", "10.1016/j.media.2026.103945"),
    ]


def test_extract_arxiv_with_version_url_and_trailing_punctuation():
    text = "arXiv 2405.19644v2、https://arxiv.org/abs/1709.07871。DOI 10.24963/ijcai.2023/90."
    found = v.extract_ids(text)
    assert [(f.kind, f.id) for f in found] == [
        ("arxiv", "2405.19644"),
        ("arxiv", "1709.07871"),
        ("doi", "10.24963/ijcai.2023/90"),
    ]


def test_extract_rejects_six_digit_suffix_and_letter_prefix():
    assert v.extract_ids("1602.030123 と cvpr42600.2020 と L2016.12345") == []


def test_extract_merges_repeats_and_keeps_every_line():
    found = v.extract_ids(f"{ARXIV_ID}\n本文\narXiv {ARXIV_ID}\nDOI {CROSSREF_DOI.lower()}\nDOI {CROSSREF_DOI}")
    assert [(f.id, f.lines) for f in found] == [(ARXIV_ID, [1, 3]), (CROSSREF_DOI.lower(), [4, 5])]


# --- 地図の側の書誌 -------------------------------------------------------------

def test_description_rows_need_literature_and_id_columns():
    rows = v.description_rows(MAP + "\n| 文献 | 地図の記載 |\n|---|---|\n| M2CAI | arXiv 1610.08844 |\n")
    assert [r.row_id for r in rows] == ["X-01", "X-02", "X-03"]
    assert rows[0].line == 7


@pytest.mark.parametrize(
    ("cell", "authors", "et_al", "year", "title"),
    [
        ("Ryo Fujii, Masashi Hatano 2024, EgoSurgery-Phase: A Dataset", ["Ryo Fujii", "Masashi Hatano"], False, "2024", "EgoSurgery-Phase: A Dataset"),
        ("Twinanda ほか, EndoNet: A Deep Architecture（C2 は既所持）", ["Twinanda"], True, None, "EndoNet: A Deep Architecture"),
        ("Li, Sun 2025（arXiv 2024）, Simultaneous Detection", ["Li", "Sun"], False, "2025", "Simultaneous Detection"),
        ("Ayobi ほか 2024／2025, Pixel-Wise Recognition", ["Ayobi"], True, "2024／2025", "Pixel-Wise Recognition"),
        ("（著者は報告に記載なし）2023, Helping Hands", None, False, "2023", "Helping Hands"),
        ("Shiota ほか 2024（題名は報告に無い）", ["Shiota"], True, "2024", None),
        ("TD-Graph LSTM（題名・著者は報告に無い）", None, False, None, None),
    ],
)
def test_parse_literature(cell, authors, et_al, year, title):
    bib = v.parse_literature(cell)
    assert (bib.authors, bib.et_al, bib.year, bib.title) == (authors, et_al, year, title)


# --- 正規化と比較（両側に同じ規則） -----------------------------------------------

@pytest.mark.parametrize(
    ("map_name", "family", "full"),
    [
        ("Lüddecke", "Luddecke", "Timo Luddecke"),
        ("Luddecke", "Lüddecke", "Timo Lüddecke"),
        ("Gaël Varoquaux", "Varoquaux", "Gael Varoquaux"),
        ("Abu Farha", "Farha", "Yazan Abu Farha"),
        ("Farha", "Abu Farha", "Yazan Abu Farha"),
        ("Yazan Abu Farha", "Abu Farha", "Yazan Abu Farha"),
        ("Mephu Nguifo", "Nguifo", "Engelbert Mephu Nguifo"),
    ],
)
def test_name_matches_after_normalizing_both_sides(map_name, family, full):
    assert v.name_matches(v.normalize(map_name), v.normalize(family), v.normalize(full))


def test_name_does_not_match_a_one_letter_extension():
    assert not v.name_matches(v.normalize("Lin"), v.normalize("Li"), v.normalize("Wei Li"))


def test_title_full_partial_and_different():
    assert v.compare_title("Endonet: a deep ARCHITECTURE for recognition tasks on laparoscopic videos", [ENDONET])[0] == "一致"
    assert v.compare_title("EndoNet", [ENDONET]) == ("一致", "部分（地図の題名が照合先の題名の一部）")
    assert v.compare_title("Helping Hands", [ENDONET])[0] == "差"
    assert v.compare_title(None, [ENDONET])[0] is None


def test_authors_without_et_al_must_cover_both_lists():
    bib = v.MapBib(["Twinanda"], False, None, None)
    result, detail = v.compare_authors(bib, [("Twinanda", "Andru Twinanda"), ("Shehata", "Sherif Shehata")])
    assert result == "差" and "Sherif Shehata" in detail
    bib_etal = v.MapBib(["Twinanda"], True, None, None)
    assert v.compare_authors(bib_etal, [("Twinanda", "Andru Twinanda"), ("Shehata", "Sherif Shehata")])[0] == "一致"
    assert v.compare_authors(v.MapBib(["Shehata"], True, None, None), [("Twinanda", "A T"), ("Shehata", "S S")])[0] == "差"


# --- 対照（両方向） -------------------------------------------------------------

def _by_id(report):
    return {r["id"]: r for r in report["results"]}


def test_controls_exist_absent_and_registry():
    text = MAP + f"\n架空: DOI {FAKE_DOI}、arXiv {FAKE_ARXIV}\n"
    report = v.verify(text, _client())
    got = _by_id(report)
    assert got[CROSSREF_DOI]["class"] == v.MATCH and got[CROSSREF_DOI]["registry"] == "Crossref"
    assert got[ARXIV_ID]["class"] == v.MATCH and got[ARXIV_ID]["registry"] == "arXiv"
    # DataCite の DOI は Crossref に無いが不在ではない（環境の罠の三）
    assert got[DATACITE_DOI]["class"] == v.MATCH and got[DATACITE_DOI]["registry"] == "DataCite"
    assert got[FAKE_DOI]["class"] == v.ABSENT
    assert got[FAKE_ARXIV]["class"] == v.ABSENT
    assert sum(report["counts"].values()) == report["total_ids"] == 5
    assert report["rows_without_id"] == ["X-03"]


def test_unreachable_is_not_absent():
    def down(url):
        raise v.Unreachable("ConnectionRefusedError: [Errno 111] Connection refused")

    report = v.verify(MAP + f"\n{FAKE_DOI} {FAKE_ARXIV}\n", _client(fetch=down))
    assert {r["class"] for r in report["results"]} == {v.UNREACHABLE}
    assert report["counts"][v.ABSENT] == 0


def test_persistent_429_becomes_unreachable_after_backing_off():
    waits: list[float] = []
    calls: list[str] = []

    def busy(url):
        calls.append(url)
        return 429, b"Rate exceeded."

    client = v.Client(fetch=busy, sleep=waits.append)
    result = v.resolve_arxiv(client, [ARXIV_ID])
    assert result[ARXIV_ID].status == v.UNREACHABLE
    assert len(calls) == 1 + len(v.RETRY_WAITS)
    assert [w for w in waits if w in v.RETRY_WAITS] == list(v.RETRY_WAITS)


def test_adding_a_fake_id_adds_exactly_one_absent():
    base = v.verify(MAP, _client())["counts"]
    more = v.verify(MAP + f"\narXiv {FAKE_ARXIV}\n", _client())["counts"]
    assert more[v.ABSENT] == base[v.ABSENT] + 1
    assert {k: more[k] for k in v.CLASSES if k != v.ABSENT} == {k: base[k] for k in v.CLASSES if k != v.ABSENT}


def test_title_difference_is_reported_as_diff():
    text = MAP.replace(ENDONET + "（注記）", "Something Else Entirely（注記）")
    got = _by_id(v.verify(text, _client()))
    assert got[ARXIV_ID]["class"] == v.DIFF
    assert got[ARXIV_ID]["map_row"]["row_id"] == "X-01"


def test_id_without_a_description_row_is_uncomparable():
    got = _by_id(v.verify(f"本文だけに出る arXiv {ARXIV_ID}\n", _client()))
    assert got[ARXIV_ID]["class"] == v.UNCOMPARABLE
    assert got[ARXIV_ID]["reference"]["title"] == ENDONET


def test_pacing_waits_between_arxiv_requests():
    now = [0.0]
    waits: list[float] = []

    def sleep(seconds):
        waits.append(seconds)
        now[0] += seconds

    client = v.Client(fetch=fake_service, sleep=sleep, clock=lambda: now[0])
    client.get("arxiv", f"/api/query?id_list={ARXIV_ID}")
    client.get("arxiv", f"/api/query?id_list={ARXIV_ID}")
    assert waits == [pytest.approx(v.MIN_INTERVAL["arxiv"])]


def test_user_agent_has_no_contact():
    assert "@" not in v.USER_AGENT and "mailto" not in v.USER_AGENT


# --- 命令 -----------------------------------------------------------------------

def test_main_writes_json_and_markdown_and_exit_code(tmp_path, monkeypatch):
    map_path = tmp_path / "2026-10-18-X-test.md"
    map_path.write_text(MAP + f"\nDOI {FAKE_DOI}\n", encoding="utf-8")
    real = v.Client
    monkeypatch.setattr(v, "Client", lambda endpoints=None: real(fetch=fake_service, sleep=lambda _s: None, endpoints=endpoints))
    code = v.main([str(map_path), "--out-dir", str(tmp_path / "out")])
    assert code == 1  # 不在が一件ある
    report = json.loads((tmp_path / "out" / "2026-10-18-X-test.json").read_text(encoding="utf-8"))
    assert report["counts"][v.ABSENT] == 1
    assert "## 分類ごとの件数" in (tmp_path / "out" / "2026-10-18-X-test.md").read_text(encoding="utf-8")


def test_exit_code_prefers_unreachable():
    counts = {name: 0 for name in v.CLASSES}
    assert v.exit_code(counts) == 0
    assert v.exit_code({**counts, v.ABSENT: 1}) == 1
    assert v.exit_code({**counts, v.ABSENT: 1, v.UNREACHABLE: 1}) == 3


def test_extract_only_needs_no_network(tmp_path, capsys):
    map_path = tmp_path / "m.md"
    map_path.write_text(MAP, encoding="utf-8")
    assert v.main([str(map_path), "--extract-only"]) == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert lines == [f"m.md\tarxiv\t{ARXIV_ID}", f"m.md\tdoi\t{CROSSREF_DOI}", f"m.md\tdoi\t{DATACITE_DOI}"]
