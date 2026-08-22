/**
 * The 12 creatures with finished artwork today, out of a planned 60. Each
 * creature is a character, not just a print — name, personality blurb and a
 * signature accent colour, used across the shop grid, product pages and the
 * garment mockups in components/GarmentArt.tsx.
 *
 * Artwork lives at /public/creatures/{slug}-logo.png — a transparent-
 * background line-art lockup (creature + wordmark) generated from the
 * supplied logo sheets. See docs/curbstamps/CURB_STAMPS_SPEC.md §3 for the
 * other 48 and how they slot in once art exists.
 */
export type Creature = {
  slug: string;
  name: string;
  animal: string;
  blurb: string;
  /** Signature accent — used as a third garment colourway and as this
   * creature's tab colour throughout the shop. */
  accent: { name: string; hex: string };
};

export const CREATURES: Creature[] = [
  {
    slug: "blip",
    name: "Blip",
    animal: "caterpillar",
    blurb: "Always mid-thought, trundling wherever the curb leads.",
    accent: { name: "Grass", hex: "#7ed957" },
  },
  {
    slug: "twig",
    name: "Twig",
    animal: "stick insect",
    blurb: "Impossibly long. Allegedly a stick. Absolutely not a stick.",
    accent: { name: "Sky", hex: "#3ec6e0" },
  },
  {
    slug: "murk",
    name: "Murk",
    animal: "eel",
    blurb: "Lives in the murky bit of the drain, unbothered by any of it.",
    accent: { name: "Teal", hex: "#2c9e8f" },
  },
  {
    slug: "squib",
    name: "Squib",
    animal: "platypus",
    blurb: "Waddles like it's got somewhere better to be. It doesn't.",
    accent: { name: "Butter", hex: "#ffc93c" },
  },
  {
    slug: "plod",
    name: "Plod",
    animal: "tortoise",
    blurb: "Will get there. Eventually. No rush at all.",
    accent: { name: "Moss", hex: "#8a9a5b" },
  },
  {
    slug: "grub",
    name: "Grub",
    animal: "caterpillar",
    blurb: "Hungry, harmless, extremely good at hiding under things.",
    accent: { name: "Coral", hex: "#ff6f5e" },
  },
  {
    slug: "grit",
    name: "Grit",
    animal: "bandicoot",
    blurb: "Bossy little bandicoot energy. First in line for everything.",
    accent: { name: "Clay", hex: "#c96f4a" },
  },
  {
    slug: "bub",
    name: "Bub",
    animal: "dugong",
    blurb: "Round, happy, mostly just vibing.",
    accent: { name: "Powder", hex: "#a7c4e0" },
  },
  {
    slug: "claw",
    name: "Claw",
    animal: "crab",
    blurb: "Comes in sideways, leaves the same way.",
    accent: { name: "Tomato", hex: "#ff5757" },
  },
  {
    slug: "dreg",
    name: "Dreg",
    animal: "little devil",
    blurb: "Small devil, big grin, definitely didn't do it.",
    accent: { name: "Grape", hex: "#9b6bd6" },
  },
  {
    slug: "lod",
    name: "Lod",
    animal: "slug",
    blurb: "Slow, slippery, weirdly confident about it.",
    accent: { name: "Lilac", hex: "#c9a7e0" },
  },
  {
    slug: "snu",
    name: "Snu",
    animal: "shrew",
    blurb: "Sniffs everything first. Trust issues.",
    accent: { name: "Sand", hex: "#e0b98a" },
  },
];

export function getCreature(slug: string) {
  return CREATURES.find((c) => c.slug === slug);
}
