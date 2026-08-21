"use client";

import Link from "next/link";
import { useState } from "react";
import { IconArrowRight, IconLock, IconTruck } from "@/components/Icons";
import { account } from "@/lib/content-data.generated";
import { money } from "@/lib/money";

type OrderStatusResult = {
  reference: string;
  status: string;
  createdAt: string;
  trackingNumber: string | null;
  carrier: string | null;
  subtotalCents: number;
  discountCents: number;
  shippingCents: number;
  totalCents: number;
  items: {
    productName: string;
    colourName: string | null;
    size: string | null;
    quantity: number;
    unitPriceCents: number;
  }[];
};

/**
 * Signed-out account view. There is no auth backend yet, so this collects
 * nothing and promises nothing — it explains what an account will do and
 * offers order lookup, which is the only thing a guest actually needs.
 */
export default function AccountPage() {
  const [order, setOrder] = useState("");
  const [email, setEmail] = useState("");
  const [looking, setLooking] = useState(false);
  const [result, setResult] = useState<OrderStatusResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function lookUp(e: React.FormEvent) {
    e.preventDefault();
    setLooking(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/order-status", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ reference: order, email }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(body.error ?? "Couldn't find that order.");
        return;
      }
      setResult(body.order);
    } catch {
      setError("Couldn't reach the server. Try again.");
    } finally {
      setLooking(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 pt-8 pb-16 sm:px-6">
      <h1 className="display text-[16vw] leading-[0.84] sm:text-[76px]">
        account
      </h1>
      <p className="mt-4 max-w-[42ch] text-[16px] text-ink/70">{account.intro}</p>

      <section className="mt-9 rounded-[20px] border border-ink/12 p-5">
        <h2 className="display text-[22px]">Track an order</h2>
        <p className="mt-1 text-[14px] text-grey-dark">
          Order number from your confirmation email, e.g. SF67389.
        </p>

        <form className="mt-4 flex flex-col gap-2" onSubmit={lookUp}>
          <label htmlFor="order" className="sr-only">
            Order number
          </label>
          <input
            id="order"
            value={order}
            onChange={(e) => {
              setOrder(e.target.value);
              setResult(null);
              setError(null);
            }}
            placeholder="SF00000"
            autoComplete="off"
            className="h-14 min-w-0 flex-1 rounded-[16px] border border-ink/15 bg-transparent px-4 text-[16px] placeholder:text-grey"
          />
          <label htmlFor="email" className="sr-only">
            Email used at checkout
          </label>
          <div className="flex gap-2">
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setResult(null);
                setError(null);
              }}
              placeholder="Email used at checkout"
              autoComplete="email"
              className="h-14 min-w-0 flex-1 rounded-[16px] border border-ink/15 bg-transparent px-4 text-[16px] placeholder:text-grey"
            />
            <button
              type="submit"
              disabled={!order.trim() || !email.trim() || looking}
              className="press grid h-14 w-14 shrink-0 place-items-center rounded-[16px] bg-ink text-paper disabled:opacity-35"
              aria-label="Look up order"
            >
              <IconArrowRight className="h-5 w-5" />
            </button>
          </div>
        </form>

        {error && (
          <p role="alert" className="fade-rise mt-4 rounded-[16px] bg-coral/10 px-4 py-3 text-[14px] text-coral">
            {error}
          </p>
        )}

        {result && (
          <div className="fade-rise mt-4 rounded-[16px] bg-paper-2 px-4 py-4 text-[14px]">
            <div className="flex items-center justify-between">
              <span className="font-semibold">{result.reference}</span>
              <span className="rounded-full bg-ink px-3 py-1 text-[11px] font-bold tracking-wide text-paper uppercase">
                {result.status}
              </span>
            </div>
            <ul className="mt-3 flex flex-col gap-1 text-ink/70">
              {result.items.map((item, i) => (
                <li key={i}>
                  {item.productName}
                  {item.colourName ? ` · ${item.colourName}` : ""}
                  {item.size ? ` · ${item.size}` : ""} · Qty {item.quantity}
                </li>
              ))}
            </ul>
            {result.trackingNumber ? (
              <p className="mt-3 text-ink/70">
                Tracking: <span className="font-semibold text-ink">{result.trackingNumber}</span>
                {result.carrier ? ` (${result.carrier})` : ""}
              </p>
            ) : (
              <p className="mt-3 text-ink/70">Not shipped yet.</p>
            )}
            <p className="mt-3 border-t border-ink/10 pt-3 font-semibold">
              Total {money(result.totalCents / 100)}
            </p>
          </div>
        )}
      </section>

      <section className="mt-6 rounded-[20px] bg-ink px-5 py-6 text-paper">
        <h2 className="display text-[22px]">What an account will do</h2>
        <ul className="mt-4 flex flex-col gap-4">
          {[IconTruck, IconLock, IconArrowRight].map((Icon, i) => {
            const { a, b } = account.benefits[i];
            return (
              <li key={a} className="flex items-start gap-3">
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-paper/70" strokeWidth={1.8} />
                <span className="text-[15px] leading-tight">
                  {a}
                  <br />
                  <span className="text-paper/55">{b}</span>
                </span>
              </li>
            );
          })}
        </ul>
      </section>

      <Link
        href="/shop"
        className="press mt-8 inline-flex h-14 items-center gap-3 rounded-[18px] bg-ink pr-5 pl-6 text-[16px] font-bold text-paper"
      >
        Back to the shop
        <IconArrowRight className="h-5 w-5" />
      </Link>
    </div>
  );
}
