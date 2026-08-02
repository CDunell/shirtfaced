import Image from "next/image";
import type { Garment, Product } from "@/lib/products";
import { TeeArt } from "./TeeArt";

/* ---------------------------------------------------------------------------
   ProductMedia — the single seam between photography and fallback artwork.

   Photos live on the colourway (a shot shows one specific garment), so
   switching colour switches the gallery. Colours without photography render
   their printed design via TeeArt instead. Cards, galleries and cart
   thumbnails all go through here, so adding a shot is a data change only.
--------------------------------------------------------------------------- */

export function ProductMedia({
  product,
  garment,
  index = 0,
  className = "",
  sizes = "(max-width: 640px) 50vw, 400px",
  priority = false,
}: {
  product: Pick<Product, "art" | "name">;
  garment: Garment;
  /** Which shot in the gallery — ignored when falling back to artwork */
  index?: number;
  className?: string;
  sizes?: string;
  priority?: boolean;
}) {
  const src = garment.images?.[index];

  if (src) {
    return (
      <Image
        src={src}
        alt={`${product.name} in ${garment.name}`}
        fill
        sizes={sizes}
        priority={priority}
        loading={priority ? undefined : "lazy"}
        className={`object-cover ${className}`}
      />
    );
  }

  return (
    <TeeArt
      art={product.art}
      garment={garment}
      className={`h-full w-full object-cover ${className}`}
    />
  );
}

/** How many gallery frames this colourway has. Artwork counts as one. */
export function mediaCount(garment: Garment) {
  return garment.images?.length ?? 1;
}
