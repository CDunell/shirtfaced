import { CREATURES, creatureLockup, getCreature } from "./creatures";

export type Category = "tee" | "hoodie" | "cap";

export const CATEGORY_LABEL: Record<Category, string> = {
  tee: "Tee",
  hoodie: "Hoodie",
  cap: "Cap",
};

export const CATEGORY_PRICE: Record<Category, number> = {
  tee: 34.95,
  hoodie: 64.95,
  cap: 29.95,
};

export const TODDLER_SIZES = ["2T", "3T", "4T", "5T"] as const;
export const YOUTH_SIZES = ["XS (6/7)", "S (8)", "M (10/12)", "L (14/16)", "XL (18/20)"] as const;
export const CAP_SIZES = ["Toddler", "Youth"] as const;

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
};

function sizesFor(category: Category): readonly string[] {
  if (category === "cap") return CAP_SIZES;
  // Every tee/hoodie ships in both toddler and youth runs — one product,
  // one size chart, same as how a real kids apparel SKU is usually cut.
  return [...TODDLER_SIZES, ...YOUTH_SIZES];
}

function buildProducts(): Product[] {
  const out: Product[] = [];
  for (const creature of CREATURES) {
    const colours: Colourway[] = [
      ...BASE_COLOURWAYS,
      { name: creature.accent.name, swatch: creature.accent.hex, body: creature.accent.hex },
    ];
    (["tee", "hoodie", "cap"] as const).forEach((category) => {
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
