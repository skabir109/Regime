"use client";

import { FormEvent, useEffect, useRef, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { loadStripe, type Stripe, type StripeElements, type StripePaymentElement } from "@stripe/stripe-js";
import { apiFetch } from "@/lib/api";
import styles from "./page.module.css";

type Tier = "pro" | "desk";

type BillingIntentResponse = {
  client_secret: string;
  intent_type: "payment" | "setup" | string;
  tier: string;
  subscription_id: string;
};

const stripeKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || "";

function BillingContent() {
  const searchParams = useSearchParams();
  const initialTier = (searchParams.get("tier") || "pro").toLowerCase() === "desk" ? "desk" : "pro";
  const [tier, setTier] = useState<Tier>(initialTier);
  const [clientSecret, setClientSecret] = useState("");
  const [intentType, setIntentType] = useState<"payment" | "setup">("payment");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [mounted, setMounted] = useState(false);

  const stripeRef = useRef<Stripe | null>(null);
  const elementsRef = useRef<StripeElements | null>(null);
  const paymentElementRef = useRef<StripePaymentElement | null>(null);
  const mountNodeRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadIntent() {
      setLoading(true);
      setError("");
      setMessage("");
      try {
        const payload = await apiFetch<BillingIntentResponse>("/billing/subscription/intent", {
          method: "POST",
          body: JSON.stringify({ tier }),
        });
        if (!cancelled) {
          setClientSecret(payload.client_secret);
          setIntentType(payload.intent_type === "setup" ? "setup" : "payment");
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Unable to start billing.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    if (!stripeKey) {
      setLoading(false);
      setError("Stripe publishable key is missing. Set NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY.");
      return () => {
        cancelled = true;
      };
    }

    void loadIntent();
    return () => {
      cancelled = true;
    };
  }, [tier]);

  useEffect(() => {
    let active = true;

    async function mountPaymentElement() {
      if (!clientSecret || !mountNodeRef.current || !stripeKey) {
        return;
      }

      if (!stripeRef.current) {
        stripeRef.current = await loadStripe(stripeKey);
      }
      if (!active || !stripeRef.current) {
        return;
      }

      // Recreate elements each time we get a new client_secret for a selected tier.
      if (paymentElementRef.current) {
        paymentElementRef.current.destroy();
        paymentElementRef.current = null;
      }
      if (elementsRef.current) {
        elementsRef.current = null;
      }

      const elements = stripeRef.current.elements({
        clientSecret,
        appearance: {
          theme: "night",
          variables: {
            fontFamily: "var(--font-inter), system-ui, -apple-system, sans-serif",
            colorPrimary: "#57d4ff",
            colorBackground: "#05080d",
            colorText: "#dce4ed",
            colorDanger: "#ff6d7b",
            colorTextSecondary: "#9ba9b8",
            colorIcon: "#57d4ff",
            borderRadius: "0",
            spacingGridRow: "20px",
          },
          rules: {
            ".Input": {
              border: "1px solid rgba(140, 160, 180, 0.22)",
              backgroundColor: "rgba(255, 255, 255, 0.02)",
              padding: "12px 14px",
            },
            ".Input:focus": {
              border: "1px solid #77cbec",
              boxShadow: "0 0 0 1px rgba(77, 226, 255, 0.18)",
            },
            ".Label": {
              fontSize: "0.78rem",
              fontWeight: "500",
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              marginBottom: "8px",
              color: "#9ba9b8",
              fontFamily: "var(--font-plex-mono), Consolas, monospace",
            },
            ".Tab": {
              border: "1px solid rgba(140, 160, 180, 0.22)",
              backgroundColor: "rgba(255, 255, 255, 0.02)",
            },
            ".Tab--selected": {
              border: "1px solid #57d4ff",
              backgroundColor: "rgba(87, 212, 255, 0.08)",
            },
          },
        },
      });
      elementsRef.current = elements;
      const payment = elements.create("payment");
      payment.mount(mountNodeRef.current);
      paymentElementRef.current = payment;
      setMounted(true);
    }

    void mountPaymentElement();

    return () => {
      active = false;
    };
  }, [clientSecret]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stripeRef.current || !elementsRef.current) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    const returnUrl = `${window.location.origin}/app?billing=success&tier=${encodeURIComponent(tier)}`;
    const result =
      intentType === "setup"
        ? await stripeRef.current.confirmSetup({
            elements: elementsRef.current,
            confirmParams: { return_url: returnUrl },
            redirect: "if_required",
          })
        : await stripeRef.current.confirmPayment({
            elements: elementsRef.current,
            confirmParams: { return_url: returnUrl },
            redirect: "if_required",
          });

    if (result.error) {
      setError(result.error.message || "Payment confirmation failed.");
      setSubmitting(false);
      return;
    }

    const paymentStatus =
      "paymentIntent" in result && result.paymentIntent ? result.paymentIntent.status : undefined;
    const setupStatus = "setupIntent" in result && result.setupIntent ? result.setupIntent.status : undefined;
    const status = paymentStatus || setupStatus;
    if (status === "succeeded" || status === "processing" || status === "requires_capture") {
      setMessage("Payment submitted. Redirecting...");
      window.location.href = returnUrl;
      return;
    }

    setMessage("Payment requires additional action. Complete the Stripe flow to finish.");
    setSubmitting(false);
  }

  return (
    <main className={styles.billingShell}>
      <section className={styles.billingCard}>
        <header className={styles.header}>
          <span className={styles.eyebrow}>Regime Billing</span>
          <h1>Complete Your Upgrade</h1>
          <p>Secure payment via Stripe. Your workspace tier updates automatically after confirmation.</p>
        </header>

        <div className={styles.controls}>
          <button
            className={`${styles.planButton} ${tier === "pro" ? styles.planButtonActive : ""}`}
            onClick={() => setTier("pro")}
            type="button"
          >
            Pro Tier
          </button>
          <button
            className={`${styles.planButton} ${tier === "desk" ? styles.planButtonActive : ""}`}
            onClick={() => setTier("desk")}
            type="button"
          >
            Desk Tier
          </button>
        </div>

        <div className={styles.stripeWrap}>
          {loading ? <p className={styles.message}>Preparing secure payment form...</p> : null}
          {!loading && error ? <p className={`${styles.message} ${styles.error}`}>{error}</p> : null}
          <form onSubmit={handleSubmit}>
            <div ref={mountNodeRef} />
            {!loading && !error && mounted ? (
              <div className={styles.paymentActions}>
                <button className="button button-primary" disabled={submitting} type="submit" style={{ width: '100%' }}>
                  {submitting ? "Processing..." : `Confirm ${tier.toUpperCase()} Plan`}
                </button>
              </div>
            ) : null}
          </form>
          {message ? <p className={styles.message}>{message}</p> : null}
        </div>

        <div className={styles.links}>
          <Link href="/app">Back to Terminal</Link>
          <Link href="/pricing">View All Plans</Link>
        </div>
      </section>
    </main>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={<div>Loading billing details...</div>}>
      <BillingContent />
    </Suspense>
  );
}
