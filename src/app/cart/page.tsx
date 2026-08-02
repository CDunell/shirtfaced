"use client";

import Link from "next/link";
import { useCart } from "@/lib/cart-context";

export default function CartPage() {
  const { lines, removeLine, setQuantity, subtotal } = useCart();

  if (lines.length === 0) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col items-center gap-4 px-6 py-24 text-center">
        <p className="text-lg font-medium">Your cart is empty.</p>
        <Link href="/" className="underline underline-offset-4">
          Back to shop
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-12">
      <h1 className="mb-8 text-2xl font-bold">Cart</h1>
      <div className="flex flex-col gap-6">
        {lines.map((line) => (
          <div
            key={`${line.slug}-${line.size}`}
            className="flex items-center justify-between border-b border-black/10 pb-6 dark:border-white/10"
          >
            <div>
              <p className="font-medium">{line.name}</p>
              <p className="text-sm text-black/60 dark:text-white/60">
                Size {line.size} &middot; ${line.price}
              </p>
              <button
                type="button"
                onClick={() => removeLine(line.slug, line.size)}
                className="mt-1 text-xs underline underline-offset-4"
              >
                Remove
              </button>
            </div>
            <input
              type="number"
              min={1}
              value={line.quantity}
              onChange={(e) =>
                setQuantity(line.slug, line.size, Number(e.target.value))
              }
              className="w-16 rounded-md border border-black/20 px-2 py-1 text-center dark:border-white/20"
            />
          </div>
        ))}
      </div>
      <div className="mt-8 flex items-center justify-between">
        <p className="text-lg font-semibold">Subtotal: ${subtotal}</p>
        <button
          type="button"
          disabled
          title="Checkout isn't wired up yet"
          className="cursor-not-allowed rounded-md bg-black/40 px-5 py-3 text-sm font-semibold text-white dark:bg-white/40 dark:text-black"
        >
          Checkout (coming soon)
        </button>
      </div>
    </div>
  );
}
