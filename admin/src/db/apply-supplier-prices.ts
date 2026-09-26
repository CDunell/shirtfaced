/**
 * Price check of 26 September 2026: figures read from the Printful API (our
 * key), from Shopify stores' own product JSON, and from supplier pages in a
 * real browser. Each entry overwrites only the fields it names on that
 * supplier's record for that blank (creating the record if missing), so it
 * can be re-run safely. Run with `npm run prices:suppliers`.
 *
 * The cents fields hold one tee in the smallest size with one print, in AUD
 * including GST where the supplier says so; `price` says which, word for word.
 */
import { and, eq } from "drizzle-orm";
import { db } from "./client";
import { blanks, supplierOfferings, suppliers, type Verification } from "./schema";

const CHECKED_AT = new Date("2026-09-26T12:00:00+10:00");
const incGst = (exGstCents: number) => Math.round(exGstCents * 1.1);
/* Frankfurter (ECB) rate for 25 Sep 2026, for suppliers that bill in USD. */
const USD_AUD = 1.4224;

type Update = {
  supplier: string;
  blank: string;
  price: string;
  priceCents?: number | null;
  standardPriceCents?: number | null;
  maxFront?: string;
  maxPrintWidthMm?: number;
  maxPrintHeightMm?: number;
  standardPrint?: string;
  standardPrintWidthMm?: number;
  standardPrintHeightMm?: number;
  printedIn?: "au" | "nz" | "overseas" | "unknown";
  sourceUrl: string;
  verification: Verification;
  notes?: string;
};

const PF = "https://api.printful.com/v2/catalog-products";
const printful = (blank: string, id: number, exGst: number, notes?: string): Update => ({
  supplier: "printful",
  blank,
  price: `A$${(exGst / 100).toFixed(2)} + GST for the tee with one print, any size up to the placement maximum; extra placements +A$8.50–8.85 (Printful API, Australia selling region)`,
  priceCents: incGst(exGst),
  standardPriceCents: incGst(exGst),
  sourceUrl: `${PF}/${id}/prices?selling_region_name=australia&currency=AUD`,
  verification: "api",
  notes,
});

const tshirtCo = "Includes 1 print; +$10 for both sides; tax included (product page). Up to 35 × 45 cm, resized to the garment size.";
const printBar = (blank: string, url: string, tee: number): Update => ({
  supplier: "the-print-bar",
  blank,
  price: `From A$${(tee / 100).toFixed(2)} tee + A$8.50 one-side digital print (A$17 both sides), flat per side; GST treatment not stated`,
  priceCents: tee + 850,
  standardPriceCents: tee + 850,
  sourceUrl: url,
  verification: "page",
});
const merchSprint = (blank: string, tee: number): Update => ({
  supplier: "merchsprint",
  blank,
  price: `A$${(tee / 100).toFixed(2)} tee + A$8.80 per print position (any size; size not published); GST not stated`,
  priceCents: tee + 880,
  standardPriceCents: tee + 880,
  sourceUrl: "https://merchsprint.com.au/products",
  verification: "page",
});
const dropShirt = (blank: string): Update => ({
  supplier: "dropshirt",
  blank,
  price: "A$21.15 ex GST (colours; white A$18.35) incl. print up to A4 (~21 × 29 cm); larger up to 35 × 40 cm +A$3.65, up to 40 × 50 cm +A$7.10; 3XL–5XL +A$2.60",
  standardPriceCents: incGst(2115),
  priceCents: incGst(2115 + 710),
  standardPrint: "A4 (~21 × 29 cm) included",
  standardPrintWidthMm: 210,
  standardPrintHeightMm: 297,
  maxFront: "40 × 50 cm (+A$7.10 ex GST)",
  maxPrintWidthMm: 400,
  maxPrintHeightMm: 500,
  printedIn: "au",
  sourceUrl: "https://www.dropshirt.com.au/product-pricing/",
  verification: "page",
});

