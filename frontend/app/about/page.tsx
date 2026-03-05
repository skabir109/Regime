export default function AboutPage() {
  return (
    <main className="legal-shell">
      <section className="panel legal-card">
        <span className="landing-brand">REGIME</span>
        <h1>About Regime</h1>
        <p>Regime is a market intelligence workspace designed to make macro context faster to read, easier to trust, and more actionable for individual traders and team desks.</p>
        <section className="legal-section">
          <h2>What Regime Does</h2>
          <p>Regime combines market state modeling, world-affairs monitoring, watchlist intelligence, and collaborative desk workflow into one interface.</p>
          <ul>
            <li>Tracks regime context, confidence, and cross-asset confirmation.</li>
            <li>Surfaces market-relevant world events with intensity scoring and narrative timeline context.</li>
            <li>Maps event flow into watchlist impact and delivery channels.</li>
            <li>Supports team coordination through shared workspace tools.</li>
          </ul>
        </section>
        <section className="legal-section">
          <h2>Product Principles</h2>
          <ul>
            <li>Clarity over noise: concise, structured outputs.</li>
            <li>Actionability over commentary: what changed, why it matters, what to monitor.</li>
            <li>Workflow-first design: monitor, signals, world, desk, and system in one flow.</li>
            <li>Continuous evolution: features and models are actively improved over time.</li>
          </ul>
        </section>
        <section className="legal-section">
          <h2>Important Disclaimer</h2>
          <p>Regime provides informational and analytical tools only. It does not provide personalized investment, legal, or tax advice. Users remain fully responsible for their own decisions and risk management.</p>
        </section>
        <div className="legal-links">
          <a href="/pricing">Pricing</a>
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/login">Login</a>
        </div>
      </section>
    </main>
  );
}
