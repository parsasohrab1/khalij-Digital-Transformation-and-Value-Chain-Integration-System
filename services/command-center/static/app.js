(() => {
  const state = {
    locale: localStorage.getItem("dvc_locale") || "fa",
    role: localStorage.getItem("dvc_role") || "admin",
    token: localStorage.getItem("dvc_token") || "",
    pendingToken: "",
    view: "dashboard",
    messages: {},
    views: ["dashboard", "cost", "distribution", "alerts", "optimize", "orders", "logistics"],
    lastShipment: "",
  };

  const api = () => window.DVC_API_BASE.replace(/\/$/, "");
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  function authHeaders(extra) {
    const h = { ...(extra || {}) };
    if (state.token) h.Authorization = `Bearer ${state.token}`;
    return h;
  }

  async function fetchJSON(url, options = {}) {
    const opts = { ...options, headers: authHeaders(options.headers || {}) };
    const res = await fetch(url, opts);
    if (res.status === 401) {
      logout(true);
      throw new Error("unauthorized");
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${url} ${text.slice(0, 180)}`);
    }
    if (res.status === 204) return null;
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
      subsidiary_code: $("#subsidiary")?.value,
      product_grade: $("#product")?.value,
      region: $("#region")?.value,
      period: $("#period")?.value || "30d",
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
    if (!state.views.includes(state.view)) setActiveView(state.views[0] || "dashboard");
  }

  function showApp(loggedIn) {
    $("#loginScreen").classList.toggle("hidden", loggedIn);
    $("#appShell").classList.toggle("hidden", !loggedIn);
    if (loggedIn) {
      $("#userBadge").textContent = `${localStorage.getItem("dvc_user") || "user"} · ${state.role}`;
    }
  }

  function logout(silent) {
    state.token = "";
    state.pendingToken = "";
    localStorage.removeItem("dvc_token");
    localStorage.removeItem("dvc_role");
    localStorage.removeItem("dvc_user");
    showApp(false);
    if (!silent) $("#loginError").hidden = true;
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
    if (dash.kpis?.data_source) {
      $("#kpiGrid").insertAdjacentHTML(
        "beforeend",
        `<article class="kpi"><div class="label">Data</div><div class="value" style="font-size:1rem">${dash.kpis.data_source}</div></article>`
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
    if (!rows || !rows.length) {
      el.innerHTML = `<p class="muted">${t("no_alerts")}</p>`;
      return;
    }
    el.innerHTML = `<table><thead><tr>${columns
      .map((c) => `<th>${c.label}</th>`)
      .join("")}</tr></thead><tbody>${rows
      .map((r) => `<tr>${columns.map((c) => `<td>${r[c.key] ?? ""}</td>`).join("")}</tr>`)
      .join("")}</tbody></table>`;
  }

  async function loadFilters() {
    const data = await fetchJSON(`${api()}/filters`);
    const fill = (sel, items, labelFn) => {
      const el = $(sel);
      const cur = el.value;
      el.innerHTML =
        `<option value="">${t("all")}</option>` +
        items
          .map((x) => {
            const val = typeof x === "string" ? x : x.code;
            const label = typeof x === "string" ? x : labelFn(x);
            return `<option value="${val}">${label}</option>`;
          })
          .join("");
      el.value = cur;
    };
    fill("#subsidiary", data.subsidiaries, (x) => (state.locale === "en" ? x.name_en : x.name_fa));
    fill("#product", data.products, (x) => x);
    fill("#region", data.regions, (x) => x);
  }

  async function loadDashboard() {
    const q = qs(currentFilters());
    const dash = await fetchJSON(`${api()}/command-center/dashboard?${q}`);
    state.views = dash.views || state.views;
    applyRoleNav();
    renderKpis(dash);
    const ts = await fetchJSON(`${api()}/timeseries?${qs({ ...currentFilters(), metric: "operating_margin_percent" })}`);
    drawTrend(ts.points || []);
  }

  async function loadCost() {
    const data = await fetchJSON(`${api()}/reports/cost-per-ton?${qs(currentFilters())}`);
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
    const data = await fetchJSON(`${api()}/reports/distribution?${qs(currentFilters())}`);
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
    const data = await fetchJSON(`${api()}/alerts?${qs({ locale: state.locale, only_active: "false", limit: 30 })}`);
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
        await fetchJSON(`${api()}/alerts/${btn.dataset.ack}/acknowledge`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ by: state.role }),
        });
        loadAlerts();
      });
    });
  }

  async function loadOrders() {
    const inv = await fetchJSON(`${api()}/inventory`);
    const rows = inv.warehouses || (Array.isArray(inv) ? inv : []);
    renderTable(
      $("#inventoryTable"),
      [
        { key: "code", label: "WH" },
        { key: "city", label: "City" },
        { key: "total_tons", label: "Total t" },
        { key: "fill_rate_pct", label: "Fill %" },
        { key: "capacity_tons", label: "Capacity" },
      ],
      rows
    );
    try {
      const orders = await fetchJSON(`${api()}/orders?limit=20`);
      renderTable(
        $("#ordersTable"),
        [
          { key: "order_number", label: "Order" },
          { key: "product_grade", label: "Product" },
          { key: "quantity_tons", label: "Tons" },
          { key: "status", label: "Status" },
          { key: "allocated_warehouse", label: "WH" },
        ],
        Array.isArray(orders) ? orders : orders.items || []
      );
    } catch (_) {
      /* list may be empty on fresh start */
    }
  }

  async function loadLogistics() {
    const ports = await fetchJSON(`${api()}/ports/iran`);
    const list = ports.ports || [];
    renderTable(
      $("#portsTable"),
      [
        { key: "port_key", label: "Port" },
        { key: "name_fa", label: "Name" },
        { key: "berths", label: "Berths" },
        { key: "congestion_hours", label: "Congestion h" },
      ],
      list.map((p) => ({
        port_key: p.port_key || p.code || p.pmo_code,
        name_fa: p.name_fa || p.name_en || "",
        berths: p.berths ?? "",
        congestion_hours: p.congestion_hours ?? p.base_congestion_hours ?? "",
      }))
    );
    try {
      const ships = await fetchJSON(`${api()}/shipments?limit=20`);
      renderTable(
        $("#shipmentsTable"),
        [
          { key: "shipment_number", label: "Shipment" },
          { key: "origin_port", label: "Origin" },
          { key: "destination", label: "Dest" },
          { key: "status", label: "Status" },
          { key: "eta_days", label: "ETA" },
        ],
        Array.isArray(ships) ? ships : []
      );
    } catch (_) {
      /* ignore */
    }
  }

  async function refreshAll() {
    await loadFilters();
    await loadDashboard();
    if (state.views.includes("cost")) await loadCost();
    if (state.views.includes("distribution")) await loadDistribution();
    if (state.views.includes("alerts")) await loadAlerts();
    if (state.views.includes("orders")) await loadOrders();
    if (state.views.includes("logistics")) await loadLogistics();
  }

  async function initI18n() {
    try {
      const data = await fetchJSON(`${api()}/i18n/${state.locale}`);
      state.messages = data.messages || {};
    } catch (_) {
      state.messages = {};
    }
    applyI18n();
  }

  async function initRole() {
    try {
      const data = await fetchJSON(`${api()}/roles/${state.role}/views`);
      state.views = data.views || state.views;
    } catch (_) {
      /* keep defaults */
    }
    applyRoleNav();
  }

  async function handleLogin(e) {
    e.preventDefault();
    const err = $("#loginError");
    err.hidden = true;
    const employee_code = $("#loginUser").value.trim();
    const password = $("#loginPass").value;
    const otp = $("#loginOtp").value.trim();
    try {
      if (!state.pendingToken) {
        const login = await fetch(`${api()}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ employee_code, password }),
        }).then(async (r) => {
          if (!r.ok) throw new Error(await r.text());
          return r.json();
        });
        if (!login.requires_otp && login.access_token) {
          state.token = login.access_token;
          state.role = login.role || "admin";
          localStorage.setItem("dvc_token", state.token);
          localStorage.setItem("dvc_role", state.role);
          localStorage.setItem("dvc_user", employee_code);
          await afterLogin();
          return;
        }
        state.pendingToken = login.pending_token;
        $("#otpField").classList.remove("hidden");
        err.textContent = "OTP required";
        err.hidden = false;
        return;
      }
      const verified = await fetch(`${api()}/auth/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pending_token: state.pendingToken, otp_code: otp }),
      }).then(async (r) => {
        if (!r.ok) throw new Error(await r.text());
        return r.json();
      });
      state.token = verified.access_token;
      state.role = verified.role || "admin";
      state.pendingToken = "";
      localStorage.setItem("dvc_token", state.token);
      localStorage.setItem("dvc_role", state.role);
      localStorage.setItem("dvc_user", verified.employee_code || employee_code);
      await afterLogin();
    } catch (ex) {
      err.textContent = String(ex.message || ex);
      err.hidden = false;
      state.pendingToken = "";
      $("#otpField").classList.add("hidden");
    }
  }

  async function afterLogin() {
    showApp(true);
    await initI18n();
    await initRole();
    await refreshAll();
  }

  function bind() {
    $("#locale").value = state.locale;
    $("#loginForm").addEventListener("submit", handleLogin);
    $("#logoutBtn").addEventListener("click", () => logout(false));
    $("#locale").addEventListener("change", async (e) => {
      state.locale = e.target.value;
      localStorage.setItem("dvc_locale", state.locale);
      await initI18n();
      await refreshAll();
    });
    ["#subsidiary", "#product", "#region", "#period"].forEach((sel) => {
      $(sel).addEventListener("change", () => refreshAll());
    });
    $$(".nav button").forEach((btn) => {
      btn.addEventListener("click", () => setActiveView(btn.dataset.view));
    });
    $("#refreshBtn").addEventListener("click", () => refreshAll());
    $("#budgetCheckBtn").addEventListener("click", async () => {
      await fetchJSON(`${api()}/alerts/check-budgets`, { method: "POST" });
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
        $("#optimizeOut").textContent = String(err);
      }
    });
    $("#orderForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const out = await fetchJSON(`${api()}/orders`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            channel: "contract",
            product_grade: $("#orderProduct").value,
            quantity_tons: Number($("#orderTons").value),
            value_usd: Number($("#orderValue").value),
            destination: $("#orderDest").value,
            auto_invoice: true,
          }),
        });
        $("#orderOut").textContent = JSON.stringify(out, null, 2);
        $("#shipOrder").value = out.order_number || $("#shipOrder").value;
        await loadOrders();
      } catch (err) {
        $("#orderOut").textContent = String(err);
      }
    });
    $("#shipForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const out = await fetchJSON(`${api()}/shipments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            order_number: $("#shipOrder").value,
            origin_port: $("#shipOrigin").value,
            destination: $("#shipDest").value,
            product_grade: $("#shipProduct").value,
            quantity_tons: Number($("#shipTons").value),
            value_usd: 200000,
          }),
        });
        state.lastShipment = out.shipment_number;
        $("#shipOut").textContent = JSON.stringify(out, null, 2);
        await loadLogistics();
      } catch (err) {
        $("#shipOut").textContent = String(err);
      }
    });
    $("#trackBtn").addEventListener("click", async () => {
      try {
        const sn = state.lastShipment || ($("#shipmentsTable td")?.textContent || "");
        const out = await fetchJSON(`${api()}/shipments/live-track`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ shipment_number: sn, progress: 0.55 }),
        });
        $("#shipOut").textContent = JSON.stringify(out, null, 2);
        await loadLogistics();
      } catch (err) {
        $("#shipOut").textContent = String(err);
      }
    });
  }

  async function boot() {
    bind();
    if (state.token) {
      try {
        const me = await fetchJSON(`${api()}/auth/me`);
        state.role = me.role || state.role;
        localStorage.setItem("dvc_role", state.role);
        await afterLogin();
        return;
      } catch (_) {
        logout(true);
      }
    }
    showApp(false);
    applyI18n();
  }

  boot();
})();
