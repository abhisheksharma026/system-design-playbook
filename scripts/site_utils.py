from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Page:
    source_path: Path
    relative_path: Path
    source_title: str | None
    title: str
    h1: str | None
    description: str | None
    lang: str | None


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.h1: str | None = None
        self.description: str | None = None
        self.lang: str | None = None
        self._in_title = False
        self._in_h1 = False
        self._title_parts: list[str] = []
        self._h1_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "html":
            self.lang = attr_map.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "h1" and self.h1 is None:
            self._in_h1 = True
        elif tag == "meta":
            if attr_map.get("name", "").lower() == "description":
                content = attr_map.get("content")
                if content:
                    self.description = content.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
            title = "".join(self._title_parts).strip()
            if title:
                self.title = title
        elif tag == "h1":
            self._in_h1 = False
            if self.h1 is None:
                heading = " ".join("".join(self._h1_parts).split())
                if heading:
                    self.h1 = heading

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        if self._in_h1:
            self._h1_parts.append(data)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self._ignored_tag_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"code", "kbd", "pre", "samp", "script", "style", "textarea"}:
            self._ignored_tag_depth += 1
            return
        if self._ignored_tag_depth:
            return
        attr_map = dict(attrs)
        for attr_name in ("href", "src"):
            value = attr_map.get(attr_name)
            if value:
                self.links.append(value.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag in {"code", "kbd", "pre", "samp", "script", "style", "textarea"}:
            self._ignored_tag_depth = max(0, self._ignored_tag_depth - 1)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def iter_source_html(root: Path | None = None) -> Iterable[Path]:
    base = root or repo_root()

    for path in sorted(base.glob("*.html")):
        if path.name == "index.html":
            continue
        yield path

    topics_dir = base / "topics"
    if topics_dir.exists():
        for path in sorted(topics_dir.rglob("*.html")):
            yield path


def parse_metadata(path: Path) -> Page:
    parser = MetadataParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return Page(
        source_path=path,
        relative_path=path.relative_to(repo_root()),
        source_title=parser.title,
        title=parser.title or path.stem.replace("-", " ").title(),
        h1=parser.h1,
        description=parser.description,
        lang=parser.lang,
    )


def discover_pages(root: Path | None = None) -> list[Page]:
    return [parse_metadata(path) for path in iter_source_html(root)]


def parse_links(path: Path) -> list[str]:
    parser = LinkParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.links


def is_local_asset(link: str) -> bool:
    lowered = link.lower()
    return not (
        lowered.startswith("#")
        or lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("mailto:")
        or lowered.startswith("tel:")
        or lowered.startswith("data:")
        or lowered.startswith("javascript:")
    )
