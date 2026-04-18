# System Design Playbook

Static HTML pages for system design fundamentals. The site is intentionally simple: each topic is a standalone HTML page, shared assets live under `assets/`, and `scripts/build_site.py` copies the source pages into `dist/` while generating the landing page and knowledge graph.

## Project Layout

```text
.
├── topics/
│   └── <topic-slug>/
│       └── index.html       # Source topic page
├── assets/
│   ├── css/                 # Shared page and graph styling
│   └── js/                  # Shared topic behavior and graph UI
├── scripts/                 # Build, serve, validation, and scaffold helpers
├── dist/                    # Generated site output, do not edit directly
├── .github/workflows/       # GitHub Pages deployment
├── pyproject.toml
└── uv.lock
```

## Topic Sequence

Topics start at `01`. `security` is the final topic at `22`.

| Label | Slug | Title |
| --- | --- | --- |
| 01 | `client-server-model` | Client-Server Model |
| 02 | `network-protocols` | Network Protocols |
| 03 | `storage` | Storage |
| 04 | `latency-and-throughput` | Latency and Throughput |
| 05 | `availability` | Availability |
| 06 | `caching` | Caching |
| 07 | `proxies` | Proxies |
| 08 | `load-balancer` | Load Balancers |
| 09 | `hashing` | Hashing |
| 10 | `relational-databases` | Relational Databases |
| 11 | `key-value-stores` | Key-Value Stores |
| 12 | `specialized-storage` | Specialized Storage Paradigms |
| 13 | `replication-sharding` | Replication and Sharding |
| 14 | `leader-election` | Leader Election |
| 15 | `peer-networking` | Peer-to-Peer Networks |
| 16 | `sockets` | Polling, Streaming, and Sockets |
| 17 | `config` | Configuration Management |
| 18 | `rate-limiting` | Rate Limiting |
| 19 | `logging` | Logging and Monitoring |
| 20 | `pub-sub` | Publish/Subscribe Patterns |
| 21 | `map-reduce` | MapReduce |
| 22 | `security` | Security and HTTPS |

## Source Rules

- Topic pages live in `topics/<slug>/index.html`.
- Shared styling and behavior go in `assets/`.
- Do not edit `dist/`; it is generated output.
- Keep hero labels and footer metadata aligned with the sequence above.
- Each topic footer should include previous/next navigation where applicable, plus a Home link back to the landing page, using the shared `topic-nav` classes.
- If topic ordering changes, update the topic HTML labels, footer links, this README, and `GRAPH_LAYOUT` in `scripts/build_site.py` where needed.

## Local Workflow

```bash
uv sync
uv run python scripts/check_site.py
uv run python scripts/build_site.py
uv run python scripts/serve.py --build
```

Then open:

```text
http://127.0.0.1:8000
```

## Add a Topic

Create a page manually in `topics/<slug>/index.html`, or scaffold one:

```bash
uv run python scripts/new_topic.py --title "Load Balancing"
```

After adding or renumbering a topic, update:

- The topic hero label.
- The topic footer navigation, including its Home link.
- `GRAPH_LAYOUT` in `scripts/build_site.py` if the topic should appear in a specific place on the knowledge graph.
- The topic sequence in this README.

## Scripts

- `scripts/check_site.py`: validates required HTML metadata and local links.
- `scripts/build_site.py`: copies source pages into `dist/`, generates the landing page, and builds `knowledge-map.html`.
- `scripts/serve.py`: serves either the repo root or the built `dist/` directory.
- `scripts/new_topic.py`: creates a starter page in `topics/<slug>/index.html`.

## GitHub Pages

The workflow in `.github/workflows/pages.yml` builds the site and deploys `dist/` to GitHub Pages.
