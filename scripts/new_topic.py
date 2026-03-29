from __future__ import annotations

import argparse
import re
from pathlib import Path

from site_utils import repo_root


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>System Design - {title}</title>
  <meta name="description" content="{description}">
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,600;8..60,700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../assets/css/topic.css">
</head>
<body>
  <div class="container">
    <header class="hero">
      <div class="hero-label">System Design Fundamentals</div>
      <h1>{title}</h1>
      <p class="hero-sub">{description}</p>
    </header>

    <main>
      <p>Write your topic content here.</p>
    </main>

    <footer class="site-footer">
      System Design Fundamentals
    </footer>
  </div>
  <script src="../../assets/js/topic.js"></script>
</body>
</html>
"""


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "new-topic"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new topic HTML page.")
    parser.add_argument("--title", required=True, help="The page title.")
    parser.add_argument(
        "--description",
        default="A system design topic page.",
        help="Meta description for the page.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    topics_dir = repo_root() / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    output_dir = topics_dir / slugify(args.title)
    output_path = output_dir / "index.html"
    if output_path.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {output_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        TEMPLATE.format(title=args.title, description=args.description),
        encoding="utf-8",
    )
    print(f"Created {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
