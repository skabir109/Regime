const PRICING_TIERS = [
  {
    name: "Free",
    tagline: "Start with core market context",
    watchlist: "5 symbols",
    history: "7-day briefing history",
    price: "$0",
    cadence: "Core terminal access",
    cta: "Get Started",
    href: "/login",
    features: [
      "Monitor workspace and core regime context",
      "Signals workspace with basic watchlist coverage",
      "Email preferences and fallback catalyst calendar",
    ],
  },
  {
    name: "Pro",
    tagline: "For active individual traders",
    watchlist: "25 symbols",
    history: "30-day briefing history",
    price: "$29",
    cadence: "per month",
    cta: "Upgrade To Pro",
    href: "/login",
    featured: true,
    features: [
      "World Affairs, Markets, and News workspaces",
      "Webhook, Slack, and Discord delivery channels",
      "Verified calendar access when provider is configured",
    ],
  },
  {
    name: "Desk",
    tagline: "Team workflows and shared context",
    watchlist: "100 symbols",
    history: "90-day briefing history",
    price: "$99",
    cadence: "per month",
    cta: "Upgrade To Desk",
    href: "/login",
    features: [
      "Shared desk workspace with invite codes",
      "Shared watchlist, notes, alerts, and briefing snapshots",
      "Expanded capacity for desk-style collaboration",
    ],
  },
];

export default function PricingPage() {
  return (
    <main className="pricing-shell">
      <section className="pricing-head panel">
        <span className="landing-brand">REGIME</span>
        <h1>Simple plans for traders and desks.</h1>
        <p>Pick a plan based on watchlist size, delivery channels, and collaboration depth. You can switch plans inside System at any time.</p>
        <div className="landing-actions">
          <a className="button" href="/">Back Home</a>
          <a className="button button-primary" href="/login">Open Terminal</a>
        </div>
      </section>

      <section className="pricing-grid">
        {PRICING_TIERS.map((tier) => (
          <article className={`panel pricing-card ${tier.featured ? "is-featured" : ""}`.trim()} key={tier.name}>
            <span className="eyebrow">{tier.name}</span>
            <h2>{tier.price}</h2>
            <p className="pricing-cadence">{tier.cadence}</p>
            <p className="pricing-tagline">{tier.tagline}</p>
            <div className="pricing-meta">
              <span>{tier.watchlist}</span>
              <span>{tier.history}</span>
            </div>
            <ul className="plain-list">
              {tier.features.map((feature) => <li key={feature}>{feature}</li>)}
            </ul>
            <a className={`button ${tier.featured ? "button-primary" : ""}`.trim()} href={tier.href}>
              {tier.cta}
            </a>
          </article>
        ))}
      </section>
      <div className="legal-links">
        <a href="/">Home</a>
        <a href="/about">About</a>
        <a href="/privacy">Privacy</a>
        <a href="/terms">Terms</a>
      </div>
    </main>
  );
}
