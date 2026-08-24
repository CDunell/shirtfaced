import { notFound, redirect } from "next/navigation";
import Link from "next/link";
import { getProduct, withPrintifyData, designsForCategory, CATEGORY_LABEL, CREATURES, type Category } from "@/lib/products";
import { getCreature } from "@/lib/creatures";
import { ProductDetail } from "./ProductDetail";

const CATEGORIES = Object.keys(CATEGORY_LABEL) as Category[];

function isCategory(value: string): value is Category {
  return (CATEGORIES as string[]).includes(value);
}

/** Old per-creature URLs (`/products/blip-tee`) still exist in bookmarks and
 * a couple of homepage components — this recovers the creature+category
 * from that shape so they redirect instead of 404ing. */
function creatureSlugFromOldStyleSlug(slug: string, category: Category): string | null {
  const suffix = `-${category}`;
  if (!slug.endsWith(suffix)) return null;
  const creatureSlug = slug.slice(0, -suffix.length);
  return getCreature(creatureSlug) ? creatureSlug : null;
}

export function generateStaticParams() {
  return CATEGORIES.map((category) => ({ category }));
}

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<{ category: string }>;
  searchParams: Promise<{ design?: string }>;
}) {
  const { category } = await params;
  if (!isCategory(category)) return { title: "Curb Stamps" };
  const { design } = await searchParams;
  const creatureSlug = design && getCreature(design) ? design : CREATURES[0].slug;
  const product = getProduct(`${creatureSlug}-${category}`);
  return { title: product ? `${product.name} — Curb Stamps` : "Curb Stamps" };
}

export default async function CategoryProductPage({
  params,
  searchParams,
}: {
  params: Promise<{ category: string }>;
  searchParams: Promise<{ design?: string }>;
}) {
  const { category: rawCategory } = await params;

  if (!isCategory(rawCategory)) {
    // Might be an old `${creature}-${category}` bookmark — try every real
    // category before giving up and 404ing.
    for (const category of CATEGORIES) {
      const creatureSlug = creatureSlugFromOldStyleSlug(rawCategory, category);
      if (creatureSlug) redirect(`/products/${category}?design=${creatureSlug}`);
    }
    notFound();
  }
  const category = rawCategory;

  const { design } = await searchParams;
  const creatureSlug = design && getCreature(design) ? design : CREATURES[0].slug;

  const rawProduct = getProduct(`${creatureSlug}-${category}`);
  if (!rawProduct) notFound();
  const creature = getCreature(creatureSlug)!;
  const [product, designs] = await Promise.all([
    withPrintifyData(rawProduct),
    designsForCategory(category),
  ]);

  return (
    <div className="mx-auto max-w-5xl px-4 pt-4 pb-16 sm:px-6">
      <ProductDetail product={product} category={category} activeCreatureSlug={creatureSlug} designs={designs} />

      <div className="mt-14 rounded-card border-2 border-ink/10 bg-paper-2/60 p-6">
        <p className="display text-[20px]">
          meet {creature.name} the {creature.animal}
        </p>
        <p className="mt-1 max-w-[52ch] text-[14px] text-ink/70">{creature.blurb}</p>
      </div>

      <Link href="/shop" className="press mt-10 inline-block text-[13px] font-bold text-grey-dark">
        ← Back to shop
      </Link>
    </div>
  );
}
