import React from 'react';

export default function DocsPage() {
  return (
    <div className="nt-shell">
      <main className="nt-main">
        <header className="nt-header">
          <div>
            <h1 className="nt-regime" style={{ fontSize: '2.5rem' }}>User Guide & Documentation</h1>
            <p className="muted-copy">A comprehensive framework for institutional-grade market intelligence</p>
          </div>
          <div className="nt-actions">
            <a href="/" className="button">Home</a>
            <a href="/terminal" className="button button-primary">Enter Terminal</a>
          </div>
        </header>

        <section className="nt-view" style={{ gridTemplateColumns: '1fr', maxWidth: '1000px', margin: '0 auto', gap: '32px' }}>
          
          <article className="nt-panel">
            <span className="eyebrow">Core Framework</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>1. Machine Learning Regime Detection</h2>
            <div className="nt-copy" style={{ gap: '20px' }}>
              <p>Regime uses a specialized <strong>XGBoost Gradient Boosting</strong> model trained on decades of cross-asset price action, volatility metrics, and liquidity flows. The model classifies the market every 10 minutes into one of three primary regimes:</p>
              
              <div className="nt-grid-row" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                <div className="nt-list-item">
                  <strong style={{ color: 'var(--green)' }}>Risk-On</strong>
                  <p>Constructive tape characterized by broad sector participation, positive momentum, and stable volatility.</p>
                </div>
                <div className="nt-list-item">
                  <strong style={{ color: 'var(--amber)' }}>Risk-Off</strong>
                  <p>Defensive posture where capital flows toward safe-havens (Gold, Treasuries) and cyclical assets underperform.</p>
                </div>
                <div className="nt-list-item">
                  <strong style={{ color: 'var(--red)' }}>High-Vol</strong>
                  <p>Crisis or transition state. High intraday ranges and erratic correlations. Liquidity preservation is priority.</p>
                </div>
              </div>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Intelligence Layer</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>2. AI-Driven Strategic Insights</h2>
            <div className="nt-copy">
              <p>Beyond raw data, Regime provides an interpretation layer powered by Large Language Models (LLMs) and deterministic financial logic:</p>
              <ul>
                <li><strong>Executive Summary:</strong> A high-level distillation of live news flow (Reuters/CNBC) cross-referenced against the current ML regime.</li>
                <li><strong>Strategic Playbook:</strong> Dynamically generated tactical advice, including specific asset allocation tilts (Overweight/Underweight) and "Tactical Watches" for the current session.</li>
                <li><strong>Watchlist Exposure:</strong> Automated mapping of your symbols to global macro themes. See exactly how a Fed pivot or an Energy Shock creates a "Ripple Effect" through your specific portfolio.</li>
              </ul>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Risk Management</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>3. Interactive Stress Testing</h2>
            <div className="nt-copy">
              <p>The <strong>Stress Test Engine</strong> (located in World Affairs) allows you to simulate hypothetical macro shocks before they happen. By selecting a scenario like "Trade War" or "Monetary Tightening," the system calculates the projected impact on your watchlist names based on their historical sensitivity and sector links.</p>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Workflow & Collaboration</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>4. Desk Workspaces</h2>
            <div className="nt-copy">
              <p>Designed for professional teams, the <strong>Desk</strong> workspace allows users to create shared environments. Teams can coordinate around a single source of truth, share watchlist intelligence, and capture "Briefing Snapshots" to document the market view at specific points in time.</p>
            </div>
          </article>

          <article className="nt-panel">
            <span className="eyebrow">Outbound Intelligence</span>
            <h2 style={{ color: 'var(--cyan)', margin: '12px 0' }}>5. Real-Time Delivery</h2>
            <div className="nt-copy">
              <p>Regime is an active monitoring agent. In your <strong>Settings</strong>, you can configure outbound delivery channels:</p>
              <ul>
                <li><strong>Discord & Slack:</strong> Receive automated alerts for regime shifts and critical headlines directly in your team channels via webhooks.</li>
                <li><strong>Email Briefings:</strong> Get the Strategic Executive Summary and Morning Playbook delivered to your inbox before the market open.</li>
              </ul>
            </div>
          </article>

          <article className="nt-panel" style={{ borderStyle: 'dashed', borderColor: 'var(--line-bright)' }}>
            <span className="eyebrow">Compliance Disclaimer</span>
            <div className="nt-copy" style={{ fontSize: '0.85rem' }}>
              <p>Regime is a research and analysis tool. All signals, predictions, and AI-generated summaries are for informational purposes only and do not constitute financial, investment, or legal advice. Historical performance is not indicative of future results.</p>
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
