import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";

mermaid.initialize({
  startOnLoad: false,
  securityLevel: "loose",
  theme: "base",
  look: "classic",
  flowchart: {
    useMaxWidth: true,
    curve: "basis",
    htmlLabels: false,
    padding: 18,
    nodeSpacing: 48,
    rankSpacing: 64,
  },
  themeVariables: {
    background: "#14171e",
    primaryColor: "#222734",
    primaryTextColor: "#e2e6f0",
    primaryBorderColor: "#6ee7b7",
    lineColor: "#8891a8",
    secondaryColor: "#1a1e28",
    secondaryTextColor: "#e2e6f0",
    secondaryBorderColor: "#60a5fa",
    tertiaryColor: "#14171e",
    tertiaryTextColor: "#8891a8",
    tertiaryBorderColor: "#2a3040",
    clusterBkg: "#14171e",
    clusterBorder: "#2a3040",
    edgeLabelBackground: "#14171e",
    fontFamily: "'DM Sans', system-ui, sans-serif",
  },
});

async function renderMermaid() {
  const fonts = document.fonts;
  if (fonts?.ready) {
    await fonts.ready;
  }
  await mermaid.run({
    querySelector: ".mermaid",
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    void renderMermaid();
  }, { once: true });
} else {
  void renderMermaid();
}
