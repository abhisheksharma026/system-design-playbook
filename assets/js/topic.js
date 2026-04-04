document.querySelectorAll(".toc a").forEach((anchor) => {
  anchor.addEventListener("click", (event) => {
    const targetId = anchor.getAttribute("href");
    if (!targetId || !targetId.startsWith("#")) {
      return;
    }

    const target = document.querySelector(targetId);
    if (!target) {
      return;
    }

    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

document.querySelectorAll(".qa").forEach((item) => {
  const trigger = item.querySelector(".qa-q");
  if (!trigger) {
    return;
  }

  trigger.addEventListener("click", () => {
    item.classList.toggle("open");
  });
});

const COPY_ICON = `
  <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <rect x="9" y="9" width="11" height="11" rx="2"></rect>
    <path d="M5 15V6a2 2 0 0 1 2-2h9"></path>
  </svg>
`;

function createCopyButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy-button";
  button.setAttribute("aria-label", "Copy code");
  button.innerHTML = `${COPY_ICON}<span class="copy-label">Copy</span>`;
  return button;
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "absolute";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

function showCopiedState(button) {
  const label = button.querySelector(".copy-label");
  if (!label) {
    return;
  }

  const previous = label.textContent;
  button.dataset.copied = "true";
  label.textContent = "Copied";

  window.setTimeout(() => {
    label.textContent = previous;
    delete button.dataset.copied;
  }, 1600);
}

function attachCopyButton(target) {
  const button = createCopyButton();
  const textGetter = () => target.textContent ?? "";

  button.addEventListener("click", async () => {
    try {
      await copyText(textGetter());
      showCopiedState(button);
    } catch {
      const label = button.querySelector(".copy-label");
      if (label) {
        const previous = label.textContent;
        label.textContent = "Failed";
        window.setTimeout(() => {
          label.textContent = previous;
        }, 1600);
      }
    }
  });

  const codeBlock = target.closest(".code-block");
  if (codeBlock) {
    codeBlock.classList.add("copy-host");
    const header = codeBlock.querySelector(".code-header");
    if (header) {
      header.appendChild(button);
    } else {
      const toolbar = document.createElement("div");
      toolbar.className = "copy-toolbar";
      toolbar.appendChild(button);
      codeBlock.insertBefore(toolbar, codeBlock.firstChild);
    }
    return;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "copy-wrap";
  const toolbar = document.createElement("div");
  toolbar.className = "copy-toolbar";
  toolbar.appendChild(button);

  const parent = target.parentNode;
  if (!parent) {
    return;
  }

  parent.insertBefore(wrapper, target);
  wrapper.appendChild(toolbar);
  wrapper.appendChild(target);
}

const copyTargets = new Set();

document.querySelectorAll("pre:not(.mermaid), .memory-map").forEach((target) => {
  if (target.closest(".diagram-wrap")) {
    return;
  }

  const codeBlock = target.closest(".code-block");
  if (codeBlock) {
    if (codeBlock.dataset.copyReady === "true") {
      return;
    }
    codeBlock.dataset.copyReady = "true";
    copyTargets.add(target);
    return;
  }

  if (target.dataset.copyReady === "true") {
    return;
  }
  target.dataset.copyReady = "true";
  copyTargets.add(target);
});

copyTargets.forEach((target) => {
  attachCopyButton(target);
});
