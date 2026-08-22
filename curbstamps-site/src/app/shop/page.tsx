import { products, CATEGORY_LABEL, type Category } from "@/lib/products";
import { ProductCard } from "@/components/ProductCard";
import { ShopFilters } from "./ShopFilters";

export const metadata = { title: "Shop — Curb Stamps" };

export default async function ShopPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string }>;
}) {
  const { category } = await searchParams;
  const active = category && category in CATEGORY_LABEL ? (category as Category) : "all";
  const list = active === "all" ? products : products.filter((p) => p.category === active);

  return (
    <div className="mx-auto max-w-5xl px-4 pt-4 pb-16 sm:px-6">
      <h1 className="display text-[13vw] leading-[0.9] sm:text-[54px]">shop</h1>
      <p className="mt-3 max-w-[46ch] text-[15px] text-ink/70">
        {products.length} products across 12 creatures. Every creature comes as a tee, a
        hoodie and a cap.
      </p>

      <ShopFilters active={active} />

      <div className="mt-6 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 md:grid-cols-4">
        {list.map((p) => (
          <ProductCard key={p.slug} product={p} />
        ))}
      </div>
    </div>
  );
}
