(() => {
  document.querySelectorAll("[data-flash-item]").forEach((el) => {
    window.setTimeout(() => {
      el.style.transition = "opacity 240ms ease";
      el.style.opacity = "0";
      window.setTimeout(() => el.remove(), 260);
    }, 5000);
  });

  document.querySelectorAll("[data-row-href]").forEach((row) => {
    row.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, label, textarea, select, form")) return;
      window.location.href = row.dataset.rowHref;
    });
    row.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      if (event.target !== row) return;
      event.preventDefault();
      window.location.href = row.dataset.rowHref;
    });
  });

  document.querySelectorAll("form[data-busy-submit]").forEach((form) => {
    form.addEventListener("submit", () => {
      const btn = form.querySelector("[type=submit]");
      if (!btn || btn.dataset.busy) return;
      btn.dataset.busy = "1";
      btn.disabled = true;
      btn.textContent = form.dataset.busyLabel || "Registrando…";
    });
  });

  const drawer = document.getElementById("mobile-drawer");
  if (!drawer) return;

  function openDrawer() {
    drawer.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeDrawer() {
    drawer.hidden = true;
    document.body.style.overflow = "";
  }

  document.querySelectorAll("[data-open-drawer]").forEach((btn) => {
    btn.addEventListener("click", openDrawer);
  });
  document.querySelectorAll("[data-close-drawer]").forEach((btn) => {
    btn.addEventListener("click", closeDrawer);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDrawer();
  });
})();
