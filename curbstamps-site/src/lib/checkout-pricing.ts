/**
 * Server-side checkout pricing — the single source of truth for what an
 * order costs. Both checkout/page.tsx (for display) and
 * api/create-payment-intent (for the real charge) read SHIPPING_METHODS from
 * here so the price shown never drifts from the price charged. Same shape as
 * shirtfaced's own src/lib/checkout-pricing.ts, minus discount codes — not
 * needed for a v1 launch, see docs/curbstamps/CURB_STAMPS_SPEC.md roadmap.
 */
import { products, FREE_SHIPPING_THRESHOLD } from "./products";

export const SHIPPING_METHODS = [
  { key: "standard", name: "Standard", time: "3–7 business days", price: 9.95 },
  { key: "express", name: "Express", time: "1–3 business days", price: 14.95 },
] as const;

export type ShippingMethodKey = (typeof SHIPPING_METHODS)[number]["key"];

export type CartLineInput = {
  slug: string;
  size: string;
  colour: string;
  quantity: number;
};

export type PricedLine = CartLineInput & {
  name: string;
  art: string;
  unitPriceCents: number;
};

export class CheckoutPricingError extends Error {}

export function priceCart(lines: CartLineInput[], shippingMethod: string) {
  if (!Array.isArray(lines) || lines.length === 0) {
    throw new CheckoutPricingError("Your cart is empty.");
  }

  const priced: PricedLine[] = lines.map((line) => {
    const product = products.find((p) => p.slug === line.slug);
    if (!product) {
      throw new CheckoutPricingError(`That item isn't available any more (${line.slug}).`);
    }
    const colour = product.colours.find((c) => c.name === line.colour);
    if (!colour) {
      throw new CheckoutPricingError(`"${line.colour}" isn't a colour ${product.name} comes in.`);
    }
    if (!product.sizes.includes(line.size)) {
      throw new CheckoutPricingError(`"${line.size}" isn't a size ${product.name} comes in.`);
    }
    if (!Number.isInteger(line.quantity) || line.quantity <= 0) {
      throw new CheckoutPricingError(`Invalid quantity for ${product.name}.`);
    }
    return {
      ...line,
      name: product.name,
      art: product.art,
      unitPriceCents: Math.round(product.price * 100),
    };
  });

  const subtotalCents = priced.reduce((sum, l) => sum + l.unitPriceCents * l.quantity, 0);
  const freeShipping = subtotalCents >= Math.round(FREE_SHIPPING_THRESHOLD * 100);

  const method = SHIPPING_METHODS.find((m) => m.key === shippingMethod);
  if (!method) {
    throw new CheckoutPricingError(`Unknown shipping method: ${shippingMethod}.`);
  }

  const shippingCents = freeShipping ? 0 : Math.round(method.price * 100);

  return {
    lines: priced,
    subtotalCents,
    shippingCents,
    totalCents: subtotalCents + shippingCents,
    freeShipping,
  };
}
