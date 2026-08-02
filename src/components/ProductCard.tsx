"use client";

import Link from "next/link";
import { useState } from "react";
import { useCart } from "@/lib/cart-context";
import { money } from "@/lib/money";
import type { Product } from "@/lib/products";
import { ProductMedia } from "./ProductMedia";
import { IconCheck, IconHeart, IconPlus } from "./Icons";

/** Large imagery, minimal chrome: price, name, favourite, quick add. Nothing else. */
export function ProductCard({
  product,
  priority = false,
}: {
  product: Product;
  priority?: boolean;
}) {
  const { addLine } = useCart();
  const [fav, setFav] = useState(false);
  const [added, setAdded] = useState(false);
  const garment = product.colours[0];

  // Quick add takes the middle size — the common case, one tap, no dialog.
  const quickAdd = () => {
    const size = product.sizes[Math.floor(product.sizes.length / 2)];
    addLine({
      slug: product.slug,
      name: product.name,
      price: product.price,
      size,
      colour: garment.name,
      art: product.art,
      body: garment.body,
      ink: garment.ink,
    });
    setAdded(true);
    setTimeout(() => setAdded(false), 1400);
  };

  return (
    <div className="group flex flex-col">
      <div className="relative">
        <Link
          href={`/products/${product.slug}`}
          className="block overflow-hidden rounded-[20px] bg-paper-2"
          aria-label={product.name}
        >
          <div className="relative aspect-[4/5]">
            <ProductMedia
              product={product}
              garment={garment}
              priority={priority}
              className="transition-transform duration-[240ms] ease-[cubic-bezier(0.22,0.61,0.36,1)] group-hover:scale-[1.03]"
            />
          </div>
        </Link>

        {product.isNew && (
          <span className="pointer-events-none absolute top-3 left-3 rounded-[10px] bg-lime px-2.5 py-1 text-[11px] font-bold tracking-wide text-ink uppercase">
            New
          </span>
        )}

        <button
          type="button"
          onClick={() => setFav((f) => !f)}
          aria-label={
            fav ? `Remove ${product.name} from favourites` : `Save ${product.name}`
          }
          aria-pressed={fav}
          className="press absolute top-1.5 right-1.5 grid h-11 w-11 place-items-center rounded-full text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.45)]"
        >
          <IconHeart
            className={`h-[22px] w-[22px] transition-transform duration-200 ${
              fav ? "scale-110 text-coral" : ""
            }`}
            filled={fav}
          />
        </button>
      </div>

      <div className="mt-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link href={`/products/${product.slug}`}>
            <h3 className="display text-[17px] leading-tight">{product.name}</h3>
          </Link>
          <p className="mt-1 text-[15px] font-medium tabular-nums">
            {money(product.price)}
          </p>
        </div>

        <button
          type="button"
          onClick={quickAdd}
          aria-label={`Quick add ${product.name}`}
          className={`press grid h-11 w-11 shrink-0 place-items-center rounded-full ${
            added ? "bg-lime text-ink" : "bg-ink text-paper"
          }`}
        >
          {added ? (
            <IconCheck className="h-5 w-5" />
          ) : (
            <IconPlus className="h-5 w-5" />
          )}
        </button>
      </div>
    </div>
  );
}
