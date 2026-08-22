import type {
  PodProvider,
  PodOrderInput,
  PodOrderResult,
  PodStatusResult,
  PodShippingQuoteInput,
  PodShippingQuoteResult,
} from "./types";
import { PodError } from "./types";

/**
 * The decided POD provider (see docs/curbstamps/CURB_STAMPS_SPEC.md §4) —
 * chosen for its confirmed real kids/youth apparel SKUs (Gildan 5000B youth
 * tee, Gildan 18500B youth hoodie), OEKO-TEX-certified blanks, and the best
 * margin of the providers compared.
 *
 * This is a REAL implementation against Printify's documented REST API
 * (https://developers.printify.com/) — it will place real orders for real
 * money the moment PRINTIFY_API_KEY, PRINTIFY_SHOP_ID and a filled-in
 * SYNC_VARIANT_MAP all exist. Two things still block that:
 *
 * 1. SYNC_VARIANT_MAP is empty. Printify identifies a specific garment +
 *    colour + size as a (product_id, variant_id) pair from a product built
 *    in the Printify dashboard (or pushed via their Products API) against
 *    the real blanks — Gildan 5000B (youth tee) and 18500B (youth hoodie)
 *    confirmed to exist in Printify's catalogue; a kids cap blank hasn't
 *    been picked yet. That catalogue doesn't exist yet — this file is the
 *    wiring for once it does.
 * 2. No PRINTIFY_API_KEY/PRINTIFY_SHOP_ID exist. getPodProvider() (see
 *    ./index.ts) never selects this adapter unless POD_PROVIDER=printify is
 *    set, so it's inert by default.
 */
const PRINTIFY_API_BASE = "https://api.printify.com/v1";

/** slug -> colour name -> size -> { productId, variantId }. Empty until a
 * real Printify catalogue exists for these designs. */
const SYNC_VARIANT_MAP: Record<string, Record<string, Record<string, { productId: string; variantId: number }>>> = {};

function lookupVariant(slug: string, colourName: string | null, size: string | null) {
  const variant = SYNC_VARIANT_MAP[slug]?.[colourName ?? ""]?.[size ?? ""];
  if (!variant) {
    throw new PodError(
      `No Printify product/variant mapped for ${slug} / ${colourName ?? "-"} / ${size ?? "-"} — ` +
        `add it to SYNC_VARIANT_MAP in printify-adapter.ts once the Printify catalogue exists.`,
    );
  }
  return variant;
}

export class PrintifyProvider implements PodProvider {
  readonly name = "printify";

  private apiKey(): string {
    const key = process.env.PRINTIFY_API_KEY;
    if (!key) throw new PodError("PRINTIFY_API_KEY is not set.");
    return key;
  }

  private shopId(): string {
    const id = process.env.PRINTIFY_SHOP_ID;
    if (!id) throw new PodError("PRINTIFY_SHOP_ID is not set.");
    return id;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${PRINTIFY_API_BASE}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${this.apiKey()}`,
        "content-type": "application/json",
        ...init?.headers,
      },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new PodError(`Printify request failed (${res.status} ${path}): ${text}`);
    }
    return res.json() as Promise<T>;
  }

  async createOrder(input: PodOrderInput): Promise<PodOrderResult> {
    const body = {
      external_id: input.orderRef,
      line_items: input.items.map((item) => {
        const { productId, variantId } = lookupVariant(item.slug, item.colourName, item.size);
        return { product_id: productId, variant_id: variantId, quantity: item.quantity };
      }),
      shipping_method: 1, // 1 = standard — see getShippingQuote for the real per-order options
      send_shipping_notification: false,
      address_to: {
        first_name: input.address.name.split(" ")[0] || input.address.name,
        last_name: input.address.name.split(" ").slice(1).join(" ") || "-",
        country: input.address.country,
        region: input.address.state,
        address1: input.address.line1,
        city: input.address.suburb,
        zip: input.address.postcode,
      },
    };

    const json = await this.request<{ id: string; status: string }>(`/shops/${this.shopId()}/orders.json`, {
      method: "POST",
      body: JSON.stringify(body),
    });
    return { podOrderId: json.id, status: json.status };
  }

  async getOrderStatus(podOrderId: string): Promise<PodStatusResult> {
    const json = await this.request<{
      status: string;
      shipments?: { carrier?: string; number?: string; url?: string }[];
    }>(`/shops/${this.shopId()}/orders/${podOrderId}.json`);
    const shipment = json.shipments?.[0];
    return {
      status: json.status,
      trackingNumber: shipment?.number,
      trackingUrl: shipment?.url,
      carrier: shipment?.carrier,
    };
  }

  /**
   * Real per-order shipping cost from Printify's own rates endpoint — see
   * PodProvider.getShippingQuote's own comment for why this exists instead
   * of a hardcoded zone table. Printify's shipping-cost response is a
   * single figure (their cheapest available method for this cart+address),
   * not separate standard/express options the way Printful's is — so
   * `expressCents` is left undefined here rather than guessed.
   */
  async getShippingQuote(input: PodShippingQuoteInput): Promise<PodShippingQuoteResult> {
    const body = {
      line_items: input.items.map((item) => {
        const { productId, variantId } = lookupVariant(item.slug, item.colourName, item.size);
        return { product_id: productId, variant_id: variantId, quantity: item.quantity };
      }),
      address_to: {
        country: input.address.country,
        region: input.address.state,
        address1: input.address.line1,
        city: input.address.suburb,
        zip: input.address.postcode,
      },
    };

    // Printify returns cents already, in the shop's currency — no /100 here.
    const json = await this.request<{ standard: number }>(`/shops/${this.shopId()}/orders/shipping.json`, {
      method: "POST",
      body: JSON.stringify(body),
    });
    return { standardCents: json.standard };
  }
}
