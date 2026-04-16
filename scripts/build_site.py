from __future__ import annotations

import json
import math
import re
import shutil
from html import escape
from pathlib import Path

from site_utils import discover_pages, repo_root


TOPIC_NUMBER_RE = re.compile(r"Topic\s+(\d+)", re.IGNORECASE)
TOC_RE = re.compile(r'<nav class="toc">.*?<ol>(.*?)</ol>', re.IGNORECASE | re.DOTALL)
TOC_LINK_RE = re.compile(r'<a href="#([^"]+)">(.*?)</a>', re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
SECTION_ZERO_RE = re.compile(r'<section class="section" id="s0">(.*?)</section>', re.IGNORECASE | re.DOTALL)
H3_RE = re.compile(r"<h3>(.*?)</h3>", re.IGNORECASE | re.DOTALL)
GRAPH_SKIP_RE = re.compile(
    r"key terms|prerequisites|hands-on|mini-project|production example|interview|cheat sheet|key takeaways|mental model|what if|napkin math",
    re.IGNORECASE,
)

GRAPH_LAYOUT = {
    "client-server-model": {
        "x": 220,
        "y": 860,
        "cluster": "Foundations",
        "tone": "foundation",
        "deps": [],
        "orbit_rotation": -8,
    },
    "network-protocols": {
        "x": 430,
        "y": 670,
        "cluster": "Foundations",
        "tone": "foundation",
        "deps": ["client-server-model"],
        "orbit_rotation": -18,
    },
    "storage": {
        "x": 760,
        "y": 670,
        "cluster": "Data",
        "tone": "data",
        "deps": ["client-server-model"],
        "orbit_rotation": 14,
    },
    "latency-and-throughput": {
        "x": 400,
        "y": 430,
        "cluster": "Performance",
        "tone": "performance",
        "deps": ["network-protocols", "storage"],
        "orbit_rotation": -28,
    },
    "caching": {
        "x": 830,
        "y": 430,
        "cluster": "Data",
        "tone": "data",
        "deps": ["storage", "latency-and-throughput", "hashing"],
        "orbit_rotation": 24,
    },
    "hashing": {
        "x": 960,
        "y": 820,
        "cluster": "Foundations",
        "tone": "foundation",
        "deps": ["client-server-model"],
        "orbit_rotation": 10,
    },
    "proxies": {
        "x": 1040,
        "y": 620,
        "cluster": "Foundations",
        "tone": "foundation",
        "deps": ["client-server-model", "network-protocols"],
        "orbit_rotation": 18,
    },
    "load-balancer": {
        "x": 1180,
        "y": 430,
        "cluster": "Reliability",
        "tone": "reliability",
        "deps": ["proxies", "latency-and-throughput", "hashing"],
        "orbit_rotation": 22,
    },
    "availability": {
        "x": 620,
        "y": 160,
        "cluster": "Reliability",
        "tone": "reliability",
        "deps": ["network-protocols", "storage", "latency-and-throughput"],
        "orbit_rotation": -90,
    },
    "relational-databases": {
        "x": 1000,
        "y": 180,
        "cluster": "Data",
        "tone": "data",
        "deps": ["storage", "client-server-model"],
        "orbit_rotation": -36,
    },
    "key-value-stores": {
        "x": 1260,
        "y": 820,
        "cluster": "Data",
        "tone": "data",
        "deps": ["storage", "hashing"],
        "orbit_rotation": 34,
    },
    "specialized-storage": {
        "x": 1310,
        "y": 220,
        "cluster": "Data",
        "tone": "data",
        "deps": ["storage", "relational-databases", "key-value-stores"],
        "orbit_rotation": 12,
    },
    "replication-sharding": {
        "x": 1170,
        "y": 230,
        "cluster": "Data",
        "tone": "data",
        "deps": ["storage", "relational-databases", "availability", "hashing"],
        "orbit_rotation": -8,
    },
    "leader-election": {
        "x": 820,
        "y": 80,
        "cluster": "Reliability",
        "tone": "reliability",
        "deps": ["availability", "network-protocols", "replication-sharding"],
        "orbit_rotation": -54,
    },
    "peer-networking": {
        "x": 170,
        "y": 250,
        "cluster": "Foundations",
        "tone": "foundation",
        "deps": ["network-protocols", "hashing", "latency-and-throughput"],
        "orbit_rotation": -42,
    },
    "sockets": {
        "x": 170,
        "y": 540,
        "cluster": "Foundations",
        "tone": "foundation",
        "deps": ["client-server-model", "network-protocols", "latency-and-throughput"],
        "orbit_rotation": -24,
    },
    "config": {
        "x": 560,
        "y": 980,
        "cluster": "Foundations",
        "tone": "foundation",
        "deps": ["client-server-model", "storage", "leader-election"],
        "orbit_rotation": -12,
    },
    "rate-limiting": {
        "x": 1120,
        "y": 980,
        "cluster": "Reliability",
        "tone": "reliability",
        "deps": ["load-balancer", "latency-and-throughput", "key-value-stores", "availability"],
        "orbit_rotation": 18,
    },
    "logging": {
        "x": 850,
        "y": 980,
        "cluster": "Reliability",
        "tone": "reliability",
        "deps": ["availability", "latency-and-throughput", "sockets", "config"],
        "orbit_rotation": 6,
    },
    "security": {
        "x": 1110,
        "y": 730,
        "cluster": "Reliability",
        "tone": "reliability",
        "deps": ["client-server-model", "network-protocols", "proxies", "load-balancer"],
        "orbit_rotation": 32,
    },
    "pub-sub": {
        "x": 1290,
        "y": 620,
        "cluster": "Data",
        "tone": "data",
        "deps": ["sockets", "storage", "key-value-stores", "replication-sharding"],
        "orbit_rotation": 28,
    },
}


def topic_number_from_source(path: str) -> int | None:
    match = TOPIC_NUMBER_RE.search(path)
    if not match:
        return None
    return int(match.group(1))


def topic_slug(relative_path: Path) -> str:
    parts = relative_path.parts
    if len(parts) >= 2 and parts[0] == "topics":
        return parts[1]
    return relative_path.stem


def strip_tags(text: str) -> str:
    return re.sub(TAG_RE, "", text)


def normalize_graph_label(label: str) -> str:
    clean = " ".join(label.split())
    if re.fullmatch(r"what is an? network protocol\??", clean, flags=re.IGNORECASE):
        return "Network Protocol"
    if re.fullmatch(r"why storage matters in system design", clean, flags=re.IGNORECASE):
        return "Storage Tradeoffs"
    clean = re.sub(r"^What Is\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^an?\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^The\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+[—-]\s+Deep Dive$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+[—-]\s+Big Picture$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+[—-]\s+Anatomy in Detail$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+[—-]\s+The Contract$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+[—-]\s+The Core Strategy$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+[—-]\s+The Missing Link$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+[—-]\s+The Tradeoff$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+[—-]\s+Where It Lives$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+\(Step by Step\)$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+\(Quick Reference\)$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+\(Read & Write Patterns\)$", "", clean, flags=re.IGNORECASE)
    clean = clean.rstrip(" ?")
    return clean.strip()


def extract_toc_concepts(path: Path) -> list[dict[str, str]]:
    html = path.read_text(encoding="utf-8")
    toc_match = TOC_RE.search(html)
    if not toc_match:
        return []

    concepts: list[dict[str, str]] = []
    for anchor, label in TOC_LINK_RE.findall(toc_match.group(1)):
        clean_label = normalize_graph_label(strip_tags(label))
        if clean_label in {"References & Further Reading"} or GRAPH_SKIP_RE.search(clean_label):
            continue
        concepts.append({"id": anchor, "label": clean_label})
    return concepts[:6]


def extract_key_terms(path: Path) -> list[dict[str, str]]:
    html = path.read_text(encoding="utf-8")
    match = SECTION_ZERO_RE.search(html)
    if not match:
        return []

    terms: list[dict[str, str]] = []
    for index, label in enumerate(H3_RE.findall(match.group(1)), start=1):
        clean_label = " ".join(strip_tags(label).split())
        if not clean_label or GRAPH_SKIP_RE.search(clean_label):
            continue
        terms.append({"id": f"s0-term-{index}", "href_id": "s0", "label": clean_label})
    return terms[:5]


def dedupe_concepts(concepts: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for concept in concepts:
        normalized = concept["label"].casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(concept)
    return unique


def orbit_positions(count: int, rotation: float) -> list[tuple[int, int]]:
    base_positions = {
        1: [(154, 0)],
        2: [(-144, -48), (152, 42)],
        3: [(-154, -42), (-78, 132), (156, 32)],
        4: [(-156, -58), (-82, 136), (144, -44), (158, 96)],
        5: [(-162, -64), (-136, 92), (0, 168), (150, -48), (176, 102)],
    }
    positions = base_positions.get(count, base_positions[5])
    theta = math.radians(rotation)
    sin_theta = math.sin(theta)
    cos_theta = math.cos(theta)
    rotated: list[tuple[int, int]] = []
    for x, y in positions:
        rotated_x = int(round(x * cos_theta - y * sin_theta))
        rotated_y = int(round(x * sin_theta + y * cos_theta))
        rotated.append((rotated_x, rotated_y))
    return rotated


def build_index(pages: list[dict[str, str]]) -> str:
    topic_rows = "\n".join(
        f"""
        <a class="topic-card" href="{escape(page["href"])}">
          <span class="topic-order">{escape(page["label"])}</span>
          <span class="topic-content">
            <span class="topic-title">{escape(page["title"])}</span>
            <span class="topic-desc">{escape(page["description"])}</span>
          </span>
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
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/home.css">
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">System Design Playbook</p>
      <h1>Build system design fundamentals.</h1>
    </section>

    <section class="home-grid">
      <div class="home-sidebar">
        <div class="lead-card">
          <p class="section-kicker">Learning Path</p>
          <h2>Start at the foundation, then layer on complexity.</h2>
        </div>

        <a class="graph-card" href="knowledge-map.html">
          <span class="graph-card-kicker">Knowledge Graph</span>
          <span class="graph-card-title">See how topics connect.</span>
          <span class="graph-card-copy">Explore prerequisites, topic neighborhoods, and key concepts in the interactive graph.</span>
        </a>
      </div>

      <div class="topic-deck">
        {topic_rows}
      </div>
    </section>
  </main>
</body>
</html>
"""


def graph_path(source: dict[str, object], target: dict[str, object]) -> str:
    x1 = int(source["x"])
    y1 = int(source["y"])
    x2 = int(target["x"])
    y2 = int(target["y"])
    c1x = x1
    c1y = y1 - max(80, (y1 - y2) * 0.45)
    c2x = x2
    c2y = y2 + max(80, (y1 - y2) * 0.18)
    return f"M{x1} {y1} C{c1x} {c1y}, {c2x} {c2y}, {x2} {y2}"


def build_knowledge_graph(pages: list[dict[str, object]]) -> str:
    graph_nodes: list[dict[str, object]] = []
    fallback_y = 920
    fallback_step = 114
    graph_edges: list[dict[str, str]] = []

    for fallback_index, page in enumerate(pages):
        layout = GRAPH_LAYOUT.get(str(page["slug"]))
        if layout is None:
            layout = {
                "x": 1120,
                "y": max(120, fallback_y - fallback_index * fallback_step),
                "cluster": "Frontier",
                "tone": "frontier",
                "deps": [pages[max(0, fallback_index - 1)]["slug"]] if fallback_index else [],
                "orbit_rotation": 0,
            }
        topic_node = {**page, **layout, "kind": "topic", "parent": None}
        graph_nodes.append(topic_node)

        terms = extract_key_terms(page["source_path"])
        supporting_needed = max(0, 5 - len(terms))
        supporting_concepts = extract_toc_concepts(page["source_path"])[:supporting_needed]
        concepts = dedupe_concepts((terms + supporting_concepts)[:5])
        hub_x = int(layout["x"])
        hub_y = int(layout["y"])
        for concept, (offset_x, offset_y) in zip(concepts, orbit_positions(len(concepts), float(layout["orbit_rotation"]))):
            x = hub_x + offset_x
            y = hub_y + offset_y
            x = max(48, min(1252, x))
            y = max(48, min(992, y))
            graph_nodes.append(
                {
                    "slug": f'{page["slug"]}:{concept["id"]}',
                    "href": f'{page["href"]}#{concept.get("href_id", concept["id"])}',
                    "title": concept["label"],
                    "description": "",
                    "label": str(page["label"]),
                    "cluster": str(layout["cluster"]),
                    "tone": str(layout["tone"]),
                    "x": x,
                    "y": y,
                    "deps": [str(page["slug"])],
                    "kind": "concept",
                    "parent": str(page["slug"]),
                }
            )
            graph_edges.append(
                {
                    "source": str(page["slug"]),
                    "target": f'{page["slug"]}:{concept["id"]}',
                    "type": "concept",
                }
            )

    node_map = {str(node["slug"]): node for node in graph_nodes}
    ordered_nodes = sorted(
        [node for node in graph_nodes if node["kind"] == "topic"],
        key=lambda item: (
            item["order"] is None,
            item["order"] if item["order"] is not None else 999,
            str(item["title"]).lower(),
        ),
    )
    learning_sequence = [str(node["slug"]) for node in ordered_nodes]
    graph_payload = {
        "nodes": [
            {
                "slug": str(node["slug"]),
                "href": str(node["href"]),
                "title": str(node["title"]),
                "description": str(node["description"]),
                "label": str(node["label"]),
                "cluster": str(node["cluster"]),
                "tone": str(node["tone"]),
                "x": int(node["x"]),
                "y": int(node["y"]),
                "deps": [str(dep) for dep in node["deps"]],
                "kind": str(node["kind"]),
                "parent": str(node["parent"]) if node["parent"] is not None else None,
            }
            for node in graph_nodes
        ],
        "edges": graph_edges
        + [
            {"source": dep_slug, "target": str(node["slug"]), "type": "dependency"}
            for node in graph_nodes
            if node["kind"] == "topic"
            for dep_slug in node["deps"]
        ]
        + [
            {
                "source": learning_sequence[index],
                "target": learning_sequence[index + 1],
                "type": "learning",
            }
            for index in range(len(learning_sequence) - 1)
        ],
        "learningSequence": learning_sequence,
    }
    graph_json = json.dumps(graph_payload).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>System Design Playbook — Knowledge Graph</title>
  <meta name="description" content="Explore system design topics as a knowledge graph of concepts, prerequisites, and learning paths.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/home-graph.css">
</head>
<body>
  <main class="map-page">
    <section class="map-hero">
      <div class="map-copy">
        <p class="map-eyebrow">System Design Playbook</p>
        <h1>Knowledge graph for the playbook.</h1>
        <div class="map-legend">
          <span><i class="legend-dot legend-dependency"></i> prerequisite dependency</span>
          <span><i class="legend-dot legend-learning"></i> recommended reading order</span>
        </div>
      </div>
    </section>

    <section class="graph-shell">
      <div class="graph-stage">
        <div class="graph-frame" id="graph-frame">
          <div class="graph-controls" aria-label="Graph controls">
            <button type="button" class="graph-control" data-zoom="in" aria-label="Zoom in">+</button>
            <button type="button" class="graph-control" data-zoom="out" aria-label="Zoom out">-</button>
            <button type="button" class="graph-control graph-control-reset" id="graph-reset" aria-label="Reset view">&#8634;</button>
          </div>
          <div class="graph-overlay graph-overlay-left">
            <p class="overlay-label">Clusters</p>
            <div id="cluster-filter" class="cluster-filter"></div>
          </div>
          <div class="graph-grid" aria-hidden="true"></div>
          <div class="graph-viewport" id="graph-viewport">
            <svg class="graph-lines" viewBox="0 0 1300 1040" aria-hidden="true">
              <defs>
                <filter id="graphGlow">
                  <feGaussianBlur stdDeviation="4" result="coloredBlur"></feGaussianBlur>
                  <feMerge>
                    <feMergeNode in="coloredBlur"></feMergeNode>
                    <feMergeNode in="SourceGraphic"></feMergeNode>
                  </feMerge>
                </filter>
              </defs>
              <g id="graph-edge-layer"></g>
            </svg>
            <div class="graph-nodes" id="graph-node-layer"></div>
          </div>
        </div>
        <p class="graph-hint">Drag to pan. Scroll to zoom. Click a topic to focus its nearby concepts.</p>
      </div>
      <aside class="graph-panel">
        <div id="node-details" class="node-details">
          <p class="details-empty">Select a node to inspect how it connects to the graph.</p>
        </div>
      </aside>
    </section>
  </main>
  <script id="graph-data" type="application/json">{graph_json}</script>
  <script src="assets/js/home-graph.js"></script>
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
                "slug": topic_slug(page.relative_path),
                "title": page.h1 or page.title,
                "description": page.description or page.title,
                "order": topic_number_from_source(page.source_path.read_text(encoding="utf-8")),
                "label": "--",
                "source_path": page.source_path,
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
    (dist / "knowledge-map.html").write_text(build_knowledge_graph(page_cards), encoding="utf-8")
    print(f"Built site into {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
