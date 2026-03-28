# System Design Playbook

Static HTML pages for system design topics, with a lightweight `uv`-managed workflow for local preview, validation, build output, and GitHub Pages deployment.

## Recommended Layout

```text
.
├── topics/
│   └── <topic-slug>/
│       └── index.html       # Topic pages live in their own folders
├── assets/
│   ├── css/
│   └── js/
├── scripts/                 # Build, serve, check, and authoring helpers
├── dist/                    # Generated site output
├── .github/workflows/       # GitHub Pages deployment
├── pyproject.toml
└── uv.lock
```

## Current Source Rules

- Topic pages should live in `topics/<slug>/index.html`.
- Shared styling and behavior should go in `assets/`.
- Do not edit `dist/` directly; it is generated output.

## Local Workflow

```bash
uv sync
uv run python scripts/check_site.py
uv run python scripts/build_site.py
uv run python scripts/serve.py --build
```

Then open `http://127.0.0.1:8000`.

## Add a New Topic

Create a page manually in `topics/<slug>/index.html`, or scaffold one:

```bash
uv run python scripts/new_topic.py --title "Load Balancing"
```

## What the Scripts Do

- `scripts/check_site.py`: validates required HTML metadata and local links
- `scripts/build_site.py`: copies source pages into `dist/` and generates a landing page
- `scripts/serve.py`: serves either the repo root or the built `dist/` directory
- `scripts/new_topic.py`: creates a starter topic page in `topics/<slug>/index.html`

## GitHub Pages

The workflow in `.github/workflows/pages.yml` builds the site and deploys `dist/` to GitHub Pages.
