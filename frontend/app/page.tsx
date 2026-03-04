export default function HomePage() {
  return (
    <main className="landing-shell">
      <section className="landing-hero">
        <div className="landing-copy">
          <span className="landing-brand">REGIME</span>
          <h1 className="landing-title">Market context that is fast to read and easy to trust.</h1>
          <p className="landing-body">
            Regime brings market state, catalysts, watchlists, and desk workflow into one terminal.
            The focus is speed, structure, and clear interpretation.
          </p>
          <div className="landing-actions">
            <a className="button button-primary" href="/login">
              Sign In
            </a>
          </div>
        </div>

        <div className="panel landing-preview">
          <div className="landing-preview-head">
            <span className="eyebrow">Snapshot</span>
            <span className="status-chip">Live Workspace</span>
          </div>
          <div className="landing-preview-grid">
            <article>
              <span>State</span>
              <strong>RiskOn</strong>
              <p>Constructive tape with broad participation and steady volatility.</p>
            </article>
            <article>
              <span>Focus</span>
              <strong>Watchlist</strong>
              <p>Prioritized names, matched headlines, and scheduled catalysts.</p>
            </article>
            <article>
              <span>Desk</span>
              <strong>Shared Notes</strong>
              <p>Capture briefing snapshots and coordinate around the same market view.</p>
            </article>
            <article>
              <span>Delivery</span>
              <strong>Briefings</strong>
              <p>Control daily cadence, webhook routing, and history retention.</p>
            </article>
          </div>
        </div>
      </section>

      <section className="landing-strip">
        <article className="landing-feature">
          <span className="eyebrow">Overview</span>
          <p>Read the current market state, the drivers behind it, and what changed since the prior session.</p>
        </article>
        <article className="landing-feature">
          <span className="eyebrow">Signals</span>
          <p>Track trending names, build a watchlist, and review related headlines without leaving the terminal.</p>
        </article>
        <article className="landing-feature">
          <span className="eyebrow">Desk</span>
          <p>Share symbols, notes, alerts, and briefing snapshots across a collaborative workspace.</p>
        </article>
      </section>
    </main>
  );
}
