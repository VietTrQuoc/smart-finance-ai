let leads = [
  {
    id: "CUST_20488",
    segment: "Gold Travel",
    tier: "hot",
    leadScore: 0.91,
    fraudScore: 0.12,
    riskScore: 0.22,
    topProduct: "Travel Insurance",
    eligibility: "eligible",
    breakdown: {
      product_match: 0.88,
      propensity: 0.84,
      recency: 0.76,
      customer_value: 0.72,
      fatigue: 0.15,
    },
    products: [
      {
        id: "P002",
        name: "Travel Insurance",
        type: "insurance",
        score: 0.88,
        reasons: ["Travel spend is elevated", "Low fraud score", "Segment affinity is strong"],
      },
      {
        id: "P001",
        name: "Cashback Credit Card",
        type: "credit_card",
        score: 0.73,
        reasons: ["Shopping activity is frequent", "Healthy recent activity"],
      },
      {
        id: "P006",
        name: "Health Insurance",
        type: "insurance",
        score: 0.66,
        reasons: ["Low risk profile", "Stable customer value"],
      },
    ],
    activity: ["Viewed recommendations today", "No contact in 42 days", "Last campaign: travel bundle"],
  },
  {
    id: "CUST_10022",
    segment: "Premium High Value",
    tier: "hot",
    leadScore: 0.87,
    fraudScore: 0.28,
    riskScore: 0.41,
    topProduct: "Flexible Savings",
    eligibility: "eligible",
    breakdown: {
      product_match: 0.82,
      propensity: 0.79,
      recency: 0.83,
      customer_value: 0.91,
      fatigue: 0.18,
    },
    products: [
      {
        id: "P005",
        name: "Flexible Savings",
        type: "saving",
        score: 0.82,
        reasons: ["High value customer", "Low contact fatigue", "Active recent transactions"],
      },
      {
        id: "P002",
        name: "Travel Insurance",
        type: "insurance",
        score: 0.71,
        reasons: ["Travel signal is present", "Risk policy allows low-risk products"],
      },
      {
        id: "P006",
        name: "Health Insurance",
        type: "insurance",
        score: 0.64,
        reasons: ["Broad insurance fit", "Strong customer value"],
      },
    ],
    activity: ["Lead score recalculated", "Pitch generated yesterday", "Last status: interested"],
  },
  {
    id: "CUST_10000",
    segment: "Basic Retail",
    tier: "warm",
    leadScore: 0.74,
    fraudScore: 0.10,
    riskScore: 0.18,
    topProduct: "Cashback Credit Card",
    eligibility: "eligible",
    breakdown: {
      product_match: 0.78,
      propensity: 0.63,
      recency: 0.68,
      customer_value: 0.48,
      fatigue: 0.08,
    },
    products: [
      {
        id: "P001",
        name: "Cashback Credit Card",
        type: "credit_card",
        score: 0.78,
        reasons: ["Retail spend is high", "Recent shopping frequency is strong"],
      },
      {
        id: "P005",
        name: "Flexible Savings",
        type: "saving",
        score: 0.59,
        reasons: ["Low risk score", "Active in the last 30 days"],
      },
      {
        id: "P006",
        name: "Health Insurance",
        type: "insurance",
        score: 0.53,
        reasons: ["Low fraud score", "Eligible for low-risk offer"],
      },
    ],
    activity: ["Added to cashback campaign", "No rejection in cooldown window"],
  },
  {
    id: "CUST_73241",
    segment: "Domestic Everyday",
    tier: "warm",
    leadScore: 0.66,
    fraudScore: 0.34,
    riskScore: 0.37,
    topProduct: "Health Insurance",
    eligibility: "review_low_risk_only",
    breakdown: {
      product_match: 0.68,
      propensity: 0.61,
      recency: 0.58,
      customer_value: 0.52,
      fatigue: 0.16,
    },
    products: [
      {
        id: "P006",
        name: "Health Insurance",
        type: "insurance",
        score: 0.68,
        reasons: ["Healthcare signal is present", "Fraud review allows low-risk products only"],
      },
      {
        id: "P005",
        name: "Flexible Savings",
        type: "saving",
        score: 0.55,
        reasons: ["Low-risk product", "Suitable under review policy"],
      },
    ],
    activity: ["Fraud policy: review", "High-risk products filtered"],
  },
  {
    id: "CUST_88420",
    segment: "Dormant Retail",
    tier: "cold",
    leadScore: 0.42,
    fraudScore: 0.77,
    riskScore: 0.68,
    topProduct: "Blocked",
    eligibility: "blocked_fraud",
    breakdown: {
      product_match: 0.00,
      propensity: 0.31,
      recency: 0.62,
      customer_value: 0.35,
      fatigue: 0.22,
    },
    products: [],
    activity: ["Blocked by fraud gate", "No pitch allowed"],
  },
];

