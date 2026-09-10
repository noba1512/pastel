(() => {
  const PastelMoney = {
    format(raw) {
      const source = String(raw ?? "").replace(/[^\d,]/g, "");
      if (source === "") return "";
      const commaAt = source.indexOf(",");
      let intDigits;
      let decDigits = "";
      let hasComma = false;
      if (commaAt >= 0) {
        hasComma = true;
        intDigits = source.slice(0, commaAt).replace(/\D/g, "");
        decDigits = source.slice(commaAt + 1).replace(/\D/g, "").slice(0, 2);
      } else {
        intDigits = source.replace(/\D/g, "");
      }
      intDigits = intDigits.replace(/^0+(?=\d)/, "");
      if (intDigits === "") {
        if (!hasComma) return "";
        intDigits = "0";
      }
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      if (hasComma) return `${grouped},${decDigits}`;
      return grouped;
    },
    fromNumber(value) {
      const amount = Number(value);
      if (!Number.isFinite(amount)) return "";
      const cents = Math.round(Math.abs(amount) * 100);
      const reais = Math.floor(cents / 100);
      const rest = cents % 100;
      const grouped = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      if (rest === 0) return grouped;
      return `${grouped},${String(rest).padStart(2, "0")}`;
    },
    parse(raw) {
      const text = String(raw ?? "").trim().replace("R$", "").replace(/\s/g, "");
      if (!text) return null;
      let normalized;
      if (text.includes(",")) {
        normalized = text.replace(/\./g, "").replace(",", ".");
      } else if ((text.match(/\./g) || []).length > 1) {
        normalized = text.replace(/\./g, "");
      } else if (text.includes(".")) {
        const right = text.split(".")[1];
        normalized = right.length === 3 ? text.replace(".", "") : text;
      } else {
        normalized = text;
      }
      const value = Number(normalized);
      return Number.isFinite(value) ? value : null;
    },
    bind(input) {
      if (!input || input.dataset.moneyBound === "1") return;
      input.dataset.moneyBound = "1";
      input.setAttribute("inputmode", "decimal");
      input.setAttribute("autocomplete", "off");
      input.addEventListener("keydown", (event) => {
        if (event.key !== ".") return;
        event.preventDefault();
        if (input.value.includes(",")) return;
        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? start;
        input.value = `${input.value.slice(0, start)},${input.value.slice(end)}`;
        input.dispatchEvent(new Event("input", { bubbles: true }));
      });
      input.addEventListener("input", () => {
        const start = input.selectionStart ?? input.value.length;
        const prefix = input.value.slice(0, start).replace(/[^\d,]/g, "");
        const formatted = PastelMoney.format(input.value);
        input.value = formatted;
        let seen = 0;
        let pos = formatted.length;
        for (let i = 0; i < formatted.length; i += 1) {
          if (/[\d,]/.test(formatted[i])) seen += 1;
          if (seen >= prefix.length) {
            pos = i + 1;
            break;
          }
        }
        input.setSelectionRange(pos, pos);
      });
    },
  };

  window.PastelMoney = PastelMoney;
  document.querySelectorAll("[data-money]").forEach((el) => PastelMoney.bind(el));

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
