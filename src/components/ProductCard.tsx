import Link from "next/link";
import type { Product } from "@/lib/products";

export function ProductCard({ product }: { product: Product }) {
  return (
    <Link
      href={`/products/${product.slug}`}
      className="group flex flex-col gap-3"
    >
      <div
        className="flex aspect-square items-center justify-center rounded-lg border border-black/10 text-sm font-semibold uppercase tracking-wide text-white/80 transition group-hover:opacity-90 dark:border-white/10"
        style={{ backgroundColor: product.swatch }}
      >
        Shirtfaced
      </div>
      <div>
        <p className="font-medium">{product.name}</p>
        <p className="text-sm text-black/60 dark:text-white/60">
          ${product.price}
        </p>
      </div>
    </Link>
  );
}
