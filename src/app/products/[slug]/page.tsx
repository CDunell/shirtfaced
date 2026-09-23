import { notFound } from "next/navigation";
import Link from "next/link";
import { BuyPanel } from "@/components/BuyPanel";
import { ProductCard } from "@/components/ProductCard";
import { getProduct, products, relatedProducts } from "@/lib/products";
import { IconArrowLeft } from "@/components/Icons";

export function generateStaticParams() {
  return products.map((product) => ({ slug: product.slug }));
}

const SITE_URL = "https://shirtfaced.wtf";

export async function generateMetadata(props: PageProps<"/products/[slug]">) {
  const { slug } = await props.params;
  const product = getProduct(slug);
  if (!product) return { title: "Not found — shirtfaced" };
  return {
    title: `${product.name} — shirtfaced`,
    description: product.description,
    alternates: { canonical: `/products/${product.slug}` },
  };
}

export default async function ProductPage(props: PageProps<"/products/[slug]">) {
  const { slug } = await props.params;
  const product = getProduct(slug);

  if (!product) {
    notFound();
  }

  const related = relatedProducts(slug, 3);

  // Structured data — Product/Offer so search results can show price and
  // availability, BreadcrumbList for the Shop > Product trail. Availability
  // is a plain "does this have any size in stock" read of the same data the
  // page itself renders, not a separate claim.
  const image = product.colours.find((c) => c.images?.length)?.images?.[0];
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Product",
        name: product.name,
        description: product.description,
        ...(image && { image: `${SITE_URL}${image}` }),
        offers: {
          "@type": "Offer",
          url: `${SITE_URL}/products/${product.slug}`,
          priceCurrency: "AUD",
          price: product.price.toFixed(2),
          availability:
            product.sizes.length > 0
              ? "https://schema.org/InStock"
              : "https://schema.org/OutOfStock",
        },
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Shop", item: `${SITE_URL}/shop` },
          { "@type": "ListItem", position: 2, name: product.name, item: `${SITE_URL}/products/${product.slug}` },
        ],
      },
    ],
  };

  return (
    <div className="pb-24">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

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
      <section className="mx-auto mt-14 max-w-6xl px-4 sm:px-6">
        <h2 className="display mb-5 text-[30px]">you might like</h2>
        <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3">
          {related.map((p) => (
            <ProductCard key={p.slug} product={p} />
          ))}
        </div>
      </section>
    </div>
  );
}
