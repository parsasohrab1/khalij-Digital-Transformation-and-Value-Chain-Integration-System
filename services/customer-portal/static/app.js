(() => {
  const api = () => (window.DVC_API_BASE || "http://localhost:8000").replace(/\/$/, "");
  const $ = (s) => document.querySelector(s);

  $("#trackForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const order = $("#orderNumber").value.trim();
    const locale = $("#locale").value;
    const err = $("#error");
    err.hidden = true;
    try {
      const [portal, status] = await Promise.all([
        fetch(`${api()}/customer/orders/${encodeURIComponent(order)}/portal?locale=${locale}`).then(async (r) => {
          if (!r.ok) throw new Error(await r.text());
          return r.json();
        }),
        fetch(`${api()}/customer/orders/${encodeURIComponent(order)}/status?locale=${locale}`).then(async (r) => {
          if (!r.ok) throw new Error(await r.text());
          return r.json();
        }),
      ]);
      $("#portalOut").textContent = JSON.stringify(portal, null, 2);
      $("#statusOut").textContent = JSON.stringify(status, null, 2);
      $("#result").classList.remove("hidden");
    } catch (ex) {
      err.textContent = String(ex.message || ex);
      err.hidden = false;
      $("#result").classList.add("hidden");
    }
  });
})();
