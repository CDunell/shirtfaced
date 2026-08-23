import { products, CATEGORY_LABEL, type Category } from "@/lib/products";
import { CREATURES } from "@/lib/creatures";
import { ProductCard } from "@/components/ProductCard";
import { ShopFilters } from "./ShopFilters";

export const metadata = { title: "Shop — Curb Stamps" };

export default async function ShopPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string; creature?: string }>;
}) {
  const { category, creature } = await searchParams;
  const active = category && category in CATEGORY_LABEL ? (category as Category) : "all";
  const activeCreature = creature ? CREATURES.find((item) => item.slug === creature) : undefined;
  const list = products.filter((product) => {
    const categoryMatches = active === "all" || product.category === active;
    const creatureMatches = !activeCreature || product.creature === activeCreature.slug;
    return categoryMatches && creatureMatches;
  });

  return (
    <div className="mx-auto max-w-5xl px-4 pt-4 pb-16 sm:px-6">
      <h1 className="display text-[13vw] leading-[0.9] sm:text-[54px]">{activeCreature ? `${activeCreature.name}'s range` : "shop"}</h1>
      <p className="mt-3 max-w-[46ch] text-[15px] text-ink/70">
        {activeCreature ? `${activeCreature.blurb} Find them on a tee, hoodie and cap.` : `${products.length} products across ${CREATURES.length} creatures. Every creature comes as a tee, a hoodie and a cap.`}
      </p>

      <ShopFilters active={active} creature={activeCreature?.slug} />

      <div className="mt-6 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 md:grid-cols-4">
        {list.map((p) => (
          <ProductCard key={p.slug} product={p} />
        ))}
      </div>
    </div>
  );
}
