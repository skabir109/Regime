import React from 'react';

export default function DocsPage() {
  return (
    <div className="nt-shell">
      <main className="nt-main">
        <header className="nt-header">
          <div>
            <h1 className="nt-regime" style={{ fontSize: '2.5rem' }}>Documentation</h1>
            <p className="muted-copy">User guide and technical framework for the Regime Terminal</p>
          </div>
          <a href="/terminal" className="button button-primary">Return to Terminal</a>
        </header>

        <section className="nt-view" style={{ gridTemplateColumns: '1fr', maxWidth: '900px', margin: '0 auto' }}>
          <article className="nt-panel nt-card">
            <span className="eyebrow">1. Understanding Regimes</span>
            <div className="nt-copy" style={{ gap: '20px' }}>
              <p>The core of the application is our ML-driven Regime Detection. We classify the market into three primary states:</p>
              <div className="nt-stack">
                <div className="nt-list-item">
                  <strong>Risk-On (Expansion)</strong>
                  <p>Equities are trending higher with supportive breadth. Tactics: Trend following, overweight growth.</p>
                </div>
                <div className="nt-list-item">
                  <strong>Risk-Off (Defensive)</strong>
                  <p>Defensive assets (Gold, Bonds) are outperforming. Tactics: Capital preservation, overweight staples.</p>
                </div>
                <div className="nt-list-item">
                  <strong>High-Vol (Crisis)</strong>
                  <p>Unstable conditions with wide price swings. Tactics: Liquidity focus, active hedging.</p>
                </div>
              </div>
            </div>
          </article>

          <article className="nt-panel nt-card">
            <span className="eyebrow">2. Strategic Intelligence</span>
            <div className="nt-copy">
              <p><strong>Executive Summary:</strong> An LLM-distilled analysis of live news flow vs the current ML regime.</p>
              <p><strong>Strategic Playbook:</strong> Actionable asset allocation tilts and tactical watches updated in real-time.</p>
              <p><strong>Watchlist Exposure:</strong> Maps how global macro themes (e.g., Fed Policy, Geopolitics) specifically impact the symbols you are tracking.</p>
            </div>
          </article>

          <article className="nt-panel nt-card">
            <span className="eyebrow">3. Interactive Stress Testing</span>
            <div className="nt-copy">
              <p>Located in the <strong>World Affairs</strong> tab, this tool allows you to simulate hypothetical macro shocks (e.g., "Energy Shock") to see a "Ripple Effect" analysis across your specific portfolio names before the event occurs.</p>
            </div>
          </article>

          <article className="nt-panel nt-card">
            <span className="eyebrow">4. Report Exporting</span>
            <div className="nt-copy">
              <p>Professional users can generate institutional-grade PDF reports by clicking the <strong>Export Report</strong> button in the Terminal header. This captures the current regime, playbook, and watchlist intelligence in a format suitable for distribution.</p>
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}
