const regimeEl = document.getElementById("regime");
const regimeBlurbEl = document.getElementById("regime-blurb");
const confidenceEl = document.getElementById("confidence");
const timestampEl = document.getElementById("timestamp");
const liveClockEl = document.getElementById("live-clock");
const userBadgeEl = document.getElementById("user-badge");
const stateBreadthEl = document.getElementById("state-breadth");
const stateVolatilityEl = document.getElementById("state-volatility");
const stateTrendEl = document.getElementById("state-trend");
const stateConfirmationEl = document.getElementById("state-confirmation");
const classesEl = document.getElementById("classes");
const thresholdsEl = document.getElementById("thresholds");
const trainingSummaryEl = document.getElementById("training-summary");
const featureImportanceEl = document.getElementById("feature-importance");
const driversListEl = document.getElementById("drivers-list");
const probabilityListEl = document.getElementById("probability-list");
const ringFillEl = document.getElementById("ring-fill");
const transitionListEl = document.getElementById("transition-list");
const meaningPanelEl = document.getElementById("meaning-panel");
const playbookPanelEl = document.getElementById("playbook-panel");
const glossaryPanelEl = document.getElementById("glossary-panel");
const changesPanelEl = document.getElementById("changes-panel");
const supportPanelEl = document.getElementById("support-panel");
const conflictPanelEl = document.getElementById("conflict-panel");
const headlineStripEl = document.getElementById("headline-strip");
const leaderLaggardListEl = document.getElementById("leader-laggard-list");
const alertsListEl = document.getElementById("alerts-list");
const sectorListEl = document.getElementById("sector-list");
const marketPanelsEl = document.getElementById("market-panels");
const marketDetailEl = document.getElementById("market-detail");
const signalBoardEl = document.getElementById("signal-board");
const signalDetailEl = document.getElementById("signal-detail");
const watchlistFormEl = document.getElementById("watchlist-form");
const watchlistSymbolEl = document.getElementById("watchlist-symbol");
const watchlistListEl = document.getElementById("watchlist-list");
const watchlistIntelEl = document.getElementById("watchlist-intel");
const watchlistNewsEl = document.getElementById("watchlist-news");
const catalystCalendarEl = document.getElementById("catalyst-calendar");
const watchlistDetailEl = document.getElementById("watchlist-detail");
const premarketBriefingEl = document.getElementById("premarket-briefing");
const premarketFocusEl = document.getElementById("premarket-focus");
const briefingCatalystsEl = document.getElementById("briefing-catalysts");
const briefingHistoryEl = document.getElementById("briefing-history");
const deliveryFormEl = document.getElementById("delivery-form");
const subscriptionFormEl = document.getElementById("subscription-form");
const subscriptionTierEl = document.getElementById("subscription-tier");
const subscriptionSummaryEl = document.getElementById("subscription-summary");
const subscriptionTiersEl = document.getElementById("subscription-tiers");
const sharedWorkspaceSummaryEl = document.getElementById("shared-workspace-summary");
const sharedWorkspaceDetailEl = document.getElementById("shared-workspace-detail");
const sharedWorkspaceCreateFormEl = document.getElementById("shared-workspace-create-form");
const sharedWorkspaceJoinFormEl = document.getElementById("shared-workspace-join-form");
const sharedWorkspaceWatchlistFormEl = document.getElementById("shared-workspace-watchlist-form");
const sharedWorkspaceNoteFormEl = document.getElementById("shared-workspace-note-form");
const sharedWorkspaceBriefingButtonEl = document.getElementById("shared-workspace-briefing-button");
const sharedWorkspaceNameEl = document.getElementById("shared-workspace-name");
const sharedWorkspaceCodeEl = document.getElementById("shared-workspace-code");
const sharedWorkspaceSymbolEl = document.getElementById("shared-workspace-symbol");
const sharedWorkspaceNoteEl = document.getElementById("shared-workspace-note");
const deliveryEmailEl = document.getElementById("delivery-email");
const deliveryWebhookEnabledEl = document.getElementById("delivery-webhook-enabled");
const deliveryWebhookUrlEl = document.getElementById("delivery-webhook-url");
const deliveryCadenceEl = document.getElementById("delivery-cadence");
const deliveryStatusEl = document.getElementById("delivery-status");
const newsListEl = document.getElementById("news-list");
const newsDetailEl = document.getElementById("news-detail");
const newsSearchEl = document.getElementById("news-search");
const newsFiltersEl = document.getElementById("news-filters");
const viewTitleEl = document.getElementById("view-title");
const refreshButtonEl = document.getElementById("refresh-button");
const commandButtonEl = document.getElementById("command-button");
const logoutButtonEl = document.getElementById("logout-button");
const paletteEl = document.getElementById("command-palette");
const paletteInputEl = document.getElementById("palette-input");
const paletteResultsEl = document.getElementById("palette-results");
const navItems = [...document.querySelectorAll(".nav-item")];
const views = [...document.querySelectorAll(".view")];

let allNewsItems = [];
let allMarketPanels = [];
let allSignals = [];
let allAlerts = [];
let allWatchlist = [];
let allSectors = [];
let latestMarketState = null;
let watchlistInsights = [];
let watchlistNews = [];
let catalystCalendar = [];
let selectedWatchlistSymbol = null;
let deliveryPreferences = null;
let currentUser = null;
let subscriptionTiers = [];
let sharedWorkspace = null;
let activeNewsSource = "All";
let selectedNewsIndex = 0;
let selectedMarketSymbol = null;
let selectedSignalSymbol = null;

const regimeCopy = {
  RiskOn: {
    blurb: "Risk appetite is leading. Trend and momentum conditions are supportive.",
    briefing:
      "This regime suggests a constructive tape. Equities typically behave better when volatility stays contained and directional strength persists across the market complex.",
    color: "#7dffa1",
    meaning:
      "RiskOn means the market is acting like investors are comfortable taking risk. Stocks and cyclical assets usually behave better, and volatility is not dominating the tape.",
    use:
      "Use this as a filter for long setups, momentum names, and higher-beta trades. You still want confirmation from breadth, sectors, and catalysts before pressing size.",
    avoid:
      "Do not treat RiskOn as a guarantee that every stock will rise. It is a market backdrop, not a trade entry signal.",
  },
  RiskOff: {
    blurb: "Defensive positioning is dominating. Capital preservation is the priority.",
    briefing:
      "This regime signals a more cautious environment. Markets in this state often reward defensive assets while cyclical exposure and leverage become less forgiving.",
    color: "#ff6b7a",
    meaning:
      "RiskOff means the market is behaving defensively. Traders are generally reducing exposure, rotating away from aggressive names, or demanding more caution.",
    use:
      "Use this as a filter to reduce chase on longs, tighten risk, and focus on defensive leadership or short setups with confirmation.",
    avoid:
      "Do not assume everything is bearish at once. RiskOff often creates sharp squeezes and countertrend rallies.",
  },
  HighVol: {
    blurb: "Instability is elevated. Fast repricing and larger swings are in control.",
    briefing:
      "This is the unstable state. Volatility-driven moves can overwhelm slower signals, so traders generally expect wider ranges, faster rotations, and more fragile sentiment.",
    color: "#ffb347",
    meaning:
      "HighVol means the market is unstable enough that normal trend signals are less reliable. Large swings and rapid sentiment shifts matter more than smooth continuation.",
    use:
      "Use smaller size, faster timeframes, and tighter risk controls. Focus on liquidity, volatility, and reaction levels instead of assuming trend persistence.",
    avoid:
      "Do not over-trust slow-moving indicators or oversized positions when volatility is in control.",
  },
};

