import type { PodProvider, PodOrderInput, PodOrderResult, PodStatusResult } from "./types";

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
}
