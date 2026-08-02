import { notFound } from "next/navigation";
import Link from "next/link";
import { BuyPanel } from "@/components/BuyPanel";
import { ProductCard } from "@/components/ProductCard";
import { getProduct, products, relatedProducts } from "@/lib/products";
import { IconArrowLeft } from "@/components/Icons";

export function generateStaticParams() {
  return products.map((product) => ({ slug: product.slug }));
}

export async function generateMetadata(props: PageProps<"/products/[slug]">) {
  const { slug } = await props.params;
  const product = getProduct(slug);
  if (!product) return { title: "Not found — Shirtfaced" };
  return {
    title: `${product.name} — Shirtfaced`,
    description: product.description,
  };
}

export default async function ProductPage(props: PageProps<"/products/[slug]">) {
  const { slug } = await props.params;
  const product = getProduct(slug);

  if (!product) {
    notFound();
  }

  const related = relatedProducts(slug, 3);

  return (
    <div className="pb-24">
      <div className="mx-auto max-w-2xl px-4 pt-4 pb-2 sm:px-6">
        <Link
          href="/shop"
          className="press -ml-2 inline-flex h-11 items-center gap-2 rounded-[14px] px-2 text-[13px] font-semibold tracking-wide uppercase"
        >
          <IconArrowLeft className="h-4 w-4" />
          Shop
        </Link>
      </div>

      <BuyPanel product={product} />

      {/* Recommendations — never a dead end */}
      <section className="mx-auto mt-14 max-w-5xl px-4 sm:px-6">
        <h2 className="display distressed mb-5 text-[30px]">you might like</h2>
        <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3">
          {related.map((p) => (
            <ProductCard key={p.slug} product={p} />
          ))}
        </div>
      </section>
    </div>
  );
}
