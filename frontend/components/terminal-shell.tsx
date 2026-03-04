"use client";

import { useEffect, useState, type FormEvent } from "react";
import { apiFetch } from "@/lib/api";

type ViewKey = "monitor" | "briefing" | "world" | "markets" | "signals" | "desk" | "news" | "system";

type User = {
  id: number;
  email: string;
  name: string;
  tier: string;
  created_at: string;
};

type PredictResponse = {
  regime: string;
  confidence: number;
  probabilities: Record<string, number>;
  timestamp: string;
  source: string;
};

type RegimeDriver = {
  label: string;
  value: string;
  tone: string;
};

type MarketLeader = {
  symbol: string;
  label: string;
  metric: string;
  value: number;
};

type MarketStateSummary = {
  regime: string;
  confidence: number;
  breadth: string;
  volatility_state: string;
  trend_strength: string;
  cross_asset_confirmation: string;
  summary: string;
  drivers: RegimeDriver[];
  warnings: string[];
  leaders: MarketLeader[];
  laggards: MarketLeader[];
  supporting_signals: string[];
  conflicting_signals: string[];
  changes_since_yesterday: string[];
  bull_case: string[];
  bear_case: string[];
  next_steps: string[];
};

type RegimeTransition = {
  regime: string;
  started_at: string;
  ended_at: string;
  duration_days: number;
  average_confidence: number;
};

type NewsItem = {
  title: string;
  source: string;
  published_at: string;
  url: string;
  summary?: string | null;
  tags: string[];
};

type WorldAffairsEvent = {
  title: string;
  source: string;
  published_at: string;
  url: string;
  summary?: string | null;
  theme: string;
  region: string;
  urgency: string;
  severity: string;
  affected_assets: string[];
  market_view: string[];
  second_order_effects: string[];
  why_it_matters: string;
};

type WorldAffairsBriefing = {
  headline: string;
  summary: string;
  key_themes: string[];
  market_implications: string[];
  watchpoints: string[];
};

type WorldAffairsRegionSummary = {
  region: string;
  theme_count: number;
  active_themes: string[];
  affected_assets: string[];
  headline: string;
};

type NarrativeTimelineItem = {
  title: string;
  theme: string;
  region: string;
  published_at: string;
  event_summary: string;
  market_reaction: string;
  follow_through: string;
  current_implication: string;
  affected_assets: string[];
};

type MarketTrendPanel = {
  symbol: string;
  label: string;
  price: number;
  change_1d: number;
  change_5d?: number | null;
  change_20d?: number | null;
  signal: string;
  trend: number[];
};

type SectorPerformance = {
  symbol: string;
  label: string;
  change_1d: number;
  change_5d?: number | null;
  change_20d?: number | null;
  signal: string;
};

type SignalCard = {
  symbol: string;
  label: string;
  stance: string;
  score: number;
  price?: number | null;
  change_1d?: number | null;
  change_20d?: number | null;
  reasons: string[];
};

type WatchlistItem = {
  symbol: string;
  label: string;
  added_at: string;
};

type HeadlineReference = {
  title: string;
  source: string;
  url: string;
};

type WatchlistInsight = {
  symbol: string;
  label: string;
  stance: string;
  summary: string;
  score?: number | null;
  price?: number | null;
  change_1d?: number | null;
  change_20d?: number | null;
  reasons: string[];
  catalyst?: string | null;
  regime_alignment: string;
  trade_implication: string;
  catalyst_risk: string;
  sector_readthrough: string;
  related_news: HeadlineReference[];
};

type WatchlistExposure = {
  symbol: string;
  label: string;
  sensitivity: string;
  themes: string[];
  drivers: string[];
  market_links: string[];
};

type WatchlistNewsItem = {
  title: string;
  source: string;
  published_at: string;
  url: string;
  summary?: string | null;
  tags: string[];
  matched_symbols: string[];
};

type CatalystEvent = {
  title: string;
  category: string;
  timing: string;
  detail: string;
  symbols: string[];
  source?: string | null;
  verified: boolean;
};

type WatchlistDetail = {
  symbol: string;
  label: string;
  stance: string;
  summary: string;
  score?: number | null;
  price?: number | null;
  change_1d?: number | null;
  change_20d?: number | null;
  reasons: string[];
  exposures: string[];
  regime_alignment: string;
  trade_implication: string;
  catalyst_risk: string;
  sector_readthrough: string;
  related_news: WatchlistNewsItem[];
  world_affairs: WorldAffairsEvent[];
  narrative_timeline: NarrativeTimelineItem[];
  calendar_events: CatalystEvent[];
};

type AlertItem = {
  title: string;
  severity: string;
  message: string;
  symbol?: string | null;
};

type PremarketBriefing = {
  headline: string;
  overview: string;
  checklist: string[];
  focus_items: string[];
  risks: string[];
  catalyst_calendar: string[];
};

type BriefingHistoryItem = {
  briefing_date: string;
  headline: string;
  overview: string;
};

type Metadata = {
  classes: string[];
  features: string[];
  thresholds: Record<string, number>;
  training: Record<string, unknown>;
  feature_importance: Record<string, number>;
};

type DeliveryPreferences = {
  email_enabled: boolean;
  webhook_enabled: boolean;
  webhook_url: string;
  cadence: string;
};

type BriefingDeliveryResult = {
  headline: string;
  cadence: string;
  email_status: string;
  webhook_status: string;
  delivery_channels: string[];
};

type SubscriptionTier = {
  tier: string;
  label: string;
  description: string;
  watchlist_limit: number;
  verified_calendar: boolean;
  webhook_delivery: boolean;
  briefing_history_limit: number;
};

type SharedWorkspaceMember = {
  id: number;
  name: string;
  email: string;
  tier: string;
  role: string;
  joined_at: string;
};

type SharedWorkspaceNote = {
  id: number;
  content: string;
  created_at: string;
  author_name: string;
};

type SharedWorkspaceBriefingSnapshot = {
  id: number;
  headline: string;
  overview: string;
  created_at: string;
  author_name: string;
};

type SharedWorkspace = {
  id: number;
  name: string;
  invite_code: string;
  owner_user_id: number;
  created_at: string;
  members: SharedWorkspaceMember[];
  watchlist: WatchlistItem[];
  notes: SharedWorkspaceNote[];
  alerts: AlertItem[];
  briefing_snapshots: SharedWorkspaceBriefingSnapshot[];
};

type TerminalData = {
  me: User;
  prediction: PredictResponse;
  marketState: MarketStateSummary;
  transitions: RegimeTransition[];
  news: NewsItem[];
  worldAffairs: WorldAffairsEvent[];
  worldRegions: WorldAffairsRegionSummary[];
  worldBriefing: WorldAffairsBriefing;
  worldTimeline: NarrativeTimelineItem[];
  alerts: AlertItem[];
  sectors: SectorPerformance[];
  marketPanels: MarketTrendPanel[];
  signals: SignalCard[];
  watchlist: WatchlistItem[];
  watchlistInsights: WatchlistInsight[];
  watchlistExposures: WatchlistExposure[];
  watchlistNews: WatchlistNewsItem[];
  catalysts: CatalystEvent[];
  briefing: PremarketBriefing;
  briefingHistory: BriefingHistoryItem[];
  metadata: Metadata;
  delivery: DeliveryPreferences;
  tiers: SubscriptionTier[];
  workspace: SharedWorkspace | null;
};

type TerminalBootstrap = {
  me: User;
  prediction: PredictResponse;
  market_state: MarketStateSummary;
  transitions: RegimeTransition[];
  sectors: SectorPerformance[];
  watchlist: WatchlistItem[];
};

const views: { key: ViewKey; label: string; subtitle: string }[] = [
  { key: "monitor", label: "Overview", subtitle: "Market state" },
  { key: "briefing", label: "Briefing", subtitle: "Session plan" },
  { key: "world", label: "World Affairs", subtitle: "Macro and geopolitics" },
  { key: "markets", label: "Markets", subtitle: "Cross-asset" },
  { key: "signals", label: "Signals", subtitle: "Watchlist and ideas" },
  { key: "desk", label: "Desk", subtitle: "Shared workspace" },
  { key: "news", label: "News", subtitle: "Catalysts" },
  { key: "system", label: "Settings", subtitle: "Model and delivery" },
];

