from __future__ import annotations

import re
import shutil
from html import escape

from site_utils import discover_pages, repo_root


TOPIC_NUMBER_RE = re.compile(r"Topic\s+(\d+)", re.IGNORECASE)


def topic_number_from_source(path: str) -> int | None:
    match = TOPIC_NUMBER_RE.search(path)
    if not match:
        return None
    return int(match.group(1))


def build_index(pages: list[dict[str, str]]) -> str:
    topic_rows = "\n".join(
        f"""
        <li class="topic-item">
          <a class="topic-link" href="{escape(page["href"])}">
            <span class="topic-num">{escape(page["label"])}</span>
            <span class="topic-main">
              <span class="topic-title">{escape(page["title"])}</span>
              <span class="topic-desc">{escape(page["description"])}</span>
            </span>
          </a>
        </li>
        """.strip()
        for page in pages
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>System Design Playbook</title>
  <meta name="description" content="A visual guide to system design fundamentals, architecture patterns, and the building blocks of scalable systems.">
  <link rel="stylesheet" href="assets/css/home.css">
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">System Design Playbook</p>
      <h1>Build system design fundamentals.</h1>
    </section>

    <section class="index-shell">
      <div class="index-copy">
        <p class="section-kicker">Learning Path</p>
        <h2>Start at the foundation, then layer on complexity.</h2>
      </div>

      <ol class="topic-list">
        {topic_rows}
      </ol>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    root = repo_root()
    dist = root / "dist"
    pages = [
        page
        for page in discover_pages(root)
        if page.relative_path.parts and page.relative_path.parts[0] == "topics"
    ]

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True, exist_ok=True)

    assets_dir = root / "assets"
    if assets_dir.exists():
        shutil.copytree(assets_dir, dist / "assets")

    page_cards: list[dict[str, str]] = []
    for page in pages:
        output_path = dist / page.relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(page.source_path, output_path)

        href = page.relative_path.as_posix()
        if href.endswith("/index.html"):
            href = href[: -len("index.html")]

        page_cards.append(
            {
                "href": href,
                "title": page.h1 or page.title,
                "description": page.description or page.title,
                "order": topic_number_from_source(page.source_path.read_text(encoding="utf-8")),
                "label": "--",
            }
        )

    page_cards.sort(
        key=lambda item: (
            item["order"] is None,
            item["order"] if item["order"] is not None else 999,
            item["title"].lower(),
        )
    )
    for index, item in enumerate(page_cards, start=1):
        number = item["order"] if item["order"] is not None else index
        item["label"] = f"{number:02d}"

    (dist / "index.html").write_text(build_index(page_cards), encoding="utf-8")
    print(f"Built site into {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
