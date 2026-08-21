export type Garment = {
  /** Display name, e.g. "Washed Black" */
  name: string;
  /** Swatch colour shown in the picker */
  swatch: string;
  /** Garment body colour used by the artwork fallback renderer */
  body: string;
  /** Ink colour the design is printed in on this garment */
  ink: string;
  /**
   * Real photography for THIS colourway. A photo shows one specific garment,
   * so images live on the colour, not the product — switching colour switches
   * the gallery. Colours without shots fall back to rendered artwork.
   */
  images?: string[];
};

export type SizeKey = "S" | "M" | "L" | "XL" | "XXL";

export type Product = {
  slug: string;
  name: string;
  price: number;
  category: "tees" | "tanks" | "hoodies" | "hats" | "accessories";
  /** Artwork key — maps to a renderer in components/TeeArt.tsx */
  art: string;
  isNew?: boolean;
  colours: Garment[];
  sizes: SizeKey[];
  /** One line, dry, Australian. Never trying too hard. */
  blurb: string;
  description: string;
};

/**
 * The catalog itself comes from the admin app's database — see
 * scripts/sync-products.mjs and admin/README.md. It's regenerated before
 * every dev/build run (predev/prebuild) when SHOP_DATABASE_URL is set, and
 * falls back to the last-synced snapshot otherwise.
 */
import { products } from "./products-data.generated";
export { products };

export function getProduct(slug: string) {
  return products.find((p) => p.slug === slug);
}

/** Prefer photographed products in recommendations — they convert better. */
export function relatedProducts(slug: string, count = 3) {
  return products
    .filter((p) => p.slug !== slug)
    .sort(
      (a, b) =>
        Number(Boolean(b.colours[0].images)) -
        Number(Boolean(a.colours[0].images))
    )
    .slice(0, count);
}

export const CATEGORIES = [
  { key: "all", label: "All" },
  { key: "new", label: "New Drops" },
  { key: "tees", label: "Tees" },
  { key: "tanks", label: "Tanks" },
  { key: "hoodies", label: "Hoodies" },
  { key: "hats", label: "Hats" },
  { key: "accessories", label: "Accessories" },
] as const;

export const FREE_SHIPPING_THRESHOLD = 100;