let fraudAlerts = [
  {
    id: "ALERT-9912",
    userId: "CUST_88420",
    transactionId: "TX_77A93",
    severity: "high",
    score: 0.91,
    status: "block",
    summary: "Large card-not-present transaction from a new location",
    shap: {
      amount_zscore: 0.35,
      distance_from_home: 0.28,
      high_risk_merchant: 0.19,
      card_not_present: 0.14,
    },
    timeline: ["New device observed", "High-risk merchant flag triggered", "Amount exceeds recent pattern"],
  },
  {
    id: "ALERT-9844",
    userId: "CUST_73241",
    transactionId: "TX_102BC",
    severity: "medium",
    score: 0.54,
    status: "review",
    summary: "Velocity and merchant risk signals require manual review",
    shap: {
      tx_count_1h: 0.23,
      merchant_category_anomaly: 0.18,
      channel_switch: 0.11,
      amount_zscore: 0.09,
    },
    timeline: ["Three transactions within one hour", "Channel changed from mobile to web", "Manual review required"],
  },
  {
    id: "ALERT-9731",
    userId: "CUST_11409",
    transactionId: "TX_88DD1",
    severity: "low",
    score: 0.29,
    status: "pass",
    summary: "Mild geo deviation with low model confidence",
    shap: {
      distance_from_home: 0.13,
      card_not_present: 0.07,
      amount_zscore: 0.05,
    },
    timeline: ["Geo deviation observed", "Amount remains within normal range", "Policy decision: pass"],
  },
];

const state = {
  view: "recommendation",
  selectedLeadId: leads[0].id,
  selectedAlertId: fraudAlerts[0].id,
  tierFilter: "all",
  severityFilter: "all",
  search: "",
};

const elements = {
  viewTitle: document.querySelector("#view-title"),
  navTabs: document.querySelectorAll(".nav-tab"),
  recommendationView: document.querySelector("#recommendation-view"),
  fraudView: document.querySelector("#fraud-view"),
  customerSearch: document.querySelector("#customer-search"),
  refreshButton: document.querySelector("#refresh-button"),
  hotCount: document.querySelector("#hot-count"),
  eligibleCount: document.querySelector("#eligible-count"),
  topProductMetric: document.querySelector("#top-product-metric"),
  blockedCount: document.querySelector("#blocked-count"),
  tierFilter: document.querySelector("#tier-filter"),
  leadQueue: document.querySelector("#lead-queue"),
  customerId: document.querySelector("#customer-id"),
  customerSegment: document.querySelector("#customer-segment"),
  leadTier: document.querySelector("#lead-tier"),
  leadScore: document.querySelector("#lead-score"),
  fraudScore: document.querySelector("#fraud-score"),
  riskScore: document.querySelector("#risk-score"),
  leadBreakdown: document.querySelector("#lead-breakdown"),
  recommendationList: document.querySelector("#recommendation-list"),
  pitchBox: document.querySelector("#pitch-box"),
  generatePitch: document.querySelector("#generate-pitch"),
  markConsulted: document.querySelector("#mark-consulted"),
  activityList: document.querySelector("#activity-list"),
  severityFilter: document.querySelector("#severity-filter"),
  fraudAlertList: document.querySelector("#fraud-alert-list"),
  alertId: document.querySelector("#alert-id"),
  alertSummary: document.querySelector("#alert-summary"),
  alertSeverity: document.querySelector("#alert-severity"),
  gaugeScore: document.querySelector("#gauge-score"),
  policyDecision: document.querySelector("#policy-decision"),
  policyNote: document.querySelector("#policy-note"),
  shapBars: document.querySelector("#shap-bars"),
  fraudTimeline: document.querySelector("#fraud-timeline"),
  confirmFraud: document.querySelector("#confirm-fraud"),
  falsePositive: document.querySelector("#false-positive"),
};

