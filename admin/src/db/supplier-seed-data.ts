/**
 * Starting data for /suppliers, from the supplier sweeps run 25–26 September
 * 2026: Printful, Printify and Merchize catalogues read through our own API
 * keys ("api"), a handful of pages read in full ("page"), and everything else
 * from research agents whose page reader summarises rather than quotes
 * ("summary"). "not_published" means the supplier's own site doesn't say.
 *
 * Seeding is insert-only (see seed-suppliers.ts): once a row exists, edits
 * made in the admin win and this file never overwrites them.
 *
 * Dimensions are millimetres. Pixel sizes are converted at 300 dpi, which
 * Printify doesn't state, so those rows say so. Prices are as stated; the
 * cents fields are filled only where the supplier's own figures add up to one
 * tee with one print.
 */
import type {
  BlankCategory,
  OfferStatus,
  PrintRegion,
  SupplierKind,
  Verification,
} from "./schema";

export type BlankKey = "5026" | "1717" | "5001" | "5080" | "5025" | "4062" | "4010" | "pba250";

export const SEED_BLANKS: Record<
  BlankKey,
  { slug: string; brand: string; styleCode: string; name: string; category: BlankCategory; gsm: number | null; fit: string | null; notes: string | null; sortOrder: number }
> = {
  "5026": { slug: "as-colour-5026", brand: "AS Colour", styleCode: "5026", name: "Classic Tee", category: "tee", gsm: 220, fit: "Regular, structured", notes: "Locked main-range blank (GARMENT_BLANK_STRATEGY.md, 13 Aug 2026).", sortOrder: 10 },
  "1717": { slug: "comfort-colors-1717", brand: "Comfort Colors", styleCode: "1717", name: "Garment-Dyed Heavyweight Tee", category: "tee", gsm: 207, fit: "Relaxed, garment-dyed", notes: "Washed / vintage releases.", sortOrder: 20 },
  "5080": { slug: "as-colour-5080", brand: "AS Colour", styleCode: "5080", name: "Heavy Tee", category: "tee", gsm: 280, fit: "Relaxed", notes: "Premium heavyweight candidate; barely researched yet.", sortOrder: 30 },
  "pba250": { slug: "premium-blanks-australia-heavyweight", brand: "Premium Blanks Australia", styleCode: "250", name: "Premium Heavyweight Tee", category: "tee", gsm: 250, fit: null, notes: "Found 26 Sep 2026; unresearched beyond its product page.", sortOrder: 40 },
  "5001": { slug: "as-colour-5001", brand: "AS Colour", styleCode: "5001", name: "Staple Tee", category: "tee", gsm: 180, fit: "Regular", notes: "Lighter than the range standard; listed because many print-on-demand platforms only carry this one.", sortOrder: 50 },
  "5025": { slug: "as-colour-5025", brand: "AS Colour", styleCode: "5025", name: "Barnard Tank", category: "tank", gsm: null, fit: null, notes: null, sortOrder: 60 },
  "4062": { slug: "as-colour-4062", brand: "AS Colour", styleCode: "4062", name: "Women's Crop Tee", category: "crop", gsm: null, fit: null, notes: null, sortOrder: 70 },
  "4010": { slug: "as-colour-4010", brand: "AS Colour", styleCode: "4010", name: "Women's Bevel V-Neck", category: "v_neck", gsm: null, fit: null, notes: null, sortOrder: 80 },
};

export type SeedOffer = {
  st: OfferStatus;
  pi?: PrintRegion;
  std?: string;
  sw?: number;
  sh?: number;
  max?: string;
  back?: string;
  mw?: number;
  mh?: number;
  p?: string;
  pc?: number;
  spc?: number;
  mq?: number;
  src?: string;
  v?: Verification;
  nt?: string;
};

export type SeedSupplier = {
  s: string;
  n: string;
  k: SupplierKind;
  r: string;
  l?: string;
  pi: PrintRegion;
  m?: string[];
  min?: string;
  mq?: number;
  std?: string;
  sw?: number;
  sh?: number;
  max?: string;
  mw?: number;
  mh?: number;
  w?: string;
  i?: string;
  acct?: boolean;
  src?: string[];
  v?: Verification;
  nt?: string;
  o?: Partial<Record<BlankKey, SeedOffer>>;
};

const A4 = { std: "A4 (21 × 29.7 cm)", sw: 210, sh: 297 };

/* ---------------------------------------------------------------- accounts */

const ACCOUNTS: SeedSupplier[] = [
  {
    s: "printful", n: "Printful", k: "pod", r: "INTL", l: "Partner facilities in Brisbane & Melbourne, plus overseas", pi: "au",
    m: ["DTG", "DTF", "embroidery"], min: "No minimums", mq: 1, max: "12 × 16 in front & back (standard DTG)", mw: 305, mh: 406,
    w: "https://www.printful.com", i: "API (our account, key in My Mixups admin)", acct: true, v: "api",
    src: ["https://www.printful.com/au/print-on-demand-australia", "https://api.printful.com/products"],
    nt: "Catalogue and print areas read from the API on 26 Sep 2026. Only some products are stocked in Australia; the rest ship from overseas. Does not carry AS Colour 5026 at all.",
    o: {
      "5001": { st: "yes", pi: "au", max: "12 × 16 in", back: "12 × 16 in", mw: 305, mh: 406, p: "AU$27.49, one print included (starting price)", pc: 2749, src: "https://www.printful.com/custom/brands/as-colour/mens-staple-t-shirt-as-colour-5001", v: "api", nt: "74 of 75 variants in stock in AU. Price from a page summary." },
      "1717": { st: "yes", pi: "overseas", max: "12 × 16 in (15 × 18 in 'large' front)", back: "12 × 16 in", mw: 305, mh: 406, p: "AU$22.50 starting; ~19–20 business days to AU", pc: 2250, src: "https://www.printful.com/custom/mens/t-shirts/unisex-garment-dyed-heavyweight-shirt-comfort-colors-1717", v: "api", nt: "0 variants stocked in AU (US, CA, EU, UK only)." },
      "5026": { st: "no", v: "api", nt: "Not in the Printful catalogue." },
      "5025": { st: "yes", pi: "au", max: "12 × 16 in", back: "12 × 16 in", mw: 305, mh: 406, p: "AU$24.99", v: "api" },
      "4062": { st: "yes", pi: "au", max: "10 × 10 in", back: "10 × 10 in", mw: 254, mh: 254, p: "AU$22.39", v: "api", nt: "35 of 51 variants in stock in AU." },
    },
  },
  {
    s: "printify", n: "Printify (platform)", k: "pod", r: "INTL", l: "Routes orders to print providers", pi: "unknown",
    min: "No minimums", mq: 1, w: "https://printify.com", i: "API (our account, key in My Mixups admin)", acct: true, v: "api",
    src: ["https://printify.com/app/products/706/comfort-colors/unisex-garment-dyed-t-shirt"],
    nt: "A platform, not a printer. Its Australian printers for our blanks are The Print Bar (Brisbane), Prima Printing (Melbourne) and QTCo; each has its own row. Printify Choice may route to an AU facility but doesn't say which.",
    o: {
      "1717": { st: "yes", pi: "unknown", p: "US$12.65 via Printify Choice; US$21.82 via The Print Bar (AU)", v: "api" },
      "5026": { st: "no", v: "api", nt: "Only 5026G Organic, US-only via Fulfill Engine." },
      "5001": { st: "yes", pi: "au", p: "US$16.63–16.98 via Prima Printing / The Print Bar", v: "api" },
    },
  },
  {
    s: "merchize", n: "Merchize", k: "pod", r: "AU", l: "AU production (city not published) + US", pi: "au",
    m: ["DTG", "DTF"], min: "MOQ 1", mq: 1, w: "https://merchize.com", i: "API (our account, key in My Mixups admin)", acct: true, v: "api",
    src: ["https://merchize.com/product/classic-unisex-t-shirt-comfort-colors-1717-(made-in-au)/"],
    nt: "Catalogue searched through the API on 26 Sep 2026. Its API exposes no print-area or mockup data. Its blog quotes 'T-shirts from A$12.6 (AU production)'.",
    o: {
      "1717": { st: "yes", pi: "au", p: "'Made in AU' SKU 1717AU; $9.99 shown, print inclusion not stated", v: "api" },
      "5001": { st: "yes", pi: "au", v: "api", nt: "SKU 5001AU, Made in AU." },
      "4062": { st: "yes", pi: "au", v: "api", nt: "SKU 4062AU, Made in AU." },
      "5026": { st: "no", v: "api", nt: "No catalogue hits for 5026." },
    },
  },
  {
    s: "dropshirt", n: "DropShirt", k: "pod", r: "AU", l: "Australia (city not published)", pi: "au",
    m: ["DTG"], ...A4, std: "A4 (~21 × 29 cm) included in base price", max: "~40 × 50 cm (~2000 cm²), surcharge above ~620 cm²", mw: 400, mh: 500,
    w: "https://dropshirt.com.au", i: "WooCommerce relay (our account, live for My Mixups)", acct: true, v: "summary",
    src: ["https://dropshirt.com.au/product-pricing/", "https://dropshirt.com.au/artwork-requirements/"],
    nt: "Our live AU fulfiller for My Mixups. Base price covers an A4 print; the two research sweeps disagree on the A3 oversize surcharge (+$3.65 vs +$14.00) — ask. Can order in non-core AS Colour styles (how the My Mixups hoodie is done).",
    o: {
      "5026": { st: "no", v: "summary", nt: "Not on its pricing page; may be orderable as a non-core AS Colour style — ask." },
      "1717": { st: "no", v: "summary" },
      "5001": { st: "yes", pi: "au", ...A4, p: "$21.15 ex GST (colours), standard A4 print included", spc: 2115, v: "summary", nt: "Ex GST." },
      "5025": { st: "yes", pi: "au", ...A4, p: "$21.15 ex GST colours / $18.35 white", spc: 2115, v: "summary", nt: "Ex GST." },
      "4010": { st: "yes", pi: "au", ...A4, p: "$21.15 ex GST colours / $18.35 white", spc: 2115, v: "summary", nt: "Ex GST." },
    },
  },
];

/* -------------------------------------------- Australian print-on-demand */

