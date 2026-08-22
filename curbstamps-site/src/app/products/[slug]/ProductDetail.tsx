"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Product } from "@/lib/products";
import { money } from "@/lib/money";
import { useCart } from "@/lib/cart-context";
import { GarmentArt } from "@/components/GarmentArt";
import { IconCheck } from "@/components/Icons";

export function ProductDetail({ product }: { product: Product }) {
  const router = useRouter();
  const [colour, setColour] = useState(product.colours[0]);
  const [size, setSize] = useState<string | null>(null);
  const [added, setAdded] = useState(false);
  const { addLine } = useCart();

  function handleAdd() {
    if (!size) return;
    addLine({
      slug: product.slug,
      name: product.name,
      price: product.price,
      size,
      colour: colour.name,
      art: product.art,
      body: colour.body,
    });
    setAdded(true);
    setTimeout(() => setAdded(false), 1600);
  }

  return (
    <div className="grid gap-8 sm:grid-cols-2 sm:gap-10">
      <GarmentArt
        category={product.category}
        bodyColour={colour.body}
        art={product.art}
        creatureName={product.name}
        className="aspect-square rounded-card"
      />

      <div>
        <h1 className="display text-[32px] leading-tight sm:text-[40px]">{product.name}</h1>
        <p className="mt-2 text-[20px] font-extrabold">{money(product.price)}</p>
        <p className="mt-3 max-w-[46ch] text-[15px] leading-relaxed text-ink/70">
          {product.description}
        </p>

        <div className="mt-6">
          <p className="text-[13px] font-bold tracking-wide text-grey-dark uppercase">Colour — {colour.name}</p>
          <div className="mt-2 flex gap-2">
            {product.colours.map((c) => (
              <button
                key={c.name}
                type="button"
                aria-label={c.name}
                aria-pressed={c.name === colour.name}
                onClick={() => setColour(c)}
                className={`press h-10 w-10 rounded-full border-2 ${
                  c.name === colour.name ? "border-ink" : "border-transparent"
                }`}
                style={{ backgroundColor: c.swatch }}
              />
            ))}
          </div>
        </div>

        <div className="mt-6">
          <p className="text-[13px] font-bold tracking-wide text-grey-dark uppercase">Size</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {product.sizes.map((s) => (
              <button
                key={s}
                type="button"
                aria-pressed={size === s}
                onClick={() => setSize(s)}
                className={`press rounded-full border-2 px-4 py-2 text-[13px] font-bold ${
                  size === s ? "border-ink bg-ink text-paper" : "border-ink/15"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          disabled={!size}
          onClick={handleAdd}
          className="press mt-8 flex h-14 w-full items-center justify-center gap-2 rounded-full bg-grit-pink text-[16px] font-extrabold text-ink disabled:opacity-40"
        >
          {added ? (
            <>
              <IconCheck className="h-5 w-5" />
              Added to cart
            </>
          ) : (
            "Add to cart"
          )}
        </button>
        {added && (
          <button
            type="button"
            onClick={() => router.push("/cart")}
            className="press mt-3 w-full text-center text-[13px] font-bold underline underline-offset-4"
          >
            View cart
          </button>
        )}
      </div>
    </div>
  );
}
