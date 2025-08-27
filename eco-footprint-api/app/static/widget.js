(() => {
  const SHOP = (window.Shopify && Shopify.shop) || location.host;
  const API_BASE =
    window.CARBON_API_BASE || new URL("/", document.currentScript.src).origin;
  const CART_URL = "/cart.js";
  const UPDATE_URL = "/cart/update.js";

  function moneyCentsToStr(cents, currency) {
    const v = (cents || 0) / 100;
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
      }).format(v);
    } catch {
      return `$${v.toFixed(2)}`;
    }
  }

  async function fetchJSON(url, opts = {}) {
    const res = await fetch(url, { credentials: "include", ...opts });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function injectStyles() {
    if (document.getElementById("carbon-widget-styles")) return;
    const css = `
        .carbon-widget{border:1px solid #e5e7eb;border-radius:.75rem;padding:1rem;margin:.5rem 0;display:flex;align-items:center;gap:.75rem;font-family:system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;}
        .carbon-widget__cta{display:flex;align-items:center;gap:.5rem;cursor:pointer}
        .carbon-widget__pill{padding:.25rem .5rem;border-radius:9999px;background:#f3f4f6;font-size:.875rem}
        .carbon-widget__amount{font-weight:600}
      `;
    const s = document.createElement("style");
    s.id = "carbon-widget-styles";
    s.textContent = css;
    document.head.appendChild(s);
  }

  async function main() {
    injectStyles();

    // 1) Fetch widget config (placement/verbiage) from backend
    const cfg = await fetchJSON(
      `${API_BASE}/v1/config?shop=${encodeURIComponent(SHOP)}`
    );
    const root = document.querySelector(cfg.placement || "#cart_container");
    if (!root) return;

    // 2) Load Shopify cart
    const cart = await fetchJSON(CART_URL);
    const subtotal_cents = cart.items.reduce(
      (sum, it) => sum + it.price * it.quantity,
      0
    );
    const items = cart.items.map((it) => ({
      price_cents: it.price,
      quantity: it.quantity,
      grams: it.grams,
      product_type: it.product_type,
      vendor: it.vendor,
    }));

    // 3) Ask backend for estimate using placeholder formula
    const estimate = await fetchJSON(`${API_BASE}/v1/estimate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        shop: SHOP,
        currency: cart.currency || "USD",
        items,
      }),
    });

    // 4) Render widget
    const container = document.createElement("div");
    container.className = "carbon-widget";
    container.innerHTML = `
        <label class="carbon-widget__cta">
          <input type="checkbox" id="carbon-optin" />
          <span>${cfg.verbiage || "Reduce my order's carbon footprint"}</span>
        </label>
        <span class="carbon-widget__pill">
          Estimated offset: <span class="carbon-widget__amount">${moneyCentsToStr(
            estimate.estimate_cents,
            estimate.currency
          )}</span>
        </span>
      `;
    root.prepend(container);

    // 5) Persist on toggle: set cart attributes + notify backend
    const checkbox = container.querySelector("#carbon-optin");
    checkbox.addEventListener("change", async (e) => {
      const attrs = e.target.checked
        ? {
            carbon_offset_opt_in: "yes",
            carbon_offset_cents: estimate.estimate_cents,
          }
        : { carbon_offset_opt_in: "no", carbon_offset_cents: 0 };

      // update cart attributes so checkout/thank-you can see it
      await fetchJSON(UPDATE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attributes: attrs }),
      });

      if (e.target.checked) {
        // best-effort cart token read (Shopify AJAX returns "token" on /cart.js in many themes)
        const freshCart = await fetchJSON(CART_URL);
        const cartToken =
          freshCart.token ||
          document.cookie.match(/cart=([^;]+)/)?.[1] ||
          "unknown";
        await fetchJSON(`${API_BASE}/v1/opt-in`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            shop: SHOP,
            cart_token: cartToken,
            currency: estimate.currency,
            subtotal_cents: estimate.subtotal_cents,
            estimate_cents: estimate.estimate_cents,
            payload: { source: "widget", items_count: items.length },
          }),
        });
      }
    });
  }

  // run when DOM ready
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", main);
  else main();
})();
