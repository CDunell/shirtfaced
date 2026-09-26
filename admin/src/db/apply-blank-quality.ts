/**
 * Blank build quality, 26 September 2026: specs from each maker's own page,
 * print behaviour from AS Colour's decoration guide, printers and forum
 * reports (sources in printNotes / notes). Creates blanks that don't exist
 * yet and overwrites these fields on ones that do. Run before
 * prices:suppliers with `npm run quality:blanks`.
 */
import { eq } from "drizzle-orm";
import { db } from "./client";
import { blanks, type BlankCategory } from "./schema";

const GUIDE = "AS Colour's decoration guide";

type Quality = {
  slug: string;
  brand: string;
  styleCode: string;
  name: string;
  category: BlankCategory;
  gsm: number | null;
  fit: string;
  fibre: string;
  yarn: string;
  construction: string;
  dye: string;
  printNotes: string;
  specUrl: string;
  notes: string;
  sortOrder: number;
};

const QUALITY: Quality[] = [
  {
    slug: "as-colour-5026", brand: "AS Colour", styleCode: "5026", name: "Classic Tee", category: "tee", sortOrder: 10,
    gsm: 220, fit: "Regular; L is 56.5 cm chest × 77.5 cm long",
    fibre: "100% combed cotton", yarn: "22-singles",
    construction: "Side-seamed, shoulder-to-shoulder tape, pre-shrunk", dye: "Piece-dyed (not garment-dyed); ~57 colours",
    printNotes: `Combed cotton is the surface ${GUIDE} rates best for DTG and DTF. A US print shop finds AS Colour DTG "more predictable" than Comfort Colors, with the collar holding shape through washing.`,
    specUrl: "https://www.ascolour.com.au/classic-tee-5026",
    notes: "Best all-round for large, detailed DTG prints with a premium feel. Locked main-range blank (GARMENT_BLANK_STRATEGY.md, 13 Aug 2026).",
  },
  {
    slug: "as-colour-5069", brand: "AS Colour", styleCode: "5069", name: "Classic Oversized Tee", category: "tee", sortOrder: 15,
    gsm: 220, fit: "Oversized: dropped shoulder, extra width, slightly shorter",
    fibre: "100% combed cotton", yarn: "22-singles",
    construction: "Side-seamed, shoulder-to-shoulder tape, pre-shrunk", dye: "Piece-dyed; only 6 colours",
    printNotes: "Same fabric as the 5026, so the same clean DTG/DTF surface. No independent wash or print reviews found.",
    specUrl: "https://www.ascolour.com.au/classic-oversized-tee-5069",
    notes: "The 5026's print quality in a boxy streetwear cut; the catch is the 6-colour range.",
  },
  {
    slug: "as-colour-5080", brand: "AS Colour", styleCode: "5080", name: "Heavy Tee", category: "tee", sortOrder: 20,
    gsm: 280, fit: "Relaxed, dropped shoulder, wide neck rib; L is 59 × 78.5 cm",
    fibre: "100% carded cotton (some US resellers still list combed — check a sample)", yarn: "26-doubles",
    construction: "Side-seamed, shoulder-to-shoulder tape, pre-shrunk", dye: "Piece-dyed; ~14 colours",
    printNotes: `Carded: ${GUIDE} says "rougher hand-feel", "slightly less crisp for fine detail prints. Best for bold graphics." Loose fibres can poke through DTG ink; DTF avoids that.`,
    specUrl: "https://www.ascolour.com.au/heavy-tee-5080",
    notes: "Heaviest, most substantial in the hand. Pick it for bold graphics, printed DTF.",
  },
  {
    slug: "as-colour-5082", brand: "AS Colour", styleCode: "5082", name: "Heavy Faded Tee", category: "tee", sortOrder: 25,
    gsm: 240, fit: "Relaxed, dropped shoulder, wide twin-stitched rib; L is 59 × 77.5 cm",
    fibre: "100% carded cotton", yarn: "16-singles",
    construction: "Side-seamed, shoulder-to-shoulder tape, pre-shrunk", dye: "Garment-dyed (faded); ~21 colours",
    printNotes: `AS Colour recommends a dye blocker on faded garments; loose dyes "cause severe dye migration" above ~145 °C. DTF with low-cure powder, test each colour.`,
    specUrl: "https://www.ascolour.com.au/heavy-faded-tee-5082",
    notes: "Vintage look; a US printer calls it clients' favourite and hard to keep in stock. Not for large DTG.",
  },
  {
    slug: "comfort-colors-1717", brand: "Comfort Colors", styleCode: "1717", name: "Garment-Dyed Heavyweight Tee", category: "tee", sortOrder: 30,
    gsm: 207, fit: "Relaxed; L is 55.9 × 74.6 cm",
    fibre: "Ring-spun cotton", yarn: "Not published",
    construction: "Tubular (no side seams), twill shoulder tape, topstitched rib", dye: "Garment-dyed; smaller AU range than the US's 67",
    printNotes: "DTG pretreat can discolour light colours (forum reports on Butter); darks are fine with two light coats. DTF: press 143–154 °C with low-cure powder for dye bleed.",
    specUrl: "https://www.comfortcolors.com/us/en/1717-heavyweight-adult-tee-en_us",
    notes: "Tubular, so it can twist after washing; a UK printer measured 2–3% shrink on a hot wash and sees colour vary batch to batch. Users report mixed fading.",
  },
  {
    slug: "as-colour-5050", brand: "AS Colour", styleCode: "5050", name: "Block Tee", category: "tee", sortOrder: 45,
    gsm: 200, fit: "Regular",
    fibre: "100% carded cotton", yarn: "20-singles",
    construction: "Tubular (no side seams), shoulder-to-shoulder tape, double-needle hems", dye: "Piece-dyed; 12 colours at House of Uniforms",
    printNotes: `Carded, so ${GUIDE}'s "slightly less crisp for fine detail" applies; DropShirt: "Carded Cotton may not produce smoothest DTG print".`,
    specUrl: "https://shop.houseofuniforms.com.au/products/the-block-tubular-tee-mens-short-sleeve",
    notes: "Promo / workwear tee (House of Uniforms: A$10.45 blank). Tubular, so it can twist after washing. Below the 5026 on every build measure.",
  },
  {
    slug: "as-colour-5001", brand: "AS Colour", styleCode: "5001", name: "Staple Tee", category: "tee", sortOrder: 50,
    gsm: 180, fit: "Regular",
    fibre: "100% combed cotton", yarn: "28-singles",
    construction: "Side-seamed, shoulder-to-shoulder tape, pre-shrunk", dye: "Piece-dyed; 70+ colours",
    printNotes: "Good print surface, but at 180 gsm a 40 × 50 cm print will feel stiff against the light shirt.",
    specUrl: "https://www.ascolour.com.au/staple-tee-5001",
    notes: "Baseline only: too light for a premium large print.",
  },
];

/* Store offline and no printer stocks it: nothing to compare (26 Sep 2026). */
const DROP = ["premium-blanks-australia-heavyweight"];

async function main() {
  for (const slug of DROP) await db.delete(blanks).where(eq(blanks.slug, slug));
  for (const q of QUALITY) {
    const [existing] = await db.select({ id: blanks.id }).from(blanks).where(eq(blanks.slug, q.slug));
    if (existing) {
      await db.update(blanks).set({ ...q, updatedAt: new Date() }).where(eq(blanks.id, existing.id));
    } else {
      await db.insert(blanks).values(q);
    }
  }
  console.log(`Wrote quality for ${QUALITY.length} blanks.`);
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
