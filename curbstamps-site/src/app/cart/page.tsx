"use client";

import Link from "next/link";
import { useCart } from "@/lib/cart-context";
import { money } from "@/lib/money";
import { FREE_SHIPPING_THRESHOLD, categoryFromSlug } from "@/lib/products";
import { GarmentArt } from "@/components/GarmentArt";
import { IconArrowRight, IconMinus, IconPlus } from "@/components/Icons";

export default function CartPage() {
  const { lines, subtotal, setQuantity, removeLine, hydrated } = useCart();

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
        <h1 className="display text-[40px]">empty cart</h1>
        <p className="mt-3 text-[15px] text-grey-dark">Nothing in here yet.</p>
        <Link
          href="/shop"
          className="press mt-6 inline-flex h-14 items-center gap-2 rounded-full bg-ink px-6 text-[16px] font-extrabold text-paper"
        >
          Go shopping
          <IconArrowRight className="h-5 w-5" />
        </Link>
      </div>
    );
  }

  const remaining = Math.max(0, FREE_SHIPPING_THRESHOLD - subtotal);

  return (
    <div className="mx-auto max-w-2xl px-4 pt-4 pb-16 sm:px-6">
      <h1 className="display text-[13vw] leading-[0.9] sm:text-[54px]">your cart</h1>

      {remaining > 0 ? (
        <p className="mt-3 text-[13px] font-semibold text-grey-dark">
          Add {money(remaining)} more for free standard shipping.
        </p>
      ) : (
        <p className="mt-3 text-[13px] font-semibold text-grit-green">
          You&apos;ve got free standard shipping.
        </p>
      )}

      <ul className="mt-6 flex flex-col gap-4">
        {lines.map((line) => (
          <li key={`${line.slug}-${line.size}-${line.colour}`} className="flex gap-3">
            <GarmentArt
              category={categoryFromSlug(line.slug)}
              bodyColour={line.body}
              art={line.art}
              artDark={line.artDark}
              creatureName={line.name}
              className="h-20 w-20 shrink-0 rounded-2xl"
            />
            <div className="flex min-w-0 flex-1 flex-col justify-between">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-[15px] font-extrabold">{line.name}</p>
                  <p className="text-[13px] text-grey-dark">
                    {line.colour} · {line.size}
                  </p>
                </div>
                <p className="text-[15px] font-bold tabular-nums">{money(line.price * line.quantity)}</p>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 rounded-full border-2 border-ink/12 px-1">
                  <button
                    type="button"
                    aria-label="Decrease quantity"
                    onClick={() => setQuantity(line.slug, line.size, line.colour, line.quantity - 1)}
                    className="press flex h-8 w-8 items-center justify-center"
                  >
                    <IconMinus className="h-4 w-4" />
                  </button>
                  <span className="w-5 text-center text-[14px] font-bold tabular-nums">{line.quantity}</span>
                  <button
                    type="button"
                    aria-label="Increase quantity"
                    onClick={() => setQuantity(line.slug, line.size, line.colour, line.quantity + 1)}
                    className="press flex h-8 w-8 items-center justify-center"
                  >
                    <IconPlus className="h-4 w-4" />
                  </button>
                </div>
                <button
                  type="button"
                  onClick={() => removeLine(line.slug, line.size, line.colour)}
                  className="press text-[12px] font-bold text-grey-dark underline underline-offset-4"
                >
                  Remove
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-8 flex items-baseline justify-between border-t-2 border-ink/10 pt-5">
        <span className="text-[15px] font-bold text-grey-dark">Subtotal</span>
        <span className="display text-[24px]">{money(subtotal)}</span>
      </div>

      <Link
        href="/checkout"
        className="press mt-6 flex h-14 w-full items-center justify-center gap-2 rounded-full bg-grit-pink text-[16px] font-extrabold text-ink"
      >
        Checkout
        <IconArrowRight className="h-5 w-5" />
      </Link>
    </div>
  );
}
