(() => {
  const state = {
    locale: localStorage.getItem("dvc_locale") || "fa",
    role: localStorage.getItem("dvc_role") || "analyst",
    view: "dashboard",
    messages: {},
    views: ["dashboard", "cost", "distribution", "alerts", "optimize"],
  };

  const bi = () => window.DVC_BI_BASE.replace(/\/$/, "");
  const api = () => window.DVC_API_BASE.replace(/\/$/, "");

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  async function fetchJSON(url, options) {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
  }

  function t(key) {
    return state.messages[key] || key;
  }

  function applyI18n() {
    $$("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (state.messages[key]) el.textContent = state.messages[key];
    });
    const rtl = state.locale === "fa" || state.locale === "ar";
    document.documentElement.lang = state.locale;
    document.documentElement.dir = rtl ? "rtl" : "ltr";
    document.body.dir = rtl ? "rtl" : "ltr";
  }

  function qs(params) {
    const p = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== "") p.set(k, v);
    });
    return p.toString();
  }

  function currentFilters() {
    return {
      subsidiary_code: $("#subsidiary").value,
      product_grade: $("#product").value,
      region: $("#region").value,
      period: $("#period").value,
      locale: state.locale,
      role: state.role,
    };
  }

  function setActiveView(view) {
    state.view = view;
    $$(".view").forEach((el) => el.classList.toggle("active", el.id === `view-${view}`));
    $$(".nav button").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
  }

  function applyRoleNav() {
    $$(".nav button").forEach((btn) => {
      const allowed = state.views.includes(btn.dataset.view);
      btn.style.display = allowed ? "" : "none";
    });
    if (!state.views.includes(state.view)) {
      setActiveView(state.views[0] || "dashboard");
    }
  }

  function renderKpis(dash) {
    const map = [
      ["otif_percent", dash.labels.otif, "%"],
      ["warehouse_fill_rate_percent", dash.labels.fill, "%"],
      ["operating_margin_percent", dash.labels.margin, "%"],
      ["orders_today", dash.labels.orders, ""],
      ["ships_in_port", dash.labels.ships, ""],
      ["avg_eta_days", dash.labels.eta, ""],
    ];
    $("#kpiGrid").innerHTML = map
      .map(
        ([key, label, suffix]) => `
      <article class="kpi">
        <div class="label">${label}</div>
        <div class="value">${dash.kpis[key]}${suffix}</div>
      </article>`
      )
      .join("");
    if (dash.holding_optimized_margin_usd != null) {
      $("#kpiGrid").insertAdjacentHTML(
        "beforeend",
        `<article class="kpi"><div class="label">Holding Opt. Margin</div><div class="value">${Number(
          dash.holding_optimized_margin_usd
        ).toLocaleString()}</div></article>`
      );
    }
    $("#generatedAt").textContent = dash.generated_at || "";
  }

  function drawTrend(points) {
    const canvas = $("#trendChart");
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 600;
    const height = 160;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);
    if (!points.length) return;
    const vals = points.map((p) => p.value);
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const pad = 12;
    ctx.strokeStyle = "rgba(47,158,139,0.95)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((p, i) => {
      const x = pad + (i * (width - pad * 2)) / Math.max(points.length - 1, 1);
      const y = height - pad - ((p.value - min) / Math.max(max - min, 1e-6)) * (height - pad * 2);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  function renderTable(el, columns, rows) {
    if (!rows.length) {
      el.innerHTML = `<p class="muted">${t("no_alerts")}</p>`;
      return;
    }
    el.innerHTML = `<table><thead><tr>${columns
      .map((c) => `<th>${c.label}</th>`)
      .join("")}</tr></thead><tbody>${rows
      .map(
        (r) =>
          `<tr>${columns.map((c) => `<td>${r[c.key] ?? ""}</td>`).join("")}</tr>`
      )
      .join("")}</tbody></table>`;
  }

  async function loadFilters() {
    const data = await fetchJSON(`${bi()}/filters`);
    const fill = (sel, items, labelFn) => {
      const el = $(sel);
      const cur = el.value;
      el.innerHTML = `<option value="">${t("all")}</option>` + items.map((x) => {
        const val = typeof x === "string" ? x : x.code;
        const label = typeof x === "string" ? x : labelFn(x);
        return `<option value="${val}">${label}</option>`;
      }).join("");
      el.value = cur;
    };
    fill("#subsidiary", data.subsidiaries, (x) => (state.locale === "en" ? x.name_en : x.name_fa));
    fill("#product", data.products, (x) => x);
    fill("#region", data.regions, (x) => x);
  }

  async function loadDashboard() {
    const q = qs(currentFilters());
    const dash = await fetchJSON(`${bi()}/dashboard?${q}`);
    state.views = dash.views || state.views;
    applyRoleNav();
    renderKpis(dash);
    const ts = await fetchJSON(
      `${bi()}/timeseries?${qs({ ...currentFilters(), metric: "operating_margin_percent" })}`
    );
    drawTrend(ts.points || []);
  }

  async function loadCost() {
    const data = await fetchJSON(`${bi()}/reports/cost-per-ton?${qs(currentFilters())}`);
    renderTable(
      $("#costTable"),
      [
        { key: "unit_code", label: "Unit" },
        { key: "subsidiary_code", label: "Sub" },
        { key: "product", label: "Product" },
        { key: "cost_per_ton_usd", label: "Cost/t" },
        { key: "margin_per_ton_usd", label: "Margin/t" },
        { key: "margin_percent", label: "Margin %" },
      ],
      data.units || []
    );
  }

  async function loadDistribution() {
    const data = await fetchJSON(`${bi()}/reports/distribution?${qs(currentFilters())}`);
    renderTable(
      $("#distTable"),
      [
        { key: "subsidiary_code", label: "Sub" },
        { key: "region", label: "Region" },
        { key: "otif_percent", label: "OTIF %" },
        { key: "avg_eta_days", label: "ETA" },
        { key: "logistics_cost_per_ton_usd", label: "Log $/t" },
        { key: "delayed_shipments", label: "Delayed" },
      ],
      data.rows || []
    );
  }

  async function loadAlerts() {
    const data = await fetchJSON(`${bi()}/alerts?${qs({ locale: state.locale, only_active: "false", limit: 30 })}`);
    const box = $("#alertsList");
    const rows = data.alerts || [];
    if (!rows.length) {
      box.innerHTML = `<p class="muted">${t("no_alerts")}</p>`;
      return;
    }
    box.innerHTML = rows
      .map(
        (a) => `
      <article class="alert ${a.severity}">
        <div>
          <span class="badge ${a.severity}">${a.severity}</span>
          <strong> ${a.alert_type}</strong>
          <div class="muted">${a.message || a.message_en}</div>
        </div>
        <button type="button" class="btn" data-ack="${a.id}" ${a.acknowledged ? "disabled" : ""}>
          ${a.acknowledged ? "✓" : t("acknowledge")}
        </button>
      </article>`
      )
      .join("");
    box.querySelectorAll("[data-ack]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await fetchJSON(`${bi()}/alerts/${btn.dataset.ack}/acknowledge`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ by: state.role }),
        });
        loadAlerts();
      });
    });
  }

  async function refreshAll() {
    await loadFilters();
    await loadDashboard();
    if (state.views.includes("cost")) await loadCost();
    if (state.views.includes("distribution")) await loadDistribution();
    if (state.views.includes("alerts")) await loadAlerts();
  }

  async function initI18n() {
    const data = await fetchJSON(`${bi()}/i18n/${state.locale}`);
    state.messages = data.messages || {};
    applyI18n();
  }

  async function initRole() {
    const data = await fetchJSON(`${bi()}/roles/${state.role}/views`);
    state.views = data.views || state.views;
    applyRoleNav();
  }

  function bind() {
    $("#locale").value = state.locale;
    $("#role").value = state.role;
    $("#locale").addEventListener("change", async (e) => {
      state.locale = e.target.value;
      localStorage.setItem("dvc_locale", state.locale);
      await initI18n();
      await refreshAll();
    });
    $("#role").addEventListener("change", async (e) => {
      state.role = e.target.value;
      localStorage.setItem("dvc_role", state.role);
      await initRole();
      await refreshAll();
    });
    ["#subsidiary", "#product", "#region", "#period"].forEach((sel) => {
      $(sel).addEventListener("change", () => refreshAll());
    });
    $$(".nav button").forEach((btn) => {
      btn.addEventListener("click", () => {
        setActiveView(btn.dataset.view);
      });
    });
    $("#refreshBtn").addEventListener("click", () => refreshAll());
    $("#budgetCheckBtn").addEventListener("click", async () => {
      await fetchJSON(`${bi()}/alerts/check-budgets`, { method: "POST" });
      setActiveView("alerts");
      await loadAlerts();
    });
    $("#optimizeBtn").addEventListener("click", async () => {
      try {
        const out = await fetchJSON(`${api()}/optimize/integrated`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            horizon_days: 90,
            available_feedstock_tons: 3500,
            oil_price_usd_bbl: 78,
            model: "ensemble",
          }),
        });
        $("#optimizeOut").textContent = JSON.stringify(out, null, 2);
      } catch (err) {
        // fallback direct to analytics if gateway auth blocks anonymous UI
        try {
          const out = await fetchJSON("http://localhost:8002/optimize/integrated", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              horizon_days: 90,
              available_feedstock_tons: 3500,
              oil_price_usd_bbl: 78,
              model: "ensemble",
            }),
          });
          $("#optimizeOut").textContent = JSON.stringify(out, null, 2);
        } catch (e2) {
          $("#optimizeOut").textContent = String(err);
        }
      }
    });
  }

  async function boot() {
    bind();
    try {
      await initI18n();
      await initRole();
      await refreshAll();
    } catch (err) {
      console.error(err);
      $("#kpiGrid").innerHTML = `<p class="muted">BI API unreachable at ${bi()}. Start bi-reporting on :8005</p>`;
    }
  }

  boot();
})();
