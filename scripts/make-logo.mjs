/**
 * Turn the supplied logo lockup (light artwork on a solid black plate) into a
 * trimmed, transparent PNG.
 *
 *   node scripts/make-logo.mjs <source.png>
 *
 * The plate is discarded rather than kept, because the header, drawer and any
 * future light-background usage all need the mark to sit on their own colour.
 * Alpha is taken from luminance, which preserves the antialiased edges — a
 * plain colour-key would leave a hard, jagged cut.
 */
import sharp from "sharp";

const SRC = process.argv[2];
if (!SRC) {
  console.error("usage: node scripts/make-logo.mjs <source.png>");
  process.exit(1);
}

const OUT = "public/logo.png";
const INK = [242, 240, 237]; // --color-paper

// Trim the black plate, then work from the remaining artwork.
const trimmed = await sharp(SRC).trim({ threshold: 20 }).toBuffer();
const meta = await sharp(trimmed).metadata();

// Luminance becomes alpha: white artwork -> opaque, black plate -> clear.
const { data: lum } = await sharp(trimmed)
  .greyscale()
  .raw()
  .toBuffer({ resolveWithObject: true });

const px = meta.width * meta.height;
const rgba = Buffer.alloc(px * 4);
for (let i = 0; i < px; i++) {
  rgba[i * 4] = INK[0];
  rgba[i * 4 + 1] = INK[1];
  rgba[i * 4 + 2] = INK[2];
  rgba[i * 4 + 3] = lum[i];
}

const info = await sharp(rgba, {
  raw: { width: meta.width, height: meta.height, channels: 4 },
})
  .resize({ height: 120, withoutEnlargement: true }) // 3x a ~40px header lockup
  .png({ compressionLevel: 9 })
  .toFile(OUT);

console.log(
  `${OUT}  ${info.width}x${info.height}  ${(info.size / 1024).toFixed(1)}KB` +
    `  (source ${meta.width}x${meta.height})`
);
