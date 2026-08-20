import { test } from "node:test";
import assert from "node:assert/strict";
import { categoryFor, firstSentence, slugFor, garmentColourFor } from "./approved-design-mapping";

test("categoryFor maps known garments case-insensitively", () => {
  assert.equal(categoryFor(["Hoodie"]), "hoodies");
  assert.equal(categoryFor(["cap"]), "hats");
  assert.equal(categoryFor(["singlet"]), "tanks");
});

test("categoryFor takes the first match when multiple garments are listed", () => {
  assert.equal(categoryFor(["beanie", "tee"]), "hats");
});

test("categoryFor defaults to tees for unmapped or missing garments", () => {
  assert.equal(categoryFor(["board short"]), "tees");
  assert.equal(categoryFor([]), "tees");
  assert.equal(categoryFor(null), "tees");
  assert.equal(categoryFor(undefined), "tees");
});

test("firstSentence cuts at the first sentence boundary", () => {
  assert.equal(
    firstSentence("Take the risk. Obviously. Ships with no advice whatsoever."),
    "Take the risk.",
  );
});

test("firstSentence falls back to a 140-char clip with no sentence boundary", () => {
  const noPunctuation = "a".repeat(200);
  const result = firstSentence(noPunctuation);
  assert.equal(result.length, 140);
});

test("firstSentence handles empty input", () => {
  assert.equal(firstSentence(null), "");
  assert.equal(firstSentence(undefined), "");
  assert.equal(firstSentence("   "), "");
});

test("slugFor prefixes so a synced product never collides with a hand-authored slug", () => {
  assert.equal(slugFor("eight-ball-tee"), "studio-eight-ball-tee");
});

test("garmentColourFor reads a valid hex from production_spec", () => {
  assert.equal(garmentColourFor({ garment_colour: "#4a4a3e" }), "#4a4a3e");
});

test("garmentColourFor falls back on missing or malformed values", () => {
  assert.equal(garmentColourFor(null), "#1c1c1a");
  assert.equal(garmentColourFor({}), "#1c1c1a");
  assert.equal(garmentColourFor({ garment_colour: "not-a-colour" }), "#1c1c1a");
  assert.equal(garmentColourFor({ garment_colour: 42 }), "#1c1c1a");
});
