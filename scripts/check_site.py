from __future__ import annotations

from pathlib import Path

from site_utils import discover_pages, is_local_asset, parse_links, repo_root


def resolve_local_link(source_file: Path, link: str) -> Path:
    clean_link = link.split("#", 1)[0].split("?", 1)[0]
    if clean_link.startswith("/"):
        return (repo_root() / clean_link.lstrip("/")).resolve()
    return (source_file.parent / clean_link).resolve()


def is_generated_home_link(source_file: Path, link: str, target: Path) -> bool:
    if link.split("#", 1)[0].split("?", 1)[0] != "../../index.html":
        return False
    root = repo_root()
    try:
        source_file.relative_to(root / "topics")
    except ValueError:
        return False
    return target == (root / "index.html").resolve()


def main() -> int:
    root = repo_root()
    pages = discover_pages(root)

    if not pages:
        print("No source HTML pages found.")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    for page in pages:
        if not page.lang:
            errors.append(f"{page.relative_path}: missing <html lang=...> attribute")
        if not page.source_title:
            errors.append(f"{page.relative_path}: missing <title>")
        if not page.h1:
            errors.append(f"{page.relative_path}: missing <h1>")
        if not page.description:
            warnings.append(f"{page.relative_path}: missing meta description")

        for link in parse_links(page.source_path):
            if not is_local_asset(link):
                continue
            target = resolve_local_link(page.source_path, link)
            if not target.exists() and not is_generated_home_link(page.source_path, link, target):
                errors.append(f"{page.relative_path}: broken local link -> {link}")

    for warning in warnings:
        print(f"WARN: {warning}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"\nValidation failed with {len(errors)} error(s).")
        return 1

    print(f"Validated {len(pages)} page(s) successfully.")
    if warnings:
        print(f"{len(warnings)} warning(s) found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
