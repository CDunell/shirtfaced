"use client";

import Link from "next/link";
import { useState } from "react";
import { IconArrowRight, IconLock, IconTruck } from "@/components/Icons";

/**
 * Signed-out account view. There is no auth backend yet, so this collects
 * nothing and promises nothing — it explains what an account will do and
 * offers order lookup, which is the only thing a guest actually needs.
 */
export default function AccountPage() {
  const [order, setOrder] = useState("");
  const [looked, setLooked] = useState(false);

  return (
    <div className="mx-auto max-w-2xl px-4 pt-8 pb-16 sm:px-6">
      <h1 className="display text-[16vw] leading-[0.84] sm:text-[76px]">
        account
      </h1>
      <p className="mt-4 max-w-[42ch] text-[16px] text-ink/70">
        Accounts aren&apos;t open yet. You can still track an order — that&apos;s
        the only bit anyone actually wants.
      </p>

      <section className="mt-9 rounded-[20px] border border-ink/12 p-5">
        <h2 className="display text-[22px]">Track an order</h2>
        <p className="mt-1 text-[14px] text-grey-dark">
          Order number from your confirmation email, e.g. SF67389.
        </p>

        <form
          className="mt-4 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            setLooked(true);
          }}
        >
          <label htmlFor="order" className="sr-only">
            Order number
          </label>
          <input
            id="order"
            value={order}
            onChange={(e) => {
              setOrder(e.target.value);
              setLooked(false);
            }}
            placeholder="SF00000"
            autoComplete="off"
            className="h-14 min-w-0 flex-1 rounded-[16px] border border-ink/15 bg-transparent px-4 text-[16px] placeholder:text-grey"
          />
          <button
            type="submit"
            disabled={!order.trim()}
            className="press grid h-14 w-14 shrink-0 place-items-center rounded-[16px] bg-ink text-paper disabled:opacity-35"
            aria-label="Look up order"
          >
            <IconArrowRight className="h-5 w-5" />
          </button>
        </form>

        {looked && (
          <p className="fade-rise mt-4 rounded-[16px] bg-paper-2 px-4 py-3 text-[14px] text-ink/75">
            Order tracking isn&apos;t connected yet — nothing was looked up. Once
            orders are live this will show status and tracking.
          </p>
        )}
      </section>

      <section className="mt-6 rounded-[20px] bg-ink px-5 py-6 text-paper">
        <h2 className="display text-[22px]">What an account will do</h2>
        <ul className="mt-4 flex flex-col gap-4">
          {[
            { Icon: IconTruck, a: "Order history", b: "Everything you've regretted, itemised" },
            { Icon: IconLock, a: "Faster checkout", b: "Saved address, no retyping" },
            { Icon: IconArrowRight, a: "Early access", b: "Drops before they go public" },
          ].map(({ Icon, a, b }) => (
            <li key={a} className="flex items-start gap-3">
              <Icon className="mt-0.5 h-5 w-5 shrink-0 text-paper/70" strokeWidth={1.8} />
              <span className="text-[15px] leading-tight">
                {a}
                <br />
                <span className="text-paper/55">{b}</span>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <Link
        href="/shop"
        className="press mt-8 inline-flex h-14 items-center gap-3 rounded-[18px] bg-lime pr-5 pl-6 text-[16px] font-bold text-ink"
      >
        Back to the shop
        <IconArrowRight className="h-5 w-5" />
      </Link>
    </div>
  );
}