const cadenceOptions = [
  { value: "premarket", label: "Pre-Market" },
  { value: "intraday", label: "Intraday" },
  { value: "eod", label: "End Of Day" },
];

const regimeGuide: Record<string, { meaning: string; use: string; avoid: string }> = {
  RiskOn: {
    meaning:
      "The market is behaving like participants are comfortable taking risk. Growth, cyclicals, and momentum tend to respond better in this backdrop.",
    use:
      "Use RiskOn as a directional filter for long setups and momentum continuation, but still confirm with breadth, sectors, and catalysts before sizing up.",
    avoid:
      "Do not treat RiskOn as a guarantee. It is a market backdrop, not a trade signal for every ticker.",
  },
  RiskOff: {
    meaning:
      "The tape is acting defensively. Traders are prioritizing capital preservation and aggressive longs usually need more selectivity.",
    use:
      "Use RiskOff to tighten risk, focus on defensive leadership, and demand stronger confirmation on long exposure.",
    avoid:
      "Do not assume every name should be short. RiskOff conditions can still produce sharp squeezes and countertrend rebounds.",
  },
  HighVol: {
    meaning:
      "Volatility is dominating enough that normal trend signals are less reliable and price can reprice quickly across assets.",
    use:
      "Use smaller size, faster trade management, and clearer invalidation. Respect liquidity and headline risk more than usual.",
    avoid:
      "Do not overtrust slow-moving indicators or lean on oversized positions when the market is unstable.",
  },
};

function formatPercent(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }
  return `${(value * 100).toFixed(2)}%`;
}

function formatPrice(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }
  return `$${value.toFixed(2)}`;
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

function toneClass(value?: string | null) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("bull") || normalized.includes("positive") || normalized.includes("support")) {
    return "metric-positive";
  }
  if (normalized.includes("bear") || normalized.includes("negative") || normalized.includes("risk")) {
    return "metric-negative";
  }
  return "metric-neutral";
}

function metricClass(value?: number | null) {
  if (value === null || value === undefined) {
    return "metric-neutral";
  }
  if (value > 0) {
    return "metric-positive";
  }
  if (value < 0) {
    return "metric-negative";
  }
  return "metric-neutral";
}

function firstItems<T>(items: T[] | undefined, limit: number) {
  return (items || []).slice(0, limit);
}

function labelizeKey(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatSettingValue(value: unknown) {
  if (value === null || value === undefined) {
    return "--";
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).join(", ");
  }
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .slice(0, 3)
      .map(([key, item]) => `${labelizeKey(key)}: ${String(item)}`)
      .join(" | ");
  }
  return String(value);
}

function Sparkline({ values }: { values: number[] }) {
  if (!values.length) {
    return null;
  }

  const width = 220;
  const height = 54;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const points = values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="2.5" />
    </svg>
  );
}

function SkeletonBlock({
  className = "",
  width,
  height,
}: {
  className?: string;
  width?: string;
  height?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={`nt-skeleton ${className}`.trim()}
      style={{
        ...(width ? { width } : {}),
        ...(height ? { height } : {}),
      }}
    />
  );
}

function SkeletonList({ rows = 4 }: { rows?: number }) {
  return (
    <div className="nt-stack">
      {Array.from({ length: rows }).map((_, index) => (
        <div className="nt-list-item" key={`skeleton-row-${index}`}>
          <SkeletonBlock width="40%" height="14px" />
          <SkeletonBlock width="72%" height="12px" />
          <SkeletonBlock width="88%" height="12px" />
        </div>
      ))}
    </div>
  );
}

function SkeletonSymbolList({ rows = 4 }: { rows?: number }) {
  return (
    <div className="nt-stack">
      {Array.from({ length: rows }).map((_, index) => (
        <div className="nt-symbol" key={`skeleton-symbol-${index}`}>
          <div>
            <SkeletonBlock width="52px" height="14px" />
            <SkeletonBlock width="120px" height="12px" />
          </div>
          <div>
            <SkeletonBlock width="76px" height="12px" />
            <SkeletonBlock width="54px" height="14px" />
          </div>
        </div>
      ))}
    </div>
  );
}

function SkeletonMarketGrid({ rows = 6 }: { rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, index) => (
        <article className="nt-panel nt-market" key={`skeleton-market-${index}`}>
          <div className="nt-symbol">
            <div>
              <SkeletonBlock width="52px" height="14px" />
              <SkeletonBlock width="120px" height="12px" />
            </div>
            <div>
              <SkeletonBlock width="28px" height="12px" />
              <SkeletonBlock width="60px" height="14px" />
            </div>
          </div>
          <div className="nt-state-grid nt-compact-grid">
            {Array.from({ length: 4 }).map((__, cellIndex) => (
              <div key={`market-cell-${index}-${cellIndex}`}>
                <SkeletonBlock width="42px" height="10px" />
                <SkeletonBlock width="70px" height="14px" />
              </div>
            ))}
          </div>
          <SkeletonBlock className="nt-skeleton-chart" />
        </article>
      ))}
    </>
  );
}

function emptyPredictResponse(): PredictResponse {
  return {
    regime: "--",
    confidence: 0,
    probabilities: {},
    timestamp: new Date(0).toISOString(),
    source: "bootstrap",
  };
}

function emptyMarketState(): MarketStateSummary {
  return {
    regime: "--",
    confidence: 0,
    breadth: "--",
    volatility_state: "--",
    trend_strength: "--",
    cross_asset_confirmation: "--",
    summary: "",
    drivers: [],
    warnings: [],
    leaders: [],
    laggards: [],
    supporting_signals: [],
    conflicting_signals: [],
    changes_since_yesterday: [],
    bull_case: [],
    bear_case: [],
    next_steps: [],
  };
}

function emptyBriefing(): PremarketBriefing {
  return {
    headline: "",
    overview: "",
    checklist: [],
    focus_items: [],
    risks: [],
    catalyst_calendar: [],
  };
}

function emptyWorldBriefing(): WorldAffairsBriefing {
  return {
    headline: "",
    summary: "",
    key_themes: [],
    market_implications: [],
    watchpoints: [],
  };
}

function emptyMetadata(): Metadata {
  return {
    classes: [],
    features: [],
    thresholds: {},
    training: {},
    feature_importance: {},
  };
}

function emptyDelivery(): DeliveryPreferences {
  return {
    email_enabled: false,
    webhook_enabled: false,
    webhook_url: "",
    cadence: "premarket",
  };
}

function toInitialData(bootstrap: TerminalBootstrap): TerminalData {
  return {
    me: bootstrap.me,
    prediction: bootstrap.prediction,
    marketState: bootstrap.market_state,
    transitions: bootstrap.transitions,
    news: [],
    worldAffairs: [],
    worldRegions: [],
    worldBriefing: emptyWorldBriefing(),
    worldTimeline: [],
    alerts: [],
    sectors: bootstrap.sectors,
    marketPanels: [],
    signals: [],
    watchlist: bootstrap.watchlist,
    watchlistInsights: [],
    watchlistExposures: [],
    watchlistNews: [],
    catalysts: [],
    briefing: emptyBriefing(),
    briefingHistory: [],
    metadata: emptyMetadata(),
    delivery: emptyDelivery(),
    tiers: [],
    workspace: null,
  };
}

