/**
 * Turn a supplied logo lockup (artwork on a solid black plate) into a trimmed,
 * transparent PNG.
 *
 *   node scripts/make-logo.mjs <source.png> [outfile]
 *
 * The plate is discarded because the header, drawer and any light-background
 * usage all need the mark on their own colour.
 *
 * Colour is preserved, not flattened: the lockup mixes a white wordmark with a
 * lime sf monogram, so alpha is taken from the brightest channel rather than
 * luminance (luminance would make the lime semi-transparent). Edge pixels are
 * then un-premultiplied against black, which restores full colour on the
 * antialiased rim instead of leaving a dark halo.
 */
import sharp from "sharp";

const SRC = process.argv[2];
// NOTE: bump the filename whenever the mark changes. Cloudflare caches image
// variants keyed on the request's Accept header, so re-uploading the same URL
// leaves browsers (Accept: image/avif,image/webp) on the stale variant for
// hours even after a purge of the */* copy. A new filename is a new cache key.
const OUT = process.argv[3] || "public/logo-v2.png";
if (!SRC) {
  console.error("usage: node scripts/make-logo.mjs <source.png> [outfile]");
  process.exit(1);
}

const trimmed = await sharp(SRC).trim({ threshold: 20 }).toBuffer();
const { width, height } = await sharp(trimmed).metadata();

const { data } = await sharp(trimmed)
  .removeAlpha()
  .raw()
  .toBuffer({ resolveWithObject: true });

const px = width * height;
const rgba = Buffer.alloc(px * 4);

for (let i = 0; i < px; i++) {
  const r = data[i * 3];
  const g = data[i * 3 + 1];
  const b = data[i * 3 + 2];

  const a = Math.max(r, g, b); // distance from the black plate
  if (a === 0) continue; // fully transparent, RGB irrelevant

  const s = 255 / a; // un-premultiply against black
  rgba[i * 4] = Math.min(255, Math.round(r * s));
  rgba[i * 4 + 1] = Math.min(255, Math.round(g * s));
  rgba[i * 4 + 2] = Math.min(255, Math.round(b * s));
  rgba[i * 4 + 3] = a;
}

const info = await sharp(rgba, { raw: { width, height, channels: 4 } })
  .resize({ height: 120, withoutEnlargement: true }) // 3x a ~40px header lockup
  .png({ compressionLevel: 9 })
  .toFile(OUT);

console.log(
  `${OUT}  ${info.width}x${info.height}  ${(info.size / 1024).toFixed(1)}KB` +
    `  (source ${width}x${height})`
);
