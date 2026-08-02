import { notFound } from "next/navigation";
import { AddToCartForm } from "@/components/AddToCartForm";
import { getProduct, products } from "@/lib/products";

export function generateStaticParams() {
  return products.map((product) => ({ slug: product.slug }));
}

export default async function ProductPage(props: PageProps<"/products/[slug]">) {
  const { slug } = await props.params;
  const product = getProduct(slug);

  if (!product) {
    notFound();
  }

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-10 px-6 py-12 sm:grid-cols-2">
      <div
        className="flex aspect-square items-center justify-center rounded-lg border border-black/10 text-lg font-semibold uppercase tracking-wide text-white/80 dark:border-white/10"
        style={{ backgroundColor: product.swatch }}
      >
        Shirtfaced
      </div>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold">{product.name}</h1>
          <p className="mt-1 text-lg">${product.price}</p>
        </div>
        <p className="text-black/70 dark:text-white/70">
          {product.description}
        </p>
        <AddToCartForm product={product} />
      </div>
    </div>
  );
}
