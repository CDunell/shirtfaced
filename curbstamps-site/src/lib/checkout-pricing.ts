/**
 * Server-side checkout pricing — the single source of truth for what an
 * order costs. Both checkout/page.tsx (for display) and
 * api/create-payment-intent (for the real charge) resolve shipping the same
 * way (see lib/shipping-quote.ts) so the price shown never drifts from the
 * price charged.
 *
 * Shipping itself is NOT priced here — priceCart takes an already-resolved
 * shippingCents rather than looking one up from a fixed table. A flat table
 * (what this file used to have) is an AU-domestic rate; charging that on a
 * genuinely international order can undercharge badly against what the POD
 * provider actually bills for the parcel — see shipping-quote.ts for the
 * real per-order quote this now uses instead.
 */
import { products, FREE_SHIPPING_THRESHOLD } from "./products";

export const SHIPPING_METHODS = [
  { key: "standard", name: "Standard", time: "3–7 business days" },
  { key: "express", name: "Express", time: "1–3 business days" },
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

/** subtotalCents over the free-shipping threshold makes shipping free,
 * regardless of which method was picked — same rule this app has always
 * used, just factored out so both the quote route and priceCart apply it
 * identically. */
export function isFreeShipping(subtotalCents: number): boolean {
  return subtotalCents >= Math.round(FREE_SHIPPING_THRESHOLD * 100);
}

export function priceCart(lines: CartLineInput[], shippingCents: number) {
  if (!Array.isArray(lines) || lines.length === 0) {
    throw new CheckoutPricingError("Your cart is empty.");
  }
  if (!Number.isInteger(shippingCents) || shippingCents < 0) {
    throw new CheckoutPricingError("Invalid shipping cost.");
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
  const freeShipping = isFreeShipping(subtotalCents);
  const resolvedShippingCents = freeShipping ? 0 : shippingCents;

  return {
    lines: priced,
    subtotalCents,
    shippingCents: resolvedShippingCents,
    totalCents: subtotalCents + resolvedShippingCents,
    freeShipping,
  };
}