const UPDATES: Update[] = [
  printful("as-colour-5001", 440, 2749, "Stocked in AU (74 of 75 variants)."),
  printful("comfort-colors-1717", 586, 2250, "Not stocked in AU: ships from US/EU, ~19–20 business days."),
  printful("as-colour-5025", 539, 2499),
  printful("as-colour-4062", 636, 2725),

  { supplier: "the-t-shirt-co", blank: "as-colour-5026", price: `A$31.95 incl GST (4XL+ A$34.95). ${tshirtCo}`, priceCents: 3195, standardPriceCents: 3195, maxFront: "35 × 45 cm", maxPrintWidthMm: 350, maxPrintHeightMm: 450, printedIn: "au", sourceUrl: "https://thetshirtco.com.au/products/classic-tee-custom-printed-as-colour", verification: "page", notes: "Colours other than stock are ordered in: 7–10 business days." },
  { supplier: "the-t-shirt-co", blank: "comfort-colors-1717", price: `A$29.95 incl GST. ${tshirtCo}`, priceCents: 2995, standardPriceCents: 2995, maxFront: "35 × 45 cm (per their tee template)", printedIn: "au", sourceUrl: "https://thetshirtco.com.au/products/unisex-comfort-colours-tee-custom-printed-same-day", verification: "page", notes: "In stock in their Brisbane warehouse; printed in 3–5 business days, same-day rush available." },
  { supplier: "the-t-shirt-co", blank: "as-colour-5080", price: "A$38.95 incl GST (4XL+ A$40.95), 1 DTF print; 280 gsm AS Colour Heavy Tee (store's product JSON)", priceCents: 3895, standardPriceCents: 3895, printedIn: "au", sourceUrl: "https://thetshirtco.com.au/products/mens-heavy-tee-dtf-printed", verification: "page", notes: "Ordered in: 7–10 business days." },

  { supplier: "printibly", blank: "as-colour-5026", price: "A$32.95 incl GST = A$21.00 garment + A$11.95 per print surface; front options up to 'Front Full' 300 × 495 mm; sleeves +A$7; no setup fees, no minimum", priceCents: 3295, standardPriceCents: 3295, maxFront: "Front Full 300 × 495 mm", maxPrintWidthMm: 300, maxPrintHeightMm: 495, printedIn: "au", sourceUrl: "https://printibly.com.au/products/classic-tee-5026", verification: "page", notes: "DTF, printed in Adelaide, dispatch 3–5 business days." },

  printBar("as-colour-5026", "https://theprintbar.com/products/as-colour-mens-classic-t-shirt-5026", 2445),
  printBar("comfort-colors-1717", "https://theprintbar.com/products/comfort-colors-adult-heavyweight-t-shirt-1717", 2227),
  printBar("as-colour-5001", "https://theprintbar.com/page/digital-printing", 1789),
  printBar("as-colour-4062", "https://theprintbar.com/page/digital-printing", 1609),

  { supplier: "screenlab", blank: "as-colour-5026", price: "A$35.00 incl. product + 1-sided print; second side +A$16; print size not stated", priceCents: 3500, standardPriceCents: 3500, printedIn: "au", sourceUrl: "https://order.screenlab.co/product/classic-tee-5026/", verification: "page" },

  merchSprint("as-colour-5026", 1639),
  merchSprint("as-colour-5080", 2040),
  merchSprint("as-colour-5001", 1440),
  merchSprint("as-colour-4062", 1360),
  merchSprint("as-colour-5025", 1440),

  { supplier: "ogo", blank: "as-colour-5026", price: "A$11.00 tee + A$11 per print on coloured garments (A$8 on white); GST not stated", priceCents: 2200, standardPriceCents: 2200, sourceUrl: "https://ogo.com.au/product/as-colour-mens-classic-tee/", verification: "page" },

  dropShirt("as-colour-5001"),
  dropShirt("as-colour-5025"),
  dropShirt("as-colour-4010"),

  { supplier: "tee-junction", blank: "as-colour-5026", price: "'Digital DTF Printing from $32.95*' — exact price only in their designer", sourceUrl: "https://www.teejunction.com.au/blank_product/82870837/AS-Colour-Classic-Tee", verification: "page" },
  ...(["comfort-colors-1717", "as-colour-5001", "as-colour-4062"] as const).map((blank, i): Update => ({
    supplier: "merchize",
    blank,
    price: `Base cost ${["9.99", "12.00", "9.99"][i]} (tier 1; the API gives no currency) + AU shipping 4.99 first item, 2.50 each extra; production 1–3 days; print inclusion not stated`,
    printedIn: "au",
    sourceUrl: "Merchize API /product/catalog",
    verification: "api",
  })),
  /* Second pass, same day: gaps on the shortlist. */
  ...([["as-colour-5026", 2455], ["as-colour-5080", 3055], ["as-colour-5082", 3055], ["as-colour-5069", 2675], ["as-colour-5050", 2010]] as const).map(([blank, exGst]): Update => ({
    supplier: "dropshirt",
    blank,
    price: `Non-core style, ordered in (+4–5 working days): A$${(exGst / 100).toFixed(2)} ex GST (colours) incl. print up to A4; up to 35 × 40 cm +A$3.65, up to 40 × 50 cm +A$7.10`,
    standardPriceCents: incGst(exGst),
    priceCents: incGst(exGst + 710),
    standardPrint: "A4 (~21 × 29 cm) included",
    standardPrintWidthMm: 210,
    standardPrintHeightMm: 297,
    maxFront: "40 × 50 cm (+A$7.10 ex GST)",
    maxPrintWidthMm: 400,
    maxPrintHeightMm: 500,
    printedIn: "au",
    sourceUrl: "https://dashboard.dropshirt.com.au/support/knowledgebase.php?article=54",
    verification: "page",
  })),
  printBar("as-colour-5080", "https://theprintbar.com/products/as-colour-mens-heavy-t-shirt-5080", 2896),
  printBar("as-colour-5082", "https://theprintbar.com/products/as-colour-mens-heavy-faded-t-shirt-5082", 2819),
  ...(["as-colour-5026", "as-colour-5080", "as-colour-5082", "as-colour-5050", "as-colour-5001", "as-colour-4062", "as-colour-5025"] as const).map((blank): Update => ({
    ...merchSprint(blank, { "as-colour-5026": 1639, "as-colour-5080": 2040, "as-colour-5082": 2320, "as-colour-5050": 1360, "as-colour-5001": 1440, "as-colour-4062": 1360, "as-colour-5025": 1440 }[blank]),
    maxFront: "39 × 48.75 cm, at no extra cost, in Create Apparel's designer (MerchSprint's print house); MerchSprint itself doesn't publish a size",
    maxPrintWidthMm: 390,
    maxPrintHeightMm: 488,
    printedIn: "au",
  })),
  ...([["comfort-colors-1717", 999], ["as-colour-5001", 1200], ["as-colour-4062", 999]] as const).map(([blank, usd]): Update => ({
    supplier: "merchize",
    blank,
    price: `US$${(usd / 100).toFixed(2)} incl. one printed side (+US$4.50 double-sided) = A$${((usd * USD_AUD) / 100).toFixed(2)} at ${USD_AUD} (25 Sep 2026); AU shipping US$4.99 first item, US$2.50 each extra; print size not published; GST not stated`,
    priceCents: Math.round(usd * USD_AUD),
    standardPriceCents: Math.round(usd * USD_AUD),
    printedIn: "au",
    sourceUrl: "https://merchize.com/product/classic-unisex-t-shirt-comfort-colors-1717-(made-in-au)/",
    verification: "page",
  })),
  { supplier: "mod-merch-on-demand", blank: "as-colour-5026", price: "A$25.00 tee (store currency AUD); per-side print cost not on the product page", sourceUrl: "https://merchondemand.com.au/products/bh-mens-as-colour-classic-tee-5026", verification: "page" },
];

