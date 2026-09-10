(() => {
  const root = document.getElementById("pdv-root");
  if (!root) return;

  const checkoutUrl = root.dataset.checkoutUrl;
  const canDiscount = root.dataset.canDiscount === "1";
  const csrf = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="))
    ?.split("=")[1];

  const search = document.getElementById("pdv-search");
  const grid = document.getElementById("pdv-grid");
  const cats = document.getElementById("pdv-cats");
  const linesEl = document.getElementById("cart-lines");
  const emptyEl = document.getElementById("cart-empty");
  const subtotalEl = document.getElementById("cart-subtotal");
  const totalEl = document.getElementById("cart-total");
  const discountEl = document.getElementById("cart-discount");
  const cashBox = document.getElementById("cash-box");
  const receivedEl = document.getElementById("amount-received");
  const changeEl = document.getElementById("cart-change");
  const errorEl = document.getElementById("pdv-error");
  const bannerEl = document.getElementById("sale-banner");
  const receiptNumber = document.getElementById("receipt-number");
  const cartCount = document.getElementById("cart-count");
  const totalMobile = document.getElementById("cart-total-mobile");
  const cartPanel = document.getElementById("pdv-cart");
  const cartToggle = document.getElementById("pdv-cart-toggle");

  const cart = new Map();
  let category = "";

  function moneyFromInput(raw) {
    if (window.PastelMoney) {
      return window.PastelMoney.parse(raw) || 0;
    }
    if (raw == null || raw === "") return 0;
    const text = String(raw).trim().replace("R$", "").replace(/\s/g, "");
    if (!text) return 0;
    const normalized = text.includes(",")
      ? text.replace(/\./g, "").replace(",", ".")
      : text;
    const value = Number(normalized);
    return Number.isFinite(value) ? value : 0;
  }

  function formatBRL(value) {
    const amount = Number.isFinite(value) ? value : 0;
    return amount.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  function showError(message) {
    errorEl.textContent = message;
    errorEl.classList.toggle("hidden", !message);
  }

  function productButtons() {
    return [...grid.querySelectorAll("[data-product]")];
  }

  function filterProducts() {
    const q = search.value.trim().toLowerCase();
    let visible = 0;
    productButtons().forEach((btn) => {
      const hay = `${btn.dataset.name} ${btn.dataset.sku}`.toLowerCase();
      const catOk = !category || btn.dataset.category === category;
      const textOk = !q || hay.includes(q);
      const show = catOk && textOk;
      btn.classList.toggle("hidden", !show);
      if (show) visible += 1;
    });
    const noneEl = document.getElementById("pdv-none");
    if (noneEl) noneEl.classList.toggle("hidden", visible !== 0);
  }

  function cartTotals() {
    let subtotal = 0;
    cart.forEach((line) => {
      subtotal += line.price * line.qty;
    });
    const discount = canDiscount ? moneyFromInput(discountEl.value) : 0;
    const total = Math.max(0, subtotal - discount);
    return { subtotal, discount, total };
  }

  function renderCart() {
    const { subtotal, total } = cartTotals();
    linesEl.innerHTML = "";
    const empty = cart.size === 0;
    emptyEl.classList.toggle("hidden", !empty);
    linesEl.classList.toggle("hidden", empty);

    cart.forEach((line) => {
      const li = document.createElement("li");
      li.className = "border-b border-dashed border-ink/20 pb-3";
      li.innerHTML = `
        <div class="flex justify-between gap-3">
          <div>
            <p class="font-semibold leading-tight">${line.name}</p>
            <p class="font-mono text-xs text-ink/60">${formatBRL(line.price)}</p>
          </div>
          <p class="tabular font-semibold">${formatBRL(line.price * line.qty)}</p>
        </div>
        <div class="mt-2 flex items-center gap-2">
          <button type="button" class="qty-btn bg-ink/10" data-act="dec" data-id="${line.id}">−</button>
          <span class="tabular min-w-8 text-center text-lg">${line.qty}</span>
          <button type="button" class="qty-btn bg-ink/10" data-act="inc" data-id="${line.id}">+</button>
          <button type="button" class="ml-auto underline text-sm" data-act="rm" data-id="${line.id}">Remover</button>
        </div>`;
      linesEl.appendChild(li);
    });

    subtotalEl.textContent = formatBRL(subtotal);
    totalEl.textContent = formatBRL(total);
    if (totalMobile) totalMobile.textContent = formatBRL(total);
    if (cartCount) {
      const qty = [...cart.values()].reduce((sum, line) => sum + line.qty, 0);
      cartCount.textContent = qty === 1 ? "1 item" : `${qty} itens`;
    }
    updateCash();
    const checkoutBtn = document.getElementById("btn-checkout");
    if (checkoutBtn && !checkoutBtn.dataset.busy) {
      checkoutBtn.disabled = cart.size === 0;
    }
  }

  function stockLeft(btn, extraQty) {
    const stock = Number(btn.dataset.stock || 0);
    return stock - extraQty;
  }

  function addProduct(btn) {
    if (btn.disabled) return;
    const opening = cart.size === 0;
    const id = btn.dataset.id;
    const current = cart.get(id) || {
      id,
      name: btn.dataset.name,
      price: moneyFromInput(btn.dataset.price),
      qty: 0,
    };
    if (stockLeft(btn, current.qty) <= 0) {
      showError(`Estoque insuficiente para ${btn.dataset.name}.`);
      return;
    }
    current.qty += 1;
    cart.set(id, current);
    showError("");
    renderCart();
    if (
      opening &&
      cartPanel &&
      window.matchMedia("(max-width: 1023px)").matches
    ) {
      cartPanel.classList.add("is-open");
    }
  }

  function changeQty(id, delta) {
    const line = cart.get(id);
    if (!line) return;
    if (delta > 0) {
      const btn = grid.querySelector(`[data-id="${id}"]`);
      if (btn && stockLeft(btn, line.qty) <= 0) {
        showError(`Estoque insuficiente para ${line.name}.`);
        return;
      }
    }
    line.qty += delta;
    if (line.qty <= 0) cart.delete(id);
    renderCart();
  }

  function consumeStock() {
    cart.forEach((line) => {
      const btn = grid.querySelector(`[data-id="${line.id}"]`);
      if (!btn) return;
      const next = Math.max(0, Number(btn.dataset.stock || 0) - line.qty);
      const min = Number(btn.dataset.min || 0);
      btn.dataset.stock = String(next);
      const stockLine = btn.querySelector(".stock-line");
      if (stockLine) stockLine.textContent = `${next} un`;
      btn.classList.toggle("is-out", next <= 0);
      btn.classList.toggle("is-low", next > 0 && next <= min);
      btn.disabled = next <= 0;
    });
  }

  function selectedMethod() {
    return document.querySelector('input[name="payment_method"]:checked')?.value || "DINHEIRO";
  }

  function updateCash() {
    const isCash = selectedMethod() === "DINHEIRO";
    cashBox.classList.toggle("hidden", !isCash);
    document.querySelectorAll('input[name="payment_method"]').forEach((input) => {
      input.closest("label").classList.toggle("is-on", input.checked);
    });
    if (!isCash) {
      changeEl.textContent = formatBRL(0);
      return;
    }
    const { total } = cartTotals();
    const received = moneyFromInput(receivedEl.value);
    changeEl.textContent = formatBRL(Math.max(0, received - total));
  }

  function clearCart() {
    cart.clear();
    if (discountEl && discountEl.type !== "hidden") discountEl.value = "";
    receivedEl.value = "";
    receiptNumber.textContent = "NOVA";
    renderCart();
  }

  function reprintReceipt(url) {
    if (!url) return;
    return fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrf,
        "X-Requested-With": "XMLHttpRequest",
      },
    });
  }

  const printCheckbox = document.getElementById("print-receipt");
  if (printCheckbox) {
    if (localStorage.getItem("pdv-print-receipt") === "0") {
      printCheckbox.checked = false;
    }
    printCheckbox.addEventListener("change", () => {
      localStorage.setItem("pdv-print-receipt", printCheckbox.checked ? "1" : "0");
    });
  }

  async function checkout() {
    const btn = document.getElementById("btn-checkout");
    if (btn.dataset.busy) return;
    showError("");
    if (cart.size === 0) {
      showError("Adicione pelo menos um produto.");
      return;
    }
    const { discount, total } = cartTotals();
    const method = selectedMethod();
    const payload = {
      items: [...cart.values()].map((line) => ({ product_id: Number(line.id), quantity: line.qty })),
      payment_method: method,
      discount: canDiscount ? discount.toFixed(2) : "0.00",
      print: printCheckbox ? printCheckbox.checked : true,
    };
    if (method === "DINHEIRO") {
      const received = moneyFromInput(receivedEl.value);
      if (received < total) {
        showError("Valor recebido menor que o total.");
        return;
      }
      payload.amount_received = received.toFixed(2);
    }

    btn.disabled = true;
    btn.dataset.busy = "1";
    btn.textContent = "Registrando…";
    try {
      const response = await fetch(checkoutUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!data.ok) {
        showError(data.error || "Não foi possível finalizar.");
        return;
      }
      const changeText = data.change ? ` Troco ${formatBRL(Number(data.change))}.` : "";
      let printText = "";
      if (payload.print && data.printed) {
        printText = data.print_method === "terminal"
          ? " Comprovante no terminal."
          : " Comprovante impresso.";
      }
      bannerEl.innerHTML = `Venda <strong class="font-mono">${data.number}</strong> concluída.${changeText}${printText} Pode começar a próxima.`;
      if (data.reprint_url) {
        const reprint = document.createElement("button");
        reprint.type = "button";
        reprint.className = "ml-3 underline";
        reprint.textContent = "Imprimir de novo";
        reprint.addEventListener("click", () => {
          reprintReceipt(data.reprint_url).catch(() => {
            showError("Falha ao reimprimir.");
          });
        });
        bannerEl.appendChild(reprint);
      }
      bannerEl.classList.remove("hidden");
      consumeStock();
      clearCart();
      if (cartPanel) cartPanel.classList.remove("is-open");
      search.focus();
      window.setTimeout(() => bannerEl.classList.add("hidden"), 8000);
    } catch (_err) {
      showError("Falha de rede ao finalizar. Tente de novo.");
    } finally {
      btn.dataset.busy = "";
      btn.textContent = "Finalizar · F9";
      btn.disabled = cart.size === 0;
    }
  }

  grid.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-product]");
    if (btn) addProduct(btn);
  });

  linesEl.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-act]");
    if (!btn) return;
    const id = btn.dataset.id;
    if (btn.dataset.act === "inc") changeQty(id, 1);
    if (btn.dataset.act === "dec") changeQty(id, -1);
    if (btn.dataset.act === "rm") {
      cart.delete(id);
      renderCart();
    }
  });

  cats.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-category]");
    if (!btn) return;
    category = btn.dataset.category;
    cats.querySelectorAll("[data-category]").forEach((el) => el.classList.toggle("is-on", el === btn));
    filterProducts();
  });

  search.addEventListener("input", filterProducts);
  search.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const first = productButtons().find(
      (btn) => !btn.classList.contains("hidden") && !btn.disabled,
    );
    if (first) addProduct(first);
  });

  document.querySelectorAll('input[name="payment_method"]').forEach((input) => {
    input.addEventListener("change", updateCash);
  });
  receivedEl.addEventListener("input", updateCash);
  const exactBtn = document.getElementById("btn-exact");
  if (exactBtn) {
    exactBtn.addEventListener("click", () => {
      receivedEl.value = window.PastelMoney
        ? window.PastelMoney.fromNumber(cartTotals().total)
        : cartTotals().total.toFixed(2).replace(".", ",");
      updateCash();
      receivedEl.focus();
    });
  }
  if (discountEl) discountEl.addEventListener("input", renderCart);
  document.getElementById("btn-clear").addEventListener("click", clearCart);
  document.getElementById("btn-checkout").addEventListener("click", checkout);
  if (cartToggle && cartPanel) {
    cartToggle.addEventListener("click", () => {
      cartPanel.classList.toggle("is-open");
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement !== search) {
      event.preventDefault();
      search.focus();
    }
    if (event.key === "F9") {
      event.preventDefault();
      checkout();
    }
  });

  renderCart();
  updateCash();
})();
