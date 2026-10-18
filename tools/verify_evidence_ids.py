#!/usr/bin/env python3
"""証拠地図の書誌 ID（DOI と arXiv ID）を照合先に問い合わせ、ID ごとに分類する。

F 2026-10-03 の分担（起票者が地図を起こし、機械で照合し、利用者が原典を確かめる）の
「機械で照合」を一つの命令にしたもの。**契約ごとに照合器を作らない。**

    python tools/verify_evidence_ids.py docs/evidence/<地図>.md
    make evidence-verify MAP=docs/evidence/<地図>.md

結果は docs/evidence/verification/<地図の名前>.json（機械が読む形）と .md（人が読む要約）に
書く。**地図の本文は書き換えない。** 照合で分かった差をどう地図へ反映するかは起票者が決める。

分類は五つ。判定の規則は docs/evidence/README.md に書いた。

    実在・書誌一致 / 実在・書誌に差 / 実在・照合不能 / 不在 / 到達不能

**届かなかった ID を不在と呼ばない。** 照合先が「無い」と答えたときだけ不在とする。
DOI の実在は登録機関によらず doi.org の handle で確かめる。Crossref だけを引くと、
DataCite に登録された DOI（Zenodo など）を不在と誤るためである。

問い合わせの作法（各サービスの文書に従う）:

- 連絡先（メールアドレスなど）を問い合わせに入れない（利用者の決定 2026-10-19）
- arXiv の API は 3 秒に 1 回・接続 1 本。一つの地図の arXiv ID は id_list にまとめて引く
- Crossref の公開の枠は 5 件／秒・同時 1 本。本器は照合先ごとに間隔をあけて逐次に引く
- 429 と 5xx は間隔を延ばして引き直す。通信の失敗は一度だけ引き直す。尽きたら到達不能

終了コード:

    0  不在も到達不能も無い
    1  不在が一件以上ある（到達不能は無い）
    2  使い方の誤り・地図が読めない
    3  到達不能が一件以上ある
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "docs" / "evidence" / "verification"

# 照合器を名乗るだけで、連絡先は入れない（決定 4）。
USER_AGENT = "egosurgery-evidence-verify/1.0"
ENDPOINTS = {
    "doi": "https://doi.org",
    "crossref": "https://api.crossref.org",
    "datacite": "https://api.datacite.org",
    "arxiv": "https://export.arxiv.org",
}
# 照合先ごとの最小の間隔（秒）。arXiv は利用規約の 3 秒に余裕を足した。
MIN_INTERVAL = {"doi": 1.0, "crossref": 1.0, "datacite": 1.0, "arxiv": 3.1}
# 429・5xx のときの待ち（秒）。arXiv は Retry-After を返さないため固定の段で延ばす。
# 実測（2026-10-19）: arXiv の 429 は 4 分あけても続き、10 分あけると戻った。
RETRY_WAITS = (10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
# 接続できないときの待ち。届かない照合先で長く待たないよう一度だけにする。
CONNECT_RETRY_WAITS = (5.0,)
TIMEOUT = 30.0
ARXIV_BATCH = 50

MATCH = "実在・書誌一致"
DIFF = "実在・書誌に差"
UNCOMPARABLE = "実在・照合不能"
ABSENT = "不在"
UNREACHABLE = "到達不能"
CLASSES = (MATCH, DIFF, UNCOMPARABLE, ABSENT, UNREACHABLE)

JST = timezone(timedelta(hours=9))

# --- 抽出 -------------------------------------------------------------------

# DOI は 10. で始まり、空白・全角の括弧・読点・句点の前で切る（起票者の一覧 expected-ids.txt の
# 抽出の規則）。表の区切りとバッククォートの前でも切る。末尾の ASCII の句読点は外す。
_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s（）、。|`]+")
# arXiv は新形式（4 桁.4〜5 桁）だけ。前が英数字・下線・点、後ろが数字なら ID ではない。
# DOI の内側の数字列（10.1109/TMI.2016.2593957 の 2016.25939 など）は範囲の重なりでも落とす。
_ARXIV_RE = re.compile(r"(?<![A-Za-z0-9_.])(\d{4}\.\d{4,5})(?:v\d+)?(?!\d)")


@dataclass
class FoundId:
    kind: str  # "doi" または "arxiv"
    id: str  # 最初に書かれた形。DOI の大文字小文字は保つ
    lines: list[int] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, str]:
        # DOI は大文字小文字を区別しない（DOI Handbook）。arXiv ID は数字だけ
        return (self.kind, self.id.lower())


def _trim_doi(raw: str) -> str:
    doi = raw
    while True:
        before = doi
        doi = doi.rstrip(".,;:")
        if doi.endswith(")") and doi.count(")") > doi.count("("):
            doi = doi[:-1]
        if doi.endswith("]") and doi.count("]") > doi.count("["):
            doi = doi[:-1]
        if doi == before:
            return doi


def _ids_in(text: str) -> list[tuple[str, str, int, int]]:
    """(種別, ID, 始点, 終点) を出現順に返す。"""
    found: list[tuple[str, str, int, int]] = []
    spans: list[tuple[int, int]] = []
    for m in _DOI_RE.finditer(text):
        doi = _trim_doi(m.group(0))
        found.append(("doi", doi, m.start(), m.start() + len(doi)))
        spans.append((m.start(), m.end()))
    for m in _ARXIV_RE.finditer(text):
        if any(s <= m.start() < e for s, e in spans):
            continue
        found.append(("arxiv", m.group(1), m.start(), m.end()))
    return sorted(found, key=lambda item: item[2])


def extract_ids(text: str) -> list[FoundId]:
    """地図の本文から ID を抜き出す。**同じ ID は一つにまとめ、現れた行を全部残す。**"""
    by_key: dict[tuple[str, str], FoundId] = {}
    for lineno, line in enumerate(text.split("\n"), 1):
        for kind, ident, _s, _e in _ids_in(line):
            item = FoundId(kind, ident)
            existing = by_key.setdefault(item.key, item)
            if lineno not in existing.lines:
                existing.lines.append(lineno)
    return list(by_key.values())


# --- 地図の側の書誌 -----------------------------------------------------------


@dataclass
class Row:
    """「文献」の列と書誌 ID の列を持つ表の一行。"""

    row_id: str
    line: int
    literature: str
    venue: str
    id_text: str


_SEPARATOR_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def _cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip() for cell in body.split("|")]


def _is_id_column(header: str) -> bool:
    return "書誌 ID" in header or "DOI" in header or "arXiv" in header


def description_rows(text: str) -> list[Row]:
    """書誌の比較に使える行を返す。

    列の見出しに「ID」「文献」と書誌 ID の列（「書誌 ID」または DOI・arXiv を含む）を持つ表だけを
    対象にする。**注記や出所の欄に現れた別の文献の ID は、その行の文献の書誌とは比べない。**
    """
    lines = text.split("\n")
    rows: list[Row] = []
    i = 0
    while i < len(lines):
        if not (lines[i].lstrip().startswith("|") and i + 1 < len(lines) and _SEPARATOR_RE.match(lines[i + 1])):
            i += 1
            continue
        header = _cells(lines[i])
        lit = header.index("文献") if "文献" in header else None
        rid = header.index("ID") if "ID" in header else None
        venue = header.index("掲載先") if "掲載先" in header else None
        id_cols = [k for k, h in enumerate(header) if _is_id_column(h)]
        j = i + 2
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            cells = _cells(lines[j])
            if lit is not None and rid is not None and id_cols and len(cells) == len(header):
                rows.append(
                    Row(
                        row_id=cells[rid],
                        line=j + 1,
                        literature=cells[lit],
                        venue=cells[venue] if venue is not None else "",
                        id_text="　".join(cells[k] for k in id_cols),
                    )
                )
            j += 1
        i = j
    return rows


@dataclass
class MapBib:
    authors: list[str] | None
    et_al: bool
    year: str | None
    title: str | None


_PAREN_RE = re.compile(r"（[^（）]*）")
_YEAR = r"(?:19|20)\d{2}(?:\s*[–\-／/]\s*(?:19|20)?\d{2,4})?"
_ETAL_RE = re.compile(r"\s*(?:ほか|et al\.?)\s*$")
_BIB_ETAL_NO_YEAR = re.compile(r"^(?P<authors>[^,、]+?(?:ほか|et al\.?))\s*,\s*(?P<title>.+)$")
_BIB_WITH_YEAR = re.compile(rf"^(?P<authors>.*?)\s*(?<!\d)(?P<year>{_YEAR})(?!\d)\s*(?:,\s*(?P<title>.+))?$")


def parse_literature(cell: str) -> MapBib:
    """「著者 年, 題名（注記）」の形を読む。全角の括弧の中は注記として外す。

    読めない形（年も「ほか」も無い）は著者・題名とも無しとする。推測で埋めない。
    """
    plain = cell
    while True:
        stripped = _PAREN_RE.sub("", plain)
        if stripped == plain:
            break
        plain = stripped
    plain = plain.strip()
    m = _BIB_ETAL_NO_YEAR.match(plain)
    if m:
        authors_text, year, title = m["authors"], None, m["title"]
    else:
        m = _BIB_WITH_YEAR.match(plain)
        if not m:
            return MapBib(None, False, None, None)
        authors_text, year, title = m["authors"], m["year"], m["title"]
    et_al = bool(_ETAL_RE.search(authors_text))
    names = [n.strip() for n in re.split(r",|、|\band\b|&", _ETAL_RE.sub("", authors_text)) if n.strip()]
    title = title.strip() if title and title.strip() else None
    return MapBib(names or None, et_al, year, title)


# --- 正規化と比較 -------------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]+>")


def normalize(text: str) -> str:
    """両側に同じ規則を当てる。発音記号を外し、大文字小文字を揃え、英数字以外を除く。

    複合姓（Abu Farha）と発音記号（Lüddecke、Gaël）を片側だけ正規化すると差と誤る
    （前回の照合の誤検出。tasks/inbox.d/T-2026-09-16-evidence-map-ab.md）。
    """
    text = html.unescape(_TAG_RE.sub("", text))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).casefold()
    return "".join(c for c in text if c.isalnum())


def name_matches(map_name: str, family: str, full: str) -> bool:
    """地図の名前（正規化済み）が照合先の著者（姓・氏名とも正規化済み）に当たるか。

    地図は「姓」だけのことも「名 姓」のこともある。前後に二文字以上の余りがあるときだけ
    前方・後方一致を認める（Li と Lin を取り違えないため）。
    """
    if not map_name or not family:
        return False
    if map_name in (family, full):
        return True
    if len(map_name) - len(family) >= 2 and (map_name.startswith(family) or map_name.endswith(family)):
        return True
    return len(family) - len(map_name) >= 2 and family.endswith(map_name)


def compare_title(map_title: str | None, ref_titles: list[str]) -> tuple[str | None, str]:
    """(一致 / 差 / None, 説明)。None は比べられなかったことを表す。"""
    if not map_title:
        return None, "地図に題名なし"
    refs = [normalize(t) for t in ref_titles if t]
    if not refs:
        return None, "照合先に題名なし"
    m = normalize(map_title)
    if any(r and (m == r or r in m) for r in refs):
        return "一致", "全体"
    if len(m) >= 4 and any(m in r for r in refs):
        return "一致", "部分（地図の題名が照合先の題名の一部）"
    return "差", "題名が一致しない"


def compare_authors(bib: MapBib, ref_authors: list[tuple[str, str]]) -> tuple[str | None, str]:
    """(一致 / 差 / None, 説明)。ref_authors は (姓, 氏名) の並び。"""
    if not bib.authors:
        return None, "地図に著者なし"
    if not ref_authors:
        return None, "照合先に著者なし"
    mapped = [normalize(n) for n in bib.authors]
    refs = [(normalize(f), normalize(full)) for f, full in ref_authors]
    if bib.et_al:
        bad = [
            bib.authors[i]
            for i, m in enumerate(mapped)
            if i >= len(refs) or not name_matches(m, *refs[i])
        ]
        if bad:
            return "差", f"「ほか」の前の著者が照合先の同じ位置の著者と合わない: {', '.join(bad)}"
        return "一致", f"先頭 {len(mapped)} 名（ほか）"
    lost_map = [n for n, m in zip(bib.authors, mapped) if not any(name_matches(m, f, u) for f, u in refs)]
    lost_ref = [ref_authors[k][1] for k, (f, u) in enumerate(refs) if not any(name_matches(m, f, u) for m in mapped)]
    if lost_map or lost_ref:
        parts = []
        if lost_map:
            parts.append(f"照合先に無い地図の著者: {', '.join(lost_map)}")
        if lost_ref:
            parts.append(f"地図に無い照合先の著者: {', '.join(lost_ref)}")
        return "差", f"地図 {len(mapped)} 名・照合先 {len(refs)} 名。" + "。".join(parts)
    return "一致", f"全 {len(mapped)} 名"


# --- 問い合わせ ---------------------------------------------------------------


class Unreachable(Exception):
    """照合先から判定に使える応答を得られなかったことを示す。不在とは別に扱う。"""


def urllib_fetch(url: str, timeout: float = TIMEOUT) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise Unreachable(f"{type(exc).__name__}: {exc}") from exc


class Client:
    """照合先ごとに間隔をあけ、逐次に問い合わせる。応答の記録を残す。"""

    def __init__(
        self,
        fetch: Callable[[str], tuple[int, bytes]] = urllib_fetch,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        endpoints: dict[str, str] | None = None,
    ) -> None:
        self.fetch = fetch
        self.sleep = sleep
        self.clock = clock
        self.endpoints = {**ENDPOINTS, **(endpoints or {})}
        self.last: dict[str, float] = {}
        self.log: list[dict] = []

    def _pace(self, service: str) -> None:
        last = self.last.get(service)
        if last is not None:
            wait = MIN_INTERVAL.get(service, 1.0) - (self.clock() - last)
            if wait > 0:
                self.sleep(wait)
        self.last[service] = self.clock()

    def get(self, service: str, path: str) -> tuple[int, bytes]:
        url = self.endpoints[service].rstrip("/") + path
        http_waits, connect_waits = list(RETRY_WAITS), list(CONNECT_RETRY_WAITS)
        while True:
            self._pace(service)
            at = datetime.now(JST).isoformat(timespec="seconds")
            try:
                status, body = self.fetch(url)
            except Unreachable as exc:
                self.log.append({"service": service, "url": url, "at": at, "error": str(exc)})
                if not connect_waits:
                    raise Unreachable(f"{url}: {exc}") from exc
                self.sleep(connect_waits.pop(0))
                continue
            self.log.append({"service": service, "url": url, "at": at, "status": status, "bytes": len(body)})
            if status == 429 or status >= 500:
                if not http_waits:
                    raise Unreachable(f"{url}: HTTP {status}")
                self.sleep(http_waits.pop(0))
                continue
            return status, body


@dataclass
class Resolution:
    status: str  # "実在" / ABSENT / UNREACHABLE
    registry: str | None = None
    ref: dict | None = None
    note: str = ""


def _quote_doi(doi: str) -> str:
    return urllib.parse.quote(doi, safe="/")


def _crossref_ref(body: bytes) -> dict:
    msg = json.loads(body)["message"]
    titles = [t for t in (msg.get("title") or []) if t]
    subtitles = [t for t in (msg.get("subtitle") or []) if t]
    authors = []
    for a in msg.get("author") or []:
        family = a.get("family") or a.get("name") or ""
        full = " ".join(p for p in (a.get("given"), a.get("family")) if p) or a.get("name") or ""
        authors.append((family, full))
    year = None
    for key in ("issued", "published-print", "published-online", "created"):
        parts = (msg.get(key) or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            year = str(parts[0][0])
            break
    container = [t for t in (msg.get("container-title") or []) if t]
    return {
        "title": titles[0] if titles else None,
        "title_candidates": titles + [f"{t}: {s}" for t in titles[:1] for s in subtitles],
        "authors": authors,
        "year": year,
        "venue": container[0] if container else (msg.get("event") or {}).get("name") or msg.get("publisher"),
        "extra": {k: msg.get(k) for k in ("type", "publisher", "volume", "issue", "page") if msg.get(k)},
    }


def _datacite_ref(body: bytes) -> dict:
    attr = json.loads(body)["data"]["attributes"]
    titles = [t.get("title") for t in attr.get("titles") or [] if t.get("title")]
    authors = []
    for c in attr.get("creators") or []:
        name = c.get("name") or ""
        family = c.get("familyName") or (name.split(",")[0] if "," in name else name.split(" ")[-1])
        given = c.get("givenName") or ""
        authors.append((family, f"{given} {family}".strip() if given else name))
    publisher = attr.get("publisher")
    if isinstance(publisher, dict):
        publisher = publisher.get("name")
    container = (attr.get("container") or {}).get("title")
    related = [
        f"{r.get('relationType')} {r.get('relatedIdentifierType')} {r.get('relatedIdentifier')}"
        for r in attr.get("relatedIdentifiers") or []
    ]
    return {
        "title": titles[0] if titles else None,
        "title_candidates": titles,
        "authors": authors,
        "year": str(attr["publicationYear"]) if attr.get("publicationYear") else None,
        "venue": container or publisher,
        "extra": {
            "publisher": publisher,
            "resource_type": (attr.get("types") or {}).get("resourceTypeGeneral"),
            "url": attr.get("url"),
            "related_identifiers": related,
        },
    }


def resolve_doi(client: Client, doi: str) -> Resolution:
    """実在は doi.org の handle、登録機関は doiRA、書誌は登録機関の API で引く。"""
    try:
        status, body = client.get("doi", "/api/handles/" + _quote_doi(doi))
    except Unreachable as exc:
        return Resolution(UNREACHABLE, note=str(exc))
    try:
        code = json.loads(body).get("responseCode") if body else None
    except ValueError:
        code = None
    if status == 404 and code == 100:
        return Resolution(ABSENT, note="doi.org の handle が responseCode 100（Handle Not Found）")
    if not (status == 200 and code == 1):
        return Resolution(UNREACHABLE, note=f"doi.org の handle が想定外の応答（HTTP {status}, responseCode {code}）")

    registry = None
    try:
        status, body = client.get("doi", "/doiRA/" + _quote_doi(doi))
        if status == 200:
            registry = (json.loads(body) or [{}])[0].get("RA")
    except (Unreachable, ValueError) as exc:
        return Resolution("実在", note=f"登録機関を引けない: {exc}")
    service = {"Crossref": "crossref", "DataCite": "datacite"}.get(registry or "")
    if service is None:
        return Resolution("実在", registry, note=f"登録機関 {registry} の書誌は引いていない")
    path = ("/works/" if service == "crossref" else "/dois/") + _quote_doi(doi)
    try:
        status, body = client.get(service, path)
    except Unreachable as exc:
        return Resolution(UNREACHABLE, registry, note=f"実在は確かめたが書誌に届かない: {exc}")
    if status != 200:
        return Resolution("実在", registry, note=f"{registry} が書誌を返さない（HTTP {status}）")
    parse = _crossref_ref if service == "crossref" else _datacite_ref
    return Resolution("実在", registry, ref=parse(body))


_ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
_ABS_RE = re.compile(r"abs/(\d{4}\.\d{4,5})(?:v\d+)?$")


def _arxiv_entries(body: bytes) -> dict[str, dict]:
    root = ET.fromstring(body)
    if root.tag != f"{{{_ATOM['a']}}}feed":
        raise ValueError(f"Atom の feed ではない: {root.tag}")
    out: dict[str, dict] = {}
    for entry in root.findall("a:entry", _ATOM):
        m = _ABS_RE.search(entry.findtext("a:id", "", _ATOM).strip())
        if not m:
            continue
        names = [n.findtext("a:name", "", _ATOM).strip() for n in entry.findall("a:author", _ATOM)]
        title = " ".join(entry.findtext("a:title", "", _ATOM).split())
        out[m.group(1)] = {
            "title": title or None,
            "title_candidates": [title] if title else [],
            "authors": [(n.split(" ")[-1], n) for n in names if n],
            "year": entry.findtext("a:published", "", _ATOM)[:4] or None,
            "venue": entry.findtext("arxiv:journal_ref", None, _ATOM),
            "extra": {
                k: v
                for k, v in (
                    ("comment", entry.findtext("arxiv:comment", None, _ATOM)),
                    ("doi", entry.findtext("arxiv:doi", None, _ATOM)),
                )
                if v
            },
        }
    return out


def resolve_arxiv(client: Client, ids: list[str]) -> dict[str, Resolution]:
    """arXiv の API に id_list でまとめて問い合わせる。応答の feed に無い ID を不在とする。"""
    out: dict[str, Resolution] = {}
    for start in range(0, len(ids), ARXIV_BATCH):
        batch = ids[start : start + ARXIV_BATCH]
        path = f"/api/query?id_list={','.join(batch)}&max_results={len(batch)}"
        try:
            status, body = client.get("arxiv", path)
            if status != 200:
                raise Unreachable(f"HTTP {status}")
            entries = _arxiv_entries(body)
        except (Unreachable, ET.ParseError, ValueError) as exc:
            for ident in batch:
                out[ident] = Resolution(UNREACHABLE, note=str(exc))
            continue
        for ident in batch:
            if ident in entries:
                out[ident] = Resolution("実在", "arXiv", ref=entries[ident])
            else:
                out[ident] = Resolution(ABSENT, note="arXiv の API の応答に該当の entry が無い")
    return out


# --- 分類と記録 ---------------------------------------------------------------


def classify(found: FoundId, rows: list[Row], res: Resolution) -> dict:
    """一つの ID の結果。比べた地図の行と、照合先が返した書誌を並べて残す。"""
    hits = [r for r in rows if found.key in {(kind, ident.lower()) for kind, ident, _s, _e in _ids_in(r.id_text)}]
    used = hits[0] if hits else None
    record: dict = {
        "kind": found.kind,
        "id": found.id,
        "lines": found.lines,
        "registry": res.registry,
        "reference": None,
        "map_row": asdict(used) if used else None,
        "other_rows": [r.row_id for r in hits[1:]],
        "title": None,
        "authors": None,
        "venue": {"reference": None, "map": used.venue if used else None},
        "note": res.note,
    }
    if res.status in (ABSENT, UNREACHABLE):
        record["class"] = res.status
        return record
    ref = res.ref
    if ref is None:
        record["class"] = UNCOMPARABLE
        return record
    record["reference"] = {
        "title": ref["title"],
        "authors": [full for _f, full in ref["authors"]],
        "year": ref["year"],
        "venue": ref["venue"],
        "extra": ref["extra"],
    }
    record["venue"]["reference"] = ref["venue"]
    if used is None:
        record["class"] = UNCOMPARABLE
        record["note"] = (record["note"] + " " if record["note"] else "") + "地図に書誌の行（文献と書誌 ID の列を持つ表の行）が無い"
        return record
    bib = parse_literature(used.literature)
    title, title_detail = compare_title(bib.title, ref["title_candidates"])
    authors, authors_detail = compare_authors(bib, ref["authors"])
    record["title"] = {"result": title, "detail": title_detail, "map": bib.title}
    record["authors"] = {"result": authors, "detail": authors_detail, "map": bib.authors, "et_al": bib.et_al}
    if title is None and authors is None:
        record["class"] = UNCOMPARABLE
    elif "差" in (title, authors):
        record["class"] = DIFF
    else:
        record["class"] = MATCH
    return record


def verify(text: str, client: Client) -> dict:
    found = extract_ids(text)
    rows = description_rows(text)
    resolutions: dict[tuple[str, str], Resolution] = {}
    for item in found:
        if item.kind == "doi":
            resolutions[item.key] = resolve_doi(client, item.id)
    arxiv = resolve_arxiv(client, [item.id for item in found if item.kind == "arxiv"])
    for item in found:
        if item.kind == "arxiv":
            resolutions[item.key] = arxiv[item.id]
    results = [classify(item, rows, resolutions[item.key]) for item in found]
    counts = {name: sum(1 for r in results if r["class"] == name) for name in CLASSES}
    assert sum(counts.values()) == len(found), "分類の件数の和が抽出した ID の数と合わない"
    rows_without_id = [r.row_id for r in rows if not _ids_in(r.id_text)]
    return {
        "total_ids": len(found),
        "by_kind": {k: sum(1 for f in found if f.kind == k) for k in ("doi", "arxiv")},
        "counts": counts,
        "rows_without_id": rows_without_id,
        "results": results,
        "requests": client.log,
    }


def _cell(value) -> str:
    if value is None or value == "" or value == []:
        return "—"
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    return str(value).replace("|", "／").replace("\n", " ")


def render_markdown(report: dict) -> str:
    lines = [
        f"# 照合の結果 — {report['map']}",
        "",
        f"- 地図の sha256: `{report['map_sha256']}`",
        f"- 照合の日時: {report['checked_at']}",
        f"- 命令: `{report['command']}`",
        f"- 照合先: {', '.join(f'{k}={v}' for k, v in report['endpoints'].items())}",
        f"- 問い合わせの数: {len(report['requests'])}",
        "",
        "## 分類ごとの件数",
        "",
        "| 分類 | 件数 |",
        "|---|---|",
        *[f"| {name} | {report['counts'][name]} |" for name in CLASSES],
        f"| 計（抽出した ID） | {report['total_ids']}（DOI {report['by_kind']['doi']}、arXiv {report['by_kind']['arxiv']}） |",
        "",
        f"書誌 ID の無い行（照合の対象外。件数だけを数える）: {len(report['rows_without_id'])} 行"
        + (f"（{', '.join(report['rows_without_id'])}）" if report["rows_without_id"] else ""),
        "",
        "## ID ごとの結果",
        "",
        "掲載先は分類に入れず、参考として並べる。",
        "",
        "| 種別 | ID | 分類 | 比べた地図の行 | 題名 | 著者 | 照合先の題名 | 照合先の著者 | 年 | 掲載先（照合先） | 掲載先（地図） | 登録機関・注記 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in report["results"]:
        ref = r["reference"] or {}
        row = r["map_row"]
        where = f"{row['row_id']}（L{row['line']}）" if row else f"行なし（L{', L'.join(map(str, r['lines']))}）"
        authors = ref.get("authors") or []
        shown = authors[:3] + ([f"ほか {len(authors) - 3} 名"] if len(authors) > 3 else [])
        title = r["title"] or {}
        author = r["authors"] or {}
        lines.append(
            "| "
            + " | ".join(
                _cell(v)
                for v in (
                    r["kind"],
                    r["id"],
                    r["class"],
                    where,
                    f"{title.get('result') or '比べず'}: {title.get('detail')}" if title else None,
                    f"{author.get('result') or '比べず'}: {author.get('detail')}" if author else None,
                    ref.get("title"),
                    shown,
                    ref.get("year"),
                    r["venue"]["reference"],
                    r["venue"]["map"],
                    " ".join(p for p in (r["registry"] or "", r["note"] or "") if p),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def exit_code(counts: dict[str, int]) -> int:
    if counts[UNREACHABLE]:
        return 3
    return 1 if counts[ABSENT] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="証拠地図の書誌 ID を照合する。")
    parser.add_argument("map", help="照合する地図（Markdown）")
    parser.add_argument("--out-dir", default=str(OUT_DIR), help="結果の置き場（既定 docs/evidence/verification）")
    parser.add_argument(
        "--endpoint", action="append", default=[], metavar="NAME=URL",
        help=f"照合先の基底 URL を差し替える（{', '.join(ENDPOINTS)}）。対照に使う",
    )
    parser.add_argument("--extract-only", action="store_true", help="問い合わせずに抽出した ID をタブ区切りで出す")
    args = parser.parse_args(argv)

    path = Path(args.map)
    try:
        data = path.read_bytes()
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR 地図を読めません: {path}: {exc}", file=sys.stderr)
        return 2

    if args.extract_only:
        for item in extract_ids(text):
            print(f"{path.name}\t{item.kind}\t{item.id}")
        return 0

    endpoints: dict[str, str] = {}
    for spec in args.endpoint:
        name, _, url = spec.partition("=")
        if name not in ENDPOINTS or not url:
            print(f"ERROR --endpoint は NAME=URL（NAME は {', '.join(ENDPOINTS)}）: {spec}", file=sys.stderr)
            return 2
        endpoints[name] = url

    client = Client(endpoints=endpoints)
    report = {
        "tool": "tools/verify_evidence_ids.py",
        "map": _display_path(path),
        "map_sha256": hashlib.sha256(data).hexdigest(),
        "checked_at": datetime.now(JST).isoformat(timespec="seconds"),
        "command": " ".join(["python", "tools/verify_evidence_ids.py", *(argv if argv is not None else sys.argv[1:])]),
        "user_agent": USER_AGENT,
        "endpoints": client.endpoints,
        **verify(text, client),
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = path.name.removesuffix(".md")
    (out_dir / f"{stem}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / f"{stem}.md").write_text(render_markdown(report), encoding="utf-8")

    counts = report["counts"]
    print(" / ".join(f"{name} {counts[name]}" for name in CLASSES) + f"（計 {report['total_ids']}）")
    print(f"結果: {_display_path(out_dir / f'{stem}.json')}、{_display_path(out_dir / f'{stem}.md')}")
    return exit_code(counts)


if __name__ == "__main__":
    raise SystemExit(main())
