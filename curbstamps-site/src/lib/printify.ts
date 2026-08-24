import { CREATURES } from "./creatures";

/**
 * Live Printify catalog data — tee, hoodie, crewneck and bucket hat are all
 * built in Printify (shop 28675131); cap was dropped (embroidery couldn't
 * carry the full lockup legibly). One paginated fetch of the whole shop
 * covers every category — each product's title tells us which category and
 * creature it is ("Blip Hoodie — Curb Stamps"), so there's no need for a
 * separate fetch per category.
 *
 * Server-only: PRINTIFY_API_TOKEN never reaches the client. Any failure
 * (missing token, network error, creature not found in the catalog) resolves
 * to `null` for that creature/category rather than throwing, so a page
 * always falls back to the honest SVG stand-in instead of breaking.
 */

const SHOP_ID = process.env.PRINTIFY_SHOP_ID;
const API_TOKEN = process.env.PRINTIFY_API_TOKEN;

export type PrintifyCategory = "tee" | "hoodie" | "crewneck" | "bucket-hat";

/** Matched against each product's own title — case-insensitive, captures
 * the creature name in group 1. Order doesn't matter; a title only ever
 * matches one of these. */
const CATEGORY_TITLE_PATTERN: Record<PrintifyCategory, RegExp> = {
  tee: /^(.+?)\s+Tee\b/i,
  hoodie: /^(.+?)\s+Hoodie\b/i,
  crewneck: /^(.+?)\s+Crewneck\b/i,
  "bucket-hat": /^(.+?)\s+Bucket Hat\b/i,
};

export type PrintifySize = {
  title: string;
  variantId: number;
};

export type PrintifyColourway = {
  name: string;
  hex: string;
  image: string | null;
  sizes: PrintifySize[];
};

export type PrintifyProductData = {
  productId: string;
  price: number;
  colours: PrintifyColourway[];
};

type RawVariant = {
  id: number;
  price: number;
  is_enabled: boolean;
  is_available: boolean;
  options: [number, number];
};

type RawOptionValue = { id: number; title: string; colors?: string[] };
type RawOption = { name: string; type: string; values: RawOptionValue[] };

type RawImage = {
  src: string;
  variant_ids: number[];
  position: string;
  is_default: boolean;
};

type RawProduct = {
  id: string;
  title: string;
  options: RawOption[];
  variants: RawVariant[];
  images: RawImage[];
};

function normalizeProduct(raw: RawProduct): PrintifyProductData {
  // variant.options is positional, but which position is colour vs size
  // varies by blueprint (tee/crewneck/bucket-hat put colour first; hoodie
  // puts size first) — raw.options itself declares the real order via each
  // group's own index — except variant.options doesn't reliably follow that
  // declared order either (confirmed on blueprint 314: options declares
  // [Colors, Sizes] but a real variant's own `options` array is
  // [sizeId, colourId] anyway). The only thing that's actually reliable is
  // which map a given option id is a member of, so match by membership
  // instead of position.
  const colourOption = raw.options.find((o) => o.type === "color");
  const sizeOption = raw.options.find((o) => o.type === "size");
  const colourById = new Map((colourOption?.values ?? []).map((v) => [v.id, v]));
  const sizeById = new Map((sizeOption?.values ?? []).map((v) => [v.id, v]));

  function resolveIds(options: number[]) {
    let colourId: number | undefined;
    let sizeId: number | undefined;
    for (const id of options) {
      if (colourById.has(id)) colourId = id;
      else if (sizeById.has(id)) sizeId = id;
    }
    return { colourId, sizeId };
  }

  const enabled = raw.variants.filter((v) => v.is_enabled && v.is_available);
  const price = enabled.length > 0 ? enabled[0].price / 100 : 0;

  const byColour = new Map<number, RawVariant[]>();
  for (const v of enabled) {
    const { colourId } = resolveIds(v.options);
    if (colourId === undefined) continue;
    if (!byColour.has(colourId)) byColour.set(colourId, []);
    byColour.get(colourId)!.push(v);
  }

  const colours: PrintifyColourway[] = [];
  for (const [colourId, variants] of byColour) {
    const colourInfo = colourById.get(colourId);
    if (!colourInfo) continue;
    const variantIds = new Set(variants.map((v) => v.id));
    // Position varies by decoration method ("front" for DTG, "front_dtf" for
    // the bucket hat's DTF print) — is_default is the reliable signal here,
    // not the position string.
    const frontImage = raw.images.find(
      (im) => im.is_default && im.variant_ids.some((id) => variantIds.has(id))
    );
    colours.push({
      name: colourInfo.title,
      hex: colourInfo.colors?.[0] ?? "#cccccc",
      image: frontImage?.src ?? null,
      sizes: variants
        .map((v) => ({ title: sizeById.get(resolveIds(v.options).sizeId ?? -1)?.title ?? "", variantId: v.id }))
        .filter((s) => s.title)
        .sort((a, b) => a.variantId - b.variantId),
    });
  }

  return { productId: raw.id, price, colours };
}

