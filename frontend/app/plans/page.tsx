"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import styles from "./page.module.css";

type AuthMe = {
  tier: string;
  tier_selection_required?: boolean;
};

type Tier = {
  tier: string;
  label: string;
  description: string;
  watchlist_limit: number;
  briefing_history_limit: number;
  verified_calendar: boolean;
  webhook_delivery: boolean;
};

const TIER_CONTENT: Record<
  string,
  { tagline: string; additions: string[]; includes?: string[]; price: string; cadence: string }
> = {
  free: {
    tagline: "Start with core market context",
    price: "$0",
    cadence: "Always free",
    includes: [
      "Monitor workspace and core regime context",
      "Signals workspace with basic watchlist coverage",
      "Email preferences and fallback catalyst calendar",
    ],
    additions: [],
  },
  pro: {
    tagline: "For active individual traders",
    price: "$29",
    cadence: "per month",
    additions: [
      "World Affairs, Markets, and News workspaces",
      "Webhook, Slack, and Discord delivery channels",
      "Verified calendar access when provider is configured",
    ],
  },
  desk: {
    tagline: "Team workflows and shared context",
    price: "$99",
    cadence: "per month",
    additions: [
      "Shared desk workspace with invite codes",
      "Shared watchlist, notes, alerts, and briefing snapshots",
      "Expanded capacity for desk-style collaboration",
    ],
  },
};

export default function PlansPage() {
  const router = useRouter();
  const [tiers, setTiers] = useState<Tier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submittingTier, setSubmittingTier] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const [mePayload, tiersPayload] = await Promise.all([
          apiFetch<AuthMe>("/auth/me"),
          apiFetch<Tier[]>("/billing/tiers"),
        ]);
        if (cancelled) {
          return;
        }
        if (!mePayload.tier_selection_required) {
          router.replace("/terminal");
          return;
        }
        setTiers(tiersPayload);
      } catch (caught) {
        if (cancelled) {
          return;
        }
        const message = caught instanceof Error ? caught.message : "Unable to load plans.";
        if (message.toLowerCase().includes("not authenticated") || message.includes("401")) {
          router.replace("/login");
          return;
        }
        setError(message);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [router]);

  const ordered = useMemo(() => {
    const rank: Record<string, number> = { free: 0, pro: 1, desk: 2 };
    return [...tiers].sort((a, b) => (rank[a.tier] ?? 99) - (rank[b.tier] ?? 99));
  }, [tiers]);

  async function chooseFree() {
    setSubmittingTier("free");
    setError("");
    try {
      await apiFetch("/billing/select-free", { method: "POST" });
      router.replace("/terminal");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to continue with Free.");
    } finally {
      setSubmittingTier("");
    }
  }

  function choosePaid(tier: string) {
    setSubmittingTier(tier);
    router.push(`/billing?tier=${encodeURIComponent(tier)}`);
  }

  if (loading) {
    return (
      <main className={styles.plansShell}>
        <section className={styles.panel}>
          <h1 className={styles.title}>Loading plan options...</h1>
        </section>
      </main>
    );
  }

  return (
    <main className={styles.plansShell}>
      <section className={styles.panel}>
        <h1 className={styles.title}>Choose Your Plan Before Entering Regime</h1>
        <p className={styles.subtitle}>
          Pick a tier now, then continue to your dashboard. Paid tiers route to secure checkout.
        </p>
        {error ? <p className={styles.error}>{error}</p> : null}

        <div className={styles.cards}>
          {ordered.map((tier, index) => {
            const isFree = tier.tier === "free";
            const isBusy = submittingTier === tier.tier;
            const previousTier = index > 0 ? ordered[index - 1] : null;
            const content = TIER_CONTENT[tier.tier] ?? {
              tagline: tier.description,
              additions: [],
              includes: [],
              price: "--",
              cadence: "",
            };
            return (
              <article className={styles.card} key={tier.tier}>
                <div className={styles.head}>
                  <span className={styles.eyebrow}>{tier.label}</span>
                  <h2>{content.price}</h2>
                  <p className={styles.cadence}>{content.cadence}</p>
                  <p className={styles.tagline}>{content.tagline}</p>
                </div>

                <div className={styles.meta}>
                  <span>Watchlist {tier.watchlist_limit}</span>
                  <span>{tier.briefing_history_limit}-day history</span>
                </div>

                {previousTier ? (
                  <div className={styles.ladder}>
                    <p className={styles.inherits}>All features of {previousTier.label}</p>
                    <p className={styles.additionsLabel}>New in {tier.label}</p>
                    <ul className={styles.list}>
                      {content.additions.map((feature) => (
                        <li key={feature}>{feature}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className={styles.ladder}>
                    <p className={styles.inherits}>Core includes</p>
                    <ul className={styles.list}>
                      {(content.includes ?? []).map((feature) => (
                        <li key={feature}>{feature}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className={styles.capabilities}>
                  <span>Verified calendar: {tier.verified_calendar ? "Included" : "Not included"}</span>
                  <span>Webhook delivery: {tier.webhook_delivery ? "Included" : "Not included"}</span>
                </div>

                <button
                  className={`${styles.button} ${isFree ? styles.buttonAlt : ""}`}
                  disabled={Boolean(submittingTier)}
                  onClick={() => (isFree ? void chooseFree() : choosePaid(tier.tier))}
                  type="button"
                >
                  {isBusy ? "Processing..." : isFree ? "Continue with Free" : `Upgrade to ${tier.label}`}
                </button>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}