function formatScore(value) {
  return Number(value).toFixed(2);
}

function titleCase(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function currentLead() {
  return leads.find((lead) => lead.id === state.selectedLeadId) || leads[0];
}

function currentAlert() {
  return fraudAlerts.find((alert) => alert.id === state.selectedAlertId) || fraudAlerts[0];
}

function setView(view) {
  state.view = view;
  elements.viewTitle.textContent = view === "fraud" ? "Fraud Review Workspace" : "Recommendation Workspace";
  elements.recommendationView.classList.toggle("active", view === "recommendation");
  elements.fraudView.classList.toggle("active", view === "fraud");
  elements.navTabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.view === view));
}

function renderSummary() {
  const hot = leads.filter((lead) => lead.tier === "hot").length;
  const eligible = leads.filter((lead) => lead.eligibility === "eligible").length;
  const blocked = leads.filter((lead) => lead.eligibility === "blocked_fraud").length;
  const topProduct = leads
    .filter((lead) => lead.topProduct !== "Blocked")
    .reduce((acc, lead) => {
      acc[lead.topProduct] = (acc[lead.topProduct] || 0) + 1;
      return acc;
    }, {});
  const topProductName = Object.entries(topProduct).sort((a, b) => b[1] - a[1])[0]?.[0] || "--";

  elements.hotCount.textContent = hot;
  elements.eligibleCount.textContent = eligible;
  elements.blockedCount.textContent = blocked;
  elements.topProductMetric.textContent = topProductName;
}

