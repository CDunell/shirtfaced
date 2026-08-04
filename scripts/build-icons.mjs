/**
 * Generate favicon + mobile icons from DEV/smiley.svg.
 *
 *   node scripts/build-icons.mjs
 *
 * The smiley artwork is 672x922 — tall, because the drips hang well below the
 * face. Centring that raw in a square leaves the face small and off-centre, so
 * the face is fitted to the square and the drips are allowed to run to the
 * bottom edge, which is how the mark reads on packaging anyway.
 *
 * Icons sit on the brand ink rather than transparent: an iOS home-screen icon
 * gets a solid background regardless, and lime-on-white is close to unreadable.
 */
import sharp from "sharp";
import { readFile, writeFile } from "node:fs/promises";

const SRC = "DEV/smiley.svg";
const INK = { r: 13, g: 13, b: 13, alpha: 1 };

/**
 * The face occupies the top ~68% of the 672x922 artwork; the rest is drips.
 * Fitting the whole thing into a square leaves the face tiny, and at 16px the
 * drips are just noise. Crop to the face plus a hint of drip — near square,
 * and still unmistakably the mark.
 */
const KEEP = 0.82; // of artwork height

/** Square icon: mark inset with breathing room, on ink. */
async function icon(size, inset = 0.16) {
  const box = Math.max(8, Math.round(size * (1 - inset * 2)));

  const full = await sharp(SRC, { density: 900 })
    .resize({ height: 1200 })
    .png()
    .toBuffer();
  const fm = await sharp(full).metadata();

  const mark = await sharp(full)
    .extract({
      left: 0,
      top: 0,
      width: fm.width,
      height: Math.round(fm.height * KEEP),
    })
    .resize({ width: box, height: box, fit: "inside" })
    .png()
    .toBuffer();

  const m = await sharp(mark).metadata();
  return sharp({
    create: { width: size, height: size, channels: 4, background: INK },
  })
    .composite([
      {
        input: mark,
        left: Math.round((size - m.width) / 2),
        top: Math.round((size - m.height) / 2),
      },
    ])
    .png({ compressionLevel: 9 })
    .toBuffer();
}

/**
 * Minimal ICO writer. sharp has no .ico encoder, but the format happily
 * embeds PNGs — a 6-byte header, a 16-byte directory entry per image, then
 * the PNG payloads.
 */
function ico(pngs) {
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0); // reserved
  header.writeUInt16LE(1, 2); // type: icon
  header.writeUInt16LE(pngs.length, 4);

  let offset = 6 + pngs.length * 16;
  const entries = [];
  for (const { size, data } of pngs) {
    const e = Buffer.alloc(16);
    e.writeUInt8(size >= 256 ? 0 : size, 0); // width  (0 means 256)
    e.writeUInt8(size >= 256 ? 0 : size, 1); // height
    e.writeUInt8(0, 2); // palette
    e.writeUInt8(0, 3); // reserved
    e.writeUInt16LE(1, 4); // colour planes
    e.writeUInt16LE(32, 6); // bits per pixel
    e.writeUInt32LE(data.length, 8);
    e.writeUInt32LE(offset, 12);
    entries.push(e);
    offset += data.length;
  }
  return Buffer.concat([header, ...entries, ...pngs.map((p) => p.data)]);
}

const targets = [
  ["src/app/icon.png", 512, 0.16],
  ["src/app/apple-icon.png", 180, 0.14],
  ["public/icon-192.png", 192, 0.16],
  ["public/icon-512.png", 512, 0.16],
];

for (const [path, size, inset] of targets) {
  await writeFile(path, await icon(size, inset));
  console.log(`${path.padEnd(26)} ${size}x${size}`);
}

// Legacy /favicon.ico — 16/32/48 so it stays crisp in tab strips and bookmarks.
const sizes = [16, 32, 48];
const pngs = [];
for (const s of sizes) pngs.push({ size: s, data: await icon(s, 0.08) });
await writeFile("src/app/favicon.ico", ico(pngs));
const bytes = (await readFile("src/app/favicon.ico")).length;
console.log(`src/app/favicon.ico        ${sizes.join("/")}  ${(bytes / 1024).toFixed(1)}KB`);