const glossaryEntries = [
  {
    term: "RiskOn",
    definition: "A supportive environment where traders are generally willing to own risk assets such as equities and growth-sensitive names.",
  },
  {
    term: "RiskOff",
    definition: "A defensive environment where capital preservation matters more and traders often prefer safer assets or reduced exposure.",
  },
  {
    term: "HighVol",
    definition: "An unstable environment where volatility is elevated and price action can override slower trend signals.",
  },
  {
    term: "Breadth",
    definition: "A quick read on how many parts of the market are participating. Strong breadth means the move is being confirmed by more than a few names.",
  },
  {
    term: "Confirmation",
    definition: "Whether other assets and sectors agree with the regime call. Strong confirmation makes the signal more credible.",
  },
];

const commands = [
  { label: "Go to Monitor", description: "Open the main regime workspace.", run: () => setView("monitor") },
  { label: "Go to Markets", description: "Inspect cross-asset trend panels.", run: () => setView("markets") },
  { label: "Go to Briefing", description: "Open the personalized pre-market plan.", run: () => setView("briefing") },
  { label: "Go to Signals", description: "View bullish and bearish stock indicators.", run: () => setView("signals") },
  { label: "Open Watchlist", description: "Jump to the signals workspace and manage saved tickers.", run: () => setView("signals") },
  { label: "Go to Desk", description: "Open the shared workspace and team coordination view.", run: () => setView("desk") },
  { label: "Go to News", description: "Open the market news stream.", run: () => setView("news") },
  { label: "Go to System", description: "Inspect model, billing, and system settings.", run: () => setView("system") },
  { label: "Open Delivery Settings", description: "Configure briefing cadence and webhook delivery.", run: () => setView("system") },
  { label: "Refresh Terminal", description: "Reload model, market, signal, and news data.", run: () => boot() },
  { label: "Open API Docs", description: "Open FastAPI documentation in a new tab.", run: () => window.open("/docs", "_blank", "noreferrer") },
];

