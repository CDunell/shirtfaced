/**
 * Seeds the 36 live products (12 creatures × tee/hoodie/cap). This is a
 * point-in-time copy of curbstamps-site/src/lib/creatures.ts + products.ts —
 * dumped here rather than imported live so this app stays deployable on its
 * own, same reasoning as shirtfaced-admin/src/db/seed.ts. Keep the two in
 * sync by hand until the storefront's catalog moves into this database and
 * syncs the other way (see curbstamps-site/README.md).
 *
 * Safe to re-run — replaces the product table each time. Run with `npm run seed`.
 */
import { db } from "./client";
import { products as productsTable } from "./schema";

const CREATURES = [
  { slug: "blip", name: "Blip", animal: "caterpillar", blurb: "Always mid-thought, trundling wherever the curb leads.", accent: { name: "Grass", hex: "#7ed957" } },
  { slug: "twig", name: "Twig", animal: "stick insect", blurb: "Impossibly long. Allegedly a stick. Absolutely not a stick.", accent: { name: "Sky", hex: "#3ec6e0" } },
  { slug: "murk", name: "Murk", animal: "eel", blurb: "Lives in the murky bit of the drain, unbothered by any of it.", accent: { name: "Teal", hex: "#2c9e8f" } },
  { slug: "squib", name: "Squib", animal: "platypus", blurb: "Waddles like it's got somewhere better to be. It doesn't.", accent: { name: "Butter", hex: "#ffc93c" } },
  { slug: "plod", name: "Plod", animal: "tortoise", blurb: "Will get there. Eventually. No rush at all.", accent: { name: "Moss", hex: "#8a9a5b" } },
  { slug: "grub", name: "Grub", animal: "caterpillar", blurb: "Hungry, harmless, extremely good at hiding under things.", accent: { name: "Coral", hex: "#ff6f5e" } },
  { slug: "grit", name: "Grit", animal: "bandicoot", blurb: "Bossy little bandicoot energy. First in line for everything.", accent: { name: "Clay", hex: "#c96f4a" } },
  { slug: "bub", name: "Bub", animal: "dugong", blurb: "Round, happy, mostly just vibing.", accent: { name: "Powder", hex: "#a7c4e0" } },
  { slug: "claw", name: "Claw", animal: "crab", blurb: "Comes in sideways, leaves the same way.", accent: { name: "Tomato", hex: "#ff5757" } },
  { slug: "dreg", name: "Dreg", animal: "little devil", blurb: "Small devil, big grin, definitely didn't do it.", accent: { name: "Grape", hex: "#9b6bd6" } },
  { slug: "lod", name: "Lod", animal: "slug", blurb: "Slow, slippery, weirdly confident about it.", accent: { name: "Lilac", hex: "#c9a7e0" } },
  { slug: "snu", name: "Snu", animal: "shrew", blurb: "Sniffs everything first. Trust issues.", accent: { name: "Sand", hex: "#e0b98a" } },
];

const CATEGORY_LABEL = { tee: "Tee", hoodie: "Hoodie", cap: "Cap" } as const;
const CATEGORY_PRICE_CENTS = { tee: 3495, hoodie: 6495, cap: 2995 } as const;

const TODDLER_SIZES = ["2T", "3T", "4T", "5T"];
const YOUTH_SIZES = ["XS (6/7)", "S (8)", "M (10/12)", "L (14/16)", "XL (18/20)"];
const CAP_SIZES = ["Toddler", "Youth"];

const BASE_COLOURWAYS = [
  { name: "Jet Black", swatch: "#1c1a17", body: "#1c1a17" },
  { name: "Natural", swatch: "#f1e9d8", body: "#f1e9d8" },
];

async function main() {
  await db.transaction(async (tx) => {
    await tx.delete(productsTable);

    for (const creature of CREATURES) {
      const colours = [...BASE_COLOURWAYS, { name: creature.accent.name, swatch: creature.accent.hex, body: creature.accent.hex }];

      for (const category of ["tee", "hoodie", "cap"] as const) {
        await tx.insert(productsTable).values({
          slug: `${creature.slug}-${category}`,
          creature: creature.slug,
          category,
          name: `${creature.name} ${CATEGORY_LABEL[category]}`,
          priceCents: CATEGORY_PRICE_CENTS[category],
          art: `/creatures/${creature.slug}-logo.png`,
          colours,
          sizes: category === "cap" ? CAP_SIZES : [...TODDLER_SIZES, ...YOUTH_SIZES],
          blurb: creature.blurb,
          description: `${creature.name} the ${creature.animal}, stamped on a ${CATEGORY_LABEL[category].toLowerCase()} kids will actually wear twice.`,
        });
      }
    }
  });

  console.log(`Seeded ${CREATURES.length * 3} products.`);
  process.exit(0);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
