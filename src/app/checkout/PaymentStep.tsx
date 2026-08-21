"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { loadStripe, type Stripe as StripeJs } from "@stripe/stripe-js";
import {
  Elements,
  PaymentElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import { useCart } from "@/lib/cart-context";
import { money } from "@/lib/money";
import { IconLock } from "@/components/Icons";
import type { CartLineInput } from "@/lib/checkout-pricing";
import { trackPurchase, markPurchaseTracked } from "@/lib/analytics";

const publishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
let stripePromise: Promise<StripeJs | null> | null = null;
if (publishableKey) {
  stripePromise = loadStripe(publishableKey);
}

export type CheckoutRequest = {
  lines: CartLineInput[];
  shippingMethod: string;
  contact: { email: string; name: string };
  address: { line1: string; suburb: string; state: string; postcode: string };
  discountCode: string | null;
};

/** Same "no card form here" honesty as before, now shown only when payments
 * actually aren't configured, rather than always. */
function NotConnected({ total }: { total: number }) {
  return (
    <div className="mt-8 rounded-[20px] border-2 border-dashed border-ink/20 px-5 py-6 text-center">
      <p className="display text-[20px]">Payment isn&apos;t connected</p>
      <p className="mx-auto mt-2 max-w-[40ch] text-[14px] leading-relaxed text-grey-dark">
        No card form here on purpose — no processor is wired up yet, so
        nothing could be charged. Once Stripe keys are set, payment happens
        right here, in Stripe&apos;s own embedded form.
      </p>
      <button
        type="button"
        disabled
        className="mt-5 inline-flex h-14 w-full cursor-not-allowed items-center justify-center gap-2 rounded-[18px] bg-lime text-[16px] font-bold text-ink opacity-50"
      >
        <IconLock className="h-5 w-5" />
        Pay {money(total)}
      </button>
    </div>
  );
}

export function PaymentStep({
  request,
  total,
}: {
  request: CheckoutRequest;
  total: number;
}) {
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [orderId, setOrderId] = useState<string | null>(null);
  const [notConfigured, setNotConfigured] = useState(!publishableKey);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!publishableKey) return;

    let cancelled = false;

    fetch("/api/create-payment-intent", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(request),
    })
      .then(async (res) => {
        const body = await res.json().catch(() => ({}));
        if (cancelled) return;
        if (res.status === 503 || body.notConfigured) {
          setNotConfigured(true);
          return;
        }
        if (!res.ok) {
          setError(body.error || "Couldn't start checkout. Try again.");
          return;
        }
        setClientSecret(body.clientSecret);
        setOrderId(body.orderId);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't reach the server. Check your connection and try again.");
      });

    return () => {
      cancelled = true;
    };
    // Deliberately once per mount of the review step, not on every keystroke
    // upstream — a new PaymentIntent (and a new draft order) per keystroke
    // would leave a trail of abandoned pending orders in admin.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (notConfigured) return <NotConnected total={total} />;

  if (error) {
    return (
      <div className="mt-8 rounded-[20px] border border-coral/40 bg-coral/10 px-5 py-4 text-[14px] text-coral">
        {error}
      </div>
    );
  }

  if (!clientSecret || !orderId || !stripePromise) {
    return <div className="skeleton mt-8 h-48 rounded-[20px]" />;
  }

  return (
    <Elements stripe={stripePromise} options={{ clientSecret }}>
      <PaymentForm orderId={orderId} total={total} />
    </Elements>
  );
}

function PaymentForm({ orderId, total }: { orderId: string; total: number }) {
  const stripe = useStripe();
  const elements = useElements();
  const router = useRouter();
  const { lines, clearCart } = useCart();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!stripe || !elements) return;
    setSubmitting(true);
    setError(null);

    const { error: confirmError, paymentIntent } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/checkout/success?orderId=${orderId}`,
      },
      redirect: "if_required",
    });

    if (confirmError) {
      setError(confirmError.message ?? "Payment failed. Check your details and try again.");
      setSubmitting(false);
      return;
    }

    // A payment method needing an off-page step (bank redirect, some 3DS
    // flows) already left via return_url above and never reaches this line.
    // Anything that returns here without redirecting is either settled or
    // on its way — either way the customer's part is done.
    if (paymentIntent) {
      trackPurchase({
        transactionId: orderId,
        value: total,
        currency: "AUD",
        items: lines.map((line) => ({
          id: line.slug,
          name: line.name,
          price: line.price,
          quantity: line.quantity,
          variant: `${line.colour} / ${line.size}`,
        })),
      });
      markPurchaseTracked(orderId);
      clearCart();
      router.push(`/checkout/success?orderId=${orderId}`);
    } else {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
      <PaymentElement />
      {error && (
        <p role="alert" className="text-[13px] font-semibold text-coral">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={!stripe || submitting}
        className="press flex h-14 w-full items-center justify-center gap-2 rounded-[18px] bg-lime text-[16px] font-bold text-ink disabled:opacity-50"
      >
        <IconLock className="h-5 w-5" />
        {submitting ? "Processing…" : `Pay ${money(total)}`}
      </button>
    </form>
  );
}
