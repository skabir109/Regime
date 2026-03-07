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

export default function PlansPage() {
  const router = useRouter();
  const [me, setMe] = useState<AuthMe | null>(null);
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
        setMe(mePayload);
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
          Select Free to continue instantly, or choose Pro/Desk to open secure billing checkout.
        </p>
        {error ? <p className={styles.error}>{error}</p> : null}

        <div className={styles.cards}>
          {ordered.map((tier) => {
            const isFree = tier.tier === "free";
            const isBusy = submittingTier === tier.tier;
            return (
              <article className={styles.card} key={tier.tier}>
                <h3>{tier.label}</h3>
                <p>{tier.description}</p>
                <p>Watchlist: {tier.watchlist_limit}</p>
                <p>History: {tier.briefing_history_limit}</p>
                <p>Verified calendar: {tier.verified_calendar ? "Yes" : "No"}</p>
                <p>Webhook delivery: {tier.webhook_delivery ? "Yes" : "No"}</p>
                <button
                  className={`${styles.button} ${isFree ? styles.buttonAlt : ""}`}
                  disabled={Boolean(submittingTier)}
                  onClick={() => (isFree ? void chooseFree() : choosePaid(tier.tier))}
                  type="button"
                >
                  {isBusy ? "Processing..." : isFree ? "Continue with Free" : `Choose ${tier.label}`}
                </button>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}
