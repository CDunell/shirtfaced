"use client";

import Link from "next/link";
import { useCart, money } from "@/lib/cart-context";
import { FREE_SHIPPING_THRESHOLD, products } from "@/lib/products";
import { ProductCard } from "@/components/ProductCard";
import { TeeArt } from "@/components/TeeArt";
import { ProductMedia } from "@/components/ProductMedia";
import {
  IconArrowRight,
  IconLock,
  IconMinus,
  IconPlus,
  IconTrash,
  IconTruck,
} from "@/components/Icons";

const SHIPPING = 10;

export default function CartPage() {
  const { lines, removeLine, setQuantity, subtotal, hydrated } = useCart();

  if (!hydrated) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
        <div className="skeleton h-16 rounded-[20px]" />
        <div className="skeleton mt-4 h-28 rounded-[20px]" />
        <div className="skeleton mt-3 h-28 rounded-[20px]" />
      </div>
    );
  }

  /* Empty states are never dead ends. */
  if (lines.length === 0) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
        <h1 className="display distressed text-[42px] leading-none">
          cart&apos;s empty
        </h1>
        <p className="mt-3 max-w-[38ch] text-[15px] text-grey-dark">
          Bold restraint. Admirable, even. These are the ones people usually
          cave on.
        </p>
        <Link
          href="/shop"
          className="press mt-6 inline-flex h-14 items-center gap-3 rounded-[18px] bg-ink pr-5 pl-6 text-[16px] font-bold text-paper"
        >
          Start the damage
          <IconArrowRight className="h-5 w-5" />
        </Link>

        <div className="mt-12 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3">
          {products.slice(0, 4).map((p) => (
            <ProductCard key={p.slug} product={p} />
          ))}
        </div>
      </div>
    );
  }

  const remaining = Math.max(0, FREE_SHIPPING_THRESHOLD - subtotal);
  const freeShipping = remaining === 0;
  const shipping = freeShipping ? 0 : SHIPPING;
  const pct = Math.min(100, (subtotal / FREE_SHIPPING_THRESHOLD) * 100);

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 sm:px-6">
      <h1 className="display distressed text-[38px] leading-none">
        cart{" "}
        <span className="text-grey tabular-nums">
          ({lines.reduce((n, l) => n + l.quantity, 0)})
        </span>
      </h1>

      {/* Shipping progress */}
      <div className="mt-5 rounded-[20px] bg-ink px-4 py-4 text-paper">
        <p className="flex items-center gap-2 text-[14px]">
          <IconTruck className="h-5 w-5 shrink-0 text-lime" strokeWidth={1.8} />
          {freeShipping ? (
            <span>
              Nice. <span className="font-bold text-lime">Free shipping</span>{" "}
              unlocked.
            </span>
          ) : (
            <span>
              You&apos;re{" "}
              <span className="font-bold text-lime tabular-nums">
                {money(remaining)}
              </span>{" "}
              away from free shipping.
            </span>
          )}
        </p>
        <div
          className="mt-3 h-2 overflow-hidden rounded-full bg-paper/15"
          role="progressbar"
          aria-valuenow={Math.round(pct)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Progress towards free shipping"
        >
          <div
            className="h-full rounded-full bg-lime transition-[width] duration-[240ms] ease-[cubic-bezier(0.22,0.61,0.36,1)]"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Lines */}
      <ul className="mt-5 flex flex-col gap-3">
        {lines.map((line) => {
          const garment = {
            name: line.colour,
            swatch: line.body,
            body: line.body,
            ink: line.ink,
          };
          const product = products.find((p) => p.slug === line.slug);
          return (
            <li
              key={`${line.slug}-${line.size}-${line.colour}`}
              className="fade-rise flex gap-3 rounded-[20px] border border-ink/10 p-3"
            >
              <Link
                href={`/products/${line.slug}`}
                className="relative h-[104px] w-[84px] shrink-0 overflow-hidden rounded-[14px] bg-paper-2"
              >
                {product ? (
                  <ProductMedia
                    product={product}
                    garment={
                      product.colours.find((c) => c.name === line.colour) ??
                      product.colours[0]
                    }
                    sizes="84px"
                  />
                ) : (
                  <TeeArt art={line.art} garment={garment} className="h-full w-full" />
                )}
              </Link>

              <div className="flex min-w-0 flex-1 flex-col">
                <div className="flex items-start justify-between gap-2">
                  <Link href={`/products/${line.slug}`} className="min-w-0">
                    <h2 className="display text-[16px] leading-tight">
                      {line.name}
                    </h2>
                    <p className="mt-1 text-[12px] tracking-wide text-grey-dark uppercase">
                      {line.colour} · Size {line.size}
                    </p>
                  </Link>
                  <button
                    type="button"
                    onClick={() =>
                      removeLine(line.slug, line.size, line.colour)
                    }
                    aria-label={`Remove ${line.name}`}
                    className="press -mt-1 -mr-1 grid h-11 w-11 shrink-0 place-items-center rounded-[14px] text-grey-dark"
                  >
                    <IconTrash className="h-5 w-5" />
                  </button>
                </div>

                <div className="mt-auto flex items-center justify-between pt-2">
                  <div className="flex items-center gap-1 rounded-full border border-ink/15">
                    <button
                      type="button"
                      onClick={() =>
                        setQuantity(
                          line.slug,
                          line.size,
                          line.colour,
                          line.quantity - 1
                        )
                      }
                      aria-label={`Decrease quantity of ${line.name}`}
                      className="press grid h-11 w-11 place-items-center rounded-full"
                    >
                      <IconMinus className="h-4 w-4" />
                    </button>
                    <span className="w-6 text-center text-[15px] font-semibold tabular-nums">
                      {line.quantity}
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        setQuantity(
                          line.slug,
                          line.size,
                          line.colour,
                          line.quantity + 1
                        )
                      }
                      aria-label={`Increase quantity of ${line.name}`}
                      className="press grid h-11 w-11 place-items-center rounded-full"
                    >
                      <IconPlus className="h-4 w-4" />
                    </button>
                  </div>
                  <p className="text-[16px] font-semibold tabular-nums">
                    {money(line.price * line.quantity)}
                  </p>
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {/* Totals */}
      <dl className="mt-6 flex flex-col gap-2 border-t border-ink/10 pt-5 text-[15px]">
        <div className="flex justify-between">
          <dt className="text-grey-dark">Subtotal</dt>
          <dd className="font-semibold tabular-nums">{money(subtotal)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-grey-dark">Shipping</dt>
          <dd className="font-semibold tabular-nums">
            {freeShipping ? (
              <span className="text-lime-700">Free</span>
            ) : (
              money(shipping)
            )}
          </dd>
        </div>
        <div className="mt-2 flex items-baseline justify-between border-t border-ink/10 pt-3">
          <dt className="display text-[20px]">Est. total</dt>
          <dd className="display text-[24px] tabular-nums">
            {money(subtotal + shipping)}{" "}
            <span className="text-[13px] text-grey-dark">AUD</span>
          </dd>
        </div>
      </dl>

      {/* Checkout — express first, per the spec */}
      <div className="mt-6 flex flex-col gap-2">
        <button
          type="button"
          disabled
          title="Payment isn't wired up yet"
          className="press flex h-14 cursor-not-allowed items-center justify-center gap-2 rounded-[18px] bg-lime text-[16px] font-bold text-ink opacity-60"
        >
          <IconLock className="h-5 w-5" />
          Checkout
        </button>
        <p className="text-center text-[13px] text-grey-dark">
          Payment isn&apos;t connected yet — nothing will be charged.
        </p>
      </div>
    </div>
  );
}
