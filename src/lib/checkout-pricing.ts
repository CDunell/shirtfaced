/**
 * Server-side checkout pricing. The single source of truth for what an order
 * actually costs — the browser never gets to say what anything is worth.
 * Both src/app/checkout/page.tsx (for display) and
 * src/app/api/create-payment-intent/route.ts (for the real charge) read
 * SHIPPING_METHODS from here rather than each keeping their own copy, so the
 * price shown can never drift from the price charged.
 */
import { products, FREE_SHIPPING_THRESHOLD } from "./products";

export const SHIPPING_METHODS = [
  { key: "standard", name: "Standard", time: "3–5 business days", price: 10 },
  { key: "express", name: "Express", time: "1–2 business days", price: 15 },
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

/**
 * Recomputes an order total from the catalogue, never from client-sent
 * prices or subtotals. Throws CheckoutPricingError — with a message safe to
 * show the customer — on anything that doesn't resolve to a real product,
 * colour, size or shipping method, rather than pricing it at zero or
 * guessing what was meant.
 */
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
    if (!product.sizes.includes(line.size as (typeof product.sizes)[number])) {
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
