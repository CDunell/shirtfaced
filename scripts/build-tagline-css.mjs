/**
 * Generate the hero tagline rotation rules from lib/taglines.ts.
 *
 * The rules were hand-written, one block per pair, each repeating the image
 * path already held in the data. That was fine at six and is not at fifty-four:
 * the same fact in two places, and every new pair a manual edit in a file that
 * has nothing else to do with content.
 *
 * The per-index rule stays rather than moving the background inline, because
 * it is load-bearing: a background-image on a rule that does not match is never
 * fetched, so exactly one of fifty-four photographs downloads. An <img> per
 * pair, or an inline style on every pair, gives that away.
 *
 *   node scripts/build-tagline-css.mjs
 */
import { readFile, writeFile } from "node:fs/promises";

const START = "/* @generated tagline rotation — build-tagline-css.mjs */";
const END = "/* @end tagline rotation */";

const source = await readFile(
  new URL("../src/lib/taglines.ts", import.meta.url),
  "utf8",
);

// Read the data without importing it: this is a .ts module and the script runs
// under plain node. The shape is fixed and written by the generator's own
// sibling, so a regex is honest here rather than fragile.
const pairs = [
  ...source.matchAll(/image:\s*"([^"]+)",[\s\S]*?position:\s*"([^"]+)",/g),
].map(([, image, position]) => ({ image, position }));

if (pairs.length === 0) {
  throw new Error(
    "no taglines found in lib/taglines.ts — refusing to write an empty rotation",
  );
}

const rules = pairs
  .map(
    ({ image, position }, i) => `[data-tag="${i}"] .tl-${i} {
  display: contents;
}
[data-tag="${i}"] .hero-img {
  background-image: url("${image}");
  background-position: ${position};
}`,
  )
  .join("\n");

const fallback = `/* No JS: the first pair still renders rather than an empty hero. */
html:not([data-tag]) .tl-0 {
  display: contents;
}
html:not([data-tag]) .hero-img {
  background-image: url("${pairs[0].image}");
  background-position: ${pairs[0].position};
}`;

const cssPath = new URL("../src/app/globals.css", import.meta.url);
const css = await readFile(cssPath, "utf8");

const block = `${START}\n${rules}\n${fallback}\n${END}`;
const from = css.indexOf(START);
const to = css.indexOf(END);

let next;
if (from >= 0 && to > from) {
  next = css.slice(0, from) + block + css.slice(to + END.length);
} else {
  // First run: replace the hand-written rules, which start at the first
  // [data-tag= rule and end after the no-JS fallback.
  const first = css.indexOf('[data-tag="0"]');
  const last =
    css.indexOf("}", css.indexOf("html:not([data-tag]) .hero-img")) + 1;
  if (first < 0 || last <= first) {
    throw new Error(
      "could not find the hand-written rotation rules to replace",
    );
  }
  next = css.slice(0, first) + block + css.slice(last);
}

await writeFile(cssPath, next, "utf8");
console.log(`wrote ${pairs.length} tagline rotation rules`);
