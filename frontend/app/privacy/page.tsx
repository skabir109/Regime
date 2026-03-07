export default function PrivacyPage() {
  return (
    <main className="legal-shell">
      <section className="panel legal-card">
        <span className="eyebrow">Legal</span>
        <h1>Privacy Policy</h1>
        <p>
          Effective date: March 5, 2026. This policy describes how Regime collects, uses, stores, and safeguards data
          when you use the product.
        </p>
        <section className="legal-section">
          <h2>Data We Collect</h2>
          <ul>
            <li>Account data such as email, display name, authentication records, and session metadata.</li>
            <li>Workspace data including watchlists, notes, preferences, and collaboration activity.</li>
            <li>Delivery configuration such as webhook, Slack, and Discord endpoints you explicitly provide.</li>
            <li>Operational telemetry used for reliability, abuse prevention, and performance monitoring.</li>
          </ul>
        </section>
        <section className="legal-section">
          <h2>How We Use Data</h2>
          <ul>
            <li>Provide core product functionality, state persistence, and user-specific configuration.</li>
            <li>Deliver briefings, alerts, and workflow updates through enabled channels.</li>
            <li>Improve model quality, ranking, and user experience through aggregate usage analysis.</li>
            <li>Maintain security controls, detect abuse, and respond to incidents.</li>
          </ul>
        </section>
        <section className="legal-section">
          <h2>Sharing and Processors</h2>
          <p>
            Regime does not sell personal data. Data may be processed by infrastructure and communication providers
            required to operate the service. These providers process data on our behalf under contractual controls.
          </p>
        </section>
        <section className="legal-section">
          <h2>Retention and Security</h2>
          <p>
            We retain data for as long as needed to provide the service, meet legal requirements, and resolve disputes.
            Security controls include access restrictions, transport encryption, and operational monitoring. No system
            can be guaranteed 100% secure.
          </p>
        </section>
        <section className="legal-section">
          <h2>Your Controls</h2>
          <ul>
            <li>Update or remove delivery endpoints in System settings at any time.</li>
            <li>Request account-level data correction or deletion, subject to legal retention obligations.</li>
            <li>Manage session security by signing out from active devices where available.</li>
          </ul>
        </section>
        <section className="legal-section">
          <h2>Policy Updates</h2>
          <p>
            We may update this policy as product capabilities evolve. Material updates will be reflected by changing the
            effective date and posting the revised policy page.
          </p>
        </section>
        <section className="legal-section">
          <h2>Contact</h2>
          <p>For privacy requests, contact: legal@regime.local</p>
        </section>
        <div className="legal-links">
          <a href="/">Home</a>
          <a href="/about">About</a>
          <a href="/pricing">Pricing</a>
          <a href="/terms">Terms</a>
        </div>
      </section>
    </main>
  );
}
