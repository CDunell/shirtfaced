/**
 * Provider-agnostic print-on-demand interface. Nothing in db/store-queries.ts
 * or the internal API routes talks to a specific POD vendor's API shape —
 * they call this interface, and getPodProvider() (see ./index.ts) decides
 * which implementation answers, based on POD_PROVIDER. Swapping vendors
 * later means writing one new file that implements PodProvider, not
 * reworking the order pipeline.
 */
export type PodAddress = {
  name: string;
  line1: string;
  suburb: string;
  state: string;
  postcode: string;
  country: string;
};

export type PodOrderItem = {
  /** This app's own product slug + colour + size — e.g. "blip-tee". The
   * real vendor mapping (a Printful/Printify "sync variant id" per
   * slug/colour/size combination) lives in each adapter, not here — see
   * printful-adapter.ts's SYNC_VARIANT_MAP for why that's still a TODO. */
  slug: string;
  productName: string;
  colourName: string | null;
  size: string | null;
  quantity: number;
};

export type PodOrderInput = {
  /** This app's own order id — round-tripped so webhook responses can be
   * matched back without depending on a second lookup table. */
  orderRef: string;
  address: PodAddress;
  items: PodOrderItem[];
};

export type PodOrderResult = {
  podOrderId: string;
  status: string;
};

export type PodStatusResult = {
  status: string;
  trackingNumber?: string;
  trackingUrl?: string;
  carrier?: string;
};

export type PodShippingQuoteInput = {
  address: PodAddress;
  items: PodOrderItem[];
};

/**
 * Cents, not dollars — matches every other money value in this app
 * (priceCents, totalCents, etc.), so the internal API and checkout never
 * have to convert between the two representations mid-flow.
 */
export type PodShippingQuoteResult = {
  standardCents: number;
  expressCents?: number;
};

export interface PodProvider {
  readonly name: string;
  createOrder(input: PodOrderInput): Promise<PodOrderResult>;
  getOrderStatus(podOrderId: string): Promise<PodStatusResult>;
  /**
   * Real per-destination shipping cost for a cart, before payment. Added
   * because a flat AU-domestic-style rate (what curbstamps-site's checkout
   * used before this existed) badly undercharges genuinely international
   * orders — Printful's own published rates run a single hoodie from
   * ~US$8 domestically to ~US$25+ to a "Worldwide" destination. Rather than
   * hardcode a second guessed rate table with more zones, this asks the
   * real POD provider what it actually costs for this exact cart and
   * address — accurate by construction instead of approximated.
   */
  getShippingQuote(input: PodShippingQuoteInput): Promise<PodShippingQuoteResult>;
}

export class PodError extends Error {}
