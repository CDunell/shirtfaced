"use client";

import Link from "next/link";
import { useState } from "react";
import { useCart } from "@/lib/cart-context";
import { money } from "@/lib/money";
import { FREE_SHIPPING_THRESHOLD, categoryFromSlug } from "@/lib/products";
import { SHIPPING_METHODS } from "@/lib/checkout-pricing";
import { GarmentArt } from "@/components/GarmentArt";
import { PaymentStep, type CheckoutRequest } from "./PaymentStep";
import { IconArrowLeft, IconArrowRight, IconCheck, IconLock } from "@/components/Icons";

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
        <div className="skeleton h-14 rounded-card" />
        <div className="skeleton mt-4 h-64 rounded-card" />
      </div>
    );
  }

  if (lines.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6">
        <h1 className="display text-[40px] leading-none">nothing to check out</h1>
        <p className="mt-3 text-[15px] text-grey-dark">Your cart&apos;s empty.</p>
        <Link
          href="/shop"
          className="press mt-6 inline-flex h-14 items-center gap-3 rounded-full bg-ink px-6 text-[16px] font-extrabold text-paper"
        >
          Go shopping
          <IconArrowRight className="h-5 w-5" />
        </Link>
      </div>
    );
  }

  const freeShipping = subtotal >= FREE_SHIPPING_THRESHOLD;
  const shipping = freeShipping ? 0 : SHIPPING_METHODS.find((m) => m.key === method)!.price;
  const total = subtotal + shipping;

  const addressDone =
    form.email.includes("@") &&
    form.name.trim() &&
    form.address.trim() &&
    form.suburb.trim() &&
    /^\d{4}$/.test(form.postcode);

  const field =
    "h-14 rounded-2xl border-2 border-ink/15 bg-transparent px-4 text-[16px] placeholder:text-grey";

  return (
    <div className="mx-auto max-w-2xl px-4 pt-4 pb-16 sm:px-6">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => (step === 1 ? history.back() : setStep((step - 1) as Step))}
          className="press -ml-2 inline-flex h-11 items-center gap-2 rounded-full px-3 text-[13px] font-bold text-grey-dark"
        >
          <IconArrowLeft className="h-4 w-4" />
          Back
        </button>
        <span className="flex items-center gap-1.5 text-[13px] font-bold text-grey-dark">
          <IconLock className="h-4 w-4" />
          Secure
        </span>
      </div>

      <h1 className="display mt-2 text-[13vw] leading-[0.9] sm:text-[54px]">checkout</h1>

      <ol className="mt-6 flex gap-2" aria-label="Checkout progress">
        {["Details", "Shipping", "Review"].map((label, i) => {
          const n = (i + 1) as Step;
          return (
            <li key={label} className="flex-1">
              <div className={`h-1.5 rounded-full ${n <= step ? "bg-grit-pink" : "bg-ink/12"}`} />
              <span
                className={`mt-2 block text-[12px] font-bold ${n === step ? "text-ink" : "text-grey-dark"}`}
                aria-current={n === step ? "step" : undefined}
              >
                {label}
              </span>
            </li>
          );
        })}
      </ol>

      {step === 1 && (
        <div className="fade-rise mt-8">
          <h2 className="display text-[22px]">Contact</h2>
          <input
            className={`${field} mt-3 w-full`}
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
              className={`${field} w-full`}
              autoComplete="name"
              placeholder="Parent / guardian name"
              aria-label="Full name"
              value={form.name}
              onChange={set("name")}
            />
            <input
              className={`${field} w-full`}
              autoComplete="street-address"
              placeholder="Street address"
              aria-label="Street address"
              value={form.address}
              onChange={set("address")}
            />
            <input
              className={`${field} w-full`}
              autoComplete="address-level2"
              placeholder="Suburb"
              aria-label="Suburb"
              value={form.suburb}
              onChange={set("suburb")}
            />
            <div className="flex gap-3">
              <select
                className={`${field} min-w-0 flex-1 appearance-none bg-[length:12px] bg-[right_1rem_center] bg-no-repeat pr-10`}
                style={{
                  backgroundImage:
                    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231c1a17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9.5 6 6 6-6'/%3E%3C/svg%3E\")",
                }}
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
                className={`${field} w-32 shrink-0`}
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
            className="press mt-8 h-14 w-full rounded-full bg-ink text-[16px] font-extrabold text-paper disabled:opacity-35"
          >
            Continue to shipping
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="fade-rise mt-8">
          <div className="rounded-card border-2 border-ink/12 p-4">
            <p className="text-[15px] font-bold">{form.name}</p>
            <p className="text-[14px] text-grey-dark">
              {form.address}, {form.suburb} {form.state} {form.postcode}
            </p>
            <button
              type="button"
              onClick={() => setStep(1)}
              className="press mt-2 text-[13px] font-bold underline underline-offset-4"
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
                    className={`press flex w-full items-center justify-between gap-3 rounded-2xl border-2 px-4 py-4 text-left ${
                      active ? "border-grit-pink bg-grit-pink/10" : "border-ink/12"
                    }`}
                  >
                    <span>
                      <span className="block text-[15px] font-bold">{m.name}</span>
                      <span className="text-[13px] text-grey-dark">{m.time}</span>
                    </span>
                    <span className="text-[15px] font-bold tabular-nums">
                      {cost === 0 ? "Free" : money(cost)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          {freeShipping && (
            <p className="mt-3 text-[13px] text-grey-dark">
              Free shipping applied — you&apos;re over {money(FREE_SHIPPING_THRESHOLD)}.
            </p>
          )}

          <button
            type="button"
            onClick={() => setStep(3)}
            className="press mt-8 h-14 w-full rounded-full bg-ink text-[16px] font-extrabold text-paper"
          >
            Continue to review
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="fade-rise mt-8">
          <h2 className="display text-[22px]">Your order</h2>
          <ul className="mt-3 flex flex-col gap-3">
            {lines.map((line) => (
              <li key={`${line.slug}-${line.size}-${line.colour}`} className="flex gap-3">
                <GarmentArt
                  category={categoryFromSlug(line.slug)}
                  bodyColour={line.body}
                  art={line.art}
                  artDark={line.artDark}
                  creatureName={line.name}
                  className="h-[76px] w-[62px] shrink-0 rounded-xl"
                />
                <div className="flex min-w-0 flex-1 justify-between gap-2">
                  <span className="min-w-0">
                    <span className="block text-[15px] font-bold">{line.name}</span>
                    <span className="text-[13px] text-grey-dark">
                      {line.colour} · {line.size} · Qty {line.quantity}
                    </span>
                  </span>
                  <span className="text-[15px] font-bold tabular-nums">{money(line.price * line.quantity)}</span>
                </div>
              </li>
            ))}
          </ul>

          <dl className="mt-6 flex flex-col gap-2 border-t-2 border-ink/10 pt-5 text-[15px]">
            <div className="flex justify-between">
              <dt className="text-grey-dark">Subtotal</dt>
              <dd className="font-bold tabular-nums">{money(subtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-grey-dark">Shipping</dt>
              <dd className="font-bold tabular-nums">{shipping === 0 ? "Free" : money(shipping)}</dd>
            </div>
            <div className="mt-2 flex items-baseline justify-between border-t-2 border-ink/10 pt-3">
              <dt className="display text-[20px]">Total</dt>
              <dd className="display text-[24px] tabular-nums">
                {money(total)} <span className="text-[13px] text-grey-dark">AUD</span>
              </dd>
            </div>
          </dl>

          <PaymentStep
            request={{
              lines: lines.map((l) => ({ slug: l.slug, size: l.size, colour: l.colour, quantity: l.quantity })),
              shippingMethod: method,
              contact: { email: form.email, name: form.name },
              address: { line1: form.address, suburb: form.suburb, state: form.state, postcode: form.postcode },
            } satisfies CheckoutRequest}
            total={total}
          />

          <p className="mt-5 flex items-start gap-2 text-[13px] text-grey-dark">
            <IconCheck className="mt-0.5 h-4 w-4 shrink-0" />
            Card details go straight to Stripe — this page never sees or stores them.
          </p>
        </div>
      )}
    </div>
  );
}
