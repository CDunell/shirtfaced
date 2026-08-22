import type { CartLineInput } from "./checkout-pricing";
import { getProduct } from "./products";

export type ShippingAddressInput = {
  name: string;
  line1: string;
  suburb: string;
  state: string;
  postcode: string;
  /** AU-only today — the checkout form has no country field yet (see
   * docs/curbstamps/CURB_STAMPS_SPEC.md §7, "International shipping").
   * Hardcoded here rather than threaded through from a form field that
   * doesn't exist, so this stays the one place to change once it does. */
  country?: string;
};

export type ShippingQuote = {
  standardCents: number;
  expressCents: number;
  /** True if this came from curbstamps-admin's real POD quote; false if it
   * fell back to a flat estimate (POD unconfigured, or the call failed).
   * The checkout UI doesn't need to show this, but it's useful in logs. */
  live: boolean;
};

/** Same numbers MockPodProvider.getShippingQuote returns, so a customer
 * sees a consistent price whether or not the admin backend is reachable —
 * this is the fallback, not a second guess at what's realistic. */
const FALLBACK_STANDARD_CENTS = 995;
const FALLBACK_EXPRESS_CENTS = 1495;

/**
 * Asks curbstamps-admin for a real shipping cost for this cart + address —
 * see PodProvider.getShippingQuote's own comment for why a flat rate isn't
 * good enough for a worldwide launch. Falls back to a flat estimate rather
 * than blocking checkout if the admin backend or POD provider isn't
 * reachable/configured — same "degrade honestly, don't break checkout"
 * pattern as Stripe being unconfigured.
 */
export async function getShippingQuote(lines: CartLineInput[], address: ShippingAddressInput): Promise<ShippingQuote> {
  const adminApiUrl = process.env.ADMIN_API_URL;
  const adminApiKey = process.env.ADMIN_INTERNAL_API_KEY;

  if (!adminApiUrl || !adminApiKey) {
    return { standardCents: FALLBACK_STANDARD_CENTS, expressCents: FALLBACK_EXPRESS_CENTS, live: false };
  }

  const items = lines.map((line) => {
    const product = getProduct(line.slug);
    return {
      slug: line.slug,
      productName: product?.name ?? line.slug,
      colourName: line.colour,
      size: line.size,
      quantity: line.quantity,
    };
  });

  try {
    const res = await fetch(`${adminApiUrl}/api/internal/shipping-quote`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-internal-api-key": adminApiKey },
      body: JSON.stringify({
        address: { ...address, country: address.country ?? "AU" },
        items,
      }),
    });
    if (!res.ok) {
      throw new Error(`shipping-quote returned ${res.status}`);
    }
    const json = (await res.json()) as { standardCents: number; expressCents?: number };
    return {
      standardCents: json.standardCents,
      expressCents: json.expressCents ?? json.standardCents + 500,
      live: true,
    };
  } catch (error) {
    console.error("getShippingQuote: falling back to flat estimate —", error);
    return { standardCents: FALLBACK_STANDARD_CENTS, expressCents: FALLBACK_EXPRESS_CENTS, live: false };
  }
}
