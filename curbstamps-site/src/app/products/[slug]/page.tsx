import { notFound } from "next/navigation";
import Link from "next/link";
import { getProduct, relatedProducts, products } from "@/lib/products";
import { getCreature } from "@/lib/creatures";
import { ProductCard } from "@/components/ProductCard";
import { ProductDetail } from "./ProductDetail";

export function generateStaticParams() {
  return products.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = getProduct(slug);
  return { title: product ? `${product.name} — Curb Stamps` : "Curb Stamps" };
}

export default async function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = getProduct(slug);
  if (!product) notFound();
  const creature = getCreature(product.creature);
  const related = relatedProducts(slug);

  return (
    <div className="mx-auto max-w-5xl px-4 pt-4 pb-16 sm:px-6">
      <ProductDetail product={product} />

      {creature && (
        <div className="mt-14 rounded-card border-2 border-ink/10 bg-paper-2/60 p-6">
          <p className="display text-[20px]">
            meet {creature.name} the {creature.animal}
          </p>
          <p className="mt-1 max-w-[52ch] text-[14px] text-ink/70">{creature.blurb}</p>
        </div>
      )}

      {related.length > 0 && (
        <div className="mt-14">
          <h2 className="display text-[22px]">more from the crew</h2>
          <div className="mt-5 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-4">
            {related.map((p) => (
              <ProductCard key={p.slug} product={p} />
            ))}
          </div>
        </div>
      )}

      <Link href="/shop" className="press mt-10 inline-block text-[13px] font-bold text-grey-dark">
        ← Back to shop
      </Link>
    </div>
  );
}
