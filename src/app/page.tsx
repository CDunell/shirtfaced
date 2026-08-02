import { ProductCard } from "@/components/ProductCard";
import { products } from "@/lib/products";

export default function Home() {
  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-12">
      <div className="mb-10">
        <h1 className="text-2xl font-black tracking-tight uppercase">
          Shirtfaced
        </h1>
        <p className="mt-1 text-black/60 dark:text-white/60">
          Get shirtfaced.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3">
        {products.map((product) => (
          <ProductCard key={product.slug} product={product} />
        ))}
      </div>
    </div>
  );
}
