/**
 * Convert raw product photography to web-ready WebP.
 *
 * `output: "export"` means next/image cannot optimise at request time
 * (images.unoptimized is on), so source images have to arrive already sized
 * and compressed. Drop new PNG/JPG shots into public/products and run:
 *
 *   node scripts/optimise-images.mjs
 */
import sharp from "sharp";
import { readdir, stat, unlink } from "node:fs/promises";
import path from "node:path";

const DIR = "public/products";
// 2x a ~500px column for product shots. Full-bleed banners need more, so
// anything named hero-* gets a wider cap.
const PRODUCT_WIDTH = 1000;
const HERO_WIDTH = 1800;

const files = (await readdir(DIR)).filter((f) => /\.(png|jpe?g)$/i.test(f));

if (files.length === 0) {
  console.log("Nothing to optimise.");
  process.exit(0);
}

for (const file of files) {
  const src = path.join(DIR, file);
  const base = file.replace(/\.(png|jpe?g)$/i, "");
  const out = path.join(DIR, `${base}.webp`);
  const before = (await stat(src)).size;

  const width = base.startsWith("hero-") ? HERO_WIDTH : PRODUCT_WIDTH;

  await sharp(src)
    .resize({ width, withoutEnlargement: true })
    .webp({ quality: 80, effort: 6 })
    .toFile(out);

  const after = (await stat(out)).size;
  console.log(
    `${base.padEnd(16)} ${(before / 1e6).toFixed(2)}MB -> ${(after / 1e3).toFixed(0)}KB` +
      `  (${Math.round((1 - after / before) * 100)}% smaller)`
  );

  await unlink(src);
}
