import React from 'react';

export default function DocsPage() {
  return (
    <div className="nt-shell">
      <main className="nt-main">
        <header className="nt-header">
          <div>
            <h1 className="nt-regime" style={{ fontSize: '2.5rem' }}>Documentation</h1>
            <p className="muted-copy">Product capabilities, workflows, controls, and API reference for Regime.</p>
          </div>
          <div className="nt-actions">
            <a href="/" className="button">Home</a>
            <a href="/terminal" className="button button-primary">Enter Terminal</a>
          </div>
        </header>

        <section className="nt-view" style={{ gridTemplateColumns: '1fr', maxWidth: '1000px', margin: '0 auto', gap: '32px' }}>
          <article className="nt-panel">
            <span className="eyebrow">Quick Start</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>1. Getting Started</h2>
            <div className="nt-copy">
              <ul>
                <li><strong>Sign in:</strong> Authenticate and choose a plan.</li>
                <li><strong>Open Terminal:</strong> Review regime, transitions, and cross-asset state.</li>
                <li><strong>Build watchlist:</strong> Add symbols to personalize signals and event monitoring.</li>
                <li><strong>Configure delivery:</strong> Enable cadence/webhooks for team routing.</li>
              </ul>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Architecture</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>2. How Regime Works End-to-End</h2>
            <div className="nt-copy">
              <ol>
                <li><strong>Data ingestion:</strong> Market, sector, and headline data is collected and normalized.</li>
                <li><strong>Feature generation:</strong> Regime features are computed across trend, breadth, volatility, and confirmation dimensions.</li>
                <li><strong>Regime inference:</strong> The model scores current state probabilities and classification.</li>
                <li><strong>Context synthesis:</strong> Alerts, briefings, watchlist intelligence, and world-affairs views are generated from state + user context.</li>
                <li><strong>User personalization:</strong> Watchlist, delivery settings, and plan entitlements shape visible outputs.</li>
                <li><strong>Delivery:</strong> Insights are shown in terminal and routed to configured channels (email/webhooks).</li>
              </ol>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">System Model</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>3. Regime Engine</h2>
            <div className="nt-copy" style={{ gap: '20px' }}>
              <p>The platform classifies market state with an XGBoost model using cross-asset and volatility features. States:</p>
              <div className="nt-grid-row" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                <div className="nt-list-item">
                  <strong style={{ color: 'var(--green)' }}>Risk-On</strong>
                  <p>Constructive participation and stable volatility.</p>
                </div>
                <div className="nt-list-item">
                  <strong style={{ color: 'var(--amber)' }}>Risk-Off</strong>
                  <p>Defensive rotation and reduced risk appetite.</p>
                </div>
                <div className="nt-list-item">
                  <strong style={{ color: 'var(--red)' }}>High-Vol</strong>
                  <p>Unstable tape with elevated repricing risk.</p>
                </div>
              </div>
              <p>Use regime output as context, not standalone trade advice.</p>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Feature Map</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>4. What The Application Can Do</h2>
            <div className="nt-copy">
              <ul>
                <li><strong>Monitor:</strong> Market state, transitions, drivers, leaders/laggards, and alerts.</li>
                <li><strong>Briefing:</strong> Premarket plan, checklist, risks, and catalyst timeline.</li>
                <li><strong>World Affairs:</strong> Geopolitical events, regional summaries, narrative timeline, stress tests.</li>
                <li><strong>Markets:</strong> Trend panels and sector breadth for cross-asset confirmation.</li>
                <li><strong>Signals:</strong> Ranked symbols with stance, reasons, and watchlist intelligence.</li>
                <li><strong>Desk:</strong> Shared workspace, notes, shared watchlist, and briefing snapshots.</li>
                <li><strong>System:</strong> Model metadata, training summary, billing tier controls, and delivery settings.</li>
              </ul>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Delivery & Integrations</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>5. Outbound Intelligence</h2>
            <div className="nt-copy">
              <ul>
                <li><strong>Email:</strong> Scheduled briefing delivery by cadence.</li>
                <li><strong>Webhooks:</strong> Generic webhook, Slack webhook, and Discord webhook routing.</li>
                <li><strong>Billing:</strong> Plan-aware capability gating (free/pro/desk).</li>
              </ul>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Operating Workflow</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>6. Daily Usage Playbook</h2>
            <div className="nt-copy">
              <ol>
                <li><strong>Open Monitor:</strong> confirm regime, confidence, and major drivers.</li>
                <li><strong>Review Briefing:</strong> extract checklist, risks, and catalyst timing.</li>
                <li><strong>Scan Markets/Signals:</strong> identify alignment/divergence before position decisions.</li>
                <li><strong>Refine Watchlist:</strong> remove stale names, add active symbols, read related headlines.</li>
                <li><strong>Check World Affairs:</strong> assess second-order macro impacts and stress scenarios.</li>
                <li><strong>Coordinate in Desk:</strong> post notes/snapshots for team alignment.</li>
                <li><strong>Configure Delivery:</strong> ensure alerts/briefings are routed for next session.</li>
              </ol>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Security Controls</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>7. Platform Protections</h2>
            <div className="nt-copy">
              <ul>
                <li>Cookie-based sessions with secure defaults and CSRF enforcement on unsafe authenticated requests.</li>
                <li>Global + route-level rate limiting, with additional per-user endpoint quotas for high-cost operations.</li>
                <li>Input validation/sanitization and ORM-backed SQL access patterns.</li>
                <li>Legacy static dashboard surface removed to reduce XSS risk footprint.</li>
              </ul>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">API Surface</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>8. API Reference</h2>
            <div className="nt-copy">
              <p>Core endpoint groups:</p>
              <ul>
                <li><strong>Auth:</strong> `/auth/*` session, profile, and recovery endpoints.</li>
                <li><strong>Terminal Data:</strong> `/market/*`, `/regime/*`, `/news`, `/signals/*`, `/watchlist/*`, `/world-affairs/*`.</li>
                <li><strong>Workspace:</strong> `/workspace/shared*` for collaboration flows.</li>
                <li><strong>Billing:</strong> `/billing/*` for plans, checkout, and portal sessions.</li>
              </ul>
              <p>Use the in-app API docs endpoint (`/docs` on backend service) for schema-level details.</p>
            </div>
          </article>

          <article className="nt-panel" style={{ borderStyle: 'dashed', borderColor: 'var(--line-bright)' }}>
            <span className="eyebrow">Disclaimer</span>
            <div className="nt-copy" style={{ fontSize: '0.85rem' }}>
              <p>Regime is a research and analysis platform. Outputs are informational and not financial, legal, or investment advice.</p>
            </div>
          </article>
        </section>

        <footer className="nt-footer" style={{ justifyContent: 'center', marginTop: '40px', paddingBottom: '40px' }}>
          <span>&copy; 2026 Regime Terminal Intelligence</span>
        </footer>
      </main>
    </div>
  );
}
