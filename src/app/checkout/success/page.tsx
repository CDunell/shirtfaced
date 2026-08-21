"use client";

import { useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCart } from "@/lib/cart-context";
import { IconArrowRight, IconCheck } from "@/components/Icons";
import { trackPurchase, hasTrackedPurchase, markPurchaseTracked } from "@/lib/analytics";

function SuccessContent() {
  const { lines, subtotal, clearCart } = useCart();
  const orderId = useSearchParams().get("orderId");

  useEffect(() => {
    // Covers the redirect-based confirmation path (bank redirects, some 3DS
    // flows) — PaymentStep already tracks the purchase and clears the cart on
    // the inline path, but a payment method that leaves the page via
    // return_url skips that call entirely and lands here instead, with the
    // cart still populated (nothing else has cleared it yet).
    if (orderId && lines.length > 0 && !hasTrackedPurchase(orderId)) {
      // subtotal only — shipping/discount live in the checkout page's own
      // pricing calc, which this page (reached via bank redirect, no state
      // carried over) has no access to.
      trackPurchase({
        transactionId: orderId,
        value: subtotal,
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
    }
    clearCart();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-lime">
        <IconCheck className="h-8 w-8 text-ink" />
      </div>
      <h1 className="display mt-6 text-[13vw] leading-[0.86] sm:text-[56px]">
        order placed
      </h1>
      <p className="mx-auto mt-3 max-w-[42ch] text-[15px] text-grey-dark">
        A confirmation is on its way to your inbox. We&apos;ll email again the
        moment it ships.
      </p>
      {orderId && (
        <p className="mt-4 text-[12px] tracking-wide text-grey-dark uppercase">
          Reference {orderId.slice(0, 8)}
        </p>
      )}
      <Link
        href="/shop"
        className="press mt-10 inline-flex h-14 items-center gap-3 rounded-[18px] bg-ink pr-5 pl-6 text-[16px] font-bold text-paper"
      >
        Keep shopping
        <IconArrowRight className="h-5 w-5" />
      </Link>
    </div>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={null}>
      <SuccessContent />
    </Suspense>
  );
}
