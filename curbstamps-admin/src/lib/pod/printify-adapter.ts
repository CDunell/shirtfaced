import type { PodProvider, PodOrderInput, PodOrderResult, PodStatusResult, PodOrderItem } from "./types";
import { PodError } from "./types";

/**
 * Real implementation against Printify's Orders API (schema confirmed
 * against https://developers.printify.com/openapi.json — "Submit an order"
 * using an existing product, POST /v1/shops/{shop_id}/orders.json), targeting
 * the actual Curb Stamps shop and catalog (shop 28675131, blueprint 157 —
 * see docs/curbstamps and the build scripts referenced there).
 *
 * There is no hand-maintained id map here (unlike printful-adapter.ts's
 * SYNC_VARIANT_MAP) — the catalog spans 40+ creatures × 9 colours × 5 sizes,
 * too large to hand-write and kept in sync. Instead this resolves the live
 * Printify catalog at request time (same technique curbstamps-site/src/lib/
 * printify.ts uses for the storefront) and matches an order item's slug
 * (e.g. "blip-tee") to a product/variant structurally: strip the trailing
 * "-tee"/"-hoodie"/"-cap" to get the creature slug, then match it against
 * each Printify product's own title ("Blip Tee — Curb Stamps").
 *
 * createOrder() deliberately stops once Printify has the order in "pending"
 * — it never calls the separate POST .../send_to_production.json endpoint,
 * so nothing is billed or actually sent to a print provider until that's
 * called on purpose (a staff action or a later, deliberately-added
 * automation) once this integration has been proven against real test
 * orders. Same caution as printful-adapter.ts's confirm: false.
 */
const PRINTIFY_API_BASE = "https://api.printify.com/v1";

type RawVariant = {
  id: number;
  is_enabled: boolean;
  is_available: boolean;
  options: [number, number];
};
type RawOptionValue = { id: number; title: string };
type RawOption = { name: string; type: string; values: RawOptionValue[] };
type RawProduct = { id: string; title: string; options: RawOption[]; variants: RawVariant[] };

type CatalogEntry = { productId: string; variantId: number };
/** creatureSlug -> colourName (lowercased) -> size (lowercased) -> entry */
type Catalog = Map<string, Map<string, Map<string, CatalogEntry>>>;

function shopId(): string {
  const id = process.env.PRINTIFY_SHOP_ID;
  if (!id) throw new PodError("PRINTIFY_SHOP_ID is not set.");
  return id;
}

function apiToken(): string {
  const key = process.env.PRINTIFY_API_TOKEN;
  if (!key) throw new PodError("PRINTIFY_API_TOKEN is not set.");
  return key;
}

function creatureSlugFrom(itemSlug: string): string {
  return itemSlug.replace(/-(tee|hoodie|cap)$/, "");
}

let cachedCatalog: Promise<Catalog> | null = null;

