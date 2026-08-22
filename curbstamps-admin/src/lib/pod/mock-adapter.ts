import type {
  PodProvider,
  PodOrderInput,
  PodOrderResult,
  PodStatusResult,
  PodShippingQuoteInput,
  PodShippingQuoteResult,
} from "./types";

/**
 * Default provider until a real vendor account exists. Accepts every order,
 * logs what a real provider would have received, and reports a fake
 * lifecycle. Good enough to exercise the whole checkout → paid →
 * "in production" pipeline end to end without spending real money on test
 * garments — see docs/curbstamps/CURB_STAMPS_SPEC.md §4 for swapping this
 * out for Printful/Printify once an account exists.
 */
export class MockPodProvider implements PodProvider {
  readonly name = "mock";

  async createOrder(input: PodOrderInput): Promise<PodOrderResult> {
    const podOrderId = `mock_${input.orderRef.slice(0, 8)}_${Date.now()}`;
    console.log(
      `[pod:mock] createOrder ${podOrderId} for order ${input.orderRef} — ${input.items
        .map((i) => `${i.quantity}x ${i.productName} (${i.colourName ?? "-"}/${i.size ?? "-"})`)
        .join(", ")} → ${input.address.suburb} ${input.address.state} ${input.address.postcode}`,
    );
    return { podOrderId, status: "submitted" };
  }

  async getOrderStatus(podOrderId: string): Promise<PodStatusResult> {
    console.log(`[pod:mock] getOrderStatus ${podOrderId}`);
    return { status: "in_production" };
  }

  /**
   * A flat, honestly-fake estimate — AU domestic rate for an AU address,
   * otherwise a rough "further away costs more" guess by item count. Not
   * calibrated against anything real; it exists so checkout has a shipping
   * quote to show while no real POD account exists, same spirit as the
   * mock adapter's createOrder. Never confuse this for a real rate table —
   * see getShippingQuote on PrintifyProvider for the real thing.
   */
  async getShippingQuote(input: PodShippingQuoteInput): Promise<PodShippingQuoteResult> {
    const itemCount = input.items.reduce((sum, i) => sum + i.quantity, 0);
    const isDomestic = input.address.country === "AU";
    const base = isDomestic ? 995 : 2495;
    const perExtra = isDomestic ? 200 : 800;
    const standardCents = base + perExtra * Math.max(0, itemCount - 1);
    return { standardCents, expressCents: standardCents + (isDomestic ? 500 : 1500) };
  }
}
