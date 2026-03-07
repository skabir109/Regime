"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { SignedIn, SignedOut, useAuth, useClerk, useSignIn, useSignUp } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";

type AuthMode = "login" | "register";
type OAuthStrategy = "oauth_google" | "oauth_discord" | "oauth_slack";

type AuthMeResponse = {
  tier_selection_required?: boolean;
};

type ClerkBridgeProps = {
  onError: (message: string) => void;
  onFailure: () => void;
};

function clerkErrorMessage(error: unknown, fallback: string): string {
  if (!error || typeof error !== "object") {
    return fallback;
  }
  const maybeWithErrors = error as { errors?: Array<{ longMessage?: string; message?: string }> };
  const first = maybeWithErrors.errors?.[0];
  return first?.longMessage || first?.message || fallback;
}

export default function LoginPage() {
  return <ClerkLoginPage />;
}

async function withTimeout<T>(promise: Promise<T>, timeoutMs: number, message: string): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  const timeoutPromise = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => reject(new Error(message)), timeoutMs);
  });
  try {
    return await Promise.race([promise, timeoutPromise]);
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
}

function ClerkSessionBridge({ onError, onFailure }: ClerkBridgeProps) {
  const router = useRouter();
  const { getToken } = useAuth();

  useEffect(() => {
    let active = true;

    async function bridgeSession() {
      try {
        const sessionToken = await getToken();
        if (!sessionToken) {
          throw new Error("Unable to read session token.");
        }

        await withTimeout(
          apiFetch("/auth/clerk/session", {
            method: "POST",
            body: JSON.stringify({ session_token: sessionToken }),
          }),
          12000,
          "Session handshake timed out. Please try again.",
        );

        const me = await withTimeout(
          apiFetch<AuthMeResponse>("/auth/me"),
          12000,
          "Profile load timed out. Please try again.",
        );
        if (!active) {
          return;
        }
        router.replace(me.tier_selection_required ? "/plans" : "/terminal");
      } catch (caught) {
        if (!active) {
          return;
        }
        onError(caught instanceof Error ? caught.message : "Failed to complete sign-in.");
        onFailure();
      }
    }

    void bridgeSession();
    return () => {
      active = false;
    };
  }, [getToken, onError, onFailure, router]);

  return null;
}

function ClerkLoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signOut } = useClerk();
  const { isLoaded: signInLoaded, signIn, setActive: setSignInActive } = useSignIn();
  const { isLoaded: signUpLoaded, signUp, setActive: setSignUpActive } = useSignUp();

  const [mode, setMode] = useState<AuthMode>("login");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [allowAutoBridge, setAllowAutoBridge] = useState(searchParams.get("bridge") === "1");

  const isLogin = mode === "login";
  const processingLabel = isLogin ? "Signing you in..." : "Creating your account...";
  const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

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

    try {
      setAllowAutoBridge(true);
      if (isLogin) {
        if (!signInLoaded || !signIn || !setSignInActive) {
          throw new Error("Authentication is still loading. Try again.");
        }
        const attempt = await signIn.create({ identifier: normalizedEmail, password });
        if (attempt.status !== "complete" || !attempt.createdSessionId) {
          throw new Error("Unable to complete login. Check your credentials and try again.");
        }
        await setSignInActive({ session: attempt.createdSessionId });
      } else {
        if (!signUpLoaded || !signUp || !setSignUpActive) {
          throw new Error("Authentication is still loading. Try again.");
        }
        const attempt = await signUp.create({
          emailAddress: normalizedEmail,
          password,
          unsafeMetadata: { name: normalizedName },
        });

        if (attempt.status === "complete" && attempt.createdSessionId) {
          await setSignUpActive({ session: attempt.createdSessionId });
        } else {
          setNotice("Account created. Complete verification, then sign in.");
          setMode("login");
        }
      }
    } catch (caught) {
      setError(clerkErrorMessage(caught, "Authentication failed."));
    } finally {
      setLoading(false);
    }
  }

  async function handleOAuth(strategy: OAuthStrategy) {
    if (loading) {
      return;
    }
    setLoading(true);
    setError("");
    setNotice("");

    try {
      const redirectUrl = "/sso-callback";
      const redirectUrlComplete = "/login?bridge=1";

      if (isLogin) {
        if (!signInLoaded || !signIn) {
          throw new Error("Authentication is still loading. Try again.");
        }
        await signIn.authenticateWithRedirect({ strategy, redirectUrl, redirectUrlComplete });
      } else {
        if (!signUpLoaded || !signUp) {
          throw new Error("Authentication is still loading. Try again.");
        }
        await signUp.authenticateWithRedirect({ strategy, redirectUrl, redirectUrlComplete });
      }
    } catch (caught) {
      setError(clerkErrorMessage(caught, "Unable to start OAuth flow."));
      setLoading(false);
    }
  }

  async function handleClerkSignOut() {
    setError("");
    setNotice("");
    setAllowAutoBridge(false);
    await signOut({ redirectUrl: "/login" });
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
          {clerkEnabled ? (
            <>
              <SignedOut>
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

                {error ? <div className="auth-error">{error}</div> : null}
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
                    type="email"
                    autoComplete="email"
                    disabled={loading}
                    placeholder="Email"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                  <input
                    className="auth-input"
                    type="password"
                    autoComplete={isLogin ? "current-password" : "new-password"}
                    disabled={loading}
                    placeholder="Password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                  <button className="button button-primary auth-submit" disabled={loading} type="submit">
                    {loading ? processingLabel : isLogin ? "Sign In" : "Create Account"}
                  </button>
                </form>

                <div className="auth-divider">or continue with</div>
                <div className="auth-social-grid">
                  <button
                    className="auth-oauth-button auth-oauth-google"
                    disabled={loading}
                    onClick={() => void handleOAuth("oauth_google")}
                    type="button"
                  >
                    <span className="auth-oauth-icon" aria-hidden="true">
                      <img src="/brands/google-official-v2.svg" alt="" />
                    </span>
                    Google
                  </button>
                  <button
                    className="auth-oauth-button auth-oauth-discord"
                    disabled={loading}
                    onClick={() => void handleOAuth("oauth_discord")}
                    type="button"
                  >
                    <span className="auth-oauth-icon" aria-hidden="true">
                      <img src="/brands/discord-original.svg" alt="" />
                    </span>
                    Discord
                  </button>
                  <button
                    className="auth-oauth-button auth-oauth-slack"
                    disabled={loading}
                    onClick={() => void handleOAuth("oauth_slack")}
                    type="button"
                  >
                    <span className="auth-oauth-icon" aria-hidden="true">
                      <img src="/brands/slack-official-v2.svg" alt="" />
                    </span>
                    Slack
                  </button>
                </div>
              </SignedOut>

              <SignedIn>
                {allowAutoBridge ? (
                  <>
                    <div className="auth-notice">Signing you in...</div>
                    {error ? <div className="auth-error">{error}</div> : null}
                    <ClerkSessionBridge onError={setError} onFailure={() => setAllowAutoBridge(false)} />
                  </>
                ) : (
                  <>
                    <div className="auth-notice">
                      Your account is authenticated. Continue to open Regime.
                    </div>
                    <div className="auth-form">
                      <button
                        className="button button-primary auth-submit"
                        type="button"
                        onClick={() => setAllowAutoBridge(true)}
                      >
                        Continue to Regime
                      </button>
                      <button className="button auth-submit" type="button" onClick={() => void handleClerkSignOut()}>
                        Sign Out
                      </button>
                    </div>
                  </>
                )}
              </SignedIn>
            </>
          ) : (
            <div className="auth-error">
              Authentication is not configured. Set <code>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> in
              <code> frontend/.env.local</code>.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
