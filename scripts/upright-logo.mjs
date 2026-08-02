/**
 * De-slant the italic logo into an upright version.
 *
 *   node scripts/upright-logo.mjs            # write candidates for review
 *   node scripts/upright-logo.mjs 13         # commit one angle to logo-upright.png
 *
 * Works by shearing horizontally against the oblique angle. The exact angle of
 * the supplied artwork isn't documented anywhere, so the no-arg mode renders a
 * strip of candidates to compare rather than guessing once and hoping.
 */
import sharp from "sharp";

const SRC = "public/logo.png";
const angleArg = process.argv[2] ? Number(process.argv[2]) : null;

async function deslant(deg) {
  const k = Math.tan((deg * Math.PI) / 180);
  // x' = x + k*y shifts lower rows right; with y increasing downward that
  // straightens artwork whose tops lean right.
  return sharp(SRC)
    .ensureAlpha()
    .affine([1, k, 0, 1], {
      background: { r: 0, g: 0, b: 0, alpha: 0 },
      interpolator: "bicubic",
    })
    .trim({ threshold: 1 })
    .png()
    .toBuffer();
}

if (angleArg !== null) {
  const buf = await deslant(angleArg);
  const info = await sharp(buf)
    .resize({ height: 120, withoutEnlargement: true })
    .png({ compressionLevel: 9 })
    .toFile("public/logo-upright.png");
  console.log(
    `public/logo-upright.png  ${info.width}x${info.height}  ${(
      info.size / 1024
    ).toFixed(1)}KB  (shear ${angleArg}deg)`
  );
} else {
  const angles = [15, 16, 17, 18];
  const rows = [];
  for (const a of angles) {
    const buf = await deslant(a);
    rows.push({
      a,
      buf: await sharp(buf).resize({ height: 90 }).png().toBuffer(),
    });
  }
  const metas = await Promise.all(rows.map((r) => sharp(r.buf).metadata()));
  const W = Math.max(...metas.map((m) => m.width)) + 20;
  const H = rows.length * 110;

  await sharp({
    create: {
      width: W,
      height: H,
      channels: 4,
      background: { r: 13, g: 13, b: 13, alpha: 1 },
    },
  })
    .composite(rows.map((r, i) => ({ input: r.buf, left: 10, top: i * 110 + 10 })))
    .png()
    .toFile("logo-candidates.png");

  console.log("logo-candidates.png written — angles top to bottom: " + angles.join(", "));
}
