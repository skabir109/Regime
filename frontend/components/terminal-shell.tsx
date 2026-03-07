"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { feature } from "topojson-client";
import { geoCentroid, geoGraticule10, geoNaturalEarth1, geoPath } from "d3-geo";
import worldAtlasCountries from "world-atlas/countries-110m.json";
import { useClerk } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";

type ViewKey = "monitor" | "briefing" | "world" | "markets" | "signals" | "desk" | "news" | "system";

type User = {
  id: number;
  email: string;
  name: string;
  tier: string;
  created_at: string;
  tier_selection_required?: boolean;
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

type PlaybookAssetAllocation = {
  asset: string;
  weight: string;
  target: string;
};

type Playbook = {
  title: string;
  posture: string;
  actions: string[];
  asset_allocation: PlaybookAssetAllocation[];
  tactical_watch: string;
};

type MarketStateSummary = {
  regime: string;
  confidence: number;
  breadth: string;
  volatility_state: string;
  trend_strength: string;
  cross_asset_confirmation: string;
  summary: string;
  executive_summary: string;
  playbook?: Playbook;
  drivers: RegimeDriver[];
  warnings: string[];
  leaders: MarketLeader[];
  laggards: MarketLeader[];
  supporting_signals: string[];
  conflicting_signals: string[];
  changes_since_yesterday: string[];
  what_matters_now: string[];
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
  sentiment: string;
  directional_bias: string;
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
  intensity: number;
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
  sentiment: string;
  directional_bias: string;
  themes: string[];
  drivers: string[];
  market_links: string[];
};

type StressTestAssetImpact = {
  symbol: string;
  impact_direction: string;
  magnitude: string;
  rationale: string;
};

type StressTestResult = {
  theme: string;
  scenario_description: string;
  affected_assets: StressTestAssetImpact[];
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

type AIAnalyzeResponse = {
  mode: string;
  content: string;
  attempts: number;
  model: string;
  validator_passed: boolean;
  validation_errors: string[];
};

type ParsedAIBriefing = {
  headline: string;
  whatChanged: string[];
  marketImplications: string[];
  watchlistImpact: string[];
  bullCase: string[];
  bearCase: string[];
  riskFlags: string[];
  nextActions: string[];
};

type ParsedAISections = {
  order: string[];
  sections: Record<string, string[]>;
};

type GeoRegionKey =
  | "north_america"
  | "south_america"
  | "europe"
  | "africa"
  | "middle_east"
  | "asia"
  | "oceania";

type GeoRegionDescriptor = {
  key: GeoRegionKey;
  label: string;
  center: [number, number];
};

type GeoRegionHeat = GeoRegionDescriptor & {
  rawScore: number;
  intensity: number;
  fill: string;
};

type WorldCountryPath = {
  id: string;
  name: string;
  path: string;
  region: GeoRegionKey;
  centroid: [number, number];
  center: [number, number];
};

type CountryHeatPoint = WorldCountryPath & {
  rawScore: number;
  intensity: number;
  fill: string;
  drivers: string[];
};

type WorldWsPayload = {
  type: "world_update";
  as_of: string;
  world_affairs: WorldAffairsEvent[];
  world_regions: WorldAffairsRegionSummary[];
  world_briefing: WorldAffairsBriefing;
  world_timeline: NarrativeTimelineItem[];
};

type MapViewport = {
  scale: number;
  tx: number;
  ty: number;
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
  slack_enabled: boolean;
  slack_webhook_url: string;
  discord_enabled: boolean;
  discord_webhook_url: string;
  cadence: string;
  timezone: string;
};

type BriefingDeliveryResult = {
  headline: string;
  cadence: string;
  email_status: string;
  webhook_status: string;
  slack_status?: string;
  discord_status?: string;
  delivery_channels: string[];
};

type SubscriptionTier = {
  tier: string;
  label: string;
  description: string;
  watchlist_limit: number;
  email_delivery: boolean;
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
  world_timeline: NarrativeTimelineItem[];
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

const tierOrder: Record<string, number> = {
  free: 0,
  pro: 1,
  desk: 2,
};

const viewTierAccess: Record<ViewKey, "free" | "pro" | "desk"> = {
  monitor: "free",
  signals: "free",
  system: "free",
  briefing: "pro",
  world: "pro",
  markets: "pro",
  news: "pro",
  desk: "desk",
};

const tierWorkspaceHighlights: Record<string, string[]> = {
  free: ["Overview", "Signals", "Settings"],
  pro: ["Briefing", "World Affairs", "Markets", "News"],
  desk: ["Desk workspace", "Shared alerts", "Desk snapshots"],
};

const tierUpgradeCopy: Record<string, { nextTier: string; features: string[] }> = {
  free: {
    nextTier: "Pro",
    features: ["Global macro briefing", "World Affairs monitor", "Cross-asset markets", "Full news workspace"],
  },
  pro: {
    nextTier: "Desk",
    features: ["Shared workspace", "Team watchlist", "Desk notes and snapshots"],
  },
  desk: {
    nextTier: "",
    features: [],
  },
};

const cadenceOptions = [
  { value: "premarket", label: "Pre-Market" },
  { value: "intraday", label: "Intraday" },
  { value: "eod", label: "End Of Day" },
];

const timezoneOptions = [
  { value: "local", label: "Local (Browser)" },
  { value: "America/Toronto", label: "America/Toronto (ET)" },
  { value: "America/New_York", label: "America/New_York (ET)" },
  { value: "America/Chicago", label: "America/Chicago (CT)" },
  { value: "America/Denver", label: "America/Denver (MT)" },
  { value: "America/Los_Angeles", label: "America/Los_Angeles (PT)" },
  { value: "UTC", label: "UTC" },
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

function toDate(value: string): Date | null {
  const raw = value.trim();
  if (!raw) {
    return null;
  }

  // If timestamp has no timezone, treat it as UTC for consistent cross-feed handling.
  const looksIsoNoTz = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(raw);
  const looksSpaceNoTz = /^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$/.test(raw);
  const normalized = looksIsoNoTz
    ? `${raw}Z`
    : looksSpaceNoTz
      ? `${raw.replace(" ", "T")}Z`
      : raw;

  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
}

function formatDateTime(value?: string | null, timezoneName: string = "local") {
  if (!value) {
    return "--";
  }
  const date = toDate(value);
  if (!date) {
    return value;
  }
  try {
    const options =
      timezoneName && timezoneName !== "local"
        ? ({ timeZone: timezoneName } as Intl.DateTimeFormatOptions)
        : undefined;
    return `${date.toLocaleDateString(undefined, options)} ${date.toLocaleTimeString(undefined, options)}`;
  } catch {
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
  }
}

function buildWorldWsUrl() {
  const explicit = (process.env.NEXT_PUBLIC_WS_BASE_URL || "").trim();
  if (explicit) {
    return `${explicit.replace(/\/$/, "")}/ws/world-affairs`;
  }
  const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
  if (apiBase.startsWith("http://") || apiBase.startsWith("https://")) {
    const wsBase = apiBase
      .replace(/^http:\/\//, "ws://")
      .replace(/^https:\/\//, "wss://")
      .replace(/\/api\/?$/, "");
    return `${wsBase.replace(/\/$/, "")}/ws/world-affairs`;
  }
  if (typeof window === "undefined") {
    return "";
  }
  return `${window.location.protocol === "https:" ? "wss" : "ws"}://127.0.0.1:8000/ws/world-affairs`;
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

function newsKey(title: string, url: string) {
  return `${url || ""}::${(title || "").trim().toLowerCase()}`;
}

function labelizeKey(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function hasTierAccess(userTier: string | undefined, requiredTier: "free" | "pro" | "desk") {
  const current = tierOrder[userTier || "free"] ?? 0;
  return current >= tierOrder[requiredTier];
}

function canAccessView(view: ViewKey, userTier: string | undefined) {
  return hasTierAccess(userTier, viewTierAccess[view]);
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

function stripMarkdown(value: string) {
  return value.replace(/\*\*/g, "").trim();
}

function splitInlineBullets(value: string) {
  const cleaned = stripMarkdown(value).replace(/\s+/g, " ").trim();
  if (!cleaned) {
    return [];
  }
  if (!cleaned.includes("•")) {
    return [cleaned];
  }
  return cleaned
    .split(/\s*•\s*/g)
    .map((part) => part.trim())
    .filter(Boolean);
}

function uniqueItems(items: string[], limit: number) {
  const seen = new Set<string>();
  const output: string[] = [];
  for (const raw of items) {
    const item = stripMarkdown(raw).replace(/\s+/g, " ").trim();
    const key = item.toLowerCase();
    if (!item || seen.has(key)) {
      continue;
    }
    seen.add(key);
    output.push(item);
    if (output.length >= limit) {
      break;
    }
  }
  return output;
}

function conciseFocusItem(item: string) {
  const compact = stripMarkdown(item).replace(/\s+/g, " ").trim();
  if (!compact.includes(";")) {
    return compact;
  }
  const parts = compact.split(";").map((part) => part.trim()).filter(Boolean);
  return parts.slice(0, 2).join("; ");
}

function parseAISections(content: string): ParsedAISections {
  const parsed: ParsedAISections = { order: [], sections: {} };
  let current = "";
  const lines = (content || "").split(/\r?\n/);

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }
    const isBullet = /^(?:-|[*]|\d+[.])\s+/.test(line);
    const headerMatch = line.match(/^\*{0,2}([A-Za-z0-9\-/ ]+)\*{0,2}:\*{0,2}\s*(.*)$/);

    if (!isBullet && headerMatch) {
      const header = stripMarkdown(headerMatch[1]).trim();
      current = header;
      if (!parsed.sections[current]) {
        parsed.sections[current] = [];
        parsed.order.push(current);
      }
      const trailing = stripMarkdown(headerMatch[2] || "");
      if (trailing) {
        parsed.sections[current].push(...splitInlineBullets(trailing));
      }
      continue;
    }

    const bulletMatch = line.match(/^(?:-|[*]|\d+[.])\s+(.*)$/);
    const values = splitInlineBullets((bulletMatch ? bulletMatch[1] : line) || "");
    if (!values.length || !current) {
      continue;
    }
    parsed.sections[current].push(...values);
  }

  return parsed;
}

function pickSectionItems(parsed: ParsedAISections | null, headers: string[], limit = 4) {
  if (!parsed) {
    return [];
  }
  const merged: string[] = [];
  for (const name of headers) {
    const items = parsed.sections[name] || [];
    merged.push(...items);
  }
  return uniqueItems(merged, limit);
}

function parseAIBriefingContent(content: string): ParsedAIBriefing {
  const parsed: ParsedAIBriefing = {
    headline: "",
    whatChanged: [],
    marketImplications: [],
    watchlistImpact: [],
    bullCase: [],
    bearCase: [],
    riskFlags: [],
    nextActions: [],
  };

  const sectionMap: Record<string, keyof ParsedAIBriefing> = {
    headline: "headline",
    "what changed": "whatChanged",
    "market implications": "marketImplications",
    "watchlist impact": "watchlistImpact",
    "bull case": "bullCase",
    "bear case": "bearCase",
    "risk flags": "riskFlags",
    "next actions": "nextActions",
  };

  let currentSection: keyof ParsedAIBriefing | "" = "";
  const lines = content.split(/\r?\n/);

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }

    const headerMatch = line.match(/^\*{0,2}([A-Za-z0-9\-/ ]+):\*{0,2}(.*)$/);
    const isBullet = /^(?:-|[*]|\d+[.])\s+/.test(line);
    if (!isBullet && headerMatch) {
      const normalizedHeader = stripMarkdown(headerMatch[1]).toLowerCase();
      const mapped = sectionMap[normalizedHeader];
      currentSection = mapped || "";
      const trailing = stripMarkdown(headerMatch[2] || "");
      if (currentSection === "headline" && trailing) {
        parsed.headline = splitInlineBullets(trailing)[0] || trailing;
      } else if (currentSection && trailing && currentSection !== "headline") {
        (parsed[currentSection] as string[]).push(...splitInlineBullets(trailing));
      }
      continue;
    }

    const bulletMatch = line.match(/^(?:-|[*]|\d+[.])\s+(.*)$/);
    const values = splitInlineBullets((bulletMatch ? bulletMatch[1] : line) || "");
    if (!values.length || !currentSection) {
      continue;
    }

    if (currentSection === "headline") {
      if (!parsed.headline) {
        parsed.headline = values[0];
      }
      continue;
    }

    (parsed[currentSection] as string[]).push(...values);
  }

  return parsed;
}

const GEO_REGIONS: GeoRegionDescriptor[] = [
  {
    key: "north_america",
    label: "North America",
    center: [90, 84],
  },
  {
    key: "south_america",
    label: "South America",
    center: [136, 192],
  },
  {
    key: "europe",
    label: "Europe",
    center: [272, 76],
  },
  {
    key: "africa",
    label: "Africa",
    center: [278, 152],
  },
  {
    key: "middle_east",
    label: "Middle East",
    center: [322, 106],
  },
  {
    key: "asia",
    label: "Asia",
    center: [388, 112],
  },
  {
    key: "oceania",
    label: "Oceania",
    center: [442, 192],
  },
];

function countryRegionFromCentroid(lon: number, lat: number): GeoRegionKey {
  if (lon >= 30 && lon <= 66 && lat >= 12 && lat <= 42) {
    return "middle_east";
  }
  if (lon < -25 && lat < 15) {
    return "south_america";
  }
  if (lon < -25) {
    return "north_america";
  }
  if (lon >= -26 && lon <= 46 && lat >= 35) {
    return "europe";
  }
  if (lon >= -20 && lon <= 55 && lat > -35 && lat < 38) {
    return "africa";
  }
  if (lon >= 110 && lat <= -10) {
    return "oceania";
  }
  return "asia";
}

function buildWorldMapPaths() {
  const countries = feature(
    worldAtlasCountries as never,
    (worldAtlasCountries as { objects: { countries: unknown } }).objects.countries as never,
  ) as unknown as {
    features: Array<{ id?: string | number; properties?: { name?: string } }>;
  };

  const projection = geoNaturalEarth1().fitExtent([[24, 18], [496, 262]], countries as never);
  const pathGenerator = geoPath(projection);
  const graticulePath = pathGenerator(geoGraticule10()) || "";

  const countryPaths: WorldCountryPath[] = [];
  for (const country of countries.features) {
    const path = pathGenerator(country as never);
    if (!path) {
      continue;
    }
    const [lon, lat] = geoCentroid(country as never);
    const center = projection([lon, lat]) || [0, 0];
    countryPaths.push({
      id: String(country.id ?? `${lon}-${lat}`),
      name: country.properties?.name || `Country ${String(country.id ?? "")}`,
      path,
      region: countryRegionFromCentroid(lon, lat),
      centroid: [lon, lat],
      center: [center[0], center[1]],
    });
  }

  return { countryPaths, graticulePath };
}

const WORLD_MAP = buildWorldMapPaths();

function toGeoRegionKey(value: string): GeoRegionKey | null {
  const normalized = value.toLowerCase();
  if (normalized.includes("middle_east") || normalized.includes("middle-east")) {
    return "middle_east";
  }
  if (normalized.includes("north america") || normalized.includes("u.s.") || normalized.includes("united states")) {
    return "north_america";
  }
  if (normalized.includes("south america") || normalized.includes("latam") || normalized.includes("latin america")) {
    return "south_america";
  }
  if (normalized.includes("europe") || normalized.includes("eu")) {
    return "europe";
  }
  if (normalized.includes("africa")) {
    return "africa";
  }
  if (normalized.includes("middle east") || normalized.includes("mena") || normalized.includes("gulf")) {
    return "middle_east";
  }
  if (normalized.includes("asia") || normalized.includes("china") || normalized.includes("japan") || normalized.includes("india")) {
    return "asia";
  }
  if (normalized.includes("oceania") || normalized.includes("australia") || normalized.includes("new zealand")) {
    return "oceania";
  }
  return null;
}

const GEO_KEYWORDS: Record<GeoRegionKey, string[]> = {
  north_america: ["north america", "united states", "u.s.", "us ", "canada", "mexico"],
  south_america: ["south america", "latam", "latin america", "brazil", "argentina", "chile", "colombia", "peru"],
  europe: ["europe", "eu", "uk ", "united kingdom", "france", "germany", "italy", "spain", "ukraine", "russia", "nato"],
  africa: ["africa", "egypt", "algeria", "morocco", "nigeria", "ethiopia", "south africa", "sudan", "libya"],
  middle_east: [
    "middle east", "mena", "gulf", "iran", "israel", "gaza", "lebanon", "syria", "yemen", "saudi", "uae", "qatar", "oman", "iraq", "jordan", "red sea", "hormuz", "houthi",
  ],
  asia: ["asia", "china", "japan", "india", "taiwan", "korea", "pakistan", "indonesia", "philippines", "vietnam"],
  oceania: ["oceania", "australia", "new zealand"],
};

function inferGeoRegionKey(...values: Array<string | null | undefined>): GeoRegionKey | null {
  const text = values
    .filter(Boolean)
    .map((value) => String(value).toLowerCase())
    .join(" ");

  const explicit = toGeoRegionKey(text);
  if (explicit) {
    return explicit;
  }
  for (const [key, words] of Object.entries(GEO_KEYWORDS) as Array<[GeoRegionKey, string[]]>) {
    if (words.some((word) => text.includes(word))) {
      return key;
    }
  }
  return null;
}

function fallbackThemeRegion(theme: string): GeoRegionKey | null {
  const normalized = theme.toLowerCase();
  if (normalized.includes("china")) {
    return "asia";
  }
  if (normalized.includes("geopolitical") || normalized.includes("war") || normalized.includes("conflict")) {
    return "middle_east";
  }
  if (normalized.includes("energy")) {
    return "middle_east";
  }
  return null;
}

function severityWeight(value: string) {
  const normalized = value.toLowerCase();
  if (normalized.includes("critical")) {
    return 1.0;
  }
  if (normalized.includes("high")) {
    return 0.75;
  }
  if (normalized.includes("medium")) {
    return 0.45;
  }
  if (normalized.includes("low")) {
    return 0.2;
  }
  return 0.3;
}

function urgencyWeight(value: string) {
  const normalized = value.toLowerCase();
  if (normalized.includes("high") || normalized.includes("immediate")) {
    return 0.45;
  }
  if (normalized.includes("medium")) {
    return 0.25;
  }
  if (normalized.includes("low")) {
    return 0.1;
  }
  return 0.2;
}

function heatColor(intensity: number) {
  const t = Math.max(0, Math.min(1, intensity));
  // Transition from Cyan (87, 212, 255) to Red (255, 109, 123)
  const r = Math.round(87 + (255 - 87) * t);
  const g = Math.round(212 + (109 - 212) * t);
  const b = Math.round(255 + (123 - 255) * t);
  const a = (0.28 + t * 0.62).toFixed(2);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

function buildGeoHeatmapScores(regions: WorldAffairsRegionSummary[], events: WorldAffairsEvent[]): GeoRegionHeat[] {
  const scores = new Map<GeoRegionKey, number>();

  for (const shape of GEO_REGIONS) {
    scores.set(shape.key, 0);
  }

  for (const region of regions || []) {
    const countScore = Math.max(0, region.theme_count || 0) * 0.4;
    const intensityScore = (region.intensity || 0) * 1.8;
    const totalRegionScore = countScore + intensityScore;
    
    const key = inferGeoRegionKey(region.region, region.headline, region.active_themes.join(" "));
    if (key) {
      const current = scores.get(key) || 0;
      scores.set(key, current + totalRegionScore);
      continue;
    }
    const spillover = totalRegionScore * 0.12;
    for (const descriptor of GEO_REGIONS) {
      scores.set(descriptor.key, (scores.get(descriptor.key) || 0) + spillover);
    }
  }

  for (const event of events || []) {
    const eventScore = severityWeight(event.severity || "") + urgencyWeight(event.urgency || "");
    const key = inferGeoRegionKey(event.region, event.theme, event.title, event.summary) || fallbackThemeRegion(event.theme);
    if (key) {
      const current = scores.get(key) || 0;
      scores.set(key, current + eventScore);
      continue;
    }
    const spillover = eventScore * 0.15;
    for (const descriptor of GEO_REGIONS) {
      scores.set(descriptor.key, (scores.get(descriptor.key) || 0) + spillover);
    }
  }

  const maxScore = Math.max(0.001, ...Array.from(scores.values()));
  return GEO_REGIONS.map((shape) => {
    const rawScore = scores.get(shape.key) || 0;
    const intensity = Math.max(0.06, Math.min(1, rawScore / maxScore));
    return {
      ...shape,
      rawScore,
      intensity,
      fill: heatColor(intensity),
    };
  });
}

const REGION_ANCHORS: Record<GeoRegionKey, [number, number]> = {
  north_america: [-100, 40],
  south_america: [-60, -15],
  europe: [15, 52],
  africa: [20, 5],
  middle_east: [45, 29],
  asia: [105, 34],
  oceania: [134, -25],
};

const EVENT_LOCATION_KEYWORDS: Array<{ keywords: string[]; coord: [number, number] }> = [
  { keywords: ["iran", "tehran"], coord: [53, 32] },
  { keywords: ["israel", "gaza", "jerusalem"], coord: [35, 31.5] },
  { keywords: ["saudi", "riyadh"], coord: [45, 24] },
  { keywords: ["red sea", "houthi", "yemen"], coord: [43, 16] },
  { keywords: ["hormuz", "oman"], coord: [57, 25] },
  { keywords: ["ukraine"], coord: [31, 49] },
  { keywords: ["russia", "moscow"], coord: [37, 56] },
  { keywords: ["china", "beijing"], coord: [104, 35] },
  { keywords: ["taiwan"], coord: [121, 24] },
  { keywords: ["japan"], coord: [138, 37] },
  { keywords: ["india"], coord: [79, 22] },
  { keywords: ["united states", "u.s.", "us "], coord: [-98, 39] },
];

type EventAnchor = {
  lon: number;
  lat: number;
  weight: number;
  eventTitle: string;
  region: GeoRegionKey;
};

function haversineKm(a: [number, number], b: [number, number]) {
  const toRad = (value: number) => (value * Math.PI) / 180;
  const dLat = toRad(b[1] - a[1]);
  const dLon = toRad(b[0] - a[0]);
  const lat1 = toRad(a[1]);
  const lat2 = toRad(b[1]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

function eventAnchors(events: WorldAffairsEvent[]) {
  const anchors: EventAnchor[] = [];
  for (const event of events || []) {
    const region = inferGeoRegionKey(event.region, event.theme, event.title, event.summary) || fallbackThemeRegion(event.theme) || "asia";
    const text = `${event.title} ${event.summary || ""} ${event.region} ${event.theme}`.toLowerCase();
    const baseWeight = severityWeight(event.severity || "") + urgencyWeight(event.urgency || "");
    const matches = EVENT_LOCATION_KEYWORDS.filter((item) => item.keywords.some((keyword) => text.includes(keyword)));

    if (matches.length) {
      for (const match of matches.slice(0, 2)) {
        anchors.push({
          lon: match.coord[0],
          lat: match.coord[1],
          weight: baseWeight,
          eventTitle: event.title,
          region,
        });
      }
      continue;
    }

    const fallback = REGION_ANCHORS[region];
    anchors.push({
      lon: fallback[0],
      lat: fallback[1],
      weight: baseWeight,
      eventTitle: event.title,
      region,
    });
  }
  return anchors;
}

function buildCountryHeatmap(countries: WorldCountryPath[], geoHeatmap: GeoRegionHeat[], events: WorldAffairsEvent[]): CountryHeatPoint[] {
  const anchors = eventAnchors(events);
  const regionIntensity = new Map<GeoRegionKey, number>(geoHeatmap.map((item) => [item.key, item.intensity]));
  const scored = countries.map((country) => {
    let raw = (regionIntensity.get(country.region) || 0) * 0.35;
    const drivers: Array<{ title: string; value: number }> = [];

    for (const anchor of anchors) {
      const distance = haversineKm(country.centroid, [anchor.lon, anchor.lat]);
      const spread = anchor.region === country.region ? 2200 : 1500;
      const contribution = anchor.weight * Math.exp(-((distance / spread) ** 2));
      raw += contribution;
      if (contribution > 0.025) {
        drivers.push({ title: anchor.eventTitle, value: contribution });
      }
    }

    const topDrivers = [...drivers]
      .sort((a, b) => b.value - a.value)
      .map((item) => item.title)
      .filter((title, index, list) => list.indexOf(title) === index)
      .slice(0, 2);

    return { country, raw, topDrivers };
  });

  const maxRaw = Math.max(0.001, ...scored.map((item) => item.raw));
  return scored.map(({ country, raw, topDrivers }) => {
    const intensity = Math.max(0.05, Math.min(1, raw / maxRaw));
    return {
      ...country,
      rawScore: raw,
      intensity,
      fill: heatColor(intensity),
      drivers: topDrivers,
    };
  });
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
    executive_summary: "",
    drivers: [],
    warnings: [],
    leaders: [],
    laggards: [],
    supporting_signals: [],
    conflicting_signals: [],
    changes_since_yesterday: [],
    what_matters_now: [],
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
    slack_enabled: false,
    slack_webhook_url: "",
    discord_enabled: false,
    discord_webhook_url: "",
    cadence: "premarket",
    timezone: "local",
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
    worldTimeline: bootstrap.world_timeline || [],
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

const walkthroughContent = [
  {
    title: "Market Regime Detection",
    text: "Our ML model classifies the current market state into Risk-On, Risk-Off, or High-Vol based on cross-asset flows.",
  },
  {
    title: "Strategic Executive Summary",
    text: "An AI-distilled take on how live news flow is either supporting or threatening the current regime.",
  },
  {
    title: "Strategic Playbook",
    text: "Actionable asset allocation tilts and tactical watches updated in real-time for your portfolio.",
  },
  {
    title: "State Pack & Probability",
    text: "Technical metrics like Breadth and Volatility that drive the model's confidence levels.",
  },
  {
    title: "Institutional Export",
    text: "Generate a clean, professional PDF report of this dashboard at any time using the 'Export Report' button.",
  },
];

function OnboardingTooltip({ step, onNext, onSkip }: { step: number; onNext: () => void; onSkip: () => void }) {
  const content = walkthroughContent[step];
  if (!content) return null;

  return (
    <div className="nt-walkthrough-overlay">
      <div className="nt-walkthrough-card">
        <span className="eyebrow">Tour: Step {step + 1} of 5</span>
        <h3>{content.title}</h3>
        <p>{content.text}</p>
        <div className="nt-actions">
          <button className="button button-small" onClick={onSkip} type="button">Skip Tour</button>
          <button className="button button-small button-primary" onClick={onNext} type="button">
            {step === 4 ? "Finish" : "Next Step"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function TerminalShell() {
  const { signOut } = useClerk();
  const [activeView, setActiveView] = useState<ViewKey>("monitor");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
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
    slack_enabled: false,
    slack_webhook_url: "",
    discord_enabled: false,
    discord_webhook_url: "",
    cadence: "premarket",
    timezone: "local",
  });
  const [selectedTier, setSelectedTier] = useState("");
  const [deliveryResult, setDeliveryResult] = useState<BriefingDeliveryResult | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [aiBriefing, setAiBriefing] = useState<AIAnalyzeResponse | null>(null);
  const [aiBriefingError, setAiBriefingError] = useState("");
  const [aiAlertDrilldown, setAiAlertDrilldown] = useState<AIAnalyzeResponse | null>(null);
  const [aiWorldAnalysis, setAiWorldAnalysis] = useState<AIAnalyzeResponse | null>(null);
  const [aiSignalsContext, setAiSignalsContext] = useState<AIAnalyzeResponse | null>(null);
  const [aiLoading, setAiLoading] = useState({
    briefing: false,
    alert: false,
    world: false,
    signals: false,
  });
  const [selectedAlertKey, setSelectedAlertKey] = useState("");
  const [walkthroughStep, setWalkthroughStep] = useState(-1);
  const [stressTestTheme, setStressTestTheme] = useState("Energy Shock");
  const [stressTestResult, setStressTestResult] = useState<StressTestResult | null>(null);
  const [stressTestLoading, setStressTestLoading] = useState(false);
  const [worldLastUpdatedAt, setWorldLastUpdatedAt] = useState<string>("");
  const [worldSocketConnected, setWorldSocketConnected] = useState(false);
  const [mapViewport, setMapViewport] = useState<MapViewport>({ scale: 1, tx: 0, ty: 0 });
  const [mapDragging, setMapDragging] = useState(false);
  const [hoveredCountry, setHoveredCountry] = useState<{
    screenX: number;
    screenY: number;
    name: string;
    region: string;
    intensity: number;
    drivers: string[];
  } | null>(null);
  const mapDragRef = useRef<{ x: number; y: number } | null>(null);
  const aiCacheRef = useRef<Map<string, { expiresAt: number; value: AIAnalyzeResponse }>>(new Map());
  const aiInflightRef = useRef<Map<string, Promise<AIAnalyzeResponse>>>(new Map());
  const aiSignatureRef = useRef({
    briefing: "",
    alert: "",
    world: "",
    signals: "",
  });
  const activeViewRef = useRef<ViewKey>("monitor");

  function handleExportPDF() {
    window.print();
  }

  function handleNextWalkthrough() {
    if (walkthroughStep >= 4) {
      setShowOnboarding(false);
      setWalkthroughStep(0);
    } else {
      setWalkthroughStep((s) => s + 1);
    }
  }

  async function loadCoreData(silent = false) {
    if (!silent) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError("");

    try {
      const bootstrap = await apiFetch<TerminalBootstrap>("/terminal/bootstrap");
      if (bootstrap.me?.tier_selection_required) {
        window.location.href = "/plans";
        return;
      }
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
              worldTimeline: bootstrap.world_timeline || current.worldTimeline,
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

  async function requestAIWithCache(
    cacheKey: string,
    payload: Record<string, unknown>,
    ttlMs = 45000,
  ): Promise<AIAnalyzeResponse> {
    const now = Date.now();
    const cached = aiCacheRef.current.get(cacheKey);
    if (cached && cached.expiresAt > now) {
      return cached.value;
    }

    const inflight = aiInflightRef.current.get(cacheKey);
    if (inflight) {
      return inflight;
    }

    const promise = apiFetch<AIAnalyzeResponse>("/ai/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    aiInflightRef.current.set(cacheKey, promise);

    try {
      const value = await promise;
      aiCacheRef.current.set(cacheKey, { value, expiresAt: now + ttlMs });
      return value;
    } finally {
      aiInflightRef.current.delete(cacheKey);
    }
  }

  async function handleGenerateBriefingAI(force = false) {
    if (!data) {
      return;
    }
    const watchlist = (data.watchlist || []).map((item) => item.symbol.toUpperCase());
    const signature = [
      data.marketState.regime,
      data.prediction.confidence.toFixed(3),
      data.marketState.breadth,
      data.marketState.volatility_state,
      data.alerts?.[0]?.title || "",
      data.worldBriefing?.headline || "",
      watchlist.join(","),
    ].join("|");
    if (!force && aiSignatureRef.current.briefing === signature) {
      return;
    }
    aiSignatureRef.current.briefing = signature;
    setAiLoading((current) => ({ ...current, briefing: true }));
    try {
      const cacheKey = `briefing:${data.marketState.regime}:${data.prediction.confidence}:${watchlist.join(",")}`;
      const aiResult = await requestAIWithCache(
        cacheKey,
        {
          mode: "BRIEFING",
          query: "Generate the current terminal briefing using the provided market context.",
          context: {
            regime: data.marketState.regime,
            confidence: data.prediction.confidence,
            breadth: data.marketState.breadth,
            volatility_state: data.marketState.volatility_state,
            trend_strength: data.marketState.trend_strength,
            top_alert: data.alerts?.[0]
              ? {
                  title: data.alerts[0].title,
                  severity: data.alerts[0].severity,
                  message: data.alerts[0].message,
                }
              : null,
            world_headline: data.worldBriefing?.headline || null,
          },
          watchlist,
          max_words: 160,
          regenerate_on_fail: false,
        },
        60000,
      );
      setAiBriefing(aiResult);
      setAiBriefingError("");
    } catch (caught) {
      setAiBriefingError(caught instanceof Error ? caught.message : "Failed to load AI briefing.");
    } finally {
      setAiLoading((current) => ({ ...current, briefing: false }));
    }
  }

  async function handleGenerateAlertAI(force = false) {
    if (!data?.alerts?.length) {
      return;
    }
    const selected =
      data.alerts.find((item) => `${item.title}::${item.message}` === selectedAlertKey) ||
      data.alerts[0];
    if (!selected) {
      return;
    }
    const watchlist = (data.watchlist || []).map((item) => item.symbol.toUpperCase());
    const signature = [
      selected.title,
      selected.severity,
      data.marketState.regime,
      data.prediction.confidence.toFixed(3),
      watchlist.join(","),
    ].join("|");
    if (!force && aiSignatureRef.current.alert === signature) {
      return;
    }
    aiSignatureRef.current.alert = signature;
    setAiLoading((current) => ({ ...current, alert: true }));
    try {
      const cacheKey = `alert:${selected.title}:${selected.message}:${watchlist.join(",")}`;
      const result = await requestAIWithCache(
        cacheKey,
        {
          mode: "ALERT_DRILLDOWN",
          query: "Explain why this alert fired and what should be monitored next.",
          context: {
            alert: {
              title: selected.title,
              severity: selected.severity,
              message: selected.message,
              symbol: selected.symbol || null,
            },
            regime: data.marketState.regime,
            confidence: data.prediction.confidence,
            breadth: data.marketState.breadth,
            volatility_state: data.marketState.volatility_state,
          },
          watchlist,
          max_words: 160,
          regenerate_on_fail: false,
        },
        60000,
      );
      setAiAlertDrilldown(result);
    } catch {
      // keep last successful output instead of clearing card
    } finally {
      setAiLoading((current) => ({ ...current, alert: false }));
    }
  }

  async function handleGenerateStressTest(theme: string) {
    if (!theme) return;
    setStressTestLoading(true);
    setStressTestTheme(theme);
    try {
      const result = await apiFetch<StressTestResult>(`/watchlist/stress-test/${encodeURIComponent(theme)}`);
      setStressTestResult(result);
    } catch {
      // keep previous result on error
    } finally {
      setStressTestLoading(false);
    }
  }

  async function handleGenerateWorldAI(force = false) {
    if (!data) {
      return;
    }
    const watchlist = (data.watchlist || []).map((item) => item.symbol.toUpperCase());
    const signature = [
      data.worldBriefing?.headline || "",
      data.worldAffairs?.[0]?.title || "",
      data.worldAffairs?.[0]?.published_at || "",
      watchlist.join(","),
    ].join("|");
    if (!force && aiSignatureRef.current.world === signature) {
      return;
    }
    aiSignatureRef.current.world = signature;
    setAiLoading((current) => ({ ...current, world: true }));
    try {
      const cacheKey = `world:${watchlist.join(",")}:${data.worldBriefing.headline}:${data.worldAffairs[0]?.title || "-"}`;
      const result = await requestAIWithCache(
        cacheKey,
        {
          mode: "WORLD_AFFAIRS",
          query: "Summarize the most relevant world-affairs theme impact for this session.",
          context: {
            world_headline: data.worldBriefing.headline,
            world_summary: data.worldBriefing.summary,
            lead_event: data.worldAffairs?.[0]
              ? {
                  title: data.worldAffairs[0].title,
                  theme: data.worldAffairs[0].theme,
                  region: data.worldAffairs[0].region,
                  urgency: data.worldAffairs[0].urgency,
                  severity: data.worldAffairs[0].severity,
                }
              : null,
            regions: firstItems(data.worldRegions, 2).map((item) => ({
              region: item.region,
              theme_count: item.theme_count,
              headline: item.headline,
            })),
          },
          watchlist,
          max_words: 160,
          regenerate_on_fail: false,
        },
        90000,
      );
      setAiWorldAnalysis(result);
    } catch {
      // keep last successful output instead of clearing card
    } finally {
      setAiLoading((current) => ({ ...current, world: false }));
    }
  }

  async function handleGenerateSignalsAI(force = false) {
    if (!data) {
      return;
    }
    const selectedSymbol =
      selectedWatchlistSymbol ||
      data.watchlistInsights[0]?.symbol ||
      data.watchlist?.[0]?.symbol ||
      "";
    if (!selectedSymbol) {
      return;
    }
    const selectedInsight = data.watchlistInsights.find((item) => item.symbol === selectedSymbol) || data.watchlistInsights[0];
    const signature = [
      selectedSymbol,
      selectedInsight?.stance || "",
      selectedInsight?.summary || "",
      data.signals?.[0]?.symbol || "",
      data.marketState.regime,
    ].join("|");
    if (!force && aiSignatureRef.current.signals === signature) {
      return;
    }
    aiSignatureRef.current.signals = signature;
    setAiLoading((current) => ({ ...current, signals: true }));
    try {
      const cacheKey = `signals:${selectedSymbol}:${selectedInsight?.summary || "-"}:${data.signals[0]?.symbol || "-"}`;
      const result = await requestAIWithCache(
        cacheKey,
        {
          mode: "WATCHLIST_CONTEXT",
          query: `Provide watchlist context for ${selectedSymbol}.`,
          context: {
            selected_symbol: selectedSymbol,
            selected_insight: selectedInsight
              ? {
                  stance: selectedInsight.stance,
                  summary: selectedInsight.summary,
                  catalyst_risk: selectedInsight.catalyst_risk,
                  sector_readthrough: selectedInsight.sector_readthrough,
                }
              : null,
            exposure: data.watchlistExposures.find((item) => item.symbol === selectedSymbol) || null,
            top_catalyst: data.catalysts?.[0]
              ? {
                  title: data.catalysts[0].title,
                  timing: data.catalysts[0].timing,
                  category: data.catalysts[0].category,
                }
              : null,
          },
          watchlist: [selectedSymbol],
          max_words: 160,
          regenerate_on_fail: false,
        },
        60000,
      );
      setAiSignalsContext(result);
    } catch {
      // keep last successful output instead of clearing card
    } finally {
      setAiLoading((current) => ({ ...current, signals: false }));
    }
  }

  async function loadViewData(view: ViewKey, force = false) {
    if (data && !canAccessView(view, data.me.tier)) {
      return;
    }
    if (!force && loadedViews[view]) {
      return;
    }

    try {
      if (view === "monitor") {
        const [alerts] = await Promise.all([apiFetch<AlertItem[]>("/alerts")]);
        setData((current) => (current ? { ...current, alerts } : current));
        if (alerts.length && !selectedAlertKey) {
          setSelectedAlertKey(`${alerts[0].title}::${alerts[0].message}`);
        }
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
          apiFetch<WorldAffairsEvent[]>("/world-affairs/monitor", { force }),
          apiFetch<WorldAffairsRegionSummary[]>("/world-affairs/regions", { force }),
          apiFetch<WorldAffairsBriefing>("/briefing/global-macro", { force }),
          apiFetch<NarrativeTimelineItem[]>("/world-affairs/timeline", { force }),
        ]);
        setData((current) =>
          current ? { ...current, worldAffairs, worldRegions, worldBriefing, worldTimeline } : current,
        );
        setWorldLastUpdatedAt(new Date().toISOString());
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

  async function refreshActiveView(includeViewData = true) {
    await loadCoreData(true);
    if (includeViewData) {
      await loadViewData(activeView, true);
    }
    if (includeViewData && activeView === "signals" && selectedWatchlistSymbol) {
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
    activeViewRef.current = activeView;
  }, [activeView]);

  useEffect(() => {
    void loadCoreData();
    const interval = window.setInterval(() => {
      if (document.hidden) {
        return;
      }
      const shouldRefreshActiveView = activeViewRef.current === "monitor";
      void refreshActiveView(shouldRefreshActiveView);
    }, 45000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!data) {
      return;
    }
    void loadViewData(activeView);
  }, [activeView, data]);

  useEffect(() => {
    if (!data || canAccessView(activeView, data.me.tier)) {
      return;
    }
    setActiveView("monitor");
  }, [activeView, data]);

  useEffect(() => {
    if (activeView !== "signals" || !selectedWatchlistSymbol || !data) {
      return;
    }
    void loadWatchlistDetail(selectedWatchlistSymbol);
  }, [activeView, selectedWatchlistSymbol, data]);

  // Smart auto-generation: initial load + signature-based refresh only when context changes.
  useEffect(() => {
    if (activeView !== "briefing" || !data || !loadedViews.briefing) {
      return;
    }
    void handleGenerateBriefingAI(false);
  }, [
    activeView,
    loadedViews.briefing,
    data?.marketState.regime,
    data?.prediction.confidence,
    data?.marketState.breadth,
    data?.marketState.volatility_state,
    data?.alerts?.[0]?.title,
    data?.worldBriefing?.headline,
    selectedWatchlistSymbol,
  ]);

  // Monitor AI drilldown is generated on explicit user action to keep initial load fast.

  useEffect(() => {
    if (activeView !== "world" || !data || !loadedViews.world) {
      return;
    }
    void handleGenerateWorldAI(false);
  }, [
    activeView,
    loadedViews.world,
    data?.worldBriefing?.headline,
    data?.worldAffairs?.[0]?.title,
    data?.worldAffairs?.[0]?.published_at,
  ]);

  useEffect(() => {
    if (activeView !== "signals" || !data || !loadedViews.signals) {
      return;
    }
    void handleGenerateSignalsAI(false);
  }, [
    activeView,
    loadedViews.signals,
    selectedWatchlistSymbol,
    data?.watchlistInsights?.[0]?.summary,
    data?.signals?.[0]?.symbol,
    data?.marketState.regime,
  ]);

  useEffect(() => {
    if (activeView !== "world" || !loadedViews.world) {
      setWorldSocketConnected(false);
      return;
    }
    const wsUrl = buildWorldWsUrl();
    if (!wsUrl) {
      setWorldSocketConnected(false);
      return;
    }

    let disposed = false;
    let reconnectTimer: number | undefined;
    let socket: WebSocket | null = null;

    const connect = () => {
      if (disposed) {
        return;
      }
      try {
        socket = new WebSocket(wsUrl);
      } catch {
        setWorldSocketConnected(false);
        reconnectTimer = window.setTimeout(connect, 2500);
        return;
      }
      socket.onopen = () => {
        setWorldSocketConnected(true);
      };
      socket.onmessage = (message) => {
        try {
          const payload = JSON.parse(message.data as string) as WorldWsPayload;
          if (payload.type !== "world_update") {
            return;
          }
          setData((current) =>
            current
              ? {
                  ...current,
                  worldAffairs: payload.world_affairs || [],
                  worldRegions: payload.world_regions || [],
                  worldBriefing: payload.world_briefing || emptyWorldBriefing(),
                  worldTimeline: payload.world_timeline || [],
                }
              : current,
          );
          setWorldLastUpdatedAt(payload.as_of || new Date().toISOString());
        } catch {
          // Ignore malformed socket payloads and keep polling fallback active.
        }
      };
      socket.onclose = () => {
        setWorldSocketConnected(false);
        if (!disposed) {
          reconnectTimer = window.setTimeout(connect, 2500);
        }
      };
      socket.onerror = () => {
        setWorldSocketConnected(false);
        socket?.close();
      };
    };

    connect();
    return () => {
      disposed = true;
      setWorldSocketConnected(false);
      if (reconnectTimer !== undefined) {
        window.clearTimeout(reconnectTimer);
      }
      socket?.close();
    };
  }, [activeView, loadedViews.world]);

  useEffect(() => {
    if (activeView !== "world" || !data || !loadedViews.world) {
      return;
    }
    if (worldSocketConnected) {
      return;
    }
    const refreshWorldData = () => {
      if (document.hidden) {
        return;
      }
      void loadViewData("world", true);
    };
    const interval = window.setInterval(refreshWorldData, 20000);
    const onVisibilityChange = () => {
      if (!document.hidden) {
        refreshWorldData();
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [activeView, data, loadedViews.world, worldSocketConnected]);

  useEffect(() => {
    const updateClock = () => setClock(new Date().toLocaleTimeString());
    updateClock();
    const interval = window.setInterval(updateClock, 1000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const stopDragging = () => {
      setMapDragging(false);
      mapDragRef.current = null;
    };
    window.addEventListener("mouseup", stopDragging);
    return () => window.removeEventListener("mouseup", stopDragging);
  }, []);

  useEffect(() => {
    if (!data) {
      return;
    }
    const onboardingKey = `regime_onboarding_${data.me.id}_${data.me.tier}`;
    if (!window.localStorage.getItem(onboardingKey)) {
      setShowOnboarding(true);
    }
  }, [data]);

  function dismissOnboarding() {
    if (data) {
      window.localStorage.setItem(`regime_onboarding_${data.me.id}_${data.me.tier}`, "seen");
    }
    setShowOnboarding(false);
    setWalkthroughStep(-1);
  }

  function navigateToView(view: ViewKey) {
    setMobileMenuOpen(false);
    if (!data) {
      setActiveView(view);
      return;
    }
    if (canAccessView(view, data.me.tier)) {
      setActiveView(view);
      return;
    }
    setActiveView("system");
  }

  async function handleLogout() {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } finally {
      await signOut({ redirectUrl: "/login" });
    }
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
      const currentTier = String(data?.me?.tier || "free").toLowerCase();
      const requestedTier = String(selectedTier || "free").toLowerCase();

      if (requestedTier !== "free" && requestedTier !== currentTier) {
        window.location.href = `/billing?tier=${encodeURIComponent(requestedTier)}`;
        return;
      }

      await apiFetch("/billing/tier", {
        method: "PUT",
        body: JSON.stringify({ tier: requestedTier }),
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

  function clampMapViewport(next: MapViewport): MapViewport {
    const scale = Math.max(1, Math.min(3.6, next.scale));
    const maxTx = ((scale - 1) * 520) / 2;
    const maxTy = ((scale - 1) * 280) / 2;
    return {
      scale,
      tx: Math.max(-maxTx, Math.min(maxTx, next.tx)),
      ty: Math.max(-maxTy, Math.min(maxTy, next.ty)),
    };
  }

  function applyZoom(multiplier: number) {
    setMapViewport((current) => clampMapViewport({ ...current, scale: current.scale * multiplier }));
  }

  function resetMapViewport() {
    setMapViewport({ scale: 1, tx: 0, ty: 0 });
    setMapDragging(false);
    mapDragRef.current = null;
  }

  const currentTier = data?.me?.tier || "free";
  const visibleViews = views.filter((view) => canAccessView(view.key, currentTier));
  const activeViewMeta = visibleViews.find((view) => view.key === activeView) || visibleViews[0] || views[0];
  const currentTierHighlights = tierWorkspaceHighlights[currentTier] || tierWorkspaceHighlights.free;
  const upgradeCopy = tierUpgradeCopy[currentTier] || tierUpgradeCopy.free;
  const overviewIntelUnlocked = hasTierAccess(currentTier, "pro");
  const emailUnlocked = hasTierAccess(currentTier, "pro");
  const webhookUnlocked = hasTierAccess(currentTier, "pro");
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
  const parsedAIBriefing = aiBriefing?.content ? parseAIBriefingContent(aiBriefing.content) : null;
  const parsedAlertDrilldown = aiAlertDrilldown?.content ? parseAISections(aiAlertDrilldown.content) : null;
  const parsedWorldAnalysis = aiWorldAnalysis?.content ? parseAISections(aiWorldAnalysis.content) : null;
  const parsedSignalsContext = aiSignalsContext?.content ? parseAISections(aiSignalsContext.content) : null;
  const briefingChecklist = uniqueItems(
    parsedAIBriefing?.marketImplications.length
      ? parsedAIBriefing.marketImplications
      : data?.briefing.checklist || [],
    4,
  );
  const briefingFocusItems = uniqueItems(
    parsedAIBriefing?.watchlistImpact.length
      ? parsedAIBriefing.watchlistImpact
      : data?.briefing.focus_items || [],
    5,
  ).map(conciseFocusItem);
  const briefingRisks = uniqueItems(
    parsedAIBriefing?.riskFlags.length || parsedAIBriefing?.bearCase.length
      ? [...(parsedAIBriefing?.riskFlags || []), ...(parsedAIBriefing?.bearCase || [])]
      : data?.briefing.risks || [],
    8,
  );
  const briefingNextActions = uniqueItems(
    parsedAIBriefing?.nextActions.length
      ? parsedAIBriefing.nextActions
      : data?.briefing.catalyst_calendar || [],
    6,
  );
  const normalizedChecklist = new Set(briefingChecklist.map((item) => item.toLowerCase()));
  const normalizedFocus = new Set(briefingFocusItems.map((item) => item.toLowerCase()));
  const briefingRisksFiltered = briefingRisks
    .filter((item) => {
      const key = item.toLowerCase();
      return !normalizedChecklist.has(key) && !normalizedFocus.has(key);
    })
    .slice(0, 4);
  const normalizedRisks = new Set(briefingRisksFiltered.map((item) => item.toLowerCase()));
  const briefingNextActionsFiltered = briefingNextActions
    .filter((item) => {
      const key = item.toLowerCase();
      return !normalizedChecklist.has(key) && !normalizedFocus.has(key) && !normalizedRisks.has(key);
    })
    .slice(0, 3);
  const briefingOverview =
    parsedAIBriefing?.whatChanged[0] ||
    data?.briefing.overview ||
    aiBriefingError;
  const alertDrivers = pickSectionItems(parsedAlertDrilldown, ["Trigger Drivers"], 4);
  const alertConflicts = pickSectionItems(parsedAlertDrilldown, ["Conflicting Evidence", "Supporting Evidence"], 4);
  const alertInvalidation = pickSectionItems(parsedAlertDrilldown, ["Invalidation Signals"], 3);
  const worldWhatMatters = pickSectionItems(parsedWorldAnalysis, ["Why It Matters Now"], 3);
  const worldFirstOrder = pickSectionItems(parsedWorldAnalysis, ["First-Order Market Effects"], 4);
  const geoHeatmap = buildGeoHeatmapScores(data?.worldRegions || [], data?.worldAffairs || []);
  const countryHeatmap = buildCountryHeatmap(WORLD_MAP.countryPaths, geoHeatmap, data?.worldAffairs || []);
  const countryHeatById = new Map<string, CountryHeatPoint>(countryHeatmap.map((item) => [item.id, item]));
  const topGeoHotspots = [...geoHeatmap]
    .sort((a, b) => b.rawScore - a.rawScore)
    .slice(0, 3)
    .filter((item) => item.rawScore > 0);
  const signalsDrivers = pickSectionItems(parsedSignalsContext, ["Key Drivers"], 4);
  const signalsChecklist = pickSectionItems(parsedSignalsContext, ["Monitoring Checklist"], 3);
  const currentTimezone = deliveryForm.timezone || data?.delivery?.timezone || "local";
  const watchlistNewsMap = new Map<string, string[]>();
  for (const item of data?.watchlistNews || []) {
    watchlistNewsMap.set(newsKey(item.title, item.url), item.matched_symbols || []);
  }
  const prioritizedNews = (data?.news || [])
    .map((item) => {
      const matchedSymbols = watchlistNewsMap.get(newsKey(item.title, item.url)) || [];
      return { item, matchedSymbols };
    })
    .sort((a, b) => {
      if (a.matchedSymbols.length && !b.matchedSymbols.length) {
        return -1;
      }
      if (!a.matchedSymbols.length && b.matchedSymbols.length) {
        return 1;
      }
      return 0;
    });
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
      <div className={`nt-grid ${mobileMenuOpen ? "menu-open" : ""}`}>
        <aside className={`nt-sidebar ${mobileMenuOpen ? "is-open" : ""}`}>
          <div className="nt-brand">
            <span className="nt-wordmark">REGIME</span>
            <p className="nt-brand-copy">Market context, catalysts, watchlists, and desk workflow.</p>
          </div>
          <nav className="nt-nav">
          {visibleViews.map((view) => (
            <button
              key={view.key}
              className={`nt-nav-item ${activeView === view.key ? "is-active" : ""}`}
              onClick={() => navigateToView(view.key)}
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
          {showOnboarding && walkthroughStep >= 0 && (
            <OnboardingTooltip
              step={walkthroughStep}
              onNext={handleNextWalkthrough}
              onSkip={() => { setShowOnboarding(false); setWalkthroughStep(0); }}
            />
          )}
          {showOnboarding && walkthroughStep === -1 ? (
            <section className="nt-overlay" role="dialog" aria-modal="true" aria-label="Welcome to Regime">
              <div className="nt-onboarding">
                <div className="nt-onboarding-head">
                  <div>
                    <span className="eyebrow">Welcome</span>
                    <h3>Start with the workflow for your plan.</h3>
                  </div>
                  <span className="nt-plan-badge">{currentTier.toUpperCase()}</span>
                </div>
                <p className="nt-onboarding-copy">
                  Regime works best when you move from market context into watchlist context, then into deeper macro or desk workflows as your plan unlocks them.
                </p>
                <div className="nt-onboarding-grid">
                  <article className="nt-panel nt-card">
                    <span className="eyebrow">Available Now</span>
                    <div className="nt-chip-row">
                      {currentTierHighlights.map((item) => (
                        <span className="nt-chip" key={item}>{item}</span>
                      ))}
                    </div>
                  </article>
                  <article className="nt-panel nt-card">
                    <span className="eyebrow">Start Here</span>
                    <ol className="nt-onboarding-steps">
                      <li>Read the market state and `What Matters Now` on Overview.</li>
                      <li>Open Signals to review your watchlist in context.</li>
                      <li>Use Settings to control delivery and your plan.</li>
                    </ol>
                  </article>
                  {upgradeCopy.features.length ? (
                    <article className="nt-panel nt-card">
                      <span className="eyebrow">{`Unlock With ${upgradeCopy.nextTier}`}</span>
                      <ul className="plain-list">
                        {upgradeCopy.features.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </article>
                  ) : null}
                </div>
                <div className="nt-onboarding-actions">
                  <button className="button button-primary" onClick={() => { setActiveView("monitor"); setWalkthroughStep(0); }} type="button">
                    Take the Tour
                  </button>
                  <button className="button" onClick={() => { setActiveView("monitor"); dismissOnboarding(); }} type="button">
                    Skip to Dashboard
                  </button>
                </div>
              </div>
            </section>
          ) : null}

          <header className="nt-header">
            <button 
              className="button button-small nt-mobile-menu-toggle" 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              type="button"
              aria-label="Toggle Menu"
            >
              {mobileMenuOpen ? "✕" : "☰"}
            </button>
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
                <span className="nt-signal"><i /> Live feed</span>
                <span className="nt-status-chip">
                  {data ? `Sync ${formatDateTime(data.prediction.timestamp, currentTimezone)}` : <SkeletonBlock width="112px" height="12px" />}
                </span>
              </div>
              <div className="nt-clock-row">
                <span className="nt-clock">{clock || "--:--:--"}</span>
              </div>
              <div className="nt-actions">
                <button className="button button-small" onClick={() => { setShowOnboarding(true); setWalkthroughStep(0); }} type="button">
                  Terminal Tour
                </button>
                <button className="button button-small button-primary" onClick={handleExportPDF} type="button">
                  Export Report
                </button>
                <button className="button" onClick={() => void refreshActiveView()} type="button">
                  {refreshing ? "Refreshing..." : "Refresh"}
                </button>
              </div>
            </div>
          </header>

          {error ? <section className="nt-banner">{error}</section> : null}

          {activeView === "monitor" ? (
            <section className="nt-view nt-overview">
              {/* First Row: Hero and State Pack */}
              <div className="nt-overview-main-row">
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
              </div>

              {/* Second Row: Executive Summary */}
              {data?.marketState.executive_summary ? (
                <article className="nt-panel nt-card nt-executive-summary">
                  <span className="eyebrow">Strategic Executive Summary</span>
                  <div className="nt-copy">
                    <p className="lead-copy">{data.marketState.executive_summary.replace(/\*\*/g, "")}</p>
                  </div>
                </article>
              ) : null}

              {/* Third Row: Strategic Playbook */}
              {data?.marketState.playbook ? (
                <article className="nt-panel nt-card nt-playbook">
                  <span className="eyebrow">Strategic Playbook: {data.marketState.playbook.title}</span>
                  <div className="nt-playbook-content">
                    <div className="nt-playbook-header">
                      <div className="nt-posture">
                        <span>Tactical Posture</span>
                        <strong>{data.marketState.playbook.posture}</strong>
                      </div>
                    </div>
                    <div className="nt-playbook-grid">
                      <div className="nt-playbook-actions">
                        <h4>Priority Actions</h4>
                        <ul className="plain-list">
                          {data.marketState.playbook.actions.map((action, i) => (
                            <li key={i}>{action}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="nt-playbook-allocation">
                        <h4>Model Allocation</h4>
                        <div className="nt-stack">
                          {data.marketState.playbook.asset_allocation.map((alloc, i) => (
                            <div className="nt-list-item" key={i}>
                              <strong>{alloc.asset}</strong>
                              <span>{alloc.weight} • {alloc.target}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="nt-playbook-footer">
                      <p className="nt-watch-point">
                        <strong>Tactical Watch:</strong> {data.marketState.playbook.tactical_watch}
                      </p>
                    </div>
                  </div>
                </article>
              ) : null}

              <div className="nt-grid-row">
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
                  <span className="eyebrow">What Matters Now</span>
                  {bootstrapping ? (
                    <SkeletonList rows={3} />
                  ) : (
                    <div className="nt-stack">
                      {((overviewIntelUnlocked
                        ? data?.marketState.what_matters_now
                        : firstItems(data?.marketState.what_matters_now, 1)
                      )?.length
                        ? (overviewIntelUnlocked
                            ? data?.marketState.what_matters_now
                            : firstItems(data?.marketState.what_matters_now, 1))
                        : [data?.marketState.summary || guide.meaning]
                      ).map((item, index) => (
                        <div className="nt-list-item" key={`matters-${item}-${index}`}>
                          <p>{item}</p>
                        </div>
                      ))}
                    </div>
                  )}
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
              </div>

              {overviewIntelUnlocked ? (
                <>
                  <div className="nt-grid-row">
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
                  </div>

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

                  <div className="nt-grid-row">
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
                          <button className="button button-primary" onClick={() => navigateToView("signals")} type="button">
                            Open Watchlist Context
                          </button>
                          <button className="button" onClick={() => navigateToView(hasTierAccess(currentTier, "pro") ? "world" : "system")} type="button">
                            {hasTierAccess(currentTier, "pro") ? "Open World Affairs" : "Unlock Deeper Intel"}
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
                  </div>

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

                  <div className="nt-grid-row">
                    <article className="nt-panel nt-card">
                      <span className="eyebrow">Alerts</span>
                      <div className="nt-stack">
                        {firstItems(data?.alerts, 4).map((alert) => (
                          <button
                            className={`nt-alert ${alert.severity} ${selectedAlertKey === `${alert.title}::${alert.message}` ? "is-active" : ""}`}
                            key={`${alert.title}-${alert.message}`}
                            onClick={() => setSelectedAlertKey(`${alert.title}::${alert.message}`)}
                            type="button"
                          >
                            <strong>{alert.title}</strong>
                            <p>{alert.message}</p>
                          </button>
                        ))}
                        {monitorHydrating && !data?.alerts.length ? <SkeletonList rows={3} /> : null}
                      </div>
                    </article>

                    <article className="nt-panel nt-card">
                      <span className="eyebrow">AI Alert Drilldown</span>
                      <div className="nt-actions">
                        <button
                          className="button button-small"
                          disabled={aiLoading.alert || !data?.alerts?.length}
                          onClick={() => void handleGenerateAlertAI()}
                          type="button"
                        >
                          {aiLoading.alert ? "Generating..." : "Generate AI Drilldown"}
                        </button>
                      </div>
                      {monitorHydrating ? (
                        <SkeletonList rows={3} />
                      ) : aiAlertDrilldown?.content ? (
                        <div className="nt-stack">
                          <div className="nt-list-item">
                            <strong>Trigger Drivers</strong>
                            <ul className="plain-list">
                              {alertDrivers.length ? alertDrivers.map((item, index) => <li key={`alert-driver-${index}`}>{item}</li>) : <li>--</li>}
                            </ul>
                          </div>
                          <div className="nt-list-item">
                            <strong>Support / Conflict</strong>
                            <ul className="plain-list">
                              {alertConflicts.length ? alertConflicts.map((item, index) => <li key={`alert-conflict-${index}`}>{item}</li>) : <li>--</li>}
                            </ul>
                          </div>
                          <div className="nt-list-item">
                            <strong>Invalidation</strong>
                            <ul className="plain-list">
                              {alertInvalidation.length ? alertInvalidation.map((item, index) => <li key={`alert-invalidation-${index}`}>{item}</li>) : <li>--</li>}
                            </ul>
                          </div>
                        </div>
                      ) : (
                            <p className="muted-copy">No AI drilldown available for current alerts.</p>
                          )}
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
                  </div>
                </>
              ) : (
                <article className="nt-panel nt-card">
                  <span className="eyebrow">Unlock Deeper Overview</span>
                  <div className="nt-stack">
                    <p className="muted-copy">
                      Free shows the top-line market read. Upgrade to unlock deeper regime interpretation, signal conflict, sector breadth, alert context, and transition history.
                    </p>
                    <ul className="plain-list">
                      <li>What changed since the prior session</li>
                      <li>Supporting and conflicting signals</li>
                      <li>Bull vs bear framing and next-step guidance</li>
                      <li>Sector breadth, leaders, laggards, and alert context</li>
                    </ul>
                    <div className="nt-actions">
                      <button className="button button-primary" onClick={() => navigateToView("system")} type="button">
                        Review Plans
                      </button>
                    </div>
                  </div>
                </article>
              )}
            </section>
          ) : null}

          {activeView === "briefing" ? (
            <section className="nt-view nt-briefing">
              <article className="nt-panel nt-hero">
                <span className="eyebrow">AI Analyst Brief</span>
                <div className="nt-actions">
                  <button
                    className="button button-small"
                    disabled={aiLoading.briefing || briefingHydrating}
                    onClick={() => void handleGenerateBriefingAI()}
                    type="button"
                  >
                    {aiLoading.briefing ? "Generating..." : "Generate AI Brief"}
                  </button>
                </div>
                <div className="nt-briefing-copy">
                  {briefingHydrating ? (
                    <>
                      <SkeletonBlock width="58%" height="20px" />
                      <SkeletonBlock width="92%" height="12px" />
                      <SkeletonBlock width="76%" height="12px" />
                    </>
                  ) : (
                    <>
                      <h3>{aiBriefing?.content ? "Session Summary" : data?.briefing.headline || "--"}</h3>
                      <p>{parsedAIBriefing?.headline || briefingOverview || ""}</p>
                      {!aiBriefing?.content && aiBriefingError ? (
                        <p className="muted-copy">AI brief unavailable. Showing baseline briefing.</p>
                      ) : null}
                    </>
                  )}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Checklist</span>
                <ul className="plain-list">
                  {briefingChecklist.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {briefingHydrating && !briefingChecklist.length ? <SkeletonList rows={4} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Focus Items</span>
                <ul className="plain-list">
                  {briefingFocusItems.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {briefingHydrating && !briefingFocusItems.length ? <SkeletonList rows={3} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Risks</span>
                <ul className="plain-list">
                  {briefingRisksFiltered.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {briefingHydrating && !briefingRisksFiltered.length ? <SkeletonList rows={3} /> : null}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Session Catalysts</span>
                <ul className="plain-list">
                  {briefingNextActionsFiltered.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
                {briefingHydrating && !briefingNextActionsFiltered.length ? <SkeletonList rows={3} /> : null}
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
                <span className="eyebrow">AI Theme Summary</span>
                <div className="nt-actions">
                  <button
                    className="button button-small"
                    disabled={aiLoading.world || worldHydrating}
                    onClick={() => void handleGenerateWorldAI()}
                    type="button"
                  >
                    {aiLoading.world ? "Generating..." : "Generate AI Summary"}
                  </button>
                </div>
                {worldHydrating ? (
                  <SkeletonList rows={3} />
                ) : aiWorldAnalysis?.content ? (
                  <div className="nt-stack">
                    <div className="nt-list-item">
                      <strong>Why It Matters</strong>
                      <ul className="plain-list">
                        {worldWhatMatters.length ? worldWhatMatters.map((item, index) => <li key={`world-why-${index}`}>{item}</li>) : <li>--</li>}
                      </ul>
                    </div>
                    <div className="nt-list-item">
                      <strong>First-Order Effects</strong>
                      <ul className="plain-list">
                        {worldFirstOrder.length ? worldFirstOrder.map((item, index) => <li key={`world-first-${index}`}>{item}</li>) : <li>--</li>}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <p className="muted-copy">AI theme summary unavailable.</p>
                )}
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
                <span className="eyebrow">Interactive Stress Testing</span>
                <div className="nt-stack">
                  <div className="nt-row nt-between">
                    <div className="nt-actions" style={{ flexWrap: "wrap" }}>
                      {["Energy Shock", "Geopolitical Conflict", "Monetary Policy", "China Growth", "Trade War"].map((theme) => (
                        <button
                          key={theme}
                          className={`button button-small ${stressTestTheme === theme ? 'button-primary' : ''}`}
                          onClick={() => handleGenerateStressTest(theme)}
                          disabled={stressTestLoading}
                        >
                          {stressTestLoading && stressTestTheme === theme ? "Simulating..." : `Simulate ${theme}`}
                        </button>
                      ))}
                    </div>
                  </div>
                  {stressTestResult ? (
                    <div className="nt-stack" style={{ marginTop: 12 }}>
                      <p className="lead-copy" style={{ color: "var(--cyan)", borderLeft: "3px solid var(--cyan)", paddingLeft: 12 }}>
                        {stressTestResult.scenario_description}
                      </p>
                      <div className="nt-split">
                        {stressTestResult.affected_assets.map((asset) => (
                          <div className="nt-list-item" key={asset.symbol}>
                            <strong>{asset.symbol} • {asset.magnitude} Exposure</strong>
                            <div className="nt-impact-row nt-mini">
                              <span className={`nt-sentiment ${asset.impact_direction.toLowerCase()}`}>{asset.impact_direction}</span>
                            </div>
                            <p>{asset.rationale}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="muted-copy">Select a macro shock scenario to see the projected impact on your watchlist.</p>
                  )}
                </div>
              </article>

              <article className="nt-panel nt-card nt-world-heatmap-card nt-settings-wide">
                <div className="nt-world-map-header">
                  <span className="eyebrow">Geopolitical Heatmap</span>
                  <div className="nt-world-map-meta">
                    <span className="nt-world-map-live">
                      {worldSocketConnected ? "Live WebSocket" : "Live Polling"}{" "}
                      {worldLastUpdatedAt ? `• Updated ${formatDateTime(worldLastUpdatedAt, currentTimezone)}` : ""}
                    </span>
                    <div className="nt-world-map-controls">
                      <button className="button button-small" type="button" onClick={() => applyZoom(1.2)}>+</button>
                      <button className="button button-small" type="button" onClick={() => applyZoom(0.84)}>-</button>
                      <button className="button button-small" type="button" onClick={resetMapViewport}>Reset</button>
                    </div>
                  </div>
                </div>
                <div className="nt-world-map-wrap">
                  <svg
                    className={`nt-world-map ${mapViewport.scale > 1 ? "is-zoomed" : ""} ${mapDragging ? "is-dragging" : ""}`.trim()}
                    viewBox="0 0 520 280"
                    preserveAspectRatio="xMidYMid meet"
                    role="img"
                    aria-label="Global event intensity heatmap"
                    onWheel={(event) => {
                      event.preventDefault();
                      applyZoom(event.deltaY < 0 ? 1.1 : 0.9);
                    }}
                    onMouseDown={(event) => {
                      if (mapViewport.scale <= 1) {
                        return;
                      }
                      setMapDragging(true);
                      mapDragRef.current = { x: event.clientX, y: event.clientY };
                    }}
                    onMouseMove={(event) => {
                      if (!mapDragging || !mapDragRef.current) {
                        return;
                      }
                      const rect = event.currentTarget.getBoundingClientRect();
                      const deltaX = ((event.clientX - mapDragRef.current.x) / Math.max(rect.width, 1)) * 520;
                      const deltaY = ((event.clientY - mapDragRef.current.y) / Math.max(rect.height, 1)) * 280;
                      mapDragRef.current = { x: event.clientX, y: event.clientY };
                      setMapViewport((current) => clampMapViewport({ ...current, tx: current.tx + deltaX, ty: current.ty + deltaY }));
                    }}
                    onMouseUp={() => {
                      setMapDragging(false);
                      mapDragRef.current = null;
                    }}
                    onMouseLeave={() => {
                      setMapDragging(false);
                      mapDragRef.current = null;
                    }}
                  >
                    <rect x="1" y="1" width="518" height="278" className="nt-world-map-frame" />
                    <g transform={`translate(${260 + mapViewport.tx} ${140 + mapViewport.ty}) scale(${mapViewport.scale}) translate(-260 -140)`}>
                      <path d={WORLD_MAP.graticulePath} className="nt-world-map-grid" />
                      {WORLD_MAP.countryPaths.map((country) => {
                        const countryPoint = countryHeatById.get(country.id);
                        return (
                          <path
                            key={`geo-country-${country.id}`}
                            d={country.path}
                            fill={countryPoint?.fill || "rgba(87, 212, 255, 0.16)"}
                            className="nt-world-map-region"
                            onMouseEnter={(event) => {
                              if (!countryPoint) {
                                return;
                              }
                              setHoveredCountry({
                                screenX: event.clientX,
                                screenY: event.clientY,
                                name: countryPoint.name,
                                region: GEO_REGIONS.find((item) => item.key === countryPoint.region)?.label || countryPoint.region,
                                intensity: countryPoint.intensity,
                                drivers: countryPoint.drivers,
                              });
                            }}
                            onMouseMove={(event) => {
                              setHoveredCountry((current) =>
                                current
                                  ? {
                                      ...current,
                                      screenX: event.clientX,
                                      screenY: event.clientY,
                                    }
                                  : current,
                              );
                            }}
                            onMouseLeave={() => setHoveredCountry(null)}
                          />
                        );
                      })}
                      {topGeoHotspots.map((item, index) => {
                        const radius = 8 + item.intensity * 11;
                        return (
                          <g key={`geo-hotspot-ring-${item.key}`}>
                            <circle
                              cx={item.center[0]}
                              cy={item.center[1]}
                              r={radius}
                              className="nt-world-map-hotspot-ring"
                              style={{ animationDelay: `${index * 220}ms` }}
                            />
                            <circle
                              cx={item.center[0]}
                              cy={item.center[1]}
                              r="2"
                              className="nt-world-map-hotspot-core"
                            />
                          </g>
                        );
                      })}
                      {geoHeatmap.map((region) => (
                        <g key={region.key}>
                          <text x={region.center[0]} y={region.center[1]} className="nt-world-map-label">
                            {region.label}
                          </text>
                        </g>
                      ))}
                    </g>
                  </svg>
                  {hoveredCountry ? (
                    <div
                      className="nt-world-map-tooltip"
                      style={{
                        left: `${
                          typeof window === "undefined"
                            ? hoveredCountry.screenX + 14
                            : Math.min(window.innerWidth - 280, hoveredCountry.screenX + 14)
                        }px`,
                        top: `${
                          typeof window === "undefined"
                            ? hoveredCountry.screenY + 14
                            : Math.min(window.innerHeight - 120, hoveredCountry.screenY + 14)
                        }px`,
                      }}
                    >
                      <strong>{hoveredCountry.name}</strong>
                      <span>{hoveredCountry.region}</span>
                      <span>Intensity {(hoveredCountry.intensity * 100).toFixed(0)}%</span>
                      <span>{hoveredCountry.drivers[0] || "No dominant event driver"}</span>
                    </div>
                  ) : null}
                </div>
                <ul className="plain-list">
                  {(topGeoHotspots.length ? topGeoHotspots : geoHeatmap.slice(0, 3)).map((item) => (
                    <li key={`geo-hotspot-${item.key}`}>
                      {item.label}: intensity {(item.intensity * 100).toFixed(0)}%
                    </li>
                  ))}
                </ul>
                <div className="nt-world-map-legend">
                  <span>Low</span>
                  <div className="nt-world-map-gradient" />
                  <span>High</span>
                </div>
              </article>

              <article className="nt-panel nt-card nt-settings-wide">
                <span className="eyebrow">Narrative Timeline</span>
                <div className="nt-timeline-container">
                  {(data?.worldTimeline || []).map((item) => (
                    <div className="nt-timeline-item" key={`${item.title}-${item.published_at}`}>
                      <span className="nt-timeline-date">{formatDateTime(item.published_at, currentTimezone)}</span>
                      <div className="nt-timeline-content">
                        <strong>{item.title}</strong>
                        <span>{item.theme} • {item.region}</span>
                        <p>{item.event_summary}</p>
                        <div className="nt-timeline-grid">
                          <div>
                            <span>Market Reaction</span>
                            {item.market_reaction}
                          </div>
                          <div>
                            <span>Follow-Through</span>
                            {item.follow_through}
                          </div>
                          <div style={{ gridColumn: "span 2" }}>
                            <span>Implication</span>
                            {item.current_implication}
                          </div>
                        </div>
                      </div>
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
                      <span>{event.source} • {formatDateTime(event.published_at, currentTimezone)} • {event.urgency} / {event.severity}</span>
                      <div className="nt-impact-row">
                        <span className={`nt-sentiment ${event.sentiment.toLowerCase()}`}>{event.sentiment} Sentiment</span>
                        <span className="nt-bias">{event.directional_bias}</span>
                      </div>
                      <p>{event.summary || event.why_it_matters}</p>
                    </a>                    <div className="nt-copy">
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
                <span className="eyebrow">AI Watchlist Context</span>
                <div className="nt-actions">
                  <button
                    className="button button-small"
                    disabled={aiLoading.signals || signalsHydrating}
                    onClick={() => void handleGenerateSignalsAI()}
                    type="button"
                  >
                    {aiLoading.signals ? "Generating..." : "Generate AI Context"}
                  </button>
                </div>
                {signalsHydrating ? (
                  <SkeletonList rows={3} />
                ) : aiSignalsContext?.content ? (
                  <div className="nt-stack">
                    <div className="nt-list-item">
                      <strong>Key Drivers</strong>
                      <ul className="plain-list">
                        {signalsDrivers.length ? signalsDrivers.map((item, index) => <li key={`signals-driver-${index}`}>{item}</li>) : <li>--</li>}
                      </ul>
                    </div>
                    <div className="nt-list-item">
                      <strong>Monitoring Checklist</strong>
                      <ul className="plain-list">
                        {signalsChecklist.length ? signalsChecklist.map((item, index) => <li key={`signals-check-${index}`}>{item}</li>) : <li>--</li>}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <p className="muted-copy">AI watchlist context unavailable.</p>
                )}
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">Exposure Mapping</span>
                <div className="nt-stack">
                  {firstItems(data?.watchlistExposures, 6).map((item) => (
                    <div className="nt-list-item" key={`${item.symbol}-${item.sensitivity}`}>
                      <strong>{item.symbol} • {item.sensitivity} sensitivity</strong>
                      <span>{item.label}</span>
                      {item.sentiment && (
                        <div className="nt-impact-row nt-mini">
                          <span className={`nt-sentiment ${item.sentiment.toLowerCase()}`}>{item.sentiment}</span>
                          <span className="nt-bias">{item.directional_bias}</span>
                        </div>
                      )}
                      <p>Themes: {item.themes.join(", ")}</p>
                      <p>Links: {item.market_links.join(", ")}</p>
                    </div>
                  ))}                  {signalsHydrating && !data?.watchlistExposures.length ? <SkeletonList rows={4} /> : null}
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
                      <span>{formatDateTime(note.created_at, currentTimezone)}</span>
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
                      <span>{item.author_name} • {formatDateTime(item.created_at, currentTimezone)}</span>
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
                <span className="eyebrow">Watchlist + Market News</span>
                <div className="nt-stack">
                  {firstItems(prioritizedNews, 8).map(({ item, matchedSymbols }) => (
                    <a className="nt-news-item" href={item.url} key={`${item.title}-${item.url}`} rel="noreferrer" target="_blank">
                      <strong>{item.title}</strong>
                      <span>
                        {item.source} • {formatDateTime(item.published_at, currentTimezone)}
                        {matchedSymbols.length ? ` • Matched: ${matchedSymbols.join(", ")}` : ""}
                      </span>
                      <p>{item.summary || item.tags.join(" • ")}</p>
                    </a>
                  ))}
                </div>
              </article>

              <article className="nt-panel nt-card">
                <span className="eyebrow">All Market News</span>
                <div className="nt-stack">
                  {firstItems(data?.news, 8).map((item) => (
                    <a className="nt-news-item" href={item.url} key={`${item.title}-${item.url}-all`} rel="noreferrer" target="_blank">
                      <strong>{item.title}</strong>
                      <span>{item.source} • {formatDateTime(item.published_at, currentTimezone)}</span>
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
                  <div>
                    <span>Timezone</span>
                    <strong>{deliveryForm.timezone === "local" ? "Local (Browser)" : deliveryForm.timezone}</strong>
                  </div>
                </div>
                <div className="nt-plan-current">
                  <span className="eyebrow">Current Plan</span>
                  <strong>{data?.me?.tier?.toUpperCase() || "--"}</strong>
                  <div className="nt-chip-row">
                    {currentTierHighlights.map((item) => (
                      <span className="nt-chip" key={item}>{item}</span>
                    ))}
                  </div>
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
                          disabled={!emailUnlocked}
                          checked={deliveryForm.email_enabled}
                          onChange={(event) => setDeliveryForm((current) => ({ ...current, email_enabled: event.target.checked }))}
                          type="checkbox"
                        />
                        <div>
                          <strong>Email Briefing</strong>
                          <span>{emailUnlocked ? "Send the macro briefing to your account email." : "Available on Pro and Desk plans."}</span>
                        </div>
                      </label>
                      <label className="nt-simple-toggle">
                        <input
                          disabled={!webhookUnlocked}
                          checked={deliveryForm.webhook_enabled}
                          onChange={(event) => setDeliveryForm((current) => ({ ...current, webhook_enabled: event.target.checked }))}
                          type="checkbox"
                        />
                        <div>
                          <strong>Webhook Delivery</strong>
                          <span>{webhookUnlocked ? "Forward updates into an external workflow." : "Available on Pro and Desk plans."}</span>
                        </div>
                      </label>
                      <label className="nt-simple-toggle">
                        <input
                          disabled={!webhookUnlocked}
                          checked={deliveryForm.slack_enabled}
                          onChange={(event) => setDeliveryForm((current) => ({ ...current, slack_enabled: event.target.checked }))}
                          type="checkbox"
                        />
                        <div>
                          <strong>Slack Delivery</strong>
                          <span>{webhookUnlocked ? "Post the global macro brief into a Slack channel." : "Available on Pro and Desk plans."}</span>
                        </div>
                      </label>
                      <label className="nt-simple-toggle">
                        <input
                          disabled={!webhookUnlocked}
                          checked={deliveryForm.discord_enabled}
                          onChange={(event) => setDeliveryForm((current) => ({ ...current, discord_enabled: event.target.checked }))}
                          type="checkbox"
                        />
                        <div>
                          <strong>Discord Delivery</strong>
                          <span>{webhookUnlocked ? "Post the global macro brief into a Discord channel." : "Available on Pro and Desk plans."}</span>
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
                      <label className="nt-settings-inline-field">
                        <span className="eyebrow">Timezone</span>
                        <select
                          className="nt-input nt-settings-select"
                          onChange={(event) => setDeliveryForm((current) => ({ ...current, timezone: event.target.value }))}
                          value={deliveryForm.timezone}
                        >
                          {timezoneOptions.map((option) => (
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
                      {deliveryForm.slack_enabled ? (
                        <label className="nt-settings-inline-field">
                          <span className="eyebrow">Slack Webhook URL</span>
                          <input
                            className="nt-input"
                            onChange={(event) => setDeliveryForm((current) => ({ ...current, slack_webhook_url: event.target.value }))}
                            placeholder="https://hooks.slack.com/services/..."
                            value={deliveryForm.slack_webhook_url}
                          />
                        </label>
                      ) : null}
                      {deliveryForm.discord_enabled ? (
                        <label className="nt-settings-inline-field">
                          <span className="eyebrow">Discord Webhook URL</span>
                          <input
                            className="nt-input"
                            onChange={(event) => setDeliveryForm((current) => ({ ...current, discord_webhook_url: event.target.value }))}
                            placeholder="https://discord.com/api/webhooks/..."
                            value={deliveryForm.discord_webhook_url}
                          />
                        </label>
                      ) : null}
                      {deliveryResult ? (
                        <div className="nt-settings-result">
                          <strong>{deliveryResult.headline}</strong>
                          <span>{labelizeKey(deliveryResult.cadence)}</span>
                          <p>
                            Email: {deliveryResult.email_status}
                            {" | "}Webhook: {deliveryResult.webhook_status}
                            {" | "}Slack: {deliveryResult.slack_status || "disabled"}
                            {" | "}Discord: {deliveryResult.discord_status || "disabled"}
                          </p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                  <div className="nt-settings-action-row">
                    <button className="button button-primary nt-settings-button" disabled={saving === "delivery"} type="submit">
                      {saving === "delivery" ? "Saving..." : "Save Preferences"}
                    </button>
                    <button className="button nt-settings-button" disabled={saving === "macro-delivery" || !emailUnlocked} onClick={() => void handleMacroDeliverySend()} type="button">
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
