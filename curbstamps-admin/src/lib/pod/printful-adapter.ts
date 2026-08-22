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
 * Reference implementation against Printful's real order API. Printify is
 * the decided provider (see printify-adapter.ts and
 * docs/curbstamps/CURB_STAMPS_SPEC.md §4) — this is kept as a working
 * alternative, not the one getPodProvider() defaults to. NOT
 * production-ready either way. It will make real requests and, if given a real API key
 * and confirm: true, place real orders for real money the moment
 * SYNC_VARIANT_MAP is filled in. Two things block that today:
 *
 * 1. SYNC_VARIANT_MAP is empty. Printful identifies a specific garment +
 *    colour + size as a "sync variant id" from a product you build in their
 *    dashboard (or push via their Sync Products API) using the blanks
 *    decided in docs/production/GARMENT_BLANK_STRATEGY.md (AS Colour 5026,
 *    Comfort Colors 1717) and the artwork in curbstamps-site/public/
 *    creatures/. That catalogue doesn't exist yet — this file is the wiring
 *    for once it does, not a working integration today.
 * 2. No PRINTFUL_API_KEY exists. getPodProvider() (see ./index.ts) never
 *    selects this adapter unless POD_PROVIDER=printful is set, so it's inert
 *    by default — see the mock adapter for what actually runs today.
 *
 * API reference: https://developers.printful.com/docs/ (Orders v2 — POST
 * /orders, GET /orders/{id}).
 */
const PRINTFUL_API_BASE = "https://api.printful.com";

/** slug -> colour name -> size -> Printful sync_variant_id. Empty until a
 * real Printful catalogue exists for these designs. */
const SYNC_VARIANT_MAP: Record<string, Record<string, Record<string, number>>> = {};

function lookupSyncVariantId(slug: string, colourName: string | null, size: string | null): number {
  const id = SYNC_VARIANT_MAP[slug]?.[colourName ?? ""]?.[size ?? ""];
  if (!id) {
    throw new PodError(
      `No Printful sync variant mapped for ${slug} / ${colourName ?? "-"} / ${size ?? "-"} — ` +
        `add it to SYNC_VARIANT_MAP in printful-adapter.ts once the Printful catalogue exists.`,
    );
  }
  return id;
}

export class PrintfulProvider implements PodProvider {
  readonly name = "printful";

  private apiKey(): string {
    const key = process.env.PRINTFUL_API_KEY;
    if (!key) throw new PodError("PRINTFUL_API_KEY is not set.");
    return key;
  }

  async createOrder(input: PodOrderInput): Promise<PodOrderResult> {
    const body = {
      external_id: input.orderRef,
      recipient: {
        name: input.address.name,
        address1: input.address.line1,
        city: input.address.suburb,
        state_code: input.address.state,
        country_code: input.address.country,
        zip: input.address.postcode,
      },
      items: input.items.map((item) => ({
        sync_variant_id: lookupSyncVariantId(item.slug, item.colourName, item.size),
        quantity: item.quantity,
      })),
      // false while this integration is unverified — creates a draft order
      // in Printful that still needs manual confirmation, rather than
      // charging the Printful account automatically. Flip once trusted.
      confirm: false,
    };

    const res = await fetch(`${PRINTFUL_API_BASE}/orders`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey()}`,
        "content-type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new PodError(`Printful order creation failed (${res.status}): ${text}`);
    }

    const json = (await res.json()) as { result: { id: number; status: string } };
    return { podOrderId: String(json.result.id), status: json.result.status };
  }

  async getOrderStatus(podOrderId: string): Promise<PodStatusResult> {
    const res = await fetch(`${PRINTFUL_API_BASE}/orders/${podOrderId}`, {
      headers: { Authorization: `Bearer ${this.apiKey()}` },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new PodError(`Printful order lookup failed (${res.status}): ${text}`);
    }
    const json = (await res.json()) as {
      result: { status: string; shipments?: { tracking_number?: string; tracking_url?: string; carrier?: string }[] };
    };
    const shipment = json.result.shipments?.[0];
    return {
      status: json.result.status,
      trackingNumber: shipment?.tracking_number,
      trackingUrl: shipment?.tracking_url,
      carrier: shipment?.carrier,
    };
  }

  /**
   * Printful's own /shipping/rates endpoint — real per-order shipping cost
   * instead of a hardcoded zone table, same reasoning as
   * PrintifyProvider.getShippingQuote. Unverified against a live account
   * (developers.printful.com is unreachable from this environment): the
   * request shape below (recipient + items keyed by variant_id) and the
   * response shape (result: an array of {id, rate, currency} options) are
   * both taken from Printful's own SDK examples, not confirmed against a
   * real response. Whether `items` here wants the catalog variant_id or the
   * store-specific sync_variant_id (used for orders above) is the one
   * genuine unknown — confirm against a real account before trusting this.
   */
  async getShippingQuote(input: PodShippingQuoteInput): Promise<PodShippingQuoteResult> {
    const body = {
      recipient: {
        country_code: input.address.country,
        state_code: input.address.state,
      },
      items: input.items.map((item) => ({
        sync_variant_id: lookupSyncVariantId(item.slug, item.colourName, item.size),
        quantity: item.quantity,
      })),
    };

    const res = await fetch(`${PRINTFUL_API_BASE}/shipping/rates`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey()}`,
        "content-type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new PodError(`Printful shipping rate lookup failed (${res.status}): ${text}`);
    }

    const json = (await res.json()) as { result: { id: string; rate: string }[] };
    const toCents = (rate: string) => Math.round(parseFloat(rate) * 100);
    const standard = json.result.find((r) => !/express/i.test(r.id)) ?? json.result[0];
    const express = json.result.find((r) => /express/i.test(r.id));
    if (!standard) throw new PodError("Printful returned no shipping options for this address.");

    return {
      standardCents: toCents(standard.rate),
      expressCents: express ? toCents(express.rate) : undefined,
    };
  }
}
