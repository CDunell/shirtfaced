import { test } from "node:test";
import assert from "node:assert/strict";
import { priceCart, CheckoutPricingError } from "./checkout-pricing";

// Real catalogue data, not a fixture — this is the actual server-side charge
// calculation, so it's tested against what a customer would really select.
const REAL_LINE = { slug: "roll-the-dice-tee", size: "M", colour: "Washed Black", quantity: 1 };

test("priceCart charges standard shipping under the free-shipping threshold", () => {
  const result = priceCart([REAL_LINE], "standard");
  assert.equal(result.subtotalCents, 4995);
  assert.equal(result.shippingCents, 1170);
  assert.equal(result.totalCents, 6165);
  assert.equal(result.freeShipping, false);
});

test("priceCart charges express shipping when selected", () => {
  const result = priceCart([REAL_LINE], "express");
  assert.equal(result.shippingCents, 1520);
  assert.equal(result.totalCents, 6515);
});

test("priceCart waives shipping at or over the free-shipping threshold", () => {
  const result = priceCart([{ ...REAL_LINE, quantity: 3 }], "express");
  assert.equal(result.subtotalCents, 14985);
  assert.equal(result.shippingCents, 0);
  assert.equal(result.totalCents, 14985);
  assert.equal(result.freeShipping, true);
});

test("priceCart sums multiple lines and multiple quantities", () => {
  const result = priceCart(
    [
      { ...REAL_LINE, quantity: 2 },
      { slug: "roll-the-dice-tee", size: "L", colour: "Faded Olive", quantity: 1 },
    ],
    "standard",
  );
  assert.equal(result.subtotalCents, 4995 * 3);
  assert.equal(result.lines.length, 2);
});

test("priceCart rejects an empty cart", () => {
  assert.throws(() => priceCart([], "standard"), CheckoutPricingError);
});

test("priceCart rejects a product that doesn't exist", () => {
  assert.throws(
    () => priceCart([{ ...REAL_LINE, slug: "not-a-real-product" }], "standard"),
    CheckoutPricingError,
  );
});

test("priceCart rejects a colour the product doesn't have", () => {
  assert.throws(
    () => priceCart([{ ...REAL_LINE, colour: "Bright Pink" }], "standard"),
    CheckoutPricingError,
  );
});

test("priceCart rejects a size the product doesn't have", () => {
  assert.throws(
    () => priceCart([{ ...REAL_LINE, size: "XXXL" }], "standard"),
    CheckoutPricingError,
  );
});

test("priceCart rejects a non-positive quantity — the client can't discount itself to free", () => {
  assert.throws(() => priceCart([{ ...REAL_LINE, quantity: 0 }], "standard"), CheckoutPricingError);
  assert.throws(() => priceCart([{ ...REAL_LINE, quantity: -1 }], "standard"), CheckoutPricingError);
});

test("priceCart rejects an unknown shipping method", () => {
  assert.throws(() => priceCart([REAL_LINE], "overnight-drone"), CheckoutPricingError);
});
