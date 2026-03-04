"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

type AuthMode = "login" | "register";

export default function LoginPage() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(formData: FormData) {
    setLoading(true);
    setError("");

    const payload =
      mode === "login"
        ? {
            email: String(formData.get("email") || ""),
            password: String(formData.get("password") || ""),
          }
        : {
            name: String(formData.get("name") || ""),
            email: String(formData.get("email") || ""),
            password: String(formData.get("password") || ""),
          };

    const endpoint = mode === "login" ? "/auth/login" : "/auth/register";

    try {
      await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      window.location.href = "/terminal";
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Authentication failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="panel auth-card">
        <div className="auth-copy">
          <span className="auth-brand">REGIME</span>
          <h1 className="auth-title">Terminal access for traders and desks.</h1>
          <p className="auth-body">
            Sign in to open your terminal, watchlists, delivery settings, and shared desk workspace.
          </p>
        </div>
        <div className="auth-form-panel">
          <div className="auth-toggle" role="tablist" aria-label="Authentication mode">
            <button
              className={`auth-toggle-button ${mode === "login" ? "is-active" : ""}`}
              onClick={() => setMode("login")}
              type="button"
            >
              Login
            </button>
            <button
              className={`auth-toggle-button ${mode === "register" ? "is-active" : ""}`}
              onClick={() => setMode("register")}
              type="button"
            >
              Register
            </button>
          </div>
          {error ? (
            <div className="auth-error">{error}</div>
          ) : null}
          <form action={async (formData) => await handleSubmit(formData)} className="auth-form">
            {mode === "register" ? (
              <input className="auth-input" name="name" placeholder="Name" />
            ) : null}
            <input className="auth-input" name="email" placeholder="Email" />
            <input
              className="auth-input"
              name="password"
              placeholder="Password"
              type="password"
            />
            <button className="button button-primary auth-submit" disabled={loading} type="submit">
              {loading ? "Working..." : mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>
          <div className="auth-divider" aria-hidden="true">
            <span>or</span>
          </div>
          <button className="auth-oauth-button" type="button">
            <svg aria-hidden="true" className="auth-oauth-icon" viewBox="0 0 18 18">
              <path
                d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.56 2.68-3.86 2.68-6.62Z"
                fill="#4285F4"
              />
              <path
                d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.81.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.34A9 9 0 0 0 9 18Z"
                fill="#34A853"
              />
              <path
                d="M3.97 10.72A5.41 5.41 0 0 1 3.69 9c0-.6.1-1.18.28-1.72V4.94H.96A9 9 0 0 0 0 9c0 1.45.35 2.82.96 4.06l3.01-2.34Z"
                fill="#FBBC05"
              />
              <path
                d="M9 3.58c1.32 0 2.5.45 3.43 1.33l2.57-2.57C13.46.9 11.42 0 9 0A9 9 0 0 0 .96 4.94l3.01 2.34c.71-2.12 2.69-3.7 5.03-3.7Z"
                fill="#EA4335"
              />
            </svg>
            <span>Continue with Google</span>
          </button>
        </div>
      </section>
    </main>
  );
}