type Catalog = Record<PrintifyCategory, Map<string, PrintifyProductData>>;

function emptyCatalog(): Catalog {
  return { tee: new Map(), hoodie: new Map(), crewneck: new Map(), "bucket-hat": new Map() };
}

let cachedCatalog: Promise<Catalog> | null = null;
let cachedAt = 0;
const CACHE_TTL_MS = 5 * 60 * 1000;

async function fetchCatalog(): Promise<Catalog> {
  const result = emptyCatalog();
  if (!SHOP_ID || !API_TOKEN) return result;

  const nameToSlug = new Map(CREATURES.map((c) => [c.name.toLowerCase(), c.slug]));
  const categories = Object.keys(CATEGORY_TITLE_PATTERN) as PrintifyCategory[];

  let page = 1;
  for (;;) {
    const res = await fetch(
      `https://api.printify.com/v1/shops/${SHOP_ID}/products.json?limit=50&page=${page}`,
      {
        headers: { Authorization: `Bearer ${API_TOKEN}` },
        next: { revalidate: 300 },
      }
    );
    if (!res.ok) break;
    const json = (await res.json()) as { data: RawProduct[]; last_page?: number };

    for (const raw of json.data) {
      for (const category of categories) {
        const match = raw.title.match(CATEGORY_TITLE_PATTERN[category]);
        if (!match) continue;
        const slug = nameToSlug.get(match[1].toLowerCase());
        if (!slug) continue;
        result[category].set(slug, normalizeProduct(raw));
        break;
      }
    }

    if (!json.last_page || page >= json.last_page) break;
    page += 1;
  }

  return result;
}

/** Cached in-process for 5 minutes — a full-shop paginated fetch on every
 * request would be wasteful and the catalog changes rarely, but this app's
 * server process runs for days at a time (systemd service, or a long-lived
 * dev server), so an unbounded cache would go stale the moment a new
 * category or creature gets built in Printify. */
export function getPrintifyCatalog(): Promise<Catalog> {
  if (!cachedCatalog || Date.now() - cachedAt > CACHE_TTL_MS) {
    cachedAt = Date.now();
    cachedCatalog = fetchCatalog().catch(() => emptyCatalog());
  }
  return cachedCatalog;
}

/** Which creature slugs actually have a built Printify product for this
 * category — used to filter the design picker so it never offers a design
 * that isn't a real, orderable product (e.g. "dreg", dropped from the
 * catalog entirely). Empty only means the whole catalog fetch failed/isn't
 * configured, not "no designs exist" — callers should treat that as
 * "unknown" rather than "nothing available". */
export async function getAvailableCreatureSlugs(category: PrintifyCategory): Promise<Set<string>> {
  const catalog = await getPrintifyCatalog();
  return new Set(catalog[category].keys());
}

export async function getPrintifyProductData(
  category: PrintifyCategory,
  creatureSlug: string
): Promise<PrintifyProductData | null> {
  const catalog = await getPrintifyCatalog();
  return catalog[category].get(creatureSlug) ?? null;
}
