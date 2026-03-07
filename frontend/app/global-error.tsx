"use client";

type GlobalErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "IBM Plex Mono, monospace", margin: 0, background: "#05080d", color: "#dce4ed" }}>
        <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "24px" }}>
          <section
            style={{
              width: "min(720px, 100%)",
              border: "1px solid rgba(119, 203, 236, 0.28)",
              background: "rgba(13, 20, 29, 0.96)",
              padding: "20px",
            }}
          >
            <h1 style={{ marginTop: 0 }}>Application Error</h1>
            <p style={{ color: "#8796a7" }}>
              Something went wrong while rendering this page.
            </p>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                overflowWrap: "anywhere",
                background: "rgba(0, 0, 0, 0.35)",
                border: "1px solid rgba(120, 138, 158, 0.25)",
                padding: "12px",
              }}
            >
              {error.message}
            </pre>
            <button
              type="button"
              onClick={reset}
              style={{
                marginTop: "12px",
                padding: "10px 14px",
                border: "1px solid rgba(119, 203, 236, 0.28)",
                background: "rgba(87, 212, 255, 0.08)",
                color: "#dce4ed",
                cursor: "pointer",
              }}
            >
              Try again
            </button>
          </section>
        </main>
      </body>
    </html>
  );
}