async function fetchCatalog(): Promise<Catalog> {
  const catalog: Catalog = new Map();
  const shop = shopId();
  const token = apiToken();

  let page = 1;
  for (;;) {
    const res = await fetch(`${PRINTIFY_API_BASE}/shops/${shop}/products.json?limit=50&page=${page}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new PodError(`Printify catalog fetch failed (${res.status}): ${text}`);
    }
    const json = (await res.json()) as { data: RawProduct[]; last_page?: number };

    for (const raw of json.data) {
      const words = raw.title.toLowerCase().split(/\s+/);
      const categoryIdx = words.findIndex((w) => w === "tee" || w === "hoodie" || w === "cap");
      if (categoryIdx <= 0) continue;
      const creatureSlug = words.slice(0, categoryIdx).join("-");

      const colourOption = raw.options.find((o) => o.type === "color");
      const sizeOption = raw.options.find((o) => o.type === "size");
      const colourById = new Map((colourOption?.values ?? []).map((v) => [v.id, v.title.toLowerCase()]));
      const sizeById = new Map((sizeOption?.values ?? []).map((v) => [v.id, v.title.toLowerCase()]));

      let byColour = catalog.get(creatureSlug);
      if (!byColour) {
        byColour = new Map();
        catalog.set(creatureSlug, byColour);
      }

      for (const v of raw.variants) {
        if (!v.is_enabled || !v.is_available) continue;
        const [colourId, sizeId] = v.options;
        const colourName = colourById.get(colourId);
        const sizeName = sizeById.get(sizeId);
        if (!colourName || !sizeName) continue;
        let bySize = byColour.get(colourName);
        if (!bySize) {
          bySize = new Map();
          byColour.set(colourName, bySize);
        }
        bySize.set(sizeName, { productId: raw.id, variantId: v.id });
      }
    }

    if (!json.last_page || page >= json.last_page) break;
    page += 1;
  }

  return catalog;
}

/** Cached for the life of the server process — a paginated 40+ product
 * fetch on every order would be wasteful and the catalog changes rarely.
 * Restart the admin app (or extend this with a TTL) after adding new
 * products in Printify. */
function getCatalog(): Promise<Catalog> {
  if (!cachedCatalog) cachedCatalog = fetchCatalog().catch((e) => {
    cachedCatalog = null;
    throw e;
  });
  return cachedCatalog;
}

async function lookupVariant(item: PodOrderItem): Promise<CatalogEntry> {
  const catalog = await getCatalog();
  const creatureSlug = creatureSlugFrom(item.slug);
  const byColour = catalog.get(creatureSlug);
  if (!byColour) {
    throw new PodError(`No Printify product found for "${creatureSlug}" (from order item slug "${item.slug}").`);
  }
  const colourName = (item.colourName ?? "").toLowerCase();
  const bySize = byColour.get(colourName);
  if (!bySize) {
    throw new PodError(`No Printify variant for ${item.slug} in colour "${item.colourName ?? "-"}".`);
  }
  const sizeName = (item.size ?? "").toLowerCase();
  const entry = bySize.get(sizeName);
  if (!entry) {
    throw new PodError(`No Printify variant for ${item.slug} / ${item.colourName ?? "-"} / size "${item.size ?? "-"}".`);
  }
  return entry;
}

/** Printify wants first/last name separately; our own address only has one
 * "name" field — split on the first space, and fall back to repeating the
 * first name if there's no second word rather than sending an empty
 * last_name. */
function splitName(name: string): { first: string; last: string } {
  const trimmed = name.trim();
  const idx = trimmed.indexOf(" ");
  if (idx === -1) return { first: trimmed, last: trimmed };
  return { first: trimmed.slice(0, idx), last: trimmed.slice(idx + 1) };
}

export class PrintifyProvider implements PodProvider {
  readonly name = "printify";

  async createOrder(input: PodOrderInput): Promise<PodOrderResult> {
    const line_items = await Promise.all(
      input.items.map(async (item) => {
        const { productId, variantId } = await lookupVariant(item);
        return { product_id: productId, variant_id: variantId, quantity: item.quantity };
      }),
    );

    const { first, last } = splitName(input.address.name);
    const body = {
      external_id: input.orderRef,
      line_items,
      // 1 = standard shipping per Printify's own API example; each print
      // provider defines its own numeric shipping methods, so this may need
      // revisiting once real orders are being placed against blueprint 157's
      // actual provider (99, "Printify Choice" — see docs/curbstamps).
      shipping_method: 1,
      send_shipping_notification: false,
      address_to: {
        first_name: first,
        last_name: last,
        address1: input.address.line1,
        city: input.address.suburb,
        region: input.address.state,
        zip: input.address.postcode,
        country: input.address.country,
      },
    };

    const res = await fetch(`${PRINTIFY_API_BASE}/shops/${shopId()}/orders.json`, {
      method: "POST",
      headers: { Authorization: `Bearer ${apiToken()}`, "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new PodError(`Printify order creation failed (${res.status}): ${text}`);
    }
    const json = (await res.json()) as { id: string; status: string };
    return { podOrderId: json.id, status: json.status };
  }

  async getOrderStatus(podOrderId: string): Promise<PodStatusResult> {
    const res = await fetch(`${PRINTIFY_API_BASE}/shops/${shopId()}/orders/${podOrderId}.json`, {
      headers: { Authorization: `Bearer ${apiToken()}` },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new PodError(`Printify order lookup failed (${res.status}): ${text}`);
    }
    const json = (await res.json()) as {
      status: string;
      shipments?: { carrier?: string; number?: string; url?: string }[];
    };
    const shipment = json.shipments?.[0];
    return {
      status: json.status,
      trackingNumber: shipment?.number,
      trackingUrl: shipment?.url,
      carrier: shipment?.carrier,
    };
  }
}
