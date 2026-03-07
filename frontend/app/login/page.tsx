"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type AuthMode = "login" | "register";

type SupabaseAuthResponse = {
  access_token?: string;
};

type AuthMeResponse = {
  tier_selection_required?: boolean;
};

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

async function supabaseAuthRequest<T>(path: string, payload: Record<string, unknown>) {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error("Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.");
  }

  const response = await fetch(`${SUPABASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: SUPABASE_ANON_KEY,
    },
    body: JSON.stringify(payload),
  });

  const data = (await response.json().catch(() => ({}))) as {
    msg?: string;
    error_description?: string;
  } & T;

  if (!response.ok) {
    throw new Error(data.error_description || data.msg || "Authentication failed.");
  }

  return data;
}

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>("login");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const isLogin = mode === "login";
  const processingLabel = isLogin ? "Signing you in..." : "Creating your account...";

  useEffect(() => {
    router.prefetch("/terminal");
    router.prefetch("/plans");
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) {
      return;
    }

    setLoading(true);
    setError("");
    setNotice("");

    const normalizedEmail = email.trim();
    const normalizedName = name.trim();

    if (!normalizedEmail || !password || (!isLogin && !normalizedName)) {
      setError(isLogin ? "Enter email and password." : "Enter name, email, and password.");
      setLoading(false);
      return;
    }

    let shouldResetLoading = true;

    try {
      const authPayload =
        mode === "login"
          ? await supabaseAuthRequest<SupabaseAuthResponse>("/auth/v1/token?grant_type=password", {
              email: normalizedEmail,
              password,
            })
          : await supabaseAuthRequest<SupabaseAuthResponse>("/auth/v1/signup", {
              email: normalizedEmail,
              password,
              data: { name: normalizedName },
            });

      if (!authPayload.access_token) {
        setNotice("Account created. Check your email to confirm it, then sign in to open the terminal.");
        setMode("login");
        return;
      }

      await apiFetch("/auth/supabase/session", {
        method: "POST",
        body: JSON.stringify({ access_token: authPayload.access_token }),
      });
      const me = await apiFetch<AuthMeResponse>("/auth/me");
      shouldResetLoading = false;
      router.replace(me.tier_selection_required ? "/plans" : "/terminal");
      return;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Authentication failed.");
    } finally {
      if (shouldResetLoading) {
        setLoading(false);
      }
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
              disabled={loading}
              type="button"
            >
              Login
            </button>
            <button
              className={`auth-toggle-button ${mode === "register" ? "is-active" : ""}`}
              onClick={() => setMode("register")}
              disabled={loading}
              type="button"
            >
              Register
            </button>
          </div>
          {error ? (
            <div className="auth-error">{error}</div>
          ) : null}
          {notice ? <div className="auth-notice">{notice}</div> : null}
          <form onSubmit={handleSubmit} className="auth-form">
            {mode === "register" ? (
              <input
                className="auth-input"
                disabled={loading}
                placeholder="Name"
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            ) : null}
            <input
              className="auth-input"
              disabled={loading}
              placeholder="Email"
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <input
              className="auth-input"
              disabled={loading}
              placeholder="Password"
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button className="button button-primary auth-submit" disabled={loading} type="submit">
              {loading ? processingLabel : mode === "login" ? (
                "Sign In"
              ) : (
                "Create Account"
              )}
            </button>
          </form>
          <div className="auth-divider" aria-hidden="true">
            <span>or</span>
          </div>
          <button className="auth-oauth-button" disabled={loading} type="button">
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
          <div className="legal-links">
            <a href="/about">About</a>
            <a href="/pricing">Pricing</a>
            <a href="/privacy">Privacy</a>
            <a href="/terms">Terms</a>
          </div>
        </div>
      </section>
    </main>
  );
}
