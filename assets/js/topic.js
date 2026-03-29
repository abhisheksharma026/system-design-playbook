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