async function loadBackendData() {
  if (window.location.protocol === "file:") {
    renderAll();
    return;
  }

  try {
    const response = await fetch("/api/dashboard", {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(`Dashboard API returned ${response.status}`);
    }

    const payload = await response.json();
    if (Array.isArray(payload.leads) && payload.leads.length > 0) {
      leads = payload.leads;
      state.selectedLeadId = leads[0].id;
    }
    if (Array.isArray(payload.fraudAlerts) && payload.fraudAlerts.length > 0) {
      fraudAlerts = payload.fraudAlerts;
      state.selectedAlertId = fraudAlerts[0].id;
    }
  } catch (error) {
    console.warn("Using local dashboard fallback data.", error);
  }

  renderAll();
}

function filteredLeads() {
  const query = state.search.toLowerCase();
  return leads.filter((lead) => {
    const matchesTier = state.tierFilter === "all" || lead.tier === state.tierFilter;
    const matchesSearch = [lead.id, lead.segment, lead.topProduct]
      .join(" ")
      .toLowerCase()
      .includes(query);
    return matchesTier && matchesSearch;
  });
}

function renderLeadQueue() {
  const queue = filteredLeads().sort((a, b) => b.leadScore - a.leadScore);
  elements.leadQueue.innerHTML = "";

  if (queue.length === 0) {
    elements.leadQueue.innerHTML = '<div class="queue-card">No matching leads.</div>';
    return;
  }

  queue.forEach((lead) => {
    const button = document.createElement("button");
    button.className = `queue-card ${lead.id === state.selectedLeadId ? "active" : ""}`;
    button.type = "button";
    button.dataset.leadId = lead.id;
    button.innerHTML = `
      <div class="queue-topline">
        <strong>${lead.id}</strong>
        <span class="tier-pill ${lead.tier}">${lead.tier}</span>
      </div>
      <p class="queue-meta">${lead.segment} - ${lead.topProduct}</p>
      <p class="queue-meta">Lead ${formatScore(lead.leadScore)} - Fraud ${formatScore(lead.fraudScore)}</p>
    `;
    elements.leadQueue.appendChild(button);
  });
}

function renderBars(container, values) {
  container.innerHTML = "";
  Object.entries(values).forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <span>${titleCase(label)}</span>
      <div class="bar-track"><div class="bar-fill" style="width: ${Math.max(0, Math.min(value, 1)) * 100}%"></div></div>
      <strong>${formatScore(value)}</strong>
    `;
    container.appendChild(row);
  });
}

function renderCustomerDetail() {
  const lead = currentLead();
  elements.customerId.textContent = lead.id;
  elements.customerSegment.textContent = `${lead.segment} - ${lead.eligibility}`;
  elements.leadTier.textContent = lead.tier;
  elements.leadTier.className = `tier-pill ${lead.tier}`;
  elements.leadScore.textContent = formatScore(lead.leadScore);
  elements.fraudScore.textContent = formatScore(lead.fraudScore);
  elements.riskScore.textContent = formatScore(lead.riskScore);
  renderBars(elements.leadBreakdown, lead.breakdown);

  elements.recommendationList.innerHTML = "";
  if (lead.products.length === 0) {
    elements.recommendationList.innerHTML = '<div class="product-card"><strong>No products allowed</strong><p>Fraud policy blocks recommendation and pitching.</p></div>';
  } else {
    lead.products.forEach((product, index) => {
      const card = document.createElement("article");
      card.className = "product-card";
      card.innerHTML = `
        <div class="product-topline">
          <div class="product-rank">${index + 1}</div>
          <span class="score-badge">${formatScore(product.score)}</span>
        </div>
        <strong>${product.name}</strong>
        <p>${product.type} - ${product.id}</p>
        <ul class="reason-list">${product.reasons.map((reason) => `<li>${reason}</li>`).join("")}</ul>
      `;
      elements.recommendationList.appendChild(card);
    });
  }

  elements.activityList.innerHTML = lead.activity.map((item) => `<li>${item}</li>`).join("");
  elements.generatePitch.disabled = lead.fraudScore >= 0.3 || lead.products.length === 0;
  elements.pitchBox.textContent =
    lead.fraudScore >= 0.3
      ? "Pitch generation is blocked while the account is in fraud review."
      : "Select Generate pitch to prepare an advisor script.";
}

function filteredAlerts() {
  return fraudAlerts.filter((alert) => {
    const matchesSeverity = state.severityFilter === "all" || alert.severity === state.severityFilter;
    const matchesSearch = [alert.id, alert.userId, alert.transactionId, alert.summary]
      .join(" ")
      .toLowerCase()
      .includes(state.search.toLowerCase());
    return matchesSeverity && matchesSearch;
  });
}

function renderFraudAlerts() {
  elements.fraudAlertList.innerHTML = "";
  filteredAlerts().forEach((alert) => {
    const button = document.createElement("button");
    button.className = `alert-card ${alert.id === state.selectedAlertId ? "active" : ""}`;
    button.type = "button";
    button.dataset.alertId = alert.id;
    button.innerHTML = `
      <div class="alert-topline">
        <strong>${alert.id}</strong>
        <span class="status-pill ${alert.status}">${alert.status}</span>
      </div>
      <p class="alert-meta">${alert.userId} - ${alert.transactionId}</p>
      <p class="alert-meta">${alert.summary}</p>
    `;
    elements.fraudAlertList.appendChild(button);
  });
}

function renderFraudDetail() {
  const alert = currentAlert();
  elements.alertId.textContent = alert.id;
  elements.alertSummary.textContent = `${alert.userId} - ${alert.summary}`;
  elements.alertSeverity.textContent = alert.severity;
  elements.alertSeverity.className = `tier-pill ${alert.severity === "high" ? "danger" : alert.severity === "medium" ? "warm" : "cold"}`;
  elements.gaugeScore.textContent = formatScore(alert.score);

  const decision = alert.score >= 0.7 ? "BLOCK" : alert.score >= 0.3 ? "REVIEW" : "PASS";
  elements.policyDecision.textContent = decision;
  elements.policyNote.textContent =
    decision === "BLOCK"
      ? "No recommendation or pitch allowed"
      : decision === "REVIEW"
        ? "Low-risk products only"
        : "Recommendation flow allowed";

  renderBars(elements.shapBars, alert.shap);
  elements.fraudTimeline.innerHTML = alert.timeline.map((item) => `<li>${item}</li>`).join("");
}

function generatePitch() {
  const lead = currentLead();
  if (lead.fraudScore >= 0.3 || lead.products.length === 0) {
    elements.pitchBox.textContent = "Pitch generation is blocked by fraud guardrails.";
    return;
  }

  const product = lead.products[0];
  elements.pitchBox.textContent = `Hello, this is a quick note for ${lead.id}. Based on recent activity, ${product.name} is the strongest fit today. The main reason is ${product.reasons[0].toLowerCase()}, and the account is currently eligible under the fraud policy. I would position this as a practical offer, keep the conversation concise, and invite the customer to review the benefit details before making any decision.`;
}

function markConsulted() {
  const lead = currentLead();
  lead.activity.unshift("Consultation marked just now");
  lead.breakdown.fatigue = Math.min(1, lead.breakdown.fatigue + 0.12);
  lead.leadScore = Math.max(0, lead.leadScore - 0.08);
  lead.tier = lead.leadScore > 0.85 ? "hot" : lead.leadScore >= 0.6 ? "warm" : "cold";
  renderAll();
}

function attachEvents() {
  elements.navTabs.forEach((tab) => {
    tab.addEventListener("click", () => setView(tab.dataset.view));
  });

  elements.customerSearch.addEventListener("input", (event) => {
    state.search = event.target.value;
    renderLeadQueue();
    renderFraudAlerts();
  });

  elements.refreshButton.addEventListener("click", () => {
    loadBackendData();
  });

  elements.tierFilter.addEventListener("change", (event) => {
    state.tierFilter = event.target.value;
    renderLeadQueue();
  });

  elements.leadQueue.addEventListener("click", (event) => {
    const card = event.target.closest("[data-lead-id]");
    if (!card) return;
    state.selectedLeadId = card.dataset.leadId;
    renderLeadQueue();
    renderCustomerDetail();
  });

  elements.generatePitch.addEventListener("click", generatePitch);
  elements.markConsulted.addEventListener("click", markConsulted);

  elements.severityFilter.addEventListener("change", (event) => {
    state.severityFilter = event.target.value;
    renderFraudAlerts();
  });

  elements.fraudAlertList.addEventListener("click", (event) => {
    const card = event.target.closest("[data-alert-id]");
    if (!card) return;
    state.selectedAlertId = card.dataset.alertId;
    renderFraudAlerts();
    renderFraudDetail();
  });

  elements.confirmFraud.addEventListener("click", () => {
    const alert = currentAlert();
    alert.status = "block";
    alert.score = Math.max(alert.score, 0.82);
    renderFraudAlerts();
    renderFraudDetail();
  });

  elements.falsePositive.addEventListener("click", () => {
    const alert = currentAlert();
    alert.status = "pass";
    alert.score = Math.min(alert.score, 0.18);
    renderFraudAlerts();
    renderFraudDetail();
  });
}

function renderAll() {
  renderSummary();
  renderLeadQueue();
  renderCustomerDetail();
  renderFraudAlerts();
  renderFraudDetail();
}

attachEvents();
renderAll();
loadBackendData();
