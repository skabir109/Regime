export default function TermsPage() {
  return (
    <main className="legal-shell">
      <section className="panel legal-card">
        <span className="eyebrow">Legal</span>
        <h1>Terms and Conditions</h1>
        <p>Effective date: March 5, 2026. By accessing or using Regime, you agree to these terms.</p>
        <section className="legal-section">
          <h2>Eligibility and Accounts</h2>
          <ul>
            <li>You must provide accurate registration information and keep credentials secure.</li>
            <li>You are responsible for activity under your account and for safeguarding access tokens.</li>
            <li>We may suspend access when account activity appears unauthorized or abusive.</li>
          </ul>
        </section>
        <section className="legal-section">
          <h2>Permitted Use</h2>
          <ul>
            <li>Use the product only for lawful purposes and in compliance with applicable regulations.</li>
            <li>Do not attempt to reverse engineer, disrupt, scrape, or overload service infrastructure.</li>
            <li>Do not use the service to transmit malicious code, spam, or misleading market manipulation content.</li>
          </ul>
        </section>
        <section className="legal-section">
          <h2>Product Scope and No Advice</h2>
          <p>
            Regime provides analytics, monitoring, and workflow tools. Content is informational only and does not
            constitute investment, legal, tax, or fiduciary advice. You remain solely responsible for trading,
            allocation, and risk decisions.
          </p>
        </section>
        <section className="legal-section">
          <h2>Plans, Billing, and Changes</h2>
          <p>
            Features, limits, and pricing may change over time. Paid access depends on active plan status. Unless
            required by law, fees are non-refundable for partial periods.
          </p>
        </section>
        <section className="legal-section">
          <h2>Intellectual Property</h2>
          <p>
            The service, interface, branding, and product logic are owned by Regime and licensors. These terms grant a
            limited, non-exclusive, non-transferable right to use the service while your account is in good standing.
          </p>
        </section>
        <section className="legal-section">
          <h2>Disclaimers and Liability Limits</h2>
          <p>
            Service availability and data continuity are provided on an &quot;as is&quot; and &quot;as available&quot; basis. To the
            maximum extent permitted by law, Regime is not liable for indirect, incidental, special, consequential, or
            punitive damages arising from service use or inability to use the service.
          </p>
        </section>
        <section className="legal-section">
          <h2>Termination</h2>
          <p>
            You may stop using the service at any time. We may suspend or terminate access for terms violations,
            security risks, non-payment, or legal compliance requirements.
          </p>
        </section>
        <section className="legal-section">
          <h2>Updates to Terms</h2>
          <p>
            We may revise these terms as the product evolves. Continued use after updates indicates acceptance of the
            revised terms.
          </p>
        </section>
        <section className="legal-section">
          <h2>Contact</h2>
          <p>For legal inquiries, contact: legal@regime.local</p>
        </section>
        <div className="legal-links">
          <a href="/about">About</a>
          <a href="/pricing">Pricing</a>
          <a href="/privacy">Privacy</a>
          <a href="/">Home</a>
        </div>
      </section>
    </main>
  );
}