const AU_POD: SeedSupplier[] = [
  {
    s: "ogo", n: "OGO", k: "pod", r: "VIC", l: "Ferntree Gully, Melbourne", pi: "au",
    m: ["DTF", "DTG"], min: "Print on demand, per item", mq: 1, std: "14 × 16 in per side (flat per-side price)", sw: 356, sh: 406,
    max: "14 × 16 in front & back (tanks ~12 × 16 in)", mw: 356, mh: 406, w: "https://ogo.com.au", i: "Shopify app (Australian POD)", v: "page",
    src: ["https://help.ogo.com.au/article/277-what-print-positions-are-available", "https://ogo.com.au/guides/design-guide/", "https://ogo.com.au/product/as-colour-mens-classic-tee/"],
    nt: "Print area and 5026 price checked on its own pages 26 Sep 2026. DTF is its main process since Jan 2024 though the homepage still says DTG. The Shopify listing says charges are billed in USD — confirm currency. Minimum order and GST treatment not published. Sister business: Tee Junction.",
    o: {
      "5026": { st: "yes", pi: "au", std: "14 × 16 in", sw: 356, sh: 406, max: "14 × 16 in", back: "14 × 16 in", mw: 356, mh: 406, p: "$11 tee + $11 per side on coloured garments ($8 on white)", pc: 2200, spc: 2200, src: "https://ogo.com.au/product/as-colour-mens-classic-tee/", v: "page" },
      "1717": { st: "no", v: "summary" },
      "5025": { st: "yes", pi: "au", p: "$9.00 tee", v: "summary" },
      "4062": { st: "yes", pi: "au", v: "summary", nt: "Women's Crop Tee listed." },
      "4010": { st: "yes", pi: "au", v: "summary", nt: "Women's Bevel V-neck listed." },
    },
  },
  {
    s: "merchsprint", n: "MerchSprint", k: "pod", r: "NSW", l: "Auburn, Sydney", pi: "au",
    m: ["DTG (Kornit)", "DTF"], min: "From 1 piece", mq: 1, w: "https://merchsprint.com.au", i: "Dropship platform (run by Create Apparel)", v: "page",
    src: ["https://merchsprint.com.au/products"], nt: "Prices checked on its own page 26 Sep 2026. No print area published anywhere — ask.",
    o: { "5026": { st: "yes", pi: "au", p: "$16.39 tee + $8.80 per print position (size not stated); neck labels $3.50", src: "https://merchsprint.com.au/products", v: "page" } },
  },
  {
    s: "the-print-bar", n: "The Print Bar", k: "print_shop", r: "QLD", l: "Gaythorne, Brisbane & Fitzroy, Melbourne", pi: "au",
    m: ["DTG", "DTF", "screen", "embroidery"], min: "None for digital; screen 25", mq: 1, w: "https://www.theprintbar.com", i: "Printify provider + own Shopify POD app", v: "api",
    src: ["https://www.theprintbar.com/what-we-do/print-on-demand", "https://printify.com/app/products/706/comfort-colors/unisex-garment-dyed-t-shirt"],
    nt: "Print file sizes come from Printify's API in pixels, converted here at an assumed 300 dpi; they step up with garment size. Own help pages publish no maximum.",
    o: {
      "1717": { st: "yes", pi: "au", max: "4500 × 5100 px at largest size (≈ 38 × 43 cm at 300 dpi)", mw: 381, mh: 432, p: "From $22.27 direct; US$21.82 via Printify", src: "https://www.theprintbar.com/products/comfort-colors-adult-heavyweight-t-shirt-1717", v: "api", nt: "Size from Printify API (dpi assumed)." },
      "5001": { st: "yes", pi: "au", max: "4682 × 5291 px at largest size (≈ 40 × 45 cm at 300 dpi)", mw: 396, mh: 448, p: "US$16.98 via Printify", v: "api" },
      "5026": { st: "yes", pi: "au", p: "From $24.45 + $8.50 one-side digital print (size not stated)", src: "https://www.theprintbar.com/products/as-colour-mens-classic-t-shirt-5026", v: "summary", nt: "Direct only; not offered through Printify." },
      "5025": { st: "yes", pi: "au", max: "2657–3071 × 3270–3780 px by size", p: "From $16.09 direct; US$18.28 via Printify", v: "api" },
      "5080": { st: "yes", pi: "au", v: "api", nt: "Listed through Printify for the AU market." },
      "4062": { st: "yes", pi: "au", p: "From $16.09 direct; US$18.47 via Printify", v: "api" },
    },
  },
  {
    s: "prima-printing", n: "Prima Printing", k: "pod", r: "VIC", l: "Noble Park North, Melbourne", pi: "au",
    m: ["DTG"], w: "https://primaprinting.com.au", i: "Printify provider; own API / Order Desk", v: "api",
    src: ["https://primaprinting.com.au/print-on-demand-australia/"],
    o: { "5001": { st: "yes", pi: "au", max: "4200 × 4800 px (14 × 16 in at 300 dpi)", mw: 356, mh: 406, p: "US$16.63 via Printify", v: "api" }, "5026": { st: "unknown", v: "not_published" }, "1717": { st: "no", v: "api", nt: "Not offered through Printify." } },
  },
  {
    s: "qtco", n: "QTCo", k: "print_shop", r: "QLD", l: "Brisbane (Kedron per listings)", pi: "au",
    m: ["DTG", "DTF", "screen", "embroidery", "sublimation"], min: "20 per design (its DTG page says no minimums)", max: "DTG: approx 355 × 455 mm", mw: 355, mh: 455,
    w: "https://qtco.com.au", i: "Printify provider (Gildan 5000 only) + direct orders", v: "summary",
    src: ["https://qtco.com.au/frequently-asked-questions/", "https://qtco.com.au/direct-to-garment/", "https://qtco.com.au/screen-printing/"],
    nt: "Screen: 20 shirts $20–25 each; 50 shirts $13–20 (2 colours, 1 position). Its own pages disagree on minimums.",
  },
  {
    s: "printicks", n: "Printicks", k: "pod", r: "NSW", l: "Kellyville", pi: "au",
    m: ["screen", "embroidery", "heat transfer"], std: "35 × 40 cm standard area", sw: 350, sh: 400, max: "35 × 40 cm", mw: 350, mh: 400,
    w: "https://printicks.com.au", i: "Dropshipping integration", v: "summary", src: ["https://printicks.com.au/page/dropshipping"],
    o: { "5026": { st: "yes", pi: "au", p: "From $35.75", v: "summary" }, "1717": { st: "yes", pi: "au", p: "From $38.28", v: "summary" }, "5025": { st: "yes", pi: "au", v: "summary" }, "4062": { st: "yes", pi: "au", v: "summary" } },
  },
  {
    s: "mod-merch-on-demand", n: "MOD – Merch on Demand", k: "pod", r: "AU", l: "Australia (city not published)", pi: "au",
    m: ["DTG"], max: "25 × 33 cm artwork canvas", mw: 250, mh: 330, w: "https://merchondemand.com.au", i: "Shopify app", v: "summary",
    src: ["https://merchondemand.com.au/products/bh-mens-as-colour-classic-tee-5026", "https://merchondemand.com.au/pages/design-guides"],
    o: { "5026": { st: "yes", pi: "au", max: "25 × 33 cm", mw: 250, mh: 330, p: "$25.00 tee + $8 per side (app listing says billed in USD)", v: "summary" } },
  },
  {
    s: "printdrop-express", n: "Printdrop Express", k: "pod", r: "AU", pi: "unknown", min: "No minimum order", mq: 1, w: "https://printdropexpress.com", i: "Shopify app", v: "summary",
    src: ["https://printdropexpress.com/products/classic-organic-tee-5026g"],
    nt: "Lists 5026G Organic ($22.71); the plain 5026 listing shows $0.00. Print adds a variable cost.",
    o: { "5026": { st: "unknown", v: "summary", nt: "Plain 5026 listed at $0.00 — unclear." }, "5025": { st: "yes", pi: "unknown", v: "summary" }, "4062": { st: "yes", pi: "unknown", v: "summary" } },
  },
  { s: "ink-style", n: "Ink Style", k: "pod", r: "AU", pi: "unknown", m: ["DTF", "DTG"], w: "https://inkstyle.secure-decoration.com", v: "summary", nt: "Points to OGO for Shopify; shares Tee Junction's phone number and designer.", o: { "5026": { st: "yes", pi: "unknown", p: "From $32.95", v: "summary" } } },
  { s: "constantsupply", n: "ConstantSupply", k: "pod", r: "QLD", l: "Gold Coast", pi: "au", m: ["DTG", "DTF", "screen (100+)"], w: "https://apps.shopify.com/constant-supply-print-on-demand", i: "Shopify app", v: "summary", nt: "'We print, pack and ship all products from our Gold Coast-based warehouse.' Blank brands not published. $16.22 for a single-sided white tee (listing says billed in USD).", src: ["https://help.app.constant.supply/en-US/our-decorationprinting-methods-204575"] },
  { s: "inkedjoy", n: "Inkedjoy", k: "pod", r: "AU", pi: "au", w: "https://inkedjoy.com/all-products/made-in-australia", v: "summary", nt: "'Made in Australia' range, ships to Australia only. Blank brand not published. Men's tee US$15.01 front only, US$20.90 both sides." },
  { s: "kookaburra-print", n: "Kookaburra Print", k: "pod", r: "VIC", l: "Clayton South (also Auckland)", pi: "au", w: "https://kookaburraprint.com.au", v: "not_published", nt: "Business-to-business fulfilment; no seller app published." },
  { s: "redbubble", n: "Redbubble (marketplace)", k: "pod", r: "INTL", pi: "au", m: ["DTG"], v: "summary", nt: "Classic, Premium, Relaxed and V-neck tees and tanks fulfilled in AU by third parties. Blanks aren't named; can't print front and back on one item.", src: ["https://help.redbubble.com/hc/en-us/articles/217196086-Where-does-my-order-ship-from"] },
];

/* ------------------------------------------------- New Zealand printers */

const NZ: SeedSupplier[] = [
  {
    s: "digitees", n: "Digitees", k: "pod", r: "NZ", l: "New Zealand", pi: "nz", m: ["DTG", "DTF", "screen", "embroidery", "sublimation"],
    max: "Approx 40 × 45 cm (depends on style, size and position)", mw: 400, mh: 450, w: "https://digitees.co.nz", v: "summary",
    src: ["https://digitees.co.nz/page/help/artwork-design-files", "https://digitees.co.nz/shipping"],
    nt: "All orders printed in NZ; AU shipping NZ$23 for 1–2 items, 3–6 working days plus customs. Wide AS Colour tank, crop and V-neck range.",
    o: { "5026": { st: "yes", pi: "nz", max: "~40 × 45 cm", mw: 400, mh: 450, p: "DTG printed from NZ$43.00 (print size not stated)", src: "https://digitees.co.nz/blank_product/55362827/AS-Colour-Mens-Classic-Tee", v: "summary" }, "5025": { st: "yes", pi: "nz", v: "summary" }, "4062": { st: "yes", pi: "nz", v: "summary" } },
  },
  {
    s: "printpoppa", n: "Printpoppa", k: "pod", r: "NZ", l: "Henderson, Auckland", pi: "nz", m: ["DTG", "DTF", "screen"], w: "https://www.printpoppa.co.nz", v: "summary",
    src: ["https://www.printpoppa.co.nz/shipping"], nt: "Tracked courier NZ→AU NZ$20.13 for 1–3 items. 'Your first print on every garment is Free!'",
    o: { "5026": { st: "yes", pi: "nz", p: "Printed from NZ$36.65", src: "https://www.printpoppa.co.nz/blank_product/210266843/AS-Colour-CLASSIC-TEE?c=41903", v: "summary" } },
  },
  {
    s: "printmighty", n: "PrintMighty", k: "pod", r: "NZ", l: "Paraparaumu", pi: "nz", max: "400 × 500 mm (every product)", mw: 400, mh: 500, w: "https://printmighty.co.nz", v: "summary",
    src: ["https://printmighty.co.nz/designer", "https://printmighty.co.nz/shipping-info"], nt: "International by NZ Post Airmail, 2–5 weeks; Australia not named.",
    o: { "5026": { st: "yes", pi: "nz", max: "400 × 500 mm", mw: 400, mh: 500, p: "NZ$37.00 incl GST, excl shipping (print inclusion not stated)", v: "summary" }, "5025": { st: "yes", pi: "nz", v: "summary" }, "4062": { st: "yes", pi: "nz", v: "summary" } },
  },
];

/* --------------------------------------------------- Australian print shops */

type ShopArgs = Omit<SeedSupplier, "k" | "pi"> & { pi?: PrintRegion; k?: SupplierKind };
const shop = (a: ShopArgs): SeedSupplier => ({ k: "print_shop", pi: "au", v: "summary", ...a });

