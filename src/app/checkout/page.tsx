"use client";

import Link from "next/link";
import { useState } from "react";
import { useCart } from "@/lib/cart-context";
import { money } from "@/lib/money";
import { FREE_SHIPPING_THRESHOLD, products } from "@/lib/products";
import { ProductMedia } from "@/components/ProductMedia";
import { TeeArt } from "@/components/TeeArt";
import {
  IconArrowLeft,
  IconArrowRight,
  IconCheck,
  IconLock,
} from "@/components/Icons";

/* ---------------------------------------------------------------------------
   Checkout.

   Deliberately has NO card number / CVC / expiry fields. There is no payment
   processor connected, so a form that looked like it took payment would invite
   someone to type real card details into a page that does nothing with them —
   and card data must never touch our own inputs anyway. When Stripe or Shopify
   is wired up, payment is collected in their hosted element, not here.

   Everything up to that point is real: contact, address, shipping method and
   totals all work and carry through.
--------------------------------------------------------------------------- */

const SHIPPING_METHODS = [
  { key: "standard", name: "Standard", time: "3–5 business days", price: 10 },
  { key: "express", name: "Express", time: "1–2 business days", price: 15 },
] as const;

const STATES = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"];

type Step = 1 | 2 | 3;

export default function CheckoutPage() {
  const { lines, subtotal, hydrated } = useCart();
  const [step, setStep] = useState<Step>(1);
  const [method, setMethod] = useState<string>("standard");
  const [form, setForm] = useState({
    email: "",
    name: "",
    address: "",
    suburb: "",
    state: "NSW",
    postcode: "",
  });

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  if (!hydrated) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
        <div className="skeleton h-14 rounded-[20px]" />
        <div className="skeleton mt-4 h-64 rounded-[20px]" />
      </div>
    );
  }

  if (lines.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
        <h1 className="display distressed text-[40px] leading-none">
          nothing to check out
        </h1>
        <p className="mt-3 text-[15px] text-grey-dark">
          Your cart&apos;s empty, which makes this page fairly pointless.
        </p>
        <Link
          href="/shop"
          className="press mt-6 inline-flex h-14 items-center gap-3 rounded-[18px] bg-ink pr-5 pl-6 text-[16px] font-bold text-paper"
        >
          Go shopping
          <IconArrowRight className="h-5 w-5" />
        </Link>
      </div>
    );
  }

  const freeShipping = subtotal >= FREE_SHIPPING_THRESHOLD;
  const shipping = freeShipping
    ? 0
    : SHIPPING_METHODS.find((m) => m.key === method)!.price;
  const total = subtotal + shipping;

  const addressDone =
    form.email.includes("@") &&
    form.name.trim() &&
    form.address.trim() &&
    form.suburb.trim() &&
    /^\d{4}$/.test(form.postcode);

  const field =
    "h-14 w-full rounded-[16px] border border-ink/15 bg-transparent px-4 text-[16px] placeholder:text-grey";

  return (
    <div className="mx-auto max-w-2xl px-4 pt-4 pb-16 sm:px-6">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => (step === 1 ? history.back() : setStep((step - 1) as Step))}
          className="press -ml-2 inline-flex h-11 items-center gap-2 rounded-[14px] px-2 text-[13px] font-semibold tracking-wide uppercase"
        >
          <IconArrowLeft className="h-4 w-4" />
          Back
        </button>
        <span className="flex items-center gap-1.5 text-[13px] font-semibold tracking-wide text-grey-dark uppercase">
          <IconLock className="h-4 w-4" />
          Secure
        </span>
      </div>

      <h1 className="display distressed mt-2 text-[13vw] leading-[0.86] sm:text-[64px]">
        checkout
      </h1>

      {/* Progress */}
      <ol className="mt-6 flex gap-2" aria-label="Checkout progress">
        {["Details", "Shipping", "Review"].map((label, i) => {
          const n = (i + 1) as Step;
          return (
            <li key={label} className="flex-1">
              <div
                className={`h-1.5 rounded-full ${
                  n <= step ? "bg-lime" : "bg-ink/12"
                }`}
              />
              <span
                className={`mt-2 block text-[12px] font-semibold tracking-wide uppercase ${
                  n === step ? "text-ink" : "text-grey-dark"
                }`}
                aria-current={n === step ? "step" : undefined}
              >
                {label}
              </span>
            </li>
          );
        })}
      </ol>

      {/* ---------------- Step 1: details ---------------- */}
      {step === 1 && (
        <div className="fade-rise mt-8">
          <h2 className="display text-[22px]">Contact</h2>
          <input
            className={`${field} mt-3`}
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="you@email.com"
            aria-label="Email address"
            value={form.email}
            onChange={set("email")}
          />

          <h2 className="display mt-8 text-[22px]">Shipping address</h2>
          <div className="mt-3 flex flex-col gap-3">
            <input
              className={field}
              autoComplete="name"
              placeholder="Full name"
              aria-label="Full name"
              value={form.name}
              onChange={set("name")}
            />
            <input
              className={field}
              autoComplete="street-address"
              placeholder="Street address"
              aria-label="Street address"
              value={form.address}
              onChange={set("address")}
            />
            <input
              className={field}
              autoComplete="address-level2"
              placeholder="Suburb"
              aria-label="Suburb"
              value={form.suburb}
              onChange={set("suburb")}
            />
            <div className="flex gap-3">
              <select
                className={`${field} flex-1`}
                autoComplete="address-level1"
                aria-label="State"
                value={form.state}
                onChange={set("state")}
              >
                {STATES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <input
                className={`${field} w-32`}
                inputMode="numeric"
                autoComplete="postal-code"
                placeholder="Postcode"
                aria-label="Postcode"
                maxLength={4}
                value={form.postcode}
                onChange={set("postcode")}
              />
            </div>
          </div>

          <button
            type="button"
            disabled={!addressDone}
            onClick={() => setStep(2)}
            className="press mt-8 h-14 w-full rounded-[18px] bg-ink text-[16px] font-bold text-paper disabled:opacity-35"
          >
            Continue to shipping
          </button>
        </div>
      )}

      {/* ---------------- Step 2: shipping ---------------- */}
      {step === 2 && (
        <div className="fade-rise mt-8">
          <div className="rounded-[20px] border border-ink/12 p-4">
            <p className="text-[15px] font-semibold">{form.name}</p>
            <p className="text-[14px] text-grey-dark">
              {form.address}, {form.suburb} {form.state} {form.postcode}
            </p>
            <button
              type="button"
              onClick={() => setStep(1)}
              className="press mt-2 text-[13px] font-semibold underline underline-offset-4"
            >
              Change
            </button>
          </div>

          <h2 className="display mt-8 text-[22px]">Shipping method</h2>
          <ul className="mt-3 flex flex-col gap-2">
            {SHIPPING_METHODS.map((m) => {
              const active = method === m.key;
              const cost = freeShipping ? 0 : m.price;
              return (
                <li key={m.key}>
                  <button
                    type="button"
                    onClick={() => setMethod(m.key)}
                    aria-pressed={active}
                    className={`press flex w-full items-center justify-between gap-3 rounded-[16px] border px-4 py-4 text-left ${
                      active ? "border-lime bg-lime/10" : "border-ink/12"
                    }`}
                  >
                    <span>
                      <span className="block text-[15px] font-semibold">
                        {m.name}
                      </span>
                      <span className="text-[13px] text-grey-dark">{m.time}</span>
                    </span>
                    <span className="text-[15px] font-semibold tabular-nums">
                      {cost === 0 ? "Free" : money(cost)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          {freeShipping && (
            <p className="mt-3 text-[13px] text-grey-dark">
              Free shipping applied — you&apos;re over{" "}
              {money(FREE_SHIPPING_THRESHOLD)}.
            </p>
          )}

          <button
            type="button"
            onClick={() => setStep(3)}
            className="press mt-8 h-14 w-full rounded-[18px] bg-ink text-[16px] font-bold text-paper"
          >
            Continue to review
          </button>
        </div>
      )}

      {/* ---------------- Step 3: review ---------------- */}
      {step === 3 && (
        <div className="fade-rise mt-8">
          <h2 className="display text-[22px]">Your order</h2>
          <ul className="mt-3 flex flex-col gap-3">
            {lines.map((line) => {
              const product = products.find((p) => p.slug === line.slug);
              return (
                <li
                  key={`${line.slug}-${line.size}-${line.colour}`}
                  className="flex gap-3"
                >
                  <div className="relative h-[76px] w-[62px] shrink-0 overflow-hidden rounded-[12px] bg-paper-2">
                    {product ? (
                      <ProductMedia
                        product={product}
                        garment={
                          product.colours.find((c) => c.name === line.colour) ??
                          product.colours[0]
                        }
                        sizes="62px"
                      />
                    ) : (
                      <TeeArt
                        art={line.art}
                        garment={{
                          name: line.colour,
                          swatch: line.body,
                          body: line.body,
                          ink: line.ink,
                        }}
                        className="h-full w-full"
                      />
                    )}
                  </div>
                  <div className="flex min-w-0 flex-1 justify-between gap-2">
                    <span className="min-w-0">
                      <span className="block text-[15px] font-semibold">
                        {line.name}
                      </span>
                      <span className="text-[13px] text-grey-dark">
                        {line.colour} · {line.size} · Qty {line.quantity}
                      </span>
                    </span>
                    <span className="text-[15px] font-semibold tabular-nums">
                      {money(line.price * line.quantity)}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>

          <dl className="mt-6 flex flex-col gap-2 border-t border-ink/10 pt-5 text-[15px]">
            <div className="flex justify-between">
              <dt className="text-grey-dark">Subtotal</dt>
              <dd className="font-semibold tabular-nums">{money(subtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-grey-dark">Shipping</dt>
              <dd className="font-semibold tabular-nums">
                {shipping === 0 ? "Free" : money(shipping)}
              </dd>
            </div>
            <div className="mt-2 flex items-baseline justify-between border-t border-ink/10 pt-3">
              <dt className="display text-[20px]">Total</dt>
              <dd className="display text-[24px] tabular-nums">
                {money(total)}{" "}
                <span className="text-[13px] text-grey-dark">AUD</span>
              </dd>
            </div>
          </dl>

          {/* Payment is not connected. Say so plainly rather than showing a
              card form that would collect details nothing can process. */}
          <div className="mt-8 rounded-[20px] border-2 border-dashed border-ink/20 px-5 py-6 text-center">
            <p className="display text-[20px]">Payment isn&apos;t connected</p>
            <p className="mx-auto mt-2 max-w-[40ch] text-[14px] leading-relaxed text-grey-dark">
              There&apos;s no card form here on purpose — no processor is wired
              up yet, so nothing could be charged and card details shouldn&apos;t
              be typed into a page that can&apos;t handle them. Once Stripe or
              Shopify is connected, payment happens in their hosted form.
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

          <p className="mt-5 flex items-start gap-2 text-[13px] text-grey-dark">
            <IconCheck className="mt-0.5 h-4 w-4 shrink-0" />
            Your details stay in this browser — nothing has been sent anywhere.
          </p>
        </div>
      )}
    </div>
  );
}
