import Link from "next/link";
import type { Product } from "@/lib/products";
import { money } from "@/lib/money";
import { GarmentArt } from "./GarmentArt";

export function ProductCard({ product }: { product: Product }) {
  const colour = product.colours[0];
  return (
    <Link href={`/products/${product.slug}`} className="press group block">
      <GarmentArt
        category={product.category}
        bodyColour={colour.body}
        art={product.art}
        artDark={product.artDark}
        creatureName={product.name}
        photoSrc={product.photos?.[colour.name]}
        className="aspect-square rounded-card"
      />
      <p className="mt-3 text-[15px] font-extrabold">{product.name}</p>
      <p className="text-[13px] text-grey-dark">{product.blurb}</p>
      <p className="mt-1 text-[14px] font-bold">{money(product.price)}</p>
    </Link>
  );
}
