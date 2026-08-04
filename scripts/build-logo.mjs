/**
 * Compose the primary lockup: wordmark + smiley.
 *
 *   node scripts/build-logo.mjs
 *
 * Writes public/logo-lockup.svg (scalable, used in the header) and a PNG
 * fallback. Both source files stay untouched in DEV/ so the lockup can be
 * regenerated if either asset changes.
 *
 * Alignment: the smiley's FACE — not its bounding box — is centred against the
 * wordmark. The artwork is 672x922 but the face only occupies y≈50–632; the
 * rest is drips. Centring on the bounding box would push the face far too high.
 */
import sharp from "sharp";
import { readFile, writeFile } from "node:fs/promises";

const WORDMARK = "DEV/shirtfaced.svg";
const SMILEY = "DEV/smiley.svg";

const W = { w: 699, h: 162 };
const S = { w: 672, h: 922, faceTop: 50, faceBottom: 632 };

const FACE_H = 150; // slightly under the wordmark's 162 — optically even
const GAP = 28;

const scale = FACE_H / (S.faceBottom - S.faceTop);
const smileyW = S.w * scale;
const smileyH = S.h * scale;
const faceCentre = ((S.faceTop + S.faceBottom) / 2) * scale;
const wordY = faceCentre - W.h / 2; // drop the wordmark so centres agree

const totalW = Math.round(W.w + GAP + smileyW);
const totalH = Math.round(Math.max(smileyH, wordY + W.h));

/** Everything between the outer <svg> tags. */
const inner = (src) => src.replace(/^[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "");

const wordmark = inner(await readFile(WORDMARK, "utf8"));
const smiley = inner(await readFile(SMILEY, "utf8"));

const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${totalW} ${totalH}" width="${totalW}" height="${totalH}" fill="none">
  <g transform="translate(0 ${wordY.toFixed(2)})">${wordmark}</g>
  <g transform="translate(${(W.w + GAP).toFixed(2)} 0) scale(${scale.toFixed(5)})">${smiley}</g>
</svg>
`;

// The composed SVG is kept as a reference/source, NOT shipped: the distressed
// wordmark carries so much path data that it is 162KB raw and 62KB gzipped,
// against 17KB for a 3x PNG at the size the header actually renders it.
await writeFile("DEV/logo-lockup.svg", svg);
console.log(`DEV/logo-lockup.svg        ${totalW}x${totalH}  (scale ${scale.toFixed(4)})  [reference only]`);

// Shipped asset: 3x the header's 46px slot.
const png = await sharp(Buffer.from(svg), { density: 900 })
  .resize({ height: 140 })
  .png({ compressionLevel: 9 })
  .toBuffer();
await writeFile("public/logo-lockup.png", png);
const m = await sharp(png).metadata();
console.log(
  `public/logo-lockup.png     ${m.width}x${m.height}  ${(png.length / 1024).toFixed(1)}KB`
);
