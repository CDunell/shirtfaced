import { CREATURES } from "./creatures";

/**
 * Live Printify catalog data for the tee category — the only category built
 * in Printify so far (blueprint 157, shop 28675131). Hoodie/cap stay on the
 * synthetic GarmentArt stand-in in products.ts until those are built too.
 *
 * Server-only: PRINTIFY_API_TOKEN never reaches the client. Any failure
 * (missing token, network error, creature not found in the catalog) resolves
 * to `null` for that creature rather than throwing, so a page always falls
 * back to the honest SVG stand-in instead of breaking.
 */

const SHOP_ID = process.env.PRINTIFY_SHOP_ID;
const API_TOKEN = process.env.PRINTIFY_API_TOKEN;

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

export type PrintifyTeeData = {
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

function normalizeProduct(raw: RawProduct): PrintifyTeeData {
  const colourOption = raw.options.find((o) => o.type === "color");
  const sizeOption = raw.options.find((o) => o.type === "size");
  const colourById = new Map((colourOption?.values ?? []).map((v) => [v.id, v]));
  const sizeById = new Map((sizeOption?.values ?? []).map((v) => [v.id, v]));

  const enabled = raw.variants.filter((v) => v.is_enabled && v.is_available);
  const price = enabled.length > 0 ? enabled[0].price / 100 : 0;

  const byColour = new Map<number, RawVariant[]>();
  for (const v of enabled) {
    const [colourId] = v.options;
    if (!byColour.has(colourId)) byColour.set(colourId, []);
    byColour.get(colourId)!.push(v);
  }

  const colours: PrintifyColourway[] = [];
  for (const [colourId, variants] of byColour) {
    const colourInfo = colourById.get(colourId);
    if (!colourInfo) continue;
    const variantIds = new Set(variants.map((v) => v.id));
    const frontImage = raw.images.find(
      (im) => im.position === "front" && im.is_default && im.variant_ids.some((id) => variantIds.has(id))
    );
    colours.push({
      name: colourInfo.title,
      hex: colourInfo.colors?.[0] ?? "#cccccc",
      image: frontImage?.src ?? null,
      sizes: variants
        .map((v) => ({ title: sizeById.get(v.options[1])?.title ?? "", variantId: v.id }))
        .filter((s) => s.title)
        .sort((a, b) => a.variantId - b.variantId),
    });
  }

  return { productId: raw.id, price, colours };
}

let cachedCatalog: Promise<Map<string, PrintifyTeeData>> | null = null;

async function fetchCatalog(): Promise<Map<string, PrintifyTeeData>> {
  const result = new Map<string, PrintifyTeeData>();
  if (!SHOP_ID || !API_TOKEN) return result;

  const nameToSlug = new Map(CREATURES.map((c) => [c.name.toLowerCase(), c.slug]));

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
      const match = raw.title.match(/^(.+?)\s+Tee\b/i);
      const slug = match ? nameToSlug.get(match[1].toLowerCase()) : undefined;
      if (!slug) continue;
      result.set(slug, normalizeProduct(raw));
    }

    if (!json.last_page || page >= json.last_page) break;
    page += 1;
  }

  return result;
}

/** Cached for the life of the server process / Next.js data cache window
 * (5 min) — a 43-product paginated fetch on every request would be wasteful
 * and the catalog changes rarely. */
export function getPrintifyTeeCatalog(): Promise<Map<string, PrintifyTeeData>> {
  if (!cachedCatalog) {
    cachedCatalog = fetchCatalog().catch(() => new Map());
  }
  return cachedCatalog;
}

export async function getPrintifyTeeData(creatureSlug: string): Promise<PrintifyTeeData | null> {
  const catalog = await getPrintifyTeeCatalog();
  return catalog.get(creatureSlug) ?? null;
}
