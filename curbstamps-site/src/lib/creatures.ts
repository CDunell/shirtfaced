/**
 * The finished creature artwork supplied for the launch collection. Each
 * creature is a character, not just a print — name, personality blurb and a
 * signature accent colour, used across the shop grid, product pages and the
 * garment mockups in components/GarmentArt.tsx.
 *
 * Creature-only artwork lives in /public/creatures/masters. Product lockups
 * live in /public/creatures/lockups and are generated from those masters by
 * scripts/curbstamps/build_creature_lockups.py.
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

/** Bump whenever creature artwork changes so mobile browsers cannot retain
 * superseded SVGs under the previous URL. */
export const CREATURE_ASSET_VERSION = "20260823e";

export function creatureMaster(slug: string) {
  return `/creatures/masters/${slug}.svg?v=${CREATURE_ASSET_VERSION}`;
}

export function creatureLockup(slug: string, tone: "light" | "dark") {
  return `/creatures/lockups/${slug}-${tone}.svg?v=${CREATURE_ASSET_VERSION}`;
}

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
  { slug: "drake", name: "Drake", animal: "dragon", blurb: "Tiny dragon. Huge plans. Questionable landing skills.", accent: { name: "Grass", hex: "#7ed957" } },
  { slug: "rex", name: "Rex", animal: "dinosaur", blurb: "The smallest big dinosaur on the whole curb.", accent: { name: "Sky", hex: "#3ec6e0" } },
  { slug: "boff", name: "Boff", animal: "rabbit", blurb: "Big ears, little legs, always listening for snacks.", accent: { name: "Pink", hex: "#ff6f9c" } },
  { slug: "pex", name: "Pex", animal: "armadillo", blurb: "Armoured on the outside. Absolute softie inside.", accent: { name: "Butter", hex: "#ffc93c" } },
  { slug: "crumb", name: "Crumb", animal: "caterpillar", blurb: "Leaves a trail of crumbs and very good ideas.", accent: { name: "Orange", hex: "#ff8c42" } },
  { slug: "bone", name: "Bone", animal: "fish", blurb: "Not much fish left. Still plenty of personality.", accent: { name: "Lilac", hex: "#c7b8ff" } },
  { slug: "yip", name: "Yip", animal: "dog", blurb: "Fast paws, loud opinions, excellent friend.", accent: { name: "Grass", hex: "#7ed957" } },
  { slug: "chit", name: "Chit", animal: "beetle", blurb: "A shiny little beetle with important places to be.", accent: { name: "Sky", hex: "#3ec6e0" } },
  { slug: "mug", name: "Mug", animal: "blob", blurb: "Round, proud and permanently a bit surprised.", accent: { name: "Pink", hex: "#ff6f9c" } },
  { slug: "fizz", name: "Fizz", animal: "beetle", blurb: "Small bug. Big buzz. Cannot sit still.", accent: { name: "Butter", hex: "#ffc93c" } },
  { slug: "mote", name: "Mote", animal: "mite", blurb: "So tiny you nearly missed the best one.", accent: { name: "Orange", hex: "#ff8c42" } },
  { slug: "wisp", name: "Wisp", animal: "worm", blurb: "A quiet squiggle who turns up everywhere.", accent: { name: "Lilac", hex: "#c7b8ff" } },
  { slug: "shrew", name: "Shrew", animal: "shrew", blurb: "Nose first. Questions later.", accent: { name: "Grass", hex: "#7ed957" } },
  { slug: "nub", name: "Nub", animal: "critter", blurb: "A little bit of this and a little bit of that.", accent: { name: "Sky", hex: "#3ec6e0" } },
  { slug: "loam", name: "Loam", animal: "lizard", blurb: "Likes dirt, warm rocks and doing absolutely nothing.", accent: { name: "Pink", hex: "#ff6f9c" } },
  { slug: "zot", name: "Zot", animal: "bug", blurb: "Zips in, zips out, forgets why it came.", accent: { name: "Butter", hex: "#ffc93c" } },
  { slug: "crux", name: "Crux", animal: "critter", blurb: "Pointy in places. Friendly in all the others.", accent: { name: "Orange", hex: "#ff8c42" } },
  { slug: "pip", name: "Pip", animal: "bug", blurb: "Pocket-sized trouble with excellent manners.", accent: { name: "Lilac", hex: "#c7b8ff" } },
  { slug: "slag", name: "Slag", animal: "slug", blurb: "Takes the scenic route. Every single time.", accent: { name: "Grass", hex: "#7ed957" } },
  { slug: "puff", name: "Puff", animal: "pufferfish", blurb: "Puffs up when excited. Gets excited a lot.", accent: { name: "Sky", hex: "#3ec6e0" } },
  { slug: "vol", name: "Vol", animal: "vole", blurb: "Digs first, checks the map afterwards.", accent: { name: "Pink", hex: "#ff6f9c" } },
  { slug: "blob", name: "Blob", animal: "blob", blurb: "No corners. No worries.", accent: { name: "Butter", hex: "#ffc93c" } },
  { slug: "clump", name: "Clump", animal: "critter", blurb: "Built like a pebble. Moves like one too.", accent: { name: "Orange", hex: "#ff8c42" } },
  { slug: "blink", name: "Blink", animal: "bug", blurb: "Now you see Blink. Now you probably still do.", accent: { name: "Lilac", hex: "#c7b8ff" } },
  { slug: "prick", name: "Prick", animal: "echidna", blurb: "Spiky coat. Surprisingly good cuddler.", accent: { name: "Grass", hex: "#7ed957" } },
  { slug: "tum", name: "Tum", animal: "critter", blurb: "Mostly tummy, partly feet, entirely hungry.", accent: { name: "Sky", hex: "#3ec6e0" } },
  { slug: "flit", name: "Flit", animal: "fly", blurb: "Never stays put long enough for a photo.", accent: { name: "Pink", hex: "#ff6f9c" } },
  { slug: "gnat", name: "Gnat", animal: "gnat", blurb: "Tiny wings and absolutely no indoor voice.", accent: { name: "Butter", hex: "#ffc93c" } },
  { slug: "plop", name: "Plop", animal: "frog", blurb: "Arrives with a plop. Leaves with another one.", accent: { name: "Orange", hex: "#ff8c42" } },
  { slug: "nib", name: "Nib", animal: "mouse", blurb: "Nibbles the corner. Then the other corner.", accent: { name: "Lilac", hex: "#c7b8ff" } },
  { slug: "snout", name: "Snout", animal: "pig", blurb: "Finds mud, snacks and secrets with one sniff.", accent: { name: "Grass", hex: "#7ed957" } },
  { slug: "spit", name: "Spit", animal: "lizard", blurb: "Long, low and just a little bit rude.", accent: { name: "Sky", hex: "#3ec6e0" } },
];

export function getCreature(slug: string) {
  return CREATURES.find((c) => c.slug === slug);
}

/**
 * Homepage chrome (creature picker tiles, crew cards, tile states) uses the
 * six approved brand accents, not each creature's own bespoke signature
 * colour above — see DESIGN_HANDOFF.md §3 "avoid rainbow gradients; use one
 * bright colour per tile". The signature colour stays what a garment
 * colourway option actually offers on the product page; this is a separate,
 * smaller palette cycling across creatures purely for homepage decoration.
 */
export const UI_ACCENTS = [
  { name: "Yellow", hex: "#ffc93c" },
  { name: "Blue", hex: "#3ec6e0" },
  { name: "Pink", hex: "#ff6f9c" },
  { name: "Green", hex: "#7ed957" },
  { name: "Orange", hex: "#ff8c42" },
  { name: "Lilac", hex: "#c7b8ff" },
] as const;

export function uiAccentFor(slug: string) {
  const index = CREATURES.findIndex((c) => c.slug === slug);
  return UI_ACCENTS[index % UI_ACCENTS.length];
}