function formatTimestamp(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value).toUpperCase()
    : `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return `${(value * 100).toFixed(2)}%`;
}

function formatPrice(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return value === 0 ? "Live" : value.toFixed(2);
}

function signClass(value) {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function stanceClass(value) {
  if (value === "Bullish") return "stance-bullish";
  if (value === "Bearish") return "stance-bearish";
  return "stance-neutral";
}

function updateClock() {
  liveClockEl.textContent = new Date().toLocaleTimeString();
}

function updateRing(confidence, color) {
  const circumference = 301.59;
  ringFillEl.style.strokeDashoffset = `${circumference * (1 - confidence)}`;
  ringFillEl.style.stroke = color;
}

function renderProbabilities(probabilities) {
  probabilityListEl.innerHTML = "";
  Object.entries(probabilities)
    .sort((a, b) => b[1] - a[1])
    .forEach(([label, value]) => {
      const wrapper = document.createElement("div");
      wrapper.className = "probability-item";
      wrapper.innerHTML = `
        <div class="probability-head">
          <span>${label}</span>
          <strong>${(value * 100).toFixed(1)}%</strong>
        </div>
        <div class="probability-bar"><div style="width:${(value * 100).toFixed(1)}%"></div></div>
      `;
      probabilityListEl.appendChild(wrapper);
    });
}

function sparklinePoints(values) {
  if (!values.length) return "";
  const width = 220;
  const height = 56;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    })
    .join(" ");
}

function renderTransitions(transitions) {
  transitionListEl.innerHTML = "";
  transitions.forEach((point) => {
    const row = document.createElement("div");
    row.className = "history-item";
    row.innerHTML = `
      <span>${point.started_at} to ${point.ended_at}</span>
      <strong>${point.regime}</strong>
      <span>${point.duration_days}d / ${Math.round(point.average_confidence * 100)}%</span>
    `;
    transitionListEl.appendChild(row);
  });
}

function renderHeadlineStrip(items) {
  headlineStripEl.innerHTML = "";
  items.slice(0, 3).forEach((item) => {
    const card = document.createElement("button");
    card.className = "headline-card";
    card.innerHTML = `
      <h3>${item.title}</h3>
      <p>${item.source} • ${item.tags.join(" / ")}</p>
    `;
    card.addEventListener("click", () => {
      activeNewsSource = "All";
      selectedNewsIndex = allNewsItems.findIndex((candidate) => candidate.title === item.title);
      renderNewsFilters(allNewsItems);
      renderNews(allNewsItems);
      setView("news");
    });
    headlineStripEl.appendChild(card);
  });
}

function renderSectors(sectors) {
  sectorListEl.innerHTML = "";
  sectors.forEach((sector) => {
    const node = document.createElement("div");
    node.className = "sector-card";
    node.innerHTML = `
      <strong>${sector.label} (${sector.symbol})</strong>
      <p>${sector.signal}</p>
      <p class="${signClass(sector.change_1d)}">1D ${formatPercent(sector.change_1d)}</p>
      <p class="${signClass(sector.change_20d ?? 0)}">20D ${formatPercent(sector.change_20d)}</p>
    `;
    sectorListEl.appendChild(node);
  });
}

function renderAlerts(alerts) {
  alertsListEl.innerHTML = "";
  alerts.forEach((alert) => {
    const node = document.createElement("div");
    node.className = `alert-item ${alert.severity}`;
    node.innerHTML = `
      <strong>${alert.title}</strong>
      <p>${alert.message}</p>
      <p>${alert.symbol ? `Symbol: ${alert.symbol}` : `Severity: ${alert.severity}`}</p>
    `;
    alertsListEl.appendChild(node);
  });
}

function renderDrivers(drivers, warnings) {
  driversListEl.innerHTML = "";
  drivers.forEach((driver) => {
    const node = document.createElement("div");
    node.className = "alert-item";
    node.innerHTML = `
      <strong>${driver.label}</strong>
      <p class="${driver.tone}">${driver.value}</p>
    `;
    driversListEl.appendChild(node);
  });
  warnings.forEach((warning) => {
    const node = document.createElement("div");
    node.className = "alert-item medium";
    node.innerHTML = `<strong>Warning</strong><p>${warning}</p>`;
    driversListEl.appendChild(node);
  });
}

function renderMeaning(regime, state) {
  const copy = regimeCopy[regime] || {
    meaning: "This is the current market backdrop produced by the model.",
    use: "Use it as context before deciding which setups deserve attention.",
    avoid: "Do not treat it as a standalone buy or sell signal.",
  };
  meaningPanelEl.innerHTML = `
    <p>${copy.meaning}</p>
    <p>${state.summary}</p>
  `;
  playbookPanelEl.className = "story-list plain";
  playbookPanelEl.innerHTML = `
    <h4>Use It Like This</h4>
    <ul>
      <li>${copy.use}</li>
      <li>Check leaders, laggards, sector breadth, and catalysts before acting.</li>
      <li>If the transition history is short-lived, assume the market state is less settled.</li>
    </ul>
    <h4>Do Not Assume</h4>
    <ul>
      <li>${copy.avoid}</li>
      <li>High confidence does not mean certainty. It means the current inputs fit the model strongly.</li>
    </ul>
  `;
}

function renderGlossary() {
  glossaryPanelEl.innerHTML = "";
  glossaryEntries.forEach((entry) => {
    const node = document.createElement("div");
    node.className = "glossary-item";
    node.innerHTML = `
      <strong>${entry.term}</strong>
      <p>${entry.definition}</p>
    `;
    glossaryPanelEl.appendChild(node);
  });
}

function renderBulletPanel(element, title, items, emptyText) {
  element.className = "story-list plain";
  element.innerHTML = `
    <h4>${title}</h4>
    <ul>${(items.length ? items : [emptyText]).map((item) => `<li>${item}</li>`).join("")}</ul>
  `;
}

function renderLeaderLaggards(state) {
  leaderLaggardListEl.innerHTML = "";
  const sections = [
    { title: "Leaders", items: state.leaders, className: "positive" },
    { title: "Laggards", items: state.laggards, className: "negative" },
  ];
  sections.forEach((section) => {
    const block = document.createElement("div");
    block.className = "story-list";
    block.innerHTML = `
      <h4>${section.title}</h4>
      <ul>${section.items
        .map(
          (item) =>
            `<li><span>${item.label} (${item.symbol})</span> <strong class="${section.className}">${formatPercent(item.value)}</strong></li>`
        )
        .join("")}</ul>
    `;
    leaderLaggardListEl.appendChild(block);
  });
}

function renderMarketPanels(panels) {
  marketPanelsEl.innerHTML = "";
  if (!selectedMarketSymbol && panels.length) selectedMarketSymbol = panels[0].symbol;

  panels.forEach((panel) => {
    const trendClass =
      panel.trend.at(-1) > panel.trend[0] ? "trend-up" : panel.trend.at(-1) < panel.trend[0] ? "trend-down" : "trend-neutral";
    const card = document.createElement("button");
    card.className = `market-card${panel.symbol === selectedMarketSymbol ? " is-active" : ""}`;
    card.innerHTML = `
      <div class="market-meta">
        <strong>${panel.label}</strong>
        <span>${panel.symbol}</span>
      </div>
      <h3>${formatPrice(panel.price)}</h3>
      <p class="${signClass(panel.change_1d)}">1D ${formatPercent(panel.change_1d)}</p>
      <p class="${signClass(panel.change_20d ?? 0)}">20D ${formatPercent(panel.change_20d)}</p>
      <p>${panel.signal}</p>
      <svg class="sparkline ${trendClass}" viewBox="0 0 220 56" preserveAspectRatio="none">
        <polyline points="${sparklinePoints(panel.trend)}"></polyline>
      </svg>
    `;
    card.addEventListener("click", () => {
      selectedMarketSymbol = panel.symbol;
      renderMarketPanels(allMarketPanels);
      renderMarketDetail(panel);
    });
    marketPanelsEl.appendChild(card);
  });

  const selected = panels.find((panel) => panel.symbol === selectedMarketSymbol);
  if (selected) renderMarketDetail(selected);
}

function renderMarketDetail(panel) {
  marketDetailEl.innerHTML = `
    <h3>${panel.label} (${panel.symbol})</h3>
    <p>The current market signal for this instrument is <strong>${panel.signal}</strong>. This panel uses short and medium horizon returns plus trend persistence to show whether the move is constructive or deteriorating.</p>
    <div class="market-meta">
      <span>Price ${formatPrice(panel.price)}</span>
      <span class="${signClass(panel.change_1d)}">1D ${formatPercent(panel.change_1d)}</span>
    </div>
    <div class="market-meta">
      <span class="${signClass(panel.change_5d ?? 0)}">5D ${formatPercent(panel.change_5d)}</span>
      <span class="${signClass(panel.change_20d ?? 0)}">20D ${formatPercent(panel.change_20d)}</span>
    </div>
    <svg class="sparkline ${panel.signal === "Bullish" || panel.signal === "Calm" ? "trend-up" : panel.signal === "Bearish" || panel.signal === "Stress" ? "trend-down" : "trend-neutral"}" viewBox="0 0 220 56" preserveAspectRatio="none">
      <polyline points="${sparklinePoints(panel.trend)}"></polyline>
    </svg>
  `;
}

function renderSignalCards(signals) {
  signalBoardEl.innerHTML = "";
  if (!selectedSignalSymbol && signals.length) selectedSignalSymbol = signals[0].symbol;

  signals.forEach((signal, index) => {
    const markup = `
      <div class="signal-meta">
        <strong>${signal.label}</strong>
        <span>${signal.symbol}</span>
      </div>
      <h3 class="${stanceClass(signal.stance)}">${signal.stance}</h3>
      <p>Score ${Math.round(signal.score * 100)} / 100</p>
      <p class="${signClass(signal.change_20d ?? 0)}">20D ${formatPercent(signal.change_20d)}</p>
    `;

    const card = document.createElement("button");
    card.className = `signal-card${signal.symbol === selectedSignalSymbol ? " is-active" : ""}`;
    card.innerHTML = markup;
    card.addEventListener("click", () => {
      selectedSignalSymbol = signal.symbol;
      renderSignalCards(allSignals);
      renderSignalDetail(signal);
    });
    signalBoardEl.appendChild(card);

  });

  const selected = signals.find((signal) => signal.symbol === selectedSignalSymbol);
  if (selected) renderSignalDetail(selected);
}

function renderWatchlist(items) {
  watchlistListEl.innerHTML = "";
  if (!items.length) {
    watchlistListEl.innerHTML = `<div class="watchlist-item"><div><strong>No saved symbols</strong><span>Add names you want the alert engine to prioritize.</span></div></div>`;
    watchlistDetailEl.innerHTML = `
      <div class="story-list">
        <h4>No symbol selected</h4>
        <ul><li>Add a watchlist ticker to inspect details.</li></ul>
      </div>
    `;
    return;
  }
  if (!selectedWatchlistSymbol || !items.some((item) => item.symbol === selectedWatchlistSymbol)) {
    selectedWatchlistSymbol = items[0].symbol;
  }

  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = `watchlist-item${item.symbol === selectedWatchlistSymbol ? " is-active" : ""}`;
    row.innerHTML = `
      <div>
        <strong>${item.symbol}</strong>
        <span>${item.label}</span>
      </div>
      <button type="button" data-symbol="${item.symbol}">Remove</button>
    `;
    row.querySelector("div").addEventListener("click", async () => {
      selectedWatchlistSymbol = item.symbol;
      renderWatchlist(allWatchlist);
      await loadWatchlistDetail(item.symbol);
    });
    row.querySelector("button").addEventListener("click", async () => {
      await fetch(`/watchlist/${item.symbol}`, { method: "DELETE" });
      await loadWatchlist();
      const intelResponse = await fetch("/watchlist/intelligence");
      if (intelResponse.ok) {
        watchlistInsights = await intelResponse.json();
        renderWatchlistIntelligence(watchlistInsights);
      }
      const watchlistNewsResponse = await fetch("/watchlist/news?limit=6");
      if (watchlistNewsResponse.ok) {
        watchlistNews = await watchlistNewsResponse.json();
        renderWatchlistNews(watchlistNews);
        renderNewsFilters(allNewsItems);
        renderNews(allNewsItems);
      }
      const catalystResponse = await fetch("/calendar/catalysts?limit=6");
      if (catalystResponse.ok) {
        catalystCalendar = await catalystResponse.json();
        renderCatalystCalendar(catalystCalendar);
      }
      await loadWatchlistDetail();
      await loadAlerts();
    });
    watchlistListEl.appendChild(row);
  });
}

function renderWatchlistDetail(detail) {
  if (!detail) {
    watchlistDetailEl.innerHTML = `
      <div class="story-list">
        <h4>No symbol selected</h4>
        <ul><li>Select a watchlist ticker to inspect details.</li></ul>
      </div>
    `;
    return;
  }

  const relatedNewsItems = (detail.related_news || [])
    .map(
      (article) =>
        `<li><a class="detail-link" href="${article.url}" target="_blank" rel="noreferrer">${article.title}</a> <span>${article.source}</span></li>`
    )
    .join("");
  const calendarItems = (detail.calendar_events || [])
    .map((event) => `<li>${event.timing} • ${event.title} (${event.category})</li>`)
    .join("");

  watchlistDetailEl.innerHTML = `
    <div class="story-list">
      <h4>${detail.label} (${detail.symbol})</h4>
      <ul>
        <li><strong>${detail.stance}</strong>: ${detail.summary}</li>
        <li>Score ${detail.score !== null && detail.score !== undefined ? Math.round(detail.score * 100) : "--"}/100</li>
        <li>Price ${formatPrice(detail.price)} • 1D ${formatPercent(detail.change_1d)} • 20D ${formatPercent(detail.change_20d)}</li>
      </ul>
    </div>
    <div class="story-list">
      <h4>Drivers</h4>
      <ul>${(detail.reasons || []).map((reason) => `<li>${reason}</li>`).join("") || "<li>No drivers available.</li>"}</ul>
    </div>
    <div class="story-list">
      <h4>Related News</h4>
      <ul>${relatedNewsItems || "<li>No related watchlist headlines found.</li>"}</ul>
    </div>
    <div class="story-list">
      <h4>Calendar</h4>
      <ul>${calendarItems || "<li>No calendar items matched this symbol yet.</li>"}</ul>
    </div>
  `;
}

async function loadWatchlistDetail(symbol = selectedWatchlistSymbol) {
  if (!symbol) {
    renderWatchlistDetail(null);
    return;
  }
  const response = await fetch(`/watchlist/${symbol}/detail`);
  if (!response.ok) {
    renderWatchlistDetail(null);
    return;
  }
  renderWatchlistDetail(await response.json());
}

function renderWatchlistIntelligence(items) {
  watchlistIntelEl.innerHTML = "";
  if (!items.length) {
    watchlistIntelEl.innerHTML = `
      <div class="story-list">
        <h4>No watchlist intelligence yet</h4>
        <ul><li>Add symbols to generate personalized pre-market context.</li></ul>
      </div>
    `;
    return;
  }

  items.forEach((item) => {
    const node = document.createElement("div");
    node.className = "story-list";
    const metrics = [
      item.score !== null && item.score !== undefined ? `Score ${Math.round(item.score * 100)}/100` : null,
      item.price !== null && item.price !== undefined ? `Price ${formatPrice(item.price)}` : null,
      item.change_1d !== null && item.change_1d !== undefined ? `1D ${formatPercent(item.change_1d)}` : null,
      item.change_20d !== null && item.change_20d !== undefined ? `20D ${formatPercent(item.change_20d)}` : null,
    ]
      .filter(Boolean)
      .join(" • ");
    const reasonItems = (item.reasons || []).slice(0, 2).map((reason) => `<li>${reason}</li>`).join("");
    const relatedNewsItems = (item.related_news || [])
      .slice(0, 3)
      .map(
        (article) =>
          `<li><a class="detail-link" href="${article.url}" target="_blank" rel="noreferrer">${article.title}</a> <span>${article.source}</span></li>`
      )
      .join("");
    node.innerHTML = `
      <h4>${item.label} (${item.symbol})</h4>
      <ul>
        <li><strong>${item.stance}</strong>: ${item.summary}</li>
        ${metrics ? `<li>${metrics}</li>` : ""}
        ${reasonItems}
        <li>${item.catalyst ? `Catalyst: ${item.catalyst}` : "No direct headline catalyst found."}</li>
        ${relatedNewsItems ? `<li><strong>Related News</strong></li>${relatedNewsItems}` : ""}
      </ul>
    `;
    watchlistIntelEl.appendChild(node);
  });
}

function renderWatchlistNews(items) {
  watchlistNewsEl.innerHTML = "";
  if (!items.length) {
    watchlistNewsEl.innerHTML = `
      <div class="story-list">
        <h4>No watchlist headlines yet</h4>
        <ul><li>Add symbols or wait for related headlines to appear in the feed.</li></ul>
      </div>
    `;
    return;
  }

  items.forEach((item) => {
    const node = document.createElement("div");
    node.className = "story-list";
    node.innerHTML = `
      <h4>${item.title}</h4>
      <ul>
        <li>${item.source} • ${item.tags.join(" / ")}</li>
        <li>Matched: ${item.matched_symbols.join(", ")}</li>
        <li><a class="detail-link" href="${item.url}" target="_blank" rel="noreferrer">Open Source</a></li>
      </ul>
    `;
    watchlistNewsEl.appendChild(node);
  });
}

function renderCatalystCalendar(items, targetEl = catalystCalendarEl) {
  targetEl.innerHTML = "";
  if (!items.length) {
    targetEl.innerHTML = `
      <div class="story-list">
        <h4>No catalyst windows loaded</h4>
        <ul><li>The calendar will populate from session checkpoints and watchlist headlines.</li></ul>
      </div>
    `;
    return;
  }

  items.forEach((item) => {
    const node = document.createElement("div");
    node.className = "story-list";
    node.innerHTML = `
      <h4>${item.title}</h4>
      <ul>
        <li>${item.category} • ${item.timing}${item.verified ? " • Verified" : ""}</li>
        <li>${item.detail}</li>
        ${item.source ? `<li>Source: ${item.source}</li>` : ""}
        ${item.symbols?.length ? `<li>Symbols: ${item.symbols.join(", ")}</li>` : ""}
      </ul>
    `;
    targetEl.appendChild(node);
  });
}

function renderBriefingHistory(items) {
  briefingHistoryEl.innerHTML = "";
  if (!items.length) {
    briefingHistoryEl.innerHTML = `
      <div class="story-list">
        <h4>No saved briefings yet</h4>
        <ul><li>Open the pre-market briefing workspace to start building a history.</li></ul>
      </div>
    `;
    return;
  }
  items.forEach((item) => {
    const node = document.createElement("div");
    node.className = "story-list";
    node.innerHTML = `
      <h4>${item.briefing_date}</h4>
      <ul>
        <li>${item.headline}</li>
        <li>${item.overview}</li>
      </ul>
    `;
    briefingHistoryEl.appendChild(node);
  });
}

function renderDeliveryPreferences(preferences) {
  deliveryPreferences = preferences;
  deliveryEmailEl.checked = preferences.email_enabled;
  deliveryWebhookEnabledEl.checked = preferences.webhook_enabled;
  deliveryWebhookUrlEl.value = preferences.webhook_url || "";
  deliveryCadenceEl.value = preferences.cadence;
  deliveryStatusEl.innerHTML = `
    <p>Cadence: ${preferences.cadence}</p>
    <p>Email delivery: ${preferences.email_enabled ? "enabled" : "disabled"}</p>
    <p>Webhook delivery: ${preferences.webhook_enabled ? "enabled" : "disabled"}</p>
  `;
}

function renderTrainingMetadata(training, featureImportance) {
  const metrics = training?.metrics || {};
  const classes = training?.class_distribution || {};
  const weights = training?.class_weights || {};
  const dateRange = training?.date_range || {};

  trainingSummaryEl.innerHTML = `
    <p>Coverage: ${dateRange.start || "--"} to ${dateRange.end || "--"}</p>
    <p>Rows: ${training?.rows ?? "--"} total | ${training?.train_rows ?? "--"} train | ${training?.test_rows ?? "--"} test</p>
    <p>Accuracy ${metrics.accuracy ?? "--"} | Macro F1 ${metrics.macro_f1 ?? "--"} | Weighted F1 ${metrics.weighted_f1 ?? "--"}</p>
    <p>Classes: RiskOff ${classes.RiskOff ?? "--"} | RiskOn ${classes.RiskOn ?? "--"} | HighVol ${classes.HighVol ?? "--"}</p>
    <p>Weights: RiskOff ${weights.RiskOff ?? "--"} | RiskOn ${weights.RiskOn ?? "--"} | HighVol ${weights.HighVol ?? "--"}</p>
  `;

  featureImportanceEl.innerHTML = "";
  Object.entries(featureImportance || {})
    .slice(0, 8)
    .forEach(([feature, score]) => {
      const node = document.createElement("div");
      node.className = "alert-item";
      node.innerHTML = `
        <strong>${feature}</strong>
        <p>${(score * 100).toFixed(1)}% importance</p>
      `;
      featureImportanceEl.appendChild(node);
    });
}

function renderSubscription(user, tiers) {
  const current = tiers.find((tier) => tier.tier === user.tier);
  if (!current) return;

  subscriptionSummaryEl.innerHTML = `
    <p>Current plan: ${current.label}</p>
    <p>${current.description}</p>
    <p>Watchlist limit: ${current.watchlist_limit}</p>
    <p>Verified calendar: ${current.verified_calendar ? "enabled" : "disabled"}</p>
    <p>Webhook delivery: ${current.webhook_delivery ? "enabled" : "disabled"}</p>
    <p>Briefing history: ${current.briefing_history_limit} entries</p>
  `;

  subscriptionTierEl.innerHTML = tiers
    .map((tier) => `<option value="${tier.tier}" ${tier.tier === user.tier ? "selected" : ""}>${tier.label}</option>`)
    .join("");

  subscriptionTiersEl.innerHTML = "";
  tiers.forEach((tier) => {
    const node = document.createElement("div");
    node.className = "story-list";
    node.innerHTML = `
      <h4>${tier.label}</h4>
      <ul>
        <li>${tier.description}</li>
        <li>Watchlist limit: ${tier.watchlist_limit}</li>
        <li>Verified calendar: ${tier.verified_calendar ? "Yes" : "No"}</li>
        <li>Webhook delivery: ${tier.webhook_delivery ? "Yes" : "No"}</li>
        <li>Briefing history: ${tier.briefing_history_limit} entries</li>
      </ul>
    `;
    subscriptionTiersEl.appendChild(node);
  });
}

function renderSharedWorkspace(workspace) {
  sharedWorkspace = workspace;
  if (!workspace) {
    sharedWorkspaceSummaryEl.innerHTML = `
      <p>No shared desk is active.</p>
      <p>Desk tier users can create or join a shared workspace with a team invite code.</p>
    `;
    sharedWorkspaceDetailEl.innerHTML = "";
    return;
  }

  sharedWorkspaceSummaryEl.innerHTML = `
    <p>Workspace: ${workspace.name}</p>
    <p>Invite code: ${workspace.invite_code}</p>
    <p>Members: ${workspace.members.length}</p>
    <p>Shared watchlist: ${workspace.watchlist.length} symbols</p>
  `;

  const members = workspace.members
    .map((member) => `<li>${member.name} (${member.role})</li>`)
    .join("");
  const watchlist = workspace.watchlist
    .map(
      (item) =>
        `<li>${item.symbol} <button type="button" class="detail-link" data-shared-remove="${item.symbol}">Remove</button></li>`
    )
    .join("");
  const notes = workspace.notes
    .map((note) => `<li>${note.author_name}: ${note.content}</li>`)
    .join("");
  const alerts = (workspace.alerts || [])
    .map((alert) => `<li>${alert.title}: ${alert.message}</li>`)
    .join("");
  const snapshots = (workspace.briefing_snapshots || [])
    .map((snapshot) => `<li>${snapshot.created_at}: ${snapshot.headline} <span>${snapshot.author_name}</span></li>`)
    .join("");

  sharedWorkspaceDetailEl.innerHTML = `
    <div class="story-list">
      <h4>Members</h4>
      <ul>${members || "<li>No members yet.</li>"}</ul>
    </div>
    <div class="story-list">
      <h4>Shared Watchlist</h4>
      <ul>${watchlist || "<li>No shared symbols yet.</li>"}</ul>
    </div>
    <div class="story-list">
      <h4>Desk Notes</h4>
      <ul>${notes || "<li>No notes yet.</li>"}</ul>
    </div>
    <div class="story-list">
      <h4>Shared Alerts</h4>
      <ul>${alerts || "<li>No shared alerts right now.</li>"}</ul>
    </div>
    <div class="story-list">
      <h4>Briefing Snapshots</h4>
      <ul>${snapshots || "<li>No desk briefings saved yet.</li>"}</ul>
    </div>
  `;

  sharedWorkspaceDetailEl.querySelectorAll("[data-shared-remove]").forEach((button) => {
    button.addEventListener("click", async () => {
      const symbol = button.getAttribute("data-shared-remove");
      const response = await fetch(`/workspace/shared/watchlist/${symbol}`, { method: "DELETE" });
      if (response.ok) {
        renderSharedWorkspace(await response.json());
      }
    });
  });
}

function renderSignalDetail(signal) {
  signalDetailEl.innerHTML = `
    <h3>${signal.label} (${signal.symbol})</h3>
    <p>The current stance is <strong class="${stanceClass(signal.stance)}">${signal.stance}</strong> with a normalized score of ${Math.round(signal.score * 100)}.</p>
    <div class="signal-meta">
      <span>Price ${formatPrice(signal.price)}</span>
      <span class="${signClass(signal.change_1d ?? 0)}">1D ${formatPercent(signal.change_1d)}</span>
    </div>
    <div class="signal-meta">
      <span class="${signClass(signal.change_20d ?? 0)}">20D ${formatPercent(signal.change_20d)}</span>
      <span>${signal.reasons.length} drivers</span>
    </div>
    <div class="story-list">
      <h4>Drivers</h4>
      <ul>${signal.reasons.map((reason) => `<li>${reason}</li>`).join("")}</ul>
    </div>
  `;
}

function renderPremarketBriefing(briefing) {
  premarketBriefingEl.innerHTML = `
    <div class="story-kicker">Daily Plan</div>
    <h3>${briefing.headline}</h3>
    <p class="story-summary">${briefing.overview}</p>
    <div class="story-lists">
      <div class="story-list">
        <h4>Checklist</h4>
        <ul>${briefing.checklist.map((point) => `<li>${point}</li>`).join("")}</ul>
      </div>
      <div class="story-list">
        <h4>Risks</h4>
        <ul>${briefing.risks.map((point) => `<li>${point}</li>`).join("")}</ul>
      </div>
    </div>
  `;
  premarketFocusEl.innerHTML = briefing.focus_items.map((item) => `<li>${item}</li>`).join("");
  const briefingItems = (briefing.catalyst_calendar || []).map((item) => ({
    title: item.split(" - ")[0] || item,
    category: "Briefing",
    timing: "",
    detail: item,
    symbols: [],
  }));
  renderCatalystCalendar(briefingItems, briefingCatalystsEl);
}

function renderNewsFilters(items) {
  const sources = ["All", ...(watchlistNews.length ? ["Watchlist"] : []), ...new Set(items.map((item) => item.source))];
  newsFiltersEl.innerHTML = "";
  sources.forEach((source) => {
    const button = document.createElement("button");
    button.className = `filter-chip${source === activeNewsSource ? " is-active" : ""}`;
    button.textContent = source;
    button.addEventListener("click", () => {
      activeNewsSource = source;
      selectedNewsIndex = 0;
      renderNewsFilters(allNewsItems);
      renderNews(allNewsItems);
    });
    newsFiltersEl.appendChild(button);
  });
}

function selectNewsItem(item) {
  const summary = item.summary || "No report body was provided by the upstream feed.";
  const linkMarkup =
    item.url && item.url !== "#"
      ? `<a class="detail-link" href="${item.url}" target="_blank" rel="noreferrer">Open Source</a>`
      : "";
  const matchedSymbols = item.matched_symbols?.length
    ? `<span>${item.matched_symbols.join(", ")}</span>`
    : "";
  newsDetailEl.innerHTML = `
    <div class="detail-meta">
      <span>${item.source}</span>
      <span>${item.tags.join(" / ")}</span>
      ${matchedSymbols}
    </div>
    <h3>${item.title}</h3>
    <p>${summary}</p>
    ${linkMarkup}
  `;
}

function renderNews(items) {
  const sourceItems = activeNewsSource === "Watchlist" ? watchlistNews : items;
  const query = newsSearchEl.value.trim().toLowerCase();
  const filtered = sourceItems.filter((item) => {
    const sourceMatch =
      activeNewsSource === "All" || activeNewsSource === "Watchlist" || item.source === activeNewsSource;
    const text = `${item.title} ${item.source} ${item.summary || ""}`.toLowerCase();
    return sourceMatch && (!query || text.includes(query));
  });

  newsListEl.innerHTML = "";
  if (!filtered.length) {
    newsListEl.innerHTML = `<div class="news-item"><p class="news-title">No headlines match the current filter.</p></div>`;
    newsDetailEl.innerHTML = "<p>No report selected.</p>";
    return;
  }

  selectedNewsIndex = Math.min(selectedNewsIndex, filtered.length - 1);
  filtered.forEach((item, index) => {
    const node = document.createElement("button");
    node.type = "button";
    node.className = `news-item${index === selectedNewsIndex ? " is-active" : ""}`;
    node.innerHTML = `
      <div class="news-meta">
        <span>${item.source}</span>
        <span>${item.tags.join(" / ")}${item.matched_symbols?.length ? ` • ${item.matched_symbols.join(", ")}` : ""}</span>
      </div>
      <p class="news-title">${item.title}</p>
    `;
    node.addEventListener("click", () => {
      selectedNewsIndex = index;
      renderNews(items);
    });
    newsListEl.appendChild(node);
  });

  selectNewsItem(filtered[selectedNewsIndex]);
}

function setView(view) {
  navItems.forEach((item) => {
    item.classList.toggle("is-active", item.dataset.view === view);
  });
  views.forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.viewPanel === view);
  });
  viewTitleEl.textContent = view.charAt(0).toUpperCase() + view.slice(1);
}

function openPalette() {
  paletteEl.hidden = false;
  paletteInputEl.value = "";
  renderPaletteResults(commands);
  paletteInputEl.focus();
}

function closePalette() {
  paletteEl.hidden = true;
}

function renderPaletteResults(items) {
  paletteResultsEl.innerHTML = "";
  items.forEach((command) => {
    const button = document.createElement("button");
    button.className = "palette-result";
    button.innerHTML = `${command.label}<small>${command.description}</small>`;
    button.addEventListener("click", () => {
      closePalette();
      command.run();
    });
    paletteResultsEl.appendChild(button);
  });
}

async function ensureAuthenticated() {
  const response = await fetch("/auth/me");
  if (response.status === 401) {
    window.location.href = "/login";
    throw new Error("Authentication required.");
  }
  if (!response.ok) throw new Error("Failed to load current user.");
  currentUser = await response.json();
  userBadgeEl.textContent = `${currentUser.name.toUpperCase()} • ${currentUser.tier.toUpperCase()}`;
}

async function loadSubscription() {
  const response = await fetch("/billing/tiers");
  if (!response.ok) throw new Error("Subscription request failed.");
  subscriptionTiers = await response.json();
  renderSubscription(currentUser, subscriptionTiers);
}

async function loadSharedWorkspace() {
  const response = await fetch("/workspace/shared");
  if (!response.ok) throw new Error("Shared workspace request failed.");
  renderSharedWorkspace(await response.json());
}

async function loadMetadata() {
  const [healthResponse, metadataResponse] = await Promise.all([fetch("/health"), fetch("/metadata")]);
  if (!healthResponse.ok || !metadataResponse.ok) throw new Error("Metadata request failed.");

  const health = await healthResponse.json();
  const metadata = await metadataResponse.json();

  classesEl.textContent = metadata.classes.join(" / ");
  thresholdsEl.textContent = Object.entries(metadata.thresholds)
    .map(([key, value]) => `${key}:${value}`)
    .join("  ");
  renderTrainingMetadata(metadata.training, metadata.feature_importance);
}

async function loadWatchlist() {
  const response = await fetch("/watchlist");
  if (!response.ok) throw new Error("Watchlist request failed.");
  allWatchlist = await response.json();
  renderWatchlist(allWatchlist);
}

async function loadAlerts() {
  const response = await fetch("/alerts");
  if (!response.ok) throw new Error("Alerts request failed.");
  allAlerts = await response.json();
  renderAlerts(allAlerts);
}

async function loadPrediction() {
  const response = await fetch("/predict/latest", { method: "POST" });
  if (!response.ok) throw new Error("Prediction request failed.");

  const data = await response.json();
  const copy = regimeCopy[data.regime] || {
    blurb: "Current regime available.",
    briefing: "Model output received.",
    color: "#4de2ff",
  };

  regimeEl.textContent = data.regime.toUpperCase();
  regimeEl.style.color = copy.color;
  regimeBlurbEl.textContent = copy.blurb;
  confidenceEl.textContent = `${Math.round(data.confidence * 100)}%`;
  timestampEl.textContent = `LAST SYNC: ${formatTimestamp(data.timestamp)}`;
  updateRing(data.confidence, copy.color);
  renderProbabilities(data.probabilities);
}

async function refreshTerminal() {
  const [
    transitionsResponse,
    marketStateResponse,
    sectorsResponse,
    newsResponse,
    marketPanelsResponse,
    signalResponse,
    premarketResponse,
    briefingHistoryResponse,
    watchlistResponse,
    watchlistIntelResponse,
    watchlistNewsResponse,
    alertsResponse,
    catalystResponse,
    deliveryResponse,
  ] = await Promise.all([
    fetch("/regime/transitions?limit=8"),
    fetch("/market/state"),
    fetch("/market/sectors?limit=8"),
    fetch("/news?limit=8"),
    fetch("/market/panels?window=20"),
    fetch("/signals/trending?limit=6"),
    fetch("/briefing/premarket"),
    fetch("/briefing/history?limit=6"),
    fetch("/watchlist"),
    fetch("/watchlist/intelligence"),
    fetch("/watchlist/news?limit=6"),
    fetch("/alerts"),
    fetch("/calendar/catalysts?limit=6"),
    fetch("/settings/delivery"),
  ]);

  if (
    !transitionsResponse.ok ||
    !marketStateResponse.ok ||
    !sectorsResponse.ok ||
    !newsResponse.ok ||
    !marketPanelsResponse.ok ||
    !signalResponse.ok ||
    !premarketResponse.ok ||
    !briefingHistoryResponse.ok ||
    !watchlistResponse.ok ||
    !watchlistIntelResponse.ok ||
    !watchlistNewsResponse.ok ||
    !alertsResponse.ok ||
    !catalystResponse.ok ||
    !deliveryResponse.ok
  ) {
    throw new Error("Terminal data request failed.");
  }

  renderTransitions(await transitionsResponse.json());

  latestMarketState = await marketStateResponse.json();
  stateBreadthEl.textContent = latestMarketState.breadth;
  stateVolatilityEl.textContent = latestMarketState.volatility_state;
  stateTrendEl.textContent = latestMarketState.trend_strength;
  stateConfirmationEl.textContent = latestMarketState.cross_asset_confirmation;
  regimeBlurbEl.textContent = latestMarketState.summary;
  renderDrivers(latestMarketState.drivers, latestMarketState.warnings);
  renderLeaderLaggards(latestMarketState);
  renderMeaning(latestMarketState.regime, latestMarketState);
  renderGlossary();
  renderBulletPanel(
    changesPanelEl,
    "Since Yesterday",
    latestMarketState.changes_since_yesterday,
    "No major change was detected versus the previous session."
  );
  renderBulletPanel(
    supportPanelEl,
    "Signals In Agreement",
    latestMarketState.supporting_signals,
    "There are not many clean supporting signals right now."
  );
  renderBulletPanel(
    conflictPanelEl,
    "Signals In Tension",
    latestMarketState.conflicting_signals,
    "There are no major conflicting signals at the moment."
  );

  allSectors = await sectorsResponse.json();
  renderSectors(allSectors);

  allNewsItems = await newsResponse.json();
  renderNewsFilters(allNewsItems);
  renderNews(allNewsItems);
  renderHeadlineStrip(allNewsItems);

  allMarketPanels = await marketPanelsResponse.json();
  renderMarketPanels(allMarketPanels);

  allSignals = await signalResponse.json();
  renderSignalCards(allSignals);

  renderPremarketBriefing(await premarketResponse.json());
  renderBriefingHistory(await briefingHistoryResponse.json());
  allWatchlist = await watchlistResponse.json();
  renderWatchlist(allWatchlist);
  await loadWatchlistDetail();
  watchlistInsights = await watchlistIntelResponse.json();
  renderWatchlistIntelligence(watchlistInsights);
  watchlistNews = await watchlistNewsResponse.json();
  renderWatchlistNews(watchlistNews);
  renderNewsFilters(allNewsItems);
  renderNews(allNewsItems);
  allAlerts = await alertsResponse.json();
  renderAlerts(allAlerts);
  catalystCalendar = await catalystResponse.json();
  renderCatalystCalendar(catalystCalendar);
  renderDeliveryPreferences(await deliveryResponse.json());
}

async function boot() {
  try {
    await ensureAuthenticated();
    await loadSubscription();
    await loadSharedWorkspace();
    await loadMetadata();
    await loadPrediction();
    await refreshTerminal();
  } catch (error) {
    regimeEl.textContent = "ERROR";
    regimeEl.style.color = "#ff6b7a";
    regimeBlurbEl.textContent = "Unable to fetch terminal data. Check API startup and dependencies.";
    if (driversListEl) {
      driversListEl.innerHTML = "<div class=\"alert-item high\"><strong>Error</strong><p>The monitor could not load the market state pack.</p></div>";
    }
    timestampEl.textContent = "LAST SYNC: FAILED";
  }
}

navItems.forEach((item) => {
  item.addEventListener("click", () => setView(item.dataset.view));
});

refreshButtonEl.addEventListener("click", () => boot());
commandButtonEl.addEventListener("click", openPalette);
logoutButtonEl.addEventListener("click", async () => {
  await fetch("/auth/logout", { method: "POST" });
  window.location.href = "/login";
});
watchlistFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const symbol = watchlistSymbolEl.value.trim().toUpperCase();
  if (!symbol) return;
  await fetch("/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol }),
  });
  watchlistSymbolEl.value = "";
  await loadWatchlist();
  const intelResponse = await fetch("/watchlist/intelligence");
  if (intelResponse.ok) {
    watchlistInsights = await intelResponse.json();
    renderWatchlistIntelligence(watchlistInsights);
  }
  const watchlistNewsResponse = await fetch("/watchlist/news?limit=6");
  if (watchlistNewsResponse.ok) {
    watchlistNews = await watchlistNewsResponse.json();
    renderWatchlistNews(watchlistNews);
    renderNewsFilters(allNewsItems);
    renderNews(allNewsItems);
  }
  const catalystResponse = await fetch("/calendar/catalysts?limit=6");
  if (catalystResponse.ok) {
    catalystCalendar = await catalystResponse.json();
    renderCatalystCalendar(catalystCalendar);
  }
  await loadWatchlistDetail(symbol);
  await loadAlerts();
});

deliveryFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/settings/delivery", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email_enabled: deliveryEmailEl.checked,
      webhook_enabled: deliveryWebhookEnabledEl.checked,
      webhook_url: deliveryWebhookUrlEl.value,
      cadence: deliveryCadenceEl.value,
    }),
  });
  if (response.ok) {
    renderDeliveryPreferences(await response.json());
  } else {
    deliveryStatusEl.innerHTML = "<p>Unable to save delivery preferences.</p>";
  }
});

subscriptionFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const requestedTier = subscriptionTierEl.value;
  const isUpgrade = currentUser && requestedTier !== "free" && requestedTier !== currentUser.tier;

  if (isUpgrade) {
    const checkoutResponse = await fetch("/billing/checkout/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tier: requestedTier }),
    });
    const checkoutData = await checkoutResponse.json();
    if (!checkoutResponse.ok || !checkoutData.url) {
      deliveryStatusEl.innerHTML = `<p>${checkoutData.detail || "Unable to start Stripe checkout."}</p>`;
      return;
    }
    window.location.href = checkoutData.url;
    return;
  }

  const response = await fetch("/billing/tier", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tier: requestedTier }),
  });
  const data = await response.json();
  if (!response.ok) {
    deliveryStatusEl.innerHTML = `<p>${data.detail || "Unable to update plan."}</p>`;
    return;
  }

  currentUser = data;
  userBadgeEl.textContent = `${currentUser.name.toUpperCase()} • ${currentUser.tier.toUpperCase()}`;
  renderSubscription(currentUser, subscriptionTiers);
  await refreshTerminal();
});

sharedWorkspaceCreateFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/workspace/shared", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: sharedWorkspaceNameEl.value }),
  });
  const data = await response.json();
  if (!response.ok) {
    sharedWorkspaceSummaryEl.innerHTML = `<p>${data.detail || "Unable to create shared workspace."}</p>`;
    return;
  }
  sharedWorkspaceNameEl.value = "";
  renderSharedWorkspace(data);
});

sharedWorkspaceJoinFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/workspace/shared/join", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ invite_code: sharedWorkspaceCodeEl.value }),
  });
  const data = await response.json();
  if (!response.ok) {
    sharedWorkspaceSummaryEl.innerHTML = `<p>${data.detail || "Unable to join shared workspace."}</p>`;
    return;
  }
  sharedWorkspaceCodeEl.value = "";
  renderSharedWorkspace(data);
});

sharedWorkspaceWatchlistFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/workspace/shared/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol: sharedWorkspaceSymbolEl.value }),
  });
  const data = await response.json();
  if (!response.ok) {
    sharedWorkspaceSummaryEl.innerHTML = `<p>${data.detail || "Unable to add shared symbol."}</p>`;
    return;
  }
  sharedWorkspaceSymbolEl.value = "";
  renderSharedWorkspace(data);
});

sharedWorkspaceNoteFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/workspace/shared/notes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: sharedWorkspaceNoteEl.value }),
  });
  const data = await response.json();
  if (!response.ok) {
    sharedWorkspaceSummaryEl.innerHTML = `<p>${data.detail || "Unable to post desk note."}</p>`;
    return;
  }
  sharedWorkspaceNoteEl.value = "";
  renderSharedWorkspace(data);
});

sharedWorkspaceBriefingButtonEl.addEventListener("click", async () => {
  const response = await fetch("/workspace/shared/briefing-snapshot", {
    method: "POST",
  });
  const data = await response.json();
  if (!response.ok) {
    sharedWorkspaceSummaryEl.innerHTML = `<p>${data.detail || "Unable to save desk briefing."}</p>`;
    return;
  }
  renderSharedWorkspace(data);
});

newsSearchEl.addEventListener("input", () => {
  selectedNewsIndex = 0;
  renderNews(allNewsItems);
});

paletteInputEl.addEventListener("input", () => {
  const query = paletteInputEl.value.trim().toLowerCase();
  const filtered = commands.filter((command) => {
    return command.label.toLowerCase().includes(query) || command.description.toLowerCase().includes(query);
  });
  renderPaletteResults(filtered);
});

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    openPalette();
  }
  if (event.key === "Escape" && !paletteEl.hidden) {
    closePalette();
  }
});

paletteEl.addEventListener("click", (event) => {
  if (event.target === paletteEl) closePalette();
});

updateClock();
setInterval(updateClock, 1000);

boot();
setInterval(async () => {
  try {
    await ensureAuthenticated();
    await loadPrediction();
    await refreshTerminal();
  } catch (error) {
    timestampEl.textContent = "LAST SYNC: AUTO REFRESH FAILED";
  }
}, 30000);
