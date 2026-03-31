(function () {
  const graphDataEl = document.getElementById("graph-data");
  const frame = document.getElementById("graph-frame");
  const viewport = document.getElementById("graph-viewport");
  const edgeLayer = document.getElementById("graph-edge-layer");
  const nodeLayer = document.getElementById("graph-node-layer");
  const detailsEl = document.getElementById("node-details");
  const clusterFilterEl = document.getElementById("cluster-filter");
  const resetButton = document.getElementById("graph-reset");
  const zoomButtons = document.querySelectorAll("[data-zoom]");
  const leftOverlay = document.querySelector(".graph-overlay-left");
  const rightOverlay = document.querySelector(".graph-overlay-right");

  if (!graphDataEl || !frame || !viewport || !edgeLayer || !nodeLayer || !detailsEl || !clusterFilterEl) {
    return;
  }

  const graph = JSON.parse(graphDataEl.textContent || "{}");
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const nodeMap = new Map(nodes.map((node) => [node.slug, node]));
  const adjacency = new Map();
  const clusterNames = ["All", ...new Set(nodes.map((node) => node.cluster))];

  edges.forEach((edge) => {
    const sourceLinks = adjacency.get(edge.source) || [];
    const targetLinks = adjacency.get(edge.target) || [];
    sourceLinks.push(edge.target);
    targetLinks.push(edge.source);
    adjacency.set(edge.source, sourceLinks);
    adjacency.set(edge.target, targetLinks);
  });

  const firstTopic = nodes.find((node) => node.kind === "topic");

  const state = {
    activeCluster: "All",
    selectedSlug: firstTopic ? firstTopic.slug : null,
    hoveredSlug: null,
    scale: 1,
    translateX: 0,
    translateY: 0,
    dragStartX: 0,
    dragStartY: 0,
    dragTranslateX: 0,
    dragTranslateY: 0,
    dragging: false,
    moved: false,
  };

  const nodeElements = new Map();
  const edgeElements = [];

  function pathBetween(source, target, type) {
    if (type === "concept") {
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.max(1, Math.hypot(dx, dy));
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;
      const bend = Math.min(38, distance * 0.14);
      const controlX = midX - (dy / distance) * bend;
      const controlY = midY + (dx / distance) * bend;
      return `M${source.x} ${source.y} Q${controlX} ${controlY}, ${target.x} ${target.y}`;
    }

    const vertical = source.y - target.y;
    const c1x = source.x;
    const c1y = source.y - Math.max(70, Math.abs(vertical) * 0.35);
    const c2x = target.x;
    const c2y = target.y + Math.max(70, Math.abs(vertical) * 0.18);
    return `M${source.x} ${source.y} C${c1x} ${c1y}, ${c2x} ${c2y}, ${target.x} ${target.y}`;
  }

  function applyViewportTransform() {
    viewport.style.transform = `translate(${state.translateX}px, ${state.translateY}px) scale(${state.scale})`;
  }

  function visibleNodes() {
    return nodes.filter((node) => state.activeCluster === "All" || node.cluster === state.activeCluster);
  }

  function activeSlug() {
    return state.hoveredSlug || state.selectedSlug;
  }

  function anchorSlug(slug) {
    const node = nodeMap.get(slug);
    if (!node) {
      return slug;
    }
    return node.kind === "concept" ? (node.parent || slug) : slug;
  }

  function relatedSet(slug) {
    const set = new Set();
    if (!slug) {
      return set;
    }
    set.add(slug);
    (adjacency.get(slug) || []).forEach((neighbor) => set.add(neighbor));
    return set;
  }

  function boundsFor(nodeList, padding = 180) {
    const minX = Math.min(...nodeList.map((node) => node.x)) - padding;
    const maxX = Math.max(...nodeList.map((node) => node.x)) + padding;
    const minY = Math.min(...nodeList.map((node) => node.y)) - padding;
    const maxY = Math.max(...nodeList.map((node) => node.y)) + padding;
    return { minX, maxX, minY, maxY, width: maxX - minX, height: maxY - minY };
  }

  function safeFrameBox() {
    const frameRect = frame.getBoundingClientRect();
    let left = 36;
    let right = 36;
    let top = 32;
    let bottom = 36;

    if (leftOverlay) {
      const leftRect = leftOverlay.getBoundingClientRect();
      left = Math.max(left, leftRect.width + 34);
    }

    if (rightOverlay) {
      const rightRect = rightOverlay.getBoundingClientRect();
      right = Math.max(right, rightRect.width + 34);
    }

    const width = frameRect.width - left - right;
    const height = frameRect.height - top - bottom;
    if (width < frameRect.width * 0.35 || height < frameRect.height * 0.4) {
      return {
        x: 24,
        y: 24,
        width: frameRect.width - 48,
        height: frameRect.height - 48,
      };
    }

    return { x: left, y: top, width, height };
  }

  function setViewportAnimated(animated) {
    viewport.classList.toggle("is-dragging", !animated);
  }

  function centerOnNodes(nodeList, animated) {
    const targetNodes = nodeList.length ? nodeList : nodes;
    const bounds = boundsFor(targetNodes);
    const safeBox = safeFrameBox();

    setViewportAnimated(animated);
    state.scale = Math.min(safeBox.width / bounds.width, safeBox.height / bounds.height, 1);
    state.translateX = safeBox.x + (safeBox.width - bounds.width * state.scale) / 2 - bounds.minX * state.scale;
    state.translateY = safeBox.y + (safeBox.height - bounds.height * state.scale) / 2 - bounds.minY * state.scale;
    applyViewportTransform();
  }

  function centerInitialView(animated = false) {
    const visibleTopics = visibleNodes().filter((node) => node.kind === "topic");
    centerOnNodes(visibleTopics.length ? visibleTopics : visibleNodes(), animated);
  }

  function centerOnSlug(slug) {
    const visible = visibleNodes();
    const visibleMap = new Set(visible.map((node) => node.slug));
    const focus = visible.filter((node) => relatedSet(anchorSlug(slug)).has(node.slug) && visibleMap.has(node.slug));
    centerOnNodes(focus, true);
  }

  function renderNodes() {
    nodeLayer.innerHTML = "";
    nodes.forEach((node) => {
      const anchor = document.createElement("a");
      anchor.className = `graph-node graph-node--${node.kind} tone-${node.tone}`;
      anchor.href = node.href;
      anchor.style.left = `${node.x}px`;
      anchor.style.top = `${node.y}px`;
      anchor.dataset.slug = node.slug;
      anchor.innerHTML = node.kind === "topic"
        ? `
          <span class="graph-node-dot"></span>
          <span class="graph-node-label">
            <span class="graph-node-num">${node.label}</span>
            <span class="graph-node-title">${node.title}</span>
            <span class="graph-node-meta">${node.cluster}</span>
          </span>
        `
        : `
          <span class="graph-node-dot"></span>
          <span class="graph-node-label">
            <span class="graph-node-title">${node.title}</span>
          </span>
        `;
      anchor.addEventListener("click", (event) => {
        if (state.moved) {
          event.preventDefault();
          return;
        }
        event.preventDefault();
        state.selectedSlug = node.slug;
        update();
        centerOnSlug(node.slug);
      });
      anchor.addEventListener("pointerdown", (event) => {
        event.stopPropagation();
      });
      anchor.addEventListener("mouseenter", () => {
        state.hoveredSlug = node.slug;
        updateVisualState();
      });
      anchor.addEventListener("mouseleave", () => {
        state.hoveredSlug = null;
        updateVisualState();
      });
      nodeLayer.appendChild(anchor);
      nodeElements.set(node.slug, anchor);
    });
  }

  function renderEdges() {
    edgeLayer.innerHTML = "";
    edges.forEach((edge) => {
      const source = nodeMap.get(edge.source);
      const target = nodeMap.get(edge.target);
      if (!source || !target) {
        return;
      }
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("class", `edge edge-${edge.type}`);
      path.setAttribute("d", pathBetween(source, target, edge.type));
      path.dataset.source = edge.source;
      path.dataset.target = edge.target;
      path.dataset.type = edge.type;
      edgeLayer.appendChild(path);
      edgeElements.push(path);
    });
  }

  function renderClusterFilter() {
    clusterFilterEl.innerHTML = "";
    clusterNames.forEach((cluster) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "cluster-pill";
      button.textContent = cluster;
      button.dataset.cluster = cluster;
      button.addEventListener("click", () => {
        state.activeCluster = cluster;
        ensureSelectedVisible();
        update();
        centerInitialView(true);
      });
      clusterFilterEl.appendChild(button);
    });
  }

  function uniqueBySlug(items) {
    const seen = new Set();
    return items.filter((item) => {
      if (!item || seen.has(item.slug)) {
        return false;
      }
      seen.add(item.slug);
      return true;
    });
  }

  function renderDetails() {
    const selected = nodeMap.get(state.selectedSlug);
    if (!selected) {
      detailsEl.innerHTML = '<p class="details-empty">Select a node to inspect how it connects to the graph.</p>';
      return;
    }

    const parent = selected.parent ? nodeMap.get(selected.parent) : null;
    const prerequisites = uniqueBySlug(
      selected.kind === "topic"
        ? selected.deps.map((slug) => nodeMap.get(slug))
        : parent
          ? [parent]
          : [],
    );
    const childConcepts = uniqueBySlug(
      nodes.filter((node) => node.parent === selected.slug),
    );
    const siblingConcepts = uniqueBySlug(
      parent
        ? nodes.filter((node) => node.parent === parent.slug && node.slug !== selected.slug)
        : [],
    );
    const downstreamTopics = uniqueBySlug(
      nodes.filter((node) => node.kind === "topic" && node.deps.includes(selected.slug)),
    );
    const relatedTopics = uniqueBySlug(
      parent
        ? nodes.filter((node) => node.kind === "topic" && (node.slug === parent.slug || node.deps.includes(parent.slug)))
        : [],
    );

    const title = selected.kind === "topic" ? selected.title : selected.title;
    const copy = selected.description || (selected.kind === "topic"
      ? "A core topic in the playbook and one of the main hubs in the knowledge graph."
      : "A key concept extracted directly from the topic and placed inside its local neighborhood.");

    const prerequisiteLinks = prerequisites.length
      ? prerequisites.map((node) => `<a class="details-link" href="${node.href}" data-slug-link="${node.slug}">${node.title}</a>`).join("")
      : '<span class="details-empty">No upstream prerequisite mapped for this node.</span>';

    const conceptLinks = (selected.kind === "topic" ? childConcepts : siblingConcepts).length
      ? (selected.kind === "topic" ? childConcepts : siblingConcepts)
        .map((node) => `<a class="details-link" href="${node.href}" data-slug-link="${node.slug}">${node.title}</a>`)
        .join("")
      : '<span class="details-empty">No nearby concept cluster mapped yet.</span>';

    const downstreamLinks = downstreamTopics.length
      ? downstreamTopics
        .map((node) => `<a class="details-link" href="${node.href}" data-slug-link="${node.slug}">${node.title}</a>`)
        .join("")
      : '<span class="details-empty">No downstream topic dependency mapped yet.</span>';

    detailsEl.innerHTML = `
      <p class="overlay-label">${selected.kind === "topic" ? "Selected Topic" : "Selected Concept"}</p>
      <h2 class="details-title">${title}</h2>
      <div class="details-meta">
        <span class="details-badge">${selected.kind === "topic" ? `Topic ${selected.label}` : "Key concept"}</span>
        <span class="details-badge">${selected.cluster}</span>
      </div>
      <p class="details-copy">${copy}</p>
      <div class="details-group">
        <h3>${selected.kind === "topic" ? "Prerequisites" : "Belongs to"}</h3>
        <div class="details-links">${prerequisiteLinks}</div>
      </div>
      <div class="details-group">
        <h3>${selected.kind === "topic" ? "Key concepts" : "Nearby concepts"}</h3>
        <div class="details-links">${conceptLinks}</div>
      </div>
      <div class="details-group">
        <h3>${selected.kind === "topic" ? "Unlocks next" : "Related topics"}</h3>
        <div class="details-links">${selected.kind === "topic"
          ? downstreamLinks
          : (relatedTopics.length
            ? relatedTopics.map((node) => `<a class="details-link" href="${node.href}" data-slug-link="${node.slug}">${node.title}</a>`).join("")
            : '<span class="details-empty">No broader topic links mapped yet.</span>')}</div>
      </div>
      <a class="details-open" href="${selected.href}">Open ${selected.kind === "topic" ? "topic" : "section"}</a>
    `;

    detailsEl.querySelectorAll("[data-slug-link]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        const slug = link.getAttribute("data-slug-link");
        state.selectedSlug = slug;
        update();
        centerOnSlug(slug);
      });
    });
  }

  function ensureSelectedVisible() {
    const visible = visibleNodes();
    const selectedVisible = visible.some((node) => node.slug === state.selectedSlug);
    if (!selectedVisible) {
      const firstVisibleTopic = visible.find((node) => node.kind === "topic");
      state.selectedSlug = firstVisibleTopic ? firstVisibleTopic.slug : (visible[0] ? visible[0].slug : null);
    }
  }

  function updateVisualState() {
    const visible = new Set(visibleNodes().map((node) => node.slug));
    const focusSlug = activeSlug();
    const focusAnchor = focusSlug ? anchorSlug(focusSlug) : null;
    const neighborhood = relatedSet(focusAnchor);

    nodeElements.forEach((element, slug) => {
      const node = nodeMap.get(slug);
      const isVisible = visible.has(slug);
      const isNeighbor = Boolean(focusSlug && neighborhood.has(slug) && slug !== focusSlug);
      const isMuted = Boolean(focusSlug && neighborhood.size && !neighborhood.has(slug));
      const hideConcept = Boolean(node && node.kind === "concept" && focusAnchor && !neighborhood.has(slug));
      element.classList.toggle("is-hidden", !isVisible);
      element.classList.toggle("is-hidden-concept", isVisible && hideConcept);
      element.classList.toggle("is-muted", isVisible && isMuted);
      element.classList.toggle("is-neighbor", isVisible && isNeighbor);
      element.classList.toggle("is-active", slug === state.selectedSlug);
      element.classList.toggle("is-hover-focus", slug === state.hoveredSlug);
      element.classList.toggle("is-bloom", Boolean(node && node.kind === "concept" && isVisible && isNeighbor));
    });

    edgeElements.forEach((edge) => {
      const sourceVisible = visible.has(edge.dataset.source);
      const targetVisible = visible.has(edge.dataset.target);
      const edgeActive = Boolean(focusSlug && neighborhood.has(edge.dataset.source) && neighborhood.has(edge.dataset.target));
      const conceptEdgeHidden = edge.dataset.type === "concept" && focusAnchor && !edgeActive;
      edge.classList.toggle("is-hidden", !(sourceVisible && targetVisible) || conceptEdgeHidden);
      edge.classList.toggle("is-muted", sourceVisible && targetVisible && focusSlug && !edgeActive);
      edge.classList.toggle("is-active", edgeActive);
    });

    clusterFilterEl.querySelectorAll(".cluster-pill").forEach((button) => {
      button.classList.toggle("is-active", button.dataset.cluster === state.activeCluster);
    });
  }

  function update() {
    ensureSelectedVisible();
    renderDetails();
    updateVisualState();
  }

  function zoomAt(delta, clientX, clientY) {
    const frameRect = frame.getBoundingClientRect();
    const pointX = (clientX - frameRect.left - state.translateX) / state.scale;
    const pointY = (clientY - frameRect.top - state.translateY) / state.scale;
    const nextScale = Math.min(2.2, Math.max(0.52, state.scale + delta));

    state.translateX = clientX - frameRect.left - pointX * nextScale;
    state.translateY = clientY - frameRect.top - pointY * nextScale;
    state.scale = nextScale;
    applyViewportTransform();
  }

  frame.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoomAt(event.deltaY < 0 ? 0.08 : -0.08, event.clientX, event.clientY);
  }, { passive: false });

  frame.addEventListener("pointerdown", (event) => {
    if (event.target.closest(".graph-node") || event.target.closest(".graph-control") || event.target.closest(".graph-overlay")) {
      return;
    }
    state.dragging = true;
    state.moved = false;
    state.dragStartX = event.clientX;
    state.dragStartY = event.clientY;
    state.dragTranslateX = state.translateX;
    state.dragTranslateY = state.translateY;
    frame.classList.add("is-dragging");
    viewport.classList.add("is-dragging");
  });

  window.addEventListener("pointermove", (event) => {
    if (!state.dragging) {
      return;
    }
    if (Math.abs(event.clientX - state.dragStartX) > 4 || Math.abs(event.clientY - state.dragStartY) > 4) {
      state.moved = true;
    }
    state.translateX = state.dragTranslateX + (event.clientX - state.dragStartX);
    state.translateY = state.dragTranslateY + (event.clientY - state.dragStartY);
    applyViewportTransform();
  });

  window.addEventListener("pointerup", () => {
    state.dragging = false;
    frame.classList.remove("is-dragging");
    viewport.classList.remove("is-dragging");
    window.setTimeout(() => {
      state.moved = false;
    }, 0);
  });

  zoomButtons.forEach((button) => {
    button.addEventListener("pointerdown", (event) => {
      event.stopPropagation();
    });
    button.addEventListener("click", () => {
      const direction = button.getAttribute("data-zoom") === "in" ? 0.12 : -0.12;
      const rect = frame.getBoundingClientRect();
      zoomAt(direction, rect.left + rect.width / 2, rect.top + rect.height / 2);
    });
  });

  resetButton?.addEventListener("click", () => {
    state.hoveredSlug = null;
    ensureSelectedVisible();
    centerInitialView(true);
    update();
  });

  renderNodes();
  renderEdges();
  renderClusterFilter();
  centerInitialView(false);
  update();

  window.addEventListener("resize", () => centerInitialView(false));
})();