export default function TerminalShell() {
  const [activeView, setActiveView] = useState<ViewKey>("monitor");
  const [clock, setClock] = useState("");
  const [data, setData] = useState<TerminalData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState("");
  const [loadedViews, setLoadedViews] = useState<Partial<Record<ViewKey, boolean>>>({});
  const [selectedWatchlistSymbol, setSelectedWatchlistSymbol] = useState("");
  const [watchlistDetail, setWatchlistDetail] = useState<WatchlistDetail | null>(null);
  const [watchlistSymbolInput, setWatchlistSymbolInput] = useState("");
  const [deskNameInput, setDeskNameInput] = useState("");
  const [deskCodeInput, setDeskCodeInput] = useState("");
  const [deskSymbolInput, setDeskSymbolInput] = useState("");
  const [deskNoteInput, setDeskNoteInput] = useState("");
  const [deliveryForm, setDeliveryForm] = useState<DeliveryPreferences>({
    email_enabled: false,
    webhook_enabled: false,
    webhook_url: "",
    cadence: "premarket",
  });
  const [selectedTier, setSelectedTier] = useState("");
  const [deliveryResult, setDeliveryResult] = useState<BriefingDeliveryResult | null>(null);

  async function loadCoreData(silent = false) {
    if (!silent) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError("");

    try {
      const bootstrap = await apiFetch<TerminalBootstrap>("/terminal/bootstrap");
      setData((current) =>
        current
          ? {
              ...current,
              me: bootstrap.me,
              prediction: bootstrap.prediction,
              marketState: bootstrap.market_state,
              transitions: bootstrap.transitions,
              sectors: bootstrap.sectors,
              watchlist: bootstrap.watchlist,
            }
          : toInitialData(bootstrap),
      );
      setSelectedTier(bootstrap.me.tier);
      setSelectedWatchlistSymbol((current) => current || bootstrap.watchlist[0]?.symbol || "");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Failed to load terminal.";
      if (message.toLowerCase().includes("not authenticated") || message.toLowerCase().includes("401")) {
        window.location.href = "/login";
        return;
      }
      setError(message);
    } finally {
      if (!silent) {
        setLoading(false);
      } else {
        setRefreshing(false);
      }
    }
  }

  async function loadViewData(view: ViewKey, force = false) {
    if (!force && loadedViews[view]) {
      return;
    }

    try {
      if (view === "monitor") {
        const [alerts] = await Promise.all([apiFetch<AlertItem[]>("/alerts")]);
        setData((current) => (current ? { ...current, alerts } : current));
      }

      if (view === "briefing") {
        const [briefing, briefingHistory, worldBriefing] = await Promise.all([
          apiFetch<PremarketBriefing>("/briefing/premarket"),
          apiFetch<BriefingHistoryItem[]>("/briefing/history"),
          apiFetch<WorldAffairsBriefing>("/briefing/global-macro"),
        ]);
        setData((current) =>
          current ? { ...current, briefing, briefingHistory, worldBriefing } : current,
        );
      }

      if (view === "world") {
        const [worldAffairs, worldRegions, worldBriefing, worldTimeline] = await Promise.all([
          apiFetch<WorldAffairsEvent[]>("/world-affairs/monitor"),
          apiFetch<WorldAffairsRegionSummary[]>("/world-affairs/regions"),
          apiFetch<WorldAffairsBriefing>("/briefing/global-macro"),
          apiFetch<NarrativeTimelineItem[]>("/world-affairs/timeline"),
        ]);
        setData((current) =>
          current ? { ...current, worldAffairs, worldRegions, worldBriefing, worldTimeline } : current,
        );
      }

      if (view === "markets") {
        const [marketPanels] = await Promise.all([apiFetch<MarketTrendPanel[]>("/market/panels")]);
        setData((current) => (current ? { ...current, marketPanels } : current));
      }

      if (view === "signals") {
        const [signals, watchlistInsights, watchlistExposures, watchlistNews, catalysts] =
          await Promise.all([
            apiFetch<SignalCard[]>("/signals/trending"),
            apiFetch<WatchlistInsight[]>("/watchlist/intelligence"),
            apiFetch<WatchlistExposure[]>("/watchlist/exposures"),
            apiFetch<WatchlistNewsItem[]>("/watchlist/news"),
            apiFetch<CatalystEvent[]>("/calendar/catalysts"),
          ]);
        setData((current) =>
          current
            ? {
                ...current,
                signals,
                watchlistInsights,
                watchlistExposures,
                watchlistNews,
                catalysts,
              }
            : current,
        );
      }

      if (view === "desk") {
        const [workspace] = await Promise.all([apiFetch<SharedWorkspace | null>("/workspace/shared")]);
        setData((current) => (current ? { ...current, workspace } : current));
      }

      if (view === "news") {
        const [news, watchlistNews] = await Promise.all([
          apiFetch<NewsItem[]>("/news"),
          apiFetch<WatchlistNewsItem[]>("/watchlist/news"),
        ]);
        setData((current) => (current ? { ...current, news, watchlistNews } : current));
      }

      if (view === "system") {
        const [metadata, delivery, tiers] = await Promise.all([
          apiFetch<Metadata>("/metadata"),
          apiFetch<DeliveryPreferences>("/settings/delivery"),
          apiFetch<SubscriptionTier[]>("/billing/tiers"),
        ]);
        setData((current) => (current ? { ...current, metadata, delivery, tiers } : current));
        setDeliveryForm(delivery);
      }

      setLoadedViews((current) => ({ ...current, [view]: true }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load workspace data.");
    }
  }

  async function refreshActiveView() {
    await loadCoreData(true);
    await loadViewData(activeView, true);
    if (activeView === "signals" && selectedWatchlistSymbol) {
      await loadWatchlistDetail(selectedWatchlistSymbol);
    }
  }

  async function loadWatchlistDetail(symbol: string) {
    setSelectedWatchlistSymbol(symbol);
    try {
      const detail = await apiFetch<WatchlistDetail>(`/watchlist/${symbol}/detail`);
      setWatchlistDetail(detail);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load watchlist detail.");
    }
  }

  useEffect(() => {
    void loadCoreData();
    const interval = window.setInterval(() => {
      void refreshActiveView();
    }, 30000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!data) {
      return;
    }
    void loadViewData(activeView);
  }, [activeView, data]);

  useEffect(() => {
    if (activeView !== "signals" || !selectedWatchlistSymbol || !data) {
      return;
    }
    void loadWatchlistDetail(selectedWatchlistSymbol);
  }, [activeView, selectedWatchlistSymbol, data]);

  useEffect(() => {
    const updateClock = () => setClock(new Date().toLocaleTimeString());
    updateClock();
    const interval = window.setInterval(updateClock, 1000);
    return () => window.clearInterval(interval);
  }, []);

  async function handleLogout() {
    await apiFetch("/auth/logout", { method: "POST" });
    window.location.href = "/login";
  }

  async function handleWatchlistSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!watchlistSymbolInput.trim()) {
      return;
    }
    setSaving("watchlist");
    try {
      await apiFetch("/watchlist", {
        method: "POST",
        body: JSON.stringify({ symbol: watchlistSymbolInput.trim().toUpperCase() }),
      });
      setWatchlistSymbolInput("");
      setLoadedViews((current) => ({ ...current, signals: false }));
      await refreshActiveView();
      setActiveView("signals");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to update watchlist.");
    } finally {
      setSaving("");
    }
  }

  async function handleWatchlistRemove(symbol: string) {
    setSaving(`remove-${symbol}`);
    try {
      await apiFetch(`/watchlist/${symbol}`, { method: "DELETE" });
      if (selectedWatchlistSymbol === symbol) {
        setSelectedWatchlistSymbol("");
        setWatchlistDetail(null);
      }
      setLoadedViews((current) => ({ ...current, signals: false }));
      await refreshActiveView();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to remove symbol.");
    } finally {
      setSaving("");
    }
  }

  async function handleDeliverySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving("delivery");
    try {
      await apiFetch("/settings/delivery", {
        method: "PUT",
        body: JSON.stringify(deliveryForm),
      });
      setLoadedViews((current) => ({ ...current, system: false }));
      await refreshActiveView();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to save delivery preferences.");
    } finally {
      setSaving("");
    }
  }

  async function handleTierSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving("tier");
    try {
      await apiFetch("/billing/tier", {
        method: "PUT",
        body: JSON.stringify({ tier: selectedTier }),
      });
      setLoadedViews((current) => ({ ...current, system: false }));
      await refreshActiveView();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to update plan.");
    } finally {
      setSaving("");
    }
  }

  async function handleMacroDeliverySend() {
    setSaving("macro-delivery");
    try {
      const result = await apiFetch<BriefingDeliveryResult>("/delivery/global-macro/send", {
        method: "POST",
      });
      setDeliveryResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to send macro briefing.");
    } finally {
      setSaving("");
    }
  }

  async function handleCreateDesk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deskNameInput.trim()) {
      return;
    }
    setSaving("desk-create");
    try {
      await apiFetch("/workspace/shared", {
        method: "POST",
        body: JSON.stringify({ name: deskNameInput.trim() }),
      });
      setDeskNameInput("");
      setLoadedViews((current) => ({ ...current, desk: false }));
      await refreshActiveView();
      setActiveView("desk");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to create desk.");
    } finally {
      setSaving("");
    }
  }

  async function handleJoinDesk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deskCodeInput.trim()) {
      return;
    }
    setSaving("desk-join");
    try {
      await apiFetch("/workspace/shared/join", {
        method: "POST",
        body: JSON.stringify({ invite_code: deskCodeInput.trim() }),
      });
      setDeskCodeInput("");
      setLoadedViews((current) => ({ ...current, desk: false }));
      await refreshActiveView();
      setActiveView("desk");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to join desk.");
    } finally {
      setSaving("");
    }
  }

  async function handleDeskSymbol(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deskSymbolInput.trim()) {
      return;
    }
    setSaving("desk-symbol");
    try {
      await apiFetch("/workspace/shared/watchlist", {
        method: "POST",
        body: JSON.stringify({ symbol: deskSymbolInput.trim().toUpperCase() }),
      });
      setDeskSymbolInput("");
      setLoadedViews((current) => ({ ...current, desk: false }));
      await refreshActiveView();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to add shared symbol.");
    } finally {
      setSaving("");
    }
  }

  async function handleDeskNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deskNoteInput.trim()) {
      return;
    }
    setSaving("desk-note");
    try {
      await apiFetch("/workspace/shared/notes", {
        method: "POST",
        body: JSON.stringify({ content: deskNoteInput.trim() }),
      });
      setDeskNoteInput("");
      setLoadedViews((current) => ({ ...current, desk: false }));
      await refreshActiveView();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to post desk note.");
    } finally {
      setSaving("");
    }
  }

  async function handleDeskSnapshot() {
    setSaving("desk-snapshot");
    try {
      await apiFetch("/workspace/shared/briefing-snapshot", { method: "POST" });
      setLoadedViews((current) => ({ ...current, desk: false }));
      await refreshActiveView();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to save desk briefing.");
    } finally {
      setSaving("");
    }
  }

  const activeViewMeta = views.find((view) => view.key === activeView) || views[0];
  const guide = regimeGuide[data?.marketState.regime || ""] || regimeGuide.RiskOn;
  const bootstrapping = !data;
  const monitorHydrating = bootstrapping || !loadedViews.monitor;
  const briefingHydrating = bootstrapping || !loadedViews.briefing;
  const worldHydrating = bootstrapping || !loadedViews.world;
  const marketsHydrating = bootstrapping || !loadedViews.markets;
  const signalsHydrating = bootstrapping || !loadedViews.signals;
  const deskHydrating = bootstrapping || !loadedViews.desk;
  const newsHydrating = bootstrapping || !loadedViews.news;
  const systemHydrating = bootstrapping || !loadedViews.system;
  const bullCaseItems =
    data?.marketState.bull_case?.length
      ? data.marketState.bull_case
      : data?.marketState.supporting_signals?.length
        ? data.marketState.supporting_signals
        : [guide.use];
  const bearCaseItems =
    data?.marketState.bear_case?.length
      ? data.marketState.bear_case
      : data?.marketState.conflicting_signals?.length
        ? data.marketState.conflicting_signals
        : [guide.avoid];

  return (
    <main className="nt-shell">
      <div className="nt-grid">
        <aside className="nt-sidebar">
          <div className="nt-brand">
            <span className="nt-wordmark">REGIME</span>
            <p className="nt-brand-copy">Market context, catalysts, watchlists, and desk workflow.</p>
          </div>
          <nav className="nt-nav">
          {views.map((view) => (
            <button
              key={view.key}
              className={`nt-nav-item ${activeView === view.key ? "is-active" : ""}`}
              onClick={() => setActiveView(view.key)}
              type="button"
            >
              <strong>{view.label}</strong>
              <span>{view.subtitle}</span>
            </button>
          ))}
          </nav>
          <div className="nt-sidebar-footer">
            <div className="nt-sidebar-stat">
              <span className="eyebrow">Session</span>
              {data?.me?.name ? <strong>{data.me.name}</strong> : <SkeletonBlock width="120px" height="14px" />}
            </div>
            <button className="button nt-logout-button" onClick={() => void handleLogout()} type="button">
              Logout
            </button>
          </div>
        </aside>

        <section className="nt-main">
          <header className="nt-header">
            <div className="nt-header-copy">
              <p className="eyebrow">Workspace</p>
              <h2>{activeViewMeta.label}</h2>
              <p className="nt-header-subtitle">
              {loading || refreshing
                ? <SkeletonBlock width="220px" height="12px" />
                : error
                  ? error
                  : activeViewMeta.subtitle}
              </p>
            </div>
            <div className="nt-header-meta">
              <div className="nt-status-line">
                <span className="nt-signal"><i /> Live model</span>
                <span className="nt-status-chip">
                  {data ? `Sync ${formatDateTime(data.prediction.timestamp)}` : <SkeletonBlock width="112px" height="12px" />}
                </span>
              </div>
              <div className="nt-clock-row">
                <span className="nt-clock">{clock || "--:--:--"}</span>
              </div>
              <div className="nt-actions">
              <button className="button" onClick={() => void refreshActiveView()} type="button">
                {refreshing ? "Refreshing..." : "Refresh"}
              </button>
              </div>
            </div>
          </header>

          {error ? <section className="nt-banner">{error}</section> : null}

          {activeView === "monitor" ? (
            <section className="nt-view nt-overview">
              <article className="nt-panel nt-hero">
                <span className="eyebrow">Current Market State</span>
                <div className="nt-hero-row">
                  <div>
                    {bootstrapping ? (
                      <>
                        <SkeletonBlock width="180px" height="42px" />
                        <SkeletonBlock width="88%" height="12px" />
                        <SkeletonBlock width="74%" height="12px" />
                      </>
                    ) : (
                      <>
                        <div className="nt-regime">{data?.prediction.regime || "--"}</div>
                        <p className="nt-hero-copy">{data?.marketState.summary || guide.meaning}</p>
                      </>
                    )}
                  </div>
                  <div className="nt-confidence">
                    {bootstrapping ? (
                      <>
                        <SkeletonBlock width="84px" height="24px" />
                        <SkeletonBlock width="72px" height="10px" />
                      </>
                    ) : (
                      <>
                        <span>{`${Math.round(data?.prediction.confidence ? data.prediction.confidence * 100 : 0)}%`}</span>
                        <small>confidence</small>
                      </>
                    )}
                  </div>
                </div>
              </article>

              <article className="nt-panel nt-state">
                <span className="eyebrow">State Pack</span>
                {bootstrapping ? (
                  <div className="nt-state-grid">
                    {Array.from({ length: 4 }).map((_, index) => (
                      <div key={`state-skeleton-${index}`}>
                        <SkeletonBlock width="54px" height="10px" />
                        <SkeletonBlock width="82%" height="14px" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="nt-state-grid">
                    <div><span>Breadth</span><strong>{data?.marketState.breadth || "--"}</strong></div>
                    <div><span>Volatility</span><strong>{data?.marketState.volatility_state || "--"}</strong></div>
                    <div><span>Trend</span><strong>{data?.marketState.trend_strength || "--"}</strong></div>
                    <div><span>Confirmation</span><strong>{data?.marketState.cross_asset_confirmation || "--"}</strong></div>
                  </div>
                )}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Probability Ladder</span>
                <div className="nt-stack">
                  {Object.entries(data?.prediction.probabilities || {})
                    .sort((a, b) => b[1] - a[1])
                    .map(([label, value]) => (
                      <div className="nt-probability" key={label}>
                        <div className="nt-row nt-between">
                          <span>{label}</span>
                          <strong>{formatPercent(value)}</strong>
                        </div>
                        <div className="nt-probability-bar">
                        <div style={{ width: `${Math.max(value * 100, 2)}%` }} />
                        </div>
                      </div>
                    ))}
                  {!Object.keys(data?.prediction.probabilities || {}).length ? <SkeletonList rows={3} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">How To Read It</span>
                {bootstrapping ? (
                  <div className="nt-copy">
                    <SkeletonBlock width="94%" height="12px" />
                    <SkeletonBlock width="88%" height="12px" />
                    <SkeletonBlock width="76%" height="12px" />
                  </div>
                ) : (
                  <div className="nt-copy">
                    <p>{guide.use}</p>
                    <p className="muted-copy">{guide.avoid}</p>
                  </div>
                )}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">What Changed</span>
                <ul className="plain-list">
                  {(data?.marketState.changes_since_yesterday || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Supporting Signals</span>
                <ul className="plain-list">
                  {(data?.marketState.supporting_signals || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Conflicting Signals</span>
                <ul className="plain-list">
                  {(data?.marketState.conflicting_signals || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Bull vs Bear</span>
                {bootstrapping ? (
                  <div className="nt-split">
                    <SkeletonList rows={3} />
                    <SkeletonList rows={3} />
                  </div>
                ) : (
                  <div className="nt-split nt-thesis-grid">
                    <div className="nt-thesis-column">
                      <h4>Bull Case</h4>
                      <ul className="plain-list">
                        {bullCaseItems.map((item, index) => (
                          <li key={`bull-${item}-${index}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="nt-thesis-column">
                      <h4>Bear Case</h4>
                      <ul className="plain-list">
                        {bearCaseItems.map((item, index) => (
                          <li key={`bear-${item}-${index}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Why This Regime</span>
                <div className="nt-stack">
                  {firstItems(data?.marketState.drivers, 4).map((driver) => (
                    <div className="nt-list-item" key={`${driver.label}-${driver.value}`}>
                      <strong>{driver.label}</strong>
                      <span className={toneClass(driver.tone)}>{driver.value}</span>
                    </div>
                  ))}
                  {!data?.marketState.drivers.length ? <SkeletonList rows={3} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Next Step</span>
                <div className="nt-stack">
                  {(data?.marketState.next_steps || []).map((item, index) => (
                    <div className="nt-list-item" key={`${item}-${index}`}>
                      <p>{item}</p>
                    </div>
                  ))}
                  <div className="nt-actions">
                    <button className="button button-primary" onClick={() => setActiveView("signals")} type="button">
                      Open Watchlist Context
                    </button>
                    <button className="button" onClick={() => setActiveView("world")} type="button">
                      Open World Affairs
                    </button>
                  </div>
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Transition History</span>
                <div className="nt-stack">
                  {(data?.transitions || []).map((item) => (
                    <div className="nt-list-item" key={`${item.regime}-${item.started_at}`}>
                      <strong>{item.regime}</strong>
                      <span>{item.started_at} to {item.ended_at}</span>
                      <span>{item.duration_days}d / {Math.round(item.average_confidence * 100)}%</span>
                    </div>
                  ))}
                  {!data?.transitions.length ? <SkeletonList rows={3} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Leaders / Laggards</span>
                <div className="nt-split">
                  <div className="nt-stack">
                    <h4>Leaders</h4>
                    {firstItems(data?.marketState.leaders, 4).map((item) => (
                      <div className="nt-symbol" key={`leader-${item.symbol}`}>
                        <div>
                          <strong>{item.symbol}</strong>
                          <span>{item.label}</span>
                        </div>
                        <div>
                          <span>{item.metric}</span>
                          <strong className={metricClass(item.value)}>{item.value.toFixed(2)}</strong>
                        </div>
                      </div>
                    ))}
                    {!data?.marketState.leaders.length ? <SkeletonSymbolList rows={3} /> : null}
                  </div>
                  <div className="nt-stack">
                    <h4>Laggards</h4>
                    {firstItems(data?.marketState.laggards, 4).map((item) => (
                      <div className="nt-symbol" key={`laggard-${item.symbol}`}>
                        <div>
                          <strong>{item.symbol}</strong>
                          <span>{item.label}</span>
                        </div>
                        <div>
                          <span>{item.metric}</span>
                          <strong className={metricClass(item.value)}>{item.value.toFixed(2)}</strong>
                        </div>
                      </div>
                    ))}
                    {!data?.marketState.laggards.length ? <SkeletonSymbolList rows={3} /> : null}
                  </div>
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Alerts</span>
                <div className="nt-stack">
                  {firstItems(data?.alerts, 4).map((alert) => (
                    <div className={`nt-alert ${alert.severity}`} key={`${alert.title}-${alert.message}`}>
                      <strong>{alert.title}</strong>
                      <p>{alert.message}</p>
                    </div>
                  ))}
                  {monitorHydrating && !data?.alerts.length ? <SkeletonList rows={3} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Sector Breadth</span>
                <div className="nt-stack">
                  {firstItems(data?.sectors, 6).map((sector) => (
                    <div className="nt-symbol" key={sector.symbol}>
                      <div>
                        <strong>{sector.symbol}</strong>
                        <span>{sector.label}</span>
                      </div>
                      <div>
                        <span>{sector.signal}</span>
                        <strong className={metricClass(sector.change_1d)}>{formatPercent(sector.change_1d)}</strong>
                      </div>
                    </div>
                  ))}
                  {!data?.sectors.length ? <SkeletonSymbolList rows={4} /> : null}
                </div>
              </article>
            </section>
          ) : null}

          {activeView === "briefing" ? (
            <section className="nt-view nt-briefing">
              <article className="nt-panel nt-hero">
                <span className="eyebrow">Pre-Market Briefing</span>
                <div className="nt-briefing-copy">
                  {briefingHydrating ? (
                    <>
                      <SkeletonBlock width="58%" height="20px" />
                      <SkeletonBlock width="92%" height="12px" />
                      <SkeletonBlock width="76%" height="12px" />
                    </>
                  ) : (
                    <>
                      <h3>{data?.briefing.headline || "--"}</h3>
                      <p>{data?.briefing.overview || ""}</p>
                    </>
                  )}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Checklist</span>
                <ul className="plain-list">
                  {(data?.briefing.checklist || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {briefingHydrating && !data?.briefing.checklist.length ? <SkeletonList rows={4} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Focus Items</span>
                <ul className="plain-list">
                  {(data?.briefing.focus_items || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {briefingHydrating && !data?.briefing.focus_items.length ? <SkeletonList rows={3} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Risks</span>
                <ul className="plain-list">
                  {(data?.briefing.risks || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {briefingHydrating && !data?.briefing.risks.length ? <SkeletonList rows={3} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Session Catalysts</span>
                <ul className="plain-list">
                  {(data?.briefing.catalyst_calendar || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {briefingHydrating && !data?.briefing.catalyst_calendar.length ? <SkeletonList rows={3} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Global Macro Brief</span>
                <div className="nt-copy">
                  {briefingHydrating ? (
                    <>
                      <SkeletonBlock width="70%" height="12px" />
                      <SkeletonBlock width="92%" height="12px" />
                      <SkeletonBlock width="68%" height="12px" />
                    </>
                  ) : (
                    <>
                      <p>{data?.worldBriefing.headline || "--"}</p>
                      <p>{data?.worldBriefing.summary || ""}</p>
                    </>
                  )}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Briefing History</span>
                <div className="nt-stack">
                  {firstItems(data?.briefingHistory, 5).map((item) => (
                    <div className="nt-list-item" key={`${item.briefing_date}-${item.headline}`}>
                      <strong>{item.headline}</strong>
                      <span>{item.briefing_date}</span>
                      <p>{item.overview}</p>
                    </div>
                  ))}
                  {briefingHydrating && !data?.briefingHistory.length ? <SkeletonList rows={3} /> : null}
                </div>
              </article>
            </section>
          ) : null}

          {activeView === "world" ? (
            <section className="nt-view nt-world">
              <article className="nt-panel nt-hero">
                <span className="eyebrow">Global Macro Brief</span>
                <div className="nt-briefing-copy">
                  {worldHydrating ? (
                    <>
                      <SkeletonBlock width="60%" height="20px" />
                      <SkeletonBlock width="94%" height="12px" />
                      <SkeletonBlock width="72%" height="12px" />
                    </>
                  ) : (
                    <>
                      <h3>{data?.worldBriefing.headline || "--"}</h3>
                      <p>{data?.worldBriefing.summary || ""}</p>
                    </>
                  )}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Key Themes</span>
                <ul className="plain-list">
                  {(data?.worldBriefing.key_themes || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {worldHydrating && !data?.worldBriefing.key_themes.length ? <SkeletonList rows={3} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Market Implications</span>
                <ul className="plain-list">
                  {(data?.worldBriefing.market_implications || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {worldHydrating && !data?.worldBriefing.market_implications.length ? <SkeletonList rows={3} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Watchpoints</span>
                <ul className="plain-list">
                  {(data?.worldBriefing.watchpoints || []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {worldHydrating && !data?.worldBriefing.watchpoints.length ? <SkeletonList rows={3} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Regions</span>
                <div className="nt-stack">
                  {(data?.worldRegions || []).map((region) => (
                    <div className="nt-list-item" key={region.region}>
                      <strong>{region.region}</strong>
                      <span>{region.theme_count} active themes</span>
                      <p>{region.headline}</p>
                      <p>Themes: {region.active_themes.join(", ")}</p>
                    </div>
                  ))}
                  {worldHydrating && !data?.worldRegions.length ? <SkeletonList rows={3} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card nt-settings-wide">
                <span className="eyebrow">Narrative Timeline</span>
                <div className="nt-stack">
                  {(data?.worldTimeline || []).map((item) => (
                    <div className="nt-list-item" key={`${item.title}-${item.published_at}`}>
                      <strong>{item.title}</strong>
                      <span>{item.theme} • {item.region} • {formatDateTime(item.published_at)}</span>
                      <p><strong>Event:</strong> {item.event_summary}</p>
                      <p><strong>Market Reaction:</strong> {item.market_reaction}</p>
                      <p><strong>Follow-Through:</strong> {item.follow_through}</p>
                      <p><strong>Current Implication:</strong> {item.current_implication}</p>
                    </div>
                  ))}
                  {worldHydrating && !data?.worldTimeline.length ? <SkeletonList rows={4} /> : null}
                </div>
              </article>

              {firstItems(data?.worldAffairs, 6).map((event) => (
                <article className="nt-panel nt-card" key={`${event.title}-${event.published_at}`}>
                  <span className="eyebrow">{event.theme} • {event.region}</span>
                  <div className="nt-stack">
                    <a className="nt-news-item" href={event.url} rel="noreferrer" target="_blank">
                      <strong>{event.title}</strong>
                      <span>{event.source} • {formatDateTime(event.published_at)} • {event.urgency} / {event.severity}</span>
                      <p>{event.summary || event.why_it_matters}</p>
                    </a>
                    <div className="nt-copy">
                      <p><strong>Why it matters:</strong> {event.why_it_matters}</p>
                      <p><strong>Affected assets:</strong> {event.affected_assets.join(", ")}</p>
                    </div>
                    <div className="nt-stack">
                      <h4>Market View</h4>
                      <ul className="plain-list">
                        {event.market_view.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                      </ul>
                    </div>
                    <div className="nt-stack">
                      <h4>Second-Order Effects</h4>
                      <ul className="plain-list">
                        {event.second_order_effects.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                      </ul>
                    </div>
                  </div>
                </article>
              ))}
              {worldHydrating && !data?.worldAffairs.length ? <SkeletonList rows={3} /> : null}
            </section>
          ) : null}

          {activeView === "markets" ? (
            <section className="nt-view nt-market-grid">
              {firstItems(data?.marketPanels, 8).map((panel) => (
                <article className="nt-panel nt-market" key={panel.symbol}>
                  <div className="nt-symbol">
                    <div>
                      <strong>{panel.symbol}</strong>
                      <span>{panel.label}</span>
                    </div>
                    <div>
                      <span>1D</span>
                      <strong className={metricClass(panel.change_1d)}>{formatPercent(panel.change_1d)}</strong>
                    </div>
                  </div>
                  <div className="nt-state-grid nt-compact-grid">
                    <div><span>Price</span><strong>{formatPrice(panel.price)}</strong></div>
                    <div><span>5D</span><strong className={metricClass(panel.change_5d)}>{formatPercent(panel.change_5d)}</strong></div>
                    <div><span>20D</span><strong className={metricClass(panel.change_20d)}>{formatPercent(panel.change_20d)}</strong></div>
                    <div><span>Signal</span><strong>{panel.signal}</strong></div>
                  </div>
                  <Sparkline values={panel.trend} />
                </article>
              ))}
              {marketsHydrating && !data?.marketPanels.length ? <SkeletonMarketGrid rows={6} /> : null}
            </section>
          ) : null}

          {activeView === "signals" ? (
            <section className="nt-view nt-signals">
              <article className="nt-panel nt-card">
                <span className="eyebrow">Trending Signals</span>
                <div className="nt-stack">
                  {firstItems(data?.signals, 6).map((signal) => (
                    <div className="nt-signal-card" key={signal.symbol}>
                      <div className="nt-symbol">
                        <div>
                          <strong>{signal.symbol}</strong>
                          <span>{signal.label}</span>
                        </div>
                        <strong className={toneClass(signal.stance)}>{signal.stance}</strong>
                      </div>
                      <p>{signal.reasons.join(" • ")}</p>
                      <div className="nt-row nt-between">
                        <span>{formatPrice(signal.price)}</span>
                        <span className={metricClass(signal.change_1d)}>{formatPercent(signal.change_1d)}</span>
                      </div>
                    </div>
                  ))}
                  {signalsHydrating && !data?.signals.length ? <SkeletonList rows={4} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Watchlist</span>
                <form className="nt-form" onSubmit={(event) => void handleWatchlistSubmit(event)}>
                  <input
                    className="nt-input"
                    onChange={(event) => setWatchlistSymbolInput(event.target.value)}
                    placeholder="Add symbol, e.g. NVDA"
                    value={watchlistSymbolInput}
                  />
                  <button className="button button-primary" disabled={saving === "watchlist"} type="submit">
                    {saving === "watchlist" ? "Adding..." : "Add Symbol"}
                  </button>
                </form>
                <div className="nt-stack">
                  {(data?.watchlist || []).map((item) => (
                    <div className="nt-watchlist-item" key={item.symbol}>
                      <button className="nt-ghost-button" onClick={() => void loadWatchlistDetail(item.symbol)} type="button">
                        <strong>{item.symbol}</strong>
                        <span>{item.label}</span>
                      </button>
                      <button className="button button-small" onClick={() => void handleWatchlistRemove(item.symbol)} type="button">
                        {saving === `remove-${item.symbol}` ? "..." : "Remove"}
                      </button>
                    </div>
                  ))}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Watchlist Intelligence</span>
                <div className="nt-stack">
                  {firstItems(data?.watchlistInsights, 6).map((item) => (
                    <div className="nt-signal-card" key={item.symbol}>
                      <div className="nt-symbol">
                        <div>
                          <strong>{item.symbol}</strong>
                          <span>{item.label}</span>
                        </div>
                        <strong className={toneClass(item.stance)}>{item.stance}</strong>
                      </div>
                      <p>{item.summary}</p>
                      <div className="nt-context-grid">
                        <div>
                          <span>Regime Alignment</span>
                          <strong>{item.regime_alignment}</strong>
                        </div>
                        <div>
                          <span>Trade Implication</span>
                          <strong>{item.trade_implication}</strong>
                        </div>
                        <div>
                          <span>Catalyst Risk</span>
                          <strong>{item.catalyst_risk}</strong>
                        </div>
                        <div>
                          <span>Sector Read-Through</span>
                          <strong>{item.sector_readthrough}</strong>
                        </div>
                      </div>
                      <p className="muted-copy">{item.reasons.join(" • ")}</p>
                    </div>
                  ))}
                  {signalsHydrating && !data?.watchlistInsights.length ? <SkeletonList rows={4} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Exposure Mapping</span>
                <div className="nt-stack">
                  {firstItems(data?.watchlistExposures, 6).map((item) => (
                    <div className="nt-list-item" key={`${item.symbol}-${item.sensitivity}`}>
                      <strong>{item.symbol} • {item.sensitivity} sensitivity</strong>
                      <span>{item.label}</span>
                      <p>Themes: {item.themes.join(", ")}</p>
                      <p>Links: {item.market_links.join(", ")}</p>
                    </div>
                  ))}
                  {signalsHydrating && !data?.watchlistExposures.length ? <SkeletonList rows={4} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Watchlist Detail</span>
                {watchlistDetail ? (
                  <div className="nt-stack">
                    <div className="nt-symbol">
                      <div>
                        <strong>{watchlistDetail.symbol}</strong>
                        <span>{watchlistDetail.label}</span>
                      </div>
                      <strong className={toneClass(watchlistDetail.stance)}>{watchlistDetail.stance}</strong>
                    </div>
                    <p>{watchlistDetail.summary}</p>
                    <p>{watchlistDetail.reasons.join(" • ")}</p>
                    <div className="nt-context-grid">
                      <div>
                        <span>Regime Alignment</span>
                        <strong>{watchlistDetail.regime_alignment || "--"}</strong>
                      </div>
                      <div>
                        <span>Trade Implication</span>
                        <strong>{watchlistDetail.trade_implication || "--"}</strong>
                      </div>
                      <div>
                        <span>Catalyst Risk</span>
                        <strong>{watchlistDetail.catalyst_risk || "--"}</strong>
                      </div>
                      <div>
                        <span>Sector Read-Through</span>
                        <strong>{watchlistDetail.sector_readthrough || "--"}</strong>
                      </div>
                    </div>
                    <div className="nt-state-grid nt-compact-grid">
                      <div><span>Price</span><strong>{formatPrice(watchlistDetail.price)}</strong></div>
                      <div><span>1D</span><strong className={metricClass(watchlistDetail.change_1d)}>{formatPercent(watchlistDetail.change_1d)}</strong></div>
                      <div><span>20D</span><strong className={metricClass(watchlistDetail.change_20d)}>{formatPercent(watchlistDetail.change_20d)}</strong></div>
                    </div>
                    <div className="nt-stack">
                      <h4>Related News</h4>
                      {watchlistDetail.related_news.map((item) => (
                        <a className="nt-news-item" href={item.url} key={`${item.title}-${item.url}`} rel="noreferrer" target="_blank">
                          <strong>{item.title}</strong>
                          <span>{item.source}</span>
                        </a>
                      ))}
                    </div>
                    <div className="nt-stack">
                      <h4>World Affairs Exposure</h4>
                      <ul className="plain-list">
                        {watchlistDetail.exposures.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                      </ul>
                    </div>
                    <div className="nt-stack">
                      <h4>Relevant Macro Themes</h4>
                      {watchlistDetail.world_affairs.map((item) => (
                        <div className="nt-list-item" key={`${item.title}-${item.theme}`}>
                          <strong>{item.theme}</strong>
                          <span>{item.region} • {item.severity}</span>
                          <p>{item.why_it_matters}</p>
                        </div>
                      ))}
                    </div>
                    <div className="nt-stack">
                      <h4>Relevant Timeline</h4>
                      {watchlistDetail.narrative_timeline.map((item) => (
                        <div className="nt-list-item" key={`${item.title}-${item.published_at}`}>
                          <strong>{item.title}</strong>
                          <span>{item.theme} • {item.region}</span>
                          <p><strong>Reaction:</strong> {item.market_reaction}</p>
                          <p><strong>Now:</strong> {item.current_implication}</p>
                        </div>
                      ))}
                    </div>
                    <div className="nt-stack">
                      <h4>Calendar</h4>
                      {watchlistDetail.calendar_events.map((item) => (
                        <div className="nt-list-item" key={`${item.title}-${item.timing}`}>
                          <strong>{item.title}</strong>
                          <span>{item.timing}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  signalsHydrating ? <SkeletonList rows={4} /> : <p>Select a watchlist ticker to inspect signal, related news, and scheduled catalysts.</p>
                )}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Watchlist News</span>
                <div className="nt-stack">
                  {firstItems(data?.watchlistNews, 6).map((item) => (
                    <a className="nt-news-item" href={item.url} key={`${item.title}-${item.url}`} rel="noreferrer" target="_blank">
                      <strong>{item.title}</strong>
                      <span>{item.source} • {item.matched_symbols.join(", ")}</span>
                    </a>
                  ))}
                  {signalsHydrating && !data?.watchlistNews.length ? <SkeletonList rows={4} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Catalyst Calendar</span>
                <div className="nt-stack">
                  {firstItems(data?.catalysts, 6).map((item) => (
                    <div className="nt-list-item" key={`${item.title}-${item.timing}`}>
                      <strong>{item.title}</strong>
                      <span>{item.timing} • {item.category}</span>
                      <p>{item.detail}</p>
                    </div>
                  ))}
                  {signalsHydrating && !data?.catalysts.length ? <SkeletonList rows={4} /> : null}
                </div>
              </article>
            </section>
          ) : null}

          {activeView === "desk" ? (
            <section className="nt-view nt-desk">
              <article className="nt-panel nt-card">
                <span className="eyebrow">Desk Workspace</span>
                {data?.workspace ? (
                  <div className="nt-copy">
                    <p><strong>{data.workspace.name}</strong></p>
                    <p>Invite code: {data.workspace.invite_code}</p>
                    <p>Members: {data.workspace.members.length}</p>
                  </div>
                ) : (
                  <p className="muted-copy">No shared desk yet. Create one or join an existing desk.</p>
                )}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Desk Controls</span>
                <form className="nt-form" onSubmit={(event) => void handleCreateDesk(event)}>
                  <input className="nt-input" onChange={(event) => setDeskNameInput(event.target.value)} placeholder="Desk name" value={deskNameInput} />
                  <button className="button button-primary" disabled={saving === "desk-create"} type="submit">
                    {saving === "desk-create" ? "Creating..." : "Create Desk"}
                  </button>
                </form>
                <form className="nt-form" onSubmit={(event) => void handleJoinDesk(event)}>
                  <input className="nt-input" onChange={(event) => setDeskCodeInput(event.target.value)} placeholder="Invite code" value={deskCodeInput} />
                  <button className="button button-primary" disabled={saving === "desk-join"} type="submit">
                    {saving === "desk-join" ? "Joining..." : "Join Desk"}
                  </button>
                </form>
                <form className="nt-form" onSubmit={(event) => void handleDeskSymbol(event)}>
                  <input className="nt-input" onChange={(event) => setDeskSymbolInput(event.target.value)} placeholder="Shared symbol" value={deskSymbolInput} />
                  <button className="button" disabled={saving === "desk-symbol"} type="submit">Add Shared Symbol</button>
                </form>
                <form className="nt-form" onSubmit={(event) => void handleDeskNote(event)}>
                  <input className="nt-input" onChange={(event) => setDeskNoteInput(event.target.value)} placeholder="Desk note for the team" value={deskNoteInput} />
                  <button className="button" disabled={saving === "desk-note"} type="submit">Post Note</button>
                </form>
                <button className="button button-primary" disabled={saving === "desk-snapshot"} onClick={() => void handleDeskSnapshot()} type="button">
                  {saving === "desk-snapshot" ? "Saving..." : "Save Desk Briefing"}
                </button>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Members</span>
                <div className="nt-stack">
                  {firstItems(data?.workspace?.members, 6).map((member) => (
                    <div className="nt-symbol" key={member.id}>
                      <div>
                        <strong>{member.name}</strong>
                        <span>{member.email}</span>
                      </div>
                      <div>
                        <span>{member.role}</span>
                        <strong>{member.tier}</strong>
                      </div>
                    </div>
                  ))}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Shared Symbols</span>
                <div className="nt-stack">
                  {firstItems(data?.workspace?.watchlist, 8).map((item) => (
                    <div className="nt-symbol" key={item.symbol}>
                      <div>
                        <strong>{item.symbol}</strong>
                        <span>{item.label}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Desk Alerts</span>
                <div className="nt-stack">
                  {firstItems(data?.workspace?.alerts, 4).map((alert) => (
                    <div className={`nt-alert ${alert.severity}`} key={`${alert.title}-${alert.message}`}>
                      <strong>{alert.title}</strong>
                      <p>{alert.message}</p>
                    </div>
                  ))}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Desk Notes</span>
                <div className="nt-stack">
                  {firstItems(data?.workspace?.notes, 5).map((note) => (
                    <div className="nt-list-item" key={note.id}>
                      <strong>{note.author_name}</strong>
                      <span>{formatDateTime(note.created_at)}</span>
                      <p>{note.content}</p>
                    </div>
                  ))}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Briefing Snapshots</span>
                <div className="nt-stack">
                  {firstItems(data?.workspace?.briefing_snapshots, 5).map((item) => (
                    <div className="nt-list-item" key={item.id}>
                      <strong>{item.headline}</strong>
                      <span>{item.author_name} • {formatDateTime(item.created_at)}</span>
                      <p>{item.overview}</p>
                    </div>
                  ))}
                </div>
              </article>
            </section>
          ) : null}

          {activeView === "news" ? (
            <section className="nt-view nt-news">
              <article className="nt-panel nt-card nt-news-primary">
                <span className="eyebrow">Market News</span>
                <div className="nt-stack">
                  {firstItems(data?.news, 8).map((item) => (
                    <a className="nt-news-item" href={item.url} key={`${item.title}-${item.url}`} rel="noreferrer" target="_blank">
                      <strong>{item.title}</strong>
                      <span>{item.source} • {formatDateTime(item.published_at)}</span>
                      <p>{item.summary || item.tags.join(" • ")}</p>
                    </a>
                  ))}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Watchlist-Matched News</span>
                <div className="nt-stack">
                  {firstItems(data?.watchlistNews, 6).map((item) => (
                    <a className="nt-news-item" href={item.url} key={`${item.title}-${item.url}-watchlist`} rel="noreferrer" target="_blank">
                      <strong>{item.title}</strong>
                      <span>{item.matched_symbols.join(", ")} • {item.source}</span>
                    </a>
                  ))}
                </div>
              </article>
            </section>
          ) : null}

          {activeView === "system" ? (
            <section className="nt-view nt-system">
              <article className="nt-panel nt-card">
                <span className="eyebrow">Account</span>
                <div className="nt-state-grid nt-settings-summary">
                  <div>
                    <span>User</span>
                    <strong>{data?.me?.name || "--"}</strong>
                  </div>
                  <div>
                    <span>Email</span>
                    <strong>{data?.me?.email || "--"}</strong>
                  </div>
                  <div>
                    <span>Plan</span>
                    <strong>{data?.me?.tier?.toUpperCase() || "--"}</strong>
                  </div>
                  <div>
                    <span>Briefing Cadence</span>
                    <strong>{labelizeKey(deliveryForm.cadence || "premarket")}</strong>
                  </div>
                </div>
                <div className="nt-plan-current">
                  <span className="eyebrow">Current Plan</span>
                  <strong>{data?.me?.tier?.toUpperCase() || "--"}</strong>
                  <form className="nt-plan-form" onSubmit={(event) => void handleTierSubmit(event)}>
                    <select className="nt-input nt-select" onChange={(event) => setSelectedTier(event.target.value)} value={selectedTier}>
                      {(data?.tiers || []).map((tier) => (
                        <option key={tier.tier} value={tier.tier}>
                          {tier.label}
                        </option>
                      ))}
                    </select>
                    <button className="button button-primary nt-settings-button" disabled={saving === "tier"} type="submit">
                      {saving === "tier" ? "Updating..." : "Update Plan"}
                    </button>
                  </form>
                </div>
              </article>

              <article className="nt-panel nt-card nt-settings-wide">
                <span className="eyebrow">Delivery Preferences</span>
                <form className="nt-form" onSubmit={(event) => void handleDeliverySubmit(event)}>
                  <div className="nt-settings-split">
                    <div className="nt-settings-group">
                      <span className="eyebrow">Destinations</span>
                      <label className="nt-simple-toggle">
                        <input
                          checked={deliveryForm.email_enabled}
                          onChange={(event) => setDeliveryForm((current) => ({ ...current, email_enabled: event.target.checked }))}
                          type="checkbox"
                        />
                        <div>
                          <strong>Email Briefing</strong>
                          <span>Send the macro briefing to your account email.</span>
                        </div>
                      </label>
                      <label className="nt-simple-toggle">
                        <input
                          checked={deliveryForm.webhook_enabled}
                          onChange={(event) => setDeliveryForm((current) => ({ ...current, webhook_enabled: event.target.checked }))}
                          type="checkbox"
                        />
                        <div>
                          <strong>Webhook Delivery</strong>
                          <span>Forward updates into an external workflow.</span>
                        </div>
                      </label>
                    </div>
                    <div className="nt-settings-group">
                      <label className="nt-settings-inline-field">
                        <span className="eyebrow">Cadence</span>
                        <select
                          className="nt-input nt-settings-select"
                          onChange={(event) => setDeliveryForm((current) => ({ ...current, cadence: event.target.value }))}
                          value={deliveryForm.cadence}
                        >
                          {cadenceOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      {deliveryForm.webhook_enabled ? (
                        <label className="nt-settings-inline-field">
                          <span className="eyebrow">Webhook URL</span>
                          <input
                            className="nt-input"
                            onChange={(event) => setDeliveryForm((current) => ({ ...current, webhook_url: event.target.value }))}
                            placeholder="https://..."
                            value={deliveryForm.webhook_url}
                          />
                        </label>
                      ) : null}
                      {deliveryResult ? (
                        <div className="nt-settings-result">
                          <strong>{deliveryResult.headline}</strong>
                          <span>{labelizeKey(deliveryResult.cadence)}</span>
                          <p>Email: {deliveryResult.email_status} | Webhook: {deliveryResult.webhook_status}</p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                  <div className="nt-settings-action-row">
                    <button className="button button-primary nt-settings-button" disabled={saving === "delivery"} type="submit">
                      {saving === "delivery" ? "Saving..." : "Save Preferences"}
                    </button>
                    <button className="button nt-settings-button" disabled={saving === "macro-delivery"} onClick={() => void handleMacroDeliverySend()} type="button">
                      {saving === "macro-delivery" ? "Sending..." : "Send Global Macro Brief"}
                    </button>
                  </div>
                </form>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Model Summary</span>
                <div className="nt-stack nt-settings-compact">
                  {Object.entries(data?.metadata.training || {}).slice(0, 8).map(([key, value]) => (
                    <div className="nt-symbol" key={key}>
                      <div>
                        <strong>{labelizeKey(key)}</strong>
                      </div>
                      <div>
                        <strong>{formatSettingValue(value)}</strong>
                      </div>
                    </div>
                  ))}
                  {!Object.keys(data?.metadata.training || {}).length ? <SkeletonList rows={4} /> : null}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Model Drivers</span>
                <div className="nt-stack nt-settings-compact">
                  {Object.entries(data?.metadata.feature_importance || {})
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 6)
                    .map(([feature, value]) => (
                      <div className="nt-symbol" key={feature}>
                        <div>
                          <strong>{labelizeKey(feature)}</strong>
                        </div>
                        <div>
                          <strong>{value.toFixed(4)}</strong>
                        </div>
                      </div>
                    ))}
                  {!Object.keys(data?.metadata.feature_importance || {}).length ? <SkeletonList rows={4} /> : null}
                </div>
              </article>
            </section>
          ) : null}

        </section>
      </div>
    </main>
  );
}
