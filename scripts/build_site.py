from __future__ import annotations

import shutil
from html import escape

from site_utils import discover_pages, repo_root


def build_index(pages: list[dict[str, str]]) -> str:
    cards = "\n".join(
        f"""
        <a class="card" href="{escape(page["href"])}">
          <h2>{escape(page["title"])}</h2>
          <p>{escape(page["description"])}</p>
        </a>
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
      <h1>Study one topic at a time.</h1>
      <p>
        Clear, visual notes on core system design concepts. Start with the fundamentals,
        build stronger mental models, and move from one topic to the next without getting
        lost in jargon.
      </p>
      <div class="meta">
        <span>{len(pages)} published topics</span>
        <span>Visual deep dives</span>
        <span>Open access</span>
      </div>
    </section>
    <section class="grid">
      {cards}
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    root = repo_root()
    dist = root / "dist"
    pages = discover_pages(root)

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
            }
        )

    page_cards.sort(key=lambda item: item["title"].lower())
    (dist / "index.html").write_text(build_index(page_cards), encoding="utf-8")
    print(f"Built site into {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
