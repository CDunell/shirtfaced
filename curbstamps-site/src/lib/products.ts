import { CREATURES, creatureLockup, getCreature } from "./creatures";
import { getPrintifyProductData, type PrintifyCategory } from "./printify";

export type Category = PrintifyCategory;

export const CATEGORY_LABEL: Record<Category, string> = {
  tee: "Tee",
  hoodie: "Hoodie",
  crewneck: "Crewneck",
  "bucket-hat": "Bucket Hat",
};

export const CATEGORY_PRICE: Record<Category, number> = {
  tee: 34.95,
  hoodie: 64.95,
  crewneck: 44.95,
  "bucket-hat": 29.95,
};

export const TODDLER_SIZES = ["2T", "3T", "4T", "5T"] as const;
export const YOUTH_SIZES = ["XS (6/7)", "S (8)", "M (10/12)", "L (14/16)", "XL (18/20)"] as const;
export const ONE_SIZE = ["One size"] as const;

export type Colourway = {
  name: string;
  /** Swatch shown in the picker */
  swatch: string;
  /** Garment body colour used by GarmentArt */
  body: string;
};

const BASE_COLOURWAYS: Colourway[] = [
  { name: "Jet Black", swatch: "#1c1a17", body: "#1c1a17" },
  { name: "Natural", swatch: "#f1e9d8", body: "#f1e9d8" },
];

export type Product = {
  slug: string;
  creature: string;
  category: Category;
  name: string;
  price: number;
  /** Cream-ink line art — reads on mid-to-dark garment colours. */
  art: string;
  /** Same artwork, ink-coloured — reads on light garment colours (Natural,
   * and light accents like Butter/Powder/Lilac/Sand). GarmentArt picks
   * between the two by the chosen colourway's actual brightness rather than
   * by colour name, since "light enough to need dark ink" isn't only true
   * of Natural. */
  artDark: string;
  colours: Colourway[];
  sizes: readonly string[];
  blurb: string;
  description: string;
  /** Real Printify garment mockup, keyed by colourway name — only set once
   * live data has been merged in via withPrintifyData(). Falls back to the
   * GarmentArt SVG stand-in where absent (colour not built yet, or the
   * Printify fetch failed/is unconfigured). */
  photos?: Record<string, string>;
};

function sizesFor(category: Category): readonly string[] {
  if (category === "bucket-hat") return ONE_SIZE;
  // Every tee/hoodie/crewneck ships in both toddler and youth runs — one
  // product, one size chart, same as how a real kids apparel SKU is usually
  // cut.
  return [...TODDLER_SIZES, ...YOUTH_SIZES];
}

function buildProducts(): Product[] {
  const out: Product[] = [];
  for (const creature of CREATURES) {
    const colours: Colourway[] = [
      ...BASE_COLOURWAYS,
      { name: creature.accent.name, swatch: creature.accent.hex, body: creature.accent.hex },
    ];
    (["tee", "hoodie", "crewneck", "bucket-hat"] as const).forEach((category) => {
      out.push({
        slug: `${creature.slug}-${category}`,
        creature: creature.slug,
        category,
        name: `${creature.name} ${CATEGORY_LABEL[category]}`,
        price: CATEGORY_PRICE[category],
        art: creatureLockup(creature.slug, "light"),
        artDark: creatureLockup(creature.slug, "dark"),
        colours,
        sizes: sizesFor(category),
        blurb: creature.blurb,
        description: `${creature.name} the ${creature.animal}, stamped on a ${CATEGORY_LABEL[category].toLowerCase()} kids will actually wear twice. Curb Stamps prints run small and thick — screen-printed line art that survives the wash, the yard and the second kid it gets handed down to.`,
      });
    });
  }
  return out;
}

export const products: Product[] = buildProducts();

export function getProduct(slug: string) {
  return products.find((p) => p.slug === slug);
}

/** Cart/checkout lines only store the product slug, not its category — this
 * recovers it from the `${creature}-${category}` slug shape buildProducts()
 * uses, for picking the right GarmentArt stand-in shape. */
export function categoryFromSlug(slug: string): Category {
  if (slug.endsWith("bucket-hat")) return "bucket-hat";
  if (slug.endsWith("crewneck")) return "crewneck";
  if (slug.endsWith("hoodie")) return "hoodie";
  return "tee";
}

/** Overlays live Printify data (real colours, sizes, price, mockup photos)
 * onto a product where the creature has a built Printify catalog entry for
 * that category. Any category/creature combo not yet built, or a fetch
 * failure, passes through unchanged — still the honest GarmentArt stand-in. */
export async function withPrintifyData(product: Product): Promise<Product> {
  const live = await getPrintifyProductData(product.category, product.creature);
  if (!live || live.colours.length === 0) return product;

  const photos: Record<string, string> = {};
  const colours: Colourway[] = live.colours.map((c) => {
    if (c.image) photos[c.name] = c.image;
    return { name: c.name, swatch: c.hex, body: c.hex };
  });
  const SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"];
  const sizeTitles = Array.from(new Set(live.colours.flatMap((c) => c.sizes.map((s) => s.title)))).sort(
    (a, b) => SIZE_ORDER.indexOf(a) - SIZE_ORDER.indexOf(b)
  );

  return {
    ...product,
    price: live.price || product.price,
    colours,
    sizes: sizeTitles.length > 0 ? sizeTitles : product.sizes,
    photos,
  };
}

export function productsForCreature(slug: string) {
  return products.filter((p) => p.creature === slug);
}

export function relatedProducts(slug: string, count = 4) {
  const current = getProduct(slug);
  return products
    .filter((p) => p.slug !== slug && p.creature !== current?.creature)
    .slice(0, count);
}

export { CREATURES, getCreature };

export const FREE_SHIPPING_THRESHOLD = 60;
