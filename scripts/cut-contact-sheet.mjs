/**
 * Slice a contact sheet of product shots into individual WebP files.
 *
 *   node scripts/cut-contact-sheet.mjs contact-sheet.png
 *
 * Crop boxes are fractions of the sheet so the same map survives a re-export
 * at a different resolution. A couple of pixels are trimmed off each edge to
 * avoid picking up the gutter lines between frames.
 */
import sharp from "sharp";
import path from "node:path";

const SRC = process.argv[2] || "contact-sheet.png";
const OUT = "public/products";
const INSET = 0.004; // trim gutters

// name, [x, y, w, h] as fractions of the full sheet
const FRAMES = [
  ["midnight-service", [0.0, 0.0, 0.578, 0.392]],
  ["take-your-chances", [0.582, 0.0, 0.418, 0.236]],
  ["love-fast-die-last", [0.582, 0.239, 0.418, 0.153]],
  ["eight-ball", [0.0, 0.395, 0.331, 0.287]],
  ["not-yours", [0.336, 0.395, 0.327, 0.287]],
  ["spin-cycle", [0.668, 0.395, 0.332, 0.287]],
  ["permanent", [0.0, 0.686, 0.505, 0.314]],
  ["built-different", [0.51, 0.686, 0.49, 0.314]],
];

const { width: W, height: H } = await sharp(SRC).metadata();
console.log(`sheet ${W}x${H}\n`);

for (const [name, [fx, fy, fw, fh]] of FRAMES) {
  const left = Math.round((fx + INSET) * W);
  const top = Math.round((fy + INSET) * H);
  const width = Math.round((fw - INSET * 2) * W);
  const height = Math.round((fh - INSET * 2) * H);

  const out = path.join(OUT, `${name}.webp`);
  const info = await sharp(SRC)
    .extract({ left, top, width, height })
    .resize({ width: 1000, withoutEnlargement: true })
    .webp({ quality: 82, effort: 6 })
    .toFile(out);

  console.log(
    `${name.padEnd(20)} ${width}x${height} -> ${info.width}x${info.height}  ${(
      info.size / 1024
    ).toFixed(0)}KB`
  );
}
