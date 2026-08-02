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

export const SIZE_CHART: Record<SizeKey, { chest: string; length: string }> = {
  S: { chest: "48–50cm", length: "68cm" },
  M: { chest: "51–53cm", length: "72cm" },
  L: { chest: "54–56cm", length: "75cm" },
  XL: { chest: "57–59cm", length: "78cm" },
  XXL: { chest: "60–62cm", length: "81cm" },
};

const WASHED_BLACK: Garment = {
  name: "Washed Black",
  swatch: "#1c1c1a",
  body: "#1c1c1a",
  ink: "#e8e2d5",
};
const VINTAGE_WHITE: Garment = {
  name: "Vintage White",
  swatch: "#e8e2d5",
  body: "#e8e2d5",
  ink: "#1c1c1a",
};
const FADED_OLIVE: Garment = {
  name: "Faded Olive",
  swatch: "#4a4a3e",
  body: "#4a4a3e",
  ink: "#e8e2d5",
};

const ALL_SIZES: SizeKey[] = ["S", "M", "L", "XL", "XXL"];

/* Photographed products lead the store. Artwork-only ones follow until their
   shots land — drop a file in public/products, run scripts/optimise-images.mjs,
   and add the path to the relevant colourway below. */
export const products: Product[] = [
  {
    slug: "good-times-bad-decisions-tee",
    name: "Good Times Bad Decisions Tee",
    price: 49.95,
    category: "tees",
    art: "no-regrets",
    isNew: true,
    colours: [
      { ...WASHED_BLACK, images: ["/products/good-times-1.webp"] },
      VINTAGE_WHITE,
    ],
    sizes: ALL_SIZES,
    blurb: "The house tee.",
    description:
      "Heavyweight combed cotton, boxy oversized fit, distressed cream back print. Washed black that stays black. The one everything else is judged against.",
  },
  {
    slug: "roll-the-dice-tee",
    name: "Roll The Dice Tee",
    price: 49.95,
    category: "tees",
    art: "bad-influence",
    isNew: true,
    colours: [
      { ...WASHED_BLACK, images: ["/products/roll-the-dice-1.webp"] },
      FADED_OLIVE,
    ],
    sizes: ALL_SIZES,
    blurb: "Take the risk. Obviously.",
    description:
      "Eight-ball back print on 240gsm washed black. Dropped shoulder, wide body, vintage screen texture. Ships with no advice whatsoever.",
  },
  {
    slug: "send-it-club-tee",
    name: "Send It Club Tee",
    price: 49.95,
    category: "tees",
    art: "send-it",
    isNew: true,
    colours: [
      {
        ...VINTAGE_WHITE,
        images: ["/products/send-it-2.webp", "/products/send-it-1.webp"],
      },
      WASHED_BLACK,
    ],
    sizes: ALL_SIZES,
    blurb: "Life's short. Send it long.",
    description:
      "Garment-dyed and stone-washed so it turns up already broken in. Oversized cut, dropped shoulder, full back print with the club crest.",
  },
  {
    slug: "cold-beer-warm-nights-tee",
    name: "Cold Beer Warm Nights Tee",
    price: 49.95,
    category: "tees",
    art: "cold-beer",
    isNew: true,
    colours: [
      { ...WASHED_BLACK, images: ["/products/cold-beer-1.webp"] },
      VINTAGE_WHITE,
    ],
    sizes: ALL_SIZES,
    blurb: "Summer's whole personality.",
    description:
      "230gsm mid-weight cotton with a full back print in washed blue ink. Regular fit, ribbed neck, built for long evenings and worse ideas.",
  },
  {
    slug: "midnight-service-tee",
    name: "Midnight Service Tee",
    price: 54.95,
    category: "tees",
    art: "bad-influence",
    isNew: true,
    colours: [
      { ...WASHED_BLACK, images: ["/products/midnight-service.webp"] },
    ],
    sizes: ALL_SIZES,
    blurb: "Speed shop. Built for nowhere.",
    description:
      "Vintage moto back print on heavyweight washed black. Boxy fit, dropped shoulder, cracked-ink finish straight out of the bag.",
  },
  {
    slug: "take-your-chances-tee",
    name: "Take Your Chances Tee",
    price: 49.95,
    category: "tees",
    art: "bad-influence",
    isNew: true,
    colours: [
      { ...VINTAGE_WHITE, images: ["/products/take-your-chances.webp"] },
    ],
    sizes: ALL_SIZES,
    blurb: "Don't look back.",
    description:
      "Flaming dice back print on vintage white. Garment-dyed, oversized, soft as anything. For people who already decided.",
  },
  {
    slug: "love-fast-die-last-tee",
    name: "Love Fast Die Last Tee",
    price: 49.95,
    category: "tees",
    art: "no-regrets",
    isNew: true,
    colours: [
      { ...WASHED_BLACK, images: ["/products/love-fast-die-last.webp"] },
    ],
    sizes: ALL_SIZES,
    blurb: "Panther energy.",
    description:
      "Arched type and big cat back print on washed black. Mid-weight, regular fit, quietly the best thing in the drop.",
  },
  {
    slug: "eight-ball-tee",
    name: "Eight Ball Tee",
    price: 44.95,
    category: "tees",
    art: "bad-influence",
    colours: [{ ...WASHED_BLACK, images: ["/products/eight-ball.webp"] }],
    sizes: ALL_SIZES,
    blurb: "Small print. Big call.",
    description:
      "Flaming eight-ball chest print, nothing on the back. Heavyweight cotton, boxy fit, for when you want it understated.",
  },
  {
    slug: "not-yours-tee",
    name: "Not Yours Tee",
    price: 49.95,
    category: "tees",
    art: "no-regrets",
    isNew: true,
    colours: [{ ...VINTAGE_WHITE, images: ["/products/not-yours.webp"] }],
    sizes: ALL_SIZES,
    blurb: "Never was, either.",
    description:
      "Barbed-heart back print on stone-washed vintage white. Oversized cut, raw-edge feel, says the thing so you don't have to.",
  },
  {
    slug: "spin-cycle-tee",
    name: "Spin Cycle Tee",
    price: 49.95,
    category: "tees",
    art: "offline",
    colours: [{ ...WASHED_BLACK, images: ["/products/spin-cycle.webp"] }],
    sizes: ALL_SIZES,
    blurb: "Worldwide. Allegedly.",
    description:
      "Globe-and-arch back print on faded black. Mid-weight, relaxed drape, holds up to a lot of washing.",
  },
  {
    slug: "permanent-tee",
    name: "Permanent Tee",
    price: 54.95,
    category: "tees",
    art: "bad-influence",
    colours: [{ ...WASHED_BLACK, images: ["/products/permanent.webp"] }],
    sizes: ALL_SIZES,
    blurb: "Bad idea. Permanent record.",
    description:
      "Full-colour back print on heavyweight black. Boxy oversized fit. The loudest thing we make and we're not sorry.",
  },
  {
    slug: "built-different-tee",
    name: "Built Different Tee",
    price: 49.95,
    category: "tees",
    art: "handle-with-care",
    isNew: true,
    colours: [{ ...VINTAGE_WHITE, images: ["/products/built-different.webp"] }],
    sizes: ALL_SIZES,
    blurb: "Break regularly.",
    description:
      "Crossed-spanner back print on vintage white. Garment-dyed, oversized, built to be worn badly and often.",
  },
  {
    slug: "no-regrets-tee",
    name: "No Regrets Tee",
    price: 49.95,
    category: "tees",
    art: "no-regrets",
    colours: [WASHED_BLACK, VINTAGE_WHITE, FADED_OLIVE],
    sizes: ALL_SIZES,
    blurb: "No regrets, just stories.",
    description:
      "Heavyweight combed cotton with a boxy, lived-in fit. Back print, soft hand feel, gets better every wash.",
  },
  {
    slug: "handle-with-care-tee",
    name: "Handle With Care Tee",
    price: 49.95,
    category: "tees",
    art: "handle-with-care",
    colours: [WASHED_BLACK, VINTAGE_WHITE],
    sizes: ALL_SIZES,
    blurb: "Fragile. Mostly emotionally.",
    description:
      "Shipping-label back print on heavyweight cotton. Boxy fit, double-stitched hem, honest about what it's carrying.",
  },
  {
    slug: "mentally-on-annual-leave-tee",
    name: "Mentally On Annual Leave Tee",
    price: 49.95,
    category: "tees",
    art: "annual-leave",
    colours: [WASHED_BLACK, VINTAGE_WHITE],
    sizes: ALL_SIZES,
    blurb: "Physically present. Barely.",
    description:
      "Stacked type back print on mid-weight cotton. Regular fit. Pairs well with an out-of-office you never turned off.",
  },
  {
    slug: "offline-since-birth-tee",
    name: "Offline Since Birth Tee",
    price: 49.95,
    category: "tees",
    art: "offline",
    colours: [VINTAGE_WHITE, WASHED_BLACK],
    sizes: ALL_SIZES,
    blurb: "Never had the signal. Never wanted it.",
    description:
      "Minimal chest print, heavyweight vintage-wash cotton. Boxy fit. The least online thing you'll own.",
  },
  {
    slug: "emotional-support-beverage-tee",
    name: "Emotional Support Beverage Tee",
    price: 49.95,
    category: "tees",
    art: "beverage",
    colours: [VINTAGE_WHITE, WASHED_BLACK],
    sizes: ALL_SIZES,
    blurb: "Certified. Registered. Refillable.",
    description:
      "Front print on garment-dyed cotton with a relaxed drape. Soft as hell, holds its shape, asks no questions.",
  },
];

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

export const FREE_SHIPPING_THRESHOLD = 130;