async function main() {
  let changed = 0;
  for (const { supplier, blank, ...fields } of UPDATES) {
    const [s] = await db.select({ id: suppliers.id }).from(suppliers).where(eq(suppliers.slug, supplier));
    const [b] = await db.select({ id: blanks.id }).from(blanks).where(eq(blanks.slug, blank));
    if (!s || !b) {
      console.warn(`skip ${supplier} / ${blank}: ${!s ? "supplier" : "blank"} not found`);
      continue;
    }
    const values = { ...fields, checkedAt: CHECKED_AT, updatedAt: new Date() };
    const existing = await db
      .select({ id: supplierOfferings.id })
      .from(supplierOfferings)
      .where(and(eq(supplierOfferings.supplierId, s.id), eq(supplierOfferings.blankId, b.id)));
    if (existing.length) {
      await db.update(supplierOfferings).set(values).where(eq(supplierOfferings.id, existing[0].id));
    } else {
      await db.insert(supplierOfferings).values({ supplierId: s.id, blankId: b.id, status: "yes", ...values });
    }
    changed++;
  }

  /* DropShirt's supplier-wide figures, now read from its own pricing page. */
  await db
    .update(suppliers)
    .set({
      standardPrint: "A4 (~21 × 29 cm) included in base price",
      maxPrint: "40 × 50 cm (+A$7.10 ex GST); 35 × 40 cm (+A$3.65)",
      verification: "page",
      checkedAt: CHECKED_AT,
      notes: "Our live AU fulfiller for My Mixups. First My Mixups sample (22 Sep 2026): print excellent, but the Sportage SP2644 basic tee blank felt cheap, so My Mixups moved to AS Colour 3005/3006 through DropShirt. Wholesale prices are ex GST and include one A4 print (pricing page, 26 Sep 2026). Second print position: +$6.50 (10 × 10 cm), +$11 (A4), +$14 (A3 35 × 40 cm). Can order non-core AS Colour styles (how the My Mixups hoodie is done) — ask about 5026/5080.",
      updatedAt: new Date(),
    })
    .where(eq(suppliers.slug, "dropshirt"));

  await db
    .update(suppliers)
    .set({ notes: "250 GSM 100% cotton heavyweight blank. On 26 Sep 2026 its Shopify store showed 'Store unavailable'.", checkedAt: CHECKED_AT, updatedAt: new Date() })
    .where(eq(suppliers.slug, "premium-blanks-australia"));

  console.log(`Updated ${changed}/${UPDATES.length} supplier-blank prices.`);
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