const QLD: SeedSupplier[] = [
  shop({ s: "custom-t-shirt-printing-online", n: "Custom T-Shirt Printing Online", r: "QLD", l: "12 Mumbil St, Stafford Heights, Brisbane (also Melbourne)", m: ["DTG", "DTF", "screen"], min: "No DTG minimum stated; screen 100+", w: "https://customtshirtprintingonline.com.au",
    src: ["https://customtshirtprintingonline.com.au/blank_product/64730618/Mens-Classic-Tee", "https://customtshirtprintingonline.com.au/blank_product/209193668/Short-Sleeve-Tee"],
    nt: "One of few shops listing both 5026 and 1717. 5001 one side $29.95, two sides $42.05; 5026 price only after configuring.",
    o: { "5026": { st: "yes", pi: "au", v: "summary" }, "1717": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "screenlab", n: "Screenlab", r: "QLD", l: "Nerang, Gold Coast (try-on showroom in Prahran VIC)", m: ["DTF", "screen"], min: "No minimums", mq: 1, w: "https://screenlab.co",
    src: ["https://order.screenlab.co/product/classic-tee-5026/", "https://screenlab.co/faqs/"], nt: "Doesn't print customer-supplied blanks. A search summary claimed a 35 × 45 cm max; not found on its page.",
    o: { "5026": { st: "yes", pi: "au", p: "$35.00 incl one-sided print (size not stated)", v: "summary" }, "1717": { st: "yes", pi: "au", v: "summary", nt: "Mentioned in its FAQ." }, "5025": { st: "yes", pi: "au", p: "$30", v: "summary" } } }),
  shop({ s: "thread-cred", n: "Thread Cred", r: "QLD", l: "1/11 Natasha St, Capalaba", m: ["screen", "DTG", "sublimation", "embroidery"], max: "Screen: 'up to 900mm x 650mm'; all-over tee 110 × 85 cm", w: "https://www.threadcred.com.au", src: ["https://www.threadcred.clothing/page/quotes/screen-printing"], nt: "The screen and all-over figures are print-bed sizes, not a normal chest print, so they're not used for ranking." }),
  shop({ s: "t-base", n: "T Base", r: "QLD", l: "Sunshine Plaza, Maroochydore", m: ["DTG", "HTV"], max: "'up to 350mm x 400mm in size' (DTG)", mw: 350, mh: 400, w: "https://www.tbase.com.au", src: ["https://www.tbase.com.au/pages/customs-price-list"], nt: "Custom tee front $49.95, front and back $64.95 (AS Colour, model not given)." }),
  shop({ s: "so-boss", n: "So Boss", r: "QLD", l: "Griffin QLD & Leumeah NSW", m: ["DTG", "DTF", "screen"], min: "No minimums", mq: 1, w: "https://www.soboss.co", nt: "From $29 on AS Colour Basic; DTG from $24.95 for one item." }),
  shop({ s: "monstees", n: "Monstees Custom Printing", r: "QLD", l: "Garbutt, Townsville", m: ["DTG", "DTF", "HTV", "screen", "embroidery", "sublimation"], w: "https://monstees.com.au", o: { "5026": { st: "yes", pi: "au", p: "$32.00 blank", src: "https://monstees.com.au/product/as-colour-classic-tee-5026/", v: "summary" } } }),
  shop({ s: "red-octopus", n: "Red Octopus Custom Print", r: "QLD", l: "11 Maud St, Newstead", m: ["screen", "embroidery", "digital transfers", "sublimation"], min: "Custom quoted", w: "https://redoctopus.com.au", nt: "Shows the Comfort Colors logo; same address as The Tshirt Mill.", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "xpress-tees", n: "Xpress Tees", r: "QLD", l: "Surfers Paradise & Ashmore", m: ["DTF", "HTV", "DTG", "screen", "embroidery"], min: "No minimum orders", mq: 1, w: "https://xpresstees.com.au", nt: "Accepts customer-supplied garments." }),
  shop({ s: "the-screen-house", n: "The Screen House", r: "QLD", l: "Burleigh Heads", m: ["screen (8-colour)", "DTG", "embroidery"], min: "25 (1–2 colours), 50+ (3–4), 100+ (5–8)", mq: 25, w: "https://www.thescreenhouse.com.au" }),
  shop({ s: "print-n-wear", n: "Print n Wear", r: "QLD", l: "Currumbin", m: ["screen", "DTG", "embroidery"], min: "Screen: minimum 15 prints", mq: 15, w: "https://www.printnwear.com.au" }),
  shop({ s: "heaps-good-merch", n: "Heaps Good Merch", r: "QLD", l: "Ashmore", m: ["screen", "embroidery"], w: "https://heapsgoodmerch.com.au", v: "not_published" }),
  shop({ s: "drk-lbl", n: "DRK LBL", r: "QLD", l: "Gold Coast", m: ["screen", "embroidery", "retail finishing"], min: "From 50", mq: 50, w: "https://www.drklbl.com.au" }),
  shop({ s: "mesh-impressions", n: "Mesh Impressions", r: "QLD", l: "Moffat Beach", m: ["screen", "DTF"], w: "https://www.meshimpressions.au", v: "not_published" }),
  shop({ s: "scream-print", n: "Scream Print Screen Printing", r: "QLD", l: "Mudjimba", m: ["screen", "DTF", "embroidery"], min: "Screen ideal 20+", w: "https://www.screamprintscreenprinting.com" }),
  shop({ s: "doree", n: "Doree", r: "QLD", l: "Upper Mount Gravatt", m: ["DTG", "screen", "embroidery"], w: "https://www.doree.com.au", nt: "Shop lists AS Colour 5001, 5051, 5080, crop 4062; 5026 not seen.", o: { "5080": { st: "yes", pi: "au", v: "summary" }, "4062": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "lee-t-shirts", n: "Lee T-Shirts", r: "QLD", l: "Geebung", m: ["screen", "embroidery", "sublimation"], min: "15 per design", mq: 15, w: "https://www.leetshirts.com.au", nt: "No customer garments; Comfort Colors not in its brand list.", o: { "1717": { st: "no", v: "summary" } } }),
  shop({ s: "sunprints", n: "SunPrints", r: "QLD", l: "Underwood", m: ["DTF", "screen", "embroidery", "sublimation"], w: "https://www.sunprints.com.au", v: "not_published" }),
  shop({ s: "distinct-edge", n: "Distinct Edge", r: "QLD", l: "Archerfield", m: ["embroidery", "screen", "DTG"], w: "https://www.distinctedge.com.au", v: "not_published" }),
  shop({ s: "northside-print", n: "Northside Print & Design", r: "QLD", l: "Brisbane", m: ["screen", "DTF"], min: "Pricing from quantity 1", mq: 1, w: "https://shop.northsideprint.com.au" }),
  shop({ s: "we-print-shirts", n: "We Print Shirts", r: "QLD", l: "Brisbane", m: ["screen", "DTF", "DTG", "embroidery"], w: "https://weprintshirts.com.au", v: "not_published" }),
  shop({ s: "vc-clothing", n: "VC Clothing", r: "QLD", l: "Brisbane home studio", m: ["screen"], w: "https://vcclothing.com", v: "not_published" }),
  shop({ s: "northprint", n: "Northprint", r: "QLD", l: "Toowoomba", m: ["screen", "DTF", "embroidery"], min: "MOQ of only 4", mq: 4, w: "https://northprint.com.au" }),
  shop({ s: "sportstar", n: "Sportstar Screenprinting", r: "QLD", l: "Toowoomba", m: ["screen", "embroidery", "sublimation"], w: "https://www.sportstarscreenprinting.com.au", v: "not_published" }),
  shop({ s: "prime-print", n: "Prime Print", r: "QLD", l: "Currajong, Townsville", m: ["DTG", "screen", "embroidery", "sublimation"], min: "From one shirt", mq: 1, w: "https://www.primeprint.com.au" }),
  shop({ s: "complete-tag", n: "Complete TAG Solutions", r: "QLD", l: "Aitkenvale, Townsville", m: ["screen", "embroidery"], w: "https://www.completetagsolutions.com.au", v: "not_published" }),
  shop({ s: "nq-print-co", n: "NQ Print Co", r: "QLD", l: "Cairns Northern Beaches", m: ["screen", "digital", "DTF"], w: "https://www.nqprintco.com.au", v: "not_published" }),
  shop({ s: "hello-merch", n: "Hello Merch", r: "QLD", l: "Maroochydore", m: ["screen", "embroidery", "DTF", "DTG"], w: "https://hellomerch.com.au", v: "not_published" }),
  shop({ s: "silk-and-squeeg", n: "Silk and Squeeg", r: "QLD", l: "3/39 Corunna St, Albion", m: ["screen", "DTF", "embroidery"], min: "Screen 20; DTF none", mq: 1, max: "Screen 35 × 45 cm; DTF 36 × 46 cm", mw: 360, mh: 460, w: "https://silkandsqueeg.com", src: ["https://silkandsqueeg.com/printing-and-embroidery-service-brisbane"], nt: "Can work with customer-supplied garments." }),
  shop({ s: "shopace", n: "ShopAce", r: "QLD", l: "Redbank", m: ["screen", "DTF", "sublimation", "embroidery"], min: "No MOQ; DTF from 1", mq: 1, w: "https://shopace.com.au" }),
  shop({ s: "lifestyle-australia", n: "Lifestyle Australia", r: "QLD", l: "Gold Coast", m: ["screen", "embroidery", "digital heat transfer", "Supacolour"], min: "Page says both 25 and 50 per design", mq: 25, w: "https://lifestyleaustralia.com.au", nt: "Screen + warehousing, drop shipping, swing tags, relabelling." }),
  shop({ s: "the-print-studio", n: "The Print Studio", r: "QLD", l: "16/48 Hutchinson St, Burleigh Heads", m: ["screen", "DTG", "DTF", "embroidery"], min: "5 garments per design", mq: 5, max: "DTG oversized 39 × 49 cm", mw: 390, mh: 490, w: "https://theprintstudio.com.au",
    src: ["https://theprintstudio.com.au/custom-dtg-printing/", "https://theprintstudio.com.au/product/as-colour-classic-tee-5026/"],
    o: { "5026": { st: "yes", pi: "au", max: "DTG oversized 39 × 49 cm", mw: 390, mh: 490, p: "$13.90 + GST blank; DTG oversized $23 per position (5–9 units, ex GST) + $65 setup", mq: 5, v: "summary" } } }),
  shop({ s: "the-tshirt-mill", n: "The Tshirt Mill", r: "QLD", l: "11 Maud St, Newstead", m: ["DTF", "digital", "screen", "embroidery", "Supacolour"], min: "No minimum — print from a single tee", mq: 1, max: "35 × 50 cm, up to 40 × 50 cm depending on garment (DTF online orders)", mw: 350, mh: 500, w: "https://thetshirtmill.com.au", i: "Shopify integration",
    src: ["https://thetshirtmill.com.au/blank_product/40554937/Classic-Tee"],
    o: { "5026": { st: "yes", pi: "au", max: "35 × 50 cm", mw: 350, mh: 500, v: "summary" }, "1717": { st: "yes", pi: "au", p: "As low as $26.10* (print inclusion unclear)", v: "summary" } } }),
  shop({ s: "the-t-shirt-co", n: "The T-Shirt Co", r: "QLD", l: "Kedron, Brisbane", m: ["DTG", "DTF"], min: "No minimums or setup fees", mq: 1, max: "35 cm W × 45 cm H (resized to garment size)", mw: 350, mh: 450, w: "https://thetshirtco.com.au",
    src: ["https://thetshirtco.com.au/products/classic-tee-custom-printed-as-colour"],
    o: { "5026": { st: "yes", pi: "au", max: "35 × 45 cm", mw: 350, mh: 450, p: "$31.95 incl one print (sale; $34.95 regular); both sides +$10", pc: 3195, v: "summary" }, "1717": { st: "yes", pi: "au", p: "$29.95 incl one print", pc: 2995, src: "https://thetshirtco.com.au/products/unisex-comfort-colours-tee-custom-printed-same-day", v: "summary" }, "5025": { st: "yes", pi: "au", v: "summary", nt: "On request." } } }),
  shop({ s: "tshirts-australia", n: "T Shirts Australia (was Custom T Shirt Shop)", r: "QLD", l: "Coorparoo", m: ["screen", "DTG"], w: "https://tshirtsaustralia.au/custom/", nt: "A search snippet claimed 35 × 40 cm max and $15 per area; those pages now 404. AS Colour men's tee from $45.95." }),
];

const NSW_ACT: SeedSupplier[] = [
  shop({ s: "create-apparel", n: "Create Apparel", r: "NSW", l: "52a Hampstead Rd, Auburn", m: ["DTF", "DTG", "screen", "embroidery"], min: "DTF/DTG from 1; screen minimums apply; embroidery 12", mq: 1, w: "https://www.createapparel.com.au", src: ["https://www.createapparel.com.au/create/Comfort-Colors?c=6645358"], nt: "Runs MerchSprint. Bulk discounts 5% at 5+ up to 25% at 50+.",
    o: { "5026": { st: "yes", pi: "au", src: "https://www.createapparel.com.au/blank_product/208953063/5026-Men-s-Classic-Tee", v: "summary" }, "1717": { st: "yes", pi: "au", v: "summary", nt: "Listed for printing, not sold blank." } } }),
  shop({ s: "garment-printing", n: "Garment Printing", r: "NSW", l: "2/7 Anella Ave, Castle Hill", m: ["DTG", "screen", "DTF", "embroidery", "sublimation", "puff", "foil"], min: "DTG/vinyl/transfers none; screen 25; embroidery 5", mq: 1, max: "'Images can be printed up to 35cm x 45cm'", mw: 350, mh: 450, w: "https://garmentprinting.com.au",
    src: ["https://garmentprinting.com.au/page/help/frequently-asked-questions"], nt: "Same address as T-Shirt Plus.",
    o: { "5026": { st: "yes", pi: "au", p: "Printing from $35.75*", v: "summary" }, "1717": { st: "yes", pi: "au", v: "summary", nt: "Comfort Colours page: no minimum." }, "5025": { st: "yes", pi: "au", v: "summary" }, "4062": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "t-shirt-plus", n: "T-Shirt Plus", r: "NSW", l: "2/7 Anella Ave, Castle Hill", m: ["DTG", "screen", "DTF", "vinyl", "embroidery", "sublimation"], min: "No minimum", mq: 1, max: "13.78 × 15.75 in (from its designer settings)", mw: 350, mh: 400, w: "https://tshirtplus.com.au", src: ["https://tshirtplus.com.au/page/print-on-demand"], nt: "Same address as Garment Printing.",
    o: { "5026": { st: "yes", pi: "au", p: "Printing from $41.12*", v: "summary" }, "1717": { st: "yes", pi: "au", v: "summary" }, "5025": { st: "yes", pi: "au", v: "summary" }, "4062": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "arcade-screen-printing", n: "Arcade Screen Printing", r: "NSW", l: "St Peters, Sydney", m: ["screen", "DTG", "transfers", "vinyl"], min: "DTG minimum 5 per design and style", mq: 5, std: "'generally 28 – 30cm wide'", max: "Full-size skater print 30 cm W × 50 cm H", mw: 300, mh: 500, w: "https://arcadescreenprinting.com.au", src: ["https://arcadescreenprinting.com.au/faq/"], o: { "5026": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "made-in", n: "Made-in", r: "NSW", l: "29 Sydney St, Marrickville", m: ["screen", "digital", "embroidery"], min: "20 units", mq: 20, w: "https://made-in.com.au", o: { "5026": { st: "brand_only", pi: "au", v: "summary" }, "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "ssprint", n: "SSPRINT (formerly Ssweatshop)", r: "NSW", l: "Marrickville", m: ["screen", "digital hybrid", "embroidery"], min: "50", mq: 50, w: "https://www.ssprint.com.au", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "asyd-printing", n: "ASYD Printing", r: "NSW", l: "St Peters", m: ["screen", "embroidery", "heat press"], min: "Low minimums", w: "https://asydprinting.com", o: { "5026": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "pro-garment-printers", n: "Pro Garment Printers", r: "NSW", l: "Peakhurst", m: ["screen", "DTF", "heat transfer"], min: "DTF from 1; screen 20–25", mq: 1, w: "https://progarmentprinters.au", nt: "DTF from $22 per piece at 10.", o: { "5026": { st: "yes", pi: "au", v: "summary" }, "5025": { st: "yes", pi: "au", v: "summary" }, "4062": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "halo-print-co", n: "Halo Print Co", r: "NSW", l: "St Peters", m: ["DTG", "screen", "DTF", "embroidery"], min: "DTG no minimum; screen 25+", mq: 1, w: "https://haloprintco.com" }),
  shop({ s: "24-hour-merchandise", n: "24 Hour Merchandise", r: "NSW", l: "Marrickville", m: ["digital", "screen", "embroidery", "sublimation"], min: "Digital 1; screen 15", mq: 1, max: "'The absolute maximum Print size we can do is 35 cm wide by 40 cm.'", mw: 350, mh: 400, w: "https://24hourmerchandise.com.au", src: ["https://24hourmerchandise.com.au/page/information/faqs"], o: { "5026": { st: "yes", pi: "au", max: "35 × 40 cm", mw: 350, mh: 400, v: "summary" }, "5025": { st: "yes", pi: "au", v: "summary" }, "4062": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "fresh-tees", n: "Fresh Tees", r: "NSW", l: "Marrickville & Newcastle", m: ["screen", "DTF", "DTG", "embroidery"], min: "Screen 25; DTG none", mq: 1, w: "https://freshtees.com.au", o: { "5026": { st: "yes", pi: "au", p: "$36 incl one print (size not stated)", v: "summary" }, "4062": { st: "yes", pi: "au", p: "$30", v: "summary" } } }),
  shop({ s: "mabuzi", n: "Mabuzi", r: "NSW", l: "Camperdown", m: ["screen", "DTG", "DTF", "embroidery"], min: "Low minimums possible", w: "https://mabuzi.com", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "the-print-hq", n: "The Print HQ", r: "NSW", l: "Yennora", m: ["DTG", "DTF", "screen", "embroidery"], min: "No minimum", mq: 1, w: "https://theprinthq.com.au" }),
  shop({ s: "araca-ink", n: "Araca Ink", r: "NSW", l: "Marrickville", m: ["digital", "screen", "embroidery"], min: "26 per style", mq: 26, std: "A4 print option", sw: 210, sh: 297, max: "A3 print option", mw: 297, mh: 420, w: "https://www.aracaink.com.au",
    o: { "5026": { st: "yes", pi: "au", ...A4, max: "A3", mw: 297, mh: 420, src: "https://www.aracaink.com.au/pd-as-colour-classic-tee.cfm", v: "summary" }, "1717": { st: "yes", pi: "au", max: "A3 on black and colour garments", mw: 297, mh: 420, src: "https://www.aracaink.com.au/pd-comfort-colours-1717-cc-unisex-short-sleeve-tee---s-xl.cfm", v: "summary" } } }),
  shop({ s: "flag-banner", n: "Flag Banner", r: "NSW", l: "Guildford", m: ["screen"], min: "Not stated; $50+GST setup per job", std: "Front up to A4", sw: 210, sh: 297, max: "Back up to A3 (stated as 28 × 40 cm)", mw: 280, mh: 400, w: "https://flagbanner.com.au",
    o: { "1717": { st: "yes", pi: "au", ...A4, max: "Back up to A3 28 × 40 cm (+$30)", mw: 280, mh: 400, p: "AU$24.95+GST blank; front A4 +$20, back A3 +$30; $50+GST setup", src: "https://flagbanner.com.au/comfort-colors-1717.html", v: "summary" } } }),
  shop({ s: "dot2dot-printing", n: "Dot2Dot Printing", r: "NSW", l: "Marrickville", m: ["DTG", "screen", "embroidery"], w: "https://dot2dotprinting.com.au", v: "not_published" }),
  shop({ s: "just-t-shirts", n: "Just T-Shirts", r: "NSW", l: "Sydney", m: ["screen", "DTG", "vinyl"], w: "https://justtshirts.com.au", v: "not_published" }),
  shop({ s: "occ-apparel", n: "OCC Apparel", r: "NSW", l: "Marrickville (+ Currumbin QLD)", m: ["screen"], w: "https://www.occapparel.com.au", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "julies-embroidery", n: "Julie's Embroidery", r: "NSW", l: "Brookvale", m: ["screen", "embroidery", "heat transfer"], w: "https://julies.info", v: "not_published" }),
  shop({ s: "hawkesbury-screen-printing", n: "Hawkesbury Screen Printing", r: "NSW", l: "North Richmond", m: ["screen", "DTF", "DTG", "embroidery", "sublimation"], min: "Screen 6; DTF/DTG none", mq: 1, w: "https://hawkesburyscreenprinting.com.au", nt: "A product page title lists 5026 — unconfirmed.", o: { "5026": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "onya-visuals", n: "Onya Visuals", r: "NSW", l: "Warners Bay", m: ["screen", "digital", "embroidery"], min: "10 items", mq: 10, w: "https://www.onyascreenprinting.com.au" }),
  shop({ s: "imsprint", n: "Imsprint", r: "NSW", l: "Metford", w: "https://www.imsprint.com.au", v: "not_published" }),
  shop({ s: "zulu-graphics", n: "Zulu Graphics", r: "NSW", l: "New Lambton", m: ["screen", "digital transfer", "embroidery"], w: "https://www.zulugraphics.com.au", v: "not_published" }),
  shop({ s: "newcastle-embroidery", n: "Newcastle Embroidery", r: "NSW", l: "Newcastle", m: ["screen", "DTG", "embroidery"], w: "https://www.newcastleembroidery.com.au", v: "not_published" }),
  shop({ s: "ckm-screen-printing", n: "CKM Screen Printing", r: "NSW", l: "West Gosford", m: ["screen", "embroidery"], w: "https://www.ckmscreenprinting.com.au", v: "not_published" }),
  shop({ s: "jetscreen", n: "Jetscreen", r: "NSW", l: "Unanderra, Wollongong", m: ["screen"], min: "10 shirts", mq: 10, w: "https://www.jetscreen.com.au", nt: "Example: 20 black tees, 2-colour front = $22.00 per shirt." }),
  shop({ s: "soft-power-studio", n: "Soft Power Studio", r: "NSW", l: "Albion Park Rail", m: ["screen", "embroidery"], min: "20 per design variation", mq: 20, max: "'maximum image size of 32cm wide and 42cm tall'", mw: 320, mh: 420, w: "https://www.softpowerstudio.com.au", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "ikke-printing", n: "IKKE Textile Design & Print", r: "NSW", l: "Bulli", m: ["screen", "DTF", "vinyl"], min: "Screen 10", mq: 10, w: "https://www.ikkeprinting.com.au" }),
  shop({ s: "pegasus-screenprints", n: "Pegasus Screenprints", r: "NSW", l: "Lismore", m: ["screen", "transfers", "sublimation"], min: "Single items up", mq: 1, w: "https://www.pegasusprint.com.au" }),
  shop({ s: "northern-rivers-embroidery", n: "Northern Rivers Embroidery", r: "NSW", l: "Byron Bay area", m: ["screen", "DTG", "embroidery"], w: "https://www.northernriversembroidery.com.au", v: "not_published" }),
  shop({ s: "wazzup", n: "Wazzup Screen Printing", r: "NSW", l: "Kirrawee", m: ["screen", "DTF", "embroidery", "fulfilment"], min: "Wholesale MOQ 10; e-commerce MOQ 1", mq: 1, w: "https://wazzup.au", nt: "White-label, drop shipping and fulfilment." }),
  shop({ s: "pistol-clothing", n: "Pistol Clothing", r: "NSW", l: "Arncliffe", m: ["screen", "DTG", "DTF", "embroidery"], min: "Screen 20; DTG/DTF 5", mq: 5, w: "https://pistolclothing.com.au", nt: "Accepts customer-supplied blanks.", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "ps-apparel", n: "PS Apparel", r: "NSW", l: "Port Stephens", m: ["screen (water-based)", "transfers", "embroidery", "sublimation"], min: "No minimum on most styles; screen best 24+", mq: 1, w: "https://psapparel.com.au", src: ["https://psapparel.com.au/shop/tees-singlets/t-shirts-tees-singlets/comfort-colors-adult-heavyweight-t-shirt-1717/"], nt: "Also sells blanks wholesale.",
    o: { "5026": { st: "yes", pi: "au", p: "$14.95 blank", v: "summary" }, "1717": { st: "yes", pi: "au", p: "$18.50 inc GST blank, 207 GSM, ~60 colours", v: "summary" } } }),
  shop({ s: "wowprints", n: "WowPrints", r: "NSW", l: "Villawood", m: ["screen", "DTG", "DTF", "Supacolor", "embroidery"], min: "25 per design (its pages disagree)", mq: 25, max: "Supacolor 'best kept under A3'", w: "https://wowprints.com.au", nt: "Uses AS Colour blanks; screen from $9.95/shirt at 50+." }),
  shop({ s: "the-grim-printer", n: "The Grim Printer", r: "NSW", l: "Brookvale (serves Gold Coast & Brisbane)", m: ["screen", "DTG", "DTF", "embroidery"], min: "Homepage 25 screen / 10 DTF-DTG; FAQ says 50", mq: 10, w: "https://thegrimprinter.com.au", nt: "25 shirts $22 each, 50 $17, 100 $14 (ex GST). One sweep reported 'XL: 42x30cm' without a source." }),
  shop({ s: "knight-shift", n: "Knight Shift", r: "ACT", l: "Mitchell", m: ["DTG", "DTF", "vinyl", "embroidery"], min: "Print on demand for digital", mq: 1, w: "https://knightshift.com.au" }),
  shop({ s: "rojo-merch-co", n: "ROJO Merch Co", r: "ACT", l: "Phillip", m: ["screen", "DTG", "transfers", "embroidery"], min: "Screen 20; others none", mq: 1, w: "https://rojomerchco.com.au" }),
  shop({ s: "capital-prints", n: "Capital Prints", r: "ACT", l: "Canberra", m: ["screen", "embroidery"], w: "https://capitalprints.com.au", o: { "5026": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "copperhead", n: "Copperhead Screen Printing", r: "ACT", l: "Canberra / Queanbeyan", m: ["screen", "DTG", "embroidery"], w: "https://copperhead.com.au", v: "not_published" }),
  shop({ s: "vivid-print", n: "Vivid Print", r: "ACT", l: "Fyshwick", w: "https://www.vividprint.com.au", v: "not_published" }),
  shop({ s: "inteliprint", n: "Inteliprint", r: "NSW", l: "Hamilton North", m: ["DTG"], max: "'Full Front/Back: 360w x 460h mm'", mw: 360, mh: 460, w: "https://inteliprint.com.au", o: { "5026": { st: "yes", pi: "au", max: "360 × 460 mm", mw: 360, mh: 460, src: "https://inteliprint.com.au/as-colour-5026-classic-tee-448/", v: "summary" } } }),
  shop({ s: "tshirtprinting-com-au", n: "T-Shirt Printing Australia (tshirtprinting.com.au)", r: "NSW", l: "35 Thomas St, Wallsend", m: ["screen", "DTG", "transfers", "embroidery"], min: "Online 1–20; quote 25+", mq: 1, w: "https://tshirtprinting.com.au", o: { "5026": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "t-shirt-hub", n: "T-Shirt Hub", r: "NSW", m: ["screen", "digital", "sublimation", "embroidery"], min: "No minimum", mq: 1, w: "https://tshirthub.com.au", nt: "Unbranded products only." }),
];

const VIC_TAS: SeedSupplier[] = [
  shop({ s: "printlocker", n: "PrintLocker", r: "VIC", l: "58 Phoenix St, Brunswick", m: ["digital", "DTF", "DTG", "screen", "embroidery"], min: "No minimums (screen 25)", mq: 1, max: "'Our maximum print area is 400mm wide x 500mm high'", mw: 400, mh: 500, w: "https://www.printlocker.com.au", src: ["https://www.printlocker.com.au/page/artwork-requirements"], nt: "Same address as Tee Junction.",
    o: { "5026": { st: "yes", pi: "au", max: "400 × 500 mm", mw: 400, mh: 500, p: "Digital print from $32.95*", v: "summary" }, "1717": { st: "yes", pi: "au", v: "summary", nt: "One sweep found 'Gildan Adult Comfort Colours Tee 1717' listed; another didn't." }, "5025": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "tee-junction", n: "Tee Junction", r: "VIC", l: "58 Phoenix St, Brunswick", m: ["DTF", "DTG", "screen", "embroidery"], min: "Digital none; screen 10", mq: 1, w: "https://teejunction.com.au", nt: "Sister business to OGO.", o: { "5026": { st: "yes", pi: "au", p: "Digital DTF from $32.95", v: "summary" }, "5025": { st: "yes", pi: "au", v: "summary" }, "4062": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "machine-screen-printers", n: "Machine Screen Printers", r: "VIC", l: "Pascoe Vale", m: ["screen", "embroidery", "transfers", "DTG"], min: "20 units", mq: 20, w: "https://machinescreenprinters.com.au", o: { "5026": { st: "yes", pi: "au", p: "$13.60 blank", mq: 20, v: "summary" }, "1717": { st: "yes", pi: "au", p: "$14.40 blank", mq: 20, v: "summary" }, "4062": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "house-of-uniforms", n: "House of Uniforms", r: "VIC", l: "Moorabbin", m: ["DTG", "DTF", "Supacolour", "embroidery"], min: "DTG: new artwork 12, repeat 1", mq: 12, max: "DTG 350 mm wide × 450 mm long", mw: 350, mh: 450, w: "https://shop.houseofuniforms.com.au", o: { "5026": { st: "yes", pi: "au", p: "POA", v: "summary" }, "1717": { st: "yes", pi: "au", p: "POA", v: "summary" } } }),
  shop({ s: "born-and-thread", n: "Born and Thread", r: "VIC", l: "Bayswater", m: ["screen", "DTF", "embroidery"], min: "10 (1 colour), 20 (2–4), 50 (5–6+); DTF 10", mq: 10, std: "Standard 280 × 380 mm (A3)", sw: 280, sh: 380, max: "Oversize 330 × 450 mm", mw: 330, mh: 450, w: "https://bornandthread.com", src: ["https://bornandthread.com/faqs/"], nt: "Labels, swing tags, bagging, stock holding, drop shipping.", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "das-t-shirt-automat", n: "Das T-Shirt Automat", r: "VIC", l: "Fitzroy, Kensington, Prahran, Preston", m: ["DTG", "DTF", "vinyl", "screen (50+)", "embroidery"], min: "No minimum", mq: 1, w: "https://dastshirtautomat.com.au", o: { "5026": { st: "yes", pi: "au", p: "Premium Tee (AS Colour Classic) from $29.50, white base", v: "summary" } } }),
  shop({ s: "screen-fiend", n: "Screen Fiend", r: "VIC", l: "Highett", m: ["screen", "embroidery", "heat transfers"], min: "25 prints", mq: 25, w: "https://screenfiend.com.au", o: { "5026": { st: "yes", pi: "au", v: "summary" }, "5080": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "tees-please", n: "Tees Please", r: "VIC", l: "Collingwood", m: ["DTG", "DTF", "screen", "embroidery", "puff"], min: "DTG/DTF none; screen 20", mq: 1, w: "https://teesplease.com.au", nt: "Supplies all garments; $19.95–$39.95 per shirt.", o: { "5026": { st: "yes", pi: "au", p: "$13.95 base", v: "summary" } } }),
  shop({ s: "edition-studio", n: "Edition Studio", r: "VIC", l: "Truganina & Altona North", m: ["printing", "embroidery"], max: "35 × 40 cm; oversize 40 × 45 cm on request", mw: 350, mh: 400, w: "https://editionstudio.com.au", src: ["https://editionstudio.com.au/page/artwork-requirements"], o: { "5026": { st: "yes", pi: "au", v: "summary", nt: "Per search result; product page returned 404." } } }),
  shop({ s: "melbourne-merch", n: "Melbourne Merch", r: "VIC", l: "Moorabbin", m: ["screen", "DTF", "embroidery"], min: "Screen 25; DTF none", mq: 1, w: "https://melbournemerch.com.au", nt: "Shows AS Colour 5001, 5101, 4001; screen setup $60/colour." }),
  shop({ s: "blast-ink", n: "Blast Ink", r: "VIC", l: "Melbourne", m: ["screen", "DTG", "embroidery"], min: "20 per design", mq: 20, max: "'Large print areas… no additional oversize screen-print charge' (no dimensions)", w: "https://blastink.com.au", nt: "Only prints garments it supplies." }),
  shop({ s: "all-of-the-above", n: "All of the Above", r: "VIC", l: "West Melbourne (+ Sydney)", m: ["screen", "embroidery"], min: "20 units", mq: 20, w: "https://alloftheabove.com.au" }),
  shop({ s: "australian-merch-co", n: "Australian Merch Co", r: "VIC", l: "Noble Park North", m: ["screen (12 colours)", "transfers", "embroidery"], min: "50 (up to 5 colours); own garments 25", mq: 50, w: "https://australianmerchco.com.au" }),
  shop({ s: "sunbury-printing", n: "Sunbury Printing", r: "VIC", l: "Sunbury", m: ["DTG", "screen", "vinyl"], w: "https://sunburyprinting.com.au", v: "not_published" }),
  shop({ s: "dtg-printing-melbourne", n: "DTG Printing Melbourne / Tee Print Centre", r: "VIC", l: "Melbourne", m: ["DTG", "screen"], min: "DTG no minimum", mq: 1, w: "https://dtgprinting.com.au" }),
  shop({ s: "2k-threads", n: "2K Threads", r: "VIC", l: "Springvale", m: ["DTF", "screen", "embroidery", "puff"], min: "DTF 1; screen 30", mq: 1, w: "https://2kthreads.com.au" }),
  shop({ s: "dead-set-threads", n: "Dead Set Threads", r: "VIC", l: "Lilydale", m: ["DTF"], min: "No minimums or setup fees", mq: 1, w: "https://deadsetthreads.com.au" }),
  shop({ s: "high-tee", n: "High Tee Screen Printing Co", r: "VIC", l: "West Footscray", m: ["screen", "embroidery", "DTF"], min: "Screen 20; DTF none", mq: 1, w: "https://highteescreenprinting.com.au" }),
  shop({ s: "teetees", n: "TeeTees", r: "VIC", l: "Brunswick", m: ["DTF"], min: "From 5", mq: 5, w: "https://teetees.com.au" }),
  shop({ s: "tee-it-up", n: "Tee It Up Screen Printing", r: "VIC", l: "Coburg North", m: ["screen (water-based)"], min: "25", mq: 25, w: "https://teeitupscreenprint.wixsite.com/website-1" }),
  shop({ s: "killer-merch", n: "Killer Merch", r: "VIC", l: "Coburg North", m: ["screen"], w: "https://killermerch.com.au", v: "not_published" }),
  shop({ s: "screenprint-concepts", n: "Screenprint Concepts", r: "VIC", l: "Melbourne", m: ["screen", "DTG", "DTF"], w: "https://screenprint-concepts.com", v: "not_published" }),
  shop({ s: "teesnow", n: "Teesnow", r: "VIC", l: "Oakleigh South", m: ["screen", "DTG", "vinyl"], min: "Screen 10; digital 1+", mq: 1, w: "https://teesnow.com.au" }),
  shop({ s: "fritz-print", n: "Fritz Print", r: "VIC", l: "Thomastown", m: ["screen (water-based)", "DTF", "embroidery"], min: "Screen 30; DTF under 30", mq: 1, w: "https://fritzprint.com.au", o: { "5080": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "while-you-sleep", n: "While You Sleep", r: "VIC", l: "Collingwood", m: ["screen (8 colours)", "embroidery"], min: "30 units", mq: 30, w: "https://whileyousleep.com.au", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "u-name-it", n: "U Name It", r: "VIC", l: "Bayswater & Cranbourne", m: ["screen", "heat transfer", "embroidery"], min: "No minimum", mq: 1, w: "https://unameit.com.au" }),
  shop({ s: "alfa-embroidery", n: "Alfa Embroidery", r: "VIC", l: "Knoxfield", m: ["DTF", "screen", "embroidery"], min: "DTF 10 per colourway", mq: 10, w: "https://alfaembroidery.com.au" }),
  shop({ s: "canopus-print", n: "Canopus Print", r: "VIC", l: "Dandenong South", m: ["DTF"], w: "https://canopusprint.com.au", v: "not_published" }),
  shop({ s: "fine-print-australia", n: "Fine Print Australia", r: "VIC", l: "Carrum Downs", m: ["digital"], min: "30", mq: 30, w: "https://fineprintaustralia.com" }),
  shop({ s: "senses-workwear", n: "Senses Workwear", r: "VIC", l: "Northcote", m: ["screen", "embroidery"], w: "https://sensesworkwear.com.au", v: "not_published" }),
  shop({ s: "banana-productions", n: "Banana Productions", r: "VIC", l: "Burwood", m: ["DTF", "heat transfer", "screen", "embroidery"], w: "https://bananaproductions.com.au", v: "not_published" }),
  shop({ s: "geelong-screenprinting", n: "Geelong Screenprinting", r: "VIC", l: "Grovedale", m: ["screen", "embroidery", "digital transfer"], min: "10", mq: 10, w: "https://geelongscreenprinting.com" }),
  shop({ s: "geetees", n: "Geelong Industrial Monogramming / GeeTees", r: "VIC", l: "Newtown, Geelong", m: ["DTF", "embroidery", "sublimation"], w: "https://geelongindustrialmonogramming.com.au", v: "not_published" }),
  shop({ s: "united-apparel", n: "United Apparel", r: "VIC", l: "Geelong", m: ["screen", "embroidery", "digital heat transfer"], min: "No minimum (10+ recommended)", mq: 1, w: "https://untd.com.au" }),
  shop({ s: "full-moon-printshop", n: "Full Moon Printshop", r: "VIC", l: "Moolap, Geelong", m: ["screen", "DTG", "DTF", "embroidery"], w: "https://fullmoonprintshop.com", v: "not_published", nt: "AS Colour Diamond Supplier." }),
  shop({ s: "premium-screen", n: "Premium Screen", r: "VIC", l: "Ballarat", m: ["screen", "DTG", "embroidery"], w: "https://premiumscreen.com.au", v: "not_published" }),
  shop({ s: "impact-teamwear", n: "Impact Teamwear", r: "VIC", l: "Ballarat", m: ["screen", "digital"], min: "20", mq: 20, w: "https://impactteamwear.com.au", nt: "No AS Colour; accepts customer garments." }),
  shop({ s: "bendigo-graphics", n: "Bendigo Graphics", r: "VIC", l: "Bendigo", m: ["DTF"], min: "No minimum (setup fee on singles)", mq: 1, w: "https://bendigographics.com" }),
  shop({ s: "platinum-prints", n: "Platinum Prints", r: "TAS", l: "Launceston", m: ["screen", "embroidery", "DTF"], min: "DTF no minimum", mq: 1, w: "https://platinumprints.com.au" }),
  shop({ s: "kbee-clothing", n: "KBee Clothing", r: "TAS", l: "Mowbray, Launceston", m: ["DTG", "HTV", "embroidery", "sublimation"], min: "No minimum", mq: 1, w: "https://kbeeclothing.com.au" }),
  shop({ s: "sim-branding", n: "SIM Branding / Graphic Tees Australia", r: "TAS", l: "Kings Meadows, Launceston", m: ["DTG", "embroidery"], min: "No minimum", mq: 1, w: "https://simbranding.com.au" }),
  shop({ s: "inkpot-studios", n: "Inkpot Studios", r: "TAS", l: "Hobart", m: ["screen (up to 6 spot colours)"], w: "https://inkpotstudios.com.au", nt: "Customer-supplied stock only." }),
  shop({ s: "tasmanian-clothing-company", n: "Tasmanian Clothing Company", r: "TAS", l: "Spreyton, Devonport", m: ["screen", "embroidery", "sublimation"], w: "https://tasclothing.com.au", v: "not_published" }),
  shop({ s: "uniform-city", n: "Uniform City", r: "TAS", l: "Hobart", w: "https://uniformcity.com.au", v: "not_published" }),
  shop({ s: "pumpkin-prints", n: "Pumpkin Prints", r: "TAS", l: "145 Davey St, Hobart", m: ["screen", "heat transfer", "DTG"], v: "not_published", nt: "Site failed to load; details from Facebook." }),
];

const WA_SA_NT: SeedSupplier[] = [
  shop({ s: "the-fabric-printer", n: "The Fabric Printer", r: "WA", l: "Osborne Park", m: ["DTG", "DTF", "screen", "embroidery"], min: "DTG/DTF none; screen 20", mq: 1, max: "DTG 360 × 450 mm; DTF & screen 380 × 480 mm", mw: 380, mh: 480, w: "https://fabricprinter.com.au", src: ["https://fabricprinter.com.au/pages/dtg-printing"], nt: "Doesn't print supplied stock; no dropship service. Full-colour tees from $30.49+GST.", o: { "5026": { st: "yes", pi: "au", p: "Quote only", v: "summary" } } }),
  shop({ s: "tee-shirt-republic", n: "Tee Shirt Republic", r: "WA", l: "Osborne Park", m: ["DTG", "DTF", "screen", "embroidery"], min: "Digital no minimum; screen 20", mq: 1, w: "https://teeshirtrepublic.com.au" }),
  shop({ s: "docuprint", n: "Docuprint", r: "WA", l: "Fremantle", m: ["DTF"], min: "1", mq: 1, max: "Up to A3", mw: 297, mh: 420, w: "https://docuprint.com.au", nt: "Own-brand blank; black tee front print $60 ($36 each at 6+)." }),
  shop({ s: "freo-t-shirts", n: "Freo T Shirts", r: "WA", l: "South Fremantle", m: ["DTG", "DTF"], min: "No minimum", mq: 1, w: "https://freotshirts.com.au", nt: "Custom printed AS Colour tee $65–70; back print $10–15." }),
  shop({ s: "t-bizz", n: "T-Bizz", r: "WA", l: "Osborne Park", m: ["DTF", "screen", "embroidery"], min: "Packages from 5", mq: 5, std: "A4 tier", sw: 210, sh: 297, max: "A3 tier", mw: 297, mh: 420, w: "https://t-bizz.com.au", o: { "5026": { st: "yes", pi: "au", p: "$16.80 ex GST blank", v: "summary" } } }),
  shop({ s: "as-design-and-print", n: "AS Design and Print", r: "WA", l: "Port Kennedy", m: ["DTF", "DTG", "embroidery"], w: "https://asdesignprint.com.au", v: "not_published" }),
  shop({ s: "uptempo-design", n: "Uptempo Design", r: "WA", l: "Bassendean", m: ["screen", "digital", "embroidery"], w: "https://uptempodesign.com.au", v: "not_published" }),
  shop({ s: "southern-cross-screen", n: "Southern Cross Screen Printing", r: "WA", l: "Bayswater", m: ["screen", "transfers", "embroidery"], w: "https://sxscreen.com.au", v: "not_published" }),
  shop({ s: "screen-printing-australia", n: "Screen Printing Australia", r: "WA", l: "Golden Bay", m: ["screen", "embroidery"], w: "https://screenprintingaustralia.com.au", v: "not_published" }),
  shop({ s: "id-athletic", n: "ID Athletic", r: "WA", l: "Osborne Park", m: ["screen"], min: "20+", mq: 20, w: "https://idathletic.com" }),
  shop({ s: "raza-group", n: "Raza Group", r: "WA", l: "Perth", m: ["screen", "DTF", "DTG"], w: "https://raza.com.au", v: "not_published" }),
  shop({ s: "luma-printing", n: "LUMA Printing", r: "WA", l: "Wangara", m: ["DTF", "screen", "vinyl", "embroidery"], min: "From 10", mq: 10, w: "https://lumaprinting.com.au" }),
  shop({ s: "short-batch", n: "Short Batch Printing Co.", r: "WA", l: "Rockingham", m: ["screen (hand)"], w: "https://shortbatch.com.au", v: "not_published" }),
  shop({ s: "wanneroo-uniforms", n: "Wanneroo Uniforms", r: "WA", l: "Wangara", m: ["screen", "transfers"], min: "6+", mq: 6, w: "https://wanneroouniforms.com.au" }),
  shop({ s: "flash-uniforms", n: "Flash Uniforms", r: "WA", l: "Wangara", m: ["screen", "DTF", "embroidery"], min: "Screen 11", mq: 11, w: "https://flashuniforms.com.au" }),
  shop({ s: "kings-workwear", n: "Kings Workwear", r: "WA", l: "Perth", m: ["DTF", "embroidery"], min: "4 garments", mq: 4, w: "https://kingsworkwear.com.au", nt: "Large back DTF $8–12 plus garment; $49 setup under 20." }),
  shop({ s: "noisy-pixel", n: "Noisy Pixel T-Shirts", r: "WA", l: "Perth", min: "No minimum orders", mq: 1, w: "https://noisypixeltshirts.com.au" }),
  shop({ s: "aess", n: "AESS", r: "SA", l: "Woodville SA & Malaga WA", m: ["screen", "DTG", "embroidery"], w: "https://australianess.com.au", v: "not_published" }),
  shop({ s: "hip-pocket-mandurah", n: "Hip Pocket Workwear", r: "WA", l: "Mandurah / Port Kennedy", m: ["screen", "vinyl", "embroidery"], v: "not_published" }),
  shop({ s: "bunbury-print", n: "Bunbury Print", r: "WA", l: "Bunbury", m: ["DTG"], min: "From 1", mq: 1, w: "https://bunburyprint.com.au" }),
  shop({ s: "river-design", n: "River Design", r: "WA", l: "Bunbury", m: ["screen"], min: "10", mq: 10, w: "https://riverdesign.net" }),
  shop({ s: "wicked-prints", n: "Wicked Prints", r: "WA", l: "Geraldton", m: ["DTG", "sublimation"], w: "https://wickedprints.com.au", v: "not_published" }),
  shop({ s: "the-print-parlour", n: "The Print Parlour", r: "SA", l: "Panorama", m: ["screen", "embroidery"], w: "https://theprintparlour.co", v: "not_published" }),
  shop({ s: "classic-colour-print-co", n: "Classic Colour Print Co", r: "SA", l: "Seaford Meadows", m: ["screen", "DTF", "embroidery"], min: "10 (can vary)", mq: 10, w: "https://classiccolourprintco.com.au" }),
  shop({ s: "worklocker-adelaide", n: "Worklocker Adelaide City", r: "SA", l: "Adelaide CBD", m: ["screen"], min: "10", mq: 10, w: "https://worklockeradelaidecity.com.au" }),
  shop({ s: "digimall", n: "DigiMall", r: "SA", l: "Kensington Park", m: ["DTG", "screen"], w: "https://digimall.com.au", v: "not_published" }),
  shop({ s: "norwood-screen-printers", n: "Norwood Screen Printers", r: "SA", l: "Kent Town", m: ["screen", "transfers", "embroidery"], w: "https://norwoodscreenprinters.com.au", v: "not_published" }),
  shop({ s: "the-printing-edge", n: "The Printing Edge", r: "SA", l: "Lonsdale", m: ["screen"], w: "https://theprintingedge.com.au", v: "not_published" }),
  shop({ s: "artoprint", n: "Artoprint", r: "SA", l: "Thebarton", m: ["screen", "DTG", "DTF", "vinyl", "embroidery"], w: "https://artoprint.com.au", v: "not_published" }),
  shop({ s: "2k-embroidery", n: "2K Embroidery", r: "SA", l: "Wingfield", m: ["screen", "DTF", "DTG", "embroidery"], w: "https://2kembroidery.com.au", v: "not_published" }),
  shop({ s: "uniform-me", n: "Uniform Me", r: "SA", l: "Edinburgh", m: ["screen", "embroidery", "sublimation"], w: "https://uniformme.com.au", v: "not_published" }),
  shop({ s: "ssp-adl", n: "SSP.ADL (Subterraneous)", r: "SA", l: "Adelaide", m: ["screen", "embroidery"], w: "https://subterraneous.com.au", v: "not_published" }),
  shop({ s: "deenz", n: "Deenz", r: "SA", l: "Adelaide (Victorian phone number)", m: ["screen", "DTF"], w: "https://deenz.com.au", v: "not_published" }),
  shop({ s: "printibly", n: "Printibly", r: "SA", l: "Hampstead Gardens, Adelaide", m: ["DTF"], min: "None", mq: 1, w: "https://printibly.com.au", i: "Online store", o: { "5026": { st: "yes", pi: "au", p: "$14.70 tee + $11.95 one print location (front+back $23.95)", src: "https://printibly.com.au/products/classic-tee-5026", v: "summary" }, "1717": { st: "no", v: "summary" }, "5025": { st: "yes", pi: "au", v: "summary" } } }),
  shop({ s: "teeshub", n: "TeesHub", r: "NT", l: "Casuarina & Palmerston", m: ["DTF", "embroidery"], w: "https://teeshub.com.au", nt: "Custom tees $45–65.", o: { "1717": { st: "brand_only", pi: "au", v: "summary" } } }),
  shop({ s: "moogully", n: "Moogully", r: "NT", l: "Winnellie", m: ["screen", "embroidery", "sublimation"], w: "https://moogully.com.au", v: "not_published" }),
  shop({ s: "cyan-print", n: "Cyan Print", r: "NT", l: "Yarrawonga", w: "https://cyanprint.com.au", o: { "1717": { st: "yes", pi: "au", p: "From $15.75", src: "https://cyanprint.com.au/products/brands/comfort-colours", v: "summary" } } }),
  shop({ s: "ausdesigns", n: "Ausdesigns", r: "NT", l: "Yarrawonga", m: ["screen", "digital", "embroidery"], v: "not_published" }),
  shop({ s: "officeworks", n: "Officeworks", r: "AU", l: "National", m: ["DTG"], max: "355 × 406.5 mm (4193 × 4800 px)", mw: 355, mh: 406, w: "https://www.officeworks.com.au/print-copy/p/t-shirt-printing-pcaptshcp", nt: "Unbranded tees only, from $24.95.", o: { "5026": { st: "no", v: "summary" } } }),
  shop({ s: "vistaprint-au", n: "Vistaprint AU", r: "AU", pi: "unknown", m: ["DTG", "screen", "embroidery", "heat transfer"], min: "DTG none; screen 6", mq: 1, w: "https://www.vistaprint.com.au", o: { "5026": { st: "brand_only", pi: "unknown", v: "summary" } } }),
];

/* ---------------------------------------------------- transfers & blanks */

const TRANSFERS: SeedSupplier[] = [
  { s: "dtf-transfers-australia", n: "DTF Transfers Australia", k: "transfers", r: "QLD", l: "Brisbane", pi: "au", m: ["DTF transfers"], min: "No minimums", mq: 1, max: "35 × 40 cm transfer", mw: 350, mh: 400, w: "https://dtftransfers.au", v: "summary", nt: "Transfers only — you press them. $19.50 per 35 × 40 transfer." },
  { s: "supacolor", n: "Supacolor", k: "transfers", r: "INTL", pi: "unknown", m: ["transfers"], max: "Largest template 11.7 × 16.5 in (A3)", mw: 297, mh: 419, w: "https://supacolor.com/pages/templates", v: "summary" },
  { s: "dtf-direct", n: "DTF Direct", k: "transfers", r: "QLD", l: "Newstead", pi: "au", m: ["DTF", "UV DTF"], min: "No minimums", mq: 1, w: "https://dtfdirect.com.au", v: "summary", nt: "Transfers from $2.50; gang sheet from $39.95." },
  { s: "dtf-hub", n: "DTF Hub", k: "transfers", r: "VIC", l: "Bayswater", pi: "au", m: ["DTF transfers"], w: "https://dtfhub.com.au", v: "summary", nt: "Transfers only, up to 58 cm wide." },
  { s: "perth-dtf-printing", n: "Perth DTF Printing", k: "transfers", r: "WA", l: "Osborne Park", pi: "au", m: ["DTF transfers"], w: "https://perthdtfprinting.com.au", v: "summary", nt: "Gang sheets 1–5 m, from $24/m; pressing offered." },
];

const WHOLESALERS: SeedSupplier[] = [
  { s: "gildan-brands-australia", n: "Gildan Brands Australia", k: "wholesaler", r: "NSW", l: "Sydney warehouse", pi: "unknown", w: "https://gildanbrands.com.au", v: "summary", nt: "Official Comfort Colors source in AU. Also 9360 tank, 3023CL women's boxy tee.", o: { "1717": { st: "yes", pi: "unknown", p: "$24.95–$27.45 blank, 68 colours, S–4XL", src: "https://gildanbrands.com.au/comfort-colors-1717/", v: "summary" } } },
  { s: "uniform-wholesalers", n: "Uniform Wholesalers", k: "wholesaler", r: "AU", l: "Sydney & Melbourne warehouses", pi: "unknown", w: "https://uniformwholesalers.com.au", v: "summary", o: { "1717": { st: "yes", pi: "unknown", p: "$18.00 blank", src: "https://uniformwholesalers.com.au/collections/comfort-colors", v: "summary" } } },
  { s: "t-shirt-wholesalers", n: "T Shirt Wholesalers", k: "wholesaler", r: "AU", pi: "unknown", w: "https://tshirtwholesalers.com.au", v: "summary", o: { "1717": { st: "yes", pi: "unknown", p: "$19.00 blank", src: "https://tshirtwholesalers.com.au/collections/comfort-colors", v: "summary" } } },
  { s: "alice-clothing", n: "Alice Clothing / Ausia Agencies", k: "wholesaler", r: "WA", l: "Perth (B2B)", pi: "unknown", w: "https://aliceclothing.com.au", v: "summary", o: { "1717": { st: "yes", pi: "unknown", p: "$15.50 ex GST blank, 47 colours", v: "summary" } } },
  { s: "premium-blanks-australia", n: "Premium Blanks Australia", k: "wholesaler", r: "AU", pi: "unknown", w: "https://premiumblanksaustralia.com", v: "summary", src: ["https://premiumblanksaustralia.com/products/black-premium-heavy-weighted-tee"], nt: "250 GSM 100% cotton heavyweight blank. Found 26 Sep 2026; not yet researched.", o: { "pba250": { st: "yes", pi: "unknown", src: "https://premiumblanksaustralia.com/products/black-premium-heavy-weighted-tee", v: "summary" } } },
  { s: "create-fashion-brand", n: "Create Fashion Brand", k: "wholesaler", r: "AU", pi: "unknown", w: "https://createfashionbrand.com", v: "summary", src: ["https://createfashionbrand.com/product-category/t-shirts-blanks/t-shirts-250-gsm-oversized-box-clothing-blanks/"], nt: "250 GSM oversized boxy blanks; clothing manufacturer. Not yet researched." },
];

/* ------------------------------------------------ overseas print-on-demand */

type OvArgs = Omit<SeedSupplier, "k" | "pi" | "r"> & { r?: string; pi?: PrintRegion };
const ov = (a: OvArgs): SeedSupplier => ({ k: "pod", r: "INTL", pi: "overseas", v: "summary", ...a });

const OVERSEAS: SeedSupplier[] = [
  ov({ s: "gelato", n: "Gelato", pi: "unknown", m: ["DTG", "DTF", "embroidery"], min: "No minimums", mq: 1, w: "https://www.gelato.com/au", nt: "Local production network; print area only in the logged-in dashboard.", o: { "5026": { st: "yes", pi: "unknown", p: "From A$97.51 / A$100.25 (its listings disagree)", v: "summary" }, "1717": { st: "yes", pi: "overseas", p: "From A$22.09–28.17; 'produced in US'", v: "summary" } } }),
  ov({ s: "printway", n: "Printway", pi: "unknown", m: ["DTG", "DTF"], w: "https://printway.io", o: { "5001": { st: "yes", pi: "au", p: "US$11.46; AU shipping $6.99, 7–10 working days", v: "summary" }, "1717": { st: "yes", pi: "overseas", p: "US$11.28 (DTG, US)", v: "summary" }, "5026": { st: "no", v: "summary" } } }),
  ov({ s: "prodigi", n: "Prodigi", pi: "unknown", m: ["DTG"], w: "https://www.prodigi.com", o: { "5001": { st: "yes", pi: "au", p: "From A$19.00 ex tax & shipping", v: "summary" }, "1717": { st: "yes", pi: "overseas", v: "summary", nt: "Ships to the US only." }, "5026": { st: "no", v: "summary" } } }),
  ov({ s: "fourthwall", n: "Fourthwall", pi: "unknown", m: ["DTG", "DTF", "embroidery", "screen"], w: "https://fourthwall.com", nt: "Partners in US, UK, EU and AU; print sizes only in the logged-in designer.", o: { "5026": { st: "yes", pi: "overseas", p: "From $19.57 (ships from US)", v: "summary" }, "1717": { st: "yes", pi: "overseas", p: "From $15.45", v: "summary" }, "4062": { st: "yes", pi: "au", p: "From $18.80", v: "summary" } } }),
  ov({ s: "spring", n: "Spring (ex-Teespring)", pi: "unknown", m: ["DTG", "screen"], nt: "Fulfilment partners include Australia; catalogue needs a login." }),
  ov({ s: "interestprint", n: "InterestPrint", pi: "au", nt: "Two AU factories; generic tee, front print only, $15.95 (file 960 × 1200 px @150 dpi)." }),
  ov({ s: "scalable-press", n: "Scalable Press", pi: "unknown", m: ["screen", "DTG", "embroidery"], nt: "Suppliers include Melbourne; AU routing not published.", o: { "1717": { st: "yes", pi: "unknown", v: "summary" }, "5026": { st: "no", v: "summary" } } }),
  ov({ s: "cloudprinter", n: "Cloudprinter", pi: "unknown", nt: "Network includes Australia; whether apparel is made there isn't published.", o: { "1717": { st: "yes", pi: "unknown", v: "summary" }, "5026": { st: "no", v: "summary" } } }),
  ov({ s: "tapstitch", n: "Tapstitch", pi: "unknown", m: ["DTG", "DTF", "embroidery"], nt: "Own blanks; AU orders show 'International Fulfillment'. RT0063 blank A$9.45 + A$4.68 per print frame." }),
  ov({ s: "gooten", n: "Gooten", m: ["DTF", "DTG"], max: "14 × 16 in (most tees)", mw: 356, mh: 406, nt: "AU delivery ~10 days from $10.49.", o: { "1717": { st: "yes", pi: "overseas", max: "14 × 16 in", mw: 356, mh: 406, p: "Volume pricing from $11.02", v: "summary" }, "5026": { st: "no", v: "summary" }, "5025": { st: "yes", pi: "overseas", v: "summary" } } }),
  ov({ s: "inkthreadable", n: "Inkthreadable", l: "Blackburn, UK", m: ["DTG", "DTF", "embroidery"], max: "32 × 50 cm front and back", mw: 320, mh: 500, o: { "5026": { st: "yes", pi: "overseas", max: "32 × 50 cm", back: "32 × 50 cm", mw: 320, mh: 500, p: "£14.82 incl VAT", v: "summary" }, "1717": { st: "yes", pi: "overseas", max: "32 × 50 cm", mw: 320, mh: 500, p: "£15.18", v: "summary" } } }),
  ov({ s: "apliiq", n: "Apliiq", l: "California & Philadelphia", m: ["DTG", "DTF", "screen", "embroidery"], max: "15 × 19 in (5026)", mw: 381, mh: 483, o: { "5026": { st: "yes", pi: "overseas", max: "15 × 19 in", back: "15 × 19 in", mw: 381, mh: 483, p: "US$36.54 incl 1 imprint, no minimums", v: "summary" }, "1717": { st: "yes", pi: "overseas", max: "14 × 19 in", back: "14 × 19 in", mw: 356, mh: 483, p: "US$28.76", v: "summary" }, "5025": { st: "yes", pi: "overseas", v: "summary" }, "4062": { st: "yes", pi: "overseas", v: "summary" } } }),
  ov({ s: "customcat", n: "CustomCat", l: "Detroit, US", o: { "1717": { st: "yes", pi: "overseas", max: "11.41 × 15.11 in", mw: 290, mh: 384, p: "US$14.39 (Lite) / $11.51 (Pro), 1 print included", v: "summary" }, "5026": { st: "no", v: "summary" } } }),
  ov({ s: "printonic", n: "Printonic", l: "Chatsworth, CA", m: ["DTG"], o: { "1717": { st: "yes", pi: "overseas", max: "15 × 17 in art size", mw: 381, mh: 432, p: "US$15.49–21.79", v: "summary" } } }),
  ov({ s: "printed-mint", n: "Printed Mint", l: "Phoenix, US", m: ["DTG", "DTF"], o: { "1717": { st: "yes", pi: "overseas", max: "4350 × 5400 px @300 (14.5 × 18 in)", mw: 368, mh: 457, p: "US$15.00 (two sides +$4.95)", v: "summary" } } }),
  ov({ s: "tshirtgang", n: "Tshirtgang", l: "Ajax, Ontario", m: ["DTG", "DTF"], o: { "1717": { st: "yes", pi: "overseas", max: "11 × 15 in front & back", mw: 279, mh: 381, p: "US$13.50 incl print", v: "summary" } } }),
  ov({ s: "swiftpod", n: "SwiftPOD", l: "US & Mexico", o: { "1717": { st: "yes", pi: "overseas", max: "14 × 16 in front & back", mw: 356, mh: 406, v: "summary" } } }),
  ov({ s: "gearment", n: "Gearment", l: "US", o: { "1717": { st: "yes", pi: "overseas", max: "4200 × 4800 px @300 (14 × 16 in)", mw: 356, mh: 406, p: "From US$13.00", v: "summary" } } }),
  ov({ s: "dreamship", n: "Dreamship", o: { "1717": { st: "yes", pi: "overseas", p: "US$12.79 (Basic)", v: "summary" } } }),
  ov({ s: "yoycol", n: "Yoycol", l: "China / US / EU", o: { "1717": { st: "yes", pi: "overseas", p: "US$6.69 + from $1.60 per placement", v: "summary" } } }),
  ov({ s: "bonfire", n: "Bonfire", max: "11.5 × 14 in", mw: 292, mh: 356, nt: "AU delivery 17–24 business days. Comfort Colors tee (style code not stated) base $23.90 at 5 sold." }),
  ov({ s: "fuel-pod", n: "Fuel", l: "Indianapolis", max: "14 × 16 in", mw: 356, mh: 406, nt: "Gildan 5000 $6.40 incl 1 print; no AS Colour or Comfort Colors." }),
  ov({ s: "live-ink", n: "Live Ink", l: "Bristol, UK", max: "DTG 40 × 45 cm; screen 37 × 47 cm", mw: 400, mh: 450 }),
  ov({ s: "t-pop", n: "T-Pop", l: "France", max: "30.5 × 40.5 cm", mw: 305, mh: 405, nt: "Own unbranded blanks, €11 incl print." }),
  ov({ s: "teemill", n: "Teemill", l: "UK", nt: "Own organic blanks only." }),
  ov({ s: "spreadconnect", n: "Spreadshirt / Spreadconnect", nt: "AU orders only from its US facilities." }),
  ov({ s: "swag-com", n: "Swag.com", nt: "Minimum 24; AS Colour 5001 only." }),
  ov({ s: "teelaunch", n: "teelaunch", l: "South Dakota", nt: "Own blanks; AU shipping $12.50 first item." }),
  ov({ s: "podpartner", n: "PODpartner", l: "Shenzhen", max: "Jumbo DTG up to 24 × 24 in", nt: "Own blanks only." }),
  ov({ s: "airventory", n: "Airventory", max: "60 × 60 cm", nt: "Own blanks only." }),
  ov({ s: "art-of-where", n: "Art of Where", l: "Montreal", nt: "Own unbranded tees." }),
  ov({ s: "contrado", n: "Contrado", l: "London", nt: "Own cut-and-sew garments, all-over print." }),
  ov({ s: "brandsky", n: "Brandsky", l: "Hamburg", nt: "'Up to 40 × 50 cm' per summary, unverified; own-range blanks." }),
  ov({ s: "customizingbox", n: "CustomizingBox", l: "Hangzhou" }),
  ov({ s: "printkk", n: "PrintKK", l: "China & US" }),
  ov({ s: "printy6", n: "Printy6", l: "China" }),
  ov({ s: "shineon", n: "ShineOn", l: "US" }),
  ov({ s: "completeful", n: "Completeful", l: "Louisiana" }),
  ov({ s: "print-melon", n: "Print Melon", l: "Irvine, CA" }),
  ov({ s: "mayzing", n: "Mayzing", l: "EU / UK / US" }),
  ov({ s: "printegy", n: "Printegy", l: "Essen, DE" }),
  ov({ s: "dreamprint", n: "DreamPrint", l: "Hannover, DE" }),
  ov({ s: "burgerprints", n: "Burgerprints", l: "US / EU / VN / CN" }),
  ov({ s: "printbelle", n: "Printbelle", l: "US / CN" }),
  ov({ s: "qikink", n: "Qikink", l: "India" }),
  ov({ s: "printrove", n: "Printrove", l: "India" }),
  ov({ s: "senhub", n: "SenHub", l: "US" }),
  ov({ s: "subliminator", n: "Subliminator", l: "China" }),
  ov({ s: "teescape", n: "Teescape", l: "Iowa" }),
  ov({ s: "gearlaunch", n: "GearLaunch", l: "Salt Lake City" }),
  ov({ s: "pengine", n: "Pengine", l: "Pennsylvania" }),
  ov({ s: "fulfill-engine", n: "Fulfill Engine", l: "US", nt: "Lists AS Colour as a supplier; 5026G Organic only via Printify." }),
  ov({ s: "popcustoms", n: "POPCUSTOMS", l: "US / Spain / Mexico" }),
  ov({ s: "aop-plus", n: "AOP+", l: "London" }),
  ov({ s: "hoplix", n: "Plixpod / Hoplix", l: "Naples, IT" }),
  ov({ s: "shirtigo", n: "Shirtigo", l: "Köln, DE" }),
  ov({ s: "shirtee-cloud", n: "Shirtee.Cloud", l: "Köln, DE" }),
  ov({ s: "shirt-king", n: "Shirt-King", l: "Teltow, DE" }),
  ov({ s: "merchcamp", n: "MerchCamp", l: "Innsbruck, AT" }),
  ov({ s: "promio", n: "Promio", l: "Breda, NL" }),
  ov({ s: "fullyshipd", n: "FullyShipd", l: "Hjørring, DK" }),
  ov({ s: "jetprint", n: "JetPrint", nt: "Location not published (reviewer says China)." }),
  ov({ s: "cjdropshipping", n: "CJdropshipping POD", nt: "Mentions Australian warehouses; POD details not published." }),
  ov({ s: "sellfy-pod", n: "Sellfy POD", nt: "11 fulfilment centres, countries not published." }),
  ov({ s: "peaprint", n: "PeaPrint", l: "US", nt: "'Delivery is not supported' to Australia." }),
  ov({ s: "ninjapod", n: "NinjaPOD", l: "US", nt: "US and Canada only." }),
  ov({ s: "marketprint", n: "MarketPrint", l: "DE", nt: "No Australian shipping." }),
  ov({ s: "merchone", n: "merchOne", l: "PL / US", nt: "No Australian shipping." }),
];

export const SEED_SUPPLIERS: SeedSupplier[] = [
  ...ACCOUNTS,
  ...AU_POD,
  ...NZ,
  ...QLD,
  ...NSW_ACT,
  ...VIC_TAS,
  ...WA_SA_NT,
  ...TRANSFERS,
  ...WHOLESALERS,
  ...OVERSEAS,
];
